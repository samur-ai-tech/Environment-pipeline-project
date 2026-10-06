"""INFERRED estimate of the BUILT (post Adjust*) colour of the MW ground albedos. Read-only; gis env python.
Applies UE's texture colour adjustment as recalled from TextureCompressorModule AdjustImageColors (linear space HSV:
V*=AdjustBrightness; V=V^AdjustBrightnessCurve; S*=AdjustSaturation; H+=AdjustHue; then RGB^AdjustRGBCurve), using the
asset Adjust* values measured in PACK_INVENTORY.json. Treat results as an estimate until compared with an editor readback.
"""
import os, json, struct, glob
import numpy as np
from osgeo import gdal

gdal.UseExceptions()
HERE = os.path.dirname(os.path.abspath(__file__))
C = 'C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Content/'
inv = json.load(open(os.path.join(HERE, 'PACK_INVENTORY.json')))


def png_of(b):
    best = None; i = 0
    while True:
        i = b.find(b'\x89PNG\r\n\x1a\n', i)
        if i < 0: break
        try:
            w, h = struct.unpack('>II', b[i + 16:i + 24]); k = i + 8; end = None
            while k + 8 <= len(b):
                ln = struct.unpack('>I', b[k:k + 4])[0]; typ = b[k + 4:k + 8]
                if ln > len(b): break
                k += 12 + ln
                if typ == b'IEND': end = k; break
            if end and 0 < w <= 16384 and (best is None or w * h > best[1] * best[2]): best = (i, w, h, end)
        except Exception: pass
        i += 8
    return best


def to_lin(s): return np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)
def to_srgb(l): l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, l * 12.92, 1.055 * l ** (1 / 2.4) - 0.055)


def rgb2hsv(r, g, b):
    mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b); d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-8
    rr = m & (mx == r); gg = m & (mx == g) & ~rr; bb = m & ~rr & ~gg
    h[rr] = (60 * ((g - b)[rr] / d[rr]) + 360) % 360
    h[gg] = 60 * ((b - r)[gg] / d[gg]) + 120
    h[bb] = 60 * ((r - g)[bb] / d[bb]) + 240
    s = np.where(mx > 1e-8, d / np.maximum(mx, 1e-8), 0)
    return h, s, mx


def hsv2rgb(h, s, v):
    c = v * s; hp = (h % 360) / 60; x = c * (1 - np.abs(hp % 2 - 1)); z = np.zeros_like(h)
    conds = [(hp < 1, (c, x, z)), (hp < 2, (x, c, z)), (hp < 3, (z, c, x)), (hp < 4, (z, x, c)), (hp < 5, (x, z, c)), (hp <= 6, (c, z, x))]
    r = np.zeros_like(h); g = np.zeros_like(h); b = np.zeros_like(h); done = np.zeros(h.shape, bool)
    for cond, (a1, a2, a3) in conds:
        sel = cond & ~done; r[sel] = a1[sel]; g[sel] = a2[sel]; b[sel] = a3[sel]; done |= sel
    m = v - c
    return r + m, g + m, b + m


out = {}
for f in sorted(glob.glob(C + 'MWLandscapeAutoMaterial/Textures/Ground/*_col.uasset')):
    key = '/Game/' + os.path.relpath(f, C).replace('\\', '/')[:-7]
    adj = inv.get(key, {}).get('asset_props', {})
    bb = open(f, 'rb').read(); best = png_of(bb)
    if not best:
        out[key] = {'error': 'Oodle-compressed source; not decodable offline', 'adjust': {k: v for k, v in adj.items() if k.startswith('Adjust')}}
        print(key, out[key]); continue
    s0, w, h, e = best
    vp = '/vsimem/x.png'; gdal.FileFromMemBuffer(vp, bb[s0:e])
    ds = gdal.Open(vp); a = ds.ReadAsArray(buf_xsize=w // 16, buf_ysize=h // 16).astype(np.float64)[:3] / 255.0
    ds = None; gdal.Unlink(vp)
    a = a[[2, 1, 0]]  # BGRA-in-PNG -> RGB (measured)
    lin = to_lin(a)
    H, S, V = rgb2hsv(*lin)
    V = V * adj.get('AdjustBrightness', 1.0)
    V = V ** adj.get('AdjustBrightnessCurve', 1.0)
    S = np.clip(S * adj.get('AdjustSaturation', 1.0), 0, 1)
    H = H + adj.get('AdjustHue', 0.0)
    r, g, b = hsv2rgb(H, S, V)
    rgbc = adj.get('AdjustRGBCurve', 1.0)
    r, g, b = r ** rgbc, g ** rgbc, b ** rgbc
    L = 0.2126 * r + 0.7152 * g + 0.0722 * b
    sr = to_srgb(np.stack([r, g, b]))
    out[key] = {'adjust': {k: v for k, v in adj.items() if k.startswith('Adjust')},
                'built_mean_srgb_hex_est': '#%02x%02x%02x' % tuple(int(round(float(sr[c].mean() * 255))) for c in range(3)),
                'built_linear_luminance_mean_est': round(float(L.mean()), 4),
                'built_linear_luminance_std_est': round(float(L.std()), 4)}
    print(key, out[key])
json.dump(out, open(os.path.join(HERE, 'TEXTURE_BUILT_APPROX.json'), 'w'), indent=1)
