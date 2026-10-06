# AssetId-level model-bank review ledger — 2026-10-01

This is an **offline crosswalk and per-AssetId review**, not a model qualification, release or visual acceptance. The CSV preserves the exact 1,215 AssetIds and index order, adds one assessment row for each, and keeps the historical preliminary index decision separate from the final 2026-09-29 disposition and later 2026-10-01 selection holds. No source asset, native DataTable, HDA, Unreal session, Houdini session or Linear item was changed.

## Scope and result

- [measured: source CSV/JSON crosswalk and current filesystem] **1,215 unique AssetIds**, **324 families**, 930 current and 285 external rows; 1188 asset candidates and 27 family candidates. All 1320 recorded source-member path references currently resolve to files, and each row's member count matches its path list. The index, disposition, v8 inventory, v2 disabled catalog and v8 candidate-inspection JSON have identical AssetId sets. Family, scope, source package, rights state, native class and technical state match across applicable records. The 898 current native StaticMesh paths match the disabled v2 catalog; the 317 other catalog paths are blank by design.
- [documented: final disposition] **1213 reserve, 2 exclude**. The two final exclusions are `SM_Sky_sphere_overcast` and `SM_Sky_sphere_sunday`; the index's 28 preliminary `decision=exclude` suggestions are not the final disposition.
- [measured: disabled catalog and live GazaRimal receipts] All 1,215 v2 rows remain `RunEligible=false`, weight zero and have blank ReleaseId/DecisionId. v004/v006 native readback observed 1,215 disabled rows and zero catalog model instances. The row metadata's transport is not native placement of the corresponding models.
- [measured: v8 inspection] 898 current StaticMeshes had native bounds, material-slot, LOD/Nanite and dependency queries; 131 candidate rows reach at least one unresolved dependency. The external source and family rows were hashed but were not imported into this project. 75 current rows have only partial native visual previews.
- [documented: owner decision; measured: direct-picker receipt] Four exact `Bank_ME_v3` rows (`H0013`, `H0907`, `H0051`, `H0958`) remain **technical-check-only**. `SM_H0636_Acacia` retains a foliage repair hold. `SM_utility_pole_1` has one-site direct-picker pilot permission at `GazaRimal:pole_144276113_2_2`. An earlier v002 direct-picker proof completed a fresh reopen and same-input replace-bake with one pole component and 16 map actors, while Cook/LayerInfo residue remained. The later v006 saved map reopened with two overlapping pole components; v007 has no fresh-process reopen yet. These lifecycle results must remain separate. Its canonical v2 row stays disabled. `SM_H0094_Woodenpole` is out of the current review slate.
- [inference, held conservatively] The later shortlist says Aviv declined "both earlier proposed" `Palms_Pack_01` meshes but does not give AssetIds. The preceding two-palm qualification queue named `SM_Palm_01_03_G` and `SM_Palm_01_08_G`; those two rows are marked `declined_from_current_review_slate_id_inferred`. This does **not** alter their final 2026-09-29 reserve disposition. Confirm the exact two IDs against Aviv's decision record before changing any source index or asking for renewed selection. All 33 Palms Pack rows remain disabled.

## How to read the CSV

`WhatAssetIs` and `PossibleEnvironmentalRole` use the exact indexed name, native class, representation and semantic role; a role based on names and paths is explicitly an inference. `RecordedChecks` summarizes the existing per-AssetId native or source inspection and the disabled table transport. `RecordedVisualObservation` quotes prior index evidence where available; it is not a new visual review. `PriorTechnicalGaps` preserves the original index wording even where later v8 measurements addressed a narrow part of it; `MissingChecks` states the remaining practical checks after the measured native/source inspection. `SafeNextTechnicalAction` is a preparation or future bounded check, never a release instruction. The rights and visual columns identify decisions Aviv must make for each exact ID, with deferral for excluded/held rows.

The v8 registry query measured 898 current StaticMeshes, but local AABBs, zero unresolved dependencies and package presence do not certify anchor, direction, shader appearance, collision, runtime cost or contextual suitability. The 27 external family records are grouping candidates, not selectable meshes. Nonmesh classes (materials, material functions, foliage configurations and redirectors) are explicitly identified so a row's catalog presence cannot be mistaken for a usable StaticMesh.

## Source and verification fingerprints

| File | SHA-256 |
| --- | --- |
| `BANK_CANDIDATE_INDEX_2026-09-29.csv` | `B9B0EBCAFF37ED3B0062BF54054FDBED3612C87EA7C98417BBDA9462079E3717` |
| `BANK_1215_DISPOSITION_RECORD_2026-09-29.csv` | `1D35AC00B8DC1C3B10F48389D9181BE80F0E4358404FFFA5DDF7D40B38165D09` |
| `UnifiedCatalogV2_2026-10-01\inventory_snapshot_v8.csv` | `5B600D39C61BFB5082B26850E7B13AFB9BA6EE0AEE5653F63B87422D3E4CAF0A` |
| `UnifiedCatalogV2_2026-10-01\catalog_v2_full_disabled.csv` | `ACA96D5C9EB14D73B1853F55600A9752417BEEBE99B6E9A92C4556BFDCFCA458` |
| `Connection_2026-09-30\candidate_inspection.json` | `9812B7C174A10D60EFFA377573995B83BBF5FBA8EC7C2D49BFED8B312DFC1D6C` |
| `BANK_ASSETID_REVIEW_LEDGER_2026-10-01.csv` | `A5E3B286E6C21A4B029AFD8200EA820ED85E36FF8AAB8A987C9A34A5D9B7801B` |

The script reparses the written CSV and verifies 1,215 unique IDs in source order; exact ID sets, selected metadata and all-disabled flags are asserted. Counts: current/external `{'current': 930, 'external': 285}`, final dispositions `{'reserve': 1213, 'exclude': 2}`, record kinds `{'asset_candidate': 1188, 'family_candidate': 27}`, current review holds `{'all_disabled_reserve': 1204, 'one_site_direct_picker_pilot_only_catalog_disabled': 1, 'technical_check_only': 4, 'excluded_from_current_review_slate': 1, 'repair_hold_opaque_foliage_cards': 1, 'final_exclude_sky_lighting': 2, 'declined_from_current_review_slate_id_inferred': 2}`, rights states `{'unverified': 345, 'owner_confirmed_for_technical_qualification': 32, 'acquisition_record_terms_unverified': 520, 'exact_listing_identified_terms_unverified': 33, 'unconfirmed': 199, 'local_acquisition_reported_terms_unverified': 86}`. No live application check was run for this ledger.

## Sources and limits

- [measured: `BANK_CANDIDATE_INDEX_2026-09-29.csv` (v8 content), `Connection_2026-09-30/candidate_inspection.json`, `BANK_1215_DISPOSITION_RECORD_2026-09-29.csv`, `UnifiedCatalogV2_2026-10-01/inventory_snapshot_v8.csv`, `UnifiedCatalogV2_2026-10-01/catalog_v2_full_disabled.csv`]
- [documented: `Connection_2026-09-30/RESULT.md`, `UnifiedCatalogV2_2026-10-01/FULL_DISABLED_CATALOG_RESULT.md`, `BANK_DISTINCT_CANDIDATE_SHORTLIST_2026-10-01.EN.md`, `RIGHTS_DECISION_PACKET_2026-09-29.EN.md`, `DirectPickerPilot_2026-10-01/authorization.json`, `../TrackA_Tests/HoudiniCityProof/GeoCity_direct_picker_UI_2026-10-01/RESULT.md`, `../CURRENT_STATE.md`]
- [not run: live editor/Houdini, new mesh previews, new rights-account verification, placement or qualification tests]
