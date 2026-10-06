"""Offline, read-only UE5 (FileVersionUE5 1009, legacy -8) .uasset header + tagged-property reader.
Never imports unreal. Opens files read-only. Usage: python uasset_offline.py <file.uasset> [--props]
Written 2026-10-05 for Stage1 S1_Prep pack inventory (MWLandscapeAutoMaterial / HighPoly_Tree_Model).
"""
import struct, sys, json, os


class R:
    def __init__(s, b, o=0):
        s.b = b; s.o = o
    def i32(s):
        v = struct.unpack_from('<i', s.b, s.o)[0]; s.o += 4; return v
    def u32(s):
        v = struct.unpack_from('<I', s.b, s.o)[0]; s.o += 4; return v
    def i64(s):
        v = struct.unpack_from('<q', s.b, s.o)[0]; s.o += 8; return v
    def u16(s):
        v = struct.unpack_from('<H', s.b, s.o)[0]; s.o += 2; return v
    def u8(s):
        v = s.b[s.o]; s.o += 1; return v
    def f32(s):
        v = struct.unpack_from('<f', s.b, s.o)[0]; s.o += 4; return v
    def f64(s):
        v = struct.unpack_from('<d', s.b, s.o)[0]; s.o += 8; return v
    def raw(s, n):
        v = s.b[s.o:s.o + n]; s.o += n; return v
    def fstr(s):
        n = s.i32()
        if n == 0:
            return ''
        if n > 0:
            if n > 1 << 20: raise ValueError('bad fstr len')
            v = s.b[s.o:s.o + n - 1].decode('latin-1'); s.o += n; return v
        n = -n
        if n > 1 << 20: raise ValueError('bad fstr len')
        v = s.b[s.o:s.o + 2 * n - 2].decode('utf-16-le', 'replace'); s.o += 2 * n; return v


class Pkg:
    def __init__(s, path):
        s.path = path
        with open(path, 'rb') as fh:
            b = fh.read()
        s.b = b; r = R(b)
        assert r.u32() == 0x9E2A83C1, 'not a uasset'
        s.legacy = r.i32(); r.i32(); s.ue4 = r.i32(); s.ue5 = r.i32(); r.i32()
        nc = r.i32(); s.custom = [(r.raw(16).hex(), r.i32()) for _ in range(nc)]
        s.total_header = r.i32(); s.pkgname = r.fstr(); s.flags = r.u32()
        s.name_count = r.i32(); s.name_off = r.i32()
        if s.ue5 >= 1008:
            s.softpath_count = r.i32(); s.softpath_off = r.i32()
        s.editor = not (s.flags & 0x80000000)
        if s.editor:
            s.loc_id = r.fstr()
        r.i32(); r.i32()  # gatherable text
        s.exp_count = r.i32(); s.exp_off = r.i32(); s.imp_count = r.i32(); s.imp_off = r.i32()
        s.depends_off = r.i32(); s.softpkg_count = r.i32(); s.softpkg_off = r.i32(); r.i32(); r.i32()
        r.raw(16)
        if s.editor:
            r.raw(16)
        gc = r.i32(); r.raw(8 * gc)
        s.saved_by = (r.u16(), r.u16(), r.u16(), r.u32(), r.fstr())
        s.compat = (r.u16(), r.u16(), r.u16(), r.u32(), r.fstr())
        rr = R(b, s.name_off); s.names = []
        for _ in range(s.name_count):
            s.names.append(rr.fstr()); rr.u32()
        rr = R(b, s.imp_off); s.imports = []
        for _ in range(s.imp_count):
            cp = s.fn(rr); cn = s.fn(rr); outer = rr.i32(); on = s.fn(rr)
            pn = s.fn(rr) if s.editor else None
            if s.ue5 >= 1003:
                rr.i32()
            s.imports.append(dict(class_package=cp, class_name=cn, outer=outer, name=on, package=pn))
        rr = R(b, s.exp_off); s.exports = []
        for _ in range(s.exp_count):
            ci = rr.i32(); si = rr.i32(); ti = rr.i32(); oi = rr.i32(); on = s.fn(rr); of = rr.u32()
            ss = rr.i64(); so = rr.i64(); rr.i32(); rr.i32(); rr.i32()
            if s.ue5 >= 1006:
                rr.i32()
            rr.u32(); rr.i32(); isa = rr.i32()
            if s.ue5 >= 1003:
                rr.i32()
            rr.raw(20)
            s.exports.append(dict(class_index=ci, outer=oi, name=on, size=ss, offset=so, is_asset=isa))

    def fn(s, r):
        i = r.i32(); n = r.i32()
        if i < 0 or i >= len(s.names):
            raise ValueError('bad name idx %d' % i)
        v = s.names[i]
        return v if n == 0 else '%s_%d' % (v, n - 1)

    def ref(s, idx):
        if idx == 0:
            return None
        if idx < 0:
            k = -idx - 1
            if k >= len(s.imports): return '<badimp %d>' % idx
            im = s.imports[k]; parts = [im['name']]; o = im['outer']
            while o < 0:
                parts.append(s.imports[-o - 1]['name']); o = s.imports[-o - 1]['outer']
            if len(parts) == 1:
                return parts[0]
            return '/'.join(reversed(parts[1:])) + '.' + parts[0]
        if idx - 1 >= len(s.exports): return '<badexp %d>' % idx
        return 'export:' + s.exports[idx - 1]['name']

    def cls(s, ex):
        ci = ex['class_index']
        if ci < 0:
            return s.imports[-ci - 1]['name']
        if ci > 0:
            return 'export:' + s.exports[ci - 1]['name']
        return 'Class'


EXPR_INPUT_STRUCTS = ('ExpressionInput', 'ScalarMaterialInput', 'ColorMaterialInput', 'VectorMaterialInput', 'Vector2MaterialInput',
                      'MaterialAttributesInput', 'ShadingModelMaterialInput', 'StrataMaterialInput', 'SubstrateMaterialInput')
SIMPLE_STRUCTS = ('Vector', 'LinearColor', 'Guid', 'Vector2D', 'Color', 'IntPoint', 'Vector4', 'Quat', 'Rotator')


def read_props(p, r, end, depth=0):
    out = []
    while r.o < end:
        name = p.fn(r)
        if name == 'None':
            break
        typ = p.fn(r); size = r.i32(); aidx = r.i32()
        extra = None
        if typ == 'StructProperty':
            extra = p.fn(r); r.raw(16)
        elif typ == 'BoolProperty':
            extra = r.u8()
        elif typ in ('ByteProperty', 'EnumProperty', 'ArrayProperty', 'SetProperty'):
            extra = p.fn(r)
        elif typ == 'MapProperty':
            extra = (p.fn(r), p.fn(r))
        if r.u8():
            r.raw(16)
        vstart = r.o
        try:
            val = read_value(p, R(p.b, vstart), typ, extra, size, depth)
        except Exception as e:
            val = '<unparsed %s %dB: %s>' % (typ, size, e)
        r.o = vstart + size
        out.append((name if aidx == 0 else '%s[%d]' % (name, aidx), typ, extra, val))
    return out


def read_value(p, r, typ, extra, size, depth):
    if typ == 'BoolProperty': return bool(extra)
    if typ == 'IntProperty': return r.i32()
    if typ == 'UInt32Property': return r.u32()
    if typ == 'Int64Property': return r.i64()
    if typ == 'FloatProperty': return round(r.f32(), 6)
    if typ == 'DoubleProperty': return r.f64()
    if typ == 'NameProperty': return p.fn(r)
    if typ == 'StrProperty': return r.fstr()
    if typ in ('ObjectProperty', 'ClassProperty', 'InterfaceProperty'): return p.ref(r.i32())
    if typ == 'SoftObjectProperty':
        a = p.fn(r); b = r.fstr(); return a + (':' + b if b else '')
    if typ == 'EnumProperty': return p.fn(r)
    if typ == 'ByteProperty':
        return p.fn(r) if extra != 'None' else r.u8()
    if typ == 'TextProperty': return '<text %dB>' % size
    if typ == 'StructProperty':
        if extra in ('Vector', 'Rotator'): return [round(r.f64(), 4) for _ in range(3)]
        if extra == 'Vector2D': return [round(r.f64(), 4) for _ in range(2)]
        if extra in ('Vector4', 'Quat'): return [round(r.f64(), 4) for _ in range(4)]
        if extra == 'LinearColor': return [round(r.f32(), 4) for _ in range(4)]
        if extra == 'Color': return list(r.raw(4))
        if extra == 'Guid': return r.raw(16).hex()
        if extra == 'IntPoint': return [r.i32(), r.i32()]
        if extra == 'BoxSphereBounds' and size == 56:
            return {'origin': [round(r.f64(), 2) for _ in range(3)], 'extent': [round(r.f64(), 2) for _ in range(3)],
                    'radius': round(r.f64(), 2)}
        if extra == 'Box' and size == 49:
            return {'min': [round(r.f64(), 2) for _ in range(3)], 'max': [round(r.f64(), 2) for _ in range(3)], 'valid': r.u8()}
        if extra in EXPR_INPUT_STRUCTS and size >= 36:
            # FExpressionInput native serialize (UE5.2): Expression, OutputIndex, InputName, Mask, MaskR..A
            ex = p.ref(r.i32()); oi = r.i32(); nm = p.fn(r); m = [r.i32() for _ in range(5)]
            d = {'expr': ex, 'out': oi}
            if nm and nm != 'None': d['name'] = nm
            if m[0]: d['mask'] = ''.join(c for c, b in zip('RGBA', m[1:]) if b)
            if size > 36:
                d['extra_bytes'] = size - 36
            return d
        if depth > 8: return '<deep>'
        return dict((n, v) for n, t, e, v in read_props(p, r, r.o + size, depth + 1))
    if typ in ('ArrayProperty', 'SetProperty'):
        if typ == 'SetProperty': r.i32()
        n = r.i32(); inner = extra
        if n < 0 or n > 100000: raise ValueError('bad count %d' % n)
        if inner == 'StructProperty':
            p.fn(r); p.fn(r); isz = r.i32(); r.i32(); sname = p.fn(r); r.raw(16)
            if r.u8(): r.raw(16)
            items = []
            if sname in SIMPLE_STRUCTS:
                per = isz // max(n, 1)
                for _ in range(n):
                    items.append(read_value(p, R(p.b, r.o), 'StructProperty', sname, per, depth)); r.o += per
                return {'struct': sname, 'count': n, 'items': items}
            for _ in range(n):
                items.append(dict((nn, v) for nn, t, e, v in read_props(p, r, len(p.b), depth + 1)))
            return {'struct': sname, 'count': n, 'items': items}
        if inner in ('ByteProperty',):
            return list(r.raw(n)) if n < 64 else '<%d bytes>' % n
        items = []
        for _ in range(n):
            items.append(read_value(p, r, inner, 'None', 0, depth))
        return items
    if typ == 'MapProperty': return '<map %dB>' % size
    return '<%s %dB>' % (typ, size)


def export_props(p, ex):
    r = R(p.b, ex['offset'])
    return read_props(p, r, ex['offset'] + ex['size'])


def summary(path, props=False):
    p = Pkg(path)
    d = dict(file=path, size=os.path.getsize(path), saved_by='%d.%d.%d-%d %s' % p.saved_by, ue5=p.ue5,
             imports=[(i['class_name'], p.ref(-(k + 1))) for k, i in enumerate(p.imports) if i['class_name'] != 'Package'],
             packages=[i['name'] for i in p.imports if i['class_name'] == 'Package'],
             exports=[(p.cls(e), e['name'], e['size']) for e in p.exports])
    if props:
        d['props'] = {}
        for e in p.exports:
            try:
                d['props'][p.cls(e) + ':' + e['name']] = export_props(p, e)
            except Exception as ex:
                d['props'][p.cls(e) + ':' + e['name']] = 'ERR %s' % ex
    return p, d


if __name__ == '__main__':
    p, d = summary(sys.argv[1], '--props' in sys.argv)
    print(json.dumps(d, indent=1, default=str))
