"""Tordrek's Vampire Coast skill buffs - red line nodes and special-line effects.

The Black Kraken Armada recruits 25 Vampire Coast units (see
docs/sessions/HANDOFF_20260901_NAVAL_HORDE_ROSTER.md section 8), and nothing in Tordrek's skill
tree touched them. This adds:

  red line   - CA's own ten Vampire Coast army skills (wh2_dlc11_skill_cst_army_1..6 and
               _8..11) as ten new nodes on indent 4, tiers 13-22, in derpy_tordrek_skills
               ONLY. Zero new skills, effects, loc or unit sets - every one of those skills
               already exists with art and text, and every one of their effects was measured
               to hit units actually on the kraken.
  special    - Vampire Coast unit-set effects folded into three skills Tordrek already has:
               the always-taken root and two of the three mutually exclusive capstones.

Reads and rewrites the EXPORTED TSVs in place, then imports them back, because import_tsv
replaces the whole file. Idempotent: a row already present is not added twice.

    py tools/gen_tordrek_vc_skills.py            # export, edit, check, import, save
    py tools/gen_tordrek_vc_skills.py --check    # export and edit only, no write
    py tools/gen_tordrek_vc_skills.py --selftest

Needs RPFM open (the MCP server only exists while it is).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_house_ancillaries import call, check_keys      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "Modding Files", "source", "tordrek_vc_skills", "export")
PACK = os.path.join(ROOT, "Modding Files", "Modpacks",
                    "!aa_derpy_hashut_legendary_lords.pack")

SET = "derpy_tordrek_skills"
LANE = 4                      # the red / army lane, same one derpy_shared_army_* sits in
FIRST_TIER = 13               # 0-12 are the Chaos Dwarf half, already full

# (node suffix, CA skill, parent node). The parents mirror the Chaos Dwarf half exactly:
# the six base skills hang off the lane's root, the four rank-7 ones off its mid gate.
RED = [
    (1,  "wh2_dlc11_skill_cst_army_1",  "derpy_shared_army_0"),   # Held Together by Screws
    (2,  "wh2_dlc11_skill_cst_army_2",  "derpy_shared_army_0"),   # Reanimated Marksman
    (3,  "wh2_dlc11_skill_cst_army_3",  "derpy_shared_army_0"),   # Black Powder Overload
    (4,  "wh2_dlc11_skill_cst_army_4",  "derpy_shared_army_0"),   # Rotten Death
    (5,  "wh2_dlc11_skill_cst_army_5",  "derpy_shared_army_0"),   # Haunting Horror
    (6,  "wh2_dlc11_skill_cst_army_6",  "derpy_shared_army_0"),   # Drowned & Bound
    (7,  "wh2_dlc11_skill_cst_army_8",  "derpy_shared_army_2"),   # Deadly March
    (8,  "wh2_dlc11_skill_cst_army_9",  "derpy_shared_army_2"),   # Ensorcelled Weapons
    (9,  "wh2_dlc11_skill_cst_army_10", "derpy_shared_army_2"),   # Masterly Splicing
    (10, "wh2_dlc11_skill_cst_army_11", "derpy_shared_army_2"),   # Hardened by Death
]

E = "wh2_dlc11_effect_force_stat_"
SCOPE = "general_to_force_own"

# Only skills that are actually reachable get these. derpy_tordrek_4_1/4_2/4_3 are all-pairs
# locked, so a buff on one alone would collapse the choice; 4_2 is left out because its own
# force-wide magic resistance already covers the drowned.
SPECIAL = [
    # Submersible Engineering - the root, always taken. Hull plate for the crew.
    ("derpy_tordrek_1",   1, E + "armour_cst_melee_infantry",        10.0),
    ("derpy_tordrek_1",   1, E + "magic_resistance_cst_infantry",     5.0),
    # The Black Kraken Surfaces - what comes up from below.
    ("derpy_tordrek_4_1", 1, E + "weapon_strength_cst_large_units",  12.0),
    ("derpy_tordrek_4_1", 1, E + "charge_bonus_add_cst_monsters",    10.0),
    # Crew of the Drowned - the drowned themselves.
    ("derpy_tordrek_4_3", 1, E + "melee_attack_cst_melee_infantry",   8.0),
    ("derpy_tordrek_4_3", 1, E + "leadership_cst_infantry",           8.0),
    ("derpy_tordrek_4_3", 1, E + "melee_defence_cst_melee_infantry",  6.0),
]

NODES = "db/character_skill_nodes_tables/derpy_chd_ll_custom"
ITEMS = "db/character_skill_node_set_items_tables/derpy_chd_ll_custom"
LINKS = "db/character_skill_node_links_tables/derpy_chd_unique_skills"
FX = "db/character_skill_level_to_effects_junctions_tables/derpy_chd_ll_unique_skills"


def node_key(n):
    return "derpy_tordrek_drowned_%d" % n


def pack_paths(table):
    """Every fragment of `table` in the pack. Read straight off disk - no RPFM needed."""
    from read_pack_index import paths
    return [p for p in paths(PACK) if p.startswith("db/%s/" % table)]


def read(path):
    """(header, meta, rows) of an exported TSV. RPFM writes header then a `#table;ver;path`."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    return lines[0].split("\t"), lines[1], [ln.split("\t") for ln in lines[2:]]


def write(path, header, meta, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(header) + "\n" + meta + "\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")


def add(header, rows, want, key_cols):
    """Append `want` dicts as rows, skipping any whose key columns already appear."""
    seen = {tuple(r[header.index(c)] for c in key_cols) for r in rows}
    added = 0
    for d in want:
        k = tuple(d[c] for c in key_cols)
        if k in seen:
            continue
        seen.add(k)
        rows.append([d.get(c, "") for c in header])
        added += 1
    return added


def edit(files):
    """files: {label: (path, header, meta, rows)}. Mutates rows in place, returns counts."""
    out = {}

    hdr, rows = files["nodes"][1], files["nodes"][3]
    out["nodes"] = add(hdr, rows, [
        {"key": node_key(n), "campaign_key": "", "character_skill_key": sk, "faction_key": "",
         "indent": str(LANE), "tier": str(FIRST_TIER + n - 1), "subculture": "",
         "points_on_creation": "0", "required_num_parents": "0", "visible_in_ui": "true"}
        for n, sk, _p in RED], ["key"])

    hdr, rows = files["items"][1], files["items"][3]
    out["items"] = add(hdr, rows, [
        {"set": SET, "item": node_key(n), "mod_disabled": "false"}
        for n, _sk, _p in RED], ["set", "item"])

    hdr, rows = files["links"][1], files["links"][3]
    out["links"] = add(hdr, rows, [
        {"child_key": node_key(n), "parent_key": p, "initial_descent_tiers": "0",
         "parent_link_position": "1", "child_link_position": "1",
         "parent_link_position_offset": "0.0000", "child_link_position_offset": "0.0000",
         "link_type": "REQUIRED"}
        for n, _sk, p in RED], ["child_key", "parent_key"])

    hdr, rows = files["fx"][1], files["fx"][3]
    # Drop Vampire Coast rows this generator wrote on a previous run and no longer owns, so
    # editing SPECIAL converges instead of accumulating. Only our own skills, only wh2_dlc11
    # effects - nothing else in the file is touched.
    mine = {sk for sk, _l, _e, _v in SPECIAL}
    want = {(sk, e) for sk, _l, e, _v in SPECIAL}
    isk, ifx = hdr.index("character_skill_key"), hdr.index("effect_key")
    stale = [r for r in rows if r[isk] in mine and r[ifx].startswith("wh2_dlc11_")
             and (r[isk], r[ifx]) not in want]
    for r in stale:
        rows.remove(r)
        print("  -    dropped %s / %s" % (r[isk], r[ifx]))
    out["fx"] = add(hdr, rows, [
        {"character_skill_key": sk, "effect_key": fx, "level": str(lvl),
         "effect_scope": SCOPE, "value": "%.4f" % val}
        for sk, lvl, fx, val in SPECIAL], ["character_skill_key", "effect_key", "level"])
    return out


def check_reach(minimum=3):
    """Every special-line effect must reach units the kraken can actually build.

    An effect bound to a rank-gated unit set (unit_sets.use_unit_exp_level_range) does nothing
    below that rank, and one bound to RoR-only sets does nothing at all here - both render a
    full tooltip either way. wh2_dlc11_effect_force_stat_speed_cst_monsters_rank7 shipped in
    this list once and was caught by exactly this: its only ungated sets are RoR variants.

    The red line is deliberately exempt - army_8..11 ARE CA's rank-7 capstones and the Chaos
    Dwarf half of the same lane is rank-gated in the same way.
    """
    import collections
    from read_vanilla_cache import load
    import gen_naval_horde_tordrek as horde

    sets = {r["key"]: r for r in load("unit_sets")[0]}
    binds = collections.defaultdict(set)
    for r in load("effect_bonus_value_ids_unit_sets")[0]:
        binds[r["effect"]].add(r["unit_set"])
    members = collections.defaultdict(set)
    for r in load("unit_set_to_unit_junctions")[0]:
        if not r["exclude"] and r["unit_record"]:
            members[r["unit_set"]].add(r["unit_record"])
    roster = {u for _b, u in horde.build() if u.startswith("wh2_dlc11_cst_")}

    for sk, _lvl, e, _v in SPECIAL:
        assert e in binds, "%s is bound to no unit set at all" % e
        reach = set()
        for st in binds[e]:
            if sets.get(st, {}).get("use_unit_exp_level_range"):
                continue
            reach |= members.get(st, set())
        hit = reach & roster
        assert len(hit) >= minimum, (
            "%s on %s reaches only %d ungated kraken unit(s): %s"
            % (e, sk, len(hit), sorted(hit)))
        print("      %-56s %2d units" % (e.replace("wh2_dlc11_effect_force_stat_", ""),
                                         len(hit)))


def dicts(header, rows):
    return [dict(zip(header, r)) for r in rows]


def check(files, siblings=None):
    """Fails loudly on the faults this shape can introduce.

    `siblings` is {"nodes": [dict...], "items": [dict...]} from the OTHER fragments of those
    two tables in the same pack. Without them the cell and duplicate-skill checks see only
    derpy_chd_ll_custom and would miss a collision with the Chaos Dwarf half of the same lane,
    which lives in derpy_chd_ll_shared.
    """
    siblings = siblings or {"nodes": [], "items": []}
    nodes = dicts(files["nodes"][1], files["nodes"][3]) + siblings["nodes"]
    items_rows = dicts(files["items"][1], files["items"][3]) + siblings["items"]
    links = dicts(files["links"][1], files["links"][3])
    fx = dicts(files["fx"][1], files["fx"][3])

    mine = [r for r in nodes if r["key"].startswith("derpy_tordrek_drowned_")]
    assert len(mine) == len(RED), "expected %d new nodes, found %d" % (len(RED), len(mine))

    items = {r["item"] for r in items_rows if r["set"] == SET}
    cells, skills = {}, {}
    for r in nodes:
        if r["key"] not in items:
            continue
        cell = (r["indent"], r["tier"])
        assert cell not in cells, "two nodes on cell %s: %s and %s" % (
            cell, cells[cell], r["key"])
        cells[cell] = r["key"]
        sk = r["character_skill_key"]
        assert sk not in skills, "skill %s on two nodes in %s: %s and %s" % (
            sk, SET, skills[sk], r["key"])
        skills[sk] = r["key"]

    # A parent outside the set is a node nothing can ever unlock.
    for r in links:
        if not r["child_key"].startswith("derpy_tordrek_drowned_"):
            continue
        assert r["child_key"] in items, "%s is linked but not in %s" % (r["child_key"], SET)
        assert r["parent_key"] in items,             "%s's parent %s is outside %s" % (r["child_key"], r["parent_key"], SET)

    touched = {r["character_skill_key"] for r in fx}
    for sk, _l, _f, _v in SPECIAL:
        assert sk in touched, "%s has no effect rows at all" % sk
        assert fx, "no effect rows at all"
    for _sk, _l, e, _v in SPECIAL:
        assert e.startswith("wh2_dlc11_"), "%s is not a Vampire Coast effect" % e


def selftest():
    """Break each fault in memory and confirm check() catches it."""
    def files_of(nodes, items, links, fx):
        return {"nodes": ("", ["key", "campaign_key", "character_skill_key", "faction_key",
                               "indent", "tier", "subculture", "points_on_creation",
                               "required_num_parents", "visible_in_ui"], "", nodes),
                "items": ("", ["set", "item", "mod_disabled"], "", items),
                "links": ("", ["child_key", "parent_key", "initial_descent_tiers",
                               "parent_link_position", "child_link_position",
                               "parent_link_position_offset", "child_link_position_offset",
                               "link_type"], "", links),
                "fx": ("", ["character_skill_key", "effect_key", "level", "effect_scope",
                            "value"], "", fx)}

    SIB = {"nodes": [
        {"key": "derpy_shared_army_0", "character_skill_key": "root_skill",
         "indent": "4", "tier": "0"},
        {"key": "derpy_shared_army_2", "character_skill_key": "gate_skill",
         "indent": "4", "tier": "7"}],
        "items": [{"set": SET, "item": "derpy_shared_army_0"},
                  {"set": SET, "item": "derpy_shared_army_2"}]}

    def base():
        f = files_of([], [], [], [])
        edit(f)
        return f

    ok = base()
    check(ok, SIB)

    for name, breaker in [
        ("occupied cell", lambda f: f["nodes"][3].append(
            ["squatter", "", "other", "", "4", "13", "", "0", "0", "true"])),
        ("duplicate skill", lambda f: f["nodes"][3].append(
            ["twin", "", "wh2_dlc11_skill_cst_army_1", "", "4", "99", "", "0", "0", "true"])),
        ("parent outside set", lambda f: f["links"][3].append(
            ["derpy_tordrek_drowned_1", "somewhere_else", "0", "1", "1",
             "0.0000", "0.0000", "REQUIRED"])),
        ("non-VC effect", lambda f: SPECIAL.append(
            ("derpy_tordrek_1", 1, "wh_main_effect_force_stat_armour", 5.0))),
    ]:
        f = base()
        if name in ("occupied cell", "duplicate skill"):
            breaker(f)
            f["items"][3].append(["derpy_tordrek_skills",
                                  f["nodes"][3][-1][0], "false"])
        else:
            breaker(f)
        try:
            check(f, SIB)
        except AssertionError:
            print("  caught: %s" % name)
        else:
            raise SystemExit("SELFTEST FAILED: %s not caught" % name)
        if name == "non-VC effect":
            SPECIAL.pop()
    print("selftest ok")


def main():
    if "--selftest" in sys.argv:
        return selftest()

    call("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False})
    os.path.isdir(EXP) or os.makedirs(EXP)
    pack = call("open_packfiles", {"paths": [PACK]})["StringContainerInfo"][0]

    files = {}
    for label, path in (("nodes", NODES), ("items", ITEMS),
                        ("links", LINKS), ("fx", FX)):
        tsv = os.path.join(EXP, path.rsplit("/", 1)[0].split("/")[1] + "__" +
                           path.rsplit("/", 1)[1] + ".tsv")
        call("export_tsv", {"pack_key": pack, "table_path": path, "tsv_path": tsv})
        header, meta, rows = read(tsv)
        files[label] = (tsv, header, meta, rows)

    # The other fragments of the same two tables, read-only. Tordrek's set spans four of
    # them; without these the cell check would not see the Chaos Dwarf half of the lane.
    ref = os.path.join(EXP, "ref")
    os.path.isdir(ref) or os.makedirs(ref)
    siblings = {"nodes": [], "items": []}
    for label, table in (("nodes", "character_skill_nodes_tables"),
                         ("items", "character_skill_node_set_items_tables")):
        for frag in sorted(pack_paths(table)):
            if frag in (NODES, ITEMS):
                continue
            tsv = os.path.join(ref, frag.replace("/", "__") + ".tsv")
            call("export_tsv", {"pack_key": pack, "table_path": frag, "tsv_path": tsv})
            h, _m, rows = read(tsv)
            siblings[label] += dicts(h, rows)
    print("  siblings: %d nodes, %d set items" % (len(siblings["nodes"]),
                                                  len(siblings["items"])))

    check_reach()
    added = edit(files)
    check(files, siblings)
    for label, (tsv, header, meta, rows) in files.items():
        write(tsv, header, meta, rows)
        print("  +%-3d -> %-4d  %s" % (added[label], len(rows), os.path.basename(tsv)))

    if "--check" in sys.argv:
        return print("\n--check: nothing written to the pack")

    plan = []
    for label, path in (("nodes", NODES), ("items", ITEMS), ("links", LINKS), ("fx", FX)):
        # RPFM pads the meta line with trailing tabs out to the column count.
        table, ver, dest = files[label][2].split("	")[0][1:].split(";")
        plan.append((dest, {"DB": [dest.rsplit("/", 1)[1], table, int(ver)]},
                     os.path.basename(files[label][0]), EXP))
    check_keys(plan)

    for dest, spec, fn, d in plan:
        call("import_tsv", {"pack_key": pack, "table_path": dest,
                            "tsv_path": os.path.join(d, fn)})
    call("save_packfile", {"pack_key": pack})
    print("\nsaved %s" % PACK)


if __name__ == "__main__":
    main()
