"""Copies of the six 4 km zone masks with the Paz Farm screenshot footprint cleared (so the stand-in PCG plants leave the
farm to the real models). Originals stay untouched in the zones folder (undo = re-import the originals)."""
import json
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent
FIT = json.loads((HERE / 'FIT.json').read_text()); A = complex(*FIT['a']); B = complex(*FIT['b'])
pe, pn = json.loads((HERE / 'roads.json').read_text())['pin_local_m_from_area_centre']
masks = json.loads(Path(r'C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08\Zones\MASKS.json').read_text())
OUT = Path(r'C:\Users\USER\Documents\Pipeline Environment\SourceData\KarmeiYosef_31850349_34907601_4km\zones\PazFarm\masks_without_farm'); OUT.mkdir(parents=True, exist_ok=True)
corners = [A * complex(c, -r) + B for c, r in ((0, 0), (1209, 0), (1209, 850), (0, 850))]
poly = [((z.real + pe + 2016) / 4032 * 1024, (2016 - (z.imag + pn)) / 4032 * 1024) for z in corners]   # texture col,row
rr, cc = np.mgrid[0:1024, 0:1024] + 0.5
inside = np.zeros((1024, 1024), bool)
for i in range(4):
    (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % 4]
    inside ^= ((y1 > rr) != (y2 > rr)) & (cc < (x2 - x1) * (rr - y1) / (y2 - y1 + 1e-12) + x1)
info = {'footprint_texture_px': poly, 'cleared_pixels': int(inside.sum()), 'files': {}}
for name, m in masks.items():
    ds = gdal.Open(m['file']); a = ds.GetRasterBand(1).ReadAsArray(); ds = None
    before = int((a > 0).sum()); a = a.copy(); a[inside] = 0
    mem = gdal.GetDriverByName('MEM').Create('', 1024, 1024, 1, gdal.GDT_Byte); mem.GetRasterBand(1).WriteArray(a)
    p = OUT / ('T_KY4_Mask_%s.png' % name); gdal.GetDriverByName('PNG').CreateCopy(str(p), mem)
    info['files'][name] = {'file': str(p), 'original': m['file'], 'pixels_before': before, 'pixels_after': int((a > 0).sum())}
(HERE / 'MASKS_WITHOUT_FARM.json').write_text(json.dumps(info, indent=1))
print(json.dumps({k: (v['pixels_before'], v['pixels_after']) for k, v in info['files'].items()}), info['cleared_pixels'])
