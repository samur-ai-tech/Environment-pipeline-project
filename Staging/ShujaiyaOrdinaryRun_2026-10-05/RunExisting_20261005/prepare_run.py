from pathlib import Path
import json,os,hashlib,shutil,subprocess
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
ids=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command','ConvertTo-Json -Compress -InputObject @((Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue).Id)'],text=True))
assert not [p for p in ids if p is not None],ids
thread=os.environ['CODEX_THREAD_ID']
utc=datetime.now(timezone.utc).isoformat()
exit_receipt=read(HERE/'IMPORT_EDITOR_EXIT.json')
for p,expected in exit_receipt['saved_import_packages'].items():assert sha(ROOT/'Content'/(p[6:]+'.uasset'))==expected
lease=ROOT/'Staging/ModelBank/EDITOR_OWNER.txt'
assert any(x+thread in lease.read_text().splitlines()[-1] for x in ('operator_thread_id=','released_by='))
with lease.open('a',encoding='utf-8') as f:f.write('\n'+utc+' OWNER=NONE released_by='+thread+' exited_editor_PID=21608 scope=failed_import_buffers_only shutdown_saves=0\n')
profile_path=ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json'
profile=read(profile_path)
assert 'source_family_registry_ref' not in profile['building_assembly_contract']
before=Path('\\\\?\\'+str(HERE/'Before'));before.mkdir(exist_ok=True)
backup_roots=['Content/Project/Areas/GazaShujaiya','Content/Project/Shared/SurfacePainting','Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02']
pins={}
for rel in backup_roots:
    folder=ROOT/rel
    if not folder.exists():continue
    for src in folder.rglob('*'):
        if src.is_file():
            dest=before/src.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():assert sha(dest)==sha(src),str(dest)
            else:shutil.copy2(src,dest)
            pins[str(src.relative_to(ROOT))]=sha(src)
assignment_path=ROOT/'Staging/ManagedSystemsAstra_2026-10-04/ASSIGNMENTS.json'
shutil.copy2(assignment_path,before/'ASSIGNMENTS.json')
assignment=read(assignment_path)
assignment['manager_thread_id']=thread
for row in assignment['tasks']:
    if row['id']=='task4':row.update(thread_id=thread,status='USER_AUTHORIZED_EXISTING_CONFIGURATION_RUN',mode='ONE_OPERATOR_CURRENT_AREA')
assignment['current_scoped_run']={'thread_id':thread,'utc':utc,'authorization':'Run the existing system as currently configured','map':profile['map'],'receipt':str(HERE/'RUN_AUTHORIZATION.json'),'new_modular_families_connected':False,'other_tasks_resumed':False}
write(assignment_path,assignment)
ledger=profile_path.parent/'ROADBLD_WORKFLOW_STATE.json'
candidate=ROOT/'Staging/ManagedAstra_2026-10-03/ExteriorIntervalStop_20261003T213017494226Z/ROADBLD_WORKFLOW_STATE.json'
old=read(ledger);replacement=read(candidate)
assert old['pid']==33168 and old['saved'] is False
assert len(replacement['staged_actor_paths'])==132
assert old['source_sha256']==replacement['source_sha256']
shutil.copy2(candidate,ledger)
write(HERE/'LEDGER_RECONCILIATION.json',{'old_preserved':str(before/ledger.relative_to(ROOT)),'new_source':str(candidate),'new_sha256':sha(ledger),'reason':'Prior PID33168 unsaved road attempt was discarded. Exact132 saved road actors and tags verified live before orderly close. No scene changes.','scope':'Existing saved road ownership only'})
manifest=ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
map_file=ROOT/'Content'/(profile['map'][6:]+'.umap')
auth={'status':'STARTUP_AUTHORIZED','utc':utc,'manager_thread_id':thread,'operator_thread_id':thread,
      'map':profile['map'],'map_sha256':sha(map_file),'profile':str(profile_path),'profile_sha256':sha(profile_path),
      'manifest_sha256':sha(manifest),'native_modular_integration':False,'ordinary_generation_authorized':True,
      'scope':'One retained ordinary generation of existing GazaShujaiya configuration, named saves and visible result; no source or profile edit','backup':str(before)}
write(HERE/'BEFORE_MANIFEST.json',pins);write(HERE/'RUN_AUTHORIZATION.json',auth)
print(json.dumps(auth))
