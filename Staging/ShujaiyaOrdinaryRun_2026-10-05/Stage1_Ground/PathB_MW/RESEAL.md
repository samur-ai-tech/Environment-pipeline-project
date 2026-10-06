# Path B: seal, pins, launch, ratification (manager runbook)

All commands run from the project root `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline` in PowerShell (`python` = the same interpreter that ran `seal_runtime.py` before). Set `$B = 'Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/PathB_MW'`.

## Measured baseline (2026-10-06, editor closed, OWNER=NONE)
| Item | sha256 |
|---|---|
| Runtime manifest `Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json` | 258469e14df2ca2e5e2b0c6543bf42e29c1fcde3d1628f7d258a607ee6d03024 (`seal_runtime.py --check` passes, M) |
| `Content/Python/geocity_landscape_workflow.py` | d1a5d5fdbcf8e5d3ced8dc9ccf9a2d975fb2c845546ffd84649c37137b4c998d (copy kept in `$B/Before/`) |
| Shujaiya profile | 1328d5bbdf0005bbb5b4b7ede85269c0d203beca361e193e0c9fd0edb0478b39 |
| Shujaiya map `.umap` | 4efebdfb0bf6c36b699a577b33faa64d28afbec0488115e6596883af518940d0 |
| `MI_GeoCityGround` (Shujaiya, Natural child, stays on disk) | 8fb548f8a70b65bfb696d8d7bb7c07a4914d83ecb5750c20c4c6e65391421228 |
| MW `MTL_MWAM_Landscape_DesertExample.uasset` / `MTL_MWAM_AutoMaterial_MASTER.uasset` | 0fc96edd…ac985 / 981e207c…f1d66 |
| HDA `GeoCity_city_v015_PermanentBank.uasset` | 2358c514… (unchanged by Path B) |
| Rimal profile | 8711cace… (unchanged by Path B) |

## Option 0 (recommended): no source change, no reseal
1. **Preconditions.**
   - The last line of `Staging/ModelBank/EDITOR_OWNER.txt` is `OWNER=NONE`, and no `UnrealEditor.exe` is running.
   - `python Staging/SystemCompletion_2026-10-04/seal_runtime.py --check` must print `"manifest_sha256": "258469e1…"`.
2. **Profile.**
   - Dry run: `python $B/pathb_profile_patch.py`. Expect `after_sha256` 54e3b19c990e7661ffbc74c12b1e9769215951a9f130ac67e806a088d6ec99ed.
   - Apply: `python $B/pathb_profile_patch.py --apply`. It writes `$B/Before/AREA_PROFILE_1328d5bb_<utc>.json`, the map byte copy `$B/Before/L_GazaShujaiya_BankIntegration_4efebdfb_<utc>.umap` (the rollback point), and `$B/PROFILE_PATCH_RECORD_<utc>.json`.
3. **Script pins.**
   - Add the `pathb_assign_and_save.py` and `pathb_verify_fresh.py` entries of `$B/SCRIPT_PINS.json` to `Operator/SCRIPT_PINS.json` (create it if absent). `Operator/copilot_client.py` enforces only listed names.
   - Each script also checks its own bytes (`script_sha256`) and code signature.
4. **Authoring launch.**
   ```powershell
   & Staging/SystemCompletion_2026-10-04/launch_editor.ps1 -AreaMap '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration' `
     -ExpectedMapSha256 4efebdfb0bf6c36b699a577b33faa64d28afbec0488115e6596883af518940d0 `
     -ExpectedManifestSha256 258469e14df2ca2e5e2b0c6543bf42e29c1fcde3d1628f7d258a607ee6d03024 `
     -ExpectedProfileSha256 54e3b19c990e7661ffbc74c12b1e9769215951a9f130ac67e806a088d6ec99ed `
     -ManagerThreadId cc37d4d2-3d62-4f53-b689-28432b5527ae -OperatorThreadId cc37d4d2-3d62-4f53-b689-28432b5527ae
   ```
5. **Lease (manager appends one line, actual PID).**
   `<utc> OWNER=GEOCITY_GROUND_PATHB manager_thread_id=cc37d4d2-3d62-4f53-b689-28432b5527ae operator_thread_id=cc37d4d2-3d62-4f53-b689-28432b5527ae assigned_editor_PID=<PID> map=/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration activation=GROUND_PATHB_AUTHORING scope=GeoCity_GroundPathB_MW_20261006`
6. **Run** with `python Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/copilot_client.py $B/pathb_assign_and_save.py $B/Args/<file>`. Put the PID into `expected_pid` first.
   1. `PATHB_ARGS_inspect.json`. Expect `INSPECTED_READ_ONLY`, `mi_exists=false`, one Landscape, `vendor_pins_match=true`, clean dirty state.
   2. `PATHB_ARGS_apply_P1.json`. Expect `APPLIED_VERIFIED_NO_SAVE`, with only `MI_GeoCityGround_MW` and the map dirty. Then follow CAPTURE_PLAN.md. If needed, run `apply_P2` / `apply_P3` (max 4 per PID).
   3. `PATHB_ARGS_save_mi_and_map.json` (route a). Fill in the latest apply receipt path and sha. Expect `SAVED_NAMED_ONLY` and nothing dirty. Record `disk_after.map` and `disk_after.mi`.
   - Route b (regeneration proof): run apply with `"assign_landscape": false`, then `PATHB_ARGS_save_mi_only.json`, then an ordinary regeneration under a separate MANAGER_ACTIVATED task4 lease (`ordinary_generation_authorized`).
7. **Exit without further saves.** Use the `Operator/exit_no_save_<pid>.py` pattern: it asserts the map is clean and appends `OWNER=NONE`.
8. **Fresh verify launch.**
   - Use the same command as step 4, with `-ExpectedMapSha256 <save receipt disk_after.map>` (route a) or the post-regeneration map sha (route b).
   - Append the lease line with `activation=GROUND_PATHB_VERIFY scope=GeoCity_GroundPathB_MW_20261006_readonly`.
   - Run `pathb_verify_fresh.py` with `PATHB_ARGS_verify.json`. Expect `VERIFIED_READ_ONLY`. For route b, add `expected_map_sha256`.
   - Take the CAPTURE_PLAN.md shots, then exit without saving.
9. **Write the B3 ratification record** (template below), then update the status lines in CURRENT_STATE/AGENTS.

## Option 1: optional hardening patch, needs a reseal
Run this before step 2, with the editor closed and OWNER=NONE:
1. Check that `Content/Python/geocity_landscape_workflow.py` has sha d1a5d5fd…. Review `$B/geocity_landscape_workflow.patch`.
2. Copy `$B/patched/geocity_landscape_workflow.py` over it. Expect sha 2bc51f9715ae066a37ed1ab7079856895b2135d46476f98929dbe3267adcc13c. The file is CRLF; copy it, do not `patch` it.
3. Run `python Staging/SystemCompletion_2026-10-04/seal_runtime.py` with no arguments. Predicted output: `manifest_sha256` = **6cb588f665cc1f3e5d8f57b047b05a2a3bfc7971608287dbf9f00236f18a8ac9**, byte-identical to `$B/patched/PREDICTED_geocity_runtime_manifest_option1.json`. Only the `geocity_landscape_workflow` entry changes. Then run `--check`.
4. Profile: `python $B/pathb_profile_patch.py --apply --external-block --parent desert`. Expected after sha: **fe23b280c9a412a97af0eaea60634a0e190c03f33c5c15edcb305c15fb94056c**.
5. Steps 3-9 as in Option 0, with `-ExpectedManifestSha256 6cb588f6…` and `-ExpectedProfileSha256 fe23b280…`. Also set `profile_sha256` in every `$B/Args` file to fe23b280…; the templates carry the Option 0 value. The authoring scripts do not depend on the patch. The patch acts only inside the ordinary lifecycle `prepare()`.

## Pins to update (M: grep for 1328d5bb / 4efebdfb)
- **Live:** the launch arguments above. The ratification record (B3 supersedes B2's `shujaiya_profile`, `shujaiya_map`, and in Option 1 `runtime_manifest`). The `profile_sha256` fields in `$B/Args/*`.
- **History, do not edit:**
  - `RATIFICATION_B2.json`
  - `SystemCompletion_2026-10-04/LAUNCH_STATE*.json`
  - the S1 receipts, CAPTURE files, README and plan_out
  - `ProceduralCityRegeneration_2026-10-05/PREPARATION.json`
  - the profile's own `WORKFLOW_STATE`/`BUILD_STATE`/`LAST_SUCCESSFUL_WORKFLOW_STATE`, which are rewritten by the next ordinary run
- The S1 tools (`s1_verify.py`, `s1_capture.py`) assume the Natural child. Treat them as superseded for Shujaiya ground checks.

## Ratification record template: `Staging/ShujaiyaOrdinaryRun_2026-10-05/RATIFICATION_B3_PATHB.json` (manager writes it)
```json
{
  "schema": "environmentpipeline.manager_ratification.v1",
  "utc": "<utc>",
  "manager": "Claude Code session cc37d4d2-3d62-4f53-b689-28432b5527ae",
  "decided_by": "Aviv, 2026-10-06: Path B after the unsaved MW preview (Operator/MWPreview_20261006/PREVIEW_ASSIGN.json); no grass; RoadBed/BuildingPad masks not consumed by the ground material (accepted for now); pale Gaza sand, not orange; chosen tint preset <P1|P2|P3> from captures <paths>",
  "supersedes": "RATIFICATION_B2.json for shujaiya_profile, shujaiya_map (and runtime_manifest if Option 1)",
  "ratified_baseline_B3": {
    "runtime_manifest": {"sha256": "<258469e1… (Option 0) | 6cb588f6… (Option 1)>", "seal_check": "<seal_runtime.py --check output>"},
    "geocity_landscape_workflow.py": {"sha256": "<d1a5d5fd… | 2bc51f97…>", "change": "<none | optional hardening patch PathB_MW/geocity_landscape_workflow.patch>"},
    "shujaiya_profile": {"sha256": "<54e3b19c… | fe23b280…>", "record": "<PathB_MW/PROFILE_PATCH_RECORD_<utc>.json>", "before": "1328d5bb…"},
    "shujaiya_map": {"sha256": "<save receipt disk_after.map>", "before": "4efebdfb…", "rollback_copy": "<PathB_MW/Before/L_GazaShujaiya_BankIntegration_4efebdfb_<utc>.umap>"},
    "shujaiya_ground_mi": {"path": "/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_MW", "sha256": "<save receipt disk_after.mi>", "parent_chain": ["…DesertExample", "…AutoMaterial_MASTER"], "tints": "<preset values>"},
    "mw_vendor_pins": {"DesertExample": "0fc96edd…", "master": "981e207c…"},
    "unchanged": {"rimal_profile": "8711cace…", "hda": "2358c514…", "natural_master_base_grass_old_child": "<save receipt disk_after.protected>"}
  },
  "proof": {"apply": "<receipt+sha>", "save": "<receipt+sha>", "fresh_verify": "<receipt+sha, VERIFIED_READ_ONLY>", "captures": "<paths>", "regeneration_survival": "<pending | ordinary run utc + verify re-run receipt>"},
  "rule_from_now": "Every further change to HDA, profiles, Content/Python or seal goes through the manager with a record; no self-issued leases."
}
```

## Rollback (editor closed, OWNER=NONE)
1. `python $B/pathb_profile_patch.py --rollback $B/Before/AREA_PROFILE_1328d5bb_<utc>.json --expect-current <current profile sha>`. The profile returns to 1328d5bb with grass enabled and the Natural child.
2. **Only if no ordinary regeneration has run since the map backup:** `python $B/pathb_profile_patch.py --rollback-map $B/Before/L_GazaShujaiya_BankIntegration_4efebdfb_<utc>.umap --expect-current-map <current map sha>`. The map returns byte-exactly to 4efebdfb, bound to `MI_GeoCityGround`.
   - The script refuses if `LAST_SUCCESSFUL_WORKFLOW_STATE.json` is newer than the backup. A regeneration bakes with `replace_previous_bake` and retires obsolete actors and packages, so an older `.umap` would reference Bake content that no longer matches. That always applies to route b, and to route a once the survival-proof regeneration has run.
   - After any regeneration, roll back by restoring the profile and running one ordinary regeneration. That re-binds `MI_GeoCityGround`, and `prepare()` re-runs the Natural/Grass authoring and its named saves.
3. Option 1 only: copy `$B/Before/geocity_landscape_workflow_d1a5d5fd.py` back and run `seal_runtime.py`. Expect 258469e1… again (M: today's sources reproduce that manifest).
4. `MI_GeoCityGround_MW` may stay on disk unreferenced. Do not delete it without a reference check and a record.
5. Write a rollback ratification record with the same schema.
