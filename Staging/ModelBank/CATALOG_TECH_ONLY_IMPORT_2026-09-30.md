# Technical-only bank catalog input — 2026-09-30

**Later state, 2026-10-01:** This four-row v1 CSV is a preserved technical fixture. The active full-bank v2 source and disabled 1,215-row native DataTable are documented in [the v2 schema](UnifiedCatalogV2_2026-10-01/SCHEMA.md) and [v006 live result](../TrackA_Tests/HoudiniCityProof/GeoCity_v006_update_UI_2026-10-01/RESULT.md). The original 2026-09-30 observations below remain historical; no real catalog row has been enabled. [measured: v006 live readback]

**State:** import-ready CSV and agreed HDA input fields; no native Unreal DataTable was created, bound, or cooked. The four rows are technical-check candidates only. `RunEligible=false` on every row is mandatory under Aviv's latest instruction. This file is not a qualified bank release or permission to place these meshes in a generated environment.

## Delivered input

- CSV: `CATALOG_TECH_ONLY_IMPORT_2026-09-30.csv`, SHA-256 `2552EF07EA5761A9EB6C449B95409076C62999652F83574F31CDA3F2FE9787DD`.
- Four exact current `/Game/Project/Shared/Bank_ME_v3` Static Mesh object paths and mesh-package hashes are copied from the 28-row first qualification queue. All four present `.uasset` files matched those hashes during preparation.
- H0013, H0907 and H0051 have native asset-local AABB values from the v7 index; their recorded bounds extensions are zero. `AnchorZCm` copies measured local minimum Z under the first-release bottom-offset convention. H0958 has no measured AABB: zero numeric placeholders are explicitly invalid. Orientation is unmeasured for all four.
- Role labels (`whole_building`, `street_prop`, `vegetation`) describe candidate geometry type only. They do not approve style, zone, selection weight or use in an environment.

## Native DataTable wire

Use one native Unreal DataTable as **Geometry Input 0** of the HDA. Its row struct needs the CSV columns below in this order and with these Unreal types. `Name` is the DataTable row key, not a struct property. The agreed HDA parser accepts the numbered translator names and bare names in offline fixtures; it must reject any enabled row with missing bounds, anchor or orientation.

| Ordinal | Field | Unreal type | HAPI point attribute from installed plugin |
| ---: | --- | --- | --- |
| — | Name | row key | `unreal_data_table_rowname` |
| 1 | SchemaVersion | Int32 | `unreal_data_table_1_SchemaVersion` |
| 2 | AssetId | String | `unreal_data_table_2_AssetId` |
| 3 | ObjectPath | String | `unreal_data_table_3_ObjectPath` |
| 4 | Role | String | `unreal_data_table_4_Role` |
| 5 | VariantId | String | `unreal_data_table_5_VariantId` |
| 6 | RunEligible | Boolean | `unreal_data_table_6_RunEligible` (int8) |
| 7 | BoundsValid | Boolean | `unreal_data_table_7_BoundsValid` (int8) |
| 8–13 | BoundsMinXCm/YCm/ZCm, BoundsMaxXCm/YCm/ZCm | Float32 × 6 | `unreal_data_table_8_...` through `_13_...` |
| 14 | AnchorValid | Boolean | `unreal_data_table_14_AnchorValid` (int8) |
| 15 | AnchorZCm | Float32 | `unreal_data_table_15_AnchorZCm` |
| 16 | OrientationValid | Boolean | `unreal_data_table_16_OrientationValid` (int8) |
| 17 | ForwardAxis | String | `unreal_data_table_17_ForwardAxis` |
| 18 | AssetRevision | String | `unreal_data_table_18_AssetRevision` |

The installed official plugin's `UnrealDataTableTranslator.cpp` creates one point per row (line 198), prefixes each column with `unreal_data_table_<ordinal>_` (lines 313–329), and maps Boolean to int8 (lines 365–376), Int32 to int (lines 446–456), Float32 to float (lines 515–525), and other simple values to strings (lines 798–815). Its separate `unreal_object_path` attribute identifies the **DataTable asset**, not the row's mesh. The HDA must take mesh paths from numbered `ObjectPath`, then emit them as `unreal_instance` only for eligible rows. Source support is documented, not a measured live DataTable round trip. [documented: `Plugins/HoudiniEngine/Source/HoudiniEngine/Private/UnrealDataTableTranslator.cpp`; `HoudiniEnginePrivatePCH.h`:311–313]

## Release gate and exact blocker

No row may be switched to `RunEligible=true` from this fixture. For any future selected asset, Track A must first record exact package and material-dependency revisions, a native load/reference check, required bounds/anchor/orientation and role data, visual suitability, and an explicit permission for the intended generated-environment use. Aviv has kept the four rows here at **technical checks only**; the previous owner confirmation covers technical qualification of the exact 32 Bank_ME_v3 meshes and does not expand that instruction. The rest of the 1,215-row index has no verified generation-use release either. [documented: `LICENSE_PROVENANCE.md`; `RIGHTS_DECISION_PACKET_2026-09-29.EN.md`; measured: `BANK_CANDIDATE_INDEX_2026-09-29.csv`]

The native DataTable import, geometry-input binding, observed HAPI attribute names/values, row rejection and any `unreal_instance` output remain **not run**. This CSV deliberately contains zero enabled rows, so a successful technical transport check should produce zero bank instances. It cannot prove qualified bank placement. [not run: CAT1, INST1]
