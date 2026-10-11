# Skill-tree audit — Hashut's Legendary Lords

Read out of `!aa_derpy_hashut_legendary_lords.pack`, 2026-08-21. Checked against vanilla via
RPFM's dependency database. Rerun with `py check_skill_trees.py`.

**13 lords, 140 skills, 178 nodes, 156 links, 662 set memberships.**

Findings **1–5 and 8 are fixed and deployed** — the pack was rebuilt, re-read from disk,
re-audited, and copied to the Workshop folder. Backups: `*.pack.bak_skillfix_20260821` in both
`Modding Files/Modpacks/` and the Workshop folder, holding the pre-fix state. The Steam upload
itself is still yours to do.

Not bugs: **9** is intended — Bzaark is an unstable lord, the miscast penalty is his character.
Left alone: **6** and **7** (cosmetic). Still open: **10** and **11** (need eyes in a campaign,
not a table query).

## Table layout, for reference

`character_skill_nodes.indent` is the **lane** (the horizontal row in the panel);
`.tier` is the **slot along that lane**. Both mods and CA leave gaps in either — 502 of
vanilla's 547 node sets have tier gaps and 376 have indent gaps, so a gap is never itself
a fault.

The lanes this mod uses:

| lane (indent) | content |
|---|---|
| 0 | the lord's personal row — shared character skills, ancillary skills, mentor, mounts |
| 1 | the lord's six unique skills (`derpy_<lord>_1` → four `_2_x` → `_3`) |
| 2 | `derpy_shared_combat_*` |
| 3 | CA's `wh3_dlc23_…_sorcerer_prophet_fire_combat_*`, used instead of lane 2 by five lords |
| 4 | `derpy_shared_army_*` |
| 5 | `derpy_shared_campaign_*` |
| 6 / 99 | CA's high-slot and hidden nodes |

Ghorth and Gargath are built almost entirely on CA's Drazhoath and Sorcerer Prophet trees
(47–48 vanilla nodes each) rather than the `derpy_shared_*` lanes. That is a design choice,
not an inconsistency.

---

# Part 1 — structure

## Fixed

### 1. Mentor sat on two nodes at once — Tordrek, Gordak, Warrhak   fixed

`wh3_main_skill_all_mentor_lord` was reachable twice in those three trees: via the mod's
`derpy_shared_mentor` (lane 0, slot 11) and via CA's `wh3_dlc24_skill_node_all_mentor_lord`
(lane 0, slot 30). One skill, two nodes, one tree.

`derpy_shared_mentor` was in only 3 of the 13 sets and all 3 also carried CA's node, so no lord
depended on it. Removed the three set-item rows and the now-unowned node.

### 2. Abnagg had no Mentor node at all   fixed

He was the only one of 13 without `wh3_dlc24_skill_node_all_mentor_lord`; 309 of vanilla's 315
lord trees carry it. Added. All 13 now have it.

### 3. Gargath and Abnagg had no agent-action scaling   fixed

`wh3_main_agent_action_scaling` — the hidden node (lane 99, `visible_in_ui = false`) carrying
`wh3_main_skill_agent_action_success_scaling` — is in 307 of vanilla's 315 lord trees and was
in 11 of the mod's 13. Without it those two lords' hero-action success did not scale with
level. Added. All 13 now have it.

### 4. `wh3_main_agent_action_scaling_derpy_ghorth` was in no node set   fixed

A mod-authored clone of the node above, at lane 44 slot 0, `visible_in_ui = false`, belonging
to no set, so it never loaded. Ghorth already gets the vanilla node. Row deleted.

### 5. The army lane's capstone gate was looser than the other two lanes   fixed

| capstone | parents | `required_num_parents` |
|---|---|---|
| `derpy_shared_combat_4` | 4 SUBSET_REQUIRED | 4 |
| `derpy_shared_campaign_4` | 4 SUBSET_REQUIRED | 4 |
| `derpy_shared_army_4` | 4 SUBSET_REQUIRED | **1 → 4** |

The three lanes are otherwise built identically (`_0` → a fan of `_1_x` → an all-of gate `_2`
 a fan of `_3_x` → an all-of gate `_4`), and `derpy_shared_army_2` correctly requires all 6.
The army capstone (`wh_main_skill_chs_lord_battle_stand_or_die`) now needs all four
prerequisites like its siblings. That is a balance change as much as a bug fix — revert it if
the cheap capstone was deliberate.

## Left alone

### 6. Mount nodes land in two different places

| lord | mount nodes | lane | slots |
|---|---|---|---|
| ghorth | bale taurus, great taurus, lammasu | 0 | 31, 32, 33 |
| gargath | bale taurus, great taurus, lammasu | 0 | 31, 32, 33 |
| urzkhal | great taurus, lammasu | 0 | **1, 2** |
| gordak | giant wolf | 0 | **1** |
| abnagg | great taurus, lammasu | 0 | **1, 2** |

Both work — vanilla mount nodes sit at low slots far more often than high ones, and neither
placement collides with anything. Only the reading order of the panel differs. Cosmetic.

### 7. Two misspelt key families, spelt wrong consistently

- Urzkhal's six unique nodes and skills are `derpy_urzhkal_*` (h/k swapped) while his node
  set, ancillary skills and mount skills are `derpy_urzkhal_*`.
- Warrhak's second-slot node is `derpy_warrhakk_2_2` (double k) among five `derpy_warrhak_*`.

Wrong in **every** table that references them — nodes, skills, links, set items and loc — so
they work today. They are a trap for the next edit: a Global Search for `derpy_urzkhal` misses
half his tree. Renaming means touching six tables plus the `.loc`.

---

# Part 2 — the unique line (lane 1)

Every lord has the same six-skill shape: `derpy_<lord>_1` at slot 0, four `_2_x` at slots 1–4,
`derpy_<lord>_3` at slot 5. The links are a fan, not a chain — all four `_2_x` hang off `_1`,
and `_3` requires **all four** `_2_x` (link type REQUIRED, `required_num_parents = 0`, which
means all). Rank gates are identical across all 13 lords: 4 / 11 / 11 / 19 / 19 / 29.

That is internally consistent and matches CA's own capstone pattern. Note the fan reads as a
chain in the panel because the four middle nodes occupy consecutive slots, but since the
capstone needs all four it makes no difference to play.

## Active abilities — all 16 wired correctly

Sixteen of the 78 unique skills grant a battle ability. The full chain was traced for each:

    skill → character_skill_level_to_effects_junctions
           effect_bonus_value_unit_ability_junctions (enable)
           unit_abilities (requires_effect_enabling = true)
           unit_special_abilities → phases / projectile_bombardments
           land_units_to_unit_abilites_junctions (on the lord's own unit, and his mounts)

All sixteen resolve end to end. `derpy_abnagg_3_active_vortex` and
`derpy_tordrek_2_4_active_vortex` have no `special_ability_phases` junction where the other
bombardments do — that is **not** a fault: 116 of vanilla's 124 `wh_type_bombardment`
abilities have no phase junction either.

Distribution, for reference: Balur and Warrhak have no active ability anywhere in their line;
Tordrek has one at `_2_4` but not on his capstone. Nine of thirteen capstones grant an active,
four are pure passives. Design choice, not a fault.

## 8. Snakebeard's "Master Artificer" made artillery slower to recruit   fixed

`derpy_snakebeard_1` applied `derpy_chd_snakebeard_recruit_time_artillery` at **+2**. That
custom effect binds to `global_recruit_time_mod` over the `wh3_dlc23_chd_all_artillery` unit
set, and its loc reads *"Recruitment Time +%+n for Artillery Trains"* — so the skill was adding
two turns to every artillery recruit. The effect row also carried
`is_positive_value_good = true`, so the panel painted that +2 green, and
`category = battle` on a recruitment effect.

Three edits, taking the "Master Artificer" name and the −10% recruit cost on the same skill as
the intent:

| field | was | now | why |
|---|---|---|---|
| junction value | `2.0000` | `-2.0000` | two turns faster, not slower |
| `is_positive_value_good` | `true` | `false` | 32 of vanilla's 33 `global_recruit_time_mod` effects are `false` |
| `category` | `battle` | `campaign` | all 33 vanilla ones are `campaign` |

If the slow-but-cheap trade-off was actually deliberate, put the value back to `+2` — the flag
and category are correct either way.

## 9. Bzaark's "Madman's Insight" — not a bug, by design

`derpy_bzaark_2_3` grants one effect, `wh2_main_effect_force_stat_miscast` at **+20**, which
vanilla flags `is_positive_value_good = false`. It reads as a pure penalty to a checker, and it
is meant to: Bzaark is an unstable lord and the miscast risk is his character, the same way his
accuracy penalties are (`−10` on `_1`, `−5` on `2_2`, offset by `+10` on `2_4`). **Left as-is.**

`check_skill_trees.py` will keep reporting this row, along with the accuracy pair and Warrhak's
diplomacy. Four expected warnings, not four faults.

One thing that is still worth a look: the scope is `general_to_force_own`, so the miscast risk
lands on the whole army's casters, not on Bzaark. Vanilla only ever uses this effect at
`character_to_character_regionwide_local_region`. If the drawback is meant to be *his*, the
scope is the field to change, not the value. See finding 10.

## 10. Effects used at a scope vanilla never pairs them with

A one-off pass compared every `(effect_key, effect_scope)` pair in the unique line against
every pair vanilla uses in `character_skill_level_to_effects_junctions`. 32 pairs have no
vanilla precedent. Most are harmless — a force-target scope swapped for another force-target
scope, or `character_to_character_own` where vanilla uses `character_to_character_own_armytext`
(same target, different tooltip wording).

These five are worth eyeballing in game, because vanilla's usage is **entirely** a different
target kind:

| skill | effect | used at | vanilla only ever uses |
|---|---|---|---|
| `derpy_ghorth_1` (+10), `derpy_gargath_2_4` (+15) | `wh3_main_effect_winds_of_magic_pool_cap` | `character_to_character_own` | seven scopes, all force or faction target |
| `derpy_abnagg_2_2` (+25) | `wh_main_effect_force_all_campaign_raid_income` | `character_to_character_own` | force targets |
| `derpy_abnagg_2_4` (+30) | `wh_main_effect_force_army_campaign_siege_attack_attrition` | `character_to_character_own` | `general_to_force_enemy_regionwide` — i.e. applied to the **enemy** |
| `derpy_azeros_1`, `derpy_urzhkal_1` | `wh3_dlc23_pooled_resource_chd_raw_material_efficiency` / `…_armaments_modifier` | `character_to_faction_unseen` | `character_to_province_own`, `faction_to_province_own_factionwide` |
| `derpy_bzaark_2_3` (+20, deliberate) | `wh2_main_effect_force_stat_miscast` | `general_to_force_own` | `character_to_character_regionwide_local_region` |

Winds of Magic is the one I would check first: there is no per-character winds pool, so
Ghorth's and Gargath's signature magic bonus may simply not apply. The siege-attrition one is
the clearest logical inversion — it is written as a buff on your own lord using an effect CA
only ever points at the defender.

Note this check is a heuristic, not proof. `effects_tables` carries no scope constraint, and
the pack's own `effect_bonus_value_ids_unit_sets` bindings do not settle it either, so these
need a five-minute look in a campaign rather than another table query.

## 11. `derpy_chd_balur_ironsworn_wep_dmg` on a Ghorth skill

`derpy_ghorth_2_3` "Infernal Enforcers" applies a Balur-named effect. It is deliberate reuse —
the effect buffs `wh3_dlc23_chd_infernal_ironsworn`, which is exactly what that skill is about,
and the skill also raises the Ironsworn and Infernal Guard caps. Only the key name is
misleading.

---

# What was checked and found clean

- **References** — every node key, skill key, effect key (15,152 known), effect scope (435),
  ancillary (2,720) and agent subtype (626) resolves against vanilla or the pack.
- **Reachability** — no node has all its parents outside its own set; no node's
  `required_num_parents` exceeds the parents actually present.
- **Link direction** — every link advances to a higher slot in the lane.
- **Grid** — no two nodes share a (lane, slot) cell in any of the 13 trees.
- **Duplicate skills** — after the fix, no skill sits on two nodes inside one tree.
- **Duplicate definitions** — no skill or node is defined twice across DB fragments.
- **Localisation** — 140 skills, 140 name entries, 140 description entries. Complete,
  including the two misspelt families.
- **Skill payloads** — every skill grants at least one effect or one ancillary.
- **Effect value signs** — every value checked against the effect's `is_positive_value_good`.
  Four remain, all deliberate flavour: Bzaark's `−10` / `−5` accuracy and `+20` miscast, and
  Warrhak's `−50` diplomacy with Dwarfs.
- **Active abilities** — all 16 chains complete, lord unit and mounts included.
- **Node sets** — one set per agent subtype, all 13 subtypes exist.

# Three false alarms, so they do not get re-reported

- **Tier/indent gaps are normal.** See the layout note above.
- **`character_skills.unlocked_at_rank = 0` is normal.** 4,908 of vanilla's 5,944 skills leave
  it at 0; the real rank gate is `character_skill_level_details.unlocked_at_rank` and
  `character_skills_to_level_reached_criterias.character_level`. Only 2,006 vanilla skills have
  a level_details row at all, so its absence is not a fault either.
- **A bombardment ability with no `special_ability_phases` junction is normal.** 116 of
  vanilla's 124 are wired that way.
