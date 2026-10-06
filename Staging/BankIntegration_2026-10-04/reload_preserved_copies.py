"""Phase 2: reload only the three saved recovery copies, never the originals."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=HERE/'DirtyOriginals_Transfer'
REQUEST=OUT/'COPY_RELOAD_REQUEST.json'


def run():
    request=json.loads(REQUEST.read_text(encoding='utf-8'))
    assert Path(__file__).resolve()==Path(request['script_path']).resolve()
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==request['script_sha256']
    for p,s in request['file_pins'].items(): assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==s,('readback_source_changed',p)
    helper=Path(request['preserve_helper_path']);ns={'__file__':str(helper),'__name__':'recovery_copy_readback_helpers'}
    exec(compile(helper.read_bytes(),str(helper),'exec'),ns)
    parser=Path(request['normalization_helper_path']);parser_ns={'__file__':str(parser),'__name__':'recovery_copy_readback_normalization'}
    exec(compile(parser.read_bytes(),str(parser),'exec'),parser_ns)
    import unreal
    import geocity_runtime_guard as guard
    activation=ns['read'](request['activation_path'])
    lease=[s for s in (ns['ROOT']/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1];f=ns['fields'](lease)
    assert activation['approved'] is True and activation['scope']==f['activation']=='RELOAD_RECOVERY_COPIES_ONLY'
    assert activation['request_sha256']==ns['sha'](REQUEST) and activation['script_sha256']==ns['sha'](__file__)
    assert activation['manager_thread_id']==f['manager_thread_id']==request['manager_thread_id']
    assert activation['operator_thread_id']==f['operator_thread_id']==request['operator_thread_id']
    assert f['OWNER']=='CODEX_BANK_INTEGRATION' and f['ordinary_generation_authorized']=='false' and activation['ordinary_generation_authorized'] is False
    q=ns['read'](OUT/'PRESERVE_REQUEST.json');prior=ns['read'](OUT/'PRESERVE_RESULT.json');saved=ns['read'](OUT/'PRESERVE_RESUME_RESULT.json')
    assert saved['passed'] and len(saved['saved'])==3
    mapping=dict(zip(q['source_packages'],q['destinations']))
    assert activation['destinations']==request['destinations']==q['destinations']
    before=ns['snapshot']()
    assert before['pid']==request['pid']==activation['pid'] and str(before['pid'])==f['assigned_editor_PID']
    assert before['world']==request['world']==activation['world']==f['map']
    assert before['dirty_content']==sorted(q['source_packages']) and not before['dirty_maps']
    assert before['paused'] and not before['autosave'] and not any(before['callbacks'].values()) and all(not a and not b for a,b in before['auto_flags'])
    originals={p:unreal.find_object(None,ns['obj_path'](p)) for p in mapping}
    assert all(originals.values())
    def sole_process():
        command="Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'UnrealEditor.exe'} | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress"
        completed=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],capture_output=True,text=True,check=True,timeout=15)
        processes=json.loads(completed.stdout)
        if isinstance(processes,dict):processes=[processes]
        assert len(processes)==1 and processes[0]['ProcessId']==request['pid'],'not_exact_sole_editor_process'
        assert 'Environmentpipeline.uproject' in processes[0]['CommandLine'],'unexpected_editor_project'
        return processes[0]
    os_before=sole_process()
    copy_disk={row['path']:row['sha256'] for row in saved['saved']}
    def verify_originals():
        guard.verify()
        assert ns['snapshot']()==before,'unexpected_state_change'
        for path,expected in q['protected_disk_sha256'].items(): assert ns['sha'](path)==expected
        for pkg,expected in copy_disk.items(): assert ns['sha'](ns['package_file'](pkg))==expected,'recovery_disk_changed'
        for src,obj in originals.items():
            assert ns['object_state'](obj)==prior['source_states'][src],('original_changed',src)
            exp=ns['export_text'](obj,OUT/('READBACK_ORIGINAL_'+obj.get_name()+'.t3d'))
            assert Path(exp['path']).read_text(encoding='utf-8-sig')==Path(prior['source_exports'][src]['path']).read_text(encoding='utf-8-sig')
    def verify_copies():
        result={}
        for src,dst in mapping.items():
            obj=unreal.find_object(None,ns['obj_path'](dst));assert obj and obj.get_outermost().get_path_name()==dst
            actual=ns['object_state'](obj)
            assert ns['normalized'](prior['source_states'][src],mapping)==ns['normalized'](actual,{})
            exp=ns['export_text'](obj,OUT/('READBACK_COPY_'+obj.get_name()+'.t3d'))
            source_text=Path(prior['source_exports'][src]['path']).read_text(encoding='utf-8-sig')
            for old,new in mapping.items():source_text=source_text.replace(old,new)
            target_text=Path(exp['path']).read_text(encoding='utf-8-sig')
            mesh=isinstance(obj,unreal.StaticMesh)
            if not mesh:
                actual_guids=re.findall(r'^\s*LightingGuid=([0-9A-F]{32})\s*$',target_text,re.MULTILINE)
                assert actual_guids==[request['identity_guid_deltas'][src]['recovery']],'recovery_guid_drift'
                expected_guids=re.findall(r'^\s*LightingGuid=([0-9A-F]{32})\s*$',source_text,re.MULTILINE)
                assert expected_guids==[request['identity_guid_deltas'][src]['source']],'source_guid_drift'
            assert parser_ns['canonical_t3d'](source_text,ignore_root_lighting_guid=not mesh)==parser_ns['canonical_t3d'](target_text,ignore_root_lighting_guid=not mesh,allow_empty_import_subobject=mesh),'reloaded_property_difference'
            if mesh:
                assert ns['export_corner_attributes'](obj,OUT/'READBACK_COPY_ATTRIBUTES.fbx')==prior['source_corner_attributes']
                assert obj.get_editor_property('asset_import_data').get_path_name()==ns['obj_path'](dst)+':FbxStaticMeshImportData_0'
            object_pointer=re.search(r'\(0x[0-9A-Fa-f]+\)',repr(obj))
            package_pointer=re.search(r'\(0x[0-9A-Fa-f]+\)',repr(obj.get_outermost()))
            assert object_pointer and package_pointer,'native_object_identity_not_observable'
            result[dst]={'state':actual,'text_export':exp,'disk_sha256':copy_disk[dst],'object_repr':repr(obj),'package_repr':repr(obj.get_outermost()),'object_pointer':object_pointer.group(),'package_pointer':package_pointer.group()}
        return result
    receipt=OUT/'COPY_RELOAD_RESULT.json';assert not receipt.exists(),'no_blind_reload_retry'
    result={'before':before,'sole_os_process_before':os_before,'request_sha256':ns['sha'](REQUEST),'activation_sha256':ns['sha'](request['activation_path']),'original_save_reload_discard':False,'passed':False}
    try:
        verify_originals();result['copies_before']=verify_copies();verify_originals()
        packages=[unreal.find_object(None,ns['obj_path'](p)).get_outermost() for p in q['destinations']]
        assert [p.get_path_name() for p in packages]==q['destinations']
        ns['write'](receipt,result)
        changed,error=unreal.EditorLoadingAndSavingUtils.reload_packages(packages,unreal.ReloadPackagesInteractionMode.ASSUME_NEGATIVE)
        result['reload_result']={'any_packages_reloaded':changed,'error':str(error)}
        assert changed and not str(error),'recovery_reload_failed'
        verify_originals();result['copies_after']=verify_copies();verify_originals()
        result['per_package_reloaded']={p:result['copies_before'][p]['object_pointer']!=result['copies_after'][p]['object_pointer'] and result['copies_before'][p]['package_pointer']!=result['copies_after'][p]['package_pointer'] for p in q['destinations']}
        assert all(result['per_package_reloaded'].values()),'not_all_three_native_package_and_object_identities_replaced'
        result['sole_os_process_after']=sole_process()
        assert result['sole_os_process_after']==os_before,'os_editor_process_changed'
        result['passed']=True;result['binary_disk_reload_proven']=True;result['after']=ns['snapshot']()
    except Exception as exc:
        result['error']=repr(exc);result['after']=ns['snapshot']();raise
    finally:ns['write'](receipt,result)
    return result


if __name__=='__main__': print(json.dumps(run()))
