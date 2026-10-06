# Path B: MW auto-landscape material as the GazaShujaiya ground (DESIGN)

Prepared 2026-10-06 (offline). Nothing here was executed in Unreal. Labels: **M** measured, **D** read from source, **I** inferred.
Short names: LW = `Content/Python/geocity_landscape_workflow.py` (d1a5d5fd), BW = `Content/Python/geocity_bank_workflow.py` (f349d128), MOD = `Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank/geocity_city_module.py` (e67b6e15 = definition_receipt module_sha256), HE = `Plugins/HoudiniEngine/Source/HoudiniEngine/Private/`.

## 1. Decision recap
Aviv chose Path B after the unsaved preview in PID 16824 (`Operator/MWPreview_20261006/PREVIEW_ASSIGN.json`, DesertExample on the Shujaiya Landscape, reverted, nothing saved). His wishes: no grass for now; the MW material ignores the Houdini RoadBed/BuildingPad masks (accepted for now); the colours should be pale Gaza sand, not orange (M: lit ground in preview `01_middle` averages sRGB ≈ (210,170,130)).

## 2. Result: no sealed-Python change is needed (Option 0, recommended)
The "external landscape material" mode already exists in the sealed runtime. It is selected by `landscape_grass.enabled = false` (D):
- **LW:214-216** `prepare()` returns `{'enabled': False, ...}` right after `run.guard()`. Skipped: `_config` (:37-65), Natural parent check (:222-224), Grass Type and owned-graph authoring with its shared saves (:225-354), child create/re-parent (:355-369), normal pins (:370 → :110-121), coverage (:371-383), and the runtime rewrite of `profile.landscape_material` (:384).
- **BW:651, :658, :832, :888** call `verify_landscape` only when grass is enabled, so its parent/coverage/normal checks (LW:413-421) never run for Shujaiya.
- **BW:650 stays**: the cooked official Landscape material must equal `profile.landscape_material`.
- **BW:24-55** `_runtime_profile_merge`: with grass disabled the runtime may not change `landscape_material` (BW:51-54 raises), and `prepare()` no longer changes it. The profile value is authoritative.
- **LW:398-402** `is_native_grass` is False. At BW:862/:883 every StaticMeshComponent is counted only against the bank `expected` set. Foreign meshes, including MW grass, are ignored, so the MI itself must switch MW scatter off (§5).
- **BW:938-986** saves the area MI (under `profile.root`) in the dependency closure when it is dirty. MW vendor packages are outside `root` (BW:948, :977) and are never saved by the lifecycle.
- Grep (M): only LW and BW:52 reference the Natural constants or `MI_GeoCityGround`.

**Unaffected (D):** Rimal (`PermanentIntegration…/AREA_PROFILE.json` 8711cace) and Iran keep their profiles, so they take exactly today's code path. The shared Natural master, base MI, `LG_GeoCity_PermittedGroundGrass` and Shujaiya's old `MI_GeoCityGround` are not touched; the old child stays on disk for rollback.

**One non-lifecycle caller breaks:** `inspect_near_view` (LW:485-515) calls `verify_landscape` with no grass gate and would raise "lost the retained Natural parent". Grep found no caller in `Content/Python` or `Staging` (only copies of the definition). Do not use it for Shujaiya. Option 1 (§6) makes it fail with a clear message instead.

## 3. Regeneration: the MW MI is re-bound on every ordinary cook
Chain (D):
1. BW:511 writes `profile.landscape_material` into the HDA string parameter `landscape_material`; BW:526-527 reads it back.
2. MOD:627-629 checks the path pattern `/Game/…​.Asset` (the new path matches). MOD:653-662 sets the prim attribute `unreal_material` on height and mask. `cook_surface_palette` (MOD:3824-3826, :3861, :3885) sets it on every paint-layer volume.
3. HE `HoudiniLandscapeTranslator.cpp:561-567` reads `unreal_material`. `HoudiniLandscapeUtils.cpp:859-883` (called at :659 and :1454) sets `LandscapeProxy->LandscapeMaterial = Material`. HE creates no MI of its own, because `unreal_material_instance` is not used.
4. Bake: `HoudiniBakeLandscape.cpp:543-545` returns early (no HE MI). `HoudiniEngineBakeUtils.cpp:6721-6729` duplicates the material only if it lives in the temp Cook folder; ours lives in `/Materials`. The baked Landscape keeps the MI, and BW:650 asserts it.

**M:** the B2 run (PID 10460, 18:43Z) reached `baked_saved_verified` with `parameters.landscape_material` equal to the profile value (`…/LAST_SUCCESSFUL_WORKFLOW_STATE.json`). The same route delivered the profile material then.
**I:** every ordinary regeneration will re-bind `MI_GeoCityGround_MW`. This stays inferred until one ordinary regeneration runs after Path B. A manual assignment without the profile change would be reverted by the next regeneration, which is why the profile changes first.

## 4. Profile change (`pathb_profile_patch.py`)
Exactly two leaves change. `landscape_material` becomes `…/BankIntegration_v015/Materials/MI_GeoCityGround_MW.MI_GeoCityGround_MW`, and `landscape_grass.enabled` becomes `false`. All other Grass settings stay in place for rollback.
- The dry run (M) gives before 1328d5bb → after **54e3b19c990e7661ffbc74c12b1e9769215951a9f130ac67e806a088d6ec99ed**.
- With `--external-block` (Option 1 only), one key `external_landscape_material` is added. The after hash is **fe23b280c9a412a97af0eaea60634a0e190c03f33c5c15edcb305c15fb94056c**.
- The format is preserved byte-exactly (M: both Gaza profiles round-trip as indent 2 + CRLF).
- The script backs up the profile, replaces it atomically, writes a record, and has a `--rollback` mode.

## 5. The material instance `MI_GeoCityGround_MW` (`pathb_assign_and_save.py`)
- **Path:** `/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_MW`. Class MaterialInstanceConstant, metadata `GeoCityOwner=GeoCity_GroundPathB_MW`.
- **Parent: recommend `MTL_MWAM_Landscape_DesertExample`** (chain DesertExample → `MTL_MWAM_AutoMaterial_MASTER`).
  - It is exactly what Aviv approved: SandA/SandC/Stones textures, UV 512/6144, slope powers, roughness 1.3/1.2, Water off, Snow-slot height 0.
  - It needs only 17 overrides, against about 41 under the master.
  - Risk: a vendor update to DesertExample would change our look. The vendor hashes are pinned (DesertExample 0fc96edd…, master 981e207c…) and checked on every apply, save and verify.
  - The script also supports `parent: "master"`. It then replicates DesertExample's 13 scalar and 11 texture overrides (M: MW_INVENTORY.json).
- **No grass (M, native graph):** `MW_[x]_Use{Rock,Stones,Grass,Dirt,Snow}Procedurals` feed only `LandscapeGrassOutput_0` (five `LGT_MWAM_*` types). DesertExample leaves Rock, Stones and Dirt ON, so MW scatter would spawn. The small dark specks in the preview are probably that scatter (I). All five are set OFF and confirmed by readback.
- **Tint mechanics (M, `MF_MWAM_DefaultLayer`):**
  - `ColorCorrection` is multiplied in only when the layer's `MW_[x]_Use<Layer>Advanced` is true. DesertExample has it true only for Dirt and Grass.
  - The script sets all five Advanced flags true. With `*NormalIntensity` at 1.0, the extra normal multiply is identity.
  - It also pins `MW_UseWater` = false and `MW_UseSnow` = true.
  - I: with `MW_SnowWorldPosition` = 0 and terrain at 38-50 m (profile probes), the Snow slot (SandA) probably covers flat ground. That is why `UseSnowAdvanced` matters.
- **Colours (`TINT_PRESETS.json`, `pathb_tints.py`):**
  - Multipliers are computed in linear space from the measured texture means, toward a pale-sand chromaticity.
  - Gaza pale sand needs R < 1 and G, B > 1. Dirt keeps DesertExample's own ×1.25. Rock (grey gravel on steep ground) is lifted ×1.5.
  - P1 is the recommended start: Snow/Grass (0.851, 1.360, 1.589), Dirt (1.063, 1.700, 1.987), Stones (0.820, 1.382, 1.706), Rock (1.829, 1.815, 1.524).
  - P2 is more neutral and paler; P3 is mild.
  - Lighting, tonemapping and auto exposure are not modelled. Run an unsaved apply → capture → choose loop, at most 4 applies per PID, then save.
- Macro, slope, UV and roughness settings keep the DesertExample values.
- **Modes:**
  - `inspect` is read-only.
  - `apply` creates or updates the MI, verifies the parent chain, switches and tints by readback, assigns the single Landscape, and checks the component material chains. It does **not** save.
    - Pending measurement: whether `get_material(0)` returns the per-component combination MIC; read `sample_component_chain` before calling rebinding proven.
  - `save` saves the named MI package and the map (`mi_and_map`), or the MI only (`mi_only`). It refuses if anything else is dirty, if any MW package is dirty, or if the MI, disk or vendor state drifted since apply.
  - Every run writes an exclusive receipt and checks the lease, PID, map, sole editor, paused HE, HDA auto off, autosave off, one Landscape, no proxies, and that the Landscape lives in the map package.
  - The code identity check (sha + code-object signature) follows the s1_verify pattern.
- **Fresh check:** `pathb_verify_fresh.py` runs read-only in a new PID. It checks:
  - the Landscape material equals the profile value and the MI path;
  - there is one Landscape;
  - every component binds the MW MI and none the old one;
  - the MI chain, switches and tints;
  - the saved hashes;
  - Shujaiya's old child and the MW vendor files are unchanged. The shared Natural assets are advisory only, because Rimal/Iran runs re-save them.
  - nothing is dirty before or after.

## 6. Optional hardening (Option 1: needs a reseal)
`geocity_landscape_workflow.patch` adds 32 lines to LW only; the patched file is in `patched/` (sha 2bc51f97…, `py_compile` OK). It changes two behaviours:
- (a) If grass is disabled **and** the profile carries `external_landscape_material`, `prepare()` now fails before Cook when any of these hold:
  - the MI is missing, outside `<root>/Materials/`, or not a MIC;
  - its parent chain differs from the profile or contains the Natural master/base;
  - any listed procedural switch is missing or ON.

  It returns provider `external_landscape_material` with the chain into `state.landscape_grass_connection`. Without the block, behaviour is unchanged.
- (b) `verify_landscape` (and so `inspect_near_view`) raises a clear "Natural/Grass contract only" error when grass is disabled.

Grass-enabled profiles (Rimal, Iran) follow identical code. No BW patch is needed. Option 0 already catches a missing or wrong MI after Cook (BW:650); it does not catch later re-parenting or switch drift. That residual gap is what Option 1 closes.

## 7. Order (details in RESEAL.md)
1. Profile patch with the editor closed.
2. (Option 1 only: patch and reseal.)
3. Launch with the new profile hash and map 4efebdfb.
4. Manager writes the authoring lease.
5. Run `inspect` → `apply` P1 → capture → (re-apply P2/P3) → `save`.
6. Exit without further saves.
7. Fresh launch → verify lease → `verify` plus captures.
8. Write the B3 ratification record.

## 8. Decisions for the manager
1. Option 0 (no code change) or Option 1 (hardening plus reseal).
2. Parent: DesertExample (recommended) or the master.
3. The first tint preset, P1 (recommended), and who signs off the colour (Aviv, from the captures).
4. Save route:
   - (a) Save the MI and the map now. The survival proof is the next ordinary regeneration, re-verified with `expected_map_sha256`.
   - (b) Save the MI only, then run one ordinary regeneration. That proves survival on the real save path, but needs ordinary-generation activation.
