# MISSIONS

Missions, objectives and their payloads, end to end. Written 2026-09-03 against the installed
build, from CA's own data — `data/db.pack` (via `tools/read_pack_index.py`), the Assembly Kit's
`raw_data/db/*.xml`, `data/data_script.pack`'s Lua, `data/local_en.pack`'s loc, and
`Modding Files/reference/ca_script_docs_wh3/campaign/mission_manager.html`.

A second pass the same day added the **Workshop survey** — 404 installed mod packs, 39 of them
shipping mission content — which corrected two claims and answered one open question. See §13.

Everything marked **measured** was read out of the shipped data; everything marked **untested**
is inference a build has to confirm.

**A first build has now run** — `derpy_test_missions.pack`, 2026-09-03, as
`wh3_dlc23_chd_conclave`. Both routes issue, complete and pay out; §11 has the numbers and the
two API corrections it turned up. The rest of this document is still desk research.

---

## 1. What a mission actually is

A mission is a **faction-scoped** object. There is no such thing as a character's mission in
the data model. The reverse-reference graph is decisive: **14 tables reference `missions.key`,
and not one of them mentions a character, an agent subtype, or a lord** (measured — grepped
`is_reference: Some(("missions", "key"))` across RPFM's `schema_wh3.ron`):

```
campaign_group_ritual_chains        unlock_mission
campaign_group_rituals              unlock_mission
cdir_events_dilemma_followup_missions    followup_mission_key
cdir_events_incident_followup_missions   followup_mission_key
cdir_events_mission_followup_dilemmas    mission_key
cdir_events_mission_followup_missions    followup_mission_key, mission_key
cdir_events_mission_incidents            mission_key
cdir_events_mission_issuer_junctions     mission_key
cdir_events_mission_option_junctions     mission_key
cdir_events_mission_payloads             mission_key
mission_groups_to_missions               mission
mission_timed_payloads                   mission
mission_weights                          mission_key
prophecy_of_sotek_stages_to_missions     mission
```

So **"give this lord an objective" is always: a faction mission, plus a Lua gate that only
issues it when that lord is present.** Section 9 has the pattern. Two DB near-misses that look
like the hook and are not:

- `character_skill_level_to_missions_junctions` — exists in the Assembly Kit, **exported empty**,
  and ships no `_tables` folder in `db.pack`. Dead since WH2 (its AK export is stamped Feb 2017).
- `agent_subtypes_to_mission_groups` + `mission_groups` + `mission_groups_to_missions` — real and
  populated, but this is **Wulfhart's Huntsmen** (DLC13) specifically: the agent row carries a
  `battle_effect`, an `effect_bundle` and a locked-portrait `image_path`. It is a bespoke
  companion-recruitment mechanic that happens to hang missions off it, not a general
  lord-to-mission binding.

`missions.quest_character` is a **startpos character id** (`400068026` is Zhatan). A lord added
by DB + script has no startpos id, so this column stays empty for modded lords — **except that
`!aa_derpy_hashut_legendary_lords.pack` copies CA's Drazhoath id `1536972186` onto all eleven of
its final-battle rows** (§13.1). Whether that is load-bearing or harmless is untested.

---

## 2. Three routes to a mission, one of which is dead in WH3

| Route | How | Status |
|---|---|---|
| **DB rows** | `missions` + `cdir_events_mission_option_junctions` (+ payloads, issuer), fired with `cm:trigger_mission()` | **The route to use.** Everything CA ships uses it. |
| **Lua mission string** | `mission_manager:add_new_objective()` builds a string, `cm:trigger_custom_mission_from_string()` fires it | Works, and is how `SCRIPTED` objectives are built. Still needs a `missions` row. |
| **`missions.txt`** | mission strings baked into `data/campaigns/<name>/missions.txt` | **Dead in WH3.** Measured: the three campaign folders (`wh3_main_chaos`, `wh3_main_combi`, `wh3_main_prologue`) contain `startpos.esf` and nothing else. `cm:trigger_custom_mission()` has no file to read. CA's `mission_manager.html` still documents this route and calls it "the default option" — that text is stale. |

**A `missions` row is required in all three cases.** `mission_manager:new()` takes a mission key
and CA's own doc says "must match a record in the missions table, which must be present in all
cases". The string route overrides the *objectives*, not the record.

---

## 3. The tables

Versions are what `db.pack` actually ships (measured off the decoded vanilla file), not RPFM's
default for a new table. Per `wh3-table-version-must-match-field-shape`, write these. Row counts
are 9.0's (`tools/read_vanilla_db.py`, 2026-10-09); 9.0 changed no version here.

| Table | Version | Rows in vanilla | Role |
|---|---|---|---|
| `missions` | **0** | 3,350 | The record: key, `mission_type`, text, art, generation flags |
| `cdir_events_mission_option_junctions` | **2** | 9,080 | Objective parameters *and* generation conditions |
| `cdir_events_mission_payloads` | **2** | 3,710 | Rewards, and failure/cancel payloads |
| `cdir_events_mission_issuer_junctions` | **1** | 2,589 | Who is asking (portrait + flavour) |
| `mission_weights` | — | — | Weight for the random-generation pool only |
| `mission_timed_payloads` | — | — | Payload paid out on a timer while the mission runs |
| `cdir_events_mission_followup_missions` | — | — | Chain: succeed A, issue B |
| `cdir_events_mission_followup_dilemmas` / `_incidents` | — | — | Chain into a dilemma or incident |

Note RPFM offers **two** definitions for `missions` — v6 (17 fields) and v0 (19 fields). v0 is
the shipped one; v6 lacks `localised_mission_completed_text` and `can_be_manually_cancelled`.

Tables that exist in the Assembly Kit but ship **no `_tables` folder** in `db.pack`, so they are
not moddable through DB at all:

- `mission_text` — see §6, the objective text is loc-only.
- `mission_types` — the objective-type vocabulary is engine-side (§4).
- `cdir_events_mission_statuses` — the three values are engine-side (`SUCCESS`, `FAILURE`, `CANCELLED`).
- `mission_completion_conditions` — AK export is empty.

### `missions` (v0) columns that matter

| Column | Note |
|---|---|
| `key` | Primary key. Unvalidated string everywhere it is referenced. |
| `mission_type` | **The objective.** One of the 89 in §4. |
| `localised_title` / `localised_description` / `localised_mission_completed_text` | Localised fields — §6. |
| `ui_image` | `<culture>/<name>`, resolved as `ui/eventpics/<value>.png`. §7. |
| `ui_icon` | Schema default `rom_event_mission.png`, which **ships nowhere**. §7. |
| `generate` | `false` = script-triggered only. Every quest mission CA ships is `false`. |
| `prioritised` | Bypasses turn/chance restrictions. Inert when `generate` is false. |
| `event_category` | → `cdir_events_categories`. `Quest` for quests, `Military` for generated. |
| `quest_mission` | Marks it as a quest for UI grouping. |
| `quest_mission_final` | Completing it satisfies a "complete a quest chain" objective elsewhere. |
| `sticky_by_default` | Pinned in the objectives list. CA sets `true` on quests. |
| `can_be_manually_cancelled` | CA sets `false` on quests so the player cannot bin them. |
| `quest_character` | startpos character id. Leave empty for modded lords (§1). |
| `set_piece_battle` | → `battle_set_pieces`. Required by `FIGHT_SET_PIECE_BATTLE`. |
| `location_x` / `location_y` | **Display coordinates, not logical** (CA's own field comment). |

---

## 4. The objective vocabulary — `mission_type`

89 keys exist in the Assembly Kit's `mission_types.xml`. **That list is not the whole
vocabulary** — 7 more types are used in CA's own Lua and in shipped mods and appear nowhere in
the AK (see the third list below). The AK export is stamped Nov 2023 (revision 59) and lags the
current patch.

Coverage measured three ways: **48** of the 89 have vanilla DB rows, **30** are used through
`add_new_objective` in CA's 833 campaign Lua files, and **21** in the 404 installed Workshop
packs. **Prefer a type with rows or a shipped user behind it.**

Used by WH3 DB rows (safest):

```
ACHIEVE_CHARACTER_RANK        AMBUSH_ARMY                   ASSASSINATE_CHARACTER
CAPTURE_REGIONS               CAPTURE_X_BATTLE_CAPTIVES     CONFEDERATE_FACTIONS
CONSTRUCT_N_BUILDINGS_INCLUDING  CONSTRUCT_N_OF_A_BUILDING  DECLARE_WAR
DEFEAT_N_ARMIES_OF_FACTION    DEFEAT_ROGUE_ARMY             EARN_X_AMOUNT_FROM_RAIDING
ELIMINATE_CHARACTER_IN_BATTLE EMBED_AGENT                   ENGAGE_FORCE
ENSURE_FACTIONS_HAVE_NO_MILITARY_PRESENCE                   FIGHT_SET_PIECE_BATTLE
HAVE_AT_LEAST_X_MONEY         HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE
HAVE_CHARACTER_WITHIN_RANGE_OF_POSITION                     HAVE_RESOURCES
HINDER_SETTLEMENT             INCOME_AT_LEAST_X             ISSUE_PROVINCE_INITIATIVE
KILL_X_ENTITIES               KILL_X_ENTITIES_BY            MAKE_ALLIANCE
MAKE_TRADE_AGREEMENT          MOVE_TO_PROVINCE              MOVE_TO_REGION
MOVE_X_AGENTS_TO_Y_REGIONS_OWNED_BY_Z                       OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS
OWN_N_PROVINCES               OWN_N_UNITS                   PERFORM_ANY_AGENT_ACTION
PERFORM_RITUAL                RAID_REGION                   RAID_SUB_CULTURE
RAISE_FORCE                   RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING
RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_OF_SUBCULTURE          RECRUIT_AGENT
RECRUIT_N_UNITS_FROM          RECRUIT_UNIT                  RESEARCH_TECHNOLOGY
SCRIPTED                      SEARCH_RUINS                  SIGN_NON_AGGRESSION_PACT
```

**Not in the Assembly Kit at all, yet used through the string route** — the AK list is incomplete:

```
DESTROY_FACTION                  CA=11  mods=13   (by far the most used of these)
CONTROL_N_REGIONS_INCLUDING      CA=4   mods=15
OWN_N_REGIONS_INCLUDING          CA=0   mods=3
CONSTRUCT_N_BUILDINGS_FROM       CA=1   mods=0    (the example in CA's own mission_manager doc)
CONSTRUCT_N_OF_A_BUILDING_CHAIN  CA=1   mods=0
CONTROL_N_PROVINCES_INCLUDING    CA=1   mods=0
AT_LEAST_X_PUBLIC_ORDER_IN_PROVINCES  CA=1  mods=0
```

In the AK with **no DB row but a working string-route user** — fine to use:

```
KILL_CHARACTER_BY_ANY_MEANS  CA=3 mods=1     HAVE_N_AGENTS_OF_TYPE  CA=0 mods=3
END_REBELLION                CA=1 mods=0     RAZE_OR_OWN_SETTLEMENTS  CA=1 mods=0
RESEARCH_N_TECHS_INCLUDING   CA=1 mods=0
```

In the AK with **no DB row and no user anywhere** — 36 keys, genuinely untested:

```
ALL_PLAYERS_RAZE_SACK_OR_OWN_X_SETTLEMENTS  AQUIRE_MISSION_CATEGORY_WEIGHT
ARMY_CONTAINS_N_UNITS_OF_TYPE   ASSASSINATE_X_CHARACTERS   ASSIGN_CHARACTER_TO_OFFICE
BLOCKADE_PORT                   BLOCKADE_X_SETTLEMENTS     BRIBE_FORCE
COMPLETE_RITUAL_CHAIN           CONVERT_REGION             DEMAND_TRIBUTE
DEMORALISE_FORCE                DEPLOY_AGENT_TYPE_IN_PROVINCE
DEPLOY_N_AGENTS_TO_REGIONS      DEPLOY_X_AGENTS_TO_Y_REGIONS_OWNED_BY_Z
DO_NOT_ALLY_WITH_X              DO_NOT_LOSE_REGION         DO_NOT_LOSE_SET_PIECE_BATTLE
END_REBELLION                   GIVE_TRIBUTE               HAVE_AT_LEAST_X_INFLUENCE
HAVE_N_AGENTS_OF_TYPE           HAVE_N_UNITS_IN_ARMY       KILL_CHARACTER_BY_ANY_MEANS
LIBERATE_N_REGIONS_TO_FACTION   LIBERATE_REGION            LIFT_BLOCKADE
LIMIT_FACTION_TO_REGIONS        MAKE_PEACE
MEET_ALL_OTHER_OBJECTIVES_WITHIN_X_TURNS                   OWN_N_PORTS_INCLUDING
RAID_X_REGIONS                  RAZE_OR_OWN_SETTLEMENTS    RAZE_OR_OWN_X_SETTLEMENTS
REACH_SPECIFIED_DATE            RESEARCH_N_TECHS_INCLUDING SABOTAGE_BUILDING
SABOTAGE_FORCE                  TRADE_INCOME_AT_LEAST_X    TRIGGER_WAAAGH
__DEPRECATED__AT_LEAST_X_RELIGION_IN_PROVINCES
```

The five that were in the old "unused" list and have since been shown working —
`KILL_CHARACTER_BY_ANY_MEANS`, `END_REBELLION`, `RESEARCH_N_TECHS_INCLUDING`,
`RAZE_OR_OWN_SETTLEMENTS`, `HAVE_N_AGENTS_OF_TYPE` — are the reason "no DB row" is not the same
as "does not work". Check the string route before writing a type off.

`COMPLETE_RITUAL_CHAIN` is worth a probe given the ritual work already in this workspace — but
it has zero rows and zero users anywhere, so budget for it not working.

---

## 5. Parameterising the objective — `cdir_events_mission_option_junctions`

One row per parameter: `(id, mission_key, option_key, value, target)`. `id` is an `I64` and must
be unique; CA uses large random-looking numbers. `target` is almost always `default`
(measured: 8,554 of 8,590 rows).

`option_key` comes from `cdir_events_options` (426 keys) in four families:

- **`VAR_OBJECTIVE_*`** (55 keys) — parameters of the objective itself. This is the half you
  always need.
- **`CND_*`** (158) — conditions on the *receiving faction* that gate whether the mission can
  fire at all. `cm:trigger_mission` returns false if they fail.
- **`GEN_CND_*` / `GEN_TARGET_*`** (210) — conditions on and selection of the mission's *target*
  (a faction, region, character…). `GEN_TARGET_NONE` when the objective needs no target.
- **`VAR_*`** other (turn limits and roll chance):
  `VAR_CHANCE`, `VAR_MISSION_LENGTH_MIN`/`_MAX`/`_INFINITE`/`_ADDITIONAL_MIN`/`_ADDITIONAL_MAX`,
  `VAR_MISSION_LENGTH_MOD_EASY`/`_NORMAL`/`_HARD`/`_VERY_HARD`, `VAR_DELAY_MIN`/`_MAX`,
  `VAR_FOLLOWUP_CHANCE`, `META_OPTION_SET`.

`META_OPTION_SET` pulls a shared block of conditions in from `cdir_events_option_sets` +
`cdir_event_option_set_items` — that is how CA reuses one generated-mission definition across
every culture.

### Which `VAR_OBJECTIVE_*` each type takes

Measured — for every vanilla mission of that type, which `VAR_OBJECTIVE_*` rows it carries, as
`KEY(missions carrying it / missions of that type)`. Where a count exceeds the total, some
missions carry the key twice.

```
ENGAGE_FORCE                          n=312  REQUIRES_VICTORY(5) ARMIES_ONLY(5)
CAPTURE_REGIONS                       n=187  AMOUNT_INT(3)
SCRIPTED                              n=177  (see §8 - configured from Lua, not here)
RAZE_OR_SACK_N_..._INCLUDING          n=153  NUM_REGIONS(13)
HAVE_CHARACTER_WITHIN_RANGE_OF_POSITION n=77 HEX_TRIGGER_RADIUS OVERRIDE_TEXT FORCE_STANCE_RECORD
                                             MAX_DISTANCE_TO_DECOY LOGICAL_POSTION TRIGGER_IMMEDIATELY  (all 77/77)
RECRUIT_UNIT                          n=64   UNIT_CASTE(34) UNIT_CATEGORY(20) UNIT_CLASS(6) UNIT(4)
RECRUIT_AGENT                         n=53   AGENT(2)
CONSTRUCT_N_BUILDINGS_INCLUDING       n=49   BUILDING_LEVEL(49/49) OVERRIDE_TEXT(3) AMOUNT_INT(1)
DEFEAT_N_ARMIES_OF_FACTION            n=44   NUM_ARMIES(44/44) SUBCULTURE(22) REQUIRES_VICTORY(14)
MOVE_TO_REGION                        n=36   AMOUNT_INT(1)
KILL_X_ENTITIES_BY                    n=25   UNIT_SET(26) OVERRIDE_TEXT(25/25) AMOUNT_INT(25/25)
KILL_X_ENTITIES                       n=23   AMOUNT_INT(23/23) ADDITIVE(1) SUBCULTURE(1)
OWN_N_UNITS                           n=22   UNIT(22/22) AMOUNT_INT(22/22) ADDITIVE(3)
PERFORM_RITUAL                        n=21   RITUAL(18) AMOUNT_INT(13) RITUAL_CATEGORY(3) OVERRIDE_TEXT(3)
CAPTURE_X_BATTLE_CAPTIVES             n=14   AMOUNT_INT(14/14) ADDITIVE(13)
OCCUPY_LOOT_RAZE_OR_SACK_X_SETTLEMENTS n=12  AMOUNT_INT(12/12)
RECRUIT_N_UNITS_FROM                  n=12   NUM_UNITS(12/12) OVERRIDE_TEXT(10) UNIT_SET(8) EXCLUDE_EXISTING(7) UNIT(4)
ACHIEVE_CHARACTER_RANK                n=11   AMOUNT_INT(11/11) NUM_CHARACTERS(3) AGENT(1)
HAVE_AT_LEAST_X_MONEY                 n=9    AMOUNT_INT(9/9)
OWN_N_PROVINCES                       n=7    NUM_PROVINCES(7/7) PROVINCE(1)
HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE  n=5    AMOUNT_INT(5/5) POOLED_RESOURCE(5/5) ADDITIVE(2)
CONSTRUCT_N_OF_A_BUILDING             n=5    AMOUNT_INT(5/5) BUILDING_LEVEL(5/5)
EARN_X_AMOUNT_FROM_RAIDING            n=4    AMOUNT_INT(4/4) ADDITIVE(2)
HINDER_SETTLEMENT                     n=4    SUBCULTURE(2)
HAVE_RESOURCES                        n=3    RESOURCE_TYPE(6) AMOUNT_INT(1)
RAZE_OR_SACK_N_..._OF_SUBCULTURE      n=3    SUBCULTURE(3/3) AMOUNT_INT(3/3)
INCOME_AT_LEAST_X                     n=3    AMOUNT_INT(3/3)
RESEARCH_TECHNOLOGY                   n=3    TECHNOLOGY(3/3)
MOVE_TO_PROVINCE                      n=2    PROVINCE(2/2)
AMBUSH_ARMY                           n=1    NUM_ARMIES
MOVE_X_AGENTS_TO_Y_REGIONS_OWNED_BY_Z n=1    NUM_REGIONS SUBCULTURE NUM_AGENTS
ISSUE_PROVINCE_INITIATIVE             n=1    PROVINCE_INITIATIVE NUM_PROVINCES
EMBED_AGENT                           n=1    AGENT
RAID_SUB_CULTURE                      n=1    SUBCULTURE
SEARCH_RUINS                          n=1    AMOUNT_INT
DEFEAT_ROGUE_ARMY                     n=1    REQUIRES_VICTORY
```

Nine types carry **no** `VAR_OBJECTIVE_*` rows at all — they take their target from
`GEN_TARGET_*` / `cm:trigger_mission_with_targets` instead:
`ASSASSINATE_CHARACTER`, `DECLARE_WAR`, `ELIMINATE_CHARACTER_IN_BATTLE`,
`ENSURE_FACTIONS_HAVE_NO_MILITARY_PRESENCE`, `FIGHT_SET_PIECE_BATTLE`, `MAKE_ALLIANCE`,
`MAKE_TRADE_AGREEMENT`, `RAID_REGION`, `RAISE_FORCE`.

Full `VAR_OBJECTIVE_*` list: `ADDITIVE`, `AGENT`, `AGENT_SUBTYPE`, `AMOUNT_FLOAT`, `AMOUNT_INT`,
`ARMIES_ONLY`, `BUILDING_CHAIN`, `BUILDING_LEVEL`, `CHARACTER_ID`, `ENEMY_OF_FACTION`,
`ENEMY_OF_TARGET_FACTION`, `EXCLUDE_EXISTING`, `FORCE_STANCE_RECORD`, `HEX_TRIGGER_RADIUS`,
`INVADING_ONLY`, `IS_CO_OP_COMPLETEABLE`, `LOGICAL_POSTION` (sic), `MAX_DISTANCE_TO_DECOY`,
`NUM_AGENTS`, `NUM_ARMIES`, `NUM_CHARACTERS`, `NUM_PROVINCES`, `NUM_REGIONS`, `NUM_TURNS`,
`NUM_UNITS`, `OVERRIDE_TEXT`, `POOLED_RESOURCE`, `PROCESS_LISTED_REGIONS_ONLY`, `PROVINCE`,
`PROVINCE_INITIATIVE`, `RELIGION_PCT`, `REQUIRES_VICTORY`, `RESOURCE_TYPE`, `RITUAL`,
`RITUAL_CATEGORY`, `RITUAL_CHAIN`, `SUBCULTURE`, `TECHNOLOGY`, `TRIGGER_IMMEDIATELY`, `UNIT`,
`UNIT_CASTE`, `UNIT_CATEGORY`, `UNIT_CLASS`, `UNIT_SET`.

Multiple values in one row are **semicolon-separated**, no spaces — measured on Gorduz:

```
VAR_OBJECTIVE_UNIT  wh3_dlc23_chd_cav_hobgoblin_wolf_raiders_bows;wh3_dlc23_chd_cav_hobgoblin_wolf_raiders_ror;...
VAR_OBJECTIVE_AMOUNT_INT  8
```

---

## 6. Payloads — `cdir_events_mission_payloads`

`(id, mission_key, payload_key, status_key, value, target_key)`.

`status_key` is a three-value engine vocabulary: `SUCCESS`, `FAILURE`, `CANCELLED`. Vanilla is
overwhelmingly success-only — measured **3,512 SUCCESS / 2 FAILURE / 3 CANCELLED**. Failure
payloads work but have almost no precedent.

`value` is `KEY[value];KEY2[value2]`, with bare flags carrying no bracket. Measured shapes, one
real example each:

| `payload_key` | Used on missions | Example `value` |
|---|---:|---|
| `TREASURY` | 964 | `AMOUNT[1000]` |
| `EFFECT_BUNDLE` | 815 | `KEY[wh3_dlc25_dwf_dilemma_book_of_grudges_penalty];DURATION[5];GLOBAL` |
| `ADD_ANCILLARY` | 748 | `ANCILLARY_KEY[wh_dlc06_anc_weapon_skarsniks_prodder];SHOULD_REPLACE` |
| `FACTION_POOLED_RESOURCE_TRANSACTION` | 569 | `RESOURCE[x];FACTOR[y];AMOUNT[250];CONTEXT[absolute]` |
| `TEXT_DISPLAY` | 293 | `LOOKUP[dummy_spawn_gorduz_backstabber]` |
| `DIPLOMATIC_STANDING` | 85 | `AMOUNT[6]` |
| `GIVE_TRAIT` | 19 | `TRAIT_LEVEL_KEY[wh3_dlc20_trait_champion_of_zanbaijin_valkia]` |
| `INFLUENCE` | 14 | `AMOUNT[30]` |
| `ADD_MERCENARY_TO_FACTION_POOL` | 5 | `AMOUNT[3];UNIT[wh2_twa03_def_mon_wolves_0]` |
| `SPAWN_AGENT` | 2 | `AGENT[engineer];AP_FACTOR[1.0]` |
| `CHARACTER_EXPERIENCE` | 2 | `AMOUNT[1500]` |
| `FACTION_PROVINCE_POOLED_RESOURCE_TRANSACTION` | 1 | `RESOURCE[skaven_food];FACTOR[skaven_food_missions];AMOUNT[20];CONTEXT[absolute]` |

`cdir_events_payloads` holds **33** payload keys total. The 21 with no mission precedent —
`DAMAGE_BUILDING`, `DAMAGE_CHARACTER`, `DAMAGE_WALLS`, `DEMOLISH_BUILDING_CHAIN`,
`FORM_CONFEDERATION`, `GIVE_DEVELOPMENT_POINT`, `GIVE_REGION`, `KILL_CHARACTER`, `LOYALTY`,
`MILITARY_FORCE_POOLED_RESOURCE_TRANSACTION`, `PROVINCE_SLAVES_CHANGE`, `REBELLION`,
`REGION_POOLED_RESOURCE_TRANSACTION`, `REMOVE_TRAIT`, `SPAWN_STORM`, `SPAWN_UNIT`,
`WOUND_CHARACTER`, `ADD_MERCENARY_TO_PROVINCE_POOL`, `CAMPAIGN_PAYLOAD_RECORD`,
`FACTION_SLAVES_CHANGE`, `FAVOUR_POINTS` — are shared with dilemmas and incidents and are
presumably fine, but their `value` shape is not documented and would have to be lifted from a
dilemma or incident row.

Two traps that carry over from the rituals work:

- `FACTION_POOLED_RESOURCE_TRANSACTION` needs a real `FACTOR[...]` — see
  `wh3-pooled-resource-payload-factor-trap`.
- `TEXT_DISPLAY` needs a legal `state` on the receiving side — see
  `wh3-text-display-is-mission-panel-only`.

`mission_timed_payloads` pays out on a schedule *while the mission is live*, rather than on
completion. Not investigated further.

---

## 7. Text and art

### Loc keys

`missions` has three localised fields, so three derived keys per mission, in the standard
`<table>_<field>_<key>` shape. **Measured** — all three found in `text/db/missions__.loc` inside
`local_en.pack`:

```
missions_localised_title_<key>
missions_localised_description_<key>
missions_localised_mission_completed_text_<key>
```

CA writes the English into the DB row **and** ships the loc key. For a mod, write the loc — that
is what the runtime reads and it is what a translation would override. `{{tr:some_other_key}}`
in the DB row works as an indirection (CA uses it to share generated-mission text through
`ui_text_replacements`).

`missions_localised_mission_completed_text_*` exists with an **empty value** on CA's own rows.
An empty loc value is not the same as no key — mind `wh3-placeholder-loc-key-silent-empty-tooltip`.

### Objective text — loc-only, no table

Scripted objectives use `mission_text_text_<key>`. **`mission_text_tables` does not ship in
`db.pack`** — only `text/db/mission_text__.loc` exists. Measured:

```
mission_text_text_scripted_rebuild_karaz_ankor
  = "Ensure Dwarf factions control the following province(s):"
```

So the objective line is a **pure loc entry**: put `mission_text_text_<yourkey>` in your own
`.loc` and pass that full key to `add_new_objective`'s override or to
`cm:set_scripted_mission_text`. There is no DB row to add and nothing to junction.

### Art

`ui_image` is `<culture>/<name>` and resolves to `ui/eventpics/<value>.png`, with an optional
animated twin at `movies/eventpics/<value>.ca_vp8`.

**Trap, measured:** `ui/eventpics/chd/generic.png` **does not exist**, yet 39 vanilla missions
(and 56 for `cth/generic`) point at it. The panel evidently falls back rather than drawing
nothing, but do not copy the value — the 24 CHD eventpics that *do* ship are:

```
army_morale_down  army_morale_up  besieged  blockaded  celebration
civilisation_down civilisation_up convoy_bad convoy_commerce convoy_good
defeat  diplomacy  economy_down  faction  funeral  hell_forge
land_defeat  land_victory  messenger  politics  settlement_lost
victory  zharr_boon  zharr_temple
```

`zharr_temple`, `hell_forge` and `zharr_boon` are the obvious picks for a Chaos Dwarf lord quest.

`ui_icon` is a red herring. Its schema default `rom_event_mission.png` is carried by **3,049 of
3,186** vanilla rows and **ships in no pack** — a Rome leftover. The real message icons are
`ui/campaign ui/message_icons/event_mission_{positive,neutral,negative}.png` and are selected
elsewhere. Copy CA: set it to `rom_event_mission.png` and ignore it.

### Issuer

`cdir_events_mission_issuer_junctions` binds one issuer to the mission. 19 issuers exist; the
default is `CLAN_ELDERS` (which, despite the name, uses `grey_seer_vulscreek.png`). Each has an
`icon_path` under `ui/campaign ui/mission_issuers/`. `_DEFAULT_` has an empty icon path.

**Confirmed working in a shipped mod.** `ab_mixu_legendary_lords.pack` adds three rows to
`mission_issuers` (table version **3**, same as vanilla's), each with its own icon:

```
CRUSADERS_ORIGO              0  ui/campaign ui/mission_issuers/mission_issuer_knights_of_origo.png
mixu_advisor_von_helboring   0  ui/campaign ui/mission_issuers/mixu_advisor_von_helboring.png
mixu_advisor_kragg           0  ui/campaign ui/mission_issuers/mixu_dwf_kragg_the_grim.png
```

So a Chaos Dwarf issuer face is a solved problem: one row plus the `.png` at that path.
`default_rounds_between` is 0 on every vanilla and modded row.

---

## 8. The Lua side

### Firing a DB mission — the whole thing

CA's `wh3_campaign_grudges_starting_missions.lua`, in full, is the minimal pattern:

```lua
function starting_grudge_missions:initialise()
    if cm:is_new_game() then
        local campaign = cm:get_campaign_name()
        local playable_dwarf_factions = cm:get_human_factions_of_culture(self.dwarf_culture)
        local mission_list = self.faction_missions[campaign]
        for _, faction in ipairs(playable_dwarf_factions) do
            for j = 1, #mission_list[faction] do
                cm:trigger_mission(faction, mission_list[faction][j])
            end
        end
    end
end
```

`cm:trigger_mission(faction_key, mission_key, [fire_immediately], [should_whitelist])`. CA's doc
documents three parameters; `lib_campaign_mission_manager.lua` calls it with **four**
(`should_whitelist` is undocumented). The two-argument form above is what CA's own campaign
scripts use. It returns whether the mission triggered — **but not through the command queue**,
where it always returns true.

Other entry points (`campaign/episodic_scripting.html`):

| Call | Note |
|---|---|
| `cm:trigger_mission_with_targets(faction_cqi, key, target_faction_cqi, secondary_faction_cqi, character_cqi, military_force_cqi, region_cqi, settlement_cqi)` | Pass `0` to omit a target. The route for `ASSASSINATE_CHARACTER`, `DECLARE_WAR` etc. |
| `cm:mission_is_active_for_faction(faction, mission_key)` | Query. |
| `cm:cancel_custom_mission` / `cm:fail_custom_mission` | Take a mission key from the `missions` table despite the "custom" name. |
| `cm:toggle_mission_generation(bool)` | Global kill switch for the director. |
| `cm:clear_pending_missions(faction)` | |

Events raised: `MissionSucceeded`, `MissionFailed`, `MissionCancelled`,
`MissionGenerationFailed` — each carries `context:mission()` and `context:faction()`, and the
mission's key is `context:mission():mission_record_key()` (measured in `start_listeners()`).

### `mission_manager` — when you need callbacks

`mission_manager:new(faction_name, mission_key, [success_cb], [failure_cb], [cancel_cb], [expiry_cb])`.
Setting **any** callback, any scripted objective, any persistent value, or an each-time trigger
callback makes the manager **persistent** — which means it saves script state and **must be
declared at script root, before the first tick**, or it will not re-establish on load.

**Two traps that pairing has already cost a CTD** (2026-09-03, `derpy_test_missions.pack`):

- "**Any scripted objective**" means `mission_manager:add_new_scripted_objective` — a Lua event
  plus condition. It does **not** mean `add_new_objective("SCRIPTED")`, which merely passes the
  DB objective *type* `SCRIPTED` down the string route. A manager that only does the latter is
  **not** persistent and needs nothing at script root.
- **Script root cannot ask who the player is.** CA's `campaign_manager.html` says of the whole
  Local Player Faction section: *"Each function here can only be called on or after the first
  model tick."* `cm:get_local_faction_name(true)` at file scope is a **native null-deref**
  (`0xc0000005` reading `0x0`), not a Lua error, so `pcall` around it catches nothing and the
  campaign load hard-crashes. The script log's tell is the file's `Loading mod file [...]` line
  with no matching `loaded successfully`. If a manager genuinely must be persistent, declare it
  at script root against a **hardcoded** faction key, and take the faction from
  `cm:add_first_tick_callback` for everything else.

For a pure DB mission with a reward callback:

```lua
local mm = mission_manager:new(faction_key, "derpy_mis_x", function() --[[ on success ]] end)
mm:set_is_mission_in_db()
mm:trigger()
```

9.0 changes worth knowing (`sessions/HANDOFF_20260925_UPDATE_9_0_NEW_CAPABILITY.md` §2, untested
here): `mission_manager:new` no longer refuses a non-human faction (the check at
`lib_campaign_mission_manager.lua:136` is commented out), the new `MissionUpdated` event reports
primary objectives completed of total, and `cm:set_active_mission_status_for_faction` is new.

### `SCRIPTED` objectives — arbitrary completion logic

This is the escape hatch when no `mission_type` fits. CA's `legendary_grudges` idiom, measured:

```lua
mm:add_new_objective("SCRIPTED")
mm:add_condition("override_text mission_text_text_your_loc_key")
mm:add_condition("script_key " .. unique_script_key)
mm:add_payload("money 1000")
mm:trigger()

-- populate the entity checklist shown on the panel
cm:set_scripted_mission_entity_completion_states(mission_key, script_key, {{region_interface, false}})
-- ...and later
cm:complete_scripted_mission_objective(faction_name, mission_key, script_key, true)
```

Note `add_new_objective` switches the manager to the **string** route, so a `SCRIPTED` objective
cannot be combined with DB-sourced objectives on the same mission.

The `add_condition` string vocabulary is lowercase short names, unrelated to the DB's
`VAR_OBJECTIVE_*`. Harvested from every `add_condition("...")` in CA's 833 campaign Lua files,
by frequency:

```
override_text(43) script_key(41) faction(36) total(28) region(17) requires_victory(14)
cqi(13) set_piece_battle(9) confederation_valid(6) ritual_category(4) province(3)
position(3) family_member(3) unit(2) technology(2) subculture(2) pooled_resource(2)
exclude_existing(2) building_level(2) building_chain(2) armies_only(2) ritual(1)
province_initiative(1) income(1) include_generals(1) ignore_allies(1) additive(1)
```

Payload strings for `add_payload` are a different, lowercase format again:
`money 1000`, `influence 5`, `effect_bundle{bundle_key X;turns 0;}`,
`faction_pooled_resource_transaction{resource X;factor Y;amount 10;context absolute;}`.

The constructed string is `mission{key K;issuer I;turn_limit N;primary_objectives_and_payload{objective{type T;cond;}payload{...}failure_payload{...}}}`
and is handed to `cm:trigger_custom_mission_from_string`.

Other scripted-objective calls:

- `cm:set_scripted_mission_text(mission_key, script_key, loc_key)` — live progress text.
- `cm:set_scripted_mission_position(mission_key, script_key, x, y)` — zoom-to target.
- `cm:remove_scripted_mission_entities(mission_key, script_key, entities)`.
- `mission_manager:update_scripted_objective_text(loc_key, count, total)` — formats two numbers
  into the loc string (`"Progress: %n of %n"`).

---

## 9. Attaching objectives to a lord

There is no DB hook (§1). The pattern is: **one faction mission per lord objective, issued by a
Lua gate that checks the lord is actually there.**

```lua
-- untested sketch, but every call in it is documented and in use by CA
core:add_listener(
    "derpy_lord_quest_gate",
    "FactionTurnStart",
    function(context) return context:faction():name() == FACTION_KEY end,
    function(context)
        local faction = context:faction()
        for _, char in model_pairs(faction:character_list()) do
            if char:character_subtype("derpy_chd_lord_x") and not char:is_null_interface() then
                cm:trigger_mission(FACTION_KEY, "derpy_mis_lord_x_01")
                core:remove_listener("derpy_lord_quest_gate")
                return
            end
        end
    end,
    true
)
```

Points that the memory file already paid for and that apply here:

- `cm:get_faction` returns **false**, not nil, and `call_each` has no pcall
  (`wh3-lua-nil-vs-false-and-call-each`) — guard the accessor.
- A null script interface carries only `is_null_interface()`
  (`wh3-null-script-interface-has-only-is-null-interface`).
- An erroring listener condition drops silently (`wh3-listener-condition-fails-silently`) — log
  every handler exit.
- `is_unique` lives on `character_details`, not the character (`wh3-is-unique-is-on-character-details`).
- Every key here is unvalidated. A typo in `FACTION_KEY` or the mission key does nothing forever.

For a **chain** of objectives, either use `cdir_events_mission_followup_missions` (succeed A →
issue B, DB-only, no Lua) or the narrative system (§10).

For a mission that unlocks off a **ritual**, `campaign_group_rituals.unlock_mission` already
exists and points at `missions.key` — a direct bridge to the commission/rite work in
`docs/RITUALS.md`. Untested.

---

## 10. The narrative system — not needed yet

`campaign/narrative_system.html` plus `narrative_event`, `narrative_query`, `narrative_trigger`
(~800 KB of docs) is CA's current framework for chained narrative content, and it explicitly
covers "early-game missions and chapter missions". Components chain via **script messages**
rather than events.

It is the right tool for a multi-stage lord storyline. It is **overkill for a single objective**,
and it is a large surface to learn. Start with §9's direct pattern; reach for narrative only when
the chain has enough stages that hand-rolled message passing starts to hurt.

`chapter_mission.html` and `objectives_manager.html` are the other two unread pieces —
chapter missions are the numbered "Chapter 1/2/3" long-campaign structure, and the objectives
manager drives the objectives *list panel* rather than missions themselves.

---

## 11. Checklist for a new mission

1. **`missions`** row, table version **0**. Set `mission_type`, `generate = false`,
   `event_category = Quest`, `quest_mission = true`, `sticky_by_default = true`,
   `can_be_manually_cancelled = false`, `ui_image` to a **CHD eventpic that exists** (§7),
   `ui_icon = rom_event_mission.png`. Leave `quest_character` empty.
2. **`cdir_events_mission_option_junctions`** rows, version **2**, unique `I64` `id`s: the
   `VAR_OBJECTIVE_*` keys §5 lists for that type, plus `VAR_MISSION_LENGTH_INFINITE` (or a
   `_MIN`/`_MAX` pair), plus `VAR_CHANCE 100`, plus `GEN_TARGET_NONE` if the objective needs no
   target, plus `CND_CULTURE wh3_dlc23_chd_chaos_dwarfs` and `CND_UNIQUE` for a one-shot.
   `target = default` on all of them.
3. **`cdir_events_mission_payloads`** rows, version **2**: `status_key = SUCCESS`,
   `value` in `KEY[val];KEY2[val2]` form (§6).
4. **`cdir_events_mission_issuer_junctions`** row, version **1**: `CLAN_ELDERS` unless you mint
   your own issuer.
5. **Loc**: `missions_localised_title_<key>`, `missions_localised_description_<key>`, and
   `mission_text_text_<key>` if any objective is `SCRIPTED`.
6. **Lua gate** (§9) that calls `cm:trigger_mission`.
7. Check duplicate keys before packing (`wh3-check-duplicate-keys-before-packing`), run
   `luac -p` and `py tools/check_lua_api.py`, and `py tools/check_lua_undeclared.py`.
8. In game: confirm the mission actually issues. `cm:trigger_mission` returning false because a
   `CND_*` failed is the most likely first failure, and it is silent.

### First build, measured 2026-09-03

`derpy_test_missions.pack`, run as `wh3_dlc23_chd_conclave`. **Both routes issue and render.**
The four tables written from scratch in a mod pack — `missions` v0,
`cdir_events_mission_option_junctions` v2, `cdir_events_mission_payloads` v2,
`cdir_events_mission_issuer_junctions` v1 — produce a mission that appears in the objectives
panel, and `CLAN_ELDERS` is accepted as an issuer from a mod. `cm:trigger_mission` returned
`true` for a modded row.

**The engine logs every trigger, both routes** — worth knowing before writing a Lua gate:

```
++ triggering mission from db derpy_test_mis_money for faction wh3_dlc23_chd_conclave, fire_immediately: false
++ triggering mission from string for faction wh3_dlc23_chd_conclave mission string is mission{key derpy_test_mis_scripted;issuer CLAN_ELDERS;primary_objectives_and_payload{objective{type SCRIPTED;script_key derpy_test_tally;override_text mission_text_text_derpy_test_scripted;}payload{money 2500;}}}
```

The string route prints the constructed string verbatim, so a malformed condition is readable
in the log rather than guessed at.

**Both routes then completed and paid out**, measured through the MCP bridge on turn 2:

| | DB route (`derpy_test_mis_money`) | String route (`derpy_test_mis_scripted`) |
|---|---|---|
| Objective | `HAVE_AT_LEAST_X_MONEY`, `AMOUNT_INT 1000` | `SCRIPTED`, finished by `cm:complete_scripted_mission_objective` |
| Completed | on end turn, unprompted | on the call, immediately |
| Payload | `TREASURY AMOUNT[5000]` paid | `money 2500` paid — treasury 14091 -> **16591**, exact |
| Panel | row's child switches `button_pin_mission` -> **`tick`** | same |

So a mod-authored `missions` row plus its three junction tables works **end to end**: issues,
renders, evaluates its objective, completes, and pays. Neither route logged anything on
completion — `wh3_mcp_script_errors.log` stayed at the same three pre-existing CA narrative
errors — so **a success listener is the only way to see completion in the log.**

**Two API corrections found doing it:**

- `cm:mission_is_active_for_faction(faction, key)` takes a **faction interface**, not a faction
  key string. Passing the string returns `false` for every mission, including ones visibly on
  the panel — a silent wrong answer, not an error. This is the CLAUDE.md interface-vs-key-vs-CQI
  trap, and this call is in the interface group.
- CA's `episodic_scripting.html` gives its return as `nil`. It returns a **boolean**, and that
  boolean matched the panel exactly in both states.

The cheap panel probe, no script needed: dump
`objectives_screen > subpanel_missions > mission_list_view > list_clip > list_box` and read the
child of each mission row — `tick` means completed, `button_pin_mission` means still open.

**Still unmeasured:** whether `mission_text_text_*` rendered as the objective line (the rows
completed before the text was read), and `missions_localised_mission_completed_text_*`.

---

## 11b. The first shipped quest — Abnagg's Dawn's Harbour (2026-09-09)

`derpy_mis_abnagg_dawns_harbour`, in `!aa_derpy_hashut_legendary_lords.pack`. Built by
`tools/gen_victory_routes.py` alongside the victory routes, because that generator already owns
the string route, the `missions` fragment, the loc fragment and the importer — a quest is those
same four things minus the `victory_type` row.

```
mission
{
	key derpy_mis_abnagg_dawns_harbour;
	issuer CLAN_ELDERS;
	primary_objectives_and_payload
	{
		objective
		{
			type OWN_N_REGIONS_INCLUDING;
			region wh3_main_combi_region_fortress_of_dawn;
			total 1;
		}

		payload
		{
			money 15000;
			faction_pooled_resource_transaction
			{
				resource wh3_dlc23_chd_raw_materials;
				factor missions;
				amount 2500;
				context absolute;
			}
		}
	}
}
```

Five decisions, each with the reason:

* **The string route, not the DB route.** A mod-authored `missions` row carries no objective
  parameters and no reward without `cdir_events_mission_option_junctions`, `_payloads` and
  `_issuer_junctions`, and **HLL ships none of those three** — which is why its eleven existing
  mission rows do nothing (§13.1). A mission *string* carries its objectives and its payload
  itself, and §11 measured it paying `money` to the treasury exactly.
* **What separates a quest from a victory condition is two lines**: no `victory_type` in the
  block and no `game_victory` in the payload. `--selftest` asserts both are absent, because a
  quest that carried them would end the campaign the first time a player took one settlement.
* **The DB row is shaped like CA's own Chaos Dwarf quests**, not like the victory slots:
  `event_category Quest`, `quest_mission true`, `sticky_by_default true`,
  `can_be_manually_cancelled false`, `chd/generic` + `rom_event_mission.png`, location `0,0`.
  Those are the majority values across CA's 704 `Quest` rows (696/704 sticky, 679/704
  non-cancellable) and across all 30-odd `wh3_dlc23_chd_*` quest rows. `mission_type` stays
  `SCRIPTED` — the string supplies the real objective, and `SCRIPTED` is the column value §11
  measured working with it. `generate false` keeps the CDIR from issuing it on its own.
* **The three derived loc keys are what the panel reads** (`missions_localised_title_*`,
  `_description_*`, `_mission_completed_text_*`), not the DB columns — the victory routes
  learned that the hard way with eleven blank titles. `--selftest` asserts each row's loc
  agrees with its own DB column, so the table is not a lie to whoever opens it next.
* **It is region-gated in Lua, not just in the objective.** `wh3_main_combi_region_fortress_of_dawn`
  exists on Immortal Empires and IEE and not on the Old World maps, so the quest is issued only
  where `region_by_key` answers — see `VICTORY_CONDITIONS.md` §12b for the probe (it is on
  `REGION_MANAGER_SCRIPT_INTERFACE`, not on `cm`). Shipping the objective unconditionally would
  put a mission that can never complete on three other maps.

Known ceiling: it is issued from the same `cm:is_new_game()` first tick as the victory routes,
so an existing save never receives it, and it has not yet been seen in a campaign.

**Since 2026-10-04 it is one of six** (`QUESTS` in the same generator), and the shape grew
three parts this section does not show: a `grant` that pools a faction-less lord on
`MissionSucceeded` - Dawn's Harbour now brings Gordak, at level 10 - sack-or-occupy objectives
built as `SCRIPTED` plus listeners, and culture quests issued to every human Chaos Dwarf
faction. `VICTORY_CONDITIONS.md` §12b has the list and the mechanisms.

---

## 11c. A bounty board - CA's Ogre contracts, cloned (2026-09-11)

The pattern for **repeatable, generated missions against a target chosen at runtime**. CA
ships exactly one and its global is literally called `ogre_bounties`, in
`script/campaign/wh3_campaign_ogre_contracts.lua` (extract it from `data_script.pack`; it
is compressed, so a byte-grep gets the path and not the text).

**CA's shape, in five lines.** At `FactionTurnStart`, if the faction holds fewer than three
missions in the `OgreContract` category: pick an issuer among factions met and at peace
whose capital is within 50,000 squared units of one of your settlements; pick one of that
issuer's enemies; pick the closest target to your stuff; price it as
`max(round(sqrt(distance) * 50 / 10) * 10, 2000)` gold, x1.25 for a province capital or an
immortal character; and issue the whole thing with
`cm:trigger_custom_mission_from_string`. There is no accept step and no panel of CA's that
a mod can drive - `ui/campaign ui/ogre_bounties.twui.xml` exists but is CCO-bound to ogre
factions.

**The three objective types CA drives this way**, and the only three with any evidence they
accept a runtime target:

| Objective `type` in the string | Objective conditions CA writes |
|---|---|
| `KILL_CHARACTER_BY_ANY_MEANS` | `family_member <cqi>` |
| `CAPTURE_REGIONS` | `region <region_key>` |
| `RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING` | `region <region_key>;total 1` |

`total 1` is not optional: the objective counts *different* settlements, so without it the
mission wants an unstated number of them.

### Two traps, both in CA's own data

1. **`missions.mission_type` is not the objective.** All 23
   `wh3_main_mission_ogre_contract_defeat_lord_<culture>` rows carry
   `mission_type = ELIMINATE_CHARACTER_IN_BATTLE`, while the script issues those very
   missions with `type KILL_CHARACTER_BY_ANY_MEANS`. The string carries what the game
   evaluates; the column is a label the panel and the CDIR read. Reading the column as the
   objective narrows the mission - a kill that only counts in a battle is a different
   bounty.
2. **`event_category` is a foreign key** into `cdir_events_categories.category_key` (72
   vanilla rows). A category invented for a mod is an unresolvable reference and a
   load-time reject, not a warning. Reuse a vanilla row - `Quest` is what the mods in this
   workspace use.

### The table version is 0, and that is measured

`db/missions_tables` ships at **version 0** with all 19 columns - read off CA's own
`db.pack/db/missions_tables/data__`, and the same in both mod missions tables on this
machine. RPFM's schema also holds a **version 6 with 17 columns**, the older shape
without `localised_mission_completed_text` or `can_be_manually_cancelled`.

Do not rank those definitions by counting field names in RPFM's schema JSON: it repeats
the localised field names after the field array, so v6 counts 19 and v0 counts 22, which
is backwards. Declaring 6 here shipped once and **crashed the game during loading** -
nothing in `bad_mods_report.txt`, no `crash_report/`, and no script log at all, because
the parse fails before a single script line runs. The only evidence was `used_mods.txt`
having a later timestamp than the newest script log.

`tools/gen_great_guilds.py` now pins every declared version to what CA's file declares,
via `read_vanilla_cache.version()`.

### What The Great Guilds ships on top

`derpy_great_guilds.pack`, six rows in `db/missions_tables/derpy_great_guilds` (one per
guild, keyed `derpy_gg_bounty_<guild>`), generated by `tools/gen_great_guilds.py`:

* **Offers, not orders.** CA issues contracts unasked; these sit on a three-slot board in
  the mod's own panel until the player takes one. An untaken offer is withdrawn after 6
  turns; a taken one is a live mission the game's own `turn_limit 20` ends.
* **Targets are factions you are already at war with.** A guild is not a faction and has no
  enemies of its own, so there is no issuer to borrow enemies from, and no guild should be
  able to talk you into a new war.
* **The reward is reputation, and it cannot be a payload.** No payload statement reaches a
  number a mod keeps in a saved value, so the gold is `money N` in the string and the
  reputation is paid in the `MissionSucceeded` handler, matched on
  `context:mission():mission_record_key()`. That accessor is one of exactly five functions
  on `CAMPAIGN_MISSION_SCRIPT_INTERFACE` (`is_null_interface`, `model`, `faction`,
  `mission_record_key`, `mission_issuer_record_key`).
* **One key per guild.** A mission key holds one live mission per faction, so six keys cap
  the board at six and the three-slot board sits well inside that.
* **`MissionFailed` and `MissionCancelled` share one handler.** Both carry the same context
  as `MissionSucceeded` (`mission`, `faction`, `campaign_model`); both free the slot, and
  neither costs reputation.
* **A bounty is not also a generic mission.** The same pack pays every guild a small amount
  for any completed mission; the handler skips that when the mission was a bounty, or five
  guilds get paid for work they never asked for.

Offline coverage in `tools/_guilds_harness.lua`: the board fills and does not overfill,
one offer per guild, the mission string carries the right key / objective type / target /
gold / turn limit, success pays the posting guild its **full** reputation (a bounty is
deliberately not run through the per-turn cap), failure frees the slot and costs nothing,
untaken offers expire while taken ones do not, the board survives a save, and
`rate_bounty = 0` empties it. Two faults injected and caught.

Not yet seen in a campaign: whether a `family_member` cqi captured at offer time still
resolves several turns later when the target has died of something else.

---

## 12. Open questions a first build must answer

1. Does `cm:trigger_mission` log anything when a `CND_*` gate rejects it, or is it silent? If
   silent, the debug route is to strip every `CND_*` row and re-add them one at a time.
   **Partly answered** (2026-09-03): a *successful* trigger logs
   `++ triggering mission from db <key> for faction <f>` — so absence of that line means the
   call never reached the engine. The test rows carried no `CND_*`, so a rejection is still
   untested.
2. `ui/eventpics/chd/generic.png` is missing yet 39 vanilla missions reference it — what does the
   panel actually draw? Determines whether a missing eventpic is a real bug or a shrug.
3. ~~Does a new `mission_issuers` row work?~~ **Answered in §7** — Mixu ships three working rows.
4. `COMPLETE_RITUAL_CHAIN` and `campaign_group_rituals.unlock_mission` — both would connect
   missions to the existing commission/rite system, and both have zero or near-zero precedent.
5. Whether `FAILURE`-status payloads fire reliably (2 vanilla rows is not evidence).
   `SUCCESS` payloads are confirmed on both routes (§11).
6. Whether a mission's completed-text loc key does anything, given every CA row leaves it empty.

---

## 13. What other mods do — the Workshop survey

Measured 2026-09-03 over **404 installed Workshop packs plus the game's own** (665 pack files
scanned, 0 unreadable). **39 packs ship mission content.** Across their Lua:
`cm:trigger_mission` **224** calls, `cm:trigger_custom_mission_from_string` **5**,
`cm:trigger_custom_mission` (the `missions.txt` route) **0** — independent confirmation that §2's
dead route is dead.

### 13.1 This workspace already ships 33 mission rows

`!aa_derpy_hashut_legendary_lords.pack` carries `db/missions_tables/derpy_chd_ll_missions` —
**eleven lords × three missions**, cloning CA's Chaos Dwarf ancestor-relics questline per lord by
suffixing the lord key onto CA's own mission key:

| Pattern | `mission_type` | Notes |
|---|---|---|
| `wh3_dlc23_chd_ancestor_relics_unlock_derpy_<lord>` | `FIGHT_SET_PIECE_BATTLE` | `set_piece_battle = wh3_dlc23_chd_relic_army_uncovered` |
| `wh3_dlc23_chd_ancestor_hellshard_structure_derpy_<lord>` | `CONSTRUCT_N_BUILDINGS_INCLUDING` | |
| `wh3_dlc23_chd_final_battle_derpy_<lord>` | `FIGHT_SET_PIECE_BATTLE` | `set_piece_battle = wh3_dlc23_qb_chd_drill_of_hashut_drazhoath`, `quest_character = 1536972186` |

Lords covered: `ghorth, gargath, balur, vraznak, black_dwf, bzaark, azeros, urzkhal, snakebeard,
tordrek, gordak`. Every row uses `chd/generic` for `ui_image` — the art path §7 shows does not
exist — and carries its English **in the DB row**, not a loc key.

> **Correction, 2026-09-03 (later that day).** The three-row-per-lord shape above is what the
> pack *shipped*, not what it now carries. Two of the three families were unreachable, and not
> for the reason recorded here or in either options document. `chaos_dwarfs_narrative` lives in
> `script/campaign/wh3_main_chaos/` — the **Realms of Chaos** campaign folder — and the engine
> loads a campaign folder only for its own campaign, so in Immortal Empires the Great Drill
> questline does not exist at all, for the mod's houses or for CA's own three lords. The suffix
> mismatch was real and beside the point: there was no listener on the other end. The 22
> `..._relics_unlock_derpy_<lord>` and `..._final_battle_derpy_<lord>` rows are now deleted and
> replaced by two shared rows driven by the mod's own
> `script/campaign/cr_combi_expanded/mod/derpy_chd_drill_chain.lua`. See
> `sessions/HANDOFF_20260903_DRILL_CHAIN.md`. Two details from that pass that generalise: a
> `FIGHT_SET_PIECE_BATTLE` row may sit at `location_x/y = 0,0` (15 vanilla rows do), and a
> literal backslash-n in a `localised_description` **draws on screen** — CA's build turns the escape
> into a line break, RPFM's `import_tsv` does not.
>
> **As shipped now** (read off the Workshop pack 2026-10-09): `derpy_chd_ll_missions` holds 28
> rows - 14 `..._hellshard_structure_derpy_<lord>` (Abnagg, Kharkadon and the Captain's `uzkul`
> added), one shared `wh3_dlc23_chd_ancestor_relics_unlock_derpy`, and 13
> `wh3_dlc23_chd_final_battle_derpy_<faction>` keyed by faction rather than lord. The chain
> script is in all four campaign folders, `wh3_main_combi` included. Beside it,
> `derpy_chd_victory` holds the 5 victory-route slots and 6 quests (`VICTORY_CONDITIONS.md` §12).

**This is the working precedent to copy.** CA names its own per-lord quest rows the same way
(`wh3_dlc23_chd_ancestor_relics_unlock_wh3_dlc23_chd_astragoth`), so a new lord objective is one
row per lord with the lord key as suffix, and the gate is simply which lord's faction you trigger
it for.

The pack drives them from
`script/campaign/{cr_oldworld,cr_darklands}/mod/!!!narrative_chaos_dwarfs_new_factrions.lua`,
which `require`s CA's `wh3_dlc23_narrative_chaos_dwarfs` and **overrides
`chaos_dwarfs_narrative:trigger_relic_missions(faction_key)`** wholesale — adding drill locations
for eleven new factions and re-pointing region keys at `cr_oldworld_*`. That file is the best
in-repo example of the string route:

```lua
mm_relic_tracker:set_mission_issuer("CLAN_ELDERS")
mm_relic_tracker:add_new_objective("SCRIPTED")
mm_relic_tracker:add_condition("script_key relics_counter")
mm_relic_tracker:add_condition("override_text mission_text_text_wh3_dlc23_chd_narrative_relics_counter")
mm_relic_tracker:add_payload("effect_bundle{bundle_key wh3_dlc23_chd_ancestor_relics_counter_reward_dummy;turns 0;}")
mm_relic_tracker:trigger()

cm:callback(function()
    mm_relic_tracker:update_scripted_objective_text(
        "mission_text_text_wh3_dlc23_chd_narrative_relics_counter", 0, 4, "relics_counter")
end, 0.5)
```

Two idioms worth lifting: the reward is an **effect bundle named `..._reward_dummy`** — a payload
that exists only to be a payload — and progress is a `SCRIPTED` objective whose text is re-rendered
with `update_scripted_objective_text(key, count, total, script_name)`.

Same file, the DB-free variants, confirming the condition grammar:

```lua
mm:add_new_objective("FIGHT_SET_PIECE_BATTLE")
mm:add_condition("set_piece_battle wh3_dlc23_chd_relic_of_grimnir")

mm:add_new_objective("CONTROL_N_REGIONS_INCLUDING")
mm:add_condition("total 1")
mm:add_condition("region cr_oldworld_region_silver_pinnacle")
```

### 13.2 The `add_new_objective` vocabulary as modders actually use it

Across the 404 packs, decompressed. Counts are call sites:

```
CAPTURE_REGIONS 66   HAVE_AT_LEAST_X_OF_A_POOLED_RESOURCE 45   OWN_N_UNITS 42
CONSTRUCT_N_BUILDINGS_INCLUDING 38   ENGAGE_FORCE 28   MOVE_TO_REGION 26   SCRIPTED 21
KILL_X_ENTITIES 17   FIGHT_SET_PIECE_BATTLE 16   DEFEAT_N_ARMIES_OF_FACTION 16
CONTROL_N_REGIONS_INCLUDING 15   DESTROY_FACTION 13   MAKE_TRADE_AGREEMENT 5
RAZE_OR_SACK_N_DIFFERENT_SETTLEMENTS_INCLUDING 4   KILL_CHARACTER_BY_ANY_MEANS 4
DECLARE_WAR 4   MAKE_ALLIANCE 3   HAVE_N_AGENTS_OF_TYPE 3   OWN_N_REGIONS_INCLUDING 3
MOVE_TO_PROVINCE 2   RECRUIT_N_UNITS_FROM 1
```

`add_condition` (mods): `total` 187, `region` 167, `unit` 98, `faction` 89, **`ignore_allies` 64**,
`pooled_resource` 45, `building_level` 38, `cqi` 34, `requires_victory` 32, `override_text` 28,
`script_key` 22, `set_piece_battle` 16, `subculture` 13, `confederation_valid` 6, `family_member` 4,
`culture` 4, `position` 3, `province` 2, `agent_subtype` 2, `exclude_existing` 1, `agent` 1.

`ignore_allies`, `culture`, `agent_subtype` and `agent` appear **nowhere in CA's own scripts** —
modder knowledge, not CA's.

`add_payload` (mods): `effect_bundle` 289, `money` 197, `text_display` 58,
`faction_pooled_resource_transaction` 58, **`add_ancillary_to_faction_pool` 39**, `grant_agent` 7,
`influence` 5, `game_victory` 2, `add_mercenary_to_faction_pool` 1.

`add_ancillary_to_faction_pool` is **not in CA's documented payload list** and is the obvious hook
for the house-ancillary work in `docs/ANCILLARY_ACQUISITION_DESIGN.md`.

### 13.3 Packs worth reading before building

| Pack | Why |
|---|---|
| `!aa_derpy_hashut_legendary_lords.pack` | Yours. 28 drill-chain rows, 11 route and quest rows, and the narrative override (§13.1) |
| `ab_mixu_legendary_lords.pack` | The fullest DB set — 9 mission tables including `mission_issuers`, `mission_weights` and both followup tables. Two `missions` files: `mixu_legendary_lords` and `..._contracts` |
| `nag_nagash.pack` | 8 DB files + 6 Lua: a complete quest and victory-condition system for one lord |
| `!scm_legendary.pack` | Skeleton Crew's LLs — per-lord `..._spawn_heroes_&_missions.lua` across four campaign folders |
| `!!gra_knights_origo.pack` | Issuer and payload rows split across two files, plus `..._treasure_maps.lua` |
| `Murranji_bastion.pack` | Small and complete: four tables, one script |

### 13.4 Correction — Workshop packs are no longer all uncompressed

`docs/sessions/COMPAT_ANCILLARIES_20260828.md` established that mod packs ship uncompressed, so
their DB strings and Lua read straight out of the index. **That is now only mostly true.**
`ab_mixu_legendary_lords.pack` reports `"compress": "Zstd"`, and a first survey pass that skipped
compressed entries missed **357 of 1,913 mod Lua files (19%)** — enough to change the counts in
§13.2.

Decompress before scanning. Both formats are in use (WH3 6.2+ added Lz4 and Zstd):

```python
n = struct.unpack('<I', raw[:4])[0]
try:    body = zstandard.ZstdDecompressor().decompress(raw[4:], max_output_size=n)
except: body = lz4.block.decompress(raw[4:], uncompressed_size=n)
```

`open_packfiles` reports the format per pack in its `compress` field, so check rather than assume.

---

## Sources

- `Modding Files/reference/ca_script_docs_wh3/campaign/mission_manager.html`, `episodic_scripting.html`,
  `narrative_system.html`
- `F:\...\Total War WARHAMMER III\assembly_kit\raw_data\db\{mission_types,mission_text,mission_weights,
  cdir_events_mission_statuses,character_skill_level_to_missions_junctions,agent_subtypes_to_mission_groups}.xml`
- `data/db.pack` table index; `data/local_en.pack` → `text/db/{missions__,mission_text__}.loc`
- `data/data_script.pack` → `script/_lib/lib_campaign_mission_manager.lua`,
  `script/campaign/wh3_campaign_grudges_starting_missions.lua`,
  `script/campaign/wh3_campaign_grudges_legendary.lua`
- `.skilltree_cache/` — `missions`, `cdir_events_mission_option_junctions`,
  `cdir_events_mission_payloads`, `cdir_events_mission_issuer_junctions`, `mission_issuers`,
  `cdir_event_targets`, `cdir_events_options`, `cdir_events_payloads` (cached 2026-09-03 via
  `tools/fetch_vanilla_tables.py`; readable with RPFM closed)
- RPFM `schema_wh3.ron` for the reverse-reference graph
