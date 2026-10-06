"""Offline measured normalization and immutable resume-save request."""
import hashlib
import json
import re
import runpy
from pathlib import Path

HERE=Path(__file__).resolve().parent;OUT=HERE/'DirtyOriginals_Transfer'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')


def prepare():
    request_file=OUT/'PRESERVE_RESUME_REQUEST_v2.json';assert not request_file.exists()
    q=read(OUT/'PRESERVE_REQUEST.json');prior=read(OUT/'PRESERVE_RESULT.json');diagnostic=read(OUT/'PRESERVE_PARTIAL_DIAGNOSTIC.json')
    assert not prior['passed'] and not prior['saved'] and diagnostic['passed']
    source=HERE/'resume_dirty_preservation.py';module=runpy.run_path(str(source))
    mapping=dict(zip(q['source_packages'],q['destinations']));rows=[];guids={};pins=dict(q['command_closure'])
    pins[str(source.resolve())]=sha(source)
    for p in (OUT/'PRESERVE_REQUEST.json',OUT/'PRESERVE_RESULT.json',OUT/'PRESERVE_PARTIAL_DIAGNOSTIC.json'):pins[str(p)]=sha(p)
    for row in diagnostic['rows']:
        src=row['source'];dst=row['destination']
        a=Path(prior['source_exports'][src]['path']);b=Path(row['export']['path'])
        pins[str(a)]=sha(a);pins[str(b)]=sha(b)
        original=a.read_text(encoding='utf-8-sig');copy=b.read_text(encoding='utf-8-sig');expected=original
        for old,new in mapping.items():expected=expected.replace(old,new)
        is_mesh='/Meshes/' in src
        left=module['canonical_t3d'](expected,ignore_root_lighting_guid=not is_mesh)
        right=module['canonical_t3d'](copy,ignore_root_lighting_guid=not is_mesh,allow_empty_import_subobject=is_mesh)
        assert left==right,('substantive_property_change',src)
        if not is_mesh:
            guids[src]={'source':re.findall(r'^\s*LightingGuid=([0-9A-F]{32})\s*$',original,re.MULTILINE)[0],'recovery':re.findall(r'^\s*LightingGuid=([0-9A-F]{32})\s*$',copy,re.MULTILINE)[0]}
        rows.append({'source':src,'recovery':dst,'full_normalized_named_property_tree_equal':True,
            'normalization':['exact source-to-recovery paths','sibling object/property declaration order']+(['exact recorded copied LightingGuid only'] if not is_mesh else ['exact two empty orphan Engine.AssetImportData declaration/definition nodes; retained authoritative FbxStaticMeshImportData_0 binding'])})
    normalization=OUT/'PRESERVE_NORMALIZATION.json';write(normalization,{'rows':rows,'identity_guid_deltas':guids,'substantive_values_changed':False,'native_mutations':False})
    pins[str(normalization)]=sha(normalization)
    request={'schema':'environmentpipeline.preserve_existing_resume_request.v1','status':'PREPARED_NOT_EXECUTED','pid':q['pid'],'world':q['world'],'manager_thread_id':q['manager_thread_id'],'operator_thread_id':q['operator_thread_id'],
        'script_path':str(source.resolve()),'script_sha256':sha(source),'preserve_helper_path':q['script_path'],'file_pins':pins,'destinations':q['destinations'],'identity_guid_deltas':guids,
        'activation_path':str(HERE.parents[1]/'Staging/ManagedSystemsAstra_2026-10-04/DirtyOriginals_RESUME_ACTIVATION.json'),
        'required_lease_activation':'PRESERVE_EXISTING_COPIES_ONLY','required_activation_scope':'PRESERVE_EXISTING_COPIES_ONLY',
        'no_duplicate_recreate_cleanup_original_save_reload_discard_shutdown':True,'operations':'Revalidate exact6 loaded buffers and complete measured normalized state; save only the3 already-created recovery packages. Stop on any drift. Fresh binary disk reload remains separate.'}
    write(request_file,request)
    print(json.dumps({'request':str(request_file),'request_sha256':sha(request_file),'script_sha256':sha(source),'normalization':str(normalization),'passed_objects':len(rows)}))


if __name__=='__main__':prepare()
