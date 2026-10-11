# Paz Farm structure-kit assembly

Original models and procedural PNG textures, CC0-1.0. The supplied aerial screenshot establishes site context only. These are the explicitly authorized, changeable handoff defaults; dimensions and the appearance of the actual Paz Farm structures have not been measured from ground photographs.

## Coordinates and materials

All placement formulas below use **Blender metres**. Z is up; the building entrance faces -Y. The FBX exporter uses forward -Y / up Z, unit scale 1, Apply Scalings = FBX Units Scale. The receiving operator must inspect axis conversion and native materials during import; this delivery performs no Unreal import or verification.

Each material includes BaseColor, OpenGL +Y Normal and ORM (R=AO, G=roughness, B=metallic) PNGs. Net BaseColor alpha carries the holes and must be used as masked opacity in a two-sided material. Greenhouse film uses two-sided translucent opacity with BaseColor alpha 0.20, roughness 0.28 and IOR 1.46. FBX alone does not reproduce the full native PBR node graph; use the listed PNGs. Normal green may need inversion for Unreal's DirectX convention.

## Net house: exact 8 x 4 m lattice

For an `Nx` by `Ny` rectangle, put Bay meshes at `(i*8,j*4,0)`, with `i=0..Nx-1`, `j=0..Ny-1`. The Bay's physical bounds are exactly 8 x 4 x 4 m. Each bay owns **one lower-left post**, its leading rail and its left rail. This half-open two-dimensional ownership avoids the doubled corner posts that two full leading-edge posts would produce when bays tile along X. Roof net and rails finish at the stated cell boundary.

Add the missing outside supports with `NetHouse_Post_4m`:

- Right edge: `(Nx*8-0.08,j*4,0)`, for `j=0..Ny-1`.
- Rear edge: `(i*8,Ny*4-0.08,0)`, for `i=0..Nx-1`.
- Far corner: `(Nx*8-0.08,Ny*4-0.08,0)` once.

The 0.08 m inset keeps the outermost square posts inside the exterior footprint. Total post count is exactly `(Nx+1)*(Ny+1)`; no post placement is repeated. Posts reach the underside of the 4 m roof rail at 3.96 m.

Add outer roof rails:

- Rear edge: `ClosureBeam_8m` at `(i*8,Ny*4-0.04,0)`.
- Right edge: `ClosureBeam_4m`, rotated +90 degrees around Z, at `(Nx*8,j*4,0)`.

The horizontal member joints meet at the perimeter. Perpendicular manufactured members have the small intended corner joint; there are no two complete rails lying on top of each other. Net-house side curtains carry hems, not a second set of structural posts or beams.

Side and Door pieces lie in XZ, with the ground pivot at their left edge. Place them on a 4 m pitch along the perimeter; rotate 90 degrees about Z to run them along Y. An 8 m bay edge uses two side pieces. The 4 m door panel has a 1.6 x 2.5 m opening and a net leaf folded 85 degrees into positive Y. Jamb/lintel collision leaves the walking opening clear. White and Black variants share geometry and placement rules.

Supplementary assembly previews show a 2 x 2 layout, 16 x 8 m footprint, with exactly nine posts and a 1.8 m scale person. The FBX assets are reusable components, not a monolithic assembly.

## Greenhouse: exact 4 m longitudinal pitch

Place Tunnel meshes at `(0,j*4,0)`, `j=0..N-1`. Film outer span is exactly 9 m; height is 4.5 m. The ground pivot is the centre of the leading short edge. Each section owns one leading arch inset 0.035 m from its leading boundary. Longitudinal purlins and film end at Y=0 and Y=4; adjacent sections do not duplicate arches.

Use End walls at `(0,0,0)` and `(0,N*4,0)`. Rotate the last one 180 degrees around Z if the rolled-up door should face outwards. End walls include the film and a centred 1.8 x 2.2 m doorway, jambs, lintel and visibly rolled-up film door. They deliberately exclude the perimeter arch.

Add **one** `Greenhouse_EndArch` at `(0,N*4-0.07,0)`. Its steel finishes inside the far end at `Y=N*4`. The resulting greenhouse has `N+1` arches. The front arch comes from the first Tunnel, so no extra closure arch belongs at the front.

UCX boxes follow the steel arch and doorway frames only. Neither the film skin nor the doorway creates a solid obstacle. The assembled preview shows three sections, a 9 x 12 m footprint, four arches, two end walls, and a 1.8 m scale person.

## Changing defaults

Source: `Scripts/build_structures.py`. Parameters near the top include net dimensions/height, post/rail width, door sizes, greenhouse span/height/module length and arc resolution. Rerun the script with Blender, or supply `-- --parameters <JSON>` to override named parameters. Keep any parameter file inside AstraModels. Material colours are named explicitly in the family builders. The two family `.blend` files hold exported components at their correct local origins; other components are hidden initially to prevent overlapping meshes obscuring the first asset. Reveal the desired object in the Outliner.

Changing dimensions requires using the new module pitch and recalculating placement offsets from the new post/rail dimensions. Filenames preserve the requested default names; the manifest records actual measured dimensions. The current assembly formulas refer to the delivered defaults.
