# ME1 report

**Historical source-staging receipt:** The “Active task” section names the completed ME1 staging assignment at the time it ran. It is not a current task. Current bank status is Staging/ModelBank/README.md; no ME1 asset is qualified or generator-connected by this receipt.


## Active task

Stage and file-pre-qualify the requested 34-asset representative Middle Eastern set from Aviv's existing Hergel bank, without modifying the old project or Environmentpipeline project content/configuration/plugins/maps.

## Evidence state

Everything delivered here is **available in bank, staged**. Nothing is qualified, generator-connected, generated, visually verified, or accepted. The files-only table contains provisional judgments and review flags, not Unreal qualification.

Measured staging result: 34 source FBXs and 196 per-asset texture copies (153 unique texture origins), 230 files total, 2,767,374,323 bytes. Every copy was SHA-256 compared with its origin; zero source files or report-linked textures were missing. All 34 indexed old `.uasset` paths also exist, but no `.uasset` was copied.

## Delivered files and paths

- `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\ModelBank\ME\CANDIDATES_ME.csv` — 34 measured asset rows.
- `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\ModelBank\ME\Sources\<id>_<Name>\` — copied FBX and report-linked textures, copy-only.
- `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\ModelBank\ME\MANIFEST_ME.csv` — 230 origin/destination/byte/SHA-256/source-type rows.
- `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\ModelBank\ME\QUALIFICATION_ME.md` — files-only pre-qualification, one row per asset.
- `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\ModelBank\ME\ROLE_MAP_ME.md` — proposed vendor roles and per-asset risks.
- `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\ModelBank\ME\GAPS_ME.md` — regional role gaps and reference-only non-substitutes.
- `C:\Users\USER\Documents\Unreal Projects\Environmentpipeline\Staging\ModelBank\ME\build_me1.ps1` — one-off reproducible staging/measurement script.

## Blocker

Licensing/provenance is unknown for every asset. Pivot is not stated in any selected report; all old Unreal reports record zero simple collisions; rendered appearance, new-project scale, generator compatibility, and save/reopen behavior are unknown because Unreal/editor work was outside ME1 scope. Installed vendor docs do not provide the detailed static-Prefab, PropSpawner, or PCG mesh contracts they reference.

Measured review set: H0014, H0015, H0016, H0896, and H0042 exceed 150k LOD0 triangles; H0896 and H0902-H0907 come from `Need-to-fix`; H0079 is shorter than the supplied streetlight band; H0039 is shorter than the supplied car band; H0077 records an export repair; H0650 has conflicting collision evidence; H0958 records unresolved texture GUIDs.

## Decision needed from the manager

Provide/confirm per-package license evidence, then decide which review assets should be excluded, optimized/decomposed, or scale-corrected before authorizing a later Unreal qualification pass. In particular: whether H0896 should be decomposed rather than treated as one Prefab; whether the five >150k assets advance; and whether H0025/H0060 are discrete PropSpawner items or continuous RoadModules.


