# Handoff 2026-09-01 - Tordrek's skill tree learns about the drowned

Status: **built, verified and deployed to both packs; not yet launched.**

Continues `HANDOFF_20260901_NAVAL_HORDE_ROSTER.md`, whose section 8 gave Tordrek Flamebeard his
own ship (the Black Kraken Armada) with 25 Vampire Coast units on its roster. **Nothing in his
skill tree touched a single one of them** - his red line is the shared Chaos Dwarf one
(labourers, blunderbusses, bull centaurs, k'daai) and his unique line buffs the force generically
or the Chaos Dwarf artillery specifically. Half his roster levelled with him and half did not.

Everything below is in `!aa_derpy_hashut_legendary_lords.pack`, both copies byte-identical at
sha1 **`47b9458c1580ac4e3c12bb7a10884bb66147de52`**.

| sha1 | what landed |
|---|---|
| `9e01deb6...` | start of session - the end state of `HANDOFF_20260901_NAVAL_HORDE_ROSTER.md` |
| `2bc97756...` | ten Vampire Coast red-line nodes, seven special-line effect rows |
| `47b9458c...` | one special-line effect swapped after the reach check found it dead |

Built as `tools/gen_tordrek_vc_skills.py`. `--check` dry-runs the whole thing without writing to
the pack, `--selftest` breaks each fault in memory and confirms it is caught. Four tables
touched, and **no new skills, effects, unit sets, loc or icons were authored at all.**


## 1. The red line: CA's own Vampire Coast army skills, reused whole

CA ships a complete Vampire Coast army line - `wh2_dlc11_skill_cst_army_1..6` (three levels
each) and `_8..11` (one level, the rank-7 capstones). That is **exactly the shape of the Chaos
Dwarf half already in the pack**: six base skills at tiers 1-6 and four capstones at 8-11 off a
mid gate. So the ten skills go in as ten new nodes and nothing else is authored.

| node | tier | CA skill | name | parent |
|---|---|---|---|---|
| `derpy_tordrek_drowned_1` | 13 | `wh2_dlc11_skill_cst_army_1` | Held Together by Screws | `derpy_shared_army_0` |
| `derpy_tordrek_drowned_2` | 14 | `..._army_2` | Reanimated Marksman | `derpy_shared_army_0` |
| `derpy_tordrek_drowned_3` | 15 | `..._army_3` | Black Powder Overload | `derpy_shared_army_0` |
| `derpy_tordrek_drowned_4` | 16 | `..._army_4` | Rotten Death | `derpy_shared_army_0` |
| `derpy_tordrek_drowned_5` | 17 | `..._army_5` | Haunting Horror | `derpy_shared_army_0` |
| `derpy_tordrek_drowned_6` | 18 | `..._army_6` | Drowned and Bound | `derpy_shared_army_0` |
| `derpy_tordrek_drowned_7` | 19 | `..._army_8` | Deadly March | `derpy_shared_army_2` |
| `derpy_tordrek_drowned_8` | 20 | `..._army_9` | Ensorcelled Weapons | `derpy_shared_army_2` |
| `derpy_tordrek_drowned_9` | 21 | `..._army_10` | Masterly Splicing | `derpy_shared_army_2` |
| `derpy_tordrek_drowned_10` | 22 | `..._army_11` | Hardened by Death | `derpy_shared_army_2` |

All ten sit at **indent 4**, the red / army lane, continuing straight on from the Chaos Dwarf
half's tiers 0-12. Every one is added to `derpy_tordrek_skills` **only** - `derpy_shared_army_*`
is in all eleven lords' sets and was not touched, so no other lord sees any of this.

`wh2_dlc11_skill_cst_army_7` does not exist in `character_skills`; CA skipped the number.

Four tables carry the change:

| table | fragment | rows added |
|---|---|---|
| `character_skill_nodes` | `derpy_chd_ll_custom` | 10 |
| `character_skill_node_set_items` | `derpy_chd_ll_custom` | 10 |
| `character_skill_node_links` | `derpy_chd_unique_skills` | 10 |
| `character_skill_level_to_effects_junctions` | `derpy_chd_ll_unique_skills` | 7 (section 4) |


## 2. The one check that mattered: do the effects reach units on this ship

An effect that buffs a unit set the ship cannot recruit is a **fully rendered node that does
nothing** - the exact failure shape this build keeps rediscovering. So every effect was resolved
`effect_bonus_value_ids_unit_sets.unit_set` -> `unit_set_to_unit_junctions` and intersected
against the 25 drowned units on the kraken **before** anything was written:

| skill | effects | worst overlap |
|---|---|---|
| army_1 | leadership, melee defence (deckhands / depth guard) | 4 of 6 |
| army_2 | ammunition, missile damage (gunnery mobs / deck gunners) | 6 of 9 |
| army_3 | ammunition, missile damage (artillery) | 2 of 3 |
| army_4 | melee defence, physical resistance (prometheans / leviathan / colossus) | 4 of 6 |
| army_5 | charge, melee attack, missile damage (terrorgheist / scurvy dogs / syreens / deck droppers) | 3 of 3 |
| army_6 | weapon strength, melee attack, speed, charge (hulks / mournguls / bloated corpse) | 1 of 1 |
| army_8 | armour, melee attack, missile resistance (infantry, rank 7) | 5 of 7 |
| army_9 | armour, magic resistance, missile damage (ranged, rank 7) | 8 of 12 |
| army_10 | leadership, melee defence, speed (monsters, rank 7) | 8 of 10 |
| army_11 | magic resistance, melee attack, weapon strength (giant monsters, rank 7) | 4 of 6 |

**No dead nodes.** The shortfalls are all RoR variants, `art_queen_bess` and the Sartosa units,
none of which the kraken can build.

Those are raw set-membership counts. Re-run with rank-gated sets discarded - the filter that
caught the bad special-line pick in section 4 - the six **base** skills are unchanged (`army_1`
4, `army_2` 6, `army_3` 2, `army_4` 4, `army_5` 3, `army_6` 1 ungated units on every effect),
and all four **capstones** drop to **0 ungated**. That is not a fault, it is what a rank-7
capstone is, and CA builds both races the same way: each capstone effect binds a `*_rank7` set
carrying `use_unit_exp_level_range` with `min 7 / max 9` **plus** an ungated `*_rank7_ror`
companion. `wh3_dlc23_chd_melee_chaos_dwarfs_rank7` and `wh2_dlc11_cst_army_chain_set_monster`
are the same construction. So the four Vampire Coast capstones behave on the kraken exactly as
the four Chaos Dwarf ones behave for any Chaos Dwarf lord fielding no Regiments of Renown: they
buff rank 7-9 units and nothing else.

Two shape facts found on the way, both worth keeping:

- **`unit_set_to_unit_junctions` has no `unit` column.** It is
  `(exclude, unit_caste, unit_category, unit_class, unit_record, unit_set)` - a set can be
  defined by class rather than by listing units, and `exclude = true` rows subtract. The
  explicit member column is **`unit_record`, and it holds a `main_units` key**, so it joins
  straight onto `building_units_allowed.unit` with no translation.
- **The four "rank 7" Vampire Coast capstones have no rank gate of their own.** No
  `character_skill_level_details` row, no `character_skills_to_level_reached_criterias` row -
  checked both. Their gate is the parent chain plus the unit sets above, which is why they hang
  off `derpy_shared_army_2` exactly as the Chaos Dwarf capstones do. Copying the parent shape is
  the gate; there is nothing else to copy.


## 3. The lane geometry, measured before placing anything

`indent` is the lane and `tier` the slot along it (memory
`wh3-skill-node-tier-is-slot-indent-is-lane`), so the question was whether tier 22 on indent 4
is somewhere the panel has ever been asked to draw. Counted over vanilla's 24,649
`character_skill_nodes` rows:

- indent 4 tops out at **tier 14** in vanilla, and 24 vanilla rows already sit at tier >= 13 there.
- tier is a sparse slot index, not a depth - indents 2, 5 and 9 reach **99**.
- of 20,588 same-lane links, the widest tier span is **14** and three span >= 13.

So a link from tier 0 to tier 13 is attested, and the ten nodes were placed contiguously at
13-22 with `REQUIRED` links and `required_num_parents 0`, which is byte-for-byte the shape
`derpy_shared_army_1_*` and `_3_*` already use.

Tordrek's set spans **five** node fragments and **four** set-item fragments; the Chaos Dwarf
half of his own lane lives in `derpy_chd_ll_shared`, not in the file being edited. Any check on
cells or duplicate skills has to read all of them or it sees an empty lane.


## 4. The special line

Seven effect rows on three skills Tordrek already has - no new nodes, no new skills:

| skill | what it is | added |
|---|---|---|
| `derpy_tordrek_1` "Submersible Engineering" | the root, **always taken** | +10 armour (VC melee infantry), +5 magic resistance (VC infantry) |
| `derpy_tordrek_4_1` "The Black Kraken Surfaces" | capstone | +12 weapon strength (VC large units), +10 charge bonus (VC monsters) |
| `derpy_tordrek_4_3` "Crew of the Drowned" | capstone | +8 melee attack, +8 leadership, +6 melee defence (VC infantry) |

All at `general_to_force_own`, the scope CA uses for every one of them.

`derpy_tordrek_4_1/4_2/4_3` are **mutually exclusive** (all-pairs rows in
`character_skill_nodes_skill_locks`), so putting the drowned buffs on one capstone alone would
have collapsed the choice for anyone flying the kraken. Two of the three carry them, and the
guaranteed root carries a smaller pair so a player who takes neither is not left with nothing.
**`derpy_tordrek_4_2` "Daemonpact of the Deep" is deliberately untouched** - its own
`wh_main_effect_force_stat_magic_resistance` and `..._enable_magic_attacks` are force-wide and
therefore already reach the drowned.

**One of the seven shipped wrong and was caught before launch by a check written for it.**
`wh2_dlc11_effect_force_stat_speed_cst_monsters_rank7` was the first pick for the Kraken
capstone. Its four bound sets are `wh2_dlc11_cst_army_chain_set_monster`, which carries
`unit_sets.use_unit_exp_level_range = true` with `min_unit_exp_level_inclusive = 7`, and three
**RoR-only** sets the kraken cannot recruit. Ungated reach on this ship: **zero units.** A full
tooltip, a real number, and nothing behind it. `check_reach()` in the generator now resolves
every special-line effect through its sets, discards any set with an experience-level range,
and asserts at least three surviving kraken units - it fails on that effect with
`reaches only 0 ungated kraken unit(s)`. Replaced with
`wh2_dlc11_effect_force_stat_charge_bonus_add_cst_monsters` (5 units, ungated), which reads
better for something surfacing anyway.

The red line is deliberately exempt from that check, on the measurement in section 2 rather than
on assumption: `army_8..11` **are** CA's rank-7 capstones, gated identically to the Chaos Dwarf
half of the same lane.

The generator **prunes as well as appends**: any `wh2_dlc11_` row on one of its own three skills
that is no longer in `SPECIAL` is dropped before the new rows go in. Without that step the dead
`speed_cst_monsters_rank7` row would have stayed in the pack forever while the docs said it had
been replaced - `add()`-only generators cannot retract.


## 5. Verification and state

- `check_reach()` runs before anything is written and prints the ungated kraken reach of each of
  the seven special-line effects: 7, 12, 11, 5, 7, 12, 12 units.
- `py tools/gen_tordrek_vc_skills.py --selftest` - four faults broken in memory and caught:
  a node landing on an occupied `(indent, tier)` cell, one skill on two nodes in the set, a
  link whose parent is outside the set, a non-Vampire-Coast effect in the special-line list.
  The cell and duplicate checks read **every** fragment of `character_skill_nodes_tables` and
  `character_skill_node_set_items_tables` in the pack, not just the edited one (section 3).
- All four edited tables re-exported from the **saved** pack in a fresh MCP session and compared
  byte-for-byte against the generator's own output: **4 of 4 identical**. That confirms the
  import landed, not that the generator is right - the reach check and the selftest are what
  cover the generator.
- `py tools/check_skill_trees.py`: **0 errors**, 29 warnings, identical before and after. All 29
  are pre-existing deliberate downside effects on other lords' capstones (`-armour`, `+upkeep`
  and so on), so the correct read is that this change introduced nothing.
- Deployed to the Workshop folder with `Warhammer3.exe` confirmed not running, and both copies
  hashed afterwards. Previous build backed up before the first write.

The trailing-tab trap from `HANDOFF_20260901_NAVAL_HORDE_ROSTER.md` section 9.3 bit once more on
the way: the destination path parsed out of a TSV's own meta line carries RPFM's padding tabs,
and `import_tsv` reports `File with the following path not found in the Pack:
db/..._tables/derpy_chd_ll_custom` with the tabs still on the end. Split the meta line on tab
and take field 0 before splitting on `;`.


## 6. Also this session, on the previous handoff

Two corrections to `HANDOFF_20260901_NAVAL_HORDE_ROSTER.md`, both doc-only, both made in that
file:

1. **The 25 military-group permission rows cannot leak.** The one recruitment path that does not
   go through a building the faction owns is allied / outpost recruitment, and it was checked:
   `allied_recruitment_unit_permissions` is a **single-column** table (`unit`, 753 vanilla rows)
   - a global eligibility flag with no faction and no group column - so it cannot resolve through
   `factions_tables.military_group`. 37 of the kraken roster's units, the drowned included, were
   already listed there by CA before any of this work. The heavier alternative (a private
   `derpy_chd_black_kraken` military group on the faction row) is not needed.
2. **The chain-gate claim was overstated and is now softened.** The first launch drew six chains
   and no hobgoblin card. Twelve is what an ignored `optional_required_horde_commander` would
   draw, since both chain sets sit on the same slot template, so six is real evidence - but one
   screenshot cannot say *which* six. The confirmation is per-chain and free with the relaunch:
   Tordrek's `hold` icon must be `chd_tower_tribute_halls` (Abnagg's is
   `chd_military_hobgoblins`) and his `hull` `chd_factory_assembly_line` (Abnagg's is
   `chd_military_kdaai`).


## 7. Open

**Not launched.** On the next campaign:

- Tordrek's red line should scroll right past the Chaos Dwarf half to ten Vampire Coast nodes
  with CA's own art and text, and **no other lord should have them.**
- "Submersible Engineering" should list two extra drowned-crew lines in its tooltip, and
  "The Black Kraken Surfaces" and "Crew of the Drowned" two and three.
- Carried over from the previous handoff: confirm the drowned unit cards now draw in the six
  kraken chains, and that Tordrek's `hold` / `hull` icons are the kraken ones (section 6.2).

One risk worth knowing rather than checking now: the ten new nodes carry CA's `wh2_dlc11_` skill
keys, and the panel resolves skill names and icons from those keys globally. Any other loaded
pack that overrides `wh2_dlc11_skill_cst_army_*` text will change what Tordrek's nodes say.

Balance is unmeasured. Ten extra red-line nodes is 22 more skill points of army buffs than any
other lord in the pack can spend, all of them useless to a Tordrek who never builds the ship.
