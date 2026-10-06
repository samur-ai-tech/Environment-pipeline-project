# CityBLD Toolset — User Guide

This guide is for artists, designers, and other non-technical users who received the **WorldBLD MCP Toolset** zip and want to work with **CityBLD** cities (blocks, parcels, and buildings) using an AI assistant in Unreal Engine.

The **CityBLD Toolset** lets the AI **inspect** your city and **lightly edit** existing buildings (for example change a building style and regenerate it). It does **not** yet create brand-new city blocks or districts—that is still done in CityBLD’s own editor tools.

---

## What you need before you start

1. **Unreal Engine 5.8** (or the version listed with your download).
2. **WorldBLD**, **CityBLD**, **RoadBLD**, and **TwinBLD** product plugins installed and working in your project (the toolset plugin depends on all four).
3. The **WorldBLD MCP Toolset** plugin from the zip in your project’s `Plugins` folder (see [Installing from the zip](#installing-from-the-zip)).
4. A valid **CityBLD license or trial** if you want the AI to change buildings (restyling and regeneration require it).
5. An **AI assistant connected to Unreal**.

Roads are often drawn first with **RoadBLD**; CityBLD blocks usually follow those roads. TwinBLD can also generate cities from real-world data.

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

- Summarize your city (how many blocks, parcels, buildings, which districts and styles are in use).
- List and describe districts, land uses, and building styles.
- List city blocks, parcels, and modular buildings in the level.
- Find common problems (missing districts, overlapping blocks, buildings not on parcels, and similar issues).
- **Change a building’s style** and **regenerate** that building (with a valid license).

Your AI assistant **cannot** (today):

- Draw new city blocks.
- Create new districts or land uses.
- Place new buildings from scratch.

For those jobs, use CityBLD’s toolbar in the viewport (see [Working in the editor](#working-in-the-editor-without-ai)).

---

## How to use it

### With an AI assistant

Good prompts to start with:

- *“Give me an overview of the CityBLD content in this level.”*
- *“List the building styles available in this project.”*
- *“Find problems with my city layout.”*
- *“Change this building to a different style and regenerate it.”*

If the AI reports a **license** or **cannot edit** message, sign in to WorldBLD / CityBLD in the editor and confirm your trial or subscription is active. The toolset will not retry forever on its own—fix licensing first.

### Working in the editor (without AI)

Open **WorldBLD editor mode**, then switch to **CityBLD** in the tool switcher. Main toolbar tools:

| Tool | Use it to… |
| --- | --- |
| **Add Blocks** | Pick a district and draw new city blocks; parcels and buildings fill in automatically |
| **Edit Blocks** | Adjust existing block layout and style |
| **Place Prefabs** | Place a building or city prefab by hand |
| **Draw Building** | Draw a custom building footprint with a chosen style |

**Right-click** a city block or modular building for more options (change district, regenerate, edit height, sign text, and more).

---

## Best practices

- **Check the city overview first.** Ask the AI for context before making changes—you’ll know counts, styles, and license status up front.
- **Run a “find issues” pass** before and after edits on large cities. It catches overlaps and missing pieces early.
- **Use roads first.** City blocks work best along a RoadBLD network. Finish or import roads before laying out blocks.
- **One building at a time for style changes.** Regenerating many buildings at once is easier in the UI with multi-select.
- **Save often.** AI edits are undoable, but saving gives you a clear rollback point.

---

## Things to watch out for

| Issue | What it means | What to do |
| --- | --- | --- |
| “License required” or “cannot edit” | No active CityBLD license/trial | Sign in through WorldBLD mode; activate trial or subscription |
| AI can list buildings but not create blocks | Expected limitation | Use **Add Blocks** in the CityBLD toolbar |
| Buildings look wrong after a style change | Regeneration may need a moment or a second pass | Ask the AI to regenerate again, or right-click → **Regenerate** in the editor |
| City floats above roads | Blocks not traced to roads | Re-draw or edit blocks near the road network; check RoadBLD is rebuilt |
| AI only shows first 100 items | Large levels are summarized in chunks | Ask to focus on a smaller area or a named block |
| CityBLD disabled in Plugins | Toolset installed but product off | **Edit → Plugins** → enable **CityBLD** → restart |
| Heights or sizes look “off” | Mix of meters and centimeters in data | Trust the building preview in the editor; ask the AI to describe dimensions if unsure |

---

## Typical workflow

1. **Roads** — Build or import a road network (RoadBLD or TwinBLD).
2. **Blocks** — Use **Add Blocks** in CityBLD to fill areas along roads.
3. **Review** — Ask the AI for a city overview and to find issues.
4. **Polish** — Restyle individual buildings (AI or right-click menus), then regenerate.
5. **Finish** — Bake blocks to meshes or set up HLOD when the city is done (see CityBLD product docs in the editor).

---

## Related toolsets

| If you want to… | Use this guide |
| --- | --- |
| Check what’s installed | [WorldBLD Toolset User Guide](../WorldBLDToolset/UserGuide.md) |
| Build or edit roads | [RoadBLD Toolset User Guide](../RoadBLDToolset/UserGuide.md) |
| Import a real-world location | [TwinBLD Toolset User Guide](../TwinBLDToolset/UserGuide.md) |

---

## Need more help?

- AI / developer reference: [README.md](README.md)
- CityBLD product guides (districts, styles, modular buildings): inside the **CityBLD** plugin folder in your project
- WorldBLD support: [https://worldbld.com](https://worldbld.com)
