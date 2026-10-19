"""Offline. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69) (playbook 10c: props over open land). Marks every
generated small_prop of the current run (HDA_CATALOG_RECEIPT.json) KEEP when it lies within MARGIN_M of a road edge (OSM
centreline of any highway way in the source package, half the generator's class width added; construction ways use their
construction=* class) or within MARGIN_M of a building footprint (Buildings_v2/FOOTPRINTS.json); everything else REMOVE.
Positions: Unreal cm = (P0, P2, P1) * 100 (same mapping split_buildings verified to 0.008 cm). Writes
receipts/PROPS_PLAN.json for Tools/props_trim.py. Street props and poles are not touched. Run with any Python 3.
    python -B props_near_roads_plan.py --margin-m <metres, e.g. 30>
The landscape half-extent comes from Tools/area_constants.py (HALF_EXTENT_CM); MARGIN_M is a required input.
"""
import argparse, glob, hashlib, importlib.util, json, math, os, xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('area_constants', TASK / 'Tools' / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (refuses if not filled in)
assert TASK.name == A.TASK_FOLDER, (TASK.name, A.TASK_FOLDER)
WIDTH_M = {'secondary': 12.0, 'secondary_link': 7.0, 'tertiary': 9.0, 'residential': 7.0, 'service': 4.0, 'footway': 2.2,
           'path': 1.6, 'track': 3.0, 'unclassified': 6.0, 'trunk': 12.0, 'trunk_link': 7.0, 'primary': 10.0, 'primary_link': 7.0}
ap = argparse.ArgumentParser(); ap.add_argument('--margin-m', type=float, required=True); args = ap.parse_args()
M = args.margin_m * 100.0

receipt_path = TASK / 'HDA_CATALOG_RECEIPT.json'
R = json.loads(receipt_path.read_text(encoding='utf-8'))
pkg_path = Path(json.loads((TASK / 'ACQUISITION_RECEIPT.json').read_text(encoding='utf-8'))['package_path'])
pkg = json.loads(pkg_path.read_text(encoding='utf-8')); fr, o = pkg['local_frame'], pkg['origin']
UE = lambda lon, lat: ((lon - o['lon0']) * fr['Mlon_m_per_deg'] * 100.0, -(lat - o['lat0']) * fr['Mlat_m_per_deg'] * 100.0)
root = ET.parse(next((pkg_path.parent / 'osm').glob('*.osm'))).getroot()
nodes = {n.get('id'): UE(float(n.get('lon')), float(n.get('lat'))) for n in root.iter('node')}
BOX = A.HALF_EXTENT_CM + M + 2000.0
segs = []                                                     # (ax, ay, bx, by, half_width_cm)
for w in root.iter('way'):
    t = {k.get('k'): k.get('v') for k in w.findall('tag')}
    cls = t.get('highway')
    if cls == 'construction' and t.get('construction') in WIDTH_M:
        cls = t['construction']
    if cls not in WIDTH_M:
        continue
    pts = [nodes[nd.get('ref')] for nd in w.findall('nd')]
    for a, b in zip(pts, pts[1:]):
        if min(a[0], b[0]) > BOX or max(a[0], b[0]) < -BOX or min(a[1], b[1]) > BOX or max(a[1], b[1]) < -BOX:
            continue                                          # segment bounds miss the area (+ margin)
        segs.append((a[0], a[1], b[0], b[1], WIDTH_M[cls] * 50.0))
fps = json.loads((TASK / 'Buildings_v2' / 'FOOTPRINTS.json').read_text(encoding='utf-8'))['footprints_ue_cm']


def seg_d(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def inside(px, py, poly):
    c = False
    for i in range(len(poly)):
        x1, y1 = poly[i - 1]; x2, y2 = poly[i]
        if (y1 > py) != (y2 > py) and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


entries, why = [], Counter()
for i in R['instances']:
    if i.get('role') != 'small_prop':
        continue
    P = i['P']; x, y, z = P[0] * 100.0, P[2] * 100.0, P[1] * 100.0
    keep, reason = False, 'far'
    for ax, ay, bx, by, hw in segs:
        if abs(x - ax) > 2e5 and abs(x - bx) > 2e5 and (x - ax) * (x - bx) > 0:
            continue
        if seg_d(x, y, ax, ay, bx, by) <= hw + M:
            keep, reason = True, 'road'
            break
    if not keep:
        for k, poly in fps.items():
            if inside(x, y, poly) or min(seg_d(x, y, *poly[j - 1], *poly[j]) for j in range(len(poly))) <= M:
                keep, reason = True, 'building'
                break
    why[reason] += 1
    entries.append({'mesh': i['path'].split('.')[0], 'ue': [round(x, 2), round(y, 2), round(z, 2)], 'keep': keep,
                    'pid': i.get('placement_id')})
plan = {'schema': 'environmentpipeline.props_plan.v1', 'area_id': A.AREA_ID, 'margin_m': args.margin_m,
        'receipt_sha256': hashlib.sha256(receipt_path.read_bytes()).hexdigest(), 'road_segments': len(segs),
        'footprints': len(fps), 'small_props': len(entries), 'keep': sum(e['keep'] for e in entries),
        'remove': sum(not e['keep'] for e in entries), 'reasons': dict(why),
        'remove_by_mesh': dict(Counter(e['mesh'].rsplit('/', 1)[1] for e in entries if not e['keep']).most_common()),
        'entries': entries}
(TASK / 'receipts' / 'PROPS_PLAN.json').write_text(json.dumps(plan), encoding='utf-8')
print(json.dumps({k: v for k, v in plan.items() if k != 'entries'}, indent=1))
