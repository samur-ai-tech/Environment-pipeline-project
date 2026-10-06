"""Measure actual saved Landscape collision under retained native buildings."""
import unreal
import json
from pathlib import Path

PROJECT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
world_path=world.get_outermost().get_path_name()
profiles=[p for p in (PROJECT/'Staging/ModelBank').rglob('AREA_PROFILE.json') if json.loads(p.read_text())['map']==world_path]
assert len(profiles)==1
profile=json.loads(profiles[0].read_text())
assert json.loads(Path(profile['workflow_receipt']).read_text())['phase']=='baked_saved_verified'
receipt=json.loads(Path(profile['catalog_receipt']).read_text())
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
ignored=[a for a in actors if not isinstance(a,unreal.LandscapeProxy)]
whole=[r for r in receipt['nonbuilding_instances'] if r['role']=='whole_building']
selected=[]
observed=[r for r in whole if r['placement_id'].endswith(':building_299407939')]
selected.extend(observed)
for r in sorted(whole,key=lambda x:x['placement_id']):
    if r not in selected:selected.append(r)
    if len(selected)>=4:break
measurements=[]
for record in selected:
    base=record['ground_contact_y_m']*100
    for x,z in record['footprint_xz_m']:
        low,high=base-300,base+300
        for _ in range(18):
            middle=(low+high)/2
            hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x*100,z*100,middle),unreal.Vector(x*100,z*100,base-500),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,ignored,unreal.DrawDebugTrace.NONE,False)
            if hit is None:low=middle
            else:high=middle
        delta=base-(low+high)/2
        assert abs(delta)<3.0,(record['placement_id'],delta)
        measurements.append({'placement_id':record['placement_id'],'x_cm':x*100,'y_cm':z*100,'native_base_cm':base,'landscape_collision_cm_interval':[low,high],'base_minus_ground_cm':delta})
area=json.loads(Path(profile['source']).read_text())['area_id']
result={'area':area,'method':'Only Landscape collision; all other actors ignored; 18-step downward trace height interval','comparison':'native bbox support plane, not individual foundation vertices','maximum_absolute_support_error_cm':max(abs(r['base_minus_ground_cm']) for r in measurements),'sampled_native_buildings':len(selected),'samples':measurements}
target=PROJECT/'Staging/RepairExecution_2026-10-03'/('COLLISION_'+area+'.json')
target.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'area':area,'sampled_buildings':len(selected),'max_support_error_cm':result['maximum_absolute_support_error_cm']}))
