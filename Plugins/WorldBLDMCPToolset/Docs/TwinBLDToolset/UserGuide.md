# TwinBLD Toolset — User Guide

This guide is for artists, designers, and other non-technical users who received the **WorldBLD MCP Toolset** zip and want to build **real-world locations** in Unreal Engine (digital twins) with help from an AI assistant.

The **TwinBLD Toolset** helps your AI **place the level on Earth** (set latitude/longitude), **inspect** imported real-world content, and **fix** common issues after import. The actual **import** of map data (roads, buildings, terrain) is still done through TwinBLD’s **Import Map Data** window in the editor—the AI sets the stage, then you (or the AI guiding you) run the import.

---

## What you need before you start

1. **Unreal Engine 5.8** (or the version listed with your download).
2. **WorldBLD**, **CityBLD**, **RoadBLD**, and **TwinBLD** product plugins installed and working (the toolset plugin depends on all four).
3. The **WorldBLD MCP Toolset** plugin from the zip in your project’s `Plugins` folder (see [Installing from the zip](#installing-from-the-zip)).
4. An **AI assistant connected to Unreal**.
5. For imports: internet access and any API keys or accounts TwinBLD asks for in **Project Settings → Plugins → TwinBLD** (for example elevation data).

Imported roads and buildings become **RoadBLD** and **CityBLD** content—you get the most from TwinBLD if those products are installed too.

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

- **Look up places** by name or address (for example “Flatiron Building, New York”).
- **Set the real-world location** of your level (where world origin `(0, 0)` sits on the globe).
- **Preview** how big an import area would be (read-only).
- **Summarize** what TwinBLD already generated in the level (buildings, roads, landscape, tiles).
- **Find** generated actors by type or area.
- **Fix** content after import: snap buildings or roads to terrain, update street-facing facades, adjust building height from real measurements.
- **Set the sun** to a realistic position for your location and date/time.

Your AI assistant **cannot** (today):

- Run the full **Import Map Data** pipeline by itself.

After the AI sets your location, you use **Tools → Import Map Data** (or the TwinBLD toolbar button) to fetch and generate content.

---

## How to use it

### With an AI assistant — recommended flow

1. **Pick a place**  
   *“Set up this level for downtown Seattle.”*  
   The AI looks up coordinates and explains where the map will sit.

2. **Confirm before applying**  
   A good assistant will **preview** moving the geo origin first. Say yes only when the location looks right.

3. **Import in the editor**  
   When the AI says to open **Import Map Data**, do that (see below). Generate roads, buildings, landscape, and/or parcels as needed.

4. **Inspect and fix**  
   *“What did TwinBLD import?”*  
   *“Snap these buildings to the landscape.”*  
   *“Set the sun for noon on June 21.”*

### Import Map Data (you do this step)

1. Open **WorldBLD editor mode** and switch to **TwinBLD**, **or** use **Tools → Import Map Data** from the main menu.
2. In the importer window:
   - Load an **`.osm` file** or fetch from a configured source.
   - **Select tiles** on the map for the area you want.
   - Run **Generate Roads**, **Generate Buildings**, **Generate Landscape**, and/or **Generate Parcels** as needed.
3. Wait for jobs to finish—large areas can take several minutes.
4. Return to the AI to review and fix the result.

---

## Best practices

- **Set location before importing.** Moving the geo origin *after* content exists can leave old buildings and roads in the wrong place.
- **Start small.** Import one neighborhood before an entire city. Faster iterations, easier fixes.
- **Landscape before snap.** Generate terrain first, then ask the AI to snap buildings and roads to the landscape.
- **One place name at a time.** The lookup service is rate-limited; don’t ask the AI to geocode dozens of addresses in a row.
- **Save before moving the origin.** If something goes wrong, you can revert the level.
- **Use RoadBLD / CityBLD toolsets after import.** Imported content is normal RoadBLD and CityBLD data—you can edit roads and buildings with those toolsets too.

---

## Things to watch out for

| Issue | What it means | What to do |
| --- | --- | --- |
| Buildings or roads in the wrong place after “moving the map” | Geo origin changed after import | Prefer setting location **before** import; re-import or regenerate affected tiles |
| “Stale” content | Generated under an old map position | Re-run snap or regenerate; ask the AI for a scene summary to see stale counts |
| AI can’t import OSM data | Import is manual only | Use **Import Map Data** in the editor |
| Flat terrain or missing hills | Landscape not generated or elevation API missing | Run **Generate Landscape**; check TwinBLD project settings for API keys |
| Buildings floating | No landscape yet or snap not run | Generate landscape, then ask to **snap to landscape** |
| Wrong building styles on import | OSM tag mapping | Adjust presets in TwinBLD settings or the street map customizer (see TwinBLD docs) |
| Very slow import | Large tile selection | Select fewer tiles; import in sections |
| TwinBLD disabled in Plugins | Toolset installed but product off | Enable **TwinBLD** under **Edit → Plugins** and restart |

---

## Typical workflow

1. **New level or empty area** — Start with a clean map when possible.
2. **Set geo origin** — AI looks up place and sets world location (with preview).
3. **Import Map Data** — You run generate roads / buildings / landscape in the importer.
4. **Review** — AI summarizes what was created.
5. **Fix** — Snap to terrain, facade detection, height tweaks.
6. **Polish** — Use RoadBLD and CityBLD tools for local edits; set sun for lighting tests.

---

## Related toolsets

| If you want to… | Use this guide |
| --- | --- |
| Check what’s installed | [WorldBLD Toolset User Guide](../WorldBLDToolset/UserGuide.md) |
| Edit imported roads | [RoadBLD Toolset User Guide](../RoadBLDToolset/UserGuide.md) |
| Edit imported buildings and blocks | [CityBLD Toolset User Guide](../CityBLDToolset/UserGuide.md) |

---

## Need more help?

- AI / developer reference: [README.md](README.md)
- TwinBLD import pipelines (roads, buildings, landscape, parcels): **TwinBLD** plugin → `Docs` folder in your project
- WorldBLD support: [https://worldbld.com](https://worldbld.com)
