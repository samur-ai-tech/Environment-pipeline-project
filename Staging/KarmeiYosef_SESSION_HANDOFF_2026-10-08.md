# Karmei Yosef / Paz Farm — session handoff (Claude Code session 4a6a1d0c)

Written 2026-10-08 ~16:20Z at Aviv's request before compaction. Read this first after compaction. English only.
Operator role: Aviv directly authorized this chat ("this chat, all steps"); the project manager remains session 913c2312.
Aviv's style: short answers, decisions via AskUserQuestion buttons, English in Claude Code, paste-ready English messages
for other chats (Astra = GPT-6 Astra chat used for Blender modelling and visual review).

## 1. Areas built (all saved, fresh-reopen verified)
| What | Map | Saved sha (16) | Folder / records |
|---|---|---|---|
| 2x2 km area | `/Game/Project/Areas/KarmeiYosef_31850349_34907601_2km/BankIntegration_v015/L_KarmeiYosef_31850349_34907601_2km` | 597eab0826f4fd4b | `Staging/NewArea_KarmeiYosef_31850349_34907601_2km_2026-10-08/` (RESULT.md, ASSIGNMENT.json) |
| 2 km PCG trial clone | `/Game/Project/Areas/KarmeiYosef_31850349_34907601_2km_PCGTrial/L_..._2km_PCGTrial` | 00e765dc9b4c4153 | same folder, ASSIGNMENT.json pcg_trial |
| 4x4 km area | `/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/BankIntegration_v015/L_KarmeiYosef_31850349_34907601_4km` | c7c858c50ca986d8 | `Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/` (ASSIGNMENT.json) |
| 4 km zone + Paz Farm clone | `/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/L_KarmeiYosef_31850349_34907601_4km_PCGTrial` | 2719be1c92a8a444 | 4 km folder + `Staging/PazFarm_2026-10-08/RESULT_PLACEMENT.md` |
- Centre 31.850349 N 34.907601 E (= Aviv's original point = Paz Farm, pin 31.851309 N 34.906260 E, ~127 m W / 106 m N).
- Unreal frame: X = east, Y = south (cm); landscape centred at 0,0; 4 km landscape ±201,600 cm, 2 km ±100,800 cm.
- Profiles: `Staging/ModelBank/KarmeiYosef_31850349_34907601_{2km,4km}/AREA_PROFILE.json` (AnyArea bank table, digest 12552e14;
  the bank chat's sync script does NOT update these two profiles).
- Owned generators: `Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank/revisions/20261008_KarmeiYosef_2km/…_2km_v002.hdalc`
  (type 15.0_2km_currentbank) and `…/20261008_KarmeiYosef_4km/GeoCity_city_v015_CurrentBank_4km_KY_v001.hdalc`
  (type 15.0_4km_karmeiyosef). Both = Lebanon v006 + no placeholder trees + failed generated poles omitted.
- Aviv's choices: Houdini roads (RoadBLD off), farm tracks kept as roads, Houdini props kept, no Houdini trees, never stop
  the bake for unbuildable buildings (tolerance 100%), drop failed poles.

## 2. Ground and zones (4 km)
- Area MI `…/4km/BankIntegration_v015/Materials/MI_GeoCityGround_Auto` -> parent `M_GeoCityAuto_KY4` (area-owned copy of the
  shared master; shared master untouched). Graph additions before MakeMaterialAttributes.BaseColor:
  1) satellite blend (`SatelliteColor` = T_KY4_Satellite, Sentinel-2 21 Sep 2026; Sat_Blend 0.8, Sat_DetailMid 0.35, Sat_SizeCm 403200);
  2) Paz Farm layer (`FarmColor` = T_PazFarm_Ground; Farm_OriginX -34676.4, Farm_OriginY -33691.2, Farm_SizeCm 51200,
     **Farm_Blend default 0** = off on the main map). Clone uses `…4km_PCGTrial/PazFarm/Materials/MI_GeoCityGround_PazFarm` (Farm_Blend 1).
- Snow fix: MW_SnowWorldPosition set to 1e6 on the 2 km area MI (Lebanon's MI still -1500 = white).
- Zone data: `Staging/NewArea_…_4km_2026-10-08/Zones/` (DATA_RECEIPT.json, LEGEND.json, ZONES_preview.png, MASKS.json,
  TEXTURES.json); rasters in `Pipeline Environment/SourceData/KarmeiYosef_31850349_34907601_4km/zones/20261008T131311Z/`.
- Zone PCG on the 4 km clone: graph `<clone>/PCG/PCG_KY4_Zones` (8 branches), masks `<clone>/Masks/T_KY4_Mask_*` (currently the
  farm-cleared versions; originals in the zones folder above). 112,891 stand-in plants. Method that works: landscape Surface
  Sampler -> Sample Texture (planar; Texture Sampler transform scale 201600,201600,1) -> Density Filter >= 0.5 -> layer filters.

## 3. Paz Farm (on the 4 km clone)
- Folder `Staging/PazFarm_2026-10-08/`: PLAN.md, HANDOFF_ASTRA_BLENDER.md, RESULT_PLACEMENT.md, References/ (Aviv screenshot),
  Georef/ (FIT.json scale 0.353 m/px rot -3.35°, LAYOUT.json 12 traced plots, PLACEMENTS.json, FARM_GROUND.json, scripts),
  Review/ (captures pazfarm_b_*.png), AstraModels/ (Astra delivery v1 + Revisions/).
- Aviv's facts: crops avocado, lemons, clementines, oranges, strawberries; triangle = barn at top + OPEN strawberry rows (no
  nets); wire mesh fence + entrance gate; grey-purple rows unknown (placed as young citrus, a guess).
- Unreal: `<clone>/PazFarm/{Textures,Materials,Meshes}` (117 textures, masters M_PazFarm_Master_{Opaque,Masked,Translucent},
  38 MIs, 26 Nanite meshes). Actors: `PazFarm_Detail` (HISM per mesh: 763 strawberry beds, 247 avocado, 945 citrus,
  225 fence panels, 9 posts), `PazFarm_Barn` (scaled to 25.8 x 20.5 m), `PazFarm_Gate`. Undo: delete the 3 PazFarm actors;
  Farm_Blend 0; re-import original masks.
- Pending: Astra visual-fix revision v002 (to review + apply), strawberry plant fix (requested from Astra), barn roof
  colour (dark in screenshot), young citrus look thin, ground colours a bit pink/pale.

## 4. Tools (4 km: `Staging/NewArea_…_4km_2026-10-08/Tools/`; 2 km has the same set)
- `launch_area_editor.ps1 -Purpose create|run|verify|pcg [-Map … -ExpectedMapSha256 …] -AvivWord "…"` (ports 19852/18092/8012;
  gates: zero editors, lease OWNER=NONE, seal check; writes ASSIGNMENT_RUN.json + ParallelEditors record).
- `ky_client.py <script> --args '{…}'` (run_unreal_skill on 19852; ARGS/RESULT globals; never raise SystemExit in scripts).
- `ky_capture.py --label L --cameras file.json` (native MCP 8012 CaptureViewport; take two passes after a fresh start —
  first pass often shows materials still loading). `ky_client_aviv.py`/`ky_capture_aviv.py` = Aviv's own editor (19840/8000).
- `quit_clean.py` (zero saves; `allow_cook_leftovers` after a GeoCity run), `start_area_generation.py`, `wait_lease.py`,
  `readback_area.py`, `pcg_finish.py` (status / save clone), `pcg_check_upright.py`, `pcg_gen.py`, `save_farm_assets.py`,
  `place_farm.py` (ground_mi | place | masks), `import_astra.py` (textures | master+label | instances | meshes),
  `farm_material.py`, `build_ground_satellite.py`, `build_zone_pcg.py`, `farm_readback.py`.
- Camera files: `cameras_ky4*.json`, `cameras_pazfarm.json` (4 km folder).

## 5. Gotchas learned (do not repeat)
- Unreal Python `Rotator(a,b,c)` = roll, pitch, yaw -> always keywords. PCG selector: use `import_text`, not set_attribute_name.
  After PCG settings changes: `pcg.FlushCache` before regenerating. Turn off foliage WPO (wind wobble) on PCG/ISM descriptors.
- Never keep a Python reference to a duplicated world when loading a map (World Memory Leaks crash); duplicate, save, restart on it.
- `MaterialFactoryNew` via create_asset crashed Aviv's editor 19732 -> build masters by duplicating
  `/Game/StarterContent/Materials/M_Basic_Wall` + `delete_all_material_expressions`. MIC factory works.
- `Package.set_dirty_flag` does not exist; MaterialEditingLibrary setters may return falsy while working; reading MI static
  switches marks the MI dirty; `str(LinearColor)` contains an address (compare numbers).
- numpy `linalg.lstsq` crashes in the GIS env (missing LAPACK) -> closed-form math. GIS python with `-I` needs GDAL_DATA /
  OSM_CONFIG_FILE set in code. Overpass often 504 -> retry rounds; overpass.maprva.org returns wrong-region data (excluded).
- `line_trace_single` returns a HitResult: `to_tuple()[0]` = hit flag, `[4]` = location.
- Windows can reuse PIDs: move a released same-PID ParallelEditors record to `Stale/` before writing a new one.
- Generation requires being the only Unreal editor; ask Aviv to close other chats' editors (never close them ourselves).

## 6. Next steps
1. Review Astra `AstraModels/Revisions/VisualFix_v002/` (HANDOFF_CLAUDE.md, DONE.md, INDEX.html) and apply in Unreal on the
   4 km clone (re-import changed meshes/textures, corrected ground texture, gate alignment), save, fresh reopen, captures.
2. Then Astra visual review again if Aviv wants; strawberry fix when Astra delivers.

## 7. Astra VisualFix_v002 (received 2026-10-09, reviewed, NOT yet applied)
Folder `Staging/PazFarm_2026-10-08/AstraModels/Revisions/VisualFix_v002/` — read `HANDOFF_CLAUDE.md` (ranked steps), `MANIFEST.json`.
- Real defect Astra found that I missed: tree crowns vanish in the overhead view (my `pazfarm_b_farm_overhead.png` shows
  orchard ground only). Likely Nanite + alpha-masked leaf cards at distance. Fix: 7 tree FBX with geometric leaf outlines and
  solid alpha; also check Nanite "Preserve Area" on these meshes.
- Apply order: (1) re-import 7 trees + leaf maps (keep names, slots, pivots); (2) replace ground overlay with
  `Georef/T_PazFarm_Ground.png` (same mapping: west -219.843 m, north +230.463 m from pin, 512 m, 2048², sRGB, clamp; same
  Farm_Blend route) — note the farm texture lives in the 4 km AREA folder (`…/4km/BankIntegration_v015/Materials/Zones/T_PazFarm_Ground`),
  used only by the clone (main map Farm_Blend 0); (3) re-import `SM_PazFarm_StrawberryBed_4m` (keep 763 instances);
  (4) re-import `SM_PazFarm_Barn`, bind NEW slot 4 `M_PazFarm_Barn_RoofCharcoal_v002` (BaseColor sRGB median 70,62,68, rough 0.94),
  keep slot 1 RoofPaintedGrey; keep the barn actor transform; (5) gate only: `Georef/PLACEMENT_PATCH.json` e 24.266047,
  n 52.46, dir 90.075493° (centre pivot) -> move `PazFarm_Gate`.
- Re-import needs `replace_existing=True` into `<clone>/PazFarm/Meshes/` and new MI(s) for new material names (via MIC factory,
  parent = existing masters). Then save named packages, save clone, fresh reopen, same 5 cameras (`cameras_pazfarm.json`).

## 8. v002 apply progress (2026-10-09 ~07:00Z, after compaction)
- Method (reversible, approved by advisor): v002 imported NEXT TO v1 under `<clone>/PazFarm/v002/{Textures,Materials,Meshes}`
  by `Tools/apply_v002.py` (steps probe|textures|materials|meshes|swap|revert|save); v1 packages untouched.
  Saved: 25 textures (24 changed/new + `T_PazFarm_Ground` v002 in the CLONE folder), 11 MIs, 9 meshes (plants Nanite
  shape_preservation PRESERVE_AREA; bounds within 2 cm of v1; strawberry 42.4 cm tall vs 44.2). Receipt `receipts/PAZFARM_V002_MESHES.json`.
- Swap applied IN MEMORY in my editor PID 15704 (ports 19852/18092/8012; launcher got `-AllowLiveEditorPid 18008`):
  8 HISM meshes -> v002 (counts unchanged), barn -> v002 (slot 4 charcoal), clone ground MI FarmColor -> v002 texture,
  gate moved 0.693 m to Astra's centre (24.266, 52.46, 90.075°). Before-state: `receipts/PAZFARM_V002_BEFORE.json`
  (`apply_v002.py step revert` restores it). Overhead capture `v002swap_b_farm_overhead.png`: crowns now VISIBLE (v1 baseline
  `v002pre_b_*` shows none).
- BLOCKED SAVE: Aviv's own editor PID 18008 (ports 19840/8000) opened the clone map at 2026-10-08 17:35Z and holds its
  files (Windows error 32 on MI_GeoCityGround_PazFarm). It made no saves. Asked Aviv to switch his editor off the clone
  (Don't Save) or close it; then rerun `apply_v002.py step save`, `quit_clean.py`, fresh `-Purpose verify`/pcg reopen, 5 cameras.
- DONE 2026-10-09 06:58Z: Aviv closed his editor 18008; `apply_v002.py step save` saved MI_GeoCityGround_PazFarm + clone
  map -> **clone sha 26c39d47aa346868dcfafcfd88245bdc6375b71788b9707882a2ee512cef01d3** (186 MB). Fresh reopen PID 41808
  verified (all v002 bindings, gate 24.266/52.46, dirty none); captures `receipts/Captures/v002fresh_b_*.png` (5 cameras) +
  `fence_a_*.png`. Both editors released clean (quit_clean, zero saves). Crowns visible from 460 m; strawberries full;
  barn roof matte mid-grey (not yet charcoal in close view — tuning item); v002 ground reads pale/flat at distance.
- Visibility audit `receipts/VISIBILITY_AUDIT.json` (Tools/audit_visibility.py, read-only): 161,754 instances, 0 components
  with cull/max-draw distance, no CullDistanceVolume, map NOT World Partition (no __ExternalActors__). Risk: 4 vendor Nanite
  pines `/Game/Modular_Rural_Cabin/Meshes/Foliage/SM_Pine_Tree_0{1,2,3,5}` (PCG stand-ins) have shape_preservation NONE
  (same crown-loss risk); do not edit vendor originals -> area-owned copies. Non-Nanite stand-ins (STF, Palms_Pack plants,
  ProceduralNtr) have LODs only.
- 4 km main map storage: 74 actors = 68 plain Actors (one per bank mesh, ISM over the whole 4 km, 46,667 instances) +
  3 StaticMeshActors (merged buildings / road_surfaces / sidewalks) + landscape + sky + HDA actor -> no building is its own object.
- Fence defects seen: panels flat at one Z per 3 m panel -> stair-steps + gaps under bottom rail on slopes, rails misaligned
  at joins, wire mesh reads as a pale wall from mid distance.

## 9. Aviv's new requests (2026-10-09 ~07:00Z) — awaiting his answers
1. Fix the fences. 2. Extend every Paz-Farm-affected patch to its full parcel, dirt road to dirt road (today clipped to
   his screenshot extent). 3. Consider World Partition + HLODs. 4. Consider each building as its own object (does it
   complicate the generator?). 5. Trees/plants must NEVER disappear (leaves or trunks) — only lower LODs.
Notes: WP makes unloaded-cell actors vanish unless in HLOD (trees need an instanced HLOD layer); the sealed GeoCity
generator scans get_all_level_actors (WP sees only loaded actors) and its bake path is manager-owned -> generator changes go
to the manager; a WP/per-building trial belongs on a copy of the clone.

## 10. Fence v003 (2026-10-09 07:25Z) — DONE, clone sha ce0bb6e1cc7578b1061d06f63f49b6ffb6efa782a094562cd9055b72302b6914
- Aviv EDITED the reference in place: `PazFarm_2026-10-08/References/Screenshot 2026-10-08 175537.png` now carries his black
  fence line + two yellow gate marks (copy `References/FenceRoute_Aviv_2026-10-09.webp`). Untouched original (sha d48901fd,
  = Astra's record) copied from his Pictures folder to `References/Original/` — use it for any colour re-tracing.
- Route: `Georef/fence_route_v003.py` -> `FENCE_ROUTE_V003.json` (14 vertices, 717 m, CW; manual cleanup of 3 trace glitches;
  gate 1 on edge 5 starting 0.1 m after the bend under the upper yellow mark, gate 2 spans the short SE edge 6, scaled 1.22).
  The barn road is now INSIDE the fence (Aviv: "wrap around the road leading to the barn, and go around the farm").
- Placement `Tools/fence_v003.py` (probe|place|trim|revert|save): 233 panels chained end to end, pitched to the terrain (max
  5.5 deg, X scale 0.95-1.11, 3 cm sink), no separate posts (panel start posts + gate posts), 2 corner braces at ~90 deg turns,
  panel + gate copies with Nanite OFF in `<clone>/PazFarm/v003/Meshes` (Nanite merged the diamond wire into a pale sheet),
  gate 1 = PazFarm_Gate moved, gate 2 = new PazFarm_Gate_2. One strawberry bed outside the line removed (762 left).
  Undo: `fence_v003.py step revert` (receipts PAZFARM_FENCE_V003_BEFORE.json + _TRIMMED.json). Fresh reopen PID 21828 verified;
  captures `receipts/Captures/fv3fresh_b_*.png`, `fv3_c_*`, `fv3_d_*`.
- Map roads: GeoCity tracks are OSM 'track' class, 3 m wide (ROAD_WIDTH_M in geocity_city_module.py); traces do not hit them
  (no usable collision). The south OSM track crosses the fence line on SE edge 7 (fit error); inside the farm the visible roads
  are the overlay's (screenshot-aligned), so the fence follows Aviv's line. Reconcile with the parcel/road work.
- Seen: strawberry beds look pale grey from ~50 m+ (likely leaf loss/sheen at distance) -> part of "never disappear" work.

## 11. Aviv's answers + never-disappear vegetation (2026-10-09/10) — clone sha 6ccbaeb236c262f1cbe209e5aef94bfc23dc9845a3aa35a58c591b4fa45a3d4f
- Aviv's answers: patches road-to-road = GROUND + CROPS; World Partition/HLOD/per-building = WRITTEN ASSESSMENT FIRST.
- Parcels: OSM has only a few tracks near the farm and Sentinel 10 m is too coarse -> asked Aviv for a zoomed-out screenshot
  (2-3x wider), optionally with parcel edges drawn. Context map `PazFarm_2026-10-08/Georef/parcels_context.py/.png` (+-700 m,
  Sentinel + 54 OSM tracks + landuse + screenshot frame + plots + fence). Waiting for his screenshot.
- Vegetation (Tools/never_vanish.py, steps cams|pines|copy_swap|alpha_fix|own_mis|status|save|revert_*): area-owned copies in
  `<clone>/Vegetation/{Meshes,Materials,Textures}` of 4 Modular_Rural_Cabin pines + STF green-tree01/02 + pine-small01/03;
  Nanite ON + Preserve Area; leaf textures copied with do_scale_mips_for_alpha_coverage (threshold = clip); leaf MI clip
  overrides 0.12 (pines) / 0.15 (STF) via `clip_test.py`; STF copies own all 13 MIs (Nanite usage flag otherwise dirties vendor
  MIs; flagged vendor MIs were reloaded from disk with EditorLoadingAndSavingUtils.reload_packages). PCG graph points at the
  copies; regenerated 112,891 plants. Receipts NEVER_VANISH_ALPHA.json / NEVER_VANISH_SAVE.json; captures nv_pre_*, nv_final_*,
  nvfresh_* (fresh reopen PID 28092: 0 dirty, 0 usage-flag writes). Diagnosis tools: pcg_visibility.py, nanite_toggle.py,
  lod_probe.py, mat_probe.py, find_instance.py.
- Result: crowns visible from 460 m and at 300-400 m oblique. Beyond ~600-700 m vendor pines still thin to pale trunks (needle
  cards sub-pixel; same with Nanite off). Durable fix: Astra-made Nanite-friendly Aleppo pine (geometric needle clusters, solid
  alpha) + HLOD/impostor far range. Strawberry beds pale at ~50 m+ still to check.
- WP/HLOD assessment: `NewArea_..._4km_2026-10-08/WP_HLOD_ASSESSMENT_DRAFT.md` (subagent draft, reviewed; recommendation: no
  conversion now; optional trial on a COPY of the clone only with Aviv's authorisation; vegetation non-spatially-loaded).

## 12. WP / per-building trial (Aviv 2026-10-10: trial on a copy; one object per building, reversible; always-loaded
##     Instancing HLOD for trees; grass rule excluded but should appear when zooming in; brief Astra for pine + beds)
- Trial copy: `/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/L_..._WPTrial` (copied from the clone 6ccbaeb2,
  `Tools/make_wptrial.py`; clone unchanged). Launcher purpose `wptrial` (+ WP mirrors in write scope). Save tool
  `Tools/wptrial_save.py` (label). Receipts `receipts/WPTRIAL_*`.
- Stage A DONE (non-WP, map sha 3c40d4099a3d9bfc..., 190 MB): `Tools/split_buildings.py` (plan|build|fix_attach|remove|verify)
  + `Tools/split_shells.py` (analyze|build|remove|verify). 592 actors `Bldg_<osm>` (folder Buildings): BuildingRoot (static),
  per-mesh ISMs (window/wall modules), `Door` (SM_Steeldoor, own StaticMeshComponent -> animatable later), `Building` (32 whole),
  `Shell` (per-building mesh `<trial>/Buildings/Shells/SM_Shell_<osm>`, 560 files, 18 MB; split of the merged generated-shell
  mesh by footprint, exact UVs/materials, flat normals via full build). All 35,459 instances exact (0.0 cm) after save+reload.
  Receipt data: WPTrial/BUILDINGS_COMPACT.json, FOOTPRINTS.json (from HDA_CATALOG_RECEIPT.json; UE cm = (P0,P2,P1)*100).
- Gotchas: (1) get_triangle_vertices returns 3 junk ids first -> use polygon getters; (2) rebuilding a duplicated engine Cube
  crashed the editor (render resource deleted) -> create_asset(StaticMesh, None) + build_from_static_mesh_descriptions(..., False,
  False) (fast build skips normals); (3) SubobjectDataSubsystem: a STATIC part under a MOVABLE parent loses its attachment on
  save -> make the whole chain STATIC top-down, then attach (fix_attach); (4) save after every stage (one crash lost an unsaved stage).
- Strawberry diagnosis (for Astra): beds turn pale grey-green at 60-150 m with Nanite on (Preserve Area brightens the simplified
  tiny leaves); Nanite off stays darker green but still greyish -> need a far-robust bed (larger solid leaf masses / canopy hull,
  dark mulch) and a lowest LOD that reads as a green ridge (HLOD shows the lowest LOD).
- Next: Stage B = World Partition conversion of a second copy (commandlet, -ConversionSuffix), partitioned PCG, HLOD layers
  (vegetation Instancing, not spatially loaded, Nanite allowed, instance filters 0; vet non-Nanite last LODs), measure files/
  load/save, verify with unloaded cells or PIE.
- Stage B DONE 2026-10-10 ~01:05Z: WP map `.../L_KarmeiYosef_31850349_34907601_4km_WPTrial_WP` (umap sha d8b2bfd4; 1,478 external
  actor files, 310 MB). Full result + numbers: `NewArea_..._4km_2026-10-08/WPTrial/TRIAL_RESULT.md`. Tools: wp_setup.py
  (probe|load_all|unload_all|hlod|use_converter_layers|landscape_hlod|pcg_generate|status), wp_verify.py (editor_hlod|region|hlods),
  wp_layers_check.py, dirty_classes.py. Converter layers used: `..._HLODLayer_Merged` switched to INSTANCING (always loaded) for
  vegetation+landscape, `..._HLODLayer_Instanced` (grid) for buildings; my HL_* layers in <trial>/HLOD are unused (not in the
  hash-set HLOD setups). Editor modal "Warning: Loading Instancing HLOD Layer" must be accepted (sent Enter to the window).
- 01:15Z corrections (WPTrial/TRIAL_RESULT.md "Update"): vegetation/landscape HLOD layer moved into the persistent
  "Non-Spatially Loaded HLODs" setup via RuntimePartitions StructBase.import_text (Tools/hashset_move_layer2.py; console `set`
  is blocked in the editor) -> verified 370 non-spatial HLOD actors load by default with 109,893 plants + 2,192 farm + 36,019
  building parts + 64 landscape meshes. PazFarm_Detail HISMs were Movable (excluded from HLOD) -> farm_static fix. Trial WP map
  sha 2ad84a2c. Untested: PIE/standalone runtime streaming, frame time/memory. Trial files ~2,050 / 510 MB: not for git.
- 08:40Z PLAY-MODE TEST DONE (TRIAL_RESULT.md "Play-mode test"): Aviv chose far trees = LOWEST LOD (disallow_nanite on the
  vegetation layer; 8 clone Vegetation copies got real-geometry auto LODs via Tools/lowest_lod.py, before-state
  receipts/LOWEST_LOD_BEFORE.json - persists in the clone folder, Nanite path unaffected) and trial landscape always loaded
  (he asked why ground looked low quality = landscape HLOD; he said no fix needed but it was already applied in the trial).
  PIE tools: Tools/pie_test.py + pie_run.py (unthrottle via Default__EditorPerformanceSettings.bThrottleCPUWhenNotForeground).
  Results: per-building ~2x draw calls, no measurable frame cost; WP+lowest-LOD HLOD +8 ms GPU in the whole-area view only.
- Aviv: delete trial files ONLY after his verification and explicit confirmation. Delete list: Content/Project/Areas/
  KarmeiYosef_31850349_34907601_4km_WPTrial/ (568 files), Content/__ExternalActors__/.../_4km_WPTrial/ (1,478),
  Content/__ExternalObjects__/.../_4km_WPTrial/ (6), Staging/NewArea_..._4km_2026-10-08/Before/L_..._WPTrial*.umap.

## 13. State at 2026-10-10 ~09:00Z (before Aviv's compaction) — READ THIS FIRST
- Editors: none running (all mine closed clean). No Unreal work pending in memory.
- Aviv DECIDED: keep ONE OBJECT PER BUILDING ("Lets keep the one object per building, I like it"). Production route is still
  open: (a) generator change via the manager (per-building bake), or (b) the post-bake regroup tools proven in the trial
  (`Tools/split_buildings.py` + `split_shells.py`). Not started; ask Aviv before doing it on the real areas.
- Aviv DECIDED earlier: far trees = lowest LOD (Nanite disallowed in the always-loaded vegetation HLOD); grass rule excluded
  (but grass should appear when zooming in — later).
- Trial files: delete ONLY after Aviv verifies and explicitly confirms. Not confirmed yet. Delete list in section 12.
- Persisting change outside the trial: 8 clone Vegetation copies got auto LOD chains (Tools/lowest_lod.py,
  receipts/LOWEST_LOD_BEFORE.json); clone renders them via Nanite so its look is unchanged.
- Astra: brief `PazFarm_2026-10-08/HANDOFF_ASTRA_VisualFix_v003.md` (Aleppo pine + far-robust strawberry bed; updated
  for "lowest LOD only far away"); Aviv asked what to send -> the paste-ready message at the end of that file.
- OPEN PROPOSALS awaiting Aviv's approval (do NOT act before he approves):
  1. Farm ground looks odd (flat pastel painted overlay `T_PazFarm_Ground` via Farm_Blend=1, hard rectangle edges, painted
     stripes, cut at the screenshot frame). Proposed: replace the painted overlay with real ground materials painted per
     plot (landscape layers from Aviv's ground packs: GrassMat, DesertSandPack, RealisticDesertPack, ForestLandscape, ...),
     soft noisy plot edges, field margins, crops as real low plants instead of painted stripes, parcels extended road to
     road (needs his wider screenshot); quick interim option = keep overlay as a subtle tint (blend ~0.35, feathered
     edges, no stripes).
  2. More trees around the farm and overall: Sentinel-2 vegetation index (NDVI, 10 m) -> real tree-cover map driving PCG
     tree density; windbreak/hedgerow tree rows along dirt roads and parcel edges near the farm; higher forest/scrub
     densities; isolated field trees; all with the never-vanish copies; cost note (more far HLOD trees = more GPU in wide views).
- Still waiting from Aviv: wider screenshot for the parcels (road-to-road extension, ground + crops).

## 14. Aviv APPROVED both proposals (2026-10-10 ~09:10Z, AskUserQuestion)
- Farm ground: "Real materials per plot" (remove the painted overlay; real ground materials per plot, soft edges, real low
  crops instead of painted stripes; road-to-road extension still waits for his wider screenshot).
- More trees: ALL THREE parts approved: satellite tree map (Sentinel-2 greenness), windbreak rows near the farm, denser
  forest and scrub (~2-3x + single field trees). Target: the 4 km PCG clone only. Astra message was given to him.
- 18:05Z CORRECTION from Aviv: "I don't want the plot mask to be according to screenshot boundaries at all." -> plot edges
  from the map's dirt roads. Parcel preview 1 (satellite field edges) -> Aviv chose "Push all to roads"; preview 2 -> "Yes,
  lighter rows". Parcels: `PazFarm_2026-10-08/Georef/parcels_v2.py` (USE_SAT False; rays along each plot's side lines until an
  OSM highway / traced farm road (continued straight) / building / village-water-forest zone / other plot) -> PARCELS_V2.json,
  parcels_v2_labels.tif (1 m, +-1000 m around the pin), parcels_v2_preview.png. +77.7 ha.
- Ground mask v3: `Georef/farm_ground_v3.py` -> SourceData/.../zones/PazFarm/T_PazFarm_GroundMask_v3.png (1664 m square,
  0.81 m/px, west edge -680.5 m / north edge 787.0 m from the pin), FARM_GROUND_V3.json; crops CROPS_V3.json (134,097 green
  stand-in plants at lighter spacing; 7,087 new avocado/citrus/young citrus on the same global lattice, doubles skipped).
- Trees offline: `NewArea_..._4km_2026-10-08/Zones/trees_v2.py` -> zones/<run>/trees_v2/*.png (six masks parcel-cleared *_P3,
  ForestTrees, ScrubTrees, SatTrees, OpenField), TREES_V2.json; windbreaks Georef/WINDBREAKS_V2.json (1,541 trees).
- Editor tools: `Tools/farm_real_ground.py` (v2 names, FarmR_Origin*/SizeCm, satellite colour mix; NO rebuild step),
  `Tools/ky4_trees_v2.py` (import_masks | graph (PCG_KY4_Zones_v002) | assign_graph | crops | windbreaks | status).
- INCIDENT 18:01Z: my editor PID 30592 crashed (access violation) in a material "rebuild" step (delete_material_expression);
  clone map NOT saved (sha still 6ccbaeb2). Aviv's own editor 38676 had closed by itself (no crash report). Unreferenced v1
  leftovers for Aviv's delete-on-confirmation list: <clone>/PazFarm/RealGround/{T_PazFarm_GroundMask, M_GeoCityAuto_KY4_RealFarm,
  MI_GeoCityGround_PazFarmReal} (screenshot-plot version).
- Astra delivered VisualFix v003 (3 Aleppo pines 113k tris + 1,642-tri lowest LOD; strawberry bed v003 10.4k + 282-tri lowest
  LOD, slot 0 mulch / slot 8 canopy) at PazFarm_2026-10-08/AstraModels/Revisions/VisualFix_v003/ - NOT yet imported; ask Aviv
  after the ground/tree build (separate reversible step).
- 19:12Z DONE + fresh-reopen verified (PID 26076, 0 dirty): clone map sha 023aa1f5daa20bd9... Full result:
  `PazFarm_2026-10-08/RESULT_REALGROUND_TREES_2026-10-10.md` (real ground v2 material/MI, PCG_KY4_Zones_v002, PazFarm_Extension
  141,115, KY4_Windbreaks 1,541; PCG 134,127 incl. 58,088 trees (was 31,988); PIE farm 25.1 / village 13.7 / forest 8.4 / wide
  29.8 ms vs 17.5 / 13.8 / 8.4 / 24.4). Final MI: SatMix 0.05, MacroAmt 0.25, tints in the RESULT file.
- CRASH RULES (3 crashes, same python access violation via MaterialEditor/PCG callbacks): wait for PCG idle (landscape material
  changes auto-regenerate the clone PCG), never edit the same material graph twice in one session, save after each stage
  (Tools/gc_probe.py forces a GC to surface corruption early). Records: ASSIGNMENT_RUN.json + ParallelEditors EDITOR_{30592,34872,6808}.
- Next to ask Aviv: import Astra v003 (Aleppo pines for forest + windbreaks; strawberry bed in place); optional draw-distance limit
  for the 134k green-field stand-ins. v1 RealGround leftovers added to his delete-on-confirmation list. No editor running.
- 19:45Z: Aviv "Remove the guesses for now" (guessed farm-road continuations were "way off"; OSM partial near the farm) ->
  parcels rebuilt without them; Astra v003 imported + applied (Aleppo pines in PCG_KY4_Zones_v003 + windbreaks, strawberry
  bed v003 on 762 beds). Clone map 42b39ead (fresh-reopen verified PID 3048). Details: RESULT_REALGROUND_TREES_2026-10-10.md
  "Update 19:45Z". Aviv is exploring the clone in his own editor (asked him not to save it). Real farm roads still open
  (wider screenshot / his drawing later). Crop stand-ins stay always visible (his choice). No editor of mine running.

## 15. Farmland rebuilt from Aviv's wide screenshot (2026-10-10 ~20:00Z) - IN PROGRESS
- Aviv: forest "gorgeous", farm parcels not; "scrap our approach regarding the farm parcels, and enrich it with more vegetation
  and fitting textures"; road 44 missing in Unreal. Decisions (AskUserQuestion): roads = "Extract from my screenshot"; farmland =
  "Every field from the screenshot"; field preview -> "Yes, build it".
- Folder `Staging/PazFarm_2026-10-08/Fields_2026-10-10/` (all offline, gis env python; numpy BLAS crashes in that env -> no
  corrcoef/matmul; GDAL temporaries must stay referenced):
  align_pair.py (ALIGN.json: labelled vs plain screenshot dx 4 dy -1), roads_overlay.py (road_mask.png grey Google roads,
  highway_mask.png road 44), georef_wide.py (WIDE_FIT.json: 2.03 m/px, theta 0.03 deg, te -20.5 tn 53.5 m from the pin,
  93% of road pixels within 10 m of OSM), fields_cluster.py (12 k-means clusters), fields_v1.py (223 fields, 8 types,
  FIELDS_V1.json + fields_v1.tif + fields_v1_preview.png), fields_build_v1.py (FIELD_PLANTS_V1.json: crop 135,500, orchard
  17,967, rows 1,904, weeds 14,314, margin shrubs 8,271, greenhouse tunnels 2,463; ground mask v4 4096 px over 3,456 m (v3
  weights kept inside the fence; dirt roads only on farmland); ROAD44.json (18 OSM trunk/primary ways); fields_clear_zone.png).
  References: `PazFarm_2026-10-08/References/Wide_2026-10-10/` (wide_with_roads.webp, wide_satellite.webp).
- Zones/trees_v2.py now clears zone masks from fields_clear_zone.png and spaces windbreaks from the field trees (1,140).
- Editor tools ready: Tools/farm_real_ground.py step set_mask (new T_PazFarm_GroundMask_v4, BC7, on the MI), Tools/fields_place.py
  (probe | remove_old | place | road44), ky4_trees_v2.py (reimport_masks, assign_graph v003, remove_placed, windbreaks, make_static).
- Planned stages (save after each, PCG idle before each step): 1 set_mask; 2 reimport_masks + assign_graph v003 + save;
  3 remove_old + place + remove_placed(KY4_Windbreaks) + windbreaks + make_static + road44 + save; then fresh reopen, captures, PIE.
- 20:00Z: BLOCKED - Aviv's editor PID 3188 has the clone map open (exploring); asked him to close without saving.
- 21:17Z DONE (Aviv closed his editor): fields built + fresh-reopen verified (PID 37244); clone map 65adf6dd. Result:
  `PazFarm_2026-10-08/Fields_2026-10-10/RESULT_FIELDS_2026-10-10.md`. Actors KY4_Fields_{Orchards 19,865, Crops 135,449, Weeds
  22,568, Greenhouses 2,462}, KY4_Windbreaks 1,140, KY4_Road44 (mesh <clone>/Roads/SM_KY4_Road44, MI_AsphaltMat_Inst8);
  PazFarm_Extension removed; PCG v003 regenerated with fields cleared (112,405). MI now uses T_PazFarm_GroundMask_v4 (per-field
  mixes), SatMix 0.3, MacroAmt 0.3. PIE farm 22.3 / village 15.1 / wide 33.1 ms. No editor of mine running.
- Unused now (delete only on Aviv's confirmation): <clone>/PazFarm/RealGround/{T_PazFarm_GroundMask, M_GeoCityAuto_KY4_RealFarm,
  MI_GeoCityGround_PazFarmReal} (v1) and T_PazFarm_GroundMask_v2; PCG_KY4_Zones_v002 kept for undo.

## 16. Road 44 by the generator (Aviv 2026-10-11 "Generator builds it" + "Yes, full generator route") - DONE (see 17)
- Also approved: dirt-road fix ("Yes, fix them"): field ground must step aside on the generator's Dirt_Path track paint
  (tracks have no mesh; they are RoadBed->Dirt_Path landscape paint) + lighter screenshot-road dirt. Not done yet (Aviv's
  editor PID 34732 held the clone). Astra brief for vines/olives/grass: PazFarm_2026-10-08/HANDOFF_ASTRA_FieldCrops_v004.md.
- Why road 44 was missing: the generator's ROAD_WIDTH_M/ROAD_CLASSES had no trunk/primary (dropped as 'omitted').
- Generator v002 DONE offline: build_hda_4km_v002.py + verify_hda_4km_v002.py -> .../revisions/20261008_KarmeiYosef_4km/
  GeoCity_city_v015_CurrentBank_4km_KY_v002.hdalc (sha b1cc6fab..., type 15.0_4km_karmeiyosef_v002; diff = trunk 12 /
  trunk_link 7 / primary 10 / primary_link 7 in ROAD_WIDTH_M + ROAD_CLASSES, NO_SIDEWALK_CLASSES in the active
  cook_sidewalks; HDA_SOURCE_V002.json, module copy geocity_city_module_4km_ky_v002.py). v001 untouched.
- Workflow facts (sub-agent read of geocity_bank_workflow.py): regenerate mode reuses the existing HoudiniAssetActor and never
  reads profile['hda'] (lines 1019-1038) -> v002 needs instantiate mode: delete the v001 actor + save the main map, switch
  profile['hda'] BEFORE the run (profile sha taken at start). Old baked actors are removed via LAST_SUCCESSFUL_WORKFLOW_STATE
  baked_actor_paths (72); bake packages are fixed names (KarmeiYosef_..._{buildings,road_surfaces,sidewalks}) shared by the
  clone -> backed up in NewArea_.../Before/regen_v002_<utc>/ (+ main map c7c858c5, profile, ledger, SHA256SUMS.txt).
- Ready tools: Tools/hda_v002_prepare.py (import | remove_actor), switch_profile_v002.py (backs up the profile once),
  Tools/start_area_generation.py (menu run; only editor; ~1.8 h last time).
- Plan: (1) Aviv closes Unreal; (2) launch purpose run on the MAIN map (sha c7c858c5), import v002, remove_actor (saves map),
  quit; (3) switch_profile_v002.py; (4) fresh launch run on the main map, start_area_generation, wait via lease line / mtime
  only; (5) verify (road 44 in road_surfaces, 1 Landscape, Bake folder diff), fresh reopen; (6) new clone from the new main
  map + carry over PazFarm_*, KY4_Fields_*, KY4_Windbreaks, PCG volume (drop KY4_Road44), landscape MI, regenerate PCG;
  (7) dirt-road material fix as first graph edit of a fresh session; captures, PIE, docs.
- 06:23Z RUN STARTED (Aviv closed his editor, "go ahead"): main map prepared in PID 28664 (v002 HoudiniAsset imported =
  <root>/HDA/GeoCity_city_v015_CurrentBank_4km_KY_v002; v001 actor removed, receipts/HDA_V001_ACTOR_BEFORE_V002.json; map
  saved 2f60fe1b); profile switched (switch_profile_v002.py; backup AREA_PROFILE_before_v002.json; sha 4504e3fc); fresh
  PID 15964 started the menu generation (instantiate mode, timeout 14,400 s, official Engine connected).
- Astra FieldCrops v004 DELIVERED (Revisions/FieldCrops_v004: 3 vine-row tiles, 3 olives + young, 6 grass clumps, 2 grass
  patches, authored LOD3 each; ~2 GB Temp/DistanceCache left - delete only with Aviv's OK). Tools ready: Tools/apply_astra_rev.py
  (revision param), Fields_2026-10-10/fields_build_v2.py -> FIELD_PLANTS_V2.json (olive/vine/grass/patch), fields_place.py
  (plants param, V4: meshes, KY4_Fields_Vines), trees_v2.py windbreaks 1,146 spaced from v2 trees.
- New-clone tools: Tools/clone_v2.py (export from old clone | duplicate main -> L_..._PCGTrial_v2 | import), all clone tools take
  ARGS.clone_suffix '_v2'; ky4_trees_v2.py step volume (new PCG volume + graph version); farm_real_ground.py step
  path_through (Dirt_Path pass-through; FIRST graph edit of a fresh session).
- After the run: verify (lease released baked_saved_verified, LAST_SUCCESSFUL_WORKFLOW_STATE road stats, Bake diff vs
  Before/regen_v002_*), quit, fresh reopen; old clone session: export PazFarm_Detail/Barn/Gate + duplicate; new clone session:
  path_through, assign MI, import farm, Astra v004 import, PCG volume v003, fields place V2, windbreaks, saves, captures, PIE.
- 08:07Z FIRST v002 RUN FAILED: failed_bake_save_verification "Duplicate Landscapes after bake". Cause: instantiate mode with a
  previous bake present - the new bake took the Landscape name, Unreal renamed the old one '<name>_landscape_old_0', the ledger
  (by path) then pointed at the new one, so the old one was not retired. Map NOT saved by the run; the 3 shared Bake packages
  WERE overwritten at 08:07:34-38 (originals in Before/regen_v002_20261010T214646Z/).
- Aviv: "Recover + rerun". Tools/recover_v002.py removed only '..._landscape_old_0', saved the main map (df223fc8, 74 actors,
  1 Landscape, v002 HDA actor; receipts/RECOVER_V002_FAILED_RUN.json); exit_failed_area_run.py discarded 3 cook packages and
  quit; lease release line appended by this operator (failed_bake_save_verification_recovered). 09:54Z RERUN started in
  regenerate mode (PID 32268, v002 actor kept; account_previous_landscapes handles the Landscape).

## 17. Rebuilt clone DONE (2026-10-11 12:07Z) - READ THIS FIRST
- Result doc: PazFarm_2026-10-08/RESULT_CLONE_V2_2026-10-11.md. Rerun 09:54Z succeeded: main map f21ab2c7 (lease released
  baked_saved_verified 11:44Z; trunk 134,225 / trunk_link 3,523 visible faces, no trunk sidewalks; bake 2e646c7f / fc8f0a69 /
  b5522ac6). Road 44 uses the generator's standard grey paving road material (all generated roads share it).
- NEW CLONE = /Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/L_KarmeiYosef_31850349_34907601_4km_PCGTrial_v2,
  saved sha 299c5b60..., fresh-reopen verified (receipts/VERIFY_CLONE_V2.json, all_match true). Old clone 65adf6dd kept as fallback.
- Steps done: clone_v2 export (old clone, PID 9260: PazFarm_Detail/Barn/Gate/Gate_2) -> duplicate (CLONE_V2_COPY.json) ->
  PID 5504: path_through (material e2a679ec saved) then CRASH at the map save (receipts/CRASH_PID5504_20261011.json; records
  released by hand) -> PID 27536: assign MI, save; import farm actors (dz 0-3 cm), save; apply_astra_rev FieldCrops_v004
  (textures/materials/meshes) + save_prefix; PCG volume v003 (112,285) + pcg_finish; fields_place V2 (217,600) + windbreaks
  (1,146) + make_static + save_prefix (v004 MIs dirty again after placement) + pcg_finish (299c5b60); captures clone_v2_*;
  PIE farm 18.8 / village 13.6 / forest 8.7 / wide 35.8 ms -> quit_clean -> PID 35308 fresh reopen verify.
- RULE (4th crash of the family): after any material-graph edit, quit the editor before any other step or save.
- Not applied: lighter screenshot-road dirt (FarmR_Tint_Dirt MI tune; they already read pale). Open: Aviv's look at road 44's
  paving material; deletions still need Aviv's confirmation (trial files, v1 ground packages, T_PazFarm_GroundMask_v2,
  Astra Temp/DistanceCache ~2 GB, later the old clone).
- Editor PID 35308 left OPEN on the new clone for Aviv to explore (clean, nothing dirty). If he closes it, release
  ASSIGNMENT_RUN.json / ASSIGNMENT_RUN_PID35308.json / ParallelEditors/EDITOR_35308.json before the next launch.

## 18. Wrap-up requests (2026-10-11 ~15:45Z) - READ THIS FIRST
- Aviv: (1) save the process for new environments -> "Playbook + skill": `Staging/Playbooks/NEW_ENVIRONMENT_PLAYBOOK.md` +
  project skill `.claude/skills/new-environment/SKILL.md` (/new-environment). Tools stay where they are (reference folder);
  the playbook lists which tools are generic vs site recipes.
  (2) one last fix: strawberry beds look "very gamified" -> answers: Astra finds her own photo references; season = young
  late-September plants (no fruit); rows at real spacing; beds must sit on the ground (his screenshot
  PazFarm_2026-10-08/References/Strawberry_2026-10-11/aviv_beds_not_on_ground.webp).
- DONE on the new clone (editor PID 35308): Georef/strawberry_beds_v2.py -> STRAWBERRY_BEDS_V2.json (2,482 tiles, 1.7 m
  centres, same plots/row directions, fence and track checks); Tools/straw_beds.py relayout: 762 -> 2,478 ground-fitted tiles
  (pitch to both tile ends, roll to cross slope, 3 cm sink; mid-tile 2.5-9 cm into the ground, none floating; 4 skipped, no
  ground hit). Before-state receipts/STRAW_BEDS_BEFORE_20261011T154144Z.json (`straw_beds.py step revert`). Map saved
  fafde8f006f68fe5...; captures receipts/Captures/straw_after_*.png (vs straw_now_*).
- WAITING FOR ASTRA: brief PazFarm_2026-10-08/HANDOFF_ASTRA_StrawberryBeds_v005.md (paste-ready message at the end). When
  delivered: apply_astra_rev.py revision StrawberryBeds_v005 (textures/materials/meshes) + save_prefix; then add a straw_beds
  `swap` step (3 variants A/B/C mixed over the 2,478 transforms, same -Y 4 m tile, keep transforms; re-run relayout if the
  length changed), save_prefix (MIs go dirty), clone_v2 save, fresh reopen verify, captures at cameras_straw_v2.json.
- Editor PID 35308 still OPEN on the new clone (nothing dirty) for Aviv. When he closes it: release its records, then fresh
  reopen (pcg, sha fafde8f0) + verify_clone_v2.py --args-file verify_clone_v2_args.json (PazFarm_Detail now 3,905).

## 19. Strawberry fix DONE (2026-10-11 17:10Z) - READ THIS FIRST
- Astra delivered StrawberryBeds v005 (3 tile variants + end cap, authored lowest LODs, real photo references). Applied on
  the clone _v2: apply_astra_rev.py (fixed: slots bound after the LOD import; base_model key; import_normals) + save_prefix;
  straw_beds.py place_variants (A 809 / B 824 / C 845, 106 runs, 212 end caps, exact joins by tiny Y stretch) + save_prefix
  (MIs dirty again) + clone_v2 save -> map 41c76dfb..., fresh reopen PID 3180 verified (PazFarm_Detail 4,117, all match).
  Details: PazFarm_2026-10-08/RESULT_CLONE_V2_2026-10-11.md (updates 15:42Z and 17:10Z).
- PIE: farm 19.7 ms (GPU 18.8), village 13.7, forest 8.5, wide GPU ~38 ms; wide frame time shows a 333 ms tail (editor
  idling pattern) in both runs - not attributed to the beds.
- Seen, not fixed (ask Aviv): a pale field ~300 m S of the farm turns sky-blue at grazing angles only (ground too glossy?).
- Editor PID 3180 is OPEN on the clone (nothing dirty) for Aviv. If he closes it: release its 3 records (no reopen needed,
  already verified). Deletions still await his confirmation (list in sections 12/15/16 + old clone + Astra Temp caches).

## 20. One object per building on the clone (2026-10-11 17:40Z) - READ THIS FIRST
- Aviv: "Split on the clone now, and add it to the playbook and add a question on whether to change the generator later";
  HLODs: "Keep it without" (no World Partition for this 4 km area).
- Done with the trial's tools (now `target: clone_v2`): 592 Bldg_ actors (591 + unsupported shell), 35,459 parts, 560 shell
  meshes in <clone>/Buildings_v2/Shells/, merged buildings actor removed (found by mesh; label is ..._buildings_1 after the
  regeneration). Map 7e3d06d6..., fresh reopen PID 38868 verified (verify_clone_v2.py now also checks buildings).
- Playbook: section 5.6 (split after every generation) + [D] generator per-building bake question; section 0 WP/HLOD rule.
- Editor PID 38868 OPEN on the clone (nothing dirty). PIE after distance fields: farm 18.1, village 12.6, forest 8.5, wide 35.2 ms
  (no stall tail). If Aviv closes it: release its 3 records.

## 21. Wrap-up (2026-10-11 ~18:30Z) - READ THIS FIRST
- Aviv: "delete the trial files and old clone" -> sent to the Windows Recycle Bin (2.65 GB; receipt
  receipts/DELETED_TO_RECYCLE_BIN_20261011.json): WPTrial content + its __ExternalActors__/__ExternalObjects__, the old clone
  map L_..._PCGTrial.umap, and their Before/ backups. Reference check first: nothing outside referenced them
  (receipts/DEPS_env_4km_v2.json). Kept: WPTrial/ staging records (TRIAL_RESULT.md is the playbook's WP recipe).
- Aviv: "commit this environment ... along with the playbook" + "Only the used files" of the 5 store packs ->
  local commit b38a65b6 on master (4,370 files, LFS for binaries), NOT pushed (push is Aviv's: `git push origin master`).
  Contents: both 4 km area folders, the 116 used pack files + DT_EnvironmentBank_AnyArea, this task's Staging folders,
  area profile, this handoff, Playbooks, .claude/skills/new-environment. .gitignore: this area's Cook leftovers,
  HDA_CATALOG_RECEIPT*.json, Astra Temp caches. Other sessions' working-tree changes were not staged.
- Export question answered (Migrate to an empty UE 5.8 project, then zip; ~5.5 GB of dependencies; SunPosition plugin,
  Houdini Engine for the generator actor; store-asset licences). Offered to build the zip.
- Still pending Aviv: unused v1 ground packages + T_PazFarm_GroundMask_v2, Astra Temp caches (not in his delete request);
  blue glossy field item; generator per-building bake [D]. No editor running.

## 22. Standalone zip (2026-10-12) - READ THIS FIRST
- Aviv: "Yes, build the zip for me". Zip: C:/Users/USER/Documents/UE_Exports/KarmeiYosefPaz_2026-10-12.zip (5.37 GB, 1,495
  entries, CRC ok, sha256 4AB11918...). Unzipped ready-to-open project: C:/Users/USER/KYPaz/KarmeiYosefPaz.uproject.
  Tool: Tools/export_env.py (+ deps_probe.py roots=[working map]); playbook section 10b.
- Headless check of the export (UnrealEditor-Cmd -run=pythonscript -nullrhi): map loads, 682 actors, PCG 112,285, all field/
  farm counts, 592 Bldg_ / 35,459 parts / 560 shells, 0 meshless components, 0 default-material slots; only load error = the
  Houdini actor (plugin not included, as intended).
- Found + fixed in the source: the 8 FieldCrops v004 grass meshes had unbound lowest-LOD slots (*_Low, WorldGrid) - same
  binding-order bug fixed for v005. apply_astra_rev meshes (names = the 8) re-bound them; MIs saved; map saved 3b8278a8
  (marked dirty by the mesh change; verify all_match). Follow-up commit after b38a65b6.
- Sent to Recycle Bin: the first export build and the check-only Verify.uproject (my own outputs).

## 23. Coworker hand-over questions (2026-10-12) - READ THIS FIRST
- Aviv forwarded a coworker's questions (simulation use of the KYPaz zip). Answers + data:
  NewArea_.../Handover_2026-10-12/ (ANSWERS.md, roads_wgs84/roads_ue_cm/buildings_wgs84/pois_wgs84 .geojson, BP_EnvironmentSky.t3d,
  north_offset_check.json, build_roads.py, build_rest.py); zip Documents/UE_Exports/KarmeiYosef_SimHandover_2026-10-12.zip;
  private page https://claude.ai/artifact/9s1xL2FtxzoqdNuJQBxsgZ (Aviv must share it with the coworker).
- Facts: local equirectangular frame from city_source_v1.json (Mlon 94646.29724274, Mlat 110884.19393286, origin = tile centre
  = UE 0,0); UE X east, Y south; Z = EGM2008 m x 100 (ground at origin 16,468 cm); convergence 0.
- DEFECT FOUND (not fixed, waiting for Aviv): BP_EnvironmentSky NorthOffset = 0 in this level (and the zip) -> sun 90 deg off.
  Measured headless: -90 gives 0.0 deg error at 06/12/17h. Likely the same on other GeoCity maps with this sky (Shujaiya: NorthOffset
  0.0 in Stage4 receipts; not checked, other owners). Playbook section 4.5 added.
- Roads: baked meshes (road_surfaces 1.99 M tris, sidewalks 0.82 M), +8 cm above terrain, complex collision only -> physics/simple
  traces fall to the landscape. Tracks/paths = landscape paint only. UpdateSky = 2.0 ms CPU per call (actor scan).
- Tools added (read-only): handover_probe.py, roadmesh_probe.py, roadhit_probe.py, sky_dir_probe.py, mesh_bounds.py,
  volume_collision_probe.py, mesh_collision.py. Gaza Rimal level: deleted 2026-10-06, not in git or Recycle Bin.
- Aviv's decision on the sky defect: "Only tell the coworker" -> project and zip stay with NorthOffset 0; the coworker sets -90
  on their side (ANSWERS 1.6). Do not change the sky in this project unless Aviv asks.

## 24. Trash-bin rotating pole (2026-10-12) - READ THIS FIRST
- Aviv relayed a coworker's diagnosis (open trash bin with a rotating pole); in our project the same bank material renders
  Trashcan_Open03 in 6 maps (Shujaiya, KY 2 km + its PCG trial, KY 4 km main + clone _v2, ElWahatEgypt) and the bank tables
  list the bin. Aviv: "Make it static".
- Done (PID 29296, then quit): shared bank material /Game/Project/Shared/ModelBank/Materials/BankIntegration_20261004/
  M_8577bd057998eb82 -> World Position Offset fed by a zero Constant3Vector (one node added, nothing deleted), recompiled, named
  save: sha 39c98740 -> f19ff5b1. Receipt receipts/TRASHCAN_WPO_STATIC.json, backup Before/TrashcanWPO_2026-10-12/.
  Vendor original M_Trashcan unchanged. No map re-save needed (map _v2 still 3b8278a8). Captures trashbin_after_*.png
  (the trashbin_before_* shots were taken while exposure was settling; their glowing column is a CitySample street lamp,
  not the bin - not evidence of the defect).
- NOT committed (git shows the material modified). The bank material is shared/bank-owned: tell the bank owner session.
  The KYPaz zip and C:/Users/USER/KYPaz still hold the old material (the coworker fixed his copy).
- Same ActorPositionWS+Time+RotateAboutAxis pattern exists in M_Slums / M_Slums_Cloth_Anim (unused). Playbook gotcha added.
