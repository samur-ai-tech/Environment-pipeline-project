# GazaRimal — Bank Review, New Astra, 2026-09-28

**File, role, and evidence review covered all 1,215 records. Visual review inside Unreal was blocked and not completed.** This operator opened no assets in the editor. Seventeen source and archive images were examined and linked to 25 candidates; they do not verify those assets in the current project. [measured: file_inventory.json; visual_evidence_manifest.json] [not run: BANK-VIS-NATIVE]

## Blocker and editor ownership

The measurement team finished: `ME-01` is recorded as complete at 13:22:51.758, and the editor closed at 13:39:31. The last entry in `Staging/TrackA_Tests/HoudiniCityProof/10_measure_session/coordination/EDITOR_OWNER.txt` is `2026-09-28T13:41:00+03:00 OWNER=NONE`. [documented: coordination/LEDGER.md; EDITOR_OWNER.txt]

However, another process for this project was found: `UnrealEditor.exe`, PID `18000`, created at `16:01:53.732101+03:00`, parent PID `4340`. Computer Use reported window `329384`, titled `Environmentpipeline - Unreal Editor`. This process started after the measurement editor closed; its owner was unclear. The window was not activated and received no input. [measured: EDITOR_SESSION.md]

**Bank editor ownership was not taken; this operator has no lock to release.** An old `OWNER=NONE` entry does not authorize taking over a new process. The process must not be closed or killed to clear the blocker. A handover entry from its current owner and a fresh check of the process, lock, and other operators are required. Aviv's authorization for the bank task already exists; identifying actual editor ownership is the missing step. The measurement files and old STOP were not edited.

## Deliverables

| File | Contents |
|---|---|
| `../BANK_CANDIDATE_INDEX_2026-09-28.csv` | Unified index updated to 1,215 rows and 86 fields. IDs, record order, and source paths were preserved. New review fields separate quality, rights, compatibility, placement, and evidence. |
| `FAMILY_REVIEW.csv` | All 324 families: recommendations, exact IDs, asset paths, every family member, variation, and placement rules. |
| `MEMBER_REVIEW.csv` | 1,320 distinct member paths, especially important for grouped MOUT records. |
| `REPRESENTATIVE_SUBSET_PROPOSED.csv` | Proposed focused comparison of 132 records containing 173 member paths, by role. |
| `visual_evidence_manifest.json` | 25 links to observations, paths to the 17 images and their SHA-256 hashes; evidence scope is explicit. |
| `semantic_overrides.json` | 50 role corrections or refinements, marked as inferences from names or paths until asset class and content are checked. |
| `technical_alternatives.json` | 36 alternatives with a technical suffix and an existing, unambiguous base; no claim of visual equivalence. |
| `same_name_package_comparison.json` | Nine pairs with the same name in ModularBuildingSet, but different paths and hashes. |
| `NEXT_TASKS.md` | Specific continuation: live checks, future import, and separate placement and generation tests. |
| `BANK_CANDIDATE_INDEX.before.csv` | Index before this change; the two source CSVs remained unchanged. |

The other JSON files contain working evidence and validation. There is no active HDA Data Table, project code, or generator connection here.

## Evidence states

| State | What is known |
|---|---|
| available | All 1,215 records and 1,320 member paths were found. [measured: file_inventory.json] |
| imported | 930 records have package files in the project; 285 records are external. File presence does not prove successful loading. |
| technically checked | The 32 Bank_ME_v3 assets have saved import measurements in this project. Another 898 current records have not been technically checked; the 285 external records have not been checked here. Archive measurements remain labeled as older sources. |
| rights confirmed | The documented owner authorization for the 32 Bank_ME_v3 assets is retained for technical qualification. Files or receipt records do not settle rights for other sources. |
| qualified for role | 0 |
| connected to Houdini | 0 |
| generated on this route | 0 |
| visually verified in this project | 0; viewing source or archive images does not reach this state. |
| accepted | 0 |

The last five states and `generation_enabled=false` were preserved for all 1,215 records. Unmeasured selection weights, scale ranges, contact offsets, and directions remain blank or unknown. [measured: validation.json]

## Meaning of the recommendations

**497 keep, 634 review, 56 consolidate, 28 exclude.** These are recommendations for the candidate pool only. `keep` means preserve and prioritize for examination, not permission to place. `consolidate` means compare within a family, not delete. `exclude` means leave out of the proposed GazaRimal subset; all sources are preserved. [measured: FAMILY_REVIEW.csv]

No winning package was selected. Eleven unidentified assets, including `SM_Fun`, `SM_sig2`–`SM_sig9`, `ProcMesh_Baked`, and `Brut_Master`, were moved from exclude back to review: an unclear name is no evidence that an asset is unnecessary.

## Practical recommendations for major families

| Source / family | Recommendation and differences to retain |
|---|---|
| Bank_ME_v3 — whole buildings | Retain H0905/H0906/H0907 and H0013–H0016 as distinct heights and footprints; the three H0902–H0904 remain for use and condition review. Do not turn a whole building into a BG module. [documented: ME/IMPORT_RESULTS_v3.json] |
| H0015 | The source view shows repeated balconies, a shuttered shop floor, air conditioners, and a flat roof with a service structure. Retain as a residential-over-retail building candidate; its use and fit for Rimal remain inferences. The old label `neoclassical` does not adequately describe the observed appearance. [measured: visual_evidence_manifest.json] [inference] |
| MOUT_Arabian | 86 records, some representing entire families. Retain walls, openings, corners, balconies, end pieces, market details, stone and wood benches, containers, and plants. `external.MOUT_WHOLE_ASSEMBLIES` contains ten Blueprints, not ten BG modules. No viewing or import into this project occurred. [documented: EXTERNAL_SOURCE_SELECTION_2026-09-28.csv] |
| Palms_Pack_01 | Compare all 16 palms together; do not choose by the number in a name. Green, standing dry, and fallen dry are distinct conditions. Grass, thicket, and Hazel are not more palms. The source identifies `Trachycarpus fortunei`; that does not establish ecological suitability for Rimal. [documented: CURRENT_PACK_SELECTION_2026-09-28.csv] |
| ModularCourtyard | Retain open and closed windows, T1/T2/T3 facade types, open and closed balconies, entry, arch, lower-floor corner, and cornice. Names such as 4x4/6x2 are not measurements. Wrappers with `FoliageType` require reference checks; they are not proven new plant shapes. [inference] |
| ModularBuildingSet | Retain shuttered shop versus door or display window, bay dimensions, left/right, corner, roof finish, and intact/broken/torn states. Nine same-name pairs in `Store_fronts`/`Store_fronts_interiors` are not identical files; do not merge before examining depth and interior/exterior use. [measured: same_name_package_comparison.json] |
| ProceduralBuildingGenerator | Compare B18/B55/B93: single, double, and projecting openings according to their names; retain the entrance and left/right corners. Examine worn walls, wood, roofs, scaffolding, pipes, and wires separately. The 36 technical alternatives are linked to their bases; visual equivalence has not been shown. [inference] [not run: BG1] |
| FC_Coastal_Landscape | Retain master and instance as material candidates, and Sand/Soil/Grass/Rock as separate dependencies. A Material Function is not a ready-to-apply Landscape material. RVT, layers, tiling, and masks were not tested. [not run: BANK-NATIVE-MATERIAL/SURFACE1] |
| Hergel_NYCAlley / Terre_Rural | Both five-part kits remain under review. Archive images show a red brick appearance for the first and brown vertical wood for the second. They help compare mechanisms; there is no basis to choose either as the default Rimal facade. The images show an old assembly, not a check of every part. [measured: visual_evidence_manifest.json] [inference] |
| Other Hergel/Terre | Retain crates, containers, carts, pipes, canals, air conditioners, satellite dishes, street furniture, and distinct plant shapes by role. H0896 is a candidate for a large compound based on older bounds, not a single-lot building. Compare BusStop/Street Light pairs from the two banks; a shared name does not prove duplication. [documented: source CSVs] [inference] |
| Plants in source images | T0976 branches openly; T1160 is narrower and denser; T1090 has an upright silhouette; T1183 has a broader crown. Retain these distinctions. Separately framed images do not establish relative size or local species. [measured: visual_evidence_manifest.json] |
| Rocks in source images | T1026/T1027 are upright with different silhouettes; T1028 is flat and broad; T1036 is a low, irregular cluster. T1026/T1027 appear almost white; the cause and correct material are unproven. Do not exclude automatically because of similarity. [measured: visual_evidence_manifest.json] |
| Signs | `external.H0154` actually displays X MOVIES / OPEN 24 HOURS / ADULTS ONLY. The graphic is not proposed for local signage; the sign body may be reviewed separately. H0082/H0083 and all other signs still need checks of legibility, language, and local meaning. [measured: visual_evidence_manifest.json] [inference] |
| StarterContent / road | Concrete and Gravel are control candidates only. No standalone qualified asphalt material was located here. A sidewalk or road mesh is not a material and does not replace Houdini road-network geometry. [not run: SURFACE1] |
| Warehouse_Building | Retain possible industrial use; two files are not necessarily two distinct buildings. Asset type, footprint, and materials were not checked. [inference] |
| AssetsvilleTown / Stylized_Egypt / UtopianCity | Useful items stay in the review reserve so their roles are not lost. Stylized design has not been declared realistic. Maintenance equipment, furniture, and infrastructure are reviewed separately from story props, an ancient statue, hologram, and planet. [inference] |
| Iceland_Environment | Fourteen mountain/background items are proposed for exclusion from the geographic generation bank because terrain shape should come from the source package. This is a scope decision, not a quality score. [inference] |

All exact IDs and paths, including records absent from the table, are in `FAMILY_REVIEW.csv` and the index. The old `family_id` remains a stable ID even when its name contains a corrected classification; `functional_role`, `category`, `representation`, and `role_evidence` record the new review.

## Focused technical findings

All 32 v3 meshes have one documented LOD and `Nanite=false`. H0014 has 2,476,576 triangles; H0016 has 822,754; H0015 has 201,057. These are recorded geometry costs, not FPS measurements. H0013 has a recorded height of 48.68 m and 44,241 triangles: height is no substitute for a cost measure. There is no automatic 150k rejection threshold. [documented: ME/IMPORT_RESULTS_v3.json]

There are differences from older measurements: for example, H0015 has 201,055 triangles in the archive versus 201,057 in v3; H0636 had 2,371 versus 4,352 in v3. Do not mix the figures. The new CSV preserves v3 data as documented data and archive data as historical measurements.

H0636: according to the v3 report, the billboard source `DesertTreesBillboard_7a01e99a95cf.png` is missing, and `Material__28` has no texture. H0014: `standard1` does not reference a texture; that alone does not prove a broken material. The narrative report mistakenly says “other 11 materials,” whereas the detailed check table and asset record list eight slots, seven with textures. This review uses the detailed records and leaves the visual result open. [documented: ME/IMPORT_REPORT.md:103–104,149; ME/IMPORT_RESULTS_v3.json]

Older texture-dependency checks do not test UV quality, transparency, normals, roughness, seams, or LOD transitions. Even “30 of 32 fully textured” in the import report does not visually approve 30 assets. Documented pivot offsets are not copied to contact offsets: their sign, support point, and front/up directions have not been proved here. [not run: BANK-NATIVE]

`.uasset` files are not Unity sources. Original Hergel/Terre Unity paths are provenance trails; current import and shader behavior have not been tested. The six SpeedTree trees are documented as older static imports with a billboard that does not face the camera and without wind; do not present them as a proven live vegetation system. [documented: STAGE2_CANDIDATES.md]

## Rights — separate from quality

- `Bank_ME_v3`: owner authorization for the 32 assets is retained. Do not request it again. Future distribution/attribution documents are not attached.
- `Palms_Pack_01`: the package was identified in the catalog as `Palms Pack 01 (Trachycarpus fortunei)`, listing `9f81069d-877c-4d4e-aa28-30f5d1a8d8c9`. A listing match does not prove acquisition or license terms. The older rights document says no match was found among 19 receipts; that does not mean the package itself was unidentified. [documented: CURRENT_PACK_SELECTION_2026-09-28.csv; RIGHTS_TECH_GAPS_2026-09-28.md]
- `MOUT_Arabian`, `ModularCourtyard`, `ModularBuildingSet`, `ProceduralBuildingGenerator`, `FC_Coastal_Landscape`: local receipt records were documented; terms of the specific acquisition and account/source link remain missing. A receipt is not a quality measure.
- `Hergel_NYCAlley`, `Terre_Rural`, other Hergel/Terre assets, and the six SpeedTree trees: source documents and permissions for the corresponding packages, including textures and conversions, are required. The v3 authorization does not extend to them.

A focused request was sent to Aviv for the location of existing license and source documents. No content was purchased or downloaded. No legal conclusion was drawn about an unexamined license.

## Small subset and clean organization

**There is currently no basis to determine the minimum that is visually sufficient.** The proposal includes 132 records / 173 members by documented height, use, opening type, handedness, condition, plant shape, and material dependencies. It includes the first nine assets and all 32 v3 assets; it does not narrow the review's scope. The three healthy palms in it are a sample only: all 16 palms remain for comparison before any reduction. [proposed: REPRESENTATIVE_SUBSET_PROPOSED.csv]

No large family has proven visual duplication. Therefore, do not delete, move, or replace any asset. After viewing, an alternative can be removed only if it has been shown to overlap an existing representative in role and variation, while preserving evidence and provenance links.

[proposed] Organization remains logical by role: `Buildings/Whole`, `Buildings/Modules`, `StreetProps`, `SmallProps`, `Vegetation`, `Signs`, `Materials/Road`, `Materials/Ground`, `Utility/RooftopProps`. A facade material is labeled `Materials/Facade`; wrappers and scene setup are separate from placeable content. Files need not move to apply this metadata. Source, rights, material, and LOD are fields, not winning packages.

A whole building is an instance-placement candidate. A building module requires geometry and a connection contract; `Export Input as References` sends a reference on a point, not module geometry. [documented: [SideFX Inputs](https://www.sidefx.com/docs/houdini/unreal/inputs.html), [Building Generator 4.0](https://www.sidefx.com/docs/houdini/nodes/sop/labs--building_generator-4.0.html)] `BG1`, `INST1`, cook, bake, and Tier 1 were not run. `CONTRACT v0.6` remains DRAFT.

## Next steps

1. Resolve ownership of PID 18000 and record the handover; then inspect the first nine assets and continue through all editor families according to the catalog.
2. Complete rights/source documentation, beginning with Palms and the proposed external sources.
3. Complete identity/class, materials, directions, contact, LOD, and collision checks. Reduce the set only after actual comparison.
4. Prepare a small external import with closed dependencies under a separate execution instruction. No import is part of this review.
5. Only after contract approval and separate instructions, perform module, whole-instance, surface, and required persistence tests. No recommendation in this file opens a generation gate.

**The session ended with the live-check blocker, not bank acceptance.** This operator did not alter Content, maps, source assets, HDA, or Linear. Houdini and another Unreal process were not started.
