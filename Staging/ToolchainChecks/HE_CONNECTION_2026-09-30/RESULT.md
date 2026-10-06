# Official Houdini Engine connection check — 2026-09-30

> **Later the same day:** the Installation Info field this commandlet run could not capture was observed directly in the Unreal UI. It read `License Type Acquired: Houdini Indie` and `Current Session Status: Connected` after the existing B2 HDA cooked. See [the GUI receipt](../HE_UI_2026-09-30/RESULT_AFTER_HDA.md). This receipt is otherwise unchanged.

**Outcome:** The official project Houdini Engine plugin established a valid session inside `UnrealEditor-Cmd.exe` and instantiated one existing `.hdalc` as a standalone cookable using the existing Houdini Indie entitlement. The SideFX server's available Houdini Indie 22.0 seats changed from 2/2 before the session to 1/2 while Unreal's HARS was running, then returned to 2/2 after the session stopped. No new licence was installed.

## Ownership and method

- [measured: `Staging/ModelBank/EDITOR_OWNER.txt`] The interrupted `CODEX_BANK` lease was resolved from the clean previous editor shutdown, zero editor/HARS processes, no saved catalog asset, and no competing active project chat/agent. A bounded `CODEX_HE_CHECK` lease was then recorded before launch.
- Windows Computer Use rejected launch/control of `unrealeditor` with **“Computer Use was not approved to use unrealeditor.”** The official Unreal Python commandlet was used as the supported non-UI route. [documented: https://dev.epicgames.com/documentation/unreal-engine/scripting-the-unreal-editor-using-python; https://www.sidefx.com/docs/houdini/unreal/publicapi.html]
- [measured: `check_session.py`, `runtime_result.json`, `session_log_excerpt.txt`] `UnrealEditor-Cmd.exe` loaded this project and the project-local Houdini Engine plugin. Through SideFX's `HoudiniPublicAPIBlueprintLib.get_api()`, the script called `create_session()` once, loaded the existing `/Game/Developers/USER/HoudiniCityProof/B1_probebox.B1_probebox`, and called `instantiate()` once as `Cookable` with `enable_auto_cook=false` and `enable_auto_bake=false`. It waited 40 seconds for an independent licence query, called `stop_session()` once, and exited with code 0. It did not set parameters, request a cook, inspect geometry, bake, save, or run the city pipeline.

## Live readings

| Observation | Result and evidence |
| --- | --- |
| Unreal/plugin startup | [measured: `Saved/Logs/Environmentpipeline.log`:1521–1522, 1673–1674] Houdini Engine and its Editor module loaded. `libHAPIL.dll` came from `C:/Program Files/Side Effects Software/Houdini 22.0.429/bin`. |
| Session | [measured: `runtime_result.json`] `is_session_valid()` was false before, true after `create_session()`, true after the instantiation, and false after `stop_session()`. [measured: log:1753,1757] The plugin initialized successfully and logged that the session stopped. |
| HDA activity | [measured: log:1754–1756] Exactly one `HoudiniCookable_0` instantiation started and finished for `trackb::Sop/gazarimal_b1_probebox::1.0`. Auto cook and auto bake were disabled in the call. The session log has no `StartedCooking` or `FinishedCooking` event for this run. This is a licence-triggering instantiation, not a box proof. |
| Existing Indie seat | [measured: `sesictrl print-license --brief-list --scrub-users`] Houdini Indie 22.0 showed **2/2 free before**, **1/2 free** while Unreal's HARS PID 9592 and commandlet PID 22144 were active, then **2/2 free after** both exited. The concurrent seat change plus successful HDA instantiation supports [inference] that this official session checked out the existing Houdini Indie entitlement. No Engine Indie or commercial Engine licence was listed or installed. |
| Cleanup | [measured: process list, commandlet exit code 0, `runtime_result.json`, Content timestamp scan] No UnrealEditor, UnrealEditor-Cmd, or HARS process remained; no `.uasset` or `.umap` under `Content/` was modified during this run. |

## Installation Info capture limit

The **current Installation Info dialog was not captured** because Windows Computer Use refused Unreal Editor app control. The prior direct dialog copy at `Staging/TrackA_Tests/HoudiniCityProof/10_measure_session/evidence/installation_info_session.txt` reported built/running Houdini `22.0.429.0` and HoudiniEngine `9.0.0`, executable type `houdini`, library at the Houdini 22.0.429 `bin`, and `Connected / No License Acquired` while idle. Those historical fields are not presented as a current dialog reading. In this run, the current plugin log confirmed the HAPI location, the official Public API confirmed a valid session, and the concurrent SideFX seat change supplied the licence evidence. The plugin's exact current `License Type Acquired` field remains unobserved directly.

**Conclusion:** The official Unreal–Houdini Engine connection works in the Unreal commandlet with the existing Houdini Indie entitlement for one existing HDA instantiation. A literal current Installation Info capture remains blocked by the app-control denial; the interactive GUI menu itself was not checked.
