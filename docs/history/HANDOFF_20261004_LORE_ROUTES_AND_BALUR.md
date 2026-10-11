# Lore pass on the victory routes, the Black Dwarf's Road to Praag, Balur as Gargath's brother

2026-10-04. Pack `!aa_derpy_hashut_legendary_lords.pack` (Workshop id 3432966208). Built
`3a7cc74b`, deployed to the Workshop folder (md5 equal), **not uploaded, not seen in game**.
Backup of the previous build (`c0e4de8a`): `Modding Files/Backup/hll_20261004_preroutes_lore/`.

## 1. Source

Lexicanum's "List of Chaos Dwarfs characters" and the per-lord pages, read through the Wayback
Machine (whfb.lexicanum.com answers 402/403 to direct fetches; `web.archive.org/web/<ts>id_/...`
with `--compressed` works). Lords with an entry: Abnagg, the Black Dwarf, Gargath (Balur is in
his entry), Ghorth, Snakebeard, Tordrek, Vraznak. No entry, left alone: Urzkhal, Bzaark, Azeros,
Kharkadon, the Captain.

User decisions recorded: Balur is a melee warlord in this mod (fan lore), Gargath stays home (no
"sent by Ghorth" quest), Vraznak is a Centaur lord by design, "Hashut's Chosen" is already renamed
in the unit pack, Bazherak is dead.

## 2. Routes changed (`tools/gen_victory_routes.py`)

Slugs unchanged everywhere - the slug is in the `victory_types` key, so only display names and
objectives moved. Old saves keep the routes they were issued.

| House | Route | Change |
|---|---|---|
| Black Dwarf | I | "The Unbreached Wall" -> **The Road to Praag**: where Praag exists (either namespace) 12 Kislev armies + 12 Empire armies + 25 sacks; elsewhere 25 sacks + 30 armies |
| Black Dwarf | II | renamed **A Seat on the Grand Council** |
| Balur | I | **Let the World Tremble**, + Hell-Forge melee infantry and Bull Centaur rituals |
| Balur | II | renamed **The Brothers' Altar** |
| Vraznak | III | **The Skull River Raid**: where `cr_oldworld_region_the_oak_of_ages` exists, 15 Wood Elf armies + 20 sacks + 2000 captives; elsewhere unchanged |
| Tordrek | III | where `cr_oldworld_region_barak_varr` exists: destroy `wh_main_dwf_barak_varr` + own Barak Varr + 20 sacks |
| Ghorth | IV | + Bull Centaur Hell-Forge ritual |
| Snakebeard | I | renamed **Crush, Crumble and Chop** |
| Abnagg | III | renamed **The Foundation Stone** |

Not built, and why: the Black Dwarf's gold target (`HAVE_AT_LEAST_X_MONEY`) and Tordrek's
Dreadfleet alliance with Noctilus (`MAKE_ALLIANCE`) - neither type is attested in a CA or VCO
victory objective, which `check()` requires, and VCO's `MAINTAIN_N_ALLIANCES` names no faction.

## 3. New mechanisms

- **A gate may be a tuple of region keys**, one per namespace; the Lua gets a table and
  `derpy_on_map` returns true if any exists. A tuple-gated list may not name a region.
  `check()` rule changed from "the gated list names its region" to "differs from the base list,
  and names no region its gate does not prove".
- **Sack-or-occupy quests** (`_take_quest`): one `SCRIPTED` objective per city, completed by
  listeners on `CharacterSackedSettlement` and `RegionFactionChangeEvent` (new owner = the
  faction), guarded by `mission_is_active_for_faction`. Registered on every load. Objective text
  is `mission_text_text_<script_key>`, loc only.
- **The Black Dwarf's quest**, twice: `derpy_mis_black_dwarf_road_to_praag_ie` (gated
  `wh3_main_combi_region_praag`, IEE) and `_tow` (gated `cr_oldworld_region_praag`). Sack or
  occupy Praag and Salzenmund; pays 20,000 gold and 150 Conclave influence.
- Selftest: harness replays events at the captured listeners. Four Lua mutants (no listener
  registration, no is-active guard, table gate never matching, sack listener on the wrong event)
  each fail it; four new `check()` breaks are caught.

Region keys: `cr_oldworld_region_*` read out of an Old World save body
(`read_save_values.body`) - the Old World mod is not installed here.

## 4. Balur and Gargath

- Loc, `text/derpy_chd_ll_units.loc`: Balur's short and long unit descriptions rewritten (Gargath's
  brother, a warlord of the axe, never took up the staff); one sentence added to Gargath's.
  `text/derpy_chd_ll_factions.loc`: Balur's Old World lord-select line names his brother.
  The same four lines were patched into `.skilltree_cache/extract`, which
  `gen_new_house_lords.py` rebuilds those files from. That extract is otherwise **stale against
  the pack** (it predates the 2026-10-04 drill rows) - do not run that generator with `--import`
  before re-extracting.
- `script/campaign/cr_oldworld/mod/derpy_chd_ll_diplomacy_starts.lua` (was an empty no-op): new
  game only, `cm:force_alliance("cr_chd_house_of_baal", "cr_chd_fists_of_hashut", true)`,
  skipped if either lord's MCT switch is off or either faction is missing. Old World only, not
  Dark Lands. Baal starts at war with `cr_grn_grey_hag_tribe`.
- Name drift, not touched: his campaign name is "Balur of Baal", his unit name "Balur of
  Baalrgath".

## 5. In game, first test

- Old World, Black Dwarf: objectives panel shows "The Road to Praag" quest with two lines; log
  `derpy_chd_victory_routes: issued 1 of 2 quests`. Sack Praag -> `..._praag completed by`.
- Old World, Balur or Gargath: diplomacy shows the military alliance; log
  `derpy_diplomacy_start alliance`.
- Vraznak / Tordrek on the Old World: route III shows the gated objectives.

## 6. Corrections found the hard way

- **My first proposal used three objective types nobody has used in a victory**:
  `RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_OF_SUBCULTURE`, `HAVE_AT_LEAST_X_MONEY` and `MAKE_ALLIANCE`.
  `check()` only admits CA/VCO-attested victory types. The subculture war is instead written as
  `DEFEAT_N_ARMIES_OF_FACTION` + `subculture`, which CA's own Lua issues through the string route
  (Cathay, `add_condition("subculture wh3_main_sc_cth_cathay")`). Gold and the Noctilus alliance
  were dropped.
- **No objective type means "sack OR occupy a named city"**: `RAZE_OR_SACK_..._INCLUDING` counts
  sack/raze, `OWN_N_REGIONS_INCLUDING` / `CAPTURE_REGIONS` count occupation. Hence SCRIPTED +
  listeners. `RegionFactionChangeEvent` covers every culture's own occupy variant, so the Lua names
  no `occupation_decision_*` key.
- **A seat-banner "gap" was a false flag** (corrected in `HANDOFF_20261003_NEW_HOUSE_LORDS.md`
  §11 and in memory): the `cr_chd_*` houses' seat art comes from IEE / the Old World mod.
- **Lexicanum blocks direct fetches** (402 to WebFetch, 403 to curl); Wayback `id_` URLs work, but
  only with `--compressed`, or the body is gzip noise. The Dwarf sub-list timed out twice.
- **Do not run `gen_new_house_lords.py` against another donor.** Its `OWNED` regex drops rows a
  previous run wrote, so pointing `LORDS` at Zochaz alone would delete Kharkadon's and the
  Captain's rows; and it builds from `.skilltree_cache/extract`, which is stale vs the pack.

## 7. Do not re-derive

- Old World region keys with the mod not installed: decompress a TOW save with
  `read_save_values.body()` and grep `cr_oldworld_region_*` (3,418 hits). Faction keys present on
  that map come out of the same body.
- Lexicanum per-lord facts used here: Black Dwarf - Praag, Salzenmund, the passes, the Grand
  Council, Barukh, Black Skull Mountain (WD 201). Gargath - House of Baal, Ghorth's patronage,
  the Fists of Hashut host with Balur as Sorcerer Champion (WD 203). Vraznak - 2497 IC raid with
  kinsman Sorcerer Lord **Zochaz**, revenge for a Sorcerer Lord killed in the Temple of Hashut,
  Blasted Waste, renegade Hobgoblin scouts at Mount Gunbad, forest burned with oil and tar,
  Battle of Skull River, Great Taurus (WD 170). Tordrek - Barak Varr, Red Brokk, Zhugulzar,
  Noctilus (Dreadfleet). Abnagg - Fortress of Dawn, foundation-stone oath, Hammerblaze (Plague
  Fleet). Snakebeard - Tenderiser, Whirlwind, Boar Centaurs (WD 103).
- Gargath's tree = 18 own nodes + CA's `wh3_dlc23_skill_node_chd_sorcerer_prophet_fire_*`
  nodes (that is where his spells come from - his `magic_lore` is empty). CA's lord subtypes are
  `wh3_dlc23_chd_sorcerer_prophet_{death,fire,hashut,metal}`.
- Faction-less lords reach a faction through `cm:spawn_character_to_pool(faction, name_id, "",
  "", "", 50, true, "general", subtype, false, "")` - Gordak and Warrhak, in
  `temp_spawn_pool_chd_oldworld.lua`. They have no `faction_agent_permitted_subtypes` row.

## 8. Zochaz - BUILT 2026-10-04, pack `4eca9dbd` in the Workshop folder, not seen in game

**Custom battle characters (later the same day, backup `Modding Files/Backup/hll_20261004_precb/`):**
every `units_custom_battle_permissions` general row names a `battle_set_piece_armies_characters`
row (name, model, portrait, LORE, items); CA leaves 0 of 864 dangling. Zochaz (skipped in the
first build), the Overlord of Zharrduk and the Captain of the Uzkul Mingol all were. Zochaz's now
comes from `gen_zochaz.py` (check 9: exists, his name/model/Lore of Hashut); the other two from
the new `tools/gen_new_lords_cb.py` (fragment `derpy_hll_new_lords_cb`, Gargath's row shape).
`py tools/gen_new_lords_cb.py --dangling <pack export>` is the whole-pack check - it reported
both on the old export and nothing on the new one. Not seen in a custom battle yet.

Backup of the pre-Zochaz build (`3a7cc74b`): `Modding Files/Backup/hll_20261004_prezochaz/`.

- **`tools/gen_zochaz.py`** (`--check`, `--import`, `--selftest`, 7 breaks). Clones every row
  holding `derpy_gargath` out of a fresh pack export (`tools/extract_pack_tsv.py` ->
  `Modding Files/source/zochaz/_pack`) into NEW `derpy_zochaz` fragments - 63 DB +
  `text/derpy_zochaz.loc`; no existing fragment is touched. Skips Gargath's faction, mission,
  set-piece, start-bundle and names rows and both custom actives.
- Model: CA's base Sorcerer-Prophet (variants `chd_sorcerer_prophet` /
  `chd_sorcerer_prophet_campaign_01`), porthole = CA's `..._hashut_01` block cloned into
  `portrait_settings_derpy_zochaz.bin` (portholes + units). `magic_lore wh3_dlc23_lore_hashut`,
  spells are CA's `..._sorcerer_prophet_hashut_*` nodes. Ids: name `12412537`, arts `696991703`,
  ability `13354703`, all checked free against CA and the pack.
- Skills/items/text are his own (`SKILLS` / `ITEMS` / `TEXT` in the generator); every
  (effect, scope) is one CA or the pack already uses. Passive and node 5 reuse Gargath's two
  icons on purpose. The mount skills keep Gargath's text (it only names the beast).
- **Unlock**: `derpy_mis_vraznak_kinsmans_raid` in `gen_victory_routes.py` QUESTS for
  `cr_chd_horns_of_hashut`, gated on `cr_oldworld_region_the_oak_of_ages`: 8 Wood Elf armies +
  5 settlements, 10,000 gold. New `grant` field -> `GRANT` table -> a `MissionSucceeded` listener
  calling `cm:spawn_character_to_pool(faction, "names_name_12412537", "", "", "", 50, true,
  "general", "derpy_zochaz", false, "")`. Selftest 5f; 5 grant mutants all killed.
- **Not gated on an MCT lord switch**: `derpy_hll_setting` answers nil for a key missing from
  `DERPY_HLL_DEFAULTS`, so `derpy_hll_lord_on("derpy_zochaz")` would silently never spawn him.
  Adding a switch means a default here AND the MCT page AND `check_hll_settings.py`.
- Found the hard way: the drop regex for `3_active` also matched node 5's ICON
  (`derpy_gargath_3_active_buff.png`) and dropped the skill row - `check_skill_trees` ERR
  "missing skill derpy_zochaz_5". `check()` 8 now asserts every node has its skill.
- `.skilltree_cache/extract` was refreshed by `check_skill_trees.py` against this build, so the
  §4 staleness warning no longer holds (it now includes Zochaz's rows).
- In game, first test: Old World as Vraznak - quest "The Kinsman's Raid" issued (log
  `issued 1 of 1 quests for cr_chd_horns_of_hashut`); complete it -> log
  `derpy_zochaz joins cr_chd_horns_of_hashut`, he is in the lord recruit pool with the Sorcerer-
  Prophet porthole and Lore of Hashut spells.
- Still open: the Black Dwarf's IEE lord-select army, unit packs for the houses that lack one,
  Kharkadon / Captain art and the Captain's name (see `HANDOFF_20261004_NEW_LORDS_FRONTEND_AND_WARS.md`).
