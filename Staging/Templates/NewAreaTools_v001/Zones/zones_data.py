"""Zone source data for this area (playbook section 6). Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the El Wahat
fork of the Karmei Yosef script. Area id and size from ../Tools/area_constants.py (AREA_ID, HALF_EXTENT_M, ZONE_PX); the
Sentinel-2 search windows are inputs there too (S2_RECENT_START, S2_SPRING_WINDOW: season and hemisphere of the area).

No editor, no Houdini. Writes only SourceData/<AREA_ID>/zones/<stamp>/ and this Zones/ folder.
1. OpenStreetMap land use (landuse/natural/leisure areas) from Overpass -> .osm XML -> GDAL OSM driver multipolygons ->
   GeoJSON clipped to the area.
2. Sentinel-2 L2A (Copernicus, free and open) from the public AWS archive via the Earth Search STAC API (no login): the
   most recent clear scene (S2_RECENT_START .. today) and a clear green-season scene (S2_SPRING_WINDOW); only the area window is read from the cloud-optimized GeoTIFFs
   (/vsicurl/). Bands red/green/blue/nir + scene classification, warped to EPSG:4326 on a grid that covers the
   landscape (+-HALF_EXTENT_M around the area centre, ZONE_PX x ZONE_PX px = 4 m), which is linear in the pipeline's local frame.
Every network request is recorded in DATA_RECEIPT.json.
"""
import datetime
import importlib.util
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from osgeo import gdal, ogr

gdal.UseExceptions()
gdal.SetConfigOption('GDAL_DATA', 'C:/Users/USER/miniforge3/envs/gis/Library/share/gdal')
gdal.SetConfigOption('OSM_CONFIG_FILE', 'C:/Users/USER/miniforge3/envs/gis/Library/share/gdal/osmconf.ini')
TASK = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('area_constants', TASK.parent / 'Tools' / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (refuses if not filled in)
assert TASK.parent.name == A.TASK_FOLDER, (TASK.parent.name, A.TASK_FOLDER)
AREA = A.AREA_ID
PACKAGE = json.loads(Path(json.loads((TASK.parent / 'ACQUISITION_RECEIPT.json').read_text(encoding='utf-8'))['package_path']).read_text(encoding='utf-8'))
B = PACKAGE['area_bounds']
LON0, LAT0 = PACKAGE['origin']['lon0'], PACKAGE['origin']['lat0']
MLAT, MLON = PACKAGE['local_frame']['Mlat_m_per_deg'], PACKAGE['local_frame']['Mlon_m_per_deg']
HALF = A.HALF_EXTENT_M
GRID = {'west': LON0 - HALF / MLON, 'east': LON0 + HALF / MLON, 'south': LAT0 - HALF / MLAT, 'north': LAT0 + HALF / MLAT}
PX = A.ZONE_PX
UA = 'Environmentpipeline-GeoCity-Acquisition/1.0'
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
OUT = Path('C:/Users/USER/Documents/Pipeline Environment/SourceData') / AREA / 'zones' / stamp
OUT.mkdir(parents=True, exist_ok=False)
network = []
gdal.SetConfigOption('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR')
gdal.SetConfigOption('CPL_VSIL_CURL_ALLOWED_EXTENSIONS', '.tif')
gdal.SetConfigOption('GDAL_HTTP_USERAGENT', UA)


def http(url, data=None, headers=None, timeout=180):
    h = {'User-Agent': UA, **(headers or {})}
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=timeout) as r:
        body = r.read()
    network.append({'url': url, 'bytes': len(body), 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    return body


# 1. OpenStreetMap land use ---------------------------------------------------------------------------------------
bbox = '%.9f,%.9f,%.9f,%.9f' % (GRID['south'], GRID['west'], GRID['north'], GRID['east'])
query = ('[out:xml][timeout:120];(' + ''.join('%s["%s"](%s);' % (t, k, bbox) for t in ('way', 'relation')
         for k in ('landuse', 'natural', 'leisure')) + ');(._;>;);out body;')
osm = None
# Reuse a land-use download made earlier today by this script (Overpass is often busy).
previous = sorted(p for p in OUT.parent.glob('*/landuse.osm') if p.parent != OUT and p.stat().st_size > 1000)
if previous and (previous[-1].parent / 'landuse.overpassql').read_text(encoding='utf-8') == query:
    osm = previous[-1].read_bytes()
    network.append({'reused': str(previous[-1])})
for round_index in range(0 if osm else 4):
    for endpoint in ('https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter',
                     'https://overpass.private.coffee/api/interpreter'):
        try:
            osm = http(endpoint, urllib.parse.urlencode({'data': query}).encode(), {'Content-Type': 'application/x-www-form-urlencoded'})
            if b'<osm' in osm[:400]:
                break
            osm = None
        except Exception as exc:
            network.append({'url': endpoint, 'error': repr(exc)[:200]})
            osm = None
    if osm:
        break
    print(json.dumps({'phase': 'overpass_busy_retry', 'round': round_index + 1}), flush=True)
    time.sleep(90)
assert osm, 'all Overpass endpoints failed'
(OUT / 'landuse.overpassql').write_text(query, encoding='utf-8')
(OUT / 'landuse.osm').write_bytes(osm)
clip = ogr.CreateGeometryFromWkt('POLYGON((%f %f,%f %f,%f %f,%f %f,%f %f))' % (
    GRID['west'], GRID['south'], GRID['east'], GRID['south'], GRID['east'], GRID['north'], GRID['west'], GRID['north'], GRID['west'], GRID['south']))
src = gdal.OpenEx(str(OUT / 'landuse.osm'), gdal.OF_VECTOR)
layer = src.GetLayerByName('multipolygons')
features = []
for f in layer:
    g = f.GetGeometryRef()
    if g is None:
        continue
    kind = None
    for key in ('landuse', 'natural', 'leisure'):
        idx = f.GetFieldIndex(key)
        if idx >= 0 and f.GetField(idx):
            kind = '%s=%s' % (key, f.GetField(idx))
            break
    if not kind:
        continue
    clipped = g.Intersection(clip)
    if clipped is None or clipped.IsEmpty():
        continue
    other = f.GetField(f.GetFieldIndex('other_tags')) if f.GetFieldIndex('other_tags') >= 0 else None
    features.append({'type': 'Feature', 'properties': {'kind': kind, 'osm_id': f.GetField('osm_id') or f.GetField('osm_way_id'),
                     'other_tags': other}, 'geometry': json.loads(clipped.ExportToJson())})
(OUT / 'landuse.geojson').write_text(json.dumps({'type': 'FeatureCollection', 'features': features}), encoding='utf-8')
kinds = {}
for feat in features:
    kinds[feat['properties']['kind']] = kinds.get(feat['properties']['kind'], 0) + 1

# 2. Sentinel-2 L2A from the public AWS archive ---------------------------------------------------------------------
STAC = 'https://earth-search.aws.element84.com/v1/search'


def search(start, end, max_cloud):
    body = {'collections': ['sentinel-2-l2a'], 'bbox': [GRID['west'], GRID['south'], GRID['east'], GRID['north']],
            'datetime': '%s/%s' % (start, end), 'limit': 50, 'query': {'eo:cloud_cover': {'lt': max_cloud}},
            'sortby': [{'field': 'properties.datetime', 'direction': 'desc'}]}
    res = json.loads(http(STAC, json.dumps(body).encode(), {'Content-Type': 'application/json'}))
    items = []
    for it in res.get('features', []):
        bb = it.get('bbox') or [0, 0, 0, 0]
        if bb[0] <= GRID['west'] and bb[1] <= GRID['south'] and bb[2] >= GRID['east'] and bb[3] >= GRID['north']:
            items.append(it)
    return items


def window(item, label):
    assets = item['assets']
    keys = {'red': 'red', 'green': 'green', 'blue': 'blue', 'nir': 'nir', 'scl': 'scl'}
    arrays = {}
    for name, key in keys.items():
        href = assets[key]['href']
        if href.startswith('s3://'):
            href = 'https://%s.s3.amazonaws.com/%s' % tuple(href[5:].split('/', 1))
        ds = gdal.Warp('', '/vsicurl/' + href, format='MEM', dstSRS='EPSG:4326',
                       outputBounds=(GRID['west'], GRID['south'], GRID['east'], GRID['north']), width=PX, height=PX,
                       resampleAlg='near' if name == 'scl' else 'bilinear')
        arrays[name] = ds.GetRasterBand(1).ReadAsArray().astype(np.float32)
        network.append({'url': href, 'read': 'window via /vsicurl/', 'asset': name})
        ds = None
    stack = np.stack([arrays[k] for k in ('red', 'green', 'blue', 'nir', 'scl')])
    drv = gdal.GetDriverByName('GTiff')
    path = OUT / ('S2_%s_%s.tif' % (label, item['properties']['datetime'][:10]))
    out = drv.Create(str(path), PX, PX, 5, gdal.GDT_Float32, options=['COMPRESS=DEFLATE'])
    out.SetGeoTransform((GRID['west'], (GRID['east'] - GRID['west']) / PX, 0, GRID['north'], 0, -(GRID['north'] - GRID['south']) / PX))
    out.SetProjection('EPSG:4326')
    for i, name in enumerate(('red', 'green', 'blue', 'nir', 'scl')):
        out.GetRasterBand(i + 1).WriteArray(stack[i]); out.GetRasterBand(i + 1).SetDescription(name)
    out = None
    scl = arrays['scl']
    cloudy = float(np.isin(scl, (3, 8, 9, 10)).mean())
    rgb = np.stack([arrays['red'], arrays['green'], arrays['blue']], -1)
    preview = np.clip(rgb / 2500.0 * 255.0, 0, 255).astype(np.uint8)
    png = drv.Create(str(path.with_suffix('.preview.tif')), PX, PX, 3, gdal.GDT_Byte)
    for i in range(3):
        png.GetRasterBand(i + 1).WriteArray(preview[..., i])
    png = None
    gdal.Translate(str(path.with_suffix('.png')), str(path.with_suffix('.preview.tif')), format='PNG')
    return {'item': item['id'], 'datetime': item['properties']['datetime'], 'cloud_cover_tile': item['properties'].get('eo:cloud_cover'),
            'cloud_or_shadow_fraction_in_area': round(cloudy, 4), 'file': str(path), 'preview_png': str(path.with_suffix('.png'))}


today = datetime.datetime.now(datetime.timezone.utc).date()             # the run date (template fix)
scenes = {}
recent = search(A.S2_RECENT_START, today.isoformat() + 'T23:59:59Z', 5)
spring = search(A.S2_SPRING_WINDOW[0], A.S2_SPRING_WINDOW[1], 5)
for label, items in (('recent', recent), ('spring', spring)):
    for it in items:
        info = window(it, label)
        if info['cloud_or_shadow_fraction_in_area'] < 0.01:
            scenes[label] = info
            break
        scenes.setdefault(label + '_rejected', []).append(info)

receipt = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'area_id': AREA, 'output_dir': str(OUT),
           'grid': {'bounds_epsg4326': GRID, 'pixels': PX, 'metres_per_pixel': 2 * HALF / PX, 'centre': [LON0, LAT0],
                    'local_frame': {'Mlat_m_per_deg': MLAT, 'Mlon_m_per_deg': MLON}},
           'osm': {'features_in_area': len(features), 'by_kind': kinds, 'license': 'ODbL 1.0, OpenStreetMap contributors'},
           'sentinel2': scenes, 'sentinel2_license': 'Copernicus Sentinel data, free and open (Copernicus legal notice); via AWS Open Data / Earth Search',
           'candidates': {'recent': len(recent), 'spring': len(spring)}, 'network': network}
(TASK / 'DATA_RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps({k: receipt[k] for k in ('output_dir', 'osm', 'sentinel2', 'candidates')}, indent=2))
