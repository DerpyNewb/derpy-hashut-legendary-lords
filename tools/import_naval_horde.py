"""Push Modding Files/source/naval_horde/export/*.tsv back into the lords pack.

Unlike import_house_ancillaries.py this does NOT build a pack from scratch - the naval horde
tables live inside !aa_derpy_hashut_legendary_lords.pack alongside everything else, so this
opens the live pack, re-imports each fragment from its exported TSV, and saves in place.

    py tools/import_naval_horde.py <pack path> [--lua <staged root>]

The TSVs are the exported ones, rewritten in place by tools/gen_naval_horde_tordrek.py, so
import_tsv's replace-the-whole-file behaviour is safe: every row that was in the pack is
still in the file.

Never trust import_tsv's "Success" - verify by re-opening the saved pack in a FRESH session
and decoding it. Each py invocation is its own MCP session.
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_house_ancillaries import call, check_keys      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "Modding Files", "source", "naval_horde", "export")
PACK = os.path.join(ROOT, "Modding Files", "pack")
# Campaign scripts, added from the canonical Modding Files/pack mirror at their relative
# path. One file per campaign folder, the same spread CA and this pack already use. They go
# in on every run so a regenerated derpy_chd_vc_unit_lock.lua cannot be left behind in the
# staging folder while the pack ships the old one.
# The two lord start scripts are here because the mirror had DRIFTED from the pack: the
# pack held the newer revision and the staged copy an older one, so anything that shipped
# the mirror would have silently reverted a fix. Shipping them every run keeps the mirror
# authoritative, which is the only way the drift cannot come back.
SCRIPTS = ["derpy_chd_naval_admiral.lua", "derpy_chd_vc_unit_lock.lua",
           "derpy_start_abnagg.lua", "derpy_start_tordrek.lua", "ime_derpy_abnagg.lua"]


def plan():
    """[(container_path, new_file_spec, tsv_basename, dir)] read from each TSV's meta line.

    The meta line is RPFM's own `#<table>;<version>;<path>` - taking the version and the
    destination path from there rather than a hardcoded list means a schema bump cannot
    silently write the wrong table version.
    """
    out = []
    for fn in sorted(os.listdir(EXP)):
        if not fn.endswith(".tsv"):
            continue
        with open(os.path.join(EXP, fn), encoding="utf-8") as fh:
            fh.readline()
            meta = fh.readline().rstrip("\n").split("\t")[0]
        assert meta.startswith("#"), "%s has no RPFM meta line: %r" % (fn, meta)
        table, ver, path = meta[1:].split(";")
        if table == "Loc":
            spec = {"Loc": path.rsplit("/", 1)[-1].replace(".loc", "")}
        else:
            spec = {"DB": [path.rsplit("/", 1)[-1], table, int(ver)]}
        out.append((path, spec, fn, EXP))
    return out


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pack_path = sys.argv[1]
    lua_root = None
    if "--lua" in sys.argv:
        lua_root = sys.argv[sys.argv.index("--lua") + 1]

    entries = plan()
    call("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False})
    check_keys(entries)

    pack = call("open_packfiles", {"paths": [pack_path]})["StringContainerInfo"][0]
    for path, spec, fn, d in entries:
        rows = sum(1 for _ in open(os.path.join(d, fn), encoding="utf-8")) - 2
        if rows <= 0:
            # A generator that stops owning a table writes its TSV empty. Importing that
            # leaves a zero-row fragment in the pack forever; delete it instead. RPFM
            # answers happily when the path is not there, so this is safe to re-run.
            call("delete_packed_files", {"pack_key": pack,
                                         "paths": json.dumps([{"File": path}])})
            print("  %5s  %s" % ("del", path))
            continue
        call("new_packed_file", {"pack_key": pack, "path": path,
                                 "new_file": json.dumps(spec)})
        call("import_tsv", {"pack_key": pack, "table_path": path,
                            "tsv_path": os.path.join(d, fn)})
        print("  %5d  %s" % (rows, path))

    for name in SCRIPTS:
        for src in sorted(glob.glob(os.path.join(PACK, "script", "campaign", "*", "mod",
                                                 name))):
            rel = os.path.relpath(src, PACK).replace(os.sep, "/")
            call("add_packed_files", {"pack_key": pack, "source_paths": [src],
                                      "destination_paths": json.dumps([{"File": rel}])})
            print("  %5dB  %s" % (os.path.getsize(src), rel))

    if lua_root:
        for base, _dirs, files in os.walk(lua_root):
            for f in files:
                src = os.path.join(base, f)
                rel = os.path.relpath(src, lua_root).replace(os.sep, "/")
                call("add_packed_files", {"pack_key": pack, "source_paths": [src],
                                          "destination_paths": json.dumps([{"File": rel}])})
                print("  %5dB  %s" % (os.path.getsize(src), rel))

    call("save_packfile", {"pack_key": pack})
    print("\nsaved %s" % pack_path)


if __name__ == "__main__":
    main()
