# Paz Farm visual review — 2026-10-08

Compared the reference, all five Unreal views, plot outlines and placement records. **Main gaps: disappearing distant crowns, coarse field bands, pale ground and the white barn roof.** Only this report was written; no fixes or editor actions.

RGBs are **screenshot sRGB appearance targets**, not linear material inputs. Plot values are `LAYOUT.json` averages, including crops/shadows; match exposure first, then colour and coverage. Orchard averages must not become uniform soil albedo. Directions below are geographic degrees counter-clockwise from east, not Unreal yaw. Rank 1 gives the largest expected improvement.

| Rank | Plot / object | Target RGB | Difference → specific fix |
|---:|---|---|---|
| 1 | `orchard_south` | Plot **118,100,97**; lighter soil **147,128,126** | Crowns are full close up but almost absent overhead. Fix distant foliage visibility before adding trees. Keep **247 trees**, **166.3°**, **5.93 m rows / 5.5 m in-row**. Afterwards try **0.8 XY crown scale** to separate merging crowns: ~4–4.5 m footprints are a visual starting estimate; height is unverified. |
| 2 | `field_northeast_big` | **142,126,115** | Broad cloudy bands replace fine crop/furrows. Keep **124.7°**; replace the **12.39 m** macro-pattern with fine low rows, initially **~1–2 m**, then verify a reference transect. Reduce pale mottling. The dominant FFT period is not reliably individual furrow spacing. |
| 3 | `field_southwest` | **178,155,145** | Same coarse-band defect. Keep **145°**; use the recorded **1.91 m** fine-period candidate instead of **11.86 m** bands. Restore warm dusty soil and fine low rows. |
| 4 | `fields_west_green` | **122,118,107** overall | Uniform grey loses the reference’s dark blue-green western rows and browner eastern rows with pale interruptions. Split these appearances; retain **84.2° / ~5.24 m** major-row rhythm. Use continuous low crop cover, not trees. |
| 5 | `strawberry_west` | **171,135,125** | Thin black strips and sparse leaves dominate pale lanes. Keep **85.8° / 5.48 m**, **449 tiles**. Add fuller low foliage, softer mulch contrast and dusty shoulders (~2 m total apparent ridge band initially), without stretching plants or the 0.8 m bed. |
| 6 | `strawberry_triangle` | **170,132,123** | Apply the same coverage/material correction. Keep **176.7° / 5.84 m**, **314 tiles**, and clipped row ends. Its near-perpendicular direction to the west plot is already correct. |
| 7 | Dirt roads | Diagonal **185,158,154**; east **192,168,158**; west **212,192,184** | Yellow/green corridors need continuous pink-tan dirt, irregular shoulders and widened T/Y junctions. Retain traced centrelines: **4 m** diagonal/north-access/west/spur; **5 m** south/east. Preserve the east curve; reconcile existing GeoCity tracks before adding surfaces. |
| 8 | `rows_east_unknown` | **127,115,112**; lighter gaps **145,135,132** | **861 citrus at 0.50–0.62 scale** read as sticks; reference shows continuous grey-green bands. Fix visibility, then use denser narrow row canopies if needed. Keep **88.2° / 4.89 m**, **2.6 m in-row**. Species remains unconfirmed; do not blindly add larger citrus. |
| 9 | Barn | Roof **70,62,68**; apron **202,193,186** | Replace white/glittering roof with matte charcoal and restrained pale seams; reduce corrugation aliasing. Keep **25.8 × 20.5 m**, **−3.35°**. Restore pale south apron. Height, pitch and door details cannot be established from the aerial image. |
| 10 | `orchard_northeast` | Plot **133,114,104**; lighter soil **158,136,127** | Restore discrete crowns at distance before changing density. Keep **84 citrus**, **3.8° / 5.61 m rows / 3.9 m in-row**, and current size initially. Species is provisional. |
| 11 | Fence / gate | Adjacent plot/road RGBs | Clean wire-only borders lack the reference’s dark irregular scrub, especially west/south and east bends. Add broken boundary vegetation with gate clearance. Retain 2 m fence provisionally; construction is unresolved. Correct the gate offset below. |
| 12 | `field_north_green` | **151,149,127** | Add patchy low green cover, pale soil gaps and the isolated upper/right reference trees. Retain **177.7° / 3.35 m** guide rows; no orchard conversion. |
| 13 | `field_southeast_brown` | **154,121,115** | Replace pale pink patterned ground with muted red-brown bare soil and faint **~86.7°** tillage. Suppress broad stripes; **9–11 m** FFT periods are not planted-row evidence. No trees/crops needed. |
| 14 | `triangle_top_bare` | **160,125,113** | Keep bare; reduce pale mottling and regular stripes. No added crops or structures; ignore low-confidence FFT directions. |
| 15 | `yard` | Mean **147,127,123**; exposed patch **172,149,148** | Break up generic soil, distinguish the pale south apron, and connect access to the gate. Keep working space clear; no crop stripes or invented clutter. |

**Broken / verify before applying**

- **Distant canopy loss is visible; its cause is unproven.** Check culling, opacity/mip coverage and distant mesh representation. Do not compensate by multiplying tree counts.
- **Gate placement-data mismatch:** the mesh has a centre pivot, but the generator subtracts 3 m as for an end pivot. Adjacent panels imply a gap N=49.46…55.46 m. Re-centre near **(E=24.27, N=52.46) m from the farm pin**, replacing **(23.94,50.07)**; align both posts and verify import axes. These are geographic coordinates, not Unreal centimetres. Screenshot confirmation of overlap is unavailable.
- **Barn roof moiré is visible.** The close-up also shows a ray-tracing fallback warning; recheck once rendering settles.
- No unequivocal floating asset is established; barn contact appears flush. Check bed ends/post feet individually, without a blanket Z offset. Georeference RMS is **8.96 m**: verify road tie-ins before shifting the entire farm.

Colour provenance: plot averages/light guides come from the screenshot statistics. Additional median patches, top-left pixel origin: roof x440–496/y168–210; yard x510–526/y203–219; diagonal road x673–678/y380–386; east x933–942/y438–443; west x140–149/y452–457; apron x451–490/y224–246. Use these as appearance anchors, not copied texture pixels.

**Proposed work after your go-ahead:** visibility/exposure first; then fine ground rows, strawberry coverage, barn/roads; finally gate/borders. I can prepare offline model, procedural-ground and placement revisions. Claude can apply native material/visibility and map changes in the current assignment, or I can do them under a separately authorized editor/package scope. No fixes have been applied.
