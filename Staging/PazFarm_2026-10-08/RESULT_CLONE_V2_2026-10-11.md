# Karmei Yosef 4 km: rebuilt clone with generator road 44 (2026-10-11)

Operator: Claude Code session 4a6a1d0c (Karmei Yosef). Authority: Aviv 2026-10-11, "Generator builds it", "Yes, full generator route", "Yes, fix them" (dirt roads), "Recover + rerun".

## Result (measured, fresh reopen verified 12:07Z)

- **New clone:** `/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/L_KarmeiYosef_31850349_34907601_4km_PCGTrial_v2`
  - Saved map sha256: `299c5b6095ebd76238f51788615f81017a24c0a1cf32b9e2ab9c68cedcf7e9fc`.
  - It is a copy of the regenerated main map (sha f21ab2c7, generator v002), so road 44 and its links are now built by the generator.
- **The old clone** (`..._PCGTrial`, sha 65adf6dd) is kept unchanged as the fallback.
  - Its bake packages are shared with the main map, so it now shows the new roads and buildings on the old terrain.
- **Contents of the new clone** (`receipts/VERIFY_CLONE_V2.json`; every count matches the build, every part is Static, none detached):

| Actor | Instances | What |
|---|---|---|
| PazFarm_Detail | 2,189 | farm crops, fence (from the old clone, same transforms) |
| PazFarm_Barn, PazFarm_Gate, PazFarm_Gate_2 | 3 actors | barn and the two gates |
| KY4_Fields_Crops | 135,420 | field crop stand-ins |
| KY4_Fields_Weeds | 61,236 | Astra v004 grass clumps and patches, margin shrubs |
| KY4_Fields_Orchards | 16,357 | orchards, plus Astra v004 olives |
| KY4_Fields_Vines | 2,125 | Astra v004 vine-row tiles |
| KY4_Fields_Greenhouses | 2,462 | greenhouse tunnels |
| KY4_Windbreaks | 1,146 | windbreak rows (Aleppo pines and broadleaf) |
| PCG volume (graph PCG_KY4_Zones_v003) | 112,285 | forest, scrub, field trees (old clone: 112,405) |

- **Landscape material:** `MI_GeoCityGround_PazFarmReal_v2`.
  - Its master `M_GeoCityAuto_KY4_RealFarm_v2` (sha e2a679ec) now has the dirt-track pass-through: the farm/field ground steps aside wherever the generator painted `Dirt_Path`.
  - So the generator's dirt tracks show again.
- **Astra FieldCrops v004** is imported under `<clone>/PazFarm/FieldCrops_v004/`:
  - 49 textures, 19 material instances, 15 meshes;
  - each mesh has the authored low LOD as LOD1; sizes match the manifest.
- **Play mode** (`receipts/PIE/PIE_clone_v2.json`), mean frame time:

| View | Now | Old clone |
|---|---|---|
| Farm | 18.8 ms | 22.3 ms |
| Village | 13.6 ms | 15.1 ms |
| Forest | 8.7 ms | (not given) |
| Wide | 35.8 ms | 33.1 ms |

- **Captures:** `NewArea_.../receipts/Captures/clone_v2_*.png`.
  - Views: overhead, farm, two dirt tracks, vines, olives, grass, road 44, greenhouses.

## Notes and open points

- **Road 44 surface:** road 44 uses the generator's standard road material (the same light grey paving as every generated road). A darker asphalt look for highways would be a separate change.
- **Lighter screenshot-road dirt:** this part of the dirt-road plan was NOT applied. The screenshot dirt roads already read as pale bands in the captures; it can be tuned later through the material instance (`FarmR_Tint_Dirt`) without a graph edit.
- **Fallow fields:** the grass density on fallow fields is as designed in FIELD_PLANTS_V2 (sparse tufts); it reads mostly as bare ground at 30 m.
- **Editor crash:** editor PID 5504 crashed at 11:52:57Z while saving the map right after the material-graph edit. It is the fourth crash of this family; the receipt is `receipts/CRASH_PID5504_20261011.json`.
  - Nothing saved was lost. Only an unsaved assignment was lost, and it was redone in a fresh editor.
  - New rule: after a material-graph edit, quit the editor before any other step or save.
- **New tools:**
  - `clone_v2.py` step `save` (staged named save of the new clone map);
  - `dz_probe.py`, `ground_z.py`, `verify_clone_v2.py` (all read-only).
- **Old receipts** of the old clone placement are kept in `receipts/OldClone_65adf6dd/`.
- **Still awaiting Aviv's confirmation before any deletion:**
  - the trial files;
  - the unused v1 ground packages and `T_PazFarm_GroundMask_v2`;
  - Astra's ~2 GB `Temp/DistanceCache`;
  - (new candidate) the old clone map once the new one is accepted.

## Update 2026-10-11 15:42Z: strawberry beds re-laid (saved, reopen check pending)

- **Aviv's request:** "Real spacing" and "the beds are not aligned to the ground".
- **What changed:** the strawberry beds in `PazFarm_Detail` went from 762 flat tiles (5.5 m between rows) to **2,478 ground-fitted tiles** (1.7 m between bed centres).
  - Each tile is pitched to the ground between its two ends, rolled to the cross slope, and sunk 3 cm.
  - Mid-tile, the bed sits 2.5–9 cm into the ground; none floats.
  - Tools: `Georef/strawberry_beds_v2.py` → `STRAWBERRY_BEDS_V2.json`, and `Tools/straw_beds.py relayout`.
- **Counts and map:** `PazFarm_Detail` now holds 3,905 instances. Map saved: sha `fafde8f006f68fe547264206db20d2531793682cc254a0e7b92f41e8a972583b`.
- **Undo:** `straw_beds.py step revert` with `receipts/STRAW_BEDS_BEFORE_20261011T154144Z.json`.
- **Captures:** `straw_after_*.png` (before: `straw_now_*.png`).
- **Not yet done:** the fresh-reopen check, after Aviv closes editor 35308. `verify_clone_v2_args.json` already expects 3,905.
- **Next:** the new bed model comes from Astra (`HANDOFF_ASTRA_StrawberryBeds_v005.md`); it will then be a mesh swap.

## Update 2026-10-11 17:10Z: Astra StrawberryBeds v005 applied (fresh-reopen verified)

- **Re-layout check:** the 15:42Z bed re-layout passed a fresh reopen (map fafde8f0, `PazFarm_Detail` 3,905, all counts match).
- **Imported** under `<clone>/PazFarm/StrawberryBeds_v005/`:
  - 24 textures and 8 material instances;
  - 4 meshes with Nanite on, each with its authored lowest LOD as LOD1, FBX normals imported. The meshes are tile variants A, B and C plus the end cap `SM_PazFarm_StrawberryBedEnd`.
  - **Tool fix:** `apply_astra_rev.py` now binds material slots AFTER the lowest-LOD import, because the v005 `MulchDistant` slot exists only in that LOD. It also accepts the manifest key `base_model`.
- **Placed** with `Tools/straw_beds.py place_variants` on the same 2,478 ground-fitted positions:
  - variants A 809, B 824, C 845, never the same twice in a row;
  - 106 continuous rows, closed by 212 end caps;
  - a local-Y stretch (median 1.0003, max 1.0044) so pitched tiles end exactly on the next start.
  - Before-state receipt: `receipts/STRAW_BEDS_BEFORE_20261011T170157Z.json` (`straw_beds.py step revert`).
- **Map:** saved sha `41c76dfb0e2343c953dea9479ec6cfbf13008e7cfda1d82b5ead1bd196daa9db`.
- **Fresh reopen** (PID 3180): `PazFarm_Detail` 4,117 (all match), every part Static, nothing detached, PCG 112,285, nothing dirty. Receipt: `receipts/VERIFY_CLONE_V2_strawberry_v005_41c76dfb.json`.
- **Captures:** `straw_v005fresh_*.png` (close, 15 m, 60 m).
- **Play mode** (`receipts/PIE/PIE_strawberry_v005*.json`), frame time (GPU in brackets):

| View | Now | Before |
|---|---|---|
| Farm | 19.7 ms (GPU 18.8) | 18.8 ms (GPU 17.6) |
| Village | 13.7 ms | 13.6 ms |
| Forest | 8.5 ms | 8.7 ms |
| Wide, GPU only | 37.8 ms (38.4 on a repeat run) | 34.6 ms |

  - **Wide-view frame-time stalls:** both wide-view runs ended with about 19 frames of exactly 333 ms each, with the render thread waiting and GPU and game thread normal. This is likely editor idling (the throttle pattern), not rendering cost. The normal wide frames average 39 ms.
- **Seen, not fixed (outside this task):** from about 300 m at a low angle, one pale field south of the farm turns deep sky-blue. Close and overhead views of the same spot are normal ground, and a trace hits only the landscape. The likely cause is sky reflecting off ground that is too shiny at grazing angles. Captures: `straw_v005fresh_straw_60m.png` (right edge), `bluepatch_*.png`. Tool: `Tools/ray_probe.py`.

## Update 2026-10-11 17:40Z: one object per building on the clone (fresh-reopen verified)

**Aviv's decisions:**
- "Split on the clone now, and add it to the playbook and add a question on whether to change the generator later".
- HLODs: "Keep it without". The clone stays a fully loaded level without World Partition: no HLODs, Nanite at all distances, nothing streams or culls.

**Data:** `NewArea_.../Buildings_v2/compact_buildings_v2.py` builds `BUILDINGS_COMPACT.json` and `FOOTPRINTS.json` from the current run's receipt (sha 3437fab0...): 35,427 module and door instances plus 32 whole buildings, 591 footprints.

**Buildings** (`Tools/split_buildings.py`, now with a target switch, `clone_v2`):
- 35,459 of 35,459 parts matched to their building (worst 0.014 cm), giving 591 `Bldg_<osm>` actors (folder Buildings).
- Each actor holds its wall and window instances, its door as its own component, and whole native buildings as one mesh.
- `fix_attach`: all Static, 35,459 positions exact (0.0 cm).
- `remove`: 35,459 instances moved out of the 8 area-wide bank components.

**Shells** (`Tools/split_shells.py`, target `clone_v2`):
- The merged shell mesh (598,089 triangles) is split by footprint into 560 meshes under `<clone>/Buildings_v2/Shells/`: 559 buildings plus the unsupported building's own `Bldg_1042209923`.
- The shell total is 598,087: the build drops 2 zero-area triangles, the same as the trial.
- Materials are identical to the merged actor's (checked).
- The merged actor `..._buildings_1` was removed from the clone; the shared bake asset is untouched.
- **Tool fix:** the merged actor is now found by its mesh, because after a regeneration the label has a `_1` suffix. Before the fix, one saved state briefly had both shells (6c9ffabd); it was superseded within minutes.

**Saved map:** `7e3d06d61021d694f351dc079a0e2762e060ac51c7aa8dfbd69ff2848b965ca2`.

**Fresh reopen** (PID 38868, `receipts/VERIFY_CLONE_V2_buildings_split_7e3d06d6.json`):
- 592 `Bldg_` actors holding 35,459 parts and 560 shells;
- all Static, none detached, no merged buildings actor;
- farm 4,117 and PCG 112,285 unchanged;
- nothing dirty.

**Captures:** `bldsplit_village_*.png`.

**Note:** after a reopen the editor builds a distance field for each new shell mesh (about 2 s each, cached afterwards), so play mode was measured after that.

**Open [D]:** should the generator bake one object per building by itself? That change is in the manager-owned sealed workflow; it is recorded in the playbook as a question for Aviv.

**Play mode after the distance fields finished (17:59Z, `receipts/PIE/PIE_buildings_split2.json`):**

| View | Frame time | GPU |
|---|---|---|
| Farm | 18.1 ms | 17.2 ms |
| Village | 12.6 ms | 11.7 ms |
| Forest | 8.5 ms | 7.1 ms |
| Wide | 35.2 ms | 34.2 ms |

- **Separate buildings:** no measurable cost; the village view is slightly faster than before (13.7 ms).
- **Earlier wide-view stall:** this wide run had no 333 ms tail. That supports reading the earlier one as the editor idling, not a cost of the beds.
- **First run after the reopen** (`PIE_buildings_split.json`): invalid. It ran while the distance fields were still building, so play mode did not render.
