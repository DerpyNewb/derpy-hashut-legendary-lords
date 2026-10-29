# Adding custom seats and tiers to the Tower of Zharr

How the fifth tier ("The Subjugation") in `!aa_derpy_hashut_legendary_lords.pack` was made to
work, what the engine enforces that no tutorial mentions, and what is still open.

Written 2026-08-17, **feature confirmed working in game 2026-08-18**, on three playable custom
lords and their factions in IEE: seats claim, districts complete and pay out, each seat
delivers its legendary lord, and a house holds its own seat from turn one. **Panel art settled
2026-08-19** — lava beams removed, per-seat name labels added, and the bull-head crest raised
clear of the seats (§5). Current build SHA256 `D59B4C50…`, 14,572,712 bytes.

**If you only read one thing:** four separate causes kept the seats from claiming, and every
one of them failed *silently* with all visible state reading healthy. They are §2 (two junction
tables), §4 (the wrong ritual event), and §6 (the flags that lie). Check those before
theorising.

---

## 1. What the feature is

A fifth tier in the Tower of Zharr with twelve seats, one per modded Chaos Dwarf house lord,
grouped into three districts of 4/4/4 (ten seats in 4/3/3 until 2026-10-03). Claiming a seat
does one of two things, decided per seat at runtime:

- **ANNEX** — the lord's faction exists in this campaign: confederate it.
- **GRANT** — it does not (plain Immortal Empires): spawn that lord into the claimant's
  recruitment pool instead. Since 2026-10-05 a GRANT can bring a second lord too:
  `GRANT_COMPANIONS` in `zz_derpy_toz_annex.lua`, keyed by seat suffix, pools Gordak with
  Abnagg's seat and leaves `derpy_grant_rank_<claimant>_derpy_gordak = 10`, which the victory
  routes script applies on recruit (`sessions/HANDOFF_20261004_WARRHAK_GORDAK_QUESTS.md`).

Completing both seats of a district pays out that district's effect bundle.

Seats cost **300 Conclave Influence** each.

| District | Category key | The houses | Reward on completion |
|---|---|---|---|
| Bloodline | `DISTRICTS_ANNEX_T5_A` | Overlords of Zharrduk, Baal, Fists of Hashut, Horns of Hashut | Conclave Influence +25%, recruitment points +2, global recruit time -1 |
| Thrall | `DISTRICTS_ANNEX_T5_B` | Slaves of the Black Dwarf, Uzkulak, Black Kraken, Khorakk | Labour +150/turn, convoys +1, raw material efficiency +5% |
| Forge | `DISTRICTS_ANNEX_T5_C` | Bzaark, Snakebeard's Artificers, Azeros, Uzkul Mingol Company | Armaments +5%, research +10% |

### Three districts is the ceiling, and seats are free

**Tier width is set by district COUNT, not seat count** — seats stack inside a district.
On paper `list_clip` is 1600 wide and `template_tower_district` 356 + 22 spacing, which
suggested four would fit at 1522px. **In game four still ran off both edges**, so the real
usable width is narrower than the authored clip. Three is the tested ceiling.

Vanilla caps a district at four seats, so **3 x 4 = 12 seats fit** - and since 2026-10-03 all
twelve are taken (the Overlords of Zharrduk and the Uzkul Mingol Company, `HANDOFF_20261003_NEW_HOUSE_LORDS.md`).
A thirteenth house gets no Subjugation seat without a tested fourth district. Up to the twelfth,
adding a lord meant adding a seat to a district, never adding a district.

### The twui changes worth making

### Is the override necessary? No — and it is worth knowing why

`!aa_derpy_hashut_legendary_lords` ships a full 406 KB copy of CA's
`ui/campaign ui/tower_of_zharr.twui.xml`. **The fifth tier needs none of it.** The ladder is
built from `DatabaseRecords("CcoRitualCategoryGroupRecord")`, so vanilla's own panel renders
`toz_tier_5`, prices it, and claims from it with zero UI changes — proven by the file's own
history: before 2026-08-19 the entire override existed to change **one attribute**, and the
feature worked.

```
$ diff vanilla/tower_of_zharr.twui.xml  shipped/tower_of_zharr.twui.xml   # before 2026-08-19
2366c2366
<     vertical_alignment="Center"/>
---
>     vertical_alignment="Top"/>
```

Today it carries eleven hunks, 81 lines against 11,814 (re-measured 2026-08-19). Everything in it is cosmetic or additive;
nothing in it is load-bearing.

**The cost.** The copy is pinned to the patch it was extracted from. Nothing else overrides
this file today — a scan of every subscribed Workshop pack found exactly one hit, this one — so
there is no live conflict, but any CA change to the panel is silently reverted, and any future
mod that touches it collides. **After each game patch, re-diff vanilla against the shipped copy
and re-apply the five hunks** rather than assuming it still matches.

**The override-free route**, if it ever becomes worth it: hide the lava with
`find_uicomponent` + `SetVisible(false)` on panel open, and ship the seat label as its own
small `ui/campaign ui/derpy_toz_seat_label.twui.xml` instantiated per seat with
`CreateComponent` — a new file conflicts with nobody. That trades a guaranteed-stale copy of
CA's file for per-frame component lookups; it has not been done because the current form works
and nothing competes with it.

**Line endings matter here.** CA ships this file CRLF. Editing it with a tool that normalises
to LF rewrites all 11,814 lines, costs ~11 KB, and makes the next vanilla diff useless. Check
with `grep -c $'
'` before packing.

### The edits themselves

The pack ships an override of `ui/campaign ui/tower_of_zharr.twui.xml`. Five edits so far,
eleven diff hunks:

1. **Header alignment.** `district_list`'s LayoutEngine ships `vertical_alignment="Center"`,
   so districts with different seat counts have their headers at different heights. Setting
   it to `"Top"` (line 2366) lines every district header up. One attribute.

2. **The red lava beams, removed (2026-08-19).** A completed district draws two 50×333 red
   beams down its left and right edges. They come from *two* places and hiding one leaves the
   other:
   - `template_tower_district`'s **`complete`** state carries two `<image>` entries pointing
     at `dlc23_tower_of_zharr/lava_effect_ph.png` (`_ph` = placeholder), docked Top Left and
     Top Right at `14,37` / `-14,37`.
   - `sprite_lava_start_left` / `sprite_lava_start_right` are separate components under
     `complete_status_holder > sprite_animation_holder`, each running a `SpriteAnimation`
     callback over `UI\sprite_anims\tower_of_zharr\District Lava Effect\lava_drip_start_` (backslashes, as in the file),
     31 frames at 75 ms.

   Both were cut: the two `<image>` entries deleted from the `complete` state, and the two
   sprite components removed from the `<hierarchy>` block (their definitions stay, orphaned —
   a component that is not in the hierarchy is never created). Nothing references either by
   `id`, so nothing else moves.

3. **A per-seat name label, `tx_confederate` (2026-08-19).** `template_tower_of_zharr_seat`
   is 98×218 and draws only art, so a claimed seat gave no clue which house it belonged to.
   A text component docked `Bottom Center`, 128×46, bound to:

   ```xml
   <callback_with_context callback_id="ContextTextLabel"
       context_object_id="CcoCampaignRitual"
       context_function_id="RitualContext.DisplayName"/>
   ```

   `CcoRitualRecord.DisplayName` is documented as "returns the localised name of the ritual",
   i.e. `rituals_display_name_<key>` — so the label is driven entirely from loc. The ten seat
   names were rewritten to `Confederate with <faction>`; the old flavour titles ("Breaker of
   Khorakk") live on in `rituals_description_<key>`, which the tooltip still shows.

   **The label is 128 wide against a 98-wide seat and seats zigzag on a 130px pitch**
   (`ContextCommandGiverOnCreate` offsets child 2 and 4 by 130). "Confederate with Slaves of
   the Black Dwarf" wraps to three lines. This is the tightest thing in the panel — check it
   in game before adding to it.

4. **The bull-head crest, raised one row (2026-08-19).** `top_tier_bull_head` sat on the
   seats. `dock_offset` y goes from CA's `-604` to **`-1565`**, and `offset` from `250,1479` to
   `250,518` to match. That is CA's value minus **961** — the height of the row the fifth tier
   adds, `829 + 132` spacing — measured in game, not guessed. §5 has the measurement, why the
   number is not derivable from this file, and the probe to re-derive it after a patch.

5. **The tier-four seat list, unhardcoded (2026-08-30).** CA builds the top row from
   `seat_holder` and `seat_slots_holder`, both carrying the same expression:

   ```
   (list = RitualListForManager(PlayersFaction.RitualManagerContext)
           .Filter(RitualContext.CompletionPayloadContext.ConfederatedFactionsList.Any(IsPlayersFaction) == false))
   => { list | Join(list.FirstContext(RitualContext.Key != "...t4_conclave"),
                    list.FirstContext(RitualContext.Key == "...t4_conclave"),
                    list.LastContext(RitualContext.Key != "...t4_conclave")) }
   ```

   The `Filter` is CA's own guard against offering you your own seat, and it is correct.
   The `Join` is not: it renders **exactly three** children — first, the Conclave seat,
   last — because CA assumed the player is always one of the four lords, so the filtered
   list is always the other three and `Join(first, conclave, last)` reproduces it whole.

   **That assumption is false for every faction this mod makes playable.** Play the
   Conclave and the filter drops `t4_conclave`, leaving three seats of which the middle
   one is never named by `first` or `last` — it silently vanishes. Play one of the ten
   houses and nothing is filtered at all, so the row holds four seats and the Join still
   draws three: **every house player has been missing a tier-four seat since the mod
   shipped.** There is no log line and no visual gap; the row just renders short.

   Fixed by dropping the `Join` and returning the filtered list itself, in both
   components — the pip row and the seat row must agree or the count lies. `seat_holder`
   is a `HorizontalList` with `sizetocontent="true"`, so it grows to whatever the list
   holds: 4 seats is 4x98 + 3x120 spacing = 752 wide from `offset` 751, ending at 1503
   inside the 1600 clip. **It fits, but the row is anchored not docked**, so a four-seat
   row sits ~109px right of centre. Cosmetic, and not corrected here.

   The mod's own tier five is unaffected — it is a normal district row and uses the
   plain `RitualListForManager(...)` expression at line 6561, not this one.

   Note the shipped copy of this file is **all-LF**, not CA's CRLF; that normalisation
   happened in an earlier edit and re-CRLF-ing it now would rewrite all 11,831 lines for
   nothing.

### Why every seat shows the same banner

`seat`'s `ContextImageSetter` resolves art through

```
Format("dlc23_tower_of_zharr/seat_slot_%s.png",
       RitualContext.CompletionPayloadContext.ConfederatedFactionsList
           .FirstContext.FactionRecordContext.Key.Replace("wh3_dlc23_chd_", ""))
```

with `fallback_to_default` set. CA's CCO reference defines `ConfederatedFactionsList` as "a
list with factions that will be confederated **by this payload**" — so it is populated from
`ritual_payload_form_confederations`, and §4 deliberately **removed those rows** in favour of
a script call in the claim handler (a runtime `cm:create_payload` since 2026-10-10, still not a
DB payload, so the list stays empty). The list is therefore empty for every annex
seat, the `Format` yields nothing, and every annex seat falls back to the same default banner.
The banner a seat draws once CLAIMED is a different file, `claimed_seat_<faction key less
wh3_dlc23_chd_>.png`, keyed by the claimant and resolving per house - §11.

That is the price of script-side confederation, and it is worth knowing before "fixing" the
art: restoring the payload rows would light up the icon path and any other faction-derived
binding, but would also hand the confederation back to the engine, unconditionally.

### There is no horizontal scroll to add

Do not go looking for one. Checked across all five UI packs:

- `district_list` is a `LayoutEngine type="HorizontalList"`, `sizetocontent="true"`, with no
  clip of its own — it simply grows past the panel edge.
- `tier_listview` carries a `vslider` only. The word `hslider` appears in exactly one place in
  the game: the battle speed control (`callback_id="HSlider"`, a min/max value slider, not a
  list scroller). **No `Listview` in WH3 is paired with a horizontal scrollbar.**
- The UIComponent API has no scale. CA's 5,787 scripts use only `MoveTo`, `Resize`,
  `SetDockingPoint`, `SetDockOffset`.
- Shrinking districts to fit 5 needs 296px each, against a `district_title` image of 288px
  flagged `canresizewidth="false"` — 8px of slack and no headroom for a 6th.

If you ever genuinely need more than 16 seats, add a **tier row** (one
`ritual_category_groups` row): the tier list already scrolls vertically and that machinery
works today.

---

## 2. The DB tables a custom seat needs

Thirteen files, all named `derpy_chd_toz_annex`. The row counts are the shipped ones.

| Table | Rows | Purpose |
|---|---|---|
| `ritual_category_groups` | 1 | the tier itself (`toz_tier_5`, `sort_order` 4) |
| `ritual_categories` | 3 | one row per district, `group` = the tier |
| `rituals` | 12 | one row per seat, `category` = its district |
| `ritual_payloads` | 12 | one payload per seat |
| `ritual_payload_effect_bundles` | 12 | gives each payload something to do (table v2 since 9.0) |
| **`campaign_group_rituals`** | **12** | **registers each ritual with a campaign group** |
| `resource_costs` | 1 | the seat cost definition |
| `resource_cost_pooled_resource_junctions` | 1 | −300 conclave influence, **one row for all twelve seats** |
| `effect_bundles` | 54 | tier + district rewards, the usurped-diplomacy bundles, and **24** price-modifier base records (two per seat) |
| `effect_bundles_to_effects_junctions` | 35 | the effects those bundles carry — every *reward* bundle needs at least one; the price-modifier bundles deliberately have none |
| `effects` | 37 | the custom diplomacy effect keys, plus **24** price-modifier effects (two per seat) |
| **`effect_bonus_value_ritual_junctions`** | **48** | **two rows per seat, plus **two** price-modifier rows each — every working vanilla Tower seat has them; see below** |

Counts re-read from the pack 2026-08-20. The last four grew by ten each when per-seat pricing
went in — see "A seat's price is not fixed" below, and by ten again when the annex seats got
their `_usurp_cost_modifier_hidden` records — see "CA prices annex seats too" below.
Re-read off the Workshop pack 2026-10-09 at twelve seats; the thirteenth file, `effect_bonus_value_faction_junctions` (13 rows), is the usurp
penalty's faction binding from §11.

Plus `text/derpy_chd_toz_annex.loc` (181 rows) and `db/incidents_tables/derpy_chd_toz_factions`.

### Two tables get missed, and both fail silently

**`effect_bonus_value_ritual_junctions` is the second one.** Every one of the 31 vanilla
Tower seats carries exactly these two rows; a seat without them renders, prices, reads
`disabled=false` and `script_locked=false`, accepts the click — and `Perform` does nothing:

```
bonus_value_id       effect                                                                    ritual
percentage_cost_mod  wh3_dlc23_effect_technology_chd_conclave_influence_spent_slot_claimed_mod  <ritual>
percentage_cost_mod  wh3_dlc23_effect_toz_chd_conclave_influence_spent_slot_claimed_mod         <ritual>
```

The tier 1-3 district seats carry a third row pointing at a per-seat
`..._usurp_cost_modifier_hidden` effect with its own `effects_tables` entry. The tier-4 lord
seats do not, so custom lord seats need only the two above.

**How to find tables like this:** extract all 1,520 vanilla tables from `data/db.pack` as TSV
and `grep -rl` a known-good key. Everything a working seat is in, yours must be in too:

```
grep -rl "wh3_dlc23_ritual_chd_toz_slot_t4_astragoth" vandb/db/
```

### `campaign_group_rituals` is the one that gets missed

**A ritual absent from `campaign_group_rituals_tables` is present-but-permanently-disabled.**
No script call can override it. All 31 vanilla Tower of Zharr rituals are registered there
under campaign group `wh3_dlc23_chd_ritual_toz`; the mod shipped no such table at all, and
that single omission cost five build-and-test rounds.

```
campaign_group             ritual                              unlock_mission  unlock_turn  initially_unlocked
wh3_dlc23_chd_ritual_toz   derpy_ritual_chd_toz_annex_khorakk                  0            false
```

`initially_unlocked` follows how you intend to gate the tier: vanilla tier-1 seats use
`true`, the tier-4 lord seats use `false` and are opened by script. Ours use `false`.

This is exactly the failure mode `CLAUDE.md` warns about — tracing vanilla rows in RPFM
shows which tables are *wired up*, never which are *missing*. The reliable way to find the
full set: extract `data/db.pack` (1,521 tables) and grep a known-good vanilla key across all
of them.

### A seat's price is not fixed — and varying it takes three tables

Established 2026-08-20. The price on a seat's tooltip is **not** the `resource_costs` number;
it is that number after every `percentage_cost_mod` effect currently on the faction. That is
how a tier-2 seat can read 120 while the seat beside it reads 195.

Vanilla seat costs, in conclave influence, one `resource_cost` row per tier:

| Tier | `resource_cost` key | Amount |
|---|---|---|
| 1 | `wh3_dlc23_chd_ritual_toz_tier1` | −75 |
| 2 | `wh3_dlc23_chd_ritual_toz_tier2` | −150 |
| 3 | `wh3_dlc23_chd_ritual_toz_tier3` | −300 |
| 4 | `wh3_dlc23_chd_ritual_toz_tier4` | −600 |
| 5 (ours) | `derpy_chd_ritual_toz_tier5` | −300 |

**Every ritual pointing at one `resource_cost` key shares one price.** All ten annex seats
point at `derpy_chd_ritual_toz_tier5`, so nothing in DB alone can price them differently.

CA's answer is a hidden per-seat effect driven from script, the `usurp_cost_modifier` pattern.
Reproducing it needs **three** tables per seat, and missing any one fails silently:

| Table | Row |
|---|---|
| `effects` | `<key>` · icon `""` · priority `0` · category `campaign` · `is_positive_value_good` false |
| `effect_bonus_value_ritual_junctions` | `percentage_cost_mod` · `<key>` · `<ritual_key>` |
| `effect_bundles` | `<key>` · `[hidden]` · `[hidden]` · `faction` · … |

Then from Lua:

```lua
local bundle = cm:create_new_custom_effect_bundle(effect_key)
bundle:add_effect(effect_key, "faction_to_faction_own_unseen", percentage)
bundle:set_duration(0)
cm:apply_custom_effect_bundle_to_faction(bundle, faction)
```

Two traps, both of which cost a launch cycle here:

- **`create_new_custom_effect_bundle` takes an `effect_bundles` key, not an `effects` key.**
  The docs say "using the specified effect bundle record as a base". With no matching
  `effect_bundles` row it returns nil, and the failure surfaces one line later as
  `attempt to call method 'add_effect' (a nil value)` — which reads like a wrong method name
  and is not.
- **The base bundle must carry no `effect_bundles_to_effects_junctions` row.** `add_effect`
  supplies the effect at runtime; CA's 27 usurp bundles have no junction rows for this reason.

`percentage_cost_mod` means the value is a **percentage**, so the bundle carries `+100` to
double a price, not `+300` to add 300 influence.

### CA prices annex seats too, and will nil-crash without the records

Established 2026-08-20, from the shipped pack — **not** reproduced in a log; no seat claim of
any tier appears in the 167 `script_log_*.txt` on disk.

CA's `RitualCompletedEvent` handler branches on the *seat*, not the ritual's tier:

```lua
if seat.district_group_key ~= "TOZ_TIER_4" then
    self:usurp_cost_modifier(seat, seat_key)    -- create_new_custom_effect_bundle(seat_key .. "_usurp_cost_modifier_hidden")
```

`zz_derpy_toz_annex.lua` registers the annex seats with `district_group_key` =
`DISTRICTS_ANNEX_T5_A/B/C`, so **all ten take that branch** — the tier-4 exemption does not
cover them, and "lord seats need only the two cost rows" is true of the DB pricing rows but
not of this runtime call. With no `effect_bundles` record the call returns nil and
`add_effect` kills the rest of CA's callback: the 5-turn `lock_ritual` on rivals, the
specialty district modifiers, `district_complete_check` (so the annex district reward never
pays out) and `override_ui("disable_toz_button")`. It fires on **every** annex claim, not
only on a usurp.

Fixed by cloning the ten `_strength_cost_hidden` rows across all three tables
(`effects`, `effect_bundles`, `effect_bonus_value_ritual_junctions`) under the
`_usurp_cost_modifier_hidden` name. `templates/toz_districts.py` now emits both suffixes from
`PER_SEAT_SUFFIXES`, because it rebuilds the junction table from nothing every run.

---

## 3. Naming conventions the engine enforces

These keys are **not** free-form. Get them wrong and the feature fails silently.

### District reward bundle

The panel resolves a district's reward through the `DistrictCompletionEffectBundleContext`
CCO, which derives the key from the category:

```
wh3_dlc23_chd_toz_<lowercase category key>_reward
```

Verified against all nine vanilla district categories. So `DISTRICTS_ANNEX_T5_A` **must**
have `wh3_dlc23_chd_toz_districts_annex_t5_a_reward`. The `effect_bundle_key` you set on
`tower_of_zharr.districts[...]` in script is script-side only — it controls what
`district_complete_check` *applies*, not what the banner *displays*. Both must agree.

### Tier reward bundle

`tower_of_zharr.twui.xml` builds it as `Format("wh3_dlc23_chd_%s_reward", Key)` on the group
key, so `toz_tier_5` → `wh3_dlc23_chd_toz_tier_5_reward`.

---

## 4. Script integration

`script/campaign/<campaign>/mod/zz_derpy_toz_annex.lua`, shipped to all four campaign
folders (`cr_oldworld`, `cr_darklands`, `cr_combi_expanded`, `wh3_main_combi`). The `zz_`
prefix makes it load after the base Tower script, whether that is CA's, this mod's override,
or IEE's.

**Registration** (`add_pre_first_tick_callback`) — writes into the global `tower_of_zharr`:
`tiers[…]`, `districts[…]`, `seats[…]`, `confederation_seat_mapping[…]`, `is_scripted[…]`.
All of these are assigned at file scope in the base script (lines 158–222), so they exist by
the time any pre-first-tick callback runs.

**`tier.total_seats` is ONE number for the whole tier**, and `district_complete_check`
compares `district.complete_counter == tier.total_seats`. Out of the box that means every
district in a tier must hold the same number of seats — an uneven layout either never
completes the small districts or pays the big ones out early.

`zz_derpy_toz_annex.lua` wraps the method so a district may carry its own `total_seats`,
swapping the tier value around the inner call and restoring it after. Districts without one
(every vanilla district) take the original path untouched, and the wrap is guarded on
`type(base_check) == "function"` plus a session-local flag — deliberately not a flag on
`tower_of_zharr`, which is rebuilt from the save on load. That is what lets the current 3/3/2/2
layout work, and it is the piece to keep if the districts are ever re-cut.

**Unlocking** — `cm:unlock_rituals_in_category(faction, category, -1)` (what CA's
`tier_unlocked_check` uses) plus `cm:unlock_ritual(faction, key)` per seat. Neither helps if
`campaign_group_rituals` is missing.

**No locking call.** An earlier version called `cm:lock_ritual` while the gate was unmet.
It defended nothing — before the gate the seats are unreachable anyway, because the panel
builds a tier's district list from the engine-computed `IsTierLocked`, and that only flips on
`cm:unlock_rituals_in_category`. See §6 on `script_locked()`.

**Gating** — `PREREQ_TIER` (one constant) names the tier whose unlock opens this one;
currently `toz_tier_4`, i.e. The Subjugation opens once Tier **Three** is complete —
`tiers[X].locked_status` goes false when X becomes *available*, so the constant names one
tier later than the one you must finish. Polled on `RitualCompletedEvent` (primary), human `FactionTurnStart`
(backstop) and `PanelOpenedCampaign` for the tower; all three call the same idempotent
`try_unlock_annex()`.

**Poll on the claim, not the turn.** The prerequisite only ever changes inside
`tier_unlocked_check`, which is reachable only from the seat-claim path
(`RitualStartedEvent` → `district_complete_check` → `tier_unlocked_check`, base script
line 677 sets `next_tier.locked_status = false`). A `FactionTurnStart`-only poll therefore
lags the unlock by up to a full turn — and a player who finishes Tier Three and keeps
playing that turn never sees The Subjugation open at all. Fixed 2026-08-18; the original
shipped turn-only and was reported from a session that unlocked tiers 2, 3 and 4 inside a
single turn (`wh3_dlc23_chd_toz_new_tier_unlocked_4` at 344s, last turn boundary at 155s).
`RitualCompletedEvent` not `Started`: CA claims on `Started`, so by `Completed` the tier
flip has already happened.

**A house holds its own seat from turn one.** Playing one of the twelve houses, its seat is
pre-claimed at campaign start. Without this the own-house seat is a dead purchase: it
confederates nothing (self) and grants no lord (you already field him). Hiding it instead
would strand its district one seat short forever, because `zzz_derpy_toz_ai_seats` never
claims annex seats — nobody else would ever take it.

The mechanism is CA's own, from `wh2_dlc15_eltharion_lair.lua:400`: on `cm:is_new_game()`, top
up the pooled resource, then `cm:perform_ritual` inside a `cm:callback` with delay 1.

```lua
granted_this_session[ritual_key] = true          -- claim handler must not run, see below
cm:unlock_ritual(faction, ritual_key)            -- perform_ritual needs this one unlocked
cm:faction_add_pooled_resource(faction_name, INFLUENCE, INFLUENCE_FACTOR, 1000)
cm:callback(function()
    cm:perform_ritual(faction_name, "", ritual_key)
    cm:lock_ritual(faction, ritual_key)          -- restore the tier's locked look, §5
    -- then a nested callback subtracts the difference, so influence ends where it started
end, 1)
```

Four things hold it together:

- **`perform_ritual` works while the tier is still locked**, provided that one ritual has been
  `cm:unlock_ritual`ed first. Verified — no refusal in the log.
- **Local faction only.** If every house pre-claimed, all three districts would complete on
  turn one and pay every Chaos Dwarf faction the full tier.
- **Mark `granted_this_session` before performing.** The claim handler must not run here: the
  replacer that installs the custom lord may not have fired yet, so `faction_has_subtype` could
  read false and spawn a duplicate at the capital.
- **Re-lock, and give the stipend back.** Both are covered above and in §5.

**Never confederate a faction with itself.** `cm:force_confederation(X, X)` hard-crashes the
game. Reachable the moment a house is playable and claims its own seat, which is every house in
the Old World campaign. The own-house seat is instead **pre-claimed at campaign start** for the
local faction (CA's own idiom from `wh2_dlc15_eltharion_lair.lua:400`: top up the pooled
resource, then `cm:perform_ritual` in a `cm:callback` with delay 1). Hiding it instead would
strand its district one seat short forever, since the AI never claims annex seats.

**Claim handler — listen on BOTH `RitualStartedEvent` and `RitualCompletedEvent`.** CA's own
Tower script claims seats on Started, and that is what the first version copied. Proven wrong
by an unfiltered probe on 2026-08-18: **the engine raises only `RitualCompletedEvent` for
these rituals**, never Started, so no Lua listener — ours or CA's — ever heard about a
tier-5 claim, even while the seats visibly claimed and their districts read complete. Dedupe
by ritual key so whichever event arrives first wins.

CA documents **five** ritual events and `RitualCompletedEvent` carries a `succeeded` field the
handler does not read — see §9.2.

Two related traps in the same handler:
- Put nothing in the listener **condition** that can throw. The original filter called
  `context:ritual()` there; a throw in a condition drops the listener silently instead of
  surfacing. Use `true` and `pcall` every field read in the body.
- A district reading "District Complete" in the panel is **not** evidence any script ran.
  `IsDistrictComplete` is an engine-side CCO computed from claimed seats in the category; it
  owes nothing to `tower_of_zharr.districts[...].complete_status`.

**A lord switched off in MCT keeps his seat on the panel, locked** (2026-10-03, see
`sessions/HANDOFF_20261003_HLL_MCT_SETTINGS.md`). Each `lord_<subtype>` switch is frozen in
the save at turn one. `apply_lord_switches()` runs at first tick before `try_unlock_annex()`:
it fills `disabled_seat` and sets each annex district's `total_seats` to the seats still on,
so a district completes on what is left rather than stranding one seat short. Then
`unlock_annex_rituals()` calls `cm:lock_ritual` on those seats **after**
`unlock_rituals_in_category`, which would otherwise clear the lock. **Not seen in game:** per
§6.2 a `script_locked` seat may draw an active button that does nothing when clicked.

**Confederation is script-side.** The `ritual_payload_form_confederations` rows were removed
and replaced with a script call in the claim handler, so the outcome can be conditional on the
target existing.

**Since the 2026-10-09 game patch that call is a payload, not `cm:force_confederation`.**
`force_confederation` now returns, raises nothing, and never confederates. Measured live on
2026-10-10 over the wh3-mcp bridge: bare calls on Black Kraken (no pact) and Fists (pact) sat
for 17s+ with nothing in progress, and so did one preceded by CA's own `force_diplomacy(...,
"form confederation", true, true, true)`. `cm:create_payload()` + `form_confederation(absorber,
house, false, false)` + `cm:apply_payload(p, absorber)` landed both in under half a second, and
then Zharrduk through the shipped claim handler. **`FactionJoinsConfederation` fires INSIDE
`apply_payload`**, so the handler parks its lord grant before calling `confederate()`. It used to
park it after, which would now miss the event and leave the grant to the turn-start backstop.
**It is broken for Chaos Dwarfs only, AI or human.** Same save, same session, 20s each: Greenskins
absorbing Crooked Moon (AI to AI) landed in under 5s, while Astragoth absorbing House of Baal
(a `cr_` house) and Astragoth absorbing CA's own `wh3_dlc23_chd_minor_faction` (both AI) never
did. So it is not the human absorber and not the `cr_` factions. What in the patch keys on the
race is not known. The one lead: the same patch added `and data.faction_key ~= owning_faction:name()`
to `crisis_will_of_hashut.lua`, CA's only Chaos Dwarf `force_confederation` call, which could
self-confederate and crash. A matching engine-side guard scoped too wide would explain this,
and CA's own fixed crisis line would then be dead too.

---

## 5. What the panel will and will not let you do

From `ui3.pack → ui/campaign ui/tower_of_zharr.twui.xml` (405 KB).

- **Tier 4 is pinned above everything.** The ladder is
  `DatabaseRecords("CcoRitualCategoryGroupRecord").Filter(Key.Contains("toz_tier_") && Key != "toz_tier_4").Sort(SortOrder, true)`,
  and tier 4 is drawn separately via `DatabaseRecordContext(…, "toz_tier_4")`. A fifth tier
  therefore renders *below* tier 4 no matter what `sort_order` you give it. `toz_tier_4`
  appears 21 times in that file; tiers 1, 2, 3 and 5 appear zero times.
- **Tier 4's unlock text is generated from that same filtered ladder** via `NextContext`, so
  adding a tier makes The Conclave advertise "complete 2 Districts in The Subjugation".
- **One row per district, and vanilla never exceeds four seats in one.** Ten seats in a
  single district overflow and scatter across the screen. Two districts of five lay out
  correctly.
- **`IsTierLocked` is engine-computed** on the group record. There are no `ScriptState`
  references in the panel at all, and `update_shared_states` only ever publishes
  `is_toz_tier_2_unlocked` / `is_toz_tier_3_unlocked`.
- **`top_tier_bull_head` lands on the seats, and the offset that fixes it can only be measured.**
  Fixed 2026-08-19, confirmed in game; the crest now crowns the tower with The Conclave's title,
  unlock line and seats all clear. It cost four builds, and every one of them failed the same
  way — a number derived from the file instead of from the panel.

  The 1099×834 crest (`dlc23_tower_of_zharr/top_tier_bull_head.png`) lives in
  `statues_and_effects`, which is docked **`Bottom Center`** of `tower_holder`, and
  `tower_holder` carries `ResizeToFitTarget` on `tier_list_holder`. Every decoration in that
  holder is therefore measured **up from the bottom of the tower**. Adding a tier makes the
  tower taller by that tier's own row, so the crest drops by exactly that much — onto **The
  Conclave's** seats, since tier 4 is pinned topmost and the fifth tier renders directly under it.

  **The fix is one attribute: `dock_offset="0.00,-1565.00"`** (`offset` moves to `250,518` to
  match, keeping the design-time twin in step). That is CA's `-604` minus **961** — the row The
  Subjugation adds, `829` high plus the list's `132` spacing.

  **The panel's real geometry.**

  Logged from `tier_list_holder`'s children with `Position()` y and `Dimensions()` height. These
  are the numbers that ended the guessing:

  | child | id | y | h |
  |---|---|---|---|
  | 0 | `tier_top` | -2760 | 327 |
  | 1 | `template_tier` | -2541 | 462 — `vis=false` |
  | 2 | `CcoRitualCategoryGroupRecordtoz_tier_5` | -2353 | **829** |
  | 3 | `…toz_tier_3` | -1392 | 572 |
  | 4 | `…toz_tier_2` | -688 | 697 |
  | 5 | `…toz_tier_1` | 141 | 829 |

  Crest before the fix: `y=-2516`, size `1099x834`. Four findings fall straight out of that.

  **The panel runs 1:1.** The crest reports its authored `1099x834`, so screen pixels *are* twui
  units here — which is what lets a measured pixel value go straight into `dock_offset`. And the
  dock chain solves exactly: `tower_bottom = -2516 - 35 + 2500 + 604 + 417 = 970`, which is tier
  1's bottom (`141 + 829`) to the pixel. The model was always right; only its input was wrong.

  **Nothing in the twui yields the row height.** `template_tier`, `district_list` and
  `seats_list` are all `sizetocontent`, so the authored heights in the file are design-time
  leftovers — `template_tier` says 462 where the panel lays out 829. Every attempt to compute
  the offset from the file was doomed before it started.

  **Tier rows are not a common height** — 829, 572, 697, 829, because a district is as tall as
  its seat count. There is no single "row pitch": a median gap over the rows picks 704 (tier
  3's) where the row that was actually added is 961. **Anything else assuming uniform tier
  heights has the same bug**, `total_seats` arithmetic (§4) included.

  **A dynamic list keeps its template as a child** alongside the instantiated rows — child 1
  above, `vis=false`. So `Find(1)`/`Find(2)` are *not* two adjacent tiers. That pairing measured
  188px and moved the crest almost nowhere. Filter children on `Visible()` before using them.

  **Re-deriving the offset after a CA patch.**

  The row heights change with seat count, so a patch or a district re-cut moves this number.
  Drop this probe into the `PanelOpenedCampaign` handler, read the log, then delete it:

  ```lua
  local list = find_uicomponent(core:get_ui_root(), "tower_of_zharr", "tier_list_holder")
  for i = 0, list:ChildCount() - 1 do
      local row = UIComponent(list:Find(i))
      local _, rh = row:Dimensions()
      local _, ry = row:Position()
      out("row "..i.." "..row:Id().." y="..ry.." h="..rh.." vis="..tostring(row:Visible()))
  end
  ```

  Run it a tick late (`cm:callback(..., 0.1)`) or the layout has not settled and `Position()`
  reads pre-layout values. New offset = CA's `-604` minus (our row's `h` + the gap to the row
  below it).

  **A script-side reposition was tried and dropped.** `raise_bull_head()` did the same
  measurement on every panel open and `MoveTo`'d the crest, which is self-scaling and would
  survive a sixth tier without an edit — but the final version threw inside its own `pcall`
  between dumping the rows and the next log line, leaving the crest unmoved and the failure
  invisible. A decoration is not worth debugging a silent throw when the constant it computes
  is already known. If you revive it, log the `pcall` error.

  Checked against `campaign/uicomponent.html`: `Position()` and `MoveTo()` are both **absolute
  screen pixels** from the top-left of the window, `Dimensions()` is the component's own size,
  `Bounds()` includes children, `Find(i)` is 0-based, `Id()` returns the component name.
- **A locked tier's greyed, price-less look is a component state, not something you draw.**
  `template_tower_district` carries a `ContextStateSetterConditional` whose `locked` state is
  bound to `IsDistrictLocked` (line 8250). Restore that state and the panel renders the tier
  correctly gated on its own; hiding components to fake it is both more work and wrong — a
  gated tier is supposed to be *visible*, showing its "Unlock this tier by…" line.
- **Unlocking a single ritual un-gates the whole tier's appearance.** `IsDistrictLocked` goes
  false as soon as one ritual in the category is unlocked, so any script that unlocks one seat
  early must lock it again afterwards or the tier advertises itself with full prices from turn
  one. See §4 on pre-claiming.

---

## 6. How to diagnose a seat that will not work

Work down this list in order. Every one of these failed silently with the panel looking fine.

### 6.1 The seat does not appear at all

`cm:unlock_rituals_in_category(faction, category, -1)` is what flips the engine's
`IsTierLocked` and makes a tier's district list render. Per-ritual unlocks alone do not.

### 6.2 Two flags, not one

```lua
local status = faction:rituals():ritual_status(ritual_key)
status:disabled()        -- DB validity / engine availability
status:script_locked()   -- cm:lock_ritual / cm:unlock_ritual -- a DIFFERENT flag
```

`ritual_status` returns a **`RITUAL_STATUS_SCRIPT_INTERFACE`, and CA's own note is that "the
result of this call is a bit mask and needs to be checked accordingly"** — several of its
predicates can read true at once. There are nineteen, not two:

```
is_null_interface  available  disabled  cannot_afford_resource_cost
unlock_mission_not_completed  chain_locked  prior_chain_stages_incomplete
already_completed_in_chain  on_cooldown  chain_locked_by_another_faction
reaction_constraints_not_met  not_enough_slaves  no_available_ritual_sites
script_locked  war_declaration_required  invalid_performing_characters
invalid_target  blocked_by_pending_battle  blocked_by_pending_action
```

`available()` is the single summary check the probe never used; the rest name the reason.

A seat can read `disabled=false`, render, price, accept the click and still refuse to perform
because it is `script_locked`. Always probe **both**, and always alongside a vanilla control
(`wh3_dlc23_ritual_chd_toz_slot_t1_industry_1` and `…_t4_astragoth`) to prove the probe itself
is sound. `initially_unlocked = false` in `campaign_group_rituals` means `script_locked` starts
`true` — that is normal, vanilla's tier-4 seats read the same.

**Affordability is not invisible — that was wrong.** `status:cannot_afford_resource_cost()`
is on the same interface and answers it directly. The pooled-resource read below is still
useful for logging the actual number, but it is not the only way to see the condition:
`faction:pooled_resource_manager():resource("wh3_dlc23_chd_conclave_influence"):value()`.

### 6.3 The button clicks but nothing happens

The panel's `claim_seat_button` gates on `CanPerformRitual` and fires `Do(Perform, …)`. A
button logging `state: [down]` (not `inactive`/`down_off`) means `CanPerformRitual` was true
and `Perform` ran — so the fault is in the ritual's data, not the UI.

At that point **stop theorising and diff against vanilla**:

```
grep -rl "wh3_dlc23_ritual_chd_toz_slot_t4_astragoth" vandb/db/
```

Every table a working seat appears in, yours must appear in too. That is how
`effect_bonus_value_ritual_junctions` was finally found, after cost, `disabled`,
`script_locked`, `cooldown_time`, empty payload bundles and the panel XML had all been
investigated and cleared.

### 6.4 The seat claims but no script runs

Check the event. **These rituals raise only `RitualCompletedEvent`, never
`RitualStartedEvent`** — see §4. And note that a district reading "District Complete" in the
panel proves nothing about script: `IsDistrictComplete` is an engine-side CCO.

If you need to know what the engine actually raises, attach a listener with condition `true`
to both ritual events and log `context:ritual():ritual_key()` unfiltered. That is what settled
it; it is noisy, so strip it once answered.

**One marker in this build is dead, and its absence proves nothing.** CA's `RitualCompletedEvent`
handler carries `out("XXX derpy_toz_seat ...")`, and that string appears in **zero** of the 167
`script_log_*.txt` on disk — including runs where seats demonstrably changed hands. The line sits
in a copy of `wh3_dlc23_campaign_chd_tower_of_zharr.lua` that the game does not run. Do not read
its absence as "the handler never fired". The reliable proof a claim completed is the **5-turn
`script_locked` appearing on the rivals**: `cm:lock_ritual(faction, seat_key, 5)` runs inside that
same handler, so a seat flipping `AVAILABLE -> script_locked` for everyone except the claimant is
the handler's own signature.

Ruled out during this build, so do not chase them: **cost** (vanilla tier 4 costs 600 and
reads enabled at 82 influence), a **confederation payload aimed at a missing faction**,
`ritual_chains`, `ritual_flag_sets`, `ritual_ownership_content_pack_junctions`, and the
`rituals_tables` schema version (ours is 4, matching vanilla).

## 7. Mistakes made getting here

Recorded because each cost a real test cycle.

1. **`cm:get_faction` returns boolean `false`, not `nil`.** I wrote
   `(f ~= nil) and (not f:is_null_interface())`; `false ~= nil` is true, so it indexed a
   boolean and threw. Because CA's `call_each` runs first-tick callbacks with **no pcall**,
   that one throw cancelled every first-tick callback queued after it — including an
   unrelated script of the mod's own — with **no error in the log**, since nothing caught it.
   Found by diffing a working log against a broken one and locating where the expected
   output stopped. Non-trivial first-tick bodies are now wrapped in `pcall`.
2. **Diagnosed the disabled rituals as a confederation-payload problem.** Removed the
   payload table; nothing changed. The real cause was `campaign_group_rituals`. The
   payload removal was kept because script-side confederation is genuinely better, but the
   reasoning that led there was wrong.
3. **Assumed affordability might disable a ritual.** It does not.
4. **Splitting one district into two silently broke the reward display.** Renaming the
   category from `DISTRICTS_ANNEX_T5` to `…_T5_A`/`…_T5_B` invalidated the derived bundle
   name, so both banners lost their effect line. The naming contract in §3 is now commented
   in the script so a future rename can't repeat it.
5. **Assumed the empty tier was only about missing factions.** It rendered empty because its
   *district* never reached the UI, which the log proved (`DISTRICTS_ANNEX_T5` appeared zero
   times while `toz_tier_5` appeared).
6. **Polled the tier gate on the wrong event.** `FactionTurnStart` looked like the obvious
   "check periodically" hook, but the thing being checked changes on a seat claim, not on a
   turn. Cost a full playtest. The rule that would have caught it: poll the event that
   *causes* the state change, and only add a turn poll as a backstop.
7. **The staged source under `Modding Files/pack/` went stale.** Every edit of that session
   went into the pack through the RPFM MCP server and none of it back to
   `pack/script/campaign/mod/zz_derpy_toz_annex.lua`, which still held the pre-session
   3.3 KB single-district version. The live 17 KB script existed only inside the `.pack`.
   Recoverable — pack Lua is stored uncompressed, so
   `data.find(b"-- Tower of Zharr: the Subjugation tier")` carves it straight out of the
   binary without RPFM — but check the staged copy against the pack before trusting it.
   Note also that the staged path is flat (`script/campaign/mod/`) while the pack ships four
   campaign folders; nothing ships from the flat path.
8. **Copied CA's claim event without checking it.** CA's Tower script claims on
   `RitualStartedEvent`, so the handler did too. The engine raises only
   `RitualCompletedEvent` for these rituals. Weeks of "the claim does nothing" were partly
   this — and it was invisible because the seats *did* claim, engine-side.
9. **Put a throwing call in a listener condition.** The claim filter called
   `context:ritual()` inside the condition. A throw there drops the listener silently rather
   than surfacing an error, so it looked identical to "the event never fired".
10. **Read "District Complete" in the panel as proof the script ran.** It is not.
    `IsDistrictComplete` is engine-side and independent of
    `tower_of_zharr.districts[...].complete_status`.
11. **Trusted `cm:force_confederation` to hand over the lord.** It completed, the engine raised
    `FactionJoinsConfederation`, and the player still had neither absorbed legendary lord.
12. **Confederated a faction with itself.** The claim handler never checked that the seat's
    house was not the claimant's own. `cm:force_confederation(X, X)` hard-crashes the game, and
    it became reachable the instant a house was made playable.
13. **Hid a component instead of restoring the state that drives it.** Asked to make the gated
    tier *look* locked, the first attempt was `SetVisible(false)` on the whole tier group —
    which removed it rather than gating it. The panel already had the answer: re-lock the
    ritual and `IsDistrictLocked` renders it correctly. Reach for the existing state binding
    before drawing over the UI.
14. **Read a working screenshot as proof of more than it showed.** "District Complete" and a
    claimed banner are engine state; they said nothing about whether any of the mod's Lua had
    run. Two rounds were spent on the wrong half of the problem because of it.
15. **Derived a layout offset from the `.twui.xml` four times instead of measuring the panel
    once.** The bull-head crest sat on the seats, and every fix reached for a number in the
    file: `-1308` from the tower art's storey height (and the *screen-scaled* value at that,
    where `dock_offset` is in design units); then a script that measured `Find(1)` and
    `Find(2)`, which are the dynamic list's hidden template and the first real row; then one
    that took the median row gap, when rows are 829/572/697/829 and the only row that matters
    is the one the tier added. One probe dumping `Id()`/`Position()`/`Dimensions()` for every
    child — which should have been build one — gave the answer and three findings besides
    (§5). **A `sizetocontent` component's authored size is a design-time leftover; if a number
    decides where something lands on screen, read it off the running panel.**
16. **Wrapped a decoration in `pcall` and logged nothing when it threw.** The final script
    version raised the crest correctly in principle and threw silently mid-function, so the
    crest simply stayed put and the log showed only the lines before the throw. The `pcall`
    was right — decoration must not take the gate check down — but `local ok, err = pcall(f)`
    with the error logged costs one line and would have named the fault immediately.
17. Assorted PowerShell self-inflicted noise: `$Args` and `$s` collide with automatic
   variables; `@(...)` around a `Where-Object` result that may return a single string, or
   `[0]` takes a character; array-of-arrays flattening when splicing lines.
18. **Made mistake 1 again, in the same file, on 2026-08-20.** Added an unguarded
    `cm:add_first_tick_callback` for seat pricing, placed *above* `preclaim_own_seat`'s own
    callback. It threw, `call_each` swallowed it, and every later first-tick callback died —
    so a house's own seat went back on sale to itself with nothing in the log but silence.
    The tell was comparing two runs: the file logged its status probes before the change and
    stopped at `registered toz_tier_5` after. **Any new first-tick callback in this file wraps
    its whole body in `pcall` and logs `err`** — not as defence, but because without it a throw
    is indistinguishable from code that was never written.
19. **Concluded "CA ships no such rows" from a search that had silently returned nothing.**
    A dependency query without `rebuild_dependencies: true` answers *empty*, not *error*. On
    that basis I decided CA's usurp effects had no `effect_bundles` records and skipped
    creating my own; there are 27. Costed a launch cycle and produced a confidently wrong
    paragraph. An empty result from a key that certainly exists is a broken query, not data.

---

## 8. Status and remaining gaps

### Confirmed working in game, IEE, 2026-08-18

The whole feature, on three playable custom lords and their factions:

| Lord | Faction | Route in |
|---|---|---|
| Ghorth | `wh3_dlc23_chd_conclave` | start replacer |
| Abnagg | `cr_chd_warfleet_of_uzkulak` | start replacer |
| Black Dwarf | `cr_chd_slaves_of_the_black_dwarf` | start replacer (added this session) |

- Tier renders, gated correctly, unlock incident fires.
- All ten seats claim (`script_log_180826_1110.txt`): ten `CLAIM` lines, ten
  `RitualCompletedEvent`.
- Eight GRANT seats spawned their lord at the capital at level 15 with no upkeep.
- Two ANNEX seats confederated their real IEE factions (`FactionJoinsConfederation` at 371.8s
  and 373.9s).
- Districts complete and their reward bundles apply.
- Own-house seat pre-claimed at start with the influence balance untouched
  (`preclaimed … (influence 45 -> 45, stipend returned)`), and the tier still reads locked
  until Tier Three completes.

### Confirmed working in game, Old World, 2026-08-20

**AI participation works, and the census proves *why*.** `zzzz_derpy_toz_debug.lua` probes each
rostered faction against a real open seat at first tick. All fourteen returned
`cannot_afford_resource_cost` — not `STATUS NULL`, not `disabled`, not `script_locked`. That
distinction is the whole answer: the seats are correctly registered for every faction and the
only thing holding the AI back at turn 1 is 120 influence it does not have yet. From turn 10 it
buys: eleven claims across tiers 1 and 2 in one run.

**Per-seat pricing is live.** Thirteen factions priced at first tick, ordered exactly as their
strength ranks demand — Astragoth at rank 116 pays base for all ten houses, Zhatan at rank 438
pays above base for all ten, and every faction between them lands monotonically in between.
Spot-checked: Black Dwarf at rank 276 is outranked by exactly six of the ten houses, and the
log says 6.

**AI usurping works.** Verified 2026-08-20 over turns 27–30: nine usurps, five of them tier one,
by eight different factions, with zero script errors in 4.2 MB of log. Full write-up in §11.

### Known-incomplete

- **The price per rank is a live-tuned guess.** It started at 3, which put half the roster at the
  200% ceiling — campaign ranks span roughly 100–450, so at 3%/rank anything 67 ranks apart
  maxes out and the curve collapses to base-or-900. Dropped to 1 on 2026-08-20, where the
  ceiling needs a 200-rank gap. Not yet observed in game at the new value. Since 2026-10-03
  both numbers are MCT settings, `toz_annex_pct_per_rank` (default 1) and `toz_annex_max_pct`
  (default 200), read live; the `PCT_PER_RANK` / `MAX_PCT` constants are gone.
- **A claimed seat stays claimable until its ritual completes.** `seat.current_owner` is only
  set on `RitualCompletedEvent`, so between paying and finishing, a seat still reads free.
  Three AI factions bought `t2_industry_1` in one run and one faction bought `t2_industry_3`
  twice. Fixed in `zzz_derpy_toz_ai_seats.lua` by excluding any ritual key found in
  `faction:rituals():active_rituals()` across the roster — stateless, so nothing to persist
  across a save. Not yet re-observed in game.
- **`derpy_toz_tier` never logs** even though tier 2 demonstrably opens mid-campaign. The
  unlock is reaching the panel by a path that skips that `out()`. Unexplained.

- ~~**The deferred lord grant on ANNEX seats is still unexercised.**~~ **Resolved
  2026-08-19, then corrected 2026-08-30.** `script_log_190826_0650.txt`, playing
  `wh3_dlc23_chd_conclave`: all ten seats claimed, all ten logged `annexed <faction>` followed
  ~1.2s later by `… already serves wh3_dlc23_chd_conclave (confederation delivered him) - no
  spawn`, read at the time as proof the `faction_has_subtype` guard worked and no duplicate lord
  was created. **That held for this one log, not in general.** `cm:force_confederation` is
  asynchronous — measured elsewhere at ~11.5s between the call and `FactionJoinsConfederation`
  landing, not the ~1.2s this session assumed — and the guard's `cm:callback(…, 1)` check ran
  ~10s before the absorbed characters existed, so across the full log set it read false and
  spawned a duplicate lord on most claims (57 spawns vs 26 suppressions in 470 logs — it only
  ever worked on a re-open, never on the claim itself). Fixed by parking the grant in a
  `pending_grants` table, drained on `FactionJoinsConfederation`, with a `FactionTurnStart`
  backstop. See `HANDOFF_20260830_TOZ_TIER4_SEATS.md` §7. Since 2026-10-10 the annex is a
  payload, not `force_confederation` (a no-op for Chaos Dwarfs after the 10-09 patch), and
  `FactionJoinsConfederation` fires synchronously inside `apply_payload`, so the grant is parked
  before the call (§4).
- **`RitualCompletedEvent.succeeded` is not checked.** See §9.2. An unsuccessful completion
  would annex the house anyway. One `pcall`ed field read to close.
- ~~**Old World / Darklands untested.**~~ **Resolved 2026-08-20.** Launched from
  `cr_oldworld`; own-seat pre-claim confirmed on two different houses
  (`preclaimed derpy_ritual_chd_toz_annex_horns for cr_chd_horns_of_hashut`, and the same for
  `black_dwarf`), each with the influence balance returned untouched.
- ~~**AI seat claiming** attaches and reports its seat count; no AI claim observed.~~
  **Resolved 2026-08-20**, see below.
- **Multiplayer untested.** Iteration order is deterministic (ordered tables, sorted keys,
  `cm:random_number`), and the pre-claim is local-faction-only, which is untested with two
  Chaos Dwarf players.
- **Save compatibility.** `add_loading_game_callback` backfills saves made before the tier
  existed and `try_unlock_annex` re-asserts the ritual unlock once per session, but no save has
  been carried across a version of these changes.
- **The tower background art still does not extend to a fifth tier** — masonry, torches and
  statues are authored for four. The bull-head crest above it *is* fixed (§5, `dock_offset`
  `-1565`, confirmed in game 2026-08-19).
- **Tier 4 renders above tier 5**, and The Conclave's unlock text references The Subjugation.
  Both are consequences of §5 and only go away by folding the seats into `toz_tier_4`.

## 9. Checked against CA's scripting docs

Everything below was verified on 2026-08-19 against CA's own WH3 scripting reference, mirrored
offline at `Modding Files/reference/ca_script_docs_wh3/` (`scripting.txt` for the terse command
list, `campaign/episodic_scripting.html` for the full `cm:` signatures, `scripting_doc.html` for
the model interfaces and event contexts, `cco/documentation.html` for the UI context objects).

**Confirmed correct.** Every `cm:` call this feature relies on is documented and used with the
right signature: `perform_ritual(performing_key, target_key, ritual_key)` — the empty middle
argument really is "target faction, assumed self if empty"; `force_confederation(proposing_key,
target_key)`; `faction_add_pooled_resource(faction_key, resource_key, factor_key, amount)`;
`unlock_ritual` / `lock_ritual` / `unlock_rituals_in_category`; `is_new_game`. The `-1` passed
to `unlock_rituals_in_category` is documented behaviour, not a hack: the third argument is a
duration in rounds and **"zero or negative will be infinite"**. `faction:rituals():ritual_status()`
is real, on `FACTION_RITUALS_SCRIPT_INTERFACE`. `RitualContext.DisplayName` is real, on
`CcoRitualRecord`.

### 9.1 Four irregularities the docs exposed

| # | What this file said | What CA's docs say |
|---|---|---|
| 1 | "Affordability is invisible to both flags" (§6.2) | **Wrong.** `cannot_afford_resource_cost()` sits on the same `RITUAL_STATUS_SCRIPT_INTERFACE`. Corrected in §6.2. |
| 2 | Two status flags, `disabled` and `script_locked` | **Nineteen**, and CA notes the result "is a bit mask and needs to be checked accordingly". `available()` is the summary the probe never used. Listed in §6.2. |
| 3 | "Listen on BOTH `RitualStartedEvent` and `RitualCompletedEvent`" (§4) | Correct as far as it goes, but there are **five** ritual events — `RitualEvent`, `RitualStartedEvent`, `RitualCompletedEvent`, `RitualCancelledEvent`, `RitualsCompletedAndDelayedEvent`. See 9.2. |
| 4 | "No locking call" (§4) | `cm:lock_rituals_in_category(faction, category)` is the documented inverse of the unlock, and is not used anywhere. The pre-claim re-lock instead calls per-ritual `cm:lock_ritual` five times. |

### 9.2 `RitualCompletedEvent` carries `succeeded`, and the handler ignores it

This is the one open defect the cross-check turned up.

```
RitualCompletedEvent
    succeeded              (no interface)  Whether the ritual completed successfully or not
    performing_faction     FACTION_SCRIPT_INTERFACE
    ritual_target_faction  FACTION_SCRIPT_INTERFACE
    ritual                 ACTIVE_RITUAL_SCRIPT_INTERFACE
```

`zz_derpy_toz_annex.lua:727` registers `on_annex_claimed` for both ritual events with the
condition `true` (correct — see §4 on conditions that throw) and the body never reads
`succeeded`. A ritual that completes **unsuccessfully** therefore annexes the house anyway.
No such case has been observed, and it may not be reachable for these rituals, but the check
costs one `pcall`ed field read and is the difference between "not observed" and "cannot happen".

`ACTIVE_RITUAL_SCRIPT_INTERFACE` — reachable as `context:ritual()` — also exposes more than the
handler uses: `ritual_key`, `ritual_category`, `ritual_chain_key`, `is_part_of_chain`,
`target_faction`, `cast_time`, `cooldown_time`, `expended_resources`, `slave_cost`,
`ritual_sites`, `ritual_target`, `characters_who_performed`. `ritual_category()` in particular
would let the claim handler filter to the annex categories without maintaining its own key
table.

### 9.3 Two things the docs do NOT cover

- **Interface or key, depending on the call.** `lock_ritual`, `unlock_ritual`,
  `lock_rituals_in_category` and `unlock_rituals_in_category` all take a
  `FACTION_SCRIPT_INTERFACE`. `perform_ritual`, `force_confederation` and
  `faction_add_pooled_resource` all take a **faction key string**. The shipped code gets this
  right everywhere, but nothing in the docs flags the split and the two are silently
  interchangeable to Lua.
- **None of the Tower's own CCO properties are documented.** `IsTierLocked`,
  `IsDistrictLocked`, `IsDistrictComplete`, `IsSeatClaimed` and `IsSeatClaimedByPlayer` appear
  nowhere in `cco/documentation.html` — they are DLC23-specific and undocumented, so
  `tower_of_zharr.twui.xml` stays the only source of truth for them. The generic ones
  (`ConfederatedFactionsList`, `CompletionPayloadContext`, `DisplayName`) **are** documented,
  and §5 leans on that.

---

## 10. Where things live

```
db/…/derpy_chd_toz_annex              the thirteen tables in §2
db/campaign_group_members_tables/derpy_chd_toz_ai                    13 rows, §11
db/campaign_group_member_criteria_factions_tables/derpy_chd_toz_ai   13 rows, §11
db/incidents_tables/derpy_chd_toz_factions      3 per tower faction (seat_claimed / usurping / usurped_by)
db/effect_bonus_value_faction_junctions_tables/derpy_chd_toz_annex   13 rows, §11
text/derpy_chd_toz_annex.loc          189 rows
ui/campaign ui/tower_of_zharr.twui.xml   CA's panel, 3 edits / 5 hunks — NOT required (§5)
script/campaign/<campaign>/mod/
    zz_derpy_toz_annex.lua            registration, gating, unlock, claim handler, lord grant,
                                      per-seat strength pricing
    zzz_derpy_toz_ai_seats.lua        AI seat claiming, all four campaigns
    zzzz_derpy_toz_debug.lua          AI participation diagnostics, read-only (§6); silent
                                      unless the MCT switch toz_debug_log is on
script/campaign/mod/derpy_hll_settings.lua   the MCT settings both of the above and the
                                      annex read (derpy_hll_setting); page in
                                      script/mct/settings/derpy_hll.lua
    wh3_dlc23_campaign_chd_tower_of_zharr.lua   CA's script + mod edits, cr_ only
    oldworld_…_tower_of_zharr.lua     seats the eleven cr_chd factions + the Overlords, cr_ only
    cr_iee_campaign_chd_tower_of_zharr.lua      same for IEE, plus the Conclave
    derpy_toz_factions.lua            wh3_main_combi only: seats the Conclave and the Overlords in IE
Modding Files/templates/toz_districts.py   regenerates all six district tables from one list
```

**Edit districts in `toz_districts.py`, not by hand.** It rebuilds `ritual_categories`,
`rituals`, the cost junction, `effect_bundles`, `effect_bundles_to_effects_junctions`, the loc
and the `effect_bonus_value_ritual_junctions` rows from a single `DISTRICTS` list, and purges
rows for any district you remove. The Lua's `ANNEX_DISTRICTS` must be kept in step with it;
since 2026-10-03 `gen_new_house_lords.check_annex_lua()` fails when any of its four copies
drifts from the list, and `gen_victory_routes.py` reads its annex groups out of that Lua.

> **Know which of those it regenerates from nothing.** `effect_bonus_value_ritual_junctions` is
> rebuilt from an empty list every run, so a row that is not emitted by the script is deleted —
> which is how the ten per-seat pricing rows would have vanished at the next district edit, with
> no error and no symptom beyond seats quietly reverting to a flat price. The script now emits
> them (30 rows: two cost effects plus one strength modifier per seat, verified 2026-08-20).
> `effect_bundles` is add-only and `effects_tables` is not touched at all, so their pricing rows
> survive — meaning a new seat needs those two added by hand.
>
> It also needs a `templates/cur/` directory holding the current tables exported as TSV; it
> reads from there, not from the pack.

Reference material for further work: CA's scripts are in `data/data_script.pack` (5,787 files),
all 1,520 vanilla DB tables in `data/db.pack`, the panel in `ui3.pack`. All mod-side logging
greps with a single token: `XXX derpy`.

---

## 11. Who else competes for seats — the AI, and how to add more

Written 2026-08-19, **verified in game the same day** (`script_log_190826_2157.txt`).

### The gate is campaign group membership, not the tower faction list

`tower_of_zharr.factions` is bookkeeping — it drives the post-claim 5-turn lock on rivals, the
usurp diplomacy penalty, the seat-claimed incidents and the tier-unlock loop. It does **not**
decide who may perform a seat ritual. That is:

```
db/campaign_group_members_tables                      id / group / priority
db/campaign_group_member_criteria_factions_tables     member / context / faction
```

Vanilla has exactly three members of group `wh3_dlc23_chd_ritual_toz`:
`wh3_dlc23_chd_astragoth`, `wh3_dlc23_chd_zhatan`, `wh3_dlc23_chd_legion_of_azgorh`. No culture
or subculture criteria rows exist, so **no other Chaos Dwarf faction touches the tower** — not
the Conclave, not minors, not the ten houses. Playing one of the three leaves exactly two
competitors, and that is the whole of vanilla's competition.

A faction that IS a member needs no script: **the engine's ritual AI claims and usurps on its
own.** Usurping falls out of the same behaviour — a seat that already has an owner is still a
castable ritual, just a dearer one.

### The wrong turn worth not repeating

`cai_ritual_policy_to_category_junctions` has a single row, `STANDARD_RITUAL → default`, and it
is tempting to read that as an allowlist of what the AI may cast — which would mean panel
mechanics are AI-invisible. **It is not an allowlist.** It overrides cast cadence for that one
category (5–11 rounds against the 5–25 default in `cai_ritual_variables`); STANDARD_RITUAL holds
the 50 WH2-era race rituals and nothing else. The AI casting ToZ seats was reported from a live
campaign while this file's author was arguing from that table that it could not happen.

`ToZ_ai_boost` (CA's script, `:596`) is **culture**-gated, not membership-gated: every non-human
`wh3_dlc23_chd_chaos_dwarfs` faction banks +7 conclave influence a turn after turn 10. Conclave
influence is expended by 31 rituals and every one is a ToZ seat, so a non-member AI accumulates
it forever and spends none. The houses were funded long before they were permitted.

### What was added

Eleven members — the ten houses plus `wh3_dlc23_chd_conclave` — as `derpy_toz_<slug>`, each with
one `ACTOR` criteria row. Source TSVs in `Modding Files/templates/toz_ai_members/`. Nothing else:
no Lua, no changes to CA's script.

**Membership is not the whole of it: the faction must also be in `tower_of_zharr.factions`.**
Tiers 2-4 unlock, the annex tier unlocks, the claim locks and the AI seat script all walk that
list. The cr_ campaigns' tower override hardcodes the Conclave into it; IE and IEE run CA's
unmodified script, whose list is Astragoth, Azgorh and Zhatan only, so until 2026-09-24 the
Conclave was a DB member there and still got none of those. `derpy_toz_factions.lua` (IE) and
`cr_iee_campaign_chd_tower_of_zharr.lua` (IEE) now seat it, pre-first-tick. A save started
before that is seated on load but does not get back tiers that opened before it.

**2026-09-25: the Overlords of Zharrduk (`wh3_dlc23_chd_minor_faction`) joined, the twelfth
member.** Both gates: member `derpy_toz_zharrduk` + `ACTOR` criteria row, and the guarded
Lua lists in all four campaigns (the cr_ campaigns through `oldworld_…`, not the hardcoded
override list, because a hardcoded absent faction breaks CA's unguarded `is_human()`). CA's
tower script also keys three incidents and one usurp bundle **by faction name**
(`…_seat_claimed_<f>`, `…_usurping_<f>`, `…_usurped_by_<f>`,
`…_diplomacy_mod_toz_usurped_<f>`), so a new tower faction needs those too, cloned from
Khorakk's. It had no annex seat of its own until 2026-10-03 (Kharkadon's Bloodline seat, suffix
`zharrduk`; the 2026-10-06 rename to `derpy_kharkadon` changed his subtype key, not the faction
slug or the ritual key) and no seat art: the panel looks for
`dlc23_tower_of_zharr/claimed_seat_minor_faction.png`. The `cr_chd_*` houses' seat art ships
with IEE or the Old World campaign mod, which those factions need anyway, so only a faction
neither covers needs a banner from this pack. (2026-10-03: the Uzkul Mingol Company, the
thirteenth member, `derpy_toz_skullstack`, now ships its
three files, drawn from its own flag by `tools/make_toz_seat_banner.py`, and so do the Overlords
(cloth = `banner_colour_primary`, device = `banner_colour_secondary`, measured on every shipped seat); the Khorakk/Overlords seats
swapped districts the same day - see `sessions/HANDOFF_20261003_NEW_HOUSE_LORDS.md` §10.)

**A usurp penalty needs a faction junction, or it is text only.** The usurp bundle's
diplomacy effect only applies through an `effect_bonus_value_faction_junctions` row
(`diplomatic_mod`, effect, faction) - CA has one per lord. Until 2026-09-25 the ten houses' and
the Conclave's `derpy_faction_political_diplomacy_mod_*` effects had none, so the -10 their
incident promised never happened. All twelve now have one, in
`db/effect_bonus_value_faction_junctions_tables/derpy_chd_toz_annex`.

### Verified

Turn one of `cr_oldworld`, playing the Conclave, with a throwaway debug script that gave each AI
tower faction 500 influence and performed one open tier-one seat — **and deliberately no
`cm:unlock_ritual`**, because a script unlock works with or without membership and would have
proved nothing. Nine of nine claimed, six of them modded houses. No Lua errors in 17,891 lines.

Two things that run reads wrong if skimmed:

- **`available=false` on every faction, members included.** The reason is on the same line,
  `cannot_afford=true` — a turn-one AI has no influence, so `available()` is false regardless of
  membership. Membership shows as `disabled=false script_locked=false`, and is only *proven* by
  the claim itself. See §6.2 on reading the bit mask.
- **Nine open seats, not twelve.** Three tier-one seats are `tower_of_zharr.is_scripted = true`
  (`t1_industry_2`, `t1_military_3`, `t1_sorcery_4`) and were skipped by design.

### AI usurping was gated by one line in our own script, not by the engine

Established 2026-08-20, verified in game the same day.

The engine was never the obstacle. `zzz_derpy_toz_ai_seats.lua` built its candidate list with
`seat.current_owner == nil`, so an owned seat could never be picked — and because tiers one and
two fill early, by turn 22 the only candidates left were tier-three seats at 300 influence that no
AI could afford. Seventy-nine consecutive gate checks across twelve factions returned
`cannot_afford_resource_cost` while tier-one usurps at 113 sat ignored beside them.

The fix is the predicate: `seat.current_owner ~= faction_name`. That admits the unowned seats and
every seat held by somebody else, and excludes only the faction's own. **Excluding self is not
cosmetic** — CA's usurp branch resolves the previous owner unconditionally, so a faction usurping
itself would take the diplomacy penalty for usurping itself and fire both halves of the incident
pair at the same CQI.

What a usurp costs, and why the AI can pay it:

| Tier-one seat | Influence |
|---|---|
| base | 75 |
| first usurp (`+50%`) | 113 |
| second (`+100%`) | 150 |
| third (`+150%`) | 188 |

`usurp_cost_multiplier * (1 + usurp_counter)` is a **percentage**, not a multiplier, and it is
applied permanently to all fourteen tower factions on every completion — plain claims included,
since a fresh claim runs with `usurp_counter = 0` and so already charges the first +50%. Against
CA's `ToZ_ai_boost` of +7 a turn from turn 10 a tier-one usurp is about sixteen turns of banked
income, and the AI demonstrably holds far more: factions were affording 300-influence tier-three
seats in the same campaign.

Two changes came with it:

- **Probe more than one candidate.** The loop used to abandon the turn on its first blocker, on
  the reasoning that blockers are faction-wide. That stopped being true the moment owned seats
  became candidates — price is per seat now, so a tier-three at 300 can be unaffordable in the
  same breath as a tier-one usurp at 113. `PROBES_PER_TURN = 4`.
- **`zzzz_derpy_toz_debug.lua` carries its own copy of `claimable_seats()`.** The pack holds
  **eight** copies of the predicate for four script files. Patch only the claimer and the census
  keeps reporting on rules the AI no longer follows — the diagnostics quietly disagree with the
  behaviour they exist to measure.

**Verified**, `cr_oldworld`, turns 27–30, on a save loaded mid-campaign: nine usurps by eight
factions — five tier one (`t1_sorcery_1`, `t1_sorcery_2`, `t1_industry_1`, `t1_industry_3`,
`t1_military_4`) and four tier two. Zero script errors in 4.2 MB. The eleven modded
`_toz_usurped_*` bundles and both incident sets carried CA's diplomacy branch without a nil.
Ownership transfer was read off the gate flags rather than the claim lines — see §6.4 for why the
claim lines are not proof: the usurper's own first candidate moved past the seat it had taken, and
every rival flipped to `script_locked` on that seat in the same turn.

**The player is the biggest loser, and that is not a bug.** The Conclave was usurped in four of
the nine. A 25% claim chance against fourteen factions is roughly two usurps a turn; that is the
dial to turn, not the predicate. Since 2026-10-03 the dial is the MCT setting
`toz_ai_claim_chance`, beside `toz_ai_claims` (off stops rival claiming), `toz_ai_start_turn`
(10) and `toz_ai_claims_per_turn` (1), all read every turn.

### Consequences that were accepted, not overlooked

- **Membership is per group, so the annex tier is reachable by AI too.**
  `unlock_annex_rituals()` unlocks the tier-five seats for every faction in
  `tower_of_zharr.factions`, human or not. An AI claiming one force-confederates that house to
  itself, and `granted_this_session` marks the seat spent — the player loses that lord's grant
  for the campaign. Left open on purpose 2026-08-19. To close it, add `faction:is_human()` to
  the unlock loop in `zz_derpy_toz_annex.lua` (upstream, the engine never offers the ritual)
  rather than guarding `on_annex_claimed` (by then the AI already holds the seat).
- **`zzz_derpy_toz_ai_seats.lua` now does something.** Its claims were being refused for
  non-members; from turn 10 it adds its own 25%/turn claims on top of the engine's cadence. It
  is the knob if AI claiming feels too fast — the MCT switch `toz_ai_claims` turns it off
  without removing it, and the engine does not need it.

### Still untested

Tiers 3–4 for the modded houses. Tier 2 was settled 2026-08-20, when modded houses usurped four
tier-two seats; CA's `tier_unlocked_check` runs `unlock_rituals_in_category` over
`tower_of_zharr.factions`, which holds all fourteen, so 3–4 should follow the same way. Also still
untested: unaided engine claiming over a long run with no debug script attached.
