"""Fit a similarity transform (scale, rotation, shift) from Aviv's screenshot pixels to local metres from the pin, using
road control points matched to OpenStreetMap roads; draw the OSM roads onto the screenshot to check the fit.
Control points: screenshot (col, row) <-> overlay pixel (col, row) of overlay.png (1 px = 1 m, pin at 400,400, north up)."""
import json, sys
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent
CP = json.loads((HERE / 'control_points.json').read_text())
S = np.array([c['screenshot'] for c in CP['points']], float)
O = np.array([c['overlay'] for c in CP['points']], float)
M = np.stack([O[:, 0] - 400.0, 400.0 - O[:, 1]], 1)          # metres east, north of pin
# complex least squares: m = a * s + b, with s = col - i*row (row down -> north up)
s = S[:, 0] - 1j * S[:, 1]; m = M[:, 0] + 1j * M[:, 1]
# closed-form complex least squares (numpy.linalg.lstsq crashes in this GIS environment: missing LAPACK DLL)
sm, mm = s.mean(), m.mean()
a = complex(np.sum(np.conj(s - sm) * (m - mm)) / np.sum(np.abs(s - sm) ** 2))
b = complex(mm - a * sm)
res = np.abs(a * s + b - m)
fit = {'scale_m_per_px': float(abs(a)), 'rotation_deg': float(np.degrees(np.angle(a))), 'a': [a.real, a.imag], 'b': [b.real, b.imag],
       'residuals_m': [round(float(r), 1) for r in res], 'rms_m': round(float(np.sqrt((res ** 2).mean())), 2)}
(HERE / 'FIT.json').write_text(json.dumps(fit, indent=2))
print(json.dumps(fit))
shot = next((HERE.parent / 'References').glob('*.png'))
ds = gdal.Open(str(shot)); img = np.stack([ds.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3)], -1).copy()
h, w = img.shape[:2]
roads = json.loads((HERE / 'roads.json').read_text())['roads']
for r in roads:
    pts = [complex(x, y) for x, y in r['pts_m_from_pin']]
    px = [((p - b) / a) for p in pts]                        # back to screenshot: s = (m - b) / a
    for p0, p1 in zip(px, px[1:]):
        n = int(max(abs(p1.real - p0.real), abs(p1.imag - p0.imag))) + 1
        for k in range(n + 1):
            q = p0 + (p1 - p0) * k / n
            c, rr = int(round(q.real)), int(round(-q.imag))
            for dc in (-1, 0, 1):
                if 0 <= c + dc < w and 0 <= rr < h:
                    img[rr, c + dc] = (255, 0, 0)
for c in CP['points']:
    cc, rr = map(int, c['screenshot'])
    img[max(0, rr - 6):rr + 7, max(0, cc - 1):cc + 2] = (0, 255, 255); img[max(0, rr - 1):rr + 2, max(0, cc - 6):cc + 7] = (0, 255, 255)
mem = gdal.GetDriverByName('MEM').Create('', w, h, 3, gdal.GDT_Byte)
for i in range(3): mem.GetRasterBand(i + 1).WriteArray(img[..., i])
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'screenshot_with_osm_roads.png'), mem)
