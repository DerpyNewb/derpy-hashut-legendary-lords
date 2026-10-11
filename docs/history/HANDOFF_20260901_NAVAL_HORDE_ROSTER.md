# Handoff 2026-09-01 - the naval horde gets a roster, effects and its own icons

Status: **Phases 5, 6 and the per-lord roster split built and deployed to both packs.**
Phase 5 and the chain gate are confirmed in a live campaign; the two faults that first launch
found are fixed in section 9 and are the only part not re-launched. Continues `HANDOFF_20260831_ABNAGG_TORDREK_SHIPBUILDING_SCOPE.md`, whose §25 and §26
carry the same material in the place a future reader of that file will look for it; this document
is the session record. Everything below is in
`!aa_derpy_hashut_legendary_lords.pack`, both copies byte-identical at sha1
**`9e01deb6d83010db15a37409c253c06282083f34`**.

Pack hash progression this session, each step verified by re-opening the saved pack in a fresh
RPFM session and decoding it - never by trusting `import_tsv`'s `"Success"`:

| sha1 | what landed |
|---|---|
| `8499c12a...` | start of session (2026-08-31's building-set fix) - kept as `Modding Files/Backup/Modpacks_inline_edit_backups/!aa_derpy_hashut_legendary_lords.pack.bak_prePhase5_20260901` |
| `30c25a67...` | Phase 5, `building_units_allowed_tables` 1 -> 59 rows |
| `dde9767a...` | `hull` chain moved into the recruitment panel group |
| `6e42d850...` | Phase 6, effects 16 -> 43 rows and all 37 icons repointed |
| `5246ba87...` | the Tordrek roster split - six forked chains, 22 tables re-imported, two Lua files patched |
| `9e01deb6...` | the two first-launch fixes - 25 military-group rows, and the k'daai dropped to hold main_units.tier <= 3 |

## 1. What was verified live, and what it settles

The player launched on the `dde9767a` build and sent a screenshot of the horde construction popup:
a named **"Ship Recruitment"** group, every chain drawn as a tier ladder, unit cards beside each
level. That single screenshot closes two open items at once -

- **`HANDOFF_20260831_ENCAMP_STANCE.md` §15 was right and is confirmed.** The empty popup really
  was `building_set_to_building_junctions_tables` holding only the 2 starting-kit rows. Nothing
  else was filtering.
- **Phase 5's roster renders.** Unit cards appear against the levels that grant them.

One thing did not work, and the player named it correctly: **no recruitment points, so nothing
could actually be recruited.** That is §2.

## 2. "No recruitment points" was an unbuilt phase, not a bug

Vampire Coast pays for a horde's recruitment capacity out of
`building_effects_junction_tables` - `captains_cabin` 1-5 grant
`wh_main_effect_force_all_recruitment_points` 2/3/4/5/6 and `hull` 1-3 grant 2/4/6. Phase 2 cloned
our chains' *shape* from VC but shipped **no effects at all** beyond growth on the flagship and
anchor. A horde whose buildings grant zero recruitment points has zero recruitment slots, and the
symptom is indistinguishable from a broken roster.

**The general shape worth keeping: a cloned chain skeleton with the effect rows left out looks
finished and is inert.** It renders, it builds, it charges, and it does nothing. This is the third
time on this build that a table left at its Phase-2 placeholder state produced a symptom that read
as a different bug entirely (the others: `building_upgrades_junction` in §14, the building sets in
§15, both of `HANDOFF_20260831_ENCAMP_STANCE.md`).

## 3. What Phase 5 shipped

`building_units_allowed_tables`, **1 row -> 59**, covering every unit-granting level.

| Chain | Role | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|
| `main_deck` | core melee | hobgoblin cutthroats | + chaos dwarf warriors | + cd warriors (gw), infernal guard | + infernal guard (gw), infernal ironsworn |
| `gunports` | missile | hobgoblin archers | + blunderbusses | + infernal guard fireglaives | + hobgob bolt thrower |
| `cannons` | artillery | magma cannon | + deathshrieker | + dreadquake mortar, hellcannon | - |
| `crows_nest` | lookouts, then fliers | hobgoblin sneaky gits | + lammasu | + great taurus | + bale taurus |
| `hold` | slave pens, stables | goblin + orc labourers | + wolf raiders x2 | + bull centaurs x3 | - |
| `hull` | war engines | *(bonus-only)* | iron daemon, skullcracker | + k'daai fireborn, destroyer | - |

29 distinct units. `tools/gen_naval_horde_units.py` holds the roster as editable text and emits
the full accumulated TSV to `Modding Files/source/naval_horde/`.

**One deliberate deviation from VC**: VC grants at `hull_3` only. Our `hull_1` is `primreq 0`,
`create_cost 1000`, `development_point_cost 1` - identical to `main_deck_1` - so a grant there
would be a turn-one Iron Daemon for the price of a hobgoblin hut. Grants start at `hull_2`
(primreq 2), and Phase 6 gave `hull_1` effects instead.

**`hull` also moved from `set_structure` to `set_recruitment`.** VC leaves hull in its structure
group because it grants exactly one unit at the very top of the chain; ours grants four across two
levels, so a player hunting war engines would have opened "Ship Recruitment" and found labourers.

## 4. What Phase 6 shipped

**Effects, 16 -> 43 rows**, values mirroring VC:

| Chain | Effects added |
|---|---|
| `flagship` 1-5 | recruitment points 2/3/4/5/6, upkeep 0/-5/-10/-15/-20 |
| `hull` 1-3 | replenishment 4/6/8, recruitment points 2/4/6 |
| `sail` 1-3 | movement range 10/20/30 |
| `helm` 1-3 | upkeep -5/-10/-15, Chaos corruption 4/6/8 |
| `anchor` 1-3 | agent-action army XP 20/40/80 (keeps its existing growth rows) |

`flagship_1` is half the starting kit, so a fresh horde begins with **2 recruitment points**.

**Icons, all 37 rows.** Every chain still carried a `cst_ship_*` icon - Vampire Coast art on a
Chaos Dwarf ship, inherited with everything else Phase 2 cloned.

| Chain | Icon | Chain | Icon |
|---|---|---|---|
| flagship | `chd_factory_settlement` | hold | `chd_military_hobgoblins` |
| main_deck | `chd_military_chaos_dwarf_infantry` | hull | `chd_military_kdaai` |
| gunports | `chd_tower_ballistics` | sail | `chd_factory_port` |
| cannons | `chd_military_war_machines` | helm | `chd_outpost_overseer_hut` |
| crows_nest | `chd_military_beasts` | anchor | `chd_outpost_mine` |

Tordrek's shipworks moved from `chd_factory_drill_workshop` to `chd_factory_furnace` so the two
per-lord buildings do not share art.

`tools/gen_naval_horde_phase6.py` holds the icon map and the effect ladder and rewrites the
**exported** TSVs in place rather than authoring them from scratch, so the two shipworks rows it
does not own cannot be lost to `import_tsv`.

## 5. Corrections found the hard way

- **`building_units_allowed_tables`' primary key is `key` alone.** `is_key: true` on that column
  only, and 6,396 distinct values over 6,396 vanilla rows. **`(building, unit)` is NOT unique** -
  vanilla has 48 duplicate pairs - so a duplicate-key check on this table that looks at the
  building/unit pair will report false positives and miss real collisions.
- **`XP` 0 / `conditions` 0 / `faction` empty / `enabled` false is correct, not a bug.** All 6,396
  vanilla rows carry it, `enabled`'s schema `default_value` is literally `"false"`, and the game
  demonstrably recruits from those rows. Do not "fix" `enabled` to true. (`conditions` is flagged
  `unused` in the definition patch, and `faction` is the dead column already recorded in memory.)
- **The best source of valid unit keys is vanilla's own `building_units_allowed` rows, not
  `main_units_tables`.** The plan's §8 said to Global Search `main_units`; filtering
  `building_units_allowed` on `building` starting `wh3_dlc23_chd_` gives **31 keys that are proven
  to exist AND proven recruitable from a CHD building**, which is strictly stronger, needs no
  dependency cache, and works with RPFM closed via `tools/read_vanilla_cache.py`.
- **The cumulative rule is inherited from VC's data, not independently proven.** CA's column
  description ("add all units unlocked by that building up to the specified level") is ambiguous
  read alone. VC's row counts disambiguate it: `hold_1: 2, hold_2: 5, hold_3: 6` against 3 new
  units at `hold_2` only reconciles if each level re-lists its predecessors.
- **An effect/scope pair must be checked against vanilla before it is written.**
  `wh3_main_effect_corruption_chaos_buildings` appears 212 times at `region_to_region_own` and
  only **9** times at `force_to_character_own_provincetext` - and the second is the one a horde
  building needs. Our own shipworks buildings use `faction_to_region_own` for the same effect,
  which is a settlement scope; copying that onto a horde chain would have shipped a dead row.
- **`building_culture_variants_tables.icon` is a bare filename** under `ui/buildings/icons/` in
  **`ui.pack`** (not ui2/ui3). CA ships 33 `chd_*` icons there.
- **Each `py` invocation against the RPFM MCP server is its own session.** `close_pack` on a pack
  the previous script opened fails with `Pack not found`; every script must
  `set_game_selected` then `open_packfiles` for itself.

## 6. Do not re-derive

- **VC's full ship effect table** is reproduced in §4's shape. `captains_cabin` and `hull` are the
  only two chains granting recruitment points; `cannons` grants army *abilities*,
  `gunports`/`hold` grant *agent recruitment*, and those three were deliberately not cloned
  because their effect keys are Vampire Coast specific.
- **The 31 CHD-recruitable unit keys**, from vanilla `building_units_allowed`. 29 are used; the
  two left out are `veh_iron_daemon_1dreadquake` and `veh_skullcracker_1dreadquake`.
- **Zero CHD `building_levels` rows are `faction_unique`**, and none of the 29 units is granted
  only by a landmark - so nothing in this roster is gated to one house.
- **`building_set_to_building_junctions` groups the construction popup, not the recruitment
  panel.** A unit granted from a chain filed under "structure" is still recruitable; the set only
  decides which header it is drawn under.
- **VC's cost/primreq ladder** (`captains_cabin` 1200/2500/5000/10000/20000 at primreq 0
  throughout; every secondary chain 1000-2000 at L1 rising to 10000 at its top, primreq 0-1 rising
  to 4). Phase 2 cloned it value-for-value, so our numbers are VC's numbers.
- **`tools/read_pack_index.py` lists any pack's paths with RPFM closed** - that is how the 33 CHD
  icon names were read out of `ui.pack`.

## 7. Still open

1. **Live-verify Phase 6**: build a flagship, confirm the recruit panel now offers slots, and
   confirm the construction popup draws CHD icons rather than ship art.
2. **`units_to_exclusive_faction_permissions` was never checked** - the table is not in
   `.skilltree_cache` and RPFM's dependency cache is not built. Low risk, since all 29 units are
   granted by ordinary CHD military chains in vanilla, but if one unit is missing from the popup
   while its neighbours render, look there first.
3. **Nothing has been balance-checked in a real campaign.** The roster is VC's ladder with CHD
   units dropped in; no pass has been made over whether a level-4 flagship's army is reasonable.
4. **Per-lord roster differentiation: BUILT, see section 8.**

## 8. The Black Kraken Armada - Tordrek's ship gets its own roster

The player asked for Tordrek's ship to stop being a copy of Abnagg's: Vampire Coast buildings
included, Chaos Dwarf units of tier 1-3 only, **no hobgoblin recruitment** but slaves still
allowed, most of the Vampire Coast Dreadfleet roster recruitable, and all of it grounded in
Tordrek's own lore rather than picked at random.

### 8.1 The one lever, and what it can and cannot do

`building_chains_tables.optional_required_horde_commander` takes an **agent_subtype** key. It
is the only per-lord gate that exists at chain level, and this pack already relies on it - the
two shipworks buildings carry `derpy_abnagg` / `derpy_tordrek`. CA has exactly **5 vanilla
rows**, all on `special_ship_<lord>` chains.

Three things it is **not**:

- It cannot be put on the vanilla `wh2_dlc11_vampirecoast_ship_*` chains. That would gate
  Vampire Coast's own hordes to Tordrek.
- It cannot fork a chain **set**. Chain sets bind to slot templates and both lords share
  `derpy_chd_naval_horde_secondary`, so "one lord, his own chain set" needs its own force type.
- It is **unattested on a multi-level chain**. CA's five are all single-building. If the engine
  turns out to ignore it there, the failure mode is a superset roster on both ships - not a
  crash, and visible immediately.

So the build is: fork the six unit-granting chains, gate the old six to Abnagg and the new six
to Tordrek. `flagship`, `sail`, `helm` and `anchor` carry no roster and stay shared and
ungated.

### 8.2 What shipped

`tools/gen_naval_horde_tordrek.py` holds the roster as editable text and rewrites the
**exported** TSVs in place (the Phase 6 pattern, so rows it does not own cannot be lost to
`import_tsv`). `tools/import_naval_horde.py` pushes all 22 exported TSVs back into the live
pack and saves in place - it reads each table's **version and destination path out of the
TSV's own `#table;version;path` meta line** rather than a hardcoded list, so a schema bump
cannot silently write the wrong version.

| Table | before | after |
|---|---|---|
| `building_chains` | 12 | 18 |
| `building_superchains` | 11 | 17 |
| `building_instances` | 12 | 18 |
| `building_chain_set_items` | 12 | 18 |
| `building_chain_availability_sets` | 12 | 18 |
| `building_levels` | 37 | 58 |
| `building_culture_variants` | 37 | 58 |
| `building_upgrades_junction` | 25 | 40 |
| `building_set_to_building_junctions` | 14 | 20 |
| `building_effects_junction` | 43 | 49 |
| `building_units_allowed` | 59 | 143 |
| `units_to_groupings_military_permissions` | 0 (new) | 25 |
| `derpy_chd_naval_horde.loc` | 76 | 115 |

The six new chains are `derpy_chd_naval_kraken_{main_deck,gunports,crows_nest,cannons,hold,hull}`,
cloned level-for-level from Abnagg's twins - same costs, same
`primary_slot_building_building_level_requirement`, same development-point costs, so the two
ships are the same shape and differ only in what walks off them.

### 8.3 The roster

**14 Chaos Dwarf units, 25 Vampire Coast, 84 grant rows, zero hobgoblins.** (Section 8.3 was
written at 15 CHD units and 85 rows; section 9.2 dropped one for the tier cap.)

| Chain | L1 | L2 | L3 | L4 |
|---|---|---|---|---|
| `main_deck` "Crew of the Drowned" | zombie deckhands | + chaos dwarf warriors, deckhands II | + cd warriors (gw), infernal guard, scurvy dogs | + depth guard x2 |
| `gunports` "Hail of Harpoons" | zombie gunnery mob | + blunderbusses, gunnery mob II | + infernal guard fireglaives, gunnery mob IV | + gunnery mob III, rotting prometheans gunnery mob |
| `crows_nest` "The Kraken's Eye" | fell bats | + lammasu, deck droppers | + great taurus, deck droppers II | + deck droppers III, terrorgheist |
| `cannons` "Pressure Battery" | magma cannon, mortar | + deathshrieker, carronade | + deck gunners | - |
| `hold` "Flooded Hold" | goblin + orc labourers, bloated corpse | + bull centaurs (axe), animated hulks, syreens | + mournguls, rotting prometheans, rotting leviathan | - |
| `hull` "Submersible Engineering" | *(bonus-only)* | iron daemon, skullcracker | + necrofex colossus | - |

**How "tier 1-3 Chaos Dwarf" was resolved.** Read against vanilla, the constraint is vacuous:
CHD's military chains top out at `building_levels.level == 2`, so **every Chaos Dwarf unit in
the game is already tier 1-3** and any selection satisfies the words. Taken literally it would
have handed Tordrek the whole CHD roster *plus* the whole Dreadfleet, i.e. a strictly better
ship than Abnagg's. The reading that makes the sentence do work is the ship's own ladder:
**no Chaos Dwarf unit is introduced above chain level 3, so every chain's top level is
drowned-only.** That is what the generator asserts, and it is what costs Tordrek the CHD
elites Abnagg keeps - infernal ironsworn, infernal guard great weapons, bale taurus, dreadquake
mortar, hellcannon, k'daai destroyer, hobgoblin bolt thrower.

**The lore steer was a real constraint, not decoration.**
`Modding Files/reference/concepts/data_07_tordrek.py` says outright: *"the reading to avoid is
'pirates': that is Gordak's pack, and the two must not converge."* Every Vampire Coast unit
taken here is a **drowned** thing - zombie crew, depth guard, syreens, mournguls, animated
hulks, leviathan, necrofex. The swashbuckling half of Vampire Coast lives in its **lords** and
its **cove buildings**, and none of those is touched. His own skill line supplied the chain
names: "Crew of the Drowned", "Hail of Harpoons", "Daemonpact of the Deep", "Submersible
Engineering", "Black Kraken Surfaces".

`hull` is the only one of the six carrying effects, and both halves were cloned -
replenishment 4/6/8 **and** recruitment points 2/4/6. Dropping the second would have given
Tordrek fewer recruitment slots than Abnagg for no stated reason, and section 2 is the record
of how invisible that failure is.

Icons are Abnagg's, except `hold`: his is `chd_military_hobgoblins`, and Tordrek recruits none,
so Tordrek's is `chd_tower_tribute_halls`.

### 8.4 The Lua, and why the staged copy was not the thing to edit

Gating `main_deck` to Abnagg breaks Tordrek's starting kit - `derpy_start_tordrek.lua` grants
`derpy_chd_naval_horde_main_deck_1` by `cm:add_building_to_force`, and that chain is now
Abnagg's. Both copies of the script (`cr_oldworld` and `cr_darklands`) now grant
`derpy_chd_naval_kraken_main_deck_1`.

**The staged `.lua` under `Modding Files/pack/` was 6,030 bytes against the packed copy's
6,435** - stale by an earlier in-pack edit, exactly the `pack-lua-carves-out-of-binary` memory.
The patch was made against bytes pulled out of the pack with `tools/read_pack_index.py`, syntax
-checked with `luac -p`, added back with `add_packed_files`, and only then copied over the
staged files so they stop drifting.

`effect_bonus_value_building_set_junctions` still points
`num_buildings_to_spawn_for_new_horde_army` at `derpy_chd_naval_horde_set_starting_kit`, which
still lists Abnagg's `main_deck_1`. That was left alone deliberately: the set is **inert on a
converted horde** (`wh3-starting-building-effect-needs-active-bundle`), the Lua grant is the
mechanism that actually lands, and adding a second candidate to a set consumed by a *count*
risks granting the wrong deck.

### 8.5 Verification

Every one of the 22 tables was re-exported from the **saved** pack in a fresh MCP session and
compared byte-for-byte against its source TSV - 0 mismatches. `import_naval_horde.py` runs
`check_keys` (the schema-driven duplicate-combined-key check) before it writes anything. The
generator's own `check()` asserts: no hobgoblin key anywhere in the roster, both labourers
present, all 25 Vampire Coast ship units offered, no CHD unit introduced at level 4, every
level a superset of the one below, every unit key present in vanilla
`building_units_allowed`, every grant against a level the same run declared, Abnagg's 59 rows
untouched, and the horde-commander gates landing on exactly the expected 14 chains.

`units_to_exclusive_faction_permissions` was checked for the first time (cached with
`tools/fetch_vanilla_tables.py`): its rows are overwhelmingly `allowed = true` grants, and the
7 that touch this roster all hand CHD/VC monsters to *Norsca* for the monster hunts. Nothing in
it blocks a Chaos Dwarf horde from recruiting Vampire Coast units.

> **Corrected 2026-09-02.** This paragraph originally read "**its 1,439 rows are `allowed =
> true` grants, not restrictions**". That is wrong, and the count was the tell: it is **1,423
> `true` and 16 `false`**. The table *can* deny. All 16 denials are Wood Elf units held back
> from `wh3_dlc21_wef_spirits_of_shanlin` — none touch this roster, so the conclusion above
> survives intact and no row needed changing. But "it never restricts, so checking it proves
> nothing" was the wrong general rule to write down: when a cross-race unit will not draw, this
> table is worth a look, it simply happens to be empty of Chaos Dwarf and Vampire Coast
> denials. The real permit-side requirement is the military group — see §9.1.

### 8.6 Still open

1. **Not launched.** The load-bearing unknown is whether
   `optional_required_horde_commander` gates a **multi-level** chain. Look at Tordrek's
   construction popup first: it should show six chains, none of them Abnagg's, and no hobgoblin
   card anywhere. Abnagg's should be unchanged.
2. **Existing Tordrek saves keep a building they can no longer build.** A horde already
   holding `derpy_chd_naval_horde_main_deck_1` keeps it; the chain is simply no longer offered.
   Dismantle and rebuild as the kraken deck, or start a new campaign.
3. **Balance is unmeasured.** Tordrek trades seven Chaos Dwarf elites for the entire Dreadfleet.
   Whether that is a fair trade has not been played.

## 9. Two corrections from the first launch

The player launched the `5246ba87` build and reported two things. The chain gate looks like it
worked: the popup showed **six** chains, not twelve, and no hobgoblin card. Twelve is what an
ignored `optional_required_horde_commander` would draw, since both chain sets sit on the same
slot template, so six is real evidence and section 8.1's open question is *probably* closed -
but one screenshot cannot say **which** six. The cheap confirmation is per-chain and
unambiguous, and comes free with the relaunch section 9.3 is already waiting on: Tordrek's
`hold` icon must be `chd_tower_tribute_halls` (Abnagg's is `chd_military_hobgoblins`) and his
`hull` must be `chd_factory_assembly_line` (Abnagg's is `chd_military_kdaai`).

### 9.1 A `building_units_allowed` row is not enough for a cross-race unit

**"No unit cards for VC in Tordrek's ship buildings."** Every one of the 25 Vampire Coast
grants was silently dropped: the levels rendered, the ladders rendered, the Chaos Dwarf cards
rendered, and the drowned ones simply were not there. No error, no greyed-out card, no tooltip.

The missing piece is `units_to_groupings_military_permissions_tables` (`unit`,
`military_group`, v0, 4,348 vanilla rows). A unit is recruitable by a faction only if it sits
in that faction's **`factions_tables.military_group`**. Every Vampire Coast unit is in
`wh2_dlc11_group_vampire_coast`; `cr_chd_black_kraken_armada` is
`wh3_dlc23_group_chaos_dwarfs`; the two never met.

**CA's own precedent proves it, and it was already in the data we had been reading all week.**
`wh_main_chs_art_hellcannon` is a *Warriors of Chaos* unit granted by a Chaos Dwarf building
(`wh3_dlc23_chd_military_war_machines`), and CA explicitly lists it in
`wh3_dlc23_group_chaos_dwarfs` alongside five other groups. It is the one cross-race unit on
the CHD roster, and it is the one that carries the extra permission row.

Fixed with 25 rows in a new fragment,
`db/units_to_groupings_military_permissions_tables/derpy_chd_naval_horde`, one per drowned
unit, all pointing at `wh3_dlc23_group_chaos_dwarfs`. Purely additive - it grants a
*permission*, not a recruitment source, so no faction gains a unit it has no building for.
Only `factions_tables.military_group` and this junction reference `groupings_military` at all
(checked across all 1,663 schema definitions), so there is nothing else the change can reach.

The one recruitment path that does **not** go through a building the faction owns is allied /
outpost recruitment, so it was checked separately: `allied_recruitment_unit_permissions` is a
**single-column table** (`unit`, 753 rows) - a global "this unit is allied-recruitable at all"
flag with no faction and no group column, so it cannot resolve through `military_group` and the
25 rows cannot leak into it. 37 of the roster's units, the drowned included, were already
listed there by CA before this session.

The alternative, had it leaked, would have been a private `derpy_chd_black_kraken` military
group on `cr_chd_black_kraken_armada`'s faction row holding the whole Chaos Dwarf roster plus
the drowned - much heavier, and not needed.

**This is a different table from the one checked in section 8.5 and it does the opposite job.**
`units_to_exclusive_faction_permissions` is all-grants and blocks nothing, which is true and
was correctly reported - but proving it does not block is not the same as proving something
else permits. The permission a cross-race recruit actually needs is the military group.

### 9.2 "Tier 1-3" means `main_units.tier`

Section 8.3 read "tier 1-3 Chaos Dwarf" as vacuous against the vanilla *building* ladder and
bound it to the ship's chain levels instead. The player meant **unit** tier, and there is a
literal column for it: `main_units_tables.tier`. Read that way the constraint is not vacuous at
all - six Chaos Dwarf units are above it:

| tier | unit |
|---|---|
| 4 | `mon_bale_taurus`, `mon_kdaai_fireborn`, `veh_dreadquake_mortar` |
| 5 | `mon_kdaai_destroyer`, `veh_iron_daemon_1dreadquake`, `veh_skullcracker_1dreadquake` |

Of the 15 Chaos Dwarf units picked in section 8.3, exactly one violated it -
`mon_kdaai_fireborn`, tier 4, at `kraken_hull_3`. Dropped, so the roster is **14 Chaos Dwarf
units, all tier 1-3**, and `kraken_hull` now tops out at the Necrofex Colossus. Its icon moved
off `chd_military_kdaai` accordingly, to `chd_factory_assembly_line`.

The generator now asserts `main_units.tier <= 3` for every unit whose key starts
`wh3_dlc23_chd_`. **Vampire Coast units are deliberately exempt** - the Necrofex (4),
Terrorgheist (5) and Rotting Leviathan (5) are the whole point of "most VC units under the
Dreadfleet", and they are what Tordrek gets *instead of* the Chaos Dwarf top end.

The chain-level rule from section 8.3 is kept as well, because it is doing separate work: it is
what puts the drowned at the top of each ladder rather than mixing them evenly through it.

### 9.3 State after the corrections

Pack sha1 **`9e01deb6d83010db15a37409c253c06282083f34`**, both copies. 23 tables round-trip
byte-identical against source. Tordrek's share is 84 of `building_units_allowed`'s 143 rows
(the other 59 are Abnagg's): 14 Chaos Dwarf units (all tier 1-3), 25 drowned, plus 25
military-group grants, zero hobgoblins.

One RPFM detail worth keeping: **RPFM pads a TSV meta line with trailing tabs out to the column
count.** A hand-authored meta line without them imports fine but makes every future round-trip
diff report a false mismatch on line 2.

## 10. The skill tree, split out

Giving that roster a skill tree is its own handoff:
**`HANDOFF_20260901_TORDREK_VC_SKILLS.md`**. In short - CA already ships a complete Vampire
Coast army line, so `wh2_dlc11_skill_cst_army_1..6` and `_8..11` went in as ten new nodes on
Tordrek's red lane (indent 4, tiers 13-22, in `derpy_tordrek_skills` only), plus seven Vampire
Coast effect rows folded into three skills he already had. No new skills, effects, unit sets,
loc or icons. Pack sha1 **`47b9458c1580ac4e3c12bb7a10884bb66147de52`**.

That handoff's section 6 also carries two corrections made to **this** file the same day: the
allied-recruitment check that clears section 9.1's 25 permission rows of any leak, and the
softening of section 9's chain-gate claim.
