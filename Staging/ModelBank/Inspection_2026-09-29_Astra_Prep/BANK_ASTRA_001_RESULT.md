# BANK-ASTRA-001 — inspection receipt and corrections

Date: 2026-09-29. Operator: Astra `01a0e820-c6d4-7702-8e7b-55fd20f9b020`. Canonical catalog owner: bank manager `01a0e7e2-2aac-7a63-a913-e58b1f3714a2`.

**Bounded inspection completed; qualification remains incomplete.** Three existing meshes were revisited: H0013, H0015 and H0051. H0958 received a material/texture dependency inspection, not a new whole-mesh preview. H0907 was preparation only. These are repeat inspections, so this run adds **zero new unique mesh candidates** to the prior coverage count. No asset becomes qualified, connected, generated, scene-verified or accepted.

## Ownership and preservation

- [documented: `../EDITOR_OWNER.txt`] Manager lease: 02:20:17–03:05:17 +03. At prep creation there was no lease; that earlier status is historical.
- [measured: `LIVE_PREFLIGHT.json`] At 02:28:01 the bank lease matched this task/thread; measurement latest owner was NONE; no Unreal/Houdini/HARS/hython process or Unreal window conflicted.
- [measured: `LIVE_LAUNCH.json`, `LIVE/00_start_clean__0.jpg`] UnrealEditor PID 22168 launched at 02:28:18 with `/Engine/Maps/Templates/Template_Default`. The UI showed Template_Default, 8 actors and All Saved. No proof/HDA map was opened.
- [measured: `LIVE_OBSERVATIONS.json`] 31 timestamped observations, including readouts, alpha view, material binding and the floor correction. Isolation and channel controls affected preview display only; they were restored. The shared preview profile was read, not changed.
- [measured: `LIVE_SESSION_LOG_EXCERPT.txt`, `LIVE_RELEASE_CHECK.json`] UI exit at 02:43:35; log exit at 02:43:37; PID and Unreal windows absent on verification. No save dialog required a response. Content count remained 5,989, with zero path/size/UTC-mtime differences; five selected mesh SHA-256 hashes were unchanged. Measurement-owner and canonical-index hashes were unchanged at release. This is a metadata comparison of all Content, not a full byte hash of every Content file.
- The first metadata comparison accidentally mixed JSON-parsed dates with timestamp strings and produced false differences. The corrected comparison preserves strings; the receipt records this correction and retains the unchanged original preflight.
- [documented: `../EDITOR_OWNER.txt`] The manager appended **OWNER=NONE at 02:45:08.9357886 +03**, after verification. The operator did not edit the owner ledger.
- No source/Content edits, asset/map saves, placement, import, Apply, repair, cook, bake, BG1, Tier 1, Houdini launch or Linear action occurred.

## Mandatory correction: preview floor is not asset geometry

**Withdraw the claims that H0013 has an integral broad rectangular paved base, that placement must reserve that displayed platform, and that its collision hull fails to cover that platform.**

[measured: observations 16, 28, 29] Preview Scene Settings explicitly show an enabled `Floor_Mesh` with `M_Grid`. In H0013, isolating material element 0 and then element 1 leaves different, complementary building sections visible while the same broad gridded platform stays unchanged. H0015 shows the same distinction in observations 17–18. The platform is preview scenery. It is not a measured asset footprint or a ground-contact test.

This corrects the paving interpretation in this packet's preparation text, the earlier Run02 description and live observations 05–07/11–12. Original screenshots and chronological notes are preserved; `LIVE_OBSERVATIONS.json` marks affected interpretations as superseded. The manager must propagate this erratum to canonical summaries. This correction does **not** prove the mesh has no small threshold/base geometry. Actual support points, local contact coordinates and exact mesh envelope still need measurement.

## Candidate findings

All exact IDs, Unreal object paths, source-package paths, prior bounds and dependency paths are in `BANK_ASTRA_001_CANDIDATES.json`; IDs and original packages were preserved.

| Candidate | Exact Unreal package | Findings and recommendation |
|---|---|---|
| H0013 | `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0013_Building_04` | **Review / retain candidate.** [measured] Tall pale building with recessed/stepped elevations, AC units, pipes, blue window imagery, roof structures and tanks; one camera elevation is nearly blank. Whole building, not a Building Generator module. [inference] Retain for taller residential parcels after local style and physical envelope checks. Broad paving claim withdrawn. |
| H0015 | `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0015_Building_02` | **Review / retain distinct alternative.** [measured] Five upper façade rows over shuttered ground openings, mixed open balconies and enclosed glazed bays, dishes, roof setback and a narrow brown frontage/base section. Blank narrow end wall. Glazing has repeated blue/mottled imagery; its intent remains unresolved. [inference] Mixed residential/ground-floor commercial role; not interchangeable with the taller H0013. |
| H0051 | `/Game/Project/Shared/Bank_ME_v3/StreetFurniture/SM_H0051_Garbagebin` | **Review / retain candidate.** [measured] Wood-slatted bin in a metal frame with lower leg extensions, integrated bottles/broken glass and litter. Browse from its one material slot resolves `StreetFurniture/Street_Props_Pack__003`, not the similarly named Props material. [inference] Sidewalk/public-space furnishing; constrain repeated litter/bottle appearance. Exact bin-only height and support points remain unknown. |
| H0958 | `/Game/Project/Shared/Bank_ME_v3/Vegetation/SM_H0958_CoconutPalm` | **Hold / repair candidate.** [documented: Run01/02] Whole-mesh preview has opaque leaf cards. [measured this run] The exact imported leaf texture retains a leaflet-shaped alpha channel, but `Vegetation/Original_Submesh_1` is Opaque and leaves alpha disconnected. No repair performed. Plant species/local-period suitability is still unverified. |
| H0907 | `/Game/Project/Shared/Bank_ME_v3/Buildings/SM_H0907_Arab_x3_fbx` | **Review / reserve for a specific landmark match.** [documented: prior receipt] Domed pavilion/landmark form, not ordinary housing; dome tone boundaries need review. [not run: BANK-ASTRA-001] No live inspection of this mesh in this window. |

### Live technical readouts

| Mesh | LOD0 triangles / vertices | UV channels / material slots | Collision / Nanite | Limits |
|---|---|---|---|---|
| H0013 | 44,241 / 45,927 | 2 / 4 | 1 convex element; BlockAll; Collision Complexity Project Default; Nanite unchecked | Preview LOD menu offers only LOD0 plus Auto. Hull spans façade recesses. Runtime collision and performance not run. |
| H0015 | 201,057 / 211,808 | 2 / 4 | Overlay: 1 collision primitive; Nanite unchecked | Preview LOD menu offers only LOD0 plus Auto. Collision complexity/shape not rechecked in this window. |
| H0051 | 5,180 / 4,776 | 2 / 1 | Overlay: 1 collision primitive; Nanite unchecked | No new LOD-menu, collision-shape or runtime performance check. Prior import reports one LOD. |

[measured: observations 01, 04, 09–14, 20] These are editor readouts. They do not establish UV quality, texture density, lightmap validity, playable collision or scene performance. Bounds search for H0013 revealed only **Positive/Negative Bounds Extension** fields, not actual local min/max. The historical import bounds remain documented separately and were not converted into contact vectors. Semantic front/up, signed contact, approved scale range, physical reference size, Unity behavior and Houdini placement remain UNKNOWN / NOT RUN.

## H0958 dependency diagnosis

[measured: observations 21–27]

- `Original_Submesh_1` is a Material in `/Game/Project/Shared/Bank_ME_v3/Vegetation`. Surface / Opaque / Default Lit; Two Sided unchecked. Base Color and Normal receive separate texture RGB outputs. Alpha is unconnected and Opacity Mask is inactive.
- Base Color uses `coconut_palm_leaf_3f6407d492f8_albedo_cdcdc62b95fb29` in that same directory. Alpha-only viewer shows white leaflets and black gaps. Texture Editor: imported/displayed/max-in-game 322×1024, B8G8R8A8, Source Alpha Detected=True, Format Supports Alpha=True, one mip, NoMipmaps, sRGB=True, Compress Without Alpha unchecked, resource size 1288 KB, method Not Streamed.
- Texture Editor calls its compression `Uncompressed (RGBA8)`; Content Browser tooltip calls it `Editor Icon`. Both labels are preserved; equivalence was not investigated.
- Normal uses `coconut_palm_leaf_n_d2a3401423b4`, same directory, 322×1024, Normalmap compression, World Normal Map group, sRGB=False, NoMipmaps. Its alpha is not an opacity-mask source.
- Native source-file tooltips point to `Staging/ModelBank/ME/Textures/` copies. The consolidated leaf-albedo PNG and the inspected `Sources/H0958_CoconutPalm/` PNG have identical SHA-256 `ce7991f4cb00fa2de7741d2086cc1d143af9b0c68510b193d20d27a8e12a76ac` [measured: `LIVE_VALIDATION.json`, `h0958_source_copies`, written at 02:49:20 +03]. Earlier offline alpha counts and Sources-folder duplicate hashes remain in `H0958_SOURCE_ALPHA_READOUT.json`.
- [inference] Missing material use of existing alpha is a concrete cause candidate for the opaque cards. [not run] UV/mask alignment on the actual palm, underside visibility, intended source shader, corrected material, distance aliasing and final vegetation appearance.

## Practical subset and remaining gates

[proposed] **H0013 + H0051** remain the smallest two candidates for a later whole-instance/contact measurement. Keep **H0015** as a meaningful lower mixed-use alternative. This is not a qualified set or a complete Tier 1 set. CONTRACT v0.6 §6.1 names H0907, H0013, H0051 and H0958; H0015 cannot silently replace them. BG1 remains a separate module proof.

[documented: `../LICENSE_PROVENANCE.md`] Aviv's ownership confirmation covers technical qualification of the exact 32 Bank_ME_v3 assets. That existing confirmation was not requested again. Export, redistribution and attribution terms remain unverified; it does not extend to other packs. Rights evidence does not cure a technical defect. All three v3 vegetation assets remain on hold under prior visual evidence; this run repaired none.

Next tasks and explicit evidence gates are in `Staging/Archive/PreFinalVision_2026-09-29/Bank_WorkOrders/BANK_ASTRA_001_NEXT_TESTS.md`. Canonical integration belongs to the manager. The operator has no active editor lease after the recorded release.

