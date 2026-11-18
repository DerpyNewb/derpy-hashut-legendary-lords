"""Cache any vanilla table into .skilltree_cache, for read_vanilla_cache.load().

    py tools/fetch_vanilla_tables.py dilemmas rituals ...   (names WITHOUT the _tables suffix)

check_skill_trees.fetch() only pulls its own fixed VAN_TABLES list; this is the same call
with the list on the command line. Already-cached names are skipped. Needs rpfm_server (it starts
itself) with its vanilla data loaded - rpfm_client.ensure_game(deps=True) loads it, and rebuilds RPFM's
dependency cache first only when that cache is outdated.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_skill_trees import CACHE
from rpfm_client import ensure_game, vanilla_table

want = sys.argv[1:]
need = [t for t in want if not os.path.exists(os.path.join(CACHE, t + ".json"))]
if not need:
    sys.exit("all cached")
ensure_game(deps=True)
os.path.isdir(CACHE) or os.makedirs(CACHE)
for t in need:
    d = vanilla_table(t + "_tables")
    rows = sum(len(rf["data"]["Decoded"]["DB"]["table"]["table_data"]) for rf in d["VecRFile"])
    open(os.path.join(CACHE, t + ".json"), "w", encoding="utf-8").write(json.dumps(d))
    print("%-45s %6d rows" % (t, rows))
