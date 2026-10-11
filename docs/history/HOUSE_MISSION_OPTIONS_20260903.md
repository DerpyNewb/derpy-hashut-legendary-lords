# The ten houses — mission options for the HLL pack

Design pass, 2026-09-03. Companion to `GHORTH_MISSION_OPTIONS_20260903.md`, which covers the
eleventh lord. That document ends by splitting the work across two packs because Ghorth's faction
is vanilla; **these ten cannot be split.** `cr_chd_*` factions exist only in
`!aa_derpy_hashut_legendary_lords.pack`, so every mission below ships there or nowhere.

Mechanics come from `docs/MISSIONS.md`. Every key in this document was read out of the shipped
pack or the vanilla cache, not guessed. Nothing here is built.

---

## 1. The roster, verified

Read from `script/campaign/cr_oldworld/mod/derpy_start_<lord>.lua` in the **Workshop** copy of the
pack (the live one). `subtype` is the `agent_subtypes` key the start script spawns; note three
cases where the filename, the log string and the subtype disagree.

| Lord | Faction | Subtype | Start tile (cr_oldworld) | ToZ district | Annex ritual |
|---|---|---|---|---|---|
| Urzkhal the Chainlord | `cr_chd_house_of_khorakk` | `derpy_urzkhal` | 1767, 681 | Bloodline | `..._annex_khorakk` |
| Gargath of Baal | `cr_chd_house_of_baal` | `derpy_gargath` | 1580, 775 | Bloodline | `..._annex_baal` |
| Balur of Baalrgath | `cr_chd_fists_of_hashut` | `derpy_balur` | 1519, 427 | Bloodline | `..._annex_fists` |
| Vraznak the Horned | `cr_chd_horns_of_hashut` | `derpy_vraznak` | 1901, 861 | Bloodline | `..._annex_horns` |
| The Black Dwarf | `cr_chd_slaves_of_the_black_dwarf` | `derpy_black_dwf` | 1659, 1363 | Thrall | `..._annex_black_dwarf` |
| Abnagg Hellbeard | `cr_chd_warfleet_of_uzkulak` | `derpy_abnagg` | 160, 570 | Thrall | `..._annex_uzkulak` |
| Tordrek Hackhart | `cr_chd_black_kraken_armada` | `derpy_tordrek` | 1869, 451 | Thrall | `..._annex_black_kraken` |
| Bzaark Firespitter | `cr_chd_house_of_bzaark` | `derpy_bzaark` | 1481, 603 | Forge | `..._annex_bzaark` |
| Thymbrin Snakebeard | `cr_chd_snakebeards_artificers` | `derpy_snakebeard` | 1778, 947 | Forge | `..._annex_snakebeard` |
| Azeros the Iron | `cr_chd_house_of_azeros` | `derpy_azeros` | 1604, 1177 | Forge | `..._annex_azeros` |

Filename-vs-key traps, all three live in the shipped pack:
`derpy_start_khadon.lua` spawns **Vraznak**; `derpy_start_zarakh.lua` spawns **Snakebeard**;
the Black Dwarf's subtype is `derpy_black_dwf`, not `_black_dwarf` (the *ritual* suffix is
`black_dwarf`, spelled out). All annex rituals are prefixed `derpy_ritual_chd_toz_`.

**Faction-scoped is lord-scoped for all ten**, exactly as for Ghorth: each start script passes
`make_faction_leader = true`, so the faction has one legendary lord and no Lua presence gate is
needed. The exception is the same one, and it is *sharper* here than for Ghorth: the mod's own
Tower of Zharr tier five confederates houses into each other, so a mid-campaign player can be
holding three of these lords at once. Any objective phrased about *a character*
(`ACHIEVE_CHARACTER_RANK`, `ELIMINATE_CHARACTER_IN_BATTLE`) can then be satisfied by the wrong
one. Those need `SCRIPTED` if the intent is strictly that lord.

Two lords have skill trees and **no faction**: `derpy_gordak` and `derpy_warrhak`. They cannot
carry a faction-scoped mission at all. Gordak nevertheless owns three of the pack's 33 mission
rows (section 2) — and Abnagg, who *does* have a faction, owns none.

---

## 2. What is already there, and why none of it works

`GHORTH_MISSION_OPTIONS_20260903.md` section 2 established that 22 of the 33 rows are never
triggered. Three further findings from this pass, all verified against the shipped Workshop pack:

**2.1 The pack ships `missions_tables` and nothing else.** The full table list contains no
`cdir_events_mission_option_junctions`, no `cdir_events_mission_payloads`, no
`cdir_events_mission_issuer_junctions` — and no other `derpy_` pack supplies them
(scanned every pack in `Modding Files/Modpacks/`; only the unrun `derpy_test_missions.pack`
has them). So the eleven rows that *are* triggered carry **no objective parameters and no
reward**. `wh3_dlc23_chd_ancestor_hellshard_structure_derpy_ghorth` is
`CONSTRUCT_N_BUILDINGS_INCLUDING` with no `VAR_OBJECTIVE_BUILDING_LEVEL`, against 49 of 49
vanilla rows of that type that carry one.

Adding those three tables is therefore the first task for *any* mission work in this pack, new
or repaired.

**2.2 Three of the eleven hellshard triggers are mispaired.** From
`!!!narrative_chaos_dwarfs_new_factrions.lua`, identical in `cr_oldworld` and `cr_darklands`:

| Faction triggered | Mission key passed | Verdict |
|---|---|---|
| `cr_chd_slaves_of_the_black_dwarf` | `..._hellshard_structure_cr_chd_slaves_of_the_black_dwarf` | **No such row.** Dead. |
| `cr_chd_house_of_bzaark` | `..._hellshard_structure_derpy_black_dwf` | Wrong lord's row. `..._derpy_bzaark` is never used. |
| `cr_chd_warfleet_of_uzkulak` | `..._hellshard_structure_derpy_tordrek` | Wrong lord's row. Abnagg gets Tordrek's. |
| `cr_chd_black_kraken_armada` | — | Never triggered at all. |

The other seven pairs are correct. Textbook unvalidated-key territory: nothing errors, three
houses simply never receive the quest.

> **Corrected 2026-09-03, and this is the bigger half.** "The other seven pairs are correct" is
> true and irrelevant: the whole block is inside
> `if cm:is_new_game() and cm:model():is_multiplayer()`, and CA's own
> `wh3_dlc23_narrative_chaos_dwarfs:initialise()` carries the mirror gate
> `not is_multiplayer_campaign` naming only its three vanilla factions. **In singleplayer none of
> the eleven ever fired.** Both defects are fixed — see
> `HANDOFF_20260903_HELLSHARD_REPAIR.md` §2. Reading an `elseif` chain without reading the `if`
> above it is the mistake to not repeat.

**2.3 A typo'd key in the Ghorth document.** Its C1 gives
`SUBCULTURE = wh_main_grn_greenskins`. The real key is **`wh_main_sc_grn_greenskins`**
(verified against `cultures_subcultures`). Everything in section 5 below uses verified
subculture keys.

---

## 3. What HLL can reference without leaving the pack

| Wanted | In HLL? | Key shape |
|---|---|---|
| Missions, options, payloads, issuers | **3 of 4 missing** — add them (2.1) | — |
| Reward effect bundles | yes — `effect_bundles`, `effect_bundles_to_effects_junctions` | `derpy_*`; copy CA's `..._reward_dummy` idiom |
| Reward ancillaries | yes — `ancillaries`, `ancillary_sets`, `ancillary_to_effects` | the lord ancillaries, **not** the 430 house items (separate pack) |
| Unit sets for `KILL_X_ENTITIES_BY` | yes — `unit_sets`, `unit_set_to_unit_junctions` | authorable in-pack |
| Rituals / ritual categories | yes — `rituals`, `ritual_categories`, `campaign_group_rituals` | `derpy_ritual_chd_toz_annex_*`, `DISTRICTS_ANNEX_T5_A/B/C` |
| Naval-horde buildings | yes — `building_levels` and the rest of the set | `derpy_chd_naval_horde_*`, `derpy_chd_naval_kraken_*` |
| Lord/agent subtypes | yes — `agent_subtypes` | `derpy_<lord>`, plus `derpy_chd_admiral` |
| Vanilla CHD buildings, units, pooled resources, subcultures | vanilla | verified lists in section 7 |
| Per-lord unit-pack units (Golden Legion, Ravagers, Tenderizer, Temple Guard) | **no** | separate Workshop packs — section 6 |
| House ancillaries (430) | **no** | `derpy_chd_house_ancillaries.pack` — section 6 |

---

## 4. The shared spine — three missions every house gets

One row per lord, the lord key as the suffix, exactly as the existing 33 rows are named and as CA
names its own. Eleven rows per mission (ten houses plus Ghorth), one trigger pair each. These are
the cheapest three in the document and they exercise nothing that could be missing.

| # | Mission | `mission_type` | Parameters | Payload | Rating |
|---|---|---|---|---|---|
| S1 | **The Tribute Halls** — the house pays its due to Zharr-Naggrund | `CONSTRUCT_N_BUILDINGS_INCLUDING` | `BUILDING_LEVEL = wh3_dlc23_chd_tower_tribute_halls_3` | `TREASURY` + labour transaction | **Safe** — 49 rows, `BUILDING_LEVEL` on 49/49 |
| S2 | **Hashut's Due** — feed the Bull-God in blood | `KILL_X_ENTITIES` | `AMOUNT_INT = 500` | `FACTION_POOLED_RESOURCE_TRANSACTION` labour | **Safe** — 23 rows, `AMOUNT_INT` on 23/23 |
| S3 | **A Seat at the Table** — take a district of the Tower | `PERFORM_RITUAL` | `RITUAL_CATEGORY = DISTRICTS_INDUSTRY_T1`, `AMOUNT_INT = 2` | conclave-influence transaction | **Safe type, thin params** — 21 rows but `RITUAL_CATEGORY` on only 3 |

A fourth, deliberately held back: **The Subjugation** — `PERFORM_RITUAL` on
`RITUAL_CATEGORY = DISTRICTS_ANNEX_T5_A`, `AMOUNT_INT = 1`. It is the only mission that shows off
the mod's own fifth tier, and it is **Untested twice over**: no vanilla mission targets a modded
ritual category, and "annex any one house" spans three categories (A Bloodline, B Thrall,
C Forge), so it needs either three rows, or one row with the three semicolon-joined — a shape
only attested for `VAR_OBJECTIVE_UNIT`, never for `RITUAL_CATEGORY`. Build it second, after
S1-S3 prove the plumbing; the answer it produces is one every future Hell-Forge and Tower
mission needs.

---

## 5. Per-lord options

Three per lord, drawn from that lord's own unique skill line so the quest matches the character
the mod already built. Ratings as in the Ghorth document: **Safe** = the type has vanilla rows and
these exact `VAR_OBJECTIVE_*` keys are the ones vanilla uses with it; **Untested** = safe type,
but the *value* is one of this mod's own keys; **Needs script** = no `mission_type` expresses it.

### Urzkhal the Chainlord — `cr_chd_house_of_khorakk`

Skill line: Taskmaster's Lash, Chains of Domination, Slave Economy Savant, The Ledger of Flesh,
Fodder for the Guns. He is an accountant with a whip.

| # | Mission | `mission_type` | Parameters | Rating |
|---|---|---|---|---|
| U1 | **The Ledger of Flesh** — the column must balance | `HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE` | `POOLED_RESOURCE = wh3_dlc23_chd_labour`, `AMOUNT_INT = 2000` | Safe (5 rows, both params 5/5) |
| U2 | **Fodder for the Guns** — chains off, blades on | `OWN_N_UNITS` | `UNIT = wh3_dlc23_chd_inf_orc_labourers;wh3_dlc23_chd_inf_goblin_labourers`, `AMOUNT_INT = 8` | Safe (22 rows, both 22/22) |
| U3 | **The Collection** — the debtors are greenskins, and they pay in bodies | `RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_OF_SUBCULTURE` | `SUBCULTURE = wh_main_sc_grn_greenskins`, `AMOUNT_INT = 3` | Safe (3 rows, both 3/3) |

### Gargath of Baal — `cr_chd_house_of_baal`

Skill line: Infernal Daemonologist, Daemonbinding Mastery, Screaming Iron, Living Flame of
Hashut. Fire-daemons in iron shells.

| # | Mission | `mission_type` | Parameters | Rating |
|---|---|---|---|---|
| G1 | **Bind the K'daai** — chain a fire daemon into iron | `OWN_N_UNITS` | `UNIT = wh3_dlc23_chd_mon_kdaai_destroyer`, `AMOUNT_INT = 2` | Safe |
| G2 | **The Iron Cages** — widen what the Hell-Forge will hold | `PERFORM_RITUAL` | `RITUAL_CATEGORY = HELLFORGE_CAPS_KDAAI`, `AMOUNT_INT = 2` | Safe type, thin params (`RITUAL_CATEGORY` 3/21); the category is CA's |
| G3 | **Stoke the Furnace** — the binding pits at full tier | `CONSTRUCT_N_OF_A_BUILDING` | `BUILDING_LEVEL = wh3_dlc23_chd_military_kdaai_3`, `AMOUNT_INT = 2` | Safe (5 rows, both 5/5) |

### Balur of Baalrgath — `cr_chd_fists_of_hashut`

Skill line: Ironclad Discipline, Shield of Hashut, Fists of Hashut, Zealot of the Black Altar.
A warlord second, a zealot first.

| # | Mission | `mission_type` | Parameters | Rating |
|---|---|---|---|---|
| B1 | **The Unholy Legion** — the Guard fielded in full | `OWN_N_UNITS` | `UNIT = wh3_dlc23_chd_inf_infernal_guard;wh3_dlc23_chd_inf_infernal_guard_fireglaives;wh3_dlc23_chd_inf_infernal_guard_great_weapons`, `AMOUNT_INT = 6` | Safe |
| B2 | **The Black Altar** — raise Hashut's own house | `CONSTRUCT_N_BUILDINGS_INCLUDING` | `BUILDING_LEVEL = wh3_dlc23_chd_tower_temple_of_hashut_1` | Safe |
| B3 | **Break the Throng** — the kin of the west, five hosts of them | `DEFEAT_N_ARMIES_OF_FACTION` | `NUM_ARMIES = 5`, `SUBCULTURE = wh_main_sc_dwf_dwarfs`, `REQUIRES_VICTORY` | Safe (44 rows; `NUM_ARMIES` 44/44, `SUBCULTURE` 22) |

### Vraznak the Horned — `cr_chd_horns_of_hashut`

Skill line: Beastmaster's Command, Thickened Hide, Hide of the Iron Bull, Stampede of Hashut.

| # | Mission | `mission_type` | Parameters | Rating |
|---|---|---|---|---|
| V1 | **The Herd of Hashut** | `OWN_N_UNITS` | `UNIT = wh3_dlc23_chd_cav_bull_centaurs_axe;wh3_dlc23_chd_cav_bull_centaurs_dual_axe;wh3_dlc23_chd_cav_bull_centaurs_greatweapons`, `AMOUNT_INT = 6` | Safe |
| V2 | **Hide of the Iron Bull** — drive the herd through the slag pits | `PERFORM_RITUAL` | `RITUAL_CATEGORY = HELLFORGE_CAPS_BULL_CENTAURS`, `AMOUNT_INT = 2` | Safe type, thin params |
| V3 | **The Beast Pens** — pens deep enough for a Taurus | `CONSTRUCT_N_BUILDINGS_INCLUDING` | `BUILDING_LEVEL = wh3_dlc23_chd_military_beasts_3` | Safe. Also the Temple Guard's recruitment building — see section 6 |

### The Black Dwarf — `cr_chd_slaves_of_the_black_dwarf`

Skill line: Granite Bulwark, Immovable Phalanx, The Unbreached Wall, The Granite Legion,
Wrought of Living Stone. He is the only one of the ten who wins by not moving.

| # | Mission | `mission_type` | Parameters | Rating |
|---|---|---|---|---|
| D1 | **The Unbreached Wall** — the capital raised to its fifth tier | `CONSTRUCT_N_BUILDINGS_INCLUDING` | `BUILDING_LEVEL = wh3_dlc23_chd_settlement_tower_4` | Safe |
| D2 | **The Granite Legion** — shields locked, plate double-struck | `OWN_N_UNITS` | `UNIT = wh3_dlc23_chd_inf_infernal_ironsworn`, `AMOUNT_INT = 4` | Safe |
| D3 | **Wrought of Living Stone** — the petrification, welcomed | `ACHIEVE_CHARACTER_RANK` | `AMOUNT_INT = 20`, `NUM_CHARACTERS = 1` | Safe (11 rows, `AMOUNT_INT` 11/11) — **confederation caveat, section 1** |

An alternative D1 with more character and more risk: `HAVE_CHARACTER_WITHIN_RANGE_OF_POSITION`
at his start tile, the Ghorth section 7.3 template field-for-field with
`LOGICAL_POSTION 1659;1363`. It is Safe by row count (77/77 on all six parameters) and unique to
him by construction, but it needs **one row per campaign** because the combi campaigns place him
elsewhere (section 8).

### Bzaark Firespitter — `cr_chd_house_of_bzaark`

Skill line: Unstable Ordnance, Reckless Abandon, Madman's Insight, Firespitter's Prototype,
The Proven Pattern. Deliberately an unstable lord (the `+20` miscast is not a bug).

| # | Mission | `mission_type` | Parameters | Rating |
|---|---|---|---|---|
| Z1 | **Proof by Fire** — volume over precision | `KILL_X_ENTITIES` | `AMOUNT_INT = 750` | Safe |
| Z1' | *variant* — killed specifically by his guns | `KILL_X_ENTITIES_BY` | `UNIT_SET = <new>`, `AMOUNT_INT`, `OVERRIDE_TEXT` | Untested — needs a `unit_sets` row (HLL has the table) and a `mission_text_text_*` loc key; `OVERRIDE_TEXT` is on 25/25 vanilla rows, so it is mandatory |
| Z2 | **The Proven Pattern** — one design in a hundred survives testing | `CONSTRUCT_N_OF_A_BUILDING` | `BUILDING_LEVEL = wh3_dlc23_chd_military_war_machines_3`, `AMOUNT_INT = 2` | Safe |
| Z3 | **Firespitter's Prototype** — a battery of his own making | `OWN_N_UNITS` | `UNIT = wh3_dlc23_chd_veh_magma_cannon;wh3_dlc23_chd_veh_deathshrieker_rocket_launcher;wh3_dlc23_chd_veh_dreadquake_mortar`, `AMOUNT_INT = 4` | Safe |

### Thymbrin Snakebeard — `cr_chd_snakebeards_artificers`

Skill line: Master Artificer, Precision Engineering, The Iron Road, Deathshrieker Doctrine.

| # | Mission | `mission_type` | Parameters | Rating |
|---|---|---|---|---|
| T1 | **Deathshrieker Doctrine** — longer tubes, hotter charge | `OWN_N_UNITS` | `UNIT = wh3_dlc23_chd_veh_deathshrieker_rocket_launcher`, `AMOUNT_INT = 3` | Safe |
| T2 | **The Iron Road** — the line runs where he says it runs | `CONSTRUCT_N_BUILDINGS_INCLUDING` | `BUILDING_LEVEL = wh3_dlc23_chd_factory_assembly_line_3` | Safe |
| T3 | **Masterwork Artillery** — arm the Artificers | `HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE` | `POOLED_RESOURCE = wh3_dlc23_chd_armaments`, `AMOUNT_INT = 400` | Safe |

### Azeros the Iron — `cr_chd_house_of_azeros`

Skill line: Master Smith, Ironclad Legions, Industrial Supremacy, Ten Thousand Hammers,
The Master's Mark.

| # | Mission | `mission_type` | Parameters | Rating |
|---|---|---|---|---|
| I1 | **Ten Thousand Hammers** — every furnace open, shifts worked to death | `HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE` | `POOLED_RESOURCE = wh3_dlc23_chd_raw_materials`, `AMOUNT_INT = 600` | Safe |
| I2 | **The Master's Mark** — his sigil struck into every plate | `OWN_N_UNITS` | `UNIT = wh3_dlc23_chd_inf_infernal_ironsworn_ror`, `AMOUNT_INT = 1` | Safe. Uses the RoR so it does not collide with D2 |
| I3 | **The Great Refinery** — industry before war | `CONSTRUCT_N_OF_A_BUILDING` | `BUILDING_LEVEL = wh3_dlc23_chd_factory_refinery_3`, `AMOUNT_INT = 2` | Safe |

### Abnagg Hellbeard — `cr_chd_warfleet_of_uzkulak`

Skill line: Fleetmaster's Command, Tyrant of the Waves, Infernal Artillery Specialist,
Siege Mastermind. Owns a `CHARACTER_BOUND_HORDE` ship, so his quests can be about the ship.

| # | Mission | `mission_type` | Parameters | Rating |
|---|---|---|---|---|
| H1 | **The Hellbeard Puts to Sea** — the flagship to tier three | `CONSTRUCT_N_BUILDINGS_INCLUDING` | `BUILDING_LEVEL = derpy_chd_naval_horde_flagship_3` | **Untested** — safe type, but no vanilla mission counts a *horde* building. Answer this once and every naval quest inherits it |
| H2 | **Tyrant of the Waves** — raiding is the trade | `EARN_X_AMOUNT_FROM_RAIDING` | `AMOUNT_INT = 5000` | Safe (4 rows, `AMOUNT_INT` 4/4) |
| H3 | **Siege Mastermind** — five coasts stripped | `OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS` | `AMOUNT_INT = 5` | Safe (12 rows, 12/12) |

### Tordrek Hackhart — `cr_chd_black_kraken_armada`

Skill line: Submersible Engineering, Rivalry's Wrath (Red Brokk), Daemonpact of the Deep,
Crew of the Drowned. Currently the only house with **no** hellshard mission at all (2.2).

| # | Mission | `mission_type` | Parameters | Rating |
|---|---|---|---|---|
| K1 | **The Black Kraken Surfaces** — the hull rebuilt to take the deep | `CONSTRUCT_N_BUILDINGS_INCLUDING` | `BUILDING_LEVEL = derpy_chd_naval_kraken_hull_3` | Untested, same question as H1 |
| K2 | **Rivalry's Wrath** — the grudge he took to Barak Varr, answered | `DEFEAT_N_ARMIES_OF_FACTION` | `NUM_ARMIES = 5`, `SUBCULTURE = wh_main_sc_dwf_dwarfs`, `REQUIRES_VICTORY` | Safe. A named-faction version needs `DESTROY_FACTION`, which is **string route only** (absent from the Assembly Kit; 13 mod call sites) |
| K3 | **Crew of the Drowned** — not every hand aboard is breathing | `OWN_N_UNITS` on his Vampire Coast units | — | **Do not build as written.** Those 25 units are DLC-gated and `derpy_chd_vc_unit_lock.lua` locks them for players without Vampire Coast — an uncompletable quest for anyone who lacks the DLC. Use `wh3_dlc23_chd_inf_infernal_ironsworn`, or a `SCRIPTED` objective that checks the lock first |

---

## 6. Three dependency edges to keep out of these rows

A mission key is unvalidated in both directions: a `VAR_OBJECTIVE_UNIT` naming a unit that is not
installed does not error, the objective simply never completes.

1. **Per-lord unit packs.** Bzaark's Golden Legion / Naphtaglaive / Obliterators, Balur's Ravagers
   and Goliath Hellcannon, Snakebeard's Artificers and Tenderizer, and Vraznak's Temple Guard and
   Hashut's Chosen all live in **separate Workshop packs**. Tempting for exactly the lords whose
   quests they suit, and wrong: HLL is playable without them.
2. **The 430 house ancillaries.** `ADD_ANCILLARY` reaching a `derpy_chd_house_ancillaries` item is
   the same edge. HLL's own lord ancillaries are fine — it ships `ancillaries_tables`.
3. **`derpy_chd_units` / `derpy_chd_tank` / `derpy_chd_aeromachines`.** Their Hell-Forge categories
   (`HELLFORGE_CAPS_ZHARRGRON`, `_GYROCOPTERS`) look like ideal `PERFORM_RITUAL` targets for Bzaark
   and Snakebeard, and are not in HLL. Note the start scripts *already* name units from these packs
   (`chd_wt_magma_spewer`, `chd_train_magmalobs`, `chd_turtle_tank_carrier`), so the pack is a de
   facto soft dependency — but a start army that spawns short is survivable and a quest that can
   never complete is not.

Everything in sections 4 and 5, apart from H1/K1 and the three flagged rows, uses vanilla keys or
HLL's own.

---

## 7. Verified key lists

```
factions            cr_chd_house_of_khorakk  cr_chd_house_of_baal  cr_chd_fists_of_hashut
                    cr_chd_horns_of_hashut   cr_chd_slaves_of_the_black_dwarf
                    cr_chd_warfleet_of_uzkulak  cr_chd_black_kraken_armada
                    cr_chd_house_of_bzaark   cr_chd_snakebeards_artificers
                    cr_chd_house_of_azeros   (+ wh3_dlc23_chd_conclave, vanilla, Ghorth)

subcultures         wh3_dlc23_sc_chd_chaos_dwarfs   wh_main_sc_dwf_dwarfs
                    wh_main_sc_grn_greenskins       wh_main_sc_grn_savage_orcs
                    wh2_dlc11_sc_cst_vampire_coast

pooled resources    wh3_dlc23_chd_labour     wh3_dlc23_chd_raw_materials
                    wh3_dlc23_chd_armaments  wh3_dlc23_chd_workload
                    wh3_dlc23_chd_efficiency wh3_dlc23_chd_conclave_influence

CHD building levels (131 vanilla; the ones these missions use)
                    wh3_dlc23_chd_tower_tribute_halls_1..5   wh3_dlc23_chd_tower_temple_of_hashut_1
                    wh3_dlc23_chd_tower_furnace_1..2         wh3_dlc23_chd_tower_ballistics_1..2
                    wh3_dlc23_chd_settlement_tower_1..5      wh3_dlc23_chd_settlement_factory_1..3
                    wh3_dlc23_chd_military_kdaai_1..3        wh3_dlc23_chd_military_beasts_1..3
                    wh3_dlc23_chd_military_war_machines_1..3 wh3_dlc23_chd_military_hobgoblins_1..2
                    wh3_dlc23_chd_military_chaos_dwarf_infantry_1..3
                    wh3_dlc23_chd_factory_assembly_line_1..3 wh3_dlc23_chd_factory_refinery_1..3
                    wh3_dlc23_chd_factory_drills_1..2        wh3_dlc23_chd_outpost_mine_1..3

naval horde (HLL's own)
                    derpy_chd_naval_horde_flagship_1..5  _hull_1..3  _sail_1..3  _helm_1..3
                    derpy_chd_naval_horde_anchor_1..3  _cannons_1..3  _hold_1..3
                    derpy_chd_naval_horde_crows_nest_1..4  _gunports_1..4  _main_deck_1..4
                    derpy_chd_naval_kraken_{hull,cannons,hold}_1..3
                    derpy_chd_naval_kraken_{crows_nest,gunports,main_deck}_1..4
                    derpy_chd_naval_shipworks_abnagg_1   derpy_chd_naval_shipworks_tordrek_1
                    derpy_chd_admiral   (the Fleetmaster - agent type "general", i.e. a LORD,
                                         so RECRUIT_AGENT does not apply to it)

CHD agent types     champion (Bull Centaur Taurruk)  engineer (Infernal Castellan)
                    wizard (Daemonsmith)             spy  colonel
                    - RECRUIT_AGENT / EMBED_AGENT / PERFORM_ANY_AGENT_ACTION take these,
                      not the subtype key

ritual categories   DISTRICTS_{SORCERY,INDUSTRY,MILITARY}_T1..T3   TOZ_TIER_4
                    HELLFORGE_CAPS_{KDAAI,BULL_CENTAURS,FLYING_BEASTS,MELEE_INFANTRY,
                                    MISSILE_INFANTRY,WARMACHINES}
                    LABOUR_ACTIONS  DRILL_RAW_MATERIALS  DRILL_TREASURY
                    DISTRICTS_ANNEX_T5_A (Bloodline) / _B (Thrall) / _C (Forge)   <- mod's own

art (24 CHD eventpics ship; chd/generic does NOT, and all 33 existing rows use it)
                    chd/zharr_temple  chd/hell_forge  chd/zharr_boon  chd/politics
                    chd/faction  chd/celebration  chd/economy_down  chd/land_victory
issuer              CLAN_ELDERS
```

---

## 8. Traps that apply to every row above

- **Four campaign folders, two region namespaces.** The ten houses live in `cr_oldworld` and
  `cr_darklands` (both use `cr_oldworld_region_*` keys — verified, the darklands scripts do not
  have their own namespace); `cr_combi_expanded` carries only Abnagg, the Black Dwarf and Ghorth,
  under `wh3_main_combi_region_*`.
  > **Corrected 2026-09-03, measured in game:** IEE carries **both** namespaces at once. The
  > mod's own factions hold `cr_combi_region_*` regions — Abnagg's capital is
  > `cr_combi_region_zermuda`, the Black Dwarf's `cr_combi_region_gahhuks_encampment` — while
  > vanilla's stay `wh3_main_combi_region_*` (Ghorth: `wh3_main_combi_region_zharr_naggrund`).
  > `ime_derpy_abnagg.lua` *spawns* into `wh3_main_combi_region_barak_varr` and is not a guide to
  > the capital either. Read the region at runtime, or check it per faction — never assume it
  > from the campaign. See `HANDOFF_20260903_HELLSHARD_REPAIR.md` §13.1. Any region- or position-keyed objective needs one row per
  namespace, and the trigger script needs a copy in each folder.
- **Add the three missing tables first** (2.1) — versions `cdir_events_mission_option_junctions` 2,
  `cdir_events_mission_payloads` 2, `cdir_events_mission_issuer_junctions` 1, `missions` **0**
  (RPFM also offers `missions` v6, which is the wrong shape).
- **One random unique `id` per junction row**, `1 .. 2147483646`, unique across every installed mod.
- **Objective text is loc-only.** `mission_text_tables` does not ship; any `OVERRIDE_TEXT` or
  `SCRIPTED` objective needs `mission_text_text_<key>` in HLL's own `.loc` and no DB row.
- **`ui_icon` is a red herring** — `rom_event_mission.png`, like CA's 3,049 rows; the file ships
  nowhere and the diagnostic is noise.
- **`cm:trigger_mission` returning false because a `CND_*` failed is silent.** Gate on
  `CND_SUBCULTURE wh3_dlc23_sc_chd_chaos_dwarfs` at most, and strip conditions one at a time when
  a mission does not appear.
- **`derpy_test_missions.pack`** (built 2026-09-03, undocumented, apparently never run) already
  carries a two-mission smoke test — one pure-DB `HAVE_AT_LEAST_X_MONEY`, one `SCRIPTED` through
  the string route, both with payloads and an issuer. Run it before writing 33 more rows.

---

## 9. Recommended order

1. **Run `derpy_test_missions.pack`.** It answers "do our option junctions and payloads work at
   all" for the cost of a launch, and it exists already.
2. ~~**Add the three missing tables to HLL and repair the eleven existing rows**~~ — **DONE
   2026-09-03**, `tools/gen_hellshard_missions.py`, see
   `HANDOFF_20260903_HELLSHARD_REPAIR.md`. It also found a defect 2.2 missed: the whole trigger
   block sits inside `if ... cm:model():is_multiplayer()`, and CA's own script covers only its
   three vanilla factions in singleplayer, so **all eleven were dead in singleplayer**, not just
   the three mispaired ones. Not yet run in a campaign.
3. **Build the shared spine (section 4, S1-S3).** 33 rows, three shapes, no new mechanics — and
   the same three rows give every house a quest, including Abnagg and Tordrek, who currently have
   none that fires.
4. **Answer H1** (does a `CONSTRUCT_*` objective see a horde building?). It gates every naval
   quest for two lords, and nothing else in the document depends on the answer.
5. **Then the per-lord sets (section 5)**, cheapest first: the eight `OWN_N_UNITS` and
   `CONSTRUCT_N_*` rows are all Safe and share one shape apiece.
6. **The Subjugation last** — it is the most interesting mission here and the only one that can
   fail for a reason nothing else in the document shares.
