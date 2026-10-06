# Unreal Model Library archive notes

**Scope:** documentation and source-package observations for the old `GIS_WorldBLD` model bank. No files in that project were changed. Nothing was placed in `Environmentpipeline/Content`.

## Documented layout versus actual layout

1. `Unreal_Model_Library_2026-09-24/README_HE.md` says to copy three folders from a `Content` folder **inside the library**. That `Content` folder does not exist in the current archive. The 5,687 recorded native asset files are in the old project's `Content/Astra_ModelBanks_20260924`, `Content/CityBLD_Astra_MinKit_20260924`, and `Content/CityBLD_Terre_RuralKit_20260924` folders. The archive is therefore not one self-contained native Unreal content package. Its old Stage 2 plan proposed the editor's **Migrate** tool for chosen assets; that plan is historical and does not direct the current Houdini bank workflow.
2. The archive's `Exported_FBX` directory is empty. The regular model FBX files are under `Sources/Hergel/FBX` (878) and `Sources/Terre/FBX` (1,185). The ten adapted procedural-kit FBX parts are separately under `CityBLD_Kits/Hergel_NYCAlley/FBX` and `CityBLD_Kits/Terre_Rural/FBX` (five each).
3. The six static-tree source files are `.st`, not FBX. Their images are in `Sources/Terre/SpeedTree/<tree>/`, including nested `Textures/` folders. The old native tree meshes are in `Content/Astra_ModelBanks_20260924/Terre/SpeedTree/`. The Stage 2 source copy preserves `.st` and images as-is; Unreal transfer later uses Migrate.

## Evidence and metadata gaps

- The main `Reports/library_catalog.json` has bank, ID, name, category, status, old Unreal asset path, original Unity source path, and source FBX path. It has **no per-row license or ownership field**, and it does not provide material or texture counts. `FULL_INDEX.csv` adds material-slot counts from each old `UnrealResults/<id>.json` and distinct *existing source texture-file* counts from `Sources/<bank>/Reports/<id>.json`. Those counts do not certify that every source shader map is connected in Unreal. The index leaves the license/provenance-note column empty because the catalog contains none.
- The separate kit provenance report describes the Hergel NYCAlley pieces as user-supplied commercial assets but asserts no new or transferred license. No bank-wide license or ownership proof was found for Terre, Hergel, or the six trees. See `LICENSE_PROVENANCE.md` before any qualification decision.
- Several old reports contain absolute paths to the banks' former locations under `C:\Users\USER\Documents\...`. Those are historical provenance references, not reliable current copy paths. `Candidates/MANIFEST.csv` records each **actual current origin path** used for staging.
- The Terre kit's `Evidence/kit_meshes.json` retains an earlier status of "Unreal acceptance pending," while its later `Result_Report.md` describes an old-project acceptance run. Treat these as chronological records. Neither qualifies the kit in Environmentpipeline.
- The old delivery verification reports historical hash checks for native files. The current preparation checked that the listed native files exist and match recorded sizes; it did not reopen them in Unreal or repeat a full 15.8 GB hash audit. The 349 newly staged source copies, however, were individually checked against their origins by SHA-256 during copying.

## Staging package interpretation

`Candidates/` has one folder per selected kit part or tree. Each kit-part folder contains its original adapted FBX and a copy of its kit's complete local texture set (29 Hergel or 10 Terre images), so it remains portable without guessing which ancillary source map an FBX might need. Each tree folder contains its original `.st` and all raster image files found under that tree's source folder, preserving the tree-relative layout. No file was converted or re-exported.

`Candidates/MANIFEST.csv` has one row per staged file. `origin_path` is absolute; `destination_path` is relative to `Candidates/` so the package can be moved. `size_bytes` and `sha256` describe the copied file; `source_type` is `fbx` for a kit-part folder or `speedtree_st` for a tree folder, including its associated textures. The source and copied hashes were equal at staging time.

## Old-bank reports consulted

- `Unreal_Model_Library_2026-09-24/README_HE.md`, `RESULTS_HE.md`, `STATUS_HE.md`
- `Unreal_Model_Library_2026-09-24/Reports/library_catalog.json`, `delivery_file_manifest.json`, `delivery_verification.json`
- `Unreal_Model_Library_2026-09-24/CityBLD_Kits/<kit>/Result_Report.md` and evidence JSON
- `Unreal_Model_Library_2026-09-24/Reports/Terre/Reports/speedtree_import.json`
