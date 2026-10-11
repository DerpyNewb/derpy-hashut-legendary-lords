# Hashut's Legendary Lords - MCT settings page (2026-10-03)

## 1. Build and deploy

- `!aa_derpy_hashut_legendary_lords.pack`, MD5 `fdf6e682f447ecdb4156c102ed1d3907`, 453 paths
  (was 451, MD5 `3a136816...`).
- Built into `Modding Files/Modpacks/`, copied to the Workshop folder
  (`F:\SteamLibrary\steamapps\workshop\content\1142710\3432966208\`), md5 equal. Backups
  `.bak_premct_20261003` beside both. **Not uploaded to Steam. Not played.**
- Packed by a one-off scratchpad script through `import_house_ancillaries.call` (RPFM's HTTP
  server): `open_packfiles` -> `add_packed_files` x47 -> `save_packfile`. There is no tool in
  `tools/` for this; `import_naval_horde.py` re-adds five of these scripts on every run from the
  staged mirror, which is now in sync, so that is safe.

## 2. What it does

One MCT page, mod key `derpy_hll`, title "Hashut's Legendary Lords", 26 options:

| Section | Keys | Read |
|---|---|---|
| Legendary lords | `lord_<subtype>` x11 (`derpy_abnagg` `_azeros` `_balur` `_black_dwf` `_bzaark` `_gargath` `_ghorth` `_snakebeard` `_tordrek` `_urzkhal` `_vraznak`) | frozen in the save at first read (turn one) |
| Tower of Zharr | `toz_ai_claims`, `toz_ai_start_turn` 10, `toz_ai_claim_chance` 25, `toz_ai_claims_per_turn` 1, `toz_annex_pct_per_rank` 1, `toz_annex_max_pct` 200, `toz_debug_log` false | live |
| Campaign start | `start_chd_influence` 5, `start_tower_influence` 25, `start_free_lords`, `ghorth_tiers`, `ghorth_stock`, `ghorth_gold` 10000, `ghorth_raw_materials` 2500, `ghorth_armaments` 1000 | once, new game |

Files:

- `script/mct/settings/derpy_hll.lua` - the page.
- `script/campaign/mod/derpy_hll_settings.lua` - `DERPY_HLL_DEFAULTS`, `derpy_hll_setting(key)`,
  `derpy_hll_lord_on(subtype)`. Multiplayer returns defaults before MCT is asked. Type-checked
  against the default. Keys starting `lord_` are written to `cm:set_saved_value("derpy_hll_<key>")`
  on first read and read from there afterwards.
- A switched-off lord: his start script's `add_first_tick_callback_new` is wrapped in
  `if derpy_hll_lord_on("<subtype>")` (23 files: `derpy_start_*` in `cr_oldworld`/`cr_darklands`,
  `ime_derpy_abnagg`/`_black_dwarf`). Ghorth is different: `derpy_ghorth_replace_1` returns early
  but still calls the new `derpy_ghorth_world_start()` (tiers, stock, diplomacy, each behind its
  own switch). In `zz_derpy_toz_annex.lua`, `apply_lord_switches()` at first tick fills
  `disabled_seat` and sets each annex district's `total_seats` to the seats left;
  `unlock_annex_rituals()` calls `cm:lock_ritual` instead of `unlock_ritual` for those seats.
- `zzz_derpy_toz_ai_seats.lua` lost `AI_START_TURN`/`CLAIM_CHANCE`/`CLAIMS_PER_TURN`;
  `zzzz_derpy_toz_debug.lua` lost its copy of `AI_START_TURN` and its `log()` is silent unless
  `toz_debug_log`.

Behaviour changes, not just knobs:

- **`debug_chd_influence.lua` used to grant on every load** (`add_first_tick_callback`, no
  `is_new_game`) and granted **5** while its log line said 75. Now new game only, default 5.
- The tower diagnostics log was always on; now off by default.

## 3. Verified, and how

- `luac -p` on all 47 files; `check_lua_api.py`, `check_lua_undeclared.py`,
  `check_lua_literal_left.py` clean.
- **New `tools/check_hll_settings.py`** runs the shipped page against a recording MCT stub and
  the shipped reader under Lua 5.1.5: page and defaults agree key-for-key both ways, MCT read
  live, wrong type falls back, MP falls back, lord switch freezes, and the real
  `derpy_start_azeros.lua` does not run with its switch off. Mutated (default 25->30, freeze
  removed, guard removed): 5 failures, then green after restore.
- Saved pack read back offline with `read_pack_index.py`: all 47 byte-equal to the staged
  files; vs the backup, 2 added, 45 changed scripts, 0 removed, 0 db changes past byte 80.

## 4. Do not re-derive

- **The staged mirror was stale for 20 files** (start scripts lacked the faction guard; the annex
  lacked the async-confederation fix and `OWN_T4_SEAT`). The pack's versions were copied over the
  staged ones before editing; old staged copies are in the session scratchpad `stage_bak/`.
- **`tools/gen_ghorth_settlement_tiers.py` is stale - do not run it.** It has no
  `DIPLO_FRIENDS` and emits 87 chains to the shipped 85; a write would drop Ghorth's diplomacy and
  these MCT edits. `--check` already reported WOULD WRITE before this session.
- The lords' tier-4 seats are CA's four only; "his tower seat" means the tier-5 annex seat.
- `cm:lock_ritual(faction_interface, key)` - two args, documented.
- Lord display names come from `text/derpy_chd_ll_names.loc` in the pack (`names_name_12412522`
  Ghorth ... `12412532` Abnagg); the loc is UTF-16 at an odd offset for half the entries.

## 5. Still open

- **In game:** does a script-locked annex seat read as locked on the panel, or as an active button
  that silently does nothing (`wh3-ritual-disabled-vs-script-locked`)? If the latter, the twui
  override needs a state for it.
- An old save loaded with this build freezes the lord switches at that load, not at its turn one.
- Upload to Steam and patch notes.

## 6. Castellan personal line on four lords, and the weak values buffed (2026-10-03, later)

**Built and deployed to the Workshop folder, not uploaded, not played.** Final pack MD5
`9ec8d00d287a04faa1dda8dba5bd02a6`. Backups beside both copies: `.bak_precastellan_20261003`
(before any of this) and `.bak_prebuffs_20261003` (after the first Azeros/Bzaark build, `51c782a8`).

### The line

- Azeros, Bzaark, the Black Dwarf and Warrhak carried CA's Sorcerer-Prophet fire combat line by
  reference (six `wh3_dlc23_skill_node_chd_sorcerer_prophet_fire_combat_*` nodes, lane 3). All four
  now carry the Infernal Castellan's combat line: 11 new nodes `derpy_shared_castellan_0` .. `_4`,
  skill for skill and tier for tier as `wh3_dlc23_skill_node_set_chd_infernal_castellan`
  (Survivalist; Indomitable, Bandolier, Blade Master, Piercing Shots; Extra Powder; Hard to Hit,
  Gunsight, Always Ready, Scarred Veteran; More Powder). Links copy the pack's
  `derpy_shared_combat_*` shape (16 rows, in the `derpy_ghorth` links fragment where that line's
  links already live); `_2` and `_4` at `required_num_parents = 4`. Tordrek still has fire combat.
- **Lane 3, not 2.** The first build put it on lane 2 (where the castellan has it). For the Black
  Dwarf that collided with CA's Metal magic line, which sits on lane 2 - `check_skill_trees.py`
  reported 11 ERR "slot holds 2 nodes" before deploy. Lane 3 is where the fire combat line sat for
  all four, so it is free for each.
- All four have a missile weapon (ammo: Azeros 500, Bzaark 90, Black Dwarf 30, Warrhak 10), so the
  five gun skills apply.
- The Infernal Castellan is CA's **engineer hero** (`wh3_dlc23_chd_infernal_castellan`); the lord
  with a castellan-type kit is `wh3_dlc23_chd_overseer`, shown as "Overseer".
- **Save note:** points a lord already spent in the fire combat line are on nodes no longer in his
  set. Not tested what the panel does with them in an existing save.

### The buffs

Audit method: every effect on each lord's own skills, at max level, against the median value CA
uses for that effect across its skills (`.skilltree_cache`). Most sat at or above CA; these were
raised, following CA's level steps where CA has the same 3-level shape:

| Skill | Was | Now | CA reference |
|---|---|---|---|
| Gordak `_1` ambush melee attack | 5 | 10 | innates 12-13 |
| Gordak `_2_2` hobgoblin speed | 10/15/20 | 10/20/30 | Gorduz `get_em` |
| Gordak `_2_3` ambush visibility | -10/-15/-20 | -15/-25/-35 | Oxyotl -50 (signature) |
| Gordak `_2_4` hobgoblin weapon strength | 4/8/12 | 10/15/20 | Gorduz `stab_em` |
| Gordak `_3` enemy movement | -15 | -30 | Aislinn, Verminlord -50 (signature) |
| Warrhak `_2_4` barrier recharge | 10 | 25 | Kairos 25 |
| Abnagg trait leadership at sea | 5 | 10 | 6, 15 |
| Gargath `_2_2` K'daai upkeep | -5/-10/-15 | -10/-15/-25 | Drazhoath -25 |
| Gargath `_4_1` K'daai upkeep | -15 | -25 | Drazhoath -25 |
| Snakebeard `_2_2` artillery ammo | 4/7/10 | 6/12/20 | CHD army line 6/12/20 |
| Snakebeard `_2_3` war-machine armour | 3/6/10 | 5/10/15 | Convoy Overseer 15 |
| Black Dwarf `_1` army armour | 10 | 15 | median 15 |
| Tordrek `_2_3` enemy movement | -5/-8/-10 | -10/-15/-20 | as Gordak `_3` |

The two -50 references are single signature legendary skills, so the middle and capstone stop short
of them. No skill description quotes a number, so no loc changed.

Not changed: Gargath `_1`, Ghorth `_4_1` and Azeros `_2_2` have only `_unseen` effects, so the skill
tooltip prints no effect line. They work; they just look empty.

### Changed and verified

Five fragments: `character_skill_nodes_tables/derpy_chd_ll_shared` (+11),
`character_skill_node_links_tables/derpy_ghorth` (+16),
`character_skill_node_set_items_tables/derpy_chd_ll_shared` (-24 +44), and
`character_skill_level_to_effects_junctions_tables/derpy_chd_ll_unique_skills` and `/derpy_chd_ll_trait`
(27 values). Built TSVs in `Modding Files/source/hll_castellan_line/`. The saved file was decoded
offline with `read_vanilla_db.py` and every table matches the build; pack diff vs backup touches only
those tables; `check_skill_trees.py` 0 ERR, the same 30 deliberate WARN;
`HASHUT_LL_SKILL_LINES.xlsx` regenerated. Build script: session scratchpad `castellan_line.py`; it
reads `.skilltree_cache/extract`, so run `check_skill_trees.py` first to refresh that from the pack.
