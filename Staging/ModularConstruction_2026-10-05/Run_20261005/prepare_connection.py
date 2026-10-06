from pathlib import Path
import json,hashlib,shutil,subprocess,sys,os
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
AUDIT=HERE.parent/'ContractAudit'
BANK=ROOT/'Staging/BankIntegration_2026-10-04/ModularNative_2026-10-05'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def ref(p):return {'path':str(p),'sha256':sha(p)}
before=HERE/'Before';before.mkdir(exist_ok=True)
for name in ['STAGED_NATIVE_REGISTRY_REF.json','normalize_bank_readback.py','bind_native_families.py']:
    dst=before/name
    if not dst.exists():shutil.copy2(AUDIT/name,dst)
result=read(BANK/'RESUME_RESULT_v004.json')
complete=[f['family_id'] for f in result['families'] if f['failed_parts']==0]
assert len(complete)==18 and not {'H0017','H0019'} & set(complete)
request=BANK/'NATIVE_IMPORT_REQUEST_v003.json'
text=(AUDIT/'normalize_bank_readback.py').read_text()
text=text.replace('APPROVED_REQUESTS = {','APPROVED_REQUESTS = {\n    '+repr(sha(request))+": BANK/'NATIVE_IMPORT_REQUEST_v003.json',")
old="'actual_bank_part_receipt_ref': reference(BANK/'Receipts'/args.family/(name+'.json'))}"
new="'actual_bank_part_receipt_ref': reference(BANK/'Receipts'/args.family/(name+'.json')), 'import_source': raw.get('import_source',raw['source']), 'import_source_sha256': raw.get('import_source_sha256',raw['source_sha256']), 'import_adaptation_receipt': raw.get('import_adaptation_receipt')}"
assert old in text;text=text.replace(old,new)
(AUDIT/'normalize_bank_readback_v004.py').write_text(text,encoding='utf-8')
bind=(AUDIT/'bind_native_families.py').read_text().replace("HERE / 'normalize_bank_readback.py'","HERE / 'normalize_bank_readback_v004.py'")
(AUDIT/'bind_native_families_v004.py').write_text(bind,encoding='utf-8')
args=[sys.executable,str(AUDIT/'bind_native_families_v004.py'),'--execution-mode','connection']
for family in complete:args+=['--family',family]
run=subprocess.run(args,capture_output=True,text=True)
(HERE/'BINDING_LOG.txt').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
assert run.returncode==0,run.stderr
bound=json.loads(run.stdout);registry_ref=bound['registry_ref'];registry=read(Path(registry_ref['path']))
enabled=[e for e in registry['families'] if e['enabled']]
assert len(enabled)==18 and len(registry['staged_native_bindings'])==18
assert {e['family_id'].split('.')[1] for e in enabled}==set(complete)
profile_path=ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json'
profile=read(profile_path);shutil.copy2(profile_path,before/'AREA_PROFILE.json')
failure=read(ROOT/'Staging/ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/RESULT.json')
changes={}
for key,pair in failure['normal_binding_mismatch'].items():
    assert profile['surface_normal_overrides'][key]['copy']==pair['expected']
    path=pair['actual'];assert '/EpicResident2K/' in path
    native=ROOT/'Content'/(path.split('.')[0][6:]+'.uasset');assert native.is_file()
    profile['surface_normal_overrides'][key]['copy']=path
    profile['surface_normal_overrides'][key]['current_native_package_sha256']=sha(native)
    profile['surface_normal_overrides'][key]['binding_reconciliation_receipt']=str(HERE/'PROFILE_CHANGE.json')
    changes[key]=pair
profile['building_assembly_contract']['source_family_registry_ref']=registry_ref
write(HERE/'PROPOSED_AREA_PROFILE.json',profile)
plan=read(HERE.parent/'Bindings/NATIVE_BINDING_PLAN.json')
hda=Path(plan['new_external_source']['path']);assert sha(hda)==plan['new_external_source']['sha256']
native_hda=Path(plan['native_hda_before']['original']['path'])
assert sha(native_hda)==plan['native_hda_before']['original']['sha256']
shutil.copy2(native_hda,before/native_hda.name)
auth={'status':'PREPARED','utc':datetime.now(timezone.utc).isoformat(),'operator_thread_id':os.environ['CODEX_THREAD_ID'],
 'authorization':'Direct user requested Houdini construction using the newly imported models and an actual visible run',
 'map':profile['map'],'family_ids':complete,'excluded_incomplete':['H0017','H0019'],
 'native_saved_parts_in_complete_families':sum(x['native_part_count'] for x in registry['staged_native_bindings']),
 'registry_ref':registry_ref,'profile_path':str(profile_path),'profile_before_sha256':sha(profile_path),
 'proposed_profile_ref':ref(HERE/'PROPOSED_AREA_PROFILE.json'),'native_hda':plan['native_hda_identity'],
 'native_hda_before_sha256':sha(native_hda),'external_hda_ref':ref(hda),'source_changes':False,
 'canonical_holds_preserved':True,'runtime_source_changes':False,'ordinary_generation_authorized':True}
write(HERE/'PROFILE_CHANGE.json',{'normal_reference_reconciliation':changes,'textures_modified':False,'new_family_registry_ref':registry_ref,'area':'GazaShujaiya'})
write(HERE/'CONNECTION_AUTHORIZATION.json',auth)
print(json.dumps({'complete_families':len(complete),'native_parts':auth['native_saved_parts_in_complete_families'],'registry':registry_ref,'status':auth['status']}))
