# Victory routes at VCO quality, phase 1 (Foundation) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pay the HLL victory routes' rewards again under WH3 9.0, and award CA's Chaos Dwarf victory achievement when a route completes.

**Architecture:** Both changes are emitted by `build_lua()` in `tools/gen_victory_routes.py` into the one shipped script, `script/campaign/mod/zzz_derpy_chd_victory_routes.lua`. A post-first-tick callback switches CA's campaign-wide reward switch back off, and a `MissionSucceeded` listener reuses CA's own achievement function. The generator's `--selftest` runs the shipped Lua under Lua 5.1.5 against a stubbed campaign; it gains new stubs, two new check sections and a mutation table that proves each check can fail.

**Tech Stack:** Python 3 (generator and selftest), Lua 5.1.5 (`C:\Program Files (x86)\Lua\5.1\lua.exe` / `luac.exe`), the RPFM MCP server for the import (RPFM must be open).

**Spec:** `docs/superpowers/specs/2026-10-11-victory-routes-vco-parity-design.md`

## Global Constraints

- The workspace is not a git repo: there are no commit steps. Backups go to `Modding Files/Backup/<reason>_<date>/`, never into `data/` or a Workshop folder.
- Edit the generator, never the generated Lua. `Modding Files/pack/script/campaign/mod/zzz_derpy_chd_victory_routes.lua` is written by `py tools/gen_victory_routes.py`.
- No new file, no DB row, no loc in this phase (spec section 3).
- Text written in this phase (comments, log lines, docs) contains no em dash and no en dash (antislop R-02, active this session), and no emoji (`no-emojis-anywhere`).
- Never say "rung" (`no-rung-terminology`).
- The lords pack is Workshop-hosted (id 3432966208). It is deployed to the Workshop folder and never copied into the game's `data/` folder.
- Baseline measured 2026-10-11 before any edit: Modpacks and Workshop copies of the lords pack are both md5 `153d0ae8877a21f41584fa33cc25cd3d`; the route script in the pack, the staged copy and `build_lua()` are byte-identical; `--check`, `--selftest`, `check_lua_api.py` and `check_lua_undeclared.py` are all clean.

## Review Focus

1. **A save started before this update.** The spec says running saves get both fixes on their next load. Pinned in Task 1 (switch with `new_game=False`) and Task 2 (achievement with `new_game=False`).
2. **A campaign where the reward switch method does not exist** (a game interface without it). The call must not throw out of the post-first-tick list, because CA's `call_each` has no `pcall` and every later post callback, other mods' included, would die. Pinned in Task 1 (`ca_rewards_disabled=None`).
3. **The Old World and Realms of Chaos**, where CA never sets the switch. Our `false` is then a no-op; nothing to test offline beyond item 2. In-game check only.
4. **Quests.** CA's switch is documented for victory missions only, so the six quests should pay whether or not it is set. Not testable offline; Task 3's in-game list carries it.
5. **A second route completed after the victory screen.** The listener awards again; Steam ignores a repeat award. Harmless, no test.

---

### Task 1: Switch the route rewards back on (harness plumbing, section 7, first mutants)

**Files:**
- Modify: `tools/gen_victory_routes.py` (the `HARNESS` string at lines 2124-2264, `_run_lua` at 2267-2307, `selftest()` before its section 6 at line 2700, the closing print at 2887-2891, and `build_lua()` above line 1721)
- Modify: `tools/check_lua_api.py` (the `CA_USED` dict, lines 177-180)

**Interfaces:**
- Produces: `_run_lua(..., calls=None, new_game=True, ca_rewards_disabled=True)`. `calls` receives `"log|<out text>"` for every `out()` line and one final `"rewards_final|<true|false|nil>"`. Inside `selftest()`: `bd`, `run_calls(path, humans, **kw) -> list`, `rewards_final(calls) -> str`, `check_rewards(path)`, `mutant(needle, repl) -> path`, `MUTANTS` (list of `(needle, replacement, checker)`).
- Produces (shipped Lua): `local function derpy_routes_human()` and one `cm:add_post_first_tick_callback`.

- [ ] **Step 1: Extend the harness.** In `HARNESS`, replace

```lua
local triggered = {}
local skipped = {}
local first_tick

function out(_) end
function is_table(t) return type(t) == "table" end

cm = {}
function cm:add_first_tick_callback(fn) first_tick = fn end
function cm:is_new_game() return true end
```

with

```lua
local triggered = {}
local skipped = {}
local first_tick
local post_tick
-- What the reward switch and the achievement listener did, written to CALLS_PATH:
-- "log|<out line>", "ach|<faction>|<key>", and one "rewards_final|<state>" at the end.
local calls = {}

function out(s) table.insert(calls, "log|" .. tostring(s)) end
function is_table(t) return type(t) == "table" end
function is_function(f) return type(f) == "function" end

cm = {}
function cm:add_first_tick_callback(fn) first_tick = fn end
function cm:add_post_first_tick_callback(fn) post_tick = fn end
function cm:is_new_game() return NEW_GAME ~= false end
-- CA's 9.0 shared first-tick callback has run by the time the post list does, and it leaves
-- victory rewards switched off: REWARDS_DISABLED is that state. nil = no such method.
local rewards_disabled = REWARDS_DISABLED
if REWARDS_DISABLED ~= nil then
	function cm:set_victory_mission_rewards_disabled(b) rewards_disabled = b end
end
```

Then replace `if first_tick then first_tick() end` with

```lua
if first_tick then first_tick() end
if post_tick then post_tick() end
```

Then, directly after the existing `if DONE_PATH then ... end` block, add

```lua
if CALLS_PATH then
  table.insert(calls, "rewards_final|" .. tostring(rewards_disabled))
  local fh = io.open(CALLS_PATH, "w")
  fh:write(table.concat(calls, "\n"))
  fh:close()
end
```

- [ ] **Step 2: Extend `_run_lua`.** Change the signature and docstring tail to

```python
def _run_lua(script_path, humans, probe, multiplayer=False, regions=(), fire=(), done=None,
             calls=None, new_game=True, ca_rewards_disabled=True):
    """Run the shipped Lua under the harness. Returns (report, issued) - `issued` is
    {faction: [mission string, ...]} read back out of the run, not rebuilt.

    `fire` is [(event, faction, region)] replayed at the captured listeners after the first
    tick; every cm:complete_scripted_mission_objective call they make is appended to `done`
    as "faction|mission|script_key|true".

    `calls` receives every out() line as "log|<text>", every achievement award as
    "ach|<faction>|<key>", and last "rewards_final|<state>": CA's reward switch as the
    post-first-tick list leaves it. `ca_rewards_disabled` is the state CA's 9.0 first-tick
    callback leaves behind (None: the method does not exist), and `new_game` False replays a
    loaded save."""
```

Add `calls_path = os.path.join(td, "calls.txt")` after `done_path`, and make the preamble

```python
        preamble = ("SCRIPT_PATH = %s\nHUMANS = {%s}\nPROBE = {%s}\nMULTIPLAYER = %s\n"
                    "MAP_REGIONS = {%s}\nDUMP_PATH = %s\nDONE_PATH = %s\nFIRE = {%s}\n"
                    "CALLS_PATH = %s\nNEW_GAME = %s\nREWARDS_DISABLED = %s\n") % (
            _lua_str(script_path),
            ", ".join(_lua_str(h) for h in humans),
            ", ".join(_lua_str(p) for p in probe),
            "true" if multiplayer else "false",
            ", ".join(_lua_str(r) for r in regions),
            _lua_str(dump),
            _lua_str(done_path),
            ", ".join("{%s}" % ", ".join(_lua_str(x) for x in ev) for ev in fire),
            _lua_str(calls_path),
            "true" if new_game else "false",
            "nil" if ca_rewards_disabled is None
            else ("true" if ca_rewards_disabled else "false"),
        )
```

After the existing `if done is not None ...` readback add

```python
        if calls is not None and os.path.exists(calls_path):
            with open(calls_path, encoding="utf-8") as fh:
                calls.extend(l for l in fh.read().splitlines() if l)
```

- [ ] **Step 3: Write the failing check.** In `selftest()`, immediately above the line `        # 6. deliberate breaks must be caught`, insert

```python
        # 7. CA'S 9.0 REWARD SWITCH. wh_start.lua's shared first-tick callback leaves victory
        #    mission rewards switched OFF for the whole campaign, and the harness starts there.
        #    The shipped post-first-tick callback must switch them back on for one of our
        #    houses, on a new game and on a load, and leave every other case alone.
        bd = "cr_chd_slaves_of_the_black_dwarf"

        def run_calls(path, humans, **kw):
            calls = []
            _run_lua(path, humans, humans, calls=calls, **kw)
            return calls

        def rewards_final(calls):
            finals = [c for c in calls if c.startswith("rewards_final|")]
            assert len(finals) == 1, "expected one rewards_final line, got %r" % finals
            return finals[0].split("|", 1)[1]

        def check_rewards(path):
            for who in (bd, "wh3_dlc23_chd_conclave", "wh3_dlc23_chd_minor_faction"):
                got = rewards_final(run_calls(path, [who]))
                assert got == "false", "%s: rewards left switched off (%s)" % (who, got)
            got = rewards_final(run_calls(path, [bd], new_game=False))
            assert got == "false", "a loaded save kept rewards switched off (%s)" % got
            got = rewards_final(run_calls(path, ["wh_main_dwf_dwarfs"]))
            assert got == "true", "switched rewards on for a faction we have no routes for"
            got = rewards_final(run_calls(path, HOUSES, multiplayer=True))
            assert got == "true", "touched the reward switch in multiplayer"
            calls = run_calls(path, [bd], ca_rewards_disabled=None)
            assert any("could not switch victory mission rewards on" in c for c in calls), \
                "a missing reward switch was not caught and logged"

        check_rewards(script)

        # 9. MUTANTS. Each breaks one line of the shipped Lua, still parses, and the check that
        #    guards that line must notice. A check no mutant can fail proves nothing.
        def mutant(needle, repl):
            src = build_lua()
            assert src.count(needle) == 1, (
                "mutation anchor %r occurs %d times - move the anchor with the code"
                % (needle, src.count(needle)))
            path = os.path.join(td, "mutant.lua")
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(src.replace(needle, repl))
            r = subprocess.run([LUAC, "-p", path], capture_output=True, text=True)
            assert r.returncode == 0, "mutant for %r does not parse: %s" % (needle, r.stderr)
            return path

        MUTANTS = [
            ("cm:set_victory_mission_rewards_disabled(false)", "local _ = false", check_rewards),
            ("if not derpy_routes_human() then", "if false then", check_rewards),
            ("if cm:is_multiplayer() then\n\t\treturn false", "if false then\n\t\treturn false",
             check_rewards),
        ]
        for needle, repl, guard in MUTANTS:
            try:
                guard(mutant(needle, repl))
            except AssertionError:
                continue
            raise AssertionError("mutant survived: %r -> %r" % (needle, repl))
```

- [ ] **Step 4: Run it and watch it fail.**

Run: `py tools/gen_victory_routes.py --selftest`
Expected: FAIL with `AssertionError: cr_chd_slaves_of_the_black_dwarf: rewards left switched off (true)`. If it fails anywhere else, Step 1 or 2 broke the harness; fix that first.

- [ ] **Step 5: Emit the Lua.** In `build_lua()`, inside the last `parts.append('''...''')` string, insert this block immediately above the line `cm:add_first_tick_callback(function()` (currently line 1721). It is a non-raw Python string, so indentation is written `\t` exactly as the surrounding code does:

```
-- 7. CA'S 9.0 REWARD SWITCH. victory_objectives_config.lua marks every new Immortal Empires
-- game with the saved value IEVictoryConditionUseDLC29Config, and on every load
-- _victory_objectives_ie:add_scripted_victory_listeners() then calls
-- cm:set_victory_mission_rewards_disabled(true) for the whole campaign. CA pays its own
-- factions through a Victory Achieved incident instead; our houses are not among them, so
-- every route's purse and trophy went unpaid. VCO hit the same fault and switches it back.
--
-- CA's call runs in the shared first-tick list (wh_start.lua, start_game_all_factions), and
-- process_first_tick_callbacks runs the post list after it, so ours lands last. Only when a
-- human is one of our houses: a CA faction's player keeps CA's incident and is never paid
-- twice. Not in multiplayer, where no route is issued. pcall because a throw here would take
-- every post callback queued after this one with it.
local function derpy_routes_human()
\tif cm:is_multiplayer() then
\t\treturn false
\tend

\tlocal humans = cm:get_human_factions()

\tfor i = 1, #humans do
\t\tif ROUTES[humans[i]] then
\t\t\treturn true
\t\tend
\tend

\treturn false
end

cm:add_post_first_tick_callback(function()
\tif not derpy_routes_human() then
\t\treturn
\tend

\tlocal ok, err = pcall(function()
\t\tcm:set_victory_mission_rewards_disabled(false)
\tend)

\tif ok then
\t\tout("derpy_chd_victory_routes: victory mission rewards switched back on")
\telse
\t\tout("derpy_chd_victory_routes: could not switch victory mission rewards on: " .. tostring(err))
\tend
end)

```

- [ ] **Step 6: Run the selftest and watch it pass.**

Run: `py tools/gen_victory_routes.py --selftest`
Expected: `selftest ok - ...`, exit 0. The three mutants are killed silently; a surviving one raises `mutant survived`.

- [ ] **Step 7: Record the undocumented call.** In `tools/check_lua_api.py`, change `CA_USED` to

```python
CA_USED = {
    "cm:entity_add_pooled_resource_transaction":
        "wh3_campaign_grudges.lua:870, wh3_cp1_bhashiva.lua:1354-1356 (negative values too)",
    "cm:set_victory_mission_rewards_disabled":
        "main_warhammer/victory_objectives_config.lua:13909 (true, every load of a 9.0 IE game)",
}
```

Then confirm CA really calls it, and that the checker is still sound:

Run: `grep -rn "set_victory_mission_rewards_disabled" "Modding Files/reference/ca_scripts_wh3"` (Git Bash)
Expected: one hit, `campaign/main_warhammer/victory_objectives_config.lua:13909`.
Run: `py tools/check_lua_api.py --selftest`
Expected: exit 0.

- [ ] **Step 8: Lint the generated Lua without touching the staged copy.**

```bash
py -c "import sys; sys.path.insert(0, 'tools'); import gen_victory_routes as G; open(sys.argv[1], 'w', encoding='utf-8', newline='\n').write(G.build_lua())" "$TEMP/routes_p1.lua"
"/c/Program Files (x86)/Lua/5.1/luac.exe" -p "$TEMP/routes_p1.lua"
py tools/check_lua_api.py "$TEMP/routes_p1.lua"
py tools/check_lua_undeclared.py "$TEMP/routes_p1.lua"
```

Expected: luac exit 0, `0 suspect call(s)`, `0 with undeclared names`.

---

### Task 2: The victory achievement (section 8, more mutants)

**Files:**
- Modify: `tools/gen_victory_routes.py` (`HARNESS`, `_run_lua`, `selftest()` section 8 and the `MUTANTS` list from Task 1, `build_lua()`)

**Interfaces:**
- Consumes: `run_calls`, `bd`, `mutant`, `MUTANTS` from Task 1; `SLOT_KEYS` (module level, five `derpy_route_victory_N` keys).
- Produces: `_run_lua(..., difficulty=1, achievements=True)`; `check_achievements(path)`; shipped Lua `local ROUTE_KEYS` and `local function derpy_achievement_listener()`, called from the first-tick callback on every load.

- [ ] **Step 1: Stub CA's achievement script and `is_human` in the harness.** In `HARNESS`, directly after the `function cm:set_victory_mission_rewards_disabled` block from Task 1, add

```lua
function cm:get_difficulty() return DIFFICULTY end
-- CA's wh3_campaign_achievements.lua, as wh_campaign_setup.lua loads it for every campaign.
-- ACHIEVEMENTS false leaves both globals nil, as a campaign without that script would.
if ACHIEVEMENTS then
	wh3_campaign_achievements = {long_victory = {wh3_dlc23_chd_chaos_dwarfs = "CHAOS_DWARFS"}}
	function award_achievement_to_faction(faction_key, key)
		table.insert(calls, "ach|" .. faction_key .. "|" .. key)
	end
end
local function is_human(key)
	for _, h in ipairs(HUMANS) do
		if h == key then return true end
	end
	return false
end
```

Then give both faction stand-ins an `is_human`: in `cm:get_faction` replace

```lua
	return {name = function() return key end, culture = function() return culture_of(key) end,
		is_null_interface = function() return false end}
```

with

```lua
	return {name = function() return key end, culture = function() return culture_of(key) end,
		is_null_interface = function() return false end,
		is_human = function() return is_human(key) end}
```

and in `named(n)` replace

```lua
local function named(n) return {name = function() return n end,
	culture = function() return culture_of(n) end,
	is_null_interface = function() return false end} end
```

with

```lua
local function named(n) return {name = function() return n end,
	culture = function() return culture_of(n) end,
	is_null_interface = function() return false end,
	is_human = function() return is_human(n) end} end
```

The new `is_human` sits near the top of the harness, above both `cm:get_faction` and `named`, so both closures see it.

- [ ] **Step 2: Pass difficulty and the achievement switch through `_run_lua`.** Add `difficulty=1, achievements=True` to the signature after `ca_rewards_disabled=True`. Append to the docstring: `` `difficulty` is what cm:get_difficulty() answers (4 is very hard), and `achievements` False leaves CA's achievement script unloaded.``. Extend the preamble format with `"DIFFICULTY = %d\nACHIEVEMENTS = %s\n"` and its two values, `difficulty` and `"true" if achievements else "false"`.

- [ ] **Step 3: Write the failing check.** In `selftest()`, directly after `check_rewards(script)` and above `# 9. MUTANTS`, insert

```python
        # 8. THE VICTORY ACHIEVEMENT, through the shipped listener (FIRE's third field is the
        #    mission key). A route key awards _1, and _2 only above difficulty 3, on a new game
        #    and on a load; a quest, an AI house and CA's own long-victory key award nothing;
        #    without CA's achievement script the listener logs and does not throw.
        ach = "WH3_ACHIEVEMENT_WINNING_CHAOS_DWARFS"

        def awarded(calls):
            return [c for c in calls if c.startswith("ach|")]

        def check_achievements(path):
            got = awarded(run_calls(path, [bd], fire=[("MissionSucceeded", bd, SLOT_KEYS[1])]))
            assert got == ["ach|%s|%s_1" % (bd, ach)], "difficulty 1 awarded %r" % got
            got = awarded(run_calls(path, [bd], difficulty=4,
                                    fire=[("MissionSucceeded", bd, SLOT_KEYS[4])]))
            assert got == ["ach|%s|%s_1" % (bd, ach), "ach|%s|%s_2" % (bd, ach)], \
                "very hard awarded %r" % got
            got = awarded(run_calls(path, [bd], new_game=False,
                                    fire=[("MissionSucceeded", bd, SLOT_KEYS[0])]))
            assert got == ["ach|%s|%s_1" % (bd, ach)], "a loaded save awarded %r" % got
            got = awarded(run_calls(path, [bd], difficulty=5, fire=[
                ("MissionSucceeded", bd, "derpy_mis_black_dwarf_road_to_praag_ie"),
                ("MissionSucceeded", "cr_chd_house_of_baal", SLOT_KEYS[0]),
                ("MissionSucceeded", bd, "wh_main_long_victory")]))
            assert got == [], "awarded outside a human's route: %r" % got
            calls = run_calls(path, [bd], achievements=False,
                              fire=[("MissionSucceeded", bd, SLOT_KEYS[0])])
            assert not awarded(calls), "awarded with CA's achievement script absent"
            assert any("achievement script is not loaded" in c for c in calls), \
                "an absent achievement script was not logged"
            assert not any("achievement listener failed" in c for c in calls), \
                "the achievement listener threw: %r" % [c for c in calls if "failed" in c]

        check_achievements(script)
```

and append four rows to `MUTANTS`:

```python
            ("if not ROUTE_KEYS[context:mission():mission_record_key()] then", "if false then",
             check_achievements),
            ("if not faction:is_human() then", "if false then", check_achievements),
            ("if cm:get_difficulty() > 3 then", "if true then", check_achievements),
            ("if not is_function(award_achievement_to_faction) "
             "or not is_table(wh3_campaign_achievements) then", "if false then",
             check_achievements),
```

- [ ] **Step 4: Run it and watch it fail.**

Run: `py tools/gen_victory_routes.py --selftest`
Expected: FAIL with `AssertionError: difficulty 1 awarded []`.

- [ ] **Step 5: Emit the listener.** In `build_lua()`, insert this block directly below the Task 1 block (still above `cm:add_first_tick_callback(function()`). The `ROUTE_KEYS` line splices `SLOT_KEYS` in the same way the file already splices `RANK_KEY_PREFIX`:

```
-- 8. THE VICTORY ACHIEVEMENT. CA awards WH3_ACHIEVEMENT_WINNING_<culture>_1, and _2 above
-- difficulty 3, from one listener in wh3_campaign_achievements.lua, on wh_main_long_victory
-- only, so a route win awarded nothing. Same award through CA's own function and table, as
-- VCO's vco_WH3_ACHIEVEMENT_LONG_VICTORY_COMPLETE_safety_unlock does. Registered on every
-- load: the route lives in the save, the listener does not.
local ROUTE_KEYS = {''' + ", ".join("%s = true" % k for k in SLOT_KEYS) + '''}

local function derpy_achievement_listener()
\tcore:add_listener("derpy_chd_route_achievement", "MissionSucceeded", true,
\t\tfunction(context)
\t\t\tlocal ok, err = pcall(function()
\t\t\t\tif not ROUTE_KEYS[context:mission():mission_record_key()] then
\t\t\t\t\treturn
\t\t\t\tend

\t\t\t\tlocal faction = context:faction()

\t\t\t\tif not faction:is_human() then
\t\t\t\t\treturn
\t\t\t\tend

\t\t\t\tif not is_function(award_achievement_to_faction) or not is_table(wh3_campaign_achievements) then
\t\t\t\t\tout("derpy_chd_victory_routes: CA's achievement script is not loaded, no achievement")
\t\t\t\t\treturn
\t\t\t\tend

\t\t\t\tlocal names = wh3_campaign_achievements.long_victory
\t\t\t\tlocal name = is_table(names) and names[faction:culture()]

\t\t\t\tif not name then
\t\t\t\t\treturn
\t\t\t\tend

\t\t\t\tlocal faction_key = faction:name()
\t\t\t\tlocal key = "WH3_ACHIEVEMENT_WINNING_" .. name

\t\t\t\taward_achievement_to_faction(faction_key, key .. "_1")

\t\t\t\tif cm:get_difficulty() > 3 then
\t\t\t\t\taward_achievement_to_faction(faction_key, key .. "_2")
\t\t\t\tend

\t\t\t\tout("derpy_chd_victory_routes: victory achievement awarded to " .. faction_key)
\t\t\tend)
\t\t\tif not ok then
\t\t\t\tout("derpy_chd_victory_routes: achievement listener failed: " .. tostring(err))
\t\t\tend
\t\tend, true)
end

```

Then register it on every load. In the same string replace

```
cm:add_first_tick_callback(function()
\tderpy_take_listeners()
\tderpy_grant_listeners()
\tderpy_confed_listeners()
```

with

```
cm:add_first_tick_callback(function()
\tderpy_take_listeners()
\tderpy_grant_listeners()
\tderpy_confed_listeners()
\tderpy_achievement_listener()
```

- [ ] **Step 6: Run the selftest and watch it pass.**

Run: `py tools/gen_victory_routes.py --selftest`
Expected: `selftest ok`, exit 0, with all seven mutants killed.

- [ ] **Step 7: Update the closing print** in `selftest()` so the summary names what is now verified:

```python
    print("selftest ok - %d routes across %d houses (Ghorth %d) and %d quests; Lua run, "
          "MP guard, disable guard, both map gates, sack-or-occupy listeners, TSV agreement, "
          "25 deliberate breaks, the 9.0 reward switch, the route achievement and %d Lua "
          "mutants all verified"
          % (sum(len(ROUTES[f]) for f in HOUSES), len(HOUSES),
             len(ROUTES["wh3_dlc23_chd_conclave"]), len(all_quests()), len(MUTANTS)))
```

`MUTANTS` is assigned inside the `with` block, which is still `selftest()`'s own scope, so the print can read it.

Run: `py tools/gen_victory_routes.py --selftest`
Expected: the line ends `... and 7 Lua mutants all verified`.

- [ ] **Step 8: Lint again.** Repeat Task 1 Step 8's four commands, plus:

Run: `py tools/check_lua_literal_left.py "$TEMP/routes_p1.lua"`
Expected: no finding (the only new comparison, `cm:get_difficulty() > 3`, has its literal on the right).

---

### Task 3: Generate, import, verify and deploy

**Files:**
- Regenerate: `Modding Files/pack/script/campaign/mod/zzz_derpy_chd_victory_routes.lua` and the six TSVs under `Modding Files/source/victory_routes/` (TSVs come out byte-identical; only the Lua changes)
- Modify: `Modding Files/Modpacks/!aa_derpy_hashut_legendary_lords.pack`, then its Workshop copy

**Interfaces:**
- Consumes: the generator from Tasks 1-2.

- [ ] **Step 1: Hash the TSVs, then generate.** (Git Bash) This phase adds no row, so the six TSVs must come out byte-identical:

```bash
md5sum "Modding Files/source/victory_routes/"*.tsv > "$TEMP/vr_tsv_before.md5"
py tools/gen_victory_routes.py
py tools/gen_victory_routes.py --check
```

Expected: seven `wrote ...` lines, then `check ok - 12 houses, 43 routes, ...`, exit 0.

- [ ] **Step 2: Confirm only the Lua changed.**

Run: `md5sum -c "$TEMP/vr_tsv_before.md5"`
Expected: six `OK` lines. A `FAILED` line means a TSV moved: stop and find out why before importing.

- [ ] **Step 3: Check RPFM is open.** (PowerShell)

Run: `Invoke-WebRequest http://127.0.0.1:45127/sessions -TimeoutSec 4 -UseBasicParsing`
Expected: HTTP 200. On connection refused, STOP and ask the user to open RPFM. Never fall back to editing the pack another way.

- [ ] **Step 4: Back up the base.** (Git Bash)

```bash
mkdir -p "Modding Files/Backup/pre_vco_parity_p1_20261011"
cp "Modding Files/Modpacks/!aa_derpy_hashut_legendary_lords.pack" "Modding Files/Backup/pre_vco_parity_p1_20261011/"
md5sum "Modding Files/Backup/pre_vco_parity_p1_20261011/!aa_derpy_hashut_legendary_lords.pack"
```

Expected: `153d0ae8877a21f41584fa33cc25cd3d`. Any other hash means the pack moved since this plan was written: stop and diff it against the Workshop copy before going on (`always-deploy-to-workshop-folder`).

- [ ] **Step 5: Import.** The path must be absolute.

Run: `py tools/import_victory_routes.py "G:\Modding for resources\Modding Files\Modpacks\!aa_derpy_hashut_legendary_lords.pack"`
Expected: six table lines with row counts, the script line, the dead-script deletions, `saved ...`. The duplicate-key check (`check_keys`) runs inside it and aborts on a finding.

- [ ] **Step 6: Verify the saved pack in a fresh session.**

Run: `py tools/import_victory_routes.py "G:\Modding for resources\Modding Files\Modpacks\!aa_derpy_hashut_legendary_lords.pack" --verify-only`
Expected: every fragment `ok ... rows round-tripped`, the script `ok`, all superseded copies gone, exit 0.

- [ ] **Step 7: Prove the shipped script is the new one, byte for byte.**

Run: `py -c "import sys; sys.path.insert(0,'tools'); import read_pack_index as r; P=r'Modding Files/Modpacks/!aa_derpy_hashut_legendary_lords.pack'; s=open(r'Modding Files/pack/script/campaign/mod/zzz_derpy_chd_victory_routes.lua','rb').read(); d=[d for p,c,d in r.read(P,'zzz_derpy_chd_victory_routes.lua')][0]; print(d==s, len(d), b'set_victory_mission_rewards_disabled(false)' in d, b'derpy_chd_route_achievement' in d)"`
Expected: `True <new size> True True`.

- [ ] **Step 8: Deploy to the Workshop folder.** Close the game first; `Warhammer3.exe` holds the pack open. (Git Bash)

```bash
tasklist | grep -i warhammer3 && echo "GAME RUNNING - close it first" || {
  W="/f/SteamLibrary/steamapps/workshop/content/1142710/3432966208/!aa_derpy_hashut_legendary_lords.pack"
  cp "Modding Files/Modpacks/!aa_derpy_hashut_legendary_lords.pack" "$W"
  md5sum "Modding Files/Modpacks/!aa_derpy_hashut_legendary_lords.pack" "$W"; }
```

Expected: two identical hashes, neither `153d0ae8...`. Do not copy it into `data/`. Do not upload: that is a separate step that needs the user's say-so.

- [ ] **Step 9: Hand the user the in-game list** (spec section 5), new IE or IEE campaign as the Black Dwarf or Abnagg:
  1. The script log shows `derpy_chd_victory_routes: victory mission rewards switched back on` on the first tick.
  2. The first route to complete pays its purse and trophy: the treasury or pooled resource moves by the amount the panel's Reward box showed, and the item appears in the faction's pool.
  3. A quest still pays when it completes (Review Focus 4).
  4. The Victory tab opens on one of our routes, not a vanilla node. If it does not, phase 2 builds VCO's click fix.

---

### Task 4: Docs

**Files:**
- Modify: `docs/VICTORY_CONDITIONS.md` (section 10, the bullet at lines 510-516; section 12, after the "disable guard" paragraph near line 871; the Checks paragraph near line 916)
- Modify: `docs/SESSION_INDEX.md` (one new line at the top of the list, line 3)
- Modify: `docs/MY_MODS.md` (the lords pack row, line 62)
- Check: `tools/README.md` via `py tools/gen_tools_index.py --check`

- [ ] **Step 1: Close the open 9.0 item.** In `docs/VICTORY_CONDITIONS.md`, replace the whole bullet that begins `- **9.0 may withhold every victory payload in a new Immortal Empires or IEE campaign. Open.**` (through `...has not been seen in game (`sessions/HANDOFF_20260924_UPDATE_9_0_COMPAT_AUDIT.md` §3-§4).`) with

```markdown
- **9.0 withholds every victory payload in a new Immortal Empires or IEE campaign, ours
  included, unless something switches it back.** `_victory_objectives_ie:add_scripted_victory_listeners()`
  calls `cm:set_victory_mission_rewards_disabled(true)` on every load once
  `IEVictoryConditionUseDLC29Config` is set, commented "Victory mission payload will not be
  granted to player": CA pays its own factions through a Victory Achieved incident instead.
  The call is undocumented and campaign-wide. VCO's `vco-disable-ca-wincons.lua` calls it with
  `false` after CA's setup ("Override the global flag that broke VCO rewards"), which is the
  evidence it bites mission-string routes too. Since 2026-10-11 our routes do the same from a
  post-first-tick callback, only when a human is one of our houses. Section 12c.
```

- [ ] **Step 2: Document the two listeners.** Directly after the paragraph that begins `The disable guard is \`ROUTES[faction_key]\`` in section 12, add

```markdown
### 12c. Rewards under 9.0, and the victory achievement (2026-10-11)

Two listeners in the same generated file, both registered on every load so running saves get
them too. Spec: `superpowers/specs/2026-10-11-victory-routes-vco-parity-design.md`.

* **The reward switch.** A `cm:add_post_first_tick_callback` calls
  `cm:set_victory_mission_rewards_disabled(false)` in single-player when a human faction has
  routes. CA's `true` comes from the shared first-tick list (wh_start.lua,
  `start_game_all_factions`), and `process_first_tick_callbacks` runs the post list after it,
  so ours lands last. A CA faction's player is left alone and keeps CA's incident rewards.
  Wrapped in `pcall`: a throw in the post list would take every later post callback with it.
* **The achievement.** CA awards `WH3_ACHIEVEMENT_WINNING_CHAOS_DWARFS_1`, and `_2` above
  difficulty 3, only on `wh_main_long_victory`. A `MissionSucceeded` listener on our five route
  keys reuses CA's `award_achievement_to_faction` and `wh3_campaign_achievements.long_victory`,
  as VCO's safety unlock does, and logs instead of throwing when that script is absent.

`--selftest` runs both through the stubbed campaign and carries seven Lua mutants, one per
guard line, each of which the matching check must kill.
```

- [ ] **Step 3: One SESSION_INDEX line.** Insert as the new first list item of `docs/SESSION_INDEX.md` (above the `- Stale-doc refresh, 2026-10-09` line):

```markdown
- [Victory routes at VCO quality, phase 1 of 5, 2026-10-11](superpowers/specs/2026-10-11-victory-routes-vco-parity-design.md): VCO (2026-10-09 build) compared route by route; phase 1 switches CA's 9.0 `set_victory_mission_rewards_disabled` back off for our houses (route purses and trophies were withheld in new IE/IEE games) and awards the Chaos Dwarf victory achievement on a route win; selftest with 7 Lua mutants; deployed to the Workshop folder, not uploaded. Phases 2-5 (lore text and Uzkul's routes, bespoke rewards, named objectives, story beats) each get their own spec.
```

- [ ] **Step 4: One clause in MY_MODS.** In the lords pack row of `docs/MY_MODS.md`, append before the closing ` |` of that cell:

```markdown
 **Since 2026-10-11 the victory routes pay under 9.0 and award the victory achievement** (`gen_victory_routes.py`, VICTORY_CONDITIONS.md 12c); deployed to the Workshop folder, not uploaded.
```

- [ ] **Step 5: Dash check and tools index.**

Run: `py -c "import sys; [print(f, open(f, encoding='utf-8').read().count(chr(0x2014))) for f in sys.argv[1:]]" docs/superpowers/plans/2026-10-11-victory-routes-vco-parity-phase1.md docs/superpowers/specs/2026-10-11-victory-routes-vco-parity-design.md`
Expected: both `0`. (The older docs carry em dashes of their own; this checks only what this phase wrote, plus a manual read of the four inserted blocks above.)
Run: `py tools/gen_tools_index.py --check`
Expected: exit 0. On exit 1, run `py tools/gen_tools_index.py` and re-check.
