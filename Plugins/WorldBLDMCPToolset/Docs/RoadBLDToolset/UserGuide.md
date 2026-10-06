# RoadBLD Toolset — User Guide

This guide is for artists, designers, and other non-technical users who received the **WorldBLD MCP Toolset** zip and want to **build and edit roads** in Unreal Engine with help from an AI assistant.

The **RoadBLD Toolset** is the most hands-on of the four toolsets. Your AI can draw roads, grids, roundabouts, change lane widths, apply presets, rebuild the network, and even capture viewport images to check the result.

---

## What you need before you start

1. **Unreal Engine 5.8** (or the version listed with your download).
2. **WorldBLD**, **CityBLD**, **RoadBLD**, and **TwinBLD** product plugins installed and working (the toolset plugin depends on all four).
3. The **WorldBLD MCP Toolset** plugin from the zip in your project’s `Plugins` folder (see [Installing from the zip](#installing-from-the-zip)).
4. An **AI assistant connected to Unreal**.

CityBLD and TwinBLD often use RoadBLD roads underneath—roads are a good first step for many projects.

---

## Installing from the zip

You only need to do this once per project.

1. **Close Unreal Editor** if it is open.
2. **Unzip** the WorldBLD MCP Toolset package.
3. Copy the `WorldBLDMCPToolset` folder into your project’s **`Plugins`** folder (next to your `.uproject` file).
   - If there is no `Plugins` folder, create one.
4. Open the project in Unreal.
5. Go to **Edit → Plugins**, search for **WorldBLD MCP Toolset**, and enable it. Unreal also enables the **Unreal MCP** and **EditorToolset** plugins it depends on.
6. **Restart** when prompted.

The toolset needs **WorldBLD**, **CityBLD**, **RoadBLD** and **TwinBLD** installed and enabled under **Edit → Plugins**, because the one plugin contains the toolsets for all four products.

---

## What this toolset does

Your AI assistant can:

- List road **presets** (styles like highways, residential streets, boulevards).
- **Draw roads** by describing what you want (straight roads, grids, rings, roundabouts).
- **Edit** existing roads (lane width, sidewalks, presets, control points).
- **Rebuild** the road network so intersections and meshes update.
- **Capture screenshots** of the viewport to verify how roads look.
- Create **custom presets** from descriptions (advanced; the AI validates before applying).

Junctions (intersections) are **automatic**—they appear when roads cross. You do not place junctions by hand.

---

## How to use it

### With an AI assistant

Start with clear, visual requests:

- *“Create a simple grid of residential streets in this area.”*
- *“Add a four-lane boulevard along the north edge of the map.”*
- *“Make the sidewalks wider on this road.”*
- *“Rebuild the roads and show me a screenshot.”*
- *“List the road presets that look European.”*

**Rebuild** is important. After several edits, ask the AI to rebuild if intersections look wrong or geometry is outdated.

### Working in the editor (without AI)

Open **WorldBLD editor mode**, switch to **RoadBLD**, then use the viewport toolbar:

| Tool | Use it to… |
| --- | --- |
| **Draw** | Click to place new roads with live preview |
| **Edit** / **Chop & Join** | Move points, split or join roads |
| **Junctions → Merge** | Smooth on-ramps and merges |
| **Markings → Chevrons** | Add chevron markings in intersections |

Right-click roads for more actions, including **bake to static mesh** when you want finished geometry that does not need RoadBLD installed.

Global behavior (mesh quality, landscape conforming) is under **Project Settings → RoadBLD**.

---

## Best practices

- **Pick a preset first.** Ask the AI to list presets before drawing. Starting from a close match saves time.
- **Rebuild after batches.** When the AI places several roads, one rebuild at the end is faster than rebuilding after every single segment.
- **Describe scale in real terms.** “A two-lane neighborhood street” works better than vague “a small road.”
- **Check screenshots.** Ask for a viewport capture after big changes—you catch alignment issues early.
- **Roads before cities.** Lay out your road network before CityBLD blocks or TwinBLD imports when possible.
- **Save your level** before large road edits.

---

## Things to watch out for

| Issue | What it means | What to do |
| --- | --- | --- |
| Intersections look broken or missing | Network needs a rebuild | Ask the AI to **rebuild** roads, or use RoadBLD’s rebuild in the UI |
| Side street doesn’t meet the main road cleanly | Roads must meet on the centerline for a proper junction | Ask the AI to adjust endpoints, or use **Edit** in the toolbar |
| “Smooth connection” vs intersection | Endpoint links are for continuations, not cross streets | Describe “T intersection” or “four-way crossing” instead of “connect” |
| Stretched triangles at a corner | Two roads end at the same point at an angle | Ask the AI to **close the corner** (or draw one road around the bend), then rebuild |
| Rebuild takes a long time | Large networks run as background jobs | Wait; ask the AI for job status if it offered a job ID |
| New materials or presets in wrong folder | Generated content lives under `/Game/RoadBLD_Generated` | Normal; don’t move files unless you know what you’re doing |
| Roads float above terrain | Landscape conforming may be off | Check **Project Settings → RoadBLD** or conform landscape in the product settings |
| RoadBLD disabled in Plugins | Toolset works but product does not | Enable **RoadBLD** under **Edit → Plugins** and restart |
| AI undid something unexpectedly | Each AI road edit is one undo step | Use **Ctrl+Z** / **Edit → Undo** in Unreal |

---

## Typical workflow

1. **Plan** — Sketch the road layout (grid, spine road, highway loop, etc.).
2. **Preset** — Choose or create a road style.
3. **Draw** — Place roads (AI or Draw tool).
4. **Rebuild** — Update intersections and meshes.
5. **Review** — Screenshot or fly through the level.
6. **Refine** — Lane widths, sidewalks, markings.
7. **Next steps** — Add CityBLD blocks along roads, or bake roads to static meshes for export.

---

## Related toolsets

| If you want to… | Use this guide |
| --- | --- |
| Check what’s installed | [WorldBLD Toolset User Guide](../WorldBLDToolset/UserGuide.md) |
| Add city blocks and buildings | [CityBLD Toolset User Guide](../CityBLDToolset/UserGuide.md) |
| Import real-world roads | [TwinBLD Toolset User Guide](../TwinBLDToolset/UserGuide.md) |

---

## Need more help?

- AI / developer reference: [README.md](README.md)
- RoadBLD drawing and editing guides: **RoadBLD** plugin → `Docs` folder in your project
- WorldBLD support: [https://worldbld.com](https://worldbld.com)
