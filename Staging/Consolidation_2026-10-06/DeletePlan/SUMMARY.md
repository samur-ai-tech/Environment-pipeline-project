# Delete plan summary (Consolidation 2026-10-06)

Prepared on 2026-10-06, about 16:50-17:10Z, read-only. **Nothing was deleted.** No editor, Houdini, project script or MCP tool was used. Ledgers (`*state*.json`) and `Saved/Logs` were not opened. MEASURED unless marked.
Owner decision being implemented: Aviv, 2026-10-06 about 16:40Z. Keep only GazaShujaiya (`/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration`, sha 4efebdfb, unchanged at 17:04:51Z), the bank and the project. Delete Iran, GazaRimal, the old maps, the old Houdini versions and the old chat folders. Vendor packs stay.

## 1. Lists

| File | Scope | Entries | Files under them | MB (du -sm) |
|---|---|---:|---:|---:|
| `DELETE_01_iran.txt` | Iran | 6 | 223 | 1434 |
| `DELETE_02_rimal.txt` | GazaRimal: BLOCKED, empty (BLOCKED.md section 5) | 0 | 0 | 0 |
| `DELETE_03_oldmaps.txt` | Old maps and leftovers | 49 | 828 | 294 |
| `DELETE_04_pe_houdini.txt` | PE old Houdini versions (PE/Archive and *.blend1 already deleted, see below) | 56 | 846 | 328 |
| `DELETE_05_staging.txt` | Old chat folders under Staging | 282 | 24706 | 1983 |
| `OPTIONAL_lifecycle_cook.txt` | Optional: stale Shujaiya lifecycle outputs (separate decision) | 176 | 752 | 848 |
| **DELETE_01-05 total** | | **393** | **26603** | **4039** |

- Line format: one absolute path per line, forward slashes, UTF-8 without BOM, LF line endings. A folder line means the whole folder. No line repeats or nests inside another line, within or across lists. Nested lines were removed before `du`, so the totals are not double-counted.
- List 04 has 56 folder lines: the legacy generators, the proof folders, PB revisions r001-r016 and v002, and `PB/backup`. It has 0 `*.blend1` lines.
- Already deleted by the executor while this plan was being prepared, so dropped from list 04: `PE/Archive/` (731 MB) and all 166 `PE/ModelBank/**/*.blend1` files (1,118 MB). See `Staging/Consolidation_2026-10-06/EXECUTION_LOG.md`, Phase B, steps B1 and B2, logged at 17:10Z; they were gone from disk at 17:06:58Z. An earlier version of this plan had listed both; its reference check had found 0 hits for them.
- `OPTIONAL_lifecycle_cook.txt` breaks down as: the Cook folder `311CD685` (88 packages), 4 Bake leftovers, 32 stale LayerInfos (the current `1428_1804_0` set is in the closure and is not listed), and 139 stale ClippedGeometry run folders. Every package in it is outside the converged closure. Excluded: the two runs the map references, `..._141625759113` and the 87-candidate run `20261003T203730573110_212401627821`. These outputs are owned by the lifecycle. The INVENTORY recommends removing them through the lifecycle's own cleanup (5.1, 5.3), so this list is not executed without a separate decision.
- Blocked or excluded items, with the file and line that prove each one: `BLOCKED.md`.

## 2. Shujaiya closure

- Root scan: `grep -a -o '/Game/[A-Za-z0-9_/.-]*' L_GazaShujaiya_BankIntegration.umap | sort -u` gives 530 unique strings, which are 392 root packages after cutting at the first `.`. The map is not World Partition: no `__ExternalActors__` or `__ExternalObjects__` folder exists for GazaShujaiya (or for GazaRimal or Iran).
- Expansion: each referenced package's own `.uasset`/`.umap` was scanned the same way, with a Python byte regex identical to the grep over all 10,116 Content packages (cache `content_refs.json`).
- **Closure at the 6-round cap: 2931 package files.** By round: r0 +384, r1 +1181, r2 +532, r3 +750, r4 +57, r5 +18, r6 +9.
- The closure did not converge at round 6. It converges at round 8 with **2934** files (+3 in round 7, 0 in round 8). 19 `/Game` strings are folder prefixes and 164 resolve to no file (dangling names: vendor-internal names, the six H0017/H0019 meshes, and the truncated `/Game/Project/Shared/RoadBLD/Materials/MI_`).
- Extended keep closure (the map plus the profile's 185 `/Game` values, 948 `/Game` values from the 11 registries and their 116 referenced JSON files, and 8 from `Content/Python`): **3849 files**, converged at round 8. This set is part of `must_stay_paths.tsv`.
- No package in any DELETE or OPTIONAL list is in any of these closures (checked against the converged sets, not only the capped one).
- Brief correction: `M_Landscape_GazaRimal` is `/Game/Project/Shared/Landscape/M_Landscape_GazaRimal`, not a package in the Rimal area. It is in the closure and stays; no carve-out is needed.

## 3. Reference-check method and result per list

- **Content packages (lists 01, 02, 03, OPTIONAL):**
  - (a) not in the converged or extended closure;
  - (b) not named by the Shujaiya profile, the registries, the registry-referenced JSON files, or `Content/Python`;
  - (c) a reverse check: every package that stays, including vendor packs, the bank, `Supply/`, `AreaScopes/` and `Atmosphere/`, was scanned for each candidate's package path, iterated to a fixpoint.
  - Result: 1 package blocked (`S_BankReleaseRow_v2`; the older bank catalogs use it). No package that stays references any Iran, Rimal or old-map candidate, `AreaScopes/DT_Iran_*` included (it names only itself).
- **Staging and PE folders (lists 01, 02, 04, 05):** the brief's grep scope (327 files).
  - Fixed-token `grep -obF` was used, with each hit verified in a byte window by a regex with name boundaries.
  - Generic names were anchored to their parent: `Staging/Archive`, `Staging/Operator`, `ModelBank/<name>`, `revisions/r0xx`, `<generator>/backup`, `Pipeline Environment/Archive`.
  - Result: 7 folders blocked (BLOCKED.md section 1). 3 hits were name collisions (BLOCKED.md section 7).
  - Positive controls:
    - `grep -nF AppearanceRepair_2026-10-03 Content/Python/*.py` finds `geocity_roadbld_clip.py:268,270` and `geocity_roadbld_grounding.py:1309`; that folder is kept.
    - The token method itself produced the expected hits, such as `ManagedAstra_2026-10-03` in `RunExisting_20261005/prepare_run.py:42` and `Tools/offline_ledger_summary.py:21`.
- **/Game path strings of Content candidates found in the grep scope:** informational, not blocking under the brief's Content rule. They appear in records and S1/Hybrid scripts in `ShujaiyaOrdinaryRun`, and in `SystemCompletion_2026-10-04/launch_editor.ps1:3`. That line is the sealed launcher's `ValidateSet`, which lists the Shujaiya and Rimal maps; after Rimal is deleted only the Shujaiya option works, which is the intent. The S1 tools (`s1_verify.py`, `s1_capture.py`, `s1_backup.py`) and the Hybrid scripts have per-area branches for GazaRimal. Those branches stop working with Rimal, but the GazaShujaiya branches do not use them (INFERRED from the per-area tables).

- **Limit: ledgers not read.** The runtime reads the profile ledgers (`WORKFLOW_STATE.json`, `LAST_SUCCESSFUL_WORKFLOW_STATE.json`, `ROADBLD_WORKFLOW_STATE.json`, `BUILD_STATE.json`; `geocity_editor_action.py:64-75,116-127`). These were not opened, per the brief. A path into a deleted folder recorded only in a ledger is unchecked. For the Shujaiya ledgers such paths are expected to be Shujaiya `/Game` packages (INFERRED), and every Shujaiya area package that stays is outside all DELETE lists.
- **Live-tool coupling:** `s1_verify.py` and `s1_backup.py` read the Rimal and Iran profiles and content unconditionally. Executing list 01, or the blocked Rimal set later, retires them unless they are patched (BLOCKED.md section 6). The Hybrid scripts are not affected.

## 4. Sky operator

- Map: `/Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration`.
- PIDs: 29940 (hung) at the start of the review, then 9828 (hung). It released at 17:00:06Z, then **resumed at 17:09:49Z with PID 38224** (`ReusableSky_2026-10-06/Stage3/ASSIGNMENT.json:2-3,6-7,29-30`). PID 38224 was running at 17:10:44Z.
- `Stage3/STATUS.txt:1`: "DO NOT DELETE RIMAL until Stage3 release".
- **GazaRimal is BLOCKED.** `DELETE_02_rimal.txt` is empty; the prepared, reference-checked Rimal set is in BLOCKED.md section 5.
- While this editor runs, no Content deletion from any list should be executed.

## 5. Sanity check (script `sanity_check.py` in this folder; input `must_stay_paths.tsv`, 4070 entries)

- Must-stay entries:
  - every MUST-STAY path from the brief;
  - the 22 absolute paths in the Shujaiya profile;
  - the 116 registry-referenced files and the 11 registries;
  - the runtime-read paths (`geocity_editor_action.py:26-30`, `geocity_bank_workflow.py:505-507` decision receipt, `geocity_roadbld_clip.py:266-271` and `geocity_roadbld_grounding.py:1309` into AppearanceRepair, the seal files `geocity_runtime_guard.py:123-182`);
  - all 3849 files of the extended closure;
  - all vendor packs, `Content/Project/Shared/Atmosphere`, and the PE keep set.
- Comparison: case-insensitive, on whole path components. Every folder line is walked for hold ids.
- Named carve-outs (from the brief): `UP/Content/Project/Shared/ModelBank/HDA/GeoCity_city_v015_4km.uasset` lies inside the must-stay `ModelBank/**`, but the brief names it explicitly as an Iran delete candidate. `PE/ModelBank/**/*.blend1` is excluded from the PE/ModelBank keep by the brief.
- A negative test was also run (a copy of the script in the scratchpad, with deliberately bad lines). It correctly failed on:
  - the GazaShujaiya folder and `Staging/ModelBank` (each is an ancestor of a must-stay path);
  - a hold-evidence folder;
  - the PermanentBank HDA and `StarterContent/Maps` (inside a must-stay path);
  - the v003 backup folder;
  - a cross-list nesting.
- It correctly passed the two named carve-outs.

Output of `python sanity_check.py` on the final lists:

```
DELETE_01_iran.txt             lines=6     PASS
DELETE_02_rimal.txt            lines=0     PASS
DELETE_03_oldmaps.txt          lines=49    PASS
DELETE_04_pe_houdini.txt       lines=56    PASS
DELETE_05_staging.txt          lines=282   PASS
OPTIONAL_lifecycle_cook.txt    lines=176   PASS
cross-list duplicate/nested lines: none
must-stay entries checked: 4070
RESULT: PASS
```

## 6. Absolute paths in the Shujaiya profile (`Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json`)

All `C:\Users\USER\...` and `C:/Users/USER/...` values, found by walking every JSON string plus a raw-text regex. 22 unique paths; all exist on disk.

| Path | Profile key(s) | Survives the plan |
|---|---|---|
| `C:/Users/USER/Documents/Pipeline Environment/SourceData/GazaShujaiya/city_source_v1.json` | `.source` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03/ASSIGNMENT.json` | `.appearance_repair_receipt` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03/FACADE_MATERIALS.json` | `.building_assembly_contract.building_style_variants.palettes[].native_parameter_evidence, .normal_material_policy.appear` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03/GROUND_SHADER_REPAIR_20261003T160849345599Z.json` | `.surface_normal_overrides.Sand_01_Normal.receipt_path, .surface_normal_overrides.Sand_02_Normal.receipt_path` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03/INSTANCE_MATERIALS.json` | `.building_assembly_contract.building_style_variants.modules.closed4.dependency_evidence, .building_assembly_contract.bui` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03/NATIVE_VARIETY_MEASUREMENTS.json` | `.building_assembly_contract.building_style_variants.modules.closed4.native_measurement_source, .building_assembly_contra` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03/ROADBLD_CLIP_GazaShujaiya_20261003T141625759113Z.json` | `.road_provider_contract.clipping_report.receipt` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AssetBankOperator_2026-10-06/Activation/DECISION.json` | `.release.decision_receipt` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/BankIntegration_2026-10-04/NORMAL_CONFIGURATION_f6fff4f9759af2db.json` | `.normal_asset_policy.bank_integration_receipt` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ManagedExecution_2026-10-02/Task2/NORMAL_ASSET_CONFIGURATION.json` | `.normal_asset_policy.selection_receipt` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ManagedExecution_2026-10-02/Task3/NORMAL_MATERIAL_CONFIGURATION.json` | `.normal_material_policy.receipt` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ManagedExecution_2026-10-02/Task5/NORMAL_SCOPE_CONFIGURATION.json` | `.normal_asset_policy.scope_extension_receipt, .normal_material_policy.scope_extension_receipt` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/BUILD_STATE.json` | `.build_state_alias` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/HDA_CATALOG_RECEIPT.json` | `.catalog_receipt` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/WORKFLOW_STATE.json` | `.workflow_receipt` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModularConstruction_2026-10-05/ContractAudit/Registries/8d8622b26107db17c2c14bdd8a8d3a4742c0d3cea9c79aa5244410c0cd67c885.json` | `.building_assembly_contract.source_family_registry_ref.path` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModularConstruction_2026-10-05/Run_20261005/PROFILE_CHANGE.json` | `.surface_normal_overrides.Sand_01_Normal.binding_reconciliation_receipt, .surface_normal_overrides.Sand_02_Normal.bindin` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ModularConstruction_2026-10-05/Run_20261005/ROAD_REPAIR_QUEUE.json` | `.roadbld_workflow.repair_queue_ref` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/RepairExecution_2026-10-03/ASSEMBLY_CONTRACT.json` | `.normal_asset_policy.assembly_contract_receipt` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/RepairExecution_2026-10-03/BUILDING_ASSEMBLY_PATCH.py` | `.building_assembly_contract.implementation_file` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/RepairExecution_2026-10-03/INSTANCE_MATERIALS.json` | `.building_assembly_contract.modules.door.native_measurement_source, .building_assembly_contract.modules.plain1.native_me` | yes |
| `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/RepairExecution_2026-10-03/POLE5_NORMAL_CONFIGURATION.json` | `.normal_asset_policy.repair_receipt` | yes |

The relative path value `Content/Python/geocity_roadbld_workflow.py` (`roadbld_workflow.adapter`) also survives. The registries reference 116 JSON files, all under `PE/ModelBank/Modular_2026-10-04/`, `Staging/BankIntegration_2026-10-04/ModularNative_2026-10-05/` and `Staging/ModularConstruction_2026-10-05/ContractAudit/`. None of them is a `.blend1`, and all survive.

## 7. Candidates listed for information only (not in any DELETE list)

- Loose files in `UP/Staging/ModelBank/` (the brief limits list 05 to subfolders). Each has 0 reference hits in the grep scope. Sizes in MB:
  - `UP/Staging/ModelBank/ARCHIVE_NOTES.md`: 0.00 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_1215_DISPOSITION_MANAGER_REVIEW_2026-09-29.EN.md`: 0.01 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_1215_DISPOSITION_MANAGER_REVIEW_2026-09-29.md`: 0.01 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_1215_DISPOSITION_MERGE_QA_2026-09-29.json`: 0.00 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_1215_DISPOSITION_RECORD_2026-09-29.csv`: 2.64 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_1215_DISPOSITION_RECORD_QA_2026-09-29.json`: 0.00 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_1215_DISPOSITION_REVIEW_2026-09-29.csv`: 2.09 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_ASSETID_REVIEW_LEDGER_2026-10-01.EN.md`: 0.01 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_ASSETID_REVIEW_LEDGER_2026-10-01.csv`: 3.72 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_ASTRA_008_INPUT.csv`: 0.01 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_CANDIDATE_INDEX_2026-09-28.csv`: 4.74 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_CANDIDATE_INDEX_2026-09-29.csv`: 5.42 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_DECISION_SHEET_2026-09-29.EN.md`: 0.02 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_DECISION_SHEET_2026-09-29.md`: 0.02 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_DISTINCT_CANDIDATE_SHORTLIST_2026-10-01.EN.md`: 0.02 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_FIRST_QUALIFICATION_GAP_PACKET_2026-09-29.EN.md`: 0.01 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_FIRST_QUALIFICATION_GAP_PACKET_2026-09-29.md`: 0.01 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_FIRST_QUALIFICATION_QA_2026-09-29.json`: 0.00 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_FIRST_QUALIFICATION_QUEUE_2026-09-29.EN.md`: 0.01 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_FIRST_QUALIFICATION_QUEUE_2026-09-29.csv`: 0.04 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_FIRST_QUALIFICATION_QUEUE_2026-09-29.md`: 0.01 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_INDEX_V4_MERGE_RECEIPT_2026-09-29.json`: 0.93 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_INDEX_V5_BINDINGS_RECEIPT_2026-09-29.json`: 0.00 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_INDEX_V5_SEMANTIC_DIFF_QA_2026-09-29.json`: 0.00 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_INDEX_V6_BOUNDS_RECEIPT_2026-09-29.json`: 0.00 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_INDEX_V7_NATIVE_BATCH_DIFF_QA_2026-09-29.json`: 0.01 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_KNOWLEDGE_TRANSFER_PREPARATION_2026-10-02.md`: 0.02 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_SCHEMA_GAP_AUDIT_2026-09-29.EN.md`: 0.02 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_SCHEMA_GAP_AUDIT_2026-09-29.md`: 0.02 MB, 0 hits
  - `UP/Staging/ModelBank/BANK_SHORTLIST_SOURCE_BYTE_MATCH_DELTA_2026-10-01.EN.md`: 0.00 MB, 0 hits
  - `UP/Staging/ModelBank/CANDIDATE_CATALOG_2026-09-28.EN.md`: 0.02 MB, 0 hits
  - `UP/Staging/ModelBank/CANDIDATE_CATALOG_2026-09-28.md`: 0.02 MB, 0 hits
  - `UP/Staging/ModelBank/CATALOG_TECH_ONLY_IMPORT_2026-09-30.csv`: 0.00 MB, 0 hits
  - `UP/Staging/ModelBank/CATALOG_TECH_ONLY_IMPORT_2026-09-30.md`: 0.00 MB, 0 hits
  - `UP/Staging/ModelBank/CATALOG_TECH_ONLY_REOPEN_READBACK_2026-09-30.csv`: 0.00 MB, 0 hits
  - `UP/Staging/ModelBank/CATALOG_TECH_ONLY_UI_READBACK_2026-09-30.csv`: 0.00 MB, 0 hits
  - `UP/Staging/ModelBank/CATALOG_TECH_ONLY_UI_RECEIPT_2026-09-30.md`: 0.00 MB, 0 hits
  - `UP/Staging/ModelBank/CURRENT_PACK_SELECTION_2026-09-28.csv`: 2.17 MB, 0 hits
  - `UP/Staging/ModelBank/DECISION_REVIEW_ARCHITECTURE_2026-09-29.csv`: 0.92 MB, 0 hits
  - `UP/Staging/ModelBank/DECISION_REVIEW_PROPS_2026-09-29.csv`: 0.71 MB, 0 hits
  - `UP/Staging/ModelBank/DECISION_REVIEW_SURFACE_VEGETATION_2026-09-29.csv`: 0.26 MB, 0 hits
  - `UP/Staging/ModelBank/EXTERNAL_SOURCE_SELECTION_2026-09-28.csv`: 0.66 MB, 0 hits
  - `UP/Staging/ModelBank/FULL_INDEX.csv`: 0.73 MB, 0 hits
  - `UP/Staging/ModelBank/LICENSE_PROVENANCE.md`: 0.00 MB, 0 hits
  - `UP/Staging/ModelBank/MODEL_BANK_RESEARCH_REPORT_2026-09-30.EN.md`: 0.01 MB, 0 hits
  - `UP/Staging/ModelBank/README.md`: 0.00 MB, 0 hits
  - `UP/Staging/ModelBank/RIGHTS_DECISION_PACKET_2026-09-29.EN.md`: 0.02 MB, 0 hits
  - `UP/Staging/ModelBank/RIGHTS_DECISION_PACKET_2026-09-29.md`: 0.02 MB, 0 hits
  - `UP/Staging/ModelBank/RIGHTS_TECH_GAPS_2026-09-28.EN.md`: 0.02 MB, 0 hits
  - `UP/Staging/ModelBank/RIGHTS_TECH_GAPS_2026-09-28.md`: 0.02 MB, 0 hits
  - `UP/Staging/ModelBank/SEMANTIC_CORRECTIONS_PROPOSED_2026-09-29.csv`: 0.53 MB, 0 hits
  - `UP/Staging/ModelBank/SEMANTIC_MINIMAL_PATCH_2026-09-29.csv`: 0.03 MB, 0 hits
  - `UP/Staging/ModelBank/build_assetid_review_2026-10-01.py`: 0.03 MB, 0 hits
  - `UP/Staging/ModelBank/build_full_index.py`: 0.00 MB, 0 hits
  - Total: 26.0 MB. `README.md`, `LICENSE_PROVENANCE.md` and the `RIGHTS_*` files record rights decisions (AGENTS: rights constraints remain), so review them before any removal.
- Not in either list, so left in place:
  - `UP/Staging/Brief1_SealedCode_2026-10-06` (1 MB) and `UP/Staging/Briefs_2026-10-06` (1 MB): both created today at 19:28-19:29 local;
  - `UP/Staging/MANAGER_HANDOFF_2026-10-06.md`;
  - `UP/Content/Collections` (empty);
  - `PE/Houdini/GeoCity_city_v015_4km/__pycache__`;
  - the PB root helper scripts (`build_v015.py`, `permanent_bank_module.py` and the others).
- Kept by the brief's must-stay rules, though Iran- or old-only:
  - `Content/Project/Shared/ModelBank/AreaScopes/DT_Iran_38196167_46086167_4km` (AreaScopes/ is kept);
  - the older catalogs `DT_BankRelease_v2`, `DT_BankRelease_AllDisabled_v2` and `DT_NonBuildingBank_v3` (bank);
  - `PE/SourceData/Iran_*` and `PE/SourceData/GazaRimal` (SourceData is kept).
- `UP/Content/WorldBLD` (8379 MB) becomes fully unreferenced once Stage1Kit goes (INVENTORY 9.3). It is treated as a vendor pack and kept; its removal needs a separate decision, because no VaultCache copy backs it.

## 8. Execution notes (for the executor; not performed)

- Run only with no UnrealEditor running. Content deletions must also follow AGENTS and `UNREAL_DEPENDENCY_REVIEW_2026-09-29.md:14`: a Reference Viewer check and a controlled reopen afterwards. That file is in list 05, so copy its rule before deleting it. Re-run `sanity_check.py` immediately before deleting anything.
- After list 01 (and the Rimal set, once it is unblocked), the Iran and Rimal `AREA_PROFILE.json` stay (blocked). They point at maps that no longer exist; the code reading in BLOCKED.md section 1 says this is harmless to Shujaiya. The manager decides whether to retire them too.
- List 03 removes `Content/HoudiniEngine/{Temp,Bake}`. The Houdini Engine plugin recreates its default temp folder when needed (INFERRED).
- List 04 removes `PB/backup` (all 63 auto-backups, including bak61/bak62, the only r017-era states) and the revision folders r001-r016 and v002. The brief says the owner accepts losing these intermediate states.

## 9. Kept documents that name a deleted path (informational; links break, no code depends on them)

Scanned: 5226 `.md`/`.json` files in the kept folders, the kept Staging docs, root `AGENTS.md`, `PE/ModelBank`, `PE/SourceData`, the PE root docs and the v003/v004 folders. Ledgers were not opened. Token: `<parent>/<name>` of each deleted line, in the three separator spellings. The 166 `.blend1` lines are not included. 156 files name at least one deleted path:

- `PE/AGENTS.md` -> lists 05; e.g. `UP/Staging/Archive/ReturnToPipeline_2026-10-02`
- `PE/AREA.md` -> lists 05; e.g. `UP/Staging/Archive/PreFinalVision_2026-09-29/Research`
- `PE/CONTRACT.md` -> lists 03,04,05; e.g. `PE/Houdini/CityProof` (+16 more)
- `PE/ModelBank/Modular_2026-10-04/Families/MODULAR_DELIVERY.json` -> lists 05; e.g. `UP/Staging/ModelBank/Candidates` (+1 more)
- `PE/ModelBank/Modular_2026-10-04/InspectedSources/external_KIT_SM_Astra_Corner_Middle/ASSET.json` -> lists 05; e.g. `UP/Staging/ModelBank/Candidates`
- `PE/ModelBank/Modular_2026-10-04/InspectedSources/external_KIT_SM_Astra_Corner_Top/ASSET.json` -> lists 05; e.g. `UP/Staging/ModelBank/Candidates`
- `PE/ModelBank/Modular_2026-10-04/InspectedSources/external_KIT_SM_Astra_Top/ASSET.json` -> lists 05; e.g. `UP/Staging/ModelBank/Candidates`
- `PE/ModelBank/Modular_2026-10-04/InspectedSources/external_KIT_SM_Astra_Wall_Ground/ASSET.json` -> lists 05; e.g. `UP/Staging/ModelBank/Candidates`
- `PE/ModelBank/Modular_2026-10-04/InspectedSources/external_KIT_SM_Astra_Wall_Middle/ASSET.json` -> lists 05; e.g. `UP/Staging/ModelBank/Candidates`
- `PE/ModelBank/Modular_2026-10-04/InspectedSources/external_KIT_SM_Rural_Corner_Middle/ASSET.json` -> lists 05; e.g. `UP/Staging/ModelBank/Candidates`
- `PE/ModelBank/Modular_2026-10-04/InspectedSources/external_KIT_SM_Rural_Corner_Top/ASSET.json` -> lists 05; e.g. `UP/Staging/ModelBank/Candidates`
- `PE/ModelBank/Modular_2026-10-04/InspectedSources/external_KIT_SM_Rural_Top/ASSET.json` -> lists 05; e.g. `UP/Staging/ModelBank/Candidates`
- `PE/ModelBank/Modular_2026-10-04/InspectedSources/external_KIT_SM_Rural_Wall_Ground/ASSET.json` -> lists 05; e.g. `UP/Staging/ModelBank/Candidates`
- `PE/ModelBank/Modular_2026-10-04/InspectedSources/external_KIT_SM_Rural_Wall_Middle/ASSET.json` -> lists 05; e.g. `UP/Staging/ModelBank/Candidates`
- `PE/ModelBank/Modular_2026-10-04/ProceduralFamilies/HDA_BUILD.json` -> lists 04; e.g. `PE/Houdini/GeoCity_city_v015_PermanentBank/revisions/20261005_modular_source_families_v002`
- `PE/ModelBank/Modular_2026-10-04/ProceduralFamilies_Additional20/RESUME_PRESERVATION.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `PE/SourceData/Acquisition/README.md` -> lists 04; e.g. `PE/Houdini/GeoCity_v001`
- `PE/SourceData/Acquisition/receipts/20260930T123213Z_f3309256_GazaRimal_cook.json` -> lists 04; e.g. `PE/Houdini/GeoCity_v001`
- `PE/SourceData/Acquisition/receipts/20260930T123417Z_dfb866c4_GazaRimal_cook.json` -> lists 04; e.g. `PE/Houdini/GeoCity_v001`
- `PE/SourceData/Acquisition/receipts/20260930T123439Z_8899f405_GazaRimal_cook.json` -> lists 04; e.g. `PE/Houdini/GeoCity_v001`
- `PE/SourceData/Acquisition/receipts/20260930T123703Z_88c924a4_GazaRimal_cook.json` -> lists 04; e.g. `PE/Houdini/GeoCity_v001`
- `PE/SourceData/Acquisition/receipts/20260930T124106Z_bbb74da4_GazaRimal_cook.json` -> lists 04; e.g. `PE/Houdini/GeoCity_v001`
- `PE/SourceData/Acquisition/receipts/20260930T124138Z_6afa29d3_GazaRimal_cook.json` -> lists 04; e.g. `PE/Houdini/GeoCity_v001`
- `PE/SourceData/Acquisition/receipts/20260930T124522Z_cfe4d835_GazaRimal_cook.json` -> lists 04; e.g. `PE/Houdini/GeoCity_v001`
- `PE/SourceData/Acquisition/receipts/20260930T125724Z_36708c23_GazaRimal_cook.json` -> lists 04; e.g. `PE/Houdini/GeoCity_v001`
- `PE/SourceData/Acquisition/receipts/20260930T130827Z_9f6c81b5_GazaRimal_cook.json` -> lists 04; e.g. `PE/Houdini/GeoCity_v001`
- `PE/SourceData/Acquisition/receipts/20260930T130845Z_482aa639_GazaRimal_cook.json` -> lists 04; e.g. `PE/Houdini/GeoCity_v001`
- `PE/SourceData/Iran_38196167_46086167_4km/semantic_acquisitions/20261004T155016073136Z_consumer_v2/semantic_consumer_contract.json` -> lists 01,05; e.g. `UP/Staging/ModularBank_2026-10-04` (+1 more)
- `UP/AGENTS.md` -> lists 05; e.g. `UP/Staging/Archive/AppearanceCompletion_2026-10-03` (+5 more)
- `UP/Staging/AppearanceRepair_2026-10-03/Before/AGENTS.md` -> lists 05; e.g. `UP/Staging/Archive/ExecutionStart_2026-10-02` (+3 more)
- `UP/Staging/AppearanceRepair_2026-10-03/Before/Staging/CURRENT_STATE.md` -> lists 05; e.g. `UP/Staging/Archive/RepairCompletion_2026-10-03`
- `UP/Staging/AppearanceRepair_2026-10-03/Before/Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json` -> lists 03; e.g. `UP/Content/Project/Shared/SurfacePainting/MI_SurfaceBank_AllLayers.uasset`
- `UP/Staging/AppearanceRepair_2026-10-03/Before/Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json` -> lists 03; e.g. `UP/Content/Project/Shared/SurfacePainting/MI_SurfaceBank_AllLayers.uasset`
- `UP/Staging/AppearanceRepair_2026-10-03/Before/Staging/WORK_PLAN.md` -> lists 05; e.g. `UP/Staging/Archive/RepairCompletion_2026-10-03`
- `UP/Staging/AppearanceRepair_2026-10-03/BeforeTone/20261003T132111807809Z/0_STYLE_CONTRACT_PROPOSAL.json` -> lists 03; e.g. `UP/Content/Project/Shared/SurfacePainting/MI_SurfaceBank_AllLayers.uasset` (+1 more)
- `UP/Staging/AppearanceRepair_2026-10-03/STYLE_CONTRACT_PROPOSAL.json` -> lists 03; e.g. `UP/Content/Project/Shared/SurfacePainting/MI_SurfaceBank_AllLayers.uasset` (+1 more)
- `UP/Staging/AssetBankOperator_2026-10-06/Activation/APPLY_STARTED.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/Activation/CATALOG_SOURCE.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04` (+3 more)
- `UP/Staging/AssetBankOperator_2026-10-06/Activation/TRANSACTION.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km` (+1 more)
- `UP/Staging/AssetBankOperator_2026-10-06/Before/AREA_PROFILE_Iran.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km` (+1 more)
- `UP/Staging/AssetBankOperator_2026-10-06/Before/CATALOG_SOURCE.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04` (+3 more)
- `UP/Staging/AssetBankOperator_2026-10-06/EDITOR_PREFLIGHT_29900.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/Exit_20261006/EXIT_PID29900.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/Generation/FINAL_NATIVE_READBACK.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/Generation/IRAN_STARTED.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km` (+1 more)
- `UP/Staging/AssetBankOperator_2026-10-06/Native/BANK_EXPANSION_007_IMPORT.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/Native/BANK_EXPANSION_007_SOURCE.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/Native/BANK_EXPANSION_007_VALIDATION.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/Native/BANK_EXPANSION_011_IMPORT.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/Native/BANK_EXPANSION_011_SOURCE.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/Native/BANK_EXPANSION_011_VALIDATION.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/Native/BANK_EXPANSION_014_IMPORT.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/Native/BANK_EXPANSION_014_VALIDATION.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/Native/BANK_EXPANSION_031_SOURCE.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/Native/BANK_USE_CITY_001_IMPORT.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/Native/BANK_USE_CITY_001_VALIDATION.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/PRESERVATION_CHECK.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/AssetBankOperator_2026-10-06/Resume_20261006/PREFLIGHT.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/BankIntegration_2026-10-04/ASSIGNMENT.json` -> lists 01,05; e.g. `UP/Staging/BankPreparation_2026-10-04` (+1 more)
- `UP/Staging/BankIntegration_2026-10-04/ApplyBundle/catalog_v4_source.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04` (+3 more)
- `UP/Staging/BankIntegration_2026-10-04/Before/catalog_v4_source.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04` (+3 more)
- `UP/Staging/BankIntegration_2026-10-04/CategoryBatches/Props/READY_JOBS.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04`
- `UP/Staging/BankIntegration_2026-10-04/CategoryBatches/Vegetation/INPUT_SNAPSHOT.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04`
- `UP/Staging/BankIntegration_2026-10-04/CategoryBatches/Vegetation/READY_JOBS.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04` (+1 more)
- `UP/Staging/BankIntegration_2026-10-04/CategoryBatches/Vegetation/SEMANTIC_CONSUMER_HANDOFF.json` -> lists 01,05; e.g. `UP/Staging/BankPreparation_2026-10-04` (+3 more)
- `UP/Staging/BankIntegration_2026-10-04/CategoryBatches/Vegetation/SEMANTIC_EXECUTION_MANIFEST.json` -> lists 01,05; e.g. `UP/Staging/BankPreparation_2026-10-04` (+2 more)
- `UP/Staging/BankIntegration_2026-10-04/CategoryBatches/WholeBuildings/READY_JOBS.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04`
- `UP/Staging/BankIntegration_2026-10-04/CategoryBatches/WholeBuildings/Reviews/1f8184c5e62c18be9821bf90e248c31b465faaa182923f2cf7f6c6bedcd2beef/READY_JOBS.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04`
- `UP/Staging/BankIntegration_2026-10-04/CategoryBatches/WholeBuildings/Reviews/302e53ef0643c50c00783d12d5309ce204f7b3d814410097a3334eac208cfc26/READY_JOBS.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04`
- `UP/Staging/BankIntegration_2026-10-04/CategoryBatches/WholeBuildings/Reviews/377f310acacd0abee188c9d870462aa5de0f83817cb997f4fa8d60691ec0461e/READY_JOBS.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04`
- `UP/Staging/BankIntegration_2026-10-04/CategoryBatches/WholeBuildings/Reviews/50250a693ffdce63989cc5c9945c38f50de16b965cd2e0ce489a9053c22a717f/READY_JOBS.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04`
- `UP/Staging/BankIntegration_2026-10-04/CategoryBatches/WholeBuildings/Reviews/79bab2ef24cc413fa497b8b6276916be50c6f3e9f8b1675b7f27f00c6f8a2ab0/READY_JOBS.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04`
- `UP/Staging/BankIntegration_2026-10-04/CategoryBatches/WholeBuildings/Reviews/8d99dfcf22e8ead52a38a75bc5992af0b14478c2151922e0cf72cba29b3db892/READY_JOBS.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04`
- `UP/Staging/BankIntegration_2026-10-04/CategoryBatches/WholeBuildings/Reviews/dc91dab00990167ba2c0f8670d540a9abe821e5c5a5ad1e88aa6000b9c2e1e4a/READY_JOBS.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04`
- `UP/Staging/BankIntegration_2026-10-04/CategoryBatches/WholeBuildings/Reviews/f33f51d956f3b18307ed29e9d6eefb953c57d667542eeb1b81e39e8633948181/READY_JOBS.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04`
- `UP/Staging/BankIntegration_2026-10-04/DirtyOriginals_Transfer/DIAGNOSTIC.json` -> lists 03; e.g. `UP/Content/Developers/USER/HoudiniCityProof/V13ConnectedPreview`
- `UP/Staging/BankIntegration_2026-10-04/R020_CONTENT_REQUEST.json` -> lists 01; e.g. `PE/Houdini/GeoCity_city_v015_4km/revisions` (+1 more)
- `UP/Staging/CURRENT_STATE.md` -> lists 05; e.g. `UP/Staging/Archive/RepairCompletion_2026-10-03`
- `UP/Staging/Consolidation_2026-10-06/INVENTORY.md` -> lists 01,03,04,05; e.g. `PE/Houdini/CityProof` (+82 more)
- `UP/Staging/MANAGER_HANDOFF_2026-10-06.md` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km` (+1 more)
- `UP/Staging/ManagedExecution_2026-10-02/Task2/BEFORE_AREA_PROFILE.json` -> lists 03; e.g. `UP/Content/Project/Shared/SurfacePainting/MI_SurfaceBank_AllLayers.uasset`
- `UP/Staging/ManagedExecution_2026-10-02/Task2/BEFORE_catalog_v4_source.json` -> lists 05; e.g. `UP/Staging/ModelBank/DirectPickerPilot_2026-10-01` (+2 more)
- `UP/Staging/ManagedExecution_2026-10-02/Task3/BEFORE_AREA_PROFILE.json` -> lists 03; e.g. `UP/Content/Project/Shared/SurfacePainting/MI_SurfaceBank_AllLayers.uasset`
- `UP/Staging/ManagedExecution_2026-10-02/Task3/BEFORE_catalog_v4_source.json` -> lists 05; e.g. `UP/Staging/ModelBank/DirectPickerPilot_2026-10-01` (+2 more)
- `UP/Staging/ManagedExecution_2026-10-02/Task5/BEFORE_AREA_PROFILE.json` -> lists 03; e.g. `UP/Content/Project/Shared/SurfacePainting/MI_SurfaceBank_AllLayers.uasset`
- `UP/Staging/ManagedExecution_2026-10-02/Task5/BEFORE_catalog_v4_source.json` -> lists 05; e.g. `UP/Staging/ModelBank/DirectPickerPilot_2026-10-01` (+2 more)
- `UP/Staging/ManagedSystemsAstra_2026-10-04/BANK_ACTIVATION.json` -> lists 01; e.g. `UP/Staging/IranBuildingAdaptation_2026-10-04`
- `UP/Staging/ManagedSystemsAstra_2026-10-04/FULL_BANK_COMPLETION.json` -> lists 05; e.g. `UP/Staging/BankPreparation_2026-10-04`
- `UP/Staging/ManagedSystemsAstra_2026-10-04/HistoryBeforeUserStop/BANK_ACTIVATION_before_stop.json` -> lists 01; e.g. `UP/Staging/IranBuildingAdaptation_2026-10-04`
- `UP/Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/BANK_ACTIVATION_BEFORE_FRESH_RESTART_4a29f7219b6f251f471bee8517e12c1db1a150c1f5386465be906edcf5a0dd40.json` -> lists 01; e.g. `UP/Staging/IranBuildingAdaptation_2026-10-04`
- `UP/Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/BANK_ACTIVATION_BEFORE_PID30328_56ecd11e3cdf23bcee2d4597f11af40eb1253581e9b9830b7c0443dc452469f1.json` -> lists 01; e.g. `UP/Staging/IranBuildingAdaptation_2026-10-04`
- `UP/Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/Before/AGENTS.md` -> lists 05; e.g. `UP/Staging/Archive/AppearanceCompletion_2026-10-03` (+5 more)
- `UP/Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/Before/Staging/BankIntegration_2026-10-04/ASSIGNMENT.json` -> lists 01,05; e.g. `UP/Staging/BankPreparation_2026-10-04` (+1 more)
- `UP/Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/Before/Staging/CURRENT_STATE.md` -> lists 05; e.g. `UP/Staging/Archive/RepairCompletion_2026-10-03`
- `UP/Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/Before/Staging/ManagedSystemsAstra_2026-10-04/BANK_ACTIVATION.json` -> lists 01; e.g. `UP/Staging/IranBuildingAdaptation_2026-10-04`
- `UP/Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/Before/Staging/WORK_PLAN.md` -> lists 05; e.g. `UP/Staging/Archive/RepairCompletion_2026-10-03`
- `UP/Staging/ManagedSystemsAstra_2026-10-04/Task1_Lifecycle/IranSemanticConsumer/FINAL_PIN_VERIFICATION.json` -> lists 01; e.g. `UP/Staging/IranBuildingAdaptation_2026-10-04` (+1 more)
- `UP/Staging/ManagedSystemsAstra_2026-10-04/Task1_Lifecycle/IranSemanticConsumer/PROFILE_INTERFACE_PROPOSAL.json` -> lists 01; e.g. `UP/Staging/IranBuildingAdaptation_2026-10-04`
- `UP/Staging/ManagedSystemsAstra_2026-10-04/Task1_Lifecycle/IranSemanticConsumer/RECEIPT_REFRESH.json` -> lists 01; e.g. `UP/Staging/IranBuildingAdaptation_2026-10-04` (+1 more)
- `UP/Staging/ManagedSystemsAstra_2026-10-04/Task1_Lifecycle/IranSemanticConsumer/RESULT.json` -> lists 01; e.g. `UP/Staging/IranBuildingAdaptation_2026-10-04` (+1 more)
- `UP/Staging/ManagedSystemsAstra_2026-10-04/Task1_Lifecycle/IranSemanticConsumer/ReceiptRefresh/20261004T181015Z/RESULT.json` -> lists 01; e.g. `UP/Staging/IranBuildingAdaptation_2026-10-04` (+1 more)
- `UP/Staging/ManagedSystemsAstra_2026-10-04/Task1_Lifecycle/IranSemanticConsumer/ReceiptRefresh/20261004T181015Z/SOURCE_HANDOFF.json` -> lists 01; e.g. `UP/Staging/IranBuildingAdaptation_2026-10-04` (+1 more)
- `UP/Staging/ManagedSystemsAstra_2026-10-04/Task1_Lifecycle/IranSemanticConsumer/SOURCE_CHECKS.json` -> lists 01; e.g. `UP/Staging/IranBuildingAdaptation_2026-10-04` (+1 more)
- `UP/Staging/ManagedSystemsAstra_2026-10-04/Task1_Lifecycle/IranSemanticConsumer/SOURCE_HANDOFF.json` -> lists 01; e.g. `UP/Staging/IranBuildingAdaptation_2026-10-04` (+1 more)
- `UP/Staging/ManagedSystemsAstra_2026-10-04/Task1_Lifecycle/LandscapeOwnership_Repair/AcceptedBaseline/RESULT.json` -> lists 05; e.g. `UP/Staging/HoudiniEngineOutputRepair_2026-10-04`
- `UP/Staging/ManagedSystemsAstra_2026-10-04/Task1_Lifecycle/LandscapeOwnership_Repair/AcceptedBaseline/SOURCE_HANDOFF.json` -> lists 05; e.g. `UP/Staging/HoudiniEngineOutputRepair_2026-10-04`
- `UP/Staging/ManagedSystemsAstra_2026-10-04/Task1_Lifecycle/RESULT.json` -> lists 05; e.g. `UP/Staging/HoudiniEngineOutputRepair_2026-10-04`
- `UP/Staging/ManagedSystemsAstra_2026-10-04/Task1_Lifecycle/SOURCE_HANDOFF.json` -> lists 05; e.g. `UP/Staging/HoudiniEngineOutputRepair_2026-10-04`
- `UP/Staging/ManagedSystemsAstra_2026-10-04/Task3_GroundGrass/IranSemanticConsumer/PROFILE_PATCH_PROPOSAL.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/ModelBank/H0958_MaterialRepair_Proof_20260929/AFTER_MATERIAL_COPY.json` -> lists 05; e.g. `UP/Staging/TrackA_Tests/HoudiniCityProof/10_measure_session/coordination`
- `UP/Staging/ModelBank/H0958_MaterialRepair_Proof_20260929/AFTER_MESH_COPY.json` -> lists 05; e.g. `UP/Staging/TrackA_Tests/HoudiniCityProof/10_measure_session/coordination`
- `UP/Staging/ModelBank/H0958_MaterialRepair_Proof_20260929/CONTENT_AFTER.json` -> lists 03; e.g. `UP/Content/Developers/USER/HoudiniCityProof/B1_probebox.uasset` (+12 more)
- `UP/Staging/ModelBank/H0958_MaterialRepair_Proof_20260929/FINAL_VALIDATION.json` -> lists 05; e.g. `UP/Staging/TrackA_Tests/HoudiniCityProof/10_measure_session/coordination`
- `UP/Staging/ModelBank/H0958_MaterialRepair_Proof_20260929/P1_SAVED_CHECK.json` -> lists 05; e.g. `UP/Staging/TrackA_Tests/HoudiniCityProof/10_measure_session/coordination`
- `UP/Staging/ModelBank/H0958_MaterialRepair_Proof_20260929/PREFLIGHT.json` -> lists 03,05; e.g. `UP/Content/Developers/USER/HoudiniCityProof/B1_probebox.uasset` (+13 more)
- `UP/Staging/ModelBank/ME/GAPS_ME.md` -> lists 05; e.g. `UP/Staging/Archive/PreFinalVision_2026-09-29/Research`
- `UP/Staging/ModelBank/ME/import_mcp/001_bank_ctx.json` -> lists 03; e.g. `UP/Content/Developers/USER/TrackA_T0-T5`
- `UP/Staging/ModelBank/ME/import_v2_mcp/012_v2_log.json` -> lists 03; e.g. `UP/Content/Developers/USER/TrackA_T0-T5` (+1 more)
- `UP/Staging/ModularConstruction_2026-10-05/Run_20261005/ATTEMPT2_START.json` -> lists 04; e.g. `PE/Houdini/GeoCity_city_v015_PermanentBank/revisions/20261005_modular_source_families_v002`
- `UP/Staging/ModularConstruction_2026-10-05/Run_20261005/ATTEMPT3_START.json` -> lists 04; e.g. `PE/Houdini/GeoCity_city_v015_PermanentBank/revisions/20261005_modular_source_families_v002`
- `UP/Staging/ModularConstruction_2026-10-05/Run_20261005/USE_FIX_BUILD.json` -> lists 04; e.g. `PE/Houdini/GeoCity_city_v015_PermanentBank/revisions/20261005_modular_source_families_v002`
- `UP/Staging/PROJECT_STATUS_2026-10-06.md` -> lists 01,03; e.g. `UP/Content/Project/Shared/ModelBank/HDA/GeoCity_city_v015_4km.uasset` (+1 more)
- `UP/Staging/RepairExecution_2026-10-03/ACTUAL_GazaRimal.json` -> lists 03; e.g. `UP/Content/Project/Shared/SurfacePainting/MI_SurfaceBank_AllLayers.uasset`
- `UP/Staging/RepairExecution_2026-10-03/ACTUAL_GazaShujaiya.json` -> lists 03; e.g. `UP/Content/Project/Shared/SurfacePainting/MI_SurfaceBank_AllLayers.uasset`
- `UP/Staging/RepairExecution_2026-10-03/ASSET_REPAIR_CANDIDATES.json` -> lists 05; e.g. `UP/Staging/ModelBank/UnifiedCatalogV3_2026-10-02`
- `UP/Staging/RepairExecution_2026-10-03/Before/AGENTS.md` -> lists 05; e.g. `UP/Staging/Archive/ExecutionStart_2026-10-02` (+3 more)
- `UP/Staging/RepairExecution_2026-10-03/Before/Staging__CURRENT_STATE.md` -> lists 05; e.g. `UP/Staging/Archive/ExecutionStart_2026-10-02`
- `UP/Staging/RepairExecution_2026-10-03/Before/Staging__ModelBank__GazaShujaiyaIntegration_2026-10-02__AREA_PROFILE.json` -> lists 03; e.g. `UP/Content/Project/Shared/SurfacePainting/MI_SurfaceBank_AllLayers.uasset`
- `UP/Staging/RepairExecution_2026-10-03/Before/Staging__ModelBank__PermanentIntegration_2026-10-02__AREA_PROFILE.json` -> lists 03; e.g. `UP/Content/Project/Shared/SurfacePainting/MI_SurfaceBank_AllLayers.uasset`
- `UP/Staging/RepairExecution_2026-10-03/Before/Staging__ModelBank__PermanentIntegration_2026-10-02__catalog_v4_source.json` -> lists 05; e.g. `UP/Staging/ModelBank/DirectPickerPilot_2026-10-01` (+2 more)
- `UP/Staging/RepairExecution_2026-10-03/Before/Staging__WORK_PLAN.md` -> lists 05; e.g. `UP/Staging/Archive/ExecutionStart_2026-10-02`
- `UP/Staging/RepairExecution_2026-10-03/REOPEN_GazaRimal.json` -> lists 03; e.g. `UP/Content/Project/Shared/SurfacePainting/MI_SurfaceBank_AllLayers.uasset`
- `UP/Staging/RepairExecution_2026-10-03/REOPEN_GazaShujaiya.json` -> lists 03; e.g. `UP/Content/Project/Shared/SurfacePainting/MI_SurfaceBank_AllLayers.uasset`
- `UP/Staging/RepairExecution_2026-10-03/RESULT.json` -> lists 03; e.g. `UP/Content/Project/Shared/SurfacePainting/MI_SurfaceBank_AllLayers.uasset`
- `UP/Staging/ReusableSky_2026-10-06/PREFLIGHT_READONLY.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/ReusableSky_2026-10-06/READONLY_CAPTURE_RECEIPT.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/DECISION_LET_RUN_FINISH.json` -> lists 03; e.g. `UP/Content/Project/Shared/Recovery`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/IranRun_20261006/LAUNCH_PID29900.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/IranRun_20261006/MANAGER_ACTIVATION.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/BEFORE_MANIFEST.json` -> lists 03; e.g. `UP/Content/Project/Shared/SurfacePainting/HDA/GeoCity_city_v013_AllSurfacePalette.uasset` (+3 more)
- `UP/Staging/SystemCompletion_2026-10-04/ACQUIRED_CLEAN_EDITOR.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km`
- `UP/Staging/SystemCompletion_2026-10-04/Before/AGENTS.md` -> lists 05; e.g. `UP/Staging/Archive/AppearanceCompletion_2026-10-03` (+5 more)
- `UP/Staging/SystemCompletion_2026-10-04/Before/CURRENT_STATE.md` -> lists 05; e.g. `UP/Staging/Archive/RepairCompletion_2026-10-03`
- `UP/Staging/SystemCompletion_2026-10-04/Before/Iran_AREA_PROFILE_before_capacity.json` -> lists 01; e.g. `UP/Content/Project/Areas/Iran_38196167_46086167_4km` (+1 more)
- `UP/Staging/SystemCompletion_2026-10-04/Before/WORK_PLAN.md` -> lists 05; e.g. `UP/Staging/Archive/RepairCompletion_2026-10-03`
- `UP/Staging/ToolchainChecks/B2_UNTITLED_PRESERVATION_2026-10-01.md` -> lists 03; e.g. `UP/Content/Developers/USER/HoudiniCityProof/Cook` (+1 more)
- `UP/Staging/ToolchainChecks/CLAUDE_CODE_AUDIT_RECONCILIATION_2026-10-01.md` -> lists 05; e.g. `UP/Staging/TrackA_Tests/HoudiniCityProof/GeoCity_v006_ApprovedPolePilot_2026-10-01` (+2 more)
- `UP/Staging/ToolchainChecks/EDITOR_CLOSURE_2026-10-01/B2_PID32804_CLOSE_RESULT.md` -> lists 03; e.g. `UP/Content/Developers/USER/HoudiniCityProof/L_B2_OriginalUntitled_Inspection_20261001.umap`
- `UP/Staging/ToolchainChecks/EDITOR_CLOSURE_2026-10-01/B2_PID32804_POST_CLOSE_FILES.json` -> lists 03; e.g. `UP/Content/Developers/USER/HoudiniCityProof/Cook` (+1 more)
- `UP/Staging/ToolchainChecks/EDITOR_CLOSURE_2026-10-01/B2_PID32804_PRE_CLOSE_FILES.json` -> lists 03; e.g. `UP/Content/Developers/USER/HoudiniCityProof/Cook` (+1 more)
- `UP/Staging/ToolchainChecks/EDITOR_CLOSURE_2026-10-01/V7_PID30076_CLOSE_RESULT.md` -> lists 03,05; e.g. `UP/Content/Developers/USER/HoudiniCityProof/V7FullCatalogPolePilot` (+2 more)
- `UP/Staging/ToolchainChecks/EDITOR_CLOSURE_2026-10-01/V7_POST_CLOSE_FILE_HASHES.json` -> lists 03; e.g. `UP/Content/Developers/USER/HoudiniCityProof/V7FullCatalogPolePilot`
- `UP/Staging/ToolchainChecks/HE_CONNECTION_2026-09-30/RESULT.md` -> lists 03,05; e.g. `UP/Content/Developers/USER/HoudiniCityProof/B1_probebox.uasset` (+1 more)
- `UP/Staging/ToolchainChecks/HE_CONNECTION_2026-09-30/runtime_result.json` -> lists 03; e.g. `UP/Content/Developers/USER/HoudiniCityProof/B1_probebox.uasset`
- `UP/Staging/ToolchainChecks/PID32804_OpenState_2026-10-01/RESULT.md` -> lists 03; e.g. `UP/Content/Developers/USER/HoudiniCityProof/Cook` (+1 more)
- `UP/Staging/WORK_PLAN.md` -> lists 05; e.g. `UP/Staging/Archive/RepairCompletion_2026-10-03`

## 10. Scripts and intermediate data (session scratchpad, read-only work files)

- `scan_content.py` produces `content_refs.json`, the strings scan of all Content packages.
- `dp_closure.py` and `dp_content.py` compute the closures and the reverse fixpoint (`dp_content.json`).
- `dp_grep.py` runs the folder-name grep (`dp_grep_hits.json`).
- `dp_profpaths.py`, `regscan.py` and `dp_mustay.py` build the must-stay specification.
- `dp_build.py` builds the lists. `dp_sizes.py`, `dp_links.py` and `dp_report.py` produce the sizes, the link scan and this file.
- Only `sanity_check.py` and `must_stay_paths.tsv` are copied into this folder.
