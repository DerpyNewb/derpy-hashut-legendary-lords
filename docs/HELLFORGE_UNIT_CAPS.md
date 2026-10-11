# Hell-Forge unit caps — how the mechanic resolves, and what it derives from Lua

Written 2026-08-20. Everything here is read from CA's shipped script
(`script/campaign/wh3_dlc23_campaign_chd_hellforge.lua`, 573 lines, in `data/data_script.pack`)
and from the packs themselves. **Nothing in this file has been tested in a running campaign.**

The Chaos Dwarf Hell-Forge panel sells *unit allowance* — "+1 to how many Hellcannons you may
field" — for Armaments. Two things are supposed to happen on each purchase: the cap goes up,
and the next purchase gets dearer. They are **independent code paths keyed on different
strings**, so half of the feature can work while the other half silently does nothing. That is
exactly what happened to the `derpy_` packs; see §6.

---

## 1. The two halves, and the keys they are built from

The listener:

```lua
core:add_listener(
    "hellforge_unit_category_purchase",
    "RitualCompletedEvent",
    function(context)
        return context:ritual():ritual_category():find(self.unit_cap_ritual_category)   -- "HELLFORGE_CAPS"
    end,
    function(context)
        local ritual_key = context:ritual():ritual_key()
        self:modify_ritual_cap_cost(ritual_key, context:performing_faction(), self.unit_cost_modifiers_bundle_string)
        self:modify_unit_cap(ritual_key, context:performing_faction(), self.unit_cap_modifiers_bundle_string)
    end,
    true
)
```

`:find()` is a **substring** match, not equality. A custom category such as
`HELLFORGE_CAPS_ZHARRGRON` is picked up with no script change at all — this is the one part of
the mechanic that is genuinely mod-friendly.

Both handlers then look for one effect **by a name they build themselves**:

| Function | Effect key it looks for | In which bundle | Effect |
|---|---|---|---|
| `modify_unit_cap` | `<ritual_key>` | `wh3_dlc23_bundle_chd_unit_cap_rituals` | +1 |
| `modify_ritual_cap_cost` | `<ritual_key>` .. `"_cost_mod"` | `wh3_dlc23_bundle_chd_unit_cap_rituals_cost_mods` | +25 |

```lua
hellforge = {
    unit_cap_ritual_category            = "HELLFORGE_CAPS",
    unit_ritual_cost_mod_increment      = 25,     -- cost increment each time it is performed
    warmachine_ritual_cost_mod_increment = 10,
    unit_cost_modifiers_bundle_string   = "wh3_dlc23_bundle_chd_unit_cap_rituals_cost_mods",
    unit_cap_modifiers_bundle_string    = "wh3_dlc23_bundle_chd_unit_cap_rituals",
    cost_mod_effect_suffix              = "_cost_mod",
}
```

**`_cost_mod` is the whole ball game.** A ritual `foo_cap` needs an effect `foo_cap` *and* an
effect `foo_cap_cost_mod`. Nothing in any DB table records that the second name is
load-bearing — in RPFM `foo_cap_mod` and `foo_cap_cost_mod` look equally arbitrary. Name it
anything else and the cap still rises on every purchase while the price never moves.

### How the handlers rebuild the bundle

Both do the same dance, and it explains why a wrong key is inert rather than destructive:

```lua
if current_bundle then                                  -- read the faction's live bundle
    for each active_effect do
        if key == effect_to_modify_key then new = old + increment
        else                                new = old            -- everything else preserved
    end
end
bundle_to_apply = cm:create_new_custom_effect_bundle(bundle_key)   -- fresh from the DB base
for each new_effect do
    if effects_to_new_values[key] then set(key, that)              -- preserved or bumped
    elseif effect_to_modify_key == key then set(increment)         -- first purchase
    else set(0)
end
bundle_to_apply:set_duration(0)
cm:apply_custom_effect_bundle_to_faction(bundle_to_apply, faction_interface)
```

A key that matches nothing simply never enters `effects_to_new_values`, so every other
faction's escalation survives untouched. Your ritual is the only casualty.

> **The `+10` war-machine branch is unreachable for mods.** It tests
> `active_effect_key == "wh3_dlc23_chd_ritual_unit_cap_warmachines_cost_mod"` — a **literal
> vanilla key**, not a category or a list. A modded war-machine cap always takes the 25 path.

Because `create_new_custom_effect_bundle` resolves against `effect_bundles_tables`, the two
shared bundles must exist as records and your effects must be junctioned **into them** — see
`MEMORY`/`wh3-custom-effect-bundle-needs-record` for the nil this returns otherwise.

---

## 2. Vanilla's numbers

Fourteen cap rituals since 9.0, in six categories (read off `db.pack` with
`tools/read_vanilla_db.py rituals_tables`, 2026-10-09):

| Category | Rituals |
|---|---|
| `HELLFORGE_CAPS_BULL_CENTAURS` | bull_centaurs |
| `HELLFORGE_CAPS_FLYING_BEASTS` | bale_taurus, great_taurus, lammasu, **`wh3_dlc29_chd_ritual_unit_cap_chaos_siege_giant`** (9.0, keyed `dlc29`) |
| `HELLFORGE_CAPS_KDAAI` | kdaai_destroyer, kdaai_fireborn |
| `HELLFORGE_CAPS_MELEE_INFANTRY` | chaos_dwarf_warriors, infernal_guard, infernal_ironsworn |
| `HELLFORGE_CAPS_MISSILE_INFANTRY` | chaos_dwarf_blunderbusses, infernal_guard_fireglaives |
| `HELLFORGE_CAPS_WARMACHINES` | hellcannon, warmachines |

The Siege Giant ritual is gated to `wh3_dlc29_loet_glottkin` and carries its own `_cost_mod`
row in the ToZ cost bundle (`sessions/HANDOFF_20260925_UPDATE_9_0_NEW_CAPABILITY.md` §2), so
anything that re-lists the cap rituals has one more to carry. It is in neither ToZ pool (§4).

Two things worth not re-deriving:

- **`rituals.percentage_cost_increase_per_use` is `0.0` on all fourteen**, and
  `max_times_cost_can_increase` is `2147483647`. That column looks like the escalator and is
  not — the escalation is entirely the script above. Do not "fix" a flat price by setting it.
- **The payload bundle carries no effects.** `ritual_payload_effect_bundles` maps payload
  `<ritual_key>` to bundle `<ritual_key>`, and that bundle has **zero**
  `effect_bundles_to_effects_junctions` rows in vanilla. It is a marker, not a payload. The
  values live in the two shared bundles and are written by script.

Starting caps sit in `unit_allowances` — vanilla's Chaos Dwarf rows are `faction_set =
chaos_dwarfs`, `point_cap` 1 or 2.

---

## 3. The full table set for one cap ritual

Verified by diffing a working vanilla seat against the mod's. Miss any and it fails quietly.

| Table | Row |
|---|---|
| `unit_lists` | the list key |
| `unit_to_unit_list_junctions` | which units count against it |
| `unit_allowances` | `unit_list` · `faction_set` · starting `point_cap` |
| `rituals` | `<ritual_key>` · `category` = `HELLFORGE_CAPS…` · `completion_payload` |
| `ritual_categories` | only if you add a new category; `group` = `hellforge_unit_caps` |
| `ritual_payloads` | the payload |
| `ritual_payload_effect_bundles` | payload → bundle `<ritual_key>`, duration `0` |
| `ritual_payload_resource_transactions` | e.g. `wh3_dlc23_chd_hellforge_unit_cap_increase_*` |
| `resource_costs` + `resource_cost_pooled_resource_junctions` | the Armaments price |
| **`campaign_group_rituals`** | **`wh3_dlc23_chd_ritual_hellforge` · `<ritual_key>` · `initially_unlocked`** |
| `effects` | **two rows** — `<ritual_key>` and `<ritual_key>_cost_mod` |
| `effect_bundles` | `<ritual_key>` (the marker bundle) |
| `effect_bundles_to_effects_junctions` | `<ritual_key>` → `wh3_dlc23_bundle_chd_unit_cap_rituals` @ `0`; `<ritual_key>_cost_mod` → `wh3_dlc23_bundle_chd_unit_cap_rituals_cost_mods` @ `0` |
| `effect_bonus_value_unit_list_junctions` | `unit_allowance_point_cap_mod` · `<unit_list>` · `<ritual_key>` |
| `effect_bonus_value_ritual_junctions` | `percentage_cost_mod` · `<ritual_key>_cost_mod` · `<ritual_key>` |

`campaign_group_rituals` is the same trap as the Tower of Zharr's — an unregistered ritual is
present-but-permanently-disabled and no script call overrides it. See
`TOWER_OF_ZHARR_CUSTOM_SEATS.md` §2.

---

## 4. The Tower of Zharr free-cap seats, and why modded rituals can never win them

Two tier-2 seats hand out a free unit cap every 4 turns:

| Seat | Bundle it applies | Pool it rolls from |
|---|---|---|
| `wh3_dlc23_ritual_chd_toz_slot_t2_sorcery_1` | `wh3_dlc23_bundle_chd_unit_cap_monsters_rituals_cost_mods_toz` | `unit_cap_monsters_ritual_list` — 6 keys |
| `wh3_dlc23_ritual_chd_toz_slot_t2_military_3` | `wh3_dlc23_bundle_chd_unit_cap_infantry_rituals_cost_mods_toz` | `unit_cap_infantry_ritual_list` — 5 keys |

```lua
local unit_cap_ritual = tower_of_zharr.unit_cap_monsters_ritual_list[cm:random_number(#…)]
cm:apply_effect_bundle(hidden_effect, faction, 0)      -- -9999999% : the seat makes it free
cm:perform_ritual(faction, "", unit_cap_ritual)
cm:trigger_incident(faction, "wh3_dlc23_chd_toz_cap_"..unit_cap_ritual, true)
cm:remove_effect_bundle(hidden_effect, faction)
```

**Both pools are hardcoded vanilla key lists in `wh3_dlc23_campaign_chd_tower_of_zharr.lua`**
(lines 85 and 95), and the `!aa_derpy_hashut_legendary_lords` override still carries them
verbatim — confirmed against the live Workshop pack 2026-08-20, byte offset 472111. CA's 9.0
script still has the same eleven keys at the same two lines (re-read 2026-10-09).

So a modded cap ritual can carry a perfectly correct `-9999999` row in the `_toz` bundle and
still never receive it: the seat only ever rolls one of the eleven vanilla keys. Putting a
`derpy_` ritual in those `_toz` bundles is **dead weight until the two Lua lists are
extended in the override**. It costs nothing and breaks nothing — it just never fires.

The `cm:trigger_incident` on the next line is a second reason to extend the list carefully:
the incident key is concatenated as `"wh3_dlc23_chd_toz_cap_"..unit_cap_ritual`, so any ritual
added to a pool also needs an incident row under that derived name.

---

## 5. Where the `derpy_` packs sat before 2026-08-20

Nine cap rituals across four packs, in two mod-defined and three vanilla categories:

| Pack | Rituals | Category |
|---|---|---|
| `derpy_chd_units` | art_trains, turtle_tank | `HELLFORGE_CAPS_ZHARRGRON` (mod-defined) |
| `derpy_chd_units` | elite_guard, gunners, infernal_gunners, weapon_teams | `HELLFORGE_CAPS_MISSILE_INFANTRY` |
| `derpy_chd_tank` | turtle_tank | `HELLFORGE_CAPS_ZHARRGRON` |
| `derpy_chd_aeromachines` | gyros | `HELLFORGE_CAPS_ZHARRGRON` |
| `derpy_um_mecha_dogs` | mech | `HELLFORGE_CAPS_KDAAI` |

Every table above was present and correct, including the non-obvious step of junctioning into
CA's *shared* bundles rather than private ones. The single defect was the escalator effect
named `<ritual>_cap_**mod**` instead of `<ritual>_cap_**cost**_mod` — so `modify_unit_cap`
matched and `modify_ritual_cap_cost` did not. Caps rose; prices never did.

### Fixed 2026-08-20

35 rows renamed across three tables per pack — `effects`,
`effect_bonus_value_ritual_junctions` and `effect_bundles_to_effects_junctions` (both the
`..._rituals_cost_mods` row **and** the `..._cost_mods_toz` row, so §4 stays consistent for
whenever the Lua lists get extended). No loc key references the effect, so that is the whole
surface. Backups are `.bak_capcostmod_20260820` beside each pack.

These edits were made **to the Workshop copies** — none of the four has a working copy under
`Modding Files/Modpacks/`. Steam reverts them on re-validation or the next Workshop update.
See `MEMORY`/`workshop-is-the-live-copy`.

---

## 6. Still open in those packs

- **A hand-rolled second escalator.** Every derpy cap ritual carries
  `percentage_cost_post_mod | <ritual> | <ritual>` — a row no vanilla cap ritual has. It reuses
  the cap counter (which `modify_unit_cap` increments) as a cost modifier, so the price creeps
  ~1% per limit owned. Reading it as evidence, it was added to compensate for the escalator
  that was not firing. With the real +25 now live, decide whether to keep it.
- **`unit_allowances.faction_set` is empty** on all six `derpy_chd_units` rows. All 22 vanilla
  rows name one.
- **Two packs ship the same fragment path.** `derpy_chd_tank.pack` and `derpy_chd_units.pack`
  both contain `db/<table>/derpy_chd_tanks`. Identical in-pack paths are a whole-file override,
  not a row merge, and `derpy_chd_units` sorts later, so it wins outright. (2026-09-25: the Dawi
  Gunpowder crash reports point the other way, the name that sorts FIRST winning, and this pair is
  one of four; see `sessions/WORKSHOP_BUG_REPORTS_20260925.md` §1.) Shadowed:

  ```
  effect_bundles_to_effects_junctions   monsters_..._toz <- turtle_tank_cap_cost_mod   (dropped)
  effect_bonus_value_ritual_junctions   percentage_cost_mod | turtle_tank_cap | turtle_tank_cap   (dropped)
  effect_bonus_value_ritual_junctions   post_mod | ..._iron_daemon_cost_mod | turtle_tank_cap     (dropped)
  rituals                               turtle_tank_cap, sort_order -99999, payload ..._cap       (replaced)
  ```

  Give the two packs' fragments distinct filenames and all four come back.
- **`elite_guard` contradicts itself** — it sits in `HELLFORGE_CAPS_MISSILE_INFANTRY` but
  carries `melee_infantry` and `infernal_guard` armament cost mods and no missile-infantry one.
- **`turtle_tank` is filed under the *infantry* `_toz` bundle** in `derpy_chd_units` and the
  *monsters* one in `derpy_chd_tank`. Moot while §4 holds, but pick one.

---

## 7. How to check this without launching the game

Extract every pack's `db` as TSV and assert the derived key exists for each cap ritual. This is
the check that would have caught the bug at build time:

```bash
for d in sw/*/; do
  hits=$(grep -h "HELLFORGE" $d/db/rituals_tables/*.tsv 2>/dev/null | cut -f1)
  for k in $hits; do
    grep -rhqE "^${k}_cost_mod\b" $d/db/effects_tables/*.tsv \
      && echo "  $k OK" || echo "  $k MISSING"
  done
done
```

Run over all 371 Workshop packs on 2026-08-20 this reported 9/9 `OK` after the fix, and found
`derpy_um_mecha_dogs` — a pack nobody was looking at.

**The generalisation.** CA's campaign scripts build keys by concatenation, and those are
precisely the keys DB tracing can never reveal. Two found in one day:

| Mechanic | Concatenation |
|---|---|
| Hell-Forge | `ritual_key .. "_cost_mod"` |
| Tower of Zharr | `seat_key .. "_usurp_cost_modifier_hidden"` |
| Tower of Zharr | `"wh3_dlc23_faction_political_diplomacy_mod_toz_usurped_" .. usurpee_faction` |
| Tower of Zharr | `"wh3_dlc23_chd_toz_cap_" .. unit_cap_ritual` |

Before extending any scripted mechanic, grep its script for `..` on key strings.

---

## 8. Category icons — derived from the category key, not from the DB

Added 2026-08-20, read from `ui/campaign ui/hellforge_panel_unit_caps_tab.twui.xml` (in
`data/ui3.pack`, line 968) and `hellforge_panel_category_tab.twui.xml` (line 5855).

`ritual_categories.ui_icon` is a **red herring** for this panel. All seven vanilla HELLFORGE
rows leave it at `UI\skins\default\0_placeholder.png` and the icons still draw, because the
`icon_holder` component builds the path itself with a `ContextImageSetter`:

```
CcoRitualCategoryRecord
(name = GetIfElse(Id.EndsWith("WARMACHINES"), "warmahines", Id.Replace("HELLFORGE_CAPS_",""))) => {
  "ui/skins/default/dlc23_chd_hell_forge/hellforge_quick_move_" + name + ".png"
}
```

So the icon for a custom cap category is **one PNG at a derived path**:

| Category `id` | File the panel asks for |
|---|---|
| `HELLFORGE_CAPS_ZHARRGRON` | `ui/skins/default/dlc23_chd_hell_forge/hellforge_quick_move_zharrgron.png` |
| `HELLFORGE_CAPS_GYROCOPTERS` | `ui/skins/default/dlc23_chd_hell_forge/hellforge_quick_move_gyrocopters.png` |

**56x56 RGBA PNG.** The 62x66 frame behind it is `cap_category_iconm_holder.png` and is not
per-category. Ship the filename **lowercase** — the expression yields `ZHARRGRON` but every
vanilla file is lowercase (`hellforge_quick_move_bull_centaurs.png`), so lookup is
case-folded; an uppercase in-pack path is the 6.1 crash rule, see `MEMORY`/`wh3-lowercase-rule`.

Two traps:

- **Any category whose id ends in `WARMACHINES` is forced to `warmahines`** — CA's own typo,
  hardcoded. Such a category can never have its own icon; rename it.
- Missing file falls back to whatever is baked into `image_index` 1 of the component, which is
  `hellforge_quick_move_melee_infantry.png` — an orange **axe**. An axe on a category you did not
  file under melee infantry means the derived path did not resolve. It is not `0_placeholder.png`.

The **upgrades** half of the panel does the same trick from a different table —
`initiative_set_categories.key`, `CcoInitiativeSetCategoryRecord`:

```
"ui/skins/default/dlc23_chd_hell_forge/hellforge_quick_move_" + Key.Replace("DLC23_CATEGORY_","").Replace("_INITIATIVES","") + ".png"
```

`initiative_set_categories.optional_icon` exists and this callback ignores it. Vanilla's
`DLC23_CATEGORY_WARMAHINES_INITIATIVES` carries the typo in the key itself, so no special case
is needed on that side.

Neither concatenation lives in Lua, so the §7 rule ("grep the script for `..`") would not have
found either — for a panel-drawn mechanic, grep the `.twui.xml` for `+ ".png"` as well.

### Where the `derpy_` packs sit

| Pack | Category | Icon |
|---|---|---|
| `derpy_chd_units`, `derpy_chd_tank` | `HELLFORGE_CAPS_ZHARRGRON` | `hellforge_quick_move_zharrgron.png` — added 2026-08-20 |
| `derpy_chd_aeromachines` | `HELLFORGE_CAPS_GYROCOPTERS` | `hellforge_quick_move_gyrocopters.png` — added 2026-08-20 |
| `derpy_um_mecha_dogs` | `HELLFORGE_CAPS_KDAAI` (vanilla) | inherits vanilla |

Both icons are **restyled from CA’s own art**, not drawn. The bronze-relief look already
exists in `ui/common ui/unit_category_icons/` (22x22) and `ui/campaign ui/mounts/` (59x59);
`Modding Files/source/hellforge_icons/restyle.py` reframes a source to ~38–42px of art in the
56px tile and rebuilds only the near-black rim and the drop shadow:

| Output | CA source |
|---|---|
| `hellforge_quick_move_zharrgron.png` | `ui/campaign ui/mounts/mount_steam_tank.png` |
| `hellforge_quick_move_gyrocopters.png` | `ui/common ui/unit_category_icons/dwf_gyrocopter.png` |

Two things that pass through `restyle.py` as parameters because they bit:

- **`cut`** — the `mounts/` icons bake a soft glow into their alpha (a 32–224 band around the
  subject). Keep it and the added rim traces the *glow*, giving a visible rectangular halo.
  `cut=140` drops it and rescales what is left.
- **`sharpen`** — a 22px `unit_category_icons` source blown up to 38px goes soft; an unsharp
  pass before compositing pulls the relief back.

`_src/` beside the script holds the two CA sources plus the six vanilla icons the sheet
compares against, so the script runs without RPFM. Earlier procedurally-drawn versions
(polygons + gradient) read as flat next to CA’s — restyling real art is the cheaper answer.

`zharrgron` went into **both** `derpy_chd_units` and `derpy_chd_tank` — the category is defined
in both packs, and §6's shared-fragment shadowing does not apply to identical PNG bytes.

These edits were made to the **Workshop copies**; Steam reverts them on re-validation. Backups
are `.bak_icons_20260820` beside each pack. See `MEMORY`/`workshop-is-the-live-copy`.

---

## 9. The *other* half of the panel — adding an upgrades category

Built 2026-08-21. §1–§8 are the **unit caps** tab. The **upgrades** tab is a separate mechanic
with its own eleven tables, and it is fully data-driven: `hellforge_panel_category_tab.twui.xml`
line 1146 fills the category boxes from `Helforge.UnitCategoriesList`, so a category appears as
soon as the player's faction has an `initiative_set` in it. Nothing is hardcoded to CA's six.
One 9.0 exception to check: the panel lists war machines from a hardcoded `WarmachineUnits`
list in `ui/cco/dlc23helforge.cco:156`, and whether a modded war machine needs adding to it is
open (`sessions/HANDOFF_20260925_UPDATE_9_0_NEW_CAPABILITY.md` §2).

### The table set for one category

| Table | ver | Row |
|---|---|---|
| `initiative_set_categories` | 4 | `DLC23_CATEGORY_<NAME>_INITIATIVES` · `max_active_set_count` -1 · `should_save_presets` false |
| `initiative_sets` | 7 | key · limit 3 · cooldown 3 · `category` · points_limit 0 · `allows_multiple_activation` true |
| `faction_initiative_sets` | 0 | set · `campaign_lookup` = `wh3_dlc23_feature_chaos_dwarfs` |
| `initiatives` | 8 | one per upgrade; `effects` names a `campaign_effect_lists` key |
| `initiative_set_items` | 1 | initiative → set |
| `campaign_effect_lists` | 0 | one key per upgrade, same name as the initiative |
| `campaign_effect_list_effect_junctions` | 0 | effect · list · scope `faction_to_force_not_garrsion_own_unseen` · value |
| `effects` | 0 | effect · icon · priority · icon_negative · `category` battle · is_positive_value_good |
| `effect_bonus_value_ids_unit_sets` | 0 | **`bonus_value_id` · effect · `unit_set`** — this is what binds the upgrade to units |
| `unit_sets` + `unit_set_to_unit_junctions` | | only if no suitable set already exists |
| `text/db/*.loc` | | see keys below |

**`expended_cost` / `upkeep_cost` are free** — `wh3_dlc23_chd_armaments_hellforge_upkeep_t1…t5`
are vanilla `resource_costs` records shared by all six CA categories.

### The one thing a category may NOT share: its unlocker

`required_cost` **must** point at records private to the category, and those records must spend a
**pooled resource private to the category**. Every CA category has one —
`wh3_dlc23_chd_hellforge_{bull_centaur,flying_beast,kdaai,melee_inf,missile_inf,warmachine}_unlocker`
— and that resource *is* the category's "level": its loc display name for war machines is
literally **"Total War Machines Capacity"**.

Two consequences, both observed 2026-08-21:

- **A cap ritual whose `ritual_payload_resource_transactions` grants
  `wh3_dlc23_chd_hellforge_unit_cap_increase_warmachine_1` raises CA's War Machines level.**
  Buying a turtle-tank cap was levelling CA's category, because the payload fed CA's resource.
- **Two modded categories sharing one unlocker render as one.** The second box cannot resolve
  its own set through
  `PlayersFaction.InitiativeSetList.FirstContext(InitiativeSetContext.CategoryContext.Key == this.Key)`,
  and a `card_holder`/title whose context fails to resolve **keeps whatever the previous box
  rendered** — so you get two boxes with an identical title and identical cards, not an empty
  one. Isolation test that proves it: disable one pack and the other's category renders
  correctly on its own.

The set to add per category:

| Table | ver | Row |
|---|---|---|
| `pooled_resources` | 2 | `derpy_chd_hellforge_<x>_unlocker` · max 2147483647 · min 0 · default_factor `other` · `END_OF_ROUND` · scope `FACTION` · always_display_zero_factors true |
| `pooled_resource_factor_junctions` | 2 | `derpy_chd_hellforge_unit_cap_unlocker_<x>` · factor **`wh3_dlc23_chd_hell_forge_unit_cap`** · the resource · 0 · 2147483647 |
| **`campaign_group_pooled_resources`** | **1** | **`wh3_dlc23_feature_chaos_dwarfs` · the resource · initial amount (CA uses 1–4)** |
| `resource_costs` | 0 | `derpy_chd_hellforge_required_<x>_t1…t5` **and** `derpy_chd_hellforge_unit_cap_increase_<x>_1`, all `RITUAL`/`RITUAL`/`ARMY_UPKEEP`/`BACKGROUND_INCOME` |
| `resource_cost_pooled_resource_junctions` | 1 | the five required records at `-4 -6 -8 -10 -12`, and the increase record at `+1`, all on the new factor, `absolute`/`default` |
| `initiatives` | | `required_cost` → the new `_t1…t5` |
| `ritual_payload_resource_transactions` | | the category's cap rituals → the new `_increase_<x>_1` |

Loc, four keys: `pooled_resources_display_name_<res>`, `_description_<res>`,
`_positive_factors_display_name_<res>`, `_negative_factors_display_name_<res>`.

`campaign_group_pooled_resources` is the row that **gives the faction the resource at all**, and
it is the one with no other reference to lead you to it — every other table in the chain is
reachable by following a key you already have. Without it the category renders, the upgrades
render, and then: the capacity bar never moves no matter how many caps you buy, every tier stays
padlocked, and a second modded category duplicates the first's box. Three symptoms, one absent
row. Diagnostics say nothing — `InvalidReference` stays 0, because every key that *is* written is
valid.

Do **not** put `\n` escapes in loc text imported via `import_tsv` — RPFM reports `InvalidEscape`.
Keep descriptions single-line.

### The audit that finds this in one pass

There is **no engine-side DB log** — the game writes only Lua `script_log_*.txt`. So do not try to
debug a data mechanic by adding tables until it works. Extract all 1,520 vanilla tables once
(`extract_packed_files` on `data/db.pack`, `export_as_tsv: true`, ~1.4 s) and grep every key in
the chain for the table set that mentions it:

```bash
for k in DLC23_CATEGORY_WARMAHINES_INITIATIVES          wh3_dlc23_faction_initiative_set_chd_category_warmachines          wh3_dlc23_faction_initiative_chd_category_warmachines_1          wh3_dlc23_chd_hellforge_warmachine_unlocker          wh3_dlc23_chd_hellforge_unit_cap_unlocker_warmachine          wh3_dlc23_chd_hellforge_unit_cap_required_warmachine_t1          wh3_dlc23_chd_hellforge_unit_cap_increase_warmachine_1          wh3_dlc23_chd_category_warmachines
do echo "== $k"; grep -rl "$k" vanilla_all/db/ | sed 's|.*/db/||; s|/data__.tsv||'; done
```

Run over the War Machines category that yields the complete set. Everything it names and your
pack does not is a gap; the only ones safe to skip are `cai_decision_items` (AI weighting),
`banners_permitted_unit_sets`, and `effect_bonus_value_initiative_set_junctions` (the lord
upkeep-mod effects). This one command would have replaced four rounds of guessing.

**The icon is free too**, and by the same trick as §8: `hellforge_panel_category_tab.twui.xml`
line 5855 builds
`"ui/skins/default/dlc23_chd_hell_forge/hellforge_quick_move_" + Key.Replace("DLC23_CATEGORY_","").Replace("_INITIATIVES","") + ".png"`.
`initiative_set_categories.optional_icon` is ignored. Name the category after an icon the pack
already ships and no art is needed.

Loc keys, all derived:

```
initiative_set_categories_display_name_<CATEGORY_KEY>
initiative_set_categories_description_<CATEGORY_KEY>
initiatives_localised_name_<initiative_key>
initiatives_localised_description_<initiative_key>
effects_description_<effect_key>            e.g. "Ammunition: %+n%"
```

### Bonus value ids proven to work on CHD war machines

Read off vanilla's own `effect_bonus_value_ids_unit_sets` rows for
`wh3_dlc23_chd_category_warmachines`: `ammo_mod`, `armour_mod`, `range_mod`, `reload`,
`battle_barrier_health`, `unit_damage_resistance_physical_mod`, `mod_land_movement_battle`,
`missile_explosion_damage_mod_mult`, `missile_explosion_damage_ap_mod_mult`, `cost_mod`,
`melee_attack_mod`. Stat upgrades need only the one `effect_bonus_value_ids_unit_sets` row per
unit set.

### Ability- and attribute-granting upgrades

Four more tables, all version 0. CA's eight war-machine upgrades are six of these and only two
plain stats, so this is the more common shape:

| Table | Row |
|---|---|
| `unit_set_unit_ability_junctions` | `key` · `unit_ability` · `unit_set` |
| `unit_set_unit_attribute_junctions` | `key` · `unit_attribute` · `unit_set` |
| `effect_bonus_value_unit_set_unit_ability_junctions` | `enable` · effect · **that junction key** |
| `effect_bonus_value_unit_set_unit_attribute_junctions` | `enable` · effect · that junction key |

The junction `key` is **unique** — one row, one unit set. To cover two unit sets with one
upgrade, make two junction keys and give the effect two rows in the `effect_bonus_value_*`
table; `(bonus_value_id, effect)` is *not* unique there, and vanilla relies on that.
`campaign_effect_list_effect_junctions.value` is `1.0000` for an enable.

Proven on CHD war machines, straight out of CA's own rows: abilities
`wh_main_hero_passive_forgefire`, `wh3_dlc23_unit_passive_extra_reload`,
`wh2_dlc11_unit_passive_extra_powder`, `wh3_dlc23_unit_passive_hellbound`,
`wh3_dlc23_unit_passive_blazing_body`; attribute `ignore_imbue_contact_effects_enemy` (and
`rampage`, `strider`, `guerrilla_deploy`, `causes_fear`, `causes_terror` are wired to the same
set if wanted).

One trap copied from CA by accident: their contact-immunity effect's `icon_negative` is
`contact_immunity.png`, which **does not exist** — the real file is
`attribute_contact_immunity.png`. Copy vanilla effect rows, but run diagnostics after.

### What was built

| Pack | Category | Unit sets it drives | Upgrades |
|---|---|---|---|
| `derpy_chd_units` | `DLC23_CATEGORY_ZHARRGRON_INITIATIVES` "Zharrgron Engines" | `derpy_chd_art_trains` + `derpy_chd_turtle_tank` (16 units) | 14 |

**Exactly one modded category ships — see §10 for why.**

Eight stat upgrades (ammo, armour, reload, range, speed, physical resistance, explosion damage,
barrier) plus six ability/attribute ones (Forgefire, Extra Reload, Black Powder Aplenty,
Hellbound, Blazing Body, Immune to Contact Effects), spread over armament tiers 1–5.
`active_initiative_limit` is 3, so the pool is a choice, not a stack.

It reuses an existing unit set and an icon already in the pack. Table files are all
`db/<table>/derpy_chd_zharrgron`, plus `text/db/derpy_chd_zharrgron.loc` (49 entries). It owns
its progression end to end: pooled resource `derpy_chd_hellforge_zharrgron_unlocker` ("Total
Zharrgron Engine Capacity"), factor junction
`derpy_chd_hellforge_unit_cap_unlocker_zharrgron` on CA's `wh3_dlc23_chd_hell_forge_unit_cap`,
registered to `wh3_dlc23_feature_chaos_dwarfs` at 3, its own
`derpy_chd_hellforge_required_zharrgron_t1…t5` and `..._unit_cap_increase_zharrgron_1`, and both
the `derpy_chd_art_trains` and `derpy_chd_turtle_tank` cap rituals repointed onto it — so
buying a train or tank cap levels **this** category and no longer CA's War Machines.

**Still pointed at a CA resource:** the four `derpy_chd_units` missile-infantry cap rituals
(`elite_guard`, `gunners`, `infernal_gunners`, `weapon_teams`) still grant
`wh3_dlc23_chd_hellforge_unit_cap_increase_mis_inf_1`, so they level CA's Missile Infantry
category. Those units *are* in CA's missile-infantry unit set, so that is arguably correct —
but it is the same mechanism, so decide deliberately rather than by omission.

**Why a whole new category rather than joining `wh3_dlc23_chd_category_warmachines`:** the derpy
war machines *are* junctioned into that set, correctly, and still never appear in CA's War
Machines box. Never explained — every field compared against the missile-infantry units that do
appear (caste, `campaign_cap`, military permissions, mercenary rows, `exclude`) is identical.
The one structural difference is that all 8 trains share `ui_unit_group_land = chd_iron_daemon`
and all 8 tanks share `chd_dreadquake`; CA's 11 units in that set collapse to exactly 6
`ui_unit_group_land` values and exactly 6 cards draw, which fits — but the missile box's
19 members / 9 groups / 13 cards does **not** fit the same rule, so treat it as unresolved.
A private category sidesteps it entirely.

---

## 10. Only one modded upgrades category — the ceiling, and everything ruled out

Established 2026-08-21 by isolation testing in a live campaign, then reverted to one category.

| Loaded unit categories | Result |
|---|---|
| CA's 6 + Zharrgron (**7**) | correct |
| CA's 6 + Gyrocopters (**7**) | correct |
| CA's 6 + Zharrgron + Gyrocopters (**8**) | **the first-registered modded category duplicates the other's box** |

The duplicate is not two rows — it is one box rendering another's data. `template_category_block`
(`hellforge_panel_category_tab.twui.xml:5429`) is the box, and it drives every child from a single
`ContextPropagator`:

```
CcoInitiativeSetCategoryRecord
  PlayersFaction.InitiativeSetList.FirstContext(InitiativeSetContext.CategoryContext.Key == this.Key)
```

Title (`InitiativeSetContext.CategoryContext.DisplayName`) and cards
(`Helforge.DisplayUnitsForInitiativeSet`) both hang off that one propagated
`CcoCampaignInitiativeSet`. When it fails to resolve, the children keep the previously rendered
values rather than blanking — so you get an identical title **and** identical cards, which reads
like a duplicated DB row and is not one.

`derpy_chd_aeromachines` sorts before `derpy_chd_units`, and it was the aero category that got
clobbered — the *earlier*-registered one loses.

### Ruled out, each verified against disk

- **Not the tables.** Both packs' chains were complete and independent: own category, set,
  `faction_initiative_sets`, 14 initiatives, effects, unit set, loc, `InvalidReference = 0`.
- **Not a file collision.** The two packs shared **zero** in-pack paths.
- **Not the schema.** `faction_initiative_sets` keys on `(initiative_set, campaign_lookup)`,
  `initiative_set_categories` on `key`, `initiative_sets.category` is a real FK — nothing merges.
- **Not a shared unlocker**, **not shared `required_cost` records**, **not the missing
  `campaign_group_pooled_resources` row** — each was fixed in turn and the duplication survived
  all three. (All three were real defects worth fixing on their own; §9 keeps them.)
- **Not the campaign save.** Reproduced on a fresh campaign.

Untested, and the only remaining lead if this is revisited: define **both** categories inside a
**single pack**, so they enter `initiative_set_categories` from one table file rather than one
each from two packs. That was the shape never tried.

**Practical rule until then: one modded Hell-Forge upgrades category across the whole load
order.** A second one does not fail loudly — it silently eats the first. If more units need
upgrades, widen the existing category's unit sets rather than adding a category; a category's
card list is the union of the unit sets its effects bind to, so a single category can cover
units from several packs via `effect_bonus_value_ids_unit_sets` rows added by each.

### What was reverted

`derpy_chd_aeromachines.pack` was restored from `.bak_pregyro_20260821` — no `initiative_*`,
`campaign_effect_*` or `initiative_set_*` tables — then the **unlocker half was reapplied on its
own**, in table files `derpy_chd_gyro_unlocker`:

```
pooled_resources                        derpy_chd_hellforge_gyro_unlocker    "Total Aeromachine Capacity"
pooled_resource_factor_junctions        derpy_chd_hellforge_unit_cap_unlocker_gyro  wh3_dlc23_chd_hell_forge_unit_cap
campaign_group_pooled_resources         wh3_dlc23_feature_chaos_dwarfs · the resource · 3
resource_costs                          derpy_chd_hellforge_unit_cap_increase_gyro_1
resource_cost_pooled_resource_junctions that record · +1 · absolute · default
ritual_payload_resource_transactions    derpy_chd_gyros_cap  the increase record   (repointed in place)
```

So `derpy_chd_gyros_cap` no longer levels CA's War Machines. **The payload row must be edited in
place, not added in a new file** — `ritual_payload_resource_transactions` keys on
`(payload, transaction)`, so a second row for the same payload would make the ritual grant *both*.

The resulting resource has no consumer while the gyros have no upgrades category: it accumulates
and is never spent. That is deliberate — inert is the point, versus inflating a CA category. If
the category is ever revisited, the progression side is already wired.

Pre-existing and untouched: `db/rituals_tables/uuu_vrook_chd_gyros` reports `OutdatedTable` and
`FieldWithPathNotFound` — that is the base mod's own ritual table, not part of this work.
