# StrawberryBeds v005 — independent QA plan

2026-10-11. Planning only; no model has been accepted or edited by this review. Scope is the v005 offline delivery. Preserve earlier deliveries and do not operate Unreal, Content, maps, the bank, Houdini or git.

## Evidence and reference gate

Read `HANDOFF_ASTRA_StrawberryBeds_v005.md`, the v003 `MANIFEST.json`, `Reports/strawberries_v003_notes.md` and `Scripts/build_strawberries_v003.py`; visually inspected all four captures in `References/Strawberry_2026-10-11/`.

The captures show the specific defects to remove: continuous bright green roof, repeated flat rosettes, clean straight body edges and conspicuous short-end walls/steps. They are failure examples, not colour targets. Root is collecting real planting-time photos before modelling. Require retained photos and source links in `Reports/REFERENCES.md`; record the chosen film type, observed young-plant form, and colour interpretation. Do not copy photographic lighting into BaseColor. Produce a similar-angle reference/model comparison.

## Required asset contract

| Item | Acceptance check |
|---|---|
| Names | `SM_PazFarm_StrawberryBed_4m_A/B/C`, each with separate matching `*_LOD3.fbx`. Optional `SM_PazFarm_StrawberryBedEnd`, about 0.4 m long, joins at its Y=0 end. |
| Coordinates | Metres; +Y tiling; nominal bed surface Y=0 to 4 m; pivot exactly (0,0,0), ground centre of start end; FBX -Y forward / Z up. |
| Bed profile | Top approximately 0.8 m wide; base approximately 1.0–1.1 m; top 0.20–0.30 m above pivot; rounded shoulders and sloping sides; restrained longitudinal irregularity. |
| Hidden skirt | Film and side geometry continue to Z=-0.15 m in both LODs. Measure below-pivot depth separately from above-ground height. **Do not recenter on minimum Z.** |
| Plants | Two staggered rows 0.30–0.35 m apart; within-row pitch approximately 0.25–0.30 m. Plants 0.10–0.20 m across and 0.05–0.12 m above their planting soil. Each normal young plant has 3–6 compound trifoliate leaves, each with three serrated leaflets. No fruit. |
| Variation | Different arrangements/seeds across A/B/C; meaningful size, leaf-angle and colour variation; approximately 5–10% tiny/empty planting holes, with visible soil. Record counts and tiny/empty fraction per variant. A few older yellow/red leaves; rare flowers only if referenced. |
| Budgets | LOD0 approximately 15–40k triangles; LOD3 approximately 100–300. Count the entire exported tile, including skirts and optional details. |
| Near/far roles | **No canopy hull in LOD0.** LOD3 is a low film-coloured mound with faint green detail, not a continuous bright green canopy. Young foliage must not dominate the far stripe. |

The v003 convention being retained is its 4 m length and start-end ground pivot, not its old 0.8 m overall width, Z-minimum of zero, closed green ridge, fruit or nine-slot material contents. Its closed-body validator is not directly suitable for v005.

## Geometry and every variant seam

- The bed and film have **no short-end walls** at Y=0/4. Validate end-plane faces explicitly; do not inadvertently close ends during triangulation, solidification or export. Expected open end loops are intentional. Check their topology/location; require zero unexpected boundary edges elsewhere. Solid leaf components should remain closed and nondegenerate. Do not report a blanket “all meshes watertight” pass for an intentionally open bed.
- Reuse a compatible terminal cross-section and matching terminal tangents/normals across variants; fade interior width/wrinkle irregularity into the common ends. Soil edge strips, film UV phase and wrinkle scale must also continue across the joint. Avoid coplanar duplicate film/soil faces and z-fighting around planting holes.
- Test all **nine directed joins** AA, AB, AC, BA, BB, BC, CA, CB, CC at +4 m: each at LOD0 and LOD3 (18 tests). Compare transformed endpoint profiles, gaps, positive-volume intersection, normals and texture appearance. If neighbouring tiles can occupy different LODs, also check the 18 directed cross-LOD joins. Use a small declared numeric tolerance (recommended 0.1 mm), then inspect grazing side/top views for visible seams.
- Check planting rhythm across every join, not just within a tile. Do not crop leaf geometry to the end plane. Prefer joint-safe edge plants and smaller end plants; any complete-leaf overhang must be reported separately from nominal bed length and checked against the next variant. Reject clipped leaves, colliding duplicate plants or conspicuous empty slots at every 4 m boundary.
- An optional end cap is a separate terminal object: validate each A/B/C-to-cap joint, its tucked film, and the same start-end pivot. Do not add end walls to every repeating tile to disguise the lack of a cap.

## Three-percent slope proof

Build 10 rows × 5 mixed tiles: 50 instances, 1.7 m centre spacing and 20 m along-row surface length. Use a ground plane with slope along the rows, Z=0.03Y; pitch is atan(0.03)=1.718358 degrees about X. Rotate the tiles and **chain each origin from the previous rotated 4 m endpoint**. For tile k, origin is `(Xrow, 4k cos(pitch), 4k sin(pitch))`; this gives about 0.60 m rise over a row. Keeping 4 m horizontal origin spacing after rotation introduces avoidable seams.

Include all directed variant adjacencies in the block or a separate seam strip. Show the ground and side contact; also inspect an isolated cutaway to prove the skirt exists. Compare unsunk placement with a declared few-centimetre sink to confirm the skirt covers exposed sides without burying the mulch top or plants. Do not demand identical Z minima after slope rotation. A planar slope proves correct rigid placement, not conformity to arbitrary curved terrain; changing per-tile slope/roll can still open joints and remains a native placement concern.

## Materials, export and visual evidence

- Reload the actual saved textures before previews. Verify BaseColor sRGB, Normal OpenGL +Y and ORM as non-colour data; R=AO, G=roughness, B=metallic. Opaque shader alpha and every foliage texture alpha must be 1. Use identical material names **and order** within each LOD pair, retaining unused slots; document any separate low-role material. No wind, collision or billboard.
- Mulch roughness must be at least 0.85, including the sampled ORM green channel, with low specular. Inspect grazing light: folds must not become glossy strips. Use subtle surface normals and geometry, soil-covered margins and planting holes; reject a featureless extrusion. Natural dark/mid green with slight blue cast is the target, not the current scene's bright green roof.
- Fresh Blender process: reopen source and independently import each FBX. Compare dimensions, the unchanged origin, -0.15 m skirt depth, transforms, triangle counts, ordered slots, UV0, finite positions/normals/UVs and zero degenerate geometry/UV faces. Keep expected open-end topology exemptions explicit. Bind reports to source/FBX/texture hashes; compare earlier-delivery hashes with the pre-work baseline.
- Required views: single tile at 1/3 m; 10-row slope block at 15/60/150/500 m; similar-angle photo/model comparison. Use one recorded perspective rig, lighting/exposure and resolution for paired LOD comparisons; report camera-target distance and clipping. Add fitted views if a true 1 m frame crops the bed. Inspect each variant near, and the mixed block at both LODs. A 4 km LOD3 stress view is useful for the stated far-use range but cannot prove permanent visibility at finite pixel resolution.
- Report film-stripe coverage and colour separately from foliage detail. At 60 m the lowest LOD must already read as matte film with faint young-plant dots. Reject a renewed bright green band, conspicuous disappearance of whole bed segments, periodic seams or floating sides. Numerical silhouette/colour metrics support visual judgement; avoid arbitrary thresholds that force a young sparse bed back into a solid canopy.

## Main realism risks and completion boundary

Primary risks are oversized compound leaves masquerading as young transplants, unbroken green coverage, uniform rosette orientation, overly regular shoulders, plastic gloss, black film without holes/wrinkles, and visible 4 m repetition. The skirt fixes modest ground contact gaps; it does not fix incorrect tilt or terrain placement. Offline completion requires reference-based visual review, current export/texture/seam evidence and unchanged originals. Native import, material conversion, lowest-LOD/HLOD assignment, terrain placement and scene acceptance remain with the Unreal operator.
