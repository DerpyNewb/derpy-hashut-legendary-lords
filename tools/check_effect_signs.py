# -*- coding: utf-8 -*-
"""Print every effect row in a pack whose SIGN makes it a penalty for the player.

    py tools/check_effect_signs.py "<pack path>" [owner substring]
    py tools/check_effect_signs.py --selftest

`effects.is_positive_value_good` is False on every cost modifier, so `-20` on
`derpy_chd_artillery_trains_upkeep` is a 20% DISCOUNT and `+20` is the price. Nothing else
catches a value on the wrong side of that: the key exists, the scope is precedented, the
junction row is well formed, the loc resolves and the pack loads. It has now shipped twice -
the Great Guilds' two inverted reward ladders (2026-09-10) and Thymbrin's tier-4 node, which
promised in its own description that rebuilt engines are "paid for by the turn, out of the war
chest" and then handed out a 20% upkeep discount (2026-09-17).

**This is a review instrument, not a gate, and it exits 0.** There is no invariant to assert:
deliberate downsides are the whole point of this pack's tier-4 nodes, and two of them carry
two. What the report buys is that the list is SHORT - 45 penalty rows out of 817 across the
lords pack - so "is every one of these meant to hurt?" is a minute's reading rather than a
spreadsheet. Read it against each skill's own description; that is what found the Thymbrin row.

Custom effects are read from the pack's own `effects_tables`, vanilla ones from
`.skilltree_cache`, so a mod's minted effect is judged by the flag it actually ships.

Needs RPFM open (the MCP server only exists while it is).
"""
import os
import sys
import io
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_house_ancillaries import call                      # noqa: E402
from read_vanilla_cache import load                            # noqa: E402
import read_pack_index as rpi                                  # noqa: E402

SOURCES = ("db/character_skill_level_to_effects_junctions_tables/",
           "db/effect_bundles_to_effects_junctions_tables/",
           "db/ancillary_to_effects_tables/")
OWNER_COLS = ("character_skill_key", "effect_bundle_key", "ancillary")


def is_penalty(value, positive_is_good):
    """True when this row hurts its holder. Both halves matter - a negative value on a cost
    modifier is a REWARD, which is exactly the case everybody reads backwards."""
    return (value > 0) != bool(positive_is_good)


def report(pack_path, owner_filter=""):
    call("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False})
    pack = call("open_packfiles", {"paths": [pack_path]})["StringContainerInfo"][0]
    tmp = tempfile.mkdtemp()

    def rows(path):
        dst = os.path.join(tmp, path.replace("/", "_") + ".tsv")
        call("export_tsv", {"pack_key": pack, "table_path": path, "tsv_path": dst})
        lines = io.open(dst, encoding="utf-8").read().replace("\r\n", "\n")
        lines = lines.rstrip("\n").split("\n")
        cols = lines[0].split("\t")
        return [dict(zip(cols, l.split("\t"))) for l in lines[2:]]

    good = {r["effect"]: r["is_positive_value_good"] for r in load("effects")[0]}
    loc, paths = {}, rpi.paths(pack_path)
    for p in paths:
        if p.startswith("db/effects_tables/"):
            for r in rows(p):                      # the pack's own flags win
                good[r["effect"]] = str(r["is_positive_value_good"]).lower() == "true"
        elif p.endswith(".loc"):
            for r in rows(p):
                loc[r["key"]] = r["text"]

    total, bad, unknown = 0, [], []
    for p in paths:
        if not p.startswith(SOURCES):
            continue
        for r in rows(p):
            owner = next((r[c] for c in OWNER_COLS if c in r), "")
            eff = r.get("effect_key") or r.get("effect", "")
            try:
                v = float(r["value"])
            except (KeyError, ValueError):
                continue
            total += 1
            if owner_filter and owner_filter not in owner:
                continue
            if eff not in good:
                unknown.append((owner, eff))
            elif is_penalty(v, good[eff]):
                bad.append((owner, eff, v, loc.get("effects_description_" + eff, "")))

    for owner, eff, v, d in bad:
        print("  %-38s %-52s %9.2f  %s" % (owner[:38], eff[:52], v, d[:44]))
    for owner, eff in unknown:
        print("  %-38s %-52s %9s  NOT IN effects_tables" % (owner[:38], eff[:52], "?"))
    print("%d effect rows, %d read as a penalty, %d with no effects row"
          % (total, len(bad), len(unknown)))


def _selftest():
    # a reward effect: positive is the bonus
    assert not is_penalty(20.0, True)
    assert is_penalty(-20.0, True)
    # a cost modifier: is_positive_value_good is False, so POSITIVE is the price. This pair is
    # the whole bug - -20 upkeep is a discount, not a cost.
    assert is_penalty(20.0, False)
    assert not is_penalty(-20.0, False)
    # the flag arrives from a TSV as a string; "false" must not read as truthy
    assert is_penalty(20.0, str("false").lower() == "true")
    assert not is_penalty(-20.0, str("false").lower() == "true")
    print("selftest ok - a negative value on a cost modifier is reported as a REWARD")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    elif len(sys.argv) in (2, 3):
        report(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else "")
    else:
        print(__doc__)
        sys.exit(1)
