# Warrhak and Gordak by quest, not on turn one

2026-10-04. Pack `!aa_derpy_hashut_legendary_lords.pack`, current build `6d69a054` (2026-10-05), deployed
to the Workshop folder (md5 equal), **not uploaded, not seen in game**. Backups:
`Modding Files/Backup/hll_20261004_prewarrhak_quest/` (`4eca9dbd`, before any of this) and
`.../hll_20261004_preconfed_gordak/` (`1cfa9751`, quests without the confederation grant) and `.../hll_20261005_pre_tower_gordak/` (`eabc4f34`,
before the Tower's plain-IE Gordak) and `.../hll_20261005_pre_gordak_lvl10/` (`5fa26bae`, Gordak
level 10 by the Tower only).

## What changed

- **`temp_spawn_pool_chd_oldworld.lua` removed** from all four campaign folders (staged and
  pack). It pooled Gordak and Warrhak for any human Chaos Dwarf on turn one. It is now in
  `gen_victory_routes.DEAD_SCRIPTS`, so `check()` fails if it comes back to staging, and
  `import_victory_routes.py` deletes it from the pack on every run.
- **MCT option `start_free_lords` ("Gordak and Warrhak for hire") removed** from
  `script/mct/settings/derpy_hll.lua` and `DERPY_HLL_DEFAULTS`. `check_hll_settings.py`: 27
  settings, 0 failures.
- **Warrhak, "The Silver Mountain"**: `derpy_mis_warrhak_silverspear_ie` (gated
  `wh3_main_combi_region_mount_silverspear`, IE and IEE) and `_tow` (gated
  `cr_oldworld_region_mount_silverspear`, the Old World and the Dark Lands). Objective
  `OWN_N_REGIONS_INCLUDING` that region, pays 2,000 raw materials, and puts Warrhak in the recruit
  pool. Issued to **every human Chaos Dwarf faction, CA's three included**: the reach the old script
  had.
- **Gordak**: a second reward on Abnagg's `derpy_mis_abnagg_dawns_harbour` (user's choice:
  his trait is "Labourfleet", Abnagg's house). This makes him IE and IEE only, because the Fortress of Dawn
  is not on the Old World. The quest text names him. Level 10 on first recruit (`rank: 10`, 2026-10-05).

- **Gordak also comes with confederating Abnagg** (user request, build `eabc4f34`):
  `CONFED_GRANT` in the generator, keyed by the house absorbed, and the Gordak data is the
  Dawn's Harbour grant's own dict. Its `FactionJoinsConfederation` listener pools Gordak for
  `context:confederation()` when `context:faction()` is `cr_chd_warfleet_of_uzkulak`. The Tower's
  ANNEX route uses `cm:force_confederation`, so claiming Abnagg's seat in IEE counts.
  There is no duplicate guard: the quest is only issued to a human, and a human is never confederated in
  single player, so the absorbed house cannot already have Gordak.

- **Gordak comes with the Tower's Abnagg seat in plain IE, at level 10** (user request,
  2026-10-05, build `5fa26bae`). `zz_derpy_toz_annex.lua` (all four copies) gained
  `GRANT_COMPANIONS` (keyed by seat suffix) and `grant_companion()`, called from
  `on_annex_claimed` only when the seat's house is not live, i.e. GRANT mode. It pools Gordak and
  leaves `derpy_grant_rank_<claimant>_derpy_gordak = 10`, which the victory-routes script's
  `CharacterRecruited` listener applies. `gen_victory_routes.RANK_KEY_PREFIX` now builds that key,
  and `check()` fails if any annex copy builds another or stops pooling the Dawn's Harbour lord.
  This also covers IEE when Abnagg's house is dead. There is no Lua harness for the annex script
  in `tools/`. The scratch `annex_claim_test.lua` loaded the shipped file with `on_annex_claimed`
  exposed and ran 4 cases (IE, IEE live, own seat, another absent seat). 8 mutants were all killed:
  6 by that test and 2 by `check()`.

- **Gordak is level 10 by every route** (user request, 2026-10-05, build `6d69a054`). The Dawn's
  Harbour grant carries `rank: 10`. `CONFED_GRANT` is that same dict, so its Lua row now emits
  `rank` and the confederation listener leaves the same saved value the quest grant does. 5h
  recruits him before the confederation (no level), then twice after it (level once). Two
  mutants were both killed: the listener not saving the rank, and the row losing it. `check()` now
  also holds the Tower's `GRANT_COMPANIONS` rank to the quest's.

## New mechanisms in `tools/gen_victory_routes.py`

- **Culture quests**: `QUESTS[CULTURE]` (`wh3_dlc23_chd_chaos_dwarfs`). The Lua issues
  `QUESTS[faction:culture()]` after the house's own. A GRANT row's `faction` may be the culture.
  `check()` refuses a culture quest with `take` or a `TYPES_NEEDING_FACTION` objective.
- **Grant `rank`**: `spawn_character_to_pool` has no rank argument (its `50` is the AGE). The grant
  leaves the saved value `derpy_grant_rank_<faction>_<subtype>`. A `CharacterRecruited` listener
  then calls `cm:add_agent_experience(lookup, rank, true)` once and clears the value with `false`.
- The selftest gained 5f rank cases and 5g (Astragoth and Bzaark get the culture quest, the
  Empire does not), plus 3 breaks (25 in total). Five Lua mutants were run by hand and all
  were killed: culture issue gone, culture ignored, grant matching the faction only, rank never
  cleared, and rank passed as raw XP.
- 5h: confederating Abnagg into Astragoth pools Gordak for Astragoth exactly once, and absorbing
  Zhatan pools nobody. Three mutants were run by hand and all were killed: listener never
  registered, the absorbed house pooled instead of the absorber, and any absorbed faction matching.
- Quests are still single-player only. The MP early return covers them, as it did before. The
  grant, rank and confederation listeners register on every load in MP as well.

## Corrections found the hard way

- **The `50` in `spawn_character_to_pool` is AGE, not rank.** The 2026-10-04 lore handoff and
  the old script both read like a rank. There is no rank argument at all, hence the
  recruit-time `add_agent_experience(..., true)`.
- **A patch script with `\d`, `\t` or `\n` in it must go through the Write tool**, not a bash
  heredoc. The first confederation patch died on a mangled `"}\n"` (memory
  `bash-heredoc-eats-backslashes`). It asserted before writing, so nothing was half-applied.
- RPFM's `extract_packed_files` with `export_as_tsv` on a **folder** wrote binary tables, so a
  text grep for keys found nothing. To confirm a key, decode with
  `py tools/read_vanilla_db.py <table>_tables <pack>`. Names `12412533` / `12412534` and both subtypes are confirmed in the pack.
- I wrote "25 options" in `MY_MODS.md` without measuring it. `check_hll_settings.py` says 27
  settings, and that is what is written now.

## Do not re-derive

- Mount Silverspear: `wh3_main_combi_region_mount_silverspear` (CA's `campaign_map_regions`,
  covering IE and IEE) and `cr_oldworld_region_mount_silverspear` (grepped out of the installed
  `!cr_oldworld_campaign.pack`, Workshop 3081800026; the Dark Lands reuse that prefix). Sartosa is
  `wh3_main_combi_region_sartosa` / `cr_oldworld_region_sartosa` (Gordak's unused option).
- The Old World mod IS installed now (that pack), contrary to the lore handoff. Region keys come
  out of it with `grep -a -o "cr_oldworld_region_..."`, and that is faster than decompressing a save.
- The first lines of a save hold no campaign key. Every recent `Slaves of the Black Dwarf` and
  `Estalia` save decompressed to IE (`wh3_main_combi_region_*`).
- `FactionJoinsConfederation`: `context:faction()` is the absorbed faction and
  `context:confederation()` the absorber (CA `episode_neferata.lua:874-931`).
- Gordak's flavour, for later text: pirate, trait "Labourfleet", "Wave of Deceit",
  "Seascourge's Dagger", "Pirate's Leathers". Warrhak's: rune-breaker of dwarf holds,
  "Rune-Breaker", "Chains of the Daemon-Smith".

## Still open

- ~~Plain Immortal Empires has no Gordak~~: closed 2026-10-05, he comes with the Tower seat, above.
- **The Old World**: no Dawn's Harbour. Confederation works if Abnagg's faction exists, and the
  Tower seat grants him if it does not.
- None of this has been seen in game, and the pack is not uploaded.

## In game, first test

- IE as any Chaos Dwarf: the objectives panel shows "The Silver Mountain". Take Mount Silverspear
  and the log reads `derpy_warrhak joins <faction>`. Recruit him and the log reads
  `derpy_grant_rank_<faction>_derpy_warrhak raised to level 10`. Check the rank on his card.
  This first recruit is the untested half: `CharacterRecruited` firing for a lord from the pool
  is CA's own use (`victory_objectives_config_utils.lua`), but it has not been seen here.
- Abnagg on IEE: take Dawn's Harbour and Gordak is in the pool.
- Plain IE as any Chaos Dwarf: claim Abnagg's Tower seat. The log reads `derpy_toz_annex pooled
  derpy_gordak`, and Abnagg spawns at the capital. Recruit Gordak and check he is level 10.
- IEE: claim Abnagg's seat (confederation). Recruit Gordak and check he is level 10.
- The old turn-one grant must be gone: no Gordak or Warrhak in the pool at the start.
