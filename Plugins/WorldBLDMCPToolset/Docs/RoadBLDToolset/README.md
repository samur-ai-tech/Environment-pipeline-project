# RoadBLD Toolset

Editor AI toolset that lets agents build RoadBLD road networks from text prompts. It is exposed through the
ToolsetRegistry / Model Context Protocol server (`list_toolsets`, `describe_toolset`, `call_tool`).

| Toolset | Purpose |
| --- | --- |
| `RoadBLDToolset.URoadBLDDiscoveryToolset` | Presets, style assets, material parameters, networks, roads, junctions, endpoints, junction and geometry issues |
| `RoadBLDToolset.URoadBLDAuthoringToolset` | Roads, grids, rings, roundabouts, endpoint links, corners, control points, presets, lanes, sidewalks |
| `RoadBLDToolset.URoadBLDPresetToolset` | Validate and create presets and material variants from JSON specs |
| `RoadBLDToolset.URoadBLDBuildToolset` | Rebuild jobs: wait, poll, cancel |
| `RoadBLDToolset.URoadBLDFeedbackToolset` | Viewport captures of roads, junctions, networks and areas |

## Agent workflow

1. `ListPresets(Region, Category, Tags)` to find a close preset. `DescribePreset` returns its full editable spec.
   The RoadBLD reference kit is named in the preset toolset description and flagged `bIsRecommended` in
   `ListStyleAssets`. It covers the five `RoadKit_USA` sample presets, plus sample sidewalks, crossings, lanes,
   road modules, PCG graphs, master materials and sample material instances.
2. For a new look, edit that spec: new `Name`, `BasePreset` set to the source preset Id, then only the fields that change.
   Call `ValidatePreset` until it has no errors, then `CreatePresetFromSpec`.
3. Place roads with `CreateRoad`, `CreateGrid`, `CreateRing` and `CreateRoundabout`, with `bRebuild=false` while batching.
4. Call `FindJunctionIssues`. Fix `StubPastRoad` / `ShortOfRoad` with `SetControlPoints` and `UnjoinedCorner` /
   `SharpLinkedCorner` with `CloseCorner`.
5. Call `Rebuild` (it waits up to `TimeoutMs`; large networks return a `JobId` to keep polling), then
   `FindGeometryIssues`, and `CaptureArea` at any issue it reports.
6. Call `CaptureViewport` to look at the result, and `ListJunctions` or `DescribeRoad` to inspect it. Iterate with
   `SetLaneWidth`, `SetSidewalk`, `ChangePreset`, `SetControlPoints`, `ConnectEndpoints` and `CloseCorner`.

## Conventions and gotchas

- Units are centimeters. +X forward, +Y right, +Z up. Point Z is the road elevation.
- Actor parameters take `{"refPath": "<RefPath from a previous result>"}`. Preset parameters take the preset `Id`.
- **Junctions are not authored.** They form on rebuild wherever roads overlap. End a side street on the centerline
  of the road it joins. Endpoint links are only for smooth continuations with no intersection.
- **Two roads may only end at the same point if they continue straight** (within 20 degrees). For a turn, draw one
  road through the corner with a `TurnRadius`, or call `CloseCorner`. `CreateRoad` links straight continuations
  automatically and warns about corners; `bCloseCorners=true` closes them. `ConnectEndpoints` refuses to link a corner.
- `CloseCorner` merges two same-preset roads into one (the second road is deleted; its far-end link moves to the
  first). Two different presets are pulled back from the corner and joined by a linked connector road.
- `CreateGrid` builds the perimeter as one closed loop with `Grid.PerimeterCornerRadius`; interior roads end on it.
- Optional string parameters default to a word rather than `""`, because the registry treats an empty C++ default
  as required: filters default to `Any`, labels to `Auto`, `CaptureViewport.JunctionId` to `None`. Omit them, or
  pass the word or `""`.
- Omit `SetLaneWidth.Range` (or leave both distances 0) to change the whole road.
- In preset specs, `null` clears an optional field. Unknown fields and values that do not convert are rejected with
  the field path, for example `Spec.Category: 'Highway' is not a valid value`.
- Lane index 0 is next to the centerline; higher indices are further out. Left/right follow the drawing direction.
- Every authoring call is one undoable transaction and fails atomically.
- Generated assets live under `/Game/RoadBLD_Generated` (`Presets`, `Sidewalks`, `Materials/<Preset>`). Only
  generated presets can be updated.

## Example preset spec

A European cobblestone boulevard derived from the USA 4-lane boulevard. Check parameter names with
`ListMaterialParameters` first; the names below are placeholders.

```json
{
  "spec": {
    "name": "EU_Cobble_Boulevard",
    "basePreset": "/RoadBLD/RoadBLD/RoadKit_USA/Presets/RP_Default_USA_Boulevard_4Lane_CenterTurns.RP_Default_USA_Boulevard_4Lane_CenterTurns_C",
    "region": "Germany",
    "tags": ["boulevard", "cobblestone", "european"],
    "description": "Four-lane cobblestone boulevard with a planted median and wide sidewalks.",
    "leftLanes":  [ { "width": 300, "type": "Median" }, { "width": 330, "type": "Normal" }, { "width": 330, "type": "Normal" } ],
    "rightLanes": [ { "width": 330, "type": "Normal" }, { "width": 330, "type": "Normal" } ],
    "roadMaterial": {
      "variant": {
        "parent": "/RoadBLD/RoadBLD/DefaultRoadKit/Materials/M_RoadBLD_Asphalt_Master",
        "name": "Cobble",
        "scalars": { "Roughness": 0.85 },
        "vectors": { "BaseColorTint": { "r": 0.55, "g": 0.5, "b": 0.45, "a": 1 } }
      }
    },
    "rightSidewalk": {
      "inline": {
        "width": 400,
        "material": { "variant": { "parent": "/RoadBLD/RoadBLD/DefaultRoadKit/Materials/M_RoadBLD_Sidewalk_Master", "name": "Granite" } },
        "curbClass": "/RoadBLD/RoadBLD/RoadKit_USA/Presets/RoadModules/RM_USA_Curb"
      }
    }
  }
}
```

## UI overview (for guiding a human user)

Everything the toolset can do also exists as a manual tool on RoadBLD's viewport toolbar, built on one shared
`URoadEditController`. Point a user here when they'd rather work by hand, or to fix something an agent built.
These guides live in the RoadBLD product plugin, not this toolset — paths below are relative to this file.

| Toolbar entry | What it's for | Guide |
| --- | --- | --- |
| **Draw** | Place new roads in-viewport with live preview and snapping | [`../RoadBLD/Docs/DrawRoadsTool_Guide.md`](../RoadBLD/Docs/DrawRoadsTool_Guide.md) |
| **Edit** / **Chop & Join** | Move control points, split and join roads | [`../RoadBLD/Docs/RoadEditController.md`](../RoadBLD/Docs/RoadEditController.md) |
| **Junctions → Merge** | Pull a lane off an existing road into a smooth merge/branch (on/off ramps) | [`../RoadBLD/Docs/MergeTool_Guide.md`](../RoadBLD/Docs/MergeTool_Guide.md) |
| **Junctions → Corners / Freeway Ramps** | Junction corner geometry | [`../RoadBLD/Docs/RoadEditController.md`](../RoadBLD/Docs/RoadEditController.md) |
| **Markings → Chevrons** | Paint gore/hatch markings in intersection corners and merge noses | [`../RoadBLD/Docs/ChevronTool_Guide.md`](../RoadBLD/Docs/ChevronTool_Guide.md) |
| Bake to Static Mesh (right-click / menu) | Convert finished roads to standalone Static Mesh assets that don't need RoadBLD installed | [`../RoadBLD/Docs/BakeRoadsToStaticMesh_ArtistGuide.md`](../RoadBLD/Docs/BakeRoadsToStaticMesh_ArtistGuide.md) |

Global behavior (mesh generation, rebuild, intersections, landscape conforming) is configured in
**Project Settings → RoadBLD**, documented in [`../RoadBLD/Docs/RoadBLDRuntimeSettings.md`](../RoadBLD/Docs/RoadBLDRuntimeSettings.md).

## Further reading

For a question the toolset descriptions don't answer, point the agent at these before guessing:

- [`../RoadBLD/Docs/RoadEditController.md`](../RoadBLD/Docs/RoadEditController.md) — the manual draw/edit tool this toolset mirrors.
- [`../RoadBLD/Docs/Classes/ADynamicRoad.md`](../RoadBLD/Docs/Classes/ADynamicRoad.md) — the road actor: spline, lanes, materials, modules/props/stamps.
- [`../RoadBLD/Docs/Classes/UDynamicRoadLane.md`](../RoadBLD/Docs/Classes/UDynamicRoadLane.md) — a lane band between two edge curves (width, type, overlay, tapering).
- [`../RoadBLD/Docs/Classes/URoadModuleObject.md`](../RoadBLD/Docs/Classes/URoadModuleObject.md) — edge-following geometry swept along a spline (curbs, barriers, rails).
- [`../RoadBLD/Docs/Classes/URoadStamp.md`](../RoadBLD/Docs/Classes/URoadStamp.md) — a single static-mesh decal placed on the road surface (arrows, stop lines).
- [`../RoadBLD/Docs/Classes/UPropSpawner.md`](../RoadBLD/Docs/Classes/UPropSpawner.md) — repeated prop placement along a road (lights, trees, bollards).
- [`../RoadBLD/Docs/Classes/ARoadIsland.md`](../RoadBLD/Docs/Classes/ARoadIsland.md) — standalone closed-loop island geometry (medians, planters).

CityBLD's city blocks and TwinBLD's real-world imports both build on RoadBLD networks — see
[`../CityBLDToolset/README.md`](../CityBLDToolset/README.md) and [`../TwinBLDToolset/README.md`](../TwinBLDToolset/README.md).
For whether RoadBLD itself is installed/enabled, see [`../WorldBLDToolset/README.md`](../WorldBLDToolset/README.md).

## Tests

Automation tests live under `AI.Toolsets.WorldBLD.RoadBLDToolset`:

- the root spec: schema, parameter defaults and preset validation;
- `.Authoring`: creates, edits and removes roads in the open editor level, including corners, the grid loop and
  geometry scans after a rebuild;
- `.Registry`: calls tools through the toolset registry with JSON arguments, the same path the MCP server uses.

Licensed calls in these specs run inside `RoadBLDToolset::FScopedTestAuthorization`; running automation tests does
not bypass the license check otherwise.

Headless run (close the editor first):

```
UnrealEditor-Cmd.exe MCPTesting.uproject -ExecCmds="Automation RunTests AI.Toolsets.WorldBLD.RoadBLDToolset" -TestExit="Automation Test Queue Empty" -unattended -nullrhi
```
