# Paz Farm real ground, road-to-road parcels and more trees: result (2026-10-10)

Done on the 4 km PCG clone only: `/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/L_KarmeiYosef_31850349_34907601_4km_PCGTrial`.
- Saved map sha `023aa1f5daa20bd96034005558f4156265294a0c1cfd2c1e7b121b4881182611`, 214.8 MB.
- Verified after a fresh reopen (editor PID 26076): 0 dirty packages.
- The main 4 km map, the shared master `M_GeoCityAuto_KY4`, the old PCG graph and masks, vendor content and the WP trial are unchanged. Every change is a new package or a change to the clone map.
- Labels: [M] measured; [A] Aviv's decision.

## Aviv's decisions

| Decision | Source |
|---|---|
| Ground: "Real materials per plot" | AskUserQuestion |
| Trees: satellite tree map + windbreak rows near the farm + denser forest and scrub | AskUserQuestion |
| "I don't want the plot mask to be according to screenshot boundaries at all." Plot edges come from "Dirt roads in our map". | his message |
| Parcel preview 1 (stopped at satellite field edges): "Push all to roads" | AskUserQuestion |
| Parcel preview 2: "Yes, lighter rows" | AskUserQuestion |

## 1. Parcels: road to road, no screenshot edges [M]

Tool: `Georef/parcels_v2.py`, writing `PARCELS_V2.json`, `parcels_v2_labels.tif` (1 m grid, ±1 km around the pin) and `parcels_v2_preview.png`.

- Every plot edge that was only the screenshot frame is pushed outward along the plot's own side lines until it meets one of:
  - an OSM highway, or a traced farm road, which continues straight;
  - a building;
  - the village, water or forest zone;
  - another plot's extension (the nearest original plot wins).
- Satellite field edges are not used (`USE_SAT False`).
- About 0.03 of each parcel boundary is still within 10 m of the old frame line.
- In total +77.7 ha.
- **Inference, not map data:** two traced farm roads that left the screenshot are continued straight until they meet a mapped road. They are painted as dirt and also split parcels:
  - `west_track`, about 486 m;
  - `yard_access_north`, about 392 m.
  
  Neither is in OSM. They can be dropped as painted roads and as barriers with an offline mask change and a mask reimport; the material graph doesn't need editing.

Largest pushes:

| Plot | Push |
|---|---|
| North-east field, east | 665 m |
| North-east citrus | 626–653 m |
| West fields | about 400 m |
| Avocado, south | 350–480 m |

## 2. Ground: real materials instead of the painted overlay [M]

- **Mask:** `Georef/farm_ground_v3.py` builds `T_PazFarm_GroundMask_v3.png`, covering a 1,664 m square at 0.81 m per pixel. It holds weights only: R tilled soil, G grass or weedy margin, B compacted dirt (farm roads, yard), A coverage. There are no colours and no stripes.
- **Edges and margins:**
  - noisy, feathered parcel edges;
  - weedy margins of 2–3 m along every parcel edge and road;
  - narrow leftover strips filled as verge;
  - the traced farm roads continue straight, only as far as the parcels beside them.
- **Textures** (installed packs, read only):
  - soil: Modular_Rural_Cabin Mud;
  - tilled: FC_Coastal T_SoilGround_02;
  - grass and margins: ForestLandscape fl2_ground_VII;
  - dirt: Modular_Rural_Cabin Ground_Dirt.
- **Material:** `<clone>/PazFarm/RealGround/M_GeoCityAuto_KY4_RealFarm_v2`, a copy of the area master, with MI `MI_GeoCityGround_PazFarmReal_v2` on the clone landscape.
  - The farm branch is `BlendMaterialAttributes(original, farm, mask.A × FarmR_Blend)`.
  - Two texture scales are used against tiling.
  - The tints are MI parameters.
  - A satellite brightness factor is clamped to 0.75–1.25.
  - The old painted layer is off (`Farm_Blend` 0).
- **Final MI values:**
  - `FarmR_SatMix` 0.05;
  - `FarmR_MacroAmt` 0.25 (low on purpose, so real neighbouring field shapes don't show inside the parcels);
  - tints soil (0.36, 0.28, 0.24), tilled (0.27, 0.22, 0.20), grass (0.17, 0.19, 0.18), dirt (0.36, 0.32, 0.25).

## 3. Crops in the extended parcels [M]

Actor `PazFarm_Extension` (folder PazFarm), Static chain, 141,115 instances:

| Crop | Instances | How |
|---|---|---|
| Avocado | 2,552 | Same meshes as `PazFarm_Detail`, on the same global row lattice, so rows continue straight. Doubles of existing trees were skipped. |
| Citrus and young citrus | 4,531 | As above. They share meshes, so the placed count can't be split; the plan was 1,327 citrus + 3,206 young citrus. |
| Green-field stand-ins (`green_grass_patch_tall_01` + `grass_patch_01`) | 134,032 | Rows at the measured period, lighter spacing (1.1 m). |

- Heights come from the landscape only: 69 points on other actors were skipped.
- No real vegetable or crop meshes exist in the project, so the low plants are stand-ins.

## 4. More trees [M]

- **Offline:** `NewArea_..._4km_2026-10-08/Zones/trees_v2.py` produces `TREES_V2.json` and the masks under `zones/<run>/trees_v2/`.
- **Satellite rule (Sentinel-2, 21 Sep and 4 Apr):** a "tree" is green in both scenes and not greener now than in spring, which excludes irrigated crops. The resulting probabilities are dithered into binary masks.
- **New graph:** `<clone>/PCG/PCG_KY4_Zones_v002`.
  - Its first 8 branches have the same order, seeds and meshes as the old graph, checked against it.
  - All of them run on parcel-cleared masks, so stand-ins no longer sit on the farm.
  - The forest branch uses the ForestTrees satellite mask at 0.033 points per m².
  - The scrub-tree branch uses ScrubTrees at 0.0086.
  - New branches: `sat_trees` (SatTrees, 0.012) and `field_trees` (OpenField, 0.00006). All trees are the never-vanish copies.

| Count | Before | After |
|---|---|---|
| Zone vegetation (PCG) | 112,891 | 134,127 |
| Trees in it | 31,988 | 58,088 |
| Forest pines | 13,790 | 34,896 (2.5×) |
| Scrub thicket trees | 404 | 1,194 |

- **Windbreaks:** actor `KY4_Windbreaks` (folder Vegetation), Static, 1,541 trees.
  - Offset checked against the generator's road widths (`geocity_city_module_4km_ky_v001.py` ROAD_WIDTH_M): track 3 m, service 4 m, residential 7 m. Trunks stand 2–3 m beyond the road edge, and the crowns overhang slightly.
  - One row along each OSM track or farm road within 700 m of the farm, on the side away from the farm, 4 m from the centreline, every 5 m.
  - Never-vanish pine and green-tree copies.

## 5. Play-mode frame time [M]

Editor play mode, GPU-bound, indicative only. Same cameras and method as the WP trial. CSVs: `NewArea_..._4km_2026-10-08/receipts/PIE/trees_v2_*.csv`.

| View | Clone before | Now |
|---|---|---|
| Farm | 17.5 ms | 25.1 ms |
| Village | 13.8 ms | 13.7 ms |
| Forest | 8.4 ms | 8.4 ms |
| Wide | 24.4 ms | 29.8 ms |

The farm view's +7.6 ms is mostly the 134k green-field stand-ins.

## Captures

All in `NewArea_..._4km_2026-10-08/receipts/Captures/`:
- before: `rg_pre_b_*`;
- after: `rg3_b_*` (all 8 views) and `rgt3_b_*` (final tints);
- after the fresh reopen: `rgfresh_b_*`.

## Incidents

**Measured [M]:**
- My editor crashed three times: PIDs 30592, 34872 and 6808.
- Each was an access violation inside Python, called back from engine code: MaterialEditor twice, PCG once.
- Two crashes had the same address (`0x00007465736c6f18`) in different processes.
- Changing the landscape material made the clone's PCG regenerate on its own; seen once, in the last session.
- Nothing saved was harmed. Records are in `ASSIGNMENT_RUN.json` and `Staging/ParallelEditors/EDITOR_{30592,34872,6808}.json`.

**Inference, not proven:**
- The crashes may come from running Python steps while that background PCG regeneration was running.
- The earlier idea that editing a material graph a second time is the cause was contradicted by the third crash.
- The mitigations below held for one session only:
  - wait until PCG is idle before each step;
  - save after each stage;
  - run a forced garbage-collection probe (`Tools/gc_probe.py`) after each stage.

## Undo

- Landscape material back to `MI_GeoCityGround_PazFarm` (painted) or the area MI.
- PCG volume graph back to `PCG_KY4_Zones`, then regenerate.
- Delete the `PazFarm_Extension` and `KY4_Windbreaks` actors.
- Map before this work: `Staging/NewArea_..._4km_2026-10-08/Before/L_KarmeiYosef_31850349_34907601_4km_PCGTrial_6ccbaeb2.umap`.

## Unreferenced leftovers (delete only after Aviv confirms)

- `<clone>/PazFarm/RealGround/T_PazFarm_GroundMask`
- `<clone>/PazFarm/RealGround/M_GeoCityAuto_KY4_RealFarm`
- `<clone>/PazFarm/RealGround/MI_GeoCityGround_PazFarmReal`

These are v1, built on the screenshot plots.

## Open

- **Astra VisualFix v003 delivered, not imported:**
  - 3 Aleppo pines (113k triangles, plus a 1,642-triangle lowest LOD);
  - a strawberry bed v003 (10.4k, plus a 282-triangle lowest LOD).
  - The thin, pale windbreak and forest store pines would improve most from the pines.
- **Optional:** a draw-distance limit for the green-field stand-ins, which are low plants and not covered by the never-vanish rule, to win back farm-view frame time.
- `PazFarm_Detail` is still Movable in the clone. The HLOD needs it Static, as was done in the trial.

## Update 19:45Z: guessed roads removed, Astra v003 applied (fresh-reopen verified, PID 3048) [M]

**Map:** sha `42b39ead7432007e5537360225834d9de95ca997b15920dc7177f36f9aec0b34`, 0 dirty packages after a fresh reopen.

**Roads**
- Aviv: the red continuations were "way off". OSM is partial there: only 5 mapped tracks come within about 350 m of the farm.
- His decision: "Remove the guesses for now".
- `parcels_v2.py` now has `EXTEND_TRACED_ROADS False`. The traced farm roads stop where his screenshot shows them, and the parcels on each side meet instead.
- The mask, crops, tree masks and windbreaks were all rebuilt from the new parcels.
- The MI `FarmR_OriginY` is now -89644.88; the mask's north edge is 790 m from the pin.

**Astra VisualFix v003** ("Yes, import both")
- Imported to `<clone>/PazFarm/VisualFix_v003/`:
  - 36 textures;
  - a new `M_PazFarm_Master_OpaqueTwoSided` (a copy of the opaque master with two-sided on; property only);
  - 11 MIs;
  - 4 meshes (Nanite, Preserve Area), each with Astra's `_LOD3.fbx` as LOD1.
- The LOD1 sections were checked by name:
  - pines: bark and crown hull;
  - strawberry bed: mulch and canopy.
- Receipt: `receipts/PAZFARM_V003_MESHES.json`.
- **Forest and scrub:** new graph `PCG_KY4_Zones_v003`, with the same branches and seeds as v002 and the store pines mapped by height:
  - `SM_Pine_Tree_01` (13.8 m) → Aleppo C (15 m);
  - `SM_Pine_Tree_02` (14.2 m) → Aleppo B (11 m);
  - `SM_Pine_Tree_03` and `SM_Pine_Tree_05` → Aleppo A (8 m).
- **PCG pines now:** A 17,645, B 8,634, C 8,592. Total plants 133,731.
- **Windbreaks:** `KY4_Windbreaks` holds 1,356 trees, Aleppo A/B/C plus STF green trees.
- **Strawberry beds:** the 762 beds in `PazFarm_Detail` now use bed v003. There are 762 rather than 763 because `fence_v003` trimmed one bed outside the new fence on 2026-10-09.
  - Undo receipt: `receipts/PAZFARM_V003_BEFORE.json`, holding the v002 mesh path. It was written by hand because the first call stopped on the 763 check after the swap.
- **Crops:** `PazFarm_Extension` holds 156,611 instances: 149,603 green-field stand-ins plus about 7,000 avocado and citrus trees.

**Play-mode frame time (ms)**

| View | Clone, before all of this | Ground + trees v2 | Now |
|---|---|---|---|
| Farm | 17.5 | 25.1 | 25.5 |
| Village | 13.8 | 13.7 | 13.4 |
| Forest | 8.4 | 8.4 | 8.6 |
| Wide | 24.4 | 29.8 | 30.6 |

**Seen [M]:**
- The forest reads as dense, dark olive canopy.
- The windbreaks are umbrella pines along the roads.
- The v003 strawberry beds read as continuous green rows, fairly light and saturated, with little black mulch showing.

**Not done:** Aviv's draw-distance choice for the crop stand-ins is "Keep always visible", so nothing was changed there.

**Undo:**
- volume graph back to `PCG_KY4_Zones_v002` or `_v001` and regenerate;
- `apply_v003.py revert` for the bed and windbreak meshes;
- `EXTEND_TRACED_ROADS True` and rerun the offline chain for the old parcels.
