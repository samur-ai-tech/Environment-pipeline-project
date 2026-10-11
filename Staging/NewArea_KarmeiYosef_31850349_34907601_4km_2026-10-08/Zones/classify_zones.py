"""Zone map for the Karmei Yosef 4 km area from DATA_RECEIPT.json inputs (OpenStreetMap land use + Sentinel-2).

Grid: the same 1009 x 1009 EPSG:4326 grid as the Sentinel windows (4 m, +-2016 m around the area centre = the landscape).
Rule order (first match wins):
  1. OSM polygons: water, built (residential/industrial), forest (forest/wood), orchard, vineyard, scrub,
     grass (meadow/park/pitch/playground/sports). OSM 'farmland' only marks a field; its crop state comes from the satellite.
  2. Satellite, 21 Sep 2026 (now) and 4 Apr 2026 (spring), NDVI = (nir - red) / (nir + red):
     bright, not green (greenhouses, nets, chalk)  -> bright
     NDVI_sep > 0.45                               -> green_crop (irrigated summer crops)
     NDVI_sep 0.25..0.45 and NDVI_apr > 0.45       -> trees_scrub (perennial woody cover)
     NDVI_sep < 0.22                               -> bare_field (ploughed or stubble)
     otherwise                                      -> dry_grass
Writes ZONES.tif, LEGEND.json (code, name, source, pixel share, mean real colour now and in spring) and ZONES_preview.png
(satellite | zones side by side) into the SourceData zones folder and copies the legend and preview here.
"""
import json
import shutil
from pathlib import Path

import numpy as np
from osgeo import gdal, ogr

gdal.UseExceptions()
TASK = Path(__file__).resolve().parent
R = json.loads((TASK / 'DATA_RECEIPT.json').read_text(encoding='utf-8'))
OUT = Path(R['output_dir'])
G = R['grid']['bounds_epsg4326']
PX = R['grid']['pixels']
GT = (G['west'], (G['east'] - G['west']) / PX, 0, G['north'], 0, -(G['north'] - G['south']) / PX)


def bands(path):
    ds = gdal.Open(path)
    a = {ds.GetRasterBand(i + 1).GetDescription(): ds.GetRasterBand(i + 1).ReadAsArray().astype(np.float32) for i in range(ds.RasterCount)}
    return a


now = bands(R['sentinel2']['recent']['file'])
spr = bands(R['sentinel2']['spring']['file'])
ndvi = lambda b: (b['nir'] - b['red']) / np.maximum(b['nir'] + b['red'], 1.0)
nd_now, nd_spr = ndvi(now), ndvi(spr)
bright_now = (now['red'] + now['green'] + now['blue']) / 3.0

CLASSES = [  # code, name, preview colour
    (1, 'water', (40, 90, 200)), (2, 'built', (150, 150, 150)), (3, 'forest', (20, 90, 30)), (4, 'orchard', (90, 160, 60)),
    (5, 'vineyard', (140, 60, 140)), (6, 'scrub', (120, 120, 50)), (7, 'grass', (150, 200, 90)),
    (8, 'bright', (235, 235, 225)), (9, 'green_crop', (60, 200, 60)), (10, 'trees_scrub', (70, 120, 60)),
    (11, 'bare_field', (170, 110, 60)), (12, 'dry_grass', (210, 190, 120))]
OSM_RULES = [  # priority order (later rasterization overwrites earlier, so list lowest first)
    ('grass', ('landuse=meadow', 'leisure=park', 'leisure=pitch', 'leisure=playground', 'leisure=sports_centre', 'landuse=grass')),
    ('scrub', ('natural=scrub', 'natural=heath')), ('vineyard', ('landuse=vineyard',)), ('orchard', ('landuse=orchard',)),
    ('forest', ('landuse=forest', 'natural=wood')), ('built', ('landuse=residential', 'landuse=industrial', 'landuse=commercial', 'leisure=swimming_pool')),
    ('water', ('natural=water', 'landuse=reservoir', 'landuse=basin'))]
code = {name: c for c, name, _ in CLASSES}

zones = np.zeros((PX, PX), np.uint8)
farmland = np.zeros((PX, PX), np.uint8)
src = ogr.Open(str(OUT / 'landuse.geojson'))
layer = src.GetLayer()


def rasterize(kinds):
    mem = gdal.GetDriverByName('MEM').Create('', PX, PX, 1, gdal.GDT_Byte)
    mem.SetGeoTransform(GT); mem.SetProjection('EPSG:4326')
    layer.SetAttributeFilter(' OR '.join("kind = '%s'" % k for k in kinds))
    gdal.RasterizeLayer(mem, [1], layer, burn_values=[1], options=['ALL_TOUCHED=FALSE'])
    layer.SetAttributeFilter(None)
    return mem.GetRasterBand(1).ReadAsArray().astype(bool)


farmland = rasterize(('landuse=farmland',))
osm_mask = np.zeros((PX, PX), bool)
for name, kinds in OSM_RULES:
    m = rasterize(kinds)
    zones[m] = code[name]
    osm_mask |= m

sat = ~osm_mask
rules = [('bright', (bright_now > 2600) & (nd_now < 0.25)),
         ('green_crop', nd_now > 0.45),
         ('trees_scrub', (nd_now >= 0.25) & (nd_now <= 0.45) & (nd_spr > 0.45)),
         ('bare_field', nd_now < 0.22)]
assigned = np.zeros((PX, PX), bool)
for name, m in rules:
    sel = sat & m & ~assigned
    zones[sel] = code[name]
    assigned |= sel
zones[sat & ~assigned] = code['dry_grass']
assert (zones > 0).all()

drv = gdal.GetDriverByName('GTiff')
z = drv.Create(str(OUT / 'ZONES.tif'), PX, PX, 1, gdal.GDT_Byte, options=['COMPRESS=DEFLATE'])
z.SetGeoTransform(GT); z.SetProjection('EPSG:4326'); z.GetRasterBand(1).WriteArray(zones); z = None
legend = []
for c, name, colour in CLASSES:
    m = zones == c
    if not m.any():
        legend.append({'code': c, 'name': name, 'share': 0.0}); continue
    mean = lambda b: [int(round(float(b[k][m].mean()))) for k in ('red', 'green', 'blue')]
    legend.append({'code': c, 'name': name, 'share': round(float(m.mean()), 4), 'preview_colour': colour,
                   'source': 'OpenStreetMap' if name in dict(OSM_RULES) else 'Sentinel-2',
                   'on_osm_farmland_share': round(float((m & farmland).sum() / max(m.sum(), 1)), 3),
                   'mean_reflectance_rgb_now': mean(now), 'mean_reflectance_rgb_spring': mean(spr),
                   'mean_srgb_now': [int(min(255, v / 2500 * 255)) for v in mean(now)],
                   'mean_ndvi_now': round(float(nd_now[m].mean()), 3), 'mean_ndvi_spring': round(float(nd_spr[m].mean()), 3)})
(OUT / 'LEGEND.json').write_text(json.dumps({'grid': R['grid'], 'classes': legend, 'rules': __doc__}, indent=2), encoding='utf-8')
pal = np.zeros((PX, PX, 3), np.uint8)
for c, _, colour in CLASSES:
    pal[zones == c] = colour
satimg = np.clip(np.stack([now['red'], now['green'], now['blue']], -1) / 2500 * 255, 0, 255).astype(np.uint8)
side = np.concatenate([satimg, np.full((PX, 12, 3), 255, np.uint8), pal], axis=1)
p = drv.Create(str(OUT / 'ZONES_preview.tif'), side.shape[1], side.shape[0], 3, gdal.GDT_Byte)
for i in range(3):
    p.GetRasterBand(i + 1).WriteArray(side[..., i])
p = None
gdal.Translate(str(OUT / 'ZONES_preview.png'), str(OUT / 'ZONES_preview.tif'), format='PNG')
for name in ('LEGEND.json', 'ZONES_preview.png'):
    shutil.copy2(OUT / name, TASK / name)
print(json.dumps([{k: x.get(k) for k in ('code', 'name', 'share', 'source', 'mean_srgb_now', 'mean_ndvi_now', 'mean_ndvi_spring')} for x in legend], indent=1))
