"""Continue the exact root-owned failed native transaction; keep all identities."""
import copy, datetime, importlib, json, time
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_junctions as corners

HERE=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03')
p=bank.ACTIVE[-1];r=native.ACTIVE[-1]
p.guard();p.guard_processes();r.guard()
assert not p.watch_tick and not p.save_tick and not r.tick_handle
assert p.state['phase']=='failed_native_road_transaction' and r.state['phase']=='failed_rebuilding'
assert p.api.is_asset_cooking_paused() and not r.network.is_road_network_stale()
assert len(r.derived_junction_roads)==6 and len(r.roads)==r.plan['source_piece_count']
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
(HERE/('NATIVE_SHORT_LEADS_BEFORE_'+stamp+'.json')).write_text(json.dumps({'official':p.state,'native':r.state},indent=2),encoding='utf-8')
importlib.reload(corners)
report=copy.deepcopy(r.junction_repair)
proofs=report['sourcecontrols_trimproof']
for proof in proofs.values():
 original=proof['original_control_points_world_cm']
 proof.update(expected_control_points_world_cm=copy.deepcopy(original),retained_export_point_indices=list(range(len(original))),
              expected_point_turn_radii_cm=list(proof['original_point_turn_radii_cm']),
              removed_generated_sample_export_indices=[],consumed_original_vertices_inside_trim=[],end_trims=[])
tasks=[]
for record in report['derived_junction_roads']:
 pa,pb=record['parent_road_actor_paths'];qa,qb=proofs[pa],proofs[pb]
 sa,sb=[v['start'] for v in record['native_endpoint_trims']]
 prepared=corners._prepare_pair(qa['expected_control_points_world_cm'],qa['retained_export_point_indices'],set(qa['protected_indices']),sa,
                               qb['expected_control_points_world_cm'],qb['retained_export_point_indices'],set(qb['protected_indices']),sb,
                               radius_cm=record['turn_radius_cm'])
 trims=[]
 for proof,start,suffix,partner in ((qa,sa,'a',pb),(qb,sb,'b',pa)):
  original_end=list(proof['expected_control_points_world_cm'][0 if start else -1])
  removed=prepared['removed_'+suffix]
  for index in removed:
   key='consumed_original_vertices_inside_trim' if index in proof['protected_indices'] else 'removed_generated_sample_export_indices'
   proof[key].append(index)
  proof['expected_control_points_world_cm']=prepared['expected_'+suffix]
  proof['retained_export_point_indices']=prepared['mapping_'+suffix]
  proof['expected_point_turn_radii_cm']=[proof['original_point_turn_radii_cm'][i] for i in prepared['mapping_'+suffix]]
  trim={'start':start,'source_endpoint_world_cm':original_end,
        'native_endpoint_world_cm':prepared['connector_controls'][0 if suffix=='a' else -1],
        'pullback_cm':prepared['pullback_cm'],'turn_radius_cm':prepared['turn_radius_cm'],
        'removed_export_indices':removed,'partner_actor_path':partner}
  proof['end_trims'].append(trim);trims.append(trim)
 record.update(control_points_world_cm=prepared['connector_controls'],control_points_sha256=corners._sha(prepared['connector_controls']),
               native_endpoint_trims=trims,turn_angle_deg=prepared['turn_angle_deg'],arc_tangent_pullback_cm=prepared['arc_tangent_pullback_cm'])
 tasks.append((record,sa,sb))
for proof in proofs.values():proof['expected_controls_sha256']=corners._sha(proof['expected_control_points_world_cm'])
(HERE/('NATIVE_EXTENDED_LEADS_PREFLIGHT_'+stamp+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
by_path={a.get_path_name():a for a in r.roads+r.derived_junction_roads}
for road,row in zip(r.roads,r.plan['roads']):
 proof=proofs[road.get_path_name()]
 corners._set_points(r,road,proof['expected_control_points_world_cm'],proof['expected_point_turn_radii_cm'])
for record,sa,sb in tasks:
 connector=by_path[record['road_actor_path']]
 corners._set_points(r,connector,record['control_points_world_cm'],record['point_turn_radii_cm'])
 for parent_path,parent_start,connector_start in ((record['parent_road_actor_paths'][0],sa,True),(record['parent_road_actor_paths'][1],sb,False)):
  a,b=unreal.RoadBLDEndpointRef(),unreal.RoadBLDEndpointRef()
  native._set(a,'Road',connector);native._set(a,'bStart',connector_start)
  native._set(b,'Road',by_path[parent_path]);native._set(b,'bStart',parent_start)
  result=native._tool('RoadBLDAuthoringToolset','ConnectEndpoints',a,b,unreal.RoadBLDConnectMode.LINK,None,0.1,record['turn_radius_cm'],False)
  assert str(native._get(native._get(result,'Network'),'RefPath'))==native._path(r.network)
r.junction_repair=report;r.state['junction_repair_report']=report
for road,row in zip(r.roads,r.plan['roads']):corners.verify_source_road(r,road,row,report)
corners.verify_derived_roads(r,report)
report.update(phase='extended_native_corner_leads_pending_rebuild',endpoint_trim_cm=150.0)
r.state.pop('error',None);r.clipping_report=None;r.request_rebuild()
p.native_road_run=r;p.native_road_phase='authoring';p.started_epoch=time.time()
p.state.update(phase='native_road_authoring',recovery='Exact retained native connectors extended along geographic leads; all actor identities preserved')
p.state.pop('error',None);p.write();r.write()
p.wrapper.on_post_cook_delegate.add_callable(p.after_cook)
p.wrapper.on_post_processing_delegate.add_callable(p.after_processing)
p.watch_tick=unreal.register_slate_post_tick_callback(p.watch)
r.tick_handle=unreal.register_slate_post_tick_callback(r.tick)
print(json.dumps({'phase':p.state['phase'],'native_phase':r.state['phase'],'source_roads':len(r.roads),'derived':len(r.derived_junction_roads),
                  'rebuild_pass':r.rebuild_pass,'rebuild_job':r.job_id,'source_recreation':False}))
