# Zhorgrath the Reaver replaces the Captain of the Uzkul Mingol

2026-11-18. Pack: `!aa_derpy_hashut_legendary_lords.pack` (Workshop 3432966208).

Asked: remake the Uzkul Mingol Company leader's skill lines and description from a
collaborator's character, Zhorgrath. The collaborator supplied the bio and the line's skill
names (The Reaver, then Ashen Conqueror, Forged in Cruelty, Iron Tyrant and Hashut's Iron Will,
then Ruthless Captain). The user chose a mix: Zhorgrath himself follows the bio, while the
Company keeps part of its old convoy and trade business.

**The skill and text half was built as `71a76ac1`; the model, portraits and flag followed the same
day (below), and the current lords pack is `fd1b1a2d`, in Modpacks and the Workshop folder.** Not
uploaded. Backup of the uploaded build: `Modding Files/Backup/pre_zhorgrath_20261118/` (`ccc097a5`,
uploaded 2026-11-03).

## What changed

All of it is in `tools/gen_new_house_lords.py` (`LORDS`, `SKILLS`, `TRAIT_BUNDLE`, `ITEMS`,
`PASSIVE`, `LORE`, `FRONTEND_LINE`) and `tools/gen_victory_routes.py`. The keys did not move,
so saves keep working.

| Skill | Rank | Effects |
|---|---|---|
| The Reaver | 4 | melee attack +8 (him), post-battle loot +15% |
| Ashen Conqueror | 11 | movement range +3/6/9%, replenishment +3/6/9% |
| Forged in Cruelty | 11 | post-battle Labour +5/10/15%, armaments production +5/10/15% (his province) |
| Iron Tyrant | 11 | armour +4/8/12 and melee defence +3/6/9 for Chaos Dwarf melee infantry |
| Hashut's Iron Will | 11 | leadership +3/6/9 for Chaos Dwarf melee infantry, fire resistance +5/10/15% (him) |
| No Master's Share | 24, choice | sacking income +40%, post-battle loot +25%, hobgoblin leadership -6 (was Gold Fever) |
| Charter Trade | 24, choice | unchanged effects, text names Zhorgrath |
| Ruthless Captain | 29 | melee attack +12, speed +10%, health +15% (the old capstone's effects) |

- **Name:** forename `12412536` now reads "Zhorgrath"; a new family name `12412538` reads "the
  Reaver" (`family_name`, frequency 0, like CA's row for "the Vicious"). `12412537` is Zochaz's.
  The family name is wired into the start script, the four Tower annex copies, the custom-battle
  character (`gen_new_lords_cb.py`) and the MCT label.
- **Description:** the collaborator's bio, word for word, is his long unit description, joined
  into one paragraph the way CA writes Zhatan's and Drazhoath's. Lord select gets one sentence
  (`FRONTEND_LINE`) because CA's and every other house's lord-select blurb is one sentence.
- **Faction bundle:** the +15% trade tariff became +15% post-battle Labour (CA's own pair from its
  camp-narrative bundle). Later the same day the whole bundle was rebuilt around his playstyle; see
  "His army and faction effects" below.
- **Items and passive:** the Mingol Cleaver's text no longer says it was taken from "the last
  Captain"; the Charter Seal and the set are unchanged. The passive is renamed "Where Zhorgrath Marches".
- **Victory routes:** same objectives and keys; the three texts are in his voice with no Ind, and
  Route I's display name is "Spoils of Conquest" (key still `..._spoils_of_ind`). Route III needed
  one more clause to reach the tool's 40-word floor.

Iron Tyrant and Hashut's Iron Will use the "Chaos Dwarf Melee Infantry" effects CA itself grants
(`wh3_dlc23_skill_chd_army_buff_melee_chaos_dwarfs`, Drazhoath, tech `military_3`). The
`..._chd_chaos_dwarfs_and_hobgoblins` armour and defence effects look like a better fit, but no CA
skill, bundle, ancillary or technology row grants them.

## A latent bug fixed on the way

`SKIP_LOC` did not cover `mission_text_`, so a re-run cloned Balur's three route-lore lines
(Gargath's "the Unholy Legion" text) onto both new houses' slugs. No earlier import had shipped
them; the 11-18 dry run caught six such rows. `mission_text_` is now skipped.

## Checks

Generator checks and `--selftest` pass; 106 fragments re-read from the saved pack, 0 bad; a
rebuild from the post-import extract reproduces the pack exactly. `gen_victory_routes.py --check`
and `--selftest` pass, and the importer's `--verify-only` round-trips every fragment.
`gen_new_lords_cb.py --check` passes. `check_skill_trees`: 0 ERR, the same 40 deliberate WARNs.
`check_effect_signs`: Zhorgrath's three penalties are the three intended ones.
`check_effect_bundle_loc`: 0 findings. `check_hll_settings`: 0 failures. `luac -p` and
`check_lua_api` are clean on the changed Lua. Against the backup, 21 of 589 files differ: five DB
fragments, nine loc files and seven scripts. `docs/HASHUT_LL_SKILL_LINES.xlsx` is re-exported.

## Later the same day: his model, portraits and flag

**Model.** The collaborator's NorscanWarlord overseer (body and head 05) with the axe and shield made
for Zhorgrath, from their two Workshop packs (3783054159, 3841687503). `tools/gen_zhorgrath_model.py`
traces everything the four `.wsmodel` files reach and copies every file that comes from those packs
into `!!!derpy_chd_assets` under `variantmeshes/wh_variantmodels/hu3/chd/norscanwarlord_zhorgrath/`,
renamed with a `norscanwarlord_` prefix and lowercase, so subscribing to both mods never puts two
files on one path. He keeps CA's Overseer animations. The lords pack names the mesh through
`LORDS["mesh"]` in `gen_new_house_lords.py`, for battle, campaign and the lord-select model. Assets
pack `51618d40` in Modpacks and the Workshop folder; backups (the Workshop copy `24dc6ff0`, and a
stale Modpacks copy holding two Goliath hellcannon VFX files the Workshop copy lacks) are in
`Modding Files/Backup/pre_zhorgrath_model_20261118/`.

**Portraits.** The porthole, unit card and lord-select picture come from one battle screenshot of
the model (`Modding Files/source/portraits/derpy_uzkul/shot.png`), one Codex pass each, made by
`derive.py` in that folder, which reuses Kharkadon's. The author picked the close-ups; the wider
first set is kept in `v1_bust/`. Captures need texture and unit quality at 3: the medium preset
halves the collaborator's 512 px axe texture, and **players on medium or lower see the axe smeared in
battle**. The lords pack was `a331f166` after this step (backup in `pre_zhorgrath_portraits_20261118/`).

**Flag.** `tools/make_skullstack_flag.py` redraws the collaborator's chaos star and skull the way CA
draws its Chaos Dwarf flags: CA's frame and plate, the device flat with CA's grain and inner edge,
each arrow evened out against its own mirror. The author chose IEE's own colours (parchment plate,
dark brown device) and asked for the device lower; it is now centred on the plate (y 124 on
`mon_256`, inside CA's 114-131). The six files ship at `ui/flags/cr_chd_skullstack/` in the lords
pack, which loads before IEE, so they replace IEE's flag without touching IEE's factions row.
`make_toz_seat_banner.py` now lifts the Tower seat's device from our staged `mon_256.png`, so the
seat banner and nav icon carry the chaos star too. Lords pack `fd1b1a2d`, md5-checked in Modpacks
and the Workshop folder; the import re-read 106 fragments and 43 loose files with none bad, and
only the six flag files and the three seat files changed. Backups of the old pack and seat PNGs
are in `pre_skullstack_flag_20261118/`.

## Seen in game (IEE lord select, 2026-11-18)

Under a minimal list (assets, lords, Mixer, audio mixer, IEE, the bridge), the IEE lord-select
screen showed his close-up picture on the card, the collaborator's model in the 3D view, the new
flag on the faction badge, and "Where Zhorgrath Marches" in the lord effects. The game closed
itself at 13:57, cleanly (no dump, the front end cleared its callbacks), before the campaign was
started, so the campaign HUD, porthole, unit card and seat banner have not been looked at.

The card's name read "Kastabull", IEE's start-position leader, whom the start script replaces on the
first tick. Fixed below.

## Lord-select names: the front-end script (fixed 2026-11-18)

Lord select shows the start-position general's name (CCO `CcoFrontendFactionLeader.Name`);
`frontend_faction_leaders` has no name column, and CA's own front-end Lua never touches a name.
Mixer's `campaign_select_new.twui.xml` swaps it: `dy_lord_name` and `dy_faction_leader` read
`ScriptObjectContext("mixer_lords_with_name_changes")`, keyed by the card's `GeneralKey` (the
start-position CHARACTER id), and show that land unit's name. `mixer_change_lord_name(id, unit)` in
`script/frontend/mod/mixerstuffies.lua` fills it, and it is display-only, so the MCT-off case is
unaffected. Every other house already used it; the two October houses never got the call, and
Ghorth's Immortal Empires line used `835127146`, which is the Conclave's `start_pos_factions` ID,
not its leader (`1411046267`), so it never applied either.

Ids come from three places: the Old World's and IEE's front-end scripts (`["<id>"] = "<faction>"`
in Mixer's lists) and, for CA's factions, the Assembly Kit's `start_pos_characters` joined to
`start_pos_factions` for `wh3_main_combi` (IEE's start position keeps those ids; its Zharrduk card is
`1997970184`, and CA already names that leader Kharkadon the Vicious). The script now registers every
id for every house, Azeros, the Black Dwarf and Thymbrin included. `gen_new_house_lords.py
check_frontend_names()` reads the same three sources and fails on an id that is no leader's or a card
left unregistered; on the old script it reports all nine faults, and the selftest breaks it both ways.

Seen in game (IEE): Zhorgrath, Ghorth, Kharkadon, the Black Dwarf and Abnagg each show their own
name. In the Old World only the Black Dwarf's card is listed for the Chaos Dwarfs (the Old World's
own script hides the rest, CA's three included, until another mod enables them), and it reads
"The Black Dwarf". Lords pack `d63b7631` for this step.

## His army and faction effects (2026-11-18, the author's pick)

Rebuilt around his skills (Iron Tyrant and Hashut's Iron Will buff CA's melee Chaos Dwarf set:
Warriors, Warriors (Great Weapons), Infernal Guard, Ironsworn) and No Master's Share's hobgoblin
penalty, instead of the Company's old convoys and hobgoblins.

| | Before | After |
|---|---|---|
| Army | 1 Warriors, 1 Blunderbusses, 2 Cutthroats, 2 Hobgoblin Archers, 1 Sneaky Gits, 2 Wolf Raiders (bows, spears), 1 Deathshrieker | 2 Warriors, 1 Warriors (Great Weapons), 1 Infernal Guard, 1 Blunderbusses, 2 Cutthroats, 1 Wolf Raiders (spears), 1 Deathshrieker |
| Faction effects | +1 active convoy, post-battle Labour +15%, raid income +20%, replenishment -15%, hobgoblin replenishment +15% | Chaos Dwarf Warriors limit +2, post-battle Labour +15%, sacking income +20%, +2 siege towers per army, replenishment -15% (whole army) |

The Warriors limit is CA's Hell-Forge cap effect (`wh3_dlc23_chd_ritual_unit_cap_chaos_dwarf_warriors`,
like Kharkadon's Ironsworn), so the army sits at Warriors 3 of 4 and Infernal Guard 1 of 1;
`check_army()` counts the bundle's cap effects and flags five Warriors or two Infernal Guard. The siege
towers are the one effect all three CA Chaos Dwarf lord traits share; lord select hides that line for
CA's Astragoth too. Charter Trade stays as the rank-24 choice. The Daemonsmith hero is unchanged. The
bundle's description now reads: "Zhorgrath answers to no master. His iron-clad warriors march at the
head of the Company, every captive it takes is put to work, and every city it takes is stripped bare.
Its losses are slow to replace."

Seen in game: lord select lists the four faction effects and seven unit cards (Mixer draws one card
per unit type). A new IEE campaign spawned him with exactly the nine units and the bundle applied.
**IEE's start position also gives the Company four Overseer armies holding eight more Warriors**, so
in IEE the faction starts well over its Warriors limit and the +2 only matters once those are lost or
the limit is raised further. Lords pack `9d91a131` in Modpacks and the Workshop folder, md5-checked;
only the bundle rows, two loc files and the two scripts changed. Backups in
`Modding Files/Backup/pre_frontend_names_20261118/` and `pre_zhorgrath_army_20261118/`.

## Not done

- Uploaded 2026-11-18 15:19 with the assets pack (`PATCH_NOTES_20261118_LEGENDARY_LORDS_AND_CHD_ASSETS.md`).
  The HLL tools repo is not synced (`tools/sync_hll_repo.py`).
- Not seen inside a campaign with the UI: the skill tree, the porthole and card, the flag on the HUD
  and in diplomacy, the Tower seat banner, and the unit description (`common.take_screenshot` draws
  no UI layer and the window grab came back black in campaign).
