# Eight extension families: new repeat seam audit

All eight retained one-axis extension candidates fail new Repeat→Repeat texture appearance qualification. Their original N=1 Start/Repeat/End interfaces match geometry and UVs; new repeat interfaces have noninteger UV phase and sampled diffuse/normal differences. No extension capability was enabled by this read-only audit.

| Family | Axis / pitch m | Max sampled profile gap mm | New UV phase max | BaseColor mean / max RGB delta | Samples above 0.02 | Source blend unchanged |
|---|---|---:|---:|---|---:|---|
| H0911 | Y / 1.377769 | 0.328402 | 0.081068 | 0.052101 / 0.422448 | 72.5% | True |
| H0921 | Y / 1.732191 | 1.450803 | 0.060475 | 0.045681 / 0.219231 | 73.0% | True |
| H0924 | X / 10.602469 | 1.392365 | 0.462580 | 0.060015 / 0.329617 | 84.6% | True |
| H0925 | X / 9.592434 | 1.399517 | 0.350816 | 0.064544 / 0.411818 | 77.4% | True |
| H0926 | X / 2.349596 | 0.000552 | 0.082515 | 0.059476 / 0.160082 | 88.7% | True |
| H0927 | Y / 2.458146 | 1.352895 | 0.096020 | 0.055392 / 0.189709 | 87.7% | True |
| H0930 | X / 5.224355 | 0.566483 | 0.258701 | 0.054844 / 0.210123 | 81.5% | True |
| H0931 | X / 10.912155 | 0.369072 | 0.404549 | 0.054305 / 0.268541 | 84.0% | True |

The eight original N=2 Extended.png previews were inspected. They demonstrate the retained source style and complete extension examples at one angle; they do not override close-boundary measurements or certify native appearance.

Geometry is within the source 1.5 mm profile tolerance, which is not a perfect weld for seven families. Horizontal, vertical and oblique surface profile measurements and corner endpoint measurements are recorded separately. N=3 reuses the same failing seam twice; it does not repair texture phase.

Keep extension disabled until derivative UV/texture seam correction and any necessary boundary welding are validated. Limit a correction to new derivative variations, preserving originals and unaffected faces. A narrow per-chart baked seam patch from source diffuse/normal maps is a candidate; a blanket whole-mesh UV offset or material replacement has not been proved to preserve original atlas features. Revalidate Start→Repeat, each new Repeat→Repeat, Repeat→End, roofs, corners, openings and normals.

All source extension Blender hashes remained unchanged. This audit does not certify procedural architectural floors, arbitrary footprints, cross-family substitution, full-mesh overlap/collision, materials in native Unreal, Houdini Engine regeneration, named saves/reopen, or user acceptance.

Detailed geometric samples are in EXTENSION_BOUNDARY_SAMPLES.json. Source graph evidence comes from the separately produced SOURCE_BINDINGS.json; no material-graph extraction was duplicated here.
