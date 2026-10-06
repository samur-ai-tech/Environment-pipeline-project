# BANK-ASTRA-004 result

[measured: PREFLIGHT.json; LAUNCH.json; EXIT_CHECK.json] One editor session, PID 3808, launched 2026-09-29 12:55:58 +03 into /Engine/Maps/Templates/Template_Default. Native UI displayed Template_Default, 8 actors and All Saved before and after inspection. Three asset editors and Unreal closed through Alt+F4 without save prompts. Normal LogExit at 13:02:17; zero UnrealEditor/Houdini/HARS/hython at 13:02:37. Owner ledgers were not edited.

## Current bounds

[documented: INSTALLED_TOOL_SOURCE.txt] Installed UE 5.8 EditorToolset static_mesh.py:101-110 documents a local-space axis-aligned bounding box and calls mesh.get_bounding_box(). The observed tool and native labels do not establish physical length units: units remain UNKNOWN. No signed support/contact or usable footprint is established.

| Mesh | Min X/Y/Z | Max X/Y/Z | Valid | Import comparison |
| --- | --- | --- | --- | --- |
| SM_H0907_Arab_x3_fbx | -680.353271484375, -700.4720458984375, 0.6762058734893799 | 688.6864013671875, 668.2713623046875, 1561.33740234375 | True | Exactly equal |
| SM_H0013_Building_04 | -1273.8673095703125, -1081.9207763671875, -0.3545195758342743 | 1615.8203125, 1049.0091552734375, 4868 | True | Exactly equal |
| SM_H0051_Garbagebin | -12.837084770202637, -17.898235321044922, 3.5086711136500526e-07 | 16.559925079345703, 16.53656768798828, 74.40184783935547 | True | Exactly equal |

[measured: mcp/001–003; COMPARISON.json] Exact raw floating-point representations and both old/current receipt paths are retained in COMPARISON.json.

[measured: 01_H0051_build_scale__1.jpg; 02_H0013_build_scale__1.jpg; 03_H0907_build_scale__1.jpg; OBSERVATIONS.json] Each mesh displayed LOD 0 > Build Settings > Build Scale with three values 1.0, 1.0, 1.0. All Saved displayed. No length unit labels appeared. Values/settings were not edited; search filters only.

## Direct material dependencies

[measured: mcp/004–027; COMPARISON.json] Six assigned packages resolve as Material. Twelve returned direct packages all resolve as Texture2D. No missing asset, redirector class, parent material, function or other branch was returned by this query. Each ordered dependency list exactly equals IMPORT_RESULTS_v3.json.material_texture_deps_after_save. This is the direct registry query using default AssetRegistryDependencyOptions, not recursive closure or shader pin/channel proof.

- `/Game/Project/Shared/Bank_ME_v3/Buildings/Arab_X3`:
  - `/Game/Project/Shared/Bank_ME_v3/Buildings/Arab_x3_Diffuse_Map_9e424ef08c1f` — Texture2D
- `/Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1011`:
  - `/Game/Project/Shared/Bank_ME_v3/Buildings/B04_M02_lbedoTransparency_c286d2b07cbd` — Texture2D
  - `/Game/Project/Shared/Bank_ME_v3/Buildings/B04_M02_Normal_ba61051ad683` — Texture2D
- `/Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1001`:
  - `/Game/Project/Shared/Bank_ME_v3/Buildings/B04_M01_lbedoTransparency_feb997124e3f` — Texture2D
  - `/Game/Project/Shared/Bank_ME_v3/Buildings/B04_M01_Normal_c3ebb6845660` — Texture2D
- `/Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1031`:
  - `/Game/Project/Shared/Bank_ME_v3/Buildings/B04_M04_lbedoTransparency_e0ebfc1dbb4b` — Texture2D
  - `/Game/Project/Shared/Bank_ME_v3/Buildings/B04_M04_Normal_b6e59e496bae` — Texture2D
- `/Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1021`:
  - `/Game/Project/Shared/Bank_ME_v3/Buildings/B04_M03_lbedoTransparency_e52816c231d7` — Texture2D
  - `/Game/Project/Shared/Bank_ME_v3/Buildings/B04_M03_Normal_a4f020a17487` — Texture2D
- `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/Street_Props_Pack__003`:
  - `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/Arabic_Assets_01_AlbedoTransparency_1011_4c9672e5e1dd` — Texture2D
  - `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/Arabic_Assets_01_Emission_1011_0841cebf1802_albedo_4881256d84f693` — Texture2D
  - `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/Arabic_Assets_01_Normal_1011_99d47d234c4e` — Texture2D

## Closure and limits

[measured: FINAL_VALIDATION.json; CONTENT_BEFORE.json; CONTENT_AFTER.json] Content has 5,991 files before and after; zero added/removed/changed by relative path, size and UTC mtime. All 174 SHA-256 checks match: 172 Bank_ME_v3 packages, canonical CSV and measurement owner. CSV remains 12225013B06810665B5E429299F1CD9E9931588AEAE4B1FFE1A33282B5719098. Project Config unchanged.

[measured: SIDE_EFFECTS_BEFORE.json; SIDE_EFFECTS_AFTER.json; FINAL_VALIDATION.json] Saved-only differences: 4 added, 3 removed, 8 changed. These include log rotation, CrashReportClient.ini, editor user settings, AutoScreenshot, PackageRestoreData, AutoSDKInfo and shader debug DDC key. None were reverted/deleted. [inference] Pattern is consistent with session side effects; CrashReportClient.ini presence alone does not establish a crash. SESSION_EDITOR.log records normal exit.

[not run] Physical units verification, signed support contact, footprint, bin-only height, semantic forward axis, texture fidelity/channels, recursive dependencies, collision behavior, rights expansion, visual approval, Houdini connection/generation, qualification, acceptance and save/reopen/regenerate tests. No import, setters, Content/map save, Houdini/HDA, BG1/CAT1/INST1/Tier1, catalog or source edits. qualified=no, technical_eligible=false and generation_enabled=false remain protected.

All numbered inspection/closure steps completed within the lease. Remaining evidence limitations are explicitly UNKNOWN above. Manager alone reviews and releases the bank lease.

## Raw evidence

- PREFLIGHT.json, LAUNCH.json, EXIT_CHECK.json
- BATCH_READONLY.json, BATCH_DIRECT_CLASSES.json and mcp/001–027 raw request/reply receipts
- INSTALLED_TOOL_SOURCE.txt, COMPARISON.json
- OBSERVATIONS.json and 00_startup, 01_H0051_build_scale, 02_H0013_build_scale, 03_H0907_build_scale, 04_before_exit screenshots
- CONTENT_BEFORE/AFTER.json, HASHES_BEFORE/AFTER.json, SIDE_EFFECTS_BEFORE/AFTER.json, FINAL_VALIDATION.json
- SESSION_EDITOR.log
