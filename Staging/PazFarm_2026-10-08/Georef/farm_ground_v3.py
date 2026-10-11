"""Paz Farm real-ground mask v3 + crop positions on the road-to-road parcels (no editor).
Aviv 2026-10-10: no screenshot boundaries at all; "Push all to roads" (parcels_v2.py, PARCELS_V2.json + parcels_v2_labels.tif);
"Yes, lighter rows" (green-field plants at about a third of the first spacing). Ground = weights only, no colours/stripes:
   R tilled soil, G grass / weedy margin, B compacted dirt (farm roads, yard), A farm coverage
Edges: noisy ~1.5 m feather at the outer parcel edge, 2-3 m weedy margins along every parcel edge and road.
Crops (metres from the pin):
   green fields  stand-in low plants in beds at the measured row period: lines 1.3 m apart in a bed of 60% of the
                 period, a plant every 1.1 m (lighter rows); 2.6 m off parcel edges
   orchards      avocado / citrus / young citrus on the SAME global lattice as PLACEMENTS.json (rows continue straight),
                 over the whole parcel; points within 1 m of an existing farm instance are skipped (no doubles)
Outputs: SourceData/.../zones/PazFarm/T_PazFarm_GroundMask_v3.png, Georef/FARM_GROUND_V3.json, CROPS_V3.json,
         PARCEL_CLEAR_V3.json (parcel union for clearing the zone stand-ins), farm_ground_v3_preview.png
Run with the gis env python.
"""
import json, math
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent
OUT = Path(r'C:\Users\USER\Documents\Pipeline Environment\SourceData\KarmeiYosef_31850349_34907601_4km\zones\PazFarm')
L = json.loads((HERE / 'LAYOUT.json').read_text())
PV = json.loads((HERE / 'PARCELS_V2.json').read_text())
PL = json.loads((HERE / 'PLACEMENTS.json').read_text())
names = list(L['plots'])
lt = gdal.Open(PV['labels_tif']); gt = lt.GetGeoTransform(); lab1 = lt.GetRasterBand(1).ReadAsArray(); lt = None
H1, C1 = -gt[0], gt[1]                                   # 1 m grid, x from -H1, y from +H1
rng = np.random.default_rng(20261011)
# ---- mask frame: square around all parcels + drawn roads, 2048 px ----
rr_, cc_ = np.nonzero(lab1 > 0)
e_min, e_max = cc_.min() * C1 - H1, (cc_.max() + 1) * C1 - H1
n_max, n_min = H1 - rr_.min() * C1, H1 - (rr_.max() + 1) * C1
for r in PV['roads_drawn'].values():
    for x, y in r['line_m']:
        e_min, e_max, n_min, n_max = min(e_min, x), max(e_max, x), min(n_min, y), max(n_max, y)
pad = 25.0
SIZE = math.ceil((max(e_max - e_min, n_max - n_min) + 2 * pad) / 64.0) * 64.0
N = 2048; res = SIZE / N
e0 = (e_min + e_max) / 2 - SIZE / 2; n1 = (n_min + n_max) / 2 + SIZE / 2
xs = e0 + (np.arange(N) + 0.5) * res; ys = n1 - (np.arange(N) + 0.5) * res
E, Nn = np.meshgrid(xs, ys)
li = np.clip(((H1 - Nn) / C1).astype(int), 0, lab1.shape[0] - 1); lj = np.clip(((E + H1) / C1).astype(int), 0, lab1.shape[1] - 1)
lab = lab1[li, lj]


def smooth_noise(cell_m, seed):
    r = np.random.default_rng(seed); k = int(math.ceil(SIZE / cell_m)) + 2
    g = r.uniform(-1, 1, (k, k)).astype(np.float32)
    u = (np.arange(N) + 0.5) * res / cell_m; i0 = np.floor(u).astype(int); f = (u - i0).astype(np.float32); f = f * f * (3 - 2 * f)
    rows = g[i0] * (1 - f)[:, None] + g[i0 + 1] * f[:, None]
    return rows[:, i0] * (1 - f)[None, :] + rows[:, i0 + 1] * f[None, :]


def fbm(seed):
    return 0.55 * smooth_noise(1.5, seed) + 0.3 * smooth_noise(5.0, seed + 1) + 0.15 * smooth_noise(16.0, seed + 2)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


def box(m, r):
    c = np.pad(m.astype(np.float32), ((r + 1, r), (r + 1, r))).cumsum(0).cumsum(1)
    return (c[2 * r + 1:, 2 * r + 1:] - c[:-2 * r - 1, 2 * r + 1:] - c[2 * r + 1:, :-2 * r - 1] + c[:-2 * r - 1, :-2 * r - 1]) / float((2 * r + 1) ** 2)


def seg_dist(pts):
    d = np.full((N, N), 1e9, np.float32)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy or 1e-9
        t = np.clip(((E - x0) * dx + (Nn - y0) * dy) / L2, 0, 1)
        d = np.minimum(d, np.hypot(E - (x0 + t * dx), Nn - (y0 + t * dy)))
    return d


KIND = {'yard': (0.0, 0.0, 1.0), 'strawberry_rows': (0.2, 0.12, 0.0), 'bare_soil': (0.6, 0.1, 0.0),
        'orchard_avocado': (0.0, 0.45, 0.0), 'orchard_citrus': (0.0, 0.35, 0.0), 'orchard_citrus_young': (0.45, 0.2, 0.0)}
FIELD = {'field_north_green': 0.85, 'fields_west_green': 0.85, 'field_northeast_big': 1.0, 'field_southwest': 0.4, 'field_southeast_brown': 0.75}
GREEN = ('field_north_green', 'fields_west_green')
n_edge, n_margin, n_patch = fbm(11), fbm(21), fbm(31)
R = np.zeros((N, N), np.float32); G = np.zeros((N, N), np.float32); B = np.zeros((N, N), np.float32)
for i, name in enumerate(names):
    m = lab == i + 1
    if not m.any():
        continue
    if name in FIELD:
        r_, g_, b_ = FIELD[name], 0.08, 0.0
    else:
        r_, g_, b_ = KIND[L['plots'][name]['kind']]
    R[m] = r_; B[m] = b_
    if g_:
        G[m] = (g_ * smoothstep(-0.1, 0.5, n_patch))[m]
inside = (lab > 0).astype(np.float32)
soft = box(inside, max(1, int(1.2 / res)))
cover = smoothstep(0.35, 0.65, soft + 0.18 * n_edge)
# weedy margins along every parcel edge (between parcels, at roads and at the outer edge), noisy width 1.6-3.4 m
diff = np.zeros((N, N), bool)
for ax in (0, 1):
    for sh in (1, -1):
        diff |= lab != np.roll(lab, sh, ax)
mw = box(diff, max(1, int(2.4 / res)))
margin = smoothstep(0.02, 0.12, mw + 0.05 * n_margin) * (lab > 0) * (lab != names.index('yard') + 1)
G = np.maximum(G, margin * (0.75 + 0.25 * n_patch)); R = R * (1 - margin)
# farm roads (traced, continued straight past the old frame as far as the parcels beside them): dirt + dry verge
road_a = np.zeros((N, N), np.float32); verge = np.zeros((N, N), np.float32)
for r in PV['roads_drawn'].values():
    d = seg_dist([tuple(p) for p in r['line_m']]); half = r['width_m'] / 2
    road_a = np.maximum(road_a, 1.0 - smoothstep(half - 0.4, half + 0.4, d + 0.35 * n_edge))
    verge = np.maximum(verge, 1.0 - smoothstep(half + 0.6, half + 1.8, d + 0.6 * n_margin))
G = np.maximum(G * (1 - road_a), (verge - road_a).clip(0, 1) * 0.85)
R = R * (1 - np.maximum(road_a, verge * 0.85)); B = np.maximum(B * (1 - road_a), road_a)
cover = np.maximum(cover, np.maximum(road_a, verge * 0.9))
# narrow leftover strips between parcels and roads (< ~20 m wide) become weedy verge instead of bare satellite ground
rr0 = max(1, int(10.0 / res))
solid = cover > 0.5
closed = box((box(solid, rr0) > 0).astype(np.float32), rr0) > 0.999
gap = closed & ~solid
ga = box(gap.astype(np.float32), max(1, int(1.5 / res)))
ga = np.where(solid, 0.0, ga)
R = R * (1 - ga); G = np.maximum(G, ga * (0.75 + 0.25 * n_patch)); cover = np.maximum(cover, ga)
img = np.dstack([R, G, B, cover]).clip(0, 1)
img8 = (img * 255 + 0.5).astype(np.uint8)
mem = gdal.GetDriverByName('MEM').Create('', N, N, 4, gdal.GDT_Byte)
for k in range(4): mem.GetRasterBand(k + 1).WriteArray(img8[..., k])
gdal.GetDriverByName('PNG').CreateCopy(str(OUT / 'T_PazFarm_GroundMask_v3.png'), mem)
soilc, tilled, grass, dirt = (np.array(c, np.float32) for c in ([176, 132, 98], [128, 92, 66], [170, 140, 82], [196, 172, 136]))
c = soilc[None, None] * np.ones((N, N, 1), np.float32)
for wgt, col in ((R, tilled), (G, grass), (B, dirt)):
    c = c * (1 - wgt[..., None]) + col[None, None] * wgt[..., None]
c = c * cover[..., None] + 110 * (1 - cover[..., None])
small = c[::2, ::2].clip(0, 255).astype(np.uint8)
pm = gdal.GetDriverByName('MEM').Create('', N // 2, N // 2, 3, gdal.GDT_Byte)
for k in range(3): pm.GetRasterBand(k + 1).WriteArray(small[..., k])
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'farm_ground_v3_preview.png'), pm)

# ---------------- crops on the 1 m label grid ----------------
def region(i, margin_m):
    m = lab1 == i + 1
    r = int(math.ceil(margin_m / C1))
    c = np.pad(m.astype(np.int32), ((r + 1, r), (r + 1, r))).cumsum(0).cumsum(1)
    s = c[2 * r + 1:, 2 * r + 1:] - c[:-2 * r - 1, 2 * r + 1:] - c[2 * r + 1:, :-2 * r - 1] + c[:-2 * r - 1, :-2 * r - 1]
    return s == (2 * r + 1) ** 2                       # eroded: every cell within margin_m (square) is in the parcel


def at(m, e, n):
    i_, j_ = int((H1 - n) / C1), int((e + H1) / C1)
    return 0 <= i_ < m.shape[0] and 0 <= j_ < m.shape[1] and bool(m[i_, j_])


existing = np.array([[it['e'], it['n']] for it in PL['items']], np.float64)
grid = {}
for k_, (e, n) in enumerate(existing):
    grid.setdefault((int(e // 4), int(n // 4)), []).append(k_)


def near_existing(e, n, r=1.0):
    for gx in (int(e // 4) - 1, int(e // 4), int(e // 4) + 1):
        for gy in (int(n // 4) - 1, int(n // 4), int(n // 4) + 1):
            for k_ in grid.get((gx, gy), ()):
                if (existing[k_, 0] - e) ** 2 + (existing[k_, 1] - n) ** 2 < r * r:
                    return True
    return False


def lattice_region(m, row_deg, row_pitch, in_row, jitter):
    th = math.radians(row_deg); ux, uy = math.cos(th), math.sin(th); vx, vy = -uy, ux
    rr2, cc2 = np.nonzero(m)
    pe_ = cc2 * C1 - H1 + 0.5; pn_ = H1 - rr2 * C1 - 0.5
    us = pe_ * ux + pn_ * uy; vs = pe_ * vx + pn_ * vy
    out = []
    v = math.floor(vs.min() / row_pitch) * row_pitch + row_pitch / 2            # same global lattice as farm_ground.py
    while v <= vs.max():
        u = math.floor(us.min() / in_row) * in_row
        while u <= us.max():
            e, n = u * ux + v * vx, u * uy + v * vy
            if jitter:
                e += rng.uniform(-jitter, jitter); n += rng.uniform(-jitter, jitter)
            if at(m, e, n):
                out.append((e, n))
            u += in_row
        v += row_pitch
    return out


crops = {'units': 'metres east/north of the Paz Farm pin', 'green_plants': [], 'trees': []}
stats = {}
for name in GREEN:
    i = names.index(name); p = L['plots'][name]; row = p['rows'][0]
    m = region(i, 2.6)
    th = math.radians(row['row_direction_deg_from_east']); ux, uy = math.cos(th), math.sin(th); vx, vy = -uy, ux
    period = row["period_m"]; bed = 0.6 * period; nlines = max(1, int(bed / 1.3))
    rr2, cc2 = np.nonzero(m)
    pe_ = cc2 * C1 - H1 + 0.5; pn_ = H1 - rr2 * C1 - 0.5
    us = pe_ * ux + pn_ * uy; vs = pe_ * vx + pn_ * vy
    v = math.floor(vs.min() / period) * period; cnt = 0
    while v <= vs.max():
        for li_ in range(nlines):
            vl = v + (li_ + 0.5) * (bed / nlines); u = math.floor(us.min() / 1.1) * 1.1
            while u <= us.max():
                uj = u + rng.uniform(-0.1, 0.1); vj = vl + rng.uniform(-0.1, 0.1)
                e, n = uj * ux + vj * vx, uj * uy + vj * vy
                if at(m, e, n):
                    crops['green_plants'].append([round(e, 2), round(n, 2), round(float(rng.uniform(0, 360)), 1), round(float(rng.uniform(0.75, 1.1)), 2)])
                    cnt += 1
                u += 1.1
        v += period
    stats[name] = {'green_plants': cnt, 'lines_per_bed': nlines}
ORCH = {'orchard_south': ('tree_avocado', ['SM_PazFarm_Avocado_A', 'SM_PazFarm_Avocado_B', 'SM_PazFarm_Avocado_C'], 5.5, 2.5, 0.3, (0.85, 1.1)),
        'orchard_northeast': ('tree_citrus', ['SM_PazFarm_Lemon_A', 'SM_PazFarm_Lemon_B', 'SM_PazFarm_Orange_A', 'SM_PazFarm_Orange_B'], 3.9, 2.0, 0.2, (0.85, 1.05)),
        'rows_east_unknown': ('tree_citrus_young', ['SM_PazFarm_Orange_A', 'SM_PazFarm_Orange_B', 'SM_PazFarm_Lemon_B'], 2.6, 1.5, 0.15, (0.5, 0.62))}
for name, (kind, meshes, in_row, margin_m, jit, sc) in ORCH.items():
    i = names.index(name); row = L['plots'][name]['rows'][0]
    pts = lattice_region(region(i, margin_m), row['row_direction_deg_from_east'], row['period_m'], in_row, jit)
    new = [(e, n) for e, n in pts if not near_existing(e, n)]
    for e, n in new:
        crops['trees'].append({'kind': kind, 'mesh': meshes[int(rng.integers(len(meshes)))], 'e': round(e, 2), 'n': round(n, 2),
                               'yaw_deg': round(-row['row_direction_deg_from_east'] + float(rng.uniform(-180, 180)), 1),
                               'scale': round(float(rng.uniform(*sc)), 3)})
    stats[name] = {'lattice_points': len(pts), 'new_trees': len(new), 'skipped_existing': len(pts) - len(new)}
meta = {'texture': str(OUT / 'T_PazFarm_GroundMask_v3.png'), 'size_m': SIZE, 'pixels': N, 'metres_per_pixel': round(res, 4),
        'west_edge_m_from_pin': round(e0, 3), 'north_edge_m_from_pin': round(n1, 3),
        'channels': {'R': 'tilled soil', 'G': 'grass / weedy margin', 'B': 'compacted dirt (farm roads, yard)', 'A': 'farm coverage'},
        'parcels': 'PARCELS_V2.json (road to road)', 'coverage_share_of_square': round(float((cover > 0.5).mean()), 4), 'crops': stats}
(HERE / 'FARM_GROUND_V3.json').write_text(json.dumps(meta, indent=1))
(HERE / 'CROPS_V3.json').write_text(json.dumps(crops))
print(json.dumps(meta))
