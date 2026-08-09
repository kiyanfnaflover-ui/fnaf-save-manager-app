import os
import struct

"""UE4 GVAS save parser for Five Nights at Freddy's: Help Wanted.

Binary layout (per property):
  nameFString + typeFString + size(int32) + arrayIndex(int32) + value

Type payloads (validated against Player00.sav):
  IntProperty/FloatProperty : 0x00 + value(int32/float32)
  BoolProperty               : 0x01/0x00 + 0x00
  StrProperty                : 0x00 + FString
  SetProperty                : arrayIndex(0) + elemType:FString + 0x00*5
                               + count(int32) + count * value
"""


def fstr_bytes(s):
    b = s.encode('utf-8') + b'\x00'
    return struct.pack('<i', len(b)) + b


def rd_fstr(data, o):
    n = struct.unpack_from('<i', data, o)[0]
    raw = data[o + 4:o + 4 + n]
    return raw.rstrip(b'\x00').decode('utf-8', 'replace'), o + 4 + n


def rd_i32(data, o):
    return struct.unpack_from('<i', data, o)[0]


class GvasSave:
    """Loads, edits and writes a Help Wanted GVAS save file."""

    PROP_NAMES = [
        'LevelInfo', 'Prizes', 'CollectedGlitches', 'HasPlayedMenuInstructions',
        'HUBUpdateVOListenedTo', 'HUBUpdateVOCollected', 'NumberOfGamesWon',
        'NumberOfGamesLost', 'ObjectsEaten', 'CollectedCoins', 'EULAAgreed',
        'Has_Seen_H_Title', 'DarkRideHighScore', 'GammaSettings', 'GammaSliderPOS',
    ]

    def __init__(self, file_path):
        self.file_path = str(file_path)
        self.data = None
        self.props = []
        self.none_pos = 0

    # ---------- loading ----------

    def load(self):
        with open(self.file_path, 'rb') as f:
            self.data = f.read()
        self.props, self.none_pos = self.parse(self.data)
        return self

    def parse(self, data):
        offs, none_pos = self._scan_offsets(data)
        bounds = offs + [none_pos]
        props = []
        for i, nm in enumerate(self.PROP_NAMES):
            o = offs[i]
            end = bounds[i + 1]
            name, o = rd_fstr(data, o)
            typ, o = rd_fstr(data, o)
            size_pos = o
            size = rd_i32(data, o)
            arr = rd_i32(data, o + 4)
            value_start = o + 8
            p = {
                'name': name, 'type': typ, 'start': offs[i], 'end': end,
                'size_pos': size_pos, 'size': size, 'arr': arr,
                'value_start': value_start,
            }
            if typ == 'IntProperty':
                assert value_start + 5 == end, (nm, value_start, end)
                p['value_pos'] = value_start + 1
                p['value'] = rd_i32(data, value_start + 1)
            elif typ == 'FloatProperty':
                assert value_start + 5 == end, (nm, value_start, end)
                p['value_pos'] = value_start + 1
                p['value'] = struct.unpack_from('<f', data, value_start + 1)[0]
            elif typ == 'BoolProperty':
                assert value_start + 2 == end, (nm, value_start, end)
                p['value_pos'] = value_start
                p['value'] = data[value_start]
            elif typ == 'StrProperty':
                sv = value_start + 1
                s, se = rd_fstr(data, sv)
                assert se == end, (nm, sv, end)
                p['value_pos'] = sv
                p['value'] = s
            elif typ == 'SetProperty':
                o2 = value_start
                elem_type, o2 = rd_fstr(data, o2)
                assert data[o2:o2 + 5] == b'\x00' * 5, nm
                o2 += 5
                count = rd_i32(data, o2)
                o2 += 4
                p['elem_type'] = elem_type
                items = []
                for _ in range(count):
                    if elem_type == 'IntProperty':
                        items.append(rd_i32(data, o2))
                        o2 += 4
                    elif elem_type == 'ObjectProperty':
                        s, o2 = rd_fstr(data, o2)
                        items.append(s)
                    else:
                        raise ValueError('unsupported set elem %r' % elem_type)
                assert o2 == end, (nm, o2, end)
                p['value'] = items
            props.append(p)
        return props, none_pos

    def _scan_offsets(self, data):
        offs, pos = [], 0
        for nm in self.PROP_NAMES:
            needle = fstr_bytes(nm)
            i = data.find(needle, pos)
            if i < 0:
                raise ValueError('property name not found: %r' % nm)
            offs.append(i)
            pos = i + len(needle)
        none_pos = data.find(fstr_bytes('None'), pos)
        if none_pos < 0:
            raise ValueError('None terminator not found')
        return offs, none_pos

    # ---------- access ----------

    def get(self, name, default=None):
        for p in self.props:
            if p['name'] == name:
                return p.get('value', default)
        return default

    def set(self, name, value):
        for p in self.props:
            if p['name'] == name:
                p['value'] = value
                return
        raise KeyError('unknown property %r' % name)

    # ---------- writing ----------

    def write(self):
        self.data = self.build(self.data, self.props, self.none_pos)
        return self.data

    def save(self, file_path=None):
        path = file_path or self.file_path
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(self.write())

    def build(self, data, props, none_pos):
        parts = [data[:props[0]['start']]]
        for p in props:
            parts.append(self._build_region(data, p))
        parts.append(data[none_pos:])
        return b''.join(parts)

    def _build_region(self, data, p):
        if p['type'] == 'SetProperty':
            items = p['value']
            if p['elem_type'] == 'IntProperty':
                vals = b''.join(struct.pack('<i', v) for v in items)
                new_size = 8 + 4 * len(items)
            elif p['elem_type'] == 'ObjectProperty':
                vals = b''.join(fstr_bytes(v) for v in items)
                new_size = 8 + len(vals)
            else:
                raise ValueError('unsupported set elem %r' % p['elem_type'])
            body = (struct.pack('<i', 0) + fstr_bytes(p['elem_type']) +
                    b'\x00' * 5 + struct.pack('<i', len(items)) + vals)
            return (fstr_bytes(p['name']) + fstr_bytes(p['type']) +
                    struct.pack('<i', new_size) + body)
        if p['type'] in ('IntProperty', 'FloatProperty', 'StrProperty', 'BoolProperty'):
            if p['type'] == 'IntProperty':
                newval = b'\x00' + struct.pack('<i', int(p['value']))
            elif p['type'] == 'FloatProperty':
                newval = b'\x00' + struct.pack('<f', float(p['value']))
            elif p['type'] == 'StrProperty':
                newval = b'\x00' + fstr_bytes(str(p['value']))
            elif p['type'] == 'BoolProperty':
                by = b'\x01' if p['value'] else b'\x00'
                newval = by + b'\x00'
            if len(newval) != (p['end'] - p['value_start']):
                raise ValueError('region length mismatch for %s' % p['name'])
            return (fstr_bytes(p['name']) + fstr_bytes(p['type']) +
                    struct.pack('<i', p.get('size', 0)) + struct.pack('<i', 0) + newval)
        return data[p['start']:p['end']]