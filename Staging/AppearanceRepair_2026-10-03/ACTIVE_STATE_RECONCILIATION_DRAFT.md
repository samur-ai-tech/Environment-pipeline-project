> HISTORICAL (2026-10-19): this file is kept as history. Current decisions: Docs/GOVERNANCE_RECORD.md. Closure index: Docs/CLOSURE_INDEX.md.

# Active state reconciliation — draft

Prepared 2026-10-03 16:45:41 UTC for root review. This file is a proposed reconciliation, not a published completion notice. `AGENTS.md`, `Staging/CURRENT_STATE.md` and `Staging/WORK_PLAN.md` were not changed. Root will publish final measurements after the current native road transaction completes.

## Current measured result

The active assignment remains retained appearance repair in the two existing named areas. The shared generator is `r018_retained_appearance`, reached through the official Houdini Engine route. All 667 geographic building pads remain covered: 101 whole native buildings and 566 native assemblies. GazaRimal has 269 buildings and 16,009 native part/asset instances; GazaShujaiya has 398 buildings and 18,016 instances, totaling 34,025. These are repeated native instances, not 34,025 distinct assets or buildings. Native references, facade/material partitions, geographic footprints and prior source packages are retained. Successful generation or persistence does not constitute final appearance acceptance.

| Area | Last saved geographic/HDA result | Native RoadBLD state |
| --- | --- | --- |
| GazaShujaiya | r018; 18,016 native instances; 42 HDA baked actors after vehicle-road/sidewalk suppression | Native generation `20261003T133607905511` saved and independently reopened in the same editor: 40 original source roads plus 6 native connectors; 46 total road actors; 89 RoadGeo/component bindings; 80 named native dependencies. Final visual acceptance remains open. |
| GazaRimal | Last successful saved r018 retains 16,009 native instances; 44 HDA baked actors and the Houdini visible-road provider | Current native transaction pending: 24 original roads, 43 RoadGeo actors and 2 recorded null bindings. Transient corrected geometry has not yet completed native binding, provider replacement, named-save and reopen verification. |

Shujaiya's immutable delivery JSON records `reopened=false` because it was written at the initial save. The separate reopen inspection passes exact saved bindings, geometry/material/collision readback and reports `reopened_binding_readback_verified=true`. It does not establish a fresh editor-process restart. Rimal's latest failed/current workflow state does not supersede its saved r018 result; `LAST_SUCCESSFUL_WORKFLOW_STATE.json` preserves that 44-actor generation.

Root's latest actual Rimal transient road-height measurement sampled all 24 source centerlines at intervals no greater than 1 m; maximum discrepancy was 7.729691 cm. One actual XY coverage gap of 5.141767 cm remains under repair. These measurements apply to transient geometry, and do not prove completed native bindings or a saved replacement. Null bindings are recorded separately; they are not automatically classified as a visible defect or accepted omission by this draft.

## Saved ground material repair

The retained native Landscape shader repair is complete and named-saved: exactly four assets, comprising two corrected Sand_01/Sand_02 normal copies, `M_SurfaceBank_Natural` and `MI_SurfaceBank_Natural`. The copies use linear sampling and normal-map compression. Original normal texture byte hashes remain unchanged, and all 69 material target names remain present. Four targets are actually painted: Dirt_Path, Sand_01, Sand_02 and Sand_Path; 69 supported targets do not imply 69 applied layers.

The shader now tints soil independently, uses its proper texture scale and combines two offset macro mask scales. Both existing area profiles contain exactly the two explicit corrected-normal overrides with immutable saved-receipt/hash provenance; other profile fields, including Rimal's pending native transaction, remain unchanged. Root reports that an actual Lit ground view shows native texture and soil patches. Final close/overview images and Aviv's aesthetic acceptance remain pending.

## Normal operation and ownership

The normal entry remains `Tools > GeoCity: Generate / Regenerate Current Area`. It selects the current named area's profile, uses official Engine input/Cook/Bake, scoped replacement, cooked-output removal and named dependency/map saves. The authorized native road role uses installed licensed WorldBLD/RoadBLD tools with exact geographic coverage and ownership checks; final suppression/save requires a validated matching native transaction. Geographic terrain, masks, buildings and bank placement remain in the existing HDA route. The current Rimal grounding/binding repair still needs to finish within that permanent lifecycle.

Root is the sole editor writer, `CODEX_APPEARANCE_MANAGER`, PID32752. The owner's reported bounded snapshot has official cooking paused and zero callbacks; a resumed live operation may advance that state. Source workers do not acquire the editor. Preserve native originals, source packages, scoped named saves, canonical catalog identities, existing rights/qualification boundaries and all named holds, including declined palms. The older heartbeat remains paused. No Linear action, general bank release, broad Save All or final user acceptance is implied.

## Historical paragraphs to reconcile on publication

- Label or archive the r017 snapshot with 23 baked actors, seven dependencies and OWNER=NONE PID15568 as historical evidence. Its persistent building coverage remains useful; its editor ownership, generator revision and actor/dependency counts are not the current state.
- Replace the active claim that Shujaiya native generation is merely running with its measured saved/reopened delivery. Retain the distinction between its 40 original roads and 6 derived connectors.
- Replace the blanket statement of 44 r018 baked actors in both areas with saved Rimal 44 and native-delivered Shujaiya 42. Keep native actors/dependencies separate from HDA actor/dependency counts.
- Replace the old current material/revision references (`MI_SurfaceBank_AllLayers`, r017) with the saved retained Natural material and r018. Keep older source hashes and results explicitly historical rather than deleting them.
- Keep remaining Rimal road grounding/binding/save/reopen work and both-area final visual acceptance open. Root must reconcile this draft again if the live state advances.

Evidence: `ACTUAL_GazaRimal.json`, `ACTUAL_GazaShujaiya.json`; Shujaiya `ROADBLD_DELIVERY.json` and `ROADBLD_INSPECT_GazaShujaiya_reopen_readback_20261003T143255794016Z.json`; Rimal `LAST_SUCCESSFUL_WORKFLOW_STATE.json`; `GROUND_SHADER_REPAIR_20261003T160849345599Z.json`; `BeforeGroundShaderProfiles/20261003T161245442596Z/MANIFEST.json`; latest transient Rimal measurements supplied directly by the sole editor owner. This worker made no editor calls.
