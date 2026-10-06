"""Prepared bounded legacy-connector repair; import has no editor effects.

Execute repair() only after the manager's next explicit authorization.
No native SDK edit, cook, save, rebuild, default edit or new actor is performed.
"""
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def repair():
    import unreal
    import geocity_bank_workflow as bank
    import geocity_roadbld_workflow as native
    import geocity_roadbld_junctions as junctions
    p=bank.ACTIVE[-1]
    r=native.ACTIVE[-1]
    p.guard();r.guard()
    assignment=read(HERE/'ASSIGNMENTS.json')
    worker='01a102e1-25e6-7f13-b593-4988290a283b'
    assert assignment['editor_writer_thread_id']==worker
    assert assignment['tasks']['task2_delivery']['editor_calls_authorized']
    assert os.getpid()==32752 and ('worker_thread_id='+worker) in p.lease_line
    assert p.lease_line==r.lease_line
    assert all(x.watch_tick is None and x.save_tick is None for x in bank.ACTIVE)
    assert all(x.tick_handle is None for x in native.ACTIVE) and not r._tick_running
    assert p.api.is_asset_cooking_paused() and p.api.is_session_valid()
    assert p.autosave_before is True and not p.autosave_settings.get_editor_property('bAutoSaveEnable')
    freeze=read(HERE/'TASK1_SOURCE_RESULT.json')
    assert freeze['status']=='READY_FOR_EDITOR'
    for entry in freeze['frozen_files'].values():
        assert hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest()==entry['sha256']
    failed=read(ROOT/'Staging/AppearanceRepair_2026-10-03/TASK2_FAILED_RECOVERY_20261003T181945515173Z.json')
    assert r.state['phase']=='failed_conditioning' and p.state['phase']=='failed_native_road_transaction'
    assert r.state['error']==failed['error'] and r.state['junction_recovery_error']==failed['recovery_error']
    old=r.state['junction_repair_report']
    assert old==failed['native_state']['junction_repair_report']
    assert 'checkpoint_version' not in old and not old.get('operation')
    assert r.revision=='20261003T172549017159' and r.rebuild_pass==1
    assert len(r.roads)==40 and len(r.derived_junction_roads)==1
    connector=r.derived_junction_roads[0]
    connector_path=connector.get_path_name()
    assert connector_path.endswith(':PersistentLevel.DynamicRoad_86')
    assert r.network.get_path_name().endswith(':PersistentLevel.DynamicRoadNetwork_1')
    before=junctions._owned_state(r)
    empty=before['roads'][connector_path]
    assert empty['control_points_world_cm']==[] and empty['point_turn_radii_cm']==[]
    assert empty['links']=={'Start':[],'End':[]}
    assert empty['policy']['bEnableLandscapeSplineMirroring'] is True
    for excluded in ('bConformToLandscape','bEnableLandscapePaint','bGenerateAbutments','bEnableRoadEdgeDetail'):
        assert empty['policy'][excluded] is False
    assert empty['policy']['RoadPCGGraph'] is None
    assert sorted(x.get_path_name() for x in r.roads)==old['original_source_actor_paths']
    for path,proof in old['sourcecontrols_trimproof'].items():
        original=before['roads'][path]
        junctions._controls_equal(original['control_points_world_cm'],proof['original_control_points_world_cm'])
        assert original['point_turn_radii_cm']==proof['original_point_turn_radii_cm']
        for key in ('width_start_cm','width_end_cm'):
            assert abs(original[key]-proof[key])<=0.1
    preflight=junctions._preflight_native_corners(r,recovery=old)
    assert junctions._sha(preflight['sourcecontrols_trimproof'])==junctions._sha(old['sourcecontrols_trimproof'])
    assert junctions._sha(junctions._owned_state(r))==junctions._sha(before), 'Preflight changed participants'
    first=preflight['planned_tasks'][0]
    assert first['a'].endswith(':PersistentLevel.DynamicRoad_60')
    assert first['b'].endswith(':PersistentLevel.DynamicRoad_79')
    assert first['start_a'] is True and first['start_b'] is True
    assert first['turn_radius_cm']==100.0
    parent=unreal.load_object(None,first['a'])
    assert parent in r.roads
    assert empty['preset']==before['roads'][first['a']]['preset']
    assert empty['preset_class']==before['roads'][first['a']]['preset_class']
    assert abs(empty['radius_limits'][0]-first['turn_radius_cm'])<=0.1
    fields=tuple(junctions._POLICY_FIELDS)
    assert fields==('bEnableLandscapeSplineMirroring','bConformToLandscape','bEnableLandscapePaint',
        'bGenerateAbutments','bEnableRoadEdgeDetail','RoadPCGGraph','RoadCrownHeight','RoadThickness')
    expected=copy.deepcopy(before)
    expected['roads'][connector_path]['policy']=copy.deepcopy(before['roads'][first['a']]['policy'])
    differences={key:{'before':empty['policy'][key],'after':expected['roads'][connector_path]['policy'][key]}
        for key in fields if empty['policy'][key]!=expected['roads'][connector_path]['policy'][key]}
    assert differences and expected['roads'][connector_path]['policy']['bEnableLandscapeSplineMirroring'] is False
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    evidence_root=ROOT/'Staging/AppearanceRepair_2026-10-03'
    before_path=evidence_root/('TASK2_CONNECTOR_POLICY_BEFORE_'+stamp+'.json')
    after_path=evidence_root/('TASK2_CONNECTOR_POLICY_AFTER_'+stamp+'.json')
    assert not before_path.exists() and not after_path.exists()
    evidence={'utc':stamp,'pid':os.getpid(),'revision':r.revision,'transaction_token':r.transaction_token,
        'legacy_report':old,'native_state':r.state,'parent_state':p.state,'before':before,
        'first_task':first,'first_parent_actor':first['a'],'connector_actor':connector_path,
        'full_preflight':preflight,'allowed_fields':list(fields),'expected_differences':differences,
        'source_freeze':freeze['frozen_files'],'lease':p.lease_line}
    before_path.write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    try:
        for name in fields:
            native._set(connector,name,native._get(parent,name))
        after=junctions._owned_state(r)
        assert junctions._sha(after)==junctions._sha(expected),'Policy repair changed unexpected participant state'
        junctions._closed_policy(connector,first['turn_radius_cm'])
        assert old==r.state['junction_repair_report']
        result={'status':'EXACT_EMPTY_CONNECTOR_POLICY_REPAIRED','before_receipt':str(before_path),
            'after':after,'allowed_differences':differences,'full_after_matches_expected':True,
            'legacy_report_unchanged':True,'callbacks':0,'sdk_edits':False,'defaults_changed':False,
            'saved':False,'rebuilt':False,'new_actor':False}
    except Exception as exc:
        result={'status':'FAILED_PRESERVED_FOR_MANAGER','error':repr(exc),'before_receipt':str(before_path),
            'after':junctions._owned_state(r),'callbacks':0,'saved':False}
        after_path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        raise
    after_path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return {'status':result['status'],'before_receipt':str(before_path),'after_receipt':str(after_path),
        'first_parent_actor':first['a'],'allowed_differences':differences}
