# Two new house lords - the Overlord of Zharrduk and the Captain of the Uzkul Mingol

2026-10-03. Pack: `!aa_derpy_hashut_legendary_lords.pack` (Workshop id 3432966208).
Asked: "prepare files for overlord of zharrduk and uzkal mingol company as additional new lords and
faction, using the overseer model for now". Answers given: existing factions, new lords; full house
parity; placeholder names; lords pack.

**Built, deployed to the Workshop folder, not uploaded, not run in game.** Current build
`1cd5c2ce584775625381a849f802bcd5`, 464 files (§11). §1 is the current state; §2-§5 describe the
first build and §7-§11 what changed after it.

## 1. What exists now

| | Overlords of Zharrduk | Uzkul Mingol Company |
|---|---|---|
| Faction | CA's `wh3_dlc23_chd_minor_faction` | IEE's `cr_chd_skullstack` |
| Campaigns | IE, IEE, Old World, Dark Lands | IEE and Old World only |
| Agent subtype | `derpy_zharrduk` | `derpy_uzkul` |
| Name | **Kharkadon the Vicious** - CA's own names, forename `names_name_212779775` + family name `names_name_318034614` (the minted `12412535` is purged) | Captain of the Uzkul Mingol (`names_name_12412536`, placeholder) |
| Starting hero, beside his army (not in it) | Bull Centaur (`champion`, `wh3_dlc23_chd_bull_centaur_taurruk`) | Daemonsmith Sorcerer, Lore of Metal (`wizard`, `wh3_dlc23_chd_daemonsmith_sorcerer_metal`) |
| Theme (since §8) | the Immortals (Infernal Ironsworn) and seasoned lords | a chartered expedition in Ind: convoys, trade, plunder |
| Subjugation seat | 11, Bloodline district since §10, swapped with Khorakk (`derpy_ritual_chd_toz_annex_zharrduk`) | 12, Forge district (`..._skullstack`) |
| Starting army (§9) | 8 elite: 2 Ironsworn, Infernal Guard, Fireglaives, Warriors with great weapons, Warriors, Blunderbusses, Bull Centaurs | 10: Warriors, Blunderbusses, 2 Cutthroats, 2 Archers, Sneaky Gits, 2 Wolf Raiders, Deathshrieker |
| Tower seat banner (§10-§11) | teal cloth (`008080`), red device (`C31515`) | khaki cloth (`989964`), dark brown stacked skulls (`44302A`) |
| Lord-select row | `mixer_ime_chd_minor_faction` (IE, through Mixer); since 2026-10-05 also `cr_oldworld_political_party_chd_minor_faction` (Old World - the OW mod's own row named a Sorcerer-Prophet, so lord select showed his Winds effects and no Faction effects) | `cr_political_party_combi_chd_skullstack` (IEE); since 2026-10-05 also `cr_oldworld_political_party_chd_skullstack` (OW's row named `mixer_dummy`) |
| Model | **his own since 2026-10-05**: `derpy_kharkadon` variantmesh (battle and campaign) and battle anim table `derpy_kharkadon` (= `derpy_kharkadon.bin` in the assets pack's `derpy_hu3_legendary_lords.animpack`); lord-select model too. Entity, campaign anim (`cam_hu3_dwarf_axe_and_shield`, same prop slots) and the 2D porthole stay CA's Overseer. Pack `c9de3843` | CA Overseer, `chd_overseer_campaign_02` |

Each lord has what Balur has: agent subtype, land/main unit, melee weapon, passive aura, lord trait
skill, faction trait bundle, unique line (`_1`, four 3-level middles `_2_1`..`_2_4`, the `_4_1`/`_4_2`
choice, the `_3` capstone), the shared character/combat/army/campaign lanes, weapon and talisman items
with their set, the defeat trait, custom-battle entry, MCT switch, AI tower membership and the usurp
incidents. Skill effects are in `SKILLS` / `TRAIT_BUNDLE` at the top of the generator, one table.

The Overlords already took part in the Tower (2026-09-25). Skullstack now does too: added to the IEE,
Old World and Dark Lands `tower_of_zharr.factions` lists, plus AI membership, incidents and the usurp
bundle cloned from the Fists of Hashut. Both factions were added to the Old World / Dark Lands
starting influence grant and to Mixer's major faction list.

## 2. How it is built - `tools/gen_new_house_lords.py`

Clones every row the pack holds for Balur and for the Fists of Hashut, keys swapped, then replaces the
model, the skill content and the seat order. Balur was the donor because he is already on the
Overseer's voice actor and is a plain melee lord. `--import` imports, saves, re-extracts the SAVED
pack and compares every fragment; `--selftest` proves each check fails on broken input.

Checks it runs on every build:

- every designed (effect, scope) pair occurs somewhere in vanilla or this pack. It caught seven on the
  first run: CA scopes most hobgoblin effects `character_to_force_own`, not `general_to_force_own`, and
  `wh3_dlc23_effect_armour_hobgoblins` / `..._attribute_enable_vanguard_deployment_hobgoblins` are used
  by nothing at all (the working vanguard key is `..._enable_attribute_vanguard_...`)
- no "Balur", "Baal" or "Fists" left in any cloned row; the lord has every core table row; the skill
  set has as many items as Balur's; the minted ids (art set row, ability unique id, names) are unused
  in CA's `db.pack` and in the pack
- the start script under Lua 5.1.5 against a stubbed campaign: inherits the army minus characters,
  skips an absent faction, obeys the MCT switch, falls back to a fixed army when the leader has none

A rebuild from the post-import extract reproduces all 85 fragments row for row, so a re-run replaces
its own rows. Rows are recognised as its own by `OWNED`; a clone whose combined key (RPFM's `is_key`,
read from `schema_wh3.ron`) is held by somebody else's row is dropped, which is what keeps the
Overlords' 2026-09-25 Tower rows and their hand-written loc.

**Renaming:** edit `LORDS` (and the item, set, passive and lore strings below it) and re-run with
`--import`. Then change the same two display names in `script/mct/settings/derpy_hll.lua`. Keys stay.

## 3. The start script - `script/campaign/mod/derpy_start_new_house_lords.lua`

One file for every campaign. The new lord spawns where the faction leader stands, with his own
fixed army since §9 (until then he took over the old leader's units), found next to the old leader with
`find_valid_spawn_location_for_character_from_position`; the old leader and his force are killed. No
coordinates, so a campaign that moves the faction needs no edit. New games only, behind
`derpy_hll_lord_on`, each lord in a pcall. Other lords and armies of the faction are left alone - unlike
the house start scripts, which kill every character because the mod owns those factions' start.

**2026-10-06, one exception:** a lord's optional `at` puts him on a fixed logical tile on one map.
Kharkadon has `at = { region = "cr_oldworld_region_zharr_naggrund", x = 1792, y = 1117 }`. The region
key is the map probe (`region_by_key` is null off the Old World map), so on the Old World and the Dark
Lands he spawns there. Everywhere else he still spawns beside the old leader. The search distance is 0,
so a valid tile is kept as given. The same day both Old World/Dark Lands `derpy_chd_ll_war_start.lua`
copies gained `cr_dwf_slaves_of_zharr` (Chained of Zharr) and `cr_ogr_slaves_of_zharr` (Thralls of Zharr)
declaring war on `wh3_dlc23_chd_minor_faction`. The slaves declare because the Conclave start may
already have made the Overlords its vassal. `check_start_script()` has an `oldworld` case for it.
Spliced into the pack without RPFM (the MCP server was down); backup in
`Modding Files/Backup/pre_kharkadon_spawn_20261006/`.

The hero is placed by `derpy_hll_start_hero` (§7), right after the force is created - beside the new
lord, not embedded, the same as every other house; it was embedded in the first build and changed at the
user's request. The Annex seat's
lord grant now passes `seat.surname` as the family name, so a Subjugation-granted Kharkadon is also
"the Vicious".

**Skullstack's `factions_tables` row ships in this pack** (`!!_cr_oldworld_new_factions`), IEE's row
copied out of IEE's pack. Four tables reference `cr_chd_skullstack` through `factions.key`, and the
engine refuses the whole pack at load on a reference no loaded pack defines - so without it a player
without IEE would have lost every lord. It is the same thing the pack already did for Uzkulak; the
generator proves its formatter by reproducing our Uzkulak row from IEE's data cell for cell, and
`check_faction_refs()` now fails the build on any faction reference CA or this pack does not define.
The Old World mod's own skullstack row was not available to compare; where our row wins over it, IEE's
values apply. The row's own outbound references all resolve without IEE: 12 resolve in CA's `db.pack`,
and the other four (`audio_voiceover_culture`, `movie_death_event`, `mp_force_gen_template`,
`pre_battle_speech_parameter`) target tables with no rows in `db.pack` and carry exactly the values
CA's own two Chaos Dwarf faction rows carry. No other installed pack ships the path
`db/factions_tables/!!_cr_oldworld_new_factions` (IEE's is `!cr_new_factions`), so nothing is shadowed
whole.

## 4. Not done - decide before upload

- **Placeholder names and art.** The lord-select picture is CA's Overseer porthole copied to
  `ui/portraits/faction_leaders/derpy_<lord>.png`; portholes are CA's Overseer blocks under our art
  set ids (`portrait_settings_derpy_hll_new_lords.bin`).
- **Lord-select row precedence: ours wins.** The 16:02 IEE frontend showed Abnagg with OUR
  `derpy_abnagg.png`, so our `cr_political_party_combi_chd_warfleet_of_uzkulak` row beats IEE's
  `mixer_dummy` row of the same key. The new rows use the same route (§6). Whether Mixer's
  `mixer_ime_chd_minor_faction` row loses to ours in IE as well is not yet seen.
- No Old World lord-select: neither faction has a political party there.
- Not built: victory routes (`tools/gen_victory_routes.py`), the Great Drill missions and set piece,
  house ancillaries / commissions, Iron Court, Great Guilds, Exchange entries. (Claimed-seat art: done,
  §10-§11.)
- Old saves: the seats appear on load, the start script does not run (new games only).
- Not seen in game. First test: start an IEE campaign, check the script log for
  `derpy_new_house_lords`, both leaders' skill trees, the porthole, and that the Subjugation tier
  shows the Overlords in Bloodline and the Company in Forge, each under its own banner.

## 5. Files

The first build; the current pack is in §11. Pack `f4ad7e0656fa7a45585b91b32b4e2c06` (deploys: `b5c6caea`, then `e2c7e878` with the leader-picture fix, §6, then this one with Kharkadon, the starting heroes and Skullstack's faction row; backups `.bak_preheroes_20261003`), 458 files (453 before: +2 portrait
settings, +2 leader pictures, +1 script). In Modpacks and the Workshop folder. Backups
`.bak_prenewlords_20261003` beside both (`9ec8d00d`, the uploaded build). 86 DB/loc fragments (85, plus Skullstack's factions row)
changed, 13 Lua files (4 annex copies, 3 tower lists, 2 influence grants, MCT page and reader, Mixer,
the new start script). `Modding Files/templates/toz_districts.py` now lists 12 seats.
`check_skill_trees.py`: 0 ERR; the four new WARNs are the four deliberate tier-4 downsides.
`check_effect_bundle_loc.py`: 70 bundles, 0 findings. `check_hll_settings.py`: 28 settings, 0 failures.

## 6. Frontend - how a faction gets onto the lord-select screen (IEE and IE, with Mixer)

Reported 2026-10-03 16:03 from an IEE screenshot: three CA lords plus the Black Dwarf, Ghorth and
Abnagg, and neither new faction. **Cause: the game was not running this build.** `workshop_log.txt`
shows the lords item unsubscribed and resubscribed at 16:00:41 and the published build `9ec8d00d`
downloaded at 16:00:45, over the 15:59 deploy, before the game started at 16:02. Redeployed
(`e2c7e878`). Not yet seen in game.

What has to be true for a card to show, read from Mixer's `ui/frontend ui/campaign_select_new.twui.xml`
and the packs' scripts:

1. The campaign's `startpos.esf` carries a political party for the faction. IEE's `cr_combi_expanded`
   startpos has `cr_political_party_combi_chd_skullstack` and `mixer_ime_chd_minor_faction` (it ships
   IE's startpos too, with the same keys). Old World has neither, hence no lord-select there.
2. A `frontend_faction_leaders` row of that key. Ours carries the lord's subtype and picture.
3. The startpos character id is NOT left in `mixer_factions_that_require_other_mods`. IEE adds
   skullstack's (`973581693`) there and then calls `mixer_enable_custom_faction("973581693")`, which
   removes it - the 16:02 script log shows no error for that id, so it passed.
4. Mixer's visibility filter: shown when minor factions are switched on (the eye button on the
   race panel, or Mixer's MCT `mixer_show_minor_factions`) OR the faction is in
   `mixer_major_factions`. That list is what our `script/frontend/mod/mixerstuffies.lua` fills with
   `mixer_add_faction_to_major_faction_list`, for every house - and now for
   `wh3_dlc23_chd_minor_faction` and `cr_chd_skullstack` too.

The leader pictures were also wrong: the raw 300x164 Overseer porthole, where CA's cards
(`chd_astragoth_ironhand_0.png`) and ours are 85x115. `leader_png()` now crops a bust around the face
onto the red ground of Astragoth's card and asserts the size.

To check in game: IEE, Chaos Dwarfs, minor factions hidden - both cards should be in the grid. If not,
the next suspect is the party's startpos leader (IEE's skullstack has `mixer_dummy` in its own row).

## 7. Every house's starting hero - off the local-faction read

The other houses' 25 start scripts (`derpy_start_*` in Old World / Dark Lands, `ime_derpy_*` in IEE and
IE) placed their hero inside `if cm:get_local_faction_name() == <house> then`. CA's docs: that call
**throws in multiplayer** unless passed `true`, and forced it names a different faction on each
machine. It sat in CA's pcall-less first-tick list, so in a multiplayer campaign the first house start
to reach it would have replaced its leader, thrown, and stopped every first-tick callback behind it,
ours and other mods'. Not seen in game; read from the docs and the code.

Now one shared function, `derpy_hll_start_hero(faction, type, subtype)` in
`script/campaign/mod/derpy_hll_settings.lua`: looks up the house's leader, finds a tile within 5,
skips with a log line on no leader or no tile, creates the agent, all inside its own pcall. Each
block became one call per hero, same heroes, same placement beside the army (not embedded).
**Behaviour change:** an AI-run house now gets its hero too; before, only the house the player picked
did. Kharkadon's and the Captain's script now calls the same function (it embedded the hero before);
the generator's harness loads the shipped `derpy_hll_settings.lua`, makes the local-faction reads throw,
and requires exactly one hero per lord one tile over and in no force - a mutant that drops the call and
one that embeds the hero again both fail it. Pack `e99f2ff321d6adad822bcdde1541f937`; against
`.bak_prebeside_20261003` (`d73086ea`) only that script differs.

`check_hll_settings.py` section 8 runs Azeros's real start with both local-faction reads stubbed to
throw and asserts his Castellan is placed; against the previous pack's Azeros script it fails twice.
luac, `check_lua_api`, `check_lua_undeclared`, `check_lua_literal_left`: clean on all 26 files.
Pack `d73086eab5741a1f5dc2c777c2f0fb1c`, 458 files; against `.bak_prestarthero_20261003`
(`f4ad7e06`, beside both copies) exactly the 26 scripts differ. Modpacks and the Workshop folder.


## 8. Redesign - the Immortals and the expedition

Asked: the Overlords on "Immortals and elite lords" instead of Urzhkal's slaves; the Company as "an
expeditionary company looking for gold or resources" in Ind, convoys first, lower replenishment for
its Chaos Dwarf units, a Daemonsmith hero. Units are a separate job. All of it is `SKILLS` /
`TRAIT_BUNDLE` / `ITEMS` / `SET_NAME` / `PASSIVE` / `LORE` in the generator.

**The Immortals are the Infernal Ironsworn.** CA's art folder for them is `chd_immortal`
(`chd_infernal_ironsworn_ror_base.variantmeshdefinition`), so the house is built on them and a
future house unit can reuse the art.

| | Overlords of Zharrduk | Uzkul Mingol Company |
|---|---|---|
| Faction bundle | Ironsworn Hell-Forge limit +1, Ironsworn upkeep -15%, lords and heroes +2 recruit rank; **labourer leadership -10** | +1 convoy, trade tariff +15%, raid income +20%; **replenishment -15% army-wide, +15% back for hobgoblins** |
| Lord trait (on the lord) | Infernal Guard Deathblow, Ironsworn Expert Charge Defence | post-battle loot, movement range |
| Line | Undying Guard / Born to the Guard / Iron Unbroken / Overlord's Court / Gate Wardens; 4_1 The Immortal Few (-15% replenishment) or 4_2 Lords of Zharrduk (hobgoblin leadership -6); Overlord Eternal | Company Charter / Prospectors / Ivory Road Factors / Spoils of Ind / The Long March; 4_1 Gold Fever (hobgoblin leadership -6) or 4_2 Charter Trade (raid income -20%); Captain of the Company |
| Starting hero | Bull Centaur, unchanged | Daemonsmith, **Lore of Metal** (was Hashut) |

Three things worth keeping:

- **The +1 Ironsworn is CA's own cap key.** `wh3_dlc23_chd_ritual_unit_cap_infernal_ironsworn` is the
  effect CA's Hell-Forge Lua stacks once per cap ritual (`docs/HELLFORGE_UNIT_CAPS.md`), so a +1 in
  our bundle adds to whatever the rituals give.
- **No effect lowers replenishment for Chaos Dwarf units alone.** CA binds
  `replenishment_percentage_bonus` to `wh3_dlc23_chd_hobgoblin_units` and to artillery, never to the
  dwarfs. -15 army-wide plus CA's `wh3_dlc23_effect_replenishment_rate_hobgoblins` +15 gives the
  same result with no minted effect.
- **The scope check learned bonus-value siblings.** Eight of the effects (the Ironsworn upkeep, the
  Infernal Guard XP, upkeep, armour, charge reflection and deathblow, the Ironsworn charge defence,
  the hobgoblin replenishment in a bundle) are wired in `effect_bonus_value_ids_unit_sets` /
  `..._unit_attribute_junctions` / `..._unit_ability_junctions` but CA never grants them with that
  scope, so the old rule refused them. `vanilla_pairs()` now admits a scope that another effect on
  the same bonus value is granted with. Measured: without the rule exactly those eight fail; with it,
  none; and an Ironsworn armour effect at `character_to_province_own` is still refused (selftest
  mutant). `wh3_dlc23_effect_upkeep_reduction_chd_infernal_guard` reads "negative is good" and CA
  itself ships -10 on it, so -5/-10/-15 is the discount it says.

Checks: generator checks and selftest clean; 86 fragments re-extracted from the saved pack, 0 differ;
`check_skill_trees` 0 ERR, the four WARNs for these lords are the four tier-4 downsides;
`check_effect_signs` lists only the intended penalties; `check_effect_bundle_loc` 70 bundles, 0
findings; `check_hll_settings` 0 failures. Against `.bak_preredesign_20261003` (`e99f2ff3`) 13 files
differ - four DB fragments, eight loc files, the start script - and no row or loc key outside the two
lords moved. Pack `f733b061ae5fb980bba21eced5b57fdb`, Modpacks and the Workshop folder, not
uploaded, not seen in game. `docs/HASHUT_LL_SKILL_LINES.xlsx` re-exported.

The Overlords' Tower seat was in the Thrall (slave) district, which no longer fit: swapped with
Khorakk in §10. Convoys from Ind are the engine's routing and
need a look in game.

## 9. Fixed starting armies

Asked: replace the inherited armies; "all elite for overlords, add deathshrieker for uzkol". Each
lord's `army` is in the start script's `DERPY_NEW_HOUSE_LORDS`; the old leader still dies with his
force, so CA's and IEE's starting units are gone.

| Overlords of Zharrduk (8) | Uzkul Mingol Company (10) |
|---|---|
| Infernal Ironsworn x2, Infernal Guard, Infernal Guard Fireglaives, Chaos Dwarf Warriors (great weapons), Chaos Dwarf Warriors, Chaos Dwarf Blunderbusses, Bull Centaurs (axe) | Chaos Dwarf Warriors, Chaos Dwarf Blunderbusses, Hobgoblin Cutthroats x2, Hobgoblin Archers x2, Hobgoblin Sneaky Gits, Wolf Raiders (bows), Wolf Raiders (spears), Deathshrieker Rocket Launcher |

CA units only, so the lords pack still needs none of the unit packs. **Spawned units count against
the Hell-Forge limits** (`unit_allowances`, `faction_set` `chaos_dwarfs`): the Overlords start AT
every elite limit - Ironsworn 2 (1 plus their trait's +1), Infernal Guard 1 (great weapons share
it), Fireglaives 1, Bull Centaurs 1, Warriors 2 - so more elite means a Hell-Forge ritual first.

`check_army()` in the generator runs on the harness's spawn: every key exists in CA's `main_units`
(a typo spawns nothing, silently), none of the old leader's stub units came along, each Hell-Forge
list is within its starting limit plus whatever the lord's own `TRAIT_BUNDLE` adds, and the
Overlords' list holds no labourer or hobgoblin. Selftest mutants: a typo'd Deathshrieker key, a
third Ironsworn, the old army appended - each caught. Pack `9fbfd37cdb24f9769d29e7b668821bb9`;
against `.bak_prearmies_20261003` (`f733b061`) only the start script differs. Modpacks and the
Workshop folder, not uploaded, not seen in game.

## 10. Tower of Zharr: Khorakk and the Overlords swap districts; the Company's seat banner

Asked: "swap house of khorakk and overlords in the tower of zharr", and (screenshot) "uzkul is not
using their flag".

**The swap.** Bloodline is now Overlords, Baal, Fists, Horns; Thrall is Black Dwarf, Uzkulak, Black
Kraken, Khorakk - each takes the other's slot. A seat's district lives in three places and all three
moved: `templates/toz_districts.py` `DISTRICTS` (the one list), the `rituals` rows' `category` /
`sort_order` (the generator re-sorts them from that list), and `ANNEX_DISTRICTS` in the four
identical `zz_derpy_toz_annex.lua` copies (hand-edited - it decides which district's completion a
claim counts towards). The Bloodline and Thrall reward texts named the houses, so they were reworded,
and the generator now carries every district's name and text out of `toz_districts.py` into
`text/derpy_chd_toz_annex.loc`, as it already carried the seat order.

Two drifts this exposed, both fixed by deriving instead of typing:
- **Nothing checked the Lua against the list.** `check_annex_lua()` in the generator now compares
  all four copies with `toz_districts.py`; against the pre-swap pack it fails, and a selftest
  mutant moves one seat in one copy.
- **`gen_victory_routes.py`'s `ANNEX_GROUP` was a typed copy and already stale** - it still had
  Thrall and Forge at 3 seats. It would have kept Khorakk's Tower route ("Chains of Domination",
  2 seats in his own district) in Bloodline. `ANNEX_GROUP` and `GROUP_SIZE` are now read out of the
  shipped Lua; the route moved to Thrall (one line of `zzz_derpy_chd_victory_routes.lua`), and the
  "unachievable total" mutant now asks for a whole district (`GROUP_SIZE`), since 3 of Forge's 4 is
  achievable.

Not changed: `gen_house_ancillaries.py` still tags Khorakk's items "Bloodline". There it only picks
the colour of the item text, in `derpy_chd_house_ancillaries.pack`, which was not rebuilt. Old saves:
a seat claimed before the swap counted towards its old district.

**The Company's banner.** A claimed seat draws `claimed_seat_<key>.png`; only three of the twelve
houses ship one (IEE adds two more), and without it the panel falls back to Legion of Azgorh's red
banner - the screenshot. New tool `tools/make_toz_seat_banner.py` builds the three files a house
needs (`claimed_seat_`, `claimed_seat_selected_`, `tower_nav_seat_`) from its own flag: IEE's Uzkulak
banner with the anchor blanked (normalised-convolution fill from the surrounding cloth), the flag's
stacked skulls and spikes lifted as the dark shapes clear of its frame, laid on in white; the
selected glow is IEE's own glow delta. `--check` re-measures the written files: outline and finial
untouched, the old device gone, a device drawn, a non-empty nav icon - fed IEE's banner as-is or an
empty icon, it fails. No `seat_slot_` file: that one resolves through a seat payload's confederated
faction, which no payload names. Preview: `.skilltree_cache/toz_seat_banner_preview.png`. The
generator ships the three files.

Pack `c14d23fb8c43d99a70a29459427aa2b0`, 461 files; against `.bak_preseatswap_20261003` (`9fbfd37c`):
+3 images, the rituals fragment (two rows), the Tower loc (two texts), the four Tower Lua copies and
the victory routes script; the five victory DB fragments re-encode with identical rows. Modpacks and
the Workshop folder, not uploaded, not seen in game.

## 11. Seat banners in the house's own colours; the Overlords get one too

Asked: "the banner color is wrong, why didnt u change such detail?" and "did you also check if
overlords have their own banner?". The §10 banner kept IEE's Uzkulak cloth (orange-brown) and put the
device on in white - nobody had checked what decides a seat banner's colours, and the Overlords
(`wh3_dlc23_chd_minor_faction`) had no seat art at all, so they drew Azgorh's red fallback too.

**The rule, measured on every shipped seat banner:** cloth = the faction's `banner_colour_primary`,
device = `banner_colour_secondary` (Khorakk E57300/E6B607, Kraken 943A36/C6DDDE, Uzkulak
684106/FFFFFF, Azgorh C31515/E8D016). The cloth's median sits at 0.64-0.68 of the primary's
brightness (IEE's Uzkulak runs 0.89). The nav icon is always white with a black ring. Colours are read
from an RPFM `export_as_tsv` of CA's `factions_tables` - `read_vanilla_db` returns zeros for those
columns. The Company is 989964 khaki / 44302A dark brown; the Overlords 008080 teal / C31515 red.

`make_toz_seat_banner.py` now takes `HOUSES = {faction: (flag, primary, secondary)}`, re-dyes every
cloth pixel (picked by hue and saturation, so the metal finial and rod are untouched and the cloth
above the finial's last row is dyed too) to the primary at 0.68 brightness, and paints the device in
the secondary. `--check` asserts the cloth hue matches the primary and the device pixels sit near the
secondary, so the §10 build now fails it. Measured: Company cloth 0.55 of primary (its dark device
pulls the median down), Overlords 0.70.

Pack `1cd5c2ce584775625381a849f802bcd5`, 464 files; against `.bak_prebannercolour_20261003`
(`c14d23fb`): 3 Company images changed, 3 Overlords images added, nothing else. Modpacks and the
Workshop folder, not uploaded, not seen in game. ~~Still without seat art: Fists, Horns, Azeros,
Baal, Bzaark, Snakebeard~~ - **wrong (user, 2026-10-04):** the `cr_chd_*` houses' seat art ships
with IEE or The Old World campaign mod, which those factions need anyway. Only a faction neither
mod covers needs a banner from this pack.

## 12. Lord-select Starting army (2026-10-04)

Reported: the frontend's Starting army showed the old startpos units for both factions. Every other
house gives Mixer a list with `mixer_add_starting_unit_list_for_faction` in
`script/frontend/mod/mixerstuffies.lua`; these two had none (written when they still inherited the
old army). Both now carry the §9 army. `check_frontend_army()` in the generator compares each list
with the start script's `army`; selftest mutants drop a list and drop a unit. Pack
`9c29d30ad725a9138a12326f0771ce72`; against `.bak_prefrontendarmy_20261004` (`1cd5c2ce`) only that
script differs.

Then every house, against what its start script spawns (lords pack and unit packs, read from the
installed packs). Three lists were stale and now follow the Old World spawn: the Conclave showed two
Dreadquakes (one since the feedback cut, `WORKSHOP_FEEDBACK_20260821.md`), Abnagg showed 6 Cutthroats /
4 Archers / no Warriors, the Black Dwarf had no Deathshrieker. `check_frontend_army()` now covers all
thirteen (the eleven `cr_oldworld/mod/derpy_start_*.lua` plus the two new lords) and fails on the old
file with exactly those three. Mixer resets a faction's list on every call and `mixerstuffies.lua`
loads before `mixerstuffies_<house>.lua`, so the Fists / Bzaark / Snakebeard / Horns unit packs'
lists win when enabled. Left open, both gameplay calls: IEE's Black Dwarf spawns a different 12-unit
army (`ime_derpy_black_dwarf.lua`) that no single list can also show; and the Fists, Bzaark and
Snakebeard unit packs replace the army in `cr_oldworld` only, so in Dark Lands their lists show units
the lord does not get. Pack `371eba8ce3f4f6a59182bced8f35d96f`; against `1cd5c2ce` only
`mixerstuffies.lua` differs. Modpacks only: the Workshop copy was locked by the running game.

## 13. Lord-select 3D model (2026-10-04)

Asked: the frontend 3D model, Overseer placeholders, like the other lords. Every other lord ships
`ui/frontend ui/front_end_models/<startpos character id>/3d_model.twui.xml` plus
`<id>.warscape_req.xml`. Mixer's `campaign_select_new.twui.xml` creates `.../<GeneralKey>/3d_model`
and falls back to `.../<faction key>/3d_model`, so the two new ones are keyed by **faction**
(`wh3_dlc23_chd_minor_faction`, `cr_chd_skullstack`): no startpos id is needed and it holds in every
campaign. No installed pack ships either folder. `frontend_model()` clones Balur's pair and swaps only
the mesh (CA's `chd_overseer_campaign_01` / `_02`, the variant each wears on the map) and the anim
(`axe_and_shield` celebrate / stand idle, `humanoid03` like the rest). `check_frontend_models()`
resolves every mesh and anim path against CA's `variants*.pack` / `anim*.pack` and parses the XML;
selftest mutants: a missing mesh, a missing anim, broken XML. Pack `225362fef8b6e3e9cd259cd4b321d83c`,
468 files; against `.bak_prefemodels_20261004` only the four new files. Modpacks only (the game was
running), not seen in game.
