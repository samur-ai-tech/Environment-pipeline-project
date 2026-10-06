# H0958 Material Repair Proof Brief, 2026-09-29

**To the bank manager; Briefing only.** Unreal or Houdini was not opened, no Content was created, and no correction was made as part of writing this document. [not run: H0958-MATERIAL-REPAIR]

**Updating mission permission:** According to the coordination director's directive, the late Aviv instruction to continuously complete all remaining preparations covers the limited technical proof and reversal in the briefing, after the operator allocation and editor lease. The source specified by the administrator is a user turn`01a0ea4c-6548-7bc3-b903-507877264acf` In the prefix-identified coordination chat `01a0e906...`; The brief writer received the domain's interpretation from the manager and did not read the original message here. This is a late-mission authorization record, not a rights approval or a qualification. No further go should be requested just because the original BANK-ASTRA-001 was read-only. [documented: the coordination manager's directive to the brief writer, 2026-09-29; reference: the director's interpretation of the Aviv instruction]

## Sources and field of view

`P` = `Staging/ModelBank/Inspection_2026-09-29_Astra_Prep/`; `V` = `/Game/Project/Shared/Bank_ME_v3/Vegetation/`; `TB` = `C:/Users/USER/Documents/Pipeline Environment/`.

- `P/LIVE_OBSERVATIONS.json`,labels 2029, especially 2127; these are recorded observation receipts of the operator, not a re-examination of the briefing writer.labels 20, 28, 29 pertain to other buildings and are not evidence of the palm repair. [documented: `P/LIVE_OBSERVATIONS.json`]
- `P/H0958_SOURCE_ALPHA_READOUT.json`, `P/BANK_ASTRA_001_CANDIDATES.json`, `P/LIVE_RELEASE_CHECK.json`, `P/LIVE_VALIDATION.json`, `Staging/ModelBank/EDITOR_OWNER.txt`.
- `Staging/ModelBank/RIGHTS_TECH_GAPS_2026-09-28.md`, the foliage matrix; `RIGHTS_DECISION_PACKET_2026-09-29.md`, Bank_ME_v3 domain and H0958 source; `Inspection_2026-09-28_Continuation/Native_Visual_Run_02/NATIVE_VISUAL_REVIEW.md`.
- `AGENTS.md`, rules of ownership/preservation/bank; `TB/CONTRACT.md` v0.6, Status DRAFT, Articles 4.5 and 6. Proof of material is not a Houdini gate, is not Tier 1 and is not the contract confirmation. [documented: the above sources]

## The current diagnosis

1. In the imported texture, transparency was observed and a leafy sillhouette A: 32224, B8G8R8A8, Source Alpha Detected=True, Format Supports Alpha=True. Number of Mips=1, Mip Gen Settings=NoMipmaps, sRGB=True, Method=NotStreamed. `P/LIVE_OBSERVATIONS.json`, labels 21–23]
2. Browse from Texture Sample that is connected to Base Color exactly `V/coconut_palm_leaf_3f6407d492f8_albedo_cdcdc62b95fb29`.b.`Original_Submesh_1` RGB is connected to Base Color; Channel A is not connected; Opacity Mask is inactive; Material Domain=Surface, Blend Mode=Opaque, Shading Model=Default Lite, Two Sided is off. `P/LIVE_OBSERVATIONS.json`, labels 25–26]
3. Normal is connected from a separate texture `V/coconut_palm_leaf_n_d2a3401423b4`: Normalmap, WorldNormalMap, sRGB=False, NoMaps. Its alpha should not be used for the leaf mask. [measured: `P/LIVE_OBSERVATIONS.json`, label 27]
4. File albedo measured under `ME/Sources/H0958_CoconutPalm/` Contains 223,817 alpha=0 and 105,911 alpha=255 pixels, with no intermediate values. SHA-256: `ce7991f4cb00fa2de7741d2086cc1d143af9b0c68510b193d20d27a8e12a76ac`The Source File path viewed in the editor is `Staging/ModelBank/ME/Textures/coconut_palm_leaf_3f6407d492f8_albedo_cdcdc62b95fb29.png`The late test in LIVE_VALIDATION confirms it SHA-256 in both copies and`source_copies_match_offline_alpha_input=true`; This gap is closed in the file check. This does not prove UV or SHADER. [measured: `P/H0958_SOURCE_ALPHA_READOUT.json`; `P/LIVE_OBSERVATIONS.json`, label 24; `P/LIVE_VALIDATION.json`, h0958_source_copies]
5. The Texture Editor shows `Uncompressed (RGBA8)` The Content Browser Tooltip displays `Editor Icon`Preserve both descriptions; meaning of difference not decided. UNKNOWN fields in the CANDIDATES file on imported alpha and base color binding preceded the 2127 observations; they do not cancel them. [documented: `P/LIVE_OBSERVATIONS.json`, label 26; `P/BANK_ASTRA_001_CANDIDATES.json`, H0958]

Experiment hypothesis: The correct A connection with Blend Mode=Masked may remove the atomized leaf rectangles. UV adjustment, back side, normality and source material orientation have not yet been demonstrated. [inference] No repair has been made; it should not be concluded that the alpha connection alone proves fidelity to source, rights, performance or qualication. [not run: H0958-MATERIAL-REPAIR]

## Protected Identities and Proposed Proof Products

The source ID in the catalog remains exactly `current_Project__Shared__Bank_ME_v3__Vegetation__SM_H0958_CoconutPalm`; also `variant_id` Its history does not change. [documented]: `P/BANK_ASTRA_001_CANDIDATES.json`, H0958]

| Role | Exact Object Path |
|---|---|
| Mesh source protected | `/Game/Project/Shared/Bank_ME_v3/Vegetation/SM_H0958_CoconutPalm.SM_H0958_CoconutPalm` |
| The original protected leaf material | `/Game/Project/Shared/Bank_ME_v3/Vegetation/Original_Submesh_1.Original_Submesh_1` |
| The protected race material | `/Game/Project/Shared/Bank_ME_v3/Vegetation/Original_Submesh_0.Original_Submesh_0` |
| Albedo is protected | `/Game/Project/Shared/Bank_ME_v3/Vegetation/coconut_palm_leaf_3f6407d492f8_albedo_cdcdc62b95fb29.coconut_palm_leaf_3f6407d492f8_albedo_cdcdc62b95fb29` |
| Normal is Protected | `/Game/Project/Shared/Bank_ME_v3/Vegetation/coconut_palm_leaf_n_d2a3401423b4.coconut_palm_leaf_n_d2a3401423b4` |
| Mesh Derivative Offered | `/Game/Developers/USER/ModelBankProof/H0958_MaterialRepair_20260929/SM_H0958_CoconutPalm_Proof.SM_H0958_CoconutPalm_Proof` |
| Proposed derivative material | `/Game/Developers/USER/ModelBankProof/H0958_MaterialRepair_20260929/M_H0958_Leaf_Proof.M_H0958_Leaf_Proof` |

Derivative paths are an offer, not assets created. Two packets only; no new map, no copying of textures, and no Material Instance that does not allow the required graph change. The slot name remains `Original_Submesh_1`; Only the reference in the mesh emulation will change. No Rename, Move, Reimport or Fix Up Redirects to the source. No replacement of the candidate in the catalog. [proposed]

## Terms of entry and the editor's lease

1. The manager registers one task, a single operator, start/validator time, scope and both save routes, from the late task permission power recorded at the opening. No loop renewal `Staging/Operator/STOP` And there is no need for ownership approval or going back to the same domain. [documented: Coordination Administration Directive, 2026-09-29; `AGENTS.md`, Tracks and roles]
2. `LIVE_RELEASE_CHECK.json` Documenting at 02:44:02+03:00 zero processes, 5,989 content files before/after, `content_metadata_diff=[]`, ‏`mesh_hash_diff=[]`, and the catalog is unchanged. The release was completed after`EDITOR_OWNER.txt`: ‏`2026-09-29T02:45:08.9357886+03:00 OWNER=NONE`, BANK-ASTRA-001 released by the bank manager, with OWNER MEASURATION=NONE. LIVE_VALIDATION certifies the record; the `manager_release_required=true` The old as an open block. This is historical data: before new leases are still to be made in real time at a vacant cost and zero Unreal Processes. If there is an active session, do not close it or take ownership from it. The old comparison was metadata for all 5,989 files and SHA-256 for five meshes and 12 materiels, not hash of any Content. [measured]: `P/LIVE_RELEASE_CHECK.json`; `Staging/ModelBank/EDITOR_OWNER.txt`; `P/LIVE_VALIDATION.json`]
3. Before opening: Inventory of each Content with a relativistic path, size and UTC modification time; SHA-256 targeted mesh H0958, its two materials, the protected textures/dependencies, the relevant source files, and the canonical CSV. The default hash should not be loaded against any 5,989 content files. After the experiment, SHA-256 is measured for each fileholder and the available will not be checked outside of the filename.`Staging/ModelBank/H0958_MaterialRepair_Proof_20260929/` When ready for the first file. A copy of the source and dependencies packets should be saved outside Content, with hash matching. New editor script should not be created; supported UI users and existing file measurement tools should be used. [proposed]
4. Open from Windows/PowerShell only, without Houdini and without an HDA map; a static Mesh Editor preview is enough. First make sure there are no unfamiliar dirty packets and the proof years are not present. A name conflict requires a stop, no overwrite or automatic suffix. [proposed; documented]: `AGENTS.md`]

## The limited experiment

**P0baseline, unguarded:** Verify Browse/Copy Reference from the mesh to any slot, from the material to any texture; record class, full object path and Reference Viewer Dependencies/referencers. Photograph the source from two identified angles: A close-up view of the crown and cards; B counterside/under-the-crown that allows for return views of leaves.

**P1 — Masked:** After assigning the assignment and a valid lease from the late permission power, duplicate the two proof assets to the exact paths. Make sure in the title and copy reference that the derivative is edited. In the mesh derivative only, replace the slot reference`Original_Submesh_1` For proof material. For proof material: Blend Mode `Masked`; for a friend `A` of the same Base Color Texture Sample to `Opacity Mask`. Save Surface/Default Lit and Two Sided=Off; Do not touch Normal, UV, compression, MIPS, LOD, Nanite or Collision. Record value `Opacity Mask Clip Value` Existing and leave it constant, without trial and error tuning. Perform Apply on derivative only and photograph A/B and graph. [proposed; not run: H0958-P1]

**P2 Conditional Two Sided Test:** Only if P1 resolves the cards on the front side but B shows a rear-side disappearance, and a section/geometry test supports that it is leaf cards, to check for the same derivative material `Two Sided=On`, without any other modification. Reshoot A/B on the same terms and register separately silhouette, backfaces, dark and normal. If there is no such symptom mark P2 as not required and do not change. There is no automatic switch to`Two Sided Foliage`, Translucent or Subsurface; these require a source shader diagnosis and follow-up briefing. [proposed; not run: H0958-P2]

**The result of the experiment:** The operator collects and the manager examines technical evidence without waiting for Aviv's visual judgment. Minimum four screenshots match: P0-A/P0-B vs. P1-A/P1-B; if P2 runs, two more. The separation of the leaves, UV-matching to the paint, rectangles/holes, and back disappearance; the provider remains listed as [UNKNOWN]. Style selection, use of the area and final visual acceptance must be recorded after the property has been displayed.

## Retaining, receipting and restoring policies

- **The operator is allowed to save only the two proof assets in the exact object pathes table**, as experimental evidence only, from late task authorization. P0 and source remain unguarded. No Save All, Save Current Level or Save map/config/responsibility source. Unexpected prompts are stopped and documented. [documented: Coordination Administration Directive, 2026-09-29)
- Keep the material and the mesh one by one after a P1 record; if P2 is justified, it is possible to check and save its status in those two pathes, with receipt and hash for each saved situation. A copy of the P1 status can be saved outside of Content in the Evidence folder for review, without creating a third asset. The last saved mode will be explicitly marked experimental; its retention is not a choice for production, style judgment, or classification. The proof must not be collected for Aviability.The Evidence. [documented: Coordination Administration Directive, 2026-09-29; proposed: Documentation Order]
- After authorized retention: close the operator-owned process, reopen without HDA and film A/B before further editing; verify slots, graph and material properties. binary hash before/after without additional save checks file retention, no Fidelity or regeneration. No Cook, Bake, Placement, PCG or Generation. [Proposed; not run: H0958-PERSENSE]
- Redirect required: versions of engine, task/operator/ease, full source identifier, two derived object path, slot mapping, graph pins, P0/P1/P2 settings, compile mode, each operation and save times, photocopies, dependency/referencing list [after, SHA-256 of each file/texture is currently being reviewed.
- Historical hashes for comparison only: mesh`e9575502d9e03f75537e2edcd02d22f444920aee7aa4ab1e48765752168bc3e6`; ‏Original_Submesh_1 ‏`29baa8cc251ef50fd95c41d46c3257ee8d75a720f27f723ba4042fd954a48971`; ‏Original_Submesh_0 ‏`a96652f763e913eb9e196743b75d453311da75236c509d69edf42c0632465ac9`Must be re-measured before action. [measured]: `P/BANK_ASTRA_001_CANDIDATES.json`, prep]
- Content diff is complete after closing: added/modified/deleteed according to relative path, size and UTC modification time; SHA-256 is targeted to the protected assets and each new/variable package. No default hash and no byte-equality claim for the entire project from within the metadata only. The result allowed in the save is two new packets in the source paths only.In the targeted hash. Autosaves/config will also be registered separately; do not delete them quietly. [proposed]
- Rollback before saving: close the derivatives without Save, exit without Save Map, check diff. After saving: the source is still valid; remove the derivatives from use and leave them isolated. If go includes deleting the proof assets, check references and then delete only the two paths through the editor, mesh first, without Force Delete, and verify the diff. Otherwise aviv decision is required for deletion; no deletion of the files without the file.The director/aviv and in no active editor. [proposed]

## Stopping and remaining uncertainty

Stopping if lease/license is missing, source hash has changed without explanation, binding is different from the documented, content is unpredictable, there is an error compile, UV/mask failure, unexplained leaf disappearance, demand for a texture/geometry/source change, or action seeks to keep out of both paths. There is no scope extension to obtain a good looking image. [proposed]

Even after the success of P1/P2 remain open: source shader and whether a dedicated foliage model is required; normal orientation and UV; meaning of the difference in communicative names; remote filtering and NoMipmaps; cost of Masked/Two Sided and Overraw; LOD/wind/shadows; color/contact/scale; species and HFOR-conference period.

Aviv approval from 27.9 to 32 Bank_ME_v3 assets already covers continuing technical training; it should not be re-asked. It does not automatically permit this editing experiment and is not an export/resistrigation/attribution document. Source H0958 is documented as`Assets/CityGen3D/Meshes/Ambient-Occlusion/CoconutPalm.asset`; Third-party product/content adjustment and distribution conditions are still missing. [documented: `RIGHTS_DECISION_PACKET_2026-09-29.md`, Bank_ME_v3]

## Terms of execution and remaining decisions

1. The manager assigns a single operator and lease window, after re-examination of ownership and processes. The late assignment permission is sufficient for P0/P1, the conditional P2, for retaining only the two assets and for fresh-process reopening; there is no further open go question in this area. [documented: Coordination Manager Directive, 2026-09-29)
2. After collecting the evidence, Aviv will decide whether the visual result is appropriate for the desired style and use, and later whether H0958 is botanically/geographically appropriate for the role. These are not entry conditions for collecting the proof of the material. [proposed]
3. The default at the end is to leave the two derivatives isolated as test evidence. Future deletion according to rollback track requires explicit instruction if not included in the execution task; it does not block the experiment. [proposed]

Canonical CSV change, transfer to Shared, select replacement, change Track B/Linear and full acceptance remain outside the briefing and proof task. [not run: H0958-MATERIAL-REPAIR]
