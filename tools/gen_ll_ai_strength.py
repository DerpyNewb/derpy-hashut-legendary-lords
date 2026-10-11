# -*- coding: utf-8 -*-
"""Raise the HLL lords to the vanilla Chaos Dwarf legendary-lord stat floor.

Why: a lord's auto-resolve contribution is its combat potential, and every one of these
lords already sits in a `*_highvalue` ai_usage_group carrying vanilla's +1000 additive
bonus (autoresolver_ai_usage_group_combat_potential_modifiers). The group wiring is
correct, so the only remaining lever on AI-side strength is the stat block itself.

Floors are DERIVED from the vanilla rows in .skilltree_cache, never hardcoded, so a game
patch that rebalances Astragoth/Zhatan/Drazhoath moves the floor with it. Re-run after a
patch; `--check` needs no RPFM.

    py tools/gen_ll_ai_strength.py --check      # write TSVs + print the diff, no RPFM
    py tools/gen_ll_ai_strength.py --selftest   # assert the clamp rules
    py tools/gen_ll_ai_strength.py              # same as --check (import is a separate step)

Clamp rules, in the order they apply:
  1. Foot rows      -> element-wise MIN across the three vanilla CHD foot LLs.
  2. Mounted rows   -> the vanilla CHD LL row for that same mount type. Mounting LOWERS
                       melee defence in vanilla (Zhatan 55 on foot, 28 on a great taurus),
                       so the foot floor must NOT be applied to a mounted row.
  3. Mount types with no vanilla LL analogue (Gordak's giant wolf) -> the same absolute
     increases the lord's foot row received, so mounting never becomes a downgrade.
  4. Melee weapons (foot lords only) -> total damage clamped to the vanilla foot floor
     total, splitting the increase in the weapon's OWN damage:ap ratio, so a low-ap
     caster weapon does not silently turn into an armour-shredder.

Only `derpy_*` weapons are touched. The mounted rows point at CA's own monster weapons
(wh3_dlc23_chd_mon_*), which are vanilla keys and are left alone.
"""
import csv, io, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".skilltree_cache")
OUT = os.path.join(ROOT, "Modding Files", "source", "ll_ai_strength")

PACK = os.path.join(ROOT, "Modding Files", "Modpacks",
                    "!aa_derpy_hashut_legendary_lords.pack")

# The three vanilla Chaos Dwarf legendary lords, on foot.
VAN_FOOT = [
    "wh3_dlc23_chd_cha_astragoth_ironhand",
    "wh3_dlc23_chd_cha_zhatan_the_black",
    "wh3_dlc23_chd_cha_drazhoath_the_ashen",
]
# Their mounted rows, keyed by the mount type our own keys are suffixed with.
VAN_MOUNT = {
    "bale_taurus":  "wh3_dlc23_chd_cha_drazhoath_the_ashen_bale_taurus_cinderbreath",
    "great_taurus": "wh3_dlc23_chd_cha_zhatan_the_black_great_taurus",
    "lammasu":      "wh3_dlc23_chd_cha_zhatan_the_black_lammasu",
}

# Columns clamped upward. armour is an FK, handled through its armour_value.
NUMERIC = ["melee_attack", "melee_defence", "bonus_hit_points", "morale", "charge_bonus"]

TABLES = {
    "land_units_base":  "db/land_units_tables/derpy_chd_ll_base",
    "land_units_mount": "db/land_units_tables/derpy_chd_ll_mounts",
    "melee_weapons":    "db/melee_weapons_tables/derpy_chd_ll",
}


# ---------------------------------------------------------------- vanilla cache

def _loadall(name):
    """Every row of a cached vanilla table, across all of CA's files for it.

    read_vanilla_cache.load() reads VecRFile[0] only; factions and land_units are split
    over several files, so a single-file read silently returns a partial table.
    """
    path = os.path.join(CACHE, name + ".json")
    if not os.path.exists(path):
        sys.exit("not cached: %s\n  py tools/fetch_vanilla_tables.py %s" % (name, name))
    blob = json.load(io.open(path, encoding="utf-8"))
    rows = []
    for rf in blob["VecRFile"]:
        tbl = rf["data"]["Decoded"]["DB"]["table"]
        fields = [f["name"] for f in tbl["definition"]["fields"]]
        for r in tbl["table_data"]:
            cells = [list(c.values())[0] if isinstance(c, dict) and len(c) == 1 else c
                     for c in r]
            rows.append(dict(zip(fields, cells)))
    return rows


def vanilla_floors():
    lu = {r["key"]: r for r in _loadall("land_units")}
    mw = {r["key"]: r for r in _loadall("melee_weapons")}
    arm = {r["key"]: int(r["armour_value"]) for r in _loadall("unit_armour_types")}

    def block(key):
        r = lu[key]
        w = mw[r["primary_melee_weapon"]]
        d = {c: int(r[c]) for c in NUMERIC}
        d["armour_value"] = arm[r["armour"]]
        d["armour_key"] = r["armour"]
        d["weapon_total"] = int(w["damage"]) + int(w["ap_damage"])
        return d

    foot = {}
    for key in VAN_FOOT:
        b = block(key)
        for c, v in b.items():
            if c == "armour_key":
                continue
            foot[c] = v if c not in foot else min(foot[c], v)
    # the armour RECORD that defines the floor, so a raised lord lands on a real vanilla key
    foot["armour_key"] = next(b["armour_key"] for b in (block(k) for k in VAN_FOOT)
                              if b["armour_value"] == foot["armour_value"])
    mounts = {m: block(k) for m, k in VAN_MOUNT.items()}
    return foot, mounts, arm


# ---------------------------------------------------------------------- tsv i/o

def read_tsv(path):
    """RPFM TSV: line 1 header, line 2 the #table;version;path metadata, then rows."""
    with io.open(path, encoding="utf-8", newline="") as fh:
        raw = list(csv.reader(fh, delimiter="\t"))
    crlf = io.open(path, "rb").read().find(b"\r\n") != -1
    return raw[0], raw[1], [r for r in raw[2:] if r and r[0]], crlf


def write_tsv(path, header, meta, rows, crlf):
    """Join on tabs by hand. csv.writer would quote a cell containing a quote character;
    RPFM's own export never quotes, and a quoted cell imports as literal quote marks."""
    os.path.isdir(os.path.dirname(path)) or os.makedirs(os.path.dirname(path))
    nl = "\r\n" if crlf else "\n"
    body = nl.join("\t".join(r) for r in [header, meta] + list(rows))
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(body + nl)


# --------------------------------------------------------------------- clamping

def mount_type(key):
    for m in VAN_MOUNT:
        if key.endswith("_" + m):
            return m
    return None


def clamp_row(row, floor, arm, changes, label):
    """Raise row toward floor in place. Returns the absolute deltas applied."""
    delta = {}
    for c in NUMERIC:
        cur, flo = int(row[c]), floor[c]
        if cur < flo:
            delta[c] = flo - cur
            changes.append((label, row["key"], c, cur, flo))
            row[c] = str(flo)
    cur_arm = arm.get(row["armour"])
    if cur_arm is not None and cur_arm < floor["armour_value"]:
        changes.append((label, row["key"], "armour", row["armour"], floor["armour_key"]))
        delta["armour_key"] = floor["armour_key"]
        row["armour"] = floor["armour_key"]
    return delta


def apply_delta(row, delta, changes, label):
    """Push the foot row's own increases into a mount with no vanilla LL analogue."""
    for c in NUMERIC:
        if c in delta:
            cur = int(row[c]) + delta[c]
            changes.append((label, row["key"], c, row[c], cur))
            row[c] = str(cur)
    # the foot row already resolved an armour record; reuse it rather than resolving a
    # second time, so a lord and his mount do not end up on different armour audio types
    if delta.get("armour_key") and delta["armour_key"] != row["armour"]:
        changes.append((label, row["key"], "armour", row["armour"], delta["armour_key"]))
        row["armour"] = delta["armour_key"]


def clamp_weapon(row, total_floor, changes):
    dmg, ap = int(row["damage"]), int(row["ap_damage"])
    tot = dmg + ap
    if tot >= total_floor or tot <= 0:
        return
    scale = float(total_floor) / tot
    new_d, new_a = int(round(dmg * scale)), int(round(ap * scale))
    # rounding can land a point under; give the shortfall to the larger half
    short = total_floor - (new_d + new_a)
    if short:
        if new_d >= new_a:
            new_d += short
        else:
            new_a += short
    changes.append(("weapon", row["key"], "damage", dmg, new_d))
    changes.append(("weapon", row["key"], "ap_damage", ap, new_a))
    row["damage"], row["ap_damage"] = str(new_d), str(new_a)


# ------------------------------------------------------------------------- main

def build(src_dir):
    """Clamp every table. Returns {name: (header, meta, rows, crlf)} and the change list."""
    foot, mounts, arm = vanilla_floors()
    out, changes = {}, []

    hdr, meta, rows, crlf = read_tsv(os.path.join(src_dir, "ll_land_units.tsv"))
    base = [dict(zip(hdr, r)) for r in rows]
    deltas = {}
    for r in base:
        deltas[r["key"]] = clamp_row(r, foot, arm, changes, "foot")
    out["land_units_base"] = (hdr, meta, [[r[c] for c in hdr] for r in base], crlf)

    hdr, meta, rows, crlf = read_tsv(os.path.join(src_dir, "ll_land_units_mounts.tsv"))
    mrows = [dict(zip(hdr, r)) for r in rows]
    for r in mrows:
        mt = mount_type(r["key"])
        if mt:
            clamp_row(r, mounts[mt], arm, changes, "mount:" + mt)
        else:
            # no vanilla LL rides this; carry the lord's own foot increase across
            lord = max((k for k in deltas if r["key"].startswith(k + "_")), key=len,
                       default=None)
            if lord and deltas[lord]:
                apply_delta(r, deltas[lord], changes, "mount:derived")
    out["land_units_mount"] = (hdr, meta, [[r[c] for c in hdr] for r in mrows], crlf)

    hdr, meta, rows, crlf = read_tsv(os.path.join(src_dir, "ll_melee_weapons.tsv"))
    wrows = [dict(zip(hdr, r)) for r in rows]
    for r in wrows:
        clamp_weapon(r, foot["weapon_total"], changes)
    out["melee_weapons"] = (hdr, meta, [[r[c] for c in hdr] for r in wrows], crlf)

    return out, changes, foot, mounts


def selftest():
    foot, mounts, arm = vanilla_floors()
    assert foot["melee_attack"] == 45, foot
    assert foot["melee_defence"] == 50, foot
    assert foot["armour_value"] == 125 and foot["armour_key"] == "wh2_main_plate_125", foot
    assert foot["morale"] == 85, foot
    assert foot["weapon_total"] == 430, foot
    # mounting lowers melee defence in vanilla - the foot floor must not reach a mount
    assert mounts["great_taurus"]["melee_defence"] == 28 < foot["melee_defence"]

    ch = []
    r = {"key": "t", "melee_attack": "30", "melee_defence": "70", "bonus_hit_points": "100",
         "morale": "10", "charge_bonus": "0", "armour": "wh2_main_leather_50"}
    d = clamp_row(r, foot, arm, ch, "t")
    assert r["melee_attack"] == "45", r          # raised
    assert r["melee_defence"] == "70", r         # already above floor, untouched
    assert r["armour"] == "wh2_main_plate_125", r
    assert d["melee_attack"] == 15, d
    assert d["armour_key"] == "wh2_main_plate_125", d

    # a derived mount inherits the foot row's increases AND its exact armour record
    m = {"key": "t_wolf", "melee_attack": "50", "melee_defence": "58",
         "bonus_hit_points": "4260", "morale": "65", "charge_bonus": "50",
         "armour": "wh2_main_leather_50"}
    apply_delta(m, d, ch, "t")
    assert m["armour"] == "wh2_main_plate_125", m
    assert m["melee_attack"] == "65", m           # 50 + the foot row's +15
    assert m["melee_defence"] == "58", m          # foot row was above floor, so no delta

    # weapon split preserves the ratio and hits the total exactly
    w = {"key": "w", "damage": "100", "ap_damage": "200"}
    clamp_weapon(w, 430, ch)
    assert int(w["damage"]) + int(w["ap_damage"]) == 430, w
    assert int(w["ap_damage"]) > int(w["damage"]), w   # ap-heavy weapon stays ap-heavy
    w2 = {"key": "w2", "damage": "200", "ap_damage": "50"}
    clamp_weapon(w2, 430, ch)
    assert int(w2["damage"]) + int(w2["ap_damage"]) == 430, w2
    assert int(w2["damage"]) > int(w2["ap_damage"]), w2  # and a low-ap weapon stays low-ap
    # a weapon already at or above the floor is left exactly alone
    w3 = {"key": "w3", "damage": "250", "ap_damage": "380"}
    clamp_weapon(w3, 430, ch)
    assert (w3["damage"], w3["ap_damage"]) == ("250", "380"), w3

    assert mount_type("derpy_ghorth_bale_taurus") == "bale_taurus"
    assert mount_type("derpy_gordak_giant_wolf") is None
    print("selftest OK")


def main():
    if "--selftest" in sys.argv:
        return selftest()
    src = os.path.join(ROOT, "Modding Files", "source", "ll_ai_strength", "_export")
    if not os.path.isdir(src):
        sys.exit("export the three tables to %s first (see the handoff)" % src)
    out, changes, foot, mounts = build(src)

    print("vanilla CHD LL foot floor: MA %(melee_attack)s MD %(melee_defence)s "
          "armour %(armour_key)s HP %(bonus_hit_points)s morale %(morale)s "
          "charge %(charge_bonus)s weapon-total %(weapon_total)s" % foot)
    print()
    print("%-16s %-26s %-18s %-12s -> %s" % ("SCOPE", "KEY", "COLUMN", "WAS", "NOW"))
    for scope, key, col, was, now in changes:
        print("%-16s %-26s %-18s %-12s -> %s" % (scope, key, col, was, now))
    print("\n%d cell changes across %d tables" % (len(changes), len(out)))

    for name, (hdr, meta, rows, crlf) in out.items():
        p = os.path.join(OUT, name + ".tsv")
        write_tsv(p, hdr, meta, rows, crlf)
        print("wrote", p)


if __name__ == "__main__":
    main()
