"""Retained 4 km geographic package using the existing acquisition implementation.

Same method as the Lebanon 4 km wrapper (NewArea_33390778_35506639_4km_2026-10-06/acquire_area.py):
the shared acquire.py is imported unchanged; only its 1008 m size limit and DSM margin
are widened for a 4033-sample, 1 m terrain grid (same as Lebanon 4 km). Only this task's staging and its new
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
AREA = 'KarmeiYosef_31850349_34907601_4km'
LAT = 31.850349
LON = 34.907601
HALF = 2000.0          # requested area: 4000 m square
GRID_HALF = 2016.0     # HDA terrain grid: 4033 samples at 1 m = 4032 m
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
        raise acq.IntakeError('New area exceeds the 4033-sample, 1 m grid')
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
           'extent_m': [4000, 4000], 'terrain_grid_samples': 4033, 'terrain_grid_spacing_m': 1,
           'base_acquisition_sha256': acq.sha256(BASE), 'native_operations': False}
acq.write_json(TASK / 'REQUEST.json', REQUEST)
print(json.dumps({'phase': 'request_prepared', **REQUEST}), flush=True)

try:
    # The GLO-30 tile for this degree square is already in the shared read-only
    # cache (used for Gaza). Copy it into this task's cache; tile_for re-verifies
    # SHA-256, URL, version and coverage before use and downloads only if invalid.
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
