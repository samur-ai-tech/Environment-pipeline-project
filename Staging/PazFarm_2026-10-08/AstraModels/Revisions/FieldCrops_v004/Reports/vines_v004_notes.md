# Grapevine row modules v004

Offline VSP grapevine modules for late-September green vineyards. Three variants and their separately exported lowest LODs share the +Y, 3 m tiling contract. No Unreal, placement or earlier delivery file was changed.

| Variant | Detailed triangles | Lowest triangles | Detailed width | Overall height |
|---|---:|---:|---:|---:|
| A | 36,802 | 294 | 0.6584 m | 1.9 m |
| B | 37,762 | 294 | 0.6590 m | 1.9 m |
| C | 38,722 | 294 | 0.6602 m | 1.9 m |

Each module contains one 0.07 m wooden post at Y=0…0.07 m and two grounded vine trunks at Y=0.75/2.25 m. The post is 1.9 m high. The approximately 0.9 m trunks support low cordons and sixteen shoots. Three thin wires run continuously along Y at Z=0.90/1.28/1.62 m, with two small post supports for the outer catch wires. Four restrained grape bunches and 420/432/444 closed, lobed leaf prisms provide the detailed surface. The side and top leaves conceal a closed inner hull, 0.48 m thick and approximately 0.92…1.70 m high. Leaf and shoot tips break the top outline around 1.8 m.

Each 294-triangle lowest mesh retains one closed canopy band, the post and two supports, two trunks, two cordons and three wires. It omits individual leaves, grape bunches and shoots. The low canopy expands to about 0.53 m thickness and 1.78 m height to stand in for the outer detailed leaves. Its full module width is 0.585 m, including the small wire supports. It is real closed geometry, never a card or billboard. Detailed and low hulls deliberately differ in cross-section; compatible end profiles are proved across all three variants separately at each LOD.

The seven material slots retain identical names and order in every export: **0 bark, 1 post, 2 wire, 3 leaf, 4 lighter leaf, 5 canopy, 6 grape**. The lowest meshes use slots 0, 1, 2 and 5 and retain the unused slots. Explicitly assign each matching `_LOD3.fbx` to the receiving mesh's actual lowest conventional LOD or far-instance binding; exporting a separate file does not install it automatically.

All materials are opaque and two-sided with alpha 1. There is no wind or collision. The 21 original texture PNGs are 1024 × 1024: sRGB BaseColor, OpenGL +Y Normal, and non-color ORM (R=AO, G=roughness, B=metallic). Leaf RGB is nominally 49/79/28 sRGB; the canopy is 47/76/27. Leaves and canopy use roughness 0.93/0.94 with low specular. Texture files are explicitly reloaded after byte-accurate PNG creation; the Blender sources use relative texture paths.

Fresh source and FBX checks pass for all six meshes: dimensions/pivots, triangle budgets, finite geometry and UV0, zero geometric degenerates, closed topology, material order, solid alpha and texture paths. Component analysis finds exactly one post, two grounded trunk components and one connected canopy in each mesh. All nine ordered A/B/C joins at each LOD have equal end profiles and zero longitudinal gap. Geometry is bounded by Y=0…3, so translated neighbours cannot overlap in positive volume. Closed caps coincide only on the internal join plane; the flat cap is exposed only at an actual row termination. Use an exact 3 m pitch and do not duplicate terminal posts.

The 5-row × 10-tile mixed assembly at 2.75 m row pitch contains **50 posts and 100 trunks**, derived from source component counts, at unique positions. Every row extends 30 m; post spacing is 3 m and vine spacing is 1.5 m. See `vines_v004_qa.json` for the 50 placements and all 18 seam cases.

Fitted detailed/low heroes and `Previews/VineRows_Structure_A.png` were visually inspected. The structural view intentionally omits the scale figure to expose both trunks and the low cordon. Root supplies the fixed-camera single and mixed-block distance captures and measurements. These offline checks do not certify Unreal import, native material reconstruction or HLOD selection.

`Blend/VineRows.blend` contains all six objects at the same origin; isolate one for inspection. Editable parameters and deterministic seeds are in `Scripts/build_vines_v004.py` and the scene's `PazFarm_parameters` property. Original artwork and scripts are confined to this revision.
