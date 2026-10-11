# Handoff 2026-09-17 - Abnagg and Tordrek lose their stances on confederation

Status: **two fixes, both deployed.** `Modpacks/` and the Workshop copy at
`...\1142710\3432966208\` are byte-identical, 15,918,355 bytes, md5
`82d6a798e23373d2debcb0fee30294d9`. Backups
`!aa_derpy_hashut_legendary_lords.pack.bak_preconfedstances_20260917` (before section 2) and
`.bak_prestancetitle_20260917` (before section 6). **Not re-uploaded to the Workshop item, and
both fixes are unverified in game.**

**Symptom, as reported:** "in the HLL mod, abnagg and Tordrek is missing their stances when
confederated in the tower of zharr."

## 1. Root cause - the two stance layers that key on FACTION

`docs/sessions/HANDOFF_20260909_ABNAGG_SEA_STANCES.md` established four layers. Split them by
what they key on and the bug is immediate:

| layer | keyed on | survives confederation |
|---|---|---|
| 1 `wh3_dlc26_effect_stance_availability_*` on `derpy_abnagg_lord_trait` | the faction the bundle was applied to | **no** |
| 2 `campaign_stance_effects_junctions` | force type `DERPY_CHD_NAVAL_HORDE` | yes - rides the force |
| 3 `campaign_stances_factions_junctions` | `factions.key` | **no** |
| 4 `campaign_stances_composite_scenes` | campaign group, matched by agent subtype | yes - rides the character |

Layer 1 is applied by the start scripts as
`cm:apply_effect_bundle("derpy_abnagg_lord_trait", "cr_chd_warfleet_of_uzkulak", 0)` - a bundle
on the HOUSE FACTION. A seat claim confederates that faction out of existence and a faction
effect bundle does not transfer to the absorber, so the lord arrives under the new flag with no
`settle_enable`: no Encamp button on a horde that is nothing but a horde. Layer 3, which the
2026-09-09 session proved is the gate the **sea** stance bar reads, held rows for exactly two
factions - the two houses - so the naval bar collapses to DEFAULT as well.

This is not a stance fact. **Any faction-applied bundle a mod uses as a lord's "trait" is lost
on confederation** - here that also costs the new owner Abnagg's +20 movement range, his port
and sea-trade economy and Tordrek's high-seas attrition immunity.

## 2. What shipped

**DB.** `db/campaign_stances_factions_junctions_tables/derpy_chd_naval_horde`, 22 -> **165
rows**: the same eleven stances for all **15** Chaos Dwarf factions (the ten Tower of Zharr
houses, CA's four playable, and `wh3_dlc23_chd_conclave`), because any of them can hold the
tower and nothing can write this table at runtime. The list is CA's eight
(`wh3_dlc23_faction_trait_chaos_dwarfs`, measured) plus `SETTLE` / `SEA_RAID` /
`ASSEMBLE_FLEET`, so it is a superset of every stance any Chaos Dwarf faction can hold and is
correct whether the table adds to a faction's list or replaces it - still unknown. `PATROL`
stays out; it needs a cloned recruitment-dummy bundle.

Source of truth is now `Modding Files/source/naval_horde/export/campaign_stances_factions_junctions_tables.tsv`,
which it was not before - the table had been written straight into the pack in RPFM.

**Lua.** `derpy_chd_naval_admiral.lua`, all four campaign folders, one new block: sweep the
Chaos Dwarf subculture, and for any faction holding `derpy_abnagg` or `derpy_tordrek` that does
not already have the matching bundle, apply it. Three triggers, and all three are needed:

* `FactionJoinsConfederation` - the ANNEX route, where the house faction exists.
* `CharacterCreated` - the GRANT route. Where the house is absent from the campaign the seat
  SPAWNS the lord and no confederation event ever fires. **That is Tordrek in Immortal
  Empires**: `cr_chd_black_kraken_armada` is not on that map (2026-09-09 section 10).
* `cm:add_first_tick_callback` - backfill for a save that confederated before this shipped.
  Without it the player would have to confederate again to get the stances back.

`faction:has_effect_bundle()` makes the sweep idempotent, so all three can be blunt.

## 3. The check

`tools/test_naval_confed_stances.lua` runs the **shipped** file under Lua 5.1.5 against a
stubbed `cm`/`core`/world and reads back every `apply_effect_bundle` call: a Chaos Dwarf faction
holding both lords gets both bundles once, a faction that already holds one is skipped, a
Vampire Coast faction holding a character of the same subtype key is skipped, the spawn route
applies on the created lord and does nothing for an unrelated character.

    & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\test_naval_confed_stances.lua

Three mutants of the shipped Lua - subculture gate removed, `has_effect_bundle` guard removed,
spawn subtype gate removed - were each watched to fail it before the file was restored.

## 4. A landmine found on the way, and half-defused

`import_naval_horde.py` re-imports every TSV in `Modding Files/source/naval_horde/export/`.
Three of them had drifted from the pack, so running it would have silently reverted live work:

* `zz_campaign_group_members.tsv` held priority **0.0000** where the pack holds **1.0000** -
  the 2026-09-09 composite-scene override. **Resynced from the pack**, so this one is gone.
* `zz_agent_culture_details.tsv` and `zz_effect_bonus_value_agent_subtype_junctions.tsv`
  generate tables the pack **does not contain at all**. A run would ADD them. Left alone -
  nobody established today whether that is wanted. **Read this section before running that
  importer.**

Today's write was therefore targeted (the one table plus the four Lua copies), not a full
importer run, and verified by re-opening the saved pack in a fresh MCP session: 165 rows across
15 factions, group-members priority still 1.0, all four Lua copies byte-identical to the mirror
and parsing under `luac -p`.

## 5. What is left

1. **Re-upload.** The Workshop *folder* is deployed, so the next launch loads the fix, but
   Steam reverts a hand-copied file on re-validation - the durable route is re-uploading
   workshop item 3432966208 through the Mod Manager.
2. **Test.** Claim the Uzkulak seat in IEE (ANNEX) and the Black Kraken seat (GRANT), then
   check Abnagg's land bar for Encamp and his naval bar for DOUBLE_TIME. Grep the script log
   for `re-applied derpy_abnagg_lord_trait` - the sweep logs every application.
3. **Open question kept open.** SETTLE at sea has never drawn (2026-09-09 section 10) and this
   changes nothing about that. The fix restores what confederation took; it does not add what
   was never there.

---

## 6. Second fault, found by the player's screenshot: the Encamp tooltip has no title

Reported the same session, after the restore was deployed: the Encamp stance tooltip draws its
six effect lines and **no title line at all** - not a blank title, an absent one.

`db/effect_bundles_tables/derpy_chd_naval_horde` carries
`localised_title = "Stance: Encamp"` and a full description **in the row**, which is why this
looked correct in RPFM. It is not what the panel reads.
`MEMORY/wh3-effect-bundles-text-in-db-row` already records this for the Faction Effects panel
(27 bundles, 2026-09-05); the stance tooltip is a **third** consumer of the same loc keys. CA
ships both halves for every bundle that displays - `effect_bundles_localised_title_<key>` and
`effect_bundles_localised_description_<key>`, measured in `local_en.pack` on
`wh2_dlc11_bundle_stance_army_encampment_horde_coast`, the Vampire Coast flagship encampment
this bundle was modelled on, which reads "Stance: Encamp" in both the row and the loc.

The 2026-09-05 sweep missed this one because it covered the `derpy_chd_ll` and
`derpy_chd_toz_annex` fragments and this bundle lives in `derpy_chd_naval_horde`, added later.
**A per-fragment fix does not generalise.** So the fix is two loc rows plus a check.

### What shipped

Two rows appended to `text/db/derpy_chd_naval_horde.loc` (157 -> 159), the text **read out of
the DB row programmatically** rather than retyped, so the two copies cannot disagree.

`tools/check_effect_bundle_loc.py <pack>` (new) reads every `db/effect_bundles_tables/*`
fragment and every `.loc` in a pack and reports any bundle missing either key. Run against the
deployed pack it isolated exactly this bundle out of 60. **It checks existence and nothing
else**, and section 7 is why.

    py tools\check_effect_bundle_loc.py "<pack>"     # exit 1 on a finding
    py tools\check_effect_bundle_loc.py --selftest

## 7. Do not re-derive: the two stricter checks that are both wrong

Both were written, run, and backed out against measurement. Do not add either back.

* **Comparing the loc against the row** reported **19** of this pack's own bundles. Most of them
  leave `localised_title` / `localised_description` empty or `"PH"` on purpose - the loc is the
  single source and the row column is dead weight. A check that compares two copies has to know
  which one is live.
* **Flagging a blank or `"PH"` description** reported **12** more, and one of them is CA's own
  convention: `effect_bundles_localised_description_wh3_dlc23_chd_toz_tier_1_reward` through
  `_4_reward` read literally `"PH"` **in vanilla**. Our tier 5 matching them is correct, not a
  leftover placeholder.
* `[hidden]` bundles are exempt by design - 20 of the Tower of Zharr fragment's 46 rows are
  hidden cost modifiers, and having no loc is how they stay invisible.

Also measured and **not** changed: eleven `derpy_*_lord_trait` bundles ship a title and an
**empty** description loc. That is a style gap, not a defect, and filling it means authoring
eleven pieces of flavour text nobody asked for. Left alone deliberately.

## 8. Section 6 deployed and verified

Verified against the **deployed** file, not the source: `check_effect_bundle_loc.py` reports
0 findings across all 60 bundles, both loc entries read back as "Stance: Encamp" and the full
description, the stance junction table still holds its 165 rows and the four
`derpy_chd_naval_admiral.lua` copies still match the mirror. Both packs md5
`82d6a798e23373d2debcb0fee30294d9`.

Still open: the Workshop *item* upload (Steam reverts a hand-copied file on re-validation), and
both fixes are unverified in play - see section 5.
