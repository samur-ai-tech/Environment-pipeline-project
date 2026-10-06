# Delivery of the five bank candidates before the coalition 2026-09-29

**Index update:** [Current v7](BANK_CANDIDATE_INDEX_2026-09-29.csv) Adds native readings to H0015 and 11 other v3 candidates; the data for H0013/H0907/H0051 was already in v6. Five of these delivery candidates remain off-line, with no verified contact/axis or connection to the generator. `A` The following is the historical v6 basis for the document; [diff QA](BANK_INDEX_V7_NATIVE_BATCH_DIFF_QA_2026-09-29.json) and[Manager's Check](Inspection_2026-09-29_Astra_V3_Batch/MANAGER_REVIEW_2026-09-29.md) Documenting the change to v7. [measured]

**There is no property here that is Qualified, Enabled or Ready for Tier1.** The four contract candidates are H0013, H0907, H0051, H0958; H0015 is a test-only alternative. In all five lines: `qualified=no`, `technical_eligible=false`, `generation_enabled=false`This document is not a running catalog and does not change selection, rights or canonical data.[measured: A, read on 2026-09-29]

When writing the original delivery only existing files and receipts were checked. A late and limited native test of H0907/H0013/H0051 was completed in BANK-ASTRA-003 and is summarized in the appendix at the end of this document. It is not a visual confirmation of spring. [documented: B; K below]

## Evidence Key

Relative pathways are from the root of environmentpipeline. `TB` = `C:/Users/USER/Documents/Pipeline Environment`.

- **A Current status:** `Staging/ModelBank/BANK_CANDIDATE_INDEX_2026-09-28.csv`; revision `v6_current_bounds_2026-09-29`; SHA-256: `BFEE371865DED0D32C9372F704FF0B333E869B4BFE6C72392A7DE8F98E2CC8E9`. v5 entered bindings measured in three rows off; v6 added only to these rows current asset-local AABB under fields `_cm`, with the meaning of the units and receiving the change in`BANK_INDEX_V6_BOUNDS_RECEIPT_2026-09-29.json`Any mention of A below refers to v6. v5 (`12225013B06810665B5E429299F1CD9E9931588AEAE4B1FFE1A33282B5719098`), v4 (`495985E2697C4BBBBE735E80184C5E73DA5B94A4444FEB5BAFDCBC6621ADEA42`V3 and V3`B05F8691402B47B4C6730F842163BD0555662C0802D4CA7EAADFE04266DCCC9F`They are historical photographs.
- **A-QA:** `Staging/ModelBank/BANK_INDEX_V5_SEMANTIC_DIFF_QA_2026-09-29.json` Restores hash v4 exactly after reversing the three substance cells, the six vision references and the`index_revision`; v5 also changed CSV's quoting style without any additional value changes. This is a semantic diff test, not a Qualification test.
- **B:** `Staging/ModelBank/Inspection_2026-09-28_Continuation/Native_Visual_Run_02/COMBINED_NATIVE_REVIEW.json`; Fields `asset_id`, `inspection_run`, `evidence_directory`, `evidence_files`. **R2** = same folder; **R1** = `Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01/`.
- **C:** `Staging/ModelBank/LICENSE_PROVENANCE.md`, section Owner configuration 2026-09-27.
- **D:** `Staging/ModelBank/BANK_SCHEMA_GAP_AUDIT_2026-09-29.md`.
- **E:** `Staging/TrackA_Tests/HoudiniCityProof/11_topic3_readiness_2026-09-28/BANK_INTERFACE_REQUIREMENTS.md`.
- **F:** In the same readiness folder: `VALIDATION_GATES.md`, `MEASUREMENT_SPEC.md`, `bank_field_alias_map.proposed.json`.
- **G:** `TB/CONTRACT.md` v0.6 DRAFT, §§4.4–4.5, 6.1; `AGENTS.md`.
- **H:** `Staging/HANDOFF_2026-09-28/MANAGER_HANDOFF_2026-09-28.md`; `Staging/PROJECT_STATUS_2026-09-27.md` Historical sources, not checking the status of the editor now.

## Exact identity

`H####` It's a read-only nickname in all five lines. `variant_id` Equal to`asset_id`; canonical identifiers should not be converted to aliases. The paths in A and B are compatible. [measured: A,B]

| Nickname | canonical `asset_id` | UE `unreal_object_path` |
|---|---|---|
| H0013 | `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0013_Building_04` | `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0013_Building_04.SM_H0013_Building_04` |
| H0907 | `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0907_Arab_x3_fbx` | `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0907_Arab_x3_fbx.SM_H0907_Arab_x3_fbx` |
| H0051 | `current_Project__Shared__Bank_ME_v3__StreetFurniture__SM_H0051_Garbagebin` | `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/SM_H0051_Garbagebin.SM_H0051_Garbagebin` |
| H0958 | `current_Project__Shared__Bank_ME_v3__Vegetation__SM_H0958_CoconutPalm` | `/Game/Project/Shared/Bank_ME_v3/Vegetation/SM_H0958_CoconutPalm.SM_H0958_CoconutPalm` |
| H0015 Alternative only | `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0015_Building_02` | `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0015_Building_02.SM_H0015_Building_02` |

## Native Findings and Possible Roles

The B report. `StaticMesh`, two UV channels and one primary collision per candidate. The number does not prove collision behavior. Nanite is not marked/false in all five; no performance measurement or LOD transitions. [measured: B] [not run: BANK-PERF]

| Candidate and Role | Visual and Material Findings from the Reception | LOD0 triangles / vertices; slots | The following focused evidence and pending decision |
|---|---|---|---|
| **H0013** — `whole_building` / `whole_instance` In A; possible use as a residential tower [inference] | A light gray tower with a graded mantle, blue-gray windows, pipes/air conditioners, roof rooms and a water tank; the rear wall is sealed. Run02 reported on an integral rectangular base floor, but this claim continued: two-material sections isolation leaves the same wide platform with grid, and Preview Scene settings display `Floor_Mesh`/`M_Grid`; The platform is a preview scenery. The property base, footprint and actual contact have not yet been measured. This is a temporary administrator correction according to the live observations, not a final BANK-ASTRA-001 acceptance. [documented: `Staging/ModelBank/Inspection_2026-09-29_Astra_Prep/LIVE_OBSERVATIONS.json`, entries `28_H0013_section0_isolated`, `29_H0013_section1_floor_correction`[No checkerboard or sealed foliage cards were observed.] **Run02_direct**, R2 `05_H0013_whole__1.jpg`, `08_H0013_back_framed__1.jpg`. [measured: B] | 44,241 / 45,927; 4 | Current local AABB and Build Scale have already been measured in L; complete geometry-only footprint, signed contact point and front; do not infer shell or collision defect from the display platform; check pitch and street line match. Spring sets local/period match and usage. No placement confirmation. [not run: BANK-WHOLE-PLACEMENT] |
| **H0907** — `domed_landmark_pavilion` / `whole_instance` | An entire polygonal structure with dome, arches, doors and windows of a tangle; light plaster/stone worn out. Tint boundaries and sharp spots in the dome in the display lighting. **Run01_prior**, R1 `06_H0907_whole__1.jpg`. [measured: B] | 3,302 / 4,835; 1 | Spring/contractor approves landmark in a suitable location or an express name exchange. Check local/period photography, match footprint/contact, and find out the dome tones in additional lighting and source material. Not a normal housing according to the recommendation of the reception. [inference] [not run: BANG-LANDMARK-ROLE] |
| **H0051** — `littered_pedestrian_waste_bin` / `compound_prop_instance` | A square tin with brown phases in a light metal frame; green bottles and debris are built into its head. Fine texture and ground contact have not been verified. **Run01_prior**, R1 `28_Garbagebin__1.jpg`. [measured: B; `BANK_CANDIDATE_INDEX_2026-09-28.csv`, v6] | 5,180 / 4,776; 1 | Check bottom/point of support, scale/axis and material closely; spring sets area and use in dirty mode, with clearance for transition and weight decision that does not generate repetitivity of the bottles. [inference] [not run: BANK-NATIVE-PROP] |
| **H0958** — `palm` / `vegetation_instance`; Source pending, P1 derivative passed limited proof | Run02 documented sealed leaf cards; `Original_Submesh_1` The original remains Surface/Opaque/Default Lit, Two Sided Off and Alpha Unconnected. BANK-ASTRA-001 Imported Alpha and Base Color Binding. BANK-ASTRA-002 has proven in isolated derivative Masked + albedo A to Opacity Mask. BANK-ASTRA-001 Confirmed Alpha and Base Color Binding. | 4,160 / 3,326; 2 | The source has not been repaired and the derivative is not a valid underset. Full shader/UV/normal/backface source required, root contact, title/race shell, performance, wind/LOD, gender and regional/period adjustment, and rights mapping for the selected use. Derivative adoption or candidate change requires explicit decision; no Masked/Two Sided sweeping. [NOTUN] |
| **H0015 Alternative only** — `mixed_use_whole_building` / `whole_instance` | A medium-sized, beige building is worn; five upper front rows above shutters/shops with shutters, roof rooms and panel-like element; glazed and open balconies, laundry and plates. In the blue glaze stains stand out. **Run01_prior**, R1 `55_H0015_whole__1.jpg`. [measured: B] | 201,057 / 211,808; 4 | First a decision on whether to test as a replacement and to which candidate; then a front/footprint/contact, clearance for balconies/roof, glaze check and performance budget. There is no evidence that it is a suitable replacement on the same field or BG module. [inference] [not run: BANG-ALTERNATIVE-SELECTION] |

Update 2026-09-29: BANK-ASTRA-001 has already provided the imported alpha vision and exact connection; BANK-ASTRA-002 completed P1 in derivative and preservation in two packages after opening in a new process. The previous claim for future vision only is SUPERSEED. The original H0958 remains opaque and pending; the derivative is not qualified. [documented: I,J]

## Recorded measurements are not verified contact

These are import values copied in A, not new placement measurements. UI native displays Approx Size without explicit units; it should not be used to fill cm fields. [documented: A, `Staging/ModelBank/ME/IMPORT_RESULTS_v3.json`] [measured: B]

| Candidate | Sizes X/Y/Z reported, cm | `reported_pivot_to_bottom_cm` Unverified signal/direction |
|---|---|---|
| H0013 | 2889.69 / 2130.93 / 4868.35 | `[-170.98, 16.46, 0.35]` |
| H0907 | 1369.04 / 1368.74 / 1560.66 | `[-4.17, 16.1, -0.68]` |
| H0051 | 29.4 / 34.43 / 74.4 | `[-1.86, 0.68, -0.0]` |
| H0958 | 605.24 / 612.81 / 870.63 | `[-134.07, 60.81, 0.0]` |
| H0015 | 2034.02 / 1170.84 / 2417.33 | `[282.94, -22.29, -0.1]` |

All five candidates lack the same mandatory data for delivery. Do not fill in defaults: [measured: A] [documented: D,E]

- **Bounds/contact:** in v6 `local_bounds_min_cm`/`local_bounds_max_cm` Filled only to H0907/H0013/H0051, based on current local-space AABB, Build Scale 1/1/1 and means unreal/Track A units documented in M below. BANK-ASTRA-007R index for both vectors extending zero bounds in the three properties; the AABB is still not a support form. `contact_offset_cm` Remains blank; marked contact for the job, geometry-only footprint and H0958/H0015 boundaries are still missing. A Pivot or Bounds-bottom vector should not be copied as a contact.
- **Orientation/limits:** `forward_axis`, `up_axis`, `scale_min`, `scale_max` Blank; yaw/rotation rule and nonuniform scale permission are not closed. The front, contact base and placement shell must match the specific role.
- **Materials/dependencies:** in v6 `material_paths` Contains an organized JSON with a slot index/name/object path only for H0907/H0013/H0051; 1,212 lines still empty. BANG-ASTRA-005 Close to three rows off package-reference closure by limited registry policy: 21 content packs, 12 texture leaves and limit `/Script/NavigationSystem` BANK-ASTRA-006 found in their six materials only 12 TextSample nodes and without a per-instance reader or an opaque branch; UNUSED applies to only six of these material variants. shader Fidelity, dynamic references, H0958 materials, AssetRevision and positionability are still missing. `KeepDefaultMaterials` Requires a statement for each eligible subset; no overall ID channel is allowed to assume a blank.
- **Selection/use:** `allowed_zones`, `selection_weight` Empty; footprint/style/role tokens and unfrozen gate usage decision. No approved area, weight or scale is implied. `decision=keep` Keeps a candidate for research and is not a generation certificate.
- **Identity delivery:** Asset/material revision, schema/catalog revision/hash of the running subset and actual Alias binding have not yet been delivered; resolve/class is required without redictor/fallback and obtaining qualification for the role. Native preview sequence does not fulfill this.

## Rightsseparate from qualifications

All five within 32 properties `Bank_ME_v3` That the Spring Declaration of 2026-09-27 covers. It means: Rights do not block the **The Technical Examination** Of these assets; there is no need to reapply for the same statement. `rights_eligibility_scope=technical_qualification_only_owner_confirmation`There is no attachment receipt/EULA; attribution/redistrification conditions for future exports are not documented. The statement does not authorize a role, plot, material, Tier1 selection or generation; an alternative property outside this scope requires its own clarification. [documented: C][measured: A]

## Three different gates and Tier1 scope

- **CAT1 Data Transfer:** Subset freezing/consenting and mapping; the same group of IDs and the same types/values are consumed in Unreal and HDA, with no missing fields/order/redirector/fallback. Metadata transition is not a proof of substitution or qualication. No dataTable/exported chema is now verified. [documented: D,E,F] [not run: CAT]
- **INST1 Actual placement:** A qualifying asset, two asymmetric posts and a separate placement IDs/tokens; comparing transforms/contact/materials and the Ledger after Bake, Fresh-Process Reopen, Relook and Replace, No Missing/Extra/Duplicate. This is a mechanism check; it does not replace the four specified Tier1 assets. [dot:Dotted]
- **BG1 Modules:** Only required if using Labs Building Generator. A module requires real geometry, profile, connectors, dimensions, axes, seams/UV/materials verified. Whole building is an entire object placed on a suitable footprint using `unreal_instance`; metadata or label change does not make it a module. H0013/H0907/H0015 is not a BG delivery. [documented: E 4,G 4.4] [not run: BG1]

The current profile requires H0907 + H0013, H0051, H0958, marked blockout, ground and node; H0015 is not automatically added to the count. Bank barriers are part of the preparation; proper HDA, B1/B2 and their decisions are also required, full approval for v0.6 and a licensed editor window. CAT1/INST1 is not a route to override this draft rule. There is no need to complete the entire bank or Tier2:

## Transfer documentation gaps for the manager

1. **Historical v3 photo, SUPERSEED:** The original A is written `not_run`/empty class for H0013 and H0958 despite receipts `Run02_direct` In B. in CSV v4 saved in J both `StaticMesh` With partial preview; the source H0958 still helped. H0907/H0051/H0015 in B are **Run01_prior**; Late Return Receipts are kept separately, and BANK-ASTRA-002 is proof of the H0958 derivative. Update of this document does not change CSV. [documented: A,B,J; `Staging/ModelBank/BANK_INDEX_V4_MERGE_RECEIPT_2026-09-29.json`]
2. G calls H0907 one of the two structures on matching footprints; the dome find requires a landmark or explicit substitution to be decided. F already records the block; it does not have a replacement permit. [documented: G,F] [measured: B]
3. H includes a statement that Tier1 is reachable with the bank with the Declaration of Rights. Facing nativist evidence is at most potential: H0958 materially blocked and the rest has not yet been past placement/role classification. [documented: H] [measured: A,B]
4. G 4.5 describes rounded pivot offsets H0958 1.5m / H0013 1.7m; this is not the signaled local contact required according to E. Neither are the three numbers in A verified contact. [documented: G,E] [measured: A]

**Next pass:** The above-targeted usage decisions  Authorized Measurement/Repair Only  Acceptances Placement/Material/Role  Subset is eligible with mapping/revisions  CAT1/INST1 and the approved Tier1. All five are now candidates only. [documented: DG]

## H0958 Proof of BANK-ASTRA-002 derivative, update 2026-09-29

**I Acceptance of proof:** `Staging/ModelBank/H0958_MaterialRepair_Proof_20260929/BANK_ASTRA_002_RECEIPT.json`. **J Final Authentication:** `Staging/ModelBank/H0958_MaterialRepair_Proof_20260929/FINAL_VALIDATION.json`[documented: I,J] Proof of limited technical material passed derivative: P1 is Surface/Masked/Default Lit, with Albedo A to Opacity Mask; Two Sided Off. Seen on leaves separated in Front/Back views and saved the situation after opening a new process. P2 was not spawned because the paired view does not detect a full disappearance symptom from the appointed face; this test is not.

The only two exact test packages are `/Game/Developers/USER/ModelBankProof/H0958_MaterialRepair_20260929/SM_H0958_CoconutPalm_Proof` and`/Game/Developers/USER/ModelBankProof/H0958_MaterialRepair_20260929/M_H0958_Leaf_Proof`J records two added Content files, zero unexpected Content changes, 26/26 hashes protected compatible and two hashes of matching derivatives before/after reopening. The source H0958 and its materials have not been modified: the source remains opaque/held, and the derivatives are not a canonical replacement. While BANK-ASTRA-002 the CSV remains v4 with hash `495985E2697C4BBBBE735E80184C5E73DA5B94A4444FEB5BAFDCBC6621ADEA42`; The current state is A above.

[not run: BANK-FOLIAGE-ROLE-QUALICATION; BANK-GEN] There is no quotient, wide-use rights certification, linked, generalized, scene visual certification or received. The previous technical owner's approval is not extended. source-shader-fidelity, UV/normal/recoverface complete, NoMipDraws.

## BANK-ASTRA-003 Limited Native Update, 2026-09-29

**K Receiving the test:** `Staging/ModelBank/Inspection_2026-09-29_Astra_Tier1/BANK_ASTRA_003_RESULT.md`; Screen evidence, `OBSERVATIONS.json` and`FINAL_VALIDATION.json` In the same folder. [measured: K] Unreal unit check closed unguarded. In independent admin check: 5,991 before and after content files, unchanged path/size/mtime; 174/174 compatible protected signatures, including v4 catalog; zero Unreal/Houdini processes after port. `Staging/ModelBank/EDITOR_OWNER.txt` Released to`OWNER=NONE` At 12:35:21. Side effects under `Saved` Recorded in`FINAL_VALIDATION.json`.

| Candidate | A New Fact Measured | What hasn't been decided yet |
|---|---|---|
| H0907 | Single material, slot `Arab_X3`Path, Path `/Game/Project/Shared/Bank_ME_v3/Buildings/Arab_X3.Arab_X3`The border of tint and stripe around the base of the dome; an open bottom partly in view. | Reason for the change of hue, contact/footprint, approved role/style. |
| H0013 | The preview floor was hidden and confirmed as the wide surface source; the building itself displays openings on the front side of the display and an almost sealed wall on the back side. Four materials in the order of slots 03: `Material_Building_04_1011`, `Material_Building_04_1001`, `Material_Building_04_1031`, `Material_Building_04_1021`Everyone in`/Game/Project/Shared/Bank_ME_v3/Buildings/`. | A complete absence of a combined base should not be inferred; in the K stage the local bounds have not yet been measured (later measured in L). Signed contact, footprint and semantic front axis are still UNKNOWN. |
| H0051 | Single Material `Street_Props_Pack__003` In`/Game/Project/Shared/Bank_ME_v3/StreetFurniture/`The durations of frame supports under the tin body and bottles/waste are built over it; the bottom of the wall appears to be in the frame. | The height of the trash-free tin and numerical contact points is still UNKNOWN. |

[not run: BANK-ROLE-QUALIFIcation; CAT1; INST1; TIER1] The six exact material paths and order are kept in K. Following the proposed absorption contract `MATERIAL_BINDING_CONTRACT_2026-09-29.md`, they were encoded in v5 as JSON arranged in three off rows. The encoding does not close material/texture dependencies or promote `technical_eligible`, `qualified`, `generation_enabled`,Connected, Generated or Accepted; Contract v0.6 is still DRAFT.

In the offline comparison phase before L, the Astra test followed by an administrator test of `Staging/ModelBank/ME/IMPORT_RESULTS_v3.json` They found that at the time of arrival they were received `bounds_min`/`bounds_max` Scissors for the three properties using `StaticMeshTools.get_bounds`; Current mesh files matched K signatures, LOD/slots calls, and import file times. The import file does not have mesh signatures from the same point of time, so at this point the bounds have only been classified **[documented: IMPORT_RESULTS_v3.json, import-era]**L below provided the current measurement. Do not copy the `pivot_offset_to_bottom_centre_cm` To`contact_offset_cm`.

In the same file, `material_texture_deps` The initial is empty in the six materials; `material_texture_deps_after_save` The latter contains 1 texture dependencies for H0907, eight for the four H0013 materials, and three for H0051. The twelve texture files and six material files are currently present and included in the K signatures; this is evidence of existence and linkage at the time of import, without checking the dependency close, shader channel or current Fidelity. H0051's old slot name in imports, `Street Props Pack _003`, different from the current slot `Street_Props_Pack__003`The full path must be used under `StreetFurniture`Not in a substance of the same name under `Props`. [documented: IMPORT_RESULTS_v3.json] [measured: K]

## BANK-ASTRA-004 Current Boundaries and Dependencies, 2026-09-29

**L Getting the test:** `Staging/ModelBank/Inspection_2026-09-29_Astra_Bounds/BANK_ASTRA_004_RESULT.md`; `COMPARISON.json`, 27 Raw MCP Replies, Build Scale Photos and`FINAL_VALIDATION.json` In the same folder. [measured: L] received local-space axis-aligned bunding box valid for the three meshes; all min/max exactly the same as receiving import. In LOD0 of all three `Build Scale = (1.0, 1.0, 1.0)`The API/display itself does not mark longitudinal units; in the historical paragraph of L the units remain open, and M below closes their meaning for v6 delivery. Physical support, marked contact, or footprint should not be inferred from the AAB.

| Candidate | current min X/Y/Z | current max X/Y/Z |
|---|---|---|
| H0907 | `-680.353271484375, -700.4720458984375, 0.6762058734893799` | `688.6864013671875, 668.2713623046875, 1561.33740234375` |
| H0013 | `-1273.8673095703125, -1081.9207763671875, -0.3545195758342743` | `1615.8203125, 1049.0091552734375, 4868` |
| H0051 | `-12.837084770202637, -17.898235321044922, 3.5086711136500526e-07` | `16.559925079345703, 16.53656768798828, 74.40184783935547` |

[Measured:L] The current six materials are opened as`Material`; 12 registry dependencies directly open to approximately`Texture2D`, fine and in exactly the same paths to the field `material_texture_deps_after_save` of importation. `get_dependencies` Using`AssetRegistryDependencyOptions` Default; no recursive scan, shader pins/channels or Fidelity test. Unreal closed without a save request; independent admin test 5,991 unmodified content files path/size/mtime, 174/174 SHA-256 compatible signatures, identical v5 catalog and zero Unreal/Houdini processes.`OWNER=NONE` At 13:04:31. Phenomena `Saved` Only documented in L.

[not run: BANK-PLACEMENT; BANK-MATERIAL-CLOSURE; CAT1; INST1; Tier1] at the time of receipt of L, rights, roll/style/zone, contact, units `_cm`, the Custom Channels data track and operating conditions remain separate. M below closes the unit meaning only. There was no promotion to connected, generalized, visually received or accepted.

## v6 means units and limited bounces delivery

**M receiving v6:** `Staging/ModelBank/BANK_INDEX_V6_BOUNDS_RECEIPT_2026-09-29.json`After receiving L, the installed Unreal 5.8 settings were tested: `Engine/Config/BaseEditor.ini:600–603` Sets `DistanceUnits=EUnit::Centimeters`; `Engine/Source/Runtime/Engine/Classes/Engine/StaticMesh.h:2202–2204` Sets `GetBoundingBox` Local-space includes extensions bounds; `Plugins/HoudiniEngine/Source/HoudiniEngine/Private/HoudiniEnginePrivatePCH.h:113` Sets a factor of 100, and`HoudiniInputTranslator.cpp:2813–2819,5500–5518` Distributing Unreal limits at 100 and replacing Y/Z at Houdini login. Track A confirmed that this is enough for mapping L numbers to fields `_cm` of three candidate lines off. [documented: installed sources; Track A 2026-09-29 message] [measured: L,M]

v6 saves the raw X/Y/Z of Unreal; conversion `(x,z,y)/100` Takes place once at the HDA limit, and not again in the catalog. Do not double again in the Build Scale, which was 1/1/1. The Bounds are the AABB of the property including extensions, not geometry-only footprint or support points. In v6 exactly three lines with `local_bounds_min_cm/max_cm` and`material_paths` Filled; 1,212 other rows remain empty in these fields. All 1,215 rows still `qualified=no`, `technical_eligible=false`, `generation_enabled=false`Inversion of the six bone cells, the six visual references and the`index_revision` Restores exactly the previous hash v5, as specified in M. [measured: M]

[not run: BANG-PLACEMENT; BANG-MATERIAL-CLOSURE; CAT1; INST1; TIER1] At the time point of v6 before BANSK-ASTRA-005, index encoding does not measure physical source scale, marked connection, footprint, bin-only height, orientation, and no indexing.

## BANK-ASTRA-005 Limited package referrals closure, 2026-09-29

**N Acceptance of dependencies:** `Staging/ModelBank/Inspection_2026-09-29_Astra_Closure/DEPENDENCY_CLOSURE.json`, SHA-256 `03ADF90BAE77936AE8312517F612CB9D18FCDDC036A7F2E60202663A3543048A`; `BANK_ASTRA_005_RESULT.md`, raw `mcp/001–018` and`RECEIPT_SHA256.json` In the same folder. [measured: N] Three current mesh-root queries returned 1/4/1 materials and the `/Script/NavigationSystem`; 12 Texture queries returned explicit blank lists. The six materials lists and class receipts from BANK-ASTRA-004 were only re-used after adjusting the 21 package signatures and tool policy. The graph contains 21 content packs, 18 arcs between them and three arcs for a single module; a blank frontier. The module is linked to the installation of Unreal through receiving Track A, without proof of runtime load. The verdict is `COMPLETE_FOR_DECLARED_REGISTRY_POLICY` Only: hard/soft and game/editor package references are included in the default; searchable names, management, and dynamic references are not checked. The single arch type is not classified.

The administrator independently decoded the 21 adjacency and class receipts, compared all the arches and source files, verified the received hash, 5,991 unmodified content files and 174 compatible protected signatures. The editor closed and`EDITOR_OWNER.txt` Released at 13:30:03; corrected append-only at 13:33:02 clarifies that cache rotation in`Intermediate` A blog entry but not independently filmed. AssetRevision remains null and the three lines are left off. [not run: BANG-MATERIAL-GRAPH; BANG-PLACEMENT; CAT1; INST1; Tier1] There is no rights authorization, use, role, custom-data channel, connection to HDA, generation or acceptance.

## BANK-ASTRA-006 Graphic reading materials for per-instance channels, 2026-09-29

**O receiving the channels:** `Staging/ModelBank/Inspection_2026-09-29_Astra_Channels/MATERIAL_CHANNEL_AUDIT.json`, SHA-256 `A18B4E302B1C147B5CBA49DCCA81021013CCC61E6D73369A2D1D9F8462975EF9`; `BANK_ASTRA_006_RESULT.md`, raw `mcp/001–018` and`RECEIPT_SHA256.json` In the same folder. [measured:O] Six Calls `MaterialTools.get_expressions` Return 1/2/2/2/3 nodes. 12 exclamations `ObjectTools.get_class` On the exact refPath return all `/Script/Engine.MaterialExpressionTextureSample`No readers found. `PerInstanceCustomData` scalar/3Vector, function, custom HLSL, layer or opaque branch. Only six versions of the exact material have a result `verified_no_PerInstanceCustomData_reader_in_inspected_graph`; There is no Shader Compiled test or promise for future material.

The administrator independently compared each node list and class acceptance to a current material file and to the reception hash. 5,991 Content files and 174 protected signatures remain unchanged; `Saved` and`Intermediate` Photographed separately and include normal opening/closing effects. The editor closes and`EDITOR_OWNER.txt` Released at 13:45:41. CSV remains v6, and all 1,215 lines are blocked. [not run: H0958-MATERIAL-CHANNELS; CAT1; INST1; Tier1; ID channel is not reserved for all Tier 1: H0958 materials and the final subset has not been tested. No rights promotion, role, character shader, connection, generation or acceptance.

## BANK-ASTRA-007R Boundary Extension, 2026-09-29

**P Accept the extensions:** `Staging/ModelBank/Inspection_2026-09-29_Astra_Extensions_Retry/BANK_ASTRA_007R_RECEIPT.json`, SHA-256 `ADD4C52987A6B3715A4F8CE8E6103D2AA3F82E999F4F499A901A041B387126E8`; `MANAGER_REVIEW_2026-09-29.md` And three raw MCP answers in the same folder. [measured: P] Three readings `ObjectTools.get_properties` Return for H0907/H0013/H0051 also `PositiveBoundsExtension` And also `NegativeBoundsExtension` With X/Y/Z zero. The manager independently decoded the requests and answers and verified three current mesh signatures, 5,991 content files without meta-change, 174 compatible protected signatures and an identical v6 catalog. The editor was closed and released to`OWNER=NONE` At 14:34:12. The previous 007 run was interrupted before the readings and kept separate; it has no result.

The original AABB is kept as it is. Extension value zero removes only the property-defined ambiguity; it does not measure support vertices, useful footprint, semantic front or position adjustment. No change in`contact_offset_cm`, in forward/up or in the fitness flags. [not run: BANK-PLACEMENT; CAT1; INST1; BG1; Tier1]
