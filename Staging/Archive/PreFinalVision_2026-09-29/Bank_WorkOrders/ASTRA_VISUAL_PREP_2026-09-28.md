# Astra bank inspection preparation — 2026-09-28

Status: PREPARED ONLY. No UI interaction, Unreal launch, Houdini launch, asset load or visual inspection has occurred in this assignment. Manager must confirm Aviv's exclusive editor window before launch. Earlier Operator/STOP remains intact.

Scope: nine already-present current-project candidates listed in `ASTRA_VISUAL_PREP_CANDIDATES_2026-09-28.csv`. Names and paths are candidate-index facts; object identity/class/load remains unverified until opened. Inspection is capped at 45 minutes after manager go, with partial results reported honestly. Prioritize the seven meshes before the two material previews if navigation is slow.

## Candidate rationale

- Whole buildings: Bank_ME_v3 SM_H0907_Arab_x3_fbx and SM_H0014_Building_01; compare form and investigate the previously documented standard1 material concern. The proposed regional versus tall/heavy comparison remains inference until viewed.
- Modules: ModularCourtyard SM_wall_windows_4x4_01 and ModularBuildingSet store_front_shutters_4x1_a; inspect isolated facade roles, without asserting BG compatibility or regional suitability.
- Prop: Bank_ME_v3 SM_H0051_Garbagebin.
- Vegetation: Bank_ME_v3 SM_H0636_Acacia; inspect the previously documented missing-texture concern.
- Sign: Bank_ME_v3 SM_H0082_Streetsign; record actual visible graphic/language only if legible.
- Road material candidate: StarterContent M_Concrete_Poured.
- Ground material candidate: FC_Coastal_Landscape M_Master_CL_Landscape; native preview is not Landscape application evidence.

## Execution after explicit manager go

1. Select the uniquely identified current-project editor window using Computer Use returned window objects. If a launch is needed, launch only the current project through Windows/PowerShell. Record initial process/window, current map and any visible dirty state. Unexpected dirty state, another operator or a blocking modal stops the session before changes.
2. Use Content Browser search/navigation to the exact listed package, inspect identity/type, then open the asset's own native editor. Do not drag into a map. Handle one asset at a time.
3. Inspect visible form and material appearance from a framed preview, then a second useful angle. Record the preview limitations and any visible error or missing surface.
4. For meshes, capture the stats overlay and readable details: dimension labels/units, displayed LOD and triangle count, LOD count, material slot names/paths, collision settings and collision overlay as exposed. Observe pivot/origin with preview visualization only. Numeric local bounds, pivot offsets, contact, axis conventions and build scale stay unknown if not explicitly visible. Never derive exact numbers by visual estimation.
5. For materials, capture class, native preview and visible settings/compile status. Do not edit graph, parameters, assignments or apply changes. Mesh dimensions/collision are not applicable.
6. Close inspected asset tabs without saving. Do not discard pre-existing unsaved content. Report unexpected dirty indicators before proceeding.
7. Return receipt and comparison with observed, unverified and not-applicable fields, screenshot references and explicit next checks. No automatic changes to the candidate index.

## Evidence

All new files stay under Staging/ModelBank. Conditional screenshot names: `<asset_id>__01_identity.png`, `__02_form.png`, `__03_stats_materials.png`, `__04_collision_pivot.png` where relevant. PNG evidence is produced only if a supported capture/save workflow is available without Content or map changes. Otherwise record actual returned screenshot IDs and capture times as UI-observation references, and mark durable PNGs not produced. Computer Use captures display automatically: do not decode, save or re-emit their payloads solely for inspection. Do not manufacture views or statistics. Missing views are recorded as not run. A receipt CSV stores exact asset ID/path/class/load result, appearance, dimensions/units, pivot observations, LOD/triangles, collision, materials, view references and unresolved checks. Any numeric value requires its own visible source.

`ASTRA_VISUAL_RECEIPT_TEMPLATE_2026-09-28.csv` contains all nine exact candidate IDs and expected object paths plus the observation fields and planned screenshot filenames. Every row is `[not run: BANK-VIS]`. Planned filenames are not evidence that images exist. On execution, write a separate actual receipt; use `[measured: relative screenshot path]` only for directly observed values, `[documented: source]` for inherited facts, `[inference]` for visual role/style interpretation, and `[not run: check]` for missing checks. Use explicit `not_applicable` for mesh-only fields on material assets.

## Stop conditions

Stop at the 45-minute cap, loss of exclusive control, user/manager stop, unexpected dirty content or save prompt, target project/window ambiguity, security/authentication modal, editor crash, or repeated capture/control failure after the skill's bounded recovery. Never accept a save, overwrite, delete, import, compile/apply change, cook or bake to unblock this inspection. Record the exact blocker and last observed state. An individual unavailable asset is recorded failed/not run; proceed to the next listed asset only if the editor remains stable and the scope remains unchanged.

## Boundaries

No generation, cook, bake, HDA/session work, import, Content mutation, map save, Track B edit, Linear, Tier 1, BG1 or qualification decisions. Native preview observation does not prove generator compatibility, persistence, rights clearance, region/style approval, physical collision behavior or acceptance. All eligibility and generation flags remain unchanged.

## Guidance read

Root AGENTS.md; MANAGER_HANDOFF_2026-09-28.md; BANK_CANDIDATE_INDEX_2026-09-28.csv (parsed and scoped); ORGANIZATION_AND_NEXT_STEPS_2026-09-28.md; entire computer-use SKILL.md plus guidance.md and confirmations.md. Use node_repl and @oai/sky for desktop control. Observe, inspect, perform one action, refresh. No terminal commands through UI and no general project automation.
