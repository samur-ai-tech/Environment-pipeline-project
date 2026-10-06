# WorldBLD Toolset — User Guide

This guide is for artists, designers, and other non-technical users who received the **WorldBLD MCP Toolset** zip and want to get started in Unreal Engine.

The **WorldBLD Toolset** is the “starting point” toolset. It helps your AI assistant understand what WorldBLD products you have installed, what map you are working in, and whether WorldBLD’s editor mode is active. It does **not** create roads, cities, or real-world imports by itself.

---

## What you need before you start

1. **Unreal Engine 5.8** (or the version listed with your download).
2. An **Unreal project** that already has the **WorldBLD**, **CityBLD**, **RoadBLD**, and **TwinBLD** product plugins installed and working (the toolset plugin depends on all four).
3. The **WorldBLD MCP Toolset** zip (this package includes WorldBLD Toolset plus CityBLD, RoadBLD, and TwinBLD toolsets).
4. An **AI assistant connected to Unreal** (for example through Cursor or another tool that talks to the editor). The toolsets are built for that workflow.

> **Tip:** Install and test WorldBLD in the editor first (open WorldBLD mode, sign in if prompted). The toolset only helps the AI *see* what is already there—it cannot replace the main WorldBLD plugins.

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

After restart, the toolset is installed. You do not need to copy files into the Engine folder.

The toolset needs **WorldBLD**, **CityBLD**, **RoadBLD** and **TwinBLD** installed and enabled under **Edit → Plugins**, because the one plugin contains the toolsets for all four products.

---

## What this toolset does

Your AI assistant can use WorldBLD Toolset to:

- See which WorldBLD products are installed (WorldBLD, CityBLD, RoadBLD, TwinBLD).
- See whether each product is turned on in your project.
- See basic information about your current level (map).
- See landscapes and PCG volumes already in the level.
- Turn **WorldBLD editor mode** on or off (same as clicking the WorldBLD mode in the toolbar).

It is mostly **read-only**. The only direct change it makes is switching editor mode.

---

## How to use it

### With an AI assistant

Ask simple questions, for example:

- *“What WorldBLD tools do I have available?”*
- *“Is CityBLD enabled in this project?”*
- *“What’s in my level right now?”*
- *“Turn on WorldBLD editor mode.”*

The assistant should check capabilities **before** trying to build roads or cities. If a product is installed but disabled, the assistant can tell you to enable it under **Edit → Plugins**.

### In the editor (without AI)

1. In the main toolbar, open the **Modes** panel.
2. Select **WorldBLD** to enter WorldBLD editor mode.
3. Use the **tool switcher** in the viewport to jump between WorldBLD, CityBLD, RoadBLD, and TwinBLD tools (depending on what you own).
4. Use the **plugin manager** inside WorldBLD mode to install, update, or enable WorldBLD product plugins if something is missing.

---

## Best practices

- **Start here.** Before a big task, ask the AI to check what products are available. That avoids errors later.
- **Keep product plugins enabled.** If CityBLD or RoadBLD is disabled in **Edit → Plugins**, the matching toolset will not work even if it is installed.
- **One project, one copy.** Install the toolsets into the project you are actually opening—not only into a template you never use.
- **Save your level** before long AI sessions so you can undo or revert if needed.

---

## Things to watch out for

| Issue | What it means | What to do |
| --- | --- | --- |
| AI says a product is “not enabled” | The plugin is on disk but turned off in the project | **Edit → Plugins** → search for CityBLD / RoadBLD / TwinBLD / WorldBLD → enable → restart |
| AI says a product is “not available” | The main product plugin is not in the project | Install the product through WorldBLD’s plugin manager or your WorldBLD account download |
| WorldBLD mode won’t open | WorldBLD product may be missing or broken | Confirm WorldBLD works manually first; restart the editor |
| AI tries to build roads or cities using only WorldBLD Toolset | Wrong toolset for the job | Use **RoadBLD Toolset**, **CityBLD Toolset**, or **TwinBLD Toolset** for those tasks (see their user guides) |
| Changes after “turn on WorldBLD mode” | Mode change only; no content was created | That is normal. Use the product’s own tools to create content |
| Packaging / cook fails, or the packaged game will not start | WorldBLD plugins are not set up for packaging | Ask the AI to run **GetPackagingGuide**. Common fixes: install the plugins into the **project** (not the engine), convert a Blueprint project to C++ (add one C++ class), disable **Full Rebuild**, enable **GeometryScripting**, package to a **short path** such as `H:/Pack`, restart the PC for locked files |

---

## Related toolsets

| If you want to… | Use this guide |
| --- | --- |
| Build or edit roads | [RoadBLD Toolset User Guide](../RoadBLDToolset/UserGuide.md) |
| Work with city blocks and buildings | [CityBLD Toolset User Guide](../CityBLDToolset/UserGuide.md) |
| Import real-world locations | [TwinBLD Toolset User Guide](../TwinBLDToolset/UserGuide.md) |

---

## Need more help?

- Technical details for developers and AI agents: [README.md](README.md) in this folder.
- WorldBLD product support: [https://worldbld.com](https://worldbld.com)
