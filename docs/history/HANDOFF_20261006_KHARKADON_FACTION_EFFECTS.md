# Kharkadon faction effects: Immortal Legions and Old Blood

2026-10-06. User requested faction-effect choices, chose a mix of Immortal Legions and Old Blood for a veteran Immortal overlord, then approved labourer and hobgoblin drawbacks. Implemented, verified and locally deployed after the user closed the game. No upload or live campaign test.

## Approved package

| Faction effect | Value |
|---|---:|
| Infernal Ironsworn unit capacity | +3 |
| Infernal Guard, Ironsworn and Immortals upkeep | -25% |
| Lord and hero recruit rank | +4 |
| Infernal Guard, Ironsworn and Immortals experience gain | +30% |
| Armaments production | +15% |
| Labourer troop leadership, all armies | -10 |
| Hobgoblin troop leadership, all armies | -10 |
| Hobgoblin upkeep (later addition) | +25% |
| Hobgoblin recruitment cost (later addition) | +25% |

The initial drawback was troop leadership. The user later requested higher hobgoblin upkeep and recruitment costs; both are now +25%, with the existing leadership penalties retained. The bonuses and drawbacks are factionwide. Faction name, lord effects, personal skills, items, starting armies and custom-battle portraits remain unchanged.

Upkeep and experience reuse the generator's existing `derpy_kharkadon_personal_guard` family bindings. These include all native Infernal Guard variants, ordinary Ironsworn, the Immortals RoR and the three matching elite bodyguard forms; the Warriors bodyguard is excluded. The production modifier is CA's `wh3_dlc23_pooled_resource_chd_armaments_modifier`, wired through `effect_bonus_value_pooled_resource_factor_junctions` as `percentage_multiplier_mod` on `wh3_dlc23_chd_armaments_produced`. This specifically boosts production, clarifying the proposal's broader wording "armaments gained".

## Source and validation

- Source: `tools/gen_new_house_lords.py`, `TRAIT_BUNDLE["derpy_kharkadon"]`; generated output: `Modding Files/source/hll_new_lords/db/effect_bundles_to_effects_junctions_tables/derpy_chd_ll_traits.tsv`.
- Kept `derpy_kharkadon_lord_trait`, its existing faction/start-script/frontend connections and `start_turn_completed` stage. Capacity uses the native additive Hell-Forge key, recruit rank uses the existing combined lord/hero key. Upkeep -25 is a discount, verified against the donor effect's `is_positive_value_good=false`.
- Added one assertion in the existing selftest for the exact seven assembled effect/value/scope triples. It failed against the old four-effect package, then passed after replacement. Updated the existing starting-army cap mutant: five Ironsworn now exceed the faction's four-unit starting limit; the former three-unit mutant became legal after the approved capacity increase. Actual starting armies were not edited.
- Generator selftest passes, retaining 10 item and 17 personal-line mutants. Fresh extraction reproduces every generated fragment. Skill-tree audit: 0 errors / 39 intentional warnings. Sign report: only the existing personal-line penalties and the approved two faction leadership penalties; no missing effect definitions.

## Saved pack and deployment

Backups: `Modding Files/Backup/pre_kharkadon_faction_20261006/`. Both original packs were MD5 `ec70571ef615e9a11af4df2841447d89`.

Imported only `db/effect_bundles_to_effects_junctions_tables/derpy_chd_ll_traits`. Fresh saved-file export matched the generated fragment, zero differences. Direct decoder confirmed all seven effects, exact scopes and values, and every other faction bundle row unchanged. All 582 other original files byte-identical, no added/deleted files; 583 files total.

Current Modpacks and enabled Workshop copies: MD5 `4f831fd5ffeb570d6341763180049825`. The game started during validation; the deployment guard caught it before any Workshop copy occurred. The user chose to close the game, and both the WH3 status tool and a process check confirmed it had exited. Deployed to `F:/SteamLibrary/steamapps/workshop/content/1142710/3432966208/!aa_derpy_hashut_legendary_lords.pack` after confirming the destination still matched its backup; the saved destination is byte-identical to Modpacks with the hash above. No duplicate data-folder copy and no upload.

Still owed in game: lord-select faction-effect display, Hell-Forge capacity, discounts/XP across the elite family, new recruit ranks, per-turn production and leadership in armies. Existing personal-army bonuses stack with these faction bonuses; native runtime behavior was not measured in this change.

## Hobgoblin cost penalties (later 2026-10-06; current)

User: "you can add upkeep and recruitment cost for hobgoblin higher as well". Added +25% to both, using native `wh3_dlc23_effect_upkeep_chd_hobgoblin` (`upkeep_mod`) and `wh3_dlc23_effect_force_recruit_cost_chd_hobgoblins` (`cost_mod`), each at `faction_to_force_own_unseen`. Both bindings target `wh3_dlc23_chd_hobgoblin_units` exclusively; these cost penalties do not extend to labourers. Both effect definitions have `is_positive_value_good=false`, so +25 increases costs as intended.

Expanded the existing assembled-bundle assertion to nine exact effects: it failed before the two additions and passed afterwards. Generator selftest passes; the saved fragment re-export matched, with no differences. Direct saved-pack comparison proves exactly two effect rows added, every pre-existing row retained and 582 other original files byte-identical. Sign check identifies both +25 costs as penalties alongside the existing leadership/personal-line penalties. Skill-tree audit remains 0 errors / 39 intentional warnings; fresh extraction matches all generator outputs.

Backups: `Modding Files/Backup/pre_kharkadon_hobgoblin_costs_20261006/`; baseline `4f831fd5ffeb570d6341763180049825`. Only the same faction-bundle fragment was imported. Current Modpacks and enabled Workshop copies: MD5 `815f90d92f442213e8005f396f73d90e`, 583 files. Deployed with the game closed after verifying the Workshop destination still matched its backup. No duplicate data-folder copy or upload. Hobgoblin recruitment prices/upkeep still need a live check.
