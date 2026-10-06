# Saved ground painting repair — 2026-10-03

The shared ground shader repair is saved, and Rimal's repaired material and native roads now pass fresh saved-map reopen without recooking. The [bank/material reopen receipt](<C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03/REOPEN_GazaRimal_20261003T172107331435Z.json>) verifies the four selected targets and both corrected normal overrides. The [saved Lit image](<C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03/RIMAL_SAVED_LIT_20261003T1722.png>) shows ground texture and soil patches; the worker inspected that image without operating the editor. User visual acceptance remains open. Shujaiya's new ordinary replacement started 2026-10-03T17:22:46Z and remains in progress.

The [immutable repair receipt](GROUND_SHADER_REPAIR_20261003T160849345599Z.json) records the actual graph, parameters, named saves, original hashes and backup. [Structured fidelity evidence](GROUND_PAINTING_RESULT.json) includes native function hashes and decoded normal-space branches.

Fixed defects:

- The two sand normals were configured as sRGB colour textures. Scoped copies now use `TC_NORMALMAP`, `sRGB=false`, and `NORMAL` samplers in reachable master defaults and the two MI overrides.
- Sand tint previously affected both sand and soil after blending. Each texture now receives its own tint before the existing blend.
- Macro soil sampling now uses the soil’s 2.6 metre tile parameter, rather than the sand’s 2.2 metre tile.
- Weak single-mask variation was replaced by two samples of the same native mask at 36/57 metres. A stable offset, inversion and contrast produce soil patches capped at 60%, with matching colour and normal blending.

The exact saved packages are:

- `/Game/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural`
- `/Game/Project/Shared/SurfacePainting/Appearance_20261003/MI_SurfaceBank_Natural`
- `/Game/Project/Shared/SurfacePainting/Appearance_20261003/Textures/T_Sand_01_Normal_GeoCity`
- `/Game/Project/Shared/SurfacePainting/Appearance_20261003/Textures/T_Sand_02_Normal_GeoCity`

Both existing area profiles retain this shared MI. Geographic heights and masks are unchanged; all 69 bank weight-layer names remain. The four painted targets remain `Sand_01`, `Sand_02`, `Dirt_Path`, and `Sand_Path`. Rimal's fresh repaired-shader reopen verifies them and both corrected normals; Shujaiya's prior actual r018 readback remains the earlier baseline pending its new replacement. Other resolved material parameters and native originals were preserved. The two original normal package SHA256 hashes match before/after; exact hashes and retained backup paths are in the receipts.

Read-only decoding of the installed Engine function confirms `WorldSpace=false` by default. Its `XYZ Texture` branch transforms World→Tangent, matching the retained `tangent_space_normal=True` setting. Both native function paths sample normals as `SAMPLERTYPE_Normal`; the repaired master adds no second colour-to-normal decoding. No change to these defaults is warranted.

Rimal's [saved/native reopen verification](<C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03/SAVED_NATIVE_VERIFICATION_GazaRimal_20261003T172036083014Z.json>) passes 24 original roads, 43 RoadGeo actors, 41 bound native meshes and 2 exact physically supported null placeholders. Actual saved/reopened maximum surface-height error is 7.729658493965417 cm. The saved map retains 43 HDA actors/6 HDA dependencies and 68 owned native actors/65 native dependencies; 16,009 bank instances remain. Geometry/material/transform/collision hashes and geographic footprint checks pass. A fresh editor-process restart was not performed.

Native RGB-mask roughness/AO/height semantics remain unverified, so roughness was preserved. Shujaiya's new ordinary replacement, final two-area visual review and user acceptance remain open. Full MOUT shader reproduction is not claimed. The separate `TOOL_CONNECTION_AUDIT_CURRENT.md/json` records tool handshake and operation scope.
