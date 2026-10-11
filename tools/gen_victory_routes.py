"""Build the Chaos Dwarf victory routes - three alternative victory paths per house.

WHAT THIS REPLACES
------------------
`derpy_chd_victory_objectives.lua` (four copies) registered each house in CA's
`victory_objectives_<campaign>.factions` table so the subculture long victory came back.
That was a repair, not content: every house's `objectives` list was empty, so all eleven
played CA's generic "paint the map" short victory.

This builds the VCO route instead, measured out of `victory_conditions_overhaul.pack`
(Workshop 3140200173) on 2026-09-07. See docs/VICTORY_CONDITIONS.md section 12.

  1. mint a `victory_types` row per route            -> the node in the victory tree
  2. write the objectives as a MISSION STRING        -> the old missions.txt block syntax
  3. issue it with cm:trigger_custom_mission_from_string(faction, string)
  4. wrap CA's initialise_victory_missions and return early for our factions

TWO DELIBERATE DEVIATIONS FROM VCO, AND ONE REVERSED
----------------------------------------------------
* **One Lua file, not 107.** VCO requires `script/<mod>/<campaign>/<faction>/missions`,
  keyed on `cm:get_campaign_name()`. That call returns whatever the campaign's own start
  script passed to `set_campaign_name` (lib_campaign_manager.lua:714) - measured
  `cr_oldworld` in a live Old World campaign, while VCO's folder for Immortal Empires is
  `main_warhammer`, a script root. It is not derivable, and seven installed mods redeclare
  the `cr_oldworld` row in `campaigns_tables`. With eleven factions the whole dimension is
  not worth the risk: the routes are one table in one file under `script/campaign/mod/`,
  which loads in every campaign.
* **Three mission slot keys, not one.** VCO gives all three of a faction's routes
  `key vco_route_victory`. A mission manager is keyed `(faction_name, mission_key)` -
  lib_campaign_mission_manager.lua:96 - so three live missions on one key is at best
  unverified. Three distinct rows cost two DB rows and remove the question.
* **SCRIPTED flavour objectives: copied since 2026-10-11 (phase 2).** VCO opens each route
  with a `SCRIPTED` objective carrying `override_text` and `script_key vco_dummy`, and one
  `FactionTurnStart` listener (`vco-listeners.lua:48`) completes them every turn. This file
  now does the same: every route opens with its paragraph (`LORE`) and every ritual objective
  has an explainer above it (`EXPLAIN`), all on `script_key derpy_route_lore`, and section 9
  of the shipped Lua completes them. The trade stands as it was written here before: every
  route now depends on that listener running, which is why the selftest replays it and
  carries a mutant for each of its guards. Two differences from VCO: the call only happens
  once the saved value `derpy_route_lore_v1` says this game's routes carry lines, so saves
  from before the change never see it; and there is no `<dummy>` marker and no UI listener,
  so the paragraph draws as a plain objective line.

WHY NO PROVINCE OR REGION OBJECTIVES - AND THE ONE EXCEPTION
-----------------------------------------------------------
Region and province keys carry the campaign's own prefix (`wh3_main_combi_region_*` vs
`cr_oldworld_region_*`), and one mission string cannot hold both. CA's victory objectives
lean on `CONTROL_N_PROVINCES_INCLUDING` heavily; we cannot, because one file serves four
maps. The palette below is the map-agnostic subset.

The exception is a **map-gated route**: a route may carry a second objective list used only
where a named region exists. Both lists are emitted, and the shipped Lua picks at issue time
with `cm:region_by_key(key)` - one script, four campaigns, and a null interface names the map
([[wh3-region-by-key-is-a-map-probe]]). The base list stays map-agnostic, so the route is
alive on every map either way. `check()` refuses a region key outside VERIFIED_REGIONS and
refuses any map-bound type in a base list. Immortal Empires Expanded keeps the vanilla
`wh3_main_combi_region_*` namespace - its own `campaign_map_regions` fragment maps those keys
onto `cr_combi_expanded_map_1` - so one key covers IE and IEE together.

    py tools/gen_victory_routes.py --check      # validate, write nothing
    py tools/gen_victory_routes.py              # write TSVs + the Lua
    py tools/gen_victory_routes.py --selftest
    py tools/gen_victory_routes.py --review     # write the text review file, nothing else

Exit 1 on findings. Nothing here needs RPFM.
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Modding Files", "source", "victory_routes")
LUA_OUT = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "mod",
                       "zzz_derpy_chd_victory_routes.lua")
LUA = r"C:\Program Files (x86)\Lua\5.1\lua.exe"
LUAC = r"C:\Program Files (x86)\Lua\5.1\luac.exe"

# Files the routes and quests replace, four copies each. check() fails while any still ships:
# the first puts entries back in CA's table for factions we now disable, the second hands
# Warrhak and Gordak out on turn one instead of through their quests.
DEAD_SCRIPTS = ["derpy_chd_victory_objectives.lua", "temp_spawn_pool_chd_oldworld.lua"]
DEAD_CAMPAIGNS = ["cr_oldworld", "cr_combi_expanded", "wh3_main_combi", "cr_darklands"]

# ---------------------------------------------------------------------------
# Vocabulary. Everything below is measured, not assumed.
# ---------------------------------------------------------------------------

# Objective types CA itself uses inside a victory objective, counted across all 5,472 lines
# of script/campaign/main_warhammer/victory_objectives.lua. A type outside this set may be a
# perfectly good mission type and still not be attested in a VICTORY mission, which is the
# only context that matters here.
CA_VICTORY_TYPES = {
    "DESTROY_FACTION", "SCRIPTED", "CONTROL_N_PROVINCES_INCLUDING",
    "CONTROL_N_REGIONS_FROM", "OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS",
    "HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE", "FIGHT_SET_PIECE_BATTLE",
    "OWN_N_REGIONS_INCLUDING", "CONSTRUCT_N_BUILDINGS_FROM", "PERFORM_RITUAL",
    "CONSTRUCT_N_OF_A_BUILDING", "COMPLETE_N_MISSIONS_OF_CATEGORY",
    "RAZE_OR_OWN_SETTLEMENTS", "OWN_N_UNITS", "CONSTRUCT_N_BUILDINGS_INCLUDING",
    "ALL_PLAYERS_RAZE_SACK_OR_OWN_X_SETTLEMENTS", "ACHIEVE_CHARACTER_RANK",
}

# Types CA does not use in a victory objective but Victory Conditions Overhaul does, counted
# the same way over all 107 of its `script/vco-*/*/*/missions.lua` files (Workshop
# 3140200173, read 2026-09-08). VCO is a shipped, widely installed mod whose whole content is
# victory missions issued by exactly the call this file uses, so a type it leans on is
# attested in this context in the only way that matters. Counts are its uses:
#
#   CONSTRUCT_BUILDING_IN_PROVINCES 131   MOVE_TO_REGION 57   HAVE_CHARACTER_WOUNDED 37
#   DEFEAT_N_ARMIES_OF_FACTION 26   CONTROL_N_REGIONS_INCLUDING 20
#   CAPTURE_X_BATTLE_CAPTIVES 11   RECRUIT_UNIT 5   ASSASSINATE_X_CHARACTERS 3
#   MAINTAIN_N_ALLIANCES 3   MOVE_TO_PROVINCE 1   EARN_X_AMOUNT_FROM_RAIDING 1
VCO_VICTORY_TYPES = {
    "CONSTRUCT_BUILDING_IN_PROVINCES", "MOVE_TO_REGION", "HAVE_CHARACTER_WOUNDED",
    "DEFEAT_N_ARMIES_OF_FACTION", "CONTROL_N_REGIONS_INCLUDING",
    "CAPTURE_X_BATTLE_CAPTIVES", "RECRUIT_UNIT", "ASSASSINATE_X_CHARACTERS",
    "MAINTAIN_N_ALLIANCES", "MOVE_TO_PROVINCE", "EARN_X_AMOUNT_FROM_RAIDING",
}
ATTESTED_VICTORY_TYPES = CA_VICTORY_TYPES | VCO_VICTORY_TYPES

# Types whose ONLY attested use carries a count and nothing else, so they are safe in a file
# that serves four maps. Kept as a note rather than a rule - MAP_BOUND_TYPES below is the
# rule, and it is the one check() enforces.

# Types that carry a map-specific key, so they cannot appear in a file shared by four
# campaigns. Enforced by check().
MAP_BOUND_TYPES = {
    "CONTROL_N_PROVINCES_INCLUDING", "CONTROL_N_REGIONS_FROM",
    "OWN_N_REGIONS_INCLUDING", "RAZE_OR_OWN_SETTLEMENTS",
    # the VCO half: every one of these carries a `region` or `province` key in all of its
    # uses, so they are as map-bound as CA's four
    "CONSTRUCT_BUILDING_IN_PROVINCES", "MOVE_TO_REGION", "MOVE_TO_PROVINCE",
    "CONTROL_N_REGIONS_INCLUDING",
}

# Condition keywords CA uses, harvested the same way. `total2` and the valueless flags
# `include_generals` / `confederation_valid` are real - ACHIEVE_CHARACTER_RANK uses
# "total 1", "total2 25", "include_generals".
CA_CONDITIONS = {
    "province", "faction", "region", "total", "total2", "override_text", "script_key",
    "count", "building_level", "pooled_resource", "set_piece_battle", "event_category",
    "ritual_category", "subculture", "text_display", "start_pos_character", "ritual",
    "include_generals", "confederation_valid",
    # `vassalization_valid` counts a faction as destroyed once it is a vassal - CA uses it on
    # 5 DESTROY_FACTION objectives and VCO on 33. `count_completion` appears only alongside
    # SCRIPTED's progress counter (39 of CA's 88), which this file never emits.
    "vassalization_valid", "count_completion",
    "unit",
}
VALUELESS_CONDITIONS = {"include_generals", "confederation_valid", "vassalization_valid"}

# Conditions attested ONLY on the types listed. `override_text` is the one that matters:
# CA puts it on SCRIPTED and on the four region/province types and nowhere else, and VCO's
# 113 uses are all CONTROL_N_REGIONS_FROM. It is not attested on a counter objective, so
# retitling e.g. a pooled-resource objective is unproven and check() refuses it - which is
# why a route's written lines (LORE, EXPLAIN) are SCRIPTED objectives of their own, completed
# by section 9 of the shipped Lua, rather than retitled counters.
CONDITION_ONLY_ON = {
    "override_text": {
        "SCRIPTED", "CONTROL_N_PROVINCES_INCLUDING", "CONTROL_N_REGIONS_FROM",
        "CONTROL_N_REGIONS_INCLUDING", "OWN_N_REGIONS_INCLUDING",
        "CONSTRUCT_N_BUILDINGS_FROM",
    },
    "confederation_valid": {"DESTROY_FACTION"},
    "vassalization_valid": {"DESTROY_FACTION"},
    "include_generals": {"ACHIEVE_CHARACTER_RANK"},
    "pooled_resource": {"HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE"},
    "ritual_category": {"PERFORM_RITUAL"},
    "ritual": {"PERFORM_RITUAL"},
}

# Types that never appear without a `total` in either source: CA writes it on 4/4
# CONSTRUCT_N_OF_A_BUILDING and 1/1 CONSTRUCT_N_BUILDINGS_INCLUDING, VCO on 23/23 and 4/4.
# A count-N objective with no N shipped here for a while; check() now refuses it.
TYPES_NEEDING_TOTAL = {
    "CONSTRUCT_N_OF_A_BUILDING", "CONSTRUCT_N_BUILDINGS_INCLUDING",
    "CONSTRUCT_N_BUILDINGS_FROM", "OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS",
    "OWN_N_UNITS", "DEFEAT_N_ARMIES_OF_FACTION", "CAPTURE_X_BATTLE_CAPTIVES",
    "HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE", "PERFORM_RITUAL",
    # counted the same way over VCO 2026-09-09, each `total` and nothing else:
    # EARN_X_AMOUNT_FROM_RAIDING 1/1 (7500), ASSASSINATE_X_CHARACTERS 3/3,
    # MAINTAIN_N_ALLIANCES 3/3
    "EARN_X_AMOUNT_FROM_RAIDING", "ASSASSINATE_X_CHARACTERS", "MAINTAIN_N_ALLIANCES",
}

# Types that must carry a `faction` line, which the ROUTES tables never declare because
# mission_string() adds it: CA's own `victory_objectives.lua` special-cases exactly these in
# `add_objectives` and appends `"faction " .. faction_key`, commenting that "these objectives
# will fail if we don't add them here". Measured true 2026-09-09 - Ghorth's routes I, IV and V
# drew NO node in the victory panel while II and III drew, and a CONSTRUCT objective was the
# only thing the three dead ones had in common. VCO writes the line on 157/157 of its CONSTRUCT
# objectives and PoW's victory mod on 19/19; neither ever omits it.
TYPES_NEEDING_FACTION = {
    "CONSTRUCT_N_OF_A_BUILDING", "CONSTRUCT_N_BUILDINGS_INCLUDING",
    "CONSTRUCT_N_BUILDINGS_FROM", "CONSTRUCT_BUILDING_IN_PROVINCES",
}

# What a route pays. Not one flat purse for all 35: a route may pay raw materials only,
# armaments only, gold only, or a mix, and the amounts differ per purse. Gold is in the mix
# rather than the whole of it - a Chaos Dwarf faction runs on materials, armaments and Conclave
# influence, and the first draft paid 50,000 treasury and nothing else.
#
# `factor missions` is the attribution bucket, and it is CA own: `missions` exists as a factor on
# all four Chaos Dwarf pools and is **grant-capable** on each - min 0 / max 2147483647 on raw
# materials and influence, unbounded both ways on armaments, read out of
# `pooled_resource_factor_junctions`. That matters because most factors are bounded ONE way and
# an amount pushed the wrong way through one clamps to nothing in silence
# ([[wh3-pooled-resource-payload-factor-trap]]) - which is why this is not `wh3_dlc23_chd_mined`
# or `..._consumed`.
#
# `wh3_dlc23_chd_labour` is deliberately NOT paid: its `pooled_resources` scope is
# FACTION_PROVINCE, and a FACTION_PROVINCE pool answers with a null interface at both the
# faction and the province level ([[wh3-faction-province-pool-unreachable]]). Asking for it in an
# objective is fine - the engine reads that itself - but paying it is not.
#
# Amounts are read against the start this workspace sets Ghorth (10,000 gold, 2,500 raw
# materials, 1,000 armaments, 0 influence) and against what the routes themselves ask for (60 to
# 400 influence). A single-currency purse pays about double what a mixed one pays of the same
# resource, so a narrow reward is not a smaller one.
REWARD_FACTOR = "missions"

# `money` is not a pooled resource and takes no transaction block - it is the bare statement
# `money <n>;`, measured paid through this exact route on 2026-09-05 (treasury 14091 -> 16591 on
# `money 2500`, docs/MISSIONS.md section 12) and attested in `pow_victory_conditions` as a cost,
# `money -70000`. The sign is the obvious inverse and check() refuses a non-positive one.
MONEY = "money"

# Seven purses, spread over the 35 routes by house index as well as route index. Seven against
# eight trophies means the purse and the trophy do not travel together, and three consecutive
# route indices can never collide, so no house pays the same purse twice.
PURSES = (
    (("wh3_dlc23_chd_raw_materials", 8000),),
    (("wh3_dlc23_chd_armaments", 4000),),
    ((MONEY, 30000),),
    (("wh3_dlc23_chd_raw_materials", 4000), ("wh3_dlc23_chd_armaments", 1500)),
    (("wh3_dlc23_chd_armaments", 2000), ("wh3_dlc23_chd_conclave_influence", 400)),
    ((MONEY, 15000), ("wh3_dlc23_chd_raw_materials", 3000)),
    (("wh3_dlc23_chd_raw_materials", 6000), ("wh3_dlc23_chd_armaments", 2500),
     ("wh3_dlc23_chd_conclave_influence", 200)),
)


def route_rewards(faction, idx):
    """The purse for one route, as ((resource_or_MONEY, amount), ...)."""
    return PURSES[(HOUSES.index(faction) + idx) % len(PURSES)]

# The trophy pool: eight items this generator MINTS, shipped in the lords pack beside the script
# that pays them, so the reward still needs no other pack. Three filters, each learned the hard
# way:
#
#  1. NOT one of the lords pack own 37 per-lord items. Those are bound to the lord in
#     `ancillaries_required_skills` and are handed over as he LEVELS - measured in game
#     2026-09-09, the panel offered "Mace of Dominion" for a route Ghorth would be given it for
#     free. Rewarding a player with something already coming to them is not a reward.
#  2. NOT `randomly_dropped`, and NOT one of CA's eight Dwarf-god relics either: the Great Drill
#     chain (`derpy_chd_drill_chain.lua`) hands all eight to every house, so a relic trophy is
#     filter 1 again.
#  3. NOT locked to a character. The first pool was vanilla, and five of its eight carry a row in
#     `ancillaries_included_agent_subtypes`: the Obsidian Axe, Armour of Gazrakh and Chaos
#     Runeshield are Zhatan's, the Dagger of Malice and Banner of Slavery Gorduz Backstabber's.
#     No house lord could equip them. Reported by a player 2026-09-24. Every vanilla Chaos Dwarf
#     item worth the name is either locked, randomly dropped, a relic or a convoy reward, so
#     vanilla has no clean pool left and these are minted instead.
#
# So each row is: faction_set `all`, transferrable, no subtype or skill row, never dropped at
# random, never stolen or destroyed, unique band (200). Every effect is one vanilla already puts
# on an ancillary, and its scope is NOT chosen here - effect_rows() reads it out of
# anc_effect_scopes.SCOPE, because a hand-picked scope is silently wrong (21 were, 2026-08-25).
# Every ability effect binds through a plain `effect_bonus_value_unit_ability_junctions` row with
# no unit set, checked 2026-09-24, so none of them is secretly one race's. The icon is the slot's
# own generic type, which is what every vanilla weapon and armour row does.
#
# Ordered weapon / armour / talisman / enchanted twice: a house draws three or five CONSECUTIVE
# entries (route_reward_item), so its routes never pay two items for the same slot.
TROPHY_ITEMS = (
    ("derpy_trophy_conquerors_cleaver", "weapon", "The Conqueror's Cleaver",
     "Hashut's priests quench this blade in the blood of the first king a house throws down. "
     "It has never been blunted since, and whoever carries it is owed the next crown.",
     (("wh3_dlc20_effect_ability_enable_bound_flame_storm", 1),
      ("wh2_dlc10_effect_character_stat_enable_sundering_attacks", 1),
      ("wh_main_effect_character_stat_weapon_strength", 25),
      ("wh_main_effect_character_stat_ap_damage", 60))),
    ("derpy_trophy_hell_iron_warplate", "armour", "Hell-Iron Warplate",
     "Hammered on the anvils beneath the Ziggurat from iron that was still screaming. "
     "Wounds close under it as fast as the enemy can open them.",
     (("wh2_main_effect_ability_enable_regeneration", 1),
      ("wh_main_effect_character_stat_armour", 40),
      ("wh_main_effect_character_stat_ward_save", 15),
      ("wh_main_effect_character_stat_fire_resistance", 20))),
    ("derpy_trophy_heart_of_the_furnace", "talisman", "Heart of the Great Furnace",
     "A coal lifted from the great furnace of Zharr-Naggrund and never allowed to cool. "
     "Whoever wears it breathes the same fire.",
     (("wh3_main_effect_ability_enable_fire_breath", 1),
      ("wh_main_effect_character_stat_magic_resistance", 30),
      ("wh_main_effect_character_stat_physical_resistance", 15),
      ("wh_main_effect_force_stat_ward_save", 5))),
    ("derpy_trophy_chains_of_the_conquered", "enchanted_item", "Chains of the Conquered",
     "Every link was taken from a slave-gang of a fallen rival. Those who see them know "
     "exactly what they are looking at, and the plunder comes easier for it.",
     (("wh_main_effect_attribute_enable_causes_terror", 1),
      ("wh_main_effect_force_all_campaign_raid_income", 25),
      ("wh_main_effect_force_all_campaign_sacking_income", 25),
      ("wh_main_effect_public_order_characters", 5),
      ("wh_main_effect_force_stat_melee_attack", 6))),
    ("derpy_trophy_horn_blade_of_the_bull", "weapon", "Horn-Blade of the Bull",
     "Cut from the horn of a Lammasu that answered Hashut's call too slowly. "
     "It still burns, and it still charges.",
     (("wh_main_effect_ability_enable_deadly_onslaught", 1),
      ("wh3_dlc20_effect_enables_warpflame_attacks", 1),
      ("wh_main_effect_character_stat_enable_magic_attacks", 1),
      ("wh_main_effect_character_stat_melee_attack", 15),
      ("wh_main_effect_character_stat_charge_bonus_add", 25))),
    ("derpy_trophy_ash_veil_mantle", "armour", "The Ash-Veil Mantle",
     "Woven from the ash of a burned capital and still smouldering. Arrows and spells alike "
     "are lost in it, and an army led beneath it mends on the march.",
     (("wh3_main_effect_battle_barrier_health_add", 600),
      ("wh_main_effect_character_stat_missile_resistance", 25),
      ("wh_main_effect_character_stat_magic_resistance", 20),
      ("wh_main_effect_force_all_campaign_replenishment_rate", 10),
      ("wh_main_effect_force_army_campaign_enable_replenishment_in_foreign_territory", 1))),
    ("derpy_trophy_tyrants_seal", "talisman", "The Tyrant's Seal",
     "The seal of office of the last lord to hold the Tower of Zharr outright. "
     "Nobody who wore it has ever been seen to run.",
     (("wh_main_effect_attribute_enable_unbreakable", 1),
      ("wh_main_effect_character_stat_melee_defence", 15),
      ("wh_main_effect_force_stat_melee_defence", 6),
      ("wh_main_effect_force_stat_leadership", 8))),
    ("derpy_trophy_everburning_censer", "enchanted_item", "The Everburning Censer",
     "It is fed on the incense of Hashut's temples and it has not gone out in a thousand "
     "years. Soldiers who march behind its smoke learn their trade quickly.",
     (("wh_main_effect_ability_enable_bound_fireball", 1),
      ("wh_main_effect_force_stat_physical_resistance", 10),
      ("wh2_main_effect_force_army_campaign_experience_all", 20))),
)
TROPHIES = tuple(t[0] for t in TROPHY_ITEMS)
TROPHY_SLOT_TYPE = {"weapon": "wh_main_anc_weapon", "armour": "wh_main_anc_armour",
                    "talisman": "wh_main_anc_talisman",
                    "enchanted_item": "wh_main_anc_enchanted_item"}

# Everything `ancillaries_required_skills_tables/derpy_chd_ll_ancillary` binds to a skill, read
# out of the deployed pack 2026-09-09. A reward may never be one of these - see filter 1 above.
SKILL_GRANTED_ANCILLARIES = frozenset("""
derpy_abnagg_armor derpy_abnagg_ench derpy_abnagg_weapon
derpy_azeros_armor derpy_azeros_ench derpy_azeros_talisman derpy_azeros_weapon
derpy_balur_talisman derpy_balur_weapon
derpy_black_dwf_armor derpy_black_dwf_talisman derpy_black_dwf_weapon
derpy_bzaark_armor derpy_bzaark_talisman derpy_bzaark_weapon
derpy_gargath_armor derpy_gargath_ench derpy_gargath_weapon
derpy_ghorth_armor derpy_ghorth_ench derpy_ghorth_talisman derpy_ghorth_weapon
derpy_gordak_armor derpy_gordak_weapon
derpy_snakebeard_armor derpy_snakebeard_talisman derpy_snakebeard_weapon
derpy_tordrek_armor derpy_tordrek_talisman derpy_tordrek_weapon
derpy_urzkhal_armor derpy_urzkhal_talisman derpy_urzkhal_weapon
derpy_vraznak_armor derpy_vraznak_weapon
derpy_warrhak_armor derpy_warrhak_ench derpy_warrhak_weapon
""".split())


# Ghorth pays no trophy. His five routes are the Conclave's own, and he already holds the
# Tower - handing him a vanilla Chaos Dwarf relic on top of the purse was the same mistake as
# filter 1 one step out, so his payload is the purse alone. None here, and payload_lines
# already omits the block for a falsy trophy.
NO_TROPHY_FACTIONS = frozenset({"wh3_dlc23_chd_conclave"})


def route_reward_item(faction, idx):
    """The trophy for one route, or None for a house that pays none. Offset by the house index
    as well as the route index, so the routes of one house never repeat an item and the eight
    are spread across the roster."""
    if faction in NO_TROPHY_FACTIONS:
        return None
    return TROPHIES[(HOUSES.index(faction) + idx) % len(TROPHIES)]

# Verified key lists - docs/sessions/HOUSE_MISSION_OPTIONS_20260903.md section 7.
POOLED_RESOURCES = {
    "wh3_dlc23_chd_labour", "wh3_dlc23_chd_raw_materials", "wh3_dlc23_chd_armaments",
    "wh3_dlc23_chd_workload", "wh3_dlc23_chd_efficiency",
    "wh3_dlc23_chd_conclave_influence",
}
RITUAL_CATEGORIES = {
    "DISTRICTS_SORCERY_T1", "DISTRICTS_SORCERY_T2", "DISTRICTS_SORCERY_T3",
    "DISTRICTS_INDUSTRY_T1", "DISTRICTS_INDUSTRY_T2", "DISTRICTS_INDUSTRY_T3",
    "DISTRICTS_MILITARY_T1", "DISTRICTS_MILITARY_T2", "DISTRICTS_MILITARY_T3",
    "TOZ_TIER_4", "LABOUR_ACTIONS", "DRILL_RAW_MATERIALS", "DRILL_TREASURY",
    "HELLFORGE_CAPS_KDAAI", "HELLFORGE_CAPS_BULL_CENTAURS",
    "HELLFORGE_CAPS_FLYING_BEASTS", "HELLFORGE_CAPS_MELEE_INFANTRY",
    "HELLFORGE_CAPS_MISSILE_INFANTRY", "HELLFORGE_CAPS_WARMACHINES",
    # the mod's own fifth tier
    "DISTRICTS_ANNEX_T5_A", "DISTRICTS_ANNEX_T5_B", "DISTRICTS_ANNEX_T5_C",
}
BUILDING_LEVELS = set()
for _stem, _hi in [
    ("wh3_dlc23_chd_tower_tribute_halls", 5), ("wh3_dlc23_chd_tower_furnace", 2),
    ("wh3_dlc23_chd_tower_ballistics", 2), ("wh3_dlc23_chd_settlement_tower", 5),
    # read out of vanilla `building_levels` 2026-09-08, like the rest of this list
    ("wh3_dlc23_chd_tower_temple_guardhouse", 5),
    ("wh3_dlc23_chd_settlement_factory", 3), ("wh3_dlc23_chd_military_kdaai", 3),
    ("wh3_dlc23_chd_military_beasts", 3), ("wh3_dlc23_chd_military_war_machines", 3),
    ("wh3_dlc23_chd_military_hobgoblins", 2),
    ("wh3_dlc23_chd_military_chaos_dwarf_infantry", 3),
    ("wh3_dlc23_chd_factory_assembly_line", 3), ("wh3_dlc23_chd_factory_refinery", 3),
    ("wh3_dlc23_chd_factory_drills", 2), ("wh3_dlc23_chd_outpost_mine", 3),
]:
    for _i in range(1, _hi + 1):
        BUILDING_LEVELS.add("%s_%d" % (_stem, _i))
BUILDING_LEVELS.add("wh3_dlc23_chd_tower_temple_of_hashut_1")

# DESTROY_FACTION targets. The first two were probed in a live cr_oldworld campaign on
# 2026-09-07 and answered present. They are core WH1 factions, which is the reason to pick
# them: a faction absent from a map makes its objective unachievable, silently and for ever.
#
# `wh2_main_hef_fortress_of_dawn` is Abnagg's elf-grudge target and is NOT live-probed yet.
# What it does have, read 2026-09-09: a row in vanilla `factions` (subculture
# wh2_main_sc_hef_high_elves), 4 byte occurrences in IEE's `startpos.esf` beside its own flag
# path and a `start_pos_factions_description` key, and 11 in `!cr_oldworld_campaign.pack`. CA
# names its region in `victory_objectives.lua` itself. That is DB and startpos evidence, not a
# live probe - see the open list in the handoff.
#
# `wh_main_dwf_barak_varr` is Tordrek's grudge (he was exiled from Barak Varr for shooting Red
# Brokk - Dreadfleet rulebook pp. 66-67). Read 2026-10-04: a row in vanilla `factions`, and the
# key in the decompressed body of an Old World save (`House of Azeros_Auto-save.4...`). Only ever
# named inside a route gated on `cr_oldworld_region_barak_varr`, so a map without the region
# never sees the objective.
#
# `cr_dwf_slaves_of_zharr` / `cr_ogr_slaves_of_zharr` are the Chained and the Thralls of Zharr,
# the two slave revolts the Old World war start sets on the Overlords of Zharrduk. Read
# 2026-10-07: a row each in the installed `!cr_oldworld_campaign.pack` `factions` table, and two
# occurrences each in its `campaigns/cr_oldworld/startpos.esf`. Only ever named inside a route
# gated on `cr_oldworld_region_zharr_naggrund`.
DESTROY_TARGETS = {"wh_main_dwf_dwarfs", "wh_main_grn_greenskins",
                   "wh2_main_hef_fortress_of_dawn", "wh_main_dwf_barak_varr",
                   "cr_dwf_slaves_of_zharr", "cr_ogr_slaves_of_zharr"}

# Regions a map-gated objective may name. A region key is as unvalidated as any other string,
# and this one has to be right twice - the objective needs it and so does the runtime probe
# that decides which variant to issue.
#
# `wh3_main_combi_region_fortress_of_dawn`: in vanilla `campaign_map_regions` on all five
# `wh3_main_combi_map_*` maps, in IEE's own `!cr_vanilla` fragment against
# `cr_combi_expanded_map_1`, and in CA's `victory_objectives.lua` as an
# OWN_N_REGIONS_INCLUDING `region` line (Aislinn's colonies). NOT on `cr_oldworld_map_1` -
# that fragment has zero occurrences of it - which is the whole reason the gate exists.
#
# The rest, read 2026-10-04. `wh3_main_combi_region_praag` / `_salzenmund` are rows in vanilla
# `regions` (read_vanilla_db). The `cr_oldworld_region_*` five are in the decompressed body of
# an Old World save (`House of Azeros_Auto-save.4...`, read_save_values.body) - the Old World mod
# is not installed here, so that save is the only offline list of its regions. Praag and
# Salzenmund are the Black Dwarf's two named targets (White Dwarf 201, "Furnace of Hashut");
# the Oak of Ages stands for Athel Loren in Vraznak's Skull River raid (WD 170); Barak Varr is
# Tordrek's grudge.
VERIFIED_REGIONS = {"wh3_main_combi_region_fortress_of_dawn",
                    "wh3_main_combi_region_praag", "wh3_main_combi_region_salzenmund",
                    "cr_oldworld_region_praag", "cr_oldworld_region_salzenmund",
                    "cr_oldworld_region_the_oak_of_ages", "cr_oldworld_region_barak_varr",
                    # CA's campaign_map_regions; the Old World key out of the installed
                    # !cr_oldworld_campaign.pack (the Dark Lands reuse that namespace)
                    "wh3_main_combi_region_mount_silverspear",
                    "cr_oldworld_region_mount_silverspear",
                    # Kharkadon's gate: 99 occurrences in the installed !cr_oldworld_campaign.pack,
                    # and the same key derpy_start_new_house_lords.lua already probes to place him
                    "cr_oldworld_region_zharr_naggrund"}

# The eleven playable houses, and which annex group each belongs to. A house may perform any
# annex ritual but its own, so a `total` must stay under its own group's size. Read out of the
# Tower's own ANNEX_DISTRICTS in the shipped zz_derpy_toz_annex.lua, never typed: a typed copy
# went stale twice - it kept B and C at 3 seats after the two new lords made them 4, and a seat
# swap (2026-10-03, Khorakk to Thrall) would have sent Khorakk's Tower route into the district
# he left. gen_new_house_lords.check_annex_lua() ties that Lua to templates/toz_districts.py.
# Ghorth is in none - he already holds the Tower.
ANNEX_LUA = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", "wh3_main_combi", "mod",
                         "zz_derpy_toz_annex.lua")


def _annex_groups():
    text = open(ANNEX_LUA, encoding="utf-8").read()
    body = text[text.index("local ANNEX_DISTRICTS"):]
    body = body[:body.index("\n}")]
    groups = {}
    for m in re.finditer(r'key = "DISTRICTS_ANNEX_T5_(\w)", seats = \{(.*?)\}\},', body, re.S):
        for faction in re.findall(r'faction = "(\w+)"', m.group(2)):
            groups[faction] = m.group(1)
    return groups


_GROUPS = _annex_groups()
ANNEX_GROUP = {f: _GROUPS[f] for f in (
    "cr_chd_house_of_khorakk", "cr_chd_house_of_baal", "cr_chd_fists_of_hashut",
    "cr_chd_horns_of_hashut", "cr_chd_slaves_of_the_black_dwarf", "cr_chd_warfleet_of_uzkulak",
    "cr_chd_black_kraken_armada", "cr_chd_house_of_bzaark", "cr_chd_snakebeards_artificers",
    "cr_chd_house_of_azeros", "wh3_dlc23_chd_minor_faction", "cr_chd_skullstack")}
ANNEX_GROUP["wh3_dlc23_chd_conclave"] = None
GROUP_SIZE = {g: list(_GROUPS.values()).count(g) for g in set(_GROUPS.values())}

# ---------------------------------------------------------------------------
# The routes. Three per house, drawn from that house's own skill line where there is one -
# docs/sessions/HOUSE_MISSION_OPTIONS_20260903.md section 5 named them.
#
# Each route is (slug, display name, [(objective type, [conditions...]), ...]).
# Route 1 is the house's craft, route 2 the Tower, route 3 the war. They are alternatives:
# completing any one wins the campaign.
# ---------------------------------------------------------------------------


def _tower(faction, total):
    """The Tower route's annex objective, in the house's own group."""
    group = ANNEX_GROUP[faction] or "A"
    return ("PERFORM_RITUAL",
            ["ritual_category DISTRICTS_ANNEX_T5_%s" % group, "total %d" % total])


def _on_map(region, objectives):
    """A route's map-gated objective list: used only where `region` exists. `region` may be
    a tuple of keys, one per map namespace - the list is used where ANY of them exists, which
    is how a route reaches both IE/IEE (`wh3_main_combi_region_*`) and the Old World
    (`cr_oldworld_region_*`). A tuple-gated list cannot name a region itself (no one key
    exists on every map it is used on); it must stay namespace-free."""
    return (region, objectives)


def gate_keys(region):
    """A gate as a tuple of region keys, whether it was written as one key or several."""
    return tuple(region) if isinstance(region, (tuple, list)) else (region,)


ROUTES = {
    "cr_chd_house_of_khorakk": [
        ("ledger_of_flesh", "The Ledger of Flesh", [
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_labour", "total 2000"]),
            ("CONSTRUCT_N_OF_A_BUILDING",
             ["building_level wh3_dlc23_chd_military_hobgoblins_2", "total 3"]),
        ]),
        ("chains_of_domination", "Chains of Domination", [
            _tower("cr_chd_house_of_khorakk", 2),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_conclave_influence", "total 60"]),
        ]),
        ("the_collection", "The Collection", [
            ("DESTROY_FACTION", ["faction wh_main_grn_greenskins", "confederation_valid"]),
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 25"]),
        ]),
    ],
    "cr_chd_house_of_baal": [
        ("bind_the_kdaai", "Bind the K'daai", [
            ("CONSTRUCT_N_OF_A_BUILDING",
             ["building_level wh3_dlc23_chd_military_kdaai_3", "total 2"]),
            ("PERFORM_RITUAL", ["ritual_category HELLFORGE_CAPS_KDAAI", "total 2"]),
        ]),
        ("the_iron_cages", "The Iron Cages", [
            _tower("cr_chd_house_of_baal", 2),
            ("CONSTRUCT_N_BUILDINGS_INCLUDING",
             ["building_level wh3_dlc23_chd_tower_furnace_2", "total 1"]),
        ]),
        ("stoke_the_furnace", "Stoke the Furnace", [
            ("DESTROY_FACTION", ["faction wh_main_dwf_dwarfs", "confederation_valid"]),
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 25"]),
        ]),
    ],
    # "We shall be known as the Fists of Hashut. Let the world tremble at our name." - Gargath,
    # naming the host his brother Balur marched in (White Dwarf 203). The host: great-weapon
    # warriors, Blunderbusses, the Tower's own Bull Centaurs and an Earthshaker battery. Balur
    # is this mod's melee lord, so the two Hell-Forge rituals are the melee infantry and the
    # Bull Centaurs rather than the guns. Slugs are unchanged on purpose: the slug is part of
    # the victory_types key, and a renamed key orphans the node in every running save.
    "cr_chd_fists_of_hashut": [
        ("the_unholy_legion", "Let the World Tremble", [
            ("CONSTRUCT_N_OF_A_BUILDING",
             ["building_level wh3_dlc23_chd_military_chaos_dwarf_infantry_3", "total 3"]),
            ("OWN_N_UNITS", ["total 60"]),
            ("PERFORM_RITUAL", ["ritual_category HELLFORGE_CAPS_MELEE_INFANTRY", "total 1"]),
            ("PERFORM_RITUAL", ["ritual_category HELLFORGE_CAPS_BULL_CENTAURS", "total 1"]),
        ]),
        ("the_black_altar", "The Brothers' Altar", [
            ("CONSTRUCT_N_BUILDINGS_INCLUDING",
             ["building_level wh3_dlc23_chd_tower_temple_of_hashut_1", "total 1"]),
            _tower("cr_chd_fists_of_hashut", 2),
        ]),
        ("break_the_throng", "Break the Throng", [
            ("DESTROY_FACTION", ["faction wh_main_dwf_dwarfs", "confederation_valid"]),
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 20"]),
        ]),
    ],
    "cr_chd_horns_of_hashut": [
        ("the_herd_of_hashut", "The Herd of Hashut", [
            ("CONSTRUCT_N_OF_A_BUILDING",
             ["building_level wh3_dlc23_chd_military_beasts_3", "total 2"]),
            ("PERFORM_RITUAL",
             ["ritual_category HELLFORGE_CAPS_BULL_CENTAURS", "total 2"]),
        ]),
        ("hide_of_the_iron_bull", "Hide of the Iron Bull", [
            _tower("cr_chd_horns_of_hashut", 2),
            ("ACHIEVE_CHARACTER_RANK", ["total 1", "total2 25", "include_generals"]),
        ]),
        # Vraznak's raid on the Wood Elves (White Dwarf 170, "The Battle of Skull River"):
        # revenge for a Sorcerer Lord murdered in the Temple of Hashut, the forest burned with
        # oil and tar, the skulls carried home. Gated on Athel Loren being on the map - the Old
        # World has it, the Dark Lands do not - and off it the route stays the old stampede
        # through the Greenskins he hired past Mount Gunbad. CA's own Lua issues
        # DEFEAT_N_ARMIES_OF_FACTION with a `subculture` line through this same string route.
        ("the_stampede", "The Skull River Raid", [
            ("DESTROY_FACTION", ["faction wh_main_grn_greenskins", "confederation_valid"]),
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 25"]),
        ], _on_map("cr_oldworld_region_the_oak_of_ages", [
            ("DEFEAT_N_ARMIES_OF_FACTION",
             ["subculture wh_dlc05_sc_wef_wood_elves", "total 15"]),
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 20"]),
            ("CAPTURE_X_BATTLE_CAPTIVES", ["total 2000"]),
        ])),
    ],
    # The Black Dwarf and Abnagg (below) are the only two houses of the ten that
    # IMMORTAL EMPIRES EXPANDED places - `ime_derpy_black_dwarf.lua` says so in its own
    # header, and the tower seating script logs "seated 2, skipped 8" there. With Ghorth
    # that makes three houses a player meets in IEE, so these two carry FIVE routes like
    # his rather than the roster's three: they are the ones that will actually be seen.
    #
    # Everything below is still map-agnostic - see WHY NO PROVINCE OR REGION OBJECTIVES at
    # the top. Both houses also exist in cr_oldworld, so an IEE-only region key would kill
    # the route on the other map silently. What "IEE" changed is the CONTENT, not the
    # palette: the annex totals, and the two lords' own material.
    #
    # The annex route is completable in IEE even though the other group-B house
    # (black_kraken, Tordrek) is absent. `zz_derpy_toz_annex.lua` decides per seat at
    # runtime: ANNEX mode confederates a faction the campaign placed, GRANT mode spawns the
    # missing lord into the claimant's recruitment pool instead. Two seats is also the
    # ceiling for a group-B house - a house may claim any seat but its own - so these are
    # the whole of district B, and in IEE one of the two is the OTHER of these two lords.
    "cr_chd_slaves_of_the_black_dwarf": [
        # I - the Road to Praag. His own plan in White Dwarf 201 ("Furnace of Hashut"): sack
        # Praag and Salzenmund, then hold the passes west for the Cathay and Ind trade. It
        # replaced "The Unbreached Wall" (2026-10-04), which made him win by not moving - the
        # opposite of the one lord on the list whose lore is a march west. The slug stays
        # `the_unbreached_wall` because it is part of the victory_types key.
        #
        # Gated on Praag in EITHER namespace, so IE/IEE and the Old World both get the war on
        # Kislev and the Empire, and a map without Praag (the Dark Lands) gets a plain campaign
        # of conquest instead of an objective against factions it may not have. The named
        # cities themselves are the quest below, `derpy_mis_black_dwarf_road_to_praag_*`.
        ("the_unbreached_wall", "The Road to Praag", [
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 25"]),
            ("DEFEAT_N_ARMIES_OF_FACTION", ["total 30"]),
        ], _on_map(("wh3_main_combi_region_praag", "cr_oldworld_region_praag"), [
            ("DEFEAT_N_ARMIES_OF_FACTION", ["subculture wh3_main_sc_ksl_kislev", "total 12"]),
            ("DEFEAT_N_ARMIES_OF_FACTION", ["subculture wh_main_sc_emp_empire", "total 12"]),
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 25"]),
        ])),
        # II - the Tower, and the Grand Council of the Sorcerer Lords his Praag campaign was
        # meant to buy him a seat on. Both seats of district B, which in IEE means the
        # Warfleet (present, so confederated) and the Black Kraken (absent, so granted).
        ("chains_of_the_conclave", "A Seat on the Grand Council", [
            _tower("cr_chd_slaves_of_the_black_dwarf", 2),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_conclave_influence", "total 150"]),
        ]),
        # III - the war, and it is a slaving war: his faction is Slaves of the Black Dwarf
        # and the Greenskins are the stock. One DESTROY_FACTION objective carrying its
        # target, which is how both CA and VCO write them.
        ("the_slave_harvest", "The Slave Harvest", [
            ("DESTROY_FACTION", ["faction wh_main_grn_greenskins",
                                 "confederation_valid", "vassalization_valid"]),
            ("CAPTURE_X_BATTLE_CAPTIVES", ["total 4000"]),
        ]),
        # IV - the Granite Legion: his skill line's elite infantry, built and armed.
        # `military_chaos_dwarf_infantry_3` needs a level-4 settlement under it
        # (`primary_slot_building_building_level_requirement`), so two of them is two grown
        # cities on top of the units and the armaments.
        ("the_granite_legion", "The Granite Legion", [
            ("CONSTRUCT_N_OF_A_BUILDING",
             ["building_level wh3_dlc23_chd_military_chaos_dwarf_infantry_3", "total 2"]),
            ("OWN_N_UNITS", ["total 60"]),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_armaments", "total 500"]),
        ]),
        # V - Wrought of Living Stone: the petrification, and the anvil it stands on. The
        # rank is his skill line's capstone; the battles are the armies that broke on him
        # rather than settlements he took, which is the one thing this house is about.
        ("wrought_of_living_stone", "Wrought of Living Stone", [
            ("ACHIEVE_CHARACTER_RANK", ["total 1", "total2 30", "include_generals"]),
            ("DEFEAT_N_ARMIES_OF_FACTION", ["total 40"]),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_labour", "total 3000"]),
        ]),
    ],
    "cr_chd_house_of_bzaark": [
        ("proof_by_fire", "Proof by Fire", [
            ("CONSTRUCT_N_OF_A_BUILDING",
             ["building_level wh3_dlc23_chd_military_war_machines_3", "total 2"]),
            ("PERFORM_RITUAL",
             ["ritual_category HELLFORGE_CAPS_WARMACHINES", "total 2"]),
        ]),
        ("the_proven_pattern", "The Proven Pattern", [
            _tower("cr_chd_house_of_bzaark", 1),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_armaments", "total 500"]),
        ]),
        ("firespitters_prototype", "Firespitter's Prototype", [
            ("DESTROY_FACTION", ["faction wh_main_dwf_dwarfs", "confederation_valid"]),
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 25"]),
        ]),
    ],
    "cr_chd_snakebeards_artificers": [
        # Named for his own White Dwarf 103 feature, "Crush, Crumble and Chop" - the
        # Tenderiser and the Whirlwind. Those machines live in his unit pack, which this pack
        # must not depend on, so the objectives stay the war-machine forges.
        ("deathshrieker_doctrine", "Crush, Crumble and Chop", [
            ("CONSTRUCT_N_OF_A_BUILDING",
             ["building_level wh3_dlc23_chd_military_war_machines_3", "total 3"]),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_armaments", "total 400"]),
        ]),
        ("the_iron_road", "The Iron Road", [
            ("CONSTRUCT_N_OF_A_BUILDING",
             ["building_level wh3_dlc23_chd_factory_assembly_line_3", "total 3"]),
            _tower("cr_chd_snakebeards_artificers", 1),
        ]),
        ("masterwork_artillery", "Masterwork Artillery", [
            ("DESTROY_FACTION", ["faction wh_main_dwf_dwarfs", "confederation_valid"]),
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 20"]),
        ]),
    ],
    "cr_chd_house_of_azeros": [
        ("ten_thousand_hammers", "Ten Thousand Hammers", [
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_raw_materials", "total 600"]),
            ("CONSTRUCT_N_OF_A_BUILDING",
             ["building_level wh3_dlc23_chd_factory_refinery_3", "total 2"]),
        ]),
        ("the_masters_mark", "The Master's Mark", [
            _tower("cr_chd_house_of_azeros", 1),
            ("CONSTRUCT_N_OF_A_BUILDING",
             ["building_level wh3_dlc23_chd_settlement_factory_3", "total 3"]),
        ]),
        ("the_great_refinery", "The Great Refinery", [
            ("DESTROY_FACTION", ["faction wh_main_grn_greenskins", "confederation_valid"]),
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 25"]),
        ]),
    ],
    # The two naval houses deliberately carry no horde-building objective. No vanilla
    # mission counts a horde building (HOUSE_MISSION_OPTIONS section 5, H1/K1, rated
    # Untested), and an untested objective shape inside a VICTORY condition is the worst
    # place to find out - it cannot be patched out of a running save. So Abnagg's flagship
    # is the thing he DOES it all with, never the thing counted: his routes count raiding,
    # captives, sacked coasts and guns instead.
    #
    # The second of the two houses IEE places, and the one it places on top of Barak Varr -
    # `ime_derpy_abnagg.lua` spawns him at `wh3_main_combi_region_barak_varr` (185, 366) as
    # a converted DERPY_CHD_NAVAL_HORDE with no settlement of his own. Hence route IV, the
    # only one that needs him to hold ground, is the artillery route rather than his craft
    # route, and routes I, III and V ask for nothing a fleet cannot do from the water.
    # The Dwarfs are his DESTROY target for the same reason: he starts in their harbour.
    "cr_chd_warfleet_of_uzkulak": [
        # I - Tyrant of the Waves, his own skill line's name, and the trade he is in.
        # 7,500 is VCO's own figure for EARN_X_AMOUNT_FROM_RAIDING (its single use, on
        # Wintertooth), which is the only attested amount for a type this rare.
        ("tyrant_of_the_waves", "Tyrant of the Waves", [
            ("EARN_X_AMOUNT_FROM_RAIDING", ["total 7500"]),
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 25"]),
        ]),
        # II - the Tower: both seats of district B, the Black Dwarf's (present in IEE, so
        # confederated) and the Black Kraken's (absent, so granted).
        ("the_hellbeard_ashore", "The Hellbeard Comes Ashore", [
            _tower("cr_chd_warfleet_of_uzkulak", 2),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_conclave_influence", "total 150"]),
        ]),
        # III - Siege Mastermind, and the one map-gated route in the file. On Immortal
        # Empires and IEE it is the elf grudge: burn the High Elf colony at the Fortress of
        # Dawn and hold the fortress itself. Off those maps the region does not exist, so
        # the route falls back to the holds he actually starts next to.
        #
        # Why the Fortress of Dawn and not Lothern: CA already built a **Chaos Dwarf**
        # version of its landmark harbour. `wh3_dlc23_special_fortress_of_dawn_dawns_harbour_chd`
        # is chain_category `money` on the `wh_main_sch_port` superchain, and at level 3 pays
        # +500 sea-trade GDP, +5 post-battle labour and storm/reef attrition immunity
        # factionwide - a trade port, a slave engine and safe water for a fleet, in one
        # region. It is the single most Abnagg settlement on the map, and it is held by
        # elves. Hatred with a ledger behind it.
        #
        # High Elves rather than Dark Elves on purpose: Naggarond is the Chaos Dwarfs' slave
        # customer, so the grudge that reads as lore is the one against the elves who hunt
        # slavers, not the ones who buy from them.
        # His oath (Plague Fleet rulebook p. 17): never to return to Zharr-Naggrund without the
        # foundation stone of the elf citadel. The slug keeps its old name - see Balur's note.
        ("siege_mastermind", "The Foundation Stone", [
            ("DESTROY_FACTION", ["faction wh_main_dwf_dwarfs",
                                 "confederation_valid", "vassalization_valid"]),
            ("DEFEAT_N_ARMIES_OF_FACTION", ["total 30"]),
        ], _on_map("wh3_main_combi_region_fortress_of_dawn", [
            ("OWN_N_REGIONS_INCLUDING",
             ["region wh3_main_combi_region_fortress_of_dawn", "total 1"]),
            ("DESTROY_FACTION", ["faction wh2_main_hef_fortress_of_dawn",
                                 "confederation_valid", "vassalization_valid"]),
            ("DEFEAT_N_ARMIES_OF_FACTION", ["total 25"]),
        ])),
        # IV - Infernal Artillery Specialist. The one route that needs him to hold ground:
        # the guns are built ashore and the Hell-Forge caps are what let him field them.
        # `military_war_machines_3` carries
        # `primary_slot_building_building_level_requirement = 5`, so ONE of them already
        # means a settlement grown to its top tier - two would be the hardest ask in the
        # file for a lord who starts with no settlement at all.
        ("infernal_artillery", "Infernal Artillery", [
            ("CONSTRUCT_N_OF_A_BUILDING",
             ["building_level wh3_dlc23_chd_military_war_machines_3", "total 1"]),
            ("PERFORM_RITUAL",
             ["ritual_category HELLFORGE_CAPS_WARMACHINES", "total 2"]),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_armaments", "total 400"]),
        ]),
        # V - Fleetmaster's Command: the fleet as a slaving concern. Captives and labour
        # are what a Chaos Dwarf raider sails for, and 50 units is the fleet that carries
        # them - under CA's own 60 for a land house, because these are ships.
        ("fleetmasters_command", "Fleetmaster's Command", [
            ("CAPTURE_X_BATTLE_CAPTIVES", ["total 3000"]),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_labour", "total 2000"]),
            ("OWN_N_UNITS", ["total 50"]),
        ]),
    ],
    "cr_chd_black_kraken_armada": [
        ("crew_of_the_drowned", "Crew of the Drowned", [
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 30"]),
            ("ACHIEVE_CHARACTER_RANK", ["total 1", "total2 25", "include_generals"]),
        ]),
        ("daemonpact_of_the_deep", "Daemonpact of the Deep", [
            _tower("cr_chd_black_kraken_armada", 1),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_conclave_influence", "total 60"]),
        ]),
        # The grudge he sails for (Dreadfleet rulebook pp. 66-67): Barak Varr, which banished
        # him for shooting Red Brokk Gunnarsson a dozen times with a rivet claw. Gated on the
        # port being on the map; off it, the old war on the Dwarfs at large.
        ("rivalrys_wrath", "Rivalry's Wrath", [
            ("DESTROY_FACTION", ["faction wh_main_dwf_dwarfs", "confederation_valid"]),
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 20"]),
        ], _on_map("cr_oldworld_region_barak_varr", [
            ("DESTROY_FACTION", ["faction wh_main_dwf_barak_varr",
                                 "confederation_valid", "vassalization_valid"]),
            ("OWN_N_REGIONS_INCLUDING", ["region cr_oldworld_region_barak_varr", "total 1"]),
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 20"]),
        ])),
    ],
    # Ghorth already sits at the Tower's summit, so his routes are about holding it and
    # about what the Conclave can compel, not about climbing.
    #
    # He is the only house carrying FIVE routes rather than three, and the only one that
    # can. GHORTH_MISSION_OPTIONS_20260903.md section 1 names three identity pillars -
    # Sorcerer-Prophet of Hashut, Master of the Conclave, Tyrant of Zharr-Naggrund - drawn
    # from his own skill tree; the three-route shape covered one of them twice and the
    # other two not at all. Routes I, II and III keep the roster's craft / Tower / war
    # meaning so the shared slot icons still mean the same thing at the same index; IV and
    # V are the two pillars that had no route. VCO ships 3 routes for 129 of its factions
    # and 4 for the other 4, so more than three is its practice as well as ours.
    #
    # Slots I-III keep their old POSITIONS, not their old contents: the Tower route was
    # sitting at index 0, wearing the `short` icon every other house gives its craft route.
    #
    # Depth per route follows VCO's measured shape - its routes carry 1 to 4 engine-
    # evaluated objectives, most often 2 or 3. Three was the target here.
    "wh3_dlc23_chd_conclave": [
        # I - Sorcerer-Prophet of Hashut. DISTRICTS_SORCERY_T3 holds exactly two seats in
        # vanilla `rituals`, so `total 2` is "take the whole top of the sorcery ladder"
        # rather than an open-ended grind, and a seat an AI reached first is still
        # reachable through the usurp path (TOWER_OF_ZHARR_CUSTOM_SEATS.md section 11).
        ("the_blackening", "The Blackening", [
            ("PERFORM_RITUAL", ["ritual_category DISTRICTS_SORCERY_T3", "total 2"]),
            ("CONSTRUCT_N_BUILDINGS_INCLUDING",
             ["building_level wh3_dlc23_chd_tower_temple_of_hashut_1", "total 1"]),
            # After a confederation the faction holds other lords and this can be satisfied
            # by one of them. Acceptable in a faction-scoped victory condition; it is the
            # reason the mission document rates the same objective SCRIPTED for a quest
            # that has to mean Ghorth personally.
            ("ACHIEVE_CHARACTER_RANK", ["total 1", "total2 30", "include_generals"]),
        ]),
        # II - Master of the Conclave. Ghorth belongs to no annex group, so he is the only
        # house that can be asked for seats in more than one district: every other house
        # sits inside one of the three and may not annex itself. Two seats from Bloodline
        # (4 seats) and two from Thrall (4) stays inside both group sizes and inside the
        # two-of-a-type ceiling.
        ("the_seat_of_zharr", "The Seat of Zharr", [
            ("PERFORM_RITUAL", ["ritual_category DISTRICTS_ANNEX_T5_A", "total 2"]),
            ("PERFORM_RITUAL", ["ritual_category DISTRICTS_ANNEX_T5_B", "total 2"]),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_conclave_influence", "total 200"]),
        ]),
        # III - the war, in VCO's own shape. ONE objective carrying both targets: every
        # multi-target DESTROY_FACTION in CA's file (93 objectives, 258 `faction` lines) and
        # in VCO's (181 / 528) is a single objective with a `faction` line per target. This
        # shipped as two separate DESTROY_FACTION objectives, a shape neither source writes.
        # `vassalization_valid` is VCO's flag (33 uses, CA 5): Ghorth already holds Zhatan as
        # a vassal, so counting a vassal as settled is the Conclave's own idea of a result.
        # 35 armies is VCO's own figure for the Chaos Dwarf war routes.
        ("hashuts_ledger", "Hashut's Ledger", [
            ("DESTROY_FACTION", ["faction wh_main_dwf_dwarfs",
                                 "faction wh_main_grn_greenskins",
                                 "confederation_valid", "vassalization_valid"]),
            ("DEFEAT_N_ARMIES_OF_FACTION", ["total 35"]),
        ]),
        # IV - Tyrant of Zharr-Naggrund: the Tower itself rather than the seats in it. Both
        # chains top out at the level named, and both are the Tower's own, so this is the
        # one route that dies with the city.
        ("the_conclaves_writ", "The Conclave's Writ", [
            ("CONSTRUCT_N_BUILDINGS_INCLUDING",
             ["building_level wh3_dlc23_chd_tower_tribute_halls_5", "total 1"]),
            ("CONSTRUCT_N_BUILDINGS_INCLUDING",
             ["building_level wh3_dlc23_chd_tower_temple_guardhouse_5", "total 1"]),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_conclave_influence", "total 400"]),
            # The Bull Centaurs of the Tower of Zharr, which he grants as an honour (White
            # Dwarf 203, Ghorth to Gargath).
            ("PERFORM_RITUAL", ["ritual_category HELLFORGE_CAPS_BULL_CENTAURS", "total 1"]),
        ]),
        # V - the tribute economy the whole Conclave runs on: slaves in, war material out.
        # CAPTURE_X_BATTLE_CAPTIVES is VCO's (11 uses, none in CA), and 5,000 is the figure
        # it gives Astragoth - the one objective in this whole file that says "Chaos Dwarf"
        # without naming a Chaos Dwarf key.
        ("the_tribute_of_slaves", "The Tribute of Slaves", [
            ("CAPTURE_X_BATTLE_CAPTIVES", ["total 5000"]),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_labour", "total 3000"]),
            ("CONSTRUCT_N_OF_A_BUILDING",
             ["building_level wh3_dlc23_chd_factory_refinery_3", "total 3"]),
        ]),
    ],
    # Kharkadon the Vicious and the Overlords of Zharrduk (CA's minor faction), added
    # 2026-10-07. No Lexicanum entry, so the routes come from the house as this mod built it:
    # the Immortals (CA's Infernal Ironsworn), veteran lords, and his own line - First into the
    # Breach, Plate and Oath, Blood and Iron. LAST in this dict on purpose: purse and trophy
    # rotate by HOUSES.index, so appending moves no other house's rewards.
    "wh3_dlc23_chd_minor_faction": [
        # I - the Immortals. `military_chaos_dwarf_infantry_3` is the only building that allows
        # `wh3_dlc23_chd_inf_infernal_ironsworn` (vanilla building_units_allowed, read
        # 2026-10-07), and HELLFORGE_CAPS_MELEE_INFANTRY is the ritual that raises their cap.
        ("immortal_legions", "The Immortal Legions", [
            ("CONSTRUCT_N_OF_A_BUILDING",
             ["building_level wh3_dlc23_chd_military_chaos_dwarf_infantry_3", "total 2"]),
            ("PERFORM_RITUAL", ["ritual_category HELLFORGE_CAPS_MELEE_INFANTRY", "total 2"]),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_armaments", "total 500"]),
        ]),
        # II - the Tower: two of the three Bloodline seats he may claim, and one seasoned lord.
        ("lords_of_zharrduk", "Lords of Zharrduk", [
            _tower("wh3_dlc23_chd_minor_faction", 2),
            ("ACHIEVE_CHARACTER_RANK", ["total 1", "total2 25", "include_generals"]),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_conclave_influence", "total 150"]),
        ]),
        # III - the war. Where Zharr-Naggrund is on the map (the Old World, the Dark Lands) the
        # two slave revolts the war start sets on him are the enemy at his gates; elsewhere the
        # Dwarfs.
        ("blood_and_iron", "Blood and Iron", [
            ("DESTROY_FACTION", ["faction wh_main_dwf_dwarfs", "confederation_valid"]),
            ("DEFEAT_N_ARMIES_OF_FACTION", ["total 35"]),
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 20"]),
        ], _on_map("cr_oldworld_region_zharr_naggrund", [
            ("DESTROY_FACTION", ["faction cr_dwf_slaves_of_zharr",
                                 "faction cr_ogr_slaves_of_zharr", "confederation_valid"]),
            ("DEFEAT_N_ARMIES_OF_FACTION", ["total 30"]),
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 20"]),
        ])),
        # IV - asked for by name: Grimgor's Ardboyz and the Dwarfs, both gone. One objective with
        # a `faction` line per target, as every multi-target DESTROY_FACTION in CA and VCO is.
        # confederation_valid but NOT vassalization_valid: extinct, not kneeling.
        ("the_extinction", "The Extinction", [
            ("DESTROY_FACTION", ["faction wh_main_grn_greenskins", "faction wh_main_dwf_dwarfs",
                                 "confederation_valid"]),
        ]),
    ],
    # The Uzkul Mingol Company (IEE's cr_chd_skullstack) and its Captain, added 2026-10-11. No
    # Lexicanum entry, so the routes come from his own line: Company Charter, Prospectors, Ivory
    # Road Factors, Spoils of Ind, The Long March. Map-agnostic for now: named places in Ind are
    # phase 4. LAST in this dict, like Kharkadon: purse and trophy rotate by HOUSES.index.
    "cr_chd_skullstack": [
        # I: the plunder the Charter is paid from. Every type here already ships in Abnagg's or
        # Vraznak's routes, and 7,500 is VCO's own raiding figure.
        ("spoils_of_ind", "Spoils of Ind", [
            ("EARN_X_AMOUNT_FROM_RAIDING", ["total 7500"]),
            ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 20"]),
            ("CAPTURE_X_BATTLE_CAPTIVES", ["total 2000"]),
        ]),
        # II: the Tower. Two of the three Forge District seats he may claim (the fourth is his
        # own), and the influence to hold them.
        ("the_company_charter", "The Company Charter", [
            _tower("cr_chd_skullstack", 2),
            ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
             ["pooled_resource wh3_dlc23_chd_conclave_influence", "total 150"]),
        ]),
        # III: the war, on the road from the Dark Lands to Ind.
        ("the_long_march", "The Long March", [
            ("DESTROY_FACTION", ["faction wh_main_grn_greenskins", "confederation_valid"]),
            ("DEFEAT_N_ARMIES_OF_FACTION", ["total 30"]),
        ]),
    ],
}

HOUSES = list(ROUTES.keys())

# ---------------------------------------------------------------------------
# The route text (phase 2, 2026-10-11). Every route opens with a paragraph and every ritual
# objective has a one-line explainer above it. mission_string() emits both as SCRIPTED
# objectives sharing LORE_SCRIPT_KEY, and section 9 of the shipped Lua completes them at every
# human turn start. Sources: Lexicanum for Gargath, Balur, Vraznak, the Black Dwarf, Snakebeard,
# Abnagg, Tordrek and Ghorth; the mod's own skill lines for Urzkhal, Bzaark, Azeros, Kharkadon
# and the Captain. Spec: docs/superpowers/specs/2026-10-11-victory-routes-vco-parity-phase2-
# design.md, section 4. A paragraph states the house's aim, never the objectives or their
# numbers, and a map-gated route's paragraph reads true on both halves.
# ---------------------------------------------------------------------------
LORE_SCRIPT_KEY = "derpy_route_lore"
# Set by the shipped Lua when it issues routes that carry the lines. A save from before
# 2026-10-11 never has it, so its routes, which carry no such line, never see the call.
LORE_SAVED_KEY = "derpy_route_lore_v1"

# One paragraph per route, keyed by victory_types key. A gated route's halves share it.
LORE = {
    # House of Khorakk: Urzkhal the Chainlord (skill line only)
    "derpy_victory_type_house_of_khorakk_1_ledger_of_flesh": (
        "Urzkhal the Chainlord never sees a slave, only a column in his ledger, and he reads "
        "that column better than any Sorcerer-Prophet reads the flames. The House of Khorakk "
        "counts its worth in hands at work. When the ledger shows more of them than any other "
        "house can field, the Conclave will have to buy its labour from him."),
    "derpy_victory_type_house_of_khorakk_2_chains_of_domination": (
        "Every chain in the Thrall District leads back to a house that holds it, and Urzkhal "
        "wants every one of them to lead back to Khorakk. The other slave-masters of the Tower "
        "work their gangs at a profit he could double. Once he holds their seats, the Conclave "
        "will have to bargain with him for every labourer in Zharr-Naggrund."),
    "derpy_victory_type_house_of_khorakk_3_the_collection": (
        "Urzkhal keeps an account for the greenskins, and in his ledger they are a debt. The "
        "House of Khorakk collects that debt in the only coin a greenskin has, which is its own "
        "body in chains. He has done the arithmetic and it favours the anvil. The account "
        "closes when there is no tribe left to pay it."),

    # House of Baal: Gargath (Lexicanum, WD 203)
    "derpy_victory_type_house_of_baal_1_bind_the_kdaai": (
        "The House of Baal has given Zharr-Naggrund great generals and mighty sorcerers for "
        "millennia, and Gargath means to be remembered as both. His art is binding fire-daemons "
        "into iron shells, with a Daemonsmith's precision and a sorcerer's will. A host of K'daai "
        "marching under the banner of Baal would show the Conclave whose command Hashut's fire "
        "obeys."),
    "derpy_victory_type_house_of_baal_2_the_iron_cages": (
        "Baal is one of the old bloodlines of the Tower, and Gargath intends it to be the first "
        "of them. The other houses of the Bloodline District hold seats he wants for Baal. He "
        "will cage them as he cages daemons, in iron and under his own seal, and the Tower's "
        "furnace will burn in Baal's name."),
    "derpy_victory_type_house_of_baal_3_stoke_the_furnace": (
        "Hashut's fire must be fed. The lords of Baal have always fed it with slaves and "
        "sacrifices taken in war, and Gargath seeks the Father of Darkness's favour with "
        "sacrifices of his own before he makes war. The Dwarf holds of the west are the oldest "
        "prize there is. Every one that burns stokes the furnace higher."),

    # Fists of Hashut: Balur (Lexicanum, Gargath's entry, WD 203; the author's melee warlord)
    "derpy_victory_type_fists_of_hashut_1_the_unholy_legion": (
        "\"We shall be known as the Fists of Hashut. Let the world tremble at our name.\" "
        "Gargath said it when he named the host, and his brother Balur has never let the words "
        "go. The Fists marched first as axemen in heavy armour with the Bull Centaurs of the "
        "Tower beside them. Balur will field that host again, larger than before."),
    "derpy_victory_type_fists_of_hashut_2_the_black_altar": (
        "Balur is a warlord second and a zealot first. Gargath binds daemons for the house; "
        "Balur kneels at the Black Altar and carries its word into the legion until fear has "
        "no purchase on any of them. A temple of Hashut raised in the Tower, with the Bloodline "
        "seats beside it in the Fists' hands, would set the brothers' faith before the whole "
        "Conclave."),
    "derpy_victory_type_fists_of_hashut_3_break_the_throng": (
        "The Fists of Hashut first marched to take slaves and sacrifices from the lesser races, "
        "and no race fights harder to keep its own than the Dwarfs of the west. Balur prefers it "
        "that way. His legion goes in behind him and does not stop for wounds or for broken "
        "lines until the throng in front of it is gone."),

    # Horns of Hashut: Vraznak (Lexicanum, WD 170; a Centaur lord in this mod)
    "derpy_victory_type_horns_of_hashut_1_the_herd_of_hashut": (
        "Vraznak's bond with the beasts of Hashut is the strength of his house. The Horns take "
        "their name from the herd, and Vraznak judges a lord of Zharr-Naggrund by the bulls he "
        "can put in the field. He wants a herd larger than any the Dark Lands have seen, and "
        "nothing left standing in front of its charge."),
    "derpy_victory_type_horns_of_hashut_2_hide_of_the_iron_bull": (
        "Vraznak drives his herd through the slag pits until the ash cakes hard over every "
        "hide, and he has led them through that fire himself. The Bloodline District of the "
        "Tower is full of lords who have never done either. He will take their seats and "
        "stand in the Conclave as the veteran none of them can match."),
    "derpy_victory_type_horns_of_hashut_3_the_stampede": (
        "Centuries ago a Sorcerer Lord was murdered in the Temple of Hashut itself, and the "
        "raid that answers it is a tradition. Vraznak crosses the Blasted Waste with oil and "
        "tar, sets a fire the enemy cannot ignore, and carries skulls home for the Temple. "
        "\"Patience,\" he says. \"They are coming. We shall taste their blood soon.\""),

    # Slaves of the Black Dwarf (Lexicanum, WD 201)
    "derpy_victory_type_slaves_of_the_black_dwarf_1_the_unbreached_wall": (
        "The Black Dwarf's plan is a long one. Sack Praag and Salzenmund, then seize the "
        "passes into the western Old World and hold the trade roads from Cathay and Ind in his "
        "own hand. Whoever controls those roads takes a share of every caravan that uses them, "
        "and the Black Dwarf intends that share to be his."),
    "derpy_victory_type_slaves_of_the_black_dwarf_2_chains_of_the_conclave": (
        "Every victory on the road west serves one end: a place on the Grand Council of the "
        "Sorcerer Lords of Zharr-Naggrund. The Black Dwarf will not wait to be invited. The "
        "Thrall District's seats belong to houses that live on slaves he could take from them, "
        "and once he holds those seats the Council will have to make room."),
    "derpy_victory_type_slaves_of_the_black_dwarf_3_the_slave_harvest": (
        "\"One hundred slaves are to be immersed in molten gold in the name of Hashut the "
        "Father of Darkness,\" the Black Dwarf told his captain Barukh. Offerings like that "
        "need stock, and his house is named for its slaves. The greenskin tribes are the stock "
        "he will draw on, until there is no tribe left to run from his chains."),
    "derpy_victory_type_slaves_of_the_black_dwarf_4_the_granite_legion": (
        "Shields locked, spears set, every plate double-struck at his own order: the Granite "
        "Legion is the Black Dwarf's answer to anyone who thinks a Chaos Dwarf line can be "
        "broken. Arrows break on it and the line does not move. Kitting a legion to that "
        "standard is not cheap, and he pays the cost without complaint."),
    "derpy_victory_type_slaves_of_the_black_dwarf_5_wrought_of_living_stone": (
        "The Black Dwarf was already feeling the Sorcerer's Curse when he fought General Borri's "
        "Dwarfs at Black Skull Mountain. The stone has taken his left side since then, and he "
        "has stopped resisting it. Blades turn on him and shot glances away, and the armies "
        "thrown against him break long before he does."),

    # House of Bzaark: Bzaark Firespitter (skill line only)
    "derpy_victory_type_house_of_bzaark_1_proof_by_fire": (
        "Bzaark Firespitter packs his shells by his own hand and to no known standard. They fly "
        "wide, and where they land nothing is left standing. The other houses call it madness. "
        "Bzaark calls it testing, and he will keep testing until every battery in the Dark "
        "Lands fires a design of his."),
    "derpy_victory_type_house_of_bzaark_2_the_proven_pattern": (
        "One design in a hundred survives Bzaark's own testing, and that one is stamped, copied "
        "and issued to every battery the house fields. A seat in the Forge District would put "
        "the Tower's foundries to work on it as well, with armaments enough to build it at a "
        "scale even Bzaark has not yet tried."),
    "derpy_victory_type_house_of_bzaark_3_firespitters_prototype": (
        "Bzaark strips his guns to the frame and rebuilds them to a design only he can read. "
        "What comes off the bench hits like nothing else in the Dark Lands and cannot be aimed. "
        "The Dwarf holds of the west have some of the thickest walls in the world, which makes "
        "them the best place to find out what it can do."),

    # Snakebeard's Artificers: Thymbrin Snakebeard (Lexicanum, WD 103)
    "derpy_victory_type_snakebeards_artificers_1_deathshrieker_doctrine": (
        "\"Simple but effective,\" Thymbrin Snakebeard says of the Whirlwind and the "
        "Tenderiser: get them going fast and they carve big, ragged holes in the enemy's ranks. "
        "He is working on a number of other ideas, of course. Every one of them needs a forge to "
        "build it and armaments to feed it, and he will have both."),
    "derpy_victory_type_snakebeards_artificers_2_the_iron_road": (
        "Thymbrin keeps a snake in his beard, and keeps it well fed so it will not strangle "
        "him in his sleep. He looks after his engines with the same care. Every one in the "
        "train is stripped and rebuilt until it can take a cannonball and keep rolling, and a "
        "seat in the Forge District would put the Tower's foundries on his schedule too."),
    "derpy_victory_type_snakebeards_artificers_3_masterwork_artillery": (
        "Thymbrin will not call a war machine finished until it has been tried against the "
        "hardest target there is, and nothing is harder than a Dwarf hold. The Dwarf engineers "
        "think themselves the masters of the craft. He bred Boar Centaurs to push his machines "
        "into battle, and next he will push them through Dwarf gates."),

    # House of Azeros: Azeros the Iron (skill line only)
    "derpy_victory_type_house_of_azeros_1_ten_thousand_hammers": (
        "Azeros the Iron throws open every furnace in his house and works the slave gangs in "
        "shifts until they drop. Ore goes in at one end and plate comes out at the other, and "
        "the house with the most furnaces decides what Zharr-Naggrund can arm. Azeros means "
        "every hammer in the Dark Lands to strike to his count."),
    "derpy_victory_type_house_of_azeros_2_the_masters_mark": (
        "Nothing leaves the House of Azeros without his own sigil struck into the plate, and he "
        "wants that mark on the Forge District too. Bzaark's foundries and Snakebeard's "
        "workshops sit beside his in the Tower. Azeros sees no reason a district built to make "
        "iron should answer to anyone but the house that makes it best."),
    "derpy_victory_type_house_of_azeros_3_the_great_refinery": (
        "The House of Azeros puts industry before war, but industry eats slaves faster than the "
        "pens can fill. The greenskin tribes are the nearest supply and the largest. Azeros "
        "will march for them, and every tribe he breaks goes to the furnaces, until there are "
        "no tribes left to break."),

    # Warfleet of Uzkulak: Abnagg Hellbeard (Lexicanum, Plague Fleet)
    "derpy_victory_type_warfleet_of_uzkulak_1_tyrant_of_the_waves": (
        "Abnagg Hellbeard sailed with the largest fleet ever to leave the lands of the Chaos "
        "Dwarfs, and in its first two months it left shattered cities along the coast of the "
        "Southlands. The Warfleet of Uzkulak still lives that way. Every coast is a market to "
        "the Hellbeard, and he sets the prices with his guns."),
    "derpy_victory_type_warfleet_of_uzkulak_2_the_hellbeard_ashore": (
        "The Thrall District of the Tower is where the harvest of the coasts is counted. "
        "Abnagg's house sits there beside Khorakk's slave-drivers, the Black Dwarf's chains and "
        "the Black Kraken's raiders, and he would rather they all answered to him. Then the "
        "Conclave would deal with the Hellbeard directly, at the Hellbeard's price."),
    "derpy_victory_type_warfleet_of_uzkulak_3_siege_mastermind": (
        "Abnagg swore never to return to Zharr-Naggrund without the foundation stone of the Elf "
        "citadel that had blockaded his people for so long. The Fortress of Dawn held against "
        "him for years while his fleet burned its cliff-tops to a blackened waste. He has not "
        "given up the oath, and anything between him and that stone is in his way."),
    "derpy_victory_type_warfleet_of_uzkulak_4_infernal_artillery": (
        "When the High Elf fleet broke his line at the Fortress of Dawn, Abnagg reformed his "
        "ships into a great circle of iron with the bombardment ships at its centre, and the "
        "guns drove the Elves back into their harbour. He has trusted his artillery above "
        "everything since. Ashore or afloat, the Hellbeard wants more guns."),
    "derpy_victory_type_warfleet_of_uzkulak_5_fleetmasters_command": (
        "On the Southlands coast his fleet left ziggurats raised by enslaved survivors, who were "
        "then walled up inside them. Abnagg knows what a fleet is for. It brings slaves home to "
        "the forges of Zharr-Naggrund, and every ship he adds to it adds to his share of the "
        "trade that keeps those forges burning."),

    # Black Kraken Armada: Tordrek Hackhart (Lexicanum, Dreadfleet)
    "derpy_victory_type_black_kraken_armada_1_crew_of_the_drowned": (
        "Not every hand aboard the Black Kraken is still breathing, and Tordrek Hackhart has "
        "stopped counting which. The Kraken breaks surface off a coast that thought itself "
        "safe, and his crew are gone with the plunder before a relief column forms. Tordrek has "
        "raided this way since Barak Varr banished him, and he grows better at it."),
    "derpy_victory_type_black_kraken_armada_2_daemonpact_of_the_deep": (
        "Tordrek reached Zhugulzar a banished Dwarf with nothing but his own submersible. The "
        "fever-dreams that drove him there were never dreams, and the bargain he began in "
        "Barak Varr is nearly finished. A seat in the Tower's Thrall District would make the "
        "outcast a lord of Zharr-Naggrund, and he means to sit in it."),
    "derpy_victory_type_black_kraken_armada_3_rivalrys_wrath": (
        "Tordrek was the master of submersible engineering in Barak Varr, and for decades he "
        "watched the accolades go to Red Brokk Gunnarsson instead. One day in the shipyard he "
        "accidentally shot Brokk a dozen times with a rivet claw, and somehow failed to kill "
        "him. Barak Varr banished him for it. He has planned his return ever since."),

    # The Conclave: Ghorth the Cruel (Lexicanum)
    "derpy_victory_type_conclave_1_the_blackening": (
        "Ghorth the Cruel is the most potent of the Sorcerer Lords of Zharr-Naggrund, and the "
        "petrification that takes them all has nearly finished with him. Half-statue, half-god, "
        "he means to stand at the summit of the Tower and speak with Hashut's voice. The "
        "highest seats of sorcery and a temple to the Father of Darkness are the last steps up."),
    "derpy_victory_type_conclave_2_the_seat_of_zharr": (
        "Ghorth already sits at the top of the Tower. What he wants now is a Conclave that no "
        "longer debates his edicts, where vassals march at his summons and the old houses do "
        "as they are told. That means seats in the Bloodline and Thrall Districts held by his "
        "own people, and the influence to keep them there."),
    "derpy_victory_type_conclave_3_hashuts_ledger": (
        "\"I, Supreme Lord Ghorth, do not suffer failures gladly,\" he told the young Gargath of "
        "Baal, and he holds the enemies of Zharr-Naggrund to the same rule. He has written two "
        "names in Hashut's ledger, the Dwarfs and the greenskins. Ghorth will close the "
        "account on both of them."),
    "derpy_victory_type_conclave_4_the_conclaves_writ": (
        "Ghorth rules Zharr-Naggrund through fear, and that takes soldiers. His chief servant, "
        "Zhatan the Black, commands the Tower in his name, and the tribute halls and the "
        "temple guard are his to raise. Ghorth grants the Bull Centaurs of the Tower as an "
        "honour, and he intends to have plenty to grant."),
    "derpy_victory_type_conclave_5_the_tribute_of_slaves": (
        "\"You must return with an abundance of slaves and sacrifices before the sun has passed "
        "the tower of Hashut ninety times,\" Ghorth told Gargath of Baal. The whole Conclave "
        "runs on that tribute: slaves in, war material out. Ghorth will collect more of it "
        "than any Sorcerer Lord before him."),

    # Overlords of Zharrduk: Kharkadon the Vicious (skill line only)
    "derpy_victory_type_minor_faction_1_immortal_legions": (
        "The Overlords of Zharrduk put the Infernal Guard and the Ironsworn first in everything. "
        "They eat, train and draw their pay before the rabble, and they wear the best plate in "
        "Zharrduk. Kharkadon the Vicious expects them to earn it, and he wants enough of these "
        "Immortals to fill legions, whatever keeping them costs the house."),
    "derpy_victory_type_minor_faction_2_lords_of_zharrduk": (
        "Every officer in Kharkadon's court has served in the field, and their orders carry the "
        "weight of it. The Bloodline District of the Tower is full of lords who have not. "
        "Kharkadon intends to take their seats and fill them with veterans of his own, and to "
        "give the Conclave an Overlord who led from the first rank."),
    "derpy_victory_type_minor_faction_3_blood_and_iron": (
        "Kharkadon makes an example of his enemies, and the hobgoblins and labourers of "
        "Zharrduk know their turn may come. Wherever revolt rises against the Overlords, and "
        "wherever a Dwarf army stands in the way, he answers it the same way: in the first "
        "rank, splitting armour and the dwarf beneath it with one stroke."),
    "derpy_victory_type_minor_faction_4_the_extinction": (
        "Some enemies can be chained and put to work. Kharkadon has decided that the greenskins "
        "and the Dwarfs are not among them. The Overlords will take neither their surrender nor "
        "their tribute, and Kharkadon will call Zharrduk safe when both are gone from the "
        "world, and not before."),

    # Uzkul Mingol Company: the Captain (skill line only)
    "derpy_victory_type_skullstack_1_spoils_of_ind": (
        "The temples of Ind are full of gold, and the Uzkul Mingol Company is full of people who "
        "know it. The Captain pays by the town sacked and the hoard taken, and the hobgoblins "
        "in the column fight for exactly that. The Charter names the Company's share of "
        "everything it finds, and the Captain means for there to be a great deal to find."),
    "derpy_victory_type_skullstack_2_the_company_charter": (
        "The Company's factors sit in every market from Ind to the Dark Lands, taking their cut, "
        "and its prospectors send every seam they find to the forges. The houses of the Forge "
        "District are its best customers. The Captain would rather own them than sell to them, "
        "and nothing in the Charter forbids it."),
    "derpy_victory_type_skullstack_3_the_long_march": (
        "An expedition that stops is an expedition that starves. The Company's road runs from "
        "the Dark Lands to the markets of Ind, and anything that stands across it is in the "
        "way, the greenskins first. No one rises to lead the Company by being merciful, or "
        "slow, and the Captain is neither."),
}

# One line per ritual category, drawn directly above every PERFORM_RITUAL of that
# category. The names are CA's own ritual_categories loc.
EXPLAIN = {
    "DISTRICTS_ANNEX_T5_A": (
        "At the Tower of Zharr. Each Bloodline District seat you claim brings its house into "
        "yours, or sends you its lord if that house is not in this campaign."),
    "DISTRICTS_ANNEX_T5_B": (
        "At the Tower of Zharr. Each Thrall District seat you claim brings its house into "
        "yours, or sends you its lord if that house is not in this campaign."),
    "DISTRICTS_ANNEX_T5_C": (
        "At the Tower of Zharr. Each Forge District seat you claim brings its house into "
        "yours, or sends you its lord if that house is not in this campaign."),
    "DISTRICTS_SORCERY_T3": (
        "At the Tower of Zharr. Claim the seats at the top of the Sorcery District."),
    "HELLFORGE_CAPS_BULL_CENTAURS": (
        "At the Hell-Forge. Each Bull Centaurs ritual raises how many Bull Centaurs you may "
        "field."),
    "HELLFORGE_CAPS_KDAAI": (
        "At the Hell-Forge. Each K'daai ritual raises how many of one kind you may field: "
        "K'daai Fireborn or K'daai Destroyers."),
    "HELLFORGE_CAPS_MELEE_INFANTRY": (
        "At the Hell-Forge. Each Melee Infantry ritual raises how many of one unit you may "
        "field: Chaos Dwarf Warriors, Infernal Guard or Infernal Ironsworn."),
    "HELLFORGE_CAPS_WARMACHINES": (
        "At the Hell-Forge. Each War Machines ritual raises how many Hellcannons or other war "
        "machines you may field."),
}

# Words players read as internals (memory: player-text-plain-words), matched as whole words.
# AI and HUD only in capitals: the lower-case forms are ordinary English.
JARGON = {"cap", "caps", "accrue", "accrues", "rep", "ratchet", "gated", "agent", "agents"}
JARGON_EXACT = {"AI", "HUD"}
LORE_WORDS = (40, 70)
EXPLAIN_WORDS = (1, 30)


def lore_loc_key(vt):
    """The loc key a route's paragraph line reads its text from."""
    return "mission_text_text_derpy_route_lore_" + vt[len("derpy_victory_type_"):]


def explain_loc_key(category):
    """The loc key a ritual category's explainer line reads its text from."""
    return "mission_text_text_derpy_route_explain_" + category.lower()


def text_findings(where, text, words=None):
    """The player-text rules of spec section 4.1, as finding strings."""
    out = []
    if not text or any(not (32 <= ord(ch) < 127) for ch in text):
        out.append("%s: not printable ASCII (a dash, a curly quote, an emoji or a tab?)" % where)
    if " - " in text or "--" in text:
        out.append("%s: a hyphen used as a dash" % where)
    if "[[" in text:
        out.append("%s: [[ markup, which this phase does not use" % where)
    for w in re.findall(r"[A-Za-z]+", text):
        if w.lower() in JARGON or w in JARGON_EXACT:
            out.append("%s: jargon word %r" % (where, w))
    n = len(text.split())
    if words and not (words[0] <= n <= words[1]):
        out.append("%s: %d words, want %d to %d" % (where, n, words[0], words[1]))
    return out


def ritual_categories_used():
    """Every ritual category a PERFORM_RITUAL objective names, in a base or a gated list."""
    cats = set()
    for f in HOUSES:
        for i in range(len(ROUTES[f])):
            _slug, _name, objectives, variant = route_parts(f, i)
            for objs in [objectives] + ([variant[1]] if variant else []):
                for otype, conds in objs:
                    if otype == "PERFORM_RITUAL":
                        cats.update(c.split(" ", 1)[1] for c in conds
                                    if c.startswith("ritual_category "))
    return cats


def block_text_findings(faction, idx, block, loc_keys):
    """What one emitted route block must carry (spec section 5), read off the block itself so
    it checks what ships rather than what the emitter meant: the paragraph line first, an
    explainer directly above every ritual, no other SCRIPTED line, and loc behind each."""
    where = "%s route %d" % (faction, idx + 1)
    parsed = []
    for body in re.findall(r"\bobjective\s*\{(.*?)\}", block, re.S):
        stmts = [s.strip() for s in body.split(";") if s.strip()]
        otype = next((s.split(" ", 1)[1] for s in stmts if s.startswith("type ")), None)
        parsed.append((otype, stmts))
    out = []
    lore = "override_text %s" % lore_loc_key(victory_type_key(faction, idx))
    if not parsed or parsed[0][0] != "SCRIPTED" or lore not in parsed[0][1]:
        out.append("%s: the first objective is not its paragraph line" % where)
    for j, (otype, stmts) in enumerate(parsed):
        if otype == "SCRIPTED":
            if "script_key %s" % LORE_SCRIPT_KEY not in stmts:
                out.append("%s: a SCRIPTED line nothing completes" % where)
            texts = [s.split(" ", 1)[1] for s in stmts if s.startswith("override_text ")]
            if len(texts) != 1 or texts[0] not in loc_keys:
                out.append("%s: a SCRIPTED line with no loc row behind it" % where)
            if j and (j + 1 >= len(parsed) or parsed[j + 1][0] != "PERFORM_RITUAL"):
                out.append("%s: a SCRIPTED line that is neither its paragraph nor above a "
                           "ritual" % where)
        if otype == "PERFORM_RITUAL":
            cat = next((s.split(" ", 1)[1] for s in stmts if s.startswith("ritual_category ")),
                       None)
            above = parsed[j - 1] if j else (None, [])
            if above[0] != "SCRIPTED" or (
                    "override_text %s" % explain_loc_key(cat or "")) not in above[1]:
                out.append("%s: ritual %s has no explainer directly above it" % (where, cat))
    return out

# ---------------------------------------------------------------------------
# QUESTS - ordinary faction missions, not victory conditions.
#
# Same machinery, three differences: no `victory_type` line (that is the whole of what makes
# a mission a victory condition), no `game_victory` in the payload, and the payload is the
# point rather than a consolation for a player who keeps going after the victory screen.
#
# The string route is used for the same reason the routes use it: a mod-authored `missions`
# row carries no objective parameters and no reward without
# `cdir_events_mission_option_junctions`, `_payloads` and `_issuer_junctions`, and HLL ships
# none of those three - which is why its eleven existing mission rows do nothing
# (HOUSE_MISSION_OPTIONS_20260903.md section 2.1). A mission string carries its objectives
# and its payload itself, and was measured end to end on 2026-09-03: issued, rendered,
# evaluated, completed, and `money 2500` paid exactly (MISSIONS.md section 12).
#
# `region` gates the whole quest rather than choosing a variant: there is nothing to capture
# on a map without the region, so on the Old World maps it is simply never issued.
def _take_quest(key, title, description, completed, gate, targets, payload):
    """A quest whose objectives are "sack OR occupy <city>" - one SCRIPTED objective per city.

    No objective type counts both: RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING counts a sack
    or a raze, OWN_N_REGIONS_INCLUDING / CAPTURE_REGIONS an occupation. So each city is a
    SCRIPTED objective, and the shipped Lua's TAKE listeners complete it on
    CharacterSackedSettlement (a sack) or RegionFactionChangeEvent (the city now belongs to the
    faction - which covers every culture's own occupy variant without naming any of them).

    `targets` is [(slug, region key, objective text)]. The script key is the quest key plus the
    slug, so two copies of one quest on two maps never share a loc key."""
    take = {}
    objectives = []
    for slug, region, text in targets:
        script_key = "%s_%s" % (key, slug)
        take[script_key] = (region, text)
        objectives.append(("SCRIPTED", ["script_key %s" % script_key,
                                        "override_text mission_text_text_%s" % script_key]))
    return {"key": key, "title": title, "description": description, "completed": completed,
            "region": gate, "objectives": objectives, "take": take, "payload": payload}


# The Black Dwarf's own plan (White Dwarf 201, "Furnace of Hashut"): sack Praag and Salzenmund
# and take his place on the Grand Council of the Sorcerer Lords. One quest per map namespace,
# each gated on its own Praag, so exactly one is issued wherever both cities exist.
_ROAD_TO_PRAAG = dict(
    title="The Road to Praag",
    description=("Praag and Salzenmund stand between Zharr-Naggrund and the passes west, and the "
                 "trade of Cathay and Ind runs through them. Sack them or hold them, and the "
                 "Grand Council of the Sorcerer Lords will have to make room."),
    completed="Praag and Salzenmund have paid their tithe to Hashut.",
    payload=[(MONEY, 20000), ("wh3_dlc23_chd_conclave_influence", 150)],
)

QUESTS = {
    "cr_chd_slaves_of_the_black_dwarf": [
        _take_quest("derpy_mis_black_dwarf_road_to_praag_ie", gate="wh3_main_combi_region_praag",
                    targets=[("praag", "wh3_main_combi_region_praag", "Sack or occupy Praag"),
                             ("salzenmund", "wh3_main_combi_region_salzenmund",
                              "Sack or occupy Salzenmund")],
                    **_ROAD_TO_PRAAG),
        _take_quest("derpy_mis_black_dwarf_road_to_praag_tow", gate="cr_oldworld_region_praag",
                    targets=[("praag", "cr_oldworld_region_praag", "Sack or occupy Praag"),
                             ("salzenmund", "cr_oldworld_region_salzenmund",
                              "Sack or occupy Salzenmund")],
                    **_ROAD_TO_PRAAG),
    ],
    # Vraznak's raid of 2497 (White Dwarf 170, "The Battle of Skull River"), led with his
    # kinsman the Sorcerer Lord Zochaz in revenge for a Sorcerer Lord murdered in the Temple of
    # Hashut. Old World only: Athel Loren's Oak of Ages is the gate, so there is no Zochaz in
    # the Dark Lands. `grant` is what success does beyond the payload - the shipped Lua puts
    # the lord in the faction's recruit pool (tools/gen_zochaz.py builds him).
    "cr_chd_horns_of_hashut": [
        {
            "key": "derpy_mis_vraznak_kinsmans_raid",
            "title": "The Kinsman's Raid",
            "description": ("A Sorcerer Lord was murdered in the Temple of Hashut, and the "
                            "Temple has not forgotten who did it. Carry the vengeance into the "
                            "forest of the elves with your kinsman Zochaz, burn it, and bring "
                            "home the skulls."),
            "completed": "The forest burned, and Zochaz rides with the Horns of Hashut.",
            "region": "cr_oldworld_region_the_oak_of_ages",
            "objectives": [
                ("DEFEAT_N_ARMIES_OF_FACTION",
                 ["subculture wh_dlc05_sc_wef_wood_elves", "total 8"]),
                ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS", ["total 5"]),
            ],
            "payload": [(MONEY, 10000)],
            "grant": {"subtype": "derpy_zochaz", "name": "names_name_12412537"},
        },
    ],
    "cr_chd_warfleet_of_uzkulak": [
        {
            "key": "derpy_mis_abnagg_dawns_harbour",
            "title": "Dawn's Harbour",
            "description": ("The elves of the Fortress of Dawn keep the southern lanes and "
                            "hang slavers from their own yardarms. Take the harbour, and the "
                            "lanes are ours to tax - and Gordak Seascourge will bring his "
                            "ships to the Labourfleet."),
            "completed": "Dawn's Harbour answers to Uzkulak, and Gordak Seascourge sails "
                         "with the Labourfleet.",
            "region": "wh3_main_combi_region_fortress_of_dawn",
            "objectives": [
                ("OWN_N_REGIONS_INCLUDING",
                 ["region wh3_main_combi_region_fortress_of_dawn", "total 1"]),
            ],
            # The plunder of a trade port, and its cargo. The lasting reward is the landmark
            # itself - `wh3_dlc23_special_fortress_of_dawn_dawns_harbour_chd`, +500 sea-trade
            # GDP and +5 post-battle labour at level 3 - which arrives with the region and
            # needs nothing from this payload.
            "payload": [(MONEY, 15000), ("wh3_dlc23_chd_raw_materials", 2500)],
            # Gordak's trait is "Labourfleet", this house's name, so he is this house's alone
            # - and with the harbour, IE and IEE only. Replaces temp_spawn_pool_chd_oldworld.lua.
            "grant": {"subtype": "derpy_gordak", "name": "names_name_12412533", "rank": 10},
        },
    ],
}

# Quests keyed by CULTURE instead of a house: issued to every human Chaos Dwarf faction,
# CA's three included. Their grant matches on the culture too.
CULTURE = "wh3_dlc23_chd_chaos_dwarfs"

# Warrhak Skullcrusher, faction-less like Zochaz. Replaces temp_spawn_pool_chd_oldworld.lua,
# which handed him (and Gordak) to the player on turn one. `rank` is the level he arrives at:
# spawn_character_to_pool has no rank argument (its 50 is his AGE), so the shipped Lua raises
# him with cm:add_agent_experience(..., rank, true) the first time he is recruited.
_SILVERSPEAR = dict(
    title="The Silver Mountain",
    description=("Mount Silverspear is a fortress of the greenskins, and the silver in its roots "
                 "has never paid tithe to Hashut. Take the mountain, and Warrhak Skullcrusher, "
                 "breaker of runes, will answer the summons."),
    completed="Mount Silverspear is ours. Warrhak Skullcrusher awaits your command.",
    payload=[("wh3_dlc23_chd_raw_materials", 2000)],
    grant={"subtype": "derpy_warrhak", "name": "names_name_12412534", "rank": 10},
)
QUESTS[CULTURE] = [
    dict(key="derpy_mis_warrhak_silverspear_ie", region="wh3_main_combi_region_mount_silverspear",
         objectives=[("OWN_N_REGIONS_INCLUDING",
                      ["region wh3_main_combi_region_mount_silverspear", "total 1"])],
         **_SILVERSPEAR),
    dict(key="derpy_mis_warrhak_silverspear_tow", region="cr_oldworld_region_mount_silverspear",
         objectives=[("OWN_N_REGIONS_INCLUDING",
                      ["region cr_oldworld_region_mount_silverspear", "total 1"])],
         **_SILVERSPEAR),
]


# A house whose lord comes to whoever CONFEDERATES it: the faction that absorbs the house gets
# the same lord its quest grants. Abnagg's quest is only ever issued to a human, and a human is
# never confederated in single player, so the absorbed house cannot already have Gordak.
# The saved-value prefix a lord's recruit-time rank waits under. zz_derpy_toz_annex.lua builds the
# same key for the Tower's plain-IE Gordak, and check() holds it to this.
RANK_KEY_PREFIX = "derpy_grant_rank_"

CONFED_GRANT = {
    "cr_chd_warfleet_of_uzkulak": QUESTS["cr_chd_warfleet_of_uzkulak"][0]["grant"],
}


def all_quests():
    """[(faction or CULTURE, quest)] in emission order."""
    return [(f, q) for f in HOUSES + [CULTURE] for q in QUESTS.get(f, ())]


def n_take_objectives():
    """How many sack-or-occupy objectives the quests declare - one loc line each."""
    return sum(len(q.get("take", {})) for _f, q in all_quests())

# The mission slot rows. One per route INDEX, shared by every house, so a house's routes are
# that many distinct (faction, mission_key) pairs rather than several missions fighting over
# one key. A house with three routes uses slots 1-3 and never sees 4 and 5; the two extra
# rows cost nothing when unused.
SLOT_KEYS = ["derpy_route_victory_1", "derpy_route_victory_2", "derpy_route_victory_3",
             "derpy_route_victory_4", "derpy_route_victory_5"]
SLOT_TITLES = ["Route I", "Route II", "Route III", "Route IV", "Route V"]
# CA's own icons, reused by name so this ships no art at all. Vanilla victory_types rows use
# the bare filenames `short`, `long`, `ultimate`, `domination` and nothing else - and reuse
# them freely, `short` on 7 of the 18 rows - so repeating `long` at index 4 is vanilla
# practice rather than a shortcut. Indices 0-2 are left alone: they are shared with the
# other ten houses, where they mean craft / Tower / war.
SLOT_ICONS = ["short", "long", "ultimate", "domination", "long"]
# tree_y is the route index. Vanilla's own wh3_combi_* set runs tree_y 0..4, so five nodes in
# one victory tree is attested.

COMPLETED_TEXT = "Success! You have achieved one of your goals."
# The missions row's three localised fields are read from loc, not from the DB column
# (`wh3-mission-title-is-loc-driven`), and this pack shipped none - so every route drew a
# blank title. Written per slot because a slot is shared by every house; the route's own
# name lives on the victory_types node instead.
MISSION_DESC = ("One of the paths to victory open to your house. "
                "Completing any single route wins the campaign.")

# The most objectives of ONE type CA puts in a single victory objective set, counted across
# all 5,472 lines of victory_objectives.lua: 2, reached by both PERFORM_RITUAL and
# CONTROL_N_REGIONS_FROM. Repeating a type is therefore attested and three of one is not, so
# check() caps it here. Multi-target DESTROY_FACTION is not an exception to look for - both
# CA and VCO write that as ONE objective with a `faction` line per target.
MAX_SAME_TYPE_PER_ROUTE = 2


def victory_type_key(faction, idx):
    return "derpy_victory_type_%s_%d_%s" % (
        faction.replace("cr_chd_", "").replace("wh3_dlc23_chd_", ""),
        idx + 1, ROUTES[faction][idx][0])


# ---------------------------------------------------------------------------
# Emitters
# ---------------------------------------------------------------------------

def route_parts(faction, idx):
    """(slug, display name, base objectives, variant) - variant is None, or the
    (region key, objectives) pair a map-gated route uses where that region exists."""
    r = ROUTES[faction][idx]
    return r[0], r[1], r[2], (r[3] if len(r) > 3 else None)


def _scripted_line(loc_key):
    """One route text line: a SCRIPTED objective in VCO's header shape. Every one carries
    LORE_SCRIPT_KEY, so the shipped Lua's one call per slot completes them all."""
    return ["\t\tobjective", "\t\t{", "\t\t\ttype SCRIPTED;",
            "\t\t\tscript_key %s;" % LORE_SCRIPT_KEY,
            "\t\t\toverride_text %s;" % loc_key, "\t\t}", ""]


def mission_string(faction, idx, objectives=None):
    """One mission block in the missions.txt syntax cm:trigger_custom_mission_from_string
    parses. Indentation is cosmetic; the parser is whitespace-tolerant.

    `objectives` overrides the route's base list, which is how the two halves of a
    map-gated route are emitted from one route definition."""
    slug, name, base_objectives, _variant = route_parts(faction, idx)
    if objectives is None:
        objectives = base_objectives
    lines = ["mission", "{",
             "\tvictory_type %s;" % victory_type_key(faction, idx),
             "\tkey %s;" % SLOT_KEYS[idx],
             "\tissuer CLAN_ELDERS;",
             "\tprimary_objectives_and_payload", "\t{"]
    # The route's paragraph first, and each ritual's explainer directly above it.
    lines += _scripted_line(lore_loc_key(victory_type_key(faction, idx)))
    for otype, conds in objectives:
        if otype == "PERFORM_RITUAL":
            cat = next(c.split(" ", 1)[1] for c in conds if c.startswith("ritual_category "))
            lines += _scripted_line(explain_loc_key(cat))
        lines += ["\t\tobjective", "\t\t{", "\t\t\ttype %s;" % otype]
        if otype in TYPES_NEEDING_FACTION and not any(
                c == "faction" or c.startswith("faction ") for c in conds):
            conds = ["faction %s" % faction] + list(conds)
        for c in conds:
            lines.append("\t\t\t%s;" % c)
        lines += ["\t\t}", ""]
    # game_victory is the payload of last resort: a mission with no payload at all fails to
    # generate. It is NOT what ends the campaign - the victory_type above is. The purse and the
    # trophy beside it are the reward for the route, and they only matter to a player who keeps
    # playing past the victory screen; PoW is the attestation for
    # `faction_pooled_resource_transaction` (19 uses, same four lines in the same order) and for
    # mixing several payload entries in one block.
    lines += payload_lines(route_rewards(faction, idx),
                           trophy=route_reward_item(faction, idx), victory=True)
    lines += ["\t}", "}"]
    return "\n".join(lines)


def payload_lines(rewards, trophy=None, victory=False):
    """The payload block, shared by the victory routes and the quests. `money` is a bare
    statement; a pooled resource takes the four-line transaction PoW writes."""
    lines = ["\t\tpayload", "\t\t{"]
    if victory:
        lines.append("\t\t\tgame_victory;")
    for pool, amount in rewards:
        if pool == MONEY:
            lines.append("\t\t\tmoney %d;" % amount)
            continue
        lines += ["\t\t\tfaction_pooled_resource_transaction", "\t\t\t{",
                  "\t\t\t\tresource %s;" % pool,
                  "\t\t\t\tfactor %s;" % REWARD_FACTOR,
                  "\t\t\t\tamount %d;" % amount,
                  "\t\t\t\tcontext absolute;",
                  "\t\t\t}"]
    if trophy:
        lines += ["\t\t\tadd_ancillary_to_faction_pool", "\t\t\t{",
                  "\t\t\t\tancillary_key %s;" % trophy,
                  "\t\t\t}"]
    lines.append("\t\t}")
    return lines


def quest_string(faction, quest):
    """One ordinary mission block: no victory_type, no game_victory, and its own key."""
    lines = ["mission", "{",
             "\tkey %s;" % quest["key"],
             "\tissuer CLAN_ELDERS;",
             "\tprimary_objectives_and_payload", "\t{"]
    for otype, conds in quest["objectives"]:
        lines += ["\t\tobjective", "\t\t{", "\t\t\ttype %s;" % otype]
        if otype in TYPES_NEEDING_FACTION and not any(
                c == "faction" or c.startswith("faction ") for c in conds):
            conds = ["faction %s" % faction] + list(conds)
        for c in conds:
            lines.append("\t\t\t%s;" % c)
        lines += ["\t\t}", ""]
    lines += payload_lines(quest["payload"])
    lines += ["\t}", "}"]
    return "\n".join(lines)


def build_victory_types_tsv():
    rows = ["victory_type\ttree_y\ttree_x\ticon\tlength_type\tshould_show_end_game_ui",
            "#victory_types_tables;3;db/victory_types_tables/derpy_chd_victory\t\t\t\t\t"]
    for faction in HOUSES:
        for idx in range(len(ROUTES[faction])):
            rows.append("%s\t%d\t0\t%s\tlong\ttrue"
                        % (victory_type_key(faction, idx), idx, SLOT_ICONS[idx]))
    return "\n".join(rows) + "\n"


def build_trophy_info_tsv():
    rows = ["ancillary", "#ancillary_info_tables;0;db/ancillary_info_tables/derpy_chd_victory"]
    rows += [key for key, *_ in TROPHY_ITEMS]
    return "\n".join(rows) + "\n"


def build_trophy_ancillaries_tsv():
    """Field for field a vanilla relic row (e.g. ..._major_relic_of_grungni), bar key, type and
    category - the shape proven to sit in any character's slot with no lock."""
    header = ("key\ttype\tapplies_to\ttransferrable\tunique_to_world\tunique_to_faction\t"
              "precedence\tstart_date\tend_date\tavatar_skill\tavatar_special_ability\t"
              "legendary_item\tmp_exclusive\tis_wife_ancillary\tcategory\tmin_starting_age\t"
              "max_starting_age\tmin_expiry_age\tmax_expiry_age\timmortal\t"
              "provided_bodyguard_unit\tprovided_banner\tuniqueness_score\t"
              "turns_before_swap_allowed\tsubcategory\trandomly_dropped\tcan_be_stolen\t"
              "can_be_destroyed\tfaction_set")
    rows = [header, "#ancillaries_tables;0;db/ancillaries_tables/derpy_chd_victory" + "\t" * 28]
    for key, cat, *_ in TROPHY_ITEMS:
        rows.append("\t".join([
            key, TROPHY_SLOT_TYPE[cat], ".", "true", "false", "false", "1", "0", "9999", "", "",
            "false", "false", "false", cat, "16", "30", "30", "50", "true", "", "", "200", "0",
            "", "false", "false", "false", "all"]))
    return "\n".join(rows) + "\n"


def trophy_effect_rows():
    """(ancillary, effect, scope, value) - the scope always vanilla's own for that effect."""
    from anc_effect_scopes import SCOPE
    return [(key, eff, SCOPE.get(eff), val)
            for key, _c, _n, _f, effects in TROPHY_ITEMS for eff, val in effects]


def build_trophy_effects_tsv():
    rows = ["ancillary\teffect\teffect_scope\tvalue",
            "#ancillary_to_effects_tables;0;db/ancillary_to_effects_tables/derpy_chd_victory\t\t\t"]
    rows += ["%s\t%s\t%s\t%.4f" % r for r in trophy_effect_rows()]
    return "\n".join(rows) + "\n"


def build_missions_tsv():
    header =("key\tmission_type\tlocalised_title\tlocalised_description\tui_image\tui_icon\t"
              "generate\tprioritised\tevent_category\tset_piece_battle\tlocation_x\t"
              "location_y\tquest_mission\tquest_mission_final\ttrigger_radius\t"
              "quest_character\tsticky_by_default\tlocalised_mission_completed_text\t"
              "can_be_manually_cancelled")
    rows = [header, "#missions_tables;0;db/missions_tables/derpy_chd_victory" + "\t" * 18]
    for i, key in enumerate(SLOT_KEYS):
        # Field-for-field VCO's own vco_route_victory row, which is the only shape proven to
        # work with trigger_custom_mission_from_string: SCRIPTED type, VictoryCondition
        # category, generate false so the CDIR never issues it on its own.
        # The DB text is decoration - build_loc_tsv writes the keys the runtime actually
        # reads - but CA writes the English into both, and a row that disagrees with its own
        # loc is a trap for whoever opens the table next.
        rows.append("\t".join([
            key, "SCRIPTED", "Victory " + SLOT_TITLES[i], MISSION_DESC, "chd/hell_forge",
            "event_province_positive.png", "false", "false", "VictoryCondition", "",
            "0", "0", "false", "false", "0.0000", "", "false", COMPLETED_TEXT, "true",
        ]))
    for _faction, q in all_quests():
        # A quest row, shaped like CA's own Chaos Dwarf quests rather than like the victory
        # slots: `event_category Quest`, `quest_mission true`, `chd/generic` art. Read off
        # the 30-odd `wh3_dlc23_chd_*` rows with quest_mission set - every one of them uses
        # exactly these, and every non-battle one leaves location at 0,0.
        #
        # `mission_type` stays SCRIPTED for the same reason the slots do: the string route
        # supplies the real objectives, and SCRIPTED is the column value measured to work
        # with it. `generate false` keeps the CDIR from ever issuing it on its own.
        rows.append("\t".join([
            q["key"], "SCRIPTED", q["title"], q["description"], "chd/generic",
            "rom_event_mission.png", "false", "false", "Quest", "",
            "0", "0", "true", "false", "0.0000", "", "true", q["completed"], "false",
        ]))
    return "\n".join(rows) + "\n"


def build_loc_tsv():
    rows = ["key\ttext\ttooltip", "#Loc;1;text/db/derpy_chd_victory.loc\t\t"]
    for faction in HOUSES:
        for idx in range(len(ROUTES[faction])):
            rows.append("victory_types_display_name_%s\t%s - %s\ttrue"
                        % (victory_type_key(faction, idx), SLOT_TITLES[idx],
                           ROUTES[faction][idx][1]))
    # The route text lines: loc only, like every SCRIPTED objective's text (MISSIONS.md).
    for vt, text in sorted(LORE.items()):
        rows.append("%s\t%s\ttrue" % (lore_loc_key(vt), text))
    for cat, text in sorted(EXPLAIN.items()):
        rows.append("%s\t%s\ttrue" % (explain_loc_key(cat), text))
    # The missions rows' own text. The DB columns are decoration - the runtime reads these
    # three derived keys - so without them every route drew a blank title in the objectives
    # panel, for all eleven houses. They are per SLOT, not per route, because a slot is
    # shared: the route's own name is on its victory_types node above.
    for i, key in enumerate(SLOT_KEYS):
        rows.append("missions_localised_title_%s\tVictory %s\ttrue" % (key, SLOT_TITLES[i]))
        rows.append("missions_localised_description_%s\t%s\ttrue" % (key, MISSION_DESC))
        rows.append("missions_localised_mission_completed_text_%s\t%s\ttrue"
                    % (key, COMPLETED_TEXT))
    # The same three derived keys for each quest - the runtime reads these, not the DB
    # columns, and a missing one is a blank title with nothing in any log.
    for _faction, q in all_quests():
        rows.append("missions_localised_title_%s\t%s\ttrue" % (q["key"], q["title"]))
        rows.append("missions_localised_description_%s\t%s\ttrue"
                    % (q["key"], q["description"]))
        rows.append("missions_localised_mission_completed_text_%s\t%s\ttrue"
                    % (q["key"], q["completed"]))
        # A SCRIPTED objective's line is a pure loc entry named by its override_text - no DB
        # row at all (MISSIONS.md). Missing, the objective draws blank.
        for script_key, (_region, text) in sorted(q.get("take", {}).items()):
            rows.append("mission_text_text_%s\t%s\ttrue" % (script_key, text))
    # The trophies: name and flavour. colour_text is the description; explanation_text is
    # the "how you got it" line and is left empty, as 2,269 vanilla items leave it.
    for key, _cat, name, flavour, _e in TROPHY_ITEMS:
        rows.append("ancillaries_onscreen_name_%s\t%s\ttrue" % (key, name))
        rows.append("ancillaries_colour_text_%s\t%s\ttrue" % (key, flavour))
    return "\n".join(rows) + "\n"


def _lore_lua():
    """Section 9 of the shipped Lua: the listener that completes every route text line."""
    return '''
-- 9. THE ROUTE TEXT. Every route opens with its paragraph and every ritual objective has an
-- explainer above it: SCRIPTED objectives sharing one script key, VCO's vco_dummy header
-- shape. Only cm:complete_scripted_mission_objective completes one, so without this listener
-- no route could be won. It completes them all at every human turn start, as VCO's
-- vco_dummy_missions_check does. Registered on every load: the route lives in the save, the
-- listener does not.
--
-- Only in a game whose routes carry the lines: the issue block sets LORE_SAVED_KEY when it
-- issues them. A save from before 2026-10-11 never has it, and what the call does to a
-- mission that exists without this script key is unmeasured. Every slot is called, not only
-- as many as the house has routes: VCO makes the same call where no mission exists with no
-- harm, and a later build that changes a house's route count then cannot strand a running
-- save's route. No mission_is_active_for_faction guard: it was never measured on a victory
-- mission, and a wrong false would block every route.
local LORE_SCRIPT_KEY = %s
local LORE_SAVED_KEY = %s
local LORE_SLOTS = {%s}

local function derpy_lore_listener()
\tcore:add_listener("derpy_chd_route_lore", "FactionTurnStart",
\t\tfunction(context) return context:faction():is_human() end,
\t\tfunction(context)
\t\t\tlocal ok, err = pcall(function()
\t\t\t\tif not cm:get_saved_value(LORE_SAVED_KEY) then
\t\t\t\t\treturn
\t\t\t\tend

\t\t\t\tlocal faction_key = context:faction():name()

\t\t\t\tfor j = 1, #LORE_SLOTS do
\t\t\t\t\tcm:complete_scripted_mission_objective(faction_key, LORE_SLOTS[j], LORE_SCRIPT_KEY, true)
\t\t\t\tend

\t\t\t\tout("derpy_chd_victory_routes: route text lines completed for " .. faction_key)
\t\t\tend)
\t\t\tif not ok then
\t\t\t\tout("derpy_chd_victory_routes: route text listener failed: " .. tostring(err))
\t\t\tend
\t\tend, true)
end
''' % (_lua_str(LORE_SCRIPT_KEY), _lua_str(LORE_SAVED_KEY),
       ", ".join(_lua_str(k) for k in SLOT_KEYS))


def build_lua():
    parts = ['''-- The Chaos Dwarf victory routes: three alternative victory paths per house.
--
-- GENERATED by tools/gen_victory_routes.py - edit the generator, not this file.
--
-- ONE COPY, NOT FOUR. This lives in script/campaign/mod/, which the engine loads for every
-- campaign - unlike script/campaign/<campaign>/, which loads only for its own and is why
-- the drill chain ships four times. Nearly every objective below is map-agnostic on purpose:
-- no province and no region conditions, because those keys carry the campaign's own prefix
-- and one mission string cannot hold both namespaces.
--
-- The exception is a MAP-GATED route, written as a table rather than a string: it carries a
-- region key and two mission blocks, and derpy_pick asks the map which one applies. The
-- off_map block is always map-agnostic, so the route exists on every map either way.
--
-- Completing ANY ONE of a house's three routes wins the campaign. They are alternatives,
-- not stages.

local ROUTES = {}
''']
    for faction in HOUSES:
        parts.append("ROUTES[%s] = {" % _lua_str(faction))
        for idx in range(len(ROUTES[faction])):
            _slug, name, _objs, variant = route_parts(faction, idx)
            parts.append("\t-- %s" % name)
            if variant is None:
                parts.append("\t[==[\n%s\n\t]==]," % mission_string(faction, idx))
                continue
            # A map-gated route ships both halves and lets the runtime pick - derpy_pick
            # below.
            region, vobjectives = variant
            parts.append("\t{")
            parts.append("\t\tregion = %s," % _lua_gate(region))
            parts.append("\t\ton_map = [==[\n%s\n\t\t]==],"
                         % mission_string(faction, idx, vobjectives))
            parts.append("\t\toff_map = [==[\n%s\n\t\t]==],"
                         % mission_string(faction, idx))
            parts.append("\t},")
        parts.append("}\n")

    # The quests: ordinary missions with ordinary rewards, not victory conditions. Same
    # table shape as a gated route minus the second block - there is nothing to capture on a
    # map without the region, so the quest is not issued there at all.
    parts.append("local QUESTS = {}\n")
    for faction in HOUSES + [CULTURE]:
        if not QUESTS.get(faction):
            continue
        parts.append("QUESTS[%s] = {" % _lua_str(faction))
        for q in QUESTS[faction]:
            parts.append("\t-- %s" % q["title"])
            parts.append("\t{")
            if q.get("region"):
                parts.append("\t\tregion = %s," % _lua_str(q["region"]))
            parts.append("\t\tmission = [==[\n%s\n\t\t]==]," % quest_string(faction, q))
            parts.append("\t},")
        parts.append("}\n")

    # Sack-or-occupy objectives: one row per SCRIPTED objective a quest declares in `take`.
    parts.append("local TAKE = {")
    for faction, q in all_quests():
        for script_key, (region, _text) in sorted(q.get("take", {}).items()):
            parts.append("\t{ faction = %s, mission = %s, script_key = %s, region = %s },"
                         % (_lua_str(faction), _lua_str(q["key"]), _lua_str(script_key),
                            _lua_str(region)))
    parts.append("}\n")

    # Quests whose success puts a lord in the faction's recruit pool.
    parts.append("local GRANT = {")
    for faction, q in all_quests():
        g = q.get("grant")
        if g:
            parts.append("\t{ faction = %s, mission = %s, name = %s, subtype = %s%s },"
                         % (_lua_str(faction), _lua_str(q["key"]), _lua_str(g["name"]),
                            _lua_str(g["subtype"]),
                            ", rank = %d" % g["rank"] if g.get("rank") else ""))
    parts.append("}\n")

    # Houses whose confederation pools a lord for the faction that absorbs them.
    parts.append("local CONFED_GRANT = {")
    for faction, g in sorted(CONFED_GRANT.items()):
        parts.append("\t[%s] = { name = %s, subtype = %s%s },"
                     % (_lua_str(faction), _lua_str(g["name"]), _lua_str(g["subtype"]),
                        ", rank = %d" % g["rank"] if g.get("rank") else ""))
    parts.append("}\n")

    parts.append('''
-- 1. TAKE CA'S VICTORY MISSIONS OFF OUR FACTIONS.
--
-- Wrapping the entry point is VCO's technique and it beats editing the data: CA's table is
-- read in a first-tick callback, so a wrapper installed now is in place before anything
-- reads it. The guard is `ROUTES[faction_key]`, not a separate list - a faction we have no
-- routes for keeps CA's conditions, so a house can never end up with no victory at all.
--
-- Multiplayer is left entirely alone. CA's own MP victory is a separate mission key and
-- our three routes would collide with each other on it; `multiplayer` is CA's own argument.
--
-- Written out one global at a time, not collected into a table and looped. A table
-- constructor with a nil hole gives an undefined `#` in Lua 5.1 - it returned 0 here once,
-- and every house silently kept the entry it did not have.
local function derpy_disable(vo)
\tif not is_table(vo) or not is_table(vo.factions) then
\t\treturn
\tend

\tlocal old_init = vo.initialise_victory_missions

\tvo.initialise_victory_missions = function(self, faction_key, multiplayer)
\t\tif not multiplayer and ROUTES[faction_key] then
\t\t\tout("derpy_chd_victory_routes: CA victory missions skipped for " .. faction_key)
\t\t\treturn
\t\tend

\t\treturn old_init(self, faction_key, multiplayer)
\tend
end

derpy_disable(victory_objectives_ie)        -- main_warhammer: IE and IEE
derpy_disable(victory_objectives_oldworld)  -- cr_oldworld
derpy_disable(victory_objectives)           -- wh3_main_chaos: Realms of Chaos

-- 2. ISSUE OUR OWN.
--
-- Reading a global here rather than through _G is deliberate: measured 2026-09-07 in a live
-- campaign, `victory_objectives_oldworld` resolves as a direct read while
-- rawget(_G, "victory_objectives_oldworld") is nil. The mod script environment is not _G.
-- A route may be a table instead of a string: {region, on_map, off_map}.
-- region_by_key answers with a NULL INTERFACE for a region this map does not have, which is
-- the cheapest way to tell four campaigns apart from one file - no campaign name, no script
-- root. It lives on REGION_MANAGER_SCRIPT_INTERFACE, NOT on cm; the same walk is in
-- derpy_chd_drill_chain.lua and zzz_derpy_chd_exchange.lua.
--
-- pcall because a throw inside a first-tick callback takes every callback queued after it
-- with it: CA's call_each has no pcall. An unreachable region manager then reads as
-- off-map, which is the safe way to be wrong - the off_map block is map-agnostic.
--
-- A gate may also be a TABLE of keys, one per map namespace (`wh3_main_combi_region_*` for
-- IE and IEE, `cr_oldworld_region_*` for the Old World); it is on the map if any one is.
local function derpy_on_map(region)
\tif region == nil then
\t\treturn true
\tend

\tif type(region) == "table" then
\t\tfor i = 1, #region do
\t\t\tif derpy_on_map(region[i]) then
\t\t\t\treturn true
\t\t\tend
\t\tend
\t\treturn false
\tend

\tlocal found = false

\tpcall(function()
\t\tlocal r = cm:model():world():region_manager():region_by_key(region)
\t\tfound = (r and not r:is_null_interface()) or false
\tend)

\treturn found
end

-- 4. SACK-OR-OCCUPY OBJECTIVES. A TAKE row's SCRIPTED objective completes when its faction
-- sacks the region's settlement (CharacterSackedSettlement) or comes to own the region
-- (RegionFactionChangeEvent - any occupy option of any culture ends there, and so does a city
-- that changes hands by confederation). Registered on EVERY load, not only a new game: the
-- mission lives in the save, the listener does not.
local function derpy_take(faction_key, region_key)
\tfor i = 1, #TAKE do
\t\tlocal t = TAKE[i]

\t\tif t.faction == faction_key and t.region == region_key then
\t\t\tlocal faction = cm:get_faction(faction_key)

\t\t\tif faction and cm:mission_is_active_for_faction(faction, t.mission) then
\t\t\t\tcm:complete_scripted_mission_objective(faction_key, t.mission, t.script_key, true)
\t\t\t\tout("derpy_chd_victory_routes: " .. t.script_key .. " completed by " .. faction_key)
\t\t\tend
\t\tend
\tend
end

local function derpy_take_listeners()
\tif #TAKE == 0 then
\t\treturn
\tend

\tcore:add_listener("derpy_chd_take_sacked", "CharacterSackedSettlement", true,
\t\tfunction(context)
\t\t\tlocal ok, err = pcall(function()
\t\t\t\tderpy_take(context:character():faction():name(),
\t\t\t\t\tcontext:garrison_residence():region():name())
\t\t\tend)
\t\t\tif not ok then
\t\t\t\tout("derpy_chd_victory_routes: sack listener failed: " .. tostring(err))
\t\t\tend
\t\tend, true)

\tcore:add_listener("derpy_chd_take_owned", "RegionFactionChangeEvent", true,
\t\tfunction(context)
\t\t\tlocal ok, err = pcall(function()
\t\t\t\tlocal region = context:region()
\t\t\t\tlocal owner = region:owning_faction()
\t\t\t\tif owner and not owner:is_null_interface() then
\t\t\t\t\tderpy_take(owner:name(), region:name())
\t\t\t\tend
\t\t\tend)
\t\t\tif not ok then
\t\t\t\tout("derpy_chd_victory_routes: ownership listener failed: " .. tostring(err))
\t\t\tend
\t\tend, true)
end

-- 5. A QUEST THAT GRANTS A LORD. On success the lord joins the faction's recruit pool.
-- MissionSucceeded fires once, so there is no saved flag; registered on every load because
-- the mission can succeed on any turn after the one it was issued on. A row's `faction` may
-- be a culture key, for a quest every faction of that culture is issued.
--
-- spawn_character_to_pool takes no rank (its 50 is the AGE), so a row with `rank` leaves a
-- saved value behind and the lord is raised to that level the first time he is recruited.
-- Cleared with false, not nil: the value has to stay a value in the save.
local function derpy_rank_key(faction_key, subtype)
\treturn "''' + RANK_KEY_PREFIX + '''" .. faction_key .. "_" .. subtype
end

local function derpy_grant_listeners()
\tif #GRANT == 0 then
\t\treturn
\tend

\tcore:add_listener("derpy_chd_quest_grant", "MissionSucceeded", true,
\t\tfunction(context)
\t\t\tlocal ok, err = pcall(function()
\t\t\t\tlocal key = context:mission():mission_record_key()
\t\t\t\tlocal faction = context:faction()
\t\t\t\tlocal faction_key = faction:name()
\t\t\t\tlocal culture = faction:culture()

\t\t\t\tfor i = 1, #GRANT do
\t\t\t\t\tlocal g = GRANT[i]

\t\t\t\t\tif g.mission == key and (g.faction == faction_key or g.faction == culture) then
\t\t\t\t\t\tcm:spawn_character_to_pool(faction_key, g.name, "", "", "", 50, true,
\t\t\t\t\t\t\t"general", g.subtype, false, "")
\t\t\t\t\t\tif g.rank then
\t\t\t\t\t\t\tcm:set_saved_value(derpy_rank_key(faction_key, g.subtype), g.rank)
\t\t\t\t\t\tend
\t\t\t\t\t\tout("derpy_chd_victory_routes: " .. g.subtype .. " joins " .. faction_key)
\t\t\t\t\tend
\t\t\t\tend
\t\t\tend)
\t\t\tif not ok then
\t\t\t\tout("derpy_chd_victory_routes: grant listener failed: " .. tostring(err))
\t\t\tend
\t\tend, true)

\tcore:add_listener("derpy_chd_quest_grant_rank", "CharacterRecruited", true,
\t\tfunction(context)
\t\t\tlocal ok, err = pcall(function()
\t\t\t\tlocal character = context:character()
\t\t\t\tlocal key = derpy_rank_key(character:faction():name(), character:character_subtype_key())
\t\t\t\tlocal rank = cm:get_saved_value(key)

\t\t\t\tif rank then
\t\t\t\t\tcm:set_saved_value(key, false)
\t\t\t\t\tcm:add_agent_experience(cm:char_lookup_str(character), rank, true)
\t\t\t\t\tout("derpy_chd_victory_routes: " .. key .. " raised to level " .. rank)
\t\t\t\tend
\t\t\tend)
\t\t\tif not ok then
\t\t\t\tout("derpy_chd_victory_routes: rank listener failed: " .. tostring(err))
\t\t\tend
\t\tend, true)
end

-- 6. CONFEDERATING A HOUSE pools its lord for the absorbing faction. context:faction() is the
-- house absorbed, context:confederation() the faction absorbing it (CA's episode_neferata.lua).
-- The Tower's annex rituals confederate through cm:force_confederation, so they count too.
local function derpy_confed_listeners()
\tif next(CONFED_GRANT) == nil then
\t\treturn
\tend

\tcore:add_listener("derpy_chd_confed_grant", "FactionJoinsConfederation", true,
\t\tfunction(context)
\t\t\tlocal ok, err = pcall(function()
\t\t\t\tlocal g = CONFED_GRANT[context:faction():name()]

\t\t\t\tif g then
\t\t\t\t\tlocal faction_key = context:confederation():name()
\t\t\t\t\tcm:spawn_character_to_pool(faction_key, g.name, "", "", "", 50, true,
\t\t\t\t\t\t"general", g.subtype, false, "")
\t\t\t\t\tif g.rank then
\t\t\t\t\t\tcm:set_saved_value(derpy_rank_key(faction_key, g.subtype), g.rank)
\t\t\t\t\tend
\t\t\t\t\tout("derpy_chd_victory_routes: " .. g.subtype .. " joins " .. faction_key
\t\t\t\t\t\t.. " by confederation")
\t\t\t\tend
\t\t\tend)
\t\t\tif not ok then
\t\t\t\tout("derpy_chd_victory_routes: confederation listener failed: " .. tostring(err))
\t\t\tend
\t\tend, true)
end

local function derpy_issue_quests(faction_key, quests)
\tif not quests then
\t\treturn
\tend

\tlocal issued = 0

\tfor j = 1, #quests do
\t\tif derpy_on_map(quests[j].region) then
\t\t\tcm:trigger_custom_mission_from_string(faction_key, quests[j].mission)
\t\t\tissued = issued + 1
\t\tend
\tend

\tout("derpy_chd_victory_routes: issued " .. issued .. " of " .. #quests
\t\t.. " quests for " .. faction_key)
end

local function derpy_pick(entry)
\tif type(entry) == "string" then
\t\treturn entry
\tend

\tif derpy_on_map(entry.region) then
\t\treturn entry.on_map
\tend

\treturn entry.off_map
end

-- 7. CA'S 9.0 REWARD SWITCH. victory_objectives_config.lua marks every new Immortal Empires
-- game with the saved value IEVictoryConditionUseDLC29Config, and on every load
-- _victory_objectives_ie:add_scripted_victory_listeners() then calls
-- cm:set_victory_mission_rewards_disabled(true) for the whole campaign. CA pays its own
-- factions through a Victory Achieved incident instead; our houses are not among them, so
-- every route's purse and trophy went unpaid. VCO hit the same fault and switches it back.
--
-- CA's call runs in the shared first-tick list (wh_start.lua, start_game_all_factions), and
-- process_first_tick_callbacks runs the post list after it, so ours lands last. Only when a
-- human is one of our houses: a CA faction's player keeps CA's incident and is never paid
-- twice. Not in multiplayer, where no route is issued. pcall because a throw here would take
-- every post callback queued after this one with it.
local function derpy_routes_human()
\tif cm:is_multiplayer() then
\t\treturn false
\tend

\tlocal humans = cm:get_human_factions()

\tfor i = 1, #humans do
\t\tif ROUTES[humans[i]] then
\t\t\treturn true
\t\tend
\tend

\treturn false
end

cm:add_post_first_tick_callback(function()
\tif not derpy_routes_human() then
\t\treturn
\tend

\tlocal ok, err = pcall(function()
\t\tcm:set_victory_mission_rewards_disabled(false)
\tend)

\tif ok then
\t\tout("derpy_chd_victory_routes: victory mission rewards switched back on")
\telse
\t\tout("derpy_chd_victory_routes: could not switch victory mission rewards on: " .. tostring(err))
\tend
end)

-- 8. THE VICTORY ACHIEVEMENT. CA awards WH3_ACHIEVEMENT_WINNING_<culture>_1, and _2 above
-- difficulty 3, from one listener in wh3_campaign_achievements.lua, on wh_main_long_victory
-- only, so a route win awarded nothing. Same award through CA's own function and table, as
-- VCO's vco_WH3_ACHIEVEMENT_LONG_VICTORY_COMPLETE_safety_unlock does. Registered on every
-- load: the route lives in the save, the listener does not.
local ROUTE_KEYS = {''' + ", ".join("%s = true" % k for k in SLOT_KEYS) + '''}

local function derpy_achievement_listener()
\tcore:add_listener("derpy_chd_route_achievement", "MissionSucceeded", true,
\t\tfunction(context)
\t\t\tlocal ok, err = pcall(function()
\t\t\t\tif not ROUTE_KEYS[context:mission():mission_record_key()] then
\t\t\t\t\treturn
\t\t\t\tend

\t\t\t\tlocal faction = context:faction()

\t\t\t\tif not faction:is_human() then
\t\t\t\t\treturn
\t\t\t\tend

\t\t\t\tif not is_function(award_achievement_to_faction) or not is_table(wh3_campaign_achievements) then
\t\t\t\t\tout("derpy_chd_victory_routes: CA's achievement script is not loaded, no achievement")
\t\t\t\t\treturn
\t\t\t\tend

\t\t\t\tlocal names = wh3_campaign_achievements.long_victory
\t\t\t\tlocal name = is_table(names) and names[faction:culture()]

\t\t\t\tif not name then
\t\t\t\t\treturn
\t\t\t\tend

\t\t\t\tlocal faction_key = faction:name()
\t\t\t\tlocal key = "WH3_ACHIEVEMENT_WINNING_" .. name

\t\t\t\taward_achievement_to_faction(faction_key, key .. "_1")

\t\t\t\tif cm:get_difficulty() > 3 then
\t\t\t\t\taward_achievement_to_faction(faction_key, key .. "_2")
\t\t\t\tend

\t\t\t\tout("derpy_chd_victory_routes: victory achievement awarded to " .. faction_key)
\t\t\tend)
\t\t\tif not ok then
\t\t\t\tout("derpy_chd_victory_routes: achievement listener failed: " .. tostring(err))
\t\t\tend
\t\tend, true)
end
''' + _lore_lua() + '''
cm:add_first_tick_callback(function()
\tderpy_take_listeners()
\tderpy_grant_listeners()
\tderpy_confed_listeners()
\tderpy_achievement_listener()
\tderpy_lore_listener()

\tif not cm:is_new_game() then
\t\treturn
\tend

\tif cm:is_multiplayer() then
\t\tout("derpy_chd_victory_routes: multiplayer campaign, leaving CA's victory conditions alone")
\t\treturn
\tend

\tlocal humans = cm:get_human_factions()

\tfor i = 1, #humans do
\t\tlocal faction_key = humans[i]
\t\tlocal routes = ROUTES[faction_key]

\t\tif routes then
\t\t\tfor j = 1, #routes do
\t\t\t\tcm:trigger_custom_mission_from_string(faction_key, derpy_pick(routes[j]))
\t\t\tend

\t\t\t-- These routes carry the route text lines: section 9 may complete them.
\t\t\tcm:set_saved_value(LORE_SAVED_KEY, true)
\t\t\tout("derpy_chd_victory_routes: issued " .. #routes .. " victory routes for " .. faction_key)
\t\tend

\t\t-- 3. AND THE QUESTS. Ordinary missions, issued the same way and skipped outright
\t\t-- where their region is not on this map: the house's own, then its culture's.
\t\tderpy_issue_quests(faction_key, QUESTS[faction_key])

\t\tlocal faction = cm:get_faction(faction_key)
\t\tif faction then
\t\t\tderpy_issue_quests(faction_key, QUESTS[faction:culture()])
\t\tend
\tend
end)
''')
    return "\n".join(parts)


REVIEW_OUT = os.path.join(ROOT, "docs", "sessions", "VICTORY_ROUTE_TEXT_REVIEW_20261011.md")


def describe(otype, conds):
    """One objective in plain words. For the review file only; the game draws its own."""
    c = {}
    for cond in conds:
        k, _, v = cond.partition(" ")
        c.setdefault(k, []).append(v)
    total = c.get("total", ["1"])[0]

    def one(k):
        return c.get(k, [""])[0]

    if otype == "DEFEAT_N_ARMIES_OF_FACTION" and "subculture" in c:
        return "Defeat %s armies of %s" % (total, one("subculture"))
    return {
        "HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE": "Hold %s %s" % (total, one("pooled_resource")),
        "CONSTRUCT_N_OF_A_BUILDING": "Build %s of %s" % (total, one("building_level")),
        "CONSTRUCT_N_BUILDINGS_INCLUDING": "Build %s" % one("building_level"),
        "PERFORM_RITUAL": "Perform %s rituals of %s" % (total, one("ritual_category")),
        "DESTROY_FACTION": "Destroy %s" % " and ".join(c.get("faction", [])),
        "OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS":
            "Occupy, loot, raze or sack %s settlements" % total,
        "OWN_N_UNITS": "Own %s units" % total,
        "ACHIEVE_CHARACTER_RANK": "Raise a lord to rank %s" % one("total2"),
        "DEFEAT_N_ARMIES_OF_FACTION": "Defeat %s armies" % total,
        "CAPTURE_X_BATTLE_CAPTIVES": "Capture %s battle captives" % total,
        "EARN_X_AMOUNT_FROM_RAIDING": "Earn %s from raiding" % total,
        "OWN_N_REGIONS_INCLUDING": "Own %s" % one("region"),
    }.get(otype, "%s: %s" % (otype, "; ".join(conds)))


def review_markdown():
    """Every route's name, paragraph and objectives, each explainer where the panel shows it:
    the file the author approves before anything is packed (spec section 4.4)."""
    out = ["# Victory route text, for review (%d routes, %d explainers)"
           % (sum(len(ROUTES[f]) for f in HOUSES), len(EXPLAIN)), "",
           "Generated by `py tools/gen_victory_routes.py --review` from `LORE`, `EXPLAIN` and "
           "`ROUTES`. Edit the generator, not this file, and regenerate. Italic lines are the "
           "explainers, shown above the ritual they explain.", ""]

    def objective_lines(objectives):
        lines = []
        for otype, conds in objectives:
            if otype == "PERFORM_RITUAL":
                cat = next(c.split(" ", 1)[1] for c in conds if c.startswith("ritual_category "))
                lines.append("- *%s*" % EXPLAIN.get(cat, "(no explainer)"))
            lines.append("- %s" % describe(otype, conds))
        return lines

    for faction in HOUSES:
        out += ["## %s" % faction, ""]
        for idx in range(len(ROUTES[faction])):
            _slug, name, objectives, variant = route_parts(faction, idx)
            out += ["### %s: %s" % (SLOT_TITLES[idx], name), "",
                    "> %s" % LORE.get(victory_type_key(faction, idx), "(no paragraph)"), ""]
            out += objective_lines(objectives)
            if variant:
                out += ["", "Where %s is on the map, instead:" % " or ".join(gate_keys(variant[0])),
                        ""]
                out += objective_lines(variant[1])
            out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check(quiet=False):
    findings = []

    def bad(msg):
        findings.append(msg)

    if len(HOUSES) != 13:
        bad("expected 13 houses, have %d" % len(HOUSES))
    for _i, _purse in enumerate(PURSES):
        if not _purse:
            bad("purse %d is empty - that route would pay the trophy and nothing else" % _i)
        _seen = set()
        for _pool, _amount in _purse:
            if _pool in _seen:
                bad("purse %d names %s twice - two transactions on one pool in one payload"
                    % (_i, _pool))
            _seen.add(_pool)
            if _pool != MONEY and _pool not in POOLED_RESOURCES:
                bad("reward pool %s is not a verified pooled resource key" % _pool)
            if _pool == "wh3_dlc23_chd_labour":
                bad("wh3_dlc23_chd_labour is a FACTION_PROVINCE pool and cannot be paid into")
            if _amount <= 0:
                bad("reward amount for %s is %d - a negative amount would charge the player "
                    "for winning, and `factor missions` is bounded at min 0 on two of the "
                    "three pools so it would clamp to nothing anyway" % (_pool, _amount))
    if REWARD_FACTOR != "missions":
        bad("REWARD_FACTOR is %r - `missions` is the only factor verified grant-capable on all "
            "three reward pools" % REWARD_FACTOR)

    seen_types = set()
    for faction in HOUSES:
        routes = ROUTES[faction]
        # Three is the roster's shape; more is allowed up to the number of mission slot rows
        # that exist, because route index IS the slot index. Fewer is always a mistake.
        if len(routes) < 3:
            bad("%s has %d routes, want at least 3" % (faction, len(routes)))
        if len(routes) > len(SLOT_KEYS):
            bad("%s has %d routes but only %d mission slot rows exist - add to SLOT_KEYS, "
                "SLOT_TITLES and SLOT_ICONS together"
                % (faction, len(routes), len(SLOT_KEYS)))
        for idx in range(len(routes)):
            slug, name, objectives, variant = route_parts(faction, idx)
            where = "%s route %d (%s)" % (faction, idx + 1, slug)
            vt = victory_type_key(faction, idx)
            if vt in seen_types:
                bad("duplicate victory_type %s" % vt)
            seen_types.add(vt)
            if not objectives:
                bad("%s has no objectives" % where)
            trophy = route_reward_item(faction, idx)
            if trophy is None:
                pass
            elif trophy in SKILL_GRANTED_ANCILLARIES:
                bad("%s: reward %s is handed to the lord for levelling, so the route pays "
                    "nothing the player was not already getting" % (where, trophy))
            elif trophy not in {t[0] for t in TROPHY_ITEMS}:
                bad("%s: reward %s is not a TROPHY_ITEMS row - a vanilla item can be locked to "
                    "one character (five of the first pool were Zhatan's or Gorduz's), and a "
                    "key from another pack drops the whole mission if that pack is not "
                    "installed" % (where, trophy))

            # A map-gated route is validated TWICE, once per emitted block, and only the
            # gated list may name a region: the base list ships to every campaign.
            lists = [(objectives, False, where)]
            if variant is not None:
                vregion, vobjectives = variant
                keys = gate_keys(vregion)
                for k in keys:
                    if k not in VERIFIED_REGIONS:
                        bad("%s: gate region %r is not in VERIFIED_REGIONS - the objective and "
                            "the runtime probe both need it, and a wrong region key is a route "
                            "that never completes and never says so" % (where, k))
                named = [c.split(" ", 1)[1] for _t, conds in vobjectives for c in conds
                         if c.startswith("region ")]
                if not vobjectives:
                    bad("%s: the map-gated objective list is empty" % where)
                elif list(vobjectives) == list(objectives):
                    bad("%s: the map-gated list is the base list, so gating it buys nothing"
                        % where)
                elif len(keys) > 1 and named:
                    bad("%s: a list gated on several maps names %s, which exists on only one "
                        "of them - a gate over namespaces must stay namespace-free"
                        % (where, ", ".join(named)))
                elif len(keys) == 1 and any(r != keys[0] for r in named):
                    bad("%s: the map-gated list names %s but is gated on %s - the gate does "
                        "not prove that region is on the map" % (where, named, keys[0]))
                lists.append((vobjectives, len(keys) == 1,
                              "%s [where %s exists]" % (where, " or ".join(keys))))

            for objectives, allow_map_bound, where in lists:
                same_type = {}
                for otype, conds in objectives:
                    same_type[otype] = same_type.get(otype, 0) + 1
                    if otype not in ATTESTED_VICTORY_TYPES:
                        bad("%s: objective type %s is attested in a victory objective by "
                            "neither CA nor VCO" % (where, otype))
                    if otype in TYPES_NEEDING_TOTAL and not any(
                            c == "total" or c.startswith("total ") for c in conds):
                        bad("%s: %s never appears without a `total` in CA or VCO"
                            % (where, otype))
                    if otype in MAP_BOUND_TYPES and not allow_map_bound:
                        bad("%s: %s carries a campaign-prefixed key and cannot ship in a file "
                            "shared by four maps - put it in a map-gated list if you mean it"
                            % (where, otype))
                    if otype == "SCRIPTED":
                        bad("%s: a SCRIPTED objective is only completed by "
                            "cm:complete_scripted_mission_objective, so it would block the "
                            "victory for ever" % where)
                    for cond in conds:
                        parts = cond.split(" ", 1)
                        kw = parts[0]
                        if kw not in CA_CONDITIONS:
                            bad("%s: unknown condition keyword %r" % (where, kw))
                            continue
                        if kw in VALUELESS_CONDITIONS:
                            if len(parts) != 1:
                                bad("%s: %s takes no value" % (where, kw))
                            continue
                        if len(parts) != 2 or not parts[1].strip():
                            bad("%s: condition %r has no value" % (where, cond))
                            continue
                        val = parts[1].strip()
                        if kw == "pooled_resource" and val not in POOLED_RESOURCES:
                            bad("%s: pooled resource %r is not a verified key" % (where, val))
                        if kw == "ritual_category" and val not in RITUAL_CATEGORIES:
                            bad("%s: ritual category %r is not a verified key" % (where, val))
                        if kw == "building_level" and val not in BUILDING_LEVELS:
                            bad("%s: building level %r is not a verified key" % (where, val))
                        if kw == "region" and val not in VERIFIED_REGIONS:
                            bad("%s: region %r is not in VERIFIED_REGIONS" % (where, val))
                        if kw == "faction" and val not in DESTROY_TARGETS:
                            bad("%s: DESTROY_FACTION target %r was not probed live; a faction "
                                "absent from a map is unachievable for ever" % (where, val))
                        if kw in ("total", "total2", "count") and not val.isdigit():
                            bad("%s: %s wants an integer, got %r" % (where, kw, val))

                # A condition on a type neither source ever pairs it with. `override_text` is
                # the one this actually catches: it reads like a free retitle and is attested
                # only on SCRIPTED and the region/province types.
                for otype, conds in objectives:
                    for cond in conds:
                        kw = cond.split(" ", 1)[0]
                        allowed = CONDITION_ONLY_ON.get(kw)
                        if allowed and otype not in allowed:
                            bad("%s: condition %r is attested only on %s, not on %s"
                                % (where, kw, "/".join(sorted(allowed)), otype))

                for otype, n in sorted(same_type.items()):
                    if n > MAX_SAME_TYPE_PER_ROUTE:
                        bad("%s: %d %s objectives in one route - the most either CA or VCO "
                            "writes is %d, and a multi-target objective is written as one "
                            "objective with repeated conditions"
                            % (where, n, otype, MAX_SAME_TYPE_PER_ROUTE))

                # An annex objective must stay under the house's own group size: a house can
                # perform any annex ritual but its own.
                for otype, conds in objectives:
                    if otype != "PERFORM_RITUAL":
                        continue
                    cat = next((c.split(" ", 1)[1] for c in conds
                                if c.startswith("ritual_category ")), None)
                    tot = next((int(c.split(" ", 1)[1]) for c in conds
                                if c.startswith("total ")), None)
                    if cat and cat.startswith("DISTRICTS_ANNEX_T5_") and tot is not None:
                        group = cat[-1]
                        ceiling = GROUP_SIZE[group]
                        if ANNEX_GROUP[faction] == group:
                            ceiling -= 1  # cannot annex itself
                        if tot > ceiling:
                            bad("%s: annex total %d exceeds what group %s offers this house (%d)"
                                % (where, tot, group, ceiling))

    # The route text: one paragraph per route, one explainer per ritual category in use, and
    # every line inside the player-text rules.
    route_keys = {victory_type_key(f, i) for f in HOUSES for i in range(len(ROUTES[f]))}
    for vt in sorted(route_keys - set(LORE)):
        bad("%s has no paragraph in LORE" % vt)
    for vt in sorted(set(LORE) - route_keys):
        bad("LORE has a paragraph for %s, which is no route" % vt)
    used = ritual_categories_used()
    for cat in sorted(used - set(EXPLAIN)):
        bad("ritual category %s has no explainer in EXPLAIN" % cat)
    for cat in sorted(set(EXPLAIN) - used):
        bad("EXPLAIN has a line for %s, which no route uses" % cat)
    for vt, text in sorted(LORE.items()):
        for f in text_findings("LORE %s" % vt, text, LORE_WORDS):
            bad(f)
    for cat, text in sorted(EXPLAIN.items()):
        for f in text_findings("EXPLAIN %s" % cat, text, EXPLAIN_WORDS):
            bad(f)
    for f_ in HOUSES:
        for i in range(len(ROUTES[f_])):
            for f in text_findings("route name %s" % victory_type_key(f_, i), ROUTES[f_][i][1]):
                bad(f)
    # Every emitted block, both halves of a gated route, as it will ship. A house with more
    # routes than slots is reported above, and neither its blocks nor the loc can be built
    # until that is fixed, so this waits for it.
    if all(len(ROUTES[f_]) <= len(SLOT_KEYS) for f_ in HOUSES):
        loc_keys = {l.split("\t")[0] for l in build_loc_tsv().splitlines()[2:]}
        for f_ in HOUSES:
            for i in range(len(ROUTES[f_])):
                variant = route_parts(f_, i)[3]
                blocks = [mission_string(f_, i)]
                if variant:
                    blocks.append(mission_string(f_, i, variant[1]))
                for block in blocks:
                    for f in block_text_findings(f_, i, block, loc_keys):
                        bad(f)

    # The quests. Fewer rules than a route because there is no victory type, no slot and no
    # trophy - but the same two that matter: an objective the engine will not evaluate, and a
    # region key nobody verified, are both silent for ever.
    quest_keys = set()
    for faction, q in all_quests():
        where = "quest %s" % q.get("key", "<no key>")
        if faction not in HOUSES and faction != CULTURE:
            bad("%s: %s is not one of the houses" % (where, faction))
        if faction == CULTURE:
            # The TAKE listeners and quest_string's faction line both need a faction key.
            if q.get("take"):
                bad("%s: a culture quest cannot be sack-or-occupy - TAKE matches one faction"
                    % where)
            if any(t in TYPES_NEEDING_FACTION for t, _c in q.get("objectives", ())):
                bad("%s: a culture quest has no faction to write into its objective" % where)
        g = q.get("grant")
        if g and "rank" in g and not (isinstance(g["rank"], int) and 1 < g["rank"] <= 50):
            bad("%s: grant rank %r is not a level from 2 to 50" % (where, g["rank"]))
        for field in ("key", "title", "description", "completed", "objectives", "payload"):
            if not q.get(field):
                bad("%s: no %s" % (where, field))
        key = q.get("key", "")
        if not key.startswith("derpy_mis_"):
            bad("%s: a quest key must start with derpy_mis_ - the victory slots own "
                "derpy_route_victory_*" % where)
        if key in quest_keys or key in SLOT_KEYS:
            bad("%s: duplicate mission key" % where)
        quest_keys.add(key)
        if "\t" in "".join(str(q.get(f, "")) for f in ("title", "description", "completed")):
            bad("%s: a tab in the text would break the TSV" % where)
        gated = bool(q.get("region"))
        if gated and q["region"] not in VERIFIED_REGIONS:
            bad("%s: gate region %r is not in VERIFIED_REGIONS" % (where, q["region"]))
        for otype, conds in q.get("objectives", ()):
            if otype not in ATTESTED_VICTORY_TYPES:
                bad("%s: objective type %s is attested by neither CA nor VCO through the "
                    "string route" % (where, otype))
            if otype == "SCRIPTED":
                sk = next((c.split(" ", 1)[1] for c in conds if c.startswith("script_key ")),
                          None)
                if sk not in q.get("take", {}):
                    bad("%s: a SCRIPTED objective needs a listener to complete it - its "
                        "script_key %r is not in the quest's `take`" % (where, sk))
                if ("override_text mission_text_text_%s" % sk) not in conds:
                    bad("%s: SCRIPTED objective %r has no override_text, so it draws blank"
                        % (where, sk))
            if otype in TYPES_NEEDING_TOTAL and not any(
                    c == "total" or c.startswith("total ") for c in conds):
                bad("%s: %s never appears without a `total`" % (where, otype))
            if otype in MAP_BOUND_TYPES and not gated:
                bad("%s: %s carries a campaign-prefixed key, so the quest needs a `region` "
                    "gate or it ships a dead objective to three other maps" % (where, otype))
            for cond in conds:
                parts_ = cond.split(" ", 1)
                kw = parts_[0]
                if kw not in CA_CONDITIONS:
                    bad("%s: unknown condition keyword %r" % (where, kw))
                    continue
                if kw in VALUELESS_CONDITIONS:
                    continue
                val = parts_[1].strip() if len(parts_) == 2 else ""
                if not val:
                    bad("%s: condition %r has no value" % (where, cond))
                elif kw == "region" and val not in VERIFIED_REGIONS:
                    bad("%s: region %r is not in VERIFIED_REGIONS" % (where, val))
                elif kw == "faction" and val not in DESTROY_TARGETS:
                    bad("%s: DESTROY_FACTION target %r was not verified" % (where, val))
                elif kw == "pooled_resource" and val not in POOLED_RESOURCES:
                    bad("%s: pooled resource %r is not a verified key" % (where, val))
                elif kw in ("total", "total2", "count") and not val.isdigit():
                    bad("%s: %s wants an integer, got %r" % (where, kw, val))
        for pool, amount in q.get("payload", ()):
            if pool != MONEY and pool not in POOLED_RESOURCES:
                bad("%s: reward pool %s is not a verified pooled resource key"
                    % (where, pool))
        # A sack-or-occupy target is a region key the listener compares against, so it must
        # be real, and on the map the quest is issued on: the gate's namespace.
        take = q.get("take", {})
        if take and not gated:
            bad("%s: a sack-or-occupy quest needs a `region` gate - its targets carry one "
                "map's prefix" % where)
        for sk, (region, text) in take.items():
            if region not in VERIFIED_REGIONS:
                bad("%s: target %r is not in VERIFIED_REGIONS" % (where, region))
            if gated and region.split("_region_")[0] != q["region"].split("_region_")[0]:
                bad("%s: target %s is in another map's namespace than the gate %s"
                    % (where, region, q["region"]))
            if not text or "\t" in text:
                bad("%s: objective %s has no text" % (where, sk))
            if not any(c == "script_key %s" % sk for _t, conds in q["objectives"]
                       for c in conds):
                bad("%s: `take` lists %s but no objective carries it" % (where, sk))

    for faction, g in CONFED_GRANT.items():
        if faction not in HOUSES:
            bad("confederation grant: %s is not one of the houses" % faction)
        if not re.fullmatch(r"names_name_\d+", g.get("name", "")) or not g.get("subtype"):
            bad("confederation grant for %s needs a names_name_ id and a subtype" % faction)

    # The Tower's GRANT mode (plain IE) pools Gordak itself and leaves his rank under a saved
    # value OUR CharacterRecruited listener applies, so both sides must build the same key, and
    # it must pool the lord Dawn's Harbour grants.
    gordak = QUESTS["cr_chd_warfleet_of_uzkulak"][0]["grant"]
    for c in DEAD_CAMPAIGNS:
        p = ANNEX_LUA.replace("wh3_main_combi", c)
        text = open(p, encoding="utf-8").read()
        if '"%s"..faction_name.."_"..c.subtype' % RANK_KEY_PREFIX not in text:
            bad("%s: the Tower companion's rank key is not derpy_grant_rank_<faction>_<subtype>" % p)
        if 'uzkulak = { subtype = "%s", name = "%s", rank = %d }' % (gordak["subtype"], gordak["name"],
                                                                     gordak.get("rank", 0)) not in text:
            bad("%s: the Tower's Abnagg seat no longer pools %s" % (p, gordak["subtype"]))

    # The minted trophies. Keys are unvalidated strings, so every one is checked here.
    trophy_keys = [t[0] for t in TROPHY_ITEMS]
    if len(set(trophy_keys)) != len(trophy_keys):
        bad("TROPHY_ITEMS has a duplicate key")
    for key, cat, name, flavour, effects in TROPHY_ITEMS:
        if not re.fullmatch(r"derpy_trophy_[a-z0-9_]+", key):
            bad("trophy %s: key must be lowercase derpy_trophy_* (uppercase in a pack path "
                "crashes since 6.1, and the prefix keeps it clear of CA's keys)" % key)
        if cat not in TROPHY_SLOT_TYPE:
            bad("trophy %s: category %r has no slot type" % (key, cat))
        if not name or not flavour or "\t" in name + flavour or "\n" in name + flavour:
            bad("trophy %s: name and flavour must be set, one line, no tabs" % key)
        if not effects:
            bad("trophy %s has no effects - it would do nothing" % key)
        if len({e for e, _v in effects}) != len(effects):
            bad("trophy %s lists one effect twice" % key)
    for key, eff, scope, _v in trophy_effect_rows():
        if scope is None:
            bad("trophy %s: effect %s is on no vanilla ancillary, so it has no proven scope "
                "- see anc_effect_scopes.py" % (key, eff))
            if pool == "wh3_dlc23_chd_labour":
                bad("%s: labour is a FACTION_PROVINCE pool and cannot be paid into" % where)
            if amount <= 0:
                bad("%s: reward amount for %s is %d" % (where, pool, amount))

    # The file this replaces must be gone from all four campaign folders. Leaving one in
    # place would put entries back in CA's table for factions we now disable.
    for campaign in DEAD_CAMPAIGNS:
        for dead in DEAD_SCRIPTS:
            p = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign", campaign,
                             "mod", dead)
            if os.path.exists(p):
                bad("%s still ships in %s - delete it, it is superseded" % (dead, campaign))

    if not quiet:
        for f in findings:
            print("FINDING: %s" % f)
        if not findings:
            print("check ok - %d houses, %d routes, %d victory types, %d mission slots"
                  % (len(HOUSES), sum(len(ROUTES[f]) for f in HOUSES), len(seen_types),
                     len(SLOT_KEYS)))
            print("           %d quests: %s"
                  % (len(all_quests()),
                     ", ".join(q["key"] for _f, q in all_quests()) or "none"))
    return findings


def write():
    os.makedirs(SRC, exist_ok=True)
    outputs = {
        os.path.join(SRC, "victory_types_tables__derpy_chd_victory.tsv"):
            build_victory_types_tsv(),
        os.path.join(SRC, "missions_tables__derpy_chd_victory.tsv"): build_missions_tsv(),
        os.path.join(SRC, "loc__derpy_chd_victory.tsv"): build_loc_tsv(),
        os.path.join(SRC, "ancillary_info_tables__derpy_chd_victory.tsv"):
            build_trophy_info_tsv(),
        os.path.join(SRC, "ancillaries_tables__derpy_chd_victory.tsv"):
            build_trophy_ancillaries_tsv(),
        os.path.join(SRC, "ancillary_to_effects_tables__derpy_chd_victory.tsv"):
            build_trophy_effects_tsv(),
        LUA_OUT: build_lua(),
    }
    for path, body in outputs.items():
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        print("wrote %s (%d bytes)" % (os.path.relpath(path, ROOT), len(body)))
    return list(outputs)


# ---------------------------------------------------------------------------
# Selftest - the shipped Lua is RUN, not read.
# ---------------------------------------------------------------------------

HARNESS = r'''
-- Stand-ins for the campaign environment, enough to load the mod file and watch what it does.
local triggered = {}
local skipped = {}
local first_tick
local post_tick
-- What the reward switch and the achievement listener did, written to CALLS_PATH:
-- "log|<out line>", "ach|<faction>|<key>", and one "rewards_final|<state>" at the end.
local calls = {}

function out(s) table.insert(calls, "log|" .. tostring(s)) end
function is_table(t) return type(t) == "table" end
function is_function(f) return type(f) == "function" end

cm = {}
function cm:add_first_tick_callback(fn) first_tick = fn end
function cm:add_post_first_tick_callback(fn) post_tick = fn end
function cm:is_new_game() return NEW_GAME ~= false end
-- CA's 9.0 shared first-tick callback has run by the time the post list does, and it leaves
-- victory rewards switched off: REWARDS_DISABLED is that state. nil = no such method.
local rewards_disabled = REWARDS_DISABLED
if REWARDS_DISABLED ~= nil then
	function cm:set_victory_mission_rewards_disabled(b) rewards_disabled = b end
end
function cm:get_difficulty() return DIFFICULTY end
-- CA's wh3_campaign_achievements.lua, as wh_campaign_setup.lua loads it for every campaign.
-- ACHIEVEMENTS false leaves both globals nil, as a campaign without that script would.
if ACHIEVEMENTS then
	wh3_campaign_achievements = {long_victory = {wh3_dlc23_chd_chaos_dwarfs = "CHAOS_DWARFS"}}
	function award_achievement_to_faction(faction_key, key)
		table.insert(calls, "ach|" .. faction_key .. "|" .. key)
	end
end
local function is_human(key)
	for _, h in ipairs(HUMANS) do
		if h == key then return true end
	end
	return false
end
function cm:is_multiplayer() return MULTIPLAYER == true end
function cm:get_human_factions() return HUMANS end
function cm:trigger_custom_mission_from_string(faction, mission)
	triggered[faction] = triggered[faction] or {}
	table.insert(triggered[faction], mission)
end

-- The sack-or-occupy half: listeners are captured, FIRE replays events at them, and a
-- mission counts as active for a faction only if this run issued it to that faction.
local listeners = {}
local done = {}
core = {}
function core:add_listener(name, event, cond, cb, persist)
	table.insert(listeners, {event = event, cond = cond, cb = cb})
end
-- Every faction key with "_chd_" in it is a Chaos Dwarf one, which holds for all fourteen.
local function culture_of(key)
	return string.find(key, "_chd_", 1, true) and "wh3_dlc23_chd_chaos_dwarfs" or "wh_main_emp_empire"
end
function cm:get_faction(key)
	return {name = function() return key end, culture = function() return culture_of(key) end,
		is_null_interface = function() return false end,
		is_human = function() return is_human(key) end}
end
local saved = SAVED or {}
function cm:get_saved_value(k) return saved[k] end
function cm:set_saved_value(k, v) saved[k] = v end
function cm:char_lookup_str(c) return "lookup:" .. c:faction():name() end
function cm:add_agent_experience(lookup, xp, by_level)
	table.insert(done, table.concat({"xp", lookup, tostring(xp), tostring(by_level)}, "|"))
end
function cm:mission_is_active_for_faction(faction, key)
	assert(type(faction) == "table", "mission_is_active_for_faction takes a faction interface")
	for _, m in ipairs(triggered[faction:name()] or {}) do
		if string.find(m, "key " .. key .. ";", 1, true) then return true end
	end
	return false
end
function cm:complete_scripted_mission_objective(faction, mission, script_key, ok)
	table.insert(done, faction .. "|" .. mission .. "|" .. script_key .. "|" .. tostring(ok))
end
function cm:spawn_character_to_pool(faction, forename, surname, clan, other, age, male, agent,
		subtype, immortal, art_set)
	table.insert(done, table.concat({"pool", faction, forename, surname, clan, other,
		tostring(age), tostring(male), agent, subtype, tostring(immortal), art_set}, "|"))
end
local function named(n) return {name = function() return n end,
	culture = function() return culture_of(n) end,
	is_null_interface = function() return false end,
	is_human = function() return is_human(n) end} end
local function fire(ev)
	local event, faction, region = ev[1], ev[2], ev[3]
	local context = {
		faction = function() return named(faction) end,
		mission = function() return {mission_record_key = function() return region end} end,
		confederation = function() return named(region) end,
		character = function() return {faction = function() return named(faction) end,
			character_subtype_key = function() return region end} end,
		garrison_residence = function() return {region = function() return named(region) end} end,
		region = function()
			local r = named(region)
			r.owning_faction = function() return named(faction) end
			return r
		end,
	}
	for _, l in ipairs(listeners) do
		if l.event == event and (l.cond == true or l.cond(context)) then l.cb(context) end
	end
end

-- The map probe the gated routes read, through the same interface walk the shipped file
-- uses: cm:model():world():region_manager():region_by_key(key). MAP_REGIONS is the list of
-- regions "this map" has; anything else answers with a null interface, as the engine does.
local function stub_region(key)
  for _, k in ipairs(MAP_REGIONS or {}) do
    if k == key then
      return {is_null_interface = function() return false end}
    end
  end
  return {is_null_interface = function() return true end}
end

function cm:model()
  return {world = function()
    return {region_manager = function()
      return {region_by_key = function(_, key) return stub_region(key) end}
    end}
  end}
end

victory_objectives_ie = {factions = {}}
function victory_objectives_ie:initialise_victory_missions(faction_key, multiplayer)
	skipped[faction_key] = false
end

dofile(SCRIPT_PATH)

if first_tick then first_tick() end
if post_tick then post_tick() end

for _, ev in ipairs(FIRE or {}) do fire(ev) end
if DONE_PATH then
  local fh = io.open(DONE_PATH, "w")
  fh:write(table.concat(done, "\n"))
  fh:close()
end
if CALLS_PATH then
  table.insert(calls, "rewards_final|" .. tostring(rewards_disabled))
  local fh = io.open(CALLS_PATH, "w")
  fh:write(table.concat(calls, "\n"))
  fh:close()
end

-- Ask the wrapper whether it would run CA's init for each faction.
for _, f in ipairs(PROBE) do
	skipped[f] = true
	victory_objectives_ie:initialise_victory_missions(f, MULTIPLAYER == true)
end

local report = {}
for _, f in ipairs(PROBE) do
	local n = triggered[f] and #triggered[f] or 0
	table.insert(report, f .. ":" .. n .. ":" .. tostring(skipped[f]))
end
print(table.concat(report, "\n"))

-- The mission strings themselves, so the python side can read what was ISSUED rather
-- than re-deriving what it thinks was issued.
if DUMP_PATH then
  local fh = io.open(DUMP_PATH, "w")
  for _, f in ipairs(PROBE) do
    for _, m in ipairs(triggered[f] or {}) do
      fh:write("=== " .. f .. "\n" .. m .. "\n")
    end
  end
  fh:close()
end
'''


def _run_lua(script_path, humans, probe, multiplayer=False, regions=(), fire=(), done=None,
             calls=None, new_game=True, ca_rewards_disabled=True, difficulty=1,
             achievements=True, saved=()):
    """Run the shipped Lua under the harness. Returns (report, issued) - `issued` is
    {faction: [mission string, ...]} read back out of the run, not rebuilt.

    `fire` is [(event, faction, region)] replayed at the captured listeners after the first
    tick; every cm:complete_scripted_mission_objective call they make is appended to `done`
    as "faction|mission|script_key|true".

    `calls` receives every out() line as "log|<text>", every achievement award as
    "ach|<faction>|<key>", and last "rewards_final|<state>": CA's reward switch as the
    post-first-tick list leaves it. `ca_rewards_disabled` is the state CA's 9.0 first-tick
    callback leaves behind (None: the method does not exist), and `new_game` False replays a
    loaded save. `difficulty` is what cm:get_difficulty() answers (4 is very hard), and
    `achievements` False leaves CA's achievement script unloaded. `saved` lists saved-value
    keys that start as true, as in a save that already set them."""
    with tempfile.TemporaryDirectory() as td:
        harness = os.path.join(td, "h.lua")
        dump = os.path.join(td, "issued.txt")
        done_path = os.path.join(td, "done.txt")
        calls_path = os.path.join(td, "calls.txt")
        preamble = ("SCRIPT_PATH = %s\nHUMANS = {%s}\nPROBE = {%s}\nMULTIPLAYER = %s\n"
                    "MAP_REGIONS = {%s}\nDUMP_PATH = %s\nDONE_PATH = %s\nFIRE = {%s}\n"
                    "CALLS_PATH = %s\nNEW_GAME = %s\nREWARDS_DISABLED = %s\n"
                    "DIFFICULTY = %d\nACHIEVEMENTS = %s\nSAVED = {%s}\n") % (
            _lua_str(script_path),
            ", ".join(_lua_str(h) for h in humans),
            ", ".join(_lua_str(p) for p in probe),
            "true" if multiplayer else "false",
            ", ".join(_lua_str(r) for r in regions),
            _lua_str(dump),
            _lua_str(done_path),
            ", ".join("{%s}" % ", ".join(_lua_str(x) for x in ev) for ev in fire),
            _lua_str(calls_path),
            "true" if new_game else "false",
            "nil" if ca_rewards_disabled is None
            else ("true" if ca_rewards_disabled else "false"),
            difficulty,
            "true" if achievements else "false",
            ", ".join("[%s] = true" % _lua_str(k) for k in saved),
        )
        with open(harness, "w", encoding="utf-8") as fh:
            fh.write(preamble + HARNESS)
        r = subprocess.run([LUA, harness], capture_output=True, text=True)
        if r.returncode != 0:
            raise AssertionError("lua failed: %s" % (r.stderr.strip() or r.stdout.strip()))
        parsed = {}
        for line in r.stdout.strip().splitlines():
            faction, count, skip = line.rsplit(":", 2)
            parsed[faction] = (int(count), skip == "true")
        issued = {}
        if os.path.exists(dump):
            with open(dump, encoding="utf-8") as fh:
                for chunk in fh.read().split("=== ")[1:]:
                    faction, _, mission = chunk.partition("\n")
                    issued.setdefault(faction.strip(), []).append(mission)
        if done is not None and os.path.exists(done_path):
            with open(done_path, encoding="utf-8") as fh:
                done.extend(l for l in fh.read().splitlines() if l)
        if calls is not None and os.path.exists(calls_path):
            with open(calls_path, encoding="utf-8") as fh:
                calls.extend(l for l in fh.read().splitlines() if l)
        return parsed, issued


def _lua_str(s):
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"')


def _lua_gate(region):
    """A gate as Lua: one key as a string, several as a table derpy_on_map walks."""
    keys = gate_keys(region)
    if len(keys) == 1:
        return _lua_str(keys[0])
    return "{ %s }" % ", ".join(_lua_str(k) for k in keys)


def selftest():
    assert os.path.exists(LUA), "Lua 5.1 not installed at %s" % LUA

    findings = check(quiet=True)
    assert not findings, "check() is not clean: %s" % findings

    def human(faction):
        """A real faction to play a quest's owner - a culture quest has none of its own."""
        return "wh3_dlc23_chd_astragoth" if faction == CULTURE else faction

    with tempfile.TemporaryDirectory() as td:
        script = os.path.join(td, "routes.lua")
        with open(script, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(build_lua())

        r = subprocess.run([LUAC, "-p", script], capture_output=True, text=True)
        assert r.returncode == 0, "luac -p failed: %s" % r.stderr

        # 1. every house gets exactly the routes it declares, and CA's init is skipped
        res, _ = _run_lua(script, HOUSES, HOUSES)
        for faction in HOUSES:
            count, skipped = res[faction]
            # No MAP_REGIONS here, so every region-gated quest is skipped; an ungated one
            # would still be issued and has to be counted.
            want = len(ROUTES[faction]) + len(
                [q for q in QUESTS.get(faction, ()) if not q.get("region")])
            assert count == want, "%s got %d routes, want %d" % (faction, count, want)
            assert skipped, "CA's victory missions were NOT disabled for %s" % faction
        assert res["wh3_dlc23_chd_conclave"][0] == 5, \
            "Ghorth should be issued five routes, got %d" \
            % res["wh3_dlc23_chd_conclave"][0]

        # 2. a faction we have no routes for keeps CA's conditions - never left with none
        res, _ = _run_lua(script, ["wh_main_dwf_dwarfs"], ["wh_main_dwf_dwarfs"])
        count, skipped = res["wh_main_dwf_dwarfs"]
        assert count == 0, "issued routes to a faction we do not own"
        assert not skipped, "disabled CA's victory missions for a faction we do not cover"

        # 3. multiplayer is left entirely alone, both halves
        res, _ = _run_lua(script, HOUSES, HOUSES, multiplayer=True)
        for faction in HOUSES:
            count, skipped = res[faction]
            assert count == 0, "%s was issued routes in multiplayer" % faction
            assert not skipped, "%s had CA's victory missions disabled in multiplayer" % faction

        # 4. every emitted mission string parses as the block syntax and names its own
        #    victory type and slot key
        for faction in HOUSES:
            for idx in range(len(ROUTES[faction])):
                block = mission_string(faction, idx)
                assert block.count("{") == block.count("}"), \
                    "unbalanced braces in %s route %d" % (faction, idx + 1)
                assert "victory_type %s;" % victory_type_key(faction, idx) in block
                assert "key %s;" % SLOT_KEYS[idx] in block
                assert "game_victory;" in block
                purse = route_rewards(faction, idx)
                for _pool, _amount in purse:
                    if _pool == MONEY:
                        assert "money %d;" % _amount in block, (
                            "no treasury reward in %s route %d" % (faction, idx + 1))
                        continue
                    assert "resource %s;" % _pool in block, (
                        "no %s reward in %s route %d" % (_pool, faction, idx + 1))
                    assert "amount %d;" % _amount in block, (
                        "no %s amount in %s route %d" % (_pool, faction, idx + 1))
                assert (block.count("factor %s;" % REWARD_FACTOR)
                        == len([r for r in purse if r[0] != MONEY])), (
                    "wrong factor count in %s route %d" % (faction, idx + 1))
                _trophy = route_reward_item(faction, idx)
                if _trophy is None:
                    assert "add_ancillary_to_faction_pool" not in block, (
                        "%s route %d pays a trophy it should not" % (faction, idx + 1))
                else:
                    assert ("ancillary_key %s;" % _trophy) in block, (
                        "no trophy in %s route %d" % (faction, idx + 1))
                # The faction line CA's add_objectives appends. Without it the objective
                # fails and the route draws no node at all - silently, no log line.
                for otype, _conds in ROUTES[faction][idx][2]:
                    if otype in TYPES_NEEDING_FACTION:
                        assert ("faction %s;" % faction) in block, (
                            "%s route %d: %s carries no faction line"
                            % (faction, idx + 1, otype))
                # Every line is either a block opener, a brace, or a `;`-terminated
                # statement. A dropped semicolon is the one syntax error the parser will
                # not tell you about - it just stops reading the block.
                openers = {"mission", "objective", "payload",
                           "primary_objectives_and_payload",
                           "add_ancillary_to_faction_pool",
                           "faction_pooled_resource_transaction"}
                for line in block.splitlines():
                    s = line.strip()
                    if not s or s in ("{", "}") or s in openers:
                        continue
                    if not s.endswith(";"):
                        raise AssertionError("unterminated line %r in %s" % (s, faction))

        # 5. the TSVs agree with build() - row counts and key sets
        n_routes = sum(len(ROUTES[f]) for f in HOUSES)
        vt = build_victory_types_tsv().strip().splitlines()
        assert len(vt) == 2 + n_routes, "victory_types row count wrong"
        keys = {l.split("\t")[0] for l in vt[2:]}
        assert keys == {victory_type_key(f, i)
                        for f in HOUSES for i in range(len(ROUTES[f]))}
        # every route's icon comes from its own index, so a house with five routes must not
        # run off the end of the shared slot lists
        for line in vt[2:]:
            cells = line.split("\t")
            assert cells[3] in ("short", "long", "ultimate", "domination"), \
                "victory_types icon %r is not one of vanilla's four" % cells[3]
        ms = build_missions_tsv().strip().splitlines()
        quest_keys = [q["key"] for _f, q in all_quests()]
        assert len(ms) == 2 + len(SLOT_KEYS) + len(quest_keys), "missions row count wrong"
        assert {l.split("\t")[0] for l in ms[2:]} == set(SLOT_KEYS) | set(quest_keys)
        loc_text = {l.split("\t")[0]: l.split("\t")[1]
                    for l in build_loc_tsv().strip().splitlines()[2:]}
        for line in ms[2:]:
            cells = line.split("\t")
            for col, field in ((2, "title"), (3, "description"),
                               (17, "mission_completed_text")):
                key = "missions_localised_%s_%s" % (field, cells[0])
                assert loc_text[key] == cells[col], \
                    "%s disagrees with its DB column" % key
        loc = build_loc_tsv().strip().splitlines()
        assert len(loc) == (2 + n_routes + len(LORE) + len(EXPLAIN)
                            + 3 * (len(SLOT_KEYS) + len(quest_keys))
                            + n_take_objectives() + 2 * len(TROPHY_ITEMS)), \
            "loc row count wrong"
        for line in loc[2:]:
            k, text, _ = line.split("\t")
            assert (k.startswith("victory_types_display_name_derpy_victory_type_")
                    or k.startswith("missions_localised_")
                    or k.startswith("mission_text_text_derpy_mis_")
                    or k.startswith("mission_text_text_derpy_route_lore_")
                    or k.startswith("mission_text_text_derpy_route_explain_")
                    or k.startswith("ancillaries_onscreen_name_derpy_trophy_")
                    or k.startswith("ancillaries_colour_text_derpy_trophy_")), \
                "stray loc key %s" % k
            assert text.strip(), "empty loc text for %s" % k
        # every trophy has its three rows, and every paid trophy is one that ships
        info = build_trophy_info_tsv().strip().splitlines()[2:]
        anc = [l.split("\t") for l in build_trophy_ancillaries_tsv().strip().splitlines()[2:]]
        eff = build_trophy_effects_tsv().strip().splitlines()[2:]
        assert info == list(TROPHIES) == [r[0] for r in anc], "trophy tables disagree"
        assert all(len(r) == 29 for r in anc), "an ancillaries row is not 29 cells"
        for r in anc:
            # the columns that make it usable by anyone and a reward only this route pays
            assert (r[3], r[25], r[26], r[27], r[28], r[22]) == (
                "true", "false", "false", "false", "all", "200"), "trophy %s shape" % r[0]
        for key in TROPHIES:
            assert any(l.startswith(key + "\t") for l in eff), "%s has no effects" % key
            for fam in ("ancillaries_onscreen_name_", "ancillaries_colour_text_"):
                assert any(l.startswith(fam + key + "\t") for l in loc[2:]), \
                    "%s has no %s loc" % (key, fam)
        for faction in HOUSES:
            for idx in range(len(ROUTES[faction])):
                t = route_reward_item(faction, idx)
                assert t is None or t in TROPHIES, "%s pays unshipped %s" % (faction, t)
        # the three derived keys a missions row needs, for every slot - a missing one is a
        # blank title in game and nothing in any log
        for key in list(SLOT_KEYS) + quest_keys:
            for field in ("title", "description", "mission_completed_text"):
                want = "missions_localised_%s_%s" % (field, key)
                assert any(l.startswith(want + "\t") for l in loc[2:]), \
                    "missions row %s has no %s loc key" % (key, field)

        # 4b. the map-gated half of a route is a whole mission block too, with the same
        #     victory type, the same slot key and the same reward as its base half.
        for faction in HOUSES:
            for idx in range(len(ROUTES[faction])):
                variant = route_parts(faction, idx)[3]
                if variant is None:
                    continue
                region, vobjectives = variant
                block = mission_string(faction, idx, vobjectives)
                where = "%s route %d [on-map]" % (faction, idx + 1)
                assert block.count("{") == block.count("}"), \
                    "unbalanced braces in %s" % where
                assert "victory_type %s;" % victory_type_key(faction, idx) in block, where
                assert "key %s;" % SLOT_KEYS[idx] in block, where
                assert "game_victory;" in block, where
                assert block.strip() != mission_string(faction, idx).strip(), (
                    "%s is the base block - the gate buys nothing" % where)
                for named in re.findall(r"region (\w+);", block):
                    assert named in gate_keys(region), (
                        "%s names %s, which its gate does not prove is on the map"
                        % (where, named))
                _trophy = route_reward_item(faction, idx)
                if _trophy is None:
                    assert "add_ancillary_to_faction_pool" not in block, (
                        "%s pays a trophy it should not" % where)
                else:
                    assert ("ancillary_key %s;" % _trophy) in block, (
                        "no trophy in %s" % where)
                for otype, _conds in vobjectives:
                    if otype in TYPES_NEEDING_FACTION:
                        assert ("faction %s;" % faction) in block, (
                            "%s: %s carries no faction line" % (where, otype))

        # 4c. THE GATE, proved by running the shipped Lua twice: with the region on the map
        #     and without it. This is the only assertion that shows derpy_pick works.
        gated = [(f, i) for f in HOUSES for i in range(len(ROUTES[f]))
                 if route_parts(f, i)[3] is not None]
        assert gated, "no map-gated route in the file - 4c would pass vacuously"
        # Compared as whole blocks, stripped: the long-bracket wrapper leaves the issued string
        # with the generator's own newline and indent around it. Run once per gate key, so a
        # gate over two namespaces is proved on BOTH maps, not on whichever key came first.
        assert any(len(gate_keys(route_parts(f, i)[3][0])) > 1 for f, i in gated), \
            "no route gated over two namespaces - the table form of the gate is untested"
        for faction, idx in gated:
            region, vobjectives = route_parts(faction, idx)[3]
            on_block = mission_string(faction, idx, vobjectives).strip()
            base = mission_string(faction, idx).strip()
            _r, off = _run_lua(script, [faction], [faction])
            want = len(ROUTES[faction])
            for key in gate_keys(region):
                _r, on = _run_lua(script, [faction], [faction], regions=[key])
                # Count ROUTES only: a quest gated on the same region rides in the same run.
                n_on = len([m for m in on[faction] if "victory_type" in m])
                assert n_on == want, (
                    "%s issued %d routes where %s exists, want %d" % (faction, n_on, key, want))
                assert [m.strip() for m in on[faction]].count(on_block) == 1, (
                    "%s: the on-map block was not issued where %s exists" % (faction, key))
                assert base not in [m.strip() for m in on[faction]], (
                    "%s: the base block was issued as well where %s exists" % (faction, key))
            n_off = len([m for m in off[faction] if "victory_type" in m])
            assert n_off == want, (
                "%s issued %d routes off the gate, want %d" % (faction, n_off, want))
            assert on_block not in [m.strip() for m in off[faction]], (
                "%s: the on-map block was issued on a map without %s - its objectives may "
                "never complete" % (faction, " or ".join(gate_keys(region))))
            assert base in [m.strip() for m in off[faction]], (
                "%s: the off-map issue is not the base mission block" % faction)

        # 5c. a quest is a whole mission block, and NOT a victory condition: no
        #     victory_type line and no game_victory payload, or completing it would end the
        #     campaign the first time a player took one settlement.
        for faction, q in all_quests():
            block = quest_string(faction, q)
            where = "quest %s" % q["key"]
            assert block.count("{") == block.count("}"), "unbalanced braces in %s" % where
            assert "key %s;" % q["key"] in block, where
            assert "victory_type" not in block, "%s carries a victory_type" % where
            assert "game_victory" not in block, "%s pays game_victory" % where
            assert "issuer CLAN_ELDERS;" in block, where
            for otype, _conds in q["objectives"]:
                assert "type %s;" % otype in block, "%s is missing %s" % (where, otype)
            for pool, amount in q["payload"]:
                if pool == MONEY:
                    assert "money %d;" % amount in block, where
                else:
                    assert "resource %s;" % pool in block, where
                    assert "amount %d;" % amount in block, where
            openers = {"mission", "objective", "payload",
                       "primary_objectives_and_payload",
                       "add_ancillary_to_faction_pool",
                       "faction_pooled_resource_transaction"}
            for line in block.splitlines():
                t = line.strip()
                if not t or t in ("{", "}") or t in openers:
                    continue
                assert t.endswith(";"), "unterminated line %r in %s" % (t, where)

        # 5d. a region-gated quest is issued ONLY where its region is, proved by running the
        #     shipped Lua both ways - the same proof as 4c, on the other mechanism.
        for faction, q in all_quests():
            if not q.get("region"):
                continue
            faction = human(faction)
            _r, on = _run_lua(script, [faction], [faction], regions=[q["region"]])
            _r, off = _run_lua(script, [faction], [faction])
            hit = [m for m in on.get(faction, ()) if ("key %s;" % q["key"]) in m]
            miss = [m for m in off.get(faction, ()) if ("key %s;" % q["key"]) in m]
            assert len(hit) == 1, (
                "%s: %d issues of %s where its region exists, want 1"
                % (faction, len(hit), q["key"]))
            assert not miss, (
                "%s: %s was issued on a map without %s - an objective that can never "
                "complete" % (faction, q["key"], q["region"]))

        # 5e. SACK OR OCCUPY, run through the shipped listeners. A sack completes its city and
        #     only its city; an ownership change completes the other; neither fires for
        #     another faction, for a region the quest does not name, or where the quest was
        #     never issued (mission_is_active_for_faction is false there).
        take_quests = [(f, q) for f, q in all_quests() if q.get("take")]
        assert take_quests, "no sack-or-occupy quest - 5e would pass vacuously"
        for faction, q in take_quests:
            (sk1, (r1, _t1)), (sk2, (r2, _t2)) = sorted(q["take"].items())[:2]
            done = []
            _run_lua(script, [faction], [faction], regions=[q["region"]], done=done,
                     fire=[("CharacterSackedSettlement", faction, r1),
                           ("RegionFactionChangeEvent", faction, r2),
                           ("CharacterSackedSettlement", "wh_main_emp_empire", r2),
                           ("CharacterSackedSettlement", faction, "wh3_main_combi_region_altdorf")])
            want = ["%s|%s|%s|true" % (faction, q["key"], sk1),
                    "%s|%s|%s|true" % (faction, q["key"], sk2)]
            assert done == want, ("%s: sack/occupy completions %r, want %r"
                                  % (q["key"], done, want))
            # the same events on a map where this quest was never issued complete nothing
            done = []
            _run_lua(script, [faction], [faction], regions=[], done=done,
                     fire=[("CharacterSackedSettlement", faction, r1),
                           ("RegionFactionChangeEvent", faction, r2)])
            assert not done, "%s completed where it was never issued: %r" % (q["key"], done)
            # every objective's text ships
            for sk in q["take"]:
                assert ("mission_text_text_%s" % sk) in loc_text, \
                    "%s has no objective text" % sk

        # 5f. A GRANTING QUEST, through the shipped listener (FIRE's third field is the mission
        #     key for MissionSucceeded): its own success pools the lord once, with Gordak's
        #     argument shape; another faction's success or another mission pools nobody.
        #     A `rank` lord is raised to it on his first recruitment and only then: not before
        #     the quest, not on a second recruitment, not for another subtype.
        grants = [(f, q) for f, q in all_quests() if q.get("grant")]
        assert grants, "no granting quest - 5f would pass vacuously"
        assert any(q["grant"].get("rank") for _f, q in grants), "no ranked grant - 5f is vacuous"
        for faction, q in grants:
            g = q["grant"]
            faction = human(faction)
            done = []
            _run_lua(script, [faction], [faction], regions=[q["region"]], done=done,
                     fire=[("CharacterRecruited", faction, g["subtype"]),
                           ("MissionSucceeded", faction, q["key"]),
                           ("MissionSucceeded", "wh_main_emp_empire", q["key"]),
                           ("MissionSucceeded", faction, "derpy_mis_not_a_quest"),
                           ("CharacterRecruited", faction, "derpy_not_him"),
                           ("CharacterRecruited", faction, g["subtype"]),
                           ("CharacterRecruited", faction, g["subtype"])])
            want = ["pool|%s|%s||||50|true|general|%s|false|" % (faction, g["name"], g["subtype"])]
            if g.get("rank"):
                want.append("xp|lookup:%s|%d|true" % (faction, g["rank"]))
            assert done == want, "%s: grant calls %r, want %r" % (q["key"], done, want)
            assert re.fullmatch(r"names_name_\d+", g["name"]), "%s: grant name %r" % (q["key"], g["name"])

        # 5h. CONFEDERATING a house pools its lord for the absorber, once per event, and
        #     absorbing any other faction pools nobody. Needs no issued quest and no map. A
        #     `rank` lord is raised on his first recruitment after it, and only then.
        assert CONFED_GRANT, "no confederation grant - 5h would pass vacuously"
        for house, g in CONFED_GRANT.items():
            done = []
            _run_lua(script, ["wh3_dlc23_chd_astragoth"], ["wh3_dlc23_chd_astragoth"], done=done,
                     fire=[("CharacterRecruited", "wh3_dlc23_chd_astragoth", g["subtype"]),
                           ("FactionJoinsConfederation", house, "wh3_dlc23_chd_astragoth"),
                           ("FactionJoinsConfederation", "wh3_dlc23_chd_zhatan",
                            "wh3_dlc23_chd_astragoth"),
                           ("CharacterRecruited", "wh3_dlc23_chd_astragoth", g["subtype"]),
                           ("CharacterRecruited", "wh3_dlc23_chd_astragoth", g["subtype"])])
            want = ["pool|wh3_dlc23_chd_astragoth|%s||||50|true|general|%s|false|"
                    % (g["name"], g["subtype"])]
            if g.get("rank"):
                want.append("xp|lookup:wh3_dlc23_chd_astragoth|%d|true" % g["rank"])
            assert done == want, "%s: confederation calls %r, want %r" % (house, done, want)

        # 5g. a culture quest reaches every Chaos Dwarf human, CA's own included, and nobody
        #     else - the reach temp_spawn_pool_chd_oldworld.lua had.
        culture_quests = QUESTS.get(CULTURE, ())
        assert culture_quests, "no culture quest - 5g would pass vacuously"
        for q in culture_quests:
            for who, want in (("wh3_dlc23_chd_astragoth", 1), ("cr_chd_house_of_bzaark", 1),
                              ("wh_main_emp_empire", 0)):
                _r, on = _run_lua(script, [who], [who], regions=[q["region"]])
                n = len([m for m in on.get(who, ()) if ("key %s;" % q["key"]) in m])
                assert n == want, "%s: %s issued %d times, want %d" % (q["key"], who, n, want)

        # 5b. the purses must actually vary - one flat reward for all 35 routes is the
        #     thing this replaced
        paid = set()
        for faction in HOUSES:
            seen_here = []
            for idx in range(len(ROUTES[faction])):
                purse = route_rewards(faction, idx)
                paid.add(purse)
                assert purse not in seen_here, (
                    "%s pays the same purse for two routes" % faction)
                seen_here.append(purse)
        assert len(paid) == len(PURSES), (
            "only %d of the %d purses are ever paid" % (len(paid), len(PURSES)))
        assert any(len(pu) == 1 for pu in paid), "no route pays a single currency"
        assert any(len(pu) > 1 for pu in paid), "no route pays a mix"
        assert any(r[0] == MONEY for pu in paid for r in pu), "no route pays treasury"

        # 7. CA'S 9.0 REWARD SWITCH. wh_start.lua's shared first-tick callback leaves victory
        #    mission rewards switched OFF for the whole campaign, and the harness starts there.
        #    The shipped post-first-tick callback must switch them back on for one of our
        #    houses, on a new game and on a load, and leave every other case alone.
        bd = "cr_chd_slaves_of_the_black_dwarf"

        def run_calls(path, humans, **kw):
            calls = []
            _run_lua(path, humans, humans, calls=calls, **kw)
            return calls

        def rewards_final(calls):
            finals = [c for c in calls if c.startswith("rewards_final|")]
            assert len(finals) == 1, "expected one rewards_final line, got %r" % finals
            return finals[0].split("|", 1)[1]

        def check_rewards(path):
            for who in (bd, "wh3_dlc23_chd_conclave", "wh3_dlc23_chd_minor_faction"):
                got = rewards_final(run_calls(path, [who]))
                assert got == "false", "%s: rewards left switched off (%s)" % (who, got)
            got = rewards_final(run_calls(path, [bd], new_game=False))
            assert got == "false", "a loaded save kept rewards switched off (%s)" % got
            got = rewards_final(run_calls(path, ["wh_main_dwf_dwarfs"]))
            assert got == "true", "switched rewards on for a faction we have no routes for"
            got = rewards_final(run_calls(path, HOUSES, multiplayer=True))
            assert got == "true", "touched the reward switch in multiplayer"
            calls = run_calls(path, [bd], ca_rewards_disabled=None)
            assert any("could not switch victory mission rewards on" in c for c in calls), \
                "a missing reward switch was not caught and logged"

        check_rewards(script)

        # 8. THE VICTORY ACHIEVEMENT, through the shipped listener (FIRE's third field is the
        #    mission key). A route key awards _1, and _2 only above difficulty 3, on a new game
        #    and on a load; a quest, an AI house and CA's own long-victory key award nothing;
        #    without CA's achievement script the listener logs and does not throw.
        ach = "WH3_ACHIEVEMENT_WINNING_CHAOS_DWARFS"

        def awarded(calls):
            return [c for c in calls if c.startswith("ach|")]

        def check_achievements(path):
            got = awarded(run_calls(path, [bd], fire=[("MissionSucceeded", bd, SLOT_KEYS[1])]))
            assert got == ["ach|%s|%s_1" % (bd, ach)], "difficulty 1 awarded %r" % got
            got = awarded(run_calls(path, [bd], difficulty=4,
                                    fire=[("MissionSucceeded", bd, SLOT_KEYS[4])]))
            assert got == ["ach|%s|%s_1" % (bd, ach), "ach|%s|%s_2" % (bd, ach)], \
                "very hard awarded %r" % got
            got = awarded(run_calls(path, [bd], new_game=False,
                                    fire=[("MissionSucceeded", bd, SLOT_KEYS[0])]))
            assert got == ["ach|%s|%s_1" % (bd, ach)], "a loaded save awarded %r" % got
            got = awarded(run_calls(path, [bd], difficulty=5, fire=[
                ("MissionSucceeded", bd, "derpy_mis_black_dwarf_road_to_praag_ie"),
                ("MissionSucceeded", "cr_chd_house_of_baal", SLOT_KEYS[0]),
                ("MissionSucceeded", bd, "wh_main_long_victory")]))
            assert got == [], "awarded outside a human's route: %r" % got
            calls = run_calls(path, [bd], achievements=False,
                              fire=[("MissionSucceeded", bd, SLOT_KEYS[0])])
            assert not awarded(calls), "awarded with CA's achievement script absent"
            assert any("achievement script is not loaded" in c for c in calls), \
                "an absent achievement script was not logged"
            assert not any("achievement listener failed" in c for c in calls), \
                "the achievement listener threw: %r" % [c for c in calls if "failed" in c]

        check_achievements(script)

        # 10. THE ROUTE TEXT COMPLETER, through the shipped listener. At a human turn start
        #     every slot's lines complete, all five whatever the house's route count, on a new
        #     game and on a load carrying the saved value; an AI house, a save from before
        #     phase 2, a human with no routes and multiplayer complete nothing.
        def lore_done(path, humans, fire_for, **kw):
            done = []
            _run_lua(path, humans, humans, done=done,
                     fire=[("FactionTurnStart", f, "") for f in fire_for], **kw)
            return done

        def want_lore(faction):
            return ["%s|%s|%s|true" % (faction, k, LORE_SCRIPT_KEY) for k in SLOT_KEYS]

        def check_lore(path):
            got = lore_done(path, [bd], [bd])
            assert got == want_lore(bd), "new game: %r" % got
            sk = "cr_chd_skullstack"
            got = lore_done(path, [sk], [sk])
            assert got == want_lore(sk), "a three-route house: %r" % got
            got = lore_done(path, [bd], [bd], new_game=False, saved=[LORE_SAVED_KEY])
            assert got == want_lore(bd), "a load carrying the saved value: %r" % got
            got = lore_done(path, [bd], [bd], new_game=False)
            assert got == [], "a save from before phase 2 got calls: %r" % got
            got = lore_done(path, [bd], ["cr_chd_house_of_baal"])
            assert got == [], "an AI house got calls: %r" % got
            got = lore_done(path, ["wh_main_dwf_dwarfs"], ["wh_main_dwf_dwarfs"])
            assert got == [], "a human with no routes got calls: %r" % got
            got = lore_done(path, HOUSES, HOUSES, multiplayer=True)
            assert got == [], "multiplayer got calls: %r" % got

        check_lore(script)

        # 11. the review file shows every line it is there to show, and no gap marker
        review = review_markdown()
        for text in list(LORE.values()) + list(EXPLAIN.values()):
            assert text in review, "the review file is missing %r" % text[:40]
        for f in HOUSES:
            for i in range(len(ROUTES[f])):
                assert ROUTES[f][i][1] in review, "the review is missing %s" % ROUTES[f][i][1]
        assert "(no paragraph)" not in review and "(no explainer)" not in review, \
            "the review file shows a gap"

        # 9. MUTANTS. Each breaks one line of the shipped Lua, still parses, and the check that
        #    guards that line must notice. A check no mutant can fail proves nothing.
        def mutant(needle, repl):
            src = build_lua()
            assert src.count(needle) == 1, (
                "mutation anchor %r occurs %d times - move the anchor with the code"
                % (needle, src.count(needle)))
            path = os.path.join(td, "mutant.lua")
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(src.replace(needle, repl))
            r = subprocess.run([LUAC, "-p", path], capture_output=True, text=True)
            assert r.returncode == 0, "mutant for %r does not parse: %s" % (needle, r.stderr)
            return path

        MUTANTS = [
            ("cm:set_victory_mission_rewards_disabled(false)", "local _ = false", check_rewards),
            ("if not derpy_routes_human() then", "if false then", check_rewards),
            ("if cm:is_multiplayer() then\n\t\treturn false", "if false then\n\t\treturn false",
             check_rewards),
            ("if not ROUTE_KEYS[context:mission():mission_record_key()] then", "if false then",
             check_achievements),
            ("if not faction:is_human() then", "if false then", check_achievements),
            ("if cm:get_difficulty() > 3 then", "if true then", check_achievements),
            ("if not is_function(award_achievement_to_faction) "
             "or not is_table(wh3_campaign_achievements) then", "if false then",
             check_achievements),
            ("function(context) return context:faction():is_human() end",
             "function(context) return true end", check_lore),
            ("if not cm:get_saved_value(LORE_SAVED_KEY) then", "if false then", check_lore),
            ("cm:set_saved_value(LORE_SAVED_KEY, true)", "local _ = true", check_lore),
            ("for j = 1, #LORE_SLOTS do", "for j = 1, #LORE_SLOTS - 1 do", check_lore),
            ('local LORE_SCRIPT_KEY = "derpy_route_lore"',
             'local LORE_SCRIPT_KEY = "derpy_route_lor"', check_lore),
            ("\tderpy_lore_listener()\n\n\tif not cm:is_new_game() then\n\t\treturn\n\tend\n",
             "\n\tif not cm:is_new_game() then\n\t\treturn\n\tend\n\tderpy_lore_listener()\n",
             check_lore),
        ]
        for needle, repl, guard in MUTANTS:
            # Outside the try: a stale anchor or a mutant that will not parse is a finding,
            # not a kill.
            path = mutant(needle, repl)
            try:
                guard(path)
            except AssertionError:
                continue
            raise AssertionError("mutant survived: %r -> %r" % (needle, repl))

        # 6. deliberate breaks must be caught
        import copy
        saved = copy.deepcopy(ROUTES)
        saved_lore, saved_explain = dict(LORE), dict(EXPLAIN)
        real_mission_string = mission_string
        try:
            # the route text: a route with no paragraph, a stray paragraph, a used ritual
            # category with no explainer, and the three player-text rules
            vt0 = victory_type_key(HOUSES[0], 0)
            del LORE[vt0]
            assert any("no paragraph" in f for f in check(quiet=True)), (
                "a route with no paragraph was not caught")
            LORE[vt0] = saved_lore[vt0]
            LORE["derpy_victory_type_nobody_1_nothing"] = saved_lore[vt0]
            assert any("which is no route" in f for f in check(quiet=True)), (
                "a stray paragraph was not caught")
            del LORE["derpy_victory_type_nobody_1_nothing"]
            del EXPLAIN["HELLFORGE_CAPS_KDAAI"]
            assert any("has no explainer" in f for f in check(quiet=True)), (
                "a ritual category with no explainer was not caught")
            EXPLAIN.update(saved_explain)
            LORE[vt0] = saved_lore[vt0].replace(" ", " \u2014 ", 1)
            assert any("not printable ASCII" in f for f in check(quiet=True)), (
                "an em dash in a paragraph was not caught")
            LORE[vt0] = saved_lore[vt0]
            EXPLAIN["HELLFORGE_CAPS_KDAAI"] = "At the Hell-Forge. Raise the K'daai cap."
            assert any("jargon word" in f for f in check(quiet=True)), (
                "'cap' in an explainer was not caught")
            EXPLAIN.update(saved_explain)
            LORE[vt0] = " ".join(saved_lore[vt0].split()[:20])
            assert any("20 words" in f for f in check(quiet=True)), (
                "a 20-word paragraph was not caught")
            LORE[vt0] = saved_lore[vt0]
            # an emitted block whose paragraph line points at no loc row, and one whose
            # explainer is gone from above its ritual
            globals()["mission_string"] = lambda f, i, o=None: real_mission_string(f, i, o).replace(
                "override_text %s;" % lore_loc_key(victory_type_key(f, i)),
                "override_text mission_text_text_derpy_route_lore_nope;")
            assert any("not its paragraph line" in f for f in check(quiet=True)), (
                "a block that does not open with its paragraph was not caught")
            globals()["mission_string"] = lambda f, i, o=None: real_mission_string(f, i, o).replace(
                "override_text mission_text_text_derpy_route_explain_",
                "override_text mission_text_text_derpy_route_nope_")
            assert any("no explainer directly above" in f for f in check(quiet=True)), (
                "a ritual with no explainer above it was not caught")
            globals()["mission_string"] = real_mission_string

            ROUTES[HOUSES[0]][0][2].append(
                ("CONTROL_N_PROVINCES_INCLUDING",
                 ["total 3", "province wh3_main_combi_province_zorn_uzkul"]))
            assert any("campaign-prefixed" in f for f in check(quiet=True)), \
                "a map-bound objective type was not caught"
            ROUTES[HOUSES[0]][0][2].pop()

            ROUTES[HOUSES[0]][0][2].append(
                ("SCRIPTED", ["script_key derpy_dummy", "override_text x"]))
            assert any("SCRIPTED" in f for f in check(quiet=True)), \
                "a blocking SCRIPTED objective was not caught"
            ROUTES[HOUSES[0]][0][2].pop()

            ROUTES[HOUSES[0]][0][2].append(
                ("HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
                 ["pooled_resource wh3_dlc23_chd_typo", "total 5"]))
            assert any("not a verified key" in f for f in check(quiet=True)), \
                "a typo'd pooled resource was not caught"
            ROUTES[HOUSES[0]][0][2].pop()

            # an annex total the house's own group cannot supply
            ROUTES["cr_chd_house_of_bzaark"][1][2][0] = (      # all of C: one seat is his own
                "PERFORM_RITUAL",
                ["ritual_category DISTRICTS_ANNEX_T5_C", "total %d" % GROUP_SIZE["C"]])
            assert any("exceeds what group" in f for f in check(quiet=True)), \
                "an unachievable annex total was not caught"
            ROUTES["cr_chd_house_of_bzaark"][1][2][0] = saved[
                "cr_chd_house_of_bzaark"][1][2][0]

            # three of one objective type in a route - more than either source writes
            ROUTES["wh3_dlc23_chd_conclave"][1][2].append(
                ("PERFORM_RITUAL",
                 ["ritual_category DISTRICTS_ANNEX_T5_C", "total 1"]))
            assert any("in one route" in f for f in check(quiet=True)), \
                "three objectives of one type were not caught"
            ROUTES["wh3_dlc23_chd_conclave"][1][2].pop()

            # a count-N objective with no count
            ROUTES[HOUSES[0]][0][2].append(
                ("DEFEAT_N_ARMIES_OF_FACTION", []))
            assert any("without a `total`" in f for f in check(quiet=True)), \
                "a count objective with no total was not caught"
            ROUTES[HOUSES[0]][0][2].pop()

            # override_text on a counter objective - reads free, is not attested
            ROUTES[HOUSES[0]][0][2].append(
                ("OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS",
                 ["total 5", "override_text mission_text_text_derpy_nope"]))
            assert any("attested only on" in f for f in check(quiet=True)), \
                "override_text on an unattested type was not caught"
            ROUTES[HOUSES[0]][0][2].pop()

            # a reward paid into the province-scoped labour pool
            saved_purses = PURSES
            globals()["PURSES"] = ((("wh3_dlc23_chd_labour", 100),),)
            assert any("FACTION_PROVINCE" in f for f in check(quiet=True)), (
                "a labour reward was not caught")
            globals()["PURSES"] = ((("wh3_dlc23_chd_raw_materials", -100),),)
            assert any("would charge the player" in f for f in check(quiet=True)), (
                "a negative reward amount was not caught")
            globals()["PURSES"] = ((("wh3_dlc23_chd_armaments", 100),
                                    ("wh3_dlc23_chd_armaments", 200)),)
            assert any("twice" in f for f in check(quiet=True)), (
                "a purse paying one pool twice was not caught")
            globals()["PURSES"] = ((),)
            assert any("is empty" in f for f in check(quiet=True)), (
                "an empty purse was not caught")
            globals()["PURSES"] = saved_purses

            # a trophy the lord is handed for levelling anyway - the 2026-09-09 defect
            saved_trophies = TROPHIES
            globals()["TROPHIES"] = ("derpy_ghorth_weapon",) * len(TROPHIES)
            assert any("handed to the lord for levelling" in f
                       for f in check(quiet=True)), (
                "a skill-granted reward ancillary was not caught")
            # and a trophy out of a pack that may not be installed
            globals()["TROPHIES"] = ("derpy_not_an_ancillary",) * len(TROPHIES)
            assert any("not a TROPHY_ITEMS row" in f for f in check(quiet=True)), (
                "a foreign reward ancillary was not caught")
            # and the 2026-09-24 defect: a vanilla item locked to one character
            globals()["TROPHIES"] = ("wh3_dlc23_anc_weapon_chd_the_obsidian_axe",) * len(TROPHIES)
            assert any("not a TROPHY_ITEMS row" in f for f in check(quiet=True)), (
                "a character-locked vanilla reward (Zhatan's axe) was not caught")
            globals()["TROPHIES"] = saved_trophies

            # a minted trophy whose effect has no vanilla scope
            saved_items = TROPHY_ITEMS
            k, c, n, fl, e = TROPHY_ITEMS[0]
            globals()["TROPHY_ITEMS"] = ((k, c, n, fl, e + (("derpy_no_such_effect", 1),)),) \
                + TROPHY_ITEMS[1:]
            assert any("no proven scope" in f for f in check(quiet=True)), (
                "a trophy effect with no vanilla scope was not caught")
            globals()["TROPHY_ITEMS"] = saved_items

            # a map-gated route whose gate region nobody verified
            uz = "cr_chd_warfleet_of_uzkulak"
            gate_idx = next(i for i in range(len(ROUTES[uz]))
                            if route_parts(uz, i)[3] is not None)
            saved_route = ROUTES[uz][gate_idx]
            g_slug, g_name, g_objs, (g_region, g_vobjs) = saved_route
            ROUTES[uz][gate_idx] = (g_slug, g_name, g_objs,
                                    ("wh3_main_combi_region_not_a_real_place", g_vobjs))
            assert any("VERIFIED_REGIONS" in f for f in check(quiet=True)), (
                "an unverified gate region was not caught")
            # and a region objective in the BASE list, which ships to all four maps
            ROUTES[uz][gate_idx] = (g_slug, g_name, list(g_vobjs), (g_region, g_vobjs))
            assert any("shared by four maps" in f for f in check(quiet=True)), (
                "a map-bound objective in a base list was not caught")
            ROUTES[uz][gate_idx] = saved_route

            # a quest with a region objective and no gate: three maps get a dead mission
            uz_q = QUESTS["cr_chd_warfleet_of_uzkulak"][0]
            saved_region = uz_q["region"]
            del uz_q["region"]
            assert any("needs a `region` gate" in f for f in check(quiet=True)), (
                "an ungated region objective in a quest was not caught")
            uz_q["region"] = saved_region
            # and a quest that pays nothing - the whole point of a quest is its payload
            saved_payload = uz_q["payload"]
            uz_q["payload"] = []
            assert any("no payload" in f for f in check(quiet=True)), (
                "a quest with no payload was not caught")
            uz_q["payload"] = saved_payload

            # the sack-or-occupy quest: an objective nothing completes, and a target on the
            # wrong map for its gate
            bd = "cr_chd_slaves_of_the_black_dwarf"
            bd_q = next(q for q in QUESTS[bd] if q.get("take"))
            saved_take = dict(bd_q["take"])
            first = sorted(bd_q["take"])[0]
            del bd_q["take"][first]
            assert any("needs a listener" in f for f in check(quiet=True)), (
                "a SCRIPTED objective with no listener was not caught")
            bd_q["take"] = dict(saved_take)
            other = ("cr_oldworld_region_praag" if bd_q["region"].startswith("wh3_")
                     else "wh3_main_combi_region_praag")
            bd_q["take"][first] = (other, saved_take[first][1])
            assert any("another map's namespace" in f for f in check(quiet=True)), (
                "a sack-or-occupy target on the wrong map was not caught")
            bd_q["take"] = saved_take

            # a gate over two namespaces whose list names one of them; and a gated list that
            # is just the base list
            road = next(i for i in range(len(ROUTES[bd]))
                        if route_parts(bd, i)[3] is not None)
            saved_road = ROUTES[bd][road]
            r_slug, r_name, r_objs, (r_gate, r_vobjs) = saved_road
            ROUTES[bd][road] = (r_slug, r_name, r_objs, (r_gate, list(r_vobjs) + [
                ("OWN_N_REGIONS_INCLUDING", ["region %s" % r_gate[0], "total 1"])]))
            assert any("namespace-free" in f for f in check(quiet=True)), (
                "a region named under a two-map gate was not caught")
            ROUTES[bd][road] = (r_slug, r_name, r_objs, (r_gate, list(r_objs)))
            assert any("buys nothing" in f for f in check(quiet=True)), (
                "a gated list identical to its base was not caught")
            ROUTES[bd][road] = saved_road

            # a culture quest that needs a faction key it does not have
            cq = QUESTS[CULTURE][0]
            cq["take"] = {"x": ("cr_oldworld_region_praag", "x")}
            assert any("cannot be sack-or-occupy" in f for f in check(quiet=True)), (
                "a sack-or-occupy culture quest was not caught")
            del cq["take"]
            saved_objs = cq["objectives"]
            cq["objectives"] = saved_objs + [("CONSTRUCT_N_OF_A_BUILDING", ["total 1"])]
            assert any("no faction to write" in f for f in check(quiet=True)), (
                "a culture quest with a faction-bound objective was not caught")
            cq["objectives"] = saved_objs
            cq["grant"] = dict(cq["grant"], rank=99)
            assert any("grant rank" in f for f in check(quiet=True)), (
                "an impossible grant rank was not caught")
            cq["grant"] = dict(cq["grant"], rank=10)

            # a sixth route, with only five mission slot rows to hang it on
            ROUTES["wh3_dlc23_chd_conclave"].append(
                ("overflow", "Overflow", [("OWN_N_UNITS", ["total 10"])]))
            assert any("mission slot rows exist" in f for f in check(quiet=True)), \
                "a route with no mission slot was not caught"
            ROUTES["wh3_dlc23_chd_conclave"].pop()
        finally:
            globals()["mission_string"] = real_mission_string
            ROUTES.clear()
            ROUTES.update(saved)
            LORE.clear()
            LORE.update(saved_lore)
            EXPLAIN.clear()
            EXPLAIN.update(saved_explain)
        assert not check(quiet=True), "breaks were not fully reverted"

    print("selftest ok - %d routes across %d houses (Ghorth %d) and %d quests; Lua run, "
          "MP guard, disable guard, both map gates, sack-or-occupy listeners, TSV agreement, "
          "33 deliberate breaks, the 9.0 reward switch, the route achievement, the route text "
          "completer and %d Lua mutants all verified"
          % (sum(len(ROUTES[f]) for f in HOUSES), len(HOUSES),
             len(ROUTES["wh3_dlc23_chd_conclave"]), len(all_quests()), len(MUTANTS)))


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    elif "--check" in sys.argv:
        sys.exit(1 if check() else 0)
    elif "--review" in sys.argv:
        if check():
            print("refusing to write the review with findings outstanding")
            sys.exit(1)
        with open(REVIEW_OUT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(review_markdown())
        print("wrote %s" % os.path.relpath(REVIEW_OUT, ROOT))
    else:
        if check():
            print("refusing to write with findings outstanding")
            sys.exit(1)
        write()
