# Farmland from Aviv's wide screenshot: result (2026-10-10/11)

Built on the 4 km PCG clone `/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/L_KarmeiYosef_31850349_34907601_4km_PCGTrial`.

- **Map:** sha `65adf6ddaaf08cedc0646bdc0075922b0e3c313c1a9c007cb1966b2f2adbdf56`, verified after a fresh reopen (PID 37244: 0 dirty packages).
- **Later saves, same session:** a mask re-import and MI parameter changes. Content packages only; the map hash is unchanged.
- **Labels:** [M] measured; [A] Aviv's decision.

## Decisions [A]

| Topic | Aviv's words or choice |
|---|---|
| Farm direction | "Scrap our approach regarding to the farm parcels, and enrich it with more vegetation and fitting textures." The forest "looks gorgeous". |
| Roads | "Extract from my screenshot" |
| Farmland | "Every field from the screenshot" |
| Field preview | "Yes, build it" |

## Data (offline, this folder) [M]

**Screenshots** (`References/Wide_2026-10-10/`):
- The labelled and plain screenshots align with an offset of dx 4, dy -1 px (`ALIGN.json`).
- The Google road lines are extracted to `road_mask.png`, and road 44 to `highway_mask.png`.

**Georeference** (`WIDE_FIT.json`):
- Found by distance-transform matching against every OSM highway: 2.03 m per pixel, rotation 0.03°, offset (-20.5, 53.5) m from the pin.
- 93% of road pixels lie within 10 m of OSM.
- The screenshot covers 3.43 × 1.69 km.

**Fields:**
- 12 colour and texture clusters (`fields_cluster.py`).
- `fields_v1.py`: a 26 m majority filter, roads as barriers, then a sieve of 3,300 m², giving 223 fields of 8 types.
- Each field has a row direction from the structure tensor. Where the result is weak (coherence below 0.15), the field's long axis is used instead.

**Build data** (`fields_build_v1.py`):
- `FIELD_PLANTS_V1.json`;
- ground mask v4: 4,096 px over 3,456 m, BC7. Each field has its own soil, tilled and grass mix, and the Paz Farm interior keeps its v3 weights;
- `ROAD44.json`: 18 OSM trunk and primary ways;
- `fields_clear_zone.png`.

**Fill by type:**
- orchard: Astra avocado or citrus, one species per field, 6 × 4.5 m;
- rows: young citrus;
- green crop: stand-ins, 3 m × 1.6 m;
- ploughed and bare: weed tufts;
- grey-white light fields and structures (saturation 13 or lower): Astra greenhouse tunnels 9 × 4 m;
- natural: unchanged.
- Margin shrubs run along every filled field.
- Dirt roads are drawn only on farmland, not in the village, forest or water.

## In the map [M]

| Actor (folder Fields, Static) | Instances |
|---|---|
| `KY4_Fields_Orchards` | 19,865 (avocado 6,199, citrus 13,666) |
| `KY4_Fields_Crops` | 135,449 low crop stand-ins |
| `KY4_Fields_Weeds` | 22,568 (weed tufts 14,302, margin shrubs 8,266) |
| `KY4_Fields_Greenhouses` | 2,462 greenhouse tunnels |
| `KY4_Windbreaks` | 1,140 (Aleppo pines + STF green trees, spaced from the field trees) |
| `KY4_Road44` | mesh `<clone>/Roads/SM_KY4_Road44`: 9 strips, 1,154 quads, edges draped on the landscape + 12 cm, `MI_AsphaltMat_Inst8` |

- 75 points landed on other actors and were skipped.
- **Removed:** `PazFarm_Extension`, the crops of the scrapped road-to-road parcels.
- **Zone vegetation:** PCG v003 was regenerated with every filled field cleared, giving 112,405 plants. The Aleppo pines are kept.
- **Ground:** the MI `MI_GeoCityGround_PazFarmReal_v2` now uses `T_PazFarm_GroundMask_v4`, with `FarmR_OriginX` -179792.07, `FarmR_OriginY` -168844.88, `FarmR_SizeCm` 345600, `FarmR_SatMix` 0.3 and `FarmR_MacroAmt` 0.3.

**Play-mode frame time (ms)** [M]:

| View | Before this work | After |
|---|---|---|
| Farm | 25.5 | 22.3 |
| Village | 13.4 | 15.1 |
| Wide | 30.6 | 33.1 |

The forest sample caught only 3 frames, so it isn't reliable.

**Captures:** `NewArea_..._4km_2026-10-08/receipts/Captures/fld_b_*`, `fldt1_b_*`, `fldf2_b_*`.

## Known weak spots

- **Orchard detection:** 57 ha were found as orchards. Many dotted young-orchard or vineyard fields in the screenshot were classified bare or ploughed, so the area reads barer than the photo.
- **Mixed types:** some real fields came out split into two types where their colour shifts.
- **Stand-ins:** the low crop plants are grass stand-ins, and there is no vine or olive model.
- **Road 44:** reads light grey and plain, with no markings and no shoulders.

## Undo

- Delete the `KY4_Fields_*` and `KY4_Road44` actors.
- Point the MI's `FarmR_Mask` back to `T_PazFarm_GroundMask_v2` (old origin and size in `FARM_GROUND_V3.json`).
- Re-import the earlier masks and regenerate.
- Map backups: `NewArea_..._4km_2026-10-08/Before/L_..._PCGTrial_42b39ead.umap` (before the fields) and earlier.
