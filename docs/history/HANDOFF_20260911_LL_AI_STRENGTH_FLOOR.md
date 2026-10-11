# Handoff 2026-09-11 — the HLL lords raised to the vanilla CHD legendary-lord stat floor

Asked to "strengthen the faction strength of all the lords in the db, make it equal to vanilla
legendary lords", clarified mid-session to mean **AI faction strength — auto-resolve, so the
factions these lords lead survive longer as AI**. Chosen method: raise the floor only (leave
lords already at or above vanilla parity alone), mounts included.

> **REVERSED LATER THE SAME SESSION — read this before anything below.** The stat floor was
> built, deployed and verified, and then the user asked to undo it and apply only the missing
> rows from §6.2 instead. **The 63 stat cells are NOT in the shipped pack.** What shipped is
> three rows in `cdir_military_generator_unit_qualities` and nothing else.
>
> **Final state:** deployed **15,876,285** bytes, sha256 `9abe173eaaef4f16`, in both
> `Modding Files/Modpacks/` and `F:\SteamLibrary\...\workshop\content\1142710\3432966208\`.
> Not uploaded to the Workshop. Verified in the deployed binary: `unit_qualities` at 24 rows
> with all three `derpy_abnagg*` keys present, no duplicates, no dangling keys, version 2
> preserved; and `land_units` at **0 differences** against the pre-change export, i.e. the
> revert is real and not just claimed. Bzaark reads MA 30 / MD 40 / 5000 HP / 12 charge and
> Gordak `leather_50` / 3856 / 65 again.
>
> The revert was a file restore from
> `!aa_derpy_hashut_legendary_lords.pack.bak_pre_ai_strength_20260911` (15,876,084 B, sha256
> `7c45ee395ce1e339`), then the row edit on top. **A restore is not enough on its own:** RPFM
> held the buffed pack in memory in an open session, so the file had to be reopened and the
> revert *proved by export* before editing, or the next save would have written the buffed
> tables straight back over the restored file.
>
> `Modding Files/source/ll_ai_strength/` now holds only `unit_qualities.tsv` plus `_export/`
> (the pre-change tables, which are what the pack actually contains). The three generated stat
> TSVs were deleted so nothing can re-import them by accident; `tools/gen_ll_ai_strength.py`
> still works and `--check` regenerates them in one command if the buffs are ever revisited.

**State when the stat work was deployed (now superseded):** 15,876,083 bytes, sha256
`2536272c088472f5`. 63 cells changed across three tables, round-tripped out of the saved pack
and compared cell-by-cell against the generated TSVs (0 mismatches), floor re-asserted against
the saved pack, and re-verified again in the Workshop binary after deployment.

---

## 1. "Faction strength" is not a DB column, and the search that proved it

The phrase matches nothing in the game. Grepping RPFM's own `schema_wh3.ron` for every field
name containing `strength` and mapping each hit back to its owning table returns:

| field | owning table |
|---|---|
| `strength_record` | `campaign_payload_winds_of_magic_strength_changes` |
| `strength_locked` | `campaign_map_winds_of_magic_areas` |
| `unit_minimum_strength` | `campaign_variables` |
| `strength` | winds of magic, `campaign_storms`, `provincial_initiative_strength_levels`, `ritual_incursion_strengths`, `ritual_payload_spawn_storms` |

Nothing per-lord, nothing per-faction. The Strength Rank on the diplomacy screen is computed at
runtime from armies, regions and economy; there is no row behind it. **Do not go looking for
this column again.**

The grep-the-schema-and-map-to-owner trick is worth keeping generally:

```python
tbl = [(m.start(), m.group(1)) for m in re.finditer(r'"([a-z0-9_]+_tables)"\s*:', ron)]
# owner(pos) = the last table name whose offset precedes pos
```

One pass over `%APPDATA%\FrodoWazEre\rpfm\config\schemas\schema_wh3.ron` answers "does WH3 have
a column called X" for any X, with RPFM shut and no dependency rebuild.

## 2. The auto-resolve wiring was already correct — this is the main negative result

The lever the request was actually aiming at is the lord's **auto-resolve combat potential**,
and three separate things that looked like candidate faults all turned out to be fine:

* **`ai_usage_group`.** Every one of the 13 lords sits in a `*_highvalue` group
  (`melee_highvalue`, `melee_mage_highvalue`, `ranged_direct_highvalue`), and each of those
  carries `multiplier 1.0 / additive_mod 1000.0` in
  `autoresolver_ai_usage_group_combat_potential_modifiers` — the identical row the three vanilla
  CHD LLs get. Nothing to fix.
* **`cdir_military_generator_unit_qualities.quality = "characters_only"`.** This looks wrong
  next to Astragoth's `tier_4_step_1_units`, Zhatan's `tier_3_step_1_units` and Drazhoath's
  `tier_2_step_5_units`, and it is **not**. `characters_only` is a valid vanilla value used on
  70 rows, and every one of those rows is cp1/dlc26/dlc27 content — Arbaal, Caradryan, Aislinn,
  Dechala, Golgfag, Sayl, Beorg, Styrkaar, the Masque. It is CA's *current* convention for
  characters; the tier values on the dlc23 CHD lords are the older one. The pack is following
  the newer convention. Leave it.
* **`battle_entities.hit_points`.** 8 for every vanilla CHD LL and for ours. Actual lord health
  is `bonus_hit_points`, which is where the work went.

So the only remaining lever on AI-side strength was the stat block, which is what got changed.

## 3. What was changed

`tools/gen_ll_ai_strength.py`, with `--check` (writes TSVs, no RPFM) and `--selftest`. Floors
are **derived from the vanilla rows in `.skilltree_cache` at run time**, never hardcoded, so a
patch that rebalances Astragoth/Zhatan/Drazhoath moves the floor with it. Re-run after a patch.

Derived foot floor — the element-wise minimum across the three vanilla CHD foot LLs:

```
MA 45   MD 50   wh2_main_plate_125   5512 bonus HP   85 morale   30 charge   430 weapon total
```

Four clamp rules, in order:

1. **Foot rows** clamp to that floor.
2. **Mounted rows** clamp to the vanilla CHD LL row for *that same mount type*
   (bale taurus from Cinderbreath, great taurus and lammasu from Zhatan's).
3. **Mount types with no vanilla LL analogue** (Gordak's giant wolf) inherit the same absolute
   increases the lord's own foot row received, so mounting never becomes a downgrade.
4. **Melee weapons**, foot lords only, clamp `damage + ap_damage` to the floor total, splitting
   the increase in each weapon's *own* damage:ap ratio.

63 cells. Biggest movers: Bzaark 30/40 -> 45/50, Azeros 35/40 -> 45/50, Balur MD 30 -> 50,
Gordak 3856 HP -> 5512 and `leather_50` -> `plate_125`, Tordrek and Azeros weapons 100/200 ->
143/287, Bzaark 200/50 -> 344/86.

Files: `Modding Files/source/ll_ai_strength/{land_units_base,land_units_mount,melee_weapons}.tsv`,
generated from `_export/` (the three tables exported out of the pack — the generator's input,
keep it for re-runs).

## 4. Corrections found the hard way

**Rule 2 exists because applying the foot floor to a mount is wrong.** In vanilla, mounting
*lowers* melee defence: Zhatan is MD 55 on foot and MD 28 on a great taurus. A single global
floor would have pushed every great taurus to MD 50, i.e. well above the vanilla row it is
supposed to be matching. Mount floors must come from mounted vanilla rows, per mount type.

**Rule 4 exists because a flat total would invert weapon character.** Bzaark's weapon is
200 damage / 50 ap — a deliberately low-ap caster weapon. Topping it up to the 430 floor by
adding the shortfall to `ap_damage` would have turned an anti-infantry weapon into an
armour-shredder. Scaling both halves by the same factor keeps a low-ap weapon low-ap and an
ap-heavy weapon ap-heavy; the selftest pins both directions.

**`csv.writer` must not be used to write an RPFM TSV.** `quoting=QUOTE_NONE` with
`quotechar=""` raises (`"quotechar" must be a unicode character or None`), and any working csv
configuration will *quote* a cell containing a quote mark. RPFM's own export never quotes, and a
quoted cell re-imports as literal quote marks in the data. Join on tabs by hand.

**`read_vanilla_cache.load()` reads `VecRFile[0]` only.** `land_units`, `factions` and
`melee_weapons` are each split across several of CA's files, so the shipped helper silently
returns a partial table — `land_units` came back complete only because the loop was rewritten to
walk every `VecRFile` entry. Any new consumer of the cache needs the same loop, or it will
conclude a vanilla key does not exist when it is simply in the second file.

**The armour name suffix really is the armour value**, verified against `unit_armour_types`
(`wh2_main_plate_130` -> 130, `wh2_main_leather_50` -> 50). But **there is no leather record at
or above 125** — the maximum leather is 95 — so Gordak could not keep his leather audio type
and had to move to `wh2_main_plate_125`. Records >= 125 exist only in body, bone, chainmail,
heavy_metal and plate.

## 5. Do not re-derive

* There is **no** `faction strength` / per-lord strength column in WH3. See §1.
* `characters_only` is **not** a bug in the unit-quality table. See §2.
* The lords' `ai_usage_group` wiring is **correct** and already gets vanilla's +1000
  auto-resolve additive. See §2.
* Vanilla CHD LL reference block, for comparisons that do not want a cache read:

  | | MA | MD | armour | bonus HP | morale | charge | weapon dmg/ap |
  |---|---|---|---|---|---|---|---|
  | Astragoth | 60 | 50 | plate_130 | 6816 | 85 | 50 | 170/310 |
  | Zhatan | 62 | 55 | plate_125 | 5812 | 85 | 30 | 280/180 |
  | Drazhoath | 45 | 65 | plate_125 | 5512 | 85 | 30 | 300/130 |
  | Cinderbreath (bale taurus) | 64 | 46 | plate_80 | 8648 | 85 | 80 | 140/425 |
  | Zhatan great taurus | 46 | 28 | plate_60 | 6660 | 85 | 80 | 130/320 |
  | Zhatan lammasu | 44 | 52 | plate_60 | 6840 | 85 | 40 | 270/180 |

* `cdir_military_generator_config` is **empty on all 717 vanilla factions**. Whatever the AI
  army generator keys off, vanilla never sets this column.

## 6. Still open

Both are in the same AI-army system the request was aiming at; both were reported and
deliberately **not** changed, because each is a different table from the approved stat-floor
scope and each needs a judgement call.

1. **All 10 custom factions in `factions_tables/!!_cr_oldworld_new_factions` set
   `cdir_military_generator_config = "WH_Chaos"`** — the Warriors of Chaos generator.
   `WH_Chaos_Dwarfs` exists as a separate valid key (both are among the 105 in
   `cdir_military_generator_configs`). If the column is read at all, these Chaos Dwarf factions
   are composing Chaos armies. The complication is §5: vanilla leaves it empty everywhere, so
   the two defensible fixes are *clear it* (true vanilla parity) or *set `WH_Chaos_Dwarfs`*
   (correct race if it is read). Note the file name suggests it is shared with CR Old World, so
   check compatibility before editing.
2. ~~**Abnagg and his two mounts are absent from `cdir_military_generator_unit_qualities`.**~~
   **DONE — this is the only thing that shipped.** The three rows
   (`derpy_abnagg`, `derpy_abnagg_great_taurus`, `derpy_abnagg_lammasu`) were added at
   `characters_only` in group `wh3_default_land_characters`, matching all 21 existing rows.
   Before cloning that value the generator asserts every existing row uses the same group and
   quality, so a mixed table would stop the run rather than silently pick one.

   Worth keeping: the gap was found by **diffing `main_units` against `unit_qualities`**, not by
   eyeballing the list — `unit_key` is an FK to `main_units.unit`, so the set difference in both
   directions is the whole audit. It also proved there were no dangling rows, and the same
   two-line check now covers all 24 units. Run it after adding any lord or mount:

   ```
   main_units(base 13 + mounts 11) - unit_qualities  ->  must be empty
   unit_qualities - main_units                        ->  must be empty
   ```

**The caveat that limits this whole change:** `land_units` is shared between player and AI.
Raising these stats buffs the player's own lords identically — there is no AI-only stat block.
AI-only survivability would have to be an effect bundle applied by script to AI-controlled
factions, which is a different piece of work.

## 7. Verification actually run

* `py tools/gen_ll_ai_strength.py --selftest` — floor derivation, the clamp, the mount-delta
  inheritance, and both weapon-ratio directions.
* Cell-level diff of generated vs input TSVs: exactly 63 differing cells, confined to
  `armour`, `bonus_hit_points`, `charge_bonus`, `melee_attack`, `melee_defence`, `morale`,
  `damage`, `ap_damage`. No row-key drift, headers and `#table;version;path` metadata identical.
* After save, all three tables re-exported out of the saved pack and compared cell-by-cell
  against the generated TSVs — **0 mismatches**, which is the check that proves the pack still
  decodes rather than merely contains the files.
* Floor re-asserted against the round-tripped base table: no foot lord left under it.
