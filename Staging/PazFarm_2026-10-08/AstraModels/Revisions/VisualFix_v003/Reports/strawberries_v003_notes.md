# Strawberry bed v003

Offline delivery: the existing bed replacement and its separate lowest LOD. Neither Unreal nor the 763 placement records was changed.

| Asset | Triangles | Size in metres | Role |
|---|---:|---|---|
| `SM_PazFarm_StrawberryBed_4m` | 10,422 | 0.8 × 4 × 0.410538 | Detailed bed, 24 rosettes / 360 larger leaflets |
| `SM_PazFarm_StrawberryBed_4m_LOD3` | 282 | 0.8 × 4 × 0.408 | Closed green ridge and closed black mulch body |

Both keep the original ground/start-end pivot `(0,0,0)`, X boundary `−0.4…0.4 m`, and Y boundary `0…4 m`. Tile along +Y in 4 m increments. The 0.25 m mulch mound is retained. The green canopy is 0.68 m wide: its opaque projected footprint covers 85% of the bed width continuously, before considering individual leaves. This is a geometry measurement, not a claim about far-screen pixel coverage.

The exact same closed canopy and mulch bodies are present in both LODs. The canopy is a connected volume with a gently varying roof, side faces, bottom, and closed ends. LOD0 adds fewer, larger true-outline leaflets, 12 berries, six flowers, and petioles. LOD3 removes those small details; it contains no card or billboard. The end cross-sections match exactly, with level first/last longitudinal segments for smooth end-to-end tiling.

All material alpha is 1. Materials are opaque and two-sided, with no wind, transparency, subsurface brightening or collision. Nominal BaseColor values are sRGB: canopy `29,58,20`; leaf `35,66,23`; new leaf `42,75,28`; mulch `8,9,8`. Mulch roughness is 0.92 and specular is 0.06, with nearly flat wrinkle normals. Canopy roughness is 0.90 and specular is 0.08. Do not reconstruct these using the previous brighter mulch material.

Material names have a `_v003` suffix. Slot 0 is `M_PazFarm_StrawberryMulch_v003`; slot 8 is `M_PazFarm_StrawberryCanopy_v003`. Both LODs retain the same nine-slot order for matching during LOD import; LOD3 uses only slots 0 and 8. Import the separate `_LOD3` FBX as the receiving mesh's actual lowest LOD so the non-Nanite Instancing HLOD uses this geometry. Merely importing it as an unrelated asset will not change the original bed's lowest LOD.

All 27 textures are 1024 × 1024. BaseColor PNGs carry explicit sRGB values and an sRGB tag; Normal and ORM are non-color data. Normals use OpenGL +Y. ORM is R=AO, G=roughness, B=metallic. There is no baked illumination in BaseColor.

Fresh source reopen and independent FBX imports pass: matching dimensions and origin, finite geometry, UV0, zero degenerate geometry and UV triangles, solid alpha, relative texture paths, positive body volume, two-face edge incidence on both closed bodies, and identical front/back profiles. See `strawberries_v003_qa.json`. The close hero and paired LOD preview were visually inspected. The requested true-distance captures and measurements are supplied separately by the distance review task; no native Unreal result has been verified here.

`Blend/Strawberry.blend` contains both LODs at the same origin. Isolate one LOD at a time for source inspection or rendering. The reproducible script is `Scripts/build_strawberries_v003.py`; editable parameters are at its top and in the scene's `PazFarm_parameters` property. No original source or v002 delivery file was modified.
