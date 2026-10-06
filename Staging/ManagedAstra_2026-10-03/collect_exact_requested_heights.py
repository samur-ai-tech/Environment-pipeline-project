"""Read-only exact XY request; no source-helper reload or geometry mutation."""
import datetime
import hashlib
import json
import os
import time
import traceback
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_junctions as junctions
import geocity_roadbld_clip as clip

HERE=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ManagedAstra_2026-10-03')
ROOT=HERE.parent.parent
request_snapshot=json.loads((HERE/'TASK2_HEIGHT_441_REQUEST_SNAPSHOT.json').read_text())
request=request_snapshot['request']
assert hashlib.sha256(json.dumps(request,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==request_snapshot['request_sha256']
assert len(request['points'])==request['query_count']==441
p=bank.ACTIVE[-1];r=native.ACTIVE[-1]
p.guard();r.guard()
assert os.getpid()==32752 and r.state['phase']=='failed_clipping'
assert all(x.watch_tick is None and x.save_tick is None for x in bank.ACTIVE)
assert all(x.tick_handle is None for x in native.ACTIVE) and not r._tick_running
assert p.api.is_asset_cooking_paused()
assert p.autosave_before is True and not p.autosave_settings.get_editor_property('bAutoSaveEnable')
sampler=r.landscape_sampler
assert sampler.path==request['landscape_path']
assert request['source_road_actor_path'] in [v.get_path_name() for v in r.roads]
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
assert all(a==sampler.landscape or a in sampler.ignored for a in actors)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
receipt=ROOT/'Staging/AppearanceRepair_2026-10-03'/('TASK2_EXACT_PROJECTED_LANDSCAPE_441_'+stamp+'.json')
status_path=HERE/'TASK2_EXACT_HEIGHT_441_STATUS.json'
handle=None

def status(phase,**values):
    status_path.write_text(json.dumps(dict(phase=phase,receipt=str(receipt),**values),indent=2)+'\n')

def collect(dt):
    global handle
    unreal.unregister_slate_post_tick_callback(handle);handle=None
    start=time.monotonic()
    data={'utc':stamp,'request_sha256':request_snapshot['request_sha256'],
        'request_snapshot':str(HERE/'TASK2_HEIGHT_441_REQUEST_SNAPSHOT.json'),'request':request,'samples':[]}
    def bindings():
        return sorted([{'component':c.get_path_name(),'mesh':native._path(c.static_mesh),
            'transform':clip._transform(c.get_world_transform()),'materials':clip._materials(c)}
            for a in r.native_geos() for c in a.get_components_by_class(unreal.StaticMeshComponent)],key=lambda row:row['component'])
    try:
        before=junctions._owned_state(r)
        bound=bindings()
        checkpoint=junctions._sha(r.state['junction_repair_report'])
        status('collecting_exact_request')
        for index,point in enumerate(request['points']):
            p.guard();r.guard()
            assert time.monotonic()-start<120
            xy=point['xy_cm']
            data['samples'].append({'request_index':index,'xy_cm':xy,'roles':point['roles'],
                'actual_Landscape_z_cm':sampler(xy[0],xy[1])})
        assert junctions._sha(junctions._owned_state(r))==junctions._sha(before)
        assert checkpoint==junctions._sha(r.state['junction_repair_report'])
        assert bound==bindings()
        data.update(status='EXACT_REQUEST_HEIGHTS_COLLECTED',sample_count=len(data['samples']),
            actual_Landscape_path=sampler.path,participant_checkpoint_and_bindings_unchanged=True,
            no_source_reload_or_geometry_mutation=True,callbacks=0,autosave_current=False,original_autosave=True,
            elapsed_seconds=time.monotonic()-start)
        payload=json.dumps(data,indent=2,allow_nan=False).encode('utf-8')
        receipt.write_bytes(payload)
        status('complete',sample_count=len(data['samples']),sha256=hashlib.sha256(payload).hexdigest(),
            request_sha256=request_snapshot['request_sha256'],elapsed_seconds=data['elapsed_seconds'])
    except Exception as exc:
        data.update(status='FAILED_EXACT_REQUEST_COLLECTION',error=repr(exc),traceback=traceback.format_exc())
        receipt.write_text(json.dumps(data,indent=2)+'\n')
        status('failed',error=repr(exc))

assert not receipt.exists()
status('scheduled')
handle=unreal.register_slate_post_tick_callback(collect)
print(json.dumps({'scheduled':True,'status_path':str(status_path),'receipt':str(receipt)}))
