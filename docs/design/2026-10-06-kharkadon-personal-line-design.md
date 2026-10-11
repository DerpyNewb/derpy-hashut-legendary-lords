# Kharkadon's personal skill line

2026-10-06. Design requested in chat; the user added Perfect Vigour to Stand With Your Overlord and then approved implementation. Built and verified in the lords pack; see the [implementation handoff](../../sessions/HANDOFF_20261006_KHARKADON_PERSONAL_LINE.md) for deployment and outstanding battle checks.

**Later correction, same day:** the user rejected enumerating the bodyguard ancillaries as skill targets. [Self-buff cleanup](../../sessions/HANDOFF_20261006_KHARKADON_SELF_BUFFS.md) supersedes the explicit bodyguard targets below: custom sets contain only regular troops, with native self counterparts for Kharkadon. Read that correction before regenerating this line.

## Skill contract

Keep the existing node keys, positions, prerequisites, levels and exclusive rank-24 choice. Replace the effects and text of these eight skills only. The lord trait, faction bundle, items, existing passive and bodyguard unlocks retain their current behavior.

| Suffix | Rank | Name | Effects |
|---|---:|---|---|
| `1` | 4 | First into the Breach | Kharkadon +8 melee attack; Chaos Dwarf melee infantry in his army +10% charge bonus. |
| `2_1` | 11 | Chosen of Zharrduk | Three levels: Infernal Guard, Ironsworn and Immortals upkeep -5/-10/-15%, experience gain +10/+20/+30%. |
| `2_2` | 11 | Plate and Oath | Three levels: Ironsworn, Immortals and all four equipped bodyguard forms melee defence +3/+6/+9, armour +5/+10/+15. |
| `2_3` | 11 | The Vicious | Three levels: Kharkadon armour-piercing weapon damage +5/+10/+15%, bonus versus infantry +3/+6/+9. |
| `2_4` | 11 | A Court of Veterans | Three levels: heroes recruited in his current province +1/+2/+3 rank; army leadership +2/+4/+6. |
| `4_1` | 24 | The Immortal Few | Ironsworn, Immortals and all four equipped bodyguard forms: Perfect Vigour and +10 percentage points physical resistance. Infernal Guard, Ironsworn and Immortals upkeep +15%. |
| `4_2` | 24 | Rule by the Axe | Kharkadon: Terror and +20% weapon strength. Hobgoblins and labourers in his army: -8 leadership. |
| `3` | 29 | Stand With Your Overlord | Unlock the active ability specified below. |

The suffix mapping deliberately puts The Vicious in the former Court slot (`2_3`) and A Court of Veterans in the former Gate Wardens slot (`2_4`), matching the proposed row order. Existing learned skills will take on the new meaning.

## Stand With Your Overlord

- Key: `derpy_kharkadon_stand_with_your_overlord`.
- Active area augment centred on Kharkadon's selected unit, including its bodyguard when equipped.
- Radius 35 metres; self and friendly units; no enemies; unlimited friendly targets.
- Duration 25 seconds; cooldown 120 seconds; unlimited uses.
- Grants +8 melee attack, +8 melee defence and Perfect Vigour (`fatigue_immune`) for the phase duration.
- Requires Kharkadon's unit to be engaged in melee. Use native DB activation/deactivation conditions, verified against the installed game's records. No battle script.
- The desired duration is up to 25 seconds while engaged in melee; if the only supported native mechanism cancels the phase on leaving melee, document that behavior in the tooltip. Do not invent an activation flag or silently drop the melee condition.
- Self receives the buff as well as allies. Permanent Perfect Vigour from The Immortal Few does not stack into a second benefit.
- Reuse an existing, visually verified ability icon.

Suggested tooltip: "While engaged in melee, Kharkadon grants himself and nearby allies +8 melee attack, +8 melee defence and Perfect Vigour for up to 25 seconds."

## Targets and balance

The regular Ironsworn (`wh3_dlc23_chd_inf_infernal_ironsworn`) and the Immortals RoR (`wh3_dlc23_chd_inf_infernal_ironsworn_ror`) are separate targets. All four bodyguard keys start `derpy_kharkadon_bg_`. For Infernal Guard family effects, include the appropriate bodyguard clones through verified unit-set membership; Warriors bodyguards receive only the explicit all-bodyguard buffs.

Personal damage and attribute effects must be checked on the solo lord and officer form. Do not substitute a whole-bodyguard damage buff for an officer-only benefit without a revised design: half-sized bodyguards were intentionally balanced around Kharkadon doing the killing.

Deathblow and Expert Charge Defence remain on the existing lord trait. Remove the former rank-24 army replenishment penalty and the former capstone's personal stat package. The new rank-24 upkeep penalty and leadership penalty are intentional.

## Ownership and preservation

Maintained source: `tools/gen_new_house_lords.py`; bodyguard source: `tools/gen_kharkadon_bodyguards.py`. Generated outputs: `Modding Files/source/hll_new_lords/` and `Modding Files/source/kharkadon_bodyguards/`. Destination: `Modding Files/Modpacks/!aa_derpy_hashut_legendary_lords.pack`. Last documented enabled copy: Workshop item `3432966208`, not a data-folder copy; verify current selection before deployment.

The 2026-10-06 rename makes `derpy_kharkadon` current. House keys still use `zharrduk`. The latest documented portraits are in the pack, not the old loose staging mirror. Implementation reconciled the generator's older base stats against the saved pack, preserving armour 130, attack 65, defence 60, shield 70 and weapon damage 230/250, together with the saved splash and weapon flags. Fresh extraction reproduces the saved baseline; do not replace it with older loose files.

## References

- [Initial elite-house redesign, section 8](../../sessions/HANDOFF_20261003_NEW_HOUSE_LORDS.md).
- [Bodyguards and officer limitations](../../sessions/HANDOFF_20261006_KHARKADON_BODYGUARDS_DESIGN.md).
- [Rename, portraits and generator drift, sections 5-6](../../sessions/HANDOFF_20261006_KHARKADON_TEXTURE_SRGB_AND_PORTRAITS.md).
- [Ability targeting and donors](../../ABILITIES.md).
- [Ability enable links and phase attributes](../../CUSTOM_ABILITIES.md).
- [Implementation plan](../plans/2026-10-06-kharkadon-personal-line.md).
