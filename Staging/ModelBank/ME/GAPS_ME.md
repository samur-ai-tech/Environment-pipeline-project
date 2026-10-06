# ME1 regional model-bank gaps

**State:** files-only gap audit. `FULL_INDEX.csv` old-project `passed` results mean an import check passed; they do not establish licensing, regional suitability, generator compatibility, rendering quality, or qualification in Environmentpipeline. Licensing/provenance is unknown for every selected and reference asset.

## 1. CityBLD modular building parts

Gap: ME1 stages whole buildings, not a proven regional facade system. There is no measured regional set with compatible ground/middle/top walls, corners, doors/windows, common dimensions, CityBLD `BuildingMesh` origins, and seam-tested materials. The vendor modular contract requires +X width, +Z up, front +Y, lower-left/back-plane origin, strict rectangular perimeter, and edge-to-edge bounds; none of the ME1 whole-building FBXs is established as such a module.

**Not a substitute, for reference only:** the already documented Hergel NYCAlley and Terre Rural five-part kits in archived `Staging/Archive/PreFinalVision_2026-09-29/Research/STAGE2_CANDIDATES.md`. Their source roots are:

- `...\CityBLD_Kits\Hergel_NYCAlley\FBX\` — `SM_Astra_Wall_Ground`, `SM_Astra_Wall_Middle`, `SM_Astra_Corner_Middle`, `SM_Astra_Top`, `SM_Astra_Corner_Top`.
- `...\CityBLD_Kits\Terre_Rural\FBX\` — `SM_Rural_Wall_Ground`, `SM_Rural_Wall_Middle`, `SM_Rural_Corner_Middle`, `SM_Rural_Top`, `SM_Rural_Corner_Top`.

Those kits have old-project evidence only and are not regional replacements or qualified in Environmentpipeline. Additional catalog references T0044 `SM_Wall_L`, T0068 `SM_Top_Wall1m`, T0070 `SM_Wall_1m`, T0072 `SM_Wall_4m`, T0074 `SM_Wall_Door_3m`, and T0083 `SM_Window_Wall_01` are also **not a substitute, for reference only**; their mutual compatibility and CityBLD readiness are unknown.

## 2. Regional vegetation breadth

Gap: the bank is not empty—H0636 Acacia, H0647 Nopal, and H0958 CoconutPalm are staged—but there is no **qualified usable** regional palette. Pivot, ecology, wind/foliage behavior, LOD transitions, collision, density, and rendered quality remain unknown; H0958 also has unresolved texture GUID notes. A diverse shrub/groundcover layer is not established.

**Not a substitute, for reference only:** T0987 `SM_Shrub_01` (`Sources\Terre\FBX\Vegetation\SM_Shrub_01__0987.fbx`), T1144 `hedge` (`...\hedge__1144.fbx`), T1172 `GrassDry_A` (`...\GrassDry_A__1172.fbx`), and the staged Terre Cypress/Pine SpeedTree sources. Their ecology and regional fit are unverified. Terre T0000 Acacia is not used as a fallback because the requested Hergel Acacia exists.

## 3. Regional ground materials

Gap: `FULL_INDEX.csv` catalogs meshes, not standalone Landscape/ground material assets. ME1 therefore has no evidenced regional sand/soil/concrete/asphalt material set, no measured tiling scale, and no Landscape/RoadBLD connection.

**Not a substitute, for reference only:** H0667 `SM_DriedGroundAlpha01`, H0668 `SM_DriedGroundAlpha02`, H0410 `sm_en_GroundConcrete_01_01`, and T0240 `SM_Terrain`. These are mesh references, not Landscape material substitutes. The installed RoadBLD docs also name USA sample asphalt/sidewalk master materials; they are **not a substitute, for reference only** and have no regional qualification.

## 4. Localized signage

Gap: H0082 and H0083 provide sign form factors, but the inspected files/reports do not establish Arabic/local text, local traffic semantics, face direction after placement, or editable sign content. Therefore regional signage remains unknown and unusable as a qualified set.

**Not a substitute, for reference only:** H0137 `SM_ParkingSign` (`Sources\Hergel\FBX\Architecture\SM_ParkingSign__0137.fbx`), H0190 `SM_electricstore_sign_01` (`...\SM_electricstore_sign_01__0190.fbx`), and T0451 `SM_Sign1` (`Sources\Terre\FBX\Other\SM_Sign1__0451.fbx`). They are non-localized reference forms only.

## Cross-cutting gap

Rights for the selected and reference assets are **unknown**. `LICENSE_PROVENANCE.md` provides no bank-wide grant, and blank catalog provenance fields cannot be treated as permission. No asset becomes usable until exact package/rightsholder evidence, project-use rights, and any redistribution/attribution terms are recorded.
