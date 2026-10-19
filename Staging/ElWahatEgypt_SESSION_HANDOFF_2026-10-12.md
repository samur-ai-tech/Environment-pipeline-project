# El Wahat Egypt — session handoff

Operator: Claude Code session d80546c8-441b-4f05-a98e-220e31cfd866 (Aviv direct, 2026-10-12).
Process: `.claude/skills/new-environment` + `Staging/Playbooks/NEW_ENVIRONMENT_PLAYBOOK.md`.
Task folder: `Staging/NewArea_ElWahatEgypt_29176036_29602273_4km_2026-10-12/` (read `ASSIGNMENT.json` first).

## 0. Current state (update after every stage)

| Item | Value |
|---|---|
| Stage | **DONE (19:31Z)**: v002 regeneration + redo + Astra station; final map **fc89bf00** fresh-reopen verified (82 actors, 14 EW_Station_*, 0 Bldg_, 1 Landscape, nothing dirty); 0 editors, OWNER=NONE. Waiting on Aviv: visual acceptance; deletions listed in section 5. Summary `NewArea_.../RESULT.md` |
| Map (current) | **fc89bf006a28686aad0d48c42cec269ce32fcf77d6116aa728ae05a0c5dd99fe** (19:31Z, fresh-reopen verified): 82 actors, 1 Landscape, 14 EW_Station_*, 0 Bldg_, 1,095 instances. History: run 1 54431c44 -> run-1 final 739b5c23 -> v002 run ed2ff8d1 -> redo d6405195 -> station 6e812bd7 -> fc89bf00 |
| Map (saved, pre-generation) | sha b6670f82 (empty area map with sky NorthOffset -90); HDA asset sha dacd2f92; ground MI sha b447fba9 |
| Area profile | `Staging/ModelBank/ElWahatEgypt_29176036_29602273_4km/AREA_PROFILE.json` sha **890e543a** (hda EW_v002; v001 profile 96297660 kept as AREA_PROFILE_before_v002.json) |
| Owned HDA | **EW v002** `Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank/revisions/20261012_ElWahatEgypt_4km/GeoCity_city_v015_CurrentBank_4km_EW_v002.hdalc` sha cb4ae95c, type `15.0_4km_elwahategypt_v002`, Unreal asset `.../HDA/GeoCity_city_v015_CurrentBank_4km_EW_v002` uasset 2773d46c (`HDA_SOURCE_V002.json`); v001 hdalc 56284287 (`HDA_SOURCE.json`) |
| Source package | `Pipeline Environment/SourceData/ElWahatEgypt_29176036_29602273_4km/acquisitions/1a8c08f7.../20261012T053359Z_bb01eb0e/` (SOURCE_PACKAGE_VALIDATED) |
| Profile candidate | `PROFILE_CANDIDATE.json` (Lebanon template b88ea3e3, decision 85b347ba, registry ab90ab69); HDA asset name `..._4km_EW_v001` |
| Area id | `ElWahatEgypt_29176036_29602273_4km` |
| Centre | 29.176036 N, 29.602273 E (view centre of Aviv's link) |
| Size | 4 x 4 km, 4033 samples at 1 m, landscape half-extent ±201,600 cm |
| Map (planned) | `/Game/Project/Areas/ElWahatEgypt_29176036_29602273_4km/BankIntegration_v015/L_ElWahatEgypt_29176036_29602273_4km` |
| PCG clone (planned) | `/Game/Project/Areas/ElWahatEgypt_29176036_29602273_4km_PCGTrial/L_ElWahatEgypt_29176036_29602273_4km_PCGTrial` |
| Editor ports | Copilot 19860, plugin 18100, native MCP 8020 |
| Editors live | none (checked 19:32Z: 0 UnrealEditor processes, EDITOR_OWNER last line OWNER=NONE) |
| Other shas | road bake mesh c2095747 (full-precision UVs); MI_RoadTrack_EW_v001 d04c88f5 (toned 19:29Z); ground MI 74b03a0c; station master M_EW_Station_Opaque a478d665 |

## 1. Decisions (Aviv, 2026-10-12, by buttons)

- Point: view centre 29.176036, 29.602273 (not the road pin 29.177941, 29.593812, ~850 m W).
- Size: 4 x 4 km.
- Six generator defaults kept: Houdini roads (RoadBLD off); farm tracks kept as roads; Houdini props kept; no Houdini trees; never stop the bake for unbuildable buildings (100%); failed generated poles dropped.
- Buildings: proceed with OSM as is.

## 2. Measured facts

- OSM survey of the 4 km box (Overpass, 05:12Z): 3 buildings, no landuse polygons, no place nodes; highways trunk 2, trunk_link 1, primary 2, service 5, track 4, unclassified 1, construction 1. Expect terrain + a few roads; the zone stage has no OSM land use to start from (Sentinel-2 only).
- Overpass (overpass-api.de) returns HTTP 406 without a User-Agent header.

## 3. Section 1 — setup (done 05:20Z)

- Copied the reference Tools (101 files) plus the offline scripts (`acquire_area.py`, `build_hda_4km*.py`, `verify_hda_4km_v002.py`, `prepare_profile.py`, `promote_profile.py`, `switch_profile_v002.py`, `Zones/*.py`, `Buildings_v2/compact_buildings_v2.py`).
- Global mapping on the copies (receipt `receipts/TOOLS_ADAPTATION.json`, 65 files): task folder name, area id, `KY4` -> `EW4`, ports 19852/18092/8012 -> 19860/18100/8020, centre lat/lon in `acquire_area.py` and `create_area.py`.
- Reference hashes of every copied Karmei Yosef file: `receipts/REFERENCE_TOOLS_HASHES.json` (must stay unchanged).
- Site-specific recipes (Paz Farm, fences, straw beds, fields, apply_v00N) were mapped too so nothing in this folder can write into Karmei Yosef packages; they are templates, not to be run as-is.

- Read-only setup audit (3 agents) saved as `receipts/SETUP_AUDIT_2026-10-12.json`. Fixed (receipt `TOOLS_ADAPTATION.json` passes 2-3):
  - `launch_area_editor.ps1`: operator id d80546c8, record task `ElWahatEgypt4km_<purpose>`, authority date, read scope (KY 2 km MI folder), written_by.
  - `create_area.py`: sky NorthOffset -90 + sun check at 07:00/12:00/17:00 (07:00 light must point -X, angle error < 1 deg, north arrow -Y); ground MI copy source sha-checked (KY 2 km MI 016e75a4, snow 1e6) and MW_SnowWorldPosition asserted 1e6; KY 4 km maps/MI added to protected paths; HDA_SOURCE must point at the El Wahat revision.
  - `ky_client.py` / `ky_capture.py`: client identity + docstring ports; `readback_area.py`: Rotator keywords.
  - `prepare_profile.py`: El Wahat texts/dates, HDA asset `GeoCity_city_v015_CurrentBank_4km_EW_v001`. Template stays Lebanon (sha b88ea3e3): the KY 4 km profile differs from it only in the area fields the script rewrites (same bank digest 12552e14, 1295 rows).
- Sky clock: TimeZone 2.0 without DST (as KY); Egypt civil time is UTC+3 until late October, so the sky clock reads 1 h behind civil time.
- Open later-stage tool fixes (from the audit, not yet applied): `split_buildings.py` / `split_shells.py` targets (main/clone) and the unsupported-shell id (KY-specific; El Wahat may have 0 unsupported and maybe no merged shell mesh); `verify_clone_v2.py` merged-buildings label check; `prep_zone_clone.py` source sha; `hda_v002_prepare.py`, `recover_v002.py`, `clone_v2.py` KY authority/suffix texts; `export_env.py` layer names. Stale copies `build_hda_4km.py`, `build_hda_4km_v002.py`, `verify_hda_4km_v002.py` fail safe (KY targets) and are not to be run.

## 3b. Section 2 — source package (done 05:34Z)

- `acquire_area.py` (gis env python): SOURCE_PACKAGE_VALIDATED. OSM 4,724 nodes, 19 ways (16 highway, 3 closed buildings), 0 missing refs. Overpass: overpass-api.de 504 x2, kumi 500, private.coffee 500, then overpass-api.de OK (1.28 MB) on retry round 2.
- DEM: Copernicus GLO-30 N29 E029 downloaded (41 MB) into `AcquisitionCache/tile_cache/`; DSM 236.8-255.8 m (flat desert, 19 m relief).
- The shared acquire.py already sends a User-Agent; no wrapper patch was needed.

## 3c. Section 3 — owned generator (done 06:40Z)

- Aviv's road decisions (buttons, ~05:45Z and ~06:30Z): **no sidewalks** on service/unclassified either; **build the construction road** (way 1175781900, highway=construction + construction=service, 269 m, links service 903340179 and unclassified 1198636259); **trim long roads to the area** (trunk/primary/track ways are 205-251 km long; 931.7 km total -> 21.2 km, 4,736 -> 218 vertices, every in-box segment identical; `receipts/TRIM_TEST.txt`).
- Read-only empty-output audit (3 finders + 3 verifiers, `receipts/EMPTY_OUTPUT_AUDIT_2026-10-12.json`): zero sidewalks is handled (sealed `geocity_bank_workflow.py:305-311` drops an output with 0 visible faces, as KY did for empty vegetation/street_details); the sidewalk material lane still finds its scoped catalog row (any_validated_area); 3 buildings cannot become an empty buildings output (no whole-native row fits; pads assemble or keep shells). Expected outputs: Landscape, road_surfaces, buildings, instancer (+ street_details only if proxy poles remain). Terrain note: DSM max 255.82 m vs the landscape layer max 255.99 m (0.18 m margin, no clipping; an area above 256 m would clip).
- Base: Karmei Yosef 4 km v002 (b1cc6fab, already trunk 12 / trunk_link 7 / primary 10 / primary_link 7 m without sidewalks, no tree blockouts). Edits in `hda_ew_v001_edits.py` (shared by build + verify): pole-omission tuple + El Wahat id (2 places); NO_SIDEWALK_CLASSES + service, unclassified; construction -> declared class (ledger `road_construction_mapped_json`); `_ew_trim_to_box` per way, area + 100 m (ledger `road_trimmed_json`); assembly-contract default from PROFILE_CANDIDATE.json.
- `build_hda_4km_ew_v001.py` (hython, no cook) -> sha 56284287; `verify_hda_4km_ew_v001.py`: module = base + exactly the edits (diff -3/+30), only DialogScript changed besides the module, contract default = profile, grid 4033, KY v002 unchanged (KY revision folder hashes identical before/after).
- After the run, check: `road_construction_mapped_json` = ["1175781900:construction->service"], `road_trimmed_json` lists the 6 long ways, catalog_road_material class faces include service, and look at the two junctions of the construction road (x -912..-747 m, z -396..-218 m).

## 3d. Section 4 — native area (done 06:58Z)

- Create editor PID 19344 (06:54Z, ports 19860/18100/8020), only editor. `create_area.py` attempt 1 saved the HDA asset and the ground MI (MW_SnowWorldPosition 1e6 copied, parent shared M_GeoCityAuto) but stopped at its sun check: in this flow `CorrectedElevation` reads **180 + elevation** after `UpdateSky` (191.85 at 07:00), so the self-referenced expected vector was inverted; the light itself was right. Record `NATIVE_AREA_CREATION_ATTEMPT1.json`.
- `Tools/create_area_finish.py` on the same editor: checks the sky against an independent NOAA solar model (not the blueprint's own properties): angle error 0.41 / 0.44 / 0.41 deg at 07:00 / 12:00 / 17:00, 07:00 light forward (-0.943, -0.262, -0.205) = morning sun in +X (east), north arrow -Y; then map-only named save (sha b6670f82). `new_level()` had already written the empty 8.8 KB level file in attempt 1 (expected). Protected packages unchanged. `create_area.py`'s own sun check still has the CorrectedElevation bug; reuse `create_area_finish.py`'s NOAA check for future areas (playbook note).
- `gc_probe` ok; `promote_profile.py` -> AREA_PROFILE.json sha 96297660; `quit_clean` (0 saves), records released, 0 editors live.

## 3e. Section 5 — run 1 (live)

- Run editor PID 20356 launched 07:00:35Z on the map (sha b6670f82; forensic copy `Before/L_ElWahatEgypt_29176036_29602273_4km_b6670f82.umap`), only editor. `start_area_generation.py` (expected_digest 12552e14, profile sha 96297660): GENERATION_STARTED 07:01:01Z, lease `OWNER=GEOCITY_MENU task=GENERATE_CURRENT_AREA assigned_editor_PID=20356`, official Engine connected, timeout 14,400 s. Waiting with `wait_lease.py --pid 20356` (log `Logs/wait_lease_ew4_run1.log`).
- Prepared offline during the run (no editor contact): split tools for El Wahat. `split_buildings.py` / `split_shells.py` take a required target `main` | `clone` | `clone_v2`; shells go to `<map folder>/Buildings_v2/Shells/`; leftover triangles go to `Bldg_unassigned`; `split_shells.py` skips cleanly if there is no merged shell mesh. `Buildings_v2/compact_buildings_v2.py` adds OSM footprints for every unsupported building (same local frame) and no longer fails when nothing assembled. Reference KY files re-checked: 116/116 unchanged.

- **Result (08:47:59Z, 1 h 47 min, released baked_saved_verified):** map sha 54431c44 (90.0 MB), 69 actors (67 baked), 1 Landscape, 12,784 instances = 12,072 small props + 240 street poles + 240 street props + 232 building modules. Buildings: 3 assembled (0 whole native, 0 unsupported). Sidewalks: 0 faces (no output, as designed). Roads visible faces 477,340 (trunk 293,902 / primary 129,155 / unclassified 36,142 / service 15,011 / trunk_link 3,130; tracks as road-bed paint only). Construction way 1175781900 built as service 4 m. Trimming worked: 13,072 Labs road triangles (KY 192,109). Poles: 246 generated, 240 native, 6 failed omitted, 0 proxies. Terrain support: max local correction 0.24 m. Run time was the same as KY despite 8x less road geometry: the small-prop spacing stage (12k requests over open sand) likely dominates.
- Read-back (same editor): counts match the run state; 2 unreferenced Cook packages dirty -> discarded by `quit_clean` (allow_cook_leftovers, 0 saves). Captures `receipts/Captures/ew4_run1_{a,b}_*.png` (cameras `cameras_ew4.json`: wide_southwest, station_oblique, station_close, house_service, construction_junction, trunk_street) + `ew4_run1_wide/oblique.png`.
- **Look (for Aviv):** the 3 OSM buildings (fuel-station canopy `building=roof`, café `commercial`, a 12.8 x 3.6 m shed) became 4-5 storey mediterranean_urban apartment blocks (no height tags; bank style set); roads use the grey paving material; ~12k small props are scattered over the open sand; a few green grass patches; the far view shows the pale tiled ground (satellite colour is section 6).

- **Fresh reopen** (verify editor PID 4904, 08:50Z): same sha 54431c44, 69 actors, 1 Landscape, 12,784 instances, nothing dirty. Sky kept NorthOffset -90 (`SunElevation` 53.2 = true elevation; `CorrectedElevation` 233.2 = 180 + elevation). Landscape Z 236.84-255.80 m (ceiling 255.99 m: no clipping). Buildings: seeded heights (no OSM tags) 16 / 19.2 / 16 m = 5 / 6 / 5 storeys of the native_modular_courtyard kit. Small props: grills, food crates, tyres, trash bags, gas cylinders, carts, rubble piles (~1,200 each) over the whole area.

## 3f. After run 1 — Aviv's look choices (09:00Z) and map steps

- Choices (buttons): buildings -> Astra models of the real station + café; small props -> near roads/station only; roads -> asphalt; split -> main map.
- One object per building on the MAIN map (editor PID 4904): `Buildings_v2/compact_buildings_v2.py` (3 buildings, 232 modules, 0 unsupported) -> `split_buildings.py` target main: plan 232/232 matched (max 0.008 cm), build 3 actors, fix_attach (232 positions, worst 0.0 cm), remove 232, verify ok -> map save f69e9108 -> `split_shells.py` analyze 2,312 tris (2,068 inside, 244 near, 0 unassigned) -> build 3 shells (`BankIntegration_v015/Buildings_v2/Shells/SM_Shell_<osm>`, save_prefix) -> map c9812bc8 -> remove merged shell actor (bake asset untouched) -> verify 2,312 = 2,312 -> fix_attach -> map **9f8501f1**. New tool `Tools/save_main_map.py` (map-only named save of the main map, receipts `MAIN_SAVE_<label>.json`). Map grew 90 -> 130 MB on the first editor re-save (KY showed the same growth).
- Props: `Tools/props_near_roads_plan.py` (offline; 30 m from road edge = OSM centreline + half class width, or from a footprint) -> keep 615 / remove 11,457 -> `Tools/props_trim.py` match 12,072/12,072 exact, remove 11,457 (transforms in `receipts/PROPS_REMOVED.json`), verify per mesh ok -> map **be272127** (1,324 instances left: 615 small props, 240 poles, 240 street props, 229 building modules).
- Roads: `Tools/road_asphalt.py` (map-level override on the road actor, slot 0) + `Tools/road_asphalt_mi.py` (area-owned `MI_Road_Asphalt_EW`, copy of AsphaltMat `MI_AsphaltMat_Inst3`). Candidates tried (unsaved): AsphaltMat Inst1 (pale), RealisticDesertPack MI_Road_1 (lane stripes across), CitySample freeway (pink), RoadBLD GeoCity worn (black), RoadBLD default / CitySample raw (light gravel), ModularCourtyard blend (glossy; its dry copy `MI_Road_Asphalt_EW_v2` turned watery: vertex-paint layered master), AsphaltMat Inst3 (dark; area copy `MI_Road_Asphalt_EW` with Tile U/V 5 -> 0.05 did not change the pattern).
- **Half-precision road UVs: CONFIRMED (11:00Z), after a wrong interim refutation.** Road UVs are world metres (-2000..+2000) and the baked road mesh stored them at half precision (`use_full_precision_u_vs` false), so vertex UVs snap to 0.5-1 m and individual triangles show the texture squashed/stretched (smeared streaks, uniform triangles up close). First test (~09:35Z) used the AsphaltMat texture, whose own spot pattern hid the difference, so I wrongly called it refuted and reloaded the mesh. Aviv then reported the stochastic road "messed up and jumbled" up close (his screenshot: streaks + white triangles). Same-camera test (`receipts/Captures/diag_before_lane_down.png` vs `diag_after_lane_down.png`): full-precision UVs + full rebuild (`road_uv_fix.py` + `road_uv_rebuild.py`) removes the artifacts. Saved the road bake mesh (Aviv had approved 'Fix this area's mesh'): sha af19ea3d -> **14676be6** (backup `Before/ElWahatEgypt_..._road_surfaces_af19ea3d.uasset`). A regeneration re-bakes the mesh at half precision until the bake/generator is fixed (Aviv declined a manager brief for now). Likely affects every area's baked roads (KY grey paving).

- Aviv on the comparison (10:10Z): "Both look bad because of their tiling. Can you try to use stochastic texturing? Or maybe increase their tile size / texture resolution?"; discard both test MIs (done: `Tools/discard_scratch_mis.py`, memory only). Map saved without override: e4932ccf.
- Road material plan (`Tools/build_road_material.py`): new master `M_RoadAsphalt_EW_v001` (duplicate StarterContent M_Basic_Wall + rebuild, the 2026-10-08 proven method): UV0 (metres) / `TileSizeM` (3) -> engine `TextureVariation` (stochastic offsets from a linear-grayscale heightmap; rotation off) -> `Shifted UVs` sample the 4K ModularCourtyard Asphalt_cracked set (basecolor, normal, roughness, AO, height); x macro variation (engine T_Default_MacroVariation at `MacroSizeM` 40, `MacroDark`/`MacroBright`), lerp to `DustColor` by `DustAmount`, `Brightness`, `NormalStrength`, `RoughnessMult`. Tuning later only through an area MI. Quit the editor right after the build.
- Built (editor PID 23988, dry run then build): 27 nodes / 27 connections, TextureVariation pins confirmed (inputs Heightmap, UVs, Variation Scale, Variation Levels, Heightmap Influence, Mask Channel, Use Dither, Random Rotation and Scale, HQ Edge Comparison; output Shifted UVs), saved, nothing dirty -> quit_clean (crash rule).
- Applied (editor PID 31544, fresh on e4932ccf): `Tools/road_mi.py` -> `Materials/MI_RoadAsphalt_EW_v001` (TileSizeM 3, MacroSizeM 40, MacroDark 0.78, MacroBright 1.1, DustAmount 0.08, **Brightness 0.32**; TextureVariation defaults: Random Offset Variation 8, Dithering 0.2, Random Scale Variation -0.5) on the road actor (map-level override, slot 0). Tiling gone at every distance, no seams close up. Saved MI (save_prefix) + map **028a7ae1**; gc ok. Sheet `receipts/Captures/ROADS_stochastic_before_after.png` sent to Aviv.

## 3g. Astra brief — station, shop, shed (written 10:40Z)

- OSM facts (`receipts/STATION_BUILDINGS_OSM.json`): way 1327565325 `amenity=fuel building=roof` "وطنية / Watanya" 24.75 x 9.56 m, bearing 42.5; 1327565326 `building=commercial shop=convenience` "Timeout" 22.55 x 11.16 m, 41.4; 953803842 `building=yes` 12.84 x 3.59 m, 43.9 (240 m SW of the station). Canopy ~23 m SE of the shop (shop front faces SE).
- Aviv: real Wataniya look (logos and names as photographed).
- Site folder `Staging/ElWahatStation_2026-10-12/`: `HANDOFF_ASTRA_StationCafe_v001.md` (paste-ready message at the end), `References/` (captures of the generated blocks, `STATION_PLAN_OSM.svg`, footprints JSON), Astra delivers to `AstraModels/Revisions/StationCafe_v001/`. Placement later: hide/remove the 3 `Bldg_<osm>` actors only after Aviv confirms, place the Astra assets by footprint centre + yaw (bearing).

## 3h. Section 6 — satellite ground (done 10:47Z)

- `Zones/zones_data.py` (date 2026-10-12): OSM land use 0 features; Sentinel-2 L2A recent S2C_35RQN_20260927 (0% cloud in area), spring S2A_35RQN_20260512; output `SourceData/ElWahatEgypt_29176036_29602273_4km/zones/20261012T104030Z/`.
- Desert reflectance: red p50 0.389 / p99.9 0.48; NDVI max 0.18 (nothing > 0.2). `classify_zones.py` (guard added for an empty land-use layer): bright 95.7%, bare_field 4.3%; all PCG masks empty (no vegetation zones). `make_textures.py`: stretch **/5000** (was /2500, which clipped 99.8% to white) -> mean sRGB (199, 143, 85), 0.005% clipped.
- OSM vs Sentinel-2 alignment measured by road correlation: within 2 m (1 px). No offset.
- In editor 31544: map re-saved first (the road mesh rebuild had dirtied it): **739b5c23**. `Tools/build_ground_satellite.py`: imported `Materials/Zones/T_EW4_Satellite` + `T_EW4_Zones`, area copy `Materials/M_GeoCityAuto_EW4` of the shared master with the satellite blend (Sat_Blend 0.8, Sat_DetailMid 0.35), area MI reparented; shared master unchanged (sha 46076bce); then quit_clean (crash rule).
- Fresh reopen (PID 19768): sha 739b5c23, 71 actors, 1 Landscape, 1,324 instances, nothing dirty, NorthOffset -90, road full-precision UVs, landscape MI = area MI. Near views: real sandy-orange desert. High views (600 m / 1,500 m) showed a ~150-200 m checker from the MW auto-material; fixed by MI parameters only (`Tools/set_mi_params.py`): `MW_LandscapeWorldUVSizeFar` 8192 -> 40000 and `MW_VariationWorldUVSize` 64 -> 512 (sheets `receipts/Captures/ground_tiling_test*.png`). MI saved (sha **74b03a0c**); map unchanged 739b5c23; quit clean.

- Final fresh reopen (PID 31076): sha 739b5c23, 71 actors, 1 Landscape, 1,324 instances, nothing dirty; ground MI params persisted (Far 40000, Variation 512, Sat_Blend 0.8, snow 1e6); quit clean, 0 editors live. KY reference files 116/116 unchanged.

- Far-edge check (editor PID 31864, quit clean, 0 saves): road UVs clean at x -1,747 m / y -815 m; **new defect** there: stair-stepped holes in the trunk road mesh (sand visible, dark cut edge), near where the two carriageways run close; 7 top-down views along the trunk show only this one place (`receipts/Captures/faredge_*.png`, `trunk_top_sheet.png`). Cause not investigated. All 8 ParallelEditors records of this session released.

## 3i. Aviv's answers (11:05Z) and follow-up

- Playbook: **update** -> section 10c "Lessons from El Wahat" + a pointer in 4.5 added to `Staging/Playbooks/NEW_ENVIRONMENT_PLAYBOOK.md` (no Karmei Yosef file changed).
- Road holes: **investigate now** -> cause found read-only (see RESULT.md "Far-edge checks"): `cook_road_surfaces` labels faces by nearest centreline and `track`/`path` faces are deleted (paint only), so drivable surface nearest a track is cut. 3 sites in El Wahat, all confirmed by captures (`receipts/Captures/ROAD_HOLES_track_sites.png`; capture editor PID 23644 quit clean, 0 saves). Fix approach awaits Aviv.
- Vegetation: **skip**.
- Old copies: **delete** -> `build_hda_4km.py` (6efbcb1e), `build_hda_4km_v002.py` (35921b09), `verify_hda_4km_v002.py` (af228ba6) removed from the El Wahat task folder only (KY originals intact).

## 3j. v002 preparation (offline, in progress)

- Planning workflow (4 agents incl. adversarial check) -> `receipts/V002_PLAN_2026-10-12.json`. Key facts: the menu regenerates (reusing the v001 actor, ignoring profile['hda']) whenever a HoudiniAssetActor exists, so the v001 actor must be deleted; deleting the old Landscape up front avoids the KY 'Duplicate Landscapes' failure (instantiate renames the old landscape `_old_0`); the 3 `Bldg_` actors are in no ledger and would fail the run's post-bake overlap check, so they must go; the road actor + 64 bank_instances are retired by the sealed run via the run-1 ledger (new actors get `_1`); the HDA parm `route_surface_materials_json` is always overwritten with the profile value '{}' (geocity_bank_workflow.py:521), so the track material is a module default; the road mesh will have 2 material slots in no fixed order.
- Aviv (buttons ~13:20Z): **delete those 5** actors; tracks **Sandy gravel** (Poly Haven sandy_gravel_02 on the stochastic master, `MI_RoadTrack_EW_v001`); **all other editors closed** until the run ends.
- `hda_ew_v002_edits.py` (frozen spec, generated from the exact v001 text): L drivable precedence (helpers + cook_road_surfaces + detail `road_drivable_precedence_json`), L2 (receipt `drivable_precedence`), T (module default track = TRACK_MI). Build `build_hda_4km_ew_v002.py` (first attempt stopped before writing: v001 had to be installed to read its parm template) -> `revisions/20261012_ElWahatEgypt_4km/GeoCity_city_v015_CurrentBank_4km_EW_v002.hdalc` **sha cb4ae95c**, type `15.0_4km_elwahategypt_v002`; `verify_hda_4km_ew_v002.py`: diff -1/+52, no other section changed, parm defaults equal v001, helper synthetic test ok, v001 + KY v002 unchanged. Record `HDA_SOURCE_V002.json`.
- Tool patches (workflow, 3 writers on disjoint files + reviewer): hda_v002_prepare (import / remove_actor / clear_for_instantiate), switch_profile_v002, start_area_generation (expected_action/hda/track_mi), wait_lease (--log, exit 5 on 'GeoCity failed_'), recover_v002, road_asphalt (by mesh, by slot material), split_shells (shell_folder), new track_mi.
- Backup `Before/regen_v002_20261012T140503Z/` (37 files, 158 MB, SHA256SUMS.txt): area content except Cook, AREA_PROFILE, ledgers, receipts.

## 3k. v002 prepare (done 14:50Z, editor PID 26136, quit clean 0 saves)

- Review fixes applied to the run tools (receipts/TOOLS_ADAPTATION.json pass v002_review_fixes): start_area_generation requires all expected_* ARGS for the El Wahat instantiate run, a present run-1 ledger, outside-ledger classes == [BP_EnvironmentSky_C], HDA asset class, track MI not asphalt textures; switch_profile only after CLEAR_BEFORE_V002 CLEARED_SAVED on the current map; prepare asserts HoudiniAssetActor_0 path and keeps superseded receipts; recover/split_shells record before destroy; wait_lease whole-PID match + release race. KY reference files 116/116 unchanged.
- `MI_RoadTrack_EW_v001` created and saved (uasset c317b232): sandy_gravel_02 diff/normal, T_White rough/AO, Sand_height; TileSizeM 2.75, DustAmount 0.35, Brightness 1.1, NormalStrength 0.8, RoughnessMult 0.9, DustColor (0.571, 0.275, 0.091). Measured: the MaterialEditingLibrary MI setters return False in this build even when the value is set; track_mi.py now relies on its readback (pass track_mi_texture_setter_return).
- v002 HDA imported `.../HDA/GeoCity_city_v015_CurrentBank_4km_EW_v002` (uasset 2773d46c).
- Deleted (Aviv approved the 5, all recorded first): HoudiniAssetActor_0 (receipts/HDA_V001_ACTOR_BEFORE_V002.json, 41 parameters) -> map 6ff77515; landscape + Bldg_1327565325/1327565326/953803842 (receipts/CLEAR_BEFORE_V002.json) -> **map d6c52ddf**, 66 actors (64 bank_instances + road SMA + sky), nothing dirty.
- Profile `AREA_PROFILE.json` switched hda -> EW_v002: 96297660 -> **890e543a** (receipts/PROFILE_SWITCH_V002.json; backup AREA_PROFILE_before_v002.json).

## 3l. v002 run + redo (done 17:00Z)

- Run PID 40028: lease 14:50:46Z -> OWNER=NONE released_phase=**baked_saved_verified** 16:45:16Z (1 h 54 min); map ed2ff8d1, 69 actors. Ledger (LAST_SUCCESSFUL cdeb9496): profile 890e543a, 67 baked, 65 old actors retired (road + 64 bank_instances), 1 Landscape, 12,784 instances. Road material stats: track visible faces **45,295** (was 0, mask-only), drivable precedence reassigned **238** faces (track->primary 204, track->trunk 34), trunk 294,031 / primary 133,306 (>= run 1), route track = MI_RoadTrack_EW_v001. Captures `receipts/Captures/v002_tracksites_*`: the 3 hole sites are continuous.
- Quit clean (2 unreferenced Cook leftovers discarded, 0 saves).
- Redo editor PID 15712: compact_buildings_v2 (232 modules, footprints unchanged, receipt 7dd28f03) -> split_buildings main 232/232, worst 0.0 cm -> map 1dd8572c -> split_shells Shells_v002 (2,312 tris; `Buildings_v2/Shells_v002/SM_Shell_*` saved; merged actor recorded in receipts/MAIN_MERGED_BUILDINGS_REMOVED_20261012T164900Z.json then removed) -> map fec004c0 -> props plan keep 615 / remove 11,457, trim verified -> map ace803b1 -> road UV full precision + rebuild (2 slots kept; mesh 79f3682e -> **c2095747**, backup in Before/) -> map 956fb201 -> road_asphalt set on slot 0 only (track slot 1 keeps MI_RoadTrack) -> map **d6405195**. Quit clean, 0 saves.
- Track look (measured): UVs 1.0/m like asphalt, textures 4K; sandy_gravel_02 is a fine-grain sand, so the track reads as a smooth pale-orange band beyond a few metres (`v002_track_close_*`). Open look choice for Aviv (MI values only, no graph edit).
- Station tool `Tools/station_import.py` (new, Opus review applied: Interchange UCX import, ignore-list ground trace, MI dirty after binding, compile-error check, Nanite off, triangle/collision checks).

## 3m. Astra StationCafe v001 import + placement (done 17:00Z)

- Fresh reopen of d6405195 (PID 40672): sha unchanged, nothing dirty, 1 Landscape, 3 Bldg_, ground MI 74b03a0c, sky NorthOffset -90 (noon sun azimuth 184.9).
- `Tools/station_import.py` steps: check (16 FBX hashes ok, 19 used material sets, 57 PNGs) -> textures (57 under `/Game/Project/Areas/ElWahatEgypt_.../Station/StationCafe_v001/Textures`, normals green-flipped, ORM masks, non-VT) -> master `.../Station/Materials/M_EW_Station_Opaque` (BaseColor/Normal/ORM; quit after the graph edit) -> PID 19416: materials (19 MI_EW_*, readback) -> meshes (8, non-Nanite, FBX normals, authored LOD3 as LOD1; triangles exact vs manifest; UCX convex = manifest, 0 auto primitives; first attempt refused on a wrong simple-collision check, fixed, the unsaved slab reused via accept_in_memory) -> lod_screen (LOD1 at 0.1; auto value was 0.75) -> place dry run (canopy pad 24,483.6 cm, shop pad 24,508.6 cm, forecourt ground span 53.7 cm; shop moved to its own pad) -> place (15 actors, accept_group_span_cm 54) -> verify (mesh/xy/yaw all match) -> map **6e812bd7**.
- Measured in this build: `get_simple_collision_count` excludes convex hulls; `bAutoComputeLODScreenSize` is not a Python property (SetLodScreenSizes + readback); Interchange FBX import needs auto_generate_collision True to keep UCX.
- Captures `receipts/Captures/station_with_blocks_*` and `station_blocks_hidden_*` (blocks hidden in the editor only, never saved). Slab 2 (canopy frame Y 16) lies mostly under the OSM service road between canopy and shop; a white corner shows.

## 3n. Aviv answers (~19:25Z) and final state

- Buttons: **Remove all 3** generated blocks, **Remove slab 2**, track **Darker, less orange**.
- `Tools/remove_actors.py` (new; records first, x-mode receipt `receipts/REMOVED_ACTORS_20261012T192914Z.json`): Bldg_1327565325, Bldg_1327565326, Bldg_953803842, EW_Station_Forecourt_Slab_2 removed. `set_mi_params.py`: MI_RoadTrack_EW_v001 Brightness 1.1->0.9, DustAmount 0.35->0.15, saved by name. Map **fc89bf00**.
- Final fresh reopen PID 9308: sha unchanged, nothing dirty, 82 actors, 1 Landscape, 1,095 instances; station verify reported 14 of 15 planned (its ok flag is false because slab 2 was removed by Aviv's decision); all 14 present match on mesh, xy and yaw; LOD screen sizes [1.0, 0.1] persisted; UCX convex counts kept. Quit clean, 0 editors.
- New tools this stage: station_import.py, station_lod_probe.py, remove_actors.py, temp_hide.py, track_probe.py, texture_export_probe.py (receipts/TOOLS_ADAPTATION.json). The El Wahat copy of lod_probe.py was overwritten by mistake and restored byte-identical from the KY original (KY 116/116 unchanged).

## 3o. After any future regeneration (written down only; no generator change)

- The 3 OSM buildings are still in the source package and EW v002 still assembles them: a regeneration re-bakes the 5-storey blocks on top of the station. After the split, remove the 3 regenerated `Bldg_` blocks again (record first, `Tools/remove_actors.py`) under Aviv's standing "Astra models replace them" decision; re-confirm with Aviv the first time.
- An instantiate run over this map must list the 14 station StaticMeshActors in `expected_outside_ledger_classes` (they are outside the run ledger and survive the scoped replacement), i.e. BP_EnvironmentSky_C + 14 x StaticMeshActor.
- Redo after a regeneration: compact_buildings_v2 -> split_buildings -> split_shells (new shell folder) -> remove the 3 blocks -> props trim -> road_uv_fix/rebuild + Bake save -> road_asphalt set -> track MI is unchanged (module default).

## 4. Next steps

0. **Approved (Aviv ~11:15Z): generator revision EW v002 + one regeneration**, with (L) the lineage fix (a face inside a drivable half-width keeps the drivable class) and (T) tracks built as 3 m dirt surfaces (area dirt MI on the stochastic master) instead of being deleted. Explained to Aviv: tracks were paint-only by the shared generator's design (route material '' for track/path). Read-only planning workflow running (regeneration procedure incl. the KY 'Duplicate Landscapes' lesson, Bldg_ actors to remove first, profile switch; HDA edits; dirt texture set). Then: build/verify v002, prepare map, run (only editor), redo split / props trim / road UV fix / road + track materials, verify.
1. **Astra delivered StationCafe v001 (~11:30Z)**: `Staging/ElWahatStation_2026-10-12/AstraModels/Revisions/StationCafe_v001/` (INDEX.html, HANDOFF_CLAUDE.md, MANIFEST.json, Reports/PLACEMENTS.json): 8 assets (Wataniya canopy 24.75 x 9.56 m, pump island A x3, forecourt slab 32 x 16 m x2, Timeout shop 22.55 x 11.16 m two-tier ~7.3 m, shed, price pylon 7.5 m, trash bin, fire extinguisher), 16 FBX (LOD0 + authored LOD3), 72 PBR maps (BaseColor sRGB, Normal OpenGL, ORM), UCX collision; pivot = footprint centre on the ground, -0.15 m skirt; canopy-local X along bearing 42.5. Import/placement AFTER the v002 regeneration and split. Plan: area-owned opaque master (duplicate M_Basic_Wall + rebuild, quit after) + MIs per material set; meshes with LOD3 as the last LOD; place by OSM footprint centres + yaw (UE yaw = atan2(-cos b, sin b) for bearing b, i.e. -47.5 deg for 42.5), pumps/slab/props per PLACEMENTS.json; hide/remove the 3 `Bldg_<osm>` only after Aviv confirms. Original step text: Aviv passes `Staging/ElWahatStation_2026-10-12/HANDOFF_ASTRA_StationCafe_v001.md` to Astra. On delivery: import (`apply_astra_rev.py` pattern) under the area folder, place each asset at its OSM footprint centre with yaw from the bearing (canopy 42.5, shop 41.4, shed 43.9; X east / Y south frame), ground-fit, Static chains; remove or hide the 3 `Bldg_<osm>` actors only after Aviv confirms; save; fresh reopen.
2. Section 7 vegetation: no data-driven zones (NDVI max 0.18); only if Aviv wants desert shrubs.
3. Section 10: play-mode timing / standalone export only if Aviv asks.
4. Generator/bake: road UVs at full precision (all areas) — Aviv declined a manager brief for now.
5. Playbook lessons to propose (not applied): see `NewArea_.../RESULT.md` open point 4.

## 5. Delete-on-confirmation list

Nothing pending. Done: the three stale KY template copies (11:05Z); the 5 actors before the v002 run (~13:20Z); the 3 Bldg_ blocks + EW_Station_Forecourt_Slab_2 (~19:29Z); 2026-10-13 (Aviv buttons): 13 packages / 175.5 MB with 0 referencers (v001 Cook folder, Shells, Shells_v002, v001 HDA asset) via `Tools/delete_assets.py` (long-path safe), backup `Before/deleted_20261012T221455Z/`, record `receipts/DELETED_ASSETS_20261012T221455Z.json`; fresh reopen after: fc89bf00 unchanged, nothing dirty. Backups in `Before/` are kept.
