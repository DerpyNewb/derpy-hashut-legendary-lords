"""Push Modding Files/source/naval_horde/export/*.tsv back into the lords pack.

Unlike import_house_ancillaries.py this does NOT build a pack from scratch - the naval horde
tables live inside !aa_derpy_hashut_legendary_lords.pack alongside everything else, so this
opens the live pack, re-imports each fragment from its exported TSV, and saves in place.

    py tools/import_naval_horde.py <pack path> [--lua <staged root>]

The TSVs are the exported ones, rewritten in place by tools/gen_naval_horde_tordrek.py, so
import_tsv's replace-the-whole-file behaviour is safe: every row that was in the pack is
still in the file.

Never trust import_tsv's row count - verify by re-opening the saved pack from disk in a
separate run and decoding it.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_house_ancillaries import check_keys            # noqa: E402
from rpfm_client import call, db, ensure_game, exists, open_pack   # noqa: E402

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
    """[(container_path, create_file_kind, tsv_basename, dir)] read from each TSV's meta line.

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
        spec = {"type": "loc"} if table == "Loc" else db(table, int(ver))
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
    ensure_game()
    check_keys(entries)

    pack = open_pack(pack_path)
    for path, spec, fn, d in entries:
        rows = sum(1 for _ in open(os.path.join(d, fn), encoding="utf-8")) - 2
        there = exists(pack, path)
        if rows <= 0:
            # A generator that stops owning a table writes its TSV empty. Importing that
            # leaves a zero-row fragment in the pack forever; delete it instead. Only when
            # it is there, so this is safe to re-run.
            if there:
                call("delete_files", {"pack": pack, "paths": [path]})
            print("  %5s  %s" % ("del", path))
            continue
        if not there:                    # import_tsv replaces a table; it cannot make one
            call("create_file", {"pack": pack, "path": path, "kind": spec})
        call("import_tsv", {"pack": pack, "path": path, "tsv_path": os.path.join(d, fn)})
        print("  %5d  %s" % (rows, path))

    for name in SCRIPTS:
        for src in sorted(glob.glob(os.path.join(PACK, "script", "campaign", "*", "mod",
                                                 name))):
            rel = os.path.relpath(src, PACK).replace(os.sep, "/")
            call("add_files_from_disk", {"pack": pack, "paths": [src], "pack_paths": [rel]})
            print("  %5dB  %s" % (os.path.getsize(src), rel))

    if lua_root:
        for base, _dirs, files in os.walk(lua_root):
            for f in files:
                src = os.path.join(base, f)
                rel = os.path.relpath(src, lua_root).replace(os.sep, "/")
                call("add_files_from_disk", {"pack": pack, "paths": [src], "pack_paths": [rel]})
                print("  %5dB  %s" % (os.path.getsize(src), rel))

    call("save_pack", {"pack": pack})
    print("\nsaved %s" % pack_path)


if __name__ == "__main__":
    main()
