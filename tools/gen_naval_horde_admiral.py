"""Characters for the naval horde: heroes on Abnagg's ship, and a recruitable Fleetmaster.

Two halves, both asked for as "recruitment of lords and heroes under Abnagg".

HEROES are an effect, not a `building_units_allowed` row. Lords and heroes never appear in
that table - 0 of 6,396 vanilla rows have a `lord` or `hero` caste. A building enables a hero
with `<race>_effect_agent_enable_recruitment_<agent>_<culture>` and pays for the slot with
`..._agent_cap_increase_...`. Chaos Dwarfs already have all six keys in vanilla, so this half
authors no effects at all - it is 15 `building_effects_junction` rows.

The scope is the whole trick and it is not the one CHD's own settlements use. Of the 509
vanilla enable rows, 396 sit at `province_to_province_own_unseen` (settlements, including
CHD's own military buildings) and 98 at `force_to_force_own` - and every one of those 98 is a
HORDE building: Vampire Coast ships, Lizardmen and Beastmen and Dark Elf hordes, Ogre camps,
Malakai's airship, the High Elf dragonships. A horde has no province, so the settlement scope
would apply to nothing, silently. Caps go the other way: `faction_to_faction_own_unseen`, which
is what all three character-bound-horde precedents use.

LORDS have no such effect. Re-checking all 106 `agent_enable_recruitment` keys in the game and
bucketing them by agent-type token gives champion, engineer, wizard, dignitary, runesmith, spy,
exalted, sorcerer, amethyst, mist and the race-prefixed rest - and nothing for `general`, which
is the agent type lords are. So a building cannot make a lord recruitable, and the only route
to "recruit a lord" is a new lord. CA's own precedent for a lord who founds a ship is
`wh2_dlc11_cst_admiral_tech_01..04`: an ordinary generic lord subtype listed in the campaign
group that `agent_subtype_military_force_creation_overrides` binds to the ship force type. This
pack already owns that whole apparatus - force type `DERPY_CHD_NAVAL_HORDE`, group
`derpy_chd_naval_horde_agents` - with Abnagg and Tordrek as its only two members. The
Fleetmaster becomes the third.

He gets his own six chains because the roster chains are gated one-lord-each by
`building_chains.optional_required_horde_commander`, so a third lord sharing the ungated
flagship/sail/helm/anchor would sail a ship that can build but recruit nothing. His roster is
deliberately the junior one: hobgoblin-heavy, `main_units.tier <= 3`, three levels per chain
instead of four, and none of the elites that top out Abnagg's ladder (no k'daai, no bale
taurus, no dreadquake, no hellcannon) - and no Vampire Coast at all, which is Tordrek's.

Authors no art and no skills. The three art sets point `agent_uniforms` at CA's existing
`wh3_dlc23_chd_overseer_campaign_0N` files, and the skill node set is CA's 73 Overseer nodes
listed into a set of our own - legal because a node is freely shared between sets in vanilla
(1,995 nodes sit in more than one, and one sits in 535).

Rewrites the EXPORTED TSVs in place, the way gen_naval_horde_tordrek.py does, so rows this
script does not own cannot be lost when import_tsv replaces the whole file.

    py tools/gen_naval_horde_admiral.py            rewrite the TSVs
    py tools/gen_naval_horde_admiral.py --check    checks only, write nothing
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "Modding Files", "source", "naval_horde", "export")
sys.path.insert(0, os.path.join(ROOT, "tools"))

ABNAGG_CHAINS = "derpy_chd_naval_horde"        # the shared prefix, gated to derpy_abnagg
KRAKEN_CHAINS = "derpy_chd_naval_kraken"       # Tordrek's fork, gated to derpy_tordrek
NEW = "derpy_chd_naval_admiral"                # the Fleetmaster's fork
LORD = "derpy_chd_admiral"
ABNAGG = "derpy_abnagg"
TORDREK = "derpy_tordrek"
FACTION = "cr_chd_warfleet_of_uzkulak"         # Abnagg's faction, from derpy_start_abnagg.lua
TORDREK_FACTION = "cr_chd_black_kraken_armada"  # from derpy_start_tordrek.lua

C = "wh3_dlc23_chd_"

# --------------------------------------------------------------------------- heroes

# Chaos Dwarfs have exactly three enable keys and three cap keys in vanilla. Note the enable
# is CHAMPIONS and the cap is CHAMPION - CA's own inconsistency, and a silent no-op if copied
# across.
HERO_ENABLE = {
    "wizard": "wh3_dlc23_effect_agent_enable_recruitment_wizard_chaos_dwarfs",
    "engineer": "wh3_dlc23_effect_agent_enable_recruitment_engineer_chaos_dwarfs",
    "champion": "wh3_dlc23_effect_agent_enable_recruitment_champions_chaos_dwarfs",
}
HERO_CAP = {
    "wizard": "wh3_dlc23_effect_agent_cap_increase_wizard_chaos_dwarfs",
    "engineer": "wh3_dlc23_effect_agent_cap_increase_engineer_chaos_dwarfs",
    "champion": "wh3_dlc23_effect_agent_cap_increase_champion_chaos_dwarfs",
}
ENABLE_SCOPE = "force_to_force_own"                 # 98/98 vanilla horde rows
CAP_SCOPE = "faction_to_faction_own_unseen"         # all three ship precedents

# An enable effect opens a recruitment slot; it does not decide WHAT may go in it. That is
# `faction_agent_permitted_subtypes`, and Abnagg's faction had one row in it - Abnagg. So did
# every other custom house: one row each, their own legendary lord, no hero of any kind and no
# generic lord. CA gives each of its own Chaos Dwarf factions 15 rows, so this is a per-faction
# gate with no culture-wide fallback, and without these six the three effects above would light
# up a panel with nothing in it. CHD's spy is Gorduz, a named character, and `colonel` is an
# internal type - neither has an enable effect on the ship, so neither is granted here.
HERO_SUBTYPES = [
    ("champion", C + "bull_centaur_taurruk"),
    ("engineer", C + "infernal_castellan"),
    ("wizard", C + "daemonsmith_sorcerer_death"),
    ("wizard", C + "daemonsmith_sorcerer_fire"),
    ("wizard", C + "daemonsmith_sorcerer_hashut"),
    ("wizard", C + "daemonsmith_sorcerer_metal"),
]

# Only Abnagg-gated chains, so none of this reaches Tordrek. VC hangs its third hero on
# captains_cabin, which maps to our flagship - and flagship is SHARED and ungated, so the
# wizard moves to crows_nest instead. gunports->engineer and hold->champion are CA's own
# mapping kept intact.
#   (chain, agent, [levels that enable], {level: cap value})
HEROES = [
    ("crows_nest", "wizard", [2, 3, 4], {3: 1, 4: 2}),
    ("gunports", "engineer", [2, 3, 4], {3: 1, 4: 2}),
    ("hold", "champion", [2, 3], {3: 1}),
]

# Tordrek had no hero of any kind: the comment above is why - the effects had to stay off the
# shared flagship chain, and at the time his own chains did not exist. They do now, and
# `derpy_chd_naval_kraken_*` is gated to derpy_tordrek (check() proves it), so an effect here
# reaches him and nobody else. Same chain and same levels as Abnagg's engineer, so the two ships
# read alike. These rows are authored HERE rather than in gen_naval_horde_tordrek.py because
# block 7 below strips every hero effect row in the file and rewrites it - a kraken row added by
# that generator would be deleted by the next run of this one.
KRAKEN_HEROES = [
    ("gunports", "engineer", [2, 3, 4], {3: 1, 4: 2}),
]

# One enable effect opens the engineer slot; `faction_agent_permitted_subtypes` decides what is
# in it. !cr_oldworld_campaign.pack already permits the Infernal Castellan for Tordrek's faction
# (check_oldworld_permissions proves it), so the Castellan needs no row.
#
# The Gunnery Wight is CA's OWN subtype, permitted to Tordrek's faction. It used to be a
# duplicate under derpy_ keys - land unit, main unit, variant, abilities, agent subtype, five art
# sets and a skill node set - and every one of those rows read correct against CA's, yet the clone
# came out of the panel with a placeholder porthole, a placeholder unit card, Chaos Dwarf names
# and no skill tree at all (SkillList.Size 0, against 41 on the Infernal Castellan standing beside
# it; measured over the wh3 bridge 2026-09-02). Two of those are structural, not fixable in DB:
#   * portholes and unit cards are NOT read from campaign_character_arts - `portrait` and `card`
#     are empty on all 1,495 vanilla rows. They come out of ui/portraits/{portholes,units}/
#     portrait_settings__.bin, a binary keyed by ART_SET_ID, so a new art set id has no image
#     anywhere in the game and every panel falls back to the placeholder.
#   * the skill tree never bound, with character_skill_node_sets and _set_items rows matching CA's
#     field for field, the nodes all present in character_skill_nodes and agent_key resolved.
# Granting CA's subtype takes all of that from CA for free, and costs nothing in DLC terms: the
# clone still pointed at CA's variantmesh, entity and animations, so it was never playable without
# Curse of the Vampire Coast anyway, and agent_subtype_ownership_content_pack_junctions carries no
# row for the wight at all.
#
# The one thing CA's row does not supply is the name: names_group is empty there, so inside a
# Chaos Dwarf faction the wight is christened out of names_chd_chaos_dwarfs. Block 19 rewrites
# CA's row with names_group set - the lever wh3_dlc23_chd_bull_centaur_taurruk uses to get bull
# centaur names inside a Chaos Dwarf faction - which is a no-op for Vampire Coast factions, where
# that is already the group the faction itself supplies.
WIGHT_DONOR_SUBTYPE = "wh2_dlc11_cst_gunnery_wight"
WIGHT_SUBTYPE = WIGHT_DONOR_SUBTYPE
WIGHT_UNIT = "wh2_dlc11_cst_cha_gunnery_wight_0"
WIGHT_NAMES = "names_cst_vampire_coast"
# ...and the voice. Every agent action plays a VO line, and the engine resolves the actor group
# inside the VO culture of the character's FACTION - Chaos Dwarfs here, which has never heard of
# wh2_dlc11_vo_actor_VampireCoast_Gunnery_Wight. Measured 2026-09-02: with this empty, the wight
# could move and be recruited but every hero action (Training, Scout Ruins, Block Army, Wound) and
# the army embed were discarded by the engine without spending an action point, while the Infernal
# Castellan beside it worked. This is the column CA sets on every foreign-culture agent -
# wh3_dlc23_chd_gorduz_backstabber, a Hobgoblin inside this same Chaos Dwarf culture, sets
# wh3_dlc23_vo_culture_Hobgoblins; so do Grom, the River Troll Hag, the Tiger Warriors and every
# Daemon Prince. 150 of CA's 613 subtype rows carry it and every one is that same shape.
WIGHT_VO_CULTURE = "wh2_dlc11_vo_culture_Vampire_Coast"
# ...and the culture's unit list. agent_culture_details is NOT unique on (agent, culture) - its
# primary key is the numeric `key` column, and the table enumerates one row per
# (agent type, culture, unit) the culture may field. The Chaos Dwarf `engineer` entry lists exactly
# one unit, the Infernal Castellan's; the Gunnery Wight's unit is not in it, and every cross-race
# hero mod installed here ships this table for that reason - alshua_cultists adds
# (dignitary, wh_main_chs_chaos, kho_brass_cultist), (champion, wh3_main_dae_daemons,
# wh3_main_sla_cha_cultist_0) and nine more of exactly that shape. Ours is CA's own
# (engineer, wh2_dlc11_cst_vampire_coast) row with the culture swapped to Chaos Dwarfs.
WIGHT_CULTURE = "wh3_dlc23_chd_chaos_dwarfs"
WIGHT_DONOR_CULTURE = "wh2_dlc11_cst_vampire_coast"
# Numeric primary key. Checked free against vanilla's 186 rows AND every agent_culture_details row
# in the 17 installed mods that ship the table (436 keys in use); a duplicate drops a row in
# silence. crc32("derpy_chd_naval_horde_wight_engineer") & 0x3FFFFFFF.
WIGHT_CULTURE_KEY = "634426295"
WIGHT_CULTURE_KEY_DONOR = "1928090079"        # CA's (engineer, wh2_dlc11_cst_vampire_coast) row
# What the clone owned. Kept only so a regeneration prunes it: a generator removes exactly the
# keys it currently writes, so a key it stops writing survives forever unless it is listed here.
STALE_WIGHT = ["derpy_chd_gunnery_wight", "derpy_chd_cha_gunnery_wight_0"]
TORDREK_HERO_SUBTYPES = [("engineer", WIGHT_SUBTYPE)]

# ...and the switch that is OFF. The wight recruited, walked and levelled, but every hero action
# it dispatched was discarded by the engine before the model saw it - Training on its own lord,
# Scout Ruins, Block Army, Wound and the army embed all clicked, closed the panel, spent no
# action point and no gold, while CA's Infernal Castellan standing beside it did all five.
# Two candidate causes were fixed and NEITHER moved it: audio_vo_culture_override (2026-09-02,
# section 16 of the handoff) and the agent_culture_details row above (section 17). Rather than
# ship a hero that cannot act, the grant is withdrawn. Everything it needs is still written
# below and gated on this one flag, so putting it back is a one-line change once the real cause
# is found. See docs/sessions/HANDOFF_20260902_NAVAL_HORDE_LIVE_VERIFY.md sections 14-17 for
# what is already eliminated, and section 18 for where to look next.
WIGHT_ENABLED = False

# --------------------------------------------------------------------------- the Fleetmaster

ART_SETS = 3                                   # CA ships three Overseer art sets; mirror them
DONOR_ART = "wh3_dlc23_chd_overseer_campaign_%02d"
DONOR_UNIT = C + "cha_overseer"
DONOR_VO = "wh3_dlc23_vo_actor_Chaos_Dwarf_Overseer"

# campaign_character_arts is what actually dresses the character, and an art set with no row here
# renders a DEFAULT HUMAN, not nothing - the Fleetmaster shipped once as a High Elf because of it.
# All three values are CA's own on wh3_dlc23_art_set_chd_overseer_0N. sea/navy uniform is the
# Chaos Dwarf ship the horde shows on the map; Abnagg and Tordrek have private ones, this is the
# generic.
DONOR_SEA_UNIFORM = "wh3_dlc23_uniform_chd_ship_lord"
DONOR_LAND_ANIM = "cam_hu3_dwarf_axe_and_shield"
DONOR_SHIP_ANIM = "cam_chaosdwarfsship_01"
ARTS_ID_BASE = 696991601                       # the 13 LL rows run 696991588..696991600
DONOR_SKILL_SET = "wh3_dlc23_skill_node_set_chd_overseer"
SKILL_SET = LORD + "_skills"
GROUP = "derpy_chd_naval_horde_agents"
MEMBER = GROUP + "_admiral"
# recruitment_category IS the tab in the lord recruitment panel. Reusing CA's overseer
# category put the Fleetmaster inside the Overseer group with no tab of his own; every
# ship-founding lord CA ships has a private one instead (cst_legendary_admirals,
# cst_vampire_fleet_admiral, wh3_dlc27_hef_dragonships), so this declares one.
# A category may hold many subtypes - vmp_bloodlines holds five - so sharing was legal,
# just not what a ship-founder looks like.
OWN_CATEGORY = "derpy_chd_fleetmaster"
CATEGORY_ORDER = 4                             # CHD uses 0 prophet / 1 overseer / 3 convoy
CATEGORY_ICON = "UI\\Common UI\\unit_category_icons\\wh3_dlc27_hef_dragonship.png"

# 2026-09-02: the private category shipped and NO tab appeared - the turn-1 screenshot shows only
# Sorcerer-Prophet / Legendary Lords / Overseer. The row is structurally identical to
# wh3_dlc27_hef_dragonships (same icon; order 4, which 14 vanilla rows also use), so the row is
# not obviously the fault - but it is the last untested variable. Park it and put the admiral in
# CA's overseer category, which is PROVEN to render for this faction, then disable the vanilla
# overseer for Abnagg's faction so that tab holds admirals only. Flip this one line back to
# OWN_CATEGORY once cards are confirmed to draw; the parked row and its two loc rows are still
# generated, and an unreferenced category is inert.
RECRUITMENT_CATEGORY = "wh3_dlc23_chd_overseer"

# Everything else is deliberately the overseer's, so "horde lord" is the ONLY difference left -
# the user asked for same models, same art. That now includes AUTO_GENERATE: see the comment on
# the agent_subtypes row below, and HANDOFF_20260902 section 9.9 for the panel dump that settled it.
AUTO_GENERATE = "true"                         # was false; the overseer is true and must match
COST = 1500                                    # was 1800; match the overseer exactly
CAN_BE_LOANED = "true"                         # was false; the overseer is true

# --------------------------------------------------------------------------- his six chains

CHAINS = ["main_deck", "gunports", "crows_nest", "cannons", "hold", "hull"]
LEVELS = {c: 3 for c in CHAINS}

# What each level ADDS; build() accumulates. Nothing above main_units.tier 3, and none of the
# six units that top out Abnagg's ship.
NEW_AT = {
    "main_deck": {
        1: [C + "inf_hobgoblin_cutthroats"],
        2: [C + "inf_chaos_dwarf_warriors"],
        3: [C + "inf_chaos_dwarf_warriors_great_weapons"],
    },
    "gunports": {
        1: [C + "inf_hobgoblin_archers"],
        2: [C + "inf_chaos_dwarf_blunderbusses"],
        3: [C + "inf_infernal_guard_fireglaives"],
    },
    "crows_nest": {
        1: [C + "inf_hobgoblin_sneaky_gits"],
        2: [C + "mon_lammasu"],
        3: [C + "mon_great_taurus"],
    },
    "cannons": {
        1: [C + "veh_magma_cannon"],
        2: [C + "veh_deathshrieker_rocket_launcher"],
    },
    "hold": {
        1: [C + "inf_goblin_labourers", C + "inf_orc_labourers"],
        2: [C + "cav_hobgoblin_wolf_raiders_bows", C + "cav_hobgoblin_wolf_raiders_spears"],
        3: [C + "cav_bull_centaurs_axe"],
    },
    # hull_1 is primreq 0 / cost 1000, so this grant is available turn one - deliberate for the
    # bolt thrower, the one war engine cheap enough to be a starting piece. Abnagg matches.
    "hull": {
        1: ["wh3_main_chd_art_hobgob_bolt_thrower"],
        2: [C + "veh_iron_daemon"],
        3: [C + "veh_skullcracker"],
    },
}

# building_culture_variants.icon is a BARE FILENAME under ui/buildings/icons/ in ui.pack, and
# a name that is not there draws nothing with no error - check_icons() asserts all 34 exist.
# Distinct within this ship, because these six are the ones seen side by side in one popup.
ICONS = {
    "main_deck": "chd_military_hobgoblins",
    "gunports": "chd_tower_ballistics",
    "crows_nest": "chd_outpost_watch_tower",
    "cannons": "chd_military_war_machines",
    "hold": "chd_outpost_raiding_camp",
    "hull": "chd_factory_refinery",
}

# building_sets.icon is the CONSTRUCTION PANEL TAB, and unlike building_culture_variants.icon
# it is a FULL PATH, not a bare filename. All four naval sets shipped as the literal string
# "placeholder", which draws ui/buildings/icons/0_placeholder_building.png - the bright magenta
# missing-image square - on every visible tab. Vanilla uses "placeholder" on 106 of 280 rows and
# 26 of those ARE show_in_ui=true, so show_in_ui is the wrong test: those 26 are settlement/primary
# sets that draw as the main slot, not as a tab (wh_main_set_settlement_major/_minor/_port,
# vampire_coast_ship_settlement, hef_dragonship_settlement, chd_settlement_*) - if they drew tabs
# every settlement panel would be magenta. Every set that DOES draw a tab is pathed: VC's
# ship_unique / ship_recruitment / ship_extra. Ours are tabs. set_starting_kit is show_in_ui=false.
# All four chd_cat_* icons are parchment scrolls that differ only by the inner symbol; these
# three are the most distinct of them (tan horned mask / red axes / green scales).
SET_ICONS = {
    "derpy_chd_naval_horde_set_flagship": "UI/Buildings/Icons/chd_cat_defence.png",
    "derpy_chd_naval_horde_set_recruitment": "UI/Buildings/Icons/chd_cat_basic_military.png",
    "derpy_chd_naval_horde_set_structure": "UI/Buildings/Icons/chd_cat_infrastructure.png",
}

NAMES = {
    "main_deck": ("Crew Deck", "Press-Ganged Crew"),
    "gunports": ("Shot Ports", "Shot Ports"),
    "crows_nest": ("Masthead", "Masthead Watch"),
    "cannons": ("Gun Deck", "Gun Deck"),
    "hold": ("Slave Hold", "Slave Hold"),
    "hull": ("Iron Hull", "Iron Hull"),
}

LONG = {
    "main_deck": "A Fleetmaster is given what Zharr-Naggrund can spare, and what it can spare "
                 "is hobgoblins. They are counted aboard, not welcomed, and the count is "
                 "taken again after every storm.",
    "gunports": "Ports cut to a standard pattern and fitted with whatever the foundries sent "
                "down river that season. Nothing here is the best work of the Dawi-Zharr, and "
                "every piece of it fires.",
    "crows_nest": "A plain iron cage at the masthead. The Fleetmaster's own beasts roost on "
                  "the spars beneath it, and the watch has learned not to climb past them "
                  "after dark.",
    "cannons": "Magma and rocket, racked on a deck braced for recoil the shipwrights never "
               "quite trusted. A junior captain gets guns that work, not guns that impress.",
    "hold": "Chained ranks and a wolf-pen, divided by a bulkhead neither side respects. The "
            "hold is where the Fleetmaster's wealth is kept, and it is measured in bodies.",
    "hull": "Riveted iron over a Dwarf keel, with room below decks for engines the Guild "
            "would not release to a lord of any greater rank.",
}
SHORT = {
    "main_deck": "Recruits hobgoblin crew and Dawi-Zharr marines.",
    "gunports": "Recruits missile crews.",
    "crows_nest": "Recruits scouts and flying beasts.",
    "cannons": "Recruits artillery.",
    "hold": "Recruits slaves and wolf riders.",
    "hull": "Recruits war engines. Improves replenishment and recruitment capacity.",
}

# Cloned value-for-value from derpy_chd_naval_horde_hull, the only one of the six that carries
# effects. Without them this ship would have fewer recruitment slots than the other two for no
# stated reason.
HULL_EFFECTS = [("wh_main_effect_force_all_campaign_replenishment_rate", [4, 6, 8]),
                ("wh_main_effect_force_all_recruitment_points", [2, 4, 6])]

FIRST_UNIT_KEY = 952000001          # Abnagg 950000001-59, Tordrek 951000001+
CHD_MAX_TIER = 3


def lvl(chain, n):
    return "%s_%s_%d" % (NEW, chain, n)


def build():
    """[(building_level_key, unit)] - cumulative, in chain then level then unit order."""
    out = []
    for chain in CHAINS:
        acc = []
        for n in range(1, LEVELS[chain] + 1):
            acc = acc + NEW_AT[chain].get(n, [])
            for u in acc:
                out.append((lvl(chain, n), u))
    return out


# --------------------------------------------------------------------------- TSV plumbing

def read_tsv(fn):
    p = os.path.join(EXP, fn)
    with open(p, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    return lines[0].split("\t"), lines[1], [l.split("\t") for l in lines[2:]]


def write_tsv(fn, cols, meta, rows):
    body = "\n".join(["\t".join(cols), meta] + ["\t".join(r) for r in rows]) + "\n"
    with open(os.path.join(EXP, fn), "w", encoding="utf-8", newline="") as fh:
        fh.write(body)


def blank(cols, **kw):
    row = [""] * len(cols)
    for k, v in kw.items():
        row[cols.index(k)] = v
    return row


def van_typed(table, field, value):
    """One vanilla row as {column: RPFM TSV text}, formatted by CA's OWN field types.

    read_vanilla_cache.load() unwraps every cell to a plain Python value, and re-rendering those
    by guesswork writes an F32 0.0 back as "0" and a Boolean as "True" - neither of which is what
    import_tsv reads. The cached dump keeps the type tag on each cell, so the tag decides the
    format and a clone round-trips. Raises rather than returning a half-row if the key is gone.
    """
    import json as _json
    from read_vanilla_cache import CACHE
    with open(os.path.join(CACHE, table + ".json"), encoding="utf-8") as fh:
        tbl = _json.load(fh)["VecRFile"][0]["data"]["Decoded"]["DB"]["table"]
    names = [f["name"] for f in tbl["definition"]["fields"]]
    out = []
    for raw in tbl["table_data"]:
        cells = dict(zip(names, raw))
        if next(iter(cells[field].values())) != value:
            continue
        row = {}
        for n, cell in cells.items():
            (kind, v), = cell.items()
            if kind == "Boolean":
                row[n] = "true" if v else "false"
            elif kind.startswith("F"):
                row[n] = "%.4f" % v
            elif kind.startswith("I"):
                row[n] = str(int(v))
            else:
                row[n] = "" if v is None else str(v)
        out.append(row)
    assert out, "%s: no row with %s = %r" % (table, field, value)
    return out


def clone_row(cols, src, **kw):
    """A donor row mapped onto a TSV's columns by NAME, with overrides. Column order differs
    between RPFM's export and the cached definition, so position is never safe here."""
    missing = set(cols) - set(src)
    assert not missing, "donor row is missing %s - the table version moved" % sorted(missing)
    src = dict(src, **kw)
    return [src[c] for c in cols]


def drop_prefix(rows, cols, key_col, prefix):
    i = cols.index(key_col)
    return [r for r in rows if not r[i].startswith(prefix)]


# --------------------------------------------------------------------------- the tables

def gen():
    made = {}
    T = lambda n: "%s_tables.tsv" % n                                        # noqa: E731

    # 1. building_chains - six new ones, gated to the Fleetmaster.
    cols, meta, rows = read_tsv(T("building_chains"))
    rows = drop_prefix(rows, cols, "key", NEW)
    order = 18                                  # Abnagg 1-11, Tordrek 12-17
    for c in CHAINS:
        rows.append(blank(cols, key="%s_%s" % (NEW, c), chain_category="military",
                          in_encyclopedia="false",
                          building_superchain="%s_sch_%s" % (NEW, c),
                          optional_sort_order=str(order),
                          optional_required_horde_commander=LORD,
                          can_be_dismantled="true", is_foreign_slot_chain="false"))
        order += 1
    made[T("building_chains")] = (cols, meta, rows)

    # 2. one row per chain in each of the four registration tables
    for name, key_col, mk in (
            ("building_superchains", "key",
             lambda c, cols: blank(cols, key="%s_sch_%s" % (NEW, c))),
            ("building_instances", "key",
             lambda c, cols: blank(cols, key="%s_%s" % (NEW, c), num_instances="1")),
            ("building_chain_set_items", "chain",
             lambda c, cols: blank(cols, chain="%s_%s" % (NEW, c),
                                   set="%s_secondary" % ABNAGG_CHAINS, remove="false")),
            ("building_chain_availability_sets", "building_chain",
             lambda c, cols: blank(cols, building_chain="%s_%s" % (NEW, c),
                                   id="derpy_chd_bas_naval_horde"))):
        cols, meta, rows = read_tsv(T(name))
        rows = drop_prefix(rows, cols, key_col, NEW)
        rows += [mk(c, cols) for c in CHAINS]
        made[T(name)] = (cols, meta, rows)

    # 3. building_levels - cost/primreq ladder copied from Abnagg's twin, level for level
    cols, meta, rows = read_tsv(T("building_levels"))
    src = {r[cols.index("level_name")]: r for r in rows}
    rows = drop_prefix(rows, cols, "level_name", NEW)
    for c in CHAINS:
        for n in range(1, LEVELS[c] + 1):
            r = list(src["%s_%s_%d" % (ABNAGG_CHAINS, c, n)])
            r[cols.index("level_name")] = lvl(c, n)
            r[cols.index("chain")] = "%s_%s" % (NEW, c)
            r[cols.index("building_instance_key")] = "%s_%s" % (NEW, c)
            rows.append(r)
    made[T("building_levels")] = (cols, meta, rows)

    # 4. building_culture_variants
    cols, meta, rows = read_tsv(T("building_culture_variants"))
    rows = drop_prefix(rows, cols, "building", NEW)
    for c in CHAINS:
        for n in range(1, LEVELS[c] + 1):
            rows.append(blank(cols, building=lvl(c, n), description="%s_%s" % (NEW, c),
                              icon=ICONS[c], disables="false",
                              short_description="%s_%s" % (NEW, c), display_tooltip="true"))
    made[T("building_culture_variants")] = (cols, meta, rows)

    # 5. building_upgrades_junction - no row means the tier greys out with no reason given
    cols, meta, rows = read_tsv(T("building_upgrades_junction"))
    rows = drop_prefix(rows, cols, "from", NEW)
    for c in CHAINS:
        for n in range(1, LEVELS[c]):
            rows.append(blank(cols, **{"from": lvl(c, n), "to": lvl(c, n + 1)}))
    made[T("building_upgrades_junction")] = (cols, meta, rows)

    # 6. building_set_to_building_junctions - unjunctioned chains draw an empty popup
    cols, meta, rows = read_tsv(T("building_set_to_building_junctions"))
    rows = drop_prefix(rows, cols, "building_chain", NEW)
    for c in CHAINS:
        rows.append(blank(cols, building_chain="%s_%s" % (NEW, c),
                          building_set="%s_set_recruitment" % ABNAGG_CHAINS, exclude="false"))
    made[T("building_set_to_building_junctions")] = (cols, meta, rows)

    # 7. building_effects_junction - the hero half on Abnagg's chains, plus the hull ladder
    cols, meta, rows = read_tsv(T("building_effects_junction"))
    rows = drop_prefix(rows, cols, "building", NEW)
    ours = set(HERO_ENABLE.values()) | set(HERO_CAP.values())
    ec = cols.index("effect")
    rows = [r for r in rows if r[ec] not in ours]

    def eff(building, effect, scope, v):
        rows.append(blank(cols, building=building, effect=effect, effect_scope=scope,
                          value="%.4f" % v, value_damaged="%.4f" % v, value_ruined="0.0000"))

    for prefix, heroes in ((ABNAGG_CHAINS, HEROES), (KRAKEN_CHAINS, KRAKEN_HEROES)):
        for chain, agent, enable_at, caps in heroes:
            for n in enable_at:
                eff("%s_%s_%d" % (prefix, chain, n), HERO_ENABLE[agent], ENABLE_SCOPE, 1)
            for n, v in sorted(caps.items()):
                eff("%s_%s_%d" % (prefix, chain, n), HERO_CAP[agent], CAP_SCOPE, v)
    for effect, vals in HULL_EFFECTS:
        for n, v in enumerate(vals, 1):
            eff(lvl("hull", n), effect, "force_to_force_own", v)
    made[T("building_effects_junction")] = (cols, meta, rows)

    # 8. building_units_allowed
    cols, meta, rows = read_tsv(T("building_units_allowed"))
    rows = drop_prefix(rows, cols, "building", NEW)
    for i, (b, u) in enumerate(build()):
        rows.append(blank(cols, building=b, unit=u, XP="0", key=str(FIRST_UNIT_KEY + i),
                          conditions="0", faction="", enabled="false"))
    made[T("building_units_allowed")] = (cols, meta, rows)

    # ----------------------------------------------------------------- the Fleetmaster

    # 9. agent_subtypes
    cols, meta, rows = read_tsv("zz_agent_subtypes.tsv")
    rows = drop_prefix(rows, cols, "key", LORD)
    # auto_generate must be TRUE, and the count of vanilla ship-founders that set it false is a
    # red herring. The lord recruitment panel lists MINTED CANDIDATES, not subtypes - a live dump
    # of it shows only `general_candidate_N_` entries with rolled names and background traits
    # (HANDOFF_20260902 section 9.9). auto_generate is what lets the engine mint a subtype, so with
    # it false nothing ever creates a Fleetmaster and the card cannot draw - and an empty category
    # draws no tab either, which is the same fault that hid the private tab in 9.7. The 40-of-43
    # count is about ship-founders CA mints by another route (legendary lords via
    # campaign_to_agent_subtypes, bloodlines and dragonships via their own mechanics); we have no
    # such route. The minting risk it was guarding against is bounded: only
    # cr_chd_warfleet_of_uzkulak permits this subtype, and derpy_chd_naval_admiral.lua's
    # CharacterCreated seeder already handles any ship founded this way.
    rows.append(blank(cols, key=LORD, auto_generate=AUTO_GENERATE, is_caster="false", small_icon="",
                      associated_unit_override=DONOR_UNIT, audio_voiceover_actor_group=DONOR_VO,
                      show_in_ui="true", cap="-1", has_female_name="false", can_gain_xp="true",
                      loyalty_is_applicable="false", contributes_to_agent_cap="true",
                      recruitment_category=RECRUITMENT_CATEGORY, magic_lore="", names_group="",
                      can_be_loaned=CAN_BE_LOANED, recruitable="true",
                      saving_settings="can_be_saved_loaded", audio_vo_culture_override="",
                      spam_click_vo_enabled="false", can_equip_ancillaries="true",
                      cost=str(COST), recruitment_button_active_icon_path="",
                      recruitment_button_background_icon_path=""))
    made["zz_agent_subtypes.tsv"] = (cols, meta, rows)

    # 10. campaign_character_art_sets - art_set_id is the SOLE primary key, so CA's ids cannot
    # be reused: writing wh3_dlc23_art_set_chd_overseer_01 here would repoint CA's own Overseer.
    cols, meta, rows = read_tsv("zz_campaign_character_art_sets.tsv")
    rows = drop_prefix(rows, cols, "art_set_id", LORD)
    for i in range(1, ART_SETS + 1):
        rows.append(blank(cols, art_set_id="%s_%02d" % (LORD, i), agent_type="general",
                          culture="", subculture="", faction="", is_custom="false",
                          is_male="true", agent_subtype=LORD, campaign_map_scale="1.0000"))
    made["zz_campaign_character_art_sets.tsv"] = (cols, meta, rows)

    # 11. agent_uniforms - our art_set_id, CA's model files. No new assets.
    cols, meta, rows = read_tsv("zz_agent_uniforms.tsv")
    rows = drop_prefix(rows, cols, "uniform_name", LORD)
    for i in range(1, ART_SETS + 1):
        art = DONOR_ART % i
        rows.append(blank(cols, filename=art, uniform_name="%s_%02d" % (LORD, i),
                          battle_filename=art, campaign_porthole_filename=art,
                          campaign_politician_filename="", campaign_override_skeleton=""))
    made["zz_agent_uniforms.tsv"] = (cols, meta, rows)

    # 11b. campaign_character_arts - the row that binds an art set to a uniform and to the walk
    # and sail animations. campaign_character_art_sets alone is NOT enough: it says which subtype
    # owns the art set and nothing about what to draw, so without this the engine falls back to a
    # default human. Cloned field for field from CA's wh3_dlc23_art_set_chd_overseer_0N.
    cols, meta, rows = read_tsv("zz_campaign_character_arts.tsv")
    rows = drop_prefix(rows, cols, "art_set_id", LORD)
    for i in range(1, ART_SETS + 1):
        art = "%s_%02d" % (LORD, i)
        rows.append(blank(cols, id=str(ARTS_ID_BASE + i - 1), art_set_id=art, level="0", age="0",
                          portrait="", season="none", uniform=art, card="", info="",
                          sea_uniform=DONOR_SEA_UNIFORM, navy_uniform=DONOR_SEA_UNIFORM,
                          land_animation=DONOR_LAND_ANIM, sea_animation=DONOR_SHIP_ANIM,
                          navy_animation=DONOR_SHIP_ANIM, land_animation_vfx_filter="0",
                          sea_animation_vfx_filter="1", navy_animation_vfx_filter="1"))
    made["zz_campaign_character_arts.tsv"] = (cols, meta, rows)

    # 12. character_skill_node_sets - binds only by agent_subtype_key; there is no
    # subculture-wide general set to inherit (0 such rows in 547).
    cols, meta, rows = read_tsv("zz_character_skill_node_sets.tsv")
    rows = drop_prefix(rows, cols, "key", LORD)
    for stale in STALE_WIGHT:
        rows = drop_prefix(rows, cols, "key", stale)
    rows.append(blank(cols, key=SKILL_SET, agent_key="general", for_army="false",
                      faction_key="", for_navy="false", campaign_key="", subculture="",
                      agent_subtype_key=LORD))
    made["zz_character_skill_node_sets.tsv"] = (cols, meta, rows)

    # 13. character_skill_node_set_items - CA's Overseer nodes, read live rather than listed
    from read_vanilla_cache import load
    van_items = load("character_skill_node_set_items")[0]
    donor = sorted({r["item"] for r in van_items if r["set"] == DONOR_SKILL_SET})
    assert donor, "no nodes found in %s" % DONOR_SKILL_SET
    cols, meta, rows = read_tsv("zz_character_skill_node_set_items.tsv")
    rows = drop_prefix(rows, cols, "set", LORD)
    for stale in STALE_WIGHT:
        rows = drop_prefix(rows, cols, "set", stale)
    for item in donor:
        rows.append(blank(cols, set=SKILL_SET, item=item, mod_disabled="false"))
    made["zz_character_skill_node_set_items.tsv"] = (cols, meta, rows)

    # 14. faction_agent_permitted_subtypes - the Fleetmaster, and ONLY him.
    # An earlier pass also wrote the six hero subtypes here, on the finding that Abnagg's
    # faction permitted one subtype in total. That finding was wrong: it surveyed vanilla and
    # this pack, and cr_chd_* factions are created by !cr_oldworld_campaign.pack, which ships
    # the full 15-row CA set for all ten of them. The six rows were exact duplicates of rows
    # already in db/faction_agent_permitted_subtypes_tables/cr_oldworld_new_factions.
    # check() now proves that pack carries them instead of shipping our own copies.
    cols, meta, rows = read_tsv("zz_faction_agent_permitted_subtypes.tsv")
    si, fi = cols.index("subtype"), cols.index("faction")
    ours = {LORD} | {s for _a, s in HERO_SUBTYPES}
    rows = [r for r in rows if not (r[fi] == FACTION and r[si] in ours)]
    rows.append(blank(cols, agent="general", faction=FACTION, subtype=LORD,
                      mod_disabled="false"))
    # Tordrek's Gunnery Wight - the one hero subtype cr_oldworld does not already grant.
    # WIGHT_DONOR_SUBTYPE is in the drop set because an earlier version DID grant CA's Vampire
    # Coast subtype here; without it that row survives every regeneration, since a generator
    # only ever removes the keys it currently writes.
    theirs = {s for _a, s in TORDREK_HERO_SUBTYPES} | set(STALE_WIGHT)
    rows = [r for r in rows if not (r[fi] == TORDREK_FACTION and r[si] in theirs)]
    for agent, subtype in (TORDREK_HERO_SUBTYPES if WIGHT_ENABLED else []):
        rows.append(blank(cols, agent=agent, faction=TORDREK_FACTION, subtype=subtype,
                          mod_disabled="false"))
    made["zz_faction_agent_permitted_subtypes.tsv"] = (cols, meta, rows)

    # 14b. effect_bonus_value_agent_subtype_junctions - THE unlock link, and the reason the
    # Gunnery Wight sat in the Recruit Hero panel reading "This type is not yet unlocked" with
    # every other row correct. A permission row puts a subtype in the panel; an enable effect
    # opens the slot for its (agent type, culture); this junction is what says WHICH subtypes
    # that effect makes available, via bonus_value_id "availability" - the same shape as
    # docs/CUSTOM_ABILITIES.md's bonus_value_id = "enable". All six vanilla Chaos Dwarf hero
    # subtypes have one and no lord does (the overseer has zero rows, because lords have no
    # enable effect at all). CA's own wight carries exactly one, against the Vampire Coast
    # engineer effect; ours points at the Chaos Dwarf one instead. New fragment - this table
    # is not in the pack yet, so it is authored rather than read.
    cols = ["bonus_value_id", "effect", "subtype"]
    meta = ("#effect_bonus_value_agent_subtype_junctions_tables;0;"
            "db/effect_bonus_value_agent_subtype_junctions_tables/derpy_chd_naval_horde"
            + "\t" * (len(cols) - 1))
    made["zz_effect_bonus_value_agent_subtype_junctions.tsv"] = (
        cols, meta,
        [["availability", HERO_ENABLE["engineer"], WIGHT_SUBTYPE]] if WIGHT_ENABLED else [])

    # 15. agent_recruitment_categories - the Fleetmaster's own tab in the lord panel.
    cols, meta, rows = read_tsv("zz_agent_recruitment_categories.tsv")
    rows = drop_prefix(rows, cols, "key", OWN_CATEGORY)
    rows.append(blank(cols, key=OWN_CATEGORY, order=str(CATEGORY_ORDER),
                      icon_file_path=CATEGORY_ICON, show_in_recruitment="true",
                      counts_towards_caps_when_off_the_map="true"))
    made["zz_agent_recruitment_categories.tsv"] = (cols, meta, rows)

    # 16. building_sets - real tab icons in place of the magenta placeholder. Shared by all
    # three ships, so it lives here rather than in a per-ship generator.
    cols, meta, rows = read_tsv("building_sets_tables.tsv")
    ki, ii = cols.index("key"), cols.index("icon")
    for r in rows:
        if r[ki] in SET_ICONS:
            r[ii] = SET_ICONS[r[ki]]
    made["building_sets_tables.tsv"] = (cols, meta, rows)

    # 17/18. the campaign group that turns a recruited Fleetmaster's force into the ship
    cols, meta, rows = read_tsv("zz_campaign_group_members.tsv")
    rows = drop_prefix(rows, cols, "id", MEMBER)
    rows.append(blank(cols, id=MEMBER, group=GROUP, priority="0.0000"))
    made["zz_campaign_group_members.tsv"] = (cols, meta, rows)

    cols, meta, rows = read_tsv("zz_campaign_group_member_criteria_agent_subtypes.tsv")
    rows = drop_prefix(rows, cols, "member", MEMBER)
    rows.append(blank(cols, member=MEMBER, agent_subtype=LORD))
    made["zz_campaign_group_member_criteria_agent_subtypes.tsv"] = (cols, meta, rows)

    # ------------------------------------------------- 19. Tordrek's Gunnery Wight
    # CA's own subtype row, rewritten with a Vampire Coast names group and VO culture, nothing else.
    # See the WIGHT_* block for why there is no clone here any more, and what the clone broke.
    cols, meta, rows = read_tsv("zz_agent_subtypes.tsv")
    for stale in STALE_WIGHT + [WIGHT_SUBTYPE]:
        rows = drop_prefix(rows, cols, "key", stale)
    if WIGHT_ENABLED:
        rows.append(clone_row(cols, van_typed("agent_subtypes", "key", WIGHT_DONOR_SUBTYPE)[0],
                              key=WIGHT_SUBTYPE, names_group=WIGHT_NAMES,
                              audio_vo_culture_override=WIGHT_VO_CULTURE))
    made["zz_agent_subtypes.tsv"] = (cols, meta, rows)

    # The (agent, culture, unit) row that lets a Chaos Dwarf faction field the wight's unit at all.
    # With the wight off this file goes empty, and import_naval_horde.py deletes the fragment
    # from the pack rather than shipping a table with no rows in it.
    cols, meta, rows = read_tsv("zz_agent_culture_details.tsv")
    rows = drop_prefix(rows, cols, "key", WIGHT_CULTURE_KEY)
    if WIGHT_ENABLED:
        rows.append(clone_row(cols,
                              van_typed("agent_culture_details", "key",
                                        int(WIGHT_CULTURE_KEY_DONOR))[0],
                              key=WIGHT_CULTURE_KEY, culture=WIGHT_CULTURE))
    made["zz_agent_culture_details.tsv"] = (cols, meta, rows)

    # The clone's five art sets and their arts rows go the same way. They are the reason the
    # porthole was a placeholder, so leaving them behind would leave the bug behind.
    for fn in ("zz_campaign_character_art_sets.tsv", "zz_campaign_character_arts.tsv"):
        cols, meta, rows = made[fn]
        for stale in STALE_WIGHT:
            rows = drop_prefix(rows, cols, "art_set_id", stale)
        made[fn] = (cols, meta, rows)

    return made


def gen_loc():
    fn = "derpy_chd_naval_horde_loc.tsv"
    cols, meta, rows = read_tsv(fn)
    rows = [r for r in rows if not r[0].endswith(LORD) and NEW not in r[0]]
    roman = ["", "I", "II", "III", "IV", "V"]
    for c in CHAINS:
        base, tip = NAMES[c]
        for n in range(1, LEVELS[c] + 1):
            rows.append(["building_culture_variants_name_%s" % lvl(c, n),
                         "%s %s" % (base, roman[n]), "false"])
        rows.append(["building_chains_chain_tooltip_%s_%s" % (NEW, c), tip, "false"])
        rows.append(["building_description_texts_long_description_%s_%s" % (NEW, c),
                     LONG[c], "false"])
        rows.append(["building_short_description_texts_short_description_%s_%s" % (NEW, c),
                     SHORT[c], "false"])
    rows = [r for r in rows if OWN_CATEGORY not in r[0]]
    rows.append(["agent_recruitment_categories_onscreen_name_%s" % OWN_CATEGORY,
                 "Fleetmasters", "false"])
    rows.append(["agent_recruitment_categories_onscreen_description_%s" % OWN_CATEGORY,
                 "Captains raised to command a vessel of the Warfleet.", "false"])
    rows.append(["agent_subtypes_onscreen_name_override_%s" % LORD, "Fleetmaster", "false"])

    # Tordrek's Gunnery Wight needs no loc of its own now that it is CA's subtype - name,
    # description and unit text all resolve against CA's keys. These strip the clone's.
    rows = [r for r in rows if not any(st in r[0] for st in STALE_WIGHT)]
    # The army-banner badge's tooltip. The state itself is added to CA's army_banner.twui.xml by
    # tools/patch_army_banner.py; the component is tooltipslocalised, so the label must resolve
    # here or the hover comes up blank.
    from patch_army_banner import LOC_LABEL as BANNER_LABEL, TOOLTIP as BANNER_TOOLTIP
    banner_key = "uied_component_texts_localised_string_%s" % BANNER_LABEL
    rows = [r for r in rows if r[0] != banner_key]
    rows.append([banner_key, BANNER_TOOLTIP, "false"])
    rows.append(["agent_subtypes_description_text_override_%s" % LORD,
                 "A captain of the Warfleet of Uzkulak, granted an iron hull and as much of a "
                 "crew as Zharr-Naggrund could be persuaded to spare. He commands his own "
                 "vessel and answers for it.", "false"])
    return fn, cols, meta, rows


# --------------------------------------------------------------------------- checks

UI_PACK = (r"F:\SteamLibrary\steamapps\common\Total War WARHAMMER III\data\ui.pack")
OW_PACK = (r"F:\SteamLibrary\steamapps\workshop\content\1142710\3081800026"
           r"\!cr_oldworld_campaign.pack")
OW_TABLE = "db/faction_agent_permitted_subtypes_tables/cr_oldworld_new_factions"


def check_oldworld_permissions():
    """The six hero permissions must exist in !cr_oldworld_campaign.pack, not in this pack.

    That pack creates the cr_chd_* factions and ships CA's full 15-row permission set for
    every one of them, so our own rows would be exact duplicates. Workshop mod packs are
    uncompressed, so the row can be matched byte-exactly without RPFM: RPFM writes each
    StringU8 as u16 length + bytes, and a row's fields are adjacent, so agent+faction+subtype
    concatenated in definition order is a unique needle. A bogus subtype must not match.
    """
    import struct
    import read_pack_index
    if not os.path.exists(OW_PACK):
        print("  check_oldworld_permissions SKIPPED - pack not at %s" % OW_PACK)
        return
    fh, ents = read_pack_index.entries(OW_PACK)
    try:
        data = None
        for p, size, off, comp in ents:
            if p.replace("\\", "/") == OW_TABLE:
                assert comp == 0, "cr_oldworld's DB is compressed (%s) - bytes unreadable" % comp
                fh.seek(off)
                data = fh.read(size)
    finally:
        fh.close()
    assert data, "%s not in %s - has the mod been renamed?" % (OW_TABLE, OW_PACK)

    def needle(agent, faction, subtype):
        return b"".join(struct.pack("<H", len(s)) + s.encode()
                        for s in (agent, faction, subtype))

    assert needle("champion", FACTION, "no_such_subtype") not in data, \
        "byte match is not selective"
    missing = [(a, s) for a, s in HERO_SUBTYPES if needle(a, FACTION, s) not in data]
    assert not missing, (
        "cr_oldworld does not permit %s for %s - the hero panels would open empty and the "
        "rows would have to be shipped here after all" % (missing, FACTION))

    # Tordrek's engineer slot leans on the same pack for the Castellan, and must NOT already
    # carry the Gunnery Wight - our row would be an exact duplicate if it did.
    castellan = C + "infernal_castellan"
    assert needle("engineer", TORDREK_FACTION, castellan) in data, (
        "cr_oldworld does not permit the Castellan for %s - it needs a row here too"
        % TORDREK_FACTION)
    dupes = [(a, s) for a, s in TORDREK_HERO_SUBTYPES
             if needle(a, TORDREK_FACTION, s) in data]
    assert not dupes, "cr_oldworld now grants %s for %s - drop our rows" % (
        dupes, TORDREK_FACTION)
    print("  check_oldworld_permissions ok: %d hero subtypes for %s, Castellan already "
          "permitted for %s, Gunnery Wight is ours to grant"
          % (len(HERO_SUBTYPES), FACTION, TORDREK_FACTION))


def check_icons(made):
    """Every building icon we ship must exist in ui.pack, ours and the two older ships'.

    Phase 8's leftover. `icon` is a bare filename under ui/buildings/icons/ and a wrong one
    draws nothing at all - no error, no placeholder - which is how chd_outpost_slave_pens (a
    name that simply does not exist) survived being written here in the first place.
    """
    import read_pack_index
    if not os.path.exists(UI_PACK):
        print("  check_icons SKIPPED - ui.pack not at %s" % UI_PACK)
        return
    fh, ents = read_pack_index.entries(UI_PACK)
    try:
        have = {p.replace("\\", "/").rsplit("/", 1)[-1][:-4]
                for p, _s, _o, _c in ents
                if "ui/buildings/icons/" in p.replace("\\", "/").lower()
                and p.lower().endswith(".png")}
    finally:
        fh.close()
    assert have, "no building icons found in ui.pack - the path convention moved"

    cols, _, rows = made["building_culture_variants_tables.tsv"]
    bi, ii = cols.index("building"), cols.index("icon")
    used = {}
    for r in rows:
        used.setdefault(r[ii], []).append(r[bi])
    missing = sorted(k for k in used if k not in have)
    assert not missing, "icons not in ui.pack: %s" % [
        (k, used[k][0]) for k in missing]

    # within one ship the six chains are drawn side by side, so they must differ
    mine = {c: ICONS[c] for c in CHAINS}
    dupes = [k for k in set(mine.values()) if list(mine.values()).count(k) > 1]
    assert not dupes, "the Fleetmaster's chains share an icon: %s" % dupes

    # building_sets.icon is the panel TAB and takes a full path, not a bare filename. Every
    # visible set must point at a file that exists, and no two tabs may share one.
    scols, _, srows = made["building_sets_tables.tsv"]
    ki, ii, vi = (scols.index(x) for x in ("key", "icon", "show_in_ui"))
    tabs = {r[ki]: r[ii] for r in srows if r[vi] == "true"}
    bad = sorted(k for k, v in tabs.items() if v == "placeholder")
    assert not bad, "visible building_set still draws the magenta placeholder: %s" % bad
    stems = {}
    for k, v in tabs.items():
        stem = v.replace("\\", "/").rsplit("/", 1)[-1]
        assert stem.endswith(".png") and stem[:-4] in have, \
            "building_set %s points at %s, which is not in ui.pack" % (k, v)
        stems.setdefault(stem, []).append(k)
    shared = {s: ks for s, ks in stems.items() if len(ks) > 1}
    assert not shared, "two construction tabs share an icon: %s" % shared

    # the Fleetmaster's own recruitment-category icon lives elsewhere in ui.pack
    ccols, _, crows = made["zz_agent_recruitment_categories.tsv"]
    path = [r[ccols.index("icon_file_path")] for r in crows
            if r[ccols.index("key")] == OWN_CATEGORY][0]
    fh, ents = read_pack_index.entries(UI_PACK)
    try:
        cat = {p.replace("\\", "/").lower() for p, _s, _o, _c in ents}
    finally:
        fh.close()
    assert path.replace("\\", "/").lower() in cat, \
        "recruitment category icon not in ui.pack: %s" % path
    print("  check_icons ok: %d distinct building icons, %d tabs, all present in ui.pack"
          % (len(used), len(tabs)))


def check(made):
    from read_vanilla_cache import load
    T = lambda n: "%s_tables.tsv" % n                                        # noqa: E731

    # --- the roster
    cols, _, rows = made[T("building_units_allowed")]
    bi, ui, ki = (cols.index(x) for x in ("building", "unit", "key"))
    mine = [r for r in rows if r[bi].startswith(NEW)]
    theirs = [r for r in rows if not r[bi].startswith(NEW)]
    keys = [r[ki] for r in rows]
    assert len(keys) == len(set(keys)), "building_units_allowed key collision"
    assert len(theirs) == 145, "Abnagg's + Tordrek's 145 rows must survive, found %d" % len(
        theirs)

    units = {r[ui] for r in mine}
    tier = {r["unit"]: r["tier"] for r in load("main_units")[0]}
    over = sorted((u, tier[u]) for u in units if tier.get(u, 0) > CHD_MAX_TIER)
    assert not over, "units above tier %d: %s" % (CHD_MAX_TIER, over)

    vanilla = {r["unit"] for r in load("building_units_allowed")[0]}
    assert not units - vanilla, "unit keys not recruitable in vanilla: %s" % sorted(
        units - vanilla)

    # the junior ship must not carry what tops out the other two
    ELITE = {C + "mon_bale_taurus", C + "mon_kdaai_fireborn", C + "mon_kdaai_destroyer",
             C + "veh_dreadquake_mortar", "wh_main_chs_art_hellcannon",
             C + "inf_infernal_ironsworn"}
    assert not units & ELITE, "elite unit on the Fleetmaster's ship: %s" % sorted(units & ELITE)
    assert not any(u.startswith("wh2_dlc11_cst_") for u in units), \
        "Vampire Coast unit on the Fleetmaster's ship - that roster is Tordrek's"

    # cumulative: each level is a superset of the one below
    by = {}
    for r in mine:
        by.setdefault(r[bi], set()).add(r[ui])
    for c in CHAINS:
        for n in range(2, LEVELS[c] + 1):
            assert by.get(lvl(c, n - 1), set()) <= by.get(lvl(c, n), set()), \
                "%s is not a superset of the level below" % lvl(c, n)

    lcols, _, lrows = made[T("building_levels")]
    declared = {r[lcols.index("level_name")] for r in lrows}
    for r in mine:
        assert r[bi] in declared, "grant against an undeclared level: %s" % r[bi]

    # every new chain has an upgrade edge into every level above 1, or it greys out silently
    ucols, _, urows = made[T("building_upgrades_junction")]
    edges = {(r[ucols.index("from")], r[ucols.index("to")]) for r in urows}
    for c in CHAINS:
        for n in range(1, LEVELS[c]):
            assert (lvl(c, n), lvl(c, n + 1)) in edges, "no upgrade edge %s -> %d" % (
                lvl(c, n), n + 1)

    # --- the gate, and that nothing else moved
    ccols, _, crows = made[T("building_chains")]
    kc, gc = ccols.index("key"), ccols.index("optional_required_horde_commander")
    gated = {r[kc]: r[gc] for r in crows if r[gc]}
    want = {"%s_%s" % (ABNAGG_CHAINS, c): ABNAGG for c in CHAINS}
    want.update({"derpy_chd_naval_kraken_%s" % c: TORDREK for c in CHAINS})
    want.update({"%s_%s" % (NEW, c): LORD for c in CHAINS})
    want["derpy_chd_naval_shipworks_abnagg"] = ABNAGG
    want["derpy_chd_naval_shipworks_tordrek"] = TORDREK
    assert gated == want, "horde-commander gates wrong:\n  got  %s\n  want %s" % (
        sorted(gated.items()), sorted(want.items()))

    # --- the heroes
    ecols, _, erows = made[T("building_effects_junction")]
    eb, ee, es, ev = (ecols.index(x) for x in ("building", "effect", "effect_scope", "value"))
    hero = [r for r in erows if r[ee] in set(HERO_ENABLE.values()) | set(HERO_CAP.values())]
    want_hero = sum(len(en) + len(caps)
                    for _, _, en, caps in HEROES + KRAKEN_HEROES)
    assert len(hero) == want_hero, "expected %d hero rows, got %d" % (want_hero, len(hero))

    vanilla_effects = {r["effect"] for r in load("effects")[0]}
    for r in hero:
        assert r[ee] in vanilla_effects, "effect key not in vanilla: %s" % r[ee]
        assert r[eb].startswith((ABNAGG_CHAINS + "_", KRAKEN_CHAINS + "_")), \
            "hero effect on a chain that is neither Abnagg's nor Tordrek's: %s" % r[eb]
        assert not r[eb].startswith(NEW + "_"), \
            "the Fleetmaster is deliberately hero-less: %s" % r[eb]
        want_scope = ENABLE_SCOPE if r[ee] in HERO_ENABLE.values() else CAP_SCOPE
        assert r[es] == want_scope, "%s has scope %s, want %s" % (r[eb], r[es], want_scope)

    # the enable scope is the horde one, and it is not the one CHD settlements use
    van = load("building_effects_junction")[0]
    horde_scoped = {x["effect_scope"] for x in van
                    if "agent_enable_recruitment" in x["effect"]
                    and x["building"].startswith("wh2_dlc11_vampirecoast_ship")}
    assert horde_scoped == {ENABLE_SCOPE}, "VC ships no longer prove the scope: %s" % horde_scoped

    # every hero effect lands on a level that chain actually declares
    declared_levels = {r[lcols.index("level_name")] for r in lrows}
    for r in hero:
        assert r[eb] in declared_levels, "hero effect on an undeclared level: %s" % r[eb]

    # PK is (building, effect, context_requirement); context is blank on all of ours
    pk = [(r[eb], r[ee]) for r in erows]
    assert len(pk) == len(set(pk)), "duplicate (building, effect) in building_effects_junction"

    # --- the Fleetmaster
    acols, _, arows = made["zz_agent_subtypes.tsv"]
    lord = [r for r in arows if r[acols.index("key")] == LORD]
    assert len(lord) == 1, "expected exactly one Fleetmaster row"
    want_subtypes = 15 if WIGHT_ENABLED else 14
    assert len(arows) == want_subtypes, \
        "13 existing subtypes + the Fleetmaster%s, got %d" % (
            " + the Gunnery Wight" if WIGHT_ENABLED else "", len(arows))

    scols, _, srows = made["zz_campaign_character_art_sets.tsv"]
    ids = [r[scols.index("art_set_id")] for r in srows]
    assert len(ids) == len(set(ids)), "art_set_id collision"
    van_art = {r["art_set_id"] for r in load("campaign_character_art_sets")[0]}
    clash = set(ids) & van_art
    assert not clash, "art_set_id overrides a vanilla row: %s" % sorted(clash)

    ucols2, _, urows2 = made["zz_agent_uniforms.tsv"]
    names = [r[ucols2.index("uniform_name")] for r in urows2]
    assert len(names) == len(set(names)), "uniform_name collision"
    mine_art = {r[scols.index("art_set_id")] for r in srows
                if r[scols.index("agent_subtype")] == LORD}
    assert mine_art <= set(names), "art set with no agent_uniforms row: %s" % sorted(
        mine_art - set(names))

    # An art set with no campaign_character_arts row draws a DEFAULT HUMAN - this is the check
    # that was missing when the Fleetmaster shipped as a High Elf. Proven to bite by deleting a
    # row and re-running. The `uniform` must resolve in agent_uniforms, ours or CA's.
    rcols, _, rrows = made["zz_campaign_character_arts.tsv"]
    arts = {r[rcols.index("art_set_id")]: r for r in rrows}
    assert len(arts) == len(rrows), "art_set_id collision in campaign_character_arts"
    orphans = mine_art - set(arts)
    assert not orphans, "art set with no campaign_character_arts row: %s" % sorted(orphans)
    van_uniforms = {r["uniform_name"] for r in load("agent_uniforms")[0]}
    for a in sorted(mine_art):
        u = arts[a][rcols.index("uniform")]
        assert u in set(names) | van_uniforms, "%s points at unknown uniform %r" % (a, u)
    ids_n = [r[rcols.index("id")] for r in rrows]
    assert len(ids_n) == len(set(ids_n)), "duplicate id in campaign_character_arts"

    ncols, _, nrows = made["zz_character_skill_node_set_items.tsv"]
    van_nodes = {r["key"] for r in load("character_skill_nodes")[0]}
    ours = [r for r in nrows if r[ncols.index("set")] == SKILL_SET]
    missing = {r[ncols.index("item")] for r in ours} - van_nodes
    assert not missing, "skill nodes that do not exist: %s" % sorted(missing)
    assert len(ours) > 40,         "only %d skill nodes copied into %s - the donor set looks wrong" % (len(ours), SKILL_SET)

    # Every subtype this pack MINTS needs a node set of its own; CA's subtypes bring theirs. The
    # Fleetmaster is the only minted one left - the Gunnery Wight is CA's now, and a set of ours
    # over CA's nodes was measured in game to bind to nothing at all.
    nscols, _, nsrows = made["zz_character_skill_node_sets.tsv"]
    bound = {r[nscols.index("agent_subtype_key")] for r in nsrows}
    assert LORD in bound, "agent subtype with no character_skill_node_sets row: %s" % LORD
    skeys = [r[nscols.index("key")] for r in nsrows]
    assert len(skeys) == len(set(skeys)), "duplicate character_skill_node_sets key"
    # key is that table's primary key - 547 vanilla rows, 547 distinct - so a reused one is a
    # silently dropped row, not a shared set.
    clash = set(skeys) & {r["key"] for r in load("character_skill_node_sets")[0]}
    assert not clash, "skill node set key collides with vanilla: %s" % sorted(clash)

    fcols, _, frows = made["zz_faction_agent_permitted_subtypes.tsv"]
    fs, ff, fa = (fcols.index(x) for x in ("subtype", "faction", "agent"))
    perm = [r for r in frows if r[fs] == LORD]
    assert len(perm) == 1 and perm[0][ff] == FACTION, \
        "the Fleetmaster must be permitted to exactly one faction"

    # A permission row only LISTS a hero subtype in the panel. What unlocks it is an
    # `availability` junction tying it to the enable effect that opens its slot - without one
    # the entry renders greyed as "This type is not yet unlocked", every other row correct.
    bcols, _, brows = made["zz_effect_bonus_value_agent_subtype_junctions.tsv"]
    ours_avail = {(r[bcols.index("subtype")], r[bcols.index("effect")]) for r in brows
                  if r[bcols.index("bonus_value_id")] == "availability"}
    van_avail = {(r["subtype"], r["effect"])
                 for r in load("effect_bonus_value_agent_subtype_junctions")[0]
                 if r["bonus_value_id"] == "availability"}
    for agent, subtype in HERO_SUBTYPES + (TORDREK_HERO_SUBTYPES if WIGHT_ENABLED else []):
        pair = (subtype, HERO_ENABLE[agent])
        assert pair in ours_avail or pair in van_avail, \
            "no availability junction for %s against %s - it will read 'not yet unlocked'" % (
                subtype, HERO_ENABLE[agent])

    # An enable effect only opens the slot. If the faction permits no subtype of that agent
    # type the panel opens EMPTY, which is indistinguishable from the effect not working.
    # The permissions are not ours - they come from !cr_oldworld_campaign.pack, which creates
    # these factions - so check them THERE rather than shipping duplicate rows.
    van_subtypes = {r["key"] for r in load("agent_subtypes")[0]}
    for agent, subtype in HERO_SUBTYPES:
        assert subtype in van_subtypes, "agent subtype not in vanilla: %s" % subtype
    assert LORD not in van_subtypes, "%s collides with a vanilla agent subtype" % LORD

    # --- Tordrek's Gunnery Wight, whichever way WIGHT_ENABLED is set.
    if WIGHT_ENABLED:
        # it must BE vanilla, our row must differ from CA's in names_group and nothing else, and no
        # trace of the clone may survive anywhere in the fragments this generator writes.
        assert WIGHT_SUBTYPE in van_subtypes,         "%s is not a vanilla agent subtype - the wight is meant to be CA's own" % WIGHT_SUBTYPE
        wight = [r for r in arows if r[acols.index("key")] == WIGHT_SUBTYPE]
        assert len(wight) == 1, "expected exactly one Gunnery Wight subtype row"
        van_wight = clone_row(acols, van_typed("agent_subtypes", "key", WIGHT_DONOR_SUBTYPE)[0])
        differs = {c for i, c in enumerate(acols) if van_wight[i] != wight[0][i]}
        assert differs == {"names_group", "audio_vo_culture_override"},         "our agent_subtypes row may differ from CA's in names_group and audio_vo_culture_override only, differs in %s" % (
                sorted(differs),)
        assert wight[0][acols.index("audio_vo_culture_override")] == WIGHT_VO_CULTURE,         "without the VO culture override the engine discards every hero action - see the WIGHT_* block"
        ccols, _, crows = made["zz_agent_culture_details.tsv"]
        cul_ours = [r for r in crows if r[ccols.index("key")] == WIGHT_CULTURE_KEY]
        assert len(cul_ours) == 1, "expected exactly one agent_culture_details row of ours"
        donor = clone_row(ccols, van_typed("agent_culture_details", "key", int(WIGHT_CULTURE_KEY_DONOR))[0])
        cdiff = {c for i, c in enumerate(ccols) if donor[i] != cul_ours[0][i]}
        assert cdiff == {"key", "culture"},         "our agent_culture_details row may differ from CA's CST engineer row in key and culture only, differs in %s" % (
                sorted(cdiff),)
        assert cul_ours[0][ccols.index("agent")] == "engineer" and         cul_ours[0][ccols.index("associated_unit")] == WIGHT_UNIT and         cul_ours[0][ccols.index("culture")] == WIGHT_CULTURE,         "the culture row must bind the wight's unit to engineer in the Chaos Dwarf culture"
        assert wight[0][acols.index("names_group")] == WIGHT_NAMES,         "without a names_group the wight is christened out of the faction's Chaos Dwarf names"
        wperm = [r for r in frows if r[fs] == WIGHT_SUBTYPE]
        assert len(wperm) == 1 and wperm[0][ff] == TORDREK_FACTION and wperm[0][fa] == "engineer",         "the Gunnery Wight must be permitted to Tordrek's faction as an engineer"
    else:
        # OFF. Nothing may grant it: no permission row, no availability junction, no subtype
        # override and no culture row - any one of those left behind is a half-granted hero,
        # which is exactly the state that shipped broken.
        assert not [r for r in arows if r[acols.index('key')] == WIGHT_SUBTYPE], \
            'WIGHT_ENABLED is off but the agent_subtypes override is still written'
        assert not [r for r in frows if r[fs] == WIGHT_SUBTYPE], \
            'WIGHT_ENABLED is off but the wight is still permitted to a faction'
        assert not made['zz_effect_bonus_value_agent_subtype_junctions.tsv'][2], \
            'WIGHT_ENABLED is off but the availability junction is still written'
        assert not made['zz_agent_culture_details.tsv'][2], \
            'WIGHT_ENABLED is off but the agent_culture_details row is still written'
        # The military-group row for its character unit belongs to the other generator, and
        # the same flag has to reach it or the unit stays in the Chaos Dwarf roster alone.
        import gen_naval_horde_tordrek
        assert gen_naval_horde_tordrek.WIGHT_ENABLED is WIGHT_ENABLED, \
            'gen_naval_horde_tordrek.py reads a different WIGHT_ENABLED - it must import this one'

    # The clone is gone; a leftover row of it is a duplicate character in the panel.
    for fn, (fcols_, _m, frows_) in sorted(made.items()):
        for row in frows_:
            for cell in row:
                assert not any(cell == st for st in STALE_WIGHT),                     "%s still carries a clone row for %s" % (fn, cell)

    ours_here = {r[fs] for r in frows if r[ff] == FACTION}
    dupes = ours_here & {s for _a, s in HERO_SUBTYPES}
    assert not dupes, "hero permissions duplicate cr_oldworld's rows: %s" % sorted(dupes)
    check_oldworld_permissions()

    # auto_generate must match the overseer's, because the panel lists minted candidates and
    # nothing else mints this subtype. Proven by a live panel dump - see section 9.9.
    mine_row = [r for r in arows if r[acols.index("key")] == LORD][0]
    assert mine_row[acols.index("auto_generate")] == AUTO_GENERATE == "true",         "auto_generate must be true, or no candidate is ever minted and no card draws"

    mcols, _, mrows = made["zz_campaign_group_members.tsv"]
    assert len(mrows) == 3, "the ship group must hold Abnagg, Tordrek and the Fleetmaster"

    check_icons(made)

    print("checks ok: %d Fleetmaster grants over %d chains, %d units (all tier <= %d), "
          "%d hero rows on Abnagg's and Tordrek's ships, %d skill nodes reused, %d art sets"
          % (len(mine), len(CHAINS), len(units), CHD_MAX_TIER, len(hero), len(ours),
             ART_SETS))


def main():
    made = gen()
    check(made)
    if "--check" in sys.argv:
        print("--check: nothing written")
        return
    for fn, (cols, meta, rows) in made.items():
        write_tsv(fn, cols, meta, rows)
        print("%-56s %d rows" % (fn, len(rows)))
    fn, cols, meta, rows = gen_loc()
    write_tsv(fn, cols, meta, rows)
    print("%-56s %d rows" % (fn, len(rows)))


if __name__ == "__main__":
    main()
