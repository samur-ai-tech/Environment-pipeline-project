# CityBLD Toolset

Editor AI toolset for inspecting and lightly editing a "CityBLD" procedural city (city blocks, parcels and
modular buildings, usually traced along RoadBLD roads). It is exposed through the ToolsetRegistry / Model
Context Protocol server (`list_toolsets`, `describe_toolset`, `call_tool`), the same mechanism used by
RoadBLDToolset, TwinBLDToolset and WorldBLDToolset.

| Toolset | Purpose |
| --- | --- |
| `CityBLDToolset.UCityBLDDiscoveryToolset` | Read-only: city context, presets (districts, land uses, building styles), blocks, parcels, buildings, issue checks |
| `CityBLDToolset.UCityBLDToolset` | List/describe buildings and blocks, list Building Style assets, assign a style, regenerate a building |

**There is no "create" tool yet.** Unlike RoadBLDToolset, nothing here lays down new city blocks, districts or
buildings — only inspecting existing ones and reassigning a building's style. To add new blocks or buildings,
guide the user to the manual UI (see UI overview below).

## Agent workflow

1. `GetCityContext()` first. It summarizes block/parcel/building counts, districts and styles in use, available
   presets, **license state**, and running jobs. Check `bCanEdit`/`LicenseState`/`LicenseMessage` here before
   attempting any mutating call — `SetBuildingStyle` and `GenerateBuilding` require a CityBLD license or active
   trial and fail otherwise.
2. Browse presets with `ListPresets(Kind, Query)` and read one with `DescribeDistrict`, `DescribeLandUse` or
   `DescribeBuildingStyle` (or `ListBuildingStyles` for a bare list of style class paths).
3. Inspect the level with `ListCityBlocks` / `DescribeBlock`, `ListParcels`, `ListModularBuildings` /
   `DescribeBuilding`. Use `Bounds` to scope large levels; results are capped with a `TotalCount` telling you if
   more exist.
4. Run `FindCityIssues` before and after edits — it flags blocks without a district or parcels, slow skeleton
   subdivision, bad outlines, overlapping blocks/buildings, parcels missing their buildings, and buildings not
   registered to a parcel, each with a suggested fix.
5. To restyle an existing building: `SetBuildingStyle(Building, StyleClass)` then `GenerateBuilding(Building)`
   to rebuild its meshes. Both are one undoable transaction each.
6. To add new blocks, districts or buildings, or to author a new Building Style, there's no tool call — walk the
   user through the toolbar tools in the UI overview below instead.

## Conventions and gotchas

- Most fields are centimeters; fields explicitly named `...Meters` (e.g. `AreaSquareMeters`, `HeightMeters`,
  `SidewalkWidthMeters`) are meters. Read field names carefully — the same struct often mixes both.
- Bounds and outlines are 2D in the XY plane (`FCityBLDBounds` ignores Z); area/centroid/overlap checks work the
  same way.
- Actor parameters take `{"refPath": "..."}` from a previous result, same convention as every other BLD toolset.
  Preset/class parameters take a `ClassPath` (the Blueprint generated-class soft path) from `ListPresets` or a
  `Describe*` call.
- A City Block's `District` decides how it subdivides into Parcels and which Land Use each parcel gets; a Land
  Use spawns a modular building with one of its Building Styles, a static Prefab, or nothing. Modular buildings
  can also be hand-placed independent of any parcel.
- Every mutating call is one undoable transaction and fails atomically; every mutating call also fails outright
  without a valid CityBLD license/trial, so surface `LicenseMessage` to the user rather than retrying.

### Modular Building mesh authoring contract

Apply this contract whenever an agent creates or replaces a `BuildingMesh` static mesh in Blender or Unreal:

- In Unreal local space, **+X is module width, +Z is up, and the facade/front faces +Y**. With this project's
  Blender-to-Unreal export convention, model the front toward **Blender -Y**. A sill is a front-only feature: place it on
  that side, then verify both its placement and the outward face normals after import. Apply transforms before export and
  recalculate outward normals after any mirror or negative scale.
- Put the origin at the lower-left corner of the back plane: imported bounds should have `Min X = 0`, `Min Z = 0`, and
  the back plane at `Y = 0` (allowing only normal floating-point tolerance).
- The complete left, right, top, and bottom perimeter must remain a sharp, perfect rectangle. Do not bevel or chamfer the
  module's outer boundary or corners. Bevels are safe only on internal/detail edges.
- Do not let a sill, frame, trim, molding, glass, collision mesh, or other feature exceed the intended X/Z rectangle.
  Facade details may project in depth toward Unreal +Y, but a sill must stop at the left and right module boundaries.
- `AModularBuildingActor` reserves and advances modules using the imported static mesh's bounds, not the visual wall
  rectangle. Even a small X/Z overhang changes the measured module size and creates seams or gaps in the final building.
- Before using the mesh in a Building Style, inspect the imported Unreal bounds and place two unscaled copies exactly one
  intended module width apart. Their rectangular boundaries must meet edge-to-edge without a gap, overlap, or rounded
  outside corner, and the facade details and normals must face +Y.

## UI overview (for guiding a human user)

The CityBLD viewport toolbar has four main tools, plus an overflow menu and right-click context menus — point
users here for anything the toolset can't yet do (new blocks, districts, buildings, or authoring new presets):

| UI entry | What it's for |
| --- | --- |
| Toolbar → **Add Blocks** | Pick a District, draw new city blocks in-viewport; parcels and buildings auto-fill |
| Toolbar → **Edit Blocks** | Select and adjust the layout/style of existing blocks |
| Toolbar → **Place Prefabs** | Pick a building or city Prefab and place it directly |
| Toolbar → **Draw Building** | Pick a Building Style, click 3+ points to draw a hand-placed building footprint |
| Toolbar overflow → **Convert Buildings to Meshes/Prefabs** | Turn generated buildings into plain actors/Prefabs |
| Toolbar overflow → **CityBLD Settings** | Project-wide defaults: collision, materials, mesh quality |
| Right-click a City Block | Change District, Sidewalk Preset/Width, Regenerate, Edit/Delete |
| Right-click a Modular Building | Change Building Style, Ground Floor Override, Height, Sign Text, Collision, Edit Shape, Regenerate (single or all), Build/Preview HLOD, Batch Building Edit (multi-select) |
| **Building Mesh Creator** window | Author one facade module (a BuildingMesh asset) |
| **Building Style Creator** window | Assemble a full Building Style with live preview |
| **Ground Floor Creator** window | Turn a BuildingMesh into a Ground Floor Type override |

## Further reading

These guides live in the CityBLD product plugin, not this toolset — paths are relative to this file.

| Doc | Covers |
| --- | --- |
| [`../CityBLD/DISTRICT_REFERENCE.md`](../CityBLD/DISTRICT_REFERENCE.md) | Full parameter reference for a District (subdivision + land use weighting) |
| [`../CityBLD/LAND_USE_REFERENCE.md`](../CityBLD/LAND_USE_REFERENCE.md) | Full parameter reference for a Land Use and what it spawns |
| [`../CityBLD/BUILDING_STYLE_REFERENCE.md`](../CityBLD/BUILDING_STYLE_REFERENCE.md) | Full parameter reference for a Building Style |
| [`../CityBLD/MODULAR_BUILDING_GUIDE.md`](../CityBLD/MODULAR_BUILDING_GUIDE.md) | The Modular Building actor and its context-menu workflow end to end |
| [`../CityBLD/BUILDING_STYLE_CREATOR_UI_GUIDE.md`](../CityBLD/BUILDING_STYLE_CREATOR_UI_GUIDE.md) | Using the Building Style Creator window |
| [`../CityBLD/BUILDING_MESH_CREATOR_UI_GUIDE.md`](../CityBLD/BUILDING_MESH_CREATOR_UI_GUIDE.md) | Using the Building Mesh Creator window |
| [`../CityBLD/GROUND_FLOOR_CREATOR_UI_GUIDE.md`](../CityBLD/GROUND_FLOOR_CREATOR_UI_GUIDE.md) | Using the Ground Floor Creator window |
| [`../CityBLD/BUILDING_SIGN_TEXT_GUIDE.md`](../CityBLD/BUILDING_SIGN_TEXT_GUIDE.md) | Building sign text (see MODULAR_BUILDING_GUIDE.md) |
| [`../CityBLD/CITYBLD_PREFAB_GUIDE.md`](../CityBLD/CITYBLD_PREFAB_GUIDE.md) | Authoring a CityBLD Prefab and hooking it to Districts/Land Uses |
| [`../CityBLD/CONVERT_MODULAR_BUILDINGS_GUIDE.md`](../CityBLD/CONVERT_MODULAR_BUILDINGS_GUIDE.md) | The toolbar's Convert Buildings to Meshes/Prefabs tool |
| [`../CityBLD/BakeCityBlocksToMeshes_ArtistGuide.md`](../CityBLD/BakeCityBlocksToMeshes_ArtistGuide.md) | Baking a finished block into plain, export-ready actors |
| [`../CityBLD/CITYBLD_HLOD_ARTIST_GUIDE.md`](../CityBLD/CITYBLD_HLOD_ARTIST_GUIDE.md) | Building HLOD/proxy meshes for World Partition performance |

CityBLD blocks are usually traced along RoadBLD roads, and TwinBLD can generate both from real-world data — see
[`../RoadBLDToolset/README.md`](../RoadBLDToolset/README.md) and [`../TwinBLDToolset/README.md`](../TwinBLDToolset/README.md).
For whether CityBLD itself is installed/enabled, see [`../WorldBLDToolset/README.md`](../WorldBLDToolset/README.md).

## Tests

Automation tests live under `AI.Toolsets.WorldBLD.CityBLDToolset`.
