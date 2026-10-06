"""Offline analysis of M_SurfaceBank_Natural graph dumps written by the ground chat.

OFFLINE ONLY: never imports unreal. Input is any receipt JSON whose 'nodes' (or
'before'/'after' -> 'nodes') map uses the describe() schema of
Staging/GroundPainting_2026-10-04/native_graph_stochastic.py:246 (class, edges
{pin: {source, output}}, properties, input_names, output_names, layers).

Usage:
  python graph_dump_tools.py facts <receipt.json> [key]         -> JSON facts to stdout
  python graph_dump_tools.py diff  <old.json> <new.json> [okey nkey] -> node/edge diff
  python graph_dump_tools.py uasset <file.uasset> [...]         -> header names/exports/imports

The digest equals the receipts' graph_sha256 (sha256 of json.dumps(nodes, sort_keys=True)).
"""
import collections
import hashlib
import json
import struct
import sys

PREFIX = '/Game/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural.M_SurfaceBank_Natural:MaterialExpression'
ACTIVE = ('Sand_01', 'Sand_02', 'Dirt_Path', 'Sand_Path')  # Ground/Steep/RoadBed/BuildingPad (LW:18-19)
GRASS_OWNER = 'GeoCity_LandscapeGrass'                        # LW:12, :278, :323


def short(name):
    return name.replace(PREFIX, '') if name else name


def load(path, key=None):
    data = json.load(open(path, encoding='utf-8-sig'))
    if key:
        data = data[key]
    if 'nodes' not in data:
        raise SystemExit('no nodes in ' + path)
    return data


def digest(nodes):
    return hashlib.sha256(json.dumps(nodes, sort_keys=True).encode()).hexdigest()


def consumers(nodes):
    out = collections.defaultdict(list)
    for name, row in nodes.items():
        for pin, edge in row['edges'].items():
            if edge['source']:
                out[edge['source']].append((name, pin))
    return out


def reach(nodes, start):
    seen, stack = set(), [start]
    while stack:
        cur = stack.pop()
        if cur in seen or cur not in nodes:
            continue
        seen.add(cur)
        stack.extend(e['source'] for e in nodes[cur]['edges'].values() if e['source'])
    return seen


def facts(dump):
    nodes, roots = dump['nodes'], {k: v for k, v in dump['roots'].items() if v}
    cons = consumers(nodes)
    grass_out = [k for k, v in nodes.items() if v['class'] == 'MaterialExpressionLandscapeGrassOutput']
    grass = set().union(*(reach(nodes, g) for g in grass_out)) if grass_out else set()
    every = set(grass)
    for root in roots.values():
        every |= reach(nodes, root)
    per_layer, active = {}, set(grass)
    for prop, root in roots.items():
        for layer in ACTIVE:
            edge = nodes[root]['edges'].get('Layer ' + layer) or {}
            got = reach(nodes, edge['source']) if edge.get('source') else set()
            per_layer[prop + '/' + layer] = {'input': short(edge.get('source')), 'nodes': len(got)}
            active |= got
    blends = {}
    for name, row in nodes.items():
        if row['class'] != 'MaterialExpressionLandscapeLayerBlend':
            continue
        blends[short(name)] = {
            'root': next((p for p, r in roots.items() if r == name), None),
            'consumers': len(cons.get(name, [])),
            'layers': len(row.get('layers', [])),
            'connected_layer_pins': sum(1 for p, e in row['edges'].items() if e['source'] and p.startswith('Layer ')),
            'height_pins': [p for p in row['input_names'] if p.startswith('Height ')],
            'blend_types': dict(collections.Counter(str(l['blend_type']) for l in row.get('layers', []))),
            'active_inputs': {l: short((row['edges'].get('Layer ' + l) or {}).get('source')) for l in ACTIVE}}
    samples = {}
    for name in sorted(active):
        row = nodes[name]
        if row['class'] != 'MaterialExpressionTextureSample':
            continue
        tex = row['edges'].get('Tex', {}).get('source')
        p = row['properties']
        samples[short(name)] = {'desc': p.get('desc'), 'sampler_type': p.get('sampler_type'),
                                'sampler_source': p.get('sampler_source'), 'mip_value_mode': p.get('mip_value_mode'),
                                'texture_parameter': nodes[tex]['properties'].get('parameter_name') if tex in nodes else None}
    calls = {short(n): {'function': nodes[n]['properties'].get('material_function'),
                        'inputs': {p: short(e['source']) for p, e in nodes[n]['edges'].items() if e['source']}}
             for n in sorted(active) if nodes[n]['class'] == 'MaterialExpressionMaterialFunctionCall'}
    params = collections.defaultdict(list)
    for name, row in nodes.items():
        pname = row['properties'].get('parameter_name')
        if pname:
            params[pname].append({'node': short(name), 'class': row['class'].replace('MaterialExpression', ''),
                                  'default': row['properties'].get('default_value', row['properties'].get('texture')),
                                  'live_any_root': name in every, 'live_active_layers': name in active})
    return {
        'graph_sha256': digest(nodes), 'node_count': len(nodes),
        'class_counts': dict(collections.Counter(v['class'].replace('MaterialExpression', '') for v in nodes.values()).most_common()),
        'desc_prefix_counts': dict(collections.Counter((v['properties'].get('desc') or '').split(':')[0] or '<none>' for v in nodes.values())),
        'reachable_any_root_plus_grass': len(every), 'reachable_active4_plus_grass': len(active),
        'roots': {k: short(v) for k, v in roots.items()}, 'material_settings': dump.get('material_settings'),
        'landscape_layer_blends': blends, 'per_root_layer': per_layer,
        'active_texture_samples': samples,
        'sampler_source_census_all_texture_samples': dict(collections.Counter(
            v['properties'].get('sampler_source') for v in nodes.values() if v['class'] == 'MaterialExpressionTextureSample')),
        'active_function_calls': calls,
        'grass_nodes': {short(n): {'class': nodes[n]['class'], 'desc': nodes[n]['properties'].get('desc'),
                                   'parameter_name': nodes[n]['properties'].get('parameter_name'),
                                   'default': nodes[n]['properties'].get('default_value'),
                                   'grass_types': nodes[n].get('grass_types'),
                                   'inputs': {p: short(e['source']) for p, e in nodes[n]['edges'].items() if e['source']}}
                        for n in sorted(grass)},
        'grass_owner_prefixed_nodes': sum(1 for v in nodes.values() if str(v['properties'].get('desc', '')).startswith(GRASS_OWNER)),
        'parameter_name_count': len(params),
        'duplicated_parameter_names': sorted(k for k, v in params.items() if len(v) > 1),
        'parameters': {k: v for k, v in sorted(params.items())},
        'editor_extent_by_desc_prefix': {k: [min(x for x, _ in pts), max(x for x, _ in pts), min(y for _, y in pts), max(y for _, y in pts)]
                                         for k, pts in _extent(nodes).items()}}


def _extent(nodes):
    out = collections.defaultdict(list)
    for row in nodes.values():
        p = row['properties']
        if p.get('material_expression_editor_x') is not None:
            out[(p.get('desc') or '').split(':')[0] or '<none>'].append((p['material_expression_editor_x'], p['material_expression_editor_y']))
    return out


def diff(old, new):
    """Node/edge/property diff. Mirrors native_graph_revision.py:496-505 but reports instead of asserting.
    Height-blend edits legitimately add 'Height <layer>' pins and change 'layers' rows."""
    o, n = old['nodes'], new['nodes']
    result = {'added_nodes': sorted(short(k) for k in set(n) - set(o)),
              'removed_nodes': sorted(short(k) for k in set(o) - set(n)),
              'changed_edges': [], 'changed_properties': [], 'changed_pin_sets': [], 'changed_layers': []}
    for key in sorted(set(o) & set(n)):
        a, b = o[key], n[key]
        if set(a['edges']) != set(b['edges']):
            result['changed_pin_sets'].append({'node': short(key), 'added': sorted(set(b['edges']) - set(a['edges'])),
                                               'removed': sorted(set(a['edges']) - set(b['edges']))})
        for pin in sorted(set(a['edges']) & set(b['edges'])):
            if a['edges'][pin] != b['edges'][pin]:
                result['changed_edges'].append({'node': short(key), 'pin': pin, 'before': short(a['edges'][pin]['source']),
                                                'after': short(b['edges'][pin]['source'])})
        if a.get('properties') != b.get('properties'):
            keys = set(a['properties']) | set(b['properties'])
            result['changed_properties'].append({'node': short(key), 'fields': sorted(k for k in keys if a['properties'].get(k) != b['properties'].get(k))})
        if a.get('layers') != b.get('layers'):
            result['changed_layers'].append(short(key))
    result['old_sha256'], result['new_sha256'] = digest(o), digest(n)
    return result


def _fstr(b, o):
    n = struct.unpack_from('<i', b, o)[0]; o += 4
    if n == 0:
        return '', o
    if n > 0:
        return b[o:o + n - 1].decode('latin1'), o + n
    return b[o:o - 2 * n - 2].decode('utf-16le'), o - 2 * n


def uasset_header(path):
    """Minimal FPackageFileSummary read for UE 5.8 (legacy -9, UE5 1018). Names, exports, imports."""
    b = open(path, 'rb').read()
    tag, legacy = struct.unpack_from('<Ii', b, 0); o = 8
    assert tag == 0x9E2A83C1, 'not a uasset'
    if legacy != -4:
        o += 4
    ue4 = struct.unpack_from('<i', b, o)[0]; o += 4
    ue5 = None
    if legacy <= -8:
        ue5 = struct.unpack_from('<i', b, o)[0]; o += 4
    o += 4  # licensee
    total_header = None
    if ue5 is not None and ue5 >= 1015:  # saved hash + header size precede custom versions
        o += 20; total_header = struct.unpack_from('<i', b, o)[0]; o += 4
    count = struct.unpack_from('<i', b, o)[0]; o += 4 + count * 20
    if total_header is None:
        total_header = struct.unpack_from('<i', b, o)[0]; o += 4
    package, o = _fstr(b, o)
    flags, name_count, name_offset = struct.unpack_from('<Iii', b, o); o += 12
    if ue5 and ue5 >= 1008:
        o += 8
    if not flags & 0x80000000:
        _, o = _fstr(b, o)
    o += 8  # gatherable text
    exports, _, imports, _ = struct.unpack_from('<iiii', b, o)
    names, p = [], name_offset
    for _ in range(name_count):
        s, p = _fstr(b, p); p += 4; names.append(s)
    return {'file': path, 'size': len(b), 'sha256': hashlib.sha256(b).hexdigest(), 'ue4': ue4, 'ue5': ue5,
            'package': package, 'total_header_size': total_header, 'names': name_count, 'exports': exports,
            'imports': imports, 'referenced_packages': sorted(n for n in names if n.startswith('/Game/')),
            'name_table_sha256': hashlib.sha256('\n'.join(sorted(names)).encode()).hexdigest()}


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'facts':
        print(json.dumps(facts(load(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)), indent=1))
    elif mode == 'diff':
        ok = sys.argv[4] if len(sys.argv) > 4 else None
        nk = sys.argv[5] if len(sys.argv) > 5 else None
        print(json.dumps(diff(load(sys.argv[2], ok), load(sys.argv[3], nk)), indent=1))
    elif mode == 'uasset':
        print(json.dumps([uasset_header(p) for p in sys.argv[2:]], indent=1))
    else:
        raise SystemExit(__doc__)
