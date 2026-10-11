# Paz Farm Blender delivery — DONE

Date: 2026-10-08. Status: modelling and offline verification complete.

Delivered **26 FBX meshes, 9 editable Blender family files, 117 original PNG textures, and one PNG preview per asset with a 1.8 m human scale figure**. Additional structure assembly views and a strawberry detail view are included. Open [INDEX.html](INDEX.html) to browse the previews, or use [MANIFEST.json](MANIFEST.json) for sizes, pivots, materials, texture provenance, budgets and hashes.

All task files were written inside this AstraModels folder. Unreal, Content, maps, the bank, Houdini and git were not opened or changed.

## Delivered assets

Dimensions below are measured Blender X / Y / Z extents in metres, including overhangs. They are not always the modular placement pitch. The barn footprint is 20 x 12 m; the roof overhang makes its full geometry wider. Strawberry bed height includes plants above the 0.25 m raised bed. Fence panel pitch is exactly 3 m despite its start post extending around the pivot.

| Asset | Width x depth x height (m) | LOD0 triangles |
|---|---:|---:|
| `SM_PazFarm_Avocado_A` | 5.5 x 5.25 x 5.8 | 57,884 |
| `SM_PazFarm_Avocado_B` | 5.9 x 5.45 x 6.4 | 57,884 |
| `SM_PazFarm_Avocado_C` | 5.15 x 5.4 x 5.4 | 57,884 |
| `SM_PazFarm_Lemon_A` | 3.25 x 3.1 x 3.45 | 56,556 |
| `SM_PazFarm_Lemon_B` | 3.5 x 3.25 x 3.8 | 56,556 |
| `SM_PazFarm_Orange_A` | 3.65 x 3.35 x 3.65 | 57,012 |
| `SM_PazFarm_Orange_B` | 3.2 x 3.05 x 3.3 | 57,012 |
| `SM_PazFarm_StrawberryBed_4m` | 0.8 x 4 x 0.442 | 17,748 |
| `SM_PazFarm_LowTunnel_4m` | 1.2 x 4 x 1 | 2,560 |
| `SM_PazFarm_NetHouse_Bay_8x4` | 8 x 4 x 4 | 218 |
| `SM_PazFarm_NetHouse_Side_4` | 4 x 0.012 x 4 | 114 |
| `SM_PazFarm_NetHouse_Door` | 4 x 1.639 x 4 | 364 |
| `SM_PazFarm_NetHouse_Bay_8x4_Black` | 8 x 4 x 4 | 218 |
| `SM_PazFarm_NetHouse_Side_4_Black` | 4 x 0.012 x 4 | 114 |
| `SM_PazFarm_NetHouse_Door_Black` | 4 x 1.639 x 4 | 364 |
| `SM_PazFarm_NetHouse_Post_4m` | 0.08 x 0.08 x 3.96 | 44 |
| `SM_PazFarm_NetHouse_ClosureBeam_4m` | 4 x 0.04 x 0.04 | 44 |
| `SM_PazFarm_NetHouse_ClosureBeam_8m` | 8 x 0.04 x 0.04 | 44 |
| `SM_PazFarm_Greenhouse_Tunnel_9x4` | 9 x 4 x 4.5 | 960 |
| `SM_PazFarm_Greenhouse_End` | 9 x 0.193 x 4.5 | 330 |
| `SM_PazFarm_Greenhouse_EndArch` | 9 x 0.07 x 4.5 | 740 |
| `SM_PazFarm_Barn` | 20.57 x 12.585 x 8.113 | 17,168 |
| `SM_PazFarm_Fence_Mesh_3m` | 3.039 x 0.075 x 2 | 1,936 |
| `SM_PazFarm_Fence_Post` | 0.096 x 0.096 x 2 | 220 |
| `SM_PazFarm_Fence_Corner` | 0.752 x 0.752 x 2 | 300 |
| `SM_PazFarm_Gate_Double_6m` | 6 x 0.138 x 2 | 3,664 |

## Defaults and documented adaptations

- Avocado A/B/C, lemon A/B, orange A and smaller-fruited clementine B are delivered. The trees have branch/trunk geometry, individually curved masked leaves and scattered fruit. Plants have no collision and no wind.
- The barn uses the authorized light-grey corrugated-metal default. Its appearance is not a verified reconstruction of the real barn; no ground photograph was supplied.
- Net-house Bay, Side and Door use the exact handoff names for the white defaults, plus `_Black` alternatives. Roofs are flat and 4 m high.
- For correct 2D tiling, each net bay owns one leading-corner post and its leading/left rails. Separate Post, ClosureBeam_4m and ClosureBeam_8m parts close the outer edges. Greenhouse_EndArch closes the last greenhouse section. These four additions are needed to form complete assemblies without duplicated shared supports. The exact placement formulas are in [structures_assembly.md](Reports/structures_assembly.md).
- Strawberries are supplied as open 4 m raised beds with separate optional low-tunnel film and hoops. The bed can also be placed beneath the net houses. The low tunnel's optional terminal hoop is exposed in its source parameters.
- The unknown grey-purple rows were not assigned a species; the handoff provides no crop default or listed mesh for them. Tree species locations and the farm layout remain the receiving operator's placement work.

## Verification performed

[VALIDATION.json](Reports/VALIDATION.json) records a fresh Blender process reopening all 9 sources and separately reimporting all 26 FBXs. All checks passed: source unit scale 1.0, real-size export roundtrip, ground/module pivots, one render mesh per FBX, expected UCX objects, UV0, finite vertices/normals, zero zero-area triangles, per-asset triangle budgets, texture references and preview presence. Measured triangle range for trees is 56,556–57,884, below the 60,000 limit; barn is 17,168/30,000; all kit pieces are below 5,000; strawberry bed is 17,748/20,000.

All source textures resolve locally and are 1024 x 1024 pixels. All asset previews were visually inspected across the modelling jobs. Strawberry/low-tunnel end-boundary matching and post/arch ownership are recorded in the family reports. This is offline model/export verification; native Unreal import, materials, collision behaviour, placement, saving and regeneration were not performed.

## Import information for the receiving operator

Sources use metres with unit scale 1.0. FBX uses Apply Scalings: FBX Units Scale, global scale 1.0, forward -Y / up Z. Source front is -Y, with the handoff's intended +X Unreal front after axis conversion. A source metre represents 100 Unreal centimetres. Verify importer axis handling against a known module before placement.

Connect BaseColor as sRGB; Normal and ORM as linear/Non-Color. ORM channels are R=AO, G=roughness, B=metallic. Normals are OpenGL +Y; enable green-channel inversion for the DirectX convention. Use BaseColor alpha for masked two-sided leaves/net and translucent two-sided film. FBX material import does not reproduce the complete shader node graph automatically. The supplied PNG maps and manifest define the materials. Named UCX boxes are provided for barn, fence/gate and structure supports; no plants collision.

## Changing the defaults

The nine `.blend` files are split by family: Avocado, Lemon, Orange, Strawberry, LowTunnel, NetHouse, Greenhouse, Barn and Fence. Variants share their intended local origins; hidden alternative objects can be revealed in the Outliner. Edit or rescale the appropriate source, or change dimensions, counts, colours and deterministic seeds in the parameter sections of `Scripts/build_trees.py`, `build_strawberries.py`, `build_structures.py` and `build_barn_fence.py`. Parameters are also recorded in source scene/object properties and family reports. Rebuilding a family replaces its outputs within AstraModels. `Scripts/paz_common.py` supplies the shared PBR/export/preview helpers.

The provided aerial image was used only for context. Every model and texture is original procedural artwork, recorded as CC0-1.0; no satellite imagery or third-party pixels were used in textures. No external reference was needed to build these authorized defaults.

## Remaining work outside this assignment

The Karmei Yosef operator still imports, wires native materials, places and verifies these assets. Real-farm visual matching awaits any later barn/net/field identification from Aviv. No requested modelling item is left undelivered.
