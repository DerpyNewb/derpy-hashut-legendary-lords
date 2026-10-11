# Kharkadon's pink model (texture colour space), two faction flags, and his portraits

2026-10-06. Four requests in one session, all about the Overlords of Zharrduk lord
(`derpy_kharkadon` since §6, `derpy_zharrduk` before it; Kharkadon the Vicious, CA's
`wh3_dlc23_chd_minor_faction`) and the Uzkul Mingol
Company (`cr_chd_skullstack`, IEE). Assets pack: `!!!derpy_chd_assets.pack` (Workshop `3297605217`).

## 0. State at the end of the session

| Item | State |
|---|---|
| Faction flags for both houses | Extracted to `Modding Files/pack/ui/flags/`. Not referenced by anything yet. |
| Four recoloured base-colour textures | **Fixed and in the live pack.** Patched in the project folder at 16:31; the user re-saved the Workshop `!!!derpy_chd_assets.pack` at 16:37 and all four now read `BC3_UNORM_SRGB` inside it. The user's next in-game screenshot shows the hat, mask and horns red, not pink. |
| Portraits for Kharkadon | **Approved and packed** (18:16; lords pack `216b3fb5` in the Workshop folder, not uploaded, not seen in game). Ships `porthole.png` as `ui/portraits/portholes/no_culture/derpy_kharkadon.png`, `card.png` as `ui/portraits/units/no_culture/derpy_kharkadon.png` and `modern.png` as `ui/portraits/faction_leaders/derpy_kharkadon.png` (the desert `leader.png` is superseded, not shipped). His entry in both `portrait_settings_derpy_hll_new_lords.bin` files now reads `['derpy_kharkadon', 'ui/portraits/portholes/no_culture/derpy_kharkadon.png']`, no masks, the 13 lords' shape (variant name = his `campaign_character_arts.uniform`; the Overseer variant it replaced did not match that). `gen_new_house_lords.py` owns all five through `LORDS[...]["portraits"]` and the pack was filled from its output; verified on the saved file: 3 replaced, 2 added, the other 562 byte-identical. Backup `Backup/pre_kharkadon_portraits_20261006/`. **The staged `Modding Files/pack/ui/portraits/` copies are an OLDER set** (8 of 13 cards, 6 of 13 portholes and the lord-select images differ from the pack's Partypus ones); compare against the pack, not them. |
| Modern lord-select image (Partypus's style) | **Approved and packed** (row above): `modern.png` (85x115) in the same folder, from `py derive.py --prepare modern` (one Codex pass: desert swapped for his fire ground, relit warm, four of his portraits attached as style references) then `py derive.py --modern` (contrast curve, exposure gain 1.35, his bottom glow band measured off all 13 of his portraits). Contrast and edge strength inside his range; p95 145 against his 160-211, limited by the red palette. Ships as `ui/portraits/faction_leaders/derpy_kharkadon.png`, replacing the Overseer stand-in; `leader_png()` in `gen_new_house_lords.py` would overwrite it, so that needs skipping for him. |
| Key rename `derpy_zharrduk` -> `derpy_kharkadon` | **Done, verified, in the Workshop folder** (lords pack `0d301c5d`, 18:00). Not uploaded, not seen in game. Section 6. |

The game, AssetEditor and RPFM were all running during the texture patch. Nothing was deployed to
`data/` by me, and the only pack written was the user's own re-save.

## 1. Faction flags

Asked: "extract the icon flags of overlords of zharrduk and uzkol mingol to ui/flags".

- `wh3_dlc23_chd_minor_faction` (Overlords): from CA's `ui.pack`. PNG bytes there are a `u32` length
  then a zstd frame.
- `cr_chd_skullstack` (Uzkul Mingol Company): from `!cr_immortal_empires_expanded.pack`, uncompressed.
- Each folder holds the usual six files: `mon_24`, `mon_64`, `mon_256`, `mon_icon`, `mon_rotated`
  (png) and `mon_banner.dds`. All twelve decode at the expected sizes. They are CA's and IEE's own
  files, unmodified.

## 2. The model drew pink in game and correct in AssetEditor

**Cause, measured: four base-colour DDS files had a legacy `DXT5` header, which cannot carry the sRGB
flag.** The engine reads them as linear, so dark crimson (80,10,10) comes out near (150,60,60).

| Texture | Was | Now (project folder) |
|---|---|---|
| `chd_immortal_hat_01_base_colour` | DXT5 legacy | `BC3_UNORM_SRGB` |
| `chd_immortal_head_01_base_colour` | DXT5 legacy | `BC3_UNORM_SRGB` |
| `chd_immortal_body_01_base_colour` | DXT5 legacy | `BC3_UNORM_SRGB` |
| `dwf_belegar_cape_01_base_colour` | DXT5 legacy | `BC3_UNORM_SRGB` |
| castellan body and head, lammasu accessories | `BC3_UNORM_SRGB` | untouched, and they drew correctly in the same screenshot |

- **Fix:** header only. FourCC set to `DX10`, the 20-byte block `(78, 3, 0, 1, 0)` inserted after byte
  128 (texconv writes the same block), pixels byte-identical (asserted). Files:
  `Modding Files/AssetEditor Projects/!!!derpy_chd_assets/variantmeshes/wh_variantmodels/hu3/chd/derpy_kharkadon/kharkadon_colors/`.
  Originals backed up in `Modding Files/Backup/kharkadon_dds_presrgb_20261006/`.
- **The patch script is not in `tools/`.** It was in the session scratchpad. If the fault recurs, it
  is about 30 lines: read the file, assert FourCC is `DXT5`, splice in the block, assert the pixels
  match, re-read.
- **Verified:** `texdiag info` reads all four as `BC3_UNORM_SRGB`; `texconv` decodes each to a normal
  image. **Confirmed in game afterwards** by the user's next screenshot (reds, not pink) once the
  pack was re-saved. Why AssetEditor looked right all along is still an inference (it most likely
  ignores the flag).
- Memory written: `wh3-legacy-dxt5-base-colour-is-linear-pink-in-game`.

## 3. Portraits

Asked: "create unit and character portraits for the character for me to approve". I read it as the
porthole (300x164, transparent) and the unit card (60x130, opaque). Folder:
`Modding Files/source/portraits/derpy_kharkadon/`.

**Drafts 1 and 2 (rejected).** Cut from the user's AssetEditor render (`render.png`, 2012x1728, real
alpha) and framed against CA's Overseer porthole and Astragoth's card. The user: "use the ones
currently in the hll mod as the basis, these are horrible examples." Our lords (Balur, Ghorth and the
rest in `Modding Files/pack/ui/portraits/`) are much tighter than CA's: helm fills the frame, hat
cut off at the top, horns and shoulders at the sides. A brightening step I added pushed the reds
pinker and was removed. The render is flatter than the in-game shots the HLL portraits come from.

**Draft 3 (ready for approval).** The user then sent an in-game screenshot ("how about this
image"), 886x972 with a desert backdrop, saved as `shot.png`. `derive.py` works from it:

- `py derive.py --prepare` crops the porthole window plus a 40px margin, upscales 2x and has Codex
  cut the background out (`gen_character_portrait.codex`, the accepted format of
  `docs/UNIT_CARDS.md` section 6) into `porthole_out.png`. About two minutes.
- `py derive.py` frames `porthole.png` from it and cuts `card.png` straight from `shot.png`, then
  writes `compare.png` beside Azeros and Snakebeard, the two HLL lords in the same tall black hat.
- Windows are `(centre x, top y, width)` in the screenshot's pixels: porthole `(445, 180, 480)`,
  card `(445, 200, 170)`. Codex returns the input's aspect at a larger size (here 1120x684 in,
  1605x980 out), so the framing maps back by ratio and needs no eye positions; Kharkadon has none.
- **The cut-out was checked against its input piece by piece** (all four horns, both crown spikes,
  emblem, grill, shoulder pads, braids, the axe skull: same places and counts, clean edges). Codex
  evened the light and left it slightly smoother and brighter.
- The card keeps the desert behind it, as the HLL cards keep their scenes.

**Draft 3 was judged "flat in all the images"; draft 4 is the current one.** Cause: the standard
cut-out prompt tells Codex to lift the shadows and use even studio light. `derive.py` now has its own
prompts (`DEPTH`): keep the screenshot's light direction and strengthen it, deeper shadow, brighter
highlights on metal, horn and trim, crisp edges, no chrome, rim light or effects, and the same ban on
adding or changing any piece. It is one Codex pass per picture, each run from the ORIGINAL crop (a
second pass over a flattened result would compound).

- Three pictures, three passes: `--prepare porthole` (cut-out and depth), `--prepare card` and
  `--prepare leader` (depth only, the desert stays). Run them as separate background jobs; the
  Codex runs take about two minutes each and can go in parallel. Windows in screenshot pixels:
  porthole `(445, 180, 480)`, card `(445, 200, 170)`, lord-select `(445, 190, 200)`.
- **Lord-select image** = `ui/portraits/faction_leaders/<sub>.png`, 85x115 opaque, the file
  `frontend_faction_leaders.character_image` names (`derpy_kharkadon` for Kharkadon since §6; the HLL pack
  currently ships the Overseer-based composite `leader_png()` builds). The recent HLL busts are tight
  in-game crops on their own scene; the older ones sit on CA's red-orange ground, and the orange band
  along the bottom of many is NOT a shared overlay (measured against Astragoth's: it differs
  everywhere), so none was added.
- **Final step `finish()`**, applied to all three: a luminance-only S curve (every channel scaled by
  one ratio so hue is kept) and a mild unsharp mask. Measured against the shipped HLL portholes
  (contrast std 47-59, p95 154-206, edge strength 44-61) and cards (std 45-71, p95 150-240, edge
  50-75): the Codex result alone was std 44 / edge 38 (porthole) and 43 / 43 (card), below the
  range; with `finish()` they are 50 / 45 and 51 / 52, inside it, saturation unchanged. The
  v1 version (even light) is kept in `v1_even_light/`.
- **Each Codex result was checked against its input piece by piece** (every horn, spike, stud, the
  emblem, the grill, braids with their rings, shoulder pads, the axe skull): same places and counts.
  **One thing it adds:** a fine surface grain (a faintly hammered look on the black cylinder,
  scratchier horn paint) the screenshot does not have. Shapes and counts are unchanged; the user
  should decide whether that is acceptable.

## 4. Do not re-derive

- Kharkadon = `wh3_dlc23_chd_minor_faction`; the Uzkul Mingol Company = `cr_chd_skullstack`.
- **The faction mask is not the cause of the pink.** CA's `*_mask.dds` for hat, head, body and cape
  cover 0% of R, G and B. Measured.
- A deployed pack's DDS entries are compressed (zstd behind a `u32` prefix); `read_pack_index.read`
  hands back the raw entry. Legacy `DXT5` has no DX10 block, so the format sits at byte 84.
- `Modpacks/!!!derpy_chd_assets.pack` holds no `kharkadon_colors` files; the Workshop copy (re-saved
  16:37 with the sRGB fix) is the live one.
- The two older copies of those four textures (`AssetEditor Projects/kharkadon/dds` and
  `source/lords/kharkadon`) are sRGB but have different pixels from the project folder's. Do not copy
  them over; the project folder holds the user's later edits.
- `tools/recolor_kharkadon.py` already asks texconv for sRGB; whatever rewrote the four files after its
  last run is unknown.
- Our lord cards are 60x130 opaque, CA's lord cards are 60x130 or 60x134 with some alpha. Our
  portholes are 300x164 with alpha. The faction-leader image is 85x115 opaque.
- Kharkadon's art set still points at CA's Overseer images through the cloned block in
  `portrait_settings_derpy_hll_new_lords.bin` (see `portrait_bin()` in `tools/gen_new_house_lords.py`).
  New portrait files need that block repointed, or they never draw.
- Git Bash `/tmp` paths mean nothing to Windows `texconv.exe` or `py`. A check that fails on a missing
  file there is a harness fault, not a bad file.
- Standing rules that bind this work: [[unit-cards-from-ingame-screenshots]] (the character's pixels
  come from a real render or screenshot, never generation; show before packing),
  `docs/UNIT_CARDS.md` section 6 (the accepted porthole format).

## 5. Still open

1. ~~Re-save the assets pack with the patched textures~~ Done by the user at 16:37 (section 0). If
   AssetEditor still holds the old bytes from before the patch, a later save from it would write the
   fault back; check `texdiag` on the four after any further save.
2. **Get the user's approval of draft 4** (porthole, card, lord-select image), then pack: decide the
   file stems, repoint the portrait settings block (its art set id is now `derpy_kharkadon`), add
   the porthole and card, and replace `ui/portraits/faction_leaders/derpy_kharkadon.png` (renamed
   from `derpy_zharrduk.png` in §6; generated by `leader_png()` in
   `tools/gen_new_house_lords.py`, which would overwrite it on its next run - change or skip that
   there too). A whole-hat porthole (smaller figure) is available if wanted.
3. The 85x115 lord-select image is made (`leader.png`, section 3), not packed.
4. **"Use the modern portraits by Partypus and delete the old ones" (17:30-17:41) is unresolved.** The
   user sent a screenshot of the frontend lord-select grid and asked where those portraits are: they
   are the HLL pack's `ui/portraits/faction_leaders/derpy_<lord>.png` (85x115). No separate Partypus
   set exists in any installed pack, `Backup/`, `Modpacks/` or the user's folders (searched all, by
   file name, by token and by image content; the HLL pack has only ever held one version of each file
   except Ghorth's porthole). The user then said the modern ones are "right there" in that folder and
   **"everything that's already in the pack should not be deleted"**, and asked "where are you getting
   the old portraits from". My list of "old" sets (Feb 2025 / Aug 2026 file dates, staged leftovers,
   CA placeholders) was a guess from file dates, not something the user said. **Nothing was deleted.**
   Working reading: the pack's current set is the modern Partypus one and is the style basis for
   Kharkadon's new portraits; the only stand-ins are `derpy_kharkadon.png` and `derpy_uzkul.png`
   (built from CA's Overseer by `leader_png()`), and the Overseer bin entries.
5. The two flag folders are extracted but unused; nothing yet points a faction at them.
6. **The rename breaks saves.** A campaign started before it holds a `derpy_zharrduk` character, his
   skills and his hellshard mission by the old keys; start a new one. His MCT switch is now
   `lord_derpy_kharkadon`, so a saved MCT value for him falls back to the default (on).
7. `gen_new_house_lords.py --import` would put Kharkadon's base stats back to the generator's
   (plate 90, 60/50, weapon 200/220) and flip one Uzkul weapon flag: the 10:57 buff was hand-made in
   the pack and never reached the generator (see the bodyguards handoff). Same before and after the
   rename; not fixed here.

## 6. The key rename: `derpy_zharrduk` -> `derpy_kharkadon`

Asked: "rename the data name to derpy_kharkadon instead of derpy_zharrduk, even in the db".

**Scope, measured by scanning every installed pack:** the key lives in one pack only, the lords pack
(Workshop `3432966208`): 121 files - 107 DB/loc fragments (31 of them NAMED after it, the
`derpy_zharrduk_bodyguards` set), 11 Lua files, 2 portrait settings bins, 1 PNG. Every key built on
it went with it (`derpy_kharkadon_bg_*`, `..._officer_*`, `_lord_trait`, skills, ancillaries, the
mission `wh3_dlc23_chd_ancestor_hellshard_structure_derpy_kharkadon`, the loc keys).
**Not renamed, on purpose:** the faction slug `zharrduk` (`derpy_toz_zharrduk`,
`derpy_ritual_chd_toz_annex_zharrduk`, `..._diplomacy_mod_zharrduk`, `suffix = "zharrduk"` in the
Tower Lua) names the house, not the lord, and so does every "Overlords of Zharrduk" string.
`derpy_kharkadon` already existed as the anim table key, the variantmesh filename and the assets
pack's folder; none of those is in a key column the rename writes, and no other pack has it in a DB
table.

**Tool: `tools/rename_data_key.py <pack> <old> <new> [--write]`** (new). Dry run by default. Exports
every DB/loc fragment as TSV, renames as text, imports back; Lua and xml byte-replaced; portrait
settings through `gen_portrait_settings.parse/dump` (length-prefixed strings, so no byte replace);
file names through RPFM's `rename_packed_files`. Stops on a binary it does not know. Before writing:
a duplicate-key check across EVERY fragment of each table (schema `is_key`; loc on its key column),
shown to fail on a duplicated DB table and a duplicated loc file. After writing, from a fresh
session: every fragment re-exports to exactly the renamed TSV (318), every other file is the
expected bytes (247), the old key is nowhere, and each file's raw count of the new key equals its old
count of old+new. Result: 0 bad.

- Backups: `Modding Files/Backup/pre_kharkadon_rename_20261006/{workshop,modpacks}/` (both `84cd84b3`),
  and `staged/` for every workspace file the rename edited.
- Lords pack now `0d301c5d`, copied to the Workshop folder after checking it still matched the
  backup. No copy in `data/`. Game was shut.
- Workspace renamed too (197 files edited, 32 renamed): the four generators that name him
  (`gen_new_house_lords.py`, `gen_kharkadon_bodyguards.py`, `gen_new_lords_cb.py`,
  `gen_hellshard_missions.py`), staged Lua under `Modding Files/pack/script/`, and the source TSV trees
  `hll_new_lords`, `kharkadon_bodyguards`, `new_lords_cb`, `hellshard_missions`, `zochaz/_pack`.
  Dated handoffs keep the old name.
- Checks after: `luac -p` on all 11 Lua files, `check_hll_settings.py` (27 settings, 0 failures),
  `check_skill_trees.py` (0 errors; its 38 warnings are the deliberate tier-4 downsides), the
  selftests of `gen_new_house_lords`, `gen_kharkadon_bodyguards` and `gen_hellshard_missions`, and
  `gen_new_lords_cb.py --check`. Regenerated: `gen_kharkadon_bodyguards` matches its renamed tree
  (one file, same rows, new order); `gen_new_house_lords` matches the renamed pack on 86 of 88
  fragments, the other two being item 7 above.
- **Bug found and fixed in `gen_new_house_lords.py`:** with `.skilltree_cache/extract` fresh, its
  `OWNED` regex matched the bodyguards rows, so `build()` wrote all 30 `*_bodyguards` fragments back
  EMPTY; an `--import` would have blanked them. It predates the rename (the old extract was older than
  the bodyguards). `build()` now skips any `_bodyguards` fragment. The 30 empty files were deleted;
  nothing was imported.
- `gen_hellshard_missions.py --check` re-rolls the random `id` column of two of its TSVs on every run;
  those two were put back to the renamed copies so the source tree matches the pack.
