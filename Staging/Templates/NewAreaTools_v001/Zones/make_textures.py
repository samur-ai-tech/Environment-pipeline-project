"""Textures for Unreal from the zone data (no editor). Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69). Orientation: row 0 = north
edge, column 0 = west edge of the +-HALF_EXTENT_M landscape grid; in GeoCity maps Unreal X = east and Y = south, so
u = (X - Xmin) / (2 HALF_EXTENT_M) and v = (Y - Ymin) / (2 HALF_EXTENT_M) with Xmin = Ymin = -HALF_EXTENT_CM.
  T_<AREA_SHORT>_Satellite.png  2048 x 2048 RGB, the recent Sentinel-2 scene; stretch = SAT_STRETCH of area_constants.py
                       (El Wahat: /5000, because desert sand reflectance is 0.33-0.48 in red and /2500 clipped 99.8% of the
                       area to white); TEXTURES.json records clipped_fraction.
  T_<AREA_SHORT>_Zones.png      1024 x 1024 grey, zone code * 20 (nearest), for PCG sampling with range filters.
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
from osgeo import gdal

gdal.UseExceptions()
TASK = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('area_constants', TASK.parent / 'Tools' / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (refuses if not filled in)
assert TASK.parent.name == A.TASK_FOLDER, (TASK.parent.name, A.TASK_FOLDER)
R = json.loads((TASK / 'DATA_RECEIPT.json').read_text(encoding='utf-8'))
OUT = Path(R['output_dir'])
G = R['grid']['bounds_epsg4326']
src = R['sentinel2']['recent']['file']
sat = gdal.Warp('', src, format='MEM', width=2048, height=2048, resampleAlg='cubic',
                outputBounds=(G['west'], G['south'], G['east'], G['north']))
rgb = np.stack([sat.GetRasterBand(i).ReadAsArray().astype(np.float32) for i in (1, 2, 3)], -1)
STRETCH = float(A.SAT_STRETCH)
img = np.clip(rgb / STRETCH * 255.0, 0, 255).astype(np.uint8)
mem = gdal.GetDriverByName('MEM').Create('', 2048, 2048, 3, gdal.GDT_Byte)
for i in range(3):
    mem.GetRasterBand(i + 1).WriteArray(img[..., i])
gdal.GetDriverByName('PNG').CreateCopy(str(OUT / (A.SAT_TEXTURE + '.png')), mem)
z = gdal.Warp('', str(OUT / 'ZONES.tif'), format='MEM', width=1024, height=1024, resampleAlg='near',
              outputBounds=(G['west'], G['south'], G['east'], G['north']))
codes = z.GetRasterBand(1).ReadAsArray().astype(np.uint8)
mem = gdal.GetDriverByName('MEM').Create('', 1024, 1024, 1, gdal.GDT_Byte)
mem.GetRasterBand(1).WriteArray((codes * 20).astype(np.uint8))
gdal.GetDriverByName('PNG').CreateCopy(str(OUT / (A.ZONES_TEXTURE + '.png')), mem)
info = {'satellite': str(OUT / (A.SAT_TEXTURE + '.png')), 'zones': str(OUT / (A.ZONES_TEXTURE + '.png')),
        'zone_value': 'code * 20 (codes 1..12 -> 20..240)', 'zone_codes_present': sorted(int(c) for c in np.unique(codes)),
        'mapping': 'u = (X + %g) / %g, v = (Y + %g) / %g (cm, X east, Y south)' % ((A.HALF_EXTENT_CM, 2 * A.HALF_EXTENT_CM) * 2),
        'stretch': STRETCH, 'clipped_fraction': round(float((img == 255).any(-1).mean()), 5), 'mean_srgb': [round(float(img[..., i].mean()), 1) for i in range(3)]}
(TASK / 'TEXTURES.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
print(json.dumps(info, indent=2))
