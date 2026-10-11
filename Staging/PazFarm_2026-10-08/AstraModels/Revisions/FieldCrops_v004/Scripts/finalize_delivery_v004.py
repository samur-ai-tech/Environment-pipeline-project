"""Assemble a verified offline packet. Refuses stale geometry or render evidence."""
import hashlib,html,json,re
from pathlib import Path
from urllib.parse import unquote,urlparse
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,data):(ROOT/p).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
assets=[]
for name in ('vines_v004.json','olives_v004.json','grass_v004.json'):assets+=read('Reports/'+name)['assets']
qa=read('Reports/VALIDATION.json');assert qa['passed'] and len(assets)==30
for r in qa['assets']:
    a=next(a for a in assets if a['name']==r['name']);assert r['sha256']==sha(ROOT/a['fbx'])
for s in qa['sources']:
    assert s['sha256']==sha(ROOT/s['file'])
    for t in s['images']:assert t['sha256']==sha(ROOT/t['delivery_path'])
dist=read('Reports/distance_validation.json');assert dist['status']=='COMPLETE_OFFLINE_EVIDENCE' and dist['actual_frames']==154
assert dist['all_frame_source_bindings_current']
for f in dist['frames']:
    assert f['source_blend_sha256']==sha(f['source_blend']) and f['png_sha256']==sha(ROOT/f['file'])
    assert f['texture_hash_capture']=='before render'
    for p,h in f['source_texture_sha256'].items():assert sha(p)==h
review=read('Reports/VISUAL_REVIEW.json');assert review['delivery_ready']
seams=read('Reports/vines_v004_qa.json');assert seams['pass'] and seams['input_hashes_unchanged']
for p,r in seams['input_hashes'].items():
    assert sha(ROOT/p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes'],'Stale vine seam evidence: '+p
baseline=read('Reports/ORIGINAL_INPUTS_SHA256.json')
changed=[r['path'] for r in baseline if not Path(r['path']).is_file() or sha(r['path'])!=r['sha256']]
preservation={'passed':not changed,'files_checked':len(baseline),'changed_or_missing':changed,'method':'SHA256 compared against all earlier farm staging files baselined before this revision.'}
write('Reports/ORIGINALS_UNCHANGED.json',preservation);assert not changed,changed
textures=sorted({t.replace('\\','/') for a in assets for m in a['materials'] for t in m['textures']})
pairs=[]
for a in assets:
    if a['name'].endswith('_LOD3'):continue
    b=next(x for x in assets if x['name']==a['name']+'_LOD3')
    pairs.append({'base_asset':a['name'],'lod0_fbx':a['fbx'],'lowest_mesh':b['name'],'lowest_fbx':b['fbx'],
                  'lod0_triangles':a['triangles_LOD0'],'lowest_triangles':b['triangles_LOD0'],'source':a['blend'],
                  'material_slots':[m['name'] for m in a['materials']],
                  'lowest_role':'Separate authored final conventional LOD. Must explicitly assign to the receiving base mesh/far-instance path.'})
table='\n'.join(f"| `{p['base_asset']}` | {p['lod0_triangles']:,} | {p['lowest_triangles']:,} |" for p in pairs)
grass_far=review['grass_scatter_150m']
patch_far=review['grass_patches_150m']
handoff=f'''# Karmei Yosef farmland — FieldCrops v004

**Offline Blender delivery complete. Native application and acceptance are pending.**

Follows `HANDOFF_ASTRA_FieldCrops_v004.md`. All new files are inside `AstraModels/Revisions/FieldCrops_v004/`. Start with `INDEX.html`, then `Previews/Distance/INDEX.html`. The supplied wide farm reference was sufficient. Earlier deliveries are preserved.

## Models

| Base model | Detailed triangles | Authored lowest triangles |
|---|---:|---:|
{table}

There are 15 base models, 30 separate FBXs, three editable Blender scenes and {len(textures)} PBR maps. Exact dimensions, pivots, material slots, paths and hashes are in `MANIFEST.json`.

## Lowest LOD assignment

**Each base FBX contains only its detailed mesh.** Explicitly assign the matching `_LOD3.fbx` as the final custom LOD, or bind that mesh to the operator's existing far-instance route. The filename does not automatically install an LOD chain. Preserve its material slot order, including unused slots. Do not replace it with automatic reduction or a billboard.

The brief specifies an always-loaded Instancing HLOD using each item's lowest LOD with Nanite disallowed. These files supply solid conventional geometry for that existing route. No HLOD configuration or native imports were performed. Verify which geometry is actually drawn at distance under the operator's current ownership.

## Vine rows

Three 3 m modules extend from Y=0 to Y=3, with Z up and the pivot at ground centre of the start end. Place successive modules at +3 m along their local Y axis. Use 2.5–3 m row pitch; the preview uses 2.75 m. Each tile contains two vines 1.5 m apart and one post at its start. Mixed A/B/C sequences use the same end profile within each LOD. The detailed inner band is 0.48 m wide with a 1.70 m top; the low band expands to 0.53 m / 1.78 m to replace the outer leaves. The shared join plane may contain coincident end-cap faces; there is no positive-volume tile overlap.

LOD0 combines solid vine leaves, shoots, cordons, trunks, wires and an inner green hedge. The authored low mesh retains the hedge and support line as closed geometry. `Reports/vines_v004_qa.json` contains seam, pitch and block checks. The final exposed row end can be finished by the receiving operator if a terminal trellis support is required; repeating tiles themselves have one start post each.

## Olives

Mature A/B/C target 4.5 / 5.5 / 6.5 m heights and 4–6 m crowns; Young targets 2 m. Twisted branching trunks, narrow silvery leaves and irregular open crown groups distinguish these from the earlier broadleaf/citrus trees. Keep the olive palette grey-green, with lighter leaf undersides. Each lowest LOD retains the actual trunk and opaque crown groups, with branch gaps and variant-specific shape. Use 6–7 m orchard spacing.

The extra 100 m frames include the previous Lemon and Avocado sources under identical lighting, camera FOV and distance at their actual sizes. Those sources were read only. See `Reports/VISUAL_REVIEW.json` for the assessed comparison and any limits.

## Field grass

Clumps A–D are predominantly dry straw; E/F are greener. The two 2 m patches provide denser cover. Detailed meshes use opaque blades, seedheads and a little broadleaf variation over compact backing tufts. Their authored lowest LODs are small closed pointed volumes, each within 20–80 triangles, including the patches. No per-blade opacity mask is needed.

The 10 × 10 m preview uses 100 deterministic clump placements and four patches. Both LODs use identical placements and rotations. `Reports/grass_preview_placements.json` records the exact arrangement; it is preview data, not a native placement change. Individual clumps occupy very few pixels at 150 m; judge the retained field colour using the scatter as well as the individual views. Triangle budgets are verified; native draw-call and frame-time costs are not measured.

At 150 m the final scatter retains {grass_far['LOD3_over_LOD0_opaque_area_ratio']*100:.1f}% of detailed geometry coverage; patches A/B retain {patch_far['Patch_2m_A']['LOD3_over_LOD0_opaque_area_ratio']*100:.1f}% / {patch_far['Patch_2m_B']['LOD3_over_LOD0_opaque_area_ratio']*100:.1f}%. Patch silhouette-overlap flags remain because 80-triangle tufts replace individual blades. This is a reviewed simplification, documented in `Reports/VISUAL_REVIEW.json`. The low mounds look coarse at 15–50 m; preserve the detailed meshes near the viewer and inspect the actual native transition.

## Materials and import

- Metres, FBX −Y forward / Z up, ground pivots at origin. Apply the established metre-to-Unreal import conversion once; do not add a second ×100 scale.
- Opaque materials, alpha 1. Foliage is two-sided. No wind or collision. Slot names/order match each detailed/lowest pair, including unused slots.
- BaseColor is sRGB; Normal and ORM are non-colour. ORM channels are R=AO, G=roughness, B=metallic. Normals are OpenGL +Y; apply the project's established green-channel conversion when building Unreal materials.
- Retain the hull/tuft material assignments and matte roughness at distance. FBX does not automatically recreate all custom PBR connections. Do not inherit old citrus colours or opacity masks.

## Evidence and checks

`Reports/VALIDATION.json` records fresh imports of all 30 FBXs, compared with reopened source scenes: dimensions, pivots, triangles, UV0, finite geometry, solid alpha, closed lowest-LOD surfaces, matching slots and relative texture paths. All {len(baseline)} baseline files match the original hashes (`Reports/ORIGINALS_UNCHANGED.json`).

There are 154 fixed-camera frames: vines at 2/30/150/500 m including a 5-row × 10-tile block; olives at 5/50/100/300/1000 m plus top-down; every grass asset and the scatter at 2/15/50/150 m; and two 100 m legacy comparison frames. Both detailed and lowest meshes are rendered directly. Full frames remain 1920 × 1080 with a 60° horizontal FOV, fixed lighting and exposure. Close frames may crop; separate hero previews show whole models. Magnified diagnostic crops are clearly labelled.

Every distance frame binds to the source scene and texture hashes captured before rendering. `Reports/distance_validation.json` contains exact cameras, geometry-only alpha coverage and colour comparisons. `Reports/VISUAL_REVIEW.json` records the review of any numerical flags. These are offline Blender measurements, not proof of Unreal visibility, streaming, material appearance or HLOD selection. Verify the same native distance views, ground contact and actual final LOD assignment before scoped named saves and reopen.

Editable dimensions, seeds, palettes and construction settings remain in the three family build scripts. Rebuilding a family invalidates its preview/QA hashes; rerender and revalidate before use.

## Temporary cache

`Temp/DistanceCache/` contains approximately 2.06 GB of optional decoded image arrays. These are not needed for import or viewing the PNG evidence and are excluded from the delivery manifest. Automatic approval review blocked the attempted cache cleanup with the reason “blocked by policy”; the files were retained.
'''
(ROOT/'HANDOFF_CLAUDE.md').write_text(handoff,encoding='utf-8')
write('NATIVE_ACTIONS.json',{'status':'HANDOFF_ONLY_NOT_EXECUTED','native_actions_performed':False,'lod_pairings':pairs,
    'material_mode':'Opaque; foliage two-sided; alpha1','checks':['Assign each authored lowest mesh explicitly','Verify material slots and colours on both LODs','Check native near/far views and no unintended disappearance','Use existing instance/HLOD route','Verify ground contact and tile pitch','Scoped named saves and reopen by owning operator']})
cards=[]
for p in pairs:
    a=next(a for a in assets if a['name']==p['base_asset']);b=next(a for a in assets if a['name']==p['lowest_mesh']);label=html.escape(a['name'].replace('SM_PazFarm_',''))
    cards.append(f'<section><h2>{label}</h2><div class="pair"><article><a href="{a["preview"]}"><img loading="lazy" src="{a["preview"]}"></a><p>Detailed · {p["lod0_triangles"]:,} triangles · <a href="{a["fbx"]}">FBX</a></p></article><article><a href="{b["preview"]}"><img loading="lazy" src="{b["preview"]}"></a><p>Authored lowest LOD · {p["lowest_triangles"]:,} triangles · <a href="{b["fbx"]}">FBX</a></p></article></div><p><a href="{a["blend"]}">Editable Blender source</a></p></section>')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Karmei Yosef — FieldCrops v004</title><style>:root{color-scheme:dark}body{background:#1d231b;color:#edf0e7;font:16px/1.6 system-ui;margin:0}main{max-width:1380px;margin:auto;padding:36px 24px}h1{font-size:48px;line-height:1.12}a{color:#c8d6a8}nav{display:flex;flex-wrap:wrap;gap:20px;margin:24px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}article{background:#30392a;border-radius:10px;overflow:hidden}article img{display:block;width:100%}article p{margin:14px}.note{border-left:3px solid #a5b77c;padding-left:16px}section{margin:40px 0}@media(max-width:700px){.pair{grid-template-columns:1fr}h1{font-size:36px}}</style><main><p>OFFLINE BLENDER DELIVERY · NATIVE APPLICATION PENDING</p><h1>Vine rows, olive groves<br>and late-summer field grass.</h1><p>Fifteen models with solid foliage and deliberately authored lowest LODs. Three compatible vine tiles, four olive trees, six grass clumps and two patches.</p><nav><a href="Previews/Distance/INDEX.html">Distance comparisons</a><a href="HANDOFF_CLAUDE.md">Claude handoff</a><a href="MANIFEST.json">Manifest</a><a href="DONE.md">Completion</a></nav><p class="note">Each separate lowest-LOD FBX needs explicit assignment to its base mesh or far-instance path. Importing the detailed FBX alone does not install it.</p>'''+''.join(cards)+'''<h2>Verification</h2><p>Thirty fresh FBX imports, three reopened Blender sources and 154 fixed-distance frames. Geometry, units, pivots, material slots, solid alpha and vine tile joins are checked. Earlier farm deliveries remain unchanged.</p><nav><a href="Reports/VALIDATION.json">Model checks</a><a href="Reports/VISUAL_REVIEW.json">Visual review</a><a href="Reports/distance_validation.json">Distance measurements</a><a href="Reports/ORIGINALS_UNCHANGED.json">Originals preserved</a></nav><p class="note">Distance images are offline Blender evidence. Unreal imports, HLOD assignment, native appearance and persistence remain with the operator.</p></main></html>'''
(ROOT/'INDEX.html').write_text(page,encoding='utf-8')
(ROOT/'DONE.md').write_text(f'''# FieldCrops v004 — DONE

**Offline delivery complete. Native application and acceptance pending.**

- 3 trellised grapevine tiles, 4 olive trees, 6 grass clumps and 2 patches.
- 30 FBXs including an authored solid lowest LOD for every model; 3 Blender sources; {len(textures)} PBR maps.
- 154 fixed-camera frames, fitted model previews, vine seam checks and independent fresh FBX round-trips.
- {len(baseline)} original files unchanged by SHA256 comparison.

Open [INDEX.html](INDEX.html) and [HANDOFF_CLAUDE.md](HANDOFF_CLAUDE.md). Lowest LODs require explicit assignment; they are separate FBXs. No Unreal, Content, maps, asset bank, Houdini or git action was performed.
''',encoding='utf-8')
manifest={'revision':'FieldCrops_v004','date':'2026-10-11','status':'OFFLINE_COMPLETE_NATIVE_NOT_APPLIED','asset_count':30,'base_model_count':15,'source_blend_count':3,'material_texture_count':len(textures),
          'temporary_cache_note':'Temp/DistanceCache is optional, approximately 2.06GB, and excluded from deliverables. Automatic policy blocked cleanup; no alternate deletion was attempted.',
          'assets':assets,'lod_pairings':pairs,'distance_frame_count':154,'distance_validation':'Reports/distance_validation.json','visual_review':'Reports/VISUAL_REVIEW.json','originals_preserved':preservation,'native_actions_performed':False,'files':[]}
for folder in ('FBX','Blend','Textures','Scripts'):
    for p in sorted((ROOT/folder).rglob('*')):
        if p.is_file() and p.suffix.lower() not in ('.blend1','.pyc'):manifest['files'].append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
write('MANIFEST.json',manifest)
links=[];missing=[]
for page in (ROOT/'INDEX.html',ROOT/'Previews/Distance/INDEX.html'):
    for value in re.findall(r'(?:href|src)=["\']([^"\']+)',page.read_text(encoding='utf-8')):
        parsed=urlparse(value)
        if parsed.scheme or value.startswith('#') or not parsed.path:continue
        exists=(page.parent/unquote(parsed.path)).exists();links.append(value)
        if not exists:missing.append(value)
write('Reports/LINK_VALIDATION.json',{'passed':not missing,'local_targets_checked':len(links),'missing':missing});assert not missing
print(json.dumps({'status':manifest['status'],'assets':30,'textures':len(textures),'originals':len(baseline),'links':len(links)}))
