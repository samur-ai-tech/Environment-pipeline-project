"""Paz Farm parcels, step 1 (Aviv 2026-10-09: extend every Paz-Farm-affected patch road to road, ground + crops).
Context map 1 m/px, north up, around the pin: Sentinel-2 (2026-09-21, 4 m) underneath, all OSM highways (tracks yellow,
others orange), OSM landuse outlines (farmland cyan, orchard green, other grey), the screenshot footprint (white), traced
plots (magenta) and fence v003 (red). Writes parcels_context.png + PARCELS_CONTEXT.json (OSM ways/landuse in metres from pin).
Run with the gis env python:  python -W ignore parcels_context.py
"""
import json, math
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent
SRC = Path(r'C:\Users\USER\Documents\Pipeline Environment\SourceData\KarmeiYosef_31850349_34907601_4km')
OSM = next(SRC.glob('acquisitions/*/*/osm/overpass_response.json'))
ZD = SRC / 'zones' / '20261008T131311Z'
REC = json.loads((HERE.parents[1] / 'NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/Zones/DATA_RECEIPT.json').read_text())
LAT0, LON0 = 31.850349, 34.907601
MLAT, MLON = REC['grid']['local_frame']['Mlat_m_per_deg'], REC['grid']['local_frame']['Mlon_m_per_deg']
pe, pn = json.loads((HERE / 'roads.json').read_text())['pin_local_m_from_area_centre']
en = lambda lon, lat: complex((lon - LON0) * MLON - pe, (lat - LAT0) * MLAT - pn)      # metres from the pin
HALF = 700                                                                             # map covers +-700 m around the pin
N = 2 * HALF
px = lambda z: (z.real + HALF, HALF - z.imag)                                          # metres -> image col,row

# Sentinel background: grid bounds -> metres from pin
b = REC['grid']['bounds_epsg4326']
ds = gdal.Open(str(ZD / 'S2_recent_2026-09-21.png'))
s2 = np.stack([ds.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3)], -1)
H2, W2 = s2.shape[:2]
west = en(b['west'], LAT0).real; north = en(LON0, b['north']).imag
mpp = (en(b['east'], LAT0).real - west) / W2
img = np.zeros((N, N, 3), np.uint8)
cols = ((np.arange(N) - HALF) - west) / mpp
rows = (north - (HALF - np.arange(N))) / mpp
ci = np.clip(cols.astype(int), 0, W2 - 1); ri = np.clip(rows.astype(int), 0, H2 - 1)
img[:] = s2[ri[:, None], ci[None, :]]


def line(z0, z1, col, w=1):
    (c0, r0), (c1, r1) = px(z0), px(z1)
    if max(abs(c0 - HALF), abs(r0 - HALF), abs(c1 - HALF), abs(r1 - HALF)) > 3 * HALF:
        return
    n = int(max(abs(c1 - c0), abs(r1 - r0))) + 1
    for k in range(n + 1):
        c = int(round(c0 + (c1 - c0) * k / n)); r = int(round(r0 + (r1 - r0) * k / n))
        if w <= c < N - w and w <= r < N - w:
            img[r - w:r + w + 1, c - w:c + w + 1] = col


osm = json.loads(OSM.read_text(encoding='utf-8'))
nodes = {e['id']: en(e['lon'], e['lat']) for e in osm['elements'] if e['type'] == 'node'}
ways = []
for e in osm['elements']:
    if e['type'] == 'way' and 'highway' in e.get('tags', {}):
        pts = [nodes[i] for i in e['nodes'] if i in nodes]
        if pts and min(abs(p) for p in pts) < HALF * 1.5:
            ways.append({'id': e['id'], 'highway': e['tags']['highway'], 'pts': [[round(p.real, 2), round(p.imag, 2)] for p in pts]})
lu = json.loads((ZD / 'landuse.geojson').read_text(encoding='utf-8'))
landuse = []
for f in lu['features']:
    g = f['geometry']; kind = str(f['properties'].get('kind', '?')).split('=')[-1]
    polys = g['coordinates'] if g['type'] == 'Polygon' else [p[0] for p in g['coordinates']] if g['type'] == 'MultiPolygon' else []
    if g['type'] == 'Polygon':
        polys = [g['coordinates'][0]]
    for ring in polys:
        pts = [en(x, y) for x, y in ring]
        if min(abs(p) for p in pts) < HALF * 1.5:
            landuse.append({'kind': kind, 'id': f['properties'].get('@id') or f.get('id'), 'pts': [[round(p.real, 2), round(p.imag, 2)] for p in pts]})
for l in landuse:
    col = {'farmland': (0, 230, 255), 'orchard': (40, 220, 60)}.get(l['kind'], (150, 150, 150))
    P = [complex(*p) for p in l['pts']]
    for a, c in zip(P, P[1:]):
        line(a, c, col, 0)
for w in ways:
    col = (255, 230, 0) if w['highway'] == 'track' else (255, 140, 0)
    P = [complex(*p) for p in w['pts']]
    for a, c in zip(P, P[1:]):
        line(a, c, col, 1)
# screenshot footprint + traced plots + fence
FIT = json.loads((HERE / 'FIT.json').read_text()); A, B = complex(*FIT['a']), complex(*FIT['b'])
to_m = lambda c, r: A * complex(c, -r) + B
corners = [to_m(0, 0), to_m(1209, 0), to_m(1209, 850), to_m(0, 850)]
for i in range(4):
    line(corners[i], corners[(i + 1) % 4], (255, 255, 255), 1)
L = json.loads((HERE / 'LAYOUT.json').read_text())
for name, p in L['plots'].items():
    P = [complex(*q) for q in p['polygon_m']]
    for i in range(len(P)):
        line(P[i], P[(i + 1) % len(P)], (255, 0, 255), 0)
F = [complex(*v) for v in json.loads((HERE / 'FENCE_ROUTE_V003.json').read_text())['vertices_m']]
for i in range(len(F)):
    line(F[i], F[(i + 1) % len(F)], (255, 0, 0), 0)
# 100 m tick grid on the border
for k in range(-HALF, HALF + 1, 100):
    img[0:12, k + HALF - 1:k + HALF + 1] = 255; img[k + HALF - 1:k + HALF + 1, 0:12] = 255
drv = gdal.GetDriverByName('MEM').Create('', N, N, 3, gdal.GDT_Byte)
for i in range(3):
    drv.GetRasterBand(i + 1).WriteArray(img[:, :, i])
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'parcels_context.png'), drv)
(HERE / 'PARCELS_CONTEXT.json').write_text(json.dumps({'frame': 'metres east/north of the Paz Farm pin; image 1 m/px, pin at (700,700)',
    'osm_ways': ways, 'landuse': landuse, 'screenshot_corners_m': [[round(z.real, 2), round(z.imag, 2)] for z in corners]}, indent=1))
print(json.dumps({'ways': len(ways), 'tracks': sum(w['highway'] == 'track' for w in ways), 'landuse': len(landuse),
                  'landuse_kinds': sorted({l['kind'] for l in landuse})}))
