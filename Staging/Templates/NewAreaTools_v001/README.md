# NewAreaTools_v001 - the template Tools folder for a new area

Created 2026-10-19 per `Docs/GOVERNANCE_RECORD.md` item 16 (RC-71): "build one template from everything relevant in both the
El Wahat and the Karmei Yosef tool sets, with the NorthOffset defect fixed and the _aviv clients excluded". The file list,
sources and fixes follow `Environmentpipeline_Audit/Audit16_2026-10-17_1346Z/Repairs/Decisions_2026-10-18/TEMPLATE_FOLDER_PROPOSED_LIST.md`
(155 rows: 25 include, 61 include-after-fix, 68 exclude, 1 new). Maintenance owner: Aviv, through the agent he
assigns (RC-69). Evidence of the build: `Environmentpipeline_Audit/Audit16_2026-10-17_1346Z/Repairs/Executed_2026-10-19/TEMPLATE/`.

## What this folder is

The tools that build a new real-world area (playbook `Staging/Playbooks/NEW_ENVIRONMENT_PLAYBOOK.md`, skill
`.claude/skills/new-environment/SKILL.md`), in the layout of a task folder: `Tools/`, `Zones/`, `Buildings_v2/` and the
area-root scripts. Generation, after-generation and per-building tools come from El Wahat (it ran the newest generation);
the PCG, vegetation and farm-ground tools come from Karmei Yosef (El Wahat never made a PCG clone, so its copies never ran).

**Never run anything in place.** Every tool refuses unless it sits in `Staging/<TASK_FOLDER>/` with a filled
`Tools/area_constants.py` (the launcher and `wait_lease.py` / `export_env.py` also check the folder depth).

## How to use

1. Copy the whole folder to `Staging/NewArea_<Name>_<lat8>_<lon8>_<size>_<YYYY-MM-DD>/` (playbook 1.2).
2. Set every value in the "SET PER AREA" block of `Tools/area_constants.py`: name, centre, size, area id, task date, short
   prefix, sky date / time zone / check hours, three free editor ports, ground MI copy source (+ sha), profile template
   (+ row count, digest, release, registry sha), generator base (+ shas, revision folder, version), Sentinel-2 windows,
   satellite stretch, zone and tree thresholds, protected packages. Everything else (map, clone, graph, mask and material
   names, sizes) is derived there. Check with `python -I -B Tools/area_constants.py --json`.
3. Write `ASSIGNMENT.json` with `operator_session_id` (the launcher and `switch_profile_hda.py` read it) and
   `profile_decisions` (this area's [D] answers; `prepare_profile.py` lists the required keys).
4. Run the steps of the playbook. In-editor tools run only through `Tools/ky_client.py`, which passes `script_file`; the
   tools find this task's `area_constants.py` through it. Clone suffixes and graph versions are explicit, required ARGS.
5. Generator: `hython build_hda.py "<Aviv's words>"`, then `verify_hda.py`; add the area's own module edits to
   `hda_edits.py` EXTRA_EDITS (and re-measure EXPECTED_DIFF offline) when its [D] answers need them.

## Files and sources

Source key: EW = El Wahat, KY = Karmei Yosef 4 km task folder (paths relative to the source folder; # = row of the list).
Fix codes: G1 task folder from the file's own location (in the editor: from `ARGS['script_file']`), G2 area values from
`area_constants.py`, G3 explicit clone suffix, G4 short prefix, G5 sizes from the half-extent, G6 no operator ids or dated
authority strings ("Template v001" header), G7 World Partition trial removed.

| template file | source | # | status | fixes applied |
|---|---|---:|---|---|
| `Buildings_v2/compact_buildings_v2.py` | EW `Buildings_v2/compact_buildings_v2.py` | 37 | copied, fixed | G6 header (no operator id / dated authority) |
| `Tools/apply_astra_rev.py` | KY `Tools/apply_astra_rev.py` | 85 | copied, fixed | revisions root, site name (folder + M_/MI_ prefix) and the two masters are ARGS; TRIAL from constants; VF3 renamed DEST; G6 header (no operator id / dated authority) |
| `Tools/area_mi_copy.py` | EW `Tools/area_mi_copy.py` | 58 | copied, fixed | area Materials folder from constants; G6 header (no operator id / dated authority) |
| `Tools/audit_visibility.py` | KY `Tools/audit_visibility.py` | 83 | copied, fixed | G1; external-actors check scoped to the loaded map; G6 header (no operator id / dated authority) |
| `Tools/bldg_inspect.py` | EW `Tools/bldg_inspect.py` | 42 | copied unchanged |  |
| `Tools/bldg_scan.py` | EW `Tools/bldg_scan.py` | 41 | copied unchanged |  |
| `Tools/build_ground_satellite.py` | EW `Tools/build_ground_satellite.py` | 71 | copied, fixed | G1; names (G4) and origin/size (G5) from constants; node guard kept; G6 header (no operator id / dated authority) |
| `Tools/build_road_material.py` | EW `Tools/build_road_material.py` | 48 | copied, fixed | master name and root from constants (G4); G6 header (no operator id / dated authority) |
| `Tools/build_zone_pcg.py` | KY `Tools/build_zone_pcg.py` | 78 | copied, fixed | G3 clone_suffix required; G4 graph, mask prefix, volume label; G5 scale; order note (pack originals vs never-vanish copies); G6 header (no operator id / dated authority) |
| `Tools/clone_v2.py` | KY `Tools/clone_v2.py` | 77 | copied, fixed | MAIN/OLD/NEW from constants with explicit required suffixes (G3); authority from ARGS; G6 header (no operator id / dated authority) |
| `Tools/create_area.py` | EW `Tools/create_area.py` | 30 | copied, fixed | NorthOffset fix: -90 kept per instance (no class default); faulty sun_check replaced by the NOAA model of create_area_finish.py (noaa(), asserts < 1.5 deg, north arrow -Y, first hour light -X); raw CorrectedElevation not recorded; LAT/LON/TZ/date/check hours from constants; map-prefix and HDA revision asserts from constants; protected list from PROTECTED_CONTENT_FILES; log tag; G6 |
| `Tools/deps_probe.py` | EW `Tools/deps_probe.py` | 111 | copied, fixed | G1; G6 header (no operator id / dated authority) |
| `Tools/dirty_classes.py` | EW `Tools/dirty_classes.py` | 124 | copied unchanged |  |
| `Tools/dz_probe.py` | EW `Tools/dz_probe.py` | 108 | copied unchanged |  |
| `Tools/exit_failed_area_run.py` | EW `Tools/exit_failed_area_run.py` | 7 | copied, fixed | G1; docstring (RG4 #22): Aviv or the agent he assigns appends the OWNER=NONE line (no manager); G6 header (no operator id / dated authority) |
| `Tools/export_env.py` | KY `Tools/export_env.py` | 112 | copied, fixed | G1 + constants; map = the single DEPS root under this area; LAYER_FILES found by the profile HDA name + landscape name; ENGINE_ASSOCIATION a build argument; README/description texts neutral; G6 header (no operator id / dated authority) |
| `Tools/farm_real_ground.py` | KY `Tools/farm_real_ground.py` | 74 | copied, fixed | G3 clone_suffix required; G2/G4 names; Paz Farm names -> ARGS.site, PAINTED_MI -> ARGS.painted_mi; find_sat graph-chain precondition documented; G6 header (no operator id / dated authority) |
| `Tools/gc_probe.py` | EW `Tools/gc_probe.py` | 9 | copied unchanged |  |
| `Tools/ground_z.py` | EW `Tools/ground_z.py` | 107 | copied unchanged |  |
| `Tools/hda_revision_prepare.py` | EW `Tools/hda_v002_prepare.py` | 32 | copied, fixed | renamed from hda_v002_prepare.py; hda_edits loaded by path; HDA names from constants; receipts versioned; El Wahat run facts (67 ledger actors, 64 bank_instances, 3 Bldg ids, 66 kept) became ARGS; authority from ARGS; G6 |
| `Tools/inspect_ground_master.py` | EW `Tools/inspect_ground_master.py` | 72 | copied, fixed | MI path from constants; G6 header (no operator id / dated authority) |
| `Tools/ky_capture.py` | EW `Tools/ky_capture.py` | 3 | copied, fixed | PORT = NATIVE_PORT from area_constants.py; garbled docstring fixed; ASSIGNMENT_RUN native-endpoint check added; clientInfo; G6 header (no operator id / dated authority) |
| `Tools/ky_client.py` | EW `Tools/ky_client.py` | 2 | copied, fixed | PORT = COPILOT_PORT from area_constants.py; usage text names ky_client.py; clientInfo from AREA_ID; G6 header (no operator id / dated authority) |
| `Tools/launch_area_editor.ps1` | EW `Tools/launch_area_editor.ps1` | 1 | copied, fixed | G1 task = parent of the script folder (refuses Staging/Templates); G2 area id, prefixes, profile path, MAIN map and the 3 ports read from area_constants.py --json; operator id from ASSIGNMENT.json; G6; G7 wptrial purpose and WP mirrors removed; pcg needs -Map; read scope: ground MI source folder from constants (EW had the KY 2 km Materials scope, not Lebanon) |
| `Tools/list_dirty.py` | EW `Tools/list_dirty.py` | 123 | copied unchanged |  |
| `Tools/lod_api.py` | EW `Tools/lod_api.py` | 91 | copied unchanged |  |
| `Tools/lod_probe.py` | EW `Tools/lod_probe.py` | 90 | copied unchanged |  |
| `Tools/lowest_lod.py` | KY `Tools/lowest_lod.py` | 82 | copied, fixed | VM from constants; G6 header (no operator id / dated authority) |
| `Tools/mat_probe.py` | EW `Tools/mat_probe.py` | 92 | copied unchanged |  |
| `Tools/mesh_bounds.py` | EW `Tools/mesh_bounds.py` | 119 | copied unchanged |  |
| `Tools/mesh_class.py` | EW `Tools/mesh_class.py` | 120 | copied unchanged |  |
| `Tools/mesh_collision.py` | EW `Tools/mesh_collision.py` | 121 | copied, fixed | shell folder from constants; G6 header (no operator id / dated authority) |
| `Tools/mi_param_probe.py` | EW `Tools/mi_param_probe.py` | 59 | copied, fixed | G6 header (no operator id / dated authority) |
| `Tools/mob_probe.py` | EW `Tools/mob_probe.py` | 43 | copied unchanged |  |
| `Tools/never_vanish.py` | KY `Tools/never_vanish.py` | 81 | copied, fixed | G3 clone_suffix required; graph version required; vendor reload list ARGS.vendor_prefixes (default /Game/STF/); G6 header (no operator id / dated authority) |
| `Tools/pcg_check_upright.py` | EW `Tools/pcg_check_upright.py` | 87 | copied unchanged |  |
| `Tools/pcg_doc.py` | EW `Tools/pcg_doc.py` | 88 | copied unchanged |  |
| `Tools/pcg_finish.py` | KY `Tools/pcg_finish.py` | 84 | copied, fixed | G3 clone_suffix required; G6 header (no operator id / dated authority) |
| `Tools/pcg_tex_inspect.py` | EW `Tools/pcg_tex_inspect.py` | 89 | copied unchanged |  |
| `Tools/pie_run.py` | EW `Tools/pie_run.py` | 110 | copied, fixed | receipts/Captures and receipts/PIE created with parents; G6 header (no operator id / dated authority) |
| `Tools/pie_test.py` | EW `Tools/pie_test.py` | 109 | copied, fixed | checked, no change: bThrottleCPUWhenNotForeground works (12 KY receipts of this exact file, sha f4385fb4, return ok/throttle false); RG2 #11 inference refuted |
| `Tools/prep_zone_clone.py` | KY `Tools/prep_zone_clone.py` | 76 | copied, fixed | G2/G4; SRC_SHA -> ARGS.expected_sha; DST = clone_map("") (first clone, explicit); G6 header (no operator id / dated authority) |
| `Tools/props_near_roads_plan.py` | EW `Tools/props_near_roads_plan.py` | 55 | copied, fixed | G5 half-extent from constants; --margin-m required; schema neutral; G6 header (no operator id / dated authority) |
| `Tools/props_trim.py` | EW `Tools/props_trim.py` | 56 | copied, fixed | G1; MAIN from constants; G6 header (no operator id / dated authority) |
| `Tools/quit_clean.py` | EW `Tools/quit_clean.py` | 6 | copied, fixed | G1 (task from script_file); COOK from constants; NameError fixed (bank = None; refuses when the workflow module is missing and cook leftovers exist); G6 header (no operator id / dated authority) |
| `Tools/ray_probe.py` | EW `Tools/ray_probe.py` | 114 | copied unchanged |  |
| `Tools/readback_area.py` | EW `Tools/readback_area.py` | 34 | copied, fixed | G1; docstring path; G6 header (no operator id / dated authority) |
| `Tools/remove_actors.py` | EW `Tools/remove_actors.py` | 40 | copied, fixed | G1; MAIN from constants; G6 header (no operator id / dated authority) |
| `Tools/road_asphalt.py` | EW `Tools/road_asphalt.py` | 50 | copied, fixed | hda_edits loaded by path (was import hda_ew_v002_edits); MAIN/MESH from constants; G6 header (no operator id / dated authority) |
| `Tools/road_material_probe.py` | EW `Tools/road_material_probe.py` | 52 | copied, fixed | G6 header (no operator id / dated authority) |
| `Tools/road_mi.py` | EW `Tools/road_mi.py` | 49 | copied, fixed | G4 names from constants; G6 header (no operator id / dated authority) |
| `Tools/road_uv_fix.py` | EW `Tools/road_uv_fix.py` | 45 | copied, fixed | G1; bake mesh from constants; G6 header (no operator id / dated authority) |
| `Tools/road_uv_probe.py` | EW `Tools/road_uv_probe.py` | 47 | copied, fixed | MESH from constants; G6 header (no operator id / dated authority) |
| `Tools/road_uv_rebuild.py` | EW `Tools/road_uv_rebuild.py` | 46 | copied, fixed | bake mesh from constants; G6 header (no operator id / dated authority) |
| `Tools/roadhit_probe.py` | EW `Tools/roadhit_probe.py` | 116 | copied unchanged |  |
| `Tools/roadmesh_probe.py` | EW `Tools/roadmesh_probe.py` | 117 | copied unchanged |  |
| `Tools/save_main_map.py` | EW `Tools/save_main_map.py` | 11 | copied, fixed | G1; MAIN from constants; G6 header (no operator id / dated authority) |
| `Tools/save_prefix.py` | EW `Tools/save_prefix.py` | 10 | copied, fixed | refuses dirty maps (matches its docstring); G6 header (no operator id / dated authority) |
| `Tools/scene_info.py` | EW `Tools/scene_info.py` | 113 | copied unchanged |  |
| `Tools/set_mi_params.py` | EW `Tools/set_mi_params.py` | 57 | copied, fixed | area Materials folder from constants; G6 header (no operator id / dated authority) |
| `Tools/sky_dir_probe.py` | EW `Tools/sky_dir_probe.py` | 115 | copied unchanged |  |
| `Tools/sma_list.py` | EW `Tools/sma_list.py` | 125 | copied unchanged |  |
| `Tools/split_buildings.py` | EW `Tools/split_buildings.py` | 38 | copied, fixed | G1; map dict from constants (clone_map); G7 docstring; fix_attach step documented; G6 header (no operator id / dated authority) |
| `Tools/split_shells.py` | EW `Tools/split_shells.py` | 39 | copied, fixed | G1; SRC and map dict from constants; G7 docstring; pre-destroy authority from ARGS; G6 header (no operator id / dated authority) |
| `Tools/start_area_generation.py` | EW `Tools/start_area_generation.py` | 33 | copied, fixed | G1; EW_MAP branch generic: expectations mandatory for every instantiate (first generation: empty ledger); spec = hda_edits.py; REGEN_ACTIVE reset to GENERATION_START_FAILED on a failed start; RoadBLD assert kept; G6 |
| `Tools/state.py` | EW `Tools/state.py` | 122 | copied unchanged |  |
| `Tools/switch_profile_hda.py` | EW `Tools/switch_profile_v002.py` | 29 | copied, fixed | renamed from switch_profile_v002.py; loads hda_edits by path; previous/new HDA from constants; versioned backup and receipt names; authority by --authority, operator from ASSIGNMENT.json; RC-12 note; G6 |
| `Tools/temp_hide.py` | EW `Tools/temp_hide.py` | 60 | copied, fixed | G6 header (no operator id / dated authority); docstring neutral |
| `Tools/texture_export_probe.py` | EW `Tools/texture_export_probe.py` | 126 | copied, fixed | G6 header (no operator id / dated authority) |
| `Tools/track_mi.py` | EW `Tools/track_mi.py` | 51 | copied, fixed | hda_edits loaded by path; name check from TRACK_MI_NAME (G4); G6 header (no operator id / dated authority) |
| `Tools/trees_pcg.py` | KY `Tools/ky4_trees_v2.py` | 79 | copied, fixed | renamed from ky4_trees_v2.py; G3; graph version required; Paz Farm Georef/meshes/labels -> optional ARGS.site/site_georef/site_mesh_folder (site only); G4; G5; G6 header (no operator id / dated authority) |
| `Tools/verify_clone_v2.py` | KY `Tools/verify_clone_v2.py` | 86 | copied, fixed | NEW renamed CLONE = clone_map(ARGS.clone_suffix); merged-buildings label prefix = AREA_ID; G6 header (no operator id / dated authority) |
| `Tools/volume_collision_probe.py` | EW `Tools/volume_collision_probe.py` | 118 | copied unchanged |  |
| `Tools/wait_lease.py` | EW `Tools/wait_lease.py` | 8 | copied, fixed | G1 TASK = parents[1] with a Staging check; G6 header (no operator id / dated authority) |
| `Tools/world_probe.py` | EW `Tools/world_probe.py` | 36 | copied unchanged |  |
| `Zones/classify_zones.py` | EW `Zones/classify_zones.py` | 68 | copied, fixed | thresholds from ZONE_RULES; docstring dates from DATA_RECEIPT; G6 header (no operator id / dated authority) |
| `Zones/make_masks.py` | EW `Zones/make_masks.py` | 69 | copied, fixed | mask prefix (G4) and side length (G5) from constants; G6 header (no operator id / dated authority) |
| `Zones/make_textures.py` | EW `Zones/make_textures.py` | 70 | copied, fixed | STRETCH from SAT_STRETCH; names (G4) and mapping (G5) from constants; G6 header (no operator id / dated authority) |
| `Zones/trees_v2.py` | KY `Zones/trees_v2.py` | 80 | copied, fixed | full text: Paz Farm parts removed (Georef reads, parcels/fields clearing, windbreak rows and their write); footprints from Buildings_v2; S2 files from DATA_RECEIPT; HALFA (G5); NDVI thresholds from TREE_RULES; G6 header (no operator id / dated authority) |
| `Zones/zones_data.py` | EW `Zones/zones_data.py` | 67 | copied, fixed | AREA, HALF, PX from constants (G5); run date = today; Sentinel windows from constants; G6 header (no operator id / dated authority) |
| `acquire_area.py` | EW `acquire_area.py` | 12 | copied, fixed | G2 AREA/LAT/LON; G5 request half, grid half, extent, samples from SIZE_KM; neutral cache comment; header |
| `build_hda.py` | EW `build_hda_4km_ew_v002.py` | 19 | copied, fixed | renamed from build_hda_4km_ew_v002.py; imports hda_edits; base generator, grid (G5) and record name are inputs; authority from argv; G6 |
| `hda_edits.py` | EW `hda_ew_v002_edits.py` | 21 | copied, fixed | renamed from hda_ew_v002_edits.py; full skeleton: base = HDA_BASE_* inputs; EDITS built from the base text: P pole tuple + this AREA_ID, T module track path -> this TRACK_MI (+ EXTRA_EDITS); names from G2/G4; G6 |
| `prepare_profile.py` | EW `prepare_profile.py` | 26 | copied, fixed | template profile = PROFILE_TEMPLATE_* inputs (not Lebanon); HDA from the build record; decision texts from ASSIGNMENT.json profile_decisions; RoadBLD block kept disabled (status text from the [D] answer); G6 |
| `promote_profile.py` | EW `promote_profile.py` | 27 | copied, fixed | AREA from constants; bank digest checked against the named template profile; RC-12 note; header |
| `verify_hda.py` | EW `verify_hda_4km_ew_v002.py` | 20 | copied, fixed | renamed from verify_hda_4km_ew_v002.py; base and grid are inputs; "v001 and KY v002 unchanged" -> "base unchanged"; G6 |
| `Tools/area_constants.py` | new | 155 | new file | the only file that names an area (see "How to use") |

`pie_test.py` is listed include-after-fix only for a check: 12 receipts of this exact file (sha f4385fb4) in the KY task
returned ok with `bThrottleCPUWhenNotForeground` set, so it is unchanged.

## Intentionally excluded (68 rows of the list)

The `_aviv` clients (Aviv's own editor ports 19840 / 8000) are excluded and no template file names those ports. Area output
files (`DATA_RECEIPT.json`, `MASKS.json`, `BUILDINGS_COMPACT.json`, receipts, cameras, args files) are not template content.

| # | file | why (from the list) |
|---:|---|---|
| 4 | `Tools\ky_client_aviv.py` | `PORT = 19840` (:13), Aviv's own editor (RG2 #6). GR:121 and RC-70 exclude it. |
| 5 | `Tools\ky_capture_aviv.py` | `PORT = 8000` (:8) (RG2 #15). GR:121 and RC-70 exclude it. |
| 13 | `build_hda_4km.py` | It derives from Lebanon v006, which has no trunk/primary roads (RG4 #12; F-T07-16). Its anchors only match a Lebanon-shaped module. The edits-file pattern replaces it (PB:301). |
| 14 | `build_hda_4km_v002.py` | KY one-off; its anchors only fit the KY v001 module (RG4 #11). |
| 15 | `verify_hda_4km_v002.py` | KY one-off (RG3 #17). |
| 16 | `build_hda_4km_ew_v001.py` | Superseded by the v002 pattern. Its edits P/S/C/T are already inside the EW v002 generator. |
| 17 | `hda_ew_v001_edits.py` | Same as row 16. |
| 18 | `verify_hda_4km_ew_v001.py` | Same as row 16. |
| 22 | `geocity_city_module_4km_ky_v001.py` | A generated text copy of the module (6,992 lines), written by the build script. |
| 23 | `geocity_city_module_4km_ky_v002.py` | Same as row 22. |
| 24 | `geocity_city_module_4km_ew_v001.py` | Same as row 22. |
| 25 | `geocity_city_module_4km_ew_v002.py` | Same as row 22. |
| 28 | `switch_profile_v002.py` | Superseded by row 29. KY :9 also names the HDA outside the constants (RG2 #25). |
| 31 | `Tools\create_area_finish.py` | It holds the NOAA check (PB:121, :306). RUNS EW 2. |
| 35 | `Tools\recover_v002.py` | A one-off incident recovery (RG2 #17). The EW docstring :1-9 calls it a "FALLBACK", because row 33's checks avoid the case. |
| 44 | `Tools\bldg_poscheck.py` | It reads `WPTRIAL_BLD_PLAN.json` (:8); stale (RG4 #23). |
| 53 | `Tools\road_asphalt_mi.py` | An earlier vendor-MI route. Its two MIs were discarded (`discard_scratch_mis.py` docstring), and rows 48-49 replace it. |
| 54 | `Tools\track_probe.py` | A one-issue diagnosis ("why the v002 track shows no gravel detail", docstring :1-4). |
| 61 | `Tools\hide_merged.py` | "Trial only" (docstring). Row 60 replaces it. |
| 62 | `Tools\discard_scratch_mis.py` | One-off ("Discard both", docstring). |
| 63 | `Tools\delete_assets.py` | One-off for the 2026-10-13 decision; no PB step calls it. Deletions need Aviv's confirmation (PB:60). |
| 64 | `Tools\asphalt_texture_probe.py` | One-time survey. |
| 65 | `Tools\station_import.py` | El Wahat hero site (the station). |
| 66 | `Tools\station_lod_probe.py` | El Wahat hero site. |
| 73 | `Tools\farm_material.py` | One-shot (asserts at :22 that the texture is absent); Paz Farm (RG2 #12). No PB step calls it. |
| 75 | `Tools\farm_readback.py` | PazFarm labels (RG3 #32). |
| 93 | `Tools\pcg_gen.py` | It takes the first volume (`[0]`) and has no map assert (RG4 #37). Row 79's volume step replaces it. |
| 94 | `Tools\pcg_visibility.py` | It dirties the level (RG4 #31). |
| 95 | `Tools\zone_probe.py` | A temporary probe that can leave an actor behind (RG4 #13). |
| 96 | `Tools\clip_test.py` | A diagnosis that leaves MIs dirty (RG4 #27). |
| 97 | `Tools\nanite_toggle.py` | Changes meshes without saving (RG4 #34). |
| 98 | `Tools\save_farm_assets.py` | Its allowlist is PazFarm (RG2 #34). |
| 99 | `Tools\place_farm.py` | Hero site (PB:232, :347). It creates HISMs as Movable and unattached (RG2 #9). |
| 100 | `Tools\fence_v003.py` | Hero site (PB:233, :347). Its posts are never filled (RG4 #1). |
| 101 | `Tools\straw_beds.py` | Hero site (PB:233-237, :347; RG2 #3). |
| 102 | `Tools\fields_place.py` | Site-specific (PB:347). It reads `PazFarm_2026-10-08` field data (RG3 #3). |
| 103 | `Tools\apply_v002.py` | Site-specific (PB:347; RG4 #2). |
| 104 | `Tools\apply_v003.py` | Site-specific (PB:347; RG3 #4). |
| 105 | `Tools\import_astra.py` | Hero site (PB:231). BASE is PazFarm (:13-14). The save result is never checked (:24; RG3 #6). Row 85 covers the general Astra import (PB:253). |
| 106 | `Tools\trace_probe.py` | Paz Farm pin coordinates (:8; RG2 #30). |
| 127 | `Tools\tex_export.py` | Same purpose as row 126, but tied to the Paz Farm plots (docstring :1). |
| 128 | `Tools\find_instance.py` | Writes a fixed `cameras_lodcheck.json`; no PB step calls it. |
| 129 | `Tools\handover_probe.py` | One-off facts for a simulation hand-over (docstring :1). |
| 130 | `Tools\wp_setup.py` | targets a deleted map (RG2 #2) |
| 131 | `Tools\wp_verify.py` | deleted target (RG2 #10) |
| 132 | `Tools\make_wptrial.py` | RG2 #19 |
| 133 | `Tools\reset_trial.py` | RG2 #28 |
| 134 | `Tools\wptrial_save.py` | RG4 #20 |
| 135 | `Tools\hlod_probe.py` | RG3 #26 |
| 136 | `Tools\hlod_readback.py` | RG3 #16 |
| 137 | `Tools\hlod_doc.py` | HLOD API doc |
| 138 | `Tools\shell_debug.py` | RG4 #29 |
| 139 | `Tools\bld_probe.py` | RG3 #14 |
| 140 | `Tools\hashset_move_layer.py` | RG3 #27 |
| 141 | `Tools\hashset_move_layer2.py` | RG4 #24 |
| 142 | `Tools\hashset_probe.py` | WP only (RG4 #26) |
| 143 | `Tools\hash_class_probe.py` | WP API |
| 144 | `Tools\wp_hash_probe.py` | WP only |
| 145 | `Tools\wp_layers_check.py` | WP only; PazFarm labels |
| 146 | `Tools\obj_dump.py` | dumps the WP runtime hash set |
| 147 | `Tools\reload_pkgs.py` | no PB step calls it; WPTrial allowlist (RG2 #31) |
| 148 | `Tools\md_api_probe.py` | unreliable ids (RG2 #18, #26) |
| 149 | `Tools\md_debug.py` | RG2 #26 |
| 150 | `Tools\clone_cleanup.py` | one-off; its hash :29 no longer matches (RG3 #20) |
| 151 | `Tools\trashcan_wpo_static.py` | one-off fix to a shared bank material (PB:362). Bank owner is Aviv (GR:47). |
| 152 | `Handover_2026-10-12\build_rest.py` | a hand-over package for another person, outside the tool folders |
| 153 | `Handover_2026-10-12\build_roads.py` | same as row 152 |
| 154 | `WPTrial\compact_buildings.py` | WP trial data; row 37 replaces it |

## Open items

1. **RoadBLD for all areas (RC-60) is decided, but the sealed code is unchanged.** `Content/Python/geocity_editor_action.py:139`
   and `Content/Python/geocity_roadbld_clip.py:96` still limit RoadBLD to ('GazaRimal', 'GazaShujaiya',
   'Lebanon_33390778_35506639_4km'). So `prepare_profile.py` keeps the RoadBLD block disabled and `start_area_generation.py`
   refuses a RoadBLD profile. A RoadBLD-on template needs that sealed change first (Aviv's per-item approval).
2. **Playbook and skill lines to repoint** (listed here, not edited; current text quoted verbatim, read on 2026-10-19):

**SK:18** now:
> - **Work in a copy of the reference tools.** Make a new task folder `Staging/NewArea_<Name>_<lat8>_<lon8>_<size>_<date>/` and copy the reference `Tools/` from `Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/`. Change only the path constants (playbook section 11). Never edit the reference folder's tools for the new area.

should say: copy the whole `Staging/Templates/NewAreaTools_v001/` folder and set only `Tools/area_constants.py` (never run the template in place)

**PB:76** now:
> 3. **Copy the tools:** copy `Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/Tools/` into the new folder. Most tools name the area only in their top constants, so change those (see section 11):

should say: copy `Staging/Templates/NewAreaTools_v001/` (Tools, Zones, Buildings_v2 and the root scripts); every area value is in `Tools/area_constants.py`

**PB:77-81** now:
>    - `TASK`, `MAIN`, `MAP`, `CLONE`, `TRIAL`, `AREA`;
>    - the area id;
>    - the landscape half-extent (4 km: ±201,600 cm; 2 km: ±100,800 cm);
>    - in `launch_area_editor.ps1`, the `$AreaPrefix` lines;
>    - **the editor ports.** The reference set uses 19852 (Copilot), 18092 (plugin) and 8012 (native MCP), hard-coded in `launch_area_editor.ps1` (`$CopilotPort`, `$PluginPort`, `$NativePort`), `ky_client.py` (`PORT`) and `ky_capture.py` (`PORT`). Choose three ports that no other task folder uses and set them in all three files. Otherwise a new area's editor collides with any open editor of another task, and parallel editors are impossible.

should say: the constants and the three ports live in `Tools/area_constants.py` (COPILOT_PORT, PLUGIN_PORT, NATIVE_PORT); the launcher, `ky_client.py` and `ky_capture.py` read them

**PB:97** now:
> - **Start from the closest HDA that completed a full non-Gaza cook.** Last time: Lebanon 4 km v006 for 4 km, its 2 km variant for 2 km. Use `build_hda_4km.py` / `build_hda_4km_v002.py` as templates. They:

should say: name `build_hda.py` / `hda_edits.py` (edits-file pattern; base = HDA_BASE_* in area_constants.py)

**PB:102** now:
> - **No cook during authoring.** Verify separately (`verify_hda_4km_v002.py`).

should say: name `verify_hda.py`

**PB:121** now:
>    - **El Wahat (2026-10-12):** after `UpdateSky`, `CorrectedElevation` reads 180 + elevation, so a check built on it inverts. The real elevation is in `SunElevation`. Check the light against an independent sun model instead: `create_area_finish.py` (NOAA formulas) in the El Wahat Tools. The reference `create_area.py` still has the faulty check.

should say: the template `create_area.py` sets NorthOffset -90 per instance and checks the sun with the NOAA model (RC-72)

**PB:132** now:
>    - On a failure: `exit_failed_area_run.py` (no saves). The manager, or the operator with Aviv's approval, appends the OWNER=NONE release line.

should say: "Aviv, or the agent he assigns, appends the OWNER=NONE release line" (there is no manager; the template exit_failed_area_run.py says so)

**PB:139** now:
>      - switch `profile['hda']` before the run (`hda_v002_prepare.py` and `switch_profile_v002.py`).

should say: name `hda_revision_prepare.py` and `Tools/switch_profile_hda.py`

**PB:142** now:
>      - remove only `_old_0` and save (`recover_v002.py`);

should say: one line: `recover_v002.py` is not in the template (one-off; the instantiate checks of start_area_generation.py prevent the case)

**PB:190** now:
> 2. **PCG graph** (`build_zone_pcg.py`, later `ky4_trees_v2.py graph|volume|assign_graph`):

should say: name `trees_pcg.py`

**PB:209** now:
>    6. `fields_place place` → windbreaks → `make_static` → `save_prefix` → `pcg_finish save`.

should say: add "only when the area has fields" (fields_place.py is a site recipe, not in the template)

**PB:294** now:
> **Source:** `Staging/ElWahatEgypt_SESSION_HANDOFF_2026-10-12.md` and `Staging/NewArea_ElWahatEgypt_29176036_29602273_4km_2026-10-12/RESULT.md`. The El Wahat Tools folder holds generalised or fixed versions of several reference tools; prefer those for the next area.

should say: name `Staging/Templates/NewAreaTools_v001/`

**PB:330** now:
> ## 11. Tool inventory (reference folder `Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/Tools/`)

should say: name the template folder

**PB:337** now:
> | Close and recover | `quit_clean.py`, `exit_failed_area_run.py`, `recover_v002.py` |

should say: drop `recover_v002.py` (not in the template)

**PB:338** now:
> | Generation | `start_area_generation.py`, `wait_lease.py`, `readback_area.py`, `create_area.py`, `hda_v002_prepare.py` |

should say: `hda_v002_prepare.py` -> `hda_revision_prepare.py`

**PB:340** now:
> | PCG and vegetation | `ky4_trees_v2.py`, `never_vanish.py`, `lowest_lod.py`, `audit_visibility.py` |

should say: `ky4_trees_v2.py` -> `trees_pcg.py`

**PB:345** now:
> | World Partition trial (only if Aviv wants WP) | `split_buildings.py`, `split_shells.py`, `wp_setup.py`, `wp_verify.py` |

should say: split_buildings.py / split_shells.py move to the standard steps (5.6); the WP tools are not in the template

**PB:347** now:
> **Site-specific recipes (adapt, don't run as-is):** `place_farm.py`, `fence_v003.py`, `straw_beds.py`, `fields_place.py`, `apply_v002.py`, `apply_v003.py`, and the scripts in `PazFarm_2026-10-08/Georef/` and `Fields_2026-10-10/`.

should say: add "these stay in their own task folders; they are not in the template"

**PB:350** now:
> - area folder: `acquire_area.py`, `build_hda_*.py`, `verify_hda_*.py`, `prepare_profile.py`, `promote_profile.py`, `switch_profile_v002.py`;

should say: `build_hda.py`, `verify_hda.py`, `Tools/switch_profile_hda.py` (and `hda_edits.py`)


3. The PCG, vegetation and farm-ground tools are the Karmei Yosef code that ran there; no run has proved them on a second area.
4. `farm_real_ground.py` 'build' needs a painted-farm Lerp in the area ground master (its `find_sat` precondition, now
   documented); a master made only by `build_ground_satellite.py` does not have it, so a site that needs the farm branch must
   adapt that step first.
5. The generator base (El Wahat v002 at the time of writing) carries the El Wahat decisions S (no sidewalks on service and
   unclassified), C (construction ways) and the long-way trim; a new area whose [D] answers differ adds EXTRA_EDITS.
6. `track_mi.py` texture defaults are the El Wahat 'Sandy gravel' set; pass ARGS.textures for another ground.
7. `hda_revision_prepare.py` 'clear_for_instantiate' now takes the run facts as ARGS (ledger actor count, bank_instances,
   Bldg labels, expected kept classes); they were El Wahat literals.
