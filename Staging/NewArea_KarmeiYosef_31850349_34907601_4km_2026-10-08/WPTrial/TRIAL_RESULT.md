# World Partition / one-object-per-building trial: result (2026-10-10)

Authority: Aviv, 2026-10-10:
- "Yes, let's do a trial on a copy of the clone."
- One object per building: "Can we trial it and make it reversible?"
- Trees: "an always loaded instancing HLOD, so every instance shows the tree's lowest LOD."
- Grass: excluded, but should appear when zooming in (future).

Everything below is on copies. The 4 km area, its PCG clone (6ccbaeb2) and all shared or vendor content are unchanged.
Labels: [M] measured.

## Maps

| Stage | Map | Kind | State |
|---|---|---|---|
| Copy | `/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/L_KarmeiYosef_31850349_34907601_4km_WPTrial` | non-World Partition | stage A, sha 3c40d409 |
| Converted | `.../L_KarmeiYosef_31850349_34907601_4km_WPTrial_WP` | World Partition | stage B, map file sha d8b2bfd4 |

## Stage A: one object per building (non-World Partition)

Tools: `Tools/split_buildings.py`, `Tools/split_shells.py`.

**Result [M]:**
- 592 actors `Bldg_<osm>`, folder Buildings: 559 assembled, 32 whole native and 1 retained generated shell.
- Each actor has:
  - a static `BuildingRoot`;
  - one instanced component per wall module mesh;
  - `Door`, its own StaticMeshComponent, ready to become an animated child later;
  - `Building` (whole native mesh) or `Shell`.
- `Shell` is a per-building mesh `<trial>/Buildings/Shells/SM_Shell_<osm>`. It holds the floor and roof slabs, corner closures, door lintels and infills, split from the old merged mesh by footprint. UVs and materials are exact.

**Checks [M]:**
- 35,459 instances placed exactly (worst 0.0 cm) after save and reload.
- Shell triangles 598,087 = original.
- Town views identical before and after.

**Files [M]:**
- One map file of 190 MB.
- 560 shell mesh files, 18 MB.
- No per-building files otherwise.
- Save 8–15 s.

**Why the shells need files:** only 26% of the 55,367 generated parts are rectangles, so stretched cube instances cannot reproduce them.

## Stage B: World Partition with HLOD

**Conversion** (`WorldPartitionConvertCommandlet -ConversionSuffix`) [M]:
- 19 min (landscape partitioning 18.5 min), peak 16.7 GB RAM, 0 errors.
- Runtime hash: WorldPartitionRuntimeHashSet.
- 64 landscape streaming proxies.

**Files [M]:**
- Map file 14 KB.
- External actor files: 1,478, 310 MB = 736 converted actors + 256 PCG cell actors + 486 HLOD actors.
- One file per actor is default with World Partition. No setting to keep actors in the map was found for a World Partition level.
- These files exist only in the editor; cooked builds put actors back into the level.

**Save [M]:** first full save 988 packages in 68 s; later saves 257 packages in 14 s.

**Open [M]:** about 34 s to ready, with only non-spatial actors and HLODs loaded. Loading all 992 actors takes 3 s.

**Plants (PCG):**
- Partitioned into 256 cells of 256 m.
- 109,893 plants, against 112,891 unpartitioned (−2.7%), because sampling and pruning are per cell.
- Partitioned generation needs `PCGComponent.generate(True)`; `generate_local` does nothing for the cells.

**HLOD:**
- The converter's hash set only builds HLODs for layers in its partition HLOD setups: its own `..._HLODLayer_Instanced` (grid, 256 m cells, 768 m range) and `..._HLODLayer_Merged` (always loaded). Python cannot edit those setups.
- So the `Merged` asset was switched to **Instancing** (Nanite allowed, no instance filtering) and used for vegetation and landscape. That gives the requested **always-loaded instancing HLOD**.
- Buildings use the grid `Instanced` layer, which chains into the persistent layer.
- HLOD build: 486 HLOD actors in 48 s, 0 errors [M].

**Streaming check [M]:**
- Only a 500 m region around the farm was loaded (66 actors); 1,337 were unloaded.
- In the unloaded regions:
  - the forest 3 km away shows its trees with crowns and shadows;
  - trees at 400 m still read;
  - the village buildings all show;
  - the ground shows as the simplified landscape HLOD.
- Captures: `receipts/Captures/wpv_b_*.png`.

**Seen:**
- The landscape HLOD ground is blurrier than real terrain.
- Next to unloaded cells the always-loaded road mesh can float slightly above the simplified ground. At runtime the cells near the camera are loaded.
- One STF tree type reads sparser through its HLOD instance at close range.

**Gotchas:**
- Setting an Instancing layer to editor `FORCE_LOADED` opens a modal "Warning: Loading Instancing HLOD Layer". It must be accepted, or the Python call blocks.
- The first save after partitioned PCG generation leaves the 256 cells dirty again; a second save is clean.

## Still open

- The generator (sealed, manager-owned) assumes one map file and loaded actors. See WP_HLOD_ASSESSMENT_DRAFT.md section 2.
- Per-building output at bake time (route a) is still a manager decision.
- Props, roads and sidewalks are still 4 km-wide always-loaded actors.
- Aviv's zoom-in grass request.
- Astra v003: pine with a robust lowest LOD, and a far-robust strawberry bed.


## Update 01:15Z: verification corrections (all [M])

**1. "Always loaded" was not true at first.**
- Every HLOD actor came out spatially loaded. The converter's three HLOD setups were:
  - `HLODLayer_Instanced` on grid 1;
  - `HLODLayer_Merged` on grid 2, holding vegetation and landscape;
  - an empty "Non-Spatially Loaded HLODs" setup on a persistent partition.
- Fix: the vegetation/landscape layer was moved into the persistent setup. The engine refuses `set` in the editor ("Set commands not allowed in the editor"), so this was done through `RuntimePartitions` element `StructBase.import_text` (`Tools/hashset_move_layer2.py`), then saved and HLODs rebuilt.
- Proof: with the editor's default loading and nothing else loaded, 370 HLOD actors load by themselves. All are non-spatial on the persistent partition.

**2. The farm detail was missing from the HLOD.**
- PazFarm_Detail's HISMs were Movable, from the subobject default, and HLOD builders take only Static components. Only the barn and gates were in it.
- Fix: the whole chain set Static (`wp_setup.py step farm_static`).
- The always-loaded HLOD now holds all 2,192 farm instances.

**3. Always-loaded HLOD contents now:**

| Content | Instances / meshes |
|---|---|
| Vegetation | 109,893 (= every PCG plant) |
| Farm | 2,192 |
| Buildings (their HLOD1) | 36,019 parts |
| Landscape | 64 simplified meshes |

The finer building HLOD0 (116 actors) streams on grid 1.

**4. Trees use Nanite, not their lowest LOD.** Nanite is allowed in the layer, so the Nanite trees render at full Nanite detail in the HLOD, better than a lowest LOD. Non-Nanite plants show their lowest LOD:
- `bush01` and the grass bushes are cards (42 and 16 triangles), seen as small pale-green tufts;
- the thickets, creosote, elderberry and grass patch are real geometry.

Scrub captures from an HLOD-only region: `receipts/Captures/hscrub_b_*.png`. If Aviv wants exactly "lowest LOD" for every tree, set `disallow_nanite` on the layer.

**5. Not tested:**
- runtime streaming in PIE or standalone, including whether the always-loaded HLOD hides near the camera or doubles the trees;
- frame time and memory. One object per building replaced 68 instanced groups with about 2,700 non-Nanite building components, the main runtime question.

**6. Files now:**
- 1,478 external actor files, 311 MB;
- trial folder 568 files, 199 MB;
- 6 external object files;
- plus the converter's `L_..._WPTrial.ini` inside Content.

Nothing else was written outside the trial folders, and no DataLayers folder was created. Do not `git add` these unless the trial should be kept.

## Play-mode test (2026-10-10 08:22-08:38Z; Aviv: "Play-mode test first"; far trees "Force the lowest LOD")

Changes before the test (trial, plus the clone's own vegetation copies):
- **Far trees at their lowest LOD:** `disallow_nanite` is on in the always-loaded vegetation layer.
- **Real-geometry lowest LODs** (`Tools/lowest_lod.py`, before-state `receipts/LOWEST_LOD_BEFORE.json`):
  - The STF trees' lowest LOD was a 40-triangle dead-tree card; the small pines' was a 46-triangle card.
  - The vendor-pine copies had a single 8.9k level, about 122M triangles for 13.8k far pines.
  - These 8 area-owned copies in `<clone>/Vegetation/Meshes` were given automatic reduced LODs from LOD0, with no cards. The clone still renders them through Nanite, so only their non-Nanite path changed.
- **Ground:** Aviv asked why it looked low quality; the answer is the landscape HLOD stand-in. In the trial the 64 landscape proxies are now always loaded (no landscape HLOD), so the ground is full quality everywhere.
- **HLOD rebuilt:** 423 actors.

Method: Play In Editor, DefaultPawn moved to 4 fixed views (farm, village, forest, wide), 10 s for streaming, HighResShot, then an 8 s `csvprofile`. Editor background throttling was off for the session only. These are editor numbers, GPU-bound, and indicative only; some CSV windows caught few frames. Memory was not captured.

| View | Clone (68 groups) | One object per building (no WP) | WP + HLOD (far trees lowest LOD) |
|---|---|---|---|
| Farm | 17.5 ms, 2,127 draws | 17.2 ms, 3,400 draws | 19.2 ms, 3,836 draws |
| Village | 13.8 ms, 1,522 | 12.6 ms, 3,143 | 13.9 ms, 3,964 |
| Forest | 8.4 ms, 848 | 9.5 ms, 1,441 | 8.9 ms, 1,667 |
| Wide (whole area) | 24.4 ms, 3,580 | 24.5 ms, 6,287 | 32.2 ms, 6,641 |

**Streaming (WP):**
- Standing anywhere, the 307 always-loaded HLOD actors are present, and only nearby cells load.
- Where real content is loaded, the matching HLODs hide, so nothing is doubled: 8 hidden at the farm, 34 at the village, 23 at the forest, 0 in the wide view.
- Screenshots: `receipts/Captures/PIE_wp3_*.png`, `PIE_clone_*`, `PIE_perbldg_*`. CSVs: `receipts/PIE/`.

**Reading:**
- One object per building roughly doubles draw calls, but frame time did not change measurably here.
- WP + HLOD costs nothing close up. The always-loaded lowest-LOD (non-Nanite) far vegetation costs about +8 ms GPU in the whole-area view. That is the price of "lowest LOD"; the previous Nanite-allowed setting would likely cost less.
