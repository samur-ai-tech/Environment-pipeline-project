# Indexing and catalog maintenance

Use [Files and state](FILES_AND_STATE.md) for current paths, revisions and status. Follow [Rules](RULES.md) before any write, [Connection](CONNECTION.md) for the retained Houdini/Unreal route, and [Modular workflow](MODULAR_WORKFLOW.md) for adapted building parts.

Updated 18 October 2026. For Houdini bank work, start at the single [Bank entry point](README.md). The [binding catalog](FILES_AND_STATE.md#houdini-input-catalog) and [delivery queue](../../Staging/HoudiniBankConsolidation_2026-10-18/DELIVERY_QUEUE.csv) are derived navigation/work views; neither publishes rows or changes eligibility. Native table/material/import operations below belong to their receiving owner when outside the current task.

This guide distinguishes the available inventory tools from native bank publication and the engineering work still needed for general intake. Reading this guide does not activate historical assignments or scripts.

## Choose the correct index

| Layer | What it describes | Identity and authority |
|---|---|---|
| Legacy `Staging/ModelBank/FULL_INDEX.csv` | The old Hergel/Terre archive and its import reports | The pair `source_bank` + `id`; historical provenance, not current selection |
| `Staging/AllAssetScan_2026-10-07/` | Saved packages under project Content and local project plugins | Package path, mount and saved registry class; discovery only |
| Historical `catalog_v4_source.json` / `catalog_v4_full.csv` packets | Rich provenance, decisions and runtime projections | Preserve existing `AssetId`, row `Name` and `ObjectPath`; historical packets are not automatically the current authoring source |
| `DT_EnvironmentBank_AnyArea` and its verified native readback | The shared runtime bank consumed by the retained system | Exact native package hash, typed rows, schema and catalog digest |
| Source-family registries and kit manifests | Assembly recipes, interfaces and native part references | Family/version/part identities; recipe flags are separate from bank eligibility and acceptance |
| `CATALOG_DATA.json`, HTML, CSV and thumbnails | A derived review snapshot | Its source export, package hashes and receipt; browser marks do not change the bank |

Do not add these row counts together. Archive models, canonical records, modular parts and supplier candidates overlap. A discovered package or imported mesh does not establish selection, consumer support or accepted output.

## Refresh the saved file inventory

The documented offline entry point is [RunScan.ps1](../../Staging/AllAssetScan_2026-10-07/RunScan.ps1). From PowerShell:

```powershell
& 'C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\AllAssetScan_2026-10-07\RunScan.ps1'
```

The script uses the installed Unreal Python runtime without opening an editor. Its [README](../../Staging/AllAssetScan_2026-10-07/README.txt) defines the scope and limitations.

1. Input: saved project Content, local plugin Content roots and optional historical `FULL_INDEX` path hints. Unsaved buffers, other projects and Epic VaultCache are excluded.
2. Output: a new `runs/<timestamp>/` containing `assets.csv`, `assets.json`, `packs.csv`, duplicate information, `REPORT.txt` and `asset_browser.html`. Top-level copies and `LATEST.json` point to the latest run.
3. Check: successful exit, reported scope, unknown classes, read errors and changes during the scan. Inspect the timestamp before using a browser or CSV as current evidence.
4. Interpretation: class and duplicate results describe saved files. They do not update canonical IDs, holds, materials, selection or assembly rules. Equal bytes and visual similarity are different checks.

The scanner writes its own output folder. Do not run it during a documentation-only or report-only assignment unless that output write is in scope.

## Preserve legacy provenance

[build_full_index.py](../../Staging/ModelBank/build_full_index.py) reconstructs `FULL_INDEX.csv` from the old `GIS_WorldBLD` library catalog, source reports and native import reports. It has fixed archive paths and a fixed snapshot size, and overwrites that CSV.

Use it only for an explicitly scoped legacy-index rebuild. It is not a current bank rescan, new-model registration tool or AnyArea exporter. [Archive notes](../../Staging/ModelBank/ARCHIVE_NOTES.md) explain the actual source layout and the limits of the old material/texture counts. Preserve the source-bank field when matching numeric archive IDs.

## Establish the current bank baseline

The native package is `/Game/Project/Shared/ModelBank/DT_EnvironmentBank_AnyArea`. Its saved file is `Content/Project/Shared/ModelBank/DT_EnvironmentBank_AnyArea.uasset`.

The current native authority is [CURRENT_NATIVE_BANK_READBACK.json](../../Staging/HoudiniBankFixes_2026-10-18/CURRENT_NATIVE_BANK_READBACK.json), explained by the [18 October permanent-fix result](../../Staging/HoudiniBankFixes_2026-10-18/RESULT.md). It follows the [marked-item removal](../../Staging/BankMarkedRemoval_2026-10-18/RESULT.txt) and preserves all of its exclusions. The earlier [NATIVE_HANDOFF.txt](../../Staging/SharedBankConnection_2026-10-08/NATIVE_HANDOFF.txt) remains dated publication evidence. Confirm the current package hash matches the current export before relying on its rows. If it differs, obtain a fresh scoped native export; do not label an older export current.

Keep these facts separate:

- A native readback proves the exported table revision, not a new HDA Cook or current map appearance.
- `HDA_CATALOG_RECEIPT.json` is evidence from its recorded Cook. A later content-only change must not rewrite it as synthetic generation evidence.
- The older intake code's `Staging/ModelBank/PermanentIntegration_2026-10-02/catalog_v4_source.json` and companion CSV paths are absent. Preserved transaction or ApplyBundle copies must not be silently promoted to replace them. Resolve authoring-source ownership through the current state page before intake work.

## Change existing rows

This is native publication under the current owner and exact assignment, separate from inventory. Do not reuse a historical PID, endpoint, lease, before-hash or output label.

1. Input: a fresh native row export, exact before-package hash, authorized per-AssetId field diff, unchanged identities/holds outside that diff, and all profiles consuming the shared table.
2. Prepare: retain the before snapshot and proposed complete row set; run the [shared publication preflight](#existing-row-publication-preflight). It computes the typed digest and exact changed fields, checks all current consuming profiles, and requires exact-revision evidence for changed physical claims. Keep unknowns unresolved; missing proof is not proof of a bad asset. Material/consumer evidence remains required for its applicable route. The tool verifies retained measurements and reviews; it does not create them automatically.
3. Existing mechanism: [SharedBankConnection/write_table_rows.py](../../Staging/SharedBankConnection_2026-10-08/Tools/write_table_rows.py) checks its assigned PID, clean state, before hash, schema, digest and existing row-name set before one named table save. It now invokes the same shared publication check before filling the table and requires full typed JSON equality before saving; column-string differences remain diagnostic. It preserves identity, holds, eligibility, area/release and consumer policy. It remains bound to its historical row count/task: the current owner must provide a reviewed task binding, never replay a released assignment. The earlier [bounded binding](../../Staging/HoudiniBankFixes_2026-10-18/Tools/publish_contact_rows.py) now passes its qualification file explicitly. Its prior [fresh-process readback](../../Staging/HoudiniBankFixes_2026-10-18/receipts/FRESH_NATIVE_VERIFICATION.json) proves that earlier data transaction, not execution of today's source change.
4. Verify: export all actual rows after the named save, compare intended values, record the saved package hash, inspect dirty state, and obtain fresh-process reopen evidence within the owner's scope.
5. Publish profile changes: update every affected profile's row count and catalog/release digest fields with backups and receipts. [patch_profile.py](../../Staging/BankSimplification_2026-10-07/Tools/patch_profile.py) supports individual profile fields. The later `sync_connection_profiles.py` names only its original two profiles; do not treat that list as the full current consumer inventory.
6. Verify normal generation separately through [Connection](CONNECTION.md), then publish a matching review snapshot. A successful table save alone does not complete that sequence.

### Existing-row publication preflight

Implemented 18 October: [publication_checks.py](../../Staging/ModelBank/publication_checks.py) is the common file-only entry point and the existing native writer's validation module. [Implementation and checks](../../Staging/BankPublicationGuard_2026-10-18/RESULT.md) distinguish source/fixture verification from native execution.

Later native evidence: [accepted iteration 001](../../Staging/HoudiniBankVerificationLoop_2026-10-18/Review/Iterations/001/VERDICT.md) exercised one actual identical-value fill, named table save and independent fresh typed readback of all 1,295 rows. Changed-value native publication remains open. The current profile inventory is six; the shared preflight discovers all consumers dynamically, while historical task bindings/receipts retain their original five-profile scope. Coordinate remaining automation through B01 in the [execution plan](../../Staging/HoudiniBankImprovementRoadmap_2026-10-18/EXECUTION_PLAN.md).

From the project root, use a fresh verified native readback as `--before`, proposed complete typed rows as `--after`, and repeat `--qualifications` for each applicable existing-format `CONTACT_QUALIFICATIONS` document:

```powershell
python -B Staging/ModelBank/publication_checks.py --before <CURRENT_NATIVE_BANK_READBACK.json> --after <PROPOSED_ROWS.json> --qualifications <CONTACT_QUALIFICATIONS.json> --out <Staging/OwnedTask/NewPreflight>
```

The angle-bracket values are placeholders for owned inputs, not a literal command. `--out` is optional; when supplied it must be a new folder under project `Staging`. Without it, the command only reads files and prints the result. It opens no application and writes no table/profile/HDA/model.

- Inputs: current table package/hash and typed readback, unchanged identities/schema/policy, proposed rows, and exact-revision physical qualifications for changed bounds, anchor, axis, validity or model revision.
- Checks: strict types and finite values; identity uniqueness; preserved holds/eligibility/consumer/area/release policy; measured bounds, support vertices and reviewed facing; referenced geometry/image/measurement/native hashes; every current consuming profile's before digest/count.
- Output: one `PUBLICATION_CHECK.json` with exact field changes, resulting typed digest, input hashes and all affected profile targets. This is a derived publication plan, not another catalog or an applied profile update.
- Failure: stop before native fill; resolve the named identity/revision/evidence mismatch. Do not alter flags, fabricate evidence or change an old hash to force a pass. An unchanged row does not require a new individual review on every transaction.
- Native handoff: pass `qualification_files` to the reviewed owner-bound writer. After the table save, use the existing profile patcher for each derived target; independently read back/reopen before treating the transaction as persisted. Never use an old packet or run during generation. This first repair does not automate the entire publication transaction or add new-identity admission.

## Add a model or adapted family

Start with [Modular workflow](MODULAR_WORKFLOW.md) when geometry, interfaces, assembly rules or native aliases change. Reuse an existing canonical identity when the source/model is already registered; use explicit family/version/part identities for derivatives. Never use model name or gallery order as the identity key.

Required intake inputs include exact source/native paths and hashes, material/texture bindings, measured geometry and units, pivot/contact/axes, LOD and slot contracts, role/consumer requirements, provenance and preserved holds. Record unknown fields explicitly. Outputs must distinguish prepared source, native import, registration, selection, actual output and acceptance.

**Current engineering gap:** there is no documented general new-identity publisher for the current AnyArea bank. The existing AnyArea row writer preserves the same names and count. It cannot be used as-is to insert new identities.

The older [native supplier](../../Staging/NativeUnrealAssetSupply_2026-10-04/native_supplier.py) already contains useful deduplication, held additive transactions, before/after checks and native readback logic. However, it targets `DT_EnvironmentBank_v4` and the missing rich-source paths above. Its sealed command packets are historical examples, not runnable current-AnyArea intake instructions.

The assigned engineer must adapt and review that retained mechanism against the declared current source, AnyArea schema, new row-count support and every affected profile. Preserve existing identity, hold and hash checks; prepare a new versioned packet rather than weakening frozen guards or creating another bank.

Complete only the publication capability required by the next intended delivery. Search its existing writers/callers and identify affected validation/self-checks, exports, logical digest/readback, profile bindings and review views before editing. A current inventory or refreshed gallery does not implement missing placement/assembly support or establish native acceptance.

## Publish a fresh review snapshot

Current review views after Aviv's 141 marked exclusions: [remaining bank](../../Staging/BankMarkedRemoval_2026-10-18/Gallery/INDEX.html) and [dependency reserve](../../Staging/BankMarkedRemoval_2026-10-18/Gallery/RESERVE.html). They reuse the existing builder and saved thumbnails, with current native row metadata. Twenty deleted packages are omitted; 121 retained dependencies are excluded from the main view and selection. See the [per-item transaction result](../../Staging/BankMarkedRemoval_2026-10-18/RESULT.txt).

The [original Catalog](../../Staging/BankSimplification_2026-10-07/Catalog/INDEX.html) is a frozen review delivery. Its extractor intentionally pins older row and native-package hashes, while its QA checks that snapshot's counts. These protections and its browser marks remain intact.

1. Input: a verified current native export and package hash, explicit snapshot revision, normalized field types, and exact source packages for imagery. The current readback wraps its rows in a document; it is not the old extractor's list input. HTML eligibility/hold fields require actual booleans.
2. Prepare a reviewed successor extraction recipe using those inputs. Retain the previous catalog, images and receipt. Do not edit old expected hashes merely to make extraction pass.
3. Retain image provenance and distinguish saved asset thumbnails from assembled-model or native-scene views. Check missing bindings and unavailable images explicitly.
4. Existing builders: [build_catalog_html.py](../../Staging/BankSimplification_2026-10-07/Catalog/build_catalog_html.py) accepts `--input` and `--output`; `build_catalog_csv.mjs` consumes `CATALOG_DATA.json` beside it. These build derived views, not bank data. Extraction needs Pillow; CSV generation uses `@oai/artifact-tool`; UI QA uses Playwright. Record the actual runtime/dependency versions in the new packet.
5. Output: matching data, HTML, CSV, images and extraction/UI receipts. Check unique AssetIds, field types, source hashes, image loading, counts, filters and review exports. Version the QA expectations with the new snapshot; never relabel an old PASS as current.

## Return review marks

The HTML stores X marks locally in the browser and exports a marked CSV or AssetId JSON. Download the export before moving the folder. Marks are review choices, not deletion, hold release or automatic native updates.

For an authorized follow-up, compare the export's snapshot and exact AssetIds against the current bank. Report missing IDs or changed bindings, preserve unrelated fields, and prepare the explicit proposed diff and profile implications. The gallery assignment describes this future packet; it does not provide a completed current apply-back command. Use the existing-row publication sequence above only after the owner has supplied the reviewed packet and scope.
