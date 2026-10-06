"""Repair one retained derivative from an exact matching existing source variant."""
import bpy,json,pathlib,hashlib,numpy as np,math
from mathutils import Vector
from io_scene_fbx import parse_fbx,fbx_utils
OUT=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path('C:/Users/USER/Documents/Pipeline Environment/ModelBank/Prepared_2026-10-04')
def signature():
    h=hashlib.sha256()
    for ob in sorted((o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render),key=lambda o:o.name):
        me=ob.data;me.calc_loop_triangles();h.update(ob.name.encode());h.update(np.round(np.array(ob.matrix_world),7).tobytes())
        co=np.empty(len(me.vertices)*3,dtype=np.float64);me.vertices.foreach_get('co',co);h.update(np.round(co,7).tobytes())
        loops=np.empty(len(me.loops),dtype=np.int32);me.loops.foreach_get('vertex_index',loops);h.update(loops.tobytes())
        mi=np.empty(len(me.polygons),dtype=np.int32);me.polygons.foreach_get('material_index',mi);h.update(mi.tobytes())
        for uv in me.uv_layers:
            a=np.empty(len(uv.data)*2,dtype=np.float64);uv.data.foreach_get('uv',a);h.update(np.round(a,7).tobytes())
    return h.hexdigest()
fingerprints=[]
for file in sorted(ROOT.glob('*/ASSET.json')):
    r=json.loads(file.read_text());bpy.ops.wm.open_mainfile(filepath=r['prepared_blend'],load_ui=False,use_scripts=False)
    digest=signature();r['render_geometry_uv_slotindex_sha256']=digest;file.write_text(json.dumps(r,indent=2)+'\n')
    fingerprints.append({'asset_id':r['asset_id'],'geometry_uv_slotindex_sha256':digest})
(OUT/'SOURCE_GEOMETRY_FINGERPRINTS.json').write_text(json.dumps(fingerprints,indent=2)+'\n')
byid={r['asset_id']:r['geometry_uv_slotindex_sha256'] for r in fingerprints}
assert byid['external.H0633']==byid['external.T1157'],'donor_geometry_UV_or_material_face_assignment_not_exact'
targetfile=ROOT/'external_H0633/ASSET.json';target=json.loads(targetfile.read_text());donor=json.loads((ROOT/'external_T1157/ASSET.json').read_text())
report_a=json.loads(pathlib.Path(target['source_report']).read_text());report_b=json.loads(pathlib.Path(donor['source_report']).read_text())
assert report_a['source']==report_b['source'],'original_source_identity_differs'
bpy.ops.wm.open_mainfile(filepath=target['prepared_blend'],load_ui=False,use_scripts=False)
oldnames={slot.material.name for o in bpy.context.scene.objects if o.type=='MESH' for slot in o.material_slots if slot.material}
with bpy.data.libraries.load(donor['prepared_blend'],link=False) as (src,dst):
    assert oldnames.issubset(set(src.materials))
    ordered=tuple(sorted(oldnames));dst.materials=list(ordered)
mapping=dict(zip(ordered,dst.materials))
for ob in bpy.context.scene.objects:
    if ob.type!='MESH':continue
    for slot in ob.material_slots:
        if slot.material:
            key=slot.material.name;slot.material=mapping[key]
    ob['bank_material_donor']='external.T1157'
    ob['bank_material_repair']='exact_source_geometry_UV_slotindex_match_material_only'
for im in bpy.data.images:
    if im.source=='FILE':
        path=pathlib.Path(bpy.path.abspath(im.filepath))
        if not path.is_file():
            matches={x['path'] for x in donor['texture_references'] if pathlib.Path(x['path']).name==path.name and x['exists']}
            if len(matches)==1:path=pathlib.Path(next(iter(matches)))
        if path.is_file():im.filepath=str(path)
used={s.material for o in bpy.context.scene.objects if o.type=='MESH' for s in o.material_slots if s.material}
missing=[]
for mat in used:
    for node in mat.node_tree.nodes if mat.node_tree else []:
        if node.type=='TEX_IMAGE' and node.image and any(o.is_linked for o in node.outputs):
            im=node.image
            if not im.packed_file and not pathlib.Path(bpy.path.abspath(im.filepath)).is_file():missing.append(im.name)
assert not missing,missing
assert signature()==byid['external.H0633'],'geometry_changed'
folder=targetfile.parent;resolved=folder/'MaterialResolved.blend';bpy.ops.wm.save_as_mainfile(filepath=str(resolved),check_existing=False)
# Match the source FBX orientation metadata using the installed exporter's table.
root,version=parse_fbx.parse(target['source_fbx'])
settings=next(e for e in root.elems if e.id==b'GlobalSettings');props=next(e for e in settings.elems if e.id==b'Properties70')
values={e.props[0].decode():e.props[-1] for e in props.elems if e.id==b'P'}
axes=tuple((values[k+'Axis'],values[k+'AxisSign']) for k in ('Up','Front','Coord'))
matches=[k for k,v in fbx_utils.RIGHT_HAND_AXES.items() if tuple(v)==axes];assert len(matches)==1
up,forward=matches[0]
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.context.scene.objects:
    if ob.type=='MESH':ob.select_set(True)
export=folder/'MaterialResolved.fbx'
bpy.ops.export_scene.fbx(filepath=str(export),use_selection=True,object_types={'MESH'},axis_up=up,axis_forward=forward,
    global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_mesh_modifiers=True,
    mesh_smooth_type='OFF',bake_anim=False,path_mode='ABSOLUTE',add_leaf_bones=False)
repair={'asset_id':'external.H0633','donor_asset_id':'external.T1157','original_source_identity':report_a['source'],
    'exact_geometry_uv_slotindex_sha256':byid['external.H0633'],'geometry_edited':False,'material_references_repaired':True,
    'original_source_files_unchanged':True,'prepared_blend':str(resolved),'prepared_fbx':str(export),
    'source_fbx_axes':{k:values[k] for k in ['UpAxis','UpAxisSign','FrontAxis','FrontAxisSign','CoordAxis','CoordAxisSign','UnitScaleFactor']},'export_axis_up':up,'export_axis_forward':forward,
    'linked_render_material_missing_images':missing,'native_imported':False,'enabled':False,
    'material_slot_mapping':{k:v.name for k,v in mapping.items()},'rights_state_preserved':target['rights_state']}
(folder/'MATERIAL_REPAIR.json').write_text(json.dumps(repair,indent=2)+'\n');(OUT/'MATERIAL_REPAIR.json').write_text(json.dumps(repair,indent=2)+'\n')
print('BANK_MATERIAL_REPAIR',json.dumps(repair))
