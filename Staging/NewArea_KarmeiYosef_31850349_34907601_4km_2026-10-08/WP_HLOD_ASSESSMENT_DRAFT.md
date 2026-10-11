# World Partition, HLOD and one-actor-per-building: assessment (DRAFT)

Draft, 2026-10-10, reviewed by the Karmei Yosef operator (section 5 updated with the measured vegetation fix). Read-only work: no editor or Houdini session was used and no project file was changed. Labels: **[M]** measured from files or from the given audit, **[D]** documented (URL), **[3P]** third-party or forum source, **[I]** inference.

## Summary for Aviv

1. Our areas are not World Partition (WP) maps: one map file, and almost every object spans the whole 4 km.
2. Switching WP on as-is gains almost nothing: an actor that covers 4 km is always loaded.
3. WP pays off only if output is cut into pieces (per building or tile), so distant pieces swap to cheap HLOD stand-ins.
4. 4×4 km with Nanite is small for WP, and no performance problem is measured yet. Gains would be easier editing and smaller files.
5. Our sealed generator scripts assume one map file, everything loaded and one Landscape. About a dozen checks would break or quietly go wrong.
6. Houdini Engine supports baking into WP, Data Layers and HLOD layers.
7. One actor per building: a manager generator change, or a post-bake clean-up script. Both are real work.
8. Trees: keep vegetation always loaded and out of HLOD, or use an Instancing HLOD only after checking every tree's last LOD. No cull distances.
9. Question for you: landscape grass disappears at distance by design. Does your rule cover it?
10. Recommendation: do not convert the real maps now. If you authorise it, run one measured trial on a copy of the 4 km PCG clone.

## 1. Why converting as-is gains little

- [M] 68 of 74 actors are ISM actors spreading one mesh over 4 km; 3 merged StaticMeshActors hold buildings, roads and sidewalks; the clone's PCG volume has 43 ISM components. All building prims share one `unreal_output_name`, hence one mesh (`geocity_city_module.py:559-562`).
- [D] Spatially loaded actors go into grid cells (https://dev.epicgames.com/documentation/en-us/unreal-engine/world-partition-in-unreal-engine), placed by bounding box by default, with "promotion of actors to upper grid levels" (https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UWorldPartitionRuntimeSpatialHas-).
- [I] Our 4 km-wide actors would sit at the top level and load together: no streaming, no meaningful per-cell HLOD.

## 2. Pipeline assumptions affected by WP + One File Per Actor (OFPA)

The `Content/Python` modules are sha-sealed, so any edit to them needs a manager reseal (`geocity_runtime_guard.py:56`) [M]. The Staging tools in row 10 are not sealed.

| # | Code (file:line) [M] | Current assumption | Under WP/OFPA |
|---|---|---|---|
| 1 | `geocity_editor_action.py:247-248`; `geocity_bank_workflow.py:1017-1026` | Chooses instantiate or regenerate by finding a *loaded* HoudiniAssetActor | If the HDA cell is unloaded, a **second HDA is instantiated** [I]. The HDA actor must be non-spatially-loaded. |
| 2 | `geocity_bank_workflow.py:873-890` | Obsolete-actor removal and the "no overlapping copies" check use `get_all_level_actors()` | That call sees only loaded actors. Unloaded old actors survive on disk while the check passes [I]. A load-all step is needed (`WorldPartitionBlueprintLibrary.load_actors/get_actor_descs`, https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/WorldPartitionBlueprintLibrary) [D]. |
| 3 | `geocity_bank_workflow.py:1001-1006`; `geocity_roadbld_workflow.py:623-625` | Dirty packages = the map plus cook leftovers | If external actor packages are already dirty at start (for example after an interrupted run), they are neither the map nor known cook leftovers, so generation is refused [I]. Loading regions alone does not dirty them [I]. |
| 4 | `geocity_bank_workflow.py:949-951, 980` | Saves the dependency closure only under `p['root']` | External actor packages live in the `__ExternalActors__` mirror, outside the root, so they are never saved by name [I]. |
| 5 | `geocity_bank_workflow.py:904`; `geocity_roadbld_workflow.py:1512-1516` | `save_map` / `save_packages([world.get_outermost()])` saves the area | With OFPA, actors live in their own packages. Whether these calls write them is **unverified**. Road actors could be left unsaved while the "map not dirty" check passes [I]. Must be measured in the trial. |
| 6 | `geocity_bank_workflow.py:407`; `geocity_roadbld_landscape.py:35, 42` | `actor.get_outermost()` equals the map package | For an external actor this probably returns its own package [I]. Needs a trial readback. |
| 7 | `geocity_bank_workflow.py:112-113` | Landscape equals its LandscapeProxy | Already **fails closed** on a partitioned Landscape (streaming proxies) [M]. Code exists that anticipates this. |
| 8 | `geocity_bank_workflow.py:882`; `geocity_roadbld_landscape.py:71-75` | Exactly one Landscape, fully loaded | WP splits it into streaming proxies (https://dev.epicgames.com/documentation/unreal-engine/landscape-overview) [D]. Sampling and painting need every proxy loaded [I]. |
| 9 | `geocity_bank_workflow.py:333-335` | Exactly 5 mesh outputs, 1 landscape, 1 instancer | Breaks if output is split per building (route a) [I]. |
| 10 | `geocity_bank_workflow.py:429`; `Tools/create_area.py:120`; `promote_profile.py:13`; `Tools/readback_area.py:22` | The sha256 of one `.umap` proves the saved area | With OFPA, actors leave the `.umap`. Receipts need a hash manifest over all external actor files [I]. |
| 11 | `geocity_editor_action.py:81-88` | Map dependency graph shows what the area references | The map no longer references actor content. This half is blind, but the referencer check (90-93) still fails closed [I]. |
| 12 | `geocity_roadbld_junctions.py:562-564` | Fixed actor names (`DynamicRoad_86`, `DynamicRoadNetwork_1`) | WP/OFPA actor naming may differ [I]. |

The single-editor process checks (`geocity_bank_workflow.py:293-295`, `geocity_editor_action.py:236-240`) are unaffected [M]. RoadBLD (third-party) WP behaviour is unverified [I].

## 3. Houdini Engine for Unreal and WP

- [M] Installed: `Plugins/HoudiniEngine/HoudiniEngine.uplugin` is "3.0 - H22.0.429".
- [D] Houdini 20 notes list WP exports, OFPA support, Data Layer import/export, HLOD layer attributes and foliage instancing in WP: https://www.sidefx.com/docs/houdini/news/20/engine.html
- [D] Data Layers are assigned through groups `unreal_data_layer_<Name>`, and `unreal_create_data_layers=1` creates new layers. "Only actors directly created by Houdini" are assigned; foliage is not. https://www.sidefx.com/docs/houdini/unreal/worldpartition/datalayers.html
- [D] HLOD settings: `unreal_hlod_layer`, plus `unreal_uproperty_bEnableAutoLODGeneration`, `unreal_uproperty_ExcludeFromHLODLevels` and `unreal_uproperty_HLODBatchingPolicy` (0/1/2). https://www.sidefx.com/docs/houdini/unreal/worldpartition/hlodlayers.html
- [D] `unreal_split_attr` splits instancers into **components**, not actors. `unreal_bake_actor` / `unreal_bake_actor_class` name or choose the bake actor. https://www.sidefx.com/docs/houdini/unreal/attributes.html . The bake option "One Actor Per Component" creates an actor per output component: https://www.sidefx.com/docs/houdini/unreal/detailspanel.html . How `unreal_bake_actor` behaves on instancers is known only from a forum thread [3P]: https://www.sidefx.com/forum/topic/91357/
- [D] Conflict: `unreal_level_path` is listed on the attributes page but called deprecated on https://www.sidefx.com/docs/houdini/unreal/worldpartition/worldpartition.html . That page also gives `unreal_landscape_partition_grid_size` (default 4).
- [M] We bake with `bake_all_outputs()` (`geocity_bank_workflow.py:810`), replace-previous and remove-output on (537-540).

## 4. Unreal WP / HLOD facts for a 4×4 km area

- **Grid:** Epic's example is 256 m cells, 768 m loading range [D, WP page], i.e. 16×16 cells over 4 km [I]. Quoted defaults of 128 m / 256 m are third-party [3P].
- **HLOD layer types:** Instancing ("lowest LOD", "ideal for... trees and foliage"), Merged Mesh and Simplified Mesh [D] https://dev.epicgames.com/documentation/en-us/unreal-engine/world-partition---hierarchical-level-of-detail-in-unreal-engine . Approximated Mesh and Custom are named only in Simplygon's docs [3P].
- **HLOD requirements:** an HLOD layer, Static mobility and HLOD generation enabled. Build with Build > Build HLODs or the `WorldPartitionHLODsBuilder` commandlet. A layer can be Always Loaded [D].
- **Instancing builder settings:** `disallow_nanite` ("Nanite ignores forced LODs") and instance filtering by minimum area, extent or volume [D] https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/HLODBuilderInstancingSettings
- **PCG:** use Partitioned Generation (grid on the PCGWorldActor). Hierarchical generation requires partitioning, and nodes can assign HLOD layers [D] https://dev.epicgames.com/documentation/unreal-engine/using-pcg-with-world-partition-in-unreal-engine . Our clone's single PCG volume is not partitioned [M], so it would become one 4 km actor [I].
- **Conversion:** use Tools > Convert Level, or `WorldPartitionConvertCommandlet` with `-ReportOnly` and `-ConversionSuffix` [D, WP page]. [M] `Config/DefaultEngine.ini:33-34` already names this commandlet.
- **OFPA:** on by default with WP. Changelist tooling is described for Perforce [D] https://dev.epicgames.com/documentation/en-us/unreal-engine/one-file-per-actor-in-unreal-engine . [M] We use Git with LFS for `.uasset/.umap` (`.gitattributes`), with 24,343 tracked files. [I] Each regeneration would create and delete hundreds or thousands of LFS objects.

## 5. "Trees never vanish" under WP

- [M] No cull distances, max draw distances or CullDistanceVolume today (`receipts/VISIBILITY_AUDIT.json`). Paz Farm crown loss was fixed with Preserve Area and Astra's geometric leaves (v002).
- [M] Update 2026-10-10 (clone sha 6ccbaeb2, `receipts/NEVER_VANISH_SAVE.json`): the PCG stand-in trees (4 Modular_Rural_Cabin pines, 2 STF green trees, 2 STF small pines) now use **area-owned copies** in `<clone>/Vegetation/`:
  - Nanite is on with Preserve Area.
  - Leaf textures preserve alpha coverage.
  - Leaf clip is lowered to 0.12–0.15.
  - The STF copies own all their MIs, so vendor MIs never get the Nanite usage flag.
  - Vendor originals are unchanged; the STF dead-tree billboard LOD is no longer rendered in the clone.
- [M] Result: the forest keeps its crowns from 460 m overhead and at 300–400 m oblique. Beyond about 600–700 m the vendor pines still thin to pale trunks: their thin needle cards fall below a pixel, with or without Nanite (tested). The durable fix is a Nanite-friendly pine with solid geometric needle clusters, as Astra built for the farm trees, plus an HLOD or impostor for far range.
- [D] An Instancing HLOD uses the lowest LOD, so it would show those billboards.
- **Option A (recommended) [I]:** vegetation actors are non-spatially-loaded and excluded from HLOD. This is the same memory cost as today, and the rule is kept exactly.
- **Option B:** an Instancing HLOD layer that is Always Loaded, keeps Nanite allowed (`disallow_nanite` off), has all instance filter minimums at 0, and uses vetted last LODs. Unchecked minimums make plants vanish [D].
- In both options, keep instance cull distances and max draw distance at 0 [I].
- [D] Nanite Foliage (Voxelize, Assemblies) exists in UE 5.8 but is **Experimental**, and it discourages masked leaves: https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-foliage
- **Open question:** native landscape grass (`geocity_landscape_workflow.py:398`, and comment `geocity_bank_workflow.py:850-853`) is generated around the viewer and culls by design. It is not covered by HLOD. Does the rule include ground grass?

## 6. One actor per building

**Pros [I]:**
- Per-building select/edit/replace, real WP streaming and per-cell HLOD, a basis for later gameplay or destruction.

**Cons [I]:**
- About 600-2,000 actors per 4 km, each one an OFPA file and LFS object.
- Components multiply as buildings × distinct meshes per building, possibly into the thousands. Without Nanite, draw calls rise.
- Every gate in section 2 changes.

**Identity data available [M]:**
- `source_osm_id` on building prims (`geocity_city_module.py:559`; KY variant `geocity_city_module_4km_ky_v001.py:559`).
- `placement_id` and `source_osm_id` on module points (`:4685-4688`).
- Whole-building ids (`:4644`; KY `:4729`).
- Per-instance positions and osm ids in the bank receipt JSON (`:2471-2475`, `:4706-4708`, `:4723-4725`).
- These ids do **not** reach the baked components: `native_components` (`geocity_bank_workflow.py:634-635`) carries no osm id.

**Route (a), generator change via the manager:**
- Per-building `unreal_output_name` instead of one per area (`:562`).
- A composite split key. `unreal_split_attr` names one attribute and is already `assembly_material_signature` (`:6054`; KY `:6140`).
- Bake "One Actor Per Component", or `unreal_bake_actor` [3P].
- Reworked gates (rows 2-10 of section 2).
- This is clean and repeatable, but it is a sealed-code change.

**Route (b), post-bake regrouping in Unreal:**
- Move ISM instances into per-building actors by matching transforms against the receipt.
- It cannot split the single merged buildings mesh, so it is **partial**.
- It must re-run after every regeneration, and it conflicts with the lifecycle's own ownership ledger (`previous_baked_paths`) [I].

## 7. Recommendation and staged plan

**Recommendation:** do not convert the real maps now. Decide after one measured trial.

**One actor per building:** worth doing only if WP is adopted. If it is, prefer route (a), because route (b) cannot split the merged buildings mesh and must re-run after every regeneration. Start neither route before the trial.

**Stages:**

0. This assessment. You decide two things: the grass scope, and whether to authorise a trial.
1. **Trial on a COPY of the 4 km PCG clone.** AGENTS.md forbids pilots and test maps, so this needs your explicit authorisation and its own assignment record (PID, map, writable scope, endpoint).
   - Run the convert commandlet with `-ReportOnly`, then with `-ConversionSuffix`. The commandlet is an `UnrealEditor` process, and other sessions' single-editor guards would count it, so run it only while no GeoCity generation is in progress.
   - No generator run on it.
   - Set vegetation non-spatially-loaded and build HLODs for the rest.
2. If the trial shows value, write a brief to the manager covering:
   - per-building output keys;
   - WP-aware lifecycle: load-all, external-package save closure, manifest receipts, HDA always loaded, Landscape-proxy authority;
   - reseal.
3. One real retained regeneration on a WP area.

**Trial measurements:**
- Cost: map open time (full vs region load), editor and standalone memory, GPU frame time at the fixed `cameras_ky4*.json` cameras, external-actor file count and bytes, named-save time, Git/LFS delta for one edit, HLOD build time.
- Correctness: every external package saved and present after a fresh reopen; Landscape-proxy seams and grass.
- Trees: crowns at 250 m, 1 km, 2 km and 4 km, plus a fly-through across cell boundaries. No tree, trunk or leaf may vanish.

**Risks:** the table in section 2, section 5, and whether the project rules allow the trial copy.
