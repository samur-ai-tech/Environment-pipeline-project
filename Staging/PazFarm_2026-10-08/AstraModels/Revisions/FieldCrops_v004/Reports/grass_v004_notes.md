# Field grass v004

Eight original grass variants are delivered as sixteen independent meshes. A–D are mostly dry golden Mediterranean annual grasses; E/F have living olive-green blades and a few broadleaf weeds. Patch A is predominantly straw; patch B mixes straw and green. Solid barley-style awns and oat-style drooping seed heads add close detail.

| Variant | High dimensions W × D × H, metres | High triangles | Lowest triangles |
|---|---:|---:|---:|
| Clump A | 0.36 × 0.32 × 0.28 | 2,072 | 80 |
| Clump B | 0.52 × 0.45 × 0.51 | 2,396 | 80 |
| Clump C | 0.67 × 0.55 × 0.68 | 2,744 | 80 |
| Clump D | 0.85 × 0.73 × 0.78 | 2,908 | 80 |
| Clump E | 0.39 × 0.34 × 0.25 | 2,152 | 80 |
| Clump F | 0.64 × 0.56 × 0.55 | 2,808 | 80 |
| Patch 2m A | 2.00 × 2.00 × 0.60 | 7,420 | 80 |
| Patch 2m B | 2.00 × 2.00 × 0.63 | 7,420 | 80 |

The lowest mesh has twenty closed pointed tetrahedral tufts/spears. The high mesh retains smaller backing tufts and adds closed curved blades, stems, seeds and weeds. The lowest proxies are independently expanded to replace the removed blade coverage, while the high backing stays narrow/low for the close view. The proxies stay within the high bounding envelope and are solid geometry, never billboards. Distance diagnostics found too little low coverage, so final clump proxy bases use width/depth factors 1.6/1.3 for A/E/F and 2.0/1.6 for B/C/D, with all tips unchanged. Final patch proxy bases use width ×3.0, depth ×2.2 and height ×1.9; the tall central tuft keeps its top Z and has a 0.36 ×0.22 m base to fill the central hole. Separate fixed-distance frames measure resulting coverage; fitted heroes show construction but do not substitute for those checks.

Eight shared two-sided opaque materials have the same slot names and order in every pair: Grass_Dry, Grass_Straw, Grass_Green, Grass_Stem, then the four matching _Low roles. Unused slots remain present. The high uses four original 1K BaseColor/Normal/ORM sets; low roles reuse those Normal/ORM images and add four BaseColors, for sixteen textures total. The low colors use 0.70 linear albedo, then correct sRGB encoding, to compensate for lost self-shadowing; no unsupported shader multiplier is needed on import. BaseColor is explicitly encoded sRGB; Normal is OpenGL +Y; ORM is R=AO, G=roughness, B=metallic. All texture alpha bytes are 255 and shader alpha is 1. No wind, collision, cards or external image content is used.

All pivots are at ground centre, minimum Z is 0, units are metres and FBX axes are -Y forward / Z up. FieldGrass.blend contains all sixteen meshes at their individual origins: only A high is initially visible to prevent overlapping variants. Unhide a selected mesh and hide the previously visible one when inspecting. Each mesh has its own FBX; import the explicit _LOD3 counterpart as the lowest LOD and preserve material slot order.

Source QA verifies budgets, finite geometry, no zero-area triangles, closed components, UV0, pivots and ground contact. Reports/grass_v004_qa.json contains measured values. Fresh FBX imports, original-preservation hashes and perspective distance tests are independently supplied by the main delivery. This source report does not claim Unreal or HLOD validation. Hero previews are fitted orthographic views with fixed family lighting, not distance evidence. Procedural dimensions, seeds, blade counts and dry/green proportions are editable in Scripts/build_grass_v004.py.
