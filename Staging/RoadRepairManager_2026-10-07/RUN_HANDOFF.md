> HISTORICAL (2026-10-19): this file is kept as history. Current decisions: Docs/GOVERNANCE_RECORD.md. Closure index: Docs/CLOSURE_INDEX.md.

# Road contribution to the manager run handoff

Status: NOT_READY. No executable terrain-backend command is published yet. READY_FOR_FIRST_NATIVE_RUN, NATIVE_VERIFIED and AUTOMATIC_PIPELINE_COMPLETE are all false. This is a current blocker contribution; the manager must not present it as the final executable run handoff.

Latest implementation milestone: the operator's `Candidates/native_backend_v001/RoadTerrainBridge/` now contains the .uplugin, Build.cs, reflected header and C++ implementation. Actions are Inspect/Begin/Apply/Poll/Rollback/Commit. Source is mutable during implementation; no frozen build bundle or binary exists. Python runner/input producer and defensive checks remain in progress. Native source availability does not establish module load, persistence, rollback or native verification. Aviv's direct CONTINUE instruction was relayed to the existing sole operator; useful implementation continues without new chats or renewed generic permission.

Superseding pinned milestone: `Staging/RoadBLDRepair_2026-10-07/Candidates/native_backend_v001/BUNDLE.json`, SHA256 `8f12eb19513b053941df9a3643c8777ef9a9d9cc0cc1cc48d6e22448f3cf5fd1`, now pins 15 source/evidence files, five installed baselines and three dependencies. All 23 pins independently match. The runner and caller are delivered as inactive source; no binary exists. The operator's adjacent FUNCTIONAL_FIRST_HANDOFF.md and BUILD_RECIPE.txt contain the concrete schema and isolated build command. This milestone supersedes the earlier mutable/native-only description above.

Actual inactive signatures: `post_bake_runner.start(manifest_path, identity_provider, support_provider)`; automatic caller configuration `pipeline_hook.configure(bank_run, manifest_path, identity_provider, support_provider)`. Runner yields on editor ticks to verified_unsaved; explicit job.commit() or job.rollback() at the owned boundary. They are not yet runnable on the installed system: native module and real input providers are missing. Each update/restore phase deadline is 240 seconds; blocking native engine calls remain unmeasured. Eight fake-native control-flow checks are not native verification.

Actionable external build request routed to root: review the pinned source and permit only the exact isolated staging BuildPlugin recipe; afterward pin real artifacts. No live install requested by that build recipe. Remaining integration work: independent current final asphalt/sidewalk classifier plus exclusion masks, fresh native identity provider, Option A suppression before validated geometry, calibration/nonzero restore and exact reviewed promotion/reseal. Editor-only patch serialization is explicitly not proof of saved merged height/collision persistence.

Successor v002 implementation update (bundle not yet finalized at this check): partial-save recovery now marks the persistence boundary before each bank and native-road dependency/map save, tracks API-true-and-clean successes and uncertain attempts, and forbids full rollback claims after any attempted save. Actual hook source and save placements checked; five fake-save regressions report PASS. `native_origin.create(bank_run, reviewed_extra_files)` now exists and freshly verifies official final baked Landscape membership, native GUID/path/PID, process creation time, source/export and artifact pins; seven mocked-Unreal provider checks report PASS. This closes the source omission of the origin provider but does not prove native ReadIdentity compilation/load. Independent support classification/masks, Option A suppression, calibration and real saved/reopen verification remain. Frozen v001 is preserved; exact successor pin will supersede it only when delivered.

Concrete automatic-generation suppression blocker: installed RoadBLDRuntime.Build.cs:11 uses bUsePrecompiled=true; the expected DynamicRoad/DynamicRoadNetwork implementation headers are absent. Generated UHT metadata exposes IntersectionPatchOverrides and per-signature bDisableLandscapeAlignment, but supported enumeration of all rebuild signatures before the first write is unproven. Per-road mirroring False alone does not prove intersection suppression. Minimum missing interface: supported per-network height-write suppression before rebuild, or complete deterministic prebuild signature enumeration with honored disable overrides and restoration/completion semantics. Routed to root for the existing manager/interface path. This blocks automatic adoption, not ongoing final post-Bake adapter source or isolated compile. No runtime Option B or after-write check substitutes for suppression.

Current immutable source bundle is v002: `Staging/RoadBLDRepair_2026-10-07/Candidates/native_backend_v002/BUNDLE.json`, SHA256 `16192747baa58b2cb0d1b298906094286e130224fd4a5c92c7f57791763e5c12`. All 31 pins independently match: 23 source/evidence, five installed baselines, three dependencies. This supersedes v001 for source review and isolated build; v001 remains preserved. Binary count zero, compiled false, native_execution false, NOT_READY. Partial-save ledger and fresh origin provider are implemented source; native origin still unverified/unconfigured. Operator proceeds with actual support classification/protected masks in successor-only staging. Exact build recipe and required remaining interface are in the current bundle, not inferred from older files.

Root supplied bounded offline BuildPlugin scope under Aviv's implementation/CONTINUE authorization. Existing sole operator proceeds with installed UAT/UBT/UHT into a new empty resolved task staging output, immutable input/baseline verification, normal compiler host and per-user logs/caches, exact command/log/exit and linked-artifact pins. Routine compile fixes use new successor source and fresh empty output. No editor, live plugin install/load, source/config/profile adoption, engine/vendor edits or native lease follows. Formal source review and zero-consumer adoption/reseal remain required before live use. Build execution/result is pending the operator's receipt; authorization is not compilation success.

See FUNCTIONAL_FIRST_HANDOFF.md for the bounded implementation assignment and saved visual baseline. Operator 01a115d6 is writing RoadTerrainBridge and the post-Bake runner; source, binary, command, schema, texture encoding and native completion/rollback are not yet delivered. No candidate binary has been installed. Exact invocation and numeric deadline must come from the actual completed implementation, not a proposed API name.

## Installed pins rechecked on 2026-10-07

| File | SHA256 |
|---|---|
| Content/Python/geocity_bank_workflow.py | d52711bc71a8ec4e77fe5a7e0ef9bbcb136fe73fc8afda665a7afe795ca7d5d0 |
| Content/Python/geocity_roadbld_grounding.py | 0a0d813a7a05f42ab6967bab6608e7e7fb2cd3fe6501fe80441d76f4dc951f89 |
| Content/Python/geocity_roadbld_workflow.py | 451bb0d4d0d2d318440ed1fef31a668e529549a7e7387b48229f6be70100f342 |
| Config/DefaultRoadBLD.ini | 7033849614db4bc773836e5dd35ed70a5fa1e965ef23a036fe4f9e3123649f43 |
| Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json | a4be18be0ac64b9b5e4c7792f067fc781362bdbe143f5a658207c22d8f691714 |
| Original Shujaiya BankIntegration map | d3e570a6de7d0daa754ef4768bda997923c0ee9b1dfb21b359fbcb83d81b87f2 |

These identify installed differences, not approval to alter sealed files. Candidate source/binary/profile/config hashes and exact package list are pending the operator's immutable manifest. Existing staged material guard and raster candidates remain inactive; neither supplies the native backend.

The current installed menu label is `GeoCity: Generate / Regenerate Current Area` (geocity_editor_action.py:270). It is the retained run entry point, NOT evidence that grading is wired or authorization to click it now. Its activation/area/profile/seal preflight remains required.

## Required executable handoff fields before readiness

Operator must supply actual literal runner command/menu hook, module load check, version-pinned input schema and concrete data files: final post-Bake Landscape actor plus native GUID; complete validated asphalt/sidewalk delivery; independent pad/bridge masks; grid/transform; target/alpha texture files and encoding metadata; baseline height/paint digests; exact owned layer and patch paths. Document update polling deadline, completed height/collision signals and idle check, including stop/cancel behavior. Build and module load may establish availability only; the retained native run establishes verification.

Global manager routes independent review, exact promotion/build/install and zero-editor reseal; root consolidates one run handoff. Roads remains sole road/map writer only in its manager-issued actual-PID window. No hot replacement, new lease, vendor mutation, runtime Option B or held-mesh cleanup.

## Required order and named saves

MG09 exact132 persistent hide -> ONE named original-map save -> fresh reopen; then ordinary geographic/HDA/official Engine run -> minimum native junction/curb/building-clearance repair -> FINAL Landscape Bake -> grading before first dependency save/native road commit -> independent height/collision/protection verification -> ground owner reapply -> vegetation owner rebind/reapply. Ownership and dirty buffers must transfer explicitly at each mapwriter handoff.

Named map only: /Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration. Additional generated road/patch/texture packages must be enumerated by the actual output manifest and approved scope before save; there is no blanket package permission. Preserve 87 held meshes and all ground packages outside the receiving owner's scope.

MG09 fresh reopen is visibility-only: retain 433 actors, 268 road actors and 176 regular-asphalt bindings, with exactly 132 scope-listed actors serialized hidden; preserve all 87 held meshes and 12 ground packages. Both network actor inventories remain. Do not require deleting old actors to pass hiding verification.

After generation, verify the actual new output manifest and only the exact retirements explicitly approved for that generation stage. New counts come from that manifest; no fixed MG09 count or implicit held-network removal is imposed. Fresh reopen must reproduce the approved output, owned layer/patch identities, support/collision agreement, unchanged protected/outside/paint hashes and regular-asphalt bindings. Same-input ordinary repeat must replace only the authorized prior output without duplicates or accumulated terrain deformation, then exact named save/reopen. Explicit staged calls are acceptable for a first useful run only if actually callable; missing automatic hook remains AUTOMATIC_PIPELINE_COMPLETE=false.

## Failure and recovery

Before irreversible save, error or timeout stops commit and restores baseline bytes, paint and exact prior owned layer/patch membership/priority/binding; verify collision and idle state. If recovery cannot be proved, preserve the buffer and receipts and request bounded manager recovery; do not save partial output. Sharing violation stops saving without bypass/retry against other editors. Restore affects only road-owned state; never save, close or discard another editor.

## Visible first result and genuine blockers

Target: one connected retained regular-asphalt road network with terrain meeting road/sidewalk support, preserved buildings, reapplied ground and qualified vegetation. Current screenshots still show raised roads and old ground. Blocking: native bridge/runner and encoding/completion/restore; validated support/classification and minimum safety geometry; reviewed adoption/build/module load/Option A reseal/profile; actual final-Bake input/caller; manager single-editor run. Ground boundary/material and vegetation final-map binding/DLL prerequisites belong to their owners. Cosmetic road variety and extra general-purpose qualification are deferred.
