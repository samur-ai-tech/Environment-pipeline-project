"""Same-light/material read-only source/FBX appearance comparison."""
import sys, json, hashlib, re
from pathlib import Path
sys.dont_write_bytecode=True
import bpy, numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'Scripts'))
import build_strawberries_v005 as b
rec=json.loads((ROOT/'Reports/strawberries_v005.json').read_text())['assets'][0]
files=[ROOT/'Blend/StrawberryBeds.blend',ROOT/rec['fbx']]+sorted((ROOT/'Textures').glob('T_PazFarm_Strawberry_*_v005_*.png'))
def hashes():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=hashes();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blend/StrawberryBeds.blend'))
source=bpy.data.objects[rec['name']];materials={m.name:m for m in source.data.materials};existing=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(ROOT/rec['fbx']),use_custom_normals=True)
imported=[o for o in bpy.data.objects if o not in existing and o.type=='MESH'];assert len(imported)==1
fbx=imported[0];bindings=[]
for i,mat in enumerate(fbx.data.materials):
 name=re.sub(r'\.\d+$','',mat.name);assert name in materials,(name,list(materials));fbx.data.materials[i]=materials[name];bindings.append(name)
assert bindings==rec['material_slot_order']
focus=Vector(json.loads(sys.argv[sys.argv.index('--focus')+1])) if '--focus' in sys.argv else Vector((-.10,.74,.285))
def render(obj,label):
 s=bpy.context.scene;prior={o:o.hide_render for o in s.objects}
 for o in s.objects:o.hide_render=o!=obj
 tmp=[];floor=b.p.plain_mat('Normal_compare_ground',(.13,.104,.071));tmp.append(b.p.box('Normal_compare_ground',(0,2,-.025),(3000,3000,.05),floor))
 target=focus;eye=target+Vector((.48,-.64,.48));bpy.ops.object.camera_add(location=eye);camera=bpy.context.object;tmp.append(camera);camera.rotation_euler=(target-eye).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=.30;s.camera=camera
 bpy.ops.object.light_add(type='AREA',location=target+Vector((-3,-3,5)));light=bpy.context.object;tmp.append(light);light.data.energy=500;light.data.size=5;light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;tmp.append(sun);sun.rotation_euler=(.52,-.32,-.65);sun.data.energy=2.;sun.data.angle=.12
 s.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.63,.72,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.45
 s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.render.resolution_x=1400;s.render.resolution_y=1000;s.cycles.samples=64;s.cycles.seed=31911;s.cycles.use_animated_seed=False
 path=ROOT/'Previews'/('Strawberry_A_NormalCompare_'+label+'.png');s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 for o in tmp:bpy.data.objects.remove(o,do_unlink=True)
 for o,v in prior.items():o.hide_render=v
 return path
source_png=render(source,'Source');fbx_png=render(fbx,'FBX')
def pixels(path):
 im=bpy.data.images.load(str(path),check_existing=False);arr=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4)[:,:,:3]
 return np.where(arr<=.0031308,arr*12.92,1.055*np.power(np.maximum(arr,0),1/2.4)-.055)
aa=pixels(source_png);bb=pixels(fbx_png);difference=np.abs(aa-bb)*255;maximum=difference.max(axis=2);after=hashes()
heat=np.ones((*maximum.shape,4))*255;heat[:,:,:3]=np.stack((np.clip(maximum*8,0,255),np.zeros_like(maximum),np.zeros_like(maximum)),axis=-1)
heat_path=ROOT/'Previews/Strawberry_A_NormalCompare_Difference8x.png';b.png_bytes(heat_path,heat[::-1])
receipt={'passed_input_unchanged':before==after,'input_hashes_before':before,'input_hashes_after':after,'source_object':source.name,'fresh_FBX_object':fbx.name,'identical_material_names':bindings,'camera_target_m':list(focus),'camera_orthographic_scale_m':.30,'render_samples':64,'render_seed':31911,'measurement':'Absolute sRGB-byte RGB difference, computed from Blender-reloaded linear PNG pixels with standard linear-to-sRGB transfer. All pixels including ground are counted. Difference preview red is max-channel difference amplified 8x. No source/model/texture saves.','mean_abs_RGB_byte_difference':float(difference.mean()),'p95_max_channel_byte_difference':float(np.percentile(maximum,95)),'max_channel_byte_difference':float(maximum.max()),'pixels_max_channel_difference_above_2_bytes':int((maximum>2).sum()),'pixels_total':int(maximum.size),'fraction_pixels_above_2_bytes':float((maximum>2).mean()),'images':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (source_png,fbx_png,heat_path)},'interpretation':'Diagnostic comparison only; appearance similarity does not waive a confirmed incorrect normal.'}
(ROOT/'Reports/strawberries_v005_fbx_normal_comparison.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2),flush=True)
