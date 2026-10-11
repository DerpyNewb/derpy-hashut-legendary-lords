# Victory routes at VCO quality, phase 2 of 5: Lore text

Status: design approved in chat 2026-10-11 ("do phase 2 first", then "Approve"). Roadmap and
phase 1: `2026-10-11-victory-routes-vco-parity-design.md`. Phase 1 is built and deployed to the
Workshop folder (`66551d8b`), not uploaded and not yet seen in game.

The author's two choices: the paragraph is a plain objective line for now (no UI restyle, no
`[[col:]]` tags; restyling waits for an in-game look), and explainer lines go above the ritual
objectives, written once per ritual category rather than once per route.

## 1. What the player gets

- Every route opens with a short paragraph in the house's voice: what the house wants and why
  this road leads there. 46 paragraphs: the 43 existing routes plus three new ones for the Uzkul
  Mingol.
- Directly above every Tower of Zharr annex objective and every Hell-Forge objective, one line
  that says where to go and what the ritual does. Eight lines in all, one per ritual category.
- The Uzkul Mingol Company (`cr_chd_skullstack`), the only playable house with no routes today,
  gets three.

Nothing about winning changes. The engine-checked objectives, rewards and keys stay as they are.

## 2. Mechanism

### 2.1 The lines

Both kinds are a `SCRIPTED` objective, VCO's header shape:

```text
objective
{
    type SCRIPTED;
    script_key derpy_route_lore;
    override_text mission_text_text_derpy_route_lore_<route>;
}
```

- `<route>` is the route's `victory_type` key without its `derpy_victory_type_` prefix, so
  `derpy_victory_type_house_of_khorakk_1_ledger_of_flesh` reads its paragraph from
  `mission_text_text_derpy_route_lore_house_of_khorakk_1_ledger_of_flesh`. A map-gated route's two halves
  share the one paragraph.
- An explainer uses `mission_text_text_derpy_route_explain_<category>`, the ritual category in
  lower case (`..._explain_hellforge_caps_kdaai`).
- Every line, paragraph or explainer, carries the same `script_key`, so one call completes all
  of them. VCO does the same with `vco_dummy`.

`ROUTES` stays as it is. The lines are not written into it. `mission_string()` inserts them as it
emits: the paragraph first, then each explainer directly above its `PERFORM_RITUAL` objective.
The text lives in two new dicts beside `ROUTES`: `LORE`, keyed by the `victory_type` key, and
`EXPLAIN`, keyed by ritual category. Quests are untouched.

Attested: VCO puts up to nine `SCRIPTED` lines in one mission, and 111 of its 403 mission blocks
have one somewhere other than first place (counted 2026-10-11 over every `missions.lua` in
`victory_conditions_overhaul.pack`). Blocks of seven or more objectives occur 34 times there; our
longest route becomes seven (Let the World Tremble: four objectives, a paragraph, two
explainers). Our own string route with `SCRIPTED` and `override_text` was measured in game on
2026-09-03 (MISSIONS.md, "First build"): it issued, drew, and completed on the call.

### 2.2 The completer

A `SCRIPTED` objective completes only through `cm:complete_scripted_mission_objective`. Without
the call, a route can never be won. The completer is VCO's own shape (`vco-listeners.lua`,
`vco_dummy_missions_check`):

- A `FactionTurnStart` listener, condition `context:faction():is_human()`.
- It returns at once unless the saved value `derpy_route_lore_v1` is set. The issue block sets
  it, in the same first tick where it issues the routes, so it is set only in a game whose routes
  carry the lines. A save from before phase 2 never has it, and its routes, which have no line
  with that key, never see the call. Multiplayer never has it either, since no route is issued
  there.
- Otherwise, for every one of the five slot keys `derpy_route_victory_1..5`, it calls
  `cm:complete_scripted_mission_objective(faction_key, slot_key, "derpy_route_lore", true)`,
  then logs one line. All five, not `#ROUTES[faction]`: a three-route house gets two calls on
  missions it does not have, which VCO shows is harmless (below), and a later build that changes
  a house's route count cannot leave a route in a running save with a line nobody completes.
  For the same reason it needs no `ROUTES` lookup: the saved value is set only when a human's
  routes were issued.
- The body is wrapped in `pcall`, and a failure is logged.
- It is registered in the first-tick list beside the phase 1 listeners, above the
  `is_new_game()` return, so it runs on every load. The route lives in the save; the listener
  does not.

The lines show open on the first turn and ticked from the second at the latest, as VCO's do.

**One departure from the design approved in chat: no `mission_is_active_for_faction` guard.**
Our quests use it, but it has never been measured on a victory mission, and a wrong `false` would
leave every route blocked forever. VCO calls the completer with no guard, every turn, for every
human faction, including factions it issued no routes to: its loader `require`s
`script/<mod>/<campaign>/<faction_key>/missions` inside a `pcall`, and a faction with no file gets
no missions but still gets the call. So a call on a missing mission is harmless in practice.

A call on a mission that exists but lacks the script key is NOT shown harmless by VCO. Its 42
mission blocks with no `SCRIPTED` line looked like evidence, but 39 of them sit in folders named
`GORROK`, `HARKON` and so on, which are not faction keys, so the loader never reaches them. That
case is the one the saved value keeps us out of.

## 3. The Uzkul Mingol's routes

Appended last to `ROUTES`, so purse and trophy rotation (`HOUSES.index`) moves no other house.
Named from his skill line, as the other houses' routes are. Map-agnostic: named places in Ind
wait for phase 4. Every objective shape below already ships in another house's route.

| # | Slug | Name | Objectives |
|---|---|---|---|
| I | `spoils_of_ind` | Spoils of Ind | `EARN_X_AMOUNT_FROM_RAIDING` total 7500; `OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS` total 20; `CAPTURE_X_BATTLE_CAPTIVES` total 2000 |
| II | `the_company_charter` | The Company Charter | `_tower("cr_chd_skullstack", 2)` (Forge District: four seats, his own excluded, so three are his to take); `HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE` `wh3_dlc23_chd_conclave_influence` total 150 |
| III | `the_long_march` | The Long March | `DESTROY_FACTION` `wh_main_grn_greenskins` with `confederation_valid`; `DEFEAT_N_ARMIES_OF_FACTION` total 30 |

`cr_chd_skullstack` is added to the explicit faction list behind `ANNEX_GROUP`. `_GROUPS` already
reads him into group C from `zz_derpy_toz_annex.lua`.

## 4. The text

### 4.1 Rules, enforced by `check()`

- Printable ASCII only, which rules out em and en dashes, curly quotes and emoji at once. No
  ` - ` and no `--` used as a dash. No `[[` markup.
- None of the jargon the plain-words rule names, as whole words: cap, caps, accrue, accrues, rep,
  ratchet, gated, agent, agents, and `AI` and `HUD` in capitals.
- A paragraph is 40 to 70 words. An explainer is one sentence or two, at most 30 words.

### 4.2 Rules for the writer, checked in review

- In-world, in the house's voice. The paragraph states the house's aim and why this road serves
  it. It does not restate the objectives or their numbers, which draw directly beneath it and may
  change in phases 3 and 4. A gated route's paragraph must read true on both halves.
- No invented canon. Facts come only from the sources in the table below.
- The recorded author rulings stand: Gargath stays home, Bazherak is dead.

| House | Lord | Source |
|---|---|---|
| House of Baal | Gargath | Lexicanum (White Dwarf 203) |
| Fists of Hashut | Balur | Lexicanum, Gargath's entry (WD 203); the author's ruling that Balur is a melee warlord |
| Horns of Hashut | Vraznak | Lexicanum (WD 170); a Centaur lord by design |
| Slaves of the Black Dwarf | the Black Dwarf | Lexicanum (WD 201) |
| Snakebeard's Artificers | Snakebeard | Lexicanum (WD 103) |
| Warfleet of Uzkulak | Abnagg | Lexicanum (Plague Fleet rulebook) |
| Black Kraken Armada | Tordrek | Lexicanum (Dreadfleet rulebook) |
| The Conclave | Ghorth | Lexicanum |
| House of Khorakk, Bzaark, Azeros, Overlords of Zharrduk, Uzkul Mingol | Urzkhal, Bzaark, Azeros, Kharkadon, the Captain | No Lexicanum entry. Only the mod's own skill lines (`HOUSE_MISSION_OPTIONS_20260903.md` section 5, `HASHUT_LL_SKILL_LINES.xlsx`) and the house themes the generator's comments record |

The facts already harvested are listed in `HANDOFF_20261004_LORE_ROUTES_AND_BALUR.md` section 7.
Lexicanum answers direct fetches with 402/403; Wayback `id_` URLs with `--compressed` work.

### 4.3 The eight explainers

Each line says where the ritual is performed and what it gives, in CA's own names (read from
vanilla `ritual_categories` loc): Bull Centaurs, K'daai, Melee Infantry, War Machines, Sorcery
District. The annex districts' names come from `templates/toz_districts.py`.

| Category | Where | What the line must say |
|---|---|---|
| `DISTRICTS_ANNEX_T5_A` | Tower of Zharr | Take a Bloodline District seat. The house in it joins yours, or, if that house is not on this map, its lord comes to serve you |
| `DISTRICTS_ANNEX_T5_B` | Tower of Zharr | The same, Thrall District |
| `DISTRICTS_ANNEX_T5_C` | Tower of Zharr | The same, Forge District |
| `DISTRICTS_SORCERY_T3` | Tower of Zharr | The top seats of the Sorcery District |
| `HELLFORGE_CAPS_BULL_CENTAURS` | Hell-Forge | Raise how many Bull Centaurs your armies may field |
| `HELLFORGE_CAPS_KDAAI` | Hell-Forge | The same, K'daai |
| `HELLFORGE_CAPS_MELEE_INFANTRY` | Hell-Forge | The same, melee infantry |
| `HELLFORGE_CAPS_WARMACHINES` | Hell-Forge | The same, war machines |

"Joins yours, or its lord comes to serve you" is the Tower's ANNEX and GRANT modes
(`zz_derpy_toz_annex.lua`). The chat design said seven explainers; the routes use eight
categories.

### 4.4 Review before packing

`py tools/gen_victory_routes.py --review` writes
`docs/sessions/VICTORY_ROUTE_TEXT_REVIEW_20261011.md` from `ROUTES`, `LORE` and `EXPLAIN`: per
house, each route's name, its objectives in plain words, its paragraph, and the explainers it
shows. It is generated, so it cannot drift from what ships. The build stops there. Nothing is
imported until the author has read it and said yes, or marked what to change.

## 5. Checks

`check()`:

- `len(HOUSES) == 13` (was 12).
- `LORE` has exactly one entry per route and no others. `EXPLAIN` has exactly one entry per
  ritual category any route list uses, base or gated, and no others.
- The text rules of 4.1, over every `LORE` and `EXPLAIN` entry and every route display name.
- Over every emitted mission string: the first objective is the route's paragraph line; every
  `PERFORM_RITUAL` sits directly under its category's explainer line; no other `SCRIPTED`
  objective appears; every `override_text` key has a loc row.
- The existing refusal of a hand-written `SCRIPTED` objective in `ROUTES` stays. Only the emitter
  adds them.

`--selftest`, against the shipped Lua under Lua 5.1.5:

- The loc row count gains one per route and one per explainer; the stray-key list gains the two
  new prefixes.
- Replaying `FactionTurnStart`: a human house records five completions,
  `derpy_route_victory_1..5`, each with `derpy_route_lore`, whatever its route count. An AI
  house, a human CA faction, and any faction in multiplayer record none. A loaded game carrying
  `derpy_route_lore_v1` records the same as a new one; a loaded game without it (a save from
  before phase 2) records none.
- New mutants, each of which must fail the selftest: the `is_human` condition dropped, the
  saved-value return dropped, the issue block not setting the value, the loop stopping one
  short, the wrong script key, and the listener registered below the `is_new_game()` return.
- New deliberate `check()` breaks, each of which must be caught: a route with no paragraph, a
  stray paragraph, a used category with no explainer, an em dash in a paragraph, "cap" in an
  explainer, a 20-word paragraph.

Also `luac -p`, `check_lua_api.py`, `check_lua_undeclared.py` and `check_lua_literal_left.py` on
the shipped Lua, and `import_victory_routes.py`'s `EXPECTED_ROWS` loc term gains
`len(LORE) + len(EXPLAIN)`.

## 6. Ship, and what to look at in game

After the author approves the review file: import with `tools/import_victory_routes.py` (RPFM
open), `--verify-only` on the saved pack, back up the previous build to `Modding Files/Backup/`,
copy into the Workshop folder (Workshop-hosted, so never `data/`). Wait while the game is
running. Upload only on the author's word.

In game, on top of phase 1's three items:

1. A new campaign as any house: each route's first line is its paragraph, and each ritual
   objective has its explainer line above it.
2. From turn 2, those lines show ticked, and the log has the completer's line.
3. A save from before phase 2 loads and plays a turn with nothing new in the script error log.
4. IEE as the Uzkul Mingol: three routes in the Victory panel.

## 7. Not in this phase

The styled header (VCO's `<dummy>` UI listener; the author chose plain first), colour tags,
named places in Ind (phase 4), bespoke rewards (phase 3), story beats (phase 5). VCO's
panel click fix stays out until phase 1's in-game check says the Victory tab opens on the wrong
node.

## 8. Docs

- `tools/gen_victory_routes.py` docstring: the third deviation, "No SCRIPTED flavour objectives",
  is reversed. It is rewritten to say what is copied, the completer's shape, and why the
  `<dummy>` marker is still skipped.
- `docs/VICTORY_CONDITIONS.md`: a new section 12d for the lines and the completer.
- `docs/SESSION_INDEX.md`: one line. `docs/MY_MODS.md`: one clause in the lords pack row.
