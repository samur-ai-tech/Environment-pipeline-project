# PermissionError diagnosis: PID 10460, 2026-10-05 16:12:01Z

Read-only diagnosis by a manager-session sub-agent (Claude Code session cc37d4d2). No editor or MCP calls, no process control, and no file changes other than this file.

Labels: MEASURED = read directly from a file, log or attribute. INFERRED = reasoning from code or documented OS behaviour. NOT MEASURED = could not be observed.

## 0. The state has moved on since the incident note was written (read this first)

- MEASURED: chat 01a10c77 kept working after the failure.
  - At 16:14:52Z it ran `Staging/ModularConstruction_2026-10-05/Run_20261005/resume_completed_cook.py` inside PID 10460.
  - Before resuming, it copied the failed state to `Run_20261005/Attempt3/WORKFLOW_BEFORE_SAVE_RECOVERY.json`. The copy keeps the original mtime, 16:12:01.82Z.
  - It also wrote `Attempt3/SAVE_RECOVERY.json`.
- MEASURED: the script changed the live `GeoCityRun` object in memory:
  - asserted that the phase was `failed_cook_verification` and the error was `PermissionError(13, 'Access is denied')`;
  - set `phase='cooking'` and removed `error`;
  - re-registered the `watch` tick;
  - called `after_processing(wrapper)` again.
- MEASURED: what the editor log shows next:
  - official Bake at 16:14:56Z;
  - named saves of `Bake/GazaShujaiya_buildings` and 4 LayerInfos at 16:15:05Z;
  - map save at 16:15:15Z ("Saving map ... took 5.490");
  - map reopen at 16:16:02Z.
- MEASURED: `WORKFLOW_STATE.json` and `BUILD_STATE.json` now show `phase=baked_saved_verified` (16:15:17Z), and `LAST_SUCCESSFUL_WORKFLOW_STATE.json` was rewritten.
  - The map hash is now `911cc7ef...`; it was `17d5929a` before.
  - `EDITOR_OWNER.txt` last line, 16:17:11Z: `OWNER=NONE released_by=01a10c77 ... phase=BUILDINGS_GENERATED_SAVED_REOPENED`.
- MEASURED leftovers in the final state:
  - `lease_released=false` in the workflow state, although the chat appended an OWNER=NONE line itself;
  - `transaction_autosave.held_disabled_for_recovery=true`. Autosave was already off before the run, so nothing is lost;
  - one dirty, unreferenced cook package: `.../Cook/.../GeoCity_city_v015_PermanentBank_3_376_0_main_geo`.
- So "Map NOT saved; cooked unbaked result in memory" in `DECISION_LET_RUN_FINISH.json` is stale. A Bake and map save did happen.
- They happened through an out-of-band resume that bypassed the fail-closed failed phase, not through the ordinary lifecycle. Whether to accept that save is a manager/Aviv decision. This diagnosis does not make it.

## 1. Correction: the failure was not in the road phase

- MEASURED: `AREA_PROFILE.json` (sha `568a994e`, the same at run start and now) has `roadbld_workflow.enabled=false`.
- Therefore `native_road_phase=None` (line 159). `begin_native_roads` (line 694) cannot run in this operation.
- MEASURED: the failed state copy has `geographic_ground_connection.paint_ready=false`. It has no `paint_readiness_wait_seconds`, and only 2 `official_landscape_identity_reads` (16:07:34Z and 16:11:59.99Z).
- So after `cooked_verified` was written (line 657), the code took the paint-wait branch (lines 658-665), not `advance_cooked`.
- INFERRED: the "Houdini Engine cooking paused" log line at 16:12:01.434 is `finish_operation()` (line 242) running inside `fail()`. It is not line 745.
  - The 0.414 s gap before the error log at 16:12:01.848 is the final 18.9 MB state write in `finish_operation()`.
- The only filesystem operation between line 657 and the exception is line 664: `self.state['phase']='cooked_waiting_for_paint'; self.write()`.
- `write()` (lines 436-443) does two things for each target, `WORKFLOW_STATE.json` first and then the `BUILD_STATE.json` alias:
  1. `pending.write_text(...)`
  2. `os.replace(pending, target)`
- The exception reached `after_processing`'s `except`, so the phase became `failed_cook_verification`. Had it occurred inside `finish_cook_readiness`, the phase would be `failed_cook_paint_readiness`. The tick at line 665 was never registered.

## 2. Exact operation and culprit

- **Failing call (INFERRED, high confidence):** `os.replace('...\WORKFLOW_STATE.json.10460.pending', '...\WORKFLOW_STATE.json')` at line 443, during the line-664 write.
- **Why this call:**
  - The text `'Access is denied'` is the Win32 message for WinError 5. Python reports it only for Win32 API calls such as MoveFileExW (`os.replace`).
  - A plain `open()`/`write_text` failure reports `'Permission denied'` instead.
  - The repr `PermissionError(13, 'Access is denied')` drops the filename, which is why the log shows no path.
- **Most likely holder (MEASURED timing + INFERRED mechanism):** the manager session's own background monitor, task `bddm8tq6f`.
  - It was started at 16:11:14.9Z (session cc37d4d2 transcript). It ran `json.load(io.open(WORKFLOW_STATE.json))` every 45 s, then `tasklist` and a SHA-256 of the 70 MB map.
  - Its output contains `16:12:01Z phase cooked_verified`. That sample opened the 18.9 MB file right after the line-657 write and was parsing it at the moment of the line-664 replace.
  - CPython opens files without `FILE_SHARE_DELETE`. Windows refuses a replace-rename onto a target that has such an open handle and returns ERROR_ACCESS_DENIED (5).
  - The earlier sample (16:11:15Z, phase `cooking`) did not coincide with a write. The later one (16:12:46Z) saw `failed_cook_verification`.
- **Ruled out (MEASURED):**
  - Read-only, hidden, system or reparse-point attributes: none on `WORKFLOW_STATE.json`, `BUILD_STATE.json`, `GazaShujaiyaIntegration_2026-10-02\` (recursive), or `Staging\ModularConstruction_2026-10-05\` (recursive, including `Run_20261005` and `ContractAudit\Registries`).
  - ACL deny: none. Inherited ACEs give USER, Administrators and SYSTEM full control, and CodexSandboxUsers modify.
  - Directory/file confusion: none. Both targets are regular files and the folder is a directory.
  - `\\?\` prefix: it appears only in `RunExisting_20261005/RUN_AUTHORIZATION.json` as a backup path string. The profile's `workflow_receipt` and `build_state_alias` are plain paths.
  - A permanent condition: `fail()`'s own rewrite of the same files succeeded about 0.5 s later (`failure_receipt_write_error` absent, `cleanup_errors=[]`). No `.pending` file is left over, because later successful writes consumed it.
- **Not excluded (NOT MEASURED):** a simultaneous read by chat 01a10c77's own tooling, or an antivirus or indexer scan of the freshly replaced file.
- **Live lock check (NOT MEASURABLE):** `handle.exe` and `handle64.exe` are not installed. `openfiles` needs admin rights and the "maintain objects list" flag plus a reboot. The transient handle closed long ago, and the monitor exited at 16:12:46Z.

## 3. Fix

- No permission, attribute, ACL or path change is needed. All targets are writable.
- Operational rule for future runs: while a GeoCity run is live, no monitor, agent or script may open `WORKFLOW_STATE.json` or `BUILD_STATE.json`, nor read the 135 MB `HDA_CATALOG_RECEIPT.json` around write points.
  - Poll only `os.stat` (mtime and size), the editor log, or `EDITOR_OWNER.txt`.
  - Read the contents only after a terminal phase, or from a copy made after the run ends.
- Optional hardening (a code change, so it is the source owner's decision; not applied here): a bounded retry of `os.replace` on `PermissionError` in `GeoCityRun.write()` and `save_profile()`. The same pattern exists in `geocity_roadbld_workflow.write()`.

## 4. Resume path and the cooked state

- The retained code has no resume path.
  - `fail()` sets a `failed_*` phase.
  - `guard()` (line 192) asserts that the phase is not failed.
  - `bake_and_save` requires `phase=='cooked_verified'`.
  - `finish_operation()` removes the delegates and pauses cooking.
- Within the code's own lifecycle, a failed operation needs a fresh run.
- The cooked result was nevertheless reused, through the ad-hoc in-memory resume described in section 0. That resume is the reason the "fresh run needed" premise no longer matches the disk.
