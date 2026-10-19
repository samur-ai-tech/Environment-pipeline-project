# Governance record

Append-only. Each entry is dated and signed by Aviv's decision. Newer entries supersede older ones only where they say so. Rules of operation live in AGENTS.md; this file records WHO decides and the standing principles. README.md links here.

## 2026-10-18 — Governing authority and the map principle (Aviv)

Authority: Aviv directs operators directly. There is no manager session.

Manager switch: the cc37d4d2 → 913c2312 switch is cancelled. Both session ids are retired as managers.

Principle: Maps are disposable outputs. The product is the generation system, not any single map. The goal is a system that generates good-looking maps continuously with no manual work. Any map may be accepted as-is, regenerated, or deleted. Generators, the model bank, and pipeline code are NOT disposable and must be protected.

Deliberate differences with other files (not edited by this record; Aviv's instruction):
- AGENTS.md (live line 23, HEAD line 12): still names Claude session cc37d4d2 as SOLE manager and MANAGER_HANDOFF_2026-10-06.md as handoff of record. This record supersedes the manager statement. The handoff-of-record question is not decided here.
- Staging\ManagedSystemsAstra_2026-10-04\ASSIGNMENTS.json field manager_thread_id = cc37d4d2-3d62-4f53-b689-28432b5527ae: a record read by sealed code; left unchanged on purpose. The managed bank route that checks it stays as it is until Aviv decides on that route.
- Staging\MANAGER_HANDOFF_2026-10-07.md:13-14: states that AGENTS.md and ASSIGNMENTS.json manager_thread_id still name cc37d4d2. This record supersedes the manager statement.
- Staging\MANAGER_HANDOFF_2026-10-06.md:3: written by "the current sole manager", cc37d4d2. Superseded here as to the manager.
- Staging\MANAGER_HANDOFF_2026-10-06.md:11: the identity-switch procedure for a successor manager. Not to be run; the switch is cancelled.
- Staging\CURRENT_STATE.md:6: entry point "decided/measured: Claude manager session cc37d4d2". Superseded here as to the manager.
- Staging\WORK_PLAN.md:6: plan of record "decided: Claude manager session cc37d4d2". Superseded here as to the manager.
- Staging\PROJECT_STATUS_2026-10-06.md:3: written by "the project manager (Claude Code session cc37d4d2)". Superseded here as to the manager.
- Staging\Manager_2026-10-07\ (e.g. DECISIONS_20261007_AVIV.json:3 manager_session_id 913c2312; MANAGER_BULLETIN.md:9 "Manager: Claude Code session 913c2312"; ASSIGNMENT_*.json and OUTBOX messages): name 913c2312 as manager. Superseded here; 913c2312 is retired as manager.

Source: audit Audit16_2026-10-17_1346Z, checklist item RC-03; findings F-T02-01, F-T09-03.

Recorded by: Claude Code (Opus 5.5) on Aviv's written approval, 2026-10-18.

## 2026-10-18 — Consolidated decisions on the Audit16 repair checklist (Aviv)

Recorded on Aviv's written decisions of 2026-10-18. This entry restates the 2026-10-18 authority entry above and adds Part A and Part B decisions. Nothing in this entry executes anything; each item still runs only when Aviv approves its execution.

### Principle

Maps are disposable outputs. The product is the generation system. Goal: a system that generates good-looking maps continuously with no manual work. Any map may be accepted, regenerated or deleted. Generators, the model bank and pipeline code are NOT disposable.

### Part A (prerequisites)

1. RC-03 — Authority = "Aviv directs operators directly." No manager session. The cc37d4d2 → 913c2312 switch is cancelled; both are retired.
2. RC-01 — If Houdini, hython, HARS or Unreal is found running, stop and ask Aviv.
3. RC-05 — Accept the El Wahat disk map (6a4d8bea) as baseline. No restore. Map `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Areas\ElWahatEgypt_29176036_29602273_4km\BankIntegration_v015\L_ElWahatEgypt_29176036_29602273_4km.umap`, sha256 `6a4d8beaa4d119c0a0efcfb8b373a5c86f6082e2de0f309e15e69da07d69f332` (on disk 2026-10-18: matches).
4. RC-06 — Every Unreal start writes ParallelEditors\EDITOR_<pid>.json, and every map save is preceded by a byte copy to the task's Before\ folder.
5. RC-09 — Accept the Shujaiya 2026-10-17 regeneration (0d67d2c7 / cebf0851 / eddce466). Done by Codex threads under Aviv's direct instruction.
   - Map `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Areas\GazaShujaiya\BankIntegration_v015\L_GazaShujaiya_BankIntegration.umap`, sha256 `0d67d2c7dbf32f0af78264c6ccbb8c9611378558275f4bd1dda1c77158343bd6` (on disk: matches).
   - Asset `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\ModelBank\HDA\GeoCity_city_v015_PermanentBank.uasset`, sha256 `cebf08514388c00e762e9174193c9cbfccbbfee0546f6c5f67bfac0706b1573a` (on disk: does NOT match; see open points).
   - Source `C:\Users\USER\Documents\Pipeline Environment\Houdini\GeoCity_city_v015_PermanentBank\revisions\20261017_stable_bank_instancers_v001\GeoCity_city_v015_PermanentBank_StableBankInstancers_v001.hdalc`, sha256 `eddce4669220514c6c554347267df0e7cab0610477a7fefab41cbbc272c0420b` (on disk: matches).
6. RC-11 — Not decided. First screenshots of Shujaiya in Unreal and proof the generator revision cooks; Aviv's go before opening any editor.
7. RC-12 — Aviv is the bank owner. Only an agent Aviv assigns to a task may change the bank or AREA_PROFILE.json. All other bank owners are retired.
8. RC-13 — Pre-approved: a KY 4km regeneration may change the Paz Farm clone.
9. RC-14 — Do not redo the El Wahat manual steps. Recorded as a system gap to automate. The steps (`C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\ElWahatEgypt_SESSION_HANDOFF_2026-10-12.md:161-165`, §3o): a regeneration re-bakes the 3 OSM `Bldg_` blocks (still in the source package, still assembled by EW v002) on top of the station, so after the split they are removed again (record first, `Tools/remove_actors.py`). An instantiate run must list the 14 station StaticMeshActors in `expected_outside_ledger_classes` (BP_EnvironmentSky_C + 14 x StaticMeshActor). Redo: compact_buildings_v2 -> split_buildings -> split_shells (new shell folder) -> remove the 3 blocks -> props trim -> road_uv_fix/rebuild + Bake save -> road_asphalt set; the track MI is unchanged.

### Part B

1. RC-35 — Managed path not needed. Menu path only. ASSIGNMENTS.json untouched.
2. RC-69 — Maintenance owner of the reference Tools and Content\Python = Aviv, through an agent he assigns per task.
3. RC-31 — Aviv will decide the 93 governance-force files one by one (list to be sent).
4. RC-46 / RC-46a / RC-46b — No winner picked now. Task: verify what actually works in NEW_ENVIRONMENT_PLAYBOOK.md, then update CONTRACT.md from the verified results. The stop at CONTRACT.md:9 stays until that update is done and Aviv approves it. PCG vegetation for new areas: yes.
5. RC-40 — Lebanon kept aside as a scaffold; not retried now.
6. RC-71 — One template Tools folder to be proposed with reasons.
7. RC-72 — The create-area tool must set NorthOffset automatically for every new area (per instance, no class-default change); existing maps get it at their next regeneration.
8. RC-50 — Keep the vendor packs (OwnedPackSources, NativeIntake).
9. RC-76 — Remove the 150 ME1 texture copies only after proof that nothing references them; proof first, removal a separate step.
10. RC-78 — Keep the RunExisting backup.
11. RC-51 — Compare the nested repository with the main project; differences to Aviv before he decides.
12. RC-53 — English is canonical. All project documents are in English.
13. RC-79 — Yes: 260-character path limit for Staging and Content\Project\Areas.
14. RC-45 — Classify the 55 Houdini files (source / evidence / backup) for Aviv.
15. RC-39 — Not now.
16. RC-82 — No.

### Open points stated by the record (not decided here)

- RC-09 asset: the shared asset on disk since 2026-10-18 10:05Z is sha256 `f5e9c6c828e17895b2fa69672601f49034e846d7990c49166cc63f4f20c9bfeb` (Staging\HoudiniBankFixes_2026-10-18\, thread 01a14e6b, "Direct Aviv implementation request"), embedding `revisions/20261018_normal_semantics_v001/20261017_stable_bank_instancers_v001/GeoCity_city_v015_PermanentBank_StableBankInstancers_v001.hdalc`, FileMD5 e2da782f… (exists, matches; sha256 3e782114…). cebf0851 has a byte copy in `Staging\HoudiniBankFixes_2026-10-18\Before\Content\Project\Shared\ModelBank\HDA\`. Aviv's decision names cebf0851 / eddce466. Which asset the Shujaiya baseline names is for Aviv to confirm.
- RC-09 digest: none named; the Shujaiya profile now carries catalog_sha256 6f9ee7ba… (thread 01a14e6b, today). For Aviv to confirm.
- RC-12: thread 01a14e6b wrote the bank table, five AREA_PROFILE.json files and five HDA assets today; whether it was an agent Aviv assigned is for Aviv to confirm.
- RC-05: the history row in the El Wahat handoff §0 is NOT written in this step (Aviv: "only write the record").
- RC-11: cook proof target (eddce466 vs the live source 3e782114…) is for Aviv to confirm.

### Deliberate differences with other files (not edited)

- AGENTS.md:23, :25 (sole managers cc37d4d2, 01a10789); :11, :16 (manager identity, "designated manager"); :29, :31, :33, :35 (bank chat 01a1067c; "Root owns" profiles). Superseded by RC-03, RC-12.
- Staging\ManagedSystemsAstra_2026-10-04\ASSIGNMENTS.json:5, :104 (cc37d4d2); :132 (profiles owner 01a10789); :148 (bank 01a1067c); :197, :201, :207. Untouched (RC-35).
- Docs\Bank\RULES.md:14-16, Docs\Bank\CONNECTION.md:30 ("establish the actual owner"; "bank owner"). Owner is Aviv (RC-12).
- Pipeline Environment\CONTRACT.md:9 stop stays; :240 unchanged until the RC-46 update.
- Staging\ElWahatEgypt_SESSION_HANDOFF_2026-10-12.md:11-12 still fc89bf00 (RC-05); :169 §4 item 0, a used 2026-10-12 regeneration approval.
- 64052d88 called current only in dated 2026-10-08 reports (e.g. Staging\Manager_2026-10-07\REPORTS_INBOX\REPORT_three_task_coordination_01a1161b.md:72,84,93; Staging\VegetationCompletionManager_2026-10-07\RUN_HANDOFF_VEGETATION.md:5). Superseded by RC-09.
- Staging\ParallelEditors\README.md:3, :31 ("the manager"); :7 guard covers generation start only, so RC-06 is procedural.
- Staging\HoudiniBankFixes_2026-10-18\RESULT.md:81 ("the existing manager" cc37d4d2).

Source: Audit16_2026-10-17_1346Z\FINAL\FINAL_REPAIR_CHECKLIST.md, Parts A and B.

Recorded by: Claude Code (Opus 5.5) on Aviv's written decisions, 2026-10-18.

## 2026-10-18 — Answers to the open points (Aviv)

Recorded on Aviv's written answers of 2026-10-18. These close the open points of the consolidated entry above. Nothing in this entry executes anything.

### Baseline of record for GazaShujaiya (closes RC-09 open points)

- Map: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Areas\GazaShujaiya\BankIntegration_v015\L_GazaShujaiya_BankIntegration.umap`, sha256 `0d67d2c7dbf32f0af78264c6ccbb8c9611378558275f4bd1dda1c77158343bd6` (on disk 2026-10-18: matches).
- Shared generator asset: `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Content\Project\Shared\ModelBank\HDA\GeoCity_city_v015_PermanentBank.uasset`, sha256 `f5e9c6c828e17895b2fa69672601f49034e846d7990c49166cc63f4f20c9bfeb` (on disk 2026-10-18: matches), saved 2026-10-18 10:05Z by Staging\HoudiniBankFixes_2026-10-18 (thread 01a14e6b, assigned by Aviv). Embedded source: `C:\Users\USER\Documents\Pipeline Environment\Houdini\GeoCity_city_v015_PermanentBank\revisions\20261018_normal_semantics_v001\20261017_stable_bank_instancers_v001\GeoCity_city_v015_PermanentBank_StableBankInstancers_v001.hdalc`, sha256 `3e7821146c02fc5362c17bbf46456658a88242a029e33c68221956eee601edef` (on disk 2026-10-18: matches), FileMD5 `e2da782fba727c29ab99542f6ff5cd87` (embedded in the asset; equals the source file's MD5 on disk). Earlier asset cebf0851 (source eddce466) is historical; its byte copy is at `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\HoudiniBankFixes_2026-10-18\Before\Content\Project\Shared\ModelBank\HDA\GeoCity_city_v015_PermanentBank.uasset` (sha256 `cebf08514388c00e762e9174193c9cbfccbbfee0546f6c5f67bfac0706b1573a`, matches). This supersedes the asset and source lines of item 5 in Part A of the consolidated entry above; its map value 0d67d2c7 is unchanged.
- Bank: AnyArea table (`/Game/Project/Shared/ModelBank/DT_EnvironmentBank_AnyArea`) catalog digest `6f9ee7bacd0622d1e1ac8ca1628618f16806b66dd5edd7e9230be4ff1fe9bd80` (catalog_sha256 in the profile), Shujaiya AREA_PROFILE.json `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\ModelBank\GazaShujaiyaIntegration_2026-10-02\AREA_PROFILE.json` sha256 `9ef884cf2db3dfbb267b0bdd906b6f1d16862b8c599baccefd78c65c0235f7d5` (on disk 2026-10-18). The 2026-10-18 bank, profile and HDA changes by thread 01a14e6b are valid (Aviv).
- Cook-proof target when RC-11 runs: the new source 3e782114….

### Answers

1. RC-09 — Shujaiya asset: "keep the NEW version on disk (f5e9c6c8). It has improvements. Record it as the current baseline. No restore."
2. RC-12 — Thread 01a14e6b: "yes, I asked for it. Its bank, profile and HDA changes this morning are valid."
3. RC-11 — Cook proof target: "the new source (3e782114), since we keep the new version."
4. RC-05 — El Wahat handoff: "no history row needed. The governance record is enough." El Wahat handoff §0 keeps fc89bf00 as a historical value; the record governs.
5. RC-01 — Houdini PID 11448: "leave it open. Do not touch it." (Measured at recording, 2026-10-18 ~12:35Z: no process with PID 11448 was running, and no Houdini, hython, HARS or Unreal process was running; no process was touched.)
6. RC-45 — The 9 Houdini source files (bank scene + 8 ModularBuildingSet HDAs): "explain each one to me first: what it does, how it differs from the others, and which are relevant. Then I decide."
7. RC-11 — Visual check of Shujaiya: "not now."
8. Q11 — Generation authority: "standing permission to regenerate, as long as an approved generator and approved bank are used." Standing authorization: regeneration is permitted without a per-run decision whenever the generator and the bank in use are ones Aviv approved (see RC-11 for the generator; the bank as of 2026-10-18 per item 2).
9. Q12 — Map acceptance: "I look at every map myself."
10. Q3 — Sealed code: "may be changed only with my approval per item. Also list the 2026-10-07/08 backlog for me to approve or reject one by one."
11. RC-07 — Surface-painting handoff: "leave it as is."
12. RC-60 — RoadBLD: "open it to all areas, not Gaza only."
13. RC-43 — Rimal and Iran last map states: "allowed to delete." The deletion itself is a separate step and needs Aviv's go.
14. Q18 — Issue register: "one file inside the project (not Linear). Yes, put the handoffs that are not in git into git. Explain to me what SourceComparison_2026-10-18 is." No git commit is made by an agent; the git step waits for Aviv's go.
15. RC-76 — ME1 proof: "later."
16. RC-71 — Template folder: "build one template from everything relevant in both the El Wahat and the Karmei Yosef tool sets, with the NorthOffset defect fixed and the _aviv clients excluded. Show me the proposed list (file, source folder, why) before creating anything."
17. RC-51 — Nested repository: "merge. First show me exactly what exists in the nested copy and not in the main project, and the merge plan. Do not merge until I approve."
18. RC-31 — The 93 files: "you mark each one (historical / superseded by the record / still in force) and show me the full list for review."

### Pending for Aviv (not decided)

- RC-11 ratification of the generator and the seal (after the visual check, which is "not now").
- Items 6, 10 (backlog list), 14 (SourceComparison explanation), 16, 17, 18: explanations and proposals to be shown first.

### Deliberate differences with other files (not edited)

- Staging\ElWahatEgypt_SESSION_HANDOFF_2026-10-12.md:11-12: still names fc89bf00 as the current map. Historical value; the record governs (item 4, RC-05).
- Docs\Bank\RULES.md:15-16 ("establish the actual owner"; distinct owners); Docs\Bank\CONNECTION.md:30 ("the bank owner's existing transaction"). Owner is Aviv (RC-12); thread 01a14e6b was assigned by Aviv (item 2).
- AGENTS.md:11, :16 (bank documentation; "designated manager"); :23, :25 (sole managers cc37d4d2, 01a10789); :31, :33, :35 (bank chat 01a1067c; "Root owns" profiles). Superseded by RC-03, RC-12.
- Staging\ManagedSystemsAstra_2026-10-04\ASSIGNMENTS.json:5, :104 (cc37d4d2); :132 (profiles owner 01a10789); :148 (bank 01a1067c). Untouched (RC-35).
- Pipeline Environment\CONTRACT.md:9: the stop stays until the RC-46 update.
- Content\Python\geocity_editor_action.py:139 and Content\Python\geocity_roadbld_clip.py:96: RoadBLD area list is ('GazaRimal', 'GazaShujaiya', 'Lebanon_33390778_35506639_4km'). RC-60 decided (all areas); code untouched.
- Staging\StandaloneSurfacePainting_2026-10-07\CLEAN_HANDOFF.json: left as is (item 11, RC-07).
- Files naming cebf0851 / eddce466 as the current asset / source (superseded by the baseline above): Staging\ConnectionRepair_2026-10-17\RESULT.md:12-13, FINAL_STATE.json:37, :55, HDA_SOURCE.json:5, REFERENCES.md:47, HDA_REVIEW.md:20, receipts\APPLIED_DEPENDENCIES.json:8, :36, receipts\CLIENT_apply_dependencies_20261017T185224Z.json, receipts\PREFLIGHT_PID24592/24736/35412.json; Staging\BankGapValidation_2026-10-18\RESULT.txt:18, :20 (also its NATIVE_EVIDENCE.json, BASELINE_VERIFICATION.json, PREFLIGHT_PID24952.json); Staging\SourceImplementation_2026-10-18\BASELINE.json:69 and GeoGenius\COMPARISON.md; Staging\BankMarkedRemoval_2026-10-18\receipts\PREFLIGHT_PID31128/34524.json; Staging\SourceComparison_2026-10-18\ reports in 09_city_generator, 10_citysample, 11_titan, 12_geogenius_short (11 files).

Recorded by: Claude Code (Opus 5.5) on Aviv's written answers, 2026-10-18.

## 2026-10-19 — Execution of the decided items (Aviv's order "Work")

Executed on Aviv's order of 2026-10-19 to carry out everything already decided, without further questions. Each item lists its evidence folder under C:\Users\USER\Documents\Environmentpipeline_Audit\Audit16_2026-10-17_1346Z\Repairs\Executed_2026-10-19\.

1. RC-31 — Approval of the marked list (Aviv, 2026-10-19: "Work" after review of 93_FILES_MARKED.md): 40 files received a top banner line (17 HISTORICAL, 23 SUPERSEDED by this record), 42 .json files and 1 sealed-read file are recorded in Docs\CLOSURE_INDEX.md only, 1 was already bannered, 8 "Aviv to confirm" rows and 1 still-in-force row were not edited. Index: Docs\CLOSURE_INDEX.md. Evidence: MARK\.
2. RC-71 — Template folder created: Staging\Templates\NewAreaTools_v001\ (87 scripts + README; 25 verbatim, 61 fixed, 1 new area_constants.py; NorthOffset -90 per instance in create_area.py with the NOAA sun check; no _aviv clients; never run in place). Playbook and SKILL.md lines still point at the KY task Tools (listed in the template README); not repointed. Evidence: TEMPLATE\.
3. RC-51 — Content merge of the nested clone: its AGENTS.md copied verbatim to Docs\PERSONAL_PREFERENCES_from_nested_clone.md; the nested folder and its .git are left in place for Aviv to remove. Evidence: DOCS\.
4. Q18 — Issue register created: Docs\ISSUE_REGISTER.md (113 rows: 93 open, 20 closed). README.md links the register, the closure index and the template. Evidence: DOCS\.
5. Q18 — Git: the untracked handoffs and today's documentation were committed (see Part 2; commit: see Repairs\Executed_2026-10-19\GIT\COMMIT.txt). No push.
6. Correction: the answers entry of 2026-10-18 (item 12 and its deliberate-differences line on Content\Python) labels RoadBLD "RC-60"; in FINAL_REPAIR_CHECKLIST.md RoadBLD is RC-56 and RC-60 is a different item (cross-reference of the two vegetation routes). The decision ("open to all areas") stands; it refers to RoadBLD. The sealed code (Content\Python\geocity_editor_action.py:139, geocity_roadbld_clip.py:96) is unchanged until Aviv approves that sealed change per item.
7. Observed, not edited: AGENTS.md (working copy, uncommitted) now opens with a 2026-10-18 paragraph (written by another process) that appoints chat 01a14f23 as "successor manager" of the Houdini-bank loop. Line 5 reads: "Aviv directly appointed review chat `01a14f23-30c9-7172-ad49-2909ffeef359` as successor manager of the Houdini-bank run/review/repair loop." This record (entries of 2026-10-18) states that there is no manager session and that Aviv directs operators directly. The AGENTS.md paragraph is a deliberate difference not resolved here.
8. Next action under this order: one regeneration of Karmei Yosef 4 km with the approved generator and bank (standing permission, Q11; RC-13 pre-approved), screenshots for Aviv, no manual steps. Its evidence will be in REGEN\.

Recorded by: Claude Code (Opus 5.5) on Aviv's order, 2026-10-19.
