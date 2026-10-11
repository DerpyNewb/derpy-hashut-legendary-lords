-- Runs the SHIPPED derpy_chd_naval_admiral.lua under Lua 5.1 against a stubbed campaign and
-- checks the confederation stance restore.
--
--     & "C:\Program Files (x86)\Lua\5.1\lua.exe" tools\test_naval_confed_stances.lua
--
-- The thing it protects: a Tower of Zharr seat claim destroys the house faction, so the lord
-- trait bundle carrying SETTLE / SEA_RAID / ASSEMBLE_FLEET has to be re-applied to whoever
-- took him, exactly once, and never to a faction that is not holding him.

local SCRIPT = "Modding Files/pack/script/campaign/cr_combi_expanded/mod/derpy_chd_naval_admiral.lua"

local applied, world, first_tick, listeners = {}, {}, nil, {}

local function faction(name, subculture, bundles, subtypes)
	local f = {}
	f.name = function() return name end
	f.subculture = function() return subculture end
	f.has_effect_bundle = function(_, key) return bundles[key] == true end
	f.character_list = function()
		local chars = {}
		for _, st in ipairs(subtypes) do
			table.insert(chars, {
				character_subtype_key = function() return st end,
				is_null_interface = function() return false end,
			})
		end
		return {
			num_items = function() return #chars end,
			item_at = function(_, i) return chars[i + 1] end,
		}
	end
	f._bundles = bundles
	return f
end

world = {
	faction_list = function()
		return {
			num_items = function() return #world._list end,
			item_at = function(_, i) return world._list[i + 1] end,
		}
	end,
}

cm = {
	add_first_tick_callback = function(_, fn) first_tick = fn end,
	apply_effect_bundle = function(_, bundle, faction_key, turns)
		table.insert(applied, bundle .. "|" .. faction_key .. "|" .. tostring(turns))
	end,
	model = function() return { world = function() return world end } end,
	callback = function() end,
	get_character_by_cqi = function() return nil end,
	add_building_to_force = function() end,
}
core = { add_listener = function(_, name, _event, _cond, handler) listeners[name] = handler end }
out = function() end

local chunk = assert(loadfile(SCRIPT))
chunk()

assert(first_tick, "no first tick callback registered")
assert(listeners["derpy_chd_naval_traits_confed"], "no confederation listener")
assert(listeners["derpy_chd_naval_traits_spawned"], "no spawn listener")

-- The world after a Tower of Zharr claim: the player holds Abnagg and Tordrek and has neither
-- bundle; the dead houses hold nothing; a Vampire Coast faction holds a lord of the same NAME
-- but is not Chaos Dwarf; and a Chaos Dwarf faction that already has a bundle is left alone.
world._list = {
	faction("wh3_dlc23_chd_astragoth", "wh3_dlc23_sc_chd_chaos_dwarfs", {},
		{ "derpy_abnagg", "derpy_tordrek", "wh3_dlc23_chd_sorcerer_prophet" }),
	faction("cr_chd_warfleet_of_uzkulak", "wh3_dlc23_sc_chd_chaos_dwarfs", {}, {}),
	faction("wh2_dlc11_cst_pirates_of_sartosa", "wh2_dlc11_sc_cst_vampire_coast", {},
		{ "derpy_abnagg" }),
	faction("cr_chd_house_of_bzaark", "wh3_dlc23_sc_chd_chaos_dwarfs",
		{ derpy_tordrek_lord_trait = true }, { "derpy_tordrek" }),
}

first_tick()

table.sort(applied)
local got = table.concat(applied, "\n")
local want = table.concat({
	"derpy_abnagg_lord_trait|wh3_dlc23_chd_astragoth|0",
	"derpy_tordrek_lord_trait|wh3_dlc23_chd_astragoth|0",
}, "\n")
assert(got == want, "first tick applied:\n" .. got .. "\nwanted:\n" .. want)

-- Idempotent: the same sweep from the confederation listener must add nothing, because the
-- stub reports the bundles as still absent only where they were never applied.
world._list[1]._bundles.derpy_abnagg_lord_trait = true
world._list[1]._bundles.derpy_tordrek_lord_trait = true
applied = {}
listeners["derpy_chd_naval_traits_confed"]({})
assert(#applied == 0, "re-applied a bundle the faction already held: " .. table.concat(applied, ","))

-- The spawn route: a seat claim in Immortal Empires creates Tordrek instead of confederating.
world._list[2]._bundles = {}
world._list[2].has_effect_bundle = function() return false end
world._list[2].character_list = function()
	local ch = { character_subtype_key = function() return "derpy_tordrek" end,
	             is_null_interface = function() return false end }
	return { num_items = function() return 1 end, item_at = function() return ch end }
end
applied = {}
listeners["derpy_chd_naval_traits_spawned"]({
	character = function()
		return { is_null_interface = function() return false end,
		         character_subtype_key = function() return "derpy_tordrek" end }
	end,
})
assert(#applied == 1 and applied[1] == "derpy_tordrek_lord_trait|cr_chd_warfleet_of_uzkulak|0",
	"spawn route applied: " .. table.concat(applied, ","))

-- A character that is not one of the two must not trigger the sweep at all.
applied = {}
listeners["derpy_chd_naval_traits_spawned"]({
	character = function()
		return { is_null_interface = function() return false end,
		         character_subtype_key = function() return "derpy_chd_admiral" end }
	end,
})
assert(#applied == 0, "swept on an unrelated character")

print("ok - naval confederation stance restore")
