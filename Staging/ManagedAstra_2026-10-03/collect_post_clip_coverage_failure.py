"""Read-only preservation and exact Road41 post-binding coverage diagnosis."""
import datetime, hashlib, json, os, time, traceback
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_grounding as grounding
import geocity_roadbld_clip as clip
import geocity_roadbld_junctions as junctions
ROOT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE=ROOT/'Staging/ManagedAstra_2026-10-03'
p=bank.ACTIVE[-1];r=native.ACTIVE[-1]
p.guard();r.guard()
assert os.getpid()==32752 and r.state['phase']=='failed_validating'
assert 'DynamicRoad_41' in r.state['error']
assert all(x.watch_tick is None and x.save_tick is None for x in bank.ACTIVE)
assert all(x.tick_handle is None for x in native.ACTIVE) and not r._tick_running
assert p.api.is_asset_cooking_paused() and p.api.is_session_valid()
assert p.autosave_before is True and not p.autosave_settings.get_editor_property('bAutoSaveEnable')
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
receipt=ROOT/'Staging/AppearanceRepair_2026-10-03'/('TASK2_POST_CLIP_COVERAGE_STOP_'+stamp+'.json')
status_path=HERE/'TASK2_POST_CLIP_COVERAGE_STATUS.json'
def ledger():
    return [{'geo':a.get_path_name(),'source_refs':sorted(native._path(x) for x in native._get(a,'SourceRoads')),
      'component':c.get_path_name(),'mesh':native._path(c.static_mesh),'transform':clip._transform(c.get_world_transform()),
      'materials':clip._materials(c),'collision':clip._collision(c,c.static_mesh) if c.static_mesh else None}
      for a in r.native_geos() for c in a.get_components_by_class(unreal.StaticMeshComponent)]
data={'utc':stamp,'pid':os.getpid(),'phase':r.state['phase'],'error':r.state['error'],
  'parent_state':p.state,'native_state':r.state,'grounding_report':r.grounding_report,'clipping_report':r.clipping_report,
  'junction_repair':r.junction_repair,'owned_participant_snapshot':junctions._owned_state(r),
  'bound_components':ledger(),'transaction_token':r.transaction_token,'revision':r.revision,'rebuild_pass':r.rebuild_pass,
  'lease':p.lease_line,'callbacks':0,'official_engine_paused':True,'official_engine_session_valid':True,
  'autosave_current':False,'original_autosave':True,
  'world':unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name(),
  'dirty_maps':[x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
  'dirty_content':[x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],
  'no_cook_rebuild_save_or_bound_geometry_mutation':True}
mapfile=ROOT/'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration.umap'
data['saved_map_sha256']=hashlib.sha256(mapfile.read_bytes()).hexdigest()
data['saved_map_matches_prior_delivery']=data['saved_map_sha256']=='fe56a24d0eb493f70c3582c2167124b79d1930704be0bac8d33683c8d178c0e7'
receipt.write_text(json.dumps(data,indent=2)+'\n')
handle=None
def collect(dt):
    global handle
    unreal.unregister_slate_post_tick_callback(handle);handle=None
    began=time.monotonic()
    def bounded():
        p.guard();r.guard()
        assert time.monotonic()-began<180
        assert r.tick_handle is None and p.watch_tick is None and p.save_tick is None
    try:
        road=next(a for a in r.roads if a.get_name()=='DynamicRoad_41')
        actors=[a for a in r.native_geos() if road in list(native._get(a,'SourceRoads'))]
        rows,surfaces,empty=grounding._read_native(r,actors,bounded)
        row=next(x for x in rows if x['road_actor_path']==road.get_path_name())
        fields=[(s,grounding.AsphaltField(s['points_cm'],s['triangles'],s['material_ids'],s['upward'])) for s in surfaces]
        samples=[];missing=[]
        for point,segment,fraction in grounding._samples(row,r.plan['settings']['surface_clearance_cm'],100):
            bounded()
            hits=[]
            for s,f in fields:
                eligible=grounding._source_eligibility(s,row['road_actor_path'],point)
                hit=f.covered(point)
                if eligible and hit:hits.append({'component':s['component_path'],'z_cm':hit[0],'triangle':hit[1],'weights':hit[2]})
            item={'point_cm':point,'segment':segment,'fraction':fraction,'hits':hits}
            if not hits:
                item['nearest_by_surface']=[]
                for s,f in fields:
                    distance,xy,number=min((*grounding._closest_xy(point,t),i) for i,t in f.faces.items())
                    item['nearest_by_surface'].append({'component':s['component_path'],'distance_cm':distance,'xy_cm':xy,'triangle':number,'triangle_world_cm':f.faces[number]})
                missing.append(item)
            samples.append(item)
        data.update(source_row=row,samples=samples,missing_samples=missing,missing_sample_count=len(missing),sample_count=len(samples),
          surfaces=[{k:v for k,v in s.items() if k not in ('component','dynamic_mesh','transform')} for s in surfaces],empty_geometry=empty)
        assert ledger()==data['bound_components']
        assert junctions._owned_state(r)==data['owned_participant_snapshot']
        data['participant_and_binding_ledger_unchanged']=True
        data['status']='READ_ONLY_POST_CLIP_COVERAGE_EVIDENCE_COMPLETE'
    except Exception:
        data['status']='READ_ONLY_COLLECTION_FAILED';data['collection_error']=traceback.format_exc()
    data['elapsed_seconds']=time.monotonic()-began
    receipt.write_text(json.dumps(data,indent=2)+'\n')
    status_path.write_text(json.dumps({'status':data['status'],'receipt':str(receipt),'sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),'missing_sample_count':data.get('missing_sample_count'),'elapsed_seconds':data['elapsed_seconds']},indent=2)+'\n')
handle=unreal.register_slate_post_tick_callback(collect)
status_path.write_text(json.dumps({'status':'scheduled_read_only','receipt':str(receipt)},indent=2)+'\n')
print(json.dumps({'scheduled':True,'stop_receipt':str(receipt)}))
