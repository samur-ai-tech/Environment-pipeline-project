"""Retained material-only corrections for two existing native building candidates."""
import bpy
import hashlib
import json
from pathlib import Path
import numpy as np
from mathutils import Vector

HERE=Path(__file__).resolve().parent
ARCHIVE=Path('C:/Users/USER/Documents/Unreal Projects/GIS_WorldBLD/SourceData/ModelBanks_Archive/Unreal_Model_Library_2026-09-24/Sources/Hergel')
DEST=Path('C:/Users/USER/Documents/Pipeline Environment/ModelBank/Prepared_2026-10-04/NativeMaterialCorrections')

def signature():
    h=hashlib.sha256()
    for ob in sorted((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:o.name):
        mesh=ob.data;h.update(ob.name.encode());h.update(np.asarray(ob.matrix_world,dtype=np.float64).tobytes())
        for collection,field,dtype,size in [(mesh.vertices,'co',np.float64,3),(mesh.loops,'vertex_index',np.int32,1),(mesh.polygons,'material_index',np.int32,1)]:
            values=np.empty(len(collection)*size,dtype=dtype);collection.foreach_get(field,values);h.update(values.tobytes())
        for layer in mesh.uv_layers:
            values=np.empty(len(layer.data)*2,dtype=np.float64);layer.data.foreach_get('uv',values);h.update(values.tobytes())
    return h.hexdigest()

def render(folder,name):
    scene=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get();points=[]
    for ob in scene.objects:
        if ob.type=='MESH' and not ob.hide_render:points.extend(ob.matrix_world@Vector(c) for c in ob.bound_box)
    low=Vector([min(p[i] for p in points) for i in range(3)]);high=Vector([max(p[i] for p in points) for i in range(3)])
    center=(low+high)/2;extent=max(high-low)
    camdata=bpy.data.cameras.new('MaterialReviewCamera');cam=bpy.data.objects.new('MaterialReviewCamera',camdata);scene.collection.objects.link(cam)
    cam.location=center+Vector((1.4,-1.8,1.1))*extent;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    camdata.type='ORTHO';camdata.ortho_scale=extent*1.55;camdata.clip_end=max(100,extent*30);camdata.clip_start=max(0.00001,extent/10000);scene.camera=cam
    for n,offset,energy in [('Key',(1,-2,4),1300),('Fill',(-2,1,2),500)]:
        data=bpy.data.lights.new(n,'AREA');data.energy=energy*extent*extent;data.size=4*extent
        ob=bpy.data.objects.new(n,data);scene.collection.objects.link(ob);ob.location=center+Vector(offset)*extent;ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
    if scene.world is None:scene.world=bpy.data.worlds.new('MaterialReviewWorld')
    scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(0.16,0.18,0.21,1);scene.world.node_tree.nodes.get('Background').inputs[1].default_value=0.5
    scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
    scene.render.resolution_x=1000;scene.render.resolution_y=850;scene.render.resolution_percentage=100
    scene.render.filepath=str(folder/(name+'.png'));scene.render.image_settings.file_format='PNG';bpy.ops.render.render(write_still=True)
    for ob in list(scene.objects):
        if ob.type in {'CAMERA','LIGHT'}:bpy.data.objects.remove(ob,do_unlink=True)
    return scene.render.filepath

results=[]
for num in ['0902','0016']:
    report=json.loads((ARCHIVE/'Reports'/(num+'.json')).read_text());source=ARCHIVE/report['blend'];original_sha=hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    geometry=signature();folder=DEST/('H'+num);folder.mkdir(parents=True,exist_ok=True)
    refs={Path(value['file']).name:ARCHIVE/value['file'] for maps in report['material_maps'].values() for value in maps.values() if isinstance(value,dict) and value.get('file')}
    for im in bpy.data.images:
        if im.source=='FILE':
            path=Path(bpy.path.abspath(im.filepath))
            if not path.is_file() and path.name in refs:path=refs[path.name]
            if path.is_file():im.filepath=str(path)
    used={s.material for o in bpy.context.scene.objects if o.type=='MESH' for s in o.material_slots if s.material}
    changes=[]
    for mat in used:
        if not mat.node_tree:continue
        nodes=list(mat.node_tree.nodes)
        for bsdf in [n for n in nodes if n.type=='BSDF_PRINCIPLED']:
            for link in list(bsdf.inputs['Normal'].links):
                normal=link.from_node
                if normal.type!='NORMAL_MAP':continue
                texlinks=list(normal.inputs['Color'].links)
                if not texlinks or texlinks[0].from_node.type!='TEX_IMAGE':continue
                tex=texlinks[0].from_node
                if tex.image and Path(bpy.path.abspath(tex.image.filepath)).name=='T_CracksStreet_normal_076f5fec4437.png':
                    changes.append({'material':mat.name,'removed_normal_file':str(refs['T_CracksStreet_normal_076f5fec4437.png']),
                        'correction':'Disconnect unrelated street-crack normal from building surface; preserve base color and all remaining texture/scalar inputs. Native derivative will use neutral tangent normal (0,0,1).',
                        'reconnect_nodes':[normal.name,bsdf.name]})
                    mat.node_tree.links.remove(link)
    assert changes,'no_exact_crack_normal_binding_found'
    assert signature()==geometry,'geometry_or_uv_changed'
    blend=folder/'MaterialResolved.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend),check_existing=False)
    preview=render(folder,'MaterialResolved')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==original_sha
    bpy.ops.wm.open_mainfile(filepath=str(blend),load_ui=False,use_scripts=False)
    assert signature()==geometry,'reopened_geometry_or_uv_changed'
    receipt={'native_catalog_asset_id':'current_Project__Shared__Bank_ME_v3__Buildings__SM_H'+num+('_Slum_k_fbx' if num=='0902' else '_Building_03'),
        'original_blend':str(source),'original_blend_sha256':original_sha,'source_report':str(ARCHIVE/'Reports'/(num+'.json')),
        'prepared_blend':str(blend),'prepared_blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),
        'geometry_uv_slotindex_sha256':geometry,'geometry_uv_material_slot_faces_unchanged':True,'reopened_verified':True,
        'material_changes':changes,'source_material_preview':preview,'native_material_applied':False,'enabled':False,
        'reason':'Historical native pixels showed unrelated street-crack relief over complete building facade; exact source graph identifies the incorrect normal binding. No replacement texture is guessed.'}
    (folder/'MATERIAL_CORRECTION.json').write_text(json.dumps(receipt,indent=2)+'\n');results.append(receipt)
    (HERE/'BUILDING_MATERIAL_CORRECTIONS.json').write_text(json.dumps(results,indent=2)+'\n')
    print('BUILDING_MATERIAL_CORRECTED',num,len(changes),flush=True)
