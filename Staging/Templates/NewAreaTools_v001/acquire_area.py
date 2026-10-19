"""Retained geographic package using the existing acquisition implementation. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69).
Area id, centre and size come from Tools/area_constants.py (AREA_ID, LAT, LON, REQUEST_HALF_M, HALF_EXTENT_M, GRID_SAMPLES).

Same method as the Lebanon 4 km wrapper (NewArea_33390778_35506639_4km_2026-10-06/acquire_area.py):
the shared acquire.py is imported unchanged; only its 1008 m size limit and DSM margin
are widened for the area's GRID_SAMPLES 1 m terrain grid (same as Lebanon 4 km for 4033 samples). Only this task's staging and its new
geographic source directory are written. No Houdini Cook, Unreal operation, shared
cache index change or source hot reload.
"""
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys
import time

sys.dont_write_bytecode = True
TASK = Path(__file__).resolve().parent
BASE = Path('C:/Users/USER/Documents/Pipeline Environment/SourceData/Acquisition/acquire.py')
SOURCE = Path('C:/Users/USER/Documents/Pipeline Environment/SourceData')
_spec = importlib.util.spec_from_file_location('area_constants', TASK / 'Tools' / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (refuses if not filled in)
assert TASK.name == A.TASK_FOLDER, (TASK.name, A.TASK_FOLDER)
AREA = A.AREA_ID
LAT = A.LAT
LON = A.LON
HALF = A.REQUEST_HALF_M          # requested area: 2 * HALF m square (4000 m for 4 km)
GRID_HALF = A.HALF_EXTENT_M      # HDA terrain grid: GRID_SAMPLES at 1 m = 2 * GRID_HALF m (4033 / 4032 m for 4 km)
spec = importlib.util.spec_from_file_location('existing_geocity_acquisition', BASE)
acq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acq)
acq.HERE = TASK / 'AcquisitionCache'
acq.ROOT = SOURCE
acq.HERE.mkdir(exist_ok=True)
NETWORK = []
# 2026-10-08 attempt 1: overpass-api.de 504 twice, kumi 500, and overpass.maprva.org
# answered with ways in Sweden (regional mirror; rejected by the shared validator as
# incomplete geometry). Use only full-planet instances for this task; the shared list
# in acquire.py is not changed.
acq.ENDPOINTS = ('https://overpass-api.de/api/interpreter',
                 'https://overpass.kumi.systems/api/interpreter',
                 'https://overpass.private.coffee/api/interpreter')
_fetch_osm = acq.fetch_osm


def fetch_osm_with_rounds(query, record):
    for round_index in range(3):
        try:
            return _fetch_osm(query, record)
        except acq.IntakeError:
            if round_index == 2:
                raise
            print(json.dumps({'phase': 'overpass_busy_retry', 'round': round_index + 1}), flush=True)
            time.sleep(90)


acq.fetch_osm = fetch_osm_with_rounds


def normalize(values):
    w, s, e, n = map(float, values)
    if not all(math.isfinite(v) for v in (w, s, e, n)) or not (-180 <= w < e <= 180 and -85 <= s < n <= 85):
        raise acq.IntakeError('Invalid WGS84 bounds')
    mlat, mlon = acq.frame_factors((s + n) / 2)
    if max((e - w) * mlon, (n - s) * mlat) > 2 * GRID_HALF + 0.001:
        raise acq.IntakeError('New area exceeds the %d-sample, 1 m grid' % A.GRID_SAMPLES)
    return dict(zip(acq.BOUNDS_KEYS, (w, s, e, n)))


def raster_bounds(bounds):
    lat0 = (bounds['south'] + bounds['north']) / 2
    lon0 = (bounds['west'] + bounds['east']) / 2
    mlat, mlon = acq.frame_factors(lat0)
    return {'west': min(bounds['west'], lon0 - GRID_HALF / mlon),
            'east': max(bounds['east'], lon0 + GRID_HALF / mlon),
            'south': min(bounds['south'], lat0 - GRID_HALF / mlat),
            'north': max(bounds['north'], lat0 + GRID_HALF / mlat)}


acq.normalize_bounds = normalize
acq.required_raster_bounds = raster_bounds
mlat, mlon = acq.frame_factors(LAT)
BOUNDS = normalize([LON - HALF / mlon, LAT - HALF / mlat, LON + HALF / mlon, LAT + HALF / mlat])
REQUEST = {'area_id': AREA, 'center': {'lat': LAT, 'lon': LON}, 'bounds': BOUNDS,
           'extent_m': [int(2 * HALF), int(2 * HALF)], 'terrain_grid_samples': A.GRID_SAMPLES, 'terrain_grid_spacing_m': 1,
           'base_acquisition_sha256': acq.sha256(BASE), 'native_operations': False}
acq.write_json(TASK / 'REQUEST.json', REQUEST)
print(json.dumps({'phase': 'request_prepared', **REQUEST}), flush=True)

try:
    # When the GLO-30 tile is NOT in the shared read-only cache, this copy is a no-op and tile_for
    # downloads it from the public Copernicus S3 bucket into this task's AcquisitionCache/tile_cache
    # (shared cache and index untouched).
    name = acq.tile_name(math.floor(LON), math.floor(LAT))
    shared = SOURCE / 'Acquisition' / 'tile_cache'
    cache = acq.HERE / 'tile_cache'
    cache.mkdir(exist_ok=True)
    for suffix in ('.tif', '.json'):
        if (shared / (name + suffix)).is_file() and not (cache / (name + suffix)).exists():
            shutil.copy2(shared / (name + suffix), cache / (name + suffix))
    print(json.dumps({'phase': 'acquiring', 'elevation_source': 'GLO-30', 'tile': name, 'bounds': BOUNDS}), flush=True)
    key, identity = acq.identity(AREA, BOUNDS, 'live')
    package_path = acq.create_live_package(AREA, BOUNDS, key, False, NETWORK)
    validation = acq.validate_package(package_path, AREA, BOUNDS, accepted=False)
    receipt = {'status': 'SOURCE_PACKAGE_VALIDATED', 'completed_utc': acq.now(),
               'request': REQUEST, 'identity': identity, 'package_path': str(package_path),
               'validation': validation, 'elevation_source': 'GLO-30', 'network': NETWORK,
               'coverage_limit': acq.OSM_COVERAGE_LIMIT, 'houdini_cooked': False,
               'native_imported': False, 'area_generated': False}
    acq.write_json(TASK / 'ACQUISITION_RECEIPT.json', receipt)
    print(json.dumps({'status': receipt['status'], 'package_path': receipt['package_path'],
                      'osm': validation['osm'], 'dsm_min_max_m': [validation['dsm']['min_m'], validation['dsm']['max_m']],
                      'network': NETWORK}), flush=True)
except Exception as exc:
    acq.write_json(TASK / 'ACQUISITION_FAILURE.json', {'utc': acq.now(), 'error': repr(exc), 'network': NETWORK, 'request': REQUEST})
    raise
