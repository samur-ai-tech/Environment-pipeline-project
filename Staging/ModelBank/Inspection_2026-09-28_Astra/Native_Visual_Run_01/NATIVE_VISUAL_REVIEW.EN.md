# GazaRimal — Findings from Viewing in Unreal, Round 01

Date: 2026-09-28. New operator: Astra, thread `01a0e820-c6d4-7702-8e7b-55fd20f9b020`.

**23 assets were opened and viewed in the current project, from 12 families and seven packages.** All nine ASTRA_VISUAL_PREP assets and 14 more were inspected. This is a partial round; 907 records already in the project and 285 external records have not been viewed here. All 1,215 records remain in the catalog.

[measured: preflight.json; release_check.json] After confirming there was no conflicting editor process, ownership was taken and PID 33844 was opened with `/Engine/Maps/Templates/Template_Default`. Only existing assets were inspected. The editor was closed through the UI without saving and ownership was released at 17:56:29+03:00. No Unreal/Houdini/HARS process remained. The measurement ownership file retained the same SHA-256. Comparison of 5,989 Content files before/after found no path, size, or write-time difference. This is a metadata comparison, not a full Content hash. No measurement file had a write time later than acquisition of the lock.

## Evidence limits

- `[measured]` below means what was visible in the asset view or data panel under built-in lighting. `[inference]` marks a proposed role and fit for GazaRimal.
- An asset view is not scene placement, Houdini connection, generation, qualification, or acceptance. `visually_verified` remains `no` for the scene/output gate; the new `native_preview_state=observed_partial` records actual viewing in the project.
- Geometric figures are LOD0. Approx Size was copied as a string without assuming units; existing cm fields were retained. Contact offset, pivot, and front/up mapping were not measured. Front/Back are camera names, not semantic facade direction.
- A collision-primitives count is not a collision test. LOD transition, runtime performance, Unity, and Houdini tests were not run. Assembly seams and BG1 were not checked.
- For Palm01, an LOD0–3 menu was observed; an attempt to select LOD3 left Auto/LOD0. There is no evidence that LOD3 was inspected. Motion between images was visible, but no wind test was conducted.
- A Ray Tracing memory notice appeared after a series of views: 83.76 MiB of 400 MiB, exceeding 20% of the budget. This is a session message, not a proven cost of any particular asset or a benchmark.
- Raw files include loading states, menus, and unsuccessful attempts to change angles. Names such as `43_Palm01_LOD3` describe intent, not proof of outcome. `native_receipts.json` defines valid observations; `native_evidence_manifest.json` links images and hashes.

## Findings by asset

### 1. SM_H0907_Arab_x3_fbx

ID: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0907_Arab_x3_fbx`

Unreal: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0907_Arab_x3_fbx.SM_H0907_Arab_x3_fbx`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0907_Arab_x3_fbx.uasset`

[measured] A whole structure with a broad dome, blue-gray doors, and ornate arches. Color boundaries are visible on the dome.

[inference] review: a special structure or pavilion; exact local use is unknown.

[measured] LOD0: **3,302 triangles**, 4,835 vertices; UV channels 2; material slots 1; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `1,369 x 1,368 x 1,560`.

Rights: `owner_confirmed_for_technical_qualification`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of SM_H0907_Arab_x3_fbx](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/06_H0907_whole__1.jpg)

### 2. SM_H0014_Building_01

ID: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0014_Building_01`

Unreal: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0014_Building_01.SM_H0014_Building_01`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0014_Building_01.uasset`

[measured] A whole building with three balcony rows over a shop floor, green shutters, arches, air conditioners, and dishes. Arabic writing and graffiti are visible; the text was not transcribed.

[inference] review: residential above commercial in an older, ornate appearance. 2,476,576 LOD0 triangles require a cost test, without an automatic rejection threshold.

[measured] LOD0: **2,476,576 triangles**, 2,775,920 vertices; UV channels 4; material slots 8; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `1,728 x 2,095 x 2,119`.

Rights: `owner_confirmed_for_technical_qualification`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of SM_H0014_Building_01](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/14_H0014_perspective__1.jpg)

### 3. SM_wall_windows_4x4_01

ID: `current_ModularCourtyard__Meshes__SM_wall_windows_4x4_01`

Unreal: `/Game/ModularCourtyard/Meshes/SM_wall_windows_4x4_01.SM_wall_windows_4x4_01`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ModularCourtyard\Meshes\SM_wall_windows_4x4_01.uasset`

[measured] Worn ochre plaster wall with two closed windows, sills, and exposed brick patches. The opposite side is a solid wall.

[inference] keep as a candidate for a closed exterior facade segment; it is not a through-opening.

[measured] LOD0: **656 triangles**, 916 vertices; UV channels 2; material slots 4; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `54 x 400 x 400`.

Rights: `acquisition_record_terms_unverified`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of SM_wall_windows_4x4_01](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/21_Courtyard_whole__1.jpg)

### 4. store_front_shutters_4x1_a

ID: `current_ModularBuildingSet__Meshes__Store_fronts__store_front_shutters_4x1_a`

Unreal: `/Game/ModularBuildingSet/Meshes/Store_fronts/store_front_shutters_4x1_a.store_front_shutters_4x1_a`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ModularBuildingSet\Meshes\Store_fronts\store_front_shutters_4x1_a.uasset`

[measured] A closed, perforated, flat metal shop shutter. It was not visible from Back after framing.

[inference] keep as a candidate inset with a supporting wall; it is not a freestanding door or open passage.

[measured] LOD0: **16 triangles**, 32 vertices; UV channels 2; material slots 2; collision primitives 0; Nanite unchecked. Approx Size (unit not labeled): `0 x 600 x 384`.

Rights: `acquisition_record_terms_unverified`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of store_front_shutters_4x1_a](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/24_Storefront_whole__1.jpg)

### 5. SM_H0051_Garbagebin

ID: `current_Project__Shared__Bank_ME_v3__StreetFurniture__SM_H0051_Garbagebin`

Unreal: `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/SM_H0051_Garbagebin.SM_H0051_Garbagebin`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\StreetFurniture\SM_H0051_Garbagebin.uasset`

[measured] A street bin clad in brown slats with a light frame, with bottles and trash built into its top.

[inference] review as a littered variant; do not repeat the same bottles along every street.

[measured] LOD0: **5,180 triangles**, 4,776 vertices; UV channels 2; material slots 1; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `29 x 34 x 74`.

Rights: `owner_confirmed_for_technical_qualification`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of SM_H0051_Garbagebin](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/28_Garbagebin__1.jpg)

### 6. SM_H0636_Acacia

ID: `current_Project__Shared__Bank_ME_v3__Vegetation__SM_H0636_Acacia`

Unreal: `/Game/Project/Shared/Bank_ME_v3/Vegetation/SM_H0636_Acacia.SM_H0636_Acacia`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Vegetation\SM_H0636_Acacia.uasset`

[measured] After loading, opaque white cards and black angular foliage patches remained.

[inference] Review is blocked for use by the visual failure. Material/transparency as the cause is only an inference; no repair was performed.

[measured] LOD0: **4,352 triangles**, 2,562 vertices; UV channels 2; material slots 3; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `552 x 454 x 481`.

Rights: `owner_confirmed_for_technical_qualification`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of SM_H0636_Acacia](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/32_Acacia_whole__1.jpg)

### 7. SM_H0082_Streetsign

ID: `current_Project__Shared__Bank_ME_v3__StreetFurniture__SM_H0082_Streetsign`

Unreal: `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/SM_H0082_Streetsign.SM_H0082_Streetsign`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\StreetFurniture\SM_H0082_Streetsign.uasset`

[measured] A red octagonal sign with a white human figure on a post; not a street-name sign.

[inference] review until the symbol's meaning and local fit are established.

[measured] LOD0: **420 triangles**, 569 vertices; UV channels 2; material slots 1; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `40 x 7 x 122`.

Rights: `owner_confirmed_for_technical_qualification`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of SM_H0082_Streetsign](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/34_Streetsign_loaded__1.jpg)

### 8. M_Concrete_Poured

ID: `current_StarterContent__Materials__M_Concrete_Poured`

Unreal: `/Game/StarterContent/Materials/M_Concrete_Poured.M_Concrete_Poured`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\StarterContent\Materials\M_Concrete_Poured.uasset`

[measured] Rough light-gray concrete appears on the preview sphere. BaseColor, Roughness, and Normal connections are visible in the graph.

[inference] keep as a generic concrete candidate; tiling and color on a real surface were not checked.

[measured] Surface; Opaque; Default Lit; Two Sided unchecked. [not run] Scale/tiling, layers, surface and runtime test.

Rights: `unverified`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of M_Concrete_Poured](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/36_Concrete_preview__1.jpg)

### 9. M_Master_CL_Landscape

ID: `current_FC_Coastal_Landscape__Landscape__M_Master_CL_Landscape`

Unreal: `/Game/FC_Coastal_Landscape/Landscape/M_Master_CL_Landscape.M_Master_CL_Landscape`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\FC_Coastal_Landscape\Landscape\M_Master_CL_Landscape.uasset`

[measured] A dark brown-gray mottled surface appears on the sphere. The graph uses Material Attributes; a RuntimeVirtualTextureEnable? switch displays False.

[inference] review as a material system; there is no evidence of Landscape-layer blending or Houdini masks.

[measured] Surface; Opaque; Default Lit; Use Material Attributes checked; Two Sided unchecked. [not run] Scale/tiling, layers, surface and runtime test.

Rights: `acquisition_record_terms_unverified`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of M_Master_CL_Landscape](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/39_Coastal_loaded__1.jpg)

### 10. SM_Palm_01_01_G

ID: `current_Palms_Pack_01__Meshes__SM_Palm_01_01_G`

Unreal: `/Game/Palms_Pack_01/Meshes/SM_Palm_01_01_G.SM_Palm_01_01_G`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Palms_Pack_01\Meshes\SM_Palm_01_01_G.uasset`

[measured] A tall green palm, slightly leaning trunk, fan crown, and long skirt of dry leaves. Leaf cutouts appear correct in preview.

[inference] keep as a mature-form candidate; species fit for Rimal is unproven.

[measured] LOD0: **19,293 triangles**, 19,838 vertices; UV channels 3; material slots 7; collision primitives 3; Nanite unchecked. Approx Size (unit not labeled): `296 x 481 x 762`.

Rights: `exact_listing_identified_terms_unverified`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of SM_Palm_01_01_G](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/41_Palm01_whole__1.jpg)

### 11. SM_Palm_01_06_G

ID: `current_Palms_Pack_01__Meshes__SM_Palm_01_06_G`

Unreal: `/Game/Palms_Pack_01/Meshes/SM_Palm_01_06_G.SM_Palm_01_06_G`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Palms_Pack_01\Meshes\SM_Palm_01_06_G.uasset`

[measured] A more upright green palm with a tiered crown and upper fan. Its silhouette differs from Palm01.

[inference] keep separately from Palm01; no duplication is proven.

[measured] LOD0: **20,729 triangles**, 21,422 vertices; UV channels 3; material slots 7; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `331 x 326 x 648`.

Rights: `exact_listing_identified_terms_unverified`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of SM_Palm_01_06_G](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/46_Palm06_whole__2.jpg)

### 12. SM_Palm_01_12_G

ID: `current_Palms_Pack_01__Meshes__SM_Palm_01_12_G`

Unreal: `/Game/Palms_Pack_01/Meshes/SM_Palm_01_12_G.SM_Palm_01_12_G`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Palms_Pack_01\Meshes\SM_Palm_01_12_G.uasset`

[measured] A very short trunk and sparse, wide green fan crown. A low growth form distinct from mature palms.

[inference] keep separately; it is not just a scaled-down mature palm.

[measured] LOD0: **2,915 triangles**, 3,006 vertices; UV channels 3; material slots 6; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `172 x 170 x 126`.

Rights: `exact_listing_identified_terms_unverified`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of SM_Palm_01_12_G](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/48_Palm12_whole__1.jpg)

### 13. SM_Palm_01_13_Dry

ID: `current_Palms_Pack_01__Meshes__SM_Palm_01_13_Dry`

Unreal: `/Game/Palms_Pack_01/Meshes/SM_Palm_01_13_Dry.SM_Palm_01_13_Dry`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Palms_Pack_01\Meshes\SM_Palm_01_13_Dry.uasset`

[measured] A tall narrow palm with hanging brown-gray leaves and no green crown visible in preview.

[inference] review as a localized dry state, not a default pre-war planting.

[measured] LOD0: **23,221 triangles**, 23,856 vertices; UV channels 3; material slots 5; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `298 x 289 x 854`.

Rights: `exact_listing_identified_terms_unverified`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of SM_Palm_01_13_Dry](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/50_Palm13_whole__1.jpg)

### 14. SM_Palm_01_15_Dry_Fallen

ID: `current_Palms_Pack_01__Meshes__SM_Palm_01_15_Dry_Fallen`

Unreal: `/Game/Palms_Pack_01/Meshes/SM_Palm_01_15_Dry_Fallen.SM_Palm_01_15_Dry_Fallen`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Palms_Pack_01\Meshes\SM_Palm_01_15_Dry_Fallen.uasset`

[measured] A whole fallen dry palm, with exposed roots and a dry crown.

[inference] review only as a fallen state and according to place/time evidence; do not place it as ordinary planting.

[measured] LOD0: **31,198 triangles**, 31,199 vertices; UV channels 3; material slots 5; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `738 x 247 x 289`.

Rights: `exact_listing_identified_terms_unverified`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of SM_Palm_01_15_Dry_Fallen](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/52_Palm15_whole__1.jpg)

### 15. SM_H0015_Building_02

ID: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0015_Building_02`

Unreal: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0015_Building_02.SM_H0015_Building_02`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0015_Building_02.uasset`

[measured] A whole building with five upper facade rows above commerce/entrances and set-back rooftop structures; open balconies, glazed projections, laundry, and dishes.

[inference] keep as a residential-over-commercial candidate. Preserve height, balconies, and roof; it is not a BG module.

[measured] LOD0: **201,057 triangles**, 211,808 vertices; UV channels 2; material slots 4; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `2,034 x 1,170 x 2,417`.

Rights: `owner_confirmed_for_technical_qualification`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of SM_H0015_Building_02](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/55_H0015_whole__1.jpg)

### 16. SM_H0905_Arab_x1_fbx

ID: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0905_Arab_x1_fbx`

Unreal: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0905_Arab_x1_fbx.SM_H0905_Arab_x1_fbx`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0905_Arab_x1_fbx.uasset`

[measured] A long low structure with a dome, five closed pointed openings, and ornate detail.

[inference] review as a special structure, not a generic low-rise residential base.

[measured] LOD0: **6,075 triangles**, 8,496 vertices; UV channels 2; material slots 1; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `2,192 x 1,021 x 963`.

Rights: `owner_confirmed_for_technical_qualification`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of SM_H0905_Arab_x1_fbx](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/59_H0905_whole__1.jpg)

### 17. SM_H0906_Arab_x2_fbx

ID: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0906_Arab_x2_fbx`

Unreal: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0906_Arab_x2_fbx.SM_H0906_Arab_x2_fbx`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0906_Arab_x2_fbx.uasset`

[measured] A narrow polygonal structure with two formal tiers, a dome, latticework, and closed openings.

[inference] review as a special tower/pavilion; distinct from long H0905 and broad H0907.

[measured] LOD0: **4,361 triangles**, 6,398 vertices; UV channels 2; material slots 1; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `789 x 794 x 1,367`.

Rights: `owner_confirmed_for_technical_qualification`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of SM_H0906_Arab_x2_fbx](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/61_H0906_whole__1.jpg)

### 18. B18_Win_Wall_3x3_Set

ID: `current_ProceduralBuildingGenerator__Meshes__Wall__B18_Win_Wall_3x3_Set`

Unreal: `/Game/ProceduralBuildingGenerator/Meshes/Wall/B18_Win_Wall_3x3_Set.B18_Win_Wall_3x3_Set`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ProceduralBuildingGenerator\Meshes\Wall\B18_Win_Wall_3x3_Set.uasset`

[measured] A brick segment with a tall narrow two-pane window. The opposite side has a light tile finish and a window.

[inference] review as a narrow-opening segment; brick finish and BG connections are not qualified.

[measured] LOD0: **280 triangles**, 446 vertices; UV channels 2; material slots 6; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `27 x 300 x 300`.

Rights: `acquisition_record_terms_unverified`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of B18_Win_Wall_3x3_Set](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/63_B18_whole__1.jpg)

### 19. B55_2Win_Wall_3x3_Set

ID: `current_ProceduralBuildingGenerator__Meshes__Wall__B55_2Win_Wall_3x3_Set`

Unreal: `/Game/ProceduralBuildingGenerator/Meshes/Wall/B55_2Win_Wall_3x3_Set.B55_2Win_Wall_3x3_Set`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ProceduralBuildingGenerator\Meshes\Wall\B55_2Win_Wall_3x3_Set.uasset`

[measured] One broad opening divided into two glazing columns and four panes, with lintel and sill.

[inference] review: preserve the rhythm of the broad opening; these are not two independent wall openings.

[measured] LOD0: **282 triangles**, 392 vertices; UV channels 2; material slots 5; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `34 x 300 x 300`.

Rights: `acquisition_record_terms_unverified`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of B55_2Win_Wall_3x3_Set](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/67_B55_Front__1.jpg)

### 20. B93_Win_Extruded_Wall_3x3_Var2_Set

ID: `current_ProceduralBuildingGenerator__Meshes__Wall__B93_Win_Extruded_Wall_3x3_Var2_Set`

Unreal: `/Game/ProceduralBuildingGenerator/Meshes/Wall/B93_Win_Extruded_Wall_3x3_Var2_Set.B93_Win_Extruded_Wall_3x3_Var2_Set`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ProceduralBuildingGenerator\Meshes\Wall\B93_Win_Extruded_Wall_3x3_Var2_Set.uasset`

[measured] A brick segment with deep relief around a multi-pane window, lintel, and sill.

[inference] review: retain depth and pane-layout variety relative to B18/B55.

[measured] LOD0: **932 triangles**, 1,275 vertices; UV channels 2; material slots 4; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `50 x 300 x 300`.

Rights: `acquisition_record_terms_unverified`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of B93_Win_Extruded_Wall_3x3_Var2_Set](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/69_B93_whole__1.jpg)

### 21. SM_wall_windows_4x4_open

ID: `current_ModularCourtyard__Meshes__SM_wall_windows_4x4_open`

Unreal: `/Game/ModularCourtyard/Meshes/SM_wall_windows_4x4_open.SM_wall_windows_4x4_open`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ModularCourtyard\Meshes\SM_wall_windows_4x4_open.uasset`

[measured] Similar to the closed-window segment, with a small open black area in the left window and an additional M_Dark_Empty material. The wall back remains solid.

[inference] review as a window-condition variant; the suffix open is not proof of a through-opening.

[measured] LOD0: **660 triangles**, 924 vertices; UV channels 2; material slots 5; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `54 x 400 x 400`.

Rights: `acquisition_record_terms_unverified`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of SM_wall_windows_4x4_open](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/72_Courtyard_open_whole__1.jpg)

### 22. store_front_windows_intact_4x1_a

ID: `current_ModularBuildingSet__Meshes__Store_fronts__store_front_windows_intact_4x1_a`

Unreal: `/Game/ModularBuildingSet/Meshes/Store_fronts/store_front_windows_intact_4x1_a.store_front_windows_intact_4x1_a`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ModularBuildingSet\Meshes\Store_fronts\store_front_windows_intact_4x1_a.uasset`

[measured] A dark shop front with four bays, eight glass panes, and a lower tile strip. Most frames and the base are not visible in Back view.

[inference] review as an exterior frontage with backing; not a finished interior wall.

[measured] LOD0: **488 triangles**, 946 vertices; UV channels 2; material slots 4; collision primitives 1; Nanite unchecked. Approx Size (unit not labeled): `35 x 600 x 394`.

Rights: `acquisition_record_terms_unverified`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of store_front_windows_intact_4x1_a](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/75_Storefront_exterior_whole__1.jpg)

### 23. store_front_windows_intact_4x1_a

ID: `current_ModularBuildingSet__Meshes__Store_fronts_interiors__store_front_windows_intact_4x1_a`

Unreal: `/Game/ModularBuildingSet/Meshes/Store_fronts_interiors/store_front_windows_intact_4x1_a.store_front_windows_intact_4x1_a`

Source: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\ModularBuildingSet\Meshes\Store_fronts_interiors\store_front_windows_intact_4x1_a.uasset`

[measured] The same facade rhythm, but glazing allows a view through it, with depth and additional return pieces; frames/base are also visible in Back view. A bright vertical gap appears near the inner left support.

[inference] review separately as a version also visible from inside; inspect the gap and seams. Do not merge with the exterior version.

[measured] LOD0: **798 triangles**, 1,528 vertices; UV channels 3; material slots 3; collision primitives 2; Nanite unchecked. Approx Size (unit not labeled): `117 x 600 x 394`.

Rights: `acquisition_record_terms_unverified`; approval scope unchanged. [not run] Final role fit, placement, and Houdini.

![Original view of store_front_windows_intact_4x1_a](C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/79_Storefront_interior_reverse__1.jpg)

## Narrowing and test sequence

The three viewed green palms retain silhouette and growth-form differences; dry and fallen forms are separate states. Do not infer that the 11 not yet viewed are redundant. B18/B55/B93, H0905/H0906/H0907, and the two shop-window versions are also not proven duplicates. The proposed subset grew to 133 records / 174 member paths because of the interior shop version. That is still not a proven visual minimum.

The exact continuation is in `../NEXT_TASKS.md`. Acacia diagnosis and shop seams precede qualification; any material change/import/generation requires separate GO under task limits. Further view-only inspections are already authorized, subject to a new lock. CONTRACT v0.6 remains DRAFT.
