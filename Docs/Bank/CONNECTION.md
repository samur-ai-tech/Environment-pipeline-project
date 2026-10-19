# Connecting the bank through Houdini to Unreal

Documentation baseline: **2026-10-18**. This guide records the retained connection and receiving-owner verification. Current Houdini-bank consolidation does not authorize Unreal tool changes or map authoring.
See [Bank README](README.md), [rules](RULES.md), [current files/state](FILES_AND_STATE.md), [indexing](INDEXING.md) and [modular workflow](MODULAR_WORKFLOW.md).

## How it works

The bank supplies native models/materials and catalog/assembly contracts.
Houdini reads the geographic source and those contracts, chooses compatible models or assembles measured parts, and emits native object paths with transforms/material instructions.
The official Houdini Engine plugin resolves `unreal_instance` references to the existing Unreal assets.
Ordinary native-reference outputs do not require full native mesh materialization inside Houdini. Keep geometry files where the selected source-family route requires them.
The retained Unreal adapter manages ordinary output, scoped replacement Bake and exact dependency/map saves.
Bank work therefore includes connection contracts, not only folder organization; area generation, terrain/roads and visual acceptance remain separately owned operations.

The exact stored branch is `bank_catalog` → `catalog_geometry_input_0` → `disabled_bank_catalog_guard` → `nonbuilding_catalog_selector` → `normal_building_assembly_points` → `modular_wall_points` → `output_bank_instances`. The normal assembly stage also receives geographic pads and corrected terrain; polygon building/surface branches are separate. The guard's historical name does not mean it can be skipped. See the [input catalog](FILES_AND_STATE.md#houdini-input-catalog) and [per-route contracts](MODULAR_WORKFLOW.md#asset-contracts-required-by-the-retained-generator).

The [18 October SourceImplementation result](../../Staging/SourceImplementation_2026-10-18/RESULT.md) supplies the current no-evaluation inspection rules, correct connection indices, bounds/sampling limits and version distinctions. Its fixture/registration results are not scene or bank qualification. Do not restart another owner's connection to obtain a newer schema; use the documented template-only fallback if required.

## Resolve the live baseline before every change

1. Identify the actual intended map and its one matching persistent `Staging/ModelBank/*/AREA_PROFILE.json`.
   The [menu adapter](../../Content/Python/geocity_editor_action.py) resolves profiles by their `map` field; a historical receipt is not an active profile.
2. Read the profile's `source`, `hda`, `table`, catalog digest, output folders, materials and `building_assembly_contract`.
   Follow `building_assembly_contract.source_family_registry_ref` and verify its exact file hash.
3. Resolve the source `.hdalc` from the intended native HDA's actual import metadata and retained receipts.
   A familiar native asset name does not identify the current source revision. A root `.hdalc` or newer candidate filename alone is insufficient.
4. Follow registry family/kit references to the actual manifests, native object paths, geometry files and frozen evidence.
   Determine whether the requested change uses an already supported capability or requires a new consumer.
   Identify definitions by exact path and revision/hash, not family ID alone. Check the target area's profile, canonical policy and family/kit authorization independently of registration, then check geometric fit. Record the permitted source-shell fallback for this target; do not impose zero fallback globally. See the dated [coverage matrix](FILES_AND_STATE.md#current-evidence-and-open-work).
5. Reconcile the current native table, authoring catalog/projection and profile digest through the bank owner's existing transaction; preserve identities, holds and other consumers.
   Resolve current ownership and writable paths through [Rules](RULES.md) before any later application.

There is one profile per named area, not one globally authoritative profile for every area.
Rimal/Iran historical run receipts do not recreate missing current maps/profiles; a retained area-scope DataTable alone does not activate an area.
Use [Files and state](FILES_AND_STATE.md) for the complete current path map and dated output evidence.

The retained workflow explicitly binds current AnyArea, release/digest and contracts. All five inspected standalone HDA defaults still name v4; dragging an untouched HDA is not the configured workflow. Standalone support is separately requested work. Selection also has separate canonical, style, fixed-family and procedural seed streams, including procedural literal `1337`; do not promise that the exposed HDA seed controls every choice.

## Verified shared Shujaiya example

This is a resolution example from the documentation audit, not a permanent pin for all future operations.

| Item | Exact current reference at the audit |
|---|---|
| Area contract | [Shujaiya AREA_PROFILE.json](../../Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json) |
| Native HDA object | `/Game/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank` |
| Native HDA package | [GeoCity_city_v015_PermanentBank.uasset](../../Content/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank.uasset) |
| Actual imported source | [GeoCity_city_v015_PermanentBank_StableBankInstancers_v001.hdalc][shared-source] |
| Shared native table | [DT_EnvironmentBank_AnyArea.uasset](../../Content/Project/Shared/ModelBank/DT_EnvironmentBank_AnyArea.uasset); checked row state is maintained in [Files and bank state](FILES_AND_STATE.md) |
| Family/kit registry | [40a73d1d…bbe98c6.json](../../Staging/HoudiniBankFixes_2026-10-18/Registries/40a73d1d0880c47f23cd25f05f8f1f28578543d5a63aa70b4a16ba538bbe98c6.json) |
| Native adapter | [geocity_bank_workflow.py](../../Content/Python/geocity_bank_workflow.py) |

The imported shared source is under `C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank/revisions/20261018_normal_semantics_v001/20261017_stable_bank_instancers_v001/`.
The [18 October HR01 repair](../../Staging/HoudiniBankFixes_2026-10-18/RESULT.md) updates the registry default and all five profile/import bindings to corrected BGEO derivatives. The PythonModules and ordinary graph behavior are unchanged. Exact native import-source readback and a fresh isolated Houdini process verified the saved definitions; do not read same-type defaults from a GUI session with a different preferred candidate definition and treat them as file-specific evidence.
The [17 October connection repair](../../Staging/ConnectionRepair_2026-10-17/RESULT.md) adds point integer `unreal_force_instancer=1` to keep singleton bank groups instanced. This prevents the installed Bake path from reusing a prior instancer's stale instance array as a plain mesh component. Graph, parameters, selections, transforms, material slots and the runtime source seal remain unchanged; the linked record separates source review, installed import and retained native evidence.
Other areas use their own retained HDA revisions; do not substitute the shared Shujaiya definition for them automatically.
`DT_EnvironmentBank_v4`, `DT_NonBuildingBank_v3` and area-scope tables are distinct retained snapshots, not aliases for AnyArea.
The expanded [shared-bank candidate](../../Staging/HoudiniBankIntegration_2026-10-07/STATUS.json) is a separate staged integration; its existence does not replace the imported native HDA.
Its missing final native/complete-kit qualification is not a new blanket prerequisite for an independently authorized existing-baseline run.

## Prepare an additive delivery and update references in order

Freeze each upstream artifact before recording its downstream hash:

1. Original identity/provenance and owned derivative source; measured roles, pivots, cuts, materials and limits.
2. Source validation and exact native mesh/material bindings with named saved/readback evidence.
3. Route-required Houdini geometry and/or native-reference data, then the final family/kit manifest, including actual native paths and applicable geometry hashes.
4. Consumer/appearance/fit contracts required by that route, then an immutable registry referencing the final manifests.
5. Only the intended profile fields, HDA contract/defaults and runtime changes required to consume those references.
6. Reviewed combined HDA/runtime package and applicable source/binary seal; canonical native import/application by its assigned owner.

The profile supplies the runtime building contract; updating an HDA default alone does not update the area's actual profile.
Changing a hash-bound manifest requires rebuilding affected downstream references. Never edit a content-addressed registry file in place.
Append or update exact reviewed identities and fields; preserve later ground, road, vegetation, catalog and other family changes.
Full candidate HDA/profile/runtime files are review artifacts, not permission to overwrite the current complete source.
Recheck current bytes immediately before application so a stale snapshot cannot replace newer work.

Trace affected builders/callers and their tests/self-checks before editing. Regenerate changed derivatives and refresh only their dependent native bindings, manifest hashes, immutable registries, profile references, HDA source/imported definitions and evidence. A builder repair alone does not update existing BGEO or imported definitions.

Native object references use `/Game/Package/Asset.Asset`; filesystem paths, original-project provenance paths and current native references serve different purposes.
Existing native packages can remain in their vendor folders while the catalog points to them; physical relocation is not required for connection.
Prepared modular children need their actual manifest/consumer identities; do not invent duplicate canonical whole-building rows simply to register parts.
Baseline modular admission and newer parent-row admission differ; [parent reconciliation](../../Staging/ModularBankAlignment_2026-10-07/ParentReconciliation_v010/INTEGRATION_HANDOFF.txt) explains the distinction.

## Know when a consumer change is required

The existing source-family planner can consume validated `facade_floor_grid` families through the retained registry.
The registered native wall-kit implementation is Courtyard-specific; a different wall pack needs measured assembly rules and supported dispatch, not merely a new `KIT.json` or enabled row.
Fixed component groups and Blueprint/spline/dynamic output can require additional source-state, appearance, terrain or runtime contracts.
The [modular guide](MODULAR_WORKFLOW.md) identifies the supported examples and their replay limits.
Historical builders/promoters pin old batches/profiles/HDA revisions; current-base resolution and bounded adaptation remain manual work.
This documentation does not install a generic adapter, change a runtime schema, merge candidates or fill missing qualification with a status flag.

## Verify through the ordinary retained operation

**Receiving-owner boundary:** the sequence below documents the existing native output contract. During Houdini-bank-only work, deliver the exact source/catalog/registry and unresolved checks to the native/map operator; leave this operation unperformed. Existing dated evidence can be reused only for unchanged applicable inputs and its recorded scope. The current 18 October digest has no new area Cook receipt; never rewrite the older receipt to match it.

In the applicable authorized original-map window, use **Tools > GeoCity: Generate / Regenerate Current Area**.
The existing [menu](../../Content/Python/geocity_editor_action.py) and [workflow](../../Content/Python/geocity_bank_workflow.py) handle profile matching, native DataTable input binding, parameters, official Engine execution and scoped lifecycle checks.
Verify the intended HDA/catalog/registry/source and actual native output; a successful cook or request count alone does not establish placement.
Inspect actual cooked attribute owners/types/tuple sizes and separate instancer parts, resolved asset identities, and asymmetric/off-center transforms at nonzero yaw. Check authored offsets and scale/reflection where the capability uses them; preserve the defined conversion boundaries. Preserve explicit zero-based material emission including slot 0 and splitting by component material sets, then inspect actual native groups/slots, joins, shading, culling and contact. A shared transform test does not certify every model.
Use the retained scoped Replace Previous Bake behavior and removal/accounting of cooked output; do not use an undocumented manual export as equivalent evidence.
Save only the exact owned generated dependencies and named original map, then reopen in a fresh process and compare the saved output.
Repeat ordinary generation on the same map and verify intended replacement without duplicate or stale output, then retain its save/reopen evidence.
Record real family/model/part identities, geographic source IDs, transforms/materials, unsupported cases and inspectable locations; all families need not appear in one run.
Report native bank placements/assemblies separately from retained source-shell fallback and omissions, against the target's declared allowance. Lifecycle success alone does not establish full bank coverage.
Compare source/generated appearance and required contact/clearance using the route's actual measurements and views; automatic count equality is not visual approval.

## Keep the evidence levels separate

The per-kit/area handoff should link source adaptation, native saved/readback, Houdini selection/output, integrated references, ordinary first save/reopen, repeat save/reopen and visual acceptance as separate results.
Record the exact catalog/HDA/registry/source revision for each run. A map generated against an older bank digest is not proof of a newer connection patch.
Later manual map changes can make a workflow's original instance count historical; use the actual subsequent saved/reopened receipt for current state.
Ground painting and vegetation PCG have separate Unreal-only consumer catalogs even when they reuse the same physical assets.
No instruction here releases their holds, changes area scope, rewrites shared sources or claims complete native acceptance from preparation.

[shared-source]: <C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank/revisions/20261018_normal_semantics_v001/20261017_stable_bank_instancers_v001/GeoCity_city_v015_PermanentBank_StableBankInstancers_v001.hdalc>
