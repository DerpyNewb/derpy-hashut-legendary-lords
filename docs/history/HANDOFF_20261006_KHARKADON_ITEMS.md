# Kharkadon's blood-infused axe and shield

2026-10-06. User asked to redo his items around an axe infused with Hashut's blood and to check saved screenshots. After inspecting the images, the user explicitly chose the visible shield instead of a talisman. Implemented and locally deployed; not uploaded. **The initial numbers below were superseded by the Unique-tier rebalance below. Later lore-text correction: current build `0e776d9c`.**

## Screenshot and design basis

Inspected `Modding Files/source/portraits/derpy_kharkadon/shot.png` (in-game: broad red-and-black axe and heavy shield) and `render.png` (AssetEditor: glowing armour plates). Screenshot appearance does not establish magical effects; the blood infusion is the user's design instruction.

| Item | Unlock | New effects |
|---|---:|---|
| Axe of Hashut's Blood | Rank 15 | +25% armour-piercing weapon damage, +8 melee attack, flaming attacks and magical attacks. |
| Shield of the Bloodsworn | Rank 10 | +10 melee defence, 8% ward save, 20% fire resistance. Occupies the armour slot. |
| Blood and Iron (both equipped) | Set | +10 armour for Ironsworn, Immortals and all four Kharkadon bodyguard forms; +5 army leadership. |

Removed the inherited Balur weapon's +20% weapon strength, +10 bonus versus infantry and Frenzy; removed the talisman's two 15% resistance effects. Replaced the set's +10% personal weapon strength and +3 Infernal Guard cap with the stated army benefits. Base weapon damage and magical flag remain unchanged.

The internal shield key remains `derpy_kharkadon_talisman`, preserving grants, prerequisites, set membership and the rank-10 skill. Its ancillary `type` is now `wh_main_anc_armour`, `category` is `armour`, and its skill icon is `item_armour.png`, matching vanilla shield slot conventions. Weapon and set keys remain `derpy_kharkadon_weapon` and `derpy_kharkadon_set`.

## Source and pack ownership

- Maintained source: `tools/gen_new_house_lords.py`, with `ITEMS`, `ITEM_EFFECTS`, `ITEM_SET_EFFECTS`, `SET_NAME`, the ancillary/skill transformations, and the existing selftest. Uzkul retains its inherited effects and its own names.
- Generated outputs: `Modding Files/source/hll_new_lords/`. Six fragments changed: `db/ancillaries_tables/derpy_chd_ll_ancillary`, `db/ancillary_to_effects_tables/derpy_chd_ll_ancillary`, `db/ancillary_set_effect_junctions_tables/derpy_chd_ll_ancillary`, `db/character_skills_tables/derpy_chd_ll_anc`, `text/derpy_chd_ll_ancillary.loc`, `text/derpy_chd_ll_ancillary_set.loc`.
- Destination: `Modding Files/Modpacks/!aa_derpy_hashut_legendary_lords.pack`.
- Enabled local copy: `F:/SteamLibrary/steamapps/workshop/content/1142710/3432966208/!aa_derpy_hashut_legendary_lords.pack`.
- Backups, import list and before/after content manifests: `Modding Files/Backup/pre_kharkadon_items_20261006/`. Both starting packs MD5 `d44f0a9ae2470b13f3c5c93f70d067cb`.

## Fresh verification

- Saved pack MD5 `7fbf4132edde58de4856b3ba4f86bdb2`, 583 files. Six existing fragments changed, no files added/deleted; 577 original files byte-identical. Decoded differences in shared fragments belong only to Kharkadon. His personal line, bodyguards, base stats, portraits and all other lords are preserved.
- All selected native character effects have the exact `character_to_character_own` precedent. AP damage uses the percentage effect `wh_main_effect_character_stat_weapon_strength_ap_damage_mult`, not the flat AP-damage effect. The set reuses the verified personal elite-armour binding and `general_to_force_own` army scope.
- RPFM selected WH3, opened the pack and confirmed schema loaded. Only the reviewed six-fragment subset was imported. Fresh saved-file export matched all six, zero differences.
- Schema foreign-reference checker on the changed DB fragments against installed vanilla and the complete saved pack: zero missing references. Native armour skill icon exists.
- Refreshed saved-pack extraction matches every generated fragment. `gen_new_house_lords.py --selftest` passes: three new item mutants (wrong equipment type, disabled flaming effect, wrong set scope) and the previous 17 personal-line mutants are caught.
- Skill-tree audit: 0 errors, 39 intentional warnings, unchanged from the personal-line build.
- Independent read-only review found no concrete defects; it independently checked slot fields against native shields, ranks, set bindings and saved-pack preservation.
- Game closed at deployment. Workshop destination still matched its backup before copying; after copying, it is byte-identical to Modpacks with MD5 `7fbf4132edde58de4856b3ba4f86bdb2`. No duplicate `data/` copy and no upload.

## Remaining live checks

Equip/unequip the shield in the armour slot, including a post-rename save that previously equipped the talisman. Verify the rank-10/rank-15 grants and that Blood and Iron applies only while both items are equipped. Check magical/flaming attacks and personal item stats on the solo lord and embedded officer; the `additional_officer` inheritance question from the personal-line handoff is still unmeasured. No regiment-wide damage replacement or custom battle ability was introduced.

Previous subsystem record: [personal skill line](HANDOFF_20261006_KHARKADON_PERSONAL_LINE.md).

## Unique-tier rebalance (later 2026-10-06; current)

User: "effects are too weak, base it on unique tier ancillery and check other legendary items". Read the actual saved `derpy_chd_house_ancillaries.pack`, the saved lords pack, the installed vanilla `db.pack`, and the rarity contract in `tools/gen_house_ancillaries.py`. The house system's Unique rung is uniqueness score 200, three substantive stat effects plus an active ability. Kharkadon's existing items already have score 200 and `legendary_item=true`; the previous small stat-only packages did not match that rung's design.

### Benchmarks measured from saved records

| Item | Permanent effects relevant to the comparison | Active |
|---|---|---|
| Khorakk's Bull-Crowned Axe (house Unique) | +30% weapon strength, +15 melee attack, +18 versus infantry | Tithe of Blood |
| Black Dwarf's Scourge (house Unique) | +25% weapon strength, +20 melee attack, +15 versus infantry | Oathbreaker's Due |
| Khorakk's Last Accounting (house Unique armour) | +25 armour, 15% physical resistance, +12 melee defence | Anvil Stance |
| Baal's Founder's Skin (house Unique armour) | 20% spell resistance, +18 armour, 12% ward save | Unyielding Guard |
| Grimgor's Gitsnik (vanilla) | +6 melee attack, +12 versus large, magical attacks and campaign effects | +24 melee attack and +50% base/AP damage, 33 seconds, 120-second recharge |
| Black Hammer of Hashut (vanilla) | +15% weapon strength and +1 control | +50% base/AP damage, 32 seconds, 120-second recharge |
| Armour of Gazrakh (vanilla) | +20 armour, +10 melee defence | 30% ward save, 48 seconds, 120-second recharge |

Also checked Ghal Maraz, Axe of Dargo and the mod's Ghorth, Balur, Gargath, Vraznak, Black Dwarf and Azeros items. The basis is the stronger house Unique rung and the native active-ability patterns; this does not claim every legendary item has identical numerical power. The native Black Hammer phase also has a Flammable contact grant: it was explicitly removed from Kharkadon's clone to keep the implemented effects and tooltip aligned.

### Current equipment contract

| Item | Permanent effects | Active |
|---|---|---|
| Axe of Hashut's Blood | +35% weapon strength, +15 melee attack, +15 versus infantry, magical and flaming attacks | **Hashut's Blood:** +50% base/AP weapon damage and +20 melee attack, self only, 32 seconds, 120-second recharge, unlimited uses |
| Shield of the Bloodsworn | +20 melee defence, 15% ward save, 40% fire resistance | **Bloodsworn Bulwark:** self and allies within 35 metres gain 20% ward save and +15 melee defence, 25 seconds, 120-second recharge, unlimited uses |

Blood and Iron remains +10 armour for Ironsworn/Immortals/all four bodyguards and +5 army leadership. Rank-10/rank-15 unlocks, item/set keys and the shield's armour slot are preserved. New abilities are independent of the rank-29 personal capstone and are enabled by equipping the appropriate item.

`tools/gen_new_house_lords.py` owns `ITEM_ABILITIES` alongside the existing item stats. Native donors: Black Hammer for the axe's self augment, Morgrim's Eye for the shield's area augment. Existing RPFM-processed headers are reused. All ability/effect/phase/stat/enable/loc rows are emitted into the generator's `derpy_kharkadon_personal` fragments; that fragment name now covers both his capstone and these item abilities. No dependency on the separate house-ancillaries pack, and no battle Lua. Ability IDs `1863434659` and `894899759` are persisted and unique in installed vanilla and the lords pack. Existing native icons were extracted and visually inspected (8,768 and 9,208 bytes, not placeholders).

### Rebalance evidence and deployment

- Backups and content/import manifests: `Modding Files/Backup/pre_kharkadon_unique_20261006/`. Both starting packs were `7fbf4132edde58de4856b3ba4f86bdb2`.
- Saved and locally deployed current pack: MD5 `7b69057553538eafb23a650c09c01800`, 583 files. Exactly nine existing fragments changed; 574 original files byte-identical, no additions/deletions. Old personal-line aura records, all other-lord rows and every bodyguard/base-stat/model/portrait fragment are preserved.
- Nine reviewed fragments imported: `ancillary_to_effects/derpy_chd_ll_ancillary`, plus the personal `effects`, `unit_abilities`, `unit_special_abilities`, `special_ability_phases`, phase junctions, phase stat effects, ability enable bindings and loc fragments. Saved-file re-export: 9 matched, 0 differences.
- Foreign-reference check on new/changed rows against installed vanilla and the saved pack: 0 missing references. Fresh saved-pack extraction reproduces every generated output; repeated builds do not accumulate or erase abilities.
- `gen_new_house_lords.py --selftest` passes: 10 item mutants and the earlier 17 personal-line mutants caught. It checks the exact damage multipliers versus flat increases, both target routings, phase durations, radius, cooldown, item enable links, ID collisions and absence of unlisted contact effects.
- Read-only review caught the donor's inherited Flammable contact grant before import. Added a failing test, cleared `imbue_contact`, then proved reintroducing it is caught. Follow-up review verified the fix and found no remaining concrete blockers.
- Skill-tree audit remains 0 errors / 39 intentional warnings. Game closed at deployment; Workshop copy still matched its backup before copying, and afterwards matched Modpacks byte-for-byte. No duplicate data-folder copy and no Workshop upload.

Still owed in game: equip/unequip gating of both active abilities, self-only axe targeting, shield radius and no enemy targets, expiration and recharge, shield migration in an existing save, and personal effects/ability availability on the embedded officer in all four bodyguard forms. Offline validation does not establish those runtime outcomes.

## Lore descriptions (later 2026-10-06; current)

User supplied an in-game Bloodsworn Bulwark tooltip showing the ability and rejected the flavour paragraph repeating its numerical effects. **Ability flavour descriptions must be lore; the engine's stat/target/range/duration/cooldown lines already explain the mechanics.** The screenshot confirms this ability's tooltip appeared in game, not that every outstanding runtime check above passed.

Changed `ITEM_ABILITIES[*].tip` for both item abilities and the capstone's skill/ability description in `tools/gen_new_house_lords.py`:

- **Bloodsworn Bulwark:** "The names of fallen Bloodsworn are hammered into the shield's black iron. Their oaths outlast their flesh, and Kharkadon calls upon them when the line buckles."
- **Hashut's Blood:** "Hashut's blood boils within the axe-head. Every kill stokes its heat; the edge leaves blackened armour and flesh fused together."
- **Stand With Your Overlord:** "Kharkadon takes his place in the first rank. The Bloodsworn close around their master; those who abandon him will answer to his axe."

Generated and imported only `text/derpy_kharkadon_personal.loc` and `text/derpy_chd_ll_unique_skills.loc`; four strings changed. Saved-file readback: both fragments matched, zero differences. Every DB file and the other 581 original files are byte-identical. No effects, targeting, duration or cooldown changes. Backups: `Modding Files/Backup/pre_kharkadon_lore_20261006/`. Deployed with the game closed to the same Workshop location; Modpacks and Workshop byte-identical, MD5 `0e776d9c1682617dc228f9c93f355855`. No upload.
