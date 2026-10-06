"""Orderly no-save exit only after exact recovery disk readback and activation."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent;OUT=HERE/'DirtyOriginals_Transfer'
REQUEST=OUT/'NO_SAVE_RESTART_REQUEST.json'


def run():
    request=json.loads(REQUEST.read_text(encoding='utf-8'))
    assert Path(__file__).resolve()==Path(request['script_path']).resolve()
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==request['script_sha256']
    for p,s in request['file_pins'].items(): assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==s,('shutdown_input_changed',p)
    helper=Path(request['preserve_helper_path']);ns={'__file__':str(helper),'__name__':'reviewed_bank_shutdown_helpers'}
    exec(compile(helper.read_bytes(),str(helper),'exec'),ns)
    import unreal
    import geocity_runtime_guard as guard
    guard.verify()
    activation=ns['read'](request['activation_path'])
    f=ns['fields']([s for s in (ns['ROOT']/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1])
    assert activation['approved'] is True and activation['scope']==f['activation']=='NO_SAVE_PRESERVED_RESTART'
    assert activation['request_sha256']==ns['sha'](REQUEST) and activation['script_sha256']==ns['sha'](__file__)
    assert activation['manager_thread_id']==f['manager_thread_id']==request['manager_thread_id']
    assert activation['operator_thread_id']==f['operator_thread_id']==request['operator_thread_id']
    assert f['OWNER']=='CODEX_BANK_INTEGRATION' and f['ordinary_generation_authorized']=='false'
    state=ns['snapshot']()
    assert state['pid']==activation['pid']==request['pid'] and str(state['pid'])==f['assigned_editor_PID']
    assert state['world']==activation['world']==request['world']==f['map']
    q=ns['read'](OUT/'PRESERVE_REQUEST.json');prior=ns['read'](OUT/'PRESERVE_RESULT.json');readback=ns['read'](OUT/'COPY_RELOAD_FINAL_VERIFICATION.json')
    assert readback['passed'] and readback['binary_disk_reload_proven'] and all(readback['per_package_reloaded'].values())
    assert readback['actual_reload_receipt_sha256']==ns['sha'](OUT/'COPY_RELOAD_RESULT.json')
    assert state['dirty_content']==sorted(q['source_packages']) and not state['dirty_maps']
    assert state['paused'] and not state['autosave'] and not any(state['callbacks'].values()) and all(not a and not b for a,b in state['auto_flags'])
    assert not unreal.HoudiniPublicAPIBlueprintLib.get_api().is_session_valid(),'unexpected_live_official_session'
    command="Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'UnrealEditor.exe'} | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
    proc=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],capture_output=True,text=True,check=True,timeout=15)
    process=json.loads(proc.stdout)
    assert isinstance(process,dict) and process['ProcessId']==request['pid'] and 'Environmentpipeline.uproject' in process['CommandLine'],'unexpected_editor_process_set'
    for src in q['source_packages']:
        obj=unreal.find_object(None,ns['obj_path'](src));assert obj
        assert ns['object_state'](obj)==prior['source_states'][src],'original_buffer_changed_since_preservation'
        exp=ns['export_text'](obj,OUT/('SHUTDOWN_ORIGINAL_'+obj.get_name()+'.t3d'))
        assert Path(exp['path']).read_text(encoding='utf-8-sig')==Path(prior['source_exports'][src]['path']).read_text(encoding='utf-8-sig')
        if isinstance(obj,unreal.StaticMesh):assert ns['export_corner_attributes'](obj,OUT/'SHUTDOWN_ORIGINAL_ATTRIBUTES.fbx')==prior['source_corner_attributes']
    for p,s in q['protected_disk_sha256'].items():assert ns['sha'](p)==s,'protected_original_changed'
    assert ns['snapshot']()==state,'shutdown_preflight_changed_state'
    receipt=OUT/'NO_SAVE_SHUTDOWN_REQUESTED.json';assert not receipt.exists(),'no_blind_shutdown_retry'
    ns['write'](receipt,{'request_sha256':ns['sha'](REQUEST),'activation_sha256':ns['sha'](request['activation_path']),'state':state,'sole_os_process':process,
        'quit_method':'unreal.SystemLibrary.quit_editor()','save_requested':False,'forced_process_termination':False,
        'exact_original_buffers_to_discard_after_proven_recovery':q['source_packages'],'recovery_disk_readback_receipt_sha256':ns['sha'](OUT/'COPY_RELOAD_FINAL_VERIFICATION.json'),
        'process_exit_confirmed':False,'post_exit_disk_hash_verification_required':True})
    unreal.SystemLibrary.quit_editor()


if __name__=='__main__':run()
