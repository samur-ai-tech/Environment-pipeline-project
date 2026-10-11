# Paz Farm (Hevat Paz) — higher-fidelity plan (draft for Aviv)

Date: 2026-10-08. Author: Claude Code session 4a6a1d0c (Karmei Yosef operator). Status: DRAFT, nothing built yet.
Labels: [M] measured, [A] from Aviv, [I] inference to confirm.

## 1. Where it is
- [A] Farm pin: 31.851309 N, 34.906260 E.
- [M] That is about 127 m west and 106 m north of the Karmei Yosef area centre, i.e. Unreal X ≈ -12,700 cm, Y ≈ -10,640 cm
  (X = east, Y = south) in both maps:
  - 2 km: `/Game/Project/Areas/KarmeiYosef_31850349_34907601_2km/BankIntegration_v015/L_KarmeiYosef_31850349_34907601_2km`
  - 4 km: `/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/BankIntegration_v015/L_KarmeiYosef_31850349_34907601_4km`
    (+ PCG zone clone `..._4km_PCGTrial/L_KarmeiYosef_31850349_34907601_4km_PCGTrial`)
- [M] OpenStreetMap has no farm buildings or plots here; the Nahal Ekron stream is mapped further west.
- Proposed focus box: about 700 m × 500 m around the pin (the extent of Aviv's screenshot), to confirm.

## 2. What is there
- [A] Crops (from the farm's public listing): avocado, lemons, clementines, oranges, strawberries, seasonal vegetables.
- [A] The triangle plot with the pin: one barn at the top of the triangle; greenhouses / net houses fill the rest.
- [A] Fences: wire / mesh fence around the farm, a gate at the entrance.
- [A] Scope: farm buildings and yard, orchards and crops by type, dirt roads and fences around the farm. Not all small details.
- [I] From the screenshot: dense dark-green tree rows = citrus and avocado; striped rows inside the triangle = strawberry
  beds under nets/tunnels (farm offers picking); ploughed and row-crop fields around; dirt farm roads between plots;
  Nahal Ekron with bushes on the north-west side.
- Open: the grey-purple rows east of the farm road (Aviv unsure). Options: young orchard, vineyard, lavender/herbs.

## 3. What we already have (keep)
- Real terrain (Copernicus 1 m grid), real satellite colours on the ground (4 km area), zone map, GeoCity roads
  (farm tracks drawn as roads by Aviv's choice), PCG zone vegetation on the 4 km clone with stand-ins.

## 4. What is missing (to model in Blender — see HANDOFF_ASTRA_BLENDER.md)
1. Avocado tree (2-3 variants).
2. Citrus tree: lemon, orange/clementine (2-3 variants each, with fruit colour variants).
3. Strawberry bed row segment (raised bed with mulch film), optional low tunnel hoop segment.
4. Net house modular kit (bay, end wall, door) and plastic greenhouse tunnel kit.
5. Farm barn (one, matching the real barn).
6. Wire / mesh fence kit (segment, post, corner, end) and entrance gate.
Not modelled: dirt roads (done in Unreal), irrigation, signs and other small details (Aviv: not all small details).

## 5. How it will be placed in Unreal (after the models arrive)
1. Georeference Aviv's screenshot(s) to the map (match 4+ road junctions / plot corners) — needs the image files saved in
   `Staging/PazFarm_2026-10-08/References/`.
2. Trace each plot as a polygon with: crop type, row direction, row spacing, in-row spacing; trace the fence line,
   gate position, barn footprint and the net-house / greenhouse area.
3. PCG per plot (same method as the zone trial: mask per plot -> rows on a grid rotated to the real row direction ->
   real model), fence and net-house kits placed along their traced lines, barn placed at its footprint.
4. Dirt roads: landscape paint along the traced farm roads (the GeoCity track roads stay unless Aviv wants them removed
   inside the farm).
5. Work on a clone of the 4 km map first (as with the PCG trials), then decide what moves into the main map.

## 6. Open questions for Aviv
1. Grey-purple rows: what are they?
2. Strawberries: open beds, low tunnels, or under the net houses?
3. Barn: size, wall/roof material and colour (a ground photo would help).
4. Net houses: white or black/green net? Flat or gabled roof? Height?
5. Any ground-level photos of the farm (yard, barn, fence, gate) — save to `References/`.
6. Which trees are where (avocado vs lemon vs oranges/clementines) — mark on a screenshot if possible.
