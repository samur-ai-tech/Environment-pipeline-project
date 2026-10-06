# GazaRimal — First model-bank qualification queue, 2026-09-29

This is a **queue of candidates to check**, not a list approved for generation. The [data file](BANK_FIRST_QUALIFICATION_QUEUE_2026-09-29.csv) gives the exact ID and path for each of the 28 rows. All are `reserve`; **zero** are `qualified`, `connected`, `generated`, or `accepted`. The four P0 rows are the previously named Tier 1 candidates, but Tier 1 has not run. [measured: `BANK_FIRST_QUALIFICATION_QA_2026-09-29.json`; not run: Tier 1]

**Rights key:** `O` — Aviv confirmed technical qualification may continue for this exact `Bank_ME_v3` asset, while source documents and the terms for the chosen use remain open; `F` — a local acquisition record exists, but entitlement and terms are unverified; `P` — the package is identified, but entitlement and terms are missing; `U` — `StarterContent` provenance and applicable terms need mapping. Rights and technical quality are independent. [documented: `RIGHTS_DECISION_PACKET_2026-09-29.md`]

| Priority | Exact asset | Specific role and useful variation | Rights | Next check |
| --- | --- | --- | --- | --- |
| P0 | `SM_H0013_Building_04` | Tall residential building with height and silhouette distinct from H0015 | O | Materials and facade, orientation, collision, building margin, and plinth on sloped terrain |
| P0 | `SM_H0907_Arab_x3_fbx` | Whole domed landmark | O | Aviv's site/style decision; facade, roof, margin, and plinth |
| P0 | `SM_H0051_Garbagebin` | Bin with built-in rubbish; do not count that rubbish as a separate asset | O | Materials, collision, and pedestrian clearance |
| P0 | `SM_H0958_CoconutPalm` | Palm form distinct from the `Palms_Pack_01` palms | O | Foliage material fidelity, bounds, alpha/wind, and local ecology; experimental material derivative is not adopted |
| P1 | `SM_H0015_Building_02` | Lower building with a commercial-facing facade | O | Facade and materials, performance budget, margin, and plinth |
| P1 | `SM_H0904_Slum_v_fbx` | Low, worn building, distinct from the taller facades | O | Material/UV damage, facade, access, and terrain fit |
| P1 | `ModularCourtyard/SM_wall_windows_4x4_01` | Closed-window wall module | F | Grid, thickness, connectors, material, and seam; `BG1` not run |
| P1 | `ModularCourtyard/SM_wall_windows_4x4_open` | Open-window state; a through-opening is not yet proved | F | Opening geometry, grid, connectors, and seam; `BG1` not run |
| P1 | `ModularCourtyard/SM_wall_corner` | Corner needed to test assembly within the same kit | F | Corner profile, pivot, connectors, and material; `BG1` not run |
| P1 | `ModularCourtyard/SM_Enter_T1_DoorT1` | Entrance function that window bays cannot supply | F | Door opening, threshold, grid, and facade direction; `BG1` not run |
| P1 | `ModularBuildingSet/Store_fronts/store_front_shutters_4x1_a` | Closed shutter storefront | F | Front/back, grid, material, and sidewalk threshold; separate kit from `ModularCourtyard` |
| P1 | `ModularBuildingSet/Store_fronts/store_front_windows_intact_4x1_a` | Intact glazed exterior storefront | F | Glass, backing, grid, and seam; distinct from the interior asset with the same name |
| P1 | `SM_H0043_Foodcart_001` | Food cart for a market zone | O | Materials, scale, wheel contact, and pedestrian clearance |
| P1 | `SM_H0025_Barrier` | Temporary street barrier, distinct from a permanent fence | O | Length, collision, road-edge placement, and passage |
| P1 | `SM_H0077_Stones_Stack` | Masonry supply stack for construction context | O | Materials, scale, collision, and construction zones |
| P1 | `SM_H0081_Streetpowerbox` | Electrical utility cabinet | O | Service-facing side, collision, and setback from doors/sidewalk |
| P1 | `SM_H0039_Destryoedcar` | Damaged vehicle; adds a different street condition | O | Material/UV, scale, collision, and deliberate lane placement |
| P1 | `SM_H0090_Watertank` | Pallet-mounted IBC-style container; not a generic roof tank | O | Materials, support, collision, and exact placement role |
| P1 | `SM_H0091_Watertank_001` | Drinking-water dispenser, distinct from H0090 | O | Scale, materials, access, and pedestrian clearance |
| P1 | `SM_H0082_Streetsign` | Street/wayfinding sign | O | Legibility, language/content, facing direction, and pole location |
| P1 | `ModularBuildingSet/Rubble_Piles/rubble_trash_pile_a` | Loose rubble/trash pile, distinct from H0051's built-in litter | F | Class, materials, scale, density, and pedestrian clearance |
| P1 | `Palms_Pack_01/SM_Palm_01_03_G` | Tall, narrow-trunk palm | P | Entitlement, bounds, foliage/LOD, and canopy clearance |
| P1 | `Palms_Pack_01/SM_Palm_01_08_G` | Leaning palm needing asymmetric clearance | P | Entitlement, lean direction, foliage/LOD, and utility clearance |
| P1 | `Palms_Pack_01/SM_Palm_01_12_G` | Low/young growth form, not merely a scaled mature palm | P | Entitlement, material/LOD, and fit in narrow locations |
| P1 | `Palms_Pack_01/SM_Grass_02_3` | Low grass layer, distinct from tree forms | P | Entitlement, alpha/LOD, density, and permitted ground zones |
| P1 | `FC_Coastal_Landscape/M_Master_CL_Landscape` | Candidate sand/soil terrain material | F | Graph, textures, layers, tiling, and road/building transitions |
| P1 | `StarterContent/M_Concrete_Poured` | Concrete sidewalk finish candidate; not asphalt | U | Provenance and terms, UV/normal/roughness, dependencies, and sidewalk/road join |
| P1 | `StarterContent/M_Ground_Gravel` | Gravel/ground-shoulder candidate | U | Provenance and terms, tiling, dependencies, and terrain blend |

**Why generation is still blocked:** [measured] Thirteen rows have measured bounds and ordered material paths; 24 have a partial native preview. [inference] Neither proves placement or generation qualification. [not run: CAT1, INST1, BG1, Tier 1] The project still needs a decision on the `CONTRACT.md` §4.5 schema, numeric `FootprintClass` margins, role/zone/style, rights documents, and the per-row native checks. Only then can a qualified subset be frozen. The [gap packet](BANK_FIRST_QUALIFICATION_GAP_PACKET_2026-09-29.EN.md) details the remaining interface and evidence.
