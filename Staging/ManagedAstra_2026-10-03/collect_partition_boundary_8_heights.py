"""Exact eight requested Landscape heights; no geometry processing or reload."""
import datetime,hashlib,json,os,time
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_clip as clip
import geocity_roadbld_junctions as j
ROOT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline');HERE=ROOT/'Staging/ManagedAstra_2026-10-03'
request=HERE/'TASK2_PARTITION_8_HEIGHT_REQUEST_SNAPSHOT.json'
assert hashlib.sha256(request.read_bytes()).hexdigest()=='1905ec35d72407e4cf78c5ec82fea175afe0fefe5ac3104e8054a209d20b1e76'
coords=json.loads(request.read_text(encoding='utf-8-sig'))['partition_boundary_sampling_request']['coordinates'];assert len(coords)==8
p=bank.ACTIVE[-1];r=native.ACTIVE[-1];p.guard();r.guard()
assert os.getpid()==32752 and r.state['phase']=='failed_validating'
assert p.watch_tick is None and p.save_tick is None and r.tick_handle is None and not r._tick_running
assert p.api.is_asset_cooking_paused() and p.api.is_session_valid() and not p.autosave_settings.get_editor_property('bAutoSaveEnable')
assert r.landscape_sampler.path==r.grounding_report['landscape_actor_path']
def ledger():return [{'component':c.get_path_name(),'mesh':native._path(c.static_mesh),'materials':clip._materials(c),'transform':clip._transform(c.get_world_transform())} for a in r.native_geos() for c in a.get_components_by_class(unreal.StaticMeshComponent)]
def dirty():return {'maps':sorted(x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),'content':sorted(x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
before=ledger();owned=j._owned_state(r);checkpoint=j._sha(r.junction_repair);dirty_before=dirty();began=time.monotonic()
measurements=[dict(row,actual_Landscape_z_cm=r.landscape_sampler(*row['xy_cm'])) for row in coords]
assert time.monotonic()-began<10 and ledger()==before and j._owned_state(r)==owned and j._sha(r.junction_repair)==checkpoint and dirty()==dirty_before
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
receipt=ROOT/'Staging/AppearanceRepair_2026-10-03'/('TASK2_PARTITION_BOUNDARY_8_HEIGHTS_'+stamp+'.json')
d={'status':'READ_ONLY_EXACT8_BOUNDARY_HEIGHTS_COMPLETE','pid':os.getpid(),'world':unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name(),
 'request_snapshot':str(request),'request_sha256':hashlib.sha256(request.read_bytes()).hexdigest(),'landscape_path':r.landscape_sampler.path,
 'measurements':measurements,'elapsed_seconds':time.monotonic()-began,'bound_ledger_sha256':j._sha(before),'participants_sha256':j._sha(owned),'checkpoint_sha256':checkpoint,
 'participant_binding_checkpoint_dirty_packages_unchanged':True,'callbacks':0,'Engine_paused':True,'Engine_valid':True,'autosave_current':False,'no_geometry_processing_reload_cook_rebuild_or_save':True}
receipt.write_text(json.dumps(d,indent=2)+'\n')
(HERE/'TASK2_PARTITION_BOUNDARY_8_STATUS.json').write_text(json.dumps({'status':d['status'],'receipt':str(receipt),'sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),'elapsed_seconds':d['elapsed_seconds'],'sample_count':len(measurements)},indent=2)+'\n')
print(json.dumps({'receipt':str(receipt),'sample_count':8,'elapsed_seconds':d['elapsed_seconds']}))
