# Bank Schema Gap Audit — 2026-09-29

**Reconciliation with Track A r3, 2026-09-29:** [documented: `Staging/TrackA_Tests/HoudiniCityProof/11_topic3_readiness_2026-09-28/CATALOG_INTERFACE_R3_PROPOSAL_2026-09-29.md` and its four JSON companions] The newer proposal corrects the strict contact requirement in the older alias table below. Under Aviv's first-release ruling, `PlacementAnchorValid` and `PlacementAnchor{X,Y,Z}Cm` express a declared bottom-anchor convention, **not measured contact with support geometry**. `ContactValid`/`Contact{X,Y,Z}Cm` below document an older proposal and are not the current first-release entry gate. r3 still has 54 fields, but names 31–34 and SchemaVersion 3 remain proposals. A DataTable in Geometry Input carries the row metadata; `Export Input as References` alone does not transfer it. Row `ObjectPath` selects the instance asset, while translator `unreal_object_path` identifies the DataTable. [documented: r3 proposal; decided: Aviv 2026-09-29 as recorded in `BANK_DECISION_SHEET_2026-09-29.md`; not run: CAT1]

**Proposed runtime placement policy:** [documented: `role_placement_policy.r3.proposed.json`] The 54 fields do not contain numeric bounds margins, setbacks, slope, or plinth values. r3 proposes a native HDA `placement_rules` multiparm keyed by `(Role, FootprintClass)`, with 15 fields per rule and still-null approved numeric values. This is proposed placement policy, not a second asset catalog. Zero must not become a default, and no candidate becomes qualified. Bank candidates stay disabled until policy decisions, rights checks, and measurements are complete. [proposed; not run: CAT1, INST1, BG1, Tier 1]

**Later update:** The current index is [v7](BANK_CANDIDATE_INDEX_2026-09-29.csv), SHA-256 `1553B0AFE81F816C1AD6F2F44CE4B1CEC6C3943E68251E4E73C7B61ACB3DC1B1`. BANK-ASTRA-008 measured bounds and 30 materials on 12 additional `Bank_ME_v3` assets; the [manager review](Inspection_2026-09-29_Astra_V3_Batch/MANAGER_REVIEW_2026-09-29.md) and [diff QA](BANK_INDEX_V7_NATIVE_BATCH_DIFF_QA_2026-09-29.json) confirm 15 rows with bounds/material paths, 1,215 unqualified rows, and zero enabled. References to v6 below describe the original audit snapshot. [measured]

At the time of the original audit, only files were inspected. Later, BANK-ASTRA-003 and 004 supplied limited native observations; v5 encoded three material lists, and v6 added current local AABB to three disabled candidate rows. No import, asset repair, cook, bake, or qualification followed that encoding. Integration requirements are documented proposals; this document does not approve them.

**Conclusion:** The candidate index passed the checks of ID uniqueness and path syntax, but currently has no approved row for HDA delivery. v4 merged 75 native receipts and 24 corrections to meaning/representation/technical blockers; v5 added ordered material bindings to three rows; v6 added local AABB to them. BANK-ASTRA-005 closed their package-reference graph under the declared Asset Registry policy, and BANK-ASTRA-006 verified the absence of per-instance readers in only their six materials; those two receipts are external to the CSV. Dynamic references, materials of additional candidates, contact, orientation, and eligibility are still missing for CAT1/INST1. An alias alone cannot complete qualification. [measured: A,C; `Inspection_2026-09-29_Astra_Closure/DEPENDENCY_CLOSURE.json`; `Inspection_2026-09-29_Astra_Channels/MATERIAL_CHANNEL_AUDIT.json`] [documented: D,E,G]

## Sources and evidence state

- **A:** `Staging/ModelBank/BANK_CANDIDATE_INDEX_2026-09-28.csv`. The then-current v6 snapshot, SHA-256 `BFEE371865DED0D32C9372F704FF0B333E869B4BFE6C72392A7DE8F98E2CC8E9`; receipts `BANK_INDEX_V5_BINDINGS_RECEIPT_2026-09-29.json` and `BANK_INDEX_V6_BOUNDS_RECEIPT_2026-09-29.json`. v5 (`12225013B06810665B5E429299F1CD9E9931588AEAE4B1FFE1A33282B5719098`), v4 (`495985E2697C4BBBBE735E80184C5E73DA5B94A4444FEB5BAFDCBC6621ADEA42`), and v3 (`B05F8691402B47B4C6730F842163BD0555662C0802D4CA7EAADFE04266DCCC9F`) are historical.
- **B:** `Staging/ModelBank/Inspection_2026-09-28_Continuation/Native_Visual_Run_02/BANK_INTERFACE_FINDINGS.md` and `BANK_SCHEMA_MAPPING_REPLY.md`.
- **C:** `Staging/ModelBank/Inspection_2026-09-28_Continuation/Native_Visual_Run_02/COMBINED_NATIVE_REVIEW.json` — prior inspection receipts, not a new visual inspection.
- **D:** `Staging/TrackA_Tests/HoudiniCityProof/11_topic3_readiness_2026-09-28/BANK_INTERFACE_REQUIREMENTS.md`.
- **E:** In the same integration folder: `bank_field_alias_map.proposed.json`, `VALIDATION_GATES.md`, `MEASUREMENT_SPEC.md`.
- **F:** `AGENTS.md`; `Staging/CURRENT_STATE.md`; archived handoff `Staging/Archive/PreFinalVision_2026-09-29/Handoffs/HANDOFF_2026-09-28/MANAGER_HANDOFF_2026-09-28.md` (historical context only). Current contract limits, editor ownership, and execution approval apply. The process state during the overlap was not checked here.
- **G:** `Staging/ModelBank/BANK_INDEX_V4_MERGE_RECEIPT_2026-09-29.json` — merge of 24 corrections and 75 receipts, and repair of 46 `role_evidence` cells after review. IDs, paths, rights, eligibility flags, dimensions/contact, and protected fields were preserved.
- **H:** `Staging/ModelBank/Inspection_2026-09-29_Astra_Prep/BANK_ASTRA_001_RESULT.md` — repeat evidence for H0013/H0015/H0051/H0958; zero newly covered unique candidates. H0013's preview-floor correction supersedes the old interpretation in C.

## What is currently measured

| Check on A | Result |
|---|---|
| Row / column count | 1,215 / 101 |
| `asset_id` | 1,215 filled; 0 duplicates, including case-insensitive comparison |
| `variant_id` | 1,188 filled and unique; 27 empty, all `family_candidate` |
| `unreal_object_path` | 930 filled and unique; 0 syntax failures under `/Game/.../Object.Object`; 285 empty |
| Source file for 930 rows with an object path | All 930 `source_path` values exist on disk; this is not a load or redirector test |
| Object-path evidence within the index | 75 documented by native receipts; 855 based only on the filename convention; 285 `not_imported_here` |
| `native_class` | 73 `StaticMesh`, two `Material`, 1,140 empty |
| `qualified` / `technical_eligible` / `generation_enabled` | In all 1,215 rows: `no` / `false` / `false` |
| `index_revision` | `v6_current_bounds_2026-09-29` in every row |
| `material_paths` | Three ordered JSON lists for H0907/H0013/H0051; 1,212 empty; no eligibility change |
| `local_bounds_min_cm/max_cm` | Two numerical vectors in three rows, H0907/H0013/H0051; 1,212 empty. BANK-ASTRA-007R measured `(0,0,0)` for all six bounds-extension vectors on the current versions of those three assets; the AABB still is not a footprint or contact. |
| C against A | All 75 receipt IDs and object paths matched exactly and were merged into native/inspection fields; this is a record match, not fresh native verification. H records four repeat inspections without expanding coverage. |
| Metric exception | `SM_Hazel_14_G.native_triangles` remains empty: 206 in C's receipt is marked for recheck and was not copied to the index; mesh metrics of the two Material rows are empty. |

[measured: A,C; reading CSV/JSON, grouping IDs and paths, and checking `source_path` existence on 2026-09-29]

**Types and missing values:** CSV defines no types; all 101 fields are strings when read. `false` and `no` are text, not Boolean; an empty field is an empty string, not JSON null. The dimension fields `dimensions_x_cm`, `dimensions_y_cm`, `dimensions_z_cm` contain 32 numeric strings. `reported_pivot_to_bottom_cm` is filled in 32 rows as a textual three-number list, for example `[-170.98, 16.46, 0.35]` for H0013. It is **not a scalar across the records**, but it is also not a verified contact vector: `pivot_convention` in those rows says sign and direction were not independently verified. Successful parsing still does not justify inferring contact. [measured: A]

All of these fields exist in the header and are empty in all 1,215 rows: `contact_offset_cm`, `forward_axis`, `up_axis`, `scale_min`, `scale_max`, `selection_weight`, `allowed_zones`. `material_paths` and `local_bounds_min_cm/max_cm` are filled only in the three disabled rows above. Do not turn missing values into 0, a default axis, an unrestricted range, or an allowed zone. [measured: A]

## Alias table and minimum gap

Target types in the integration proposal are String, Int32, Boolean, and Float32. Every `actual_binding` in the alias map is still null; `actual_exported_schema` is null. The map's `source_schema` says `bank_candidate_index_2026-09-28_v3_astra_native_preview_01`, whereas the actual index is v6 and includes native fields; freeze the actual delivered header. [documented: E, `bank_field_alias_map.proposed.json:4`] [measured: A]

| Exact existing fields | Target field / type | Alias or gap / completion |
|---|---|---|
| `asset_id`, `family_id`, `variant_id` | `AssetId`, `FamilyId`, `VariantId` / String | Preserve exactly; do not invent a short ID or turn a family row into a selectable asset. Can be checked offline. |
| `unreal_object_path`, `unreal_package_path`, `object_path_verification` | `ObjectPath` / String | A package path is not an object path. The 930 are candidates with valid syntax only; loading, class, and absence of redirectors require a native receipt. |
| `native_class` | `AssetClass` / String | **This field already exists**, although the map shows an empty source list. Native receipts can be linked by ID; blanks remain unknown. A material's class is not the class of a mesh using it. |
| `index_revision` | `CatalogRevision` / String | Index revision is not necessarily the delivered subset revision; freeze the delivery path/hash/revision/row list. |
| `source_revision`, `source_catalog_sha256`, `inspection_revision` | `AssetRevision` / String | No safe alias: source, index, and inspection are not the revision of the mesh and its materials. A receipt for asset and dependency revisions is missing. |
| `source_catalog`, `source_revision`, `source_catalog_sha256`, `source_package`, `source_path` | `SourceProvenance` / String | Source and links may be retained offline; this is not rights proof. |
| No `SchemaVersion` | `SchemaVersion` / Int32 | Delivery metadata; requires agreement on schema revision, not a guess. |
| `functional_role`, `category`, `representation`, `style`, `allowed_zones` | `Role`, `Representation`, `StyleTokens`, `AllowedZoneTokens` / String | Organizational `category` is not role; `bg_module_candidate` is not a qualified `bg_module`. Enum/token dictionaries are not frozen; empty zones mean no approved zone. |
| `condition`, `environment_context`, `building_type`, `architectural_role`, `tags` | No matching fields in the proposed 54 columns | Retain metadata; if HDA selection consumes it, freeze an explicit binding before delivery. Do not silently drop it or infer from names. |
| `technical_state`, `technical_eligible`, `qualified`, `evidence`, `inspection_evidence`, `role_evidence` | `TechnicalStatus`, `QualificationEvidence` / String | A preview is not qualification; link evidence to role and intended use. |
| `rights_state`, `rights_eligibility_scope`, `decision`, `decision_reason` | `RightsEvidenceStatus`, `UseDecisionReference` / String | Separate rights evidence from the use decision. The 32 `technical_qualification_only_owner_confirmation` values do not authorize generation. Aviv's decision and its use scope are required. |
| `generation_enabled`, `qualified`, `technical_eligible`, `rights_eligibility_scope` | `RunEligible` / Boolean | Do not copy a single flag; require an explicit subset by gate and role, with no required gaps. Currently A has zero eligible. |
| `selection_weight` | `SelectionWeight` / Float32 | Entirely missing; a final nonnegative value and at least one positive weight per required role/zone are needed. Zero only for deliberate disabling. |
| `local_bounds_min_cm`, `local_bounds_max_cm`; `dimensions_*_cm` | `BoundsMin/Max{X,Y,Z}Cm` / Float32; `BoundsValid` / Boolean | v6 fills only H0907/H0013/H0051: current local-space AABB, Build Scale 1/1/1, and cm units linked through Unreal/Track A. BANK-ASTRA-007R measured zero `PositiveBoundsExtension` and `NegativeBoundsExtension` on all three meshes; that removes only extension ambiguity, not geometry-only footprint or contact. The other 1,212 rows remain unknown. |
| `contact_offset_cm`, `pivot_convention`, `reported_pivot_to_bottom_cm` | `Contact{X,Y,Z}Cm` / Float32; `ContactValid` / Boolean | No verified contact. Measure a signed local-space contact point; do not copy pivot-to-bottom or bounds-bottom. |
| `forward_axis`, `up_axis` | `Forward{X,Y,Z}`, `Up{X,Y,Z}` / Float32; `OrientationValid` / Boolean | Empty; front/up direction needs measurement and a role decision. |
| `scale_min`, `scale_max`; no other limits fields | `UniformScaleMin/Max`, `YawMin/MaxDeg` / Float32; `PlacementLimitsValid`, `AllowNonuniformScale` / Boolean; `RotationRule` / String | Values and use decision missing. Do not infer scale=1 or unrestricted yaw. |
| `material_paths`, `native_material_slots` | `MaterialBindingsJson`, `MaterialCustomDataChannels` / String; `KeepDefaultMaterials` / Boolean | v6 retains ordered index/name/object paths only for three disabled rows. JSON format is anchored in `MATERIAL_BINDING_CONTRACT_2026-09-29.md` [proposed]. For these three rows, BANK-ASTRA-005 checked limited package-reference closure; BANK-ASTRA-006 inspected the exact six materials and found no `PerInstanceCustomData` reader, as detailed in an external receipt. UNUSED applies only to those six material versions; H0958 and the final subset are not covered. An empty channels field without a linked receipt does not prove unused. `KeepDefaultMaterials=true` preserves defaults only on the proposed transfer route, after separate qualification. |
| No footprint/profile/module measurements | `FootprintClass`, `ModuleProfileId`, `ModuleQualificationEvidence`, `ModuleName` / String; `ModuleWidthM/HeightM` / Float32; `ModuleDimensionsValid` / Boolean | Footprint is required by role; other module fields are conditional on BG. Do not invent dimensions or a profile. BG1 and module geometry are needed only if BG is used. |
| `technical_variant_of` | Derivative→source link and asset revision | The field's meaning does not approve this new use. The bank owner decides link and revision; do not alter existing IDs or merge a repaired derivative by name. |

[measured: A] [documented: B,D,E] Every new binding in the table is [proposed], not a canonical change.

## Meaning corrections merged into v4 and remaining gaps

| Assets — short labels for readability only | Gap versus A and treatment |
|---|---|
| H0090 / H0091 | In A v4: `ibc_liquid_storage_container` / `drinking_water_dispenser`, respectively; both remain `prop_instance`. The old shared `water_storage_tank` classification is SUPERSEDED. Zones remain unknown. |
| H0079 | In A v4: `combined_junction_signal_lamp_sign` / `compound_junction_assembly`. The old simple-lamp classification is SUPERSEDED. Orientation, clearance, and graphics still need verification. |
| H0013 | `whole_instance` remains. **SUPERSEDED:** The claim that a broad paving/base floor was integrated, the requirement to preserve its area, and the hull comparison against this floor were withdrawn. According to H, the broad platform is Static Mesh Editor's `Floor_Mesh`/`M_Grid`. Actual footprint/contact remain unknown; this does not prove the absence of a small threshold/base. |
| H0016 | `whole_instance` remains. C described attached paving, but that remains a description from an earlier receipt, not a measured envelope/contact. H0013's inspection proves no conclusion about H0016. |
| H0905/H0906/H0907 | Retain domed landmark/pavilion and the local-fit condition. H0907 is already `domed_landmark_pavilion` in A; no ID correction or justification for ordinary housing follows. |
| H0647, Thicket_01/02, H0089, H0034/H0043, H0051 | In A v4, representation is `compound_vegetation_instance` for compound plants or `compound_prop_instance` for prop assemblies. One mesh instance is not the count of its pieces. Thicket_01/02 are `woody_thicket_cluster`; Thicket_03 is `tall_sparse_tree_form`. These are index corrections, not qualification or agreement on HDA-delivery enums. |
| H0039, dry/fallen palms, Palms_01_01–16 | Preserve condition, curvature, clearance, and variant IDs. Visual dryness does not prove biological death; there is no generic scale. |
| H0077, Stone_07/08 | H0077 in v4 is `construction_masonry_supply` / `compound_prop_instance`. Stone_07/08 remain `natural_stone`. Building supplies and natural/decorative stones are not evidence of rubble. |
| H0082/H0083, H0081, H0091 | Sign/poster meaning and local/period fit remain open. Rights evidence does not validate the graphics. |
| H0636/H0647/H0958/H0650/H0902/H0903/H0058/H0089 | Eight explicit material/quality blockers were merged into `technical_state` in v4; ineligibility remained. H0958 remains held for foliage: H documented leaf-shaped alpha in the exact imported Base Color texture, but the material is Opaque and alpha unconnected. No repair had been performed at this audit snapshot. |
| H0650 and `MI_baseMaterial_AC` | C documents a `StaticMesh` mesh and dependent `Material`. Do not write `Material` into H0650's `native_class`. |
| Courtyard/storefront/PBG | Whole/facade/module, backing/pairing/connectors differ. No preview proves BG1. |

[measured: A values] [documented: B,C; prior observations and role inferences, without a fresh visual check]

## Smallest delivery for CAT1, INST1, and Tier1

1. **Delivery envelope:** Catalog and subset paths, schema/catalog revision, hash, exact IDs, row count and role counts, one frozen alias map, and a use decision for the gate. Separate candidate data from the qualified subset. [documented: D §1]
2. **CAT1:** For each selected row: ID/variant/revision, object path/class, role/representation/family/zone/style/footprint, entitlement and evidence, weight, bounds/contact/axes/limits, ordered material bindings, and channel declaration. Missing numerical fields need validity=false and an explanation; a row with a required unknown is ineligible. Freeze Unreal property/display names, order, and types, then measure HAPI attribute names/storage/values for the same IDs. The `unreal_object_path` that the DataTable translator adds is the table path, not a mesh path; use the designated `ObjectPath` column. [documented: D §§2–5]
3. **INST1:** At least one qualified asset in two asymmetric placements, with separate placement IDs, transforms, and tile/role in the expected ledger. Use an approved channel that does not conflict with materials; a unique integer token 1…16777215; uniform K slots in an instancer group and complete measurement of N×K values. Separate asset ID, placement ID, actor/component, and instance count. Include material and mesh-path matches and check after bake/reopen/recook/replace. [documented: E, MEASUREMENT_SPEC]
4. **Tier1 under the proposed profile:** Two structures H0907/H0013, prop H0051, palm H0958, and an explicit blockout, alongside terrain/junction content owned by integration. The four canonical IDs below exist, but no qualified subset exists. Changing candidates requires a recorded decision; do not silently replace H0958 because it is blocked. [documented: E, VALIDATION_GATES] [measured: A]

| Historical label | Existing `asset_id` to preserve |
|---|---|
| H0013 | `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0013_Building_04` |
| H0907 | `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0907_Arab_x3_fbx` |
| H0051 | `current_Project__Shared__Bank_ME_v3__StreetFurniture__SM_H0051_Garbagebin` |
| H0958 | `current_Project__Shared__Bank_ME_v3__Vegetation__SM_H0958_CoconutPalm` |

The full path for each appears in A and matches C exactly. All four, including H0013/H0958, are documented as `native_class=StaticMesh` in v4. All four have `qualified=no`, `technical_eligible=false`, `generation_enabled=false`. Do not turn native observation into eligibility. Tier2 requires 10 building assets/modules, 10 props, and 5 plants actually used; that threshold is not a prerequisite for completing a small Tier1 subset. [measured: A,C] [documented: D,E,G]

## Deterministic checks and owners for completion

| Check | Pass rule | State / where to complete |
|---|---|---|
| Identity | Nonempty asset_id, case-insensitive uniqueness, explicit variant for a selected asset; ID/path match in measurement receipt | Identity in A and 75 joins passed; subset selection remains. Offline. |
| Typing/null | Explicit parsing; do not turn any nonempty string into true; finite numbers; unknown with reason; false-validity is not a measurement | CSV lacks types and validity fields. Binding and null policy can be prepared offline. |
| Source/path | Exact package/object match and revision evidence; supported class, load without redirector/default fallback | Syntax and source-file existence documented; class/preview-load receipts merged for 75 rows. BANK-ASTRA-005 closed the package-reference graph for only three candidates under its query policy; redirector/default fallback for the whole bank, dynamic references, and AssetRevision remain unproven. |
| Shape/contact | min≤max, dimensions=max−min; agreed local cm and build scale; signed contact; unit forward/up vectors with a valid basis | [measured: `Inspection_2026-09-29_Astra_Bounds/BANK_ASTRA_004_RESULT.md`; `Inspection_2026-09-29_Astra_Extensions_Retry/BANK_ASTRA_007R_RECEIPT.json`; `BANK_INDEX_V6_BOUNDS_RECEIPT_2026-09-29.json`] Local min/max and Build Scale measured for three; `_cm` interpretation fixed in v6; both bounds-extension vectors are zero in the tested versions. Contact, footprint, and axes remain open. [not run: BANK-PLACEMENT] |
| Selection | Subset by gate/role/zone, weight≥0 and positive for every required pool; stable ID order and recorded seed | Weights/zones missing throughout A; pool approval and scale/use decisions belong to the bank owner and Aviv. |
| Semantic role | Run02 proposals linked to original ID; no whole→module or tank→roof based on a name | 24 meaning/representation/blocker corrections merged; 46 `role_evidence` cells clarify documented class/form versus unverified exact use/local fit. Aviv approves local/period fit. |
| Materials and channels | Ordered slots with index/name/object path, dependency receipt, known custom-data channels | [measured: `Inspection_2026-09-29_Astra_Tier1/BANK_ASTRA_003_RESULT.md`; `Inspection_2026-09-29_Astra_Closure/DEPENDENCY_CLOSURE.json`; `Inspection_2026-09-29_Astra_Channels/MATERIAL_CHANNEL_AUDIT.json`] Six bindings measured and encoded in v5, retained in v6; the three roots have 21 explicit Content packages and 12 texture leaves. The six current material graphs contain only 12 TextureSample nodes and no per-instance reader, function, or custom/opaque path; UNUSED is proven only for those six versions. H0958 and every other material in the final subset need separate checking; do not reserve a global ID channel before that. |
| Revision | Schema/catalog/asset/inspection revisions remain distinct; a mesh/material-dependency change changes the corresponding receipt | Convention and derivative link need agreement; do not overload `source_revision`. |
| CAT1 | Equal row count and ID set; every consumed field equal in type and value; no unknown or lost column | [not run: CAT1] `actual_binding`/schema remain null. DataTable and HDA test requires an authorized task. |
| Determinism | In offline HDA, reordered rows and a disabled row do not change selection; invalid path fails; no fallback | [not run: HDA-SELECTION] HDA responsibility; this audit does not change the CSV. |
| INST1/lifecycle | Complete ledger; zero missing/extra/duplicate placement IDs; compare transforms/materials at every checkpoint; separate counts | [not run: INST1] Requires editor/HDA and an authorized gate. Actor labels and HISM indices are not stable IDs. |

**Narrow action order:** Linking the 75 C receipts to A and v4 corrections is complete. Close the stale alias map under separate authorization, retain unknowns, and decide only the remaining role proposals relevant to the subset. Then targeted measurements and material/rights/use evidence are needed only for gate candidates. Aviv approves use and exceptions; qualification and CAT1/INST1 remain separate tests. [proposed] A perfect bank is not required to deliver a qualified slice, but none exists yet. [measured: A] [documented: B,D,E,G]
