"""v2 of the plant list (2026-10-11, Astra FieldCrops_v004 delivered: vine rows, olives, field grass). Plants only;
the ground mask v4, ROAD44.json and the zone clearing mask stay as written by fields_build_v1.py.
Changes: orchard species avocado / citrus / olive (a third each; olives 6.5 x 6 m); young-row fields = Astra vine-row tiles
(3 m tiles end to end, row pitch 2.75 m); weeds = Astra grass clumps (bare 1 per 60 m2, ploughed 1 per 250 m2); margins =
shrubs as before + Astra 2 m grass patches every ~8 m.
Original header of v1 follows.
Step 3 of 'every field from the screenshot' (Aviv 2026-10-10: "Yes, build it"). Offline build data, metres from the pin.
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
rng = np.random.default_rng(20261014)
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
OLV = ['V4:SM_PazFarm_Olive_A', 'V4:SM_PazFarm_Olive_B', 'V4:SM_PazFarm_Olive_C']        # V4: = <clone>/PazFarm/FieldCrops_v004/Meshes
VIN = ['V4:SM_PazFarm_VineRow_3m_A', 'V4:SM_PazFarm_VineRow_3m_B', 'V4:SM_PazFarm_VineRow_3m_C']
GRS = ['V4:SM_PazFarm_GrassClump_' + c for c in 'AABBCCDDEF']                   # mostly dry (A-D), some green (E, F)
PAT = ['V4:SM_PazFarm_GrassPatch_2m_A', 'V4:SM_PazFarm_GrassPatch_2m_B']
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
        pick_ = rng.uniform()
        if pick_ < 1 / 3:
            f['species'] = 'olive'
            for e, n in lattice(i, rd, 6.5, 6.0, 3.0, 0.3):
                add('olive', OLV[int(rng.integers(len(OLV)))], e, n, rng.uniform(0, 360), rng.uniform(0.85, 1.1))
        else:
            sp = AVO if pick_ < 2 / 3 else CIT
            f['species'] = 'avocado' if sp is AVO else 'citrus'
            for e, n in lattice(i, rd, 6.0, 4.5, 3.0, 0.25):
                add('orchard', sp[int(rng.integers(len(sp)))], e, n, -rd + rng.uniform(-180, 180), rng.uniform(0.85, 1.1))
    elif fill == 'rows':
        # Astra vine-row tiles: local +Y = row direction -> Unreal yaw = -rd - 90; tiles start every 3 m along the row
        f['species'] = 'vine'
        for e, n in lattice(i, rd, 2.75, 3.0, 3.0, 0.0):
            add('vine', VIN[int(rng.integers(len(VIN)))], e, n, -rd - 90.0, 1.0)
    elif fill == 'green_crop':
        for e, n in lattice(i, rd, 3.0, 1.6, 2.6, 0.12):
            add('crop', 'GREEN', e, n, rng.uniform(0, 360), rng.uniform(0.75, 1.1))
    elif fill == 'ploughed':
        for e, n in scatter(i, 1 / 250.0, 2.0):
            add('grass', GRS[int(rng.integers(len(GRS)))], e, n, rng.uniform(0, 360), rng.uniform(0.7, 1.15))
    elif fill in ('bare', 'pale_soil'):
        for e, n in scatter(i, 1 / 60.0, 2.0):
            add('grass', GRS[int(rng.integers(len(GRS)))], e, n, rng.uniform(0, 360), rng.uniform(0.7, 1.2))
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
            pick2 = rng.choice(len(rr), max(1, int(len(rr) / 8)), replace=False)
            for j in pick2:
                add('patch', PAT[int(rng.integers(len(PAT)))], round(E0 + cc[j] + 0.5, 2), round(N1 - rr[j] - 0.5, 2), rng.uniform(0, 360), rng.uniform(0.8, 1.2))
    stats.setdefault(fill, {'fields': 0, 'items': 0}); stats[fill]['fields'] += 1; stats[fill]['items'] += len(plants['items']) - n0
from collections import Counter
plants['counts'] = dict(Counter(it[0] for it in plants['items'])); plants['per_fill'] = stats
(HERE / 'FIELD_PLANTS_V2.json').write_text(json.dumps(plants))
print(json.dumps({'counts': plants['counts'], 'per_fill': stats}))

