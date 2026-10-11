"""Align Aviv's two wide screenshots (2026-10-10): A = with Google road lines/labels, B = satellite only. Finds the pixel
offset (and checks scale) of B relative to A by normalised cross-correlation of grey images. Writes ALIGN.json."""
import json
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
REF = Path(__file__).resolve().parents[1] / 'References/Wide_2026-10-10'
def load(n):
    d = gdal.Open(str(REF / n)); return np.stack([d.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3)], -1).astype(np.float32)
A, B = load('wide_with_roads.webp'), load('wide_satellite.webp')
ga, gb = A.mean(-1), B.mean(-1)
best = None
for s in (0.995, 1.0, 1.005):
    for dy in range(-10, 11):
        for dx in range(-10, 11):
            # B pixel (x, y) ~ A pixel (x*s + dx, y*s + dy); sample on a coarse grid
            ys, xs = np.mgrid[40:780:6, 40:1640:6]
            xa = np.round(xs * s + dx).astype(int); ya = np.round(ys * s + dy).astype(int)
            ok = (xa >= 0) & (xa < ga.shape[1]) & (ya >= 0) & (ya < ga.shape[0])
            a = ga[ya[ok], xa[ok]]; b = gb[ys[ok], xs[ok]]
            a = a - a.mean(); b = b - b.mean(); r = float((a * b).mean() / (a.std() * b.std() + 1e-9))     # no BLAS (env not activated)
            if best is None or r > best[0]:
                best = (r, s, dx, dy)
print('best corr %.4f scale %.3f dx %d dy %d' % best)
json.dump({'corr': best[0], 'scale_B_to_A': best[1], 'dx': best[2], 'dy': best[3], 'shape_A': list(A.shape), 'shape_B': list(B.shape)}, open('ALIGN.json', 'w'), indent=1)
