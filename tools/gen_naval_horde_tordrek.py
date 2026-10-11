"""Tordrek's ship gets its own roster: the Black Kraken Armada.

Forks the six unit-granting chains of the shared naval horde. The existing six become
Abnagg's (`optional_required_horde_commander = derpy_abnagg`); six new
`derpy_chd_naval_kraken_*` chains become Tordrek's. Everything with no roster in it
(flagship, sail, helm, anchor) stays shared and ungated.

The lever is `building_chains_tables.optional_required_horde_commander`, an agent_subtype
key. It is already load-bearing in this pack - the two per-lord shipworks buildings use it -
and CA uses it on five `special_ship_<lord>` chains. Using it on a MULTI-LEVEL chain is
unattested; if the gate turns out to be ignored, the failure is a superset roster on both
ships, not a crash.

Tordrek's spec, from the player:
  - Vampire Coast buildings included             -> all 25 VC ship-chain units, cloned in,
                                                    each granted the CHD military group so a
                                                    Chaos Dwarf faction may actually recruit it
  - Chaos Dwarf units of tier 1-3 only           -> main_units.tier <= 3 on every CHD unit,
                                                    asserted; and no CHD unit is introduced
                                                    above chain level 3, so every chain top
                                                    level is drowned-only
  - no hobgoblin recruitment, but slaves allowed -> zero hobgoblin keys, both labourers kept
  - grounded in his lore, not picked at random   -> his own skill line names the chains:
      "Crew of the Drowned"    -> main_deck    "Hail of Harpoons"        -> gunports
      "Daemonpact of the Deep" -> hold         "Submersible Engineering" -> hull
      "Black Kraken Surfaces"  -> the leviathan and necrofex at the top of hold/hull

The lore file's one hard steer is honoured: "the reading to avoid is 'pirates': that is
Gordak's pack, and the two must not converge." Every VC unit taken here is a DROWNED thing -
zombie crew, depth guard, syreens, mournguls, hulks, leviathan. The swashbuckling half of
Vampire Coast lives in its lords and its cove buildings, none of which are touched.

Rewrites the EXPORTED TSVs in place (Modding Files/source/naval_horde/export), the way
gen_naval_horde_phase6.py does, so rows this script does not own cannot be lost -
import_tsv replaces the whole file.

    py tools/gen_naval_horde_tordrek.py            rewrite the TSVs
    py tools/gen_naval_horde_tordrek.py --check    checks only, write nothing
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "Modding Files", "source", "naval_horde", "export")

OLD = "derpy_chd_naval_horde"          # the shared chains, now Abnagg's
NEW = "derpy_chd_naval_kraken"         # Tordrek's fork
ABNAGG = "derpy_abnagg"
TORDREK = "derpy_tordrek"

# The six unit-granting chains. flagship/sail/helm/anchor carry no roster and stay shared.
CHAINS = ["main_deck", "gunports", "crows_nest", "cannons", "hold", "hull"]

C = "wh3_dlc23_chd_"
V = "wh2_dlc11_cst_"

# Cumulative expansion happens in build(); this lists only what each level ADDS.
# CHD keys stop appearing at level 3 - level 4 (and the top of each 3-level chain) is drowned.
NEW_AT = {
    "main_deck": {
        1: [V + "inf_zombie_deckhands_mob_0"],
        2: [C + "inf_chaos_dwarf_warriors", V + "inf_zombie_deckhands_mob_1"],
        3: [C + "inf_chaos_dwarf_warriors_great_weapons", C + "inf_infernal_guard",
            V + "mon_scurvy_dogs"],
        4: [V + "inf_depth_guard_0", V + "inf_depth_guard_1"],
    },
    "gunports": {
        1: [V + "inf_zombie_gunnery_mob_0"],
        2: [C + "inf_chaos_dwarf_blunderbusses", V + "inf_zombie_gunnery_mob_1"],
        3: [C + "inf_infernal_guard_fireglaives", V + "inf_zombie_gunnery_mob_3"],
        4: [V + "inf_zombie_gunnery_mob_2", V + "mon_rotting_prometheans_gunnery_mob_0"],
    },
    "crows_nest": {
        1: [V + "mon_fell_bats"],
        2: [C + "mon_lammasu", V + "cav_deck_droppers_0"],
        3: [C + "mon_great_taurus", V + "cav_deck_droppers_1"],
        4: [V + "cav_deck_droppers_2", V + "mon_terrorgheist"],
    },
    "cannons": {
        1: [C + "veh_magma_cannon", V + "art_mortar"],
        2: [C + "veh_deathshrieker_rocket_launcher", V + "art_carronade"],
        3: [V + "inf_deck_gunners_0"],
    },
    "hold": {
        1: [C + "inf_goblin_labourers", C + "inf_orc_labourers", V + "mon_bloated_corpse_0"],
        2: [C + "cav_bull_centaurs_axe", V + "mon_animated_hulks_0", V + "inf_syreens"],
        3: [V + "mon_mournguls_0", V + "mon_rotting_prometheans_0",
            V + "mon_rotting_leviathan_0"],
    },
    # hull_1 is primreq 0 / cost 1000, so it stays bonus-only exactly as Abnagg's does.
    # No k'daai here: main_units.tier is 4 on the Fireborn and 5 on the Destroyer.
    "hull": {
        2: [C + "veh_iron_daemon", C + "veh_skullcracker"],
        3: [V + "mon_necrofex_colossus_0"],
    },
}
LEVELS = {"main_deck": 4, "gunports": 4, "crows_nest": 4, "cannons": 3, "hold": 3, "hull": 3}

# Distinct from Abnagg's only where his would lie: his hold is chd_military_hobgoblins and
# Tordrek recruits no hobgoblins at all.
ICONS = {
    "main_deck": "chd_military_chaos_dwarf_infantry",
    "gunports": "chd_tower_ballistics",
    "crows_nest": "chd_military_beasts",
    "cannons": "chd_military_war_machines",
    "hold": "chd_tower_tribute_halls",
    # not chd_military_kdaai like Abnagg's: the tier cap took both k'daai off this ship
    "hull": "chd_factory_assembly_line",
}

NAMES = {
    "main_deck": ("Drowned Deck", "Crew of the Drowned"),
    "gunports": ("Harpoon Ports", "Hail of Harpoons"),
    "crows_nest": ("Kraken's Eye", "The Kraken's Eye"),
    "cannons": ("Pressure Battery", "Pressure Battery"),
    "hold": ("Flooded Hold", "Flooded Hold"),
    "hull": ("Pressure Hull", "Submersible Engineering"),
}

LONG = {
    "main_deck": "Tordrek's crew do not muster; they surface. What the Black Kraken drags "
                 "down it gives back sooner or later, still wearing its armour, still "
                 "holding its axe, and no longer troubled by the need to breathe.",
    "gunports": "Sealed iron hatches, each one a harpoon-thrower charged from the ship's own "
                "pressure lines. Munitions are never short here - the Armada makes its own, "
                "and the crews that load them have no appetite for rest.",
    "crows_nest": "The Kraken's Eye rides above the smoke on a lattice of riveted iron. What "
                  "watches from it is not always a lookout, and what it signals is not "
                  "always meant for the living.",
    "cannons": "Guns built the way a Dwarf engineer builds when nobody is left to tell him "
               "no: over-pressured, over-braced, and bolted to a deck that flexes rather "
               "than splits. They fire below the waterline as readily as above it.",
    "hold": "Chained ranks forward of the bulkhead, and behind it a flooded compartment the "
            "crew do not open. Whatever the Daemonpact put down there answers when the "
            "hatches are unsealed, and only then.",
    "hull": "A pressure shell, not a hull - sealed, ribbed and blind, built for a place with "
            "no air. The engines racked inside it were never meant to see daylight, and the "
            "one thing coiled beneath the keel was never meant to be a passenger.",
}
SHORT = {
    "main_deck": "Recruits the Armada's drowned crew and Dawi-Zharr marines.",
    "gunports": "Recruits harpoon and gunnery crews.",
    "crows_nest": "Recruits fliers and scouts.",
    "cannons": "Recruits the Armada's heavy guns.",
    "hold": "Recruits slaves, beasts and the things kept below the waterline.",
    "hull": "Recruits sealed war engines. Improves replenishment and recruitment capacity.",
}

# Cloned value-for-value from derpy_chd_naval_horde_hull - the ONLY one of the six chains
# that carries effects, and both halves matter: without the recruitment points, Tordrek's
# ship would have fewer recruitment slots than Abnagg's for no stated reason.
HULL_EFFECTS = [("wh_main_effect_force_all_campaign_replenishment_rate", [4, 6, 8]),
                ("wh_main_effect_force_all_recruitment_points", [2, 4, 6])]

FIRST_UNIT_KEY = 951000001      # Abnagg's rows run 950000001-950000059

# A building_units_allowed row is NOT enough to recruit a unit from another race. The unit
# must also sit in the recruiting faction's `factions_tables.military_group`, via
# units_to_groupings_military_permissions. CA does exactly this for the one cross-race unit a
# Chaos Dwarf building already grants: wh_main_chs_art_hellcannon is a Warriors of Chaos unit
# and CA lists it in wh3_dlc23_group_chaos_dwarfs. Without these 25 rows the cards are simply
# absent from the construction popup - no error, no tooltip, nothing.
CHD_GROUP = "wh3_dlc23_group_chaos_dwarfs"
# The Gunnery Wight is recruited as an AGENT, so it has no building_units_allowed row -
# but its character unit still needs a Chaos Dwarf military_group row, the same gate
# that made the VC line units' cards appear. CA's own record: the derpy_ clone that used
# to stand here is gone, and gen_naval_horde_admiral.py says why.
WIGHT_UNIT = "wh2_dlc11_cst_cha_gunnery_wight_0"
# ...but only while the wight is actually recruitable. gen_naval_horde_admiral.py owns that
# switch and it is currently off, so the unit drops out of the military group with the rest of
# the grant. One flag, imported rather than copied, so the two generators cannot disagree.
sys.path.insert(0, os.path.join(ROOT, "tools"))
from gen_naval_horde_admiral import WIGHT_ENABLED      # noqa: E402

# main_units.tier ceiling for the Chaos Dwarf half of the roster. Vampire Coast units are
# deliberately exempt: the Necrofex (4), Terrorgheist (5) and Rotting Leviathan (5) are the
# point of "most VC units under the Dreadfleet", and they are what Tordrek gets INSTEAD of
# the Chaos Dwarf top end.
CHD_MAX_TIER = 3

# --------------------------------------------------------- the Vampire Coast ownership lock
#
# Every unit above is Curse of the Vampire Coast content, and CA already tags all 25 in
# main_unit_ownership_content_pack_junctions against `wh2_dlc11_vampire_coast`. That gate has
# never been measured against a MODDED recruitment source on a machine without the DLC, and it
# cannot be measured from here - this machine owns it. So the pack carries its own lock as
# well, using the only lever the campaign API has:
# cm:add_event_restricted_unit_record_for_faction RESTRICTS, it never grants. The same shape as
# derpy_vraznak_units_confed.lua's house lock, minus the confederation half.
#
# The script is GENERATED from the roster above rather than hand-listed, so a unit added to
# Tordrek's chains cannot be left out of the lock - check() asserts the two lists are equal.
VC_PRODUCT = "TW_WH2_DLC11_VAMPIRE_COAST"          # ownership_products.key
VC_TOOLTIP = "ui_text_replacements_localised_text_derpy_vc_unit_locked"
VC_TOOLTIP_TEXT = ("Requires Total War: WARHAMMER II - Curse of the Vampire Coast.")
LOCK_SCRIPT = "derpy_chd_vc_unit_lock.lua"
# One file, four campaign folders - the same spread derpy_chd_naval_admiral.lua uses. These are
# the canonical mirror under Modding Files/pack; import_naval_horde.py adds them from there.
LOCK_CAMPAIGNS = ["cr_combi_expanded", "cr_darklands", "cr_oldworld", "wh3_main_combi"]
LOCK_DIR = os.path.join(ROOT, "Modding Files", "pack", "script", "campaign")


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

def read_tsv(name):
    p = os.path.join(EXP, "%s_tables.tsv" % name)
    with open(p, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    return lines[0].split("\t"), lines[1], [l.split("\t") for l in lines[2:]]


def write_tsv(name, cols, meta, rows):
    p = os.path.join(EXP, "%s_tables.tsv" % name)
    body = "\n".join(["\t".join(cols), meta] + ["\t".join(r) for r in rows]) + "\n"
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(body)


def blank(cols, **kw):
    row = [""] * len(cols)
    for k, v in kw.items():
        row[cols.index(k)] = v
    return row


def drop_ours(rows, cols, key_col):
    """Idempotence: strip any row this script wrote on a previous run."""
    i = cols.index(key_col)
    return [r for r in rows if not r[i].startswith(NEW)]


# --------------------------------------------------------------------------- the tables

def gen():
    made = {}

    # 1. building_chains - gate the six existing ones to Abnagg, add six for Tordrek.
    cols, meta, rows = read_tsv("building_chains")
    rows = drop_ours(rows, cols, "key")
    kc, gc = cols.index("key"), cols.index("optional_required_horde_commander")
    for r in rows:
        if r[kc] in ["%s_%s" % (OLD, c) for c in CHAINS]:
            r[gc] = ABNAGG
    order = 12
    for c in CHAINS:
        rows.append(blank(cols, key="%s_%s" % (NEW, c), chain_category="military",
                          in_encyclopedia="false",
                          building_superchain="%s_sch_%s" % (NEW, c),
                          optional_sort_order=str(order),
                          optional_required_horde_commander=TORDREK,
                          can_be_dismantled="true", is_foreign_slot_chain="false"))
        order += 1
    made["building_chains"] = (cols, meta, rows)

    # 2. superchains / instances / chain_set_items / availability_sets - one row per chain
    for name, key_col, mk in (
            ("building_superchains", "key",
             lambda c, cols: blank(cols, key="%s_sch_%s" % (NEW, c))),
            ("building_instances", "key",
             lambda c, cols: blank(cols, key="%s_%s" % (NEW, c), num_instances="1")),
            ("building_chain_set_items", "chain",
             lambda c, cols: blank(cols, chain="%s_%s" % (NEW, c),
                                   set="%s_secondary" % OLD, remove="false")),
            ("building_chain_availability_sets", "building_chain",
             lambda c, cols: blank(cols, building_chain="%s_%s" % (NEW, c),
                                   id="derpy_chd_bas_naval_horde"))):
        cols, meta, rows = read_tsv(name)
        rows = drop_ours(rows, cols, key_col)
        rows += [mk(c, cols) for c in CHAINS]
        made[name] = (cols, meta, rows)

    # 3. building_levels - the cost/primreq ladder copied from Abnagg's twin, level for level
    cols, meta, rows = read_tsv("building_levels")
    src = {r[cols.index("level_name")]: r for r in rows}
    rows = drop_ours(rows, cols, "level_name")
    for c in CHAINS:
        for n in range(1, LEVELS[c] + 1):
            r = list(src["%s_%s_%d" % (OLD, c, n)])
            r[cols.index("level_name")] = lvl(c, n)
            r[cols.index("chain")] = "%s_%s" % (NEW, c)
            r[cols.index("building_instance_key")] = "%s_%s" % (NEW, c)
            rows.append(r)
    made["building_levels"] = (cols, meta, rows)

    # 4. building_culture_variants
    cols, meta, rows = read_tsv("building_culture_variants")
    rows = drop_ours(rows, cols, "building")
    for c in CHAINS:
        for n in range(1, LEVELS[c] + 1):
            rows.append(blank(cols, building=lvl(c, n), description="%s_%s" % (NEW, c),
                              icon=ICONS[c], disables="false",
                              short_description="%s_%s" % (NEW, c), display_tooltip="true"))
    made["building_culture_variants"] = (cols, meta, rows)

    # 5. building_upgrades_junction
    cols, meta, rows = read_tsv("building_upgrades_junction")
    rows = drop_ours(rows, cols, "from")
    for c in CHAINS:
        for n in range(1, LEVELS[c]):
            rows.append(blank(cols, **{"from": lvl(c, n), "to": lvl(c, n + 1)}))
    made["building_upgrades_junction"] = (cols, meta, rows)

    # 6. building_set_to_building_junctions - all six are recruitment chains
    cols, meta, rows = read_tsv("building_set_to_building_junctions")
    rows = drop_ours(rows, cols, "building_chain")
    for c in CHAINS:
        rows.append(blank(cols, building_chain="%s_%s" % (NEW, c),
                          building_set="%s_set_recruitment" % OLD, exclude="false"))
    made["building_set_to_building_junctions"] = (cols, meta, rows)

    # 7. building_effects_junction - hull only
    cols, meta, rows = read_tsv("building_effects_junction")
    rows = drop_ours(rows, cols, "building")
    for eff, vals in HULL_EFFECTS:
        for n, v in enumerate(vals, 1):
            rows.append(blank(cols, building=lvl("hull", n), effect=eff,
                              effect_scope="force_to_force_own",
                              value="%.4f" % v, value_damaged="%.4f" % v,
                              value_ruined="0.0000"))
    made["building_effects_junction"] = (cols, meta, rows)

    # 8. building_units_allowed
    cols, meta, rows = read_tsv("building_units_allowed")
    rows = drop_ours(rows, cols, "building")
    for i, (b, u) in enumerate(build()):
        rows.append(blank(cols, building=b, unit=u, XP="0", key=str(FIRST_UNIT_KEY + i),
                          conditions="0", faction="", enabled="false"))
    made["building_units_allowed"] = (cols, meta, rows)

    # 9. units_to_groupings_military_permissions - the reason the cards were invisible.
    # A fresh fragment, so it is written rather than read: this table is not in the pack yet.
    cols = ["unit", "military_group"]
    # RPFM pads the meta row out to the column count, so the trailing tabs matter if a
    # round-trip diff against a freshly exported copy is to come back clean.
    meta = ("#units_to_groupings_military_permissions_tables;0;"
            "db/units_to_groupings_military_permissions_tables/derpy_chd_naval_horde"
            + "\t" * (len(cols) - 1))
    vc = sorted({u for _, u in build() if u.startswith(V)}
                | ({WIGHT_UNIT} if WIGHT_ENABLED else set()))
    made["units_to_groupings_military_permissions"] = (
        cols, meta, [[u, CHD_GROUP] for u in vc])

    return made


def gen_loc():
    p = os.path.join(EXP, "derpy_chd_naval_horde_loc.tsv")
    with open(p, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    head, meta = lines[0], lines[1]
    rows = [l for l in lines[2:] if NEW not in l]
    roman = ["", "I", "II", "III", "IV", "V"]
    for c in CHAINS:
        base, tip = NAMES[c]
        for n in range(1, LEVELS[c] + 1):
            rows.append("building_culture_variants_name_%s\t%s %s\tfalse"
                        % (lvl(c, n), base, roman[n]))
        rows.append("building_chains_chain_tooltip_%s_%s\t%s\tfalse" % (NEW, c, tip))
        rows.append("building_description_texts_long_description_%s_%s\t%s\tfalse"
                    % (NEW, c, LONG[c]))
        rows.append("building_short_description_texts_short_description_%s_%s\t%s\tfalse"
                    % (NEW, c, SHORT[c]))
    rows = [l for l in rows if not l.startswith(VC_TOOLTIP + "\t")]
    rows.append("%s\t%s\tfalse" % (VC_TOOLTIP, VC_TOOLTIP_TEXT))
    return p, "\n".join([head, meta] + rows) + "\n"


def gen_lock_script(units):
    """The campaign script that locks the Vampire Coast roster for anyone without the DLC."""
    listed = "\n".join('\t"%s",' % u for u in sorted(units))
    return LOCK_BODY % {"product": VC_PRODUCT, "tooltip": VC_TOOLTIP, "units": listed}


LOCK_BODY = """-- Curse of the Vampire Coast units, locked for a player who does not own the DLC.
--
-- GENERATED by tools/gen_naval_horde_tordrek.py from the Black Kraken Armada roster.
-- Edit the generator, not this file.
--
-- Tordrek's ship recruits Vampire Coast units, granted to the Chaos Dwarf military group in
-- units_to_groupings_military_permissions so their cards draw at all. CA tags every one of
-- them in main_unit_ownership_content_pack_junctions, which should hide them from a non-owner
-- on its own - this is the belt to that brace, because the DB gate has never been measured
-- against a modded recruitment source and cannot be measured on a machine that owns the DLC.
--
-- The API only ever takes recruitment AWAY: cm:add_event_restricted_unit_record_for_faction
-- has no granting counterpart. So the DB grants and this locks, the same shape as
-- derpy_vraznak_units_confed.lua.
--
-- Runs on EVERY load, not just a new game, and is idempotent in both directions - re-adding a
-- restriction already in the save is a no-op, and so is removing one that is not there. The
-- removal branch is not decoration: restrictions are written into the save, so a player who
-- buys the DLC mid-campaign carries them until this pass lifts them.

local PRODUCT = "%(product)s";
local TOOLTIP = "%(tooltip)s";

local UNITS = {
%(units)s
};

local function log(msg)
	out("XXX derpy_chd_vc_unit_lock " .. tostring(msg) .. " XXX");
end

cm:add_first_tick_callback(function()
	-- Everything inside a pcall: an error here would otherwise take the rest of the first-tick
	-- callbacks with it, and a missing roster lock is a far smaller bug than a dead campaign.
	local ok, err = pcall(function()
		local humans = cm:get_human_factions();
		for i = 1, #humans do
			local faction_key = humans[i];
			-- Two STRINGS, product key then faction key. AI factions are deliberately not
			-- touched: DLC ownership is a property of a human player, and CA's own
			-- cm:faction_has_dlc_or_is_ai answers true for every AI for that reason.
			local owns = cm:is_dlc_flag_enabled(PRODUCT, faction_key);
			for j = 1, #UNITS do
				if owns then
					cm:remove_event_restricted_unit_record_for_faction(UNITS[j], faction_key);
				else
					cm:add_event_restricted_unit_record_for_faction(UNITS[j], faction_key, TOOLTIP);
				end
			end
			log(faction_key .. " owns=" .. tostring(owns) .. " units=" .. tostring(#UNITS));
		end
	end);
	if not ok then
		log("first tick error: " .. tostring(err));
	end
end);

log("loaded");
"""


# --------------------------------------------------------------------------- checks

def check(made):
    cols, _, rows = made["building_units_allowed"]
    bi, ui, ki = (cols.index(x) for x in ("building", "unit", "key"))
    mine = [r for r in rows if r[bi].startswith(NEW)]
    theirs = [r for r in rows if not r[bi].startswith(NEW)]

    keys = [r[ki] for r in rows]
    assert len(keys) == len(set(keys)), "building_units_allowed key collision"
    # Count Abnagg's rows by his own prefix rather than as "everything that is not mine":
    # gen_naval_horde_admiral.py added a THIRD owner (derpy_chd_naval_admiral_*), and the old
    # `len(theirs) == 59` form counted his 38 rows as Abnagg's and failed.
    abnagg = [r for r in rows if r[bi].startswith(OLD + "_")]
    assert len(abnagg) == 61, "Abnagg's 61 rows must survive, found %d" % len(abnagg)

    units = {r[ui] for r in mine}
    # "hobgob", not "hobgoblin": wh3_main_chd_art_hobgob_bolt_thrower is a hobgoblin-crewed
    # artillery piece and would sail straight past the longer needle.
    hob = sorted(u for u in units if "hobgob" in u)
    assert not hob, "hobgoblin unit in Tordrek's roster: %s" % hob
    assert C + "inf_goblin_labourers" in units and C + "inf_orc_labourers" in units, \
        "slaves must stay recruitable"

    # every VC ship-chain unit is offered
    vc_all = {u for u in units if u.startswith(V)}
    assert len(vc_all) == 25, "expected all 25 Vampire Coast ship units, got %d" % len(vc_all)

    # CHD grants stop at chain level 3. The lists are cumulative, so the rule is about what
    # each level INTRODUCES: nothing Chaos Dwarf is ever introduced at level 4.
    for chain, adds in NEW_AT.items():
        chd = [u for u in adds.get(4, []) if not u.startswith(V)]
        assert not chd, "%s introduces a CHD unit at level 4: %s" % (chain, chd)

    # cumulative: each level is a superset of the one below
    by = {}
    for r in mine:
        by.setdefault(r[bi], set()).add(r[ui])
    for c in CHAINS:
        for n in range(2, LEVELS[c] + 1):
            lo, hi = by.get(lvl(c, n - 1), set()), by.get(lvl(c, n), set())
            assert lo <= hi, "%s is not a superset of level %d" % (lvl(c, n), n - 1)

    # every unit key exists in vanilla, and every level key is one we declared
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from read_vanilla_cache import load
    vanilla = {r["unit"] for r in load("building_units_allowed")[0]}
    missing = units - vanilla
    assert not missing, "unit keys not in vanilla building_units_allowed: %s" % sorted(missing)

    # the Chaos Dwarf half is capped at main_units.tier 3 - the player's actual constraint
    tier = {r["unit"]: r["tier"] for r in load("main_units")[0]}
    over = sorted((u, tier[u]) for u in units
                  if u.startswith(C) and tier.get(u, 0) > CHD_MAX_TIER)
    assert not over, "Chaos Dwarf units above tier %d: %s" % (CHD_MAX_TIER, over)

    # every Vampire Coast unit is granted the Chaos Dwarf military group, or its card will
    # simply not draw - plus the Gunnery Wight's character unit, which is recruited as an agent
    # and so appears in no roster of ours
    gcols, _, grows = made["units_to_groupings_military_permissions"]
    granted = {r[0] for r in grows if r[1] == CHD_GROUP}
    want_group = vc_all | ({WIGHT_UNIT} if WIGHT_ENABLED else set())
    assert granted == want_group, (
        "military-group rows do not match the drowned roster: %s" % sorted(want_group ^ granted))

    # The lock script is generated from this same set, so the two cannot drift apart - but
    # a hand edit to the .lua on disk can, and the .lua is what ships.
    body = gen_lock_script(vc_all)
    listed = {l.strip().strip(chr(34) + ",") for l in body.split(chr(10))
              if l.startswith(chr(9) + chr(34))}
    assert listed == vc_all, \
        "the DLC lock script and the roster disagree: %s" % sorted(listed ^ vc_all)
    assert VC_TOOLTIP in body and VC_PRODUCT in body, "lock script lost product or tooltip"
    for camp in LOCK_CAMPAIGNS:
        on_disk = os.path.join(LOCK_DIR, camp, "mod", LOCK_SCRIPT)
        if os.path.exists(on_disk):
            with io.open(on_disk, encoding="utf-8") as fh:
                assert fh.read() == body, \
                    "%s was hand-edited - the generator owns this file" % on_disk

    lcols, _, lrows = made["building_levels"]
    declared = {r[lcols.index("level_name")] for r in lrows}
    for r in mine:
        assert r[bi] in declared, "grant against an undeclared level: %s" % r[bi]

    # the Abnagg gate landed on exactly the six chains, and nothing else moved
    ccols, _, crows = made["building_chains"]
    kc, gc = ccols.index("key"), ccols.index("optional_required_horde_commander")
    gated = {r[kc]: r[gc] for r in crows if r[gc]}
    want = {"%s_%s" % (OLD, c): ABNAGG for c in CHAINS}
    want.update({"%s_%s" % (NEW, c): TORDREK for c in CHAINS})
    want["derpy_chd_naval_shipworks_abnagg"] = ABNAGG
    want["derpy_chd_naval_shipworks_tordrek"] = TORDREK
    # Subset, not equality: gen_naval_horde_admiral.py gates six chains of its own to a third
    # lord, and this script has no business asserting they are absent. What it must still
    # guarantee is that every chain IT owns carries the right gate, and that none of the twelve
    # went ungated - an ungated roster chain would show on every ship.
    wrong = {k: (gated.get(k), v) for k, v in want.items() if gated.get(k) != v}
    assert not wrong, "horde-commander gates wrong (got, want): %s" % sorted(wrong.items())

    # no Vampire Coast icon crept back in
    vcols, _, vrows = made["building_culture_variants"]
    ic = vcols.index("icon")
    bad = [r[vcols.index("building")] for r in vrows if r[ic].startswith("cst_")]
    assert not bad, "Vampire Coast icons still on %s" % bad

    print("checks ok: %d Tordrek grants, %d CHD (tier <= %d) + %d drowned units, "
          "%d chains forked, %d military-group grants"
          % (len(mine), len(units) - len(vc_all), CHD_MAX_TIER, len(vc_all), len(CHAINS),
             len(granted)))


def main():
    made = gen()
    check(made)
    if "--check" in sys.argv:
        print("--check: nothing written")
        return
    for name, (cols, meta, rows) in made.items():
        write_tsv(name, cols, meta, rows)
        print("%-40s %d rows" % (name, len(rows)))
    p, body = gen_loc()
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(body)
    print("%-40s %d rows" % ("loc", len(body.split("\n")) - 3))

    gcols, _, grows = made["units_to_groupings_military_permissions"]
    script = gen_lock_script({r[0] for r in grows if r[0].startswith(V)})
    for camp in LOCK_CAMPAIGNS:
        dest = os.path.join(LOCK_DIR, camp, "mod", LOCK_SCRIPT)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with io.open(dest, "w", encoding="utf-8", newline=chr(10)) as fh:
            fh.write(script)
        print("%-40s %d bytes" % (camp + "/" + LOCK_SCRIPT, len(script)))


if __name__ == "__main__":
    main()
