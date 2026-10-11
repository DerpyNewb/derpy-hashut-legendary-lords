"""Character porthole (300x164) for a Hashut's Legendary Lords lord, from an in-game screenshot.

    py tools/gen_character_portrait.py <stem> <screenshot.png> --eyes LX,LY,RX,RY [--mirror]
    py tools/gen_character_portrait.py <stem> --derive [--gap 15] [--at 151,75] [--out-eyes LX,LY,RX,RY]
    py tools/gen_character_portrait.py <stem> --pack
    py tools/gen_character_portrait.py --selftest

Guide: docs/UNIT_CARDS.md section 6. <stem> is the porthole's file name, e.g. derpy_ghorth - the
name portrait_settings_derpy_hashut_ll.bin points at, which is NOT always the lord key
(derpy_urzkhal's file is derpy_urzhkal.png).

The character's pixels come from the screenshot, never from generation: Codex generating Ghorth
from scratch was rejected on 2026-10-05 as "doesn't look like the character at all". Codex
only cuts the background out (the porthole needs alpha) and evens the light. --eyes are the two
eye centres in the ORIGINAL screenshot; --mirror flips the screenshot and the coordinates.

Framing: eyes --gap px apart, centred on --at. Match the HEAD SIZE of the current porthole
by eye in compare.png, not its eye gap - Ghorth's old render measured 19-20 px between the eyes
but its visor was narrower, and 19 zoomed the new one in ~30%. 15 matched. --derive re-frames
the cached cut-out without calling Codex, so try a few.

Writes Modding Files/source/portraits/<stem>/: shot.png, meta.json, porthole_in.png (what Codex
was shown), porthole_out.png (its cut-out), porthole.png, compare.png. --pack replaces ONLY the
porthole in the HLL pack (backup first, byte round-trip after) and the staged copy.
"""
import datetime, glob, json, os, re, shutil, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageOps

sys.path.insert(0, os.path.dirname(__file__))
import read_pack_index as rpi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "Modding Files", "source", "portraits")
HLL = r"F:\SteamLibrary\steamapps\workshop\content\1142710\3432966208\!aa_derpy_hashut_legendary_lords.pack"
STAGED = os.path.join(ROOT, "Modding Files", "pack")
SIZE = (300, 164)
GAP, AT = 15, (151, 75)            # Ghorth's accepted framing
MARGIN, UPSCALE = 40, 2            # screenshot px kept around the window; Codex input scale

PROMPT = """Use the built-in image_gen tool (not the CLI fallback). Do not run shell commands and do not copy files.

The attached image porthole_in.png is a crop of an in-game screenshot of a Total War: WARHAMMER III character. It will become the character's porthole.

EDIT this exact image - a photo retouch and cut-out, NOT a new picture. The output must be the same character, the same pose, the same camera, the same framing and the same composition, so that it lines up with the input when laid on top of it.

Only do this:
- remove the background completely: fully transparent (real alpha) everywhere that is not the character or what they hold, with clean edges;
- lift the dark shadows so the face or helm, armour and beard read clearly, with soft even studio light from the front, like a character-select portrait;
- clean up the blur and screenshot noise so edges are crisp.

Do NOT change anything else. Do not redraw, restyle or "improve" any part of the model: every piece of the helm or face, crest, horns, eyes, beard, armour, trim, weapons and anything held must keep exactly its shape, size, position, count and colour. Do not add a face, plates, spikes, ornaments, symbols or glow. Do not remove anything except the background. If unsure, leave that area as it is.

Same size and aspect ratio as the input. No text, no border, no shadow plate.

Reply with the full path of the saved image only."""


def pack_path(stem):
    return "ui/portraits/portholes/no_culture/%s.png" % stem


def window(eyes, gap, at, size):
    """The porthole's box in an image's pixels, given the eye centres in that image."""
    lx, ly, rx, ry = eyes
    s = gap / (rx - lx)
    cx, cy = (lx + rx) / 2, (ly + ry) / 2
    return (cx - at[0] / s, cy - at[1] / s, cx + (size[0] - at[0]) / s, cy + (size[1] - at[1]) / s)


def frame(im, eyes, gap, at, size=SIZE):
    """Cut the porthole window out of `im` (padding with transparency where it runs off)."""
    box = window(eyes, gap, at, size)
    can = Image.new("RGBA", (round(box[2] - box[0]), round(box[3] - box[1])), (0, 0, 0, 0))
    src = im.crop((max(0, round(box[0])), max(0, round(box[1])),
                   min(im.width, round(box[2])), min(im.height, round(box[3]))))
    can.alpha_composite(src.convert("RGBA"), (max(0, -round(box[0])), max(0, -round(box[1]))))
    return can.resize(size, Image.LANCZOS)


def red_eye(a, x, y, r):
    """Centre of the red pixels within r of (x, y), or None. Only lords with glowing eyes."""
    y0, x0 = max(0, int(y - r)), max(0, int(x - r))
    sub = a[y0:int(y + r), x0:int(x + r)]
    ys, xs = np.nonzero((sub[..., 0] - np.maximum(sub[..., 1], sub[..., 2]) > 70) & (sub[..., 3] > 200))
    return (float(np.median(xs) + x0), float(np.median(ys) + y0)) if len(xs) > 20 else None


def out_eyes(meta, out):
    """Eyes in Codex's cut-out: the input eyes scaled by the size change, refined on red pixels."""
    sx, sy = out.width / meta["in_size"][0], out.height / meta["in_size"][1]
    a = np.asarray(out.convert("RGBA")).astype(int)
    pred = [(x * sx, y * sy) for x, y in meta["in_eyes"]]
    r = 0.45 * (pred[1][0] - pred[0][0])     # under half the gap, or one search finds both eyes
    e = [red_eye(a, px, py, r) or (px, py) for px, py in pred]
    return (e[0][0], e[0][1], e[1][0], e[1][1])


def codex(d, refs=()):
    """refs: extra images attached after porthole_in.png (style references the prompt names)."""
    from gen_commodity_icons import codex_exe
    last = os.path.join(d, "codex_last.txt")
    images = [a for p in [os.path.join(d, "porthole_in.png"), *refs] for a in ("-i", p)]
    r = subprocess.run([codex_exe(), "exec", "--skip-git-repo-check", "-s", "read-only", "-C", d,
                        *images, "-o", last, "-"],
                       input=PROMPT, text=True, encoding="utf-8", capture_output=True, timeout=900)
    msg = open(last, encoding="utf-8").read() if os.path.exists(last) else ""
    m = re.search(r"[A-Za-z]:\\[^`\n]*?generated_images\\[^`\n]*?\.png", msg)
    if m and os.path.exists(m.group(0)):
        return m.group(0)
    sid = re.search(r"session id: (\S+)", r.stdout + r.stderr)
    hits = sid and glob.glob(os.path.expanduser(r"~\.codex\generated_images\%s\*.png" % sid.group(1)))
    if not hits:
        sys.exit("Codex made no image: " + (msg or r.stderr[-400:]))
    return max(hits, key=os.path.getmtime)


def prepare(stem, shot, eyes, mirror, gap, at):
    d = os.path.join(OUT, stem)
    os.makedirs(d, exist_ok=True)
    im = Image.open(shot).convert("RGB")
    if mirror:
        im = ImageOps.mirror(im)
        lx, ly, rx, ry = eyes
        eyes = (im.width - 1 - rx, ry, im.width - 1 - lx, ly)
    im.save(os.path.join(d, "shot.png"))
    b = window(eyes, gap, at, SIZE)
    b = (max(0, round(b[0]) - MARGIN), max(0, round(b[1]) - MARGIN),
         min(im.width, round(b[2]) + MARGIN), min(im.height, round(b[3]) + MARGIN))
    crop = im.crop(b)
    crop = crop.resize((crop.width * UPSCALE, crop.height * UPSCALE), Image.LANCZOS)
    crop.save(os.path.join(d, "porthole_in.png"))
    meta = {"shot_eyes": eyes, "mirror": mirror, "in_box": b, "in_size": crop.size,
            "in_eyes": [((eyes[0] - b[0]) * UPSCALE, (eyes[1] - b[1]) * UPSCALE),
                        ((eyes[2] - b[0]) * UPSCALE, (eyes[3] - b[1]) * UPSCALE)],
            "gap": gap, "at": at}
    json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=1)
    return d


def derive(stem, gap=None, at=None, eyes=None):
    """Frame the cut-out. Eye positions are STORED in meta.json once found: a 2-4 px wobble in the
    finder changes the gap and rescales the whole porthole ~5%, so a re-derive must reuse them."""
    d = os.path.join(OUT, stem)
    meta = json.load(open(os.path.join(d, "meta.json")))
    gap, at = gap or meta["gap"], at or tuple(meta["at"])
    out = Image.open(os.path.join(d, "porthole_out.png")).convert("RGBA")
    eyes = eyes or meta.get("out_eyes") or out_eyes(meta, out)
    print("eyes in cut-out: %.1f,%.1f %.1f,%.1f - check them on porthole_out.png" % tuple(eyes))
    p = frame(out, eyes, gap, at)
    p.save(os.path.join(d, "porthole.png"))
    meta.update(gap=gap, at=at, out_eyes=list(eyes))
    json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=1)
    compare(stem)
    a = np.asarray(p)[..., 3]
    print("%s: gap %s at %s, transparent %.0f%%, bottom row %d/300 opaque"
          % (stem, gap, at, 100 * (a <= 8).mean(), (a[-1] > 8).sum()))


def current(stem):
    import io
    got = rpi.read(HLL, pack_path(stem))
    return Image.open(io.BytesIO(got[0][2])).convert("RGBA") if got else None


def compare(stem):
    d, S = os.path.join(OUT, stem), 2
    ims = [("current", current(stem)), ("new", Image.open(os.path.join(d, "porthole.png")).convert("RGBA"))]
    sheet = Image.new("RGBA", (SIZE[0] * S, len(ims) * (SIZE[1] * S + 24)), (45, 45, 45, 255))
    dr = ImageDraw.Draw(sheet)
    for i, (t, im) in enumerate(ims):
        y = i * (SIZE[1] * S + 24)
        if im:
            sheet.alpha_composite(im.resize((SIZE[0] * S, SIZE[1] * S), Image.NEAREST), (0, y))
        dr.text((4, y + SIZE[1] * S + 6), t if im else t + " (none in pack)", fill=(255, 255, 255))
    sheet.save(os.path.join(d, "compare.png"))


def pack(stem):
    from rpfm_client import call
    src = os.path.join(OUT, stem, "porthole.png")
    dst = pack_path(stem)
    before = {p: b for p, c, b in rpi.read(HLL, "")}
    if dst not in before:
        sys.exit("%s is not in the pack - check the stem against the portrait settings file" % dst)
    bak = os.path.join(ROOT, "Modding Files", "Backup",
                       "pre_porthole_%s_%s" % (stem, datetime.date.today().strftime("%Y%m%d")))
    os.makedirs(bak, exist_ok=True)
    shutil.copy2(HLL, bak)
    staged = os.path.join(STAGED, *dst.split("/"))
    if os.path.exists(staged):
        shutil.copy2(staged, bak)
    key = call("open_packfiles", {"paths": [HLL]})["StringContainerInfo"][0]
    call("add_packed_files", {"pack_key": key, "source_paths": [src],
                              "destination_paths": json.dumps([{"File": dst}])})
    call("save_packfile", {"pack_key": key})
    call("close_pack", {"pack_key": key})
    after = {p: b for p, c, b in rpi.read(HLL, "")}
    changed = sorted(p for p in before if before[p] != after.get(p))
    ok = set(before) == set(after) and changed == [dst] and after[dst] == open(src, "rb").read()
    print("files %d -> %d, changed %s, round-trip %s" % (len(before), len(after), changed, ok))
    if not ok:
        sys.exit("pack check FAILED - restore from %s" % bak)
    if os.path.exists(staged):
        shutil.copy2(src, staged)
    print("replaced %s (backup %s)" % (dst, bak))


def selftest():
    """Re-frame Ghorth's cached cut-out and compare with the porthole that shipped 2026-10-05."""
    d = os.path.join(OUT, "derpy_ghorth")
    meta = json.load(open(os.path.join(d, "meta.json")))
    out = Image.open(os.path.join(d, "porthole_out.png")).convert("RGBA")
    e = meta["out_eyes"]
    found = out_eyes(meta, out)
    assert max(abs(a - b) for a, b in zip(found, e)) < 6, "eye finder far from the stored eyes: %s" % (found,)
    got = np.asarray(frame(out, e, meta["gap"], tuple(meta["at"]))).astype(int)
    shipped = np.asarray(current("derpy_ghorth")).astype(int)
    diff = np.abs(got - shipped).mean()
    assert diff < 1.0, "re-derived porthole differs from the shipped one: mean %.2f" % diff
    # a framing change must show: the check is not blind
    other = np.asarray(frame(out, e, meta["gap"] + 3, tuple(meta["at"]))).astype(int)
    assert np.abs(other - shipped).mean() > 5, "framing change not detected"
    print("selftest ok (mean diff %.3f)" % diff)


def main(a):
    if "--selftest" in a:
        return selftest()
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    stem = a[0]
    gap = float(opt("--gap")) if opt("--gap") else None
    at = tuple(map(float, opt("--at").split(","))) if opt("--at") else None
    oe = tuple(map(float, opt("--out-eyes").split(","))) if opt("--out-eyes") else None
    if "--pack" in a:
        return pack(stem)
    if "--derive" not in a:
        if not opt("--eyes"):
            sys.exit("need --eyes LX,LY,RX,RY (eye centres in the screenshot)")
        d = prepare(stem, a[1], tuple(map(float, opt("--eyes").split(","))), "--mirror" in a,
                    gap or GAP, at or AT)
        Image.open(codex(d)).save(os.path.join(d, "porthole_out.png"))
    derive(stem, gap, at, oe)


if __name__ == "__main__":
    main(sys.argv[1:])
