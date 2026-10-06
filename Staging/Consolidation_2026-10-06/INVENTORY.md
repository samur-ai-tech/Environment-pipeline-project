# Environmentpipeline consolidation inventory (2026-10-06)

## 0. Header

- **Date:** 2026-10-06
- **Author:** read-only consolidation review (Claude Code session ff22121a), for the manager (Claude Code session cc37d4d2)
- **Status:** PROPOSAL ONLY. The manager decides. Nothing was deleted, moved, renamed, saved or reorganized.
- **Snapshot window:** the surveys ran about 16:50-17:45 local time (UTC+3), i.e. 13:50-14:45Z. The author's spot checks ran at about 14:50Z.
- **Sources:**
  - Seven survey parts written today by five reviewers plus the coordinator: 00 sizes, 00b root/plugins/config, 01 generators and HDAs, 02 runtime/launchers/leases, 03 ground material and Recovery, 04 Content references, 05 Staging/Archive/Git.
  - `Staging/PROJECT_STATUS_2026-10-06.md`.
  - The first three paragraphs of `AGENTS.md`.
  - In the tables, "(part 0X)" names the source part. "(author)" marks a spot check made while this document was written.
- **Roots:**
  - `UP` = `C:/Users/USER/Documents/Unreal Projects/Environmentpipeline`. Paths with no root prefix are relative to UP.
  - `PE` = `C:/Users/USER/Documents/Pipeline Environment`.
  - `PB` = `PE/Houdini/GeoCity_city_v015_PermanentBank`.
  - `4K` = `PE/Houdini/GeoCity_city_v015_4km`.
- **Labels:**
  - MEASURED = hashed, listed, grepped or read on disk on 2026-10-06.
  - DOCUMENTED = quoted from a project record (path:line).
  - INFERRED = reasoned, not proved.
- **Units:** hashes are sha256, first 8 hex characters unless more are needed. Sizes are MiB written as "MB" unless stated otherwise.
- **Times:** "Z" is UTC. `ls` mtimes in the parts are local time (UTC+3), so 21:41 local = 18:41Z.

### Snapshot caveat

The tree moved while the survey ran (MEASURED unless marked otherwise).

1. **Bank-operator lease.**
   - Since 14:14:05Z, the last line of `Staging/ModelBank/EDITOR_OWNER.txt` has been `OWNER=ASSET_BANK_OPERATOR assigned_editor_PID=29900 ... scope=bank_import_validate_register_enable_profi...` (parts 03, 04). Its activation record is `Staging/AssetBankOperator_2026-10-06/DIRECT_USER_ACTIVATION_29900.json`.
   - At about 14:00Z, the last line (line 493 of 493) was `2026-10-06T13:39:07.979194+00:00 OWNER=NONE task=GEOCITY_MENU editor_PID=29900 released_phase=baked_saved_verified` (part 02).
   - The lease file changed again at 14:48:43Z (131,518 B). The author saw this in a directory listing only. The file was not opened, because the operator is appending to it.
2. **A new Content folder is not classified.**
   - `Content/Project/Shared/ModelBank/Supply/` (244 files, 794 MB, subfolders `desert/` and `phoenix_palms/`) was written 14:19-14:22Z (part 04). It is in no count and no table below.
   - The brief named it `Staging/ModelBank/Supply/`. The author checked: that Staging path does not exist, and the folder is under Content.
   - Two Staging folders also appeared mid-audit (part 05): `Staging/AssetBankOperator_2026-10-06/NativeIntake/` (13:58-14:19Z) and `Staging/ReusableSky_2026-10-06/` (14:02Z).
3. **AGENTS.md changed.**
   - `AGENTS.md` was rewritten at 14:22:58Z (mtime 17:22:58 local).
   - Two new blocks now sit above the manager paragraph: a "Parallel editor rule - current decision, Aviv, 2026-10-06" section (lines 3-5) and a Reusable Sky operator activation for chat 01a1118e (lines 7-9) (author).
   - The manager paragraph is now line 12.
4. **A banner was added.** The manager added a HISTORICAL banner to `Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/STAGE1_GROUND_PLAN.md` at 14:18:18Z (line 3). This shifted that file's line numbers by +2. The citations below use the post-edit numbers (part 03).
5. **Catalog and profiles changed inside the window.**
   - At 14:25Z they were still unchanged: `DT_EnvironmentBank_v4` f763b072; profiles 4174a627 / 492b9ac5 / 004ec07d (MEASURED, part 04). Every value below that cites those hashes is "as of 13:50-14:25Z" and is marked "superseded in-window".
   - At 14:32:57-58Z the bank operator rewrote the catalog and all three profiles. The hashes were MEASURED by the coordinator's reviewer; the author confirmed the new mtimes and sizes by listing.
     - The catalog `DT_EnvironmentBank_v4` is now e26bf06c (1,582,250 B), with row_count 1,295. Its catalog_sha256 is e0bd4e85 (Gaza) and a2d14c36 (Iran).
     - The profiles are now: Shujaiya f722381f, Rimal e6dead27, Iran cb0f3cab.
     - All three profiles' `decision_receipt` now point to `Staging/AssetBankOperator_2026-10-06/Activation/DECISION.json` (5,790 B, 14:32:09Z; MEASURED existence). `geocity_bank_workflow.py:505-507` hash-checks it, so AssetBankOperator is LIVE by criterion 2 as well.
   - The old profiles 4174a627 / 492b9ac5 / 004ec07d now exist only as `Staging/AssetBankOperator_2026-10-06/Before/AREA_PROFILE_{GazaShujaiya,GazaRimal,Iran}.json` (14:32:09Z; MEASURED listing). The rollback analysis in 3.7 and section 4 item 6 depends on these copies.
   - All 8 `Stage1_Ground/Hybrid_Auto/Args/HYBRID_ARGS_*.json` still pin `profile_sha256` 4174a627 (MEASURED, author grep), so the Hybrid args are stale (section 4 item 16).
   - The author did not re-read the new profiles, to avoid touching files the operator writes. Whether the new Shujaiya profile still names `MI_GeoCityGround_Auto` was not re-checked (INFERRED: likely, since the operator's scope is the bank).
   - Re-run the Content reference closure (3.11 and Appendix A) after the bank lease is released.
6. **Shujaiya assignment state.** `Staging/ShujaiyaOrdinaryRun_2026-10-05/ASSIGNMENT.json:44` has read `"state": "EDITOR_PID29900_LEASED_TO_ASSET_BANK_CHAT_BY_AVIV_HYBRID_WAITS"` since 14:18:18Z (MEASURED, author grep and mtime).
7. **Drift after the survey window** (MEASURED from author listings at about 15:25Z unless marked).
   - The Rimal map was re-saved at 14:52:20Z and is now 1d670c8e (hash MEASURED by the reviewer).
     - Its size (33,209,758 B) and mtime equal those of `Staging/ReusableSky_2026-10-06/Before/L_GazaRimal_BankIntegration_1d670c8e.umap`.
     - The previous state a6961c8e is preserved at `Staging/ReusableSky_2026-10-06/Before/L_GazaRimal_BankIntegration_a6961c8e.umap` (33,208,729 B), so 5 copies of a6961c8e now exist.
     - INFERRED: the Reusable Sky task saved the Rimal map.
     - Rimal rows below that say a6961c8e are "as of the survey window".
   - `Environmentpipeline.uproject` gained the SunPosition plugin at 14:47:15Z (`Environmentpipeline.uproject:8`). A pre-change copy is in `ReusableSky_2026-10-06/Before/`.
   - Two more editor startups were recorded: `Staging/SystemCompletion_2026-10-04/RUNTIME_STARTUP_PID28148.json` (14:53:30Z) and `RUNTIME_STARTUP_PID5288.json` (15:21:23Z). At about 15:25Z two editors were running, PIDs 29900 and 5288 (`tasklist`).
   - `Staging/AssetBankOperator_2026-10-06/Before/IRAN_MAP_BEFORE_EXPANSION.umap` has the same size (86,341,223 B) and mtime (13:39:07Z) as the live Iran map c409279c. A backup of c409279c therefore probably exists (INFERRED; not hashed).
   - By listing, the live Iran and Shujaiya maps were unchanged.

**Read-only statement.**
- The review was read-only.
- No Unreal editor, Houdini, hython, MCP tool, Workflow tool or project script was run.
- Nothing in either project tree was written except this file and its folder.
- No `*_STATE.json`, `WORKFLOW_STATE.json`, `EDITOR_CURRENT_STATE.json` or `Saved/Logs` file was opened on purpose.
- Part 01 listed `PB/revisions/r016_inward_roof_before_repair/WORKFLOW_STATE.json` without opening it.

**Ledger-read disclosure.**
- One reviewer (part 03) ran a recursive grep over Staging. At about 14:18Z it matched, and therefore opened, `Staging/ModelBank/PermanentIntegration_2026-10-02/EDITOR_CURRENT_STATE.json` once, read-only. This was after the 14:14:05Z bank lease began. No content from that file was used.
- A listing-only check found no ledger written after 13:39Z, so no ledger was being written in that window (MEASURED). The check was `find Staging/ModelBank -name '*STATE*.json' -newermt '2026-10-06 16:39'`, where 16:39 local = 13:39Z.
- Recommendation: the bank operator checks its log for access-denied or PermissionError entries between 14:10Z and 14:20Z.

## 1. Summary for the manager

> Added later on 2026-10-06: section 10 answers whether a Git clone works on another computer (it does not for generation: the three profiles hold about 40 absolute machine paths each and the runtime reads four of them).

1. **Seal intact.** `Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json` hashes to 258469e1, the B2 seal in `RATIFICATION_B2.json:7-9`. All 17 pinned files match by full 64-hex hash, so there is no drift (MEASURED, part 02).
2. **The native 1 km HDA runs v004, not v003.**
   - `Content/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank.uasset` (3cf1f840, saved 07:33Z today) embeds the v004 ProceduralThirty hdalc (886ab082) byte-exact. It contains no v003 string. PROJECT_STATUS §3 item 2 (and part 05) say v003.
   - The v004 receipts record `"native_city_regeneration_performed": false`, so v004 has never been cooked into a saved area.
   - The HDA sits outside the seal, and the profiles carry only its asset path. The next Gaza regeneration will therefore use v004 without any gate noticing.
   - (MEASURED; "without any gate noticing" INFERRED; parts 01, 02.)
3. **The B2 native has one copy, outside the Unreal project, and its ratification record mislabels it.**
   - No byte copy of the B2-ratified native 2358c514 exists in Content, Staging or Saved (MEASURED, part 05).
   - The only copy found is `PE/ModelBank/Modular_2026-10-04/ProceduralFamilies_Additional20/Integration/Before/GeoCity_city_v015_PermanentBank.uasset`. It looks like a routine backup (MEASURED, part 01).
   - A B2 rollback must also restore the v003 registry refs a39dbbb9 / b2e1876b in both Gaza profiles (MEASURED).
   - `RATIFICATION_B2.json:15-18` calls 2358c514 a "v002 modular source families derivative". Its bytes embed the v003 ProceduralTen hdalc 462f1d50 (MEASURED). INFERRED: "v002" is the family-id suffix used inside the families.
4. **GazaShujaiya cannot be regenerated now.**
   - Its profile (4174a627 as of 14:25Z; superseded in-window by f722381f, not re-read) sets `landscape_material` to `MI_GeoCityGround_Auto` and `parent_chain` to `M_GeoCityAuto`. Both assets are absent.
   - `geocity_bank_workflow.py:650` asserts that the Landscape material equals the profile value, so a regeneration is expected to fail.
   - Neither scripted rollback is clean.
   - (MEASURED; the failure INFERRED; part 03.)
5. **Only one launcher works.**
   - Only `Staging/SystemCompletion_2026-10-04/launch_editor.ps1` works under the current seal, and it is Gaza-only. Six other launchers fail their own gates.
   - The Iran editor (PID 29900) was started "manager_direct", without any launcher file.
   - (MEASURED, part 02.)
6. **ASSIGNMENTS.json already names the new manager.**
   - `Staging/ManagedSystemsAstra_2026-10-04/ASSIGNMENTS.json` names cc37d4d2 as manager and as task4 (applied 2026-10-05T20:02:49Z), as the AGENTS.md:12 technical note correctly says.
   - That note's stale part is its claim that `GENERATION_ACTIVATION.json` manager_thread_id is "also validated by the sealed launcher and by geocity_editor_action". Grep finds no reader in `Content/Python` or `launch_editor.ps1`.
   - Stale inner fields remain in the file.
   - `BANK_ACTIVATION.json` and `BankIntegration_2026-10-04/ASSIGNMENT.json` still carry 01a10789, and sealed code still reads both. The bank branch is therefore always refused.
   - (MEASURED, part 02.)
7. **More Staging folders are LIVE than status §3 item 6 says.**
   - Sealed code writes receipts into `AppearanceRepair_2026-10-03` (`geocity_roadbld_clip.py:266-271`, `geocity_roadbld_grounding.py:1309`).
   - Sealed code reads `BankIntegration_2026-10-04` (`geocity_editor_action.py:28`). Until 14:32:58Z it also hash-checked a decision receipt there (`geocity_bank_workflow.py:505-507`). Since then the profiles' `decision_receipt` points into `AssetBankOperator_2026-10-06/Activation/` (snapshot caveat 5).
   - The Hybrid scripts import `GroundPainting_2026-10-04/native_graph_stochastic.py`.
   - In total, 12 Staging folders are LIVE (2 of them created today: ReusableSky at 14:02Z, and AssetBankOperator), plus this review's new folder. Two more are pinned by profile provenance.
   - (MEASURED, parts 02, 03, 05.)
8. **Maps.**
   - During the survey, the three live map hashes matched the status: 4efebdfb, a6961c8e and c409279c.
   - After the window, the Rimal map was re-saved at 14:52:20Z and is now 1d670c8e (snapshot caveat 7).
   - No backup of the previous Iran map 623aa0c0 exists under Staging.
   - (MEASURED, parts 04, 05, reviewer.)
9. **Unreachable Content.**
    - 1,326 `Content/Project` packages (2,968 MB) are unreachable from the live roots (maps, profiles, catalog, registry chain, Python).
    - Most of them are lifecycle outputs: Cook folders (1,921 MB), 628 stale RoadBLD clip packages and 72 stale LayerInfos. About 746 MB is in the bank owner's scope.
    - Removal belongs to the owner, after the ledgers are reconciled.
    - Two LIVE dependencies sit outside `Content/Project`. The Rimal live map references `/Game/Developers/USER/HoudiniCityProof/Materials/M_GeoCity_VertexColorPreview`. 37 StarterContent packages feed the ground material.
    - (MEASURED; ownership INFERRED; part 04.)
10. **Recovery copies.**
    - The 15 `Content/Project/Shared/Recovery/ProceduralCity_20261005/DiskFunctions/*` files are unreferenced: 0 hits across 30 GB of Content, the profiles, Python and Config.
    - They are renamed re-saves of the Vault-original MW functions. Byte-exact originals exist in VaultCache and in `Staging/ProceduralCityRegeneration_2026-10-05/Before/DiskPackages/`.
    - The 18:42Z vendor modification was written by `ProceduralCityRegeneration_2026-10-05/prepare_run.py:20`, not by an "unidentified chat".
    - (MEASURED, part 03.)
11. **AGENTS.md contradicts itself.**
    - The new parallel-editor rule (line 5) conflicts with "One editor writer at a time." (line 12).
    - "Seal 3cd33b15" (line 12) conflicts with the current seal, 258469e1.
    - Line 46 still points at `ManagedAstra_2026-10-03/ASSIGNMENTS.json` as current.
    - (MEASURED, author grep; part 05.)
12. **A runtime assertion depends on a log file.** `geocity_roadbld_junctions.py:580-582` asserts that a 2026-10-03 line exists in `Saved/Logs/Environmentpipeline.log`. That log holds bearer tokens and must stay out of Git. A fresh clone, or a log rotation, fails this assertion whenever that legacy-adoption path runs (MEASURED code, author; impact INFERRED).
13. **Git size, using tested patterns.**
    - About 1.5 GB of plain text, 31-53 GB of LFS depending on whether vendor packs are excluded or tracked, and 43-65 GB excluded.
    - `core.longpaths true` is required.
    - Status §5 needs these corrections: plugins ship binaries only; there is no CitySample folder; StarterContent is LIVE; WorldBLD (8.4 GB) is missing; the `Staging/**/Before/` rule is wrong in both directions; Staging holds 10.9 GB of JSON.
    - (MEASURED, parts 04, 05.)
14. **Risks (section 4).**
    - The lease was free while an editor was open (MEASURED, 13:39Z to 14:14Z). The 14:14Z bank lease now supersedes this (MEASURED).
    - `Operator/iran_generate.py` (asserts PID 29900, which is still alive) and `copilot_client.py` are unpinned (MEASURED).
    - The Iran `launch.ps1` would start an editor and write a lease before failing (MEASURED code; sequence INFERRED).
    - v004 has never been cooked (DOCUMENTED).
    - Shujaiya cannot be regenerated (INFERRED from MEASURED code and profile), and both scripted rollbacks are unclean (MEASURED).
    - The Hybrid args still pin the superseded profile 4174a627 (MEASURED).
    - A runtime assertion depends on a log file (MEASURED code).
    - The bank operator downloads packs with the `legendary` client (MEASURED code; acceptability INFERRED open).
    - Some paths are over 260 characters (MEASURED).
15. **Owner decision (section 9).**
    - At about 15:35Z Aviv decided to keep only the latest Gaza environment, GazaShujaiya, and to delete the rest (DOCUMENTED).
    - Section 9 maps that decision onto this inventory and lists what must stay for Shujaiya and for the holds (INFERRED).
    - It flags that counting GazaRimal in "the rest" is an assumption not yet confirmed by Aviv.

## 2. Corrections to PROJECT_STATUS_2026-10-06.md

### 2.1 Status text versus today's measurements

| # | Status says | Measured today | Evidence | Label |
|---|---|---|---|---|
| 1 | §2 row "Houdini generator, 1 km": native "re-imported by the modular-bank chat (v002/v003 family derivatives); current uasset hash 3cf1f840" | The hash 3cf1f840 is correct, but it embeds the **v004** ProceduralThirty hdalc 886ab082. Lineage: 357eeac6 (r018) -> f407976c (v001) -> 1de0e6fe (v002) -> 2358c514 (v003) -> 3cf1f840 (v004). | part 01 `embed_check.py`; `PE/ModelBank/Modular_2026-10-04/ProceduralFamilies_Additional20/INTEGRATION_RECEIPT.json` (`completed_utc 2026-10-06T07:33:34Z`, PID 35156) | MEASURED |
| 2 | §3 item 2: "the native uasset embeds the `20261005_procedural_ten_families_v003` derivative (MEASURED)" | It embeds `20261005_procedural_thirty_families_v004` (the string appears 3 times). There is no v003 string. The re-import path points into the v004 folder. | part 01 section (b) | MEASURED |
| 3 | §3 item 2 fix: "register the v003 revision folder as canonical (sibling revision + REVISION.json)" | The running revision is v004. The B2 revision is v003. None of v001-v004 has a `REVISION.json` or a `definition_receipt.json`; only v001 has a `BUILD_RECEIPT.json`. Their receipts sit under `PE/ModelBank/Modular_2026-10-04/*` and `Staging/ModularConstruction_2026-10-05/Run_20261005/`. | part 01 (b); part 05 (c) | MEASURED |
| 4 | §2 row 1 km: "OPEN: ratify as B3 or roll back to ratified 2358c514" | No copy of 2358c514 exists inside UP. The only copy is in `PE/ModelBank/.../ProceduralFamilies_Additional20/Integration/Before/`. A rollback must also restore the v003 registry refs a39dbbb9 / b2e1876b in both Gaza profiles. | part 01 table D and (b); part 05 key asset copies | MEASURED |
| 5 | §3 item 1: "the 4 km semantic palette replaces `cook_surface_palette` entirely" | The live 4K root (c0cc6fdc) has the **same** `cook_surface_palette` as PB r018. Only the unpromoted r019 (a42a9fe8) replaces it. The live 4K also lacks all 33 modular-family defs. | part 01 module divergence (AST diff) | MEASURED |
| 6 | §3 item 4: four launchers | Seven distinct launchers exist: 1 LIVE (Gaza-only) and 6 DEAD. The status does not list `launch_modular_editor.ps1`, `launch_replacement_editor_PREPARED.ps1` or `launch_reviewed.ps1`. The Iran editor was started "manager_direct", without a launcher file. | part 02 launcher verdict; `Operator/IranRun_20261006/LAUNCH_PID29900.json`; lease line 485 | MEASURED |
| 7 | §3 item 5: "`ASSIGNMENTS.json` (manager id cc37d4d2, task4 operator cc37d4d2 ...)" | Correct. The status omits two things:<br>- Stale inner fields remain: `editor.current_actual_pid` 32508, `editor_activation` "...PID32508", `shared_files.area_profiles_owner` 01a10789, `created_chats` task4 01a106e8, `management_succession.successor_manager_thread_id` 01a10789 (`ASSIGNMENTS.json:201`).<br>- `BANK_ACTIVATION.json` and `BankIntegration_2026-10-04/ASSIGNMENT.json` (01a10789) are still read, so the bank branch is always refused.<br>The AGENTS.md:12 technical note states the cc37d4d2 switch correctly. Its stale part is the claim that `GENERATION_ACTIVATION.json` is validated by sealed code (no reader found). | part 02; `geocity_editor_action.py:40`; `launch_editor.ps1:26` | MEASURED |
| 8 | §3 item 6: "none should be deleted, but only the folders in §2 are live" | 12 Staging folders are LIVE (2 of them created today: ReusableSky at 14:02Z, and AssetBankOperator): AppearanceRepair, AssetBankOperator, BankIntegration, GroundPainting, Iran_4km, ManagedSystemsAstra, ModelBank, ModularConstruction, ReusableSky, ShujaiyaOrdinaryRun, SystemCompletion and ToolchainChecks. This review's new Consolidation folder makes 13. ManagedExecution and RepairExecution are pinned by profile provenance. | part 05 Staging table; part 02 runtime refs | MEASURED |
| 9 | §3 item 8: "`RunExisting_20261005/Before` ≈ 1.2 GB" | 3,599 MiB (about 3.8 GB) in 990 files. 450 packages (1,084 MiB) are byte-identical to live Content and 499 differ. 13 catalog-receipt copies add about 2.3 GB (INFERRED from name, size and mtime). | part 05 (b) | MEASURED |
| 10 | §3 item 8: "`S1_Prep/Before/S1B_*` ≈ 533 MB" | 509 MiB, which is about 534 MB. Consistent: only the units differ. | part 05 (b) | MEASURED |
| 11 | §2 row "Operator tooling": `Stage1_Ground/S1_Prep/` (verify/capture/backup) "Working" | `PathB_MW/RESEAL.md:66` says `s1_verify` and `s1_capture` assume the Natural child, so they are superseded for Shujaiya ground checks. No Hybrid script calls them; the only hit is a comment at `hybrid_build_master.py:56`. | parts 02, 03 | DOCUMENTED; MEASURED |
| 12 | §2 row "Area profiles": "or the profile rolled back: backup in `Stage1_Ground/Hybrid_Auto/Before/`" | That backup (1bd89e5b) points at the absent Path B MI `MI_GeoCityGround_MW`. The older 1328d5bb backup restores the Natural child, but it also sets `landscape_grass.enabled` to true and reverts the registry ref from 8d8622b2 to a39dbbb9. No scripted rollback is clean. | part 03 (b) | MEASURED |
| 13 | §5: track `Content/Project/**` and `Content/Python/**`, which leaves `Content/Developers` untracked | The Rimal live map references `/Game/Developers/USER/HoudiniCityProof/Materials/M_GeoCity_VertexColorPreview`. Leaving Developers untracked breaks a LIVE map. | part 04 (a) | MEASURED |
| 14 | §5: exclude `Content/MWLandscapeAutoMaterial`, `Content/StarterContent`, `Content/CitySample*` and `Content/HighPoly_Tree_Model` | StarterContent is transitively LIVE: 37 of its 270 packages feed `MI_GeoCityGround` and the Appearance textures. MW is the Hybrid's source. HighPoly is a planned bank consumer. Excluding these packs needs a pinned restore record. | part 04 (d); `AssetBankOperator_2026-10-06/EXPANSION_SUMMARY.json` | MEASURED; DOCUMENTED |
| 15 | §5: `Content/CitySample*` | No CitySample folder exists in Content. City Sample lives in VaultCache (`CitySample_5.8`) and in the separate CitySample project. | parts 04 (d), 05 (d) fact 3 | MEASURED |
| 16 | §5 vendor list does not name WorldBLD | `Content/WorldBLD` is 8,379 MB, has no VaultCache backing, and is the largest Content folder. It has 0 references from LIVE roots; Stage1Kit references 24 of its assets. | part 04 (a), (d) | MEASURED |
| 17 | §5 vendor list does not name 14 other packs | Another 14 VaultCache-backed packs hold 12,161 MB. Each is file-for-file identical to its VaultCache folder. | part 04 (d) | MEASURED |
| 18 | §5: track "`Plugins/` sources (not binaries)" | RoadBLD, CityBLD, TwinBLD and WorldBLDMCPToolset ship `Binaries/` and **no** `Source/`. WorldBLD has 218 MB of Binaries and 2 MB of Source. `Plugins/RoadBLD/RoadBLD.uplugin:96` declares a dependency on WorldBLD. Excluding binaries would break the road role. | part 05 (d) fact 2; author read of `RoadBLD.uplugin` | MEASURED |
| 19 | §5: exclude `Staging/**/Before/` | The pattern misses BeforeNative, BeforeOrdinaryReplacement, BeforeGroundShader, BeforeTone, SamplerBefore, EpicBefore_R027, EpicResidentBefore_R028, EpicRimalBefore_R031 and SafeStartupConfigPreserve_*. It would also drop pinned JSON: `Hybrid_Auto/Before/AREA_PROFILE_1bd89e5b_*.json`, `PathB_MW/Before/AREA_PROFILE_1328d5bb_*.json`, and `S1B/BACKUP_MANIFEST.json` (pinned as c32afcdb in ASSIGNMENT.json). | part 05 (d) fact 5 | MEASURED |
| 20 | §5: track `Staging/**` text (json/md/txt/py/ps1) | Staging holds 74 JSON files over 20 MB, about 10.9 GB in total. 54 JSON files exceed 100 MB; the largest is `ALL40_INTERVALS` at 720 MB. GitHub rejects files over 100 MB outside LFS. | part 05 fact 6 | MEASURED |
| 21 | §5: "Second repository (or submodule)" for PE | A PE repo already exists: commit `dfb49ef`, one commit from 2026-09-27, with 681 MB of LFS objects. Its working tree shows 702 deleted, 8 modified and 44 untracked files. The profiles reference PE by absolute paths, so a submodule does not fit. | part 05 (c), (d) | MEASURED |
| 22 | §5 is silent about existing Git files | The Unreal root already has a `.gitignore` and a `.gitattributes` from 2026-09-27. The Unreal `.git` was deleted on 09-27 at Aviv's request ("no git"). The nested `Environmentpipeline/.git` is a separate one-commit clone with remote Samorai-Studio/Environmentpipeline. | part 05 (d) fact 1; `Staging/Archive/PreFinalVision_2026-09-29/Baseline/GitBaseline_2026-09-27/BASELINE_REPORT.md`; part 00b | MEASURED; DOCUMENTED |
| 23 | §5 is silent about runtime dependencies on logs | `geocity_roadbld_junctions.py:580-582` asserts that a 2026-10-03 line exists in `Saved/Logs/Environmentpipeline.log`, a file that §5 rightly excludes. | author read of lines 576-584 | MEASURED |
| 24 | §5: "Use Git LFS for `*.uasset *.umap *.hdalc *.png *.t3d`" | The existing `.gitattributes` already has 78 LFS patterns (author count of `filter=lfs` lines). It is missing `.r8 .bin .b64 .pyd .ttf .otf .ico` and the names of the large JSON/HTML receipts. | part 05 (d); author count | MEASURED |
| 25 | §5: "large DEM/OSM acquisitions via LFS or excluded" | The Copernicus DEM tile N31 E034 (27.6 MB, d157903d) exists 5 times, byte-identical, so 110 MB is redundant. Its hash is recorded in 5 manifests. | part 05 (c) | MEASURED |
| 26 | §6: "Last lease line ... `OWNER=NONE released_phase=baked_saved_verified` (13:39:07Z)" | Since 14:14:05Z the last line is `OWNER=ASSET_BANK_OPERATOR` on PID 29900. The lease file changed again at 14:48:43Z. | parts 03, 04; author listing | MEASURED |
| 27 | §2 row "Documentation of record": "`AGENTS.md` (first paragraph = current governance)" | Since 14:22Z a new top section (parallel editor rule; Reusable Sky activation) sits above that paragraph. It "supersedes the earlier project-wide single-editor/single-writer restrictions below". The former first paragraph is now line 12. | `AGENTS.md:3-9` (author) | MEASURED |
| 28 | §3 item 3: "Keep only Hybrid + Natural; mark the rest as historical in their READMEs" | LIVE Hybrid inputs and rollback tools sit inside the superseded folders: `PathB_MW/TINT_PRESETS.json` (read at `hybrid_build_master_offline.py:428`); `PathB_MW/pathb_profile_patch.py` (rollback, `Hybrid_Auto/README.md:276`); `PathB_MW/Before/AREA_PROFILE_1328d5bb_*`; `S1_Prep/AstraMWInventory/native_inventory_complete.json` (`hybrid_build_master_offline.py:426`); `GroundPainting_2026-10-04/native_graph_stochastic.py`. Add banners only; move nothing. | part 03 | MEASURED |
| 29 | §3 item 7: Recovery copies "made by an Astra inspection" | Consistent. They are also renamed re-saves (`inspect_dirty_materials.py:19,26`), 48 to 909 B larger than the originals. The earlier vendor modification was saved by `prepare_run.py:20`. | part 03 | MEASURED; DOCUMENTED |
| 30 | §2 row "Area maps": Iran "re-saved today 13:39Z, fresh reopen pending" | Consistent. The status does not mention that no Staging backup of the previous Iran map 623aa0c0 exists. | parts 04, 05 | MEASURED |
| 31 | §2 row 1 km: "`definition_receipt.json` says r018" | Consistent: the PB root hdalc 61303c15 and module e67b6e15 match their receipt. However, no live native has embedded r018 since 2026-10-05 15:29Z. | parts 01, 05 | MEASURED |
| 32 | §2 rows "Asset bank" and "Area profiles": catalog f763b072 (digest f6fff4f9 Gaza, 2e1e548f Iran), 1,223 identities; profiles 4174a627 / 492b9ac5 / 004ec07d | These values were correct until 14:25Z. They were superseded in-window at 14:32:57-58Z:<br>- catalog e26bf06c, row_count 1,295, catalog_sha256 e0bd4e85 (Gaza) / a2d14c36 (Iran);<br>- profiles f722381f / e6dead27 / cb0f3cab;<br>- `decision_receipt` now points to `AssetBankOperator_2026-10-06/Activation/DECISION.json`.<br>The old profiles survive only in `AssetBankOperator_2026-10-06/Before/`. | reviewer hashes; author listing of mtimes, sizes, `Before/` and `Activation/` | MEASURED |
| 33 | §2 row "Area maps": Rimal a6961c8e | Re-saved at 14:52:20Z, after the survey window. Now 1d670c8e; a6961c8e is kept in `ReusableSky_2026-10-06/Before/`. | reviewer hash; author listing | MEASURED |

### 2.2 Other records (not PROJECT_STATUS) that disagree with measurements

| Record | Says | Measured today | Label |
|---|---|---|---|
| `Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/RATIFICATION_B2.json:15-18` | native 2358c514 = "v002 modular source families derivative" | 2358c514 embeds the v003 ProceduralTen hdalc 462f1d50. INFERRED: "v002" is the family-id suffix `source_derived_modular.*.v002`. | MEASURED; INFERRED |
| `AGENTS.md:12` technical note | "BANK_ACTIVATION.json system_owner and GENERATION_ACTIVATION.json manager_thread_id are also validated by the sealed launcher and by geocity_editor_action" | Half true. `BANK_ACTIVATION.json` is read (`geocity_editor_action.py:30`, `launch_editor.ps1:20-25`). Grep finds no reader of `GENERATION_ACTIVATION` in `Content/Python` or `launch_editor.ps1`. The note's first clause, that ASSIGNMENTS was switched to the Claude session id on 2026-10-05 20:02Z, is correct. | MEASURED (author grep) |
| `AGENTS.md:12` | "Seal 3cd33b15 / geocity_bank_workflow f349d128 stay unchanged" | The current seal is 258469e1. Its only difference from 3cd33b15 is props bf59bf96 -> 2bf41ec3 (RATIFICATION_B2). | MEASURED; DOCUMENTED |
| `AGENTS.md:12` versus `AGENTS.md:5` | "One editor writer at a time." versus "Multiple Unreal Editor instances may work in parallel" | Direct contradiction since 14:22Z. Line 5 says it supersedes "the earlier project-wide single-editor/single-writer restrictions below". | MEASURED |
| `AGENTS.md:46` | "the [current Astra assignments](Staging/ManagedAstra_2026-10-03/ASSIGNMENTS.json)" | That file's root control is `READONLY_AUDIT_NATIVE_INSPECTION_PENDING_NO_EDITOR_ACTIVATION`, i.e. historical. | MEASURED |
| AGENTS.md historical paragraph | "exactly 3 dirty Palms_Pack_01 originals" | `Content/Palms_Pack_01` is 353/353 byte-identical to VaultCache today. INFERRED: those edits were never saved, or were restored. | MEASURED; INFERRED |
| `Staging/ModelBank/README.md` (09-29) | "zero assets qualified" | Stale: the catalog had 1,223 identities at the survey (row_count 1,295 since 14:32:57Z), and Bank_ME_v3 is LIVE. | MEASURED |
| Root `README.md`, paragraph 2 | the surface route is `GeoCity_city_v013_AllSurfacePalette` | The live generator is v015. No map references v013. | MEASURED |
| `Incident_01a10c77_2026-10-05/MW_Func_modified_20261005T202743Z/RESTORE_RECEIPT.json` and the handoff | the vendor functions were saved by an "unidentified chat" | `Staging/ProceduralCityRegeneration_2026-10-05/prepare_run.py:20` (`save_loaded_asset(asset, only_if_is_dirty=True)`) saved all 15. `PREPARATION.json:31` lists them, and the CombineNormal `saved_sha256` 65800a1e equals the receipt's `modified_sha256`. | MEASURED; DOCUMENTED |
| `Stage1_Ground/PathB_MW/DESIGN.md:3` | "Nothing here was executed in Unreal" | The PID34928 receipts record `APPLIED_VERIFIED_NO_SAVE`, an in-memory apply. | MEASURED |
| `Stage1_Ground/S1_Prep/README.md:3` | "PREPARED, NOT EXECUTED" | The `S1_APPLY_*` and `S1_TUNE_*` receipts on PID23156 record an apply and a tune. Both were discarded without saving (`STAGE1_GROUND_PLAN.md:304-305`). | MEASURED; DOCUMENTED |
| `Staging/UNREAL_DEPENDENCY_REVIEW_2026-09-29.md:11` | "The shared Districts and Landscape assets are historical Stage 1 material" (exact words; the literal path string `Shared/Landscape` does not occur in the file) | `M_Landscape_GazaRimal` in `Content/Project/Shared/Landscape/` is named by all three live maps (part 04; author re-grep of the Shujaiya map: 1 hit). The claim holds for Districts but not for this Landscape material. | MEASURED |
| `Staging/SystemCompletion_2026-10-04/RESULT.txt` | "ORIGINAL SHUJAIYA ORDINARY OPERATION ACTIVE; DELIVERY NOT YET COMPLETE" | Stale. Later runs passed: Shujaiya on 2026-10-05 at 18:43Z and Iran today at 13:39Z. | MEASURED |
| `Staging/SystemCompletion_2026-10-04/LAUNCH_STATE.json` | the launch state of the current editor | It has the same size and mtime as `LAUNCH_STATE_PID23068.json`, while the running editor is PID 29900. The file was not opened, so "stale" is INFERRED. | MEASURED; INFERRED |
| Earlier reference counts ("31/10 references") | `Staging/Operator/` duplicates `ShujaiyaOrdinaryRun_2026-10-05/Operator/` | `Staging/Operator/` is a 2-file tombstone (README.md and STOP). The hits were substrings of `.../ShujaiyaOrdinaryRun_2026-10-05/Operator`. | MEASURED |
| part 05, section (c) | "The native uasset now embeds the v003 derivative (status §3.2)" | Part 01's byte embed check supersedes this: the native embeds v004. | MEASURED |
| part 05, section (b) | "No byte copy of 2358c514 exists anywhere"; a B3 rollback "would mean re-importing from a PE revision `.hdalc`" | Part 05 did not search `PE/ModelBank`. Part 01 found a byte copy there. A file restore is therefore possible, but that file is the only copy. | MEASURED |
| part 05, section (c) | 4K hdalc dated "2026-10-04 12:33Z" | Part 01 dates it 2026-10-04T09:33Z. INFERRED: part 05 printed local time with a Z suffix. | MEASURED; INFERRED |
| part 05, section (a) | Staging has "35 folders and 8 loose .md files" (43 entries) | The author's listing at about 14:50Z, taken before this Consolidation folder existed, shows 33 folders and 10 `.md` files (43 entries). | MEASURED |
| The brief for this document | Supply folder at `Staging/ModelBank/Supply/` | `Content/Project/Shared/ModelBank/Supply/` exists. The Staging path does not. | MEASURED |
| part 00b | `Plugins/WorldBLD` is HISTORICAL | `Plugins/RoadBLD/RoadBLD.uplugin:96` declares WorldBLD (Enabled true) as a dependency, so the WorldBLD plugin is LIVE. | MEASURED |
| part 05, (d) fact 4 | "WorldBLD content backs RoadBLD" | The plugin dependency is real (row above). The content is not referenced: `Content/WorldBLD/Assets` has 0 references from LIVE roots, even through plugin content. Part 04's plugin-aware closure added 0 `/Game` packages. | MEASURED |

## 3. Classified inventory

### How the classes were applied

- **One class per row.** Each row's Class cell holds exactly one of LIVE, DUPLICATE, DEAD or HISTORICAL. Qualifiers go in the "Duplicates / why dead" cell. These include planned/absent, transitional, pinned, vendor payload, candidate, rollback point and CONFLICT.
- **LIVE.** The item is used by the current sealed runtime or the current plan. This covers:
  - items that a LIVE map, profile, catalog or registry chain references;
  - rollback points that the current plan names;
  - folders being written by an active task;
  - the vendor payload of a LIVE plugin or pack.
- **DUPLICATE.** The item is a second copy or a parallel route of a LIVE item. Examples are a byte copy, a renamed re-save, an unpromoted fork and a parallel client.
- **DEAD.** The item does not work, failed, or is blocked by its own records. Part 04 also classed orphaned generated outputs as DEAD when they have zero referrers. Where a DEAD class rests only on "unreferenced", the row says so.
- **HISTORICAL.** The item is superseded and kept only as evidence.
  - Part 01's rule: a byte copy of a non-LIVE item takes the original's class, and the row says "byte copy of X".
  - Part 05's "HISTORICAL-PINNED" becomes HISTORICAL plus the note "pinned by profile provenance; keep at path".
- **CONFLICT.** "CONFLICT: part X = A, part Y = B" means two parts disagreed. Both statements are kept, and the class shown is the author's choice. The reason uses the mission's definitions and is labelled INFERRED.
- **Referenced by LIVE?** This column answers whether any LIVE item (map, profile, catalog, registry, sealed runtime, launcher, current plan or pinned script) points at the item.
- **Total.** 367 rows are classified: LIVE 131, DUPLICATE 20, DEAD 37, HISTORICAL 179 (MEASURED by counting Class cells after the review fixes). That is 366 before the fixes, plus one new LIVE row for the survey-time profile copies in 3.7. The Rimal prior-state copies moved from DUPLICATE to HISTORICAL.
- **Deliberately not classified:**
  - the hold assets themselves (H0013, H0907, H0051, H0958, H0094) and the 87 unvalidated road candidates, which are untouched and mentioned only. Folders that contain them (e.g. `Bank_ME`, `Bank_ME_v2`, `Prepared/Modular/H0013/Procedural_v002`, the clip run in 3.8) are classified as folders;
  - `Content/Project/Shared/ModelBank/Supply/` (appeared mid-audit);
  - the PE documents `AGENTS.md`, `AREA.md`, `Handoff/` and `Research/` (not reviewed).

### 3.1 Documentation of record and governance files

The four Staging-level documents of record (`PROJECT_STATUS_2026-10-06.md`, `MANAGER_HANDOFF_2026-10-06.md`, `CURRENT_STATE.md`, `WORK_PLAN.md`) have their rows in 3.14. The Hybrid plan is in 3.9.

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Project instructions (29,136 B; mtime 14:22:58Z) | `AGENTS.md` | LIVE | Governance of record, but internally inconsistent since 14:22Z:<br>- line 5 parallel rule vs line 12 "One editor writer at a time.";<br>- line 12 "Seal 3cd33b15" vs current 258469e1;<br>- the line 12 technical note says `GENERATION_ACTIVATION.json` is validated by the sealed launcher and `geocity_editor_action`, but no reader exists (its ASSIGNMENTS clause is correct);<br>- line 46 calls ManagedAstra current.<br>About 15 historical paragraphs remain below line 12. | `AGENTS.md:3-9` (author read); `:12`, `:22`, `:46` (author grep) | Is the governance root | MEASURED |
| Shujaiya run assignment | `Staging/ShujaiyaOrdinaryRun_2026-10-05/ASSIGNMENT.json` | LIVE | `status.state` was `IRAN_ORDINARY_RUN_PASSED_EDITOR_IDLE` at the survey. Since 14:18:18Z it is `EDITOR_PID29900_LEASED_TO_ASSET_BANK_CHAT_BY_AVIV_HYBRID_WAITS` (`:44`). Names the S1B backup set (`:51`) and `s1_backup_manifest_sha256` c32afcdb (`:52`). Its `waiting_for` names the Hybrid. | part 05 Staging table; part 03; author grep and mtime | `AGENTS.md:12` | MEASURED |
| Run plan | `Staging/ShujaiyaOrdinaryRun_2026-10-05/PLAN_PROPOSAL.md` | LIVE | Run sequence:<br>- `:59` says launch_reviewed "cannot pass after a ground release";<br>- `:119` says never run the menu under OWNER=NONE;<br>- step 3 requires RoadBLD ledger reconciliation;<br>- step 5 uses `launch_editor.ps1`. | part 02 | `AGENTS.md:12` | DOCUMENTED |
| Stage 1 ground plan | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/STAGE1_GROUND_PLAN.md` | HISTORICAL | The manager's banner (line 3, 14:18:18Z) says the Hybrid plan supersedes it. `:304-305` v1 rejected; `:309-310` Path B chosen earlier; `:310` v2a shelved. | part 03 | `AGENTS.md:12` still links it as the Stage 1 plan | MEASURED; DOCUMENTED |
| Incident folder | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/` | LIVE | Holds RATIFICATION_B2.json (next row), `DECISION_HYBRID_20261006.json` (`:6` decision, `:23` Path B superseded), `DECISION_LET_RUN_FINISH.json` (`:63-64`) and `MW_Func_modified_20261005T202743Z/` (evidence, see 3.10). | parts 01, 02, 03 | `AGENTS.md:12` | MEASURED |
| B2 ratification | `.../Incident_01a10c77_2026-10-05/RATIFICATION_B2.json` | LIVE | The binding B2 record: seal 258469e1 at `:7-9`, native 2358c514 at `:15-18`. Label conflict: `:15-18` says "v002 modular source families derivative", but the bytes are v003 ProceduralTen. | part 01 (b); part 02 seal check | `AGENTS.md:12` | MEASURED |
| Bank editor inspection | `Staging/ShujaiyaOrdinaryRun_2026-10-05/BankEditorInspection_2026-10-05/INSPECTION.md` | LIVE | Step (1) of the AGENTS sequence. Lists the six failed modular parts (`:16-18`). | part 04 (c) dangling refs | `AGENTS.md:12` | DOCUMENTED |
| Root README | `README.md` | HISTORICAL | Stale. Points at the superseded `GeoCity_city_v013_AllSurfacePalette` HDA and the SurfacePainting README as the surface route. | part 00b (paragraph 2) | No live link | MEASURED; INFERRED |
| Licence-looking file | `Liscenses.rtf` | HISTORICAL | Attribution list for four Wikimedia paintings (T_Painting01-04), a StarterContent-style leftover. Not a project licence record. | part 00b | No | MEASURED |
| Vendor preview image (83 KB) | `AssetsvilleTown.png` | HISTORICAL | Preview image for `Content/AssetsvilleTown` | part 00b | No | MEASURED |
| Model bank README | `Staging/ModelBank/README.md` | HISTORICAL | Stale: "zero assets qualified" (09-29) | part 05 | No | MEASURED |
| SurfacePainting README | `Staging/ModelBank/SurfacePainting/README.md` | HISTORICAL | Records that the old Rimal SurfacePainting map stays on its accepted v002 HDA (`:11`). `:5` names the v013 definition. | part 04; author read of `:5` and `:11` | No | DOCUMENTED |
| Old Astra assignments | `Staging/ManagedAstra_2026-10-03/ASSIGNMENTS.json` | HISTORICAL | `latest_root_control_20261004.status=READONLY_AUDIT_NATIVE_INSPECTION_PENDING_NO_EDITOR_ACTIVATION`. `AGENTS.md:46` still calls it "current Astra assignments" (stale pointer). | part 05 | No runtime use | MEASURED; DOCUMENTED |

### 3.2 Houdini generators and every HDA copy

Sources: part 01 for all rows, except where noted. Part 01's per-file record (path, size, mtime, sha256 and other copies, including embeds) for all 442 `.hdalc`/`.hda` files under `PE/Houdini` and `UP/Staging` is `hda_files_inventory.tsv` in the session scratchpad. That file is temporary (see Appendix A). Embed method (MEASURED): a Houdini Engine native `.uasset` stores the full `.hdalc` bytes from the `INDX` header, preceded by an int32 length. Each slice was compared byte-for-byte with every `.hdalc` on disk.

#### 3.2.A 1 km generator, `PB` (`trackb::geocity_city::15.0`, `GRID_SAMPLES = 1009`)

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| PB root definition (r018) | `PB/GeoCity_city_v015_PermanentBank.hdalc` (61303c15, 498,556 B, 2026-10-03T11:47Z); `PB/geocity_city_module.py` (e67b6e15, 327,851 B); `PB/definition_receipt.json` | HISTORICAL | Canonical by receipt only. No live native has embedded it since 2026-10-05 15:29Z. It is the base of v001-v004 and of the 4K fork. Keep in place. | `definition_receipt.json`: `"revision": "r018_retained_appearance"`, hda/module hashes match disk; the module text is embedded verbatim in the hdalc | Yes, indirectly: `base_hda_sha256` of v001 (`BUILD_RECEIPT.json`); `source_hda_sha256` of 4K (`Staging/Iran_4km_2026-10-04/HDA_DEFINITION.json`); r019 `REVISION.json` | MEASURED; DOCUMENTED |
| PB helper and authoring scripts | `PB/permanent_bank_module.py` (50ae9530, byte-identical to copies in r007/r010/r011/r012), `build_v015.py`, `repair_v015.py`, `update_r007.py`, `promote_material_default.py`, `add_material_slot_metadata.py`, `repair_and_diagnose.py`, `inspect_definition.py` | HISTORICAL | One-shot authoring scripts | mtimes 2026-10-02 | No | MEASURED |
| PB auto-backups (24.1 MB) | `PB/backup/` (63 `*_bakN.hdalc`) | HISTORICAL | 26 of 63 are unique states.<br>Only copies anywhere: bak61 (457,869 B) and bak62 (498,222 B), both 10-03T11:47Z, the only r017-era states (no r017 folder exists); bak49 (r015 era); 23 earlier 10-02 states.<br>Byte copies: bak63 = root; bak45/46 = r014; bak55/56 = r016 saved-native embed; bak57/58 = r016 unversioned_winding; bak59/60 = AppearanceRepair ExternalHDA. | `hda_files_inventory.tsv`, column `other_copies` = `-` | No | MEASURED; INFERRED (bak61 = r017) |
| PB revisions r001-r016 (20 folders, incl. the three byte-copy folders in the next row; author `ls -d revisions/r0*` = 20) | `PB/revisions/r001` ... `r016_inward_roof_before_repair` | HISTORICAL | Chain of 2026-10-02/03 states, each with hdalc, module and `definition_receipt.json`. No r017 or r018 folder exists; r018 exists only at the PB root. | per-folder sha256 list | No | MEASURED |
| PB revision byte copies | `PB/revisions/r007_task4_before` (hdalc 2289565d and module a20e53f7 = r007); `r012_road_repair_before` (hdalc 6cdf9bc6 = r012); `r014_fix_start` (module 76dfce80 = r014) | HISTORICAL | Byte copies of retained HISTORICAL files (part 01 rule). Only the listed files were compared; the folders' own receipts were not. | sha256 | No | MEASURED |
| r016 archive folder | `PB/revisions/r016_inward_roof_before_repair/` (`HDA_CATALOG_RECEIPT.json` 169,581,535 B; `WORKFLOW_STATE.json` 253 KB, not opened; `r016_saved_native_HDA.uasset` 2d99201f, which embeds 22951961 = bak55/56; `unversioned_winding_before_r017.hdalc` debe33ea) | HISTORICAL | Evidence of the r016 -> r017 roof-winding repair. The 170 MB receipt is 76% of the 223 MB PB folder. | `ARCHIVE_NOTE.txt`: "it is not the original r016 external HDA" | No | MEASURED |
| v001 modular source families | `PB/revisions/20261005_modular_source_families_v001/..._ModularFamilies_v001.hdalc` (b5ab917a, 538,743 B, 10-05T13:48Z), `BUILD_RECEIPT.json`, module 616e2512 | HISTORICAL | Superseded by v002 at about 15:49Z. Embedded in native f407976c (Attempt1). | `BUILD_RECEIPT.json`: `"passed": true`, `"base_hda_sha256": "61303c15..."`, `"actual_stage_cook": false` | No | MEASURED; DOCUMENTED |
| v002 modular source families | `PB/revisions/20261005_modular_source_families_v002/..._ModularFamilies_v002.hdalc` (ebcc8b7d, 539,206 B, 10-05T15:47Z), module 38db2e77 | HISTORICAL | Superseded by v003 at 17:43Z. No receipt in the folder. | `Staging/ModularConstruction_2026-10-05/Run_20261005/ATTEMPT2_START.json`: `"source_after_sha256": "ebcc8b7d..."`, native `"after_sha256": "1de0e6fe..."` | No | MEASURED; DOCUMENTED |
| v003 procedural ten families | `PB/revisions/20261005_procedural_ten_families_v003/..._ProceduralTen_v003.hdalc` (462f1d50, 573,627 B, 10-05T17:41Z), module da279972 | LIVE | Source of the ratified B2 rollback target: it is embedded in 2358c514. No receipt in the folder. | `PE/ModelBank/Modular_2026-10-04/ProceduralFamilies/INTEGRATION_RECEIPT.json`: `"completed_utc": "2026-10-05T17:43:01Z"`, `"native_saved_uasset_sha256": "2358c514..."`, `"hda"."sha256": "462f1d50..."`, PID 10460 | Yes (B2 baseline, RATIFICATION_B2) | MEASURED; DOCUMENTED |
| v004 procedural thirty families | `PB/revisions/20261005_procedural_thirty_families_v004/..._ProceduralThirty_v004.hdalc` (886ab082, 573,667 B, 10-06T07:22Z), module 037018e1 | LIVE | Running and unratified (B3 open). The native's re-import path points here. No receipt in the folder. | `PE/ModelBank/Modular_2026-10-04/ProceduralFamilies_Additional20/INTEGRATION_RECEIPT.json`: `"completed_utc": "2026-10-06T07:33:34Z"`, `"native_saved_uasset_sha256": "3cf1f840..."`, `"native_city_regeneration_performed": false`, PID 35156 | Yes (current native, via the Gaza profiles and maps) | MEASURED; DOCUMENTED |
| v003/v004 final-state backups | `..._v003/backup/..._ProceduralTen_v003_bak16.hdalc`; `..._v004/backup/..._ProceduralThirty_v004_bak5.hdalc` | DUPLICATE | Byte copies of LIVE v003 (462f1d50) and LIVE v004 (886ab082) | sha256 | No | MEASURED |
| v003/v004 intermediate backups | `..._v003/backup/` (15 others), `..._v004/backup/` (4 others) | HISTORICAL | 19 unique intermediate saves (v003 15, some as identical pairs; v004 4) | `hda_files_inventory.tsv` | No | MEASURED |
| v001/v002 backups | `..._v001/backup/` (6), `..._v002/backup/` (3) | HISTORICAL | v001 bak6 = v001; v002 bak3 = v002 | sha256 | No | MEASURED |

#### 3.2.B 4 km generator, `4K` (`trackb::geocity_city::15.1`, `GRID_SAMPLES = 4033`)

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| 4K root definition | `4K/GeoCity_city_v015_4km.hdalc` (c0cc6fdc, 500,060 B, 10-04T09:33Z), `4K/geocity_city_module.py` (7b1d5ca4, 329,454 B) | LIVE | Forked from PB r018 (61303c15). No `definition_receipt.json` in the folder (part 05). Time conflict: part 05 printed 12:33Z (INFERRED: local time). | `Staging/Iran_4km_2026-10-04/HDA_DEFINITION.json`: `"hda_sha256": "c0cc6fdc..."`, `"grid_samples": 4033`, `"status": "official_engine_cooked_baked_saved_and_map_reopened"`; embedded byte-exact in native 43ca7d0e | Yes (Iran native, profile, map) | MEASURED; DOCUMENTED |
| 4K final-state backup | `4K/backup/GeoCity_city_v015_4km_bak12.hdalc` | DUPLICATE | Byte copy of the LIVE 4K root c0cc6fdc | sha256 | No | MEASURED |
| 4K intermediate backups (5.4 MB) | `4K/backup/` bak1-bak11 | HISTORICAL | Authoring steps of the 4 km fork on 10-04 (08:55-09:18Z). All 11 are unique states with no copy elsewhere. | `hda_files_inventory.tsv` | No | MEASURED |
| r019 semantic categories | `4K/revisions/20261004T113908374370Z_r019_semantic_categories/` (hdalc a42a9fe8, 530,894 B; module e854c9d9; `REVISION.json`) | DEAD | Blocked by its own record (parked, not failed). Never promoted to native. Replaces `cook_surface_palette` and adds 23 semantic defs. The only copy of the semantic-palette logic, so keep it with r020. | `REVISION.json`: `"status": "RETAINED_EXTERNAL_DEFINITION_IMPLEMENTED_NATIVE_PROMOTION_NOT_RUN"`; `known_incomplete[0]`: "Water class80 needs supported native treatment before complete Bake" | No (predecessor of r020 only) | MEASURED; DOCUMENTED |
| r019 backup | `.../r019_semantic_categories/backup/GeoCity_city_v015_4km_bak1.hdalc` | DUPLICATE | Equals the LIVE 4K root c0cc6fdc | sha256; embed match | No | MEASURED |
| r019 record copy | `Staging/PipelineSemanticRepair_2026-10-04/RETAINED_SOURCE_REVISION.json` | HISTORICAL | Byte-identical to r019 `REVISION.json` (03229dad) | sha256 | No | MEASURED |
| r020 use-aware buildings (receipted) | `4K/revisions/20261004T121230879087Z_r020_use_aware_buildings/` (hdalc fa4388c1, 569,610 B; module 32fb0d16; `REVISION.json`; `authoring_history/` 3; `backup/` 12) | DEAD | Blocked by its own record (parked). Built on r019. Unreal was never run. The only copy of the use-aware building logic. | `REVISION.json`: `"status": "HOUDINI_BUILDING_LOGIC_AND_GEOMETRY_VERIFIED_CONTENT_DEPENDENCIES_OPEN_UNREAL_NOT_RUN"`; `Staging/IranBuildingAdaptation_2026-10-04/HANDOFF.json` gives the same status | No | MEASURED; DOCUMENTED |
| r020 orphan first folder | `4K/revisions/20261004T121206056541Z_r020_use_aware_buildings/` (hdalc 7d7661f0, module 12ec4696, `backup/` 1) | DEAD | Aborted first start with no `REVISION.json`. Its module = `...121230.../authoring_history/20261004T121950039977Z/geocity_city_module.py` (12ec4696). | Missing receipt; `HANDOFF.json` names only the `...121230...` folder | No | MEASURED |

#### 3.2.C Other folders in `PE/Houdini/` (37 folders, about 130 MB besides v015)

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Legacy generators v001-v014 and pilots | `PE/Houdini/GeoCity_v001`, `GeoCity_city_v002` ... `v014*` (incl. `_SurfacePainting_v001/v002`, `v008_*Prototype/Pilot/Forensics`, `v009_ModularPilot`, `v009_SecondAreaOffline`, `v010_NonBuildingPilot`, `v011_NonBuildingBank`, `v012`-`v014` palette) | HISTORICAL | Superseded by v015 (2026-10-02) | Each folder has its own `RESULT.md` / `definition_receipt.json`. Top-level hdalc hashes, e.g. v014 da725275, v013 a1fc268a, v007 4fbd2e4c. | No | MEASURED |
| Proof and layout folders | `CityProof` (B1/B2, 22 hdalc), `BuildGenPadLayout_v001`, `ModularLayout_v001` ... `v005_Concave`, `ModularCoverageSensitivity_v001`, `EntranceSite_1010234236_v001` | HISTORICAL | Narrow proofs. Keep CityProof in place. | `PE/Houdini/README.md`: "CityProof/ ... narrow tests ... Keep them in place because path behavior after moving them is untested" | No | DOCUMENTED |
| Failed build file | `PE/Houdini/GeoCity_city_v007_SurfacePainting_v001/GeoCity_city_v007_SurfacePainting_v001.failed_build.hdalc` (ff3ceebb) | DEAD | The filename says the build failed | filename | No | MEASURED |
| Failed dispatch file | `PE/Houdini/GeoCity_city_v009_ModularPilot/GeoCity_city_v009_ModularPilot.failed_module_dispatch.hdalc` (fdef96d9) | DEAD | The filename says the dispatch failed | filename | No | MEASURED |

#### 3.2.D Native HDA assets and HDA copies in UP and `PE/ModelBank`

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Native 1 km HDA (current) | `Content/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank.uasset` (3cf1f840, 576,822 B, 2026-10-06T07:33Z) | LIVE | Unratified; B3 is open. Embeds v004 886ab082 byte-exact. Its strings contain `20261005_procedural_thirty_families_v004` 3 times and no v003/v002 string. Outside the seal (no HDA hash in the manifest; profiles carry only the asset path). | `embed_check.py`; `grep -a`; `geocity_bank_workflow.py:1020` `api.instantiate_asset(unreal.load_asset(self.p['hda']), ...)` (author) | Yes: `L_GazaShujaiya_BankIntegration.umap` (4efebdfb), `L_GazaRimal_BankIntegration.umap` (a6961c8e), profile key `"hda"` in both Gaza profiles | MEASURED |
| Native 4 km HDA | `Content/Project/Shared/ModelBank/HDA/GeoCity_city_v015_4km.uasset` (43ca7d0e, 502,822 B, 2026-10-04T09:34Z) | LIVE | Embeds the 4K root c0cc6fdc. Re-import path `.../GeoCity_city_v015_4km/GeoCity_city_v015_4km.hdalc`. No drift. | `embed_check.py` | Yes: `L_Iran_38196167_46086167_4km.umap` (c409279c), Iran profile `"hda"` | MEASURED |
| B2 native snapshot (ratified) | `PE/ModelBank/Modular_2026-10-04/ProceduralFamilies_Additional20/Integration/Before/GeoCity_city_v015_PermanentBank.uasset` (2358c514, 576,758 B, 10-05T17:43Z) | LIVE | The ONLY on-disk copy of the ratified B2 native. Embeds v003 462f1d50. Looks like a routine backup. The pre-v004 profile backups sit in the same folder. CONFLICT: part 05 says no copy exists anywhere, but part 05 did not search `PE/ModelBank`. | v004 `INTEGRATION_RECEIPT.json` `"native_backup"` points here | Yes (rollback target in status §2 and RATIFICATION_B2) | MEASURED |
| v002 native snapshot | `PE/ModelBank/Modular_2026-10-04/ProceduralFamilies/Integration/Before/GeoCity_city_v015_PermanentBank.uasset` (1de0e6fe, 542,347 B, 10-05T15:49Z) | HISTORICAL | The only copy of the v002 native. Embeds v002 ebcc8b7d. | `ATTEMPT2_START.json` `"after_sha256": "1de0e6fe..."` | No | MEASURED |
| v001 native snapshot | `Staging/ModularConstruction_2026-10-05/Run_20261005/Attempt1/GeoCity_city_v015_PermanentBank.uasset` (f407976c, 541,884 B, 10-05T15:29Z) | HISTORICAL | The only copy of the first-ratified native ("native HDA f407976c", `AGENTS.md:12`). B2 superseded it. Embeds v001 b5ab917a. | `ATTEMPT2_START.json` `"before_sha256": "f407976c..."` | No | MEASURED; DOCUMENTED |
| r018 native snapshot | `Staging/ModularConstruction_2026-10-05/Run_20261005/Before/GeoCity_city_v015_PermanentBank.uasset` (357eeac6, 501,448 B, 10-03T11:47Z) | HISTORICAL | The only native copy of the canonical r018 import. Embeds PB root 61303c15. | `embed_check.py` | No | MEASURED |
| r018 native snapshot, second copy | `Staging/ModularConstruction_2026-10-05/Bindings/Before/GeoCity_city_v015_PermanentBank_before.uasset` (357eeac6, mtime 10-05T13:54Z) | HISTORICAL | Byte copy of `Run_20261005/Before` (part 01 rule) | sha256 | No | MEASURED |
| AppearanceRepair before (native and hdalc) | `Staging/AppearanceRepair_2026-10-03/Before/Content/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank.uasset` (e2de089d); `.../Before/ExternalHDA/GeoCity_city_v015_PermanentBank.hdalc` (bd62ec4d) | HISTORICAL | The native embeds bd62ec4d, which equals PB bak59/bak60 | `embed_check.py` | No | MEASURED |
| RepairExecution before (native and hdalc) | `Staging/RepairExecution_2026-10-03/Before/Content__Project__Shared__ModelBank__HDA__GeoCity_city_v015_PermanentBank.uasset` (acc39bfe); `.../Before/GeoCity_city_v015_PermanentBank.hdalc` (2acabf3b) | HISTORICAL | The hdalc is a byte copy of `PB/revisions/r014`. The native embeds the same bytes. | `embed_check.py` | No | MEASURED |
| SurfacePainting HDAs (Content) | `Content/Project/Shared/SurfacePainting/HDA/GeoCity_city_v007_SurfacePainting_v002.uasset` (b7f84946), `..._v013_AllSurfacePalette.uasset` (d8255faf), `..._v014_AllSurfacePaletteFix.uasset` (95bbcf61), all 10-02 | HISTORICAL | Superseded by v015. v007_SP_v002 is referenced only by the legacy map `L_GazaRimal_SurfacePainting_20261002`. v014 is referenced only by the Developer map `L_GazaRimal_V13_ColorsModels_20261002`. No map references v013. | `grep -a` over all `.umap` < 200 MB (part 01); reverse check (part 04); Content-wide grep (part 03) | No (no LIVE map or profile) | MEASURED |
| SurfacePainting HDA backups | `Staging/ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/Before/Content/Project/Shared/SurfacePainting/HDA/*.uasset` (3) | HISTORICAL | Byte copies of the three Content copies, inside the RunExisting backup set. Part 05 says keep that set whole. | sha256 | No | MEASURED |
| Developer proof HDAs (10 assets, 09-27 to 10-02) | `Content/Developers/USER/HoudiniCityProof/`: `B1_probebox`, `B2_labs_osm`, `DirectPickerPilot/GeoCity_city_v002`, `HDA/GeoCity_city_v002/v006/v007`, `SingleModuleConnection/GeoCity_city_v008`, `V3DisabledCatalog/GeoCity_city_v003`, `V4UnifiedCatalog/GeoCity_city_v004`, `V9ModularPilot_20261002/HDA/GeoCity_city_v009_ModularPilot` | HISTORICAL | Proof and pilot HDAs | Referenced only by 18 Developer proof maps (`HoudiniCityProof/*.umap`, `ModelBankProof/L_BankCatalogConnection_2026_09_30.umap`) | No | MEASURED |
| Autosave HDA copies (5) | `Saved/Autosaves/Game/...`: `B1_probebox_Auto1`, `GeoCity_city_v008_Auto1`, `GeoCity_city_v004_Auto2`, `GeoCity_city_v009_ModularPilot_Auto1`, `GeoCity_city_v007_SurfacePainting_v002_Auto1` | HISTORICAL | Editor autosaves of historical HDAs. Their hashes differ from the originals. | sha256 | No | MEASURED |
| TrackA re-import copies | `Staging/TrackA_Tests/HoudiniCityProof/GeoCity_request_wiring_UI_2026-09-30/GeoCity_city_v002_before_{reimport,proxy_reimport}.uasset` | HISTORICAL | Pre-re-import copies from 09-30 | path | No | MEASURED |
| Connection-era hdalc | `Staging/ModelBank/Connection_2026-09-30/GeoCity_city_v002_before.hdalc` (bc3e59e8) | HISTORICAL | 09-30 connection evidence | path | No | MEASURED |
| Archived SideFX probe HDAs (13) | `Staging/Archive/PreFinalVision_2026-09-29/Research/.../SideFXSampleProbe/**` | HISTORICAL | Already archived | Archive path | No | MEASURED |
| Pegasus listing HDAs | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/S1_Prep/pegasus_listing/**` (4 `.hda` and `HDA_FileLoad.uasset`) | HISTORICAL | Third-party product listing used for ground research. The generator does not use it. | path; part 03 S1 tooling row | No | INFERRED |
| Houdini Engine plugin sample HDAs (15) | `Plugins/HoudiniEngine/Content/{Examples,NodeSync,Tools}/*.hda` (all 2026-09-01) | LIVE | Vendor payload of the LIVE official plugin. The generator does not use them. Do not touch. | mtimes match the plugin install | No (unused by the generator) | MEASURED; INFERRED |

#### 3.2.E Cook outputs with GeoCity names (not HDAs; listed for completeness)

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Area Cook outputs (229 packages, 1,921 MB) | `Content/Project/Areas/GazaRimal/BankIntegration_v015/Cook/GeoCity_city_v015_PermanentBank/B7CE31BC` (113, 664 MB, 10-03); `.../GazaShujaiya/BankIntegration_v015/Cook/.../311CD685` (88, 791 MB, 10-05 18:47Z); `.../Iran_38196167_46086167_4km/BankIntegration_v015/Cook/GeoCity_city_v015_4km/78F86F39` (28, 466 MB, today 13:38Z) | DEAD | Orphaned temporary cook output, regenerable and owned by the lifecycle. CONFLICT: part 01 = LIVE ("outputs of the three current maps"); part 04 = DEAD (0 referrers after Bake). DEAD chosen on part 04's measured scan (INFERRED). Remove only through the lifecycle. The Iran folder was written while PID 29900 held the map, so the disk view may lag. | part 04 reverse check: 0 referrers in Content/Project and Developers | No. The profiles name only the folder path as the HE temp-cook setting. | MEASURED; INFERRED (regenerable) |
| Autosave and backup cook copies | `Saved/Autosaves/Game/**/Cook/**`; `Staging/ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/Before/Content/**` | HISTORICAL | Autosaves and pre-run backups. 450 RunExisting packages are byte-identical to live Content (3.15). | parts 01, 05 | No | MEASURED |

Developer cook outputs (`Content/Developers/USER/HoudiniCityProof/Cook/**`, `.../LayerInfos`) are covered by the Developers row in 3.12. `Content/HoudiniEngine/{Temp,Bake}` is in 3.12.

#### 3.2.F Drift finding (1 km generator: three different "current" states; MEASURED unless marked)

Label: every cell in the next table is MEASURED (part 01: hashes and embed check). The "Source of the claim" column names the DOCUMENTED record.

| Role | Revision | hdalc sha256 | Native uasset sha256 | Source of the claim |
|---|---|---|---|---|
| Canonical by receipt | `r018_retained_appearance` | 61303c1559b82daa... | 357eeac6 (snapshot only) | `PB/definition_receipt.json` |
| Ratified B2 | folder `20261005_procedural_ten_families_v003` | 462f1d50ba25a6ce... | 2358c514baeba04e... | RATIFICATION_B2 and the v003 INTEGRATION_RECEIPT |
| Running now | folder `20261005_procedural_thirty_families_v004` | 886ab082ac98d1bd... | 3cf1f84020c9783f... | the v004 INTEGRATION_RECEIPT and the byte embed |

- **Native lineage (MEASURED from embedded bytes and receipts):** 357eeac6 (r018 root, 10-03 11:47Z) -> f407976c (v001, 10-05 15:29Z, Attempt1) -> 1de0e6fe (v002, 10-05 about 15:49Z, ATTEMPT2_START) -> 2358c514 (v003, 10-05 17:43:01Z, PID 10460) -> 3cf1f840 (v004, 10-06 07:33:34Z, PID 35156).
- **v004 has never been cooked into a saved area (DOCUMENTED).** Both v004 receipts say `"native_city_regeneration_performed": false` and `"city_regenerated": false`.
  - INFERRED: the Shujaiya map 4efebdfb (saved 10-05 18:54Z) was generated with v003.
  - INFERRED: the Rimal map a6961c8e (mtime 10-04 20:38Z) predates v001, so it was generated with r018.
  - The next Gaza regeneration will run v004.
- **The HDA is outside the seal (MEASURED).**
  - `geocity_runtime_manifest.json` pins only `init_unreal.py` and the 12 `Content/Python` modules, plus 4 support files. It holds no HDA hash.
  - `geocity_bank_workflow.py:1020` instantiates whatever `self.p['hda']` names.
  - This is how the native changed twice without breaking the seal.
- **The profiles are already coupled to v004 (MEASURED).**
  - `building_assembly_contract.source_family_registry_ref` points at the v004 registries: `ContractAudit/Registries/8d8622b2...` (Shujaiya) and `b3fe7421...` (Rimal).
  - A rollback to B2 must also restore the v003 registries a39dbbb9 / b2e1876b.
  - Backups of the pre-v004 profiles are in `PE/ModelBank/Modular_2026-10-04/ProceduralFamilies_Additional20/Integration/Before/`.
  - The Shujaiya profile changed again today at 13:10Z: 4174a627 differs from the v004 "after" hash 1bd89e5b, because of the hybrid profile patch (3.7).
  - The Rimal profile 492b9ac5 equals the v004 "after" hash.
  - Superseded in-window: these profile hashes are as of 13:50-14:25Z. At 14:32:58Z the profiles became Shujaiya f722381f, Rimal e6dead27, Iran cb0f3cab. The author did not re-check whether the registry refs changed (snapshot caveat 5).
- **Which area uses which generator (MEASURED from each profile's `"hda"` key and from the map imports; values as of 13:50-14:25Z):**
  - GazaShujaiya (profile 4174a627, now f722381f; map 4efebdfb) and GazaRimal (profile 492b9ac5, now e6dead27; map a6961c8e, now 1d670c8e) use `/Game/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank`.
  - Iran_38196167_46086167_4km (profile 004ec07d, now cb0f3cab; map c409279c) uses `/Game/Project/Shared/ModelBank/HDA/GeoCity_city_v015_4km`.
- **4 km generator: no drift (MEASURED).** Native 43ca7d0e embeds root c0cc6fdc, which is the hash recorded in `HDA_DEFINITION.json`. r019 and r020 were never promoted.
- **Module divergence (AST diff of top-level defs; MEASURED):**
  - **Live 1 km v004 (274 defs) vs live 4K (241 defs):**
    - 14 defs changed: `GRID_SAMPLES` (1009 vs 4033), `_rasterize`, `_sample_grid`, `_terrain_r015_coherent_pad_records`, `_permanent_spacing_ok`, `_nonbuilding_ground_ok`, `_roadside_near_road`, `_style_validate`, `_final_proxy_generated_identity`, `cook_bank_proxy_filter`, `cook_road_eligibility`, `cook_street_details`, `cook_vegetation`, `assembly_layout`.
    - 33 defs exist only in v004: the procedural/source-family code (`source_family_plan`, `procedural_bank_families`, `materialize_procedural_record`, the `_sf_*` helpers, the `SOURCE_*` gates).
    - The Iran generator therefore lacks all modular-family code.
  - **PB r018 root vs 4K root:** 13 defs changed. `cook_surface_palette` is identical in both.
  - **r019 vs 4K root:**
    - 8 defs changed: `cook_surface_palette`, `cook_city_terrain`, `cook_vegetation`, `cook_nonbuilding_requests`, `cook_nonbuilding_selector`, `load_package`, `_permanent_fit_setup`, `_permanent_candidate_rejection`.
    - 23 `semantic_*` / `_SEMANTIC_*` defs added.
  - **r020 vs r019:** 11 defs changed and 21 `_building_*` defs added.
  - **PB v003 vs v004:** only `assembly_layout` (which honours `allowed_building_uses`) and `materialize_procedural_record` (bulk prim attribute set) differ.

### 3.3 Sealed runtime modules and support files

#### 3.3.A Seal check result (MEASURED, part 02)

- **Seal identity.** The manifest has no seal-id field. The seal id is the file's own sha256: `Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json` = `258469e14df2ca2e5e2b0c6543bf42e29c1fcde3d1628f7d258a607ee6d03024`.
- **Binding record.** `RATIFICATION_B2.json:7-9` names the same path and sha256.
- **Schema.** `"schema": "environmentpipeline.geocity_runtime_sources.v2"`, `"loading": "exact project source; no stale-module reload; no startup generation"`.

Label: every cell in the next table is MEASURED (part 02, full 64-hex sha256 comparison).

| Pinned file | Manifest sha | Disk sha | Result |
|---|---|---|---|
| `Content/Python/init_unreal.py` (startup) | bd3ff65c | bd3ff65c | MATCH |
| `geocity_bank_workflow.py` | f349d128 | f349d128 | MATCH |
| `geocity_editor_action.py` | 1b13b051 | 1b13b051 | MATCH |
| `geocity_landscape_workflow.py` | d1a5d5fd | d1a5d5fd | MATCH |
| `geocity_roadbld_clip.py` | 479842e4 | 479842e4 | MATCH |
| `geocity_roadbld_grounding.py` | 0a0d813a | 0a0d813a | MATCH |
| `geocity_roadbld_junctions.py` | a2afdf91 | a2afdf91 | MATCH |
| `geocity_roadbld_landscape.py` | 4f48f02a | 4f48f02a | MATCH |
| `geocity_roadbld_props.py` | 2bf41ec3 | 2bf41ec3 | MATCH (B2 fix) |
| `geocity_roadbld_seams.py` | fbba14b4 | fbba14b4 | MATCH |
| `geocity_roadbld_topology.py` | 0b39c79e | 0b39c79e | MATCH |
| `geocity_roadbld_workflow.py` | 451bb0d4 | 451bb0d4 | MATCH |
| `geocity_runtime_guard.py` | 8f2efd14 | 8f2efd14 | MATCH |
| `Config/DefaultEngine.ini` | ba043fdc | ba043fdc | MATCH |
| `Config/DefaultRoadBLD.ini` | 70338496 | 70338496 | MATCH |
| `Staging/SystemCompletion_2026-10-04/launch_editor.ps1` | ba70eac4 | ba70eac4 | MATCH |
| `Staging/SystemCompletion_2026-10-04/seal_runtime.py` | e3b3c26f | e3b3c26f | MATCH |

**Verdict.** All 17 pins match, compared by full 64-hex hash. There is no drift. `launch_editor.ps1` and `seal_runtime.py` exist only under `Staging/SystemCompletion_2026-10-04/`.

**Older seals still pinned by non-LIVE files (MEASURED):**
- 3cd33b15: GroundPainting `STARTUP_REVIEWED_PINS.json`, `BANK_ACTIVATION.json`, `CONTINUATION_MANIFEST.json`, the MODULAR_* activations.
- 17a9105f: `GENERATION_ACTIVATION.json`, `OWNERSHIP_REPAIR_FRESH_ACTIVATION.json`.
- 06129276: `INSPECTION_ACTIVATION.json`.
- a3a7e5c0: HoudiniEngineOutputRepair `STARTUP.json`.

The only difference between 3cd33b15 and 258469e1 is props bf59bf96 -> 2bf41ec3 (DOCUMENTED, RATIFICATION_B2).

**Profiles are not sealed.**
- At the survey, the current profiles (Shujaiya 4174a627, Rimal 492b9ac5) differed from the B2-ratified ones (1328d5bb / e136df32). Callers of `launch_editor.ps1` must pass the current profile hash (MEASURED).
- Superseded in-window: since 14:32:58Z the profiles are Shujaiya f722381f, Rimal e6dead27 and Iran cb0f3cab. The bank operator rewrote them without any seal change, which confirms that profiles sit outside the seal (MEASURED by the reviewer; author listing).

#### 3.3.B Runtime files, copies and forks

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Runtime module: bank workflow | `Content/Python/geocity_bank_workflow.py` (71,606 B, 10-04 16:56 local, f349d128) | LIVE | Sealed. `:650` asserts landscape material = profile; `:505-507` hash-checks the profile's `decision_receipt`; `:1020` instantiates the profile's `hda`. | sha = manifest; author read `:646-652`, `:1020` | Sealed; imported by the guard | MEASURED |
| Runtime module: editor action | `Content/Python/geocity_editor_action.py` (17,428 B, 1b13b051) | LIVE | Sealed. Reads ASSIGNMENTS/BANK_ACTIVATION (`:26`, `:30`) and the lease (`:218`). When not managed, it self-issues an `OWNER=GEOCITY_MENU` lease (`:243-246`). | sha = manifest; author read `:243-246` | Sealed; menu entry | MEASURED |
| Runtime module: landscape workflow | `Content/Python/geocity_landscape_workflow.py` (32,775 B, d1a5d5fd) | LIVE | Sealed. Hard-codes the Natural master and base MI (`:14-17`) | sha = manifest | Sealed | MEASURED |
| Runtime module: road clip | `Content/Python/geocity_roadbld_clip.py` (35,507 B, 479842e4) | LIVE | Sealed. Hard-codes and asserts `Staging/AppearanceRepair_2026-10-03` as the road-clip receipt destination (`:266-271`) | sha = manifest | Sealed | MEASURED |
| Runtime module: road grounding | `Content/Python/geocity_roadbld_grounding.py` (88,834 B, 0a0d813a) | LIVE | Sealed. Writes continuity receipts into `AppearanceRepair_2026-10-03` (`:1309`) | sha = manifest | Sealed | MEASURED |
| Runtime module: road junctions | `Content/Python/geocity_roadbld_junctions.py` (58,935 B, a2afdf91) | LIVE | Sealed. Asserts a 2026-10-03 line in `Saved/Logs/Environmentpipeline.log` (`:580-582`) on the legacy-adoption path | sha = manifest; author read `:576-584` | Sealed | MEASURED |
| Runtime module: road landscape | `Content/Python/geocity_roadbld_landscape.py` (6,466 B, 4f48f02a) | LIVE | Sealed | sha = manifest | Sealed | MEASURED |
| Runtime module: road props | `Content/Python/geocity_roadbld_props.py` (10,363 B, 10-05 18:47 local, 2bf41ec3) | LIVE | Sealed. The B2 fix, ratified in `RATIFICATION_B2.json` | sha = manifest | Sealed | MEASURED |
| Runtime module: road seams | `Content/Python/geocity_roadbld_seams.py` (45,703 B, fbba14b4) | LIVE | Sealed | sha = manifest | Sealed | MEASURED |
| Runtime module: road topology | `Content/Python/geocity_roadbld_topology.py` (13,439 B, 0b39c79e) | LIVE | Sealed | sha = manifest | Sealed | MEASURED |
| Runtime module: road workflow | `Content/Python/geocity_roadbld_workflow.py` (101,309 B, 451bb0d4) | LIVE | Sealed. Reads the lease (`:544`) | sha = manifest | Sealed | MEASURED |
| Runtime guard | `Content/Python/geocity_runtime_guard.py` (8,584 B, 8f2efd14) | LIVE | Sealed. `verify()` re-hashes the manifest and its 4 support files before every Generate (`:123-182`) | sha = manifest | Sealed | MEASURED |
| Startup entry point | `Content/Python/init_unreal.py` (2,095 B, bd3ff65c) | LIVE | Sealed entry point. Reads the manifest (`:13`) and executes the guard from source (`:28`) | sha = manifest `startup` | Sealed | MEASURED |
| Python bytecode (16 files) | `Content/Python/__pycache__/*.pyc` (cpython-310/311, newest 10-04 11:59 local) | DEAD | Stale build artefacts, older than most sources; the props pyc is absent. The guard installs a source finder/loader. Not an Unreal package. | `init_unreal.py:28` (`exec(compile(...))`); part 04 `find` = 16 | No | MEASURED (dates); INFERRED (not loaded) |
| Seal manifest | `Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json` (2,845 B, 10-05 18:47 local, 258469e1) | LIVE | The B2 seal. No HDA hash inside. | file sha256 = 258469e1 | Read by `init_unreal.py:13`, guard `:123`/`:158`, `launch_editor.ps1:40` | MEASURED |
| Seal tool | `Staging/SystemCompletion_2026-10-04/seal_runtime.py` (2,477 B, e3b3c26f) | LIVE | Sealed support file. Writes the manifest. | sha = manifest support_files | Re-hashed by the guard | MEASURED |
| Startup receipts | `Staging/SystemCompletion_2026-10-04/RUNTIME_STARTUP.json`, `LAUNCH_STATE.json` | LIVE | Written by `guard.bootstrap` (`:179-185`) and `launch_editor.ps1` (`:97-98`). `LAUNCH_STATE.json` looks stale: same size and mtime as `LAUNCH_STATE_PID23068.json` while the editor is PID 29900 (not opened). | `ls -l` | Written by sealed code | MEASURED; INFERRED |
| Per-PID receipts | `Staging/SystemCompletion_2026-10-04/RUNTIME_STARTUP_PID*.json` (34), `LAUNCH_STATE_PID*.json` (11) | HISTORICAL | One per launch. `RUNTIME_STARTUP_PID29900.json` exists; there is **no** `LAUNCH_STATE_PID29900.json`, because the Iran launch did not use `launch_editor.ps1`. After the window, two more appeared: `RUNTIME_STARTUP_PID28148.json` (14:53:30Z) and `RUNTIME_STARTUP_PID5288.json` (15:21:23Z), so there are now 36. PID 5288 was running at about 15:25Z. | `ls`; author listing and `tasklist` | No | MEASURED |
| Prepared copies equal to LIVE | `Staging/SystemCompletion_2026-10-04/Prepared/geocity_roadbld_clip.py`, `.../geocity_roadbld_grounding.py` | DUPLICATE | Byte copies of LIVE clip (479842e4) and grounding (0a0d813a) | sha equal | No | MEASURED |
| Prepared older versions | `Staging/SystemCompletion_2026-10-04/Prepared/geocity_roadbld_props.py` (bf59bf96), `.../geocity_roadbld_workflow.py` (4e85299c) | HISTORICAL | Older versions (pre-B2 props; pre-seal workflow) | sha differs from live | No | MEASURED |
| Attempt2 props copy | `Staging/ModularConstruction_2026-10-05/Run_20261005/Attempt2/geocity_roadbld_props.py` | DUPLICATE | Byte copy of LIVE props 2bf41ec3 (origin of the B2 fix) | sha equal | No | MEASURED |
| Attempt1 props copy | `Staging/ModularConstruction_2026-10-05/Run_20261005/Attempt1/geocity_roadbld_props.py` (bf59bf96) | HISTORICAL | Pre-B2 props | sha | No | MEASURED |
| Unpromoted bank workflow fork | `Staging/ManagedSystemsAstra_2026-10-04/Task1_Lifecycle/IranSemanticConsumer/geocity_bank_workflow.py` (bf0ddff1, 86,320 B) and helpers/`build_candidate.py` | DUPLICATE | Parallel version of the LIVE bank workflow (71,606 B). Not promoted. | `RESULT.json` status `STAGED_FROZEN_READY_FOR_COMBINED_REVIEW_NATIVE_NOT_RUN` | No | MEASURED |
| Unpromoted landscape workflow fork | `Staging/ManagedSystemsAstra_2026-10-04/Task3_GroundGrass/IranSemanticConsumer/geocity_landscape_workflow.py` (b13c555a, 78,670 B) and `semantic_consumer_extension.py` (re-implements `prepare`/`verify_landscape`/`inspect_near_view`) | DUPLICATE | Parallel version of the LIVE landscape workflow (32,775 B) | `RESULT.json` `STAGING_ONLY_..._NATIVE_NOT_RUN`; `PROFILE_PATCH_PROPOSAL.json` `PROPOSED_NOT_APPLIED` | No | MEASURED |
| Old reviewed copies | `Staging/HoudiniEngineOutputRepair_2026-10-04/geocity_bank_workflow.reviewed.py` (a3ac3a86), `prepare_repair.py` (re-implements `configure_engine_outputs`/`configure_and_bind`); `Staging/ManagedExecution_2026-10-02/Task4/BEFORE_geocity_editor_action.py` | HISTORICAL | Pre-seal versions of runtime functions | grep of runtime def names | No | MEASURED |
| Runtime backup copies | 54 runtime-module copies under `Staging/**/Before*/` (e.g. `ManagedSystemsAstra_2026-10-04/Before/Content/Python` x13, `ManagedAstra_2026-10-03/BeforeReplacementV3_20261004` x4); 70 Staging copies in total, 16 outside `Before*` | HISTORICAL | Pre-change backups | `find` | No | MEASURED |
| Pre-runtime bake/build route | `Staging/ModelBank/PermanentIntegration_2026-10-02/{bake_environment,build_environment,run_integrated_workflow,refresh_bank_input,verify_native_recook,...}.py` (10-02) | HISTORICAL | Earlier bake/build/regeneration route, replaced by `geocity_bank_workflow.run()` | hits on `after_bake`, `bake_all_outputs*` | No, but they sit inside the LIVE Rimal profile folder (`AREA_PROFILE.json` 492b9ac5) | MEASURED |
| Pre-runtime bake routes | `Staging/PaintBank_2026-10-02/bake_surface_area.py`; `Staging/V13ConnectedPreview_2026-10-02/{bake_save_map,build_map}.py`; `Staging/RestartReview_2026-10-01/SingleModuleConnection_2026-10-01/*` | HISTORICAL | Superseded proof and bake scripts | grep | No | MEASURED |
| Pre-runtime road route | `Staging/AppearanceRepair_2026-10-03/{start_native_road_delivery,resume_*,finish_bound_native_ground,...}.py`; `Staging/ManagedAstra_2026-10-03/{fresh_delivery_21780,continue_*_21780,...}.py` | HISTORICAL | Earlier RoadBLD delivery drivers (PID 21780 era) | grep `DynamicRoadNetwork/RoadBLD` | The scripts: no. The `AppearanceRepair_2026-10-03` folder is written by LIVE code. | MEASURED |
| Profile-referenced patch script | `Staging/RepairExecution_2026-10-03/BUILDING_ASSEMBLY_PATCH.py` (10-03, 30,341 B) | LIVE | Named as `implementation_file` in all three profiles. No reader in `Content/Python` or in the 1 km HDA module (grep), so the reference is provenance only. | profile key `implementation_file` | Yes (profiles) | MEASURED; INFERRED (provenance only) |

The Path B patched copy of `geocity_landscape_workflow.py` is a ground-route item, in 3.9.

### 3.4 Editor launchers (all of them)

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Sealed launcher | `Staging/SystemCompletion_2026-10-04/launch_editor.ps1` (10,483 B, 10-04 16:49 local, ba70eac4) | LIVE | The only launcher on disk that is valid for the current seal. **Gaza only**: ValidateSet at line 3 and a `native_area_maps` check at line 34. A sealed support file, so any change needs a reseal. | sha = manifest support_files; it wrote lease lines 457/465/471/479 (PIDs 23156, 16824, 34928, 23068) | `ASSIGNMENT.json` scope; `PLAN_PROPOSAL.md` step 5; `PLAN_HYBRID.md`; re-hashed by the guard | MEASURED |
| Iran launch record (no launcher file) | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/IranRun_20261006/LAUNCH_PID29900.json` | LIVE | Records how the running editor PID 29900 was started: "manager_direct" with the sealed launcher's arguments. **No LIVE Iran launcher exists.** | lease line 485 `launcher=manager_direct_same_args_as_sealed_launcher`; no `LAUNCH_STATE_PID29900.json` | `RESULT_IRAN_20261006.json` | MEASURED |
| Old Iran launcher | `Staging/HoudiniEngineOutputRepair_2026-10-04/launch_current_area.ps1` (4,528 B, 10-04 13:27 local, 3a2ee381) | DEAD | Parallel Iran route of `launch_editor.ps1`. Its gate (line 9) requires a last lease `OWNER=CODEX_ENGINE_OUTPUT_REPAIR ... assigned_editor_PID=NONE`, which is absent. It embeds the retired thread `01a10654-12e1-7c20-b7fa-2016e655abcd` (line 40). No manager id and no profile/support-file check. | Last use in `STARTUP.json`: PID 17872, manifest a3a7e5c0 (pre-v2 seal), 10-04 11:19Z | No (only PROJECT_STATUS §3 item 4 mentions it) | MEASURED |
| Iran new-area launcher | `Staging/Iran_4km_2026-10-04/launch.ps1` (2,090 B, 10-04 11:58 local, 491047d1) | DEAD | One-shot new-area creator. Opens `/Engine/Maps/Entry`, prepends `Bootstrap/` to UE_PYTHONPATH, sets `GEOCITY_NEW_AREA_TOKEN` and self-issues an `OWNER=CODEX_NEW_AREA` lease (line 18). No seal check. **Hazard (INFERRED):** it checks only OWNER=NONE and no running editor, so it would still start an editor and append a held lease before its bootstrap fails. | `Bootstrap/new_area_bootstrap.py:34` `assert not does_asset_exist(p['map'])` (the Iran map exists, c409279c) and `:60` (the HDA exists) | No | MEASURED (code); INFERRED (hazard) |
| Iran bootstrap | `Staging/Iran_4km_2026-10-04/Bootstrap/init_unreal.py` (c92034eb), `new_area_bootstrap.py` | DEAD | Alternate startup entry; fails for the reason in the row above | `new_area_bootstrap.py:34`, `:60` | No. The Iran profile's `workflow_receipt` points into the `Iran_4km` folder, so that folder's ledgers are LIVE, not these scripts. | MEASURED |
| Ground launcher | `Staging/GroundPainting_2026-10-04/launch_ground.py` (4,490 B, 10-04 23:16 local, e628244a) | DEAD | Gaza-only ground launcher (thread 01a10883). Its own pins differ from the current 258469e1 / 2bf41ec3: `STARTUP_REVIEWED_PINS.json` pins manifest **3cd33b15** (`:2`) and props **bf59bf96** (`:12`), and `launch_ground.py:24` asserts the manifest pin. The map/profile hashes in `LAUNCH_BASELINES.json` (17d5929a / 00877b7c) are stale. | `STARTUP_REVIEWED_PINS.json:2,12`; `launch_ground.py:24` (author read) | No | MEASURED |
| Modular launcher | `Staging/BankIntegration_2026-10-04/ModularNative_2026-10-05/launch_modular_editor.ps1` (7,788 B, 10-05 16:11 local, caa531b0) | DEAD | Hard-codes the relieved manager `01a10789...` (line 11). Needs an activation with `status=MODULAR_STARTUP_AUTHORIZED`. | Every `MODULAR_*_ACTIVATION*.json` says `USER_STOPPED_ALL_AUTHORING_REPORT_ONLY`, `startup_authorized=false`, manifest 3cd33b15 | No | MEASURED |
| Modular launcher copies | `.../ModularNative_2026-10-05/Handoffs/8a253d5b.../launch_modular_editor.ps1`, `.../Handoffs/e71bd768.../launch_modular_editor.ps1` | HISTORICAL | Byte copies (caa531b0) of the DEAD launcher, kept as evidence | sha256 equal | No | MEASURED |
| Replacement launcher | `Staging/ManagedAstra_2026-10-03/launch_replacement_editor_PREPARED.ps1` (4,735 B, 10-03 23:25 local, 17dce6ea) and `RecoveryBootstrap/init_unreal.py` (934ea946) | DEAD | Hard-coded map sha fe56a24d (line 21), which is not the current Shujaiya map 4efebdfb. It uses `RecoveryBootstrap`, which `launch_editor.ps1:88-89` explicitly excludes. | lines 10-21 | No | MEASURED |
| Continuation launcher | `Staging/ManagedSystemsAstra_2026-10-04/Task4_Integration/Continuation/launch_reviewed.ps1` (2,037 B, 10-04 18:48 local, 6c1cec06) | DEAD | Wrapper around `launch_editor.ps1`. It reads `STARTUP_ACTIVATION.json` (line 4), which does not exist. `CONTINUATION_MANIFEST.json` binds manager 01a10789, operator 01a106e8 and seal 3cd33b15. | `PLAN_PROPOSAL.md:59`: it "cannot pass after a ground release" | No | MEASURED; DOCUMENTED |
| Launcher backups | `Staging/ManagedSystemsAstra_2026-10-04/Before/Staging/SystemCompletion_2026-10-04/launch_editor.ps1` and `.../Task1_Lifecycle/Before/launch_editor.ps1` (both 406e99fc); `.../Task1_Lifecycle/BankAuthority_Repair/Before/launch_editor.ps1` (dfec5863) | HISTORICAL | Pre-repair copies of the LIVE launcher | sha differs from ba70eac4 | No | MEASURED |
| Plugin installer (not a launcher) | `Staging/TrackA_Tests/HoudiniCityProof/02_install/install_and_verify.ps1` (09-27) | HISTORICAL | Only checks that UnrealEditor is not running | line 12 | No | MEASURED |

**Launcher verdict (MEASURED, part 02).**
- One launcher works under the current seal: `launch_editor.ps1`, Gaza only.
- Six distinct launchers are DEAD. Each fails its own gate: a stale seal, a relieved manager id, a missing activation file, a stale map hash, or an existing-map assert.
- Five copies are HISTORICAL: two modular handoff copies and three `Before/` backups of `launch_editor.ps1`.
- The Iran editor was started without a launcher file.

### 3.5 Lease and activation files

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Lease log | `Staging/ModelBank/EDITOR_OWNER.txt` (493 lines at about 14:00Z; 131,518 B at 14:48:43Z) | LIVE | The single legacy lease log. Since 14:14:05Z the last line is `OWNER=ASSET_BANK_OPERATOR` on PID 29900. Under `AGENTS.md:9` the parallel Sky task keeps its record elsewhere. Content after 14:00Z was not read. | parts 02, 03, 04; author listing | `geocity_editor_action.py:218`; `geocity_bank_workflow.py:119`, `:144`, `:265`; `geocity_roadbld_workflow.py:544`; all launchers | MEASURED |
| Managed assignments | `Staging/ManagedSystemsAstra_2026-10-04/ASSIGNMENTS.json` (10-05 23:47 local) | LIVE | `manager_thread_id` = **cc37d4d2** and task4 `thread_id` = cc37d4d2 (applied 2026-10-05T20:02:49Z / 20:47:19Z). `native_area_maps` lists the 2 Gaza maps only. Stale fields: `editor.current_actual_pid` 32508, `editor_activation` "...PID32508", `shared_files.area_profiles_owner` 01a10789, `created_chats` task4 = 01a106e8-f85a..., `management_succession.successor_manager_thread_id` 01a10789 (`:201`). Re-read on every Generate, so do not edit it while an editor is live. | grep of fields | `geocity_editor_action.py:26`, `:51`, `:56`; `launch_editor.ps1:13-15`, `:34` | MEASURED |
| Bank activation | `Staging/ManagedSystemsAstra_2026-10-04/BANK_ACTIVATION.json` (10-04 21:20 local) | DEAD | As an authority, it is blocked by its own fields: `manager_thread_id` 01a10789 (not cc37d4d2), `native_authorized_now=false`, `ordinary_generation_authorized=false`, `startup_authorized=false`, PID 30328, manifest 3cd33b15. The bank route is always refused. | `geocity_editor_action.py:40` and `launch_editor.ps1:26` require its id to equal ASSIGNMENTS | **Yes, still read**: `geocity_editor_action.py:30`, `launch_editor.ps1:20-25`. Moving it would make those branches throw instead of refuse. | MEASURED |
| Bank scope assignment | `Staging/BankIntegration_2026-10-04/ASSIGNMENT.json` (10-04 18:32 local) | DEAD | As an authority: `system_owner` 01a10789 is not the current manager. The folder itself is LIVE (3.14). | `geocity_editor_action.py:28-40`; `launch_editor.ps1:19-26` | **Yes, still read** by sealed code (bank branch) | MEASURED |
| Generation activation | `Staging/ManagedSystemsAstra_2026-10-04/GENERATION_ACTIVATION.json` (10-04 16:28 local) | DEAD | Manager 01a106bc, operator 01a106e8-f85a, PID 33168 (not running), seal 17a9105f | No reader in `Content/Python` (grep); PROJECT_STATUS §3 item 5 and `PLAN_PROPOSAL.md:14` call it dead | No | MEASURED; DOCUMENTED |
| Status file | `Staging/ManagedSystemsAstra_2026-10-04/STATUS.txt` (10-04 21:28 local) | HISTORICAL | Names 01a10789 as sole manager and PIDs 30328/32508. Superseded by `AGENTS.md:12` and PROJECT_STATUS. | text: "USER STOP - ALL ENGINEERING STOPPED" | No reader (grep) | MEASURED |
| Succession records | `Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/` (`STATE.json`, `RECEIPT.json`, `STATUS_REPORT.txt`, `SUCCESSOR_REVIEW.json`, 2 x `BANK_ACTIVATION_BEFORE_*.json`, `complete_succession.py`, `Before/`) | HISTORICAL | Transfer from 01a106bc to 01a10789, PID 32508 | ids extracted by grep (`STATE.json` not opened by the author) | No reader | MEASURED |
| Modular activations | `.../MODULAR_STARTUP_ACTIVATION(_v002)_2026-10-05.json`, `MODULAR_NATIVE_ACTIVATION(_v002)...`, `MODULAR_HDA_COMPILE_ACTIVATION...` | DEAD | Status USER_STOPPED; manager 01a10789; PIDs 24804/21608; seal 3cd33b15 | grep | Only by the DEAD modular launcher | MEASURED |
| Other activation and stop records | `.../INSPECTION_ACTIVATION.json` (PID 27188), `OWNERSHIP_REPAIR_FRESH_ACTIVATION.json`, 4 x `DirtyOriginals_*_ACTIVATION.json` (PID 32508), `WHOLE_H0017_RECOVERY_ACTIVATION.json` (PID 30328), `LANDSCAPE_DIAGNOSTIC_*`, `USER_STOP_2026-10-05.json`, `MODULAR_DEADLINE_STOP...`, `BANK_PROFILE_MERGE_*.json`, `apply_reviewed_bank_profile_patch.py`, `HistoryBeforeUserStop/`, `ProfileMergeBefore/` | HISTORICAL | Managers 01a106bc/01a10789; all PIDs historical (27188, 30328, 32508, 33168, 5368, 24804, 21608; none running) | grep | No reader | MEASURED |
| Continuation manifest | `Staging/ManagedSystemsAstra_2026-10-04/Task4_Integration/Continuation/CONTINUATION_MANIFEST.json` | DEAD | Binds manager 01a10789, operator 01a106e8 and seal 3cd33b15. It is used only by the DEAD `launch_reviewed.ps1`. | part 02 launcher rows | No | MEASURED |
| Ground launcher pins | `Staging/GroundPainting_2026-10-04/STARTUP_REVIEWED_PINS.json`, `LAUNCH_BASELINES.json` | DEAD | Pin seal 3cd33b15, props bf59bf96, and stale map/profile hashes 17d5929a / 00877b7c | `STARTUP_REVIEWED_PINS.json:2` (manifest 3cd33b15), `:12` (props bf59bf96); assert at `launch_ground.py:24` | No (only the DEAD `launch_ground.py`) | MEASURED |
| Engine-output repair startup record | `Staging/HoudiniEngineOutputRepair_2026-10-04/STARTUP.json` | HISTORICAL | PID 17872, manifest a3a7e5c0 (pre-v2 seal), 10-04 11:19Z | part 02 | No | MEASURED |
| Bank operator activation | `Staging/AssetBankOperator_2026-10-06/DIRECT_USER_ACTIVATION_29900.json` | LIVE | Record behind the current `OWNER=ASSET_BANK_OPERATOR` lease on PID 29900. Not opened by the author. | part 04 snapshot caveat | The current lease line | DOCUMENTED |
| Reusable Sky ownership record | `Staging/ReusableSky_2026-10-06/` (assignment and plan) | LIVE | Parallel editor task authorized by Aviv (`AGENTS.md:7-9`). Its ownership record must stay here, not in `EDITOR_OWNER.txt` (`AGENTS.md:9`). | part 05; author read `AGENTS.md:7-9` | `AGENTS.md:7-9` | MEASURED; DOCUMENTED |

**Lease verdict (MEASURED, part 02, unless marked).**
- **`ASSIGNMENTS.json` already names cc37d4d2,** as the `AGENTS.md:12` technical note says. That note's claim that `GENERATION_ACTIVATION.json` manager_thread_id is "also validated by the sealed launcher and by geocity_editor_action" is unsupported: grep finds no reader in `Content/Python` or `launch_editor.ps1` (MEASURED, author grep).
- **The managed path cannot serve Iran.**
  - `native_area_maps` lists only the Gaza maps (`geocity_editor_action.py:56`). The 13:19:20Z MANAGER_ACTIVATED line for Iran (line 487) was therefore unusable.
  - The manager released to OWNER=NONE (line 489). The menu then self-issued `OWNER=GEOCITY_MENU` (line 491; `geocity_editor_action.py:243-246`).
  - `PLAN_PROPOSAL.md:119` says never to run the menu under OWNER=NONE, so the run went against the project's own plan. A manager note was recorded.
- **Free lease with a live editor.** From 13:39Z to 14:14Z the last lease was OWNER=NONE while PID 29900 was open. During that window, any menu click or rerun of `Operator/iran_generate.py` would have self-issued a GEOCITY_MENU lease and regenerated the map (INFERRED). The 14:14:05Z bank lease superseded this state.
- **The bank route is always refused.** `BANK_ACTIVATION.json` and `BankIntegration_2026-10-04/ASSIGNMENT.json` both carry 01a10789, and sealed code still reads both.
- **Records with no reader.** `GENERATION_ACTIVATION.json`, `STATUS.txt`, `ManagementTransfer/*` and the other activation records have no runtime reader.

### 3.6 Operator tooling and pins

The Hybrid, Path B and S1 scripts are classified in 3.9.

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| MCP client | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/copilot_client.py` (2,147 B, 10-05 23:01 local, 0323d614) | LIVE | **Unpinned**, although it executes every operator script (UnrealCopilot 127.0.0.1:19840 `run_unreal_skill`) | Not in any `SCRIPT_PINS.json` | `PLAN_HYBRID.md` "Critical files"; `hybrid_*.py` headers | MEASURED |
| Operator pin file | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/SCRIPT_PINS.json` (10-06 16:44 local) | LIVE | Pins 5 `pathb_*`, 5 `hybrid_*`, `iran_probe_scene` and `iran_probe_density`. All 12 MATCH. | sha check | Used by the operator | MEASURED |
| State probe | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/probe_state.py` (afd31450) | LIVE | Generic read-only state probe with no PID assert. Unpinned. | text | PROJECT_STATUS §2 "Operator tooling" | MEASURED |
| Exit helpers (6) | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/exit_no_save.py` (PID 10460), `exit_no_save_16824.py`, `_16824b.py`, `_23068.py`, `_23156.py`, `_35156.py` | HISTORICAL | Near-identical per-PID copies; they differ only in PID and reason text. Each asserts its own PID and has an `EXIT_PID*.json` receipt. | `assert os.getpid()==...` at line 5 | No | MEASURED |
| Iran dispatcher | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/iran_generate.py` (96bd67af) | HISTORICAL | One-shot dispatcher of `generate_current_area()` that asserts PID 29900. **Hazard (INFERRED):** PID 29900 is still alive, so this unpinned script could re-dispatch a generation. | text | No | MEASURED; INFERRED |
| Iran probes | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/iran_probe_scene.py`, `iran_probe_density.py` | LIVE | Pinned, read-only, no PID assert | SCRIPT_PINS MATCH | `RESULT_IRAN_20261006.json` | MEASURED |
| Iran capture | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/IranRun_20261006/capture_mcp.py` (c7cfed2f) | LIVE | Unpinned. Uses unreal-mcp 127.0.0.1:8000 `CaptureViewport`. | `CAPTURE_RECEIPT_r002.json` | `RESULT_IRAN_20261006.json` | MEASURED |
| Iran run record | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/IranRun_20261006/` (`RESULT_IRAN_20261006.json`, `Capture/` with 4 Lit captures, receipts) | LIVE | Record of today's ordinary Iran regeneration (PASSED 13:39:07Z; map 623aa0c0 -> c409279c). The fresh reopen is still pending. | PROJECT_STATUS §6 | `MANAGER_HANDOFF_2026-10-06.md` | DOCUMENTED |
| MW preview scripts | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/preview_mw_assign.py`, `preview_mw_revert.py` | HISTORICAL | Assert PID 16824. Unsaved preview, reverted. | `PREVIEW_ASSIGN/REVERT.json` | No | MEASURED |
| MW probes | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/probe_mma_t3d.py`, `probe_mma_wiring.py`, `probe_mma_wiring2.py` | HISTORICAL | Unpinned one-off diagnostics (10-06 13:14Z, hybrid session PID 23068) | mtime | No | MEASURED |
| Offline ledger summary | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Tools/offline_ledger_summary.py` (b1d8803e) | LIVE | Read-only offline summary with no `unreal` import. Note: running it during a live run would read ledgers, which the never-read-live-ledgers lesson forbids. | `ASSIGNMENT.json` `preparation_in_progress` names `Tools/` | `ASSIGNMENT.json` | DOCUMENTED |
| Parallel MCP client (ground) | `Staging/GroundPainting_2026-10-04/copilot_call.py` (10-04 23:11 local) | DUPLICATE | Parallel client: same endpoint and tool as LIVE `copilot_client.py` (19840 `run_unreal_skill`) | line 4, `:26` | Cited as a reference only by the HISTORICAL `S1v2/run_s1v2a.py:32` and `S1_Prep/run_s1.py:5` | MEASURED |
| Parallel MCP client (Iran) | `Staging/Iran_4km_2026-10-04/copilot_call.py` | DUPLICATE | Same as the row above | `find` | No | MEASURED |

### 3.7 Area profiles

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| GazaShujaiya profile | `Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json` (4174a627 as of 14:25Z; superseded in-window: f722381f at 14:32:58Z) | LIVE | Values below are as of 13:50-14:25Z. The 4174a627 file now survives only as `AssetBankOperator_2026-10-06/Before/AREA_PROFILE_GazaShujaiya.json`. **Blocked.** `:13` `landscape_material` = `.../MI_GeoCityGround_Auto` (absent). `:78173` `parent_chain` = `/Game/Project/Shared/SurfacePainting/Auto_20261006/M_GeoCityAuto` (absent). `landscape_grass.enabled` false (`:78087`). `:78171` decision "Aviv 2026-10-06 Hybrid ... Path B MI_GeoCityGround_MW was never saved and is superseded". Registry ref 8d8622b2 (v004). `roadbld_workflow.enabled=false` since the 10-05 incident. Changed 13:10:01Z by `hybrid_profile_patch.py` (1bd89e5b -> 4174a627). | parts 01, 03; `geocity_bank_workflow.py:650` | Is a root; `hda` = PermanentBank | MEASURED |
| GazaRimal profile | `Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json` (492b9ac5 as of 14:25Z; superseded in-window: e6dead27 at 14:32:58Z) | LIVE | Values below are as of 13:50-14:25Z. The old file is in `AssetBankOperator_2026-10-06/Before/AREA_PROFILE_GazaRimal.json`. Route A Natural: `:13` -> Rimal `MI_GeoCityGround`. Grass on (`:83598`, coverage 0.15). Registry ref b3fe7421 (v004). Equals the v004 "after" hash. The folder also holds HISTORICAL 10-02 scripts (3.3). | parts 01, 03 | Is a root | MEASURED |
| Iran profile | `Staging/ModelBank/Iran_38196167_46086167_4km/AREA_PROFILE.json` (004ec07d as of 14:25Z; superseded in-window: cb0f3cab at 14:32:58Z) | LIVE | Values below are as of 13:50-14:25Z. The old file is in `AssetBankOperator_2026-10-06/Before/AREA_PROFILE_Iran.json`. `:13` -> base `MI_SurfaceBank_Natural` directly. No `landscape_grass` block, so grass is off (`geocity_landscape_workflow.py:214-216`). `hda` = 4km. `source` -> PE Iran acquisition package. | part 03; part 05 (c) | Is a root | MEASURED |
| Hybrid rollback profile and record | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/Hybrid_Auto/Before/AREA_PROFILE_1bd89e5b_20261006T131001Z.json` (2.3 MB), `PROFILE_PATCH_RECORD_20261006T131001Z.json` | LIVE | Rollback point of `hybrid_profile_patch.py --rollback`. **Not clean:** it points at the absent Path B MI `MI_GeoCityGround_MW`. The patch's output state 4174a627 is no longer the live profile (f722381f since 14:32:58Z), so the rollback chain now starts from a superseded base (INFERRED). | `Hybrid_Auto/README.md:273` | Yes (Hybrid rollback chain) | MEASURED; DOCUMENTED |
| Pre-Path B profile backup | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/PathB_MW/Before/AREA_PROFILE_1328d5bb_20261006T002131Z.json` | LIVE | Rollback point (`pathb_profile_patch.py --rollback`). **Not clean:** it restores the Natural child, but it also sets `landscape_grass.enabled` true and reverts the registry ref from 8d8622b2 to a39dbbb9. 1328d5bb is also the B2-ratified Shujaiya profile hash. | `Hybrid_Auto/README.md:276`; part 03 (b) | Yes (documented rollback) | MEASURED; DOCUMENTED |
| Survey-time profiles (pre-14:32:58Z) | `Staging/AssetBankOperator_2026-10-06/Before/AREA_PROFILE_GazaShujaiya.json`, `AREA_PROFILE_GazaRimal.json`, `AREA_PROFILE_Iran.json` (14:32:09Z) | LIVE | The only remaining copies of profiles 4174a627 / 492b9ac5 / 004ec07d, the base of every rollback analysed in this document (3.7, section 4 item 6). Made by the bank operator before its in-window rewrite. | reviewer; author listing (sizes 2,330,307 / 3,371,685 / 44,629 B) | Yes (rollback base; bank operator's own backup) | MEASURED |
| Pre-v004 profile backups | `PE/ModelBank/Modular_2026-10-04/ProceduralFamilies_Additional20/Integration/Before/` (profile files next to the 2358c514 native) | LIVE | B2 rollback partners for the native (v003 registry refs) | part 01 (b) | Yes (B2 rollback path) | MEASURED |
| Bound registries (v004) | `Staging/ModularConstruction_2026-10-05/ContractAudit/Registries/8d8622b2....json` (Shujaiya), `b3fe7421....json` (Rimal), plus the 116 JSON files they reference (ASSEMBLY / SOURCE / NATIVE_FAMILY / ROUTE_AUTHORIZATION / SOURCE_QUALIFICATION / EXTENSION / SOURCE_BINDINGS and 3 parent registries) | LIVE | `building_assembly_contract.source_family_registry_ref` in both Gaza profiles. Through this chain, 948 packages are bound. The runtime does not read the ref itself (INFERRED: it is an HDA input or provenance). | parts 01, 04, 05 | Yes (profiles) | MEASURED |
| v003 registries | `Staging/ModularConstruction_2026-10-05/ContractAudit/Registries/a39dbbb9...`, `b2e1876b...` | HISTORICAL | Superseded by the v004 registries. **Needed for a B2 rollback; keep.** | part 01 (b) | Only through the rollback backups | MEASURED |
| Live catalog receipts | `Staging/ModelBank/<area>/HDA_CATALOG_RECEIPT.json` (unsuffixed, Gaza); `Staging/Iran_4km_2026-10-04/CATALOG_RECEIPT.json` (written 13:38Z today) | LIVE | Profile `catalog_receipt` | part 05 (b) | Yes (profiles) | MEASURED |
| Timestamped catalog receipt history | `Staging/ModelBank/<area>/HDA_CATALOG_RECEIPT_<ns>.json` (about 2.8 GB Shujaiya, 0.7 GB Rimal); `Staging/Iran_4km_2026-10-04/CATALOG_RECEIPT_<ns>.json` x6 and one `...before_normalized_recook...` copy (262 MB each, 1.57 GB) | HISTORICAL | Earlier receipts. Only the unsuffixed files are live. | part 05 | No | MEASURED |
| Hash-checked decision receipts (as of 13:50-14:25Z) | `Staging/BankIntegration_2026-10-04/.../NORMAL_CONFIGURATION_f6fff4f9759af2db.json` (Gaza); `Staging/Iran_4km_2026-10-04/NEW_AREA_SCOPE.json` (Iran) | LIVE | Profile `decision_receipt`; existence and hash checked at run time. **Superseded in-window:** since 14:32:58Z all three profiles point to `Staging/AssetBankOperator_2026-10-06/Activation/DECISION.json` instead (reviewer; file exists, author listing). The two old receipts stay as provenance. | `geocity_bank_workflow.py:505-507` | Yes, until 14:32:58Z; the new target is LIVE now | MEASURED |
| Provenance-only profile keys | `selection_receipt`, `receipt`, `scope_extension_receipt` -> `Staging/ManagedExecution_2026-10-02/Task2,3,5/...`; `implementation_file`, `ASSEMBLY_CONTRACT.json`, `POLE5_NORMAL_CONFIGURATION.json`, `INSTANCE_MATERIALS.json` -> `Staging/RepairExecution_2026-10-03/` | HISTORICAL | Pinned by profile provenance; keep at path. The runtime does not read these keys (grep of `Content/Python`). | part 05 | Yes (profile provenance only) | MEASURED |

The source packages that the profiles name (`"source"`) are in 3.16.

### 3.8 Area maps, area outputs and all other .umap files

**Scope (MEASURED, part 04).** There are 64 `.umap` files under `Content/`: 6 in Project, 26 in Developers, 31 vendor maps and 1 at the root. No two share a hash, so Content holds no byte-duplicate maps. The live maps are not World Partition maps and have no `__ExternalActors__` folder, so each live `.umap` is a complete reference root. Copies of maps under Staging are listed in 3.15.

#### 3.8.A Project maps and area outputs

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Live map, GazaShujaiya (68,164,347 B, 2026-10-05 21:54 local) | `Content/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration.umap` | LIVE | sha 4efebdfb matches the status. It still renders Route A: the Natural child `MI_GeoCityGround` 8fb548f8 and LayerInfo set `1428_1804_0`. It holds the 2026-10-03 road actors (two DynamicRoadNetwork actors). | part 04 (b) | Is a root | MEASURED |
| Live map, GazaRimal (33,208,729 B, 2026-10-04 23:38 local) | `Content/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration.umap` | LIVE | At the survey its sha a6961c8e matched the status, and it referenced `/Game/Developers/USER/HoudiniCityProof/Materials/M_GeoCity_VertexColorPreview`. **Superseded after the window:** re-saved at 14:52:20Z, now 1d670c8e (33,209,758 B; reviewer hash). a6961c8e is kept at `Staging/ReusableSky_2026-10-06/Before/`. The new state was not re-scanned for references. | part 04 (a), (b); reviewer; author listing | Is a root | MEASURED |
| Live map, Iran (86,341,223 B, 13:39Z today) | `Content/Project/Areas/Iran_38196167_46086167_4km/BankIntegration_v015/L_Iran_38196167_46086167_4km.umap` | LIVE | sha c409279c matches today's re-save (it was 623aa0c0). No Staging backup of 623aa0c0 exists. The fresh reopen is pending. | part 04 (b); part 05 (b) | Is a root | MEASURED |
| Area content reached from the maps (266 packages: 185 Shujaiya, 73 Rimal, 8 Iran) | `Content/Project/Areas/{GazaShujaiya,GazaRimal,Iran_...}/`: baked meshes, current LayerInfos (4 per area), area MIs, RoadBLD presets and sidewalks (`GazaShujaiya/RoadBLD/Sidewalks`, 5, reached transitively), the 2 current clip runs | LIVE | n/a | part 04 closure | Yes | MEASURED |
| Stale RoadBLD clip runs, Shujaiya (628 packages, 85.8 MB) | `Content/Project/Areas/GazaShujaiya/RoadBLD/ClippedGeometry/*` (139 of 141 run folders) | DEAD | Leftovers of earlier 2026-10-03 RoadBLD attempts. The map references only runs `..._141625759113` and `20261003T203730573110_212401627821`. The lifecycle may record these runs in its ledger, which was not read. **Excluded from any cleanup:** run `20261003T203730573110_212401627821` (87 uassets, MEASURED). The reviewer identifies it as the 87 unvalidated road candidates; it is not part of this DEAD group, and the map references it. | 0 referrers (part 04); one stale run is named in `Staging/AppearanceRepair_2026-10-03/NATIVE_METADATA_STALE_20261003T135414437654Z.json:53075` | No | MEASURED |
| Stale generated LayerInfos (72) | Rimal `BankIntegration_v015/GazaRimal/LayerInfos/` prefixes `1446_373`, `1452_373`, `1453_373`, `1454_373`, `2860_3236`, `4310_3236`, `5718_6095`, `8598_7523` (32); Shujaiya `.../GazaShujaiya/LayerInfos/` prefixes `1425_1808`, `2881_1808`, `2882_1808`, `3_373_0_...landscape_0_`, `4288_4664`, `5739_4664`, `5741_4664`, `8578_8951` (32); Iran `.../Iran_.../LayerInfos/` prefixes `1428_1804`, `3_373_0_...landscape_0_` (8) | DEAD | Outputs of older Houdini landscape generations. Current sets: Rimal `1427_1805_0_...landscape_0_*`, Shujaiya `1428_1804_0_*`, Iran `3_373_0_...landscape_*`. CONFLICT: part 03 = HISTORICAL, part 04 = DEAD. DEAD chosen to match the other orphaned generated outputs (INFERRED). Keep Shujaiya `1428_1804_0` until the post-Hybrid verify recreates the four LayerInfos (`PLAN_HYBRID.md:37`). | 0 referrers in Content/Project and the profiles; ledgers not read | No (maps/profiles) | MEASURED |
| Stale Bake leftovers (7 packages, 12.8 MB) | `.../GazaShujaiya/BankIntegration_v015/Bake/GazaShujaiya_{road_surfaces,sidewalks,street_details,vegetation}` (10.6 MB, mtimes 2026-10-03); `.../GazaRimal/BankIntegration_v015/Bake/GazaRimal_{sidewalks,street_details,vegetation}` (2.2 MB) | DEAD | Superseded Houdini bake outputs, replaced by the RoadBLD road role and newer bakes (superseded: INFERRED) | 0 referrers | No | MEASURED; INFERRED |
| Old Rimal surface-painting map and its outputs | `Content/Project/Areas/GazaRimal/L_GazaRimal_SurfacePainting_20261002.umap` (6,507,312 B, a0bfaae9), `Areas/GazaRimal/BakedSurfacePainting/*` (5), `Areas/GazaRimal/LayerInfos/GeoCity_city_v007_SurfacePainting_v002_*` (8) | HISTORICAL | An earlier accepted area map, superseded by BankIntegration_v015. A closed chain: the map uses HDA v007 (3.2), which uses `MI_StarterSurfaceBank_Default` (3.9). | `Staging/ModelBank/SurfacePainting/README.md:11` ("remains on its accepted v002 HDA ... preserved") | No | DOCUMENTED; MEASURED |
| Stage 1 WorldBLD map | `Content/Project/Areas/Stage1Kit/Maps/Stage1Kit.umap` (15,852,307 B, 93df54aa, 09-26) | HISTORICAL | The WorldBLD Stage 1 baseline. It references 24 `Content/WorldBLD` assets, `District_LittleHavana_Dense` and `RoadBLD_Generated/Presets`. | `Staging/UNREAL_DEPENDENCY_REVIEW_2026-09-29.md:8` | No | DOCUMENTED |
| District asset | `Content/Project/Shared/Districts/District_LittleHavana_Dense` | HISTORICAL | WorldBLD Stage 1; referenced only by Stage1Kit | `UNREAL_DEPENDENCY_REVIEW_2026-09-29.md:8,11` | No | DOCUMENTED |
| Stray Untitled world | `Content/Untitled.umap` (12,968 B, aba72605, 2026-09-25 16:59 local), `Content/Untitled_HLOD0_Instancing.uasset`, `Content/__ExternalActors__/Untitled/**` (139 files, 32 MB), `Content/__ExternalObjects__/Untitled/**` (5) | DEAD | The default World Partition map from project creation, never used. It is not an area map. | `Staging/TrackA_Tests/HoudiniCityProof/01_audit/UNREAL_AUDIT.md:34` ("Only the stray `/Game/Untitled` is WP"); 0 referrers | No | DOCUMENTED; MEASURED |

The area Cook outputs (DEAD) are classified in 3.2.E. The pre-PermanentBank recovery world `Content/Project/Recovery/BeforePermanentBank_20261002.umap` (HISTORICAL) is in 3.10.

#### 3.8.B Developer maps (`Content/Developers/USER/`; records found by one scan of Staging `*.md/*.json/*.txt`, excluding `*_STATE.json`, `Before/` and `Backups/`)

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| TrackA base (46,550 B) | `TrackA_T0-T5/TrackA_Base.umap` (753923ef) | HISTORICAL | Track A proof | `Staging/TrackA_Tests/HoudiniCityProof/06_B1_B2_LIVE_RESULT.md:25` | No | MEASURED |
| T0 load (55,260 B) | `TrackA_T0-T5/T0_Load.umap` (3cb01850) | HISTORICAL | Track A proof | `Staging/Archive/PreFinalVision_2026-09-29/Operator_Legacy/done/TASK_0009.md:1` | No | MEASURED |
| T1 origin (55,308 B) | `TrackA_T0-T5/T1_Origin.umap` (9ebd013c) | HISTORICAL | Track A proof | `.../Operator_Legacy/done/TASK_0011.md:16` | No | MEASURED |
| T2 orient (2,370,026 B) | `TrackA_T0-T5/T2_Orient.umap` (6ea3aa06) | HISTORICAL | Track A proof | `.../Operator_Legacy/done/TASK_0014.md:1` | No | MEASURED |
| T5 masks (46,490 B) | `TrackA_T0-T5/T5_Masks.umap` (8172b2df) | HISTORICAL | Track A proof | `Staging/TrackA_Tests/HoudiniCityProof/01_audit/UNREAL_AUDIT.md:34` | No | MEASURED |
| Houdini city proof (87,908 B) | `HoudiniCityProof/HoudiniCityProof.umap` (fcd3d764) | HISTORICAL | Proof map (keep decision) | `UNREAL_DEPENDENCY_REVIEW_2026-09-29.md:9` | No | MEASURED |
| Bank catalog connection (22,871 B) | `ModelBankProof/L_BankCatalogConnection_2026_09_30.umap` (91e75f00) | HISTORICAL | Proof map | `Staging/ModelBank/Connection_2026-09-30/RESULT.md:17` | No | MEASURED |
| Pole pilot (6,565,701 B) | `HoudiniCityProof/DirectPickerPilot/L_GazaRimal_PolePilot_20261001.umap` (7d4e50c9) | HISTORICAL | Pilot | `.../GeoCity_direct_picker_UI_2026-10-01/RESULT.md:18` | No | MEASURED |
| V3 disabled catalog (6,506,299 B) | `HoudiniCityProof/V3DisabledCatalog/L_GazaRimal_V3_DisabledCatalog_20261001.umap` (57528127) | HISTORICAL | Pilot | `.../GeoCity_v003_disabled_catalog_UI_2026-10-01/RESULT.md:19` | No | MEASURED |
| Shujaiya second area (6,322,699 B) | `HoudiniCityProof/L_GazaShujaiya_SecondArea_20261001.umap` (d5aa6161) | HISTORICAL | Pilot | `.../GeoCity_v004_Shujaiya_Repeat_2026-10-01/RESULT.md:7` | No | MEASURED |
| V4 full catalog (6,547,451 B) | `HoudiniCityProof/L_GazaRimal_V4_FullCatalog_20261001.umap` (57e8d45d) | HISTORICAL | Pilot | `.../GeoCity_v004_full_catalog_UI_2026-10-01/PACKAGE_AUDIT.md:99` | No | MEASURED |
| V5 LayerInfo (6,549,558 B) | `HoudiniCityProof/V5LayerInfoBake/L_GazaRimal_V5_LayerInfo_20261001.umap` (b9f313da) | HISTORICAL | Pilot | `.../GeoCity_v005_layerinfo_UI_2026-10-01/PACKAGE_AUDIT.md:14` | No | MEASURED |
| V6 update test (6,578,967 B) | `HoudiniCityProof/L_GazaRimal_V6_UpdateTest_20261001.umap` (3829bb02) | HISTORICAL | Pilot | `.../GeoCity_v006_update_UI_2026-10-01/RESULT.md:9` | No | MEASURED |
| Shujaiya V4 repeat (6,326,563 B) | `HoudiniCityProof/L_GazaShujaiya_V4_RepeatTest_20261001.umap` (04512fd5) | HISTORICAL | Pilot | `.../GeoCity_v004_Shujaiya_Repeat_2026-10-01/RESULT.md:7` | No | MEASURED |
| Shujaiya V6 generate/update (6,318,064 B) | `HoudiniCityProof/L_GazaShujaiya_V6_GenerateUpdate_20261001.umap` (e4f4f25b) | HISTORICAL | Pilot | `.../GeoCity_v006_Shujaiya_GenerateUpdate_2026-10-01/RESULT.md:10` | No | MEASURED |
| B2 original Untitled inspection (6,544,168 B) | `HoudiniCityProof/L_B2_OriginalUntitled_Inspection_20261001.umap` (6abbc0bb) | HISTORICAL | Saved for Aviv's inspection | `Staging/ToolchainChecks/B2_UNTITLED_PRESERVATION_2026-10-01.md:5` (hash 6ABBC0BB... matches) | No | MEASURED |
| V6 semantic probe (6,569,870 B) | `HoudiniCityProof/L_GazaRimal_V6_SemanticProbe_20261001.umap` (582a7f9c) | HISTORICAL | Pilot | `.../GeoCity_v006_LandscapeSentinel_2026-10-01/RESULT.md:9` | No | MEASURED |
| V6 catalog fixture (6,559,421 B) | `HoudiniCityProof/CatalogFixture/L_GazaRimal_V6_CatalogFixture_20261001.umap` (a89ce30f) | HISTORICAL | Pilot | `Staging/ModelBank/CatalogFixture_2026-10-01/LIVE_RESULT.md:31` | No | MEASURED |
| V6 catalog fixture regen (10,288,094 B) | `HoudiniCityProof/CatalogFixture/L_GazaRimal_V6_CatalogFixture_Regen_20261001.umap` (448b02d4) | HISTORICAL | Pilot | `Staging/ModelBank/CatalogFixture_2026-10-01/LIVE_RESULT.md:39` | No | MEASURED |
| V6 approved pole pilot (6,619,024 B) | `HoudiniCityProof/V6ApprovedPolePilot/L_GazaRimal_V6_ApprovedPolePilot_20261001.umap` (acdcda8f) | HISTORICAL | Pilot | `.../GeoCity_v006_ApprovedPolePilot_2026-10-01/RESULT.md:18` | No | MEASURED |
| V7 full catalog pole pilot (6,572,457 B) | `HoudiniCityProof/V7FullCatalogPolePilot/L_GazaRimal_V7_FullCatalogPolePilot_20261001.umap` (655814ca) | HISTORICAL | Pilot | `Staging/Archive/ReturnToPipeline_2026-10-02/CURRENT_STATE_before.md:49` | No | MEASURED |
| One wall module (82,475 B) | `HoudiniCityProof/SingleModuleConnection/L_GazaRimal_OneWallModule_20261001.umap` (7326b3de) | HISTORICAL | Proof | `Staging/RestartReview_2026-10-01/BuildGenSingleProof/PROCESSES_AFTER.json:25` | No | MEASURED |
| BuildGen single wall (10,995 B) | `HoudiniCityProof/BuildGenSingleProof/L_BuildGenSingleWall_Empty_20261001.umap` (013bef3e) | HISTORICAL | Proof | `Staging/RestartReview_2026-10-01/BuildGenSingleProof/RESULT.md:57` | No | MEASURED |
| Terrain material proof (6,462,606 B) | `HoudiniCityProof/TerrainMaterialProof/L_GazaRimal_TerrainMaterial_Proof.umap` (7f17d25b) | HISTORICAL | Proof | `Staging/RestartReview_2026-10-01/TerrainMaterialProof/RESULT.md:53` | No | MEASURED |
| V13 colors and models (6,883,075 B) | `HoudiniCityProof/V13ConnectedPreview/L_GazaRimal_V13_ColorsModels_20261002.umap` (4ac2e2bf) | HISTORICAL | Preview. It references `MI_SurfaceBank_AllLayers`, HDA v014 and `DT_NonBuildingBank_v3`. | `Staging/ModelBank/PermanentIntegration_2026-10-02/EDITOR_HANDOFF.md:24` | No | MEASURED |
| Stray V7 Untitled (358,293 B) | `HoudiniCityProof/V7FullCatalogPolePilot/Untitled.umap` (9358d19d, 10-02 11:43 local) | DEAD | No Staging record found (0 hits for `V7FullCatalogPolePilot/Untitled`). INFERRED: a stray save. | part 04 record scan | No | MEASURED; INFERRED |

#### 3.8.C Vendor demo maps (31; their class follows the pack, per part 04's rule)

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Demo maps in packs classed LIVE (27) | AssetsvilleTown (Demonstration 3387a414, Overview 909ce3af); FC_Coastal_Landscape (Map_CoastalLandscape 209,963,913 B, 50817bfa); HighPoly_Tree_Model (HP_Tree_Showcace b8d2ead8); Iceland_Environment (Lv_Mountain_Tops_VT 179,723,634 B a396b8c5, _Elevation 92ccf279); ModularBuildingSet (Demo_Scene **414,527,597 B** f851089a, Overview 78,872,833 B 2d922bbc); ModularCourtyard (5 maps); MWLandscapeAutoMaterial (Desert dedd5a6c, Island ce6a87a1, MountainRange cdd6d9ed; mtime 2026-10-05 17:11 local); Palms_Pack_01 (Scene d9319438, Showroom 773efe5b); ProceduralBuildingGenerator (Demo_GhostCity 05ac1f62, Features_Highlight d21ede79); StarterContent (Advanced_Lighting, Minimal_Default, StarterMap); Stylized_Egypt (fb72d995); UtopianCity (DemoMap 154,807,118 B bbee32d8, Overview 6c5bbecd); Warehouse_Building (71be5ed0) | LIVE | Vendor payload of LIVE packs. The maps themselves are not referenced by any LIVE root. | All byte- or size-identical to their VaultCache copies (part 04 (d)) | No (the maps) | MEASURED |
| Demo maps in unreferenced packs (4) | FantasyRuins (Demo b71b877d, Overview f96065f4); PWL_Light_Manager (Demo 9bdc7f86); Radar (L_RadarExample 2188f3ed) | DEAD | Follows the pack class (unreferenced vendor packs, 3.12) | part 04 (d) | No | MEASURED |

### 3.9 Ground-material routes (Natural, Path B, Hybrid, S1 v1, S1v2) and their assets

#### 3.9.A Route per area (MEASURED, part 03)

Label: every cell in the next table is MEASURED (part 03) as of 13:50-14:25Z. Superseded in-window: at 14:32:58Z the profiles became Shujaiya f722381f, Rimal e6dead27 and Iran cb0f3cab, and their material keys were not re-read. After the window the Rimal map became 1d670c8e.

| Area | Profile (sha) | Material keys | Route now |
|---|---|---|---|
| GazaShujaiya | `Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json` (4174a627) | `:13` `landscape_material` = `/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_Auto.MI_GeoCityGround_Auto`; `landscape_grass.enabled` = false (`:78087`; base MI `:78079`, coverage 0.15, ground_layer Sand_01); `painted_layer_names` = [Sand_01, Sand_02, Dirt_Path, Sand_Path] (`:78164`); `external_landscape_material.decision` (`:78171`); `parent_chain` = [`/Game/Project/Shared/SurfacePainting/Auto_20261006/M_GeoCityAuto.M_GeoCityAuto`] (`:78173`); `static_switches_false` = 5 MW Procedurals; `surface_choices` paint 17/18/16/20 | **Split state.** The profile is on Route C (Hybrid), but both target assets are absent. The saved map 4efebdfb still renders Route A. Regeneration is blocked until `MI_GeoCityGround_Auto` is saved or the profile is patched. No ready-made clean rollback exists, so a Natural fallback needs a manager-written leaf patch: Natural child, drop `external_landscape_material`, keep grass false, keep registry 8d8622b2. |
| GazaRimal | `Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json` (492b9ac5) | `:13` = Rimal `MI_GeoCityGround`; `landscape_grass.enabled` = true (`:83598`; base MI `:83590`, coverage 0.15); the same four painted layers; no `external_landscape_material` key | **Route A (Natural) with Grass.** The map a6961c8e binds the Rimal `MI_GeoCityGround`, the base MI and the LG grass. The Hybrid for Rimal is planned later (`PLAN_HYBRID.md:30,54`). |
| Iran_38196167_46086167_4km | `Staging/ModelBank/Iran_38196167_46086167_4km/AREA_PROFILE.json` (004ec07d) | `:13` = base `MI_SurfaceBank_Natural` directly; no `landscape_grass`, `painted_layer_names` or `external_landscape_material` keys; `surface_normal_overrides` -> `T_Sand_0{1,2}_Normal_GeoCity` | **Route A (Natural base MI), Grass off** (`geocity_landscape_workflow.py:214-216` returns disabled when the block is absent). The map c409279c references the base MI, the LG grass and LayerInfo set `3_373_0_...landscape_*`. |

#### 3.9.B Route A, Natural master (current on Rimal and Iran; still rendered on Shujaiya's saved map)

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Natural master | `/Game/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural` (70f82e50, 1,151,295 B, saved 2026-10-05 18:43Z) | LIVE | The 18:43Z re-save was `prepare()` during Aviv's menu run | Hard-coded in `geocity_landscape_workflow.py:16` (LW d1a5d5fd = manifest pin); `Incident_01a10c77_2026-10-05/DECISION_LET_RUN_FINISH.json:63` | Yes (LW:16; base MI) | MEASURED; DOCUMENTED |
| Natural base MI | `.../Appearance_20261003/MI_SurfaceBank_Natural` (27b379f4) | LIVE | n/a | Iran profile `:13`; the Iran and Rimal maps; both `MI_GeoCityGround`; `LW:15`; both Gaza profiles' `landscape_grass.base_material_instance` (Shujaiya `:78079`, Rimal `:83590`) | Yes | MEASURED |
| Rimal area child | `/Game/Project/Areas/GazaRimal/BankIntegration_v015/Materials/MI_GeoCityGround` (99ad6bb8) | LIVE | n/a | Rimal profile `:13`; Rimal map a6961c8e | Yes | MEASURED |
| Shujaiya area child | `/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround` (8fb548f8, saved 10-05 18:43Z) | LIVE | Transitional: no longer in the profile (`:13` -> `_Auto`). It is the map rollback target. It becomes HISTORICAL only after the Hybrid save, the fresh verify and a `RATIFICATION_B3_HYBRID.json`. | Binary grep hit in `L_GazaShujaiya_BankIntegration` (4efebdfb); `Hybrid_Auto/README.md:270-285` | Yes (current saved map) | MEASURED; DOCUMENTED |
| Grass type | `.../Appearance_20261003/LG_GeoCity_PermittedGroundGrass` | LIVE | n/a | Referenced by all 3 area maps and by the master; Rimal grass enabled (`PermanentIntegration.../AREA_PROFILE.json:83598`) | Yes | MEASURED |
| EpicResident2K textures (4) | `.../Appearance_20261003/Textures/EpicResident2K/T_Ground_Gravel_{D,N}...`, `T_Rock_Sandstone_{D,N}...` | LIVE | n/a | Referenced by both `MI_GeoCityGround`; the `_N` maps are in both Gaza profiles' `surface_normal_overrides` | Yes | MEASURED |
| GeoCity normals and masks (6) | `.../Textures/T_Sand_0{1,2}_Normal_GeoCity`, `T_{Sand_01,Sand_02,Dirt_Path_01,Sand_Path_01}_Mask_GeoCity` | LIVE | n/a | The normals are referenced by the master, the base MI and the Iran profile; the masks by the master | Yes | MEASURED |
| Resident4K albedo (41.4 MB) | `.../Appearance_20261003/Textures/Resident4K/T_Sand_01_Albedo_GeoCityResident4K` | HISTORICAL | Superseded by the EpicResident2K set (INFERRED; no explicit record line). Last used in the r026/r027 receipts. CONFLICT: part 03 = HISTORICAL, part 04 = DEAD (candidate). HISTORICAL chosen because nothing records a failure, so it is superseded rather than dead (INFERRED). | 0 references in any `.uasset`/`.umap` across 30 GB of Content and the 3 profiles; `Staging/GroundPainting_2026-10-04/Revision_2026-10-05/EPIC_GROUND_*_r027_*` | No | MEASURED; INFERRED |
| Other LIVE landscape/road materials | `/Game/Project/Shared/Landscape/M_Landscape_GazaRimal`; `/Game/Project/Shared/RoadBLD/Materials/*` (1 MI) | LIVE | `UNREAL_DEPENDENCY_REVIEW_2026-09-29.md:11` says "The shared Districts and Landscape assets are historical Stage 1 material". That holds for Districts, not for this Landscape material. It is also a Shujaiya dependency despite its Rimal name. | `M_Landscape_GazaRimal` is named by all 3 live maps (part 04; author re-grep of the Shujaiya map: 1 hit); the RoadBLD MI by the Shujaiya map and the profiles | Yes | MEASURED |

#### 3.9.C Route B, Path B pure MW (superseded)

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Path B route as a whole | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/PathB_MW/` | HISTORICAL | A parallel route to the Hybrid, superseded. It fails two needs. The MW material names only one layer, so the plugin drops the 4 Houdini layers on regeneration. It also ignores the RoadBed/BuildingPad masks. Several files inside are LIVE (rows below), so add a banner only and move nothing. | `DECISION_HYBRID_20261006.json:23` ("Path B superseded by Hybrid"); Shujaiya profile `:78171`; reason at `Hybrid_Auto/PLAN_HYBRID.md:7`; chosen earlier at `STAGE1_GROUND_PLAN.md:309-310` | Partly (rows below) | DOCUMENTED |
| Path B in-editor scripts | `PathB_MW/pathb_assign_and_save.py` (4936bd5b), `pathb_verify_fresh.py` (5f2c480f), `pathb_tints.py`, `pathb_png_mean.py` | HISTORICAL | The Hybrid scripts are forks that copy this code rather than import it (`hybrid_assign_and_save.py:2`, `hybrid_verify_fresh.py:2`). The pins MATCH. | All 5 `pathb_*` are still pinned in `Operator/SCRIPT_PINS.json` | Pinned only (a pattern for the Hybrid) | MEASURED |
| Path B profile patch (rollback tool) | `PathB_MW/pathb_profile_patch.py` (00ad0511) | HISTORICAL | Superseded route, but still a documented rollback tool. Keep. | `Hybrid_Auto/README.md:276` (pre-Path B baseline via `--rollback`) | Yes (documented rollback) | DOCUMENTED |
| Tint presets | `PathB_MW/TINT_PRESETS.json` | LIVE | The Hybrid MI uses preset P1 | `PLAN_HYBRID.md:30`; `Hybrid_Auto/DECISIONS.json:35`; read by `hybrid_build_master_offline.py:428` | Yes | MEASURED |
| Path B patched sealed module (never deployed) | `PathB_MW/patched/geocity_landscape_workflow.py` (2bc51f97), `geocity_landscape_workflow.patch`, `patched/PREDICTED_geocity_runtime_manifest_option1.json` (predicted seal 6cb588f6), `RESEAL.md` | DUPLICATE | An unapplied fork of the LIVE `geocity_landscape_workflow.py` (d1a5d5fd), with a reseal recipe (`RESEAL.md:53-54`). The live LW is still d1a5d5fd (= `PathB_MW/Before/geocity_landscape_workflow_d1a5d5fd.py`) and the manifest is still 258469e1. CONFLICT: part 02 = DUPLICATE, part 03 = HISTORICAL. DUPLICATE chosen because it is a parallel version of a LIVE sealed file (mission definition; INFERRED). | `PLAN_HYBRID.md:9` ("No change to the sealed Python: external-material mode is already in effect") | No | MEASURED; DOCUMENTED |
| Path B MI (planned, never saved) | `/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_MW` | DEAD | Never saved, and must stay absent. The Hybrid scripts gate on its absence. | Absent on disk; 0 references in Content/Project and the profiles; `Hybrid_Auto/DECISIONS.json:36`; `hybrid_assign_and_save.py:487` | Only as an absence gate (and as the target of the 1bd89e5b rollback profile) | MEASURED; DOCUMENTED |
| Path B receipts and docs | `PathB_MW/receipts/PATHB_{INSPECT,APPLY}_*_PID34928.json` (`INSPECTED_READ_ONLY`, `APPLIED_VERIFIED_NO_SAVE`), `DESIGN.md`, `RISKS.md`, `CAPTURE_PLAN.md`, `CodexReview/` | HISTORICAL | `DESIGN.md:3` "Nothing here was executed in Unreal" is stale: the receipts show an in-memory apply. | receipts | No | MEASURED |

The pre-Path B profile backup (`PathB_MW/Before/AREA_PROFILE_1328d5bb_*`) is in 3.7. The Path B map backup is in 3.15.

#### 3.9.D Route C, Hybrid (chosen; not yet built)

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Hybrid plan and runbook | `Stage1_Ground/Hybrid_Auto/PLAN_HYBRID.md`, `README.md`, `DECISIONS.json`, `HYBRID_EDIT_EXPECTATIONS.json` | LIVE | The current ground plan. `README.md:3`: "Nothing here has been executed in Unreal". | `PLAN_HYBRID.md:3` ("Decided by Aviv 2026-10-06 ... 'build the hybrid'"); `DECISION_HYBRID_20261006.json:6`; PROJECT_STATUS §2 line 22 | Yes | DOCUMENTED |
| Hybrid scripts (5) and Args (8) | `Hybrid_Auto/hybrid_build_master.py` (ad7daced), `hybrid_assign_and_save.py` (dded811f), `hybrid_verify_fresh.py` (0aab1528), `hybrid_profile_patch.py` (2a147d96), `hybrid_build_master_offline.py` (69c98d51), `Args/HYBRID_ARGS_*.json`, `Hybrid_Auto/SCRIPT_PINS.json` | LIVE | Each script re-implements a small `lease_fields()` helper. This is not a route duplicate. | On-disk sha256 equals both `Hybrid_Auto/SCRIPT_PINS.json` and `Operator/SCRIPT_PINS.json` for all 5 | Yes (`ASSIGNMENT.json` `waiting_for`; status §2) | MEASURED |
| Hybrid master (planned) | `/Game/Project/Shared/SurfacePainting/Auto_20261006/M_GeoCityAuto` | LIVE | Planned asset, **absent**. The folder `Content/Project/Shared/SurfacePainting/Auto_20261006` does not exist. | Shujaiya profile `:78173` `parent_chain` | Yes (profile; dangling) | MEASURED |
| Hybrid area MI (planned) | `/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_Auto` | LIVE | Planned asset, **absent**. An ordinary regeneration now is expected to fail at `geocity_bank_workflow.py:650` (INFERRED). | Shujaiya profile `:13` (its only reference) | Yes (profile; dangling) | MEASURED; INFERRED |
| Hybrid inspect receipts | `Hybrid_Auto/receipts/HYBRID_MASTER_INSPECT_hyb_inspect_r00{1,2}_PID23068.json` (`FAILED_INSPECT`, legacy output-name reader) | HISTORICAL | Evidence of the reader bug, which is now fixed. Not a dead route. | `Hybrid_Auto/README.md:113` (the legacy reader is advisory only) | No | MEASURED |
| Hybrid inputs kept in other folders | `Stage1_Ground/S1_Prep/AstraMWInventory/native_inventory_complete.json`; `Staging/GroundPainting_2026-10-04/native_graph_stochastic.py` | LIVE | They live inside the superseded S1 folder and the GroundPainting folder. Do not move them. | `hybrid_build_master_offline.py:426` (`INVENTORY`); `hybrid_build_master.py:78`, `hybrid_assign_and_save.py:68`, `hybrid_verify_fresh.py:52` (`HELPER_REL`) | Yes | MEASURED |

The Hybrid rollback set `Hybrid_Auto/Before/` is in 3.7 (profile and patch record) and 3.15 (map copy).

#### 3.9.E S1 v1 (rejected) and S1v2 / v2a (shelved)

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| S1 v1 material edit | `Stage1_Ground/S1_Prep/s1_material_edit.py` (5c48daaf), `s1_material_edit_offline.py`, `S1_EDIT_EXPECTATIONS*.json`, `S1_MAXREUSE_EDIT_SPEC.json`, `Stage1_Ground/Args/S1_ARGS_*` | DEAD | Aviv rejected it after an in-memory apply and tune on PID23156 (`S1_APPLY_...` `APPLIED_VERIFIED_NO_SAVE`; `S1_TUNE_...` `TUNED_VERIFIED_NO_SAVE`). It was discarded without saving, and its `MF_GeoCity_*` functions never reached disk. `S1_Prep/README.md:3` is stale. CONFLICT: part 02 = HISTORICAL, part 03 = DEAD. DEAD chosen because the route was tried and rejected, i.e. failed (mission definition; INFERRED). | `STAGE1_GROUND_PLAN.md:304-305` ("v1 rejected ... Discarded without saving"); `PLAN_HYBRID.md:7`; 0 `MF_GeoCity_*` under Content | No. The Hybrid copies the Builder pattern (`hybrid_build_master.py:357`); PLAN_HYBRID cites `s1_material_edit.py` as the "Builder" pattern. | MEASURED; DOCUMENTED |
| S1 helper scripts (verify, capture, backup) | `Stage1_Ground/S1_Prep/s1_verify.py`, `s1_capture.py`, `s1_backup.py` | LIVE | Pins MATCH. `s1_backup.py` produced the pinned set S1B_20261005T202836Z. CONFLICT: part 02 = LIVE (documented as working tooling, PROJECT_STATUS §2); part 03 = HISTORICAL (`PathB_MW/RESEAL.md:66`: verify/capture assume the Natural child). LIVE chosen conservatively because Rimal and Iran are still Natural (INFERRED). The manager should state their role. | sha check; PROJECT_STATUS §2 line 23 | No caller: the Hybrid scripts do not import them (only a comment at `hybrid_build_master.py:56`) | DOCUMENTED; MEASURED |
| S1 v1 run tooling | `Stage1_Ground/S1_Prep/run_s1.py`, `s1_set_args.py`, `graph_dump_tools.py`, `MW_HP_PackInventory/` | HISTORICAL | Tooling of the rejected v1 route. Pins MATCH. `pegasus_listing/` is in 3.2. | part 02, part 03 | No | MEASURED; DOCUMENTED |
| S1v2 / v2a | `Stage1_Ground/S1v2/` (`s1v2_material_edit.py` 3e965c48, `s1v2a_material_edit.py` bf1bee4f, offline variants, `run_s1v2a.py`, `noise_stats_v2a.py`, specs, `Args/`, `SCRIPT_PINS_v2a.json`), plus `Stage1_Ground/Args/S1V2A_ARGS_GazaShujaiya_*.json` (4) | HISTORICAL | Shelved and never executed. No `MF_GeoCityV2*` functions exist on disk. The v2a pins MATCH. `s1v2_material_edit*.py` are unpinned and marked "reference only" (README_v2a). | `STAGE1_GROUND_PLAN.md:310`; `DECISION_HYBRID_20261006.json:23` ("v2a and full-v2 shelved"); `S1v2/README_v2a.md:3` ("PREPARED OFFLINE, NOT EXECUTED") | No | MEASURED; DOCUMENTED |

The S1 backup set (`S1_Prep/Before/S1B_20261005T202836Z/`) is in 3.15.

#### 3.9.F Older SurfacePainting materials (the HDAs are in 3.2; the old Rimal map is in 3.8)

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| 2026-10-02 SurfacePainting v002 chain | `/Game/Project/Shared/SurfacePainting/M_StarterSurfaceBank`, `MI_StarterSurfaceBank_Default` | HISTORICAL | The earlier paint-bank route. A closed chain: master <- MI <- HDA v007 <- old Rimal map. | `Staging/ModelBank/SurfacePainting/README.md:11`; `Staging/PaintBank_2026-10-02/FAMILY_NATIVE_ASSETS.json:273`; reverse check | No | MEASURED; DOCUMENTED |
| AllLayers materials | `/Game/Project/Shared/SurfacePainting/M_SurfaceBank_AllLayers`, `MI_SurfaceBank_AllLayers` | HISTORICAL | Not referenced in Content/Project. The MI is referenced by the Developer map `L_GazaRimal_V13_ColorsModels_20261002`, so it is not an orphan. Decide together with that map. | Content-wide grep (part 03) | No | MEASURED |

### 3.10 Recovery and snapshot assets in Content (and their Staging provenance)

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| 15 Recovery snapshots (0.7 MB; 11.9-113.9 KB each; saved 2026-10-05 18:41:17-19Z) | `Content/Project/Shared/Recovery/ProceduralCity_20261005/DiskFunctions/*.uasset` (`MF_MWAM_CombineNormal`, `CombineNormalSimple`, `DefaultLayer`, `DepthFade`, `LandscapeUVs`, `LayerBlend`, `Opacity`, `PivotMask`, `Roughness`, `SlopeMask`, `Snow`, `SnowMask`, `SubSurface`, `WaterMask`, `MW_MWAM_Water`) | DUPLICATE | Renamed, re-serialized copies of the original (Vault) MW vendor functions. Their sha256 differs from the vendor files (15 of 15) only because each was re-saved under a new package name, adding 48-909 B: `inspect_dirty_materials.py:19` copies the vendor file, then `:26` runs `save_loaded_asset`. Byte-exact originals exist in VaultCache and in `Staging/ProceduralCityRegeneration_2026-10-05/Before/DiskPackages/`. Each copy contains only its own Recovery path string. Outbound vendor refs: DefaultLayer 2, SubSurface 1, Water 2. CONFLICT: part 03 = DUPLICATE, part 04 = DEAD (snapshot, not a byte copy). DUPLICATE chosen because they are renamed copies of LIVE vendor content (INFERRED). | `DIRTY_MATERIAL_COMPARISON.json`: `disk_sha256` = Vault for 15 of 15; created by the Astra inspection (`DECISION_LET_RUN_FINISH.json:64`); reference checks in 3.10.B | **No** (0 inbound references) | MEASURED |
| 15 MW vendor functions | `Content/MWLandscapeAutoMaterial/Materials/MASTER/Func/*.uasset` (restored 2026-10-05 20:27:43Z) | LIVE | Vendor payload. The Hybrid duplicates `MTL_MWAM_AutoMaterial_MASTER`, which uses these functions (`PLAN_HYBRID.md:21`). | sha256 equals `VaultCache/MWLandsc0bb389159dceV3/.../Func/` for 15 of 15 today | Yes (Hybrid source) | MEASURED |
| Modified vendor copies (evidence) | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Incident_01a10c77_2026-10-05/MW_Func_modified_20261005T202743Z/` (15 files and `RESTORE_RECEIPT.json`) | HISTORICAL | Evidence of the 18:42Z modified save. The writer was **not** unidentified: `ProceduralCityRegeneration_2026-10-05/prepare_run.py:20` saved all 15. Before saving, that script asserted that the loaded and disk graphs matched once StateId/Combined*Types lines were ignored (`prepare_run.py:17`), so by its own check the change was derived-only (DOCUMENTED). | `RESTORE_RECEIPT.json:5` ("manager restored byte-identical VaultCache originals before Stage 1 backup"); `PREPARATION.json:31`; CombineNormal `saved_sha256` 65800a1e = `modified_sha256` | No | MEASURED; DOCUMENTED |
| Astra disk backups | `Staging/ProceduralCityRegeneration_2026-10-05/Before/DiskPackages/*.uasset` (15), plus `*_disk.t3d`, `*_loaded.t3d` and `.diff.txt` | HISTORICAL | Byte-identical to VaultCache (15 of 15). The provenance to keep if the Recovery copies leave Content. | sha256 | No | MEASURED |
| Pre-PermanentBank recovery world | `Content/Project/Recovery/BeforePermanentBank_20261002.umap` (13,215 B, e4dc6ac8) and HLOD stub; `Content/__ExternalActors__/Project/Recovery/**` (138 files, 32 MB); `Content/__ExternalObjects__/Project/Recovery/**` (5) | HISTORICAL | Preservation snapshot of the world before the bank work, 2026-10-02 | `Staging/ModelBank/PermanentIntegration_2026-10-02/WORLD_PRESERVATION.json:4`; 0 inbound references from outside its own folders | No | DOCUMENTED; MEASURED |
| Plant07 recovery | `Content/Project/Shared/ModelBank/Prepared/Recovery_20261004_Plant07` (3: `SM_Plant_07_6_G`, `MI_Plant_07_6_Leaves_G`, `MI_Plant_07_6_Stem_G`) | HISTORICAL | Recovery copy made during the bank's dirty-originals transfer | `Staging/BankIntegration_2026-10-04/RESULT.json:554` | No | DOCUMENTED |

#### 3.10.B Recovery reference check (MEASURED, part 03; run from the project root in Git Bash)

1. **Literal brief command:** `MSYS_NO_PATHCONV=1 grep -rla "/Game/Project/Shared/Recovery" Content/Project Content/MWLandscapeAutoMaterial --include=*.uasset --include=*.umap`
   - Result: 15 hits, all in the Recovery files themselves.
   - Each hit is a self-name string (checked per file with `grep -ao`).
2. **All of Content (30 GB), self files removed:** `MSYS_NO_PATHCONV=1 grep -rlaF "/Game/Project/Shared/Recovery" Content --include=*.uasset --include=*.umap | grep -v "^Content/Project/Shared/Recovery/"`
   - Result: 0 lines (47 s).
   - An earlier `--exclude-dir=Recovery` variant was discarded, because 4 directories named Recovery exist.
3. **Positive control:** the same method finds `L_GazaShujaiya_BankIntegration.umap` for the Shujaiya `MI_GeoCityGround` path.
   - A Python boundary-aware scan (`refscan.py`) covered 3,186 Content/Project binaries, the 3 profiles and `Content/Python/*.py`. It also found 0 references to each of the 15 packages.
4. **Staging text:** 20 files name the path. All are creation records, not consumers:
   - `ProceduralCityRegeneration_2026-10-05/{inspect_dirty_materials.py, prepare_run.py, DIRTY_MATERIAL_COMPARISON.json}`;
   - 15 `Before/*_disk.t3d`;
   - `PROJECT_STATUS_2026-10-06.md`;
   - `DECISION_LET_RUN_FINISH.json`.
   - No profile, pin file, args file or sealed runtime file names the path.
5. **Config and Python:** `MSYS_NO_PATHCONV=1 grep -rlF "Shared/Recovery" Config Content/Python --include=*.ini --include=*.py --include=*.json`
   - Result: 0.

Label: every cell in the next table is MEASURED (part 03, sha256).

| Hash comparison | Result |
|---|---|
| Each Recovery copy vs the vendor function of the same name in `Content/MWLandscapeAutoMaterial/Materials/MASTER/Func/` | DIFFERENT 15/15 (sizes +48 to +909 B) |
| Vendor vs `VaultCache/MWLandsc0bb389159dceV3/data/Content/MWLandscapeAutoMaterial/Materials/MASTER/Func/` | IDENTICAL 15/15 |
| Recovery vs `Incident.../MW_Func_modified_20261005T202743Z/` | DIFFERENT 15/15 |
| `DIRTY_MATERIAL_COMPARISON.json` `disk_sha256` vs Vault | IDENTICAL 15/15 |
| `ProceduralCityRegeneration.../Before/DiskPackages` vs Vault | IDENTICAL 15/15 |

Conclusion: the Recovery copies are renamed duplicates of today's vendor content (MEASURED). That their content is equivalent beyond the package rename is INFERRED from the copy-then-resave code path.

### 3.11 Asset bank, registries, catalog, modular kit, bank orphans

The holds (H0013, H0907, H0051, H0958, H0094) and the 87 unvalidated road candidates are mentioned only. They are not classified, and no proposal touches them. `Content/Project/Shared/ModelBank/Supply/` is not classified (snapshot caveat).

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Asset bank catalog | `Content/Project/Shared/ModelBank/DT_EnvironmentBank_v4.uasset` and `S_BankReleaseRow_v3` | LIVE | As of 13:50-14:25Z: 1,223 catalog identities, canonical digest f6fff4f9 for the Gaza profiles, 1,000 `/Game` packages named. **Superseded in-window:** at 14:32:57Z the bank operator rewrote it (now e26bf06c, 1,582,250 B), with row_count 1,295 and catalog_sha256 e0bd4e85 (Gaza) / a2d14c36 (Iran). The closure in 3.11.B uses the old state. | sha256 f763b072 = status §2, unchanged at 14:25Z (part 04); new hash from the reviewer; author listing | Is a root | MEASURED |
| Iran area-scoped catalog | `Content/Project/Shared/ModelBank/AreaScopes/DT_Iran_38196167_46086167_4km` | LIVE | Iran catalog 2e1e548f (status §2) as of 14:25Z. **Superseded in-window:** the Iran catalog_sha256 is a2d14c36 since 14:32:57Z (reviewer). | part 04 closure; reviewer | Yes (Iran profile) | MEASURED; DOCUMENTED |
| Older catalogs (2.1 MB) | `Content/Project/Shared/ModelBank/DT_BankRelease_v2`, `DT_BankRelease_AllDisabled_v2`, `DT_NonBuildingBank_v3` | HISTORICAL | Superseded by `DT_EnvironmentBank_v4`. Referenced only by Developer maps (V3/V4/V6 pilots, V13). | `Staging/ModelBank/UnifiedCatalogV2_2026-10-01/SCHEMA.md:7,9`; `UnifiedCatalogV3_2026-10-02/SCHEMA.md:3` | No | DOCUMENTED; MEASURED |
| Prepared bank content reached from LIVE roots | `Content/Project/Shared/ModelBank/Prepared/{External,Modular,Dependencies}` (1,407 of 1,674 ModelBank packages reachable) | LIVE | n/a | Closure; the registry chain binds 948 packages | Yes | MEASURED |
| Instancing materials | `Content/Project/Shared/ModelBank/Materials/Instancing` (1) and `.../Instancing/Repair_20261003` (4) | LIVE | Not named directly by a root, but reached transitively | closure (0 transitively unreachable) | Yes (transitive) | MEASURED |
| Bank orphans in the bank save scope (about 746 MB) | `ModelBank/Materials/BankIntegration_20261004` (92 of 95 unreachable); `Prepared/Dependencies/Textures` (135 of 296; 540 MB); `Prepared/Dependencies/Materials` (8); `Prepared/Modular/Additional20Dependencies/{Textures 9 (204 MB), Materials 3}` | DEAD | **Candidate; the DEAD class rests only on "unreferenced".** The catalog, maps, profiles and registry chain do not reference them. 135 textures and 68 materials have zero referrers in all of Content/Project and Developers. The bank result is still INCOMPLETE, so they may be meant for pending rows. Bank-owner decision. | `Staging/BankIntegration_2026-10-04/RESULT.json:4` (`ACTIVE_NATIVE_FULL_BANK_INTEGRATION_INCOMPLETE`); Python treats these folders as the bank named-save scope (`geocity_editor_action.py:32-34`) | No | MEASURED (unreferenced); INFERRED (dead) |
| Procedural v002 families for H0013 / H0020 | `Prepared/Modular/H0013/Procedural_v002` (9), `Prepared/Modular/H0020/Procedural_v002` (5) | DEAD | Candidate (unreferenced only). The bound registries (8d8622b2, b3fe7421) do not reach them. **H0013 is a hold: mention only, do not touch.** | 0 referrers | No | MEASURED |
| Current imported bank | `Content/Project/Shared/Bank_ME_v3` (172 packages, 1,488 MB) | LIVE | All 172 reachable (catalog 32 rows, registry, maps) | closure | Yes | MEASURED |
| Bank_ME v1 (79 packages, 123 MB) | `Content/Project/Shared/Bank_ME` | DUPLICATE | First import without textures. All 79 names recur in Bank_ME_v3, all with different sizes, so this is a superseded re-import, not a byte copy. It holds same-named copies of hold assets H0013/H0907/H0051/H0094 (mention only), so hold policy may require keeping it. | `Staging/ModelBank/ME/IMPORT_REPORT.md:3` (v1 import), `:91` (texture re-import) | No | MEASURED; DOCUMENTED |
| Bank_ME v2 | `Content/Project/Shared/Bank_ME_v2/Vegetation` (3: `Original_Submesh_0/1`, **`SM_H0958_CoconutPalm`**) | HISTORICAL | Partial texture re-import. Holds the H0958 hold asset (mention only). Keep. | `Staging/ModelBank/ME/IMPORT_REPORT.md:86` | No | DOCUMENTED |
| Six failed modular meshes (named, absent) | `/Game/Project/Shared/ModelBank/Prepared/Modular/H0017/Modules/SM_H0017_Tier01_WestFacade`, `...Tier03_EastFacade`, `...Tier04_EastFacade`, `...Tier05_EastFacade`, `...Tier05_WestFacade`; `/Game/.../H0019/Modules/SM_H0019_Roof_EastFacade` | DEAD | The "six failed parts": they fail the one-triangle check, were dirty and never saved, and are absent on disk. The bound registry chain still names them (dangling). Repair is step (1) of the AGENTS sequence. | `BankEditorInspection_2026-10-05/INSPECTION.md:16-18`; part 04 dangling-reference table | Yes (registry chain; dangling) | MEASURED; DOCUMENTED |

The bound registries are in 3.7, Plant07 in 3.10, `PE/ModelBank` in 3.16, and `Staging/ModelBank/ME/Sources` in 3.15.

#### 3.11.B Content/Project reference closure result (MEASURED, part 04; heuristic, not an Asset Registry graph)

Label: every number in the tables of 3.11.B is MEASURED (part 04) and uses the roots as of 13:45-14:25Z. These roots predate the in-window catalog and profile rewrite (14:32:57-58Z), the Rimal map re-save (14:52:20Z) and the new Supply folder. Re-run the closure after the bank lease is released.

**Root sets (unique package paths).**

| Root | Packages |
|---|---:|
| Shujaiya map | 392 |
| Rimal map | 173 |
| Iran map | 108 |
| The three `Staging/ModelBank/*/AREA_PROFILE.json` | 263 |
| `DT_EnvironmentBank_v4.uasset` | 1,000 |
| Registry chain (2 bound registries and their 116 referenced JSON files) | 948 |
| `Content/Python/*.py` | 8 |
| **Union** | **2,296** |

`Config/*.ini` holds no `/Game` path and no startup map. The transitive closure reaches 3,589 packages. A plugin-aware rerun reached 101 plugin packages and **0 additional `/Game` packages**. Both live Gaza maps reference about 1,330-1,460 `/RoadBLD/...` plugin paths.

**Result.**

| Set | Packages | Size |
|---|---:|---:|
| `Content/Project` packages (uasset and umap) | 3,186 | 7,697 MB |
| Directly unreferenced (by the task definition) | 1,803 | 7,154 MB |
| of which reached transitively (dependencies of LIVE assets) | 477 | n/a |
| **Transitively unreachable from LIVE roots** (the only basis for DEAD) | **1,326** | **2,968 MB** |

**Groups (transitively unreachable packages; MB is for the unreachable part).**

| Group (folder under `/Game/Project/`) | Directly unreferenced | Transitively unreachable | MB |
|---|---:|---:|---:|
| `Areas/GazaRimal/BakedSurfacePainting` | 5 | 5 | 0.8 |
| `Areas/GazaRimal/BankIntegration_v015/Bake` | 3 | 3 | 2.2 |
| `Areas/GazaRimal/BankIntegration_v015/Cook/.../B7CE31BC` | 113 | 113 | 664.1 |
| `Areas/GazaRimal/BankIntegration_v015/GazaRimal/LayerInfos` | 32 | 32 | 0.1 |
| `Areas/GazaRimal` (old SurfacePainting map) | 1 | 1 | 6.5 |
| `Areas/GazaRimal/LayerInfos` | 8 | 8 | 0.0 |
| `Areas/GazaShujaiya/BankIntegration_v015/Bake` | 4 | 4 | 10.6 |
| `Areas/GazaShujaiya/BankIntegration_v015/Cook/.../311CD685` | 88 | 88 | 790.8 |
| `Areas/GazaShujaiya/BankIntegration_v015/GazaShujaiya/LayerInfos` | 32 | 32 | 0.1 |
| `Areas/GazaShujaiya/RoadBLD/ClippedGeometry/*` | 628 | 628 | 85.8 |
| `Areas/GazaShujaiya/RoadBLD/Sidewalks` | 5 | 0 | 0.0 |
| `Areas/Iran_.../BankIntegration_v015/Cook/GeoCity_city_v015_4km/78F86F39` | 28 | 28 | 466.3 |
| `Areas/Iran_.../BankIntegration_v015/Iran_.../LayerInfos` | 8 | 8 | 0.0 |
| `Areas/Stage1Kit/Maps` | 1 | 1 | 15.9 |
| `Recovery` | 2 | 2 | 0.0 |
| `Shared/Bank_ME/{Buildings 38, Props 17, StreetFurniture 13, Vegetation 9, Vehicles 2}` | 79 | 79 | 128.3 |
| `Shared/Bank_ME_v2/Vegetation` | 3 | 3 | 0.2 |
| `Shared/Bank_ME_v3/*` (Buildings 57, Props 26, StreetFurniture 19, Vegetation 16, Vehicles 4) | 122 | 0 | 0.0 |
| `Shared/Districts` | 1 | 1 | 0.0 |
| `Shared/ModelBank` (older catalogs) | 3 | 3 | 2.1 |
| `Shared/ModelBank/Materials/BankIntegration_20261004` | 93 | 92 | 1.9 |
| `Shared/ModelBank/Materials/Instancing` (+ `Repair_20261003`) | 5 | 0 | 0.0 |
| `Shared/ModelBank/Prepared/Dependencies/Materials` | 98 | 8 | 0.1 |
| `Shared/ModelBank/Prepared/Dependencies/Textures` | 296 | 135 | 540.3 |
| `Shared/ModelBank/Prepared/Modular/Additional20Dependencies/Materials` | 3 | 3 | 0.0 |
| `Shared/ModelBank/Prepared/Modular/Additional20Dependencies/Textures` | 62 | 9 | 204.2 |
| `Shared/ModelBank/Prepared/Modular/Dependencies/{Materials 13, Textures 20}` | 33 | 0 | 0.0 |
| `Shared/ModelBank/Prepared/Modular/H*/Procedural_v002` | 14 | 14 | 4.1 |
| `Shared/ModelBank/Prepared/Recovery_20261004_Plant07` | 3 | 3 | 0.1 |
| `Shared/Recovery/ProceduralCity_20261005/DiskFunctions` | 15 | 15 | 0.7 |
| `Shared/SurfacePainting/Appearance_20261003` (+ `Textures`, `EpicResident2K`) | 7 | 0 | 0.0 |
| `Shared/SurfacePainting/Appearance_20261003/Textures/Resident4K` | 1 | 1 | 41.4 |
| `Shared/SurfacePainting/HDA` | 3 | 3 | 0.9 |
| `Shared/SurfacePainting` (Starter/AllLayers masters and MIs) | 4 | 4 | 0.6 |
| **Total** | **1,803** | **1,326** | **2,968.3** |

**Referrer notes for unreachable groups (MEASURED).** These packages are referenced only by other non-LIVE packages:
- BakedSurfacePainting and the old Rimal LayerInfos: only by `L_GazaRimal_SurfacePainting_20261002`.
- Recovery world: only by its own OFPA actors.
- Bank_ME v1: only by its own meshes (e.g. `SM_H0907_Arab_x3_fbx`, `SM_H0014_Building_01`).
- Districts: only by Stage1Kit.
- Older catalogs: only by Developer maps.
- Additional20 textures and materials: only by `SM_H0020_PF2_*` meshes.
- Plant07: only by its own mesh.
- SurfacePainting masters: by HDA v007 and the V13 map.

**Dangling references from LIVE roots (named, not on disk; MEASURED).**
- The six H0017/H0019 meshes, named by the registry chain (3.11 table).
- `MI_GeoCityGround_Auto` and `M_GeoCityAuto`, named by the Shujaiya profile (3.9).
- The other 15 unresolved names are folder prefixes, plus one truncated string (`/Game/Project/Shared/RoadBLD/Materials/MI_`) in the Shujaiya map.
- Vendor packs carry 82 pre-existing internal dangling names (e.g. `/Game/Textures`, `/Game/ModularCity`). These are vendor-internal and outside the project.

### 3.12 Vendor packs and other Content top-level folders

**Method (MEASURED, part 04).**
- Each `Content/<pack>` was compared file by file with `C:/ProgramData/Epic/EpicGamesLauncher/VaultCache/<id>/data/Content/<pack>`, by relative path and size.
- Five packs also got a full sha256 comparison: MWLandscapeAutoMaterial, Palms_Pack_01, HighPoly_Tree_Model, Radar and Warehouse_Building.

**Column meanings.** The "Referenced by LIVE?" cell gives two figures:
- "direct": packages of the pack named by the live maps / the profiles / the catalog.
- "closure": packages reachable from all LIVE roots, out of the pack's total.

`Content/` totals 29,882 MB.

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| AssetsvilleTown (681 MB, 1,077 files) | `Content/AssetsvilleTown`; VaultCache `Assetsvicb796a074ca2V2` | LIVE | Vendor pack, re-downloadable | 1,077/1,077 same path and size | direct 2 / 1 / 237; closure 261 / 1,077 | MEASURED |
| FC_Coastal_Landscape (1,921 MB, 84) | `Content/FC_Coastal_Landscape`; `FREE4x4k21f7cb882be0V1` | LIVE | Transitive only: reached through the `SurfacePainting/Appearance_20261003` material | 84/84 same | direct 0 / 0 / 0; closure 11 / 84 | MEASURED |
| FantasyRuins (245 MB, 33) | `Content/FantasyRuins`; `FreeSamp759c8fafaa38V1` | DEAD | Unreferenced vendor pack (DEAD rests only on "unreferenced"). It appears in `Staging/AssetBankOperator_2026-10-06/SOURCE_INVENTORY.json`, so the bank operator may plan to use it. Not a plain delete. | 33/33 same | direct 0; closure 0 / 33 | MEASURED |
| HighPoly_Tree_Model (38 MB, 9) | `Content/HighPoly_Tree_Model`; `HighPoly7a52ca673258V1` | LIVE | Planned consumer (status §5 proposes excluding it from Git) | 9/9 byte-identical; `AssetBankOperator_2026-10-06/EXPANSION_SUMMARY.json` source_packs `HighPoly_Tree_Model: 1` | direct 0; closure 0 / 9 (planned) | MEASURED; DOCUMENTED |
| Iceland_Environment (1,200 MB, 80) | `Content/Iceland_Environment`; `FREEMounc1f4bef6b908V1` | LIVE | Vendor pack | 80/80 same | direct 0 / 0 / 14; closure 35 / 80 | MEASURED |
| MOUT_Arabian (880 MB, 29) | `Content/MOUT_Arabian`; `ModularM8ab5ae4681caV6` | LIVE | **Partial install:** 29 of 789 vault files, all 29 the same size. The Sand normals and masks feed SurfacePainting. | 29 same size | direct 0 / 2 / 0; closure 16 / 29 | MEASURED |
| MWLandscapeAutoMaterial (702 MB, 100) | `Content/MWLandscapeAutoMaterial`; `MWLandsc0bb389159dceV3` | LIVE | Planned: the Hybrid ground master source. 15 functions were restored from Vault on 2026-10-05 (status §5 proposes excluding it from Git). | 100/100 byte-identical | direct 0; closure 0 / 100 (planned, `PLAN_HYBRID.md`) | MEASURED; DOCUMENTED |
| ModularBuildingSet (732 MB, 317) | `Content/ModularBuildingSet`; `ModularBuildingSet410` | LIVE | Vendor pack. Holds the largest single vendor file (Demo_Scene.umap, 395 MB). | 317/317 same | direct 2 / 2 / 139; closure 205 / 317 | MEASURED |
| ModularCourtyard (1,935 MB, 328) | `Content/ModularCourtyard`; `ModularC798ab2003378V1` | LIVE | Vendor pack | 328/328 same | direct 23 / 23 / 104; closure 198 / 328 | MEASURED |
| PWL_Light_Manager (235 MB, 56) | `Content/PWL_Light_Manager`; `Untitled3a702319480fV1` | DEAD | Unreferenced vendor pack (DEAD rests only on "unreferenced") | 56/56 same | direct 0; closure 0 / 56 | MEASURED |
| Palms_Pack_01 (1,157 MB, 353) | `Content/Palms_Pack_01`; `PalmsPaccb57d20c74ffV3` | LIVE | Bank content. Rights are still open. The AGENTS "3 dirty originals" were unsaved in-editor edits; they are not on disk today (INFERRED). | 353/353 byte-identical; `Staging/ModelBank/BANK_1215_DISPOSITION_MANAGER_REVIEW_2026-09-29.EN.md:19` | direct 5 / 2 / 33; closure 332 / 353 | MEASURED; DOCUMENTED |
| ProceduralBuildingGenerator (684 MB, 774) | `Content/ProceduralBuildingGenerator`; `Procedur82cd1614076dV1` | LIVE | Vendor pack | 774/774 same | direct 7 / 7 / 258; closure 395 / 774 | MEASURED |
| Radar (13 MB, 22) | `Content/Radar`; `Radar7c7a10b0f57dV1` | DEAD | Unreferenced vendor pack (DEAD rests only on "unreferenced"). The "Radar" hits in AssetBankOperator files are a CitySample mesh name, not this pack. | 22/22 byte-identical | direct 0; closure 0 / 22 | MEASURED |
| StarterContent (635 MB, 270) | `Content/StarterContent`; bundled in `ModularC798ab2003378V1` (also an engine template feature pack) | LIVE | **Transitively LIVE:** it feeds `Areas/Gaza*/.../Materials/MI_GeoCityGround` and the Appearance textures. Status §5 proposes excluding it from Git. | 270/270 same | direct 0; closure **37 / 270** | MEASURED |
| Stylized_Egypt (654 MB, 303) | `Content/Stylized_Egypt`; `Stylized9ec755cb81bdV1` | LIVE | Catalog content | 303/303 same | direct 0 / 0 / 21; closure 45 / 303 | MEASURED |
| UtopianCity (1,798 MB, 237) | `Content/UtopianCity`; `UtopianC7adfbf7ad5c3V1` | LIVE | Vendor pack | 237/237 same | direct 1 / 1 / 67; closure 170 / 237 | MEASURED |
| Warehouse_Building (26 MB, 24) | `Content/Warehouse_Building`; `Warehous2fc606d53413V1` | LIVE | Catalog content | 24/24 byte-identical | direct 0 / 0 / 1; closure 23 / 24 | MEASURED |
| WorldBLD downloaded assets (**8,379 MB**, 1,594 files) | `Content/WorldBLD/Assets`; no VaultCache folder (INFERRED: downloaded through the WorldBLD asset library 2026-09-25 to 27) | HISTORICAL | A retained Stage 1 dependency. 0 references from any LIVE root, even through plugin content. Stage1Kit references 24 of these assets. The WorldBLD *plugin* is LIVE (3.13), but this content is not. | `UNREAL_DEPENDENCY_REVIEW_2026-09-29.md:3,10` (keep decision) | direct 0; closure 0 / 1,594 | MEASURED; DOCUMENTED |
| Project tree (7,697 MB, 3,186 files) | `Content/Project/` | LIVE | Mixed. Its subgroups are classified in 3.2 and 3.7 to 3.11. | part 04 (a0) | Contains the roots | MEASURED |
| Python runtime (2 MB, 29 files) | `Content/Python/` | LIVE | 13 sealed `.py` (3.3) and 16 `.pyc` (DEAD, 3.3) | seal 258469e1 | Sealed | MEASURED |
| Developers, LIVE exception | `Content/Developers/USER/HoudiniCityProof/Materials/M_GeoCity_VertexColorPreview` | LIVE | Referenced by the **Rimal live map**. Excluding Developers from Git would break that map. | Rimal map name table; origin `Staging/TrackA_Tests/HoudiniCityProof/GeoCity_visual_fix_UI_2026-09-30/RESULT.md:21` | **Yes** | MEASURED |
| Developers, rest (451 files, 207 MB) | `Content/Developers/USER/**` (`HoudiniCityProof`, `ModelBankProof` incl. H0958 proof copies, `TrackA_T0-T5`, `Collections`; 25 proof/pilot maps; Cook/HDA/proof assets) | HISTORICAL | Track A, pilot and proof history, 2026-09-27 to 10-02. AGENTS: "Keep old Developer evidence as history". | map records in 3.8.B; `UNREAL_DEPENDENCY_REVIEW_2026-09-29.md:9` | No (except the material above) | MEASURED; DOCUMENTED |
| Houdini Engine default folders (68 files, 7 MB) | `Content/HoudiniEngine/{Temp,Bake}`: Temp folders for `B1_probebox`, `B2_labs_osm`, `GeoCity_city_v007`, `..._v007_SurfacePainting_v002`, `...v013...`, `...v014...` (6.7 MB); Bake 28 files, v002-v004, all 10-01 | HISTORICAL | Plugin default temp/bake output from the pilots | Default paths per `Staging/Archive/PreFinalVision_2026-09-29/Guides/BuildSystemGuide_2026-09-27/CORRECTED_PIPELINE_STATUS_EN.md:57`; no LIVE referrer (part 04) | No | MEASURED; DOCUMENTED |
| RoadBLD_Generated presets (<1 MB, 1 file) | `Content/RoadBLD_Generated/Presets` | HISTORICAL | CONFLICT: part 00b = LIVE (RoadBLD preset storage, by role); part 04 = HISTORICAL (measured: only Stage1Kit references it). HISTORICAL chosen on the measured reference. The RoadBLD plugin may write here at run time, which nobody verified (INFERRED). | `UNREAL_DEPENDENCY_REVIEW_2026-09-29.md:10` | No | MEASURED |
| Recovery-world OFPA folders | `Content/__ExternalActors__/Project/Recovery/**` (138, 32 MB), `Content/__ExternalObjects__/Project/Recovery/**` (5) | HISTORICAL | Part of the pre-PermanentBank recovery world (3.10) | part 04 | No | MEASURED |
| Collections (empty) | `Content/Collections` | DEAD | Empty editor folder | `find Content/Collections -type f` = 0 | No | MEASURED |

**Notes.**
- The stray `Content/Untitled*` world and its `__ExternalActors__/__ExternalObjects__` folders are in 3.8.
- **`Content/CitySample*` has no class, because it is not installed.**
  - No such folder exists, so the status §5 exclusion has nothing to act on.
  - City Sample is in VaultCache `CitySample_5.8` and `FabLibrary/City_Sample-4898e707`.
  - The AssetBankOperator plans 346 CitySample candidates (`EXPANSION_SUMMARY.json`). These would land under `/Game/Project/Shared/ModelBank/Supply/`.
  - (MEASURED, part 04 (d).)

**Vendor totals (MEASURED).**
- The 17 VaultCache-backed packs total 13,536 MB.
- 12 packs are LIVE by direct or transitive reference, and 2 more are planned consumers.
- Three packs are fully unreferenced and not planned, 493 MB in total: FantasyRuins, PWL_Light_Manager and Radar.
- The 14 VaultCache-backed packs not named in status §5 hold 12,161 MB.
- No file outside `.uasset`/`.umap` is large: the only non-asset files in Content are 13 `.py` and 16 `.pyc`.

### 3.13 Plugins, Config and project root

**Plugins enabled in `Environmentpipeline.uproject` (MEASURED, part 00b):** ModelingToolsEditorMode, WorldBLD, CityBLD, RoadBLD, TwinBLD, MCPClientToolset, CustomDetailsView, DataflowAgent, HTNPlanner, InterchangeChaosClothAsset, LearningAgents, MVVMToolset, ExampleCustomDataInterface, PhysicsToolsets, AIModuleToolset, AIAssistant, AlembicHairImporter, ConfigSettingsToolset, MLAdapter, UnrealCopilot, UnrealMCP, FastGeoStreaming, WaterAdvanced, WaterExtras.
- **Stale after the window:** SunPosition was added at 14:47:15Z (`Environmentpipeline.uproject:8`, author grep; INFERRED: added for the Reusable Sky task, which `AGENTS.md:7` allows to enable "necessary SunPosition dependency"). A pre-change copy is in `Staging/ReusableSky_2026-10-06/Before/Environmentpipeline.uproject`.

HoudiniEngine is a project plugin (`Plugins/HoudiniEngine`) that is not listed in the `.uproject` array. INFERRED: it is auto-loaded through `EnabledByDefault`; not verified. The engine plugins in the list were not reviewed for use and are not classified.

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Houdini Engine plugin (242 MB) | `Plugins/HoudiniEngine` | LIVE | The official application connection for instantiate/cook/Bake. `Config/DefaultHoudiniEngine.ini`: `UseCustomHoudiniLocation=Project`, empty path. | `AGENTS.md` "Ownership and tools" | Yes (runtime, native HDAs) | DOCUMENTED |
| RoadBLD plugin (4,475 MB) | `Plugins/RoadBLD` | LIVE | The explicitly authorized native road role. Ships Binaries, no Source. Its dependencies include WorldBLD (`RoadBLD.uplugin:96`). | `AGENTS.md`; `geocity_roadbld_*.py`; part 05 fact 2 | Yes (sealed runtime; ~1,330-1,460 `/RoadBLD/` paths per Gaza map) | DOCUMENTED; MEASURED |
| WorldBLD plugin (2,477 MB; 218 MB Binaries, 2 MB Source) | `Plugins/WorldBLD` | LIVE | A required plugin dependency of the LIVE RoadBLD plugin. CONFLICT: part 00b = HISTORICAL (AGENTS "historical retained dependencies"); the author's read of `RoadBLD.uplugin:96` (`"Name": "WorldBLD", "Enabled": true`) makes it LIVE. | author read of `Plugins/RoadBLD/RoadBLD.uplugin:94-98` | Yes (RoadBLD dependency) | MEASURED |
| UnrealCopilot plugin (168 MB) | `Plugins/UnrealCopilot` | LIVE | Operator tooling: `copilot_client.py` calls the UnrealCopilot MCP at 127.0.0.1:19840 (`run_unreal_skill`). Its `Content/Python/.venv/` should be excluded from Git. | PROJECT_STATUS §2 | Yes (operator) | DOCUMENTED |
| UnrealMCP plugin (108 MB) | `Plugins/UnrealMCP` | LIVE | The MCP inspection connection used by chats (127.0.0.1:8000); `capture_mcp.py` uses it | `AGENTS.md` "Ownership and tools" | Yes (operator inspection) | DOCUMENTED |
| CityBLD plugin (2,206 MB) | `Plugins/CityBLD` | HISTORICAL | A retained dependency, not an active work order. Not a RoadBLD dependency (author read of `RoadBLD.uplugin`). Still enabled in the `.uproject`. Ships Binaries only. | `AGENTS.md` preservation rules; `CityBLD.uplugin` dependency list | No | DOCUMENTED; MEASURED |
| TwinBLD plugin (190 MB) | `Plugins/TwinBLD` | HISTORICAL | As CityBLD. It depends on WorldBLD, CityBLD and RoadBLD. Binaries only. | `TwinBLD.uplugin` dependency list | No | DOCUMENTED; MEASURED |
| WorldBLD MCP toolset (335 MB) | `Plugins/WorldBLDMCPToolset` | HISTORICAL | MCP toolset over the WorldBLD family. Binaries only. | `WorldBLDMCPToolset.uplugin` dependency list | No | DOCUMENTED; MEASURED |
| Sealed config files | `Config/DefaultEngine.ini` (ba043fdc), `Config/DefaultRoadBLD.ini` (70338496) | LIVE | Sealed support files. `DefaultRoadBLD.ini` holds the terrain-write policy (see the `DefaultEngine.ini:59-60` comment). | sha = manifest support_files | Re-hashed by the guard | MEASURED |
| Other project config | `Config/DefaultEditor.ini`, `DefaultEditorPerProjectUserSettings.ini`, `DefaultGame.ini`, `DefaultHoudiniEngine.ini`, `DefaultInput.ini` | LIVE | Project configuration. Track all of `Config/`. | part 00b | Yes (editor startup) | MEASURED |
| TwinBLD config | `Config/DefaultTwinBLD.ini` | HISTORICAL | TwinBLD is historical. Keep (harmless). | part 00b | No | MEASURED |
| Project file | `Environmentpipeline.uproject` (1,795 B, changed 14:47:15Z) | LIVE | Lists the enabled plugins. SunPosition added after the window (`:8`). | part 00b; author listing and grep | Yes | MEASURED |
| Existing root Git files (2026-09-27) | `.gitignore`, `.gitattributes` (UP root) | LIVE | `.gitignore` documents that `/Saved/Logs/` holds live bearer tokens and that `/Environmentpipeline/` is a separate clone. `.gitattributes` = `* -text`, then LFS by extension. Merge with these files; do not replace them. | part 05 (d) fact 1 | Input to the Git setup | MEASURED |
| Nested stale Git repo | `Environmentpipeline/` (`.git/`, `.gitattributes` with `* text=auto` only, `README.md`) | DEAD | One-commit repo ("1f92a6a Initial commit", 2026-09-25) with remote `https://github.com/Samorai-Studio/Environmentpipeline.git`. Its README says "This nested folder is not the project entry point". `git status`: README modified. | `Environmentpipeline/README.md:3`; `git log` = 1 commit (part 00b) | No | MEASURED |
| Runtime-asserted log | `Saved/Logs/Environmentpipeline.log` | LIVE | Holds live bearer tokens (BASELINE_REPORT 2026-09-27), so never track it. Sealed code asserts a 2026-10-03 line in it, so it cannot simply be rotated either. | `geocity_roadbld_junctions.py:580-582` (author) | Yes (sealed code, legacy-adoption path) | MEASURED |
| Editor autosaves and downloads | `Saved/Autosaves/` (2.1 GB), `Saved/PersistentDownloadDir/` (3.2 GB), `Saved/Crashes`, per-user `Saved/Config` | HISTORICAL | Editor caches and autosaves; the HDA autosaves are in 3.2.D | part 05 `.gitignore` notes | No | MEASURED |

`DerivedDataCache/`, `Intermediate/`, `Binaries/` and `Plugins/*/Intermediate/` (4.4 GB) are regenerable build caches. They are not classified and are excluded from Git.

### 3.14 Staging top-level entries and Archive manifests

**Count (MEASURED, author listing at about 14:50Z).** Staging had 43 entries, 33 folders and 10 loose `.md` files, before this Consolidation folder existed. Part 05 counted 35 + 8 = 43 at 14:35Z. The total size is about 45.5 GB.

**How a Staging folder counts as LIVE (part 05).** Any one of these is enough:
1. the sealed runtime or launcher reads or writes it;
2. a profile field that the runtime reads points into it (`catalog_receipt`, `workflow_receipt`, `build_state_alias`, `decision_receipt`);
3. the current governance docs name it;
4. work is being written there now.

Provenance-only profile pointers give HISTORICAL with a "pinned" note. Sizes are `du -sm` at about 13:58Z.

**Runtime references (MEASURED).**
- `geocity_editor_action.py:14,26-30` -> `ModelBank/EDITOR_OWNER.txt`, `ManagedSystemsAstra/ASSIGNMENTS.json`, `BANK_ACTIVATION.json`, `BankIntegration/ASSIGNMENT.json`.
- `geocity_roadbld_clip.py:266-271` -> `AppearanceRepair_2026-10-03`.
- `geocity_roadbld_grounding.py:1309` -> `AppearanceRepair_2026-10-03`.
- `geocity_runtime_guard.py:123-182` and `init_unreal.py:13` -> `SystemCompletion`.
- `geocity_bank_workflow.py:119,144,265` -> `ModelBank`.
- `launch_editor.ps1:13,19,20,35,44,52` -> the same folders.

| Item | Path | Class | Duplicates / why dead | Evidence (status line) | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| AppearanceRepair (1,013 MB; 10-03 to 10-04; root 01a0ff41, task2 Astra) | `Staging/AppearanceRepair_2026-10-03/` | LIVE | A runtime write target, plus profile receipts. Inside it, `BeforeNative/` (349 MB) and `BeforeOrdinaryReplacement/` (280 MB) hold old map copies and 154-193 MB HDA_CATALOG_RECEIPT copies (3.15). Must stay at this path, because roads are re-enabled in the next Shujaiya run. | `ASSIGNMENT.json`: `status=Rimal_native_saved_reopened_Shuj_continuation_managed_by_Astra_tasks` | **Yes.** Runtime: `clip.py:266-271`, `grounding.py:1309`. All 3 profiles: FACADE_MATERIALS, INSTANCE_MATERIALS, NATIVE_VARIETY_MEASUREMENTS, GROUND_SHADER_REPAIR_*, ROADBLD_CLIP_* | MEASURED |
| Archive (352 MB; 8 archives) | `Staging/Archive/` | HISTORICAL | Keep; manifests in the table below | archive table | `AGENTS.md:46` lists the archives | MEASURED |
| AssetBankOperator (19,005 MB at 13:58Z; 20.1 GB of cache dirs at 14:19Z; created today; Astra bank-filling operator under manager cc37d4d2) | `Staging/AssetBankOperator_2026-10-06/` | LIVE | Active, and holds the `OWNER=ASSET_BANK_OPERATOR` lease on PID 29900 since 14:14Z.<br>- `OwnedPackChunks/` (9,502 MB, 9,497 `.raw` Epic CDN chunks) is a DUPLICATE of the assembled `OwnedPackSources/` (9,497 MB, 1,691 uassets from 5 packs) once SOURCE_RECEIPT verification passes (INFERRED).<br>- `NativeIntake/phoenix_palms` (1,110 MB, 302 uassets) was being written.<br>- Download route is OPEN for the manager: `stage_owned_packs.py:11,49` fetches packs with the third-party `legendary` client from Epic CDN hosts (`IntakeTools/legendary`). | `EXPANSION_DELIVERY.json` (13:55Z): `native_imports 0, manager_lease_received false, model_candidates 834, source_bytes_verified 9950041957` | Named in `AGENTS.md:7` ("existing Asset Bank editor"). Not in status §2. **Since 14:32:58Z also LIVE by criterion 2:** all three profiles' `decision_receipt` point to `Activation/DECISION.json`, which `geocity_bank_workflow.py:505-507` hash-checks. `Before/` holds the only copies of the survey-time profiles (3.7). | MEASURED; INFERRED |
| BankDepthAudit (26 MB; 10-04) | `Staging/BankDepthAudit_2026-10-04/` | HISTORICAL | Audit report | `REPORT.txt`: "model bank depth audit ... ordinary configuration uses a narrow selection" | No (1 ref, from BankPreparation) | MEASURED |
| BankIntegration (271 MB; 10-03 to 10-05; bank chat 01a1067c) | `Staging/BankIntegration_2026-10-04/` | LIVE | `Before/` 21 MB. Its `ASSIGNMENT.json` is DEAD as an authority but still read (3.5). | `ASSIGNMENT.json`: `status=NATIVE_AUTHORING_PAUSED_EXACT_DIRTY_VENDOR_PACKAGES;84imports/24active preserved`; `RESULT.json`: `ACTIVE_NATIVE_FULL_BANK_INTEGRATION_INCOMPLETE` | **Yes.** `editor_action.py:28` reads `ASSIGNMENT.json`; `launch_editor.ps1:19`; status §2. Until 14:32:58Z the `decision_receipt` `NORMAL_CONFIGURATION_f6fff4f9759af2db.json` (Shujaiya and Rimal) was hash-checked; superseded in-window by `AssetBankOperator_2026-10-06/Activation/DECISION.json`. The folder stays LIVE by criterion 1. | MEASURED |
| BankPreparation (158 MB; 10-04; thread 01a10653) | `Staging/BankPreparation_2026-10-04/` | HISTORICAL | Predecessor input to BankIntegration (38 refs). Holds `BANK_GALLERY.html` (69 MB) and `gallery_check.js` (69 MB). | `RESULT.json`: `nonmodular_measurement_and_source_preparation_delivered_native_import_activation_pending` | No | MEASURED |
| CONTRACT v0.6 approval options (25 KB) | `Staging/CONTRACT_V06_APPROVAL_OPTIONS_2026-09-29.md` | HISTORICAL | Decision aid | "Decision aid only. Nothing below is approved." | No | MEASURED |
| CONTRACT v0.6 decision matrix (13 KB) | `Staging/CONTRACT_V06_DECISION_MATRIX_2026-09-29.md` | HISTORICAL | Decision aid | "All 15 rows remain proposed." | No | MEASURED |
| Current state (36 KB; 10-05) | `Staging/CURRENT_STATE.md` | LIVE | A document of record. Most sections are historical (headings from line 56 on). | text | `AGENTS.md:46`; status §2 | MEASURED |
| Diagnostics (<1 MB; 10-03) | `Staging/Diagnostics_2026-10-03/` | HISTORICAL | Root-cause audit | `ROOT_CAUSE.txt`: "focused current-area root-cause audit ... retained r014" | No | MEASURED |
| GroundPainting (2,334 MB; 09-23 to 10-05; ground chat 01a10883) | `Staging/GroundPainting_2026-10-04/` | LIVE | A tooling dependency. `Images/` 395 MB; `Before/` 165 MB; `Revision_2026-10-05/Before` 317 MB and `SamplerBefore` 448 MB hold byte-identical map copies (3.15). It also contains the DEAD `launch_ground.py` and its pins, and a DUPLICATE `copilot_call.py`. | `RESULT.json`: `finite_ground_task_status=COMPLETE_WITH_REPORTED_VISUAL_LIMITS, authoring_released=True`; `Revision_2026-10-05/RESULT.txt`: "EPIC GROUND SOURCE CHECKPOINT" | **Yes.** The Hybrid scripts and `PLAN_HYBRID.md` use `native_graph_stochastic.py`. The capture tooling uses the camera presets `CAMERAS_Gaza*.json` (MANAGER_HANDOFF §6). | MEASURED |
| HoudiniEngineOutputRepair (2 MB; 10-04) | `Staging/HoudiniEngineOutputRepair_2026-10-04/` | HISTORICAL | Superseded by today's Iran run (map 623aa0c0 -> c409279c). It holds the DEAD `launch_current_area.ps1`. | `RESULT.json`: `status=PERMANENT_ORDINARY_OPERATION_SAVED_REOPENED_REGENERATED`, `release.map_sha256=623aa0c0...` | No | MEASURED |
| HoudiniUnrealDataReport (4 MB; 10-04) | `Staging/HoudiniUnrealDataReport_2026-10-04/` | HISTORICAL | Read-only assessment | "Read only assessment ... transfer works for the saved Iran 4 km area" | No | MEASURED |
| IranBuildingAdaptation (862 MB; 10-04) | `Staging/IranBuildingAdaptation_2026-10-04/` | HISTORICAL | The parked r019/r020 building-logic study; not promoted. Not a duplicate of Iran_4km (which is the area run). Holds 3 `CATALOG.json` files of 220-243 MB. | `ASSIGNMENT.json`: `status=HOUDINI_BUILDING_LOGIC_AND_GEOMETRY_VERIFIED_CONTENT_DEPENDENCIES_OPEN_UNREAL_NOT_RUN` | No (referenced by ManagedSystemsAstra and PipelineSemanticRepair) | MEASURED |
| Iran_4km (1,875 MB; 10-04 to 10-06) | `Staging/Iran_4km_2026-10-04/` | LIVE | 6 timestamped `CATALOG_RECEIPT_<ns>.json` and one `...before_normalized_recook...` copy, 262 MB each (1.57 GB of history). Only `CATALOG_RECEIPT.json` (13:38Z today) is live. Also holds the DEAD `launch.ps1` and `Bootstrap/`, and a DUPLICATE `copilot_call.py`. | `RESULT.json`: `status=generated_saved_reopened`; `HDA_DEFINITION.json` | **Yes,** as of 13:50-14:25Z: the Iran profile's `catalog_receipt`, `workflow_receipt` and `build_state_alias` pointed here, and the `decision_receipt` `NEW_AREA_SCOPE.json` was hash-checked. Superseded in-window: since 14:32:58Z the `decision_receipt` points to `AssetBankOperator_2026-10-06/Activation/DECISION.json`; the other keys were not re-read. MANAGER_HANDOFF §6. | MEASURED |
| Manager handoff (19 KB; 14:10Z) | `Staging/MANAGER_HANDOFF_2026-10-06.md` | LIVE | A document of record | "manager handoff (2026-10-06, ~14:10Z)" | `AGENTS.md:12` governance | MEASURED |
| ManagedAstra (1,561 MB; 10-03 to 10-04; root 01a0ff41) | `Staging/ManagedAstra_2026-10-03/` | HISTORICAL | Holds `ALL40_INTERVALS_...json` (720 MB, the largest file in Staging), two identical AutosaveEvidence maps (bee525f0, 101 MB each), `FAILED_HDA_CATALOG_RECEIPT` (178 MB) and the DEAD `launch_replacement_editor_PREPARED.ps1` | `ASSIGNMENTS.json`: `latest_root_control_20261004.status=READONLY_AUDIT_NATIVE_INSPECTION_PENDING_NO_EDITOR_ACTIVATION` | No runtime use. `AGENTS.md:46` still calls it current (stale pointer). | MEASURED; DOCUMENTED |
| ManagedExecution (19 MB; 10-02 to 10-03; manager 01a0fd40) | `Staging/ManagedExecution_2026-10-02/` | HISTORICAL | **Pinned by profile provenance; keep at path.** | `MANAGER_STATUS.txt`: "The actual r017 repair supersedes this folder's historical r014 ..." | All 3 profiles: `selection_receipt` `Task2/NORMAL_ASSET_CONFIGURATION.json`, `receipt` `Task3/...MATERIAL...`, `scope_extension_receipt` `Task5/...SCOPE...`. The runtime does not read these keys. | MEASURED |
| ManagedSystemsAstra (73 MB; 10-03 to 10-05) | `Staging/ManagedSystemsAstra_2026-10-04/` | LIVE | Lease validation. Holds LIVE `ASSIGNMENTS.json`, the DEAD-but-read `BANK_ACTIVATION.json`, the DEAD `GENERATION_ACTIVATION.json` and `launch_reviewed.ps1`, the DUPLICATE IranSemanticConsumer forks, and HISTORICAL succession records. | `STATUS.txt`: "USER STOP - ALL ENGINEERING STOPPED"; `ASSIGNMENTS.json` `phase=SUCCESSOR_MANAGER_ACTIVE_BANK_NATIVE_PAUSED...` | **Yes.** `editor_action.py:26,30`; `launch_editor.ps1:13,20`; `AGENTS.md:12` | MEASURED |
| ModelBank (11,015 MB; 07-06 to 10-06) | `Staging/ModelBank/` | LIVE | Holds the lease file, the profiles and the ledgers, and is being written by the bank operator now.<br>- `ME/Sources/` (about 5.7 GB): copies of vendor FBX and texture files (INFERRED DUPLICATE, 3.15).<br>- `Candidates/`: 1.2 GB.<br>- Timestamped `HDA_CATALOG_RECEIPT_<ns>.json` history: about 2.8 GB (Shujaiya) and 0.7 GB (Rimal).<br>- `README.md` is stale. | `README.md`: "Shared model bank - current status ... zero assets qualified" (2026-09-29, stale) | **Yes.** `EDITOR_OWNER.txt`; the 3 `AREA_PROFILE.json`; runtime refs above; status §2 | MEASURED |
| ModularBank (9 MB; 10-04; thread 01a10653) | `Staging/ModularBank_2026-10-04/` | HISTORICAL | Blender family-authoring receipts for 2 families. Not a duplicate of ModularConstruction. The kit sources now live in `PE/ModelBank/Modular_2026-10-04`. | `RESULT.json`: `status=Blender authoring complete for two families; native integration pending` | No | MEASURED |
| ModularConstruction (664 MB; 10-03 to 10-06; bank chat 01a1067c/01a10c77) | `Staging/ModularConstruction_2026-10-05/` | LIVE | Registry and pinned receipts.<br>- `Bindings/Before` (108 MB): map copies (3.15).<br>- `Run_20261005/Attempt1-3`: 113-185 MB HDA receipt copies.<br>- `Attempt1/GeoCity_city_v015_PermanentBank.uasset`: f407976c, the only copy. | `EXECUTION.json`: `status=STOPPED_USER_DEADLINE`; `STOP_REPORT_20261005.json`: `STOPPED_REPORT_ONLY` | **Yes.** Gaza profiles: `building_assembly_contract.source_family_registry_ref.path` -> `ContractAudit/Registries/<sha>.json`; `binding_reconciliation_receipt` = `Run_20261005/PROFILE_CHANGE.json`; `repair_queue_ref` = `ROAD_REPAIR_QUEUE.json` | MEASURED |
| NativeUnrealAssetSupply (250 MB; 10-04; supplier 01a1075c) | `Staging/NativeUnrealAssetSupply_2026-10-04/` | HISTORICAL | A supplier delivery. Its role passed to AssetBankOperator, which cites it in 2 files. | `FINAL_REBASE_HANDOFF.json`: `status=REBASED_FROZEN_DATA_READY_FOR_ROOT_BANK_REVIEW` | Only the historical AGENTS "Current assignment" paragraph | MEASURED; INFERRED |
| Operator tombstone (1 MB; 09-27 to 09-29) | `Staging/Operator/` | HISTORICAL | A 2-file tombstone (`README.md` and `STOP`). **Not** a duplicate of `ShujaiyaOrdinaryRun_2026-10-05/Operator/`. The earlier "31/10 references" were substring hits. The only true references are in `EDITOR_OWNER.txt` history and TrackA evidence. | `README.md`: "The file-task operator loop is closed. STOP is retained here intentionally." | No | MEASURED |
| Prerequisite setup receipt | `Staging/PREREQUISITE_SETUP_RECEIPT_2026-09-30.md` | HISTORICAL | Superseded the same day | "Later the same day: ... superseded by GUI connection receipt" | No | MEASURED |
| Project status (12 KB) | `Staging/PROJECT_STATUS_2026-10-06.md` | LIVE | The manager's consolidation status. Corrections are in section 2 of this document. | text | MANAGER_HANDOFF; the mission | MEASURED |
| PaintBank (9 MB; 10-02) | `Staging/PaintBank_2026-10-02/` | HISTORICAL | v013-era surface painting. `FRESH_REOPEN_*.log` are copies of Unreal logs that may contain tokens (unverified). | `AREA_HDA_CATALOG_RECEIPT.json` | No | MEASURED; INFERRED |
| PipelineSemanticRepair (3 MB; 10-04; chat 01a1067b) | `Staging/PipelineSemanticRepair_2026-10-04/` | HISTORICAL | The r019 semantic revision, not promoted | `RESULT.txt`: "ACQUISITION/RULES AND RETAINED EXTERNAL HDA REVISION IMPLEMENTED" | No | MEASURED |
| ProceduralCityRegeneration (273 MB; 10-05) | `Staging/ProceduralCityRegeneration_2026-10-05/` | HISTORICAL | Evidence for the current Shujaiya baseline 4efebdfb. `Before/City/` holds the pre-run map 911cc7ef and a 129 MB catalog receipt. `Before/DiskPackages` holds the 15 Vault-identical MW function copies (3.10). | `Incident.../DECISION_LET_RUN_FINISH.json` (an Astra chat wrote this folder; 9 INSPECT_MODULAR camera actors were saved into the map at 18:54:00Z); `INSPECTION_GUIDE.txt`: 267 new modular buildings | Cited as "History, do not edit" in `PathB_MW/RESEAL.md:64` | MEASURED |
| RepairExecution (196 MB; 10-02 to 10-03) | `Staging/RepairExecution_2026-10-03/` | HISTORICAL | **Pinned by profile provenance; keep at path.** `Before/` 19 MB holds older maps and an HDA (3.2, 3.15). `r015_Shujaiya/HDA_CATALOG_RECEIPT.json` is 162 MB. | `ASSIGNMENT.json`: `status=implemented_saved_reopened` (r017) | All 3 profiles: `implementation_file` `BUILDING_ASSEMBLY_PATCH.py` (LIVE row, 3.3), `ASSEMBLY_CONTRACT.json`, `POLE5_NORMAL_CONFIGURATION.json`, `INSTANCE_MATERIALS.json`. The runtime does not read these keys. | MEASURED |
| RestartReview (32 MB; 10-01 to 10-02) | `Staging/RestartReview_2026-10-01/` | HISTORICAL | The earlier approach, stopped | `PREVIOUS_APPROACH_OUTCOME_AND_STOP.md`: "the requested end result did not work" | No | MEASURED |
| ReturnToPipeline (1 MB; 10-02) | `Staging/ReturnToPipeline_2026-10-02/` | HISTORICAL | Review record | `INDEPENDENT_REVIEW.txt`: "ready for a bounded repair" | Only a historical AGENTS paragraph | MEASURED |
| ReusableSky (<1 MB at the survey; created 14:02Z today; chat 01a1118e) | `Staging/ReusableSky_2026-10-06/` | LIVE | A new parallel task, plan only at the survey. Its ownership record is kept here (`AGENTS.md:9`). After the window, `Before/` gained the Rimal map copies a6961c8e and 1d670c8e and a pre-change `Environmentpipeline.uproject` (about 65 MB; author listing). | `WORK_PLAN.md`: "Status: implementation plan; no native package has been built or placed." | `AGENTS.md:7-9` (Aviv, 2026-10-06) | MEASURED |
| Status and report index | `Staging/STATUS_AND_REPORT_INDEX_2026-09-30.md` | HISTORICAL | 09-30 handoff | "factual handoff for an independent follow-up chat" | No | MEASURED |
| ShujaiyaOrdinaryRun (4,313 MB; 10-02 to 10-06; manager cc37d4d2) | `Staging/ShujaiyaOrdinaryRun_2026-10-05/` | LIVE | Governance of record.<br>- `RunExisting_20261005/Before`: **3,599 MB**, not the ~1.2 GB in status §3 item 8 (3.15).<br>- `S1_Prep/Before` (509 MB): pinned.<br>- `Hybrid_Auto/Before` and `PathB_MW/Before`: pinned rollback sets. | `ASSIGNMENT.json`: `status.state=IRAN_ORDINARY_RUN_PASSED_EDITOR_IDLE` at the survey; since 14:18:18Z `EDITOR_PID29900_LEASED_TO_ASSET_BANK_CHAT_BY_AVIV_HYBRID_WAITS` (`:44`, author grep) | `AGENTS.md:12`; status §2; MANAGER_HANDOFF | MEASURED |
| SystemCompletion (104 MB; 10-02 to 10-06) | `Staging/SystemCompletion_2026-10-04/` | LIVE | Seal and launcher. `Before/` 101 MB. `RESULT.txt` text is stale. | `ASSIGNMENT.json`: `status=CRASH_REPAIRED_PENDING_FRESH_NATIVE_CONFIG_START`; `RESULT.txt`: "ORIGINAL SHUJAIYA ORDINARY OPERATION ACTIVE; DELIVERY NOT YET COMPLETE" | **Yes.** `init_unreal.py:13`; `runtime_guard.py:123-182` (manifest and support files) | MEASURED |
| Toolchain verification | `Staging/TOOLCHAIN_VERIFICATION_2026-09-29.md` | HISTORICAL | Superseded | "Later evidence, 2026-09-30: ... superseded" | No | MEASURED |
| ToolchainChecks (5 MB; 09-25 to 10-02) | `Staging/ToolchainChecks/` | LIVE | A reference: the MCP guide only; the rest is history. Holds `B2_UNTITLED_PRESERVATION_2026-10-01.md`. | n/a | AGENTS "Ownership and tools" cites `MCP_CONNECTIONS_2026-10-02/USAGE_AND_PROJECT_FIT.txt` and `TOOL_GUIDE.html` | MEASURED |
| TrackA_Tests (76 MB; 09-27 to 10-02) | `Staging/TrackA_Tests/` | HISTORICAL | Track A proofs | `README.md`: "Earlier WorldBLD Mission 1-6 tests ... preserved under ../Archive/PreFinalVision_2026-09-29/" | No | MEASURED |
| Unreal dependency review | `Staging/UNREAL_DEPENDENCY_REVIEW_2026-09-29.md` | HISTORICAL | Keep decision for WorldBLD content. `:11` says "The shared Districts and Landscape assets are historical Stage 1 material", which is not true for `M_Landscape_GazaRimal`: all three live maps name it. `:14` sets the precondition for any move or delete (Reference Viewer, controlled reopen). | "keep Unreal Content/, Plugins/ ... in place" | No (its `:14` precondition is adopted in section 5) | MEASURED |
| UnrealConstructionAudit (1 MB; 10-04) | `Staging/UnrealConstructionAudit_2026-10-04/` | HISTORICAL | Audit synthesis | `RESULT.json`: `status=ROOT_READONLY_SYNTHESIS_RECORDED_NATIVE_AUDIT_INCOMPLETE` | No | MEASURED |
| V13ConnectedPreview (4 MB; 10-02) | `Staging/V13ConnectedPreview_2026-10-02/` | HISTORICAL | The v013 build, save and reopen scripts | `V013_FIRST_COOK_FAILED.json` | No | MEASURED |
| Work plan (34 KB; 10-05) | `Staging/WORK_PLAN.md` | LIVE | A document of record. Most sections are historical (headings from line 48 on). | text | `AGENTS.md:46` | MEASURED |
| This review (created about 15:00Z today) | `Staging/Consolidation_2026-10-06/` | LIVE | Holds only this document (`INVENTORY.md`), a proposal for the manager | this file | The manager's consolidation mission | MEASURED |

**The pairs the mission asked about (MEASURED).**
- `Staging/Operator` vs `ShujaiyaOrdinaryRun/Operator`: not a duplicate. The first is a tombstone.
- `Iran_4km` vs `IranBuildingAdaptation`: `Iran_4km` is the live area run; `IranBuildingAdaptation` is a parked Houdini study.
- `ModularBank` vs `ModularConstruction`: `ModularBank` holds historical Blender receipts; `ModularConstruction` holds the registry the live profiles reference.
- Bank* folders: BankIntegration is LIVE; BankPreparation and BankDepthAudit are HISTORICAL.

#### 3.14.B Archive manifests (`Staging/Archive/*`)

| Item | Path | Class | Duplicates / why dead | Evidence (MANIFEST) | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| AppearanceCompletion (6 files) | `Staging/Archive/AppearanceCompletion_2026-10-03/` | HISTORICAL | Active-document snapshot before the r018 reconciliation (AGENTS, CURRENT_STATE, WORK_PLAN) | `MANIFEST.json` `created_utc 2026-10-03T17:38:34Z` | `AGENTS.md:46` | DOCUMENTED |
| ExecutionStart (4) | `Staging/Archive/ExecutionStart_2026-10-02/` | HISTORICAL | `_before` snapshots of AGENTS, WORK_PLAN and CURRENT_STATE, taken before the five-task start | Bare JSON list without a date field; mtime 2026-10-02 20:09 local | `AGENTS.md:46` | DOCUMENTED; INFERRED |
| ManagerPlan (4) | `Staging/Archive/ManagerPlan_2026-10-02/` | HISTORICAL | AGENTS, CURRENT_STATE and WORK_PLAN before the manager-plan rewrite | Bare list; mtime 2026-10-02 19:49 local | `AGENTS.md:46` | INFERRED |
| ManagerReset (1) | `Staging/Archive/ManagerReset_2026-10-01/` | HISTORICAL | `WORK_PLAN_before_reset.md` (10-01 10:13) | **No MANIFEST** | No | MEASURED |
| PreExecutionRevision (8) | `Staging/Archive/PreExecutionRevision_2026-09-30/` | HISTORICAL | Dated AGENTS, CURRENT_STATE and WORK_PLAN snapshots from 09-29/30, plus EDIT_NOTE | **No MANIFEST** | No | MEASURED |
| PreFinalVision (15,606 files, 352 MB) | `Staging/Archive/PreFinalVision_2026-09-29/` | HISTORICAL | Pre-final-vision guides, handoffs, PROJECT_STATUS_2026-09-27, AUTOMATION_LEDGER, GitBaseline_2026-09-27 (incl. `BASELINE_REPORT.md`), WorldBLD Mission 1-6 evidence, Operator_Legacy | `README.md` path map only | Cited as evidence (3.8.B, section 6) | DOCUMENTED |
| RepairCompletion (5) | `Staging/Archive/RepairCompletion_2026-10-03/` | HISTORICAL | Superseded r014 repair-active instruction and status snapshots | MANIFEST `utc 2026-10-03T03:18:29Z` | No | DOCUMENTED |
| ReturnToPipeline (6) | `Staging/Archive/ReturnToPipeline_2026-10-02/` | HISTORICAL | TrackA/TrackB AGENTS, CURRENT_STATE, PERMANENT_STATUS and WORK_PLAN before the return-to-pipeline plan | Bare list; mtime 2026-10-02 18:25 local | `AGENTS.md:46` | INFERRED |

### 3.15 Large binary backups and map/package copies inside Staging

**Totals (MEASURED, part 05, file list at 14:19Z).**
- **Files over 20 MB:** 469 files under Staging, 24.7 GB in total. Most are JSON, not binaries: 74 JSON files over 20 MB hold 10.9 GB, and `*CATALOG*.json` overall is 209 files (9.8 GB).
- **Unreal package copies:** about 1,101 `.uasset`/`.umap` files (about 3.5 GB) outside the bank-operator vendor caches. Vendor packs inside `AssetBankOperator/OwnedPackSources` and `NativeIntake` add another 1,993 uassets (about 10.6 GB).
- **Backup-type folders:** 46 folders named `*Before*`, `Backup*`, `Capture*`, `Images`, `Snapshots` or `Screenshots`, 6,337 MB in total.

#### 3.15.A Backup folders

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| RunExisting pre-run backup (3,599 MB, 990 files) | `Staging/ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/Before/` | HISTORICAL | One backup set; keep it whole. By full hash, 450 packages (1,084 MB) are byte-identical to live Content (all the large Cook `main_geo_HSM` and LayerInfo packages). 499 differ (176 MB; mostly RoadBLD `SM_Clipped_*` and `Bake/*`); "differ" is partly an ambiguous namesake match (INFERRED). It also holds 13 catalog-receipt copies (about 2.3 GB, INFERRED) and the 17d5929a map. | full-hash pass; `BEFORE_MANIFEST.json` | No | MEASURED |
| S1 backup set (509 MB, 21 files) | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/S1_Prep/Before/S1B_20261005T202836Z/` | HISTORICAL | A pinned record. Its Shujaiya map copy equals the live 4efebdfb. Its Rimal copy equals a6961c8e, which was live until 14:52:20Z. Its `M_SurfaceBank_Natural` and both `MI_GeoCityGround` copies matched the live files at the survey. CONFLICT: part 03 = HISTORICAL ("record only"); part 05 = pinned. HISTORICAL with "keep" chosen, because the Hybrid uses its own rollback set (INFERRED). | `ASSIGNMENT.json:51` `s1_backup_set`; `s1_backup_manifest_sha256` = c32afcdb = `S1B/BACKUP_MANIFEST.json` (verified) | Yes (pinned manifest hash in ASSIGNMENT.json) | MEASURED |
| Hybrid rollback set (67 MB, 2 files plus records) | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/Hybrid_Auto/Before/` | LIVE | The current plan's rollback point: profile 1bd89e5b, patch record, and map `L_GazaShujaiya_BankIntegration_4efebdfb_20261006T131001Z.umap` | `Hybrid_Auto/README.md:273,281`; MANAGER_HANDOFF §5.3 | Yes | MEASURED; DOCUMENTED |
| Path B rollback set (67 MB, 3 files) | `Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/PathB_MW/Before/` | LIVE | Profile 1328d5bb (rollback source), map `..._4efebdfb_20261006T002131Z.umap`, and `geocity_landscape_workflow_d1a5d5fd.py` | `Hybrid_Auto/README.md:276`; `RESEAL.md` | Yes (documented rollback chain) | MEASURED; DOCUMENTED |
| GroundPainting images (395 MB, 268) | `Staging/GroundPainting_2026-10-04/Images/` | HISTORICAL | Capture images | part 05 | No | MEASURED |
| AppearanceRepair BeforeNative (349 MB, 8) | `Staging/AppearanceRepair_2026-10-03/BeforeNative/` | HISTORICAL | Old map copies (Shujaiya 61768b8c, Rimal f9b5c919) and an HDA_CATALOG_RECEIPT copy | part 05 | No | MEASURED |
| GroundPainting revision backup (317 MB, 13) | `Staging/GroundPainting_2026-10-04/Revision_2026-10-05/Before/` | HISTORICAL | Holds a6961c8e and 17d5929a map copies | part 05 | No | MEASURED |
| AppearanceRepair BeforeOrdinaryReplacement (280 MB, 8) | `Staging/AppearanceRepair_2026-10-03/BeforeOrdinaryReplacement/` | HISTORICAL | Map fe56a24d and catalog-receipt copies | part 05 | No | MEASURED |
| ProceduralCityRegeneration backup (236 MB, 96) | `Staging/ProceduralCityRegeneration_2026-10-05/Before/` | HISTORICAL | Pre-run map 911cc7ef, a 129 MB receipt, and DiskPackages (3.10) | part 05 | No | MEASURED |
| GroundPainting backup (165 MB, 8) | `Staging/GroundPainting_2026-10-04/Before/` | HISTORICAL | Maps a473338f (Shujaiya) and 2199527f (Rimal) | part 05 | No | MEASURED |
| ModularConstruction bindings backup (108 MB, 5) | `Staging/ModularConstruction_2026-10-05/Bindings/Before/` | HISTORICAL | Holds a6961c8e and 17d5929a map copies and the 357eeac6 HDA copy | part 05 | No | MEASURED |
| SystemCompletion backup (101 MB, 27) | `Staging/SystemCompletion_2026-10-04/Before/` | HISTORICAL | Pre-change backups | part 05 | No | MEASURED |
| GroundPainting sampler backup (448 MB) | `Staging/GroundPainting_2026-10-04/Revision_2026-10-05/SamplerBefore/` | HISTORICAL | Holds a6961c8e and 17d5929a map copies. The name escapes the status `Staging/**/Before/` pattern. | part 05 | No | MEASURED |
| Epic ground revision backups | `Staging/GroundPainting_2026-10-04/.../EpicBefore_R027`, `EpicResidentBefore_R028`, `EpicRimalBefore_R031` | HISTORICAL | Their names escape the status pattern | part 05 (d) fact 5 | No | MEASURED |
| Safe startup config preserve (207 MB) | `Staging/ManagedAstra_2026-10-03/SafeStartupConfigPreserve_20261003T202315598242Z/` | HISTORICAL | Holds the two bee525f0 autosave maps. The name escapes the status pattern. | part 05 | No | MEASURED |
| 34 smaller backup folders (about 48 MB) | `Staging/**/*Before*`, `Backup*`, `Capture*`, `Snapshots`, `Screenshots` | HISTORICAL | Pre-change backups and captures | part 05 | No | MEASURED |

#### 3.15.B Map copies under Staging, compared by content hash (26 `.umap` files; no Iran map copy)

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Shujaiya live-map copies (3 x 65 MB) | `S1_Prep/Before/S1B_20261005T202836Z/Content/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration.umap`; `Stage1_Ground/Hybrid_Auto/Before/L_GazaShujaiya_BankIntegration_4efebdfb_20261006T131001Z.umap`; `Stage1_Ground/PathB_MW/Before/L_GazaShujaiya_BankIntegration_4efebdfb_20261006T002131Z.umap` | DUPLICATE | Byte copies of the LIVE Shujaiya map 4efebdfb (all three sha 4efebdfb0bf6...). They become unique once the Hybrid saves. The Hybrid rollback uses its own copy (`Hybrid_Auto/README.md:281`). CONFLICT on the PathB_MW copy: part 03 = not referenced by LIVE (the Hybrid uses its own copy); part 05 = pinned via `RESEAL.md`. Either way it stays in Keep. | sha256 (parts 03, 04, 05) | Yes: S1B (ASSIGNMENT), Hybrid_Auto (PLAN_HYBRID, MANAGER_HANDOFF §5.3); PathB_MW contested (see CONFLICT) | MEASURED |
| Rimal prior-state copies a6961c8e (5 x 31.7 MB) | `GroundPainting_2026-10-04/Revision_2026-10-05/Before/...`; `.../Revision_2026-10-05/SamplerBefore/...`; `ModularConstruction_2026-10-05/Bindings/Before/...`; `S1_Prep/Before/S1B_20261005T202836Z/...`; `ReusableSky_2026-10-06/Before/L_GazaRimal_BankIntegration_a6961c8e.umap` (added after the window) | HISTORICAL | a6961c8e was the live Rimal map during the survey. It was superseded at 14:52:20Z by 1d670c8e, so these are prior-state copies, no longer DUPLICATEs of LIVE. Keep two: the S1B copy (pinned) and the ReusableSky copy (the Sky task's pre-change backup). The other 3 are redundant. | sha256 (parts 04, 05); reviewer hash of the new map; author listing | S1B copy (pinned manifest); ReusableSky copy (LIVE task folder) | MEASURED |
| Older Shujaiya state 17d5929a (4 x 70.4 MB, 2026-10-04 23:31) | `GroundPainting_2026-10-04/Revision_2026-10-05/{Before,SamplerBefore}/...`; `ModularConstruction_2026-10-05/Bindings/Before/...`; `ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/Before/...` | HISTORICAL | The pre-10-05 state. The 4 copies are byte-identical to each other, so 3 are redundant (part 01 rule: a copy of a non-LIVE item takes its class). Also the stale baseline in `LAUNCH_BASELINES.json`. | sha256 | No | MEASURED |
| Shujaiya autosave evidence bee525f0 (2 x 101 MB) | `ManagedAstra_2026-10-03/SafeStartupConfigPreserve_*/AutosaveEvidence_0.umap` and `.../AutosaveEvidence/Game/.../..._Auto0.umap` | HISTORICAL | The pair is identical, so 1 copy is redundant | sha256 | No | MEASURED |
| Older unique Shujaiya states (6) | 01ca593f (`AppearanceRepair/Before`), 61768b8c (`BeforeNative`), fe56a24d (`BeforeOrdinaryReplacement`), a473338f (`GroundPainting/Before`), 911cc7ef (`ProceduralCityRegeneration/Before/City`), aeb7f747 (`RepairExecution/Before`) | HISTORICAL | One copy each; history | sha256 | No | MEASURED |
| Older unique Rimal states (4) | 984a3906 (`AppearanceRepair/Before`), f9b5c919 (`BeforeNative`), 2199527f (`GroundPainting/Before`), 82635b46 (`RepairExecution/Before`) | HISTORICAL | One copy each; history | sha256 | No | MEASURED |
| Other maps (3) | `RestartReview_2026-10-01/.../BLANK_MAP_BEFORE_SAVE.umap` (49 KB); `S1_Prep/pegasus_listing/LVL_Pegasus...` (12 KB); `TrackA_Tests/.../PRE_SAVE_L_GazaRimal_V7...` (6.3 MB) | HISTORICAL | No live counterpart | sha256 | No | MEASURED |

**No backup of the pre-run Iran map 623aa0c0 exists under Staging** (MEASURED). Only `Operator/IranRun_20261006/` was checked beyond the Content tree.

#### 3.15.C Full-hash result and key asset copies

- **Full-hash result (MEASURED).** Each of the 1,101 Staging package copies was compared with the live Content file of the same name: 530 MATCH (2,526 MB), 554 differ (643 MB) and 17 have no live namesake (315 MB).

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Ground master copy in S1B | `S1_Prep/Before/S1B_.../.../M_SurfaceBank_Natural.uasset` | DUPLICATE | Byte copy of LIVE 70f82e50 (inside the pinned S1B set). 7 older copies differ (549acf58 x2, d7c5d23a x2, 3644dfd0, 28902d63, bea25944); these are HISTORICAL. | sha256 | Pinned set only | MEASURED |
| Area child MI copies in S1B | `S1_Prep/Before/S1B_.../.../MI_GeoCityGround.uasset` (Rimal, Shujaiya) | DUPLICATE | Byte copies of LIVE 99ad6bb8 and 8fb548f8. 9 older copies differ (HISTORICAL). | sha256 | Pinned set only | MEASURED |
| GeoCity normal and mask copies | `Staging/**/T_Sand_01/02_Normal_GeoCity` (5 copies each), `*_Mask_GeoCity` and MOUT `T_*_Mask` (2 copies each), `TEX_MWAM_*` copies | DUPLICATE | Byte copies of LIVE textures (2fbc15e8 / 7212bbc8 and others), about 340 MB of redundant bytes, all inside backup sets | sha256 | No | MEASURED |
| Older catalog copy | `Staging/RepairExecution_2026-10-03/Before/...DT_EnvironmentBank_v4...` (6df8acee) | HISTORICAL | An older catalog state; the live one is f763b072 | sha256 | No | MEASURED |

The HDA source and native copies are in 3.2.D.

#### 3.15.D Large JSON copies and other duplicates

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| RunExisting catalog-receipt copies (12 x 162-193 MB, plus one unsuffixed 178 MB copy; about 2.3 GB) | `Staging/ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/Before/Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/HDA_CATALOG_RECEIPT_<ns>.json` | HISTORICAL | Each equals its `Staging/ModelBank/...` original. Copies of HISTORICAL timestamped receipts. Compared by name, size and mtime only, not hashed. | part 05 (b) | No | INFERRED |
| Attempt and City catalog-receipt copies | `Staging/ModularConstruction_2026-10-05/Run_20261005/Attempt1-3/` (185, 113, 129 MB); `Staging/ProceduralCityRegeneration_2026-10-05/Before/City/HDA_CATALOG_RECEIPT.json` (129 MB) | HISTORICAL | Equal ModelBank `_1791215366...`, `_1791216458...` and `_1791225807...` (by name, size, mtime) | part 05 (b) | No | INFERRED |
| AppearanceRepair catalog-receipt copies (154-193 MB) | `Staging/AppearanceRepair_2026-10-03/{BeforeNative,BeforeOrdinaryReplacement}/HDA_CATALOG_RECEIPT*.json` | HISTORICAL | Equal the ModelBank `_<ns>` files of the same time (by name, size, mtime) | part 05 (b) | No | INFERRED |
| Largest JSON in Staging (720 MB) | `Staging/ManagedAstra_2026-10-03/.../ALL40_INTERVALS_...json` (and `TASK2_ALL40_POST_CLIP_GAPS_*.json`) | HISTORICAL | Task2 road-clip interval evidence | part 05 | No | MEASURED |
| Failed HDA catalog receipt (178 MB) | `Staging/ManagedAstra_2026-10-03/.../FAILED_HDA_CATALOG_RECEIPT*.json` | DEAD | The filename says it failed. Keep as evidence. | filename | No | MEASURED |
| Iran adaptation catalogs (3 x 220-243 MB) | `Staging/IranBuildingAdaptation_2026-10-04/**/CATALOG.json` | HISTORICAL | Catalogs of the parked r019/r020 study | part 05 | No | MEASURED |
| Bank gallery files (2 x 69 MB) | `Staging/BankPreparation_2026-10-04/BANK_GALLERY.html`, `gallery_check.js` | HISTORICAL | Large text files | part 05 | No | MEASURED |
| Raw CDN download chunks (9,502 MB, 9,497 files) | `Staging/AssetBankOperator_2026-10-06/OwnedPackChunks/` | DUPLICATE | Equivalent to the assembled `OwnedPackSources/` once the SOURCE_RECEIPT verification passes (INFERRED, not proved). Owned by the active operator. | `stage_owned_packs.py` | Only by the operator's own `stage_owned_packs.py`; not by the runtime or profiles | INFERRED |
| Model-bank source copies (about 5.7 GB) | `Staging/ModelBank/ME/Sources/` | DUPLICATE | Copies of vendor FBX and texture files whose origin, `.../GIS_WorldBLD/SourceData/ModelBanks_Archive/Unreal_Model_Library_2026-09-24` (33 GB), still exists. `MANIFEST_ME.csv` records each sha256 (INFERRED duplicate). H0013 sources appear here (hold; mention only). | part 05 (b) | No runtime or profile reference | INFERRED |

The timestamped receipt histories in ModelBank and Iran_4km are in 3.7. The 170 MB r016 receipt in PE is in 3.2.A.

### 3.16 Pipeline Environment root (`PE`, 9,936 MB, 8,399 files at 14:21Z)

`PE/Houdini` (363 MB) is classified file by file in 3.2: the v015 PermanentBank (217 MB) and 4km (20 MB) folders, and about 125 MB of legacy and proof folders.

| Item | Path | Class | Duplicates / why dead | Evidence | Referenced by LIVE? | Label |
|---|---|---|---|---|---|---|
| Modular kit sources (7,513 MB) | `PE/ModelBank/Modular_2026-10-04/` | LIVE | Blender and Houdini sources of the modular kit. Holds the v003/v004 INTEGRATION_RECEIPTs and the `Integration/Before/` natives (2358c514 LIVE, 1de0e6fe HISTORICAL; 3.2.D). Largest files: H0017_Modular.blend 263 MB, H0021 .blend 215 MB, H0019 168 MB, H0018 153 MB, ModularFamilies_Assembly/Library .blend 79 MB each; H0014 Variant_1_3/1_2/1_1 `.bgeo.sc` 205/165/125 MB. | part 05 (c); part 01 | Yes (receipts, B2 rollback) | MEASURED |
| Blender auto-backups (1,118 MB) | `PE/ModelBank/Modular_2026-10-04/**/*.blend1` (e.g. H0017 268 MB, H0021 216 MB, H0019 167 MB, H0018 152 MB) | HISTORICAL | Each holds the previous save state of a `.blend`, not a byte copy of it. Keep on disk; ignore in Git. | part 05 (c) | No | MEASURED |
| Prepared bank sources (364 MB) | `PE/ModelBank/Prepared_2026-10-04/` | LIVE | Source side of the prepared bank content (INFERRED from the name and part 05's "Source" label) | part 05 (c) | INFERRED yes (bank preparation) | INFERRED |
| GazaShujaiya source package | `PE/SourceData/GazaShujaiya/city_source_v1.json` (db5c0bce) and its files (OSM 379 KB, DSM 8.8 KB, control points 2.7 KB) | LIVE | Profile `"source"`. `files[0..2].sha256` = 54374986..., f2b4df9b..., 305a6ec0...; `accepted_source_manifest_sha256` = e1cbd16f... | part 05 (c) | Yes (Shujaiya profile) | MEASURED |
| GazaRimal source package | `PE/SourceData/GazaRimal/city_source_v1.json` (dbcfcb2e) and its files (296 KB, 7 KB, 2.8 KB); `GazaRimal/acquisitions/` (92 MB of provenance) | LIVE | Profile `"source"`. `files[0..2]` = f1c6cf0e..., a8230ea4..., 68c7a3ed...; `accepted_source_manifest_sha256` = b4ec6fcb... | part 05 (c) | Yes (Rimal profile) | MEASURED |
| Iran source package | `PE/SourceData/Iran_38196167_46086167_4km/acquisitions/78b3266d.../20261004T085304Z_65213cc1/city_source_v1.json` (c54a814b) and its files (121 KB, 11 KB, 2.8 KB) | LIVE | Profile `"source"`. `files[0..2]` = f34515c3..., 076c7203..., 50fcae32...; `source_manifest_sha256` = 07091a7d... | part 05 (c) | Yes (Iran profile) | MEASURED |
| Iran semantic consumer_v2 package | `PE/SourceData/Iran_38196167_46086167_4km/...` consumer_v2 (849cf4ce, parent c54a814b) | HISTORICAL | Input of the parked r019/r020 semantic route. The profile does not use it. | part 05 (c) | No | MEASURED |
| Redundant DEM tile copies (4 x 27.6 MB) | Copernicus N31 E034 tile, d157903d: `SourceData/Acquisition/tile_cache/...`, 2 x `GazaRimal/acquisitions/.../elevation/tiles/...`, `GazaRimal/elevation/copdem_N31_E034.tif`, `Reference/GazaRimal_Input_20230101/copdem_N31_E034.tif` (5 copies; 110 MB redundant) | DUPLICATE | Byte-identical copies of a LIVE source input. Each path is recorded in a manifest (`tile_cache/Copernicus_DSM_COG_10_N31_00_E034_00_DEM.json`, both `GazaRimal/acquisitions/.../manifest.json`, `GazaRimal/manifest.json`, `GazaShujaiya/manifest.json`), so keep them on disk and exclude only the cache from Git. | sha256; grep (part 05) | Yes (by manifests) | MEASURED |
| Acquisition cache (33 MB) | `PE/SourceData/Acquisition/tile_cache/` | DUPLICATE | A re-downloadable cache holding one of the DEM copies above | part 05 (c) | Recorded in manifests | MEASURED |
| Reference input (121 MB) | `PE/Reference/GazaRimal_Input_20230101/` (`israel-and-palestine-230101.osm.pbf` 92 MB, a DEM copy) | HISTORICAL | Archive/reference input from the 09-2x Rimal build | part 05 (c) | No | MEASURED |
| PE archive (729 MB) | `PE/Archive/PreFinalVision_2026-09-29/` (728 MB, incl. Restored_Unsorted terrain references: Terrain-Decorator `.asset` 76/55/51 MB; `deliot2019.pdf` 53 MB x3) and `PE/Archive/PreExecutionRevision_2026-09-30/` | HISTORICAL | Already archived. The three identical PDFs are internal copies of a historical file. | part 05 (c) | No | MEASURED |
| Existing PE repository (685 MB) | `PE/.git` (one commit `dfb49ef` "Baseline: Pipeline Environment on-disk state, 2026-09-27"; 681 MB LFS objects); `PE/.gitignore` (only `__pycache__/`, `*.pyc`); `PE/.gitattributes` (byte-identical to the Unreal root's) | LIVE | Continue this repo; do not create a new one. Working tree: 702 deleted, 8 modified, 44 untracked (INFERRED: the 09-29 archive moves and all work since 09-27 are uncommitted). | `git --no-optional-locks status` (part 05) | Proposed Git base (section 6) | MEASURED |
| Track B contract draft (65 KB) | `PE/CONTRACT.md` (v0.6) | HISTORICAL | DRAFT. AGENTS: "CONTRACT.md v0.6 remains DRAFT; old box/checklist stages do not create new prerequisites". | `AGENTS.md` preservation rules | No | DOCUMENTED |

**Not reviewed:** `PE/AGENTS.md`, `PE/AREA.md`, `PE/Handoff/` and `PE/Research/` (all small). They are not classified.

## 4. Risks observed

These risks are outside the classification, but the manager needs to know them.

1. **The lease was free while an editor was open.**
   - From 13:39:07Z to 14:14:05Z, the last lease line was `OWNER=NONE` while PID 29900 was open on the Iran map (MEASURED).
   - In that state, any menu click self-issues `OWNER=GEOCITY_MENU` and regenerates (`geocity_editor_action.py:243-246`, MEASURED code). `PLAN_PROPOSAL.md:119` says never to run the menu under OWNER=NONE (DOCUMENTED).
   - The 14:14:05Z `OWNER=ASSET_BANK_OPERATOR` lease superseded this state (MEASURED). The same pattern returns whenever an editor stays open after a release to NONE (INFERRED).
2. **Unpinned scripts can act on the live editor.**
   - `Operator/iran_generate.py` (96bd67af) dispatches `generate_current_area()` and asserts PID 29900, which is still alive. It is unpinned (MEASURED). A rerun would dispatch a generation in the editor that the bank operator now holds (INFERRED).
   - `Operator/copilot_client.py` executes every operator script, and `probe_state.py` and `IranRun_20261006/capture_mcp.py` touch the live editor. All three are unpinned (MEASURED).
3. **The Iran new-area launcher fails late.** `Staging/Iran_4km_2026-10-04/launch.ps1` checks only OWNER=NONE and that no editor is running. It would start an editor and append an `OWNER=CODEX_NEW_AREA` lease (line 18) before its bootstrap fails at `new_area_bootstrap.py:34` (the map exists) (MEASURED code; INFERRED sequence).
4. **v004 has never been cooked.**
   - The native 1 km HDA embeds v004, which has never been cooked into a saved area (MEASURED/DOCUMENTED).
   - The HDA is outside the seal, and the profiles carry no HDA hash. The next Gaza regeneration therefore runs v004 silently (MEASURED: seal contents and `geocity_bank_workflow.py:1020`; "silently" INFERRED).
   - The only copy of the B2 native is a file in `PE/ModelBank/.../Integration/Before/` that looks like a routine backup (MEASURED).
5. **GazaShujaiya cannot be regenerated.**
   - The profile names the absent `MI_GeoCityGround_Auto` and `M_GeoCityAuto` (MEASURED).
   - `geocity_bank_workflow.py:650` asserts the Landscape material equals the profile value (MEASURED). A regeneration attempt is therefore expected to fail mid-run (INFERRED).
6. **Both scripted rollbacks are unclean (MEASURED).**
   - `hybrid_profile_patch.py --rollback` restores 1bd89e5b, which points at the absent `MI_GeoCityGround_MW`.
   - `pathb_profile_patch.py --rollback` restores 1328d5bb, which turns grass back on (Aviv wants none) and reverts the registry ref from 8d8622b2 to a39dbbb9.
   - A Natural fallback needs a manager-written leaf patch.
   - Both rollback sources were patched against the survey-time profile 4174a627. That file now exists only in `AssetBankOperator_2026-10-06/Before/`, because the live profile is f722381f since 14:32:58Z (MEASURED by the reviewer; author listing). Any rollback must first be re-based on the bank operator's change (INFERRED).
7. **A runtime assertion depends on a log file.**
   - `geocity_roadbld_junctions.py:580-582` asserts a 2026-10-03 line in `Saved/Logs/Environmentpipeline.log`. That log is token-bearing and excluded from Git (MEASURED).
   - A fresh clone or a log rotation fails this assertion whenever the legacy-adoption path runs (INFERRED).
8. **The bank operator's download route is an open question.**
   - `Staging/AssetBankOperator_2026-10-06/stage_owned_packs.py:11,49` fetches owned packs with the third-party `legendary` client from Epic CDN hosts (`IntakeTools/legendary`) (MEASURED code).
   - Whether this route is acceptable under the Epic/Fab terms and the project's tool rules is not decided (INFERRED; open question 7).
   - Relevant rules: Windows tools must be started from PowerShell (DOCUMENTED, AGENTS "Ownership and tools"). AGENTS also says not to add a generator bridge, alternate city generator or PCG migration "by implication", which is not exactly the same as an unreviewed download tool (INFERRED).
9. **Some paths exceed 260 characters.**
   - The project has paths over 260 characters. The first hash pass failed on a `RunExisting_20261005/Before/.../Cook/..._HSM.uasset` path until a `\\?\` prefix was used. A Git test also warned "Filename too long" on the S1B path (MEASURED).
   - Any repo needs `git config core.longpaths true`. Windows tools that move these folders may fail silently (INFERRED).
10. **AGENTS.md contradicts itself (MEASURED).**
    - The parallel-editor rule (line 5) conflicts with "One editor writer at a time" (line 12).
    - The seal is named as 3cd33b15 on line 12 but is 258469e1.
    - Under the parallel rule, `EDITOR_OWNER.txt` remains a single-writer log read by sealed code, while the Sky task keeps its record elsewhere (`AGENTS.md:9`). A Generate in the Sky editor would still read the bank operator's lease line (INFERRED).
11. **Live-read authority files.**
    - `BANK_ACTIVATION.json` and `BankIntegration_2026-10-04/ASSIGNMENT.json` are read by sealed code. Moving them makes the bank branch throw instead of refuse.
    - `ASSIGNMENTS.json` is re-read on every Generate (`geocity_editor_action.py:26`), so editing it while an editor is open changes that editor's behaviour at once.
    - (MEASURED code; INFERRED effect.)
12. **No rollback copy of the previous Iran map.** No Staging copy of 623aa0c0 exists. If today's Iran re-save (c409279c) has to be undone, no on-disk map backup was found (MEASURED; only `Operator/IranRun_20261006/` was checked beyond Content).
13. **Token-bearing log copies.** `Staging/PaintBank_2026-10-02/FRESH_REOPEN_*.log` and other Unreal log copies under Staging may contain bearer tokens. Scan them before any push (INFERRED; unverified).
14. **Unreachable content is owned by others.** Cook folders, stale clip runs, LayerInfos and Bake leftovers may be listed as prior outputs in run ledgers that were not read. Hand cleanup could break the lifecycle's replace/cleanup step (INFERRED).
15. **A ledger was read once (disclosure).** `EDITOR_CURRENT_STATE.json` was opened read-only once at about 14:18Z, during the bank lease. The bank operator should check for access-denied errors between 14:10Z and 14:20Z (MEASURED event; impact unknown).
16. **The Hybrid args are stale.**
    - All 8 `Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/Hybrid_Auto/Args/HYBRID_ARGS_*.json` pin `profile_sha256` 4174a627 (MEASURED, author grep). The live Shujaiya profile is f722381f since 14:32:58Z (MEASURED by the reviewer).
    - A Hybrid step that gates on the profile hash would refuse to run. A step that does not gate would patch a profile it was not reviewed against (INFERRED).
    - The args, and the `hybrid_profile_patch.py` before/after hashes, need re-pinning after the bank operator's change is reviewed (INFERRED).
17. **Concurrent writers outside one lease.**
    - Inside the window the catalog and all three profiles changed under the bank lease (MEASURED).
    - After the window the Rimal map and `Environmentpipeline.uproject` changed, apparently from the Sky task (MEASURED change; author INFERRED).
    - A second editor (PID 5288) was running at about 15:25Z (MEASURED).
    - Any consolidation step, and any regeneration, must re-hash its inputs first, because the parallel-editor rule (`AGENTS.md:5`) now permits these concurrent changes (INFERRED).

## 5. Proposed keep, archive and delete lists (PROPOSAL ONLY; the manager decides)

**Labels for this section.**
- The facts in these lists are carried over from section 3, which gives their labels and evidence.
- Sizes are MEASURED (parts 00, 01, 04, 05).
- The proposals themselves (keep, archive, delete, preconditions) are INFERRED recommendations.

**Preconditions for every move or delete (DOCUMENTED and adopted from `Staging/UNREAL_DEPENDENCY_REVIEW_2026-09-29.md:14` and part 04):**
- a Reference Viewer / Asset Registry check;
- a controlled editor reopen with the redirector results;
- one writer per package, under a manager lease;
- the bank lease on PID 29900 has been released;
- the Content reference closure (Appendix B) has been re-run after the release.

Never Save All. The holds H0013, H0907, H0051, H0958 and H0094 and the 87 unvalidated road candidates appear only in the Keep list.

### 5.1 Keep in place

Label note: rows inherit the label of the section 3 row they cite. Sizes are MEASURED. The keep decision is an INFERRED recommendation.

| Path | Size | Reason | Precondition |
|---|---|---|---|
| Every row classed LIVE in section 3 | n/a | Used by the sealed runtime or the current plan | n/a |
| Holds H0013, H0907, H0051, H0958, H0094 (wherever they are recorded) and the 87 unvalidated road candidates | n/a | Mission and AGENTS rule; untouched | Never moved by this proposal |
| `Content/Project/Shared/Bank_ME/` (v1) | 123 MB | DUPLICATE, but it holds same-named copies of H0013/H0907/H0051/H0094 | Hold policy decides (open question) |
| `Content/Project/Shared/Bank_ME_v2/` | 0.2 MB | Holds `SM_H0958_CoconutPalm` | Hold policy |
| `Content/Project/Shared/ModelBank/Prepared/Modular/H0013/Procedural_v002` | 9 pkgs | DEAD candidate, but it belongs to hold H0013 | Hold policy |
| `Content/Developers/USER/ModelBankProof/H0958_MaterialRepair_20260929/` (`SM_H0958_CoconutPalm_Proof`, `M_H0958_Leaf_Proof`) | small | Proof assets of hold H0958. Excluded from the Developers archive row in 5.2. | Hold policy |
| `Staging/ModelBank/ME/Sources/` | about 5.7 GB | INFERRED duplicate of the external library, but it holds H0013 sources (hold). Excluded from the archive list. | Hold policy; owner only; verify `MANIFEST_ME.csv` against the origin before any later move |
| Clip run `Content/Project/Areas/GazaShujaiya/RoadBLD/ClippedGeometry/20261003T203730573110_212401627821` | 87 uassets | Referenced by the Shujaiya map; the reviewer identifies it as the 87 unvalidated road candidates. Excluded from every lifecycle cleanup. | Never touched by this proposal |
| `Staging/AssetBankOperator_2026-10-06/Before/AREA_PROFILE_*.json` | about 5.7 MB | The only copies of the survey-time profiles 4174a627 / 492b9ac5 / 004ec07d, the rollback base | Owner (bank operator) and manager |
| `PE/ModelBank/Modular_2026-10-04/ProceduralFamilies_Additional20/Integration/Before/` (the 2358c514 native and the pre-v004 profiles) | about 0.6 MB plus profiles | The only copy of the ratified B2 native, and its rollback partners | Do not archive it as "just a backup" |
| `PE/ModelBank/Modular_2026-10-04/ProceduralFamilies/Integration/Before/` (1de0e6fe) | 0.5 MB | The only copy of the v002 native | n/a |
| `Staging/ModularConstruction_2026-10-05/Run_20261005/Before/...uasset` (357eeac6) and `.../Attempt1/...uasset` (f407976c) | 1 MB | The only native copies of r018 and of the first-ratified v001 | n/a |
| `PB` root hdalc, module and receipt; the `PB/revisions/20261005_*_v003/` and `_v004/` folders; the `4K` root | n/a | Embed and re-import sources; the base of every fork | Register v003/v004 with a REVISION.json (manager) |
| `4K/revisions/...r019...` and `...121230..._r020...` | about 2 MB | DEAD (parked), but the only copies of the semantic-palette and use-aware building logic | Keep together |
| All `*/backup/*_bakN.hdalc` (361 files in PE/Houdini and Staging) | about 40 MB | **292 of 361 have no copy anywhere else**, neither standalone nor embedded in the 9 native snapshots (part 01). Examples: PB bak61/bak62 (the only r017-era states), 4K bak1-11, r020 bak2/4/5/8/9/11/12, v003 bak1/2/5/6/9/12/15, v004 bak1/4. | Keep on disk; exclude from Git |
| `Staging/ModularConstruction_2026-10-05/ContractAudit/Registries/a39dbbb9...`, `b2e1876b...` | small | The v003 registries, needed for any B2 rollback | n/a |
| `Staging/ManagedSystemsAstra_2026-10-04/BANK_ACTIVATION.json`, `Staging/BankIntegration_2026-10-04/ASSIGNMENT.json` | small | DEAD as authorities, but still read by sealed code | Re-issue under cc37d4d2, or leave as refused (manager) |
| `Staging/RepairExecution_2026-10-03/BUILDING_ASSEMBLY_PATCH.py` and the whole `RepairExecution_2026-10-03/` and `ManagedExecution_2026-10-02/` folders | 196 MB, 19 MB | Profile provenance points there | n/a |
| `Staging/AppearanceRepair_2026-10-03/` | 1,013 MB | Sealed code writes there (`clip.py:266-271`, `grounding.py:1309`) | Its bulky `BeforeNative`/`BeforeOrdinaryReplacement` may move (5.2) only if the folder path itself stays |
| `PathB_MW/TINT_PRESETS.json`, `PathB_MW/pathb_profile_patch.py`, `PathB_MW/Before/` (whole), `S1_Prep/AstraMWInventory/native_inventory_complete.json`, `GroundPainting_2026-10-04/native_graph_stochastic.py` | small, 67 MB | LIVE Hybrid inputs and rollback tools inside superseded folders | README banners only |
| `Stage1_Ground/Hybrid_Auto/Before/` (whole) | 67 MB | The current plan's rollback set (profile 1bd89e5b, map 4efebdfb) | n/a |
| `Stage1_Ground/S1_Prep/Before/S1B_20261005T202836Z/` | 509 MB | `BACKUP_MANIFEST.json` is pinned (c32afcdb) in ASSIGNMENT.json | Keep its binaries out of Git |
| `/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround` | small | Map rollback target until `RATIFICATION_B3_HYBRID.json` exists | n/a |
| `/Game/Developers/USER/HoudiniCityProof/Materials/M_GeoCity_VertexColorPreview` | small | The Rimal live map references it | It could move into `/Game/Project/Shared/` with a redirector fix-up in a leased editor |
| `Content/StarterContent`, `Content/MWLandscapeAutoMaterial`, `Content/MOUT_Arabian`, `Content/Palms_Pack_01` and the other packs classed LIVE | 13.0 GB | LIVE vendor dependencies | Git option A or B (section 6) |
| `Plugins/WorldBLD` (with RoadBLD) | 2,477 MB | Required dependency of RoadBLD (`RoadBLD.uplugin:96`) | n/a |
| `Content/WorldBLD/Assets` | 8,379 MB | Keep decision (`UNREAL_DEPENDENCY_REVIEW_2026-09-29.md:3,10`); Stage1Kit uses 24 assets; no VaultCache backing | Git decision (LFS or exclude) is open |
| `Staging/ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/Before/` | 3,599 MB | One coherent backup set. 176 MB of it is unique pre-run Bake and clip state. Part 01 proposed deleting its 3 SurfacePainting HDA byte copies; part 05 recommends keeping the set whole. **Recommendation: keep whole** (CONFLICT noted). | It may move as a whole to a `Backups/` root (5.2) |
| Lifecycle-owned outputs: the Cook folders (1,921 MB), the 628 stale ClippedGeometry packages, the 72 stale LayerInfos, the 7 Bake leftovers | about 2.0 GB | DEAD, but possibly recorded in the unread ledgers. The 87-candidate clip run `20261003T203730573110_212401627821` is not one of them (row above). | **Owner only** (see 5.3) |
| `Saved/Logs/Environmentpipeline.log` | n/a | Asserted by sealed code | Never track it; do not rotate it until the assertion is resolved |
| `PE/SourceData/**` including the 5 DEM copies | 161 MB | Each DEM path is recorded in a manifest | Exclude only `tile_cache/` from Git |
| `PE/ModelBank/Modular_2026-10-04/**/*.blend1` | 1,118 MB | Previous-save states, not byte copies | Exclude from Git |
| `PE/Houdini/CityProof/` | small | README: keep in place, because path behaviour after a move is untested | n/a |

### 5.2 Archive (move under `Staging/Archive/<name>/MANIFEST.json` or a dated `Backups/` root outside the repo, with a hash MANIFEST)

Label note: rows inherit the label of the section 3 row they cite. Sizes are MEASURED. The archive decision is an INFERRED recommendation.

| Path | Size | Reason | Precondition |
|---|---|---|---|
| `Staging/ManagedSystemsAstra_2026-10-04/GENERATION_ACTIVATION.json`, `STATUS.txt`, `ManagementTransfer/`, the `MODULAR_*`, `DirtyOriginals_*`, `INSPECTION_*`, `OWNERSHIP_REPAIR_*`, `WHOLE_H0017_*`, `LANDSCAPE_DIAGNOSTIC_*` records, `CONTINUATION_MANIFEST.json` | small | DEAD or HISTORICAL authorities with no runtime reader | Editor closed. Leave `ASSIGNMENTS.json` and `BANK_ACTIVATION.json` in place. |
| DEAD launchers: `HoudiniEngineOutputRepair_2026-10-04/launch_current_area.ps1`; `GroundPainting_2026-10-04/launch_ground.py` (+ `STARTUP_REVIEWED_PINS.json`, `LAUNCH_BASELINES.json`); `BankIntegration_2026-10-04/ModularNative_2026-10-05/launch_modular_editor.ps1` (+2 Handoffs copies); `ManagedAstra_2026-10-03/launch_replacement_editor_PREPARED.ps1` (+ `RecoveryBootstrap/`); `ManagedSystemsAstra_2026-10-04/Task4_Integration/Continuation/launch_reviewed.ps1` | small | Each fails its own gate (3.4) | Record each move in a MANIFEST |
| **Quarantine first:** `Staging/Iran_4km_2026-10-04/launch.ps1` (+ `Bootstrap/`), `Operator/iran_generate.py` | small | Runnable hazards (section 4, items 2 and 3) | Rename or quarantine with a MANIFEST. The `Iran_4km` folder itself stays LIVE. |
| `PE/Houdini` legacy folders v001-v014 and pilots (not CityProof); `PB/revisions/r001-r016` | about 125 MB, about 200 MB | Superseded generator states | A reference check. Path behaviour after a move is untested (README). |
| `4K/revisions/20261004T121206056541Z_r020_use_aware_buildings/` (orphan first r020 start) | about 1 MB | DEAD (no receipt). Its hdalc 7d7661f0 has no other copy, and its `backup/` bak1 falls under the keep rule for unique backups, so archive rather than delete. Only its module is a byte copy (of 12ec4696 in the receipted r020 `authoring_history`). | Archive as one folder with the r019/r020 group; a MANIFEST |
| `Content/Project/Shared/Recovery/ProceduralCity_20261005/` (15 DUPLICATE re-saves) | 0.7 MB | Unreferenced renamed copies. **Not byte-exact**, so archive, not delete. The byte-exact originals stay in VaultCache and in `ProceduralCityRegeneration_2026-10-05/Before/DiskPackages/` (with t3d and `DIRTY_MATERIAL_COMPARISON.json`). | Re-run reference check 3.10.B command 2 at that time; editor closed |
| `Content/Project/Recovery/BeforePermanentBank_20261002` (+ OFPA, 32 MB) | 32 MB | HISTORICAL preservation snapshot, unreferenced | Manager decision; reference check |
| SurfacePainting v002 chain: `L_GazaRimal_SurfacePainting_20261002.umap`, `BakedSurfacePainting/*`, `GazaRimal/LayerInfos/*`, HDA v007_SP_v002, `M_StarterSurfaceBank`, `MI_StarterSurfaceBank_Default` | about 7.5 MB | A closed historical chain | Archive as a group |
| AllLayers/v014 chain (`M/MI_SurfaceBank_AllLayers`, HDA v014) with the Developer map `L_GazaRimal_V13_ColorsModels_20261002`; HDA v013; `Resident4K/T_Sand_01_Albedo_GeoCityResident4K` | about 42 MB | Historical; v013 and Resident4K have 0 referrers | Decide the V13 map together with its chain |
| Developer proof HDAs and maps (`Content/Developers/USER/**`, except `M_GeoCity_VertexColorPreview` and `ModelBankProof/H0958_MaterialRepair_20260929/`, the hold H0958 proof assets kept in 5.1) | about 207 MB | Historical proofs. AGENTS: keep old Developer evidence as history. | Optional. Moving them within Content needs a leased editor. |
| `Content/HoudiniEngine/{Temp,Bake}` | 7 MB | Pilot leftovers | Reference check (part 01 did not run one; part 04 found no LIVE referrer) |
| IranSemanticConsumer forks (Task1 and Task3); `PathB_MW/patched/` and its predicted manifest | small | Unpromoted DUPLICATE forks | Or promote the IranSemanticConsumer forks through review and reseal (manager) |
| `GroundPainting_2026-10-04/copilot_call.py`, `Iran_4km_2026-10-04/copilot_call.py` | small | Parallel MCP clients | Mark historical; HISTORICAL scripts cite them |
| Bulk backup sets: `RunExisting_20261005/Before` (as one set), `GroundPainting/Revision_2026-10-05/SamplerBefore` (448 MB), `AppearanceRepair/BeforeNative` (349 MB) and `BeforeOrdinaryReplacement` (280 MB), `ManagedAstra/SafeStartupConfigPreserve_*` (207 MB) | about 4.9 GB | Pre-change backups that inflate Staging | A hash MANIFEST; keep the S1B, Hybrid_Auto and PathB_MW sets in place |
| `Staging/AssetBankOperator_2026-10-06/OwnedPackSources/` | 9,497 MB | Vendor source cache; better under an external vendor-source root | Operator and manager agreement; licence check (legendary route) |
| Timestamped `HDA_CATALOG_RECEIPT_<ns>.json` / `CATALOG_RECEIPT_<ns>.json` history | about 5.1 GB | Superseded receipts (Git option C) | Keep the unsuffixed live receipts |
| `Staging/Archive/ManagerReset_2026-10-01`, `PreExecutionRevision_2026-09-30` | small | No MANIFEST | Add a `MANIFEST.json` (no move) |

### 5.3 Delete candidates (only items proven DEAD, or byte-exact copies of a file kept elsewhere, with no LIVE reference)

"Byte-exact" covers copies of LIVE files and copies of retained HISTORICAL files; the latter keep class HISTORICAL in section 3 (part 01 rule). Every item needs the general preconditions above, and an archive MANIFEST (path, sha256, reason) written before removal.

Label note: rows inherit the label of the section 3 row they cite. Sizes are MEASURED. The delete proposal is an INFERRED recommendation.

| Path | Size | Reason | Precondition |
|---|---|---|---|
| `PE/Houdini/GeoCity_city_v007_SurfacePainting_v001/...failed_build.hdalc` (ff3ceebb); `PE/Houdini/GeoCity_city_v009_ModularPilot/...failed_module_dispatch.hdalc` (fdef96d9) | about 1 MB | DEAD: the filename says failed | Owner confirms |
| `PB/revisions/r007_task4_before` (hdalc 2289565d and module a20e53f7), `r012_road_repair_before` (hdalc 6cdf9bc6), `r014_fix_start` (module 76dfce80) | about 2 MB | Byte copies of r007, r012 and r014 (HISTORICAL files kept elsewhere) | Delete only the compared files; keep each folder's receipt unless it also hashes equal |
| `Staging/ModularConstruction_2026-10-05/Bindings/Before/GeoCity_city_v015_PermanentBank_before.uasset` (357eeac6) | 0.5 MB | Byte copy of `Run_20261005/Before` (which is kept) | Check that no `Bindings` manifest names it |
| `Content/Untitled.umap`, `Content/Untitled_HLOD0_Instancing.uasset`, `Content/__ExternalActors__/Untitled/**` (139), `Content/__ExternalObjects__/Untitled/**` (5) | 32 MB | DEAD stray default WP world; 0 referrers | Editor closed; Reference Viewer check |
| `Content/Developers/USER/HoudiniCityProof/V7FullCatalogPolePilot/Untitled.umap` (9358d19d) | 0.4 MB | DEAD stray save (no record; INFERRED) | Reference Viewer check |
| `Content/Collections/` | 0 | Empty folder | n/a |
| `Content/Python/__pycache__/` (16 `.pyc`) | <1 MB | DEAD bytecode; regenerated on import | Prefer Git-ignore only. If deleted, do it with no editor running. |
| Redundant Staging map copies: a6961c8e x3 (`GroundPainting/Revision_2026-10-05/Before`, `.../SamplerBefore`, `ModularConstruction/Bindings/Before`), 17d5929a x3 (keep one, e.g. in RunExisting), bee525f0 x1 | about 0.4 GB | Byte-exact copies of HISTORICAL prior states. a6961c8e stopped being the live Rimal map at 14:52:20Z. Of its 5 copies, the S1B copy (pinned) and the `ReusableSky_2026-10-06/Before/` copy (the Sky task's backup) stay. | Keep one copy per hash outside Content. Prefer a move to `Backups/` over deletion, since each copy sits in a backup set whose own manifest may list it. |
| `Environmentpipeline/` (nested one-commit clone) | small | DEAD; a separate GitHub clone | **Owner only.** `git status` shows README modified: commit or discard first, and confirm the remote holds the commit. |

**Lifecycle-owned outputs are not on this list.** These are the Cook folders, the stale ClippedGeometry runs, the stale LayerInfos and the Bake leftovers.
- They stay in 5.1 (Keep), because the profiles name the Cook folder path and the unread ledgers may name the rest.
- Cleanup is owner-only, through the lifecycle's own replace/cleanup step or the RoadBLD ledger reconciliation (`PLAN_PROPOSAL.md` step 3).

**Eligible, but the reviewer recommends keeping (part 01).** These backups are pure byte copies of retained files: PB bak45/46, 50-60 and 63; 4K bak12; r019 bak1; v001 bak6; v002 bak3; v003 bak16; v004 bak5. Recommendation: keep all backup folders on disk and exclude them from Git.

**Not proposed for deletion under the strict rule.** These items are neither proven DEAD nor byte-exact copies:
- `Saved/Autosaves/**` HDA copies (their hashes differ from the originals; already outside Git via `/Saved/`).
- The three SurfacePainting HDA copies inside `RunExisting_20261005/Before` (keep the set whole).
- `Staging/RepairExecution_2026-10-03/Before/GeoCity_city_v015_PermanentBank.hdalc` (2acabf3b, a byte copy of `PB/revisions/r014`). It sits inside the profile-pinned RepairExecution folder, which 5.1 keeps whole.
- The orphan r020 folder `4K/revisions/20261004T121206056541Z_r020_use_aware_buildings/`. Its hdalc 7d7661f0 is the only copy, so it is moved to 5.2 (archive).
- The tiny byte-identical runtime and launcher copies (`SystemCompletion/Prepared/` clip and grounding, `Attempt2/` props, the modular Handoffs copies). Evidence; no gain.

### 5.4 Conditional candidates (not yet proven; listed so the manager can order the proof)

Every item here stays kept until its proof is done. The bank-orphan folders are also named as the bank named-save scope by sealed code (`geocity_editor_action.py:32-34`).

Label note: rows inherit the label of the section 3 row they cite. Sizes are MEASURED. The required proofs are INFERRED.

| Path | Size | What must be proved first | Owner |
|---|---|---|---|
| `Staging/AssetBankOperator_2026-10-06/OwnedPackChunks/` | 9,502 MB | That the SOURCE_RECEIPTs verify the assembled `OwnedPackSources/`, i.e. the chunks are redundant (INFERRED today) | Bank operator and manager; licence check |
| Bank orphans: `ModelBank/Materials/BankIntegration_20261004` (92), `Prepared/Dependencies/{Textures 135, Materials 8}`, `Prepared/Modular/Additional20Dependencies/{Textures 9, Materials 3}`, `Prepared/Modular/H0020/Procedural_v002` (5) | about 750 MB | That no pending bank row needs them (the bank result is INCOMPLETE) | Bank owner |
| `Content/FantasyRuins`, `Content/PWL_Light_Manager`, `Content/Radar` | 493 MB | That they are not in the AssetBankOperator supply plan (FantasyRuins is listed in `SOURCE_INVENTORY.json`). They are re-downloadable from VaultCache. | Manager and bank operator |
| RunExisting catalog-receipt copies (13, about 2.3 GB) and the other INFERRED JSON copies in 3.15.D | about 3 GB | A full-hash comparison (only name, size and mtime were compared) | Manager |

### 5.5 Record and tooling fixes proposed by the parts (no file moves)

1. **Register v003 and v004.** Add a `REVISION.json` to `PB/revisions/20261005_procedural_ten_families_v003/` and `..._thirty_families_v004/`, with the hashes in 3.2 and the receipt paths under `PE/ModelBank/Modular_2026-10-04/*`. Then update `PB/definition_receipt.json`, or add a pointer file, so that "canonical" names the revision the native actually runs (part 01).
2. **Annotate RATIFICATION_B2.** Record in a new note (do not edit the receipt) that 2358c514 is revision folder v003 (ProceduralTen) and that "v002" is the family-id suffix (part 01).
3. **Correct the vendor-function writer.** Add a note in `Incident_01a10c77_2026-10-05/` (do not edit `RESTORE_RECEIPT.json`) that `ProceduralCityRegeneration_2026-10-05/prepare_run.py:20` saved the 15 vendor functions (part 03).
4. **Clean `ASSIGNMENTS.json` with no editor open.**
   - Remove or refresh the stale fields `editor.current_actual_pid`, `editor_activation`, `shared_files.area_profiles_owner`, `created_chats` and `management_succession.successor_manager_thread_id` (part 02).
   - The file is re-read on every Generate, so never edit it while an editor is live.
   - Two editors are open now (PIDs 29900 and 5288).
5. **README banners only.**
   - `PathB_MW/` gets "SUPERSEDED by Hybrid (DECISION_HYBRID_20261006.json:23); TINT_PRESETS.json and pathb_profile_patch.py still used". Fix the stale `DESIGN.md:3`.
   - `S1_Prep/README.md:3` gets "v1 APPLIED IN MEMORY AND REJECTED (STAGE1_GROUND_PLAN.md:304-305); AstraMWInventory is a Hybrid input".
   - `S1v2/README_v2a.md` gets "SHELVED (STAGE1_GROUND_PLAN.md:310)".
   - Refresh `Staging/ModelBank/README.md` and the root `README.md`.
   - (parts 00b, 03, 05.)
6. **Pins.**
   - Add `Operator/copilot_client.py`, `Operator/probe_state.py` and `IranRun_20261006/capture_mcp.py` to `Operator/SCRIPT_PINS.json`.
   - After the Hybrid is ratified, drop the 5 `pathb_*` entries or mark them historical, so the client cannot run the superseded route.
   - Mark the two `copilot_call.py` copies historical.
   - (parts 02, 03.)
7. **One exit helper.** Replace the six per-PID `exit_no_save*.py` copies with one helper that takes the PID as a parameter, and keep the old copies as evidence (part 02).
8. **Align PROJECT_STATUS.** Apply the section 2.1 corrections, in particular §3 item 1 (r019 is unpromoted), §3 item 2 (the native runs v004), §2 "Operator tooling" versus `RESEAL.md:66`, and §5 (part 05).

## 6. Proposed Git setup (PROPOSAL ONLY)

### 6.1 Facts that change PROJECT_STATUS §5

1. **Both roots already have Git files from 2026-09-27 (MEASURED).**
   - The Unreal root has a `.gitignore` and a `.gitattributes` (`* -text`, then LFS by extension).
   - The Unreal `.git` was deleted on 09-27 at Aviv's request ("no git"), per `Staging/Archive/PreFinalVision_2026-09-29/Baseline/GitBaseline_2026-09-27/BASELINE_REPORT.md` (DOCUMENTED).
   - Merge with these files; do not replace them.
   - **Re-ask Aviv before creating an Unreal `.git`.**
2. **The nested `Environmentpipeline/` folder is a separate clone (MEASURED).**
   - It is a one-commit repo (`1f92a6a Initial commit`, 2026-09-25) with remote `https://github.com/Samorai-Studio/Environmentpipeline.git`.
   - The root `.gitignore` already excludes `/Environmentpipeline/`. Do not reuse it as the project repo.
3. **The PE repository exists (MEASURED).**
   - History: one commit, `dfb49ef` "Baseline: Pipeline Environment on-disk state, 2026-09-27", with LFS in use (681 MB of objects).
   - Working tree: 702 deleted, 8 modified, 44 untracked.
   - `.gitignore` has only `__pycache__/` and `*.pyc`. `.gitattributes` is byte-identical to the Unreal root's.
   - Continue this repo. A submodule does not fit, because the profiles reference PE by absolute `C:/Users/USER/Documents/Pipeline Environment/...` paths. Record the PE commit id in the Unreal repo, for example in a pin file next to the seal manifest.
4. **"Plugins/ sources (not binaries)" would break the project (MEASURED).**
   - RoadBLD, CityBLD, TwinBLD and WorldBLDMCPToolset have `Binaries/` and no `Source/`.
   - RoadBLD depends on WorldBLD (`RoadBLD.uplugin:96`).
   - Track `Plugins/*/Binaries` in LFS. Exclude only `Plugins/*/Intermediate` (4.4 GB).
5. **`Content/CitySample*` matches nothing (MEASURED).**
6. **All 14 vendor packs that 3.12 classes LIVE are dependencies (MEASURED).** The most direct ones:
   - StarterContent (37 packages feed the ground material) and MOUT_Arabian (masks);
   - MWLandscapeAutoMaterial (the Hybrid source; 15 functions restored from Vault);
   - Palms_Pack_01 (bank content).
   - The other 10 are reached through the catalog, the maps or transitively (3.12).
   - Excluding them is acceptable only with a pinned restore record listing each pack's Content folder, VaultCache id, file count and per-file sha256, the 15 restored MW functions and MOUT's 29-file subset. Part 04 proposes this as `VENDOR_PACKS.json`; part 05 as `Content/VENDOR_PACKS.md`.
   - The licence is OPEN (status §7).
7. **Developers must stay tracked (MEASURED).** At least `M_GeoCity_VertexColorPreview` must be tracked, because the Rimal live map references it.
8. **WorldBLD content has no VaultCache backing (MEASURED).** `Content/WorldBLD` (8.4 GB) cannot be re-downloaded from VaultCache. The choice is OPEN:
   - LFS-track it as the Stage1Kit dependency, or
   - exclude it and accept that Stage1Kit, `RoadBLD_Generated` and Districts become unloadable history.
9. **`Staging/**/Before/` is wrong in both directions (MEASURED, see 2.1 row 19).** Instead, ignore the binaries and catalog copies inside Before-type folders, and keep their JSON and manifests.
10. **"Staging/** text" would put about 10.9 GB of JSON into plain Git (MEASURED).**
    - 54 JSON files exceed 100 MB, and the largest is 720 MB.
    - Route the big receipts to LFS by name.
    - After the patterns below are applied, the residual text files over 20 MB are 5 files of 22-30 MB.
11. **The runtime depends on a file Git will never hold (MEASURED code; INFERRED impact).**
    - `geocity_roadbld_junctions.py:580-582` asserts a 2026-10-03 line in `Saved/Logs/Environmentpipeline.log`.
    - That log is token-bearing and must stay excluded, so a fresh clone fails that assertion whenever the legacy-adoption path runs.
    - Fixing it is a sealed-code change (reseal) for the manager.
12. **Long paths (MEASURED).** The project has paths over 260 characters. Set `git config core.longpaths true` in any repo.
13. **Cook folders (part 04, not in the tested block).** Part 04 proposes excluding `Content/Project/Areas/*/BankIntegration_v015/Cook/` (1,921 MB, 229 packages, 0 referrers). That line is **not** in part 05's tested block. If the manager adds it, re-run the pattern test. Note that a fresh clone would then lack these cook folders, which each regeneration rewrites (INFERRED).

### 6.2 Proposed Unreal root `.gitignore` (merge into the existing file; tested by part 05)

Comments sit on their own lines. In `.gitignore`, a `#` after a pattern becomes part of the pattern, so that pattern silently matches nothing.

```gitignore
# --- keep existing 2026-09-27 lines ---
/DerivedDataCache/
/Intermediate/
/Binaries/
/Plugins/*/Intermediate/
# Saved/Logs holds live bearer tokens (BASELINE_REPORT 2026-09-27)
/Saved/Logs/
# separate GitHub clone
/Environmentpipeline/
.vs/
.idea/
# --- new ---
/Build/
# whole Saved folder: Autosaves 2.1 GB, PersistentDownloadDir 3.2 GB, Crashes, per-user Config
/Saved/
__pycache__/
*.pyc
# Unreal log copies under Staging may hold tokens; scan before adding any exception
*.log
/Plugins/UnrealCopilot/Content/Python/.venv/
/Staging/AssetBankOperator_2026-10-06/OwnedPackChunks/
/Staging/AssetBankOperator_2026-10-06/OwnedPackSources/
/Staging/AssetBankOperator_2026-10-06/NativeIntake/
# backup binaries and catalog copies inside Before-type folders (json/md/manifests stay tracked)
/Staging/**/*Before*/**/*.uasset
/Staging/**/*Before*/**/*.umap
/Staging/**/*Before*/**/*.png
/Staging/**/*Before*/**/*.jpg
/Staging/**/*Before*/**/*.tga
/Staging/**/*Before*/**/*.tif
/Staging/**/*Before*/**/*.fbx
/Staging/**/*Before*/**/*.blend
/Staging/**/*Before*/**/*.sc
/Staging/**/*Before*/**/*.raw
/Staging/**/*Before*/**/*.r8
/Staging/**/*Before*/**/*.r16
/Staging/**/*Before*/**/*.bin
/Staging/**/*Before*/**/*CATALOG_RECEIPT*.json
/Staging/**/*Before*/**/*CATALOG.json
/Staging/**/*Preserve_*/**/*.umap
/Staging/**/*Preserve_*/**/*.uasset
/Staging/**/*Preserve_*/**/*CATALOG_RECEIPT*.json
# pinned rollback map copies stay tracked (re-include)
!/Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/Hybrid_Auto/Before/*.umap
!/Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/PathB_MW/Before/*.umap
# OPTION B only (vendor packs re-installed from Fab; add Content/VENDOR_PACKS.md with item, version, engine, dependent assets):
# /Content/ModularCourtyard/  /Content/FC_Coastal_Landscape/  /Content/UtopianCity/  /Content/Iceland_Environment/
# /Content/Palms_Pack_01/  /Content/MOUT_Arabian/  /Content/ModularBuildingSet/  /Content/MWLandscapeAutoMaterial/
# /Content/ProceduralBuildingGenerator/  /Content/AssetsvilleTown/  /Content/Stylized_Egypt/  /Content/StarterContent/
# /Content/FantasyRuins/  /Content/PWL_Light_Manager/  /Content/HighPoly_Tree_Model/  /Content/Warehouse_Building/  /Content/Radar/
# OPTION C (optional, saves 4.8 GB of LFS): historical timestamped catalog receipts; keep only the live unsuffixed ones
# /Staging/**/HDA_CATALOG_RECEIPT_[0-9]*.json
# /Staging/**/CATALOG_RECEIPT_[0-9]*.json
```

**One change from part 05's tested block.** `/Content/WorldBLD/` was removed from the Option B comment, because it has no VaultCache backing and cannot be "re-installed from Fab" (3.12; 6.1 fact 8). Its Git treatment is the separate open decision in fact 8. `Plugins/WorldBLD` stays tracked in every option (LIVE, RoadBLD dependency). The edited line is a comment, so the pattern test result is unaffected (INFERRED).

**Re-including S1B.** The S1B pinned set is not re-included:
- Its Shujaiya map copy equals the live map 4efebdfb (MEASURED).
- Its Rimal map copy equals a6961c8e, which was live until 14:52:20Z (MEASURED).
- Its pinned `BACKUP_MANIFEST.json` stays tracked (MEASURED, pattern test).

Add `!` lines for S1B if the manager wants its binaries in Git (INFERRED proposal).

**Pattern test (MEASURED, part 05).** The test ran in a throwaway repo in the scratchpad, never in the project:
1. `git init`;
2. apply the block above plus the appended `.gitattributes`;
3. create dummy files at the real path shapes;
4. check them with `git check-ignore -v --no-index` and `git check-attr filter`.

**Ignored, as intended:**
- `Saved/Logs/Environmentpipeline.log` and `Saved/Autosaves/*`
- `Environmentpipeline/README.md`
- `RunExisting_20261005/Before/Content/*.uasset` and `.../Before/Staging/ModelBank/.../HDA_CATALOG_RECEIPT_1791....json`
- `Revision_2026-10-05/SamplerBefore/*.umap`
- `EpicBefore_R027/*.uasset`
- `BeforeNative/.../HDA_CATALOG_RECEIPT.json`
- `SafeStartupConfigPreserve_.../AutosaveEvidence_0.umap`
- the S1B map copy
- `Plugins/RoadBLD/Intermediate/*`
- `UnrealCopilot/.../.venv/*`
- `OwnedPackChunks/*`
- `PaintBank/LIVE_UNREAL.log`

**Tracked, as intended:**
- `RunExisting_20261005/BEFORE_MANIFEST.json`
- `Hybrid_Auto/Before/AREA_PROFILE_1bd89e5b_....json`
- `S1B/BACKUP_MANIFEST.json`
- the Hybrid_Auto rollback `.umap`, via the `!` re-include (lfs)
- `Plugins/RoadBLD/Binaries/Win64/*.dll` (lfs)
- `TASK2_ALL40_POST_CLIP_GAPS_*.json` (lfs)
- `Iran_4km/CATALOG_RECEIPT.json` (lfs)
- `WORKFLOW_STATE.json` (lfs)
- the live Shujaiya `.umap` (lfs)
- `Content/Python/*.py` and `ContractAudit/Registries/*.json` (plain text)

### 6.3 Proposed `.gitattributes` additions (keep the existing file; append these; tested by part 05)

```gitattributes
# measured types missing from the 2026-09-27 list
*.r8   filter=lfs diff=lfs merge=lfs -text
*.bin  filter=lfs diff=lfs merge=lfs -text
*.b64  filter=lfs diff=lfs merge=lfs -text
*.pyd  filter=lfs diff=lfs merge=lfs -text
*.ttf  filter=lfs diff=lfs merge=lfs -text
*.otf  filter=lfs diff=lfs merge=lfs -text
*.ico  filter=lfs diff=lfs merge=lfs -text
# large JSON/HTML receipts (gitattributes matches names, not sizes)
*CATALOG_RECEIPT*.json         filter=lfs diff=lfs merge=lfs -text
*CATALOG.json                  filter=lfs diff=lfs merge=lfs -text
*HDA_RECEIPT*.json             filter=lfs diff=lfs merge=lfs -text
*ALL40*.json                   filter=lfs diff=lfs merge=lfs -text
*WORKFLOW_STATE*.json          filter=lfs diff=lfs merge=lfs -text
*GALLERY*.html                 filter=lfs diff=lfs merge=lfs -text
*CALLBACK_CONTINUATION*.jsonl  filter=lfs diff=lfs merge=lfs -text
Staging/BankPreparation_2026-10-04/gallery_check.js filter=lfs diff=lfs merge=lfs -text
```

**Already covered.** The existing `.gitattributes` has 78 LFS patterns (MEASURED, author count of `filter=lfs` lines). Among them are `.uasset .umap .png .jpg .tga .tif .exr .fbx .blend .hda .hdalc .bgeo .sc .dll .pdb .exe .raw .r16 .npz .pbf .asset .gz .pdf .zip` (MEASURED, part 05). The unclassified leftovers total 10 MB (`.geo`, `.defotl`, `.OPdummydefs`, `.osm` and similar) and are fine as plain files.

### 6.4 Size estimate (patterns applied to the 14:19Z file list; MEASURED arithmetic, INFERRED forecast)

Label: each cell in the next table is MEASURED arithmetic (part 05) over the 14:19Z file list. As a forecast of a future repo it is INFERRED. It does not include files written after 14:19Z (Supply folder, NativeIntake growth, ReusableSky/Before).

| Bucket | Option A: vendor packs tracked | Option B: vendor packs excluded |
|---|---|---|
| Plain text | about 1.5 GB (34,205 files) | about 1.5 GB |
| LFS | about 52.9 GB (44.7 GB by extension, 8.1 GB named JSON/HTML, 0.06 GB new extensions) | about 31.0 GB |
| Excluded | about 42.9 GB (20.1 GB bank-operator caches, 11.7 GB root caches/Saved/clone, 6.6 GB Staging backup binaries and copies, 4.4 GB plugin Intermediate, 0.1 GB venv/logs) | about 64.8 GB (adds 21.9 GB of vendor packs) |

**Effect of removing WorldBLD from Option B.**
- Part 05's Option B figures count `Content/WorldBLD` (8,379 MB, about 8.2 GB) among the 21.9 GB of excluded vendor packs (13.5 GB of VaultCache packs plus WorldBLD).
- With `/Content/WorldBLD/` removed from the Option B list, Option B becomes about 39.2 GB LFS and 56.6 GB excluded if WorldBLD is tracked. It stays at 31.0 / 64.8 GB if WorldBLD is excluded under fact 8.
- (INFERRED arithmetic; the summary's 31-53 / 43-65 GB ranges still hold.)

**Option C and the two rollback maps.**
- Option C subtracts a further 4.8 GB (48 files) of LFS.
- The classifier figures do not yet count the two re-included rollback maps (about +130 MB of LFS).

**Largest LFS objects.**
- `ALL40_INTERVALS` (720 MB).
- `Content/ModularBuildingSet/Demo_Scene.umap` (395 MB).
- `AssetsvilleTown/.../Demonstration_BuiltData.uasset` (362 MB).

**Cost note (INFERRED).**
- GitHub's per-file LFS limit is 2 GB on Free/Pro, and LFS storage is billed by quota. This is general knowledge from part 05; nobody checked it for this account.
- 31-53 GB of LFS is a cost decision for Aviv.

**LIVE paths that would land in "excluded" (checked mechanically).**
1. **4efebdfb map copies.** Three on-disk copies exist (S1B, `Hybrid_Auto/Before`, `PathB_MW/Before`). Without the `!` lines all three would be excluded from Git. After the Hybrid save these backups will be the only copies of 4efebdfb. The block above re-includes the Hybrid_Auto and PathB_MW copies; the S1B copy stays excluded. (MEASURED, parts 03-05.)
2. `Saved/Logs/Environmentpipeline.log` (fact 11).
3. **Option B only:** all 14 packs classed LIVE in 3.12, including StarterContent, MOUT_Arabian, MWLandscapeAutoMaterial and Palms_Pack_01 (MEASURED classification; impact INFERRED).

### 6.5 Pipeline Environment repository

- **Add to the PE `.gitignore`:**
  - `*.blend1` (1,118 MB);
  - `*.log`;
  - `SourceData/Acquisition/tile_cache/` (a re-downloadable DEM cache whose hash d157903d is recorded in five manifests).
  - Optional: `Reference/GazaRimal_Input_20230101/*.pbf`, with a README that records its sha.
- **Exclude or LFS** `PB/revisions/r016_inward_roof_before_repair/HDA_CATALOG_RECEIPT.json` (170 MB) and its `WORKFLOW_STATE.json`. Exclude `*/backup/` from Git, but keep it on disk (292 unique backup states).
- **Estimate (same arithmetic):** text about 0.2 GB; LFS about 7.9 GB (dominated by `Modular_2026-10-04`); excluded about 1.8 GB (`.git` 0.7 GB, `.blend1` 1.1 GB).
- **First commit:** it must record the 702 archive moves (deleted at old paths, untracked in Archive), so run `git add -A` per subtree after review. (The 702 is MEASURED, part 05; the procedure is an INFERRED proposal.)
- **Before the first push of either repo:**
  - scan every tracked `.log`, `*UNREAL*.log` and JSON in Staging for bearer tokens (INFERRED proposal; that `Saved/Logs` holds tokens is DOCUMENTED in the 2026-09-27 `.gitignore` and BASELINE_REPORT);
  - commit the reproducibility pins: the seal manifest, profiles, `RATIFICATION_B2.json`, all `SCRIPT_PINS*.json` and `EDITOR_OWNER.txt`.

## 7. Open questions for the manager

1. B3: ratify v004 (3cf1f840) or roll back to B2 (restore 2358c514 from `PE/ModelBank/.../Integration/Before/` and also restore the v003 registries a39dbbb9/b2e1876b)?
2. Pin the native HDA sha256 in the profiles or the seal manifest, so a silent re-import fails a gate (a reseal record is needed)?
3. Register v003 and v004 with a `REVISION.json` each, point `PB/definition_receipt.json` at the running revision, and annotate RATIFICATION_B2 ("v002" = family suffix; bytes = v003)?
4. Shujaiya: wait for the Hybrid save, or write the Natural-fallback leaf patch now (Natural child, no `external_landscape_material`, grass false, registry 8d8622b2)?
5. Consolidate the launchers into one area-parameterized `launch_editor.ps1` (reseal, B3 record) and add the Iran map to `native_area_maps`, both with no editor running?
6. Bank route: re-issue `BANK_ACTIVATION.json` and `BankIntegration_2026-10-04/ASSIGNMENT.json` under cc37d4d2, or leave them as refused authorities?
7. Is the `legendary`-client download route in `AssetBankOperator_2026-10-06/stage_owned_packs.py` acceptable (Epic/Fab terms, licence)?
8. Quarantine `Iran_4km_2026-10-04/launch.ps1` and `Operator/iran_generate.py` now, and pin `copilot_client.py`, `probe_state.py` and `capture_mcp.py`?
9. How should AGENTS.md be fixed: reconcile the parallel-editor rule with "One editor writer at a time", update the seal to 258469e1, correct the technical note's claim that `GENERATION_ACTIVATION.json` is validated by sealed code, and drop the stale `ManagedAstra` pointer (line 46)?
10. Under parallel editors, what does `EDITOR_OWNER.txt` mean for a Generate in a second editor, given that sealed code reads only that file?
11. Remove the 15 Recovery re-saves from Content (archive with MANIFEST), and separately decide `BeforePermanentBank_20261002`?
12. Keep `Content/Project/Shared/Bank_ME` (v1) because it holds same-named hold copies, or archive it?
13. Are the bank orphans (about 750 MB) and FantasyRuins/PWL_Light_Manager/Radar intended for pending bank rows or for the supply plan?
14. Who reconciles the ledgers (`named_generated_dependency_paths`, `ROADBLD_WORKFLOW_STATE.json`) before the stale Cook, clip, LayerInfo and Bake outputs are cleaned?
15. `geocity_roadbld_junctions.py:580-582`: change the code (reseal), or accept that a fresh clone cannot run the legacy-adoption path?
16. Git: re-ask Aviv before creating an Unreal `.git` (he said "no git" on 09-27)?
17. Git: vendor option A or B, option C, and `Content/WorldBLD` in LFS or excluded?
18. Git: keep `Content/Developers` tracked, or move `M_GeoCity_VertexColorPreview` into `/Game/Project/Shared/` in a leased editor?
19. Git: exclude the Cook folders (part 04 proposal, untested pattern)?
20. Is the lack of any backup of the previous Iran map 623aa0c0 acceptable, given that the fresh reopen of c409279c is still pending?
21. Are `S1_Prep/s1_verify.py`, `s1_capture.py` and `s1_backup.py` still working tooling (status §2), or superseded (`RESEAL.md:66`)?
22. Add the missing `MANIFEST.json` to `Staging/Archive/ManagerReset_2026-10-01` and `PreExecutionRevision_2026-09-30`?
23. Review the bank operator's in-window catalog and profile rewrite (14:32:57-58Z), then re-pin the 8 Hybrid args (still 4174a627)?
24. Owner decision (section 9): does "the rest" include GazaRimal?

## 8. Appendices

### Appendix A. Method and limits

**Reference audit (part 04).** This was a strings-based audit, not an Unreal Asset Registry graph.
- `strings` is not installed in this Git Bash, so a Python byte-regex reader stood in. It reads ASCII `/Game/...` FNames and FStrings, plus UTF-16LE FStrings, and normalizes each match to a package path.
- **Roots:** the three live maps, the three profiles, the catalog, the registry chain (the 2 bound registries plus their 116 referenced JSON files, one level deep) and `Content/Python/*.py`.
- **Closure:** a breadth-first search over every reachable package's bytes. A plugin-aware rerun also mounted `/RoadBLD/`, `/CityBLD/`, `/WorldBLD/`, `/TwinBLD/`, `/HoudiniEngine/` and `/UnrealCopilot/`.
- **Reverse check:** for each unreachable package, a search of `Content/Project`, `Developers`, `__External*`, `HoudiniEngine` and `RoadBLD_Generated` for referrers.

**What "unreferenced" does not prove.**
- A hit means a name is present in the package header, not that the package is hard-loaded.
- A package referenced only by another unreferenced package still counts as unreferenced.
- FName number splitting (`Name_5` stored as `Name` plus a number) is handled conservatively: every `X_N` counts as referenced when `X` is named. This over-includes, which is the safe direction.
- Files of 64 MB or more were read only for their first 16 MB, which holds the name and import tables. This affects only large vendor maps and textures.
- The native HDA embeds its definition compressed, so any `/Game` paths inside it cannot be resolved. The same applies to paths built at run time from folder settings (cook and bake folders, the bank save scope).
- **The run ledgers were not read** (`*_STATE.json`, including `ROADBLD_WORKFLOW_STATE.json` and `WORKFLOW_STATE.json`). The lifecycle may list Cook outputs, clip runs, Bake outputs and LayerInfos there. "Unreferenced from LIVE roots" therefore does not mean "unknown to the lifecycle".
- The method is not a substitute for the Reference Viewer check and the controlled editor reopen required by `UNREAL_DEPENDENCY_REVIEW_2026-09-29.md:14`.

**Snapshot limits.**
- The counts are a snapshot from about 13:45-14:25Z.
- `Content/Project/Shared/ModelBank/Supply/` (244 files, 794 MB) is not counted. Neither are `Staging/AssetBankOperator_2026-10-06/NativeIntake/` growth after 14:19Z or any lease lines after 14:14:05Z.
- Superseded in-window or after it (snapshot caveat 5-7):
  - the catalog and three profiles (14:32:57-58Z);
  - the Shujaiya assignment state (14:18:18Z);
  - the Rimal map (14:52:20Z);
  - the `.uproject` (14:47:15Z);
  - two new editor startups (PIDs 28148, 5288).
- The reference closure, the route-per-area table and the profile rows use the survey-time values.
- The new hashes come from the coordinator's reviewer. The author confirmed them only by listing (mtime, size), without opening files the operators are writing.

**Re-run advice.** After the bank lease on PID 29900 is released, re-run these with no editor writing:
- the closure (Appendix B, part 04 script);
- the Recovery reference check (3.10.B);
- the map hash check;
- the 17-pin seal check.

**Temporary evidence.** The reviewers' working files live in this session's scratchpad (`C:/Users/USER/AppData/Local/Temp/claude/C--Users-USER-Documents-Unreal-Projects-Environmentpipeline/ff22121a-53df-4931-b47d-2e304b337189/scratchpad/`). That folder is session-temporary and will not persist. It holds `hda_files_inventory.tsv`, `hda_inventory.py`, `embed_check.py`, `refscan.py`, `extract_game.py`, `closure.py`, `closure_plugins.py`, `reverse.py`, `mkgroups.py` and the `refs/` outputs. Copy them into this folder if the manager wants them kept.

**Pinned values.** Hashes in this document are first-8 prefixes unless written in full. Full hashes for the seal, the source packages and the B2/v004 natives are quoted where the parts gave them.

### Appendix B. Commands and scripts the reviewers used (short; source part in brackets)

```bash
# [00] sizes
du -sm Staging/* Content/* "/c/Users/USER/Documents/Pipeline Environment"/*
# [02] running editors, lease tail, seal pins (read-only)
tasklist /FI "IMAGENAME eq UnrealEditor.exe"
tail -5 Staging/ModelBank/EDITOR_OWNER.txt
sha256sum Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json Content/Python/*.py Config/DefaultEngine.ini Config/DefaultRoadBLD.ini Staging/SystemCompletion_2026-10-04/{launch_editor.ps1,seal_runtime.py}
# [03] Recovery reference checks
MSYS_NO_PATHCONV=1 grep -rla "/Game/Project/Shared/Recovery" Content/Project Content/MWLandscapeAutoMaterial --include=*.uasset --include=*.umap
MSYS_NO_PATHCONV=1 grep -rlaF "/Game/Project/Shared/Recovery" Content --include=*.uasset --include=*.umap | grep -v "^Content/Project/Shared/Recovery/"
MSYS_NO_PATHCONV=1 grep -rlaF "/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround" Content/Project --include=*.umap --include=*.uasset
MSYS_NO_PATHCONV=1 grep -rlF "/Game/Project/Shared/Recovery" Staging --include=*.json --include=*.md --include=*.py --include=*.txt --include=*.t3d
MSYS_NO_PATHCONV=1 grep -rlF "Shared/Recovery" Config Content/Python --include=*.ini --include=*.py --include=*.json
find Staging/ModelBank -name '*STATE*.json' -newermt '2026-10-06 16:39'   # listing only
# [04] map hashes
find Content -name "*.umap" -printf '%s\t%TY-%Tm-%Td %TH:%TM\t%p\n'   # then sha256sum | cut -c1-8 per file
# [04] roots (Python byte-regex extractor stands in for strings)
python extract_game.py <map.umap> > map_<area>.txt
MSYS_NO_PATHCONV=1 grep -oh '/Game/[A-Za-z0-9_/.-]*' Staging/ModelBank/*/AREA_PROFILE.json | sort -u > profiles.txt
MSYS_NO_PATHCONV=1 grep -oh '/Game/[A-Za-z0-9_/.-]*' Content/Python/*.py | sort -u > python.txt
grep -oh '"path": *"[^"]*"' Staging/ModularConstruction_2026-10-05/ContractAudit/Registries/{8d8622b2...,b3fe7421...}.json
sed 's/\..*$//; s#/$##' <set>.txt | sort -u > pkg_<set>.txt
# [04] closure / reverse / grouping: closure.py, closure_plugins.py, reverse.py, mkgroups.py (scratchpad, read-only)
# [05] snapshots, Git pattern test (throwaway repo in scratchpad), PE repo status
python -c "os.scandir walk -> path,size,mtime(UTC)"          # 14:19Z UP, 14:21Z PE
git init <scratch>; git check-ignore -v --no-index <paths>; git check-attr filter <paths>
git --no-optional-locks -C "/c/Users/USER/Documents/Pipeline Environment" status
# [author] spot checks while writing
ls -1p Staging
ls -l --time-style=full-iso Staging/ModelBank/EDITOR_OWNER.txt
MSYS_NO_PATHCONV=1 ls -d Content/Project/Shared/ModelBank/Supply Staging/ModelBank/Supply
sed -n 576,584p Content/Python/geocity_roadbld_junctions.py
sed -n 646,652p Content/Python/geocity_bank_workflow.py
sed -n 243,246p Content/Python/geocity_editor_action.py
grep -n '"Name"' Plugins/RoadBLD/RoadBLD.uplugin
grep -n "current Astra assignments\|One editor writer at a time\|3cd33b15" AGENTS.md
```

**Python regexes [04]:**

```python
pat   = re.compile(rb'/Game/[A-Za-z0-9_/.\-]+')                                   # ASCII FNames / FStrings
pat16 = re.compile(rb'(?:/\x00G\x00a\x00m\x00e\x00/\x00)(?:[A-Za-z0-9_/.\-]\x00)+')  # UTF-16LE FStrings
# package path = match.split('.')[0].rstrip('/')
```

**Embed check [01].** For each native `.uasset`:
1. find the `INDX` header;
2. read the int32 length just before it;
3. slice that many bytes;
4. compare the slice byte-for-byte with every `.hdalc` on disk.

A match is reported as `EXACT_EMBED_MATCH` (script `embed_check.py`). Per-file inventory: `hda_inventory.py` -> `hda_files_inventory.tsv`.

**Module divergence [01].** An AST-level diff of the top-level `def`s and constants between module files (v004 vs 4K root; PB r018 vs 4K; r019 vs 4K; r020 vs r019; v003 vs v004).

### Appendix C. Mission text (verbatim, from the manager)

"build one inventory of the project as it is now, and classify every system, script, profile, launcher, map, material route, HDA copy and Staging folder into exactly one of: LIVE (used by the current sealed runtime or the current plan), DUPLICATE (a second copy or parallel route of something LIVE), DEAD (does not work, failed, or is blocked by its own records), or HISTORICAL (superseded, kept only as evidence). For each DUPLICATE or DEAD item give: path, what it duplicates or why it is dead, the file or log line that proves it, and whether anything LIVE still references it. Check especially: the two Houdini generators (1 km PermanentBank vs 4 km fork), canonical vs native HDA drift, the three ground-material routes (Natural, Path B MW, Hybrid), the four editor launchers, the lease/activation files under Staging/ManagedSystemsAstra_2026-10-04/, recovery copies under /Game/Project/Shared/Recovery/, large binary backups inside Staging, and anything in Content that no profile, catalog or map references. Deliverable: one English document Staging/Consolidation_2026-10-06/INVENTORY.md with the classified table, a proposed delete/archive/keep list, and a proposed .gitignore + Git LFS pattern list. Propose only; the manager decides. Do not delete, reorganize, rename, Save All, open an Unreal editor, cook Houdini, or touch the holds (H0013, H0907, H0051, H0958, H0094) or the 87 unvalidated road candidates. Label every statement as measured, documented or inferred."

## 9. Owner decision (Aviv, 2026-10-06 ~15:35Z, given in the review conversation; DOCUMENTED)

- **Decision (DOCUMENTED, relayed by the coordinator).**
  - Keep only the latest Gaza environment, GazaShujaiya (`/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration`, 4efebdfb).
  - Delete four categories: the Iran map; the old pilot/proof/test maps; the old Houdini generator versions; the working folders of the old chats.
  - Aviv's words: "only the latest version of Gaza, all the rest can be deleted".
- **Assumption made by this review, not yet confirmed by Aviv.** GazaRimal is included in "the rest" (open question 24).
- **How the decision is recorded here.** The decision changes no class in section 3. Where it touches a LIVE item, the item keeps its LIVE class and gets the note "retire on owner decision". This keeps the classification measured and the decision visible (INFERRED method).
- **Labels.** Category membership in the table below is INFERRED from the section 3 rows. The classes and dependencies cited come from those rows, with their labels.

### 9.1 Reconciliation table

| Owner category | Items in this inventory | Current class | Must stay (dependency of Shujaiya or of the holds) | Note |
|---|---|---|---|---|
| The Iran map | Map `L_Iran_38196167_46086167_4km` (3.8.A); Iran profile (3.7); native 4 km HDA 43ca7d0e (3.2.D); `4K` root, backups, r019, r020, orphan r020 (3.2.B); AreaScopes `DT_Iran_...` (3.11); Iran Cook `78F86F39` (3.2.E) and LayerInfos (3.8.A); `Staging/Iran_4km_2026-10-04/` incl. `launch.ps1`, `Bootstrap/`, `copilot_call.py` (3.14, 3.4, 3.6); `IranBuildingAdaptation_2026-10-04`, `PipelineSemanticRepair_2026-10-04`, `HoudiniEngineOutputRepair_2026-10-04`, `HoudiniUnrealDataReport_2026-10-04` (3.14); IranSemanticConsumer forks (3.3); `Operator/IranRun_20261006/` and `iran_*.py` (3.6); PE Iran source packages (3.16); `AssetBankOperator_2026-10-06/Before/IRAN_MAP_BEFORE_EXPANSION.umap` | LIVE items (map, profile, native, 4K root, AreaScopes catalog, Iran_4km folder, IranRun record, iran probes, PE Iran source): retire on owner decision. Others DEAD (r019, r020, orphan r020, launchers), DUPLICATE (forks, copilot_call) or HISTORICAL. | None of the Iran items. Items shared with Shujaiya stay: `MI_SurfaceBank_Natural` (parent of the Shujaiya child MI), `M_SurfaceBank_Natural`, `LG_GeoCity_PermittedGroundGrass`, the GeoCity normals and masks, `M_Landscape_GazaRimal`, the catalog `DT_EnvironmentBank_v4`. | PID 29900 still holds the Iran map under the bank operator's lease (since 14:14:05Z), so retirement waits for its release. The Iran profile's `decision_receipt` now points into AssetBankOperator (snapshot caveat 5). |
| GazaRimal (assumed; not confirmed) | Map (1d670c8e since 14:52:20Z) (3.8.A); Rimal profile (3.7); Rimal child `MI_GeoCityGround` 99ad6bb8 (3.9.B); registry `b3fe7421...` (3.7); Rimal Cook `B7CE31BC`, stale LayerInfos, Bake leftovers (3.2.E, 3.8.A); `M_GeoCity_VertexColorPreview` (3.12; only the Rimal map uses it); the 5 a6961c8e copies (3.15.B); `Staging/ModelBank/PermanentIntegration_2026-10-02/` (Rimal profile folder and its 10-02 scripts) | LIVE items (map, profile, child MI, registry, material): retire on owner decision. Others DEAD (stale outputs) or HISTORICAL (copies, scripts). | `M_Landscape_GazaRimal` must stay despite its name: the Shujaiya map names it (author re-grep, 1 hit). Also stay: `MI_SurfaceBank_Natural`, the LG grass type, the EpicResident2K textures (the Shujaiya child MI uses them). | The Reusable Sky task appears to be working on the Rimal map now (`ReusableSky_2026-10-06/Before/` holds both states; INFERRED). Coordinate with that operator first. `PermanentIntegration_2026-10-02/` sits inside `Staging/ModelBank` and holds run ledgers that the lifecycle may read; check before removal (INFERRED). |
| Old pilot/proof/test maps | Developer maps (26, 3.8.B) and Developer proof HDAs (3.2.D); `Content/HoudiniEngine/{Temp,Bake}` (3.12); old Rimal SurfacePainting map and chain (3.8.A, 3.9.F); `Stage1Kit.umap`, `District_LittleHavana_Dense`, `RoadBLD_Generated` (3.8.A, 3.12); `BeforePermanentBank_20261002` recovery world (3.10); stray `Untitled` worlds (3.8.A, 3.8.B); SurfacePainting HDAs v007/v013/v014 and the AllLayers chain (3.2.D, 3.9.F); older catalogs `DT_BankRelease_v2`, `DT_BankRelease_AllDisabled_v2`, `DT_NonBuildingBank_v3` (only Developer maps use them; 3.11); Staging map copies from TrackA/RestartReview/pegasus (3.15.B) | HISTORICAL, except the two Untitled worlds (DEAD) | `Content/Developers/USER/ModelBankProof/H0958_MaterialRepair_20260929/` (hold H0958 proof assets). `M_GeoCity_VertexColorPreview` until Rimal retires. | Vendor demo maps (3.8.C) are vendor payload, not pilot maps; this review leaves them out of this category (AGENTS: preserve native originals). Deleting Stage1Kit leaves `Content/WorldBLD/Assets` (8.4 GB) fully unreferenced, but the WorldBLD plugin stays (RoadBLD dependency). This decision overrides "Keep old Developer evidence as history" (AGENTS) and the WorldBLD keep decision (`UNREAL_DEPENDENCY_REVIEW_2026-09-29.md:3,10`) only if Aviv confirms (INFERRED). |
| Old Houdini generator versions | `PE/Houdini` v001-v014, pilots, proof/layout folders, CityProof, failed files (3.2.C); PB helper scripts, revisions r001-r016 incl. byte-copy folders, r016 archive, v001, v002 and their backups, `PB/backup/` (3.2.A); `4K` fork if Iran retires (3.2.B); Staging HDA and native copies (AppearanceRepair, RepairExecution, TrackA, Connection, Bindings copy; 3.2.D); Content SurfacePainting HDAs (3.2.D); `Saved/Autosaves` HDA copies | Mostly HISTORICAL. DEAD: failed files, r019, r020, orphan r020. DUPLICATE: v003/v004/4K final backups. The 4K root (LIVE) retires with Iran. | **Stay:**<br>- PB root r018 (hdalc 61303c15, module, receipt): the base of v001-v004.<br>- The v003 folder (B2 ratified) and the v004 folder (running).<br>- Native 1 km `GeoCity_city_v015_PermanentBank.uasset` 3cf1f840.<br>- The B2 native 2358c514 and the v002 native 1de0e6fe under `PE/ModelBank/Modular_2026-10-04/*/Integration/Before/` (only copies), with the pre-v004 profiles there.<br>- Unless Aviv explicitly accepts losing them: the r018 native snapshot 357eeac6 and the v001 native f407976c (only copies); `PB/backup/` bak61/bak62 (the only r017-era states); the unique v003/v004 intermediate backups. | `PE/Houdini/README.md`: path behaviour after moving CityProof is untested. r019 and r020 are the only copies of the semantic-palette and use-aware building logic, so retiring Iran retires that logic too (INFERRED). |
| Working folders of the old chats | Staging folders classed HISTORICAL in 3.14: BankDepthAudit, BankPreparation, Diagnostics, HoudiniEngineOutputRepair, HoudiniUnrealDataReport, IranBuildingAdaptation, ManagedAstra, ModularBank, NativeUnrealAssetSupply, Operator (tombstone), PaintBank, PipelineSemanticRepair, ProceduralCityRegeneration, RestartReview, ReturnToPipeline, TrackA_Tests, UnrealConstructionAudit, V13ConnectedPreview; the loose `.md` records (CONTRACT x2, PREREQUISITE, STATUS_AND_REPORT_INDEX, TOOLCHAIN_VERIFICATION, UNREAL_DEPENDENCY_REVIEW) | All HISTORICAL (3.14) | **Stay (LIVE by code, profile or current task):** AppearanceRepair_2026-10-03, BankIntegration_2026-10-04, GroundPainting_2026-10-04, ManagedExecution_2026-10-02, RepairExecution_2026-10-03, SystemCompletion_2026-10-04, ShujaiyaOrdinaryRun_2026-10-05, AssetBankOperator_2026-10-06, ModelBank, ManagedSystemsAstra_2026-10-04, ToolchainChecks. Also **ModularConstruction_2026-10-05** (the Shujaiya profile's registry ref points into it; missing from the coordinator's list), ReusableSky_2026-10-06 (active task), Archive (AGENTS cites it) and Consolidation_2026-10-06. | "The six dead launchers go with their old folders" holds for only three of them: `launch_current_area.ps1` (HoudiniEngineOutputRepair), `launch_replacement_editor_PREPARED.ps1` (ManagedAstra) and the Iran `launch.ps1` (Iran_4km, with Iran). The other three sit inside must-stay folders and need individual archiving (5.2): `launch_ground.py` (GroundPainting), `launch_modular_editor.ps1` (BankIntegration), `launch_reviewed.ps1` (ManagedSystemsAstra). `UNREAL_DEPENDENCY_REVIEW_2026-09-29.md:14` holds the reference-check precondition; copy that rule before its file goes. |
| Holds and the 87 candidates (not an owner category; listed so nothing in them is deleted) | `Content/Project/Shared/Bank_ME` (same-named H0013/H0907/H0051/H0094 copies); `Bank_ME_v2` (`SM_H0958_CoconutPalm`); `Prepared/Modular/H0013/Procedural_v002`; `ModelBankProof/H0958_MaterialRepair_20260929/`; `Staging/ModelBank/ME/Sources/` (H0013 sources); clip run `20261003T203730573110_212401627821` (87 uassets) | DUPLICATE (Bank_ME), HISTORICAL (Bank_ME_v2, Developers), DEAD candidate (H0013 Procedural_v002), DUPLICATE (ME/Sources); the clip run is LIVE area content | All of them stay | Mission and AGENTS rule. The hold assets are mentioned only. |

### 9.2 Must stay for GazaShujaiya to keep working (INFERRED from section 3; re-check before any deletion)

- **Bank and modular kit:**
  - catalog `DT_EnvironmentBank_v4` (now e26bf06c) and `S_BankReleaseRow_v3`;
  - `Content/Project/Shared/ModelBank/Prepared/**` (the reachable part) and `Materials/Instancing`;
  - `Bank_ME_v3`;
  - the bound registry `8d8622b2...` and its 116 referenced JSON files in `ModularConstruction_2026-10-05/ContractAudit/`;
  - the modular kit sources in `PE/ModelBank/Modular_2026-10-04/`.
- **Generator:**
  - the 1 km native 3cf1f840;
  - the PB root r018 and the v003 and v004 revision folders;
  - the B2 native 2358c514 and its partners under `PE/ModelBank/Modular_2026-10-04/*/Integration/Before/`;
  - the v003 registries a39dbbb9 / b2e1876b (B2 rollback).
- **Ground:**
  - the Natural route: `M_SurfaceBank_Natural`, `MI_SurfaceBank_Natural`, the Shujaiya child `MI_GeoCityGround` (map rollback target), `LG_GeoCity_PermittedGroundGrass`, the EpicResident2K and GeoCity textures;
  - the StarterContent textures they use (37 packages) and `M_Landscape_GazaRimal`;
  - the Hybrid route inputs: `Content/MWLandscapeAutoMaterial`, `Hybrid_Auto/`, `PathB_MW/TINT_PRESETS.json`, `pathb_profile_patch.py`, `PathB_MW/Before/`, `S1_Prep/AstraMWInventory/`, `GroundPainting_2026-10-04/native_graph_stochastic.py`.
- **Map content:**
  - the 185 Shujaiya packages reached from the map;
  - the Shujaiya RoadBLD sidewalks and the 2 referenced clip runs (including the 87-candidate run);
  - `Shared/RoadBLD/Materials`;
  - the lifecycle-owned Shujaiya Cook/LayerInfo set `1428_1804_0` until the post-Hybrid verify.
- **Runtime:**
  - the sealed runtime (13 files), its manifest 258469e1, `launch_editor.ps1`, `seal_runtime.py`;
  - `Config/DefaultEngine.ini` and `DefaultRoadBLD.ini`;
  - the other Config files and `Environmentpipeline.uproject`;
  - `Saved/Logs/Environmentpipeline.log` (asserted by `geocity_roadbld_junctions.py:580-582`).
- **Plugins:** `Plugins/HoudiniEngine`, `RoadBLD`, `WorldBLD` (plugin), `UnrealCopilot`, `UnrealMCP`.
- **Staging:**
  - the folders listed in the "Working folders" row above;
  - the Shujaiya profile `Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json` and its receipts;
  - the survey-time profile copies in `AssetBankOperator_2026-10-06/Before/`.
- **Source:** `PE/SourceData/GazaShujaiya/` (and the DEM tile whose hash its manifest records).
- **Holds and the 87 candidates:** everything in the last row of 9.1.
- **Vendor packs:** the closure in 3.11.B was computed over all three maps together. Before any vendor pack or shared package is removed because only Iran or Rimal used it, re-run the closure with Shujaiya-only roots (INFERRED requirement).

### 9.3 Consequences to flag (INFERRED)

- Deleting the Iran map retires with it:
  - the 4 km generator (`4K`, native 43ca7d0e) and the parked r019/r020 logic;
  - the Iran profile and AreaScopes catalog;
  - `Iran_4km_2026-10-04`.
- The project then has one generator line (1 km PermanentBank), and status §3 item 1 ("two generators") resolves by retirement, not by merging.
- Deleting GazaRimal removes the only area on the Natural route with grass on. Shujaiya has grass off, and its Hybrid is unbuilt.
- Old-chat folders that are LIVE by code reference cannot be deleted until the code paths or profile fields that point into them are changed and the runtime is resealed (sealed-file change, B3-style record). Examples:
  - `AppearanceRepair_2026-10-03` (`geocity_roadbld_clip.py:266-271`, `geocity_roadbld_grounding.py:1309`);
  - `BankIntegration_2026-10-04` (`geocity_editor_action.py:28`);
  - `ManagedSystemsAstra_2026-10-04` (`geocity_editor_action.py:26,30`);
  - `RepairExecution_2026-10-03` and `ManagedExecution_2026-10-02` (profile provenance).
- "Old Houdini versions" excludes the following unless Aviv explicitly accepts losing them:
  - the r018 root, v003 and v004;
  - the unique `_bak61` / `_bak62` states;
  - the only-copy natives 357eeac6 and f407976c.
- `Content/WorldBLD/Assets` becomes fully unreferenced once Stage1Kit goes, but it is 8.4 GB with no VaultCache backing. Deleting it cannot be undone from the launcher, so it needs a separate explicit decision.
- The decision overlaps two active operators. The bank operator holds PID 29900 on the Iran map. The Sky task appears to own the Rimal map. Neither can be touched until they release (`AGENTS.md:5-9`).

### 9.4 Execution (not performed by this review)

- The manager (session cc37d4d2) executes the deletions through the editor.
- Before each package deletion, a reference check (AGENTS.md: "do not clean old packages without checking their references"; `UNREAL_DEPENDENCY_REVIEW_2026-09-29.md:14`).
- Only after the bank operator (PID 29900) and the Sky operator (PID 5288 at about 15:25Z) have released their editors.
- Never Save All.
- Non-Content folders (Staging, `PE/Houdini`) are removed only after the same reference re-check (3.10.B method plus a code and profile grep).
- The deletions are recorded in a receipt under `Staging/Consolidation_2026-10-06/` (path, sha256, reason, reference-check result).
- Nothing in this section has been executed.

## 10. Portability of a Git clone to another computer (added by the review at Aviv's request, 2026-10-06 ~15:55Z)

Question from Aviv: after the deletions, can the whole project be pushed to Git and work on another computer that clones it, or do folder locations have to change first?

Answer (MEASURED unless labelled): opening and viewing the saved GazaShujaiya map in a clone would work, because maps and assets reference `/Game/...` package paths only. Running the generator (Generate / Regenerate, roads, bank binding) would NOT work in a clone as the tree stands, because the profiles carry this computer's absolute paths and the runtime reads them.

### 10.1 Machine-bound facts

| Item | Measured today | Effect in a clone | Label |
|---|---|---|---|
| Absolute paths in the three area profiles | `Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json` 41 hits, `PermanentIntegration_2026-10-02/AREA_PROFILE.json` 42, `Iran_38196167_46086167_4km/AREA_PROFILE.json` 34, all of the form `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\...` or `C:/Users/USER/Documents/Pipeline Environment/...` | Every path breaks when the user name, drive or folder differs | MEASURED |
| Profile keys the sealed runtime actually opens as files | `profile['source']` (`geocity_editor_action.py:148`, `geocity_roadbld_workflow.py:347`) = `C:/Users/USER/Documents/Pipeline Environment/SourceData/<Area>/city_source_v1.json`; `catalog_receipt` (`geocity_bank_workflow.py:145`, `geocity_roadbld_workflow.py:405,475,546`); `build_state_alias` (`geocity_bank_workflow.py:439`); `decision_receipt` (`geocity_bank_workflow.py:505-506`, hash-checked) | Generation stops at the first read. The `source` key also crosses into the second tree (Pipeline Environment), so that tree must exist at the same absolute path | MEASURED |
| Registries bound by the Gaza profiles | 152 absolute `"path"` values in registry 8d8622b2 (93 under the Unreal project, 58 under `Pipeline Environment/ModelBank/Modular_2026-10-04`) | The runtime reads `item['path']` for meshes (`geocity_bank_workflow.py:450,627,857`); whether those are the filesystem paths or `/Game` paths was not traced. INFERRED: the filesystem ones are provenance | MEASURED / INFERRED |
| Sealed runtime modules `Content/Python/*.py` | 0 absolute paths | Portable | MEASURED |
| Sealed launcher `launch_editor.ps1` | Finds the project relative to its own folder (`$taskRoot`, line 12, 80); one absolute path to `C:\Program Files\Epic Games\UE_5.8\...\UnrealEditor.exe` (line 79) | Portable if UE 5.8 is installed at the default launcher location | MEASURED |
| `Environmentpipeline.uproject` EngineAssociation | GUID `{F2B44468-4491-1E02-F0D0-7087DF70CD1C}`, registered only in this computer's registry (`HKCU\Software\Epic Games\Unreal Engine\Builds` -> `C:/Program Files/Epic Games/UE_5.8`) | A clone does not know which engine to use until the association is switched; setting it to the string `5.8` is portable (DOCUMENTED Unreal behaviour) | MEASURED / DOCUMENTED |
| Houdini | Installed `Houdini 22.0.429`; plugin `Plugins/HoudiniEngine` VersionName `3.0 - H22.0.429`; `DefaultHoudiniEngine.ini` uses the default Houdini location | The other computer needs the same Houdini version and a licence | MEASURED |
| `Config/DefaultEditorPerProjectUserSettings.ini:16` | `UvExecutable=C:/Users/USER/.local/bin/uv.exe` | UnrealCopilot operator tooling only; harmless for generation | MEASURED |
| Operator scripts under `ShujaiyaOrdinaryRun_2026-10-05/Operator/` | 8 one-time scripts with one absolute path each | Not part of generation | MEASURED |
| Houdini source module `geocity_city_module.py:2823` | One absolute path inside a provenance constant (a Downloads file with its sha256) | INFERRED: not read at cook | MEASURED / INFERRED |
| Two separate trees | Unreal project at `Documents/Unreal Projects/Environmentpipeline`, sources at `Documents/Pipeline Environment` (two repos) | A clone must reproduce both at the same absolute paths, or the paths must become relative | MEASURED |

### 10.2 Does the folder layout have to change? (PROPOSAL; the manager decides)

Not the layout by itself: the absolute paths do. Two ways, both small and bounded:

1. **Keep two roots, make paths relative.** Convert the ~40 absolute paths per profile to paths relative to the project root (for Staging receipts) and to a second anchor for the source tree; resolve them in the 4 runtime read sites listed above (the HDA module already expands `~` and environment variables at `geocity_city_module.py:86`, the runtime does not). This touches 3 profiles and 4 code lines, so it needs a reseal record and a manager-approved profile patch. The clone then needs an environment variable or a fixed sibling folder for `Pipeline Environment`.
2. **One repository.** Move the Houdini/GIS tree inside the Unreal project (for example `Environmentpipeline/PipelineSources/`) or add it as a submodule at a fixed relative path, and convert the profile paths to project-relative. This changes the standing AGENTS.md rule "Keep GIS/Houdini sources under C:/Users/USER/Documents/Pipeline Environment", so it is Aviv's and the manager's decision. It is the simplest layout for "clone and it works".

Either way, also set `EngineAssociation` to `5.8` in the `.uproject`.

### 10.3 What the other computer must have anyway (DOCUMENTED / MEASURED)

Unreal Engine 5.8 from the Epic launcher at the default location; Houdini 22.0.429 with a licence (the plugin is in the repo); the owner's signed-in licensed session for RoadBLD; `git config core.longpaths true` before cloning; Git LFS installed; the Fab vendor packs re-installed if Option B of section 6 excludes them (StarterContent at least, see 3.12). The `Saved/Logs` assertion (section 4) is noted; Aviv said on 2026-10-06 it is not a concern for him now.

Open question 25 (for the manager): which of the two portability routes, and when to patch the profiles given that the bank operator rewrote them at 14:32Z and the Hybrid args still pin the old Shujaiya profile hash.

### 10.4 Aviv's variant (2026-10-06 ~16:05Z): push only the Unreal project with the bank, without the GIS acquisition and Houdini trees

Assessment (INFERRED from the measured facts in 10.1):
- **Works as a viewer.** A clone of the Unreal project alone opens the saved GazaShujaiya map and the bank assets, because maps and assets reference `/Game/...` paths only and the baked actors are ordinary static-mesh instances. The Houdini Engine plugin travels in `Plugins/`; without Houdini installed it simply has no session.
- **Cannot create or regenerate an environment.** The generator is the Houdini HDA. Cooking needs Houdini 22.0.429 installed with a licence on that computer, and the HDA reads the area's geographic source package from disk (`profile['source']` -> `Pipeline Environment/SourceData/<Area>/city_source_v1.json`). Without the SourceData packages there is no input.
- **Smallest set that can still regenerate the existing areas:** the Unreal project + the `Pipeline Environment/SourceData/` packages (161 MB total; GazaShujaiya 1 MB) + Houdini installed, with the profile `source` path (and the Staging receipt paths) made relative as in 10.2. Not needed to run: the acquisition tooling (conda/QGIS), the Houdini `.hdalc` source (240 MB, only for editing the generator; the native uasset embeds it), the Blender/Houdini model sources under `Pipeline Environment/ModelBank` (7.9 GB, only for editing models), and the archives.
- The `.uproject` EngineAssociation change to `5.8` applies in every variant.

**Decision (Aviv, 2026-10-06 ~16:10Z, DOCUMENTED):** the Git repository holds the Unreal project with the bank only, as a viewer of the saved GazaShujaiya environment. The GIS acquisition and Houdini trees stay out of Git for now. The small "can still regenerate" add-on in 10.4 (SourceData packages + Houdini install + relative profile paths) is not decided. This closes open question 25 as "Unreal-only for now".

## 11. Execution record (added 17:25Z)

The owner's decisions in sections 9 and 10 were executed by the review session on 2026-10-06 from 16:30Z on Aviv's direct instruction. The step-by-step record, receipts and the deletion plan are in `EXECUTION_LOG.md`, `Deleted/*.tsv` and `DeletePlan/` next to this file. First local commit 18473fb9 (24,102 files, 12,574 LFS objects). GazaRimal and the Sky Stage 3 folder follow in the second commit after the Sky operator releases. Classifications in section 3 describe the tree BEFORE these deletions.
