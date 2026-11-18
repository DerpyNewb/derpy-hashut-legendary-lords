# Changelog

## 2026-11-18

- `gen_kharkadon_bodyguards.py`: a bodyguard option now joins only Kharkadon's own two unit sets. It used to inherit its base unit's sets as well, which put him in every Chaos Dwarf infantry set, so infantry buffs listed him and CA's infantry techs applied to him. `check()` fails on any other set, and the selftest gained two breaks.
- `gen_new_house_lords.py` and `gen_victory_routes.py`: the Uzkul Mingol Company's lord is now Zhorgrath the Reaver, with a collaborator's bio, skill names and model, a new skill line and faction effects, and rewritten route texts.
- New `make_skullstack_flag.py`: the Uzkul Mingol Company's flag, drawn from a collaborator's design in CA's own style. `make_toz_seat_banner.py` lifts the Tower seat's device from it.
- `rpfm_mcp_bridge.py` is mirrored: the RPFM tools start `rpfm_server` themselves when the RPFM window is closed.
- Hell-Forge doc: the empty `unit_allowances.faction_set` gap is fixed.

## 2026-11-02

- Victory routes: a Tower route asks for one more annex ritual than the seats it names, because the house's own seat is claimed for it on turn one and counts. `check()` refuses an own-group total under 2. Tordrek's and Khorakk's influence goal 60 to 150.
- `gen_new_house_lords.py`: `check_annex_lua()` fails on a `RitualStartedEvent` listener in the annex script (it crashed the game on a tier-four seat claim), and the start-army check reads lists wrapped in `derpy_hll_units(...)` again, so the selftest passes.
- Every RPFM-facing tool moved to the RPFM 5.3 API through `rpfm_client.py`.
- Hell-Forge doc: the shared layout script and the Houses card.

## 2026-10-11

- First public version: 38 tools, two Lua test harnesses and the docs they cite.
- Victory routes phase 2: a lore paragraph opens every route, explainers above Tower and Hell-Forge rituals, three routes for the Uzkul Mingol (46 routes, 13 houses).
