"""Tower of Zharr seat art for a house that ships none, built from the house's own flag and colours.

    py tools/make_toz_seat_banner.py            write the files and a preview sheet
    py tools/make_toz_seat_banner.py --check    measure the files already written, write nothing

A claimed seat draws `dlc23_tower_of_zharr/claimed_seat_<faction key minus wh3_dlc23_chd_>.png`
(193x217), `claimed_seat_selected_<...>.png` when picked, and the tier navigation marks the seat's
owner with `tower_nav_seat_<...>.png` (20x20). With no file the panel falls back to Legion of
Azgorh's red banner, so every house without art claims under Azgorh's crest.

THE COLOURS ARE THE FACTION'S BANNER COLUMNS, measured, not chosen: every seat banner that ships has
its cloth in the faction's `banner_colour_primary` and its device in `banner_colour_secondary`
(Azgorh C31515 red cloth, the Conclave 704848, Khorakk E57300 cloth with an E6B607 gold arrow, the
Kraken 943A36 with a C6DDDE device, Uzkulak 684106 with FFFFFF). The first build of this tool kept
IEE's orange cloth and a white device and was wrong for exactly that reason. Read the two values
out of the faction's row - RPFM's export for CA's factions, because the offline reader misaligns
CA's colour columns.

The banner is IEE's Uzkulak seat banner (its cloth is 684106) with the anchor blanked, the cloth
re-hued from 684106 to the house's primary, and the house's flag device laid on in its secondary,
shaded by the cloth underneath so the folds show through. The device is lifted from the flag's
`mon_256.png` by asking each opaque pixel whether it is nearer the device colour or the field
colour, keeping the shapes that stay clear of the frame. The selected banner is the new one plus
exactly what IEE's selected banner adds to its plain one. The nav icon is white with a black ring,
like every nav icon that ships. No seat_slot_ file: that image is resolved through a seat
payload's confederated faction, and no seat payload names these houses.
"""
import colorsys
import io
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import read_pack_index as rpi  # noqa: E402

GAME = r"F:\SteamLibrary\steamapps\common\Total War WARHAMMER III\data"
IEE = r"F:\SteamLibrary\steamapps\workshop\content\1142710\3007996493\!cr_immortal_empires_expanded.pack"
TOZ = "ui/skins/default/dlc23_tower_of_zharr/"
OUT = os.path.join(ROOT, "Modding Files", "pack", *TOZ.split("/"))
PREVIEW = os.path.join(ROOT, ".skilltree_cache", "toz_seat_banner_preview.png")

# faction key -> (flag source, banner_colour_primary, banner_colour_secondary)
HOUSES = {
    # IEE's row, which this pack ships: khaki cloth, the dark brown of its skulls
    "cr_chd_skullstack": ((IEE, "ui/flags/cr_chd_skullstack/mon_256.png"), "989964", "44302A"),
    # CA's row (RPFM export of db.pack): teal cloth, red device
    "wh3_dlc23_chd_minor_faction": ((os.path.join(GAME, "ui.pack"), "ui/flags/wh3_dlc23_chd_minor_faction/mon_256.png"),
                                    "008080", "C31515"),
}
BASE = (IEE, TOZ + "claimed_seat_cr_chd_warfleet_of_uzkulak.png")
BASE_SEL = (IEE, TOZ + "claimed_seat_selected_cr_chd_warfleet_of_uzkulak.png")
FINIAL_BOTTOM = 46          # rows above this are the bull-skull finial and rod, never touched
WHITE = (242, 238, 230)     # the nav icons' white
FRAME_MARGIN = 0.12         # a device-coloured shape reaching this close to the flag's edge is frame


def rgb(hexs):
    return np.array([int(hexs[i:i + 2], 16) for i in (0, 2, 4)], float)


def png(src):
    pack, path = src
    d = rpi.read(pack, path)[0][2]
    if d[:4] != b"\x89PNG":                     # CA's ui packs: u32 length, then zstd
        import zstandard
        n, = struct.unpack("<I", d[:4])
        d = zstandard.ZstdDecompressor().decompress(d[4:], max_output_size=n)
    return Image.open(io.BytesIO(d)).convert("RGBA")


def names(key):
    k = key.replace("wh3_dlc23_chd_", "")
    return ("claimed_seat_%s.png" % k, "claimed_seat_selected_%s.png" % k, "tower_nav_seat_%s.png" % k)


def white_device(a):
    """Bool mask of a white device: bright, unsaturated, opaque, below the finial."""
    c = a[..., :3].astype(int)
    mx, mn = c.max(-1), c.min(-1)
    m = (a[..., 3] > 200) & (mx > 150) & ((mx - mn) / np.maximum(mx, 1) < 0.4)
    m[:FINIAL_BOTTOM] = False
    return m


def blur(x, r):
    k = np.exp(-0.5 * (np.arange(-3 * r, 3 * r + 1) / r) ** 2)
    k /= k.sum()
    x = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 0, x)
    return np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, x)


def blank(base):
    """The base banner with its device filled from the surrounding cloth (normalised convolution)."""
    a = np.asarray(base).astype(float)
    old = white_device(np.asarray(base))
    hole = np.asarray(Image.fromarray(old.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
    hole[:FINIAL_BOTTOM] = False                # the dilation must not reach the finial
    valid = ((a[..., 3] > 200) & ~hole).astype(float)
    out = a.copy()
    for r in (2, 4, 8):                          # small radius first keeps the folds' shading
        w = blur(valid, r)
        todo = hole & (w > 0.05)
        for c in range(3):
            fill = blur(a[..., c] * valid, r) / np.maximum(w, 1e-6)
            out[..., c][todo] = fill[todo]
        valid = np.maximum(valid, todo.astype(float))
        hole = hole & ~todo
    return out, old


CLOTH_VALUE = 0.68          # shipped banners' cloth median / their banner_colour_primary, by value:
                            # Khorakk 0.64, the Kraken 0.68 (Uzkulak's IEE cloth runs brighter, 0.89)


def is_cloth(a):
    """The base cloth's pixels: Uzkulak's orange-brown hue, saturated enough to be dyed. The finial
    and rod are blue-grey metal and the shadow is grey, so neither is touched."""
    px = a[..., :3] / 255
    mx, mn = px.max(-1), px.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    hue = np.array([colorsys.rgb_to_hsv(*p)[0] for p in px.reshape(-1, 3)]).reshape(px.shape[:2])
    return (a[..., 3] > 0) & (sat > 0.25) & (hue < 0.14)


def recolour(a, dst_hex):
    """Re-dye the cloth to dst: every cloth pixel takes dst's hue, and saturation and value are
    scaled so the cloth's median lands where the shipped banners' cloth sits against their primary.
    The base's own light and folds survive as the per-pixel variation around that median."""
    dh, ds, dv = colorsys.rgb_to_hsv(*(rgb(dst_hex) / 255))
    cloth = is_cloth(a)
    hsv = np.array([colorsys.rgb_to_hsv(*p) for p in (a[..., :3][cloth] / 255)])
    s_med, v_med = np.median(hsv[:, 1]), np.median(hsv[:, 2])
    hsv[:, 0] = dh
    hsv[:, 1] = np.clip(hsv[:, 1] * ds / max(s_med, 1e-6), 0, 1)
    hsv[:, 2] = np.clip(hsv[:, 2] * CLOTH_VALUE * dv / max(v_med, 1e-6), 0, 1)
    out = a.copy()
    out[..., :3][cloth] = np.array([colorsys.hsv_to_rgb(*p) for p in hsv]) * 255
    return out


def shapes(mask):
    """4-connected components of a bool mask, as lists of (y, x)."""
    seen, out = np.zeros_like(mask), []
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        stack, comp = [(y, x)], []
        seen[y, x] = True
        while stack:
            cy, cx = stack.pop()
            comp.append((cy, cx))
            for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        out.append(comp)
    return out


def device(flag, field_hex, ink_hex):
    """Alpha (0..1) of the flag's device, cropped to its bounding box: the opaque pixels nearer the
    device colour than the field colour, in shapes that stay clear of the frame."""
    f = np.asarray(flag).astype(float)
    d_ink = np.linalg.norm(f[..., :3] - rgb(ink_hex), axis=-1)
    d_field = np.linalg.norm(f[..., :3] - rgb(field_hex), axis=-1)
    ink = (f[..., 3] > 200) & (d_ink < d_field)
    H, W = ink.shape
    my, mx = H * FRAME_MARGIN, W * FRAME_MARGIN
    keep = np.zeros_like(ink)
    for comp in shapes(ink):
        ys, xs = zip(*comp)
        if len(comp) >= 12 and min(ys) > my and max(ys) < H - my and min(xs) > mx and max(xs) < W - mx:
            keep[tuple(zip(*comp))] = True
    near = np.asarray(Image.fromarray(keep.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(3))) > 0
    alpha = np.clip(0.5 + (d_field - d_ink) / 60, 0, 1) * near * (f[..., 3] > 200)
    ys, xs = np.nonzero(keep)
    return alpha[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def place(alpha, box_w, box_h):
    """Device alpha resized to fit box_w x box_h, keeping its proportions."""
    h, w = alpha.shape
    s = min(box_w / w, box_h / h)
    im = Image.fromarray((alpha * 255).astype(np.uint8)).resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
    return np.asarray(im).astype(float) / 255


def build(key):
    flag_src, cloth_hex, ink_hex = HOUSES[key]
    base, base_sel = png(BASE), png(BASE_SEL)
    blanked, old = blank(base)
    cloth = recolour(blanked, cloth_hex)
    ys, xs = np.nonzero(old)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    flag = png(flag_src)
    dev = place(device(flag, cloth_hex, ink_hex), (xs.max() - xs.min()) * 1.15, (ys.max() - ys.min()) * 1.1)
    h, w = dev.shape
    # centred where the old device was, but never up into the finial's rod
    top, left = max(int(round(cy - h / 2)), FINIAL_BOTTOM + 2), int(round(cx - w / 2))
    out = cloth.copy()
    region = out[top:top + h, left:left + w]
    a = dev[..., None] * (region[..., 3:4] > 200)          # only on the cloth
    # the device in its colour, shaded by the cloth's own light so the folds run through it
    lum = region[..., :3] @ [0.299, 0.587, 0.114]
    shade = np.clip(lum / max(np.median(lum[region[..., 3] > 200]), 1), 0.75, 1.25)[..., None]
    paint = np.clip(rgb(ink_hex) * (0.8 + 0.2 * shade), 0, 255)
    region[..., :3] = region[..., :3] * (1 - a) + paint * a
    plain = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")
    glow = np.asarray(base_sel).astype(float) - np.asarray(base).astype(float)
    sel = Image.fromarray(np.clip(out + glow, 0, 255).astype(np.uint8), "RGBA")
    # nav icon: the device in white with a black ring, 20x20 like every nav icon that ships
    d16 = place(device(flag, cloth_hex, ink_hex), 16, 16)
    canvas = np.zeros((20, 20))
    t, l = (20 - d16.shape[0]) // 2, (20 - d16.shape[1]) // 2
    canvas[t:t + d16.shape[0], l:l + d16.shape[1]] = d16
    ring = np.asarray(Image.fromarray((canvas * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))).astype(float) / 255
    nav = np.zeros((20, 20, 4))
    nav[..., :3] = np.array(WHITE) * canvas[..., None]
    nav[..., 3] = np.maximum(ring, canvas) * 255
    return plain, sel, Image.fromarray(nav.astype(np.uint8), "RGBA"), base, old


def cloth_colour(a):
    """Median colour of a banner's cloth: opaque, below the finial, away from the device box."""
    m = a[..., 3] > 240
    m[:FINIAL_BOTTOM] = False
    m[FINIAL_BOTTOM:105, 50:145] = False
    return np.median(a[..., :3][m], 0)


def measure(key, plain, sel, nav, base, old):
    """What has to be true of the three files, measured."""
    _src, cloth_hex, ink_hex = HOUSES[key]
    bad = []
    p, b = np.asarray(plain).astype(float), np.asarray(base).astype(float)
    if plain.size != base.size or sel.size != base.size or nav.size != (20, 20):
        return ["%s: sizes %s %s %s" % (key, plain.size, sel.size, nav.size)]
    if not np.array_equal(p[..., 3] > 0, b[..., 3] > 0):
        bad.append("%s: the banner's outline changed" % key)
    metal = ~is_cloth(b)[:FINIAL_BOTTOM]
    if not np.array_equal(p[:FINIAL_BOTTOM][metal], b[:FINIAL_BOTTOM][metal]):
        bad.append("%s: the finial changed" % key)
    if (old & white_device(p.astype(np.uint8))).sum() > 0.6 * old.sum():
        bad.append("%s: the base banner's white device is still there" % key)
    # the cloth is the faction's banner_colour_primary: same hue, unlike the base's
    want_h = colorsys.rgb_to_hsv(*(rgb(cloth_hex) / 255))[0]
    got = colorsys.rgb_to_hsv(*(cloth_colour(p) / 255))
    dh = min(abs(got[0] - want_h), 1 - abs(got[0] - want_h))
    if got[1] > 0.12 and dh > 0.04:
        bad.append("%s: cloth hue %.2f, banner_colour_primary %s is %.2f" % (key, got[0], cloth_hex, want_h))
    # the device is drawn, in banner_colour_secondary
    box = p[FINIAL_BOTTOM:110, 50:145]
    near = (np.linalg.norm(box[..., :3] - rgb(ink_hex), axis=-1) < 70) & (box[..., 3] > 200)
    if near.sum() < 0.3 * old.sum():
        bad.append("%s: %d device pixels in %s, expected near %d" % (key, near.sum(), ink_hex, old.sum()))
    if (np.asarray(nav)[..., 3] > 0).sum() < 60:
        bad.append("%s: nav icon nearly empty" % key)
    return bad


def main():
    bad, tiles = [], []
    for key in HOUSES:
        plain, sel, nav, base, old = build(key)
        files = dict(zip(names(key), (plain, sel, nav)))
        if "--check" in sys.argv:
            files = {n: Image.open(os.path.join(OUT, n)).convert("RGBA") for n in files}
            plain, sel, nav = files.values()
        bad += measure(key, plain, sel, nav, base, old)
        if "--check" not in sys.argv:
            os.makedirs(OUT, exist_ok=True)
            for n, im in files.items():
                im.save(os.path.join(OUT, n))
                print("wrote", os.path.join(TOZ, n))
        tiles += [png(HOUSES[key][0]).resize((193, 193)), plain, sel, nav.resize((100, 100), Image.NEAREST)]
    sheet = Image.new("RGBA", (sum(t.width + 10 for t in tiles[:4]) + 10, 237 * len(HOUSES)), (40, 36, 34, 255))
    for i, t in enumerate(tiles):
        row, col = divmod(i, 4)
        x = 10 + sum(tt.width + 10 for tt in tiles[row * 4:row * 4 + col])
        sheet.alpha_composite(t, (x, 10 + row * 237))
    os.makedirs(os.path.dirname(PREVIEW), exist_ok=True)
    sheet.save(PREVIEW)
    print("preview", PREVIEW)
    for b in bad:
        print("FAIL", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
