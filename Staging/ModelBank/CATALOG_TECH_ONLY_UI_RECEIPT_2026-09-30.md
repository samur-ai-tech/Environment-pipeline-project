# Native technical-only catalog UI receipt — 2026-09-30

## Scope and session

[measured] B03 was performed through the ordinary Unreal Editor 5.8.2 UI in `Environmentpipeline`. The source was `CATALOG_TECH_ONLY_IMPORT_2026-09-30.csv` (SHA-256 `2552EF07EA5761A9EB6C449B95409076C62999652F83574F31CDA3F2FE9787DD`). No commandlet, editor script, model placement, HDA cook, bake, map save, or Linear action was used.

[decided: Aviv 2026-09-30] The previous `Untitled*` B2 test state with three unsaved packages could be discarded. [measured] The original project editor PID 12028 and HARS PID 25420 exited through the UI after **Don't Save**. Its `Saved/Autosaves/` restore files were left in place. A separate Unreal Editor PID 15476 was not operated.

## Saved native assets

| Asset path | Purpose | SHA-256 |
| --- | --- | --- |
| `/Game/Developers/USER/ModelBankProof/CatalogTechnicalOnly/S_CatalogTechnicalOnlyRow` | User-defined row structure | `FAA8A775C3451447B4CE9419E4DC30257AA0D3FDF03AFDFC01ACB165F9A96942` |
| `/Game/Developers/USER/ModelBankProof/CatalogTechnicalOnly/DT_CatalogTechnicalOnly_2026_09_30` | Four-row DataTable | `77D5B6A79CEBE5EAD5204FD447351F3480E79CF6AE5911450CC8AB61EE7D3B6A` |

[measured] The structure has the 18 fixture fields in order: `SchemaVersion`, `AssetId`, `ObjectPath`, `Role`, `VariantId`, `RunEligible`, `BoundsValid`, `BoundsMinXCm`, `BoundsMinYCm`, `BoundsMinZCm`, `BoundsMaxXCm`, `BoundsMaxYCm`, `BoundsMaxZCm`, `AnchorValid`, `AnchorZCm`, `OrientationValid`, `ForwardAxis`, `AssetRevision`. CSV `Name` is the DataTable row key. The structure was saved with its own Save button; the DataTable was saved as its named asset, including a final explicit **Save** on that selected asset. **Save All** was not used. Only these two `Content/` files had write times after the 15:21 lease began.

[measured] Unreal's UserDefinedStruct UI labeled its `Float` choice **Float (double-precision)**. The seven bounds/anchor numeric fields therefore use double precision, a precise deviation from the fixture's planned Float32 type. [documented: `Plugins/HoudiniEngine/Source/HoudiniEngine/Private/UnrealDataTableTranslator.cpp:515-531`] The installed official translator maps `FFloatProperty` to `HAPI_STORAGETYPE_FLOAT` and the double path to `HAPI_STORAGETYPE_FLOAT64`. [not run: HDA DataTable input inspection] Actual HAPI storage for this table must be measured when it is connected to the city HDA; this receipt does not claim that integration.

## Readback and fresh-process persistence

[measured] The DataTable UI showed four keys: `H0013`, `H0907`, `H0051`, `H0958`. All four `RunEligible` values were `False`, all four `OrientationValid` values were `False`, and all four `ForwardAxis` values were empty. `H0958` had `BoundsValid=False` and `AnchorValid=False`; the other three had both flags `True`.

[measured] A native **Export as CSV** produced `CATALOG_TECH_ONLY_UI_READBACK_2026-09-30.csv`. Comparison with the fixture found four rows, 19 CSV columns including the key, matching keys and strings, matching Boolean values after case normalization, and no numeric difference above `0.000001` cm. The largest difference was `0.0000005` cm because Unreal's export writes six decimal places. The exported key header is `---`, rather than the fixture's `Name`.

[measured] The editor was closed and the project reopened in a new process (PID 2916). The saved DataTable loaded with the four rows and the saved row type. A second native export, `CATALOG_TECH_ONLY_REOPEN_READBACK_2026-09-30.csv`, was byte-identical to the first export; both have SHA-256 `0EC1F46D390C125D64406140230EC2D6E970CA6ACF8C3A25A8DC91DA6643D0CF`. A final process (PID 29512) explicitly saved the selected DataTable; its asset hash remained unchanged. The editor's last observed map was `Untitled` without a dirty marker, the status was **All Saved**, and the Outliner showed 138 loaded actors. The temporary asset-editor placement preference was returned to `Default`.

[measured: process check 2026-09-30 16:36 +03:00] Project editor PIDs 12028, 21208, 2916 and 29512 were no longer running; no HARS process was running. The unrelated Unreal Editor PID 15476 and pre-existing `houdini_launcher`/`houdini_installer` processes remained untouched. No project editor window or dirty package was left under this lease.

## Limit

This table is a disabled technical catalog interface. It does not qualify model rights, approve visual use, enable generator selection, connect the HDA, prove HAPI column types, or establish city acceptance.
