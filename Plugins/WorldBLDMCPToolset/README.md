# WorldBLD MCP Toolset

Editor-only AI toolsets that let agents inspect and edit WorldBLD, CityBLD, RoadBLD and TwinBLD content. The
toolsets register with the engine's **Toolset Registry** and are exposed through the **Unreal MCP** server
(`ModelContextProtocol` plugin) as `list_toolsets`, `describe_toolset` and `call_tool`.

This plugin merges the former experimental `WorldBLDToolset`, `CityBLDToolset`, `RoadBLDToolset` and
`TwinBLDToolset` plugins. Each keeps its own module, so toolset names such as
`RoadBLDToolset.URoadBLDDiscoveryToolset` are unchanged.

## Toolsets

| Toolset | Purpose |
| --- | --- |
| `WorldBLDToolset.UWorldBLDToolset` | Session context: product-plugin capabilities, editor-mode state, landscape/PCG actors, packaging / cook / plugin-load troubleshooting |
| `WorldBLDToolset.UWorldBLDValidationToolset` | Post-edit readiness, one validation pass across the City/Road/Twin toolsets, and viewport evidence captures |
| `CityBLDToolset.UCityBLDDiscoveryToolset` | Read-only: city context, presets (districts, land uses, building styles), blocks, parcels, buildings, issue checks |
| `CityBLDToolset.UCityBLDToolset` | List/describe buildings and blocks, list Building Style assets, assign a style, regenerate a building |
| `RoadBLDToolset.URoadBLDDiscoveryToolset` | Presets, style assets, material parameters, networks, roads, junctions, endpoints, junction and geometry issues |
| `RoadBLDToolset.URoadBLDAuthoringToolset` | Roads, grids, rings, roundabouts, endpoint links, corners, control points, presets, lanes, sidewalks |
| `RoadBLDToolset.URoadBLDPresetToolset` | Validate and create presets and material variants from JSON specs |
| `RoadBLDToolset.URoadBLDBuildToolset` | Rebuild jobs: wait, poll, cancel |
| `RoadBLDToolset.URoadBLDFeedbackToolset` | Viewport captures of roads, junctions, networks and areas |
| `TwinBLDToolset.UTwinBLDLocationToolset` | Geocoding, the level's geo origin, geo↔world conversion, sun position |
| `TwinBLDToolset.UTwinBLDSceneToolset` | Inspect and fix content TwinBLD already generated |

## Modules

| Module | Contents |
| --- | --- |
| `BLDToolsetCommon` | Shared helpers used by every toolset: validation, job registry, HTTP, viewport capture |
| `WorldBLDToolset` | WorldBLD session and validation toolsets |
| `CityBLDToolset` | CityBLD toolsets |
| `RoadBLDToolset` | RoadBLD toolsets, preset spec IO, rebuild jobs |
| `TwinBLDToolset` | TwinBLD toolsets, Nominatim geocoding |

All modules are `Editor` modules restricted to the Editor target; nothing ships in a packaged game.

## Requirements

- Unreal Engine 5.8.
- Engine plugins: **Unreal MCP** (`ModelContextProtocol`), **EditorToolset** and **Toolset Registry**. They are
  experimental engine plugins and are enabled automatically with this plugin.
- **WorldBLD**, **CityBLD**, **RoadBLD** and **TwinBLD** installed in the project. The modules link against all
  four products, so the plugin cannot load if any of them is missing or disabled.

## Documentation

Per-product agent notes and user guides are in `Docs/`:

- WorldBLD: [README](Docs/WorldBLDToolset/README.md), [User Guide](Docs/WorldBLDToolset/UserGuide.md)
- CityBLD: [README](Docs/CityBLDToolset/README.md), [User Guide](Docs/CityBLDToolset/UserGuide.md)
- RoadBLD: [README](Docs/RoadBLDToolset/README.md), [User Guide](Docs/RoadBLDToolset/UserGuide.md)
- TwinBLD: [README](Docs/TwinBLDToolset/README.md), [User Guide](Docs/TwinBLDToolset/UserGuide.md)

## Packaging

```powershell
.\Tools\ReleasePlugin.ps1 -ToolId WorldBLDMCPToolset
```

The release script packages and stages WorldBLD, CityBLD, RoadBLD and TwinBLD into the engine first, because the
toolset modules compile against them. Add `-NoVersionBump` to repackage the current version.
