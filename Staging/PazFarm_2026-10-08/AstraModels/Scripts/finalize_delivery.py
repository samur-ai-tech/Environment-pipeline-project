"""Package the verified retained asset delivery. No writes outside AstraModels."""
from pathlib import Path
import json,hashlib,html,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
qa=json.loads((ROOT/'Reports/VALIDATION.json').read_text())
assert qa['passed'],qa['failures']
assets=[]
for filename in ['trees.json','strawberries.json','structures.json','barn_fence.json']:
 assets.extend(json.loads((ROOT/'Reports'/filename).read_text())['assets'])
assert len(assets)==26,len(assets)
source={'origin':'Original self-authored geometry and procedural texture pixels made for this delivery.','licence':'CC0-1.0','reference_use':'Provided aerial image inspected for site context only; no image pixels used in any texture.'}
for a in assets:
 a['notes']=[n.replace('Variant B is clementine: smaller 64 mm fruit diameter versus 84 mm orange A.','Variant B is clementine, with smaller fruit than orange variant A.') for n in a['notes']]
 a['model_source_licence']=source
 a['textures']=sorted(set(t.replace('\\','/') for m in a['materials'] for t in m['textures']))
 a['fbx_sha256']=hashlib.sha256((ROOT/a['fbx']).read_bytes()).hexdigest()
 a['blend_sha256']=hashlib.sha256((ROOT/a['blend']).read_bytes()).hexdigest()
 a['size_axes']='W=X, D=Y, H=Z in the Blender source; dimensions include geometry overhangs. Module pitch is documented separately.'
 a['native_unreal_verified']=False
 a['offline_fbx_roundtrip_verified']=True

manifest={
 'schema':'pazfarm.asset-delivery.v1','date':'2026-10-08','project':'Paz Farm detail work / Environmentpipeline',
 'status':'Blender modelling and offline delivery complete; native import and placement belong to Karmei Yosef operator.',
 'asset_count':len(assets),'source_family_count':len(set(a['blend'] for a in assets)),
 'units':{'blender':'metres','unit_scale':1.0,'fbx_apply_scalings':'FBX Units Scale / FBX_SCALE_UNITS','global_scale':1.0,'apply_unit_scale':True,'axis_forward':'-Y','axis_up':'Z','source_front':'-Y','intended_unreal_front':'+X after importer axis conversion','scale_contract':'1 metre in source = 100 centimetres in Unreal; offline Blender FBX reimport verified, Unreal not opened'},
 'materials':{'naming':'M_PazFarm_<Material>','base_color':'sRGB; alpha is foliage/net opacity mask or film opacity','normal':'OpenGL +Y, Non-Color. In Unreal use Flip Green Channel for DirectX tangent convention.','ORM':'Non-Color; R = Ambient Occlusion, G = Roughness, B = Metallic','foliage':'Masked, two-sided; wind disabled','net':'Masked, two-sided; BaseColor alpha carries net apertures','film':'Translucent, two-sided; BaseColor alpha carries opacity','receiving_operator':'FBX cannot reconstruct all shader wiring automatically. Rebuild the material connections from the supplied PNGs and mode entries.'},
 'defaults':{'barn':'20 x 12 m footprint, 6 m eave, 8 m ridge, light grey corrugated metal; no ground photograph available. Roof overhang included in measured bounds.','net':'White default plus black alternative, flat roof, 4 m height.','strawberries':'Open raised bed supplied independently of optional removable low tunnel, compatible with placement beneath a net house.','unknown_grey_purple_rows':'Unidentified in handoff. No crop species or additional asset invented.','tree_locations':'Not assigned from aerial screenshot; placement belongs to operator.'},
 'adaptation_notes':['NetHouse Bay/Side/Door use the exact unsuffixed handoff names for white defaults; black alternatives use _Black.','Two-dimensional net-house post ownership uses one leading-corner post per bay and separate boundary pieces to avoid doubled shared corner posts.','NetHouse_Post_4m, ClosureBeam_4m, ClosureBeam_8m and Greenhouse_EndArch are four added closure components.','LowTunnel optional terminal hoop is an editable source parameter; repeat modules use start-owned hoops.'],
 'assembly_instructions':'Reports/structures_assembly.md','verification':'Reports/VALIDATION.json','assets':assets
}
(ROOT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
textures=sorted({t for a in assets for t in a['textures']})
tex_inventory=[]
for t in textures:
 fp=ROOT/t;tex_inventory.append({'file':t,'sha256':hashlib.sha256(fp.read_bytes()).hexdigest(),'source_licence':source})
(ROOT/'Reports/TEXTURE_INVENTORY.json').write_text(json.dumps(tex_inventory,indent=2),encoding='utf-8')

rows=[]
for a in assets:
 dim=' x '.join(f'{x:.3f}'.rstrip('0').rstrip('.') for x in a['size_metres_W_D_H'])
 rows.append(f"| `{a['name']}` | {dim} | {a['triangles_LOD0']:,} |")
done='''# Paz Farm Blender delivery — DONE

Date: 2026-10-08. Status: modelling and offline verification complete.

Delivered **26 FBX meshes, 9 editable Blender family files, TEXTURECOUNT original PNG textures, and one PNG preview per asset with a 1.8 m human scale figure**. Additional structure assembly views and a strawberry detail view are included. Open [INDEX.html](INDEX.html) to browse the previews, or use [MANIFEST.json](MANIFEST.json) for sizes, pivots, materials, texture provenance, budgets and hashes.

All task files were written inside this AstraModels folder. Unreal, Content, maps, the bank, Houdini and git were not opened or changed.

## Delivered assets

Dimensions below are measured Blender X / Y / Z extents in metres, including overhangs. They are not always the modular placement pitch. The barn footprint is 20 x 12 m; the roof overhang makes its full geometry wider. Strawberry bed height includes plants above the 0.25 m raised bed. Fence panel pitch is exactly 3 m despite its start post extending around the pivot.

| Asset | Width x depth x height (m) | LOD0 triangles |
|---|---:|---:|
ASSETROWS

## Defaults and documented adaptations

- Avocado A/B/C, lemon A/B, orange A and smaller-fruited clementine B are delivered. The trees have branch/trunk geometry, individually curved masked leaves and scattered fruit. Plants have no collision and no wind.
- The barn uses the authorized light-grey corrugated-metal default. Its appearance is not a verified reconstruction of the real barn; no ground photograph was supplied.
- Net-house Bay, Side and Door use the exact handoff names for the white defaults, plus `_Black` alternatives. Roofs are flat and 4 m high.
- For correct 2D tiling, each net bay owns one leading-corner post and its leading/left rails. Separate Post, ClosureBeam_4m and ClosureBeam_8m parts close the outer edges. Greenhouse_EndArch closes the last greenhouse section. These four additions are needed to form complete assemblies without duplicated shared supports. The exact placement formulas are in [structures_assembly.md](Reports/structures_assembly.md).
- Strawberries are supplied as open 4 m raised beds with separate optional low-tunnel film and hoops. The bed can also be placed beneath the net houses. The low tunnel's optional terminal hoop is exposed in its source parameters.
- The unknown grey-purple rows were not assigned a species; the handoff provides no crop default or listed mesh for them. Tree species locations and the farm layout remain the receiving operator's placement work.

## Verification performed

[VALIDATION.json](Reports/VALIDATION.json) records a fresh Blender process reopening all 9 sources and separately reimporting all 26 FBXs. All checks passed: source unit scale 1.0, real-size export roundtrip, ground/module pivots, one render mesh per FBX, expected UCX objects, UV0, finite vertices/normals, zero zero-area triangles, per-asset triangle budgets, texture references and preview presence. Measured triangle range for trees is TREERANGE, below the 60,000 limit; barn is 17,168/30,000; all kit pieces are below 5,000; strawberry bed is 17,748/20,000.

All source textures resolve locally and are 1024 x 1024 pixels. All asset previews were visually inspected across the modelling jobs. Strawberry/low-tunnel end-boundary matching and post/arch ownership are recorded in the family reports. This is offline model/export verification; native Unreal import, materials, collision behaviour, placement, saving and regeneration were not performed.

## Import information for the receiving operator

Sources use metres with unit scale 1.0. FBX uses Apply Scalings: FBX Units Scale, global scale 1.0, forward -Y / up Z. Source front is -Y, with the handoff's intended +X Unreal front after axis conversion. A source metre represents 100 Unreal centimetres. Verify importer axis handling against a known module before placement.

Connect BaseColor as sRGB; Normal and ORM as linear/Non-Color. ORM channels are R=AO, G=roughness, B=metallic. Normals are OpenGL +Y; enable green-channel inversion for the DirectX convention. Use BaseColor alpha for masked two-sided leaves/net and translucent two-sided film. FBX material import does not reproduce the complete shader node graph automatically. The supplied PNG maps and manifest define the materials. Named UCX boxes are provided for barn, fence/gate and structure supports; no plants collision.

## Changing the defaults

The nine `.blend` files are split by family: Avocado, Lemon, Orange, Strawberry, LowTunnel, NetHouse, Greenhouse, Barn and Fence. Variants share their intended local origins; hidden alternative objects can be revealed in the Outliner. Edit or rescale the appropriate source, or change dimensions, counts, colours and deterministic seeds in the parameter sections of `Scripts/build_trees.py`, `build_strawberries.py`, `build_structures.py` and `build_barn_fence.py`. Parameters are also recorded in source scene/object properties and family reports. Rebuilding a family replaces its outputs within AstraModels. `Scripts/paz_common.py` supplies the shared PBR/export/preview helpers.

The provided aerial image was used only for context. Every model and texture is original procedural artwork, recorded as CC0-1.0; no satellite imagery or third-party pixels were used in textures. No external reference was needed to build these authorized defaults.

## Remaining work outside this assignment

The Karmei Yosef operator still imports, wires native materials, places and verifies these assets. Real-farm visual matching awaits any later barn/net/field identification from Aviv. No requested modelling item is left undelivered.
'''
tree_tris=[a['triangles_LOD0'] for a in assets if any(s in a['name'] for s in ('Avocado','Lemon','Orange'))]
done=done.replace('TEXTURECOUNT',str(len(textures))).replace('ASSETROWS','\n'.join(rows)).replace('TREERANGE',f'{min(tree_tris):,}–{max(tree_tris):,}')
(ROOT/'DONE.md').write_text(done,encoding='utf-8')

cards=[]
for a in assets:
 name=a['name'].removeprefix('SM_PazFarm_').replace('_',' ')
 dim=' × '.join(f'{v:.2f}' for v in a['size_metres_W_D_H'])+' m'
 cards.append(f'<article><a href="{a["preview"]}"><img loading="lazy" src="{a["preview"]}" alt="{html.escape(name)} with 1.8 m human scale figure"></a><div><h2>{html.escape(name)}</h2><p>{dim} · {a["triangles_LOD0"]:,} triangles</p><a href="{a["fbx"]}">FBX</a> <a href="{a["blend"]}">Blender source</a></div></article>')
extra=[]
known={a['preview'] for a in assets}
for f in sorted((ROOT/'Previews').glob('*.png')):
 rel=f.relative_to(ROOT).as_posix()
 if rel not in known:extra.append(f'<article><a href="{rel}"><img loading="lazy" src="{rel}" alt="{html.escape(f.stem)}"></a><div><h2>{html.escape(f.stem.replace("_"," "))}</h2></div></article>')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Paz Farm · Model delivery</title><style>*{box-sizing:border-box}body{margin:0;font:15px system-ui,sans-serif;background:#edf0ea;color:#25372b}header{padding:44px max(24px,5vw);background:#24372e;color:#f5f5ec}header p{max-width:900px;line-height:1.6;color:#d4dece}h1{font:500 42px Georgia,serif;margin:0}header a{color:#dcdfa8}main{padding:32px max(24px,5vw)}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:22px}article{border:1px solid #d4dacd;border-radius:10px;overflow:hidden;background:white}img{display:block;width:100%;aspect-ratio:1.2;object-fit:contain;background:#bcc4c2}article div{padding:18px}h2{font-size:18px;margin:0 0 10px}article p{color:#626f64}article a{color:#38674b;margin-right:16px}aside{line-height:1.65;background:#dce4d5;padding:20px;border-radius:8px;margin-bottom:28px}footer{padding:28px 0;color:#626f64}</style><header><h1>Paz Farm · Model delivery</h1><p>26 reusable meshes · 9 editable Blender families · original PBR textures<br>Measured in metres, shown with a 1.8 m human scale figure. Authorized defaults, 8 October 2026.</p><a href="DONE.md">Delivery notes</a> · <a href="MANIFEST.json">Manifest</a> · <a href="Reports/VALIDATION.json">Verification</a></header><main><aside>All 26 FBX exports passed offline scale, geometry, UV, pivot and collision-name checks. The barn and structures follow the handoff defaults. Native import, materials and placement remain with the Karmei Yosef operator. Click an image for the full preview.</aside><section>CARDS</section><h2 style="margin-top:40px">Assembly and detail views</h2><section>EXTRA</section><footer>Original modelling and textures. No satellite pixels used. All work retained inside AstraModels.</footer></main></html>'''
(ROOT/'INDEX.html').write_text(page.replace('CARDS',''.join(cards)).replace('EXTRA',''.join(extra)),encoding='utf-8')
print('PACKAGED',len(assets),'assets',len(textures),'textures',len(extra),'extra previews')
