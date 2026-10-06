# BANK-ASTRA-002 — H0958 isolated material proof

**Result:** P1 removes the opaque fill between palm leaflets in the inspected Front and Back views, and the two saved proof packages survive a fresh-process reopen. The original H0958 asset and its dependencies remain unchanged. This is an experimental material proof, **not role qualification or acceptance**. [measured: `OBSERVATIONS.json`, labels 01–02, 11–12, 22–26; `FINAL_VALIDATION.json`]

Operator: `01a0e820-c6d4-7702-8e7b-55fd20f9b020`. Task: `BANK-ASTRA-002`. Engine: **5.8.2, CL 56702186**. Exclusive lease began 2026-09-29 02:57:44 with a 04:00 deadline. Both owned editor processes are closed. The manager released the lease as **OWNER=NONE at 03:26:10 Israel time**; the operator verified the ledger and closed PIDs in `RELEASE_ACK.json`. This task has no permission to reopen the editor. [measured: `LAUNCH_1.json`, `LAUNCH_2.json`, `FINAL_VALIDATION.json`, `RELEASE_ACK.json`; documented: `../EDITOR_OWNER.txt`]

## What was changed

The original source candidate remains `current_Project__Shared__Bank_ME_v3__Vegetation__SM_H0958_CoconutPalm`; its catalog identity was not changed. Native **Asset Editor → File → Save As** created copies directly at the two permitted destinations. The command replaced the source editor tab with the derivative tab, while preserving the source package and source mesh references. All 26 protected hashes were rechecked after each copy, before edits. No `.uasset` was copied into Content through the filesystem. [measured: `AFTER_MATERIAL_COPY.json`, `AFTER_MESH_COPY.json`, `OBSERVATIONS.json`, labels 06–08]

Only these new packages were saved:

- `/Game/Developers/USER/ModelBankProof/H0958_MaterialRepair_20260929/SM_H0958_CoconutPalm_Proof.SM_H0958_CoconutPalm_Proof`
- `/Game/Developers/USER/ModelBankProof/H0958_MaterialRepair_20260929/M_H0958_Leaf_Proof.M_H0958_Leaf_Proof`

| Property | P0 original | P1 saved proof / fresh reopen |
|---|---|---|
| Material Domain | Surface | Surface |
| Blend Mode | Opaque | Masked |
| Shading Model | Default Lit | Default Lit |
| Two Sided | Off | Off |
| Leaf albedo RGB | Base Color | Base Color, unchanged |
| Leaf albedo A | Unconnected | Opacity Mask |
| Leaf normal RGB | Normal | Normal, unchanged |
| Opacity Mask Clip Value | Not separately read before changing blend mode | 0.3333, never edited; persisted |
| Mesh Element 0 | Original_Submesh_0 | Original_Submesh_0, unchanged |
| Mesh Element 1 | Original_Submesh_1 | M_H0958_Leaf_Proof |
| Element 1 imported slot name | Original_Submesh_1 | Original_Submesh_1 retained |

[measured: `OBSERVATIONS.json`, labels 04–05, 09–10, 19, 24–26]

The albedo A connection was made through the native pin context command **Connect To Opacity Mask**. Two initial drag attempts did not create a connection; the final graph visibly confirms the correct wire. Apply completed on the proof material. No visible material error appeared, and the two preserved session logs contain no matches for the recorded material/shader compile-error patterns. This is not a claim that every unrelated log warning was audited. [measured: `OBSERVATIONS.json`, labels 09–10, 25; `FINAL_VALIDATION.json`]

**P2 was not run:** the paired P1 Back view retained the leaflets and did not show the specific back-side disappearance that would trigger the conditional Two Sided experiment. This observation does not certify every leaf normal or view angle. [measured: labels 11–12; not run: H0958-P2]

## Visual comparison

| View | Original P0 | Masked P1 | Fresh process |
|---|---|---|---|
| A — Front | [P0-A](LIVE/01_P0_A_FRONT__1.jpg) | [P1-A](LIVE/11_P1_A_FRONT__1.jpg) | [Reopen-A](LIVE/22_REOPEN_A_FRONT__1.jpg) |
| B — Back | [P0-B](LIVE/02_P0_B_BACK__1.jpg) | [P1-B](LIVE/12_P1_B_BACK__1.jpg) | [Reopen-B](LIVE/23_REOPEN_B_BACK__1.jpg) |

P0 has broad, continuous opaque card surfaces. P1 exposes separate leaflets and the gaps between them; the color broadly follows the visible leaflets in these views. Both orientations retain a crown, and the fresh process reproduces the result. This supports the alpha-wiring diagnosis. It does not establish full UV fidelity, realistic leaf shading, botanical suitability, or final appearance in GazaRimal. [measured: comparison images; inference: bounded UV/color alignment]

Comparison recipe: Front orthographic, Lit, LOD Auto displaying LOD 0; focus the mesh viewport, `Alt+H`, `F`, then scroll -240 and -1200 at crown coordinate (397,427), with the original viewport width restored. Back uses `Alt+Shift+H` at the same zoom. Numeric camera position, zoom and exposure were not measured; no shared preview profile or lighting setting was edited. The screenshots document the actual framing and lighting. The grid platform is the editor preview floor. [measured: `OBSERVATIONS.json`]

## Dependencies and mesh observations

Protected prefix: `/Game/Project/Shared/Bank_ME_v3/Vegetation/`.

- Original mesh: `SM_H0958_CoconutPalm.SM_H0958_CoconutPalm`.
- Trunk material, unchanged: `Original_Submesh_0.Original_Submesh_0`.
- Original leaf material, unchanged: `Original_Submesh_1.Original_Submesh_1`.
- Albedo, shared by original and proof: `coconut_palm_leaf_3f6407d492f8_albedo_cdcdc62b95fb29.coconut_palm_leaf_3f6407d492f8_albedo_cdcdc62b95fb29`.
- Normal, shared by original and proof: `coconut_palm_leaf_n_d2a3401423b4.coconut_palm_leaf_n_d2a3401423b4`.

Reference Viewer at depth 1 / breadth 20 shows the original mesh depending on its two original materials; the saved proof mesh depends on the original trunk material and the proof leaf material. The proof leaf material has the proof mesh as its displayed referencer and the two original leaf textures as dependencies. The original leaf material retains the original mesh as its displayed referencer. These are bounded viewer results, not an unlimited dependency audit. The original-material Reference Viewer capture was made after P1; the unchanged source hashes support comparison with the preflight state. [measured: labels 03, 15–18; `FINAL_VALIDATION.json`]

Both mesh previews display 4,160 triangles, 3,326 vertices, 2 UV channels, 2 material slots, 1 collision primitive, Nanite disabled and approximate size 605 × 612 × 870 cm. Rendered LOD is 0. These are editor readouts; physical scale, contact, orientation, pivot and collision suitability were not measured. No geometry, UV, LOD, Nanite, collision or texture setting was edited. [measured: labels 01–02, 11–12, 22–24; not run: H0958-PLACEMENT-MEASUREMENT]

## Persistence and preservation

First session: PID **7132**, launched 03:00:18; UI close at 03:18:43, log exit at 03:18:45. Second session: PID **27736**, launched 03:19:24; UI close at 03:22:36, log exit at 03:22:39. Both used `/Engine/Maps/Templates/Template_Default`, with 8 actors and All Saved on exit. The second session only inspected the saved proof; it made no package saves. [measured: launch records, `SESSION_1_EXIT_CHECK.json`, `SESSION_1_EDITOR.log`, `SESSION_2_EDITOR.log`, labels 20–27]

At 03:23:37, no Unreal/Houdini/HARS/hython process remained. Content increased from **5,989 to 5,991 files**, with exactly the two allowed additions, zero modifications and zero deletions. All 26 protected-file SHA-256 checks match, including original packages, relevant sources, canonical index and measurement ownership. All existing project Config hashes match and no new project Config file exists. Seven verified source-package backups remain outside Content. The full Content check is metadata-based; it is not a byte-for-byte hash of every project asset. [measured: `FINAL_VALIDATION.json`, `CONTENT_AFTER.json`, `SOURCE_PACKAGE_BACKUPS.json`]

Proof hashes before and after the fresh-process inspection match:

| Package | SHA-256 |
|---|---|
| M_H0958_Leaf_Proof | `B841172B9A817A7E5FB0A08FC9990E6D728AD3B4E8B81FBCAAA5B11CF83192C6` |
| SM_H0958_CoconutPalm_Proof | `0BF425C33023A66504099BB0A53FEF9EA66EBBBBED3FE9FFBA337C3A5F68445E` |

Saved-side changes are preserved and disclosed: two proof autosaves, `PackageRestoreData.json`, two CrashReportClient initialization INIs, `Editor.ini`, and `EditorPerProjectUserSettings.ini`. Their paths, metadata and current hashes are in `FINAL_VALIDATION.json`. The two normal editor shutdowns are confirmed in logs; creation of a CrashReportClient INI alone is not crash evidence. No autosave/config file was deleted or restored. [measured: final validation and session logs]

## Status and next evidence gates

The source is available/imported, and the isolated derivatives now have a bounded material and package-persistence check in this project. They remain **experimental, unqualified, not connected to Houdini, not generated, and not accepted**. No map save, import, cook, bake, Houdini launch, BG1, Tier 1, Linear or catalog modification occurred in this task. CONTRACT v0.6 remains unapproved. [measured: this receipt and preservation evidence; documented: execution brief]

Keep both proof packages isolated as evidence. Do not replace the source, promote the proof to Shared, or add it to generator rules on the strength of this result alone. [proposed]

Prioritize later tasks as follows:

1. **Shader/source fidelity and geometry:** compare the source shader intent, UV alignment, normals and leaf backs in close and underside views. Gate: documented correspondence or explicit remaining differences, without changing source assets. [not run: H0958-SOURCE-FIDELITY]
2. **Filtering and performance:** investigate existing NoMipmaps, distance aliasing, masked overdraw, shadows, LOD and wind under a separate brief. Gate: measured representative distances and performance; no inference from this preview alone. [not run: H0958-PERFORMANCE]
3. **Placement and role:** measure scale, pivot/contact/orientation/collision and confirm species/style for pre-war GazaRimal. This is a whole vegetation mesh suitable for evaluating an instancing role, not a Building Generator module. Gate: role-specific evidence and Aviv's visual/style decision. [inference: prospective role; not run: H0958-ROLE-QUALIFICATION]
4. **Rights and integration:** existing Bank_ME_v3 owner confirmation covers continued technical qualification, as documented in the brief; it is not new export/redistribution/attribution evidence. Resolve the CityGen3D source-content mapping and applicable rights separately. Any future Houdini placement/generation test needs its own authorized task and evidence gate. [documented: `../H0958_MATERIAL_REPAIR_PROOF_BRIEF_2026-09-29.md`; not run: H0958-GENERATOR-PLACEMENT]

Machine-readable receipt: `BANK_ASTRA_002_RECEIPT.json`. Full visual ledger: `OBSERVATIONS.json`, 28 observations / 73 saved screenshots, all referenced files present. The fresh-launch record also discloses and corrects a nonterminating date-type comparison error in the launch guard; no extra process was launched. [measured: receipt and `LAUNCH_2.json`]
