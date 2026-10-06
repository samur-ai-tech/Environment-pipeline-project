"""Explicit manager-activated post-rebuild continuation; import has no effects.

Call schedule() only after the reviewed grounding/clip source freeze.
Preserves completed junctions and the existing official-export transaction.
"""
import datetime
import hashlib
import importlib
import json
import os
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
ACTIVE_CONTINUATIONS=[]

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def schedule():
    import unreal
    import geocity_bank_workflow as bank
    import geocity_roadbld_workflow as native
    import geocity_roadbld_junctions as junctions
    import geocity_roadbld_grounding as grounding
    import geocity_roadbld_clip as clip
    p=bank.ACTIVE[-1]
    r=native.ACTIVE[-1]
    p.guard();r.guard()
    assignment=read(HERE/'ASSIGNMENTS.json')
    worker='01a102e1-25e6-7f13-b593-4988290a283b'
    assert assignment['editor_writer_thread_id']==worker
    assert assignment['tasks']['task2_delivery']['status']=='active_editor_writer'
    assert assignment['tasks']['task2_delivery']['editor_calls_authorized']
    assert os.getpid()==32752 and ('worker_thread_id='+worker) in p.lease_line
    assert p.lease_line==r.lease_line
    p.guard_processes()
    assert all(x.watch_tick is None and x.save_tick is None for x in bank.ACTIVE)
    assert all(x.tick_handle is None for x in native.ACTIVE) and not r._tick_running
    assert all(item['handle'] is None for item in ACTIVE_CONTINUATIONS)
    assert p.api.is_asset_cooking_paused() and p.api.is_session_valid()
    assert p.autosave_before is True and not p.autosave_settings.get_editor_property('bAutoSaveEnable')
    freeze=read(HERE/'TASK1_SOURCE_RESULT.json')
    assert freeze['status']=='READY_FOR_EDITOR'
    required={'geocity_roadbld_grounding.py','geocity_roadbld_clip.py',
        'geocity_roadbld_junctions.py','geocity_roadbld_workflow.py'}
    assert required.issubset(freeze['frozen_files']), 'Complete reviewed source freeze is required'
    for name in required:
        row=freeze['frozen_files'][name]
        assert Path(row['path']).resolve()==(ROOT/'Content/Python'/name).resolve()
        assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256']
    stopped=read(ROOT/'Staging/AppearanceRepair_2026-10-03/TASK2_HEIGHT_GATE_STOP_20261003T185123265485Z.json')
    earlier_stop=read(ROOT/'Staging/AppearanceRepair_2026-10-03/TASK2_GROUNDING_STOP_20261003T183116246178Z.json')
    evidence=read(ROOT/'Staging/AppearanceRepair_2026-10-03/TASK2_GROUNDING_GEOMETRY_20261003T183550025521Z.json')
    assert evidence['status']=='READ_ONLY_EVIDENCE_COMPLETE'
    assert r.state['phase']=='failed_clipping' and p.state['phase']=='failed_native_road_transaction'
    assert r.state['error']==stopped['error']
    assert stopped['error'].startswith("AssertionError('Actual native asphalt exceeds source-ground height tolerance:")
    assert r.state['junction_repair_report']==stopped['native_state']['junction_repair_report']
    assert stopped['native_state']['junction_repair_report']==earlier_stop['native_state']['junction_repair_report']
    assert junctions._sha(r.state['junction_repair_report'])==evidence['junction_checkpoint_sha256']
    assert r.junction_repair==r.state['junction_repair_report']
    assert r.junction_repair['completed_corner_count']==4
    assert r.junction_repair['checkpoint_version']==1 and r.junction_repair['task_index']==4
    assert r.junction_repair['step_index']==0 and not r.junction_repair.get('operation')
    assert r.junction_repair['phase']=='native_corners_authored_pending_rebuild'
    assert r.revision=='20261003T172549017159' and r.rebuild_pass==3
    assert r.transaction_token==r.junction_repair['transaction_identity']['token']
    assert len(r.roads)==40 and len(r.derived_junction_roads)==4
    assert r.network.get_path_name()==r.junction_repair['transaction_identity']['network']
    assert not r.network.is_road_network_stale()
    assert not getattr(r,'grounding_report',None) and not r.clipping_report
    assert 'grounding_report' not in r.state and 'clipping_report' not in r.state
    owned=junctions._owned_state(r)
    assert junctions._sha(owned)==junctions._sha(evidence['participant_snapshot_before'])
    assert junctions._sha(owned)==junctions._sha(stopped['owned_participant_snapshot'])
    assert junctions._sha(owned)==junctions._sha(earlier_stop['owned_participant_snapshot'])
    geos=r.native_geos()
    bindings=[{'geo':a.get_path_name(),'component':c.get_path_name(),'mesh':native._path(c.static_mesh),
        'transform':clip._transform(c.get_world_transform()),'materials':clip._materials(c)}
        for a in geos for c in a.get_components_by_class(unreal.StaticMeshComponent)]
    ordered=lambda values:sorted(values,key=lambda row:row['component'])
    assert ordered(bindings)==ordered(evidence['bound_component_snapshot_before'])
    assert all(row['mesh'] is None or (':PersistentLevel.RoadGeo_' in row['mesh'] and row['mesh'].endswith('.RoadGeoSurfaceMesh')) for row in bindings)
    source_refs={a.get_path_name():sorted(native._path(road) for road in native._get(a,'SourceRoads')) for a in geos}
    owned_roads={native._path(road) for road in r.roads+r.derived_junction_roads}
    assert all(paths and set(paths).issubset(owned_roads) for paths in source_refs.values())
    for surface in evidence['surfaces']:
        assert source_refs[surface['geometry_actor']]==sorted(surface['native_source_refs'])
    assert source_refs[stopped['failure_geo']]==sorted(stopped['failure_geo_source_refs'])
    by_component={row['component']:row for row in bindings}
    for measured in stopped['native_meshes_before_grounding']:
        actual=by_component[measured['component']]
        assert actual['mesh']==measured['bound_mesh']
        assert actual['transform']==measured['transform'] and actual['materials']==measured['materials']
        component=unreal.load_object(None,measured['component'])
        assert clip._collision(component,component.static_mesh)==measured['collision']
    # Compare fresh read-copy geometry of the offending component to the full
    # original native geometry captured after the height failure. Historical
    # grounded reconstructions never serve as inputs to this continuation.
    detail=read(ROOT/'Staging/AppearanceRepair_2026-10-03/TASK2_HEIGHT_GATE_DETAIL_20261003T185441439244Z.json')
    assert detail['status']=='READ_ONLY_HEIGHT_DETAIL_COMPLETE'
    for measured in detail['original_native_components']:
        component=unreal.load_object(None,measured['component'])
        assert native._path(component.static_mesh)==measured['bound_mesh']
        copied=clip._copy_static(component.static_mesh)
        points,triangles=clip._read_geometry(copied,component.get_world_transform())
        assert points==measured['world_vertices_cm'] and triangles==measured['triangles']
    dirty_maps=[x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    dirty_content=[x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    before_path=ROOT/'Staging/AppearanceRepair_2026-10-03'/('TASK2_PRE_CLIPPING_RESUME_'+stamp+'.json')
    assert not before_path.exists()
    before_path.write_text(json.dumps({'utc':stamp,'pid':os.getpid(),'source_freeze':freeze['frozen_files'],
        'parent_state':p.state,'native_state':r.state,'junction_repair':r.junction_repair,
        'exact_latest_stop_receipt':'TASK2_HEIGHT_GATE_STOP_20261003T185123265485Z.json',
        'earlier_grounding_stop_receipt_preserved':'TASK2_GROUNDING_STOP_20261003T183116246178Z.json',
        'fresh_offending_native_geometry_matches_recorded_original':True,
        'owned_snapshot':owned,'bound_components':bindings,'native_source_refs':source_refs,
        'native_previous_delivery':r.previous,'transaction_token':r.transaction_token,
        'landscape_sampler_before':getattr(getattr(r,'landscape_sampler',None),'path',None),
        'dirty_maps':dirty_maps,'dirty_content':dirty_content,'lease':p.lease_line,
        'autosave_current':False,'original_autosave':True},indent=2)+'\n',encoding='utf-8')

    # Only the two manager-reviewed source helpers change. Keep p/r classes,
    # ACTIVE lists, completed junctions, original export and transaction token.
    clip=importlib.reload(clip)
    grounding=importlib.reload(grounding)
    assert bank.ACTIVE[-1] is p and native.ACTIVE[-1] is r
    r.on_complete=p.after_native_roads
    p.native_road_phase='authoring'
    p.started_epoch=time.time()
    p.state['phase']='native_road_authoring'
    p.state['task2_clipping_resume_evidence']=str(before_path)
    p.wrapper.on_post_cook_delegate.add_callable(p.after_cook)
    p.wrapper.on_post_processing_delegate.add_callable(p.after_processing)
    p.watch_tick=unreal.register_slate_post_tick_callback(p.watch)
    continuation={'handle':None,'started':False}
    def post_rebuild(delta):
        if continuation['started']:
            return
        continuation['started']=True
        unreal.unregister_slate_post_tick_callback(continuation['handle'])
        continuation['handle']=None
        try:
            p.guard();r.guard()
            assert r.tick_handle is None and not r._tick_running
            assert junctions._sha(r.junction_repair)==evidence['junction_checkpoint_sha256']
            r._tick_running=True
            r.state['phase']='clipping';r.write()
            # Existing helper chooses the current official-export Landscape,
            # prepares transient grounding and binds only verified clip output.
            r.clip_final_geometry()
            r.state['phase']='validating';r.write()
            r.validate()
            r.finish()
            r.on_complete(r,True)
        except Exception as exc:
            r.fail(exc)
        finally:
            r._tick_running=False
            if r.state['phase'].startswith('failed') or p.state['phase'].startswith('failed'):
                p.suspend_transaction_autosave()
                p.write()
    p.write()
    ACTIVE_CONTINUATIONS.append(continuation)
    continuation['handle']=unreal.register_slate_post_tick_callback(post_rebuild)
    return {'scheduled':True,'pre_resume_evidence':str(before_path),'revision':r.revision,
        'rebuild_pass_retained':r.rebuild_pass,'completed_corners_retained':4,'new_cook_or_rebuild':False}
