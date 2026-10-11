"""Strawberry bed layout v2 (Aviv 2026-10-11: "Real spacing" + beds must sit on the ground). Same two traced plots and row
directions as farm_ground.py (LAYOUT.json strawberry_west / strawberry_triangle) and the same 4 m tiles, but 1.7 m between
bed centres instead of the measured 5.5-5.8 m screenshot stripe period. A tile (start point + 4 m along the row) is kept
only when both ends are inside its plot (start margin 1.5 m as before, end margin 0.5 m), both ends are inside the v003
fence (FENCE_ROUTE_V003.json) at least 1.0 m from it, and the tile stays 2.5 m from every OSM track centreline.
Writes STRAWBERRY_BEDS_V2.json (metres east/north of the Paz Farm pin; row_deg from east, counter-clockwise) and
strawberry_beds_v2_preview.png is not made (no GDAL needed). Run: python strawberry_beds_v2.py
"""
import json, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
PITCH, TILE, START_MARGIN, END_MARGIN, FENCE_MARGIN, TRACK_CLEAR = 1.7, 4.0, 1.5, 0.5, 1.0, 2.5
L = json.loads((HERE / 'LAYOUT.json').read_text())
FENCE = json.loads((HERE / 'FENCE_ROUTE_V003.json').read_text())['vertices_m']
TRACKS = [w['pts_m_from_pin'] for w in json.loads((HERE / 'roads.json').read_text())['roads'] if w['highway'] == 'track']


def in_poly(e, n, poly):
    inside = False
    for i in range(len(poly)):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % len(poly)]
        if (y0 > n) != (y1 > n) and e < x0 + (n - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def seg_dist(e, n, pts, closed):
    best = 1e18
    m = len(pts) if closed else len(pts) - 1
    for i in range(m):
        x0, y0 = pts[i][:2]; x1, y1 = pts[(i + 1) % len(pts)][:2]
        dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy or 1e-9
        t = min(1, max(0, ((e - x0) * dx + (n - y0) * dy) / L2))
        best = min(best, math.hypot(e - (x0 + t * dx), n - (y0 + t * dy)))
    return best


out, stats = [], {}
for name in ('strawberry_west', 'strawberry_triangle'):
    p = L['plots'][name]; poly = p['polygon_m']; rd = p['rows'][0]['row_direction_deg_from_east']
    th = math.radians(rd); ux, uy = math.cos(th), math.sin(th); vx, vy = -uy, ux
    us = [q[0] * ux + q[1] * uy for q in poly]; vs = [q[0] * vx + q[1] * vy for q in poly]
    st = {'candidates': 0, 'plot': 0, 'fence': 0, 'track': 0, 'kept': 0, 'rows': set()}
    v = math.floor(min(vs) / PITCH) * PITCH + PITCH / 2
    while v <= max(vs):
        u = math.floor(min(us) / TILE) * TILE
        while u <= max(us):
            e0, n0 = u * ux + v * vx, u * uy + v * vy
            e1, n1 = e0 + TILE * ux, n0 + TILE * uy
            st['candidates'] += 1
            if not (in_poly(e0, n0, poly) and seg_dist(e0, n0, poly, True) >= START_MARGIN
                    and in_poly(e1, n1, poly) and seg_dist(e1, n1, poly, True) >= END_MARGIN):
                st['plot'] += 1
            elif not all(in_poly(a, b, FENCE) and seg_dist(a, b, FENCE, True) >= FENCE_MARGIN for a, b in ((e0, n0), (e1, n1))):
                st['fence'] += 1
            elif any(seg_dist(a, b, t, False) < TRACK_CLEAR for t in TRACKS for a, b in ((e0, n0), ((e0 + e1) / 2, (n0 + n1) / 2), (e1, n1))):
                st['track'] += 1
            else:
                st['kept'] += 1; st['rows'].add(round(v, 2))
                out.append({'plot': name, 'e': round(e0, 3), 'n': round(n0, 3), 'row_deg': rd})
            u += TILE
        v += PITCH
    st['rows'] = len(st['rows']); stats[name] = st
rec = {'units': 'metres east/north of the Paz Farm pin; e/n = tile start (pivot); tile runs 4 m along row_deg (from east, CCW)',
       'pitch_m': PITCH, 'tile_m': TILE, 'margins_m': {'plot_start': START_MARGIN, 'plot_end': END_MARGIN, 'fence': FENCE_MARGIN,
       'track_clear': TRACK_CLEAR}, 'stats': stats, 'count': len(out), 'beds': out,
       'authority': 'Aviv 2026-10-11: "Real spacing" (rows 1.7 m apart) + beds must sit on the ground'}
(HERE / 'STRAWBERRY_BEDS_V2.json').write_text(json.dumps(rec, indent=1), encoding='utf-8')
print(json.dumps({'count': len(out), 'stats': stats}, indent=1))
