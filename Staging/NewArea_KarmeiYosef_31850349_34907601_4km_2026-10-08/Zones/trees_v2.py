"""More trees on the 4 km clone, offline part (Aviv 2026-10-10 approved: satellite tree map, windbreak rows near the farm,
denser forest and scrub ~2-3x + single field trees). 1024 x 1024 masks in the T_KY4_Zones orientation (row 0 = north edge,
4032 m square) for the zone PCG graph v002, plus windbreak positions for a separate static instanced actor.
Every mask is also cleared of the Paz Farm road-to-road parcels (PARCELS_V2, dilated 3 m) and the old farm footprint, so the
stand-ins do not double-plant on the new farm ground and crops; building footprints + 5 m are kept free of new trees.
Sentinel-2 (10 m, 21 Sep and 4 Apr 2026): in the dry season irrigated crops are greener than forest, so "tree" = green in
BOTH scenes and not much greener now than in spring (green_crop class 9 is never a tree class).
  ForestTrees  forest zone (3)            p = clip((min NDVI - 0.28) / 0.22, 0.4, 1)   -> forest branch, more trees where denser
  ScrubTrees   scrub zones (6, 10)        p = clip((min NDVI - 0.26) / 0.24, 0.12, 1)  -> scrub_trees branch
  SatTrees     grass/bare/dry grass (7, 11, 12): NDVI now >= 0.36, spring >= 0.42, now - spring <= 0.05;
               p = clip((NDVI now - 0.34) / 0.14, 0, 1)                                -> new sat_trees branch
  OpenField    open fields (7, 9, 11, 12) -> new field_trees branch (single trees, very sparse)
  <zone>_P3    the six existing masks cleared of the parcels (all existing branches use these)
Continuous probabilities are dithered into binary masks (the graph's Density Filter >= 0.5 is a yes/no test), so the
sampler density x the share of 'on' pixels is the real density.
Windbreaks: one row along each OSM track / farm road within 700 m of the pin, on the side away from the pin, 4 m from
the centreline, a tree every 5 m (0.5 m jitter); no trees inside the fence, on buildings (+5 m), village/water/forest,
within 10 m of a junction or within 3 m of a farm crop tree.
Outputs: zones/<run>/trees_v2/*.png, TREES_V2.json (this folder), PazFarm Georef/WINDBREAKS_V2.json. Run with the gis env python.
"""
import json, math
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
HERE = Path(__file__).resolve().parent
GEO = HERE.parents[1] / 'PazFarm_2026-10-08/Georef'
REC = json.loads((HERE / 'DATA_RECEIPT.json').read_text(encoding='utf-8'))
ZD = Path(REC['output_dir']); B4 = REC['grid']['bounds_epsg4326']
OUT = ZD / 'trees_v2'; OUT.mkdir(exist_ok=True)
MWF = json.loads((GEO / 'MASKS_WITHOUT_FARM.json').read_text())
PV = json.loads((GEO / 'PARCELS_V2.json').read_text())
L = json.loads((GEO / 'LAYOUT.json').read_text())
CTX = json.loads((GEO / 'PARCELS_CONTEXT.json').read_text())
FENCE = json.loads((GEO / 'FENCE_ROUTE_V003.json').read_text())
PL = json.loads((GEO / 'PLACEMENTS.json').read_text()); CR = json.loads((GEO / 'CROPS_V3.json').read_text())
FOOT = json.loads((HERE.parent / 'WPTrial/FOOTPRINTS.json').read_text())['footprints_ue_cm']
pe, pn = json.loads((GEO / 'roads.json').read_text())['pin_local_m_from_area_centre']
S = 1024; HALFA = 2016.0
rng = np.random.default_rng(20261012)


def warp(f, alg):
    ds = gdal.Warp('', str(ZD / f), format='MEM', width=S, height=S, resampleAlg=alg, outputBounds=(B4['west'], B4['south'], B4['east'], B4['north']))
    return [ds.GetRasterBand(i + 1).ReadAsArray().astype(np.float32) for i in range(ds.RasterCount)]


zone = warp('ZONES.tif', 'near')[0].astype(np.int16)
rec, spr = warp('S2_recent_2026-09-21.tif', 'average'), warp('S2_spring_2026-04-04.tif', 'average')
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


# parcels (1 m labels around the pin) -> mask pixels with any parcel cell; dilate 1 px (~4 m) for the 3 m margin
lt = gdal.Open(PV['labels_tif']); gt = lt.GetGeoTransform(); lab = lt.GetRasterBand(1).ReadAsArray() > 0; lt = None
H1 = -gt[0]
li = ((H1 - (AN - pn)) / gt[1]).astype(int); lj = ((AE - pe + H1) / gt[1]).astype(int)
ok = (li >= 0) & (li < lab.shape[0]) & (lj >= 0) & (lj < lab.shape[1])
par = np.zeros((S, S), bool)
for di in (-1.5, 0, 1.5):                 # 3 samples per axis inside each 3.9 m pixel
    for dj in (-1.5, 0, 1.5):
        i2 = np.clip(li + int(di), 0, lab.shape[0] - 1); j2 = np.clip(lj + int(dj), 0, lab.shape[1] - 1)
        par |= ok & lab[i2, j2]
clear = dilate(par, 1)
# Aviv 2026-10-10 "every field from the screenshot" (parcels scrapped): clear the filled fields + the farm fence instead
FIELDS = GEO.parent / 'Fields_2026-10-10'
if (FIELDS / 'fields_clear_zone.png').exists():
    fcz = gdal.Open(str(FIELDS / 'fields_clear_zone.png')); clear = dilate(fcz.GetRasterBand(1).ReadAsArray() > 127, 1); fcz = None
    info_clear_source = 'Fields_2026-10-10/fields_clear_zone.png (filled fields + fence), dilated 1 px'
else:
    info_clear_source = 'PARCELS_V2 parcels, dilated 1 px'
for f in MWF['files'].values():          # old footprint already cleared in the *_without_farm masks; keep it cleared
    pass
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
    p = OUT / ('T_KY4_Mask_%s.png' % name); gdal.GetDriverByName('PNG').CreateCopy(str(p), mem); return str(p)


files = {}
for name, f in MWF['files'].items():               # the six existing masks, farm-cleared, now parcel-cleared too
    ds = gdal.Open(f['file']); a = ds.GetRasterBand(1).ReadAsArray().copy(); ds = None
    before = int((a > 0).sum()); a[clear] = 0
    files[name + '_P3'] = {'file': save(name + '_P3', a), 'on_before': before, 'on_after': int((a > 0).sum())}
base_block = clear | bld | np.isin(zone, (1, 2))


def dither(p):
    return (rng.uniform(0, 1, p.shape) < p) * 255


new = {
    'ForestTrees': (zone == 3, np.clip((nd_min - 0.28) / 0.22, 0.4, 1.0)),
    'ScrubTrees': (np.isin(zone, (6, 10)), np.clip((nd_min - 0.26) / 0.24, 0.12, 1.0)),
    'SatTrees': (np.isin(zone, (7, 11, 12)) & (nd_now >= 0.36) & (nd_spr >= 0.42) & (nd_now - nd_spr <= 0.05), np.clip((nd_now - 0.34) / 0.14, 0, 1)),
    'OpenField': (np.isin(zone, (7, 9, 11, 12)), np.ones((S, S), np.float32)),
}
for name, (zmask, p) in new.items():
    prob = np.where(zmask & ~base_block, p, 0.0)
    a = dither(prob) if name != 'OpenField' else (prob > 0) * 255
    files[name] = {'file': save(name, a), 'zone_pixels': int(zmask.sum()), 'mean_p_in_zone': round(float(prob[zmask & ~base_block].mean()) if (zmask & ~base_block).any() else 0.0, 3),
                   'on_pixels': int((a > 0).sum()), 'on_km2': round(float((a > 0).mean()) * (2 * HALFA / 1000) ** 2, 3)}
info['masks'] = files

# ---------------- windbreaks (metres from the pin) ----------------
fence = [complex(*v) for v in FENCE['vertices_m']]


def in_poly(z, poly):
    ins = False
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        if (a.imag > z.imag) != (b.imag > z.imag) and z.real < (b.real - a.real) * (z.imag - a.imag) / (b.imag - a.imag) + a.real:
            ins = not ins
    return ins


lines = [('osm_%d' % w['id'], [complex(*p) for p in w['pts']], {'track': 2.0, 'service': 3.0, 'residential': 3.5}.get(w['highway'], None))
         for w in CTX['osm_ways'] if w['highway'] in ('track', 'service', 'residential')]
lines += [('farm_' + n, [complex(*p) for p in r['line_m']], r['width_m'] / 2) for n, r in PV['roads_drawn'].items()]
all_lines = lines + [('osm_%d' % w['id'], [complex(*p) for p in w['pts']], 9.0 if w['highway'] == 'trunk' else 2.0)
                     for w in CTX['osm_ways'] if w['highway'] not in ('track', 'service', 'residential')]


def dist_to(z, pts):
    best = 1e9
    for a, b in zip(pts, pts[1:]):
        d = b - a; L2 = abs(d) ** 2 or 1e-9
        t = max(0, min(1, ((z - a) * d.conjugate()).real / L2))
        best = min(best, abs(z - (a + t * d)))
    return best


FPF = FIELDS / ('FIELD_PLANTS_V2.json' if (FIELDS / 'FIELD_PLANTS_V2.json').exists() else 'FIELD_PLANTS_V1.json')
FP = json.loads(FPF.read_text()) if FPF.exists() else None
crop_pts = np.array([[it['e'], it['n']] for it in PL['items'] if it['kind'].startswith('tree')] +
                    ([[it[2], it[3]] for it in FP['items'] if it[0] in ('orchard', 'rows', 'olive', 'vine', 'greenhouse', 'margin')] if FP else [[t['e'], t['n']] for t in CR['trees']]),
                    np.float64)
cgrid = {}
for k_, (e, n) in enumerate(crop_pts):
    cgrid.setdefault((int(e // 5), int(n // 5)), []).append(k_)


def near_crop(z, r=3.0):
    for gx in range(int(z.real // 5) - 1, int(z.real // 5) + 2):
        for gy in range(int(z.imag // 5) - 1, int(z.imag // 5) + 2):
            for k_ in cgrid.get((gx, gy), ()):
                if (crop_pts[k_, 0] - z.real) ** 2 + (crop_pts[k_, 1] - z.imag) ** 2 < r * r:
                    return True
    return False


def area_pix(z):
    e, n = z.real + pe, z.imag + pn
    return int((HALFA - n) / (2 * HALFA) * S), int((e + HALFA) / (2 * HALFA) * S)


# Aviv 2026-10-10 'Yes, import both': windbreak pines are Astra's Aleppo pines (VF3: = <clone>/PazFarm/VisualFix_v003/Meshes)
MESHES = [('VF3:SM_PazFarm_AleppoPine_A', 3), ('VF3:SM_PazFarm_AleppoPine_B', 3), ('VF3:SM_PazFarm_AleppoPine_C', 2), ('SM_green-tree01', 2), ('SM_green-tree02', 2)]
wsum = sum(w for _, w in MESHES)
wb = {'units': 'metres east/north of the Paz Farm pin', 'meshes_folder': '<clone>/Vegetation/Meshes (never-vanish copies)', 'trees': []}
skipped = {'fence': 0, 'junction': 0, 'building_zone': 0, 'crop': 0, 'outside': 0, 'parcel_deep': 0}
for lid, pts, hw in lines:
    others = [l for l in all_lines if l[0] != lid]
    for a, b in zip(pts, pts[1:]):
        d = b - a; Lg = abs(d)
        if Lg < 1e-3:
            continue
        u = d / Lg; nrm = complex(-u.imag, u.real)
        mid = (a + b) / 2
        if abs(mid) > 700:
            continue
        side = nrm if (mid + nrm).real * mid.real + (mid + nrm).imag * mid.imag > abs(mid) ** 2 else -nrm   # away from the pin
        off = hw + 2.0
        s = 2.5
        while s < Lg:
            z = a + u * s + side * off + complex(rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5))
            s += 5.0
            if abs(z) > 700:
                skipped['outside'] += 1; continue
            if in_poly(z, fence):
                skipped['fence'] += 1; continue
            if any(dist_to(z, l[1]) < l[2] + 6.0 for l in others if l[2] is not None):
                skipped['junction'] += 1; continue
            r_, c_ = area_pix(z)
            if not (0 <= r_ < S and 0 <= c_ < S) or bld[r_, c_] or zone[r_, c_] in (1, 2, 3):
                skipped['building_zone'] += 1; continue
            if near_crop(z):
                skipped['crop'] += 1; continue
            k = rng.uniform(0, wsum); acc = 0
            for m_, w in MESHES:
                acc += w
                if k <= acc:
                    break
            wb['trees'].append({'mesh': m_, 'e': round(z.real, 2), 'n': round(z.imag, 2), 'yaw_deg': round(float(rng.uniform(0, 360)), 1),
                                'scale': round(float(rng.uniform(0.85, 1.15)), 3), 'line': lid})
wb['skipped'] = skipped
(GEO / 'WINDBREAKS_V2.json').write_text(json.dumps(wb))
info['windbreak_trees'] = len(wb['trees']); info['windbreak_skipped'] = skipped
info['method'] = __doc__.split('Outputs:')[0].strip()
(HERE / 'TREES_V2.json').write_text(json.dumps(info, indent=1))
print(json.dumps({k: v for k, v in info.items() if k != 'method'}, indent=0)[:3000])
