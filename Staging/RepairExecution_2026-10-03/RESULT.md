# Retained environment repair result

Updated 2026-10-03, Asia/Jerusalem. Measured result: the requested generation, native coverage, support and roof defects are repaired in the shared r017 generator and both existing saved areas. Final artistic acceptance remains separate.

## Actual retained result

Both real areas were regenerated, baked with scoped replacement, explicitly saved and opened again in the same editor with cooking paused and no recook. Every recorded native mesh/material reference and all transferred anchors were checked; maximum allowed anchor error is 1 mm. Both saved areas have one Landscape, 23 baked actors, zero cooked mesh components, zero proxy primitives and seven clean named generated dependencies plus their map. This is saved-map persistence in one editor, not a fresh-process restart claim.

| Area | Buildings | Whole native | Native assemblies | Native trees | Native poles | Native street props | Native part/asset instances |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GazaRimal | 269 | 60 | 209 | 45 | 27 | 23 | 16,009 |
| GazaShujaiya | 398 | 41 | 357 | 79 | 53 | 41 | 18,016 |

The 34,025 native instances include 33,377 facade/filler/door module instances. They are not 34,025 distinct assets or buildings. There are 667 actual geographic building pads: 101 whole native buildings plus 566 retained native assemblies, zero unsupported pads. Floor/roof slabs and corner closures are generated closed geometry with existing native materials. Geographic source packages and native originals remain intact.

## Changes and verification

- Preserved height provenance: only actual source height/floor data imposes a hard height gate; seeded heights are preferences. Native whole-building scale remains 1:1.
- Closed the medium-building size gap with measured facade bays, bounded widths/story heights, 1 m/2 m filler panels, real steel-door openings, true footprint floors/roofs and clipped corner solids. Simple concave footprints are supported. The shared generated solids now use outward Houdini winding and aligned normals, fixing the visibly open/black roofs.
- Corrected terrain support on the authoritative grid: complete pad interpolation-cell support, coherent touching-pad datums and bounded graded collars. The generator checks full whole-building support. Live Landscape-only collision samples at four whole buildings per area measured maximum bbox support-plane errors of 1.047 cm in Rimal and 1.214 cm in Shujaiya; these are sampled bbox planes, not every foundation vertex.
- Derived roadside positions from native asset dimensions and bounded candidate searches; configured the supported non-held native utility pole for both areas. Street furniture and poles now survive the full footprint/clearance checks and appear as native baked instances.
- Applied bounded generated-tree fitting within the original vegetation seed cell. Final failed generated decorations are explicitly omitted rather than rendered as box/cylinder proxies. Rimal omitted 15 of 60 generated trees and 9 of 36 generated poles; Shujaiya omitted 35 of 114 trees and 4 of 57 poles. These 63 omissions are not native substitutions or deletion of surveyed source features.
- Retained previous successful baked-actor/package ledgers across failed runs. Optional empty outputs can disappear without leaving old baked copies; ordinary regeneration can still recognize exact unreferenced Cook leftovers after a failed attempt.

Official Engine completed the real replacements: Shujaiya r014 -> repaired r015/r016 -> r017 and Rimal r014 -> r017. Failed intermediate contract/API attempts are preserved; the final generator uses supported float4 orient attributes and forward-slash contract paths. Actual viewport inspection confirmed closed, lit roofs; an independent image read agreed for the Shujaiya elevated view.

## Exact retained paths

Shared HDA: `/Game/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank`.
External source: `C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank`.
Revision: `r017_retained_native_environment`.
HDA SHA256: `bd62ec4d9df7fa3b90b7959ebda927c0d85c7066fded8de1361e98f065d019b1`.
PythonModule SHA256: `e69e5da20a731e1b7295337a724a715bbdccc8d8fd4f1f64193ba9b75298000a`.
Native table: `/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4`.
Typed catalog digest: `135fda14b5173ca919b1568b3faff20e1763cfb3dc90c0635983d1ce32b3ded1`.

Rimal: `/Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration`.
Shujaiya: `/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration`.
Ordinary project action: `Tools > GeoCity: Generate / Regenerate Current Area`. Its existing official lifecycle performs input rebinding, configured rebuild/cook, scoped previous-bake replacement, cooked-output removal and named dependency/map saves. No separate disposable demonstration or alternate generator was introduced.

## Limits and preservation

Native assets and their materials are really referenced and retained. The selected variety remains narrow: repeated Courtyard facades, four whole-building models, one tree family, one utility-pole model and one street-prop model. Missing geographic height/storey/entrance data still uses explicit generator rules. Shrub/small-prop/understory requests that cannot fit remain rejected. Signs, roof utilities and vehicles are outside the assigned active asset lanes. Final artistic suitability and Aviv's visual acceptance remain open; counts and successful cooking do not imply that approval.

The current Landscape uses MI_SurfaceBank_AllLayers with Dirt_Path, Sand_01, Sand_02 and Sand_Path. Live readback verified all four area-local LayerInfo bindings and all eight native MOUT albedo/normal parameter values. Actual views show the textured route. The shared base MI's used-textures query returns an empty array and Python does not expose the component MaterialInstances property; this query is recorded as inconclusive about component shader sampling. No material compile error was found. Existing ray-tracing resident-memory viewport warning remains.

The same 1,223 catalog identities, qualification, rights and explicit holds remain. Eighteen scoped runtime rows are enabled (16 meshes and two materials); measured assembly dependencies use the separate normal-area contract without clearing unrelated prop-role projection holds. H0013, H0907, H0051, H0958 and declined palms remain held. No general bank release or new rights approval occurred.

## Editor handoff

OWNER=NONE; sole editor PID15568 left on GazaRimal. Official cooking paused, auto-cooking disabled, zero lifecycle callbacks, no dirty maps and no dirty named retained dependencies. 76 exact previously recorded unreferenced Cook packages remain unsaved; no broad save or deletion was used. Refresh ownership, processes, world and dirty state before later editor operations. Old heartbeat remains paused; no Linear work.

## Receipts

- [Rimal actual viewport](RIMAL_R017_CAPTURE.png)
- [Shujaiya actual viewport](SHUJ_R017_CAPTURE.png)
- [Machine-readable result](RESULT.json)
- [Rimal saved-map readback](REOPEN_GazaRimal.json)
- [Shujaiya saved-map readback](REOPEN_GazaShujaiya.json)
- [Focused original diagnosis](../Diagnostics_2026-10-03/ROOT_CAUSE.txt)
- [Lifecycle audit](LIFECYCLE_AUDIT.txt)
- [Appearance limits](APPEARANCE_LIMITATIONS_DRAFT.txt)
