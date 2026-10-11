# Paz Farm / Karmei Yosef — VisualFix v003

**Offline Blender delivery. No Unreal import, HLOD rebuild, map save or native acceptance was performed.**

This revision follows `Staging/PazFarm_2026-10-08/HANDOFF_ASTRA_VisualFix_v003.md` dated 2026-10-10. The supplied six distance captures were reviewed. Work is confined to `AstraModels/Revisions/VisualFix_v003/`; older deliveries remain unchanged. Start with `INDEX.html` and the distance gallery in `Previews/Distance/INDEX.html`.

## Meshes and the lowest-LOD contract

| Base mesh | LOD0 triangles | Lowest triangles | Separate lowest-LOD FBX |
|---|---:|---:|---|
| `SM_PazFarm_AleppoPine_A` | 113,466 | 1,642 | `FBX/SM_PazFarm_AleppoPine_A_LOD3.fbx` |
| `SM_PazFarm_AleppoPine_B` | 113,466 | 1,642 | `FBX/SM_PazFarm_AleppoPine_B_LOD3.fbx` |
| `SM_PazFarm_AleppoPine_C` | 113,466 | 1,642 | `FBX/SM_PazFarm_AleppoPine_C_LOD3.fbx` |
| `SM_PazFarm_StrawberryBed_4m` | 10,422 | 282 | `FBX/SM_PazFarm_StrawberryBed_4m_LOD3.fbx` |

**The base FBX contains LOD0 only.** The `_LOD3` files are explicit low-detail geometry, not billboard cards or automatically linked LODs. Import each matching `_LOD3.fbx` as the base mesh's final custom LOD, or explicitly bind that low mesh to the receiving operator's far-instance path. Record the resulting native LOD index and verify the actual mesh drawn. The suffix describes its intended role; a separately imported asset alone does not update the original mesh's LOD chain. Do not allow automatic reduction or a billboard to replace this authored final LOD.

The operator's brief specifies always-loaded Instancing HLOD with Nanite disallowed and each instance using the lowest LOD. Apply these files to that existing route under the operator's current ownership. This packet neither creates nor changes that system. Near-tree Nanite and far conventional rendering must be verified separately.

## Aleppo pine

Three original *Pinus halepensis* variants target heights 8 / 11 / 15 m and crown widths 6 / 8 / 10 m. The asymmetrical leaning trunks support irregular, flattened clump crowns. LOD0 uses solid needle geometry and opaque inner crown clumps; lowest LOD retains a trunk and solid crown volumes. No masked needle cards, wind or collision are included. Details and editable parameters are in `Scripts/build_pines_v003.py` and `Reports/pines_v003.json`.

Use the three material roles: bark, opaque two-sided needles, and opaque crown hull. Keep needle and hull colours closely matched, dark grey-olive. The far crown depends on its hull material, so do not inherit a pale default or masked store-pine material on it. Use the authored final mesh for every pine variant rather than reusing one generic silhouette.

## Strawberry bed

`SM_PazFarm_StrawberryBed_4m` retains the 0.8 × 4 m tile, ground/start-end pivot and +Y tile direction. Replace the current mesh in place and retain all 763 existing placements. Its closed continuous opaque green canopy sits beneath fewer, larger rosettes. Dark mulch has high roughness and reduced specular/normal response. The lowest mesh keeps a continuous green ridge over the mulch strip, with no dependence on tiny individual leaves.

LOD0 and lowest LOD share the same tile envelope and compatible end profiles. Preserve all instance positions, rotations and scale; do not widen the mesh, move its pivot or offset successive tiles. `Scripts/build_strawberries_v003.py` contains editable dimensions, canopy height/colour, rosette count and mulch settings. Component construction and QA are in `Reports/strawberries_v003.json`.

The strawberry lowest mesh deliberately retains all nine material slots: visible mulch is **slot 0 `M_PazFarm_StrawberryMulch_v003`** and the green ridge is **slot 8 `M_PazFarm_StrawberryCanopy_v003`**. Do not remap the canopy to slot 1 simply because only two surface roles are used.

## Import and material settings

- Source units are metres, pivot at ground origin (bed at the centre of its start end), FBX −Y forward / Z up with FBX Units Scale. Reuse the established metre-to-Unreal import conversion once. Fresh round-trips check size and pivot; do not add another ×100 scale.
- Use **Opaque** foliage and hull materials, alpha 1, two-sided needles/leaves. Do not connect the old opacity masks or substitute translucent foliage. No wind animation or displacement is required.
- BaseColor uses sRGB. Normal and ORM use non-colour data; ORM is R=AO, G=roughness, B=metallic. Normals use OpenGL +Y; apply the project's established Unreal green-channel conversion. Preserve the authored dark colours and matte roughness on both LODs. FBX does not reconstruct these custom material connections automatically.
- Map each low mesh's material slots by its own recorded names. Low meshes use fewer surface roles than the detailed meshes. Check the material remap after assigning a custom LOD; a wrong remap can turn a canopy into bark or plastic.

## Distance evidence and acceptance

`Previews/Distance/INDEX.html` contains actual perspective frames and labelled magnifications. `Reports/distance_validation.json` records camera distances, resolution, FOV, fixed light/exposure, alpha silhouette and colour measurements. `Reports/distance_notes.md` explains the comparisons. Close fixed-distance views can crop a tall tree or a multi-bed block; fitted hero previews are provided separately. Far frames are never auto-framed to disguise their projected size.

Pine previews cover 5, 50, 300 and 1,000 m, plus top-down inspection. Bed previews cover a single tile and ten tiles at 2, 30, 150 and 500 m. Lowest LODs are rendered directly in Blender without Nanite. The ten-tile block uses five parallel rows and two end-to-end tiles per row, at 5.48 m row pitch. All distances and targets are disclosed in the camera receipt.

The geometry and offline images demonstrate retained solid crowns/ridges. They do not guarantee a particular pixel footprint under every native FOV, screen resolution, exposure, mip filter, anti-aliasing or atmosphere. At kilometre distances the projected tree is small; preserve that honest scale in native review. Native acceptance requires the same provided forest and strawberry camera views, explicitly showing the authored lowest meshes in the always-loaded non-Nanite path. Check no disappearance, no pale material swap, no billboard, complete trunks/crowns, continuous dark-green rows, ground contact and no duplicate instances before named saves/reopen.

## Verification and preservation

`Reports/VALIDATION.json` checks all eight fresh FBX imports and both retained Blender sources: dimensions, pivots, triangle budgets, UV0, finite geometry/normals/UVs, material order, solid texture alpha, relative texture paths and closed manifold lowest-LOD surfaces. Component QA includes construction and tile seam checks. `Reports/ORIGINALS_UNCHANGED.json` verifies 430 original files against their pre-work hashes. `MANIFEST.json` includes LOD pairings and hashes of deliverables.

No forest placement, farm ground, fence, barn, bank, existing map, Content asset, Houdini graph or git state is changed by this revision. The optional young pine is omitted; the three requested mature variants are delivered.
