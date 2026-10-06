"""Read-only pin checks; write only a Task1 bookkeeping receipt."""
import datetime, hashlib, json
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
handoff=read(OUT/'SOURCE_HANDOFF.json')
verified={}
for group in ('interfaces','cross_owner_dependencies','joint_staging_references'):
    for name,digest in handoff[group].items():
        assert sha(ROOT/name)==digest,name
        verified[name.replace('\\','/')]=digest
for name,digest in handoff['files'].items():assert sha(OUT/name)==digest,name
assert handoff['candidate_sha256']==sha(OUT/'geocity_bank_workflow.py')=='bf0ddff109964fe5c93a629bbcc149fb7887d317648f18dec8d2342c3c6d9c6f'
assert handoff['patch_sha256']==sha(OUT/'SOURCE_PATCH.diff')=='0c132d16751b45e66430a0b3fdde2bb786311e9800611b2fc5a3925a292df633'
owners=[ROOT/'Staging/ManagedSystemsAstra_2026-10-04/Task3_GroundGrass/IranSemanticConsumer/SOURCE_HANDOFF.json',
        ROOT/'Staging/PipelineSemanticRepair_2026-10-04/Completion/HANDOFF.json']
owner_readbacks=[]
for path in owners:
    data=read(path)
    for name,digest in data['files'].items():assert sha(path.parent/name)==digest,str(path.parent/name)
    owner_readbacks.append({'path':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':sha(path),'member_files_verified':len(data['files'])})
assert read(owners[0])['producer_candidate_sha256']=='51e374e9fe0d86750105e4026a7a28e03b040a8da4be56ddc3d8d67c45a4ff9c'
for name,digest in handoff['active_runtime_modules_preserved'].items():assert sha(ROOT/name)==digest,name
assert sha(ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json')==handoff['active_runtime_manifest_sha256_preserved']
result={'status':'FINAL_TASK1_FROZEN_PINS_MATCH_CURRENT_OWNER_HANDOFFS',
    'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'task1_handoff_sha256':sha(OUT/'SOURCE_HANDOFF.json'),
    'candidate_sha256':handoff['candidate_sha256'],'patch_sha256':handoff['patch_sha256'],
    'verified_dependency_pins':verified,'current_owner_handoffs_read':owner_readbacks,
    'reference_policy':'Task1 implementation/dependency pins remain stable. Owner handoffs are read snapshots; root/semantic may now seal the final aggregate referencing this Task1 handoff, avoiding reciprocal aggregate hash rewrites.',
    'focused_offline_checks_last_rerun':36,'retained_regression_checks':18,
    'runtime_changed':False,'runtime_resealed':False,'hda_actions':False,'native_actions':False,'new_activation':False}
(OUT/'FINAL_PIN_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'handoff_sha256':result['task1_handoff_sha256'],'owner_handoffs':owner_readbacks}))
