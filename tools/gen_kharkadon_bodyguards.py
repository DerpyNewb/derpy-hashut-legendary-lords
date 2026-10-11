"""Kharkadon's four bodyguard options for the Hashut's Legendary Lords pack.

Spec: docs/superpowers/specs/2026-10-06-kharkadon-bodyguards-design.md

Each option is a mount-category ancillary whose `provided_bodyguard_unit` is a clone of a Chaos
Dwarf infantry unit: half the men, twice the health per man, Kharkadon in it as an
`additional_officer` at half his solo health. A skill of the same key grants the ancillary at a
level, in the mount format, and character_skills_to_level_reached_criterias learns that skill for him free
at the same rank (CA's route for Tomb Kings mounts). Everything is derived from CA's db.pack and the lords pack, nothing typed twice:

    py tools/gen_kharkadon_bodyguards.py --fetch-headers   once: RPFM's own column order per table
    py tools/gen_kharkadon_bodyguards.py                   build TSVs + run every check, write nothing bad
    py tools/gen_kharkadon_bodyguards.py --import          then import into the lords pack, save, verify from disk
    py tools/gen_kharkadon_bodyguards.py --selftest        prove each check fails on broken input

The pack worked on is Modding Files/Modpacks/!aa_derpy_hashut_legendary_lords.pack; sync it from
the Workshop copy first (the Workshop copy is the live one) and deploy back after.
"""
import copy
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import read_vanilla_db as rvd                                  # noqa: E402
from read_pack_index import entries, paths                     # noqa: E402

OUT = os.path.join(ROOT, "Modding Files", "source", "kharkadon_bodyguards")
PACK = os.path.join(ROOT, "Modding Files", "Modpacks", "!aa_derpy_hashut_legendary_lords.pack")
GAME = r"F:\SteamLibrary\steamapps\common\Total War WARHAMMER III\data"
FRAG = "derpy_kharkadon_bodyguards"
LOC_PATH = "text/%s.loc" % FRAG

LORD = "derpy_kharkadon"
LORD_NAME = "Kharkadon the Vicious"
NODE_SET = "derpy_kharkadon_skills"
OVERSEER = "wh3_dlc23_chd_cha_overseer"          # his solo entity; CA's row, shared, never edited
ANIM = "derpy_kharkadon"
SKILL_ICON = "wh3_dlc29_hero_passive_sworn_bodyguard.png"
# CA's generic armour slot art (type wh_main_anc_armour); the unit card it replaced was 60x130 blown up.
ICON = "ui/skins/default/equipment_items_armour.png"
# Does the clone's bonus_hit_points also land on the officer entity? Every entity of an ordinary
# unit gets it, so yes until the game says otherwise (spec open question 1). One flag, one cell.
STACKS_BONUS = True
# Unit sets the clone must NOT inherit from its base: multiplayer caps count it as a recruit, and the
# all-RoR set would treat an unrecruitable lord's unit as a Regiment of Renown.
NOT_SETS = re.compile(r"^mp_cap_|^wh2_main_ror_units_all$")
# Per-man stats are the base unit's; these must equal the base on every clone (the spec's section 3).
KEEP = ["armour", "melee_attack", "melee_defence", "morale", "charge_bonus", "shield", "primary_melee_weapon",
        "primary_missile_weapon", "spacing", "rank_depth", "man_entity", "man_animation", "training_level"]

OPTIONS = [
    dict(opt="warriors", base="wh3_dlc23_chd_inf_chaos_dwarf_warriors", rank=8, tier=22,
         title="Warrior Bodyguard", what="Chaos Dwarf Warriors", plural="Chaos Dwarf Warriors",
         lore="The household axemen, shield to shield, who go where the Overlord goes."),
    dict(opt="infernal_guard", base="wh3_dlc23_chd_inf_infernal_guard", rank=15, tier=23,
         title="Infernal Bodyguard", what="Infernal Guard", plural="Infernal Guard",
         lore="The Infernal Guard stand where an overlord's word would otherwise have to be shouted."),
    dict(opt="ironsworn", base="wh3_dlc23_chd_inf_infernal_ironsworn", rank=25, tier=24,
         title="Ironsworn Bodyguard", what="Infernal Ironsworn", plural="Infernal Ironsworn",
         lore="Ironsworn take their oath on hot iron. Kharkadon makes sure none of them regrets it, or says so."),
    dict(opt="immortals", base="wh3_dlc23_chd_inf_infernal_ironsworn_ror", rank=32, tier=25,
         title="Immortal Bodyguard", what="The Immortals", plural="Immortals",
         lore="The Immortals have outlived every master but this one, and mean to outlive him too."),
]
for _o in OPTIONS:
    _o["key"] = "derpy_kharkadon_bg_" + _o["opt"]

TABLES = """land_units main_units land_units_to_unit_abilites_junctions unit_variants unit_set_to_unit_junctions
ui_unit_bullet_point_unit_overrides unit_banner_unit_height_offsets units_custom_battle_permissions
units_custom_battle_mounts units_to_groupings_military_permissions unit_attributes_groups
unit_attributes_to_groups_junctions battle_entities battle_entity_stats battle_personalities
land_units_to_battle_personalities_junctions ancillaries ancillary_types ancillary_info ancillaries_required_skills
ancillaries_included_agent_subtypes ancillary_to_included_agents character_skills character_skill_nodes
character_skill_node_set_items character_skill_level_details character_skill_level_to_ancillaries_junctions
character_skill_level_to_effects_junctions character_skill_utilization_hints_junctions effects
character_skills_to_level_reached_criterias""".split()

HDR_JSON = os.path.join(OUT, "headers.json")


# ------------------------------------------------------------------------------------------ reading
_cache = {}


def rows(pack, table):
    """[row dict] of one table across every fragment of a pack; row['__ver'] and row['__frag'] say where from."""
    k = (pack, table)
    if k not in _cache:
        out = []
        for path, ver, rs in rvd.load(pack, table + "_tables"):
            out += [dict(x, __ver=ver, __frag=path.split("/")[-1]) for x in rs]
        _cache[k] = out
    return [dict(x) for x in _cache[k]]


def by(rs, col):
    return {x[col]: x for x in rs}


def where(rs, **kv):
    return [x for x in rs if all(x[k] == v for k, v in kv.items())]


def lords(table):
    return rows(PACK, table)


def vanilla(table):
    return rows(rvd.DB_PACK, table)


def one(rs, what):
    assert len(rs) == 1, "%s: expected one row, got %d" % (what, len(rs))
    return rs[0]


# ------------------------------------------------------------------------------------------ build
def derive(o):
    """The numbers of one option, from the base rows. Returns a dict, never writes."""
    lu = one(where(vanilla("land_units"), key=o["base"]), "land_units " + o["base"])
    mu = one(where(vanilla("main_units"), unit=o["base"]), "main_units " + o["base"])
    ent = one(where(vanilla("battle_entities"), key=lu["man_entity"]), "entity " + lu["man_entity"])
    solo = one(where(vanilla("battle_entities"), key=OVERSEER), "overseer")["hit_points"] + \
        one(where(lords("land_units"), key=LORD), "lord land unit")["bonus_hit_points"]
    base_hp = ent["hit_points"] + lu["bonus_hit_points"]
    bonus = 2 * base_hp - ent["hit_points"]
    half = solo // 2
    return dict(lu=lu, mu=mu, men=mu["num_men"] // 2, base_hp=base_hp, bonus=bonus,
                solo=solo, officer_total=half,
                officer_hp=half - (bonus if STACKS_BONUS else 0))


def build():
    """({table: [row dict]}, {loc key: text}) for the whole fragment."""
    T = {t: [] for t in TABLES}
    loc = {}
    k_lu = one(where(lords("land_units"), key=LORD), "lord land unit")
    k_mu = one(where(lords("main_units"), unit=LORD), "lord main unit")
    mount = one(where(lords("ancillaries"), key="derpy_ghorth_great_taurus"), "mount ancillary donor")
    k_perm = one(where(lords("units_custom_battle_permissions"), unit=LORD), "lord custom battle row")
    from gen_new_house_lords import custom_battle_portrait
    k_perm["general_portrait"] = custom_battle_portrait(LORD)
    k_grp = one(where(lords("units_to_groupings_military_permissions"), unit=LORD), "lord military group")
    k_att = [x["attribute"] for x in where(lords("unit_attributes_to_groups_junctions"),
                                           attribute_group=k_lu["attribute_group"])]
    v_abil, v_sets = vanilla("land_units_to_unit_abilites_junctions"), vanilla("unit_set_to_unit_junctions")
    v_bul, v_banner = vanilla("ui_unit_bullet_point_unit_overrides"), vanilla("unit_banner_unit_height_offsets")
    v_att = vanilla("unit_attributes_to_groups_junctions")
    v_uv = vanilla("unit_variants")
    overseer = one(where(vanilla("battle_entities"), key=OVERSEER), "overseer")
    k_abil = [x for x in where(lords("land_units_to_unit_abilites_junctions"), land_unit=LORD)
              if x["ability"] != "wh3_main_unit_passive_single_entity"]   # a 50-man unit is not a single entity
    k_sets = where(lords("unit_set_to_unit_junctions"), unit_record=LORD)
    k_bul = where(lords("ui_unit_bullet_point_unit_overrides"), unit_key=LORD)

    T["battle_entity_stats"].append(dict(key="derpy_kharkadon_officer", primary_melee_weapon=LORD,
                                         primary_missile_weapon=""))
    for o in OPTIONS:
        C, B, d = o["key"], o["base"], derive(o)
        o["d"] = d
        what = o["what"]
        # unit: the base's per-man stats, the lord's identity
        lu = dict(d["lu"], key=C, **{"class": "com"})
        lu.update(bonus_hit_points=d["bonus"], campaign_action_points=k_lu["campaign_action_points"],
                  historical_description_text=k_lu["historical_description_text"],
                  short_description_text=k_lu["short_description_text"],
                  selection_vo=k_lu["selection_vo"], selected_vo_secondary=k_lu["selected_vo_secondary"],
                  selected_vo_tertiary=k_lu["selected_vo_tertiary"], ai_usage_group=k_lu["ai_usage_group"],
                  attribute_group=C + "_att")
        T["land_units"].append(lu)
        mu = dict(k_mu, unit=C, land_unit=C, num_men=d["men"], melee_cp=d["mu"]["melee_cp"] / 2)
        T["main_units"].append(mu)
        for a in {(x["ability"], x["culture"]) for x in k_abil} | \
                {(x["ability"], x["culture"]) for x in where(v_abil, land_unit=B)}:
            T["land_units_to_unit_abilites_junctions"].append(dict(ability=a[0], land_unit=C, culture=a[1]))
        vu = one(where(v_uv, unit=B), "unit_variants " + B)
        T["unit_variants"].append(dict(faction="", unit=C, name=C, variant=vu["variant"], unit_card="placeholder"))
        seen = set()
        for x in k_sets + [s for s in where(v_sets, unit_record=B) if not NOT_SETS.search(s["unit_set"])]:
            if x["unit_set"] not in seen:
                seen.add(x["unit_set"])
                T["unit_set_to_unit_junctions"].append(dict(x, unit_record=C))
        for b in sorted({x["bullet_point"] for x in k_bul + where(v_bul, unit_key=B)}):
            T["ui_unit_bullet_point_unit_overrides"].append(dict(bullet_point=b, unit_key=C))
        T["unit_banner_unit_height_offsets"].append(dict(one(where(v_banner, unit_record=B), "banner " + B),
                                                         unit_record=C))
        T["units_custom_battle_permissions"].append(dict(k_perm, unit=C))
        T["units_custom_battle_mounts"].append(dict(base_unit=LORD, mounted_unit=C,
                                                    icon_name=ICON))
        T["units_to_groupings_military_permissions"].append(dict(k_grp, unit=C))
        T["unit_attributes_groups"].append(dict(group_name=C + "_att"))
        for a in sorted(set(k_att) | {x["attribute"] for x in where(v_att, attribute_group=d["lu"]["attribute_group"])}):
            T["unit_attributes_to_groups_junctions"].append(dict(attribute=a, attribute_group=C + "_att"))
        # Kharkadon inside the unit
        OC = "derpy_kharkadon_officer_" + o["opt"]
        T["battle_entities"].append(dict(overseer, key=OC, hit_points=d["officer_hp"]))
        T["battle_personalities"].append(dict(key=OC, man_animations_table=ANIM, variant=LORD, battle_entity=OC,
                                              battle_entity_stats="derpy_kharkadon_officer",
                                              autonomous_rider_hero=False, autonomous_rider_can_shoot_in_melee=False,
                                              can_only_be_used_by_draught=False))
        T["land_units_to_battle_personalities_junctions"].append(dict(
            battle_personality=OC, land_unit=C, attach="additional_officer", riders_attachment_point="",
            engine_articulation_index=-1, jettison_rider=False))
        # the item and the skill that grants it
        T["ancillaries"].append(dict(mount, key=C, type=C, provided_bodyguard_unit=C))
        T["ancillary_types"].append(dict(type=C, ui_icon=ICON))
        T["ancillary_info"].append(dict(ancillary=C))
        T["ancillaries_required_skills"].append(dict(ancillary=C, required_skill=C, required_skill_level=1))
        T["ancillaries_included_agent_subtypes"].append(dict(agent_subtype=LORD, ancillary=C))
        T["ancillary_to_included_agents"].append(dict(ancillary=C, agent="general"))
        desc = "%s In battle Kharkadon leads %d %s, each twice as tough as the usual kind. He fights among " \
               "them with half his own health." % (o["lore"], d["men"], o["plural"])
        T["character_skills"].append(dict(key=C, image_path=SKILL_ICON, localised_description=desc,
                                          localised_name=o["title"], unlocked_at_rank=0, is_background_skill=False,
                                          is_female_only_background_skill=False, is_male_only_background_skill=False,
                                          background_weighting=0.0, influence_cost=0))
        T["character_skill_nodes"].append(dict(key=C, campaign_key="", character_skill_key=C, faction_key="",
                                               indent=0, tier=o["tier"], subculture="", points_on_creation=0,
                                               required_num_parents=0, visible_in_ui=True))
        T["character_skill_node_set_items"].append(dict(set=NODE_SET, item=C, mod_disabled=False))
        T["character_skill_level_details"].append(dict(campaign_key="", faction_key="", level=1, skill_key=C,
                                                       subculture_key="", image_path="x", unlocked_at_rank=o["rank"]))
        T["character_skill_level_to_ancillaries_junctions"].append(dict(granted_ancillary=C, skill=C, level=1))
        # learned free on reaching the rank - CA's own route for Tomb Kings mounts (Arkhan's steed at 6)
        T["character_skills_to_level_reached_criterias"].append(dict(character_skill=C, character_level=o["rank"],
                                                                     upgrade_to_skill_level=1))
        T["character_skill_level_to_effects_junctions"].append(dict(character_skill_key=C, effect_key=C, level=0,
                                                                    effect_scope="character_to_character_own",
                                                                    value=1.0))
        T["character_skill_utilization_hints_junctions"].append(dict(hint="USEFUL_ALWAYS", key=C))
        T["effects"].append(dict(effect=C, icon="mount.png", priority=50, icon_negative="mount.png",
                                 category="both", is_positive_value_good=True))
        loc.update({
            "effects_description_" + C: "Grants bodyguard: " + what,
            "units_custom_battle_permissions_override_name_%s%strue" % (C, k_perm["faction"]): "",
            "units_custom_battle_mounts_mount_name_%s%s" % (LORD, C): o["title"],
            "units_custom_battle_mounts_localised_description_%s%s" % (LORD, C): o["lore"],
            "ancillaries_onscreen_name_" + C: o["title"], "ancillaries_colour_text_" + C: desc,
            "ancillaries_explanation_text_" + C: "",
            "character_skills_localised_name_" + C: o["title"], "character_skills_localised_description_" + C: desc,
            "land_units_onscreen_name_" + C: LORD_NAME, "land_units_concealed_name_" + C: ""})
    for t in T:
        T[t] = [{k: v for k, v in r.items() if not k.startswith("__")} for r in T[t]]
    return T, loc


# ------------------------------------------------------------------------------------------ output
def headers():
    if not os.path.exists(HDR_JSON):
        raise SystemExit("no %s - run with --fetch-headers (needs RPFM open)" % HDR_JSON)
    return json.load(open(HDR_JSON, encoding="utf-8"))


def fetch_headers():
    from import_house_ancillaries import call
    versions = {t: one(vanilla_ver(t), t) for t in TABLES}
    call("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False})
    pack = call("new_pack", {})["String"]
    tmp = tempfile.mkdtemp()
    out = {}
    for t, v in versions.items():
        path = "db/%s_tables/probe" % t
        call("new_packed_file", {"pack_key": pack, "path": path,
                                 "new_file": json.dumps({"DB": ["probe", t + "_tables", v]})})
        dst = os.path.join(tmp, t + ".tsv")
        call("export_tsv", {"pack_key": pack, "table_path": path, "tsv_path": dst})
        hdr, meta = open(dst, encoding="utf-8").read().split("\n")[:2]
        out[t] = dict(ver=v, cols=hdr.split("\t"), meta=meta)
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(HDR_JSON, "w", encoding="utf-8"), indent=1)
    print("headers for %d tables -> %s" % (len(out), HDR_JSON))


def vanilla_ver(t):
    return [x for x in {r["__ver"] for r in vanilla(t)}]


def fmt(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return "%.4f" % v
    return str(v)


def table_tsv(t, rs, H):
    h = H[t]
    body = []
    for r in rs:
        extra = set(r) - set(h["cols"])
        missing = set(h["cols"]) - set(r)
        assert not extra and not missing, "%s: extra %s missing %s" % (t, sorted(extra), sorted(missing))
        body.append("\t".join(fmt(r[c]) for c in h["cols"]))
    meta = h["meta"].replace("/probe", "/" + FRAG)
    return "\n".join(["\t".join(h["cols"]), meta] + body) + "\n"


def loc_tsv(loc):
    return "\n".join(["key\ttext\ttooltip", "#Loc;1;%s\t\t" % LOC_PATH] +
                     ["%s\t%s\tfalse" % (k, v) for k, v in loc.items()]) + "\n"


def write_all(T, loc, H):
    if os.path.isdir(OUT):
        for f in os.listdir(OUT):
            if f != "headers.json":
                p = os.path.join(OUT, f)
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    plan = []
    for t in TABLES:
        d = os.path.join(OUT, "db", t + "_tables")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, FRAG + ".tsv"), "w", encoding="utf-8", newline="\n").write(table_tsv(t, T[t], H))
        plan.append(("db/%s_tables/%s" % (t, FRAG), {"DB": [FRAG, t + "_tables", H[t]["ver"]]}, FRAG + ".tsv", d,
                     len(T[t])))
    d = os.path.join(OUT, "text")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, FRAG + ".loc.tsv"), "w", encoding="utf-8", newline="\n").write(loc_tsv(loc))
    plan.append((LOC_PATH, {"Loc": FRAG}, FRAG + ".loc.tsv", d, len(loc)))
    return plan


# ------------------------------------------------------------------------------------------ checks
_ui = []


def ui_paths():
    if not _ui:
        import glob
        for p in glob.glob(GAME + r"\ui*.pack"):
            _ui.extend(x.lower() for x in paths(p))
    return set(_ui)


def check(T, loc, H):
    """[finding] - every rule the spec states, measured on the built rows, not on the code."""
    bad = []
    from gen_new_house_lords import custom_battle_portrait
    if any(r["general_portrait"] != custom_battle_portrait(LORD) for r in T["units_custom_battle_permissions"]):
        bad.append("bodyguards use the wrong custom battle portrait")
    for t in TABLES:
        for r in T[t]:
            if set(r) != set(H[t]["cols"]):
                bad.append("%s: columns differ from RPFM's header" % t)
                break
    # duplicated combined keys, from the schema
    from gen_new_house_lords import key_fields
    for t in TABLES:
        ks = key_fields(t + "_tables", H[t]["ver"])
        seen = set()
        for r in T[t]:
            ck = tuple(fmt(r[k]) for k in ks) if ks else tuple(fmt(r[c]) for c in H[t]["cols"])
            if ck in seen:
                bad.append("%s: duplicated key %s" % (t, "|".join(ck)))
            seen.add(ck)
    # our keys must not exist anywhere else: a clash would be silently shadowed or drop a row
    mine = {o["key"] for o in OPTIONS}
    for t, col in (("land_units", "key"), ("main_units", "unit"), ("ancillaries", "key"), ("character_skills", "key"),
                   ("character_skill_nodes", "key"), ("effects", "effect")):
        for pk in (PACK, rvd.DB_PACK):
            for r in rows(pk, t):
                if r[col] in mine and r.get("__frag") != FRAG:
                    bad.append("%s %s already exists in %s (%s)" % (t, r[col], os.path.basename(pk), r.get("__frag")))
    for o in OPTIONS:
        C, d = o["key"], o["d"]
        lu = one(where(T["land_units"], key=C), "clone " + C)
        base = d["lu"]
        for c in KEEP:
            if lu[c] != base[c]:
                bad.append("%s: %s is %r, base has %r" % (C, c, lu[c], base[c]))
        ent = one(where(vanilla("battle_entities"), key=base["man_entity"]), "ent")["hit_points"]
        if ent + lu["bonus_hit_points"] != 2 * (ent + base["bonus_hit_points"]):
            bad.append("%s: per-man health is not twice the base's" % C)
        mu = one(where(T["main_units"], unit=C), "main " + C)
        if mu["num_men"] * 2 != d["mu"]["num_men"]:
            bad.append("%s: %d men is not half of %d" % (C, mu["num_men"], d["mu"]["num_men"]))
        if lu["class"] != "com" or mu["land_unit"] != C:
            bad.append("%s: not a commander unit on its own key" % C)
        oc = one(where(T["battle_entities"], key="derpy_kharkadon_officer_" + o["opt"]), "officer entity")
        total = oc["hit_points"] + (lu["bonus_hit_points"] if STACKS_BONUS else 0)
        if total != d["solo"] // 2:
            bad.append("%s: officer total health %d is not half of %d" % (C, total, d["solo"]))
        j = one(where(T["land_units_to_battle_personalities_junctions"], land_unit=C), "junction")
        if j["attach"] != "additional_officer":
            bad.append("%s: Kharkadon is not an additional_officer" % C)
        a = one(where(T["ancillaries"], key=C), "ancillary")
        if a["provided_bodyguard_unit"] != C or a["category"] != "mount":
            bad.append("%s: ancillary does not provide the bodyguard unit" % C)
        if one(where(T["character_skill_level_details"], skill_key=C), "level").get("unlocked_at_rank") != o["rank"]:
            bad.append("%s: wrong unlock rank" % C)
        auto = one(where(T["character_skills_to_level_reached_criterias"], character_skill=C), "auto " + C)
        if auto["character_level"] != o["rank"] or auto["upgrade_to_skill_level"] != 1:
            bad.append("%s: not learned free at rank %d" % (C, o["rank"]))
        if one(where(T["character_skill_level_to_ancillaries_junctions"], skill=C), "grant")["granted_ancillary"] != C:
            bad.append("%s: the skill does not grant its ancillary" % C)
        node = one(where(T["character_skill_nodes"], key=C), "node " + C)
        if node["tier"] > 48 or node["indent"] != 0 or node["required_num_parents"] != 0:
            bad.append("%s: node tier %d indent %d parents %d (ceiling 48, root node)" %
                       (C, node["tier"], node["indent"], node["required_num_parents"]))
        for ico in (one(where(T["ancillary_types"], type=C), "type")["ui_icon"],):
            if ico.lower() not in ui_paths():
                bad.append("%s: icon %s is in no CA ui pack" % (C, ico))
        if "wh3_main_unit_passive_single_entity" in {x["ability"] for x in
                                                     where(T["land_units_to_unit_abilites_junctions"], land_unit=C)}:
            bad.append("%s: a 50-man unit carries the single-entity passive" % C)
        if any(NOT_SETS.search(x["unit_set"]) for x in where(T["unit_set_to_unit_junctions"], unit_record=C)):
            bad.append("%s: joined a set a lord's unit must not join" % C)
    if any(r["icon_name"] != ICON for r in T["units_custom_battle_mounts"]):
        bad.append("custom battle mount icon is not the armour icon")
    if "ui/campaign ui/skills/" + SKILL_ICON.lower() not in ui_paths():
        bad.append("skill icon %s is in no CA ui pack" % SKILL_ICON)
    # references the pack must already hold
    if not where(lords("battle_animations_table"), key=ANIM):
        bad.append("anim table %s is not in the lords pack" % ANIM)
    if not where(lords("variants"), variant_name=LORD):
        bad.append("variant %s is not in the lords pack" % LORD)
    if not where(lords("melee_weapons"), key=LORD):
        bad.append("weapon %s is not in the lords pack" % LORD)
    if not where(lords("character_skill_node_sets"), key=NODE_SET):
        bad.append("node set %s is not in the lords pack" % NODE_SET)
    if not where(vanilla("battle_entities"), key=OVERSEER):
        bad.append("entity %s is not vanilla" % OVERSEER)
    return bad


def selftest(T, loc, H):
    """Each rule above must fail when its subject is broken; a check nobody watched fail proves nothing."""
    assert not check(T, loc, H), "the clean build does not pass its own checks: %s" % check(T, loc, H)
    breaks = {
        "men": lambda t: t["main_units"][0].update(num_men=t["main_units"][0]["num_men"] + 1),
        "health": lambda t: t["land_units"][0].update(bonus_hit_points=t["land_units"][0]["bonus_hit_points"] + 1),
        "stat": lambda t: t["land_units"][1].update(melee_defence=1),
        "officer": lambda t: t["battle_entities"][2].update(hit_points=t["battle_entities"][2]["hit_points"] + 5),
        "attach": lambda t: t["land_units_to_battle_personalities_junctions"][0].update(attach="officer"),
        "rank": lambda t: t["character_skill_level_details"][3].update(unlocked_at_rank=1),
        "tier": lambda t: t["character_skill_nodes"][0].update(tier=49),
        "grant": lambda t: t["character_skill_level_to_ancillaries_junctions"][0].update(granted_ancillary="x"),
        "dupe": lambda t: t["effects"].append(dict(t["effects"][0])),
        "single": lambda t: t["land_units_to_unit_abilites_junctions"].append(
            dict(ability="wh3_main_unit_passive_single_entity", land_unit=OPTIONS[0]["key"], culture="*")),
        "capset": lambda t: t["unit_set_to_unit_junctions"].append(
            dict(t["unit_set_to_unit_junctions"][0], unit_set="mp_cap_unit_x")),
        "icon": lambda t: t["ancillary_types"][0].update(ui_icon="ui/units/icons/no_such_unit.png"),
        "column": lambda t: t["effects"][0].pop("icon"),
        "class": lambda t: t["land_units"][0].update(**{"class": "inf_mel"}),
        "portrait": lambda t: t["units_custom_battle_permissions"][0].update(general_portrait="old_overseer.png"),
        "cb_icon": lambda t: t["units_custom_battle_mounts"][0].update(icon_name="ui/units/icons/x.png"),
        "auto_rank": lambda t: t["character_skills_to_level_reached_criterias"][1].update(character_level=16),
        "auto_gone": lambda t: t["character_skills_to_level_reached_criterias"].pop(),
    }
    for name, brk in breaks.items():
        t = copy.deepcopy(T)
        brk(t)
        try:
            found = check(t, loc, H)
        except (AssertionError, KeyError):
            found = ["raised"]
        assert found, "breaking %r was not caught" % name
    print("selftest ok (%d breaks caught)" % len(breaks))


# ------------------------------------------------------------------------------------------ import
def snapshot(pack):
    """{path: md5 of the content past the per-save GUID}."""
    import hashlib
    f, es = entries(pack)
    out = {}
    for path, size, off, _c in es:
        f.seek(off)
        d = f.read(size)
        out[path.lower()] = hashlib.md5(d[80:] if path.startswith("db/") else d).hexdigest()
    f.close()
    return out


def do_import(plan):
    from import_house_ancillaries import call, check_keys
    call("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False})
    check_keys([e[:4] for e in plan])
    before = snapshot(PACK)
    try:
        call("close_pack", {"pack_key": PACK})
    except Exception:
        pass
    call("open_packfiles", {"paths": [PACK]})
    for path, spec, fn, d, n in plan:
        try:
            call("delete_packed_files", {"pack_key": PACK, "paths": json.dumps([{"File": path}])})
        except Exception:
            pass
        call("new_packed_file", {"pack_key": PACK, "path": path, "new_file": json.dumps(spec)})
        call("import_tsv", {"pack_key": PACK, "table_path": path, "tsv_path": os.path.join(d, fn)})
    call("save_packfile", {"pack_key": PACK})
    call("close_pack", {"pack_key": PACK})
    print("saved")
    # Verify the SAVED file, re-opened fresh, table by table.
    dest = tempfile.mkdtemp()
    call("open_packfiles", {"paths": [PACK]})
    call("extract_packed_files", {"pack_key": PACK, "export_as_tsv": True, "destination_path": dest,
         "source_paths": json.dumps({"PackFile": [{"File": e[0]} for e in plan]})})
    call("close_pack", {"pack_key": PACK})
    bad = 0
    for path, spec, fn, d, n in plan:
        got = open(os.path.join(dest, *path.split("/")) + ".tsv", encoding="utf-8").read().split("\n")[2:]
        want = open(os.path.join(d, fn), encoding="utf-8").read().split("\n")[2:]
        g = sorted(x.lower() for x in got if x.strip("\t"))
        w = sorted(x.lower() for x in want if x.strip("\t"))
        if g != w or len(w) != n:
            print("DIFF   %s  pack %d rows, built %d" % (path, len(g), n))
            bad += 1
    shutil.rmtree(dest, ignore_errors=True)
    after = snapshot(PACK)
    ours = {e[0].lower() for e in plan}
    for p in sorted(set(before) | set(after)):
        if p in ours:
            continue
        if before.get(p) != after.get(p):
            print("CHANGED OUTSIDE THE FRAGMENT  " + p)
            bad += 1
    print("%d fragments verified, %d other files unchanged, %d bad" %
          (len(plan), len(before) - sum(1 for p in before if p in ours), bad))
    return bad


def main():
    if "--fetch-headers" in sys.argv:
        fetch_headers()
        return
    H = headers()
    T, loc = build()
    if "--selftest" in sys.argv:
        selftest(T, loc, H)
        return
    bad = check(T, loc, H)
    for b in bad:
        print("FAIL  " + b)
    if bad:
        raise SystemExit("%d finding(s) - nothing written" % len(bad))
    plan = write_all(T, loc, H)
    for o in OPTIONS:
        d = o["d"]
        print("  %-15s rank %2d  %3d men  per-man health %3d -> %3d  officer %d (+%d) = %d" %
              (o["opt"], o["rank"], d["men"], d["base_hp"], 2 * d["base_hp"], d["officer_hp"],
               d["bonus"] if STACKS_BONUS else 0, d["officer_total"]))
    for path, spec, fn, d, n in plan:
        print("  %5d  %s" % (n, path))
    if "--import" in sys.argv:
        sys.exit(1 if do_import(plan) else 0)


if __name__ == "__main__":
    main()
