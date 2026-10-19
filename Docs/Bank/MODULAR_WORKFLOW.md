# Adding or adapting a building kit

Documentation baseline: **2026-10-18**. This guide preserves the reusable method; live authoring follows the user's current scope, ownership and exact saved-source bindings. Native publication and map validation require their receiving operators.
Start with [Bank README](README.md), [rules and ownership](RULES.md), [current files/state](FILES_AND_STATE.md) and [indexing](INDEXING.md).
Resolve the actual area/HDA/registry before integration using [Connection](CONNECTION.md); a dated handoff is an example, not the current baseline.

## Choose the construction route

Record the full source path and identity before choosing a route. Similar names such as external H0017 “Building 05” and ModularBuildingSet “Building05A” do not identify the same source.

| Source capability | What can be reused | Required kit-specific work |
|---|---|---|
| Whole native building mesh | Existing native-reference placement and whole-building selector | Measure anchor, facing, dimensions, materials, intended use and geographic fit. |
| Fixed reconstruction from parts | Restore the recorded part transforms and matching neighbors | Verify complete reconstruction and closure; cutting a building into cells does not permit growth. |
| Source-derived facade/floor family | Existing `facade_floor_grid` planner and source converter | Choose measured repeat bands, cuts, pitches and supported counts; preserve fixed ends/roof/details. |
| Native wall/door construction kit | Existing measured wall/door/closure techniques | Define roles, compatible interfaces, openings and fit rules. The admitted Courtyard consumer is specific to that kit. |
| Fixed component group | Preserve original component transforms, material overrides, scales and reflections | Capture effective source state and complete compound bounds; no inferred repeated floors or scaling to fit. |
| Blueprint, spline or dynamic assembly | Official native asset references and applicable retained consumers | Capture effective components/properties, attachments, spline settings and motion; static mesh export does not establish equivalence. |

Do not add a catalog row and assume that an unsupported construction route will execute.
An existing capability can often consume new validated data; a new capability needs a bounded consumer implementation in the retained HDA/runtime.
There is no demonstrated generic adapter that automatically converts every native kit into a complete procedural building.

## Asset contracts required by the retained generator

The following requirements map to existing runtime fields and manifests. The adaptation record below is documentation, not an extra runtime format. Do not manufacture a new canonical identity for a modular child or replace a source restriction with an enabled flag.

| Asset route | Required data and physical meaning | Assembly / fit / failure boundary |
| --- | --- | --- |
| **Complete model**, including a whole building or supported prop | Current table `Name`, `AssetId`, `ObjectPath`, `AssetRevision`; `BoundsMin*Cm` / `BoundsMax*Cm`; physically reviewed `AnchorZCm` and `ForwardAxis` or verified free yaw; effective ordered native materials; role, `RequestRole`, `PlacementRule`, style/weight, scopes and holds. Record full size = max minus min and distinguish vertex bounds from render bounds. | Whole-building selector or supported prop placement must already exist. Preserve footprint/proportions and supported ground/road alignment. No automatic subdivision or arbitrary height stretching follows from a complete mesh. Missing support semantics stays ROW-G01/HDA04; unsupported hosted placement stays a consumer gap. |
| **Fixed reconstruction** | Registry entry plus hash-bound source bindings, `NATIVE_FAMILY.json`, authorization and source qualification. Each part needs exact native identity/material slots, source-to-native basis, source bounds, authored local transform/restoration translation and neighbor relationship. Full reconstruction must agree with the exact source revision. | Reassemble only permitted recorded arrangements/counts. Doors, roof, floors, closure and detail must remain present. Source Z tiers do not prove architectural storeys. Growth requires independently measured repeat interfaces and explicit supported capability; do not infer it from cut cells. |
| **Variable source-derived family** | `ASSEMBLY.json`: exact `family_id`, `modules[].role`, `floor_role`, `bounds_m`, `dimensions_m`, `assembly_translation_m`, `pivot_policy`, repeat flags, compatible families, source/native material slots, `native.path`, geometry paths/hashes, `interfaces` with axis/bands/pitch and declared capability counts. Source provenance and validation/native readbacks remain linked. | `procedural_family_plan` must support the declared horizontal/floor counts and height/use/fit policy. Test Start→Repeat, Repeat→Repeat, Repeat→End, corners, openings and roof continuity, including UV/material phase. Current ordinary enumeration is 1..3 per axis; manifest claims cannot enlarge it. Native scale is retained; fixed roof/details move with their declared roles. |
| **Native modular kit** | Exact `kit_id` and `KIT.json`: measured construction module identities, roles, local axes, anchor/socket contact frames, widths/heights/thickness, effective slots, validated materials, allowed adjacent roles, corners, door/opening rules, style/palette and allowed scaling/height/footprint envelope. | Current dispatcher accepts the Courtyard kit only. Its declared bounds are height 2.65..48 m, storey 2.65..4.4 m, bay scale 0.5..1.5, wall vertical scale 0.65..1.1, door scale (1,1,1), compatible simple hole-free polygons; corners/floor/roof slabs are generated by that consumer. These are that kit's limits, not defaults for a new pack. A new kit needs measured dispatch/closure rules before registration can become useful. |

For a connection, record the mating origin/plane, normal and tangent in the declared local basis, allowable neighbor role, gap/overlap tolerance and allowed scale/rotation. Use the route's existing interfaces/recipe fields; arbitrary sockets are not read by today's family planner. If a required relationship cannot be expressed, deliver the missing-consumer requirement rather than an invented socket field. The measured roles and join tolerances belong to each kit revision.

Native centimetres remain explicit in catalog scalar fields. Source-family Blender metres `(x,y,z)` map to Houdini `(x,z,-y)`, then official Engine to Unreal `(100x,-100y,100z)`. Do not apply that source transform again to an already-native row or assume numeric `*Cm` attributes are converted geometric positions. Preserve negative scale/reflection where the supported fixed-component contract requires it and inspect winding/culling in actual output.

### Native references or Houdini geometry

Use **native references** when Houdini only selects, positions or assembles existing Unreal models. The native mesh and original native material graphs stay where they are; Houdini needs measured contracts and paths, not duplicate imported meshes. The retained output uses point string `unreal_instance`, point `P`, float4 quaternion `orient` and float3 `scale`. Assembly material overrides are point `unreal_material0`, `unreal_material1`, etc., with explicit slot 0; detail `unreal_split_attr` names point `assembly_material_signature`. Shujaiya's current revision also sets point integer `unreal_force_instancer=1` to preserve singleton replacement. Verify the actual HAPI owners/storage/tuple sizes when the receiving output operator runs; source text alone is not HAPI evidence.

Use **real Houdini geometry** when the requested operation actually inspects/deforms/cuts source surfaces, validates geometric interfaces in Houdini, materializes modules, or delivers generated geometry to a downstream consumer. Keep the existing source-family NPZ/FBX/BGEO artifacts and their hashes; these are existing route dependencies even when ordinary output uses native references. Generated geometry additionally needs correct normals/type semantics, winding, UVs and material assignments. An Unreal reference is not a locally deformable mesh, and a proxy box is not a replacement for the source.

**HR01 repaired, 18 October:** both active batch builders now create vertex `N` with `transform_as_normal=True`. All 253 affected modules have preserved-source corrected derivatives, referenced by 30 revised manifests and all five installed HDA/profile bindings. [Fresh verification](../../Staging/HoudiniBankFixes_2026-10-18/NORMAL_VERIFICATION.json) reopened every corrected BGEO and exercised the actual `materialize_procedural_record` helper with asymmetric geometry, a 37-degree rotation and translation; positions and normals match the expected transforms. Original values, topology, UVs and material assignments are preserved. The helper remains uncalled by ordinary generation; this repair does not claim native scene shading acceptance. See the [complete dependency receipt](../../Staging/HoudiniBankFixes_2026-10-18/NORMAL_REPAIR.json).

## Common conventions and kit measurements

The source-family conversion route uses these established conventions. A different source/native recipe must declare and verify its own basis rather than inherit an unsuitable pivot or facing rule.

Measure each exact native revision's physical support/contact anchor and functional facing or verified free-yaw behavior. Minimum bounds Z is not automatically the terrain contact plane; +X and centered pivots are not universal requirements. Preserve authored offsets. If the consumer cannot represent the required support/orientation, record the missing capability instead of marking invented metadata valid.

| Contract | Reusable rule | What must be measured or declared |
|---|---|---|
| Units and basis | Source-family Blender metres `(x,y,z)` become Houdini `(x,z,-y)` and Unreal centimetres `(100x,-100y,100z)`. | Verify asymmetric geometry and actual native bounds. Apply the metre/centimetre conversion once. |
| FBX export | Existing family exports use `-Y` forward and `Z` up. | Verify the source export/import contract; front direction is not inferred from a symmetric box. |
| Pivots | Keep the declared module anchor and restoration translation together. | Cell-minimum pivots, ground-centre pivots and row-start pivots serve different consumers. Do not recenter to the lowest bound. |
| Scale | Source-derived family placements use unit scale; fixed source groups preserve authored component scale/reflection. | Courtyard has separately bounded wall scaling. Neither rule authorizes arbitrary scale-to-fit. |
| Roles | Use actual wall/floor/roof/start/repeat/end or compound roles. | A geometric Z subdivision is not automatically an architectural storey; an apron is not a repeated facade. |
| Geometry and normals | Preserve originals and meaningful derivative detail; retain explicit before/after changes. | Identify true degenerate/import-unstable triangles, openings, winding and native shading behavior. |
| UVs | Preserve required source render UVs and test new joins. | The retained converter/importer supports one active render UV channel; extra source-channel dependencies need explicit support. |
| Materials | Bind by unambiguous source material identity and measured effective native slots. | Native import may collapse duplicate slots. Do not reuse obsolete numeric slot arrays or substitute a similar material name. |
| Texture interpretation | BaseColor normally uses sRGB; data/ORM channels use linear interpretation. | Follow each source's actual channel packing, opacity and normal convention. Do not flip every normal green channel blindly. |
| Dependencies | Reuse exact compatible native dependencies and retain source hashes. | Missing textures, inherited overrides, static switches and Blueprint dependencies remain explicit gaps. |

FBX does not reconstruct a complete custom material graph automatically.
Preserve source opacity, texture channels, UV transforms and normal interpretation; opaque site-delivery rules are not a blanket rule for all bank materials.
Preserve slot names/order where the contract requires them, including matching detailed/lowest-LOD pairs.
Collision, lightmap UVs, LODs, culling and HLOD behavior require an explicit consumer contract; a geometry-preserving import does not supply them automatically.

## Keep one adaptation record per kit and revision

Use one owned record in that kit's existing staging/delivery scope and link its evidence instead of repeating instructions across chats.
The outline below is a documentation template, **not a new runtime schema or a file consumed by the current HDA**.
Map actual runtime fields to the existing source-family, kit, catalog and profile contracts.

```text
Kit/revision and full source identity:
Route: whole / fixed reconstruction / source family / native wall kit / component / dynamic
Source paths, hashes, original objects and dependency inventory:
Current base: area profile, native HDA import source, registry, catalog and hashes:
Owned source/native destinations and responsible operators:
Units/basis, facing, pivot/anchor and transform policy:
Roles, dimensions, cuts, pitches, interfaces and supported variation counts:
Materials: source identities, effective slots, UV channels, texture interpretation:
Fit/use/height/terrain rules; unsupported cases and preserved holds:
Required consumer: already supported / exact missing implementation:
Evidence: source, seams, variants, native readback, Houdini, integration, city lifecycle:
Status, unresolved work, immutable delivery references and next owner:
```

Record kit-specific cut choices as configuration. Do not promote a successful H0017, H0019 or H0909 cut pitch into a global default.
Keep thresholds with their measurement method and source scope; the historical permitted `0.4 m` correction is not permission to remodel every new source by that amount.

## Follow the same phase sequence

Use this seven-stage sequence for each exact revision. Keep its record and evidence in the existing asset/family delivery folder. Update the existing queue by identity; the derived delivery CSV is not a second issue tracker.

| Stage / existing tool | Input | Retained output / success condition | On failure / next owner |
| --- | --- | --- | --- |
| **1. Intake** — current typed readback, existing `FULL_INDEX` provenance, saved-package scan only if discovery is needed | Source/native identity and hash, dependencies, intended capability/area, current holds | One matched identity and route; source/provenance/dependency record. Search before registering. Begin with the [current delivery subset](../../Staging/HoudiniBankConsolidation_2026-10-18/DELIVERY_QUEUE.csv). | Missing dependency, rights restriction or unsupported route stays explicit in that item's existing queue. No duplicate import, eligibility promotion or full-bank rescan. Bank preparation owner resolves. |
| **2. Measure** — existing `PREPARED_BANK.json`, native mesh readbacks, Blender source inspection; `inspect_delivery_items.py` only by its native owner in a fresh scoped session | Exact revision plus prior measurement method/evidence | Full bounds/units, functional contact/pivot and facing/free yaw, material-slot/UV inventory; modular pitch/roles/interface/height measurements. Reuse matching measurements; success needs physical meaning as well as finite numbers. | Hash mismatch invalidates the old measurement for that revision. Missing semantics remains ROW-G01/HDA04, without declaring a mesh defect. Native inspection is a receiving-owner dependency in this scope. |
| **3. Adapt** — existing `author_families.py` + owned config for source families; existing fixed/native kit recipe for supported routes | Measurements and allowed capability | Minimal owned derivatives only where needed; declared anchors/roles/materials/joins/counts, preserved originals. A complete native model needing no geometry change passes through without copying it. | Wrong seams, unsupported socket/roof/floor grammar or missing materials returns to the same kit's authoring record. Do not broaden counts/scale/holds or repurpose the Courtyard consumer. |
| **4. Check** — converter `VARIANT_VALIDATION.json` / `READBACK.json`, existing native importer/readback, retained planner's focused assertions | Actual adapted modules/recipes and allowed/rejected variants | Reconstruction and combined variations, openings/roof/corner/texture seams, asymmetric rotated transforms and expected rejection cases agree. Native geometry/material checks stay separate from source checks. | Keep failed part/variant and exact cause in the kit queue. Confirmed defects get a minimal root repair plus rebuilt dependent artifacts. Missing runtime/pixel proof is an open gate, not PASS. |
| **5. Register** — current row transaction for existing identities; immutable family registry/kit references using existing builders as bounded examples | Validated revision, exact native bindings/materials, unchanged holds, current before hashes | Existing identity reused; final manifest frozen before downstream hashes. Registry and permitted profile reference updates are reviewed field deltas. Native bank publication is handed to its owner. | Writer row-count/name guards, unknown current authoring source or unsupported new-identity insertion stops publication only. Preserve packet/old baseline; [Indexing](INDEXING.md#add-a-model-or-adapted-family) names the missing publisher. No direct table edit or weakened guard. |
| **6. Connect to Houdini** — retained HDA PythonModule, `procedural_family_plan` / `assembly_layout`; current binding checker | Final catalog/registry/manifests, selected area's exact HDA source and contract | Existing dispatch resolves correct identity automatically, respects use/area/fit and fallback; required geometry hashes match. HDA changes require source review and coherent dependent references, then native import by its owner. | Registration without dispatch remains unconnected. Reject hash/area/fit failures; preserve the declared source-shell fallback. Never substitute the GUI candidate, force a family, or overwrite whole profiles from old builders. |
| **7. Verify** — no-evaluation Houdini metadata first; receiving owner's existing official Engine workflow and `verify_saved.py` pattern | Owned intended HIP/HDA and exact revisions, then applicable authorized native output | Check real emitted attributes/parts, selected identities, nonzero-yaw transforms, material groups, joins/contact. For saved environment delivery: native output → visible review → named save → fresh reopen → ordinary replacement without duplicates → save/reopen, with explicit acceptance. | A successful call/Cook, registration, file check or native slot resolution closes only that gate. Leave exact unperformed checks and their receiving owner in the handoff. Do not run Unreal tools or modify maps to close them during Houdini-bank-only work. |

The converter/importer/build scripts are frozen batch implementations with fixed paths and historical guards. Read their inputs/callers before a bounded adaptation; no unchanged historical command is a general intake command. Preflight live Houdini PID/start/listener, HIP, dirty state and definition library before authoring. Owning a node does not authorize saving another operator's HIP or changing its loaded definition.

The selected ROW-G01/HDA04 delivery's 39 missing asset-local support/facing qualifications are now closed by [individual geometry-backed receipts](../../Staging/HoudiniBankFixes_2026-10-18/CONTACT_QUALIFICATIONS.json). The [appended 50-item evidence](../../Staging/HoudiniBankFixes_2026-10-18/DELIVERY_ITEMS.json) preserves the 11 prior reviews and the [original dated JSON](../../Staging/BankGapValidation_2026-10-18/DELIVERY_ITEMS.json). All 50 retain a separate material/scene contact and appearance gate. Future revisions require fresh applicable evidence; do not extend these qualifications to unreviewed or excluded identities. Selected assembly families/Courtyard retain their existing family evidence and HR03/MOD-04 output gates.

For fixed reconstruction, validate the exact recorded arrangement before considering any extension.
For a variable family, exercise every growth direction it declares, combined variation where supported, rotated placement and rejection cases.
The existing planner enumerates small repeat counts `1..3`; increasing a manifest limit alone does not change that enumeration.
The source-family planner retains native scale, full-pad containment, minimum coverage and measured-height/terrain checks; record the actual applicable contract rather than relaxing it to fit a source.

Check Start→Repeat, new Repeat→Repeat and Repeat→End interfaces, plus roof/corner/opening continuity.
Geometry agreement alone is insufficient: the [eight-family seam audit](../../Staging/ModularConstruction_2026-10-05/SourceAudit/EXTENSION_SEAM_AUDIT.md) found new texture-phase failures despite close geometric profiles.
Do not certify all instances from one preview angle or a few contact samples.

## Reuse the existing implementation

The external source root is `C:/Users/USER/Documents/Pipeline Environment/ModelBank/Modular_2026-10-04/`.
Follow actual registry references when locating a family; first-batch and Additional20 manifests remain in different directories.

| Existing implementation | Useful retained behavior | Replay boundary |
|---|---|---|
| [ProceduralFamilies converter][converter] and `CONVERSION_CONFIG.json` | Source partitioning, anchors, module roles, FBX/geometry export and manifest creation. | Read arguments and dependencies; use new owned derivatives/configuration, preserving registered files. |
| [Additional20 continuation][additional-converter] and its configuration | Fixed-axis capability, source detail preservation and bounded interface repairs. | This implementation rewrites predecessor source text; it is a proven batch example, not a stable generic public API. |
| [Additional20 native importer][native-import] and material/readback helpers | Legacy mesh-only FBX, source material mapping, geometry-preserving settings, native bounds/triangle/UV checks and named saves. | Fixed roots, native destination revision and historical ownership checks require current adaptation by the owner. |
| [Source-family HDA extension][family-extension] | Generic registered `facade_floor_grid` loading and native-scale family planning. | Declare actual supported capabilities; normal automatic discovery must be exercised without a forced family ID. |
| [Additional20 HDA builder][hda-builder] and promotion example | Geometry materialization, immutable registry construction and field-level profile/HDA binding. | Pins old HDA/profile/batch state, including a removed Rimal profile. Never run unchanged against current production. |
| [Courtyard kit registration](../../Staging/ModularCourtyardBank_2026-10-06/kit_extension.py) | Existing native kit identity/material checks and retained assembly connection. | Selects the explicit Courtyard kit; another pack needs its own measured recipe/consumer support. |
| [Current menu adapter](../../Content/Python/geocity_editor_action.py) and [official Engine workflow](../../Content/Python/geocity_bank_workflow.py) | Current-area resolution, native input binding, ordinary output/Bake and named persistence. | Use only in the applicable authorized operator scope; documentation work does not execute this sequence. |

For native family imports, the proven geometry-preservation example uses mesh-only legacy FBX, imported normals, scene-unit conversion, scale `1`, no automatic material/texture import, no automatic collision/lightmap generation, no automatic triangle removal, and full-precision UVs.
The example verifies triangle counts, bounds and bidirectional native XYZ/UV readback; copy its measurement semantics as well as its settings.
A new source with different UV, material, collision or LOD needs may require a bounded supported extension.
Diagnose Blender preview interpretation separately from native material faults; the retained packed-PNG alpha repair was a preview issue for particular sources, not a global opacity fix.

The [293-line procedural handoff][long-guide] contains the detailed method and case studies.
Its header supersedes its older Courtyard-retirement instructions, and its body still names older HDA/table/profile revisions.
Use its conversion lessons; resolve the current source and permissions again through [Connection](CONNECTION.md) and [Rules](RULES.md).
The [native Courtyard README][courtyard-guide] explains that kit's eight-piece construction subset; it does not admit all 104 cataloged meshes into assembly.
The [Building05A handoff](../../Staging/ModularKitIntake_2026-10-07/ModularBuildingSet/Building05A/INTEGRATION_HANDOFF.txt) documents a fixed component group, not a parameterized floor kit.

## Report what each layer proves

Retain separate results for source adaptation, source variants/seams, native asset saves/readback, Houdini selection/output, current integration and original-area lifecycle.
Record actual selected family/model/part IDs and inspectable output locations; all valid families need not appear in one ordinary run.
Imported assets, enabled rows, a green cook, source previews and registration counts do not establish original-map visual acceptance.
Existing whole-parent catalog state and modular-family admission are separate: the inherited baseline does not universally require a whole-parent row, while newer admission branches can require one.
Do not fabricate a parent alias or clear a hold to satisfy the wrong route's contract; see [parent reconciliation](../../Staging/ModularBankAlignment_2026-10-07/ParentReconciliation_v010/INTEGRATION_HANDOFF.txt).

Necessary new design work is choosing architecture, cuts, compatible roles, interfaces and actual support/appearance for this source.
Avoidable repeat work is rediscovering conventions, remeasuring already retained evidence, locating the live baseline and manually reconciling duplicated configuration.
Those remaining automation gaps are explicit; this documentation change does not modify converters, consumers or runtime schemas.

[converter]: <C:/Users/USER/Documents/Pipeline Environment/ModelBank/Modular_2026-10-04/ProceduralFamilies/author_families.py>
[additional-converter]: <C:/Users/USER/Documents/Pipeline Environment/ModelBank/Modular_2026-10-04/ProceduralFamilies_Additional20/author_families.py>
[native-import]: <C:/Users/USER/Documents/Pipeline Environment/ModelBank/Modular_2026-10-04/ProceduralFamilies_Additional20/import_native.py>
[family-extension]: <C:/Users/USER/Documents/Pipeline Environment/ModelBank/Modular_2026-10-04/ProceduralFamilies/houdini_family_extension.py>
[hda-builder]: <C:/Users/USER/Documents/Pipeline Environment/ModelBank/Modular_2026-10-04/ProceduralFamilies_Additional20/build_houdini_bank.py>
[long-guide]: <C:/Users/USER/Documents/Pipeline Environment/ModelBank/Modular_2026-10-04/ProceduralFamilies_Additional20/PROCEDURAL_BUILDING_HANDOFF.txt>
[courtyard-guide]: <C:/Users/USER/Documents/Pipeline Environment/ModelBank/NativeKits/ModularCourtyard_2026-10-06/README.txt>
