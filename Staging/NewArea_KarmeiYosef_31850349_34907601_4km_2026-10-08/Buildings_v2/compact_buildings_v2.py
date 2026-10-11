"""Offline (Karmei Yosef operator, 2026-10-11; Aviv: "Split on the clone now"): compact per-building data from the CURRENT 4 km run (v002 regeneration) bank
receipt (HDA_CATALOG_RECEIPT.json, 428 MB). Houdini metres (Y up) -> Unreal cm guess X=P0*100, Y=P2*100, Z=P1*100 (verified
in-editor against real instance transforms before use; transforms themselves are never rebuilt from P).
Writes BUILDINGS_COMPACT.json and prints generated-part shape statistics."""
import hashlib, json, math
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
RP = HERE.parent / 'HDA_CATALOG_RECEIPT.json'
R = json.loads(RP.read_text(encoding='utf-8'))
ue = lambda P: [round(P[0] * 100.0, 2), round(P[2] * 100.0, 2), round(P[1] * 100.0, 2)]
mods = []
for m in R['building_module_instances']:
    mods.append({'osm': str(m['source_osm_id']), 'mesh': m['path'].split('.')[0], 'ue': ue(m['P']), 'key': m.get('module_key'),
                 'pid': m['placement_id']})
whole = []
for i in R['instances']:
    if i.get('role') == 'whole_building':
        whole.append({'osm': i['placement_id'].split('building_')[-1], 'mesh': i['path'].split('.')[0], 'ue': ue(i['P']), 'pid': i['placement_id']})
parts, shapes = [], Counter()
def is_rect(pts, tol_deg=2.0):
    if len(pts) != 4:
        return False
    for k in range(4):
        a, b, c = pts[k - 1], pts[k], pts[(k + 1) % 4]
        v1 = (a[0] - b[0], a[1] - b[1]); v2 = (c[0] - b[0], c[1] - b[1])
        n1, n2 = math.hypot(*v1), math.hypot(*v2)
        if n1 < 1e-6 or n2 < 1e-6:
            return False
        cosang = (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)
        if abs(cosang) > math.sin(math.radians(tol_deg)):
            return False
    return True
for rec in R['native_building_assembly_records']:
    osm = str(rec['source_feature']['osm_id'])
    for g in rec.get('generated_parts', []):
        o = g['outline_xz_m']
        rect = is_rect(o)
        shapes['rect' if rect else ('n%d' % len(o))] += 1
        parts.append({'osm': osm, 'role': g.get('role'), 'rect': rect, 'n': len(o), 'mat': g.get('material_path', '').split('.')[0],
                      'bottom': g.get('bottom_y_m'), 'top': g.get('top_y_m'), 'outline': o, 'id': g.get('part_id')})
roles = Counter(p['role'] for p in parts)
rect_by_role = Counter(p['role'] for p in parts if p['rect'])
doors = [m for m in mods if 'door' in (m['key'] or '').lower() or 'Door' in m['mesh']]
out = {'modules': mods, 'whole': whole, 'generated_parts': parts, 'unsupported': R['building_assembly'].get('unsupported', []),
       'stats': {'modules': len(mods), 'whole': len(whole), 'parts': len(parts), 'shapes': dict(shapes), 'roles': dict(roles),
                 'rect_by_role': dict(rect_by_role), 'doors': len(doors), 'buildings_with_modules': len({m['osm'] for m in mods}),
                 'module_meshes': len({m['mesh'] for m in mods}), 'part_keys': sorted({k for p in R['native_building_assembly_records'][0]['generated_parts'] for k in p})}}
out['receipt_sha256'] = hashlib.sha256(RP.read_bytes()).hexdigest()
(HERE / 'BUILDINGS_COMPACT.json').write_text(json.dumps(out), encoding='utf-8')
fp = {}
for rec in R['native_building_assembly_records']:
    fp[str(rec['source_feature']['osm_id'])] = [[round(x * 100, 1), round(z * 100, 1)] for x, z in rec['footprint_xz_m']]
for i in R['instances']:
    if i.get('role') == 'whole_building':
        fp[i['placement_id'].split('building_')[-1]] = [[round(x * 100, 1), round(z * 100, 1)] for x, z in i['footprint_xz_m']]
(HERE / 'FOOTPRINTS.json').write_text(json.dumps({'footprints_ue_cm': fp, 'receipt_sha256': out['receipt_sha256']}), encoding='utf-8')
print('footprints', len(fp), 'receipt', out['receipt_sha256'][:16])
print(json.dumps(out['stats'], indent=1))
print('door sample', doors[:2])
print('part sample', json.dumps(parts[0])[:500])
