import bpy,json,pathlib,numpy as np,math
from mathutils import Vector
OUT=pathlib.Path(__file__).resolve().parent
r=json.loads((OUT/'MATERIAL_REPAIR.json').read_text());folder=pathlib.Path(r['prepared_blend']).parent
base=json.loads((folder/'ASSET.json').read_text())
def bounds():
    coords=[]
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':continue
        a=np.array([tuple(ob.matrix_world@v.co) for v in ob.data.vertices])*bpy.context.scene.unit_settings.scale_length
        coords.extend(a)
    a=np.array(coords);return a.min(axis=0),a.max(axis=0)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.unit_settings.scale_length=1
bpy.ops.import_scene.fbx(filepath=r['prepared_fbx'],use_manual_orientation=False,global_scale=1,use_custom_normals=True,use_image_search=False,use_anim=False)
lo,hi=bounds();error=max(np.max(np.abs(lo-np.array(base['bounds_m']['min']))),np.max(np.abs(hi-np.array(base['bounds_m']['max']))))
assert error<0.0001,('export_dimensions_changed',error)
bpy.ops.wm.open_mainfile(filepath=r['prepared_blend'],load_ui=False,use_scripts=False)
scene=bpy.context.scene;lo,hi=bounds();center=Vector(((lo+hi)/2).tolist());extent=float(max(hi-lo))
camdata=bpy.data.cameras.new('PreparationPreview');cam=bpy.data.objects.new('PreparationPreview',camdata);scene.collection.objects.link(cam)
cam.location=center+Vector((1.25,-1.6,0.75))*extent;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=extent*1.25;camdata.clip_end=extent*20;scene.camera=cam
if scene.world is None:scene.world=bpy.data.worlds.new('PreparationStudio')
scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(0.12,0.14,0.18,1);scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=0.5
for name,rot,power in [('Key',(25,-35,-30),3),('Fill',(50,20,130),1.2)]:
    data=bpy.data.lights.new(name,'SUN');data.energy=power;ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.rotation_euler=tuple(math.radians(v) for v in rot)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(folder/'MaterialPreview.png');bpy.ops.render.render(write_still=True)
r.update(blender_fbx_reimport_bounds_error_m=float(error),prepared_blend_reopened=True,material_preview=scene.render.filepath,native_unreal_validation=False)
(folder/'MATERIAL_REPAIR.json').write_text(json.dumps(r,indent=2)+'\n');(OUT/'MATERIAL_REPAIR.json').write_text(json.dumps(r,indent=2)+'\n');print('REPAIR_READBACK',error)
