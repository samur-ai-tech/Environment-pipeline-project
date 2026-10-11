# Barn roof v002 — offline delivery

Changed only the roof sheets and roof flashings: charcoal paint, roughness 0.94, metallic 0, reduced specular response, flat normal texture, and corrugation relief reduced from 45 mm to 6 mm. The existing corrugation pitch and ridge/seam geometry remain. PNG BaseColor bytes were measured at **RGB 70,62,68**; the image is loaded as sRGB. All texture files are 1024 × 1024. Textures are original procedural artwork, CC0; no aerial-image pixels were copied.

Use `FBX/SM_PazFarm_Barn.fbx` with `Blend/Barn.blend`. Keep the current map instance position, **25.8 × 20.5 m** placement scale and **−3.35°** geographic orientation. Source wall footprint remains **20 × 12 m**, eave **6 m**, ridge **8 m**. Measured outer bounds, including roof/flashing and the original door reveal, remain **20.57 × 12.585 × 8.11338 m**. The original ground-centred pivot, front axis and all three UCX boxes are preserved exactly.

## Required material-slot mapping on reimport

| Slot | Material | Action |
|---:|---|---|
| 0 | `M_PazFarm_Barn_WallGalvanized` | Retain existing appearance. |
| 1 | `M_PazFarm_Barn_RoofPaintedGrey` | Retain: this original slot still serves light uprights, wall trim and the sliding door. |
| 2 | `M_PazFarm_Barn_DarkHardware` | Retain. |
| 3 | `M_PazFarm_Barn_ConcretePlinth` | Retain. |
| 4 | `M_PazFarm_Barn_RoofCharcoal_v002` | New roof-only slot. Use the three matching v002 roof textures. BaseColor sRGB on; ORM and Normal sRGB off. ORM = AO / Roughness / Metallic. |

Do not recolour slot 1 to charcoal: that would change the doors and wall trim. FBX does not reliably reconstruct the custom packed ORM shader; map slot 4 explicitly. Blender Specular IOR Level is 0.20; native specular response still needs visual checking. The normal map is flat, so its green-axis convention has no visual effect.

Offline verification passed: **17,168 triangles / 30,000 budget**, zero degenerate geometry triangles, zero degenerate UV triangles, closed geometry, UV0, three unchanged UCX boxes, exact non-roof vertex preservation and no missing texture paths after source reopen. Original Blend/FBX hashes and all copied original material texture hashes remained unchanged. Full measurements and SHA-256 hashes are in `barn_v002.json`, `barn_v002_readback.json` and `barn_v002_texture_pixels.json`.

Both previews were visually reviewed with the 1.8 m scale figure. They show reduced roof ridges/glint and unchanged walls/door. Preview lighting is deliberately bright for shape inspection; its displayed roof pixels are not an exposure-matched aerial comparison. **No Unreal import, native material setup, map save or native visual verification was performed.** Recheck the roof against the aerial screenshot after native exposure and lighting settle; the target RGB is an appearance anchor, not a guarantee of framebuffer colour under arbitrary lighting.
