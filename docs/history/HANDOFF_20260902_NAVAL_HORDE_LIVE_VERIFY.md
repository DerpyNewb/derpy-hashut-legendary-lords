# Handoff 2026-09-02 — The naval horde verified live: tier V, recruiting, and the XP question

Nothing was built this session. It is a **measurement** session over the `mcp__wh3__*` bridge
against a running campaign, and it closes three open items that four previous handoffs had been
carrying, plus one bug found on the way.

Campaign under test: `cr_oldworld`, `cr_chd_warfleet_of_uzkulak` (Abnagg), turns 4-7, played live
by the player while this was being read. Deployed pack at the time:
`!aa_derpy_hashut_legendary_lords.pack`, **sha1 `273c9412f1b2450fe04b130ab7af77646592dbce`,
15,512,315 bytes**, Modpacks copy and Workshop copy byte-identical. **That hash is in no other
document** — the last one recorded is §9.11's `48db72f9` / 15,510,045, so a build shipped after the
army-banner patch with no write-up.

---

## 1. Tier V flagship, and the whole ship — CONFIRMED

`HANDOFF_20260831_ABNAGG_TORDREK_SHIPBUILDING_SCOPE.md` §21-23 (the development-points saga) and
`HANDOFF_20260902_ADMIRAL_AND_HERO_RECRUITMENT.md` §9's "the ship's chains are still level 1" are
both **closed**. Every slot is filled and the primary is at its top level:

```
0 derpy_chd_naval_horde_primary   -> derpy_chd_naval_horde_flagship_5
1 derpy_chd_naval_horde_secondary -> main_deck_3
2 derpy_chd_naval_horde_secondary -> gunports_4
3 derpy_chd_naval_horde_secondary -> crows_nest_3
4 derpy_chd_naval_horde_secondary -> sail_2
5 derpy_chd_naval_horde_secondary -> hold_3
6 derpy_chd_naval_horde_secondary -> helm_2
7 derpy_chd_naval_horde_secondary -> anchor_2
8 derpy_chd_naval_horde_secondary -> hull_2
9 derpy_chd_naval_horde_secondary -> cannons_3
```

All ten `active=true`. `HordeContext.DevelopmentPoints` 50, `GrowthPerTurn` 14.

**So §23's reorder (both `add_building_to_force` calls first, `add_development_points_to_horde`
last) is the fix, and it works.** Today's 09:46 log shows the shipped order:

```
XXX derpy_naval_horde convert cqi 2430 ok=true err=nil XXX
add_building_to_force() ... derpy_chd_naval_horde_flagship_1 ... cqi [2067]
add_building_to_force() ... derpy_chd_naval_horde_main_deck_1 ... cqi [2067]
XXX derpy_naval_horde add_building force_cqi=2067 ok=true err=nil XXX
XXX derpy_naval_horde dev_points ok=true err=nil XXX
```

### 1.1 How to read a horde's buildings, with the method notes that cost the time

`HANDOFF_20260831_ENCAMP_STANCE.md` §11 got as far as `HordeContext.BuildingSlotList.Size` and
stopped there, because **the CCO list has no working index accessor** — `BuildingSlotList(0)`,
`.Item(0).BuildingKey`, `.Item(0).Building.Key` and `.Item(0).Name` all return no value. The
route that works is Lua, and **CA's `scripting_doc.html` names two of its three methods wrongly**:

```lua
local sl = cm:get_military_force_by_cqi(2067):horde_details():military_force_slot_list()
for i = 0, sl:num_items() - 1 do
  local s = sl:item_at(i)
  print(s:template_key(), s:active(), s:has_building(), s:building())
end
```

- `HORDE_DETAILS_SCRIPT_INTERFACE` has **`military_force_slot_list`**, not the documented
  `slot_list`, and it has **no `is_null_interface`** — guarding on it throws.
- `MILITARY_FORCE_SCRIPT_INTERFACE` has **no `has_building`**. That lives on the slot.
- **`slot:building()` returns a plain string**, not a `BUILDING_SCRIPT_INTERFACE` — its metatable
  is Lua's string metatable, so `:name()` on it is nil. Use the value directly.

The general technique that unstuck all of this: when a documented method is nil, dump the
userdata's metatable — for these interfaces the methods sit **directly on the metatable**, not
behind `__index` (which is nil for them):

```lua
local ks = {} for k in pairs(getmetatable(obj)) do ks[#ks+1] = tostring(k) end
```

Wrap every probe in `pcall`. One unprotected error inside `wh3_eval` wedges the bridge for the
rest of the game session ([[wh3-mcp-bridge-wedges-after-eval-error]]); with `pcall` a wrong guess
costs nothing, and about a dozen wrong guesses were made here with no wedge.

---

## 2. Recruiting — CONFIRMED, and the level gating is exact

`MILITARY_FORCE_SCRIPT_INTERFACE:can_recruit_unit(key)` is the instrument. It answers per force,
so it tests the whole chain — `building_units_allowed` row, chain level, military group,
faction permissions — in one boolean. Positives *and* negatives were both checked, because a
table of all-true proves nothing:

| unit | granted at | `can_recruit_unit` |
|---|---|---|
| `inf_hobgoblin_cutthroats` | main_deck_1 | true |
| `inf_chaos_dwarf_warriors_great_weapons` | main_deck_3 | true |
| `inf_infernal_guard` | main_deck_3 | true |
| **`inf_infernal_ironsworn`** | main_deck_**4** (not built) | **false** |
| `inf_infernal_guard_fireglaives` | gunports_3 | true |
| `veh_dreadquake_mortar` | cannons_3 | true |
| **`wh_main_chs_art_hellcannon`** | cannons_3 | **true** — the cross-race grant resolves |
| `mon_great_taurus` | crows_nest_3 | true |
| **`mon_bale_taurus`** | crows_nest_**4** (not built) | **false** |
| `wh2_dlc11_cst_inf_zombie_deckhands_0` | Tordrek's chains only | **false** |

The last two rows are the valuable ones: the ladder gates correctly by level, and Abnagg cannot
reach Tordrek's drowned roster. Abnagg's stack is 20 units; flagship_5 (6) + hull_2 (4) = 10
recruitment points, so Phase 6's `building_effects_junction` rows are live.

---

## 3. The XP question — the mod is not doing it

Reported as "Abnagg is levelling up too quickly". Measured at turn 7, and **rank agrees with XP**
(`CurrentXpPercent` 0.339), so no level is being injected:

| lord | `CurrentXp` | rank | battles won | XP/battle |
|---|---|---|---|---|
| **Abnagg** | 61,424 | 23 | 9 | ~6,800 |
| Karl Franz | 13,086 | 8 | 4 | ~3,270 |
| **Tordrek** (same ship, AI) | 5,808 | 5 | 2 | ~2,900 |
| Ghorth | 6,504 | 5 | 2 | ~3,250 |

`CcoCampaignCharacter` + character cqi answers **`Rank`**, **`CurrentXp`** (raw), and
**`CurrentXpPercent`** (0-1 toward the next rank). `ExperiencePoints`, `Experience`,
`ExperienceThisLevel` and `ExperiencePercentageToNextRank` all return nothing — the documented
`Experience*` family on CCO is **unit** experience, not character.

### What was eliminated, so it is not re-walked

- **The ship grants no character XP.** All 43 rows of
  `building_effects_junction_tables/derpy_chd_naval_horde` were read. The only XP row is the
  anchor chain's `wh_main_effect_agent_action_outcome_parent_army_xp_gain_factionwide` at
  20/40/80 — which is **CA's exact Vampire Coast anchor ladder**
  (`wh2_dlc11_vampirecoast_ship_anchor_1..3` carry 20/40/80 at the same `force_to_force_own`
  scope), and whose vanilla loc reads **"Unit experience gain per turn: %+n"**. It is unit XP.
  `HANDOFF_20260831...SCOPE.md` §26 and `HANDOFF_20260901_NAVAL_HORDE_ROSTER.md` both describe it
  as "agent-action army XP", which is literally right and reads as if it were the lord's —
  **worth rewording, it sent this session down a blind alley.**
- **`derpy_abnagg_lord_trait` has no XP effect** (7 effect rows read out of
  `.skilltree_cache/extract`).
- **The character carries zero effect bundles.** `character:effect_bundles():num_items()` is 0.
- **No skill in his tree has one** — grepping the whole extracted table set for
  `experience|_xp` returns only `unit_xp_mod` (a column name),
  `wh3_dlc23_effect_agent_recruitment_xp_chd_daemonsmith_sorcerer` and the anchor effect above.
- **No enabled pack grants character XP.** Every pack in `used_mods.txt` under 210MB was
  byte-grepped. The only member of the character-XP family anywhere in the load order is
  `wh2_main_effect_force_army_campaign_experience_all` in `derpy_chd_house_ancillaries.pack`, at
  value **2** on nine ancillaries. `!b_mixer.pack`'s `add_character_experience` is its
  roving-pirate spawner (`pirate.level`), which is why the seven rogue Vampire Coast admirals sit
  at rank 20-35 with `battles_fought = 0` — normal, not a bug.
- **The ToZ annex grant is not it.** `zz_derpy_toz_annex.lua` has `GRANT_LEVEL = 15` and calls
  `cm:add_agent_experience(..., 15, true)`, but only inside the `create_force_with_general`
  callback for a **newly spawned** lord, and no `derpy_toz_annex granted lord` line appears in any
  of today's logs.

So it is battle XP: roughly 2x the per-battle value of the AI lords, on 2-4x the battle count, in
a save with 50,000 treasury and a 20-unit stack. **Still open**: his 6 equipped ancillaries and 8
traits were not enumerated — see §6.

### 3.1 A real bug, found on the way

`tools/gen_house_ancillaries.py:338` labels `wh2_main_effect_force_army_campaign_experience_all`
as `"+{v} army experience ranks"`. CA's own loc for that effect is
**"Experience gain: %+n% for Lords and Heroes"**. Nine ancillaries carry it at value 2, so they
advertise "+2 recruit ranks" and deliver +2% lord/hero XP. If recruit ranks were the intent the
effect should be a `force_recruit_rank` one. Not the cause of anything above (+2% cannot make 2x),
but it is wrong text on shipped items.

---

## 4. Reading vanilla loc offline — the header, corrected

[[wh3-vanilla-loc-readable-offline]] says "zstd with a u32 prefix, then LOC layout" and that is
right, but the layout itself cost three attempts. The working parse, against
`local_en.pack : text/db/*.loc` via `tools/read_pack_index.py`'s `read(pack, ".loc")`:

```
u32 uncompressed size, then a zstd frame          (when compression != 0)
  BOM ff fe | "LOC" | 1 pad byte | u32 version | u32 count
  then count x: u16 len + UTF-16LE key, u16 len + UTF-16LE value, 1 byte
```

The pad byte after `"LOC"` is the part that is easy to miss — treating the magic as 3 bytes and
the version as a `u16` parses garbage and the entry loop then fails silently inside a `try`.
A throwaway `loc_lookup.py` doing this lives in the session scratchpad; it is worth promoting to
`tools/` if loc lookups come up again.

---

## 5. Do not re-derive

- `CcoCampaignMilitaryForce` still cannot be constructed from a force CQI; go through
  `CcoCampaignCharacter` + character cqi and `MilitaryForceContext.HordeContext.*`.
- The CCO list properties (`BuildingSlotList`, `AncillaryList`) answer `.Size` and **nothing
  indexed**. Four accessor shapes were tried. Use Lua for slots; ancillaries have no Lua
  enumerator either (`has_ancillary(key)` only), so that one is still unsolved.
- `character:battles_fought()` / `battles_won()` / `number_of_traits()` / `all_traits()` (a plain
  Lua table of keys) / `effect_bundles()` all work and are the cheap way to characterise a lord.
- `mf:can_recruit_unit(key)` is the whole recruitment chain in one boolean — better than reading
  five tables.
- `wh3_soak_status` answering *"no soak has run in this script session"* is how you tell that
  turns advancing under you are **the player playing**, not a harness. Worth checking before
  treating a moving number as a bug.
- Byte-grep **does** reach DB row strings in our own packs (they are stored uncompressed), proven
  by finding `derpy_chd_naval_horde_flagship_5` and 20 `wh_main_effect_*` keys in the LL pack.
  [[wh3-byte-grep-reaches-text-not-db]] is about **CA's** packs, whose DB is compressed. Do not
  read that memory as "never grep a pack for a DB string" — for a mod pack it is the fastest
  survey there is.
- The RPFM MCP server was up this whole session (`/sessions` answered) but was never needed;
  everything above was read with the game as the source of truth.

---

## 6. Still open

1. **Abnagg's 6 ancillaries and 8 traits are unread.** They are the only place a hidden XP
   multiplier could still be. Enumerating them needs either a working CCO list accessor or
   `fetch_vanilla_tables.py` for the trait tables, which pays the 105MB dependency rebuild.
2. **Tordrek's ship is unverified** — build, recruit, and a report of "gunnery not unlocked or
   type is not available" plus "Tordrek is level 11 at turn 4". That is the next thing to measure.
3. Carried over and still unverified: the Fleetmaster's model after the `campaign_character_arts`
   fix, the army-banner badge, and the ten Vampire Coast skill nodes on Tordrek and no one else.
4. **Balance is still unmeasured**, and now has a number attached to it: a player lord on this
   ship reaches **rank 23 by turn 7**.
5. The deployed `273c9412` build is undocumented — whatever shipped after §9.11 has no write-up.

---

## 7. Second pass — Tordrek measured, and the XP question answered by control

Campaign switched: `cr_chd_black_kraken_armada` (Tordrek), turn 4, same pack. Tordrek char cqi
2454 / mf 2075.

### 7.1 Build and recruit — CONFIRMED, same shape as Abnagg

Ten of ten slots filled, all active, and the fork is visibly real — shared chains keep the
`derpy_chd_naval_horde_` prefix, his own carry `derpy_chd_naval_kraken_`:

```
0 primary   -> derpy_chd_naval_horde_flagship_4      5 derpy_chd_naval_horde_helm_2
1 secondary -> derpy_chd_naval_kraken_main_deck_2    6 derpy_chd_naval_horde_anchor_2
2 -> derpy_chd_naval_kraken_gunports_3               7 derpy_chd_naval_horde_sail_2
3 -> derpy_chd_naval_kraken_crows_nest_2             8 derpy_chd_naval_kraken_hull_2
4 -> derpy_chd_naval_kraken_hold_2                   9 derpy_chd_naval_kraken_cannons_2
```

`DevelopmentPoints` 99, `ChainList.Size` 11 (10 shared + his shipworks only). Army 19 units,
including `wh2_dlc11_cst_inf_zombie_gunnery_mob_0/1`, `inf_syreens`, `mon_bloated_corpse_0` and
two `wh_main_chs_art_hellcannon` — so the drowned roster and the cross-race grant both draw.
`can_recruit_unit` at `kraken_gunports_3`: mob_0 / mob_1 / mob_3 / blunderbusses / fireglaives
**true**, mob_2 and `mon_rotting_prometheans_gunnery_mob_0` (both level 4) **false**. Correct.

### 7.2 "Gunnery not unlocked / type is not available" — it is the Gunnery Wight, and it is one missing row

The hero **slot** is fine, and this is the call that proves it — `can_recruit_agent_at_force`
takes **one argument, the agent-type key** (the two-argument form returns false for everything,
including agents the faction already fields, so it is not a signature and tells you nothing):

```
mf 2075 (Tordrek's ship): engineer=true  wizard=false champion=false
mf 2102/2103/2104/2112  : engineer=false wizard=false champion=false
```

`faction:agent_cap("engineer")` = 2, `agent_cap_remaining` = 1, so `KRAKEN_HEROES`'
`kraken_gunports_2/3/4` enable rows and the `_3` cap row are all live. The permitted-subtype row
is there too (`engineer / cr_chd_black_kraken_armada / derpy_chd_gunnery_wight / false`), and so
are the wight's `agent_subtypes`, `main_units`, `land_units`, five `campaign_character_art_sets`,
five `campaign_character_arts` and its `units_to_groupings_military_permissions` row.

**What it does not have is a `character_skill_node_sets` row.** Vanilla has 547 rows covering
526 of 613 subtypes, CA's own donor included:

```
wh2_dlc11_cst_gunnery_wight  -> wh2_dlc11_skill_node_set_cst_gunnery_wight  (agent_key engineer)
wh3_dlc23_chd_infernal_castellan -> wh3_dlc23_skill_node_set_chd_infernal_castellan
```

and every other subtype this pack owns has one in `zz_character_skill_node_sets.tsv` — thirteen
legendary lords plus `derpy_chd_admiral_skills`. `derpy_chd_gunnery_wight` is the only custom
subtype in the pack with no skill set at all. That is the single structural gap between it and
the Infernal Castellan, which recruits fine in the same slot.

**A blank `recruitment_category` is NOT the fault** — it looks wrong next to the Fleetmaster's,
but 284 of 613 vanilla subtypes are blank there and CA's own gunnery wight, infernal castellan,
bull centaur taurruk and all four daemonsmiths are among them. That column is the *lord* panel's
tab ([[wh3-recruitment-category-is-the-panel-tab]]); heroes do not use it. Do not "fix" it.

### 7.3 The XP bug is real, and the control proves it is not this mod

The clean control the previous campaign could not give: **33 generals in the world have fought
exactly one battle.** Every AI one is rank 2-5; the one human is rank 11.

| lord | rank | battles | XP |
|---|---|---|---|
| **derpy_tordrek (human)** | **11** | **1** | **21,889** |
| `wh3_dlc25_dwf_malakai_makaisson` — highest AI | 5 | 1 | 5,826 |
| **derpy_abnagg — AI, on the identical ship** | **3** | **1** | **2,597** |
| derpy_gargath / vraznak / bzaark / urzkhal | 3 | 1 | 2,292 - 2,521 |

Sorted by XP-per-battle across all 108 generals with a battle, Tordrek is first at 21,889 and the
runner-up is 5,826 — **3.8x the entire rest of the world, and the only human on the list.**

**AI Abnagg is the load-bearing row.** Same force type, same converted horde, same shared chains,
same `derpy_*_lord_trait` shape, same anchor chain — and 2,597 from his one battle. The ship, the
force type and the lord trait bundles are therefore exonerated by measurement, not by argument.

Also eliminated this pass:
- **Not per-turn.** `derpy_balur` and `derpy_chd_admiral` sit at 0 XP with 0 battles;
  `derpy_snakebeard` at 130. The per-turn trickle is tens of XP, not thousands.
- **Not difficulty.** `cm:get_difficulty(true)` returns **`normal`** (int 2). No player handicap.
- **Not traits.** 8 traits at one battle is unremarkable — 6 of the 33 one-battle AI lords have 8.
- **Not an injected level.** `CurrentXpPercent` 0.996, so rank and XP agree; he genuinely holds
  21,889 XP, and `SkillPointsAvailable` is 0 (all eleven spent).
- **Not any enabled pack.** The first pass skipped five packs over 210MB; the one that mattered,
  **`!cr_oldworld_campaign.pack` (2.4GB)**, was grepped this pass. Its only XP keys are
  `wh_main_effect_force_all_campaign_experience_base_all` (loc: *recruit rank* / unit XP) and
  `wh_dlc05_effect_building_army_xp_gain` (unit XP per turn), and its four `add_agent_experience`
  calls are CA's own scripted spawns — Ubersreik agents, the endgame forces, Belegar's starting
  characters and Nakai's. None reaches a player lord.

**So the anomaly is confirmed and its source is outside everything this project ships.** What is
left is a single battle's award: either that one battle was enormous (a full rogue Skaven stack
at sea — his traits are `wins_against_skaven` + `wins_at_sea` + `attacking_victory`), or the human
player's lord is getting a battle-XP multiplier from something that leaves no readable string in
any pack.

**The test that settles it, with the baseline already taken:** turn 4, rank 11, `battles_fought`
1, `CurrentXp` **21,889**. Fight one ordinary battle and re-read `CurrentXp`. A normal award on
this map at this turn is 2,300-5,800. A second ~20,000 award means a real multiplier and the hunt
continues; a ~3,000 award means the first battle was simply huge and there is no bug.

### 7.4 Do not re-derive (second pass)

- `can_recruit_agent_at_force(agent_type_key)` — **one argument**, and it is the agent *type*
  (`engineer`), not a subtype. It is the cheap oracle for "is the hero slot open on this force".
- `faction:agent_cap(type)` / `agent_cap_remaining(type)` work and are worth reading before
  blaming the DB; `agent_subtype_cap` returns 4294967296 (unbounded) and is useless.
- `agent_subtype_subculture_overrides` is **empty in vanilla** — a dead table, do not populate it.
- CA's `wh2_dlc11_cst_gunnery_wight` has **no** `agent_subtype_ownership_content_pack_junctions`
  row, so the clone needing one is not a theory worth testing.
- Sorting every general in the world by XP-per-battle is a five-second `wh3_eval` and is the
  single most informative thing to run against any "this levels too fast" report. Do that first
  next time instead of reading tables.

### 7.5 Still open (second pass)

1. ~~Add the wight's `character_skill_node_sets` row~~ — **BUILT AND DEPLOYED, see section 8.**
2. **The XP multiplier's source is unidentified.** Run 7.3's one-battle test before hunting
   further; the baseline is turn 4 / rank 11 / battles_fought 1 / CurrentXp 21,889.
3. Everything in section 6 still stands.


---

## 8. The wight's skill node set — built and deployed 2026-09-02

`tools/gen_naval_horde_admiral.py` owns the Gunnery Wight, so the row was added there rather than
hand-imported, and the generator prunes as well as appends so a re-run cannot leave a stale copy.

**CA's set key cannot be reused.** `character_skill_node_sets` has 547 vanilla rows and **547
distinct `key` values**, so `key` is the primary key — pointing
`wh2_dlc11_skill_node_set_cst_gunnery_wight` at a second `agent_subtype_key` is a duplicate key,
which the game drops in silence ([[wh3-check-duplicate-keys-before-packing]]). So the wight gets
its own set over CA's node list, exactly the shape the Fleetmaster already uses for the Overseer's:

| table | row |
|---|---|
| `character_skill_node_sets` | `derpy_chd_gunnery_wight_skills`, `agent_key` **engineer**, `agent_subtype_key` `derpy_chd_gunnery_wight` |
| `character_skill_node_set_items` | **40 rows**, every node of `wh2_dlc11_skill_node_set_cst_gunnery_wight`, read live out of the vanilla cache rather than listed |

No new skills, no new nodes, no loc, no art. 14 -> 15 set rows, 595 -> 635 item rows, and the
generator's summary line now reads **113 skill nodes reused** (73 Overseer + 40 wight).

**Three new assertions in `check()`**, the first of which is the one that would have caught this:

- every subtype this pack owns has a `character_skill_node_sets` row — proven to bite by dropping
  the wight's row in memory and re-running: *"agent subtype with no character_skill_node_sets row:
  derpy_chd_gunnery_wight"*
- no duplicate `key` among our set rows
- no set key of ours collides with vanilla's 547

Imported with `tools/import_naval_horde.py` (its `check_keys` ran clean first) and verified by
re-reading the **saved file from disk**, not from `import_tsv`'s return: `derpy_chd_gunnery_wight_skills`
and `wh2_dlc11_skill_cst_gunnery_wight_ranged_00` are both present.

Deployed to both copies, **sha1 `207cd5d7991545790dd6640bde55f3c02d6c4c7d`, 15,515,704 bytes**
(was `273c9412` / 15,512,315). The Workshop copy took the write with the game still running, so
the "deploying is a game-shut step" rule is not absolute — but the change is DB, so it needs a
**game restart** before the save will see it.

**Not launched.** Next launch answers whether the Gunnery Wight card now appears in Tordrek's
engineer slot on `kraken_gunports_2+`. If it still does not, the skill set was not the cause and
the remaining untested variables are the wight's `agent_subtypes` clone fields themselves.


---

## 9. The wight is still locked — what the message is, and everything now ruled out

Player screenshot after the `207cd5d7` deploy: Recruit Hero panel on Tordrek's ship, hero cap
**1/2**, three type tabs (Bull Centaur Taur'ruk / Infernal Castellan / Daemonsmith Sorcerer) and a
two-entry subtype strip on the left whose second entry is the **Gunnery Wight**, hovering as
**"This type is not yet unlocked"**. So section 8's skill node set was **not** the cause — correct
to ship, not the fix.

### 9.1 The building DOES grant recruitment — that half is settled

Three independent confirmations, so this is not where to look again:

- `can_recruit_agent_at_force("engineer")` is **true on Tordrek's ship and false on all four other
  forces in his faction** — the `kraken_gunports_2/3/4` enable rows are doing exactly their job.
- `faction:agent_cap("engineer")` is **2** with **1 remaining**, which is base plus the
  `kraken_gunports_3` cap row.
- The panel itself: it opened, it reads 1/2, and the Infernal Castellan is recruitable in that
  slot with two rolled candidates.

The enable effect is per **(agent type, culture)**. It opens the slot; it has never had anything
to say about which subtype goes in it.

### 9.2 The message, and why there is no UI expression to read

The string is `ui_text_replacements_localised_text_agent_subtype_unavailable` =
`[[col:red]]This type is not yet unlocked[[/col]]`, found by decompressing every `.loc` in
`local_en.pack`. **It appears in no `.twui.xml` in ui.pack / ui2.pack / ui3.pack** — every one was
decompressed and searched. `ui_text_replacements` is substituted by the **engine**, so unlike the
rites panel there is no CCO expression in a layout file to read the gate off. That closes the
route that solved the rites-panel problems.

### 9.3 Verified out of the DEPLOYED pack, not the exports

Both rows decoded straight from `!aa_derpy_hashut_legendary_lords.pack` with RPFM:

```
faction_agent_permitted_subtypes v1: {agent: engineer, faction: cr_chd_black_kraken_armada,
                                      subtype: derpy_chd_gunnery_wight, mod_disabled: False}
character_skill_node_sets      v0: {key: derpy_chd_gunnery_wight_skills, agent_key: engineer,
                                      agent_subtype_key: derpy_chd_gunnery_wight}
```

`engineer` is right: CA's own 20 permitted rows for `wh2_dlc11_cst_gunnery_wight` are all `engineer`,
and so are the castellan's 11.

### 9.4 The clone is faithful — three field-by-field diffs against CA's donor

- **`agent_subtypes`**: identical to `wh2_dlc11_cst_gunnery_wight` in all 24 columns except `key`
  and `associated_unit_override`. Blank `recruitment_category` matches CA's.
- **`campaign_character_art_sets`**: identical in all 9 columns except the two keys — `culture`,
  `subculture` and `faction` are blank on CA's rows too.
- **`main_units`**: identical except `unit`/`land_unit` and float formatting. Note
  `ui_unit_group_land` legitimately still reads `wh2_dlc11_cst_gunnery_wight` — CA's row says the
  same, it is a `ui_unit_groupings` key and not a subtype binding.

### 9.5 The table sweep, and what it eliminated

Every one of the **38 tables whose schema references `agent_subtypes.key`** was enumerated with
RPFM's `referencing_columns_for_definition`, and every cached vanilla table was swept for
`wh2_dlc11_cst_gunnery_wight`. CA populates exactly twelve tables for its wight, and the three we
do not ship (`battle_personalities`, `campaign_agent_subtype_factorial_effect_junctions`,
`effect_bonus_value_agent_subtype_junctions`) cannot gate recruitment.

Specifically ruled out:

- **`campaign_to_agent_subtypes`** — 181 vanilla rows and **none of CA's heroes are in it**
  (not the wight, castellan, taurruk or overseer). It is a legendary-lord/campaign table.
- **`agent_subtype_ownership_content_pack_junctions`** — CA's wight has **no** row (the castellan
  does), so absence is not a lock.
- **`agent_subtype_subculture_overrides`** — **0 rows in vanilla**, a dead table.
- **`agent_subtype_set_items`** — 87 rows, neither the wight nor the castellan appear.
- **`units_to_exclusive_faction_permissions`** — no row for either CA hero unit.
- **`units_to_groupings_military_permissions`** — hero units DO need one, and ours is right:
  CHD's overseer, castellan and taurruk units are all in `wh3_dlc23_group_chaos_dwarfs`, which is
  exactly the group our wight unit carries. CA's own wight unit is in the two Vampire Coast groups.
- **A per-subtype enable effect does not exist** — 0 of vanilla's 15,064 effect keys contain
  `agent_subtype`, and the 106 `agent_enable_recruitment` keys are all (type, culture).

### 9.6 What to do next — ANSWERED IN SECTION 10

The gate is engine-side and per (faction, subtype), and every DB row CA populates for a working
hero of that type is present and correct under our keys. The next move is **not** another table:
open the Recruit Hero panel with the bridge up, get the locked entry's component, read its
`GetContextObjectId`, and query that object — the engine will name its own gate. `CcoAgentSubtypeRecord`
constructs from a subtype key and is the likely type.

Two things to try in the same session, both cheap:

1. `mf:can_recruit_unit("derpy_chd_cha_gunnery_wight_0")` returned **false** on Tordrek's ship, and
   that was dismissed as "heroes are not in `building_units_allowed`". **Test it against
   `wh3_dlc23_chd_cha_infernal_castellan` on the same force.** If the castellan answers true, that
   call is meaningful for heroes and the wight's false is the gate, pointing back at the unit.
2. Compare against a control that must work: temporarily permit `wh3_dlc23_chd_cha_bull_centaur_taurruk`
   nothing — instead permit **CA's own** `wh2_dlc11_cst_gunnery_wight` to Tordrek's faction for one
   launch. If CA's subtype unlocks and ours does not, the fault is in our clone; if CA's is locked
   too, the fault is that a Vampire Coast hero cannot be unlocked for a Chaos Dwarf faction at all,
   and the feature needs a different donor.


---

## 10. Root cause: the `availability` junction. One row, and it is the whole lock

`effect_bonus_value_agent_subtype_junctions_tables` (v0, 457 vanilla rows, three key columns
`bonus_value_id` / `effect` / `subtype`). 193 of its rows carry `bonus_value_id = "availability"`,
and **that is the link that says which subtypes an enable effect actually unlocks**:

```
availability | wh3_dlc23_effect_agent_enable_recruitment_engineer_chaos_dwarfs | wh3_dlc23_chd_infernal_castellan
availability | wh2_dlc11_effect_agent_enable_recruitment_engineer_cst          | wh2_dlc11_cst_gunnery_wight
```

**All six vanilla Chaos Dwarf hero subtypes have one** — the castellan against the engineer
effect, the taurruk against the champions effect, all four daemonsmiths against the wizard
effect. `wh3_dlc23_chd_overseer` has **zero**, which is consistent and not an exception: it is a
lord, and lords have no enable effect at all
([[wh3-hero-recruitment-is-an-effect-lords-have-none]]). `derpy_chd_gunnery_wight` had zero.

So the model is three-layered, and every previous session only had two of them:

| layer | table | what it does |
|---|---|---|
| slot | `building_effects_junction` -> `..._agent_enable_recruitment_<type>_<culture>` | opens a hero slot on the force |
| listing | `faction_agent_permitted_subtypes` | puts the subtype in the panel's strip |
| **unlock** | **`effect_bonus_value_agent_subtype_junctions`, `bonus_value_id = "availability"`** | **makes that subtype selectable** |

With layers 1 and 2 and not 3 you get exactly what shipped: the entry is present, correctly under
the right agent type, and greyed as **"This type is not yet unlocked"**. It is the same shape as
`docs/CUSTOM_ABILITIES.md`'s `bonus_value_id = "enable"` link, in a different table.

**Abnagg's six heroes were never affected** because they are CA's own subtypes and CA already
ships their availability rows. Only a *new* subtype needs one, which is why this never surfaced
until Tordrek got a cloned hero.

### 10.1 What shipped

One row, in a new fragment `db/effect_bonus_value_agent_subtype_junctions_tables/derpy_chd_naval_horde`:

```
availability | wh3_dlc23_effect_agent_enable_recruitment_engineer_chaos_dwarfs | derpy_chd_gunnery_wight
```

CA's own wight carries exactly one such row (the castellan carries two, the second against a
per-subtype effect `wh3_dlc23_effect_enable_recruitment_chd_infernal_castellan`), so one is enough
— the rows are an OR.

`check()` now asserts **every** subtype in `HERO_SUBTYPES + TORDREK_HERO_SUBTYPES` is reachable
from the enable effect that opens its slot, ours or vanilla's. Proven to bite by emptying the
fragment in memory: *"no availability junction for derpy_chd_gunnery_wight against
wh3_dlc23_effect_agent_enable_recruitment_engineer_chaos_dwarfs - it will read 'not yet unlocked'"*.

Imported and **verified by decoding the row back out of the saved pack**. Deployed to both copies,
**sha1 `107a81e71c5f00fc2df9b0e5d9cf5ccc349b94f4`, 15,515,971 bytes** (was `207cd5d7` /
15,515,704). The first attempt failed `Device or resource busy` — unlike the `207cd5d7` deploy,
this one really did need the game shut, so treat that as the rule and the earlier success as luck.

### 10.2 How it was found, and the two dead ends worth not repeating

- The string is `ui_text_replacements_localised_text_agent_subtype_unavailable`, and
  `ui_text_replacements` is **engine-substituted**: it appears in no `.twui.xml` in ui/ui2/ui3 and
  in none of `data_script.pack`'s 1,005 Lua files. There was no UI expression to read, which is
  what made this feel unfalsifiable.
- **Component state is not a reliable signal here.** The locked wight reads `CurrentState()
  = "inactive"` — but so do the perfectly working `champion` and `wizard` **tabs** in the same
  panel, while the lore strip uses `active` for its unselected entries. Two conventions in one
  panel. What did settle it was `SimulateLClick()` on the entry: the selection did not move, so
  it is genuinely non-interactive.
- **`can_recruit_unit` is meaningless for heroes.** It returns false for
  `wh3_dlc23_chd_cha_infernal_castellan` on the very force that has one recruited. Section 9.6's
  first proposed test is therefore dead — do not run it.
- The panel's own "no candidates" path is a *different* condition with its own component
  (`no_candidates_panel`, "A new character will be available on the next turn"), so minting and
  `auto_generate` were never involved.

### 10.3 Also confirmed this pass

- The game **did** restart after the `207cd5d7` deploy (logs at 18:21 and 18:35 against an 18:19
  file), so the skill node set was live and genuinely not the cause. It stays: it is correct, and
  526 of vanilla's 613 subtypes have one.
- **No `bad_mods_report.txt`** — nothing in the pack is being rejected at load.
- The hero panel's component path, for next time:
  `character_panel > character_panel_info_holder > general_selection_panel > main_holder >
  lore_select_parent > wizard_type > type_list > <subtype key>`, with the agent-type tabs at
  `character_panel > lords_and_agents_holder > agent_parent > list_box` and the candidate list at
  `main_holder > character_list_parent`. Each strip entry is **named after the subtype key** and
  carries **no context object**, so there is nothing to CCO-query — read `CurrentState()` and
  click it instead.

### 10.4 Still open

1. ~~Deploy the Workshop copy~~ done, and **confirmed unlocked in game** — the strip entry reads
   `state=selected`, not `inactive`. The availability junction was the whole gate. Section 11 is
   what came next.
2. The XP multiplier from section 7.3 is still unexplained; the baseline for the one-battle test
   is turn 4 / rank 11 / `battles_fought` 1 / `CurrentXp` 21,889.


---

## 11. The clone was the bug: the Gunnery Wight is CA's subtype now

Deployed sha1 `94edeb745dd8b66bf486d50f23ec8ccd1e00cdd7`, 15,508,124 bytes (was `107a81e7` /
15,515,971). Both copies identical; the game was open and did **not** hold the file this time.

Unlocking the wight only exposed the next four faults, all reported from the live game:
placeholder porthole, placeholder unit card, Chaos Dwarf names, and no skill tree. Three of them
turned out to be one cause.

### 11.1 Measured, not guessed

Over the wh3 bridge, `CcoCampaignCharacter`:

| character | rank | `SkillList.Size` |
|---|---|---|
| `wh3_dlc23_chd_infernal_castellan` (same army) | 3 | 41 |
| `wh3_dlc23_chd_sorcerer_prophet_death` | 1 | 55 |
| `derpy_tordrek` | 11 | 56 |
| **`derpy_chd_gunnery_wight`** | 1 | **0** |

`SkillList` is documented as "available to a character (**regardless of current state**)", so it is
the whole tree, not the unlocked part. Rank was ruled out by the rank-1 sorcerer, and standalone
(non-embedded) status by sweeping all 174 standalone characters in the world: every one returned
25-62. Zero is the clone's alone. Its name came back "Hurgar Grimtidesson".

### 11.2 Portholes and unit cards are not in the DB at all

`campaign_character_arts.portrait` and `.card` are **empty on all 1,495 vanilla rows** — they are
not the lever. The image is a pre-rendered PNG resolved through
`ui/portraits/portholes/portrait_settings__.bin` (and the `ui/portraits/units/` twin), a zstd
binary keyed by **`art_set_id`**:

```
u16 len + art_set_id ("wh2_dlc11_art_set_cst_gunnery_wight_01")
5 x f32 body camera, u8, u8, u8 has_head_camera
[5 x f32 head camera, u8, u8]          only when the flag is 1
u32 variant count
  u16+name ("cst_gunnery_wight_campaign_01")
  u16+png  ("UI/Portraits/Portholes/no_culture/cst_gunnery_wight_campaign_01_0.png")
  u16+mask1, u16+mask2                 length 0 when absent
```

A **new art set id therefore has no image anywhere in the game** and every panel falls back to the
placeholder. That is one cause for both the porthole and the unit card — `unit_variants.unit_card`
is literally the string `"placeholder"` on CA's own wight, so it was never the card's source.

### 11.3 The skill tree that would not bind

Everything checked clean and it still returned nothing:

- `character_skill_node_sets` row decoded out of the saved pack, field for field identical in shape
  to CA's (`agent_key` engineer, `agent_subtype_key` ours, the rest empty).
- All 40 `character_skill_node_set_items` rows present, `mod_disabled` false, every `item` present
  in `character_skill_nodes` and `visible_in_ui` true.
- Node reuse is not the problem: `derpy_ghorth_skills` reuses 47 of 47 vanilla nodes and works.
- `enc_title` loc is not the gate: `derpy_tordrek_skills` has none and works.
- `character_experience_skill_tiers` is keyed by `agent_key`, not subtype.
- `character_skill_node_sets_to_agent_subtypes` and `agent_subtype_subculture_overrides` are
  **empty in vanilla** — not the modern mechanism.
- The RPFM schema's full reference graph (55 columns pointing at `agent_subtypes.key`, 38 tables)
  turned up nothing the clone was missing.
- `wh3_check_errors` mentions nothing of ours; there is no `bad_mods_report.txt`.

Root cause unidentified. **The fix was to stop cloning.**

### 11.4 What changed

`tools/gen_naval_horde_admiral.py` no longer mints a wight. `WIGHT_SUBTYPE` is now
`wh2_dlc11_cst_gunnery_wight` and `WIGHT_UNIT` is `wh2_dlc11_cst_cha_gunnery_wight_0`; blocks
19-24 collapse to one block that rewrites CA's `agent_subtypes` row with
`names_group = names_cst_vampire_coast` and nothing else. `STALE_WIGHT` keeps the two dead keys
listed purely so a regeneration prunes them, and `check()` asserts no fragment carries either.

Deleted with it: 5 fragments (`land_units`, `main_units`, `unit_variants`,
`land_units_to_unit_abilites_junctions`, `unit_set_to_unit_junctions` under
`derpy_chd_naval_horde` — the wight was their only row), 5 art sets, 5 arts rows, 40 skill-node
items, its node set and 2 loc keys. `gen_naval_horde_tordrek.py`'s military-group row now names
CA's unit.

The names lever is CA's own: `wh3_dlc23_chd_bull_centaur_taurruk` sets
`names_group = names_chd_bull_centaurs` to get bull centaur names inside a Chaos Dwarf faction. It
is a no-op for Vampire Coast factions, where that is already the group the faction supplies.

The clone bought nothing in DLC terms either — it still pointed at CA's variantmesh, entity and
animations, and `agent_subtype_ownership_content_pack_junctions` carries no row for the wight at
all (the Castellan has one; the wight does not).

### 11.5 "No characters currently available" is the candidate pool, not the wiring

After the deploy the strip entry reads `wh2_dlc11_cst_gunnery_wight` / `state=selected` and the
panel says *"No characters currently available. A new character will be available on the next
turn."* That is the pool, and the control proves it: `character_list_parent > list_box` holds
`general_candidate_0_` and `general_candidate_1_`, **both invisible under the Wight and both
visible the instant the Castellan entry is clicked**. Two engineer candidates were minted, both
Castellans; the Wight was permitted only this build, so nothing of its subtype had been rolled yet.

Candidates can be seeded rather than waited for:

```lua
cm:spawn_character_to_pool("cr_chd_black_kraken_armada", "", "", "", "", 25, true,
                           "engineer", "wh2_dlc11_cst_gunnery_wight", false, "")
```

Empty forename/surname/art set let the engine roll them, which is what exercises `names_group`. The
call returns a `character_details` interface, but `:character()` on it is null - a pool candidate
has no map character yet - and **hero pool candidates do not appear in `faction:character_list()`**
either, though *lord* pool candidates do (the four `wh3_dlc23_chd_overseer` rows there come back
with `character_type_key() == "colonel"`). The Recruit Hero panel is the only readout.

Also confirmed: **the clone's already-recruited character vanished cleanly.** Deleting the subtype
did not leave a dangling record - `derpy_chd_gunnery_wight` is simply gone from the faction's
character list, no crash, nothing to kill.

### 11.6 Still open

1. ~~The Fleetmaster has the same porthole bug~~ **fixed** — see section 12.
2. Whether the Fleetmaster's skill tree binds is **untested** — it is the other subtype this pack
   mints, and it uses the same machinery that failed for the wight.
3. The XP multiplier from section 7.3 is still unexplained; the baseline for the one-battle test
   is turn 4 / rank 11 / `battles_fought` 1 / `CurrentXp` 21,889.


---

## 12. The Fleetmaster's porthole: `tools/gen_portrait_settings.py`

Deployed sha1 `4ede419ea8ba4c0fb2a7ebcdcff1dc485d67b9e8`, 15,509,994 bytes (was `94edeb74` /
15,508,124).

The Gunnery Wight escaped the porthole bug by becoming CA's subtype. The Fleetmaster cannot — he is
genuinely new — so `derpy_chd_admiral_01..03` needed real `portrait_settings` entries. The new tool
clones CA's `wh3_dlc23_art_set_chd_overseer_01..03` blocks under our ids, changing only the id, and
ships the result as `portrait_settings_derpy_naval_horde.bin`.

### 12.1 The format, corrected

Section 11.2's sketch was wrong twice. What actually round-trips, byte for byte, against all five
portrait settings files on this machine:

```
u32 version (4), u32 entry count, then per entry:
  u16 len + ascii art_set_id
  5 x f32 body camera, u16+attachment bone, u8 has_head_camera
  [5 x f32 head camera, u16+attachment bone]     only when that flag is 1
  u32 variant count, then per variant:
    u16+name, u16+png, u16+mask1, u16+mask2, u16+spare      (length 0 when absent)
```

- **The attachment bone is a string, not padding.** It is empty on 1,395 of CA's 1,402 entries, so
  its two zero bytes read as filler right up to entry 264,
  `wh2_dlc16_art_set_wef_sisters_of_twilight`, which names `shoulder_pad_left` — and everything
  after it comes out as rubbish. Seven entries in the whole file have one.
- **A variant carries FIVE strings, not four.** An entry with no masks therefore ends in six zero
  bytes; a parser that stops at four is one byte short on the very next entry.
- The head camera has no flag of its own — the body camera's flag decides whether it is there.
  989 of 1,402 entries have one.

CA compresses the file (zstd behind a u32 uncompressed-size prefix); ours ships raw, and both load.

### 12.2 CA ships the same file in both folders

`ui/portraits/portholes/portrait_settings__.bin` and `ui/portraits/units/portrait_settings__.bin`
are **byte-identical**, and every png path inside either of them reads
`UI/Portraits/Portholes/...`. So it is the folder the file sits in that picks the render, not the
content. Ours is written to both for the same reason.

Loose end this exposed: the 13 legendary lords ship `ui/portraits/units/no_culture/derpy_*.png` but
`portrait_settings_derpy_hashut_ll.bin` exists only under `portholes/`, so nothing references those
thirteen PNGs. Nobody has reported a fault from it, so it is left alone — but dropping the same
file into `ui/portraits/units/` is a one-line fix if a lord's unit render ever comes up placeholder.

### 12.3 The check

`py tools/gen_portrait_settings.py --selftest` parses and re-serialises all five files and asserts
the bytes are identical, then asserts the corpus covers every shape that matters (739 masked, 607
bare, 989 with a head camera, 7 with a named bone). `check()` additionally asserts that every
`art_set_id` this pack **mints** — all 16 of them, 13 lords plus 3 Fleetmaster — is covered by one
of our two portrait settings files. That is the assertion that would have caught the original bug:
a minted art set with no entry anywhere draws the placeholder and says nothing.


---

## 13. "No characters currently available" — the DB is exhausted, the pool is not

The wight unlocks, the strip entry reads `selected`, and the panel still says *"No characters
currently available. A new character will be available on the next turn."* This section is the
elimination, so the next session does not repeat it.

### 13.1 The panel is healthy

- `type_list` holds `wh2_dlc11_cst_gunnery_wight` (**`selected`**) and
  `wh3_dlc23_chd_infernal_castellan` (`active`). Not locked, not hidden.
- `character_list_parent > listview > list_clip > list_box` holds `general_candidate_0_` and
  `general_candidate_1_`. Both `Visible() == false` under the Wight, both **true** the moment the
  Castellan entry is clicked. `no_candidates_panel` is visible under the Wight only.
- So the two minted engineer candidates are Castellans, and the Wight has none. The cards carry no
  context object (`GetContextObjectId` returns nil), so there is nothing to CCO-query on them.
- CA's `character_panel.twui.xml` puts a `dev_button_spawn_agent_subtype` on every `type_button` —
  stripped in the retail build, the live entry has only a `frame` child.

### 13.2 Nothing in the database is missing

Every vanilla table that references `agent_subtypes.key` was taken from the RPFM schema's reference
graph — **55 columns across 38 tables** — and swept for CA's Castellan against CA's Wight. The Wight
is short only of rows that cannot gate recruitment:

| table | Castellan | Wight |
|---|---|---|
| `agent_subtype_ownership_content_pack_junctions` | 1 | **0** (so the Wight is not DLC-gated) |
| `effect_bonus_value_ids_unit_sets`, `unit_set_to_unit_junctions`, `unit_sets` | 1 each | 0 |
| `agent_subtypes`, `character_skill_node_sets`, `campaign_agent_subtype_factorial_effect_junctions` | 1 | 1 |
| `campaign_character_art_sets` | 5 | 5 |
| `faction_agent_permitted_subtypes` | 11 | 20 (+ ours) |
| `effect_bonus_value_agent_subtype_junctions` | 2 | 1 (+ ours) |

On the row itself: `auto_generate` true, `recruitable` true, `show_in_ui` true, `cap` -1,
`recruitment_category` empty on both. `names_cst_vampire_coast` has 67 male forenames and 92 family
names, so name generation cannot be failing.

And there is **no DB table for the candidate pool at all**: of the 1,663 tables in the WH3 schema,
nothing matching `pool`, `candidat`, `generat` or `recruit` governs character candidates, and no CA
Lua in any shipped pack mentions `general_candidate` or `no_candidates_panel`. The pool is engine
code. There is nothing left in the pack to fix.

### 13.3 `spawn_character_to_pool` cannot be used to test this

`cm:spawn_character_to_pool` returns a live `character_details` interface, but:

- `:character()` on it is a null interface — a pool candidate has no map character;
- `faction:character_list()` does not change, **not even for CA's own subtypes** (spawning a
  Castellan and an Overseer both left the count at 7);
- the panel's card list does not change either.

So the call is unobservable from script, and the four `wh3_dlc23_chd_overseer` rows that DO appear
in `character_list()` (as `character_type_key() == "colonel"`) are something else. Do not use this
as a probe again.

### 13.4 What ending a turn showed, and what it cost

Turn 4 -> 5 was ended over the bridge after a named save (`wight_pool_test_pre_endturn`). No engineer
pool character appeared in `character_list()` — but per 13.3 that list never shows them, so the test
is **inconclusive**; only the panel can answer, and it was not reopened.

**The game then crashed** on
`common.get_context_value("CcoCampaignFaction", cqi, "AgentSubtypeCap(<key>)")` —
`0xc0000005` reading `0x0` at `Warhammer3.exe+0x1F368AC`. A parameterised CCO function is a native
call; the `pcall` around it catches nothing. Recorded as
`wh3-cco-function-with-argument-hard-crashes`. Turn 5 survives in
`Black Kraken Armada_Auto-save.4551214738.save`.

Unrelated but visible in the same tick: **Tordrek went from rank 11 to rank 12 with no battle
fought**, which is section 7.3's XP bug still running.

### 13.5 The two hypotheses left, and how to separate them

1. **The engineer candidate pool is full.** Two Castellans occupy it, and a Wight can only be rolled
   once a slot frees. Test: recruit one of the two Castellans, end a turn, reopen the panel.
2. **The pool's subtype list is fixed when the campaign starts.** A subtype permitted mid-campaign
   would then never be rolled in *this* save, while a new campaign works. Test: start a fresh
   Tordrek campaign and open Recruit Hero.

Hypothesis 2 is the one that matters for shipping, and it is the cheaper test. Run it first.

---

## 14. The Wight recruits but will not join the army — the DB is clean, the engine accepts it

Reported live: recruitment now works (the pool did fill), the hero stands on the map with the
right name and the right porthole, and it **will not embed in Tordrek's naval horde** from the UI.

### 14.1 The engine has no objection — measured, not argued

`cm:embed_agent_in_force(wight, tordrek_force)` **succeeded**: the hero went in, the force went
19 -> 20 units, `is_embedded_in_military_force()` true, and nothing errored. CA documents that
call as bypassing "normal restrictions other than that force being under siege", so this does not
prove the restriction is absent — but it does prove there is **no data impossibility**. The unit
record exists, the slot accepts it, the force renders it.

`common.get_context_value("CcoCampaignCharacter", cqi, "CanBeEmbedded")` is `true` for the Wight
and for the Castellan, `false` for Tordrek and for a garrison-commanding Overseer. It is a
character-only property ("is a hero not commanding a force"), so it says nothing about the pair.

### 14.2 Every pairwise restriction checked and passing, at the moment of the failure

| Restriction | Measured |
|---|---|
| Same faction | both `cr_chd_black_kraken_armada` |
| Both on land | `is_at_sea()` false for both |
| Same region | `cr_oldworld_region_scalded_swamp` |
| Distance | 2 tiles (`dist^2 = 5`) |
| Movement | Wight `action_points_remaining_percent` 100 |
| Force not full | 19 units; `MilitaryForceContext.UnitCountPercent` reads **1.0 at 20**, so the cap is 20 and one slot was free |
| Force under siege | no |
| Force accepts agents | `DERPY_CHD_NAVAL_HORDE` carries `character_bound`, `general_is_irreplaceable`, `can_attack_garrisons_from_sea` — **not** `unable_to_contain_agents`. Identical to CA's `ALBERIC` / `DRAGONSHIP_HORDE` / `SEAFANG`, all of which take heroes |
| Hero of the same type already present | the Castellan is `engineer` too, but **9 forces in this live world hold two heroes of one agent type**, so no such rule exists |

### 14.3 Unit-side gates: swept through the schema reference graph, all clean

Every table in `schema_wh3.ron` that references `main_units.unit` — 68 columns — was enumerated and
the candidates checked against CA's Gunnery Wight unit `wh2_dlc11_cst_cha_gunnery_wight_0`:

- `units_to_groupings_military_permissions` — **our row is live**. Byte-scanned all 665 installed
  packs: `!aa_derpy_hashut_legendary_lords.pack` ships
  `db/units_to_groupings_military_permissions_tables/derpy_chd_naval_horde` (1796 bytes) containing
  the unit key. And `factions.military_group` for `cr_chd_black_kraken_armada` decodes to
  `wh3_dlc23_group_chaos_dwarfs` in **both** packs that define the faction
  (`!cr_oldworld_campaign.pack` and ours) — the same group the row grants.
- `units_to_exclusive_faction_permissions` — 0 rows for this unit (and 0 for the Castellan).
- `main_unit_faction_overrides`, `unit_conditions`,
  `factionwide_recruitment_unit_exclusions_units_sets_junctions`,
  `unit_required_technology_junctions`, `commander_unit_permissions` — 0 rows, or the whole table
  is empty in vanilla.
- `main_unit_ownership_content_pack_junctions` — one row,
  `wh2_dlc11_vampire_coast`. **Not** the blocker:
  `cm:is_dlc_flag_enabled("TW_WH2_DLC11_VAMPIRE_COAST", faction)` returns **true** on this machine
  (control: a made-up product key returns false).
- `unit_variants` — one faction-agnostic row, same shape as the Castellan's and as the CST zombie
  units already sitting in the army.
- `main_units` row diff Wight vs Castellan: only art, audio, cost and `can_be_bribed` differ.
  Same `caste`, same `is_naval`.
- `agent_subtypes` row diff: only `key`, `small_icon`, `associated_unit_override`,
  `audio_voiceover_actor_group`, `cost`. Nothing structural.
- `campaign_to_agent_subtypes` lists **neither** subtype, so it is opt-in and not a gate.

### 14.4 Why this could not be reproduced from script — do not repeat these two mistakes

**`cm:move_to` cannot embed.** Ordering the Wight onto the army's tile (1872,460) leaves it where
it stands with 100% AP. So does ordering **CA's own Infernal Castellan**, spawned fresh next to the
army, onto the same tile. `move_to` is a pathfinding order and will not path onto an occupied
tile; the UI's "join army" is a different interaction command with no scripted equivalent. Any
"the hero refuses the army tile" reading off `move_to` is an artifact, **not** the bug.

**Movement orders are asynchronous, and reading immediately lies.** Every `move_to` in this session
read back as "did not move" when checked in the same or the next tool call, then executed seconds
later. Ordering Tordrek's army one tile as a control walked it into an enemy stack and **started a
battle**. Recovery: ESC menu (`menu_bar > buttongroup > button_menu`, then
`esc_menu/main/menu_left/menu_buttons/frame_quit/button_quit`) to the main menu, then
`wh3_load_campaign` on the save taken beforehand. Save before any live movement probe; wait 8-12s
before reading a position.

Also: a **script-spawned agent cannot move on the turn it is spawned** (`cm:spawn_agent_at_position`
then `move_to` -> nothing, AP stays 100), so it is useless as a same-turn control.

### 14.5 What is left

The pack is not missing a row. The remaining unknown is what the campaign UI evaluates on the
click, and it is not reachable from script — no CCO exposes the pair, and no CA Lua implements it.
The one datum still missing is what the screen actually does: whether the hero walks over and
stops, whether the cursor shows a forbidden icon, and whether the same click works on a
**settlement garrison** (which would separate "this hero" from "this force"). Ask before guessing
again.

---

## 15. It is not the embed — **no hero action of any kind resolves** for this Wight

Screenshots from the player reframed §14 completely. The Wight cannot embed in Tordrek's army, and
it also cannot do **Training** (on your own lord), **Scout Ruins**, **Block Army** or **Wound**.
Every one behaves the same way: the hero walks to the target, stops beside it, the Hero Actions
panel opens correctly, the action is clickable — and nothing happens.

### 15.1 Instrumented reproduction

With the live `agent_options` panel open I read it and clicked it from script:

- The panel is **healthy**. `button_method` state `active` for both entries, real numbers on them
  (`Block Army` 45% vs Drachau Malus Darkblade rank 6, `Wound` 0% vs Baine rank 5), costs, portraits,
  cooldown 10. Training against Tordrek reads "This action cannot fail / Positive outcome 100%".
- `SimulateLClick()` on `button_method` **closed the panel** — so the click is accepted — and then:
  `ActionPointsRemaining` **3500 before and after**, treasury **50,000 before and after**, position
  unchanged. The engine takes the order and drops it.

So the failure is not in the UI and not in the panel's data. The command reaches the engine and
dies there, spending nothing.

### 15.2 The character is healthy

`is_at_sea` false, `region` `cr_oldworld_region_tidal_flats` (not null), `IsOnMap` true,
`IsInLimbo` false, `IsDetailsOnly` false, `CanUseAp` true, `CanBeEmbedded` true, not wounded,
`ActionPointsRemaining` = `ActionPointsPerTurn` = 3500, Zeal/Subterfuge/Authority 3/3/3, rank 1,
subtype reads back as CA's `wh2_dlc11_cst_gunnery_wight`.

### 15.3 The action chain, checked

- `agent_actions` is keyed by **`agent` (the type), not the subtype** — the Wight is `engineer`, so
  it gets the identical 26 rows the Infernal Castellan gets. `subculture` is **empty on all 176
  rows** in the table, so it gates nothing.
- `agent_actions_subculture_overrides` — **0 rows** in vanilla.
- `campaign_group_agent_action_composite_scenes` — 7 rows, all special cases (Kroak, Ariel,
  earthquake). Not the general mechanism.
- `campaign_character_art_sets`: 5 rows for the Wight, `culture`/`subculture`/`faction` **all
  empty** — exactly the Castellan's shape, so the art set resolves in any faction.
- `campaign_character_arts`: full row — `uniform`, `sea_uniform`, `navy_uniform`,
  `land_animation` `cam_hero_hu1_cst_gunnery_rifle`. `campaign_anim_set_enums` is empty in the
  game files, so that column validates against nothing and cannot be checked this way.
- **No other installed pack touches it.** Byte-scanned all 665 packs under `data/` and
  `workshop/content/1142710/` for `wh2_dlc11_cst_gunnery_wight` inside `agent_subtypes_tables`,
  `agent_actions_tables` and `agent_culture_details_tables`: exactly one hit, our own
  `!aa_derpy_hashut_legendary_lords.pack`. No mod conflict.
- Our override row is written at **`agent_subtypes` table version 2** (24 columns) while CA ships
  **version 3** (25 — v2 plus `audio_force_contextual_vo`). The same v2 file has shipped the derpy
  legendary lords for months, so the layout is not fatal, but it is the one structural difference
  between our row and CA's and is worth eliminating if nothing else pans out.
- No script error accompanies the click: `wh3_check_errors` since the previous offset shows only
  leftovers from this session's own probes and the pre-existing `wh2_main_hef_caledor` warning.

### 15.4 The one thing that splits it, and the probe left armed

Everything checked is identical between the Wight and the Infernal Castellan, so the next datum
has to come from the game. Three listeners are armed in the live session under
`DERPY_PROBE` (a Lua global):

```
core:add_listener("derpy_probe_cct", "CharacterCharacterTargetAction", ...)
core:add_listener("derpy_probe_cgt", "CharacterGarrisonTargetAction", ...)
core:add_listener("derpy_probe_cpf", "CharacterPerformsActionAgainstFriendlyTarget", ...)
```

They append one line per event; read them back with `return table.concat(DERPY_PROBE, "\n")`.
**They die on a game restart** — re-arm before asking for another click.

- Event fires -> the engine ran the action and the *outcome* is being dropped.
- Nothing fires -> the command never reaches the model at all.

And the control that costs nothing: have the **Infernal Castellan already in Tordrek's army** try
the same action on the same target. Castellan works -> Wight-specific. Castellan also fails ->
agent actions are broken campaign-wide in this save and the Wight is innocent.

---

## 16. Root cause: `agent_subtypes.audio_vo_culture_override`

### 16.1 The split, measured

Three listeners armed in the live session (`DERPY_PROBE`), then one click each:

```
entries=1
CharacterCharacterTargetAction actor=wh3_dlc23_chd_infernal_castellan/2455 ability=assist_army target=derpy_tordrek crit=false
```

The **Castellan's** action raised the event and resolved. The **Wight's** click raised **nothing**.
Same faction, same agent type (`engineer`), same 26 `agent_actions` rows, same panel. So the engine
was discarding the Wight's command before the model ever saw it — which is why no action point and
no gold were ever spent.

### 16.2 What was different

`agent_subtypes.audio_vo_culture_override` was **empty** on our Wight row, and the Wight's
`audio_voiceover_actor_group` is `wh2_dlc11_vo_actor_VampireCoast_Gunnery_Wight`. Every entry in
`agent_actions` carries a `voiceover` (-> `audio_vo_campaign_special_ability_states`), and the
engine resolves the actor group inside the VO culture of the character's **faction** — Chaos
Dwarfs, which has never heard of a Vampire Coast actor group. Recruitment and movement need no
action VO and worked; every hero action and the army embed do, and were dropped.

**CA's precedent is unambiguous.** 150 of 613 vanilla `agent_subtypes` rows set this column, and
every one is the same shape — a subtype whose voice belongs to a culture other than its faction's:

| Subtype | Faction culture | Override |
|---|---|---|
| `wh3_dlc23_chd_gorduz_backstabber` | Chaos Dwarfs | `wh3_dlc23_vo_culture_Hobgoblins` |
| `wh2_dlc15_grn_grom_the_paunch` | Greenskins | `WH_MAIN_VO_CULTURE_GOBLIN` |
| `wh2_dlc15_grn_river_troll_hag` | Greenskins | `WH_MAIN_VO_CULTURE_TROLL` |
| `wh3_cp1_cth_*` (Tiger Warriors) | Cathay | `wh3_cp1_vo_culture_TigerWarriors` |
| every `wh3_dlc20_chs_daemon_prince_*` | Chaos | `wh3_main_vo_culture_DaemonPrince` |

Gorduz is the one that matters: a **Hobgoblin agent inside this exact Chaos Dwarf culture**.

### 16.3 The fix

`tools/gen_naval_horde_admiral.py`, block 19 — one cell:

```python
WIGHT_VO_CULTURE = "wh2_dlc11_vo_culture_Vampire_Coast"
rows.append(clone_row(cols, van_typed("agent_subtypes", "key", WIGHT_DONOR_SUBTYPE)[0],
                      key=WIGHT_SUBTYPE, names_group=WIGHT_NAMES,
                      audio_vo_culture_override=WIGHT_VO_CULTURE))
```

`check()` now pins `differs == {"names_group", "audio_vo_culture_override"}` against CA's row and
asserts the override value, so a regeneration cannot drop it. The key is confirmed real: it is the
`audio_voiceover_culture` every `wh2_dlc11_cst_*` unit in `main_units` uses.

Not changed: the file stays at `agent_subtypes` **version 2** against CA's **version 3**. The only
v3-only field is `audio_force_contextual_vo`, and CA has it `false` on both the Wight and the
Castellan, so the version gap drops nothing. Worth bumping one day, not part of this fix.

Deployed pack sha1 `d0a6604a8ca46e46e334c8836236666deb5bba65`, 15,509,994 bytes.

### 16.4 Still to confirm in game

Restart, load, and with the Gunnery Wight try in order: **Training on Tordrek**, **embed into the
army**, **Scout Ruins**, **Block Army**. If the VO culture was the whole story all four work. If
they still fail, the next suspects in order are the `agent_subtypes` v2/v3 version gap, then
dropping our override row entirely (the Wight then takes Chaos Dwarf names, which isolates whether
*any* override of CA's row is what breaks it).

---

## 17. The VO override was wrong. `agent_culture_details` is the missing table

### 17.1 Correction to section 16

The `audio_vo_culture_override` fix in section 16 **did not work**. The reasoning there was
correlation dressed as mechanism: it was the only asymmetry left, and CA sets it on every
foreign-culture agent, so it got promoted to a cause without any evidence that its absence blocks
an action. The row is still correct to have (a Vampire Coast voice in a Chaos Dwarf faction should
resolve in its own VO culture) and it stays, but it is not the bug. **Do not repeat that inference
shape - "the only difference left" is a hypothesis, not a finding.**

### 17.2 What the survey of other mods turned up

Scanning all 665 installed packs for `faction_agent_permitted_subtypes` files that grant a
**vanilla** subtype whose race is not among the factions in the same file - our exact trick -
returned 12 packs. The useful ones:

| Pack | Grants | To |
|---|---|---|
| `alshua_cultists.pack` | `wh3_main_nur/sla/tze_cultist` (heroes) | Chaos, Daemon, Norsca factions |
| `inq_lol_hero.pack` | `wh_main_dwf_runesmith`, `wh_main_dwf_master_engineer` | many races |
| `!scm_marienburg.pack` | `wh2_dlc11_cst_admiral_deep` | Empire |
| `!scm_totn.pack` | `wh3_dlc27_sla_styrkaar` | Norsca |

**Every one of them ships `agent_actions_tables`, and the smallest and closest -
`alshua_cultists.pack`, 104 db tables, cross-race hero grants - also ships
`agent_culture_details_tables`. We shipped neither.**

### 17.3 What that table actually is

`agent_culture_details` is **not unique on (agent, culture)**. Its primary key is the numeric `key`
column, and the table is a list: one row per **(agent type, culture, unit)** the culture may field.
The cultist mod's 11 rows are exactly that shape -

```
dignitary | wh_main_chs_chaos    | kho_brass_cultist
dignitary | wh_main_chs_chaos    | wh3_main_kho_cha_cultist_0
dignitary | wh3_main_nur_nurgle  | nur_deathbell_cultist
champion  | wh3_main_dae_daemons | wh3_main_sla_cha_cultist_0
runesmith | wh_dlc08_nor_norsca  | wh3_main_kho_cha_cultist_0
```

- one row per foreign hero unit it wants a culture to be able to field.

Vanilla's Chaos Dwarf `engineer` entry lists exactly one unit,
`wh3_dlc23_chd_cha_infernal_castellan`. **`wh2_dlc11_cst_cha_gunnery_wight_0` is not in it.** The
Castellan's actions dispatch; the Wight's do not; and embedding puts that same unit into an army.

### 17.4 The row added

`Modding Files/source/naval_horde/export/zz_agent_culture_details.tsv`, a new fragment at
`db/agent_culture_details_tables/derpy_chd_naval_horde`, table **version 9** (CA's):

```
634426295  engineer  wh3_dlc23_chd_chaos_dwarfs  wh2_dlc11_cst_cha_gunnery_wight_0  ""  0  ""  m  ""  ui/campaign ui/agents/wh2_dlc11_cst_engineer.png  true
```

It is CA's own `(engineer, wh2_dlc11_cst_vampire_coast)` row (key 1928090079) with the culture
swapped and a fresh key. `check()` pins that: the row may differ from CA's donor in `key` and
`culture` **only**, and must bind `WIGHT_UNIT` to `engineer` in the Chaos Dwarf culture.

**The numeric key matters.** It is the primary key, and a duplicate drops a row in silence. 634426295
was checked free against vanilla's 186 rows *and* every `agent_culture_details` row in the **17
installed mods** that ship the table - 436 keys in use, none of them this one. Seventeen mods ship
this table, so a lazily chosen id is a real collision risk here, unlike most tables.

`recruitable_in_ui` is `true`, matching both CA's two engineer rows and every row the cultist mod
adds. If a spurious Gunnery Wight entry appears in the hero panel of Chaos Dwarf factions that
cannot recruit it, that flag is the one to flip - CA uses `false` on the Nurgle engineer row and
the Chaos Dwarf spy row for exactly that reason.

Pack sha1 `f7c1849d9abd5fab70f46bab821f23f3ea2bedc3`.

### 17.5 Confidence, honestly

This is a mechanical gap with a working precedent doing our exact trick, which the VO theory never
had. It is still not proven until it is clicked. If it fails too, the next step is **not** another
single-cell guess: take `alshua_cultists.pack` and diff its whole agent-side table set against
ours, since it is a small mod that demonstrably makes cross-race heroes work -
`agent_actions_tables`, `campaign_group_agent_action_foreign_slots_tables` and
`effect_bonus_value_agent_action_record_junctions_tables` are the next three it ships and we do not.

---

## 18. The Gunnery Wight is withdrawn, and the Vampire Coast roster is DLC-locked

Both at the player's instruction, 2026-09-02. Pack sha1 `0bb803a7b3344defe95a7f069fa66d9cb907ea0c`,
deployed to the Workshop folder.

### 18.1 Recruitment withdrawn, not deleted

`agent_culture_details` did not fix it either, so the grant comes out rather than shipping a hero
that cannot act. Everything sections 14-17 built is still in `tools/gen_naval_horde_admiral.py`,
behind one flag:

```python
WIGHT_ENABLED = False
```

Set it back to `True` and re-run the two generators to restore the whole grant. What the flag
gates, in both generators:

| Table | With the flag on | Now |
|---|---|---|
| `faction_agent_permitted_subtypes` | 1 row, wight to `cr_chd_black_kraken_armada` | 12 rows, none the wight |
| `effect_bonus_value_agent_subtype_junctions` | 1 `availability` row | fragment **deleted** from the pack |
| `agent_subtypes` | CA's row rewritten with names group and VO culture | 14 rows, no wight |
| `agent_culture_details` | 1 row, key 634426295 | fragment **deleted** from the pack |
| `units_to_groupings_military_permissions` | 26 rows (25 VC + the wight's character unit) | 25 rows |

`check()` has an `else` branch that asserts all four are absent - a half-granted hero is exactly
the state that shipped broken, so it cannot come back one row at a time. It also asserts
`gen_naval_horde_tordrek.WIGHT_ENABLED is WIGHT_ENABLED`; the second generator imports the flag
rather than copying it, so the two cannot disagree.

**Two new pieces of plumbing came out of this**, both in `tools/import_naval_horde.py`:

- A TSV that generates to **zero rows** now gets `delete_packed_files` instead of `import_tsv`.
  Without that a generator which stops owning a table leaves a zero-row fragment in the pack for
  good, since `import_tsv` can only replace a file, never remove one.
- The campaign scripts under `Modding Files/pack/script/campaign/*/mod/` named in `SCRIPTS` are
  added on **every** run. They were previously hand-added, which is how a staged `.lua` goes stale
  against the one the pack actually ships.

### 18.2 The Vampire Coast lock

Tordrek's roster is 25 Curse of the Vampire Coast units. CA already tags **all 25** in
`main_unit_ownership_content_pack_junctions` against `wh2_dlc11_vampire_coast`, which resolves
through `ownership_content_pack_required_products` to the product `TW_WH2_DLC11_VAMPIRE_COAST`
(Steam app 835670). That gate should hide them from a non-owner on its own - but it has never been
measured against a **modded** recruitment source, and it cannot be measured on this machine, which
owns the DLC. So the pack carries its own lock as well.

`script/campaign/{cr_combi_expanded,cr_darklands,cr_oldworld,wh3_main_combi}/mod/derpy_chd_vc_unit_lock.lua`
- **generated** by `gen_naval_horde_tordrek.py` from the same set that fills
`units_to_groupings_military_permissions`, so a unit added to Tordrek's chains cannot be left out of
the lock. `check()` compares the two and also refuses if a copy on disk was hand-edited.

The shape is `derpy_vraznak_units_confed.lua`'s, minus the confederation half:

- `cm:is_dlc_flag_enabled(product_key, faction_key)` - **two strings**, product first.
- `cm:add_event_restricted_unit_record_for_faction(unit, faction, tooltip)` restricts;
  `remove_...` lifts. There is no granting counterpart, so the DB grants and the script locks.
- Runs on **every** load, not new-game-only, and is idempotent both ways. The removal branch is not
  decoration: restrictions are written into the save, so a player who buys the DLC mid-campaign
  carries them until this pass lifts them.
- **Human factions only.** DLC ownership is a property of a player, and CA's own
  `campaign_manager:faction_has_dlc_or_is_ai` answers `true` for every AI faction for that reason.

The tooltip is `ui_text_replacements_localised_text_derpy_vc_unit_locked`, "Requires Total War:
WARHAMMER II - Curse of the Vampire Coast." - the same loc namespace the house-unit lock uses.

Checks that ran clean: `luac -p`, `check_lua_api.py` (0 suspect calls, so `cm:get_human_factions`
and both restriction calls are documented), `check_lua_undeclared.py` (0 undeclared names).

### 18.3 What is untested

The lock itself cannot be exercised here - every path through it needs a machine without the DLC.
What was verified is that the script parses, that every call in it is in CA's documentation, that
the unit list matches the roster exactly, and that the four copies are in the saved pack byte for
byte. On a machine that owns the DLC the script takes the `remove_...` branch, which is a no-op
against a save with no restrictions in it.

---

## 19. The starting development points are gone, and the mirror had drifted

Pack sha1 `fbe0118f28de364e1481af7d191065c0465d0cb0`, deployed.

### 19.1 What was granting them

Reported as "debug 20 growth" on both ships. It was **not** growth and not in the DB - the only
`wh_main_effect_hordebuilding_growth_core` rows anywhere are the flagship at a flat 10 and the
anchor at 2/4/6, and a flat 10 on the primary is **CA's own shape** (Malakai's airship hull 1-5 and
the Lizardmen ziggurat 1-5 are all 10; 15 of vanilla's 47 rows are). A byte scan of the game data
folder plus all 665 workshop packs found that one fragment and no other derpy growth row.

It was `cm:add_development_points_to_horde`, granted at start:

| Script | Was | Now |
|---|---|---|
| `cr_oldworld/mod/derpy_start_abnagg.lua` | **20**, plus an 18-point `FactionTurnStart` top-up listener | none |
| `cr_combi_expanded/mod/ime_derpy_abnagg.lua` | **20**, plus the same top-up listener | none |
| `cr_oldworld/mod/derpy_start_tordrek.lua` | 2 | none |
| `cr_darklands/mod/derpy_start_tordrek.lua` | 2 | none |

The `derpy_naval_horde_devpoints_granted_*` saved value went with them - it existed only to gate
the top-up. Each grant site keeps a three-line comment saying it was removed deliberately.

Nothing breaks: the two starting buildings are handed over by `cm:add_building_to_force` and cost
no development points, and the flagship pays 10 growth a turn. The ship now starts at zero points
and earns its second tier instead of being handed it.

### 19.2 The mirror had drifted, and the wrong way round

`Modding Files/pack/` is meant to be the source of truth, and for the two Abnagg scripts it was
**older than the pack**: on disk sat a revision granting 2 points with a debug readback calling
`slot_list()` (a method that does not exist - it is `military_force_slot_list`, section 1.1);
in the pack sat the newer 20-point revision with the top-up listener. So the live bytes were the
base for this edit, never the mirror - shipping the mirror unchecked would have reverted a real fix
and reintroduced a broken call.

[[pack-lua-carves-out-of-binary]] already says to carve the pack copy and diff before editing a
staged `.lua`; what it did not say is that the pack can be the newer side. Both directions now.

**The structural fix** is in `tools/import_naval_horde.py`: `SCRIPTS` names the campaign scripts
this pack owns and they are re-added from the mirror on **every** import, so the pack can no longer
hold a revision the mirror does not. It now carries `derpy_chd_naval_admiral.lua`,
`derpy_chd_vc_unit_lock.lua`, `derpy_start_abnagg.lua`, `derpy_start_tordrek.lua` and
`ime_derpy_abnagg.lua`. Add a basename there the first time you edit that script.

Checks: `luac -p` on all four, `check_lua_api.py` (0 suspect calls), `check_lua_undeclared.py`
(0 findings), and a byte scan of the saved pack confirming **0** remaining
`add_development_points_to_horde` or `devpoints_topup` occurrences.
