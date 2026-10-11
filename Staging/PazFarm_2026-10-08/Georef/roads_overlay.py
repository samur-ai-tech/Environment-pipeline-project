"""Satellite crop (Sentinel-2 21 Sep 2026, 10 m) around the Paz Farm pin with OSM roads from the 4 km source package,
for matching Aviv's screenshot. Writes Georef/overlay.png (north up, 1 px = 1 m, 800 x 800 m) and roads.json."""
import json, math
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent
PIN = (31.851309, 34.906260)
S4 = Path(r'C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08')
pkg = json.loads(Path(json.loads((S4 / 'ACQUISITION_RECEIPT.json').read_text())['package_path']).read_text())
LON0, LAT0 = pkg['origin']['lon0'], pkg['origin']['lat0']
MLAT, MLON = pkg['local_frame']['Mlat_m_per_deg'], pkg['local_frame']['Mlon_m_per_deg']
osm = Path(json.loads((S4 / 'ACQUISITION_RECEIPT.json').read_text())['package_path']).parent / 'osm'
osm_file = next(osm.glob('*.osm'))
recv = json.loads((S4 / 'Zones/DATA_RECEIPT.json').read_text())
px, py = (PIN[1] - LON0) * MLON, (PIN[0] - LAT0) * MLAT   # pin in local metres (east, north)
H = 400
ds = gdal.Warp('', recv['sentinel2']['recent']['file'], format='MEM', width=2 * H, height=2 * H, resampleAlg='cubic',
               outputBounds=(PIN[1] - H / MLON, PIN[0] - H / MLAT, PIN[1] + H / MLON, PIN[0] + H / MLAT))
img = np.clip(np.stack([ds.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3)], -1) / 2500 * 255, 0, 255).astype(np.uint8)
root = ET.parse(osm_file).getroot()
nodes = {n.get('id'): (float(n.get('lon')), float(n.get('lat'))) for n in root.findall('node')}
roads = []
for w in root.findall('way'):
    t = {x.get('k'): x.get('v') for x in w.findall('tag')}
    if 'highway' not in t:
        continue
    pts = [nodes[n.get('ref')] for n in w.findall('nd')]
    loc = [((lo - PIN[1]) * MLON, (la - PIN[0]) * MLAT) for lo, la in pts]
    if not any(abs(x) < H and abs(y) < H for x, y in loc):
        continue
    roads.append({'id': w.get('id'), 'highway': t['highway'], 'pts_m_from_pin': [[round(x, 1), round(y, 1)] for x, y in loc]})
    for (x0, y0), (x1, y1) in zip(loc, loc[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for k in range(n + 1):
            x = x0 + (x1 - x0) * k / n; y = y0 + (y1 - y0) * k / n
            c, r = int(round(x + H)), int(round(H - y))
            if 0 <= c < 2 * H and 0 <= r < 2 * H:
                img[r, c] = (255, 0, 0)
for d in range(-6, 7):                                   # pin cross
    for (c, r) in ((H + d, H), (H, H + d)):
        img[r, c] = (0, 255, 255)
mem = gdal.GetDriverByName('MEM').Create('', 2 * H, 2 * H, 3, gdal.GDT_Byte)
for i in range(3):
    mem.GetRasterBand(i + 1).WriteArray(img[..., i])
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'overlay.png'), mem)
(HERE / 'roads.json').write_text(json.dumps({'pin': PIN, 'pin_local_m_from_area_centre': [px, py], 'roads': roads}, indent=1), encoding='utf-8')
print(len(roads), 'roads; pin local m', round(px, 1), round(py, 1))
