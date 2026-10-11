# Kharkadon's bodyguard options: built and deployed, not yet seen in game

2026-10-06. Research and design in sections 1-4 below; the build is section 0. Pack the work would land in: `!aa_derpy_hashut_legendary_lords.pack` (Workshop
`3432966208`). Asked: "add a mount option for kharkadon, but not as mounts but as unit body
guards", the officer of a Chaos Dwarf Warriors (shields) unit at level 8, Infernal Guard at 15,
Ironsworn at 25 and Immortals at 32, half the men and twice the health of the base unit, and
Kharkadon at half his solo health as a single entity.

Spec: `docs/superpowers/specs/2026-10-06-kharkadon-bodyguards-design.md` (as-built).

**Corrected 2026-10-08: the original build left out `character_skills_to_level_reached_criterias`**, the
table that learns a mount's skill free at its rank. Every other mount and item in the pack has a row there
(fragment `derpy_chd_ll_anc`), so the bodyguards cost a skill point while every other lord's mount was free.
Fixed in `gen_kharkadon_bodyguards.py` (one row per option, rank 8/15/25/32, `upgrade_to_skill_level 1`) and
shipped as `f050f8e2`, together with CA's generic armour icon (`ui/skins/default/equipment_items_armour.png`)
in place of the unit card on `ancillary_types` and `units_custom_battle_mounts`. No script.

## 0. What was built, deployed and verified

**Deployed to the Workshop folder, not uploaded, not seen in game.** The game was closed. The
wh3 MCP bridge tools were not loaded in this session, so no in-game check was possible.

| Pack | md5 now | Backup of what it replaced |
|---|---|---|
| lords pack, Workshop `3432966208` and `Modding Files/Modpacks/` | `84cd84b3` (565 files: the old 534 plus 31 new) | `Modding Files/Backup/pre_kharkadon_bodyguards_20261006/{workshop,modpacks}/` (`99881d11` and `a055b90f`) |

- **Base was the Workshop copy, not `Modpacks/`.** The Workshop copy was newer (10:57 that morning):
  Kharkadon buffed to plate 130 / attack 65 / defence 60 / shield 70 / weapon 230 and 250, an Uzkul
  weapon flag, a set-piece row. Diffed per file by content (3 fragments differed, nothing else),
  backed up both, synced `Modpacks/` from the Workshop copy, built there, copied back.
- **New tool `tools/gen_kharkadon_bodyguards.py`** (`--fetch-headers`, build + checks, `--import`,
  `--selftest`). Reads CA's `db.pack` and the lords pack, writes TSVs to
  `Modding Files/source/kharkadon_bodyguards/` (`headers.json` there is RPFM's own column order, fetched
  once), imports in place. 31 files: 30 DB fragments named `derpy_zharrduk_bodyguards` plus
  `text/derpy_zharrduk_bodyguards.loc` (44 keys).
- **Verified three ways.** `--import` re-opens the saved pack fresh and compares every fragment
  with what was built (31 matched); the same run hashed all 534 other files before and after (none
  changed); a second decoder (`read_vanilla_db`) read the saved pack back: 190 DB rows, 50 men and
  bonus hit points 156 / 172 / 204 / 204, officer entities 2948 / 2932 / 2900 / 2900, Kharkadon's own
  unit unchanged (6200, attack 65, plate 130). The selftest breaks 14 rules and each is caught.
- **No panel cell collision**: his nodes at tier 22-25, indent 0, beside talisman 20 and weapon 21.
- **What the build chose beyond the spec's first draft**: one officer entity and personality per
  option (so each option's officer total is exactly 3104 if the clone's bonus stacks); the clone's
  attribute group is the base's attributes plus his `encourages`; the clone's unit sets are his two
  plus the base's minus `mp_cap_*` and `wh2_main_ror_units_all`; his abilities carry over minus the
  single-entity passive; no `cdir_military_generator_unit_qualities` row.

### Corrections found the hard way (build)

- **The first tier check could not fail.** It compared the generator's own input to 48, not the
  built node row; the selftest's break "tier 49" was not caught. Fixed to read the built row.
  A selftest that breaks the rows is what found it.
- **`call()` in `import_house_ancillaries.py` has no `quiet` argument**; `rpfm_client.call` does.
- **The Immortals' base unit sits in `wh2_main_ror_units_all` and an `exclude` row of
  `all_units_rank_0_to_3`**; copying the base's sets verbatim made the lord's unit a Regiment of
  Renown. Filtered by `NOT_SETS`.
- **The in-game text read "50 The Immortals"**: the per-option `plural` field fixes it.
- **Vanilla and the lords pack agree on every table version** used here, so the generator takes
  the vanilla version for a new fragment.

### Open after the build (all answered by loading a campaign with Kharkadon at rank 8)

The five spec section 7 questions, plus: does the unit icon read well as a mount-slot icon, and
does an `anc_set_exclusive_chaos_dwarfs` faction-set donor row (copied from Ghorth's mount) let
Kharkadon's house equip it. If the officer's health does not stack with the clone's bonus, set
`STACKS_BONUS = False`, regenerate and re-import. Re-running `--import` is safe: it deletes and
recreates only its own 31 paths and checks the rest is untouched.

## Research and design (before the build)

The design was presented in chat; the user said "continue" with stats left as the base's, then
"implement now".

## 1. What was settled with the user

- Classified architectural (four new land units plus an ancillary and skill chain), so the path is
  design approval, then a written spec, then a plan.
- Health question answered "officer entity only": Kharkadon's solo unit stays exactly as it is;
  only the new officer entity he uses inside the bodyguard units carries half his solo health.
- "The Immortals" is CA's RoR `wh3_dlc23_chd_inf_infernal_ironsworn_ror` (display name "The
  Immortals (Infernal Ironsworn)"); no unit in vanilla or any installed Chorf mod is called
  Immortals otherwise.

## 2. The design as presented

One clone chain per option, keys `derpy_zharrduk_bg_warriors`, `_bg_infernal_guard`,
`_bg_ironsworn`, `_bg_immortals`, the same key on the land unit, main unit, ancillary, skill,
node and effect (the mounts do the same). New fragment `derpy_zharrduk_bodyguards` in the lords
pack, built by a new `tools/gen_kharkadon_bodyguards.py`.

| Option | Base land unit | Unlock rank | Men | Per-man HP now (entity 8 + bonus) | Doubled | `bonus_hit_points` |
|---|---|---|---|---|---|---|
| Warriors | `wh3_dlc23_chd_inf_chaos_dwarf_warriors` | 8 | 100 -> 50 | 82 | 164 | 156 |
| Infernal Guard | `wh3_dlc23_chd_inf_infernal_guard` | 15 | 100 -> 50 | 90 | 180 | 172 |
| Ironsworn | `wh3_dlc23_chd_inf_infernal_ironsworn` | 25 | 100 -> 50 | 106 | 212 | 204 |
| Immortals | `wh3_dlc23_chd_inf_infernal_ironsworn_ror` | 32 | 100 -> 50 | 106 | 212 | 204 |

Kharkadon's officer: new `battle_entities` row cloned from CA's `wh3_dlc23_chd_cha_overseer`
(entity hit_points 8; his lord unit adds `bonus_hit_points` 6200, solo total 6208), set so his
total is 3104. New `battle_personalities` row on his `derpy_kharkadon` mesh and anim bin, then
one `land_units_to_battle_personalities_junctions` row per unit with `attach = additional_officer`.

Unlock chain: four skill nodes in `derpy_zharrduk_skills` beside the talisman (tier 20) and
weapon (tier 21) nodes, no parents, granting the ancillary through
`character_skill_level_to_ancillaries_junctions`, and learned free at the rank through
`character_skills_to_level_reached_criterias` (added 2026-10-08).

## 3. Corrections found the hard way

- **There is no officers table in WH3.** `land_units_officers_tables` (v4) is in RPFM's
  `schema_wh3.ron`, but `db.pack` ships no such path. Officers are `battle_personalities` rows
  attached through `land_units_to_battle_personalities_junctions.attach`.
- **`additional_officer` is real but not vanilla.** CA's 1,507 junction rows use only
  `autonomous_rider` (1,466) and `officer` (41); `battle_personalities_attach_types` has no rows in
  `db.pack`. `additional_officer` appears in `derpy_dwf_polearms` (the spears mod),
  `derpy_hashuts_polearm`, `derpy_chd_units`, `derpy_units_bzaark`, `derpy_units_snakebeard`,
  `derpy_units_fist_of_hashut`, `derpy_units_vraznak` and `!scm_legendary`. It keeps the unit's own
  officer and adds a second. `derpy_hashuts_polearm` applies it to the same Chaos Dwarf Warriors
  and Infernal Guard, pointing `battle_entity` at `wh3_dlc23_chd_cha_sorcerer_prophet` and
  `battle_entity_stats` at an empty string.
- **Vanilla CHD infantry have no junction rows at all**, so their standard officer comes from
  the variant mesh, not from the DB.
- **`ancillaries.provided_bodyguard_unit` is the mount mechanism.** It names the land unit that
  replaces the lord's own battle unit while the ancillary is equipped. The engine's own word for
  the lord's unit is "bodyguard" (`general_bodyguard_size_mod` is the lord hit-points effect).
- **The level gate is `character_skill_level_details_tables.unlocked_at_rank`**, not
  `character_skills_tables.unlocked_at_rank`, which is 0 on every mount and ancillary skill. Ghorth's
  great taurus is rank 9 on tier 32, his talisman rank 10 and weapon rank 15.
- **What makes a mount free is `character_skills_to_level_reached_criterias`** (`character_skill`,
  `character_level`, `upgrade_to_skill_level`): it learns the skill on reaching the level without a
  point. The rank gate alone only unlocks the node for purchase. Missed in this build; see the note at the top.
- **A lord whose unit has many entities is supported.** `main_units` rows with `caste = lord` and
  `num_men > 1`: Ikit Claw and the Warlock Master at 25, the Vampire coven thrones at 17, the
  user's own `derpy_chd_mount_tank_prophet_*` at 13. None is an infantry bodyguard, so that exact
  shape is still untested.
- **The RPFM MCP tools were not loaded in this session** although the server answered 200 on
  `127.0.0.1:45127`; no `mcp__rpfm__*` tool existed. All reading used `tools/read_vanilla_db.py`
  and `tools/read_pack_index.py`.
- **`read_pack_index.py <pack> <substring>` crashes on a non-ASCII dump** under cp1252; set
  `PYTHONIOENCODING=utf-8`.

## 4. Do not re-derive

- Mount chain tables (lords pack, fragments `derpy_chd_ll_mounts` and `derpy_zochaz`):
  `ancillaries`, `ancillaries_required_skills`, `ancillaries_included_agent_subtypes`,
  `ancillary_to_included_agents` (agent `general`), `character_skills`,
  `character_skill_nodes`, `character_skill_node_set_items`, `character_skill_level_details`,
  `character_skill_level_to_ancillaries_junctions`, `character_skills_to_level_reached_criterias`
  (the free learn at the rank - its rows for the mounts live in fragment `derpy_chd_ll_anc`),
  `character_skill_level_to_effects_junctions`
  (a dummy effect named like the skill, scope `character_to_character_own`, value 1),
  `character_skill_utilization_hints_junctions`, `effects`, `land_units`, `main_units`,
  `land_units_to_unit_abilites_junctions`, `ui_unit_bullet_point_unit_overrides`,
  `unit_banner_unit_height_offsets`, `unit_set_to_unit_junctions`,
  `units_custom_battle_mounts`, `units_custom_battle_permissions`, `campaign_mounts`.
- Kharkadon today: land unit `derpy_zharrduk` in fragment `derpy_chd_ll_base`, man_entity
  `wh3_dlc23_chd_cha_overseer`, `man_animation = derpy_kharkadon`, `class = com`,
  `bonus_hit_points 6200`, melee attack 65, defence 60, plate 130, morale 90, weapon
  `derpy_zharrduk`; main unit `derpy_zharrduk` num_men 1, recruitment cost 1200, upkeep 250.
- Base unit stats read from `db.pack`: Warriors attack 30, defence 44, plate 85; Infernal Guard
  32, 56, plate 100; Ironsworn 42, 64, plate 125; Immortals 52, 60, plate 125, no shield, dual
  axes. All use `hu3_dwarf_axe_and_shield` except the Immortals (`hu3_dwarf_dual_axe_slayer`).
  Ironsworn and Immortals use the Infernal Guard's man_entity.
- Kharkadon's skill tree: node set `derpy_zharrduk_skills`, custom nodes tiers 0-7 at indent 1,
  ancillary nodes talisman 20 and weapon 21 at indent 0. Tier must stay at or under 48.

## 5. Open

- Superseded by section 0: the build is done; what remains is the in-game test of Warriors first.
- Whether `bonus_hit_points` on the clone also stacks onto the officer (it does for every entity
  of an ordinary unit). Read his real HP in game; the fix is one cell of the officer entity.
- Whether a commander-class unit accepts `additional_officer` as the general's entity at all. The
  Warriors spike in game is the test, through the wh3 MCP bridge.
- Whether `additional_officer` takes a slot from `num_men` or adds one.
- Balance: decided as per-man stats unchanged, damage output about half the base unit's, `melee_cp`
  at half, a `DAMAGE_SCALE` setting defaulting to 1.0 (spec section 3). Doubling weapon damage was
  advised against because the lord's unit is free. An officer's stats are expected to come from the
  unit row, so Kharkadon inside the unit would fight on the base unit's attack, defence and armour.
- Effects: only the mount-style dummy effect is planned; the user has not named any bonuses.
