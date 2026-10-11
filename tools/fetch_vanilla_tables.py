"""Cache any vanilla table into .skilltree_cache, for read_vanilla_cache.load().

    py tools/fetch_vanilla_tables.py dilemmas rituals ...   (names WITHOUT the _tables suffix)

check_skill_trees.fetch() only pulls its own fixed VAN_TABLES list; this is the same call
with the list on the command line. Already-cached names are skipped. Needs RPFM open, and
pays the dependency rebuild once per run when anything is missing.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_skill_trees import _rpc, _call, CACHE

want = sys.argv[1:]
need = [t for t in want if not os.path.exists(os.path.join(CACHE, t + ".json"))]
if not need:
    sys.exit("all cached")
_rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "fetch_van", "version": "1"}})
_rpc("notifications/initialized", notify=True)
_call("set_game_selected", {"game_name": "warhammer_3", "rebuild_dependencies": True})
os.path.isdir(CACHE) or os.makedirs(CACHE)
for t in need:
    d = _call("get_tables_from_dependencies", {"value": t + "_tables"})
    rows = sum(len(rf["data"]["Decoded"]["DB"]["table"]["table_data"]) for rf in d["VecRFile"])
    open(os.path.join(CACHE, t + ".json"), "w", encoding="utf-8").write(json.dumps(d))
    print("%-45s %6d rows" % (t, rows))
