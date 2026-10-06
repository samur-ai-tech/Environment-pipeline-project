"""Read-only texture source statistics (no unreal import). Run with the gis env python (numpy + GDAL).
Extracts the embedded TSCF_PNG source from each .uasset into GDAL /vsimem/ (memory only, nothing written to disk),
decodes at a reduced overview (every 8th pixel) and reports per-channel mean/std/min/max, sRGB mean colour, luminance
and whether alpha carries data. Writes TEXTURE_STATS.json next to this script.
Note: these are SOURCE pixels, before the asset's Adjust* (brightness/saturation/hue/curve) settings are applied.
"""
import os, sys, glob, struct, json
import numpy as np
from osgeo import gdal

gdal.UseExceptions()
C = 'C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Content/'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'TEXTURE_STATS.json')
files = sorted(glob.glob(C + 'MWLandscapeAutoMaterial/Textures/**/*.uasset', recursive=True) +
               glob.glob(C + 'HighPoly_Tree_Model/Textures/**/*.uasset', recursive=True))
res = {}
for f in files:
    name = os.path.relpath(f, C).replace('\\', '/')
    if '/FX/TEX_MW_Cloud' in name or '/Bake/' in name:
        continue
    b = open(f, 'rb').read()
    best = None; i = 0
    while True:
        i = b.find(b'\x89PNG\r\n\x1a\n', i)
        if i < 0: break
        try:
            w, h = struct.unpack('>II', b[i + 16:i + 24])
            # walk chunks properly until IEND
            k = i + 8; end = None
            while k + 8 <= len(b):
                ln = struct.unpack('>I', b[k:k + 4])[0]; typ = b[k + 4:k + 8]
                if ln > len(b): break
                k += 12 + ln
                if typ == b'IEND':
                    end = k; break
            if end and 0 < w <= 16384 and 0 < h <= 16384 and (best is None or w * h > best[1] * best[2]):
                best = (i, w, h, end)
        except Exception:
            pass
        i += 8
    if not best:
        res[name] = {'error': 'no plain PNG source found (bulk payload is Oodle-compressed; not decodable offline without Oodle)'}; print(name, res[name]); continue
    s, w, h, e = best
    vp = '/vsimem/t_%d.png' % len(res)
    gdal.FileFromMemBuffer(vp, b[s:e])
    try:
        ds = gdal.Open(vp)
        step = 8
        bw, bh = max(1, w // step), max(1, h // step)
        arr = ds.ReadAsArray(buf_xsize=bw, buf_ysize=bh).astype(np.float32)  # bands, y, x (nearest)
        if arr.shape[0] >= 3:
            # MEASURED: UE TSF_BGRA8 sources are stored as raw BGRA bytes in the PNG (normal maps read ch0~250, ch2~128),
            # so swap PNG channels 0 and 2 to get true R,G,B.
            arr[[0, 2]] = arr[[2, 0]]
        bands = ds.RasterCount
        st = {'png_size': [w, h], 'bands': bands, 'sample_step': step}
        ch = 'RGBA'[:bands]
        for k in range(bands):
            a = arr[k]
            st[ch[k]] = {'mean': round(float(a.mean()), 1), 'std': round(float(a.std()), 1), 'min': int(a.min()), 'max': int(a.max())}
        if bands >= 3:
            srgb = arr[:3] / 255.0
            lin = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
            L = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
            st['mean_srgb_hex'] = '#%02x%02x%02x' % tuple(int(round(float(arr[c].mean()))) for c in range(3))
            st['linear_luminance_mean'] = round(float(L.mean()), 4)
            st['linear_luminance_std'] = round(float(L.std()), 4)
            # coarse low-frequency variation: std of 8x8-block means (tile-scale variation)
            by, bx = (bh // 8) * 8, (bw // 8) * 8
            blk = L[:by, :bx].reshape(by // 8, 8, bx // 8, 8).mean(axis=(1, 3))
            st['blockmean_luminance_std'] = round(float(blk.std()), 4)
        if bands == 4:
            al = arr[3]
            st['alpha_used'] = bool(al.min() < 250)
        res[name] = st
        ds = None
    finally:
        gdal.Unlink(vp)
    print(name, json.dumps(res[name]))
with open(OUT, 'w', encoding='utf-8') as fh:
    json.dump(res, fh, indent=1)
print('wrote', OUT)
