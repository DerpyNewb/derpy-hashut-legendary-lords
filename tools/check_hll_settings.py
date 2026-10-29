# -*- coding: utf-8 -*-
"""Run the Hashut Legendary Lords MCT settings under Lua 5.1.5 and assert they behave.

    py tools\\check_hll_settings.py

Two files hold the settings and cannot see each other in game: script/mct/settings/derpy_hll.lua
registers the MCT page in MCT's environment, script/campaign/mod/derpy_hll_settings.lua reads it
in the campaign's. A key or default that differs between them reads the default forever with no
error anywhere, so this runs the page against a recording MCT stub and compares, then drives the
reader through no-MCT, MCT, wrong-type, multiplayer and the save freeze, and runs one real start
script with its lord switched off - and on, with the local-faction reads throwing as they do in
multiplayer, asserting his hero is still placed (derpy_hll_start_hero). Last, every start army
wrapped in derpy_hll_units must drop all other-mod units when their packs are absent and keep
them when present. Exit 1 on a failure.
"""
import os, re, subprocess, sys, tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Modding Files", "pack", "script")
PAGE = os.path.join(ROOT, "mct", "settings", "derpy_hll.lua")
READER = os.path.join(ROOT, "campaign", "mod", "derpy_hll_settings.lua")
START = os.path.join(ROOT, "campaign", "cr_oldworld", "mod", "derpy_start_azeros.lua")
LUA = r"C:\Program Files (x86)\Lua\5.1\lua.exe"

HARNESS = r'''
local PAGE, READER, START, LISTS = ...
local fails = 0
local function check(cond, msg)
    if not cond then fails = fails + 1; print("FAIL " .. msg) end
end
function out(s) end

-- A recording MCT: the page registers into `opts`, the reader reads `values` back out.
local opts, values = {}, {}
local function option(key)
    local o = {key = key}
    function o:set_default_value(v) opts[key] = v end
    function o:get_finalized_setting() return values[key] end
    setmetatable(o, {__index = function() return function() end end})
    return o
end
local mod = setmetatable({}, {__index = function() return function() end end})
function mod:add_new_option(key) return option(key) end
function mod:get_option_by_key(key) return option(key) end
local mct = setmetatable({}, {__index = function() return function() end end})
function mct:register_mod() return mod end
function mct:get_mod_by_key(k) if k == "derpy_hll" then return mod end end
function get_mct() return mct end
dofile(PAGE)

-- The campaign side.
local saved, mp = {}, false
cm = {}
function cm:is_multiplayer() return mp end
function cm:get_saved_value(k) return saved[k] end
function cm:set_saved_value(k, v) saved[k] = v end
dofile(READER)

-- 1. Page and defaults agree, both ways.
local n = 0
for k, v in pairs(DERPY_HLL_DEFAULTS) do
    n = n + 1
    check(opts[k] ~= nil, "default " .. k .. " has no MCT option")
    check(opts[k] == nil or opts[k] == v,
        "default " .. k .. " = " .. tostring(v) .. " but the page says " .. tostring(opts[k]))
end
for k in pairs(opts) do
    check(DERPY_HLL_DEFAULTS[k] ~= nil, "MCT option " .. k .. " is never read")
end

-- 2. Nothing set in MCT reads the default.
check(derpy_hll_setting("toz_ai_claim_chance") == 25, "unset slider is not its default")

-- 3. MCT is honoured, live.
values.toz_ai_claim_chance = 60
check(derpy_hll_setting("toz_ai_claim_chance") == 60, "MCT slider value ignored")
values.toz_ai_claims = false
check(derpy_hll_setting("toz_ai_claims") == false, "MCT checkbox false ignored")

-- 4. A wrong-typed value is the default.
values.toz_ai_start_turn = "12"
check(derpy_hll_setting("toz_ai_start_turn") == 10, "string accepted for a slider")

-- 5. Multiplayer ignores MCT.
mp = true
check(derpy_hll_setting("toz_ai_claim_chance") == 25, "multiplayer read MCT")
mp = false

-- 6. A lord switch freezes at its first read.
values.lord_derpy_azeros = false
check(derpy_hll_setting("lord_derpy_azeros") == false, "lord switch off not read")
check(saved.derpy_hll_lord_derpy_azeros == false, "lord switch not written to the save")
values.lord_derpy_azeros = true
check(derpy_hll_setting("lord_derpy_azeros") == false, "lord switch followed MCT after freezing")

-- 7. The real start script does nothing for a lord switched off, and runs for one switched on.
local registered
function cm:add_first_tick_callback_new(f) registered = f end
local ran, real_replace = false
local function load_start()
    dofile(START)
    real_replace = derpy_azeros_replace_1
    derpy_azeros_replace_1 = function() ran = true end
end
load_start()
registered()
check(ran == false, "azeros start ran with his switch off")
saved.derpy_hll_lord_derpy_azeros = true
registered()
check(ran == true, "azeros start did not run with his switch on")

-- 8. The real start places his hero for the house whoever plays it. The local-faction reads
--    throw here, as they do in multiplayer, so a start that still leans on one fails this.
local function noop() end
local function stub(t) return setmetatable(t, {__index = function() return noop end}) end
local leader = stub({})
function leader:is_null_interface() return false end
function leader:logical_position_x() return 10 end
function leader:logical_position_y() return 20 end
local faction = stub({})
function faction:is_null_interface() return false end
function faction:faction_leader() return leader end
model_pairs = function() return noop end
setmetatable(cm, {__index = function() return noop end})
function cm:get_faction() return faction end
function cm:get_local_faction_name() error("local faction read") end
function cm:get_local_faction() error("local faction read") end
local spawn_x, created = 11, {}
function cm:find_valid_spawn_location_for_character_from_position() return spawn_x, 21 end
function cm:create_agent(f, t, s, x, y) created[#created + 1] = table.concat({f, t, s, x, y}, " ") end
local loaded, army = {}
common = {vfs_exists = function(p) return loaded[p] == true end}
function cm:create_force_with_general(f, units) army = units end
local ok, err = pcall(real_replace)
check(ok, "azeros start threw: " .. tostring(err))
check(created[1] == "cr_chd_house_of_azeros engineer wh3_dlc23_chd_infernal_castellan 11 21" and #created == 1,
    "azeros hero not placed as before: " .. tostring(created[1]))
check(army and not army:find("chd_turtle_tank_carrier") and army:find("^wh3_dlc23_chd_veh_iron_daemon,"),
    "azeros spawned other-mod units with their mod absent: " .. tostring(army))

-- 9. derpy_hll_units: with neither unit pack loaded, no start list keeps a chd_ unit (every
--    other-mod key is chd_, every vanilla one wh3_); with both loaded, every list is unchanged.
for list in LISTS:gmatch("[^;]+") do
    local bare = derpy_hll_units(list)
    check(not ("," .. bare):find(",chd_"), "an other-mod unit has no fallback: " .. bare)
end
loaded["script/campaign/mod/derpy_chd_units_mct.lua"] = true
loaded["script/campaign/mod/derpy_hashut_spears_mct.lua"] = true
for list in LISTS:gmatch("[^;]+") do
    check(derpy_hll_units(list) == list, "a list changed with both unit packs loaded: " .. list)
end
spawn_x, created = -1, {}
derpy_hll_start_hero("f", "engineer", "s")
check(#created == 0, "hero placed with no spawn point")
spawn_x = 11
function cm:create_agent() error("boom") end
check(pcall(derpy_hll_start_hero, "f", "engineer", "s"), "a failing create_agent escaped the hero's pcall")

print(n .. " settings, " .. fails .. " failure(s)")
os.exit(fails == 0 and 0 or 1)
'''


def start_lists():
    """Every unit list a start script passes through derpy_hll_units, joined by ';'."""
    out = []
    for d, _, files in os.walk(os.path.join(ROOT, "campaign")):
        for name in files:
            if name.endswith(".lua"):
                out += re.findall(r'derpy_hll_units\("([^"]+)"\)', open(os.path.join(d, name), encoding="utf-8").read())
    assert len(out) >= 16, "only %d wrapped start lists found" % len(out)
    return ";".join(out)


def main():
    fd, path = tempfile.mkstemp(suffix=".lua")
    os.close(fd)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(HARNESS)
    try:
        r = subprocess.run([LUA, path, PAGE, READER, START, start_lists()], capture_output=True, text=True)
    finally:
        os.remove(path)
    sys.stdout.write(r.stdout + r.stderr)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
