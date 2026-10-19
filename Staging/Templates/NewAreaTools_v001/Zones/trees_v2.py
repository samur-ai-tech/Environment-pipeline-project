"""More trees on the PCG clone, offline part (playbook 7.3). Template v001 (NewAreaTools_v001; maintained by the agent Aviv
assigns, GOVERNANCE_RECORD.md RC-69); from the Karmei Yosef trees_v2.py (Aviv approved: satellite tree map, denser forest and
scrub ~2-3x + single field trees) with the Paz Farm parts removed (RG4 #4): no hero-site parcel or field clearing and no
windbreak rows (those read a site's pin, fence, parcels and crops; a site keeps them in its own folder).
1024 x 1024 masks in the T_<AREA_SHORT>_Zones orientation (row 0 = north edge, 2 x HALF_EXTENT_M square) for the zone PCG
graph v002 (Tools/trees_pcg.py); building footprints (Buildings_v2/FOOTPRINTS.json from compact_buildings_v2.py) + ~5 m
are kept free of new trees.
Sentinel-2 (the recent and the spring scene of DATA_RECEIPT.json): in the dry season irrigated crops are greener than
forest, so "tree" = green in BOTH scenes and not much greener now than in spring (green_crop class 9 is never a tree class).
Thresholds: ../Tools/area_constants.py TREE_RULES (Karmei Yosef values: forest 0.28/0.22/0.4, scrub 0.26/0.24/0.12,
sat 0.36/0.42/0.05/0.34/0.14).
  ForestTrees  forest zone (3)            p = clip((min NDVI - forest_min) / forest_span, forest_floor, 1) -> forest branch
  ScrubTrees   scrub zones (6, 10)        p = clip((min NDVI - scrub_min) / scrub_span, scrub_floor, 1)   -> scrub_trees branch
  SatTrees     grass/bare/dry grass (7, 11, 12): NDVI now >= sat_now, spring >= sat_spring, now - spring <= sat_delta;
               p = clip((NDVI now - sat_min) / sat_span, 0, 1)                                         -> sat_trees branch
  OpenField    open fields (7, 9, 11, 12) -> field_trees branch (single trees, very sparse)
  <zone>_P3    the six zone masks of make_masks.py (MASKS.json); the _P3 name is kept because the graph reads it
Continuous probabilities are dithered into binary masks (the graph's Density Filter >= 0.5 is a yes/no test), so the
sampler density x the share of 'on' pixels is the real density.
Outputs: zones/<run>/trees_v2/*.png, TREES_V2.json (this folder). Run with the gis env python.
"""
import importlib.util, json, math
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('area_constants', HERE.parent / 'Tools' / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (refuses if not filled in)
assert HERE.parent.name == A.TASK_FOLDER, (HERE.parent.name, A.TASK_FOLDER)
TR = A.TREE_RULES
REC = json.loads((HERE / 'DATA_RECEIPT.json').read_text(encoding='utf-8'))
ZD = Path(REC['output_dir']); B4 = REC['grid']['bounds_epsg4326']
OUT = ZD / 'trees_v2'; OUT.mkdir(exist_ok=True)
MASKS = json.loads((HERE / 'MASKS.json').read_text(encoding='utf-8'))
FOOT = json.loads((HERE.parent / 'Buildings_v2/FOOTPRINTS.json').read_text())['footprints_ue_cm']
S = 1024; HALFA = A.HALF_EXTENT_M
rng = np.random.default_rng(20261012)


def warp(f, alg):
    ds = gdal.Warp('', str(ZD / f), format='MEM', width=S, height=S, resampleAlg=alg, outputBounds=(B4['west'], B4['south'], B4['east'], B4['north']))
    return [ds.GetRasterBand(i + 1).ReadAsArray().astype(np.float32) for i in range(ds.RasterCount)]


zone = warp('ZONES.tif', 'near')[0].astype(np.int16)
rec, spr = warp(REC['sentinel2']['recent']['file'], 'average'), warp(REC['sentinel2']['spring']['file'], 'average')
ndvi = lambda b: (b[3] - b[0]) / np.maximum(b[3] + b[0], 1.0)
nd_now, nd_spr = ndvi(rec), ndvi(spr); nd_min = np.minimum(nd_now, nd_spr)
rows, cols = np.mgrid[0:S, 0:S] + 0.5
AE = cols / S * 2 * HALFA - HALFA; AN = HALFA - rows / S * 2 * HALFA          # area-local metres (east, north)


def poly_mask(poly):           # poly in area-local metres
    m = np.zeros((S, S), bool)
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        m ^= ((y1 > AN) != (y2 > AN)) & (AE < (x2 - x1) * (AN - y1) / ((y2 - y1) if y2 != y1 else 1e-9) + x1)
    return m


def dilate(m, r):
    c = np.pad(m.astype(np.int32), ((r + 1, r), (r + 1, r))).cumsum(0).cumsum(1)
    return (c[2 * r + 1:, 2 * r + 1:] - c[:-2 * r - 1, 2 * r + 1:] - c[2 * r + 1:, :-2 * r - 1] + c[:-2 * r - 1, :-2 * r - 1]) > 0


clear = np.zeros((S, S), bool)            # template: no site parcels / fields to clear (a hero site adds its own mask)
info_clear_source = 'none (template without a hero site)'
bld = np.zeros((S, S), bool)
for poly in FOOT.values():
    ring = [(X / 100.0, -Y / 100.0) for X, Y in poly]
    m = poly_mask(ring)
    if not m.any():
        cx, cy = sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)
        r_, c_ = int((HALFA - cy) / (2 * HALFA) * S), int((cx + HALFA) / (2 * HALFA) * S)
        if 0 <= r_ < S and 0 <= c_ < S:
            m[r_, c_] = True
    bld |= m
bld = dilate(bld, 1)                      # ~ +4-5 m
info = {'clear_source': info_clear_source, 'parcel_pixels_cleared': int(clear.sum()), 'building_pixels_blocked': int(bld.sum())}


def save(name, a):
    mem = gdal.GetDriverByName('MEM').Create('', S, S, 1, gdal.GDT_Byte); mem.GetRasterBand(1).WriteArray(a.astype(np.uint8))
    p = OUT / ('%s%s.png' % (A.MASK_PREFIX, name)); gdal.GetDriverByName('PNG').CreateCopy(str(p), mem); return str(p)


files = {}
for name, f in MASKS.items():                       # the six zone masks of make_masks.py (1024 x 1024 = S x S)
    ds = gdal.Open(f['file']); a = ds.GetRasterBand(1).ReadAsArray().copy(); ds = None
    before = int((a > 0).sum()); a[clear] = 0
    files[name + '_P3'] = {'file': save(name + '_P3', a), 'on_before': before, 'on_after': int((a > 0).sum())}
base_block = clear | bld | np.isin(zone, (1, 2))


def dither(p):
    return (rng.uniform(0, 1, p.shape) < p) * 255


new = {
    'ForestTrees': (zone == 3, np.clip((nd_min - TR['forest_min']) / TR['forest_span'], TR['forest_floor'], 1.0)),
    'ScrubTrees': (np.isin(zone, (6, 10)), np.clip((nd_min - TR['scrub_min']) / TR['scrub_span'], TR['scrub_floor'], 1.0)),
    'SatTrees': (np.isin(zone, (7, 11, 12)) & (nd_now >= TR['sat_now']) & (nd_spr >= TR['sat_spring']) & (nd_now - nd_spr <= TR['sat_delta']),
                 np.clip((nd_now - TR['sat_min']) / TR['sat_span'], 0, 1)),
    'OpenField': (np.isin(zone, (7, 9, 11, 12)), np.ones((S, S), np.float32)),
}
for name, (zmask, p) in new.items():
    prob = np.where(zmask & ~base_block, p, 0.0)
    a = dither(prob) if name != 'OpenField' else (prob > 0) * 255
    files[name] = {'file': save(name, a), 'zone_pixels': int(zmask.sum()), 'mean_p_in_zone': round(float(prob[zmask & ~base_block].mean()) if (zmask & ~base_block).any() else 0.0, 3),
                   'on_pixels': int((a > 0).sum()), 'on_km2': round(float((a > 0).mean()) * (2 * HALFA / 1000) ** 2, 3)}
info['masks'] = files
info['tree_rules'] = TR
info['method'] = __doc__.split('Outputs:')[0].strip()
(HERE / 'TREES_V2.json').write_text(json.dumps(info, indent=1))
print(json.dumps({k: v for k, v in info.items() if k != 'method'}, indent=0)[:3000])
