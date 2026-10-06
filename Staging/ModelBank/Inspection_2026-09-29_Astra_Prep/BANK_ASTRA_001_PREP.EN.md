# BANK-ASTRA-001 — Subset Preparation and Measurements

Date: 2026-09-29. Owner: Astra `01a0e820-c6d4-7702-8e7b-55fd20f9b020`.

**Preparation-time status:** the packet was prepared before an editor lease existed; no asset was qualified. **Authorized window:** the manager subsequently recorded BANK-ASTRA-001 for this operator from `2026-09-29T02:20:17.3257739+03:00` through `2026-09-29T03:05:17.3257739+03:00` [documented: `../EDITOR_OWNER.txt`, entry dated 02:20:17]. **Final status:** bounded inspection completed, Unreal closed without saving at 02:43:37, and the manager recorded OWNER=NONE at 02:45:08.9357886 +03. See `BANK_ASTRA_001_RESULT.md` and `LIVE_RELEASE_CHECK.json`. No asset was qualified. The bank manager `01a0e7e2-2aac-7a63-a913-e58b1f3714a2` owns the catalog. Writing is limited to this folder; Run01/Run02 and the catalog are preserved.

**Corrections after inspection:** the broad gridded platform around H0013 is preview scenery; the earlier integral-paving interpretation is withdrawn. H0958's imported alpha and exact Base Color texture binding are now measured, while the Opaque material leaves alpha disconnected. Detailed historical metrics and the proposed click list below are preparation records; the result receipt states what actually ran and what remains unknown.

## Conclusion and proposed minimum subset

[inference] The focused pair for preparing a whole-instance measurement is **H0013 + H0051**: a whole building and a street item, without replacing or repairing a source. **H0015** remains a residential-over-retail alternative with a different envelope and height. This is a measurement candidate subset, not a qualified subset or a complete Tier 1.

[documented: CONTRACT.md §6.1] The Tier 1 draft names H0907 and H0013, H0051 and H0958, as well as terrain, a junction, and a blockout. Therefore, the five preparation records also include H0907 and H0958. H0015 does not replace a contract asset without an explicit change. BG1 is a separate open module test; it should not be invented as a prerequisite for a slice defined around whole buildings.

[documented: Run02/COMBINED_NATIVE_REVIEW.json] **None of the three Bank_ME_v3 vegetation assets is qualified or free of a known material defect**: H0636, H0647, and H0958 show foliage-card or material failures. Palms_Pack_01 is outside the rights approval scope for the 32 v3 assets and does not automatically replace H0958.

[measured: H0958_SOURCE_ALPHA_READOUT.json] The H0958 leaf source file is RGBA, 322×1024. It contains 223,817 pixels with A=0 and 105,911 with A=255, with no intermediate values. The copy in the Textures folder has the same SHA-256. An alpha channel exists; its fit for the intended mask and survival in the imported texture are not yet proven. The opaque graph is documented in Run02; nothing was changed or repaired here.

## Queue and gate results

| Order | Short ID | Proposed role | Role in queue | Material/role gate | Overall state |
|---|---|---|---|---|---|
| 1 | H0013 | Tall whole residential building; the grid surface is the preview floor | Contract building; model envelope and support points still need measurement | UNKNOWN: preview partly sound; contact, front, and footprint missing | candidate / unqualified |
| 2 | H0015 | Residential-over-retail building | Proposed alternative; inspect glazing and balconies | UNKNOWN: mottled glazing and cost not checked | candidate / unqualified |
| 3 | H0051 | Street bin with integral bottles/litter | Contract prop; support points and use orientation | UNKNOWN: detail/contact missing | candidate / unqualified |
| 4 | H0958 | Palm, species/period unverified | Alpha and dependency diagnosis only | FAIL: opaque leaf cards; source alpha exists | HOLD / unqualified |
| 5 | H0907 | Special domed structure/pavilion | Contract asset; prior receipt only in this task | UNKNOWN: local fit and dome color boundaries | reserve / unqualified |

For all five: PASS only for prior asset loading and recorded owner approval for technical qualification. Qualified, connected, generated, scene visually verified, and accepted remain false. The detailed table’s allowed_zones values are proposals, not an active permission list.

## Exact records — measurement status

### H0013

- asset_id / variant_id: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0013_Building_04` (unchanged).
- Unreal object: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0013_Building_04.SM_H0013_Building_04`.
- Current file: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0013_Building_04.uasset`. SHA-256: `e5bb8f2ca2cf7ac473fa479251725933123a31f9f9d41d775eb11e675a039da6`.
- Role `[inference]`: `tall_residential_whole_building`; proposed representation `whole_instance`.
- Proposed zones only: `["residential_parcel_matching_full_base_envelope"]`; approved allowed_zones: UNKNOWN.
- Observed condition: weathered. The earlier integral-paving interpretation is withdrawn: separate section isolation confirms the broad grid platform is preview scenery [measured: LIVE observations 28–29].
- Material: No default/checkerboard appearance in inspected views; four loaded materials. Close surface, seam and underside QA incomplete.
- `[documented: ME/IMPORT_RESULTS_v3.json]` Size cm: `[2889.69,2130.93,4868.35]`; local bounds min: `{"x":-1273.8673095703125,"y":-1081.9207763671875,"z":-0.3545195758342743}`; max: `{"x":1615.8203125,"y":1049.0091552734375,"z":4868}`. These are prior import measurements, not a new live measurement.
- Same source: reported pivot-to-bottom-centre `[-170.98,16.46,0.35]`. **Do not transfer this value to a signed contact vector**: the support point, sign, and transform operation were not verified.
- `[documented: native receipts]` LOD0 `44241` triangles, `45927` vertices, UV channels `2`, material slots `4`, collision primitives `1`, Nanite `unchecked`. Import metadata reports LOD count `1`. collision behavior/LOD performance: NOT RUN.
- Missing: exact local bounds verification if accessible in the UI; signed contact/support points, semantic front/up, scale limits, physical size reference, collision behavior, scene performance, local/period fit, and Houdini. Do not fill UNKNOWN using UI size or the asset name.
- Rights `[documented: LICENSE_PROVENANCE.md]`: owner approval for technical qualification of the 32 v3 assets; no extension to distribution/attribution rights or other packages.

| Documented slot | Documented package | Documented class | Dependency state |
|---|---|---|---|
| Material_Building_04_1011 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1011` | Material | File exists; current binding was not rechecked |
| Material_Building_04_1001 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1001` | Material | File exists; current binding was not rechecked |
| Material_Building_04_1031 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1031` | Material | File exists; current binding was not rechecked |
| Material_Building_04_1021 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1021` | Material | File exists; current binding was not rechecked |

Exact texture paths, material-package hashes, and prior evidence for each row: `BANK_ASTRA_001_CANDIDATES.json`.

### H0015

- asset_id / variant_id: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0015_Building_02` (unchanged).
- Unreal object: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0015_Building_02.SM_H0015_Building_02`.
- Current file: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0015_Building_02.uasset`. SHA-256: `106253b92e6b9c4c7a3cbbca9ee6baca337449d8957d3e8cbfef5779096655d2`.
- Role `[inference]`: `residential_over_shops_whole_building`; proposed representation `whole_instance`.
- Proposed zones only: `["mixed_use_parcel_street_frontage"]`; approved allowed_zones: UNKNOWN.
- Observed condition: weathered; blue glazing mottled.
- Material: Textured facade present; blue glazing has conspicuous mottling. Compare close view before approval.
- `[documented: ME/IMPORT_RESULTS_v3.json]` Size cm: `[2034.02,1170.84,2417.33]`; local bounds min: `{"x":-1299.954345703125,"y":-563.1273193359375,"z":0.09817590564489365}`; max: `{"x":734.0643920898438,"y":607.7086181640625,"z":2417.42529296875}`. These are prior import measurements, not a new live measurement.
- Same source: reported pivot-to-bottom-centre `[282.94,-22.29,-0.1]`. **Do not transfer this value to a signed contact vector**: the support point, sign, and transform operation were not verified.
- `[documented: native receipts]` LOD0 `201057` triangles, `211808` vertices, UV channels `2`, material slots `4`, collision primitives `1`, Nanite `unchecked`. Import metadata reports LOD count `1`. collision behavior/LOD performance: NOT RUN.
- Missing: exact local bounds verification if accessible in the UI; signed contact/support points, semantic front/up, scale limits, physical size reference, collision behavior, scene performance, local/period fit, and Houdini. Do not fill UNKNOWN using UI size or the asset name.
- Rights `[documented: LICENSE_PROVENANCE.md]`: owner approval for technical qualification of the 32 v3 assets; no extension to distribution/attribution rights or other packages.

| Documented slot | Documented package | Documented class | Dependency state |
|---|---|---|---|
| Building_02_1003 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Building_02_1003` | Material | File exists; current binding was not rechecked |
| Building_02_1004 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Building_02_1004` | Material | File exists; current binding was not rechecked |
| Building_02_1001 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Building_02_1001` | Material | File exists; current binding was not rechecked |
| Building_02_1002 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Building_02_1002` | Material | File exists; current binding was not rechecked |

Exact texture paths, material-package hashes, and prior evidence for each row: `BANK_ASTRA_001_CANDIDATES.json`.

### H0051

- asset_id / variant_id: `current_Project__Shared__Bank_ME_v3__StreetFurniture__SM_H0051_Garbagebin` (unchanged).
- Unreal object: `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/SM_H0051_Garbagebin.SM_H0051_Garbagebin`.
- Current file: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\StreetFurniture\SM_H0051_Garbagebin.uasset`. SHA-256: `1b1ca536131e7ae3d5616f887b29277ee6a29829d350d6d497b1043b44fc419d`.
- Role `[inference]`: `pedestrian_waste_bin_with_attached_litter`; proposed representation `compound_instance`.
- Proposed zones only: `["pedestrian_service_edge_outside_clear_walkway"]`; approved allowed_zones: UNKNOWN.
- Observed condition: littered; bottles integral.
- Material: Slats/frame/bottles visible; close surface and ground-support QA incomplete. Current material path must distinguish StreetFurniture from same-name Props material.
- `[documented: ME/IMPORT_RESULTS_v3.json]` Size cm: `[29.4,34.43,74.4]`; local bounds min: `{"x":-12.837084770202637,"y":-17.898235321044922,"z":3.5086711136500526e-07}`; max: `{"x":16.559925079345703,"y":16.53656768798828,"z":74.40184783935547}`. These are prior import measurements, not a new live measurement.
- Same source: reported pivot-to-bottom-centre `[-1.86,0.68,-0.0]`. **Do not transfer this value to a signed contact vector**: the support point, sign, and transform operation were not verified.
- `[documented: native receipts]` LOD0 `5180` triangles, `4776` vertices, UV channels `2`, material slots `1`, collision primitives `1`, Nanite `unchecked`. Import metadata reports LOD count `1`. collision behavior/LOD performance: NOT RUN.
- Missing: exact local bounds verification if accessible in the UI; signed contact/support points, semantic front/up, scale limits, physical size reference, collision behavior, scene performance, local/period fit, and Houdini. Do not fill UNKNOWN using UI size or the asset name.
- Rights `[documented: LICENSE_PROVENANCE.md]`: owner approval for technical qualification of the 32 v3 assets; no extension to distribution/attribution rights or other packages.

| Documented slot | Documented package | Documented class | Dependency state |
|---|---|---|---|
| Street Props Pack _003 | `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/Street_Props_Pack__003` | Material | File exists; current binding was not rechecked |

Exact texture paths, material-package hashes, and prior evidence for each row: `BANK_ASTRA_001_CANDIDATES.json`.

### H0958

- asset_id / variant_id: `current_Project__Shared__Bank_ME_v3__Vegetation__SM_H0958_CoconutPalm` (unchanged).
- Unreal object: `/Game/Project/Shared/Bank_ME_v3/Vegetation/SM_H0958_CoconutPalm.SM_H0958_CoconutPalm`.
- Current file: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Vegetation\SM_H0958_CoconutPalm.uasset`. SHA-256: `e9575502d9e03f75537e2edcd02d22f444920aee7aa4ab1e48765752168bc3e6`.
- Role `[inference]`: `palm_candidate_species_unverified`; proposed representation `whole_instance`.
- Proposed zones only: `["planting_zone_after_species_and_crown_clearance_validation"]`; approved allowed_zones: UNKNOWN.
- Observed condition: opaque_foliage_card_defect; biological condition unknown.
- Material: HOLD: prior visible opaque-card defect. Imported alpha and exact Base Color/Normal dependencies were measured in this run; Original_Submesh_1 remains Opaque/Default Lit, Two Sided off, with alpha disconnected [measured: LIVE observations 21–27]. No repair, UV-mask surface proof or new mesh-slot binding check occurred.
- `[documented: ME/IMPORT_RESULTS_v3.json]` Size cm: `[605.24,612.81,870.63]`; local bounds min: `{"x":-168.54640197753906,"y":-367.2211608886719,"z":-4.231946604704717e-06}`; max: `{"x":436.6885986328125,"y":245.5916290283203,"z":870.6278686523438}`. These are prior import measurements, not a new live measurement.
- Same source: reported pivot-to-bottom-centre `[-134.07,60.81,0.0]`. **Do not transfer this value to a signed contact vector**: the support point, sign, and transform operation were not verified.
- `[documented: native receipts]` LOD0 `4160` triangles, `3326` vertices, UV channels `2`, material slots `2`, collision primitives `1`, Nanite `False`. Import metadata reports LOD count `1`. collision behavior/LOD performance: NOT RUN.
- Missing: exact local bounds verification if accessible in the UI; signed contact/support points, semantic front/up, scale limits, physical size reference, collision behavior, scene performance, local/period fit, and Houdini. Do not fill UNKNOWN using UI size or the asset name.
- Rights `[documented: LICENSE_PROVENANCE.md]`: owner approval for technical qualification of the 32 v3 assets; no extension to distribution/attribution rights or other packages.

| Documented slot | Documented package | Documented class | Dependency state |
|---|---|---|---|
| Original_Submesh_0 | `/Game/Project/Shared/Bank_ME_v3/Vegetation/Original_Submesh_0` | Material | File exists; current binding was not rechecked |
| Original_Submesh_1 | `/Game/Project/Shared/Bank_ME_v3/Vegetation/Original_Submesh_1` | Material | File exists; current binding was not rechecked |

Exact texture paths, material-package hashes, and prior evidence for each row: `BANK_ASTRA_001_CANDIDATES.json`.

### H0907

- asset_id / variant_id: `current_Project__Shared__Bank_ME_v3__Buildings__SM_H0907_Arab_x3_fbx` (unchanged).
- Unreal object: `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0907_Arab_x3_fbx.SM_H0907_Arab_x3_fbx`.
- Current file: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\Bank_ME_v3\Buildings\SM_H0907_Arab_x3_fbx.uasset`. SHA-256: `3c1726f412f92ac187a66e0c040c70ece42423527d1060c4d6ac5c57aff289bc`.
- Role `[inference]`: `domed_landmark_pavilion`; proposed representation `whole_instance`.
- Proposed zones only: `["exact_local_landmark_match_only"]`; approved allowed_zones: UNKNOWN.
- Observed condition: weathered; dome tone boundaries.
- Material: Textured domed structure present; visible tone/patch boundaries on dome need intent/source review. Not typical residential architecture.
- `[documented: ME/IMPORT_RESULTS_v3.json]` Size cm: `[1369.04,1368.74,1560.66]`; local bounds min: `{"x":-680.353271484375,"y":-700.4720458984375,"z":0.6762058734893799}`; max: `{"x":688.6864013671875,"y":668.2713623046875,"z":1561.33740234375}`. These are prior import measurements, not a new live measurement.
- Same source: reported pivot-to-bottom-centre `[-4.17,16.1,-0.68]`. **Do not transfer this value to a signed contact vector**: the support point, sign, and transform operation were not verified.
- `[documented: native receipts]` LOD0 `3302` triangles, `4835` vertices, UV channels `2`, material slots `1`, collision primitives `1`, Nanite `unchecked`. Import metadata reports LOD count `1`. collision behavior/LOD performance: NOT RUN.
- Missing: exact local bounds verification if accessible in the UI; signed contact/support points, semantic front/up, scale limits, physical size reference, collision behavior, scene performance, local/period fit, and Houdini. Do not fill UNKNOWN using UI size or the asset name.
- Rights `[documented: LICENSE_PROVENANCE.md]`: owner approval for technical qualification of the 32 v3 assets; no extension to distribution/attribution rights or other packages.

| Documented slot | Documented package | Documented class | Dependency state |
|---|---|---|---|
| Arab_X3 | `/Game/Project/Shared/Bank_ME_v3/Buildings/Arab_X3` | Material | File exists; current binding was not rechecked |

Exact texture paths, material-package hashes, and prior evidence for each row: `BANK_ASTRA_001_CANDIDATES.json`.

## Proposed UI sequence, only after an explicit lease

The window is limited to 45 minutes from lease start, including closing and recording release. Do not open a working HDA/map. No scene placement, asset change, Apply/Save/Compile/Import, cook/bake, repair, Houdini, or Linear.

1. **W0** — The bank manager coordinates with integration and issues a written lease naming BANK-ASTRA-001, owner, scope, existing PID if relevant, map, start/end times, and release method. Before input, recheck owners/operators and processes, dirty state, and Content baseline. Stop if anything conflicts. Record ownership only in the bank folder under the manager’s procedure; do not change measurement records.
2. **W1** — Only with a valid lease, open the project on `/Engine/Maps/Templates/Template_Default` through PowerShell/Windows; record the actual PID rather than inventing one. Confirm the map and All Saved; do not select Resume/Cook/Session. Use an already open editor only under an explicit handover, without guessing ownership.
3. **A1 H0051, target about 7 minutes** — `Ctrl+P`, search the exact name and `Path=/Game/Project/Shared/Bank_ME_v3/StreetFurniture/`. Open only the exact result. Click the viewport and then `F`; capture full and close views of the base/frame/bottles. Use Perspective and Front/Back/Top through the camera menu and capture the axis gizmo; do not equate the Front camera with semantic front. Read the collision view only if available; do not Generate/Add/Remove. Read slot/path through Browse or by opening the material only; confirm StreetFurniture, not Props.
4. **A2 H0013, target about 10 minutes** — Use the exact path above. Capture full facade, opposite, and Top/base views; identify any face, threshold, or paving that expands the footprint. Read the four slots, geometry data, and Nanite/LOD count/collision complexity as shown. Search Details for bounds in read-only mode: extension fields are not actual bounds. If the UI does not provide numeric local min/max or support points, record UNKNOWN and an image of the missing capability. Do not derive signed contact from an image or lower bound.
5. **A3 H0015, target about 9 minutes** — Use the exact path above. Capture the shop/balcony frontage and close glazing; compare sides, roof, and support. Identify all four material paths exactly and read LOD/collision. Do not switch to another material for comparison. H0015 remains a proposed alternative; do not select it instead of H0013/H0907 in the contract.
6. **A4 H0958 dependency, target about 9 minutes** — No need to repeat the mesh preview that already shows cards. Open `/Game/Project/Shared/Bank_ME_v3/Vegetation/Original_Submesh_1` for reading; identify the texture sample’s actual object path. Open imported texture `coconut_palm_leaf_3f6407d492f8_albedo_cdcdc62b95fb29` and read Texture2D class, source filename if shown, dimensions, compression/alpha discard, and view its A channel through viewer display only. Do not change any asset setting checkbox or connect nodes. Mark `[not run]` if the alpha display is inaccessible. The source PNG has already been measured; source shader and mask correspondence remain missing.
7. **W2, about 10 minutes remaining** — Restore display toggles as needed, confirm no dirty assets, and close without saving according to UI state. If any dirty state was not caused by expected viewing, stop and document it without automatic save/discard. Record process exit and ownership release, inventory/hash preservation, and a receipt for each section. Do not open H0907 or more families without a task extension from the coordinator.

The times above are targets, not measured execution times. If time expires, close/release and report partial results with exactly what was not run.

## Measurement closure conditions and real limits

- Loading/material: exact class/path with image, full material slots/dependencies, and two useful views of the problem. A clean close-up is not scene acceptance.
- Geometry: documented source bounds exist; their frame and support points must be verified before catalog-to-HDA contact. Numeric bounds, contact, and placement transforms may exceed what an asset preview can prove without placement. In that case report UNKNOWN and propose a separate measurement gate, not an unauthorized script or scene.
- Generation: later contact measurement must define whether the contact vector is a local-space point or a translation correction and specify the rotation/scale operation. Compare support points against ground as the contract requires; the actual measurement method has not yet been chosen.
- H0958: source-alpha PASS is not surface PASS. Actual imported alpha/binding, source shader, and ultimately an authorized repair with variant identity and source link are required. This task does not authorize repair.
- Tier 1 remains blocked by the DRAFT contract and route gates; in addition, no approved, sound vegetation asset is available within v3. Do not run BG1/Tier 1 or invent a qualified subset.

## Ownership and sequence

At preparation time this packet awaited an explicit lease; historical OWNER=NONE was not authorization. The manager subsequently granted the bounded window recorded above. Preflight, native inspection and no-save exit are now recorded in this folder. The manager released the lease to OWNER=NONE at 02:45:08.9357886 +03. The operator did not write the owner ledger or canonical catalog; any further editor action needs a new assignment and lease.
