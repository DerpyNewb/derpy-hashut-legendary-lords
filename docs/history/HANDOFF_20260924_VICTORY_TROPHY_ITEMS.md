# Handoff 2026-09-24 - the victory routes paid Zhatan's and Gorduz's items

Status: **fixed, built and deployed to the Workshop folder.** Not uploaded to the Workshop item.

| copy | size | sha256 (first 16) | backup |
|---|---|---|---|
| Workshop `...\1142710\3432966208\!aa_derpy_hashut_legendary_lords.pack` | 15,927,924 | `326a5b657992e29a` | `.bak_pretrophyitems_20260924` beside it |
| `Modding Files\Modpacks\!aa_derpy_hashut_legendary_lords.pack` | 15,952,661 | `15e4c9449f2afb63` | `.bak_pretrophyitems_20260924` beside it |

The two copies are **not** byte-identical, and that is not this session's doing - see section 5.

**Symptom, as reported:** "the victory conditions have still items that are specific to
characters like zhatan the black, change or create powerful ancillaries items that can be used
by everyone."

## 1. Root cause

`gen_victory_routes.TROPHIES` was eight vanilla ancillaries, filtered on `faction_set`,
`randomly_dropped` and "not a lords-pack skill item". **`faction_set` says who may OWN an item,
never who may WEAR it** - that is `ancillaries_included_agent_subtypes`, which nothing checked.
Five of the eight had a row there:

| item | locked to |
|---|---|
| `wh3_dlc23_anc_weapon_chd_the_obsidian_axe` | `wh3_dlc23_chd_zhatan` |
| `wh3_dlc23_anc_armour_chd_armour_of_gazrakh` | `wh3_dlc23_chd_zhatan` |
| `wh3_dlc23_anc_enchanted_item_chd_chaos_runeshield` | `wh3_dlc23_chd_zhatan` |
| `wh3_dlc23_anc_weapon_chd_dagger_of_malice` | `wh3_dlc23_chd_gorduz_backstabber` |
| `wh3_dlc23_anc_enchanted_item_chd_banner_of_slavery` | `wh3_dlc23_chd_gorduz_backstabber` |

All five are also `transferrable = false`. No house lord could equip them.

## 2. Why minted items and not a vanilla swap

Surveyed every vanilla unique (score >= 199) that is unlocked, not randomly dropped, and in
`all` or `anc_set_exclusive_chaos_dwarfs`. The strong Chaos Dwarf candidates all fail a filter:

* **the eight Dwarf-god relics** (5 lesser + 3 major) are exactly the right shape, but
  `derpy_chd_drill_chain.lua` grants all eight to every house through the Great Drill chain -
  the "already coming to them" mistake of 2026-09-09 again. The three lesser relics that WERE
  in the old pool had that problem too; they are gone as well.
* **the `wh3_dlc23_anc_convoy_*` items** are the convoy's rewards.
* the rest of the CHD set is `randomly_dropped` or subtype-locked.

So `TROPHY_ITEMS` mints eight `derpy_trophy_*` items in the lords pack itself - the same pack as
the script that pays them, so the payload key always resolves (the dependency argument that
first chose vanilla still holds).

## 3. What shipped

`tools/gen_victory_routes.py`:

* `TROPHY_ITEMS` - key, category, name, flavour, `(effect, value)` list. Ordered weapon /
  armour / talisman / enchanted twice, so a house's consecutive routes never pay one slot twice.
  `TROPHIES` is derived from it.
* three new TSVs in `Modding Files/source/victory_routes/`: `ancillary_info_tables`,
  `ancillaries_tables`, `ancillary_to_effects_tables`, all fragment `derpy_chd_victory`, v0.
  16 loc rows appended to `loc__derpy_chd_victory.tsv` (onscreen_name + colour_text;
  explanation_text left empty on purpose).
* each `ancillaries` row is field-for-field a vanilla relic row: `faction_set all`,
  `transferrable true`, score 200, swap 0, not randomly dropped, not stolen, not destroyed, type
  = the slot's generic `wh_main_anc_*` icon type.
* effect scope is **not** in `TROPHY_ITEMS` - `trophy_effect_rows()` reads it out of
  `anc_effect_scopes.SCOPE`.
* `check()`: a reward that is not a `TROPHY_ITEMS` row is refused (replaces the old
  `startswith("wh3_")` rule, which is what let the locked items through); every trophy key must
  be lowercase `derpy_trophy_*`; every effect must have a vanilla scope; no duplicate keys or
  effects; name and flavour one line, no tabs.
* `--selftest`: +3 mutants - a foreign key, **Zhatan's axe put back** (the reported defect),
  and a trophy effect with no vanilla scope. Also asserts every trophy has its info, ancillaries
  and effects rows and both loc keys, the 29-cell row shape, and that every paid trophy ships.

`tools/import_victory_routes.py`: `EXPECTED_ROWS` covers the three new TSVs and the larger loc.
It already imports every TSV in the source folder, so no other change.

`tools/gen_commission_dilemmas.py`: `vanilla_pool()` now also drops subtype-locked items. Seven
vanilla items are `randomly_dropped` AND locked, none is CHD-eligible, so the pool is still 117
and nothing was rebuilt - the guard is there so a patch cannot slip one in.

The eight items:

| key | slot | effects |
|---|---|---|
| `derpy_trophy_conquerors_cleaver` | weapon | Flame Storm (bound), sundering attacks, WS +25, AP +60 |
| `derpy_trophy_hell_iron_warplate` | armour | Regeneration, armour +40, ward +15, fire res +20 |
| `derpy_trophy_heart_of_the_furnace` | talisman | Fire Breath, magic res +30, physical res +15, army ward +5 |
| `derpy_trophy_chains_of_the_conquered` | enchanted | Terror, raid +25, sacking +25, PO +5, army melee attack +6 |
| `derpy_trophy_horn_blade_of_the_bull` | weapon | Deadly Onslaught, warpflame + magic attacks, MA +15, charge +25 |
| `derpy_trophy_ash_veil_mantle` | armour | barrier +600, missile res +25, magic res +20, army replenish +10 and in foreign territory |
| `derpy_trophy_tyrants_seal` | talisman | Unbreakable, MD +15, army MD +6, army leadership +8 |
| `derpy_trophy_everburning_censer` | enchanted | Fireball (bound), army physical res +10, army XP +20 |

`docs/VICTORY_CONDITIONS.md` section 12 now has filter 3 and the minted-items paragraph.

## 4. How it was verified

* `gen_victory_routes.py --check` and `--selftest` green (18 deliberate breaks); `luac -p` on
  the Lua exit 0; the Lua names `derpy_trophy_*` 35 times (34 routes + the second block of the
  map-gated route) and a `wh3_` ancillary 0 times.
* all 34 effect keys exist in vanilla `effects`, and every value's sign agrees with
  `is_positive_value_good` (checked against `.skilltree_cache/effects.json`).
* every ability effect binds through a plain `effect_bonus_value_unit_ability_junctions` row
  with no `effect_bonus_value_unit_set_unit_ability_junctions` row, so none is secretly one
  race's (the [[wh3-effect-unit-set-binding-trap]] check). Regeneration binds to CA's generic
  `wh_main_unit_passive_regeneration`.
* no existing pack in `Modpacks/` contains `derpy_trophy_`.
* both packs: imported, then `--verify-only` in a fresh RPFM session round-tripped 8 / 8 / 34 /
  73 / 6 / 39 rows and the script. Per-file diff against each backup (db entries hashed past the
  GUID bytes): **3 added, 4 changed, 0 removed, nothing else touched.** The missions and
  victory_types entries show as changed bytes but decode to identical rows - RPFM re-encodes on
  save.
* the Workshop copy was imported by a background job that waited for `Warhammer3.exe` to exit
  (it held the file open), confirmed RPFM was up, backed up, imported and verified.

**Not verified in game.** No campaign has been started with these items.

## 5. Found on the way: the two lords-pack copies have diverged

Before this session, Workshop (Sep 19, 15,918,510 B) and Modpacks (Sep 17, 15,943,247 B) differed
in 13 files, with changes on both sides:

* **Modpacks only:** the four `derpy_chd_drill_chain.lua` copies at 35,432 B (Workshop has
  29,209 B) - the 2026-09-17 Drill relic dilemma fix, which that handoff says was **not
  deployed**.
* **Workshop only:** 9 DB tables that differ from Modpacks - `agent_subtypes`,
  `battle_entities`, `battle_set_piece_armies_characters_junctions`, two
  `campaign_character_art_sets`, `character_skill_level_to_effects_junctions`,
  `effects/derpy_chd_naval_horde`, `slot_templates/derpy_chd_naval_horde`,
  `special_ability_groups_to_units_junctions`. No handoff found that accounts for the Sep 19
  Workshop change.

This session imported into **each copy in place** and copied neither over the other, so the
divergence is exactly as it was. **Do not copy Modpacks over the Workshop copy** until someone
reconciles it, or those 9 tables are lost from the game.

## 6. Do not re-derive

* The vanilla trophy survey is done: every strong vanilla CHD item is locked, a random drop, a
  Drill relic or a convoy reward. Do not go back to vanilla for this pool.
* `anc_effect_scopes.SCOPE` is the scope source; do not hand-pick a scope for a trophy effect.
* Ability names to avoid on a generic item: the lord-signature abilities (Obsidian Axe, Stone
  Mantle, Hellshard Amulet, ...) bind generically, but their names and tooltips name an item or a
  lord (Stone Mantle's says Astragoth), which reads as character-specific again. Dark Protection
  (`wh2_dlc11_lord_abilities_dark_protection`) is a Vampire Coast lord ability.
* The trophy mission payload is written at issue time, and routes are issued only when
  `cm:is_new_game()` - **a campaign started before this deploy still pays the old items.**

## 7. Also this session: the memory index

`MEMORY.md` was 43.3KB against a 24.4KB read limit, so its last 120 of 308 entries - including
the user's "always deploy to the Workshop folder" rule - never loaded. It is now 4.8KB: 18
working rules inline, and one line per topic hub (`index-*.md`, 9 of them) holding the other 290
entries verbatim. A script asserted all 308 landed exactly once; no memory file was edited or
deleted. The pre-change index is in the session scratchpad only.

## 8. What is left

1. **Upload** the Workshop item 3432966208 through the Mod Manager - the folder is deployed, the
   item is not, and Steam reverts a hand-copied file on re-validation.
2. **In-game check**, new campaign: finish a route, and confirm the item preview on the victory
   panel names the new item, and that a non-Zhatan lord can equip it.
3. **Reconcile the two lords-pack copies** (section 5), then deploy the undeployed 2026-09-17
   Drill dilemma Lua.
4. Balance is a first pass. The numbers sit at or a little above the major relics; tune
   `TROPHY_ITEMS` and re-run generate + import if they play too strong.
