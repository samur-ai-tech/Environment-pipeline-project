# Path B risks (GazaShujaiya, MW auto-landscape ground)

Labels: **M** measured, **D** read from source, **I** inferred, **A** assertion by the manager/Aviv (not verified here).

## 1. Grass contract
- **D:** with `landscape_grass.enabled=false`, the sealed lifecycle no longer authors or verifies native Grass for Shujaiya (LW:214-216; BW:651/658/832/888). Paint-readiness waits, coverage and normal pins are also gone for this area.
  - That is intended ("no grass for now").
  - Re-enabling grass later is **not** a profile flip. `_config`/`prepare()` require the Natural base and master (LW:39, :222-224) and re-parent `MI_GeoCityGround` (:366). Enabling grass while `landscape_material` points to the MW MI would fail at BW:650 or BW:51-54. It needs a new decision: rollback to Natural, or a Grass design for the MW material.
- **M (native graph):** the MW master has its own `LandscapeGrassOutput` (Rock, Stones, Grass, Dirt, Snow → `LGT_MWAM_*`). DesertExample leaves Rock, Stones and Dirt ON. The lifecycle would **not** catch MW scatter, because `is_native_grass` is False and MW meshes are not in `expected`, so they are silently ignored.
  - Mitigation: the MI sets all five `Use*Procedurals` OFF, with readback in apply, save and verify. Option 1 also checks them before every Cook.
  - Residual risk without Option 1: someone flips a switch on the MI later and nothing in the lifecycle notices.
- **I:** the Grass cache is viewer-dependent. A zero HISM count at load is advisory only. The switch state is the proof.

## 2. Houdini mask loss (accepted by Aviv for now)
- **D:** the HDA still paints Sand_01/Sand_02/Dirt_Path/Sand_Path weightmaps (MOD:3824-3895), and HE still creates their LayerInfos and weightmaps.
- **M:** the MW material samples only `RemoveFoliage` (MW_INVENTORY features.painted_layers). The weightmaps cost memory and do nothing visually.
- Roads read only through RoadBLD meshes, and pads only through buildings. Ground under roads and pads is MW slope/height colour, not Dirt_Path/Sand_Path.
- Slope/height masks are absolute: `MW_SnowWorldPosition`=0 against terrain at 38-50 m (profile probes). The colour mix depends on elevation and slope, not on geography (I).

## 3. Two areas drifting
- Rimal stays on the Natural master and grass profile (8711cace) and keeps the S1 status quo. The two Gaza areas will look different until Rimal gets its own decision.
- The shared Natural master, base MI and GrassType are untouched, so Iran is unaffected (D: Iran binds the base MI).
- The S1 tooling (`s1_verify.py`, `s1_capture.py`, `s1_material_edit.py`) assumes the Natural child for both Gaza areas, so its Shujaiya checks no longer describe the bound material.
- Any future shared-material work must state which areas it targets.

## 4. Reseal and governance
- Option 0 changes no sealed file. The manifest stays 258469e1 (M: `--check` passes today). The governance surface is the profile (1328d5bb → 54e3b19c), the map and one new Content package. These still need a manager record (RATIFICATION B3) under the B2 rule "every change to HDA, profiles, Content/Python or seal goes through the manager with a record".
- Option 1 changes LW, gives the predicted manifest 6cb588f6, and must be resealed by the manager only. Workers never run `seal_runtime.py` without `--check`.
- The MI lives under the area root, so the next ordinary run re-saves it if dirty (BW:948-984). Expect it in `named_generated_dependency_paths`.
- MW vendor packages: the 2026-10-05 inspection left 15 MW function packages dirty; they were restored from Vault (`Incident_01a10c77/MW_Func_modified_*`). The scripts refuse to run when any `/Game/MWLandscapeAutoMaterial` package is dirty, pin DesertExample/master hashes, and snapshot all 100 vendor files. Never call the MCP `get_material_info` tool on MW assets.

## 5. MW licence
- **M:** no licence/readme/EULA file in `Content/MWLandscapeAutoMaterial` or `VaultCache/MWLandsc0bb389159dceV3` (manifest only).
- **A:** "Installed from the Epic Launcher vault, so project use is fine." This is the manager's/Aviv's position, not verified evidence. Record it as such in B3. Redistribution or export of the MW textures outside the project is not covered by anything measured.

## 6. Sampler and performance on the 1009² Landscape
- **M (material statistics, not frame time):** master 2 samplers / 48 pixel samples / 524 pixel instructions; DesertExample 2 / 32 / 479.
- **I:** our MI adds 3 Advanced layers (ColorCorrection multiply plus an identity normal multiply), a few instructions, and one new static permutation. The first apply compiles shaders, which can take minutes; capture only after that.
- 4K SandA/SandC/Stones/Variation textures stream; distance blending (`MW_DistanceBlendFade*`) is inherited. The component count and real GPU cost are not measured (inspect records the components). Profile with `stat gpu` / `ProfileGPU` before calling it production-ready.
- The physical-material outputs (PM_MW_*) are now active on the Landscape. Physics surfaces change from Natural to MW (I), with no gameplay consumer known.

## 7. Process risks
- **Survival on regeneration:** proven by source and by B2 receipts for the profile route (D/M). For MW specifically it is still I until one ordinary regeneration runs. Route b of RESEAL proves it on the real save path; route a defers the proof to the next regeneration.
- **Component material instances:** apply requires zero components on the old MI and at least one on the MW MI. Verify requires all components on the MW MI. If an engine refresh lags, apply may refuse; exit without saving and retry in a fresh PID.
  - **Pending measurement:** it is not known whether `LandscapeComponent.get_material(0)` in 5.8 returns the per-component combination MIC or the Landscape material itself. In the second case the check only repeats the Landscape-material check.
  - The manager reads `sample_component_chain` in the inspect/apply receipts before calling component rebinding proven.
- **Verify re-run after other areas regenerate:** a Rimal/Iran ordinary run legitimately re-saves the shared Natural master, base and GrassType (LW:353). The verify script therefore treats those as advisory (`shared_changed_since_save_advisory`) and hard-checks only Shujaiya's old child and the MW vendor files.
- **Setter return values:** UE 5.8 Python setters can return False while applying (LW:375-377). The scripts trust readback only and record the setter returns.
- **Failure mid-apply** leaves only in-memory changes. Recovery is to exit without saving (exit_no_save pattern). The disk keeps B2, and the profile change is separately reversible.

## 8. Rollback
- With the editor closed, restore the profile backup (`--rollback`), then restore the map byte copy (`--rollback-map`, back to 4efebdfb).
- The map byte copy is valid **only until the next ordinary regeneration**: Bake replaces and retires actors and packages. The script refuses when `LAST_SUCCESSFUL_WORKFLOW_STATE.json` is newer than the backup. After that point, rollback = restore the profile + one ordinary regeneration.
- Option 1 only: restore `Before/geocity_landscape_workflow_d1a5d5fd.py` and run `seal_runtime.py`, which gives 258469e1 again.
- `MI_GeoCityGround_MW` may stay on disk unreferenced. Without the map copy, an ordinary regeneration after the profile restore re-binds `MI_GeoCityGround`, and `prepare()` re-authors and saves the Natural/Grass assets.
- Full commands are in RESEAL.md.
