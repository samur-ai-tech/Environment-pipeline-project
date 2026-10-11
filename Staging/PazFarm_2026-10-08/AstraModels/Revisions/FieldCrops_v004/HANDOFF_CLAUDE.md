# Karmei Yosef farmland — FieldCrops v004

**Offline Blender delivery complete. Native application and acceptance are pending.**

Follows `HANDOFF_ASTRA_FieldCrops_v004.md`. All new files are inside `AstraModels/Revisions/FieldCrops_v004/`. Start with `INDEX.html`, then `Previews/Distance/INDEX.html`. The supplied wide farm reference was sufficient. Earlier deliveries are preserved.

## Models

| Base model | Detailed triangles | Authored lowest triangles |
|---|---:|---:|
| `SM_PazFarm_VineRow_3m_A` | 36,802 | 294 |
| `SM_PazFarm_VineRow_3m_B` | 37,762 | 294 |
| `SM_PazFarm_VineRow_3m_C` | 38,722 | 294 |
| `SM_PazFarm_Olive_A` | 94,212 | 1,424 |
| `SM_PazFarm_Olive_B` | 94,212 | 1,424 |
| `SM_PazFarm_Olive_C` | 94,212 | 1,424 |
| `SM_PazFarm_Olive_Young` | 94,212 | 1,424 |
| `SM_PazFarm_GrassClump_A` | 2,072 | 80 |
| `SM_PazFarm_GrassClump_B` | 2,396 | 80 |
| `SM_PazFarm_GrassClump_C` | 2,744 | 80 |
| `SM_PazFarm_GrassClump_D` | 2,908 | 80 |
| `SM_PazFarm_GrassClump_E` | 2,152 | 80 |
| `SM_PazFarm_GrassClump_F` | 2,808 | 80 |
| `SM_PazFarm_GrassPatch_2m_A` | 7,420 | 80 |
| `SM_PazFarm_GrassPatch_2m_B` | 7,420 | 80 |

There are 15 base models, 30 separate FBXs, three editable Blender scenes and 49 PBR maps. Exact dimensions, pivots, material slots, paths and hashes are in `MANIFEST.json`.

## Lowest LOD assignment

**Each base FBX contains only its detailed mesh.** Explicitly assign the matching `_LOD3.fbx` as the final custom LOD, or bind that mesh to the operator's existing far-instance route. The filename does not automatically install an LOD chain. Preserve its material slot order, including unused slots. Do not replace it with automatic reduction or a billboard.

The brief specifies an always-loaded Instancing HLOD using each item's lowest LOD with Nanite disallowed. These files supply solid conventional geometry for that existing route. No HLOD configuration or native imports were performed. Verify which geometry is actually drawn at distance under the operator's current ownership.

## Vine rows

Three 3 m modules extend from Y=0 to Y=3, with Z up and the pivot at ground centre of the start end. Place successive modules at +3 m along their local Y axis. Use 2.5–3 m row pitch; the preview uses 2.75 m. Each tile contains two vines 1.5 m apart and one post at its start. Mixed A/B/C sequences use the same end profile within each LOD. The detailed inner band is 0.48 m wide with a 1.70 m top; the low band expands to 0.53 m / 1.78 m to replace the outer leaves. The shared join plane may contain coincident end-cap faces; there is no positive-volume tile overlap.

LOD0 combines solid vine leaves, shoots, cordons, trunks, wires and an inner green hedge. The authored low mesh retains the hedge and support line as closed geometry. `Reports/vines_v004_qa.json` contains seam, pitch and block checks. The final exposed row end can be finished by the receiving operator if a terminal trellis support is required; repeating tiles themselves have one start post each.

## Olives

Mature A/B/C target 4.5 / 5.5 / 6.5 m heights and 4–6 m crowns; Young targets 2 m. Twisted branching trunks, narrow silvery leaves and irregular open crown groups distinguish these from the earlier broadleaf/citrus trees. Keep the olive palette grey-green, with lighter leaf undersides. Each lowest LOD retains the actual trunk and opaque crown groups, with branch gaps and variant-specific shape. Use 6–7 m orchard spacing.

The extra 100 m frames include the previous Lemon and Avocado sources under identical lighting, camera FOV and distance at their actual sizes. Those sources were read only. See `Reports/VISUAL_REVIEW.json` for the assessed comparison and any limits.

## Field grass

Clumps A–D are predominantly dry straw; E/F are greener. The two 2 m patches provide denser cover. Detailed meshes use opaque blades, seedheads and a little broadleaf variation over compact backing tufts. Their authored lowest LODs are small closed pointed volumes, each within 20–80 triangles, including the patches. No per-blade opacity mask is needed.

The 10 × 10 m preview uses 100 deterministic clump placements and four patches. Both LODs use identical placements and rotations. `Reports/grass_preview_placements.json` records the exact arrangement; it is preview data, not a native placement change. Individual clumps occupy very few pixels at 150 m; judge the retained field colour using the scatter as well as the individual views. Triangle budgets are verified; native draw-call and frame-time costs are not measured.

At 150 m the final scatter retains 75.5% of detailed geometry coverage; patches A/B retain 85.3% / 82.3%. Patch silhouette-overlap flags remain because 80-triangle tufts replace individual blades. This is a reviewed simplification, documented in `Reports/VISUAL_REVIEW.json`. The low mounds look coarse at 15–50 m; preserve the detailed meshes near the viewer and inspect the actual native transition.

## Materials and import

- Metres, FBX −Y forward / Z up, ground pivots at origin. Apply the established metre-to-Unreal import conversion once; do not add a second ×100 scale.
- Opaque materials, alpha 1. Foliage is two-sided. No wind or collision. Slot names/order match each detailed/lowest pair, including unused slots.
- BaseColor is sRGB; Normal and ORM are non-colour. ORM channels are R=AO, G=roughness, B=metallic. Normals are OpenGL +Y; apply the project's established green-channel conversion when building Unreal materials.
- Retain the hull/tuft material assignments and matte roughness at distance. FBX does not automatically recreate all custom PBR connections. Do not inherit old citrus colours or opacity masks.

## Evidence and checks

`Reports/VALIDATION.json` records fresh imports of all 30 FBXs, compared with reopened source scenes: dimensions, pivots, triangles, UV0, finite geometry, solid alpha, closed lowest-LOD surfaces, matching slots and relative texture paths. All 669 baseline files match the original hashes (`Reports/ORIGINALS_UNCHANGED.json`).

There are 154 fixed-camera frames: vines at 2/30/150/500 m including a 5-row × 10-tile block; olives at 5/50/100/300/1000 m plus top-down; every grass asset and the scatter at 2/15/50/150 m; and two 100 m legacy comparison frames. Both detailed and lowest meshes are rendered directly. Full frames remain 1920 × 1080 with a 60° horizontal FOV, fixed lighting and exposure. Close frames may crop; separate hero previews show whole models. Magnified diagnostic crops are clearly labelled.

Every distance frame binds to the source scene and texture hashes captured before rendering. `Reports/distance_validation.json` contains exact cameras, geometry-only alpha coverage and colour comparisons. `Reports/VISUAL_REVIEW.json` records the review of any numerical flags. These are offline Blender measurements, not proof of Unreal visibility, streaming, material appearance or HLOD selection. Verify the same native distance views, ground contact and actual final LOD assignment before scoped named saves and reopen.

Editable dimensions, seeds, palettes and construction settings remain in the three family build scripts. Rebuilding a family invalidates its preview/QA hashes; rerender and revalidate before use.

## Temporary cache

`Temp/DistanceCache/` contains approximately 2.06 GB of optional decoded image arrays. These are not needed for import or viewing the PNG evidence and are excluded from the delivery manifest. Automatic approval review blocked the attempted cache cleanup with the reason “blocked by policy”; the files were retained.
