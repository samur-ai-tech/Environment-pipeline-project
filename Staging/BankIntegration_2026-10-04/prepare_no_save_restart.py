"""Freeze orderly preserved shutdown and existing original-map startup parameters."""
import ast
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=HERE/'DirtyOriginals_Transfer'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def prepare():
    target=OUT/'NO_SAVE_RESTART_REQUEST.json';assert not target.exists()
    q=read(OUT/'PRESERVE_REQUEST.json');rr=read(OUT/'COPY_RELOAD_REQUEST.json');verified=read(OUT/'COPY_RELOAD_FINAL_VERIFICATION.json')
    assert verified['passed'] and all(verified['per_package_reloaded'].values())
    script=HERE/'quit_preserved_editor.py';ast.parse(script.read_text(encoding='utf-8-sig'))
    pins=dict(rr['file_pins']);pins[str(script)]=sha(script)
    for p in (OUT/'COPY_RELOAD_REQUEST.json',OUT/'COPY_RELOAD_RESULT.json',OUT/'COPY_RELOAD_FINAL_VERIFICATION.json',HERE/'verify_loaded_recovery.py'):pins[str(p)]=sha(p)
    for path,expected in pins.items():assert sha(path)==expected,('shutdown_pin_changed',path)
    profiles=[ROOT/'Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json',ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json']
    profile=next(p for p in profiles if read(p)['map']==q['world'])
    manifest=ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
    launcher=ROOT/'Staging/SystemCompletion_2026-10-04/launch_editor.ps1'
    result={'schema':'environmentpipeline.preserved_no_save_restart_request.v1','status':'PREPARED_NOT_EXECUTED',
        'manager_thread_id':q['manager_thread_id'],'operator_thread_id':q['operator_thread_id'],'pid':q['pid'],'world':q['world'],
        'script_path':str(script),'script_sha256':sha(script),'file_pins':pins,'preserve_helper_path':q['script_path'],
        'activation_path':str(ROOT/'Staging/ManagedSystemsAstra_2026-10-04/DirtyOriginals_RESTART_ACTIVATION.json'),
        'required_scope_and_lease_activation':'NO_SAVE_PRESERVED_RESTART','exact_original_buffers_to_discard':q['source_packages'],
        'save_requested':False,'forced_termination':False,'maps_to_save':[],
        'shutdown_method':'unreal.SystemLibrary.quit_editor(); exact current-buffer checks and existing saved recovery proof before request.',
        'post_exit_required':['Confirm PID32508 exited and no UnrealEditor exists','Verify every protected original/map/catalog/profile/source hash and all84 saved imports plus3recovery package hashes','Manager publishes OWNER=NONE after actual exit; no competing editor'],
        'fresh_start':{'existing_launcher':str(launcher),'launcher_sha256':sha(launcher),
            'parameters':{'AreaMap':q['world'],'ExpectedMapSha256':sha(ROOT/'Content'/(q['world'][6:]+'.umap')),'ExpectedManifestSha256':sha(manifest),'ExpectedProfileSha256':sha(profile),'ManagerThreadId':q['manager_thread_id'],'OperatorThreadId':q['operator_thread_id']},
            'startup_scope':'One existing original Shujaiya map, official cooking paused/auto flags off, no generation/save or asset-tab restore. Verify new actualPID and fresh successor startup checkpoint before bank content activation.',
            'manager_activation_refresh_required':['expected_profile_sha256 must use current profile, not historical startup hash','startup_inspector_sha256 must use current reviewed bank inspector','assigned_editor_PID must use actual new process']},
        'no_execution_yet':True}
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'request':str(target),'request_sha256':sha(target),'script_sha256':sha(script),'pins':len(pins)}))

if __name__=='__main__':prepare()
