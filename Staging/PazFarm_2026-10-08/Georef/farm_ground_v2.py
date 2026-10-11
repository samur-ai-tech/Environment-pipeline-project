"""Paz Farm real-ground mask v2 + crop-row positions (no editor). Aviv 2026-10-10 approved "Real materials per plot":
remove the painted overlay; real ground materials per plot, soft edges, real low crops instead of painted stripes.
Writes a WEIGHT mask only (no colours, no stripes); the area material blends real pack textures with it:
   R = tilled soil, G = grass / weedy margin, B = compacted dirt (roads, yard), A = farm coverage.
   (none of R/G/B = plain farm soil). Material order: soil -> lerp tilled (R) -> lerp grass (G) -> lerp dirt (B).
Same 512 m frame as v1 (FARM_GROUND.json) so Farm_OriginX/Y and Farm_SizeCm stay valid. Edges: noisy feather ~1-2 m;
2-3 m weedy margins inside plot edges; plot / road edges that are only the screenshot frame fade out over ~25 m instead
of a hard cut (the road-to-road extension waits for Aviv's wider screenshot).
Crops: stand-in low plants in beds along the measured row direction/period, green field plots only (brown/bare stay soil).
Outputs: SourceData/.../zones/PazFarm/T_PazFarm_GroundMask.png, Georef/FARM_GROUND_V2.json, CROPS_V2.json, farm_ground_v2_preview.png
Run with the gis env python (GDAL + numpy).
"""
import json, math
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent
L = json.loads((HERE / 'LAYOUT.json').read_text())
G1 = json.loads((HERE / 'FARM_GROUND.json').read_text())
OUT = Path(r'C:\Users\USER\Documents\Pipeline Environment\SourceData\KarmeiYosef_31850349_34907601_4km\zones\PazFarm')
FIT = L['fit']; A_ = complex(*FIT['a']); B_ = complex(*FIT['b'])
to_m = lambda c, r: A_ * complex(c, -r) + B_
SHOT_W, SHOT_H = 1209, 850
SIZE, N = G1['size_m'], G1['pixels']; res = SIZE / N
e0, n1 = G1['west_edge_m_from_pin'], G1['north_edge_m_from_pin']
rng = np.random.default_rng(20261010)
xs = e0 + (np.arange(N) + 0.5) * res; ys = n1 - (np.arange(N) + 0.5) * res
E, Nn = np.meshgrid(xs, ys)


def smooth_noise(cell_m, seed):
    """value noise in [-1, 1] with features of about cell_m metres (bilinear on a random grid)"""
    r = np.random.default_rng(seed)
    k = int(math.ceil(SIZE / cell_m)) + 2
    g = r.uniform(-1, 1, (k, k)).astype(np.float32)
    u = (np.arange(N) + 0.5) * res / cell_m
    i0 = np.floor(u).astype(int); f = (u - i0).astype(np.float32); f = f * f * (3 - 2 * f)
    rows = g[i0][:, None, :] * (1 - f)[:, None, None] + g[i0 + 1][:, None, :] * f[:, None, None]     # (N, 1, k)
    rows = rows[:, 0, :]
    out = rows[:, i0] * (1 - f)[None, :] + rows[:, i0 + 1] * f[None, :]
    return out


def fbm(seed):
    return 0.55 * smooth_noise(1.5, seed) + 0.3 * smooth_noise(5.0, seed + 1) + 0.15 * smooth_noise(16.0, seed + 2)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


def seg_dist(p0, p1):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy or 1e-9
    t = np.clip(((E - x0) * dx + (Nn - y0) * dy) / L2, 0, 1)
    return np.hypot(E - (x0 + t * dx), Nn - (y0 + t * dy))


def inside(poly):
    m = np.zeros((N, N), bool); n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        m ^= ((y1 > Nn) != (y2 > Nn)) & (E < (x2 - x1) * (Nn - y1) / ((y2 - y1) if y2 != y1 else 1e-9) + x1)
    return m


def frame_edge(p, q):
    return (p[0] == q[0] and p[0] in (0, SHOT_W)) or (p[1] == q[1] and p[1] in (0, SHOT_H))


# per-kind layer values: (tilled R, grass-patch strength G, dirt B)
KIND = {'yard': (0.0, 0.0, 1.0), 'strawberry_rows': (0.2, 0.12, 0.0), 'bare_soil': (0.6, 0.1, 0.0),
        'orchard_avocado': (0.0, 0.45, 0.0), 'orchard_citrus': (0.0, 0.35, 0.0), 'orchard_citrus_young': (0.45, 0.2, 0.0)}
FIELD = {'field_north_green': 0.85, 'fields_west_green': 0.85, 'field_northeast_big': 1.0, 'field_southwest': 0.4,
         'field_southeast_brown': 0.75}
GREEN_FIELDS = ('field_north_green', 'fields_west_green')
n_edge, n_margin, n_patch, n_fade = fbm(11), fbm(21), fbm(31), fbm(41)
num = np.zeros((N, N, 3), np.float32); den = np.zeros((N, N), np.float32); cover = np.zeros((N, N), np.float32)
margin = np.zeros((N, N), np.float32)
plots_info = {}
for name, p in L['plots'].items():
    poly_m = p['polygon_m']; poly_px = p['polygon_px']; n = len(poly_m)
    ins = inside(poly_m)
    d_all = np.full((N, N), 1e9, np.float32); d_real = np.full((N, N), 1e9, np.float32); d_frame = np.full((N, N), 1e9, np.float32)
    frames = 0
    for i in range(n):
        d = seg_dist(poly_m[i], poly_m[(i + 1) % n]).astype(np.float32)
        d_all = np.minimum(d_all, d)
        if frame_edge(poly_px[i], poly_px[(i + 1) % n]):
            d_frame = np.minimum(d_frame, d); frames += 1
        else:
            d_real = np.minimum(d_real, d)
    sd = np.where(ins, d_all, -d_all)
    a = smoothstep(-1.0, 1.0, sd + 1.3 * n_edge)                       # noisy feathered plot edge
    fade = smoothstep(0.0, 25.0, np.where(ins, d_frame, 0.0) + 5.0 * n_fade)
    a = a * np.where(d_frame < 1e8, fade, 1.0)                         # frame-only edges fade out over ~25 m
    if name in FIELD:
        R, Gp, B = FIELD[name], 0.08, 0.0
    else:
        R, Gp, B = KIND[p['kind']]
    patches = Gp * smoothstep(-0.1, 0.5, n_patch) if Gp else np.zeros((N, N), np.float32)
    if p['kind'] != 'yard':                                            # weedy margin inside real (non-frame) edges
        w = 2.4 + 1.1 * n_margin
        m = (1.0 - smoothstep(w - 0.7, w + 0.7, np.where(ins, d_real, 99.0))) * (d_real < 1e8)
        margin = np.maximum(margin, m * a)
    num[..., 0] += a * R; num[..., 1] += a * patches; num[..., 2] += a * B
    den += a; cover = np.maximum(cover, a)
    plots_info[name] = {'kind': p['kind'], 'tilled': R, 'grass_patches': Gp, 'dirt': B, 'frame_edges': frames}
w = np.maximum(den, 1e-6)
R = num[..., 0] / w; Gc = num[..., 1] / w; Bc = num[..., 2] / w
Gc = np.maximum(Gc, margin); R = R * (1 - margin)
# the yard wins where traced polygons overlap it
ya = smoothstep(-1.0, 1.0, np.where(inside(L['plots']['yard']['polygon_m']), 1, -1) * np.min(
    [seg_dist(q0, q1) for q0, q1 in zip(L['plots']['yard']['polygon_m'], L['plots']['yard']['polygon_m'][1:] + L['plots']['yard']['polygon_m'][:1])], 0) + 1.3 * n_edge)
R = R * (1 - ya); Gc = Gc * (1 - ya); Bc = np.maximum(Bc, ya)
# roads: compacted dirt with a narrow dry-grass verge; frame ends fade like the plots
road_a = np.zeros((N, N), np.float32); verge = np.zeros((N, N), np.float32)
frame_poly = [to_m(0, 0), to_m(SHOT_W, 0), to_m(SHOT_W, SHOT_H), to_m(0, SHOT_H)]
d_frame_box = np.full((N, N), 1e9, np.float32)
for i in range(4):
    z0, z1 = frame_poly[i], frame_poly[(i + 1) % 4]
    d_frame_box = np.minimum(d_frame_box, seg_dist((z0.real, z0.imag), (z1.real, z1.imag)))
in_frame = inside([(z.real, z.imag) for z in frame_poly])
road_fade = smoothstep(0.0, 25.0, np.where(in_frame, d_frame_box, 0.0) + 5.0 * n_fade)
for name, r in L['roads'].items():
    d = np.full((N, N), 1e9, np.float32)
    for p0, p1 in zip(r['line_m'], r['line_m'][1:]):
        d = np.minimum(d, seg_dist(p0, p1))
    half = r['width_m'] / 2
    ra = 1.0 - smoothstep(half - 0.4, half + 0.4, d + 0.35 * n_edge)
    va = 1.0 - smoothstep(half + 0.6, half + 1.8, d + 0.6 * n_margin)
    road_a = np.maximum(road_a, ra * road_fade); verge = np.maximum(verge, va * road_fade)
Gc = np.maximum(Gc * (1 - road_a), (verge - road_a).clip(0, 1) * 0.85)
R = R * (1 - np.maximum(road_a, verge * 0.85))
Bc = np.maximum(Bc, road_a)
cover = np.maximum(cover, np.maximum(road_a, verge * 0.9))
# close the narrow uncovered strips between traced plots and roads (< ~20 m) with weedy verge, noisy edge
def box(m, r):
    c = np.pad(m.astype(np.float32), ((r + 1, r), (r + 1, r))).cumsum(0).cumsum(1)
    return c[2 * r + 1:, 2 * r + 1:] - c[:-2 * r - 1, 2 * r + 1:] - c[2 * r + 1:, :-2 * r - 1] + c[:-2 * r - 1, :-2 * r - 1]
rr = int(10.0 / res)
solid = cover > 0.5
closed = box(box(solid, rr) > 0, rr) >= (2 * rr + 1) ** 2 - 0.5
gap = closed & ~solid & (smooth_noise(3.0, 51) > -0.85)
ga = np.where(gap, 1.0, 0.0).astype(np.float32)
ga = box(ga, 3) / 49.0                                                   # ~1.75 m soft edge
ga = np.where(solid, 0.0, ga) * road_fade
mix = 0.75 + 0.25 * n_patch
R = np.where(ga > 0, R * (1 - ga), R); Gc = np.maximum(Gc, ga * mix); cover = np.maximum(cover, ga)
img = np.dstack([R, Gc, Bc, cover]).clip(0, 1)
img8 = (img * 255 + 0.5).astype(np.uint8)
mem = gdal.GetDriverByName('MEM').Create('', N, N, 4, gdal.GDT_Byte)
for i in range(4): mem.GetRasterBand(i + 1).WriteArray(img8[..., i])
gdal.GetDriverByName('PNG').CreateCopy(str(OUT / 'T_PazFarm_GroundMask.png'), mem)
# preview: soil brown, tilled dark brown, grass straw, dirt beige, over grey (outside = satellite ground)
soil, tilled, grass, dirt = (np.array(c, np.float32) for c in ([176, 132, 98], [128, 92, 66], [170, 140, 82], [196, 172, 136]))
c = soil[None, None] * np.ones((N, N, 1), np.float32)
for wgt, col in ((R, tilled), (Gc, grass), (Bc, dirt)):
    c = c * (1 - wgt[..., None]) + col[None, None] * wgt[..., None]
c = c * cover[..., None] + 110 * (1 - cover[..., None])
small = c[::2, ::2].clip(0, 255).astype(np.uint8)
pm = gdal.GetDriverByName('MEM').Create('', N // 2, N // 2, 3, gdal.GDT_Byte)
for i in range(3): pm.GetRasterBand(i + 1).WriteArray(small[..., i])
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'farm_ground_v2_preview.png'), pm)


# ---------------- crop rows (green field plots only) ----------------
def in_poly(e, n, poly):
    ins_ = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > n) != (y2 > n) and e < (x2 - x1) * (n - y1) / (y2 - y1) + x1:
            ins_ = not ins_
    return ins_


def edge_dist(e, n, poly, skip_frame_px=None):
    best = 1e9
    for i in range(len(poly)):
        if skip_frame_px is not None and frame_edge(skip_frame_px[i], skip_frame_px[(i + 1) % len(poly)]):
            continue
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
        dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy or 1e-9
        t = min(1, max(0, ((e - x0) * dx + (n - y0) * dy) / L2))
        best = min(best, math.hypot(e - (x0 + t * dx), n - (y0 + t * dy)))
    return best


def road_dist(e, n):
    best = 1e9
    for r in L['roads'].values():
        for (x0, y0), (x1, y1) in zip(r['line_m'], r['line_m'][1:]):
            dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy or 1e-9
            t = min(1, max(0, ((e - x0) * dx + (n - y0) * dy) / L2))
            best = min(best, math.hypot(e - (x0 + t * dx), n - (y0 + t * dy)) - r['width_m'] / 2)
    return best


def frame_fade_ok(e, n):
    # crops thin out with the same ~25 m fade as the ground near screenshot-frame edges
    d = min(abs(complex(e, n) - z) for z in frame_poly)
    for i in range(4):
        z0, z1 = frame_poly[i], frame_poly[(i + 1) % 4]
        dz = z1 - z0; t = max(0, min(1, ((complex(e, n) - z0) * dz.conjugate()).real / abs(dz) ** 2))
        d = min(d, abs(complex(e, n) - (z0 + t * dz)))
    return rng.uniform() < min(1.0, d / 25.0)


crops = {'units': 'metres east/north of the Paz Farm pin', 'method': 'beds at the measured row period; 0.9 m plant lines inside a bed '
         'of 60% of the period; plants every 0.45 m with 0.08 m jitter; 2.6 m off real plot edges, 1.5 m off roads; thinned near the frame', 'items': []}
for name in GREEN_FIELDS:
    p = L['plots'][name]; row = p['rows'][0]; poly = p['polygon_m']
    th = math.radians(row['row_direction_deg_from_east']); ux, uy = math.cos(th), math.sin(th); vx, vy = -uy, ux
    period = row['period_m']; bed = 0.6 * period; nlines = max(1, int(bed / 0.9))
    us = [q[0] * ux + q[1] * uy for q in poly]; vs = [q[0] * vx + q[1] * vy for q in poly]
    v = math.floor(min(vs) / period) * period
    count = 0
    while v <= max(vs):
        for li in range(nlines):
            vl = v + (li + 0.5) * (bed / nlines)
            u = min(us)
            while u <= max(us):
                uj = u + rng.uniform(-0.08, 0.08); vj = vl + rng.uniform(-0.08, 0.08)
                e, n = uj * ux + vj * vx, uj * uy + vj * vy
                if in_poly(e, n, poly) and edge_dist(e, n, poly, p['polygon_px']) >= 2.6 and road_dist(e, n) >= 1.5 and frame_fade_ok(e, n):
                    crops['items'].append([round(e, 2), round(n, 2), round(float(rng.uniform(0, 360)), 1), round(float(rng.uniform(0.75, 1.1)), 2)])
                    count += 1
                u += 0.45
        v += period
    plots_info[name]['crop_plants'] = count
meta = {'texture': str(OUT / 'T_PazFarm_GroundMask.png'), 'size_m': SIZE, 'pixels': N, 'metres_per_pixel': res,
        'west_edge_m_from_pin': e0, 'north_edge_m_from_pin': n1, 'channels': {'R': 'tilled soil', 'G': 'grass / weedy margin',
        'B': 'compacted dirt (roads, yard)', 'A': 'farm coverage'}, 'plots': plots_info,
        'coverage_share_of_square': round(float((cover > 0.5).mean()), 4), 'crop_plants': len(crops['items']),
        'method': 'weights only (no screenshot pixels, no painted stripes); noisy feathered edges; margins; frame-edge fades'}
(HERE / 'FARM_GROUND_V2.json').write_text(json.dumps(meta, indent=1))
(HERE / 'CROPS_V2.json').write_text(json.dumps(crops))
print(json.dumps({k: v for k, v in meta.items() if k != 'plots'}), json.dumps(plots_info))
