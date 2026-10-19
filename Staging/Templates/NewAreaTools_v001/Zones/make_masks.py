"""Per-zone mask textures (1024 x 1024, 255 inside the zone, 0 outside; same orientation as T_<AREA_SHORT>_Zones) for PCG.
Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69). Names and size from ../Tools/area_constants.py (MASK_PREFIX, HALF_EXTENT_M)."""
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
SIDE_KM = 2 * A.HALF_EXTENT_M / 1000.0
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
    path = OUT / ('%s%s.png' % (A.MASK_PREFIX, name))
    gdal.GetDriverByName('PNG').CreateCopy(str(path), mem)
    info[name] = {'codes': codes, 'file': str(path), 'share': round(float((m > 0).mean()), 4), 'area_km2': round(float((m > 0).mean()) * SIDE_KM ** 2, 3)}
(TASK / 'MASKS.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
print(json.dumps({k: (v['share'], v['area_km2']) for k, v in info.items()}))
