"""Give the Chaos Dwarf naval horde its own army-banner badge, the way Malakai has one.

The badge on an army banner is the `horde` component in `ui/campaign ui/army_banner.twui.xml`,
and it is STATE-DRIVEN BY CULTURE KEY. CA ships one state per seafaring/flying culture and a
`normal` fallback:

    normal                      ui/skins/default/icon_horde.png       "Horde"          (a cart wheel)
    wh2_dlc11_cst_vampire_coast ui/skins/default/icon_horde_cst.png   -                (a ship's helm)
    wh2_main_def_dark_elves     ui/skins/warhammer2/icon_black_ark.png
    wh2_main_hef_high_elves     .../wh3_dlc27_hef_dragonship.png
    wh_main_dwf_dwarfs          ui/skins/default/icon_horde_dwf.png   "The Spirit of Grungni||..."

Chaos Dwarfs have no state, so our ships fall through to `normal` and show the generic cart
wheel with the tooltip "Horde". There is no DB column for this and no runtime call that can add
a state - `SetState` only selects one that already exists - so the only route is to ship the
file with a `wh3_dlc23_chd_chaos_dwarfs` state added.

That is a CA file override, which is why this is a script and not a checked-in blob: when CA
patches army_banner.twui.xml, re-run this and the override is rebuilt on top of the new file
instead of silently reverting their changes. It is additive - one state, nothing else touched -
and no vanilla Chaos Dwarf faction has a horde, so nothing but our ships can reach it.

Reuses `icon_horde_cst.png` (a ship's wheel, not a Vampire Coast device) so this adds NO new
asset. Swap ICON_GUID for a new <component_image> if a bespoke icon is ever drawn into
!!!derpy_chd_assets.pack.

    py tools/patch_army_banner.py            write Modding Files/pack/...
    py tools/patch_army_banner.py --check    verify only, write nothing
    py tools/patch_army_banner.py --selftest
"""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from read_pack_index import read                                        # noqa: E402

UI_PACK = (r"F:\SteamLibrary\steamapps\common\Total War WARHAMMER III"
           r"\data\ui3.pack")
SRC = "ui/campaign ui/army_banner.twui.xml"
DST = os.path.join(ROOT, "Modding Files", "pack", "ui", "campaign ui", "army_banner.twui.xml")

CULTURE = "wh3_dlc23_chd_chaos_dwarfs"
ANCHOR = "</wh_main_dwf_dwarfs>"          # insert straight after CA's dwarf state
ICON_GUID = "8D2739FB-E8D6-4CAD-846EA6CAE4EF6511"      # icon_horde_cst.png, already declared
STATE_GUID = "D3A7C1F0-4B62-4E19-9C41DE7F0A5B6231"     # ours, must not collide
IMAGE_GUID = "D3A7C1F0-4B62-4E19-9C41DE7F0A5B6232"

LOC_LABEL = "StateTooltip_derpy_chd_naval_horde"
TITLE = "Hellforged Ironclad"
BODY = "This lord's warship has access to Shipworks buildings."
TOOLTIP = "%s||%s" % (TITLE, BODY)

_STATE_TEMPLATE = (
    '<{c}\n'
    '\t\t\t\t\tthis="{sg}"\n'
    '\t\t\t\t\tname="{c}"\n'
    '\t\t\t\t\twidth="24"\n'
    '\t\t\t\t\theight="24"\n'
    '\t\t\t\t\ttooltip="{tip}"\n'
    '\t\t\t\t\ttooltiplabel="{lbl}"\n'
    '\t\t\t\t\tinteractive="true"\n'
    '\t\t\t\t\tdisabled="true"\n'
    '\t\t\t\t\tuniqueguid="{sg}">\n'
    '\t\t\t\t\t<imagemetrics>\n'
    '\t\t\t\t\t\t<image\n'
    '\t\t\t\t\t\t\tthis="{ig}"\n'
    '\t\t\t\t\t\t\tuniqueguid="{ig}"\n'
    '\t\t\t\t\t\t\tcomponentimage="{icon}"\n'
    '\t\t\t\t\t\t\twidth="24"\n'
    '\t\t\t\t\t\t\theight="24"/>\n'
    '\t\t\t\t\t</imagemetrics>\n'
    '\t\t\t\t</{c}>'
).format(c=CULTURE, sg=STATE_GUID, ig=IMAGE_GUID, icon=ICON_GUID, tip=TOOLTIP, lbl=LOC_LABEL)


def _nl(text):
    """CA ships this file CRLF; keep whatever it uses so the diff stays a single insert."""
    return "\r\n" if "\r\n" in text else "\n"


def vanilla():
    """CA's army_banner.twui.xml as text. ui3.pack stores it zstd-framed behind a u32 size."""
    for _path, compressed, data in read(UI_PACK, SRC):
        if compressed:
            import zstandard
            size = struct.unpack_from("<I", data, 0)[0]
            data = zstandard.ZstdDecompressor().decompress(data[4:], max_output_size=size)
        return data.decode("utf-8")
    raise SystemExit("%s not found in %s" % (SRC, UI_PACK))


def patch(text):
    check(text)
    nl = _nl(text)
    i = text.index(ANCHOR) + len(ANCHOR)
    return text[:i] + nl + "\t\t\t\t" + _STATE_TEMPLATE.replace("\n", nl) + text[i:]


def check(text):
    """Everything the insert assumes, asserted against CA's live file."""
    assert text.count(ANCHOR) == 1, "expected exactly one %s" % ANCHOR
    open_tag = '<horde' + _nl(text)
    assert open_tag in text and '</horde>' in text, "no horde component"
    horde = text[text.index(open_tag):text.index('</horde>')]
    assert ANCHOR in horde, "the dwarf state moved out of the horde component"
    assert 'componentimage="%s"' % ICON_GUID in horde, \
        "icon_horde_cst.png's component_image guid is gone - re-read the <componentimages> block"
    assert 'name="%s"' % CULTURE not in text, "CA now ships a %s state - drop this patch" % CULTURE
    assert STATE_GUID not in text and IMAGE_GUID not in text, "our guids collide with CA's"
    assert 'tooltipslocalised="true"' in horde, "tooltiplabel is not a loc key any more"


def _selftest():
    t = vanilla()
    check(t)
    out = patch(t)
    assert out.count('name="%s"' % CULTURE) == 1, "state not inserted exactly once"
    assert len(out) > len(t)
    body = out[out.index('<horde' + _nl(out)):out.index('</horde>')]
    assert 'name="%s"' % CULTURE in body, "state landed outside the horde component"
    # each guard must bite
    for broken, why in (
        (t.replace(ANCHOR, "", 1), "missing anchor"),
        (t.replace('componentimage="%s"' % ICON_GUID, 'componentimage="X"'), "icon guid gone"),
        (t.replace('name="wh_main_dwf_dwarfs"', 'name="%s"' % CULTURE), "CA shipped our state"),
    ):
        try:
            check(broken)
        except AssertionError:
            continue
        except ValueError:
            continue
        raise AssertionError("check() did not catch: %s" % why)
    print("selftest ok - state inserts once, all three guards bite")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        text = vanilla()
        out = patch(text)
        if "--check" in sys.argv:
            print("check ok: %s state would be added (%d -> %d bytes)"
                  % (CULTURE, len(text), len(out)))
        else:
            os.path.isdir(os.path.dirname(DST)) or os.makedirs(os.path.dirname(DST))
            with open(DST, "w", encoding="utf-8", newline="") as fh:
                fh.write(out)
            print("wrote %s (%d bytes)" % (DST, len(out)))
            print("  state    %s" % CULTURE)
            print("  icon     ui/skins/default/icon_horde_cst.png (a ship's wheel)")
            print("  tooltip  %s" % TOOLTIP)
            print("  loc key  uied_component_texts_localised_string_%s" % LOC_LABEL)
