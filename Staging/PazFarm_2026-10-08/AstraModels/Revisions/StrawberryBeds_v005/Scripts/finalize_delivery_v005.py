"""Package only current, verified offline v005 assets and visual evidence."""
import hashlib,html,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def write(path,doc):(ROOT/path).write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

model=read('Reports/strawberries_v005.json');assets=model['assets']
assert len(assets)==8
qa=read('Reports/validation_v005.json')
assert qa.get('passed') is True, 'Fresh-import QA has not passed'
for r in qa['inputs'].values():assert sha(ROOT/r['file'])==r['sha256'], 'Stale geometry input: '+r['file']
for r in qa['assets']:assert sha(ROOT/r['file'])==r['sha256'], 'Stale FBX: '+r['file']
for r in qa['source']['images']:assert sha(ROOT/r['file'])==r['sha256'], 'Stale texture: '+r['file']
dist=read('Reports/distance_validation.json')
assert dist['status']=='COMPLETE_OFFLINE_EVIDENCE' and dist['actual_frames']==33 and dist['all_current']
for frame in dist['frames']:
    assert sha(ROOT/frame['source_blend'])==frame['source_blend_sha256']
    assert sha(ROOT/frame['file'])==frame['png_sha256']
    assert frame['texture_hash_capture']=='before render'
    for p,h in frame['source_texture_sha256'].items():assert sha(p)==h
refs=read('Reports/reference_selection.json')
assert refs['reference_gate']['status']=='PASSED_BEFORE_MODELLING'
for r in refs['selected']:assert sha(ROOT/r['path'])==r['sha256']
comparison=read('Reports/reference_comparison.json')
for k in ('photo','render'):assert sha(ROOT/comparison[k])==comparison[k+'_sha256']
assert sha(ROOT/comparison['file'])==comparison['output_sha256']
review=read('Reports/INDEPENDENT_VISUAL_REVIEW.json')
assert review.get('delivery_ready') is True and not review.get('blocking_issues')
for p,h in review.get('input_hashes',{}).items():assert sha(ROOT/p)==h, 'Stale review: '+p
baseline=read('Reports/ORIGINAL_INPUTS_SHA256.json')
earlier_models=[r for r in baseline if Path(r['path']).is_relative_to(ROOT.parents[1])]
changed=[]
for r in baseline:
    p=Path(r['path'])
    current=sha(p) if p.is_file() else None
    if current!=r['sha256']:
        changed.append({'path':r['path'],'before_sha256':r['sha256'],'current_sha256':current,
                        'within_earlier_model_deliveries':p.is_relative_to(ROOT.parents[1]),
                        'edited_by_this_task':False})
changed_models=[r for r in changed if r['within_earlier_model_deliveries']]
preservation={'passed':not changed_models,'scope':'Earlier AstraModels deliveries; broader farm snapshot differences retained separately',
              'earlier_model_files_checked':len(earlier_models),'earlier_models_changed_or_missing':changed_models,
              'files_checked':len(baseline),'bytes_checked':sum(r['bytes'] for r in baseline),
              'all_snapshot_files_unchanged':not changed,'broader_snapshot_differences':changed,
              'method':'Streaming SHA256 compared with the immutable pre-work baseline of earlier farm files.',
              'broader_difference_note':'RESULT_CLONE_V2_2026-10-11.md outside AstraModels was updated during the snapshot interval. Readback contains the operator placement update at 15:42Z. This task did not edit it or restore its previous bytes; the writer was not independently identified.'}
write('Reports/ORIGINALS_UNCHANGED.json',preservation)
assert not changed_models, changed_models
pairs=[]
for a in assets:
    if a['name'].endswith('_LOD3'):continue
    low=next(b for b in assets if b['name']==a['name']+'_LOD3')
    assert [m['name'] for m in a['materials']]==[m['name'] for m in low['materials']]
    pairs.append({'base_model':a['name'],'detailed_fbx':a['fbx'],'lowest_fbx':low['fbx'],
                  'detailed_triangles':a['triangles_LOD0'],'lowest_triangles':low['triangles_LOD0'],
                  'source':a['blend'],'material_slots':[m['name'] for m in a['materials']],
                  'detailed_dimensions_m':a['size_metres_W_D_H'],'lowest_dimensions_m':low['size_metres_W_D_H'],
                  'pivot_m':a['pivot']['position_metres']})
textures=sorted({p.replace('\\','/') for a in assets for m in a['materials'] for p in m['textures']})
table='\n'.join(f"| `{p['base_model']}` | {p['detailed_triangles']:,} | {p['lowest_triangles']:,} |" for p in pairs)
byid={f['id']:f for f in dist['frames']}
distance_rows=[]
for d in (60,150,500,4000):
    p=next(p for p in dist['comparisons'] if p['id']==f'block_10x5_{d}m')
    a,b=byid[p['LOD0_frame']],byid[p['LOD3_frame']]
    distance_rows.append(f"| {d:,} m | {a['metrics']['equivalent_opaque_pixels']:.2f} | {b['metrics']['equivalent_opaque_pixels']:.2f} | {p['lowest_area_ratio']:.3f} | {p['lowest_minus_detailed_luma']:+.2f} |")
distance_table='\n'.join(distance_rows)

handoff=f'''# Paz Farm — StrawberryBeds v005

**Offline Blender delivery complete. Native import, placement and visual acceptance remain with the Unreal operator.**

The previous continuous green block is replaced with young, separate plants on dusty charcoal mulch. Real planting photographs were gathered, retained and reviewed before modelling. Start with `INDEX.html` and `Previews/REFERENCE_COMPARISON.png`.

## Delivered models

| Model | Detailed triangles | Authored lowest triangles |
|---|---:|---:|
{table}

Eight FBXs, one editable `Blend/StrawberryBeds.blend`, {len(textures)} original PBR maps, three regular variants and a separate terminal cap. The regular modules have solid serrated trifoliate leaves, real film openings with exposed soil, rounded/sloped shoulders, soil-covered edges and no close-range canopy hull. There is no fruit or flower. The repeated modules have no short-end walls.

## Placement contract

- Regular tile: **4 m along local +Y, Y=0..4**, pivot exactly `(0,0,0)` at ground centre of the start end. **Minimum Z=-0.15 m is a hidden skirt, not the placement pivot.** Do not recenter the mesh to its minimum bound.
- Bed top is approximately 0.8 m wide and 0.25 m above the pivot, with sloping sides to approximately 1.1 m base width. Young plants rise above that top. Use the actual measured bounds in `MANIFEST.json`; below-ground depth is included in total bound height.
- Mix A/B/C at **1.7 m row centres**. Tilt each tile to the local ground, then place the next start pivot at the previous tile's transformed `(0,4,0)` endpoint. A 3% longitudinal slope uses `atan(0.03)=1.718358 degrees`; simply adding 4 m in horizontal Y after rotation introduces gaps.
- The previews use 50 regular tiles: 10 rows × 5 tiles, 20 m surface length. Both LODs share exactly the same placement. Twenty optional caps close both row ends. `Reports/slope_preview_placements.json` records the transforms.
- `SM_PazFarm_StrawberryBedEnd` joins with its Y=0 edge at the row's final Y=4 endpoint. For the beginning of a row, rotate the cap 180 degrees about the tile's local up axis so it extends away from the start. Apply the terrain pitch to that orientation as well.
- A modest sink can use the skirt to hide contact gaps. The skirt does not conform rigid tiles to curved terrain, nor fix incorrect tile tilt. Planar-slope evidence does not prove arbitrary native terrain placement.

## Lowest LOD: install explicitly

Each base FBX contains only its detailed mesh. **Assign its matching separate `_LOD3.fbx` as the final custom LOD or as the geometry used by the existing far-instance route.** File naming alone does not install an LOD chain. The lowest mesh is a film-coloured mound with sparse muted green detail, without a bright green backing band or billboard.

The brief's 60 m–4 km route uses always-loaded Instancing HLOD with Nanite disallowed. The supplied lowest geometry is conventional opaque geometry for that route. Preserve it instead of substituting automatic reduction. No HLOD, streaming or native project settings were changed here.

## Materials

- Selected film: **dark charcoal-black**, based on the Huelva planting photograph. The white UC ANR film photograph informed shape and planting scale only. `Reports/REFERENCES.md` gives originals, credits and limits. Photos are references, not model textures.
- Use all supplied material slots in their recorded order on both LODs, including unused roles. In particular, keep the distant mulch role assigned to the low mesh; do not inherit v003's green canopy material.
- BaseColor is sRGB; Normal and ORM are non-colour. ORM is R=AO, G=roughness, B=metallic. Normal maps use OpenGL +Y; use the project's established green-channel conversion for Unreal.
- All materials and leaf geometry are opaque, with solid alpha. Film roughness is at least 0.85 and specular is low. No wind, collision or opacity masks. FBX does not recreate the full custom PBR graph automatically.
- Metres, FBX -Y forward / Z up. Apply the established metre-to-Unreal conversion once, without adding another ×100.
- FBXs retain the source polygons and corner normals. The budgets above count their evaluated triangles. Exporter-side triangulation changed shading on small stems, so it is disabled; final fresh imports and a focused source/export image comparison verify the corrected shading. Preserve imported normals and inspect native triangulation/shading during import.

## Appearance and distance evidence

`Previews/Distance/INDEX.html` contains 33 source-render frames. Each A/B/C tile is shown at 1 and 3 m with both LODs. The mixed 3% slope block is shown at 15/60/150/500 m with both LODs and soil-ground views. There is an extra 4 km geometry-only stress view, a portrait reference-angle render and two seam views.

Full comparison frames are 1920 × 1080. Singles use 85° horizontal FOV and 45° elevation; the block uses 110° and 70° elevation to keep the whole requested field visible at 15 m. Distances are camera-to-target slant distances. No distance frame is auto-fitted. The 1 m views intentionally show local detail; fitted previews show the entire module. The reference render is 800 × 1200. Lighting/exposure remain fixed within the comparison suite.

| Block distance | Detailed coverage px | Lowest coverage px | Lowest/detailed area | Lowest luma change |
|---|---:|---:|---:|---:|
{distance_table}

Coverage is alpha-weighted equivalent opaque pixels with holdout ground hiding the skirt and excluding cast shadows. Lit sRGB measurements are from saved PNG bytes, not BaseColor swatches. Magnified crops are labelled and never replace the full frames. At 4 km the entire block occupies very few pixels; individual stripe separation cannot be guaranteed at that resolution/FOV. Check actual native material lighting, anti-aliasing and lowest-LOD selection in the operator's distance captures.

The photo comparison is a shape and planting-stage reference, not a matched-lighting reproduction. The model is darker, more regular and smoother than the bright Huelva photograph; its young leafy plugs follow the separate UC ANR references. Procedural microdetail remains simpler than real dusty film and clods. The optional cap has a different film UV phase at its join; this is recorded separately from its continuous geometry.

## Verification and retained evidence

`Reports/validation_v005.json` contains independent fresh-process source/FBX checks, dimensions, pivot/skirt, triangle budgets, material order, UV0, finite geometry, opaque textures and all directed variant joins. Intentional open film/soil ends and planting openings are distinguished from accidental boundary edges; solid leaves remain closed.

`Reports/distance_validation.json` binds every frame to source and texture hashes recorded before rendering. `Reports/INDEPENDENT_VISUAL_REVIEW.json` records the photo comparison and near/far review. `Reports/ORIGINALS_UNCHANGED.json` confirms all {len(earlier_models):,} earlier model-delivery files match their pre-work hashes. The broader {len(baseline):,}-file farm snapshot contains one changed placement report outside AstraModels (`RESULT_CLONE_V2_2026-10-11.md`); this task left it untouched and records its before/current hashes separately.

`Reports/strawberries_v005_fbx_normal_comparison.json` records the final export appearance comparison. Reports named `probe`, `draft` or `before_fix` preserve intermediate diagnostics and do not supersede the final validation report.

Editable parameters, seeds, dimensions and palettes remain in `Scripts/build_strawberries_v005.py`. A rebuild invalidates current export, preview and QA hashes; rerender and revalidate before handoff. Compressed preview caches under `Temp/` are optional and excluded from the asset manifest.

All writes were confined to `AstraModels/Revisions/StrawberryBeds_v005/`. No Unreal, Content, maps, bank, Houdini or git action was performed.
'''
(ROOT/'HANDOFF_CLAUDE.md').write_text(handoff,encoding='utf-8')
(ROOT/'Reports/distance_notes.md').write_text(f'''# Lowest LOD and distance checks

The detailed mesh has no green canopy hull. The lowest mesh is a coarse dark mulch mound carrying faint green plant marks, retaining all material slots. It was rendered directly, not obtained by automatic reduction during these previews.

33 current source-render frames; 11 matched geometry-only LOD pairs. See `distance_validation.json` for cameras, pre-render source/texture hashes and saved-PNG coverage/colour. Soil-ground frames show the 10×5 mixed field at 1.7 m centres on a 3% slope.

| Distance | Detailed px | Lowest px | Area ratio | Luma difference |
|---|---:|---:|---:|---:|
{distance_table}

The 4 km frame is a pixel-limit stress check. Individual 1.1 m beds cannot be expected to remain separable at all resolutions and camera FOVs. Native HLOD assignment, antialiasing and lighting are not tested by Blender evidence. The operator must explicitly install the supplied final LOD and inspect its native distance captures.
''',encoding='utf-8')
cards=[]
for p in pairs:
    a=next(a for a in assets if a['name']==p['base_model']);b=next(a for a in assets if a['name']==p['base_model']+'_LOD3')
    cards.append(f'''<section><h2>{html.escape(a['name'].replace('SM_PazFarm_',''))}</h2><div class="pair"><article><a href="{a['preview']}"><img loading="lazy" src="{a['preview']}"></a><p>Detailed · {p['detailed_triangles']:,} triangles · <a href="{a['fbx']}">FBX</a></p></article><article><a href="{b['preview']}"><img loading="lazy" src="{b['preview']}"></a><p>Authored lowest · {p['lowest_triangles']:,} triangles · <a href="{b['fbx']}">FBX</a></p></article></div></section>''')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Paz Farm · Young strawberry beds v005</title><style>:root{color-scheme:dark}body{background:#20241e;color:#e9eddf;font:16px/1.65 system-ui;margin:0}main{max-width:1400px;margin:auto;padding:32px 24px}h1{font-size:50px;line-height:1.12}h2{font-size:27px}a{color:#c6dca1}nav{display:flex;flex-wrap:wrap;gap:22px;margin:24px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}article{background:#303829;border-radius:10px;overflow:hidden}img{max-width:100%;display:block}article img{width:100%}article p{margin:14px}.note{border-left:3px solid #a8bd7e;padding-left:16px}section{margin:40px 0}@media(max-width:700px){.pair{grid-template-columns:1fr}h1{font-size:36px}}</style><main><p>PAZ FARM · OFFLINE BLENDER DELIVERY</p><h1>Young plants.<br>Dark mulch. Natural bed edges.</h1><p>Three 4 m strawberry-bed variants and a separate end cap, built from real planting photographs. Small solid leaves sit above wrinkled film with visible soil openings; the authored lowest LOD keeps the dark film stripe.</p><nav><a href="Previews/Distance/INDEX.html">Near and far review</a><a href="HANDOFF_CLAUDE.md">Operator handoff</a><a href="MANIFEST.json">Manifest</a><a href="DONE.md">Completion</a></nav><p class="note">Native application is pending. Preserve the start-end ground pivot, 1.7 m row spacing and below-ground skirt. Explicitly assign each separate lowest-LOD FBX.</p><section><h2>Reference and model</h2><a href="Previews/REFERENCE_COMPARISON.png"><img src="Previews/REFERENCE_COMPARISON.png"></a><p>Agrofresas planting photograph (Huelva, Spain), alongside the offline model from a comparable view down the furrows. Leafy young plugs follow UC ANR photographs. <a href="Reports/REFERENCES.md">Sources and selected features</a>.</p></section>'''+''.join(cards)+'''<section><h2>Rows on a 3% slope</h2><a href="Previews/SLOPE_DISTANCE_CONTACT_SHEET.png"><img loading="lazy" src="Previews/SLOPE_DISTANCE_CONTACT_SHEET.png"></a><p>Detailed left, authored lowest right. Full-resolution frames and labelled magnified crops are in the distance review.</p></section><section><h2>Joined row end</h2><a href="Previews/Strawberry_A_EndCap_FBX_JoinedClose.png"><img loading="lazy" src="Previews/Strawberry_A_EndCap_FBX_JoinedClose.png"></a><p>Freshly imported bed and end-cap FBXs at 2.29 m, using the supplied materials.</p></section><h2>Verification</h2><nav><a href="Reports/validation_v005.json">Fresh FBX and seams</a><a href="Reports/INDEPENDENT_VISUAL_REVIEW.json">Independent visual review</a><a href="Reports/distance_validation.json">Distance measurements</a><a href="Reports/ORIGINALS_UNCHANGED.json">Earlier files preserved</a><a href="Blend/StrawberryBeds.blend">Editable Blender source</a></nav><p class="note">No Unreal, Content, maps, bank, Houdini or git action was performed. Native material conversion, ground tilt, HLOD selection and final scene acceptance remain with the operator.</p></main></html>'''
(ROOT/'INDEX.html').write_text(page,encoding='utf-8')
(ROOT/'DONE.md').write_text(f'''# StrawberryBeds v005 — DONE

**Offline delivery complete. Native application and acceptance pending.**

- Three young strawberry-bed variants and one optional end cap.
- Eight FBXs, including a separate authored lowest LOD for each; one editable Blender scene; {len(textures)} PBR maps.
- Four retained real photo references, a reference/model comparison, fitted previews and 33 additional near/far, slope and seam frames.
- Fresh source/FBX round-trips, variant seams, pivot/skirt, budgets, UVs and opaque materials checked.
- All {len(earlier_models):,} earlier model files unchanged by SHA256 comparison. The broader snapshot's separate placement-report change is recorded in `Reports/ORIGINALS_UNCHANGED.json`.

Open [INDEX.html](INDEX.html) and [HANDOFF_CLAUDE.md](HANDOFF_CLAUDE.md). No Unreal, Content, maps, bank, Houdini or git action was performed.
''',encoding='utf-8')
write('NATIVE_ACTIONS.json',{'status':'HANDOFF_ONLY_NOT_EXECUTED','native_actions_performed':False,'lod_pairings':pairs,
    'row_centres_m':1.7,'pivot':'Ground centre of start end, exact origin; minimum Z=-0.15 is skirt',
    'operator_actions':['Import detailed and explicitly assign matching authored lowest LOD','Retain new dark mulch and distant mulch material slots','Tilt and chain every tile by transformed endpoints','Use separate end caps only at row ends','Verify actual 60m-4km far-instance geometry under existing HLOD route','Review ground contact, native materials and near/far scene appearance']})
manifest={'revision':'StrawberryBeds_v005','completed_at_utc':datetime.now(timezone.utc).isoformat(),
          'status':'OFFLINE_COMPLETE_NATIVE_NOT_APPLIED','base_model_count':4,'asset_count':8,'source_blend_count':1,
          'material_texture_count':len(textures),'assets':assets,'lod_pairings':pairs,'reference_selection':'Reports/reference_selection.json',
          'distance_frame_count':33,'distance_validation':'Reports/distance_validation.json','fresh_import_validation':'Reports/validation_v005.json',
          'visual_review':'Reports/INDEPENDENT_VISUAL_REVIEW.json','originals_preserved':preservation,'native_actions_performed':False,
          'excluded':'Temp caches, runtime logs, and any .blend1 backups are not import dependencies. Reference photographs retain their original copyrights.','files':[]}
for folder in ('FBX','Blend','Textures','Scripts','References','Reports','Previews'):
    for p in sorted((ROOT/folder).rglob('*')):
        if p.is_file() and p.suffix.lower() not in ('.blend1','.pyc','.log'):
            manifest['files'].append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
for name in ('INDEX.html','DONE.md','HANDOFF_CLAUDE.md','NATIVE_ACTIONS.json','ASSIGNMENT.json'):
    p=ROOT/name
    manifest['files'].append({'path':name,'bytes':p.stat().st_size,'sha256':sha(p)})
write('MANIFEST.json',manifest)
print('PACKET_COMPLETE',len(assets),'FBXs',len(textures),'maps',len(earlier_models),'earlier model files unchanged;',len(changed),'broader snapshot differences recorded')
