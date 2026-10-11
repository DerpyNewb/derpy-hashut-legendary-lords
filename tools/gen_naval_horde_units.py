"""Phase 5 - unit-granting levels for the Abnagg/Tordrek naval horde ship chains.

Emits the FULL accumulated building_units_allowed_tables fragment, because
import_tsv replaces the whole file (see [[wh3-import-tsv-replaces-whole-file]]).
Phase 4's single main_deck_1 row is included here and keeps its original key.

The table is cumulative per level: a level must list every unit its chain
unlocked at or below that level, not just the new ones. CA's own column
description says so; VC's rows confirm it.

Run:  py tools/gen_naval_horde_units.py
Then: import Modding Files/source/naval_horde/building_units_allowed_tables__derpy_chd_naval_horde.tsv
      into db/building_units_allowed_tables/derpy_chd_naval_horde (RPFM, game closed).
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
OUT = os.path.join(ROOT, "Modding Files", "source", "naval_horde")

TABLE = "building_units_allowed_tables"
VERSION = 4
FRAG = "derpy_chd_naval_horde"
HEADER = "key\tbuilding\tunit\tXP\tconditions\tfaction\tenabled"  # RPFM display order, key first
PREFIX = "derpy_chd_naval_horde"
FIRST_KEY = 950000001  # Phase 4's key; main_deck_1/cutthroats must keep it

C = "wh3_dlc23_chd_"

# chain -> level -> units NEWLY unlocked at that level. Cumulative expansion below.
# Roles mirror Vampire Coast's split (main_deck core melee, gunports missile,
# cannons artillery, crows_nest fliers, hold beasts/slaves, hull war engines).
NEW_AT = {
    "main_deck": {                                    # the fighting deck
        1: [C + "inf_hobgoblin_cutthroats"],
        2: [C + "inf_chaos_dwarf_warriors"],
        3: [C + "inf_chaos_dwarf_warriors_great_weapons", C + "inf_infernal_guard"],
        4: [C + "inf_infernal_guard_great_weapons", C + "inf_infernal_ironsworn"],
    },
    "gunports": {                                     # firing slits down the flanks
        1: [C + "inf_hobgoblin_archers"],
        2: [C + "inf_chaos_dwarf_blunderbusses"],
        3: [C + "inf_infernal_guard_fireglaives"],
        4: [],                                        # bolt thrower moved to hull_1 (a war engine)
    },
    "cannons": {                                      # the heavy batteries
        1: [C + "veh_magma_cannon"],
        2: [C + "veh_deathshrieker_rocket_launcher"],
        3: [C + "veh_dreadquake_mortar", "wh_main_chs_art_hellcannon"],
    },
    "crows_nest": {                                   # lookouts, then fliers
        1: [C + "inf_hobgoblin_sneaky_gits"],
        2: [C + "mon_lammasu"],
        3: [C + "mon_great_taurus"],
        4: [C + "mon_bale_taurus"],
    },
    "hold": {                                         # slave pens and stables
        1: [C + "inf_goblin_labourers", C + "inf_orc_labourers"],
        2: [C + "cav_hobgoblin_wolf_raiders_bows", C + "cav_hobgoblin_wolf_raiders_spears"],
        3: [C + "cav_bull_centaurs_axe", C + "cav_bull_centaurs_dual_axe",
            C + "cav_bull_centaurs_greatweapons"],
    },
    # hull_1 is primreq 0 / cost 1000, so its grant IS available turn one - deliberate for the
    # bolt thrower, the one war engine cheap enough to be a starting piece.
    "hull": {                                         # what rides in the ship's belly
        1: ["wh3_main_chd_art_hobgob_bolt_thrower"],
        2: [C + "veh_iron_daemon", C + "veh_skullcracker"],
        3: [C + "mon_kdaai_fireborn", C + "mon_kdaai_destroyer"],
    },
}

# levels each chain actually has, read out of the shipped pack (Phase 2, VC 1:1)
CHAIN_LEVELS = {"main_deck": 4, "gunports": 4, "cannons": 3,
                "crows_nest": 4, "hold": 3, "hull": 3}


def build():
    """chain -> level -> cumulative unit list."""
    out = {}
    for chain, by_level in NEW_AT.items():
        seen, levels = [], {}
        for lvl in sorted(by_level):
            for u in by_level[lvl]:
                assert u not in seen, "%s re-granted in %s" % (u, chain)
                seen.append(u)
            levels[lvl] = list(seen)
        out[chain] = levels
    return out


# main_deck first so Phase 4's shipped row keeps FIRST_KEY
CHAIN_ORDER = ["main_deck", "gunports", "cannons", "crows_nest", "hold", "hull"]


def rows():
    key, tree = FIRST_KEY, build()
    for chain in CHAIN_ORDER:
        for lvl in sorted(tree[chain]):
            for unit in tree[chain][lvl]:
                yield key, "%s_%s_%d" % (PREFIX, chain, lvl), unit
                key += 1


def check(rs):
    from read_vanilla_cache import load
    van, _ = load("building_units_allowed")
    recruitable = set(r["unit"] for r in van
                      if str(r.get("building", "")).startswith("wh3_dlc23_chd_"))
    van_keys = set(int(r["key"]) for r in van)

    keys = [r[0] for r in rs]
    assert len(set(keys)) == len(keys), "duplicate key"
    assert not (set(keys) & van_keys), "key collides with vanilla"
    for k, b, u in rs:
        assert u in recruitable, "%s is not a CHD-recruitable unit key" % u
        chain, lvl = b[len(PREFIX) + 1:].rsplit("_", 1)
        assert 1 <= int(lvl) <= CHAIN_LEVELS[chain], "no such level %s" % b
    # cumulative: every level contains its predecessor's units
    per = {}
    for _, b, u in rs:
        per.setdefault(b, set()).add(u)
    for chain, top in CHAIN_LEVELS.items():
        for lvl in range(2, top + 1):
            lo = per.get("%s_%s_%d" % (PREFIX, chain, lvl - 1), set())
            hi = per.get("%s_%s_%d" % (PREFIX, chain, lvl), set())
            if lo and hi:
                assert lo <= hi, "%s_%d drops units from level %d" % (chain, lvl, lvl - 1)
    # Phase 4's shipped row survives the regeneration
    assert (FIRST_KEY, PREFIX + "_main_deck_1", C + "inf_hobgoblin_cutthroats") in rs, \
        "Phase 4 row missing"


def main():
    rs = list(rows())
    check(rs)
    os.makedirs(OUT, exist_ok=True)
    meta = "#%s;%d;db/%s/%s" % (TABLE, VERSION, TABLE, FRAG)
    pad = "\t" * (HEADER.count("\t"))
    lines = [HEADER, meta + pad]
    for k, b, u in rs:
        lines.append("%d\t%s\t%s\t0\t0\t\tfalse" % (k, b, u))  # XP/conditions 0, faction blank,
                                                               # enabled false - all 6396 vanilla rows
    path = os.path.join(OUT, "%s__%s.tsv" % (TABLE, FRAG))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("%d rows -> %s" % (len(rs), path))
    for chain in sorted(CHAIN_LEVELS):
        per = build()[chain]
        print("  %-11s %s" % (chain, " ".join("L%d:%d" % (l, len(per[l])) for l in sorted(per))))


if __name__ == "__main__":
    main()
