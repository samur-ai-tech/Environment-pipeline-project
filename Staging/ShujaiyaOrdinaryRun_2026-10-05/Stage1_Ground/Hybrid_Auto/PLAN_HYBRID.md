> HISTORICAL (2026-10-19): this file is kept as history. Current decisions: Docs/GOVERNANCE_RECORD.md. Closure index: Docs/CLOSURE_INDEX.md.

# Plan: Hybrid ground material for GazaShujaiya (MW auto-landscape + Urban layer)

Manager/operator: Claude session cc37d4d2 (sole manager per AGENTS.md). Decided by Aviv 2026-10-06 ("use Unreal's system", then "build the hybrid").

## Context

- Aviv rejected the Natural-master patch route (S1 v1: hard blotches, repetition) and chose the Unreal auto-landscape approach. An unsaved preview and an in-memory Path B apply (MW DesertExample instance, pale preset P1) looked right on our terrain but: (a) MW's material names only one painted layer, so on the next Houdini regeneration the plugin would DROP our four layers (HoudiniLandscapeUtils.cpp:941-972, Translator:666-671); (b) MW ignores the Houdini RoadBed/BuildingPad masks, so no concrete around buildings.
- The hybrid fixes both: a project-owned copy of the MW master that (1) names all four layers Sand_01/Sand_02/Dirt_Path/Sand_Path, (2) blends an Urban (concrete) layer in where Sand_Path + Dirt_Path weights are, (3) keeps MW's slope/height auto layering for everything else. Serves Gaza now and the future mountainous area (auto base + masks as overrides).
- No change to the sealed Python: external-material mode is already in effect (profile landscape_grass.enabled=false; profile landscape_material path; the only sealed checks are geocity_bank_workflow.py:650 material equality, the HDA path pattern, and launch pins). Grass stays off.
- Live state (07:40Z): map 4efebdfb; manifest 258469e1; Natural master 70f82e50; Shujaiya profile 1bd89e5b (changed 07:33Z by the modular bank chat: added building_assembly_contract.source_family_registry_ref; my Path B leaves intact: landscape_material -> MI_GeoCityGround_MW (NOT on disk), grass off); Rimal profile 492b9ac5 (same registry leaf). **An editor PID 35156 is open with no lease line** (bank chat, registry binding). **Shujaiya cannot be regenerated until the hybrid MI exists and the profile points to it.**

## Decisions (Aviv, 2026-10-06 ~07:45Z)

1. Urban texture set: **Asphalt_cracked** (Aviv's choice over the recommended Concrete_plate): /Game/ModularCourtyard/Textures/Asphalt/Asphalt_cracked/T_asphalt_cracked_{basecolor,normal,roughness} (+ _AO, _height available). Graph consequence: separate `Urban_Roughness` and `Urban_AO` texture objects instead of one ORM (+1 Shared:Wrap sample; sampler states still 2). Inspect must measure sRGB/compression/VT of these textures first; roughness/AO must be linear (sRGB off) — if not, STOP and choose the fallback set (Concrete_plate), never edit vendor/project textures.
2. Urban amount pads vs roads: **1.0 / 1.0** (full on both); tunable later.
3. Concurrent bank editor (PID 35156, no lease, edited both profiles at 07:33Z): **wait for its orderly release**; manager accepts the registry-ref leaf in writing (record in Incident folder) and re-measures profile hashes before step 2.
Manager decisions: injection Option A (Lerps into MakeMaterialAttributes_0; Substrate is on, root unchanged); do NOT feed Sand_02 into MW's rock mask; keep Concrete_plate as the documented fallback set.

## Asset layout

- Master `/Game/Project/Shared/SurfacePainting/Auto_20261006/M_GeoCityAuto` = `EditorAssetLibrary.duplicate_asset` of `/Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER` (vendor untouched; read-only refs to MF_MWAM_*/LGT/PM). Outside the profile root so the lifecycle never re-saves it.
- Urban graph (desc marker `GeoCity_GroundHybrid_20261006:`), ~40 nodes + 15 params, Shared:Wrap samplers:
  - 4× LandscapeLayerSample `Sand_01`,`Sand_02`,`Dirt_Path`,`Sand_Path`; `LayerPresenceZero = (W_Sand_01+W_Sand_02)*0` added into the mask so all four are reachable from the root.
  - `UrbanMask = sat( sat(W_Sand_Path*PadAmount + W_Dirt_Path*RoadAmount + LayerPresenceZero) * Urban_Amount )`.
  - UV = LandscapeLayerCoords × Urban_GridCm/Urban_TileCm; far UV = UV/Urban_FarScale; Dist = sat(PixelDepth/Urban_FarDistanceCm).
  - UrbanColor = lerp(Near,Far,Dist)×Urban_Tint; UrbanNormal = normalize(lerp((0,0,1),N,Urban_NormalStrength)); UrbanRough = sat(Rough.r×Urban_RoughnessScale) from `Urban_Roughness` (linear); UrbanAO = AO.r from `Urban_AO` (linear) — Asphalt_cracked ships separate roughness/AO maps.
  - Into MakeMaterialAttributes_0: BaseColor←lerp(StaticSwitchParameter_16, UrbanColor, mask); Normal←normalize(lerp(MF_14:Normal, UrbanNormal, mask)); Roughness←lerp(MF_14:Roughness, UrbanRough, mask); Specular←lerp(MF_14:Specular, Urban_Specular, mask); AO←lerp(1, UrbanAO, mask); Metallic unchanged. Master defaults neutral (Urban_Amount 0 ⇒ pure MW).
  - Params: Urban_BaseColor/Normal/ORM (texture objects), Urban_Amount 0, Urban_PadAmount 1, Urban_RoadAmount 1, Urban_TileCm 400, Urban_FarScale 6, Urban_FarDistanceCm 4000, Urban_GridCm 100, Urban_RoughnessScale 1, Urban_NormalStrength 1, Urban_Specular 0.5, Urban_Tint (1,1,1).
  - Sampler budget: MW master measured 2 sampler states / 48 pixel samples; +4 Shared:Wrap samples ⇒ still 2 (gate ≤3); weightmaps add ≤2 per component.
- Area MI `/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_Auto` (parent M_GeoCityAuto): DesertExample's 13 scalar + 11 texture overrides replicated (pathb_assign_and_save.py:70-82), 5 Procedurals OFF, 5 Advanced ON, Water OFF, Snow ON, P1 tints (PathB_MW/TINT_PRESETS.json), Urban params set (Amount 1, textures explicit, GridCm = measured Landscape scale X). Parity gate: all 99 MW params read back vs live DesertExample; exactly 11 allowed differences. Rimal MI later, own session.

## Scripts (new folder Stage1_Ground/Hybrid_Auto/, pins in Operator/SCRIPT_PINS.json; run via Operator/copilot_client.py)

- `hybrid_profile_patch.py` (offline, from PathB_MW/pathb_profile_patch.py): requires editor closed + OWNER=NONE; changes only `/landscape_material` → MI_GeoCityGround_Auto, `/external_landscape_material/parent_chain` → [M_GeoCityAuto], decision text; grass stays false; exclusive backups of profile + map; `--rollback`.
- `hybrid_build_master.py` (in-editor): inspect (vendor pins/snapshot, texture rows sRGB/compression/VT → sampler types, vendor graph dump, master+MI absent, dirty clean) → build (duplicate_asset; copied graph == vendor graph; add nodes + rewire MMA_0; recompile_material == []; gates: node count 190+N, other 189 rows unchanged, MMA_0 exactly 4 re-pointed inputs + AO, root unchanged, layer samples ⊇ the four + RemoveFoliage all reachable, every new sample Shared:Wrap, samplers ≤3, no vendor dirty) → BUILT_VERIFIED_NO_SAVE receipt. Offline mock self-test writes HYBRID_EDIT_EXPECTATIONS.json. Reuse s1_material_edit.py Builder (:771-912) and native_graph_stochastic.py describe/digest/reachable.
- `hybrid_assign_and_save.py` (fork of pathb_assign_and_save.py): apply (bound build receipt; bounded Urban args; parity gate; all 64 components bound; ≤5 applies/PID; allowed dirty {master, MI} + map) / save (`master_mi_map`: save_packages master, then MI, then save_map; dirty ([],[]) after; vendor + protected unchanged).
- `hybrid_verify_fresh.py` (fork of pathb_verify_fresh.py): fresh PID; receipts bound by sha; profile/master/MI/map hashes; graph digest == build's; 4 layer samples reachable; full MI readback; 1 Landscape, material == profile, all components bound; paint-probe weights (pads Sand_Path ≥0.8, roads Dirt_Path ≥0.8); `--post_regeneration` additionally requires LAST_SUCCESSFUL phase baked_saved_verified, parameters.landscape_material == Auto MI, the 4 `_landscape_<layer>` LayerInfo packages among named_generated_dependency_paths, target layer names ⊇ the four.
- Captures: maximize the editor window first (ShowWindowAsync SW_SHOWMAXIMIZED), wait for shader compile, MCP CaptureViewport at close/middle/wide presets (CAMERAS_GazaShujaiya.json); gate width>height and ≥1600 px.
- Lease lines: `OWNER=GEOCITY_GROUND_HYBRID … activation=GROUND_HYBRID_AUTHORING scope=GeoCity_GroundHybrid_20261006_auto_material`; verify: `activation=GROUND_HYBRID_VERIFY`.

## Run order

1. Preconditions: bank editor PID 35156 released in order (0 UnrealEditor, OWNER=NONE); re-measure profile/map/manifest hashes; manager accepts the registry-ref leaf in writing.
2. Profile: dry run, then `--apply`; record P′.
3. Launch via launch_editor.ps1 (map 4efebdfb, manifest 258469e1, profile P′); authoring lease with the actual PID.
4. Build master: inspect → build (no save).
5. Mask proof: apply #1 with high-contrast Urban_Tint (2.5,0.4,0.4); capture (shows where masks land).
6. First look: apply #2 neutral concrete + P1; capture; send to Aviv.
7. Tune ≤3 (MI values only). Graph change ⇒ exit without saving, rebuild in a new PID.
8. Save `master_mi_map` after Aviv's approval receipt.
9. Quit clean; OWNER=NONE.
10. Fresh launch (new map hash, P′), verify lease, `hybrid_verify_fresh` == VERIFIED_READ_ONLY, acceptance captures.
11. Ratification record RATIFICATION_B3_HYBRID.json (profile/map before-after, 2 new packages, receipts, images, sign-off).
12. Later: the clean regeneration run, then `hybrid_verify_fresh --post_regeneration` (4 LayerInfos recreated, Auto MI kept). Then Rimal; then the HDA skirt revision (dilate pads 3-6 m, roads +1.5 m, 2 m falloff; append-only override of cook_surface_palette derived from the v003 module; sibling revision folder + REVISION.json; manager-recorded reimport).

## STOP conditions

Vendor package dirty or pins changed; copied graph ≠ vendor graph; compile errors or "Default Material will be used" in the log; samplers >3; any of the 4 layer names missing/unreachable; texture VT on or sampler-type mismatch (choose another set, never edit textures); dirty outside {master, MI, map}; profile/map/manifest drift; >5 applies; Aviv rejects after 3 tunes.

## Risks

Regeneration layer drop (mitigated by reachable layer samples + post-regeneration check; proven only by a real regeneration); Rimal remains Natural until its own MI/profile; vendor function references (pins checked every script; never call MCP get_material_info — it dirtied 15 MW functions); sampler/permutation load (first compile minutes; measure GPU later); texture settings unmeasured until inspect; mountain area needs Urban_GridCm = landscape scale and matching painted_layer_names; rollback = profile backup + map copy (valid until next regeneration), delete new assets only when unreferenced (manager-only).

## Critical files

PathB_MW/pathb_assign_and_save.py, pathb_profile_patch.py, pathb_verify_fresh.py, TINT_PRESETS.json; S1_Prep/s1_material_edit.py (Builder); S1_Prep/AstraMWInventory/native_inventory_complete.json (MW graph dump); Staging/GroundPainting_2026-10-04/native_graph_stochastic.py; Content/Python/geocity_bank_workflow.py:650; Plugins/HoudiniEngine/Source/HoudiniEngine/Private/HoudiniLandscapeUtils.cpp; Staging/SystemCompletion_2026-10-04/launch_editor.ps1; Operator/copilot_client.py.

## Verification

Build gates + recompile == []; apply parity gate + 64 components bound; captures judged by Aviv (mask proof, then look); named save then fresh-process verify (hashes, graph digest, layers reachable, paint probes); post-regeneration verify after the clean run.
