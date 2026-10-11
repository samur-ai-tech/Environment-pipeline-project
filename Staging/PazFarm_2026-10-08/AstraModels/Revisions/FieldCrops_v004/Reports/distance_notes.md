# FieldCrops v004 — distance evidence

154 / 154 fixed-camera frames; 76 matched LOD pairs.

1920 × 1080 perspective, 60° horizontal field of view, Cycles CPU 16 samples, no denoising or adaptive sampling. Standard sRGB view, exposure 0. Geometry-only transparent alpha excludes ground and cast shadows. Each distance is measured from the camera to the declared target, with no far auto-framing. Full camera transforms and source/texture hashes are recorded per frame.

The separate fitted hero views show the complete models. Close fixed-distance views may crop, especially the 2 m block/scatter and 5 m mature trees. Magnified pixel crops are labelled and do not replace full-resolution evidence.

| Model / arrangement | Distance | LOD0 area px | Lowest area px | Alpha IoU | Lowest luma change |
|---|---:|---:|---:|---:|---:|
| grass Clump_A single | 150 m | 4.00 | 2.63 | 0.583 | -2.15 |
| grass Clump_B single | 150 m | 10.62 | 7.56 | 0.702 | -2.67 |
| grass Clump_C single | 150 m | 16.01 | 10.38 | 0.624 | -1.48 |
| grass Clump_D single | 150 m | 26.82 | 18.01 | 0.633 | +2.90 |
| grass Clump_E single | 150 m | 4.07 | 2.82 | 0.666 | +0.66 |
| grass Clump_F single | 150 m | 13.39 | 8.75 | 0.654 | -5.91 |
| grass Patch_2m_A single | 150 m | 137.49 | 117.29 | 0.542 | -6.26 |
| grass Patch_2m_B single | 150 m | 140.03 | 115.29 | 0.532 | -3.23 |
| grass mixed scatter_10x10m | 150 m | 1643.86 | 1240.77 | 0.642 | -2.13 |
| olives A single | 300 m | 259.38 | 276.06 | 0.889 | +1.86 |
| olives A single | 1000 m | 22.76 | 24.82 | 0.893 | +3.08 |
| olives B single | 300 m | 324.63 | 350.63 | 0.868 | +1.28 |
| olives B single | 1000 m | 28.57 | 31.33 | 0.849 | +1.81 |
| olives C single | 300 m | 505.11 | 558.77 | 0.878 | +1.13 |
| olives C single | 1000 m | 44.62 | 50.63 | 0.859 | +1.51 |
| olives Young single | 300 m | 40.95 | 43.76 | 0.906 | +2.82 |
| olives Young single | 1000 m | 3.51 | 3.76 | 0.871 | +9.76 |
| vines A single | 150 m | 282.53 | 270.79 | 0.915 | +2.17 |
| vines A single | 500 m | 24.95 | 23.76 | 0.924 | +1.70 |
| vines B single | 150 m | 281.45 | 270.79 | 0.921 | +2.90 |
| vines B single | 500 m | 25.26 | 23.76 | 0.931 | +2.73 |
| vines C single | 150 m | 283.33 | 270.54 | 0.915 | +2.39 |
| vines C single | 500 m | 25.38 | 23.64 | 0.908 | +1.82 |
| vines mixed block_5x10 | 150 m | 13022.17 | 12035.09 | 0.914 | +2.83 |
| vines mixed block_5x10 | 500 m | 1162.36 | 1076.90 | 0.918 | +2.96 |

Area is alpha-weighted equivalent opaque pixels. Lit colour is measured from actual PNG bytes, weighted by geometry alpha. Comparison flags use deliberately simple review bands: area ratio 0.65–1.45, alpha IoU at least 0.55, lowest-LOD brightening at most 10 luma code values and absolute RGB channel difference at most 18. Cropped views are informational. See VISUAL_REVIEW.json for the outcome and interpretation of flagged pairs. These bands are not user acceptance criteria.

Single small grass clumps become only a few pixels at 150 m; scatter coverage matters more there. No geometry can guarantee visibility at every raster resolution/FOV. This suite verifies source appearance in Blender. Unreal material construction, anti-aliasing, HLOD selection, streaming, native distance appearance and save/reopen remain untested.
