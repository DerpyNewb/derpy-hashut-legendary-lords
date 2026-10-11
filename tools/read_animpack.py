"""Read .animpack containers and the AnimFragmentBattle .bin files inside them.

RPFM carries these files in and out of a pack but cannot decode either one, so this is the
only route to "which animation slots does this unit actually have?" with RPFM shut.

.animpack   u32 entry count, then per entry: u16 path length, path, u32 size, data.
.bin (v4/3) u32 version, u32 subversion, name, MOUNT name, u16, skeleton, locomotion graph,
            u8, u8, u32 row count, then per row: u32 slot id, f32 blend, f32 weight, u8 flags,
            u32 unknown, u32 anim count, then per anim three strings (anim, .anm.meta,
            .snd.meta - the last two are often empty).

The mount name is the trap: it is an empty string on nearly every infantry bin, so a reader
that treats those two zero bytes as part of a u32 parses every foot unit and derails on all
341 mounted ones.

Slot ids are named by RPFM's own anim_ids_warhammer_3.csv, not by this file - see slot_names().

    py tools/read_animpack.py <file.animpack|file.bin> [--slots 1368-1433]
    py tools/read_animpack.py --selftest
"""
import os
import struct
import sys

ANIM_IDS = os.path.expandvars(
    r"%APPDATA%\FrodoWazEre\rpfm\config\schemas\anim_ids_warhammer_3.csv")

# PIKE_HIGH_READY .. PIKE_FRONT_ATTACK_5. Vanilla fills none of them; see docs/FORMATIONS.md 15.
PIKE_SLOTS = range(1368, 1434)


class _R:
    def __init__(self, b):
        self.b, self.o = b, 0

    def u8(self):
        v = self.b[self.o]; self.o += 1; return v

    def u16(self):
        v, = struct.unpack_from('<H', self.b, self.o); self.o += 2; return v

    def u32(self):
        v, = struct.unpack_from('<I', self.b, self.o); self.o += 4; return v

    def f32(self):
        v, = struct.unpack_from('<f', self.b, self.o); self.o += 4; return v

    def s(self):
        n = self.u16()
        v = self.b[self.o:self.o + n].decode('utf-8', 'replace'); self.o += n; return v


def read_animpack(data):
    """-> [(path, bytes)]. Raises if the entry table does not consume the file exactly."""
    r = _R(data)
    out = []
    for _ in range(r.u32()):
        path = r.s()
        n = r.u32()
        out.append((path, r.b[r.o:r.o + n]))
        r.o += n
    if r.o != len(data):
        raise ValueError('animpack: %d trailing bytes' % (len(data) - r.o))
    return out


def _s(text):
    b = text.encode('utf-8')
    return struct.pack('<H', len(b)) + b


def write_animpack(items):
    """[(path, bytes)] -> container bytes. Inverse of read_animpack."""
    out = struct.pack('<I', len(items))
    for path, data in items:
        out += _s(path) + struct.pack('<I', len(data)) + data
    return out


def write_bin(hdr, rows):
    """(header dict, [row dict]) -> fragment bytes. Inverse of read_bin."""
    out = struct.pack('<II', hdr['version'], hdr['subversion']) + _s(hdr['name']) \
        + _s(hdr['mount']) + struct.pack('<H', hdr['unk']) + _s(hdr['skeleton']) \
        + _s(hdr['graph']) + bytes([hdr['f1'], hdr['f2']]) + struct.pack('<I', len(rows))
    for r in rows:
        out += struct.pack('<IffBII', r['slot'], r['blend'], r['weight'],
                           r['flags'], r['unk'], len(r['anims']))
        for anim in r['anims']:
            out += _s(anim[0]) + _s(anim[1]) + _s(anim[2])
    return out


def read_bin(data):
    """-> (header dict, [row dict]). Rows carry 'slot' and 'anims'."""
    r = _R(data)
    hdr = {'version': r.u32(), 'subversion': r.u32(), 'name': r.s(), 'mount': r.s(),
           'unk': r.u16(), 'skeleton': r.s(), 'graph': r.s(), 'f1': r.u8(), 'f2': r.u8()}
    if (hdr['version'], hdr['subversion']) != (4, 3):
        raise ValueError('unsupported bin version %(version)s/%(subversion)s' % hdr)
    rows = []
    for _ in range(r.u32()):
        row = {'slot': r.u32(), 'blend': r.f32(), 'weight': r.f32(),
               'flags': r.u8(), 'unk': r.u32()}
        row['anims'] = [(r.s(), r.s(), r.s()) for _ in range(r.u32())]
        rows.append(row)
    if r.o != len(data):
        raise ValueError('bin: %d trailing bytes' % (len(data) - r.o))
    return hdr, rows


def parse_slot_table(text):
    """Slot id -> name, from RPFM's anim_ids csv or AssetEditor's AnimationSlots txt.

    The csv is id, tabs, name - and 4.0's has trailing tabs on three rows, so the name is the
    last NON-EMPTY cell, not the last cell. The txt is one name per line, line number = id,
    behind one BOM (two in _dlc24)."""
    lines = text.replace('﻿', '').splitlines()
    if '\t' not in text:
        return {i: n.strip() for i, n in enumerate(lines)}
    out = {}
    for line in lines:
        cells = [c.strip() for c in line.split('\t')]
        if cells[0].isdigit() and any(cells[1:]):    # 9.0's csv pads the id: "0   "
            out[int(cells[0])] = [c for c in cells[1:] if c][-1]
    return out


def slot_names(path=ANIM_IDS):
    """RPFM's slot id -> name table. Empty dict if RPFM is not installed."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as fh:
        return parse_slot_table(fh.read())


def _dump(path, keep=None):
    data = open(path, 'rb').read()
    items = [(path, data)]
    if path.endswith('.animpack'):
        items = read_animpack(data)
        print('%s: %d entries' % (os.path.basename(path), len(items)))
    names = slot_names()
    for p, b in items:
        hdr, rows = read_bin(b)
        print('\n=== %s  skeleton=%s mount=%r  %d rows'
              % (p.rsplit('/', 1)[-1], hdr['skeleton'], hdr['mount'], len(rows)))
        for row in sorted(rows, key=lambda x: x['slot']):
            if keep and row['slot'] not in keep:
                continue
            first = row['anims'][0][0] if row['anims'] else ''
            print('  %5d  %-28s %s' % (row['slot'], names.get(row['slot'], '?'),
                                       first.replace('\\', '/').rsplit('/', 2)[-1]))


def _selftest():
    # animpack round trip
    inner = _fake_bin([(1, 'a.anim'), (1429, 'b.anim')])
    pk = struct.pack('<I', 1) + struct.pack('<H', 4) + b'x.bin' [:4] \
        + struct.pack('<I', len(inner)) + inner
    items = read_animpack(pk)
    assert len(items) == 1 and items[0][0] == 'x.bi', items
    hdr, rows = read_bin(items[0][1])
    assert [r['slot'] for r in rows] == [1, 1429], rows
    assert rows[1]['anims'][0][0] == 'b.anim'

    # a non-empty mount name must not derail the header
    mounted = _fake_bin([(7, 'c.anim')], mount='wm_wh3_burning_chariot01')
    h2, r2 = read_bin(mounted)
    assert h2['mount'] == 'wm_wh3_burning_chariot01' and r2[0]['slot'] == 7, (h2, r2)

    # writers are the exact inverse, byte for byte, including the float fields
    assert write_bin(*read_bin(inner)) == inner
    assert write_bin(*read_bin(mounted)) == mounted
    assert write_animpack(read_animpack(pk)) == pk

    # trailing bytes are a failure, not a silent short read
    for bad, fn in ((pk + b'\x00', read_animpack), (inner + b'\x00', read_bin)):
        try:
            fn(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('trailing bytes not reported')

    # 4.0's csv has trailing tabs; AssetEditor's txt has a (double) BOM and no ids
    assert parse_slot_table('364 \t\t\tX\n365 \t\t\tRESURRECT\t\t \n') == {364: 'X', 365: 'RESURRECT'}
    assert parse_slot_table('﻿﻿MISSING_ANIM\r\nSTAND\r\n') == {0: 'MISSING_ANIM', 1: 'STAND'}

    n = slot_names()
    if n:
        assert n[1429] == 'PIKE_FRONT_ATTACK_1', n.get(1429)
        assert n[1368] == 'PIKE_HIGH_READY', n.get(1368)
        assert set(PIKE_SLOTS) <= set(n), 'pike band not covered by RPFM table'
    else:
        print('  (RPFM anim id table not found - slot names unchecked)')
    print('selftest OK')


def _fake_bin(slots, mount=''):
    def s(t):
        t = t.encode()
        return struct.pack('<H', len(t)) + t
    out = struct.pack('<II', 4, 3) + s('n') + s(mount) + struct.pack('<H', 0) \
        + s('humanoid01d') + s('g.xml') + bytes([0, 0]) + struct.pack('<I', len(slots))
    for slot, anim in slots:
        out += struct.pack('<IffBII', slot, 0.3, 1.0, 63, 0, 1) + s(anim) + s('') + s('')
    return out


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        _selftest()
    else:
        keep = None
        if '--slots' in sys.argv:
            lo, _, hi = sys.argv[sys.argv.index('--slots') + 1].partition('-')
            keep = set(range(int(lo), int(hi or lo) + 1))
        _dump(sys.argv[1], keep)
