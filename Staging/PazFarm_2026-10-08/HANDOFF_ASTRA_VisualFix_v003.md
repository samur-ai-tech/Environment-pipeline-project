# Astra brief: VisualFix v003 (Aleppo pine and far-robust strawberry bed)

Written 2026-10-10 by the Karmei Yosef operator (Claude Code), for Aviv to pass to Astra. Offline Blender work only; Unreal is
handled by the operator. Deliver to `Staging/PazFarm_2026-10-08/AstraModels/Revisions/VisualFix_v003/` with the same layout as v002:
`FBX/`, `Blend/`, `Textures/`, `Previews/`, `Reports/`, `MANIFEST.json`, `HANDOFF_CLAUDE.md`, `DONE.md`. Original deliveries
stay unchanged.

## Why (Aviv's rules)

- Trees and plants must never disappear, neither leaves nor trunks; they may only degrade to a lower level of detail.
- Distant vegetation uses an always-loaded Instancing HLOD with Nanite disallowed, as Aviv decided on 2026-10-10.
  Every far instance therefore shows the mesh's **lowest LOD**, never Nanite. The lowest LOD must still read as a full
  tree or a full green bed from about 300 m to 4 km, and it must stay light (thousands of trees use it at once).
- Your v002 approach fixed the farm trees: geometric leaves with solid alpha, Nanite Preserve Area. Crowns now show from 460 m.

## 1. Aleppo pine (new): replaces the forest stand-ins

**What we measured** (captures in `Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08/receipts/Captures/`):

- The 4 km forest uses store pines with thin masked needle cards.
- Even after our fixes, crowns thin to pale trunks beyond about 600–700 m. Those fixes were Nanite Preserve Area, leaf textures with alpha-coverage preservation, and an opacity clip lowered to 0.12.
- The needle cards fall below one pixel. With Nanite off the result is the same.
- Evidence:
  - `nv_pre_b_forest_oblique.png`: before, bare trunks.
  - `nv_final_b_forest_oblique.png`: after our fixes.
  - `lod_f_SM_green-tree01_400m.png`: pale sticks remain far right.

**Species and look:**

- *Pinus halepensis*, the KKL forests around Karmei Yosef and Hulda.
- An irregular, umbrella-like, open crown of clumped needle tufts.
- The trunk is often leaning and the bark grey-brown.
- From above and from far away the crowns read **dark grey-olive green**.

**Variants:** 3 (A/B/C), heights about 8, 11 and 15 m, crown widths about 6, 8 and 10 m. One young variant around 4 m is welcome.

**Geometry (LOD0, Nanite):**

- Needle clusters as **real geometry with solid alpha (1)**, no masked cards.
- Also an **opaque inner crown volume**: low-poly clump hulls behind the tufts, so the silhouette and colour hold at 1–4 km.
- Budget about 40–120k triangles per tree.

**Lowest LOD (for the non-Nanite or HLOD path):**

- A separate mesh `SM_..._LOD3`, or LOD3 in the FBX, of about 800–2,000 triangles.
- Built from the crown hulls and trunk, never a billboard card.
- It must look like the same tree at 1 km.

**Materials:**

- Bark, needles (opaque, two-sided), crown hull.
- BaseColor / Normal / ORM as in v002; normals OpenGL +Y as before.
- No wind and no collision except an optional trunk capsule.

**Pivot:** trunk base at the origin. Metres, FBX −Y forward, Z up, as v002.

**Previews:** each variant at 5 m, 50 m, 300 m and 1 km, at fixed exposure, plus one top-down view.

## 2. Strawberry bed v003 (far-robust): replaces `SM_PazFarm_StrawberryBed_4m` v002

**What we measured:**

- v002 looks good up close: dense rosettes, 19,624 triangles.
- At 60–150 m with Nanite on, the beds turn **pale grey-green**. Nanite simplification of the many tiny leaves brightens them.
- With Nanite off they stay darker green, but still greyish.
- Evidence: `sb_b_straw_150m.png` (Nanite on) and `sb_nn_b_straw_150m.png` (Nanite off), plus `sb_b_straw_60m.png`.

**Keep:**

- The 0.8 × 4 m tile, the ground/start-end pivot and the axis convention.
- The 763 placements will be swapped in place.

**Change:**

- Add a **continuous opaque canopy hull**: a low green mound along the bed under the rosettes, so the bed reads as one dark-green ridge at distance.
- Use slightly larger and fewer leaf clumps rather than many tiny leaves.
- Make the black plastic mulch **matte and darker**, with no sheen at grazing angles: roughness about 0.9 and low specular.

**Lowest LOD:** a simple ridge (green mound on a black mulch strip) of about 100–400 triangles that keeps the same colour.

**Previews:** one bed and a 10-bed block at 2 m, 30 m, 150 m and 500 m.

## 3. Checks to include (as in v002)

- Fresh FBX import round-trip, dimensions and pivots.
- Triangle budgets, UV0, finite geometry and solid alpha on all foliage.
- The originals-unchanged hash report.
- A short note on how each lowest LOD was built and verified to read correctly at distance.

---

## Paste-ready message for Astra

> Hi Astra, a new visual task for Paz Farm and the Karmei Yosef forest (offline Blender only, no Unreal). Please read
> `Staging/PazFarm_2026-10-08/HANDOFF_ASTRA_VisualFix_v003.md` and deliver to
> `Staging/PazFarm_2026-10-08/AstraModels/Revisions/VisualFix_v003/` in the same layout as v002. It covers two items.
> (1) A Nanite-friendly Aleppo pine, 3 variants. The needle clusters must be solid geometry with an opaque inner crown
> hull, and the lowest LOD (no billboard) must still read as a full tree at 1 km, because distant trees will use an
> always-loaded Instancing HLOD that shows each tree's lowest LOD. (2) A far-robust strawberry bed v003 with the same
> 0.8 × 4 m tile and pivot. Add a continuous green canopy hull and a matte darker mulch so it stays dark green at
> 60–500 m, plus a ridge-like lowest LOD. Far away, every tree and bed is drawn only with its lowest LOD (no Nanite), so
> those lowest LODs matter most. Our distance captures and measurements are listed in the brief. Thanks!
