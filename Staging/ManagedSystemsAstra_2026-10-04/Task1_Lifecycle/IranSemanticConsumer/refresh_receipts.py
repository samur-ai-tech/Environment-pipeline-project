"""Bookkeeping-only refresh after owners froze the same implementation bytes."""
import datetime, hashlib, json
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
before=OUT/'ReceiptRefresh'/stamp
before.mkdir(parents=True,exist_ok=False)
handoff=read(OUT/'SOURCE_HANDOFF.json')
checks=read(OUT/'SOURCE_CHECKS.json')
sample_refresh=[]
for name,digest in handoff['files'].items():
    if name=='SOURCE_CHECKS.json':continue
    assert sha(OUT/name)==digest,'Frozen task1 artifact changed: '+name
for name,digest in handoff['cross_owner_dependencies'].items():
    actual=sha(ROOT/name)
    if actual!=digest:
        assert name.endswith('PRODUCER_SAMPLE_CONTRACT_TEST_ONLY.json'),'Implementation dependency changed: '+name
        assert checks['dependencies'][name]==actual,'Refreshed test sample was not tested'
        sample_refresh.append({'file':name,'before_sha256':digest,'sha256':actual,
                               'kind':'Owner regenerated classified test sample; synthetic geometry, no native evidence'})
assert sha(ROOT/'Content/Python/geocity_bank_workflow.py')==handoff['before_sha256']
manifest=ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
assert sha(manifest)==handoff['active_runtime_manifest_sha256_preserved']
producer=ROOT/'Staging/PipelineSemanticRepair_2026-10-04/Completion'
combined_path=producer/'COMBINED_STAGING_VERIFICATION.json'
combined=read(combined_path);semantic=read(producer/'COMBINED_PAYLOAD.json')
for path,digest in [(Path(combined['candidate']),combined['candidate_sha256']),
                    (Path(semantic['candidate']),semantic['candidate_sha256']),
                    (Path(semantic['append']),semantic['append_sha256']),
                    (Path(combined['building_append']),combined['building_append_sha256']),
                    (Path(combined['building_manifest']),combined['building_manifest_sha256'])]:
    assert sha(path)==digest,str(path)
assert combined['candidate_sha256']=='02b770b47e7a4bc79f852f55e2f1ac1ab9001dbc13a8a97eeab1cdbe2a1bac15'
assert semantic['candidate_sha256']==combined['semantic_candidate_sha256']=='51e374e9fe0d86750105e4026a7a28e03b040a8da4be56ddc3d8d67c45a4ff9c'
assert combined['building_manifest_sha256']=='942a20d5552895b176db4e74ba1f60bd038196f7d723b11c11ab1258767f43d3'
for key in ('building_input_contract','building_source_binding'):
    assert sha(Path(combined[key]['path']))==combined[key]['sha256']
checks=read(OUT/'SOURCE_CHECKS.json')
assert checks['passed']==36 and checks['candidate_sha256']==handoff['candidate_sha256']
for name in ('SOURCE_HANDOFF.json','RESULT.json','RESULT.txt'):
    (before/name).write_bytes((OUT/name).read_bytes())
changed=[]
for name,old in list(handoff['interfaces'].items()):
    new=sha(ROOT/name)
    if old!=new:
        assert name.endswith('ConsumerIntegration/INTEGRATION_MANIFEST.json')
        changed.append({'file':name,'before_sha256':old,'sha256':new})
        handoff['interfaces'][name]=new
references=[combined_path,producer/'COMBINED_PAYLOAD.json',Path(combined['candidate']),Path(semantic['candidate']),
            Path(combined['building_append']),Path(combined['building_manifest'])]
handoff['joint_staging_references']={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in references}
for entry in sample_refresh:handoff['cross_owner_dependencies'][entry['file']]=entry['sha256']
handoff['receipt_refresh']={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Bookkeeping and cross-owner references only; all task1 implementation/test/patch/profile-proposal bytes unchanged',
    'preserved_previous_receipts':str(before.relative_to(OUT)).replace('\\','/'),'changed_interfaces':changed,
    'refreshed_test_samples':sample_refresh,
    'focused_offline_checks_rerun':36,'retained_prior_regression_checks':18,
    'joint_owner_report':'Combined staging context/source-loader checks reported PASS; this refresh verifies exact referenced bytes. It does not rerun Houdini or native checks.',
    'qualification_status':{'owner_reported_accepted':combined['building_accepted_count'],'owner_reported_rejected':combined['building_rejected_count']},
    'runtime_changed':False,'native_actions':False,'hda_actions':False,'activation':False}
handoff['files']['SOURCE_CHECKS.json']=sha(OUT/'SOURCE_CHECKS.json')
for name in ('SOURCE_HANDOFF.json','RESULT.json'):
    (OUT/name).write_text(json.dumps(handoff,indent=2)+'\n',encoding='utf-8')
text=(OUT/'RESULT.txt').read_text()
text+='\nReceipt-only refresh '+stamp+': building manifest '+combined['building_manifest_sha256']+'; semantic candidate '+semantic['candidate_sha256']+'; combined candidate '+combined['candidate_sha256']+'.36 focused offline checks rerun;18 previous retained regressions preserved. All task1 source/patch/runtime/seal/profile bytes unchanged. No Houdini/native actions or activation.\n'
(OUT/'RESULT.txt').write_text(text,encoding='utf-8')
refresh={**handoff['receipt_refresh'],'joint_staging_references':handoff['joint_staging_references'],
         'candidate_sha256_unchanged':handoff['candidate_sha256'],'patch_sha256_unchanged':handoff['patch_sha256'],
         'updated_handoff_sha256':sha(OUT/'SOURCE_HANDOFF.json')}
(OUT/'RECEIPT_REFRESH.json').write_text(json.dumps(refresh,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'RECEIPTS_REFRESHED_IMPLEMENTATION_FROZEN','changed_interfaces':changed,'focused_checks_rerun':36,'handoff_sha256':refresh['updated_handoff_sha256']}))
