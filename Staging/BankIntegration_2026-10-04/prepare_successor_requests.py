"""Create immutable file-only recovery request and bank source-change receipts."""
import ast
import copy
import csv
import datetime
import hashlib
import json
import runpy
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bank_contracts as C


def prepare():
    out=HERE/'DirtyOriginals_Transfer'
    request_path=out/'PRESERVE_REQUEST.json'
    assert not request_path.exists(),'immutable_request_exists'
    diagnostic=C.read(out/'DIAGNOSTIC.json')
    preflight=C.read(out/'OBJECT_STATE_PREFLIGHT.json')
    corners=C.read(out/'CORNER_ATTRIBUTE_PREFLIGHT.json')
    assert diagnostic['state_unchanged'] and preflight['source_api_preflight_passed'] and corners['passed']
    script=HERE/'preserve_dirty_originals.py'
    manifest_path=C.ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
    manifest=C.read(manifest_path)
    closure={str(script):C.sha(script),str(manifest_path):C.sha(manifest_path)}
    for row in manifest['modules'].values():
        p=C.ROOT/'Content/Python'/row['file'];assert C.sha(p)==row['sha256'];closure[str(p)]=row['sha256']
    for relative,entry in manifest['support_files'].items():
        p=C.ROOT/relative;expected=entry['sha256'] if isinstance(entry,dict) else entry
        assert C.sha(p)==expected;closure[str(p)]=expected
    startup=C.ROOT/'Content/Python'/manifest['startup']['file'];closure[str(startup)]=C.sha(startup)
    protected={r['disk_file']:r['disk_sha256'] for r in diagnostic['rows']}
    protected.update({r['path']:r['actual_sha256'] for r in diagnostic['protected_files']})
    packages=[r['path'].split('.')[0] for r in diagnostic['rows']]
    destination_root='/Game/Project/Shared/ModelBank/Prepared/Recovery_20261004_Plant07'
    request={'schema':'environmentpipeline.dirty_preserve_request.v1','status':'PREPARED_REVIEW_REQUIRED_NOT_EXECUTED',
        'manager_thread_id':C.read(HERE/'ASSIGNMENT.json')['system_owner'],'operator_thread_id':C.read(HERE/'ASSIGNMENT.json')['thread'],
        'pid':diagnostic['before']['pid'],'world':diagnostic['before']['world'],'script_path':str(script.resolve()),'script_sha256':C.sha(script),
        'command_closure':closure,'source_packages':packages,'destinations':[destination_root+'/'+p.rsplit('/',1)[1] for p in packages],
        'protected_disk_sha256':protected,
        'source_state_sha256':{p:hashlib.sha256(json.dumps(preflight['source_states'][p+'.'+p.rsplit('/',1)[1]],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest() for p in packages},
        'evidence':{str(out/n):C.sha(out/n) for n in ('DIAGNOSTIC.json','OBJECT_STATE_PREFLIGHT.json','CORNER_ATTRIBUTE_PREFLIGHT.json','CACHED_HELPERS_BEFORE_PATCH.json')},
        'required_activation_path':str(C.ROOT/'Staging/ManagedSystemsAstra_2026-10-04/DirtyOriginals_PRESERVE_ACTIVATION.json'),
        'required_activation_fields':['approved=true','scope=PRESERVE_ONLY','manager_thread_id','operator_thread_id','pid','world','request_sha256','script_sha256','destinations','ordinary_generation_authorized=false'],
        'required_lease_activation':'PRESERVE_ONLY','native_mutations_executed':False,'no_original_save_reload_discard_close':True,
        'readback':'Immediate source/copy raw LOD geometry, UV, full normalized T3D/subobject properties, Nanite, material settings, collision, exported LOD normals/tangents/binormals and named save checks. Binary disk reload is a separately activated second phase before any original discard.',
        'limits':['FBX export omits one zero-area source LOD0 triangle; raw topology/UV checksum retains it. No exported color layers exist for these three LODs; do not invent a color measurement.','No author/intent attribution is established. Copies retain unknown-author changes and are not catalog assets or placement approvals.']}
    for p in [script,HERE/'bank_batch_loader.py',HERE/'native_bank_ops.py',HERE/'apply_bank_configuration.py',HERE/'inspect_bank_startup.py',HERE/'acquire_bank_checkpoint.py']:
        ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
    C.write(request_path,request)
    checks=[]
    module=runpy.run_path(str(HERE/'apply_bank_configuration.py'))
    verify=module['assert_catalog_identity']
    source=C.read(C.SOURCE)
    with C.CSV.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    assert len(verify(source,rows))==len(source['rows']);checks.append('current_source_csv_identity_and_typed_agreement_pass')
    grown=copy.deepcopy(source); extra=copy.deepcopy(grown['rows'][0]);extra['asset_id']='verification_only_extra_id';extra['catalog_row_name']='verification_only_extra_row';extra['runtime']['Name']=extra['catalog_row_name'];grown['rows'].append(extra)
    grown_rows=copy.deepcopy(rows)+[copy.deepcopy(extra['runtime'])]
    assert len(verify(grown,grown_rows))==len(rows)+1;checks.append('dynamic_catalog_size_pass_in_memory_only')
    for label,bad_source,bad_rows in (
        ('missing_csv_row',source,rows[:-1]),
        ('duplicate_csv_row',source,rows[:-1]+[rows[0]]),
        ('duplicate_asset_identity',{'rows':source['rows']+[source['rows'][0]]},rows+[rows[0]])):
        try:verify(bad_source,bad_rows)
        except AssertionError:checks.append(label+'_rejected')
        else:raise AssertionError(label+'_was_not_rejected')
    changed=copy.deepcopy(rows);changed[0]['SelectionWeight']=str(float(changed[0]['SelectionWeight'])+1)
    try:verify(source,changed)
    except AssertionError:checks.append('typed_field_mismatch_rejected')
    else:raise AssertionError('typed_field_mismatch_accepted')
    patches={n:{'before_sha256':C.sha(HERE/'SourcePatchBefore_Succession'/n),'after_sha256':C.sha(HERE/n)} for n in ('native_bank_ops.py','apply_bank_configuration.py','acquire_bank_checkpoint.py','inspect_bank_startup.py')}
    C.write(HERE/'SUCCESSOR_SOURCE_PATCH.json',{'schema':'environmentpipeline.bank_successor_source_patch.v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'patches':patches,'checks':checks,'source_catalog_sha256':C.sha(C.SOURCE),'csv_sha256':C.sha(C.CSV),
        'native_execution':False,'system_sources_profiles_untouched':True,'cached_helpers_reloaded':False,
        'current_process_note':'PID32508 has old native_bank_ops cached; strict command loader must reject it after the disk patch. Reviewed fresh paused startup is required for later normal bank content operations; preservation script uses no cached bank helpers.',
        'changes':['Successor IDs resolved from assignments/activation, not old hard-coded manager.','Write preflight rejects inspection-only/paused activation and stale manager checkpoint.','Dynamic row count retains nonempty unique canonical IDs, exact row identity sets, typed source/CSV/native and before-hash agreement.','Bundle identity/digest and manager-profile before-hash checks happen before DataTable mutation.'],
        'old_unapplied_bundles':'Old NORMAL_CONFIGURATION receipts without catalog_identities are not silently accepted; build a new bundle after next actual changes.'})
    print(json.dumps({'request':str(request_path),'request_sha256':C.sha(request_path),'script_sha256':C.sha(script),'source_patch':str(HERE/'SUCCESSOR_SOURCE_PATCH.json'),'checks':checks}))


if __name__=='__main__':prepare()
