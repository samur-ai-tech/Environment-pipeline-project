"""Reviewed continuation for exact already-created Plant07 recovery buffers."""
import hashlib
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=HERE/'DirtyOriginals_Transfer'
REQUEST=OUT/'PRESERVE_RESUME_REQUEST.json'


def canonical_t3d(text,ignore_root_lighting_guid=False,allow_empty_import_subobject=False):
    """Order-independent object records, retaining all property values/indices."""
    roots=[];stack=[]
    for line in text.splitlines():
        line=line.strip()
        if not line:continue
        if line.startswith('Begin Object '):
            node={'header':line,'properties':[],'children':[]}
            (stack[-1]['children'] if stack else roots).append(node);stack.append(node)
        elif line=='End Object':
            assert stack,'unbalanced_t3d';stack.pop()
        else:
            assert stack,'property_outside_object'
            stack[-1]['properties'].append(line)
    assert not stack and len(roots)==1,'incomplete_t3d'
    root=roots[0]
    if ignore_root_lighting_guid:
        guid=[p for p in root['properties'] if p.startswith('LightingGuid=')]
        assert len(guid)==1 and re.fullmatch(r'LightingGuid=[0-9A-F]{32}',guid[0]),'unexpected_lighting_guid'
        root['properties'].remove(guid[0]);root['properties'].append('LightingGuid=PER_COPY_IDENTITY')
    if allow_empty_import_subobject:
        extra=[c for c in root['children'] if re.search(r'\bName="AssetImportData"(?: |$)',c['header'])]
        assert len(extra)==2,'unexpected_extra_import_subobject_count'
        assert sum('Class=/Script/Engine.AssetImportData ' in c['header'] for c in extra)==1
        assert all(not c['children'] and not c['properties'] for c in extra),'extra_import_subobject_has_data'
        assert all(":AssetImportData'" in c['header'] for c in extra)
        assert not any(p.startswith('AssetImportData=') and ":AssetImportData'" in p for p in root['properties']),'extra_import_subobject_is_active'
        import_binding=[p for p in root['properties'] if p.startswith('AssetImportData=')]
        assert len(import_binding)==1 and "FbxStaticMeshImportData_0'" in import_binding[0],'authoritative_import_data_binding_changed'
        root['children']=[c for c in root['children'] if c not in extra]
    def normalize(node):
        return [node['header'],sorted(node['properties']),sorted((normalize(c) for c in node['children']),key=lambda n:json.dumps(n,sort_keys=True))]
    return normalize(root)


def run():
    request=json.loads(REQUEST.read_text(encoding='utf-8'))
    assert Path(__file__).resolve()==Path(request['script_path']).resolve()
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==request['script_sha256']
    for path,expected in request['file_pins'].items(): assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected,('resume_file_changed',path)
    helper=Path(request['preserve_helper_path']);ns={'__file__':str(helper),'__name__':'reviewed_preservation_helpers'}
    exec(compile(helper.read_bytes(),str(helper),'exec'),ns)
    import unreal
    import geocity_runtime_guard as guard
    activation=ns['read'](request['activation_path'])
    assert activation['approved'] is True and activation['scope']=='PRESERVE_EXISTING_COPIES_ONLY'
    assert activation['request_sha256']==ns['sha'](REQUEST) and activation['script_sha256']==ns['sha'](__file__)
    lease=[s for s in (ns['ROOT']/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1]
    f=ns['fields'](lease)
    assert f['activation']=='PRESERVE_EXISTING_COPIES_ONLY' and f['OWNER']=='CODEX_BANK_INTEGRATION'
    assert f['manager_thread_id']==activation['manager_thread_id']==request['manager_thread_id']
    assert f['operator_thread_id']==activation['operator_thread_id']==request['operator_thread_id']
    assert f['ordinary_generation_authorized']=='false' and activation['ordinary_generation_authorized'] is False
    assert f['assigned_editor_PID']==str(request['pid'])==str(activation['pid'])
    q=ns['read'](OUT/'PRESERVE_REQUEST.json');prior=ns['read'](OUT/'PRESERVE_RESULT.json')
    assert prior['passed'] is False and prior['saved']==[] and prior['created']==q['destinations']
    mapping=dict(zip(q['source_packages'],q['destinations']))
    assert activation['destinations']==request['destinations']==q['destinations']
    state=ns['snapshot']()
    assert state['pid']==request['pid'] and state['world']==request['world']==activation['world']==f['map']
    assert state==prior['after'],'partial_native_state_changed'
    originals={p:unreal.find_object(None,ns['obj_path'](p)) for p in mapping}
    copies={p:unreal.find_object(None,ns['obj_path'](dst)) for p,dst in mapping.items()}
    assert all(originals.values()) and all(copies.values())
    assert all(not ns['package_file'](dst).exists() for dst in mapping.values()),'unexpected_already_saved_copy'
    receipt=OUT/'PRESERVE_RESUME_RESULT.json';assert not receipt.exists(),'no_blind_resume_retry'
    result={'request_sha256':ns['sha'](REQUEST),'activation_sha256':ns['sha'](request['activation_path']),'before':state,'saved':[],'originals_saved_reloaded_discarded':False,'binary_disk_reload_proven':False,'passed':False}
    def verify(label):
        guard.verify()
        current=ns['snapshot']()
        assert {k:v for k,v in current.items() if k!='dirty_content'}=={k:v for k,v in state.items() if k!='dirty_content'},('native_state_drift',label)
        assert set(q['source_packages']).issubset(current['dirty_content'])
        assert set(current['dirty_content']).issubset(set(q['source_packages']+q['destinations']))
        for path,expected in q['protected_disk_sha256'].items(): assert ns['sha'](path)==expected
        for path,expected in request['file_pins'].items(): assert ns['sha'](path)==expected
        for src,dst in mapping.items():
            assert ns['object_state'](originals[src])==prior['source_states'][src],('original_state_drift',label,src)
            assert ns['normalized'](prior['source_states'][src],mapping)==ns['normalized'](ns['object_state'](copies[src]),{}),('copy_state_drift',label,src)
            e=ns['export_text'](originals[src],OUT/('RESUME_ORIGINAL_'+originals[src].get_name()+'.t3d'))
            original_text=Path(e['path']).read_text(encoding='utf-8-sig')
            prior_text=Path(prior['source_exports'][src]['path']).read_text(encoding='utf-8-sig')
            assert original_text==prior_text,('original_export_drift',label,src)
            expected_text=original_text
            for old,new in mapping.items():expected_text=expected_text.replace(old,new)
            e=ns['export_text'](copies[src],OUT/('RESUME_COPY_'+copies[src].get_name()+'.t3d'))
            copy_text=Path(e['path']).read_text(encoding='utf-8-sig')
            is_mesh=isinstance(copies[src],unreal.StaticMesh)
            if not is_mesh:
                original_guid=re.findall(r'^\s*LightingGuid=([0-9A-F]{32})\s*$',original_text,re.MULTILINE)
                copy_guid=re.findall(r'^\s*LightingGuid=([0-9A-F]{32})\s*$',copy_text,re.MULTILINE)
                assert original_guid==[request['identity_guid_deltas'][src]['source']] and copy_guid==[request['identity_guid_deltas'][src]['recovery']],'unreviewed_guid_delta'
            else:
                assert originals[src].get_editor_property('asset_import_data').get_path_name()==ns['obj_path'](src)+':FbxStaticMeshImportData_0'
                assert copies[src].get_editor_property('asset_import_data').get_path_name()==ns['obj_path'](dst)+':FbxStaticMeshImportData_0'
            assert canonical_t3d(expected_text,ignore_root_lighting_guid=not is_mesh)==canonical_t3d(copy_text,ignore_root_lighting_guid=not is_mesh,allow_empty_import_subobject=is_mesh),('substantive_export_difference',label,src)
            if is_mesh:
                assert ns['export_corner_attributes'](originals[src],OUT/'RESUME_ORIGINAL_ATTRIBUTES.fbx')==prior['source_corner_attributes']
                assert ns['export_corner_attributes'](copies[src],OUT/'RESUME_COPY_ATTRIBUTES.fbx')==prior['source_corner_attributes']
    try:
        verify('before_any_save')
        ns['write'](receipt,result)
        for src,dst in mapping.items():
            assert unreal.EditorAssetLibrary.save_asset(dst,only_if_is_dirty=True)
            result['saved'].append({'path':dst,'sha256':ns['sha'](ns['package_file'](dst))});ns['write'](receipt,result)
            verify('after_save_'+dst)
        result['after']=ns['snapshot']()
        assert result['after']['dirty_content']==sorted(q['source_packages'])
        result['passed']=True
        result['source_states']=prior['source_states'];result['source_corner_attributes']=prior['source_corner_attributes']
        result['copies_saved_but_disk_deserialization_pending']=True
    except Exception as exc:
        result['error']=repr(exc);result['after']=ns['snapshot']();raise
    finally:ns['write'](receipt,result)
    return result


if __name__=='__main__':print(json.dumps(run()))
