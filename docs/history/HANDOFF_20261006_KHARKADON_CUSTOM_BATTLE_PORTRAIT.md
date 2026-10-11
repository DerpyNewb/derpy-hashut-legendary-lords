# Kharkadon's custom-battle portrait references

2026-10-06. User supplied a custom-battle lord-selector screenshot showing CA's Overseer art for Kharkadon. Fixed and locally deployed, not uploaded. The changed selector has not yet been observed in game.

## Cause and fix

The approved `ui/portraits/portholes/no_culture/derpy_kharkadon.png` and `ui/portraits/units/no_culture/derpy_kharkadon.png` were already in the pack, byte-identical to the maintained approved portrait sources. Both portrait-settings bins already had the correct `derpy_kharkadon` group and variant, pointing at his own art. The problem was the explicit custom-battle overrides still pointing at `chd_overseer_campaign_01_0.png`:

- Solo `units_custom_battle_permissions.general_portrait` (one row).
- All four bodyguard `units_custom_battle_permissions.general_portrait` rows, copied from the solo donor.
- `battle_set_piece_armies_characters.portrait` for `derpy_kharkadon` (one row).

These six fields now point to `ui/portraits/portholes/no_culture/derpy_kharkadon.png`, the same convention as the other custom legendary lords. No new/replaced images, portrait-settings edits or unit-card aliases were needed.

## Maintained source

- `tools/gen_new_house_lords.py`: new shared `custom_battle_portrait(subtype)` selects a lord's own approved portrait when its `LORDS` entry has `portraits`; the Captain's previous fallback remains unchanged. The custom-battle permission transform uses it.
- `tools/gen_new_lords_cb.py`: character rows use the same helper; the checker rejects a stale portrait. Its stale comment about never rerunning the main generator was replaced with the actual fragment ownership rule.
- `tools/gen_kharkadon_bodyguards.py`: corrects the donor's portrait through the helper before cloning permissions, so a stale saved donor cannot reproduce the bug. Checker and selftest include portrait regression.

Generated outputs: `Modding Files/source/hll_new_lords/`, `Modding Files/source/new_lords_cb/`, and the permissions TSV in `Modding Files/source/kharkadon_bodyguards/`. CB orchestration used the freshly exported `.skilltree_cache/extract` rather than the older `zochaz/_pack` snapshot. Do not confuse those extraction caches with maintained source or enable a loose staging folder as if it were a complete pack.

## Verification and deployment

- Backups: `Modding Files/Backup/pre_kharkadon_cb_portrait_20261006/`. Both starting packs MD5 `0e776d9c1682617dc228f9c93f355855`.
- New pack MD5 `ec70571ef615e9a11af4df2841447d89`, 583 files. Exactly three DB fragments changed: `units_custom_battle_permissions/derpy_chd_ll`, `units_custom_battle_permissions/derpy_kharkadon_bodyguards`, and `battle_set_piece_armies_characters/derpy_hll_new_lords_cb`. Per-row comparisons show exactly the six portrait fields above changed; all other columns and row counts identical. All 580 other original files byte-identical, including every portrait/card/settings bin and all items, skills, models and stats.
- Only those three reviewed fragments imported through RPFM. Fresh saved-file export: 3 matched, 0 differences. Direct decoder reads all five permission rows and the one character row pointing to his packed PNG; both settings bins checked for the correct own-art group and variant.
- Main-generator regression failed on the old portrait before fixing the transform, then passed. `gen_new_house_lords.py --selftest`: passes (existing 10 item and 17 personal mutants retained). `gen_kharkadon_bodyguards.py --selftest`: passes, 15 breaks including stale portrait. `gen_new_lords_cb.py --check`: passes, and its old-portrait mutant is rejected.
- Skill-tree audit remains 0 errors / 39 intentional warnings. Independent read-only review confirmed the six-field diff and found no concrete defects.
- Deployed with the game closed to `F:/SteamLibrary/steamapps/workshop/content/1142710/3432966208/!aa_derpy_hashut_legendary_lords.pack`. The Workshop copy still matched its backup before copying; after copying it is byte-identical to Modpacks, MD5 above. No duplicate data-folder copy and no upload.

Remaining check: reopen custom battles and inspect the selector, selected army card and in-battle portrait for the solo lord and each bodyguard option. Saved-reference verification establishes the corrected wiring; no fresh in-game screenshot was taken.
