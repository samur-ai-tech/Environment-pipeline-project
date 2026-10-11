# Fixed-distance preview evidence — v003

**OFFLINE_DISTANCE_EVIDENCE_COMPLETE**: 53 of 53 full-resolution frames.

1920×1080 perspective; horizontal FOV 60°; Cycles CPU 32 samples; no denoising/adaptive sampling; Standard sRGB; exposure 0. World/sun/camera settings remain fixed. Transparent alpha covers geometry only. All distances are camera-to-declared-target slant distances.

See `Previews/Distance/INDEX.html`; full settings and camera transforms are in `Reports/distance_validation.json`. Magnified pairs are diagnostic crops; original full frames are retained.

| Asset / arrangement | Distance | LOD0 area px | LOD3 area px | Alpha IoU | LOD3 luma delta |
|---|---:|---:|---:|---:|---:|
| pines A single | 300 m | 383.753 | 398.153 | 0.891 | +1.89 |
| pines A single | 1000 m | 34.580 | 35.478 | 0.914 | +1.82 |
| pines B single | 300 m | 712.514 | 750.125 | 0.892 | +1.39 |
| pines B single | 1000 m | 64.212 | 67.796 | 0.902 | +1.46 |
| pines C single | 300 m | 1228.537 | 1316.933 | 0.893 | +0.79 |
| pines C single | 1000 m | 108.957 | 117.659 | 0.903 | +0.95 |
| strawberry bed single | 150 m | 296.816 | 281.537 | 0.949 | -3.08 |
| strawberry bed single | 500 m | 26.569 | 25.353 | 0.954 | -3.12 |
| strawberry bed ten_tiles | 150 m | 2882.690 | 2731.318 | 0.947 | -3.20 |
| strawberry bed ten_tiles | 500 m | 258.663 | 245.173 | 0.948 | -3.60 |

## Calibration and source binding

The initial A check found the smoother LOD3 upper-crown screen region about 42–44% brighter than LOD0. The model author calibrated the shared hull texture by a 0.63 linear-albedo multiplier, then regenerated the pine sources. Final comparison values above use those updated sources. The superseded numerical check remains in `distance_calibration_initial.json`. The crown region is an explicit screen-space proxy above the 55%-height projection, not a material-ID mask.
All final frame source/texture bindings current and captured before rendering: **True**. Each family also verifies those textures and its .blend are unchanged after rendering. Resume requires matching pre-render texture hashes, source hash, settings hash and PNG hash.

## Limits

5 m pine and 2 m bed/block frames intentionally crop at fixed FOV; the separate hero views show complete close assets. Subpixel plants cannot be guaranteed visible in every raster/view. 4 km pine stress frames are included. These renders assess model source appearance in Blender, not Unreal Nanite/HLOD/streaming. Native import, lowest-LOD selection, always-loaded policy, final lighting, save/reopen and acceptance remain with the operator.

Diagnostic review bands (not visual acceptance): nonzero alpha in both LODs, area ratio 0.65–1.45, alpha IoU at least 0.55, LOD3 brightening no more than 10 luma code values, absolute channel difference no more than 18. Upper-crown proxy brightening is flagged when both over 20% and over 2 code values. Cropped close views are informational. Individual failures are retained in JSON for review.
