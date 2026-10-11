# Handoff 2026-09-08 — Ghorth's victory routes, rebuilt on VCO's measured shape

Ghorth's three victory routes became **five**, and the roster-wide checks around them were
tightened against counts taken from CA's `victory_objectives.lua` and from all 107 of Victory
Conditions Overhaul's mission files.

**State at the end:** deployed **15,839,573** bytes, sha256 `2b455b05d81eb3f2`, in both
`Modding Files/Modpacks/` and
`F:\SteamLibrary\steamapps\workshop\content\1142710\3432966208\` (byte-identical, hashed both
sides). Round-tripped out of the saved pack in a fresh MCP session. **Nothing has been run in a
campaign.** Not uploaded to the Workshop. Pre-change backup:
`!aa_derpy_hashut_legendary_lords.pack.bak_preghorthroutes_20260908`.

---

## 1. Why five

`GHORTH_MISSION_OPTIONS_20260903.md` §1 names three identity pillars out of his own skill tree —
**Sorcerer-Prophet of Hashut**, **Master of the Conclave**, **Tyrant of Zharr-Naggrund**. The
three-route shape covered the second one twice (`The Seat of Zharr` and `The Conclave's Writ`
were both Tower/influence) and the other two not at all. Two routes were added, not padded on:
each new one is a pillar that had no route.

He is also the only house that *can* carry a wider Tower route: he belongs to **no annex group**,
and every other house sits inside one of the three and may not annex itself.

| # | Route | Pillar | Objectives | Icon |
|---|---|---|---|---|
| I | **The Blackening** | Sorcerer-Prophet | both `DISTRICTS_SORCERY_T3` seats; the Temple of Hashut; a lord at rank 30 | `short` |
| II | **The Seat of Zharr** | Master of the Conclave | 2 Bloodline annexations, 2 Thrall annexations, 200 Conclave Influence | `long` |
| III | **Hashut's Ledger** | the war | Dwarfs **and** Greenskins in one `DESTROY_FACTION`; 35 armies broken | `ultimate` |
| IV | **The Conclave's Writ** | Tyrant of Zharr-Naggrund | Tribute Halls 5; Temple Guardhouse 5; 400 Conclave Influence | `domination` |
| V | **The Tribute of Slaves** | the tribute economy | 5,000 battle captives; 3,000 Labour; three tier-3 Refineries | `long` |

Routes I–III keep the roster's craft / Tower / war meaning at their old **index**, so the shared
slot icons still say the same thing for every house. Their old *contents* moved: the Tower route
had been sitting at index 0 wearing the `short` icon every other house gives its craft route.

Route index **is** slot index. A house with three routes uses slots 1–3 and never sees 4 and 5;
the two extra `missions` rows cost nothing when unused. Vanilla's own `wh3_combi_*` set runs
`tree_y` 0..4, and VCO ships 4 routes for 4 of its factions, so five nodes in one tree is
attested on both sides.

## 2. What was measured, and what it overturned

CA's `script/campaign/main_warhammer/victory_objectives.lua` (out of `data_script.pack`) and
VCO's 107 `script/vco-*/<campaign>/<faction>/missions.lua` were both parsed, not skimmed.

| # | Measured | Effect |
|---|---|---|
| 1 | Multi-target `DESTROY_FACTION` is **one objective with a `faction` line per target** — CA 93 objectives / 258 lines, VCO 181 / 528, neither ever writes two objectives | **Ghorth's war route was wrong.** It shipped as two separate `DESTROY_FACTION` objectives, a shape neither source writes |
| 2 | `CONSTRUCT_N_OF_A_BUILDING` and `CONSTRUCT_N_BUILDINGS_INCLUDING` always carry `total` — CA 4/4 and 1/1, VCO 23/23 and 4/4 | **Four objectives across the roster had no count at all.** All four fixed; `check()` now refuses a count-N objective with no N |
| 3 | The most objectives of ONE type either source puts in a single victory objective set is **2** (`PERFORM_RITUAL`, `CONTROL_N_REGIONS_FROM`) | Repeating a type is attested, three of one is not. `check()` caps it, which is what forced route II into two annex districts rather than three |
| 4 | `override_text` appears only on `SCRIPTED` and the four region/province types — CA 88 + 28, and all 113 of VCO's are `CONTROL_N_REGIONS_FROM` | **Killed the plan** to give every objective a written prose line. It is not attested on a counter objective, so `check()` refuses it |
| 5 | VCO uses 11 objective types CA never uses in a victory objective; **6 of them are map-agnostic** — `DEFEAT_N_ARMIES_OF_FACTION`, `CAPTURE_X_BATTLE_CAPTIVES`, `RECRUIT_UNIT`, `ASSASSINATE_X_CHARACTERS`, `MAINTAIN_N_ALLIANCES`, `EARN_X_AMOUNT_FROM_RAIDING` | The one-file/four-maps rule bans region and province objectives, so CA leaves this file very little. Two of the six are now in Ghorth's routes |
| 6 | `vassalization_valid` — a valueless `DESTROY_FACTION` flag, CA 5 uses, VCO 33 | Added. Ghorth already holds Zhatan as a vassal, so a vassal counting as settled is the Conclave's own idea of a result |
| 7 | VCO **does** complete its `vco_dummy` flavour headers — `vco-listeners.lua:48`, a `FactionTurnStart` listener on every human faction, every turn | **Corrects `HANDOFF_20260907_VICTORY_ROUTES.md`**, which read them as never completed. The SCRIPTED-header technique is usable; §4 says why it was still not taken |
| 8 | `DISTRICTS_SORCERY_T3` holds exactly two seats in vanilla `rituals`; `TOZ_TIER_4` four | `total 2` on route I is "the whole top of the ladder", not an open-ended grind |
| 9 | `wh3_dlc23_chd_tower_temple_guardhouse_5` exists in vanilla `building_levels` | Route IV's second hall. The generator's `BUILDING_LEVELS` hand-list did not have it; it does now |
| 10 | Vanilla `victory_types` has exactly four icon names and reuses them freely — `short` on 7 of 18 rows | Repeating `long` at index 4 is vanilla practice, so five routes still ship no art |

## 3. What changed in the workspace

| Path | What |
|---|---|
| `tools/gen_victory_routes.py` | Ghorth's five routes; `VCO_VICTORY_TYPES` and `ATTESTED_VICTORY_TYPES`; `CONDITION_ONLY_ON`; `TYPES_NEEDING_TOTAL`; `MAX_SAME_TYPE_PER_ROUTE`; five slot rows; the missions loc; per-house route counts throughout |
| `tools/import_victory_routes.py` | `EXPECTED_ROWS` derived from `ROUTES` rather than `len(HOUSES) * 3`, which stopped being the row count |
| `Modding Files/source/victory_routes/*.tsv` | 35 victory types (was 33), 5 missions rows (was 3), 50 loc rows (was 33) |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_chd_victory_routes.lua` | 19,921 bytes (was 18,497) |
| `docs/VICTORY_CONDITIONS.md` | §11.1b (VCO's added vocabulary and which of it is map-agnostic), §11.2 corrected, §12 rewritten for five routes and the new checks |

## 4. The blank titles, and the flavour text that was not taken

**Every victory route drew a blank title, for all eleven houses.** The `missions` rows carried
`localised_title` in the DB and no loc entry, and the runtime reads the loc
(`wh3-mission-title-is-loc-driven`). Fixed at the root: `build_loc_tsv()` now writes all three
derived keys per slot, and `--selftest` asserts each one exists and **agrees with its own DB
column**, since a row that disagrees with its loc is a trap for whoever opens the table next.

The slot title is shared by every house, so it says `Victory Route I`, not the route's name —
the name is on the `victory_types` node, which is where the panel draws it.

**What was designed and then dropped:** a written line per objective, VCO-style. Two independent
findings killed it. `override_text` is not attested on a counter objective (measurement 4), and
the alternative — VCO's `SCRIPTED` header plus the turn-start completer (measurement 7) — makes
**every route in the file** depend on one listener still running. A victory condition cannot be
patched out of a running save; that is the same reasoning that kept `SCRIPTED` out on 2026-09-07,
and it survives knowing how VCO makes it work. If it is wanted later, the listener in §11.2 of
`VICTORY_CONDITIONS.md` is the whole of it — and skip the `<dummy>` marker.

## 5. What was verified

* `--check` clean: 11 houses, 35 routes, 35 victory types, 5 mission slots.
* `--selftest` green, now **8** deliberate breaks rather than 4. The four new ones: three
  objectives of one type in a route; a count-N objective with no `total`; `override_text` on a
  type neither source pairs it with; a sixth route with only five slot rows to hang it on. It
  also runs the shipped Lua under Lua 5.1.5 and asserts Ghorth is issued exactly five.
* `luac -p` clean. `check_lua_api.py`: 0 suspect calls. `check_lua_undeclared.py`: clean.
* Every key used was read back out of vanilla before it shipped:
  `wh3_dlc23_chd_tower_temple_guardhouse_5`, `_tower_tribute_halls_5`,
  `_tower_temple_of_hashut_1`, `_factory_refinery_3` against `building_levels`;
  `DISTRICTS_SORCERY_T3` against `rituals`.
* Imported and then re-verified in a **fresh MCP session** against the saved file: 50 / 5 / 35
  rows round-tripped back out as TSV, the script present, all four superseded
  `derpy_chd_victory_objectives.lua` copies confirmed gone. Verified again directly against the
  **deployed Workshop copy**, then hashed on both sides.

**A trap worth one line: the pack changed under us after the importer exited.** The Modpacks copy
was 15,839,573 bytes immediately after the save and 15,852,913 four minutes later, same 445
paths, same content, both round-tripping clean — RPFM's backup autosave re-saving a pack the
importer's MCP session had left open. So *hash straight after saving is not a stable identity*.
The fix taken was to verify the Workshop copy directly and re-sync Modpacks from it, which is
also the right direction: the Workshop folder is the live one.

## 6. What is open

**AMENDED 2026-09-09 - it has now been run, and it found a defect.** In two live Ghorth
campaigns (`script_log_080926_2354.txt`, `script_log_090926_0917.txt`, both cr_combi_expanded)
the wrapper suppressed CA's victory missions for `wh3_dlc23_chd_conclave` and all five routes
were issued with no error - and the victory panel drew **two nodes, II and III**. Root cause:
every `CONSTRUCT_*` objective needs a `faction` line, which `gen_victory_routes.py` never
emitted, so routes I, IV and V were dead on arrival. This file's own reference doc already
carried CA's comment saying so ("these objectives will fail if we don't add them here"); the
generator simply did not do it. Fixed in `mission_string()`, with a selftest assertion
(mutation-proven) and a bullet in `VICTORY_CONDITIONS.md` §10. **19 of the 35 routes across all
eleven houses carried the defect**, so this was never Ghorth-only. Redeployed 15,853,539 B sha
`5ccdc66ffabeb5c0` to both Modpacks and the Workshop folder, round-tripped 50/5/35 in a fresh
session, 17/17 `CONSTRUCT` objectives verified carrying the line by byte-reading the saved pack.
**Re-run and confirmed the same day: all five nodes draw.** Which answers three of this
section's questions at once - the victory panel does NOT clip at four the way the Tower of
Zharr's districts do; `CONSTRUCT_N_BUILDINGS_INCLUDING`, `CONSTRUCT_N_OF_A_BUILDING`,
`CAPTURE_X_BATTLE_CAPTIVES` and `vassalization_valid` are all accepted; and route I drawing means
`ACHIEVE_CHARACTER_RANK` with `include_generals` is accepted too, since a rejected objective
takes its whole mission with it. Route V renders its three objectives in full, counter included
("Current total: 0 / 5000"), and `wh3_dlc23_chd_factory_refinery_3` carries no
`resource_requirement`, is not `only_in_capital` and is not `faction_unique`, so 3 of them is a
settlement-growth objective and not a map lottery. What a run still has to show is the far end:
whether completing a route actually ends the campaign.

1. **Still nothing has been run.** The 2026-09-07 list stands unchanged — whether
   `cm:trigger_custom_mission_from_string` accepts the blocks, whether the nodes draw, whether
   the wrapper suppresses CA's, whether completing a route ends the campaign. Five new questions
   join it, all Ghorth's:
   - do **five** nodes draw in the victory panel, or does it clip at four the way the Tower of
     Zharr's districts did;
   - `CAPTURE_X_BATTLE_CAPTIVES` and `DEFEAT_N_ARMIES_OF_FACTION` are VCO-attested but have
     never run in *this* pack;
   - `PERFORM_RITUAL` on `DISTRICTS_SORCERY_T3` assumes Ghorth does not start holding both
     seats. Nothing in the mod pre-claims them (his start scripts touch no ritual, and the annex
     pre-claim is own-house only, which he has none of), but **CA's startpos was not checked**;
   - `vassalization_valid` has never been used in this pack;
   - two `CONSTRUCT_N_BUILDINGS_INCLUDING` objectives in one route (route IV) is inside the
     two-per-type cap but is not itself attested — CA writes that type once, ever.
2. **A dead route is a dead node, not a soft lock.** The five are alternatives, so an
   unachievable one costs a line in the panel and nothing else. This is what makes the
   unattested-shape risk above tolerable, and it is only true while no route is SCRIPTED.
3. **A new campaign is required.** Issued from an `is_new_game()` first-tick callback.
4. **The other ten houses still carry three routes each**, and their objectives are still two
   apiece. The generator now supports any count up to the number of slot rows, so widening them
   is data, not code.

## 7. Do not re-derive

* **CA's victory objective types and conditions, counted**: see
  `gen_victory_routes.CA_VICTORY_TYPES` and the four rules in §2. The tally script is three
  regexes over `script/campaign/main_warhammer/victory_objectives.lua`, extracted from
  `data_script.pack` — the pack is Zstd, so a byte-grep of it returns nothing.
* **VCO's added vocabulary**: `VICTORY_CONDITIONS.md` §11.1b, with per-type use counts and which
  are map-bound.
* **VCO completes its dummies.** `vco-listeners.lua:42-50`. Do not re-read the mission files
  looking for it; it is in the listener file, not beside the objective.
* **VCO's route shape**: 3 routes for 129 factions, 4 for 4; 1 to 4 engine-evaluated objectives
  per route, most often 2 or 3; a per-route `issuer` row and a per-route `effect_bundle` +
  `add_ancillary_to_faction_pool` payload. The issuers and payloads are **not** copied — a
  payload fires at campaign victory, and an issuer needs a DB row and a png.
* **`victory_types` icons**: `short`, `long`, `ultimate`, `domination`, and nothing else. Reuse
  is vanilla practice, not a shortcut.
* **The `missions` row's three loc keys** are what the runtime reads; the DB columns are
  decoration. Write both and make them agree.
