# Astra brief: StrawberryBeds v005 (realistic young strawberry beds)

Written 2026-10-11 by the Karmei Yosef operator (Claude Code), for Aviv to pass to Astra.
- **Scope:** offline Blender work only; Unreal is handled by the operator.
- **Deliver to:** `Staging/PazFarm_2026-10-08/AstraModels/Revisions/StrawberryBeds_v005/`.
- **Layout:** the same as FieldCrops_v004: `FBX/`, `Blend/`, `Textures/`, `Previews/`, `Reports/`, `References/`, `MANIFEST.json`, `HANDOFF_CLAUDE.md`, `DONE.md`.
- **Originals:** all earlier deliveries stay unchanged.

## Why

Aviv: the strawberry beds "look very gamified compared to the rest of the vegetation". Your Aleppo pines, olives and vine rows look right; the beds do not.

**Evidence** is in `Staging/PazFarm_2026-10-08/References/Strawberry_2026-10-11/`:
- `aviv_beds_not_on_ground.webp`: Aviv's own view.
- `current_v003_close.png`, `current_v003_15m.png`, `current_v003_60m.png`: our captures of v003 in the scene.

**What reads as game-like:**
1. **A smooth, bright yellow-green block** along each bed. This is the v003 continuous canopy hull, which our v003 brief asked for. In v005 the hull belongs only in the lowest LOD; at near range it must not be visible.
2. **Identical leaf rosettes:** flat and stamped, all the same size, colour and orientation, evenly spaced.
3. **The bed body:** vertical walls, a perfectly straight top edge, and one clean uniform grey-black material.
4. **The colour:** the green is too saturated and too light.

The steps every 4 m in Aviv's view are a placement problem; we fix those in Unreal by tilting each tile to the ground. The rows will also move to real spacing (1.7 m between bed centres, instead of 5.5 m).

## Reference: please collect real photos yourself

- **Gather real photo references** before modelling. Show strawberry fields at planting time in Israel or a similar Mediterranean climate:
  - raised beds with plastic mulch;
  - young transplants;
  - drip irrigation.
- **Record your references:** put the photos you used in `References/` and list their source links in `Reports/REFERENCES.md`.
- **Base the look on the photos**, not on stylised game assets.
- **Comparison preview:** add one side-by-side preview of your best reference photo next to your model, from a similar camera angle.

## Target look: late September, young plants

The scene is late September. In Israel strawberries are mostly transplanted in late summer and picked from winter to spring, so the beds hold **young plants on plastic mulch, with no fruit**. If a rare flower appears in your references, it is optional.

**Raised bed:**
- About 0.20–0.30 m high.
- Top about 0.8 m wide, with rounded shoulders.
- **Sloping sides**, not vertical walls, reaching about 1.0–1.1 m wide at the base.
- Slightly irregular along its length, not a perfect extrusion.

**Plastic mulch film:**
- It covers the top and sides and is tucked into the soil at the base, with a strip of soil thrown over the edge.
- Matte: roughness at least 0.85 and low specular, with no sheen at grazing angles.
- Gentle wrinkles and stretch folds.
- **Colour:** take it from your references. Black is common; white-on-black or silver also occur. Choose one and say which.

**Planting holes:** two staggered rows about 0.30–0.35 m apart, about 0.25–0.30 m apart within each row. Show a little soil in each hole.

**Young plants:**
- Each plant is 0.10–0.20 m across and 0.05–0.12 m tall.
- 3–6 **trifoliate leaves with serrated edges**.
- Colour: natural dark to mid green with a slight blue cast. Add a few yellowed or reddish older leaves.
- Sizes vary, and about 5–10% of the holes have a tiny plant or none.

**Optional details:** a drip tape at the ends of the bed, and small soil clods on the film edges. Include them only if your references show them.

## Tile: keep the convention, so Unreal only swaps the mesh

- **Size:** 4.0 m long, tiling along +Y in Blender (Y = 0 to 4 m).
- **Pivot:** on the ground at the centre of the Y = 0 short end, exactly as v003 (see the v003 MANIFEST notes).
- **Format:** FBX with -Y forward and Z up, in metres.
- **Width:** the base may grow to about 1.1 m because of the sloping sides.
- **Hidden skirt:** the bed sides and the film continue **0.15 m below pivot level**. On uneven ground we sink tiles a few cm, and the skirt prevents visible gaps.
- **Tile ends:**
  - the film and soil run continuously across joints;
  - no end walls on the tile;
  - no plant is cut at a joint.
- **Variants:** 3 tile variants, `SM_PazFarm_StrawberryBed_4m_A`, `_B` and `_C`, with different plant arrangements and missing plants. Unreal mixes them so the 4 m repeat is not visible.
- **End cap (optional):** `SM_PazFarm_StrawberryBedEnd`, about 0.4 m long, with the film tucked down at the row end. Use the same pivot convention (Y = 0 joins the last tile's Y = 4 m end).

## Geometry and LODs

**Geometry:**
- Leaves are solid geometry; any alpha must be solid (1).
- Nanite-friendly.
- About 15–40k triangles per tile.
- **No canopy hull in LOD0.**

**Lowest LOD (`*_LOD3.fbx`):**
- From 60 m to 4 km every bed is drawn only with its lowest LOD (always-loaded Instancing HLOD, no Nanite).
- Because the plants are small, a real bed reads from afar as a film stripe with faint green dots. Build it as a simple mound (top plus sloped sides) in the film colour, with a faint green pattern.
- About 100–300 triangles.
- It must **not** read as a bright green band.

## Previews

- One tile at 1 m and at 3 m.
- A block of 10 rows (1.7 m between bed centres, about 20 m long) on a gentle 3% slope, at 15, 60, 150 and 500 m.
- The side-by-side reference preview described above.

## Common rules (as in v003 and v004)

- **Format:** FBX in metres, -Y forward and Z up. Each lowest LOD is a separate `*_LOD3.fbx` with the same material slot names as its base mesh.
- **Materials:** opaque. BaseColor (sRGB), Normal (OpenGL +Y), ORM (R = AO, G = roughness, B = metallic). No wind and no collision.
- **Checks to include:**
  - fresh FBX import round-trips, dimensions and pivots;
  - triangle budgets, UV0 and finite geometry;
  - solid alpha on all foliage;
  - tile seams between all variant pairs (A-B, B-C, C-A, and each with itself);
  - the originals-unchanged hash report;
  - a short note on how the lowest LOD was built and checked at distance.

---

## Paste-ready message for Astra

> Hi Astra, one more task for the Paz Farm (offline Blender only, no Unreal). Please read
> `Staging/PazFarm_2026-10-08/HANDOFF_ASTRA_StrawberryBeds_v005.md` and deliver to
> `Staging/PazFarm_2026-10-08/AstraModels/Revisions/StrawberryBeds_v005/` in the same layout as FieldCrops_v004.
> Aviv finds the strawberry beds "very gamified" next to your pines, olives and vines (our captures and his screenshot are in
> `References/Strawberry_2026-10-11/`). Please first collect real photo references of strawberry fields at planting time
> (raised beds, plastic mulch, young transplants; Israel or similar Mediterranean climate), keep them with their links,
> and model from them: late-September young plants with trifoliate serrated leaves, no fruit, sloping bed sides, matte
> wrinkled mulch, natural irregularity. Keep the v003 tile convention (4 m along +Y, pivot at the centre of the start end)
> so we only swap the mesh. Add a 0.15 m hidden skirt below ground, and make 3 variants. The v003 green canopy hull must
> not show up close (lowest LOD only), and the lowest LOD should read as a film stripe with faint green, not a bright
> green band. Thanks!
