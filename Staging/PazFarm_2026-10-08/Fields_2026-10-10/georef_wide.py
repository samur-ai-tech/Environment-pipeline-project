"""Georeference Aviv's wide screenshot (plain satellite frame B) to metres east/north of the Paz Farm pin, by matching the
extracted Google road lines (road_mask.png + highway_mask.png) to every OSM highway in the 4 km source package
(distance-transform matching of a similarity transform: scale, rotation, shift). Start: the Google 'Paz Farm' marker
(B pixel ~807,318) = the pin. Writes WIDE_FIT.json and wide_fit_check.png (OSM lines drawn over the screenshot)."""
import json, math
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent; GEO = HERE.parent / 'Georef'; REF = HERE.parent / 'References/Wide_2026-10-10'
SRC = Path(r'C:\Users\USER\Documents\Pipeline Environment\SourceData\KarmeiYosef_31850349_34907601_4km')
OSM = next(SRC.glob('acquisitions/*/*/osm/overpass_response.json'))
REC = json.loads((HERE.parents[1] / 'NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/Zones/DATA_RECEIPT.json').read_text())
LAT0, LON0 = 31.850349, 34.907601
MLAT, MLON = REC['grid']['local_frame']['Mlat_m_per_deg'], REC['grid']['local_frame']['Mlon_m_per_deg']
pe, pn = json.loads((GEO / 'roads.json').read_text())['pin_local_m_from_area_centre']
en = lambda lon, lat: ((lon - LON0) * MLON - pe, (lat - LAT0) * MLAT - pn)
osm = json.loads(OSM.read_text(encoding='utf-8'))
nodes = {e['id']: en(e['lon'], e['lat']) for e in osm['elements'] if e['type'] == 'node'}
ways = [(e['tags']['highway'], [nodes[i] for i in e['nodes'] if i in nodes]) for e in osm['elements'] if e['type'] == 'way' and 'highway' in e.get('tags', {})]
HALF = 2600.0; N = int(2 * HALF)
ras = gdal.GetDriverByName('MEM').Create('', N, N, 1, gdal.GDT_Byte)
a = np.zeros((N, N), np.uint8)
for hw, pts in ways:
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(math.hypot(x1 - x0, y1 - y0)) + 2
        t = np.linspace(0, 1, n)
        c = ((x0 + (x1 - x0) * t) + HALF).astype(int); r = (HALF - (y0 + (y1 - y0) * t)).astype(int)
        ok = (c >= 0) & (c < N) & (r >= 0) & (r < N); a[r[ok], c[ok]] = 1
ras.GetBandRef = None
ras.GetRasterBand(1).WriteArray(a)
prox = gdal.GetDriverByName('MEM').Create('', N, N, 1, gdal.GDT_Float32)
gdal.ComputeProximity(ras.GetRasterBand(1), prox.GetRasterBand(1), ['VALUES=1', 'DISTUNITS=PIXEL', 'MAXDIST=60', 'NODATA=60'])
D = prox.GetRasterBand(1).ReadAsArray()
rm = gdal.Open(str(HERE / 'road_mask.png')).ReadAsArray() > 0
hm = gdal.Open(str(HERE / 'highway_mask.png')).ReadAsArray() > 0
ys, xs = np.nonzero(rm | hm)
rng = np.random.default_rng(1); k = rng.choice(len(xs), min(6000, len(xs)), replace=False)
px, py = xs[k].astype(np.float64), ys[k].astype(np.float64)
X0, Y0 = 807.0, 318.0                        # Google 'Paz Farm' marker tip in B pixels


def cost(s, th, te, tn, P=None):
    qx, qy = (px, py) if P is None else P
    dx, dy = qx - X0, -(qy - Y0)
    c, si = math.cos(th), math.sin(th)
    e = s * (c * dx - si * dy) + te; n = s * (si * dx + c * dy) + tn
    col = (e + HALF).astype(int); row = (HALF - n).astype(int)
    ok = (col >= 0) & (col < N) & (row >= 0) & (row < N)
    d = np.full(len(e), 60.0); d[ok] = D[row[ok], col[ok]]
    return float(np.minimum(d, 25.0).mean())


best = None
for s in np.arange(1.9, 2.8, 0.04):
    for thd in np.arange(-4, 4.01, 1.0):
        for te in np.arange(-100, 101, 20):
            for tn in np.arange(-100, 101, 20):
                cst = cost(s, math.radians(thd), te, tn)
                if best is None or cst < best[0]:
                    best = (cst, s, thd, te, tn)
print('coarse', best)
for step in ((0.01, 0.25, 5), (0.003, 0.08, 1.5), (0.001, 0.03, 0.5)):
    c0, s0, t0, e0, n0 = best
    for s in np.arange(s0 - 4 * step[0], s0 + 4.01 * step[0], step[0]):
        for thd in np.arange(t0 - 4 * step[1], t0 + 4.01 * step[1], step[1]):
            for te in np.arange(e0 - 4 * step[2], e0 + 4.01 * step[2], step[2]):
                for tn in np.arange(n0 - 4 * step[2], n0 + 4.01 * step[2], step[2]):
                    cst = cost(s, math.radians(thd), te, tn)
                    if cst < best[0]:
                        best = (cst, s, thd, te, tn)
    print('refined', best)
cst, s, thd, te, tn = best
allx, ally = xs.astype(np.float64), ys.astype(np.float64)
dx, dy = allx - X0, -(ally - Y0); c, si = math.cos(math.radians(thd)), math.sin(math.radians(thd))
e = s * (c * dx - si * dy) + te; n = s * (si * dx + c * dy) + tn
col = (e + HALF).astype(int); row = (HALF - n).astype(int); ok = (col >= 0) & (col < N) & (row >= 0) & (row < N)
dd = D[row[ok], col[ok]]
fit = {'model': 'e,n = s*R(theta)*[x-X0, -(y-Y0)] + [te,tn]; x,y = plain-screenshot pixels (right, down); e,n = metres east/north of the Paz Farm pin',
       'X0': X0, 'Y0': Y0, 'scale_m_per_px': s, 'theta_deg': thd, 'te': te, 'tn': tn, 'mean_trunc_dist_m': cst,
       'road_pixels_within_5m': round(float((dd <= 5).mean()), 3), 'within_10m': round(float((dd <= 10).mean()), 3),
       'image_size_px': [int(rm.shape[1]), int(rm.shape[0])], 'covers_m': [round(rm.shape[1] * s), round(rm.shape[0] * s)]}
(HERE / 'WIDE_FIT.json').write_text(json.dumps(fit, indent=1))
# check image: OSM ways drawn into the screenshot frame
bds = gdal.Open(str(REF / 'wide_satellite.webp')); B = np.stack([bds.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3)], -1)       # keep the dataset referenced
img = (B * 0.75).astype(np.uint8)
inv = lambda E, Nn: ((c * (E - te) + si * (Nn - tn)) / s + X0, Y0 - (-si * (E - te) + c * (Nn - tn)) / s)
for hw, pts in ways:
    col_ = (0, 255, 255) if hw in ('trunk', 'primary', 'trunk_link') else (0, 255, 0)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for t in np.linspace(0, 1, int(math.hypot(x1 - x0, y1 - y0) / max(s, 0.5)) + 2):
            u, v = inv(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            if 0 <= u < img.shape[1] and 0 <= v < img.shape[0]:
                img[int(v), int(u)] = col_
img[rm] = (img[rm] * 0.3 + np.array([255, 0, 0]) * 0.7).astype(np.uint8)
m = gdal.GetDriverByName('MEM').Create('', img.shape[1], img.shape[0], 3, gdal.GDT_Byte)
for i in range(3): m.GetRasterBand(i + 1).WriteArray(img[..., i])
gdal.GetDriverByName('PNG').CreateCopy(str(HERE / 'wide_fit_check.png'), m)
print(json.dumps(fit))
