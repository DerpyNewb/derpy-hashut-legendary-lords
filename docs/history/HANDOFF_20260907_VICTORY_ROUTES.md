# Handoff 2026-09-07 — the victory conditions rebuilt as VCO-style routes

The eleven houses' victory conditions were CA's generic "paint the map" fallback. They now have
three named alternative routes each, built by the mission-string method measured out of
`victory_conditions_overhaul.pack`.

**State at the end:** deployed **15,833,486** bytes, sha256 `5af9270ccce282a5`, in both
`Modding Files/Modpacks/` and
`F:\SteamLibrary\steamapps\workshop\content\1142710\3432966208\` (byte-identical, hashed both
sides). **Nothing has been run in a campaign** — section 6. Not uploaded to the Workshop.

---

## 1. Where it started

`derpy_chd_victory_objectives.lua` registered all eleven houses in CA's
`victory_objectives_<campaign>.factions` table. That was a *repair*: `create_long_objective`
hides the subculture objectives behind `if self.factions[faction_key] then`, so a faction with
no entry loses the whole Chaos Dwarf long victory. It worked, and it was all it did — every
house's `objectives` list was empty, so the short victory was CA's alignment fallback for all
eleven, identical to Astragoth's.

## 2. What was measured, and what it overturned

The Steam discussion the user linked (`3140200173`, thread `6273018183380408557`) turned out to
be Oh_Man's compatibility/troubleshooting post — script breaks, `<dummy>` text, the Cost-Based
Army Caps freeze. **No code and nothing about custom objectives.** The pack itself is installed,
so it was read instead.

Six measurements, three of which corrected something written down here:

| # | Measured | Effect |
|---|---|---|
| 1 | VCO's objectives are **mission blocks in `missions.txt` syntax**, issued with `cm:trigger_custom_mission_from_string` | **Corrects `VICTORY_CONDITIONS.md` §9**, which said they build a mission manager by hand, and **§10**, which said the string route only works through `mission_manager:add_new_objective` |
| 2 | `cm:get_campaign_name()` returned **`cr_oldworld`** in a live campaign; the call just returns whatever the start script passed to `set_campaign_name` (`lib_campaign_manager.lua:714`) | VCO's `require` path is keyed on it and its Immortal Empires folder is `main_warhammer`, a *script root*. Not derivable, and seven mods redeclare the `cr_oldworld` row. Path convention dropped |
| 3 | `victory_objectives_oldworld` reads fine as a plain global, but `rawget(_G, "victory_objectives_oldworld")` is **nil** | **The mod script environment is not `_G`.** A `_G[name]` probe finds nothing, in every campaign, and reports the table absent when it is right there |
| 4 | `mission_manager` is keyed `(faction_name, mission_key)` — `lib_campaign_mission_manager.lua:96` | VCO gives all three of a faction's routes one key. Three slot rows instead, question removed |
| 5 | Vanilla `victory_types` icons are the bare names `short`, `long`, `ultimate`, `domination` | Reusing them ships **no art at all**; VCO ships three PNGs |
| 6 | `wh_main_dwf_dwarfs`, `wh_main_grn_greenskins`, `wh3_dlc23_chd_conclave`, `cr_chd_house_of_azeros` all present in a live `cr_oldworld` campaign | The `DESTROY_FACTION` targets are safe on that map. A faction absent from a map makes its objective unachievable for ever |

## 3. What shipped into the workspace

| Path | What |
|---|---|
| `tools/gen_victory_routes.py` | the generator, `--check` / `--selftest`. Carries the 33 routes as data |
| `tools/import_victory_routes.py` | pushes the three fragments and the script into the lords pack **in place**, deletes the four superseded copies, `--verify-only` re-opens the saved pack in a fresh session |
| `Modding Files/pack/script/campaign/mod/zzz_derpy_chd_victory_routes.lua` | generated, 18,497 bytes — **one file, loads in every campaign** |
| `Modding Files/source/victory_routes/victory_types_tables__derpy_chd_victory.tsv` | 33 rows, v3 |
| `Modding Files/source/victory_routes/missions_tables__derpy_chd_victory.tsv` | 3 rows, v0 |
| `Modding Files/source/victory_routes/loc__derpy_chd_victory.tsv` | 33 display names |

Route I is the house's own craft, II the Tower (`DISTRICTS_ANNEX_T5_*` plus conclave influence),
III the war (`DESTROY_FACTION` plus settlements). Names come from
`HOUSE_MISSION_OPTIONS_20260903.md` §5, which had already drawn three lore-grounded quests per
lord out of that lord's skill line. Completing **any one** of a house's three wins.

**Deleted:** the four copies of `derpy_chd_victory_objectives.lua`, and
`tools/check_victory_objectives.py` which existed to check them. Both archived under
`docs/archive/` with a `.bak_superseded_20260907` suffix — *not* as `.bak_` files inside
`pack/`, where three already sit and would ship.

## 4. The four departures from VCO, each with its reason

- **One file in `script/campaign/mod/`.** That folder loads in every campaign — our own Zharr
  Exchange scripts already prove it. So no `require` path, no campaign dimension, no four
  copies. The cost is that the routes must be **map-agnostic**: no region and no province
  objective, because those keys carry the campaign's prefix and one string cannot hold both
  namespaces. CA leans on `CONTROL_N_PROVINCES_INCLUDING` heavily; we cannot.
- **Three mission slot keys**, not one shared `vco_route_victory`. Two extra rows, no
  same-key question.
- **No `SCRIPTED` objectives.** VCO opens every route with one as a flavour paragraph and
  strips a literal `<dummy>` prefix in a UI listener. A `SCRIPTED` objective is only ever
  completed by `cm:complete_scripted_mission_objective`, so one nobody completes **blocks the
  victory for ever**. Every objective here is engine-evaluated.
- **Multiplayer untouched.** VCO `gsub`s its single key to `wh3_main_mp_victory`; with one key
  per route that would collapse three routes onto one MP key. The wrapper returns early only
  when CA's own `multiplayer` argument is false, and the trigger returns on
  `cm:is_multiplayer()`.

The disable guard is `ROUTES[faction_key]` rather than a separate list, so a faction we have no
routes for keeps CA's conditions. **No house can end up with no victory at all** — which is the
failure mode that matters, because a victory condition cannot be patched out of a running save.

The two naval houses carry no horde-building objective on purpose: no vanilla mission counts a
horde building (`HOUSE_MISSION_OPTIONS_20260903.md` §5, H1/K1, *Untested*).

## 5. What was verified

* `--check` clean: 11 houses, 33 routes, 33 victory types, 3 slots.
* `--selftest` green. It **runs** the generated Lua under Lua 5.1.5 against a stubbed campaign
  and reads back what it did: every house issued exactly three routes and had CA's init
  skipped; a faction we do not own issued none and **kept** CA's; multiplayer issued none and
  disabled none; every block brace-balanced and `;`-terminated; the three TSVs agreeing with
  `build()` row for row; and four deliberate breaks confirmed caught (a map-bound objective
  type, a blocking `SCRIPTED` objective, a typo'd pooled resource, an annex `total` larger than
  the house's own group can supply).
* `luac -p` clean. `check_lua_api.py`: 0 suspect calls.
* `check_lua_undeclared.py`: clean — **after fixing the tool.** It stripped `--[[ ]]` comments
  and quoted strings but not Lua **long-bracket strings**, so every ALL_CAPS word inside the
  `[==[ ]==]` mission blocks was read as an undeclared global: `DESTROY_FACTION`,
  `PERFORM_RITUAL`, `CLAN_ELDERS` and eleven more, on a file that is entirely correct.
  `_strip()` now removes `[=*[ ... ]=*]` with a backreferenced level. The tool's own
  `--selftest` still passes, and this fixes it for every caller, not just this file.

## 5a. The deploy

`py tools/import_victory_routes.py "<abs path to the lords pack>"`, then the same command with
`--verify-only`. It takes an **absolute** path; a workspace-relative one fails
`open_packfiles` with `os error 3`.

Imported: `text/db/derpy_chd_victory.loc` (33), `db/missions_tables/derpy_chd_victory` (3),
`db/victory_types_tables/derpy_chd_victory` (33), plus the 18,497-byte script. Deleted: all
four `derpy_chd_victory_objectives.lua`. **A file removed from `Modding Files/pack` is not
removed from the pack** — it sits there until something deletes it, which is why the importer
deletes them explicitly on every run rather than relying on the staging mirror.

Verified after saving, in a **fresh MCP session** against the saved file: every fragment
extracted back out as TSV and counted (33 / 3 / 33, matching source), the script present, all
four superseded copies confirmed gone, and the in-pack Lua byte-identical to the staged copy
(18,497 bytes both sides). Then copied to the Workshop folder and hashed on both sides.

Two RPFM parameter shapes cost a round each and are worth writing down: `packed_file_exists`
takes `value`, not `path`, and `get_rfile_info` takes neither — the round-trip through
`extract_packed_files` with `export_as_tsv` is a better check anyway, because a file that is
merely *present* proves nothing about whether it still decodes against the schema.

## 6. What is open

1. **Nothing has been run.** Riskiest first:
   - does `cm:trigger_custom_mission_from_string` accept these blocks at all — a malformed
     block is likely to fail silently, which is the whole reason `--selftest` checks braces
     and semicolons;
   - do the three routes appear as three nodes in the victory-conditions panel, with the
     `victory_types_display_name_*` loc drawn;
   - does the wrapper actually suppress CA's, i.e. is the panel free of the old short/long
     ladder for a house;
   - does completing one route end the campaign (`victory_type` is what ends it, not
     `game_victory` — §7).
2. **`DESTROY_FACTION` targets are verified on `cr_oldworld` only.** `cr_darklands` was not
   checked; nothing installed provides it. If either major is absent there, those eleven
   route-III objectives are unachievable on that map — the other two routes still win.
3. **The annex-group ceilings are arithmetic, not measurement.** `--check` enforces that a
   house's annex `total` stays under what its own group offers, on the documented rule that a
   house may perform any annex ritual but its own. That rule came from the old script's comment
   and has not been re-measured against `campaign_group_rituals`.
4. **A new campaign is required.** The routes are issued from an `is_new_game()` first-tick
   callback, so an existing save keeps whatever victory conditions it was started with.

## 7. Do not re-derive

* **`cm:trigger_custom_mission_from_string(faction_key, block)`** is a documented call —
  `episodic_scripting.html` line 12161. So are `cm:complete_scripted_mission_objective` and
  `cm:set_scripted_mission_text`. The `missions.txt` *file* is dead; its *syntax* is not.
* **The mission block's condition keywords**, harvested from all 5,472 lines of CA's
  `victory_objectives.lua`: `province, faction, region, total, total2, override_text,
  script_key, count, building_level, pooled_resource, set_piece_battle, event_category,
  ritual_category, subculture, text_display, start_pos_character, ritual`, plus the valueless
  flags `include_generals` and `confederation_valid`. `AMOUNT_INT` is `total`.
* **`SCRIPTED` with `total N` / `count 0`** is a progress counter, not a flavour line — that is
  CA's dwarf grudge-points objective.
* **CA's victory-context objective types** are the 17 in `gen_victory_routes.CA_VICTORY_TYPES`.
  A type can be a fine mission type and still never appear in a *victory* mission.
* **Vanilla `victory_types` icons** are bare filenames: `short`, `long`, `ultimate`,
  `domination`. `victory_type_links` draws the ladder and gates nothing — VCO ships no links
  row at all.
* **CA's scripts come out of `data_script.pack`** via RPFM `extract_packed_files`; the pack is
  Zstd, so byte-grepping it returns nothing. `open_packfiles` wants the **full path** as the
  `pack_key` afterwards, not the basename.
* **`script/campaign/mod/` loads in every campaign**; `script/campaign/<campaign>/` loads only
  in its own. The drill chain ships four copies for that reason — it did not have to, and that
  is a live simplification nobody has taken.
* **RPFM parameter shapes** that cost a round each: `packed_file_exists` takes `value`, and
  `get_rfile_info` takes neither `path` nor `value`.
* **`--verify-only` exists** — do not hand-check the pack in RPFM's GUI.

## 8. Reading order for the next session

`docs/VICTORY_CONDITIONS.md` §11 is the method, §12 is what we ship and why it departs from
VCO, §10 carries the new traps (`_G`, `get_campaign_name`, absent `DESTROY_FACTION` targets,
blocking `SCRIPTED`). §13 is the checklist, now split by which of the two routes you are taking.
