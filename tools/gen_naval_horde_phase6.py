"""Phase 6 - real effects on the naval horde's chains, and CHD icons on all of them.

Reads the TSVs exported out of the pack and rewrites them in place, so the rows this
phase does not touch (the two shipworks buildings) cannot be lost to import_tsv
replacing the whole file. Re-export before running if the pack has moved on.

Run:  py tools/gen_naval_horde_phase6.py
Then: import both TSVs back into their db/<table>/derpy_chd_naval_horde paths.
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
SRC = os.path.join(ROOT, "Modding Files", "source", "naval_horde")
P = "derpy_chd_naval_horde"

# chain -> vanilla CHD building icon (ui/buildings/icons/<name>.png in ui.pack).
# Was cst_ship_* throughout: Vampire Coast art on a Chaos Dwarf ship.
ICONS = {
    "flagship":   "chd_factory_settlement",            # the ship is the settlement
    "main_deck":  "chd_military_chaos_dwarf_infantry", # the fighting deck
    "gunports":   "chd_tower_ballistics",              # firing slits
    "cannons":    "chd_military_war_machines",         # the batteries
    "crows_nest": "chd_military_beasts",               # lookouts and fliers
    "hold":       "chd_military_hobgoblins",           # slave pens and stables
    "hull":       "chd_military_kdaai",                # war engines in the belly
    "sail":       "chd_factory_port",                  # canvas and speed
    "helm":       "chd_outpost_overseer_hut",          # who steers the slaves
    "anchor":     "chd_outpost_mine",                  # holding fast, and growth
}
SHIPWORKS_ICON = {"abnagg": "chd_factory_drill_workshop", "tordrek": "chd_factory_furnace"}

# effect -> scope. Every pair below is attested in vanilla building_effects_junction,
# including corruption_chaos_buildings at force_to_character_own_provincetext (9 rows),
# which is the horde-building scope VC uses for its own corruption row.
SCOPE = {
    "wh_main_effect_force_all_recruitment_points": "force_to_force_own",
    "wh_main_effect_force_all_campaign_upkeep": "force_to_force_own",
    "wh_main_effect_force_all_campaign_replenishment_rate": "force_to_force_own",
    "wh_main_effect_force_all_campaign_movement_range": "force_to_force_own",
    "wh_main_effect_agent_action_outcome_parent_army_xp_gain_factionwide": "force_to_force_own",
    "wh3_main_effect_corruption_chaos_buildings": "force_to_character_own_provincetext",
}
RECRUIT = "wh_main_effect_force_all_recruitment_points"
UPKEEP = "wh_main_effect_force_all_campaign_upkeep"

# level -> [(effect, value)]. Added to whatever the level already has (flagship and
# anchor already carry hordebuilding_growth_core from Phases 2/16 - not repeated here).
ADD = {}
for lvl, (pts, upk) in enumerate([(2, 0), (3, -5), (4, -10), (5, -15), (6, -20)], 1):
    ADD["flagship_%d" % lvl] = [(RECRUIT, pts)] + ([(UPKEEP, upk)] if upk else [])
for lvl, (rep, pts) in enumerate([(4, 2), (6, 4), (8, 6)], 1):
    ADD["hull_%d" % lvl] = [("wh_main_effect_force_all_campaign_replenishment_rate", rep),
                            (RECRUIT, pts)]
for lvl, mv in enumerate([10, 20, 30], 1):
    ADD["sail_%d" % lvl] = [("wh_main_effect_force_all_campaign_movement_range", mv)]
for lvl, (upk, corr) in enumerate([(-5, 4), (-10, 6), (-15, 8)], 1):
    ADD["helm_%d" % lvl] = [(UPKEEP, upk),
                            ("wh3_main_effect_corruption_chaos_buildings", corr)]
for lvl, xp in enumerate([20, 40, 80], 1):
    ADD["anchor_%d" % lvl] = [
        ("wh_main_effect_agent_action_outcome_parent_army_xp_gain_factionwide", xp)]


def read(name):
    path = os.path.join(SRC, "%s__%s.tsv" % (name, P))
    with open(path, encoding="utf-8") as f:
        lines = f.read().rstrip("\n").split("\n")
    return path, lines[0].split("\t"), lines[1], [l.split("\t") for l in lines[2:]]


def write(path, cols, meta, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(["\t".join(cols), meta] + ["\t".join(r) for r in rows]) + "\n")
    return len(rows)


def icons():
    path, cols, meta, rows = read("building_culture_variants_tables")
    b, i = cols.index("building"), cols.index("icon")
    for r in rows:
        name = r[b]
        if name.startswith(P + "_"):
            chain = name[len(P) + 1:].rsplit("_", 1)[0]
            r[i] = ICONS[chain]
        else:                                            # derpy_chd_naval_shipworks_<lord>_1
            r[i] = SHIPWORKS_ICON[name.rsplit("_", 2)[-2]]
    assert not any(r[i].startswith("cst_") for r in rows), "a Vampire Coast icon survived"
    return write(path, cols, meta, rows)


def effects():
    path, cols, meta, rows = read("building_effects_junction_tables")
    b, e, s = cols.index("building"), cols.index("effect"), cols.index("effect_scope")
    v, vd, vr = (cols.index(c) for c in ("value", "value_damaged", "value_ruined"))
    have = set((r[b], r[e]) for r in rows)
    for suffix in sorted(ADD):
        level = "%s_%s" % (P, suffix)
        for eff, val in ADD[suffix]:
            assert (level, eff) not in have, "%s already has %s" % (level, eff)
            row = [""] * len(cols)
            row[b], row[e], row[s] = level, eff, SCOPE[eff]
            # value_damaged mirrors value, matching this fragment's existing rows
            row[v] = row[vd] = "%.1f" % val
            row[vr] = "0.0"
            rows.append(row)
            have.add((level, eff))
    assert len(have) == len(rows), "duplicate (building, effect) combined key"
    return write(path, cols, meta, rows)


if __name__ == "__main__":
    print("building_culture_variants_tables  %d rows" % icons())
    print("building_effects_junction_tables  %d rows" % effects())
