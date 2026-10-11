# Paz Farm — StrawberryBeds v005

**Offline Blender delivery complete. Native import, placement and visual acceptance remain with the Unreal operator.**

The previous continuous green block is replaced with young, separate plants on dusty charcoal mulch. Real planting photographs were gathered, retained and reviewed before modelling. Start with `INDEX.html` and `Previews/REFERENCE_COMPARISON.png`.

## Delivered models

| Model | Detailed triangles | Authored lowest triangles |
|---|---:|---:|
| `SM_PazFarm_StrawberryBed_4m_A` | 35,370 | 240 |
| `SM_PazFarm_StrawberryBed_4m_B` | 32,920 | 240 |
| `SM_PazFarm_StrawberryBed_4m_C` | 35,100 | 240 |
| `SM_PazFarm_StrawberryBedEnd` | 1,962 | 257 |

Eight FBXs, one editable `Blend/StrawberryBeds.blend`, 24 original PBR maps, three regular variants and a separate terminal cap. The regular modules have solid serrated trifoliate leaves, real film openings with exposed soil, rounded/sloped shoulders, soil-covered edges and no close-range canopy hull. There is no fruit or flower. The repeated modules have no short-end walls.

## Placement contract

- Regular tile: **4 m along local +Y, Y=0..4**, pivot exactly `(0,0,0)` at ground centre of the start end. **Minimum Z=-0.15 m is a hidden skirt, not the placement pivot.** Do not recenter the mesh to its minimum bound.
- Bed top is approximately 0.8 m wide and 0.25 m above the pivot, with sloping sides to approximately 1.1 m base width. Young plants rise above that top. Use the actual measured bounds in `MANIFEST.json`; below-ground depth is included in total bound height.
- Mix A/B/C at **1.7 m row centres**. Tilt each tile to the local ground, then place the next start pivot at the previous tile's transformed `(0,4,0)` endpoint. A 3% longitudinal slope uses `atan(0.03)=1.718358 degrees`; simply adding 4 m in horizontal Y after rotation introduces gaps.
- The previews use 50 regular tiles: 10 rows × 5 tiles, 20 m surface length. Both LODs share exactly the same placement. Twenty optional caps close both row ends. `Reports/slope_preview_placements.json` records the transforms.
- `SM_PazFarm_StrawberryBedEnd` joins with its Y=0 edge at the row's final Y=4 endpoint. For the beginning of a row, rotate the cap 180 degrees about the tile's local up axis so it extends away from the start. Apply the terrain pitch to that orientation as well.
- A modest sink can use the skirt to hide contact gaps. The skirt does not conform rigid tiles to curved terrain, nor fix incorrect tile tilt. Planar-slope evidence does not prove arbitrary native terrain placement.

## Lowest LOD: install explicitly

Each base FBX contains only its detailed mesh. **Assign its matching separate `_LOD3.fbx` as the final custom LOD or as the geometry used by the existing far-instance route.** File naming alone does not install an LOD chain. The lowest mesh is a film-coloured mound with sparse muted green detail, without a bright green backing band or billboard.

The brief's 60 m–4 km route uses always-loaded Instancing HLOD with Nanite disallowed. The supplied lowest geometry is conventional opaque geometry for that route. Preserve it instead of substituting automatic reduction. No HLOD, streaming or native project settings were changed here.

## Materials

- Selected film: **dark charcoal-black**, based on the Huelva planting photograph. The white UC ANR film photograph informed shape and planting scale only. `Reports/REFERENCES.md` gives originals, credits and limits. Photos are references, not model textures.
- Use all supplied material slots in their recorded order on both LODs, including unused roles. In particular, keep the distant mulch role assigned to the low mesh; do not inherit v003's green canopy material.
- BaseColor is sRGB; Normal and ORM are non-colour. ORM is R=AO, G=roughness, B=metallic. Normal maps use OpenGL +Y; use the project's established green-channel conversion for Unreal.
- All materials and leaf geometry are opaque, with solid alpha. Film roughness is at least 0.85 and specular is low. No wind, collision or opacity masks. FBX does not recreate the full custom PBR graph automatically.
- Metres, FBX -Y forward / Z up. Apply the established metre-to-Unreal conversion once, without adding another ×100.
- FBXs retain the source polygons and corner normals. The budgets above count their evaluated triangles. Exporter-side triangulation changed shading on small stems, so it is disabled; final fresh imports and a focused source/export image comparison verify the corrected shading. Preserve imported normals and inspect native triangulation/shading during import.

## Appearance and distance evidence

`Previews/Distance/INDEX.html` contains 33 source-render frames. Each A/B/C tile is shown at 1 and 3 m with both LODs. The mixed 3% slope block is shown at 15/60/150/500 m with both LODs and soil-ground views. There is an extra 4 km geometry-only stress view, a portrait reference-angle render and two seam views.

Full comparison frames are 1920 × 1080. Singles use 85° horizontal FOV and 45° elevation; the block uses 110° and 70° elevation to keep the whole requested field visible at 15 m. Distances are camera-to-target slant distances. No distance frame is auto-fitted. The 1 m views intentionally show local detail; fitted previews show the entire module. The reference render is 800 × 1200. Lighting/exposure remain fixed within the comparison suite.

| Block distance | Detailed coverage px | Lowest coverage px | Lowest/detailed area | Lowest luma change |
|---|---:|---:|---:|---:|
| 60 m | 27089.31 | 27075.98 | 1.000 | -0.85 |
| 150 m | 4333.40 | 4332.16 | 1.000 | -0.81 |
| 500 m | 388.37 | 388.12 | 0.999 | -0.48 |
| 4,000 m | 6.45 | 6.45 | 1.000 | +1.05 |

Coverage is alpha-weighted equivalent opaque pixels with holdout ground hiding the skirt and excluding cast shadows. Lit sRGB measurements are from saved PNG bytes, not BaseColor swatches. Magnified crops are labelled and never replace the full frames. At 4 km the entire block occupies very few pixels; individual stripe separation cannot be guaranteed at that resolution/FOV. Check actual native material lighting, anti-aliasing and lowest-LOD selection in the operator's distance captures.

The photo comparison is a shape and planting-stage reference, not a matched-lighting reproduction. The model is darker, more regular and smoother than the bright Huelva photograph; its young leafy plugs follow the separate UC ANR references. Procedural microdetail remains simpler than real dusty film and clods. The optional cap has a different film UV phase at its join; this is recorded separately from its continuous geometry.

## Verification and retained evidence

`Reports/validation_v005.json` contains independent fresh-process source/FBX checks, dimensions, pivot/skirt, triangle budgets, material order, UV0, finite geometry, opaque textures and all directed variant joins. Intentional open film/soil ends and planting openings are distinguished from accidental boundary edges; solid leaves remain closed.

`Reports/distance_validation.json` binds every frame to source and texture hashes recorded before rendering. `Reports/INDEPENDENT_VISUAL_REVIEW.json` records the photo comparison and near/far review. `Reports/ORIGINALS_UNCHANGED.json` confirms all 1,371 earlier model-delivery files match their pre-work hashes. The broader 1,462-file farm snapshot contains one changed placement report outside AstraModels (`RESULT_CLONE_V2_2026-10-11.md`); this task left it untouched and records its before/current hashes separately.

`Reports/strawberries_v005_fbx_normal_comparison.json` records the final export appearance comparison. Reports named `probe`, `draft` or `before_fix` preserve intermediate diagnostics and do not supersede the final validation report.

Editable parameters, seeds, dimensions and palettes remain in `Scripts/build_strawberries_v005.py`. A rebuild invalidates current export, preview and QA hashes; rerender and revalidate before handoff. Compressed preview caches under `Temp/` are optional and excluded from the asset manifest.

All writes were confined to `AstraModels/Revisions/StrawberryBeds_v005/`. No Unreal, Content, maps, bank, Houdini or git action was performed.
