"""Structural audit of the Hashut's Legendary Lords skill trees.

Pulls the mod's skill tables out of the .pack and the matching vanilla tables out
of RPFM's dependency database, then checks the things RPFM diagnostics do not:
dangling references, grid collisions, unreachable nodes, duplicate skills inside
one tree, and the per-lord omissions that only show up by comparing lords.

Needs RPFM open (the MCP server at 127.0.0.1:45127 only exists while it runs).

    py tools/check_skill_trees.py [path\\to\\pack]

Vanilla tables are cached under .skilltree_cache/ - delete it after a game patch.
Exit 1 if anything is reported.
"""
import collections, glob, json, os, shutil, sys, urllib.error, urllib.request

URL = "http://127.0.0.1:45127/mcp"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # tools/ -> workspace root
CACHE = os.path.join(ROOT, ".skilltree_cache")
PACK = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    ROOT, "Modding Files", "Modpacks", "!aa_derpy_hashut_legendary_lords.pack")

VAN_TABLES = ["character_skill_nodes", "character_skills", "character_skill_node_links",
              "character_skill_node_sets", "character_skill_node_set_items",
              "effects", "ancillaries", "agent_subtypes", "campaign_effect_scopes"]

# ---------------------------------------------------------------- MCP client
_sid = [None]
_id = [0]

def _rpc(method, params=None, notify=False):
    body = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        body["params"] = params
    if not notify:
        _id[0] += 1
        body["id"] = _id[0]
    hdr = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if _sid[0]:
        hdr["Mcp-Session-Id"] = _sid[0]
    req = urllib.request.Request(URL, json.dumps(body).encode(), hdr)
    with urllib.request.urlopen(req, timeout=1800) as r:
        _sid[0] = _sid[0] or r.headers.get("Mcp-Session-Id")
        raw = r.read().decode("utf-8", "replace")
    if notify:
        return None
    out = None
    for line in raw.splitlines():          # responses are SSE; the last data: line wins
        if line.startswith("data:"):
            try:
                out = json.loads(line[5:].strip())
            except ValueError:
                pass
    return out if out is not None else json.loads(raw)

def _call(tool, args):
    r = _rpc("tools/call", {"name": tool, "arguments": args})
    res = r.get("result", {})
    if r.get("error") or res.get("isError"):   # rmcp reports tool failure inside a 200
        raise SystemExit("RPFM %s failed: %s" % (tool, json.dumps(r.get("error") or res)[:400]))
    txt = "".join(c.get("text", "") for c in res.get("content", []))
    try:
        return json.loads(txt)
    except ValueError:
        return txt

def fetch(dest):
    """Extract the pack's db/ + text/ as TSV and cache the vanilla tables."""
    need_van = [t for t in VAN_TABLES if not os.path.exists(os.path.join(CACHE, t + ".json"))]
    try:
        _rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                            "clientInfo": {"name": "check_skill_trees", "version": "1"}})
    except urllib.error.URLError:
        raise SystemExit("RPFM is not running - its MCP server only exists while RPFM is open.")
    _rpc("notifications/initialized", notify=True)
    # dependency state is per-MCP-session, so this must happen in the same run
    _call("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": bool(need_van)})
    _call("open_packfiles", {"paths": [PACK]})
    _call("extract_packed_files", {
        "pack_key": PACK,
        "source_paths": json.dumps({"PackFile": [{"Folder": "db"}, {"Folder": "text"}]}),
        "destination_path": dest, "export_as_tsv": True})
    os.path.isdir(CACHE) or os.makedirs(CACHE)
    for t in need_van:
        d = _call("get_tables_from_dependencies", {"value": t + "_tables"})
        rows = sum(len(rf["data"]["Decoded"]["DB"]["table"]["table_data"]) for rf in d["VecRFile"])
        if not rows:                      # an unloaded dependency db answers empty, never errors
            raise SystemExit("vanilla %s came back empty - dependency database did not load" % t)
        open(os.path.join(CACHE, t + ".json"), "w", encoding="utf-8").write(json.dumps(d))

# ---------------------------------------------------------------- loaders
def tsv(ex, folder, root="db"):
    rows = []
    for p in sorted(glob.glob(os.path.join(ex, root, folder, "*.tsv"))):
        lines = open(p, encoding="utf-8").read().splitlines()
        cols = lines[0].split("\t")
        for ln in lines[1:]:
            if ln.startswith("#") or not ln.strip():
                continue
            v = ln.split("\t")
            v += [""] * (len(cols) - len(v))
            r = dict(zip(cols, v))
            r["_src"] = os.path.basename(p)
            rows.append(r)
    return rows

def van(name):
    d = json.load(open(os.path.join(CACHE, name + ".json"), encoding="utf-8"))
    out = []
    for rf in d["VecRFile"]:
        t = rf["data"]["Decoded"]["DB"]["table"]
        names = [f["name"] for f in t["definition"]["fields"]]
        for row in t["table_data"]:
            out.append({n: list(c.values())[0] for n, c in zip(names, row)})
    return out

def num(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return 0

# ---------------------------------------------------------------- the audit
def audit(ex):
    m_sets = tsv(ex, "character_skill_node_sets_tables")
    m_items = tsv(ex, "character_skill_node_set_items_tables")
    m_nodes = tsv(ex, "character_skill_nodes_tables")
    m_links = tsv(ex, "character_skill_node_links_tables")
    m_skills = tsv(ex, "character_skills_tables")
    m_eff = tsv(ex, "character_skill_level_to_effects_junctions_tables")
    m_anc = tsv(ex, "character_skill_level_to_ancillaries_junctions_tables")

    node = {n["key"]: n for n in van("character_skill_nodes")}
    node.update({n["key"]: n for n in m_nodes})
    skill = {s["key"]: s for s in van("character_skills")}
    skill.update({s["key"]: s for s in m_skills})

    links = collections.defaultdict(list)
    seen = set()
    for l in van("character_skill_node_links") + m_links:
        k = (l["child_key"], l["parent_key"])
        if k not in seen:
            seen.add(k)
            links[l["child_key"]].append(l["parent_key"])

    items = collections.defaultdict(list)
    for it in m_items + van("character_skill_node_set_items"):
        items[it["set"]].append(it["item"])

    loc = {}
    for p in glob.glob(os.path.join(ex, "text", "*.tsv")):
        for ln in open(p, encoding="utf-8").read().splitlines()[1:]:
            f = ln.split("\t")
            if not ln.startswith("#") and len(f) >= 2:
                loc[f[0]] = f[1]

    eff_keys = {e["effect"] for e in van("effects")}
    eff_keys |= {r["effect"] for r in tsv(ex, "effects_tables")}
    scopes = {s["key"] for s in van("campaign_effect_scopes")}
    anc_keys = {a["key"] for a in van("ancillaries")} | {r["key"] for r in tsv(ex, "ancillaries_tables")}
    sub_keys = {s["key"] for s in van("agent_subtypes")} | {r["key"] for r in tsv(ex, "agent_subtypes_tables")}

    found = []
    def F(sev, where, msg):
        found.append((sev, where, msg))

    sets = [s["key"] for s in m_sets]
    in_a_set = set()
    for sk in sets:
        mem = items[sk]
        for k, c in collections.Counter(mem).items():
            if c > 1:
                F("WARN", sk, "node listed %d times in the set: %s" % (c, k))
        mem = list(dict.fromkeys(mem))
        memset = set(mem)
        in_a_set |= memset
        for k in mem:
            if k not in node:
                F("ERR", sk, "set item points at a node that does not exist: %s" % k)
        present = [k for k in mem if k in node]

        for k in present:
            s = node[k].get("character_skill_key", "")
            if s and s not in skill:
                F("ERR", sk, "node %s -> missing skill %s" % (k, s))

        cell = collections.defaultdict(list)
        for k in present:
            cell[(num(node[k].get("tier")), num(node[k].get("indent")))].append(k)
        for (t, ind), ks in sorted(cell.items()):
            if len(ks) > 1:
                F("ERR", sk, "row %d slot %d holds %d nodes: %s" % (ind, t, len(ks), ", ".join(sorted(ks))))

        dup = collections.Counter(node[k].get("character_skill_key") for k in present)
        for s, c in dup.items():
            if c > 1 and s:
                on = sorted(k for k in present if node[k].get("character_skill_key") == s)
                F("ERR", sk, "skill %s sits on %d nodes in one tree: %s" % (s, c, ", ".join(on)))

        for k in present:
            ps = links.get(k, [])
            outside = sorted({p for p in ps if p not in memset})
            inside = [p for p in ps if p in memset]
            req = num(node[k].get("required_num_parents"))
            if ps and not inside:
                F("ERR", sk, "%s unreachable - every parent is outside this set (%s)" % (k, ", ".join(outside)))
            elif outside:
                F("WARN", sk, "%s has parent(s) outside this set: %s" % (k, ", ".join(outside)))
            if req > len(inside):
                F("ERR", sk, "%s needs %d parents, only %d in set - never unlockable" % (k, req, len(inside)))
            if req == 0 and len(ps) > 1:
                # 0 means literally zero, not "all parents" - the panel prints the number and
                # refuses the node. Vanilla: 0 in none of 1,933 four-parent nodes.
                F("ERR", sk, "%s has %d parents but required_num_parents = 0 - the panel says "
                             "'available after spending 0 points' and never unlocks it" % (k, len(ps)))
            for p in ps:
                if p in memset and num(node[p].get("tier")) >= num(node[k].get("tier")):
                    F("ERR", sk, "link %s -> %s does not advance (slot %d -> %d)"
                      % (p, k, num(node[p].get("tier")), num(node[k].get("tier"))))
        if not [k for k in present if num(node[k].get("tier")) == 0]:
            F("ERR", sk, "no slot-0 node in the set")

    # nodes CA puts in almost every lord tree - a modded lord without one is missing a stock skill
    v_sets = {s["key"] for s in van("character_skill_node_sets") if s.get("agent_key") == "general"}
    v_items = collections.defaultdict(set)
    for it in van("character_skill_node_set_items"):
        if it["set"] in v_sets:
            v_items[it["set"]].add(it["item"])
    v_count = collections.Counter(k for mem in v_items.values() for k in mem)
    for k, c in v_count.items():
        if c < 0.95 * len(v_sets):
            continue
        for sk in sets:
            if k not in set(items[sk]):
                F("WARN", sk, "lacks %s, which %d of vanilla's %d lord trees carry"
                  % (k, c, len(v_sets)))

    for n in m_nodes:
        if n["key"] not in in_a_set:
            F("WARN", "_pack", "node %s (%s) is in no node set - it never appears in game"
              % (n["key"], n["_src"]))
    for tbl in ("character_skills_tables", "character_skill_nodes_tables"):
        for k, c in collections.Counter(r["key"] for r in tsv(ex, tbl)).items():
            if c > 1:
                F("ERR", "_pack", "%s defines %s %d times across fragments" % (tbl, k, c))

    # character_skills.unlocked_at_rank does not gate on its own: the game reads the rank off a
    # character_skill_level_details row for level 1. 946 of vanilla's 1,036 non-zero-rank skills
    # carry both. Set only the former and the skill is buyable the moment its parents are, which
    # lets a lord walk a whole tree as soon as he has the points for it.
    gated = {d["skill_key"] for d in tsv(ex, "character_skill_level_details_tables")
             if num(d.get("level")) == 1}
    for s in m_skills:
        if num(s.get("unlocked_at_rank")) > 0 and s["key"] not in gated:
            F("ERR", "_pack", "%s sets unlocked_at_rank %s but has no character_skill_level_details "
                              "level-1 row - the rank is never enforced"
              % (s["key"], s["unlocked_at_rank"]))

    # a value whose sign fights the effect's is_positive_value_good is a malus wearing a skill icon
    good = {e["effect"]: str(e.get("is_positive_value_good")).lower() for e in van("effects")}
    good.update({r["effect"]: str(r.get("is_positive_value_good")).lower() for r in tsv(ex, "effects_tables")})

    eff_of = collections.defaultdict(list)
    for e in m_eff:
        eff_of[e["character_skill_key"]].append(e)
        g, v = good.get(e["effect_key"]), num(e["value"])
        if g == "false" and v > 0:
            F("WARN", "_pack", "%s: %s %s - positive is BAD for this effect"
              % (e["character_skill_key"], e["effect_key"], e["value"]))
        elif g == "true" and v < 0:
            F("WARN", "_pack", "%s: %s %s - positive is GOOD for this effect"
              % (e["character_skill_key"], e["effect_key"], e["value"]))
        if e["effect_key"] not in eff_keys:
            F("ERR", "_pack", "%s -> unknown effect %s" % (e["character_skill_key"], e["effect_key"]))
        if e["effect_scope"] not in scopes:
            F("ERR", "_pack", "%s -> unknown effect_scope %s" % (e["character_skill_key"], e["effect_scope"]))
    anc_of = collections.defaultdict(list)
    for a in m_anc:
        anc_of[a["skill"]].append(a)
        if a["granted_ancillary"] not in anc_keys:
            F("ERR", "_pack", "skill %s grants unknown ancillary %s" % (a["skill"], a["granted_ancillary"]))
    for s in m_sets:
        st = s["agent_subtype_key"]
        if st and st not in sub_keys:
            F("ERR", "_pack", "node set %s -> unknown agent_subtype %s" % (s["key"], st))
    for st, c in collections.Counter(s["agent_subtype_key"] for s in m_sets if s["agent_subtype_key"]).items():
        if c > 1:
            F("ERR", "_pack", "agent_subtype %s has %d node sets - only one applies" % (st, c))

    for s in m_skills:
        k = s["key"]
        if not eff_of[k] and not anc_of[k]:
            F("ERR", "_pack", "skill %s (%s) grants no effect and no ancillary" % (k, s["_src"]))
        if "character_skills_localised_name_" + k not in loc and not s.get("localised_name"):
            F("ERR", "_pack", "skill %s has no name loc and no inline name" % k)
        if "character_skills_localised_description_" + k not in loc and not s.get("localised_description"):
            F("WARN", "_pack", "skill %s has no description loc - empty tooltip" % k)
        if not s.get("image_path"):
            F("WARN", "_pack", "skill %s has no image_path" % k)

    return found, sets

def main():
    dest = os.path.join(CACHE, "extract")
    shutil.rmtree(dest, ignore_errors=True)
    fetch(dest)
    found, sets = audit(dest)
    for where in sets + ["_pack"]:
        rows = [f for f in found if f[1] == where]
        if rows:
            print("\n== %s" % where)
            for sev, _, msg in sorted(rows):
                print("  [%s] %s" % (sev, msg))
    errs = sum(1 for f in found if f[0] == "ERR")
    print("\n%d finding(s): %d ERR, %d WARN" % (len(found), errs, len(found) - errs))
    return 1 if found else 0

if __name__ == "__main__":
    sys.exit(main())
