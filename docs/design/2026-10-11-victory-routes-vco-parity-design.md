# Victory routes at VCO quality - design (phase 1 of 5: Foundation)

Status: design approved in chat 2026-10-11. Request: "update the victory condition of the hll
mod to be on par quality with the vco mod". The author chose all four areas offered (lore text,
bespoke rewards, named objectives, story and plumbing) and approved the five-phase split below,
with the Uzkul Mingol added. Each phase gets its own spec, plan and build. This file is the
roadmap and the phase 1 spec.

## 1. What VCO has that the HLL routes lack

Measured 2026-10-11 against `victory_conditions_overhaul.pack` (Workshop 3140200173, updated
2026-10-09, 233 MB, 1,522 files), reading Zhatan's IE routes
(`script/vco-ie/main_warhammer/wh3_dlc23_chd_zhatan/missions.lua`), `vco-listeners.lua`,
`vco-listeners-chd.lua`, `vco-loader.lua`, `vco-disable-ca-wincons.lua` and the pack's loc.
The HLL side is `tools/gen_victory_routes.py` and the Lua it emits,
`Modding Files/pack/script/campaign/mod/zzz_derpy_chd_victory_routes.lua`.

| Area | VCO | HLL on 2026-10-11 |
|---|---|---|
| Lore text | Every route opens with a prose paragraph (a `SCRIPTED` objective, `script_key vco_dummy`, completed each turn by one `FactionTurnStart` listener); key objectives carry their own explanatory `override_text` | The route's name, and one sentence shared by all routes |
| Reward | A named effect bundle per route with its own lore and icon (`vco_victory_payload_chd_zha_1_storms_end`, "Corrupted Wu Xing Compass"), often a unique item | A rotating purse and one of eight shared `derpy_trophy_*` items |
| Objectives | Named places: raze or own Wei-Jin, build the Nan-Gau forge in Gunpowder Road, control 5 of 8 named regions | Mostly counts any map can satisfy; five routes switch by map (`_on_map`) |
| Story | A dilemma on some route completions (Astragoth gets Grimgor), the Great Drill chain, an epilogue dilemma after three routes, an ultimate-victory screen | None |
| Issuer | One issuer per route (`VCO_ISSUER_CHD_IME_ZHATAN_1`), two with their own portrait | `CLAN_ELDERS` on every route |
| Achievement | `MissionSucceeded` on `vco_route_victory` awards `WH3_ACHIEVEMENT_WINNING_<culture>_1/_2` | Nothing (section 3.2) |
| 9.0 reward switch | Turned back off after CA turns it on (section 3.1) | Not handled |
| Panel | Clicks the first VCO node when the Victory tab opens | Not handled, not observed |
| Multiplayer | Rewrites the mission key to `wh3_main_mp_victory` | Single-player only, by design (VICTORY_CONDITIONS.md 11.3) |

Separately: the Captain of the Uzkul Mingol (`cr_chd_skullstack`) has no routes. `ROUTES` lists
twelve houses and he is not one of them.

## 2. The five phases

| # | Phase | Covers | Depends on |
|---|---|---|---|
| 1 | Foundation (this spec) | Route rewards paid again under 9.0; the victory achievement on route completion; the panel measured | nothing |
| 2 | Lore text | An opening paragraph for each route (the `SCRIPTED` header and its completer, which reverses the generator's "no SCRIPTED flavour objectives" decision), explanatory text on key objectives, and three routes for the Uzkul Mingol. Sources: Lexicanum and White Dwarf, as in the 2026-10-04 lore pass. VCO's panel click fix goes in here if phase 1's measurement fails | 1 |
| 3 | Bespoke rewards | A named effect bundle per route, lore and effects tied to the route, CA icons | 1 |
| 4 | Named objectives | Named cities and landmarks behind the existing map gate: the Old World first, where most houses live, then IE/IEE for Ghorth, Kharkadon, the Black Dwarf and Abnagg. Every region key verified on its map | 1 |
| 5 | Story beats | A completion incident or dilemma per house; an epilogue after several routes | 1-4 |

Multiplayer stays out of every phase: VCO's key rewrite would collapse our five route keys onto
one.

## 3. Phase 1: Foundation

Both changes go into the Lua that `build_lua()` in `tools/gen_victory_routes.py` emits. No new
file, no DB row, no loc.

### 3.1 Pay the route rewards again

**The fault.** 9.0's `victory_objectives_config.lua` sets the saved value
`IEVictoryConditionUseDLC29Config` on every new Immortal Empires game (line 13725), and
`_victory_objectives_ie:add_scripted_victory_listeners()` then calls
`cm:set_victory_mission_rewards_disabled(true)` on every load (line 13909), commented "Victory
mission payload will not be granted to player". CA pays its own factions through a Victory
Achieved incident instead. Our houses are not in `config.factions`, so nothing pays them.
VCO's `vco-disable-ca-wincons.lua` names the same fault ("Override the global flag that broke
VCO rewards") and calls `cm:set_victory_mission_rewards_disabled(false)`. So in a new IE or IEE
game since 9.0 our purses and trophies are most likely withheld. Nobody has seen this in game.
This closes the open item in VICTORY_CONDITIONS.md section 10 on the side of "withheld".

**The fix.** A `cm:add_post_first_tick_callback`, registered at file scope, runs on every load.
In single-player, when the human faction has an entry in `ROUTES`, it calls
`cm:set_victory_mission_rewards_disabled(false)` and logs one line.

Why post-first-tick: CA's call runs inside `start_game_all_factions()`, from wh_start.lua's
`cm:add_first_tick_callback` (the shared list). `process_first_tick_callbacks` runs the shared
list and then the post list (`lib_campaign_manager.lua` 2495-2498), so ours always lands after
CA's.

Rejected:

- Wrapping `_victory_objectives_ie.add_scripted_victory_listeners`, VCO's way. It reaches into
  CA's internals for the same result.
- Paying the rewards from our own `MissionSucceeded` listener. It pays twice whenever the switch
  is already off (VCO installed, a pre-9.0 save, the Old World), the double payment the
  `wh3-mission-string-route-carries-no-db-payload` memory records.

Scope: the switch is campaign-wide, so we touch it only when a human faction is ours. A CA
faction's player keeps CA's incident rewards and is never paid twice. Multiplayer is skipped,
because we issue no routes there. Running saves get the fix on their next load, before any route
can complete.

### 3.2 The victory achievement

**The fault.** CA awards `WH3_ACHIEVEMENT_WINNING_CHAOS_DWARFS_1` (and `_2` above difficulty 3)
from one listener, `WH3_ACHIEVEMENT_LONG_VICTORY_COMPLETE` in `wh3_campaign_achievements.lua`
(line 380), on `MissionSucceeded` for `wh_main_long_victory` only. Our routes run on
`derpy_route_victory_1` to `_5`, so no route win awards it.

**The fix.** One `core:add_listener` on `MissionSucceeded`, registered on every load. It fires
when the mission key is one of `SLOT_KEYS` and the faction is human. It reuses CA's own
`award_achievement_to_faction(faction_key, key)` and `wh3_campaign_achievements.long_victory`
table, the way VCO's `vco_WH3_ACHIEVEMENT_LONG_VICTORY_COMPLETE_safety_unlock` does: `_1`
always, `_2` when `cm:get_difficulty() > 3`. Both are globals from `wh3_campaign_achievements.lua`,
which `wh_campaign_setup.lua` requires for every campaign. The listener checks they exist and
logs when they do not, so a campaign without them loses the achievement and nothing else.
Awarding twice is harmless. Running saves benefit, since their routes use the same keys.

### 3.3 The panel: measure, do not build

VCO clicks its first route node when the Victory tab opens, because the panel otherwise showed
vanilla conditions. No handoff records our panel doing that. This becomes one item on the
in-game check in section 5; VCO's fix is built in phase 2 only if that item fails.

## 4. Checks

- `py tools/gen_victory_routes.py --selftest` gains three cases, run against the shipped Lua
  under Lua 5.1.5 with the existing stubbed campaign:
  1. A stubbed CA call sets the switch to `true` in the shared first-tick list; after our post
     callback it reads `false`. With a CA faction as the human, and in multiplayer, it stays
     `true`.
  2. Firing `MissionSucceeded` with `derpy_route_victory_2` for a human house records `_1`, and
     `_2` only above difficulty 3. A quest key, an AI faction and `wh_main_long_victory` record
     nothing.
  3. With CA's two achievement globals absent, the listener logs and does not throw.
- Each new assertion is mutation-proven: delete the call it guards and watch the selftest fail
  (`test-must-measure-not-restate`).
- `luac -p`, `tools/check_lua_api.py` and `tools/check_lua_undeclared.py` on the shipped Lua.
  `set_victory_mission_rewards_disabled` is not in CA's docs, so `check_lua_api.py` will flag
  it; the plan settles how that finding is recorded rather than suppressed blindly.
- `py tools/gen_victory_routes.py --check` stays green.

## 5. Ship, and what to look at in game

Import the regenerated Lua into `!aa_derpy_hashut_legendary_lords.pack` with
`tools/import_victory_routes.py` (RPFM open), run `--verify-only` on the saved pack, back up to
`Modding Files/Backup/`, and copy the pack into its Workshop folder. It is Workshop-hosted, so
it does not go into `data/`.

In game, a new IE or IEE campaign as the Black Dwarf or Abnagg:

1. The script log shows the switch line on the first tick.
2. The first route to complete pays its purse and trophy: the treasury or pooled resource moves
   by the amount the panel's Reward box showed, and the item appears in the faction's pool.
3. The Victory tab opens on one of our routes, not a vanilla node (section 3.3).

The achievement cannot be tested without spending it; the selftest is its evidence.

## 6. Docs

- VICTORY_CONDITIONS.md section 10: replace the open 9.0 item with VCO's evidence and the fix.
  Section 12: the two listeners.
- `docs/SESSION_INDEX.md`: one line.
- `docs/MY_MODS.md`: one clause in the lords pack row.
