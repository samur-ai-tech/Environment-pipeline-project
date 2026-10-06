# BLOCKED: excluded from the DELETE lists (Consolidation 2026-10-06)

Prepared by the delete-plan review on 2026-10-06, about 16:50-17:10Z. Nothing was deleted. MEASURED unless marked.
UP = `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline`, PE = `C:/Users/USER/Documents/Pipeline Environment`. Sizes are `du -sm` (MB).

Rules applied (details in SUMMARY.md, "Method"):
- Staging and PE folders (all lists): any hit for the folder name in the brief's grep scope that refers to that folder blocks it. The scope is the Shujaiya `AREA_PROFILE.json`, the 11 registries, `Content/Python/*.py`, the top-level `*.ps1|*.py|*.json` of `SystemCompletion_2026-10-04`, and `ShujaiyaOrdinaryRun_2026-10-05/**/*.json|*.py`. Files with "state" in a `.json` name were not opened.
- Content packages: a package is blocked if it is in the Shujaiya closure, if the profile or a registry chain names it, or if any package that stays references it (a reverse check over all 10,116 Content packages, iterated to a fixpoint).
- Hold ids (H0013, H0907, H0051, H0958, H0094): a file or folder with a hold id in its name stays. So does any folder that directly contains such a file; that folder is kept whole.

## 1. Blocked by a reference hit (Staging and PE folders)

### `UP/Staging/ModelBank/Iran_38196167_46086167_4km` (list 01, 1 MB)

8 citing line(s): 1 in code, 7 in records.

- `UP/Staging/SystemCompletion_2026-10-04/CAPACITY_INTEGRATION.json:5` (record): `..."C:\\Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ModelBank\\Iran_38196167_46086167_4km\\AREA_PROFILE.json", "profile_sha256...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/PRODUCTION_SNAPSHOT_2026-10-05T153223Z.json:15` (record): `...: "2026-10-04T18:18:12Z" }, "iran_profile": { "path": "Staging/ModelBank/Iran_38196167_46086167_4km/AREA_PROFILE.json", "sha256": "0...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/IranRun_20261006/LEDGER_MTIMES_BEFORE.json:2` (record): `...{ "Staging/ModelBank/Iran_38196167_46086167_4km\\AREA_PROFILE.json": [ 1791112699.03...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/S1_Prep/s1_verify.py:95` (code): `...ermanentIntegration_2026-10-02/AREA_PROFILE.json', 'Iran': 'Staging/ModelBank/Iran_38196167_46086167_4km/AREA_PROFILE.json'} VENDOR = ('/Game/MW...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/S1_Prep/receipts/VERIFY_s1_shuj_baseline_r001_23156.json:44` (record): `... "C:\\Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ModelBank\\Iran_38196167_46086167_4km\\AREA_PROFILE.json", "sha256": "004...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/S1_Prep/receipts/VERIFY_s1_shuj_baseline_r002_23156.json:44` (record): `... "C:\\Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ModelBank\\Iran_38196167_46086167_4km\\AREA_PROFILE.json", "sha256": "004...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/S1_Prep/receipts/VERIFY_s1_shuj_baseline_r003_16824.json:44` (record): `... "C:\\Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ModelBank\\Iran_38196167_46086167_4km\\AREA_PROFILE.json", "sha256": "004...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Tools/receipts/OFFLINE_LEDGER_SUMMARY.json:105` (record): `..."C:\\Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ModelBank\\Iran_38196167_46086167_4km\\AREA_PROFILE.json", "C:\\Users\\U...`

### `UP/Staging/Iran_4km_2026-10-04` (list 01, 1875 MB)

1 citing line(s): 0 in code, 1 in records.

- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/IranRun_20261006/RESULT_IRAN_20261006.json:11` (record): `...9:07Z OWNER=NONE released_phase=baked_saved_verified" }, "ledger": "Staging/Iran_4km_2026-10-04/LAST_SUCCESSFUL_WORKFLOW_STATE.json (ph...`

### `UP/Staging/ModelBank/PermanentIntegration_2026-10-02` (list 02, 772 MB)

28 citing line(s): 1 in code, 27 in records.

- `UP/Staging/SystemCompletion_2026-10-04/ASSIGNMENT.json:22` (record): `.../ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json", "Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json" ], "native_are...`
- `UP/Staging/SystemCompletion_2026-10-04/STOP_HANDOFF.json:58` (record): `.../ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json", "Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json" ], "awaiting_m...`
- `UP/Staging/SystemCompletion_2026-10-04/STOP_HANDOFF.json:149` (record): `...C:\\Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ModelBank\\PermanentIntegration_2026-10-02\\AREA_PROFILE.json", "sha256": "...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/Before_ASSIGNMENTS_da8fc0a6.json:129` (record): `...odelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json", "Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json" ], "manage...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/Before_RimalProfile_e136df32_20261005T195927Z.json:23` (record): `...Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ModelBank\\PermanentIntegration_2026-10-02\\HDA_CATALOG_RECEIPT.json", "workflo...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/Before_RimalProfile_e136df32_20261005T195927Z.json:24` (record): `...Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ModelBank\\PermanentIntegration_2026-10-02\\WORKFLOW_STATE.json", "procedural_m...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/Before_RimalProfile_e136df32_20261005T195927Z.json:26` (record): `...Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ModelBank\\PermanentIntegration_2026-10-02\\BUILD_STATE.json", "instance_materi...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/DECISION_HYBRID_20261006.json:18` (record): `...bab88207dbaa340a8afc5b2c5a2e2a6544564fadecde07d979e3fd014", "Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json": "492b9ac54fc3e00d90...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/PRODUCTION_SNAPSHOT_2026-10-05T153223Z.json:10` (record): `..."2026-10-05T15:29:16Z" }, "rimal_profile": { "path": "Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json", "sha256": "b...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/RATIFICATION_B2.json:25` (record): `...1e193e0c9fd0edb0478b39" }, "rimal_profile": { "path": "Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json", "sha256": "e...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/RIMAL_PROFILE_REPIN_20261005T195927Z.json:3` (record): `...{ "utc": "20261005T195927Z", "file": "Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json", "before_sha256":...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/Before/ASSIGNMENTS.json:129` (record): `...odelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json", "Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json" ], "manage...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/S1_Prep/plan_out.json:309` (record): `...bdf0005bbb5b4b7ede85269c0d203beca361e193e0c9fd0edb0478b39", "Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json": "8711caceac69324f73...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/S1_Prep/plan_out.json:426` (record): `...0d203beca361e193e0c9fd0edb0478b39" }, { "file": "Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json", "rev": "b1...`
- ... and 14 more (full list: scratchpad `dp_grep_hits.json`)

### `PE/Houdini/GeoCity_city_v015_PermanentBank/revisions/20261005_modular_source_families_v001` (list 04, 4 MB)

2 citing line(s): 0 in code, 2 in records.

- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/BankEditorInspection_2026-10-05/INSPECTION.json:2600` (record): `...e Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank/revisions/20261005_modular_source_families_v001 (hdalc b5ab917a..., module 616e2512...,...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/DECISION_LET_RUN_FINISH.json:17` (record): `...6:19:23Z", "decision": "RATIFY: keep the native HDA f407976c (derivative 20261005_modular_source_families_v001 reimported), the Shujaiya AREA_PROFILE...`

### `UP/Staging/ManagedAstra_2026-10-03` (list 05, 1561 MB)

12 citing line(s): 2 in code, 10 in records.

- `UP/Staging/SystemCompletion_2026-10-04/ASSIGNMENT.json:14` (record): `...aging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json", "Staging/ManagedAstra_2026-10-03/v3_fresh_owner_20261004.py", "Cont...`
- `UP/Staging/SystemCompletion_2026-10-04/STARTUP_REPAIR.json:6` (record): `...r": "C:\\Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ManagedAstra_2026-10-03\\v3_fresh_owner_20261004.py", "sourc...`
- `UP/Staging/SystemCompletion_2026-10-04/STOP_HANDOFF.json:52` (record): `...aging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json", "Staging/ManagedAstra_2026-10-03/v3_fresh_owner_20261004.py", "Cont...`
- `UP/Staging/SystemCompletion_2026-10-04/STOP_HANDOFF.json:139` (record): `...e": "C:\\Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ManagedAstra_2026-10-03\\v3_fresh_owner_20261004.py", "s...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/LEDGER_RECONCILIATION.json:3` (record): `...e": "C:\\Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ManagedAstra_2026-10-03\\ExteriorIntervalStop_20261003T21301749...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/prepare_run.py:42` (code): `...edger=profile_path.parent/'ROADBLD_WORKFLOW_STATE.json' candidate=ROOT/'Staging/ManagedAstra_2026-10-03/ExteriorIntervalStop_20261003T213017494...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Tools/offline_ledger_summary.py:21` (code): `...odelBank/GazaShujaiyaIntegration_2026-10-02' CANDIDATE_LEDGER = ROOT / 'Staging/ManagedAstra_2026-10-03/ExteriorIntervalStop_20261003T213017494...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Tools/receipts/OFFLINE_LEDGER_SUMMARY.json:839` (record): `...h": "C:\\Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ManagedAstra_2026-10-03\\ExteriorIntervalStop_20261003T21301749...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Tools/receipts/OFFLINE_LEDGER_SUMMARY.json:871` (record): `...e": "C:\\Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ManagedAstra_2026-10-03\\FRESH_fresh_dispatch_retry_20261003T20...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Tools/receipts/OFFLINE_LEDGER_SUMMARY.json:873` (record): `...e": "C:\\Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ManagedAstra_2026-10-03\\FRESH_LICENSE_CONTINUATION_20261003T20...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Tools/receipts/OFFLINE_LEDGER_SUMMARY.json:874` (record): `...e": "C:\\Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ManagedAstra_2026-10-03\\EXPLICIT_CALLBACK_CONTINUATION_2026100...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Tools/receipts/OFFLINE_LEDGER_SUMMARY.json:877` (record): `...e": "C:\\Users\\USER\\Documents\\Unreal Projects\\Environmentpipeline\\Staging\\ManagedAstra_2026-10-03\\GROUNDING_ONLY_RESUME_20261003T2124001...`

### `UP/Staging/NativeUnrealAssetSupply_2026-10-04` (list 05, 250 MB)

2 citing line(s): 0 in code, 2 in records.

- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/Before_ASSIGNMENTS_da8fc0a6.json:145` (record): `...l_supplier": "01a1075c-313d-7133-9bc5-580cb2681f9b GPT-6 Astra owns Staging/NativeUnrealAssetSupply_2026-10-04 only. Adds installed Unreal/Epic/store/...`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/Before/ASSIGNMENTS.json:145` (record): `...l_supplier": "01a1075c-313d-7133-9bc5-580cb2681f9b GPT-6 Astra owns Staging/NativeUnrealAssetSupply_2026-10-04 only. Adds installed Unreal/Epic/store/...`

### `UP/Staging/ProceduralCityRegeneration_2026-10-05` (list 05, 273 MB)

1 citing line(s): 0 in code, 1 in records.

- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/DECISION_LET_RUN_FINISH.json:64` (record): `...3:25Z.", "astra_inspection": "Aviv asked an Astra chat; it wrote Staging/ProceduralCityRegeneration_2026-10-05 (CITY_BEFORE/AFTER/REOPENED/FINAL, gall...`

Notes on the blocked Iran and Rimal profile folders (INFERRED from reading the code; nothing was run):
- `UP/Staging/ModelBank/Iran_38196167_46086167_4km/` and `UP/Staging/ModelBank/PermanentIntegration_2026-10-02/` hold the Iran and Rimal `AREA_PROFILE.json`. The sealed runtime globs `Staging/ModelBank/*/AREA_PROFILE.json` (`geocity_editor_action.py:12-14`; `launch_editor.ps1:44`). It selects the profile whose `map` equals the open world (`geocity_editor_action.py:214-217`), so a profile left behind after its map is deleted does not affect a Shujaiya run.
- Code that cites these folders: `ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/S1_Prep/s1_verify.py:95` (a per-area profile path table). The other hits are records: receipts, backups, the incident and ratification files, and the S1 backup manifest.
- Interpretation used: "not referenced by any kept profile" means the Shujaiya profile. The brief itself names the Iran and Rimal profile folders as delete candidates. Applying the any-hit rule to them is what separates each profile folder from its map.
- **One manager decision per area:**
  - Iran: list 01 together with `Staging/ModelBank/Iran_38196167_46086167_4km/` and `Staging/Iran_4km_2026-10-04/` (the Iran profile's receipt and ledger folder).
  - Rimal: the prepared Rimal set (section 5) together with `Staging/ModelBank/PermanentIntegration_2026-10-02/`.
  - If the manager accepts that the citations are records only, plus the `s1_verify.py:95` table (section 6), each area is deleted as one unit, and no area profile is left pointing at a missing map.

## 2. Blocked by a Content package that stays

- `UP/Content/Developers/USER/ModelBankProof/CatalogTechnicalOnly/S_BankReleaseRow_v2.uasset` (list 03): referenced by `Content/Project/Shared/ModelBank/DT_BankRelease_AllDisabled_v2.uasset`, `Content/Project/Shared/ModelBank/DT_BankRelease_v2.uasset`. These are older catalogs inside `Content/Project/Shared/ModelBank/`, which is a must-stay path. The other two `CatalogTechnicalOnly` packages are in list 03.

## 3. Excluded because the brief conflicts with a must-stay path

- `PE/Archive` (? MB): does not exist. The brief asks to delete all `*_bakN.hdalc`, but it also keeps the v003 and v004 revision folders whole. Owner decision needed. Each folder holds a byte copy of its revision's final hdalc (v003 bak16, v004 bak5; INVENTORY 3.2.A) and unique intermediate states.
- `PE/Houdini/GeoCity_city_v015_PermanentBank/revisions/20261005_procedural_ten_families_v003/backup` (9 MB): inside a must-stay revision folder (brief conflict; excluded). The brief asks to delete all `*_bakN.hdalc`, but it also keeps the v003 and v004 revision folders whole. Owner decision needed. Each folder holds a byte copy of its revision's final hdalc (v003 bak16, v004 bak5; INVENTORY 3.2.A) and unique intermediate states.
- `PE/Houdini/GeoCity_city_v015_PermanentBank/revisions/20261005_procedural_thirty_families_v004/backup` (3 MB): inside a must-stay revision folder (brief conflict; excluded). The brief asks to delete all `*_bakN.hdalc`, but it also keeps the v003 and v004 revision folders whole. Owner decision needed. Each folder holds a byte copy of its revision's final hdalc (v003 bak16, v004 bak5; INVENTORY 3.2.A) and unique intermediate states.

## 4. Kept by the hold rule (inside folders that are otherwise deleted)

- `UP/Content/Developers/USER/ModelBankProof/H0958_MaterialRepair_20260929` (1 MB): hold name
- `UP/Staging/TrackA_Tests/HoudiniCityProof/01_audit/mcp` (1 MB): hold-evidence folder kept whole (directly holds 1 hold-named files, e.g. 001_ref_SM_H0958_CoconutPalm.json)
- `UP/Staging/TrackA_Tests/HoudiniCityProof/03_relaunch/mcp` (1 MB): hold-evidence folder kept whole (directly holds 1 hold-named files, e.g. 003_dirty_SM_H0958_CoconutPalm.json)
- `UP/Staging/TrackA_Tests/HoudiniCityProof/10_measure_session/evidence/mcp` (2 MB): hold-evidence folder kept whole (directly holds 1 hold-named files, e.g. 139_M22_dirty_SM_H0958_CoconutPalm.json)
- `UP/Staging/TrackA_Tests/HoudiniCityProof/11_topic3_readiness_2026-09-28/evidence` (1 MB): hold-evidence folder kept whole (directly holds 1 hold-named files, e.g. h0958_bank_proof_review_2026-09-29.json)
- `UP/Staging/TrackA_Tests/HoudiniCityProof/GeoCity_request_wiring_UI_2026-09-30` (2 MB): hold-evidence folder kept whole (directly holds 1 hold-named files, e.g. 06_H0094_native_mesh_view.jpg)
- `UP/Staging/Archive/PreFinalVision_2026-09-29/Bank_WorkOrders` (1 MB): hold-evidence folder kept whole (directly holds 2 hold-named files, e.g. H0958_MATERIAL_REPAIR_PROOF_BRIEF_2026-09-29.EN.md)
- `UP/Staging/Archive/PreFinalVision_2026-09-29/Reports/ReportTranslations_2026-09-29/Drafts/A/Staging/ModelBank` (1 MB): hold-evidence folder kept whole (directly holds 1 hold-named files, e.g. H0958_MATERIAL_REPAIR_PROOF_BRIEF_2026-09-29.EN_DRAFT.md)
- `UP/Staging/ModelBank/Connection_2026-09-30/native_assets` (14 MB): hold-evidence folder kept whole (directly holds 15 hold-named files, e.g. 709_current_Project__Shared__Bank_ME_v3__Buildings__SM_H0013_Building_04__get_asset_class.json)
- `UP/Staging/ModelBank/Inspection_2026-09-28_Astra/Native_Visual_Run_01` (41 MB): hold-evidence folder kept whole (directly holds 24 hold-named files, e.g. 01_H0907_search__0.jpg)
- `UP/Staging/ModelBank/Inspection_2026-09-28_Continuation/Native_Visual_Run_02` (29 MB): hold-evidence folder kept whole (directly holds 22 hold-named files, e.g. 02_H0013_identity__0.jpg)
- `UP/Staging/ModelBank/Inspection_2026-09-29_Astra_Bounds` (4 MB): hold-evidence folder kept whole (directly holds 6 hold-named files, e.g. 01_H0051_build_scale__0.jpg)
- `UP/Staging/ModelBank/Inspection_2026-09-29_Astra_Closure/mcp` (1 MB): hold-evidence folder kept whole (directly holds 6 hold-named files, e.g. 001_deps_SM_H0907_Arab_x3_fbx.json)
- `UP/Staging/ModelBank/Inspection_2026-09-29_Astra_Extensions_Retry` (6 MB): hold-evidence folder kept whole (directly holds 3 hold-named files, e.g. 001_H0907.json)
- `UP/Staging/ModelBank/Inspection_2026-09-29_Astra_Prep` (9 MB): hold-evidence folder kept whole (directly holds 1 hold-named files, e.g. H0958_SOURCE_ALPHA_READOUT.json)
- `UP/Staging/ModelBank/Inspection_2026-09-29_Astra_Tier1` (15 MB): hold-evidence folder kept whole (directly holds 113 hold-named files, e.g. 01_H0907_identity__0.jpg)
- `UP/Staging/ModelBank/H0958_MaterialRepair_Proof_20260929/` (12 MB) and `UP/Staging/ModelBank/ME/` (5855 MB, which holds the H0013 sources `ME/Sources` and their manifest `MANIFEST_ME.csv`) were never candidates.

## 5. Sky-operator conflict: GazaRimal is BLOCKED (whole list 02)

Timeline (MEASURED):

- About 16:42Z: `UP/Staging/ReusableSky_2026-10-06/Stage3/ASSIGNMENT.json` assigned the Rimal map `/Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration` to the ReusableSky operator (thread 01a1118e, manager cc37d4d2), on PID 29940. That PID was the only UnrealEditor running. `Stage3/RECOVERY_REQUEST.txt:1-3` reported it hung.
- 17:00:06Z: the operator released the map after a replacement editor, PID 9828, also hung (`"status": "BLOCKED_RELEASED"`, `"closed_utc": "2026-10-06T17:00:06.7634867Z"`). `tasklist` at 17:02:51Z found no UnrealEditor. The Rimal map hash at 17:04:51Z was still 76445808.
- **17:09:49Z: the operator resumed on Rimal.**
  - `Stage3/ASSIGNMENT.json:2` `"authority": "MANAGER_CC37D4D2_STAGE3_APPROVE_BOUNDED_RESUME"`; `:3` `"status": "MANAGER_RESUME_PREFLIGHT_PASSED"`; `:6` `"assigned_editor_PID": 38224`; `:7` the Rimal map; `:29` `"created_utc": "2026-10-06T17:09:49.9880067Z"`; `:30` `"editor_live": true`.
  - `Stage3/STATUS.txt:1` says: "Dedicated editor38224 starting on original Rimal; DO NOT DELETE RIMAL until Stage3 release."
  - Process check at 17:10:44Z: PID 38224 is `UnrealEditor.exe ... Environmentpipeline.uproject /Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration -NoAutoSave -NoSaveConfig`, created 20:09:49 local.

**Result: `DELETE_02_rimal.txt` is empty.** The Rimal set was prepared and reference-checked with Rimal treated as a delete candidate: no package that stays references any of these, and none is in the Shujaiya closure. Run it only after the Sky operator releases Stage 3 and no editor is running. Re-run `dp_content.py` and `sanity_check.py` first, because the Sky task may save the Rimal map again. Prepared lines (1474 MB):

- `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Content/Developers/USER/HoudiniCityProof/Materials/M_GeoCity_VertexColorPreview.uasset`
- `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Content/Project/Areas/GazaRimal`
- `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Content/Project/Shared/SurfacePainting/HDA/GeoCity_city_v007_SurfacePainting_v002.uasset`
- `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Content/Project/Shared/SurfacePainting/M_StarterSurfaceBank.uasset`
- `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Content/Project/Shared/SurfacePainting/MI_StarterSurfaceBank_Default.uasset`
- `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/PermanentIntegration_2026-10-02`: also blocked by its own reference hits (section 1).

Why the three SurfacePainting packages are in this set: the old Rimal map `Content/Project/Areas/GazaRimal/L_GazaRimal_SurfacePainting_20261002.umap` references `HDA/GeoCity_city_v007_SurfacePainting_v002`, which references `MI_StarterSurfaceBank_Default`, which references `M_StarterSurfaceBank`. `M_GeoCity_VertexColorPreview` is referenced by the live Rimal map. All four can go only together with Rimal.

Consequence (MEASURED): the saved Rimal map references `/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky`. It is the only map where the reusable sky is placed. The sky assets (`Content/Project/Shared/Atmosphere/`) are kept; no list touches them.

**While PID 38224 runs, no Content deletion from any list should be executed** (AGENTS: one editor writer; deleting packages under a live editor).

## 6. Live-tool coupling: a precondition for lists 01 and 02 (MEASURED from code)

- `ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/S1_Prep/s1_verify.py`:
  - It reads all three profiles unconditionally (`:93-95` the `PROFILES` table; `:646-650` the loop with `read_text`).
  - It indexes the Rimal profile for every run (`:669-670`).
  - It has never-waivable Iran checks (`:127-129`; `:600` "iran_statistics_equal is required").
  - It stops working for every area, Shujaiya included, once the Rimal or Iran profile goes. Removing Iran content may already break the Iran checks (INFERRED).
- `S1_Prep/s1_backup.py`: its copy set includes the Rimal child MI and the Rimal map (`:104`, `:106`). It refuses on a missing copy-set package (`:414`).
- `S1_Prep/s1_capture.py`: keyed by area (`:69`, `:386`), so it is not affected for Shujaiya.
- These are tools of the rejected S1 v1 route. The current Hybrid plan does not call them: `hybrid_build_master.py:56` only names `s1_verify.py` as a code pattern. INVENTORY 3.9.E classes them LIVE only conservatively.
- The Hybrid scripts list the Rimal child MI in `PROTECTED_FILES`. A missing file hashes to `None`, and the check compares before and after within one run (`hybrid_assign_and_save.py:145-146,271,658`; `hybrid_build_master.py:172-173,339,866`, where only the texture files must exist). Deleting Rimal therefore does not break the Hybrid run.
- **Precondition:** executing list 01 or 02 retires `s1_verify.py` and `s1_backup.py`, unless they are patched first. The manager accepts this explicitly.

## 7. Hits not counted (verified name collisions)

- `PE/Houdini/GeoCity_city_v007_SurfacePainting_v002`: the hit `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/BEFORE_MANIFEST.json:948` names the Content file `Content\\Project\\Shared\\SurfacePainting\\HDA\\GeoCity_city_v007_SurfacePainting_v002.uasset` (a RunExisting backup manifest), not the PE folder.
- `PE/Houdini/GeoCity_city_v013_AllSurfacePalette`: the hit `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/BEFORE_MANIFEST.json:949` names the Content file `Content\\Project\\Shared\\SurfacePainting\\HDA\\GeoCity_city_v013_AllSurfacePalette.uasset` (a RunExisting backup manifest), not the PE folder.
- `PE/Houdini/GeoCity_city_v014_AllSurfacePaletteFix`: the hit `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/BEFORE_MANIFEST.json:950` names the Content file `Content\\Project\\Shared\\SurfacePainting\\HDA\\GeoCity_city_v014_AllSurfacePaletteFix.uasset` (a RunExisting backup manifest), not the PE folder.

