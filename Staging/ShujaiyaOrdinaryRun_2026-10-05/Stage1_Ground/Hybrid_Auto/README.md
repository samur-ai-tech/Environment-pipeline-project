> HISTORICAL (2026-10-19): this file is kept as history. Current decisions: Docs/GOVERNANCE_RECORD.md. Closure index: Docs/CLOSURE_INDEX.md.

# Hybrid ground for GazaShujaiya: runbook

The plan is `PLAN_HYBRID.md`; Aviv's choices are in `DECISIONS.json`. Nothing here has been executed in Unreal. All tooling was prepared offline on 2026-10-06.

Labels: **M** = measured, **D** = read from source, **I** = inferred.

## Files

| File | Role |
|---|---|
| `hybrid_profile_patch.py` | Offline profile edit with backups and rollback. |
| `hybrid_build_master.py` | In-editor. `inspect` / `build` of `M_GeoCityAuto`. No save. |
| `hybrid_build_master_offline.py` | Offline. Subcommands: `selftest`, `expectations`, `staticscan`, `argscheck`. |
| `HYBRID_EDIT_EXPECTATIONS.json` | The 56 planned nodes, edges and parameters for both texture sets. It is bound to the build script's sha. |
| `hybrid_assign_and_save.py` | In-editor. `inspect` / `apply` / `save` of `MI_GeoCityGround_Auto`. |
| `hybrid_verify_fresh.py` | In-editor, fresh PID, read-only. Runs `verify`; use `post_regeneration` after the clean run. |
| `Args/HYBRID_ARGS_*.json` | Argument templates. Only `<FILL ...>` values change: PID, receipt paths/shas, profile sha. |
| `SCRIPT_PINS.json` | The sha256 of every script. `argscheck` proves that the Args and pins match the files. |

Every in-editor script follows the same rules:
- It runs via `Operator/copilot_client.py` (inline exec, ARGS in, RESULT out).
- It checks its own bytes and code signature against `script_file` / `script_sha256`.
- It checks the lease, PID, map, sole editor, paused Houdini Engine, HDA auto cook/bake off, autosave off, and that exactly one Landscape exists.
- It writes one exclusive receipt under `receipts/`.
- On failure it writes the receipt, then raises, so the client exits 1.

## Commands

Run everything from the project root in PowerShell:

```powershell
$H = 'Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/Hybrid_Auto'
$C = 'Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/copilot_client.py'
```

### 0. Offline checks (already passed; re-run after any edit)

```powershell
python -B $H/hybrid_build_master_offline.py selftest
python -B $H/hybrid_build_master_offline.py staticscan
python -B $H/hybrid_build_master_offline.py argscheck
```

After editing `hybrid_build_master.py`:
1. Run `expectations --force`.
2. Re-pin `expectations_sha256`, `script_sha256` and `SCRIPT_PINS.json`.
3. Run `argscheck`.

### 1. Preconditions

- The bank editor PID 35156 has released in order: 0 `UnrealEditor.exe`, and the last line of `Staging/ModelBank/EDITOR_OWNER.txt` is `OWNER=NONE`.
- Re-measure the hashes:
  - The profile was `1bd89e5b…` at 07:40Z (M).
  - The map must be `4efebdfb…`.
  - The manifest must be `258469e1…`. Check with `python Staging/SystemCompletion_2026-10-04/seal_runtime.py --check`.
- The manager accepts the registry-ref leaf in writing. This is already recorded in `Incident_01a10c77_2026-10-05/DECISION_HYBRID_20261006.json`.

### 2. Profile (editor closed, OWNER=NONE)

```powershell
python -B $H/hybrid_profile_patch.py --expected-before <re-measured profile sha256> --dry-run
python -B $H/hybrid_profile_patch.py --expected-before <same sha256> --apply
```

**What changes:** exactly these leaves:
- `/landscape_material` becomes `MI_GeoCityGround_Auto`.
- `/external_landscape_material/parent_chain` becomes `[M_GeoCityAuto]` (the leaf diff shows `[0]` changed and `[1]` absent).
- `/external_landscape_material/decision` gets the new text.

The grass setting stays `false`.

**Prediction (M, dry run on `1bd89e5b`):** P′ = `4174a62787da9b203a647ce89438e5ddd0066e5bd9e10b816cd88204be0c9142`.

**Outputs:**
- `Before/AREA_PROFILE_1bd89e5b_<utc>.json`
- `Before/L_GazaShujaiya_BankIntegration_4efebdfb_<utc>.umap` (the map rollback point)
- `PROFILE_PATCH_RECORD_<utc>.json`

Then put P′ into every `Args/*.json` `profile_sha256`.

### 3. Pins

`copilot_client.py` enforces only the names listed in `Operator/SCRIPT_PINS.json`. The manager must add the three in-editor entries from `$H/SCRIPT_PINS.json` to `Operator/SCRIPT_PINS.json`. This folder's tooling does not write outside `Hybrid_Auto`.

### 4. Launch and authoring lease

```powershell
& Staging/SystemCompletion_2026-10-04/launch_editor.ps1 -AreaMap '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration' `
  -ExpectedMapSha256 4efebdfb0bf6c36b699a577b33faa64d28afbec0488115e6596883af518940d0 `
  -ExpectedManifestSha256 258469e14df2ca2e5e2b0c6543bf42e29c1fcde3d1628f7d258a607ee6d03024 `
  -ExpectedProfileSha256 <P'> `
  -ManagerThreadId cc37d4d2-3d62-4f53-b689-28432b5527ae -OperatorThreadId cc37d4d2-3d62-4f53-b689-28432b5527ae
```

The manager then appends exactly one line to `Staging/ModelBank/EDITOR_OWNER.txt`, using the actual PID:

```
<utc> OWNER=GEOCITY_GROUND_HYBRID manager_thread_id=cc37d4d2-3d62-4f53-b689-28432b5527ae operator_thread_id=cc37d4d2-3d62-4f53-b689-28432b5527ae assigned_editor_PID=<PID> map=/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration activation=GROUND_HYBRID_AUTHORING scope=GeoCity_GroundHybrid_20261006_auto_material
```

Put the PID into `expected_pid` in every authoring Args file.

### 5. Build the master (no save)

```powershell
python $C $H/hybrid_build_master.py $H/Args/HYBRID_ARGS_inspect_build.json
python $C $H/hybrid_build_master.py $H/Args/HYBRID_ARGS_build.json
```

**Inspect** must return `INSPECTED_READ_ONLY`.
- The receipt records `textures.*` (sRGB, compression, LOD group, VT, derived sampler) and `texture_selection`.
- The receipt also records `mma_true_outputs`: MakeMaterialAttributes_0 wiring read from a T3D export of the MW master (`receipts/HYBRID_T3D_<label>_vendor_PID<pid>.t3d`), each pin's OutputIndex resolved against MaterialFunctionCall_14's `Outputs(N)` names. It must be pin-matched (BaseColor <- SSP_16 index 0; Metallic/Specular/Roughness/Normal <- MW_MWAM_Water index 1/2/3/4).
- The legacy output-name reader (`get_input_node_output_name_for_material_expression`) returns one name per (target, source) pair. M, PID23068: it gives 'Metallic' for all four MF_14 pins, so it is advisory only (`mma_legacy_reader_outputs_advisory`).
- `STOP_TEXTURE_FALLBACK_REQUIRED` means an Asphalt roughness/AO map is sRGB or VT, and Concrete_plate passes. The client exits 1. To continue:
  1. Record the manager decision.
  2. Set `texture_set: "concrete_plate"` and `"fallback_acknowledged_by_manager": true` in the build Args.
  3. Bind the inspect receipt.

  Never change a texture.

**Build** fills `inspect_receipt` and `inspect_receipt_sha256`, and must return `BUILT_VERIFIED_NO_SAVE`.
- It exports the copy to T3D twice. `copy_pre` must equal the inspected wiring and supplies the true MF_14 output names for the Lerp A-inputs. `copy_post` must show MMA_0 pins pointing to the 5 Out nodes plus Metallic <- MF_14 index 1, and every new node's (source, OutputIndex) set must match the expectations.
- Only one build attempt is allowed per PID; the `receipts/HYBRID_BUILD_ONCE_PID<pid>.json` latch enforces it.
- The first shader compile can take minutes. The client times out at 600 s, but the script keeps running in the editor. Read the receipt; do not re-run.
- If the build fails, close the editor with Don't Save and rebuild in a new PID.

### 6. Area MI: mask proof, then first look (no save)

Copy the build receipt path and sha into `build_receipt` and `build_receipt_sha256` in the assign/verify Args.

```powershell
python $C $H/hybrid_assign_and_save.py $H/Args/HYBRID_ARGS_assign_inspect.json
python $C $H/hybrid_assign_and_save.py $H/Args/HYBRID_ARGS_apply_maskproof.json
python $C $H/hybrid_assign_and_save.py $H/Args/HYBRID_ARGS_apply_P1.json
```

**Expected statuses:**
- Assign inspect: `INSPECTED_READ_ONLY`.
- Each apply: `APPLIED_VERIFIED_NO_SAVE`.

**Each apply gates on:**
- `parity.differing`, which must be the 11 names listed below.
- All 64 components bound.
- The dirty set is a subset of {`M_GeoCityAuto`, `MI_GeoCityGround_Auto`} plus the map.

The 11 names are:
- the 5 ColorCorrection tints;
- Dirt, Stones and Rock Procedurals;
- Snow, Stones and Rock Advanced.

The parity gate was also re-checked offline against the measured DesertExample inventory (M).

**Captures after each apply:**
1. Maximize the editor window (ShowWindowAsync SW_SHOWMAXIMIZED).
2. Wait for the shader compile.
3. Run MCP CaptureViewport at the `close`, `middle` and `wide` presets of `Staging/GroundPainting_2026-10-04/CAMERAS_GazaShujaiya.json`.
4. Gate: width > height and width ≥ 1600 px.
5. Store the images as `$H/images/<label>_<NN>_<shot>.png`.

What to look for:
- The mask proof (Urban_Tint 2.5, 0.4, 0.4) shows red where the BuildingPad and RoadBed weights land.
- The P1 look is sent to Aviv.

**Tunes:** at most 3, MI values only, at most 5 applies per PID. For each tune, copy `HYBRID_ARGS_apply_P1.json` and give it a new `label`. A graph change means exit without saving and rebuild in a new PID.

### 7. Never call these

- The MCP `get_material_info` tool. It dirtied 15 MW functions on 2026-10-05.
- Save All or `save_assets([])`.
- `prepare()` or `verify_landscape()`.
- Cook or Bake.

### 8. Approval, then save

After Aviv approves, the manager writes `$H/APPROVAL_<label>.json`:

```json
{"schema": "environmentpipeline.hybrid_visual_approval.v1", "utc": "<utc>", "pid": <authoring PID>,
 "approved_by": "Aviv", "save_approved": true, "apply_receipt": "<latest look apply receipt path>",
 "apply_receipt_sha256": "<its sha256>", "captures": ["<image paths>"], "words": "<Aviv's approval, quoted>"}
```

Then fill `HYBRID_ARGS_save.json` (apply and approval paths/shas) and run:

```powershell
python $C $H/hybrid_assign_and_save.py $H/Args/HYBRID_ARGS_save.json
```

**What it checks before saving:**
- The approval binds this PID and the latest apply, and that apply's `purpose` is `look`. A mask proof is never saved.
- The master digest equals the build's.
- The MI values equal the apply's.
- The dirty set is exactly {master, MI} + map.
- The anchored log scan since the build offset is clean.

**What it does:** `save_packages(M_GeoCityAuto)`, then `save_packages(MI_GeoCityGround_Auto)`, then `save_map(Shujaiya)`.

**What it gates after saving:** dirty is `([], [])`, and the vendor, protected and pins are unchanged.

**Result:** `SAVED_NAMED_ONLY`. Record `disk_after.copy`, `disk_after.mi` and `disk_after.map`.

### 9. Close clean

Exit without further saves, using the `Operator/exit_no_save_<pid>.py` pattern: assert nothing is dirty, then append `OWNER=NONE`.

### 10. Fresh verify

1. Launch as in step 4, with `-ExpectedMapSha256 <save receipt disk_after.map>`.
2. Append the lease line with `activation=GROUND_HYBRID_VERIFY scope=GeoCity_GroundHybrid_20261006_auto_material_readonly`.
3. Run:
   ```powershell
   python $C $H/hybrid_verify_fresh.py $H/Args/HYBRID_ARGS_verify.json
   ```
4. The result must be `VERIFIED_READ_ONLY`.
5. Take the acceptance captures (same presets).
6. Exit without saving.

### 11. Ratification

The manager writes `RATIFICATION_B3_HYBRID.json` with:
- profile before/after: `1bd89e5b…` → P′;
- map before/after: `4efebdfb…` → saved;
- the 2 new packages and their shas;
- receipts, images, and Aviv's sign-off.

### 12. After the clean regeneration run

1. Launch fresh with the regenerated map sha.
2. Fill `expected_map_sha256` in `HYBRID_ARGS_verify_postregen.json`.
3. Run `hybrid_verify_fresh.py` with that Args file.

**Extra gates in this mode:**
- Ledger `phase == baked_saved_verified`.
- `parameters.landscape_material == MI_GeoCityGround_Auto`.
- Four `…_landscape_<Layer>` LayerInfo packages in `named_generated_dependency_paths`. The suffix format was measured on the B2 ledger (M).
- Landscape target layers include the four.

**Advisory only in this mode:** the MI file sha. The lifecycle may re-save area packages (BW:938-986, D), so the full value readback is the gate instead.

## STOP conditions (from the plan; each one is a hard gate, followed by close without saving)

- A vendor package is dirty, or the vendor pins or snapshot changed.
- The copied graph differs from the vendor graph: rows keyed by expression name, vendor path rewritten, GUIDs advisory.
- The copy lost the expression names.
- The MMA_0 wiring (from T3D) differs from the plan:
  - BaseColor ← `StaticSwitchParameter_16` (`MW_DebugBake`) output 0;
  - Metallic, Specular, Roughness and Normal ← `MaterialFunctionCall_14` (`MW_MWAM_Water`), with the output named like the pin.
- The copy's T3D wiring differs from the vendor's, or the post-edit T3D differs from the expectations.
- `recompile_material` is not `[]`, or the log contains "Failed to compile Material" or "Default Material will be used".
- `num_samplers` > 3.
- Any of the 4 layer names is missing or unreachable from MMA_0, or `RemoveFoliage` is unreachable.
- VT is on, a roughness/AO map is sRGB, or the sampler type does not match the derived one. Choose another set; never edit textures.
- Something is dirty outside {master, MI, map}.
- The profile, map or manifest drifted.
- More than 5 applies.
- Aviv rejects after 3 tunes.

## What each receipt proves

| Receipt | Proves |
|---|---|
| `HYBRID_MASTER_INSPECT_*` | Preconditions; vendor graph digest; MMA_0 wiring from T3D (`mma_true_outputs`); texture verdicts and derived samplers. |
| `HYBRID_MASTER_BUILD_*` | Copy equals vendor (rows and T3D MMA_0 wiring). The 56 nodes match the expectations exactly (class, edges, positions, parameters), with output indices proven by the post-edit T3D. Only the 5 MMA_0 pins changed. Compile clean; statistics; log clean. Graph digest (no GUIDs) that later steps bind to. |
| `HYBRID_ASSIGN_APPLY_*` | Full MI value table; 99-parameter parity vs live DesertExample; Urban values incl. measured GridCm = Landscape scale X; 64/64 components bound. |
| `HYBRID_ASSIGN_SAVE_*` | Three named saves only, in order; dirty `([], [])`; vendor and protected files unchanged; on-disk shas of master, MI and map. |
| `HYBRID_VERIFY_*` | A fresh process reproduces the saved state: hashes, graph digest, layer reachability, MI values, binding, paint-probe weights. With `post_regeneration` it also proves that regeneration kept the Auto MI and recreated the four LayerInfos. |

## Rollback

**Before any save.** Close with Don't Save; nothing in Content changed. To restore the Path B profile, run:

```powershell
python -B $H/hybrid_profile_patch.py --rollback $H/Before/AREA_PROFILE_1bd89e5b_<utc>.json --expect-current <P'>
```

That profile still points to the absent MW MI, so regeneration stays blocked. The pre-Path B baseline is `PathB_MW/Before/AREA_PROFILE_1328d5bb_*.json`, via `pathb_profile_patch.py --rollback`.

**After the save.** First run the profile rollback above, then:

```powershell
python -B $H/hybrid_profile_patch.py --rollback-map $H/Before/L_GazaShujaiya_BankIntegration_4efebdfb_<utc>.umap --expect-current-map <saved map sha>
```

- The map rollback is valid only until the next ordinary regeneration. The script refuses it after that.
- `M_GeoCityAuto` and `MI_GeoCityGround_Auto` stay on disk unreferenced. Deleting them is manager-only, after a reference check.

## Known limits (I = inferred, not yet measured)

- `PixelDepth` output names and `get_statistics` on the copy are asserted live. Only the Python wiring is proven offline.
- The Concrete_plate ORM channel order (R = AO, G = Roughness) is inferred from convention. It is used only on the fallback path.
- Survival through regeneration is proven only by step 12.
