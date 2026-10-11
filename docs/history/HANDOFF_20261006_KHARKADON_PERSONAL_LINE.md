# Kharkadon personal skill line: implemented

2026-10-06. User requested a revised personal line, added Perfect Vigour to Stand With Your Overlord, then approved implementation. Built and verified in Modpacks; local Workshop deployment is recorded below. No Workshop upload. Battle behavior has not yet been observed.

- [Design](../superpowers/specs/2026-10-06-kharkadon-personal-line-design.md): eight existing slots, elite infantry and personal combat, rank-24 exclusive choice, rank-29 active aura with +8 attack, +8 defence and temporary Perfect Vigour.
- [Implementation plan](../superpowers/plans/2026-10-06-kharkadon-personal-line.md): baseline preservation, skill bindings, aura, saved-pack and live checks.

## Findings from source and installed vanilla data

- `gen_new_house_lords.py` owns the skill definitions and clones Balur's surrounding records. Its `--import` covers much more than skills; review its whole manifest.
- The latest portrait/rename handoff records base-stat and Uzkul weapon-flag drift in that generator. Reconcile it against current saved packs before any import.
- `_bodyguards` fragments are explicitly excluded from the cloning loop after an earlier deletion bug. New personal ability fragments need similarly explicit ownership.
- `pack_pairs()` skips owned keys. New generated effects need binding-aware validation, not an exemption or an expectation that pack extraction will whitelist them.
- Native Morgrim's Eye is an active area augment: radius 35, cooldown 120, phase targets self and friends. Its native duration is 32; the planned clone changes it to 25.
- Perfect Vigour's phase attribute is `fatigue_immune`. Permanent unit-set attribute enabling additionally routes through `unit_set_unit_attribute_junctions`; the effect binding does not directly contain an `attribute` field.
- Installed `special_ability_to_auto_deactivate_flags` contains `out_of_melee`; the read of `special_ability_to_invalid_usage_flags` found no rows using that flag. Activation and phase cancellation require tracing and live verification, not a guessed usage flag.
- Personal damage effects on `additional_officer` bodyguards remain an implementation feasibility check. Do not silently make every bodyguard soldier receive Kharkadon's intended personal damage boosts.

## Implementation and verification

Source changed: `tools/gen_new_house_lords.py`. New processed-column/schema snapshot: `Modding Files/templates/kharkadon_personal_headers.json`, exported by RPFM from the installed WH3 versions. Generated output is the existing `Modding Files/source/hll_new_lords/` tree; `docs/HASHUT_LL_SKILL_LINES.xlsx` re-exported from the refreshed saved-pack extraction. The bodyguard generator and all 31 bodyguard fragments were left unchanged.

- Both original pack copies matched: MD5 `f37fd30cf3d02fe883954be1715d2043`, 567 files. Backups and before/after content manifests: `Modding Files/Backup/pre_kharkadon_personal_20261006/`. The mod manager's current game configuration includes the Workshop lords pack; the game was closed.
- Built pack MD5 `d44f0a9ae2470b13f3c5c93f70d067cb`, 583 files. Exactly 19 changed/new fragments: the three shared unique-skill skill/effect/loc fragments, 15 new DB fragments named `derpy_kharkadon_personal`, and one new loc fragment. All 564 other original files byte-identical; no deletions. Other lords' rows in the changed shared skill tables also identical.
- Reconciled generator drift with the measured saved pack: Kharkadon armour 130, attack 65, defence 60, shield 70; weapon 230/250, large splash, 10 attacks, splash multiplier 2, magical flag true. Uzkul's magical weapon flag remains false. Neither base fragment was imported because it already matched the baseline after source reconciliation.
- Imported only the reviewed 19-fragment subset through the existing generator importer. Fresh saved-file export: 19 matched, 0 mismatches. Initial verification caught only float formatting (`25.0` versus RPFM's `25.0000`); generation now uses RPFM's four-decimal form, and readback passed.
- New custom sets: melee infantry (11 memberships), Infernal Guard family (8), Ironsworn/Immortals plus all four bodyguards (6). Warriors bodyguards get the explicitly requested all-bodyguard buffs, not Infernal Guard upkeep/XP. AP damage uses `wh_main_effect_character_stat_weapon_strength_ap_damage_mult`, not the flat AP damage effect.
- Aura cloned from Morgrim's Eye: 35 metres, 25 seconds, 120-second recharge, self/friends only, +8 attack/+8 defence and `fatigue_immune`. Both invalid-usage and auto-deactivation junctions use the native defined `out_of_melee` flag. Native flag definition confirmed; no invented usage key. Native icon inspected, 8,737 bytes, not a placeholder. Aura ID `1047410657` persisted and distinct in vanilla and this pack. The baseline already has two unrelated rows sharing ID `13354598`; those were preserved.
- `gen_new_house_lords.py --selftest`: passes, including 17 new deliberately broken personal-line cases. `gen_kharkadon_bodyguards.py --selftest`: passes, 14 breaks caught.
- `check_skill_trees.py`: 0 ERR, 39 WARN. The previous 38 warnings become 39 because Rule by the Axe deliberately penalizes both hobgoblins and labourers. The former replenishment penalty is removed.
- `check_effect_signs.py <pack> derpy_kharkadon`: only the new +15 upkeep, -8 hobgoblin leadership, -8 labourer leadership, and preserved faction -10 labourer leadership; no missing effect rows.
- Schema reference checker (`check_live_references.check`) run on the 19 imported fragments against installed vanilla plus the whole saved pack: 0 missing references. Fresh `.skilltree_cache/extract`: generator reproduces all 104 output fragments with no row differences. No duplication or blanking of the new personal fragments on regeneration.

### Local deployment

Deployed to `F:/SteamLibrary/steamapps/workshop/content/1142710/3432966208/!aa_derpy_hashut_legendary_lords.pack` with the game closed. The destination was still byte-identical to its backup before copying; after copying it is byte-identical to Modpacks, MD5 `d44f0a9ae2470b13f3c5c93f70d067cb`. No extra `data/` copy and no upload. Independent read-only review found no concrete defects and independently confirmed exact pack preservation; it identifies the same live-test gaps below.

### Outstanding live checks

The game was not running. The native database and references establish valid wiring, not runtime outcomes. Test the capstone unlearned/learned in solo and all four bodyguard forms; activation in melee, cancellation on leaving melee, 35-metre targeting, duration/recharge and temporary Perfect Vigour expiration. Check native character-scoped personal damage and Terror on the embedded officer; no whole-regiment damage substitute was added. Permanent Perfect Vigour, recruit rank, XP and the rank-24 exclusive choices also need a live look. Do not describe these as observed until tested.
