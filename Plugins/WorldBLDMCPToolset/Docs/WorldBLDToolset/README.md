# WorldBLD Toolset

Editor AI toolset that lets agents inspect the current WorldBLD editor session: which WorldBLD product plugins
are installed, whether WorldBLD's own editor mode is active, and what landscapes/PCG volumes exist in the level.
It is read-only except for toggling the editor mode, and it never modifies WorldBLD, CityBLD, RoadBLD or TwinBLD
content. It is exposed through the ToolsetRegistry / Model Context Protocol server (`list_toolsets`,
`describe_toolset`, `call_tool`), the same mechanism used by CityBLDToolset, RoadBLDToolset and TwinBLDToolset.

| Toolset | Purpose |
| --- | --- |
| `WorldBLDToolset.UWorldBLDToolset` | Session context: product-plugin capabilities, editor-mode state, landscape/PCG actors, **packaging / cook / plugin-load troubleshooting** |

## Agent workflow

1. Call `GetCapabilities()` first in any new session. It reports which of WorldBLD, CityBLD, RoadBLD and TwinBLD
   are discovered and enabled in this project, with their `VersionName`. Only call tools from a product's own
   toolset (`CityBLDToolset`, `RoadBLDToolset`, `TwinBLDToolset`) when that product shows `bEnabled=true` here —
   otherwise their tools will fail because the underlying plugin content isn't loaded.
2. Call `GetEditorContext()` to see the current map and whether WorldBLD's own editor mode is active.
3. Call `ListLevelActors()` to get a bounded summary of landscape proxies and PCG volumes already in the level —
   useful before deciding whether a task needs a new landscape or can build on an existing one. It caps results
   at 100 actors; `TotalCount` tells you if more exist.
4. `SetWorldBLDEditorModeActive(bActive)` is the only mutating call here. It just switches the editor's active
   mode (equivalent to a human clicking the WorldBLD mode button in the Modes panel) — it doesn't create or
   change any content by itself. Most agent tasks don't need to call it; the other three toolsets work whether
   or not WorldBLD mode is active.
5. **Packaging / cook / compile / plugin-load errors** for WorldBLD, CityBLD, TwinBLD or RoadBLD: call
   `GetPackagingGuide()` (optionally pass the log excerpt as `ErrorText`) **before guessing**. It returns how the
   product plugins integrate, live checks for *this* project (launcher vs source engine, Engine vs Project
   install, Blueprint vs C++ project, Full Rebuild, GeometryScripting), and the usual fixes. Lead the user with
   `SuggestedFirst` and `Checks` where `bLooksOk=false`, then the numbered `CommonSolutions`.

## Conventions and gotchas

- This toolset never talks to a specific product's data model. For city/road/twin content, use that product's
  own toolset (see the table below) — WorldBLDToolset only tells you *whether* those toolsets will work.
- Actor references use `{"refPath": "<RefPath from a previous result>"}`, the same convention as every other BLD
  toolset.
- A product plugin can be "discovered" (`bAvailable=true`) but not "enabled" (`bEnabled=false`) if it's present
  in the project but disabled in plugin settings — enabling it is a project-settings change outside any toolset,
  so tell the user to enable it from Edit > Plugins if `GetCapabilities()` shows this.
- Packaging these plugins is a project-setup problem, not a level-content problem. Do not try CityBLD/RoadBLD/
  TwinBLD authoring tools to "fix" a cook or `Unable to load plugin` failure — use `GetPackagingGuide`.

## Packaging errors (`GetPackagingGuide`)

Call this whenever the user reports WorldBLD / CityBLD / TwinBLD / RoadBLD packaging, cooking, compiling, or a
packaged `.exe` that will not launch.

Typical causes, in the order the tool lists them:

1. Custom **source** engine with **binary/Fab** plugins — you need the source plugin drop.
2. Plugins installed to the **engine** (Fab default) instead of `<Project>/Plugins` — you can only build from a
   project install.
3. **Blueprint-only** project — add one C++ class so Unreal converts it, then compile.
4. **Locked files** — restart the PC.
5. **Full Rebuild** enabled in Project Settings > Packaging — turn it off.
6. Source-engine users: set `DefaultBuildSettings = BuildSettingsVersion.V4` or `V5` in each WorldBLD plugin
   `*.Build.cs`.
7. Cook **path too long** (`Content is missing from cook... /ModernEssentials/WorldBLD_Content`) — package to a
   short path such as `H:/Pack`.
8. Missing **GeometryScripting** at runtime (`Unable to load plugin 'CityBLD' ... GeometryScripting`) — enable
   the plugin and add `GeometryScriptingCore` to the game module `PublicDependencyModuleNames`.

## Where the other toolsets live

| Product | Use this toolset for... |
| --- | --- |
| CityBLD (city blocks, parcels, buildings) | `CityBLDToolset` — see [`../CityBLDToolset/README.md`](../CityBLDToolset/README.md) |
| RoadBLD (road networks) | `RoadBLDToolset` — see [`../RoadBLDToolset/README.md`](../RoadBLDToolset/README.md) |
| TwinBLD (real-world digital twins) | `TwinBLDToolset` — see [`../TwinBLDToolset/README.md`](../TwinBLDToolset/README.md) |

## UI overview (for guiding a human user)

WorldBLD adds a **WorldBLD editor mode** to the Unreal Editor's Modes panel. Activating it opens a WorldBLD panel
in the level viewport with:

- A **tool switcher** for jumping between each installed product's own tool palette (WorldBLD, CityBLD, RoadBLD,
  TwinBLD), plus "Mini Tools" and "Custom Tools" sections and a login tab for the user's WorldBLD account.
- A **plugin/tool manager** for installing, updating and enabling the WorldBLD product plugins themselves
  (separate from Unreal's own Edit > Plugins window) — point a user here if `GetCapabilities()` shows a product
  as not available or out of date.
- An **asset library** panel for browsing bundled content, and generic item/context-menu widgets shared across
  the product tool palettes.

If a user asks "how do I get to CityBLD/RoadBLD/TwinBLD," the answer is: open the WorldBLD editor mode (or ask
the agent to call `SetWorldBLDEditorModeActive(true)`), then use the tool switcher to pick the product.

## Tests

Automation tests live under `AI.Toolsets.WorldBLD.WorldBLDToolset` (registration, schema, and GetPackagingGuide content).
