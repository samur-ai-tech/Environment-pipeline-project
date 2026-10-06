# Path B capture plan (GazaShujaiya)

**Cameras:** reuse the three presets `close` / `middle` / `wide` from `Staging/GroundPainting_2026-10-04/CAMERAS_GazaShujaiya.json` (sha256 9cd59936…, FOV 65), all LIT.
- Compare each image side by side with Aviv's approved MW preview: `Operator/MWPreview_20261006/MWAutoLandscape_Shujaiya_preview_0{0_close,1_middle,2_wide}.png`.
- I: the preview used the same preset names. Confirm the eye/target positions from the receipt.

## When
1. **Authoring PID, unsaved loop:** run `apply P1` → capture 3 shots. If needed, run `apply P2` or `P3` (new label each time) → capture 3 shots. That is at most 4 applies per PID. Aviv picks a preset, and only that preset is saved. The final apply must be the chosen preset, because `save` accepts only the latest apply of the PID.
2. **Fresh verify PID, evidence:** after `pathb_verify_fresh.py` returns VERIFIED_READ_ONLY, capture the same 3 shots. These are the acceptance images.
3. **Optional, after the first ordinary regeneration:** capture the same 3 shots. These are the regeneration-survival evidence, together with the verify re-run using `expected_map_sha256`.

## How (either route)
**Route A: MCP CaptureViewport** (acceptable, light).
- Place the camera with one tiny inline call per shot: `UnrealEditorSubsystem.set_level_viewport_camera_info(eye, rotator)`, with the rotation from `s1_capture.rotation_for(eye, target)`.
- Then call CaptureViewport. Do not touch CVars or exposure; auto exposure is fine, because the preview also used it.
- Wait for shader compilation of the new static permutation (the first apply compiles it, which can take minutes) before the first shot. Re-shoot if the ground still shows the default checker or grey material.
- Store PNGs in `PathB_MW/images/<label>_<NN>_<shot>.png`.

**Route B: pinned `S1_Prep/s1_capture.py`** (fe5156d4…, phased begin/prepare/request/complete/end).
- Use ARGS `owner: GEOCITY_GROUND_PATHB`, `exposure: {mode: auto_recorded}`, `residency: {mode: none}`, `viewmode: LIT`.
- During the unsaved loop, also set `allowed_dirty_content: ["/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_MW"]`. In the verify PID, use `[]`.
- Caveats:
  - Its `force_bound_textures` residency mode targets the Natural child's parameters, so do not use it.
  - Its receipt field `material_begin` reads the old `MI_GeoCityGround`, which is now unbound, so ignore that field.
  - It writes under `S1_Prep/` (CAPTURE_<label>.json, images/), not under PathB_MW.

## Quantitative helper (offline)
`python pathb_png_mean.py <png> 1250,520,1500,640 80,380,280,500 1100,650,1400,780 300,450,450,560`, using the middle shot at the preview's 1879×820. For other sizes, pick open-ground boxes once and keep them.
- **Rejected orange (M):** sRGB ≈ (204-216, 167-178, 126-135). The R−B gap is about 80.
- **Rule of thumb for "pale Gaza sand" (proposal):** R−B ≤ 40, G/R ≥ 0.90, and mean luminance not darker than the preview. This only supports Aviv's visual sign-off; it does not replace it.

## Not part of this plan
No post-process, exposure lock, CVar or streaming changes; no Save; no Cook/Bake; no `get_material_info` MCP tool. That tool dirtied 15 MW packages on 2026-10-05.
