# Hashut's Legendary Lords: the tools

The build and audit tools behind **Hashut's Legendary Lords**, a Chaos Dwarf campaign mod for
**Total War: WARHAMMER III** ([Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3432966208)).

The mod gives the Chaos Dwarf houses legendary lords of their own: skill trees, traits, items,
mounts, missions and starting armies, plus new factions and flags. It adds a fifth tier to the
Tower of Zharr, "The Subjugation", where computer-controlled houses claim and usurp seats,
the player's included. Abnagg's and Tordrek's ships are naval hordes with their own build
queue and recruitment. Each of the 13 houses has three to five alternative victory routes, 46
in all. A Mod Configuration Tool page switches lords on and off.

The pack holds 152 database tables and 77 Lua scripts (counted 2026-10-11). The Python tools
here generate many of those tables, their localisation and several of the scripts. They import
the output into the pack through RPFM, then read the saved pack back to check what actually
shipped.

## What is here

This repository holds the tools only, not the mod. The mod is the `.pack` on the Workshop.

- `tools/`: 38 Python tools (about 17,000 lines) and two Lua test harnesses.
- `docs/`: four reference docs (victory conditions, missions, the Tower of Zharr's seats,
  Hell-Forge unit caps).
- `docs/design/` and `docs/plans/`: the specs and plans for the victory routes and Kharkadon.
- `docs/history/`: the working notes written as each part was built.

The tools resolve paths relative to the author's workspace (`tools/`, `Modding Files/...`),
and this repository keeps that layout.

## The tools

**Victory routes.** `gen_victory_routes.py` defines every route in one Python table and
generates the database rows, the text and the one Lua script that issues the routes as mission
strings. Every route opens with a paragraph in its house's voice, and every Tower or Hell-Forge
ritual objective has a one-line explainer. `import_victory_routes.py` pushes the output into
the pack and verifies the saved file in a fresh RPFM session.

**New lords.** `gen_new_house_lords.py` builds two lords from one table: Kharkadon, Overlord
of Zharrduk, and the Captain of the Uzkul Mingol. That covers skill trees, traits, items,
Subjugation seats, start scripts and portraits. `gen_zochaz.py` adds a lord with no faction of
his own. `gen_new_lords_cb.py` gives them custom battle entries, and
`gen_kharkadon_bodyguards.py` gives Kharkadon four bodyguard options. Portraits and seat art
come from `gen_portrait_settings.py`, `gen_character_portrait.py` and
`make_toz_seat_banner.py`. Their art comes from in-game screenshots and the game's own files,
so none of it is published here.

**The naval horde.** `gen_naval_horde_units.py`, `_phase6.py`, `_admiral.py` and
`_tordrek.py` build the ships' build queue, roster, heroes and Tordrek's separate Vampire
Coast roster. `import_naval_horde.py` pushes them into the pack. `gen_tordrek_vc_skills.py`
adds his Vampire Coast skill nodes.

**Missions and balance.** `gen_hellshard_missions.py` repairs the hellshard missions, and
`gen_ll_ai_strength.py` raises the lords to the vanilla legendary-lord stat floor.
`gen_ghorth_settlement_tiers.py` is stale and says so at its top.

**Audits.**

- `check_skill_trees.py`: dangling keys, unreachable nodes, two nodes on one cell, missing text.
- `check_effect_signs.py`: effects whose sign makes them a penalty.
- `check_effect_bundle_loc.py`: effect bundles with no title text.
- `check_hll_settings.py`: the MCT page against the script that reads it.
- `check_lua_api.py`, `check_lua_undeclared.py`, `check_lua_literal_left.py`: calls CA does
  not document, globals nothing declares, and a miscompile in the game's Lua.

The rest are readers that decode CA's database, `.pack` and `.animpack` files without RPFM,
plus the RPFM client.

## How it is tested

There is no test framework. Twenty of the tools carry a `--selftest`, and the generators check
their output before writing it.

- **The shipped Lua runs.** `gen_victory_routes.py --selftest` runs the generated script
  under Lua 5.1.5 against a stubbed campaign. It replays turn starts and loads, and reads back
  every mission issued and every objective completed.
- **Every guard is proven.** 13 mutants each break one line of that script and must be caught.
  33 deliberate breaks must each be reported by `--check`.
- **The two Lua harnesses.** `test_drill_relic_dilemma.lua` and `test_naval_confed_stances.lua`
  run shipped scripts the same way.
- **The pack, not the plan.** `import_victory_routes.py --verify-only` re-opens the saved pack
  in a fresh RPFM session and round-trips every table back out, because a file merely present
  in a pack proves nothing about whether it decodes.

## Running it

You need Python 3 with Pillow, numpy, zstandard, lz4 and openpyxl, and Lua 5.1.5. Imports need
[RPFM](https://github.com/Frodo45127/rpfm) open with its MCP server. Many tools also read your
own Total War: WARHAMMER III install; the paths are at the top of `tools/read_vanilla_db.py` and
the other readers.

These self-tests pass from a fresh clone, with the game installed:

```text
py tools/check_effect_bundle_loc.py --selftest
py tools/check_effect_signs.py --selftest
py tools/check_lua_literal_left.py --selftest
py tools/check_lua_undeclared.py --selftest
py tools/gen_commodity_icons.py --selftest
py tools/gen_tordrek_vc_skills.py --selftest
py tools/patch_army_banner.py --selftest
py tools/read_vanilla_db.py --selftest
py tools/sync_guilds_repo.py --selftest
py tools/sync_hll_repo.py --selftest
```

The rest need inputs that are not published:

- the mod's own staged scripts and tables (the generators cross-check against them);
- a cache of vanilla tables built by `tools/fetch_vanilla_tables.py`;
- CA's scripting documentation from the Assembly Kit, for `check_lua_api.py`.

## Licence and legal

The code and documentation in this repository are released under the
[MIT License](LICENSE).

This is an unofficial, fan-made mod. It is not made, endorsed or supported by Games
Workshop, Creative Assembly or SEGA.

- **No game files or assets are included.** The repository contains no art, models, sounds
  or game data files from Total War: WARHAMMER III. The tools read the game's own data from
  your install, and you need your own copy of the game to use them.
- Warhammer and the names, places and characters of the Warhammer world are trademarks
  and/or copyright of Games Workshop Limited. Total War and Total War: WARHAMMER are
  trademarks and/or copyright of The Creative Assembly Limited and SEGA. All are used here for
  identification only.
- The MIT License covers only the original work in this repository. It grants no rights in
  any Games Workshop, Creative Assembly or SEGA property.
