"""Paz Farm ground layer and model positions from LAYOUT.json (no editor). Aviv: "rebuild each plot, reversible".
Ground layer: our own drawing, not screenshot pixels. Each plot = smooth row stripes at its measured direction and
spacing, coloured between its measured dark and light colours, with a little noise; dirt roads in their measured colour;
1 m feathered edges; alpha 0 outside the traced plots/roads. 2048 x 2048 RGBA, 0.25 m per pixel, 512 m square centred on
the screenshot, north up.  -> SourceData/.../zones/PazFarm/T_PazFarm_Ground.png and FARM_GROUND.json
Positions (metres east/north of the pin) -> PLACEMENTS.json:
  strawberry beds along each measured row (4 m tiles), trees on row lattices, fence along the farm perimeter, gate, barn.
"""
import json, math
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent
L = json.loads((HERE / 'LAYOUT.json').read_text())
FIT = L['fit']; A = complex(*FIT['a']); B = complex(*FIT['b'])
to_m = lambda c, r: A * complex(c, -r) + B
OUT = Path(r'C:\Users\USER\Documents\Pipeline Environment\SourceData\KarmeiYosef_31850349_34907601_4km\zones\PazFarm')
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20261008)
# screenshot centre in metres, texture square
shot_w, shot_h = 1209, 850
centre = to_m(shot_w / 2, shot_h / 2)
SIZE, N = 512.0, 2048
res = SIZE / N
e0, n1 = centre.real - SIZE / 2, centre.imag + SIZE / 2          # west edge, north edge (metres from pin)
ys, xs = np.mgrid[0:N, 0:N]
E = e0 + (xs + 0.5) * res; Nn = n1 - (ys + 0.5) * res


def poly_mask(poly_m):
    m = np.zeros((N, N), bool); n = len(poly_m)
    for i in range(n):
        (x1, y1), (x2, y2) = poly_m[i], poly_m[(i + 1) % n]
        m ^= ((y1 > Nn) != (y2 > Nn)) & (E < (x2 - x1) * (Nn - y1) / ((y2 - y1) if y2 != y1 else 1e-9) + x1)
    return m


def feather(mask, metres=1.0):
    k = max(1, int(metres / res))
    f = mask.astype(np.float32)
    for axis in (0, 1):
        acc = np.zeros_like(f)
        for d in range(-k, k + 1):
            acc += np.roll(f, d, axis)
        f = acc / (2 * k + 1)
    return f


rgb = np.zeros((N, N, 3), np.float32); alpha = np.zeros((N, N), np.float32)
noise = rng.normal(0, 1, (N // 8, N // 8)).astype(np.float32)
noise = np.kron(noise, np.ones((8, 8), np.float32))
for name, p in L['plots'].items():
    mk = poly_mask(p['polygon_m'])
    if not mk.any():
        continue
    dark, light = np.array(p['colour_dark'], np.float32), np.array(p['colour_light'], np.float32)
    row = p['rows'][0]
    if p['kind'] in ('yard',):
        col = np.broadcast_to(np.array(p['colour_mean'], np.float32), (N, N, 3)).copy()
    else:
        th = math.radians(row['row_direction_deg_from_east'])
        dist = -E * math.sin(th) + Nn * math.cos(th)            # distance across the rows
        s = 0.5 + 0.5 * np.cos(2 * math.pi * dist / row['period_m'])
        s = s ** 1.6                                              # narrower dark row lines
        col = light[None, None, :] + (dark - light)[None, None, :] * s[..., None]
    col *= (1.0 + 0.04 * noise)[..., None]
    a = feather(mk, 1.0)
    rgb = rgb * (1 - a[..., None]) + col * a[..., None]; alpha = np.maximum(alpha, a)
# roads: colour measured from the screenshot along each road
shot = gdal.Open(L['screenshot']); simg = np.stack([shot.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3)], -1).astype(np.float32); shot = None
for name, r in L['roads'].items():
    samples = []
    for (c0, r0), (c1, r1) in zip(r['line_px'], r['line_px'][1:]):
        for t in np.linspace(0, 1, 40):
            c, rr = int(c0 + (c1 - c0) * t), int(r0 + (r1 - r0) * t)
            if 0 <= c < shot_w and 0 <= rr < shot_h:
                samples.append(simg[rr, c])
    road_col = np.median(np.array(samples), 0) if samples else np.array([180, 150, 120], np.float32)
    r['colour'] = [int(v) for v in road_col]
    mk = np.zeros((N, N), bool)
    for (x0, y0), (x1, y1) in zip(r['line_m'], r['line_m'][1:]):
        dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy
        t = np.clip(((E - x0) * dx + (Nn - y0) * dy) / L2, 0, 1)
        d = np.hypot(E - (x0 + t * dx), Nn - (y0 + t * dy))
        mk |= d <= r['width_m'] / 2
    a = feather(mk, 0.75)
    col = road_col[None, None, :] * (1.0 + 0.05 * noise)[..., None]
    rgb = rgb * (1 - a[..., None]) + col * a[..., None]; alpha = np.maximum(alpha, a)
img = np.dstack([np.clip(rgb, 0, 255), np.clip(alpha * 255, 0, 255)]).astype(np.uint8)
mem = gdal.GetDriverByName('MEM').Create('', N, N, 4, gdal.GDT_Byte)
for i in range(4): mem.GetRasterBand(i + 1).WriteArray(img[..., i])
gdal.GetDriverByName('PNG').CreateCopy(str(OUT / 'T_PazFarm_Ground.png'), mem)
prev = gdal.GetDriverByName('MEM').Create('', N // 2, N // 2, 3, gdal.GDT_Byte)
small = img[::2, ::2]
bg = np.full_like(small[..., :3], 90)
mix = (small[..., :3] * (small[..., 3:] / 255.0) + bg * (1 - small[..., 3:] / 255.0)).astype(np.uint8)
for i in range(3): prev.GetRasterBand(i + 1).WriteArray(mix[..., i])
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'farm_ground_preview.png'), prev)

# ---------------- placements (metres east/north of the pin) ----------------
def in_poly(e, n, poly):
    inside = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > n) != (y2 > n) and e < (x2 - x1) * (n - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def edge_dist(e, n, poly):
    best = 1e9
    for i in range(len(poly)):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
        dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy or 1e-9
        t = min(1, max(0, ((e - x0) * dx + (n - y0) * dy) / L2))
        best = min(best, math.hypot(e - (x0 + t * dx), n - (y0 + t * dy)))
    return best


def lattice(poly, row_deg, row_pitch, in_row, margin, jitter=0.0):
    th = math.radians(row_deg); ux, uy = math.cos(th), math.sin(th); vx, vy = -uy, ux   # u along rows, v across
    us = [p[0] * ux + p[1] * uy for p in poly]; vs = [p[0] * vx + p[1] * vy for p in poly]
    out = []
    v = math.floor(min(vs) / row_pitch) * row_pitch + row_pitch / 2
    while v <= max(vs):
        u = math.floor(min(us) / in_row) * in_row
        while u <= max(us):
            e, n = u * ux + v * vx, u * uy + v * vy
            if jitter:
                e += rng.uniform(-jitter, jitter); n += rng.uniform(-jitter, jitter)
            if in_poly(e, n, poly) and edge_dist(e, n, poly) >= margin:
                out.append([round(e, 2), round(n, 2)])
            u += in_row
        v += row_pitch
    return out


P = L['plots']; place = {'units': 'metres east/north of the Paz Farm pin; row_deg = row direction from east, counter-clockwise',
                         'items': []}
def add(kind, meshes, pts, row_deg, scale, yaw_jitter=0.0):
    for i, (e, n) in enumerate(pts):
        place['items'].append({'kind': kind, 'mesh': meshes[int(rng.integers(len(meshes)))], 'e': e, 'n': n,
                               'row_deg': row_deg + (rng.uniform(-yaw_jitter, yaw_jitter) if yaw_jitter else 0.0),
                               'scale': round(float(rng.uniform(*scale)), 3)})
for name in ('strawberry_west', 'strawberry_triangle'):
    p = P[name]; r = p['rows'][0]
    add('strawberry_bed', ['SM_PazFarm_StrawberryBed_4m'], lattice(p['polygon_m'], r['row_direction_deg_from_east'], r['period_m'], 4.0, 1.5),
        r['row_direction_deg_from_east'], (1.0, 1.0))
p = P['orchard_south']; r = p['rows'][0]
add('tree_avocado', ['SM_PazFarm_Avocado_A', 'SM_PazFarm_Avocado_B', 'SM_PazFarm_Avocado_C'],
    lattice(p['polygon_m'], r['row_direction_deg_from_east'], r['period_m'], 5.5, 2.5, 0.3), r['row_direction_deg_from_east'], (0.85, 1.1), 180)
p = P['orchard_northeast']; r = p['rows'][0]
add('tree_citrus', ['SM_PazFarm_Lemon_A', 'SM_PazFarm_Lemon_B', 'SM_PazFarm_Orange_A', 'SM_PazFarm_Orange_B'],
    lattice(p['polygon_m'], r['row_direction_deg_from_east'], r['period_m'], 3.9, 2.0, 0.2), r['row_direction_deg_from_east'], (0.85, 1.05), 180)
p = P['rows_east_unknown']; r = p['rows'][0]
add('tree_citrus_young', ['SM_PazFarm_Orange_A', 'SM_PazFarm_Orange_B', 'SM_PazFarm_Lemon_B'],
    lattice(p['polygon_m'], r['row_direction_deg_from_east'], r['period_m'], 2.6, 1.5, 0.15), r['row_direction_deg_from_east'], (0.5, 0.62), 180)
# barn: footprint rectangle on the screenshot (col 432..505, row 160..218)
c = to_m(468.5, 189); w_m = 73 * FIT['scale_m_per_px']; d_m = 58 * FIT['scale_m_per_px']
place['barn'] = {'mesh': 'SM_PazFarm_Barn', 'e': round(c.real, 2), 'n': round(c.imag, 2), 'footprint_ew_m': round(w_m, 2),
                 'footprint_ns_m': round(d_m, 2), 'rotation_deg': round(FIT['rotation_deg'], 2), 'door_facing': 'south (towards the farm road)'}
# fence: farm perimeter (screenshot px), gate gap where the farm road leaves the yard
fence_px = [(366, 705), (366, 88), (414, 88), (430, 100), (552, 105), (560, 240), (643, 362), (846, 690), (846, 705), (366, 705)]
fence_m = [to_m(cc, rr) for cc, rr in fence_px]
gate_c = to_m(557, 205)
segs = []
for z0, z1 in zip(fence_m, fence_m[1:]):
    L_ = abs(z1 - z0); d = (z1 - z0) / L_; k = 0.0
    while k + 3.0 <= L_ + 0.01:
        a0 = z0 + d * k
        mid = a0 + d * 1.5
        if abs(mid - gate_c) > 3.5:
            segs.append({'e': round(a0.real, 2), 'n': round(a0.imag, 2), 'dir_deg': round(math.degrees(math.atan2(d.imag, d.real)), 2)})
        k += 3.0
place['fence_segments'] = segs
gz0, gz1 = to_m(560, 240), to_m(552, 105); gd = (gz1 - gz0) / abs(gz1 - gz0)
place['gate'] = {'mesh': 'SM_PazFarm_Gate_Double_6m', 'e': round((gate_c - gd * 3).real, 2), 'n': round((gate_c - gd * 3).imag, 2),
                 'dir_deg': round(math.degrees(math.atan2(gd.imag, gd.real)), 2)}
place['corner_posts'] = [{'e': round(z.real, 2), 'n': round(z.imag, 2)} for z in fence_m[:-1]]
from collections import Counter
cnt = Counter(i['kind'] for i in place['items'])
ground = {'texture': str(OUT / 'T_PazFarm_Ground.png'), 'size_m': SIZE, 'pixels': N, 'metres_per_pixel': res,
          'west_edge_m_from_pin': round(e0, 3), 'north_edge_m_from_pin': round(n1, 3), 'road_colours': {k: v['colour'] for k, v in L['roads'].items()},
          'method': 'procedural stripes from measured colours/row spacing per traced plot; no screenshot pixels copied'}
(HERE / 'FARM_GROUND.json').write_text(json.dumps(ground, indent=1))
(HERE / 'PLACEMENTS.json').write_text(json.dumps(place, indent=1))
print(json.dumps({'ground': ground['texture'], 'items': cnt, 'fence_segments': len(segs), 'barn': place['barn'], 'gate': place['gate']}))
