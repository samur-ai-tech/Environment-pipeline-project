"""Read back retained Blender files and their texture paths; no edits."""
import bpy,json,pathlib,hashlib
ROOT=pathlib.Path('C:/Users/USER/Documents/Pipeline Environment/ModelBank/Prepared_2026-10-04')
OUT=pathlib.Path(__file__).resolve().parent
records=[]
for p in sorted(ROOT.glob('*/ASSET.json')):
    r=json.loads(p.read_text());bpy.ops.wm.open_mainfile(filepath=r['prepared_blend'],load_ui=False,use_scripts=False)
    meshes={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
    issues=[]
    for old in r['objects']:
        ob=meshes.get(old['name'])
        if ob is None:issues.append('missing_object:'+old['name']);continue
        if len(ob.data.vertices)!=old['vertices']:issues.append('vertex_count:'+old['name'])
        if [s.material.name if s.material else None for s in ob.material_slots]!=old['material_slots']:issues.append('material_order:'+old['name'])
        if ob.get('bank_asset_id')!=r['asset_id']:issues.append('identity:'+old['name'])
    # Only image nodes used by render-object materials affect the prepared visible asset.
    used_materials={s.material for o in meshes.values() if not o.hide_render for s in o.material_slots if s.material}
    used_images=set()
    for material in used_materials:
        if material.node_tree:
            for n in material.node_tree.nodes:
                if n.type=='TEX_IMAGE' and n.image and any(o.is_linked for o in n.outputs):used_images.add(n.image)
    missing=[]
    for im in used_images:
        if im.source=='FILE' and not im.packed_file and not pathlib.Path(bpy.path.abspath(im.filepath)).is_file():missing.append({'image':im.name,'path':bpy.path.abspath(im.filepath)})
    records.append({'asset_id':r['asset_id'],'prepared_blend':r['prepared_blend'],'file_sha256':hashlib.sha256(pathlib.Path(r['prepared_blend']).read_bytes()).hexdigest(),'reopened':True,'identity_geometry_counts_and_slot_order_preserved':not issues,'issues':issues,'linked_render_material_missing_images':missing})
(OUT/'BLENDER_REOPEN_READBACK.json').write_text(json.dumps(records,indent=2)+'\n')
print('BANK_REOPEN',json.dumps({'reopened':len(records),'with_issues':sum(bool(r['issues']) for r in records),'missing_linked_images':[(r['asset_id'],len(r['linked_render_material_missing_images'])) for r in records if r['linked_render_material_missing_images']]}))
