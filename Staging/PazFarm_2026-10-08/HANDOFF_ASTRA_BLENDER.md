# Handoff to Astra: model the missing Paz Farm assets in Blender

Date: 2026-10-08. From: Claude Code session 4a6a1d0c (Karmei Yosef operator), at Aviv's request.
Read first: `Staging/PazFarm_2026-10-08/PLAN.md` (location, what is there, open questions).
Reference images: `Staging/PazFarm_2026-10-08/References/` (Aviv adds screenshots and photos there).

## Your job
Model the assets below in Blender (installed: Blender 5.2) and deliver FBX + textures + a manifest. You do not touch Unreal,
the project `Content/` folder, maps, the asset bank, Houdini, or git. The Karmei Yosef operator imports and places your
assets afterwards.

Write only inside `Staging/PazFarm_2026-10-08/AstraModels/`:
- `Blend/` — one .blend per asset family (source files).
- `FBX/` — one FBX per asset (`SM_PazFarm_<Asset>_<Variant>.fbx`).
- `Textures/` — PNG textures (`T_PazFarm_<Asset>_<Map>.png`).
- `Previews/` — one preview PNG per asset, with a 1.8 m human silhouette for scale.
- `MANIFEST.json` — per asset: name, real size in metres (W × D × H), triangle count, materials, texture files and their
  source/licence, pivot, notes.

## Conventions (all assets)
- Real-world scale, metres in Blender (unit scale 1.0). FBX export with "Apply Scalings: FBX Units Scale" so 1 m = 100 cm
  in Unreal. Z up; front of the asset faces +X in Unreal (export forward -Y / up Z from Blender is fine; state what you used).
- Pivot at the ground contact point, centred (trees: trunk base; kit pieces: the documented corner/edge, see each piece).
- Modular kit pieces must tile exactly (ends flush, no gaps at the stated module length).
- PBR materials named `M_PazFarm_<Material>`: Base Colour, Normal, ORM (AO/Roughness/Metallic packed). 2K max; 1K for small
  props. Foliage: masked, two-sided leaves. No wind animation needed (it is switched off in Unreal).
- Budgets (LOD0): trees ≤ 60k triangles; barn ≤ 30k; kit pieces ≤ 5k; strawberry bed ≤ 20k per 4 m. Clean normals, no
  zero-area faces, UV0 for textures.
- Collision: simple boxes (`UCX_` prefix) for barn, fence, gate and structure posts. None for plants.
- Licensing: model it yourself, or use CC0 sources (e.g. Poly Haven, ambientCG) and record each source in the manifest.
  Do not build textures from Google or other satellite imagery.

## Assets to deliver

### 1. Avocado tree — `SM_PazFarm_Avocado_A/B/C`
5–7 m tall, round dense crown 5–6 m wide, short trunk ~25 cm thick, dark glossy green leaves, a few fruits optional.
Orchard spacing in reality ~5–6 m between rows, ~4 m in-row (for your previews only).

### 2. Lemon tree — `SM_PazFarm_Lemon_A/B`
3–4 m tall, dense round crown ~3–3.5 m wide, dark green, scattered yellow lemons.

### 3. Orange / clementine tree — `SM_PazFarm_Orange_A/B`
3–4 m tall, crown 3–4 m, dark green, scattered orange fruit (clementine = slightly smaller fruit; one variant is enough).

### 4. Strawberry bed — `SM_PazFarm_StrawberryBed_4m` (+ optional `SM_PazFarm_LowTunnel_4m`)
Raised bed 4.0 m long (tiles along its length), 0.8 m wide, 0.25 m high, covered with black plastic mulch film, two lines
of strawberry plants (leaves ~20 cm high, some red berries). Pivot: centre of one short end at ground level.
Optional low tunnel: plastic hoops 1.0 m high, 1.2 m wide, 4.0 m long, semi-transparent film.

### 5. Net house kit (the triangle plot) — net colour default white, add a black variant
- `SM_PazFarm_NetHouse_Bay_8x4`: one roof bay 8.0 m wide × 4.0 m deep, steel posts 4.0 m high at the corners (posts only on
  one edge so bays tile without doubled posts), flat roof shade net, tiles in both directions. Pivot: one corner at ground.
- `SM_PazFarm_NetHouse_Side_4`: side wall net 4.0 m long × 4.0 m high.
- `SM_PazFarm_NetHouse_Door`: a doorway piece in the side wall, 4.0 m long.

### 6. Plastic greenhouse tunnel kit
- `SM_PazFarm_Greenhouse_Tunnel_9x4`: arched tunnel section 9.0 m span, 4.5 m high, 4.0 m long (tiles along length),
  semi-transparent plastic film over steel arches.
- `SM_PazFarm_Greenhouse_End`: end wall with a door.

### 7. Barn — `SM_PazFarm_Barn`
One farm barn at the top of the triangle plot. Default until Aviv supplies a photo: about 20 × 12 m footprint, 6 m eave,
8 m ridge, corrugated metal walls and roof (light grey), one large sliding door on a long side. Keep it easy to rescale.

### 8. Fence and gate kit
- `SM_PazFarm_Fence_Mesh_3m`: 2.0 m high wire/chain-link mesh panel, 3.0 m long, with a post at one end only (tiles).
- `SM_PazFarm_Fence_Post` (end/corner post), `SM_PazFarm_Fence_Corner`.
- `SM_PazFarm_Gate_Double_6m`: double swing gate 6.0 m wide, 2.0 m high, steel frame with mesh, two posts.

## Not in scope
Dirt roads (done in Unreal), irrigation pipes, signs, small yard clutter (Aviv: not all small details).

## Open questions (build the defaults now; keep them easy to change)
Grey-purple rows east of the farm road (unknown); strawberries open vs tunnel vs under nets; barn look; net colour/roof
shape/height. Aviv will answer in the Karmei Yosef chat; the operator will pass changes on.

## When you finish
Write `AstraModels/DONE.md` with the asset list, any deviations, and anything you could not do. Tell Aviv.
