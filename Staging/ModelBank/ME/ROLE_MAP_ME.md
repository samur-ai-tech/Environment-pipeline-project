# ME1 proposed generator role map

**Evidence state:** proposal from files and installed documentation only. Every asset is **available in bank, staged**; none is qualified, generator-connected, generated, visually verified, or accepted.

## Installed vendor contract used

| Proposed role | What the installed vendor documentation establishes | What remains unknown |
| --- | --- | --- |
| CityBLD whole-building static Prefab | A District assigns Land Uses to parcels; a Land Use can spawn a modular Building Style, a static Prefab, or nothing. CityBLD also exposes **Place Prefabs**. (`Plugins/WorldBLDMCPToolset/Docs/CityBLDToolset/README.md:45-47,78-88`) | The installed docs do not state the required Prefab class/wrapper, component restrictions, origin, local forward axis, parcel-footprint behavior, collision contract, or Land Use weighting fields. The detailed Prefab/Land Use guides linked at lines 96-105 are absent. The Neoclassical, Arab low-rise, and slum labels below are project proposals, not vendor taxonomy. |
| RoadBLD PropSpawner | A PropSpawner repeatedly places props along a road; documented examples are lights, trees, and bollards. RoadBLD world convention is centimetres, +X forward, +Y right, +Z up. (`Plugins/WorldBLDMCPToolset/Docs/RoadBLDToolset/README.md:30-33,112-115`) | Accepted asset/class type, prop-local axis, base pivot, side/curb offset, spacing, collision, sockets, and light-component support are unknown. The linked PropSpawner guide is absent. The world-axis convention does not prove a mesh-local-axis contract. |
| RoadBLD RoadModule alternative | A RoadModule is edge-following geometry swept along a spline; examples include curbs, barriers, and rails. (`RoadBLDToolset/README.md:112`) | Module cross-section, endpoint, pivot, axis, length, and seam requirements are unknown from installed docs. This matters for H0025/H0060 if they are continuous barriers rather than isolated props. |
| PCG / controlled prop placement | The RoadBLD reference kit includes sample PCG graphs, while the installed WorldBLD toolset can only inspect existing PCG volumes. (`RoadBLDToolset/README.md:16-19`; `WorldBLDToolset/README.md:3-7,20-25`) | No installed vendor document defines mesh inputs, pivot, attachment, density, exclusion, collision, slope, tags, metadata, or placement-facing requirements. |
| Vehicle placement | No vehicle-placement contract was found in the installed vendor docs. | Generator requirements are unknown. H0039 is therefore proposed for manual placement only, not generation. |
| PCG vegetation scatter | No installed vendor document defines a vegetation-mesh contract. | Base pivot, LOD/Nanite, foliage/wind material, collision, density, slope, scale variation, and biome filters are unknown. |

The CityBLD modular `BuildingMesh` contract at `CityBLDToolset/README.md:51-69` applies to facade modules, not automatically to these whole-building Prefabs. It requires +X module width, +Z up, front +Y, a lower-left/back-plane origin, rectangular X/Z perimeter, and edge-to-edge bounds. ME1 contains no proven regional modular set.

## Asset proposals and specific risks

| ID | Asset | Proposed generator role / grouping | Specific pre-connection risk |
| --- | --- | --- | --- |
| H0013 | Building 04 | CityBLD static Prefab; Land Use group **Neoclassical** | 48.684 m measured height is outside the supplied house example; Prefab wrapper, parcel footprint, origin/front, and collision are unknown. |
| H0014 | Building 01 | CityBLD static Prefab; **Neoclassical** | 2,476,576 LOD0 triangles; Prefab and parcel-footprint contract unknown. |
| H0015 | Building 02 | CityBLD static Prefab; **Neoclassical** | 201,055 LOD0 triangles and 24.173 m height; Prefab contract unknown. |
| H0016 | Building 03 | CityBLD static Prefab; **Neoclassical** | 822,754 LOD0 triangles and 52.689 m measured Y extent; parcel fit and front/origin unknown. |
| H0905 | Arab_x1_fbx | CityBLD static Prefab; **Arab low-rise** | Original path is under `Export models-Need-to-fix`; one material/texture and rendered suitability remain unverified. |
| H0906 | Arab_x2_fbx | CityBLD static Prefab; **Arab low-rise** | Original path is under `Export models-Need-to-fix`; ground contact, front, and parcel footprint unknown. |
| H0907 | Arab_x3_fbx | CityBLD static Prefab; **Arab low-rise** | Original path is under `Export models-Need-to-fix`; ground contact, front, and parcel footprint unknown. |
| H0902 | Slum_k_fbx | CityBLD static Prefab; **slum** | Original path is under `Export models-Need-to-fix`; small-shack ground contact and parcel fit unknown. |
| H0903 | Slum_s_fbx | CityBLD static Prefab; **slum** | Original path is under `Export models-Need-to-fix`; ground contact, footprint, and front unknown. |
| H0904 | Slum_v_fbx | CityBLD static Prefab; **slum** | Original path is under `Export models-Need-to-fix`; ground contact, footprint, and front unknown. |
| H0896 | middle east buildings | CityBLD static Prefab; separate **Arab low-rise block/compound review** | 137.233 x 111.088 m bounds, 40 materials, 208,623 triangles, and a Need-to-fix source indicate a combined block; likely unsuitable as one parcel building without decomposition. |
| H0079 | Streetlight | RoadBLD PropSpawner | 3.693 m height is below the supplied 6-12 m example; base pivot, upright axis, curb offset, spacing, and functional light component are unknown. |
| H0082 | Streetsign | RoadBLD PropSpawner | Sign face direction, Arabic/local content, editability, installed height, base pivot, and curb offset unknown. |
| H0083 | Streetsign_001 | RoadBLD PropSpawner | Sign face direction, Arabic/local content, editability, installed height, base pivot, and curb offset unknown. |
| H0025 | Barrier | RoadBLD PropSpawner for discrete units; RoadModule review for a continuous run | Vendor docs classify continuous barriers as RoadModules; choose discrete versus swept use, then verify end seams/orientation or instance spacing. |
| H0060 | Metal_Barrier | RoadBLD PropSpawner for discrete units; RoadModule review for a continuous run | Same role ambiguity as H0025; endpoint fit, local axis, pivot, and repeat spacing unknown. |
| H0051 | Garbagebin | RoadBLD PropSpawner | Bins are outside the documented examples; sidewalk clearance, base pivot, facing/random rotation, and spacing unknown. |
| H0081 | Streetpowerbox | RoadBLD PropSpawner | Frontage/facing and clearance constraints are unknown; indiscriminate repetition would be implausible. |
| H0094 | Woodenpole | RoadBLD PropSpawner | 3.380 m measured height is short for an assumed utility pole; base pivot, spacing, and wire/attachment behavior unknown. |
| H0090 | Watertank | PCG or controlled prop placement | Roof versus ground support, base pivot, footprint, orientation, and collision filters unknown. |
| H0091 | Watertank_001 | PCG or controlled prop placement | Narrow 0.348 m footprint needs visual scale confirmation; support surface, orientation, and collision filters unknown. |
| H0042 | Foodcart | PCG or controlled prop placement | 155,520 LOD0 triangles; random scatter could obstruct a road/sidewalk, and facing/clearance rules are unknown. |
| H0043 | Foodcart_001 | PCG or controlled prop placement | Facing, sidewalk clearance, base contact, and controlled density unknown. |
| H0034 | Cart | PCG or controlled prop placement | Resting orientation, facing, ground contact, and clearance unknown. |
| H0046 | Foodcrate | PCG or controlled prop placement | Single versus stacked use, ground contact, random rotation, and overlap avoidance unknown. |
| H0058 | Gaz | PCG or controlled prop placement | The requested gas-prop interpretation is not established by vendor docs; upright placement and safety/context clearance unknown. |
| H0059 | Grill_ | PCG or controlled prop placement | Context/clearance, ground contact, and facing unknown. |
| H0089 | Tires | PCG or controlled prop placement | Resting orientation, overlap avoidance, grouping, and density unknown. |
| H0077 | Stones_Stack | PCG or controlled prop placement | Source report records persisted precision/triangulation repair; slope alignment, base contact, and overlap remain unknown. |
| H0650 | SM_AirConditioner | Controlled facade/roof prop placement, not generic ground scatter | Requires surface-normal attachment; source report records one collision mesh but old Unreal reports zero simple collisions. |
| H0039 | Destryoedcar | Manual vehicle placement; **not generated** | 3.171 m longest extent is below the supplied car example; wheel/ground contact, forward axis, lane alignment, and collision unknown. |
| H0636 | Acacia | PCG vegetation scatter | Base pivot, scale variation, slope/biome filters, foliage/wind, LOD behavior, and collision unknown. |
| H0647 | Nopal | PCG vegetation scatter | Base pivot, planted orientation, density, slope/biome filters, LOD behavior, and collision unknown. |
| H0958 | CoconutPalm | PCG vegetation scatter | Converted Unity source; source notes contain unresolved texture GUIDs. Base pivot, wind/foliage, LOD, collision, and biome rules unknown. |

