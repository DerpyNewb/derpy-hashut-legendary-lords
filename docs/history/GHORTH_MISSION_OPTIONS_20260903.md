# Ghorth the Cruel — lore-grounded mission options

Design pass, 2026-09-03. Written against `docs/MISSIONS.md` (the mechanics) and the lord as
this workspace actually implements him, read out of `!aa_derpy_hashut_legendary_lords.pack`,
CA's `wh3_dlc23_narrative_chaos_dwarfs.lua`, and the vanilla tables in `.skilltree_cache/`.

Nothing here is built. Every option carries a buildability rating with the evidence behind it.

---

## 1. The constraint set — who Ghorth is, mechanically

| | |
|---|---|
| Character key | `derpy_ghorth` |
| Faction key | `wh3_dlc23_chd_conclave` ("The Conclave") |
| Political party | `chd_conclave` / `mixer_ime_chd_conclave` (IE-scoped) |
| Trait-line title | Master of the Conclave |
| Skill line title | Ghorth the Blackened |
| Start tile | `1735, 1204` — the Zharr-Naggrund settlement tile itself |
| Start state | 4 regions, treasury 5000, income 8841, 5 wars, holds `wh3_dlc23_chd_zhatan` as vassal |
| Origin | A **vanilla CA lord** the mod reworks in place, not a new character |

**The one simplification that matters: for Ghorth, faction-scoped is lord-scoped.**
`docs/MISSIONS.md` §1 establishes that no DB table binds a mission to a character, so every
lord objective is normally a faction mission plus a Lua presence gate. Ghorth is the exception
in this roster — he *is* the Conclave's legendary lord, so triggering for
`wh3_dlc23_chd_conclave` already means "Ghorth's player". No gate script is needed for any
option below except where the table says otherwise.

The exception to the exception: **confederation**. Absorb another Chaos Dwarf house and the
faction gains other lords, at which point any objective phrased about *a character*
(`ACHIEVE_CHARACTER_RANK`, `ELIMINATE_CHARACTER_IN_BATTLE`) can be satisfied by the wrong one.
Those need `SCRIPTED` if the intent is strictly Ghorth.

### His three identity pillars, from his own skill tree

Taken from `GHORTH_SKILL_OPTIONS_20260823.md`, so the missions match the character the mod
already built rather than a generic Chaos Dwarf:

1. **Sorcerer-Prophet of Hashut** — Master of the Dark Arts, Sorcerous Supremacy, Petrified
   Resilience. He carries Drazhoath's entire Lore of Hashut lane with every spell's overcast
   variant at level 1, and 107 distinct effects.
2. **Master of the Conclave** — Conclave Strategist, the `wh3_dlc23_chd_conclave_influence`
   pooled resource, the Tower of Zharr seats.
3. **Tyrant of Zharr-Naggrund** — raw materials and armaments efficiency, Tower public order,
   Infernal Guard and Infernal Ironsworn unit caps.

---

## 2. Before designing anything: 22 of the 33 existing mission rows are unreachable

Found while surveying what Ghorth already has. This is a live defect, not a design note.

The pack ships 11 lords x 3 missions. CA's narrative script builds two of those three keys by
**concatenating the faction key**:

```lua
-- wh3_dlc23_narrative_chaos_dwarfs.lua:498
function chaos_dwarfs_narrative:trigger_relic_unlock_mission(faction_key)
    local dwarf_battle_faction = "wh3_dlc23_chd_ancestor_relics_unlock_"..faction_key
    cm:trigger_mission(faction_key, dwarf_battle_faction, true, true)
```

and the finale is a hardcoded three-entry table, also faction-keyed:

```lua
chaos_dwarfs_narrative.finale = {
    wh3_dlc23_chd_astragoth        = { mission = "wh3_dlc23_chd_final_battle_wh3_dlc23_chd_astragoth", ... },
    wh3_dlc23_chd_legion_of_azgorh = { ... },
    wh3_dlc23_chd_zhatan           = { ... },
}
```

The mod's rows are suffixed with **character** keys (`derpy_ghorth`, `derpy_gargath`, ...), and
the mod's own Lua never calls `trigger_relic_unlock_mission` and never mentions `final_battle` —
verified across **all 70 Lua files in the pack, every one uncompressed, none skipped**.

| Row family | Count | Triggered by | Reachable |
|---|---|---|---|
| `..._ancestor_hellshard_structure_derpy_<lord>` | 11 | the mod's own `trigger_relic_missions` override, explicit faction/mission pairs | **yes** |
| `..._ancestor_relics_unlock_derpy_<lord>` | 11 | nothing — CA would ask for `..._unlock_<faction_key>` | **no** |
| `..._final_battle_derpy_<lord>` | 11 | nothing — not in `chaos_dwarfs_narrative.finale` | **no** |

**Ghorth's relic-unlock row has a second, independent fault.** Its key is missing its leading
character, confirmed at byte level in the shipped Workshop pack:

```
h3_dlc23_chd_ancestor_relics_unlock_derpy_ghorth     <- Ghorth, missing the "w"
wh3_dlc23_chd_ancestor_relics_unlock_derpy_gargath   <- every other lord
```

So even correcting the faction-vs-character naming would leave his row dead. This is exactly
the failure mode `CLAUDE.md` warns about: an unvalidated key that never errors and never fires.

**Two ways to fix, if the intent was for these to work:**

1. **Rename to faction keys** — `wh3_dlc23_chd_ancestor_relics_unlock_wh3_dlc23_chd_conclave`,
   `..._cr_chd_house_of_baal`, and so on for all eleven, then add matching entries to
   `chaos_dwarfs_narrative.finale` in the override file. Cheapest, and CA's listeners
   (`starts_with("wh3_dlc23_chd_ancestor_relics_unlock_")`) then pick them up unchanged.
2. **Hand-trigger them** the way the hellshard rows already are — explicit
   `cm:trigger_mission(faction, key)` pairs in the override. Keeps the existing key names.

Route 1 is smaller and reuses CA's chain plumbing. Neither is in scope for this document; it is
recorded so the decision is deliberate.

---

## 3. The options

Ratings, with the evidence behind each:

- **Safe** — the `mission_type` has vanilla DB rows and the exact `VAR_OBJECTIVE_*` parameters
  below are the ones vanilla uses with it (counts from `docs/MISSIONS.md` §5).
- **Untested** — the type is safe but the *value* is one of this mod's own keys, so no vanilla
  precedent exists for that combination.
- **Needs script** — no `mission_type` expresses it; `SCRIPTED` plus Lua.

### Questline A — "The Voice of the Conclave" (Master of the Conclave)

The political ladder. Ghorth rules by influence and by seats in the Tower, not by conquest.
Every objective here is faction-scoped by nature, so nothing needs a lord gate.

| # | Mission | `mission_type` | Parameters | Payload | Rating |
|---|---|---|---|---|---|
| A1 | **Seat of Sorcery** — claim the sorcery districts of the Tower | `PERFORM_RITUAL` | `RITUAL_CATEGORY = DISTRICTS_SORCERY_T1`, `AMOUNT_INT = 2` | `FACTION_POOLED_RESOURCE_TRANSACTION` conclave influence | Safe (21 rows; RITUAL_CATEGORY on 3, AMOUNT_INT on 13) |
| A2 | **The Weight of Words** — hoard the influence to out-vote the Prophets | `HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE` | `POOLED_RESOURCE = wh3_dlc23_chd_conclave_influence`, `AMOUNT_INT = 150` | `TREASURY` + `EFFECT_BUNDLE` (influence income) | Safe (5 rows, both params on 5/5) |
| A3 | **The Subjugation** — annex a rival house through the Tower's fifth tier | `PERFORM_RITUAL` | `RITUAL_CATEGORY = DISTRICTS_ANNEX_T5_A`, `AMOUNT_INT = 1` | `ADD_ANCILLARY` from that house's vault | Untested — the category is the mod's own (`derpy_chd_toz_annex`), no vanilla mission targets a modded ritual category |

This is the strongest questline for him. It is the only one that uses systems the mod itself
built, it needs no region or character keys, and A1/A2 are the two lowest-risk missions in this
whole document.

### Questline B — "The Blackening" (Sorcerer-Prophet of Hashut)

The petrification curse. A Sorcerer-Prophet's power and his slow turning to stone are the same
process, so the reward should carry the cost — that is the lore, not a balance compromise.

| # | Mission | `mission_type` | Parameters | Payload | Rating |
|---|---|---|---|---|---|
| B1 | **Ash in the Veins** — Ghorth's mastery deepens, and so does the stone | `ACHIEVE_CHARACTER_RANK` | `AMOUNT_INT = 20`, `NUM_CHARACTERS = 1` | `ADD_ANCILLARY` talisman + `EFFECT_BUNDLE` granting magic and **taking** campaign movement | Safe (11 rows, AMOUNT_INT 11/11) — but see the confederation caveat in §1 |
| B2 | **Fuel for the Forge** — feed Hashut in blood | `KILL_X_ENTITIES` | `AMOUNT_INT = 500` | `FACTION_POOLED_RESOURCE_TRANSACTION` labour | Safe (23 rows, AMOUNT_INT 23/23) |
| B2' | *variant* — kill them specifically with fire | `KILL_X_ENTITIES_BY` | `UNIT_SET = <new>`, `AMOUNT_INT`, `OVERRIDE_TEXT` | as above | Untested — needs a `unit_sets` row of its own, and `OVERRIDE_TEXT` is mandatory (25/25 vanilla rows carry it), so a loc key too |
| B3 | **Bind the K'daai** — chain a fire daemon into iron | `OWN_N_UNITS` | `UNIT = wh3_dlc23_chd_mon_kdaai_destroyer`, `AMOUNT_INT = 2` | `EFFECT_BUNDLE` (K'daai upkeep or cap) | Safe (22 rows, UNIT 22/22, AMOUNT_INT 22/22) |

B3 pairs naturally with a `PERFORM_RITUAL` prerequisite on `RITUAL_CATEGORY = HELLFORGE_CAPS_KDAAI`
if you want the Hell-Forge step made explicit.

### Questline C — "The Tribute of Slaves" (Tyrant of Zharr-Naggrund)

The industrial pillar. Chaos Dwarf power is slaves, ore and the Forge, in that order.

| # | Mission | `mission_type` | Parameters | Payload | Rating |
|---|---|---|---|---|---|
| C1 | **The Slave Raids** — take the living, not the land | `RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_OF_SUBCULTURE` | `SUBCULTURE = wh_main_grn_greenskins`, `AMOUNT_INT = 3` | labour transaction | Safe (3 rows, both params 3/3) |
| C2 | **The Hell-Forge Hungers** — arm the Legion | `HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE` | `POOLED_RESOURCE = wh3_dlc23_chd_armaments`, `AMOUNT_INT` | `EFFECT_BUNDLE` armaments efficiency | Safe |
| C3 | **The Black Fortress** — raise the Tower higher | `CONSTRUCT_N_BUILDINGS_INCLUDING` | `BUILDING_LEVEL = <a Zharr-Naggrund top-tier building>` | `TREASURY` + public order | Safe (49 rows, BUILDING_LEVEL 49/49) — note the existing hellshard mission already uses this type |

### Standalone options, higher flavour and higher risk

| Mission | `mission_type` | Why it is riskier | Rating |
|---|---|---|---|
| **The Grudge Answered** — destroy a Dwarf hold outright | `DESTROY_FACTION` | Absent from the Assembly Kit entirely, so it is **string route only** — no DB row can carry it. 24 CA call sites and 13 in mods, so it works; it just cannot be authored in the tables | Untested by DB, proven by script |
| **Rivals in Stone** — kill Astragoth or Drazhoath in person | `ELIMINATE_CHARACTER_IN_BATTLE` | Takes no `VAR_OBJECTIVE_*` at all; the target arrives through `cm:trigger_mission_with_targets(..., character_cqi, ...)`, so Lua must find the character first and the mission cannot be issued until he exists | Needs script |
| **The Seat of the Prophets** — take a rival's tier-4 seat | `PERFORM_RITUAL` on `RITUAL_CATEGORY = TOZ_TIER_4` | Ghorth's own T4 seat is **pre-claimed at start**, and the tier-4 row hardcodes three seats assuming the player is one of CA's four lords (`wh3-toz-tier4-seat-list-hardcodes-three`) | Needs script |
| **Hold the Ashen City** — never lose Zharr-Naggrund | `CAPTURE_REGIONS` / `DO_NOT_LOSE_REGION` | Region keys differ per campaign (`cr_oldworld_region_zharr_naggrund` vs the combi equivalents), so this needs one row per campaign. `DO_NOT_LOSE_REGION` additionally has no vanilla row and no user anywhere | Untested |

---

## 4. Keys this document verified, ready to paste

Read from the shipped tables, not guessed.

```
faction                 wh3_dlc23_chd_conclave
character               derpy_ghorth
start tile              1735, 1204   (= cr_oldworld_region_zharr_naggrund capital)

pooled resources        wh3_dlc23_chd_conclave_influence   (FACTION, max 999999)
                        wh3_dlc23_chd_armaments  wh3_dlc23_chd_raw_materials
                        wh3_dlc23_chd_labour     wh3_dlc23_chd_workload  wh3_dlc23_chd_efficiency

ritual categories       DISTRICTS_SORCERY_T1 / _T2 / _T3      DISTRICTS_INDUSTRY_T1..3
                        DISTRICTS_MILITARY_T1..3              TOZ_TIER_4
                        HELLFORGE_CAPS_KDAAI / _BULL_CENTAURS / _FLYING_BEASTS /
                        _MELEE_INFANTRY / _MISSILE_INFANTRY / _WARMACHINES
                        LABOUR_ACTIONS  DRILL_RAW_MATERIALS  DRILL_TREASURY
                        DISTRICTS_ANNEX_T5_A / _B / _C        <- the mod's own fifth tier

Ghorth's own T4 seat    wh3_dlc23_ritual_chd_toz_slot_t4_conclave   (pre-claimed at start)
annex rituals           derpy_ritual_chd_toz_annex_{khorakk,baal,fists,horns,black_dwarf,
                        uzkulak,black_kraken,bzaark,snakebeard,azeros}

units                   wh3_dlc23_chd_inf_infernal_guard        _fireglaives  _great_weapons
                        wh3_dlc23_chd_inf_infernal_ironsworn    _ror
                        wh3_dlc23_chd_mon_kdaai_destroyer       _fireborn
                        wh3_dlc23_chd_veh_iron_daemon           wh3_dlc23_chd_veh_magma_cannon
                        wh3_dlc23_chd_veh_deathshrieker_rocket_launcher

art (24 CHD eventpics ship; chd/generic does NOT)
                        chd/zharr_temple   chd/hell_forge   chd/zharr_boon
                        chd/politics       chd/faction      chd/celebration
issuer                  CLAN_ELDERS  (or mint a Ghorth issuer - one row + a png, proven by Mixu)
```

---

## 5. Traps that apply to all of the above

- **Every key here is unvalidated.** A typo never errors. §2 of this document is what that looks
  like after it ships.
- **`missions` is version 0**, junctions 2 / 2 / 1, loc 1. RPFM also offers `missions` v6, which
  is the wrong shape.
- **Title and description can live in the DB row** — vanilla carries English there. Writing the
  derived loc keys as well (`missions_localised_title_<key>`) is what a translation would
  override, and costs three lines.
- **Objective text is loc-only.** `mission_text_tables` does not ship. Any `OVERRIDE_TEXT` or
  `SCRIPTED` objective needs `mission_text_text_<key>` in your own `.loc` and nothing in the DB.
- **`ui_icon` is a red herring** — set it to `rom_event_mission.png` like CA's 3,049 rows and
  ignore the diagnostic that says the file is missing. It is a Rome leftover that ships nowhere.
- **One `id` per junction row, random, in `1 .. 2147483646`.** They must be unique across every
  installed mod.
- **Region-keyed objectives need one row per campaign.** `cr_oldworld`, `cr_darklands`,
  `cr_combi_expanded` and `wh3_main_combi` do not share region keys, and Ghorth is the only lord
  in this roster with a `wh3_main_combi` start script.

---

## 6. Recommendation

Build **Questline A** first, in full. Three missions, two of them the lowest-risk shapes in the
document, no region keys, no character targeting, no Lua gate — and it is the only questline
that exercises the Tower of Zharr and conclave influence, which are this mod's own systems and
therefore the thing no other Chaos Dwarf mod can offer.

A3 is the one to build second rather than third: it is the only Untested row in that questline,
and finding out whether a `mission_type` can target a **modded** ritual category settles a
question that Questline B's K'daai step and every future Hell-Forge mission also depend on.

Fix §2 before or alongside it. Adding new missions on top of 22 silently dead ones makes the
next failure much harder to attribute.

---

## 7. Two packs, and which quest belongs in which

Decided 2026-09-03: Questline C becomes a **standalone Chaos Dwarf mission mod**, not a submod.
That is a hard constraint, not a packaging preference — a standalone pack may reference
**vanilla keys only**. Nothing from `!aa_derpy_hashut_legendary_lords.pack` or
`derpy_chd_house_ancillaries.pack` can appear in it: no `derpy_*` faction, character, ritual,
ancillary or effect-bundle key, and no `DISTRICTS_ANNEX_T5_*` ritual category.

### 7.1 The standalone pack does not need 14 copies of anything

The existing pack carries 11 rows per questline because **CA's** relic and finale keys embed a
faction key (§2). Your own missions are under no such rule. `cm:trigger_mission(faction, key)`
issues any row to whatever faction you name, and vanilla proves one row serves many factions —
every `generate = true` mission does exactly that, gated by `CND_CULTURE`.

So Questline C for every Chaos Dwarf is **3 rows plus a loop**, not 42 rows:

```lua
-- picks up modded CHD factions automatically, without depending on the pack that adds them
for i = 0, cm:model():world():faction_list():num_items() - 1 do
    local f = cm:model():world():faction_list():item_at(i)
    if f:subculture() == "wh3_dlc23_sc_chd_chaos_dwarfs" and not f:is_dead() then
        cm:trigger_mission(f:name(), "derpy_chd_mis_slave_raids")
    end
end
```

Filtering on **subculture** rather than a hardcoded faction list is what keeps it standalone and
still makes it cover the eleven modded houses when the lords pack happens to be installed.
`wh3_dlc23_sc_chd_chaos_dwarfs` is the only Chaos Dwarf subculture; there is no separate
culture column value to check. Add `CND_SUBCULTURE` to the rows as a belt-and-braces guard —
a failing `CND_*` makes `cm:trigger_mission` return false rather than issuing to the wrong race.

### 7.2 Ghorth ships standalone too — the other ten lords cannot

`wh3_dlc23_chd_conclave` is a **vanilla CA faction**. Since a mission is faction-scoped and
never names a character (§1), a Ghorth quest keyed on that faction needs nothing the base game
does not already have, and works with or without the lords pack installed. The other ten lords'
factions (`cr_chd_house_of_baal`, `cr_chd_fists_of_hashut`, ...) exist only in the lords pack,
so their quests can only ship there.

| Quest | Pack | Why |
|---|---|---|
| Questline C, all three | standalone | vanilla subculture, vanilla pooled resources, vanilla buildings |
| Questline A1, A2 | standalone | `DISTRICTS_SORCERY_T1` and `wh3_dlc23_chd_conclave_influence` are both CA's |
| Questline A3 (The Subjugation) | lords pack | `DISTRICTS_ANNEX_T5_A` is the mod's own fifth tier |
| Questline B, all three | standalone | vanilla units, vanilla Hell-Forge categories |
| Every G-quest in §7.3 | standalone | all keyed on `wh3_dlc23_chd_conclave` |
| Anything paying an `ADD_ANCILLARY` from a house vault | lords/ancillary pack | those 430 items are not vanilla |

Reward payloads are where a standalone pack most easily leaks a dependency. `TREASURY`,
`FACTION_POOLED_RESOURCE_TRANSACTION` on the CHD resources, and vanilla `ADD_ANCILLARY` are all
safe; a `derpy_*` effect bundle is not.

### 7.3 Ghorth-specific quests — the ones no other lord can carry

The organising idea, and the reason his set should not look like anyone else's: **every other
Chaos Dwarf lord climbs the Tower of Zharr. Ghorth begins at its summit.** He starts holding
Zharr-Naggrund itself, his tier-4 Conclave seat is pre-claimed before turn 1, and he holds
Zhatan as a vassal. CA's own characterisation agrees — the stock `wh3_conclave_of_sorcerers`
personality is one of only three rows in the 227-row `cai_personalities` table carrying
`wh3_strategic_component_sentinel`: it garrisons Zharr-Naggrund and never marches.

So his quests are about **retention, legitimacy and procedure**, not conquest. The flavour
vocabulary is already established by his own thirty house ancillaries, which theme the Conclave
as a temple-senate: sessions, decrees, quorum, proxies, precedent, bought silence.

| # | Quest | `mission_type` | Parameters | Rating |
|---|---|---|---|---|
| G1 | **The Long Session** — the Conclave does not march. Keep Ghorth at the Tower while the campaign burns around him | `HAVE_CHARACTER_WITHIN_RANGE_OF_POSITION` | `LOGICAL_POSTION = 1735;1204`, `HEX_TRIGGER_RADIUS = 3`, `MAX_DISTANCE_TO_DECOY = 50`, `FORCE_STANCE_RECORD = MILITARY_FORCE_ACTIVE_STANCE_TYPE_CHANNELING`, `TRIGGER_IMMEDIATELY = ''`, `OVERRIDE_TEXT`, `GEN_TARGET_NONE` | Safe — 77 vanilla rows, all six params on 77/77 |
| G2 | **The Sixth Decree** — a ruling that binds the provinces, named for his Rod of the Sixth Decree | `ISSUE_PROVINCE_INITIATIVE` | `PROVINCE_INITIATIVE = <key>`, `NUM_PROVINCES`, `GEN_TARGET_NONE` | Thin — 2 vanilla rows, but both parameters attested |
| G3 | **Master of Whispers** — the Conclave rules by knowing first | `RECRUIT_AGENT` then `PERFORM_ANY_AGENT_ACTION` | `AGENT = <daemonsmith or overseer subtype>` | Safe — 54 and 2 rows |
| G4 | **The Unbroken Quorum** — still hold Zharr-Naggrund and the Conclave seat after N turns, at war with two or more houses | `SCRIPTED` | `script_key`, `override_text`; a `FactionTurnStart` counter in Lua | Needs script — no type expresses "hold for N turns"; `REACH_SPECIFIED_DATE` exists in the AK with no row and no user anywhere |
| G5 | **Ghorth's Final Reading** — pass sentence on a rival Prophet in person | `ELIMINATE_CHARACTER_IN_BATTLE` | none — target passed as a character CQI | Needs script — `cm:trigger_mission_with_targets`, and it cannot be issued until that character exists |
| G6 | **The Ledger of Owed Silence** — buy the silence of three houses, then collect | `SIGN_NON_AGGRESSION_PACT` | none | Needs script — 1 vanilla row with no options at all; the diplomacy types are built for the generated-mission director, not scripted quests (see below) |

**A trap the measurements exposed.** `MAKE_ALLIANCE`, `CONFEDERATE_FACTIONS` and
`SIGN_NON_AGGRESSION_PACT` look like easy DB missions and are not. Their vanilla rows carry
**no `VAR_OBJECTIVE_*` at all** — `MAKE_ALLIANCE` reaches its target through
`META_OPTION_SET = mis_make_alliance` plus `GEN_CND_SUBCULTURE`, which is generator machinery,
and the single `CONFEDERATE_FACTIONS` row has no option rows whatsoever. For a quest with a
**fixed** target the only route is `cm:trigger_mission_with_targets(faction_cqi, key,
target_faction_cqi, ...)`, passing `0` for every slot you are not using. Budget script for any
diplomacy objective.

**Start with G1.** It is the only quest in this document that is simultaneously Safe, unique to
Ghorth by construction (nobody else stands on `1735, 1204`), thematically exact, and free of
both region keys and character targeting. It also has a complete field-for-field vanilla
template to clone — `wh2_dlc11_cst_treasure_map_animal_treasure_me_1_level_1`:

```
VAR_OBJECTIVE_LOGICAL_POSTION        705;188        <- x;y, semicolon separated (CA's typo, keep it)
VAR_OBJECTIVE_HEX_TRIGGER_RADIUS     3
VAR_OBJECTIVE_MAX_DISTANCE_TO_DECOY  50
VAR_OBJECTIVE_FORCE_STANCE_RECORD    MILITARY_FORCE_ACTIVE_STANCE_TYPE_CHANNELING
VAR_OBJECTIVE_TRIGGER_IMMEDIATELY    (empty)
VAR_OBJECTIVE_OVERRIDE_TEXT          mission_text_text_<your key>
GEN_TARGET_NONE                      (empty)
VAR_MISSION_LENGTH_INFINITE          (empty)
VAR_CHANCE                           100
```

Note `LOGICAL_POSTION` is misspelled in CA's own schema. Write it as they do or it will be
ignored in silence.
