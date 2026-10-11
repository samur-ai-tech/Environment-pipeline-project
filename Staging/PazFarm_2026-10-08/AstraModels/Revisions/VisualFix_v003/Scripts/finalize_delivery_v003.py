"""Finalize the reviewed v003 offline packet without modifying older deliveries."""
import hashlib, html, json, re
from pathlib import Path
from urllib.parse import unquote, urlparse
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def write(path,data):
    target=ROOT/path
    assert target.resolve().is_relative_to(ROOT.resolve())
    target.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assets=[]
for f in ['pines_v003.json','strawberries_v003.json']:assets+=read('Reports/'+f)['assets']
qa=read('Reports/VALIDATION.json')
assert qa['passed'] and len(assets)==8
for result in qa['assets']:
    a=next(a for a in assets if a['name']==result['name'])
    assert result['sha256']==sha(ROOT/a['fbx']), result['name']+' stale model QA'
for source in qa['sources']:
    assert source['sha256']==sha(ROOT/source['file']), source['file']+' stale source QA'
    for texture in source['images']:
        assert texture['delivery_path'] and texture['sha256']==sha(ROOT/texture['delivery_path']), texture['name']+' stale texture QA'
distance=read('Reports/distance_validation.json')
assert distance['status']=='OFFLINE_DISTANCE_EVIDENCE_COMPLETE'
assert distance['diagnostic_result']=='PASS_COMPLETED_PAIRS'
assert distance['pass_criteria']['fixed_frame_and_settings']
assert distance['pass_criteria']['all_LOD_pairs_have_nonzero_geometry']
assert distance['all_frame_source_bindings_current']
for frame in distance['frames']:
    source='Blend/AleppoPine.blend' if frame['family']=='pines' else 'Blend/Strawberry.blend'
    assert frame['source_blend_sha256']==sha(ROOT/source), frame['id']+' stale source'
    assert frame['png_sha256']==sha(ROOT/frame['file']), frame['id']+' image hash mismatch'
    assert frame.get('source_texture_sha256'), frame['id']+' missing texture dependencies'
    for texture_path,texture_hash in frame['source_texture_sha256'].items():
        assert texture_hash==sha(ROOT/texture_path), frame['id']+' stale render texture'
assert (ROOT/'Previews/Distance/INDEX.html').is_file()
records=read('Reports/ORIGINAL_INPUTS_SHA256.json')
changed=[r['path'] for r in records if not Path(r['path']).is_file() or sha(Path(r['path']))!=r['sha256']]
preservation={'passed':not changed,'files_checked':len(records),'changed_or_missing':changed,
              'method':'SHA256 compared with baseline captured before v003 work. Includes original Paz Farm staging files, v002 and the six supplied forest/bed captures.'}
write('Reports/ORIGINALS_UNCHANGED.json',preservation)
assert not changed, changed
textures=sorted({t.replace('\\','/') for a in assets for m in a['materials'] for t in m['textures']})
pairs=[]
for high in [a for a in assets if not a['name'].endswith('_LOD3')]:
    low=next(a for a in assets if a['name']==high['name']+'_LOD3')
    pairs.append({'base_asset':high['name'],'lod0_fbx':high['fbx'],'lowest_mesh':low['name'],'lowest_fbx':low['fbx'],
                  'lod0_triangles':high['triangles_LOD0'],'lowest_triangles':low['triangles_LOD0'],
                  'source':high['blend'],'lowest_role':'Authored final conventional LOD for the non-Nanite far/HLOD path; separate FBX, not embedded in the base export.'})
table='\n'.join(f"| `{p['base_asset']}` | {p['lod0_triangles']:,} | {p['lowest_triangles']:,} | `{p['lowest_fbx']}` |" for p in pairs)
handoff=f'''# Paz Farm / Karmei Yosef — VisualFix v003

**Offline Blender delivery. No Unreal import, HLOD rebuild, map save or native acceptance was performed.**

This revision follows `Staging/PazFarm_2026-10-08/HANDOFF_ASTRA_VisualFix_v003.md` dated 2026-10-10. The supplied six distance captures were reviewed. Work is confined to `AstraModels/Revisions/VisualFix_v003/`; older deliveries remain unchanged. Start with `INDEX.html` and the distance gallery in `Previews/Distance/INDEX.html`.

## Meshes and the lowest-LOD contract

| Base mesh | LOD0 triangles | Lowest triangles | Separate lowest-LOD FBX |
|---|---:|---:|---|
{table}

**The base FBX contains LOD0 only.** The `_LOD3` files are explicit low-detail geometry, not billboard cards or automatically linked LODs. Import each matching `_LOD3.fbx` as the base mesh's final custom LOD, or explicitly bind that low mesh to the receiving operator's far-instance path. Record the resulting native LOD index and verify the actual mesh drawn. The suffix describes its intended role; a separately imported asset alone does not update the original mesh's LOD chain. Do not allow automatic reduction or a billboard to replace this authored final LOD.

The operator's brief specifies always-loaded Instancing HLOD with Nanite disallowed and each instance using the lowest LOD. Apply these files to that existing route under the operator's current ownership. This packet neither creates nor changes that system. Near-tree Nanite and far conventional rendering must be verified separately.

## Aleppo pine

Three original *Pinus halepensis* variants target heights 8 / 11 / 15 m and crown widths 6 / 8 / 10 m. The asymmetrical leaning trunks support irregular, flattened clump crowns. LOD0 uses solid needle geometry and opaque inner crown clumps; lowest LOD retains a trunk and solid crown volumes. No masked needle cards, wind or collision are included. Details and editable parameters are in `Scripts/build_pines_v003.py` and `Reports/pines_v003.json`.

Use the three material roles: bark, opaque two-sided needles, and opaque crown hull. Keep needle and hull colours closely matched, dark grey-olive. The far crown depends on its hull material, so do not inherit a pale default or masked store-pine material on it. Use the authored final mesh for every pine variant rather than reusing one generic silhouette.

## Strawberry bed

`SM_PazFarm_StrawberryBed_4m` retains the 0.8 × 4 m tile, ground/start-end pivot and +Y tile direction. Replace the current mesh in place and retain all 763 existing placements. Its closed continuous opaque green canopy sits beneath fewer, larger rosettes. Dark mulch has high roughness and reduced specular/normal response. The lowest mesh keeps a continuous green ridge over the mulch strip, with no dependence on tiny individual leaves.

LOD0 and lowest LOD share the same tile envelope and compatible end profiles. Preserve all instance positions, rotations and scale; do not widen the mesh, move its pivot or offset successive tiles. `Scripts/build_strawberries_v003.py` contains editable dimensions, canopy height/colour, rosette count and mulch settings. Component construction and QA are in `Reports/strawberries_v003.json`.

The strawberry lowest mesh deliberately retains all nine material slots: visible mulch is **slot 0 `M_PazFarm_StrawberryMulch_v003`** and the green ridge is **slot 8 `M_PazFarm_StrawberryCanopy_v003`**. Do not remap the canopy to slot 1 simply because only two surface roles are used.

## Import and material settings

- Source units are metres, pivot at ground origin (bed at the centre of its start end), FBX −Y forward / Z up with FBX Units Scale. Reuse the established metre-to-Unreal import conversion once. Fresh round-trips check size and pivot; do not add another ×100 scale.
- Use **Opaque** foliage and hull materials, alpha 1, two-sided needles/leaves. Do not connect the old opacity masks or substitute translucent foliage. No wind animation or displacement is required.
- BaseColor uses sRGB. Normal and ORM use non-colour data; ORM is R=AO, G=roughness, B=metallic. Normals use OpenGL +Y; apply the project's established Unreal green-channel conversion. Preserve the authored dark colours and matte roughness on both LODs. FBX does not reconstruct these custom material connections automatically.
- Map each low mesh's material slots by its own recorded names. Low meshes use fewer surface roles than the detailed meshes. Check the material remap after assigning a custom LOD; a wrong remap can turn a canopy into bark or plastic.

## Distance evidence and acceptance

`Previews/Distance/INDEX.html` contains actual perspective frames and labelled magnifications. `Reports/distance_validation.json` records camera distances, resolution, FOV, fixed light/exposure, alpha silhouette and colour measurements. `Reports/distance_notes.md` explains the comparisons. Close fixed-distance views can crop a tall tree or a multi-bed block; fitted hero previews are provided separately. Far frames are never auto-framed to disguise their projected size.

Pine previews cover 5, 50, 300 and 1,000 m, plus top-down inspection. Bed previews cover a single tile and ten tiles at 2, 30, 150 and 500 m. Lowest LODs are rendered directly in Blender without Nanite. The ten-tile block uses five parallel rows and two end-to-end tiles per row, at 5.48 m row pitch. All distances and targets are disclosed in the camera receipt.

The geometry and offline images demonstrate retained solid crowns/ridges. They do not guarantee a particular pixel footprint under every native FOV, screen resolution, exposure, mip filter, anti-aliasing or atmosphere. At kilometre distances the projected tree is small; preserve that honest scale in native review. Native acceptance requires the same provided forest and strawberry camera views, explicitly showing the authored lowest meshes in the always-loaded non-Nanite path. Check no disappearance, no pale material swap, no billboard, complete trunks/crowns, continuous dark-green rows, ground contact and no duplicate instances before named saves/reopen.

## Verification and preservation

`Reports/VALIDATION.json` checks all eight fresh FBX imports and both retained Blender sources: dimensions, pivots, triangle budgets, UV0, finite geometry/normals/UVs, material order, solid texture alpha, relative texture paths and closed manifold lowest-LOD surfaces. Component QA includes construction and tile seam checks. `Reports/ORIGINALS_UNCHANGED.json` verifies {len(records)} original files against their pre-work hashes. `MANIFEST.json` includes LOD pairings and hashes of deliverables.

No forest placement, farm ground, fence, barn, bank, existing map, Content asset, Houdini graph or git state is changed by this revision. The optional young pine is omitted; the three requested mature variants are delivered.
'''
(ROOT/'HANDOFF_CLAUDE.md').write_text(handoff,encoding='utf-8')
write('NATIVE_ACTIONS.json',{'status':'HANDOFF_ONLY_NOT_EXECUTED','source_brief':'../../../HANDOFF_ASTRA_VisualFix_v003.md',
    'lod_pairings':pairs,'preserve_strawberry_instances':763,'material_mode':'OPAQUE; foliage two-sided; alpha1',
    'required_native_checks':['Actual authored lowest mesh in the non-Nanite HLOD path','No automatic billboard or replacement reduction','Correct low-LOD material remapping','Same forest and strawberry distance cameras','Ground contact and no duplicate instances','Scoped named saves and reopen'],
    'native_actions_performed':False})
manifest={'revision':'VisualFix_v003','date':'2026-10-10','status':'OFFLINE_COMPLETE_NATIVE_NOT_APPLIED','asset_count':len(assets),
    'base_model_count':len(pairs),'source_blend_count':len({a['blend'] for a in assets}), 'material_texture_count':len(textures),
    'assets':assets,'lod_pairings':pairs,'handoff':'HANDOFF_CLAUDE.md','distance_gallery':'Previews/Distance/INDEX.html',
    'model_validation':'Reports/VALIDATION.json','distance_validation':'Reports/distance_validation.json','distance_frame_count':distance['actual_frames'],'distance_diagnostics':distance['diagnostic_result'],'originals_preserved':preservation,
    'native_actions_performed':False,'files':[]}
for folder in ['FBX','Blend','Textures','Scripts']:
    for p in sorted((ROOT/folder).rglob('*')):
        if p.is_file() and p.suffix.lower() not in ['.blend1','.pyc']:
            manifest['files'].append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
write('MANIFEST.json',manifest)
cards=[]
for pair in pairs:
    a=next(a for a in assets if a['name']==pair['base_asset']);b=next(a for a in assets if a['name']==pair['lowest_mesh'])
    label=html.escape(a['name'].replace('SM_PazFarm_',''))
    cards.append(f'<section class="model"><h2>{label}</h2><div class="pair"><article><a href="{a["preview"]}"><img src="{a["preview"]}" alt="{label} detailed mesh"></a><h3>Detailed mesh</h3><p>{pair["lod0_triangles"]:,} triangles · <a href="{a["fbx"]}">FBX</a></p></article><article><a href="{b["preview"]}"><img src="{b["preview"]}" alt="{label} lowest LOD"></a><h3>Authored lowest LOD</h3><p>{pair["lowest_triangles"]:,} triangles · <a href="{b["fbx"]}">FBX</a></p></article></div><p><a href="{a["blend"]}">Editable Blender source</a></p></section>')
page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Paz Farm / Karmei Yosef — VisualFix v003</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{background:#17201a;color:#eff3e9;font:16px/1.6 system-ui;margin:0}main{max-width:1380px;margin:auto;padding:44px 28px}h1{font-size:clamp(32px,5vw,56px);line-height:1.1;max-width:1000px}h2{font-size:26px;margin-top:38px}h3{margin:12px 16px 0}p{max-width:1000px}a{color:#b4d7a3}nav{display:flex;gap:14px;flex-wrap:wrap;margin:28px 0}nav a,.badge{border:1px solid #607951;border-radius:9px;padding:9px 14px;text-decoration:none}.badge{font-size:13px;display:inline-block;color:#dbe9bb}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}article{background:#243329;border:1px solid #42503c;border-radius:12px;overflow:hidden}article img{display:block;width:100%;height:auto}article p{margin:6px 16px 18px}.note{border-left:3px solid #9eb97e;padding-left:18px;color:#c4d1bd}li{margin:7px 0}@media(max-width:760px){main{padding:24px 16px}.pair{grid-template-columns:1fr}}
</style></head><body><main><span class="badge">OFFLINE BLENDER DELIVERY · NATIVE APPLICATION PENDING</span><h1>Solid crowns.<br>Continuous green beds.</h1><p>Three Aleppo pines and a revised strawberry tile, each with a deliberately authored lowest LOD for distant instances. The low meshes retain real crown or ridge geometry; no billboard or masked needle card is used.</p><nav><a href="Previews/Distance/INDEX.html">Distance comparisons</a><a href="HANDOFF_CLAUDE.md">Claude handoff</a><a href="MANIFEST.json">Files and LOD pairings</a><a href="DONE.md">Completion note</a></nav><p class="note">The separate lowest-LOD FBXs must be assigned to the receiving mesh's final LOD or explicitly bound to its far-instance path. Importing the detailed FBX alone does not install the low mesh.</p>'''+''.join(cards)+'''<h2>Distance proof</h2><p>Inspect the original-size perspective frames alongside clearly labelled magnifications. Lighting and exposure stay fixed. Pines are shown through 1 km; strawberry tiles and a ten-tile block through 500 m. Both detailed and lowest meshes are compared directly, without Nanite.</p><nav><a href="Previews/Distance/INDEX.html">Open all distances</a><a href="Reports/distance_notes.md">Camera and measurement method</a><a href="Reports/distance_validation.json">Distance measurements</a></nav><h2>Delivery checks</h2><ul><li>All eight meshes pass fresh FBX round-trips; both Blender sources reopen with their textures.</li><li>Lowest LODs are closed solid geometry within the requested triangle budgets.</li><li>Metre units, pivots, UV0, solid alpha and material mappings are verified.</li><li>Original farm assets, v002 and supplied capture files match the pre-work hashes.</li></ul><nav><a href="Reports/VALIDATION.json">Model checks</a><a href="Reports/ORIGINALS_UNCHANGED.json">Preservation receipt</a></nav><p class="note">These are offline Blender previews. Unreal imports, HLOD rebuilding, native distance behaviour, named saves and reopen remain with the operator.</p></main></body></html>'''
(ROOT/'INDEX.html').write_text(page,encoding='utf-8')
done=f'''# VisualFix v003 — DONE

**Offline Blender delivery complete. Native application and acceptance remain pending.**

- Three Aleppo pines (8 / 11 / 15 m target heights) with geometric needles, opaque crown volumes and separate authored lowest LODs.
- Strawberry v003 with the unchanged 0.8 × 4 m tile and start-end pivot, continuous opaque green canopy, darker matte mulch and a simple lowest-LOD ridge.
- **8 FBX meshes, 2 editable Blender sources, {len(textures)} material PNG maps**. See `MANIFEST.json` for exact LOD pairings and triangle counts.
- Actual fixed-camera distance previews for both mesh levels, individual beds and a ten-tile block; labelled magnifications and measurement receipts in `Previews/Distance/` and `Reports/`.
- Independent fresh FBX/source checks pass. **{len(records)} original files remain unchanged** by SHA256 comparison.

Open [INDEX.html](INDEX.html) and [HANDOFF_CLAUDE.md](HANDOFF_CLAUDE.md). The low FBXs require explicit native LOD assignment; they are not embedded in the detailed export. No Unreal, Content, map, bank, Houdini or git action was performed.
'''
(ROOT/'DONE.md').write_text(done,encoding='utf-8')
# Delivery links are checked after every final assembly.
links=[];missing=[]
for page in [ROOT/'INDEX.html',ROOT/'Previews/Distance/INDEX.html']:
    for value in re.findall(r'(?:href|src)=["\']([^"\']+)',page.read_text(encoding='utf-8')):
        parsed=urlparse(value)
        if parsed.scheme or value.startswith('#') or not parsed.path:continue
        target=(page.parent/unquote(parsed.path)).resolve()
        links.append({'page':str(page.relative_to(ROOT)),'target':value,'exists':target.exists()})
        if not target.exists():missing.append(value)
write('Reports/LINK_VALIDATION.json',{'passed':not missing,'local_targets_checked':len(links),'missing':missing})
assert not missing,missing
print(json.dumps({'status':manifest['status'],'assets':len(assets),'textures':len(textures),'originals':len(records),'local_links':len(links)}))
