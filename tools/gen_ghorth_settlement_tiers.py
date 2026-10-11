# -*- coding: utf-8 -*-
"""Generate the settlement-tier pass in Ghorth's four start scripts.

STALE as of 2026-10-03 - do not write with it. The shipped scripts gained Ghorth's diplomacy
block (DIPLO_FRIENDS) and the MCT reads (derpy_ghorth_world_start, derpy_hll_setting) after
this was last run, and HEAD carries neither, so a write deletes both. Bring HEAD up to date
from the shipped file first. See docs/sessions/HANDOFF_20261003_HLL_MCT_SETTINGS.md.

    py tools\\gen_ghorth_settlement_tiers.py            # write the four staged .lua files
    py tools\\gen_ghorth_settlement_tiers.py --check    # report only, write nothing
    py tools\\gen_ghorth_settlement_tiers.py --selftest # run the generated Lua under lua.exe

wh3_dlc23_chd_conclave's settlements come out of the startpos and no DB row in a pack
reaches them, so they are levelled by script at first tick. Setting the settlement itself is
easy; capping the buildings *around* it is not, because the gate is
`building_levels.primary_slot_building_building_level_requirement` and no runtime interface
exposes it - BUILDING_SCRIPT_INTERFACE offers name/chain/building_level and nothing else.

Two traps that make the obvious shortcuts wrong:

  * The `_N` key suffix is NOT the level. Settlement chains carry a `_ruin` row at level 0,
    so `wh3_dlc23_chd_settlement_tower_3` really is level 3 - but secondary chains have no
    ruin row, so `wh3_dlc23_chd_military_kdaai_3` is level **2**. Deriving a key by
    rewriting the suffix works on the settlement and silently misses every building beside it.
  * The requirement is not the suffix either. `wh3_dlc23_chd_military_kdaai_3` and
    `wh3_dlc23_chd_military_war_machines_3` both need a tier **5** capital, while
    `wh3_dlc23_chd_factory_refinery_3` needs tier 3. Capping on the displayed numeral leaves
    K'daai and war-machine recruitment standing on a tier 3 city.

So the chain table is emitted from the vanilla DB and the clamp is a lookup. Scope is the 85
chains of `wh3_dl23_bas_chd`, the Chaos Dwarf availability set - every chd-named chain plus
the special/landmark chains a Chaos Dwarf region can hold (the Great Drills, the four
fortress gates, the ports).

Re-run after a game patch that touches building_levels; delete .skilltree_cache first.
"""
import io, os, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from read_vanilla_cache import load

PACK = r"G:\Modding for resources\Modding Files\pack\script\campaign"
FILES = [
    r"cr_oldworld\mod\derpy_start_ghorth.lua",
    r"cr_darklands\mod\derpy_start_ghorth.lua",
    r"cr_combi_expanded\mod\ime_derpy_ghorth.lua",
    r"wh3_main_combi\mod\ime_derpy_ghorth.lua",
]
ANCHOR = "function derpy_ghorth_replace_1()"
TAIL = '        out("XXX derpy_ghorth Finished XXX");'
# Tiers first, then the stockpiles, so the stock pass has the last word and lands on the exact
# target whatever the settlement work did or did not move.
CALLS = ["derpy_ghorth_settlement_tiers", "derpy_ghorth_starting_stock"]
CALL = "".join("        %s();\n" % c for c in CALLS)
AVAILABILITY_SET = "wh3_dl23_bas_chd"
LUA = r"C:\Program Files (x86)\Lua\5.1\lua.exe"

CAPITAL_TIER = 3
MINOR_TIER = 2

# Startpos gave 25,500 / 10,700 / 3,990 / 50 at turn 1. Tune here.
START_TREASURY = 10000

# (pool, target, factor to spend through, factor to grant through). The two factors are not
# interchangeable - pooled_resource_factor_junctions bounds most of them to one direction, and
# an amount of the wrong sign clamps to nothing in silence. --selftest asserts the bounds.
START_POOLS = [
    ("wh3_dlc23_chd_raw_materials", 2500,
     "wh3_dlc23_chd_consumed", "wh3_dlc23_chd_mined"),
    ("wh3_dlc23_chd_armaments", 1000,
     "events", "events"),
    ("wh3_dlc23_chd_conclave_influence", 0,
     "wh3_dlc23_chd_conclave_influence_spent_events",
     "wh3_dlc23_chd_conclave_influence_gained_events"),
]


def chain_levels():
    """{chain: [(key, level, primary_tier_required)]} ascending by level, CHD chains only."""
    avail, _ = load("building_chain_availability_sets")
    wanted = set(r["building_chain"] for r in avail if r["id"] == AVAILABILITY_SET)
    assert wanted, "availability set %s not in the cache" % AVAILABILITY_SET

    rows, _ = load("building_levels")
    out = {}
    for r in rows:
        if r["chain"] in wanted:
            out.setdefault(r["chain"], []).append(
                (r["level_name"], int(r["level"]),
                 int(r["primary_slot_building_building_level_requirement"])))
    for c in out:
        out[c].sort(key=lambda t: (t[1], t[0]))
    missing = wanted - set(out)
    assert not missing, "chains with no levels: %s" % sorted(missing)
    return out


def clamp(levels, key, want):
    """Mirror of the shipped Lua. None = leave alone, `key` = nothing lower exists, else
    the replacement key."""
    chain = None
    for c, ls in levels.items():
        if any(l[0] == key for l in ls):
            chain = c
    if chain is None:
        return None
    ls = levels[chain]
    cur = [i for i, l in enumerate(ls) if l[0] == key][0]
    if ls[cur][2] <= want:
        return None
    for i in range(cur - 1, -1, -1):
        if ls[i][2] <= want:
            return ls[i][0]
    return key


def settlement_level(levels, chain, want):
    ls = levels.get(chain)
    if not ls:
        return None
    best = None
    for key, lvl, req in ls:
        if lvl == want:
            return key
        if req <= want:
            best = key
    return best


def render(levels):
    body = []
    for chain in sorted(levels):
        cells = ",".join('{"%s",%d,%d}' % t for t in levels[chain])
        body.append('\t["%s"]={%s},' % (chain, cells))
    pools = "\n".join('\t{"%s", %d, "%s", "%s"},' % p for p in START_POOLS)
    return HEAD % ("\n".join(body), CAPITAL_TIER, MINOR_TIER, START_TREASURY, pools)


HEAD = '''-- Starting settlement tiers for wh3_dlc23_chd_conclave.
--
-- GENERATED by tools/gen_ghorth_settlement_tiers.py - do not hand-edit the table below.
-- Re-run that script after a game patch that touches building_levels.
--
-- The Conclave's settlements are set in the startpos and no DB row in a pack reaches them,
-- so they are levelled here at first tick: province capitals (and the home region, in case
-- the Conclave ever holds only a minor) to CAPITAL_TIER, every other region to MINOR_TIER.
--
-- The settlement itself is SET - a capital that starts above the target comes down, a minor
-- below it goes up. Every OTHER building in the region is only ever CAPPED, never handed out
-- and never destroyed: a tier 3 capital that keeps its tier 5 K'daai pit is still a tier 5
-- start, but a landmark whose chain has no lower rung is left standing rather than razed.
--
-- The cap cannot be computed at runtime. It lives in
-- building_levels.primary_slot_building_building_level_requirement and no script interface
-- exposes it, so CHAIN_LEVELS is {key, level, required primary tier} for the 85 chains of
-- the Chaos Dwarf availability set. Two things it exists to get right, both of which defeat
-- the obvious shortcuts: the _N suffix is not the level (secondary chains have no _ruin row,
-- so wh3_dlc23_chd_military_kdaai_3 is level 2), and the numeral is not the requirement
-- (that same _3 needs a tier 5 capital, while wh3_dlc23_chd_factory_refinery_3 needs 3).
--
-- grep the log for: derpy_ghorth tiers
local CHAIN_LEVELS = {
%s
}

local CONCLAVE = "wh3_dlc23_chd_conclave"

-- Tune the two numbers here. Anything 1-5 works without regenerating the table.
local CAPITAL_TIER = %d
local MINOR_TIER   = %d

-- What to do in the CAPITAL with a building the clamp cannot bring down - a one-level chain
-- whose requirement is above the tier. At CAPITAL_TIER 3 that is the req-5 specials sitting on
-- Zharr-Naggrund: wh3_dlc23_chd_tower_temple_of_hashut_1 and
-- wh3_dlc23_special_great_temple_of_hashut_chd. true razes them, which is the point - a tier 3
-- capital keeping its tier 5 temple is still a tier 5 start.
--
-- It is deliberately capital-only. The same rule in a MINOR at tier 2 would take out every
-- wh3_dlc23_chd_resource_*_1 (req 3) and every landmark the Conclave holds, and destroying a
-- region's gem mine is not what was asked for. Minors keep and log instead.
--
-- Reversible in game: a razed one-level building comes back from the construction list once
-- the settlement climbs to its required tier again.
local RAZE_UNCLAMPED_IN_CAPITAL = true

-- Starting stockpiles, measured on the deployed build at turn 1: 25,500 gold at +4,489 a
-- turn, 10,700 raw materials, 3,990 armaments, 50 conclave influence. None of that is ours -
-- no script in this pack calls treasury_mod at all, and all 18 faction_add_pooled_resource
-- calls in it belong to the Tower of Zharr or the drill chain. It is CA's startpos for a
-- background faction nobody was meant to play, and the startpos is out of reach of the DB,
-- so it is corrected here.
--
-- Set, not subtracted: the delta is measured against the live value, so this lands on the
-- same number whatever the startpos or the difficulty handed out, and re-reading it after a
-- patch costs nothing.
local START_TREASURY = %d

-- {pool, target, factor to spend through, factor to grant through}
--
-- Two factors per pool because a pooled_resource_factor_junctions row carries its own
-- minimum/maximum and most are one-way: wh3_dlc23_chd_consumed is capped at max 0 and
-- wh3_dlc23_chd_mined at min 0, so pushing an amount of the wrong sign through either one
-- clamps to nothing with no error anywhere. Bounds read from the DB, not guessed.
local START_POOLS = {
%s
}

local function derpy_ghorth_starting_stock()
\tlocal faction = cm:get_faction(CONCLAVE)
\tif not faction or faction:is_null_interface() then
\t\tout("XXX derpy_ghorth stock ABORT - no Conclave in this campaign XXX")
\t\treturn
\tend

\tlocal gold = faction:treasury()
\tif gold ~= START_TREASURY then
\t\tcm:treasury_mod(CONCLAVE, START_TREASURY - gold)
\t\tout("XXX derpy_ghorth stock treasury "..gold.." -> "..START_TREASURY.." XXX")
\tend

\tlocal manager = faction:pooled_resource_manager()
\tif not manager or manager:is_null_interface() then
\t\tout("XXX derpy_ghorth stock SKIP pools - faction has no pooled resource manager XXX")
\t\treturn
\tend

\tfor i = 1, #START_POOLS do
\t\tlocal key    = START_POOLS[i][1]
\t\tlocal target = START_POOLS[i][2]
\t\tlocal pool   = manager:resource(key)
\t\tif not pool or pool:is_null_interface() then
\t\t\tout("XXX derpy_ghorth stock SKIP "..key.." - not a pool on this faction XXX")
\t\telse
\t\t\tlocal have  = pool:value()
\t\t\tlocal delta = target - have
\t\t\tif delta == 0 then
\t\t\t\tout("XXX derpy_ghorth stock "..key.." already "..target.." XXX")
\t\t\telse
\t\t\t\tlocal factor = START_POOLS[i][3]
\t\t\t\tif delta > 0 then factor = START_POOLS[i][4] end
\t\t\t\tcm:faction_add_pooled_resource(CONCLAVE, key, factor, delta)
\t\t\t\tout("XXX derpy_ghorth stock "..key.." "..have.." -> "..target.." (via "..factor..") XXX")
\t\t\tend
\t\tend
\tend
end

local KEY_TO_CHAIN = {}
for chain, levels in pairs(CHAIN_LEVELS) do
\tfor i = 1, #levels do
\t\tKEY_TO_CHAIN[levels[i][1]] = chain
\tend
end

-- What this building should become once the settlement sits at tier `want`. Returns nil to
-- leave the slot alone - an unknown building, or one already legal at that tier, since this
-- only ever takes buildings down - `key` itself when the building is above the tier but its
-- chain has nothing lower, or the replacement key.
--
-- That middle case is the landmarks, and it must NOT dismantle. A one-level chain like
-- wh3_dlc23_special_great_temple_of_hashut_chd needs a tier 5 capital and has no lower rung,
-- so clamping it would mean destroying the landmark with no way to put it back until the
-- settlement is tier 5 again. The engine leaves landmarks standing through settlement damage
-- and so do we; the caller logs each one instead.
local function derpy_ghorth_clamp(key, want)
\tlocal chain = KEY_TO_CHAIN[key]
\tif not chain then return nil end
\tlocal levels = CHAIN_LEVELS[chain]
\tlocal cur = nil
\tfor i = 1, #levels do
\t\tif levels[i][1] == key then cur = i end
\tend
\tif not cur or levels[cur][3] <= want then return nil end
\tfor i = cur - 1, 1, -1 do
\t\tif levels[i][3] <= want then return levels[i][1] end
\tend
\treturn key
end

-- The primary settlement building for `chain` at tier `want`: the entry whose own level is
-- `want`, falling back to the highest that tier allows. Unlike the clamp this raises as well
-- as lowers, because the settlement is set to the tier rather than capped by it.
local function derpy_ghorth_settlement_level(chain, want)
\tlocal levels = CHAIN_LEVELS[chain]
\tif not levels then return nil end
\tlocal best = nil
\tfor i = 1, #levels do
\t\tif levels[i][2] == want then return levels[i][1] end
\t\tif levels[i][3] <= want then best = levels[i][1] end
\tend
\treturn best
end

local function derpy_ghorth_settlement_tiers()
\tlocal faction = cm:get_faction(CONCLAVE)
\tif not faction or faction:is_null_interface() then
\t\tout("XXX derpy_ghorth tiers ABORT - no Conclave in this campaign XXX")
\t\treturn
\tend

\tlocal home = ""
\tif faction:has_home_region() then
\t\thome = faction:home_region():name()
\tend

\tlocal regions = faction:region_list()
\tfor i = 0, regions:num_items() - 1 do
\t\tlocal region     = regions:item_at(i)
\t\tlocal want       = MINOR_TIER
\t\tlocal is_capital = false
\t\tif region:is_province_capital() or region:name() == home then
\t\t\twant       = CAPITAL_TIER
\t\t\tis_capital = true
\t\tend

\t\t-- The settlement first, so the slot list read below is the post-downgrade one: a
\t\t-- capital dropping from 5 to 3 deactivates slots, and a list taken before that is stale.
\t\tlocal primary = region:settlement():primary_slot()
\t\tlocal pb      = primary:building()
\t\tif not pb or pb:is_null_interface() then
\t\t\tout("XXX derpy_ghorth tiers "..region:name().." has no settlement building XXX")
\t\telse
\t\t\tlocal have   = pb:name()
\t\t\tlocal target = derpy_ghorth_settlement_level(KEY_TO_CHAIN[have], want)
\t\t\tif not target then
\t\t\t\t-- Building keys fail silently, so never mint one by guess.
\t\t\t\tout("XXX derpy_ghorth tiers SKIP "..region:name().." - "..have.." is not in a known chain XXX")
\t\t\telseif target == have then
\t\t\t\tout("XXX derpy_ghorth tiers "..region:name().." settlement already "..have.." XXX")
\t\t\telse
\t\t\t\tif pb:building_level() > want then
\t\t\t\t\tcm:region_slot_instantly_dismantle_building(primary)
\t\t\t\tend
\t\t\t\tcm:region_slot_instantly_upgrade_building(primary, target)
\t\t\t\tout("XXX derpy_ghorth tiers "..region:name().." settlement "..have.." -> "..target.." XXX")
\t\t\tend
\t\tend

\t\tlocal slots = region:slot_list()
\t\tfor s = 0, slots:num_items() - 1 do
\t\t\tlocal slot = slots:item_at(s)
\t\t\tlocal b    = slot:building()
\t\t\tif b and not b:is_null_interface() then
\t\t\t\tlocal have   = b:name()
\t\t\t\tlocal target = derpy_ghorth_clamp(have, want)
\t\t\t\tif target == have then
\t\t\t\t\tif is_capital and RAZE_UNCLAMPED_IN_CAPITAL then
\t\t\t\t\t\tcm:region_slot_instantly_dismantle_building(slot)
\t\t\t\t\t\tout("XXX derpy_ghorth tiers "..region:name().." RAZED "..have.." - needs a higher tier than "..want.." and its chain has no lower level XXX")
\t\t\t\t\telse
\t\t\t\t\t\tout("XXX derpy_ghorth tiers "..region:name().." KEPT "..have.." - above tier "..want.." but its chain has no lower level XXX")
\t\t\t\t\tend
\t\t\t\telseif target then
\t\t\t\t\tcm:region_slot_instantly_dismantle_building(slot)
\t\t\t\t\tcm:region_slot_instantly_upgrade_building(slot, target)
\t\t\t\t\tout("XXX derpy_ghorth tiers "..region:name().." "..have.." -> "..target.." XXX")
\t\t\t\tend
\t\t\tend
\t\tend

\t\tcm:heal_garrison(region:cqi())
\tend
end

'''


def selftest():
    levels = chain_levels()
    print("chains %d, levels %d" % (len(levels), sum(len(v) for v in levels.values())))

    # The Python mirror, against rows read straight out of the cache.
    cases = [
        # key                                        want  expected
        ("wh3_dlc23_chd_military_kdaai_3",           3, "wh3_dlc23_chd_military_kdaai_2"),
        ("wh3_dlc23_chd_military_kdaai_3",           2, "wh3_dlc23_chd_military_kdaai_1"),
        ("wh3_dlc23_chd_military_war_machines_3",    3, "wh3_dlc23_chd_military_war_machines_2"),
        ("wh3_dlc23_chd_factory_refinery_3",         3, None),   # req 3, already legal
        ("wh3_dlc23_chd_factory_refinery_1",         3, None),   # never raise
        ("wh3_dlc23_chd_settlement_tower_5",         3, "wh3_dlc23_chd_settlement_tower_3"),
        ("wh2_main_special_fortress_gate_eagle_chd_5", 3, None), # req 0, legal at any tier
        ("wh_main_dwf_military_1",                   3, None),   # not a CHD chain
        # One-level landmarks: above the tier, nothing lower, must be KEPT not razed.
        ("wh3_dlc23_special_great_temple_of_hashut_chd", 3,
         "wh3_dlc23_special_great_temple_of_hashut_chd"),
        ("wh3_dlc23_chd_resource_gems_1",            2, "wh3_dlc23_chd_resource_gems_1"),
    ]
    for key, want, expect in cases:
        got = clamp(levels, key, want)
        assert got == expect, (key, want, got, expect)

    scases = [
        ("wh3_dlc23_chd_settlement_tower", 3, "wh3_dlc23_chd_settlement_tower_3"),
        ("wh3_dlc23_chd_settlement_outpost", 2, "wh3_dlc23_chd_settlement_outpost_2"),
        ("wh3_dlc23_chd_settlement_factory", 2, "wh3_dlc23_chd_settlement_factory_2"),
    ]
    for chain, want, expect in scases:
        got = settlement_level(levels, chain, want)
        assert got == expect, (chain, want, got, expect)

    # Two invariants over every level of every chain, at every tier:
    #   a replacement must itself be legal at that tier, and
    #   "keep" must mean there really was nothing lower to drop to.
    req = {}
    chain_of = {}
    for chain, ls in levels.items():
        for key, _lvl, r in ls:
            req[key] = r
            chain_of[key] = chain
    kept = 0
    for key in req:
        for want in range(1, 6):
            got = clamp(levels, key, want)
            if got is None:
                continue
            if got == key:
                assert req[key] > want, (key, want)
                ls = levels[chain_of[key]]
                cur = [i for i, l in enumerate(ls) if l[0] == key][0]
                assert all(l[2] > want for l in ls[:cur]), (key, want)
                kept += 1
            else:
                assert req[got] <= want, (key, want, got, req[got])
    print("python mirror OK (%d clamp probes, %d keeps)" % (len(req) * 5, kept))

    # Pooled-resource factors, against pooled_resource_factor_junctions. A factor bounded the
    # wrong way clamps the transaction to nothing and logs nothing, so this is the only place
    # the mistake is visible before a campaign runs.
    junc, _ = load("pooled_resource_factor_junctions")
    bounds = {(r["resource"], r["factor"]): (int(r["minimum"]), int(r["maximum"]))
              for r in junc}
    for pool, target, down, up in START_POOLS:
        assert (pool, down) in bounds, "no junction row for %s x %s" % (pool, down)
        assert (pool, up) in bounds, "no junction row for %s x %s" % (pool, up)
        assert bounds[(pool, down)][0] < 0, ("spend factor is not negative-capable", pool, down)
        assert bounds[(pool, up)][1] > 0, ("grant factor is not positive-capable", pool, up)
        assert target >= 0, (pool, target)
    print("pooled-resource factors OK (%d pools)" % len(START_POOLS))

    # And the shipped Lua, run for real - the prefix is side-effect free by construction.
    src = io.open(os.path.join(PACK, FILES[0]), encoding="utf-8", newline="").read()
    assert ANCHOR in src, "generate the scripts first"
    prefix = src.split(ANCHOR)[0]
    harness = prefix + "\nreturn derpy_ghorth_clamp, derpy_ghorth_settlement_level\n"
    fd, path = tempfile.mkstemp(suffix=".lua")
    os.close(fd)
    probe = path + ".probe.lua"
    io.open(path, "w", encoding="utf-8", newline="\n").write(harness)
    checks = "\n".join(
        'assert(c(%r, %d) == %s, %r)' % (
            k, w, ("nil" if e is None else ("false" if e is False else repr(e).replace("'", '"'))), k)
        for k, w, e in cases)
    checks += "\n" + "\n".join(
        'assert(s(%r, %d) == %s, %r)' % (c, w, repr(e).replace("'", '"'), c)
        for c, w, e in scases)
    io.open(probe, "w", encoding="utf-8", newline="\n").write(
        'local c, s = dofile(%s)\n%s\nprint("lua OK")\n'
        % (repr(path.replace("\\", "\\\\")).replace("'", '"'), checks))
    r = subprocess.run([LUA, probe], capture_output=True, text=True)
    os.remove(path)
    os.remove(probe)
    if r.returncode != 0:
        raise SystemExit("lua selftest FAILED:\n%s%s" % (r.stdout, r.stderr))
    print("shipped lua OK:", r.stdout.strip())
    print("selftest passed")


def main():
    if "--selftest" in sys.argv:
        return selftest()

    levels = chain_levels()
    head = render(levels)
    print("chains %d, levels %d, generated prefix %d B"
          % (len(levels), sum(len(v) for v in levels.values()), len(head)))

    for rel in FILES:
        p = os.path.join(PACK, rel)
        src = io.open(p, encoding="utf-8", newline="").read()
        assert ANCHOR in src, rel
        assert src.count(TAIL) == 1, (rel, src.count(TAIL))
        # Drop any call lines a previous run left, then re-insert the canonical set, so the
        # generator is idempotent across changes to CALLS.
        body = src[src.index(ANCHOR):]
        for c in CALLS:
            body = body.replace("        %s();\n" % c, "")
        body = body.replace(TAIL, CALL + TAIL)
        out = head + body
        if out == src:
            print("  unchanged  %s" % rel)
            continue
        if "--check" in sys.argv:
            print("  WOULD WRITE %s  %d -> %d B" % (rel, len(src), len(out)))
            continue
        io.open(p, "w", encoding="utf-8", newline="").write(out)
        print("  wrote      %s  %d -> %d B" % (rel, len(src), len(out)))


if __name__ == "__main__":
    main()
