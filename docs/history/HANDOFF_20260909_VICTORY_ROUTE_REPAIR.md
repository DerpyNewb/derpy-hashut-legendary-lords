# Handoff 2026-09-09 — the victory routes, run for the first time: two nodes of five, and why

The 2026-09-08 routes were finally seen in a campaign. They were issued cleanly and **drew two
nodes out of five**. This session found the cause, fixed it at the root for all eleven houses,
confirmed the repair in game, then added a reward to every route — and the reward turned out to
be the wrong item, which is the third correction below.

**State at the end:** deployed **15,873,168** bytes, sha256 `875cbe762e47d927`, in both
`Modding Files/Modpacks/` and
`F:\SteamLibrary\steamapps\workshop\content\1142710\3432966208\` - hashed identical on both
sides, the Workshop copy re-verified in a fresh MCP session (50/5/35 rows round-tripped, the
script present, the four superseded `derpy_chd_victory_objectives.lua` gone) and its in-pack Lua
byte-read for all 35 routes: the `faction` line, three pooled-resource transactions with the
right factor and amounts, a trophy, and zero occurrences of `money`. Not uploaded to the
Workshop.

**Worth keeping from the way this went out:** two saves failed with `Access is denied. (os error
5)` because **WH3 was running** - RPFM cannot write a pack the game holds. Neither wrote
anything, each file hashing identical to its pre-attempt backup afterwards, and that hash
comparison is the check to run before assuming a failed RPFM save was harmless. The route taken
both times: import into `Modpacks/`, verify there, then `cp` across once the game closed.

Backups, oldest first: `.bak_prefactionline_20260909` (15,852,913),
`.bak_prerewards_20260909` (15,853,539 sha `5ccdc66ffabeb5c0`),
`.bak_prevanillatrophies_20260909` (15,856,999 sha `386be5ffe9de5b6c`) and
`.bak_pretreasuryswap_20260909` (15,857,873 sha `5290637aca73df77`, in both folders).

---

## 1. The status question that started it

Asked what state Ghorth's missions and victory conditions were in. The answer out of the docs
was "built, deployed, never run" — and that was **stale by nine hours**. Two script logs in the
game folder post-dated the handoff that said it:

```
script_log_080926_2354.txt   (cr_combi_expanded, local faction wh3_dlc23_chd_conclave)
  <72.9s>  derpy_chd_victory_routes: CA victory missions skipped for wh3_dlc23_chd_conclave
  <82.5s>  ++ triggering mission from string for faction wh3_dlc23_chd_conclave ... (x5)
  <82.5s>  derpy_chd_victory_routes: issued 5 victory routes for wh3_dlc23_chd_conclave
script_log_090926_0917.txt   (the run behind the screenshot, same lines at <91.9s>)
```

**The lesson is the diagnostic, not the dates.** Grepping the last 25 script logs for one of our
own `out()` strings took one command and answered three of the handoff's open questions
(does the wrapper suppress CA's, does the string route parse, are the routes issued) without
launching anything. Do that before writing "nothing has been run".

## 2. Correction 1: a `CONSTRUCT_*` objective with no `faction` line kills its whole route

Ghorth drew nodes for routes **II and III** only. The three dead ones were exactly the three
holding a `CONSTRUCT` objective, and that was the whole of it.

* Our own reference doc already carried the answer, as a footnote: CA's
  `victory_objectives.lua` special-cases the three `CONSTRUCT_N_*` types in `add_objectives` and
  appends `"faction " .. faction_key`, commenting *"these objectives will fail if we don't add
  them here"*. `gen_victory_routes.py` never did it.
* Corroborated by counting two installed mods: **VCO writes the line on 157/157** of its
  CONSTRUCT objectives (`CONSTRUCT_BUILDING_IN_PROVINCES` included) and
  `pow_victory_conditions` on **19/19**. Neither ever omits it.
* **The failure is silent and total.** Not "the objective never completes" — the whole mission
  is dropped, so the route has no node in the victory panel. `trigger_mission_from_string`
  still echoes the block, our own line still says "issued 5", and no log line anywhere
  complains. A mission that was issued proves nothing about whether its objectives were taken.
* **19 of the 35 routes across all eleven houses** carried the defect. This was never
  Ghorth-only; every house had one or two dead routes.

Fixed in `mission_string()`, which now prepends the cond so the existing loop writes it at the
right indent — the `ROUTES` tables stay declarative and no route entry had to change.
`--selftest` asserts every emitted CONSTRUCT objective carries the line, and the assertion was
mutation-proven (strip the lines from `mission_string` at runtime → `cr_chd_house_of_khorakk
route 1: CONSTRUCT_N_OF_A_BUILDING carries no faction line`).

**Confirmed in game the same day: all five nodes draw**, route V rendering all three objectives
with its counter ("Current total: 0 / 5000"). Which settles four more open questions at once —
the panel does **not** clip at four the way the Tower of Zharr district list does;
`CAPTURE_X_BATTLE_CAPTIVES`, `vassalization_valid` and both CONSTRUCT variants are accepted; and
route I drawing means `ACHIEVE_CHARACTER_RANK` with `include_generals` is accepted too, because a
rejected objective takes its whole mission with it. VCO and PoW both write that type with
`start_pos_character` instead and neither uses `include_generals` at all, so this is the one
place the workspace is ahead of both of them.

## 3. Then: the rewards, which the panel does preview

**The victory panel draws a `Reward` box** under the objectives - measured, screenshot: green
"Treasury: +50000" and the item with its icon and display name. That answers an open question
from 2026-09-08 (whether a reward shows at all) and it is what made correction 3 below visible
before anything shipped further.


Routes paid nothing — `payload { game_victory; }` and no more, `game_victory` being there only
because a mission with no payload at all fails to generate. Added per route:

```
payload
{
	game_victory;
	money 50000;
	add_ancillary_to_faction_pool
	{
		ancillary_key <one item>;
	}
}
```

* `money` is attested in PoW (as `money -70000`, a **cost**, so the sign is the obvious
  inverse); `check()` refuses a non-positive `REWARD_MONEY`.
* `add_ancillary_to_faction_pool` is what **CA itself** gives the Chaos Dwarf long victory
  (`payload_ancillary = { lesser relics of skavor / morgrim / smednir }`), so the shape is CA's
  and not just PoW's.
* Flat 50,000 for all 35: the routes are alternatives, not stages, so nothing about the index
  says harder.
* **One deliberately unattested detail:** `game_victory` is kept *beside* the reward, where CA
  adds it only when there is neither a bundle nor an ancillary. Kept because the string route
  has no counterpart to `mm:set_victory_type` beyond its `victory_type` line, and because the
  cost of being wrong is one look at the panel. **If a route ever disappears after a reward
  edit, drop `game_victory` first.**

## 4. Correction 2: the trophy must come out of the same pack

First instinct was the 430 house ancillaries. They live in
`derpy_chd_house_ancillaries.pack`, which is **not** a dependency of the lords pack — and by
§2 an unresolvable key in a payload can drop the whole mission, which is the failure that had
just cost three of Ghorth's five routes. So the reward draws only from
`ancillaries_tables/derpy_chd_ll_ancillary`, the lords pack's own 37 keys, held in the
generator as `LL_ANCILLARY_KEYS` for `check()` to compare against, with a deliberate break.

## 5. Correction 3: those 37 items are granted on level-up anyway

Reported from the campaign: the per-lord items are **handed to the lord automatically as he
levels**, via the pack's own `ancillaries_required_skills` rows. So a trophy drawn from that set
rewards a route with something the player already gets for free — correct data, worthless
reward. Being replaced with vanilla Chaos Dwarf ancillaries, which have the same zero-dependency
property (they ship with the game) and CA's own precedent above.

**Done.** `HOUSE_ITEMS` and `LL_ANCILLARY_KEYS` are gone, replaced by `TROPHIES` - eight vanilla
items, offset by house index as well as route index so no house repeats one:

| Trophy | Source |
|---|---|
| The Obsidian Axe, Armour of Gazrakh, Dagger of Malice, Chaos Runeshield, Banner of Slavery | `anc_set_exclusive_chaos_dwarfs`, `randomly_dropped = False` |
| Lesser Relic of Smednir / Skavor / Morgrim | `faction_set = all`, and what CA itself pays the Chaos Dwarf long victory |

Two filters, both now `check()` rules with a deliberate break each: a trophy may not be in
`SKILL_GRANTED_ANCILLARIES` (the 38 keys `ancillaries_required_skills` binds to a skill), and it
must be a `wh3_`-prefixed vanilla key so no other pack becomes a dependency. Also excluded but
not codified: CA six `wh3_dlc23_anc_banner_chd_*` banners are `randomly_dropped = True` and
arrive free, which is the same mistake one step out.

**`anc_set_exclusive_chaos_dwarfs` is culture-keyed**, one `faction_set_items` row on
`wh3_dlc23_chd_chaos_dwarfs` with no faction list - so the ten invented `cr_chd_*` houses are
inside it and the five CHD-exclusive trophies are legal for all eleven. This is the check
[[wh3-vanilla-ancillary-pool-filters]] asks for: read the set rows, not the set name.

## 5b. Correction 4: the currency was wrong too

`money 50000` was the reward on the first two builds. Replaced on sight with what a Chaos Dwarf
faction actually runs on - **5,000 raw materials, 2,500 armaments, 250 Conclave influence**, one
`faction_pooled_resource_transaction` block each, gold dropped entirely. Three findings made it
safe rather than a guess:

* **`factor missions` exists on all four Chaos Dwarf pools and is grant-capable on each** -
  `min 0 / max 2147483647` on raw materials, influence and labour, unbounded both ways on
  armaments. It is CA own attribution bucket for a mission payout, so no factor had to be
  invented, and it sidesteps the one-way bound that makes `wh3_dlc23_chd_mined` /
  `..._consumed` the wrong choice.
* **Labour cannot be paid.** `pooled_resources.scope` is FACTION_PROVINCE for
  `wh3_dlc23_chd_labour`, which is script-unreachable at both levels. Route V still *asks* for
  3,000 labour as an objective, which the engine evaluates itself; `check()` refuses to pay it.
* Amounts are pinned to the start this workspace sets (2,500 / 1,000 / 0) and to what the routes
  demand (60-400 influence), so a reward is about a doubling of a starting stock.

`check()` gained three rules and `--selftest` two more breaks (paying labour, a negative
amount), now **12**. Verified in the saved pack: 35/35 routes carry three transactions with the
right factor and amounts, `money` occurs zero times, every pool is FACTION-scoped and the factor
maximum covers the amount - all read back out of vanilla rather than out of the constant being
checked.

## 5c. Abnagg and the Black Dwarf: five routes each, because IEE places only those two

The last change of the day, and the one with an outside fact behind it: **Immortal Empires
Expanded places exactly two of the ten `cr_chd` houses** - `cr_chd_slaves_of_the_black_dwarf`
and `cr_chd_warfleet_of_uzkulak`. `ime_derpy_black_dwarf.lua` states it in its header and
`zz_derpy_toz_annex.lua` logs it in game as *"seated 2, skipped 8"*. With the vanilla Conclave
that is the whole Chaos Dwarf roster an IEE player can pick, so those two now carry five routes
like Ghorth instead of the roster's generic three, drawn from their own skill lines
(`HOUSE_MISSION_OPTIONS_20260903.md` section 5).

| | Black Dwarf - the fortress | Abnagg - the fleet |
|---|---|---|
| I | The Unbreached Wall - one `settlement_tower_5`, four `_3` | Tyrant of the Waves - raid 7,500, sack 25 |
| II | Chains of the Conclave - both district-B seats, 150 influence | The Hellbeard Comes Ashore - the same two seats, 150 influence |
| III | The Slave Harvest - destroy the Greenskins, 4,000 captives | Siege Mastermind - destroy the Dwarfs, 30 battles |
| IV | The Granite Legion - two `chd_infantry_3`, 60 units, 500 armaments | Infernal Artillery - one `war_machines_3`, 2 Hell-Forge caps, 400 armaments |
| V | Wrought of Living Stone - rank 30, 40 battles, 3,000 labour | Fleetmaster's Command - 3,000 captives, 2,000 labour, 50 units |

Four things decided the content, and each is a measurement rather than a preference:

1. **Both are group B, and both routes II ask for the whole rest of that district (2 seats).**
   A house may claim any seat but its own, so 2 is the ceiling. The third group-B house
   (Tordrek) is absent from IEE and that does **not** block the route: `zz_derpy_toz_annex.lua`
   picks per seat at runtime - ANNEX confederates a faction the campaign placed, **GRANT spawns
   the missing lord into the claimant's recruitment pool**. In IEE the other claimable seat is
   the other of these two lords.
2. **Abnagg starts with no settlement.** `ime_derpy_abnagg.lua` spawns him on
   `wh3_main_combi_region_barak_varr` (185, 366) and converts his force to
   `DERPY_CHD_NAVAL_HORDE`, so four of his five routes ask for nothing a fleet cannot do from
   the water, and his DESTROY target is the Dwarfs because he starts in their harbour.
3. **`primary_slot_building_building_level_requirement` is what a `CONSTRUCT_*` total really
   costs.** `military_war_machines_3` and `military_kdaai_3` want a **level-5** settlement under
   them, `military_chaos_dwarf_infantry_3` a level-4, and `settlement_tower_N` wants level N.
   So "two war machine halls" is "two cities grown to maximum". Abnagg's artillery route was cut
   to one on that reading and the Black Dwarf's barracks route from three to two.
4. **No horde-building objective, and at this point no region key either.** No vanilla
   mission counts a horde building (`HOUSE_MISSION_OPTIONS` H1/K1, rated Untested), which is
   not something to discover inside a victory condition - Abnagg's flagship is what he does it
   all with, never the thing counted. The region half of that rule was because both houses
   exist in `cr_oldworld` too, where an IEE-only key would kill the route in silence;
   **§5d then bought the region objective properly, with a runtime gate**, rather than
   dropping the rule.

`EARN_X_AMOUNT_FROM_RAIDING` enters the file here, at VCO's own figure of 7,500 - its single
use, on Wintertooth. It, `ASSASSINATE_X_CHARACTERS` and `MAINTAIN_N_ALLIANCES` are now in
`TYPES_NEEDING_TOTAL` (each `total` and nothing else in VCO, 1/1 and 3/3 and 3/3).

## 5d. Abnagg's elf grudge, and the first map-gated route in the file

Asked for two things: Abnagg's hatred of elves, and the capture of a rich trade settlement in
IEE the player named "Dawnstar".

**There is no "Dawnstar".** Byte-scanned all 674 installed packs (game data and every Workshop
mod) for the string in UTF-8 and UTF-16LE: zero hits. Vanilla loc has three Dawn settlements -
Dawn's Light, Fortress of Dawn, Ziggurat of Dawn - and IEE adds none.

**The Fortress of Dawn is what the description fits, and the DB says so outright.** CA built a
**Chaos Dwarf variant of its landmark harbour**:
`wh3_dlc23_special_fortress_of_dawn_dawns_harbour_chd`, `chain_category` `money` on the
`wh_main_sch_port` superchain, and at level 3 it pays

| effect | value |
|---|---|
| `wh_main_effect_economy_gdp_trade_sea` | +500 |
| `wh3_dlc23_effect_force_chd_campaign_post_battle_labour` | +5, factionwide |
| `wh2_dlc11_effect_force_army_campaign_attrition_storm_reef_immunity` | 1, factionwide |

A trade port, a slave engine and safe water for a fleet, in one region, held by High Elves.
There is no other settlement on the map that is more Abnagg's. High Elves rather than Dark
Elves for the grudge on purpose: Naggarond is the Chaos Dwarfs' slave *customer*, so the
loreful enemy is the elves who hunt slavers, not the ones who buy from them.

So **Abnagg's route III became map-gated** rather than a sixth route (five slot rows exist and
five nodes are measured to draw; six is unverified, and the panel's ceiling took a live run to
answer once already). One route, two mission blocks:

* on IE and IEE: `OWN_N_REGIONS_INCLUDING region wh3_main_combi_region_fortress_of_dawn total 1`
  + `DESTROY_FACTION wh2_main_hef_fortress_of_dawn` + 25 battles
* anywhere else: the Dwarf war it already was - `DESTROY_FACTION wh_main_dwf_dwarfs` + 30
  battles

The mechanism, and the four things it cost, are in `VICTORY_CONDITIONS.md` §12b. The two worth
repeating here:

1. **`region_by_key` is on `REGION_MANAGER_SCRIPT_INTERFACE`, not on `cm`.** The first draft
   wrote `cm:region_by_key`, which throws *attempt to call method (a nil value)* - inside a
   first-tick callback, so it would have taken every callback queued after it. `luac -p` passed
   it. `tools/check_lua_api.py` caught it against CA's own `scripting_doc.html`, which is what
   that tool is for. The probe is now the same walk the drill chain and the exchange use, in a
   `pcall`, and an unreachable manager reads as off-map - the safe way to be wrong.
2. **IEE reuses Immortal Empires' region keys.** Its `!cr_vanilla` `campaign_map_regions`
   fragment maps `wh3_main_combi_region_*` onto `cr_combi_expanded_map_1`; `cr_oldworld_map_1`
   carries none of them. One key covers IE and IEE, and the gate exists for the Old World maps.

`--selftest` now runs the shipped Lua **twice**, with the region on the stub map and without,
and asserts the region objective is issued exactly once and never where the region is absent.
Mutating `return entry.off_map` to `on_map` fails it - checked, not assumed.

## 5e. And a quest for the same settlement - the file's first ordinary mission

Asked for after the victory route: a **mission** to take the Fortress of Dawn, not only a
victory condition. `derpy_mis_abnagg_dawns_harbour`, issued to
`cr_chd_warfleet_of_uzkulak`, one objective and a payload that is the point rather than a
consolation prize:

```
key derpy_mis_abnagg_dawns_harbour;      OWN_N_REGIONS_INCLUDING
issuer CLAN_ELDERS;                        region wh3_main_combi_region_fortress_of_dawn
                                           total 1
payload: money 15000; raw materials 2500
```

Built by `gen_victory_routes.py` rather than a new pipeline, because a quest is the same four
artefacts as a victory route **minus the `victory_type` row**: a `missions` row, three loc keys,
a mission string, and a line in the issue loop. The generator already owned all four and the
importer already pushed the two fragments; the new code is `QUESTS`, `quest_string()` and a
shared `payload_lines()` that both halves now use.

What decided the shape, all measured rather than assumed:

* **The string route, because HLL cannot use the DB route.** A mod-authored `missions` row pays
  nothing without `cdir_events_mission_option_junctions`, `_payloads` and
  `_issuer_junctions`, and HLL ships **none** of the three - which is why its eleven existing
  mission rows do nothing at all (`HOUSE_MISSION_OPTIONS_20260903.md` §2.1). A mission string
  carries objectives and payload itself, and `MISSIONS.md` §11 measured it paying to the
  treasury exactly.
* **A quest differs from a victory condition by two lines**: no `victory_type` in the block, no
  `game_victory` in the payload. `--selftest` asserts both are absent - carrying either would
  end the campaign the first time the player took one settlement.
* **The DB row copies CA's own Chaos Dwarf quests**: `event_category Quest`,
  `quest_mission true`, `sticky_by_default true`, `can_be_manually_cancelled false`,
  `chd/generic` + `rom_event_mission.png`, location `0,0`. Those are the majority values over
  CA's 704 `Quest` rows (696/704 sticky, 679/704 non-cancellable) and over every
  `wh3_dlc23_chd_*` quest row. `mission_type` stays `SCRIPTED`, the column value measured to
  work with the string route.
* **The quest is gated in Lua, not only in its objective.** The gate now factors out as
  `derpy_on_map(region)`, shared with `derpy_pick`: a route with no region on this map falls
  back to its other half, a quest with no region on this map is **not issued at all** - there
  is nothing to capture. `--selftest` runs the shipped Lua both ways for quests too, and the
  pack verifier checks the Lua gate exists as well as the objective.

`check()` gained a quest section: key prefix (`derpy_mis_`), no collision with a victory slot
key, no tab in any text (it would break the TSV), an attested objective type, no `SCRIPTED`, a
`total` where the type needs one, a verified region, a verified faction target, a payable pool,
a positive amount, and **a map-bound objective with no region gate is refused** - that last one
is the trap that would ship a dead mission to three maps. 18 deliberate breaks now, two of them
new.

## 6. What changed in the workspace

| Path | What |
|---|---|
| `tools/gen_victory_routes.py` | `TYPES_NEEDING_FACTION` + the emitter line; `REWARD_MONEY`, `LL_ANCILLARY_KEYS`, `HOUSE_ITEMS`, `route_reward_item()`; the payload block; three new `check()` rules; two new selftest assertions and a 9th deliberate break. Then `PURSES` + `route_rewards()` replacing `REWARD_POOLS` (5b), five more `check()` rules and 14 breaks; then five routes each for `cr_chd_slaves_of_the_black_dwarf` and `cr_chd_warfleet_of_uzkulak` (5c) and three more types in `TYPES_NEEDING_TOTAL` |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_chd_victory_routes.lua` | 38,671 bytes (was 19,921): 39 routes in 40 blocks (one route ships two) plus 1 quest |
| `tools/import_victory_routes.py` | `EXPECTED_ROWS` derives the missions and loc counts from `G.all_quests()` too |
| `docs/VICTORY_CONDITIONS.md` | §6 table rows now list `faction` on the three CONSTRUCT types; the footnote under it became a measured rule; §7 gained "What the routes in this workspace pay" (rewritten for the purses); §10 gained two trap bullets and the corrected `region_by_key` receiver; §12 now carries which houses IEE places and the two IEE notes; **§12b is the map-gated route** |
| `CLAUDE.md` | the `gen_victory_routes.py` line names the three five-route houses, the map gate and the quests |
| `docs/MISSIONS.md` | **§11b, the first shipped quest** - the five decisions and the known ceiling |
| `docs/sessions/HANDOFF_20260908_GHORTH_VICTORY_ROUTES.md` | §6 amended — it has been run, what it found, what it settled |
| `docs/SESSION_INDEX.md` | the 2026-09-08 line amended twice |
| memory | `wh3-construct-objective-needs-faction-line` |

## 7. Do not re-derive

* **There is no settlement called "Dawnstar" in any installed pack** - 674 scanned, both
  encodings. The rich elf trade port in IE/IEE is the **Fortress of Dawn**, and CA gave its
  landmark harbour a `_chd` variant paying +500 sea-trade GDP and +5 post-battle labour.
* **`region_by_key` is on the region manager, not on `cm`** - and IEE reuses IE's
  `wh3_main_combi_region_*` keys, so one key serves both. §5d.
* **IEE places only `cr_chd_slaves_of_the_black_dwarf` and `cr_chd_warfleet_of_uzkulak`** of
  the ten modded houses - with the vanilla Conclave, three Chaos Dwarf lords in that campaign.
  The tower seating script logs it: "seated 2, skipped 8".
* **A `CONSTRUCT_*` total is priced by `primary_slot_building_building_level_requirement`.**
  Level 5 for `military_war_machines_3` / `military_kdaai_3`, 4 for
  `military_chaos_dwarf_infantry_3`, N for `settlement_tower_N`. Read it before picking a count.
* **Every `CONSTRUCT_*` objective in the mission-string syntax needs `faction <own key>;`.**
  §2. Nothing logs its absence. VCO 157/157, PoW 19/19, CA's own comment says so.
* **"The mission was issued" is not evidence its objectives were accepted.** The engine echoes
  the block either way. Only a node in the victory panel proves it.
* **The victory panel draws at least five route nodes.** Measured with Ghorth's five, all
  selectable. Vanilla's own `wh3_combi_*` set runs `tree_y` 0..4.
* **`ACHIEVE_CHARACTER_RANK` + `total`/`total2`/`include_generals` parses**, despite neither
  reference mod writing it that way.
* **`wh3_dlc23_chd_factory_refinery_3` is ungated** — no `resource_requirement`, not
  `only_in_capital`, not `faction_unique`, needs a tier-3 primary slot. Route V asks for three
  and that is settlement growth, not a map lottery.
* **Payload vocabulary that is attested**: `game_victory`, `money`, `effect_bundle {bundle_key;
  turns;}`, `add_ancillary_to_faction_pool {ancillary_key;}`,
  `faction_pooled_resource_transaction {resource; factor; amount; context;}`, and nested
  `objective` blocks (VCO's SCRIPTED headers). Counts and examples are in §7 of
  `VICTORY_CONDITIONS.md`. VCO's 403 payloads are all one **dummy** effect bundle, so "VCO
  rewards its victories" is not really true.
* **The Bash tool mangles `\\` inside a heredoc here, and chokes on some apostrophes.** Three
  patch scripts failed on it before the pattern was clear: a heredoc pattern containing `\\t`
  arrives as a real tab and matches nothing. Write patch scripts with the Write tool instead,
  or build the escape as `chr(92) + "t"`. This is a tooling trap, not a Python one.
* **The 1,000+ Lua warnings in the editor are the workspace, not the mod.** Measured with the
  same language server VS Code runs (sumneko 3.19.1) from its own CLI - `lua-language-server
  --check <dir> --checklevel=Information --configpath=<a .luarc.json built from
  .vscode/settings.json>` - which is the way to get a breakdown by code instead of a badge
  count. 3,638 problems, of which `redundant-parameter` 1,646 and `duplicate-set-field` 1,329,
  and **3,355 of those came from two sources that are not shipped Lua**: the `tools/` selftest
  harnesses, which exist to *lie* about the API (ten declare `function out() end`, so every real
  `out("XXX ...")` is checked against a 0-argument function), and `_bak_*` copies, where one
  474KB backup of the exchange script was 1,220 findings on its own. Both are now in
  `Lua.workspace.ignoreDir`, and the 18 real globals the settings lacked are in
  `Lua.diagnostics.globals`: **1K+ -> 106, and 0 errors**. The single Error was
  `tools/_layout_harness.lua`, which is a Python format-string template and therefore not valid
  Lua on disk - `luac -p` fails on it too, by design. What remains is worth reading: 34
  `need-check-nil`, 32 `lowercase-global`, and 26 `duplicate-set-field` that are structural (the
  ToZ override ships one copy per campaign folder and always will).
* **RPFM's autosave re-saves an open pack minutes after the importer exits**, so a hash taken
  straight after saving is not a stable identity — hash the Workshop copy and re-sync
  `Modpacks/` from it. Confirmed again this session.

## 8. What is open

1. **Whether completing a route ends the campaign.** Still the one thing no run has shown, and
   the reason `game_victory` is being kept beside the reward.
2. **The other ten houses have never been played.** Their routes carried the same §2 defect and
   the same fix; only Ghorth's have been seen on screen.
3. **`wh2_main_hef_fortress_of_dawn` has not been live-probed.** It has a vanilla `factions`
   row, 4 byte occurrences in IEE's `startpos.esf` beside its own flag path and a
   `start_pos_factions_description` key, and 11 in `!cr_oldworld_campaign.pack`; CA names its
   region in `victory_objectives.lua`. That is DB and startpos evidence, not the live probe the
   other two DESTROY targets got. If it is absent from a map, that one route is unachievable
   there - the other four are untouched. Probe it with
   `cm:get_faction("wh2_main_hef_fortress_of_dawn")` on the next run.
4. **The map gate has never run in a real campaign.** It is proved under Lua 5.1 against a stub
   region manager, twice, but `region_by_key` answering during a **first tick** is not measured.
   The failure mode is benign by construction: the pcall makes an unreachable manager read as
   off-map, so Abnagg gets the Dwarf war instead of the elf grudge.
5. **No purse with treasury in it has been seen drawn.** The three-pooled-resource purse and a
   trophy were; `money` was drawn back when gold was the whole reward, so both halves are
   attested separately and only the mix is not.

Two items closed the same day:

* **The trophies and the pooled rewards draw.** Ghorth route III on 2026-09-09: "Banner of
  Slavery" with its icon, then "Raw Materials: +5000", "Armaments: +2500" and "Conclave
  Influence: +250", each in green with its own resource icon. So a
  `faction_pooled_resource_transaction` payload is previewed exactly the way `money` was - the
  old open item 4.
* **The flat reward became seven purses.** All 35 routes paying the same three resources read as
  a template, so `REWARD_POOLS` became `PURSES`, picked by `(house index + route index) % 7`
  against the trophy's `% 8`, so purse and item do not travel together and no house repeats
  either. Three purses are a single currency, three are mixed, one is the full three-way, and
  **treasury is back** in two (30,000 alone, or 15,000 beside 3,000 materials) - 10 of the 35
  routes pay gold. `money <n>;` is a bare payload statement and needs no transaction block; it
  sits beside the pooled transactions in one payload. Amounts differ per purse on purpose: a
  one-currency purse pays about double what a mixed one pays of the same resource, so a narrow
  reward is not a smaller one. `check()` now walks every purse - unknown pool, labour,
  non-positive amount, one pool named twice, an empty purse - and the selftest asserts the
  purses actually differ: flattening `PURSES` back to a single entry fails it with "pays the
  same purse for two routes", mutation-proved. Deployed and byte-verified out of the Workshop
  pack: 35/35 blocks, 10 paying treasury, 0 findings.
