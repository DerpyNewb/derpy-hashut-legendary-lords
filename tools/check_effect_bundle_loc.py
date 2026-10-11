# -*- coding: utf-8 -*-
"""Every effect bundle a pack mints must ship its two loc keys.

    py tools/check_effect_bundle_loc.py "<pack path>"
    py tools/check_effect_bundle_loc.py --selftest

`effect_bundles_tables.localised_title` / `.localised_description` are `localised_fields`, and
the raw row value is NOT what the panels read. A bundle with text in the row and no
`effect_bundles_localised_title_<key>` / `..._description_<key>` in a `.loc` draws with no text
at all - applied, visible, unreadable. That shipped once as 27 bundles in the Faction Effects
panel (2026-09-05) and again as the naval horde's Encamp stance tooltip, whose title line was
simply absent while every effect under it read correctly (2026-09-17). Both times the row text
was already right, which is exactly why nobody looked.

It checks that the two keys EXIST, and nothing else. Two narrower rules were tried and both
were wrong against measurement:

* Comparing the loc against the row reported 19 of this pack's own bundles. Most of them leave
  the row columns empty or "PH" on purpose - the loc is the single source and the row column is
  dead weight. The check has to know which copy is the live one.
* Flagging a blank or "PH" description reported 12 more, including CA's own convention:
  `effect_bundles_localised_description_wh3_dlc23_chd_toz_tier_1_reward` through `_4_reward`
  all read literally "PH" in vanilla, so our tier 5 matching them is correct, not a leftover.

`[hidden]` bundles are skipped by design. A cost modifier the player must never see is meant to
have no loc; that is how it stays invisible.

Needs RPFM open (the MCP server only exists while it is).
"""
import os
import sys
import io
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_house_ancillaries import call                      # noqa: E402
import read_pack_index as rpi                                  # noqa: E402

HIDDEN = "[hidden]"
TITLE = "effect_bundles_localised_title_"
DESC = "effect_bundles_localised_description_"


def findings(bundles, locs):
    """[(key, problem)] for bundle rows {key, localised_title, localised_description}.

    Pure, so --selftest can break it without a pack. `locs` is {loc key: text}.
    """
    out = []
    for row in bundles:
        key = row["key"]
        if row["localised_title"] == HIDDEN:
            continue
        for prefix in (TITLE, DESC):
            if prefix + key not in locs:
                out.append((key, "no loc key %s%s" % (prefix, key)))
    return out


def read_pack(pack_path):
    """(bundle rows, loc dict) out of a saved pack."""
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

    bundles, locs = [], {}
    for p in rpi.paths(pack_path):
        if p.startswith("db/effect_bundles_tables/"):
            bundles += rows(p)
        elif p.endswith(".loc"):
            for r in rows(p):
                locs[r["key"]] = r["text"]
    return bundles, locs


def _selftest():
    good = [{"key": "a", "localised_title": "T", "localised_description": "D"}]
    locs = {TITLE + "a": "T", DESC + "a": "D"}
    assert findings(good, locs) == [], findings(good, locs)

    # the 2026-09-17 fault: row text present, loc absent. One finding per missing key.
    assert len(findings(good, {})) == 2
    assert len(findings(good, {TITLE + "a": "T"})) == 1

    # the row columns are NOT the source and must not be compared - this pack leaves them
    # empty or "PH" on purpose, and comparing them reported 19 false faults on the first run
    blank_row = [{"key": "a", "localised_title": "", "localised_description": "PH"}]
    assert findings(blank_row, locs) == [], findings(blank_row, locs)

    # and a present-but-empty loc value is CA's own convention here, not a fault
    assert findings(good, {TITLE + "a": "T", DESC + "a": "PH"}) == []

    # a hidden bundle needs neither
    hidden = [{"key": "h", "localised_title": HIDDEN, "localised_description": HIDDEN}]
    assert findings(hidden, {}) == []

    print("selftest ok - a missing key is reported, a blank row column and a 'PH' loc are not")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    elif len(sys.argv) == 2:
        bundles, locs = read_pack(sys.argv[1])
        bad = findings(bundles, locs)
        for key, why in bad:
            print("  %-60s %s" % (key, why))
        print("%d bundles, %d loc keys, %d finding(s)" % (len(bundles), len(locs), len(bad)))
        sys.exit(1 if bad else 0)
    else:
        print(__doc__)
        sys.exit(1)
