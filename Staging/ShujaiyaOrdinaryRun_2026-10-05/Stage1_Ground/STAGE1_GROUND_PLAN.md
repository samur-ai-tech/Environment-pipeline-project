# Stage 1 Ground plan: GazaShujaiya + GazaRimal

**HISTORICAL as of 2026-10-06 (manager cc37d4d2):** this plan and its v1/v2/Path B sections are superseded by the hybrid plan `Hybrid_Auto/PLAN_HYBRID.md` and run order `Hybrid_Auto/README.md`. Thread ids, seal hashes and the grass rule quoted below are older than the current baseline B2 (manifest 258469e1; Shujaiya grass off; Aviv wants no grass for now). Current entry point: `Staging/MANAGER_HANDOFF_2026-10-06.md`.

PLAN ONLY, 2026-10-05. Nothing was executed and no editor ran. The plan is built from four read-only research passes and one critique in this workflow. This writer did not re-read the cited lines.

**Labels:** M = MEASURED (from a file or receipt), D = DOCUMENTED (official page), I = INFERRED.

**Short names:**
- GP = `Staging/GroundPainting_2026-10-04`
- REV = `GP/Revision_2026-10-05`
- LW = `Content/Python/geocity_landscape_workflow.py`
- BW = `Content/Python/geocity_bank_workflow.py`
- MOD = `C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank/geocity_city_module.py`
- Master = `/Game/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural`
- Child = `<Area>/BankIntegration_v015/Materials/MI_GeoCityGround`

**Cost rule:** Aviv objected to research agents running on Opus 5.5. Execution uses one operator chat per editor session, on the cheapest acceptable model, with no parallel research agents.

## 1. Context

Aviv rejected the fresh-reopen Lit images (`GP/Images/GazaShujaiya_epic_r030_fresh_*`, `GazaRimal_epic_r031_fresh_*`). His five defects:
1. No colour variety.
2. Pale and uniform at middle and wide distance.
3. Visible repetition and tiling.
4. Sharp joins and strips between surfaces.
5. Buildings and roads look placed on the ground, with no contact.

**Already tried** (M: REV `VIDEO_REVIEW.md:76-88`, `VISUAL_ITERATION_HISTORY.json`, `RESULT.txt:22`):
- Soil strength 0.10 → 0.35: dark gouge chains.
- Dirt normal 0.85 → 0.20, SandFarScale 2, CellScale 0.1 → 1.
- Sand tint (0.78, 0.84, 0.94): no gain.
- r015 stochastic Sand_01: insufficient visible gain.
- Full Epic palette swap, r027-r031.

**Why these were not enough** (M+I): every attempt tuned instance values or swapped textures inside a graph that has fixed ceilings.
- `Clamp_3` caps macro at 0.08, `Clamp_21` caps soil alpha at 0.35, and `Clamp_20` limits soil tiling to 20-35 m.
- Roughness is a constant 0.8, AO is a constant 1, and there is no far colour and no normal fade.
- Many tuned controls are dead: `Ground_MacroContrast/Tile2Cm/OffsetCm`, `Ground_MacroSoil*`, `GeoCity_RoughnessDetail`, `GeoCity_AOStrength` and `*_PackedMask` (`Stage1_Ground/MATERIAL_GRAPH_REACHABILITY_r030.txt`).
- The masks are binary, and no contact mechanism exists.
- The ground chat agrees that a palette swap cannot reach reference quality (REV `RESULT.txt:21-22`).

**BLOCKER: fix before any image counts.**
- M: Both children bind `Sand_01/02_Normal` to `EpicResident2K/T_Ground_Gravel_N_GeoCityResident2K` and `T_Rock_Sandstone_N_GeoCityResident2K` (REV r030 verify dump `before.instances`; REV `EPIC_RIMAL_CONSUMER_PLAN_R031.json`).
- M: Both profiles still require `T_Sand_0{1,2}_Normal_GeoCity` (`Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json:78053`; `Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json:83561`).
- M: LW:112-121 raises on that mismatch. It is called from `prepare()` at :370 and from `verify_landscape()` at :421.
- I: The next ordinary Generate therefore stops before Cook. This assumes those profiles are the ones loaded, which is not confirmed.
- M: The saved `GeoCity_GrassCoverage` is 0 (REV `RESULT.txt:19`). `prepare()` writes 0.15 (LW:377), `verify_landscape()` requires 0.15 (:418-420), and `_config` rejects 0 (:47-50).

## 2. Root causes

| # | Cause | Evidence |
|---|---|---|
| 1 | Ground, RoadBed and BuildingPad all bind one gravel D/N, and every tint is 1. The macro is one scalar octave, on Ground only, at ±8%. The soil partner is the same gravel (alpha ≤0.35, strength 0.1). Ground ≈1 on flat ground. | M: REV `RESULT.txt:6`; r030 dump; `Stage1_Ground/SAND01_COLOR_BRANCH_TRACE_r030.txt`; MOD:5134-5137 |
| 2 | The far set is the same texture at a larger UV, so its mip mean is pale. There is no far colour. Roughness has been 0.8 and AO 1 since r027. Epic's originals use 3 macro octaves (×0.125-3.4), a roughness lerp and a far colour. Auto exposure and atmosphere may also contribute (I, unmeasured). | M: REV `EPIC_GROUND_INTEGRATION_REVIEW_GazaShujaiya_r027_PID32464.json`; REV `EPIC_STARTER_GROUND_NATIVE_READONLY_PID32464.json`; `Config/DefaultEngine.ini:24,26` |
| 3 | Cells translate only and exist on Ground only. Steep, RoadBed and Pad have no anti-tiling. Normals stay at full strength at every distance. The macro is weak. The faceted hill is geometry, cause unproven. | M: r030 dump; REV `VISUAL_REVIEW_GazaShujaiya_epic_r030_fresh_PID18844.json:80`; `VISUAL_REVIEW_GazaRimal_epic_r031_fresh_PID35000.json:93` |
| 4 | RoadBed and Pad are binary PIL polygon fills on a 1 m grid, combined by hard products. About 96% of weights are exactly 0 or 1. The blend is LB_WEIGHT_BLEND with no Height pin. The 0.35 m/m collar slope gives Steep ≈0.22, which shows as sandstone rings. Rimal's strips and slivers are probably lifted single-sided meshes (I). | M: MOD:23-24, 577-584, 619-620, 3832-3842, 5033-5036, 5687-5690, 5766, 5806-5807; GP `GazaShujaiya_baseline_PROBE_PID31080.json` |
| 5 | There is no plinth, skirt or decal, and walls start at the pad datum. RoadBLD sits 5 cm above the terrain with a 15 cm curb and never edits the Landscape. Sidewalks are lifted 0.16 m. There is no RVT, and AO is constant. | M: MOD grep; `Content/Python/geocity_roadbld_grounding.py:133-176`; `geocity_roadbld_workflow.py:34-36` |

- D: LB Height Blend "adds detail to the transition between layers based on a height map", so it cannot widen a 1 m binary edge (https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-materials-in-unreal-engine).
- D: RVT needs an RVT asset, a Volume, Output nodes in the mesh materials and a Sample node in the Landscape material (https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine).

## 3. Approach: one path, five sub-steps

**Principle:** make real changes in retained shared assets, so they survive `prepare()` and regeneration. Do the material work first, because it can run now with no reseal. Do the HDA work second, because it is gated.

**Iran rule.** M: `Staging/ModelBank/Iran_38196167_46086167_4km/AREA_PROFILE.json:13` binds the base `MI_SurfaceBank_Natural` directly.
- Every new master branch must be neutral at its default value: amounts default to 0, and the parameterised clamps default to today's 0.08 / 0.35 / 2000-3500 cm.
- The base MI keeps those defaults. The effects are enabled only in the two Gaza Children.

**Edit in place.** I: a new master or base path would be a sealed-Python change (LW:15-16, :222-224, :366, :416). New logic goes into new `MF_GeoCity_*` packages, so the master edit is only a few function calls plus rewiring.

**S0: Prerequisites** (no editor, small)
- Confirm which AREA_PROFILE the next ordinary run loads.
- Run a read-only texture inventory: GeoCity `T_Sand_0x` copies, EpicResident2K, StarterContent, NativeUnrealAssetSupply candidates and the 69-layer bank sources. Pick one distinct, value-matched albedo/normal per role, plus a soil partner that is not gravel.
- Read offline: the source DEM's native resolution and resampling method (faceting candidate).
- Get decisions 1-5 and 11.
- Save: none. If decision 1 is taken, root edits the profile outside the editor and re-pins it.

**S1: Material rework** (one editor session, medium). Aviv's gate covers defects 1-3.
- **Read-only first, in the same session:**
  - fog, atmosphere and post-process actors;
  - a pick on Rimal's strips and slivers to tell mesh from Landscape;
  - a B0 baseline of 3+3 images under the §8 capture conditions.
- **a.** `MF_GeoCity_MacroColor`, inserted between `LandscapeLayerBlend_6` and BaseColor, so it covers all 4 layers continuously across seams.
  - The product of 3 WorldAligned `T_MacroVariation` octaves, starting near 4 m, 20 m and 500 m (I).
  - A hue lerp between `GeoCity_HueColorA` and `B`, driven by the low octave.
  - A far-colour lerp by `SharedDistanceAlpha × GeoCity_FarColorAmount`.
  - The output is clamped.
- **b.** Replace `Clamp_3`, `Clamp_20` and `Clamp_21` with parameters. The soil lerp goes toward a new `Ground_SoilAlbedo` and is albedo-only, with no soil normal lerp, to avoid the gouge chains.
- **c.** Per-role textures from S0, set through Child overrides. `Sand_01_Normal` and `Sand_02_Normal` must equal the profile copies (decision 1).
- **d.** Steep remap: the Sand_02 input colour = lerp(GroundColor, Sandstone, smoothstep(0.25, 0.45, Sand_02 weight)). This hides the collar rings at about 0.22. The new LayerSample's desc must not start with `GeoCity_LandscapeGrass` (LW:323).
- **e.** Per-layer roughness = lerp(R, R × `GeoCity_RoughMinFactor`, macro × luminance), wired into `LandscapeLayerBlend_8` (Epic's pattern). AO stays 1, because the packed-mask semantics are unverified (`Staging/AppearanceRepair_2026-10-03/GROUND_PAINTING_RESULT.md:27`).
- **f.** A PixelDepth normal fade to (0, 0, 1) over about 10-30 m, with a noise offset, after `LandscapeLayerBlend_7`.
- **g.** Set the Child `GeoCity_GrassCoverage` to 0.15 (decision 2).
- **Survives regeneration (I):** yes. `prepare()` recompiles and saves the master (LW:350-354), re-parents the Child to the base (:366) and keeps the overrides. Proof comes only at the next authorized ordinary run.
- **Save:** named only: Master, the new MFs, and the Shujaiya and Rimal Children. The base MI is saved only if a default must change, which it should not. No maps.
- **Images:** reopen Shujaiya fresh, then Rimal; 3 Lit images each.
- **Moved to S3:** the contact rim and LB_HEIGHT_BLEND. I: with binary weights they have little effect.

**S2: Conditional anti-tiling** (medium). Only if Aviv still sees repetition after S1.
- `MF_GeoCity_StochasticRotate`: a random 90° rotation per cell, with the normal XY rotated as well, applied to all 4 layers.
- Saves and close-out are the same as S1. The gate is defect 3.

**S3: Stage 1b, feathered paint plus height blend plus contact band** (large, gated).
- **Gate:** decision 6 plus the open system queue. M (AGENTS.md):
  - `ordinary_generation_authorized=false`;
  - the official Engine session is invalid and paused;
  - WORKFLOW_STATE is `failed_native_road_transaction`;
  - retirement of the second Shujaiya Landscape is still pending.
- **First measure:** the distance from each road probe to the road edges and to the pads.
- **HDA PermanentBank r019.** Label it distinctly, because the Iran HDA has its own r019/r020. Only the PythonModule `cook_surface_palette` changes (MOD:3817-3907):
  - an outward-only smoothstep feather: pads 2-4 m, roads 1.5-3 m, with ±1 m low-frequency edge noise;
  - `road''=road'·(1-pad')` and `open=1-pad'-road''`;
  - paint Steep from the pre-grading slope, or zero it in the collar mask.
  - The semantic placement volumes stay unchanged (MOD:3818-3821). The 4 names, the sum of 1 and the parts/instancer stay the same, so no Python change is needed (I).
- **Master changes:**
  - LB_HEIGHT_BLEND on the 4 layers, identical on `_6`, `_7`, `_8` and `_0`, with Height = albedo luminance (decision 7).
  - A contact band that peaks at fractional RoadBed/Pad weight: darken, shift toward the soil texture, raise roughness. Neutral defaults; enabled only in the Gaza Children.
- **Revision procedure:** follow the `update_r007.py` pattern (revisions/ backup, `installFile`, `addSection('PythonModule')`, `definition_receipt`). Re-import with a new reviewed copy of `import_appearance_hda.py`, because its :8 lease is CODEX_APPEARANCE_MANAGER. Save only the HDA uasset by name.
- **Regenerate:** an ordinary run of Shujaiya, then Rimal. `prepare()` must pass, and each area must end with exactly one Landscape.
- **Save:** the lifecycle's named saves, plus Master and the HDA uasset.
- **Images:** a fresh reopen, then 3 Lit images per area. The gate is defects 4-5, plus no regression on 1-3.

**S4: Stage 1c, contact geometry** (large). Only if Aviv's S3 verdict on defect 5 is negative.
- HDA r020:
  - skirt or plinth primitives 0.3-0.5 m below the pad datum, inside the existing `buildings` part;
  - side faces for sidewalks and roads, or a lower lift (MOD:5687-5690, :5766, :5806-5807).
- It must pass the BW gates: :303-311, :333-335, and :598 (`conflicting_support_cells==0`). The plinths need an existing native material.
- Regeneration and close-out are the same as S3.

## 4. Decisions for Aviv (recommended default, then the consequence)

1. **Normal blocker.** Default: after S0, root points both profiles' `surface_normal_overrides` at the chosen Sand_01/02 normals and re-pins them (`launch_editor.ps1:46` and the freeze receipt; currently Shujaiya 00877b7c, Rimal b1648e34).
   - Consequence: no Python change and no reseal.
   - Alternative: revert the Children to `T_Sand_0x_Normal_GeoCity`, which puts the old normals under the new albedos.
2. **Grass coverage.** Default: 0.15 from S1, which is what `prepare()` enforces anyway.
   - Consequence: grass is visible in every Stage 1 image. Changing the profile instead means a re-pin.
3. **Shared master, edited in place, neutral defaults, effects enabled only in Gaza.** Default: yes.
   - Consequence: Iran is unchanged by construction and no reseal is needed. Rollback means restoring the `.uasset` backups with the editor closed.
   - A dev copy would need an exception to the no-temporary-assets rule.
4. **Role textures.** Default: installed content only. If residency fails, any NeverStream copies are made by the owner Aviv names (the bank chat is the sole native writer, and NativeUnrealAssetSupply owns supply).
   - Consequence: new content is requested only if no distinct soil texture exists.
5. **Capture conditions.** Default: a transient, unsaved exposure lock, Lumen at High or above, compile and residency gates, and B0 recaptured under the same conditions.
   - Consequence: the images are comparable. Six extra captures.
6. **Stage 1b (S3).** Unfreeze PermanentBank for a palette-branch-only r019 and authorize ordinary regeneration of both areas. Default: approve in principle; run after the system queue clears.
   - Consequence: this is the only route to wider joins and to removing the rings.
7. **Height-blend source.** Default: albedo luminance.
   - Alternative: verify the packed-mask B channel first.
8. **Contact route.** Default: the S3 material band; S4 geometry only if needed; RVT deferred.
   - Consequence: RVT would need a `DefaultEngine.ini` reseal (seal 3cd33b15) and native material edits. A route that survives regeneration may later exist through HE `unreal_uproperty_*` on the Landscape output (`Plugins/HoudiniEngine/Source/HoudiniEngine/Private/HoudiniOutputTranslator.cpp:649-662`); array support is unverified.
9. **Geometry defects** (Rimal step walls and slivers, the faceted hill). Default: diagnose read-only in S0/S1, then decide.
   - Consequence: they stay visible after S1.
10. **Second Shujaiya Landscape.** Default: leave it to lifecycle retirement. No manual deletion and no per-actor edits.
11. **Operator, lease and cost.** Default: one operator chat per editor session, on the cheapest acceptable model, with no parallel agents. Aviv or root names the OWNER token and thread IDs. Stage 1 copies of `GP/native_capture*.py` are re-pinned.
12. **Review cadence.** Default: Aviv reviews after S1, S3 and S4; S2 only if needed.

## 5. Preservation and rules

- **Sealed runtime 3cd33b15** (`Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json`) stays unchanged: `init_unreal.py`, the 12 `Content/Python` modules, `DefaultEngine.ini`, `DefaultRoadBLD.ini`, `launch_editor.ps1` and `seal_runtime.py`.
- **Grass contract** (LW:321-344):
  - exactly 1 `LandscapeGrassOutput`;
  - exactly 4 `GeoCity_LandscapeGrass*` nodes, labelled Ground, Density, GroundDensity and Output;
  - the Ground sample is Sand_01;
  - the GrassInput maps `GeoCityGroundGrass` to `LG_GeoCity_PermittedGroundGrass`;
  - the master coverage default is 0.0.
- **Layer contract:**
  - Sand_01/Sand_02/Dirt_Path/Sand_Path = Ground/Steep/RoadBed/BuildingPad;
  - choices 17/18/16/20 (LW:18-21, :427);
  - weights sum to 1 ± 4/255, and probes are ≥0.8 (LW:124-190).
- **Parent chain:** Master → `MI_SurfaceBank_Natural` → Child.
- **Also preserved:**
  - the holds H0013, H0907, H0051 and H0958;
  - the declined palms;
  - the 87 unvalidated candidates;
  - the native originals (only the GeoCity copies are bound);
  - the source packages and catalog IDs.
- **One editor.**
  - Read the last line of `Staging/ModelBank/EDITOR_OWNER.txt` (now `OWNER=NONE`, 2026-10-05T09:55:17Z).
  - Inspect processes, the world and dirty packages.
  - Work under an actual-PID lease; never reuse a historical PID.
- **Saves:** named saves only. Never Save All or `save_assets([])`. No map save unless the lifecycle saves it or Aviv approves.
- **Backup** before each editor sub-step:
  - mirror the packages to `Stage1_Ground/Before_S<n>/Content/...`;
  - write a `BACKUP_MANIFEST.json` with the REV schema: `ready, created_utc, files[{file,sha256,backup}], preserved_files, sealed_files, new_asset_paths, pid, world, execution_thread_id, file_bindings`;
  - put receipts in `Stage1_Ground/S<n>/`.

## 6. Not in scope

- The sealed Python, `DefaultEngine.ini` and the launch scripts.
- RVT.
- Edits to native building and road materials, decals, and extra instancers or mesh parts.
- A 5th Landscape layer, or changes to palette indexes or layer names.
- RoadBLD Landscape flags, and flattening the Landscape under roads.
- Nanite Landscape, displacement and tessellation, and sculpting.
- Persistent changes to lighting, exposure or post-processing.
- Manual Landscape deletion, and per-actor Landscape edits.
- The Iran HDA and Iran's ground look.
- Save All, test maps, pilots, temporary assets, new generators and PCG.
- Linear.

## 7. Critical files and assets

- **Assets:**
  - Master, the base `MI_SurfaceBank_Natural`, and the Shujaiya and Rimal Children;
  - `/Game/StarterContent/Textures/T_MacroVariation`;
  - the `Textures/EpicResident2K/*` copies;
  - `/Game/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank.uasset`.
- **Code:** LW, BW and MOD, plus `.../GeoCity_city_v015_PermanentBank/definition_receipt.json` (r018, hda 61303c15, module e67b6e15).
- **Data:**
  - the 3 `AREA_PROFILE.json` files listed above;
  - `GP/CAMERAS_GazaShujaiya.json`, `GP/CAMERAS_GazaRimal.json` and `GP/native_capture_epic_resident.py`;
  - REV `BACKUP_MANIFEST.json` and REV `EPIC_RESIDENT_CONSUMER_verify_r030_fresh_reopen_PID18844.json`;
  - `Staging/AppearanceRepair_2026-10-03/NATIVE_HDA_IMPORT.json`;
  - the two `Stage1_Ground/*_r030.txt` traces.

## 8. Verification per sub-step

**Close-out for every editor sub-step:**
1. Backup.
2. Named save.
3. The dirty list must equal the expected list.
4. Fresh reopen of Shujaiya, then Rimal.
5. Captures under the conditions below.
6. Contract readback.
7. Receipts.

**Capture conditions:**
- the GP cameras, FOV 65, 1600x1000;
- VMI_LIT read back;
- zero pending shader compiles;
- texture residency settled (transient force-resident, recorded);
- Lumen active at High or above, with settle frames after each camera jump;
- a fixed, unsaved exposure, with the EV recorded.

**S0**
- The decisions are recorded.
- A texture shortlist JSON lists each texture's path, size and mean albedo.
- The DEM resolution is noted.

**S1**
- The graph-dump diff against r030 shows only the intended nodes and edges.
- The Grass and layer contracts read back correctly.
- The base MI hash is unchanged, and the new master parameters sit at their neutral defaults (Iran).
- The Child normals equal the profile copies, and coverage is 0.15.
- The maps are clean after the fresh reopen.
- Image proxies against B0 (I): a higher std-dev of block-mean luminance and of chroma at middle and wide distance, and a lower autocorrelation peak at a 1-4 m period at middle distance.
- Visual: at least two hue/value zones at middle and wide distance, and no blotches at close range.

**S2**
- The autocorrelation peak is lower than in S1.
- No cell-border seams show at close range.

**S3**
- `prepare()` and `verify_landscape()` pass, and there is exactly one Landscape per area.
- A transect shows a 1-3 m ramp across road and pad edges, and the probes are ≥0.8.
- Steep stays below the remap threshold on the collars.
- The BW gates pass (:303-337, :598).
- Visual: irregular blended edges, no rings, and a contact band at bases and curbs.

**S4**
- The gates pass, with `conflicting_support_cells==0` and the native instance count equal to the receipt.
- Visual: bases look grounded, and sidewalks do not float.

**Open items:**
- Which profile is loaded.
- The road-probe clearances.
- Whether the RoadBed footprint lines up with the RoadBLD meshes.
- Whether `r.VirtualTextures` is on by default in UE 5.8.
- The causes of the faceting and the slivers.
- `CURRENT_STATE.md:85` is stale: it says r017/bd62ec4d, but the live definition is r018/61303c15.

## Decisions recorded from Aviv (2026-10-05, via Claude Code question windows)

1. **Profile/normal mismatch:** Aviv did not pick a route; he answered that the real issue is not per-area settings but that the ground needs MANY colors/textures as options ("then everything will work well"). Manager applies the recommended default: point both profiles' `surface_normal_overrides` at the saved Epic normals and re-pin, no Python change. Aviv's intent is recorded as a requirement for S0/S1: build a rich palette (several albedo/color variants per layer plus macro color variation), not a single texture per layer.
2. **Shared master edit in place, effects off by default, full `.uasset` backups first:** APPROVED.
3. **Grass:** Aviv wants NO grass for now. Stage 1 does not call `prepare()`, so coverage stays 0.0 during ground work. OPEN for Stage 2: an ordinary run forces 0.15 via `prepare()`; a true "off" needs a profile value > 0 that is visually negligible or a code change (reseal). Decide before the clean run.
4. **Capture conditions (locked exposure, same cameras, not saved to the map):** APPROVED.

Pending decisions (not yet asked): role textures source (default: installed only), Stage 1b HDA palette-only unfreeze, height-blend source, contact route, Rimal/hill geometry diagnosis, second Shujaiya Landscape (default: lifecycle retires it), review cadence.

Execution gate: the bank chat's editor (PID 24804, task=modular_bank) is authorized by Aviv and holds the single writer slot; S1+ waits for its orderly release. S0 (offline) may run earlier only on Aviv's go.

## Research intake (Aviv, 2026-10-05): three pasted reports (Houdini↔UE5 integration; RVT/decal/PDO/WPO blending; auto landscape materials)

Confirms S1/S2 as designed: near/far double sampling (distance blend), multi-scale macro variation, UV-bombing/random rotation, height-based layer blending, Grass driven from the Ground sample.

Changes to Stage 1 (adopted):
- **Sampler limit:** adding near/far samples + macro textures to the 1015-node master will likely exceed the SM5 16-sampler limit (material falls back to gray). Every new/changed Texture Sample must use Sampler Source = Shared: Wrap (Shared: Clamp for non-tiling masks). Add a sampler-count check to the S1 graph diff.
- **Soft Steep transition without Houdini:** compute slope in the material (WorldAlignedBlend / dot(normal, up) with bias + sharpness) and combine with the Houdini Steep weight (LandscapeLayerSample as override). Gives a graded Ground↔Steep edge in S1; the binary RoadBed/BuildingPad edges still need S3.
- **Height blend earlier:** LB_HeightBlend is material-only; move it from S3 into S1 (same switch on all four blends; verify the Python pin/array write with readback, else do it in the editor UI and record it). Even with binary weights the edge follows texture height instead of a straight line.
- RVT caveat recorded: distance blending cannot be baked into an RVT (top-down capture); keep distance blend after any future RVT sample.

Later stages (not Stage 1):
- **Contact (defect 5):** RVT is the standard answer, but it needs "Enable Virtual Texture Support" in DefaultEngine.ini (a sealed support file → reseal) plus RVT sample nodes in the building/road materials (vendor originals must not be mutated → wrapper instances). Decals scattered from Houdini (dirt at bases, road edges) are the cheaper alternative. Decide at Stage 1b.
- PDO+DitherTemporalAA / DistanceToNearestSurface / WPO: mesh-side blending; touches building materials and costs Early-Z. Not before contact route is decided.
- Vegetation (Stage 3): the reports recommend Houdini rules → PCG scatter instead of per-tree unreal_instance points. Architectural question for Stage 3, not now.
- Nanite landscape tessellation (real pebble relief) and edit-layer output mode: need DefaultEngine.ini cvars → reseal. Later.

Original research texts are saved verbatim under `Research/` (01 Houdini-UE5 integration, 02 landscape/mesh blending with RVT and decals, 03 auto landscape materials).

- 2026-10-05 ~21:10Z capture decision: the manual exposure cvar lock (r.EyeAdaptation.MethodOverride=3, offset 0) produced a fully black PNG while a plain viewport capture of the same editor showed the normal sunlit scene; B0 and S1 captures therefore use exposure.mode=auto_recorded (same mode before/after, same cameras). Receipts mark EXPOSURE_NOT_LOCKED; comparability relies on identical auto-exposure conditions.

## 2026-10-06 ~00:40Z: v1 rejected, Codex review, v2a decision
- S1 v1 applied in memory (PID23156) and judged by Aviv: "no blending between colours, no fade between patches, repetition not solved". Discarded without saving (Operator/EXIT_PID23156.json; disk unchanged). Diagnosis: thresholded 37 m noise "patches" (PatchLo/Hi), plain-sampled MW variants, unmatched warm tints, FarSaturation 1.2; the live Sand_01 hash-grid anti-tiling chain was kept but the macro/soil chain was bypassed.
- Codex read-only review (S1v2/CodexReview/CODEX_DESIGN_REVIEW.md): full v2 (cell-sampling every albedo, height blends, 47-81 fetches) is overbuilt and not guaranteed to remove 2-4 m lattice repetition; recommended first revision = macro colour variation only (3 rotated macro-noise samples at 61/211/733 m, weights .45/.35/.20, rotations 17/53/89 deg, recentred; ValueAmount 0.07, HueGain 0.25-0.35, FarAmount 0, NormalFade 0.25-0.35 if any), keep weight blends, then Epic Texture_Bombing selectively (paired albedo+normal) where motifs remain; normals must follow albedo on Road/Pad.
- Manager decision: build and run v2a (macro colour only, 3 extra fetches) on the fresh editor PID16824; evaluate in BaseColor and Lit with camera movement; repetition handled in v2b (Texture_Bombing) only if still visible. Height blend deferred until feathered weights exist (Stage 1b/Houdini).

## 2026-10-06 ~01:30Z: Aviv chose Path B (Unreal auto-landscape material)
- After an unsaved preview of MW MTL_MWAM_Landscape_DesertExample on the Shujaiya Landscape (Operator/MWPreview_20261006/, reverted, editor closed without saving), Aviv decided: "use Unreal's system" -> Path B: project-owned MI parented to the MW auto-material becomes the Shujaiya ground material, with a small reviewed change to the sealed geocity_landscape_workflow.py (external material mode: skip Natural master/base/child enforcement, normal pins and Grass authoring when the profile says so), reseal with a ratification record, profile patch (landscape_material, landscape_grass.enabled=false), named save of the MI + map, fresh reopen, captures. Known trade-offs accepted for now: Houdini RoadBed/BuildingPad masks are ignored by the auto material; no Grass; Rimal follows later. v2a (macro colour on the Natural master) is shelved, files kept under S1v2/.
