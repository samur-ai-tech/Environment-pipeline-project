"""PREPARED ONLY. Explicit root activation required; import performs no action.

schedule(expected_grounding_sha256, expected_workflow_sha256, independent_review_sha256,
         manager_activation='ROOT_ACTIVATED_POSTBINDING_VALIDATION')
Only the already-bound native candidate is validated, then the normal parent
suppression/Bake/named-save lifecycle proceeds. Never re-ground or re-clip.
"""
import datetime,hashlib,importlib,json,os,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
ACTIVE=[]
STOP='Staging/AppearanceRepair_2026-10-03/TASK2_POST_CLIP_COVERAGE_STOP_20261003T192250614726Z.json'
SCAN='Staging/AppearanceRepair_2026-10-03/TASK2_ALL40_POST_CLIP_GAPS_20261003T192521158589Z.json'
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def frozen(expected_grounding_sha256,expected_workflow_sha256,independent_review_sha256):
    freeze=read(HERE/'TASK1_SOURCE_RESULT.json');assert freeze['status']=='READY_FOR_EDITOR'
    assert expected_grounding_sha256=='62a8a28a03803fb845bafa2ce820b742a83cb35134b25cf192fcd532bbf6233d'
    assert expected_workflow_sha256=='1909fb60f22be17a18012a5b2a8f990d6fdc7c5c73b8ae164f8fbef5e74ad453'
    assert sha(HERE/'TASK3_REVIEW_RESULT.json')==independent_review_sha256
    expected={'geocity_roadbld_grounding.py':expected_grounding_sha256,
      'geocity_roadbld_clip.py':'872f4814060a214cdf4238a8ae8c7b9a0a819364bc4f5ea486e573d396980211',
      'geocity_roadbld_junctions.py':'3b61e97c5fc5f4b167329f0f620a0a365c5a71e772e62fbd02a9af0343f48699',
      'geocity_roadbld_workflow.py':expected_workflow_sha256}
    for name,digest in expected.items():
        entry=freeze['frozen_files'][name]
        assert Path(entry['path']).resolve()==(ROOT/'Content/Python'/name).resolve()
        assert entry['sha256']==digest==sha(entry['path'])
    return freeze
def schedule(expected_grounding_sha256,expected_workflow_sha256,independent_review_sha256,manager_activation):
    assert manager_activation=='ROOT_ACTIVATED_POSTBINDING_VALIDATION','Explicit root activation required after review'
    import unreal
    import geocity_bank_workflow as bank
    import geocity_roadbld_workflow as native
    import geocity_roadbld_clip as clip
    import geocity_roadbld_grounding as grounding
    import geocity_roadbld_junctions as junctions
    p=bank.ACTIVE[-1];r=native.ACTIVE[-1];p.guard();r.guard();p.guard_processes()
    assignment=read(HERE/'ASSIGNMENTS.json');worker='01a102e1-25e6-7f13-b593-4988290a283b'
    assert assignment['editor_writer_thread_id']==worker and assignment['tasks']['task2_delivery']['status']=='active_editor_writer'
    assert assignment['tasks']['task2_delivery']['editor_calls_authorized']
    assert os.getpid()==32752 and ('worker_thread_id='+worker) in p.lease_line and p.lease_line==r.lease_line
    assert not any(item['handle'] is not None for item in ACTIVE)
    assert all(x.watch_tick is None and x.save_tick is None for x in bank.ACTIVE)
    assert all(x.tick_handle is None for x in native.ACTIVE) and not r._tick_running
    assert p.api.is_asset_cooking_paused() and p.api.is_session_valid()
    assert p.autosave_before is True and not p.autosave_settings.get_editor_property('bAutoSaveEnable')
    freeze=frozen(expected_grounding_sha256,expected_workflow_sha256,independent_review_sha256)
    assert sha(ROOT/STOP)=='553b5fedd7781672b2dbb81740d4c917b9d8ee73382da854acf779b48cb93d1c'
    assert sha(ROOT/SCAN)=='4e13c9270191f003d770909349247bb6ba31ef41d3d9b0d715d878c3ae3950a9'
    stop=read(ROOT/STOP);scan=read(ROOT/SCAN)
    assert p.state['phase']==stop['parent_state']['phase']=='failed_native_road_transaction'
    assert r.state['phase']==stop['phase']=='failed_validating' and r.state['error']==stop['error']
    assert p.native_road_run is r and r.revision==stop['revision']=='20261003T172549017159'
    assert r.on_complete==p.after_native_roads,'Original parent completion callback differs'
    assert r.transaction_token==stop['transaction_token'] and r.rebuild_pass==stop['rebuild_pass']==3
    assert len(r.roads)==40 and len(r.derived_junction_roads)==4 and not r.network.is_road_network_stale()
    assert r.junction_repair==stop['junction_repair']==scan['junction_repair']
    assert r.junction_repair['checkpoint_version']==1 and r.junction_repair['completed_corner_count']==4
    assert r.junction_repair['task_index']==4 and r.junction_repair['step_index']==0 and not r.junction_repair.get('operation')
    assert junctions._owned_state(r)==stop['owned_participant_snapshot']==scan['owned_snapshot']
    assert r.grounding_report==stop['grounding_report'] and r.grounding_report['passed']
    assert r.clipping_report==stop['clipping_report'] and len(r.clipping_report['bindings'])==87
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name()==stop['world'] and r.landscape_sampler.path==r.grounding_report['landscape_actor_path']
    mapfile=ROOT/'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration.umap'
    assert sha(mapfile)==stop['saved_map_sha256']=='fe56a24d0eb493f70c3582c2167124b79d1930704be0bac8d33683c8d178c0e7'
    bindings=[{'geo':a.get_path_name(),'source_refs':sorted(native._path(x) for x in native._get(a,'SourceRoads')),
      'component':c.get_path_name(),'mesh':native._path(c.static_mesh),'transform':clip._transform(c.get_world_transform()),
      'materials':clip._materials(c),'collision':clip._collision(c,c.static_mesh) if c.static_mesh else None}
      for a in r.native_geos() for c in a.get_components_by_class(unreal.StaticMeshComponent)]
    order=lambda items:sorted(items,key=lambda x:x['component'])
    assert order(bindings)==order(stop['bound_components']) and len(bindings)==87
    began=time.monotonic()
    def bounded():
        p.guard();r.guard();assert time.monotonic()-began<180
    # Old loaded reader only: remeasure actual bound geometry before refreshing
    # the final verifier. This copies meshes and does not evaluate the HDA.
    rows,surfaces,empty=grounding._read_native(r,None,bounded)
    hashes=[{'component':s['component_path'],'mesh':s['original_mesh_path'],
      'geometry_sha256':grounding._sha({'points_cm':s['points_cm'],'triangles':s['triangles']}),
      'material_ids_sha256':grounding._sha(s['material_ids']),'upward_sha256':grounding._sha(s['upward'])} for s in surfaces]
    assert order(hashes)==order(scan['geometry_hashes']) and len(hashes)==87 and empty==scan['empty_geometry']
    assert rows==scan['source_rows']
    dirty_maps=sorted(x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
    dirty_content=sorted(x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
    assert dirty_maps==sorted(stop['dirty_maps']) and dirty_content==sorted(stop['dirty_content'])
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    receipt=ROOT/'Staging/AppearanceRepair_2026-10-03'/('TASK2_PRE_POSTBINDING_RESUME_'+stamp+'.json')
    assert not receipt.exists()
    receipt.write_text(json.dumps({'utc':stamp,'pid':os.getpid(),'source_freeze':freeze['frozen_files'],'review_sha256':independent_review_sha256,
      'activation':manager_activation,'parent_state':p.state,'native_state':r.state,'bound_components':bindings,'actual_geometry_hashes':hashes,
      'owned_snapshot':junctions._owned_state(r),'junction_repair':r.junction_repair,'dirty_maps':dirty_maps,'dirty_content':dirty_content,
      'saved_map_sha256':sha(mapfile),'grounding_report':r.grounding_report,'clipping_report':r.clipping_report,
      'callbacks_before':0,'official_engine_paused':True,'official_engine_valid':True,'no_geometry_replay':True},indent=2)+'\n')
    grounding=importlib.reload(grounding)
    assert grounding.SCHEMA==stop['grounding_report']['schema']
    assert bank.ACTIVE[-1] is p and native.ACTIVE[-1] is r
    # Keep the original class, parent phase, callbacks and reports untouched
    # until the separately requested first read-only physical verifier passes.
    original_class=type(r)
    state={'handle':None,'started':False,'lifecycle_started':False,'completion_called':False}
    def resume(dt):
        if state['started']:return
        state['started']=True;unreal.unregister_slate_post_tick_callback(state['handle']);state['handle']=None
        try:
            p.guard();r.guard();assert r.tick_handle is None and not r._tick_running
            assert r.junction_repair==stop['junction_repair']
            assert p.watch_tick is None and p.save_tick is None
            preliminary=grounding.verify_native_delivery(r,r.landscape_sampler,
                landscape_actor_path=r.landscape_sampler.path,max_seconds=180.0)
            assert preliminary['passed'] and type(r) is original_class and native.ACTIVE[-1] is r
            evidence=read(receipt);evidence['initial_read_only_final_verifier']=preliminary
            receipt.write_text(json.dumps(evidence,indent=2)+'\n')
            assert r.on_complete==p.after_native_roads
            p.native_road_phase='authoring';p.started_epoch=time.time()
            p.state['phase']='native_road_authoring';p.state['task2_postbinding_resume_evidence']=str(receipt)
            p.wrapper.on_post_cook_delegate.add_callable(p.after_cook)
            p.wrapper.on_post_processing_delegate.add_callable(p.after_processing)
            p.watch_tick=unreal.register_slate_post_tick_callback(p.watch)
            state['lifecycle_started']=True;p.write()
            r._tick_running=True;r.state['phase']='validating';r.write()
            r.validate();r.finish()
            assert not state['completion_called'];state['completion_called']=True
            r.on_complete(r,True)
        except Exception as exc:
            if state['lifecycle_started']:r.fail(exc)
            else:
                evidence=read(receipt);evidence['initial_read_only_final_verifier_error']=repr(exc)
                evidence['stopped_without_parent_or_native_phase_transition']=True
                receipt.write_text(json.dumps(evidence,indent=2)+'\n')
        finally:
            r._tick_running=False
            if state['lifecycle_started'] and (r.state['phase'].startswith('failed') or p.state['phase'].startswith('failed')):
                p.suspend_transaction_autosave();p.write()
    ACTIVE.append(state);state['handle']=unreal.register_slate_post_tick_callback(resume)
    return {'scheduled':True,'pre_resume_receipt':str(receipt),'revision':r.revision,'next':'Fresh validate then existing finish/after_native_roads lifecycle','re_ground_clip_rebuild_corner_replay':False}
