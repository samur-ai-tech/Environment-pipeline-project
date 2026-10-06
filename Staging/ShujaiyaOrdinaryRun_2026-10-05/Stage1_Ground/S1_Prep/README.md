# S1_Prep: Stage 1 ground material rework (GazaShujaiya, then GazaRimal)

Status 2026-10-05: **PREPARED, NOT EXECUTED.** No backup set exists (`S1_Prep/Before/` is absent), there is no `receipts/` folder, and no editor step has run (MEASURED, ls). S1 cannot start until the blockers in section 7 are cleared.

Update 2026-10-05 ~20:25Z (offline P0 pass): items 7.1, 7.3, 7.4, 7.6 and 7.13 are cleared offline; 7.2 and 7.7 were cleared by the manager; 7.5 is closed by an ordering rule (no code change). New blockers 7.14 (15 MW `Func/*` files differ from VaultCache on disk) and 7.15 (spec baseline disk shas predate B2) and decision 7.16 (sealed launcher operator id) are open. See section 7.

**Labels:** M = MEASURED (from a file, hash or receipt), D = DOCUMENTED (official API or doc), I = INFERRED.

**Short names:** LW = `Content/Python/geocity_landscape_workflow.py`; EDIT = `s1_material_edit.py`; GP = `Staging/GroundPainting_2026-10-04`.

**Retained contract (S1 must keep all of this):**
- **Material chain.** The master path `/Game/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural` is fixed (LW:15-16). It feeds the base `MI_SurfaceBank_Natural`, which feeds the area children `MI_GeoCityGround`. Parent checks are at LW:222-224 and :416; the re-parent is at LW:366-369.
- **Layers.** Sand_01 = Ground, Sand_02 = Steep, Dirt_Path = RoadBed, Sand_Path = BuildingPad (LW:18-21).
- **Grass (LW:321-344):**
  - exactly 1 LandscapeGrassOutput;
  - 4 nodes whose desc starts with `GeoCity_LandscapeGrass`;
  - the Ground sample is Sand_01;
  - the master coverage default is 0.0.
- **Iran.** Iran binds the base MI directly. Every new effect is therefore neutral at the master default and turned on only in the two Gaza children.

## 1. Chosen design: defect → change

This is design D2 (`S1_MINIMAL_SAFE_SPEC.json`) plus root corrections 1-9, as implemented in EDIT.

1. **No colour variety.** Two extra ground textures, GroundB (MW SandA) and GroundC (MW SandC), plus an albedo-only soil (MW Dirt), are blended into Ground as patches. A 37 m noise from the R, G and B channels of MW Noise drives them, and each patch has its own tint and amount (EDIT:1230-1271).
2. **No colour variety.** `MF_GeoCity_MacroColor` adds hue zones between HueA and HueB, driven by a rotated far noise (311 m in Shujaiya, 233 m in Rimal). It also adds ±ValueAmount brightness variation from the near and far noise (EDIT:933-942).
3. **Pale and uniform at distance.** A far colour multiplies saturation by FarSaturation and value by FarValue. It is blended in by the existing `SharedDistanceAlpha` × FarAmount (EDIT:938-942).
4. **Pale, and repetition.** `MF_GeoCity_DistanceBlend` samples every new texture twice: near, and far at UV / FarScale (12). The two are lerped by distance (EDIT:926-930).
5. **Repetition.** The normal fades to flat with distance (NormalFade 0.7), and roughness varies by ±RoughVar with noise (EDIT:1335-1344). Random cell rotation is S2, not S1.
6. **Sharp join between Ground and Steep.** `MF_GeoCity_SlopeBlend` computes the Steep alpha as smoothstep(SteepLo..SteepHi) of a mix of the painted Steep weight and a 15-35° slope from VertexNormalWS.z (mixed by SlopeMix), plus noise jitter. SteepStones mixes the Pad (Stones) texture into Steep (EDIT:945-950, :1277-1286).
7. **Sharp joins on all edges.** Three new 4-layer LandscapeLayerBlend nodes use LB_HEIGHT_BLEND. The height is the luminance detail (near minus far) from `MF_GeoCity_HeightBlend`. HeightAmount 0 is identity (I) (EDIT:953-958, :1286-1318).
8. **RoadBed and BuildingPad ground layers** (the Landscape under and beside roads and under building pads; the RoadBLD road meshes and buildings are unchanged). These use existing child parameters (EDIT:245; `S1_ARGS_TEMPLATE.json`):
   - Dirt_Path → MW Dirt, tint 2.2/2.1/2.0, 4 m tile;
   - Sand_Path → MW Stones, tint 2.0/1.95/1.9, 3 m tile.
9. **No contact with buildings or roads: NOT fixed in S1.** The contact-band nodes exist and peak where the RoadBed/Pad weight is fractional, but every amount is 0. EDIT refuses non-zero values until root sets `contact_band_acknowledged` (correction 9, EDIT:672). Today's masks are binary at 1 m, so the real fix is S3/S4.
10. **MW Variation.** The Variation mask and normal (×1.5, an MW recipe) are wired in, but the amount stays 0 until `variation_reviewed` (correction 5, EDIT:675).
11. **Switch mechanism.** Three StaticSwitchParameter nodes named `GeoCity_S1_Enable` (default False) sit at BaseColor, Normal and Roughness. The False input is the untouched LandscapeLayerBlend_6, _7 and _8. The AO root (LandscapeLayerBlend_0) is untouched.
12. **Iran and the base MI.** Only the False permutation compiles for them. The base MI is never written. New amounts default to 0, tints to 1, and SteepLo/Hi to 0/0.001 (EDIT:189-242).
13. **New packages.** There are 5 new parameter-free functions: `.../Appearance_20261003/Functions/MF_GeoCity_{MacroNoise,DistanceBlend,MacroColor,SlopeBlend,HeightBlend}`. The master gains 157 nodes, 52 parameters and 12 new texture samples, all Shared:Wrap, with 0 new sampler states. M: the offline mock selftest was re-run on 2026-10-05 against EDIT sha `dfcd84a0` and returned `SELFTEST_PASSED_MOCK_ENGINE`; it ran again inside the expectations generator against the current EDIT `5c48daaf` with the same result (7.4).
14. **Nothing existing is edited.** No existing node, edge or property changes, and the Grass nodes, layer names and GrassOutput are untouched. Only the 3 root bindings move. New descs use the prefix `GeoCity_GroundS1_20261005:`, never `GeoCity_LandscapeGrass`.
15. **Caveat.** With the switch True, the current Gaza Sand_01 macro/soil chain is bypassed: LinearInterpolate_42, Clamp_21, Ground_MacroContrast and Ground_SoilBlendStrength. So "True at zero amounts" is **not** today's look, and every B0-vs-S1 comparison must say so (M: r031 dump; review r1).

## 2. Assets: taken and not taken

### Taken from MWLandscapeAutoMaterial: 11 textures

- They are bound only through the two Gaza children's overrides.
- The master gains 0 MW imports; its defaults reuse textures it already imports.
- MW files are read in place. They are never saved, copied into project paths or modified.
- `s1_backup.py` checks all 100 MW files against VaultCache.

| MW texture (`/Game/MWLandscapeAutoMaterial/Textures/...`) | S1 parameter | Use |
|---|---|---|
| `FX/TEX_MW_Noise_msk` (2048², 3 RGB noises) | GeoCity_S1_MacroNoise | noise for patches, hue, value, steep jitter and roughness |
| `Ground/TEX_MWAM_SandA_col` + `_nrm` (4096²) | GroundB_Albedo/Normal | Ground patch (amount 0.55 Shujaiya / 0.45 Rimal) |
| `Ground/TEX_MWAM_SandC_col` + `_nrm` | GroundC_Albedo/Normal | Ground patch (0.35 / 0.60) |
| `Ground/TEX_MWAM_Dirt_col` | Soil_Albedo, Dirt_Path_Albedo | soil patch (albedo only, 0.45 / 0.30); RoadBed |
| `Ground/TEX_MWAM_Dirt_nrm` | Dirt_Path_Normal | RoadBed |
| `Ground/TEX_MWAM_Stones_col` + `_nrm` | Sand_Path_Albedo/Normal | BuildingPad; also SteepStones 0.35 |
| `Extra/TEX_MWAM_Variation_msk` + `_nrm` | VariationMask/Normal | bound, amount 0 (pending review) |

**MW recipes rebuilt as project logic** (no MW function is referenced; `S1_MAXREUSE_EDIT_SPEC.json` mw_function_tiers):
- near/far double sampling, the `MF_MWAM_DefaultLayer` pattern;
- the variation ×1.5 multiply;
- depth fade, mapped to the existing `SharedDistanceAlpha`;
- the slope mask, as a VertexNormalWS.z smoothstep.

### Not taken from MW, with reasons

- **The 15 `MF_MWAM_*` functions.** Referencing them would add a vendor dependency to the shared master, and so to Iran. PID10460's MCP `get_material_info` already left all 15 dirty in memory (M: `AstraMWInventory/final_readonly_check.json`). Tier A (textures only) was chosen.
- **`MTL_MWAM_AutoMaterial_MASTER` and the `MTL_MWAM_Landscape_*` MIs as parent.** Incompatible: the sealed LW fixes the master path (:15-16, :222-224, :366-369, :416).
- **`LGT_MWAM_*` grass types, `Meshes/Plants` and `MTL_MWAM_PlantsGrass`.** Aviv wants no grass now. A second grass output would also break the rule of exactly 1 LandscapeGrassOutput (LW:321-344).
- **Rock col/nrm.** It is dark grey, and its fit as pale limestone is unverified (`MW_INVENTORY.md`, "Rock"). Steep keeps its current sandstone.
- **Grass and Snow ground textures.** Wrong biome for dry Gaza.
- **CoverRocks/CoverSnow materials and textures, and `SM_MWAM_StoneA-D`.** These are scatter props. They belong to a later props/vegetation stage, done through the bank chat, which is the sole native writer.
- **Background mountains, clouds, water normal, bake render targets, `BP_BakeLandscapeLayers`, `PM_MW_*` physical materials, Temp/ColorChecker and the 3 demo maps.** None is a ground-material input. No demo map was loaded.

### HighPoly_Tree_Model (9 files): not taken in S1

- `SM_HP_Tree` has 564,214 triangles, Nanite on, 2 materials, and was saved in UE 5.3.2 (M: `MW_HP_PackInventory/PACK_INVENTORY.json`).
- It is vegetation, not ground. It belongs to the vegetation stage (Stage 3), placed through the catalog and `unreal_instance` by the bank chat.
- S1 only checks it against VaultCache.

### Pegasus zip: nothing imported

The zip is `Downloads/projectfiles_pegasus_colormap.zip` (226,993,919 B, 31 entries). Reasons it is not imported (M: `pegasus_listing/PEGASUS_ZIP_LISTING.json`):
- Its UE assets were saved in UE 5.3.
- It lacks their `MI_Landscape` master and the `TA_Landscape_D/N/ORDp` texture arrays.
- `T_Landscape_D.tga` (2017²) is the colour map of Pegasus's own terrain, not Gaza.
- Its 4 HDAs (`heightfield_color_adjust`, `color_layers`, `occlusion_mask`, `texture_mask`) are Houdini SOPs. Using them means changing the PermanentBank HDA, which is S3: gated and upstream-frozen.
- It has no readme or licence.

`/Game/Pegasus` does not exist (M), and `s1_verify.py:96-97` treats it as a vendor prefix that is never saved. Pegasus's ideas (colour-zone adjust, camera fade, normal intensity) overlap MacroColor, the distance fade and NormalStrength (I; the S1 code does not reference Pegasus).

### Licence

- **MW:** no licence, readme or EULA was found in the project or VaultCache (M: `AstraMWInventory/MW_INVENTORY.md:482-486`). Entitlement is unverified, and Aviv must confirm the purchase.
- **HighPoly:** not checked.
- **Pegasus:** no terms in the zip.

## 3. Files (sha256 MEASURED 2026-10-05)

Full sha256 values of every script are in `S1_Prep/SCRIPT_PINS.json` (re-measured after the P0 pass).

| File | sha256 (first 8) | Runs |
|---|---|---|
| `s1_backup.py` | 9112608a (was 439a31f6; 7.13 exit-code change) | offline, with the editor closed |
| `s1_material_edit.py` | 5c48daaf (was dfcd84a0; docstring-only fix 7.6, same line numbers) | in-editor; modes inspect/apply/tune/save/child_save/verify |
| `s1_material_edit_offline.py` | 00cab7ac | offline: `selftest`, `expectations` |
| `s1_verify.py` | 2a93ed9e | in-editor, read-only; phases baseline/post_s1 |
| `s1_capture.py` | fe5156d4 | in-editor, phased; transient exposure lock |
| `graph_dump_tools.py` | bf93b72b | offline: facts/diff/uasset |
| `run_s1.py` | a1ab6205 (new, 7.3) | Windows Python, outside the editor: pinned runner |
| `s1_set_args.py` | 1f639da6 (new, 7.3) | in-editor via `run_s1.py`: sets/clears `GEOCITY_S1_ARGS` |
| `SCRIPT_PINS.json` | see 7.3 | pins of all 8 scripts above (flat `{name: sha256}`) |
| `S1_ARGS_TEMPLATE.json` / `S1_ARGS_TEMPLATE_TUNE_GazaRimal.json` / `S1_ROOT_ACTIVATION_TEMPLATE.json` | templates (updated in 7.6) | templates |
| `S1_EDIT_EXPECTATIONS_GazaShujaiya.json` | fdb8dba3 (new, 7.4) | the expectations for Session A/B |
| `S1_EDIT_EXPECTATIONS.json` | 0d6b7556 | **STALE, do not use** (two-area, old EDIT sha); kept as history |

Prepared run inputs (outside S1_Prep, placeholders start with `<FILL` and fail closed): `Stage1_Ground/Activation/S1_ROOT_ACTIVATION_{GazaShujaiya,GazaRimal}.json`; `Stage1_Ground/Args/S1_ARGS_GazaShujaiya_{inspect,apply,save}.json`, `S1_VERIFY_GazaShujaiya_baseline.json`, `S1_CAPTURE_GazaShujaiya_{B0,S1}.json`.

## 4. Operator run order

The task chain is: backup → fresh paused editor → edit → verify in the same process → named saves → quit → fresh editor → verify → capture both areas. The steps below are that chain in the order the scripts actually enforce it. Use **one area per editor session**: EDIT binds its scope to the open map (EDIT:29-31).

### P0. Root, before any editor

- Clear the open blockers in section 7 (now 7.14, 7.15, 7.16).
- Fill in and SHA-pin the activation documents and the args copies. Activation documents go under `Stage1_Ground`, never `S1_Prep`, and their file name must start with `S1_ROOT_ACTIVATION` (EDIT:378). Args files may go anywhere under `Stage1_Ground` (EDIT:2129). Prepared copies: `Stage1_Ground/Activation/` and `Stage1_Ground/Args/` (section 3).
- The expectations for the current EDIT bytes (5c48daaf) are already generated (7.4). If EDIT bytes or the apply `child_values` ever change, regenerate (the generator writes only new files directly under S1_Prep):
  `python -B s1_material_edit_offline.py expectations ..\Args\S1_ARGS_GazaShujaiya_apply.json S1_EDIT_EXPECTATIONS_GazaShujaiya_<new label>.json`

### 1. Backup (every UnrealEditor closed)

Use Windows Python, not MSYS: the own-PID tasklist check fails closed under MSYS (I). Run from `S1_Prep`. The ratification record is `RATIFICATION_B2.json` itself (7.1).

```
python -B s1_backup.py --plan --ratified-seal 258469e14df2ca2e5e2b0c6543bf42e29c1fcde3d1628f7d258a607ee6d03024 --ratification-record "C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\ShujaiyaOrdinaryRun_2026-10-05\Incident_01a10c77_2026-10-05\RATIFICATION_B2.json"
#   read-only; must exit 0 with would_refuse=false (it now exits 1 when would_refuse is true, 7.13)
python -B s1_backup.py --ratified-seal 258469e14df2ca2e5e2b0c6543bf42e29c1fcde3d1628f7d258a607ee6d03024 --ratification-record "C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\ShujaiyaOrdinaryRun_2026-10-05\Incident_01a10c77_2026-10-05\RATIFICATION_B2.json"
python -B s1_backup.py --verify Before\S1B_<UTC>     # must print INTACT
Get-FileHash -Algorithm SHA256 Before\S1B_<UTC>\BACKUP_MANIFEST.json   # -> backup_manifest_sha256 in the args
```

- Record `Before/S1B_<UTC>/BACKUP_MANIFEST.json` and its sha256.
- Take the backup **after** any profile re-pin. All 238 preserved pins are re-checked at apply (EDIT:745-768), so a later re-pin would block apply.

### 2. Session A: fresh paused editor on `L_GazaShujaiya_BankIntegration`

Start with the sealed launcher. Houdini cooking must be paused, autosave off, the HDA count as expected, and no Material/MI/MF editor open.

- a. Root writes a **read-only** lease line: `activation=STARTUP_INSPECTION_ONLY` plus the read-only scope.
- b. Run `s1_verify.py` with phase=`baseline`. It must come before the save (`s1_verify.py:340-341`).
- c. Run EDIT mode=`inspect`.
- d. Run the `s1_capture.py` B0 capture: begin, then prepare/wait/request/complete for each of the 3 shots, then end.
- e. Root writes the **authoring** lease line: `activation=<authoring> scope=GeoCity_GroundS1_20261005_material_edit`.
- f. Run EDIT mode=`apply`. It builds the graph and verifies it in the same process, and does **not** save. Its gates are:
  - the graph diff;
  - a compile with the switch forced True, then forced False (EDIT:1520-1534);
  - the G2 replay of LW:366-367;
  - the exact dirty set.
- g. Run the `s1_capture.py` S1 capture with `allowed_dirty_content` set to the 5 MFs, the master and the Shujaiya child. This is gate G1: the change must be visible and must not be default grey.
- h. Optional: EDIT mode=`tune` (phase a), at most 3 times per area (EDIT:1886), each followed by a capture.
- i. Aviv judges the images. Root then writes the visual-review receipt: `{pid, save_approved:true, areas, state_receipt_sha256, state_instances_sha256, captures, stage}`.
- j. Run EDIT mode=`save` in the same PID. **Named saves only**: the 5 MFs, the master and the Shujaiya child, via `save_packages(named, False)` (EDIT:1797). `dirty_after` must be empty.
- k. Quit the editor. Nothing may be dirty; if a save prompt appears, choose "Don't Save" and stop. Root releases the lease (`OWNER=NONE`).

#### Session A exact commands (PowerShell, Windows Python; `cd` into `S1_Prep` first)

Every `run_s1.py` call prints one JSON summary; exit 0 ok, 1 failed, 2 refused before sending, 3 HTTP timeout (NOT an abort: read `receipts/`, `*_ONCE*.json`, `CAPTURE_<label>.json`). OWNER `GEOCITY_GROUND_S1` and operator `cc37d4d2-…` are the proposals in the prepared activation; change them everywhere together if root renames.

1. Backup: section 4.1 (after 7.14 is fixed).
2. Launch (sealed launcher; needs last lease `OWNER=NONE` and no UnrealEditor process):
   `powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\SystemCompletion_2026-10-04\launch_editor.ps1" -AreaMap /Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration -ExpectedMapSha256 4efebdfb0bf6c36b699a577b33faa64d28afbec0488115e6596883af518940d0 -ExpectedManifestSha256 258469e14df2ca2e5e2b0c6543bf42e29c1fcde3d1628f7d258a607ee6d03024 -ExpectedProfileSha256 1328d5bbdf0005bbb5b4b7ede85269c0d203beca361e193e0c9fd0edb0478b39 -ManagerThreadId cc37d4d2-3d62-4f53-b689-28432b5527ae -OperatorThreadId 01a10c77-46ba-7001-a657-5014f6205d3a`
   (operator id: see 7.16). It writes `LAUNCH_STATE_PID<pid>.json` and a lease line `OWNER=CODEX_MANAGED_SYSTEMS_STARTUP … activation=AWAITING_MANAGER_ACTUAL_PID`. Wait until the map is loaded.
   Smoke test of the runner channel (changes nothing): `python -B run_s1.py --env-status` must exit 0 with `value: null`. Any other result: stop before step 4.
3. Root: copy `Stage1_Ground\Activation\S1_ROOT_ACTIVATION_GazaShujaiya.json` to `…\S1_ROOT_ACTIVATION_GazaShujaiya_PID<pid>.json`, set `assigned_editor_PID` to the integer PID, hash it; fill every `<FILL` in `Args\S1_ARGS_GazaShujaiya_inspect.json`, `S1_CAPTURE_GazaShujaiya_B0.json` (`expected_pid` as an integer); append the READ-ONLY lease line:
   `<utc> OWNER=GEOCITY_GROUND_S1 manager_thread_id=cc37d4d2-3d62-4f53-b689-28432b5527ae operator_thread_id=cc37d4d2-3d62-4f53-b689-28432b5527ae assigned_editor_PID=<pid> map=/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration activation=STARTUP_INSPECTION_ONLY scope=GeoCity_GroundS1_20261005_readonly`
4. Baseline verify: `python -B run_s1.py s1_verify.py ..\Args\S1_VERIFY_GazaShujaiya_baseline.json` → `receipts\VERIFY_s1_shuj_baseline_r001_<pid>.json`, status `BASELINE_VERIFIED_READ_ONLY` (expect `disk_matches_spec_baseline` to fail until 7.15 is decided).
5. Inspect: `python -B run_s1.py s1_material_edit.py ..\Args\S1_ARGS_GazaShujaiya_inspect.json` → `receipts\S1_INSPECT_s1_shuj_r001_inspect_PID<pid>.json` + `GRAPH_BEFORE_<pid>.json`.
6. B0 capture (`$c='..\Args\S1_CAPTURE_GazaShujaiya_B0.json'`):
   `python -B run_s1.py s1_capture.py $c`; then for `$i` in 0, 1, 2: `python -B run_s1.py s1_capture.py $c --phase prepare --index $i`; `Start-Sleep 10` (settle ≥ min_settle_seconds 8); `python -B run_s1.py s1_capture.py $c --phase request --index $i`; `Start-Sleep 5`; `python -B run_s1.py s1_capture.py $c --phase complete --index $i` (repeat complete while PENDING). Finish with `python -B run_s1.py s1_capture.py $c --phase end`. Never loop `request` on `STREAMER_VIEW_NOT_AT_CAMERA`.
7. Root: append the AUTHORING lease line (same as 3 but `activation=GROUND_S1_AUTHORING scope=GeoCity_GroundS1_20261005_material_edit`); fill `Args\S1_ARGS_GazaShujaiya_apply.json` (activation copy + sha, PID, backup manifest + sha, inspect receipt + sha); the operator sets `operator_preconditions.no_asset_editors_open_on_s1_assets` to true only after checking that no Material/MI/MF editor is open.
8. Apply: `python -B run_s1.py s1_material_edit.py ..\Args\S1_ARGS_GazaShujaiya_apply.json` → `receipts\S1_APPLY_s1_shuj_r001_apply_PID<pid>.json` status `APPLIED_VERIFIED_NO_SAVE` (no save).
9. S1 capture: as step 6 with `$c='..\Args\S1_CAPTURE_GazaShujaiya_S1.json'` (fill `expected_pid`; `allowed_dirty_content` = 5 MFs + master + Shujaiya child).
10. Optional tune phase a: no args file is prepared; copy the apply args, set `mode=tune`, a new label, `apply_receipt`(+sha) and `state_receipt`(+sha).
11. Aviv judges the images; root writes the visual review receipt under `Stage1_Ground` and fills `Args\S1_ARGS_GazaShujaiya_save.json`.
12. Save: `python -B run_s1.py s1_material_edit.py ..\Args\S1_ARGS_GazaShujaiya_save.json` → `receipts\S1_SAVE_s1_shuj_r001_save_PID<pid>.json` status `SAVED_NAMED_ONLY`, `dirty_after` empty.
13. Quit: check nothing is dirty (e.g. `python -B ..\..\Operator\copilot_client.py ..\..\Operator\probe_state.py`), close the editor (File > Exit; on a save prompt choose "Don't Save" and stop); `python -B run_s1.py --env-status` beforehand should show `value: null`. Root appends the `OWNER=NONE` line.

### 3. Session B: fresh editor, Shujaiya, read-only lease

- Run EDIT mode=`verify`. The PID must differ from the apply/save PID.
- Run `s1_verify.py` phase=`post_s1`. This must run **before** the Rimal `child_save` (see 7.5).
- Run the `s1_capture.py` S1_fresh capture: 3 Lit shots.
- Quit.

### 4. Session C: fresh editor on `L_GazaRimal_BankIntegration`

This session needs a new activation whose `modes` include `tune`, `child_save` and `verify` (see 7.6).
- Take the B0 capture.
- Run EDIT mode=`tune` (phase b), passing the apply, save and state receipts. This turns the switch on for the Rimal child.
- Capture; root writes the review receipt.
- Run EDIT mode=`child_save`. It saves only the Rimal child (EDIT:2033).
- Quit.

### 5. Session D: fresh editor, Rimal

- Run EDIT mode=`verify` with `child_save_receipts`.
- Take the S1_fresh capture.
- Quit, then release the lease.

### Rollback (editor closed, root decision)

Copy `Before/S1B_*/Content/...` back with `shutil.copyfile`. Do not use `copy2`: it copies the read-only flag. The 5 new MF packages are listed in `new_asset_paths`; removing them is root's decision, because the scripts never clean up.

## 5. Invocation and args examples

### Runner (`run_s1.py`, 7.3)

- Channel (M): the UnrealCopilot MCP endpoint `http://127.0.0.1:19840/mcp`, tool `run_unreal_skill` with inline `python` + `args`. This is how the ground chat ran `native_capture.py` (GP `LAUNCH_PID*.json` → `ARGS_capture_*.json` → `CAPTURE_*.json`, through GP/copilot_call.py) and how the manager closed PID10460 (`Operator/copilot_client.py`). The plugin execs the text with an `ARGS` global, no `__file__`, on the game thread through a FIFO queue (`Plugins/UnrealCopilot/Content/Python/unreal_copilot/skills/runner.py:98-107, :221-236`; `execution.py:58-92`). It is not a launcher startup script, so a runner (not a command line) is the right tool.
- `run_s1.py` refuses (exit 2, nothing sent) unless itself, `s1_set_args.py` and the target match `SCRIPT_PINS.json`, the target is one of EDIT / `s1_verify.py` / `s1_capture.py`, and the args file is a `.json` under `Stage1_Ground`. It reads the pinned bytes once and sends exactly those (newlines normalised as `read_text` does in GP/copilot_call.py).
- HTTP wait per call: `--timeout` (default 1800 s). **A runner timeout is not an abort**: read `receipts/` and the `*_ONCE*.json` latches.
- Not executed offline (it needs a live editor); only `py_compile` (M).

### EDIT

EDIT reads only `os.environ['GEOCITY_S1_ARGS']` inside the editor. If it is unset, the script does nothing (EDIT:2123-2126).

```
python -B run_s1.py s1_material_edit.py <abs or relative Stage1_Ground\...\args.json>
#  1) s1_set_args.py {action:set, path, sha256}  (refuses if the variable is already set)
#  2) the EDIT file text (EDIT runs the mode named in the args)
#  3) s1_set_args.py {action:clear}  (always; FIFO order puts it after EDIT even after a timeout)
python -B run_s1.py --env-status     # read the variable;  --clear-env  pops a stale value
```

The EDIT args must name `executed_script_file` = the absolute `S1_Prep/s1_material_edit.py` (inline exec has no `__file__`, EDIT:443-449) and `script_sha256` = its pin; the runner checks both before sending.

Example apply args. The full value sets are in `S1_ARGS_TEMPLATE.json`; the Rimal tune values are in `S1_ARGS_TEMPLATE_TUNE_GazaRimal.json`.

```json
{"schema": "environmentpipeline.s1_material_edit.args.v2", "mode": "apply", "label": "s1_r001_apply",
 "root_activation": "<abs>/Stage1_Ground/S1_ROOT_ACTIVATION_r001.json", "root_activation_sha256": "<64hex>",
 "expected_pid": 12345, "script_sha256": "<sha of reviewed s1_material_edit.py>",
 "executed_script_file": "<abs>/Stage1_Ground/S1_Prep/s1_material_edit.py",
 "operator_preconditions": {"no_asset_editors_open_on_s1_assets": true},
 "backup_manifest": "<abs>/S1_Prep/Before/S1B_<UTC>/BACKUP_MANIFEST.json", "backup_manifest_sha256": "<64hex>",
 "inspect_receipt": "<abs>/S1_Prep/receipts/S1_INSPECT_s1_r001_inspect_PID12345.json", "inspect_receipt_sha256": "<64hex>",
 "contact_band_acknowledged": false, "variation_reviewed": false,
 "areas": ["GazaShujaiya"], "grass_coverage": {"GazaShujaiya": 0.0},
 "child_values": {"GazaShujaiya": {"textures": {"...": "..."}, "vectors": {"...": []}, "scalars": {"...": 0.0}}}}
```

### Activation and lease line

The activation follows `S1_ROOT_ACTIVATION_TEMPLATE.json`. The last line of `Staging/ModelBank/EDITOR_OWNER.txt` must match it (EDIT:391-436):

```
OWNER=<S1 owner> manager_thread_id=<id> operator_thread_id=<id> assigned_editor_PID=<pid> map=/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration activation=<authoring> scope=GeoCity_GroundS1_20261005_material_edit
```

### s1_verify.py

ARGS go through the runner (`s1_verify.py:21-75`). It needs a lease with `activation=STARTUP_INSPECTION_ONLY` (:122, :496-499).

```json
{"label": "s1_post_shujaiya", "phase": "post_s1", "lease_owner": "<S1 owner>", "operator_thread_id": "<id>",
 "expectations": "<abs regenerated S1_EDIT_EXPECTATIONS_*.json>", "expectations_sha256": "<64hex>",
 "baseline_receipt": "<abs>/receipts/VERIFY_<label>_<pid>.json", "baseline_receipt_sha256": "<64hex>",
 "save_receipt": "<abs>/receipts/S1_SAVE_<label>_PID<pid>.json", "save_receipt_sha256": "<64hex>",
 "expected_grass_coverage": {"GazaShujaiya": 0.0},
 "accepted_failures": {},   # exact-text waivers only; none for profile_normal_pins:GazaRimal (7.7); see 7.15
 "verifier_file": "<abs>/S1_Prep/s1_verify.py", "verifier_sha256": "<64hex>"}
```

### s1_capture.py

See `s1_capture.py:128-130` and :383-417.
- For the B0 begin, use `allowed_dirty_content` = [].
- Each later phase sends `{"mode": "prepare|request|complete", "expected_pid", "label", "index"}`, and the run finishes with `{"mode": "end"}`. With `run_s1.py` these are derived from the begin file: `run_s1.py s1_capture.py <begin.json> --phase prepare --index 0` … `--phase end [--cancel]`. Begin files must not contain extra keys such as `_note` (validate_begin refuses unknown keys).

```json
{"mode": "begin", "expected_pid": 12345, "owner": "<S1 owner>", "operator_thread_id": "<id>",
 "area": "GazaShujaiya", "label": "GazaShujaiya_S1_B0",
 "camera_file_sha256": "9cd59936201f2e1a4825eb49dbff87aff7ea468a5ebc183d6303e658f28956c0",
 "shots": ["close", "middle", "wide"], "viewmode": "LIT",
 "exposure": {"mode": "manual_cvar", "exposure_offset": 0.0},
 "residency": {"mode": "force_bound_textures", "seconds": 60.0},
 "allowed_dirty_content": []}
```

The Rimal camera file sha256 is `2c430dc3a2d507be84a8aba641eb6ed56f180d9a3f094a3098843a1d93eedc36` (M). Images are 1600x1000 at FOV 65 from the GP cameras.

## 6. STOP conditions

On any of these, nothing is saved. If anything has already been changed in memory, close the editor with **"Don't Save"** and root reviews.

- **Backup refuses.** Causes:
  - an UnrealEditor process is running;
  - the seal manifest ≠ 3cd33b15 and there is no ratification;
  - a sealed file ≠ its pin;
  - any MW or HighPoly file ≠ VaultCache;
  - a pin is missing;
  - any `MF_GeoCity_*` is already on disk.
- **Guard fails.** Causes:
  - the lease OWNER, thread, PID or map ≠ the activation, or the owner is a foreign one (EDIT:107);
  - Houdini cooking is not paused, or autosave is on;
  - the HDA count ≠ expected, or HDA auto-cook/auto-bake is on;
  - a Landscape is not bound to the area child.
- **Baseline fails** (EDIT:136):
  - node count ≠ 1015;
  - graph sha ≠ `605c55d0…`;
  - reachability ≠ 631/241;
  - root Layer pins ≠ 207;
  - any package is dirty at the start.
- **Anchors, Grass or consumers fail:**
  - anchors are not unique;
  - the Grass contract fails, before or after;
  - master or base MI has consumers that are not pinned.
- **Probe or diff fails:**
  - the probe dirties a map;
  - the G2 readback differs;
  - an existing node or edge changed;
  - an added node is outside the prefix or canvas;
  - a sampler is not Shared:Wrap;
  - a runtime pin-name assert fails (switch True/False, `Height <layer>`, FunctionOutput, VertexNormalWS).
- **Compile fails.**
  - `RecompileMaterial` returns a non-empty list with the switch forced True or forced False.
  - The log scan hits `Failed to compile Material`, `Default Material will be used` or `: Error:` (EDIT:119).
- **Dirty set is wrong.** It must be exactly the 5 MFs, the master and the open area's child. A dirty map, base MI, Grass type, vendor package or Cook package means stop.
- **G1 fails.** There is no visible change versus B0, or the ground shows default grey/checker. Never re-assign `landscape_material`: it dirties the map.
- **G5 fails.** The MW 4K textures are not at full resolution in the close shot. Escalate to the NeverStream-copy decision.
- **Capture fails.**
  - `STREAMER_VIEW_NOT_AT_CAMERA` cannot be fixed by retrying, so do not loop.
  - The exposure does not read back.
- **Save is refused:**
  - the review receipt is missing or mismatched;
  - a backup copy or pin changed;
  - `dirty_after` is not empty.
- **Fresh verify fails:**
  - any check is FAIL or NOT_RUN;
  - the base MI hash changed;
  - a map is dirty after reopen;
  - Iran statistics ≠ baseline.
- **Tune budget is used up** (3 per area). More tuning needs a new root decision.
- **Never:** `prepare()`, `verify_landscape()`, Save All, `save_assets([])`, saves of the base MI, Grass type, maps or vendor packages, the MCP `get_material_info` tool, or edits to existing nodes.

## 7. Open issues (for root)

State after the offline P0 pass of 2026-10-05 (~20:20Z measurements). Open now: **7.14 (blocker), 7.15 (blocker for a passing baseline), 7.16 (decision)**, plus the standing 7.8-7.12.

1. **Seal ratification: CLEARED.**
   - The manager ratified `258469e1` as baseline B2 (`Incident_01a10c77_2026-10-05/RATIFICATION_B2.json`).
   - `s1_backup.py` expects no schema: `make_seal_override` only needs a file under `Staging` whose text contains the exact 64-hex sha (s1_backup.py:389-405). RATIFICATION_B2.json satisfies that, so no adapter record was written.
   - M: `--plan` with `--ratified-seal 258469e1… --ratification-record <abs RATIFICATION_B2.json>` gives `seal.accepted_by = ratification_record`, `drift_vs_manifest = []`, record sha `c97079b8…`. The REV delta (`geocity_roadbld_props.py` bf59bf96 → 2bf41ec3) is only a warning. The exact invocation is in section 4.1.
   - Do not edit RATIFICATION_B2.json from now on: the backup manifest records its sha.
2. **PID10460: CLEARED by the manager.**
   - M: `../../Operator/EXIT_PID10460.json` (20:02:03Z): 0 shutdown saves, 6 non-MW dirty packages discarded.
   - M: the last lease line is `OWNER=NONE` (20:02:03Z), and tasklist at 20:20Z shows no UnrealEditor.
   - However, the 15 MW files were already modified on disk earlier (see 7.14).
3. **Runner: CLEARED offline.**
   - New files: `run_s1.py`, `s1_set_args.py` and `SCRIPT_PINS.json` (sections 3 and 5).
   - Only `py_compile` was run. Its first live use is Session A.
4. **Expectations: CLEARED offline.**
   - Args: `Stage1_Ground/Args/S1_ARGS_GazaShujaiya_apply.json`, made from the template. It is one-area, uses `BACKUP_MANIFEST.json`, and marks placeholders `<FILL…>`.
   - Command: `python -B s1_material_edit_offline.py expectations ..\Args\S1_ARGS_GazaShujaiya_apply.json S1_EDIT_EXPECTATIONS_GazaShujaiya.json`.
   - Result: sha `fdb8dba3…`, `generated_by.target_sha256` = EDIT `5c48daaf`, 52 parameters, 157 added nodes, 12 new samples. The selftest inside the generator passed.
   - Offline replica of s1_verify :634-635, :659-660, :366-369 and `plan_mismatches`: `exp_areas = ['GazaShujaiya']`, `children` lists both areas, and the scope after a Shujaiya save = apply plans = exp_areas = `['GazaShujaiya']`. 0 plan mismatches. (I: this is a replica, not the verifier itself.)
   - The old `S1_EDIT_EXPECTATIONS.json` is stale; do not use it.
   - Rule: inspect and apply args keep identical `areas`, `child_values`, `grass_coverage`, `contact_band_acknowledged` and `variation_reviewed`. Changing any of them means regenerating the expectations.
5. **`s1_verify.py` child_save support: CLOSED BY AN ORDERING RULE (no code change).**
   - A fix limited to `named_save_boundary` would not help. After the Rimal `child_save`, a Shujaiya-scope `post_s1` also fails two other never-waive checks:
     - `effective_values_off_base_on_children`: an out-of-scope child must have the switch False and the master defaults (:1240-1246);
     - `instances_unchanged_outside_s1` (:1273-1310).
   - Real support would need two-area expectations, scope taken from child_save receipts, plan binding to tune receipts (:366-369) and a Rimal baseline taken before the master save (:325, :340-341). That is not small.
   - Rule: Session B (Shujaiya `post_s1`) runs **before** Session C (Rimal `child_save`).
   - Rimal is verified by EDIT `verify` with `child_save_receipts` (EDIT:2064-2120) plus the S1_fresh capture.
   - Any `s1_verify` `post_s1` run after the Rimal child_save fails by design.
6. **Templates and activations: CLEARED.**
   - `S1_ROOT_ACTIVATION_TEMPLATE.json`: the note now states the `S1_ROOT_ACTIVATION` name prefix and the one-PID-per-activation rule, and adds `_modes_GazaRimal = [tune, child_save, verify]`.
   - Concrete activations, with manager `cc37d4d2-3d62-4f53-b689-28432b5527ae` and a PID placeholder:
     - `Stage1_Ground/Activation/S1_ROOT_ACTIVATION_GazaShujaiya.json`: modes inspect, apply, tune, save, verify;
     - `Stage1_Ground/Activation/S1_ROOT_ACTIVATION_GazaRimal.json`: modes tune, child_save, verify.
   - They are named `S1_ROOT_ACTIVATION_*`, not `ACTIVATION_S1_*`, because EDIT:378 refuses any other prefix.
   - One activation binds one PID (EDIT:384). Root makes a PID-filled copy per session, and the copy's sha goes into the args.
   - OWNER `GEOCITY_GROUND_S1`, operator id `cc37d4d2…`, `authoring_activations = [GROUND_S1_AUTHORING]` and the read-only pair `[STARTUP_INSPECTION_ONLY, GeoCity_GroundS1_20261005_readonly]` are proposals; root may rename them consistently.
   - `S1_ARGS_TEMPLATE*.json` now use the `BACKUP_MANIFEST.json` path, and `executed_script_file` is the absolute EDIT path (required with the runner).
   - EDIT docstring (:77-81, :731-732) now says the backup copies the Grass type and maps. The change is docstring-only and line numbers are unchanged.
7. **Profile normal pins: CLEARED by the manager.**
   - M: `../../Incident_01a10c77_2026-10-05/RIMAL_PROFILE_REPIN_20261005T195927Z.json`. The Rimal profile went e136df32 → 8711cace, and the Sand_01/02 copies are now EpicResident2K.
   - RATIFICATION_B2's `rimal_profile` sha is therefore superseded.
   - Do not add a `profile_normal_pins:GazaRimal` waiver: an unmatched waiver fails `waivers_matched`.
8. **Grass: ROOT DECISION (reported, unchanged).** M:
   - Profiles: Shujaiya `landscape_grass` enabled, coverage **0.15**, density 12; Rimal enabled, coverage **0.15**, density 12.
   - S1 args: Shujaiya `grass_coverage {GazaShujaiya: 0.0}`; Rimal tune template `{GazaRimal: 0.0}` (its note says r031 measured Rimal at 0.0). EDIT accepts only 0.0 (EDIT:676-679).
   - The next ordinary `prepare()` writes 0.15 back (LW:371-382).
   - s1_verify feeds the coverage comparison into the never-waive `effective_values_off_base_on_children`. So the baseline args omit `expected_grass_coverage` (the Shujaiya child is 0.15 now; I), and `post_s1` must pass `{GazaShujaiya: 0.0}`.
   - Decide before Stage 2.
9. **Not yet proven at runtime:**
   - that the static switch reaches the Landscape component MICs (G1);
   - the LLB height math, so "identity" is I;
   - what RecompileMaterial covers (D: `MaterialEditingLibrary.h:262-267`; the forced-True route is I);
   - Iran-safe statistics.
   The new height LLBs carry only the 4 active layers, while the old ones carry 69. That is fine where the weights of those 4 sum to 1 (LW:124-190); I.
10. **Texture residency.**
    - The MW textures are streamed 4K originals.
    - Captures force them resident only temporarily, which counts as a diagnostic.
    - Acceptance may need owned NeverStream copies (decision 4; owner: bank chat / NativeUnrealAssetSupply).
11. **Not fixed by S1:**
    - contact with buildings and roads (defect 5);
    - the binary RoadBed/Pad edges, which need S3 (PermanentBank r019, gated);
    - Rimal's strips and slivers and the faceted hill (geometry).
    That S1 survives regeneration is inferred only; it is proven only at the next authorized ordinary run.
12. **Licensing.** MW entitlement is unverified, and the Pegasus zip has no terms. Aviv must confirm both.
13. **`--plan` exit code: CLEARED.** `main()` now returns 1 when `would_refuse` is true (s1_backup.py:1236). M: the 20:20Z `--plan` run exited 1.
14. **NEW BLOCKER: 15 MW `Func/*` packages on disk differ from VaultCache.**
    - M (`--plan`, 20:20Z): all 14 `Content/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_*.uasset` files plus `MW_MWAM_Water.uasset` differ. Their mtimes are 18:42:19-20Z, one minute before the 18:43:23Z GEOCITY_MENU lease line. Their sizes differ from the vault (e.g. CombineNormal 113,782 vs 113,678 B).
    - Who saved them is INFERRED: PID10460, the only editor then. This is the case 7.2 warned about.
    - The other 85 MW files and all 9 HighPoly files match the vault.
    - The backup refuses until they match. S1 never references MW functions.
    - Fix (root decision, editor closed): first preserve the 15 current files and their sha256 (for example under `Incident_01a10c77_2026-10-05/`). Then copy the originals back from `C:/ProgramData/Epic/EpicGamesLauncher/VaultCache/MWLandsc0bb389159dceV3/data/Content/MWLandscapeAutoMaterial/Materials/MASTER/Func/` with `shutil.copyfile` (not `copy2`).
    - Acceptance: re-run `--plan`; it must show MWLandscapeAutoMaterial identical 100/100 and exit 0.
    - Not done here: `Content/` is outside this worker's write scope.
15. **NEW: the spec baseline disk shas predate B2.**
    - M: `S1_MINIMAL_SAFE_SPEC.json` `baseline_expectations.disk_sha256`, which is copied into the expectations, has master 78b0f7cd and Shujaiya child 8c54b7e3. On disk now: master 70f82e50 and child 8fb548f8, both saved at 18:43Z and both equal to RATIFICATION_B2. Base MI 27b379f4 and Rimal child 99ad6bb8 match.
    - Effect 1: s1_verify baseline `disk_matches_spec_baseline` will FAIL. It is waivable (not never-waive).
    - Effect 2: the backup reports `ready_for_s1=false`; this is only a warning.
    - Effect 3: EDIT inspect gates on the graph digest (605c55d0, 1015 nodes), not on the file sha. Whether that gate passes is unknown until inspect runs. (I: `prepare()` re-saves the master and child, LW:350-353 and :382, and may leave the graph unchanged.)
    - The checks next to it are tied to pre-B2 references and are **never-waive**: `old_graph_identity` and `graph_snapshot` use the r031 graph dump; `iran_statistics_equal` uses `baseline_expectations.master_and_children_preview_stats_PID10460`.
    - Root option (a), valid only if `old_graph_identity`, `graph_snapshot` and `iran_statistics_equal` all PASS in the baseline **and** EDIT inspect's graph-digest gate passes: accept with `"accepted_failures": {"disk_matches_spec_baseline": "Disk differs from spec baseline: re-baseline (graph digest decides) before S1"}`. The text must be exact, and post_s1 then carries no such waiver.
    - Option (b): if any of those fails, a spec-only disk-sha edit is not enough. Root needs an in-editor re-baseline of the graph, the statistics and the disk values, then regenerated expectations.
16. **DECISION: sealed launcher identities.**
    - `launch_editor.ps1` (sealed) requires `-ManagerThreadId` = the `ManagedSystemsAstra_2026-10-04/ASSIGNMENTS.json` `manager_thread_id`. M now: `cc37d4d2…`, updated by the manager.
    - It also requires `-OperatorThreadId` = that file's task4 `thread_id`. M: `01a10c77-46ba-7001-a657-5014f6205d3a`. Any other operator id takes the bank path and throws.
    - So Session A launches with `-OperatorThreadId 01a10c77-…`, unless root updates task4's thread_id.
    - The launcher's own lease line is not the S1 lease. Root's S1 lines (operator `cc37d4d2…` in the prepared activation) follow it, so the two operator ids may differ.
    - `expected_hda_count = 1` in the activations and baseline args is INFERRED from GP receipts (`len(hdas)==1`). The guard fails closed if it is wrong.
