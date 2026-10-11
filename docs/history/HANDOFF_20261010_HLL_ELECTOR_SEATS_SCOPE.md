# HLL - an Elector Count style for the house lords: scope

Date: 2026-10-10. Request: "add a elector count recruitment style for the hll lord mod, scope
what is possible". Read-only session. Nothing was built, packed or deployed.

## 1. What CA's Elector Counts actually is (read from the 9.0 files)

It is not a lord type. No `agent_subtypes` key contains `elector` or `count`. An Elector Count
is a **ministerial position** (`wh2_main_minister_emp_<state>`, 13 of them). You take a
state's capital, then **appoint a lord or hero you already have** to that seat. The seat
gives the character a runefang, unlocks the state's Regiment of Renown and applies a bundle.

| Table | Vanilla rows | Role |
|---|---|---|
| `ministerial_positions` | 62 | the seat records (Empire, Luthor's fleet, Wood Elves, old WH1 ranks) |
| `ministerial_positions_culture_details` | 100 | which culture, subculture **or single faction** has the seat, its loc, and its x/y on the panel |
| `ministerial_positions_to_region_restrictions` | 13 | seat -> the capital region you must own |
| `ministerial_position_effect_bundles` | - | campaign group -> bundle on the holder |
| `campaign_group_member_criteria_ministerial_positions` | - | seat -> campaign group, for the bundle |
| `elector_counts` | 13 | capital, seat, map x/y, `ancillary_reward`, `unit_reward` (**no culture column**) |
| `elector_count_region_to_capital_region_junctions` | 49 | which regions make up each state |
| `campaign_features` | - | `politics` = true for group `wh_main_feature_empire_politics`, whose only member is `wh_main_emp_empire` (faction criterion). Vampire Coast and Wood Elves get it culture-wide |

- **Panel:** `ui/campaign ui/elector_counts.twui.xml` (ui3.pack, 389 KB), bound to
  `CcoCampaignElectorSeat` / `CcoElectorCountRecord`. The HUD's `button_elector_counts` ships
  `is_visible="false"` with no context binding: the **engine** decides who sees it. CA's CCO
  docs list no faction-level function that returns the seats, so the engine fills the list too.
  The generic sibling is `offices.twui.xml` (Luthor's fleet offices, Wood Elves), a legacy
  non-CCO panel (`WarhammerOffices`, `OfficesPanelCallback`) behind `button_offices`.
- **Rewards are Lua, not engine.** `wh2_dlc13_empire_politics.lua:268` listens on
  `CharacterAssignedToPost` and calls `empire_elector_rewards` (`:664`), which force-adds the
  runefang and calls `remove_event_restricted_unit_record_for_faction` for the RoR, out of
  its own hardcoded `EMPIRE_ELECTOR_REWARDS`. The `elector_counts` reward columns only feed
  the panel's display (`UnitRewardContext`, `AncillaryRewardContext`). A mod's own
  `CharacterAssignedToPost` listener can pay out anything.
- **Nothing can appoint from script.** `character:ministerial_position()` is read-only, and
  `episodic_scripting` has no call that writes a seat. Kislev's Atamans (province governors,
  `ProvinceGovernorAppointed`) are the same. Seats are filled by the player's clicks and by
  the engine for the AI. A script cannot fill one for the AI or for the player.

## 2. What other mods have done (installed Workshop packs, surveyed 2026-10-10)

- **The Old World campaign** (`!cr_oldworld_campaign`, which places the HLL houses) extends
  the Empire panel to **18 seats with DB rows only** (`cr_minister_emp_*` on
  `cr_oldworld_region_*` capitals), and **overrides `elector_counts.twui.xml`**.
- Mixu (`!b_mixer`), IEE and SCM add **faction-scoped Wood Elf offices**, DB only. Each one
  stays inside a culture that already has `politics`.
- **Nobody turns `politics` on for a new culture.** Mixer and the Old World turn it *off* for
  some factions (TEB, two Wood Elf factions). Whether CA's panels work for Chaos Dwarfs is
  **unproven**.

## 3. What the HLL pack already does here (audit first)

- **ToZ tier 5, "The Subjugation"** (`zz_derpy_toz_annex.lua`): one seat per modded lord, 12
  seats in three districts. Claiming one confederates the house through a payload (since
  10-10, because `cm:force_confederation` went silent), or, where the house is absent,
  spawns its lord at the claimant's capital at rank 15 with no upkeep
  (`grant_lord_at_capital`). **"Get a house's lord" therefore already exists**; an
  elector-style route would be a second gate onto the same lords.
- **Iron Court** (separate mod): the player appoints governors per province and fills
  offices, all Lua with its own panel. **"Appoint a man to a province" already exists
  there.**
- House ancillaries: the Uniques are vault-only (ToZ seat claim) **by design**. Giving one as
  a seat reward would cut across that design.
- The per-lord unit packs have house RoRs, so an RoR reward per seat is possible for the
  houses that have one. Not every house has one.

## 4. Routes

**A. CA's Elector Counts panel for Chaos Dwarfs. DB plus one Lua listener. Possible in
principle, unproven.** It needs a campaign group with `politics` for the CHD factions, about
14 seats across the seven tables in section 1, loc, `ui/campaign ui/ministerial_offices/<seat>.png`
icons, and a `CharacterAssignedToPost` listener for the rewards. Open questions, each
answerable only in game:
1. Does the engine show `button_elector_counts`, `button_offices` or neither for a
   non-Empire culture?
2. `elector_counts` has no culture column. Would Karl Franz's panel also list the Chaos Dwarf
   seats?
3. The panel's map is the Empire. A Dark Lands map means editing the `.twui.xml`, and the
   Old World campaign already overrides that file. HLL would have to carry the Old World's
   edits too, or lose them.
4. `politics` may switch on more than the panel for that faction.
5. Seats are keyed by region, and the houses live in three campaigns with three region
   namespaces (`cr_oldworld_`, `cr_darklands`, `wh3_main_combi_`). That means one row set per
   campaign, and rows naming regions a loaded campaign lacks. The landmarks pack had to split
   in two over the same problem.

**B. CA's Offices panel (Luthor's style).** The same DB without `elector_counts`. It is
proven for Wood Elf factions, but not for a new culture, so question 1 still applies. It has
no map, no capitals and no holder flags, so it loses most of the Elector Count feel. It is
also unknown whether this panel honours the region restriction.

**C. Our own seats panel, in Lua.** Full control:
- Seats are keyed by **house**, and each capital is read at first tick from `faction:home_region()`,
  so there are no per-campaign region keys.
- Any reward: the existing `grant_lord_at_capital`, `remove_event_restricted_unit_record_for_faction`
  for an RoR, a bundle, an ancillary.
- The AI can hold seats, as `zzz_derpy_toz_ai_seats.lua` already does for the tower.

This is the most expensive route: a new panel under `docs/CUSTOM_UI.md` rules (brief, render,
harness), about the size of the Iron Court governors map. It also overlaps most with the
Iron Court's governors.

**D. The cheapest reading of "recruitment style": hold a house's seat, recruit its lord. Lua
only, no UI.**
- Holding a house's capital puts its lord into your recruit pool, once, with
  `cm:spawn_character_to_pool`, which CA documents.
- Losing the capital takes nothing back, since a pooled or recruited lord cannot be
  un-recruited.
- It reuses the ToZ seat list (subtype, name keys) and its `faction_has_subtype` duplicate
  guard. The rank-on-recruit hook is `derpy_grant_rank_*` in `zzz_derpy_chd_victory_routes.lua`.
- About one file, an MCT switch, and a harness check under Lua 5.1.
- Its weakness: the capital to watch is a region key per campaign, or the house's
  `home_region()` read while the house still lives.

## 5. Recommendation

1. **Decide what "recruitment style" means**, since it picks the route:
   - (i) appoint an existing lord to a house seat for buffs and the house RoR. This is
     faithful to the Empire, and is A, B or C.
   - (ii) owning a house's seat makes its lord recruitable. This is D.
2. For (ii), build D. It is the smallest build of the four and touches no UI.
3. For (i), run **a probe before any design**: one CHD faction in the `politics` group, two
   seats with region restrictions on two capitals it owns, nothing else. That answers
   questions 1, 2 and 4 in one launch. If the panel appears and behaves, A is mostly DB. If
   it does not, C is the only route, and it should be designed against the Iron Court's
   governors rather than beside them.
