# Paz Farm — first placement in Unreal (2026-10-08)

Map (clone, not the main 4 km map): `/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/L_KarmeiYosef_31850349_34907601_4km_PCGTrial`
saved sha256 `2719be1c...` (186 MB), fresh reopen verified (PID 33508). Main 4 km map unchanged (c7c858c5).

## What was done
- Screenshot georeferenced to the map's OSM roads (0.353 m/px, rotation -3.35 deg, RMS ~9 m): `Georef/FIT.json`, check image `Georef/screenshot_with_osm_roads.png`.
- 12 plots traced, colours and row direction/spacing measured: `Georef/LAYOUT.json`, `Georef/plots_check.png`.
- Farm ground layer drawn by us (no screenshot pixels), 0.25 m/px: `T_PazFarm_Ground` in the 4 km area's own material
  `M_GeoCityAuto_KY4` behind `Farm_Blend` (default 0 = off). The clone uses its own `MI_GeoCityGround_PazFarm` (Farm_Blend 1).
- Astra models imported to `<clone>/PazFarm/` (117 textures, 3 masters, 38 MIs, 26 Nanite meshes).
- Placed on actor `PazFarm_Detail` (folder PazFarm): 763 strawberry-bed tiles, 247 avocado, 84 lemon/orange (NE orchard),
  861 young citrus (grey-purple rows, guess), 225 fence panels + 9 posts; `PazFarm_Barn` (scaled to the 25.8 x 20.5 m
  footprint), `PazFarm_Gate`. Zone PCG stand-ins removed from the farm footprint (masks re-imported, 112,891 plants left).

## Undo (reversible as Aviv asked)
- Ground: set `Farm_Blend` to 0 in `MI_GeoCityGround_PazFarm`, or set the clone landscape back to the area MI.
- Models: delete the three `PazFarm_*` actors.
- Stand-in plants: re-import the original masks (`SourceData/.../zones/20261008T131311Z/T_KY4_Mask_*.png`) and regenerate.

## Known gaps
- Strawberry plants: Astra's first version (fix requested). Barn roof colour (dark in the screenshot, light grey here).
- Young citrus in the grey-purple rows (unknown crop) look thin from afar. Ground colours slightly pinker/paler than the screenshot.
- Dirt farm roads are only painted in the farm layer (the GeoCity track roads remain).
- Note: Aviv's own editor (PID 19732) crashed at 16:00:06Z during my first material step (new Material via
  MaterialFactoryNew); nothing of his was lost; masters are now built by copying a StarterContent material.
