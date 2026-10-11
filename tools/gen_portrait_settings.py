"""Write the portrait_settings entries a MINTED campaign_character_art_sets id needs.

A character's porthole is not in the database. `campaign_character_arts.portrait` and `.card` are
empty on every vanilla row; the image is a pre-rendered PNG resolved through
`ui/portraits/portholes/portrait_settings__.bin` (and its `ui/portraits/units/` twin), a binary
keyed by **art_set_id**. Mint a new art set id and no portrait settings file anywhere mentions it,
so every panel draws the placeholder - with no error, no log line and nothing in the DB to fix.
Reusing CA's art set id is not an option either: `art_set_id` is that table's primary key.

That is what put a placeholder on Tordrek's Gunnery Wight (since dropped for CA's own subtype) and
what still sits under the Fleetmaster's three art sets. This clones CA's Overseer blocks under our
ids, changing only the id, so the Fleetmaster wears the Overseer's porthole - the same model his
`campaign_character_arts` row already dresses him in.

    py tools/gen_portrait_settings.py            write the .bin under Modding Files/source
    py tools/gen_portrait_settings.py --selftest round-trip CA's four files and ours, byte for byte

Format, after a zstd frame with a u32 uncompressed-size prefix (CA compresses, we do not):

    u32 version (4), u32 entry count, then per entry:
      u16 len + ascii art_set_id
      5 x f32 body camera, u16+attachment bone, u8 has_head_camera
      [5 x f32 head camera, u16+attachment bone]   present only when that flag is 1
      u32 variant count, then per variant:
        u16+name, u16+png, u16+mask1, u16+mask2, u16+spare   (length 0 when absent)

Two traps. The attachment bone is empty on almost every entry, so its two zero bytes read as
padding right up until wh2_dlc16_art_set_wef_sisters_of_twilight, entry 264 of 1,402, which names
"shoulder_pad_left" and desynchronises everything after it. And a variant carries FIVE strings, so
one with no masks ends in six zero bytes, not four - stop at four and the next entry is rubbish.

Built 2026-09-02. See docs/sessions/HANDOFF_20260902_NAVAL_HORDE_LIVE_VERIFY.md section 11.
"""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = r"F:\SteamLibrary\steamapps\common\Total War WARHAMMER III\data"
OURS = os.path.join(ROOT, "Modding Files", "Modpacks",
                    "!aa_derpy_hashut_legendary_lords.pack")

# Where the new file is staged. import_naval_horde.py --lua walks this root and adds every file
# under it at its relative path, so the folders below ARE the in-pack path.
STAGE = os.path.join(ROOT, "Modding Files", "source", "naval_horde", "pack")
# CA ships portrait_settings__.bin BYTE-IDENTICAL in both folders - the png paths inside always
# read "UI/Portraits/Portholes/...", so it is the folder the file sits in that picks the render,
# not the content. Ship the same bytes twice for the same reason.
OUT = ["ui/portraits/portholes/portrait_settings_derpy_naval_horde.bin",
       "ui/portraits/units/portrait_settings_derpy_naval_horde.bin"]

# The Fleetmaster. His campaign_character_arts rows already point at the Overseer's uniforms, so
# the porthole that belongs to him is the Overseer's - one donor per art set, in order.
CLONES = [("derpy_chd_admiral_%02d" % i, "wh3_dlc23_art_set_chd_overseer_%02d" % i)
          for i in (1, 2, 3)]


def _str(b, o):
    n, = struct.unpack_from("<H", b, o)
    return b[o + 2:o + 2 + n].decode("ascii"), o + 2 + n


def _put(s):
    e = s.encode("ascii")
    return struct.pack("<H", len(e)) + e


def parse(b):
    """(version, [entry]) where entry is (art_set_id, cam_body, cam_head or None, [variant]).

    A camera is (5 floats, attachment bone, flag); the head camera has no flag of its own.
    """
    ver, count = struct.unpack_from("<II", b, 0)
    o = 8
    entries = []
    for _ in range(count):
        key, o = _str(b, o)
        floats = struct.unpack_from("<5f", b, o)
        o += 20
        bone, o = _str(b, o)
        flag = b[o]
        o += 1
        body = (floats, bone, flag)
        head = None
        if flag:
            floats = struct.unpack_from("<5f", b, o)
            o += 20
            bone, o = _str(b, o)
            head = (floats, bone)
        n, = struct.unpack_from("<I", b, o)
        o += 4
        variants = []
        for _ in range(n):
            strings = []
            for _ in range(5):
                s, o = _str(b, o)
                strings.append(s)
            variants.append(strings)
        entries.append((key, body, head, variants))
    assert o == len(b), "parsed %d of %d bytes - the format moved" % (o, len(b))
    return ver, entries


def dump(ver, entries):
    out = bytearray(struct.pack("<II", ver, len(entries)))
    for key, body, head, variants in entries:
        out += _put(key)
        out += struct.pack("<5f", *body[0]) + _put(body[1]) + bytes([body[2]])
        if head is not None:
            out += struct.pack("<5f", *head[0]) + _put(head[1])
        out += struct.pack("<I", len(variants))
        for strings in variants:
            for s in strings:
                out += _put(s)
    return bytes(out)


def read_settings(pack, path):
    """The decoded bytes of one portrait settings file, CA's zstd frame unwrapped if present."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from read_pack_index import read
    hits = read(pack, path)
    assert hits, "%s does not ship %s" % (pack, path)
    _p, compression, data = hits[0]
    if not compression:
        return data
    import zstandard
    size, = struct.unpack("<I", data[:4])
    return zstandard.ZstdDecompressor().decompress(data[4:], max_output_size=size)


def build():
    """(version, entries) for our file: CA's Overseer blocks under the Fleetmaster's ids."""
    ver, entries = parse(read_settings(os.path.join(GAME, "ui.pack"),
                                       "ui/portraits/portholes/portrait_settings__.bin"))
    by_key = {e[0]: e for e in entries}
    out = []
    for mine, donor in CLONES:
        assert donor in by_key, "no portrait settings entry for %s" % donor
        _k, body, head, variants = by_key[donor]
        assert variants, "%s has no image - cloning it would change nothing" % donor
        out.append((mine, body, head, variants))
    return ver, out


def check():
    ver, entries = build()
    assert len(entries) == len(CLONES)
    for (mine, donor), (key, _b, _h, variants) in zip(CLONES, entries):
        assert key == mine
        pngs = [s for strings in variants for s in strings if s.endswith(".png")]
        assert pngs, "%s cloned no png path" % mine
        for p in pngs:
            assert p.lower().startswith("ui/portraits/portholes/"), \
                "%s points outside the portholes folder: %s" % (mine, p)

    # The art set ids must be the ones the DB mints, or the file names something that never renders.
    art = os.path.join(ROOT, "Modding Files", "source", "naval_horde", "export",
                       "zz_campaign_character_art_sets.tsv")
    with open(art, encoding="utf-8") as fh:
        cols = fh.readline().rstrip("\n").split("\t")
        fh.readline()
        minted = {r.split("\t")[cols.index("art_set_id")] for r in fh if r.strip()}
    van = {e[0] for e in parse(read_settings(os.path.join(GAME, "ui.pack"),
                                             "ui/portraits/portholes/portrait_settings__.bin"))[1]}
    ours = {k for k, _d in CLONES}
    assert ours <= minted, "art set ids not in campaign_character_art_sets: %s" % sorted(ours - minted)
    assert not ours & van, "art set id collides with a vanilla portrait settings entry"
    # Anything minted and not covered here (or by the LL file) draws a placeholder.
    ll = {e[0] for e in parse(read_settings(
        OURS, "ui/portraits/portholes/portrait_settings_derpy_hashut_ll.bin"))[1]}
    naked = minted - ours - ll - van
    assert not naked, "minted art sets with no porthole entry: %s" % sorted(naked)
    print("checks ok: %d entries, %d minted art sets all covered" % (len(entries), len(minted)))
    return ver, entries


def selftest():
    """Round-trip every portrait settings file on this machine, byte for byte."""
    files = [(os.path.join(GAME, "ui.pack"), "ui/portraits/portholes/portrait_settings__.bin"),
             (os.path.join(GAME, "ui.pack"), "ui/portraits/units/portrait_settings__.bin"),
             (os.path.join(GAME, "ui_3.pack"), "ui/portraits/portholes/portrait_settings__3.bin"),
             (os.path.join(GAME, "ui_3.pack"), "ui/portraits/units/portrait_settings__3.bin"),
             (OURS, "ui/portraits/portholes/portrait_settings_derpy_hashut_ll.bin")]
    for pack, path in files:
        raw = read_settings(pack, path)
        ver, entries = parse(raw)
        assert dump(ver, entries) == raw, "round trip changed %s" % path
        print("  round trip ok: %-46s v%d, %d entries, %d bytes"
              % (path.rsplit("/", 1)[-1], ver, len(entries), len(raw)))

    # A masked entry and a bare one must both survive, since they differ by four bytes and an
    # off-by-one there is silent until the entry AFTER it comes out as rubbish.
    raw = read_settings(os.path.join(GAME, "ui.pack"),
                        "ui/portraits/portholes/portrait_settings__.bin")
    _v, entries = parse(raw)
    masked = [e for e in entries if any(s.endswith("_mask1.png") for st in e[3] for s in st)]
    bare = [e for e in entries if all(not s for st in e[3] for s in st[2:])]
    assert masked and bare, "expected both masked and unmasked entries in CA's file"
    heads = [e for e in entries if e[2] is not None]
    bones = [e for e in entries if e[1][1] or (e[2] and e[2][1])]
    assert heads, "expected at least one entry with a head camera"
    assert bones, "expected at least one entry with a named attachment bone"
    print("  shapes covered: %d masked, %d bare, %d with a head camera, %d with a bone (%s)"
          % (len(masked), len(bare), len(heads), len(bones), bones[0][0]))

    check()
    print("selftest ok")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return
    ver, entries = check()
    blob = dump(ver, entries)
    for out in OUT:
        dest = os.path.join(STAGE, *out.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as fh:
            fh.write(blob)
        print("wrote %s (%d bytes)" % (out, len(blob)))
    for key, _b, _h, variants in entries:
        print("  %-24s %s" % (key, variants[0][1]))


if __name__ == "__main__":
    main()
