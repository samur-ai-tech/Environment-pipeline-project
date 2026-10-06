**V2 should improve colour fades, but I would revise it before implementation. It does not yet justify “no visible repetition at 5–60 m.”** I reviewed the supplied designs, graph evidence and six B0/A2 images. No files or editor state were changed. Values below are suggested starting points, not measured Gaza calibration.

1. **Expected visual result and weaknesses**

   A2 visibly introduces repeated, similarly sized dabs. Removing its narrow noise thresholds is the right correction. V2’s continuous macro field should produce softer colour changes.

   However, several problems remain:

   - **The old pattern survives inside Ground:** `LinearInterpolate_42` retains the soil branch driven by the **20–35 m clamped mask**, including its plain-sampled colour and normal. The original ±8% macro also remains underneath the new macro.
   - **Soft colour variation does not soften semantic boundaries.** Height blending cannot create a several-metre transition where RoadBed/Pad weights are binary. Contact remains unsolved.
   - **Four-tap crossfading can reveal its lattice through detail contrast:** detail is strongest around cell corners and softer where several samples mix. Seam-free does not mean visually pattern-free.
   - **Near-minus-far albedo is not a heightmap.** Different scales and random offsets compare unrelated features; using this to drive layer dominance can introduce arbitrary mottling.

   I would retain **weight blending for this colour revision**, defer height blending until feathered weights exist, and evaluate repetition in both **BaseColor and Lit**, including camera movement. The proposed autocorrelation check at 20–60 m misses the **2–4 m cell lattice**.

2. **Reusing the hash-grid sampler**

   **Mathematically sound for translated albedo samples**, provided adjacent cells share consistent neighbour hashes and derivatives come from each texture’s continuous UVs. Reusing Sand_01’s weights with another texture scale does not inherently create discontinuities.

   It is nevertheless expensive and couples every material to the same locations of maximum crossfade softness. Translation also preserves recognisable directional features; it does not scramble orientation.

   **Leaving structured normals unchanged is the largest visual weakness.** Road/Pad highlights will still repeat and will no longer correspond to their shifted stones or dirt. Steep is worse: XY albedo plus triplanar normals describes two different surfaces.

   My recommendation: use matching UVs, hashes, weights and distance blends for **albedo and normals on Road/Pad**; preserve matching projection on Steep. Decode normals with a **NORMAL sampler**, blend and normalize. If rotation is introduced, transform normal XY consistently. Albedo-only Ground variants are acceptable only when they behave as subtle colour stains over compatible fine-grain relief.

   Start with variant amounts **B=0.25, C=0.20**, and **FarScale=2**, not 4. Also correct the coverage claim: sequential lerps give B weight `b×(1−c)`, so the proposed mean contribution is approximately **18.6% B and 17.5% C**, not 22.5% and 17.5%.

3. **Macro scales and dry-sand palette**

   Recentering, additive octaves and restrained warm/cool multipliers are sensible. **127/463/1531 m is too weighted toward broad variation for this particular 5–60 m complaint**: its dominant features are approximately 40/150/500 m.

   I would start with **61/211/733 m tiles**, weights **0.45/0.35/0.20**, rotations **17°/53°/89°**, retaining independent offsets. With the supplied texture spectrum, that introduces roughly **20/70/240 m features** without returning to small camouflage patches. These are starting scales; prime numbers themselves provide no special protection against repetition.

   Use **ValueAmount=0.07**, **HueGain=0.25–0.35**, and the proposed symmetric hue endpoints. They produce about **±5% R/B ratio variation**, not ±5% per-channel changes. Keep `FarAmount=0` initially.

   Correct two assumptions: `0.07×clamp(Value,−2,2)` permits **±14%**, although approximately ±8% is the estimated two-sigma range; and globally centred noise can still have a local bias across one area. Measure means in **linear sampled colour**, not display thumbnails. The proposed tint multipliers up to 3 need particular scrutiny for clipped highlights.

   Start **NormalFade=0.25–0.35**, rather than 0.5. Additional flattening risks recreating the pale, featureless middle distance.

4. **Python/API and preservation pitfalls**

   **Derivative pins:** your saved `TextureSample_37` already exposes `DDX(UVs)`/`DDY(UVs)`; `DDX_0` exposes `Value`. Set `TMVM_DERIVATIVE` first, enumerate pins, assert every connection succeeds, then verify edges. Compute gradients before `Floor`/hash offsets; divide far gradients by FarScale. Keep derivative-dependent logic out of vertex/Grass paths. [Epic texture-expression reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/texture-expressions?application_version=4.27)

   **Height pins:** construct and assign the `LayerBlendInput` array before connecting `Height Sand_01`, etc. Heights must match across colour/normal/roughness. `PreviewWeight` is not a runtime fallback. All-height blends can produce zero-contribution regions and invalid normals; `HeightAmount=0` identity remains an implementation assumption, not an API guarantee. Keeping weight blends avoids this unnecessary risk here. [Epic landscape guidance](https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-material-expressions-in-unreal-engine)

   **Static switch:** the installed UE 5.8.2 header confirms `set_material_instance_static_switch_parameter_value` exists. Update functions/master, set the Gaza child override, and allow instance compilation to finish. A child’s Boolean readback does **not** prove every Landscape component MIC is rendering that permutation; inspect their effective inheritance and actual output. One parameter shared by three switch nodes is sound. Iran remains equivalent only if each False branch and every reachable existing dependency stays unchanged. [MaterialEditingLibrary](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MaterialEditingLibrary)

   **Shared:Wrap:** set `SSM_WRAP_WORLD_GROUP_SETTINGS` on the actual samples inside functions. Texture objects do not enforce it. Match COLOR/NORMAL/MASKS sampler types and texture settings. Shared samplers address sampler-state pressure, **not texture-fetch cost**; verify compiled Landscape permutations against the 16-state budget. [TextureSample API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MaterialExpressionTextureSample)

5. **Cheapest standard alternative**

   My preferred first revision keeps the existing Sand_01 sampler and adds **only macro colour variation**, behind `GeoCity_S1_Enable`:

   `WorldPosition → ComponentMask RG → Divide by tile size → rotated UVs → 3 Shared:Wrap T_MacroVariation samples → Subtract measured mean → weighted Add → brightness Multiply + restrained tint Lerp → existing blended BaseColor`.

   Keep existing layer names, Grass nodes and weight blends. This adds **three texture fetches**, versus the design’s estimated **47 Ground-only / 81 all-layer fetches**. It improves colour organisation but cannot guarantee removal of normal-driven repetition.

   Where recognisable texture motifs remain, use **Epic `Texture_Bombing` selectively**, with paired albedo/normal calls, identical UVs, **Offset≈1**, `Is Normalmap=True` for normals, and Height Lerp initially disabled. `TextureBomb_SingleSample` is a helper, **not a complete seam-blended one-fetch substitute**. Inspect internal sampler sources before use. [Epic implementation author’s explanation](https://forums.unrealengine.com/t/texture-bombing/65652)

   The installed engine also contains **`TextureVariation`** under `Engine_MaterialFunctions03/Texturing`; do not assume a generic `MF_TextureVariation` has the same interface or cost. Plain distance scaling is cheaper to assemble—two samples at **UV and UV/2**, lerped over approximately **15–60 m**—but only changes repetition scale. **Lerp sampled results, not UVs**, to avoid texture swimming.