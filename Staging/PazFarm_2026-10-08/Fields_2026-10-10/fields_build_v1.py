"""Step 3 of 'every field from the screenshot' (Aviv 2026-10-10: "Yes, build it"). Offline build data, metres from the pin.
Inputs: FIELDS_V1.json + fields_v1.tif (fields_v1.py), road_mask.png (Google road lines), WIDE_FIT.json, the Paz Farm fence
(FENCE_ROUTE_V003.json), the previous farm-interior ground mask v3 (kept inside the fence), OSM (road 44), footprints.
Field types and fills:
  orchard      Astra avocado or citrus (one species per field) on a row lattice 6 m x 4.5 m along the field's rows, 3 m margin
  rows         young citrus (scale 0.5) 4 m x 2.5 m, 1.5 m margin
  green_crop   low crop stand-ins in lines 3 m apart, a plant every 1.6 m, 2.6 m margin
  ploughed     tilled ground only (a weed every ~400 m2)
  bare         dry soil + a weed tuft every ~120 m2
  light        grey-white (saturation <= 13) -> greenhouse tunnels in rows; warm -> pale soil only
  structures   grey (saturation <= 15) -> greenhouse tunnels; otherwise left alone
  natural      left to the existing zone vegetation
  margins      shrubs every ~12 m (p 0.5) along every filled field edge, 1.5 m inside
Row direction: the field's measured row direction when the structure tensor is coherent (>= 0.15), else the field's long axis.
No points inside the Paz Farm fence (the farm keeps its own models), within 4 m of a road line, on buildings (+5 m).
Ground mask v4 (RGBA weights R tilled, G grass/weeds, B dirt/roads/light soil, A coverage) over a square frame; inside the
fence the v3 farm-interior weights are kept. Road 44 (OSM trunk) is written as a polyline for a separate asphalt strip.
Outputs: FIELD_PLANTS_V1.json, ROAD44.json, FARM_GROUND_V4.json, SourceData/.../zones/PazFarm/T_PazFarm_GroundMask_v4.png,
fields_clear_zone.png (zone frame), fields_build_preview.png
"""
import json, math
from pathlib import Path
import numpy as np
from osgeo import gdal, ogr
gdal.UseExceptions(); ogr.UseExceptions()
HERE = Path(__file__).resolve().parent; GEO = HERE.parent / 'Georef'
TASK4 = HERE.parents[1] / 'NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
SRC = Path(r'C:\Users\USER\Documents\Pipeline Environment\SourceData\KarmeiYosef_31850349_34907601_4km')
OUTDIR = SRC / 'zones' / 'PazFarm'
FIT = json.loads((HERE / 'WIDE_FIT.json').read_text()); FV = json.loads((HERE / 'FIELDS_V1.json').read_text())
REC = json.loads((TASK4 / 'Zones/DATA_RECEIPT.json').read_text())
FENCE = [tuple(v) for v in json.loads((GEO / 'FENCE_ROUTE_V003.json').read_text())['vertices_m']]
G3 = json.loads((GEO / 'FARM_GROUND_V3.json').read_text())
FOOT = json.loads((TASK4 / 'WPTrial/FOOTPRINTS.json').read_text())['footprints_ue_cm']
LAT0, LON0 = 31.850349, 34.907601
MLAT, MLON = REC['grid']['local_frame']['Mlat_m_per_deg'], REC['grid']['local_frame']['Mlon_m_per_deg']
pe, pn = json.loads((GEO / 'roads.json').read_text())['pin_local_m_from_area_centre']
rng = np.random.default_rng(20261013)
s, th, te, tn, X0, Y0 = FIT['scale_m_per_px'], math.radians(FIT['theta_deg']), FIT['te'], FIT['tn'], FIT['X0'], FIT['Y0']
c_, si_ = math.cos(th), math.sin(th)
GT_B = (te - s * c_ * X0 - s * si_ * Y0, s * c_, s * si_, tn - s * si_ * X0 + s * c_ * Y0, s * si_, -s * c_)   # screenshot px -> metres


def b_ds(path, dtype=gdal.GDT_Byte):
    d = gdal.Open(str(path)); a = d.GetRasterBand(1).ReadAsArray()
    m = gdal.GetDriverByName('MEM').Create('', a.shape[1], a.shape[0], 1, dtype); m.SetGeoTransform(GT_B); m.GetRasterBand(1).WriteArray(a)
    return m


# ---- 1 m working grid (pin metres) over the screenshot ----
E0, E1 = math.floor(GT_B[0]), math.ceil(GT_B[0] + 1691 * s); N1, N0 = math.ceil(GT_B[3]), math.floor(GT_B[3] - 832 * s)
GW, GH = E1 - E0, N1 - N0
def band0(ds):
    a = ds.GetRasterBand(1).ReadAsArray(); return a              # keep the dataset alive while reading (GDAL frees temporaries)


def warp(src, alg='near', dtype=gdal.GDT_Byte):
    return band0(gdal.Warp('', src, format='MEM', outputBounds=(E0, N0, E1, N1), width=GW, height=GH, resampleAlg=alg, outputType=dtype))
fid = warp(b_ds(HERE / 'fields_v1.tif', gdal.GDT_Int32), 'near', gdal.GDT_Int32)
roads = warp(b_ds(HERE / 'road_mask.png'), 'near') > 0
gx = E0 + np.arange(GW) + 0.5; gy = N1 - np.arange(GH) - 0.5
GE, GN = np.meshgrid(gx, gy)


def poly_mask(poly, E, N):
    m = np.zeros(E.shape, bool)
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        m ^= ((y1 > N) != (y2 > N)) & (E < (x2 - x1) * (N - y1) / ((y2 - y1) if y2 != y1 else 1e-9) + x1)
    return m


fence = poly_mask(FENCE, GE, GN)
bld = np.zeros((GH, GW), bool)
for poly in FOOT.values():
    ring = [(X / 100.0 - pe, -Y / 100.0 - pn) for X, Y in poly]
    if min(E0 - 20 <= x <= E1 + 20 and N0 - 20 <= y <= N1 + 20 for x, y in ring):
        xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
        c0, c1 = int(max(0, min(xs) - E0 - 6)), int(min(GW, max(xs) - E0 + 6)); r0, r1 = int(max(0, N1 - max(ys) - 6)), int(min(GH, N1 - min(ys) + 6))
        if c1 > c0 and r1 > r0:
            sub = poly_mask(ring, GE[r0:r1, c0:c1], GN[r0:r1, c0:c1])
            bld[r0:r1, c0:c1] |= sub
def prox(mask, maxd=60):
    src = gdal.GetDriverByName('MEM').Create('', GW, GH, 1, gdal.GDT_Byte); src.GetRasterBand(1).WriteArray(mask.astype(np.uint8))
    dst = gdal.GetDriverByName('MEM').Create('', GW, GH, 1, gdal.GDT_Float32)
    gdal.ComputeProximity(src.GetRasterBand(1), dst.GetRasterBand(1), ['VALUES=1', 'DISTUNITS=PIXEL', 'MAXDIST=%d' % maxd, 'NODATA=%d' % maxd])
    return dst.GetRasterBand(1).ReadAsArray()
d_road = prox(roads); d_bld = prox(bld)
edge = np.zeros((GH, GW), bool)
for ax in (0, 1):
    for sh in (1, -1):
        edge |= fid != np.roll(fid, sh, ax)
d_edge = prox(edge)                                   # distance to the nearest field edge (any neighbour, road gap, outside)
TYPE = {f['id']: f for f in FV['fields']}
# split 'light' / 'structures' by colour (measured from the screenshot per field)
bimg = gdal.Open(str(HERE.parent / 'References/Wide_2026-10-10/wide_satellite.webp')); Bm = np.stack([bimg.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3)], -1).astype(np.float32)
fbd = gdal.Open(str(HERE / 'fields_v1.tif')); fb = fbd.ReadAsArray(); k = fb.max() + 1; cnt = np.maximum(np.bincount(fb.ravel(), minlength=k), 1)
meanc = np.stack([np.bincount(fb.ravel(), Bm[..., c].ravel(), k) / cnt for c in range(3)], -1)
for f in FV['fields']:
    sat = float(meanc[f['id']].max() - meanc[f['id']].min())
    f['sat'] = round(sat, 1)
    if f['type'] == 'light':
        f['fill'] = 'greenhouse' if sat <= 13 else 'pale_soil'
    elif f['type'] == 'structures':
        f['fill'] = 'greenhouse' if sat <= 15 else 'none'
    else:
        f['fill'] = f['type']


def long_axis_deg(i):
    m = fid == i
    if not m.any():
        return 0.0
    x = GE[m]; y = GN[m]; x = x - x.mean(); y = y - y.mean()
    a, b, c = (x * x).mean(), (y * y).mean(), (x * y).mean()
    return math.degrees(0.5 * math.atan2(2 * c, a - b)) % 180.0


ok_base = ~fence & (d_road >= 4) & (d_bld >= 5)
def lattice(i, row_deg, pitch, step, margin, jitter):
    m = (fid == i) & ok_base & (d_edge >= margin)
    if not m.any():
        return []
    thr = math.radians(row_deg); ux, uy = math.cos(thr), math.sin(thr); vx, vy = -uy, ux
    xs, ys = GE[m], GN[m]
    us = xs * ux + ys * uy; vs = xs * vx + ys * vy
    out = []
    v = math.floor(vs.min() / pitch) * pitch + pitch / 2
    while v <= vs.max():
        u = math.floor(us.min() / step) * step
        while u <= us.max():
            e, n = u * ux + v * vx + rng.uniform(-jitter, jitter), u * uy + v * vy + rng.uniform(-jitter, jitter)
            c, r = int(e - E0), int(N1 - n)
            if 0 <= c < GW and 0 <= r < GH and m[r, c]:
                out.append((round(e, 2), round(n, 2)))
            u += step
        v += pitch
    return out


def scatter(i, per_m2, margin):
    m = (fid == i) & ok_base & (d_edge >= margin)
    nm = int(m.sum() * per_m2)
    if nm == 0:
        return []
    rr, cc = np.nonzero(m); pick = rng.choice(len(rr), min(nm, len(rr)), replace=False)
    return [(round(E0 + cc[j] + rng.uniform(0, 1), 2), round(N1 - rr[j] - rng.uniform(0, 1), 2)) for j in pick]


AVO = ['SM_PazFarm_Avocado_A', 'SM_PazFarm_Avocado_B', 'SM_PazFarm_Avocado_C']
CIT = ['SM_PazFarm_Lemon_A', 'SM_PazFarm_Lemon_B', 'SM_PazFarm_Orange_A', 'SM_PazFarm_Orange_B']
plants = {'units': 'metres east/north of the Paz Farm pin; yaw degrees (Unreal), scale uniform', 'items': []}
def add(kind, mesh, e, n, yaw, sc):
    plants['items'].append([kind, mesh, e, n, round(yaw, 1), round(sc, 3)])
stats = {}
for f in FV['fields']:
    i = f['id']; fill = f['fill']
    rd = f['row_deg_from_east'] if f['row_coherence'] >= 0.15 else long_axis_deg(i)
    f['row_deg_used'] = round(rd, 1)
    n0 = len(plants['items'])
    if fill == 'orchard':
        sp = AVO if rng.uniform() < 0.5 else CIT
        f['species'] = 'avocado' if sp is AVO else 'citrus'
        for e, n in lattice(i, rd, 6.0, 4.5, 3.0, 0.25):
            add('orchard', sp[int(rng.integers(len(sp)))], e, n, -rd + rng.uniform(-180, 180), rng.uniform(0.85, 1.1))
    elif fill == 'rows':
        for e, n in lattice(i, rd, 4.0, 2.5, 1.5, 0.15):
            add('rows', CIT[int(rng.integers(len(CIT)))], e, n, -rd + rng.uniform(-180, 180), rng.uniform(0.45, 0.6))
    elif fill == 'green_crop':
        for e, n in lattice(i, rd, 3.0, 1.6, 2.6, 0.12):
            add('crop', 'GREEN', e, n, rng.uniform(0, 360), rng.uniform(0.75, 1.1))
    elif fill == 'ploughed':
        for e, n in scatter(i, 1 / 400.0, 2.0):
            add('weed', 'WEED', e, n, rng.uniform(0, 360), rng.uniform(0.6, 1.0))
    elif fill in ('bare', 'pale_soil'):
        for e, n in scatter(i, 1 / 120.0, 2.0):
            add('weed', 'WEED', e, n, rng.uniform(0, 360), rng.uniform(0.6, 1.1))
    elif fill == 'greenhouse':
        # tunnels 9 m long x 4 m wide laid end to end along the rows, rows every 4.4 m (0.4 m gutter)
        for e, n in lattice(i, rd, 4.4, 9.0, 3.0, 0.0):
            add('greenhouse', 'SM_PazFarm_Greenhouse_Tunnel_9x4', e, n, -rd, 1.0)
    if fill not in ('natural', 'none'):
        # margin shrubs: sample the field edge band 1-2 m inside
        m = (fid == i) & ok_base & (d_edge >= 1) & (d_edge < 2)
        rr, cc = np.nonzero(m)
        if len(rr):
            pick = rng.choice(len(rr), max(1, int(len(rr) / 12 * 0.5)), replace=False)
            for j in pick:
                add('margin', 'SHRUB', round(E0 + cc[j] + 0.5, 2), round(N1 - rr[j] - 0.5, 2), rng.uniform(0, 360), rng.uniform(0.6, 1.1))
    stats.setdefault(fill, {'fields': 0, 'items': 0}); stats[fill]['fields'] += 1; stats[fill]['items'] += len(plants['items']) - n0
from collections import Counter
plants['counts'] = dict(Counter(it[0] for it in plants['items'])); plants['per_fill'] = stats
(HERE / 'FIELD_PLANTS_V1.json').write_text(json.dumps(plants))

# ---- ground mask v4 (square frame over the screenshot), weights per fill, v3 farm interior kept inside the fence ----
SIZE = math.ceil(max(E1 - E0, N1 - N0) / 64.0) * 64.0; NM = 4096; res = SIZE / NM
me0 = (E0 + E1) / 2 - SIZE / 2; mn1 = (N0 + N1) / 2 + SIZE / 2
fid4 = band0(gdal.Warp('', b_ds(HERE / 'fields_v1.tif', gdal.GDT_Int32), format='MEM', outputBounds=(me0, mn1 - SIZE, me0 + SIZE, mn1), width=NM, height=NM,
                       resampleAlg='near', outputType=gdal.GDT_Int32))
rd4 = band0(gdal.Warp('', b_ds(HERE / 'road_mask.png'), format='MEM', outputBounds=(me0, mn1 - SIZE, me0 + SIZE, mn1), width=NM, height=NM,
                      resampleAlg='bilinear', outputType=gdal.GDT_Float32)) / 255.0
W4 = {'orchard': (0.0, 0.45, 0.0), 'rows': (0.5, 0.2, 0.0), 'green_crop': (0.85, 0.08, 0.0), 'ploughed': (1.0, 0.05, 0.0),
      'bare': (0.15, 0.12, 0.0), 'pale_soil': (0.0, 0.1, 0.35), 'greenhouse': (0.0, 0.0, 0.6)}
lut = np.zeros((fid4.max() + 2, 4), np.float32)
vr = np.random.default_rng(777)
for f in FV['fields']:
    if f['fill'] in W4:
        r_, g_, b_ = W4[f['fill']]
        # each field its own mix (crisp field-to-field variety without satellite blur): tilled +-0.3, grass +-0.12, light +-0.12
        r_ = float(np.clip(r_ + vr.uniform(-0.3, 0.3), 0, 1)); g_ = float(np.clip(g_ + vr.uniform(-0.12, 0.12), 0, 1))
        b_ = float(np.clip(b_ + vr.uniform(-0.12, 0.12), 0, 1)) if f['fill'] in ('bare', 'pale_soil', 'ploughed') else b_
        lut[f['id']] = (r_, g_, b_, 1.0)


def smooth_noise(cell_m, seed):
    r = np.random.default_rng(seed); kk = int(math.ceil(SIZE / cell_m)) + 2
    g = r.uniform(-1, 1, (kk, kk)).astype(np.float32)
    u = (np.arange(NM) + 0.5) * res / cell_m; i0 = np.floor(u).astype(int); fr = (u - i0).astype(np.float32); fr = fr * fr * (3 - 2 * fr)
    rows_ = g[i0] * (1 - fr)[:, None] + g[i0 + 1] * fr[:, None]
    return rows_[:, i0] * (1 - fr)[None, :] + rows_[:, i0 + 1] * fr[None, :]


def box(a, r):
    c = np.pad(a.astype(np.float32), ((r + 1, r), (r + 1, r))).cumsum(0).cumsum(1)
    return (c[2 * r + 1:, 2 * r + 1:] - c[:-2 * r - 1, 2 * r + 1:] - c[2 * r + 1:, :-2 * r - 1] + c[:-2 * r - 1, :-2 * r - 1]) / float((2 * r + 1) ** 2)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


W = lut[np.clip(fid4, 0, len(lut) - 1)]
noise = 0.55 * smooth_noise(1.5, 11) + 0.3 * smooth_noise(5.0, 12) + 0.15 * smooth_noise(16.0, 13)
patch = smoothstep(-0.1, 0.5, 0.55 * smooth_noise(1.5, 31) + 0.3 * smooth_noise(5.0, 32) + 0.15 * smooth_noise(16.0, 33))
cover = smoothstep(0.35, 0.65, box(W[..., 3], max(1, int(1.2 / res))) + 0.18 * noise)
R, G, Bc = W[..., 0], W[..., 1] * patch, W[..., 2]
diff = np.zeros((NM, NM), bool)
for ax in (0, 1):
    for sh in (1, -1):
        diff |= fid4 != np.roll(fid4, sh, ax)
margin = smoothstep(0.02, 0.12, box(diff, max(1, int(2.4 / res))) + 0.05 * noise) * (W[..., 3] > 0)
G = np.maximum(G, margin * (0.75 + 0.25 * patch)); R = R * (1 - margin)
road = smoothstep(0.25, 0.6, box(rd4, 1) + 0.1 * noise)
# dirt-road lines only on farmland: not in the village / forest / water zones (the village has its own street meshes)
zds = gdal.Open(str(Path(REC['output_dir']) / 'ZONES.tif')); zgt = zds.GetGeoTransform(); zz = zds.GetRasterBand(1).ReadAsArray()
xs4_ = me0 + (np.arange(NM) + 0.5) * res; ys4_ = mn1 - (np.arange(NM) + 0.5) * res
lon4 = LON0 + (xs4_[None, :] + pe) / MLON; lat4 = LAT0 + (ys4_[:, None] + pn) / MLAT
zone4 = zz[np.clip(((lat4 - zgt[3]) / zgt[5]).astype(int), 0, zz.shape[0] - 1), np.clip(((lon4 - zgt[0]) / zgt[1]).astype(int), 0, zz.shape[1] - 1)]
road = road * ~np.isin(zone4, (1, 2, 3))
Bc = np.maximum(Bc * (1 - road), road); R = R * (1 - road); G = G * (1 - road); cover = np.maximum(cover, road)
# inside the Paz Farm fence: the v3 weights (sampled from the v3 mask at these positions)
xs4 = me0 + (np.arange(NM) + 0.5) * res; ys4 = mn1 - (np.arange(NM) + 0.5) * res
E4, N4 = np.meshgrid(xs4, ys4)
fence4 = poly_mask(FENCE, E4, N4)
v3 = gdal.Open(G3['texture']); v3a = np.stack([v3.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3, 4)], -1).astype(np.float32) / 255.0
cj = ((E4 - G3['west_edge_m_from_pin']) / G3['metres_per_pixel']).astype(int); ri = ((G3['north_edge_m_from_pin'] - N4) / G3['metres_per_pixel']).astype(int)
okv = fence4 & (cj >= 0) & (cj < v3a.shape[1]) & (ri >= 0) & (ri < v3a.shape[0])
fsoft = box(fence4.astype(np.float32), max(1, int(3 / res)))
v3s = v3a[np.clip(ri, 0, v3a.shape[0] - 1), np.clip(cj, 0, v3a.shape[1] - 1)]
for ch, arr in enumerate((R, G, Bc, cover)):
    arr[:] = arr * (1 - fsoft) + v3s[..., ch] * fsoft
img = (np.dstack([R, G, Bc, cover]).clip(0, 1) * 255 + 0.5).astype(np.uint8)
mem = gdal.GetDriverByName('MEM').Create('', NM, NM, 4, gdal.GDT_Byte)
for i in range(4): mem.GetRasterBand(i + 1).WriteArray(img[..., i])
gdal.GetDriverByName('PNG').CreateCopy(str(OUTDIR / 'T_PazFarm_GroundMask_v4.png'), mem)
g4 = {'texture': str(OUTDIR / 'T_PazFarm_GroundMask_v4.png'), 'size_m': SIZE, 'pixels': NM, 'metres_per_pixel': res,
      'west_edge_m_from_pin': me0, 'north_edge_m_from_pin': mn1, 'weights': {k: v for k, v in W4.items()}, 'inside_fence': 'v3 weights kept'}
(HERE / 'FARM_GROUND_V4.json').write_text(json.dumps(g4, indent=1))
small = img[::4, ::4]
soilc, tilled, grass, dirt = (np.array(c, np.float32) for c in ([176, 132, 98], [128, 92, 66], [170, 140, 82], [196, 172, 136]))
cc_ = soilc[None, None] * np.ones(small.shape[:2] + (1,), np.float32)
for ch, col in ((0, tilled), (1, grass), (2, dirt)):
    w_ = small[..., ch:ch + 1] / 255.0; cc_ = cc_ * (1 - w_) + col[None, None] * w_
a_ = small[..., 3:4] / 255.0; cc_ = cc_ * a_ + 110 * (1 - a_)
pm = gdal.GetDriverByName('MEM').Create('', cc_.shape[1], cc_.shape[0], 3, gdal.GDT_Byte)
for i in range(3): pm.GetRasterBand(i + 1).WriteArray(cc_[..., i].clip(0, 255).astype(np.uint8))
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'fields_ground_preview.png'), pm)

# ---- road 44 polyline (OSM trunk) ----
OSM = next(SRC.glob('acquisitions/*/*/osm/overpass_response.json'))
osm = json.loads(OSM.read_text(encoding='utf-8'))
en = lambda lon, lat: ((lon - LON0) * MLON - pe, (lat - LAT0) * MLAT - pn)
nodes = {e['id']: en(e['lon'], e['lat']) for e in osm['elements'] if e['type'] == 'node'}
r44 = [{'id': e['id'], 'highway': e['tags']['highway'], 'ref': e['tags'].get('ref'), 'name': e['tags'].get('name'), 'lanes': e['tags'].get('lanes'),
        'pts': [[round(nodes[i][0], 2), round(nodes[i][1], 2)] for i in e['nodes'] if i in nodes]}
       for e in osm['elements'] if e['type'] == 'way' and e.get('tags', {}).get('highway') in ('trunk', 'trunk_link', 'primary', 'primary_link')]
(HERE / 'ROAD44.json').write_text(json.dumps({'units': 'metres from the Paz Farm pin', 'width_m': 11.0, 'ways': r44}, indent=1))

# ---- zone-frame clearing mask (1024, T_KY4_Zones orientation): filled fields + fence ----
S = 1024; HALFA = 2016.0
zr, zc = np.mgrid[0:S, 0:S] + 0.5
ZE = zc / S * 2 * HALFA - HALFA - pe; ZN = HALFA - zr / S * 2 * HALFA - pn                 # pin metres at zone texel centres
filled_ids = np.array([0] + [1 if f['fill'] not in ('natural', 'none') else 0 for f in sorted(FV['fields'], key=lambda q: q['id'])])
clear = np.zeros((S, S), bool)
for dx in (-1.3, 0, 1.3):
    for dy in (-1.3, 0, 1.3):
        cj2 = (ZE + dx - E0).astype(int); ri2 = (N1 - (ZN + dy)).astype(int)
        okz = (cj2 >= 0) & (cj2 < GW) & (ri2 >= 0) & (ri2 < GH)
        idv = np.where(okz, fid[np.clip(ri2, 0, GH - 1), np.clip(cj2, 0, GW - 1)], 0)
        clear |= okz & (filled_ids[np.clip(idv, 0, len(filled_ids) - 1)] > 0)
clear |= poly_mask(FENCE, ZE, ZN)
cm = gdal.GetDriverByName('MEM').Create('', S, S, 1, gdal.GDT_Byte); cm.GetRasterBand(1).WriteArray(clear.astype(np.uint8) * 255)
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'fields_clear_zone.png'), cm)
(HERE / 'FIELDS_V1.json').write_text(json.dumps(FV))
print(json.dumps({'counts': plants['counts'], 'per_fill': stats, 'mask_size_m': SIZE, 'mask_res_m': round(res, 3), 'road44_ways': len(r44),
                  'clear_zone_px': int(clear.sum())}))
