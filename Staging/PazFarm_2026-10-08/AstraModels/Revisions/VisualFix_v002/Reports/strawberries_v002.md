# Strawberry bed v002 — offline revision ready

`SM_PazFarm_StrawberryBed_4m` keeps its existing name, 0.8 × 4 m footprint, 0.25 m mound, ground/end pivot and +Y 4 m tile pitch. Replace the existing asset in the operator's authorized import scope; retain the existing 449 west / 314 triangle instances and their row direction/spacing.

- **Fuller crowns:** 32 plants instead of 24; six trifoliate stems per plant instead of four. Broader, lower-tessellation leaflets give 576 real geometric leaves within the original footprint. Red berries and white flowers remain.
- **Measured cover:** top-down geometric leaf coverage over the bed increased **24.55% → 54.53%** using the same 240 × 1200 raster-union method. This is an offline geometry measurement, not proof of Unreal distance visibility.
- **Softer mulch:** dusty charcoal BaseColor, roughness **0.79**, specular **0.22**, and wrinkle normals reduced to **20%** of the original amplitude. Reduced normal amplitude is baked into the new map; use normal strength 1 when reconstructing it.
- **Compatible placement:** actual mesh **0.8 × 4 × 0.424107 m**, identity scale, pivot **(0,0,0)** at the ground centre of its start end. Tile along Blender +Y, with the unchanged FBX `-Y` forward / Z up export convention and FBX Units Scale. Do not widen the plants to imitate dusty plot shoulders; those belong to the separate ground correction.

Deliverables: `Blend/Strawberry.blend`, `FBX/SM_PazFarm_StrawberryBed_4m.fbx`, 26 original 1024² material maps, `Scripts/build_strawberries_v002.py`, and individual, detail and labelled comparison previews in `Previews/`. The individual and comparison previews include a 1.8 m human scale figure. All artwork is original procedural CC0; no reference-image pixels are used as textures. The unchanged low tunnel remains in the original delivery.

**Offline verification passed:** a second Blender 5.2.2 process reopened the source, then imported the FBX into an empty scene. Both have **19,624 triangles / 20,000 budget**, UV0, finite geometry/UVs, zero zero-area triangles, upward leaf normals and matching dimensions. The two mound end profiles match exactly; no vertex exceeds the 0.8 × 4 m footprint. Relative source texture paths resolve, with all loaded textures at 1024². Details: `strawberries_v002_qa.json`; manifest fragment: `strawberries_v002.json`.

**For the Unreal operator:** reimport this mesh plus revised mulch BaseColor/Normal/ORM into the currently owned package scope, preserving material slots. Leaf silhouettes are geometry with solid white opacity: retain two-sided leaves and opacity 1. ORM is non-sRGB, R=AO/G=roughness/B=metallic. Normal maps use OpenGL +Y, so apply the established Unreal green-channel conversion. FBX alone does not rebuild these material connections or the mulch specular setting. Recheck far-distance leaf visibility, all tile seams, clipping at row ends and ground contact in the actual farm view.

No Unreal import, material edit, map change or native visual acceptance was performed. All writes for this revision are inside `AstraModels/Revisions/VisualFix_v002/`; original deliverables are preserved.
