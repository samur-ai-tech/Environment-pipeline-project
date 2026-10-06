"""Blender read-only inspection of prepared assets; native import recipes and renders."""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
jobs=json.loads((HERE/'EXTERNAL_IMPORT_QUEUE.json').read_text())
out=HERE/'SourceReview';out.mkdir(exist_ok=True)
recipes=[]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def val(socket):
    value=socket.default_value
    try:return list(value)
    except TypeError:return value

for job in jobs:
    aid=job['asset_id'];path=Path(job['prepared_blend']);before=sha(path)
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
    rec=json.loads(Path(job['original_source_receipt']).read_text())
    render=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
    assert len(render)==1,(aid,len(render))
    materials=[]
    for i,slot in enumerate(render[0].material_slots):
        mat=slot.material;assert mat is not None
        nodes=list(mat.node_tree.nodes) if mat.node_tree else []
        principled=[n for n in nodes if n.type=='BSDF_PRINCIPLED'];assert len(principled)==1,(aid,mat.name)
        bsdf=principled[0]
        inputs={n:{'default':val(bsdf.inputs[n]),'links':[{'node':l.from_node.name,'type':l.from_node.type,'output':l.from_socket.name} for l in bsdf.inputs[n].links]} for n in ['Base Color','Metallic','Roughness','Alpha','Normal','Emission Color','Emission Strength']}
        images=[]
        for n in nodes:
            if n.type=='TEX_IMAGE' and n.image and any(s.is_linked for s in n.outputs):
                image=Path(bpy.path.abspath(n.image.filepath));assert image.is_file(),(aid,str(image))
                images.append({'node':n.name,'path':str(image),'sha256':sha(image),'colorspace':n.image.colorspace_settings.name,'outputs':[{'socket':s.name,'destinations':[l.to_node.name+'.'+l.to_socket.name for l in s.links]} for s in n.outputs if s.is_linked]})
        materials.append({'slot':i,'source_material':job['material_mapping_by_source_object'][0]['material_slots'][i],
            'prepared_material_name':mat.name,'backface_culling':mat.use_backface_culling,'diffuse_color':list(mat.diffuse_color),
            'principled_inputs':inputs,'linked_images':images,
            'normal_basis':'Prepared Blender Normal Map shader; Unreal texture green inversion must be verified against native lit view.'})
    # Render the actual prepared material; no source changes are saved.
    scene=bpy.context.scene;scale=scene.unit_settings.scale_length
    low=Vector(rec['bounds_m']['min'])/scale;high=Vector(rec['bounds_m']['max'])/scale
    center=(low+high)/2;extent=max(high-low)
    for ob in scene.objects:
        if ob.type!='MESH':ob.hide_render=True
    camdata=bpy.data.cameras.new('BankReviewCamera');cam=bpy.data.objects.new('BankReviewCamera',camdata);scene.collection.objects.link(cam)
    cam.location=center+Vector((1.4,-1.8,1.0))*extent
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    camdata.type='ORTHO';camdata.ortho_scale=extent*1.6;camdata.clip_start=max(0.00001,extent/10000);camdata.clip_end=max(100,extent*20)
    scene.camera=cam
    for name,offset,power,size in [('Key',(2,-3,4),1000,4),('Fill',(-2,1,2),650,3)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power*extent*extent;data.shape='DISK';data.size=size*extent
        ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=center+Vector(offset)*extent
        ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
    if scene.world is None:scene.world=bpy.data.worlds.new('BankReviewWorld')
    scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(0.14,0.16,0.19,1)
    scene.world.node_tree.nodes.get('Background').inputs[1].default_value=0.6
    scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
    # Dense crossed foliage cards need more transparent ray depth in source review.
    scene.cycles.transparent_max_bounces=64
    scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.render.filepath=str(out/(aid.replace('.','_')+'.png'))
    bpy.ops.render.render(write_still=True)
    assert before==sha(path),'prepared_source_changed'
    recipes.append({'asset_id':aid,'prepared_blend':str(path),'prepared_blend_sha256':before,'source_material_render':scene.render.filepath,
        'render_kind':'actual_prepared_Blender_material_not_native_Unreal_acceptance','materials':materials,
        'source_preserved':True,'native_imported':False})
    (HERE/'EXTERNAL_MATERIAL_RECIPES.json').write_text(json.dumps(recipes,indent=2)+'\n')
    print('MATERIAL_REVIEW',aid,flush=True)
