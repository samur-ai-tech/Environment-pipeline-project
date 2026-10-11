# Ground visual revision — ready for offline review

`Georef/T_PazFarm_Ground.png` is an original procedural replacement candidate. **No native asset, source-data texture, placement or map was changed.** The reference-aligned comparison is `Previews/GROUND_COMPARE.html`.

## Apply through the existing farm material

1. Import/reimport this PNG into the already scoped Paz Farm ground texture; retain the original texture for rollback. Keep **sRGB enabled**, ordinary colour compression with alpha retained, and **Clamp** addressing.
2. Preserve the existing mapping exactly: **2048 × 2048 RGBA, 512 × 512 m, 0.25 m/px**, west **−219.843 m**, north **230.463 m** from the farm pin. Pixel origin is northwest. `u=(E+219.843)/512`, `v=(230.463−N)/512`. North-up texture rotation is **0°**; do not rotate it by the screenshot's −3.35° again.
3. Keep the existing `Farm_Blend` route and existing terrain. Alpha is coverage, with zero outside the overlay and soft plot/road edges. Do not bake alpha against the grey preview background.
4. Evaluate with the revised tree/bed models present and exposure held constant. The orchard ground is deliberately exposed soil: real crowns and shadows must lower the whole-plot average. Ground preview panels do not contain trees, barn, strawberry foliage or fences.
5. Reconcile overlapping GeoCity road surfaces during native review; this overlay alone does not remove or rebuild those roads. Preserve the existing georeference; its original 8.96 m RMS uncertainty is unchanged.

## Changes

| Area | Revised behaviour |
|---|---|
| Northeast large field | 124.7° fine **1.8 m** furrows, mean RGB ≈ **142,126,115**, reduced mottling. The pitch is editable because the original FFT macro-period did not identify individual furrows reliably. |
| Southwest field | 145° fine **1.91 m** furrows, mean ≈ **178,155,145**. |
| Western green field | 84.2° / 5.24 m major rhythm retained; blue-green west, brown-green east, sparse pale interruptions. Mean ≈ **120,121,109** against screenshot overall **122,118,107**. |
| Strawberry west / triangle | **2 m** dusty soil shoulder bands follow the actual unchanged **449 / 314** tile pivots and 4 m extents; clipped row ends. Directions/pitches remain 85.8° / 5.48 m and 176.7° / 5.84 m. Ground-only means ≈ **173,136,126 / 172,134,124**. Revised foliage adds the darker crop coverage. |
| South / northeast orchards | Exposed soil RGB **147,128,126 / 158,136,127**; no painted canopy bars. |
| Unknown eastern rows | Exposed soil RGB **145,135,132**; canopy form remains a separate model/native visibility question. Species is still unresolved. |
| North green field | Patchy green low cover, pale gaps, restrained 177.7° / 3.35 m guide rows. Mean ≈ **150,150,127**. Isolated reference trees are a placement task, not painted ground. |
| Southeast bare field / upper triangle | Muted RGB **154,121,115 / 160,125,113**, no broad crop stripes; southeast has only faint fine tillage. |
| Yard / apron | Exposed yard RGB **172,149,148** with smooth variation; pale south barn apron **202,193,186**. The darker whole-yard reference mean includes structures/shadows. |
| Roads | Pink-tan surfaces: diagonal/north access **185,158,154**, east/south/spur **192,168,158**, west **212,192,184**. Original 4/5 m widths and traced vertices retained. Smooth irregular shoulders and three local junction connectors close existing endpoint gaps. |

Every colour above is an **sRGB byte value**, written directly to a PNG with an sRGB tag. Do not feed these numbers as linear material values or apply an extra gamma conversion.

## Edit and regenerate

Edit `Georef/GROUND_SETTINGS.json`. Run `Georef/ground_v002.py` with the existing Blender 5.2 bundled Python (numpy is already included). No Blender GUI, Unreal, package installation, screenshot pixel sampling or original-script execution is required. The script reads the original layout/placements and writes only this revision folder.

`Reports/GROUND_QA.json` records per-plot means/percentiles, source hashes, the exact mapping, strawberry alignment and derived junction coordinates. PNG byte round-trip, transparent exterior, feather coverage, exact metadata match and 763-tile phase assertions pass. No native render, import, save/reopen or appearance acceptance is claimed.
