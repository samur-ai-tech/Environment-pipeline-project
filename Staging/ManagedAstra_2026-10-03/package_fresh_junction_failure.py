"""Package already measured failure evidence; no Unreal or SDK calls."""
import datetime,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
preserved=HERE/'FreshJunctionStop_20261003T2039391429154Z'
native_path=preserved/'ROADBLD_WORKFLOW_STATE.json'
native=json.loads(native_path.read_text());report=native['junction_repair_report'];op=report['operation'];call=op['calls'][-1]
livepath=HERE/'FRESH_fresh_junction_stop_20261003T203938737856Z.json'
live=json.loads(livepath.read_text());assert live['actual_participants_unchanged_from_pre_call']
connector=report['connector_actor_path'];want=op['expected_after']['roads'][connector]
logpath=preserved/'Environmentpipeline.log';log=logpath.read_bytes()
cursor=call['start_byte'];assert cursor==call['end_byte']==476884
window_start=max(0,cursor-256);window_end=min(len(log),cursor+8192)
window=log[window_start:window_end]
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
windowpath=HERE/('FRESH_JUNCTION_DELAYED_LOG_WINDOW_'+stamp+'.bin');windowpath.write_bytes(window)
warning=b'LogScript: Warning: RoadBLDToolset: The RoadBLD license check is still running. Retry in a few seconds.'
offset=log.find(warning,cursor);assert offset>=cursor
suffix=log[cursor:window_end]
evidence=dict(status='EXACT_FAILED_CALL_EVIDENCE_PACKAGED_NO_CONTINUATION',pid=21780,revision=native['revision'],
    preserved_native_state=str(native_path),preserved_native_state_sha256=hashlib.sha256(native_path.read_bytes()).hexdigest(),
    live_checkpoint_receipt=str(livepath),live_checkpoint_sha256=hashlib.sha256(livepath.read_bytes()).hexdigest(),
    operation=dict(step=op['step'],task_index=op['task_index'],attempts=op['attempts'],started_monotonic=op['started_monotonic'],deadline_monotonic=op['deadline_monotonic']),
    signature='FRoadBLDEditResult URoadBLDAuthoringToolset::SetControlPoints(ADynamicRoad* Road, const TArray<FRoadBLDPoint>& Points, double LinkTolerance, bool bSnapEndpointsToJunctions, bool bCloseCorners, bool bRebuild)',
    signature_source='Plugins/WorldBLDMCPToolset/Source/RoadBLDToolset/Private/Toolsets/RoadBLDAuthoringToolset.h:165',
    arguments=dict(Road=connector,Points=[dict(Location=p,TurnRadius=r) for p,r in zip(want['control_points_world_cm'],want['point_turn_radii_cm'])],LinkTolerance=0.1,bSnapEndpointsToJunctions=False,bCloseCorners=False,bRebuild=False),
    temporary_radius_default_cm=100.0,defaults_restored=live['actual_defaults']==live['expected_global_defaults'],
    measured_result=dict(Network_RefPath=call['result_network']),
    result_limit='The failed helper retained only Network.RefPath. Full returned FRoadBLDEditResult fields were not serialized and are unavailable without a new call; no SDK replay performed.',
    call_local_capture=call,delayed_log_window=dict(path=str(windowpath),sha256=hashlib.sha256(window).hexdigest(),source_log=str(logpath),source_log_sha256=hashlib.sha256(log).hexdigest(),start_byte=window_start,end_byte=window_end,warning_byte=offset,warning_timestamp_utc='2026-10-03T20:38:49.167Z',later_suffix=suffix.decode('utf-8',errors='replace')),
    participant_checkpoint=dict(before_sha256=live['operation_before_sha256'],actual_sha256=live['actual_owned_state_sha256'],exact_equal=True,source_roads=live['source_roads'],derived_roads=live['derived_roads'],owned_native_geos=live['owned_native_geos'],rebuild_pass=live['rebuild_pass']),
    latest_completed_live_readback={k:live[k] for k in ['callbacks','Engine_valid','Engine_paused','autosave_current','HDA_autoCook','HDA_autoBake','dirty']},
    second_readback='Read-only refresh was refused by current ASSIGNMENTS editor_calls_authorized=false guard before scheduling or native calls. Last completed live readback is the linked 20:39:38 UTC receipt.',
    interpretation='Immediate call-local bytes were empty; a later preserved file contains the exact pending-license warning 30 bytes after that cursor. Consistent with buffered log output, not permission to broaden captured-call evidence or retry.',
    no_source_edit_SDK_retry_Cook_rebuild_save_or_state_transition=True)
path=HERE/('FRESH_JUNCTION_CALL_EVIDENCE_'+stamp+'.json');path.write_text(json.dumps(evidence,indent=2)+'\n')
handoff=HERE/'TASK2_DELIVERY_RESULT.json';data=json.loads(handoff.read_text(encoding='utf-8-sig'))
data['fresh_junction_stop'].update(exact_call_evidence=str(path),exact_call_evidence_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),readback_refresh_guard='ASSIGNMENTS editor_calls_authorized=false; no action scheduled',further_authoring_stopped=True)
handoff.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(dict(receipt=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),warning_byte=offset,points=len(want['control_points_world_cm']),checkpoint_unchanged=True)))
