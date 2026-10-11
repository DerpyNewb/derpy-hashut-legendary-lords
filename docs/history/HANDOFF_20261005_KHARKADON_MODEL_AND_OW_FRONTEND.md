# Kharkadon's own model and anim bin, and the Old World lord-select rows

2026-10-05. Packs: `!aa_derpy_hashut_legendary_lords.pack` (Workshop `3432966208`) and
`!!!derpy_chd_assets.pack` (Workshop `3297605217`). Asked: "in the hll apply the model for kharkadon
for all the related tables ... has its own animation bin", then "the faction effects are not
configured front end for the old world?".

**Both deployed to the Workshop folder, neither uploaded.** The model is confirmed in game on
lord select (user's screenshot of the Old World, 22:58). The lord-select fix (§3) has not been seen in
game yet.

| Pack | Workshop md5 now | Backup of what it replaced |
|---|---|---|
| lords pack | `a055b90f` | `Modding Files/Backup/pre_ow_frontend_rows_20261005/` (that was `c9de3843`, the §2 build) and `pre_kharkadon_model_20261005/{workshop,modpacks}/` (the pre-session copies) |
| assets pack | `627116c8` | `Modding Files/Backup/pre_kharkadon_bin_fix_20261005/` |

## 1. What Kharkadon is

`derpy_zharrduk`, leader of CA's `wh3_dlc23_chd_minor_faction` (Overlords of Zharrduk), built by
`tools/gen_new_house_lords.py` by cloning Balur. Until today he wore CA's Overseer. See
`HANDOFF_20261003_NEW_HOUSE_LORDS.md` §1, whose Model and Lord-select rows are updated.

## 2. The model (lords pack, 5 files changed)

| Where | Was | Now |
|---|---|---|
| `battle_animations_table_tables/derpy_chd_ll` | - | `derpy_kharkadon` / `humanoid03` |
| `land_units_tables` `derpy_zharrduk.man_animation` | `hu3_dwarf_axe_and_shield_thane` | `derpy_kharkadon` |
| `variants_tables` `derpy_zharrduk` and `_campaign` | `chd_overseer` / `chd_overseer_campaign_01` | `derpy_kharkadon` (both, as Balur does) |
| `ui/frontend ui/front_end_models/wh3_dlc23_chd_minor_faction/` twui + warscape_req | Overseer campaign mesh | `derpy_kharkadon` |

Kept on the Overseer on purpose: battle entity `wh3_dlc23_chd_cha_overseer`, campaign anim
`cam_hu3_dwarf_axe_and_shield` (Kharkadon's mesh has the axe on `weapon_2`/`be_prop_1` and the shield
on `be_prop_2`, the same as CA's `chd_overseer.variantmeshdefinition`), and the 2D porthole and
portrait settings (an image, not the mesh).

Generator changes: `LORDS[0]` gains `mesh=` / `anim=`; `battle_animations_table_tables` left
`SKIP` and `fix()` re-keys Balur's cloned row to `L["anim"]` (None for a lord without one);
`OWNED` covers `derpy_kharkadon`; `check_own_models()` fails the build if the Workshop assets pack
lacks the variantmeshdefinition or `animations/database/battle/bin/<anim>.bin` inside one of its
`.animpack`s; `check_frontend_models()` now also looks in the assets pack. `--selftest` covers both.

## 3. Old World lord select: wrong Lord effects, empty Faction effects

The Old World mod (`!cr_oldworld_campaign.pack`, Workshop `3081800026`) ships its own
`frontend_faction_leaders` rows in `cr_mixer_factions_being_used`, and they name the wrong lords:
`cr_oldworld_political_party_chd_minor_faction` names `wh3_dlc23_chd_sorcerer_prophet_hashut`,
`cr_oldworld_political_party_chd_skullstack` names `mixer_dummy`. The lords pack overrode the
equivalent row for Balur and Ghorth but not for the two new lords.

The OW `campaign_select_new.twui.xml` binds:
- **Faction effects** = `CcoFrontendFactionLeader.FactionEffectBundle.EffectList`, which is the
  leader's agent subtype's `faction_starting_general_effects` bundle (`derpy_zharrduk_lord_trait`;
  CA's equivalent is `wh3_dlc23_lord_trait_chd_astragoth`, same flags: faction, not global,
  owner only). A Sorcerer-Prophet has none, so the list was empty.
- **Lord effects** = `FrontendFactionLeaderRecordContext.SkillEffectList`, the subtype's skills.
  That is where the Winds of Magic lines came from.

Fix: both keys added to `LORDS[...]["frontend"]`, so `add_frontend()` writes the rows (template:
IEE's warfleet row, map pin -1/-1 like the OW mod's own row) and `loc_text()` their four loc keys.
Built, imported, 88 fragments verified, only `!!derpy_cr_new_factions` and
`derpy_chd_ll_factions.loc` changed.

## 4. Corrections found the hard way

- **A full `--import` of `gen_new_house_lords.py` deleted 9 Great Drill mission loc rows.**
  `gen_hellshard_missions.py` writes `missions_localised_*_derpy_zharrduk|uzkul|skullstack`; this
  generator's `OWNED` matched them and dropped them, and `SKIP_LOC` stopped them being cloned back.
  Fixed: `keep` leaves SKIP_LOC-matching loc rows alone. Caught by diffing every output fragment
  against a fresh pack extract BEFORE importing - do that on every run of this generator.
- **The import re-adds 30 loose files** (staged Lua, seat art, leader PNGs, portrait bin). All 28
  untouched ones were byte-identical to the pack this time; check again before an import, since a
  stale staged `.lua` would overwrite newer pack Lua.
- **`Modpacks/` was stale.** The Workshop lords pack held Ghorth's new porthole (Unit card session,
  same day); synced into `Modpacks/` before building.
- **AssetEditor saves to its project pack**, `Modding Files/AssetEditor Projects/!!!derpy_chd_assets.pack`
  (`aeproject.json` `SaveLocationPath`), not the Workshop copy. The user's first "fixed it" changed
  neither; the second save landed in the project pack only. Diff the two (7,344 files, one differed)
  and deploy.
- **The assets pack's animpack is LZ4-compressed** (`04 22 4d 18` after the u32 size), not zstd.
  `lz4.frame.decompress(data[4:])`. `read_animpack.py` reads the decompressed bytes.
- **AssetEditor writes `.anm.meta` paths with backslashes.** Fine - Balur's and Ghorth's bins
  already do, and work. A regex for meta paths must allow `\`.

## 5. Do not re-derive

- `battle_animations_table_tables.key` IS the bin name: `derpy_balur` <-> `derpy_balur.bin`. No
  other table names the bin.
- Kharkadon's bin: `derpy_kharkadon.bin`, 323 slots, `humanoid03`, in
  `animations/database/battle/bin/derpy_hu3_legendary_lords.animpack` (assets pack).
- The OW frontend leader keys are campaign-bound and come from the OW mod; ours override them by
  key (our fragment `!!derpy_cr_new_factions` sorts first). Balur's OW row is the working precedent.
- `frontend_faction_leaders_tables` has no effect column, and WH3 has no political-party tables:
  both effect lists come from the named agent subtype.

## 6. Open

- Not yet seen in game: Old World lord select showing Kharkadon's lord trait under Faction effects
  and his own skills under Lord effects; the Captain likewise.
- Kharkadon's bin still names `deaths/hu3_sws_vs_hu18_bonebreaker_drill_matched_death_01.snd.meta`,
  which neither our pack nor CA's ships (sound only). `derpy_snakebeard.bin` and
  `derpy_snakebeard_artificers.bin` name five dual-axe / Garagrim `.anm.meta` files nobody ships -
  those attacks play without event data. Not touched.
- Battle not tested: the anim table, the scale (variants 1.15 battle / 1.0 campaign, inherited from
  the Overseer clone) and the campaign-map anim on the new mesh.
- Neither pack uploaded. Upload reverts other deployed-not-uploaded packs; see memory
  `workshop-is-the-live-copy`.
