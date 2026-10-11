"""Textures for Unreal from the zone data (no editor). Orientation: row 0 = north edge, column 0 = west edge of the
+-2016 m landscape grid; in the Karmei Yosef maps Unreal X = east and Y = south, so u = (X - Xmin) / 4032 m and
v = (Y - Ymin) / 4032 m with Xmin = Ymin = -201600 cm.
  T_KY4_Satellite.png  2048 x 2048 RGB, Sentinel-2 21 Sep 2026 (stretch /2500, the same look as the previews).
  T_KY4_Zones.png      1024 x 1024 grey, zone code * 20 (nearest), for PCG sampling with range filters.
"""
import json
from pathlib import Path

import numpy as np
from osgeo import gdal

gdal.UseExceptions()
TASK = Path(__file__).resolve().parent
R = json.loads((TASK / 'DATA_RECEIPT.json').read_text(encoding='utf-8'))
OUT = Path(R['output_dir'])
G = R['grid']['bounds_epsg4326']
src = R['sentinel2']['recent']['file']
sat = gdal.Warp('', src, format='MEM', width=2048, height=2048, resampleAlg='cubic',
                outputBounds=(G['west'], G['south'], G['east'], G['north']))
rgb = np.stack([sat.GetRasterBand(i).ReadAsArray().astype(np.float32) for i in (1, 2, 3)], -1)
img = np.clip(rgb / 2500.0 * 255.0, 0, 255).astype(np.uint8)
mem = gdal.GetDriverByName('MEM').Create('', 2048, 2048, 3, gdal.GDT_Byte)
for i in range(3):
    mem.GetRasterBand(i + 1).WriteArray(img[..., i])
gdal.GetDriverByName('PNG').CreateCopy(str(OUT / 'T_KY4_Satellite.png'), mem)
z = gdal.Warp('', str(OUT / 'ZONES.tif'), format='MEM', width=1024, height=1024, resampleAlg='near',
              outputBounds=(G['west'], G['south'], G['east'], G['north']))
codes = z.GetRasterBand(1).ReadAsArray().astype(np.uint8)
mem = gdal.GetDriverByName('MEM').Create('', 1024, 1024, 1, gdal.GDT_Byte)
mem.GetRasterBand(1).WriteArray((codes * 20).astype(np.uint8))
gdal.GetDriverByName('PNG').CreateCopy(str(OUT / 'T_KY4_Zones.png'), mem)
info = {'satellite': str(OUT / 'T_KY4_Satellite.png'), 'zones': str(OUT / 'T_KY4_Zones.png'),
        'zone_value': 'code * 20 (codes 1..12 -> 20..240)', 'zone_codes_present': sorted(int(c) for c in np.unique(codes)),
        'mapping': 'u = (X + 201600) / 403200, v = (Y + 201600) / 403200 (cm, X east, Y south)'}
(TASK / 'TEXTURES.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
print(json.dumps(info, indent=2))
