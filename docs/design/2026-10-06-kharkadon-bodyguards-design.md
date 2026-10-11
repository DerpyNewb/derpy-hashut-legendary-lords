# Kharkadon's bodyguard options - design

2026-10-06. Pack: `!aa_derpy_hashut_legendary_lords.pack` (Workshop `3432966208`). Research and the
reasons behind each choice: `docs/sessions/HANDOFF_20261006_KHARKADON_BODYGUARDS_DESIGN.md`.

**Status: built and deployed to the Workshop folder the same day (`tools/gen_kharkadon_bodyguards.py`),
not yet seen in game.** Where the build differs from the first draft of this spec, the text below
is the as-built version.

## 1. Intent

`derpy_zharrduk` (Kharkadon, leader of the Overlords of Zharrduk) gets four swappable options that
replace his solo battle unit with a Chaos Dwarf infantry unit he leads as an extra officer. They are
unlocked by skills at levels 8, 15, 25 and 32 and equipped like his other mount-category ancillaries.
Each option has half the men of its base unit and twice the health per man. Kharkadon inside the
unit has half the health of his solo form. His solo form is unchanged.

Success: in a campaign battle with an option equipped, the army's first unit is 50 bodyguards plus
Kharkadon on his own mesh and animations; the health numbers in section 3 hold; unequipping
returns the solo lord; the other thirteen lords' mounts and every existing Kharkadon row are
untouched.

Out of scope: new meshes or animations, new bonuses beyond section 5, recruitment of the clones,
custom-battle availability beyond what the mount fragments already ship, Workshop upload.

## 2. Options

Key `derpy_zharrduk_bg_<option>`, used as the land unit, main unit, ancillary, skill, skill node and
skill effect key (the mount fragments do the same).

| Option | Base land unit | Unlock rank | Node tier |
|---|---|---|---|
| `warriors` | `wh3_dlc23_chd_inf_chaos_dwarf_warriors` | 8 | 22 |
| `infernal_guard` | `wh3_dlc23_chd_inf_infernal_guard` | 15 | 23 |
| `ironsworn` | `wh3_dlc23_chd_inf_infernal_ironsworn` | 25 | 24 |
| `immortals` | `wh3_dlc23_chd_inf_infernal_ironsworn_ror` ("The Immortals") | 32 | 25 |

Nodes sit in `derpy_zharrduk_skills` at indent 0, no parents, beside his talisman (tier 20) and
weapon (tier 21). The rank is `character_skill_level_details.unlocked_at_rank`; the
`character_skills.unlocked_at_rank` cell stays 0, as on every existing mount skill. Tiers stay at
or under 48. Each skill is learned free at its rank by a `character_skills_to_level_reached_criterias` row, as every
other mount in the pack is (added 2026-10-08; the first build left it out and the nodes cost a point).

## 3. Numbers

Every value derives from the base row in CA's `db.pack`; the generator reads it, nothing is typed.

| Option | Men (base -> clone) | Per-man HP (entity 8 + bonus) | Clone `bonus_hit_points` |
|---|---|---|---|
| warriors | 100 -> 50 | 82 -> 164 | 156 |
| infernal_guard | 100 -> 50 | 90 -> 180 | 172 |
| ironsworn | 100 -> 50 | 106 -> 212 | 204 |
| immortals | 100 -> 50 | 106 -> 212 | 204 |

Rule: `clone_bonus = 2 * (entity_hit_points + base_bonus) - entity_hit_points`; `num_men = base / 2`.

**Per-man stats stay the base's**: melee attack, melee defence, armour, morale, charge bonus, shield,
weapon, spacing, `rank_depth`, animations, attribute group, abilities. They do not depend on the man
count. The clone's damage output is therefore about half the base unit's with the same total health,
which is the intended price of the option: a tough guard around a lord who does the killing. The
generator takes one `DAMAGE_SCALE` setting per option, default 1.0; any other value needs cloned
`melee_weapons` rows and is not built unless asked.

**Changed on the clone beyond HP and men**: `class = com` (the character's unit), the key, and
`melee_cp` at half the base's (autoresolve and AI strength; a tuning value, not measured).

## 4. Kharkadon inside the unit

- One `battle_entities` row per option, `derpy_zharrduk_officer_<option>`, cloned from
  `wh3_dlc23_chd_cha_overseer` (CA's row, shared, so it is not edited). His solo total is entity 8 +
  `bonus_hit_points` 6200 = 6208, so the officer's total is 3104. The clone's `bonus_hit_points`
  is assumed to stack onto officers, so `hit_points` is 3104 minus it: 2948, 2932, 2900, 2900. The
  assumption is the one flag `STACKS_BONUS` in the generator (open question 1).
- One `battle_personalities` row per option, `derpy_zharrduk_officer_<option>`:
  `man_animations_table = derpy_kharkadon`, `variant` = his existing `derpy_zharrduk` battle variant
  (mesh `derpy_kharkadon`, scale 1.15), that option's entity, and one shared `battle_entity_stats`
  row `derpy_zharrduk_officer` giving his weapon `derpy_zharrduk`.
- One `land_units_to_battle_personalities_junctions` row per option: `attach = additional_officer`,
  `land_unit = derpy_zharrduk_bg_<option>`, `engine_articulation_index = -1`, `jettison_rider =
  false`. The unit keeps its own officer; he is the second.
- His melee attack, defence and armour inside the unit are expected to be the unit's, not his solo
  65 / 60 / plate 130, because the stat rows hang off the land unit. His entity health and his own
  weapon are the levers; verify (open question 2).

## 5. Tables, in the new fragment `derpy_zharrduk_bodyguards`

Follows the Zochaz and `derpy_chd_ll_mounts` fragments. Four rows each unless noted.

| Group | Tables |
|---|---|
| Unit | `land_units`, `main_units` (`caste = lord`, cost and upkeep as his solo row), `land_units_to_unit_abilites_junctions` (his abilities minus the single-entity passive, plus the base's own), `unit_variants` (the base's variant, card `placeholder` as every lord), `unit_set_to_unit_junctions` (his two sets plus the base's, minus `mp_cap_*` and `wh2_main_ror_units_all`), `ui_unit_bullet_point_unit_overrides` (his plus the base's), `unit_banner_unit_height_offsets`, `units_custom_battle_permissions` (his row), `units_custom_battle_mounts`, `units_to_groupings_military_permissions`, `unit_attributes_groups` and `unit_attributes_to_groups_junctions` (the base's attributes plus his `encourages`, on a new group per option) |
| Officer | `battle_entities` (4), `battle_entity_stats` (1), `battle_personalities` (4), `land_units_to_battle_personalities_junctions` (4) |
| Item | `ancillaries` (`category = mount`, `provided_bodyguard_unit` = the land unit, `applies_to = .`, `precedence 1`, `uniqueness_score 1`, `turns_before_swap_allowed 0`), `ancillary_types` (new type row each, `ui_icon` path), `ancillaries_required_skills`, `ancillaries_included_agent_subtypes` (`derpy_zharrduk`), `ancillary_to_included_agents` (`general`) |
| Skill | `character_skills`, `character_skill_nodes`, `character_skill_node_set_items`, `character_skill_level_details`, `character_skill_level_to_ancillaries_junctions`, `character_skills_to_level_reached_criterias`, `character_skill_level_to_effects_junctions`, `character_skill_utilization_hints_junctions`, `effects` |
| Text | one `.loc`: unit names, ancillary and skill names and descriptions, effect text. Plain player words, lore-flavoured. |

**Effects**: only the dummy per-skill effect the mount skills carry (scope
`character_to_character_own`, value 1). No new bonuses. Anything else the player should get from an
equipped option is named by the user and added as `ancillary_to_effects` rows.

**Not shipped**: `mounts`, `campaign_mounts`, `campaign_mount_animation_set_overrides`,
`agent_uniforms`, `campaign_character_art_sets`. A bodyguard changes the battle unit only; his map
model stays his own. If the game refuses a `mount`-category ancillary with no `campaign_mounts` row,
the fix is a copied row with no visible mount (open question 3).

**Not shipped, on purpose**: no `cdir_military_generator_unit_qualities` row, so the AI's army
generator can never pick a clone as a commander.

**Icons** (superseded 2026-10-08: both now CA's generic armour slot art, `ui/skins/default/equipment_items_armour.png`; the unit icon read as low quality): first build points each `ancillary_types.ui_icon` at the base unit's CA icon
(`ui/units/icons/<base>.png`) and every skill `image_path` at CA's
`wh3_dlc29_hero_passive_sworn_bodyguard.png`. Whether a unit icon reads well in the mount slot is
unchecked; own art is a later step (Codex, per the standing preference).

## 6. Build and checks

- New `tools/gen_kharkadon_bodyguards.py`, same shape as `gen_new_house_lords.py`: reads base rows
  with `read_vanilla_db`, writes TSVs to `Modding Files/source/kharkadon_bodyguards/`, `--check`
  validates without writing, `--selftest` breaks each rule in memory and confirms it is caught,
  `--import` pushes into the lords pack in place.
- Before saving: duplicate-key check across the whole pack; every key in the junctions resolves;
  the numbers in section 3 recomputed from the base rows and compared.
- After saving: re-open the saved pack in a fresh session and export every new table back, counting
  rows (the `import_tsv` success message proves nothing). Diff every other fragment against a fresh
  extract so nothing else changed, as the model session had to.
- Back up the Workshop copy to `Modding Files/Backup/` first, then deploy to the Workshop folder
  and, with the game shut, to `data/`. Not uploaded.
- Game test through the wh3 MCP bridge, **Warriors first, the other three only after it passes**.
  One Lua error in `wh3_eval` wedges the bridge, so read-only probes.

## 7. Open questions, each answered by the Warriors test

1. Does the clone's `bonus_hit_points` also apply to the officer entity? Read Kharkadon's real HP;
   the fix is one `hit_points` cell.
2. Does the commander-class unit accept `additional_officer` as the general's entity, and do his
   stats come from the unit row? Read his stat card; if he is weak, campaign effects on the
   ancillary can lift the whole unit.
3. Does a `mount`-category ancillary with no mount row equip and draw on the campaign map?
4. Does `additional_officer` take one of the 50 places or add one? Count the bodyguards.
5. Does swapping between options and back to the solo lord work mid-campaign without a save issue?
