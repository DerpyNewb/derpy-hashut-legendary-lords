# Kharkadon self buffs instead of explicit bodyguard targets

2026-10-06. User showed the skill tooltip's affected-unit list and objected to explicitly listing all bodyguard ancillaries: "you can just buff self". Implemented and locally deployed, not uploaded; tooltip and mounted self-effect behavior need a fresh in-game check.

## Decision and implementation

Retained bonuses for the regular Infernal Guard/Ironsworn troops and moved Kharkadon's corresponding benefits to native `character_to_character_own` effects. A scope choice was offered; execution proceeded with the stated default of retaining regular troop bonuses. The bodyguard options themselves remain available.

- `personal_targets()` now contains only native regular troop records: melee infantry 7, Infernal Guard family 5, Ironsworn/Immortals 2. Removed all 11 explicit `derpy_kharkadon_bg_*` memberships across those three custom sets. The four bodyguard ancillary/unit definitions and their existing native set inheritance were not edited.
- First into the Breach adds self +10% charge bonus alongside its existing self attack and regular infantry charge bonuses.
- Chosen of Zharrduk keeps the regular troop upkeep/XP ladder and adds self upkeep -5/-10/-15% and native character experience +10/+20/+30%. Character experience uses `wh3_main_effect_character_campaign_experience_mod`, rather than treating the general as a rank-and-file unit.
- Plate and Oath keeps regular Ironsworn/Immortals armour/defence and adds the matching self +5/+10/+15 armour and +3/+6/+9 defence.
- The Immortal Few keeps regular elite Perfect Vigour/physical resistance and adds self Perfect Vigour, +10% physical resistance and +15% self upkeep. Its regular Infernal Guard-family upkeep penalty remains.
- The lord trait adds self -25% upkeep and +30% character experience to replace the former explicit bodyguard-family inclusion in the faction benefits. The faction bundle's nine rows are unchanged.
- Blood and Iron adds self +10 armour alongside the regular Ironsworn/Immortals armour and army leadership effects.
- Four custom effect descriptions now name only Ironsworn/Immortals and no longer say "Kharkadon's bodyguard". Ability flavour lore, ability behavior, equipment stats, portraits and custom-battle references are preserved.

These self counterparts also apply to the solo character; this is intentional following the request to buff Kharkadon himself. Native character scopes replace explicit variant enumeration; officer/mounted runtime application was not measured in this change.

## Ownership and verification

Source: `tools/gen_new_house_lords.py`; output: `Modding Files/source/hll_new_lords/`. New self effects reuse actual native keys and verified native character scopes; no new effects, scripts or conditional checks per bodyguard form.

Backups: `Modding Files/Backup/pre_kharkadon_self_buffs_20261006/`; both starting packs `815f90d92f442213e8005f396f73d90e`.

Exactly five reviewed fragments changed:

1. `character_skill_level_to_effects_junctions/derpy_chd_ll_unique_skills`: 16 added self-effect rows.
2. `character_skill_level_to_effects_junctions/derpy_chd_ll_trait`: 2 added self-effect rows.
3. `ancillary_set_effect_junctions/derpy_chd_ll_ancillary`: 1 added self-armour row.
4. `unit_set_to_unit_junctions/derpy_kharkadon_personal`: 11 removed explicit bodyguard memberships.
5. `text/derpy_kharkadon_personal.loc`: 4 descriptions revised.

Fresh saved-file export matched all five generated fragments, zero differences. Direct decoder confirmed 14 regular-unit memberships and no bodyguard records in the custom sets. All 578 other original files byte-identical, including the faction bundle, every bodyguard fragment, images/settings, models and all other lords' data; no files added/deleted, 583 files total.

The new no-bodyguard-enumeration assertion failed against the old generated sets and passed after cleanup. Existing exact skill and set-effect contracts now include the self counterparts; the missing-target mutant checks a regular Infernal Guard record instead of an intentionally removed bodyguard. Generator selftest passes (10 item and 17 personal mutants), bodyguard selftest passes (15 breaks), and fresh extraction reproduces all outputs. Skill-tree audit: 0 errors / 40 intentional warnings; one extra warning is the matching +15 self-upkeep drawback on The Immortal Few. Independent read-only review found no concrete defects and confirmed ordinary troop targets, native self bindings and unchanged faction/bodyguard data.

Current Modpacks and Workshop copies: MD5 `dd23116d65990ad510fc6acdd1d64da5`. Deployed with the game closed to `F:/SteamLibrary/steamapps/workshop/content/1142710/3432966208/!aa_derpy_hashut_legendary_lords.pack`, after confirming the destination still matched its backup. Destination bytes match Modpacks. No duplicate data-folder copy and no upload.

This supersedes explicit-bodyguard targeting in the earlier [personal-line design](../superpowers/specs/2026-10-06-kharkadon-personal-line-design.md), [item](HANDOFF_20261006_KHARKADON_ITEMS.md), and [faction](HANDOFF_20261006_KHARKADON_FACTION_EFFECTS.md) records. Live checks: affected-unit tooltip no longer enumerates the four bodyguard variants; self modifiers on solo and each equipped guard form; existing regular troop bonuses still apply once.
