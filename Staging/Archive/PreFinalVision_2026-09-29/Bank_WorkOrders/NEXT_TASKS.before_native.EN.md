# Next Tasks — ModelBank

Date: 2026-09-28. New operator: Astra, thread 01a0e820-c6d4-7702-8e7b-55fd20f9b020.

## LOCK — resolve ownership before acting in the editor

[measured: EDITOR_SESSION.md] The latest measurement record is OWNER=NONE at 13:41, but UnrealEditor PID 18000 started at 16:01:53 in this project. Its owner was not identified. Do not activate, close, or change the process to resolve the lock.

Identify who started the process and obtain a documented handover. Coordination with the measurement manager is allowed solely for this lock. Reconfirm that measurement has finished, that the last line of its ownership file is still OWNER=NONE, and that no conflicting operator or process exists. Measurement files remain unchanged. Record new ownership only under Staging/ModelBank, with thread, PID, time, scope, and release. Historical OWNER=NONE does not authorize a new process.

## BANK-NATIVE — inspection of existing assets, after resolving LOCK

This inspection is already covered by Aviv's authorization; do not request approval again for this limited inspection. No import, Content change, map save, cook, bake, or instance creation. If an action beyond viewing in the asset editor is required, record it as not run and as a separate task. Do not open a map that could activate an HDA or session. Do not click Apply/Save/Compile or change asset settings.

### First batch — nine assets

The object paths below are based on package files and their names; loading has not yet been verified. If a path does not resolve, record that and do not guess a substitute.

| Order | asset_id | Unreal object path | Proposed role |
|---|---|---|---|
| 1 | `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0907_Arab_x3_fbx` | `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0907_Arab_x3_fbx.SM_H0907_Arab_x3_fbx` | whole_building |
| 2 | `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0014_Building_01` | `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0014_Building_01.SM_H0014_Building_01` | whole_building |
| 3 | `current_ModularCourtyard__Meshes__SM_wall_windows_4x4_01` | `/Game/ModularCourtyard/Meshes/SM_wall_windows_4x4_01.SM_wall_windows_4x4_01` | window_bay |
| 4 | `current_ModularBuildingSet__Meshes__Store_fronts__store_front_shutters_4x1_a` | `/Game/ModularBuildingSet/Meshes/Store_fronts/store_front_shutters_4x1_a.store_front_shutters_4x1_a` | storefront_bay |
| 5 | `current_Project__Shared__Bank_ME_v3__StreetFurniture__SM_H0051_Garbagebin` | `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/SM_H0051_Garbagebin.SM_H0051_Garbagebin` | street_waste_bin |
| 6 | `current_Project__Shared__Bank_ME_v3__Vegetation__SM_H0636_Acacia` | `/Game/Project/Shared/Bank_ME_v3/Vegetation/SM_H0636_Acacia.SM_H0636_Acacia` | tree_or_shrub |
| 7 | `current_Project__Shared__Bank_ME_v3__StreetFurniture__SM_H0082_Streetsign` | `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/SM_H0082_Streetsign.SM_H0082_Streetsign` | sign_or_graphic |
| 8 | `current_StarterContent__Materials__M_Concrete_Poured` | `/Game/StarterContent/Materials/M_Concrete_Poured.M_Concrete_Poured` | sidewalk_surface |
| 9 | `current_FC_Coastal_Landscape__Landscape__M_Master_CL_Landscape` | `/Game/FC_Coastal_Landscape/Landscape/M_Master_CL_Landscape.M_Master_CL_Landscape` | ground_surface |

### Systematic continuation across all families

The working sources are the updated BANK_CANDIDATE_INDEX_2026-09-28.csv, FAMILY_REVIEW.csv, and MEMBER_REVIEW.csv. All 324 families remain in scope. The native_batch field points to the family queue; REPRESENTATIVE_SUBSET_PROPOSED.csv is a proposal for initial comparison, not a scope limit.

1. Compare Bank_ME_v3 by height/use/envelope and condition, including all 32 records.
2. Compare ModularCourtyard windows/doors/walls/roof edges; and ModularBuildingSet sides, corners, and interior versus exterior.
3. Compare B18/B55/B93 and ProceduralBuildingGenerator material/condition/edge; open a technical variant only if it could change selection or cost.
4. Compare all 16 green palms in Palms_Pack_01, dry/fallen variants, and understory plants; do not reduce them to the three samples without evidence. FoliageType is not another tree shape.
5. Inspect FC_Coastal_Landscape and StarterContent materials and function/instance dependencies; do not present a material function as a ready material.
6. Complete Warehouse and AssetsvilleTown/Stylized_Egypt/UtopianCity reserves by role. Exclude is a scope recommendation only; no asset is deleted.
7. MOUT_Arabian, CityBLD kits, and the Hergel/Terre archive: continue only with existing source evidence until separate GO for import.

For each asset/family: an identity image with the path and two useful views where needed; close variants under the same lighting and perspective; class identity; visible material/texture, transparency, normals, and UV; bounds and units shown by the editor; pivot/front/up only when proven; slots/dependencies; LOD/Nanite/collision and triangles according to the UI. Do not change LOD or collision. If there is no measurement, leave the field blank and mark it not run.

BANK-NATIVE gate: for each recommendation, exact identifiers, evidence scope, image or documented measurement, differences retained, and next gate. Viewing in the asset editor proves only what was observed there; qualification, connected, generated, and accepted status do not change from that alone. Record ownership release at the end.

## BANK-IMPORT — future task, separate GO required

[proposed] The exact selection base is records with source_scope=external in REPRESENTATIVE_SUBSET_PROPOSED.csv, with all member paths in MEMBER_REVIEW.csv. Before execution, freeze a smaller list only after checking rights and dependencies, and document source project/version, file type, supported importer, and explicit destination.

For Unreal assets: use supported Migrate from the source project and its dependency report. No manual uasset copying. Migrate preserves package structure under Content; inspect all target files and conflicts beforehand. Changing a package route is not included in import approval without an explicit decision. For FBX/OBJ: import only through a supported importer, with materials/textures and documented cm/axis rules. [proposed] Inspection-only destination: /Game/Developers/USER/ModelBankReview/<Pack>/ for interchange sources; this is not an approved destination and does not automatically apply to Migrate. Do not change the source or replace existing files.

Import gate: before/after manifest, rights by scope, source hashes, dependency list, 0 unapproved overwrites, exact object paths, loading and materials, units and bounds, images at the same scale. Reopening and saving require the separate execution task and explicit save paths. Import alone is not qualification.

## BANK-ROLE — future role tests

[not run: INST1/BG1/SURFACE1] Only after contract decisions and separate execution instructions.

- Whole building/prop/vegetation: test `unreal_instance`, identity/path, base contact, front/up, footprint, clearance, variation, materials, and performance. A whole building is not a BG module.
- Building module: test connector, width/height/depth, pivot, handedness, corners, and seam closure with module geometry. Define a complete parts list and fallback before BG1; no fallback was built in this review.
- Road/ground material: test units/tiling, layers, masks, surface geometry, seams, and appearance; a sidewalk mesh is not a material and does not replace the Houdini network.

Role gates will specify parameters, explicit map/output paths, versions/input hashes, counts/IDs, Aviv's visual check, save/reopen in a fresh process, recook, and, once baking begins, rebake with replace and no duplicates, according to the contract approved at execution time. At this stage v0.6 is still DRAFT, and none of these tests is performed.

## RIGHTS — missing documents

The owner's approval for the 32 Bank_ME_v3 assets is retained and is not requested again. Source/license documents and a receipt link are needed for Palms_Pack_01 and selected external packages; use terms for packages with documented receipts; and texture/conversion rights for Hergel/Terre/SpeedTree sources. Identifying a listing is not proof of entitlement. Do not extend the v3 approval to the rest of the archive.
