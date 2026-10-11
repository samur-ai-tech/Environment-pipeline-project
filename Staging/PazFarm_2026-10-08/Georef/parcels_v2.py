"""Paz Farm parcels v2 (no editor). Aviv 2026-10-10: the plots must NOT follow the screenshot boundaries at all; each plot
continues through its whole parcel, closed by the dirt roads in our map ("Dirt roads in our map (map data + satellite)").
Method: every plot edge that is only the screenshot frame is pushed outward along the plot's own side lines until it meets
  a road / track (every OSM highway + the traced farm roads; their straight continuations past the frame were removed at
  Aviv's request, EXTEND_TRACED_ROADS False), a building, the
  village, water or forest, or another plot's extension (nearest original plot wins).
  Aviv 2026-10-10 (parcel preview): "Push all to roads" -> satellite field edges are NOT used (USE_SAT False); with
  USE_SAT True a ray would also stop where Sentinel-2 leaves the plot's own signature for 10 m (preview 1, not chosen).
  Rays every 4 m along the edge; road stops follow the road (median of 5 neighbouring rays).
  MAX_EXT caps a push where neither is found (reported, never hidden). Plots with two frame edges also fill their corner.
  No fade anywhere. A first 2-D colour region-growing try leaked across neighbouring fields (blobs) and was dropped.
Outputs: PARCELS_V2.json (extended polygons in metres from the pin + stop reasons), parcels_v2_preview.png (over Sentinel)
Run with the gis env python.
"""
import json, math
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent
TASK4 = HERE.parents[1] / 'NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
SRC = Path(r'C:\Users\USER\Documents\Pipeline Environment\SourceData\KarmeiYosef_31850349_34907601_4km')
ZD = SRC / 'zones' / '20261008T131311Z'
L = json.loads((HERE / 'LAYOUT.json').read_text())
CTX = json.loads((HERE / 'PARCELS_CONTEXT.json').read_text())
REC = json.loads((TASK4 / 'Zones/DATA_RECEIPT.json').read_text())
FOOT = json.loads((TASK4 / 'WPTrial/FOOTPRINTS.json').read_text())['footprints_ue_cm']
LAT0, LON0 = 31.850349, 34.907601
MLAT, MLON = REC['grid']['local_frame']['Mlat_m_per_deg'], REC['grid']['local_frame']['Mlon_m_per_deg']
pe, pn = json.loads((HERE / 'roads.json').read_text())['pin_local_m_from_area_centre']
FIT = L['fit']; A_ = complex(*FIT['a']); B_ = complex(*FIT['b'])
to_m = lambda c, r: A_ * complex(c, -r) + B_
SHOT_W, SHOT_H = 1209, 850
HALF, CELL = 1000.0, 1.0
USE_SAT = False
EXTEND_TRACED_ROADS = False     # Aviv 2026-10-10: the straight continuations were 'way off' (OSM is partial there) -> removed
N = int(2 * HALF / CELL)
MAX_EXT, RAY_STEP, MARCH = 900.0, 4.0, 2.0
T_MIN, K, RUN = 1.6, 2.5, 5                      # satellite stop: distance > max(T_MIN, K*spread) for RUN samples (10 m)
xs = -HALF + (np.arange(N) + 0.5) * CELL; ys = HALF - (np.arange(N) + 0.5) * CELL
E, Nn = np.meshgrid(xs, ys)

# ---- Sentinel-2 features (bilinear onto the 1 m grid) ----
lon = LON0 + (E + pe) / MLON; lat = LAT0 + (Nn + pn) / MLAT
feats = []
for f in ('S2_recent_2026-09-21.tif', 'S2_spring_2026-04-04.tif'):
    ds = gdal.Open(str(ZD / f)); gt = ds.GetGeoTransform()
    bands = [ds.GetRasterBand(i + 1).ReadAsArray().astype(np.float32) / 10000.0 for i in range(4)]
    c = (lon - gt[0]) / gt[1] - 0.5; r = (lat - gt[3]) / gt[5] - 0.5
    c0 = np.clip(np.floor(c).astype(int), 0, ds.RasterXSize - 2); r0 = np.clip(np.floor(r).astype(int), 0, ds.RasterYSize - 2)
    fc = np.clip(c - c0, 0, 1); fr = np.clip(r - r0, 0, 1)
    smp = [b[r0, c0] * (1 - fc) * (1 - fr) + b[r0, c0 + 1] * fc * (1 - fr) + b[r0 + 1, c0] * (1 - fc) * fr + b[r0 + 1, c0 + 1] * fc * fr for b in bands]
    feats += smp + [(smp[3] - smp[0]) / np.maximum(smp[3] + smp[0], 1e-4)]
    ds = None
F = np.stack(feats, -1)
F = (F - F.reshape(-1, F.shape[-1]).mean(0)) / (F.reshape(-1, F.shape[-1]).std(0) + 1e-6)
F[..., 4] *= 1.5; F[..., 9] *= 1.5
zd = gdal.Open(str(ZD / 'ZONES.tif')); gt = zd.GetGeoTransform(); z = zd.GetRasterBand(1).ReadAsArray()
zone = z[np.clip(((lat - gt[3]) / gt[5]).astype(int), 0, zd.RasterYSize - 1), np.clip(((lon - gt[0]) / gt[1]).astype(int), 0, zd.RasterXSize - 1)]
barrier = np.isin(zone, (1, 2, 3))
reason_map = np.where(barrier, 2, 0).astype(np.int8)      # 1 road, 2 zone (village/water/forest), 3 building


def burn_line(pts, half_w, code):
    rad = half_w + CELL * 0.75
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        Lg = math.hypot(x1 - x0, y1 - y0)
        if Lg < 1e-6:
            continue
        lo_c = max(0, int((min(x0, x1) - rad + HALF) / CELL) - 1); hi_c = min(N, int((max(x0, x1) + rad + HALF) / CELL) + 2)
        lo_r = max(0, int((HALF - max(y0, y1) - rad) / CELL) - 1); hi_r = min(N, int((HALF - min(y0, y1) + rad) / CELL) + 2)
        if lo_c >= hi_c or lo_r >= hi_r:
            continue
        se, sn = E[lo_r:hi_r, lo_c:hi_c], Nn[lo_r:hi_r, lo_c:hi_c]
        t = np.clip(((se - x0) * (x1 - x0) + (sn - y0) * (y1 - y0)) / (Lg * Lg), 0, 1)
        hit = np.hypot(se - (x0 + t * (x1 - x0)), sn - (y0 + t * (y1 - y0))) <= rad
        barrier[lo_r:hi_r, lo_c:hi_c] |= hit
        sub = reason_map[lo_r:hi_r, lo_c:hi_c]; sub[hit & (sub == 0)] = code


def poly_mask(poly):
    m = np.zeros((N, N), bool); n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        m ^= ((y1 > Nn) != (y2 > Nn)) & (E < (x2 - x1) * (Nn - y1) / ((y2 - y1) if y2 != y1 else 1e-9) + x1)
    return m


def frame_edge(p, q):
    return (p[0] == q[0] and p[0] in (0, SHOT_W)) or (p[1] == q[1] and p[1] in (0, SHOT_H))


HW = {'track': 2.0, 'path': 1.0, 'footway': 1.0, 'service': 3.0, 'residential': 3.5, 'trunk': 9.0}
for w in CTX['osm_ways']:
    burn_line(w['pts'], HW.get(w['highway'], 3.0), 1)
for poly in FOOT.values():
    ring = [(X / 100.0 - pe, -Y / 100.0 - pn) for X, Y in poly]
    if min(math.hypot(a, b) for a, b in ring) < HALF:
        burn_line(ring + ring[:1], 3.0, 3)
        m = poly_mask(ring); barrier |= m; reason_map[m & (reason_map == 0)] = 3
# traced farm roads continue straight past the frame (they are real dirt roads) until they meet another barrier
frame_px = [(0, 0), (SHOT_W, 0), (SHOT_W, SHOT_H), (0, SHOT_H)]
frame_m = [to_m(*p) for p in frame_px]
roads_ext = {}
road_ends = []
for name, r in L['roads'].items():
    pts = [tuple(p) for p in r['line_m']]
    for end in (0, -1):
        cpx = r['line_px'][end]
        if EXTEND_TRACED_ROADS and (cpx[0] in (0, SHOT_W) or cpx[1] in (0, SHOT_H)):
            a, b = (pts[1], pts[0]) if end == 0 else (pts[-2], pts[-1])
            d = complex(b[0] - a[0], b[1] - a[1]); d /= abs(d)
            s = 0.0
            while s < MAX_EXT:
                s += MARCH
                q = complex(*b) + d * s
                rr, cc = int((HALF - q.imag) / CELL), int((q.real + HALF) / CELL)
                if not (0 <= rr < N and 0 <= cc < N) or (barrier[rr, cc] and s > 6):
                    break
            q = complex(*b) + d * s
            pts = ([(q.real, q.imag)] + pts) if end == 0 else (pts + [(q.real, q.imag)])
            road_ends.append({'road': name, 'end': end, 'frame_point': b, 'dir': (d.real, d.imag), 'barrier_len_m': s})
    roads_ext[name] = {'line_m': [[round(x, 2), round(y, 2)] for x, y in pts], 'width_m': r['width_m']}
    burn_line(pts, r['width_m'] / 2, 1)                    # as a barrier: the road keeps bounding parcels past the frame

plots = L['plots']; names = list(plots)
orig_masks = {n: poly_mask(plots[n]['polygon_m']) for n in names}
other_plot = np.zeros((N, N), np.int16)
for i, n in enumerate(names):
    other_plot[orig_masks[n]] = i + 1


def seg_dist(poly):
    d = np.full((N, N), 1e9, np.float32)
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy or 1e-9
        t = np.clip(((E - x0) * dx + (Nn - y0) * dy) / L2, 0, 1)
        d = np.minimum(d, np.hypot(E - (x0 + t * dx), Nn - (y0 + t * dy)))
    return d


def cell(q):
    return int((HALF - q.imag) / CELL), int((q.real + HALF) / CELL)


out = {}
ext_masks = {}
for i, name in enumerate(names):
    p = plots[name]; poly = [complex(*v) for v in p['polygon_m']]; ppx = p['polygon_px']; n = len(poly)
    fedges = [k for k in range(n) if frame_edge(ppx[k], ppx[(k + 1) % n])]
    if not fedges:
        continue
    core = orig_masks[name] & (seg_dist(p['polygon_m']) >= 10) & ~barrier
    if core.sum() < 50:
        core = orig_masks[name] & (seg_dist(p['polygon_m']) >= 4) & ~barrier
    mu = F[core].mean(0); spread = float(np.median(np.linalg.norm(F[core] - mu, axis=1))); thr = max(T_MIN, K * spread)
    centroid = sum(poly) / n
    pieces, edges_info = [], []
    for k in fedges:
        P0, P1 = poly[k], poly[(k + 1) % n]
        e = P1 - P0; nrm = complex(e.imag, -e.real) / abs(e)
        if ((P0 + P1) / 2 - centroid).real * nrm.real + ((P0 + P1) / 2 - centroid).imag * nrm.imag < 0:
            nrm = -nrm
        prev_k, next_k = (k - 1) % n, (k + 1) % n

        def side(vtx, other, is_frame):
            if is_frame:
                return nrm
            d = vtx - other; d /= abs(d)
            return d if (d.real * nrm.real + d.imag * nrm.imag) > 0.3 else nrm
        d0 = side(P0, poly[prev_k], prev_k in fedges)
        d1 = side(P1, poly[(k + 2) % n], next_k in fedges)
        m_rays = max(3, int(abs(e) / RAY_STEP) + 1)
        stops, reasons, origins, dirs = [], [], [], []
        for j in range(m_rays):
            t = j / (m_rays - 1)
            O = P0 + e * t; D = d0 * (1 - t) + d1 * t; D /= abs(D)
            s, run, sat_s, why = 0.0, 0, None, 'cap'
            while s < MAX_EXT:
                s += MARCH
                rr, cc = cell(O + D * s)
                if not (0 <= rr < N and 0 <= cc < N):
                    why = 'window'; break
                if barrier[rr, cc] and s > 3:
                    why = {1: 'road', 2: 'zone', 3: 'building'}.get(int(reason_map[rr, cc]), 'barrier'); break
                op = other_plot[rr, cc]
                if op and op != i + 1 and s > 3:
                    why = 'plot'; break
                if USE_SAT and np.linalg.norm(F[rr, cc] - mu) > thr:
                    run += 1
                    if run == 1:
                        sat_s = s
                    if run >= RUN:
                        s = sat_s; why = 'field_edge'; break
                else:
                    run = 0
            stops.append(s); reasons.append(why); origins.append(O); dirs.append(D)
        # straighten satellite/cap stops to one line per edge; road/plot/zone stops follow the obstacle (median-5 smoothed)
        sat = [s for s, w in zip(stops, reasons) if w in ('field_edge', 'cap', 'window')]
        straight = float(np.median(sat)) if sat else None
        hard = np.array([s if w not in ('field_edge', 'cap', 'window') else np.inf for s, w in zip(stops, reasons)])
        final = []
        for j in range(m_rays):
            lo, hi = max(0, j - 2), min(m_rays, j + 3)
            h = hard[lo:hi]; h = h[np.isfinite(h)]
            hj = float(np.median(h)) if len(h) else np.inf
            cand = [v for v in (straight, hj) if v is not None and np.isfinite(v)]
            final.append(min(cand) if cand else stops[j])
        far = [origins[j] + dirs[j] * final[j] for j in range(m_rays)]
        pieces.append([P0] + [P1] + far[::-1])
        from collections import Counter
        edges_info.append({'edge': k, 'length_m': round(abs(e), 1), 'rays': m_rays, 'stop_reasons': dict(Counter(reasons)),
                           'push_m_median': round(float(np.median(final)), 1), 'push_m_max': round(float(max(final)), 1),
                           'far_corner_0': [round(far[0].real, 2), round(far[0].imag, 2)], 'far_corner_1': [round(far[-1].real, 2), round(far[-1].imag, 2)]})
    # corners between two frame edges of this plot
    for a_, b_ in zip(fedges, fedges[1:] + fedges[:1]):
        if (a_ + 1) % n == b_ and len(fedges) > 1:
            ea = next(x for x in edges_info if x['edge'] == a_); eb = next(x for x in edges_info if x['edge'] == b_)
            C = poly[b_]                                          # shared vertex: end of edge a_, start of edge b_
            A1 = complex(*ea['far_corner_1']); B0 = complex(*eb['far_corner_0'])
            pieces.append([C, A1, A1 + (B0 - C), B0])
    m = orig_masks[name].copy()
    for pc in pieces:
        m |= poly_mask([(q.real, q.imag) for q in pc])
    ext_masks[name] = m
    out[name] = {'kind': p['kind'], 'signature_threshold': round(thr, 2), 'frame_edges': edges_info,
                 'pieces_m': [[[round(q.real, 2), round(q.imag, 2)] for q in pc] for pc in pieces],
                 'area_m2_traced': int(orig_masks[name].sum()), 'area_m2_parcel': int(m.sum())}
# overlaps between extensions: nearest original plot wins
label = np.zeros((N, N), np.int16)
for i, n in enumerate(names):
    label[orig_masks[n]] = i + 1
dist = {n: seg_dist(plots[n]['polygon_m']) for n in ext_masks}
best = np.full((N, N), 1e9, np.float32)
for n, m in ext_masks.items():
    i = names.index(n) + 1
    take = m & (label == 0) & (dist[n] < best)
    best[take] = dist[n][take]
for n, m in ext_masks.items():
    i = names.index(n) + 1
    label[m & (label == 0) & (dist[n] <= best + 1e-3)] = i
# drawn road (ground material) only as far as the extended plots beside its frame end + 10 m
roads_drawn = {n: {'line_m': [list(p) for p in r['line_m']], 'width_m': r['width_m']} for n, r in L['roads'].items()}
for re_ in road_ends:
    bx, by = re_['frame_point']; push = 0.0
    for n, v in out.items():
        for x in v['frame_edges']:
            k = x['edge']; poly = plots[n]['polygon_m']; P0, P1 = poly[k], poly[(k + 1) % len(poly)]
            dx, dy = P1[0] - P0[0], P1[1] - P0[1]; t = max(0, min(1, ((bx - P0[0]) * dx + (by - P0[1]) * dy) / (dx * dx + dy * dy)))
            if math.hypot(bx - (P0[0] + t * dx), by - (P0[1] + t * dy)) <= 15:
                push = max(push, x['push_m_max'])
    ln = min(re_['barrier_len_m'], push + 10.0) if push > 0 else 0.0
    q = (bx + re_['dir'][0] * ln, by + re_['dir'][1] * ln)
    line = roads_drawn[re_['road']]['line_m']
    if ln > 0:
        if re_['end'] == 0:
            line.insert(0, [round(q[0], 2), round(q[1], 2)])
        else:
            line.append([round(q[0], 2), round(q[1], 2)])
    re_['drawn_extension_m'] = round(ln, 1)
frame_d = seg_dist([(q.real, q.imag) for q in frame_m])
lu, ld, ll, lr = np.roll(label, 1, 0), np.roll(label, -1, 0), np.roll(label, 1, 1), np.roll(label, -1, 1)
for n in out:
    i = names.index(n) + 1; reg = label == i
    bnd = reg & ((lu != i) | (ld != i) | (ll != i) | (lr != i))
    out[n]['boundary_share_within_10m_of_old_frame'] = round(float((bnd & (frame_d <= 10)).sum() / max(1, bnd.sum())), 3)
    out[n]['area_m2_final'] = int(reg.sum())
gdrv = gdal.GetDriverByName('GTiff')
o = gdrv.Create(str(HERE / 'parcels_v2_labels.tif'), N, N, 1, gdal.GDT_Int16)
o.SetGeoTransform((-HALF, CELL, 0, HALF, 0, -CELL)); o.GetRasterBand(1).WriteArray(label); o = None
# ---- preview ----
ctx = gdal.Open(str(HERE / 'parcels_context.png'))
bg0 = np.stack([ctx.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3)], -1).astype(np.float32)
bg = np.full((N, N, 3), 60.0, np.float32); o_ = int(HALF - 700); bg[o_:o_ + 1400, o_:o_ + 1400] = bg0
pal = np.array([[0, 0, 0], [80, 200, 255], [255, 80, 80], [255, 180, 0], [255, 0, 255], [0, 255, 120], [150, 255, 0],
                [255, 255, 255], [0, 120, 255], [255, 120, 200], [200, 140, 60], [120, 0, 255], [0, 255, 255]], np.float32)
col = pal[np.clip(label, 0, len(pal) - 1)]
a = (label > 0)[..., None] * 0.38
img = bg * (1 - a) + col * a
edge = (label > 0) & ((label != lu) | (label != ll))
img[edge] = [255, 255, 255]
for nm_, r in roads_drawn.items():
    for (x0, y0), (x1, y1) in zip(r['line_m'], r['line_m'][1:]):
        for t in np.linspace(0, 1, int(math.hypot(x1 - x0, y1 - y0)) + 2):
            rr, cc = int(HALF - (y0 + (y1 - y0) * t)), int(x0 + (x1 - x0) * t + HALF)
            if 0 <= rr < N and 0 <= cc < N:
                img[rr, cc] = [255, 230, 0]
crop = img[int(HALF - 650):int(HALF + 650), int(HALF - 650):int(HALF + 650)]          # +-650 m around the pin
prev = gdal.GetDriverByName('MEM').Create('', crop.shape[1], crop.shape[0], 3, gdal.GDT_Byte)
for i in range(3): prev.GetRasterBand(i + 1).WriteArray(np.clip(crop[..., i], 0, 255).astype(np.uint8))
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'parcels_v2_preview.png'), prev)
rec = {'method': __doc__.split('Outputs:')[0].strip(), 'grid': {'half_m': HALF, 'cell_m': CELL, 'frame': 'metres from the pin, north up'},
       'params': {'MAX_EXT_m': MAX_EXT, 'ray_step_m': RAY_STEP, 'march_m': MARCH, 'T_MIN': T_MIN, 'K': K, 'run_samples': RUN, 'road_half_widths_m': HW},
       'labels_tif': str(HERE / 'parcels_v2_labels.tif'), 'legend': {i + 1: n for i, n in enumerate(names)},
       'roads_barrier_extension': roads_ext, 'roads_drawn': roads_drawn, 'road_ends': road_ends, 'extended_plots': out}
(HERE / 'PARCELS_V2.json').write_text(json.dumps(rec, indent=1))
print('road ends', [(r['road'], r['end'], round(r['barrier_len_m']), r['drawn_extension_m']) for r in road_ends])
for n, v in out.items():
    print('%-22s %6d -> %7d m2 | frame10m %.2f | %s' % (n, v['area_m2_traced'], v['area_m2_final'], v['boundary_share_within_10m_of_old_frame'],
          '; '.join('e%d push %s/%s %s' % (x['edge'], x['push_m_median'], x['push_m_max'], x['stop_reasons']) for x in v['frame_edges'])))
