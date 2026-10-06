"""Read-only verification after the already performed recovery-copy reload."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent;OUT=HERE/'DirtyOriginals_Transfer'

def run():
    import unreal
    import geocity_runtime_guard as guard
    q=json.loads((OUT/'PRESERVE_REQUEST.json').read_text())
    helper=Path(q['script_path']);assert hashlib.sha256(helper.read_bytes()).hexdigest()==q['script_sha256']
    ns={'__file__':str(helper),'__name__':'recovery_readonly_verification'};exec(compile(helper.read_bytes(),str(helper),'exec'),ns)
    rr=ns['read'](OUT/'COPY_RELOAD_REQUEST.json');failed=ns['read'](OUT/'COPY_RELOAD_RESULT.json');prior=ns['read'](OUT/'PRESERVE_RESULT.json')
    assert failed['reload_result']=={'any_packages_reloaded':True,'error':''}
    assert failed['error']=="AssertionError('unexpected_extra_import_subobject_count')"
    parser=Path(rr['normalization_helper_path']);assert ns['sha'](parser)==rr['file_pins'][str(parser)]
    ps={'__file__':str(parser),'__name__':'recovery_readonly_normalization'};exec(compile(parser.read_bytes(),str(parser),'exec'),ps)
    lease=ns['fields']([s for s in (ns['ROOT']/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1])
    assert lease['activation']=='RELOAD_RECOVERY_COPIES_ONLY' and lease['manager_thread_id']==rr['manager_thread_id'] and lease['operator_thread_id']==rr['operator_thread_id']
    def process():
        cmd="Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'UnrealEditor.exe'} | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
        p=json.loads(subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',cmd],capture_output=True,text=True,check=True,timeout=15).stdout)
        assert isinstance(p,dict) and p['ProcessId']==rr['pid'] and 'Environmentpipeline.uproject' in p['CommandLine'];return p
    before=json.loads(json.dumps(ns['snapshot']()));os_before=process();guard.verify()
    assert before==failed['after'] and before['dirty_content']==sorted(q['source_packages']) and not before['dirty_maps']
    for p,s in rr['file_pins'].items():assert ns['sha'](p)==s
    for p,s in q['protected_disk_sha256'].items():assert ns['sha'](p)==s
    mapping=dict(zip(q['source_packages'],q['destinations']));rows=[]
    for src,dst in mapping.items():
        original=unreal.find_object(None,ns['obj_path'](src));copy=unreal.find_object(None,ns['obj_path'](dst));assert original and copy
        assert ns['object_state'](original)==prior['source_states'][src]
        assert ns['normalized'](prior['source_states'][src],mapping)==ns['normalized'](ns['object_state'](copy),{})
        e=ns['export_text'](original,OUT/('FINAL_ORIGINAL_'+original.get_name()+'.t3d'))
        text=Path(e['path']).read_text(encoding='utf-8-sig')
        assert text==Path(prior['source_exports'][src]['path']).read_text(encoding='utf-8-sig')
        for old,new in mapping.items():text=text.replace(old,new)
        e=ns['export_text'](copy,OUT/('FINAL_COPY_'+copy.get_name()+'.t3d'))
        actual=Path(e['path']).read_text(encoding='utf-8-sig');mesh=isinstance(copy,unreal.StaticMesh)
        assert ps['canonical_t3d'](text,ignore_root_lighting_guid=not mesh)==ps['canonical_t3d'](actual,ignore_root_lighting_guid=not mesh),'substantive_property_difference_after_disk_reload'
        if mesh:
            assert 'Name="AssetImportData"' not in actual,'unexpected_default_orphan_retained'
            assert copy.get_editor_property('asset_import_data').get_path_name()==ns['obj_path'](dst)+':FbxStaticMeshImportData_0'
            assert ns['export_corner_attributes'](copy,OUT/'FINAL_COPY_ATTRIBUTES.fbx')==prior['source_corner_attributes']
            assert ns['export_corner_attributes'](original,OUT/'FINAL_ORIGINAL_ATTRIBUTES.fbx')==prior['source_corner_attributes']
        else:
            assert re.findall(r'^\s*LightingGuid=([0-9A-F]{32})\s*$',text,re.MULTILINE)==[rr['identity_guid_deltas'][src]['source']]
            assert re.findall(r'^\s*LightingGuid=([0-9A-F]{32})\s*$',actual,re.MULTILINE)==[rr['identity_guid_deltas'][src]['recovery']]
        native_obj=re.search(r'\(0x[0-9A-Fa-f]+\)',repr(copy)).group();native_pkg=re.search(r'\(0x[0-9A-Fa-f]+\)',repr(copy.get_outermost())).group()
        earlier=failed['copies_before'][dst]
        assert native_obj!=earlier['object_pointer'] and native_pkg!=earlier['package_pointer'],'package_not_reloaded'
        rows.append({'path':dst,'object_pointer_before':earlier['object_pointer'],'object_pointer_after':native_obj,'package_pointer_before':earlier['package_pointer'],'package_pointer_after':native_pkg,'binary_reloaded':True,'full_property_geometry_material_match':True,'text_export':e})
    after=json.loads(json.dumps(ns['snapshot']()));os_after=process();assert before==after and os_before==os_after
    result={'schema':'environmentpipeline.recovery_binary_readback_final.v1','passed':True,'binary_disk_reload_proven':True,'reload_operation_repeated':False,
        'actual_reload_receipt':str(OUT/'COPY_RELOAD_RESULT.json'),'actual_reload_receipt_sha256':ns['sha'](OUT/'COPY_RELOAD_RESULT.json'),
        'before':before,'after':after,'sole_os_process_before':os_before,'sole_os_process_after':os_after,'rows':rows,
        'per_package_reloaded':{r['path']:r['binary_reloaded'] for r in rows},'originals_and_disks_unchanged':True,'native_mutations':False,
        'resolved_failure':'The one unused empty AssetImportData default subobject is absent after binary reload. The actual FbxStaticMeshImportData_0 binding and ALL normalized substantive properties match; the readback parser now uses strict no-orphan-exclusion equality.'}
    ns['write'](OUT/'COPY_RELOAD_FINAL_VERIFICATION.json',result)
    print(json.dumps({'passed':True,'binary_disk_reload_proven':True,'per_package_reloaded':result['per_package_reloaded'],'state_unchanged':True,'receipt_sha256':ns['sha'](OUT/'COPY_RELOAD_FINAL_VERIFICATION.json')}))

if __name__=='__main__':run()
