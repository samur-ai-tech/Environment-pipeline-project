# BANK-ASTRA-003 — Limited Inspection Result

## Scope and result

[measured: PREFLIGHT.json; LAUNCH.json; EXIT_CHECK.json] One native UI inspection in the Environmentpipeline project, under the lease of /root/bank_tier1_native_29. PID 13324 started at 2026-09-29 12:09:55 +03; the log showed "LogExit Exiting" at 12:32:13; at 12:32:35, no UnrealEditor/Houdini/HARS/hython process was found. The working map was /Engine/Maps/Templates/Template_Default, with eight actors and "All Saved" at the start and end. Every asset editor and the main editor were closed with Alt+F4 without a save prompt. No Content or map save was performed.

[documented: ../BANK_ASTRA_003_BRIEF_2026-09-29.md] The assignment covered bank candidates only. H0958 was not opened. No import/reimport, material editing, Houdini/HDA, cook/bake, BG1, Tier 1 build, M0/B1-C, Linear, or catalog change was performed. The owner ledger was not edited; release belongs to the manager.

## Identity and native UI readouts

[measured: 01_H0907_identity__1.jpg; 12_H0013_identity__1.jpg; 27_H0051_identity__1.jpg; OBSERVATIONS.json] Readouts came from the tooltip and Static Mesh Editor; they are not a test of collision behavior.

| Candidate | Exact object path | LODs / displayed LOD | Triangles | Vertices | UV channels | Material slots | Collision primitives | Nanite |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| H0907 | /Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0907_Arab_x3_fbx.SM_H0907_Arab_x3_fbx | 1 / 0 (Auto) | 3302 | 4835 | 2 | 1 | 1 | false |
| H0013 | /Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0013_Building_04.SM_H0013_Building_04 | 1 / 0 (Auto) | 44241 | 45927 | 2 | 4 | 1 | false |
| H0051 | /Game/Project/Shared/Bank_ME_v3/StreetFurniture/SM_H0051_Garbagebin.SM_H0051_Garbagebin | 1 / 0 (Auto) | 5180 | 4776 | 2 | 1 | 1 | false |

[measured: identity screenshots] All three display CTF_UseSimpleAndComplex and BlockAll. H0907 Approx Size is 1369 x 1369 x 1561 in the tooltip, and 1369 x 1368 x 1560 in the editor. H0051 displays 29 x 34 x 74. The readout did not label units; no exact local dimensions, contact, or bin-only height was inferred. H0013 Approx Size is not transcribed here; the numerical target is UNKNOWN.

## Materials: slot index, name, reference

[measured: native ordered Static Materials tooltip, Details Element indices, Browse selections, copied reference text files] The slot name and material match in the tooltip pairs. Copy Reference was performed with Ctrl+C on the material selected through Browse. No material was opened for editing.

| Candidate / Element | Slot name | Exact material object path | Receipt |
| --- | --- | --- | --- |
| H0907 / 0 | Arab_X3 | /Game/Project/Shared/Bank_ME_v3/Buildings/Arab_X3.Arab_X3 | H0907_MATERIAL_REFERENCE.txt |
| H0013 / 0 | Material_Building_04_1011 | /Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1011.Material_Building_04_1011 | H0013_MATERIAL_ELEMENT_0.txt |
| H0013 / 1 | Material_Building_04_1001 | /Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1001.Material_Building_04_1001 | H0013_MATERIAL_ELEMENT_1.txt |
| H0013 / 2 | Material_Building_04_1031 | /Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1031.Material_Building_04_1031 | H0013_MATERIAL_ELEMENT_2.txt |
| H0013 / 3 | Material_Building_04_1021 | /Game/Project/Shared/Bank_ME_v3/Buildings/Material_Building_04_1021.Material_Building_04_1021 | H0013_MATERIAL_ELEMENT_3.txt |
| H0051 / 0 | Street_Props_Pack__003 | /Game/Project/Shared/Bank_ME_v3/StreetFurniture/Street_Props_Pack__003.Street_Props_Pack__003 | H0051_MATERIAL_REFERENCE.txt |

## H0907

[measured: 02–11 screenshots; OBSERVATIONS.json] A whole building with a dome, pointed arches, blue-gray doors, and small latticed windows. Front and Back display a similar arrangement of openings. Top displays a polygonal roof outline around a round dome. No cultural significance or building use was inferred.

[measured: 07_H0907_top__1.jpg; 09_H0907_dome_front__1.jpg] A light patch with a sharp/stepped boundary against a darker area and a horizontal color band around the dome base are visible. This is a visible boundary in the preview, not a proven defect. There is one slot; the source of the difference in texture/UV/lighting was not resolved. The dome image is a moderate enlargement, not a UV close-up or texture-binding test. No automatic repair is recommended.

[measured: 03_H0907_floor_control_before__1.jpg; 05_H0907_floor_control_off__1.jpg; 04_H0907_front_floor_off__1.jpg; 08_H0907_bottom__1.jpg] The Floor was hidden using the O shortcut shown in the Preview Scene menu, with the checkbox verified before and after. The broad floor disappeared; a narrow lower edge remained. In Bottom view, the background is visible through much of the underside, between a polygonal outline and a central ring, with rectangular patches. Limited description: open underside in preview. This does not prove contact, enclosure, or suitability for building interiors. The Floor was restored before closing (11).

## H0013

[measured: 14_H0013_floor_before__1.jpg; 16_H0013_floor_off_control__1.jpg; 15–21 screenshots] The Floor was hidden and verified unchecked. The underside view shows outlines and separate pieces; the lower front shows openings/doors and narrow threshold-like strips. The broad preview floor is not evidence of integrated paving. The images do not establish the complete absence of base geometry or paving anywhere in the asset.

[measured: 18_H0013_front__1.jpg; 19_H0013_back__1.jpg; 20_H0013_top__1.jpg] The Front camera shows many rows of windows and ground-floor openings. The Back camera shows a broad wall with almost no openings. The roof has rectangular blocks and round tank-like forms; the plan steps back on one side. Camera names do not determine the semantic front.

[measured: 13; 22–25 screenshots and four reference receipts] All four slots were recorded in order. [not run: mesh-local coordinate measurement] Local bounds, signed contact, exact placement footprint, threshold depth, and semantic axis definitions remain UNKNOWN. The Floor was restored and "All Saved" documented before closing (26).

## H0051

[measured: 28_H0051_floor_before__1.jpg; 30_H0051_floor_off_control__1.jpg; 29–34 screenshots] The Floor was hidden and verified. The bin has brown panels and a light metal frame, with frame posts extending below the lower rail. Front/Left show protruding supports; Perspective shows the frame structure. Contact points were not measured, and four numerical contacts were not inferred from the projection.

[measured: 31_H0051_front__1.jpg; 32_H0051_left__1.jpg; 33_H0051_top__1.jpg] An upright bottle and additional bottle/trash shapes protrude above the upper frame and are included in the asset. Whole-asset height is not bin-only height. [measured: 34_H0051_bottom__1.jpg] A square brown base appears inside a gray frame; this is an underside view, not proof of watertightness or contact. One material is verified in 35 and the reference file. The Floor was restored, and Front and "All Saved" were documented in 36.

## Closure and file comparison

[measured: FINAL_VALIDATION.json; CONTENT_BEFORE.json; CONTENT_AFTER.json] Content: 5991 files before and after; 0 added, 0 removed, 0 changed by relative path / size / UTC mtime. SHA-256 was not claimed for all Content.

[measured: HASHES_BEFORE.json; HASHES_AFTER.json] All 174 SHA-256 hashes match: 172 Bank_ME_v3 files, the canonical CSV, and the measurement EDITOR_OWNER.txt. The BANK_CANDIDATE_INDEX_2026-09-28.csv catalog remained 495985E2697C4BBBBE735E80184C5E73DA5B94A4444FEB5BAFDCBC6621ADEA42. The owner measurement remained NONE; the bank lease stayed with the operator pending manager inspection and release.

[measured: SIDE_EFFECTS_BEFORE.json; SIDE_EFFECTS_AFTER.json; FINAL_VALIDATION.json] Within Saved: 4 added, 3 removed, 8 changed. CrashReportClient.ini and three log backups were added; three old log backups were removed; AutoScreenshot.png, Autosaves/PackageRestoreData.json, two Saved/Config/WindowsEditor files, two AutoSDKInfo files, the active log, and ShaderDebugInfo DDCKey changed. Project Config itself did not change. [inference] This pattern is consistent with normal session side effects and log rotation. The presence of CrashReportClient.ini does not prove a crash; SESSION_EDITOR.log contains a normal shutdown. Side effects were neither restored nor deleted.

## Limits and steps not run

[not run] Mesh-local values with units, signed contact, numerical footprint, bin-only height, collision behavior, performance/instances, semantic front/style/rights approval, Houdini connection, generation, scene save/reopen/regeneration, and every qualification or acceptance gate. No material editing, isolation, or wireframe was performed; the source atlas and texture binding were not checked in this session. The cause of the dome's color band is UNKNOWN.

[measured: OBSERVATIONS.json] View menus that disappeared when an action changed were not pursued. Only observed Browse controls and view shortcuts were used. Shortcuts initially failed while Details had focus during H0051 reconstruction; clicking the viewport enabled reconstruction. An early screenshotId error was dismissed without action. No editor automation was added. The initial journal statement "No broad integrated paving" describes the visible frame only, not a broad geometric conclusion.

[documented: brief] qualified=no, technical_eligible=false, generation_enabled=false remain unchanged. The inspection completed the requested views, identity, and materials; unavailable numerical data remains UNKNOWN. The manager is responsible for QA and releasing OWNER.

## Evidence index

OBSERVATIONS.json contains 38 records with time, window, accessibility text, and full screenshot files. Every path below is relative to this folder; __0 is usually the full screen, __1 the asset window, and __2/3 a tooltip/menu when present.

- 00_startup: 00_startup__0.jpg
- 01_H0907_identity: 01_H0907_identity__0.jpg, 01_H0907_identity__1.jpg, 01_H0907_identity__2.jpg
- 02_H0907_front_floor_on: 02_H0907_front_floor_on__0.jpg, 02_H0907_front_floor_on__1.jpg, 02_H0907_front_floor_on__2.jpg
- 03_H0907_floor_control_before: 03_H0907_floor_control_before__0.jpg, 03_H0907_floor_control_before__1.jpg, 03_H0907_floor_control_before__2.jpg, 03_H0907_floor_control_before__3.jpg
- 04_H0907_front_floor_off: 04_H0907_front_floor_off__0.jpg, 04_H0907_front_floor_off__1.jpg
- 05_H0907_floor_control_off: 05_H0907_floor_control_off__0.jpg, 05_H0907_floor_control_off__1.jpg, 05_H0907_floor_control_off__2.jpg, 05_H0907_floor_control_off__3.jpg
- 06_H0907_back: 06_H0907_back__0.jpg, 06_H0907_back__1.jpg, 06_H0907_back__2.jpg
- 07_H0907_top: 07_H0907_top__0.jpg, 07_H0907_top__1.jpg, 07_H0907_top__2.jpg
- 08_H0907_bottom: 08_H0907_bottom__0.jpg, 08_H0907_bottom__1.jpg, 08_H0907_bottom__2.jpg
- 09_H0907_dome_front: 09_H0907_dome_front__0.jpg, 09_H0907_dome_front__1.jpg
- 10_H0907_material_browse: 10_H0907_material_browse__0.jpg, 10_H0907_material_browse__1.jpg, 10_H0907_material_browse__2.jpg
- 11_H0907_floor_restored: 11_H0907_floor_restored__0.jpg, 11_H0907_floor_restored__1.jpg
- 12_H0013_identity: 12_H0013_identity__0.jpg, 12_H0013_identity__1.jpg, 12_H0013_identity__2.jpg
- 13_H0013_ordered_slots: 13_H0013_ordered_slots__0.jpg, 13_H0013_ordered_slots__1.jpg, 13_H0013_ordered_slots__2.jpg
- 14_H0013_floor_before: 14_H0013_floor_before__0.jpg, 14_H0013_floor_before__1.jpg, 14_H0013_floor_before__2.jpg, 14_H0013_floor_before__3.jpg
- 15_H0013_lower_perspective_floor_off: 15_H0013_lower_perspective_floor_off__0.jpg, 15_H0013_lower_perspective_floor_off__1.jpg
- 16_H0013_floor_off_control: 16_H0013_floor_off_control__0.jpg, 16_H0013_floor_off_control__1.jpg, 16_H0013_floor_off_control__2.jpg, 16_H0013_floor_off_control__3.jpg
- 17_H0013_lower_front_close: 17_H0013_lower_front_close__0.jpg, 17_H0013_lower_front_close__1.jpg, 17_H0013_lower_front_close__2.jpg
- 18_H0013_front: 18_H0013_front__0.jpg, 18_H0013_front__1.jpg, 18_H0013_front__2.jpg
- 19_H0013_back: 19_H0013_back__0.jpg, 19_H0013_back__1.jpg, 19_H0013_back__2.jpg
- 20_H0013_top: 20_H0013_top__0.jpg, 20_H0013_top__1.jpg, 20_H0013_top__2.jpg
- 21_H0013_bottom: 21_H0013_bottom__0.jpg, 21_H0013_bottom__1.jpg, 21_H0013_bottom__2.jpg
- 22_H0013_element0_browse: 22_H0013_element0_browse__0.jpg, 22_H0013_element0_browse__1.jpg, 22_H0013_element0_browse__2.jpg
- 23_H0013_element1_browse: 23_H0013_element1_browse__0.jpg, 23_H0013_element1_browse__1.jpg, 23_H0013_element1_browse__2.jpg
- 24_H0013_element2_browse: 24_H0013_element2_browse__0.jpg, 24_H0013_element2_browse__1.jpg, 24_H0013_element2_browse__2.jpg
- 25_H0013_element3_browse: 25_H0013_element3_browse__0.jpg, 25_H0013_element3_browse__1.jpg, 25_H0013_element3_browse__2.jpg
- 26_H0013_floor_restored: 26_H0013_floor_restored__0.jpg, 26_H0013_floor_restored__1.jpg
- 27_H0051_identity: 27_H0051_identity__0.jpg, 27_H0051_identity__1.jpg, 27_H0051_identity__2.jpg
- 28_H0051_floor_before: 28_H0051_floor_before__0.jpg, 28_H0051_floor_before__1.jpg, 28_H0051_floor_before__2.jpg, 28_H0051_floor_before__3.jpg
- 29_H0051_perspective_floor_off: 29_H0051_perspective_floor_off__0.jpg, 29_H0051_perspective_floor_off__1.jpg
- 30_H0051_floor_off_control: 30_H0051_floor_off_control__0.jpg, 30_H0051_floor_off_control__1.jpg, 30_H0051_floor_off_control__2.jpg, 30_H0051_floor_off_control__3.jpg
- 31_H0051_front: 31_H0051_front__0.jpg, 31_H0051_front__1.jpg, 31_H0051_front__2.jpg
- 32_H0051_left: 32_H0051_left__0.jpg, 32_H0051_left__1.jpg, 32_H0051_left__2.jpg
- 33_H0051_top: 33_H0051_top__0.jpg, 33_H0051_top__1.jpg, 33_H0051_top__2.jpg
- 34_H0051_bottom: 34_H0051_bottom__0.jpg, 34_H0051_bottom__1.jpg, 34_H0051_bottom__2.jpg
- 35_H0051_material_browse: 35_H0051_material_browse__0.jpg, 35_H0051_material_browse__1.jpg, 35_H0051_material_browse__2.jpg
- 36_H0051_floor_restored: 36_H0051_floor_restored__0.jpg, 36_H0051_floor_restored__1.jpg
- 37_editor_before_close: 37_editor_before_close__0.jpg
