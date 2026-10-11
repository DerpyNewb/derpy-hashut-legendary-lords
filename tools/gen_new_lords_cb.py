"""Custom battle characters for the two lords gen_new_house_lords.py minted without one.

Every `units_custom_battle_permissions` general row names a `set_piece_character`, and that
`battle_set_piece_armies_characters` row is where custom battle reads the general's name,
model, portrait, lore and starting items. CA leaves none dangling (0 of 864 general rows);
the Overlord of Zharrduk and the Captain of the Uzkul Mingol shipped dangling on 2026-10-03.
Written as its own fragment, `derpy_hll_new_lords_cb`, because gen_new_house_lords.py does not
own the custom-battle character records. Shape is Gargath's row, the pack's own convention;
ids and portrait routing come from gen_new_house_lords.py.

    py tools/gen_new_lords_cb.py --check   # build, check against the pack export, write nothing
    py tools/gen_new_lords_cb.py --import  # write, import into the Modpacks pack, verify
    py tools/gen_new_lords_cb.py --dangling <pack export dir>   # the whole-pack check alone
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_zochaz as Z      # noqa: E402  (read_tsv, get_col, do_import, EX)
from gen_new_house_lords import custom_battle_portrait

FRAG = "derpy_hll_new_lords_cb"
OUT = os.path.join(Z.ROOT, "Modding Files", "source", "new_lords_cb")

# subtype: (forename, surname, arts id, [items]). Kharkadon wears CA's own names
# (gen_new_house_lords.py LORDS); the Captain's name is the placeholder 12412536.
LORDS = {
    "derpy_kharkadon": ("212779775", "318034614", "696991701",
                       ["derpy_kharkadon_weapon", "derpy_kharkadon_talisman"]),
    "derpy_uzkul": ("12412536", "", "696991702", ["derpy_uzkul_weapon", "derpy_uzkul_talisman"]),
}
CHARS, ITEMS = "battle_set_piece_armies_characters_tables", "battle_set_piece_armies_characters_items_tables"


def build():
    hdr, meta, _r = Z.read_tsv(os.path.join(Z.EX, "db", CHARS, "!!derpy_chd_legendary_lords.tsv"))
    ihdr, imeta, _r = Z.read_tsv(os.path.join(Z.EX, "db", ITEMS, "derpy_chd_ll_ancillary.tsv"))
    rows, irows = [], []
    for sub, (fore, sur, arts, items) in LORDS.items():
        rows.append("\t".join([sub, "5", fore, "", "1", sur, sub, "general", sub, custom_battle_portrait(sub), arts,
                               "", "true"]))
        irows += ["%s\t%s" % (i, sub) for i in items]
    assert hdr.split("\t")[:11] == ["character_name", "character_level", "forename", "magic_lore",
                                    "num_men", "surname", "unit_type", "agent_type",
                                    "agent_subtype", "portrait", "character_model"], hdr
    retag = lambda m, t: m.replace(m.split("\t")[0].split(";")[2], "db/%s/%s" % (t, FRAG))
    return {CHARS: (hdr, retag(meta, CHARS), rows), ITEMS: (ihdr, retag(imeta, ITEMS), irows)}


def _rows(ex, table):
    out = []
    for rel, t in Z.fragments(ex):
        if t == table:
            h, _m, rows = Z.read_tsv(os.path.join(ex, rel))
            out += [(h, r) for r in rows]
    return out


def dangling(ex, extra=None):
    """Custom battle generals of this pack whose set_piece_character does not exist."""
    chars = {r.split("\t")[0] for _h, r in _rows(ex, CHARS)}
    if extra:
        chars |= {r.split("\t")[0] for r in extra[CHARS][2]}
    bad = []
    for h, r in _rows(ex, "units_custom_battle_permissions_tables"):
        if Z.get_col(r, h, "general_unit") == "true" and Z.get_col(r, h, "set_piece_character") not in chars:
            bad.append("%s -> %s" % (Z.get_col(r, h, "unit"), Z.get_col(r, h, "set_piece_character")))
    return bad


def check(out):
    bad = []
    have = {t: {r.split("\t")[0] for _h, r in _rows(Z.EX, t)}
            for t in ("ancillaries_tables", "campaign_character_arts_tables", "land_units_tables",
                      "agent_subtypes_tables")}
    for sub, (_f, _s, arts, items) in LORDS.items():
        h, _m, rows = out[CHARS]
        if not any(Z.get_col(r, h, "character_name") == sub and
                   Z.get_col(r, h, "portrait") == custom_battle_portrait(sub) for r in rows):
            bad.append(sub + ": custom battle portrait does not match the lord's art")
        for t in ("land_units_tables", "agent_subtypes_tables"):
            if sub not in have[t]:
                bad.append("%s is not in the pack's %s" % (sub, t))
        if arts not in have["campaign_character_arts_tables"]:
            bad.append("%s: arts id %s is not in the pack" % (sub, arts))
        bad += ["%s: item %s is not in the pack" % (sub, i) for i in items if i not in have["ancillaries_tables"]]
    # only the Zochaz rows (built by gen_zochaz) may still be missing from a pre-Zochaz export
    bad += [d for d in dangling(Z.EX, out) if not d.startswith("derpy_zochaz")]
    return bad


def write(out):
    plan = []
    for t, (hdr, meta, rows) in out.items():
        rel = os.path.join(OUT, t, FRAG + ".tsv")
        os.makedirs(os.path.dirname(rel), exist_ok=True)
        with open(rel, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join([hdr, meta] + rows) + "\n")
        plan.append(("db/%s/%s" % (t, FRAG), rel, len(rows)))
    return plan


def main():
    if "--dangling" in sys.argv:
        bad = dangling(sys.argv[sys.argv.index("--dangling") + 1])
        print("\n".join(bad) or "no dangling custom battle characters")
        sys.exit(1 if bad else 0)
    out = build()
    bad = check(out)
    # the check has to be able to fail: drop one lord and it must report him
    assert any("derpy_uzkul" in d for d in dangling(Z.EX, {CHARS: (0, 0, out[CHARS][2][:1])})), \
        "dangling() did not report a lord left without a character"
    h, m, rows = out[CHARS]
    mutant = dict(out)
    mutant[CHARS] = (h, m, [Z.set_col(r, h, portrait="ui/portraits/portholes/no_culture/chd_overseer_campaign_01_0.png")
                            if Z.get_col(r, h, "character_name") == "derpy_kharkadon" else r for r in rows])
    assert any("portrait" in d for d in check(mutant)), "the old Overseer portrait was not caught"
    for b in bad:
        print("FAIL  " + b)
    if bad:
        sys.exit(1)
    print("ok - %d characters, %d items" % (len(out[CHARS][2]), len(out[ITEMS][2])))
    if "--check" in sys.argv:
        return
    plan = write(out)
    if "--import" in sys.argv:
        sys.exit(1 if Z.do_import(plan, [], frag=FRAG) else 0)


if __name__ == "__main__":
    main()
