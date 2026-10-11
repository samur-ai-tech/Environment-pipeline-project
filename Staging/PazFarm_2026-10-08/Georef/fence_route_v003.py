"""Fence route v003 (Aviv 2026-10-09: "wrap around the road leading to the barn, and go around the farm").
Traces the black farm outline Aviv drew on References/FenceRoute_Aviv_2026-10-09.webp (same pixels as the original
screenshot) and the two yellow marks he added (read as gates), converts them with FIT.json to metres from the pin, and
writes FENCE_ROUTE_V003.json + fence_route_v003_check.png (route red, vertices blue, gates yellow outline).
Run with the gis env python:  python -W ignore fence_route_v003.py
"""
import json, math
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent
REF = HERE.parent / 'References' / 'FenceRoute_Aviv_2026-10-09.webp'
FIT = json.loads((HERE / 'FIT.json').read_text())
A, B = complex(*FIT['a']), complex(*FIT['b'])
to_m = lambda c, r: A * complex(c, -r) + B
ds = gdal.Open(str(REF))
img = np.stack([ds.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3)], -1).astype(int)
H, W = img.shape[:2]
dark = img.max(2) < 45
yellow = (img[:, :, 0] > 190) & (img[:, :, 1] > 180) & (img[:, :, 2] < 90)


def clusters(idx):
    """Runs of consecutive indices -> centres."""
    out, run = [], []
    for i in idx:
        if run and i != run[-1] + 1:
            out.append(sum(run) / len(run)); run = []
        run.append(i)
    if run:
        out.append(sum(run) / len(run))
    return out


def track_rows(start, r0, r1, step_max):
    """Follow one line down the rows from start=(col,row); returns [(col,row)]."""
    pts, prev, slope = [start], start[0], 0.0
    for r in range(r0, r1 + 1):
        cs = clusters(np.nonzero(dark[r])[0])
        guess = prev + slope
        near = [c for c in cs if abs(c - guess) <= step_max]
        if not near:
            continue
        c = min(near, key=lambda c: abs(c - guess))
        slope = 0.7 * slope + 0.3 * (c - prev) / max(1, r - pts[-1][1])
        prev = c; pts.append((c, r))
    return pts


def track_cols(c0, c1, row_guess, step_max):
    pts, prev = [], row_guess
    for c in range(c0, c1 - 1, -1):
        rs = clusters(np.nonzero(dark[:, c])[0])
        near = [r for r in rs if abs(r - prev) <= step_max]
        if near:
            r = min(near, key=lambda r: abs(r - prev)); prev = r; pts.append((c, r))
    return pts


def dp(pts, tol):
    """Douglas-Peucker on [(x,y)]."""
    if len(pts) < 3:
        return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    L = math.hypot(x1 - x0, y1 - y0) or 1e-9
    d = [abs((y1 - y0) * x - (x1 - x0) * y + x1 * y0 - y1 * x0) / L for x, y in pts]
    i = int(np.argmax(d))
    if d[i] > tol:
        return dp(pts[:i + 1], tol)[:-1] + dp(pts[i:], tol)
    return [pts[0], pts[-1]]


# right-hand line: from the top-left vertex down the NE side to the south-east corner
top = min(((c, r) for r in range(55, 80) for c in clusters(np.nonzero(dark[r, 360:400])[0] + 360)), key=lambda p: p[1])
right = [top] + track_rows((441.5, 100), 101, 704, 6)[1:]
left = [top] + track_rows((376.0, 100), 101, 716, 4)[1:]
bottom = track_cols(892, 352, 718, 4)
route = dp(right, 2.0)[:-1] + dp(bottom, 2.0) + list(reversed(dp(left, 2.0)))
# merge near-duplicate vertices (< 4 px) and close the loop
poly = []
for p in route:
    if not poly or math.hypot(p[0] - poly[-1][0], p[1] - poly[-1][1]) > 4:
        poly.append((round(p[0], 1), round(p[1], 1)))
if math.hypot(poly[0][0] - poly[-1][0], poly[0][1] - poly[-1][1]) < 8:
    poly = poly[:-1]
# gates from yellow blobs (split by column)
ys, xs = np.nonzero(yellow)
gates = []
for lo, hi in ((820, 870), (870, 910)):
    m = (xs >= lo) & (xs < hi)
    if m.sum() > 20:
        gates.append({'px_box': [int(xs[m].min()), int(ys[m].min()), int(xs[m].max()), int(ys[m].max())],
                      'px_centre': [float(xs[m].mean()), float(ys[m].mean())]})
traced = list(poly)
# Manual cleanup of three tracing glitches (checked on fence_route_v003_check.png): the jog under the upper yellow mark,
# the zig-zag at the south-west corner and a 1-px kink near the top. Every kept vertex is a traced vertex.
poly = [(391.0, 60), (492.0, 139), (531.0, 164), (553.5, 223), (652.0, 300), (856.5, 624), (884.5, 701), (882, 721.5),
        (725, 715.0), (562, 702.0), (443, 717.0), (372, 719.5), (355.0, 697), (376.0, 101)]
poly_m = [to_m(c, r) for c, r in poly]
perim = sum(abs(poly_m[(i + 1) % len(poly_m)] - poly_m[i]) for i in range(len(poly_m)))
for g in gates:
    z = to_m(*g['px_centre'])
    # nearest route edge -> gate direction
    best = None
    for i in range(len(poly_m)):
        p0, p1 = poly_m[i], poly_m[(i + 1) % len(poly_m)]
        d = p1 - p0; t = max(0.0, min(1.0, ((z - p0) * d.conjugate()).real / abs(d) ** 2)); q = p0 + d * t
        if best is None or abs(z - q) < best[0]:
            best = (abs(z - q), i, q, d)
    g.update(e=round(best[2].real, 3), n=round(best[2].imag, 3), edge=best[1], offset_from_route_m=round(best[0], 2),
             dir_deg=round(math.degrees(math.atan2(best[3].imag, best[3].real)), 3))
# gate placement rule: gate 1 (upper yellow mark, at the bend where the barn road leaves for the junction) starts 0.1 m
# after vertex 5 on edge 5; gate 2 (lower yellow mark) spans the whole short south-east edge 6 (gate scaled to its length).
e5 = poly_m[6] - poly_m[5]; d5 = e5 / abs(e5)
g1 = poly_m[5] + d5 * 3.1
e6 = poly_m[7] - poly_m[6]
gates[0].update(e=round(g1.real, 3), n=round(g1.imag, 3), edge=5, width_m=6.0, dir_deg=round(math.degrees(math.atan2(d5.imag, d5.real)), 3))
gm = (poly_m[6] + poly_m[7]) / 2
gates[0]['spans_edge'] = False; gates[1]['spans_edge'] = True
gates[1].update(e=round(gm.real, 3), n=round(gm.imag, 3), edge=6, width_m=round(abs(e6), 3), dir_deg=round(math.degrees(math.atan2(e6.imag, e6.real)), 3))
out = {'traced_vertices_px': traced, 'source': str(REF), 'fit': 'FIT.json (0.353 m/px, rot -3.35 deg, RMS 8.96 m)', 'vertices_px': poly,
       'vertices_m': [[round(z.real, 3), round(z.imag, 3)] for z in poly_m], 'perimeter_m': round(perim, 1), 'gates': gates,
       'note': 'closed loop, order = top-left vertex, NE side down, south side west, west side up; gates = yellow marks'}
(HERE / 'FENCE_ROUTE_V003.json').write_text(json.dumps(out, indent=1))
# check image
chk = img.copy().astype(np.uint8)
def line(p0, p1, col, w=1):
    n = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]))) + 1
    for k in range(n + 1):
        c = p0[0] + (p1[0] - p0[0]) * k / n; r = p0[1] + (p1[1] - p0[1]) * k / n
        for dc in range(-w, w + 1):
            for dr in range(-w, w + 1):
                cc, rr = int(round(c)) + dc, int(round(r)) + dr
                if 0 <= cc < W and 0 <= rr < H:
                    chk[rr, cc] = col
for i in range(len(poly)):
    line(poly[i], poly[(i + 1) % len(poly)], (255, 0, 0))
for c, r in poly:
    line((c - 3, r), (c + 3, r), (0, 80, 255), 1)
drv = gdal.GetDriverByName('MEM').Create('', W, H, 3, gdal.GDT_Byte)
for i in range(3):
    drv.GetRasterBand(i + 1).WriteArray(chk[:, :, i])
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'fence_route_v003_check.png'), drv)
print(json.dumps({'vertices': len(poly), 'perimeter_m': out['perimeter_m'], 'gates': gates, 'poly_px': poly}))
