# S1v2 design: Gaza ground material (stochastic sampler for every texture + smooth macro field)

DESIGN ONLY, 2026-10-06. No editor, MCP or process was used, and nothing under Content/ was changed.

Labels: M = measured (file, graph dump, offline pixel/PNG analysis); D = documented; I = inferred. Graph: `S1_Prep/receipts/GRAPH_BEFORE_23156.json` (graph_sha256 605c55d0, 1015 nodes). Companion: `S1V2_SPEC.json`.

## 0. Correction to the brief's premise (M)
- **The live Gaza anti-tiler is NOT the Iceland functions.** It is the hand-built `GeoCity_GroundStochastic_20261005` chain, and it covers Sand_01 only: Per-cell hash translation with 4 taps: `Custom_0..3` (near) and `Custom_4..7` (far). Cells are `Floor_0/1` of `Multiply_23/29` (UV x `GeoCity_CellScale`). Quintic weights `ComponentMask_17/18` (near X/Y) and `_19/_20` (far). Fetches `TextureSample_37-56` in TMVM_DERIVATIVE with untranslated `DDX_0/DDY_0` and `DDX_1/DDY_1`, so there are no cell seams. Cell blends `LinearInterpolate_48/_57`. Distance blend `_64` (color) and `_65` (normal), driven by `Saturate_1` SharedDistanceAlpha (Shujaiya: start 12 m, range 60 m).
- **The 9 Iceland `MF_DistanceCellBlend` calls have ZERO consumers.** They are `MaterialFunctionCall_2/4/6/24/26/28/32/34/36`. `MF_TextureCellBomb` and `T_Voronoi_Perturbed_4k` are reachable only through them. Only `MF_NormalIntensity` (`MFC_8/22/30/37`) is live. CellBomb (I, string scan) is one Voronoi-ID fetch plus one rotated fetch with no DDX/DDY. That gives hard cell borders, so v2 does not revive it.
- **v1 did NOT bypass the stochastic chain.** Its anchor `Multiply_5` is downstream of `LinearInterpolate_64`. It bypassed only `Multiply_8` (the T_MacroVariation macro, ±8%) and `LinearInterpolate_42`/`Clamp_21` (soil lerp, alpha 0.025-0.1).
- `Ground_MacroContrast` is unreachable (`MATERIAL_GRAPH_REACHABILITY_r030.txt`).

## 1. Diagnosis: v1 against the images
**What the eye sees** (A2 is a 1879x820 MCP viewport grab with other framing, so it is not a controlled comparison):
- **B0:** close up, pale tan gravel-sand with fine grain and no cells. Middle and wide, one flat pale beige with no zones.
- **A1:** close: salmon/orange stains 5-10 m across, with 1-3 m edges, on paler sand that has less detail; middle: a "camouflage print", one blotch size everywhere; wide: the same print over the whole terrain, plus an orange cast at distance.
- **A2 (t001):** fainter blotches, but the wide view shows a regular lattice of small rectangular dabs in rows, plus a pinkish cast.

**Causes:**
1. **Hard blotches.** `PatchMaskB/C/Soil` = SmoothStep(PatchLo 0.40-0.45, PatchHi 0.65-0.70) of NoiseNear R/G/B. The noise channels (M, from the source PNG in TEX_MW_Noise_msk) are independent, with mean 0.35 and sigma 0.25, and ~5% are clipped to 0. Only the top ~25% passes, through a narrow ramp. The result is islands, not fades.
2. **Repetition A.** The `MF_GeoCity_MacroNoise` near UV is axis-aligned on a 37 m tile. M: 62% of the variance is at periods of tile/4 or more, which gives 6-12 m blobs that repeat every 37 m. This is the A2 lattice.
3. **Repetition B.** GroundB/C/Soil go through `MF_GeoCity_DistanceBlend`, a plain near fetch plus a far fetch with no cell offset. So the 5.12, 4.7 and 4.0 m tiles repeat inside every patch.
4. **Orange.** The SandA/SandC thumbnails have R/B 2.8 and 3.1 (M), against ~1.8 for the gravel (I). Soil = MW Dirt x (2.3, 2.15, 2.0). The far path applies FarSaturation 1.2 x FarAmount 0.75 (0.6 in t001).
5. **Bias.** `ValueNoise` = nn_g + nf_g - 1 has a mean of about -0.29, which darkens everything by 3-5%. RoughVar and SteepJitter are centred at 0.5, not 0.35. NormalFade 0.7 flattens the middle distance. `SteepStonesMask` = patch_s x 0.35 puts blotches on the collars.

## 2. v2 design (one switch; Gaza children only)
**(a) `MF_GeoCity_CellSample` (new, parameter-free) is the one sampler for every texture.**
- **Inputs:** Tex, NearUV (the texture's own untranslated UV), FarScale, NearHash0-3, FarHash0-3, NearWX/WY, FarWX/WY, DistanceAlpha.
- **Body:** DDX/DDY of NearUV. FarUV = NearUV / max(FarScale, 1), with the derivatives scaled the same way. 4 near + 4 far TMVM_DERIVATIVE fetches at UV + hash_i, all Shared:Wrap, combined bilinear-quintic with the EXISTING weights. Outputs: Color = lerp(Near, Far, DA), plus Near and Far.
- **Wiring.** Hashes, weights and DA come from `Custom_0-7`, `ComponentMask_17-20` and `Saturate_1`. Every routed texture therefore shares Sand_01's lattice (2 m near, 4 m far), its offsets and its distance law. B0 shows no cells. Tile size enters only through NearUV.
- **Five calls:** GroundB = SandA and GroundC = SandC, with NearUV = LandscapeXY x 100/TileCm x `ScalarParameter_8`. Steep = `Sand_02_Albedo` (`TextureObjectParameter_157`), XY UV from `VectorParameter_178`, far scale `Clamp_9`. RoadBed = `Dirt_Path_Albedo` (`_150`), NearUV `Multiply_17`, far scale `Clamp_12`. Pad = `Sand_Path_Albedo` (`_161`), NearUV `Multiply_19`, far scale `Clamp_16`. Tints are the existing `VectorParameter_179/174/183`. The variants are albedo-only; Road, Pad and Steep keep their normals (`Normalize_4/5/3`).
- **Ground base = the full existing Gaza ground.** Color comes from `LinearInterpolate_42` and normal from `Normalize_9`. With switch True and every amount at 0, Ground equals B0. This closes v1 caveat 15. Ground = lerp(lerp(base, B x TintB, VariantB x AmountB), C x TintC, VariantC x AmountC).

**(b) `MF_GeoCity_MacroField` (new; replaces MacroNoise).** It makes 3 Shared:Wrap MASKS fetches of one noise texture.

| Octave | Channel | Tile | Period ≈ tile/3 (M) | Rotation | Offset |
|---|---|---|---|---|---|
| o1 | R | 127 m | ~40 m | 0° | (0.13, 0.71) |
| o2 | G | 463 m | ~150 m | 37° | (0.37, 0.61) |
| o3 | B | 1531 m | ~500 m | 71° | (0.83, 0.29) |

- The tile ratios (3.65, 3.31) are non-integer. Each octave is normalised as z_i = (n_i - NoiseMean 0.35) x NoiseInvStd 4.0 (M).
- **Outputs.** All are linear: no thresholds and no PatchLo/Hi. Value = 0.25 z1 + 0.35 z2 + 0.40 z3 (sigma 0.59); HueT = sat(0.5 + HueGain x (0.4 z2 + 0.6 z3)); VariantB = sat(0.5 + VariantGain x (0.6 z1 + 0.4 z2)); VariantC = sat(0.5 + VariantGain x (0.4 z1 - 0.6 z2)); Fine = z1.
- **Properties.** B and C are uncorrelated. B leans warm (r +0.31 with HueT) and C leans cool (r -0.46). A gain of 0.35 maps ±2 sigma to 0..1, so the fades follow the whole noise gradient (10-40 m wide).

**`MF_GeoCity_MacroColor` (new body)** runs after the height-blend LLB, so it is continuous across all 4 layers:
- tint = lerp(1, lerp(HueB, HueA, HueT), HueAmount)
- value = 1 + ValueAmount x clamp(Value, -2, 2)
- out = sat(far-lerp(Base x tint x value))

**(c) Distance.** Each CellSample keeps the live `_64` near/far law at two scales: Ground 2/4 m, B/C x4, and Road/Pad/Steep at their existing FarScale. The dead Iceland calls are untouched.

**(d)-(f) Kept from v1:**
- **Height blend:** 3 LB_HEIGHT_BLEND LLBs with `MF_GeoCity_HeightBlend`. Heights come from `LinearInterpolate_48/57` and the CellSample Near/Far outputs.
- **Slope:** `MF_GeoCity_SlopeBlend` with Noise = sat(0.5 + 0.25 x Fine). Steep pin = lerp(Ground, SteepCell x tint, alpha). SteepStones is removed.
- **Switch:** one switch, `GeoCity_S1_Enable` (3 StaticSwitch nodes, default False). Only the color, normal and roughness root bindings move. The AO root `LandscapeLayerBlend_0` and all existing nodes are untouched.
- **Iran and base MI:** never written. Defaults are neutral: amounts 0, tints 1, Steep 0/0.001, HeightAmount 0.
- **Grass:** untouched, with no `GeoCity_LandscapeGrass` desc.
- **Normal:** NormalFade toward (0, 0, 1) by DA.
- **Roughness:** LLB + RoughVar x clamp(Fine, -2, 2) x 0.5.
- **Contact:** unchanged and gated at 0. It now targets the road CellSample.

**Reused from v1:** Builder, SlopeBlend, HeightBlend, height_llb, contact, and the switch/probe/compile/tune/save/verify machinery.

**Removed:** `MF_GeoCity_MacroNoise` and `MF_GeoCity_DistanceBlend`, plus 19 params:
- Soil_*;
- PatchLo/Hi;
- GroundB/C_Normal and their NormalStrength;
- Variation*;
- SteepStones;
- MacroTileNear/FarCm.

**Added:** 7 params (MacroTile1/2/3Cm, NoiseMean, NoiseInvStd, HueGain, VariantGain), for 40 in total (v1 had 52).

**Fetch budget.** Graph-level texture-sample nodes per painted-layer set (I; compiled stats must confirm):

| | Shared | Ground | +Road | +Pad | +Steep | Ground only | All 4 |
|---|---|---|---|---|---|---|---|
| v1 | 4 | 24 | 9 | 8 | 12 | 28 | 57 |
| v2 | 3 | 44 | 8 | 12 | 14 | 47 | 81 |

- Each CellSample costs 8 fetches.
- Sampler states: +0. All new fetches are Shared:Wrap, so the 16-state limit (D) is untouched. About 12 unique textures are used, of 128.
- Cost option: anchor Ground at `Multiply_8`/`Normalize_0` instead. That saves 8 fetches and drops only the ≤10% soil lerp.

## 3. Shujaiya first-try values (child only; INFERRED from images and measurements)
- **Base and brightness.** Base unchanged from B0 (pale gravel, linear ~(0.298, 0.238, 0.166), I). ValueAmount 0.07 gives ±8% at ±2 sigma with no mean bias.
- **Hue.** HueAmount 1, HueGain 0.35. HueA warm (1.025, 1.00, 0.975); HueB cool (0.975, 1.00, 1.025). The pair is symmetric, so HueT 0.5 is exactly neutral and there is no global warm bias. Luminance stays within ±0.35%. R/B shifts ±5% at the extremes and ±2.5% at ±1 sigma.
- **Variants.** VariantGain 0.35; GroundB_Amount 0.45 and GroundC_Amount 0.35 (mean coverage ~22% and 18%). Tiles 512 and 470 cm, FarScale 4. Tints are value-matched: gravel mean x a warm/cool offset, divided by the MW thumbnail mean (M; ±30%). GroundB_Tint (1.02, 1.42, 1.49): 1.00x gravel luminance, R/B 1.93. GroundC_Tint (1.25, 1.92, 2.28): 1.00x gravel luminance, R/B 1.71.
- **RoadBed:** MW Dirt col/nrm, Tint (3, 3, 3), 400 cm: 0.78x ground luminance.
- **Pad:** MW Stones col/nrm, Tint (2.9, 2.85, 2.75), 300 cm: 0.85x, slightly greyer.
- **Macro:** MacroTile1/2/3Cm 12700/46300/153100, NoiseMean 0.35, NoiseInvStd 4.0. Far path off (FarAmount 0, FarSaturation 1, FarValue 1).
- **Steep:** SteepLo/Hi 0.25/0.45 (hides the 0.22 collar rings), SlopeMix 0.5, SteepJitter 0.10.
- **Height:** Bias 0.85, Contrast 2.0, Amount 0.6.
- **Other:** NormalFade 0.5, RoughVar 0.03, Contact 0, GrassCoverage 0.0.
- **Tint correction.** In one BaseColor buffer-visualization frame, measure B-dominant, C-dominant, road and pad patches against open gravel. Scale each tint by target/measured. This takes one tune and no re-apply.

## 4. Edit script: a new file is cleaner
Copy `s1_material_edit.py` (sha 5c48daaf) to `s1v2_material_edit.py`. Reasons:
- `receipts/S1_APPLY_ONCE.json` already latches v1, and the v1 receipts stay as history.
- About 1700 reviewed lines (guard, lease, inspect, backup, compile, tune, save, verify) are reused verbatim.

Changes:
1. **Constants:** `MARK`/`OWNER_TAG` → `GeoCity_GroundS1v2_20261006`; schemas → *.v2. `RECEIPTS` → `S1v2/receipts`. Latches → `S1V2_APPLY_ONCE` and `S1V2_TUNE_ONCE_*`. Root decides `S1_SCOPE` and the activation template.
2. **`ANCHORS`:** Add: `ground_full` (LinearInterpolate_42) and `ground_full_normal` (Normalize_9); `near_hash0-3` (Custom_0-3) and `far_hash0-3` (Custom_4-7); `near_wx/wy` and `far_wx/wy` (ComponentMask_17-20); `road_uv` (Multiply_17) and `pad_uv` (Multiply_19); `steep_far`/`road_far`/`pad_far` (Clamp_9/12/16). Drop the old near/far anchors for steep, road and pad, and `ground_color`/`ground_normal`.
3. **`resolve_anchors`:** add by-name parameter anchors in the active set, as `ROUGHNESS` does: Sand_02_Albedo, Dirt_Path_Albedo, Sand_Path_Albedo; Sand_02_Tint, Dirt_Path_Tint (the active `VectorParameter_174`, not `_69`), Sand_Path_Tint; Sand_02_TileCm, GeoCity_PatternScale.
4. **`PARAMS`:** the SPEC's 40-entry table. Delete `VARIATION` and its gate in `plan_children`; keep the `CONTACT` gate.
5. **`Builder`:** add `ddx`/`ddy` (pin `Value`) and `sample_grad`. `sample_grad` sets TMVM_DERIVATIVE first, then links `DDX(UVs)`/`DDY(UVs)`, asserting both pins exist.
6. **`FUNCTIONS`:** Add `body_cell_sample` (COLOR:8), `body_macro_field` (MASKS:3), and a new `body_macro_color`. Delete MacroNoise and DistanceBlend. In `check_function`, allow DDX/DDY nodes, and assert derivative mode with both pins connected on every CellSample fetch.
7. **`build_branch` and `apply()`:** rewrite `build_branch` per the SPEC `branch`. In `apply()`, the planned census has `master_samples` = [] and calls = CellSample x5, MacroField, MacroColor, SlopeBlend, HeightBlend x4.
8. **Mock and pins:** Add the `DDX(UVs)`/`DDY(UVs)` pins to the offline mock and regenerate the expectations. Point `s1_verify.py` at the v2 file. Re-pin SCRIPT_PINS and the activation `script_sha256`.

## 5. Order, gates, risks, out of scope
**Order:**
1. Root closes PID 23156 with "Don't Save". This discards v1; its MFs were never saved.
2. Re-check the `Before/S1B_20261005T202836Z` pins.
3. Fresh paused editor: inspect, then apply. The child overrides only the switch.
4. Capture I0 with the B0 cameras.
5. Tune t001 to the §3 values, then capture A3.
6. Aviv reviews.
7. Save, Rimal and verify, as in v1.

**Gates (I):**
- I0 vs B0: compare in BaseColor buffer visualization, or in Lit against a noise floor measured from two B0-condition captures (exposure is not locked; Lumen/TAA vary). Hold GrassCoverage equal to the B0 state, or mask grass pixels. Pass = Ground-only regions within that floor.
- A3: block-mean luminance sigma 3-6% at middle and wide distance, with no 2-D autocorrelation peak at 20-60 m.

**Risks:**
- About +19 fetches on Ground-only components, unprofiled.
- Albedo-only variants over the gravel normal may show at close range.
- **Deviation from brief (a):** only albedos are routed through CellSample. The Steep normal stays triplanar (`Normalize_3`), and the Road/Pad normals stay on the existing fixed-offset 2-tap (`Normalize_4/5`). Option: add a NORMAL-sampler twin, `MF_GeoCity_CellSampleNormal`, for those three (+8 fetches each, +24 total). It is off by default for cost.
- The tints are INFERRED: the thumbnails carry ±30%, and the source channel order is inferred.
- Steep albedo stretches above 40°.
- LB_HEIGHT_BLEND identity at Amount 0 is INFERRED.
- The Python `DDX(UVs)` pin is unproven.
- The MW licence is unverified. Fallback noise: StarterContent `T_Perlin_Noise_M` (M: grayscale, mean 0.51, sigma 0.155). Using it needs a wider `texture_fit` allowlist, NoiseMean 0.51 and InvStd 6.5.

**Out of scope:** contact at bases and curbs (defect 5), binary 1 m RoadBed/Pad edges (S3 HDA feather), RVT, Rimal slivers, the faceted hill, grass, exposure.
