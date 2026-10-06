"""Close only this native import assignment; preserve failed unsaved buffers."""
import json,sys,os
from datetime import datetime,timezone
from pathlib import Path
import unreal
m=sys.modules['modular_native_adapter_v004_20261005']
activation,state=m.resume_boundary()
result=m.read(m.HERE/'RESUME_RESULT_v004.json')
assert result['status']=='COMPLETE_WITH_REPAIR_QUEUE'
assert (len(result['imported_saved']),len(result['reused_existing']),len(result['failed']))==(569,34,6)
dirty=m.N.dirty()
failed_paths={f['native_package'] for f in result['failed']}
assert set(dirty['content'])==failed_paths and dirty['maps']==[],dirty
assert all(not m.C.package_file(p).exists() for p in failed_paths)
assert not ({r['native_package'] for r in result['imported_saved']} & set(dirty['content']))
for path,expected in m.protected_files(activation['preservation_path']).items():assert m.sha(path)==expected,('protected_file_changed',path)
families=[]
for family in m.RESUME_REQUEST['families']:
    receipts=[]
    for part in family['parts']:
        p=m.HERE/'Receipts'/family['id']/(part['name']+'.json')
        if p.is_file():
            r=m.read(p)
            assert r['named_saved'] and m.C.package_file(r['native_package']).exists()
            receipts.append(r)
    failures=[f for f in result['failed'] if f['family']==family['id']]
    assert len(receipts)+len(failures)==len(family['parts'])
    summary={'family_id':family['id'],'saved_parts':len(receipts),'failed_parts':len(failures),'expected_parts':len(family['parts'])}
    families.append(summary)
    if family['id'] in ('H0910','H0911'):continue
    report={'schema':'environmentpipeline.modular_native_family_readback.v1','family_id':family['family_id'],
            'parent_asset_id':family['parent_asset_id'],'source_family_sha256':family['source_family_sha256'],
            'request_sha256':activation['request_sha256'],'parts':receipts,'expected_part_count':len(family['parts']),
            'imported_part_count':len(receipts),'complete_native_import':not failures,'failed_parts':failures,
            'native_reloaded':False,'fresh_process_reopened':False,'procedural_eligible':False,
            'visual_fidelity_verified':False,'holds_preserved':True,'state':state}
    m.write(m.HERE/'Receipts'/family['id']/'FAMILY.json',report)
utc=datetime.now(timezone.utc).isoformat()
queue={'status':'AWAITING_REPAIR','count':6,'failures':result['failed'],'failed_packages_saved':False,'unsaved_buffers_preserved':True}
m.write(m.HERE/'REPAIR_QUEUE_v004.json',queue)
result.update(completed_utc=utc,families=families,dirty_remaining=dirty,existing34_unchanged=True,
              protected_files_unchanged=True,unattempted=0,active_import_callbacks=0,
              repair_queue=str(m.HERE/'REPAIR_QUEUE_v004.json'),editor_left_open=True)
m.write(m.HERE/'RESUME_RESULT_v004.json',result)
lines=['Native building-kit import complete: all 609 parts accounted for.',
       'Successfully imported and named-saved: 569 parts with source material and texture bindings.',
       'Reused unchanged: 34 saved parts (H0910: 14; H0911: 20).',
       'Failed, isolated and awaiting repair: 6 parts; exact IDs and errors in REPAIR_QUEUE_v004.json.',
       'Each failed import lost one triangle relative to its source and remains unsaved.',
       'Shared bank: /Game/Project/Shared/ModelBank/Prepared/Modular',
       'Originals, holds, maps, geographic placement, Houdini and generation preserved.',
       'Editor PID21608 remains open with exactly the six failed unsaved meshes; native authoring is inactive.']
(m.HERE/'IMPORT_REPORT_v004.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
activation['native_authorized_now']=False
activation['status']='IMPORT_COMPLETE_REPAIR_QUEUE'
activation['completed_utc']=utc
m.write(m.HERE/'RESUME_ACTIVATION_v004.json',activation)
with (m.ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').open('a',encoding='utf-8') as f:
    f.write('\n'+utc+' OWNER=CODEX_BANK_INTEGRATION operator_thread_id='+activation['operator_thread_id']+
            ' task=modular_bank assigned_editor_PID=21608 activation=IMPORT_COMPLETE_REPAIR_QUEUE native_authorized_now=false ordinary_generation_authorized=false preserved_failed_unsaved_meshes=6 running_imports=0\n')
print(json.dumps({'new_imported_saved':569,'reused':34,'repair_queue':6,'remaining_unattempted':0,'dirty_content':len(dirty['content']),'dirty_maps':0,'protected_files_unchanged':True,'families':families}))
