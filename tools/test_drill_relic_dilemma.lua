-- Runs the SHIPPED derpy_chd_drill_chain.lua under Lua 5.1 against a stubbed campaign and
-- checks the relic dilemma end to end.
--
--     & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\test_drill_relic_dilemma.lua
--
-- What it protects, in the order the bugs would bite:
--   * the dilemma is OFFERED at all, and under the key that exists - the three majors fight
--     CA's _ie quest battles and `dilemmas` has no _ie rows, so an unstripped key is a silent
--     no-op for exactly those three;
--   * the script does NOT also pay the reward - the DB payload does, and paying twice was the
--     old behaviour;
--   * four bound relics issue the final battle, which is the whole point of the chain;
--   * the choice listener's condition REJECTS anything that is not one of the eight vanilla
--     relic dilemmas. Matching a cm:create_dilemma_builder dilemma hard-crashes the game and
--     bricks the save, and this mod ships four of those.

local SCRIPT = "Modding Files/pack/script/campaign/cr_combi_expanded/mod/derpy_chd_drill_chain.lua"

local MORGRIM = "wh3_dlc23_chd_ancestor_relic_of_morgrim"
local GRIMNIR_IE = "wh3_dlc23_chd_ancestor_relic_of_grimnir_ie"
local FACTION = "wh3_dlc23_chd_conclave"

local saved, calls, listeners, first_tick = {}, {}, {}, nil

local function record(what)
	table.insert(calls, what)
end

local function took(what)
	for i = 1, #calls do
		if calls[i] == what then
			return true
		end
	end
	return false
end

local function any(prefix)
	for i = 1, #calls do
		if calls[i]:sub(1, #prefix) == prefix then
			return calls[i]
		end
	end
	return nil
end

cm = {
	add_first_tick_callback = function(_, fn) first_tick = fn end,
	add_loading_game_callback = function() end,
	callback = function() end,
	get_saved_value = function(_, k) return saved[k] end,
	set_saved_value = function(_, k, v) saved[k] = v end,
	get_faction = function(_, key)
		return { is_null_interface = function() return false end,
		         name = function() return key end }
	end,
	trigger_dilemma_raw = function(_, faction, key)
		record("dilemma:" .. faction .. ":" .. key)
		return true
	end,
	trigger_mission = function(_, faction, key) record("mission:" .. faction .. ":" .. key) end,
	trigger_incident = function(_, faction, key) record("incident:" .. key) end,
	apply_effect_bundle = function(_, key) record("bundle:" .. key) end,
	add_ancillary_to_faction = function(_, _, anc) record("ancillary:" .. anc) end,
	faction_add_pooled_resource = function(_, _, _, _, amount)
		record("influence:" .. tostring(amount))
	end,
	remove_scripted_composite_scene = function() end,
	add_scripted_composite_scene_to_logical_position = function() end,
	model = function() return { world = function() return {} end } end,
}
core = {
	add_listener = function(_, name, event, cond, handler)
		listeners[name] = { event = event, cond = cond, handler = handler }
	end,
	svr_save_string = function(_, k, v) record("svr:" .. k .. "=" .. v) end,
}
out = function() end
common = { set_context_value = function() end }

assert(loadfile(SCRIPT), "the shipped script does not load")()
assert(first_tick, "no first tick callback registered")
first_tick()

local won = listeners["derpy_drill_relic_claimed"]
local answered = listeners["derpy_drill_relic_dilemma"]
assert(won, "no relic MissionSucceeded listener")
assert(answered, "no relic dilemma listener")
assert(answered.event == "DilemmaChoiceMadeEvent", answered.event)

local function mission_context(key)
	return {
		faction = function() return { name = function() return FACTION end } end,
		mission = function() return { mission_record_key = function() return key end } end,
	}
end

local function dilemma_context(key, choice)
	return {
		dilemma = function() return key end,
		choice = function() return choice end,
		faction = function() return { name = function() return FACTION end } end,
	}
end

-- THE CONDITION IS THE SAFETY CHECK. A builder dilemma must not match, or the click crashes.
assert(answered.cond(dilemma_context(MORGRIM, 0)) == true, "our own dilemma is not matched")
for _, foreign in ipairs({ "derpy_chd_commission_binding", "derpy_chd_commission_spoils",
                           "wh3_main_dilemma_something_else", "" }) do
	assert(answered.cond(dilemma_context(foreign, 0)) ~= true,
		"condition matched a dilemma that is not ours: " .. foreign)
end
-- and it must survive a context that throws rather than taking the dispatch down
assert(answered.cond({ dilemma = function() error("boom") end }) ~= true,
	"a throwing context was not handled")

-- A relic this chain never issued is left to its own payload.
calls = {}
won.handler(mission_context(MORGRIM))
assert(#calls == 0, "acted on a relic this chain did not issue: " .. table.concat(calls, ","))

-- Winning an issued relic OFFERS the dilemma and pays nothing.
saved["derpy_drill_issued_" .. MORGRIM] = true
calls = {}
won.handler(mission_context(MORGRIM))
assert(took("dilemma:" .. FACTION .. ":" .. MORGRIM), "no dilemma: " .. table.concat(calls, ","))
assert(not any("ancillary:"), "the script paid the relic as well as asking")
assert(not any("influence:"), "the script paid influence as well as asking")

-- The _ie majors must ask under the key that EXISTS - dilemmas has no _ie rows.
saved["derpy_drill_issued_" .. GRIMNIR_IE] = true
calls = {}
won.handler(mission_context(GRIMNIR_IE))
assert(took("dilemma:" .. FACTION .. ":wh3_dlc23_chd_ancestor_relic_of_grimnir"),
	"the _ie suffix was not stripped: " .. table.concat(calls, ","))

-- "Use for the Drill" counts it and pays nothing; the DB payload already did.
calls = {}
answered.handler(dilemma_context(MORGRIM, 0))
assert(saved["derpy_drill_relics"] == 1, tostring(saved["derpy_drill_relics"]))
assert(saved["derpy_drill_claimed_" .. MORGRIM] == true)
assert(not any("ancillary:"), "bind paid an ancillary")

-- Answering twice must not count twice.
answered.handler(dilemma_context(MORGRIM, 0))
assert(saved["derpy_drill_relics"] == 1, "a repeated answer counted twice")

-- "Claim for Yourself" does not count toward the drill, and pays nothing either.
calls = {}
answered.handler(dilemma_context("wh3_dlc23_chd_ancestor_relic_of_grimnir", 1))
assert(saved["derpy_drill_relics"] == 1, "keeping a relic advanced the drill")
assert(saved["derpy_drill_kept"] == 1, tostring(saved["derpy_drill_kept"]))
assert(not any("ancillary:"), "keep paid an ancillary on top of the DB payload")

-- The fourth bound relic issues the final battle.
saved["derpy_drill_relics"] = 3
calls = {}
answered.handler(dilemma_context("wh3_dlc23_chd_ancestor_relic_of_thungni", 0))
assert(saved["derpy_drill_relics"] == 4)
assert(took("mission:" .. FACTION .. ":wh3_dlc23_chd_final_battle_derpy_" .. FACTION),
	"no final battle: " .. table.concat(calls, ","))

-- With the drill full there is nothing left to ask: the rest are kept, and paid by hand
-- because no dilemma fires to pay them.
saved["derpy_drill_issued_wh3_dlc23_chd_ancestor_relic_of_gazul"] = true
calls = {}
won.handler(mission_context("wh3_dlc23_chd_ancestor_relic_of_gazul"))
assert(not any("dilemma:"), "asked with the drill already full")
assert(took("ancillary:wh3_dlc23_anc_weapon_lesser_relic_of_gazul"),
	"the kept relic was never handed over: " .. table.concat(calls, ","))
assert(took("influence:75"), "no influence for the kept relic")

-- And the mirror: four kept and the rest bind, with the reward_a bundle applied by hand.
saved = { ["derpy_drill_issued_wh3_dlc23_chd_ancestor_relic_of_smednir"] = true,
          ["derpy_drill_kept"] = 4 }
calls = {}
won.handler(mission_context("wh3_dlc23_chd_ancestor_relic_of_smednir"))
assert(not any("dilemma:"), "asked with the house already full")
assert(took("bundle:wh3_dlc23_chd_ancestor_relic_of_smednir_reward_a"),
	"no reward_a bundle: " .. table.concat(calls, ","))
assert(saved["derpy_drill_relics"] == 1, "the forced bind did not count")

-- A dilemma that refuses to fire must still settle the relic, or the drill can never finish.
cm.trigger_dilemma_raw = function() return false end
saved = { ["derpy_drill_issued_" .. MORGRIM] = true }
calls = {}
won.handler(mission_context(MORGRIM))
assert(saved["derpy_drill_relics"] == 1, "a refused dilemma lost the relic")
assert(took("ancillary:wh3_dlc23_anc_enchanted_item_lesser_relic_of_morgrim"),
	"a refused dilemma paid nothing: " .. table.concat(calls, ","))

print("ok - drill relic dilemma")
