"""Zochaz - a faction-less Chaos Dwarf legendary lord, Sorcerer Lord of the Temple of Hashut.

Lore: Vraznak's kinsman, who led the 2497 IC raid on the Wood Elves with him in revenge for a
Sorcerer Lord murdered in the Temple of Hashut (White Dwarf 170, "The Battle of Skull River").
They crossed the Blasted Waste, hired renegade Hobgoblin scouts near Mount Gunbad, burned the
forest with oil and tar and carried the skulls home. Design approved 2026-10-04 - see
docs/sessions/HANDOFF_20261004_LORE_ROUTES_AND_BALUR.md section 8.

How it is built: every row the lords pack holds for Gargath (the pack's other Sorcerer-Prophet)
is cloned with `derpy_gargath` -> `derpy_zochaz`, minus Gargath's faction, mission, set-piece
and start-bundle rows and his two custom actives, then:
  - the model is CA's base Sorcerer-Prophet (variants `chd_sorcerer_prophet` /
    `chd_sorcerer_prophet_campaign_01`) instead of Gargath's kitbash, with CA's porthole block
    under our art set id;
  - his spells are CA's Lore of Hashut nodes in place of Gargath's Lore of Fire ones;
  - every skill, item and line of text is Zochaz's own (SKILLS / ITEMS / TEXT below).

Everything is written to NEW fragments named `derpy_zochaz` - no existing fragment is
rewritten, so nothing another generator owns can be lost. He reaches a faction through the
Vraznak quest in tools/gen_victory_routes.py (`derpy_mis_vraznak_kinsmans_raid`), whose success
listener calls cm:spawn_character_to_pool.

    py tools/extract_pack_tsv.py <pack> "Modding Files/source/zochaz/_pack"   # fresh source
    py tools/gen_zochaz.py --check       # build in memory, run every check, write nothing
    py tools/gen_zochaz.py               # write TSVs + portrait bins to source/zochaz/out
    py tools/gen_zochaz.py --import      # ... and import into the Modpacks pack, then verify
    py tools/gen_zochaz.py --selftest
"""
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
EX = os.path.join(ROOT, "Modding Files", "source", "zochaz", "_pack")
OUT = os.path.join(ROOT, "Modding Files", "source", "zochaz", "out")
PACK = os.path.join(ROOT, "Modding Files", "Modpacks", "!aa_derpy_hashut_legendary_lords.pack")
GAME = r"F:\SteamLibrary\steamapps\common\Total War WARHAMMER III\data"

SRC, SUB = "derpy_gargath", "derpy_zochaz"
FRAG = "derpy_zochaz"                       # every new DB fragment's name
LOC_PATH = "text/derpy_zochaz.loc"
NAME_ID = "12412537"                        # 12412535 is retired (HANDOFF_20261003 section 1)
ARTS_ID = "696991703"
ABILITY_ID = "13354703"

# Gargath rows that are his house's or his story's, not a lord's.
SKIP_TABLES = {
    "frontend_faction_leaders_tables", "faction_agent_permitted_subtypes_tables",
    "missions_tables", "cdir_events_mission_issuer_junctions_tables",
    "cdir_events_mission_option_junctions_tables", "cdir_events_mission_payloads_tables",
    # his lord-trait BUNDLE reaches a faction only through a general it starts with, and
    # Zochaz never starts on the map - the trait SKILL below is what he carries
    "faction_starting_general_effects_tables", "effect_bundles_tables",
    "effect_bundles_to_effects_junctions_tables",
    "names_tables",                         # minted below
}
# no custom actives - but node 5's skill row wears the active's icon, which is art, not the ability
DROP_ROW = re.compile(r"derpy_gargath_(2_3_active|3_active)(?!_buff\.png)")
LOC_SKIP = re.compile(r"^(frontend_faction_leaders_|missions_|mission_text_|effect_bundles_localised_"
                      r"|names_name_|battle_set_piece)")

# The model: CA's base Sorcerer-Prophet (user, 2026-10-04: "use the base sorcerer-lord as his
# placeholder model"). Read off CA's own rows: unit_variants for
# wh3_dlc23_chd_cha_sorcerer_prophet_hashut -> variant wh3_dlc23_chd_cha_sorcerer_prophet ->
# chd_sorcerer_prophet; agent_uniforms wh3_dlc23_chd_sorcerer_prophet_campaign_01.
VARIANT_BATTLE = "chd_sorcerer_prophet"
VARIANT_CAMPAIGN = "chd_sorcerer_prophet_campaign_01"
DONOR_ART = "wh3_dlc23_art_set_chd_sorcerer_prophet_hashut_01"
PORTRAIT_PNG = "ui/portraits/portholes/no_culture/chd_sorcerer_prophet_campaign_01_0.png"
PORTRAIT_PATHS = ["ui/portraits/portholes/portrait_settings_derpy_zochaz.bin",
                  "ui/portraits/units/portrait_settings_derpy_zochaz.bin"]
SPELLS_FROM, SPELLS_TO = "sorcerer_prophet_fire_", "sorcerer_prophet_hashut_"

C2C, G2F, C2FU, C2PF = ("character_to_character_own", "general_to_force_own",
                        "character_to_force_own_unseen", "character_to_province_own_factionwide")

# suffix -> (name, description, [(effect, scope, [value per level])]). Level counts must match
# Gargath's, whose node and level rows are cloned (check() asserts it).
SKILLS = {
    "lord_trait": ("Vengeance of the Temple",
                   "A Sorcerer Lord was murdered in the Temple of Hashut itself. Zochaz has never "
                   "forgotten it, and the Hobgoblins who march with him have learned to fear it.",
                   [("wh2_dlc11_enable_immortal_hidden", C2C, [1]),
                    ("wh2_main_effect_force_stat_miscast", C2C, [-25]),
                    ("wh3_dlc23_effect_force_stat_leadership_chd_hobgoblins", G2F, [5])]),
    "1": ("The Temple Remembers",
          "Zochaz's warriors know why they march, and a host that marches for vengeance does not "
          "break easily.",
          [("wh_main_effect_force_stat_leadership", G2F, [4])]),
    "2_1": ("Oil and Tar",
            "The raid carried its fire in barrels. Zochaz's warriors coat their blades in burning "
            "tar before every battle.",
            [("wh2_main_effect_character_stat_enable_flaming_attacks", G2F, [1, 1, 1]),
             ("wh_main_effect_force_stat_weapon_strength", G2F, [3, 6, 9])]),
    "2_2": ("Renegade Scouts",
            "Hobgoblins hired in the shadow of Mount Gunbad lead the way, and cost him less than "
            "loyal ones would.",
            [("wh3_dlc23_effect_enable_attribute_vanguard_deployment_hobgoblins", G2F, [1, 1, 1]),
             ("wh3_dlc23_effect_force_stat_leadership_chd_hobgoblins", G2F, [2, 4, 6])]),
    "2_3": ("Kinsman of Vraznak",
            "Zochaz rode to Skull River beside Vraznak and his bulls. The Bull Centaurs of his "
            "house charge harder for him.",
            [("wh3_dlc23_effect_force_stat_charge_chd_bull_centaurs", G2F, [5, 10, 15]),
             ("wh3_dlc23_effect_force_stat_armour_chd_bull_centaurs", G2F, [3, 6, 9])]),
    "2_4": ("Lore of the Father of Darkness",
            "Zochaz's command of the Lore of Hashut deepens with every rite performed in the "
            "Temple.",
            [("wh3_main_effect_winds_of_magic_pool_cap", C2FU, [5, 10, 15]),
             ("wh3_dlc23_effect_cooldown_lore_hashut", C2C, [-4, -7, -10]),
             ("wh3_main_effect_spell_mastery", C2C, [10, 20, 30])]),
    "3": ("Hand of Hashut",
          "The Father of Darkness lends his avenger strength enough to finish what the Temple "
          "began.",
          [("wh_main_effect_character_stat_armour", C2C, [20]),
           ("wh_main_effect_character_stat_weapon_strength", C2C, [15]),
           ("wh_main_effect_character_stat_melee_attack", C2C, [15])]),
    "4_1": ("Across the Blasted Waste",
            "Zochaz drives his host across the wastes without stopping. It arrives sooner, and "
            "with fewer of its wounded on their feet.",
            [("wh_main_effect_force_all_campaign_movement_range", G2F, [15]),
             ("wh_main_effect_force_all_campaign_replenishment_rate", G2F, [-10])]),
    "4_2": ("Skulls for the Temple",
            "Every skull taken is a debt repaid. Zochaz takes more captives than any lord of "
            "Zharr-Naggrund, and his provinces fear what he does with them.",
            [("wh_main_effect_force_all_campaign_captives", G2F, [25]),
             ("wh_main_effect_public_order_characters", C2PF, [-3])]),
    "4_3": ("The Temple's Due",
            "Zochaz opens himself to the Father of Darkness and does not close the door again. "
            "Every spell comes cheaper, but what pours through him no longer answers cleanly.",
            [("wh2_dlc14_effect_magic_cost_all_lores_percentage", C2C, [-15]),
             ("wh3_main_effect_winds_of_magic_pool_min", C2FU, [15]),
             ("wh_main_effect_character_stat_miscast", C2C, [15])]),
    "4_4": ("Burn It All",
            "The forest burned for a mile high. Zochaz's host hits as hard as the fire did, and "
            "eats through its stores just as fast.",
            [("wh_main_effect_force_stat_weapon_strength", G2F, [10]),
             ("wh_main_effect_force_all_campaign_upkeep", G2F, [15])]),
    "5": ("The Debt Repaid",
          "The murderers of the Temple are long dead, and the debt is still not paid. Zochaz "
          "will not break until it is.",
          [("wh_main_effect_attribute_enable_unbreakable", C2C, [1]),
           ("wh3_main_effect_battle_barrier_health_add", C2C, [600])]),
}

# slot -> (name, description, [(effect, scope, value)])
ITEMS = {
    "weapon": ("Staff of the Murdered Prophet",
               "Taken from the Temple's altar after the murder, and carried to Skull River to "
               "see it avenged.",
               [("wh_main_effect_character_stat_weapon_strength", C2C, 10),
                ("wh2_main_effect_character_stat_enable_flaming_attacks", C2C, 1)]),
    "armor": ("Mantle of the Temple Wardens",
              "The iron robes of the priests who guard Hashut's sanctum, and failed to guard it "
              "once.",
              [("wh_main_effect_character_stat_armour", C2C, 20),
               ("wh_main_effect_character_stat_physical_resistance", C2C, 10)]),
    "ench": ("Skull River Trophy",
             "An elf skull worked in brass. The Daemonsmiths of the Temple study under the one "
             "who brought it home.",
             [("wh3_dlc23_effect_agent_recruitment_xp_chd_daemonsmith_sorcerer",
               "character_to_faction_unseen", 5),
              ("wh3_main_effect_winds_of_magic_character", C2C, 3)]),
}

TEXT = {
    "land_units_onscreen_name_derpy_zochaz": "Zochaz",
    "land_units_onscreen_name_derpy_zochaz_bale_taurus": "Zochaz",
    "land_units_onscreen_name_derpy_zochaz_great_taurus": "Zochaz",
    "land_units_onscreen_name_derpy_zochaz_lammasu": "Zochaz",
    "names_name_" + NAME_ID: "Zochaz",
    "unit_description_short_texts_text_derpy_zochaz_description":
        "Sorcerer Lord of the Temple of Hashut, Vraznak's kinsman and the avenger of Skull River.",
    "unit_description_historical_texts_text_derpy_zochaz_description":
        "Centuries ago a Sorcerer Lord was murdered in the Temple of Hashut itself, and the Temple "
        "has never forgiven the Wood Elves for it. In 2497 Zochaz and his kinsman Vraznak led the "
        "traditional raid of revenge across the Blasted Waste, hiring renegade Hobgoblin scouts "
        "near Mount Gunbad. At the source of the Skull River they set the forest alight with oil "
        "and tar, waited for the elves to answer the smoke, and carried their skulls home.",
    "ancillary_sets_name_derpy_zochaz_set": "Regalia of the Avenger",
    "ancillary_sets_description_derpy_zochaz_set":
        "The staff, mantle and trophy Zochaz carried to Skull River.",
    "effects_description_derpy_zochaz_passive": 'Passive Ability: "Blessing of the Temple"',
    "unit_abilities_onscreen_name_derpy_zochaz_passive": "Blessing of the Temple",
    "special_ability_phases_onscreen_name_derpy_zochaz_passive": "Blessing of the Temple",
    "unit_abilities_tooltip_text_derpy_zochaz_passive":
        "Zochaz's rites close the wounds of the warriors around him while the battle goes on.",
    "character_skill_node_sets_enc_title_derpy_zochaz_skills": "Vengeance of the Temple",
}
for _s, (_n, _d, _e) in SKILLS.items():
    TEXT["character_skills_localised_name_%s_%s" % (SUB, _s)] = _n
    TEXT["character_skills_localised_description_%s_%s" % (SUB, _s)] = _d
for _s, (_n, _d, _e) in ITEMS.items():
    for _k in ("character_skills_localised_name_", "ancillaries_onscreen_name_"):
        TEXT["%s%s_%s" % (_k, SUB, _s)] = _n
    for _k in ("character_skills_localised_description_", "ancillaries_colour_text_"):
        TEXT["%s%s_%s" % (_k, SUB, _s)] = _d

# Words that must not survive the clone into anything a player reads or a key that ships.
FORBIDDEN = re.compile(r"gargath|\bbaal\b|daemonbind|k'daai", re.I)
# ...except two of Gargath's own icons, reused on purpose: the passive's and node 5's.
ICON_REUSE = "derpy_gargath_passive"
SKILL5_ICON = "derpy_gargath_3_active_buff.png"


# ------------------------------------------------------------------------------------------ read
def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        lines = fh.read().split("\n")
    return lines[0], lines[1], [l for l in lines[2:] if l.strip("\t\r ")]


def fragments(root=None):
    root = root or EX
    for base, _d, files in os.walk(root):
        for f in files:
            if f.endswith(".tsv"):
                rel = os.path.relpath(os.path.join(base, f), root)
                parts = rel.split(os.sep)
                yield rel, (parts[1] if parts[0] == "db" else None)


def set_col(row, hdr, **kv):
    c, h = row.split("\t"), hdr.split("\t")
    for k, v in kv.items():
        c[h.index(k)] = str(v)
    return "\t".join(c)


def get_col(row, hdr, k):
    return row.split("\t")[hdr.split("\t").index(k)]


# ------------------------------------------------------------------------------------------ build
def build():
    """{table or None for loc: (hdr, meta, rows)} - one new fragment per table."""
    out = {}
    for rel, table in fragments():
        if table in SKIP_TABLES:
            continue
        hdr, meta, rows = read_tsv(os.path.join(EX, rel))
        src = [r for r in rows if SRC in r and not DROP_ROW.search(r)]
        if table is None:
            src = [r for r in src if SRC in r.split("\t")[0] and not LOC_SKIP.search(r)]
        if not src:
            continue
        new = [fix(r.replace(SRC, SUB).replace(SKILL5_ICON.replace(SRC, SUB), SKILL5_ICON), hdr, table)
               for r in src]
        new = [r for r in new if r is not None]
        key = table or "loc"
        if key in out:
            assert out[key][0] == hdr, "%s: two source fragments disagree on columns" % key
            out[key][2].extend(new)
        else:
            out[key] = (hdr, _meta(meta, table), new)
    add_skills(out)
    add_names(out)
    for key in out:
        hdr, meta, rows = out[key]
        out[key] = (hdr, meta, list(dict.fromkeys(rows)))
    return out


def _meta(meta, table):
    """The source fragment's metadata line, renamed to our fragment."""
    cells = meta.split("\t")
    parts = cells[0].split(";")
    if table is None:
        parts[2] = LOC_PATH
    else:
        parts[2] = "db/%s/%s" % (table, FRAG)
    cells[0] = ";".join(parts)
    return "\t".join(cells)


def fix(row, hdr, table):
    first = row.split("\t")[0]
    if table == "agent_subtypes_tables":
        return set_col(row, hdr, magic_lore="wh3_dlc23_lore_hashut")
    if table == "variants_tables":
        return set_col(row, hdr, variant_filename=VARIANT_CAMPAIGN if first.endswith("_campaign")
                       else VARIANT_BATTLE)
    if table == "campaign_character_arts_tables":
        return set_col(row, hdr, id=ARTS_ID)
    if table == "unit_special_abilities_tables":
        return set_col(row, hdr, unique_id=ABILITY_ID)
    if table == "unit_abilities_tables" and first == SUB + "_passive":
        return set_col(row, hdr, icon_name=ICON_REUSE)
    if table == "units_custom_battle_permissions_tables":
        return set_col(row, hdr, general_portrait=PORTRAIT_PNG)
    if table == "battle_set_piece_armies_characters_tables":
        # the custom battle general: name, lore and model come from here, not from the subtype
        return set_col(row, hdr, forename=NAME_ID, magic_lore="wh3_dlc23_lore_hashut",
                       portrait=PORTRAIT_PNG, character_model=ARTS_ID)
    if table == "character_skill_node_set_items_tables":
        return row.replace(SPELLS_FROM, SPELLS_TO)
    if table == "character_skills_tables":
        suf = first[len(SUB) + 1:]
        if suf in SKILLS:
            return set_col(row, hdr, localised_name=SKILLS[suf][0])
        if suf in ITEMS:
            return set_col(row, hdr, localised_name=ITEMS[suf][0])
    if table == "character_skill_level_to_effects_junctions_tables":
        suf = first[len(SUB) + 1:]
        if suf in SKILLS and "_passive\t" not in row:
            return None                     # replaced whole by add_skills()
    if table == "ancillary_to_effects_tables" and first[len(SUB) + 1:] in ITEMS:
        return None
    if table is None:
        c = row.split("\t")
        if c[0] in TEXT:
            c[1] = TEXT[c[0]]
        return "\t".join(c)
    return row


def add_skills(out):
    hdr, meta, rows = out["character_skill_level_to_effects_junctions_tables"]
    for suf, (_n, _d, effects) in SKILLS.items():
        for eff, scope, values in effects:
            for lvl, v in enumerate(values, 1):
                rows.append("\t".join(["%s_%s" % (SUB, suf), eff, str(lvl), scope, "%.4f" % v]))
    hdr, meta, rows = out["ancillary_to_effects_tables"]
    for slot, (_n, _d, effects) in ITEMS.items():
        for eff, scope, v in effects:
            rows.append("\t".join(["%s_%s" % (SUB, slot), eff, scope, "%.4f" % v]))


def add_names(out):
    hdr, meta, _rows = read_tsv(os.path.join(EX, "db", "names_tables",
                                             "!!derpy_chd_legendary_lords.tsv"))
    out["names_tables"] = (hdr, _meta(meta, "names_tables"),
                           ["\t".join([NAME_ID, "names_chd_chaos_dwarfs", "forename", "m", "0"])])
    hdr, meta, rows = out["loc"]
    rows.append("\t".join(["names_name_" + NAME_ID, TEXT["names_name_" + NAME_ID], "false"]))


def portrait_bin():
    import gen_portrait_settings as gps
    ver, entries = gps.parse(gps.read_settings(os.path.join(GAME, "ui.pack"),
                                               "ui/portraits/portholes/portrait_settings__.bin"))
    _k, body, head, variants = {e[0]: e for e in entries}[DONOR_ART]
    return gps.dump(ver, [(SUB, body, head, variants)])


# ------------------------------------------------------------------------------------------ checks
def check(out):
    bad = []
    import gen_new_house_lords as N
    import read_vanilla_db as rvd
    db = os.path.join(GAME, "db.pack")

    # 1. no trace of Gargath, Baal or the K'daai in anything that ships
    for key, (_h, _m, rows) in out.items():
        for r in rows:
            if FORBIDDEN.search(r.replace(ICON_REUSE, "").replace(SKILL5_ICON, "")):
                bad.append("%s: Gargath's content survived the clone: %s" % (key, r[:120]))

    # 2. every designed (effect, scope) pair is one CA or this pack already uses
    pairs, effects = N.vanilla_pairs()
    ppairs, peffects = N.pack_pairs()
    pairs |= ppairs
    for suf, (_n, _d, fx) in SKILLS.items():
        for eff, scope, _v in fx:
            if (eff, scope) not in pairs:
                bad.append("skill %s: (%s, %s) is used by nothing" % (suf, eff, scope))
    for slot, (_n, _d, fx) in ITEMS.items():
        for eff, scope, _v in fx:
            if (eff, scope) not in pairs:
                bad.append("item %s: (%s, %s) is used by nothing" % (slot, eff, scope))

    # 3. level counts match the cloned node/level rows (Gargath's)
    _h, _m, src_rows = read_tsv(_one("character_skill_level_to_effects_junctions_tables",
                                     "derpy_chd_ll_unique_skills.tsv"))
    _h2, _m2, trait_rows = read_tsv(_one("character_skill_level_to_effects_junctions_tables",
                                         "derpy_chd_ll_trait.tsv"))
    gl = {}
    for r in src_rows + trait_rows:
        c = r.split("\t")
        if c[0].startswith(SRC + "_") and c[2] != "0" and not DROP_ROW.search(r):
            gl[c[0][len(SRC) + 1:]] = max(gl.get(c[0][len(SRC) + 1:], 0), int(c[2]))
    for suf, (_n, _d, fx) in SKILLS.items():
        mine = max(len(v) for _e, _s, v in fx)
        if gl.get(suf) not in (None, mine):
            bad.append("skill %s has %d levels, Gargath's node has %d" % (suf, mine, gl[suf]))

    # 4. every spell node swapped in exists in CA's tables
    ca_nodes = {r["key"] for _p, _v, rows in rvd.load(db, "character_skill_nodes_tables") for r in rows}
    for r in out["character_skill_node_set_items_tables"][2]:
        item = r.split("\t")[1]
        if item.startswith("wh3_dlc23_skill_node_chd_sorcerer_prophet") and item not in ca_nodes:
            bad.append("spell node %s is not in CA's character_skill_nodes" % item)
        if SPELLS_FROM in item:
            bad.append("a Lore of Fire node survived: %s" % item)
    if not any(SPELLS_TO in r for r in out["character_skill_node_set_items_tables"][2]):
        bad.append("no Lore of Hashut node in the tree")

    # 5. minted ids are unused by CA and by the pack
    def used(table, col):
        s = {str(r[col]) for _p, _v, rows in rvd.load(db, table) for r in rows}
        for rel, t in fragments():
            if t == table:
                h, _m, rows = read_tsv(os.path.join(EX, rel))
                s |= {get_col(r, h, col) for r in rows}
        return s
    for table, col, val in (("names_tables", "id", NAME_ID),
                            ("campaign_character_arts_tables", "id", ARTS_ID),
                            ("unit_special_abilities_tables", "unique_id", ABILITY_ID)):
        if val in used(table, col):
            bad.append("%s.%s %s is already taken" % (table, col, val))

    # 6. every designed text key is actually shipped
    loc_keys = {r.split("\t")[0] for r in out["loc"][2]}
    for k in TEXT:
        if k not in loc_keys:
            bad.append("text %s has no loc row - its source key was never cloned" % k)
    for k in loc_keys:      # the mount skills keep Gargath's text - it names only the beast
        if (k.startswith("character_skills_localised_") and k not in TEXT
                and k.rsplit(SUB + "_", 1)[-1] in set(SKILLS) | set(ITEMS)):
            bad.append("skill text %s was cloned but never written" % k)

    # 7. the model is CA's, and the mesh names are CA's
    v = {r.split("\t")[0]: get_col(r, out["variants_tables"][0], "variant_filename")
         for r in out["variants_tables"][2]}
    if set(v.values()) != {VARIANT_BATTLE, VARIANT_CAMPAIGN}:
        bad.append("variants point at %s, not CA's Sorcerer-Prophet" % sorted(set(v.values())))

    # 8. every node of his tree has its skill row (node 5's was once dropped by DROP_ROW)
    skills = {r.split("\t")[0] for r in out["character_skills_tables"][2]}
    nh = out["character_skill_nodes_tables"][0]
    for r in out["character_skill_nodes_tables"][2]:
        if get_col(r, nh, "character_skill_key") not in skills:
            bad.append("node %s has no skill row" % r.split("\t")[0])

    # 9. every custom battle general names a set piece character that exists and is HIS - CA
    #    leaves none dangling (0 of 864), and that row is where custom battle reads his lore
    sh, _m, srows = out.get("battle_set_piece_armies_characters_tables", ("", "", []))
    chars = {r.split("\t")[0]: r for r in srows}
    ph = out["units_custom_battle_permissions_tables"][0]
    for r in out["units_custom_battle_permissions_tables"][2]:
        c = chars.get(get_col(r, ph, "set_piece_character"))
        if c is None:
            bad.append("custom battle %s names a missing set piece character" % get_col(r, ph, "unit"))
        elif (get_col(c, sh, "forename"), get_col(c, sh, "character_model"),
              get_col(c, sh, "magic_lore")) != (NAME_ID, ARTS_ID, "wh3_dlc23_lore_hashut"):
            bad.append("set piece character %s still carries Gargath's name, model or lore"
                       % c.split("\t")[0])
    return bad


def _one(table, name):
    return os.path.join(EX, "db", table, name)


# ------------------------------------------------------------------------------------------ write
def write(out):
    shutil.rmtree(OUT, ignore_errors=True)
    plan = []
    for key, (hdr, meta, rows) in sorted(out.items()):
        if key == "loc":
            rel, path = os.path.join(OUT, "text", "derpy_zochaz.loc.tsv"), LOC_PATH
        else:
            rel, path = os.path.join(OUT, "db", key, FRAG + ".tsv"), "db/%s/%s" % (key, FRAG)
        os.makedirs(os.path.dirname(rel), exist_ok=True)
        with open(rel, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join([hdr, meta] + rows) + "\n")
        plan.append((path, rel, len(rows)))
    blob = portrait_bin()
    loose = []
    for p in PORTRAIT_PATHS:
        dest = os.path.join(OUT, "pack", *p.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(blob)
        loose.append((dest, p))
    return plan, loose


def do_import(plan, loose, frag=FRAG):
    from import_house_ancillaries import call, check_keys
    call("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False})
    keyed = []
    for path, rel, _n in plan:
        if path.startswith("db/"):
            with open(rel, encoding="utf-8") as fh:
                fh.readline()
                ver = int(fh.readline().split("\t")[0].split(";")[1])
            new = {"DB": [frag, path.split("/")[1], ver]}
        else:
            new = {"Loc": frag}
        keyed.append((path, new, os.path.basename(rel), os.path.dirname(rel)))
    check_keys(keyed)
    try:
        call("close_pack", {"pack_key": PACK})
    except Exception:
        pass
    call("open_packfiles", {"paths": [PACK]})
    for path, new, tsv, folder in keyed:      # import_tsv only fills a file that already exists
        try:
            call("new_packed_file", {"pack_key": PACK, "path": path, "new_file": json.dumps(new)})
        except RuntimeError:
            pass                              # already there from an earlier run
        call("import_tsv", {"pack_key": PACK, "table_path": path,
                            "tsv_path": os.path.join(folder, tsv)})
    for src, dest in loose:
        call("add_packed_files", {"pack_key": PACK, "source_paths": [src],
                                  "destination_paths": json.dumps([{"File": dest}])})
    call("save_packfile", {"pack_key": PACK})
    call("close_pack", {"pack_key": PACK})
    print("saved")
    dest = tempfile.mkdtemp()
    call("open_packfiles", {"paths": [PACK]})
    call("extract_packed_files", {"pack_key": PACK, "export_as_tsv": True, "destination_path": dest,
         "source_paths": json.dumps({"PackFile": [{"File": p} for p, _r, _n in plan]})})
    call("close_pack", {"pack_key": PACK})
    bad = 0
    for path, rel, n in plan:
        got = open(os.path.join(dest, *path.split("/")) + ".tsv", encoding="utf-8").read().split("\n")[2:]
        want = open(rel, encoding="utf-8").read().split("\n")[2:]
        g = sorted(x.lower() for x in got if x.strip("\t"))
        w = sorted(x.lower() for x in want if x.strip("\t"))
        if g != w:
            print("DIFF   %s  pack %d rows, built %d" % (path, len(g), len(w)))
            bad += 1
    shutil.rmtree(dest, ignore_errors=True)
    from read_pack_index import paths
    have = {p.lower() for p in paths(PACK)}
    for _s, p in loose:
        if p.lower() not in have:
            print("MISSING  " + p)
            bad += 1
    print("%d fragments verified, %d loose files, %d bad" % (len(plan), len(loose), bad))
    return bad


# ------------------------------------------------------------------------------------------ selftest
def selftest():
    out = build()
    assert not check(out), check(out)
    # each check has to be able to fail
    import copy
    breaks = [
        ("a Gargath word survives", lambda o: o["loc"][2].append("x_derpy_zochaz\tGargath's\tfalse"),
         "survived the clone"),
        ("an effect with a scope nobody uses",
         lambda o: SKILLS["1"][2].append(("wh_main_effect_force_stat_leadership", "faction_to_region_own", [1])),
         "used by nothing"),
        ("a skill with the wrong level count",
         lambda o: SKILLS["2_1"][2].append(("wh_main_effect_force_stat_weapon_strength", G2F, [1, 2, 3, 4])),
         "levels"),
        ("a Lore of Fire node left in",
         lambda o: o["character_skill_node_set_items_tables"][2].append(
             "derpy_zochaz_skills\twh3_dlc23_skill_node_chd_sorcerer_prophet_fire_magic_0\tfalse"),
         "Lore of Fire"),
        ("Gargath's mesh", lambda o: o["variants_tables"][2].__setitem__(
            0, set_col(o["variants_tables"][2][0], o["variants_tables"][0], variant_filename="derpy_gargath")),
         "Sorcerer-Prophet"),
        ("a taken id", lambda o: globals().__setitem__("NAME_ID", "12412523"), "already taken"),
        ("no custom battle character", lambda o: o.pop("battle_set_piece_armies_characters_tables"),
         "missing set piece character"),
        ("Gargath's lore in custom battle", lambda o: o["battle_set_piece_armies_characters_tables"][2]
         .__setitem__(0, o["battle_set_piece_armies_characters_tables"][2][0]
                      .replace("wh3_dlc23_lore_hashut", "wh_main_lore_fire")), "Gargath's name"),
        ("node 5 without its skill", lambda o: o["character_skills_tables"][2].__setitem__(
            slice(None), [r for r in o["character_skills_tables"][2]
                          if not r.startswith(SUB + "_5\t")]), "no skill row"),
    ]
    for name, mutate, expect in breaks:
        saved_skills, saved_id = copy.deepcopy(SKILLS), NAME_ID
        o = copy.deepcopy(out)
        mutate(o)
        found = check(o)
        SKILLS.clear()
        SKILLS.update(saved_skills)
        globals()["NAME_ID"] = saved_id
        assert any(expect in f for f in found), "%s was not caught: %s" % (name, found)
    assert not check(build()), "breaks were not reverted"
    print("selftest ok - %d fragments, %d designed skills, %d items, %d breaks caught"
          % (len(out), len(SKILLS), len(ITEMS), len(breaks)))


def main():
    if "--selftest" in sys.argv:
        selftest()
        return
    out = build()
    bad = check(out)
    for b in bad:
        print("FAIL  " + b)
    if bad:
        raise SystemExit("%d finding(s) - nothing written" % len(bad))
    for key, (_h, _m, rows) in sorted(out.items()):
        print("  %4d  %s" % (len(rows), key))
    if "--check" in sys.argv:
        return
    plan, loose = write(out)
    print("wrote %d fragments and %d portrait files under %s" % (len(plan), len(loose), OUT))
    if "--import" in sys.argv:
        sys.exit(1 if do_import(plan, loose) else 0)


if __name__ == "__main__":
    main()
