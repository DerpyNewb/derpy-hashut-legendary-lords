"""Push the generated victory routes into the lords pack, in place.

    py tools/import_victory_routes.py <pack path>
    py tools/import_victory_routes.py <pack path> --verify-only

Six DB/loc fragments (three of them the minted trophy items the routes pay) and one campaign
script, plus the DELETION of the four copies of
`derpy_chd_victory_objectives.lua` that the routes supersede. That deletion is the part worth
being careful about: the staged copies are already gone from `Modding Files/pack`, but a file
removed from staging is NOT removed from the pack - it sits there until something deletes it,
and leaving it in would put `factions[]` entries back for the eleven houses whose CA victory
missions the routes now disable.

Run `tools/gen_victory_routes.py` first. This packs the FILES ON DISK, not the generator's
objects, so a `--selftest`-only edit would otherwise ship the previous generate; the row-count
gate below is what catches that.

Never trust `import_tsv`'s "Success" - the verify pass re-opens the saved pack in a FRESH
session and decodes every fragment back. Each py invocation is its own MCP session.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_house_ancillaries import call, check_keys      # noqa: E402
import gen_victory_routes as G                             # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Modding Files", "source", "victory_routes")
PACK_MIRROR = os.path.join(ROOT, "Modding Files", "pack")

SCRIPT_REL = "script/campaign/mod/zzz_derpy_chd_victory_routes.lua"

# Superseded by the routes - see docs/VICTORY_CONDITIONS.md section 12. Deleted from the pack
# on every run, so a stale copy cannot come back from an older build.
# temp_spawn_pool_chd_oldworld.lua handed Warrhak and Gordak out on turn one; their quests
# replace it (2026-10-04).
DEAD_SCRIPTS = ["script/campaign/%s/mod/%s" % (c, f) for f in G.DEAD_SCRIPTS
                for c in G.DEAD_CAMPAIGNS]

# What build() says each fragment should hold, so a stale TSV cannot ship.
# Ghorth carries five routes and the other ten three, so a house count times three stopped
# being the row count. Derived from ROUTES itself now, which is the only thing that cannot
# drift from what build() emits.
_N_ROUTES = sum(len(G.ROUTES[f]) for f in G.HOUSES)
# The quests ride in the same two fragments: one missions row and three loc keys each.
_N_MISSION_ROWS = len(G.SLOT_KEYS) + len(G.all_quests())
EXPECTED_ROWS = {
    "victory_types_tables__derpy_chd_victory.tsv": _N_ROUTES,
    "missions_tables__derpy_chd_victory.tsv": _N_MISSION_ROWS,
    # one display name per route, the three localised fields every missions row needs, and
    # each trophy's name and flavour
    "loc__derpy_chd_victory.tsv": _N_ROUTES + 3 * _N_MISSION_ROWS + 2 * len(G.TROPHY_ITEMS)
                                  + G.n_take_objectives()    # one line per sack-or-occupy goal
                                  + len(G.LORE) + len(G.EXPLAIN),   # the route text lines
    # the minted trophy items the routes pay (see TROPHY_ITEMS)
    "ancillary_info_tables__derpy_chd_victory.tsv": len(G.TROPHY_ITEMS),
    "ancillaries_tables__derpy_chd_victory.tsv": len(G.TROPHY_ITEMS),
    "ancillary_to_effects_tables__derpy_chd_victory.tsv": len(G.trophy_effect_rows()),
}


def plan():
    """[(container_path, new_file_spec, tsv_basename, dir)], read from each TSV's meta line.

    Taking the table version and destination path from RPFM's own `#<table>;<version>;<path>`
    line rather than a hardcoded list means a schema bump cannot silently write the wrong
    table version.
    """
    out = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith(".tsv"):
            continue
        with open(os.path.join(SRC, fn), encoding="utf-8") as fh:
            fh.readline()
            meta = fh.readline().rstrip("\n").split("\t")[0]
        assert meta.startswith("#"), "%s has no RPFM meta line: %r" % (fn, meta)
        table, ver, path = meta[1:].split(";")
        if table == "Loc":
            spec = {"Loc": path.rsplit("/", 1)[-1].replace(".loc", "")}
        else:
            spec = {"DB": [path.rsplit("/", 1)[-1], table, int(ver)]}
        assert path == path.lower(), "uppercase in a pack path crashes since 6.1: %s" % path
        out.append((path, spec, fn, SRC))
    return out


def rows_in(path):
    return sum(1 for _ in open(path, encoding="utf-8")) - 2


def gate(entries):
    """Refuse to pack a stale or disagreeing generate."""
    findings = G.check(quiet=True)
    if findings:
        raise SystemExit("gen_victory_routes.py --check is not clean:\n  "
                         + "\n  ".join(findings))

    seen = {e[2] for e in entries}
    missing = set(EXPECTED_ROWS) - seen
    if missing:
        raise SystemExit("missing TSVs - run gen_victory_routes.py first: %s"
                         % sorted(missing))

    for _path, _spec, fn, d in entries:
        want = EXPECTED_ROWS.get(fn)
        got = rows_in(os.path.join(d, fn))
        if want is not None and got != want:
            raise SystemExit("%s has %d rows but build() makes %d - re-run "
                             "gen_victory_routes.py" % (fn, got, want))

    src = os.path.join(PACK_MIRROR, *SCRIPT_REL.split("/"))
    if not os.path.isfile(src):
        raise SystemExit("missing %s - run gen_victory_routes.py first" % src)
    # The staged Lua must match what build() makes right now, for the same reason as the rows.
    if open(src, encoding="utf-8").read() != G.build_lua():
        raise SystemExit("%s is stale - re-run gen_victory_routes.py" % SCRIPT_REL)


def verify(pack_path, entries):
    """Re-open the SAVED pack in this session and decode every fragment back out."""
    pack = call("open_packfiles", {"paths": [pack_path]})["StringContainerInfo"][0]
    bad = []

    # Round-trip every fragment: extract it back out AS TSV and count the rows. A file that
    # is merely present proves nothing - this proves the pack's copy still decodes against
    # the schema and holds what the source TSV holds.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        call("extract_packed_files", {
            "pack_key": pack,
            "source_paths": json.dumps({"PackFile": [{"File": p} for p, _, _, _ in entries]}),
            "destination_path": td,
            "export_as_tsv": True,
        })
        for path, _spec, fn, d in entries:
            want = rows_in(os.path.join(d, fn))
            got_path = os.path.join(td, *path.split("/")) + ".tsv"
            if not os.path.isfile(got_path):
                bad.append("%s did not extract back out of the saved pack" % path)
                continue
            got = rows_in(got_path)
            if got != want:
                bad.append("%s has %d rows in the pack, %d in the source TSV"
                           % (path, got, want))
                continue
            print("  ok   %-56s %3d rows round-tripped" % (path, got))

    for rel in [SCRIPT_REL]:
        if not call("packed_file_exists", {"pack_key": pack, "value": rel}).get("Bool"):
            bad.append("%s is not in the saved pack" % rel)
        else:
            print("  ok   %s" % rel)

    for rel in DEAD_SCRIPTS:
        if call("packed_file_exists", {"pack_key": pack, "value": rel}).get("Bool"):
            bad.append("SUPERSEDED %s is STILL in the pack" % rel)
    if not bad:
        print("  ok   all %d superseded script copies are gone" % len(DEAD_SCRIPTS))

    return bad


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pack_path = sys.argv[1]
    entries = plan()

    call("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False})

    if "--verify-only" in sys.argv:
        bad = verify(pack_path, entries)
        for b in bad:
            print("FINDING: %s" % b)
        raise SystemExit(1 if bad else 0)

    gate(entries)
    check_keys(entries)

    pack = call("open_packfiles", {"paths": [pack_path]})["StringContainerInfo"][0]

    for path, spec, fn, d in entries:
        call("new_packed_file", {"pack_key": pack, "path": path,
                                 "new_file": json.dumps(spec)})
        call("import_tsv", {"pack_key": pack, "table_path": path,
                            "tsv_path": os.path.join(d, fn)})
        print("  %5d  %s" % (rows_in(os.path.join(d, fn)), path))

    src = os.path.join(PACK_MIRROR, *SCRIPT_REL.split("/"))
    call("add_packed_files", {"pack_key": pack, "source_paths": [src],
                              "destination_paths": json.dumps([{"File": SCRIPT_REL}])})
    print("  %5dB  %s" % (os.path.getsize(src), SCRIPT_REL))

    # RPFM answers happily when the path is not there, so this is safe to re-run.
    for rel in DEAD_SCRIPTS:
        call("delete_packed_files", {"pack_key": pack,
                                     "paths": json.dumps([{"File": rel}])})
        print("  %5s  %s" % ("del", rel))

    call("save_packfile", {"pack_key": pack})
    print("\nsaved %s" % pack_path)


if __name__ == "__main__":
    main()
