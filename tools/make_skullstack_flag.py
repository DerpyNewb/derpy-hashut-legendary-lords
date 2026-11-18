"""The Uzkul Mingol Company's flag (cr_chd_skullstack): a collaborator's device, redrawn the way CA draws its own.

    py tools/make_skullstack_flag.py --preview     both palettes into Modding Files/source/skullstack_flag/preview/
    py tools/make_skullstack_flag.py --write       the shipped palette (SHIPS) into Modding Files/pack/ui/flags/
                                                   cr_chd_skullstack/, then --check; gen_new_house_lords packs it
    py tools/make_skullstack_flag.py --check       measure the staged files
    py tools/make_skullstack_flag.py --selftest

The lords pack loads before IEE (!aa_ sorts before !cr_), so these six files replace IEE's own at the path IEE's
factions row names; the row itself is untouched. tools/make_toz_seat_banner.py lifts the Tower seat's device
from the staged mon_256.png, so run it after --write.

The supplied art (Modding Files/source/skullstack_flag/supplied.png, 1254 px) is a chaos star of eight
arrows behind a skull with a lightning bolt, in a bronze frame on a charcoal plate with one corner cut
away - the layout of CA's Chaos Dwarf flags, painted over with bevels, rivets on every arrow and noise.
Only its SHAPES are taken. The frame and the plate are CA's (Astragoth's flag, whose plate is the same
charcoal), and the device is redrawn flat in two of CA's own paints, the way Zhatan's gold skull and
Astragoth's white one are drawn.

THE PLATE UNDER CA'S DEVICE IS CA'S TOO. All of CA's Chaos Dwarf flags tint one plate texture (Azgorh's
grain correlates 0.98 with Astragoth's), so where Astragoth's device sat, the grain is read off the other
five donors wherever THEIR device is not, and only what no donor leaves bare is diffused in.

SIX FILES, as CA ships them; mon_64 and mon_24 are NOT downscales of mon_256 (CA redrew the frame at
those sizes, 8-15 grey levels off a resize), so each is restyled from CA's own file at that size:

    mon_24.png, mon_64.png, mon_256.png   the framed flag
    mon_rotated.png 112x90                the framed flag in perspective, a homography fitted to CA's pair
    mon_icon.png, mon_banner.dds          the bare device on transparency, mon_256's layout

Two palettes are previewed, because the faction's banner colours (989964 khaki, 44302A dark brown, IEE's
row, which the lords pack ships) also paint its Tower of Zharr seat banner:
    collaborator   CA's charcoal plate, Zhatan's gold arrows, Astragoth's bone skull - the supplied colours
    faction        the plate and device colours of IEE's current flag
"""
import os
import sys
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import make_ic_rebel_flags as ic                                 # noqa: E402  plate_mask, _extent, _unwrap

GAME_UI = os.path.join(ic.GAME_DATA, "ui.pack")
IEE = r"F:\SteamLibrary\steamapps\workshop\content\1142710\3007996493\!cr_immortal_empires_expanded.pack"
SRC = os.path.join(ROOT, "Modding Files", "source", "skullstack_flag", "supplied.png")
PREVIEW = os.path.join(ROOT, "Modding Files", "source", "skullstack_flag", "preview")
CACHE = os.path.join(ROOT, ".skilltree_cache", "skullstack_flag_src")
NAMES = ["mon_24.png", "mon_64.png", "mon_256.png", "mon_icon.png", "mon_rotated.png", "mon_banner.dds"]
FRAMED = ["mon_256.png", "mon_64.png", "mon_24.png", "mon_rotated.png"]

BASE = "wh3_dlc23_chd_astragoth"            # frame, plate colour and layout
# every CA Chaos Dwarf flag with its own device; the grain under BASE's device is read from these
DONORS = [BASE, "wh3_dlc23_chd_legion_of_azgorh", "wh3_dlc23_chd_zhatan", "wh3_dlc23_chd_minor_faction",
          "wh3_dlc23_chd_conclave", "wh3_dlc23_chd_chaos_dwarfs_rebels"]
GOLD_FROM = "wh3_dlc23_chd_zhatan"          # its device is one gold
BONE_FROM = BASE                            # its skull is CA's bone white
IEE_FLAG = "cr_chd_skullstack"

# ---- the supplied art, in its own 1254 px ---------------------------------------------------------
SKULL_SEED = (560, 470)
BOLT_SEED = (615, 420)
ARROW_SEEDS = [(628, 175), (775, 300), (935, 520), (775, 740), (628, 860), (470, 740), (300, 520), (470, 300)]
# The skull is bright paint inside a dark outline 5-8 px wide; its cracks are 3-4 px. A 2.5 px blur fades
# the cracks and not the outline, and at 0.43 the two diagonal shafts that touch the skull fall outside it
# (0.38 kept a shaft, 0.48 ate the top of the skull - measured on the overlay).
SKULL_BLUR, SKULL_T = 2.5, 0.43
BRIDGE = 11         # an arrow's highlight touches the skull through bridges narrower than this
HULL = 61           # the bolt reaches the skull's top edge and the teeth gaps its bottom: a close this wide
                    # makes the outline they are holes in (a disk; the square kernel managed it at 41)
RIVET = 45          # a hole in an arrow narrower than this is a rivet and closes; a wider one is plate
GAP = 11            # plate left between the skull and the arrows, ~2 px on mon_256, as CA's devices have
PROFILE = 15        # rows an arrow's half-width is median-filtered over: the bevel's teeth are ~10 px here
GRAIN = 0.06       # the device's fine grain, std over mean: inside CA's 0.027-0.093

PALETTES = ("collaborator", "faction")
SHIPS = "faction"           # the author's pick (2026-11-18): the faction's own banner colours stay true
STAGED = os.path.join(ROOT, "Modding Files", "pack", "ui", "flags", IEE_FLAG)


# ---- small mask tools (numpy bool <-> PIL L) ------------------------------------------------------
def _L(m):
    return Image.fromarray((np.asarray(m, dtype=float) * 255).clip(0, 255).astype(np.uint8), "L")


def _b(img, t=0.5):
    return np.asarray(img).astype(float) / 255 > t


def _disk(m, size):
    """Dilation of a bool mask by a DISK `size` px across. Not Pillow's MaxFilter: its kernel is square,
    and opening or closing a diagonal edge with a square leaves it a staircase of the kernel's size - the
    arrowheads came out stepped every 8-10 px that way."""
    r = size // 2
    if r < 1:
        return m.copy()
    h, w = m.shape
    p = np.pad(m, r)
    out = np.zeros_like(m)
    for dy in range(-r, r + 1):
        span = int(np.sqrt(r * r - dy * dy))
        row = p[r + dy:r + dy + h]
        for dx in range(-span, span + 1):
            out |= row[:, r + dx:r + dx + w]
    return out


def _open(m, r):
    return _disk(~_disk(~m, r), r)          # erode, then dilate


def _close(m, r):
    return ~_disk(~_disk(m, r), r)


def _grow(m, r):
    return _disk(m, r) if r > 1 else m


def _smooth(m, r):
    return _b(_L(m).filter(ImageFilter.GaussianBlur(r)))


def _component(m, seed):
    img = _L(m).copy()      # fromarray wraps the array's memory, and floodfill on that silently does nothing
    if img.getpixel(seed) < 128:
        return np.zeros(m.shape, bool)
    ImageDraw.floodfill(img, seed, 128)
    return np.asarray(img) == 128


def _gblur(a, r):
    """Gaussian blur of a float array (Pillow will not blur mode F), separable, edges clamped."""
    n = max(1, int(3 * r))
    k = np.exp(-0.5 * (np.arange(-n, n + 1) / float(r)) ** 2)
    k /= k.sum()
    p = np.pad(a, n, mode="edge")
    p = np.apply_along_axis(lambda v: np.convolve(v, k, "valid"), 0, p)
    return np.apply_along_axis(lambda v: np.convolve(v, k, "valid"), 1, p)


def _fill_holes(m):
    pad = Image.new("L", (m.shape[1] + 2, m.shape[0] + 2), 0)
    pad.paste(_L(m), (1, 1))
    ImageDraw.floodfill(pad, (0, 0), 128)
    return ~(np.asarray(pad) == 128)[1:-1, 1:-1]


# ---- CA's art -------------------------------------------------------------------------------------
def fetch():
    """The six files of every donor and of IEE's flag, into .skilltree_cache, with RPFM shut."""
    import read_pack_index as R
    want = {d: GAME_UI for d in DONORS}
    want[IEE_FLAG] = IEE
    for folder, pack in want.items():
        d = os.path.join(CACHE, folder)
        if all(os.path.isfile(os.path.join(d, n)) for n in NAMES):
            continue
        os.makedirs(d, exist_ok=True)
        for path, _c, raw in R.read(pack, "ui/flags/%s/" % folder):
            name = path.replace("\\", "/").rsplit("/", 1)[-1].lower()
            if name in NAMES:
                open(os.path.join(d, name), "wb").write(ic._unwrap(raw))
        missing = [n for n in NAMES if not os.path.isfile(os.path.join(d, n))]
        assert not missing, "%s has no %s in %s" % (folder, missing, pack)
    return CACHE


def ca(folder, name):
    return Image.open(os.path.join(fetch(), folder, name)).convert("RGBA")


def rgba(im):
    return np.asarray(im.convert("RGBA")).astype(float)


def lum(a):
    return a[..., :3].mean(-1)


def paint(folder):
    """(median RGB, grain std relative to its mean, top/bottom brightness) of a CA device, off mon_icon."""
    a = rgba(ca(folder, "mon_icon.png"))
    on = a[..., 3] > 200
    rgb = np.median(a[on][:, :3], 0)
    lu = lum(a)
    blur = np.asarray(_L(lu / 255).filter(ImageFilter.GaussianBlur(4))).astype(float)
    grain = ((lu - blur)[on]).std() / max(lu[on].mean(), 1)
    ys = np.nonzero(on)[0]
    third = (ys.max() - ys.min()) / 3.0
    top = lu[on & (np.arange(a.shape[0])[:, None] < ys.min() + third)].mean() / lu[on].mean()
    bot = lu[on & (np.arange(a.shape[0])[:, None] > ys.max() - third)].mean() / lu[on].mean()
    return rgb, grain, (top, bot)


def bone():
    """Astragoth's white: the unsaturated half of its device."""
    a = rgba(ca(BONE_FROM, "mon_icon.png"))
    on = a[..., 3] > 200
    mx, mn = a[..., :3].max(-1), a[..., :3].min(-1)
    white = on & ((mx - mn) / np.maximum(mx, 1) < 0.15) & (mx > 150)
    return np.median(a[white][:, :3], 0)


def plate_tint(folder, name="mon_256.png"):
    im = ca(folder, name)
    pm = _b(ic.plate_mask(ca(BASE, name)))
    a = rgba(im)
    return np.median(a[pm][:, :3], 0)


# ---- the clean plate ------------------------------------------------------------------------------
@lru_cache(None)
def grain(name):
    """CA's shared plate texture for one file, as brightness over each donor's plate median, with no device.

    Each donor's device is whatever strays from its own plate colour - in chroma, or in brightness - grown a
    little past its antialiased edge. Per pixel the median over the donors whose plate is bare there; what
    none leaves bare is filled by normalised convolution from the edge in."""
    base = ca(BASE, name)
    w = base.size[0]
    # plate_mask stops short of the frame's bevel on purpose; the rim it leaves is still bare plate in every
    # donor and must be repainted too, or a khaki plate keeps a charcoal ring under the frame
    k = max(3, int(round(min(base.size) / 96.0)) * 2 + 1)
    b = rgba(base)
    mx, mn = b[..., :3].max(-1) / 255, b[..., :3].min(-1) / 255
    platelike = (mx < 0.32) & ((mx - mn) / np.maximum(mx, 1e-6) < 0.40) & (b[..., 3] > 200)
    inner = _b(ic.plate_mask(base))
    pm = inner | (_grow(inner, k + 2) & platelike)
    g = max(1, int(round(w / 128.0)) * 2 + 1) if w >= 64 else 1
    layers = []
    for d in DONORS:
        a = rgba(ca(d, name))[..., :3]
        t = np.median(a[pm], 0)
        lt = t.mean()
        lu = a.mean(-1)
        chroma = a / np.maximum(lu, 1)[..., None] - (t / lt)
        ratio = lu / lt
        dev = (np.sqrt((chroma ** 2).sum(-1)) > 0.25) | (ratio > 1.8) | (ratio < 0.4)
        dev = _grow(dev, g)
        layers.append(np.where(pm & ~dev, ratio, np.nan))
    G = np.nanmedian(np.stack(layers), 0)
    hole = pm & np.isnan(G)
    known = np.where(np.isnan(G), 0, G)
    weight = (~np.isnan(G) & pm).astype(float)
    r = 1.0
    while hole.any():
        num, den = _gblur(known, r), _gblur(weight, r)
        ok = hole & (den > 0.05)
        G[ok] = num[ok] / den[ok]
        hole &= ~ok
        r *= 1.6
    return G, pm


def clean(name, tint):
    """CA's file at this size, its plate repainted `tint` x the shared grain, CA's device gone."""
    base = rgba(ca(BASE, name))
    G, pm = grain(name)
    out = base.copy()
    out[pm, :3] = np.clip(tint[None, :] * G[pm][:, None], 0, 255)
    return out


# ---- the device -----------------------------------------------------------------------------------
@lru_cache(None)
def masks():
    """(arrows, skull paint, skull outline) as bool arrays over the supplied art."""
    im = Image.open(SRC).convert("RGB")
    a = np.asarray(im).astype(float) / 255
    mx, mn = a.max(-1), a.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    valb = np.asarray(_L(mx).filter(ImageFilter.GaussianBlur(SKULL_BLUR))).astype(float) / 255
    bright = valb > SKULL_T
    core = _component(_open(bright, BRIDGE), SKULL_SEED)
    skull = bright & _grow(core, BRIDGE // 2 * 2 + 3)
    solid = _smooth(_close(skull, 9), 3)
    hull = _fill_holes(_close(solid, HULL))
    holes = _open(hull & ~solid, 7)
    # the painted cracks run out of the bolt, so its flood fill takes them along; they are 4-6 px wide
    # and the bolt ~30, so an opening between the two keeps the bolt alone
    bolt = _open(_component(holes, BOLT_SEED), 11)

    device = ((sat > 0.35) & (mx > 0.15)) | (mx > 0.40)
    device = _open(device, 7)
    arrows = np.zeros(device.shape, bool)
    for s in ARROW_SEEDS:
        arrows |= _component(device, s)
    arrows = _close(arrows, 9)
    gaps = _fill_holes(arrows) & ~arrows
    arrows = arrows | (gaps & ~_open(gaps, RIVET))

    # THE ART'S OWN SHAPES, WITH THE PAINTING'S WOBBLE AVERAGED OUT. Traced edges follow every bevel and
    # highlight of the supplied paint, which drew the arrowheads melted. The star is regular - the four
    # main arrows are quarter turns of each other, so are the four diagonal ones, and each is mirrored -
    # so the mask is averaged over those eight copies; the skull over its mirror. Nothing is drawn that the
    # artist did not draw. The bolt is the one asymmetric part and is kept as painted.
    # cut at the skull first: the shafts meet behind it, so before this every arrow is one flood fill
    arrows = _star(arrows & ~_grow(hull, GAP))
    mx_ = _axis(hull)
    # the outline is joined with its mirror (>= .5, a union) and the holes kept only where both sides
    # agree (> .5): a crack reaching the outline on one side then fills instead of cutting a crescent,
    # and a crack inside the skull, painted on one side only, is dropped
    hull = _fill_holes(_close(_sym(hull, mx_) >= 0.5, 15))
    rest = _sym(holes & ~bolt, mx_) > 0.5
    hull, rest, bolt = _smooth(hull, 2), _smooth(rest, 1.5), _smooth(bolt, 1.5)
    arrows = _smooth(arrows, 1.5) & ~_grow(hull, GAP)
    return arrows, hull & ~rest & ~bolt, hull


def _centroid(m):
    ys, xs = np.nonzero(m)
    return xs.mean(), ys.mean()


def _patch(m, c, r):
    """A (2r x 2r) float window of m centred on point c, zero-padded at the edges."""
    out = np.zeros((2 * r, 2 * r))
    x0, y0 = int(round(c[0])) - r, int(round(c[1])) - r
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(m.shape[1], x0 + 2 * r), min(m.shape[0], y0 + 2 * r)
    out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = m[sy0:sy1, sx0:sx1]
    return out


def _turn(a, deg):
    """A float array turned `deg` degrees counter-clockwise about its centre."""
    return np.asarray(Image.fromarray(a.astype(np.float32), "F").rotate(deg, Image.BILINEAR))


def _profile(up):
    """An upright arrow rebuilt from its half-width per row, median-filtered down its length.

    Upright, an arrow is one span per row - a straight ramp out from the tip, a step in to the shaft - so
    its whole shape is that half-width. The widest pixel either side of the axis gives back the shaded
    flank, and a median over PROFILE rows takes off the bevel's teeth while keeping the ramps straight and
    the step sharp, which a blur does not: it rounds the tips."""
    axis = (up.shape[1] - 1) / 2.0
    w = np.full(up.shape[0], np.nan)
    for y in np.nonzero(up.any(1))[0]:
        xs = np.nonzero(up[y])[0]
        w[y] = np.abs(xs - axis).max() + 0.5
    rows = np.nonzero(~np.isnan(w))[0]
    h = PROFILE // 2
    sm = w.copy()
    for y in rows:
        win = w[max(rows.min(), y - h):min(rows.max(), y + h) + 1]
        sm[y] = np.nanmedian(win)
    out = np.zeros(up.shape)
    cols = np.abs(np.arange(up.shape[1]) - axis)
    for y in rows:
        out[y] = np.clip(sm[y] - cols + 0.5, 0, 1)             # antialiased at the span's ends
    return out


def _star(arrows):
    """Each arrow made whole about its own axis, the line from the star's centre to its tip.

    The paint is bevelled and lit from one side, so an arrow's shaded flank falls below the device test
    and its traced outline is ragged or missing there. Each arrow is turned upright about that axis and
    joined with its own mirror image, which gives back the shaded flank from the lit one, then turned back.
    Not averaged ACROSS arrows: the art is not that regular - the side arrows are larger than the top and
    bottom ones and the diagonals are not at 45 degrees - and forcing one shape on all eight rounded the
    diagonals into spades. Every arrow keeps the size and angle the artist gave it."""
    comps = [_component(arrows, s) for s in ARROW_SEEDS]
    assert all(c.any() for c in comps) and not any(
        (comps[i] & comps[j]).any() for i in range(8) for j in range(i + 1, 8)), \
        "the arrows are not eight separate shapes: %s" % [int(c.sum()) for c in comps]
    cents = [_centroid(c) for c in comps]
    cx, cy = np.mean([c[0] for c in cents]), np.mean([c[1] for c in cents])
    yy, xx = np.mgrid[:arrows.shape[0], :arrows.shape[1]]
    dist = np.hypot(xx - cx, yy - cy)
    out = np.zeros(arrows.shape)
    for c in comps:
        k = np.argmax(np.where(c, dist, -1))
        tx, ty = xx.flat[k], yy.flat[k]
        deg = np.degrees(np.arctan2(tx - cx, cy - ty))         # clockwise from up
        ys, xs = np.nonzero(c)
        r = int(max(xs.max() - xs.min(), ys.max() - ys.min())) + 24
        p = _turn(_patch(c, (cx, cy), r * 2), deg) > 0.5      # turned about the star's centre, the axis
        whole = _turn(_profile(p), -deg)                        # is the patch's middle column
        x0, y0 = int(round(cx)) - 2 * r, int(round(cy)) - 2 * r
        sx0, sy0 = max(0, x0), max(0, y0)
        sx1, sy1 = min(out.shape[1], x0 + 4 * r), min(out.shape[0], y0 + 4 * r)
        out[sy0:sy1, sx0:sx1] = np.maximum(out[sy0:sy1, sx0:sx1], whole[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0])
    return _fill_holes(_close(out > 0.5, 9))


def _axis(m, search=16):
    """The column the skull is most nearly mirrored about."""
    ys, xs = np.nonzero(m)
    x0, top, bot = int(xs.mean()), ys.min() - 4, ys.max() + 4
    half = max(x0 - xs.min(), xs.max() - x0) + search + 4
    best = None
    for dx in range(-search, search + 1):
        w = m[top:bot, x0 + dx - half:x0 + dx + half].astype(float)
        e = np.abs(w - w[:, ::-1]).sum()
        if best is None or e < best[0]:
            best = (e, x0 + dx)
    return best[1]


def _sym(m, cx):
    """m averaged over its mirror about column cx."""
    out = m.astype(float).copy()
    ys, xs = np.nonzero(m)
    half = max(cx - xs.min(), xs.max() - cx) + 4
    w = out[:, cx - half:cx + half]
    out[:, cx - half:cx + half] = (w + w[:, ::-1]) / 2
    return out


def supplied_plate():
    """The supplied art's plate: its black surround made transparent first, or plate_mask takes it all."""
    im = Image.open(SRC).convert("RGBA")
    a = np.asarray(im).copy()
    dark = a[..., :3].max(-1) < 10
    out = _component(dark, (0, 0)) | _component(dark, (a.shape[1] - 1, a.shape[0] - 1))
    a[out, 3] = 0
    return _b(ic.plate_mask(Image.fromarray(a, "RGBA")))


@lru_cache(None)
def layout():
    """Where the device goes on mon_256: (box in the supplied art, scale to mon_256 px, its centre there).

    Placed against the plate, as make_ic_rebel_flags does: the device's size over the plate's short side and
    its offset from the plate's centroid are read off the supplied art and applied to CA's plate."""
    arrows, _p, hull = masks()
    dev = arrows | hull
    ys, xs = np.nonzero(dev)
    box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    sp = supplied_plate()
    (sx0, sy0, sx1, sy1), (scx, scy), _n = ic._extent(_L(sp))
    s_short = min(sx1 - sx0, sy1 - sy0)
    (px0, py0, px1, py1), (pcx, pcy), _n = ic._extent(ic.plate_mask(ca(BASE, "mon_256.png")))
    p_short = min(px1 - px0, py1 - py0)
    k = p_short / float(s_short)
    dcx = (box[0] + box[2]) / 2.0
    # ACROSS, where the artist put it. DOWN, on the plate's centroid (y 124 on mon_256), where CA centres its
    # own devices (y 114-131 across the six, IEE's 122). The artist's height put the top arrow on the
    # plate's edge at y 24, centre 108, and the author asked for it lower (2026-11-18).
    centre = (pcx + (dcx - scx) * k, pcy)
    return box, k, centre


def device_layer(pal, scale=4):
    """The device on transparency in mon_256's space, rendered at `scale`x and returned at 256."""
    arrows, skull_paint, _hull = masks()
    box, k, (cx, cy) = layout()
    S = 256 * scale
    tw, th = int(round((box[2] - box[0]) * k * scale)), int(round((box[3] - box[1]) * k * scale))
    ox, oy = int(round(cx * scale - tw / 2.0)), int(round(cy * scale - th / 2.0))

    def place(m):
        c = _L(m).crop(box).resize((tw, th), Image.LANCZOS)
        full = Image.new("L", (S, S), 0)
        full.paste(c, (ox, oy))
        return np.asarray(full).astype(float) / 255

    cov_a, cov_s = place(arrows), place(skull_paint)
    # The plate's own fine grain on the device, at the strength CA's devices carry it away from their edges
    # (std over mean at a 2 px blur: Zhatan 0.084, Astragoth 0.093, Azgorh 0.027 - measured 2026-11-18).
    # Clipped at 2.5 sigma: the plate's deepest scratches came through as black blots on the gold.
    G, _pm = grain("mon_256.png")
    G = np.where(np.isnan(G), 1, G)
    hp = (G / np.maximum(_gblur(G, 2), 1e-3)) - 1
    hp = np.asarray(Image.fromarray(hp.astype(np.float32), "F").resize((S, S), Image.BICUBIC))
    _rgb, _g, (top, bot) = paint(GOLD_FROM)
    inside = (cov_a + cov_s) > 0.5
    hp = np.clip(hp, -2.5 * hp[inside].std(), 2.5 * hp[inside].std())
    k_grain = GRAIN / max(hp[inside].std(), 1e-3)
    yy = np.arange(S)[:, None].astype(float)
    t = np.clip((yy - oy) / max(th, 1), 0, 1)
    gradient = top + (bot - top) * t
    # a darker inner edge, ~1 px on mon_256, as CA's devices have where paint meets plate
    def edge(c):
        inner = np.asarray(_L(c > 0.5).filter(ImageFilter.MinFilter(2 * scale + 1))).astype(float) / 255
        return 1 - 0.22 * np.clip(c - inner, 0, 1)
    shade = (1 + k_grain * hp) * gradient
    out = np.zeros((S, S, 4))
    for cov, rgb in ((cov_a, pal["arrows"]), (cov_s, pal["skull"])):
        col = np.clip(rgb[None, None, :] * (shade * edge(cov))[..., None], 0, 255)
        a = cov[..., None]
        out[..., :3] = col * a + out[..., :3] * (1 - a)
        out[..., 3] = np.maximum(out[..., 3], cov * 255)
    im = Image.fromarray(out.round().clip(0, 255).astype(np.uint8), "RGBA")
    return im.resize((256, 256), Image.LANCZOS)


def palette(name):
    if name == "collaborator":
        return dict(plate=plate_tint(BASE), arrows=paint(GOLD_FROM)[0], skull=bone())
    # IEE's flag as it is: its plate colour and its one device colour, on CA's grain
    a = rgba(ca(IEE_FLAG, "mon_icon.png"))
    dev = np.median(a[a[..., 3] > 200][:, :3], 0)
    p = rgba(ca(IEE_FLAG, "mon_256.png"))
    pm = _b(ic.plate_mask(ca(BASE, "mon_256.png")))
    lu = lum(p)
    plate = np.median(p[pm & (lu > np.percentile(lu[pm], 60))][:, :3], 0)      # its bare parchment, not the skulls
    return dict(plate=plate, arrows=dev, skull=dev)


# ---- mon_256 -> mon_rotated -------------------------------------------------------------------------
def _coeffs(dst, src):
    """PIL PERSPECTIVE coefficients mapping output points `dst` back to input points `src`."""
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float))


SQUARE = [(0, 0), (256, 0), (256, 256), (0, 256)]


def warp(im, corners, size):
    """mon_256-space RGBA -> `size`, its four corners landing on `corners`. Premultiplied, so no dark fringe."""
    c = _coeffs(corners, SQUARE)
    return im.convert("RGBa").transform(size, Image.PERSPECTIVE, tuple(c), Image.BICUBIC).convert("RGBA")


@lru_cache(None)
def fit_rotated():
    """Where mon_256's corners land on mon_rotated, fitted to CA's own pair by coordinate descent on the L1
    difference, from the affine guess the two alpha boxes give."""
    src, dst = ca(BASE, "mon_256.png"), ca(BASE, "mon_rotated.png")
    target = rgba(dst)

    def bbox(im):
        ys, xs = np.nonzero(rgba(im)[..., 3] > 40)
        return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    s, d = bbox(src), bbox(dst)
    kx, ky = (d[2] - d[0]) / float(s[2] - s[0]), (d[3] - d[1]) / float(s[3] - s[1])
    cs = [[d[0] + (x - s[0]) * kx, d[1] + (y - s[1]) * ky] for x, y in SQUARE]

    def err(c):
        return np.abs(rgba(warp(src, [tuple(p) for p in c], dst.size)) - target).mean()
    best = err(cs)
    for step in (8, 4, 2, 1, 0.5, 0.25):
        moved = True
        while moved:
            moved = False
            for i in range(4):
                for j in range(2):
                    for sgn in (1, -1):
                        trial = [list(p) for p in cs]
                        trial[i][j] += sgn * step
                        e = err(trial)
                        if e < best - 1e-6:
                            best, cs, moved = e, trial, True
    return [tuple(p) for p in cs], best


# ---- the six files --------------------------------------------------------------------------------
def build(pal_name):
    """{file name: PIL image} for one palette (mon_banner as a PNG image; --write encodes it)."""
    pal = palette(pal_name)
    dev = device_layer(pal)
    out = {}
    for name in FRAMED:
        size = ca(BASE, name).size
        bg = Image.fromarray(clean(name, pal["plate"] if name == "mon_256.png" else
                                   _tint_at(pal, name)).round().clip(0, 255).astype(np.uint8), "RGBA")
        if name == "mon_rotated.png":
            layer = warp(dev, fit_rotated()[0], size)
        else:
            layer = dev.convert("RGBa").resize(size, Image.LANCZOS).convert("RGBA")
        bg.alpha_composite(layer)
        out[name] = bg
    out["mon_icon.png"] = dev
    out["mon_banner.png"] = dev
    return out


def _tint_at(pal, name):
    """The palette's plate colour at another size: CA's own plate at that size runs a little lighter or
    darker than at 256, so the colour is scaled by BASE's own ratio between the two."""
    return pal["plate"] * (plate_tint(BASE, name).mean() / plate_tint(BASE).mean())


def preview():
    os.makedirs(PREVIEW, exist_ok=True)
    corners, e = fit_rotated()
    print("mon_rotated fit: mean abs %.2f grey levels, corners %s" % (e, [(round(x, 1), round(y, 1)) for x, y in corners]))
    rows = []
    for p in PALETTES:
        files = build(p)
        d = os.path.join(PREVIEW, p)
        os.makedirs(d, exist_ok=True)
        for n, im in files.items():
            im.save(os.path.join(d, n))
        rows.append((p, files))
        print(p, {k: tuple(int(v) for v in palette(p)[k]) for k in ("plate", "arrows", "skull")})
    sheet(rows)


def sheet(rows):
    """Reference row (CA's Astragoth and Zhatan, IEE's current flag, the supplied art), then one row per
    palette: mon_256, mon_rotated x2, mon_64 x2, mon_24 x3 and at 1x, mon_icon."""
    W = 1500
    S = Image.new("RGBA", (W, 300 * (len(rows) + 1) + 10), (46, 40, 37, 255))
    dr = ImageDraw.Draw(S)
    refs = [ca(BASE, "mon_256.png"), ca(GOLD_FROM, "mon_256.png"), ca(IEE_FLAG, "mon_256.png"),
            Image.open(SRC).convert("RGBA").resize((256, 256), Image.LANCZOS)]
    for i, (im, lab) in enumerate(zip(refs, ("CA Astragoth", "CA Zhatan", "IEE today", "supplied"))):
        S.alpha_composite(im, (10 + i * 270, 10))
        dr.text((10 + i * 270, 270), lab, fill=(255, 248, 215))
    for r, (p, f) in enumerate(rows):
        y = 300 * (r + 1) + 10
        x = 10
        for im, k in ((f["mon_256.png"], 1), (f["mon_rotated.png"], 2), (f["mon_64.png"], 2), (f["mon_24.png"], 3)):
            big = im.resize((im.width * k, im.height * k), Image.NEAREST if k > 1 else Image.LANCZOS)
            S.alpha_composite(big, (x, y))
            x += big.width + 14
        for im in (f["mon_64.png"], f["mon_24.png"], f["mon_rotated.png"]):
            S.alpha_composite(im, (x, y))
            x += im.width + 10
        S.alpha_composite(f["mon_icon.png"].resize((180, 180), Image.LANCZOS), (x, y))
        dr.text((10, y + 262), p, fill=(255, 248, 215))
    S.convert("RGB").save(os.path.join(PREVIEW, "preview.png"))
    print("wrote", os.path.join(PREVIEW, "preview.png"))


def write():
    """The chosen palette's six files into Modding Files/pack, where the lords pack's generator packs them."""
    import io
    files = build(SHIPS)
    os.makedirs(STAGED, exist_ok=True)
    for n in NAMES[:-1]:
        files[n].save(os.path.join(STAGED, n))
    # THE BATTLE BANNER THROUGH texconv: Pillow writes a .dds that is not BC3 and says nothing. texconv names
    # its output .DDS, so the bytes are copied to the lowercase name - an uppercase pack path crashes the game.
    tmp = os.path.join(CACHE, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    mid = os.path.join(tmp, "mon_banner.png")
    files["mon_banner.png"].save(mid)
    data = io.open(ic._png_to_dds(mid, tmp), "rb").read()
    io.open(os.path.join(STAGED, "mon_banner.dds"), "wb").write(data)
    for n in NAMES:
        print("wrote", os.path.join(STAGED, n))
    bad = check()
    for b in bad:
        print("FAIL", b)
    return 1 if bad else 0


def check():
    """What must be true of the staged files, measured: CA's six names and sizes, lowercase, the battle
    banner a BC3 dds with a full mip chain, every framed file opaque where CA's is."""
    import struct
    bad = []
    for n in NAMES:
        p = os.path.join(STAGED, n)
        if not os.path.isfile(p):
            bad.append("missing " + n)
            continue
        if n != n.lower():
            bad.append("uppercase in " + n)
        if n.endswith(".dds"):
            head = open(p, "rb").read(128)
            (h,), (w,), (mips,) = (struct.unpack("<I", head[o:o + 4]) for o in (12, 16, 28))
            if head[:4] != b"DDS " or head[84:88] != b"DXT5" or (w, h) != (256, 256) or mips != 9:
                bad.append("%s is not 256x256 BC3 with 9 mips: %r %dx%d %d" % (n, head[84:88], w, h, mips))
            continue
        im = Image.open(p)
        want = ca(BASE, n)
        if im.size != want.size or im.mode != "RGBA":
            bad.append("%s is %s %s, CA's is %s RGBA" % (n, im.size, im.mode, want.size))
        elif n in FRAMED and not np.array_equal(rgba(im)[..., 3] > 200, rgba(want)[..., 3] > 200):
            bad.append("%s: the flag's outline differs from CA's" % n)
    return bad


def selftest():
    arrows, paint_, hull = masks()
    # eight arrows, one skull with holes in it, and none of them touching the frame
    n_arrows = sum(_component(arrows, s).any() for s in ARROW_SEEDS)
    assert n_arrows == 8, n_arrows
    assert paint_.sum() < hull.sum() * 0.95, "the skull has no holes: the bolt and eyes were lost"
    ys, xs = np.nonzero(arrows | hull)
    assert xs.min() > 150 and xs.max() < 1100 and ys.min() > 80, "the device reaches the frame"
    assert not (arrows & _grow(hull, GAP - 2)).any(), "no gap between the skull and the arrows"
    G, pm = grain("mon_256.png")
    assert not np.isnan(G[pm]).any() and 0.3 < np.nanmedian(G[pm]) < 2, "the plate grain did not fill"
    _c, e = fit_rotated()
    assert e < 12, "mon_rotated fit is off: %.1f" % e
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    elif "--preview" in sys.argv:
        preview()
    elif "--write" in sys.argv:
        sys.exit(write())
    elif "--check" in sys.argv:
        bad = check()
        for b in bad:
            print("FAIL", b)
        sys.exit(1 if bad else 0)
    else:
        print(__doc__)
