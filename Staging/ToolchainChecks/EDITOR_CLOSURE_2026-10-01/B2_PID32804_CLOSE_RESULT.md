# B2 editor PID 32804 — reviewed changes discarded and window closed

**Scope, 2026-10-01:** Only the existing Environmentpipeline Unreal Editor PID **32804** (window 2689732) was closed. Aviv had explicitly chosen to discard this window's reviewed 15 unsaved Cook packages and close it. A fresh bounded `EDITOR_OWNER.txt` lease was recorded at 13:59:35 and released at 14:03:58. The separate Unreal Editor PID **15476** received no input and remained running. No new editor was launched. [decided: Aviv 2026-10-01; measured: `Staging/ModelBank/EDITOR_OWNER.txt`, process checks]

## Before the close

- The fresh in-editor query at 14:00:24 reported PID 32804 on `/Game/Developers/USER/HoudiniCityProof/L_B2_OriginalUntitled_Inspection_20261001`, with the same two actors, **exactly the same 15 dirty Cook package paths**, and **zero dirty map packages** as the earlier review. The package-name set had zero differences. These are five `main_geo_HSM` packages in `GeoCity_request_wiring_UI_2026_09_30` and five `main_geo` plus five `main_geo_HSM` packages in `GeoCity_visual_fix_UI_2026_09_30`, all with `GeoCity_city_v002_3_{374..378}_0` names. [measured: [`OPEN_STATE_20261001T110024Z.json`](../PID32804_OpenState_2026-10-01/OPEN_STATE_20261001T110024Z.json), compared with [`OPEN_STATE_20261001T082352Z.json`](../PID32804_OpenState_2026-10-01/OPEN_STATE_20261001T082352Z.json)]
- The named B2 `.umap` still had SHA-256 `6ABBC0BBD33A005E217A83EB537EF9E70DD2B823522B228F266C4F19415C9FAF`. A file manifest recorded hashes for that map and 64 related existing Cook/autosave files before closing. Ten of the 15 dirty package paths had no Content `.uasset`; the other five had existing files. [measured: [`B2_PID32804_PRE_CLOSE_FILES.json`](B2_PID32804_PRE_CLOSE_FILES.json)]
- The native **Save Content** dialog displayed 15 rows for `GeoCity_city_v002_3_{374..378}_0` and no map row. [measured: [`B2_PID32804_SaveContent_15.jpg`](B2_PID32804_SaveContent_15.jpg)]

## Action and result

The operator clicked **Don't Save** in that dialog. Unreal shut down normally: PID 32804 was absent at 14:03:25, and its log ended with `LogExit: Exiting.` and `Log file closed` at 14:03:24. Its child HARS PID 28836 also exited without a separate operator action. PID 15476 remained running. [measured: `Saved/Logs/Environmentpipeline.log`, process checks]

After the close, all **65** pre-existing manifest files remained present with identical sizes and SHA-256 hashes: the saved B2 map, **39** related Cook Content files, and **25** related Cook autosave files. The map hash remained `6ABBC0BBD33A005E217A83EB537EF9E70DD2B823522B228F266C4F19415C9FAF`. The ten dirty package paths previously absent from Content remained absent; the other five retained their on-disk files. [measured: [`B2_PID32804_POST_CLOSE_FILES.json`](B2_PID32804_POST_CLOSE_FILES.json), fresh path check]

Normal shutdown rewrote `Saved/Autosaves/PackageRestoreData.json` at 14:03:19 with `RestoreEnabled: false` and an empty package list. The Cook autosave copies themselves remained byte-identical. No save, cook, bake, map switch, Cook cleanup, WorldBLD operation, Linear action, or fresh-process reopen was performed. [measured: restore metadata and file manifests; not run: fresh-process reopen]
