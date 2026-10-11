"""Step 1 of 'every field from the screenshot' (Aviv 2026-10-10): per-pixel look of the plain wide screenshot (2.03 m/px)
grouped into colour/texture clusters (k-means in numpy, no BLAS), to be named by their centre values. Features: 10 m mean
R,G,B, greenness, 10 m texture (local std of brightness), 30 m mean brightness. Writes clusters.tif + CLUSTERS.json +
clusters_preview.png (each cluster in a flat colour) for naming. Only the picture's appearance is used; nothing is copied."""
import json
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent; REF = HERE.parent / 'References/Wide_2026-10-10'
bds = gdal.Open(str(REF / 'wide_satellite.webp'))
B = np.stack([bds.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3)], -1).astype(np.float32)
H, W = B.shape[:2]


def box(a, r):
    c = np.pad(a, ((r + 1, r), (r + 1, r)), mode='edge').cumsum(0).cumsum(1)
    return (c[2 * r + 1:, 2 * r + 1:] - c[:-2 * r - 1, 2 * r + 1:] - c[2 * r + 1:, :-2 * r - 1] + c[:-2 * r - 1, :-2 * r - 1]) / float((2 * r + 1) ** 2)


L = B.mean(-1)
m = [box(B[..., i], 2) for i in range(3)]
green = m[1] - 0.5 * (m[0] + m[2])
tex = np.sqrt(np.maximum(box(L * L, 2) - box(L, 2) ** 2, 0))
big = box(L, 7)
F = np.stack(m + [green * 2.0, tex * 2.0, big * 0.5], -1)
mu, sd = F.reshape(-1, 6).mean(0), F.reshape(-1, 6).std(0) + 1e-6
Z = (F - mu) / sd
rng = np.random.default_rng(3)
S = Z.reshape(-1, 6)[rng.choice(H * W, 60000, replace=False)]
K = 12
C = S[rng.choice(len(S), K, replace=False)]
for it in range(40):
    d = ((S[:, None, :] - C[None, :, :]) ** 2).sum(-1)
    lab = d.argmin(1)
    C = np.stack([S[lab == k].mean(0) if (lab == k).any() else C[k] for k in range(K)])
lab_full = np.zeros(H * W, np.uint8); flat = Z.reshape(-1, 6)
for i0 in range(0, H * W, 200000):
    blk = flat[i0:i0 + 200000]
    lab_full[i0:i0 + 200000] = ((blk[:, None, :] - C[None, :, :]) ** 2).sum(-1).argmin(1)
lab_full = lab_full.reshape(H, W)
cent = C * sd + mu
info = {}
for k in range(K):
    share = float((lab_full == k).mean())
    info[k] = {'share': round(share, 4), 'mean_rgb_10m': [int(v) for v in cent[k, :3]], 'greenness': round(float(cent[k, 3] / 2), 1),
               'texture_std': round(float(cent[k, 4] / 2), 1), 'brightness_30m': round(float(cent[k, 5] / 0.5), 1)}
d = gdal.GetDriverByName('GTiff').Create(str(HERE / 'clusters.tif'), W, H, 1, gdal.GDT_Byte); d.GetRasterBand(1).WriteArray(lab_full); d = None
pal = np.array([[230, 25, 75], [60, 180, 75], [255, 225, 25], [0, 130, 200], [245, 130, 48], [145, 30, 180], [70, 240, 240], [240, 50, 230],
                [210, 245, 60], [250, 190, 212], [0, 128, 128], [170, 110, 40]], np.uint8)
img = pal[lab_full]
pm = gdal.GetDriverByName('MEM').Create('', W, H, 3, gdal.GDT_Byte)
for i in range(3): pm.GetRasterBand(i + 1).WriteArray(img[..., i])
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'clusters_preview.png'), pm)
json.dump({'features': ['R10', 'G10', 'B10', 'greenness', 'texture', 'brightness30'], 'clusters': info, 'palette': pal.tolist()}, open(HERE / 'CLUSTERS.json', 'w'), indent=1)
for k, v in info.items(): print(k, pal[k].tolist(), v)
