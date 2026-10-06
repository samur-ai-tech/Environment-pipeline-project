"""Read saved delivery, reopen the same named map, and repeat actual readback."""
import datetime
import json
import os
import runpy
import traceback
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native

HERE=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03')
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
profiles=[HERE.parent/'ModelBank'/name/'AREA_PROFILE.json' for name in
    ('PermanentIntegration_2026-10-02','GazaShujaiyaIntegration_2026-10-02')]
matches=[path for path in profiles if json.loads(path.read_text(encoding='utf-8'))['map']==world]
assert len(matches)==1
profile=matches[0]
area=json.loads(Path(json.loads(profile.read_text(encoding='utf-8'))['source']).read_text(encoding='utf-8'))['area_id']
assert all(not r.watch_tick and not r.save_tick for r in bank.ACTIVE)
assert all(not r.tick_handle for r in native.ACTIVE)
assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
status=HERE/('SAVED_NATIVE_VERIFICATION_'+area+'_'+stamp+'.json')
handle=None
def record(phase,**values):
    status.write_text(json.dumps(dict(area=area,phase=phase,pid=os.getpid(),**values),indent=2)+'\n',encoding='utf-8')
def verify(delta):
    global handle
    unreal.unregister_slate_post_tick_callback(handle);handle=None
    try:
        namespace=runpy.run_path(str(HERE/'inspect_native_road_delivery.py'))
        inspect=namespace['inspect_delivery']
        record('inspecting_actual_saved_native_delivery')
        before=inspect(str(profile),context='saved_readback',max_seconds=300)
        record('reopening_same_named_map',saved_native_status=before['status'])
        reopen=runpy.run_path(str(HERE/'reopen_retained_area.py'))['reopen_area']
        bank_receipt=reopen(str(profile))
        record('inspecting_actual_reopened_native_delivery',bank_reopen_receipt=bank_receipt)
        after=inspect(str(profile),context='reopen_readback',max_seconds=300)
        record('passed',bank_reopen_receipt=bank_receipt,saved_native_receipt=before,
            reopened_native_receipt=after,no_recook=True,fresh_editor_restart=False)
    except Exception as exc:
        record('failed',error=repr(exc),traceback=traceback.format_exc())
record('scheduled')
handle=unreal.register_slate_post_tick_callback(verify)
print(json.dumps({'scheduled':True,'area':area,'status_path':str(status)}))
