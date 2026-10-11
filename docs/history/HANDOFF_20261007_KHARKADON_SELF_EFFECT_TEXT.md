# Kharkadon's self effects name him

2026-10-07. Asked (with a screenshot of Chosen of Zharrduk, level 3): "why is there double
effects?" Each pair was one bonus on Kharkadon and one on his regular troops, added on 10-06
(`HANDOFF_20261006_KHARKADON_SELF_BUFFS.md`). CA's character effects carry no name ("Upkeep: -15%"),
so the skill read as if it listed the same bonus twice. User chose option 1: keep both, and make
the self line say whose it is.

**Built in `Modding Files/Modpacks/` (md5 `3e475841`), deployed to the Workshop folder 18:32 with the
game shut (md5 equal; no `data/` copy).**
Not uploaded and not seen in game. The published build is still `442e09c7` (the 17:25 upload);
backup of it: `Modding Files/Backup/pre_kharkadon_self_text_20261007/`.

## What changed

Seven new effects, `derpy_kharkadon_self_<x>` (`SELF_EFFECTS` in `tools/gen_new_house_lords.py`).
Each is the native effect's `effects` row cloned under the new key, plus every bonus-value binding
the native has, so it behaves exactly as the native did. Only the tooltip text differs.

| Key | Native donor | Bound through | Text |
|---|---|---|---|
| `_charge` | `wh_main_effect_character_stat_charge_bonus_pct` | ids_unit_sets `charge_bonus` / `all_units` | Charge bonus: %+n% (Kharkadon) |
| `_xp` | `wh3_main_effect_character_campaign_experience_mod` | scripted `value` / `experience_mod` | Experience gain: %+n% (Kharkadon) |
| `_upkeep` | `wh_main_effect_force_all_campaign_upkeep` | ids_unit_sets `upkeep_mod` / `all_units` | Upkeep: %+n% (Kharkadon) |
| `_defence` | `wh_main_effect_character_stat_melee_defence` | ids_unit_sets `melee_defence_mod` | Melee defence: %+n (Kharkadon) |
| `_armour` | `wh_main_effect_character_stat_armour` | ids_unit_sets `armour_mod` | Armour: %+n (Kharkadon) |
| `_vigour` | `wh2_dlc10_effect_attribute_enable_perfect_vigour` | unit_attribute `enable` / `fatigue_immune` | Perfect Vigour (Kharkadon) |
| `_resistance` | `wh_main_effect_character_stat_physical_resistance` | ids_unit_sets `unit_damage_resistance_physical_mod` | Physical resistance: %+n% (Kharkadon) |

They replace the native key wherever a self line has a troop twin: skills `_1`, `_2_1`, `_2_2`,
`_4_1`, the lord trait skill (upkeep and experience; their troop twins are in the faction effects)
and the Blood and Iron set (armour). Self-only lines with no twin (melee attack on `_1`, everything
on `_2_3` and `_4_2`, the item stats) stay on CA's effects. Values and scopes are unchanged.

The upkeep worry raised earlier does not hold: `force_all_campaign_upkeep` binds `upkeep_mod` on
`all_units`, so at `character_to_character_own` it reaches his own unit.

## Pack

Eight entries, and nothing else, against `442e09c7`: the two new tables
`effect_bonus_value_scripted_junctions` and `effect_bonus_value_unit_attribute_junctions` (fragment
`derpy_kharkadon_personal`, both version 0; their RPFM headers were added to
`Modding Files/templates/kharkadon_personal_headers.json`), and changes to `effects`,
`effect_bonus_value_ids_unit_sets`, the `derpy_kharkadon_personal` loc, the unique skills and lord
trait effect junctions, and the set effects. These were imported as a reviewed subset of the
generator's plan. The generator reproduced the old source byte for byte before the edit (with a
fresh extract of `442e09c7`). The saved pack was re-read: 8 of 8 fragments match.

## Checks

- `check_kharkadon_personal` checks each self effect: its definition, that its bindings equal the
  donor's in all three binding tables, and that its text matches and names him. `expected_fx` uses
  the new keys. The selftest asserts that the lord trait grants no nameless native effect.
- Seven mutants were caught: a missing scripted binding, a missing attribute binding, upkeep on the
  wrong bonus value, a missing definition, text without his name, skill `_2_1` back on the native
  key, and the set back on the native key. The selftest still passes, with its 10 item and 17
  personal-line mutants. `check_skill_trees.py` reports 0 ERR and 40 WARN, the same as before.

## In game, first test

Kharkadon's skill tree: Chosen of Zharrduk should read "Upkeep: -15% (Kharkadon)" above "Upkeep:
-15% for Infernal Guard, Ironsworn and Immortals". Check that his upkeep in the army panel drops
when the skill is taken.
