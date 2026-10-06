# Bank ME — import report (StaticMeshTools.import_file over MCP)

Run 2026-09-27 02:56–02:59 local by the Track A Claude session, in the manager's "window open" slot while the operator's T2 task was held. Source: `Staging\ModelBank\ME\Sources\<id>_<Name>\*.fbx`, 32 assets (H0896 and H0042 excluded). Target: `/Game/Project/Shared/Bank_ME/{Buildings,StreetFurniture,Props,Vehicles,Vegetation}/`, asset names `SM_<id>_<Name>`, grouping per `Operator\staged\TASK_0006.md`. Arguments: import_materials true, import_textures true, combine_meshes true. The tool exposes no scale, collision or Nanite options; defaults apply.

## Result

**State: imported, measured and saved, NOT qualified. No textures were imported.** All 47 created Materials contain a single `MaterialExpressionVectorParameter` and have no dependencies; there are 0 Texture assets under Bank_ME. Cause: each FBX references its textures by bare file name (for example `palm03_5453f80b0bad.png` in `CoconutPalm__0958.fbx`), and the files sit in a `Textures\` subfolder next to the FBX, where the FBX importer did not look. The log shows no texture warning.

| Group | StaticMesh | Material | Texture |
|---|---:|---:|---:|
| Buildings | 10 | 28 | 0 |
| StreetFurniture | 8 | 5 | 0 |
| Props | 10 | 7 | 0 |
| Vehicles | 1 | 1 | 0 |
| Vegetation | 3 | 6 | 0 |
| **Total** | 32 | 47 | 0 |

- Imports: 32 of 32 returned a StaticMesh path; 0 failures. Slowest imports: 4.7s [011] ok bank_import_Buildings_H0015_Building_02 (4.6s) :: {"returnValue":[{"refPath"; 17.1s [012] ok bank_import_Buildings_H0016_Building_03 (16.9s) :: {"returnValue":[{"refPat; 52.3s [010] ok bank_import_Buildings_H0014_Building_01 (52.2s) :: {"returnValue":[{"refPat.
- Save: `AssetTools.save_assets` with the explicit list of the 79 Bank_ME asset paths returned true. There was no save-all; T2_Orient was not saved and is unchanged.
- Measurements per mesh: `IMPORT_RESULTS.csv` and `IMPORT_RESULTS.json` (bounds in cm; pivot offset to the bounds centre and to the bottom centre; material slot count and names; LOD0 triangles and vertices; LOD count; Nanite flag). Scale looks correct in centimetres. Examples: garbage bin 29 × 34 × 74 cm, streetlight 3.69 m tall, H0013 building 28.9 × 21.3 × 48.7 m.

## Import warnings (verbatim patterns; 49 lines. The 192 LogScript lines from my own first measurement attempt with wrong object paths are excluded)

- 32 × `FBXImport: Warning: No smoothing group information was found in this FBX scene.  Please make sure to enable the 'Export Smoothing Groups' option in the FBX Exporter plug-in before exporting the file.  Even for tools that don't support smoothing groups, the FBX Exporter will generate appropriate smoo`
- 1 × `FBXImport: Warning: SM_H0014_Building_01 has some nearly zero tangents which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: Warning: SM_H0014_Building_01 has some nearly zero bi-normals which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: Warning: SM_H0015_Building_02 has some nearly zero tangents which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: Warning: SM_H0015_Building_02 has some nearly zero bi-normals which can create some issues. (Tolerance of 1E-4)`
- 1 × `LogStaticMesh: Warning: SM_H0016_Building_03 has degenerate tangent bases which will result in incorrect shading.  MikkTSpace relies on tangent bases and may result in mesh corruption, consider disabling this option.`
- 1 × `FBXImport: Warning: SM_H0016_Building_03 has degenerate tangent bases which will result in incorrect shading.  MikkTSpace relies on tangent bases and may result in mesh corruption, consider disabling this option.`
- 1 × `FBXImport: Warning: SM_H0016_Building_03 has some nearly zero bi-normals which can create some issues. (Tolerance of 1E-4)`
- 1 × `LogStaticMesh: Warning: SM_H0904_Slum_v_fbx has degenerate tangent bases which will result in incorrect shading.  MikkTSpace relies on tangent bases and may result in mesh corruption, consider disabling this option.`
- 1 × `LogStaticMesh: Warning: SM_H0904_Slum_v_fbx has some nearly zero bi-normals which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: Warning: SM_H0904_Slum_v_fbx has degenerate tangent bases which will result in incorrect shading.  MikkTSpace relies on tangent bases and may result in mesh corruption, consider disabling this option.`
- 1 × `FBXImport: Warning: SM_H0904_Slum_v_fbx has some nearly zero bi-normals which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: Warning: SM_H0043_Foodcart_001 has some nearly zero tangents which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: Warning: SM_H0043_Foodcart_001 has some nearly zero bi-normals which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: Warning: SM_H0039_Destryoedcar has some nearly zero tangents which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: Warning: SM_H0039_Destryoedcar has some nearly zero bi-normals which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: Warning: SM_H0647_Nopal has some nearly zero tangents which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: Warning: SM_H0647_Nopal has some nearly zero bi-normals which can create some issues. (Tolerance of 1E-4)`

## Per mesh

| Group | Asset | Size X × Y × Z cm | Pivot → bottom centre cm | Slots | Tris LOD0 |
|---|---|---|---|---:|---:|
| Buildings | SM_H0907_Arab_x3_fbx | 1369 × 1369 × 1561 | -4, 16, -1 | 1 | 3302 |
| Buildings | SM_H0906_Arab_x2_fbx | 789 × 795 × 1367 | 3, 5, 0 | 1 | 4361 |
| Buildings | SM_H0905_Arab_x1_fbx | 2192 × 1022 × 963 | 54, -385, -18 | 1 | 6075 |
| Buildings | SM_H0904_Slum_v_fbx | 626 × 519 × 517 | 60, -39, 3 | 1 | 862 |
| Buildings | SM_H0903_Slum_s_fbx | 600 × 454 × 779 | -6, -34, 1 | 1 | 767 |
| Buildings | SM_H0902_Slum_k_fbx | 555 × 465 × 407 | -14, -24, 2 | 1 | 440 |
| Buildings | SM_H0016_Building_03 | 1842 × 5269 × 2170 | 742, -100, 0 | 9 | 822754 |
| Buildings | SM_H0015_Building_02 | 2034 × 1171 × 2417 | 283, -22, -0 | 4 | 201057 |
| Buildings | SM_H0014_Building_01 | 1728 × 2096 × 2120 | 3, -0, -3 | 8 | 2476576 |
| Buildings | SM_H0013_Building_04 | 2890 × 2131 × 4868 | -171, 16, 0 | 4 | 44241 |
| StreetFurniture | SM_H0051_Garbagebin | 29 × 34 × 74 | -2, 1, -0 | 1 | 5180 |
| StreetFurniture | SM_H0094_Woodenpole | 133 × 14 × 338 | -0, -0, 0 | 1 | 732 |
| StreetFurniture | SM_H0083_Streetsign_001 | 47 × 8 × 125 | -0, 1, -0 | 1 | 352 |
| StreetFurniture | SM_H0082_Streetsign | 41 × 8 × 123 | -0, 0, 0 | 1 | 420 |
| StreetFurniture | SM_H0081_Streetpowerbox | 80 × 30 × 105 | -0, 12, 0 | 1 | 5088 |
| StreetFurniture | SM_H0079_Streetlight | 256 × 211 × 369 | -99, 75, 0 | 1 | 34471 |
| StreetFurniture | SM_H0060_Metal_Barrier | 121 × 32 × 66 | -3, 0, -0 | 1 | 2804 |
| StreetFurniture | SM_H0025_Barrier | 193 × 41 × 57 | 0, 0, 0 | 1 | 1160 |
| Props | SM_H0650_SM_AirConditioner | 50 × 100 × 72 | 25, -50, 0 | 1 | 212 |
| Props | SM_H0091_Watertank_001 | 35 × 35 × 131 | -0, 6, 0 | 1 | 2656 |
| Props | SM_H0090_Watertank | 140 × 122 × 111 | 5, 0, 9 | 1 | 7406 |
| Props | SM_H0089_Tires | 63 × 45 × 50 | -3, -0, 1 | 1 | 3780 |
| Props | SM_H0077_Stones_Stack | 167 × 116 × 52 | 1, -26, 0 | 1 | 1934 |
| Props | SM_H0059_Grill_ | 36 × 31 × 48 | -0, 3, 0 | 1 | 17674 |
| Props | SM_H0058_Gaz | 29 × 29 × 62 | 0, -0, 0 | 1 | 12247 |
| Props | SM_H0046_Foodcrate | 33 × 48 × 25 | -0, 0, 0 | 1 | 16038 |
| Props | SM_H0043_Foodcart_001 | 244 × 220 × 209 | -39, -0, -14 | 1 | 41840 |
| Props | SM_H0034_Cart | 242 × 113 × 74 | 0, 0, 3 | 1 | 15346 |
| Vehicles | SM_H0039_Destryoedcar | 317 × 191 × 124 | 6, -20, 2 | 1 | 8330 |
| Vegetation | SM_H0647_Nopal | 77 × 51 × 53 | 5, -0, 2 | 1 | 53331 |
| Vegetation | SM_H0636_Acacia | 552 × 455 × 482 | -39, -0, 27 | 3 | 4352 |
| Vegetation | SM_H0958_CoconutPalm | 605 × 613 × 871 | -134, 61, 0 | 2 | 4160 |

## Qualification items (not import failures)

Recorded per manager 2026-09-27. These are checked during qualification against each asset's generator role.

- Heavy meshes: H0014 Building_01 has 2 476 576 triangles and H0016 Building_03 has 822 754; Nanite is off on all 32 (the tool default).
- Pivots: most props sit at the bottom centre within a few cm. Some pivots are off-centre (H0016 by 7.4 m, H0905 by 3.8 m, H0013 by 1.7 m, H0079 streetlight by ~1.2 m, H0958 palm by ~1.5 m); the generator role decides whether that matters.
- Texture fix: manager approved option (a) on 2026-09-27. Copy (never move) each asset's `Textures\*.png` beside its `.fbx` in the Sources folder, record every copy with its SHA-256 in `TEXTURE_COPY_MANIFEST.csv`, re-import into `/Game/Project/Shared/Bank_ME_v2/<Role>/` in the next idle window, and re-measure. This set, `/Game/Project/Shared/Bank_ME`, stays as is and is **superseded by v2**; deleting it needs Aviv's OK.
- Earlier analysis: the textures are only found if they sit where the FBX points (next to the FBX), or if they are imported separately. No MCP texture-import tool exists (AssetTools has no import; StaticMeshTools.import_file handles meshes only).

# v3 — textured re-import (current bank; supersedes v1 `Bank_ME` and the v2 test asset)

Run 2026-09-27 03:13–03:16 local, manager decision (a′). All 108 distinct textures were copied (never moved) into `Staging\ModelBank\ME\Textures\`, the FBX files' own relative path `../../Textures/<name>`; no FBX was edited. Every copy is recorded in `TEXTURE_FLAT_COPY_MANIFEST.csv` with its SHA-256: 108 copies MATCH, and the 42 same-name duplicates across assets have identical content. Target: `/Game/Project/Shared/Bank_ME_v3/<Role>/`, with import_materials, import_textures and combine_meshes all true. Save: explicit-path `save_assets` returned true; the scratch level T2_Orient was untouched.

| Group | StaticMesh | Material | Texture2D |
|---|---:|---:|---:|
| Buildings | 10 | 28 | 47 |
| StreetFurniture | 8 | 5 | 14 |
| Props | 10 | 7 | 19 |
| Vehicles | 1 | 1 | 3 |
| Vegetation | 3 | 6 | 10 |
| **Total** | 32 | 47 | 93 |

**Result:** 32 of 32 imports succeeded. **30 of 32 assets are fully textured.** 45 of 47 materials reference at least one texture asset (dependency lists checked after the save; the material graphs contain `MaterialExpressionTextureSample` nodes).
- **H0636 Acacia:** material `Material__28` has no texture. The FBX names `DesertTreesBillboard_7a01e99a95cf.png`, which exists nowhere in the sources: `LogFbxMaterialImport: Display: Unable to find Texture file C:\Users\USER\Documents\Hergel_Model_Bank_2026-09-24\Models_Only\Textures\DesertTreesBillboard_7a01e99a95cf.png`. This is a source gap for Aviv.
- **H0014 Building_01:** material `standard1` has no texture. The FBX references no texture for it, so the import did not fail on it. Its other 11 materials are textured with 12 textures.
- No other `Unable to find Texture file` line appears in the v3 run.

## v3 importer log (patterns since the v3 start, verbatim; Display level included this time)

- 32 × `FBXImport: Warning: No smoothing group information was found in this FBX scene.  Please make sure to enable the 'Export Smoothing Groups' option in the FBX Exporter plug-in before exporting the file.  Even for tools that don't support smoothing groups, the FBX`
- 3 × `FBXImport: Warning: SM_HN_Building_N has some nearly zero bi-normals which can create some issues. (Tolerance of 1E-4)`
- 3 × `FBXImport: FBX Scene Loading: Found texture name clash, name clash can be wrongly reassign at reimport , texture 'Arabic_Assets_N_AlbedoTransparency_N_eNff2bc3fN' was renamed 'Arabic_Assets_N_AlbedoTransparency_N_eNff2bc3fN_ncl1_1'`
- 2 × `FBXImport: Warning: SM_HN_Building_N has some nearly zero tangents which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: FBX Scene Loading: Found texture name clash, name clash can be wrongly reassign at reimport , texture 'coconut_palm_leaf_3fNdNf8_albedo_cdcdcNbNfbN' was renamed 'coconut_palm_leaf_3fNdNf8_albedo_cdcdcNbNfbN_ncl1_1'`
- 1 × `FBXImport: FBX Scene Loading: Found texture name clash, name clash can be wrongly reassign at reimport , texture 'BN_MN_AlbedoTransparency_Nf2bNe9b4_albedo_d3fNdNf6' was renamed 'BN_MN_AlbedoTransparency_Nf2bNe9b4_albedo_d3fNdNf6_ncl1_1'`
- 1 × `FBXImport: FBX Scene Loading: Found texture name clash, name clash can be wrongly reassign at reimport , texture 'BN_MN_AlbedoTransparency_5eNcNae7' was renamed 'BN_MN_AlbedoTransparency_5eNcNae7_ncl1_1'`
- 1 × `FBXImport: FBX Scene Loading: Found texture name clash, name clash can be wrongly reassign at reimport , texture 'BN_MN_Normal_NfeNdaaN' was renamed 'BN_MN_Normal_NfeNdaaN_ncl1_1'`
- 1 × `FBXImport: FBX Scene Loading: Found texture name clash, name clash can be wrongly reassign at reimport , texture 'BN_MN_AlbedoTransparency_dNdaNc5b' was renamed 'BN_MN_AlbedoTransparency_dNdaNc5b_ncl1_1'`
- 1 × `FBXImport: FBX Scene Loading: Found texture name clash, name clash can be wrongly reassign at reimport , texture 'BN_MN_Normal_Naba1a' was renamed 'BN_MN_Normal_Naba1a_ncl1_1'`
- 1 × `FBXImport: FBX Scene Loading: Found texture name clash, name clash can be wrongly reassign at reimport , texture 'BN_MN_AlbedoTransparency_dNdaNc5b' was renamed 'BN_MN_AlbedoTransparency_dNdaNc5b_ncl1_2'`
- 1 × `FBXImport: FBX Scene Loading: Found texture name clash, name clash can be wrongly reassign at reimport , texture 'BN_MN_Normal_Naba1a' was renamed 'BN_MN_Normal_Naba1a_ncl1_2'`
- 1 × `FBXImport: FBX Scene Loading: Found texture name clash, name clash can be wrongly reassign at reimport , texture 'BN_MN_AlbedoTransparency_dNdaNc5b' was renamed 'BN_MN_AlbedoTransparency_dNdaNc5b_ncl1_3'`
- 1 × `FBXImport: FBX Scene Loading: Found texture name clash, name clash can be wrongly reassign at reimport , texture 'BN_MN_Normal_Naba1a' was renamed 'BN_MN_Normal_Naba1a_ncl1_3'`
- 1 × `FBXImport: Warning: SM_HN_Building_N has degenerate tangent bases which will result in incorrect shading.  MikkTSpace relies on tangent bases and may result in mesh corruption, consider disabling this option.`
- 1 × `LogFbxMaterialImport: Warning: Manual texture reimport and recompression may be needed for T_CracksStreet_normal_Nf5fecN`
- 1 × `FBXImport: Warning: SM_HN_Slum_v_fbx has degenerate tangent bases which will result in incorrect shading.  MikkTSpace relies on tangent bases and may result in mesh corruption, consider disabling this option.`
- 1 × `FBXImport: Warning: SM_HN_Slum_v_fbx has some nearly zero bi-normals which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: Warning: SM_HN_Foodcart_N has some nearly zero tangents which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: Warning: SM_HN_Foodcart_N has some nearly zero bi-normals which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: Warning: SM_HN_Destryoedcar has some nearly zero tangents which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: Warning: SM_HN_Destryoedcar has some nearly zero bi-normals which can create some issues. (Tolerance of 1E-4)`
- 1 × `LogFbxMaterialImport: Display: Unable to find Texture file C:\Users\USER\Documents\Hergel_Model_Bank_N-N-N\Models_Only\Textures\DesertTreesBillboard_7aNeNaNcf.png`
- 1 × `FBXImport: FBX Scene Loading: Found texture name clash, name clash can be wrongly reassign at reimport , texture 'AcaciaLeafs_NdNc5d1_albedo_Ne7b1eNfN' was renamed 'AcaciaLeafs_NdNc5d1_albedo_Ne7b1eNfN_ncl1_1'`
- 1 × `FBXImport: FBX Scene Loading: Found texture name clash, name clash can be wrongly reassign at reimport , texture 'Nopal_Albedo_NeaNfNa_albedo_NcNfNdfNd' was renamed 'Nopal_Albedo_NeaNfNa_albedo_NcNfNdfNd_ncl1_1'`
- 1 × `FBXImport: Warning: SM_HN_Nopal has some nearly zero tangents which can create some issues. (Tolerance of 1E-4)`
- 1 × `FBXImport: Warning: SM_HN_Nopal has some nearly zero bi-normals which can create some issues. (Tolerance of 1E-4)`

## v3 per asset

| Group | Asset | Materials | Textured materials | Textures | Untextured materials |
|---|---|---:|---:|---:|---|
| Buildings | SM_H0907_Arab_x3_fbx | 1 | 1 | 1 | — |
| Buildings | SM_H0906_Arab_x2_fbx | 1 | 1 | 1 | — |
| Buildings | SM_H0905_Arab_x1_fbx | 1 | 1 | 1 | — |
| Buildings | SM_H0904_Slum_v_fbx | 1 | 1 | 1 | — |
| Buildings | SM_H0903_Slum_s_fbx | 1 | 1 | 2 | — |
| Buildings | SM_H0902_Slum_k_fbx | 1 | 1 | 2 | — |
| Buildings | SM_H0016_Building_03 | 9 | 9 | 18 | — |
| Buildings | SM_H0015_Building_02 | 4 | 4 | 8 | — |
| Buildings | SM_H0014_Building_01 | 8 | 7 | 12 | standard1 |
| Buildings | SM_H0013_Building_04 | 4 | 4 | 8 | — |
| StreetFurniture | SM_H0051_Garbagebin | 1 | 1 | 3 | — |
| StreetFurniture | SM_H0094_Woodenpole | 1 | 1 | 3 | — |
| StreetFurniture | SM_H0083_Streetsign_001 | 1 | 1 | 3 | — |
| StreetFurniture | SM_H0082_Streetsign | 1 | 1 | 3 | — |
| StreetFurniture | SM_H0081_Streetpowerbox | 1 | 1 | 2 | — |
| StreetFurniture | SM_H0079_Streetlight | 1 | 1 | 3 | — |
| StreetFurniture | SM_H0060_Metal_Barrier | 1 | 1 | 3 | — |
| StreetFurniture | SM_H0025_Barrier | 1 | 1 | 3 | — |
| Props | SM_H0650_SM_AirConditioner | 1 | 1 | 3 | — |
| Props | SM_H0091_Watertank_001 | 1 | 1 | 3 | — |
| Props | SM_H0090_Watertank | 1 | 1 | 1 | — |
| Props | SM_H0089_Tires | 1 | 1 | 3 | — |
| Props | SM_H0077_Stones_Stack | 1 | 1 | 3 | — |
| Props | SM_H0059_Grill_ | 1 | 1 | 3 | — |
| Props | SM_H0058_Gaz | 1 | 1 | 3 | — |
| Props | SM_H0046_Foodcrate | 1 | 1 | 3 | — |
| Props | SM_H0043_Foodcart_001 | 1 | 1 | 3 | — |
| Props | SM_H0034_Cart | 1 | 1 | 3 | — |
| Vehicles | SM_H0039_Destryoedcar | 1 | 1 | 3 | — |
| Vegetation | SM_H0647_Nopal | 1 | 1 | 2 | — |
| Vegetation | SM_H0636_Acacia | 3 | 2 | 4 | Material__28 |
| Vegetation | SM_H0958_CoconutPalm | 2 | 2 | 4 | — |

Measurements for v3 (bounds, pivots, slots, triangles) are in `IMPORT_RESULTS_v3.csv` / `.json`; the geometry is identical to v1. Earlier sets, recorded as superseded test imports, stay in place until Aviv decides: `/Game/Project/Shared/Bank_ME` (v1, untextured) and `/Game/Project/Shared/Bank_ME_v2/Vegetation/SM_H0958_CoconutPalm` (+ Original_Submesh_0/1; not saved by Track A). The 150 texture copies beside each FBX (`TEXTURE_COPY_MANIFEST.csv`) are redundant and stay in place until removal is approved.
