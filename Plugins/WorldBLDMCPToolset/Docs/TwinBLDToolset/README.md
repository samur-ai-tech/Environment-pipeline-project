# TwinBLD Toolset

Editor AI toolset that lets agents place a level at a real-world location and inspect/fix the real-world content
(roads, buildings, landscape) that TwinBLD generates there. It is exposed through the ToolsetRegistry / Model
Context Protocol server (`list_toolsets`, `describe_toolset`, `call_tool`), the same mechanism used by
CityBLDToolset, RoadBLDToolset and WorldBLDToolset.

| Toolset | Purpose |
| --- | --- |
| `TwinBLDToolset.UTwinBLDLocationToolset` | Geocoding, the level's geo origin, geo↔world conversion, sun position |
| `TwinBLDToolset.UTwinBLDSceneToolset` | Inspect and fix content TwinBLD already generated |

**There is currently no agent tool for the import itself** — fetching OpenStreetMap data and generating roads,
buildings, landscape or parcels from it is only reachable through TwinBLD's manual editor UI (see UI overview
below). Set up the location with `TwinBLDLocationToolset`, then hand the user to that UI for the actual import,
and use `TwinBLDSceneToolset` afterwards to inspect or adjust what came in.

## Agent workflow

1. `GeocodePlace("Flatiron Building, New York")` to resolve a place name or address to coordinates. Search for
   specific places — never bulk-geocode a list (Nominatim is rate limited to one request per second; answers are
   cached 30 days).
2. `SuggestImportArea(Center or Bounds)` to size the area and see which tiles it covers, read-only.
3. `SetGeoOrigin(Origin, bDryRun=true)` first to see the impact, then `bDryRun=false` to apply. This sets the
   real-world location of world `(0, 0)`. Changing it after content already exists leaves that content
   misplaced and tags it stale — always dry-run when a level might already have generated content.
4. Import is manual: tell the user to open **Tools → Import Map Data** (also on the TwinBLD viewport toolbar),
   pick tiles, and run Generate Roads / Generate Buildings / Generate Landscape / Generate Parcels as needed —
   see the further-reading table below for which guide covers which pipeline.
5. After import, call `GetSceneContext()` for a summary (what's present, counts by type and tile, stale/untagged
   content, running jobs). Narrow down with `FindGenerated(Type, Bounds/Tiles, OsmTagFilter, height range)`, and
   `DescribeGeneratedActor` to see an actor's original OSM tags (only available when the source OSM file is
   still loaded in the import session).
6. Fix generated content: `SnapToLandscape` (buildings/roads onto the terrain after a landscape import),
   `DetectFacades` (recompute which building faces are street-facing after nearby roads change), and
   `EditBuildingFromReality` (apply height/levels/roof from real-world measurements, or add stepped tiers).
   Every edit is one undoable transaction.
7. `SetSunForLocation(DateTime, UtcOffsetHours)` to aim a directional light at the real sun position for the geo
   origin at a given date/time — useful once the scene is built and needs realistic lighting.

## Conventions and gotchas

- Geographic points are WGS84 decimal degrees: `{"lat": 40.7411, "lon": -73.9897}`. Boxes are
  `{"south", "west", "north", "east"}`. World positions are Unreal centimeters, Z up.
- The geo origin has a revision number that increments whenever it changes. Actors generated under an older
  revision are tagged stale (`FindGenerated`'s `bIncludeUntagged`/results and `GetSceneContext`'s
  `StaleActorCount` surface this) — re-run `SnapToLandscape` or regenerate rather than assuming positions are
  still correct after moving the origin.
- Generated actors carry tags an agent can filter or reason about: `TwinBLD.Type.<Type>` (Building, Road,
  RoadNetwork, CustomRoadShape, Parcel, Landscape, LandscapePCG, Satellite, Detail.*), `TwinBLD.Tile=<X>,<Y>`,
  and, when imported through the OSM pipeline, `TwinBLD.OSM=<way|relation|node>/<id>`. Modular buildings without
  these tags were hand-placed or came from another tool, not TwinBLD's import.
- Actor parameters take `{"refPath": "..."}` from a previous result, the same convention as every other BLD
  toolset. Heights in `TwinBLDSceneToolset` are meters; everywhere else world values are centimeters.
- TwinBLD sits on top of RoadBLD and CityBLD — imported roads become RoadBLD networks and imported buildings
  become CityBLD modular buildings, so `RoadBLDToolset` and `CityBLDToolset` tools also apply to them once
  generated.

## UI overview (for guiding a human user)

- **Tools → Import Map Data** (also a button on the TwinBLD viewport toolbar) opens the Map Data Importer: load
  an `.osm` file or fetch from a configured source, pick a tile area on the map canvas, and run the Generate
  Roads / Generate Buildings / Generate Landscape / Generate Parcels actions. This is the only way to bring new
  real-world content in today — point users here after `SetGeoOrigin`.
- Import behavior is customized by subclassing the style/preset mapper (OSM tags → RoadBLD presets and CityBLD
  Building Styles); see the beginner guide below if a user wants to change what gets generated rather than just
  where.
- Settings live in three places: **Project Settings → Plugins → TwinBLD** (project-wide defaults), a
  `TwinBLDLevelSettings` actor in the level (per-level overrides), and the importer window's own per-user state.

## Further reading

These guides live in the TwinBLD product plugin, not this toolset — paths are relative to this file.

| Doc | Covers |
| --- | --- |
| [`../TwinBLD/Docs/TwinBLDMapImporter_LandscapePipeline.md`](../TwinBLD/Docs/TwinBLDMapImporter_LandscapePipeline.md) | Terrain generation: per-tile elevation download, shared Landscape build/resample |
| [`../TwinBLD/Docs/TwinBLDMapDataImporter_RoadPipeline_ArtistGuide.md`](../TwinBLD/Docs/TwinBLDMapDataImporter_RoadPipeline_ArtistGuide.md) | Road generation: loading `.osm`, picking tiles, Generate Roads into RoadBLD networks |
| [`../TwinBLD/Docs/TwinBLDMapImporter_BuildingPipeline.md`](../TwinBLD/Docs/TwinBLDMapImporter_BuildingPipeline.md) | Building generation from parsed OSM data and selected tiles |
| [`../TwinBLD/Docs/TwinBLDMapImporter_ParcelPipeline.md`](../TwinBLD/Docs/TwinBLDMapImporter_ParcelPipeline.md) | Parcel/city-block generation from a loaded parcel shapefile (not OSM land use) |
| [`../TwinBLD/Docs/TwinBLDMapImporter_ReplicityMaps.md`](../TwinBLD/Docs/TwinBLDMapImporter_ReplicityMaps.md) | Alternate data source (maps.replicity.ai) for custom road shapes instead of local OSM |
| [`../TwinBLD/Docs/TwinBLDSettings.md`](../TwinBLD/Docs/TwinBLDSettings.md) | The three settings layers (project / level / per-user) controlling import and generation |
| [`../TwinBLD/Source/TwinBLDEditor/STREET_MAP_CUSTOMIZER_BEGINNER_GUIDE.md`](../TwinBLD/Source/TwinBLDEditor/STREET_MAP_CUSTOMIZER_BEGINNER_GUIDE.md) | Mapping OSM tags to RoadBLD presets / CityBLD Building Styles |

Roads and buildings TwinBLD generates are RoadBLD/CityBLD content — see
[`../RoadBLDToolset/README.md`](../RoadBLDToolset/README.md) and [`../CityBLDToolset/README.md`](../CityBLDToolset/README.md).
For whether TwinBLD itself is installed/enabled, see [`../WorldBLDToolset/README.md`](../WorldBLDToolset/README.md).

## Tests

Automation tests live under `AI.Toolsets.WorldBLD.TwinBLDToolset`.
