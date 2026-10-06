"""Export two existing prepared meshes with explicit source triangulation."""
import bpy,json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
jobs={j['asset_id']:j for j in json.loads((HERE/'EXTERNAL_IMPORT_QUEUE.json').read_text())}
out={};folder=HERE/'PreparedExports';folder.mkdir(exist_ok=True)
for aid in ['external.H0045','external.H0056']:
    job=jobs[aid];source=Path(job['prepared_blend']);before=hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
    assert len(meshes)==1
    original=meshes[0];mesh=original.data;mesh.calc_loop_triangles()
    triangles=list(mesh.loop_triangles)
    tri_mesh=bpy.data.meshes.new(original.name+'_ExplicitSourceTriangles')
    tri_mesh.from_pydata([v.co[:] for v in mesh.vertices],[],[tuple(t.vertices) for t in triangles])
    for material in mesh.materials:tri_mesh.materials.append(material)
    original_loops=[loop for t in triangles for loop in t.loops]
    for index,triangle in enumerate(triangles):
        tri_mesh.polygons[index].material_index=triangle.material_index
        tri_mesh.polygons[index].use_smooth=mesh.polygons[triangle.polygon_index].use_smooth
    for layer in mesh.uv_layers:
        new_layer=tri_mesh.uv_layers.new(name=layer.name)
        for index,old_index in enumerate(original_loops):new_layer.data[index].uv=layer.data[old_index].uv
    for layer in mesh.color_attributes:
        if layer.domain not in {'POINT','CORNER'}:continue
        new_layer=tri_mesh.color_attributes.new(name=layer.name,type=layer.data_type,domain=layer.domain)
        indices=range(len(mesh.vertices)) if layer.domain=='POINT' else original_loops
        for index,old_index in enumerate(indices):new_layer.data[index].color=layer.data[old_index].color
    tri_mesh.normals_split_custom_set([mesh.corner_normals[i].vector[:] for i in original_loops])
    derived=original.copy();derived.data=tri_mesh;bpy.context.collection.objects.link(derived)
    bpy.ops.object.select_all(action='DESELECT')
    derived.select_set(True);bpy.context.view_layer.objects.active=derived
    target=folder/(aid.replace('.','_')+'_ExplicitTriangles.fbx')
    bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={'MESH'},use_mesh_modifiers=False,
        mesh_smooth_type='FACE',use_triangles=False,use_tspace=True,add_leaf_bones=False,bake_anim=False,
        axis_forward='-Z',axis_up='Y',apply_unit_scale=True,global_scale=1.0)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before
    out[aid]={'fbx':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'prepared_blend':str(source),'prepared_blend_sha256':before,
        'reason':'Export exact prepared loop-triangle indices with unchanged vertex positions, per-corner UVs, normals, colors and material indices; avoid exporter retriangulation of nonplanar faces.',
        'geometry_remodeled':False,'source_files_changed':False,'native_equivalence_pending':True}
(HERE/'IMPORT_SOURCE_OVERRIDES.json').write_text(json.dumps(out,indent=2)+'\n')
print('Two prepared-source triangulation exports saved; source files unchanged')
