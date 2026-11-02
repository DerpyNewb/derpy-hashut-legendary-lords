# Changelog

## 2026-11-02

- Victory routes: a Tower route asks for one more annex ritual than the seats it names, because the house's own seat is claimed for it on turn one and counts. `check()` refuses an own-group total under 2. Tordrek's and Khorakk's influence goal 60 to 150.
- `gen_new_house_lords.py`: `check_annex_lua()` fails on a `RitualStartedEvent` listener in the annex script (it crashed the game on a tier-four seat claim), and the start-army check reads lists wrapped in `derpy_hll_units(...)` again, so the selftest passes.
- Every RPFM-facing tool moved to the RPFM 5.3 API through `rpfm_client.py`.
- Hell-Forge doc: the shared layout script and the Houses card.

## 2026-10-11

- First public version: 38 tools, two Lua test harnesses and the docs they cite.
- Victory routes phase 2: a lore paragraph opens every route, explainers above Tower and Hell-Forge rituals, three routes for the Uzkul Mingol (46 routes, 13 houses).
