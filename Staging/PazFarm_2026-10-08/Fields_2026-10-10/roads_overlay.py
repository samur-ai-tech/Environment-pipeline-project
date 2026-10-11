"""Road lines from Aviv's two wide screenshots (2026-10-10): the Google road overlay = pixels that are light, neutral grey in
the labelled image and differ from the plain satellite image at the same place (alignment from ALIGN.json). Text labels
(dark glyphs, white halos, icons) are removed by colour and by component shape. Output in the plain image's pixel frame:
road_mask.png (0/255), road_overlay_preview.png."""
import json
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent; REF = HERE.parent / 'References/Wide_2026-10-10'
AL = json.loads((HERE / 'ALIGN.json').read_text())
def load(n):
    d = gdal.Open(str(REF / n)); return np.stack([d.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3)], -1).astype(np.float32)
A, B = load('wide_with_roads.webp'), load('wide_satellite.webp')
H, W = B.shape[:2]
ys, xs = np.mgrid[0:H, 0:W]
xa = np.clip(xs + AL['dx'], 0, A.shape[1] - 1); ya = np.clip(ys + AL['dy'], 0, A.shape[0] - 1)
Aw = A[ya, xa]                                  # labelled image resampled into B's frame
mx, mn = Aw.max(-1), Aw.min(-1)
mean = Aw.mean(-1)
grey = (mx - mn < 18) & (mean > 128) & (mean < 200)        # Google minor-road grey (~150-165, measured)
yellow = (Aw[..., 0] > 200) & (Aw[..., 1] > 195) & (Aw[..., 2] > 130) & (Aw[..., 2] < 200) & (Aw[..., 0] - Aw[..., 2] > 25)   # road 44 (cream)
diff = np.abs(Aw - B).sum(-1)
cand = grey & (diff > 40)
hw = yellow & (diff > 40)
mem = gdal.GetDriverByName('MEM').Create('', W, H, 1, gdal.GDT_Byte); mem.GetRasterBand(1).WriteArray(cand.astype(np.uint8))
# remove small specks (text, icons) with GDAL's sieve (connected components smaller than 60 px)
gdal.SieveFilter(mem.GetRasterBand(1), None, mem.GetRasterBand(1), 60, 8)
m = mem.GetRasterBand(1).ReadAsArray() > 0
out = gdal.GetDriverByName('MEM').Create('', W, H, 1, gdal.GDT_Byte); out.GetRasterBand(1).WriteArray(m.astype(np.uint8) * 255)
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'road_mask.png'), out)
hm = gdal.GetDriverByName('MEM').Create('', W, H, 1, gdal.GDT_Byte); hm.GetRasterBand(1).WriteArray(hw.astype(np.uint8))
gdal.SieveFilter(hm.GetRasterBand(1), None, hm.GetRasterBand(1), 60, 8)
hwm = hm.GetRasterBand(1).ReadAsArray() > 0
ho = gdal.GetDriverByName('MEM').Create('', W, H, 1, gdal.GDT_Byte); ho.GetRasterBand(1).WriteArray(hwm.astype(np.uint8) * 255)
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'highway_mask.png'), ho)
prev = (B * 0.6).astype(np.uint8); prev[m] = [255, 40, 40]; prev[hwm] = [255, 230, 0]
pm = gdal.GetDriverByName('MEM').Create('', W, H, 3, gdal.GDT_Byte)
for i in range(3): pm.GetRasterBand(i + 1).WriteArray(prev[..., i])
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'road_overlay_preview.png'), pm)
print('road pixels', int(m.sum()), 'highway pixels', int(hwm.sum()), 'of', H * W)
