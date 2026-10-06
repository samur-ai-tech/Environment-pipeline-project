# Rights Decision Packet — GazaRimal — 2026-09-29

**Result:** Existing owner confirmation permits continued technical qualification of **only the exact 32 Bank_ME_v3 models**. It need not be requested again. Other packages have varying levels of evidence for source identity or local acquisition, but sufficient rights evidence has not yet been linked to the selected assets. This document gives no legal determination or distribution approval. [documented: `Staging/ModelBank/LICENSE_PROVENANCE.md`, Owner confirmation]

The inspection was read-only; only this document was written. Unreal/Houdini were not run, and Content, catalogs, Track B, and Linear were not edited. AGENTS.md, the 28 September handoff, rights-gap report, provenance document, current catalog, and Run02 report were read. Candidate counts below are catalog rows, not counts of packages or all assets in a package.

## Evidence map

- `EP` = `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline`.
- `OLD` = `C:\Users\USER\Documents\Unreal Projects\GIS_WorldBLD`.
- `LIB` = `OLD\SourceData\ModelBanks_Archive\Unreal_Model_Library_2026-09-24`.
- `V` = `C:\ProgramData\Epic\EpicGamesLauncher\VaultCache`.
- `FDB` = `V\FabLibrary\listings_v1.db`.
- `IDX` = `EP\Staging\ModelBank\BANK_CANDIDATE_INDEX_2026-09-28.csv`.
- `CAT` = `LIB\Reports\library_catalog.json`.
- `R02` = `EP\Staging\ModelBank\Inspection_2026-09-28_Continuation\Native_Visual_Run_02\NATIVE_VISUAL_REVIEW.md`.

[measured: `IDX`, existence check 2026-09-29] There are 930 current and 285 external rows; all 930 `source_path` values of current rows exist. Thirty-two `SM_*.uasset` files exist under `EP\Content\Project\Shared\Bank_ME_v3`, matching the 32 Bank_ME_v3 catalog rows. File presence is not evidence of purchase or permission.

[measured: `FDB`, SQLite `mode=ro`, 2026-09-29] `sqlite_master`, `local_listing`, and `listing_acquisition` were inspected. There are 19 listing records, all with an acquisition linked to the same local account ID. `local_listing.user_uid` and `entitlement_uid` are empty in the checked records. The acquisition table contains only `listing_uid,user_uid`; it has no acquisition date, license type, tier, or terms. The account holder's identity was not verified. Listing dates, even if filled, are not purchase dates.

To reproduce the check, open FDB read-only and run: `SELECT l.uid,l.title,COUNT(a.listing_uid) FROM local_listing l LEFT JOIN listing_acquisition a ON a.listing_uid=l.uid GROUP BY l.uid,l.title;`. The account ID itself need not be displayed.

## Unreal and Fab/Vault packages

In every row marked **open**, the missing evidence is: entitlement of the authorized account/entity, acquisition date and the document applicable to that acquisition, and mapping of assets and dependencies to the package. An acquisition row alone does not supply these. The technical use of the approved 32 assets is addressed separately below.

| Package / rows | Exact local evidence | What it proves | Gap and use decision |
|---|---|---|---|
| `Palms_Pack_01` / 33 | [measured: `V\PalmsPaccb57d20c74ffV3\manifest`] Strings `Palms Pack 01 (Trachycarpus fortunei)` and listing `9f81069d-877c-4d4e-aa28-30f5d1a8d8c9` found; `EP\Content\Palms_Pack_01`; this listing/acquisition is absent from FDB | The manifest explicitly identifies the package; absence of the FDB row does not prove lack of ownership | **Open, first priority.** Entitlement + terms at acquisition + version match to the 33 candidates. Run02 shows potential visual suitability without changing rights. |
| `MOUT_Arabian` / 86 external | [measured: `FDB`] UID `2f06f74d-db49-4ce9-83e5-0f08e51af597`; [measured: `V\ModularM8ab5ae4681caV6\manifest`] Full title `Modular Military Operation Urban Training Environment - Arabian Pack`; `OLD\Content\MOUT_Arabian` | Local acquisition and explicit Vault package identity | **Open.** Entitlement and terms; match OLD files and textures to the version. Bank_ME_v3 approval does not cover it. |
| `ModularCourtyard` / 112 | [measured: `FDB`] `ecd3dc8a-5888-4421-91b5-a18390ed4828`, `Modular Courtyard 1.0`; `V\ModularC798ab2003378V1\manifest`; `EP\Content\ModularCourtyard` | Acquisition by package title and candidate files | **Open.** Entitlement/terms documents and version/asset match; binary content identity was not checked. |
| `ModularBuildingSet` / 138 | [measured: `FDB`] `474a0598-ed86-40b6-baa1-c801d96ef4ab`; [measured: `V\ModularBuildingSet410\manifest`, CustomFields] `Modular Building Set` and same listing; `EP\Content\ModularBuildingSet` | Acquisition and Vault identity; manifest names old build `4.11.0-2800390` | **Open.** Original acquisition document and terms applicable then; the current Fab name does not prove which document applied to an old version. |
| `ProceduralBuildingGenerator` / 258 | [measured: `FDB`] `783058bc-1afc-472a-96b1-289ad13c6aa9`; [measured: `V\Procedur82cd1614076dV1\manifest`, CustomFields] `[Free] Procedural Building Generator`; `EP\Content\ProceduralBuildingGenerator` | Acquisition and Vault identity | **Open.** Package documents and mapping even if only meshes or materials are selected; `Free` is not evidence of terms. |
| `FC_Coastal_Landscape` / 12 | [measured: `FDB`] `fe1373c0-969d-4ebf-a8f0-9468fd29d239`, `FREE 4x4km Coastal Landscape Sample`; `V\FREE4x4k21f7cb882be0V1\manifest`; `EP\Content\FC_Coastal_Landscape` | Acquisition and matching title | **Open.** Entitlement/terms and mapping of functions, materials, and textures; `Sample` is not a license determination. |
| `AssetsvilleTown` / 236 | [measured: `FDB`] `fd558d8c-bd7e-461f-8449-a7cc9c277078`; [measured: `V\Assetsvicb796a074ca2V2\manifest`, CustomFields] `Assetsville Town`; `EP\Content\AssetsvilleTown` | Acquisition and Vault identity | **Open.** Style/selection are also not approved by the rights document; lower priority until a role is chosen. |
| `UtopianCity` / 63 | [measured: `FDB`] `1e9f098e-5157-4cbf-b8a0-803eda37474b`, `Utopian City`; `V\UtopianC7adfbf7ad5c3V1`; `EP\Content\UtopianCity` | Acquisition and matching title | **Open.** Documents and mapping; do not extend approval to the entire bank. |
| `Warehouse_Building` / 2 | [measured: `V\Warehous2fc606d53413V1\manifest`] Strings `Warehouse Building`, listing `885f25a7-06da-4d27-bbbc-edf8ba8c7871`, and `Content/Warehouse_Building/...` names; `EP\Content\Warehouse_Building`; this listing is absent from FDB | Package identity and asset paths; an update beyond the older rights report | **Open.** Entitlement/terms and dependency mapping; no matching acquisition found in this inspection. |
| `Stylized_Egypt` / 21 | [measured: `V\Stylized9ec755cb81bdV1\manifest`, CustomFields] `Stylized Egypt`, listing `c935ca3e-dbb1-4b7d-a080-65de129c60bd`; FileManifestList has `Content/Stylized_Egypt/...`; `EP\Content\Stylized_Egypt`; listing absent from FDB | Package identity, not entitlement | **Open, lower priority** until a style decision. Entitlement/terms documents and asset match. |
| `Iceland_Environment` / 14 | [measured: `IDX`; `EP\Content\Iceland_Environment`] Candidate files exist; no matching title among 19 FDB records | Presence only; no exact purchase package identified here | **Open.** First identify product/creator/store and ID; some candidates are marked exclude, so collecting documents has no priority until selection. |
| `StarterContent` / 9 | [measured: `IDX`; `EP\Content\StarterContent`] Candidate files exist | Path and tentative source only | **Documentarily open.** Identify the Engine/source package that supplied them and its relevant document; do not necessarily request a Fab receipt for Engine-provided material. |

No public EULA is used here to infer rights to local files. No online account was opened and no email receipts were searched. [not run: ACCOUNT-ENTITLEMENT; ACQUISITION-LICENSE-MATCH; CONTENT-BYTE-MATCH]

## Bank_ME_v3 — approval scope and sources

[documented: `EP\Staging\ModelBank\LICENSE_PROVENANCE.md`, lines 5–7] Aviv's 27 September approval applies to only the 32 assets and removes the licensing blocker for their continued technical qualification. It is not a receipt, EULA, approval for all Hergel/Terre, or documentation of attribution/distribution terms. Do not request ownership approval again. Source documents are needed later to document a distribution route and select additional content.

[measured: `IDX`; `CAT`, matching Hergel IDs] Sources divide as follows:

| Source family in archive catalog | v3 assets covered by approval | Documentation missing beyond technical qualification |
|---|---|---|
| `Arabic Neoclassical` — `Buildings/Mesh` | H0013, H0014, H0015, H0016 — 4 | Package/creator/purchase and version covering these Unity files. FDB has `Arabic Neoclassical Tall Residential Complex Building`, UID `3bfa0491-13d2-487b-8609-b9e040a30906`, and `V\ArabicNe9cd2941a73aeV1\manifest` identifies it; this is a **research lead only**, not a proven match to the four files. |
| `Arabic Neoclassical/Street Props Pack/FBX` | H0025, H0034, H0039, H0043, H0046, H0051, H0058, H0059, H0060, H0077, H0079, H0081, H0082, H0083, H0089, H0090, H0091, H0094 — 18 | The Street Props package document itself and textures/graphics; do not assume the Fab buildings package includes it. |
| `_Unsorted/.../uploads_files_*` | H0902 `2396890_Slum_k`, H0903 `2396971_Slum_s`, H0904 `2396986_Slum_v`, H0905 `2398623_Arab_x1`, H0906 `2398636_Arab_x2`, H0907 `2401910_Arab_x3` — 6 | Link/invoice/creator permission for each product, matched to download numbers and textures; a downloads folder name is not a store or license. |
| `Assets/Imports/Environment/NYCAlley/Meshes/SM_AirConditioner.fbx` | H0650 — 1 | Source AC document and conversion permissions. NYCAlley in a name alone does not prove coverage by the other Leartes kit purchase. |
| `Assets/Imports/Environment/Desert Vegetation Pack/Models` | H0636 `Acacia`, H0647 `Nopal` — 2 | Package/model/texture source. If a missing billboard is recovered, identify that source file and its permission; no automatic expansion to a new substitute. |
| `Assets/CityGen3D/Meshes/Ambient-Occlusion/CoconutPalm.asset` | H0958 — 1 | CityGen3D product and exact origin of the tree/textures within it; do not assume a tool license determines all third-party content. |

Total: 4 + 18 + 6 + 1 + 2 + 1 = **32**. The source check matches IDs and paths in the historical catalog; it is not binary proof that a purchased product contains them. [not run: SOURCE-PACKAGE-LICENSE-MATCH]

### Exact scope list

Every name below is under `/Game/Project/Shared/Bank_ME_v3/`; subfolder is supplied to prevent extending approval to a similarly named asset elsewhere. [measured: `IDX`, 2026-09-29]

| Folder | Exact asset names |
|---|---|
| `Buildings` / 10 | `SM_H0013_Building_04`, `SM_H0014_Building_01`, `SM_H0015_Building_02`, `SM_H0016_Building_03`, `SM_H0902_Slum_k_fbx`, `SM_H0903_Slum_s_fbx`, `SM_H0904_Slum_v_fbx`, `SM_H0905_Arab_x1_fbx`, `SM_H0906_Arab_x2_fbx`, `SM_H0907_Arab_x3_fbx` |
| `Props` / 10 | `SM_H0034_Cart`, `SM_H0043_Foodcart_001`, `SM_H0046_Foodcrate`, `SM_H0058_Gaz`, `SM_H0059_Grill_`, `SM_H0077_Stones_Stack`, `SM_H0089_Tires`, `SM_H0090_Watertank`, `SM_H0091_Watertank_001`, `SM_H0650_SM_AirConditioner` |
| `StreetFurniture` / 8 | `SM_H0025_Barrier`, `SM_H0051_Garbagebin`, `SM_H0060_Metal_Barrier`, `SM_H0079_Streetlight`, `SM_H0081_Streetpowerbox`, `SM_H0082_Streetsign`, `SM_H0083_Streetsign_001`, `SM_H0094_Woodenpole` |
| `Vegetation` / 3 | `SM_H0636_Acacia`, `SM_H0647_Nopal`, `SM_H0958_CoconutPalm` |
| `Vehicles` / 1 | `SM_H0039_Destryoedcar` |

## Additional archive sources

All families below lack entitlement/permission documents, terms applicable to the exact content, and model+texture mapping. Use state: **open**, except for the exact v3 assets already specified. Sharing a source folder does not extend approval. [documented: `LICENSE_PROVENANCE.md`; measured: `IDX`, `CAT`]

| Family / group | Exact evidence and what it proves | Next required document |
|---|---|---|
| `Hergel_NYCAlley` / 5 kit parts, plus 44 NYCAlley source rows | `LIB\CityBLD_Kits\Hergel_NYCAlley\Evidence\source_provenance.json` lists `LeartesStudios/NYCAlley` source, hashes, and part paths; it explicitly says it grants no new/transferred license | Matching NYCAlley purchase and terms of use/conversion, including textures; match the five parts to the purchase. |
| `Terre_Rural` / 5 parts; RuralTown House / 17, Barn / 3 | `CAT` and `IDX`: `Assets/Assetforbank/HIVEMIND/RuralTown/HDRP(Default)/Art/Meshes/...` | RuralTown document and permission to use converted files; an HDRP path is not authorization. |
| Additional `Arabic Neoclassical` — Buildings / 6, Street Props / 41, Street Road / 3 | `IDX.source_package` and `CAT.source`; explicit Unity paths | Document for every selected subpackage; do not extend the 32-v3 approval to them. |
| Additional `CityGen3D` / 16 | `IDX`: `Assets/CityGen3D/Meshes/{Ambient-Occlusion,Benches,Fences,Plants,Public Transport,Sidewalks,Street Lights,Waste}` | Product and third-party content documents for each selected family. |
| `Assets/Bank/*` / 17 | `IDX`: Bushes 8, Grass 4, Rocks Materials 3, Rocks Meshes 1, Trees 1 | First identify source package and creator; Bank in a name is not commercial provenance. |
| `Industrial_Zone_Modular_Pack` / 6 | `IDX`: `Assets/Industrial_Zone_Modular_Pack/Models` | Product/creator/purchase and terms for models and textures. |
| `Chinese_Alley` / 3 | `IDX`: `Assets/Imports/Environment/woralde/LeartesStudios 1/Chinese_Alley/HDRP/Art/Meshes` | Exact Chinese Alley document, including version and conversions. |
| `PostApocalypticTown` / 2 | `IDX`: `Assets/Imports/Architecture/HIVEMIND/PostApocalypticTown/HDRP(Default)/Art/Static_Mesh/Merged` | Source package document and contents of merged files; visual fit for the area is a separate decision. |
| `Arab_x4`, `Arab_x7`–`Arab_x18`, `Arab_x20`, `Arab_x21`, `Arab_x23`–`Arab_x31`; `24-middle-east-buildings` / 25 total | `IDX.source_package` retains each candidate's `uploads_files_<id>_<name>` folder and the middle-east-buildings package GUID | Purchase/permission for every selected product and mapping to the download ID; do not assume an Arab_x1 document covers them all. |
| `Desert Vegetation Pack` outside v3 | `CAT` includes, for example, Terre id 0 `Assets/Assetforbank/Desert Vegetation Pack/Models/Acacia.FBX`; `FULL_INDEX.csv` has no license | Source package and texture document; the same Acacia name does not authorize copying the other asset. |
| `Terre_SpeedTree` / 6 | [measured: `LIB\Sources\Terre\SpeedTree`] `Conifer.st`, `Cypress_Forest_Desktop.st`, `Pine_A.st`, `Pine_B.st`, `Pine_C.st`, `Pine_D.st` | Origin and license of each tree and its textures; a software license alone is not a content document. |

## Match to Run02 and documents to request from Aviv

[documented: `R02`, opening and Readiness verdict] Run02 has partial visual coverage of all 32 v3 models and all 33 Palms meshes, within 75 of 930 current rows with partial views; 855 remain. It changed neither rights nor qualification flags. Seven v3 views rely on Run01. **The 33 Palms meshes include grass/shrubs/add-ons; they are not 33 palms.** Views do not establish entitlement or a license.

[inference] Proposed collection order to minimize requests for documents that affect an actual selection:

1. **Palms_Pack_01:** Library image/export or purchase confirmation identifying the product and authorized account, acquisition date, and document applying to that acquisition. Include ID `9f81069d-877c-4d4e-aa28-30f5d1a8d8c9`. Then link the manifest and package version to selected candidates.
2. **The selected building kit:** First `ModularCourtyard`, `ModularBuildingSet`, or `MOUT_Arabian`; collect the same evidence for whichever package is selected. `ProceduralBuildingGenerator` needs separate evidence if its parts are chosen. Source folder and purchase confirmation should identify the same version and dependencies.
3. **The selected ground/road material:** `FC_Coastal_Landscape`, `StarterContent`, or another source package — document the exact asset, source, and applicable terms. Do not require a Fab receipt for `StarterContent` before identifying its origin.
4. **Any archive expansion:** Only packages selected for a missing role, with product/creator/ID/date/terms and texture mapping. Prioritize NYCAlley/RuralTown if a parts kit is selected, or vegetation if a substitute is selected. Other style packages remain low priority.
5. **For v3 distribution:** Do not request ownership confirmation again; complete documents for the six source families in the table, including attribution, source sharing, and distribution terms relevant to intended use. This document cannot determine them without the documents.

For each package, a document connecting **who acquired → which product and version → when and under what terms → which candidates and dependencies** is better than an unidentified library screenshot. Payment details may be redacted; retain product name, date, transaction/entitlement ID, and authorized identity needed for matching. If direct creator permission exists, document the files and uses it covers.

**Manager decisions after receiving documents:** Record a decision for each selected package and each candidate covered by it; do not change `rights_state` globally for all Hergel/Terre. This inspection did not edit the catalog or close `BANK-RIGHTS-CLOSE`. [not run: BANK-RIGHTS-CLOSE]

## Fingerprints of sources read

[measured: SHA256, 2026-09-29]

| Document | SHA256 |
|---|---|
| `Staging/ModelBank/LICENSE_PROVENANCE.md` | `9954e09a13e04a6c91236a25909b7d0a5225462f344104c5879735d5959def5f` |
| `Staging/ModelBank/BANK_CANDIDATE_INDEX_2026-09-28.csv` | `b05f8691402b47b4c6730f842163bd0555662c0802d4ca7eaadfe04266dccc9f` |
| `R02` | `8fe4c965730d1a7f66ee879b3bb8e05cdf4db4b2c55de2702357fcab7a1cc270` |

Search scope: the bank documents named above, archive catalog/sources, and local Vault/Fab. No general search of email, accounts, disks, or private contracts was performed; “missing” means not found in this evidence. [not run: PRIVATE-RECEIPT-SEARCH]
