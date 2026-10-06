"""OFFLINE, read-only: measured statistics of the S1v2a macro-noise textures (source PNG inside the .uasset).

Run with a Python that has numpy + GDAL (here: %USERPROFILE%/miniforge3/envs/gis/python.exe):
  <gis python> -B noise_stats_v2a.py <out.json>        (out must be a new file directly under S1v2)

For each texture: the embedded source PNG is extracted from the package bytes (raw, or inside UE's
chunked-zlib bulk data: tag 0x9E2A83C1, chunk size, totals, (compressed, uncompressed) pairs), decoded
with GDAL (/vsimem), converted to the SAMPLED value space (sRGB textures: use_legacy_gamma=True ->
x**2.2 (M r027 texture readback); TC_MASKS textures: linear x), and measured per channel:
mean, std, and the std of 2^k block means (what the mip chain keeps at distance). It also simulates the
v2a field on 400k random world points (nearest texel, mip 0): z_i = (n_i - mean_c) / std_c for the three
octaves, V = 0.45 z1 + 0.35 z2 + 0.20 z3, and reports std(V) and the clamp fraction at +-2 sigma_V.
Labels: MEASURED from source pixels; the runtime texture is block-compressed and filtered (INFERRED close).
Never writes under Content/.
"""
import hashlib
import json
import math
import struct
import sys
import zlib
from pathlib import Path

import numpy as np
from osgeo import gdal

gdal.UseExceptions()
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]  # .../Environmentpipeline
TEXTURES = {
    'T_MacroVariation': {'package': '/Game/StarterContent/Textures/T_MacroVariation.T_MacroVariation',
                         'file': 'Content/StarterContent/Textures/T_MacroVariation.uasset',
                         'decode': 'srgb_legacy_gamma_2.2', 'sampler': 'COLOR'},
    'TEX_MW_Noise_msk': {'package': '/Game/MWLandscapeAutoMaterial/Textures/FX/TEX_MW_Noise_msk.TEX_MW_Noise_msk',
                         'file': 'Content/MWLandscapeAutoMaterial/Textures/FX/TEX_MW_Noise_msk.uasset',
                         'decode': 'linear', 'sampler': 'MASKS'},
    'T_Perlin_Noise_M': {'package': '/Game/StarterContent/Textures/T_Perlin_Noise_M.T_Perlin_Noise_M',
                         'file': 'Content/StarterContent/Textures/T_Perlin_Noise_M.uasset',
                         'decode': 'linear', 'sampler': 'MASKS'},
}
PNG = b'\x89PNG\r\n\x1a\n'
TAG = struct.pack('<I', 0x9E2A83C1)
OCTAVES = ((0, 6100.0, 17.0, (0.13, 0.71)), (1, 21100.0, 53.0, (0.37, 0.61)), (2, 73300.0, 89.0, (0.83, 0.29)))
WEIGHTS = (0.45, 0.35, 0.20)


def png_chunks_ok(data, start):
    j, size = start + 8, None
    while j + 8 <= len(data):
        length, kind = struct.unpack('>I4s', data[j:j + 8])
        if length > len(data) or not kind.isalpha():
            return None
        if kind == b'IHDR':
            size = struct.unpack('>II', data[j + 8:j + 16])
        j += 12 + length
        if kind == b'IEND':
            return size, data[start:j]
    return None


def source_png(data):
    """Largest complete PNG: raw in the package, or inside UE chunked-zlib bulk data."""
    found = []
    i = data.find(PNG)
    while i >= 0:
        ok = png_chunks_ok(data, i)
        if ok:
            found.append(('raw', i, ok[0], ok[1]))
        i = data.find(PNG, i + 1)
    k = data.find(TAG)
    while k >= 0:
        try:
            tag, chunk, csum, usum = struct.unpack('<4q', data[k:k + 32])
            if chunk > 0 and 0 < usum < 1 << 31 and 0 < csum <= len(data):
                n = (usum + chunk - 1) // chunk
                infos = [struct.unpack('<2q', data[k + 32 + 16 * m:k + 48 + 16 * m]) for m in range(n)]
                if sum(c for c, _ in infos) == csum and sum(u for _, u in infos) == usum:
                    p, out = k + 32 + 16 * n, bytearray()
                    for c, u in infos:
                        part = zlib.decompress(data[p:p + c])
                        assert len(part) == u
                        out += part
                        p += c
                    j = bytes(out).find(PNG)
                    ok = png_chunks_ok(bytes(out), j) if j >= 0 else None
                    if ok:
                        found.append(('chunked_zlib@%d' % k, j, ok[0], ok[1]))
        except (struct.error, zlib.error, AssertionError):
            pass
        k = data.find(TAG, k + 1)
    assert found, 'no complete PNG'
    return max(found, key=lambda r: r[2][0] * r[2][1])


def decode(png):
    name = '/vsimem/s1v2a_noise.png'
    gdal.FileFromMemBuffer(name, png)
    try:
        ds = gdal.Open(name)
        arr = np.stack([ds.GetRasterBand(b + 1).ReadAsArray() for b in range(ds.RasterCount)], axis=-1)
    finally:
        gdal.Unlink(name)
    return arr.astype(np.float64) / 255.0


def measure(key, row):
    data = (ROOT / row['file']).read_bytes()
    where, offset, size, png = source_png(data)
    rgb = decode(png)[..., :3]
    value = rgb ** 2.2 if row['decode'].startswith('srgb') else rgb
    mean = value.reshape(-1, 3).mean(axis=0)
    std = value.reshape(-1, 3).std(axis=0)
    mips = {}
    for level in (2, 4, 5, 6, 8):
        b = 2 ** level
        h, w = value.shape[0] // b * b, value.shape[1] // b * b
        blocks = value[:h, :w].reshape(h // b, b, w // b, b, 3).mean(axis=(1, 3))
        mips['mip%d_block%d_std' % (level, b)] = [round(float(x), 6) for x in blocks.reshape(-1, 3).std(axis=0)]
    corr = np.corrcoef(value.reshape(-1, 3).T)
    rng = np.random.default_rng(20261006)
    pts = rng.uniform(-100000.0, 100000.0, size=(400000, 2))  # world cm, 2 km square
    zs = []
    for channel, tile, degrees, offset in OCTAVES:
        c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
        q = pts / tile
        u = q[:, 0] * c - q[:, 1] * s + offset[0]
        v = q[:, 0] * s + q[:, 1] * c + offset[1]
        x = (np.floor((u % 1.0) * value.shape[1]).astype(int)) % value.shape[1]
        y = (np.floor((v % 1.0) * value.shape[0]).astype(int)) % value.shape[0]
        zs.append((value[y, x, channel] - mean[channel]) / std[channel])
    field = sum(w * z for w, z in zip(WEIGHTS, zs))
    sigma_nominal = math.sqrt(sum(w * w for w in WEIGHTS))
    return {'package': row['package'], 'file': row['file'], 'file_sha256': hashlib.sha256(data).hexdigest(),
            'png_location': where, 'png_offset': offset, 'png_size': list(size),
            'png_sha256': hashlib.sha256(png).hexdigest(), 'decode': row['decode'], 'sampler': row['sampler'],
            'mean_rgb': [round(float(x), 6) for x in mean], 'std_rgb': [round(float(x), 6) for x in std],
            'inv_std_rgb': [round(float(1.0 / x), 6) for x in std], 'block_mean_std': mips,
            'channel_corr': {'RG': round(float(corr[0, 1]), 4), 'RB': round(float(corr[0, 2]), 4),
                             'GB': round(float(corr[1, 2]), 4)},
            'field_simulation_mip0_nearest': {
                'points': len(pts), 'sigma_nominal_independent': round(sigma_nominal, 6),
                'sigma_measured': round(float(field.std()), 6), 'mean_measured': round(float(field.mean()), 6),
                'clamped_fraction_at_2sigma_nominal': round(float(np.mean(np.abs(field) > 2 * sigma_nominal)), 6)}}


def main(out):
    out = Path(out).resolve()
    assert out.parent == HERE and not out.exists(), 'writes only a new file directly under S1v2'
    result = {'schema': 'environmentpipeline.s1v2a_noise_stats.v1', 'script': str(Path(__file__).resolve()),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'labels': {'MEASURED': 'source PNG pixels in the package', 'INFERRED': 'runtime BC-compressed/filtered '
                         'sampling is close to these values; sRGB decode uses legacy gamma 2.2 (use_legacy_gamma=True, '
                         'M r027 readback for T_MacroVariation)'},
              'octaves': [{'channel': 'RGB'[c], 'tile_cm': t, 'rotation_deg': d, 'offset': list(o)} for c, t, d, o in OCTAVES],
              'weights': list(WEIGHTS), 'textures': {k: measure(k, r) for k, r in TEXTURES.items()}}
    out.write_text(json.dumps(result, indent=1), encoding='utf-8')
    print(json.dumps({'file': str(out), 'sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
                      **{k: {'mean': v['mean_rgb'], 'std': v['std_rgb'], 'field': v['field_simulation_mip0_nearest']}
                         for k, v in result['textures'].items()}}, indent=1))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
