---
name: new-environment
description: Build a new real-world environment in this Unreal project (geographic source package -> owned Houdini generator -> generated area -> satellite ground -> PCG vegetation clone -> farmland / hero site -> Astra assets -> verify). Use when Aviv asks for a new area or environment, or to redo a stage of one, following the proven Karmei Yosef / Paz Farm process.
---

# New environment

This project builds real places in Unreal: OSM and DEM data → a Houdini city generator (official Houdini Engine) → a saved area map → ground, vegetation and site detail on a PCG clone. This skill runs that process the way it was proven on the Karmei Yosef 4 km area and the Paz Farm (2026-10-08 to 2026-10-11).

## Do this first

1. Read the playbook completely: `Staging/Playbooks/NEW_ENVIRONMENT_PLAYBOOK.md`. It holds every stage, its tools and commands, and the failure rules. Treat it as the procedure.
2. Read root `AGENTS.md` (ownership, saves, preservation) and the memory index. Check what is running before touching Unreal: live `UnrealEditor` processes, the last line of `Staging/ModelBank/EDITOR_OWNER.txt`, and `Staging/ParallelEditors/`.
3. Ask Aviv the playbook's **[D]** decision points with AskUserQuestion buttons, recommended option first. For a new area that means at least: the exact point, the size, and the six generator defaults (playbook section 1).

## How to work

- **Work in a copy of the reference tools.** Make a new task folder `Staging/NewArea_<Name>_<lat8>_<lon8>_<size>_<date>/` and copy the reference `Tools/` from `Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/`. Change only the path constants (playbook section 11). Never edit the reference folder's tools for the new area.
- **One stage at a time.** Save after each stage, then verify with a fresh reopen at the end. Every run is real and retained: no tests, pilots or throwaway maps unless Aviv asks for a trial on a named copy.
- **Keep the handoff current.** Keep `Staging/<Name>_SESSION_HANDOFF_<date>.md` up to date after every stage (state, shas, tools, next step, deletions waiting for Aviv's confirmation), plus one memory line.
- **Models go to the Astra chat.** Write a brief file and a paste-ready English message for Aviv (playbook section 9). Ask Astra to collect real photo references.
- **Report to Aviv** in short English: what changed, what to look at, and open choices as one-line options.

## Hard stops

- **Generation:** start a generation only when yours is the only Unreal editor. Never close, save or touch another session's editor; ask Aviv.
- **Material graphs:** after a material-graph edit, quit the editor before the next step. On a map with PCG, wait for PCG to be idle before each step.
- **Saves:** named saves only, never Save All. Leave vendor originals, shared masters and earlier HDA revisions unchanged.
- **Deletions:** delete only after Aviv has verified and confirmed.
- **Git and Linear:** no git commit or push, and no Linear.
- **Codex:** never use `--sandbox danger-full-access`, `--yolo` or `--dangerously-bypass-approvals-and-sandbox`.
