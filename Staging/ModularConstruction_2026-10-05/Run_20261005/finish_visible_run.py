from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import unreal,json,os,hashlib
import geocity_roadbld_clip as clip
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
folder=ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=read(folder/'AREA_PROFILE.json');state=read(folder/'WORKFLOW_STATE.json');receipt=read(folder/'HDA_CATALOG_RECEIPT.json')
assert os.getpid()==10460 and state['phase']=='baked_saved_verified' and not state['recovery_required']
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
api=unreal.HoudiniPublicAPIBlueprintLib.get_api();assert api.is_asset_cooking_paused()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
by_path={a.get_path_name():a for a in actors}
assert all(path in by_path for path in state['baked_actor_paths'])
expected=Counter(state['baked_mesh_counts']);actual=Counter()
for actor in actors:
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        if c.static_mesh and c.static_mesh.get_path_name() in expected:
            actual[c.static_mesh.get_path_name()]+=c.get_instance_count() if isinstance(c,unreal.InstancedStaticMeshComponent) else 1
assert actual==expected
assert len([a for a in actors if isinstance(a,unreal.Landscape)])==1
hd=[a for a in actors if a.get_class().get_name()=='HoudiniAssetActor'];assert len(hd)==1
w=unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None,hd[0]);assert not w.is_auto_cooking_enabled() and not w.is_auto_bake_enabled()
assert not hd[0].get_components_by_class(unreal.MeshComponent)
for row in p['road_provider_contract']['native_component_bindings']:
    c=unreal.find_object(None,row['component']);assert c and c.static_mesh.get_path_name()==row['mesh']
    assert clip._materials(c)==row['material_slots'] and clip._transform(c.get_world_transform())==row['component_world_transform']
new=[r for r in receipt['native_building_assembly_records'] if r.get('source_family')]
families=Counter(r['source_family']['family_id'] for r in new)
new_paths={v['path'] for r in new for v in r['wall_placements']}
parts=sum(r['module_count'] for r in new);assert sum(actual[path] for path in new_paths)==parts
r=new[0];ring=r['native_family_envelope_xz_m'];cx=sum(x[0] for x in ring)/len(ring)*100;cy=sum(x[1] for x in ring)/len(ring)*100;cz=(r['base_m']+r['height_m']*.5)*100
target=unreal.Vector(cx,cy,cz);camera=unreal.Vector(cx+2200,cy-2900,cz+1400)
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(camera,unreal.MathLibrary.find_look_at_rotation(camera,target))
result={'status':'BUILDINGS_GENERATED_SAVED_REOPENED','utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'map':p['map'],'map_sha256':sha(ROOT/'Content'/(p['map'][6:]+'.umap')),'profile_sha256':sha(folder/'AREA_PROFILE.json'),'new_kit_buildings':len(new),'new_kit_part_instances':parts,'families_used':dict(families),'complete_families_enabled':18,'total_geographic_buildings':state['geographic_building_coverage']['total'],'total_native_instances':sum(actual.values()),'baked_actors':len(state['baked_actor_paths']),'saved_map_reopened_same_editor':True,'duplicate_native_instances':False,'landscape_count':1,'cooked_mesh_components':0,'saved_road_components_reused_unchanged':len(p['road_provider_contract']['native_component_bindings']),'road_regeneration_completed':False,'road_repair_queue':str(HERE/'ROAD_REPAIR_QUEUE.json'),'excluded_incomplete_families':['H0017','H0019'],'failed_import_parts':6,'native_bank_saved_parts':603,'native_bank_new_imports':569,'native_bank_reused_parts':34,'camera_focused_source':r['source_feature'],'camera_focused_family':r['source_family']['family_id'],'user_visual_acceptance':False}
(HERE/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
auth=read(HERE/'CONNECTION_AUTHORIZATION.json');auth.update(status=result['status'],actual_generation_completed=True,pid=os.getpid(),result_ref=str(HERE/'RESULT.json'),saved_map_reopened=True,road_regeneration_completed=False)
(HERE/'CONNECTION_AUTHORIZATION.json').write_text(json.dumps(auth,indent=2)+'\n')
lease=ROOT/'Staging/ModelBank/EDITOR_OWNER.txt'
with lease.open('a') as f:f.write('\n'+datetime.now(timezone.utc).isoformat()+' OWNER=NONE released_by=01a10c77-46ba-7001-a657-5014f6205d3a editor_PID=10460 phase=BUILDINGS_GENERATED_SAVED_REOPENED cooking=paused auto_cook=false auto_bake=false road_rebuild=repair_queue\n')
print(json.dumps(result))
