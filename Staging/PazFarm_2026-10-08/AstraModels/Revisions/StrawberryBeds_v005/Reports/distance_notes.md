# Lowest LOD and distance checks

The detailed mesh has no green canopy hull. The lowest mesh is a coarse dark mulch mound carrying faint green plant marks, retaining all material slots. It was rendered directly, not obtained by automatic reduction during these previews.

33 current source-render frames; 11 matched geometry-only LOD pairs. See `distance_validation.json` for cameras, pre-render source/texture hashes and saved-PNG coverage/colour. Soil-ground frames show the 10×5 mixed field at 1.7 m centres on a 3% slope.

| Distance | Detailed px | Lowest px | Area ratio | Luma difference |
|---|---:|---:|---:|---:|
| 60 m | 27089.31 | 27075.98 | 1.000 | -0.85 |
| 150 m | 4333.40 | 4332.16 | 1.000 | -0.81 |
| 500 m | 388.37 | 388.12 | 0.999 | -0.48 |
| 4,000 m | 6.45 | 6.45 | 1.000 | +1.05 |

The 4 km frame is a pixel-limit stress check. Individual 1.1 m beds cannot be expected to remain separable at all resolutions and camera FOVs. Native HLOD assignment, antialiasing and lighting are not tested by Blender evidence. The operator must explicitly install the supplied final LOD and inspect its native distance captures.
