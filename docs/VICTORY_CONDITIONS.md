# Victory conditions, end to end

Verified 2026-09-04 against WH3 `data_script.pack`, the RPFM `schema_wh3.ron` table list, and
a scan of all 667 installed packs (405 Workshop + the game's own).

The one-line summary: **victory conditions are not a DB table.** They are a plain Lua table
that the campaign's script root declares at load, keyed by faction, subculture and alignment,
and read back once in a first-tick callback. Editing them means writing a mod script that
mutates that table before first tick. Nothing else works.

---

## 1. The seven `victory` tables, and why six of them are red herrings

`schema_wh3.ron` has exactly seven table names containing "victor":

| Table | Rows | What it actually does |
|---|---|---|
| `victory_types` | 18 | Names the victory **types** and their UI: `tree_x`/`tree_y`, `icon`, `length_type` (`short`/`long`), `should_show_end_game_ui`. **No objectives.** |
| `victory_type_links` | 6 | `from`/`to` chain, e.g. `wh_main_victory_type_short` -> `wh_main_victory_type_long`. Draws the ladder, gates nothing. |
| `victory_conditions` | 12 | `BATTLE_SETUP_VICTORY_CONDITION_*`. **Battle** setup, not campaign. |
| `battle_types_to_victory_conditions` | - | Same, battle side. |
| `campaign_victory_conditions` | 10 | Steam achievement keys per campaign/difficulty (`WH3_ACHIEVEMENT_WINNING_IE_HARD`). |
| `achievement_campaign_victory_condition_junctions` | 338 | Ditto. |
| `start_pos_victory_conditions` | - | Assembly Kit **startpos** table. Only reachable through a full `Build Startpos` (`MOD_DEV_NOTES.md` step 3), and CA does not use it for the WH3 campaigns. |

So there is **no DB row anywhere** that says "faction X wins by doing Y". Grepping `db/` for a
faction's victory objectives returns nothing because nothing is there.

The 18 `victory_types` rows do matter in one way: `mission_manager:set_victory_type()` takes one
of these keys, and Immortal Empires uses four of them:

```
wh3_combi_victory_type_multiplayer   short
wh3_combi_victory_type_faction       short   -- "short victory"
wh3_combi_victory_type_subculture    long    -- "long victory"
wh3_combi_victory_type_domination    long
```

---

## 2. Where the objectives really live

`script/campaign/main_warhammer/required.lua` line 35:

```lua
require("victory_objectives")
```

which loads `script/campaign/main_warhammer/victory_objectives.lua` — 5,472 lines (5,635 in
9.0), a global
table plus about a dozen methods. The table has five sections:

```lua
victory_objectives_ie = {
    victory_type = { multiplayer = ..., faction = ..., subculture = ..., domination = ... },
    multiplayer  = { objectives = { ... } },
    alignments   = { order = {...}, destruction = {...}, death = {...}, chaos_dwarfs = {...}, ... },
    subcultures  = { wh3_dlc23_sc_chd_chaos_dwarfs = { alignment = "chaos_dwarfs", objectives = {...} }, ... },
    factions     = { wh3_dlc23_chd_zhatan = { objectives = {...} }, ... },
}
```

and at the bottom, the thing that runs it:

```lua
cm:add_first_tick_callback_new(function()
    local human_factions = cm:get_human_factions()
    ...
    victory_objectives_ie:initialise_victory_missions(faction_key, multiplayer)
end)
```

Four missions get built per human faction:

| Mission key | Victory type | Built from |
|---|---|---|
| `wh_main_short_victory` | faction | `factions[key].objectives` + `alignments[a].wh_main_short_victory.objectives` |
| `wh_main_long_victory` | subculture | a `SCRIPTED` "complete the short victory" step, + `alignments[a].wh_main_long_victory.objectives`, + `factions[key].long_objectives`, + `subcultures[sc].objectives` |
| `wh_main_domination_victory` | domination | hardcoded `OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS total 272` |
| `wh3_main_mp_victory` | multiplayer | `multiplayer.objectives`, MP only |

The alignment is read off the **subculture**, not the faction: `subcultures[sc].alignment`,
falling back to `alignments.default` (`"destruction"`).

**9.0 added a second, VCO-style system beside it** in the same script root:
`victory_objectives_config.lua` declares `_victory_objectives_ie` (leading underscore), fills
its `config.factions` (114 factions, CA's three Chaos Dwarf lords among them, no `cr_chd_*`)
on `WorldCreated`, and issues their missions in its own first-tick callback, setting the saved
value `IEVictoryConditionUseDLC29Config`. The old `victory_objectives_ie:initialise_victory_missions`
now returns early for any faction that config covers (`victory_objectives.lua:4299-4306`), so
everything in §3 and §8 still applies to a faction it does not. A save started before 9.0
keeps the old system. See `sessions/HANDOFF_20260924_UPDATE_9_0_COMPAT_AUDIT.md` §3, and §10
below for its reward switch.

---

## 3. The trap: no `factions[]` entry kills the subculture objectives too

`create_long_objective`, verbatim:

```lua
function victory_objectives_ie:create_long_objective(mm, faction_subculture_key, faction_key)
    local objectives = {}
    local faction_table = self.factions[faction_key]

    if faction_table then
        local used_long_objectives = cm:is_multiplayer() and faction_table.long_mp_objectives or faction_table.long_objectives
        if used_long_objectives then ... end

        if self.subcultures[faction_subculture_key] and faction_table.no_subculture_objective ~= true then
            for _,objective in pairs(self.subcultures[faction_subculture_key].objectives) do ... end
        end

        if #objectives > 0 then self:add_objectives(mm, objectives, faction_key) end
    end
end
```

The subculture block is **inside** `if faction_table then`. CA's own comment above the
`factions` table says "This table is optional; the script still populates all victory
conditions without a faction-specific objective" — that is wrong for the long victory.

A faction with no `factions[]` entry gets a long victory of exactly two things: "attain your
faction victory", and the alignment fallback (`occupy/loot/raze/sack 60 settlements`). It loses
the whole subculture objective set. For Chaos Dwarfs that is:

- own Zharr Naggrund
- destroy the Dwarfs, Karak Kadrin and the Greenskins
- **and on the Old World map**, three extra `SCRIPTED` hellshard steps

Cataph's `cr_oldworld` fork has the same guard, phrased slightly differently, with the same
effect.

**All eleven of our playable houses were in that state** — verified by grepping the `factions`
table in both CA's file and Cataph's for `cr_chd_*` and `wh3_dlc23_chd_conclave`: zero hits in
either. Registering an entry, *even an empty one*, is the whole fix.

---

## 4. The global is different in every campaign

`required.lua` resolves `require("victory_objectives")` against its own campaign folder first,
so the table lands under a different global name depending on which script root the campaign
points at:

| Script root | Global | Campaigns using it |
|---|---|---|
| `script/campaign/main_warhammer` | `victory_objectives_ie` | `wh3_main_combi` (IE), `cr_combi_expanded` (IEE) |
| `script/campaign/cr_oldworld` | `victory_objectives_oldworld` | `cr_oldworld` |
| `script/campaign/wh3_main_chaos` | `victory_objectives` | Realms of Chaos |
| `script/campaign/wh3_main_prologue` | — | prologue has none |

Those four are the **only** script roots any installed pack ships; every mod campaign reuses
one of them via `campaigns_tables.script_path`.

**And which one `cr_oldworld` gets is not stable.** Seven installed packs re-declare the
`cr_oldworld` row in `campaigns_tables` with `script_path = script/campaign/main_warhammer`:

```
!scm_totn.pack        !scm_lccp.pack       !scm_marienburg.pack   !scm_empire_secessionists.pack
ovn_araby.pack        ovn_grudgebringers.pack                     nag_nagash.pack
```

Duplicate primary key, last pack loaded wins, so with those installed the Old World campaign
runs `main_warhammer` and declares `victory_objectives_ie` after all. Hard-coding either name
is a guess about the player's mod list — **probe for the table instead**.

Note also: `cr_darklands` is referenced by Cataph's `campaignselect.cco` and by a
`CND_CAMPAIGN` condition, but **no installed pack ships a `campaigns_tables` row for it**, so
that campaign does not currently exist. The 28 Lua files the lords pack stages under
`script/campaign/cr_darklands/mod/` never load today. They are harmless and future-proof; they
are not a place to test anything.

---

## 5. Where a mod script goes, and when it runs

`script/campaign/<campaign_key>/mod/*.lua` — the campaign key from `campaigns_tables`, not the
script-root folder. (`script/campaign/mod/*.lua` loads for every campaign.) These load **after**
`required.lua` and **before** first tick, which is the window the whole technique depends on:
the table exists, and CA has not read it yet.

Write at file scope. Do not defer to a first-tick callback — CA registers its own at require
time, so yours would run after the missions were already built.

That rule is about **touching CA's table** — adding a `factions[]` entry, or installing a
wrapper round `initialise_victory_missions`. *Issuing* a mission of your own with
`cm:trigger_custom_mission_from_string` is the opposite case and belongs in a first-tick
callback, because it needs a live `cm` and the faction list. A file can do both: wrapper at
file scope, trigger on first tick. §11.

---

## 6. The objective vocabulary

Counted across CA's `main_warhammer/victory_objectives.lua` and Cataph's `cr_oldworld` fork
(the conditions each type is actually given, by frequency):

| `type` | Conditions it takes |
|---|---|
| `SCRIPTED` | `script_key`, `override_text`, and optionally `total` / `count` / `count_completion` |
| `DESTROY_FACTION` | `faction` (repeat per target), `confederation_valid`, `vassalization_valid` |
| `CONTROL_N_PROVINCES_INCLUDING` | `province` (repeat), `total`, `override_text` |
| `CONTROL_N_REGIONS_FROM` | `region` (repeat), `total`, `override_text` |
| `OWN_N_REGIONS_INCLUDING` | `region` (repeat), `total`, `subculture`, `override_text` |
| `OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS` | `total` |
| `RAZE_OR_OWN_SETTLEMENTS` | `region` |
| `HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE` | `pooled_resource`, `total` |
| `CONSTRUCT_N_BUILDINGS_FROM` | **`faction`**, `building_level` (repeat), `total`, `override_text` |
| `CONSTRUCT_N_BUILDINGS_INCLUDING` | **`faction`**, `building_level`, `total` |
| `CONSTRUCT_N_OF_A_BUILDING` | **`faction`**, `building_level`, `total` |
| `PERFORM_RITUAL` | `ritual_category` or `ritual`, `total` |
| `COMPLETE_N_MISSIONS_OF_CATEGORY` | `event_category`, `total` |
| `FIGHT_SET_PIECE_BATTLE` | `set_piece_battle` |
| `ACHIEVE_CHARACTER_RANK` | `total`, `start_pos_character`, `include_generals` |
| `OWN_N_UNITS` | `total` |
| `ALL_PLAYERS_RAZE_SACK_OR_OWN_X_SETTLEMENTS` | `total` — MP only |

The three `CONSTRUCT_N_*` types are special-cased in `add_objectives`: the script appends
`"faction " .. faction_key` itself, "these objectives will fail if we don't add them here".
**That is not a footnote, it is mandatory, and it fails silently.** Measured 2026-09-09: a
`CONSTRUCT_*` objective with no `faction` line kills the WHOLE mission - the route draws no node
in the victory panel at all, with no log line, no parse complaint and `trigger_mission_from_string`
still echoing the block as issued. Ghorth was issued five routes and drew two; the three dead ones
were exactly the three holding a `CONSTRUCT` objective. VCO writes the line on 157/157 of its
`CONSTRUCT` objectives (`CONSTRUCT_BUILDING_IN_PROVINCES` included) and `pow_victory_conditions`
on 19/19. The value is the mission's own faction key.

This is a subset. The full `mission_type` vocabulary is 89 keys — see `MISSIONS.md`, and note
that it ships **no DB table**, so a type outside the list above is not necessarily invalid.

### `SCRIPTED` objectives

180 of CA's victory objectives are `SCRIPTED`, i.e. the script owns the monitoring. Two calls
drive them, both used in `victory_objectives_ie:add_scripted_victory_listeners()`:

```lua
cm:complete_scripted_mission_objective(faction_key, mission_key, script_key, true)
cm:increase_scripted_mission_count(mission_key, script_key, 1)   -- for count / count_completion
```

`override_text` is **mandatory** on a `SCRIPTED` objective — there is no mission-type row to
supply a string, so without it the objective line is blank.

---

## 7. Rewards, and the `game_victory` payload

`trigger_mission` builds the payload before triggering:

```lua
bundle    = alignments[alignment][mission_key].payload_bundle      -- overridable per faction
ancillary = alignments[alignment][mission_key].payload_ancillary
```

Each becomes `effect_bundle{bundle_key X;turns 0;}` or `add_ancillary_to_faction_pool{...}`,
and a table of either is allowed. Then:

```lua
if (bundle == nil and ancillary == nil) or victory_type == multiplayer or victory_type == domination then
    mm:add_payload("text_display dummy_wh3_main_survival_forge_of_souls")
    mm:add_payload("game_victory")
end
```

So `game_victory` is **not** what ends the campaign for the short and long victories — the
`mm:set_victory_type(...)` call is. `game_victory` is the fallback for a mission that would
otherwise have no payload at all and so "fail to generate". Worth knowing before copying it
into a custom objective.

The Chaos Dwarf alignment rewards, for reference:

```
wh_main_short_victory  payload_bundle = "wh3_dlc23_ie_victory_objective_chaos_dwarfs_short"
wh_main_long_victory   payload_ancillary = { lesser relics of skavor / morgrim / smednir }
```

### What the routes in this workspace pay (2026-09-09)

Each route pays **one purse and one trophy**, and the purse differs per route - a route may pay
one currency only. Ghorth's five pay the purse alone (`NO_TROPHY_FACTIONS`: he already holds
the Tower). Seven purses, in `gen_victory_routes.py`:

```
0  materials 8000                                  (one currency)
1  armaments 4000                                  (one currency)
2  money 30000                                     (one currency)
3  materials 4000 + armaments 1500
4  armaments 2000 + influence 400
5  money 15000 + materials 3000
6  materials 6000 + armaments 2500 + influence 200
```

emitted as, for purse 5:

```
game_victory;
money 15000;
faction_pooled_resource_transaction { resource wh3_dlc23_chd_raw_materials; factor missions; amount 3000; context absolute; }
add_ancillary_to_faction_pool       { ancillary_key <one of eight derpy_trophy_* items>; }
```

Both purse and trophy are picked by `(house index + route index)`, the purse mod 7 and the
trophy mod 8: no house pays the same purse or the same item twice, and the two do not travel
together. 13 of the 46 routes pay treasury. A new house goes LAST in `ROUTES`, because the
rotation runs on `HOUSES.index` and an insertion would move every later house's rewards. Five
things pinned the shape:

* **`factor missions` is CA own and is the only factor verified grant-capable on all three
  pools** - `min 0 / max 2147483647` on raw materials and Conclave influence, unbounded both
  ways on armaments, straight out of `pooled_resource_factor_junctions`. Most factors are
  bounded ONE way and an amount pushed the wrong way through one clamps to nothing in silence,
  which is why this is not `wh3_dlc23_chd_mined` or `..._consumed`.
* **`wh3_dlc23_chd_labour` cannot be paid at all.** Its `pooled_resources` scope is
  FACTION_PROVINCE, and such a pool answers with a null interface at both the faction and the
  province level. Asking for labour in an *objective* is fine - the engine reads that itself -
  and route V does; paying it is not, and `check()` refuses it.
* Amounts are read against the start this workspace sets Ghorth (10,000 gold, 2,500 raw
  materials, 1,000 armaments, 0 influence) and against what the routes ask for (60-400
  influence), so a mixed purse is about a doubling of a starting stock and a single-currency
  purse about double that again - a narrow reward is not a smaller one.
* **`money` needs no transaction block** - it is the bare statement `money <n>;` in the payload,
  which is also the only shape measured *paid* through the string route (treasury 14091 ->
  16591 on `money 2500`, `docs/MISSIONS.md` section 12). It sits beside the pooled transactions in
  the same payload; PoW mixes payload entries the same way. A flat 50,000 treasury on all 35
  routes was the first draft and is the wrong reward for a Chaos Dwarf faction, but gold as one
  purse among seven is not.

* `money` is attested in `pow_victory_conditions` (as `money -70000`, a **cost** - the sign is
  the obvious inverse, and `check()` refuses a non-positive amount in any purse);
  `add_ancillary_to_faction_pool` is what CA itself gives the Chaos Dwarf long victory above.
* **The reward IS previewed on the panel, pooled resources included.** Measured 2026-09-09: the
  victory-conditions panel draws a `Reward` box under the objectives, each line in green with
  its own icon and display name - "Treasury: +50000" for `money`, and "Raw Materials: +5000",
  "Armaments: +2500", "Conclave Influence: +250" for three
  `faction_pooled_resource_transaction` entries, plus the item. So a pooled-resource payload
  previews exactly the way `money` does, no `text_display` needed, and a wrong reward is visible
  long before the campaign ends.
* **A trophy must be something the player is not already getting.** Two filters, both learned
  the hard way:
  1. **Not one of the lords pack own 37 per-lord items.** They are bound to the lord in
     `ancillaries_required_skills` and handed over as he *levels*, so the first build offered
     Ghorth the Mace of Dominion for a route that would have given it to him anyway. `check()`
     now refuses any key in `SKILL_GRANTED_ANCILLARIES`.
  2. **Not `randomly_dropped`**, and **not one of CA's eight Dwarf-god relics.** CA's six
     `wh3_dlc23_anc_banner_chd_*` banners all carry the flag and arrive on their own; the
     relics arrive through the Great Drill chain (`derpy_chd_drill_chain.lua`), which every
     house plays.
  3. **Not locked to one character.** CORRECTED 2026-09-24: the first pool was vanilla, and a
     `faction_set` says nothing about WHO may equip an item - `ancillaries_included_agent_subtypes`
     does. Five of the eight had a row there: the Obsidian Axe, Armour of Gazrakh and Chaos
     Runeshield are Zhatan's, and the Dagger of Malice and Banner of Slavery are Gorduz
     Backstabber's. No house lord could wear them. A player reported it.
* **The trophies are minted, in the lords pack itself.** Once all three filters were applied,
  every strong vanilla Chaos Dwarf item was locked, randomly dropped, a relic or a convoy reward.
  So `TROPHY_ITEMS` defines eight `derpy_trophy_*` items (two each of weapon, armour, talisman
  and enchanted item). Each is faction set `all`, transferable, unique band 200, and has no
  subtype or skill row. Their three tables and loc ship in the same pack as the script that pays
  them, so the payload key always resolves. That avoids the whole-mission drop of §10 bullet 1,
  which is also why the 430 house ancillaries in `derpy_chd_house_ancillaries.pack` stay out. Every effect is one
  vanilla already puts on an ancillary, scoped by `anc_effect_scopes.SCOPE`. Every ability
  effect binds through a plain `effect_bonus_value_unit_ability_junctions` row with no unit set.
  `check()` refuses any reward that is not a `TROPHY_ITEMS` row, and `--selftest` puts Zhatan's
  axe back to prove the check catches it. Missions are issued on a new game only, so a
  campaign started before this change still pays the old items.

**One unattested detail, deliberately:** the payload keeps `game_victory` *beside* the reward,
where CA adds it only when there is neither a bundle nor an ancillary (the `if` above). It is
kept because `mm:set_victory_type` has no counterpart in the string route beyond the
`victory_type` line, and because the cost of the mix being rejected is visible in one look at
the panel - the route simply draws no node. If a route ever disappears after a reward edit,
drop `game_victory` first.

---

## 8. The per-faction entry: every field

```lua
victory_objectives_ie.factions["my_faction"] = {
    objectives            = { ... },   -- SHORT victory
    long_objectives       = { ... },   -- LONG victory, singleplayer
    long_mp_objectives    = { ... },   -- LONG victory, multiplayer (replaces long_objectives)
    no_subculture_objective = true,    -- drop the subculture objectives from the long victory
    no_alignment_objective  = true,    -- drop the generic "paint the map" objective from both
    wh_main_short_victory = { payload_bundle = "..." },  -- override the alignment reward
    wh_main_long_victory  = { payload_bundle = "..." },
}
```

An objective is `{ type = "...", conditions = { "keyword value", ... } }`. Conditions are
space-separated strings, one keyword per entry, repeated for lists.

---

## 9. Reference implementations harvested from installed mods

27 of 667 installed packs touch victory conditions. The useful ones:

### `ab_mixu_legendary_lords.pack` — the canonical faction-mod pattern
`script/campaign/wh3_main_combi/mod/mixu_ll_victory_objectives.lua`, 539 bytes, whole file:

```lua
victory_objectives_ie.factions["mixer_emp_van_der_kraal"] = {
    objectives = {
        {
            type = "HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE",
            conditions = { "pooled_resource cst_infamy", "total 25000" }
        }
    },
    no_subculture_objective = true
}
```

Direct assignment at file scope, no guard, no ceremony. This is the whole technique.

### `!obsidian_lustria_rises.pack` — same thing in `script/campaign/mod/`
Applies to every campaign rather than one. Uses `objectives` + `long_objectives` on the same
faction, and shows the `CONSTRUCT_N_BUILDINGS_INCLUDING` / `CONTROL_N_PROVINCES_INCLUDING`
/ `DESTROY_FACTION` mix.

### `victory_conditions_overhaul.pack` — how to *disable* CA's, and the safety guard
`script/campaign/mod/vco-disable-ca-wincons.lua` wraps the entry point instead of editing data:

```lua
if not victory_objectives_ie then
    out("VCO Patch: Not in Immortal Empires (or object missing). Skipping victory override.")
    return
end

local old_init = victory_objectives_ie.initialise_victory_missions

function victory_objectives_ie:initialise_victory_missions(faction_key, multiplayer)
    if DISABLED_VICTORY_FACTIONS[faction_key] then return end
    old_init(self, faction_key, multiplayer)
end
```

Note the `if not victory_objectives_ie then return end` guard — the global genuinely is absent
in some campaigns, and this is the mod that learned it.

VCO's own objectives live in `script/vco-ie/main_warhammer/<FACTION>/missions.lua`, 100+ files,
one per faction, each returning a list of **mission blocks in the old `missions.txt` syntax**
which a loader hands to `cm:trigger_custom_mission_from_string`. **This corrects an earlier
reading here that had them building a mission manager by hand** — they do not touch
`mission_manager` at all, and the route is far lighter than that made it sound. §11 documents
the whole method.

### `rhox_chorf_ime_drill.pack` — editing CA's reward rather than the objectives
```lua
victory_objectives_ie.alignments.chaos_dwarfs.wh_main_long_victory.payload_ancillary = nil
victory_objectives_ie.alignments.chaos_dwarfs.wh_main_long_victory.payload_bundle = "wh3_main_ie_victory_objective_chaos_long"
```

### `!cr_oldworld_campaign.pack` — the fork
Ships a 230KB `script/campaign/cr_oldworld/victory_objectives.lua` declaring
`victory_objectives_oldworld`. Adapted from CA's, with the region keys rewritten to the
`cr_oldworld_region_*` prefix and the Chaos Dwarf subculture given three extra hellshard
`SCRIPTED` steps.

### Others touching it
`inq_lol_hero` (`hol_victory_objectives.lua`, plus a `.loc` of its own),
`ovn_citadel_of_dusk` / `ovn_grudgebringers` / `ovn_araby` (each also ships a
`victory_types_tables` row), `!scm_totn`, `!scm_legendary`, `nag_nagash`,
`!!gra_knights_origo`, `hsp_grom_eltharion`, `!!!hecleas_grand_strategy`,
`lingling_lzd_chars`, `@MOD_estalia_overhaul_red`, `@MOD_tilea_overhaul_red`.

---
## 10. Traps

- **A `CONSTRUCT_*` objective with no `faction` line silently kills its whole route.** §6.
  Two of Ghorth's five routes drew because three carried one. Nothing logs it.
- **The victory panel draws at least five route nodes.** Measured 2026-09-09 with Ghorth's five,
  all five in the left rail and each selectable - it does not clip at four the way the Tower of
  Zharr's district list does. Vanilla's own `wh3_combi_*` set runs `tree_y` 0..4.
- **No `factions[]` entry silently deletes the subculture long victory.** §3. The single
  highest-value fix for any faction mod that uses CA's table — and irrelevant if you disable
  CA's entry point instead, which is what this workspace now does. §12.
- **The global's name is campaign-dependent and load-order-dependent.** §4. Probe, do not name.
- **The mod script environment is not `_G`.** Measured 2026-09-07 in a live `cr_oldworld`
  campaign: `victory_objectives_oldworld` resolves as a plain global read while
  `rawget(_G, "victory_objectives_oldworld")` is `nil`. So a loop over
  `{"victory_objectives_ie", ...}` doing `_G[name]` finds **nothing**, in every campaign,
  and reports the table as absent when it is right there. Read the globals by name.
- **`cm:get_campaign_name()` is not the campaign key, and is not derivable.** It returns
  whatever that campaign's own start script passed to `set_campaign_name`
  (`lib_campaign_manager.lua:714`) — measured `cr_oldworld` on the Old World map, while VCO's
  folder for Immortal Empires is `main_warhammer`, a *script root*. Seven installed mods
  redeclare the `cr_oldworld` row in `campaigns_tables`, so even that is not stable. Do not
  build a `require` path out of it without measuring on the map you ship for.
- **Region and province keys carry the campaign prefix.** `cr_oldworld_region_zharr_naggrund`
  vs `wh3_main_combi_region_zharr_naggrund`. A script shared across campaigns cannot hard-code
  either; resolve with `region_by_key()` — which lives on
  `cm:model():world():region_manager()`, **not** on `cm` — and keep whichever answers (a key
  the map lacks returns a null interface, not an error). This is why Cataph forked the entire
  file, and why §12's routes are map-agnostic apart from the **map-gated** ones, which ship
  both halves and probe.
- **A `DESTROY_FACTION` target absent from the map is unachievable, silently and for ever.**
  Same failure shape as a typo. Probe the faction in a live campaign before shipping it in a
  victory condition, which — unlike a normal mission — cannot be patched out of a running save.
- **Faction, region, ritual and province keys are unvalidated strings.** A typo does nothing,
  for ever, with no error. Check every key against `db/` or the pack before shipping.
- **A Lua table constructor with a nil hole breaks `#`.** Collecting the three campaign globals
  into `{a, b, c}` when `a` is undefined gave `#t == 0` and the loop never ran — every house
  silently kept the entry it did not have. Test each global explicitly.
- **`game_victory` is not how the short/long victory ends the campaign.** §7. It is the payload
  of last resort, so that a mission with no payload at all does not fail to generate. The
  `victory_type` field is what ends the campaign.
- **`override_text` is mandatory on `SCRIPTED`.** §6.
- **9.0 withholds every victory payload in a new Immortal Empires or IEE campaign, ours
  included, unless something switches it back.** `_victory_objectives_ie:add_scripted_victory_listeners()`
  calls `cm:set_victory_mission_rewards_disabled(true)` on every load once
  `IEVictoryConditionUseDLC29Config` is set, commented "Victory mission payload will not be
  granted to player": CA pays its own factions through a Victory Achieved incident instead.
  The call is undocumented and campaign-wide. VCO's `vco-disable-ca-wincons.lua` calls it with
  `false` after CA's setup ("Override the global flag that broke VCO rewards"), which is the
  evidence it bites mission-string routes too. Since 2026-10-11 our routes do the same from a
  post-first-tick callback, only when a human is one of our houses. Section 12c.
- **A `SCRIPTED` objective nothing completes blocks the victory for ever.** It is only ever
  finished by `cm:complete_scripted_mission_objective`. VCO opens every route with one as a
  flavour-text line and carries listeners to complete them; if you are not writing those
  listeners, do not write the objective. §12.
- **`missions.txt` is dead as a *file*; the string route is not.** WH3 ships no `missions.txt`,
  but the block syntax that file used is alive and is a documented API —
  `cm:trigger_custom_mission_from_string(faction_key, block)`. **This corrects the earlier claim
  here that the string route only worked through `mission_manager:add_new_objective`.** VCO
  issues every one of its ~300 victory routes this way. §11.
- **Mod scripts must write at file scope**, not in a first-tick callback. §5. A wrapper round
  CA's entry point counts as writing: install it at file scope, and it is in place before the
  first-tick callback that reads the table.

---

## 11. The mission-string route — VCO's method, end to end

Everything above builds objectives by *adding to CA's Lua table*. There is a second, entirely
separate route that hands the engine a whole mission as text. Measured out of
`victory_conditions_overhaul.pack` (Workshop `3140200173`) on 2026-09-07, which is the largest
implementation of it in the wild — ~107 factions, three routes each.

**Use it when** you want named alternative victory paths with their own tree nodes and icons,
or an objective type the DB route cannot express (`DESTROY_FACTION` is absent from the Assembly
Kit's vocabulary but works fine here). **Do not use it** for a one-line "give this faction an
objective" — §8's table entry is three lines and participates in CA's own ladder.

### 11.1 The four moves

**1. Take CA's off the factions you are replacing.** Wrap the entry point rather than editing
data — CA's table is read in a first-tick callback, so a wrapper installed at file scope is
always in time:

```lua
local old_init = victory_objectives_ie.initialise_victory_missions

victory_objectives_ie.initialise_victory_missions = function(self, faction_key, multiplayer)
    if DISABLED[faction_key] then return end
    return old_init(self, faction_key, multiplayer)
end
```

VCO guards the whole file with `if not victory_objectives_ie then ... return end`, because the
global genuinely is absent in some campaigns. This is the mod that learned that.

**2. Write the objectives as a mission block.** The old `missions.txt` syntax, held in Lua as a
long string:

```
mission
{
    victory_type derpy_victory_type_house_of_baal_1_bind_the_kdaai;
    key derpy_route_victory_1;
    issuer CLAN_ELDERS;
    primary_objectives_and_payload
    {
        objective
        {
            type CONSTRUCT_N_OF_A_BUILDING;
            building_level wh3_dlc23_chd_military_kdaai_3;
            total 2;
        }

        payload
        {
            game_victory;
        }
    }
}
```

Every line is a block opener (`mission`, `objective`, `payload`,
`primary_objectives_and_payload`), a brace, or a `;`-terminated statement. The objective `type`
and condition keywords are **the same vocabulary as §6** — the table form's
`conditions = {"total 7", "province X"}` is these lines, one per entry.

**3. Issue it.** A documented call — `episodic_scripting.html` line 12161:

```lua
cm:trigger_custom_mission_from_string(faction_key, block)
```

**4. Mint the DB rows.** Two tables, and only two:

| Table | v | Rows | Shape |
|---|---|---|---|
| `victory_types` | 3 | one per route | `victory_type`, `tree_y`, `tree_x`, `icon`, `length_type`, `should_show_end_game_ui` |
| `missions` | 0 | one per *slot* | `mission_type SCRIPTED`, `event_category VictoryCondition`, `generate false`, `prioritised false`, `can_be_manually_cancelled true` |

`tree_y` stacks the routes down the victory tree (`0, 1, 2`); `tree_x` stays `0`. `icon` is a
bare filename under `ui/campaign ui/victory_type_icons/` — **CA's own are `short`, `long`,
`ultimate` and `domination`, so reusing those names ships no art**. VCO ships three of its own
instead. There is **no `victory_type_links` row** in VCO's pack at all; the links table draws
the ladder and gates nothing, so unlinked nodes are fine.

Loc keys: `victory_types_display_name_<victory_type>` names the node in the tree, and
`mission_text_text_<key>` supplies any `override_text`.

### 11.1b The objective vocabulary VCO adds, and which of it is map-agnostic

Counted over all 107 of VCO's `script/vco-*/<campaign>/<faction>/missions.lua` files on
2026-09-08. These are types CA never uses inside a *victory* objective; VCO is a shipped mod
whose entire content is victory missions issued by `cm:trigger_custom_mission_from_string`, so a
type it leans on is attested in this exact context.

| Type | VCO uses | Conditions | Map-bound? |
|---|---|---|---|
| `CONSTRUCT_BUILDING_IN_PROVINCES` | 131 | `faction`, `province`, `building_level` | yes |
| `MOVE_TO_REGION` | 57 | `region` | yes |
| `HAVE_CHARACTER_WOUNDED` | 37 | `start_pos_character` | startpos |
| `DEFEAT_N_ARMIES_OF_FACTION` | 26 | `total` | **no** |
| `CONTROL_N_REGIONS_INCLUDING` | 20 | `total`, `region`, `override_text` | yes |
| `CAPTURE_X_BATTLE_CAPTIVES` | 11 | `total` | **no** |
| `RECRUIT_UNIT` | 5 | `unit` | **no** |
| `ASSASSINATE_X_CHARACTERS` | 3 | `total` | **no** |
| `MAINTAIN_N_ALLIANCES` | 3 | `total` | **no** |
| `MOVE_TO_PROVINCE` | 1 | `province` | yes |
| `EARN_X_AMOUNT_FROM_RAIDING` | 1 | `total` | **no** |

Two condition keywords come with them: **`vassalization_valid`** (valueless, on
`DESTROY_FACTION` — CA 5 uses, VCO 33: a vassalised faction counts as destroyed) and
**`count_completion`**, which appears only beside `SCRIPTED`'s progress counter.

The six map-agnostic ones are the whole reason to read VCO: they are objectives a single file
serving four campaigns is allowed to use, and CA supplies none of them.

### 11.2 The two things VCO does that you probably should not copy

**One mission key for all three routes.** VCO gives every route `key vco_route_victory`. A
mission manager is keyed `(faction_name, mission_key)` —
`lib_campaign_mission_manager.lua:96` — so three live missions on one key is at best
unverified. Minting one `missions` row per route slot costs two extra rows and removes the
question entirely.

**The `<dummy>` prefix.** VCO opens each route with a `SCRIPTED` objective whose
`override_text` begins with a literal `<dummy>`, then finds it in the objectives panel at
runtime and strips it, to get a full-width unbulleted flavour paragraph:

```lua
if string.sub(dy_condition_uic:GetStateText(), 1, 7) == "<dummy>" then
    dy_condition_uic:SetStateText(dy_condition_uic:GetStateText():sub(8))
```

It is a nice effect and it is the source of most of the `<dummy>` bug reports on VCO's Steam
discussions: any script break anywhere stops the loader, and the raw marker is left on screen.
It also means every route carries a `SCRIPTED` objective, which only
`cm:complete_scripted_mission_objective` can ever finish.

**How VCO stops that blocking the victory — corrected 2026-09-08.** It completes them, from a
single always-on listener (`vco-listeners.lua:42-50`):

```lua
core:add_listener("vco_dummy_missions_check", "FactionTurnStart",
    function(context) return context:faction():is_human() end,
    function(context) vco:complete_mission(context:faction():name(), "vco_dummy") end,
    true)
```

429 flavour headers, one completer, fired every turn for every human faction. So the technique
*is* usable — the price is that every route in the file then depends on that listener still
running, and a victory condition cannot be patched out of a running save. §12d takes it since
2026-10-11, without the `<dummy>` marker and without the UI listener: the marker buys only the
unbulleted look and costs VCO most of its bug reports.

### 11.3 Multiplayer

VCO rewrites the mission key at trigger time, so one file serves both:

```lua
mission = mission:gsub("vco_route_victory", "wh3_main_mp_victory")
```

That works because VCO has exactly one key to swap. With one key per route it would collapse
three routes onto one MP key, so §12 leaves multiplayer on CA's own conditions instead.

---

## 12. What this workspace ships

`Modding Files/pack/script/campaign/mod/zzz_derpy_chd_victory_routes.lua` — **one file, not
four**. Generated by `tools/gen_victory_routes.py`; edit the generator.

Alternative victory routes for each of the thirteen playable houses — **three each, five for
the three houses Immortal Empires Expanded actually places, four for Kharkadon's Overlords of
Zharrduk** (`wh3_dlc23_chd_minor_faction`, added 2026-10-07) — built by §11's method.
Completing any one of a house's routes wins the campaign. 46 routes in all (the Uzkul Mingol
Company's three added 2026-10-11).

| Route | Theme | Icon |
|---|---|---|
| I | the house's own craft — the building, ritual or resource its skill line is about | `short` |
| II | the Tower — a `DISTRICTS_ANNEX_T5_*` ritual plus conclave influence | `long` |
| III | the war — `DESTROY_FACTION` plus settlements taken | `ultimate` |
| IV | *(the three IEE houses)* the fourth pillar of that lord's own skill line; *(Kharkadon)* The Extinction, Grimgor and the Dwarfs destroyed | `domination` |
| V | *(the three IEE houses)* the fifth — captives, labour, the fleet, the anvil | `long` |

Route names come from `docs/sessions/HOUSE_MISSION_OPTIONS_20260903.md` §5, which had already
drawn three lore-grounded quests per lord out of that lord's own skill line. A Lexicanum lore
pass on 2026-10-04 renamed or rewrote routes for seven lords — the Black Dwarf's I is now his
march on Praag, not a craft — **keeping every slug**, because the slug is part of the
`victory_types` key and a renamed key orphans the node in every running save
(`sessions/HANDOFF_20261004_LORE_ROUTES_AND_BALUR.md` §2). Kharkadon's four are in
`sessions/HANDOFF_20261007_KHARKADON_VICTORY_ROUTES.md`.

**Three houses carry five: Ghorth, Abnagg and the Black Dwarf — the ones IEE places.**
`ime_derpy_black_dwarf.lua` says it in its own header, and `zz_derpy_toz_annex.lua` logs it in
game: *"seated 2, skipped 8"*. **IEE places `cr_chd_slaves_of_the_black_dwarf` and
`cr_chd_warfleet_of_uzkulak` and none of the other eight `cr_chd` houses**, so with the vanilla
Conclave those three are the whole Chaos Dwarf roster a player meets there. They are the routes
that will be seen, so they carry the depth; the other eight keep three each.

Two things about the two IEE houses that are worth not re-deriving:

* **Their Tower route asks for two of district B's other three seats, and is completable
  anyway.** A house may claim any seat but its own; B has held four seats since the 2026-10-03
  swap moved Khorakk into it. The other two group-B houses (Tordrek's Black Kraken Armada and
  Khorakk) are absent from IEE, and that does not block the route: `zz_derpy_toz_annex.lua`
  decides per seat at runtime — ANNEX mode confederates a
  faction the campaign placed, **GRANT mode spawns the missing lord into the claimant's
  recruitment pool instead**. In IEE one claimable seat is the other of these two lords.
  The annex groups are read out of that Lua's `ANNEX_DISTRICTS` at generation time, never
  typed: a typed copy went stale twice.
* **`ime_derpy_abnagg.lua` spawns Abnagg on `wh3_main_combi_region_barak_varr` (185, 366) as a
  converted `DERPY_CHD_NAVAL_HORDE` with no settlement of his own.** His routes therefore count
  raiding, captives, sacked coasts and battles; exactly one of the five (Infernal Artillery)
  needs him to hold ground, and it asks for **one** `military_war_machines_3`, which already
  means a settlement grown to its top tier —
  `primary_slot_building_building_level_requirement = 5` on that row, 4 on
  `military_chaos_dwarf_infantry_3`, and `settlement_tower_N` wants level N. Read that column
  before writing any `CONSTRUCT_*` total: it is the difference between "build a barracks" and
  "grow two cities to maximum".

**Ghorth was the first to carry five, and is the only house that can ask across districts.**
`GHORTH_MISSION_OPTIONS_20260903.md` §1 names three identity pillars — Sorcerer-Prophet of
Hashut, Master of the Conclave, Tyrant of Zharr-Naggrund — and the three-route shape covered one
of them twice and the other two not at all. He is also the only house in **no annex group**, so
he is the only one whose Tower route can ask for seats in more than one district; every other
house sits inside one of the three and may not annex itself. VCO ships 3 routes for 129 of its
factions and 4 for the other 4, and vanilla's own `wh3_combi_*` set runs `tree_y` 0..4, so five
nodes in one tree is attested on both sides. The route **index is the slot index**, so a house
with three routes uses slots 1–3 and never sees 4 and 5.

Route slot rows carry the three derived loc keys (`missions_localised_title_*`,
`_description_*`, `_mission_completed_text_*`). Without them every route drew a **blank title**,
for all eleven houses — the DB columns are decoration, the loc is what the runtime reads
(`wh3-mission-title-is-loc-driven`).

**Four deliberate departures, each with a reason:**

- **One file in `script/campaign/mod/`, which loads in every campaign** — rather than VCO's
  `require` path keyed on `cm:get_campaign_name()`, which §10 shows is neither the campaign key
  nor derivable. With twelve factions the whole per-campaign dimension is not worth its risk.
  This is also why the routes are **map-agnostic**: one file, four maps, two region namespaces.
  The exceptions are the map-gated routes below.
- **One mission slot row per route index** (`derpy_route_victory_1` .. `_5`), not one shared
  key. §11.2.
- **Every objective that decides a route is engine-evaluated; its text lines are not.** Since
  2026-10-11 each route also carries `SCRIPTED` lines (its paragraph, and an explainer above
  each ritual) that only section 9 of the shipped Lua completes, so every route depends on that
  listener: never remove it. §12d. The quests in §12b carry their own `SCRIPTED` objectives,
  each with its own completing listener.
- **Multiplayer untouched.** The wrapper takes CA's own `multiplayer` argument and returns
  early only in singleplayer; the trigger returns on `cm:is_multiplayer()`. §11.3.

### 12b. The map-gated route

A route may carry a **second objective list used only where a named region exists**. Both
blocks are generated; the shipped Lua picks one when it issues, so the route means something
on every map without a per-campaign file:

```lua
-- a route is a string, or {region = ..., on_map = ..., off_map = ...}
-- region is one key, or a table of keys (one per namespace): on the map if ANY exists
local function derpy_on_map(region)
	if type(region) == "table" then
		for i = 1, #region do
			if derpy_on_map(region[i]) then return true end
		end
		return false
	end
	local found = false
	pcall(function()                                 -- see below
		local r = cm:model():world():region_manager():region_by_key(region)
		found = (r and not r:is_null_interface()) or false
	end)
	return found
end

local function derpy_pick(entry)
	if type(entry) == "string" then return entry end
	if derpy_on_map(entry.region) then return entry.on_map end
	return entry.off_map
end
```

Five things this cost, each worth keeping:

* **`region_by_key` is on `REGION_MANAGER_SCRIPT_INTERFACE`, not on `cm`.** `cm:region_by_key`
  throws *attempt to call method (a nil value)* — `luac -p` passes it, and
  `tools/check_lua_api.py` is what caught it, against CA's own `scripting_doc.html`. The same
  walk is in `derpy_chd_drill_chain.lua` and `zzz_derpy_chd_exchange.lua`.
* **The probe is wrapped in `pcall`,** because a throw inside a first-tick callback takes every
  callback queued after it — CA's `call_each` has no `pcall`. An unreachable region manager
  therefore reads as *off-map*, which is the safe way to be wrong: the `off_map` block is the
  map-agnostic one.
* **IEE reuses Immortal Empires' region namespace.** Its own `campaign_map_regions` fragment
  (`!cr_vanilla`) maps `wh3_main_combi_region_*` keys onto `cr_combi_expanded_map_1`, so one
  key covers IE and IEE together. `cr_oldworld_map_1` has none of them, which is what the gate
  is for.
* **A gate may be a tuple of keys, one per namespace** (2026-10-04), so one route reaches
  IE/IEE and the Old World together - the Black Dwarf's Praag gate is
  `("wh3_main_combi_region_praag", "cr_oldworld_region_praag")`. A tuple-gated list cannot
  name a region itself, since no one key exists on every map it is used on.
* **`check()` enforces the split**: a region key must be in `VERIFIED_REGIONS`, a map-bound
  objective type is refused in a base list, a gated list identical to the base list is refused
  as pointless, and a gated list may name no region its gate does not prove.
* **`--selftest` proves the gate by running the shipped Lua twice**, once with the region on
  the stub map and once without, and asserting the region objective is issued exactly once and
  never on the map that lacks it. Mutating `return entry.off_map` to `on_map` fails it.

The same probe gates the file's **quests** — ordinary missions with ordinary rewards, which
this generator also ships because a quest is the same four artefacts as a route minus the
`victory_type` row. There is nothing to capture on a map without the region, so a gated quest is
not issued there at all rather than picking a variant. `derpy_mis_abnagg_dawns_harbour` is the
first; `MISSIONS.md` §11b is its write-up. There are six now (`QUESTS`), and three things a
route never needs:

* **Sack-or-occupy objectives** (`_take_quest`, the Black Dwarf's Road to Praag, one quest per
  namespace). No objective type counts "sack OR occupy a named city", so each city is a
  `SCRIPTED` objective completed by listeners on `CharacterSackedSettlement` and
  `RegionFactionChangeEvent`, guarded by `mission_is_active_for_faction` and registered on
  every load. `check()` refuses a quest `SCRIPTED` objective with no such listener.
* **A `grant`**: a `MissionSucceeded` listener puts a faction-less lord in the recruit pool with
  `cm:spawn_character_to_pool` - Zochaz from Vraznak's "The Kinsman's Raid", Gordak from Dawn's
  Harbour, Warrhak from "The Silver Mountain". That call's `50` is the lord's AGE and it takes no
  rank, so a grant's `rank` waits as the saved value `derpy_grant_rank_<faction>_<subtype>` and a
  `CharacterRecruited` listener applies it with `cm:add_agent_experience(..., rank, true)`.
  `CONFED_GRANT` hands the same lord to whoever confederates the house (`FactionJoinsConfederation`,
  absorber is `context:confederation()`).
* **Culture quests**: `QUESTS["wh3_dlc23_chd_chaos_dwarfs"]` is issued to every human Chaos
  Dwarf faction, CA's three included, after the house's own.

Quests stay single-player only. The detail is in
`sessions/HANDOFF_20261004_LORE_ROUTES_AND_BALUR.md` §3 and §8 and
`sessions/HANDOFF_20261004_WARRHAK_GORDAK_QUESTS.md`.

Five routes use the gate: the Black Dwarf's I (Praag, both namespaces), Vraznak's III (the Oak
of Ages), Tordrek's III (Barak Varr), Kharkadon's III (Zharr-Naggrund, the two slave revolts)
and the first, Abnagg's III, **The Foundation Stone** (slug `siege_mastermind`): on IE and IEE it is the elf
grudge — take `wh3_main_combi_region_fortress_of_dawn` and destroy
`wh2_main_hef_fortress_of_dawn` — and elsewhere it falls back to the Dwarf war he starts next
to. The Fortress of Dawn is the target because **CA already built a Chaos Dwarf version of its
landmark harbour**: `wh3_dlc23_special_fortress_of_dawn_dawns_harbour_chd` is `chain_category`
`money` on the `wh_main_sch_port` superchain, and at level 3 pays **+500 sea-trade GDP, +5
post-battle labour and storm/reef attrition immunity factionwide** — a trade port, a slave
engine and safe water for a fleet, in one region held by elves.

The disable guard is `ROUTES[faction_key]`, not a separate list, so **a faction we have no
routes for keeps CA's conditions** — no house can end up with no victory at all.

The two naval houses carry no horde-building objective on purpose: no vanilla mission counts a
horde building (`HOUSE_MISSION_OPTIONS_20260903.md` §5, H1/K1, rated *Untested*), and a victory
condition is the worst place to discover an objective shape does not work, because it cannot be
patched out of a running save.

`derpy_chd_victory_objectives.lua` and `tools/check_victory_objectives.py` are **superseded and
deleted** — that script existed to restore the subculture long victory through CA's table, which
is moot once CA's entry point is disabled for those factions. One copy is archived at
`docs/archive/derpy_chd_victory_objectives.lua.bak_superseded_20260907`.

### 12c. Rewards under 9.0, and the victory achievement (2026-10-11)

A post-first-tick callback and one listener in the same generated file, both set up on every
load so running saves get them too. Spec: `superpowers/specs/2026-10-11-victory-routes-vco-parity-design.md`.

* **The reward switch.** A `cm:add_post_first_tick_callback` calls
  `cm:set_victory_mission_rewards_disabled(false)` in single-player when a human faction has
  routes. CA's `true` comes from the shared first-tick list (wh_start.lua,
  `start_game_all_factions`), and `process_first_tick_callbacks` runs the post list after it,
  so ours lands last. A CA faction's player is left alone and keeps CA's incident rewards.
  Wrapped in `pcall`: a throw in the post list would take every later post callback with it.
  `tools/check_lua_api.py` lists the call in `CA_USED`, since CA's docs omit it.
* **The achievement.** CA awards `WH3_ACHIEVEMENT_WINNING_CHAOS_DWARFS_1`, and `_2` above
  difficulty 3, only on `wh_main_long_victory`. A `MissionSucceeded` listener on our five route
  keys reuses CA's `award_achievement_to_faction` and `wh3_campaign_achievements.long_victory`,
  as VCO's safety unlock does, and logs instead of throwing when that script is absent.

`--selftest` runs both through the stubbed campaign and carries seven Lua mutants over the
guards the harness can reach (the reward call, the house and multiplayer guards, the route-key,
human, difficulty and missing-script guards); a mutant that survives, or whose anchor no
longer matches the code, fails the selftest. Not mutated: the `if not name` culture guard
(every stubbed house is Chaos Dwarf, so it is unreachable there) and the two `pcall`s
themselves. Both are run through (a missing switch method, and the missing-script mutant's
throw), but no mutant deletes one.

### 12d. Route text and its completer (2026-10-11)

Every route opens with a paragraph in its house's voice, and every Tower of Zharr annex or
Hell-Forge ritual objective has a one-line explainer directly above it. Both are `SCRIPTED`
objectives on `script_key derpy_route_lore`, VCO's header shape, with their text in loc only
(`mission_text_text_derpy_route_lore_<route>`, `mission_text_text_derpy_route_explain_<category>`).
Spec: `superpowers/specs/2026-10-11-victory-routes-vco-parity-phase2-design.md`.

* **The completer.** A `FactionTurnStart` listener on human factions calls
  `cm:complete_scripted_mission_objective` for all five slot keys, VCO's
  `vco_dummy_missions_check` shape. Registered on every load. No
  `mission_is_active_for_faction` guard: never measured on a victory mission.
* **The saved value.** It does nothing until `derpy_route_lore_v1` is set, which the issue
  block does when it issues routes that carry the lines. VCO shows the call is harmless where
  no mission exists; on a mission that exists without the script key it is unmeasured, and
  that is what a save from before this change holds.
* **The text** is checked by `check()`: printable ASCII, no dash, no `[[` markup, none of the
  plain-words jargon, 40 to 70 words a paragraph, 30 an explainer. `--review` writes it out for
  the author before a build.

The Uzkul Mingol Company (`cr_chd_skullstack`) gained its three routes in the same change.

### Checks

```powershell
py tools\gen_victory_routes.py --check      # validate, write nothing
py tools\gen_victory_routes.py              # write the TSVs and the Lua
py tools\gen_victory_routes.py --selftest
```

`--check` refuses to write on a finding. It rejects an objective type attested in a victory
objective by neither CA nor VCO, any map-bound type outside a gated list, any `SCRIPTED`
objective in a route, an unknown
condition keyword, a pooled resource / ritual category / building level outside the verified
lists, a `DESTROY_FACTION` target that was not probed live, a non-integer `total`, an annex
`total` larger than the house's own group can supply (a house may perform any annex ritual **but
its own**), a house with fewer than three routes or more routes than there are mission slot
rows, **a count-N objective with no `total`**, **more than two objectives of one type in one
route**, and **a condition on a type neither source pairs it with** — which in practice means
`override_text`. It also fails while any copy of the superseded script, or of the
turn-one lord grant `temp_spawn_pool_chd_oldworld.lua` the quests replaced, still ships
(`DEAD_SCRIPTS`), on a house count other than twelve, and when the Tower's plain-IE Gordak
grant in `zz_derpy_toz_annex.lua` stops building the same rank key.

Three of those rules came out of counting CA's and VCO's own files on 2026-09-08, and each one
caught something that had already shipped:

| Rule | Measured | What it caught |
|---|---|---|
| a count-N objective needs `total` | CA writes it on 4/4 `CONSTRUCT_N_OF_A_BUILDING` and 1/1 `CONSTRUCT_N_BUILDINGS_INCLUDING`; VCO on 23/23 and 4/4 | four `CONSTRUCT_N_BUILDINGS_INCLUDING` objectives across the roster had no count at all |
| at most two objectives of one type per route | the most either source writes is 2 — `PERFORM_RITUAL` and `CONTROL_N_REGIONS_FROM` | nothing yet; it is what forced Ghorth's Tower route into two districts rather than three |
| multi-target `DESTROY_FACTION` is ONE objective with a `faction` line per target | CA 93 objectives / 258 `faction` lines, VCO 181 / 528 — neither ever writes two | Ghorth's war route, which shipped as two separate `DESTROY_FACTION` objectives |
| `override_text` only on `SCRIPTED` and the region/province types | CA 88 SCRIPTED + 28 region/province and nowhere else; VCO's 113 are all `CONTROL_N_REGIONS_FROM` | the plan to retitle every objective with written prose — it is not attested on a counter objective, so it is not shipped |

`--selftest` **runs** the generated Lua under Lua 5.1.5 against a stubbed campaign and reads
back what it did: every house issued all its routes and had CA's init skipped; every gated
route issued on and off its map; the quests' listeners replayed; a faction
we do not own issued none and kept CA's; multiplayer issued none and disabled none; every
mission block brace-balanced and `;`-terminated; the three TSVs agreeing with `build()` row for
row; and every deliberate break confirmed caught.

---

## 13. Checklist for a new faction's victory conditions

Pick the route first — §8's table entry, or §11's mission strings.

**Either way**

1. Get the faction key exactly right — check it against `db/factions_tables` in the pack that
   mints it, not from memory.
2. Neither linter catches a typo'd key. Verify every faction / region / ritual / building key
   against `db/` or the pack, and probe `DESTROY_FACTION` targets in a live campaign.
3. `luac -p`, then `tools/check_lua_api.py`, then `tools/check_lua_undeclared.py`.

**CA's table (§8)**

4. Probe for the victory table; do not name a global, and do not reach it through `_G`. §4, §10.
5. Register the faction **even with an empty entry**, so the subculture long victory survives. §3.
6. Short-victory objectives go in `objectives`, long-victory ones in `long_objectives`.
7. Stage one copy per campaign key under `script/campaign/<campaign_key>/mod/`, or keep the
   objectives campaign-agnostic and ship one file in `script/campaign/mod/`.

**Mission strings (§11)**

4. Mint a `victory_types` row per route and a `missions` row per slot. Reuse CA's icon names
   unless you are shipping art.
5. Wrap `initialise_victory_missions` at file scope, guarded on the factions you actually
   cover.
6. Trigger on the first tick, guarded on `cm:is_new_game()` and `cm:is_multiplayer()`.
7. No `SCRIPTED` objective unless you are also writing the listener that completes it.
