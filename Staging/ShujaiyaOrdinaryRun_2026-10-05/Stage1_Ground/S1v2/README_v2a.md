# S1v2a: minimal macro colour variation for the Gaza ground (GazaShujaiya first)

Status 2026-10-06: **PREPARED OFFLINE, NOT EXECUTED.** No editor, MCP or process was used to author this; nothing under `Content/` was written (the texture packages were only read to measure the noise statistics). Labels: M = measured, D = documented (installed engine source / API), I = inferred.

This is the manager's minimal revision after `CodexReview/CODEX_DESIGN_REVIEW.md` §5. The full v2 design (`S1V2_DESIGN.md`, `S1V2_SPEC.json`) and the full-v2 draft script (`s1v2_material_edit.py`, `s1v2_material_edit_offline.py`) are **reference only**: they are not pinned and no runner sends them (the draft passes its own mock selftest, nothing more).

## 0. Decision needed BEFORE apply: the noise source (M)

`macro_noise_source` is fixed at inspect/apply because it sets the master sampler type (COLOR vs MASKS). Changing it later needs a new editor session (the apply latch). Measured from the source pixels (`NOISE_STATS_v2a.json`, `noise_stats_v2a.py`):

| source (args value) | texture | sampler | mean (lin) | std mip0 | std of 256-texel blocks (≈7.6 m at the 61 m tile) | kept as macro |
|---|---|---|---|---|---|---|
| `macro_variation` (manager default) | Epic `T_MacroVariation` | COLOR | 0.483/0.485/0.495 | 0.213 | 0.027 | **12.6 %** |
| `perlin` | Epic `T_Perlin_Noise_M` | MASKS | 0.507 | 0.155 | 0.051 | 33 % |
| `mw_noise` | MW `TEX_MW_Noise_msk` | MASKS | 0.346/0.356/0.361 | 0.251-0.258 | 0.181-0.191 | **72 %** |

- **Consequence (I from M):** `T_MacroVariation` is grain-dominated. Normalised by its mip0 std, most of the ±8.5 % brightness and ±5 % R/B range is fine grain (cm to a few m) close up, and at middle/wide distance the mips average it to roughly ±1 %: the 20-240 m zones the review asked for will be nearly invisible.
- **Recommendation:** `mw_noise` if Aviv confirms the MW licence; otherwise `perlin` (Epic-owned, about half as strong at macro scale). The default args keep the manager's `macro_variation`; ready variants are in `S1v2/Args/*_mw_noise.json` and `*_perlin.json` with their own expectations.
- `MacroInvStd`/`MacroMean` are parameters, so the amplitude can be re-tuned per child (`tune`) without a new apply, but the texture/sampler cannot.

## 1. What v2a changes (and what it keeps)

- **One** `StaticSwitchParameter GeoCity_S1_Enable` (default False) at **BaseColor only**. False ← the untouched `LandscapeLayerBlend_6`; True ← `MF_GeoCityV2a_MacroColor(Base = LandscapeLayerBlend_6)`. It is the only root rebinding; Normal (`LLB_7`), Roughness (`LLB_8`) and AO (`LLB_0`) stay as they are.
- **Untouched:** the Sand_01 hash-grid sampler, the `Multiply_8` macro, the `LinearInterpolate_42` soil chain, all weight-blend LLBs, the Grass nodes and their `GeoCity_LandscapeGrass` desc prefix, the base MI (never written; Iran compiles only the False permutation).
- **New MF** `/Game/Project/Shared/SurfacePainting/Appearance_20261003/Functions/MF_GeoCityV2a_MacroColor` (70 nodes, parameter-free, 3 Shared:Wrap TMVM_NONE fetches):
  - WorldPosition.XYZ → ComponentMask RG → ÷ Tile → rotate 17°/53°/89° → + offsets (0.13,0.71)/(0.37,0.61)/(0.83,0.29).
  - Tiles 61/211/733 m. Each octave uses channel R/G/B.
  - z_i = (n_i − Mean_c) × InvStd_c; V = 0.45 z1 + 0.35 z2 + 0.20 z3; Vc = clamp(V, ±2σ_V), σ_V = 0.604152. The field simulation measured 0.6052-0.6055, with 3.8-4.5 % of points clamped.
  - Color = Base × lerp(HueB, HueA, sat(0.5 + HueGain·Vc)) × (1 + ValueAmount·Vc).
- **Master additions:** 12 nodes (1 switch, 10 parameters, 1 MF call) at x −4000…−1840, y ≥ 36000. All descs start with `GeoCity_GroundS1v2a_20261006:`.
- **11 parameters (master default → Shujaiya t001):**
  - `GeoCity_S1_Enable`: False → True.
  - `GeoCity_S1_MacroNoise`: source texture.
  - `GeoCity_S1_MacroMean` and `GeoCity_S1_MacroInvStd`: the measured values of the chosen source.
  - `GeoCity_S1_MacroTile1/2/3Cm`: 6100/21100/73300.
  - `GeoCity_S1_ValueAmount`: 0 → 0.07 (brightness cap ±8.46 %).
  - `GeoCity_S1_HueGain`: 0 → 0.30.
  - `GeoCity_S1_HueA`: (1,1,1) → (1.034,1,0.966).
  - `GeoCity_S1_HueB`: (1,1,1) → (0.966,1,1.034). At the clamp R/B is 0.952…1.051.
- **Identity:** at master defaults, Color == Base **exactly** (offline numeric evaluation of the MF graph: max error 0.0 over 300 random cases). The shader is identical, but two captures still differ through TAA jitter and streaming, so the I0 gate is judged against a measured B0-vs-B0 floor (step 3/6).
- **Named save list:** `MF_GeoCityV2a_MacroColor`, `M_SurfaceBank_Natural`, and the Shujaiya `MI_GeoCityGround`, via `save_packages(named, False)`. Nothing else is saved.
- **Receipts** go to `S1v2/receipts_v2a/`. Latches are `S1V2A_APPLY_ONCE.json`, `S1V2A_SAVE_ONCE.json`, `S1V2A_TUNE_ONCE_<label>.json` and `S1V2A_CHILD_SAVE_ONCE_<label>.json`. Schemas are `*.v2a`.
- Inspect, apply and tune receipts carry `noise_stats_used`: the exact mean, inv-std, sigma_V, clamp, octaves, and the child-effective values.

**Kept from v1, reworked only where noted:** the activation/lease/PID guard, script identity, backup pins, the baseline gate (1015 nodes, `605c55d0…`), Grass contract, the consumers check, the static-switch probe plus G2 replay, the zero-old-row-change diff, compile with the switch forced True then False, the exact dirty set, tune phase a/b, save, child_save, verify, log scan and statistics gate.

## 2. Files (sha256 in `SCRIPT_PINS_v2a.json`)

| File | Role |
|---|---|
| `s1v2a_material_edit.py` (bf1bee4f) | in-editor; modes inspect/apply/tune/save/child_save/verify |
| `run_s1v2a.py` (6adc7c24) | Windows Python runner for the v2a EDIT only (sends `S1_Prep/s1_set_args.py` set → EDIT → clear). `S1_Prep/run_s1.py` stays the runner for `s1_capture.py`/`s1_verify.py`. |
| `s1v2a_material_edit_offline.py` (3eb534f0) | offline: `selftest` (all 3 sources, mock engine, numeric identity/range, baseline-dump checks, AST scan), `scan`, `expectations` |
| `noise_stats_v2a.py` (48698891) + `NOISE_STATS_v2a.json` (877bfa34) | offline texture statistics (run with the `gis` conda Python: numpy + GDAL) |
| `S1V2A_EDIT_EXPECTATIONS_GazaShujaiya.json` (77c32e59), `_mw_noise` (66219355), `_perlin` (c331e243) | generated from the final script bytes + the t001 args of each source |
| `S1V2A_ROOT_ACTIVATION_GazaShujaiya.json` (7be979ff) | activation TEMPLATE (PID placeholder). The script refuses activations under `S1_Prep`/`S1v2`; root copies it to `Stage1_Ground/Activation/S1V2A_ROOT_ACTIVATION_GazaShujaiya_PID<pid>.json`. |
| `Stage1_Ground/Args/S1V2A_ARGS_GazaShujaiya_{inspect,apply,tune1,save}.json` | default source (`macro_variation`); `<FILL` fields fail closed |
| `S1v2/Args/S1V2A_ARGS_GazaShujaiya_{inspect,apply,tune1,save}_{mw_noise,perlin}.json` | variant args sets |
| `S1v2/Args/S1V2A_CAPTURE_GazaShujaiya_{B0L,B0U,I0L,I0U,A3L,A3U}.json` | `s1_capture.py` begin files (LIT/UNLIT; B0 with an empty dirty list, I0/A3 allow MF + master + child). They pass `validate_begin` offline once `expected_pid` is an int. |

Rules: inspect and apply args must keep byte-identical `areas`/`child_values` (switch only). Every args file repeats the same `macro_noise_source` (tune, save, child_save and verify assert it against the apply receipt; a missing key means `macro_variation`). Any byte change to the script requires regenerating the expectations, activation, args `script_sha256` and pins.

## 3. Run order for the manager (from the measured current state)

M: `Operator/EXIT_PID23156.json` records that v1 was discarded, with 0 shutdown saves. The last lease line puts PID 16824 on Shujaiya with `activation=STARTUP_INSPECTION_ONLY scope=GeoCity_GroundS1_20261005_readonly`, and `S1_Prep/receipts/VERIFY_s1_shuj_baseline_r003_16824.json` is `BASELINE_VERIFIED_READ_ONLY`. Close → relaunch → baseline verify is therefore done.

0. Root picks `macro_noise_source` (§0) and uses that args set throughout.
1. Root copies the activation template to `Activation/S1V2A_ROOT_ACTIVATION_GazaShujaiya_PID16824.json`, sets `assigned_editor_PID: 16824`, hashes it, and fills `root_activation`(+sha) and `expected_pid` in the inspect args. The existing read-only lease line is accepted for inspect (its readonly pair is listed).
2. **Inspect** (from `S1v2`): `python -B run_s1v2a.py s1v2a_material_edit.py ..\Args\S1V2A_ARGS_GazaShujaiya_inspect.json` → `receipts_v2a\S1V2A_INSPECT_s1v2a_shuj_r001_inspect_PID16824.json`.
3. **B0 recapture, same session** (from `S1_Prep`, v1 runner): `python -B run_s1.py s1_capture.py ..\S1v2\Args\S1V2A_CAPTURE_GazaShujaiya_B0L.json`, then prepare/request/complete for index 0-2, then `--phase end`, exactly as in `S1_Prep/README.md` §4 step 6. Repeat with `B0U` (UNLIT), then take B0U a second time: copy the file under a new label, e.g. `GazaShujaiya_S1V2A_B0U_r002`. The two B0U sets give the capture noise floor. `s1_capture.py` checks only OWNER, PID, map and operator thread from the lease line (M: s1_capture.py:520-527), so captures also work under the v2a authoring line.
4. Root appends the AUTHORING lease line (`activation=GROUND_S1V2A_AUTHORING scope=GeoCity_GroundS1v2a_20261006_material_edit`, same OWNER/threads/PID/map) and fills the apply args (activation, PID, inspect receipt + sha). The operator sets `no_asset_editors_open_on_s1_assets: true` after checking.
5. **Apply:** `python -B run_s1v2a.py s1v2a_material_edit.py ..\Args\S1V2A_ARGS_GazaShujaiya_apply.json` → `S1V2A_APPLY_…` with status `APPLIED_VERIFIED_NO_SAVE`. No save happens here. A runner timeout is not an abort; read `receipts_v2a/`.
6. **I0 captures:** `I0L` and `I0U`. Gate: the I0U-vs-B0U difference must lie within the B0U-vs-B0U floor (shader identity is exact; TAA and streaming are not). The LIT difference must lie within the B0 noise floor (exposure is auto, and Lumen/TAA vary). Above the floor: STOP.
7. **Tune t001:** fill the tune1 args (apply receipt + sha; `state_receipt` = the apply receipt), then run it. Then capture A3 with `A3L` and `A3U`.
8. Aviv reviews. Root writes the visual review receipt (`state_receipt_sha256` = the t001 tune receipt) and fills the save args.
9. **Save:** `python -B run_s1v2a.py s1v2a_material_edit.py ..\Args\S1V2A_ARGS_GazaShujaiya_save.json` → `SAVED_NAMED_ONLY`, `dirty_after` empty.
10. Quit with nothing dirty. In a fresh editor, root makes a NEW activation copy for the new PID (one activation binds one PID) and a read-only lease line. Then run `mode=verify`: copy the save args, set `mode: verify`, a new label, the new activation + sha and `expected_pid`, and the apply + save receipts. Then take an S1_fresh capture. Rimal later runs tune phase b + child_save in its own session (not prepared here).

## 4. STOP conditions (nothing is saved; on any in-memory change close with "Don't Save", root reviews)

- **Guard and baseline:** v1 §6 guard/baseline failures, unchanged.
- **Function packages:** any v1 `MF_GeoCity_*`, draft `MF_GeoCityV2_*` or `MF_GeoCityV2a_*` package exists.
- **Noise source:** inspect `macro_noise_source` ≠ apply ≠ later args. Or a child noise texture is not the source texture. Or `texture_fit` fails: a sampler mismatch, or a virtual texture.
- **Probe and diff:**
  - the probe or G2 dirties a map;
  - an old node row changes;
  - more than the BaseColor root moves;
  - an added node is outside the prefix or canvas;
  - the parameter set ≠ the 11 names;
  - the MF does not have exactly 3 Shared:Wrap TMVM_NONE fetches and 1 WorldPosition.
- **Compile:** a forced-True or default-False `RecompileMaterial` ≠ [], or the log scan hits a failure marker.
- **Dirty set:** it ≠ {MF, master, Shujaiya child}.
- **I0U differs from B0U by more than the B0U-vs-B0U floor.** The shader identity is exact, so a larger difference means the switch/permutation or the capture conditions differ.
- **Save is refused:** no review receipt, a mismatched state, or a backup pin changed.
- **Tune budget:** 3 per area is used up.

## 5. Open risks (honest)

1. **Noise source (M, §0).** The manager's default `T_MacroVariation` will likely not produce visible 20-240 m variation. Decide before apply.
2. **LWC rotation (D/I).**
   - WorldPosition → ComponentMask RG → Divide → TextureSample already compiles in the live Gaza graph (M: `ComponentMask_14 WorldXY → Divide_7 → TextureSample_0`).
   - The extra DotProduct/Append on LWC values is D (`UE_5.8 LargeWorldCoordinates.ush:450-451` `LWCDot(FLWCVector2, float2)`; `MaterialTemplate.ush:2858` rotates texcoords the same way), not measured.
   - Backstop: the forced-True compile gate. A failure costs a "Don't Save" and a new session.
3. **Switch propagation (I).** That the child's switch reaches every Landscape component MIC is inferred. G1/I0 captures are the check.
4. **Statistics (I).** These come from source pixels. Runtime BC compression and filtering, and local area bias, are inferred close. The −2σ/+2σ clamp hits about 4 % of points (simulated, mip 0).
5. **One field drives both value and hue.** Brighter areas are warmer, as ordered. Decorrelating them would need a second weighted sum (not done).
6. **Unrelated repetition is not addressed:** normal-map repetition, binary RoadBed/Pad edges, contact and grass are unchanged. `GeoCity_GrassCoverage` is not touched, so the child keeps its current value (0.15 per README 7.8).
7. **`s1_verify.py post_s1`** reads only v1 receipt schemas and cannot verify v2a receipts. Fresh checking is v2a `mode=verify` plus captures.
8. **Reused v1 backup manifest.** `S1B_20261005T202836Z` (c32afcdb) still lists the v1 MF names in `new_asset_paths`. v2a accepts that list, asserts every S1 MF package is absent, and records its own package in the apply receipt as the rollback list.
9. **MW licence** is unverified (Aviv). It matters only for `mw_noise`.
10. **Offline proof covers wiring and maths only** (mock engine). Pin names inside MFs, compile and propagation are asserted at run time.
