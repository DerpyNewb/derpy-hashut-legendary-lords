"""Find a number literal on the LEFT of an arithmetic operator in a function the
game's Lua compiles wrongly.

THE GAME'S COMPILER IS NOT STOCK 5.1.5. Once a function holds more than 255
constants, a literal can no longer ride in the instruction and is loaded into a
register first - and the game loads it BEFORE it evaluates the right operand, so
a right operand like `ICUI.PLOTS_Y` frees that register and lands on top of it.
Measured in game 2026-09-24, inside the Iron Court panel's main chunk:

    2 * ICUI.PLOT_PAD     -> 900    (30 * 30)
    ICUI.PLOT_PAD * 2     -> 60
    2 * pad               -> 60     (pad a local)

`978 - 6 - ICUI.PLOTS_Y` became `226 - 226`, PLOT_H came out -11, and every
move card in a column was drawn 3px below the last. Stock lua.exe - the
harness, gate 8d - computes 176, so nothing offline could see it.

WHAT THIS READS: stock `luac -l`, where the same code is a LOADK into a register
immediately followed by an arithmetic op whose LEFT operand is that register.
That shape exists only for a literal-left operand in a function over 255
constants, so every hit is one to rewrite - a superset of what breaks in game,
which also covers a local right operand that happens to survive today.

THE FIX AT A SITE: put the literal on the right (`x * 2`, `x + 1`), or make the
left operand a local. Never reorder into `-x + k` for a subtraction - hoist.

    py tools\\check_lua_literal_left.py            # every shipped campaign script
    py tools\\check_lua_literal_left.py <file.lua>
    py tools\\check_lua_literal_left.py --selftest
"""
import glob
import os
import re
import subprocess
import sys
import tempfile

LUAC = r"C:\Program Files (x86)\Lua\5.1\luac.exe"
ARITH = {"ADD", "SUB", "MUL", "DIV", "MOD", "POW"}
INSN = re.compile(r"^\s*\d+\s+\[(\d+)\]\s+([A-Z]+)\s+(-?\d+)(?:\s+(-?\d+))?(?:\s+(-?\d+))?")


def findings(path):
    """[(line, op)] for every literal-left arithmetic op in the file."""
    out = subprocess.run([LUAC, "-l", "-p", path], capture_output=True, text=True)
    if out.returncode:
        raise SystemExit("luac failed on %s: %s" % (path, out.stderr.strip()))
    hits, prev, before = [], None, None
    for text in out.stdout.splitlines():
        m = INSN.match(text)
        if not m:
            prev = before = None    # a function header: registers start over
            continue
        line, op, a, b = int(m.group(1)), m.group(2), int(m.group(3)), m.group(4)
        # A LOADK RIGHT AFTER A JMP IS AN `or` FALLBACK - `(x or 0) + y` loads the
        # 0 into the left operand's own register - and that is correct code in
        # any compiler. 25 of the first 29 hits were that shape.
        if (op in ARITH and prev and prev[0] == "LOADK" and b is not None
                and int(b) == prev[1] and not (before and before[0] == "JMP")):
            hits.append((line, op))
        before, prev = prev, (op, a)
    return hits


def main(paths):
    bad = 0
    for path in paths:
        for line, op in findings(path):
            bad += 1
            print("%s:%d  %s with a number literal on the left" % (path, line, op))
    print("%d file(s), %d literal-left site(s)" % (len(paths), bad))
    return 1 if bad else 0


def _selftest():
    filler = "".join("X%d = %d\n" % (i, 1000 + i) for i in range(300))
    cases = {
        "A = 2 * T.pad\n": True,           # 900 in game
        "A = 972 - T.pad\n": True,         # the PLOT_H shape
        "A = T.pad * 2\n": False,
        "local p = T.pad\nA = 2 * p\n": True,   # survives in game; still flagged
        "A = 2 * 3\n": False,              # folded at compile time
        "A = (T.k or 0) + T.pad\n": False,  # the or fallback, not a literal
        "A = 68 + (T.pad - 1) * 18\n": True,
    }
    for tail, want in cases.items():
        with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
            f.write(filler + "T = {pad = 30}\n" + tail)
        try:
            got = bool(findings(f.name))
        finally:
            os.remove(f.name)
        assert got == want, (tail, got)
    # UNDER 256 CONSTANTS THE LITERAL RIDES IN THE INSTRUCTION, which is correct.
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
        f.write("T = {pad = 30}\nA = 2 * T.pad\n")
    try:
        assert findings(f.name) == []
    finally:
        os.remove(f.name)
    print("selftest ok")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--selftest"]:
        _selftest()
        sys.exit(0)
    sys.exit(main(args or sorted(glob.glob("Modding Files/pack/script/campaign/mod/*.lua"))))
