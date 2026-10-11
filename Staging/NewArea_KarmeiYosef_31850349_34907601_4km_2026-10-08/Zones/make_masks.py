"""Per-zone mask textures (1024 x 1024, 255 inside the zone, 0 outside; same orientation as T_KY4_Zones) for PCG."""
import json
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
TASK = Path(__file__).resolve().parent
R = json.loads((TASK / 'DATA_RECEIPT.json').read_text(encoding='utf-8'))
OUT = Path(R['output_dir']); G = R['grid']['bounds_epsg4326']
zds = gdal.Warp('', str(OUT / 'ZONES.tif'), format='MEM', width=1024, height=1024, resampleAlg='near',
               outputBounds=(G['west'], G['south'], G['east'], G['north']))
z = zds.GetRasterBand(1).ReadAsArray()
MASKS = {'Forest': (3,), 'Orchard': (4,), 'Vineyard': (5,), 'ScrubMix': (6, 10), 'Grass': (7, 12), 'Crop': (9,)}
info = {}
for name, codes in MASKS.items():
    m = np.isin(z, codes).astype(np.uint8) * 255
    mem = gdal.GetDriverByName('MEM').Create('', 1024, 1024, 1, gdal.GDT_Byte); mem.GetRasterBand(1).WriteArray(m)
    path = OUT / ('T_KY4_Mask_%s.png' % name)
    gdal.GetDriverByName('PNG').CreateCopy(str(path), mem)
    info[name] = {'codes': codes, 'file': str(path), 'share': round(float((m > 0).mean()), 4), 'area_km2': round(float((m > 0).mean()) * 4.032 ** 2, 3)}
(TASK / 'MASKS.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
print(json.dumps({k: (v['share'], v['area_km2']) for k, v in info.items()}))
