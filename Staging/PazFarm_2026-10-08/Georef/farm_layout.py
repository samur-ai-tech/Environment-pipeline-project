"""Paz Farm layout from Aviv's screenshot (fit in FIT.json, OSM-road aligned, RMS ~9 m).
Plots are traced by hand in screenshot pixels (PLOTS below). For each plot this measures colours (dark/mean/light
percentiles) and the dominant row direction and spacing (2-D FFT of the plot's grey values). Writes:
  LAYOUT.json        plots in metres from the pin + measurements
  plots_check.png    traced outlines and measured row directions drawn on the screenshot (for review)
No Unreal work here.
"""
import json, math
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent
FIT = json.loads((HERE / 'FIT.json').read_text())
A = complex(*FIT['a']); B = complex(*FIT['b'])
to_m = lambda c, r: A * complex(c, -r) + B                     # screenshot px -> metres (east + i north) from pin
PLOTS = {  # name: (kind, polygon in screenshot px (col,row))
    'yard': ('yard', [(415, 105), (552, 105), (552, 258), (415, 258)]),
    'strawberry_west': ('strawberry_rows', [(366, 88), (414, 88), (414, 258), (546, 258), (546, 700), (366, 700)]),
    'triangle_top_bare': ('bare_soil', [(552, 258), (600, 258), (642, 358), (552, 358)]),
    'strawberry_triangle': ('strawberry_rows', [(552, 362), (643, 362), (846, 690), (552, 695)]),
    'orchard_south': ('orchard_avocado', [(362, 738), (982, 726), (1002, 850), (355, 850)]),
    'rows_east_unknown': ('orchard_citrus_young', [(858, 505), (958, 428), (1032, 330), (1046, 258), (1209, 258), (1209, 592), (882, 632)]),
    'orchard_northeast': ('orchard_citrus', [(1038, 150), (1209, 140), (1209, 248), (1046, 252), (1034, 196)]),
    'field_north_green': ('field_rows', [(918, 0), (1209, 0), (1209, 128), (998, 138), (962, 92)]),
    'field_northeast_big': ('field_rows', [(440, 0), (900, 0), (1005, 262), (990, 338), (862, 470), (832, 560), (700, 410), (560, 232), (452, 60)]),
    'field_southeast_brown': ('bare_soil', [(902, 650), (1209, 604), (1209, 800), (1012, 810), (946, 722)]),
    'fields_west_green': ('field_rows', [(0, 0), (356, 0), (346, 560), (252, 520), (0, 382)]),
    'field_southwest': ('field_rows', [(0, 432), (330, 592), (342, 850), (0, 850)]),
}
ROADS = {  # dirt roads as polylines (screenshot px) for the ground layer; width in metres
    'farm_road_diagonal': ([(548, 238), (640, 330), (760, 500), (850, 690)], 4.0),
    'yard_access_north': ([(405, 0), (412, 60), (440, 105)], 4.0),
    'west_track': ([(0, 390), (150, 455), (300, 540), (340, 600), (342, 850)], 4.0),
    'south_road': ([(345, 745), (600, 728), (900, 714)], 5.0),
    'east_road': ([(895, 0), (950, 120), (1010, 250), (1000, 380), (900, 470), (848, 540), (856, 640), (910, 712), (970, 780), (1002, 850)], 5.0),
    'east_spur': ([(880, 640), (1050, 615), (1209, 600)], 4.0),
}
shot = next((HERE.parent / 'References').glob('*.png'))
ds = gdal.Open(str(shot)); img = np.stack([ds.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3)], -1).astype(np.float32); ds = None
H, W = img.shape[:2]
grey = img.mean(-1)
rows, cols = np.mgrid[0:H, 0:W]


def inside(poly):
    m = np.zeros((H, W), bool)
    x = cols + 0.5; y = rows + 0.5
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        cond = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / ((y2 - y1) if y2 != y1 else 1e-9) + x1)
        m ^= cond
    return m


def rows_fft(mask):
    r0, r1 = np.where(mask.any(1))[0][[0, -1]]; c0, c1 = np.where(mask.any(0))[0][[0, -1]]
    g = grey[r0:r1 + 1, c0:c1 + 1].copy(); mk = mask[r0:r1 + 1, c0:c1 + 1]
    g[~mk] = g[mk].mean(); g -= g.mean()
    n = 256
    while n < max(g.shape): n *= 2
    win = np.outer(np.hanning(g.shape[0]), np.hanning(g.shape[1]))
    F = np.abs(np.fft.fftshift(np.fft.fft2(g * win, s=(n, n))))
    cy = cx = n // 2
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.hypot(yy - cy, xx - cx)
    F[(rr < n / 60.0) | (rr > n / 4.0)] = 0                   # periods between 4 px and 60 px (~1.4 m .. 21 m)
    peaks = []
    for _ in range(2):
        iy, ix = np.unravel_index(np.argmax(F), F.shape)
        fy, fx = (iy - cy) / n, (ix - cx) / n
        period_px = 1.0 / math.hypot(fx, fy)
        # stripes vary along the frequency vector; rows run perpendicular to it
        ang_freq = math.degrees(math.atan2(-fy, fx))           # image row-down -> north-up
        peaks.append({'period_px': round(period_px, 2), 'period_m': round(period_px * FIT['scale_m_per_px'], 2),
                      'row_direction_deg_from_east': round((ang_freq + 90.0 + FIT['rotation_deg']) % 180.0, 1),
                      'strength': float(F[iy, ix])})
        F[max(0, iy - 4):iy + 5, max(0, ix - 4):ix + 5] = 0; F[max(0, 2 * cy - iy - 4):2 * cy - iy + 5, max(0, 2 * cx - ix - 4):2 * cx - ix + 5] = 0
    return peaks


layout = {'fit': FIT, 'screenshot': str(shot), 'plots': {}, 'roads': {}}
check = img.copy()
for name, (kind, poly) in PLOTS.items():
    m = inside(poly)
    px = img[m]
    meas = {'kind': kind, 'pixels': int(m.sum()), 'area_m2': round(float(m.sum()) * FIT['scale_m_per_px'] ** 2),
            'colour_dark': [int(v) for v in np.percentile(px, 20, axis=0)], 'colour_mean': [int(v) for v in px.mean(0)],
            'colour_light': [int(v) for v in np.percentile(px, 80, axis=0)], 'rows': rows_fft(m),
            'polygon_m': [[round(z.real, 2), round(z.imag, 2)] for z in (to_m(c, r) for c, r in poly)], 'polygon_px': poly}
    layout['plots'][name] = meas
    edge = m & ~np.roll(m, 1, 0) | m & ~np.roll(m, 1, 1)
    check[edge] = (0, 255, 255)
    cx, cy = np.mean([p[0] for p in poly]), np.mean([p[1] for p in poly])
    d = math.radians(meas['rows'][0]['row_direction_deg_from_east'] - FIT['rotation_deg'])
    for t in np.linspace(-25, 25, 120):
        c, r = int(cx + t * math.cos(d)), int(cy - t * math.sin(d))
        if 0 <= c < W and 0 <= r < H: check[r, c] = (255, 0, 255)
for name, (line, width) in ROADS.items():
    layout['roads'][name] = {'width_m': width, 'line_m': [[round(z.real, 2), round(z.imag, 2)] for z in (to_m(c, r) for c, r in line)], 'line_px': line}
    for (c0, r0), (c1, r1) in zip(line, line[1:]):
        n = int(max(abs(c1 - c0), abs(r1 - r0))) + 1
        for k in range(n + 1):
            c, r = int(c0 + (c1 - c0) * k / n), int(r0 + (r1 - r0) * k / n)
            if 0 <= c < W and 0 <= r < H: check[r, c] = (255, 128, 0)
(HERE / 'LAYOUT.json').write_text(json.dumps(layout, indent=1), encoding='utf-8')
mem = gdal.GetDriverByName('MEM').Create('', W, H, 3, gdal.GDT_Byte)
for i in range(3): mem.GetRasterBand(i + 1).WriteArray(np.clip(check[..., i], 0, 255).astype(np.uint8))
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'plots_check.png'), mem)
for name, p in layout['plots'].items():
    print(name.ljust(22), p['kind'].ljust(22), str(p['area_m2']).rjust(6), 'm2 rows', [(q['period_m'], q['row_direction_deg_from_east']) for q in p['rows']])
