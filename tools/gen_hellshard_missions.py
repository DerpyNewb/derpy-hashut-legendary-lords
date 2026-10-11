"""Repair the eleven live hellshard missions in !aa_derpy_hashut_legendary_lords.pack.

    py tools/gen_hellshard_missions.py --check      # write TSVs + Lua, touch no pack
    py tools/gen_hellshard_missions.py              # ...then import into the pack and save
    py tools/gen_hellshard_missions.py --selftest

Step 2 of docs/sessions/HOUSE_MISSION_OPTIONS_20260903.md section 9. Four defects, all
verified against the shipped pack and CA's own wh3_dlc23_narrative_chaos_dwarfs.lua:

1. HLL ships missions_tables and NONE of the other three mission tables, so every hellshard
   row has no objective parameter and no reward. CONSTRUCT_N_BUILDINGS_INCLUDING with no
   VAR_OBJECTIVE_BUILDING_LEVEL cannot be completed - 49 of 49 vanilla rows carry one.
2. The trigger block in !!!narrative_chaos_dwarfs_new_factrions.lua is inside
   `if cm:is_new_game() and cm:model():is_multiplayer()`. CA's own singleplayer branch covers
   only its three vanilla factions, so in SINGLEPLAYER none of the mod's houses ever received
   the mission at all. This is the reason none of them were ever seen in game.
3. Three of its pairs are mispaired and a fourth faction is missing:
   slaves_of_the_black_dwarf -> a key with no row, house_of_bzaark -> the Black Dwarf's row,
   warfleet_of_uzkulak -> Tordrek's row, black_kraken_armada -> never triggered.
   Abnagg had no row of his own at all; this script mints it.
4. ui_image is `chd/generic` on all 33 rows. Every race in ui2.pack has an eventpics
   generic.png EXCEPT chd - CA's own hellshard rows have the same dead reference.

Also fixes the typo'd key `h3_dlc23_chd_ancestor_relics_unlock_derpy_ghorth` (no leading w).

Since 2026-09-03 it also owns the REST of the chain - the 22 rows that were never triggered.
The reason they never were is not the one written here first. `chaos_dwarfs_narrative` lives
in script/campaign/wh3_main_chaos/, so it loads in the Realms of Chaos campaign and nowhere
else: in Immortal Empires the Great Drill questline does not exist for anybody, CA's own three
lords included. The 22 rows are replaced by two shared ones, and
script/campaign/cr_combi_expanded/mod/derpy_chd_drill_chain.lua ports the steps between them -
the relics-unlock battle, the two rogue relic armies, CA's eight relic missions with Immortal
Empires region keys and quest-battle variants, and the final survival battle.
"""
import io
import subprocess
import json
import os
import re
import sys
import urllib.request
import zlib

URL = "http://127.0.0.1:45127/mcp"
HDR = {"Content-Type": "application/json",
       "Accept": "application/json, text/event-stream"}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Modding Files", "source", "hellshard_missions")
GAME = r"F:\SteamLibrary\steamapps\common\Total War WARHAMMER III"
PACK = os.path.join(ROOT, "Modding Files", "Modpacks",
                    "!aa_derpy_hashut_legendary_lords.pack")
FRAG = "derpy_chd_ll_missions"
HELL = "wh3_dlc23_chd_ancestor_hellshard_structure_"

# The two dead files this pair replaces. `!!!narrative_chaos_dwarfs_new_factrions.lua` drove
# cr_oldworld and cr_darklands through CA's `chaos_dwarfs_narrative` module: it triggered the
# structure missions and then handed off to two MissionSucceeded listeners that only ever
# register in Realms of Chaos, so the chain stopped dead one step in. Its drill coordinates are
# replaced by runtime capital resolution and its trigger_relic_missions override by the chain
# script, so nothing in it survives. push() deletes them from the pack.
DEAD_LUA_REL = ["script/campaign/%s/mod/!!!narrative_chaos_dwarfs_new_factrions.lua" % f
                for f in ("cr_oldworld", "cr_darklands")]

# The four campaign folders the questline ships in. The engine loads a campaign folder only for
# its own campaign, which is the whole reason CA's questline does not exist outside Realms of
# Chaos, so being in four campaigns means four copies of each file.
#
# IEE loads cr_combi_expanded AND wh3_main_combi and silently drops the second file of any
# repeated basename - ime_derpy_ghorth.lua is already lost that way, visible in the log as
# "Failed to load mod:". Six other scripts in this pack are already duplicated across that pair
# and work, because the copies are byte-identical and it does not matter which one wins. That is
# the invariant --selftest enforces here.
CAMPAIGNS = ["cr_combi_expanded", "wh3_main_combi", "cr_oldworld", "cr_darklands"]
START_REL = ["script/campaign/%s/mod/derpy_chd_hellshard_start.lua" % c for c in CAMPAIGNS]

# faction key -> (drill_location suffix, missions_tables key suffix, vanilla)
# "vanilla" means CA's own narrative script already fires it in singleplayer, so it is ours
# to fire only in multiplayer, where CA fires nothing.
STARTS = [
    ("wh3_dlc23_chd_astragoth",         "astragoth",        "wh3_dlc23_chd_astragoth",         True),
    ("wh3_dlc23_chd_legion_of_azgorh",  "drazhoath",        "wh3_dlc23_chd_legion_of_azgorh",  True),
    ("wh3_dlc23_chd_zhatan",            "zhatan",           "wh3_dlc23_chd_zhatan",            True),
    ("wh3_dlc23_chd_conclave",          "conclave",         "derpy_ghorth",                    False),
    ("cr_chd_house_of_azeros",          "azeros",           "derpy_azeros",                    False),
    ("cr_chd_house_of_baal",            "gargath",          "derpy_gargath",                   False),
    ("cr_chd_house_of_bzaark",          "bzaark",           "derpy_bzaark",                    False),
    ("cr_chd_house_of_khorakk",         "khorakk",          "derpy_urzkhal",                   False),
    ("cr_chd_fists_of_hashut",          "fists_of_hashut",  "derpy_balur",                     False),
    ("cr_chd_horns_of_hashut",          "horns_of_hashut",  "derpy_vraznak",                   False),
    ("cr_chd_slaves_of_the_black_dwarf", "black_dwarf",     "derpy_black_dwf",                 False),
    ("cr_chd_snakebeards_artificers",   "snakebeard",       "derpy_snakebeard",                False),
    ("cr_chd_warfleet_of_uzkulak",      "uzkulak",          "derpy_abnagg",                    False),
    ("cr_chd_black_kraken_armada",      "black_kraken",     "derpy_tordrek",                   False),
    # the two new house lords (gen_new_house_lords.py), 2026-10-04
    ("wh3_dlc23_chd_minor_faction",     "zharrduk",         "derpy_kharkadon",                  False),
    ("cr_chd_skullstack",               "skullstack",       "derpy_uzkul",                     False),
]

# Every mod-owned hellshard row gets junctions, including derpy_gordak's - Gordak has a skill
# tree and no faction, so nothing can trigger it, but a half-configured row is worse than a
# complete one nobody reaches.
LORDS = ["derpy_ghorth", "derpy_gargath", "derpy_balur", "derpy_vraznak", "derpy_black_dwf",
         "derpy_bzaark", "derpy_azeros", "derpy_urzkhal", "derpy_snakebeard",
         "derpy_tordrek", "derpy_gordak", "derpy_abnagg", "derpy_kharkadon", "derpy_uzkul"]

# The objective. CA points each vanilla row at that faction's own great-drill landmark
# (wh3_dlc23_special_<lord>_great_drill_of_hashut_2), which no house owns. factory_drills is
# the only CHD drill chain any faction can raise: settlement type wh3_dlc23_chd_factory,
# two levels, no faction lock. Level 2 is its top, so the objective cannot auto-complete on
# turn 1 the way a settlement-tier objective would for Ghorth, who starts at tier 5.
BUILDING = "wh3_dlc23_chd_factory_drills_2"
# CA's own payload for this mission, reused verbatim - vanilla effect bundle, ships nothing.
REWARD = "KEY[wh3_dlc23_chd_drill_structure_reward];DURATION[5];GLOBAL"
ISSUER = "CLAN_ELDERS"
# 24 CHD eventpics ship in ui2.pack; generic.png is not one of them.
ART_HELLSHARD = "chd/hell_forge"
ART_BATTLE = "chd/land_victory"

# ---------------------------------------------------------------- the rest of the drill chain
#
# The pack shipped 22 further rows - eleven `wh3_dlc23_chd_ancestor_relics_unlock_derpy_<lord>`
# and eleven `wh3_dlc23_chd_final_battle_derpy_<lord>` - with no option junctions, no payloads,
# no issuers and nothing anywhere that triggers them. They were modelled on CA's chain, which
# suffixes the FACTION key, and were expected to be picked up by CA's own listeners.
#
# They never could be, and not because of the suffix. `chaos_dwarfs_narrative` lives in
# script/campaign/wh3_main_chaos/, the REALMS OF CHAOS campaign folder, and the engine loads a
# campaign folder only for its own campaign. Measured 2026-09-03: in an Immortal Empires
# Expanded campaign the script log shows `wh3_narrative_chaos_dwarfs.lua` (the generic
# per-culture narrative file) loading and `wh3_dlc23_narrative_chaos_dwarfs.lua` never. So in
# Immortal Empires the Great Drill questline does not exist at all - not for our houses, and not
# for CA's three lords either.
#
# The chain therefore has to be ours end to end. Two shared rows replace the 22, and
# derpy_chd_drill_chain.lua drives everything between them.
# These two keep CA's prefixes, and must. `ui/campaign ui/chd_narrative_panel.twui.xml` - the
# Great Drill of Hashut panel - is driven entirely from CCO expressions in the XML, with no Lua
# behind it, and every one of them matches on a hardcoded substring of the mission key:
#
#     MissionList.FirstContext(MissionRecordContext.Key.Contains("wh3_dlc23_chd_ancestor_relics_unlock_"))
#     MissionList.Any(MissionRecordContext.Key.Contains("wh3_dlc23_chd_final_battle_"))
#     MissionList.FirstContext(MissionRecordContext.Key.Contains("wh3_dlc23_chd_ancestor_hellshard_structure_"))
#
# Renaming these rows to `derpy_*` matched none of them and left the panel drawing its own
# component names - `dy_relic_name`, `dy_description` - over an empty pane. `Contains` is all it
# asks, so any key carrying the prefix binds; the suffix is ours to choose. The hellshard rows
# already kept CA's prefix, which is why that part of the panel always worked.
UNLOCK = "wh3_dlc23_chd_ancestor_relics_unlock_derpy"
FINALE = "wh3_dlc23_chd_final_battle_derpy_"   # + faction key, one row per house
# hand-written, and the first entry is the one that is edited: write() copies it to the rest
CHAIN_REL = ["script/campaign/%s/mod/derpy_chd_drill_chain.lua" % c for c in CAMPAIGNS]

# The eleven factions that can reach the end of the chain. Gordak has a skill tree and no
# faction, so he gets a hellshard row and nothing beyond it.
HOUSES = [faction for faction, _loc, _lord, vanilla in STARTS if not vanilla]

# ------------------------------------------------------------------ per-house final battles
#
# The final battle's allied reinforcement wave belongs to a faction, and that faction supplies
# the uniform and banner colours it arrives in. CA writes one army per lord, each set to that
# lord's own faction - which is exactly why borrowing Astragoth's battle made the wave turn up
# in Astragoth's colours. `battle_set_piece_armies.faction` is a plain column with no runtime
# write, so one battle per house is the only way to colour it per house.
#
# Everything else is cloned from CA's Astragoth battle: the same battle row (same script, same
# battlefield, same survival type), the same nineteen shared armies - the dwarf, daemon and ogre
# waves plus the frontend roster - and the same ten-unit reinforcement roster. Only `army_name`
# and `faction` differ.
#
# The ten units stay vanilla Chaos Dwarf. A house's own units live in a separate pack and an
# uninstalled unit key makes a set-piece army silently wrong; the same reason
# HOUSE_MISSION_OPTIONS_20260903.md keeps unit packs out of mission objectives.
BATTLE_DONOR = "wh3_dlc23_qb_chd_drill_of_hashut_astragoth"

# ------------------------------------------------- the relics-unlock quest battle
#
# A set-piece battle whose armies belong to a faction that is not in the campaign cannot be
# built, and the engine refuses the right-click in total silence - no error, no log line.
#
# CA's `wh3_dlc23_chd_relic_army_uncovered` puts four of its five armies in
# `wh3_dlc23_rogue_karaz_a_karak_expedition`, a rogue-army faction that exists in Realms of Chaos
# and **not** in Immortal Empires. Measured live 2026-09-04: `cm:get_faction` returns a null
# interface for it, while every quest-battle faction the working battles use answers -
# `wh3_main_nur_nurgle_qb1` (grimnir_ie, the battle we watched launch), `wh_main_dwf_dwarfs_qb1`
# (grungni_ie), `wh2_dlc09_tmb_tombking_qb1` (CA's IE Drazhoath quest) and
# `wh3_dlc23_chd_chaos_dwarfs_qb1` (this battle's own allied overseer, which is why only four of
# the five armies need replacing).
#
# That is the whole fault. Two earlier readings were wrong and are recorded so they are not
# tried again:
#
#   * "the mission row is malformed" - no. CA's own unmodified
#     `wh3_dlc23_chd_ancestor_relics_unlock_wh3_dlc23_chd_astragoth`, triggered for a live
#     faction standing on that row's own coordinate, fails in exactly the same way.
#   * "the battlefield must be a quest_battles tile" - no, and this one shipped before it was
#     tested. `qb_dlc06_subterranean` (grungni_ie) and `wh3_main_macro_ogr_haunted_forest_01`
#     (CA's IE Drazhoath quest) are both campaign-located tiles carrying a
#     `battle_locations_map.bin`, and both work. Moving our clone onto grimnir_ie's tile changed
#     nothing, which is what refuted it.
#
# So the clone keeps CA's tile, script and environment untouched, and only re-homes the four
# dwarf armies. `wh_main_dwf_dwarfs_qb1` is the dwarf quest-battle faction CA uses for the
# Grungni relic - the right owner for a dwarf throng, and present in every campaign.
UNLOCK_BATTLE = "derpy_chd_relic_army_uncovered"
UNLOCK_BATTLE_DONOR = "wh3_dlc23_chd_relic_army_uncovered"
UNLOCK_ABSENT_FACTION = "wh3_dlc23_rogue_karaz_a_karak_expedition"
UNLOCK_ARMY_FACTION = "wh_main_dwf_dwarfs_qb1"
UNLOCK_ARMY = "derpy_chd_dwarf_expedition_"
ARMY_DONOR = "wh3_dlc23_final_battle_astragoth_player_reinforcement"
BATTLE = "derpy_chd_drill_of_hashut_"       # + faction key
ARMY = "derpy_chd_final_battle_reinforcement_"   # + faction key

BATTLE_TABLES = [("battle_set_pieces_tables", 0),
                 ("battle_set_piece_armies_tables", 1),
                 ("battle_set_piece_armies_junctions_tables", 0),
                 ("battle_set_piece_armies_units_junctions_tables", 0),
                 ("battle_set_piece_armies_characters_junctions_tables", 1)]

# Key prefixes of the rows being replaced. The third is the shipped typo (a dropped leading w)
# that build_missions repaired before this change removed the row entirely.
# The 22 rows the pack shipped and nothing ever triggered, by exact key. These MUST be exact:
# UNLOCK and FINALE now carry CA's prefixes too (see above), so a startswith() test on the
# prefix would delete the rows we are minting.
DEAD_KEYS = frozenset(
    [p + lord
     for p in ("wh3_dlc23_chd_ancestor_relics_unlock_",
               "h3_dlc23_chd_ancestor_relics_unlock_",
               "wh3_dlc23_chd_final_battle_")
     for lord in LORDS])   # LORDS entries already carry the derpy_ prefix

# One row each, not one per house. Both are triggered by our own script, which passes the
# faction, so nothing needs the faction in the key.
#
# location_x/y are DISPLAY coordinates, not logical ones. This cost two wrong values.
#
# They first shipped as 0,0, on the reading that 0,0 meant "no location" - CA's own rows carry
# 501,177 / 618,122 / 527,108, which are Realms of Chaos positions and name nothing here, and
# wh2_dlc09_qb_tmb_final_battle_{khalida,khatep,settra} sit at 0,0 on exactly this shape. Wrong:
# 0,0 is the map origin. Measured in a live Ghorth campaign, the panel's teleport button put his
# lord on 101,55 logical, the nearest navigable tile to the corner of the world.
#
# They were then set to 935,634 - the Great Drill site beside Zharr Naggrund, read off Ghorth's
# own `derpy_drill_x/y`, and confirmed by the pathfinder as somewhere a character can stand.
# Also wrong, because that is a *logical* coordinate. The engine read it as display and resolved
# it to logical ~1400,821 in cr_combi_region_xeich_lus_last_stand, where
# `cm:find_valid_spawn_location_for_character_from_position` returns -1,-1; the teleport dumped
# the lord at sea some seventy tiles away. Two independent proofs of the coordinate space:
#
#   * All 518 vanilla rows carrying a location fit x <= 909, y <= 729. Immortal Empires logical
#     runs past x=1456 - that is simply where Ghorth's lord was standing - and CA has quest
#     battles in Cathay and the Southlands. No logical scheme could keep every row under 909.
#   * display_x = logical_x * 0.66803335 across nine measured characters, to eight decimals.
#     display_y is close to logical_y * 0.7714 but drifts about 0.2% between samples, so it
#     carries something else as well (elevation, most likely) and must not be trusted to a tile.
#
# Hence 627,490: logical ~939,635, the middle of a validated block. The whole of logical
# x 938..940 by y 630..640 answers the pathfinder, so the y drift and the integer rounding on
# both axes are absorbed - 627,490 lands on 938 or 939 by 634 or 635, and all four are valid.
# That is five tiles from the drill and seven from Zharr Naggrund, which is what "beside the
# capital" means for the house that starts there.
#
# One coordinate for all twelve rows, not one each. The chain already sends the player across
# the world - three of the eight relic missions target Castle Drakenhof, Karak Dum and Karak
# Azorn - so a fixed quest-battle site is the idiom, and it is what every vanilla set-piece does.
# Per-house coordinates would be better and are not available: the eleven house factions are
# created by another pack and nothing here knows where they start.
BATTLE_LOC = ("627", "490")

# The envelope every vanilla row with a location fits inside. A logical coordinate written into
# these columns by mistake is very likely to break it, which is the whole point of the check -
# 935,634 did not, and only the live pathfinder caught that one, so this is a floor and not a
# guarantee.
VANILLA_LOC_MAX = (909, 729)
_CHAIN_TEMPLATE = [
    # key, donor prefix, options, payloads
    (UNLOCK, "wh3_dlc23_chd_ancestor_relics_unlock_derpy_ghorth",
     [("VAR_CHANCE", "100"), ("VAR_MISSION_LENGTH_INFINITE", ""), ("GEN_TARGET_NONE", "")],
     [("EFFECT_BUNDLE", "KEY[wh3_dlc23_chd_ancestor_relic_unlock_reward];DURATION[10]"),
      ("FACTION_POOLED_RESOURCE_TRANSACTION",
       "RESOURCE[wh3_dlc23_chd_labour_global_temp];FACTOR[wh3_dlc23_chd_labour_missions];"
       "AMOUNT[300];CONTEXT[absolute]")]),
    # One row per house, each pointing at its own clone of CA's Astragoth battle - see BATTLE
    # above. build_missions() overwrites the donor's set_piece_battle with BATTLE + faction.
    #
    # CA's own battle script is kept as-is. It sniffs the player's army for one of the three
    # vanilla lord unit types and ends in
    #     else  bm:out("No lord found, defaulting to Astragoth")
    # so a house gets Astragoth's intro cutscene, subtitle and voice line rather than nothing.
    (FINALE, "wh3_dlc23_chd_final_battle_derpy_ghorth",
     [("VAR_CHANCE", "100"), ("GEN_TARGET_NONE", "")],
     [("EFFECT_BUNDLE", "KEY[wh3_dlc23_chd_final_battle_reward];DURATION[-1];GLOBAL"),
      ("TREASURY", "AMOUNT[5000]"),
      ("FACTION_POOLED_RESOURCE_TRANSACTION",
       "RESOURCE[wh3_dlc23_chd_labour_global_temp];FACTOR[wh3_dlc23_chd_labour_missions_temp];"
       "AMOUNT[1000];CONTEXT[absolute]"),
      ("FACTION_POOLED_RESOURCE_TRANSACTION",
       "RESOURCE[wh3_dlc23_chd_conclave_influence];"
       "FACTOR[wh3_dlc23_chd_conclave_influence_gained_events];AMOUNT[300];CONTEXT[absolute]")]),
]

# The finale is one row per house so each can name its own battle; the unlock is shared.
CHAIN_ROWS = []
for _key, _donor, _opts, _pays in _CHAIN_TEMPLATE:
    if _key == FINALE:
        CHAIN_ROWS += [(FINALE + _f, _donor, _opts, _pays) for _f in HOUSES]
    else:
        CHAIN_ROWS.append((_key, _donor, _opts, _pays))

# Where the generated block starts in the Lua. Also how a re-run finds its own output, so
# writing twice does not leave two copies of the table.
MARKER = "-- faction -> the drill location to place the composite scene at, and the\n"

OPTIONS = [("VAR_CHANCE", "100"), ("VAR_MISSION_LENGTH_INFINITE", ""),
           ("GEN_TARGET_NONE", ""), ("VAR_OBJECTIVE_BUILDING_LEVEL", BUILDING)]

# missions.localised_title and .localised_description are LOC-DRIVEN. The DB columns are
# decoration: the game reads missions_localised_title_<key> / _description_<key> out of a .loc
# and ignores the row. Measured in game 2026-09-03 - a row whose DB title says "The Great Drill
# of Hashut" and whose loc says "PLACEHOLDER" renders PLACEHOLDER, and a row with no loc key at
# all renders blank. All 33 shipped rows had PLACEHOLDER in every one of their 99 loc entries.
# Note the path: text/<name>.loc, NOT text/db/<name>.loc, which is what this pack already ships.
LOC_PATH = "text/%s.loc" % FRAG

TABLES = [("cdir_events_mission_option_junctions_tables", 2),
          ("cdir_events_mission_payloads_tables", 2),
          ("cdir_events_mission_issuer_junctions_tables", 1),
          ("missions_tables", 0)]


def row_id(*parts):
    """Stable unique id per junction row, 1 .. 2147483646.

    Random ids would churn the pack on every re-run and make a diff unreadable; a hash of the
    row's own key columns is reproducible and still spread out enough not to collide with
    another mod's.
    """
    return zlib.crc32("|".join(parts).encode()) % 2147483646 + 1


def tsv(table, version, rows, header):
    body = ["\t".join(header),
            "#%s;%d;db/%s/%s" % (table, version, table, FRAG) + "\t" * (len(header) - 1)]
    body += ["\t".join(str(c) for c in r) for r in rows]
    return "\n".join(body) + "\n"


def build_missions(base):
    """Repair the shipped hellshard rows, mint Abnagg's, and replace the 22 dead chain rows.

    Idempotent: re-running over its own output changes nothing.
    """
    lines = base.rstrip("\n").split("\n")
    header, meta = lines[0].split("\t"), lines[1]
    rows = [ln.split("\t") for ln in lines[2:] if ln.strip()]
    k, img = header.index("key"), header.index("ui_image")

    for r in rows:
        if r[k].startswith("h3_dlc23_"):          # dropped leading w, dead key
            r[k] = "w" + r[k]

    # keep one of each dead family as the donor for its replacement, then drop the family
    donors = {}
    for key, donor_key, _opts, _pays in CHAIN_ROWS:
        for r in rows:
            if r[k] == donor_key or r[k] == key:
                donors[key] = list(r)
                break
    rows = [r for r in rows if r[k] not in DEAD_KEYS]

    for r in rows:
        r[img] = ART_HELLSHARD if r[k].startswith(HELL) else ART_BATTLE

    have = {r[k] for r in rows}
    donor = next(r for r in rows if r[k] == HELL + "derpy_tordrek")
    for lord in LORDS:
        if HELL + lord not in have:
            new = list(donor)
            new[k] = HELL + lord
            rows.append(new)

    lx, ly = header.index("location_x"), header.index("location_y")
    qc = header.index("quest_character")
    for key, donor_key, _opts, _pays in CHAIN_ROWS:
        if key in have:
            continue
        src = donors.get(key)
        if src is None:
            raise SystemExit("no donor row for %s (wanted %s)" % (key, donor_key))
        new = list(src)
        new[k] = key
        new[img] = ART_BATTLE
        # see BATTLE_LOC - the shipped rows carry a Realms of Chaos coordinate, and 0,0 is the
        # map origin rather than the "no location" it was mistaken for
        new[lx], new[ly] = BATTLE_LOC
        # a CQI copied out of CA's save; it names no character in any other campaign
        new[qc] = ""
        if key.startswith(FINALE):
            new[header.index("set_piece_battle")] = BATTLE + key[len(FINALE):]
        elif key == UNLOCK:
            # CA's battle is on a campaign-located tile and cannot be fought here - see
            # UNLOCK_BATTLE above
            new[header.index("set_piece_battle")] = UNLOCK_BATTLE
        rows.append(new)

    return "\n".join(["\t".join(header), meta] + ["\t".join(r) for r in rows]) + "\n"


def build_options():
    rows = []
    for lord in LORDS:
        for opt, val in OPTIONS:
            rows.append((row_id(HELL + lord, opt), HELL + lord, opt, val, "default"))
    for key, _donor, opts, _pays in CHAIN_ROWS:
        for opt, val in opts:
            rows.append((row_id(key, opt), key, opt, val, "default"))
    return tsv("cdir_events_mission_option_junctions_tables", 2, rows,
               ["id", "mission_key", "option_key", "value", "target"])


def build_payloads():
    rows = [(row_id(HELL + lord, "EFFECT_BUNDLE", "SUCCESS"), HELL + lord, "EFFECT_BUNDLE",
             "SUCCESS", REWARD, "default") for lord in LORDS]
    for key, _donor, _opts, pays in CHAIN_ROWS:
        for payload, value in pays:
            rows.append((row_id(key, payload, value), key, payload, "SUCCESS", value, "default"))
    return tsv("cdir_events_mission_payloads_tables", 2, rows,
               ["id", "mission_key", "payload_key", "status_key", "value", "target_key"])


def build_issuers():
    rows = [(ISSUER, HELL + lord) for lord in LORDS]
    rows += [(ISSUER, key) for key, _donor, _opts, _pays in CHAIN_ROWS]
    return tsv("cdir_events_mission_issuer_junctions_tables", 1, rows,
               ["issuer_key", "mission_key"])


def _vanilla(name):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from read_vanilla_cache import load
    return load(name)


def build_battles():
    """One clone of CA's Astragoth drill battle per house, so the wave wears the house's colours.

    Returns {filename: tsv}. Everything is cloned field for field from the vanilla rows; the
    only edits are the battle name, the army name and the army's faction.
    """
    battles, bfields = _vanilla("battle_set_pieces")
    armies, afields = _vanilla("battle_set_piece_armies")
    junc, jfields = _vanilla("battle_set_piece_armies_junctions")
    units, ufields = _vanilla("battle_set_piece_armies_units_junctions")

    battle_donor = next(r for r in battles if r["battle_name"] == BATTLE_DONOR)
    army_donor = next(r for r in armies if r["army_name"] == ARMY_DONOR)
    # every army CA puts in that battle except its own reinforcement wave, which we replace
    shared = [r["army_name"] for r in junc
              if r["battle_name"] == BATTLE_DONOR and r["army_name"] != ARMY_DONOR]
    roster = [r for r in units if r["army_name"] == ARMY_DONOR]
    if not shared or not roster:
        raise SystemExit("vanilla cache has no armies for %s - re-run fetch_vanilla_tables.py"
                         % BATTLE_DONOR)

    def cells(fields, row, **over):
        # RPFM's TSV wants lowercase booleans; str(True) is "True" and would not parse
        out = []
        for f in fields:
            v = over.get(f, row[f])
            out.append(("true" if v else "false") if isinstance(v, bool) else str(v))
        return out

    # the relics-unlock battle. CA's row is kept whole - same tile, same script, same
    # environment - and only the four armies sitting in a faction this campaign does not have
    # are re-homed. See UNLOCK_ARMY_FACTION.
    chars, cfields = _vanilla("battle_set_piece_armies_characters_junctions")
    unlock_donor = next(r for r in battles if r["battle_name"] == UNLOCK_BATTLE_DONOR)
    unlock_armies = [r["army_name"] for r in junc if r["battle_name"] == UNLOCK_BATTLE_DONOR]
    if not unlock_armies:
        raise SystemExit("vanilla cache has no armies for %s" % UNLOCK_BATTLE_DONOR)
    army_rows = {r["army_name"]: r for r in armies}

    brows, arows, jrows, urows, crows = [], [], [], [], []
    brows.append(cells(bfields, unlock_donor, battle_name=UNLOCK_BATTLE))
    for name in unlock_armies:
        src = army_rows[name]
        if src["faction"] != UNLOCK_ABSENT_FACTION:
            # its faction is in every campaign, so vanilla's own row serves
            jrows.append([name, UNLOCK_BATTLE])
            continue
        mine = UNLOCK_ARMY + name.split("_relic_")[-1]
        arows.append(cells(afields, src, army_name=mine, faction=UNLOCK_ARMY_FACTION))
        jrows.append([mine, UNLOCK_BATTLE])
        urows += [cells(ufields, r, army_name=mine) for r in units if r["army_name"] == name]
        crows += [cells(cfields, r, army_name=mine) for r in chars if r["army_name"] == name]

    for faction in HOUSES:
        battle, army = BATTLE + faction, ARMY + faction
        brows.append(cells(bfields, battle_donor, battle_name=battle))
        arows.append(cells(afields, army_donor, army_name=army, faction=faction))
        jrows.append([army, battle])
        jrows += [[name, battle] for name in shared]
        urows += [cells(ufields, r, army_name=army) for r in roster]

    made = {"battle_set_pieces_tables": (0, brows, bfields),
            "battle_set_piece_armies_tables": (1, arows, afields),
            "battle_set_piece_armies_junctions_tables": (0, jrows, jfields),
            "battle_set_piece_armies_units_junctions_tables": (0, urows, ufields),
            "battle_set_piece_armies_characters_junctions_tables": (1, crows, cfields)}
    return dict(("%s__%s.tsv" % (t, FRAG), tsv(t, v, rows, fields))
                for t, (v, rows, fields) in made.items())


def build_loc(base, missions_tsv):
    """Mission titles and descriptions, taken from the DB rows the game will not read.

    Rows in the base loc that are not missions_localised_* pass through untouched: the pack
    keeps one units_custom_battle_permissions override in this same file.
    """
    nl, tab = chr(10), chr(9)
    lines = base.rstrip(nl).split(nl)
    keep = [l for l in lines[2:]
            if l.strip() and not l.split(tab)[0].startswith("missions_localised_")]

    mlines = missions_tsv.rstrip(nl).split(nl)
    header = mlines[0].split(tab)
    cols = [("title", header.index("localised_title")),
            ("description", header.index("localised_description")),
            ("mission_completed_text",
             header.index("localised_mission_completed_text"))]
    k = header.index("key")

    rows = []
    for line in mlines[2:]:
        if not line.strip():
            continue
        r = line.split(tab)
        for field, col in cols:
            rows.append(tab.join(["missions_localised_%s_%s" % (field, r[k]),
                                  clean(r[col]), "false"]))

    return nl.join(lines[:2] + keep + rows) + nl


def clean(text):
    """Strip the two-character sequence backslash-n out of a loc value.

    CA writes it in the DB column and something in its pipeline turns it into a real line break.
    RPFM's TSV import does not: the panel drew a literal "\\n\\n" mid-sentence, seen in game
    2026-09-03. A TSV field cannot carry a raw newline either, so the paragraph break is spent
    rather than shown.
    """
    out = text
    while chr(92) + "n" in out:
        out = out.replace(chr(92) + "n" + chr(92) + "n", " ").replace(chr(92) + "n", " ")
    return " ".join(out.split())


START_TEMPLATE = '''-- Hellshard start missions: the first step of the Great Drill of Hashut.
--
-- GENERATED by tools/gen_hellshard_missions.py - edit the generator, not this file.
--
-- SHIPPED IN FOUR CAMPAIGN FOLDERS, byte-identical: cr_combi_expanded (Immortal Empires
-- Expanded), wh3_main_combi (Immortal Empires), cr_oldworld and cr_darklands. The engine loads
-- a campaign folder only for its own campaign - that is why CA's questline does not exist
-- outside Realms of Chaos - so a copy per campaign is the only way to be in all four. IEE loads
-- cr_combi_expanded AND wh3_main_combi and drops one of any repeated basename, which is
-- harmless only because the copies are identical; --selftest fails if they ever drift.
--
-- It replaces !!!narrative_chaos_dwarfs_new_factrions.lua, which did this job on the two Old
-- World maps through CA's chaos_dwarfs_narrative module. That module's own listeners register
-- only in Realms of Chaos, so the chain stopped one step in there; its hardcoded per-faction
-- drill coordinates are replaced by the runtime resolution below, which works on any map.
--
-- This file therefore names nothing of CA's. In particular it does NOT
-- require("wh3_dlc23_narrative_chaos_dwarfs"): that module is not on the script path when
-- cr_combi_expanded mod files load, and requiring it kills the whole file at load --
--   Failed to execute loaded mod file [...], error is:
--   module 'wh3_dlc23_narrative_chaos_dwarfs' not found
-- measured in game 2026-09-03. Covering CA's own three factions in multiplayer was the only
-- thing that needed the module, so they are left entirely to CA.

-- faction -> the missions_tables row to trigger. All eleven houses, on every map: the loop
-- below walks the campaign's own human factions, so an entry for a faction this campaign does
-- not place simply never matches. IEE places two of the ten houses (the tower seating script
-- logs "seated 2, skipped 8"), Immortal Empires places none of them and only the Conclave, and
-- the two Old World maps place all eleven.
local hellshard_starts = {
%s
}

-- Where to put the drill: near the faction's CAPITAL, resolved at runtime. Not hardcoded,
-- because a campaign may place a faction anywhere and fixed coordinates cannot track a
-- startpos, let alone four maps at once --
-- ime_derpy_black_dwarf.lua makes that argument at length. And not the faction leader's own
-- tile either, which is what this did first: Abnagg's leader is a naval horde and starts
-- AFLOAT, so the drill was built on the open sea (seen in game 2026-09-03). CA's own drill
-- sites are land tiles near the capital, which is what this reproduces.
local function drill_position(faction_key)
    -- cm:get_faction returns boolean false, not nil, for a faction this campaign lacks
    local faction = cm:get_faction(faction_key)
    if not faction or faction:is_null_interface() then
        return nil
    end

    local home = faction:home_region()
    if not home or home:is_null_interface() then
        return nil
    end

    -- 4th argument is `in same region`: the drill belongs inside the faction's own home region,
    -- which is the only thing that keeps a 10-tile preferred distance from putting it in a
    -- neighbour's province. The region key is returned so the log below names where it landed -
    -- a player reported the drill standing in someone else's capital on 2026-09-11 and there is
    -- no scripted way to ask which region a logical tile belongs to.
    local x, y = cm:find_valid_spawn_location_for_character_from_settlement(faction_key, home:name(), false, true, 10)
    if not x or x <= 0 then
        return nil
    end

    return x, y, home:name()
end

cm:add_first_tick_callback(function()
    if not cm:is_new_game() then
        return
    end

    cm:callback(
        function()
            local human_factions = cm:get_human_factions_of_subculture("wh3_dlc23_sc_chd_chaos_dwarfs")

            for i = 1, #human_factions do
                local faction_key = human_factions[i]
                local mission_key = hellshard_starts[faction_key]

                if mission_key then
                    local x, y, region = drill_position(faction_key)

                    -- the composite scene is decoration; never let it gate the mission
                    if x then
                        -- last arg is show_in_unseen_shroud. CA passes false because its own
                        -- drill sites sit inside the starting army's vision. Abnagg's does not: the
                        -- Warfleet owns Zermuda without seeing it at turn 1, and the drill then draws
                        -- nothing anywhere. Measured in game 2026-09-03.
                        cm:add_scripted_composite_scene_to_logical_position("drill_stage_00", "wh3_dlc23_hellshard_00", x, y, 0, 0, false, true, true);
                        -- derpy_chd_drill_chain.lua moves the drill through stages 01 and 02 and
                        -- has no way to work this out again on a later turn
                        cm:set_saved_value("derpy_drill_x", x)
                        cm:set_saved_value("derpy_drill_y", y)
                        out("XXX derpy_hellshard drill for " .. faction_key .. " at " .. x .. "," .. y .. " in " .. region .. " XXX")
                    else
                        out("XXX derpy_hellshard no drill position for " .. faction_key .. " - mission still triggered XXX")
                    end

                    out("XXX derpy_hellshard triggering " .. mission_key .. " for " .. faction_key .. " XXX")
                    cm:trigger_mission(faction_key, mission_key, true, true)
                end
            end
        end,
        2
    )
end)
'''


def staged(rel):
    """The on-disk path of an in-pack path."""
    return os.path.join(ROOT, "Modding Files", "pack", *rel.split("/"))


def build_start_lua():
    """The standalone trigger, written whole rather than patched into an existing file.

    Every house, every map. CA's own three factions are left out: their rows are CA's, the
    chain script's listener matches on the `_derpy_` prefix, and no unlock or finale row
    exists for them, so triggering theirs would start a questline that cannot continue.
    """
    entries = ['    ["%s"] = "%s%s",' % (faction, HELL, lord)
               for faction, _loc, lord, vanilla in STARTS if not vanilla]
    return START_TEMPLATE % "\n".join(entries)

def write():
    os.makedirs(SRC, exist_ok=True)
    base_path = os.path.join(SRC, "missions_tables__base.tsv")
    if not os.path.isfile(base_path):
        raise SystemExit("missing %s - export db/missions_tables/%s from the pack first"
                         % (base_path, FRAG))
    with io.open(base_path, encoding="utf-8") as fh:
        base = fh.read()

    out = {
        "missions_tables__%s.tsv" % FRAG: build_missions(base),
        "cdir_events_mission_option_junctions_tables__%s.tsv" % FRAG: build_options(),
        "cdir_events_mission_payloads_tables__%s.tsv" % FRAG: build_payloads(),
        "cdir_events_mission_issuer_junctions_tables__%s.tsv" % FRAG: build_issuers(),
    }
    out.update(build_battles())

    loc_base = os.path.join(SRC, "loc__base.tsv")
    if not os.path.isfile(loc_base):
        raise SystemExit("missing %s - export %s from the pack first" % (loc_base, LOC_PATH))
    with io.open(loc_base, encoding="utf-8") as fh:
        out["loc__%s.tsv" % FRAG] = build_loc(fh.read(), out["missions_tables__%s.tsv" % FRAG])

    for name, text in out.items():
        with io.open(os.path.join(SRC, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("  %5d rows  %s" % (len(text.rstrip("\n").split("\n")) - 2, name))

    text = build_start_lua()
    for rel in START_REL:
        path = staged(rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        print("  %5dB      %s" % (len(text), rel))

    # the chain is hand-written; the first path is the copy that is edited, the rest are made
    # from it so the four can never drift
    chain = staged(CHAIN_REL[0])
    if not os.path.isfile(chain):
        raise SystemExit("missing %s - the chain script is hand-written, not generated" % chain)
    with io.open(chain, encoding="utf-8", newline="") as fh:
        chain_text = fh.read()
    print("  %5dB      %s (hand-written)" % (len(chain_text), CHAIN_REL[0]))
    for rel in CHAIN_REL[1:]:
        path = staged(rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(chain_text)
        print("  %5dB      %s (copy)" % (len(chain_text), rel))

    for rel in DEAD_LUA_REL:
        path = staged(rel)
        if os.path.isfile(path):
            os.remove(path)
            print("  removed     %s" % rel)


# ---------------------------------------------------------------- RPFM MCP, raw HTTP
_sid = None


def _post(payload, headers):
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.headers, r.read().decode()


def _session():
    global _sid
    if _sid is None:
        h, _ = _post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                      "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                 "clientInfo": {"name": "py", "version": "1"}}}, HDR)
        _sid = h.get("mcp-session-id")
        _post({"jsonrpc": "2.0", "method": "notifications/initialized"},
              {**HDR, "mcp-session-id": _sid})
    return {**HDR, "mcp-session-id": _sid}


def call(tool, args):
    _, body = _post({"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                     "params": {"name": tool, "arguments": args}}, _session())
    for line in body.splitlines():
        if line.startswith("data: ") and line[6:].strip():
            d = json.loads(line[6:])
            if "error" in d:
                raise RuntimeError(d["error"])
            res = d["result"]
            if res.get("isError"):
                raise RuntimeError("%s: %s" % (tool, json.dumps(res)[:400]))
            return json.loads(res["content"][0]["text"])
    raise RuntimeError("no result: %s" % body[:300])


def check_keys():
    """Duplicated combined keys abort the run - the game drops the second row in silence."""
    bad = 0
    for table, ver in TABLES + BATTLE_TABLES:
        path = os.path.join(SRC, "%s__%s.tsv" % (table, FRAG))
        fields = call("definition_by_table_name_and_version",
                      {"name": table, "version": ver})["Definition"]["fields"]
        keys = [f["name"] for f in fields if f["is_key"]]
        with io.open(path, encoding="utf-8") as fh:
            cols = fh.readline().rstrip("\n").split("\t")
            fh.readline()
            idx = [cols.index(k) for k in keys if k in cols]
            if not idx:
                continue
            seen = {}
            for n, line in enumerate(fh, 3):
                row = line.rstrip("\n").split("\t")
                ck = tuple(row[i] for i in idx)
                if ck in seen:
                    print("  DUPLICATE KEY  %s  line %d and %d: %s"
                          % (table, n, seen[ck], "|".join(ck)))
                    bad += 1
                seen[ck] = n
    if bad:
        raise SystemExit("%d duplicated combined key(s) - nothing written." % bad)


def push():
    call("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": False})
    check_keys()
    pack = call("open_packfiles", {"paths": [PACK]})["StringContainerInfo"][0]
    for table, ver in TABLES + BATTLE_TABLES:
        path = "db/%s/%s" % (table, FRAG)
        tsv_path = os.path.join(SRC, "%s__%s.tsv" % (table, FRAG))
        if not call("packed_file_exists", {"pack_key": pack, "value": path})["Bool"]:
            call("new_packed_file", {"pack_key": pack, "path": path,
                                     "new_file": json.dumps({"DB": [FRAG, table, ver]})})
            print("  created  %s (v%d)" % (path, ver))
        call("import_tsv", {"pack_key": pack, "table_path": path, "tsv_path": tsv_path})
        print("  imported %s" % path)
    call("import_tsv", {"pack_key": pack, "table_path": LOC_PATH,
                        "tsv_path": os.path.join(SRC, "loc__%s.tsv" % FRAG)})
    print("  imported %s" % LOC_PATH)
    for rel in START_REL + CHAIN_REL:
        call("add_packed_files", {"pack_key": pack, "source_paths": [staged(rel)],
                                  "destination_paths": json.dumps([{"File": rel}])})
        print("  added    %s" % rel)
    for rel in DEAD_LUA_REL:
        if call("packed_file_exists", {"pack_key": pack, "value": rel})["Bool"]:
            call("delete_packed_files", {"pack_key": pack,
                                         "paths": json.dumps([{"File": rel}])})
            print("  deleted  %s" % rel)
    call("save_packfile", {"pack_key": pack})
    print("\nsaved %s" % PACK)


# ---------------------------------------------------------------------------- selftest


def _assert_panel_prefixes():
    """Every chain key must carry a prefix the Great Drill panel actually matches on.

    `chd_narrative_panel.twui.xml` has no Lua behind it - the whole panel is CCO expressions
    that test `MissionRecordContext.Key.Contains("<prefix>")`. A key that matches none of them
    leaves the panel drawing its own component names over an empty pane. Read out of the
    installed ui3.pack, not from a list copied into this file.
    """
    import struct
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from read_pack_index import read

    pack = os.path.join(GAME, "data", "ui3.pack")
    if not os.path.exists(pack):
        print("  (skipped panel check - no ui3.pack at %s)" % pack)
        return
    hits = read(pack, "chd_narrative_panel.twui.xml")
    assert hits, "chd_narrative_panel.twui.xml is not in ui3.pack any more"
    _path, comp, data = hits[0]
    if comp:
        import zstandard
        size = struct.unpack("<I", data[:4])[0]
        data = zstandard.ZstdDecompressor().decompress(data[4:], max_output_size=size)
    xml = data.decode("utf-8", errors="replace")
    wanted = re.findall(r'Key\.Contains\(\s*&quot;([^&]+)&quot;\s*\)', xml)
    assert wanted, "the panel no longer matches on Key.Contains - re-read it before trusting this"
    for label, key in (("hellshard", HELL), ("relics unlock", UNLOCK), ("final battle", FINALE)):
        assert any(key.startswith(w) for w in wanted), (
            "%s key %r matches none of the panel's prefixes %s - the Great Drill panel will "
            "draw an empty pane for it" % (label, key, sorted(set(wanted))))

    # The drill's own pin on the panel map comes from a script object, not from a mission row.
    # Read the key the panel asks for and assert the chain script registers exactly that; an
    # absent one is not an error in game, it draws the pin at the map origin.
    pin = re.findall(r'ScriptObjectContext\(Format\(\s*&quot;([^&%]+)%s&quot;', xml)
    assert pin, ("the panel no longer builds a ScriptObjectContext key with Format() - re-read "
                 "it before trusting this")
    with io.open(staged(CHAIN_REL[0]), encoding="utf-8", newline="") as fh:
        chain = fh.read()
    for prefix in set(pin):
        assert 'common.set_context_value("%s"' % prefix in chain, (
            "the panel reads script object %r and %s never sets it - the drill pin will draw at "
            "the map origin" % (prefix + "<faction>", CHAIN_REL[0]))


# The game ships Lua 5.1 and so does this machine; the harness below runs the shipped
# campaign script under it rather than reading the file and hoping.
LUA_EXE = r"C:\Program Files (x86)\Lua\5.1\lua.exe"

def _assert_relic_grant_is_gated():
    """One relic per quest battle: the script grant must be gated on this chain having issued it.

    CA's script/campaign/main_warhammer/wh3_dlc23_chaos_dwarf_relics.lua issues the three _ie
    relic missions on short-campaign victory, by cm:trigger_mission - so the DB row's own
    ADD_ANCILLARY payload fires. relic_won() pays the same ancillary by hand on the two paths
    where no dilemma is offered, because our own issuance is a mission STRING and carries no DB
    payload. Without the flag both ran on CA's route and the player got two of every major
    relic. Reported in play 2026-09-11.

    The ordering half of this check used to be textual - "the gate appears before
    add_ancillary_to_faction in the file" - and it broke the moment the payment moved into a
    helper declared above its caller, which is a refactor and not a defect. Ordering is now
    checked by running the script, which is the only way to ask the question that matters.
    """
    with io.open(staged(CHAIN_REL[0]), encoding="utf-8", newline="") as fh:
        chain = fh.read()
    flag = 'derpy_drill_issued_'
    assert 'cm:set_saved_value("%s" .. relic.mission' % flag in chain, (
        "issue_relic() no longer records %s* - relic_won() will do nothing" % flag)
    assert 'cm:get_saved_value("%s" .. mission_key)' % flag in chain, (
        "relic_won() no longer reads %s* - CA's own relic route will double every major "
        "relic" % flag)


def _assert_relic_dilemma_behaviour():
    """Run the shipped chain under Lua 5.1 and check the relic dilemma really works.

    tools/test_drill_relic_dilemma.lua stubs a campaign, loads the SHIPPED file and reads back
    what it did: the dilemma is offered under a key that exists (the three majors fight CA's _ie
    quest battles and the dilemmas table has no _ie rows), the script does not pay a reward the
    DB payload already pays, four bound relics issue the final battle, and - the one that bricks
    saves rather than merely misbehaving - the DilemmaChoiceMadeEvent condition REJECTS every
    dilemma that is not one of the eight vanilla relic ones. Matching a
    cm:create_dilemma_builder dilemma hard-crashes the game on click and this mod ships four of
    those, so a widened condition is not a style question.
    """
    harness = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "test_drill_relic_dilemma.lua")
    assert os.path.exists(harness), harness
    if not os.path.exists(LUA_EXE):
        print("  (skipped the Lua harness - no interpreter at %s)" % LUA_EXE)
        return
    r = subprocess.run([LUA_EXE, harness], capture_output=True, text=True,
                       cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assert r.returncode == 0, "test_drill_relic_dilemma.lua failed:\n%s%s" % (r.stdout, r.stderr)


def _selftest():
    base_path = os.path.join(SRC, "missions_tables__base.tsv")
    with io.open(base_path, encoding="utf-8") as fh:
        base = fh.read()

    out = build_missions(base)
    lines = out.rstrip("\n").split("\n")
    header = lines[0].split("\t")
    rows = [l.split("\t") for l in lines[2:]]
    k, img = header.index("key"), header.index("ui_image")
    keys = [r[k] for r in rows]

    assert len(keys) == len(set(keys)), "duplicate mission key"
    assert not any(x.startswith("h3_dlc23_") for x in keys), "typo'd key survived"
    assert not (set(keys) & DEAD_KEYS), (
        "a dead chain row survived: %s" % sorted(set(keys) & DEAD_KEYS))
    assert not any(r[img] == "chd/generic" for r in rows), "chd/generic survived"
    for r in rows:
        want = ART_HELLSHARD if r[k].startswith(HELL) else ART_BATTLE
        assert r[img] == want, "wrong art on %s" % r[k]
    for lord in LORDS:
        assert HELL + lord in keys, "no row for %s" % lord
    assert build_missions(out) == out, "build_missions is not idempotent"
    # the minted row differs from its donor in exactly one column
    donor = next(r for r in rows if r[k] == HELL + "derpy_tordrek")
    minted = next(r for r in rows if r[k] == HELL + "derpy_abnagg")
    diff = [header[i] for i in range(len(header)) if donor[i] != minted[i]]
    assert diff == ["key"], "minted row differs in %s" % diff

    # every mod-owned hellshard row is completely furnished, and only those
    opts = build_options().rstrip("\n").split("\n")[2:]
    pays = build_payloads().rstrip("\n").split("\n")[2:]
    isss = build_issuers().rstrip("\n").split("\n")[2:]
    chain_opts = sum(len(o) for _k, _d, o, _p in CHAIN_ROWS)
    chain_pays = sum(len(p) for _k, _d, _o, p in CHAIN_ROWS)
    assert len(opts) == 4 * len(LORDS) + chain_opts, len(opts)
    assert len(pays) == len(LORDS) + chain_pays, len(pays)
    assert len(isss) == len(LORDS) + len(CHAIN_ROWS), len(isss)
    ids = [l.split("\t")[0] for l in opts] + [l.split("\t")[0] for l in pays]
    assert len(ids) == len(set(ids)), "junction id collision"
    assert all(1 <= int(i) <= 2147483646 for i in ids), "junction id out of range"
    for lord in LORDS:
        got = [l.split("\t")[2] for l in opts if l.split("\t")[1] == HELL + lord]
        assert got == [o for o, _ in OPTIONS], "options wrong for %s" % lord
    assert all(BUILDING in l for l in opts if "VAR_OBJECTIVE_BUILDING_LEVEL" in l)

    # the Lua: every trigger pairs its own faction with a row that exists, all eleven houses
    lua = build_start_lua()
    assert lua.count("cm:trigger_mission(") == 1, "trigger should be table-driven"
    pairs = re.findall(r'\["([^"]+)"\] = "([^"]+)",', lua)
    assert len(pairs) == len(HOUSES), "%d entries, want %d" % (len(pairs), len(HOUSES))
    assert set(f for f, _ in pairs) == set(HOUSES), "the start script does not name every house"
    vanilla = {HELL + lord for _, _, lord, is_v in STARTS if is_v}
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from read_vanilla_cache import load as load_vanilla
    ca_keys = {r["key"] for r in load_vanilla("missions")[0]}
    assert vanilla <= ca_keys, "not in CA's missions: %s" % (vanilla - ca_keys)
    assert BUILDING in {r["level_name"] for r in load_vanilla("building_levels")[0]}
    assert REWARD.split("[")[1].split("]")[0] in {
        r["key"] for r in load_vanilla("effect_bundles")[0]}
    for faction, mission in pairs:
        assert mission in keys, "%s triggers %s, which has no row" % (faction, mission)
        # CA's own three lords have no unlock and no finale row, and the chain's listener
        # matches on the _derpy_ prefix, so starting their questline would strand them one
        # step in - worse than leaving them to CA
        assert mission not in vanilla, "%s is CA's own row and leads nowhere" % mission
    seen_missions = [m for _, m in pairs]
    assert len(seen_missions) == len(set(seen_missions)), "two factions share a mission row"
    for want in ("cr_chd_slaves_of_the_black_dwarf", "cr_chd_house_of_bzaark",
                 "cr_chd_warfleet_of_uzkulak", "cr_chd_black_kraken_armada"):
        assert want in [f for f, _ in pairs], "%s still not triggered" % want
    got = dict(pairs)
    assert got["cr_chd_house_of_bzaark"] == HELL + "derpy_bzaark"
    assert got["cr_chd_slaves_of_the_black_dwarf"] == HELL + "derpy_black_dwf"
    assert got["cr_chd_warfleet_of_uzkulak"] == HELL + "derpy_abnagg"
    assert got["cr_chd_black_kraken_armada"] == HELL + "derpy_tordrek"

    # the loc: the game reads titles and descriptions from HERE, not from the DB row
    with io.open(os.path.join(SRC, "loc__base.tsv"), encoding="utf-8") as fh:
        loc = build_loc(fh.read(), out)
    lrows = [l.split(chr(9)) for l in loc.rstrip(chr(10)).split(chr(10))[2:] if l.strip()]
    lmap = dict((r[0], r[1]) for r in lrows)
    assert len(lmap) == len(lrows), "duplicate loc key"
    for r in rows:
        assert lmap["missions_localised_title_" + r[k]] == r[header.index("localised_title")]
        assert "missions_localised_description_" + r[k] in lmap
        assert "missions_localised_mission_completed_text_" + r[k] in lmap
    bad = [x for x, v in lmap.items() if x.startswith("missions_") and v == "PLACEHOLDER"]
    assert not bad, "PLACEHOLDER survives on %d mission loc keys" % len(bad)
    assert not [x for x in lmap if "_h3_dlc23" in x], "typo key survives in the loc"
    assert [x for x in lmap if x.startswith("units_custom_battle")], "passthrough row lost"

    # no dependency on anything CA ships. Comments name these things; only real code matters.
    lua_code = "\n".join(l for l in lua.split("\n") if not l.lstrip().startswith("--"))
    assert "chaos_dwarfs_narrative" not in lua_code, "the start script touches CA's module"
    # THE bug of 2026-09-03: require() of a module that is not on cr_combi_expanded's script
    # path kills the entire file at load with "module ... not found". It is on cr_oldworld's,
    # which is why the file this replaces looked healthy there and still went nowhere.
    assert "require(" not in lua_code, "the start script requires a module; it must stand alone"
    assert "drill_position(faction_key)" in lua, "no runtime position fallback"
    # show_in_unseen_shroud must be true. A drill on a tile the faction owns but has not seen
    # draws nothing at all, and nothing errors - Abnagg, in game 2026-09-03.
    for call in re.findall(r"add_scripted_composite_scene_to_logical_position\([^)]*\)", lua):
        assert call.rstrip(")").endswith("false, true, true"), (
            "the start script hides the drill in unseen shroud: %s" % call)

    # Four campaign folders, byte-identical, and the two dead files gone. The engine loads a
    # campaign folder only for its own campaign, and IEE loads two of them and drops one of any
    # repeated basename - which is safe only while the copies match.
    for rel in START_REL:
        with io.open(staged(rel), encoding="utf-8", newline="") as fh:
            assert fh.read() == lua, "%s is not the file build_start_lua() writes" % rel
    with io.open(staged(CHAIN_REL[0]), encoding="utf-8", newline="") as fh:
        chain_master = fh.read()
    for rel in CHAIN_REL[1:]:
        with io.open(staged(rel), encoding="utf-8", newline="") as fh:
            assert fh.read() == chain_master, "%s has drifted from %s" % (rel, CHAIN_REL[0])
    for rel in DEAD_LUA_REL:
        assert not os.path.isfile(staged(rel)), (
            "%s is still staged - it triggers the same missions as the start script and would "
            "double every drill" % rel)

    # ------------------------------------------------------------ the rest of the drill chain
    lxi, lyi = header.index("location_x"), header.index("location_y")
    qci, spb = header.index("quest_character"), header.index("set_piece_battle")
    made = build_battles()

    def body(name):
        nl, tab = chr(10), chr(9)
        text = made["%s__%s.tsv" % (name, FRAG)]
        head = text.split(nl)[0].split(tab)
        return head, [l.split(tab) for l in text.rstrip(nl).split(nl)[2:] if l.strip()]

    bhead, brows = body("battle_set_pieces_tables")
    ahead, arows = body("battle_set_piece_armies_tables")
    _jhead, jrows = body("battle_set_piece_armies_junctions_tables")
    uhead, urows = body("battle_set_piece_armies_units_junctions_tables")

    battles = {r["battle_name"] for r in load_vanilla("battle_set_pieces")[0]}
    battles |= {r[bhead.index("battle_name")] for r in brows}
    for key, _donor, _o, _p in CHAIN_ROWS:
        row = next((r for r in rows if r[k] == key), None)
        assert row is not None, "no row for %s" % key
        # a coordinate copied off CA's lords names nothing for a house that starts elsewhere
        assert (row[lxi], row[lyi]) == BATTLE_LOC, "%s is not at the drill site" % key
        assert row[lxi] != "0" and row[lyi] != "0", (
            "%s sits on the map origin - the teleport lands in the corner" % key)
        assert (int(row[lxi]) <= VANILLA_LOC_MAX[0]
                and int(row[lyi]) <= VANILLA_LOC_MAX[1]), (
            "%s is outside the envelope every vanilla location fits in (%d, %d) - these "
            "columns are display coordinates, so this looks like a logical one"
            % ((key,) + VANILLA_LOC_MAX))
        # CA's value is a command queue index out of its own save
        assert row[qci] == "", "%s carries a quest_character" % key
        assert row[spb] in battles, "%s -> unknown set piece battle %s" % (key, row[spb])
        if key.startswith(FINALE):
            want = BATTLE + key[len(FINALE):]
            assert row[spb] == want, "%s -> %s, want %s" % (key, row[spb], want)
        assert any(l.split("\t")[1] == key for l in pays), "%s has no payload" % key
        assert any(l.split("\t")[1] == key for l in isss), "%s has no issuer" % key

    # the chain script: hand-written, so every key it names is checked against the game here.
    # A faction, region, ancillary or bundle typo fails silently forever otherwise.
    with io.open(staged(CHAIN_REL[0]), encoding="utf-8", newline="") as fh:
        chain = fh.read()
    assert 'UNLOCK_MISSION = "%s"' % UNLOCK in chain, "chain script names another unlock row"
    assert 'FINAL_MISSION_PREFIX = "%s"' % FINALE in chain, "chain names another final row"
    assert "require(" not in chain, "chain script must be self-contained"

    # unique: the three majors are named twice, once in RELICS and once in MAJOR_RELIC_COUNTERS
    relic_missions = set(re.findall(r'mission = "(wh3_dlc23_chd_ancestor_relic_of_\w+)"', chain))
    assert len(relic_missions) == 8, "%d relic missions, want 8" % len(relic_missions)
    assert relic_missions <= ca_keys, (
        "not in CA's missions: %s" % (relic_missions - ca_keys))
    for name in re.findall(r'set_piece_battle (\S+)"', chain):
        assert name in battles, "unknown set piece battle %s" % name

    # The three lesser relics are region captures, and every map names those regions
    # differently. Each names one key per map and the chain picks the one that resolves, so
    # both halves have to be real: the Immortal Empires key against CA's own tables, the Old
    # World key against the campaign pack that mints it - byte-scanned, since a mod pack's DB
    # is not in the vanilla cache, and skipped when that pack is not installed.
    combi = {r["region"] for r in load_vanilla("campaign_map_regions")[0]
             if r["campaign_map"].startswith("wh3_main_combi_map")}
    blocks = re.findall(r"regions = \{(.*?)\}", chain, re.S)
    assert len(blocks) == 3, "%d region-capture relics, want 3" % len(blocks)
    old_world = []
    for block in blocks:
        keys = re.findall(r'"([^"]+)"', block)
        assert len(keys) == 2, "want one region key per map, got %s" % keys
        assert keys[0].startswith("wh3_main_combi_region_"), (
            "%s is not an Immortal Empires key" % keys[0])
        assert keys[0] in combi, "%s is on no Immortal Empires map" % keys[0]
        assert keys[1].startswith("cr_oldworld_region_"), (
            "%s is not an Old World key - the Darklands map uses the same prefix" % keys[1])
        old_world.append(keys[1])
    assert len(set(old_world)) == 3, "two relics share an Old World region"
    ow_pack = os.path.join(GAME, "..", "..", "workshop", "content", "1142710", "3081800026",
                           "!cr_oldworld_campaign.pack")
    if os.path.isfile(ow_pack):
        with io.open(ow_pack, "rb") as fh:
            blob = fh.read()
        for key in old_world:
            assert key.encode() in blob, "%s is in no Old World campaign table" % key
    else:
        print("  (skipped Old World region check - !cr_oldworld_campaign.pack not installed)")
    assert "live_region(relic.regions)" in chain, (
        "the chain no longer picks a region key per map; on the Old World maps the three "
        "lesser relics would name regions that are not there and fail in silence")

    ancs = {r["key"] for r in load_vanilla("ancillaries")[0]}
    for a in re.findall(r'ancillary = "(\S+)"', chain):
        assert a in ancs, "unknown ancillary %s" % a
    bundles = {r["key"] for r in load_vanilla("effect_bundles")[0]}
    for b in re.findall(r'(?:reward|bundle) = "(\S+)"', chain):
        assert b in bundles, "unknown effect bundle %s" % b
    facs = {r["key"] for r in load_vanilla("factions")[0]}
    for fkey in re.findall(r'faction = "(\S+)"', chain):
        assert fkey in facs, "unknown faction %s" % fkey
    # the relic armies name a *list* of candidate rogue factions, so the singular pattern above
    # walks straight past them - every one still has to be a real key
    lists = re.findall(r"factions = \{(.*?)\}", chain, re.S)
    assert len(lists) == 2, "expected two relic-army candidate lists, found %d" % len(lists)
    # The lists overlap, so the two relics have to claim FORCES and not factions - without this
    # both ended up on one army and one kill settled both. Measured 2026-09-04.
    # the guardian the chain builds when no rogue faction will take one. Its faction has to be
    # a real, non-rogue key that exists in every campaign - that is the whole point of it - and
    # every unit key has to be in main_units, since cm:create_force fails on a typo in silence.
    guardian = re.search(r'GUARDIAN_FACTION = "([^"]+)"', chain)
    assert guardian, "the chain script no longer names a guardian faction"
    assert guardian.group(1) in facs, "unknown guardian faction %s" % guardian.group(1)
    assert "_rogue_" not in guardian.group(1), (
        "the guardian faction is a rogue one (%s) - those are spawned per campaign and are "
        "exactly what it exists to avoid" % guardian.group(1))
    units_block = re.search(r"GUARDIAN_UNITS = table\.concat\(\{(.*?)\}", chain, re.S)
    assert units_block, "the chain script no longer names a guardian roster"
    guardian_units = re.findall(r'"([^"]+)"', units_block.group(1))
    assert len(guardian_units) >= 15, "%d guardian units, want a real army" % len(guardian_units)
    main_units = {r["unit"] for r in load_vanilla("main_units")[0]}
    for u in guardian_units:
        assert u in main_units, "guardian unit %s is not in main_units" % u

    # the survival battle reads three saved strings and freezes on wave 1 if any is missing -
    # see the comment above MAJOR_RELIC_COUNTERS in the chain script. Both the battle-key prefix
    # and the three (mission, counter) pairs have to stay true, and only this side knows the
    # battle keys it writes.
    assert 'FINAL_BATTLE_PREFIX = "%s"' % BATTLE in chain, (
        "the chain script watches another battle key prefix than the rows name")
    for god in ("grimnir", "grungni", "valaya"):
        pair = ('{mission = "wh3_dlc23_chd_ancestor_relic_of_%s_ie", '
                'counter = "relic_of_%s_bound"}' % (god, god))
        assert pair in chain, "no relic counter written for %s: %s" % (god, pair)
    assert "core:svr_save_string(m.counter" in chain, (
        "the relic counters are no longer written with core:svr_save_string")

    assert "local function free_force(faction, taken)" in chain, (
        "the relic armies no longer claim a force each")
    assert "relic_army_force(faction_key, army, taken)" in chain, (
        "relic_army_force is not being passed the claimed-force set")
    for block in lists:
        keys = re.findall(r'"([^"]+)"', block)
        assert len(keys) >= 2, "a relic army has no fallback candidate: %s" % keys
        for fkey in keys:
            assert fkey in facs, "unknown rogue faction %s" % fkey
    scenes = {r["id"] for r in load_vanilla("campaign_composite_scenes")[0]}
    for stage in ("00", "01", "02"):
        assert "wh3_dlc23_hellshard_" + stage in scenes, "no composite scene for stage " + stage

    _assert_panel_prefixes()
    _assert_relic_grant_is_gated()
    _assert_relic_dilemma_behaviour()

    # the relics-unlock battle. Every faction an army of ours sits in must exist in the
    # campaign, or the battle cannot be built and the right-click does nothing at all - the
    # fault that cost three deploys. Checked against CA's own usage: a faction is safe if some
    # vanilla battle army already uses it AND it is not a rogue-army faction, rogue factions
    # being spawned per campaign rather than present in every startpos.
    van_army_rows = load_vanilla("battle_set_piece_armies")[0]
    van_factions = {r["faction"] for r in van_army_rows}
    ub = next(r for r in brows if r[bhead.index("battle_name")] == UNLOCK_BATTLE)
    donor_b = next(r for r in load_vanilla("battle_set_pieces")[0]
                   if r["battle_name"] == UNLOCK_BATTLE_DONOR)
    for field in bhead:
        if field == "battle_name":
            continue
        want = donor_b[field]
        want = ("true" if want else "false") if isinstance(want, bool) else str(want)
        assert ub[bhead.index(field)] == want, (
            "%s.%s drifted from CA's row: %s vs %s"
            % (UNLOCK_BATTLE, field, ub[bhead.index(field)], want))

    unlock_j = [r for r in jrows if r[1] == UNLOCK_BATTLE]
    assert len(unlock_j) == 5, "%s has %d armies, CA's has 5" % (UNLOCK_BATTLE, len(unlock_j))
    by_army = {r[ahead.index("army_name")]: r for r in arows}
    for name, _battle in unlock_j:
        row = by_army.get(name)
        faction = row[ahead.index("faction")] if row else next(
            r["faction"] for r in van_army_rows if r["army_name"] == name)
        assert faction in van_factions, "unknown battle faction %s on %s" % (faction, name)
        assert "_rogue_" not in faction, (
            "%s sits in rogue faction %s, which is spawned per campaign and absent from "
            "Immortal Empires - the battle will refuse to launch, in silence" % (name, faction))
    assert not any(r[ahead.index("faction")] == UNLOCK_ABSENT_FACTION for r in arows), (
        "an army still belongs to %s" % UNLOCK_ABSENT_FACTION)
    # a re-homed army keeps its units and its characters, or it deploys empty
    for name in by_army:
        if not name.startswith(UNLOCK_ARMY):
            continue
        donor = UNLOCK_BATTLE_DONOR.replace("_relic_army_uncovered", "") and next(
            r["army_name"] for r in van_army_rows
            if r["army_name"].endswith(name[len(UNLOCK_ARMY):])
            and r["faction"] == UNLOCK_ABSENT_FACTION)
        want_u = sum(1 for r in load_vanilla("battle_set_piece_armies_units_junctions")[0]
                     if r["army_name"] == donor)
        got_u = sum(1 for r in urows if r[0] == name)
        assert got_u == want_u, "%s has %d units, %s has %d" % (name, got_u, donor, want_u)

    # the mission must point at our clone, never at CA's unbuildable original
    urow = next(r for r in rows if r[k] == UNLOCK)
    assert urow[spb] == UNLOCK_BATTLE, "%s still points at %s" % (UNLOCK, urow[spb])
    assert UNLOCK_BATTLE_DONOR not in [r[spb] for r in rows], (
        "a mission still points at CA's unbuildable battle")

    # one battle, one reinforcement army and one roster per house, and the army must belong to
    # the house or the wave arrives in somebody else's colours - the whole point of the clone
    # +1 battle for the relics-unlock clone, +4 armies for its re-homed dwarf throng
    assert len(brows) == len(HOUSES) + 1 and len(arows) == len(HOUSES) + 4
    van_units = {r["unit_name"] for r in load_vanilla("battle_set_piece_armies_units")[0]}
    van_armies = {r["army_name"] for r in load_vanilla("battle_set_piece_armies")[0]}
    house_urows = [r for r in urows if not r[0].startswith(UNLOCK_ARMY)]
    urows = house_urows
    roster_size = len(urows) // len(HOUSES)
    assert roster_size * len(HOUSES) == len(urows), "ragged reinforcement rosters"
    for faction in HOUSES:
        battle, army = BATTLE + faction, ARMY + faction
        arow = next(r for r in arows if r[ahead.index("army_name")] == army)
        assert arow[ahead.index("faction")] == faction, "%s wears %s colours" % (
            army, arow[ahead.index("faction")])
        assert arow[ahead.index("is_allied_to_player")] == "true"
        assert arow[ahead.index("override_uniform_colours")] == "false", (
            "%s overrides the colours the faction supplies" % army)
        mine = [r for r in jrows if r[1] == battle]
        assert len(mine) == 21, "%s has %d armies, CA's donor has 21" % (battle, len(mine))
        assert sum(1 for r in mine if r[0] == army) == 1, "%s has no wave of its own" % battle
        assert ARMY_DONOR not in [r[0] for r in mine], "%s still pulls CA's wave" % battle
        for name in (r[0] for r in mine):
            assert name == army or name in van_armies, "unknown army %s" % name
        rows_ = [r for r in urows if r[0] == army]
        assert len(rows_) == roster_size, "%s roster is %d" % (army, len(rows_))
        for r in rows_:
            assert r[uhead.index("unit_name")] in van_units, "unknown unit %s" % r[1]
    assert len({r[0] for r in urows}) == len(HOUSES)

    # the escape CA writes in its DB column and RPFM does not unescape - it drew literally
    loc_base = os.path.join(SRC, "loc__base.tsv")
    with io.open(loc_base, encoding="utf-8") as fh:
        loc = build_loc(fh.read(), out)
    assert chr(92) + "n" not in loc, "a literal backslash-n reached the loc"
    assert "The Great Drill of Hashut" in loc, "the mission title is not in the loc"

    print("selftest ok - %d mission rows, %d option, %d payload, %d issuer, %d triggers, "
          "%d relic missions, %d campaign folders"
          % (len(rows), len(opts), len(pays), len(isss), len(pairs),
             len(relic_missions), len(CAMPAIGNS)))




if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        write()
        if "--check" not in sys.argv:
            try:
                push()
            except urllib.error.URLError:
                sys.exit("RPFM is not running - its MCP server only exists while RPFM is open")
