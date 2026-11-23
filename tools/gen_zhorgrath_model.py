"""Zhorgrath the Reaver's model, from NorscanWarlord's own Workshop packs, into !!!derpy_chd_assets.

    body   chd_warrior/chd_overseer_of_hashut_05          NorscanWarlord Variants (3783054159)
    head   chd_zealots_of_hashut/chd_overseer_of_hashut_head_05
    axe    chd_props/chd_zhorgrath_axe                    Zhorgrath the Reaver Weapon (3841687503)
    shield chd_props/chd_zhorgrath_shield

The collaborator's own chd_overseer_campaign_10_war definition is this body and head; the weapon
pack is the axe and shield made for him. Everything the four .wsmodel files reach (materials, then
textures) is traced, and every file that comes from the collaborator's packs is copied into
`variantmeshes/wh_variantmodels/hu3/chd/norscanwarlord_zhorgrath/` under a `norscanwarlord_` name,
lowercase (6.1+ crashes on uppercase pack paths), with every reference to it rewritten. So
subscribing to both mods never puts two different files on one path. Files the chain reaches in
CA's packs or our own assets pack are referenced where they are. Four of the collaborator's
files override CA paths with different bytes (Drazhoath's masks and two materials); those are
copied too, since without their pack the CA version would draw.

    py tools/gen_zhorgrath_model.py            trace, build, check, write the staging folder
    py tools/gen_zhorgrath_model.py --import <assets pack path>   then add the files, save, verify
    py tools/gen_zhorgrath_model.py --selftest prove check() catches a dangling or uppercase path

Staging: Modding Files/source/norscanwarlord_zhorgrath/pack/ (pack layout). The lord's DB rows
name `norscanwarlord_zhorgrath` (gen_new_house_lords.py LORDS["mesh"]).
"""
import glob
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import read_pack_index as rpi                                   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = r"F:\SteamLibrary\steamapps\workshop\content\1142710"
SOURCES = [("weapon", WS + r"\3841687503\!ZhorgrathTheReaverWeapon.pack"),
           ("norscan", WS + r"\3783054159\!!!!!!!!!!NorscanWarlordVariants.pack")]
ASSETS = WS + r"\3297605217\!!!derpy_chd_assets.pack"
GAME = r"F:\SteamLibrary\steamapps\common\Total War WARHAMMER III\data"
OUT = os.path.join(ROOT, "Modding Files", "source", "norscanwarlord_zhorgrath", "pack")

NAME = "norscanwarlord_zhorgrath"
PREFIX = "norscanwarlord_"
DIR = "variantmeshes/wh_variantmodels/hu3/chd/%s/" % NAME
VMD = "variantmeshes/variantmeshdefinitions/%s.variantmeshdefinition" % NAME
SRC = "variantmeshes/wh_variantmodels/hu3/chd/"
PARTS = {"head": SRC + "chd_zealots_of_hashut/chd_overseer_of_hashut_head_05.wsmodel",
         "torso": SRC + "chd_warrior/chd_overseer_of_hashut_05.wsmodel",
         "axe": SRC + "chd_props/chd_zhorgrath_axe.wsmodel",
         "shield": SRC + "chd_props/chd_zhorgrath_shield.wsmodel"}
REF = re.compile(r"[A-Za-z0-9_ \-\\/\.]+\.(?:rigid_model_v2|wsmodel|xml\.material|dds)", re.I)


def norm(p):
    p = p.replace("\\", "/").strip().lower()
    return p[p.index("variantmeshes/"):] if "variantmeshes/" in p else p


def unpack(d):
    """A compressed pack entry: u32 size, then a zstd frame (the variants pack) or LZ4 (the weapon pack)."""
    body = d[4:]
    if body[:4] == bytes.fromhex("28b52ffd"):
        import zstandard
        return zstandard.ZstdDecompressor().decompress(body, max_output_size=int.from_bytes(d[:4], "little") + 16)
    if body[:4] == bytes.fromhex("04224d18"):
        import lz4.frame
        return lz4.frame.decompress(body)
    raise ValueError("unknown compression %r" % body[:4])


class Packs:
    """Lower-case path indexes of the collaborator's packs, our assets pack and every CA pack."""

    def __init__(self):
        self.src = [(n, fp, {p.lower(): p for p in rpi.paths(fp)}) for n, fp in SOURCES]
        self.assets = {p.lower() for p in rpi.paths(ASSETS)}
        self.ca = {}
        for fp in sorted(glob.glob(os.path.join(GAME, "*.pack"))):
            for p in rpi.paths(fp):
                self.ca.setdefault(p.lower(), []).append(fp)

    @staticmethod
    def read(fp, path):
        for p, c, d in rpi.read(fp, path):
            if p.lower() == path:
                return unpack(d) if c else d
        return None

    def collab(self, p):
        """(bytes) of the collaborator's copy of p, weapon pack first, or None."""
        for _n, fp, idx in self.src:
            if p in idx:
                return self.read(fp, idx[p])
        return None

    def ca_bytes(self, p):
        got = {self.read(fp, p) for fp in self.ca.get(p, [])}
        return got.pop() if len(got) == 1 else None

    def any_bytes(self, p):
        """What the collaborator's setup draws for p: their copy, else ours, else CA's."""
        d = self.collab(p)
        if d is None and p in self.assets:
            d = self.read(ASSETS, p)
        return d if d is not None else self.ca_bytes(p)


def refs(d):
    return [norm(m) for m in REF.findall(d.decode("utf-8"))]


def trace(packs):
    """{path: bytes or None} for every file the four parts reach; None = left where it is."""
    found, text, todo = {}, {}, list(PARTS.values())
    while todo:
        p = todo.pop(0)
        if p in found:
            continue
        mine = packs.collab(p)
        if mine is not None and p in packs.ca and packs.ca_bytes(p) == mine:
            mine = None                 # byte-identical to every CA copy: reference CA's
        found[p] = mine
        if p.endswith((".wsmodel", ".material")):
            d = mine if mine is not None else packs.any_bytes(p)
            if d:
                text[p] = d
                todo += refs(d)
    # A file left where it is that points at a path the collaborator OVERRIDES draws the other
    # version of that path without their pack - our Golden Legion material on his head reaches
    # Drazhoath's head mask, a 160-byte stub in CA's packs and a full mask in theirs. It comes along.
    grew = True
    while grew:
        grew = False
        for p, d in text.items():
            if found[p] is None and any(found.get(r) is not None and (r in packs.ca or r in packs.assets)
                                        for r in refs(d)):
                found[p], grew = d, True
    return found


def rename(found):
    """{old path: new path} for every file that is copied. Basenames are unique in one folder,
    so a clash (two different chd_fireborn materials) takes its source folder into the name."""
    sub = {".dds": "tex/", ".material": "materials/"}
    copied = sorted(p for p, d in found.items() if d is not None)
    base = lambda p: p.rsplit("/", 1)[1].replace(" - ", "_").replace(" ", "_")
    clash = {b for b in map(base, copied) if sum(base(q) == b for q in copied) > 1}
    out = {}
    for p in copied:
        b = base(p)
        if b in clash:
            b = p.split("/")[-3] + "_" + b      # .../<folder>/materials/<file>
        out[p] = DIR + next((v for k, v in sub.items() if p.endswith(k)), "") + PREFIX + b
    return out


def rewrite(text, names):
    """Every reference to a copied file, repointed; the slash style of the original is kept."""
    def one(m):
        new = names.get(norm(m.group(0)))
        if new is None:
            return m.group(0)
        return new.replace("/", "\\") if "\\" in m.group(0) else new
    return REF.sub(one, text)


def vmd(names):
    """Slots as CA's Overseer and the collaborator's chd_overseer_campaign_10_war: head, torso,
    the axe on be_prop_1, the shield on be_prop_2, CA's stumps."""
    w = lambda k: names[PARTS[k]].replace("/", "\\")
    stump = ('\t<SLOT name="%s" attach_point="%s" >\n\t\t<VARIANT_MESH model="VariantMeshes/wh_variantmodels/hu3/'
             'dlc02_blood_pack/dlc02_stump_%s_hu3.rigid_model_v2" >\n\t\t\t<META_DATA>equipment</META_DATA>\t\t\t'
             '<META_DATA>is_stump</META_DATA></VARIANT_MESH>\n\t</SLOT>\n')
    return ('<VARIANT_MESH>\n\t<META_DATA>equipment</META_DATA>\t<SLOT name="head" >\n'
            '\t\t<VARIANT_MESH model="%s" />\n\t</SLOT>\n'
            '\t<SLOT name="torso" >\n\t\t<VARIANT_MESH model="%s" >\n'
            '\t\t\t<META_DATA>audio_entity_type:wh3_dlc23_chd_overseer_LORD</META_DATA>\t\t\t'
            '<META_DATA>audio_armour_type:plate</META_DATA></VARIANT_MESH>\n\t</SLOT>\n'
            '\t<SLOT name="weapon_1" attach_point="be_prop_0" />\n'
            '\t<SLOT name="weapon_2" attach_point="be_prop_1" >\n\t\t<VARIANT_MESH model="%s" >\n'
            '\t\t\t<META_DATA>equipment</META_DATA>\t\t\t<META_DATA>audio_melee_weapon_type:axe</META_DATA>'
            '</VARIANT_MESH>\n\t</SLOT>\n'
            '\t<SLOT name="shield" attach_point="be_prop_2" >\n\t\t<VARIANT_MESH model="%s" >\n'
            '\t\t\t<META_DATA>audio_shield_type:metal</META_DATA></VARIANT_MESH>\n\t</SLOT>\n'
            '\t<SLOT name="weapon_3" attach_point="be_prop_3" />\n'
            '\t<SLOT name="weapon_4" attach_point="be_prop_4" />\n'
            '\t<SLOT name="weapon_5" attach_point="be_prop_5" />\n'
            % (w("head"), w("torso"), w("axe"), w("shield"))
            + "".join(stump % s for s in (("stump_neck", "spine_2", "neck"), ("stump_left_arm", "clav_left", "left_arm"),
                                          ("stump_right_arm", "clav_right", "right_arm"), ("stump_waist", "root", "waist"),
                                          ("stump_severed_head", "head", "head")))
            + "</VARIANT_MESH>\n")


def build(packs):
    """({pack path: bytes}, {old path: new path}) - the copied files, renamed and rewritten, plus
    the definition."""
    found = trace(packs)
    names = rename(found)
    out = {}
    for old, new in names.items():
        d = found[old]
        out[new] = rewrite(d.decode("utf-8"), names).encode("utf-8") if old.endswith((".wsmodel", ".material")) else d
    out[VMD] = vmd(names).encode("utf-8")
    return out, names


def check(files, packs, names):
    """Every path ours, lowercase and prefixed; every reference in every text file resolves to a
    file we ship, CA ships or our assets pack ships; none is left on the OLD path of a file we
    copied (the collaborator's own, or a CA/assets path they override - both draw the wrong file)."""
    bad = []
    for p in files:
        if p != p.lower() or not (p == VMD or (p.startswith(DIR) and p.rsplit("/", 1)[1].startswith(PREFIX))):
            bad.append("path not ours or not lowercase: " + p)
    for p, d in files.items():
        if not p.endswith((".wsmodel", ".material", ".variantmeshdefinition")):
            continue
        for m in REF.findall(d.decode("utf-8")):
            r = norm(m)
            if r in files:
                continue
            if r in names:
                bad.append("%s: %s still points at the copied file's old path" % (p, m))
            elif r not in packs.ca and r not in packs.assets:
                bad.append("%s: %s resolves nowhere" % (p, m))
    for k in PARTS.values():
        if not any(p.endswith(PREFIX + k.rsplit("/", 1)[1]) for p in files):
            bad.append("part not shipped: " + k)
    return bad


def write(files):
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for p, d in files.items():
        dest = os.path.join(OUT, *p.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(d)


def do_import(files, pack):
    from rpfm_client import call, ensure_game, open_pack
    ensure_game()
    key = open_pack(pack)
    srcs = [os.path.join(OUT, *p.split("/")) for p in files]
    call("add_files_from_disk", {"pack": key, "paths": srcs, "pack_paths": list(files)})
    call("save_pack", {"pack": key})
    call("close_pack", {"pack": key})
    _f, es = rpi.entries(pack)
    _f.close()
    have = {e[0].lower(): e for e in es}
    bad = [p for p in files if p not in have]
    # RPFM may compress on save; the uncompressed ones must match byte for byte
    for p, d in files.items():
        if p in have and not have[p][3]:
            got = [x for q, c, x in rpi.read(pack, p) if q.lower() == p][0]
            if got != d:
                bad.append("bytes differ: " + p)
    print("%d files in the saved pack, %d bad" % (len(files), len(bad)))
    for b in bad:
        print("  BAD " + b)
    return bad


def selftest():
    packs = Packs()
    files, names = build(packs)
    assert not check(files, packs, names), check(files, packs, names)
    k = next(p for p in files if p.endswith(".material") and b"commontextures/dither.dds" in files[p])
    broken = dict(files)
    broken[k] = files[k].replace(b"commontextures/dither.dds", b"commontextures/no_such_thing.dds")
    assert any("resolves nowhere" in b for b in check(broken, packs, names)), "dangling texture not caught"
    # every copied file's old path, put back in turn: each must be caught (the Drazhoath mask is
    # the case that matters - its old path exists, in CA's packs, as a 160-byte stub)
    for old, new in names.items():
        holder = next((p for p, d in files.items() if new.encode() in d.lower() or new.replace("/", "\\").encode() in d.lower()), None)
        if holder is None:
            continue
        broken = dict(files)
        broken[holder] = files[holder].replace(new.encode(), old.encode()).replace(
            new.replace("/", "\\").encode(), old.replace("/", "\\").encode())
        assert any("old path" in b for b in check(broken, packs, names)), "old path of %s not caught" % old
    broken = dict(files)
    broken[DIR + PREFIX + "Upper.dds"] = b""
    assert any("lowercase" in b for b in check(broken, packs, names)), "uppercase path not caught"
    print("selftest ok - %d files; a dangling texture, all %d old paths and an uppercase path caught"
          % (len(files), len(names)))


def main():
    if "--selftest" in sys.argv:
        return selftest()
    packs = Packs()
    files, names = build(packs)
    bad = check(files, packs, names)
    for b in bad:
        print("FAIL  " + b)
    if bad:
        raise SystemExit("%d finding(s) - nothing written" % len(bad))
    write(files)
    print("%d files, %.1f MB -> %s" % (len(files), sum(map(len, files.values())) / 1e6, OUT))
    if "--import" in sys.argv:
        pack = sys.argv[sys.argv.index("--import") + 1]
        sys.exit(1 if do_import(files, pack) else 0)


if __name__ == "__main__":
    main()
