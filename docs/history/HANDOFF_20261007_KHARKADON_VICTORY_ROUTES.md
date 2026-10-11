# Kharkadon's victory routes

2026-10-07. Asked: custom victory routes for Kharkadon (Overlords of Zharrduk,
`wh3_dlc23_chd_minor_faction`), designs proposed first. Approved as proposed (three routes), plus a
fourth by request: "killing or making extinct Grimgor's faction and the Dwarfs".

**Built in `Modding Files/Modpacks/` (md5 `2eabd80abef070cce777f168eefbc71c`), deployed to the
Workshop folder 2026-10-07 09:39 with the game shut** (destination was still `dd23116d`, md5 equal after copy; no
`data/` copy).
Not uploaded, not seen in game. Backup of the pre-edit pack and generated files:
`Modding Files/Backup/pre_kharkadon_victory_routes_20261007/`.

## Routes (`tools/gen_victory_routes.py`, `ROUTES["wh3_dlc23_chd_minor_faction"]`)

| | Route | Objectives |
|---|---|---|
| I | The Immortal Legions | 2x `military_chaos_dwarf_infantry_3` (the only Ironsworn building, vanilla `building_units_allowed`); 2x `HELLFORGE_CAPS_MELEE_INFANTRY`; 500 armaments |
| II | Lords of Zharrduk | 2 Bloodline (district A) annex seats; one character rank 25; 150 influence |
| III | Blood and Iron | destroy the Dwarfs, 35 armies, 20 sacks. **Gated on `cr_oldworld_region_zharr_naggrund`** (Old World, Dark Lands): destroy `cr_dwf_slaves_of_zharr` + `cr_ogr_slaves_of_zharr` (the two revolts the war start sets on him), 30 armies, 20 sacks |
| IV | The Extinction | one DESTROY_FACTION: `wh_main_grn_greenskins` (Grimgor) + `wh_main_dwf_dwarfs`, `confederation_valid` only - extinct, not vassalised |

Appended LAST in `ROUTES` so `HOUSES.index`-based purse/trophy rotation moves no other house.
His four draw purses 4/5/6/0 and trophies Chains of the Conquered, Horn-Blade, Ash-Veil Mantle,
Tyrant's Seal. `check()` now expects 12 houses; `ANNEX_GROUP` gained him (group A, ceiling 3).

New verified keys: the region (99 hits in the installed `!cr_oldworld_campaign.pack`, and the
probe the start script already uses) and both revolt factions (a `factions` row each in that
pack, two hits each in its `cr_oldworld/startpos.esf`). Grimgor and the Dwarfs are in that
startpos too. **Dark Lands is not installed here** - its keys are unverified, as for every other
house's ungated Dwarf/Greenskin target.

## Verification

`--check` and `--selftest` pass (43 routes, 12 houses; the selftest issues every house's routes
as a human and proves every gated route on and off its map, so his Route III is covered).
`luac -p`, `check_lua_api`, `check_lua_literal_left` clean. The pack's script matched the staged
copy byte for byte before import. `import_victory_routes.py --verify-only` round-trips all six
fragments. File diff vs backup: 583 files both, none added/removed; seven re-imported, decoded
rows unchanged except `victory_types` +4 (the other byte changes are the regenerated table
GUIDs).

## Open

- In game: the four nodes draw in the victory panel for Kharkadon; Route III picks the slave-revolt
  block on the Old World; whether his faction holds land at the start of plain IE (CA's endgame
  "Will of Hashut" invasion faction there).
