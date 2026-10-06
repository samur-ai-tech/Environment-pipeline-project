# Bank Consent Gaps Review 2026-09-29

**Late Update:** The current index is [v7](BANK_CANDIDATE_INDEX_2026-09-29.csv), SHA-256 `1553B0AFE81F816C1AD6F2F44CE4B1CEC6C3943E68251E4E73C7B61ACB3DC1B1`BANK-ASTRA-008 index bounces and 30 materials in 12 additional v3 assets; [Manager's Check](Inspection_2026-09-29_Astra_V3_Batch/MANAGER_REVIEW_2026-09-29.md) and[diff QA](BANK_INDEX_V7_NATIVE_BATCH_DIFF_QA_2026-09-29.json) Approving 15 rows with bounds/material pathways, 1,215 unqualified, and zero enabled. References to v6 below describe the original audit status. [measured]

At the time of the original review writing, only a file check was performed. This was followed by BANK-ASTRA-003 and 004 providing limited native observations; v5 encoded three material lists, and v6 added current local AABB in three off-line candidates. No import, asset repair, cook, Bake, or qualication was performed following the encoding. The integration requirements are documented proposals; the document does not confirm them.

**Conclusion:** There is a proper candidate index in terms of identifying uniqueities and the path syntax that has been tested, but it does not currently have an approved line for delivery to HDA. v4 has incorporated 75 native receipts and 24 technical significance/representation/block corrections; v5 has added ordered material bindings to three rows, and v6 has added a local AABB. BANK-ASTRA-005 closure to the three package-references for the six external register.Additional applicants, contact, orientation and eligibility are still lacking for CAT1/INST1. Qualification cannot be completed using alias. [measured: A,C; `Inspection_2026-09-29_Astra_Closure/DEPENDENCY_CLOSURE.json`; `Inspection_2026-09-29_Astra_Channels/MATERIAL_CHANNEL_AUDIT.json`] [documented: D,E,G]

## Sources and status of evidence

- **A:** `Staging/ModelBank/BANK_CANDIDATE_INDEX_2026-09-28.csv`Current v6 mode, SHA-256: `BFEE371865DED0D32C9372F704FF0B333E869B4BFE6C72392A7DE8F98E2CC8E9`; Receipts `BANK_INDEX_V5_BINDINGS_RECEIPT_2026-09-29.json` and`BANK_INDEX_V6_BOUNDS_RECEIPT_2026-09-29.json`. v5 (`12225013B06810665B5E429299F1CD9E9931588AEAE4B1FFE1A33282B5719098`), v4 (`495985E2697C4BBBBE735E80184C5E73DA5B94A4444FEB5BAFDCBC6621ADEA42`V3 and V3`B05F8691402B47B4C6730F842163BD0555662C0802D4CA7EAADFE04266DCCC9F`(Historic.
- **B:** `Staging/ModelBank/Inspection_2026-09-28_Continuation/Native_Visual_Run_02/BANK_INTERFACE_FINDINGS.md` and`BANK_SCHEMA_MAPPING_REPLY.md`.
- **C:** `Staging/ModelBank/Inspection_2026-09-28_Continuation/Native_Visual_Run_02/COMBINED_NATIVE_REVIEW.json` Previous test receipts, not new visual inspection.
- **D:** `Staging/TrackA_Tests/HoudiniCityProof/11_topic3_readiness_2026-09-28/BANK_INTERFACE_REQUIREMENTS.md`.
- **E:** In the same integration folder: `bank_field_alias_map.proposed.json`, `VALIDATION_GATES.md`, `MEASUREMENT_SPEC.md`.
- **F:** `AGENTS.md`; `Staging/HANDOFF_2026-09-28/MANAGER_HANDOFF_2026-09-28.md`The limitations of the contract, the ownership of the editor and the approval of the execution remain in force. The status of processes from the overlap is historical and has not been examined here.
- **G:** `Staging/ModelBank/BANK_INDEX_V4_MERGE_RECEIPT_2026-09-29.json` Merge 24 repairs and 75 receipts, and repair 46 cells `role_evidence` After review. Identifiers, routes, rights, eligibility flags, measurements/contact and protected fields have been retained.
- **H:** `Staging/ModelBank/Inspection_2026-09-29_Astra_Prep/BANK_ASTRA_001_RESULT.md` Repeated evidence of H0013/H0015/H0051/H0958; zero new unique candidates. H0013's display floor correction trumps the old interpretation in C.

## What is now measured

| Testing on A | Result |
|---|---|
| Number of rows / columns | 1,215 / 101 |
| `asset_id` | 1,215 complete; 0 duplicates also in comparison that are not sensitive to large/small letters |
| `variant_id` | 1,188 complete and unique; 27 blank, all `family_candidate` |
| `unreal_object_path` | 930 complete and unique; 0 syntax failures `/Game/.../Object.Object`; 285 blank |
| 930-line source file with object path | All 930 Values `source_path` Exist on disk; not a loading test or redirector |
| Obstruct Path vision within the index | 75 documented in native receipts; 855 by file name only agreed; 285 `not_imported_here` |
| `native_class` | 73 `StaticMesh`Two, `Material`1,140 empty. |
| `qualified` / `technical_eligible` / `generation_enabled` | In all 1,215 lines: `no` / `false` / `false` |
| `index_revision` | In all lines `v6_current_bounds_2026-09-29` |
| `material_paths` | Three JSON lists are arranged for H0907/H0013/H0051; 1,212 empty; unmodified as a service |
| `local_bounds_min_cm/max_cm` | Two numeric vectors in three rows H0907/H0013/H0051; 1,212 empty. BANK-ASTRA-007R Index for the six expansion vectors of the three properties `(0,0,0)` In current versions; the AABB is not yet footprint or contact. |
| C vs A | All 75 of the receipt identifiers and object paths have been precisely adjusted and integrated into the native/inspection fields; this is a record match rather than a new native authentication. H records four repeat tests without increasing coverage |
| Index Exception | `SM_Hazel_14_G.native_triangles` Remains blank: 206 in C-receiving is marked as being re-verified and is not copied to index; mesh metrics of two blank material rows |

[Measured: A,C; CSV/JSON reading, grouping identifiers and paths and checking source_path existence on 2026-09-29]

**Types and missing:** CSV does not define types; in reading all 101 fields are strings. `false` and`no` They are text, not Boolean; an empty field is an empty string, not JSON null. in dimensions fields `dimensions_x_cm`, `dimensions_y_cm`, `dimensions_z_cm` There are 32 numeric strings. `reported_pivot_to_bottom_cm` Fill in 32 lines as a three-number text list, for example `[-170.98, 16.46, 0.35]` For H0013. He **Not scalar in all records**, but neither is the vector contact verified: `pivot_convention` In the same lines says that the mark and direction have not been independently verified. It should not be inferred from it even after a successful parsing. [measured: A]

All of the following fields exist in the title and are blank in all 1,215 lines: `contact_offset_cm`, `forward_axis`, `up_axis`, `scale_min`, `scale_max`, `selection_weight`, `allowed_zones`. `material_paths` and`local_bounds_min_cm/max_cm` Only three lines are filled out as stated above. No missing 0, default axis, free range or allowed area. [measured: A]

## Alias Table and Minimum Gap

The target types are documented in the integration proposal: String, Int32, Boolean and Float32. All `actual_binding` In alias map still null; `actual_exported_schema` null. `source_schema` The map states `bank_candidate_index_2026-09-28_v3_astra_native_preview_01` While the actual index v6 and includes native fields; the actual title delivered must be frozen. [documented: E, `bank_field_alias_map.proposed.json:4`] [measured: A]

| Existing fields are accurate | Destination field/climbing | Alias or gap/complement |
|---|---|---|
| `asset_id`, `family_id`, `variant_id` | `AssetId`, `FamilyId`, `VariantId` / String | Precise retention; do not invent a short ID or turn a family line into a choice property. Check out offline. |
| `unreal_object_path`, `unreal_package_path`, `object_path_verification` | `ObjectPath` / String | The package path is not an object path. 930 candidates for proper syntax only; loading, class and absence of a redirector require a native receipt. |
| `native_class` | `AssetClass` / String | **The field already exists.**, although the map shows an empty source list. Native receipts can be tied to an ID; blanks remain unknown. A class of material is not a class of mesh that uses it. |
| `index_revision` | `CatalogRevision` / String | Revision of the index, not necessarily of the delivery subset; freeze path/hash/revision/line list for delivery. |
| `source_revision`, `source_catalog_sha256`, `inspection_revision` | `AssetRevision` / String | No safe alias: source, index and inspection are not a revision of mesh and its materials. Lack of revision of the property and dependencies. |
| `source_catalog`, `source_revision`, `source_catalog_sha256`, `source_package`, `source_path` | `SourceProvenance` / String | You can preserve source and offline connections; no proof of rights. |
| None `SchemaVersion` | `SchemaVersion` / Int32 | Metadata of the delivery; requires consent on a consent revision, not a guess. |
| `functional_role`, `category`, `representation`, `style`, `allowed_zones` | `Role`, `Representation`, `StyleTokens`, `AllowedZoneTokens` / String | `category` Organizational is not role; `bg_module_candidate` Is not `bg_module` Capable. enum dictionaries and tokens are not frozen; empty areas mean there is no approved area. |
| `condition`, `environment_context`, `building_type`, `architectural_role`, `tags` | There are no matching fields in the 54 column proposal | Keep metadata; if selecting HDA consumes it, freeze explicit binding before delivery. Do not leave out quietly and do not infer from names. |
| `technical_state`, `technical_eligible`, `qualified`, `evidence`, `inspection_evidence`, `role_evidence` | `TechnicalStatus`, `QualificationEvidence` / String | Preview is not qualification; evidence of the intended role and use must be tied. |
| `rights_state`, `rights_eligibility_scope`, `decision`, `decision_reason` | `RightsEvidenceStatus`, `UseDecisionReference` / String | Separate Evidence Rights from Use Decision. 32 `technical_qualification_only_owner_confirmation` Not a confirmation generation. Spring resolution and scope of use are required. |
| `generation_enabled`, `qualified`, `technical_eligible`, `rights_eligibility_scope` | `RunEligible` / Boolean | No single flag copying; express subset for goal and position, no binding missing persons. Currently zero qualifying under A. |
| `selection_weight` | `SelectionWeight` / Float32 | All missing; final value not negative, at least one positive weight per roll/zone is required.0 Only a deliberate downtime. |
| `local_bounds_min_cm`, `local_bounds_max_cm`; `dimensions_*_cm` | `BoundsMin/Max{X,Y,Z}Cm` / Float32; `BoundsValid` / Boolean | Full v6 in only three lines H0907/H0013/H0051: current local-space AABB, Build Scale 1/1/1 and cm units linked through Unreal/Track A. BANK-ASTRA-007R Index `PositiveBoundsExtension` and`NegativeBoundsExtension` Zero in all three meshes; this removes extension ambiguity only, and is not geometry-only footprint or contact. 1,212 lines remain unknown. |
| `contact_offset_cm`, `pivot_convention`, `reported_pivot_to_bottom_cm` | `Contact{X,Y,Z}Cm` / Float32; `ContactValid` / Boolean | No verified contact. Measuring a sealed contact point in local space; not copying a Pivot-to-bottom or Bounds-bottom. |
| `forward_axis`, `up_axis` | `Forward{X,Y,Z}`, `Up{X,Y,Z}` / Float32; `OrientationValid` / Boolean | Empty; Front/Upward direction requires measurement and determination for the role. |
| `scale_min`, `scale_max`; no other fields limits | `UniformScaleMin/Max`, `YawMin/MaxDeg` / Float32; `PlacementLimitsValid`, `AllowNonuniformScale` / Boolean; `RotationRule` / String | Missing values and user decision. do not infer scale=1 or free yaw. |
| `material_paths`, `native_material_slots` | `MaterialBindingsJson`, `MaterialCustomDataChannels` / String; `KeepDefaultMaterials` / Boolean | v6 preserve index/name/object path are arranged in only three rows off. JSON format is mounted in`MATERIAL_BINDING_CONTRACT_2026-09-29.md` [Proposed]. These three lines were checked for limited packet-reference in BANK-ASTRA-005; in BANK-ASTRA-006 the six exact materials were examined and no reader was found `PerInstanceCustomData`, as detailed in External Acceptance. This is an unused statement for only six material versions; H0958 and the final subset are not covered. Empty channel field without linked receipt is not unused proof. KeepDefaultMaterials=true preserves defaults only on the proposed transfer route, after separate classification. |
| No footprint/profile/module measures | `FootprintClass`, `ModuleProfileId`, `ModuleQualificationEvidence`, `ModuleName` / String; `ModuleWidthM/HeightM` / Float32; `ModuleDimensionsValid` / Boolean | Footprint is required for the job; over-module fields are conditional on BG. Dimensions or profile should not be invented. BG1 and module geometry are only required if BG is used. |
| `technical_variant_of` | Derivative LinkSource and Asset Revision | The meaning of the field does not authorize such a new use. The bank owner establishes a link and revision; no existing IDs are to be changed or a derivative temper is corrected by name. |

[Measured: A] [documented: B,D,E] Every new binding in the table is [proposed], not a canonical change.

## Meaning corrections incorporated into v4 and gaps remaining

| Assets Short labels for reading purposes only | The Gap vs. A and Treatment |
|---|---|
| H0090 / H0091 | In A v4: `ibc_liquid_storage_container` / `drinking_water_dispenser`, respectively; both remain `prop_instance`The Old Common Classification. `water_storage_tank` It is SUPERSEED. Areas remain unknown. |
| H0079 | In A v4: `combined_junction_signal_lamp_sign` / `compound_junction_assembly`The old simple lamp classification is SUPERSEED. Authentication of orientation, clearance and graphics is required. |
| H0013 | `whole_instance` Saved. **SUPERSEDED:** The claim to the Paving/Base floor is integral, the duty of preserving its area, and the comparison of the hull against this floor continued. According to H the broad platform is `Floor_Mesh`/`M_Grid` The Static Mesh Editor. true footprint/contact is still unknown; this does not prove that there is no small threshold/base. |
| H0016 | `whole_instance` Preserved. C described a connected paving, but this remains a description at previous reception rather than a measured shell/contact. H0013 test does not prove a conclusion on H0016. |
| H0905/H0906/H0907 | Keep domed landmark/pavilion and match conditions in place. H0907 already `domed_landmark_pavilion` In A; there is no ID patch or justification for normal housing. |
| H0647, Thicket_01/02, H0089, H0034/H0043, H0051 | In A v4 the representation is `compound_vegetation_instance` For the complex plants or `compound_prop_instance` For props assemblies. One mesh instance is not the number of its parts. Thicket_01/02 are `woody_thicket_cluster`; Thicket_03 is `tall_sparse_tree_form`These are index corrections, not qualication or consent on enum in HDA delivery. |
| H0039, Dry/Flower Palms, Palms_01_0116 | Maintain status, curvature, clearance and variant IDs. Visual dryness is not evidence of biological death; there is no general scale. |
| H0077, Stone_07/08 | H0077 in v4 is `construction_masonry_supply` / `compound_prop_instance`.Stone_07/08 Left `natural_stone`The supply of construction and natural/decorative stones is not evidence of rubble. |
| H0082/H0083, H0081, H0091 | Sign meanings/posters and local/period adjustments are still open. Rights view is not graphics validation. |
| H0636/H0647/H0958/H0650/H0902/H0903/H0058/H0089 | Eight explicit material/quality barriers were incorporated in`technical_state` In v4; non-entitlement is maintained. H0958 remains in the foliage barrier: H documented leaf-shaped alpha in the exact imported Base Color texture, but the Opaque and alpha material is not connected. No correction has been made. |
| H0650 and the material `MI_baseMaterial_AC` | C Documents Mesh Type `StaticMesh` and type dependent material `Material`No writing. `Material` To the native_class of the H0650 line. |
| Courtyard/storefront/PBG | Whole/facade/module, backing/pairing/connectors are distinguished. No preview proves BG1. |

[measured: A values] [documented: B,C; previous observations and roulette inferences, no visual re-verification]

## The smallest delivery to CAT1, INST1 and Tier1

1. **Delivery shell:** The catalog path and subset, schema/catalog revision, hash, exact identifiers, multiple lines and roulette accounts, one frozen alias map, gate usage decision. Candidate data must be separated from the qualifying subset. [documented: D 1]
2. **CAT1:** Each row is selected: ID/variant/revision, object path/class, role/representation/family/zone/style/footprint, eligibility and evidence, weight, bounces/contact/axes/limits, order-material bindings and channel-based configuration. `unreal_object_path` Adding a DataTable translator is a table path, not a mesh path; use a column `ObjectPath` Designated. [documented: D 25]
3. **INST1:** At least one qualifying asset in two asymmetric positionings with separate placement IDs, transforms and rollFludger expected. Confirmed channel that does not collide with the material; complete unique token 1...16777215; K slots uniform in the indexer group and complete measurement of NK values. Separate asset ID, position ID, actor/component and instance to the material.
4. **Tier1 according to the proposed profile:** Two H0907/H0013 structures, prop H0051, palm H0958 and an explicit blockout, alongside the ground/node content of the integration responsibility. There are four canonical identifiers below, but no subset qualified. Modification of candidates requires a documented decision; H0958 should not be quietly replaced because of the blockage. [documented: E, Validation_GATES] [measured: A]

| Historical label | `asset_id` Existing to be preserved |
|---|---|
| H0013 | `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0013_Building_04` |
| H0907 | `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0907_Arab_x3_fbx` |
| H0051 | `current_Project__Shared__Bank_ME_v3__StreetFurniture__SM_H0051_Garbagebin` |
| H0958 | `current_Project__Shared__Bank_ME_v3__Vegetation__SM_H0958_CoconutPalm` |

The complete path for each is listed in A and is precisely adapted to C. The four, including H0013/H0958, are recorded as`native_class=StaticMesh` in v4. The four `qualified=no`, `technical_eligible=false`, `generation_enabled=false`. . . does not make native observation eligible. Tier2 requires 10 building assets/modules, 10 props and 5 plans that were actually used; this threshold is not a prerequisite for completing a small underset for Tier1. [measured: A,C] [documented: D,E,G]

## Deterministic testing and the owner for completion

| Test | Transition Rule | Status / Where to Complement |
|---|---|---|
| Identity | nonempty asset_id, case-insensitive singularity, express variant to selected property; ID/path adjustment at measurement reception | Identity in A and 75 joins have passed; subset selection has not yet been performed. Offline. |
| typing/null | Explicit parsing; no non-empty string conversion to true; finite numbers; unknown with reason; false-validity does not measure | CSV lacks typing and validity fields. Binding and null police can be prepared offline. |
| source/path | Precisely adjust package/object and for revision vision; supported class, loading without redirect/default fallback | Syntax and source files were documented; 75 entries were combined with class/loading receipts and preview. BANK-ASTRA-005 closed to only three candidates the package references graph as per the query policy; redistrictor/default fallback to all bank, dynamic references and AssetRevision have not yet been proven. |
| shape/contact | minmax, dimensions=maxmin; local cm and build scale agreed; signed contact; forward/up unit vectors with valid base | [measured: `Inspection_2026-09-29_Astra_Bounds/BANK_ASTRA_004_RESULT.md`; `Inspection_2026-09-29_Astra_Extensions_Retry/BANK_ASTRA_007R_RECEIPT.json`; `BANK_INDEX_V6_BOUNDS_RECEIPT_2026-09-29.json`[ ] Local min/max and Build Scale were measured to three; meaning `_cm` Locked in v6; the two bounds expansion vectors are zero in the tested versions. contact, footprint and axes did not close. [not run: BANK-PLACEMENT] |
| selection | Subset to cover/role/zone, weight0 and positive for each pool required; stable IDs order and recorded seed | Weights/zones are missing in all A; pool approval and scale/use decisions by the bank owner and spring. |
| semantic role | Run02 offers are linked to the original ID; there is no wholemodule or tankroof by name | 24 meaning corrections/representation/blocking were incorporated; 46 role_evidence cells clarify a class and a documented form compared to accurate/unverified localization usage. |
| Material and Channels | Slots are arranged with index/name/object path, dependency receipt, known custom data channels | [measured: `Inspection_2026-09-29_Astra_Tier1/BANK_ASTRA_003_RESULT.md`; `Inspection_2026-09-29_Astra_Closure/DEPENDENCY_CLOSURE.json`; `Inspection_2026-09-29_Astra_Channels/MATERIAL_CHANNEL_AUDIT.json`[Six bindings have been measured and encoded in v5 and saved in v6; the three roots have 21 content packs and 12 explicit texture leaves. The six current material graphs contain only 12 TextureSample nodes and without a per-instance reader, a function or custom/opaque path; UNUSED proof only applies to these six versions. H0958 and any other material in the final subset requires a separate test. |
| revision | Schema/catalog/asset/inspection are distinguished; mesh/material change changes appropriate receipt | Convention and derivative link require consent; not overload of source_revision. |
| CAT1 | row count and ID set are equal; each field consumed is equal in type and value; no column is unknown/lost | [not run: CAT1] Actual_binding/schema still null. DataTable and HDA check when authorized. |
| determinism | In the HDA offline: order rows and disable rows do not change selection; Invalid path fails; no fallback | [not run: HDA-SELECTION] Guaranteed HDA, not CSV change within this review. |
| INST1/lifecycle | Full Ledger; Zero Missing/Extra/duplicate Placement IDs; Comparison of Transforms/Materials at Each Checkpoint; Separate Counts | [not run: INST1] Requires an editor/HDA and a licensed gateway. Actors labels and HISM index are not stable IDs. |

**Limited order of action:** 75 C-receipts to A and v4-repairs are completed; the obsolete alias map must be closed under a separate permission, preserve unknowns and only decide on roll suggestions that remain relevant to the subset. Then targeted measurements and material/rights/use evidence are required only for gate candidates. Spring permits use and exceptions; qualication and CAT1/INST1 remain separate tests. [proposed]
