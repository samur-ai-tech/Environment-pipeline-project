# Reusable sky and time of day package

Current delivery update (2026-10-06): Stage 1 and Stage 2 native assets are now saved and fresh-process reopened on original Rimal. See [Stage 2 receipt](Stage2/RESULT.txt) and [usage](Stage2/QUICK_START.txt). The planning/inspection statements below are the original pre-implementation baseline; seamless wind retiming and the receipt's explicit limitations remain open. Stage 3 is not implemented.

Prepared for Aviv on 2026-10-06. Status: implementation plan; no native package has been built or placed.

## Intended result

One reusable `BP_EnvironmentSky` actor provides sky, sun, volumetric clouds, atmospheric haze, moonlight, a visible moon, and stars. Drag it into a compatible outdoor scene and choose the time of day through a clearly labelled control. The package is independent of GeoCity generation and of ground, vegetation, buildings, and roads.

The time control itself is straightforward: Unreal's Sun Position Calculator already supplies geographic solar positioning. A polished, portable day-and-night package additionally needs cloud and night materials, exposure tuning, existing-light handling, and native save/reopen verification. This is the staged implementation option requested by Aviv, not a claim that a ready-to-use asset exists.

## User controls

Keep the default Details panel small. Put technical controls in Advanced.

| Control | Intended behavior |
| --- | --- |
| Time of Day | 0–24 slider with a readable HH:MM display; 24:00 wraps to 00:00. Updates the editor preview without Play. |
| Date and Location | Geographic position, date, UTC offset, and explicit daylight-saving choice. These determine sunrise and sunset; no fixed 06:00/18:00 assumption. |
| North Direction | 0–360 degree offset to align the sun path with the scene. A visible editor arrow shows north. |
| Manual Sun | Optional mode with direction and elevation controls; time calculation stops controlling the sun until Time mode is restored. |
| Sky Look | Clear, Partly Cloudy, Overcast, and Hazy presets; presets change atmosphere, not the chosen clock time. |
| Cloud Amount | Clear-to-overcast control, with cloud speed and direction under Advanced. |
| Haze | Subtle atmospheric depth through to visible haze. |
| Night | Moon brightness, moon phase appearance, and star brightness. The first moon orbit/phase controls are artistic, not an astronomical lunar simulation. |
| Quality | Balanced and High; tune package components without changing global scalability settings. |
| Animate Time | Off by default. Optional day length and pause control; manual time remains the normal workflow. |

The final quick-start must be: enable the stated dependency once, place the actor, resolve any existing sky-lighting conflict, set location/north, and choose time. No manual Blueprint graph edits for ordinary use.

## Technical choice

Use Unreal native atmospheric rendering and the installed Sun Position Calculator plugin. A project-owned wrapper around SunSky is the first implementation choice: it reuses the existing solar calculation and adds cloud, haze, moon, and star components. Verify child-actor editor updates before freezing that structure; if necessary, use the plugin's exposed solar calculation with directly owned components instead. Do not maintain two independent solar calculations.

Use engine cloud resources plus project-owned material instances for the portable base. Keep preset data and controllable material instances inside the package. A moving sun must remain coherent with the rendered sky; fixed HDR panoramas are not the default for continuous time changes.

The installed PWL pack is a visual and material candidate, not a proven time-of-day controller. Its sun/hour control behavior has not been established from native Blueprint inspection. Evaluate only the relevant cloud/night resources during the authorized editor turn. Include vendor resources only when their appearance, editable controls, dependencies, and permitted reuse justify them; do not duplicate the entire lighting manager alongside SunSky. The base package should function without PWL or MW.

Epic documents geographic solar time, date, north offset, and location in [Sun and Sky](https://dev.epicgames.com/documentation/en-us/unreal-engine/sun-and-sky-actor-in-unreal-engine). Its lighting and exposure defaults require scene tuning. [Sky Atmosphere](https://dev.epicgames.com/documentation/en-us/unreal-engine/sky-atmosphere-component-in-unreal-engine) supports atmospheric sun and moon lighting; detailed stars and a textured moon require additional content. [Volumetric Cloud](https://dev.epicgames.com/documentation/en-us/unreal-engine/volumetric-cloud-component-in-unreal-engine) supplies cloud rendering and engine material resources.

## Stage 1 — Retained package and sun control

1. Obtain the sole manager's bounded editor assignment under the existing project rules. Confirm current PID, world, dirty packages, and automatic cooking state before native work. Preserve the live editor's unrelated buffers.
2. Verify and enable the installed Sun Position Calculator dependency through a coordinated clean restart if required. Record only the exact necessary project configuration change; do not change unrelated plugins or rendering defaults.
3. Create the retained package under `/Game/Project/Shared/Atmosphere/ReusableSky/`, with `BP_EnvironmentSky` as the user entry point.
4. Implement Time mode, location/date settings, north offset, and Manual Sun mode. Both modes update in the editor; manual rotation is not silently overwritten by the time solver. Runtime time changes must use the same update function.
5. Add sky lighting and explicit exposure controls. Existing camera/post-process exposure remains authoritative unless the user enables the package's exposure override.

Completion: on the manager-selected original map, changing morning/noon/evening time changes the sun direction, shadows, and sky coherently; repeating the same settings gives the same result. Save only the named package assets after review.

## Stage 2 — Clouds and atmospheric appearance

1. Add volumetric clouds with one package-owned material instance per placed sky actor so editing one instance does not alter all scenes.
2. Map Cloud Amount to measured material parameters, including actual clear and overcast endpoints. Add cloud motion controls and appropriate sun/moon cloud lighting.
3. Add haze/fog controls and clear, partly cloudy, overcast, and hazy presets. Keep haze restrained by default so the existing environment remains visible.
4. Tune direct light, sky fill, cloud shadows, and exposure together. Overcast should soften direct sunlight rather than simply placing opaque clouds over an unchanged lighting setup.
5. Record Balanced and High settings and compare their frame cost from the same camera. Select the default from the actual scene and hardware, not an unmeasured quality promise.

Completion: retained views show useful cloud variation, a readable horizon, and coherent illumination without abrupt exposure changes, glaring white skies, or cloud-motion discontinuities.

## Stage 3 — Sunset and night

1. Add a second atmospheric light for moonlight and a visible moon material with adjustable phase appearance. Keep its visual direction aligned with its light. Do not describe the first implementation as astronomically accurate lunar positioning.
2. Add stars using project-owned procedural material content or a qualified existing texture. Fade stars according to sun elevation; clouds must correctly occlude the moon and stars.
3. Blend direct sun/moon intensity and sky fill smoothly through twilight. Suppress below-horizon direct sunlight appropriately. Keep night visibly distinct from daytime rather than increasing exposure until both look alike.
4. Provide optional time animation and pause; no continuous expensive updates when time and weather are static. Do not run time progression in the editor by default.

Completion: sunrise, noon, sunset, and night are visually checked on the original area. Include a near-midnight transition and verify no jump at the clock wrap. Record moon and star behavior as well as lighting.

## Stage 4 — Scene integration and portability

1. Inventory existing Directional Lights, SkyLight, SkyAtmosphere, clouds, fog, sky domes, and exposure volumes. If a conflicting sky system exists, the package must report the conflict and await explicit selection; it must not silently delete, hide, or overwrite existing actors.
2. Initially keep the new rig inactive on conflicting scenes. A deliberate activation step records the exact previous component states needed for reversal. Avoid automatic scene mutations in the Construction Script.
3. Repeated updates must reuse owned components. Detect a second active rig and stop activation instead of doubling sun/sky lighting. Never modify another map or global material parameter collection unintentionally.
4. Ensure the rig is separate from GeoCity-generated actor ownership and replacement ledgers. No HDA/profile/runtime edit or regeneration is required to use it. Review the existing replacement rules read-only before placing it in a retained area.
5. Save the exact reviewed assets and map; reopen and verify settings, references, and appearance. Demonstrate the same retained package on a second original area when assigned by the manager, without creating disposable maps or demonstrations.
6. Produce the dependency manifest, installation notes, and migration instructions. Use Unreal's dependency-aware migration for another compatible project; engine/plugin dependencies must be enabled in the destination. Do not promise compatibility with every engine version, renderer, or platform.

Completion: one shared package works in the assigned original scenes, no duplicate sky systems appear after edits or reopening, and all required dependencies and version requirements are recorded.

## Delivery

Planned native location: `/Game/Project/Shared/Atmosphere/ReusableSky/`.

- `BP_EnvironmentSky`, project-owned materials/instances, preset data, and any required supporting assets.
- A short English quick-start and a simple Hebrew usage explanation for Aviv.
- Dependency manifest identifying Engine/SunPosition resources and any optional vendor content separately.
- Before/after views from the same original-map camera, plus morning/noon/sunset/night views.
- Exact named save/reopen results, measured quality settings, unresolved limitations, and separate visual acceptance by Aviv.

The first usable delivery is Stage 1 plus Stage 2. Full requested day/night delivery includes Stages 3 and 4. No asset is described as delivered merely because a plan or source script exists.

## Current inspection evidence and execution boundary

- Read on 2026-10-06: `Content/PWL_Light_Manager/Blueprint/BP_Lighting_Manager.uasset`, seven HDR textures, cloud/night material files, and supporting lighting data exist on disk. This is content presence, not verified runtime behavior.
- The installed `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Runtime/SunPosition/SunPosition.uplugin` identifies Epic's Sun Position Calculator, allows content, and sets `EnabledByDefault=false`. The project descriptor contains no explicit SunPosition entry. Actual live loaded-plugin state was not queried.
- The OS inspection found UnrealEditor PID 29900. The last owner record reads `OWNER=NONE`, released after the Iran run. This is a released record, not an editor assignment for this chat. Current world and dirty packages were not queried; the manager handoff is historical evidence of those details.
- `AGENTS.md` retains Claude session `cc37d4d2-3d62-4f53-b689-28432b5527ae` as sole manager and prohibits self-issued leases. This plan does not transfer management or activate native work.
- No native tool calls, plugin activation, editor restart, map changes, material edits, source changes, asset saves, or generation were performed. Only this planning document was created.

This side package does not replace or reorder the manager's existing ground/system work plan. Its native implementation needs a bounded place in that schedule.
