"""Step 2 of 'every field from the screenshot' (Aviv 2026-10-10): fields = regions of one look, cut by roads.
Input: clusters.tif (fields_cluster.py), the extracted road lines (road_mask.png, highway_mask.png), every OSM highway, the
4 km zones (village/forest/water are left to the existing zone vegetation), WIDE_FIT.json (pixels -> metres from the pin).
  1. clusters -> field types (named from the cluster centres, CLUSTERS.json)
  2. 13 x 13 majority filter (26 m), roads as barriers, GDAL sieve (< 800 px = 3,300 m2 merged into neighbours)
  3. polygons (GDAL Polygonize), per field: type, area, row direction (structure tensor of the brightness inside the field)
Outputs: FIELDS_V1.json (fields in metres from the pin), fields_v1.tif (field ids, screenshot frame), fields_v1_preview.png
Uses only the picture's appearance; no screenshot pixels are copied into any asset.
"""
import json, math
from pathlib import Path
import numpy as np
from osgeo import gdal, ogr
gdal.UseExceptions(); ogr.UseExceptions()
HERE = Path(__file__).resolve().parent; GEO = HERE.parent / 'Georef'; REF = HERE.parent / 'References/Wide_2026-10-10'
SRC = Path(r'C:\Users\USER\Documents\Pipeline Environment\SourceData\KarmeiYosef_31850349_34907601_4km')
TASK4 = HERE.parents[1] / 'NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
FIT = json.loads((HERE / 'WIDE_FIT.json').read_text())
REC = json.loads((TASK4 / 'Zones/DATA_RECEIPT.json').read_text())
LAT0, LON0 = 31.850349, 34.907601
MLAT, MLON = REC['grid']['local_frame']['Mlat_m_per_deg'], REC['grid']['local_frame']['Mlon_m_per_deg']
pe, pn = json.loads((GEO / 'roads.json').read_text())['pin_local_m_from_area_centre']
s, th, te, tn, X0, Y0 = FIT['scale_m_per_px'], math.radians(FIT['theta_deg']), FIT['te'], FIT['tn'], FIT['X0'], FIT['Y0']
c_, s_ = math.cos(th), math.sin(th)
px2m = lambda x, y: (s * (c_ * (x - X0) - s_ * (-(y - Y0))) + te, s * (s_ * (x - X0) + c_ * (-(y - Y0))) + tn)
m2px = lambda e, n: ((c_ * (e - te) + s_ * (n - tn)) / s + X0, Y0 - (-s_ * (e - te) + c_ * (n - tn)) / s)
TYPES = {1: 'orchard', 2: 'rows', 3: 'green_crop', 4: 'ploughed', 5: 'bare', 6: 'light', 7: 'structures', 8: 'natural'}
CL2T = {2: 1, 1: 1, 11: 2, 9: 3, 4: 3, 8: 4, 5: 5, 7: 5, 6: 6, 0: 7, 3: 7, 10: 8}
cds = gdal.Open(str(HERE / 'clusters.tif')); cl = cds.GetRasterBand(1).ReadAsArray(); H, W = cl.shape
t = np.zeros_like(cl)
for k, v in CL2T.items():
    t[cl == k] = v


def box(a, r):
    c = np.pad(a.astype(np.float32), ((r + 1, r), (r + 1, r)), mode='edge').cumsum(0).cumsum(1)
    return c[2 * r + 1:, 2 * r + 1:] - c[:-2 * r - 1, 2 * r + 1:] - c[2 * r + 1:, :-2 * r - 1] + c[:-2 * r - 1, :-2 * r - 1]


votes = np.stack([box(t == k, 6) for k in range(1, 9)], -1)          # 13 x 13 px (26 m) majority
t = (votes.argmax(-1) + 1).astype(np.uint8)
# barriers: extracted roads (+1 px), every OSM highway, road 44 strip; village / forest / water zones
bar = (gdal.Open(str(HERE / 'road_mask.png')).ReadAsArray() > 0) | (gdal.Open(str(HERE / 'highway_mask.png')).ReadAsArray() > 0)
bar = box(bar, 1) > 0
OSM = next(SRC.glob('acquisitions/*/*/osm/overpass_response.json'))
osm = json.loads(OSM.read_text(encoding='utf-8'))
en = lambda lon, lat: ((lon - LON0) * MLON - pe, (lat - LAT0) * MLAT - pn)
nodes = {e['id']: en(e['lon'], e['lat']) for e in osm['elements'] if e['type'] == 'node'}
for e in osm['elements']:
    if e['type'] != 'way' or 'highway' not in e.get('tags', {}):
        continue
    w = 4 if e['tags']['highway'] in ('trunk', 'primary', 'trunk_link') else 1
    pts = [m2px(*nodes[i]) for i in e['nodes'] if i in nodes]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(math.hypot(x1 - x0, y1 - y0) * 2) + 2
        for tt in np.linspace(0, 1, n):
            x, y = int(x0 + (x1 - x0) * tt), int(y0 + (y1 - y0) * tt)
            if not (0 <= x < W and 0 <= y < H):
                continue                                       # off-picture (negative indices would wrap)
            bar[max(0, y - w // 2):y + w // 2 + 1, max(0, x - w // 2):x + w // 2 + 1] = True
zd = gdal.Open(str(Path(REC['output_dir']) / 'ZONES.tif')); zgt = zd.GetGeoTransform(); z = zd.GetRasterBand(1).ReadAsArray()
yy, xx = np.mgrid[0:H, 0:W]
E = s * (c_ * (xx - X0) - s_ * (-(yy - Y0))) + te; Nn = s * (s_ * (xx - X0) + c_ * (-(yy - Y0))) + tn
lon = LON0 + (E + pe) / MLON; lat = LAT0 + (Nn + pn) / MLAT
zone = z[np.clip(((lat - zgt[3]) / zgt[5]).astype(int), 0, z.shape[0] - 1), np.clip(((lon - zgt[0]) / zgt[1]).astype(int), 0, z.shape[1] - 1)]
outside = (np.abs(E + pe) > 2000) | (np.abs(Nn + pn) > 2000)          # beyond the 4 km landscape
excluded = np.isin(zone, (1, 2, 3)) | outside
t[bar] = 0; t[excluded] = 0
mem = gdal.GetDriverByName('MEM').Create('', W, H, 1, gdal.GDT_Byte); mem.GetRasterBand(1).WriteArray(t)
mem.GetRasterBand(1).SetNoDataValue(0)
gdal.SieveFilter(mem.GetRasterBand(1), mem.GetRasterBand(1), mem.GetRasterBand(1), 800, 4)
t = mem.GetRasterBand(1).ReadAsArray(); t[bar | excluded] = 0
mem.GetRasterBand(1).WriteArray(t)
drv = ogr.GetDriverByName('MEM'); ds = drv.CreateDataSource('f'); lyr = ds.CreateLayer('fields', geom_type=ogr.wkbPolygon)
lyr.CreateField(ogr.FieldDefn('t', ogr.OFTInteger))
gdal.Polygonize(mem.GetRasterBand(1), mem.GetRasterBand(1), lyr, 0, ['8CONNECTED=4'])
ids = gdal.GetDriverByName('GTiff').Create(str(HERE / 'fields_v1.tif'), W, H, 1, gdal.GDT_Int32)
ids.SetGeoTransform((0, 1, 0, 0, 0, 1))
# brightness gradients for the row direction
bds = gdal.Open(str(REF / 'wide_satellite.webp')); Lm = np.stack([bds.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3)], -1).astype(np.float32).mean(-1)
gy, gx = np.gradient(Lm)
fields = []
lyr.ResetReading()
fid_ras = np.zeros((H, W), np.int32)
tmp = gdal.GetDriverByName('MEM').Create('', W, H, 1, gdal.GDT_Int32); tmp.SetGeoTransform((0, 1, 0, 0, 0, 1))
mds = drv.CreateDataSource('g'); ml = mds.CreateLayer('g', geom_type=ogr.wkbPolygon); ml.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))
k = 0
for f in lyr:
    g = f.GetGeometryRef(); typ = f.GetField('t')
    area_px = g.GetArea()
    if typ == 0 or area_px < 800:
        continue
    k += 1
    nf = ogr.Feature(ml.GetLayerDefn()); nf.SetField('id', k); nf.SetGeometry(g.Clone()); ml.CreateFeature(nf)
    simp = g.SimplifyPreserveTopology(1.5)
    ring = simp.GetGeometryRef(0)
    pts = [px2m(ring.GetX(i), ring.GetY(i)) for i in range(ring.GetPointCount())]
    fields.append({'id': k, 'type': TYPES[typ], 'area_m2': round(area_px * s * s), 'polygon_m': [[round(a, 2), round(b, 2)] for a, b in pts],
                   'holes': g.GetGeometryCount() - 1})
gdal.RasterizeLayer(tmp, [1], ml, options=['ATTRIBUTE=id'])
fid_ras = tmp.GetRasterBand(1).ReadAsArray()
ids.GetRasterBand(1).WriteArray(fid_ras); ids = None
# row direction per field from the structure tensor (gradient across the rows -> rows run perpendicular)
Jxx, Jyy, Jxy = gx * gx, gy * gy, gx * gy
cnt = np.bincount(fid_ras.ravel(), minlength=k + 1)
sxx = np.bincount(fid_ras.ravel(), Jxx.ravel(), k + 1); syy = np.bincount(fid_ras.ravel(), Jyy.ravel(), k + 1); sxy = np.bincount(fid_ras.ravel(), Jxy.ravel(), k + 1)
for f in fields:
    i = f['id']
    a, b, c = sxx[i], syy[i], sxy[i]
    ang = 0.5 * math.atan2(2 * c, a - b)                      # dominant gradient angle in image axes (y down)
    coh = math.sqrt((a - b) ** 2 + 4 * c * c) / (a + b + 1e-9)
    grad_deg_east = math.degrees(-ang)                         # image y down -> north up
    f['row_deg_from_east'] = round((grad_deg_east + 90.0) % 180.0, 1)
    f['row_coherence'] = round(coh, 3)
TYPE_COL = {'orchard': (20, 110, 30), 'rows': (150, 200, 60), 'green_crop': (80, 230, 80), 'ploughed': (120, 70, 40),
            'bare': (205, 150, 110), 'light': (240, 225, 200), 'structures': (90, 140, 255), 'natural': (60, 160, 140)}
img = (np.stack([bds.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3)], -1) * 0.35).astype(np.float32)
lut = np.zeros((k + 1, 3), np.float32)
for f in fields:
    lut[f['id']] = TYPE_COL[f['type']]
a = (fid_ras > 0)[..., None]
img = img * (1 - 0.65 * a) + lut[fid_ras] * 0.65 * a
edge = (fid_ras != np.roll(fid_ras, 1, 0)) | (fid_ras != np.roll(fid_ras, 1, 1))
img[edge & (fid_ras > 0)] = (255, 255, 255)
pm = gdal.GetDriverByName('MEM').Create('', W, H, 3, gdal.GDT_Byte)
for i in range(3): pm.GetRasterBand(i + 1).WriteArray(np.clip(img[..., i], 0, 255).astype(np.uint8))
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'fields_v1_preview.png'), pm)
from collections import Counter
summ = {tp: {'fields': sum(1 for f in fields if f['type'] == tp), 'ha': round(sum(f['area_m2'] for f in fields if f['type'] == tp) / 1e4, 1)} for tp in TYPES.values()}
json.dump({'method': __doc__.strip(), 'fit': 'WIDE_FIT.json', 'cluster_to_type': {str(k): TYPES[v] for k, v in CL2T.items()},
           'summary': summ, 'fields': fields}, open(HERE / 'FIELDS_V1.json', 'w'))
print(len(fields), json.dumps(summ))
