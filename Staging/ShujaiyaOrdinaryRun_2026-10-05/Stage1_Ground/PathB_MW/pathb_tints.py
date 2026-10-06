"""Offline, reproducible tint proposals for MI_GeoCityGround_MW (no unreal import).

Inputs (MEASURED): 256px thumbnail means of the MW albedo textures, sRGB 0-255, from
S1_Prep/AstraMWInventory/TEX_MWAM_<name>_col_preview.png (pure-Python PNG mean, 2026-10-06).
Method (INFERRED model): MF_MWAM_DefaultLayer multiplies ColorCorrection into BaseColor only when the
layer's MW_[x]_Use<Layer>Advanced static bool is true (graphs/MF_MWAM_DefaultLayer.json: StaticSwitch_2
True->Multiply_4(ColorCorrection, lerp)). Multipliers are derived in LINEAR space so each slot's texture
mean is moved to the target chromaticity at (slot luminance x gain). Lighting, Variation mask (x1.5),
tonemapper and auto exposure are NOT modelled: these are starting points for an apply -> capture -> choose loop.
Writes TINT_PRESETS.json next to this file.
"""
import json
from pathlib import Path

TEX = {'SandA': (148.7, 113.8, 91.9), 'SandC': (132.4, 98.5, 77.1), 'Stones': (79.5, 75.6, 71.2)}
# DesertExample slot bindings (MEASURED, MW_INVENTORY.json texture_overrides)
SLOTS = {'MW_SnowColorCorrection': 'SandA', 'MW_GrassColorCorrection': 'SandA', 'MW_DirtColorCorrection': 'SandA',
         'MW_StonesColorCorrection': 'SandC', 'MW_RockColorCorrection': 'Stones'}
EXTRA = {'MW_DirtColorCorrection': 1.25,   # DesertExample's own Dirt brightening (1.25) is preserved
         'MW_RockColorCorrection': 1.5}    # lift the dark gray gravel on steep slopes toward pale ground
PRESETS = {  # target linear albedo chromaticity, luminance gain vs the slot texture
    'P1_gaza_pale_sand': {'target_linear': (0.48, 0.43, 0.32), 'gain': 1.20,
                          'intent': 'pale beige sand, clearly less orange, ~20% brighter (recommended first try)'},
    'P2_pale_neutral': {'target_linear': (0.46, 0.43, 0.36), 'gain': 1.30,
                        'intent': 'paler and more neutral/greyish beige (if P1 still reads warm)'},
    'P3_mild_warm': {'target_linear': (0.50, 0.40, 0.27), 'gain': 1.10,
                     'intent': 'closest to the approved MW preview, only de-oranged'}}
LO, HI = 0.25, 3.0


def lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def srgb(v):
    v = max(0.0, min(1.0, v))
    return 255.0 * (12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055)


def luma(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def build():
    out = {'schema': 'environmentpipeline.pathb_mw_tints.v1', 'method': __doc__.strip().splitlines()[0],
           'texture_mean_srgb': TEX, 'slot_textures': SLOTS, 'slot_extra_gain': EXTRA, 'bounds': [LO, HI], 'presets': {}}
    for name, spec in PRESETS.items():
        target = spec['target_linear']
        values, preview = {}, {}
        for param, tex in SLOTS.items():
            base = tuple(lin(c) for c in TEX[tex])
            scale = luma(base) * spec['gain'] * EXTRA.get(param, 1.0) / luma(target)
            want = tuple(t * scale for t in target)
            mult = tuple(round(min(HI, max(LO, w / b)), 3) for w, b in zip(want, base))
            values[param] = {'r': mult[0], 'g': mult[1], 'b': mult[2], 'a': 1.0}
            preview[param] = [round(srgb(b * m)) for b, m in zip(base, mult)]
        out['presets'][name] = {'intent': spec['intent'], 'target_linear': target, 'gain': spec['gain'],
                                'vectors': values, 'expected_texture_mean_srgb_after': preview}
    return out


if __name__ == '__main__':
    data = build()
    path = Path(__file__).resolve().with_name('TINT_PRESETS.json')
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    for name, p in data['presets'].items():
        print(name, {k: (v['r'], v['g'], v['b']) for k, v in p['vectors'].items()})
        print('   texture-mean sRGB after:', p['expected_texture_mean_srgb_after'])
