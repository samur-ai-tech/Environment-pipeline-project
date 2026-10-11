# Astra brief: FieldCrops v004 (grapevine rows, olive trees, field grass)

Written 2026-10-11 by the Karmei Yosef operator (Claude Code), for Aviv to pass to Astra.
- **Scope:** offline Blender work only; Unreal is handled by the operator.
- **Deliver to:** `Staging/PazFarm_2026-10-08/AstraModels/Revisions/FieldCrops_v004/`.
- **Layout:** the same as VisualFix_v003: `FBX/`, `Blend/`, `Textures/`, `Previews/`, `Reports/`, `MANIFEST.json`, `HANDOFF_CLAUDE.md`, `DONE.md`.
- **Originals:** all earlier deliveries stay unchanged.

## Why

- The farmland around Paz Farm (about 3.4 × 1.7 km) is now built field by field from Aviv's wide screenshot: 223 fields of 8 types. Each field is filled with models in real rows along the field's own direction.
- Three things are missing and use poor stand-ins today:
  - **Vineyards:** small bushes stand in for vines.
  - **Olive groves:** citrus or broadleaf trees stand in for olives.
  - **Grass:** small generic grass patches stand in for weeds, field margins and fallow fields.
- Your v003 Aleppo pines are now in the forest and the windbreaks, and they work very well. Please use the same approach here.

**Placement facts (how Unreal uses them):**
- Every item is instanced: thousands to tens of thousands of copies, on lattices or scattered.
- Far away, every item is drawn only with its lowest LOD in an always-loaded Instancing HLOD (Nanite disallowed). So the lowest LODs matter most, and they must stay light.
- Aviv's rule: trees and plants must never disappear, only degrade to a lower LOD.
- The scene is late September in the Israeli coastal plain:
  - vines are still green;
  - olives are grey-green;
  - field grass is mostly dry, golden straw with a little green.

## 1. Grapevine row tile: 3 variants

- **Names:** `SM_PazFarm_VineRow_3m_A/B/C`.
- **Form:** a trellised, vertically shoot-positioned (VSP) vine row tile, 3.0 m long along +Y.
  - It holds 2 vines, 1.5 m apart, each with a trunk of about 0.8–1.0 m and a cordon along the wire.
  - The summer canopy is a 0.5–0.7 m thick hedge, from about 0.9 m up to 1.8 m.
  - It has 2–3 thin trellis wires and one end post (galvanised steel or wood) at the start end.
- **Tiling:**
  - Tiles must join end to end with no gap or overlap; the post repeats every 3 m.
  - Rows will be 2.5–3.0 m apart.
  - The pivot is on the ground at the centre of the start end, as with the strawberry bed: +Y is the row direction, Z is up.
- **Geometry:**
  - Leaves as clustered solid geometry with solid alpha.
  - An opaque inner canopy hull, so the hedge reads as one continuous green band at distance.
  - Budget about 15–40k triangles per tile.
- **Lowest LOD:** a simple canopy band on the post line, about 100–300 triangles, the same colour.
- **Previews:**
  - one tile and a 5-row × 10-tile block;
  - at 2, 30, 150 and 500 m.

## 2. Olive tree: 3 mature variants + 1 young

**Names and sizes:**

| Mesh | Height | Crown width |
|---|---|---|
| `SM_PazFarm_Olive_A` | about 4.5 m | 4–6 m |
| `SM_PazFarm_Olive_B` | about 5.5 m | 4–6 m |
| `SM_PazFarm_Olive_C` | about 6.5 m | 4–6 m |
| `SM_PazFarm_Olive_Young` | about 2 m | |

- **Form:** a gnarled, twisted, often split trunk, and a rounded, irregular crown.
  - The small leaves are silvery grey-green on top and paler underneath.
  - It should be clearly different from citrus and avocado at 100 m: greyer, finer and more open.
- **Geometry:** the same recipe as the Aleppo pine:
  - solid leaf-cluster geometry;
  - an opaque inner crown hull;
  - about 40–100k triangles.
- **Lowest LOD:** about 800–1,500 triangles, from the crown hulls and trunk, never a billboard. It must read as the same tree at 1 km.
- **Pivot:** trunk base at the origin. Orchard spacing will be about 6–7 m.
- **Previews:** at 5, 50, 300 and 1,000 m, plus top-down.

## 3. Field grass: clumps for margins, fallow fields and roadsides

- **Clumps:** `SM_PazFarm_GrassClump_A`–`F`, 6 variants.
  - Mediterranean annual grasses (wild oat or wild barley look) and a few broadleaf weeds.
  - Mostly dry golden straw; 2 of the variants are greener.
  - Sizes 0.3–0.9 m across and 0.2–0.8 m tall.
- **Patches:** `SM_PazFarm_GrassPatch_2m_A/B`, 2 denser patches about 2 × 2 m, for continuous margin cover.
- **Budget:** these are placed by the tens of thousands.
  - About 300–3,000 triangles per clump and about 3–8k per patch.
  - Opaque blade geometry is preferred; any alpha must be solid (1).
- **Lowest LOD:** a low tuft or mound of about 20–80 triangles, the same colour.
- **Pivot:** at the ground, at the centre.
- **Previews:** single clumps, and a 10 × 10 m scatter, at 2, 15, 50 and 150 m.

## Common rules (as v002/v003)

- **Format:** metres, FBX with -Y forward and Z up. Each lowest LOD is a separate `*_LOD3.fbx`, with the same material slot names as its base mesh.
- **Materials:**
  - opaque, with foliage two-sided;
  - BaseColor (sRGB), Normal (OpenGL +Y) and ORM (R = AO, G = roughness, B = metallic);
  - no wind and no collision.
- **Checks to include:**
  - fresh FBX import round-trips, dimensions and pivots;
  - triangle budgets, UV0 and finite geometry;
  - solid alpha on all foliage;
  - tile seams on the vine row;
  - the originals-unchanged hash report;
  - a short note on how each lowest LOD was built and checked at distance.

---

## Paste-ready message for Astra

> Hi Astra, a new task for the Karmei Yosef farmland (offline Blender only, no Unreal). Please read
> `Staging/PazFarm_2026-10-08/HANDOFF_ASTRA_FieldCrops_v004.md` and deliver to
> `Staging/PazFarm_2026-10-08/AstraModels/Revisions/FieldCrops_v004/` in the same layout as VisualFix_v003. Your Aleppo pines
> work beautifully in the forest, so please use the same recipe (solid leaf clusters, opaque inner hull, authored lowest LOD,
> no billboards) for three things: (1) a trellised grapevine row tile, 3 m long, 3 variants, that tiles end to end with a post
> every 3 m; (2) olive trees, 3 mature variants (about 4.5, 5.5 and 6.5 m) plus 1 young, silvery grey-green and clearly
> different from citrus at 100 m; (3) Mediterranean field grass, 6 clumps and 2 patches, mostly dry golden with some green,
> very light because they will be placed by the tens of thousands. Far away everything is drawn only with its lowest LOD, so
> those matter most. Sizes, budgets, pivots and previews are in the brief. Thanks!
