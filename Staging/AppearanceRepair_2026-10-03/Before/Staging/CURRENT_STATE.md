# Environmentpipeline current state

Updated 2026-10-03, Asia/Jerusalem. Retained repair completed; this supersedes the r014 170/277-instance snapshots.

## Actual outcome

[measured: official Engine, live native readback, viewport inspection and saved-map reopen] The shared r017 generator repaired the selection/support/building-coverage/roadside/roof defects in both real areas. [Full result and receipts](RepairExecution_2026-10-03/RESULT.md).

Both real areas were regenerated, baked with scoped replacement, explicitly saved and opened again in the same editor with cooking paused and no recook. Every recorded native mesh/material reference and all transferred anchors were checked; maximum allowed anchor error is 1 mm. Both saved areas have one Landscape, 23 baked actors, zero cooked mesh components, zero proxy primitives and seven clean named generated dependencies plus their map. This is saved-map persistence in one editor, not a fresh-process restart claim.

| Area | Buildings | Whole native | Native assemblies | Native trees | Native poles | Native street props | Native part/asset instances |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GazaRimal | 269 | 60 | 209 | 45 | 27 | 23 | 16,009 |
| GazaShujaiya | 398 | 41 | 357 | 79 | 53 | 41 | 18,016 |

The 34,025 native instances include 33,377 facade/filler/door module instances. They are not 34,025 distinct assets or buildings. There are 667 actual geographic building pads: 101 whole native buildings plus 566 retained native assemblies, zero unsupported pads. Floor/roof slabs and corner closures are generated closed geometry with existing native materials. Geographic source packages and native originals remain intact.

Maps:
- `/Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration`
- `/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration`

## Reusable generator and normal action

Shared HDA: `/Game/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank`. External source: `C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank`. Revision `r017_retained_native_environment`, external HDA SHA256 `bd62ec4d9df7fa3b90b7959ebda927c0d85c7066fded8de1361e98f065d019b1`. Prior revisions/source and native originals are preserved.

`Tools > GeoCity: Generate / Regenerate Current Area` uses the current-map profile and official Houdini Engine input/rebuild/cook, scoped previous-bake replacement, cooked-output removal and named dependency/map saves. Successful actor/package ledgers persist across failures. This is the existing project route, not an added generator bridge.

Rimal profile: `Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json`; Shujaiya: `Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json`. Native table: `/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4`, 1,223 retained identities, 18 scoped enabled runtime rows, digest `135fda14b5173ca919b1568b3faff20e1763cfb3dc90c0635983d1ce32b3ded1`. Assembly uses the separate measured normal-area contract.

## Implemented repair

- Preserved height provenance: only actual source height/floor data imposes a hard height gate; seeded heights are preferences. Native whole-building scale remains 1:1.
- Closed the medium-building size gap with measured facade bays, bounded widths/story heights, 1 m/2 m filler panels, real steel-door openings, true footprint floors/roofs and clipped corner solids. Simple concave footprints are supported. The shared generated solids now use outward Houdini winding and aligned normals, fixing the visibly open/black roofs.
- Corrected terrain support on the authoritative grid: complete pad interpolation-cell support, coherent touching-pad datums and bounded graded collars. The generator checks full whole-building support. Live Landscape-only collision samples at four whole buildings per area measured maximum bbox support-plane errors of 1.047 cm in Rimal and 1.214 cm in Shujaiya; these are sampled bbox planes, not every foundation vertex.
- Derived roadside positions from native asset dimensions and bounded candidate searches; configured the supported non-held native utility pole for both areas. Street furniture and poles now survive the full footprint/clearance checks and appear as native baked instances.
- Applied bounded generated-tree fitting within the original vegetation seed cell. Final failed generated decorations are explicitly omitted rather than rendered as box/cylinder proxies. Rimal omitted 15 of 60 generated trees and 9 of 36 generated poles; Shujaiya omitted 35 of 114 trees and 4 of 57 poles. These 63 omissions are not native substitutions or deletion of surveyed source features.
- Retained previous successful baked-actor/package ledgers across failed runs. Optional empty outputs can disappear without leaving old baked copies; ordinary regeneration can still recognize exact unreferenced Cook leftovers after a failed attempt.

## Remaining appearance scope and preservation

Native assets and their materials are really referenced and retained. The selected variety remains narrow: repeated Courtyard facades, four whole-building models, one tree family, one utility-pole model and one street-prop model. Missing geographic height/storey/entrance data still uses explicit generator rules. Shrub/small-prop/understory requests that cannot fit remain rejected. Signs, roof utilities and vehicles are outside the assigned active asset lanes. Final artistic suitability and Aviv's visual acceptance remain open; counts and successful cooking do not imply that approval.

The current Landscape uses MI_SurfaceBank_AllLayers with Dirt_Path, Sand_01, Sand_02 and Sand_Path. Live readback verified all four area-local LayerInfo bindings and all eight native MOUT albedo/normal parameter values. Actual views show the textured route. The shared base MI's used-textures query returns an empty array and Python does not expose the component MaterialInstances property; this query is recorded as inconclusive about component shader sampling. No material compile error was found. Existing ray-tracing resident-memory viewport warning remains.

The same 1,223 catalog identities, qualification, rights and explicit holds remain. Eighteen scoped runtime rows are enabled (16 meshes and two materials); measured assembly dependencies use the separate normal-area contract without clearing unrelated prop-role projection holds. H0013, H0907, H0051, H0958 and declined palms remain held. No general bank release or new rights approval occurred.

## Handoff

[measured: FINAL_EDITOR_HANDOFF.json] OWNER=NONE; one editor PID15568 on GazaRimal, cooking paused, auto-cooking disabled, zero callbacks, no dirty maps or named retained dependencies. 76 exact unreferenced Cook leftovers remain unsaved. Ordinary action acknowledges them only after exact-ledger/reference checks. No Save All, broad deletion, extra editor, held release or Linear work. Old heartbeat remains paused.

The [single plan](WORK_PLAN.md) and [repair assignment/result](RepairExecution_2026-10-03/ASSIGNMENT.json) govern this outcome. The five 2026-10-02 execution chats and their task receipts remain historical. Superseded active documents are preserved in [RepairCompletion archive](Archive/RepairCompletion_2026-10-03/MANIFEST.json); earlier dated archives remain intact. No fresh editor-process restart or final user appearance approval is claimed.
