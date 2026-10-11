# Olive family v004

Four original olive variants: A 4.5 m tall / 4.7 m wide, B 5.5 / 5.35 m, C 6.5 / 5.95 m, and Young 2 / 1.7 m. The generator's `CONFIG` keeps these dimensions editable. All objects have the trunk-base origin, metre units and applied transforms.

Each LOD0 is 94,212 triangles: 7,200 closed, bowed lanceolate leaf volumes with grey-green upper faces and paler underside faces; 18 recessed opaque crown clumps; a gnarled split trunk and support branches. Crown gaps and thin leaf outlines distinguish the family from the dense, saturated citrus trees. Mature B/C leaf widths scale with crown size to keep the inner backing concealed.

Each LOD3 is 1,424 triangles. It uses the corresponding 18 closed clumps with four latitude bands, plus the split trunk and supporting limbs. Clump centers and crown gaps follow LOD0; the low mesh is not a billboard. Hull diffuse uses a 0.68 multiplier in linear colour space to compensate for the reduced self-shadowing. The initial A comparison at 100/300/1,000 m passed the parent's colour/coverage diagnostic; the final smoother hulls and all four variants are supplied for the parent's final distance suite.

Both LODs keep these four material slots in the same order: `M_PazFarm_Olive_Bark`, `M_PazFarm_Olive_LeafTop`, `M_PazFarm_Olive_LeafUnderside`, `M_PazFarm_Olive_CrownHull`. The leaf slots remain present, unused, in LOD3. All foliage is opaque and two-sided, alpha is 1, and there is no wind or collision. The twelve original 1K PBR textures use sRGB BaseColor, OpenGL +Y Normal and Non-Color ORM.

`olives_source_readback.json` records a fresh Blender source readback: all eight meshes pass dimensions, ground origin, transforms, triangle budgets, UV0, finite geometry, zero degenerate triangles and closed-component checks. All twelve textures pass dimensions, colour spaces and solid alpha. The parent provides independent FBX round trips and final fixed-camera distance evidence. No Unreal operation was performed.
