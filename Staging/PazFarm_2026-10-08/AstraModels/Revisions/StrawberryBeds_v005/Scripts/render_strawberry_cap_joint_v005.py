"""Read-only final FBX joined cap close view using original source PBR."""
import sys,json,re,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'Scripts'))
import build_strawberries_v005 as b
records=json.loads((ROOT/'Reports/strawberries_v005.json').read_text())['assets'];selected=[r for r in records if r['name'] in ('SM_PazFarm_StrawberryBed_4m_A','SM_PazFarm_StrawberryBedEnd')]
files=[ROOT/'Blend/StrawberryBeds.blend']+[ROOT/r['fbx'] for r in selected]+sorted((ROOT/'Textures').glob('T_PazFarm_Strawberry_*_v005_*.png'))
def hashes():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=hashes();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blend/StrawberryBeds.blend'));materials={m.name:m for m in bpy.data.objects[selected[0]['name']].data.materials}
for o in bpy.data.objects:o.hide_render=True
objects=[]
for rec in selected:
 old=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(ROOT/rec['fbx']),use_custom_normals=True);obs=[o for o in bpy.data.objects if o not in old and o.type=='MESH'];assert len(obs)==1;ob=obs[0]
 for i,mat in enumerate(ob.data.materials):ob.data.materials[i]=materials[re.sub(r'\.\d+$','',mat.name)]
 ob.hide_render=False;ob.location=(0,4 if rec['variant']=='End' else 0,0);objects.append(ob)
s=bpy.context.scene;floor=b.p.plain_mat('Cap_joint_ground',(.13,.104,.071));b.p.box('Cap_joint_ground',(0,2,-.025),(3000,3000,.05),floor)
target=Vector((0,3.96,.19));eye=target+Vector((1.30,-1.65,.90));bpy.ops.object.camera_add(location=eye);cam=bpy.context.object;cam.rotation_euler=(target-eye).to_track_quat('-Z','Y').to_euler();cam.data.type='PERSP';cam.data.lens=50;cam.data.sensor_width=36;s.camera=cam
bpy.ops.object.light_add(type='AREA',location=target+Vector((-3,-3,5)));light=bpy.context.object;light.data.energy=500;light.data.size=5;light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.rotation_euler=(.52,-.32,-.65);sun.data.energy=2.;sun.data.angle=.12
s.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.63,.72,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.45;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.render.resolution_x=1600;s.render.resolution_y=1100;s.cycles.samples=64;s.cycles.seed=31911;s.cycles.use_animated_seed=False
path=ROOT/'Previews/Strawberry_A_EndCap_FBX_JoinedClose.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);after=hashes()
receipt={'passed_input_unchanged':before==after,'input_hashes_before':before,'input_hashes_after':after,'objects':[{'source_asset':r['name'],'world_location_m':list(o.location),'rebound_material_slots':[m.name for m in o.data.materials]} for r,o in zip(selected,objects)],'camera_target_m':list(target),'camera_eye_m':list(eye),'camera_distance_to_target_m':(eye-target).length,'camera_focal_length_mm':50,'render_samples':64,'inspection_purpose':'Inspect the final fresh-FBX A-to-cap seam including UV phase under the original source PBR materials. Ground at Z=0 hides the intended buried skirt. No native verification.','images':{path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()}}
(ROOT/'Reports/strawberries_v005_cap_joint_close.json').write_text(json.dumps(receipt,indent=2)+'\n');print('FBX_CAP_JOINT_COMPLETE',json.dumps(receipt,indent=2),flush=True)
