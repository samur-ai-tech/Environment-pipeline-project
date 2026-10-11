# StrawberryBeds v005 modelling notes

Offline Blender delivery. The three 4 m modules represent young strawberry transplants on exposed matte dark film. Approved photographs guided form and palette; all meshes and texture pixels are original. No Unreal, Content, maps, bank, Houdini or git operations were performed by the modeller.

| Asset suffix | Detailed triangles | Lowest triangles |
|---|---:|---:|
| Bed_4m_A | 35,370 | 240 |
| Bed_4m_B | 32,920 | 240 |
| Bed_4m_C | 35,100 | 240 |
| BedEnd | 1,962 | 257 |

The source is `Blend/StrawberryBeds.blend`. Detailed object/FBX names are `SM_PazFarm_StrawberryBed_4m_A`, `B`, `C` and `SM_PazFarm_StrawberryBedEnd`; the separate lowest objects/FBXs append `_LOD3`. These standalone files must be explicitly assigned as each matching mesh's lowest LOD during later import. The filename alone does not create an LOD chain. No billboard, wind, collision or runtime switch configuration is included.

FBX preserves the original source polygons and corner normals (`use_triangles=False`). Export-time triangulation in this Blender version altered fine-stem and soil shading, so it is deliberately disabled. Triangle counts above are evaluated mesh triangle counts, not FBX polygon counts. Preserve the imported source normals during later import. The independent fresh-import audit and focused source/FBX render comparison verify this delivery; native Unreal import remains untested.

## Placement and joints

- Metres, unit scale 1.0, +Y row direction; pivot `(0,0,0)` at the ground and beginning of every module. FBX uses -Y forward and Z up with unit conversion enabled. Verify the imported 4 m dimension before placement; do not add an assumed 100x scale.
- Regular bounds are X=-0.55 to +0.55 m, Y=0 to 4 m. The film top is about 0.8 m wide, bed height 0.25 m and buried skirt minimum Z=-0.15 m. Plants add roughly 0.055–0.115 m above the bed, apart from the deliberately tiny plant.
- Place regular tiles at exact 4 m pitch. Shared piecewise end profiles and flat 0.125 m collars allow all nine A/B/C combinations within each LOD. End surfaces are intentionally open. Keep the ends open during import and mesh repair. Complete plants stay inside their tile; the open film and soil boundaries coincide at a join without an added cross wall.
- The optional 0.4 m cap joins at its Y=0 pivot and tapers toward +Y. Place it after the final tile. For the row's starting end, rotate the cap 180 degrees around Z at the first tile's pivot. The joining profile is open; the far film and soil are tucked/closed at or below ground. Do not insert caps between tiles.
- Follow the ground with the row placement transform. The skirt is intended to hide modest terrain variation; the parent's separate slope render is the evidence for its demonstrated case.

## Plant and film construction

Each tile has 28 real irregular apertures, in two staggered rows about 0.33 m apart. Nominal pitch along each row is 4/14 m with small interior jitter and continuous nominal cadence across joints. One aperture is empty and one contains a tiny plant: 2/28 = 7.14%. Their indices differ by variant: A empty 4/tiny 19, B empty 8/tiny 23, C empty 11/tiny 17. The two small boundary plants are complete normal plants, not the counted tiny/empty exceptions.

Every planted hole has 3–6 compound leaves and three serrated, curved leaflets per compound leaf. Actual maximum XY caliper diameters for normal plants are 0.104–0.1896 m. Leaves, petioles, hole soil and soil clods are closed geometry. A small number of older leaves have subdued warm edges. There are no fruit, flowers or foliage hulls.

Detailed film is a genuinely perforated surface, with recessed soil and small clods beneath/around the openings. Soil covers the side foot above the film; isotropic grain replaces directional streaks. The minimum sampled clearance on regular beds is about 0.99 mm for the lowest A bed and 4.45 mm for detailed beds. The cap uses matched stations and explicit matching triangle diagonals; its soil and film meet at the ground-level far tip. The surface QA uses 45 barycentric samples per relevant actual soil triangle, not only vertex clearances.

Lowest beds are simple open film mounds with the same ground/skirt profile. Faint dark-green marks occupy a small part of the dark film; there is no broad green band and no plant cards. Lowest caps use plain film without plant marks.

## Materials

All eight slots are retained in exactly this order on both LODs, including unused slots. All names have prefix `M_PazFarm_Strawberry_` and suffix `_v005`.

| Slot | Role | Use |
|---:|---|---|
| 0 | Mulch | Detailed film and both cap levels |
| 1 | Soil | Hole soil, soil body, buried edges, clods |
| 2 | LeafTop | Normal upper leaf surfaces |
| 3 | LeafUnder | Lower leaf surfaces |
| 4 | LeafOlder | Occasional older upper leaf surfaces |
| 5 | Petiole | Leaf stems |
| 6 | DripTape | Small visible cap drip detail |
| 7 | MulchDistant | Lowest regular-bed film with faint green marks |

Each role has original 1024x1024 BaseColor, Normal and ORM PNGs: 24 textures total. BaseColor is sRGB; normal and ORM are linear data. Normal maps use OpenGL +Y: adapt the green channel if a later importer expects the opposite tangent-space convention. ORM is R=AO, G=roughness, B=metallic. In Blender AO is recorded in the ORM file but not multiplied into BaseColor. Alpha is 1.0 throughout. Use opaque materials; leaf surfaces are two-sided. Film roughness is about 0.95, metallic 0, and specular is deliberately low. Keep the supplied subdued palette and restrained normal strength (film 0.30, leaf 0.45 in Blender).

## Evidence and limits

`strawberries_v005.json` lists the eight assets, component roles/ranges, individual plant and hole metadata, measured bounds, texture dependencies and LOD pairing. `strawberries_v005_source_qa.json` checks current-build topology/budgets and captures saved input hashes. `strawberries_v005_surface_qa.json` reopens the source, measures actual film/soil clearance and UV areas, and verifies equal pre/post source, FBX and texture hashes. The independent validator and parent's distance/slope results are separate evidence.

Fitted heroes and the plant-hole close view are offline Blender appearance previews. They do not prove native Unreal materials, actual runtime LOD selection, Nanite, HLOD, import scale or user acceptance. Required actual-distance comparisons belong to the parent delivery's fixed-camera suite.
