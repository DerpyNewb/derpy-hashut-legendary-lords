"""Two new house lords for the Hashut's Legendary Lords pack, on CA's Overseer model.

    the Overlord of Zharrduk         derpy_kharkadon  leads wh3_dlc23_chd_minor_faction (CA's Overlords of Zharrduk)
    the Captain of the Uzkul Mingol  derpy_uzkul     leads cr_chd_skullstack (IEE's Uzkul Mingol Company)

Both names are PLACEHOLDERS - every player-facing string is in LORDS below, nowhere else, so a
rename is one edit here and a re-run. The keys are faction-based and never change.

Built by CLONING Balur, not by authoring: every row the pack holds for derpy_balur and for his
house (the Fists of Hashut's Tower of Zharr seat, AI membership, usurp incidents) is copied with
the keys swapped, so a table nobody remembered still gets its row. Then four things are replaced:

  - the model: CA's Overseer animation, battle entity, variantmeshes and porthole, instead of
    Balur's custom mesh (variants -> chd_overseer, campaign_character_arts land_animation ->
    cam_hu3_dwarf_axe_and_shield, a portrait settings file cloned from CA's Overseer blocks).
    A lord with `mesh` / `anim` in LORDS wears his own instead (Kharkadon); check_own_models()
    asserts the assets pack ships both
  - the skill content: SKILLS / TRAIT_BUNDLE below. Every (effect, scope) pair is asserted to
    occur somewhere in vanilla or in this pack, because a scope the effect was never written for
    does nothing, silently
  - the Tower seat's district and panel order, read from Modding Files/templates/toz_districts.py
    (the one list that orders the seats; zz_derpy_toz_annex.lua's ANNEX_DISTRICTS must match it)
  - Balur-only rows that do not travel: his custom anim table and entity, his Great Drill
    missions and set piece, his victory routes, his house's factions_tables row

Rows this script owns are recognised by OWNED and dropped before the new ones are written, so a
re-run after an import replaces rather than duplicates.

    py tools/gen_new_house_lords.py             build TSVs + portrait bin + leader images, run checks
    py tools/gen_new_house_lords.py --import    then import into the lords pack, save, verify from disk
    py tools/gen_new_house_lords.py --selftest  prove the checks fail on broken input

Needs .skilltree_cache/extract fresh from the pack (py tools/check_skill_trees.py writes it).
"""
import ast
import csv
import glob
import io
import json
import os
import re
import shutil
import struct
import sys
import tempfile
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
EX = os.path.join(ROOT, ".skilltree_cache", "extract")
OUT = os.path.join(ROOT, "Modding Files", "source", "hll_new_lords")
PACK = os.path.join(ROOT, "Modding Files", "Modpacks", "!aa_derpy_hashut_legendary_lords.pack")
GAME = r"F:\SteamLibrary\steamapps\common\Total War WARHAMMER III\data"
DISTRICTS_PY = os.path.join(ROOT, "Modding Files", "templates", "toz_districts.py")

SRC = "derpy_balur"
SRC_FACTION = "cr_chd_fists_of_hashut"

LORDS = [
    dict(sub="derpy_kharkadon", faction="wh3_dlc23_chd_minor_faction", fslug="zharrduk",
         name_id=None, name="Kharkadon the Vicious", short="the Overlord",     # CA's own names 212779775 + 318034614
         house="Overlords of Zharrduk", variant="chd_overseer_campaign_01",
         donor_art="wh3_dlc23_art_set_chd_overseer_01", arts_id="696991701", ability_id="13354701",
         frontend=["mixer_ime_chd_minor_faction", "cr_oldworld_political_party_chd_minor_faction"], ma=65, md=60,
         armour="wh2_main_plate_130", shield="wh_missile_block_70_metal",
         weapon=dict(damage=230, ap_damage=250, splash_attack_target_size="large", splash_attack_max_attacks=10,
                     splash_attack_power_multiplier="2.0000", is_magical="true"),
         fe_anim=r"animations\battle\humanoid03\axe_and_shield\celebrate\hu3_axs_celebrate_01.anim",
         # his own model (2026-10-05), shipped by !!!derpy_chd_assets: the variantmeshdefinition and
         # animations/database/battle/bin/derpy_kharkadon.bin. Same prop slots as the Overseer, so
         # the campaign anim stays.
         mesh="derpy_kharkadon", anim="derpy_kharkadon",
         # his own 2D art (2026-10-06, approved): porthole.png, card.png and modern.png (lord-select,
         # in Partypus's style), all from an in-game screenshot by derive.py in that folder. A lord
         # with `portraits` ships them under his own stem; without it, CA's `variant` porthole.
         portraits=os.path.join(ROOT, "Modding Files", "source", "portraits", "derpy_kharkadon")),
    dict(sub="derpy_uzkul", faction="cr_chd_skullstack", fslug="skullstack",
         name_id="12412536", name="Captain of the Uzkul Mingol", short="the Captain",
         house="Uzkul Mingol Company", variant="chd_overseer_campaign_02",
         donor_art="wh3_dlc23_art_set_chd_overseer_02", arts_id="696991702", ability_id="13354702",
         frontend=["cr_political_party_combi_chd_skullstack", "cr_oldworld_political_party_chd_skullstack"], ma=65, md=45,
         weapon=dict(is_magical="false"),
         fe_anim=r"animations\battle\humanoid03\axe_and_shield\stand\hu3_axs_stand_idle_01.anim"),
]

# Minted name ids since replaced by a CA name - purged from names_tables and its loc on every run.
RETIRED_NAME_IDS = {"12412535"}     # "Overlord of Zharrduk", 2026-10-03 -> Kharkadon the Vicious

# IEE is the only pack that defines cr_chd_skullstack, and four of our tables reference it through
# factions.key. A dangling reference makes the engine refuse the WHOLE pack at load
# (crash_report/bad_mods_report.txt), so a player without IEE would lose every lord. The pack
# already ships IEE's own cr_chd_warfleet_of_uzkulak row byte for byte for the same reason;
# skullstack's is copied the same way, out of IEE's pack, never typed.
IEE_PACK = r"F:\SteamLibrary\steamapps\workshop\content\1142710\3007996493\!cr_immortal_empires_expanded.pack"
FACTIONS_REL = os.path.join("db", "factions_tables", "!!_cr_oldworld_new_factions.tsv")

# Tables Balur has rows in that the new lords must NOT get. Each has a reason.
SKIP = {
    "battle_entities_tables",           # Balur's custom entity - the Overseer's is vanilla
    "battle_set_pieces_tables", "battle_set_piece_armies_tables",
    "battle_set_piece_armies_junctions_tables", "battle_set_piece_armies_units_junctions_tables",
    "battle_set_piece_armies_characters_tables", "battle_set_piece_armies_characters_items_tables",
    "cdir_events_mission_issuer_junctions_tables", "cdir_events_mission_option_junctions_tables",
    "cdir_events_mission_payloads_tables", "missions_tables",   # the Great Drill: not in scope
    "victory_types_tables",             # tools/gen_victory_routes.py owns these
    "factions_tables",                  # CA's and IEE's factions are theirs to define
    "faction_potential_categories_tables",
    "frontend_faction_leaders_tables",  # written from LORDS[...]["frontend"], see frontend()
}
SKIP_LOC = re.compile(r"victory_types_|missions_localised_|frontend_faction_leaders_|"
                      r"factions_screen|factions_attack|factions_defend|derpy_chd_fists_of_hashut")
# Balur rows that are his alone
DROP_ROW = re.compile(r"whirlwind_of_death")

# Rows a previous run wrote. Anchored on the new keys, so nothing of Balur's or the houses' matches.
OWNED = re.compile(r"derpy_(?:zharrduk|uzkul|kharkadon)(?![a-z])|annex_(?:zharrduk|skullstack)(?![a-z])|"
                   r"cr_chd_skullstack|derpy_toz_skullstack|mod_skullstack(?![a-z])")

# ------------------------------------------------------------------------------------------ design
# suffix -> (rank, icon, name, description, [(effect, scope, [value per level])])
# Ranks and the lock pair are Balur's: _1 at 4, the four middles at 11 (three levels each),
# the 4_1 / 4_2 choice at 24, the capstone _3 at 29.
F, C, P = "general_to_force_own", "character_to_character_own", "character_to_province_own_factionwide"
CF = "character_to_force_own"      # what CA scopes most hobgoblin effects to
KP = "derpy_kharkadon_personal_"
KS = "derpy_kharkadon_self_"       # his own half of a paired bonus; see SELF_EFFECTS
SKILLS = {
    # The Overlords: Zharrduk's ruling caste. Few soldiers, the best ones - the Infernal Ironsworn,
    # CA's own Immortals (their art folder is chd_immortal) - and lords who take the field seasoned.
    # The slave line is Urzhkal's; here the labourers are the downside.
    "derpy_kharkadon": {
        "1": (4, "character_damage.png", "First into the Breach",
              "Kharkadon takes the first rank. His warriors follow him through the breach.",
              [("wh_main_effect_character_stat_melee_attack", C, [8]),
               (KP + "charge", F, [10]),
               (KS + "charge", C, [10])]),
        "2_1": (11, "trait_chaos_dwarfs.png", "Chosen of Zharrduk",
                "The Infernal Guard and Ironsworn eat, train and draw their pay before the rabble.",
                [(KP + "xp", F, [10, 20, 30]), (KP + "upkeep", F, [-5, -10, -15]),
                 (KS + "xp", C, [10, 20, 30]),
                 (KS + "upkeep", C, [-5, -10, -15])]),
        "2_2": (11, "character_defence.png", "Plate and Oath",
                "Kharkadon's bodyguard and Ironsworn are issued the best plate in Zharrduk. They are expected to use it.",
                [(KP + "defence", F, [3, 6, 9]), (KP + "armour", F, [5, 10, 15]),
                 (KS + "defence", C, [3, 6, 9]),
                 (KS + "armour", C, [5, 10, 15])]),
        "2_3": (11, "character_damage.png", "The Vicious",
                "Kharkadon splits armour and the dwarf beneath it with the same stroke.",
                [("wh_main_effect_character_stat_weapon_strength_ap_damage_mult", C, [5, 10, 15]),
                 ("wh_main_effect_character_stat_bonus_vs_infantry", C, [3, 6, 9])]),
        "2_4": (11, "campaign_military_spending.png", "A Court of Veterans",
                "Every officer in his court has served in the field. Their orders carry the weight of experience.",
                [("wh_main_effect_agent_recruitment_xp_all_agents", "character_to_province_own", [1, 2, 3]),
                 ("wh_main_effect_force_stat_leadership", F, [2, 4, 6])]),
        "4_1": (24, "unbreakable.png", "The Immortal Few",
                "His Ironsworn and bodyguard are slow to tire. Keeping them armed and paid costs the house dearly.",
                [(KP + "vigour", F, [1]), (KP + "resistance", F, [10]), (KP + "upkeep", F, [15]),
                 (KS + "vigour", C, [1]),
                 (KS + "resistance", C, [10]),
                 (KS + "upkeep", C, [15])]),
        "4_2": (24, "character_damage.png", "Rule by the Axe",
                "Kharkadon makes an example of his enemies. The hobgoblins and labourers know their turn may come.",
                [("wh_main_effect_attribute_enable_causes_terror", C, [1]),
                 ("wh_main_effect_character_stat_weapon_strength", C, [20]),
                 ("wh3_dlc23_effect_force_stat_leadership_chd_hobgoblins", F, [-8]),
                 ("wh3_dlc23_effect_force_stat_leadership_chd_labourers", F, [-8])]),
        "3": (29, "character_damage.png", "Stand With Your Overlord",
              "Kharkadon takes his place in the first rank. The Bloodsworn close around their master; "
              "those who abandon him will answer to his axe.",
              [("derpy_kharkadon_enable_stand_with_your_overlord", C, [1])]),
        "lord_trait": (None, None, "The Overlords of Zharrduk",
                       "Zharrduk fields more Immortals than any other house and its lords rise already "
                       "seasoned. Its Infernal Guard strike the deathblow; its slaves are left to the forges.",
                       [("wh2_dlc11_enable_immortal_hidden", C, [1]),
                        ("wh3_dlc23_effect_ability_enable_deathblow_chd_infernal_guard", F, [1]),
                        ("wh3_dlc23_effect_attribute_enable_expert_charge_defence_infernal_ironsworn", F, [1]),
                        (KS + "upkeep", C, [-25]),
                        (KS + "xp", C, [30])]),
    },
    # The Company: a chartered expedition hunting gold in Ind, living on convoys, trade and plunder.
    # Its hobgoblins are hired on the spot; its Chaos Dwarfs are a long way from home.
    "derpy_uzkul": {
        "1": (4, "campaign_military_spending.png", "Company Charter",
              "The Charter names the Company's share of everything it finds. The Captain makes sure "
              "there is a lot to find.",
              [("wh_main_effect_force_all_campaign_post_battle_loot_mod", C, [15]),
               ("wh_main_effect_force_all_campaign_raid_income", F, [15])]),
        "2_1": (11, "character_construction.png", "Prospectors",
                "Company prospectors walk ahead of the column, and every seam they find goes to the forges.",
                [("wh3_dlc23_pooled_resource_chd_armaments_modifier", "character_to_province_own", [5, 10, 15]),
                 ("wh3_dlc23_pooled_resource_chd_raw_material_efficiency", "character_to_province_own", [5, 10, 15])]),
        "2_2": (11, "campaign_military_spending.png", "Ivory Road Factors",
                "The Company's factors sit in every market from Ind to the Dark Lands, taking their cut.",
                [("wh_main_effect_economy_trade_tariff_mod", "character_to_faction_unseen", [5, 10, 15]),
                 ("wh2_main_effect_economy_gdp_mod_trade_sea_global", "character_to_region_own_factionwide", [5, 10, 15])]),
        "2_3": (11, "character_damage.png", "Spoils of Ind",
                "The temples of Ind are full of gold, and the Company is full of people who know it.",
                [("wh2_main_effect_force_all_campaign_sacking_income", C, [10, 20, 30]),
                 ("wh_main_effect_force_all_campaign_post_battle_loot_mod", C, [5, 10, 15])]),
        "2_4": (11, "character_movement.png", "The Long March",
                "An expedition that stops is an expedition that starves.",
                [("wh_main_effect_force_all_campaign_movement_range", F, [3, 6, 9]),
                 ("wh_main_effect_force_all_campaign_replenishment_rate", F, [3, 6, 9])]),
        "4_1": (24, "character_damage.png", "Gold Fever",
                "The Captain pays by the town sacked and the hoard taken. The hobgoblins fight like it - "
                "for the gold, and only as long as the gold holds out.",
                [("wh2_main_effect_force_all_campaign_sacking_income", C, [40]),
                 ("wh_main_effect_force_all_campaign_post_battle_loot_mod", C, [25]),
                 ("wh3_dlc23_effect_force_stat_leadership_chd_hobgoblins", F, [-6])]),
        "4_2": (24, "campaign_military_spending.png", "Charter Trade",
                "The Captain turns the Company from raiding to trading. The markets pay better than "
                "the villages ever did, and the villages are left alone.",
                [("wh_main_effect_economy_trade_tariff_mod", "character_to_faction_unseen", [20]),
                 ("wh3_dlc23_pooled_resource_chd_armaments_modifier", "character_to_province_own", [15]),
                 ("wh_main_effect_force_all_campaign_raid_income", F, [-20])]),
        "3": (29, "character_damage.png", "Captain of the Company",
              "No one rises to lead the Company by being merciful, or slow.",
              [("wh_main_effect_character_stat_melee_attack", C, [12]),
               ("wh_main_effect_character_stat_speed", C, [10]),
               ("wh_main_effect_character_stat_unit_health", C, [15])]),
        "lord_trait": (None, None, "The Uzkul Mingol Company",
                       "Far from Zharr, the Company lives on what it can send home: more convoys on the "
                       "road, better trade, richer raids. Its hobgoblins are hired along the way; its "
                       "Chaos Dwarfs are slow to replace.",
                       [("wh2_dlc11_enable_immortal_hidden", C, [1]),
                        ("wh_main_effect_force_all_campaign_post_battle_loot_mod", C, [10]),
                        ("wh_main_effect_force_all_campaign_movement_range", F, [5])]),
    },
}
# The faction-wide bundle the start script applies (cm:apply_effect_bundle), faction_to_* scopes.
TRAIT_BUNDLE = {
    # Adds to the Hell-Forge: CA's own Lua stacks this very effect key
    # once per cap ritual performed (docs/HELLFORGE_UNIT_CAPS.md).
    "derpy_kharkadon": [("wh3_dlc23_chd_ritual_unit_cap_infernal_ironsworn", "faction_to_faction_own_unseen", 3),
                       (KP + "upkeep", "faction_to_force_own_unseen", -25),
                       ("wh2_main_effect_agent_recruitment_xp_all_agents_and_lords", "faction_to_province_own_factionwide", 4),
                       (KP + "xp", "faction_to_force_own_unseen", 30),
                       ("wh3_dlc23_pooled_resource_chd_armaments_modifier", "faction_to_faction_own_unseen", 15),
                       ("wh3_dlc23_effect_force_stat_leadership_chd_labourers", "faction_to_force_own", -10),
                       ("wh3_dlc23_effect_force_stat_leadership_chd_hobgoblins", "faction_to_force_own", -10),
                       ("wh3_dlc23_effect_upkeep_chd_hobgoblin", "faction_to_force_own_unseen", 25),
                       ("wh3_dlc23_effect_force_recruit_cost_chd_hobgoblins", "faction_to_force_own_unseen", 25)],
    # No replenishment effect covers Chaos Dwarf units alone, so: -15 for the whole army, +15 back
    # for hobgoblins (CA's own hobgoblin effect), which leaves the dwarfs, labourers and engines down.
    "derpy_uzkul": [("wh3_dlc23_effect_technology_chd_convoy_mod_active_convoys", "faction_to_faction_own_unseen", 1),
                    ("wh_main_effect_economy_trade_tariff_mod", "faction_to_faction_own", 15),
                    ("wh_main_effect_force_all_campaign_raid_income", "faction_to_force_own", 20),
                    ("wh_main_effect_force_all_campaign_replenishment_rate", "faction_to_force_own", -15),
                    ("wh3_dlc23_effect_replenishment_rate_hobgoblins", "faction_to_force_own", 15)],
}
ITEMS = {
    "derpy_kharkadon": {"weapon": ("Axe of Hashut's Blood", "Hashut's blood was worked into the axe-head. Its edge burns through flesh and plate alike."),
                       "talisman": ("Shield of the Bloodsworn", "Black iron, brass and the oaths of Zharrduk's guard. Kharkadon carries it into the first rank.")},
    "derpy_uzkul": {"weapon": ("Mingol Cleaver", "A hobgoblin cleaver taken from the last Captain, along with the job."),
                    "talisman": ("Charter Seal", "The brass seal that makes the Company's plunder lawful in Zharr-Naggrund. Mostly.")},
}
ITEM_EFFECTS = {
    "derpy_kharkadon": {
        "weapon": [("wh_main_effect_character_stat_weapon_strength", C, 35),
                   ("wh_main_effect_character_stat_melee_attack", C, 15),
                   ("wh_main_effect_character_stat_bonus_vs_infantry", C, 15),
                   ("wh2_main_effect_character_stat_enable_flaming_attacks", C, 1),
                   ("wh_main_effect_character_stat_enable_magic_attacks", C, 1),
                   ("derpy_kharkadon_enable_hashuts_blood", C, 1)],
        # Keep the old key and unlock; the visible shield now occupies the armour slot.
        "talisman": [("wh_main_effect_character_stat_melee_defence", C, 20),
                     ("wh_main_effect_character_stat_ward_save", C, 15),
                     ("wh_main_effect_character_stat_fire_resistance", C, 40),
                     ("derpy_kharkadon_enable_bloodsworn_bulwark", C, 1)],
    },
}
ITEM_SET_EFFECTS = {"derpy_kharkadon": [(KP + "armour", F, 10), ("wh_main_effect_force_stat_leadership", F, 5),
                                     (KS + "armour", C, 10)]}
SET_NAME = {"derpy_kharkadon": ("Blood and Iron", "The blood-fed axe and the shield of his sworn guard mark Kharkadon's place at the head of the line."),
            "derpy_uzkul": ("Charter and Cleaver", "One half of the Company's business is the charter. The other half is the cleaver.")}
PASSIVE = {"derpy_kharkadon": ("Overlord's Presence", "Where the Overlord stands, his Immortals do not give a step."),
           "derpy_uzkul": ("Captain's Purse", "While the Captain stands, the pay is coming, and the Company holds.")}
# A lord listed here borrows a vanilla icon; one not listed ships ui/battle ui/ability_icons/<sub>_passive.png
PASSIVE_ICON = {"derpy_uzkul": "wh3_dlc23_hero_passive_lucky_git"}
LORE = {"derpy_kharkadon": ("Kharkadon the Vicious, Overlord of Zharrduk, master of the Immortals.",
                           "The Overlords of Zharrduk are the oldest blood in the Dark Lands, and they do not fight "
                           "with slaves. Kharkadon the Vicious marches with the Immortals of the Infernal Guard and "
                           "a court of seasoned lords, and leaves the chain-gangs to the forges."),
        "derpy_uzkul": ("Captain of the Uzkul Mingol Company, a chartered expedition hunting gold in Ind.",
                        "The Uzkul Mingol Company holds a charter from Zharr-Naggrund to find gold, and it has "
                        "gone as far as Ind to find it. Its Chaos Dwarf overseers drive hobgoblins hired along "
                        "the way, and its convoys carry the spoils home along the Ivory Road.")}
UNIT_ICON_SET = {"derpy_kharkadon": "wh3_dlc23_chd_labourers", "derpy_uzkul": "wh3_dlc23_chd_hobgoblins"}

# ------------------------------------------------------------------------------------------ io
def read_tsv(path):
    with io.open(path, encoding="utf-8", newline="") as fh:
        lines = fh.read().split("\n")
    rows = [l for l in lines[2:] if l.strip("\t\r ")]
    return lines[0], lines[1], rows


def write_tsv(rel, hdr, meta, rows):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join([hdr, meta] + rows) + "\n")
    return path


def fragments():
    """(rel path under extract, table or None for loc) for every fragment in the extract."""
    for base, _dirs, files in os.walk(EX):
        for f in files:
            if f.endswith(".tsv"):
                rel = os.path.relpath(os.path.join(base, f), EX)
                parts = rel.split(os.sep)
                yield rel, (parts[1] if parts[0] == "db" else None)


def districts(full=False):
    """DISTRICTS out of toz_districts.py without running it (it writes files on import).
    (key, seats), or with full=True the whole (key, name, seats, effects, blurb) tuple."""
    tree = ast.parse(open(DISTRICTS_PY, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and node.targets[0].id == "DISTRICTS":
            ds = ast.literal_eval(node.value)
            return ds if full else [(d[0], d[2]) for d in ds]
    raise SystemExit("no DISTRICTS in " + DISTRICTS_PY)


# ------------------------------------------------------------------------------------------ build
def swap(s, L):
    s = s.replace(SRC, L["sub"]).replace(SRC_FACTION, L["faction"])
    s = re.sub(r"_fists(?![a-z])", "_" + L["fslug"], s)
    return s.replace("Fists of Hashut", L["house"])


def is_src(row):
    return SRC in row or SRC_FACTION in row or re.search(r"_fists(?![a-z])", row)


def cols(hdr):
    return hdr.split("\t")


_KEYS = {}


def key_fields(table, version):
    """The table's combined key, from RPFM's own schema (is_key) - not guessed from the data."""
    import read_vanilla_db as rvd
    if (table, version) not in _KEYS:
        rvd.defs(table)
        s = rvd._schema[0]
        i = s.find('"%s": [' % table)
        blk = s[i:s.find('_tables": [', i + len(table) + 5)]
        m = re.search(r"version: %d,\s*fields: \[(.*?)\n {16}\]," % version, blk, re.S)
        assert m, "%s v%d not in the schema" % (table, version)
        _KEYS[(table, version)] = re.findall(r'name: "([^"]+)",\s*field_type: \w+,\s*is_key: true', m.group(1))
    return _KEYS[(table, version)]


def keyfn(table, meta, hdr):
    """row -> its combined key. Loc is keyed on its first column; a table with no key column
    (some junctions) on the whole row."""
    if table is None:
        return lambda r: r.split("\t")[0]
    ks = key_fields(table, int(meta.split(";")[1]))
    idx = [cols(hdr).index(k) for k in ks if k in cols(hdr)]
    if not idx:
        return lambda r: r
    return lambda r: tuple(r.split("\t")[i] for i in idx)


def set_col(row, hdr, **kv):
    c, h = row.split("\t"), cols(hdr)
    for k, v in kv.items():
        c[h.index(k)] = str(v)
    return "\t".join(c)


def get_col(row, hdr, k):
    return row.split("\t")[cols(hdr).index(k)]


def custom_battle_portrait(subtype):
    lord = next(lord for lord in LORDS if lord["sub"] == subtype)
    return ("ui/portraits/portholes/no_culture/%s.png" % subtype if "portraits" in lord else
            "ui/portraits/portholes/no_culture/chd_overseer_campaign_01_0.png")


def skill_rows(L):
    """character_skills / level_to_effects rows for one lord, from SKILLS."""
    out_sk, out_fx = {}, []
    for suf, (rank, icon, name, _d, effects) in SKILLS[L["sub"]].items():
        key = "%s_%s" % (L["sub"], suf)
        out_sk[key] = (rank, icon, name)
        for eff, scope, values in effects:
            for lvl, v in enumerate(values, 1):
                out_fx.append("\t".join([key, eff, str(lvl), scope, "%.4f" % v]))
    return out_sk, out_fx


def build():
    """{rel: (hdr, meta, rows, table)} - every fragment that changes, written whole."""
    files = {}
    order = [s for _d, seats in districts() for s in seats]
    district_of = {s: d for d, seats in districts() for s in seats}
    for L in LORDS:
        assert L["fslug"] in district_of, "%s has no seat in toz_districts.py DISTRICTS" % L["fslug"]

    for rel, table in fragments():
        # gen_kharkadon_bodyguards.py owns every *_bodyguards fragment. Its keys match OWNED, so on a
        # fresh extract this loop took them for its own old output and wrote them back EMPTY (found
        # 2026-10-06, caught before any import).
        if table in SKIP or "_bodyguards" in rel or "derpy_kharkadon_personal" in rel:
            continue
        hdr, meta, rows = read_tsv(os.path.join(EX, rel))
        src = [r for r in rows if is_src(r) and not DROP_ROW.search(r)]
        if table is None:
            src = [r for r in src if not SKIP_LOC.search(r.split("\t")[0])]
        if not src and not any(OWNED.search(r) for r in rows):
            continue
        new = []
        for L in LORDS:
            for r in src:
                new.append(fix(swap(r, L), hdr, table, rel, L))
        new = [r for r in new if r is not None]
        # Rows a previous run wrote go; rows anybody else wrote stay. A clone whose KEY is already
        # held by a row we do not own is dropped, so the existing row wins - that is how the
        # Overlords' own Tower rows and their hand-written loc (2026-09-25) survive the clone.
        # SKIP_LOC rows are never cloned here, so one matching OWNED is another tool's - the Great
        # Drill loc gen_hellshard_missions.py writes for both lords, which a re-run used to delete.
        keep = [r for r in rows if not OWNED.search(r) or (table is None and SKIP_LOC.search(r.split("\t")[0]))]
        kf = keyfn(table, meta, hdr)
        held = {kf(r) for r in keep}
        out = keep + [r for r in dict.fromkeys(new) if kf(r) not in held]
        if table == "rituals_tables" and "toz_annex" in rel:
            out = resort_seats(out, hdr, order, district_of)
        files[rel] = (hdr, meta, out, table)

    add_designed(files)
    add_names(files)
    add_skullstack_faction(files)
    add_frontend(files)
    add_kharkadon_personal(files)
    return files


def fix(row, hdr, table, rel, L):
    """Per-table changes to a cloned row. None drops it."""
    sub = L["sub"]
    first = row.split("\t")[0]
    if table == "land_units_tables":
        return set_col(row, hdr, man_animation=L.get("anim", "hu3_dwarf_axe_and_shield_thane"),
                       man_entity="wh3_dlc23_chd_cha_overseer", shield=L.get("shield", "wh_missile_block_55_metal"),
                       armour=L.get("armour", "wh2_main_plate_90"),
                       melee_attack=L["ma"], melee_defence=L["md"])
    if table == "battle_animations_table_tables":     # key = the .bin's name; no own bin, no row
        return set_col(row, hdr, key=L["anim"]) if "anim" in L else None
    if table == "melee_weapons_tables":
        kv = dict(damage=200, ap_damage=220, melee_weapon_type="axe", audio_type="axe",
                  splash_attack_target_size="medium", splash_attack_max_attacks=4, contact_phase="")
        kv.update(L.get("weapon", {}))
        return set_col(row, hdr, **kv)
    if table == "variants_tables":
        return set_col(row, hdr, variant_filename=L.get("mesh") or
                       (L["variant"] if first.endswith("_campaign") else "chd_overseer"))
    if table == "campaign_character_arts_tables":
        return set_col(row, hdr, id=L["arts_id"], land_animation="cam_hu3_dwarf_axe_and_shield")
    if table == "unit_special_abilities_tables":
        return set_col(row, hdr, unique_id=L["ability_id"])
    if table == "unit_abilities_tables" and first == sub + "_passive" and sub in PASSIVE_ICON:
        # swap() renames Balur's icon to <sub>_passive.png; without that file it is a white square
        return set_col(row, hdr, icon_name=PASSIVE_ICON[sub])
    if table == "units_custom_battle_permissions_tables":
        return set_col(row, hdr, general_portrait=custom_battle_portrait(sub))
    if sub == "derpy_kharkadon" and first == sub + "_talisman":
        if table == "ancillaries_tables":
            return set_col(row, hdr, type="wh_main_anc_armour", category="armour")
        if table == "character_skills_tables":
            return set_col(row, hdr, image_path="item_armour.png")
    if table == "character_skills_tables" and first in SKILL_KEYS[sub]:
        rank, icon, name = SKILL_KEYS[sub][first]
        kv = dict(localised_name=name)
        if icon:
            kv.update(image_path=icon)
        return set_col(row, hdr, **kv)
    if table == "character_skill_level_to_effects_junctions_tables" and first in SKILL_KEYS[sub]:
        return None                                     # replaced whole by add_designed()
    if table == "effect_bundles_to_effects_junctions_tables" and first == sub + "_lord_trait":
        return None
    if table == "ancillary_set_effect_junctions_tables" and sub == "derpy_uzkul" \
            and "unit_cap" in row:
        return None
    return row


def resort_seats(rows, hdr, order, district_of):
    by = {get_col(r, hdr, "key").replace("derpy_ritual_chd_toz_annex_", ""): r for r in rows}
    assert set(by) == set(order), "annex rituals %s vs DISTRICTS %s" % (sorted(by), sorted(order))
    return [set_col(by[s], hdr, category=district_of[s], sort_order=i) for i, s in enumerate(order)]


def add_designed(files):
    """The designed skill effects and trait bundle effects, and the loc for everything."""
    for rel in list(files):
        hdr, meta, rows, table = files[rel]
        if table == "character_skill_level_to_effects_junctions_tables" and "unique_skills" in rel:
            for L in LORDS:
                rows += [r for r in skill_rows(L)[1] if not r.startswith(L["sub"] + "_lord_trait")]
        if table == "character_skill_level_to_effects_junctions_tables" and rel.endswith("derpy_chd_ll_trait.tsv"):
            for L in LORDS:
                rows += [r for r in skill_rows(L)[1] if r.startswith(L["sub"] + "_lord_trait")]
                # Balur's lord_trait level-0 row enables his passive; it travels by clone, keep it
                rows += [r for r in [swap("derpy_balur_lord_trait\tderpy_balur_passive\t0\tcharacter_to_character_own\t1.0000", L)]
                         if r not in rows]
        if table == "effect_bundles_to_effects_junctions_tables" and rel.endswith("derpy_chd_ll_traits.tsv"):
            for L in LORDS:
                for eff, scope, v in TRAIT_BUNDLE[L["sub"]]:
                    rows.append("\t".join([L["sub"] + "_lord_trait", eff, scope, "%.4f" % v, "start_turn_completed"]))
        if table == "ancillary_to_effects_tables":
            owned = {s + "_" + slot for s, items in ITEM_EFFECTS.items() for slot in items}
            rows[:] = [r for r in rows if get_col(r, hdr, "ancillary") not in owned]
            for s, items in ITEM_EFFECTS.items():
                for slot, effects in items.items():
                    rows += ["\t".join([s + "_" + slot, effect, scope, "%.4f" % value]) for effect, scope, value in effects]
        if table == "ancillary_set_effect_junctions_tables":
            owned = {s + "_set" for s in ITEM_SET_EFFECTS}
            rows[:] = [r for r in rows if get_col(r, hdr, "set_key") not in owned]
            for s, effects in ITEM_SET_EFFECTS.items():
                rows += ["\t".join([effect, s + "_set", scope, "%.4f" % value]) for effect, scope, value in effects]
        if table is None:
            files[rel] = (hdr, meta, [loc_fix(r) for r in rows], table)


@lru_cache(None)
def native_rows(table):
    import read_vanilla_db as rvd
    return [r for _p, _v, rows in rvd.load(os.path.join(GAME, "db.pack"), table + "_tables") for r in rows]


PERSONAL_EFFECTS = {
    "charge": ("wh3_dlc23_effect_force_stat_charge_bonus_pct_chd_chaos_dwarfs_and_hobgoblins", "melee",
               "Charge bonus: %+n% for Chaos Dwarf melee infantry"),
    "xp": ("wh3_dlc23_chd_effect_xp_gain_rate_infernal_guard", "guard",
           "Experience gain: %+n% for Infernal Guard, Ironsworn and Immortals"),
    "upkeep": ("wh3_dlc23_effect_upkeep_reduction_chd_infernal_guard", "guard",
               "Upkeep: %+n% for Infernal Guard, Ironsworn and Immortals"),
    "defence": ("wh3_dlc23_effect_force_stat_melee_defence_chd_bull_centaurs_lammasu", "elite",
                "Melee defence: %+n for Ironsworn and Immortals"),
    "armour": ("wh3_dlc23_effect_force_stat_armour_chd_infernal_ironsworn", "elite",
               "Armour: %+n for Ironsworn and Immortals"),
    "resistance": ("wh3_dlc23_effect_force_stat_physical_resist_chd_infernal_ironsworn", "elite",
                   "Physical resistance: %+n% for Ironsworn and Immortals"),
}
# Kharkadon's own half of each bonus he shares with his troops. CA's character effects read
# "Upkeep: -15%" with no name, which sat under "Upkeep: -15% for Infernal Guard..." as if the skill
# listed it twice. Each is the native effect cloned with every bonus-value binding it has, so it
# does exactly what the native one did and only the tooltip text changes.
SELF_EFFECTS = {
    "charge": ("wh_main_effect_character_stat_charge_bonus_pct", "Charge bonus: %+n% (Kharkadon)"),
    "xp": ("wh3_main_effect_character_campaign_experience_mod", "Experience gain: %+n% (Kharkadon)"),
    "upkeep": ("wh_main_effect_force_all_campaign_upkeep", "Upkeep: %+n% (Kharkadon)"),
    "defence": ("wh_main_effect_character_stat_melee_defence", "Melee defence: %+n (Kharkadon)"),
    "armour": ("wh_main_effect_character_stat_armour", "Armour: %+n (Kharkadon)"),
    "vigour": ("wh2_dlc10_effect_attribute_enable_perfect_vigour", "Strong Vigour (Kharkadon)"),
    "resistance": ("wh_main_effect_character_stat_physical_resistance", "Physical resistance: %+n% (Kharkadon)"),
}
# CA ships no effect that grants Strong Vigour (fatigue_res), so its self half clones Perfect Vigour's
# effect and rebinds the attribute.
SELF_ATTRIBUTE = {"vigour": "fatigue_res"}


def self_binding(table, suffix):
    if table == "effect_bonus_value_unit_attribute_junctions" and suffix in SELF_ATTRIBUTE:
        return {"unit_attribute": SELF_ATTRIBUTE[suffix]}
    return {}


SELF_BINDINGS = ("effect_bonus_value_ids_unit_sets", "effect_bonus_value_scripted_junctions",
                 "effect_bonus_value_unit_attribute_junctions")
AURA = "derpy_kharkadon_stand_with_your_overlord"
AURA_EFFECT = "derpy_kharkadon_enable_stand_with_your_overlord"
ITEM_ABILITIES = {
    "hashuts_blood": dict(name="Hashut's Blood", donor="wh3_dlc23_weapon_abilities_black_hammer_of_hashut",
                         effect_donor="wh3_dlc23_effect_ability_enable_black_hammer_of_hashut",
                         uid=1863434659, duration=32, radius=0,
                         stats=[("stat_melee_damage_ap", 1.5, "mult"), ("stat_melee_damage_base", 1.5, "mult"),
                                ("stat_melee_attack", 20, "add")],
                         tip="Hashut's blood boils within the axe-head. Every kill stokes its heat; "
                             "the edge leaves blackened armour and flesh fused together."),
    "bloodsworn_bulwark": dict(name="Bloodsworn Bulwark", donor="wh3_dlc23_item_abilities_morgrims_eye",
                              effect_donor="wh3_dlc23_effect_passive_ability_enable_morgrims_eye",
                              uid=894899759, duration=25, radius=35,
                              stats=[("stat_resistance_all", 20, "add"), ("stat_melee_defence", 15, "add")],
                              tip="The names of fallen Bloodsworn are hammered into the shield's black iron. "
                                  "Their oaths outlast their flesh, and Kharkadon calls upon them when the line buckles."),
}
PERSONAL_HEADERS = os.path.join(ROOT, "Modding Files", "templates", "kharkadon_personal_headers.json")


def personal_targets():
    memberships = native_rows("unit_set_to_unit_junctions")
    def members(unit_set):
        return {r["unit_record"] for r in memberships if r["unit_set"] == unit_set and not r["exclude"]}
    ironsworn = members("wh3_dlc23_chd_infernal_ironsworn")
    return {"melee": members("wh3_dlc23_chd_category_chaos_dwarf_melee_infantry"),
            "guard": members("wh3_dlc23_chd_all_infernal_guard") | ironsworn,
            "elite": ironsworn}


def add_kharkadon_personal(files):
    headers = json.load(open(PERSONAL_HEADERS, encoding="utf-8"))
    tables = {t: [] for t in headers}
    loc = {}
    def one(table, **kv):
        return dict(next(r for r in native_rows(table) if all(r[k] == v for k, v in kv.items())))
    def add(table, donor, **kv):
        row = dict(donor, **kv)
        tables[table].append(row)
        return row
    effects = {r["effect"]: r for r in native_rows("effects")}
    for suffix, units in personal_targets().items():
        unit_set = KP + suffix
        add("unit_sets", one("unit_sets", key="wh3_dlc23_chd_infernal_ironsworn"), key=unit_set)
        donor = one("unit_set_to_unit_junctions", unit_set="wh3_dlc23_chd_infernal_ironsworn",
                    unit_record="wh3_dlc23_chd_inf_infernal_ironsworn")
        for unit in sorted(units):
            add("unit_set_to_unit_junctions", donor, unit_set=unit_set, unit_record=unit)
    for suffix, (donor, target, text) in PERSONAL_EFFECTS.items():
        key = KP + suffix
        add("effects", effects[donor], effect=key)
        add("effect_bonus_value_ids_unit_sets", one("effect_bonus_value_ids_unit_sets", effect=donor),
            effect=key, unit_set=KP + target)
        loc["effects_description_" + key] = text
    for suffix, (donor, text) in SELF_EFFECTS.items():
        key = KS + suffix
        add("effects", effects[donor], effect=key, **({"icon": "vigour.png", "icon_negative": "vigour.png"}
                                                      if suffix in SELF_ATTRIBUTE else {}))
        for table in SELF_BINDINGS:
            for r in native_rows(table):
                if r["effect"] == donor:
                    add(table, r, effect=key, **self_binding(table, suffix))
        loc["effects_description_" + key] = text
    attr = one("unit_set_unit_attribute_junctions", key="perfect_vigour_chd_kdaai")
    bind = one("effect_bonus_value_unit_set_unit_attribute_junctions", unit_set_attribute=attr["key"])
    add("effects", effects[bind["effect"]], effect=KP + "vigour", icon="vigour.png", icon_negative="vigour.png")
    add("unit_set_unit_attribute_junctions", attr, key=KP + "vigour_attribute", unit_set=KP + "elite",
        unit_attribute="fatigue_res")
    add("effect_bonus_value_unit_set_unit_attribute_junctions", bind, effect=KP + "vigour",
        unit_set_attribute=KP + "vigour_attribute")
    loc["effects_description_" + KP + "vigour"] = "Strong Vigour for Ironsworn and Immortals"

    donor = "wh3_dlc23_item_abilities_morgrims_eye"
    add("unit_abilities", one("unit_abilities", key=donor), key=AURA)
    add("unit_special_abilities", one("unit_special_abilities", key=donor), key=AURA,
        active_time=25.0, recharge_time=120.0, unique_id=1047410657, ai_usage="augment_melee_area",
        additional_melee_cp=100.0, additional_missile_cp=0.0, affect_siege_equipment=False)
    add("special_ability_phases", one("special_ability_phases", id=donor), id=AURA, duration=25.0)
    add("special_ability_to_special_ability_phase_junctions",
        one("special_ability_to_special_ability_phase_junctions", special_ability=donor),
        special_ability=AURA, phase=AURA)
    for stat in ("stat_melee_attack", "stat_melee_defence"):
        add("special_ability_phase_stat_effects", one("special_ability_phase_stat_effects", stat=stat, how="add"),
            phase=AURA, value=8.0)
    add("special_ability_phase_attribute_effects",
        one("special_ability_phase_attribute_effects", attribute="unbreakable", attribute_type="positive"),
        phase=AURA)
    assert any(r["flag_key"] == "out_of_melee" for r in native_rows("special_ability_invalid_usage_flags"))
    add("special_ability_to_invalid_usage_flags", native_rows("special_ability_to_invalid_usage_flags")[0],
        special_ability=AURA, invalid_usage_flag="out_of_melee")
    add("special_ability_to_auto_deactivate_flags",
        one("special_ability_to_auto_deactivate_flags", deactivate_flag="out_of_melee"), special_ability=AURA)
    bind = one("effect_bonus_value_unit_ability_junctions", unit_ability=donor, bonus_value_id="enable")
    add("effects", effects[bind["effect"]], effect=AURA_EFFECT)
    add("effect_bonus_value_unit_ability_junctions", bind, effect=AURA_EFFECT, unit_ability=AURA)
    loc["effects_description_" + AURA_EFFECT] = 'Ability: "Stand With Your Overlord"'
    loc["unit_abilities_onscreen_name_" + AURA] = "Stand With Your Overlord"
    loc["unit_abilities_tooltip_text_" + AURA] = SKILLS["derpy_kharkadon"]["3"][3]

    for suffix, spec in ITEM_ABILITIES.items():
        ability, effect = "derpy_kharkadon_" + suffix, "derpy_kharkadon_enable_" + suffix
        donor = spec["donor"]
        ua = one("unit_abilities", key=donor)
        add("unit_abilities", ua, key=ability, icon_name=ability)   # own icon, shipped by write_all()
        add("unit_special_abilities", one("unit_special_abilities", key=donor), key=ability,
            active_time=float(spec["duration"]), recharge_time=120.0, effect_range=float(spec["radius"]),
            unique_id=spec["uid"], ai_usage="augment_melee_area" if spec["radius"] else "augment_melee_self",
            additional_melee_cp=100.0, additional_missile_cp=0.0, affect_siege_equipment=False)
        add("special_ability_phases", one("special_ability_phases", id=donor), id=ability,
            duration=float(spec["duration"]), imbue_contact="", phase_display="wh_main_generic_ward_save_all" if spec["radius"]
            else "wh_main_generic_buff_attack")
        add("special_ability_to_special_ability_phase_junctions",
            one("special_ability_to_special_ability_phase_junctions", special_ability=donor),
            special_ability=ability, phase=ability)
        for stat, value, how in spec["stats"]:
            add("special_ability_phase_stat_effects", one("special_ability_phase_stat_effects", stat=stat, how=how),
                phase=ability, value=float(value))
        add("effects", effects[spec["effect_donor"]], effect=effect)
        add("effect_bonus_value_unit_ability_junctions",
            one("effect_bonus_value_unit_ability_junctions", unit_ability=donor, bonus_value_id="enable"),
            effect=effect, unit_ability=ability)
        loc["effects_description_" + effect] = 'Ability: "%s"' % spec["name"]
        loc["unit_abilities_onscreen_name_" + ability] = spec["name"]
        loc["unit_abilities_tooltip_text_" + ability] = spec["tip"]

    for table, rows in tables.items():
        definition = headers[table]
        columns = definition["columns"]
        assert all(set(r) == set(columns) for r in rows), table + ": donor schema differs from RPFM header"
        def fmt(value):
            if isinstance(value, float):
                return "%.4f" % value
            return str(value).lower() if isinstance(value, bool) else str(value)
        rel = os.path.join("db", table + "_tables", "derpy_kharkadon_personal.tsv")
        path = rel.replace(os.sep, "/")[:-4]
        files[rel] = ("\t".join(columns), "#%s_tables;%d;%s" % (table, definition["version"], path),
                      ["\t".join(fmt(r[c]) for c in columns) for r in rows], table + "_tables")
    rel = os.path.join("text", "derpy_kharkadon_personal.loc.tsv")
    files[rel] = ("key\ttext\ttooltip", "#Loc;1;text/derpy_kharkadon_personal.loc\t\t",
                  ["%s\t%s\tfalse" % (k, v) for k, v in sorted(loc.items())], None)


LOC = {}


def loc_text():
    """Every player-facing string, keyed by loc key."""
    # The districts' names and reward text follow toz_districts.py, as their seat order does:
    # a seat moved between districts takes its house's name out of one blurb and into another.
    for cat, name, _seats, _fx, blurb in districts(full=True):
        bundle = "wh3_dlc23_chd_toz_" + cat.lower() + "_reward"
        LOC["ritual_categories_display_name_" + cat] = name
        LOC["effect_bundles_localised_title_" + bundle] = name
        LOC["effect_bundles_localised_description_" + bundle] = blurb
    for L in LORDS:
        s = L["sub"]
        for suf, (_r, _i, name, desc, _e) in SKILLS[s].items():
            LOC["character_skills_localised_name_%s_%s" % (s, suf)] = name
            LOC["character_skills_localised_description_%s_%s" % (s, suf)] = desc
        LOC["effect_bundles_localised_title_%s_lord_trait" % s] = SKILLS[s]["lord_trait"][2]
        LOC["effect_bundles_localised_description_%s_lord_trait" % s] = SKILLS[s]["lord_trait"][3]
        LOC["character_skill_node_sets_enc_title_%s_skills" % s] = SKILLS[s]["lord_trait"][2]
        for slot, (n, d) in ITEMS[s].items():
            k = "%s_%s" % (s, slot)
            LOC["character_skills_localised_name_" + k] = n
            LOC["character_skills_localised_description_" + k] = d
            LOC["ancillaries_onscreen_name_" + k] = n
            LOC["ancillaries_colour_text_" + k] = d
        LOC["ancillary_sets_name_%s_set" % s], LOC["ancillary_sets_description_%s_set" % s] = SET_NAME[s]
        pn, pd = PASSIVE[s]
        LOC["effects_description_%s_passive" % s] = 'Passive Ability: "%s"' % pn
        LOC["unit_abilities_onscreen_name_%s_passive" % s] = pn
        LOC["special_ability_phases_onscreen_name_%s_passive" % s] = pn
        LOC["unit_abilities_tooltip_text_%s_passive" % s] = pd
        LOC["land_units_onscreen_name_" + s] = L["name"]
        LOC["unit_description_short_texts_text_%s_description" % s] = LORE[s][0]
        LOC["unit_description_historical_texts_text_%s_description" % s] = LORE[s][1]
        if L["name_id"]:
            LOC["names_name_" + L["name_id"]] = L["name"]
        for k in ("onscreen_name", "colour_text", "explanation_text", "removal_text"):
            LOC["character_trait_levels_%s_%s_defeat_lord_trait" % (k, s)] = "PLACEHOLDER"
        f = L["fslug"]
        LOC["rituals_display_name_derpy_ritual_chd_toz_annex_" + f] = "Confederate with the " + L["house"]
        LOC["rituals_description_derpy_ritual_chd_toz_annex_" + f] = "Bring the %s to heel beneath your own." % L["house"]
        for p in L["frontend"]:
            LOC["frontend_faction_leaders_frontend_description_" + p] = LORE[s][1]
            for k in ("localised_description", "localised_action_points", "loading_screen_text"):
                LOC.setdefault("frontend_faction_leaders_%s_%s" % (k, p), "")


def loc_fix(row):
    c = row.split("\t")
    if c[0] in LOC:
        c[1] = LOC[c[0]]
    return "\t".join(c)


def add_names(files):
    rel = os.path.join("db", "names_tables", "!!derpy_chd_legendary_lords.tsv")
    hdr, meta, rows = read_tsv(os.path.join(EX, rel))
    ids = {L["name_id"] for L in LORDS if L["name_id"]}
    rows = [r for r in rows if r.split("\t")[0] not in ids | RETIRED_NAME_IDS]
    rows += ["\t".join([i, "names_chd_chaos_dwarfs", "forename", "m", "0"]) for i in sorted(ids)]
    files[rel] = (hdr, meta, rows, "names_tables")
    rel = os.path.join("text", "derpy_chd_ll_names.loc.tsv")
    hdr, meta, rows, _t = files.get(rel) or (*read_tsv(os.path.join(EX, rel)), None)
    keys = {"names_name_" + i for i in ids}
    retired = {"names_name_" + i for i in RETIRED_NAME_IDS}
    rows = [r for r in rows if r.split("\t")[0] not in keys | retired]
    rows += ["\t".join([k, LOC[k], "false"]) for k in sorted(keys)]
    files[rel] = (hdr, meta, rows, None)


def add_skullstack_faction(files):
    """IEE's own cr_chd_skullstack factions row, in our fragment. The --import verify compares it
    back out of the saved pack, so a formatting slip here shows up as a DIFF there."""
    import read_vanilla_db as rvd
    iee = {r["key"]: r for _p, _v, rows in rvd.load(IEE_PACK, "factions_tables") for r in rows}
    src = iee["cr_chd_skullstack"]
    hdr, meta, rows = read_tsv(os.path.join(EX, FACTIONS_REL))
    h = cols(hdr)
    ours = {r.split("\t")[0]: r.split("\t") for r in rows}

    def cell(row, c):
        # RPFM's TSV: an r/g/b float triplet is ONE "<name>_hex" column, a u32 colour is %06X
        if c.endswith("_hex"):
            b = c[:-4]
            return "%02X%02X%02X" % tuple(int(row[b + s]) for s in ("_r", "_g", "_b"))
        v = row[c]
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, float):
            return "%.4f" % v
        if isinstance(v, int) and "colour" in c:
            return "%06X" % v
        return str(v)
    # Proof the formatter is RPFM's: it must reproduce our uzkulak row - IEE's row - cell for cell.
    want = ours["cr_chd_warfleet_of_uzkulak"]
    got = [cell(iee["cr_chd_warfleet_of_uzkulak"], c) for c in h]
    assert got == want, [(c, g, w) for c, g, w in zip(h, got, want) if g != w]
    rows = [r for r in rows if not r.startswith("cr_chd_skullstack\t")] + \
           ["\t".join(cell(src, c) for c in h)]
    files[FACTIONS_REL] = (hdr, meta, rows, "factions_tables")


def add_frontend(files):
    """One lord-select row per political party key the faction already has in its own campaign.
    The party key is campaign-bound - an invented one is never shown - so these are the keys
    IEE (skullstack) and Mixer (IE, the Overlords) define, plus the Old World's own pair
    (!cr_oldworld_campaign.pack, cr_mixer_factions_being_used), which we override: its rows name a
    Sorcerer-Prophet / mixer_dummy, so lord select showed their Lord effects and an empty Faction
    effects list. Faction effects is FactionEffectBundle = the agent subtype's
    faction_starting_general_effects bundle (<sub>_lord_trait); Lord effects is that subtype's skills."""
    rel = os.path.join("db", "frontend_faction_leaders_tables", "!!derpy_cr_new_factions.tsv")
    hdr, meta, rows = read_tsv(os.path.join(EX, rel))
    tmpl = [r for r in rows if r.startswith("cr_political_party_combi_chd_warfleet_of_uzkulak\t")][0]
    mine = {p for L in LORDS for p in L["frontend"]}
    rows = [r for r in rows if r.split("\t")[0] not in mine]
    for L in LORDS:
        for p in L["frontend"]:
            rows.append(set_col(tmpl, hdr, key=p, agent_subtype_record=L["sub"], faction=L["faction"],
                                character_image="ui/portraits/faction_leaders/%s.png" % L["sub"]))
    files[rel] = (hdr, meta, rows, "frontend_faction_leaders_tables")
    rel = os.path.join("text", "derpy_chd_ll_factions.loc.tsv")
    hdr, meta, rows = read_tsv(os.path.join(EX, rel))
    keys = [k for k in LOC if k.startswith("frontend_faction_leaders_") and any(k.endswith(p) for p in mine)]
    rows = [r for r in rows if r.split("\t")[0] not in keys] + ["\t".join([k, LOC[k], "false"]) for k in keys]
    files[rel] = (hdr, meta, rows, None)


SKILL_KEYS = {}
for _L in LORDS:
    SKILL_KEYS[_L["sub"]] = skill_rows(_L)[0]
loc_text()


# ------------------------------------------------------------------------------------------ art
def portrait_bin():
    """CA's Overseer porthole blocks under our two art set ids. Same format and reader as
    tools/gen_portrait_settings.py - a minted art set id with no entry draws the placeholder."""
    import gen_portrait_settings as gps
    ver, entries = gps.parse(gps.read_settings(os.path.join(GAME, "ui.pack"),
                                               "ui/portraits/portholes/portrait_settings__.bin"))
    by = {e[0]: e for e in entries}
    out = []
    for L in LORDS:
        _k, body, head, variants = by[L["donor_art"]]
        if "portraits" in L:    # his own files, in the shape of the 13 lords' entries: variant = uniform = stem, no masks
            variants = [[L["sub"], PORTRAIT_FILES["porthole"] % L["sub"], "", "", ""]]
        out.append((L["sub"], body, head, variants))
    return gps.dump(ver, out), out


# pack path, source file in a lord's `portraits` folder, size
PORTRAIT_FILES = {"porthole": "ui/portraits/portholes/no_culture/%s.png",
                  "card": "ui/portraits/units/no_culture/%s.png"}
PORTRAIT_SOURCES = {"porthole": ("porthole.png", (300, 164)), "card": ("card.png", (60, 130)),
                    "leader": ("modern.png", (85, 115))}


def own_portrait(L, kind):
    """The bytes of one of a lord's own portrait files, size-checked."""
    from PIL import Image
    name, size = PORTRAIT_SOURCES[kind]
    path = os.path.join(L["portraits"], name)
    assert Image.open(path).size == size, "%s is not %dx%d" % (path, size[0], size[1])
    return open(path, "rb").read()


# Hand-edited Lua this feature touches, packed from Modding Files/pack as they stand. The four
# zz_derpy_toz_annex.lua copies carry the two seats (ANNEX_DISTRICTS must match toz_districts.py).
SCRIPTS = ["script/campaign/mod/derpy_start_new_house_lords.lua",
           "script/campaign/mod/derpy_hll_settings.lua",
           "script/mct/settings/derpy_hll.lua",
           "script/frontend/mod/mixerstuffies.lua",
           # starting wars - Skullstack vs cr_skv_clan_festerlingus (IEE); OW / DL copies identical
           "script/campaign/cr_combi_expanded/mod/derpy_hashut_ll_war_start.lua",
           "script/campaign/cr_oldworld/mod/derpy_chd_ll_war_start.lua",
           "script/campaign/cr_darklands/mod/derpy_chd_ll_war_start.lua",
           "script/campaign/cr_combi_expanded/mod/cr_iee_campaign_chd_tower_of_zharr.lua"] + \
          ["script/campaign/%s/mod/oldworld_wh3_dlc23_campaign_chd_tower_of_zharr.lua" % c for c in ("cr_oldworld", "cr_darklands")] + \
          ["script/campaign/%s/mod/debug_conclave_influence.lua" % c for c in ("cr_oldworld", "cr_darklands")] + \
          ["script/campaign/%s/mod/zz_derpy_toz_annex.lua" % c
           for c in ("cr_oldworld", "cr_darklands", "cr_combi_expanded", "wh3_main_combi")]

# Lord-select 3D model. Mixer's campaign_select_new.twui.xml creates front_end_models/<startpos
# character id>/3d_model, else front_end_models/<faction key>/3d_model. The faction key needs no
# startpos id and holds in every campaign. Cloned from Balur's pair: only the mesh and the anim differ.
FE_MODEL_DIR = "ui/frontend ui/front_end_models/"
FE_DONOR = "1383677823"     # Balur
FE_DONOR_MESH = "VariantMeshes/VariantMeshDefinitions/derpy_balur.VariantMeshDefinition"
FE_DONOR_ANIM = r"animations\battle\humanoid03\dual_axe\celebrate\hu3_dual_axe_celebrate_01.anim"


def frontend_model(L):
    """{pack path: text} for one lord's lord-select model: the CA Overseer campaign variant he wears."""
    d = os.path.join(ROOT, "Modding Files", "pack", *(FE_MODEL_DIR + FE_DONOR).split("/"))
    twui = open(os.path.join(d, "3d_model.twui.xml"), encoding="utf-8").read()
    req = open(os.path.join(d, FE_DONOR + ".warscape_req.xml"), encoding="utf-8").read()
    assert twui.count(FE_DONOR_MESH) == 1 and twui.count(FE_DONOR_ANIM) == 1 and req.count(FE_DONOR_MESH) == 1
    mesh = "VariantMeshes/VariantMeshDefinitions/%s.VariantMeshDefinition" % L.get("mesh", L["variant"])
    base = FE_MODEL_DIR + L["faction"] + "/"
    return {base + "3d_model.twui.xml": twui.replace(FE_DONOR_MESH, mesh).replace(FE_DONOR_ANIM, L["fe_anim"]),
            base + L["faction"] + ".warscape_req.xml": req.replace(FE_DONOR_MESH, mesh)}


def check_frontend_models(models=None):
    """Every mesh and anim the lord-select models name is in CA's packs (a wrong path draws nothing,
    silently), and each file still parses as XML."""
    import xml.etree.ElementTree as ET
    from read_pack_index import paths
    if models is None:
        models = {}
        for L in LORDS:
            models.update(frontend_model(L))
    have = set()
    for fp in glob.glob(os.path.join(GAME, "variants*.pack")) + glob.glob(os.path.join(GAME, "anim*.pack")) + [ASSETS]:
        have.update(p.lower() for p in paths(fp))
    bad = []
    for p, text in sorted(models.items()):
        try:
            ET.fromstring(text)
        except ET.ParseError as e:
            bad.append("%s: not XML (%s)" % (p, e))
        for ref in re.findall(r'(?:\sfilepath|path value)="([^"]+)"', text):
            if ref.replace("\\", "/").lower() not in have:
                bad.append("%s: %s is in none of CA's variants / anim packs or the assets pack" % (p, ref))
    return bad


# The live assets pack (Workshop folder - the game loads that copy, not a local build).
ASSETS = r"F:\SteamLibrary\steamapps\workshop\content\1142710\3297605217\!!!derpy_chd_assets.pack"


def check_own_models(lords=None):
    """A lord with his own `mesh` / `anim` names files only the assets pack ships: the
    variantmeshdefinition, and animations/database/battle/bin/<anim>.bin inside one of its
    .animpacks. A missing one is a silent T-pose or invisible lord, not an error."""
    import lz4.frame
    import read_animpack as ra
    from read_pack_index import paths, read
    lords = LORDS if lords is None else lords
    have = {p.lower() for p in paths(ASSETS)}
    bins = set()
    for p in (p for p in have if p.endswith(".animpack")):
        _p, comp, d = read(ASSETS, p)[0]
        if comp:
            d = lz4.frame.decompress(d[4:])
        bins.update(i[0].lower() for i in ra.read_animpack(d))
    bad = []
    for L in lords:
        if "mesh" in L and "variantmeshes/variantmeshdefinitions/%s.variantmeshdefinition" % L["mesh"] not in have:
            bad.append("%s: mesh %s is not in the assets pack" % (L["sub"], L["mesh"]))
        if "anim" in L and "animations/database/battle/bin/%s.bin" % L["anim"] not in bins:
            bad.append("%s: anim bin %s.bin is in no assets-pack .animpack" % (L["sub"], L["anim"]))
    return bad


PORTRAIT_PATHS = ["ui/portraits/portholes/portrait_settings_derpy_hll_new_lords.bin",
                  "ui/portraits/units/portrait_settings_derpy_hll_new_lords.bin"]


def _ca_png(path):
    from read_pack_index import read
    from PIL import Image
    import zstandard
    _p, comp, data = read(os.path.join(GAME, "ui.pack"), path)[0]
    if data[:4] != b"\x89PNG":
        size, = struct.unpack("<I", data[:4])
        data = zstandard.ZstdDecompressor().decompress(data[4:], max_output_size=size)
    return Image.open(io.BytesIO(data)).convert("RGBA")


def leader_png(L):
    """The lord-select picture, in CA's own shape: an 85x115 bust on the red ground of
    Astragoth's card. The Overseer porthole is a 300x164 render with the face at x~150, so it
    is cropped to the card's aspect around the face rather than shipped whole - shipped whole,
    it was squashed into the card slot. A lord with his own `portraits` ships his own instead."""
    if "portraits" in L:
        return own_portrait(L, "leader")
    card = _ca_png("ui/portraits/faction_leaders/chd_astragoth_ironhand_0.png")
    src = _ca_png("ui/portraits/portholes/no_culture/%s_0.png" % L["variant"])
    from PIL import Image
    w = int(round(src.height * card.width / card.height))
    x0 = max(0, min(src.width - w, 150 - w // 2))
    out = card.crop((2, 0, 3, card.height)).resize(card.size)       # CA's ground, edge column stretched
    out.alpha_composite(src.crop((x0, 0, x0 + w, src.height)).resize(card.size, Image.LANCZOS))
    assert out.size == (85, 115), out.size
    buf = io.BytesIO()
    out.save(buf, "PNG")
    return buf.getvalue()


# ------------------------------------------------------------------------------------------ checks
def vanilla_pairs():
    """Every (effect, scope) pair CA uses, plus every effect key CA defines."""
    import read_vanilla_db as rvd
    db = os.path.join(GAME, "db.pack")
    pairs, effects = set(), set()
    for table, e, s in (("character_skill_level_to_effects_junctions_tables", "effect_key", "effect_scope"),
                        ("effect_bundles_to_effects_junctions_tables", "effect_key", "effect_scope"),
                        ("ancillary_to_effects_tables", "effect", "effect_scope")):
        for _p, _v, rows in rvd.load(db, table):
            for r in rows:
                pairs.add((r[e], r[s]))
    for _p, _v, rows in rvd.load(db, "effects_tables"):
        effects.update(r["effect"] for r in rows)
    # A unit-set effect targets through its bonus value, not its key. CA wires effects it never
    # grants (the Ironsworn's armour, the Infernal Guard's charge reflection), so a scope another
    # effect on the same bonus value is granted with is valid for them too.
    import collections
    scopes, by_bv = collections.defaultdict(set), collections.defaultdict(set)
    for e, s in pairs:
        scopes[e].add(s)
    for table in ("effect_bonus_value_ids_unit_sets_tables",
                  "effect_bonus_value_unit_set_unit_attribute_junctions_tables",
                  "effect_bonus_value_unit_set_unit_ability_junctions_tables"):
        for _p, _v, rows in rvd.load(db, table):
            for r in rows:
                by_bv[(table, r["bonus_value_id"])].add(r["effect"])
    for effs in by_bv.values():
        shared = set().union(*(scopes[e] for e in effs))
        pairs.update((e, s) for e in effs for s in shared)
    return pairs, effects


def pack_pairs():
    pairs, effects = set(), set()
    for rel, table in fragments():
        if table not in ("character_skill_level_to_effects_junctions_tables",
                         "effect_bundles_to_effects_junctions_tables", "ancillary_to_effects_tables",
                         "effects_tables"):
            continue
        hdr, _m, rows = read_tsv(os.path.join(EX, rel))
        h = cols(hdr)
        for r in rows:
            if OWNED.search(r):
                continue
            c = dict(zip(h, r.split("\t")))
            if table == "effects_tables":
                effects.add(c["effect"])
            else:
                pairs.add((c.get("effect_key") or c.get("effect"), c["effect_scope"]))
    return pairs, effects


def check(files, pairs=None):
    bad = []
    if pairs is None:
        vp, ve = vanilla_pairs()
        pp, pe = pack_pairs()
        pairs, effects = vp | pp, ve | pe
    else:
        pairs, effects = pairs
    pairs, effects = set(pairs), set(effects)
    bad += check_kharkadon_personal(files) + check_kharkadon_items(files)
    # Custom scope precedents come from each cloned binding, not merely from the custom key existing.
    for suffix, (donor, _target, _text) in PERSONAL_EFFECTS.items():
        effects.add(KP + suffix)
        pairs.update((KP + suffix, scope) for effect, scope in list(pairs) if effect == donor)
    for suffix, (donor, _text) in SELF_EFFECTS.items():
        effects.add(KS + suffix)
        pairs.update((KS + suffix, scope) for effect, scope in list(pairs) if effect == donor)
    attr = next(r for r in native_rows("effect_bonus_value_unit_set_unit_attribute_junctions")
                if r["unit_set_attribute"] == "perfect_vigour_chd_kdaai")
    effects.add(KP + "vigour")
    pairs.update((KP + "vigour", scope) for effect, scope in list(pairs) if effect == attr["effect"])
    ability_donor = "wh3_dlc23_effect_passive_ability_enable_morgrims_eye"
    effects.add(AURA_EFFECT)
    pairs.update((AURA_EFFECT, scope) for effect, scope in list(pairs) if effect == ability_donor)
    for suffix, spec in ITEM_ABILITIES.items():
        key = "derpy_kharkadon_enable_" + suffix
        effects.add(key)
        pairs.update((key, scope) for effect, scope in list(pairs) if effect == spec["effect_donor"])
    for s in SKILLS:
        designed = [(e, sc) for _r, _i, _n, _d, fx in SKILLS[s].values() for e, sc, _v in fx]
        designed += [(e, sc) for e, sc, _v in TRAIT_BUNDLE[s]]
        designed += [(e, sc) for fx in ITEM_EFFECTS.get(s, {}).values() for e, sc, _v in fx]
        designed += [(e, sc) for e, sc, _v in ITEM_SET_EFFECTS.get(s, [])]
        for e, sc in designed:
            if e not in effects:
                bad.append("%s: no such effect %s" % (s, e))
            elif (e, sc) not in pairs:
                bad.append("%s: %s is never used with scope %s" % (s, e, sc))
        for suf, (_r, _i, _n, _d, fx) in SKILLS[s].items():
            levels = {len(v) for _e, _s, v in fx}
            if len(levels) != 1:
                bad.append("%s_%s: effects disagree on level count %s" % (s, suf, levels))
    text = "\n".join(r for _h, _m, rows, _t in files.values() for r in rows if OWNED.search(r))
    for word in ("Balur", "Baalrgath", "Fists", "fists", "balur"):
        if word in text:
            line = [l for l in text.split("\n") if word in l][0]
            bad.append("leftover %r: %s" % (word, line[:160]))
    # every new lord has the pieces a house lord has
    for L in LORDS:
        s = L["sub"]
        need = {"agent_subtypes_tables": s, "land_units_tables": s, "main_units_tables": s,
                "campaign_character_art_sets_tables": s, "campaign_character_arts_tables": L["arts_id"],
                "agent_uniforms_tables": s, "variants_tables": s + "_campaign",
                "character_skill_node_sets_tables": s + "_skills", "effect_bundles_tables": s + "_lord_trait",
                "faction_agent_permitted_subtypes_tables": L["faction"],
                "rituals_tables": "derpy_ritual_chd_toz_annex_" + L["fslug"],
                "campaign_group_member_criteria_factions_tables": L["faction"],
                "incidents_tables": "wh3_dlc23_chd_toz_seat_claimed_" + L["faction"]}
        for table, key in need.items():
            if not any(table == t and any(key in r.split("\t") for r in rows) for _h, _m, rows, t in files.values()):
                # the Overlords' Tower rows predate this script and may be untouched
                if not any(table == t and any(key in r.split("\t") for r in read_tsv(os.path.join(EX, rel))[2])
                           for rel, t in fragments()):
                    bad.append("%s: nothing in %s for %s" % (s, table, key))
        n_set = sum(1 for _h, _m, rows, t in files.values() if t == "character_skill_node_set_items_tables"
                    for r in rows if r.startswith(s + "_skills\t"))
        n_src = sum(1 for _h, _m, rows, t in files.values() if t == "character_skill_node_set_items_tables"
                    for r in rows if r.startswith(SRC + "_skills\t"))
        if n_set != n_src:
            bad.append("%s: %d skill set items, Balur has %d" % (s, n_set, n_src))
    # loc: every key a clone produced has text, unless Balur's was empty too
    for rel, (_h, _m, rows, t) in files.items():
        if t is None:
            for r in rows:
                k = r.split("\t")[0]
                if OWNED.search(k) and k in LOC and r.split("\t")[1] != LOC[k]:
                    bad.append("loc not applied: " + k)
    ids = [L["arts_id"] for L in LORDS] + [L["ability_id"] for L in LORDS] + [L["name_id"] for L in LORDS if L["name_id"]]
    assert len(set(ids)) == len(ids)
    return bad


FACTION_FK = {"faction_agent_permitted_subtypes_tables": "faction",
              "effect_bonus_value_faction_junctions_tables": "faction",
              "campaign_group_member_criteria_factions_tables": "faction",
              "frontend_faction_leaders_tables": "faction"}


def check_faction_refs(files):
    """Every factions.key this pack references must be defined by CA or by this pack itself. One
    that only another mod defines makes the engine refuse the whole pack for a player without it."""
    import read_vanilla_db as rvd
    known = {r["key"] for _p, _v, rows in rvd.load(os.path.join(GAME, "db.pack"), "factions_tables") for r in rows}
    frags = {rel: (h, m, rows, t) for rel, t in fragments() for h, m, rows in [read_tsv(os.path.join(EX, rel))]
             if t in set(FACTION_FK) | {"factions_tables"}}
    frags.update({rel: v for rel, v in files.items() if v[3] in set(FACTION_FK) | {"factions_tables"}})
    for h, _m, rows, t in frags.values():
        if t == "factions_tables":
            known.update(r.split("\t")[0] for r in rows)
    bad = []
    for rel, (h, _m, rows, t) in frags.items():
        if t in FACTION_FK:
            for r in rows:
                f = get_col(r, h, FACTION_FK[t])
                if f and f not in known:
                    bad.append("%s references faction %s, which neither CA nor this pack defines" % (rel, f))
    return bad


def check_ids_unique():
    """The minted numeric ids must not collide with anything the pack or CA already uses."""
    import read_vanilla_db as rvd
    bad = []
    db = os.path.join(GAME, "db.pack")
    for table, col, attr in (("campaign_character_arts_tables", "id", "arts_id"),
                             ("unit_special_abilities_tables", "unique_id", "ability_id"),
                             ("names_tables", "id", "name_id")):
        used = set()
        for _p, _v, rows in rvd.load(db, table):
            used.update(str(r[col]) for r in rows)
        for rel, t in fragments():
            if t == table:
                hdr, _m, rows = read_tsv(os.path.join(EX, rel))
                # names rows carry no owned key, so recognise the exact row add_names() writes
                ours = {"\t".join([L["name_id"], "names_chd_chaos_dwarfs", "forename", "m", "0"]) for L in LORDS
                        if L["name_id"]}
                used.update(get_col(r, hdr, col) for r in rows if not OWNED.search(r) and r not in ours)
        for L in LORDS:
            if L[attr] in used:
                bad.append("%s %s already used in %s" % (attr, L[attr], table))
    return bad


START = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod", "derpy_start_new_house_lords.lua")
READER = os.path.join(os.path.dirname(START), "derpy_hll_settings.lua")
LUA = r"C:\Program Files (x86)\Lua\5.1\lua.exe"
START_HARNESS = r'''
local START, CASE, READER = ...
local log, spawned, killed, bundles = {}, {}, {}, {}
function out(s) table.insert(log, s) end
local function list(items) return {num_items = function() return #items end,
                                   item_at = function(_, i) return items[i + 1] end} end
local function unit(key, cmd) return {unit_key = function() return key end,
                                      has_unit_commander = function() return cmd end} end
local function faction(key, army)
    local leader = {character_subtype_key = function() return "wh3_dlc23_chd_overseer" end,
        is_null_interface = function() return false end,
        has_military_force = function() return army ~= nil end,
        military_force = function() return {unit_list = function() return list(army) end} end,
        has_region = function() return true end,
        region = function() return {name = function() return key.."_home" end} end,
        logical_position_x = function() return 100 end, logical_position_y = function() return 200 end,
        command_queue_index = function() return 7 end}
    return {is_null_interface = function() return false end, is_dead = function() return false end,
            faction_leader = function() return leader end, has_home_region = function() return true end}
end
local present = {}
local switch = {derpy_kharkadon = true, derpy_uzkul = true}
if CASE == "inherit" or CASE == "oldworld" then
    present.wh3_dlc23_chd_minor_faction = faction("wh3_dlc23_chd_minor_faction",
        {unit("lord_unit", true), unit("u_a", false), unit("hero_unit", true), unit("u_b", false)})
elseif CASE == "fallback" then
    present.wh3_dlc23_chd_minor_faction = faction("wh3_dlc23_chd_minor_faction", nil)
elseif CASE == "switch" then
    present.wh3_dlc23_chd_minor_faction = faction("wh3_dlc23_chd_minor_faction", {unit("u_a", false)})
    switch.derpy_kharkadon = false
elseif CASE == "uzkul" then
    present.cr_chd_skullstack = faction("cr_chd_skullstack", {unit("u_c", false)})
end
local heroes = {}
dofile(READER)    -- the shipped derpy_hll_start_hero
function derpy_hll_lord_on(s) return switch[s] end
local cb
cm = {}
function cm:get_faction(k) return present[k] or false end
function cm:get_local_faction_name() error("local faction read") end   -- throws in multiplayer
function cm:get_local_faction() error("local faction read") end
local finds = {}
function cm:find_valid_spawn_location_for_character_from_position(f, x, y, same, dist)
    table.insert(finds, x.."\t"..y.."\t"..tostring(dist))
    return x + 1, y
end
-- only the Old World map has cr_oldworld_ regions; elsewhere region_by_key is a null interface
local region_manager = {region_by_key = function(_, k)
    local on = CASE == "oldworld" and k:find("^cr_oldworld_region_") ~= nil
    return {is_null_interface = function() return not on end}
end}
function cm:model() return {world = function() return {region_manager = function() return region_manager end} end} end
function cm:disable_event_feed_events() end
function cm:char_lookup_str(c) return "character_cqi:"..c end
function cm:set_character_immortality() end
function cm:set_character_unique() end
function cm:kill_character(c, destroy) table.insert(killed, {c, destroy}) end
function cm:create_force_with_general(f, units, region, x, y, typ, sub, fore, a, b, c, leader, fn)
    table.insert(spawned, {f = f, units = units, region = region, x = x, sub = sub, fore = fore,
                           family = b, leader = leader})
    fn(42)
end
function cm:get_character_by_cqi(c)
    return {has_military_force = function() return true end,
            military_force = function() return {id = "force"..c} end,
            logical_position_x = function() return 101 end, logical_position_y = function() return 200 end}
end
function cm:create_agent(f, typ, sub, x, y)
    local a = {f = f, typ = typ, sub = sub, x = x}
    table.insert(heroes, a)
    return a
end
function cm:embed_agent_in_force(a, force) a.force = force.id end
function cm:apply_effect_bundle(b, f, t) table.insert(bundles, b.."@"..f.."/"..t) end
function cm:add_first_tick_callback_new(fn) cb = fn end
dofile(START)
cb()
for _, s in ipairs(spawned) do
    print("SPAWN", s.f, s.sub, s.fore, s.family, s.units, s.region, s.x, tostring(s.leader))
end
for _, a in ipairs(heroes) do print("HERO", a.f, a.typ, a.sub, a.x, tostring(a.force)) end
for _, k in ipairs(killed) do print("KILL", k[1], tostring(k[2])) end
for _, b in ipairs(bundles) do print("BUNDLE", b) end
for _, s in ipairs(finds) do print("FIND", s) end
for _, l in ipairs(log) do if l:find("ERROR") then print("LOGERR", l) end end
'''


def check_army(sub, units):
    """The army a start script spawns: CA units that exist (a typo spawns nothing, silently), none of
    the old leader's (the harness gives him u_a / u_b / u_c), within the Hell-Forge starting limits
    plus what the lord's own trait bundle adds, and for the Overlords no slave or hobgoblin."""
    import collections
    import read_vanilla_db as rvd
    db = os.path.join(GAME, "db.pack")
    known = {r["unit"] for _p, _v, rows in rvd.load(db, "main_units_tables") for r in rows}
    cap = {r["unit_list"]: int(r["point_cap"]) for _p, _v, rows in rvd.load(db, "unit_allowances_tables")
           for r in rows if r["faction_set"] == "chaos_dwarfs"}
    in_list = {}
    for _p, _v, rows in rvd.load(db, "unit_to_unit_list_junctions_tables"):
        for r in rows:
            if r["unit_list"] in cap:
                in_list[r["unit"]] = r["unit_list"]
    for e, _sc, v in TRAIT_BUNDLE[sub]:
        if e.startswith("wh3_dlc23_chd_ritual_unit_cap_"):
            cap["wh3_dlc23_chd_" + e[len("wh3_dlc23_chd_ritual_unit_cap_"):]] += int(v)
    bad = ["%s: no such unit %s" % (sub, u) for u in units if u not in known]
    bad += ["%s: kept the old leader's unit %s" % (sub, u) for u in units if u in ("u_a", "u_b", "u_c")]
    for lst, n in collections.Counter(in_list[u] for u in units if u in in_list).items():
        if n > cap[lst]:
            bad.append("%s: %d units of %s, the starting limit is %d" % (sub, n, lst, cap[lst]))
    if sub == "derpy_kharkadon":
        bad += ["%s: %s in the all-elite army" % (sub, u) for u in units if "labourers" in u or "hobgoblin" in u]
    return bad


def check_annex_lua(texts=None):
    """Every zz_derpy_toz_annex.lua copy lists the districts and seats toz_districts.py does, in
    its order. The DB side follows DISTRICTS through resort_seats(); the Lua is hand-edited, and a
    seat in one district in the DB and another in ANNEX_DISTRICTS counts towards the wrong
    district's completion with nothing to say so."""
    want = districts()
    if texts is None:
        texts = {s: open(os.path.join(ROOT, "Modding Files", "pack", *s.split("/")), encoding="utf-8").read()
                 for s in SCRIPTS if s.endswith("zz_derpy_toz_annex.lua")}
    bad = []
    for name, text in texts.items():
        body = text[text.index("local ANNEX_DISTRICTS"):]
        body = body[:body.index("\n}")]
        got = [(m.group(1), re.findall(r'suffix = "(\w+)"', m.group(2)))
               for m in re.finditer(r'key = "(DISTRICTS_ANNEX_T5_\w)", seats = \{(.*?)\}\},', body, re.S)]
        if got != want:
            bad.append("%s: ANNEX_DISTRICTS %s, toz_districts.py %s" % (name, got, want))
    return bad


def check_frontend_army(front=None):
    """The lord-select screen's Starting army (Mixer's list in mixerstuffies.lua) is the army the start
    script spawns. Without a list Mixer draws the startpos army, which the script kills on turn one.
    Every house: the two new lords from START, the rest from their Old World start script (Old World
    places all of them; IEE's Black Dwarf spawns a different army and one list cannot show both)."""
    src = open(START, encoding="utf-8").read()
    if front is None:
        front = open(os.path.join(ROOT, "Modding Files", "pack", "script", "frontend", "mod", "mixerstuffies.lua"),
                     encoding="utf-8").read()
    armies = [(fac, "".join(re.findall(r'"([^"]*)"', army)))
              for fac, army in re.findall(r'faction = "(\w+)".*?army = (.*?) \}', src, re.S)]
    for f in sorted(glob.glob(os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "cr_oldworld", "mod",
                                           "derpy_start_*.lua"))):
        armies += re.findall(r'create_force_with_general\(\s*(?:--[^\n]*\s*)?"(\w+)",\s*"([^"]*)"',
                             open(f, encoding="utf-8").read())
    assert len(armies) >= 13, armies
    bad = []
    for fac, army in armies:
        want = army.split(",")
        m = re.search(r'mixer_add_starting_unit_list_for_faction\("%s", \{(.*?)\}\)' % fac, front)
        got = re.findall(r'"(\w+)"', m.group(1)) if m else None
        if got != want:
            bad.append("frontend: %s starting army %s, start script spawns %s" % (fac, got, want))
    return bad


def check_start_script():
    """Run the shipped start script under Lua 5.1.5 against a stubbed campaign. Five cases."""
    import subprocess
    h = os.path.join(tempfile.gettempdir(), "derpy_new_lords_harness.lua")
    open(h, "w", encoding="utf-8").write(START_HARNESS)

    def run(case):
        r = subprocess.run([LUA, h, START, case, READER], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        return r.stdout.splitlines()
    bad = []
    out = run("inherit")
    sp = [l for l in out if l.startswith("SPAWN")]
    if not (len(sp) == 1 and sp[0].startswith("SPAWN\twh3_dlc23_chd_minor_faction\tderpy_kharkadon\tnames_name_212779775"
                                              "\tnames_name_318034614\t")
            and sp[0].endswith("\twh3_dlc23_chd_minor_faction_home\t101\ttrue")):
        bad.append("inherit: expected Kharkadon the Vicious next to the old leader, got %r" % sp)
    for l in sp:
        bad += check_army(l.split("\t")[2], l.split("\t")[5].split(","))
    # beside the lord like every other house's hero: one tile over, and NOT in his force
    if [l for l in out if l.startswith("HERO")] != [
            "HERO\twh3_dlc23_chd_minor_faction\tchampion\twh3_dlc23_chd_bull_centaur_taurruk\t101\tnil"]:
        bad.append("inherit: no Bull Centaur hero beside the new lord: %r" % out)
    out_u = run("uzkul")
    if [l for l in out_u if l.startswith("HERO")] != [
            "HERO\tcr_chd_skullstack\twizard\twh3_dlc23_chd_daemonsmith_sorcerer_metal\t101\tnil"]:
        bad.append("uzkul: no Daemonsmith hero beside the new lord: %r" % out_u)
    sp_u = [l for l in out_u if l.startswith("SPAWN\tcr_chd_skullstack\tderpy_uzkul\tnames_name_12412536\t\t")]
    if len(sp_u) != 1:
        bad.append("uzkul: the Captain was not spawned: %r" % out_u)
    for l in sp_u:
        bad += check_army(l.split("\t")[2], l.split("\t")[5].split(","))
    if "KILL\t7\ttrue" not in out:
        bad.append("inherit: the old leader and his force were not killed: %r" % out)
    if "BUNDLE\tderpy_kharkadon_lord_trait@wh3_dlc23_chd_minor_faction/0" not in out:
        bad.append("inherit: the lord trait bundle was not applied: %r" % out)
    if any("skullstack" in l for l in sp):
        bad.append("inherit: spawned for a faction the campaign does not place")
    if "FIND\t100\t200\t2" not in out:
        bad.append("inherit: off the Old World map the spawn was not searched from the old leader: %r" % out)
    # the Old World map: Kharkadon's fixed tile, searched with no offset so a valid tile is kept
    out = run("oldworld")
    if "FIND\t1792\t1117\t0" not in out or not any(
            l.startswith("SPAWN\twh3_dlc23_chd_minor_faction\tderpy_kharkadon")
            and l.endswith("\tcr_oldworld_region_zharr_naggrund\t1793\ttrue") for l in out):
        bad.append("oldworld: Kharkadon did not spawn at 1792,1117: %r" % out)
    out = run("fallback")
    if not any(l.startswith("SPAWN\twh3_dlc23_chd_minor_faction\tderpy_kharkadon") for l in out):
        bad.append("fallback: a leader with no army of his own stopped the new lord spawning: %r" % out)
    out = run("switch")
    if any(l.startswith(("SPAWN", "KILL", "HERO")) for l in out):
        bad.append("switch: an MCT-disabled lord still replaced the leader: %r" % out)
    if any(l.startswith("LOGERR") for case in ("inherit", "oldworld", "fallback", "uzkul") for l in run(case)):
        bad.append("the script raised inside its pcall")
    return bad


def selftest():
    files = build()
    faction_effects = {(get_col(r, h, "effect_key"), get_col(r, h, "effect_scope"),
                        float(get_col(r, h, "value")))
                       for h, _m, rs, t in files.values() if t == "effect_bundles_to_effects_junctions_tables"
                       for r in rs if get_col(r, h, "effect_bundle_key") == "derpy_kharkadon_lord_trait"}
    assert faction_effects == {
        ("wh3_dlc23_chd_ritual_unit_cap_infernal_ironsworn", "faction_to_faction_own_unseen", 3.0),
        (KP + "upkeep", "faction_to_force_own_unseen", -25.0),
        ("wh2_main_effect_agent_recruitment_xp_all_agents_and_lords", "faction_to_province_own_factionwide", 4.0),
        (KP + "xp", "faction_to_force_own_unseen", 30.0),
        ("wh3_dlc23_pooled_resource_chd_armaments_modifier", "faction_to_faction_own_unseen", 15.0),
        ("wh3_dlc23_effect_force_stat_leadership_chd_labourers", "faction_to_force_own", -10.0),
        ("wh3_dlc23_effect_force_stat_leadership_chd_hobgoblins", "faction_to_force_own", -10.0),
        ("wh3_dlc23_effect_upkeep_chd_hobgoblin", "faction_to_force_own_unseen", 25.0),
        ("wh3_dlc23_effect_force_recruit_cost_chd_hobgoblins", "faction_to_force_own_unseen", 25.0),
    }, "faction effects do not match the approved veteran Overlord package"
    self_trait = {(get_col(r, h, "effect_key"), get_col(r, h, "effect_scope"), float(get_col(r, h, "value")))
                  for h, _m, rs, t in files.values() if t == "character_skill_level_to_effects_junctions_tables"
                  for r in rs if get_col(r, h, "character_skill_key") == "derpy_kharkadon_lord_trait"}
    assert {(KS + "upkeep", C, -25.0), (KS + "xp", C, 30.0)} <= self_trait
    # Every self line names him; none falls back to the nameless native effect.
    natives = {donor for donor, _t in SELF_EFFECTS.values()}
    assert not natives & {e for e, _s, _v in self_trait}, "lord trait still grants a nameless native effect"
    portrait = "ui/portraits/portholes/no_culture/derpy_kharkadon.png"
    assert any(t == "units_custom_battle_permissions_tables" and
               any(get_col(r, h, "unit") == "derpy_kharkadon" and get_col(r, h, "general_portrait") == portrait
                   for r in rs) for h, _m, rs, t in files.values()), "custom battles still use the Overseer portrait"
    assert not check_kharkadon_items(files), check_kharkadon_items(files)
    assert not check_kharkadon_personal(files), check_kharkadon_personal(files)
    for h, _m, rows, table in files.values():
        if table == "unit_set_to_unit_junctions_tables":
            assert not any(get_col(r, h, "unit_set").startswith(KP) and
                           get_col(r, h, "unit_record").startswith("derpy_kharkadon_bg_") for r in rows), \
                "self buffs must not enumerate bodyguard ancillaries"
    import copy
    for table, selector, key, field, value in [
        ("ancillaries", "key", "derpy_kharkadon_talisman", "type", "wh_main_anc_talisman"),
        ("ancillary_to_effects", "effect", "wh2_main_effect_character_stat_enable_flaming_attacks", "value", "0"),
        ("ancillary_set_effect_junctions", "set_key", "derpy_kharkadon_set", "effect_scope", C),
        ("unit_special_abilities", "key", "derpy_kharkadon_hashuts_blood", "active_time", "25"),
        ("unit_special_abilities", "key", "derpy_kharkadon_bloodsworn_bulwark", "effect_range", "0"),
        ("special_ability_phase_stat_effects", "phase", "derpy_kharkadon_hashuts_blood", "how", "add"),
        ("special_ability_phase_stat_effects", "phase", "derpy_kharkadon_bloodsworn_bulwark", "value", "10"),
        ("effect_bonus_value_unit_ability_junctions", "effect", "derpy_kharkadon_enable_hashuts_blood", "bonus_value_id", "disable"),
        ("special_ability_to_special_ability_phase_junctions", "special_ability", "derpy_kharkadon_bloodsworn_bulwark", "target_friends", "false"),
        ("special_ability_phases", "id", "derpy_kharkadon_hashuts_blood", "imbue_contact", "wh2_dlc12_unit_contact_flammable"),
    ]:
        mutated = copy.deepcopy(files)
        for rel, (h, m, rs, t) in mutated.items():
            if t == table + "_tables":
                mutated[rel] = (h, m, [set_col(r, h, **{field: value}) if get_col(r, h, selector) == key else r
                                       for r in rs], t)
        assert check_kharkadon_items(mutated), "item mutant passed: " + field
    print("items: 10 mutants caught")
    mutants = [
        ("effects", "effect", KP + "charge", "effect", KP + "missing"),
        ("unit_abilities", "key", AURA, "source_type", "passive"),
        ("unit_special_abilities", "key", AURA, "active_time", "26"),
        ("unit_special_abilities", "key", AURA, "recharge_time", "60"),
        ("unit_special_abilities", "key", AURA, "effect_range", "50"),
        ("special_ability_to_special_ability_phase_junctions", "special_ability", AURA, "target_self", "false"),
        ("special_ability_to_special_ability_phase_junctions", "special_ability", AURA, "target_enemies", "true"),
        ("special_ability_phase_attribute_effects", "phase", AURA, "attribute", "fatigue_immune"),
        ("special_ability_phase_stat_effects", "phase", AURA, "value", "12"),
        ("effect_bonus_value_unit_attribute_junctions", "effect", KS + "vigour", "unit_attribute", "fatigue_immune"),
        ("unit_set_unit_attribute_junctions", "key", KP + "vigour_attribute", "unit_attribute", "fatigue_immune"),
        ("special_ability_to_invalid_usage_flags", "special_ability", AURA, "invalid_usage_flag", "moving"),
        ("effect_bonus_value_unit_ability_junctions", "effect", AURA_EFFECT, "bonus_value_id", "disable"),
        ("effect_bonus_value_ids_unit_sets", "effect", KP + "armour", "unit_set", "all_units"),
        ("character_skill_level_to_effects_junctions", "effect_key", AURA_EFFECT, "character_skill_key", "derpy_kharkadon_1"),
        ("character_skill_level_to_effects_junctions", "effect_key", "wh_main_effect_character_stat_weapon_strength_ap_damage_mult",
         "effect_scope", F),
        ("character_skill_level_to_effects_junctions", "effect_key", KP + "xp", "value", "40"),
    ]
    for table, selector, key, field, value in mutants:
        mutated = copy.deepcopy(files)
        for rel, (h, m, rs, t) in mutated.items():
            if t == table + "_tables":
                mutated[rel] = (h, m, [set_col(r, h, **{field: value}) if get_col(r, h, selector) == key else r
                                       for r in rs], t)
        assert check_kharkadon_personal(mutated), "personal mutant passed: " + field
    for missing in ("wh3_dlc23_chd_inf_infernal_ironsworn_ror", "wh3_dlc23_chd_inf_infernal_guard"):
        mutated = copy.deepcopy(files)
        rel = os.path.join("db", "unit_set_to_unit_junctions_tables", "derpy_kharkadon_personal.tsv")
        h, m, rs, t = mutated[rel]
        mutated[rel] = (h, m, [r for r in rs if get_col(r, h, "unit_record") != missing], t)
        assert check_kharkadon_personal(mutated), "missing target passed: " + missing
    print("personal line: %d mutants caught" % len(mutants))
    vp, ve = vanilla_pairs()
    pp, pe = pack_pairs()
    pairs = (vp | pp, ve | pe)
    assert not check(files, pairs), check(files, pairs)
    # a scope the effect is never used with must be caught
    SKILLS["derpy_uzkul"]["1"][4].append(("wh3_dlc23_effect_force_recruit_cost_chd_hobgoblins",
                                          "character_to_character_own", [-5]))
    assert any("never used with scope" in b for b in check(files, pairs))
    SKILLS["derpy_uzkul"]["1"][4].pop()
    # a typo'd effect key must be caught
    SKILLS["derpy_uzkul"]["1"][4].append(("wh3_dlc23_effect_force_recruit_cost_chd_hobgoblinz", F, [-5]))
    assert any("no such effect" in b for b in check(files, pairs))
    SKILLS["derpy_uzkul"]["1"][4].pop()
    # a never-granted unit-set effect is admitted only with a scope its bonus-value siblings use
    SKILLS["derpy_kharkadon"]["1"][4].append(("wh3_dlc23_effect_force_stat_armour_chd_infernal_ironsworn",
                                             "character_to_province_own", [5]))
    assert any("never used with scope" in b for b in check(files, pairs)), "sibling rule admitted any scope"
    SKILLS["derpy_kharkadon"]["1"][4].pop()
    # a three-level skill whose effects disagree on level count
    SKILLS["derpy_uzkul"]["2_2"][4].append(("wh_main_effect_force_stat_armour", F, [5, 10]))
    assert any("level count" in b for b in check(files, pairs))
    SKILLS["derpy_uzkul"]["2_2"][4].pop()
    # a leftover of the donor in a cloned row
    k = next(rel for rel, v in files.items() if v[3] == "land_units_tables")
    h, m, rows, t = files[k]
    files[k] = (h, m, rows + [rows[-1].replace("derpy_uzkul_description", "derpy_uzkul_balur")], t)
    assert any("leftover" in b for b in check(files, pairs))
    # a faction reference nothing in CA or this pack defines
    files = build()
    assert not check_faction_refs(files), check_faction_refs(files)
    fh, fm, frows, ft = files[FACTIONS_REL]
    files[FACTIONS_REL] = (fh, fm, [r for r in frows if not r.startswith("cr_chd_skullstack\t")], ft)
    assert any("cr_chd_skullstack" in b for b in check_faction_refs(files)), "dangling faction ref passed"
    # a missing skill set item
    files = build()
    k = next(rel for rel, v in files.items() if v[3] == "character_skill_node_set_items_tables"
             and any(r.startswith("derpy_kharkadon_skills\t") for r in v[2]))
    h, m, rows, t = files[k]
    drop = next(r for r in rows if r.startswith("derpy_kharkadon_skills\t"))
    files[k] = (h, m, [r for r in rows if r != drop], t)
    assert any("skill set items" in b for b in check(files, pairs))
    # the start script check must fail on a script that ignores the MCT switch
    global START
    real = START
    src = open(real, encoding="utf-8").read()
    mutant = os.path.join(tempfile.gettempdir(), "derpy_start_mutant.lua")
    open(mutant, "w", encoding="utf-8").write(src.replace("if derpy_hll_lord_on(lord.subtype) then", "if true then"))
    START = mutant
    assert any(b.startswith("switch:") for b in check_start_script()), "mutant with no MCT gate passed"
    # ... and on a typo'd unit key, which would spawn nothing in game and say nothing
    open(mutant, "w", encoding="utf-8").write(src.replace("wh3_dlc23_chd_veh_deathshrieker_rocket_launcher",
                                                          "wh3_dlc23_chd_veh_deathshrieker_rocket_launcherz"))
    assert any("no such unit" in b for b in check_start_script()), "mutant with a typo'd unit passed"
    # ... and on five Ironsworn, past the four the Overlords can field
    open(mutant, "w", encoding="utf-8").write(src.replace('"wh3_dlc23_chd_inf_infernal_guard,',
                                                          '"' + 'wh3_dlc23_chd_inf_infernal_ironsworn,' * 3))
    assert any("starting limit" in b for b in check_start_script()), "mutant over the Hell-Forge limit passed"
    # ... and on the old army inherited after all
    open(mutant, "w", encoding="utf-8").write(src.replace("lord.faction, lord.army, region_key",
                                                          'lord.faction, lord.army..",u_a", region_key'))
    assert any("old leader's unit" in b for b in check_start_script()), "mutant inheriting the old army passed"
    # ... and on one that never places the hero
    open(mutant, "w", encoding="utf-8").write(src.replace("derpy_hll_start_hero(lord.faction", "-- (lord.faction"))
    assert any("hero beside" in b for b in check_start_script()), "mutant without the hero passed"
    # ... and on one that embeds him after all
    open(mutant, "w", encoding="utf-8").write(src.replace(
        "\t\t\tcm:set_character_unique(str, true)\n",
        "\t\t\tcm:set_character_unique(str, true)\n"
        "\t\t\tcm:embed_agent_in_force(cm:create_agent(lord.faction, lord.hero.type, lord.hero.subtype, 101, 200), "
        "cm:get_character_by_cqi(cqi):military_force())\n"))
    assert any("hero beside" in b for b in check_start_script()), "mutant embedding the hero passed"
    START = real
    assert not check_start_script(), check_start_script()
    assert not check_annex_lua(), check_annex_lua()
    one = next(sc for sc in SCRIPTS if sc.endswith("zz_derpy_toz_annex.lua"))
    text = open(os.path.join(ROOT, "Modding Files", "pack", *one.split("/")), encoding="utf-8").read()
    moved = text.replace('suffix = "baal"', 'suffix = "QQQ"').replace('suffix = "black_dwarf"', 'suffix = "baal"') \
                .replace('suffix = "QQQ"', 'suffix = "black_dwarf"')
    assert check_annex_lua({one: moved}), "a seat moved between districts in the Lua passed"
    assert not check_frontend_army(), check_frontend_army()
    front = open(os.path.join(ROOT, "Modding Files", "pack", *SCRIPTS[3].split("/")), encoding="utf-8").read()
    assert len(check_frontend_army(front.replace('("cr_chd_skullstack", {', '("cr_chd_skullstackz", {'))) == 1, \
        "a faction with no frontend army list passed"
    assert check_frontend_army(front.replace('"wh3_dlc23_chd_cav_bull_centaurs_axe"})', '})')), \
        "a frontend list missing a unit passed"
    models = frontend_model(LORDS[0])
    assert not check_frontend_models(models), check_frontend_models(models)
    tw = next(p for p in models if p.endswith("3d_model.twui.xml"))
    assert check_frontend_models({tw: models[tw].replace(".VariantMeshDefinition", "_99.VariantMeshDefinition")}), \
        "a lord-select mesh nobody ships passed"
    assert check_frontend_models({tw: models[tw].replace("hu3_axs_celebrate_01", "hu3_axs_celebrate_99")}), \
        "a lord-select anim CA does not ship passed"
    assert check_frontend_models({tw: models[tw].replace("</layout>", "")}), "a broken lord-select twui passed"
    assert not check_own_models(), check_own_models()
    assert check_own_models([dict(LORDS[0], mesh="derpy_kharkadon_99")]), "a mesh the assets pack lacks passed"
    assert check_own_models([dict(LORDS[0], anim="derpy_kharkadon_99")]), "an anim bin the assets pack lacks passed"
    print("selftest ok")


# ------------------------------------------------------------------------------------------ main
def check_kharkadon_items(files):
    def data(table):
        return [dict(zip(cols(h), r.split("\t"))) for h, _m, rs, t in files.values()
                if t == table + "_tables" for r in rs]
    bad = []
    names = {"weapon": "Axe of Hashut's Blood", "talisman": "Shield of the Bloodsworn"}
    expected = {
        "weapon": {("wh_main_effect_character_stat_weapon_strength", C, 35.0),
                   ("wh_main_effect_character_stat_melee_attack", C, 15.0),
                   ("wh_main_effect_character_stat_bonus_vs_infantry", C, 15.0),
                   ("wh2_main_effect_character_stat_enable_flaming_attacks", C, 1.0),
                   ("wh_main_effect_character_stat_enable_magic_attacks", C, 1.0),
                   ("derpy_kharkadon_enable_hashuts_blood", C, 1.0)},
        "talisman": {("wh_main_effect_character_stat_melee_defence", C, 20.0),
                     ("wh_main_effect_character_stat_ward_save", C, 15.0),
                     ("wh_main_effect_character_stat_fire_resistance", C, 40.0),
                     ("derpy_kharkadon_enable_bloodsworn_bulwark", C, 1.0)},
    }
    effects = data("ancillary_to_effects")
    for slot, want in expected.items():
        key = "derpy_kharkadon_" + slot
        actual = {(r["effect"], r["effect_scope"], float(r["value"])) for r in effects if r["ancillary"] == key}
        if actual != want:
            bad.append("item effects: " + slot)
        if LOC.get("ancillaries_onscreen_name_" + key) != names[slot]:
            bad.append("item name: " + slot)
    shield = next((r for r in data("ancillaries") if r["key"] == "derpy_kharkadon_talisman"), {})
    if shield.get("type") != "wh_main_anc_armour" or shield.get("category") != "armour":
        bad.append("shield must equip in the armour slot")
    skill = next((r for r in data("character_skills") if r["key"] == "derpy_kharkadon_talisman"), {})
    if skill.get("image_path") != "item_armour.png":
        bad.append("shield skill: armour icon")
    actual = {(r["effect_key"], r["effect_scope"], float(r["value"])) for r in data("ancillary_set_effect_junctions")
              if r["set_key"] == "derpy_kharkadon_set"}
    if actual != {(KP + "armour", F, 10.0), ("wh_main_effect_force_stat_leadership", F, 5.0),
                  (KS + "armour", C, 10.0)}:
        bad.append("Blood and Iron set effects")
    contract = {
        "hashuts_blood": (32, 0, 1863434659, {("stat_melee_damage_ap", 1.5, "mult"),
                            ("stat_melee_damage_base", 1.5, "mult"), ("stat_melee_attack", 20.0, "add")}),
        "bloodsworn_bulwark": (25, 35, 894899759, {("stat_resistance_all", 20.0, "add"),
                                               ("stat_melee_defence", 15.0, "add")}),
    }
    defined = {r["effect"] for r in data("effects")}
    abilities = {r["key"]: r for r in data("unit_abilities")}
    for suffix, (duration, radius, uid, stats) in contract.items():
        key, effect = "derpy_kharkadon_" + suffix, "derpy_kharkadon_enable_" + suffix
        ua = abilities.get(key, {})
        kind = "wh_type_area_of_augments" if radius else "wh_type_augment"
        if ua.get("source_type") != "active" or ua.get("type") != kind:
            bad.append("item ability type: " + suffix)
        us = next((r for r in data("unit_special_abilities") if r["key"] == key), {})
        for field, value in {"active_time": duration, "recharge_time": 120, "effect_range": radius,
                             "unique_id": uid, "num_uses": -1}.items():
            if float(us.get(field, 0)) != value:
                bad.append("item ability %s: %s" % (suffix, field))
        if us.get("affect_self") != "true" or us.get("passive") != "false" or (radius and
            (us.get("num_effected_friendly_units") != "-1" or us.get("num_effected_enemy_units") != "0")):
            bad.append("item ability receivers: " + suffix)
        phase = next((r for r in data("special_ability_phases") if r["id"] == key), {})
        if float(phase.get("duration", 0)) != duration or phase.get("effect_type") != "positive":
            bad.append("item phase duration: " + suffix)
        if phase.get("imbue_contact") != "":
            bad.append("item phase: unlisted contact effect " + suffix)
        actual_stats = {(r["stat"], float(r["value"]), r["how"]) for r in data("special_ability_phase_stat_effects")
                        if r["phase"] == key}
        if actual_stats != stats:
            bad.append("item ability stats: " + suffix)
        routes = [r for r in data("special_ability_to_special_ability_phase_junctions") if r["special_ability"] == key]
        if len(routes) != 1 or any(routes[0].get(k) != v for k, v in
            {"phase": key, "order": "1", "target_self": "true", "target_friends": "true" if radius else "false",
             "target_enemies": "false"}.items()):
            bad.append("item ability routing: " + suffix)
        binds = [r for r in data("effect_bonus_value_unit_ability_junctions") if r["effect"] == effect]
        if effect not in defined or len(binds) != 1 or binds[0]["unit_ability"] != key or binds[0]["bonus_value_id"] != "enable":
            bad.append("item ability enable binding: " + suffix)
        if sum(int(r["unique_id"]) == uid for r in data("unit_special_abilities")) != 1 or any(
            int(r["unique_id"]) == uid for r in native_rows("unit_special_abilities")):
            bad.append("item ability ID collision: " + suffix)
    return bad


def check_kharkadon_personal(files):
    """Check the built personal line's self effects and regular troop targets."""
    def data(table):
        return [dict(zip(cols(h), r.split("\t"))) for h, _m, rs, t in files.values()
                if t == table + "_tables" for r in rs]

    bad = []
    expected = {"1": "First into the Breach", "2_1": "Chosen of Zharrduk", "2_2": "Plate and Oath",
                "2_3": "The Vicious", "2_4": "A Court of Veterans", "4_1": "The Immortal Few",
                "4_2": "Rule by the Axe", "3": "Stand With Your Overlord"}
    skills = {r["key"]: r for r in data("character_skills")}
    for suffix, name in expected.items():
        if skills.get("derpy_kharkadon_" + suffix, {}).get("localised_name") != name:
            bad.append("personal skill name: " + suffix)
    ability = "derpy_kharkadon_stand_with_your_overlord"
    definitions = {r["effect"] for r in data("effects")}
    if not {KP + k for k in PERSONAL_EFFECTS} | {KP + "vigour", AURA_EFFECT} <= definitions:
        bad.append("personal effects: missing definition")
    abilities = [r for r in data("unit_abilities") if r["key"] == ability]
    if len(abilities) != 1 or abilities[0]["type"] != "wh_type_area_of_augments" or abilities[0]["source_type"] != "active":
        bad.append("personal aura: active area ability")
    us = next((r for r in data("unit_special_abilities") if r["key"] == ability), {})
    for key, value in {"active_time": 25, "recharge_time": 120, "effect_range": 35,
                       "num_uses": -1, "num_effected_friendly_units": -1}.items():
        if float(us.get(key, 0)) != value:
            bad.append("personal aura: " + key)
    attr = data("special_ability_phase_attribute_effects")
    if not any(r["phase"] == ability and r["attribute"] == "unbreakable" and
               r["attribute_type"] == "positive" for r in attr):
        bad.append("personal aura: Unbreakable missing")
    phases = [r for r in data("special_ability_phases") if r["id"] == ability]
    if len(phases) != 1 or float(phases[0]["duration"]) != 25:
        bad.append("personal aura: phase duration")
    routing = [r for r in data("special_ability_to_special_ability_phase_junctions") if r["special_ability"] == ability]
    if len(routing) != 1 or any(routing[0].get(k) != v for k, v in
        {"target_self": "true", "target_friends": "true", "target_enemies": "false", "phase": ability, "order": "1"}.items()):
        bad.append("personal aura: targeting")
    stats = {(r["stat"], float(r["value"]), r["how"]) for r in data("special_ability_phase_stat_effects")
             if r["phase"] == ability}
    if stats != {("stat_melee_attack", 8.0, "add"), ("stat_melee_defence", 8.0, "add")}:
        bad.append("personal aura: stats")
    for table, field in (("special_ability_to_invalid_usage_flags", "invalid_usage_flag"),
                         ("special_ability_to_auto_deactivate_flags", "deactivate_flag")):
        if [r[field] for r in data(table) if r["special_ability"] == ability] != ["out_of_melee"]:
            bad.append("personal aura: " + field)
    unlocks = [r for r in data("effect_bonus_value_unit_ability_junctions") if r["effect"] == AURA_EFFECT]
    if len(unlocks) != 1 or unlocks[0]["bonus_value_id"] != "enable" or unlocks[0]["unit_ability"] != ability:
        bad.append("personal aura: enable binding")
    for target, units in personal_targets().items():
        actual = [r for r in data("unit_set_to_unit_junctions") if r["unit_set"] == KP + target]
        if {r["unit_record"] for r in actual} != units or any(r["exclude"] != "false" for r in actual):
            bad.append("personal targets: " + target)
    for suffix, (donor, target, _text) in PERSONAL_EFFECTS.items():
        native = next(r for r in native_rows("effect_bonus_value_ids_unit_sets") if r["effect"] == donor)
        binds = [r for r in data("effect_bonus_value_ids_unit_sets") if r["effect"] == KP + suffix]
        if len(binds) != 1 or binds[0]["unit_set"] != KP + target or binds[0]["bonus_value_id"] != native["bonus_value_id"]:
            bad.append("personal binding: " + suffix)
    loc = {r.split("\t")[0]: r.split("\t")[1] for _h, _m, rs, t in files.values() if t is None for r in rs}
    for suffix, (donor, text) in SELF_EFFECTS.items():
        key = KS + suffix
        if key not in definitions:
            bad.append("self effect: missing definition " + suffix)
        for table in SELF_BINDINGS:
            want = sorted(tuple(sorted(dict(r, effect=key, **self_binding(table, suffix)).items())) for r in native_rows(table) if r["effect"] == donor)
            got = sorted(tuple(sorted(r.items())) for r in data(table) if r["effect"] == key)
            if got != want:
                bad.append("self effect binding: %s in %s" % (suffix, table))
        if loc.get("effects_description_" + key) != text or "(Kharkadon)" not in text:
            bad.append("self effect text: " + suffix)
    attrs = [r for r in data("unit_set_unit_attribute_junctions") if r["key"] == KP + "vigour_attribute"]
    if len(attrs) != 1 or attrs[0]["unit_set"] != KP + "elite" or attrs[0]["unit_attribute"] != "fatigue_res":
        bad.append("personal binding: permanent Strong Vigour")
    attribute_binds = [r for r in data("effect_bonus_value_unit_set_unit_attribute_junctions") if r["effect"] == KP + "vigour"]
    if len(attribute_binds) != 1 or attribute_binds[0]["unit_set_attribute"] != KP + "vigour_attribute" or attribute_binds[0]["bonus_value_id"] != "enable":
        bad.append("personal binding: Strong Vigour enable")
    expected_fx = {
        "1": [("wh_main_effect_character_stat_melee_attack", C, [8]), (KP + "charge", F, [10]),
              (KS + "charge", C, [10])],
        "2_1": [(KP + "xp", F, [10, 20, 30]), (KP + "upkeep", F, [-5, -10, -15]),
                (KS + "xp", C, [10, 20, 30]),
                (KS + "upkeep", C, [-5, -10, -15])],
        "2_2": [(KP + "defence", F, [3, 6, 9]), (KP + "armour", F, [5, 10, 15]),
                (KS + "defence", C, [3, 6, 9]),
                (KS + "armour", C, [5, 10, 15])],
        "2_3": [("wh_main_effect_character_stat_weapon_strength_ap_damage_mult", C, [5, 10, 15]),
                ("wh_main_effect_character_stat_bonus_vs_infantry", C, [3, 6, 9])],
        "2_4": [("wh_main_effect_agent_recruitment_xp_all_agents", "character_to_province_own", [1, 2, 3]),
                ("wh_main_effect_force_stat_leadership", F, [2, 4, 6])],
        "4_1": [(KP + "vigour", F, [1]), (KP + "resistance", F, [10]), (KP + "upkeep", F, [15]),
                (KS + "vigour", C, [1]),
                (KS + "resistance", C, [10]),
                (KS + "upkeep", C, [15])],
        "4_2": [("wh_main_effect_attribute_enable_causes_terror", C, [1]),
                ("wh_main_effect_character_stat_weapon_strength", C, [20]),
                ("wh3_dlc23_effect_force_stat_leadership_chd_hobgoblins", F, [-8]),
                ("wh3_dlc23_effect_force_stat_leadership_chd_labourers", F, [-8])],
        "3": [(AURA_EFFECT, C, [1])],
    }
    fx = data("character_skill_level_to_effects_junctions")
    for suffix, effects in expected_fx.items():
        want = {(e, sc, level, float(value)) for e, sc, values in effects for level, value in enumerate(values, 1)}
        actual = {(r["effect_key"], r["effect_scope"], int(r["level"]), float(r["value"])) for r in fx
                  if r["character_skill_key"] == "derpy_kharkadon_" + suffix}
        if actual != want:
            bad.append("personal skill effects: " + suffix)
    ids = [int(r["unique_id"]) for r in data("unit_special_abilities")]
    if ids.count(1047410657) != 1 or any(int(r["unique_id"]) == 1047410657 for r in native_rows("unit_special_abilities")):
        bad.append("personal aura: unique ID collision")
    for table, rs in (("land_units", data("land_units")), ("melee_weapons", data("melee_weapons"))):
        for row in rs:
            if row.get("key") not in ("derpy_kharkadon", "derpy_uzkul"):
                continue
            preserved = {"land_units": ("armour", "melee_attack", "melee_defence", "shield"),
                         "melee_weapons": ("damage", "ap_damage", "is_magical", "splash_attack_target_size",
                                           "splash_attack_max_attacks", "splash_attack_power_multiplier")}[table]
            for rel, t in fragments():
                if t != table + "_tables":
                    continue
                h, _m, old = read_tsv(os.path.join(EX, rel))
                baseline = next((dict(zip(cols(h), r.split("\t"))) for r in old
                                 if get_col(r, h, "key") == row["key"]), None)
                if baseline and any(row[k] != baseline[k] for k in preserved):
                    bad.append("personal line: baseline stat changed " + row["key"])
    for h, m, rs, t in files.values():
        if t is not None:
            key = keyfn(t, m, h)
            if len({key(r) for r in rs}) != len(rs):
                bad.append("personal line: duplicate key " + t)
    return bad


def write_all(files):
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    plan = []
    for rel, (hdr, meta, rows, table) in sorted(files.items()):
        path = write_tsv(rel, hdr, meta, rows)
        inpack = rel.replace(os.sep, "/")[:-len(".tsv")]
        if table:
            ver = int(meta.split(";")[1])
            frag = inpack.rsplit("/", 1)[1]
            plan.append((inpack, {"DB": [frag, table, ver]}, os.path.basename(path), os.path.dirname(path), len(rows)))
        else:
            plan.append((inpack, {"Loc": inpack.rsplit("/", 1)[1][:-4]}, os.path.basename(path),
                         os.path.dirname(path), len(rows)))
    blob, _e = portrait_bin()
    loose = []
    for p in PORTRAIT_PATHS:
        dest = os.path.join(OUT, "pack", *p.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(blob)
        loose.append((dest, p))
    for p in SCRIPTS:
        loose.append((os.path.join(ROOT, "Modding Files", "pack", *p.split("/")), p))
    # Tower seat art, drawn from the house's own flag by tools/make_toz_seat_banner.py
    import make_toz_seat_banner as tsb
    for key in tsb.HOUSES:
        for n in tsb.names(key):
            src = os.path.join(tsb.OUT, n)
            assert os.path.exists(src), "run tools/make_toz_seat_banner.py first: " + src
            loose.append((src, tsb.TOZ + n))
    icons = [L["sub"] + "_passive" for L in LORDS if L["sub"] not in PASSIVE_ICON]
    icons += ["derpy_kharkadon_" + suffix for suffix in ITEM_ABILITIES]
    for icon in icons:
        p = "ui/battle ui/ability_icons/%s.png" % icon
        src = os.path.join(ROOT, "Modding Files", "pack", *p.split("/"))
        assert os.path.exists(src), "ability icon missing, it would draw a white square: " + src
        loose.append((src, p))
    for L in LORDS:
        p = "ui/portraits/faction_leaders/%s.png" % L["sub"]
        dest = os.path.join(OUT, "pack", *p.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(leader_png(L))
        loose.append((dest, p))
        for kind, pat in (PORTRAIT_FILES.items() if "portraits" in L else ()):
            p = pat % L["sub"]
            dest = os.path.join(OUT, "pack", *p.split("/"))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, "wb").write(own_portrait(L, kind))
            loose.append((dest, p))
        for p, text in frontend_model(L).items():
            dest = os.path.join(OUT, "pack", *p.split("/"))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, "w", encoding="utf-8", newline="").write(text)
            loose.append((dest, p))
    return plan, loose


def do_import(plan, loose):
    from import_house_ancillaries import call, check_keys
    call("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False})
    check_keys([e[:4] for e in plan])
    try:
        call("close_pack", {"pack_key": PACK})
    except Exception:
        pass
    call("open_packfiles", {"paths": [PACK]})
    from read_pack_index import paths
    existing = set(paths(PACK))
    for path, spec, fn, d, n in plan:
        if path not in existing:
            call("new_packed_file", {"pack_key": PACK, "path": path, "new_file": json.dumps(spec)})
        call("import_tsv", {"pack_key": PACK, "table_path": path, "tsv_path": os.path.join(d, fn)})
    for src, dest in loose:
        call("add_packed_files", {"pack_key": PACK, "source_paths": [src],
                                  "destination_paths": json.dumps([{"File": dest}])})
    call("save_packfile", {"pack_key": PACK})
    call("close_pack", {"pack_key": PACK})
    print("saved")
    # Verify the SAVED file, re-opened fresh.
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
        ok = g == w
        bad += not ok
        if not ok:
            print("DIFF   %s  pack %d rows, built %d" % (path, len(g), len(w)))
    shutil.rmtree(dest, ignore_errors=True)
    from read_pack_index import entries
    _f, es = entries(PACK)
    names = {str(e[0] if isinstance(e, tuple) else e).lower() for e in es}
    for _src, p in loose:
        if p.lower() not in names:
            print("MISSING  " + p)
            bad += 1
    print("%d fragments verified, %d loose files, %d bad" % (len(plan), len(loose), bad))
    return bad


def main():
    if "--selftest" in sys.argv:
        selftest()
        return
    files = build()
    bad = check(files) + check_ids_unique() + check_faction_refs(files) + check_start_script() + check_annex_lua() + \
        check_frontend_army() + check_frontend_models() + check_own_models()
    for b in bad:
        print("FAIL  " + b)
    if bad:
        raise SystemExit("%d finding(s) - nothing written" % len(bad))
    plan, loose = write_all(files)
    for path, spec, fn, d, n in plan:
        print("  %5d  %s" % (n, path))
    for _s, p in loose:
        print("  file   %s" % p)
    if "--import" in sys.argv:
        sys.exit(1 if do_import(plan, loose) else 0)


if __name__ == "__main__":
    main()
