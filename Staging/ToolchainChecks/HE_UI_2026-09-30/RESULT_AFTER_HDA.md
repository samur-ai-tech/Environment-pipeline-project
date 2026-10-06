# Official Houdini Engine connection in Unreal — visual check

**Date:** 2026-09-30, approximately 13:06–13:18 Asia/Jerusalem.  **Scope:** One manual connection and licence observation in the existing `Environmentpipeline` editor. This is not a city-pipeline, bank, bake, persistence, or acceptance test.

## Editor and versions

- [measured: process list and Unreal UI] Target window `Environmentpipeline - Unreal Editor`, `UnrealEditor.exe` PID `12028`, project `Environmentpipeline.uproject`. Its HARS PID `25420` used named pipe `hapi`. A separate `Unreal Engine 5.8` window, PID `15476`, was identified by its different command line and was not operated.
- [measured: `Installation Info`] `Plugin was built with`: Houdini `22.0.429.0`, HoudiniEngine `9.0.0`; `Plugin is running with`: Houdini `22.0.429.0`, HoudiniEngine `9.0.0`; `HoudiniEngine Library Location`: `C:/Program Files/Side Effects Software/Houdini 22.0.429/bin`.
- [measured: `Installation Info` before HDA activity] `Current Session Status: Connected`; `License Type Acquired: No License Acquired`. [Screenshot](02_installation_info_before_hda.jpg).

## Exact activity and result

1. [measured: Unreal Content Drawer] Navigated to `/Game/Developers/USER/HoudiniCityProof/` and dragged the **existing** `B2_labs_osm` HoudiniAsset once into the already open `Untitled` level. No asset was imported or modified. The level actor count changed from 138 to 139; one `B2_labs_osm` HoudiniAssetActor was selected.
2. [measured: Unreal Details] The automatic instantiate/cook completed with `HDA Successfully Cooked`. The actor's component tree exposed `HoudiniStaticMeshComponent_0` and `HoudiniStaticMeshComponent_1`. [Cook status screenshot](03_b2_hda_cooked.jpg). Double-clicking the actor in the Outliner framed visible selected OSM footprint geometry in the top viewport. [Output screenshot](06_b2_osm_output_view.jpg). The terrain behind it is not attributed to this HDA.
3. [measured: `Installation Info` after cook] **`License Type Acquired: Houdini Indie`** and **`Current Session Status: Connected`**. [Dialog screenshot](04_license_houdini_indie_after_cook.jpg); [full editor screenshot with cooked status](05_cook_and_license_full_editor.jpg).
4. [measured: `Saved/Logs/Environmentpipeline.log`] `HAPI Asynchronous Cooking Started` for `B2_labs_osm` at `10:15:24.963` UTC and `FinishedCooking` at `10:15:25.620` UTC. No `LogHoudiniEngine` error or warning was found in the scoped `10:15–10:18` UTC log interval. The UI showed no licence error.

**Conclusion:** The official plugin in Unreal connected, cooked this one existing Indie HDA, and acquired the existing `Houdini Indie` entitlement. The idle `No License Acquired` value was not a licence failure. This result says nothing about the unfinished city HDA or full geographic pipeline.

**State left for Aviv:** No bake or save command was issued. The editor remains open on `Untitled*` with the one test actor and `3 Unsaved` packages shown in the status bar. The actor and cooked output are available for inspection in memory; they were not claimed as saved content. The editor ownership lease is released separately with this explicit dirty-state caveat.
