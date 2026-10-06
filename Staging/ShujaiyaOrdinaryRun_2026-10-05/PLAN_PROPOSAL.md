# Plan: one clean end-to-end GazaShujaiya run on the current sealed code

`<root>` = `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline`. Read-only research only so far. Nothing has been executed.

## Context

- **Goal:** prove the whole chain once with today's code. The sequence is generate → Bake → named save → fresh reopen → regenerate with no duplicates → reopen. No source edit and no reseal.
- **Why:** each part was fixed separately, but the current lifecycle (`geocity_bank_workflow.py` f349d128, seal 3cd33b15) has never run a generation. Every `RUNTIME_STARTUP_PID*.json` shows `generation_started=false`. The last real cook, PID33168 on older code, failed at the road Landscape selector, and nothing was saved.
- **Live state (MEASURED 2026-10-05 ~06:50Z, re-measure at execution):**
  - **Live editor:** an active ground-painting worker holds the editor. It is PID32464, under the lease `OWNER=CODEX_GROUND_PAINTING ... STARTUP_INSPECTION_ONLY`, and it keeps opening and closing editors. Its Rimal ground work is NOT_RUN.
  - **Shujaiya map:** hash 17d5929a. It holds 2 Landscapes, 136 + 132 road actors and 87 unvalidated candidates.
  - **Shujaiya profile:** hash 00877b7c. It pins catalog f6fff4f9 with 1223 rows.
  - **Road ledger:** `ROADBLD_WORKFLOW_STATE.json` (a0541fc4) still lists the 132 unsaved staged paths from PID33168. Road preflight would therefore fail after a full Cook (`geocity_roadbld_workflow.py:695-706`). INFERRED from the code.
  - **Authority:** the user STOP is in force. `BANK_ACTIVATION.ordinary_generation_authorized=false`. `GENERATION_ACTIVATION.json` is dead (PID33168, old seal).

## On approval, this session will (read-only output only)

- Copy this plan into `Staging/ShujaiyaOrdinaryRun_2026-10-05/PLAN_PROPOSAL.md` as a proposal.
- Draft a ready-to-paste English message to the manager chat Aviv picks: role + instructions file + clear request.
- This session does NOT touch any editor, `EDITOR_OWNER.txt`, `ROADBLD_WORKFLOW_STATE.json`, `GENERATION_ACTIVATION.json`, `ASSIGNMENTS.json` or maps. All steps below belong to the manager and its operator.

**Aviv's answers (2026-10-05):**
- **Executor:** the current manager, chat 01a10789. No reassignment is needed.
- **Ground-painting task:** let it finish and close cleanly before anything starts.

**Order agreed with Aviv (Pegasus ideas from the Codex review):**

**A. Ground appearance (Pegasus Color Map ideas).** Already in progress. Nothing new is assigned.
- **Owner:** execution chat 01a10883 owns it under `Staging/GroundPainting_2026-10-04/ASSIGNMENT.json`, which cites the Pegasus color-map tutorial.
- **Scope:** broad variation, tint, texture scale, transitions, and Lit before/after plus fresh-reopen images.
- **Gate:** Aviv judges its images.

**B. One clean full run.** Steps below, starting from the ground task's final saved state.

**C. Vegetation and props scatter (Pegasus Landscape Workflow).** Only after B passes, as a separate bounded assignment, followed by another full run.

**Not reassigned:**
- The DataTable bank input already exists (`geocity_bank_workflow.py:481-553`).
- Generate/Regenerate already exists (`geocity_editor_action.py:272`).
- IDMap adoption and the buildings tutorials are out of scope.

## Aviv's decisions

1. **Scope:** lift the STOP for exactly run1, reopen1, run2, reopen2 and one Lit image. The same approval covers the evidence backup and the road-ledger fix.
2. **Who acts:** the code binds manager thread 01a10789 and operator thread 01a106e8 (`geocity_editor_action.py:49-56`, `launch_editor.ps1:15`, `ASSIGNMENTS.json`).
   - Lease lines carrying those IDs must come from those threads.
   - Another executor first needs a manager edit of `ASSIGNMENTS.json`.
3. **Ground task first:** the ground-painting worker finishes or pauses, then quits in order. OWNER=NONE is written only after 0 UnrealEditor processes remain.
   - **Collision:** this run sets the Shujaiya Grass coverage from 0.0 to 0.15. It also re-saves the shared ground master, which changes Rimal too.

## Manager decisions (defaults)

4. **Grass coverage:**
   - `prepare()` rejects 0 (`geocity_landscape_workflow.py:47-50`) and writes the profile value 0.15 into the MI.
   - It also recompiles and saves the shared master (:350-354), which also affects Rimal.
   - Accepting 0.15 is the only no-code option.
5. **Launch route:**
   - Use the direct sealed `Staging/SystemCompletion_2026-10-04/launch_editor.ps1`.
   - The reviewed Continuation launcher cannot pass after a ground release (`continuation_manifest.py:70,80-87`).
   - This drops code-enforced Continuation pins (87 candidates, table selection), so step 4 checks them by hand. Requires a manager and Aviv decision.
6. **Two new read-only editor scripts:** each is hash-pinned, and neither is a reseal.
   - (a) A startup inspection script. `inspect_task4_startup.py` is bound to the stale Continuation.
   - (b) A Lit capture helper. `native_capture.py` asserts a ground lease and picks the Landscape by name.
   - Without (b), there is no image.
7. **Editor window and sign-ins:**
   - Keep the editor window visible. A failure opens a modal dialog (`editor_action.py:263`), while the launcher hides the window.
   - Aviv does any RoadBLD or Houdini sign-in personally. No bypass.
8. **Timeout:** accept the 1800 s default (`bank_workflow.py:177`), which has never been measured on a full run.

## Freeze (zero editors, after decisions 1-5)

- **Seal:** stays 3cd33b15. The Iran r019/r020 candidates stay unpromoted.
- **Untouched:**
  - DT_EnvironmentBank_v4 (f763b072), the catalog sources and the profiles;
  - holds H0013/H0907/H0051/H0958/H0094 and the declined palms;
  - vendor originals, the 87 candidates and Rimal.
- **Freeze receipt:** re-hashes the map, profile, manifest, master, MI, the Rimal map and profile, the DT, the 87 candidates, the hold rows and the 6 Shujaiya ModelBank receipts.
- **Trap:** never add a second `AREA_PROFILE.json` under `Staging/ModelBank/*` (globs at `editor_action.py:14`, `launch_editor.ps1:44`).

## Starting map

- Start from the current on-disk Shujaiya map, as it is after the ground release.
- **No restore and no manual cleanup.** AGENTS.md forbids restoring. The fe56a24d backup lacks the 132 retained actors and would fail the road check.
- **The lifecycle itself retires the old actors:**
  - old baked actors only after a verified Bake, followed by a one-Landscape assert (`bank_workflow.py:872-879`);
  - the old road actors only after a validated replacement (`roadbld_workflow.py:1494-1505`).
- **Open:** two-Landscape accounting was proven only on the older map a473338f.

## Steps (each with a STOP condition)

1. **Ground release:** per decision 3. STOP if there are unaccounted dirty packages or a forced kill.
2. **Evidence backup (manager):**
   - Copy `Content/Project/Areas/GazaShujaiya`, `Content/Project/Shared/SurfacePainting`, the Rimal MI and the 6 Shujaiya receipts to `Staging/ShujaiyaOrdinaryRun_2026-10-05/Before/`, about 1.2 GB.
   - Record bytes and SHA256 in a MANIFEST.json.
   - STOP if any editor is running.
3. **Road-ledger fix (manager).** This is the one exception to "no manual cleanup", and it needs explicit manager sign-off:
   - Archive a0541fc4.
   - Replace the canonical `ROADBLD_WORKFLOW_STATE.json` with a byte copy of `Staging/ManagedAstra_2026-10-03/ExteriorIntervalStop_20261003T213017494226Z/ROADBLD_WORKFLOW_STATE.json` (7d39f05a: 132 staged paths, 87 bindings).
   - Record "PID33168 discarded" in a separate receipt, because the real run rewrites the ledger at :657.
   - STOP unless an offline replay of `roadbld_workflow.py:684-716` yields exactly 136 + 132 paths with no overlap.
4. **Offline pin check (manager):**
   - Re-hash the seal: 12 modules, init_unreal and 4 support files. Compare against the freeze receipt.
   - Confirm the ground fields: Grass subgraph, MI parent and the Sand normals.
   - Archive the old GENERATION_ACTIVATION, then write a new one pinning the hashes and both scripts.
   - Update AGENTS.md, CURRENT_STATE.md and STATUS.txt.
5. **Fresh paused startup (operator):**
   - Run `launch_editor.ps1 -AreaMap <Shujaiya> -ExpectedMapSha256 … -ExpectedManifestSha256 … -ExpectedProfileSha256 … -ManagerThreadId … -OperatorThreadId …`, then the inspection script.
   - Expected:
     - 12 sealed modules loaded;
     - dirty [], paused, autoCook/autoBake/autosave off, callbacks 0;
     - all 5 RoadBLD flags false; licence true;
     - table f6fff4f9 with 1223 rows;
     - 1 HoudiniAssetActor;
     - for run1: the expected 2 Landscapes, 136 ∪ 132 road actors and 0 unaccounted.
   - Never call `geocity_roadbld_workflow.preflight()`.
   - STOP on any failure: close in order, and do not retry in the same process.
6. **Activation (manager):**
   - Append `OWNER=CODEX_MANAGED_SYSTEMS_TASK4 manager_thread_id=… operator_thread_id=… assigned_editor_PID=<new> map=<Shujaiya> activation=MANAGER_ACTIVATED`.
   - Never run the menu under OWNER=NONE: it self-issues a lease (`editor_action.py:243-249`).
7. **Run1 (operator):**
   - Snapshot the 4 live ledgers.
   - Run Tools > "GeoCity: Generate / Regenerate Current Area" (`editor_action.py:272`).
   - Watch WORKFLOW_STATE.json only. STOP points:
     - **Cook:** catalog ≠ f6fff4f9, output not exactly 5 meshes / 1 Landscape / 1 instancer, or any unsupported pad.
     - **Roads:** authorities disagree.
     - **Bake:** a timeout, a count mismatch or more than 1 Landscape.
   - On failure: no retry, no manual Bake, no Save All. Quit only under an explicit manager no-save authorization, after an exact dirty inventory.
8. **Close and reopen1:**
   - Confirm dirty [], then quit_editor() and write OWNER=NONE.
   - Copy run1's ROADBLD_DELIVERY, ROADBLD_WORKFLOW_STATE, HDA_CATALOG_RECEIPT and LAST_SUCCESSFUL to `Before/run1/`. Run2 overwrites them.
   - Re-pin, then repeat step 5 expecting 1 Landscape and the delivery's owned road actors.
9. **Run2:** take a new MANAGER_ACTIVATED lease and run the same command with unchanged inputs. The STOP points are those of step 7.
10. **Reopen2 and the image:**
    - Repeat step 8.
    - Take one wide Lit image with the reviewed helper. STOP if the view mode is not VMI_LIT or the dirty set changes.
    - Final orderly close, then OWNER=NONE.

## Pass criteria (from receipts and the inspection script, never stdout)

- **Run1:**
  - LAST_SUCCESSFUL shows `baked_saved_verified`, the new PID, catalog f6fff4f9 and 1223 rows.
  - 0 unsupported pads.
  - ROADBLD_DELIVERY shows `native_generated_saved_verified`, and old revision 20261003T203730573110 appears in retired_failed_generations.
- **One Landscape:** the assert at :879 passed, AND the reopen inspection shows exactly 1. The receipt's landscape_count is a constant, so do not use it.
- **Reopen:**
  - dirty [], 1 HoudiniAssetActor;
  - road actors = the delivery's owned_actor_paths;
  - all actors = baked + road + preserved non-generated.
- **Run2:**
  - pads, road count, per-mesh instance counts, mesh and material families, and total actors all equal run1;
  - no run1 actor remains.
- **Always:**
  - the 87 candidate hashes and the hold rows are unchanged;
  - no writes outside Areas/GazaShujaiya, the master and GrassType, and the Staging receipts (diff against Before/MANIFEST).
- **Visual acceptance** is Aviv's alone.

## Not in scope

- Any code change or reseal. This includes the weak OWNER=NONE menu path and the missing early road preflight.
- Rimal generation.
- The wider multi-view visual review.
- Approving or deleting the 87 candidates.
- Releasing holds.
- Cleaning Cook packages.
- Restores.
- Linear.

## Critical files

- `Content/Python/`: geocity_editor_action.py, geocity_bank_workflow.py, geocity_roadbld_workflow.py, geocity_roadbld_landscape.py, geocity_landscape_workflow.py.
- `Staging/SystemCompletion_2026-10-04/`: launch_editor.ps1, geocity_runtime_manifest.json.
- `Staging/ModelBank/EDITOR_OWNER.txt`.
- `Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/`: AREA_PROFILE, ROADBLD_WORKFLOW_STATE, ROADBLD_DELIVERY, WORKFLOW_STATE, LAST_SUCCESSFUL_WORKFLOW_STATE (.json).
- `Staging/ManagedSystemsAstra_2026-10-04/`: GENERATION_ACTIVATION, BANK_ACTIVATION, ASSIGNMENTS, USER_STOP_STATUS_REPORT_2026-10-04.txt.

## Verification

- **Before launch:** steps 3-4 pass offline, and the manager signs the freeze receipt and the activation.
- **During runs:** watch WORKFLOW_STATE phases only.
- **At each reopen:** an independent reviewer compares the inspection receipt with the previous run's receipts.
- **At the end:** re-hash the 87 candidates, the holds, the seal and the Before/MANIFEST scope, and give Aviv the image path.


## Baseline change (Aviv, 2026-10-05 evening)
- New baseline ratified: native HDA f407976c, Shujaiya profile 6128dc93 (registry ff6e8879, 18 modular families enabled, EpicResident2K normal overrides), ground master/MI as saved by the 16:11Z run. The prepare() normal-mismatch blocker (decision 1) is therefore resolved by the profile; re-pin all hashes at Freeze.
- Proven by the 16:11Z cook (PID10460): 398/398 buildings, 11,508 instances (6,677 modular). Failed at road-phase start: PermissionError(13) — see Incident_01a10c77_2026-10-05/PERMISSION_ERROR_DIAGNOSIS.md; fix the file/permission cause, not code.
- Still required before run1: close PID10460 WITHOUT saving (manager), OWNER=NONE, ASSIGNMENTS.json manager id -> Claude session, road-ledger reconciliation (step 3), freeze receipt with the new pins, Grass decision (profile still forces 0.15 via prepare(); Aviv wants no grass yet).
- Pass criteria add: modular instance count and per-family counts equal between run1 and run2; 1 Landscape; no duplicates.

- Roads: profile 6128dc93 has roadbld_workflow.enabled=false (changed from true by chat 01a10c77). Aviv decided (2026-10-05 evening) to re-enable RoadBLD roads for the full run; manager sets enabled=true at Freeze with the editor closed and re-pins the profile hash. The failed-start cause (file lock from a monitor) is not a code or permission issue; monitors poll mtime/size only.
