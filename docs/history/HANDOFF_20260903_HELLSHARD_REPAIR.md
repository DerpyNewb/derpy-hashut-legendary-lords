# Handoff 2026-09-03 (third session) — step 2 built: the eleven hellshard missions repaired

Executes step 2 of `HOUSE_MISSION_OPTIONS_20260903.md` §9. Everything below is in the shipped
pack; nothing here is a proposal. **§9 is the in-game pass — read it first.** The DB half is
confirmed working; the Lua half cannot be reached in the campaign that is actually installed.

---

## 1. What changed

| File | What |
|---|---|
| `tools/gen_hellshard_missions.py` | **New.** Writes the four TSVs, patches both Lua copies, imports into the pack. `--check` writes files only, `--selftest` needs no RPFM |
| `Modding Files/source/hellshard_missions/` | **New.** `missions_tables__base.tsv` (the 33 rows as shipped, the generator's input) plus the four generated TSVs |
| `Modding Files/pack/script/campaign/{cr_oldworld,cr_darklands}/mod/!!!narrative_chaos_dwarfs_new_factrions.lua` | Trigger block replaced |
| `Modding Files/Modpacks/!aa_derpy_hashut_legendary_lords.pack` | 3 new DB tables, `missions_tables` rewritten, both Lua files re-added. 15,520,385 -> 15,522,079 bytes |
| Workshop `3432966208/!aa_derpy_hashut_legendary_lords.pack` | Same file, hash-identical. `.bak_premissions_20260903` beside it; a second backup in `Modpacks/backups/` |

Not uploaded to Steam. The Workshop *folder* copy is what the game loads, so it is testable now.

---

## 2. The defect that mattered most, and was not in the options document

**The whole trigger block was inside `if cm:is_new_game() and cm:model():is_multiplayer()`.**

CA's `wh3_dlc23_narrative_chaos_dwarfs:initialise()` has the mirror gate —
`if cm:is_new_game() and not is_multiplayer_campaign` — and its branch names only
`wh3_dlc23_chd_astragoth`, `wh3_dlc23_chd_legion_of_azgorh` and `wh3_dlc23_chd_zhatan`. So the
two halves cover: vanilla factions in singleplayer (CA), everyone in multiplayer (the mod), and
**the mod's own ten houses plus Ghorth's conclave in singleplayer: nobody.**

That is the reason none of these missions had ever been seen. The options document's §2.2 found
three mispaired keys by reading the `elseif` chain and did not read the `if` above it — the eight
correctly-paired triggers were just as dead as the three wrong ones.

Confirmed by grep: `hellshard` appears in exactly two files across all 70 Lua files in the pack,
both copies of `!!!narrative_chaos_dwarfs_new_factrions.lua`, and nowhere else. There is no
second trigger site. `cr_combi_expanded` had no copy of the file at all, so the three houses IEE
carries got nothing there either — **which turned out to matter more than this section, because
IEE is the only one of the three campaigns actually installed. See §9.1 and §10.**

**Fix:** the `if`/`elseif` chain is replaced by a `hellshard_starts` table keyed on faction, and
one loop. The three vanilla entries carry `vanilla = true` and are fired only when
`is_multiplayer_campaign` is true, so CA keeps singleplayer and nothing double-triggers.

The dropped `chaos_dwarfs_narrative.updates.player_faction_key = human_factions[i]` assignment
was checked before removing it: CA's own `initialise()` sets the same field in the same loop over
the same faction list, in both branches, and it is read only by `spawn_relic_armies`.

---

## 3. The other four defects

**3.1 Three mispaired triggers and a missing faction** — as the options document §2.2 found,
now fixed in the table:

| Faction | Was | Now |
|---|---|---|
| `cr_chd_slaves_of_the_black_dwarf` | `..._cr_chd_slaves_of_the_black_dwarf` (no such row) | `..._derpy_black_dwf` |
| `cr_chd_house_of_bzaark` | `..._derpy_black_dwf` | `..._derpy_bzaark` |
| `cr_chd_warfleet_of_uzkulak` | `..._derpy_tordrek` | `..._derpy_abnagg` (row minted) |
| `cr_chd_black_kraken_armada` | never triggered | `..._derpy_tordrek` |

Abnagg had no row of his own; the generator clones Tordrek's and changes exactly one column, the
key — asserted in `--selftest`. `chaos_dwarfs_narrative.drill_location_black_kraken` was already
declared in the file and never used; it is used now.

**3.2 The three missing tables.** HLL shipped `missions_tables` alone, so every row had no
objective parameter and no reward. Added at the versions measured in
`HANDOFF_20260903_MISSIONS_FIRST_BUILD.md` §3 — `cdir_events_mission_option_junctions` **2**,
`cdir_events_mission_payloads` **2**, `cdir_events_mission_issuer_junctions` **1** — and
verified as those versions by re-exporting from the saved pack.

Each of the twelve mod-owned hellshard rows now carries CA's own four-option shape:

```
VAR_CHANCE                    100
VAR_MISSION_LENGTH_INFINITE   (empty)
GEN_TARGET_NONE               (empty)
VAR_OBJECTIVE_BUILDING_LEVEL  wh3_dlc23_chd_factory_drills_2
```

plus one payload, `EFFECT_BUNDLE / SUCCESS / KEY[wh3_dlc23_chd_drill_structure_reward];DURATION[5];GLOBAL`,
and one `CLAN_ELDERS` issuer. All four option keys, the payload key and the issuer are attested in
vanilla's own rows (815 `EFFECT_BUNDLE` payloads, 2,424 `CLAN_ELDERS` issuers, and the payload
*value* string is byte-identical to the three CA uses for this same mission).

**Why `wh3_dlc23_chd_factory_drills_2`.** CA points each vanilla row at that faction's own
landmark, `wh3_dlc23_special_<lord>_great_drill_of_hashut_2`, which no house owns.
`wh3_dlc23_chd_factory_drills` is the only CHD drill chain any faction can raise — settlement type
`wh3_dlc23_chd_factory`, two levels, `faction_unique` false, `only_in_capital` false, and no row
in `building_chain_availabilities`. Level 2 is its top, so the objective cannot auto-satisfy on
turn 1 the way a settlement-tier objective would for Ghorth, who starts at tier 5. It costs
nothing to ship: the building, the effect bundle and the issuer are all vanilla.

**Note for Abnagg and Tordrek:** both start as converted `DERPY_CHD_NAVAL_HORDE` forces with no
region, so this objective needs them to take a settlement and convert it to a factory first. It
does **not** depend on the open H1/K1 question (can a `CONSTRUCT_*` objective see a *horde*
building) — that question is untouched and still gates the naval quests in §5 of the options
document.

**3.3 `chd/generic` does not ship.** Verified directly: `ui2.pack` carries 24 CHD eventpics and
`generic.png` is not among them, while every other race has one (`brt/`, `bst/`, `chs/`, `cst/`,
`def/`, `dwf/`, `emp/`, `grn/`, `hef/`, `lzd/` ...). CA's own three hellshard rows have the same
dead reference. All 34 rows are re-pointed: `chd/hell_forge` for the twelve hellshard rows,
`chd/land_victory` for the eleven relic-unlock and eleven final-battle rows.

**3.4 The typo'd key.** `h3_dlc23_chd_ancestor_relics_unlock_derpy_ghorth` lost its leading `w`.
Fixed. Nothing outside the DB row referenced it, so this changes no behaviour — the row is in the
never-triggered family for a different reason (§4).

---

## 4. Still broken, deliberately out of scope

**The relic chain never starts.** CA's `drill_structure_progress` listener fires on any
`MissionSucceeded` whose key starts with `wh3_dlc23_chd_ancestor_hellshard_structure_`, which now
includes all twelve, and calls
`cm:trigger_mission(faction_key, "wh3_dlc23_chd_ancestor_relics_unlock_" .. faction_key)`. HLL's
eleven relic-unlock rows are suffixed with the **lord subtype** (`derpy_ghorth`), not the faction
key, so that trigger finds no row and fails silently. Same shape for the eleven final-battle rows.

This is `GHORTH_MISSION_OPTIONS_20260903.md` §2's "22 of 33 rows unreachable", and renaming them
is *not* a free fix: they are `FIGHT_SET_PIECE_BATTLE` rows that need the relic armies
`trigger_relic_missions` spawns, plus option junctions and payloads of their own. Making them fire
half-configured is worse than leaving them dark. Next session's decision, not this one's.

Also unchanged: `drill_structure_progress` places the `drill_stage_01` composite scene only for
the three vanilla factions, so a house that completes the mission loses `drill_stage_00` and gets
no replacement. Cosmetic, and it needs the same override the relic work will need anyway.

`derpy_gordak`'s hellshard row got the full junction set even though Gordak has a skill tree and
no faction and nothing can ever trigger it — a complete row nobody reaches beats a half-configured
one somebody later trips over.

---

## 5. Verification actually run

- `--selftest` (no RPFM, no game): 34 mission rows with no duplicate key, the minted Abnagg row
  differs from its donor in exactly the `key` column, no `chd/generic` survives, every one of the
  twelve lords has a row and exactly the four options in order, 60 junction ids unique and in
  range, both builders idempotent over their own output, all 14 Lua pairs resolve to a row that
  exists (the three vanilla ones checked against CA's cached `missions_tables`), no two factions
  share a mission row, and the four previously-broken factions are each paired correctly.
  `wh3_dlc23_chd_factory_drills_2` and `wh3_dlc23_chd_drill_structure_reward` are checked against
  the vanilla cache too.
- Duplicated-combined-key check against the schema's own `is_key` columns, before every import.
- `luac -p`, `tools/check_lua_api.py`, `tools/check_lua_undeclared.py` — all clean on both copies.
- **Read back from the saved pack**, not from RPFM's memory: all four tables re-exported and
  diffed row-for-row against the generated TSVs (48/12/12/34, exact), table versions confirmed
  2/2/1/0, and the in-pack Lua byte-compared against the staged source.
- Workshop copy hash-equal to `Modpacks/`.

---

## 6. Not verified — the one thing left

**No campaign has been run.** The game was closed for the deploy. What a launch would answer, in
order of what would actually go wrong:

1. Does the mission appear at all now, in **singleplayer**, as any of the ten houses? This is the
   whole point of §2.
2. Does `bad_mods_report.txt` reject any of the 106 new rows at load? Three tables are new to this
   pack and were never loaded before.
3. Does the objective line read sensibly, i.e. does `mission_text_text_*` matter here? Still the
   open question from `MISSIONS.md` — these rows carry their title and description in the DB row
   and the pack's `.loc` has no entry for them.
4. Does the payload pay? `wh3_dlc23_chd_drill_structure_reward` is CA's, applied `GLOBAL` for 5
   turns.

The free probe from the last session still applies: dump
`objectives_screen > subpanel_missions > mission_list_view > list_clip > list_box` and read each
row's child — `tick` completed, `button_pin_mission` open.

---

## 7. Do not re-derive

All of this was read out of the shipped pack, `ui2.pack`, `.skilltree_cache` or CA's own scripts
this session. None of it needs RPFM open.

- **The four table versions this pack now ships**: `missions` **0**,
  `cdir_events_mission_option_junctions` **2**, `cdir_events_mission_payloads` **2**,
  `cdir_events_mission_issuer_junctions` **1**. Confirmed twice — measured in
  `HANDOFF_20260903_MISSIONS_FIRST_BUILD.md` §3, and re-read back out of the saved pack here.
  RPFM also offers `missions` v6; it is the wrong shape.
- **CA's complete hellshard row shape**, per vanilla faction: four option junctions
  (`VAR_CHANCE 100`, `VAR_MISSION_LENGTH_INFINITE` empty, `GEN_TARGET_NONE` empty,
  `VAR_OBJECTIVE_BUILDING_LEVEL <faction's own great-drill landmark>`), one payload
  (`EFFECT_BUNDLE / SUCCESS / KEY[wh3_dlc23_chd_drill_structure_reward];DURATION[5];GLOBAL`),
  and — this is the surprise — **an issuer row only for `legion_of_azgorh`**. Astragoth and Zhatan
  have none, so `cdir_events_mission_issuer_junctions` is evidently optional.
- **`ui/eventpics/chd/generic.png` does not exist.** `ui2.pack` is the only pack carrying
  `ui/eventpics/chd/` and it holds exactly 24 files: `army_morale_down`, `army_morale_up`,
  `besieged`, `blockaded`, `celebration`, `civilisation_down`, `civilisation_up`, `convoy_bad`,
  `convoy_commerce`, `convoy_good`, `defeat`, `diplomacy`, `economy_down`, `faction`, `funeral`,
  `hell_forge`, `land_defeat`, `land_victory`, `messenger`, `politics`, `settlement_lost`,
  `victory`, `zharr_boon`, `zharr_temple`. Every other race in that pack **does** have a
  `generic.png`; chd is the only gap, and CA's own rows point at it.
- **`wh3_dlc23_chd_factory_drills`** is the only CHD drill chain a mod faction can raise:
  `settlement_type_to_building_chains_junctions` binds it to settlement type
  `wh3_dlc23_chd_factory`, it has no row in `building_chain_availabilities`, and its levels are
  `only_in_capital` false / `faction_unique` false. Two levels only, so `_2` is its top.
- **CHD has exactly three settlement types**, and `wh3_dlc23_chd_tower` is the ordinary **major
  settlement**, *not* the Tower of Zharr — the Tower is rituals, not buildings. `_tower` takes 243
  chains including `wh3_dlc23_chd_tower_{tribute_halls,furnace,ballistics,living_quaters,patrol,
  port,temple_guardhouse,temple_of_hashut}` and the `military_{beasts,kdaai,war_machines,
  chaos_dwarf_infantry,hobgoblins}` chains; `wh3_dlc23_chd_factory` (231) takes
  `factory_{drills,assembly_line,refinery,port,garrison}` and `military_{war_machines,
  chaos_dwarf_infantry,hobgoblins}`; `wh3_dlc23_chd_outpost` (233) takes
  `outpost_{mine,overseer_hut,port,scavangers_hovel,watch_towers}` and `military_hobgoblins`.
  So the options document's S1 (`wh3_dlc23_chd_tower_tribute_halls_3`) is buildable by any house
  in any major settlement, and `military_beasts` / `military_kdaai` are **major-settlement only**,
  which matters for V3 and G3.
- **Vocabulary counts, for sanity-checking a future row**: vanilla has 815 `EFFECT_BUNDLE`
  mission payloads, 2,424 `CLAN_ELDERS` issuer rows, and 3 rows carrying the exact payload value
  string reused here.
- **`chaos_dwarfs_narrative.updates.player_faction_key`** is set by CA's own `initialise()` loop
  in *both* branches and read only by `spawn_relic_armies`. A mod override does not need to set
  it, which is why dropping that line from the trigger block is safe.
- **The staged Lua and the in-pack Lua differ only in line endings** — the pack copies are CRLF,
  `Modding Files/pack/**` is LF. A `diff` of the two is meaningless without `tr -d '\r'`.
- **`Modding Files/pack/db/missions_tables/derpy_chd_ll_missions`** is a stale historical binary
  and is now out of date with the pack. Nothing in `tools/` reads `Modding Files/pack/db/`
  (checked); the TSVs in `Modding Files/source/hellshard_missions/` are the source of truth.

## 8. Re-running

```powershell
py tools\gen_hellshard_missions.py --selftest   # no RPFM needed
py tools\gen_hellshard_missions.py --check      # TSVs + Lua only
py tools\gen_hellshard_missions.py              # ...and import into Modpacks\, save
```

Then copy `Modpacks\!aa_derpy_hashut_legendary_lords.pack` over the Workshop copy with the game
closed. Both write steps are idempotent — the Lua patch finds its own marker comment and replaces
from there, and `build_missions` over its own output is a no-op, asserted in `--selftest`.

`missions_tables__base.tsv` is the generator's input and holds the 33 rows **as originally
shipped**. Do not regenerate it from the repaired pack; if it is ever lost, take it from
`Modpacks\backups\!aa_derpy_hashut_legendary_lords.pack.bak_premissions_20260903`.

---

## 9. Measured in game, 2026-09-03 evening — partial, and it found a bigger blocker

Campaign running was **Immortal Empires Expanded** as `wh3_dlc23_chd_conclave`, turn 1, with the
repaired pack loaded (`used_mods.txt` line 47) and `derpy_test_missions.pack` pulled.

**Confirmed working:**

- **No `bad_mods_report.txt`.** The three new tables and all 106 new rows load with no DB
  validation reject. This was the biggest risk and it is gone.
- **The DB row is accepted and issues.** `cm:trigger_mission("wh3_dlc23_chd_conclave",
  "wh3_dlc23_chd_ancestor_hellshard_structure_derpy_ghorth", true, true)` returned `true`, and
  the script log records the trigger *and* the issue:

  ```
  [out] ++ triggering mission from db wh3_dlc23_chd_ancestor_hellshard_structure_derpy_ghorth for faction wh3_dlc23_chd_conclave, fire_immediately: true
  [out] >> whitelist_event_feed_event_type() called, event_type is faction_event_mission_issuedevent_feed_target_mission_faction
  [ui]  Panel opened events
  ```

  **This is the DB route's log shape, and it is new** — the last session recorded only the string
  route's `++ triggering mission from string ... mission string is mission{...}`. The DB route
  prints `from db <key> for faction <faction>, fire_immediately: <bool>` and, on acceptance, the
  `faction_event_mission_issued` whitelist line and the mission-review panel. A row the engine
  rejected would print the first line and not the second.
- **Zero mission-related script errors.** `wh3_mcp_script_errors.log` holds 1,991 error lines
  accumulated over many sessions and **not one** matches `mission`, `hellshard`, `narrative` or
  `drill`. The noisy majority are another mod's `edict_tooltip.lua` calling
  `find_single_uicomponent` with a dead parent (1,590 of them).

**`cm:trigger_mission` is async.** `cm:mission_is_active_for_faction(faction_interface, key)`
returned `false` when called in the same `wh3_eval` chunk immediately after a trigger that the log
shows succeeded. Do not read it back in the same tick — that is a false negative, not a rejection.

### 9.1 The blocker: the trigger file is in campaign folders that are never loaded

The repaired `!!!narrative_chaos_dwarfs_new_factrions.lua` ships in **`cr_oldworld` and
`cr_darklands` only**, exactly as it always has. Measured against what is actually installed:

| Campaign folder | Provided by | Enabled? |
|---|---|---|
| `cr_combi_expanded` (+ `wh3_main_combi`) | `!cr_immortal_empires_expanded.pack` | **yes — this is what is played** |
| `cr_oldworld` | `!cr_oldworld_campaign.pack`, Workshop **3081800026** | **no** |
| `cr_darklands` | **nothing.** No installed pack provides that campaign | n/a |

`cr_darklands` was scanned across every installed Workshop pack: the only packs that mention it
are `!aa_derpy_hashut_legendary_lords.pack` (25 files) and three `derpy_units_*` packs. **HLL
carries 25 script files for a campaign that does not exist on this machine.**

So with the current mod list the hellshard mission cannot fire in any playable campaign — the
§2 singleplayer fix is correct and lands in a folder nothing loads. Proved directly:
`cm:mission_is_active_for_faction` was `false` at turn 1 before anything was triggered by hand,
and the log's 210 `Loading mod file` lines contain no `narrative_chaos_dwarfs_new_factrions`.

Two ways forward, and they are not the same job:

- **Verify as built** — enable `!cr_oldworld_campaign.pack` (3081800026), start an Old World
  campaign as `cr_chd_house_of_bzaark` or `cr_chd_slaves_of_the_black_dwarf` (both were mispaired
  *and* singleplayer-gated, so one campaign exercises both fixes). No new code.
- **Make it work in IEE** — ship a third copy of the trigger under `cr_combi_expanded`. IEE
  carries only three of these lords (`ime_derpy_abnagg.lua`, `ime_derpy_black_dwarf.lua`,
  `ime_derpy_ghorth.lua`), and the copy must **not** include the `trigger_relic_missions`
  override: that override hardcodes `cr_oldworld_region_*` keys and IEE uses
  `wh3_main_combi_region_*`, so CA's own unmodified version is already correct there. It needs
  IEE drill coordinates, which the `cr_oldworld` values are not.

### 9.2 Bridge note

`UIComponent:GetContextObjectId(0)` returns **no values**, the same shape as
`common.get_context_value`. Passing it to `type()` or `tostring()` inside a `wh3_eval` chunk
wedged the MCP bridge — every later command answered `failed to parse command JSON: nil`, cleared
only by restarting the game. Assign it to a local and test it alone first, or read the panel rows
by component `Id()`, which already encodes the CCO type and faction
(`CcoCampaignMissionwh3_dlc23_chd_conclave4`).

---

## 10. The IEE trigger — built, in the pack, not yet deployed

Answering §9.1: rather than enable a campaign mod that is switched off, the trigger now also
ships for the campaign that is actually played.

`script/campaign/cr_combi_expanded/mod/derpy_chd_hellshard_start.lua`, 4,133 bytes, generated by
the same `tools/gen_hellshard_missions.py` from the same `STARTS` table, so the faction -> mission
mapping has one source and cannot drift between the three files.

Four things make it a **separate, standalone file** rather than a third copy:

- **It defines no CA function.** The Old World copies override
  `chaos_dwarfs_narrative:trigger_relic_missions()` with `cr_oldworld_region_*` keys; IEE uses
  `wh3_main_combi_region_*`, so CA's own unmodified version is already correct here. Asserted in
  `--selftest` (`"function chaos_dwarfs_narrative:" not in iee`).
- **It overwrites none of CA's drill locations.** The Old World copies reassign
  `drill_location_{astragoth,zhatan,drazhoath}` to Old World coordinates. On this map CA's values
  are right, and the file only reads them. Also asserted.
- **Drill positions are resolved at runtime**, off the faction leader, for the three mod factions
  — the idiom `ime_derpy_black_dwarf.lua` already uses and defends in its own header, because IEE
  may place a faction anywhere and hardcoded coordinates "cannot track a startpos". The guard is
  `not faction` first, because **`cm:get_faction` returns boolean `false`**, not nil. If no
  position resolves, the composite scene is skipped and **the mission still triggers** — the
  scene is decoration and must never gate the objective.
- **The basename is unique against `script/campaign/wh3_main_combi/mod/`.** IEE loads that folder
  *and* `cr_combi_expanded`, and silently drops the second file of any repeated name —
  `ime_derpy_ghorth.lua` is already lost that way, visible in this run's log as
  `Failed to load mod: [script\campaign\cr_combi_expanded\mod\ime_derpy_ghorth.lua]`.
  `--selftest` asserts the name does not exist in the `wh3_main_combi` folder.

Six entries: the three vanilla factions (multiplayer only, `loc` from CA) and the three IEE
actually places — `wh3_dlc23_chd_conclave`, `cr_chd_warfleet_of_uzkulak`,
`cr_chd_slaves_of_the_black_dwarf`. The other eight houses are not in IEE at all; the tower
seating script logs "seated 2, skipped 8".

**Checked before writing it:** all ten `cr_chd_*` factions carry subculture
`wh3_dlc23_sc_chd_chaos_dwarfs` (read from `db/factions_tables/!!_cr_oldworld_new_factions`), so
`cm:get_human_factions_of_subculture` does reach them. That was the one unvalidated-key risk in
the loop.

`luac -p`, `check_lua_api.py`, `check_lua_undeclared.py` clean; in-pack copy byte-compared against
the staged source. **Deploy is blocked only by the game holding the Workshop file open** — the
copy over `3432966208/` still has to happen, and the MCP bridge needs the same restart anyway.

---

## 11. The IEE file failed on its first live load — `require` is not available there

Deployed and started a fresh IEE campaign as **Abnagg / `cr_chd_warfleet_of_uzkulak`**. The file
loaded and died on line 15:

```
Loading mod file [script\campaign\cr_combi_expanded\mod\derpy_chd_hellshard_start.lua]
  Failed to execute loaded mod file [...], error is: [string "...derpy_chd_hellshard_start.lua"]:15:
  module 'wh3_dlc23_narrative_chaos_dwarfs' not found:wh3_dlc23_narrative_chaos_dwarfs
Failed to load mod: [script\campaign\cr_combi_expanded\mod\derpy_chd_hellshard_start.lua]
```

**`require("wh3_dlc23_narrative_chaos_dwarfs")` works in `cr_oldworld` and not in
`cr_combi_expanded`.** CA's module lives in `script/campaign/wh3_main_chaos/` and is not on the
script path when `cr_combi_expanded` mod files load. A failed `require` at file scope takes the
**whole file** with it — the trigger never registered, and the log says so plainly, in the same
`Loading mod file` / no-`loaded successfully` pattern that found the CTD in
`HANDOFF_20260903_MISSIONS_FIRST_BUILD.md` §2.

**Why the `require` was there at all: scope I added and did not need.** The only thing that used
`chaos_dwarfs_narrative` was the three *vanilla* factions' drill locations, included for parity
with the Old World file so that multiplayer would be covered. Nobody asked for that. Removing
those three entries removes the dependency, and the file is now **entirely self-contained** — no
`require`, no reference to any CA table, three entries, 3,685 bytes. `--selftest` now asserts
`"require(" not in iee_code` and `"chaos_dwarfs_narrative" not in iee_code`, so it cannot come
back.

The IEE copy therefore no longer fires the vanilla three in multiplayer; CA does not either. That
gap is pre-existing, is CA's, and is not worth a cross-campaign module dependency.

### 11.1 What this run did confirm

**The minted Abnagg row works.** Hand-triggered in that campaign:

```
++ triggering mission from db wh3_dlc23_chd_ancestor_hellshard_structure_derpy_abnagg for faction cr_chd_warfleet_of_uzkulak, fire_immediately: true
>> whitelist_event_feed_event_type() called, event_type is faction_event_mission_issued...
```

So the row this script minted from Tordrek's is accepted and issued exactly like Ghorth's, and
**no `bad_mods_report.txt` was written** in a second, independent campaign.

### 11.2 Two panel facts, for the next attempt

- The mission rows live under `objectives_screen > subpanel_missions > mission_list_view >
  list_clip > list_box > **pinned_missions_list**`, one child per mission named
  `CcoCampaignMission<faction><n>` plus a `template_pinned_mission` at index 0. The detail pane is
  `objectives_screen > mission_details_list > tab_details_child > list_clip > list_box >
  objectives`, whose `dy_title` and `template_objectives/*/dy_objective` read cleanly with
  `GetStateText()` — that call did **not** destabilise the bridge, unlike `GetContextObjectId`.
- **Closing and reopening the panel empties `pinned_missions_list` to just its template** and it
  did not repopulate while the panel stayed open. Read the rows on the panel's *first* open, or
  find another route; do not close/reopen to refresh.

---

## 12. It ran. And it exposed the last defect: mission text is loc-driven, and the loc said PLACEHOLDER

Fresh IEE campaign as Abnagg, second attempt. The file loads and fires itself:

```
Loading mod file [script\campaign\cr_combi_expanded\mod\derpy_chd_hellshard_start.lua]
Mod [script\campaign\cr_combi_expanded\mod\derpy_chd_hellshard_start.lua] loaded successfully
...
XXX derpy_hellshard triggering wh3_dlc23_chd_ancestor_hellshard_structure_derpy_abnagg for cr_chd_warfleet_of_uzkulak XXX
++ triggering mission from db wh3_dlc23_chd_ancestor_hellshard_structure_derpy_abnagg for faction cr_chd_warfleet_of_uzkulak, fire_immediately: true
```

No `bad_mods_report.txt`, no "no drill position" line (the leader lookup resolved), and the
mission is on the objectives panel at turn 1 with **nothing hand-triggered**. The objective reads:

> Ensure that the following building has been constructed: **Tools Manufactory**

`wh3_dlc23_chd_factory_drills_2` renders by its in-game name in the objective's
`requirements_list`, so `VAR_OBJECTIVE_BUILDING_LEVEL` is doing exactly what §3.2 intended.

**But the title was blank.** The row's DB `localised_title` is "The Great Drill of Hashut".

### 12.1 `missions.localised_title` and `.localised_description` are LOC-DRIVEN

The DB columns are decoration. The game reads `missions_localised_title_<key>` and
`missions_localised_description_<key>` out of a `.loc` and **ignores the row**.

Proved by contrast in one campaign. Hand-triggered Tordrek's row alongside Abnagg's:

| Row | DB `localised_title` | loc entry | Rendered |
|---|---|---|---|
| `..._derpy_abnagg` (minted here) | The Great Drill of Hashut | none | *(blank)* |
| `..._derpy_tordrek` (shipped) | The Great Drill of Hashut | `PLACEHOLDER` | **PLACEHOLDER** |

So a missing key renders blank and a present key wins over the DB. There is no reading of this
where the DB column is used.

**And every one of `text/derpy_chd_ll_missions.loc`'s 99 mission entries was the literal string
`PLACEHOLDER`.** All 33 shipped rows have been showing the word PLACEHOLDER as their title,
description and completion text for as long as the pack has existed — invisible until now
because nothing ever triggered them (§2).

**Fix:** the generator now emits the loc too, taking the text from the DB columns the rows
already carry — `build_loc()`, 103 rows: 34 missions x 3 keys, plus the one
`units_custom_battle_permissions_override_name_*` row that lives in this same file and is passed
through untouched. `localised_mission_completed_text` is emitted **empty** rather than
PLACEHOLDER, matching CA, which leaves it empty on every row. The three orphaned
`missions_localised_*_h3_dlc23_...` keys are gone, so the §3.4 DB rename no longer leaves a
mismatched loc behind. `--selftest` asserts each mission key has all three loc keys, that the
title equals the DB column, that no `missions_*` value is PLACEHOLDER, that no `_h3_dlc23` key
survives, and that the passthrough row is kept.

Note the path, which is not the usual one: **`text/derpy_chd_ll_missions.loc`**, not
`text/db/...`. That is what this pack already shipped, and it works.

### 12.2 A verification trap worth not repeating

`export_tsv` right after the generator's own `push()` returned the **pre-import** content — the
agent's MCP session was holding the pack it had opened earlier, and RPFM answered from that
in-memory copy rather than from the file the other session had just written. The diff looked like
a failed import and was not one.

Read a just-saved pack **from disk**: `tools/read_pack_index.py` extracts the raw file with RPFM
closed, and loc strings are **UTF-16LE**, so search with `needle.encode("utf-16-le")` — a UTF-8
byte-grep returns 0 and means nothing ([[wh3-vanilla-loc-readable-offline]]). The Workshop copy
answers 34 hits for "The Great Drill of Hashut", 1 PLACEHOLDER (the passthrough row) and 0
`_h3_dlc23`.

### 12.3 Still not measured

Completion and the payload. Nothing has built a Tools Manufactory yet, so
`EFFECT_BUNDLE / wh3_dlc23_chd_drill_structure_reward` has not been seen to pay, and CA's
`drill_structure_progress` listener has not been seen to fire (it will, and it will then fail to
find `wh3_dlc23_chd_ancestor_relics_unlock_cr_chd_warfleet_of_uzkulak` — §4).

---

## 13. Title confirmed, and the drill was built in the sea

Third IEE campaign as Abnagg, after the §12 loc fix.

**`TITLE: [The Great Drill of Hashut]`** — read off the live objectives panel. The loc route is
confirmed working end to end: DB row -> generated loc -> rendered title, alongside
`OBJ: Ensure that the following building has been constructed:` and
`REQ: [Tools Manufactory]`.

**The composite scene, however, was on open water** — a drill rig on a scrap of land in the sea
off Zermuda. `drill_position()` read the **faction leader's own tile**, and Abnagg's leader is a
`DERPY_CHD_NAVAL_HORDE` that starts **afloat**. The idiom was borrowed from
`ime_derpy_black_dwarf.lua`, where it is right — that script is placing a *character*, and a
character spawn point is exactly the lord's tile. A drill is a building, and belongs on land.

**Fix:** `drill_position()` now resolves the **capital**, not the lord —
`faction:home_region()`, then
`cm:find_valid_spawn_location_for_character_from_settlement(faction_key, home:name(), false, true, 10)`,
the same call the Black Dwarf script uses for its own fallback branch. No home region -> the
scene is skipped and the mission still triggers, which was already the rule.

Measured live in the running campaign **before** deploying it, for all three IEE factions:

| Faction | `home_region()` | drill tile | lord was at |
|---|---|---|---|
| `cr_chd_warfleet_of_uzkulak` | `cr_combi_region_zermuda` | 199, 398 | 193, 362 (at sea) |
| `cr_chd_slaves_of_the_black_dwarf` | `cr_combi_region_gahhuks_encampment` | 1345, 800 | 1349, 803 |
| `wh3_dlc23_chd_conclave` | `wh3_main_combi_region_zharr_naggrund` | 935, 634 | 943, 628 |

`cm:remove_scripted_composite_scene("drill_stage_00")` cleared the stray rig from the running
campaign without a reload.

### 13.1 A region-namespace correction

`HOUSE_MISSION_OPTIONS_20260903.md` §8 says `cr_combi_expanded` and `wh3_main_combi` both use
`wh3_main_combi_region_*`. **Not true — IEE carries both namespaces at once.** The mod's own
factions sit in `cr_combi_region_*` regions (`cr_combi_region_zermuda`,
`cr_combi_region_gahhuks_encampment`) while vanilla's stay `wh3_main_combi_region_*`. Any
hardcoded region key for an IEE mission has to be checked per faction, not assumed from the
campaign. Note that `ime_derpy_abnagg.lua` *spawns* into `wh3_main_combi_region_barak_varr` and
yet the faction's capital is `cr_combi_region_zermuda`, so the spawn script is not a guide either.

Reading the region at runtime, as this script now does, sidesteps the whole question.

## 14. The capital fix was right and still showed nothing — the shroud flag

Reported after the next launch: *"the drill seems to appear on the edge of the map not besides
the capital"*, with a screenshot of the Great Drill panel.

Two separate things, and neither is what it looks like.

### 14.1 The panel's map is not the drill

The dark map in `chd_narrative_panel` is the **whole Immortal Empires world**, not the Darklands.
The pin sits on Abnagg's own territory. His capital, `cr_combi_region_zermuda`, is at logical
205, 393 — the far west ocean, north of Lustria. So the pin *is* beside the capital; the capital
is simply at the western edge of the world. Nothing to fix, and nothing that could be fixed:
the pin is CA's panel plotting the faction.

### 14.2 The drill was placed correctly and drawn nowhere

Measured live, turn 1, `cr_chd_warfleet_of_uzkulak`:

| probe | result |
|---|---|
| capital settlement | 205, 393 |
| `drill_position()` returned | 199, 398 |
| `region_data_at_position(199, 398)` | `cr_combi_region_zermuda`, `is_sea = false` |
| camera at that tile | sunken city, **no drill** |
| `remove_scripted_composite_scene("drill_stage_00")` then re-screenshot | frame unchanged |

The scene had been created — it just drew nothing. Re-adding the same scene key with the last
argument flipped made it appear immediately, on the reef beside the sunken city, six tiles from
the capital:

```lua
-- invisible
cm:add_scripted_composite_scene_to_logical_position("drill_stage_00", "wh3_dlc23_hellshard_00", 199, 398, 0, 0, false, true, false)
-- visible
cm:add_scripted_composite_scene_to_logical_position("drill_stage_00", "wh3_dlc23_hellshard_00", 199, 398, 0, 0, false, true, true)
```

Arguments 8 and 9 are `show_in_seen_shroud` and `show_in_unseen_shroud`. CA passes
`true, false` everywhere, which is safe **only because CA's drill sites sit inside the starting
army's vision**. A naval horde owns its capital region without having explored it, so the tile is
in *unseen* shroud at turn 1 and a `false` there means the scene draws nothing at all. No error,
no log line — the same failure shape as [[wh3-listener-condition-fails-silently]].

Fixed in `tools/gen_hellshard_missions.py` for all three generated files. `--selftest` now walks
every `add_scripted_composite_scene_to_logical_position` call in both templates and fails any that
does not end `false, true, true`, so a later regeneration cannot quietly revert it.

### 14.3 What was not changed, and why

Zermuda renders as a submerged ruin, so the drill stands in shallow water even though the engine
calls the tile land. That is what the region is; there is no dry tile in any of the Warfleet's
three regions (`estragons_island`, `zermuda`, `sunken_island_of_the_gods` — all sunken). Placing
the rig in the Darklands instead would put a house's drill in another faction's territory, and
skipping the scene for the two naval houses would cost them the only visual the mission has. The
reef placement was left as is.

