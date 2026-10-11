# New environment playbook

Written 2026-10-11 by Claude Code session 4a6a1d0c at Aviv's request ("save this process so we can re-use it for new environments").

**Source:** the Karmei Yosef 4 km area and the Paz Farm site (2026-10-08 to 2026-10-11).

**Reference run (read when a step is unclear):**
- [KarmeiYosef_SESSION_HANDOFF_2026-10-08.md](../KarmeiYosef_SESSION_HANDOFF_2026-10-08.md) sections 1–17;
- `Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/` (tools, receipts, captures);
- `Staging/PazFarm_2026-10-08/` (site work and Astra briefs).

**Labels:**
- **[D]** a decision point for Aviv: ask with AskUserQuestion buttons and recommend one option;
- **[A]** work for the Astra chat: give Aviv a brief file plus a paste-ready message.

Everything else the operator does alone.

## 0. Rules that bind every step

**The basics:**
- Read root `AGENTS.md`, the user's CLAUDE.md and the memory index first. English in Claude Code; Aviv answers by buttons.
- **No tests, pilots or disposable demonstrations.** Every run is a real, retained run on the real map. A trial only happens on a named COPY, and only when Aviv asks for one.

**Editors:**
- **Generation needs to be the ONLY Unreal editor.** Ask Aviv to close other editors; never close, save or touch someone else's editor.
- Other work (ground, PCG, placement) can run in a parallel editor on its own map. One writer per map.
- **Launch editors only through `launch_area_editor.ps1`, from the PowerShell tool.** Bash's powershell is blocked by the execution policy. The launcher checks the editor count, the lease, the seal and the map sha256; it also writes `ASSIGNMENT_RUN.json` plus `Staging/ParallelEditors/EDITOR_<pid>.json`, and backs the map up into `Before/`.
- **Close editors with `quit_clean.py`** (zero saves). It releases the records.
- **After a crash, mark the three records released by hand:** `ASSIGNMENT_RUN.json`, `ASSIGNMENT_RUN_PID<pid>.json`, `ParallelEditors/EDITOR_<pid>.json`. Use status `RELEASED_AFTER_CRASH`, write a `receipts/CRASH_PID<pid>.json`, and only then relaunch.

**Saving:**
- **Save only named packages.** Never Save All and never `save_assets([])`.
- Save after every stage (one crash once lost an unsaved stage).
- Content goes in with `save_prefix.py` or the step's own save, the map with a map-only save step.
- **Freshly placed or swapped meshes mark their material instances dirty.** Run `save_prefix.py` on that folder before the map save, or the save refuses.

**The editor-crash family** (Python access violation in a GC or save path, 4 times so far):
- After ANY material-graph edit, quit the editor before any other step or save.
- Never delete material expressions; add new nodes, or rebuild under a new `_vN` name.
- Before every step on a map with PCG, wait for PCG to be idle (`status` in_progress false). A landscape-material change regenerates PCG.
- After saves, run `gc_probe.py`, so corruption surfaces at once.

**During a generation run:** never read the live `WORKFLOW_STATE.json` or `BUILD_STATE.json`. Poll the lease tail (`wait_lease.py`), or mtime and size only.

**What must stay unchanged:**
- vendor originals (make area-owned copies);
- shared masters (make area-owned copies);
- other areas' packages;
- earlier HDA revisions (new revision files only).

**Aviv's standing look rules:**
- Trees and plants never disappear; they only drop to a lower LOD. Far vegetation shows its lowest LOD.
- No placeholder trees from Houdini; vegetation comes from Unreal PCG.
- Real retained results on the original map.

**World Partition and HLODs** (Aviv 2026-10-11): a 4 km area stays one fully loaded level without World Partition. Nanite draws at every distance, there are no HLODs, and nothing streams or culls.
- **[D] Ask Aviv** before switching an area to World Partition with HLODs; it is meant for bigger areas or a game build.
- Recipe and measured costs: `Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/WPTrial/TRIAL_RESULT.md` (always-loaded tree HLODs at their lowest LOD, a building HLOD grid; about +8 ms GPU in the whole-area view).

**Deletions:** only after Aviv has verified and confirmed. Keep a running delete-on-confirmation list in the handoff.

**Git and Linear:** none. Commit and push are Aviv's step; trial files never go into git.

## 1. Set up the task

1. **[D] Point and size.** Ask Aviv for the exact point (latitude and longitude, 6 decimals) and the size (2 km = 2017 samples at 1 m; 4 km = 4033 samples at 1 m). Also confirm the choices that were defaults last time (each is one button):
   - Houdini roads (RoadBLD off);
   - farm tracks kept as roads;
   - Houdini props kept;
   - no Houdini trees;
   - never stop the bake for unbuildable buildings (tolerance 100%);
   - failed generated poles dropped.
2. **Task folder:** `Staging/NewArea_<Name>_<lat8digits>_<lon8digits>_<size>_<YYYY-MM-DD>/`. Area id = `<Name>_<lat8>_<lon8>_<size>`.
   - Map: `/Game/Project/Areas/<AreaId>/BankIntegration_v015/L_<AreaId>`.
   - PCG clone: `/Game/Project/Areas/<AreaId>_PCGTrial/L_<AreaId>_PCGTrial` (rebuilt clone: suffix `_v2`).
3. **Copy the tools:** copy `Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/Tools/` into the new folder. Most tools name the area only in their top constants, so change those (see section 11):
   - `TASK`, `MAIN`, `MAP`, `CLONE`, `TRIAL`, `AREA`;
   - the area id;
   - the landscape half-extent (4 km: ±201,600 cm; 2 km: ±100,800 cm);
   - in `launch_area_editor.ps1`, the `$AreaPrefix` lines;
   - **the editor ports.** The reference set uses 19852 (Copilot), 18092 (plugin) and 8012 (native MCP), hard-coded in `launch_area_editor.ps1` (`$CopilotPort`, `$PluginPort`, `$NativePort`), `ky_client.py` (`PORT`) and `ky_capture.py` (`PORT`). Choose three ports that no other task folder uses and set them in all three files. Otherwise a new area's editor collides with any open editor of another task, and parallel editors are impossible.
4. **Records to keep:** `ASSIGNMENT.json` (scope, authority words), a session handoff file `Staging/<Name>_SESSION_HANDOFF_<date>.md` kept current after every stage, and a memory line.

## 2. Source package (offline)

- **Script:** `acquire_area.py` (wrapper around the shared `acquire.py`; for 4 km it only widens the size limit and the DSM margin).
- **Sources:**
  - OSM from Overpass (`overpass-api.de`; retry rounds on 504);
  - DEM: Copernicus GLO-30 tile from the shared cache.
- **Output:** a geographic package under `C:/Users/USER/Documents/Pipeline Environment/SourceData/<AreaId>/`, plus `REQUEST.json`, `AREA_DECISION.json`, `ACQUISITION_RECEIPT.json` and `AREA_SOURCE_FAMILY_REGISTRY.json` in the task folder.
- **Gotchas:**
  - The mirror `overpass.maprva.org` returned the wrong region (Swedish data): reject it.
  - Check that the package bounds equal the requested box.

## 3. Owned generator (offline, hython)

- **Start from the closest HDA that completed a full non-Gaza cook.** Last time: Lebanon 4 km v006 for 4 km, its 2 km variant for 2 km. Use `build_hda_4km.py` / `build_hda_4km_v002.py` as templates. They:
  - load the source `.hdalc` (sha-checked);
  - patch the PythonModule text with exact, unique anchors;
  - `copyToHDAFile` under a NEW operator type name and save to `Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank/revisions/<date>_<Name>_<size>/`;
  - re-read the saved file and write `HDA_SOURCE*.json`.
- **No cook during authoring.** Verify separately (`verify_hda_4km_v002.py`).
- **Changes to make from the start** (each was a later fix last time):
  1. No placeholder tree blockouts in `cook_vegetation` (vegetation comes from PCG).
  2. Failed generated decorations (poles) omitted: add the area id to the final proxy policy tuple, in both places.
  3. **Road classes:** `ROAD_WIDTH_M` and `ROAD_CLASSES` must include `trunk` (12 m), `trunk_link` (7), `primary` (10) and `primary_link` (7). v001 silently dropped road 44, which was a `trunk`. Add `NO_SIDEWALK_CLASSES` for them, in the LAST (active) `cook_sidewalks` definition.
- **Building assembly contract:** the `building_assembly_contract_json` default comes from `PROFILE_CANDIDATE.json`.

## 4. Profile and native area (editor: create)

1. `prepare_profile.py`: profile candidate from the last profile that completed a full non-Gaza cook (AnyArea bank table). Task staging only.
2. **Launch:** `launch_area_editor.ps1 -Purpose create -AvivWord "<his words>"` (only editor). Then run `create_area.py`:
   - import the owned HDA to `<root>/HDA/...`;
   - duplicate a working area ground MI to `<root>/Materials/MI_GeoCityGround_Auto`;
   - create a new level with the reusable sky at this latitude and longitude;
   - make named saves of these three only.
3. `promote_profile.py`: writes `Staging/ModelBank/<AreaId>/AREA_PROFILE.json` once.
   - The bank chat's `sync_connection_profiles.py` does NOT update new profiles. A bank-table change needs this profile's digest updated too.
4. **Snow fix:** set `MW_SnowWorldPosition` to 1e6 on the area MI only. The Lebanon MI's -1500 turns the whole terrain white.

## 5. Generation (editor: run; ONLY editor)

1. **Launch:** `launch_area_editor.ps1 -Purpose run -Map <map> -ExpectedMapSha256 <sha>`. Then run `start_area_generation.py`, which goes through the sealed menu action.
   - **Timing:** 2 km took about 11 minutes; 4 km took about 1.8 hours.
   - **Timeout:** 14,400 s for 4 km.
2. **Wait** with `wait_lease.py --pid <pid>` (lease tail only).
   - Exit 0 = `baked_saved_verified`.
   - On a failure: `exit_failed_area_run.py` (no saves). The manager, or the operator with Aviv's approval, appends the OWNER=NONE release line.
3. **Read back:** `readback_area.py` (counts, sha, captures). Then `quit_clean.py` with `allow_cook_leftovers: true` (the run leaves unreferenced cook packages). Then reopen fresh with `-Purpose verify`.
4. **Regenerating with a NEW HDA revision** (lessons from the v002 failure and recovery):
   - **Regenerate vs instantiate:** regenerate mode reuses the existing HoudiniAssetActor and never reads `profile['hda']`, so a new revision needs instantiate mode:
     - import the new HoudiniAsset;
     - delete the old actor;
     - save the map;
     - switch `profile['hda']` before the run (`hda_v002_prepare.py` and `switch_profile_v002.py`).
   - **Back up** the main map, the three bake packages, the profile and the ledger to `Before/regen_<utc>/` first. Bake package names are fixed and shared with every clone.
   - **Duplicate Landscapes after bake:** instantiate over an existing bake renamed the old landscape `_old_0`, and the run failed with "Duplicate Landscapes after bake". Recovery:
     - remove only `_old_0` and save (`recover_v002.py`);
     - `exit_failed_area_run.py`;
     - append the lease release line;
     - rerun in **regenerate** mode (the new actor is kept), which succeeded.
6. **One object per building (standard step after every generation, Aviv 2026-10-11).** The generator bakes buildings merged: one area-wide instance group per module mesh, plus one merged shell mesh. Split them on the working map:
   1. Offline: rebuild the per-building data from the CURRENT run's `HDA_CATALOG_RECEIPT.json` (`Buildings_v2/compact_buildings_v2.py` → `BUILDINGS_COMPACT.json` and `FOOTPRINTS.json`).
   2. `split_buildings.py --target <map>`, steps:
      - `plan`: every instance is matched to its building within 2 cm; the step refuses if anything is unmatched.
      - `build`: slices of 150.
      - `fix_attach`: Static chains; every position is checked.
      - `remove`: takes the moved instances out of the area-wide groups.
      - `verify`.
      - Then save.
   3. `split_shells.py`, steps:
      - `analyze`: assigns each triangle to a footprint.
      - `build`: slices of 100. Each slice creates one mesh per building under `<map folder>/Buildings_v2/Shells/`. Run `save_prefix` and the map save after EACH slice.
      - `remove`: deletes the merged shell actor. It is found by its mesh, because labels get `_1` after a regeneration.
      - `verify`, then `fix_attach` again, then save.
   4. Expect:
      - the `Bldg_<osm>` count = buildings + 1 for the unsupported shell;
      - shell triangles 2 short of the source (two zero-area triangles are dropped, same as the trial).
   5. After reopening, the editor builds a distance field for each new shell mesh (about 2 s each, cached afterwards). Measure play mode only after these finish.
   6. **[D] Ask Aviv** whether the generator should bake one object per building itself, instead of this post-bake split. The bake workflow (`geocity_bank_workflow.py`) is sealed and manager-owned, so that change goes through the manager as a brief.
7. **Clones share the bake.** A clone references the main map's bake packages, so a regeneration changes every clone's roads and buildings. To get a clean clone after a regeneration, rebuild it (section 7.5).

## 6. Ground: satellite colour and zones (offline, then editor)

1. **Zone data** in `Zones/` (gis env Python, GDAL 3.13 plus numpy). Scripts write rasters to `SourceData/<AreaId>/zones/<stamp>/`:
   - `zones_data.py`: OSM land use from Overpass, and Sentinel-2 L2A from Earth Search STAC (no login). Use the latest clear scene and a clear spring scene.
   - `classify_zones.py`: 4 m grid; OSM polygons first, then NDVI rules.
   - `make_masks.py`: one 1024² mask per zone.
   - `make_textures.py`: `T_<X>_Satellite` 2048² sRGB and `T_<X>_Zones` grey.
2. **Ground material:** `build_ground_satellite.py`.
   - Import both textures.
   - Duplicate the shared ground master into an area-owned `M_GeoCityAuto_<X>`.
   - Add a satellite blend before `MakeMaterialAttributes.BaseColor`, with uv = (WorldPos.xy - min) / size and detail kept through a luminance ratio.
   - Reparent the area MI.
3. **gis env gotchas:**
   - numpy BLAS/LAPACK crash (no `lstsq`, `corrcoef`, `matmul`): use closed-form math.
   - Keep GDAL temporary datasets referenced until after `ReadAsArray`.
   - `-I` needs `GDAL_DATA` and `OSM_CONFIG_FILE` set in code.

## 7. Vegetation on a PCG clone (editor: pcg)

1. **Clone:**
   - first time: `prep_zone_clone.py` (duplicate the saved main map into `<AreaId>_PCGTrial/`, import the masks);
   - after a regeneration: `clone_v2.py` (export actors from the old clone → `duplicate` the new main map → `import` in a fresh editor → `save`).
   - Never hold a Python reference to a duplicated world; quit and relaunch on it.
2. **PCG graph** (`build_zone_pcg.py`, later `ky4_trees_v2.py graph|volume|assign_graph`):
   - Landscape Surface Sampler → Sample Texture (planar; Texture Sampler transform scale = half-extent, half-extent, 1) → Density Filter ≥ 0.5 → keep `Dirt_Path` < 0.05, `Sand_Path` < 0.05, `Sand_02` < 0.5 → Self Pruning → Transform Points (absolute yaw) → Static Mesh Spawner (WPO off).
   - Selector via `import_text`; Rotator always with keywords; run `pcg.FlushCache` after setting changes.
3. **More trees** (`Zones/trees_v2.py`):
   - Sentinel-2 greenness tree map;
   - forest and scrub at 2–3× density;
   - single field trees;
   - windbreak rows along dirt roads near the site.
4. **Never-disappear vegetation:**
   - `never_vanish.py`: area-owned mesh copies with Nanite on plus Preserve Area; leaf textures with alpha-coverage mips; clip about 0.12–0.15.
   - `lowest_lod.py`: real-geometry auto LOD chains on the copies.
   - `audit_visibility.py`: no cull distances anywhere.
   - Thin store needle cards fade beyond about 600 m whatever you do. **[A]** Astra-made foliage (solid leaf clusters, opaque inner hull, authored lowest LOD) fixed this; see `HANDOFF_ASTRA_VisualFix_v003.md`.
5. **Rebuild order for a clone** (each step a separate script call; save after each):
   1. `farm_real_ground.py path_through` (graph edit) → quit.
   2. Fresh editor: `assign` the landscape MI → `clone_v2 save`.
   3. Import carried actors → save.
   4. Astra imports (`apply_astra_rev.py` textures/materials/meshes) → `save_prefix`.
   5. PCG `volume` → wait idle → `pcg_finish save`.
   6. `fields_place place` → windbreaks → `make_static` → `save_prefix` → `pcg_finish save`.

## 8. Farmland and hero site (when the area has one)

1. **[D] Reference image.** Ask Aviv for a wide screenshot (Google satellite plus roads) around the site.
   - Georeference it with `Fields_2026-10-10/georef_wide.py`: a similarity fit against OSM roads, aiming at ≥ 90% of road pixels within 10 m.
   - Plot borders come from roads and field edges, **never from the screenshot frame**. Aviv corrected this once.
   - Do not guess missing roads; Aviv called the guesses "way off". Extract them from his screenshot or leave them out.
2. **Fields** (`Fields_2026-10-10/`):
   - `roads_overlay.py` (road masks);
   - `fields_cluster.py` (k-means);
   - `fields_v1.py` (field polygons with a type each: majority filter, sieve);
   - `fields_build_v2.py` (`FIELD_PLANTS_V2.json`: crops, margins, grass, olives, vines, orchards, greenhouses on row lattices along each field's direction; plus the ground mask v4);
   - `Tools/fields_place.py place` (Static-chain HISM actors, landscape-only heights).
3. **Ground under fields** (`farm_real_ground.py`):
   - real tiling ground materials blended by a weight mask through `BlendMaterialAttributes(orig, farm, mask.A × FarmR_Blend)`;
   - tints and satellite mix are MI parameters (no recompile);
   - `path_through` lets the generator's `Dirt_Path` track paint show through. Generator tracks are landscape paint only, without a mesh.
4. **Hero site (Paz Farm pattern):**
   - `PLAN.md` from public facts plus the screenshot;
   - `Georef/` trace (FIT, LAYOUT plots, rows);
   - **[A]** a model brief;
   - `import_astra.py` / `apply_astra_rev.py`;
   - `place_farm.py`.
5. **Anything tiled or chained must be GROUND-FITTED, never flat yaw-only.** Pitch to the terrain between the tile's two ends, roll to the cross slope, and sink about 3 cm. Examples: `fence_v003.py` (panels) and `straw_beds.py` (4 m bed tiles).
   - Real-world spacing comes from field practice, not from a screenshot stripe period. Strawberry beds are about 1.7 m apart, centre to centre.
   - **Joins:** for exact joins, stretch each pitched tile along its length by its 3D length over 4 m (under 0.5%).
   - **Variants:** mix the variants so no row repeats one twice in a row.
   - **End caps:** close every continuous run with end caps: at the start of a run turned 180° about the tile's up axis, at the end on the last tile's transformed far point (`straw_beds.py place_variants`).
6. **Static chains everywhere:** make the whole chain Static top-down (root first), then re-attach. A Static part under a Movable parent loses its attachment on save. HLOD only takes Static components.

## 9. Astra asset loop [A]

- **Brief file:** `Staging/<Site>/HANDOFF_ASTRA_<Name>_v00N.md`. Examples: `VisualFix_v003` (pines, far beds), `FieldCrops_v004` (vines, olives, grass), `StrawberryBeds_v005` (realism from references). A brief always states:
  - Why, with capture evidence;
  - the scene season (for example late September);
  - **real photo references collected by Astra**, kept in `References/` with their links;
  - exact names, sizes, pivots and tile convention (metres, FBX with -Y forward and Z up; Unreal then runs the tile along -Y);
  - solid geometry or solid alpha;
  - triangle budgets;
  - an authored lowest LOD (`*_LOD3.fbx`, same slot names). From about 60 m on, everything is drawn only with its lowest LOD;
  - the previews at set distances;
  - the checks (round-trip, dimensions, pivots, budgets, UV0, seams, originals-unchanged hashes);
  - a paste-ready message at the end.
- **Import:** `apply_astra_rev.py --revision <folder>`, steps `textures` → `materials` (reuse the existing opaque and two-sided masters) → `meshes` (Nanite on, the lowest LOD imported as LOD1, slots bound by name). Then `save_prefix`.
  - Slots are bound AFTER the LOD import, because a slot used only by the lowest LOD is created by that import (v005 `MulchDistant`).
  - Pass `import_normals: true` when Astra asks to keep the authored normals.
  - Judge vertex counts from the import log's `MeshPayload` line; `get_number_verts` shows Nanite's reduced fallback.
- **Swap or place:** keep every earlier revision. Swaps are mesh-only when the tile convention is kept.

## 10. Verify, record, report

1. **Captures:** `ky_capture.py --label <L> --cameras cameras_<x>.json`. Use `ground_z.py` to get camera heights. After a fresh start, take two passes: the first often shows materials still loading.
2. **Play mode:** `pie_run.py <label> cameras_pie.json` (mean frame time per view). Last result:

| View | Frame time |
|---|---|
| Farm | 18.8 ms |
| Village | 13.6 ms |
| Forest | 8.7 ms |
| Wide | 35.8 ms |

3. **Fresh reopen:** `quit_clean.py`, relaunch with the saved sha, then a read-only verify script (`verify_clone_v2.py` pattern: exact instance counts, Static, nothing detached, PCG count, landscape material, nothing dirty).
4. **Records:**
   - a RESULT doc (measured numbers, shas, open points);
   - the handoff section;
   - the memory line;
   - a short report to Aviv: what changed, what to look at, open choices as one-line options, and pending deletions.
   - Leave the verified editor open for Aviv only when he wants to explore. Tell him it has nothing unsaved.

## 11. Tool inventory (reference folder `Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/Tools/`)

**Generic (change only the path constants):**

| Purpose | Tools |
|---|---|
| Launch and client | `launch_area_editor.ps1`, `ky_client.py`, `ky_capture.py` |
| Close and recover | `quit_clean.py`, `exit_failed_area_run.py`, `recover_v002.py` |
| Generation | `start_area_generation.py`, `wait_lease.py`, `readback_area.py`, `create_area.py`, `hda_v002_prepare.py` |
| Clone and saves | `clone_v2.py`, `pcg_finish.py`, `save_prefix.py`, `gc_probe.py` |
| PCG and vegetation | `ky4_trees_v2.py`, `never_vanish.py`, `lowest_lod.py`, `audit_visibility.py` |
| Ground | `build_ground_satellite.py`, `farm_real_ground.py` (the farm branch is reusable for any field blend) |
| Assets | `apply_astra_rev.py` |
| Play mode | `pie_test.py`, `pie_run.py` |
| Read-only probes | `world_probe.py`, `mob_probe.py`, `dz_probe.py`, `ground_z.py`, `verify_clone_v2.py` |
| World Partition trial (only if Aviv wants WP) | `split_buildings.py`, `split_shells.py`, `wp_setup.py`, `wp_verify.py` |

**Site-specific recipes (adapt, don't run as-is):** `place_farm.py`, `fence_v003.py`, `straw_beds.py`, `fields_place.py`, `apply_v002.py`, `apply_v003.py`, and the scripts in `PazFarm_2026-10-08/Georef/` and `Fields_2026-10-10/`.

**Offline:**
- area folder: `acquire_area.py`, `build_hda_*.py`, `verify_hda_*.py`, `prepare_profile.py`, `promote_profile.py`, `switch_profile_v002.py`;
- `Zones/` (zones_data, classify_zones, make_masks, make_textures, trees_v2).

**Unreal Python gotchas:**
- `Rotator(roll=, pitch=, yaw=)` always with keywords.
- `line_trace_*`: `to_tuple()[0]` = hit flag, `[4]` = location, `[9]` = actor. Use a multi trace and keep only Landscape hits.
- Git Bash mangles `/Game/...` arguments: set `MSYS_NO_PATHCONV=1`.
- `str(LinearColor)` includes an address.
- Reading MI static switches marks the MI dirty.
- Windows reuses PIDs: move a stale same-PID ParallelEditors record to `Stale/`.
- Nanite merges thin wire meshes (fences) into a pale sheet: turn Nanite off on those copies.
