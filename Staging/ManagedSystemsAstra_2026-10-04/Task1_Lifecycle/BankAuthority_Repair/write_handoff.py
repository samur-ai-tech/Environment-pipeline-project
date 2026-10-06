"""Freeze this bounded supplement only; never seal or operate the runtime."""
import datetime
import difflib
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=['Content/Python/geocity_bank_workflow.py','Content/Python/geocity_editor_action.py','Staging/SystemCompletion_2026-10-04/launch_editor.ps1']
changes=[];patch=[]
for name in files:
    path=ROOT/name;before=OUT/'Before'/path.name
    changes.append({'file':name,'before_sha256':sha(before),'sha256':sha(path)})
    patch.extend(difflib.unified_diff(before.read_text().splitlines(True),path.read_text().splitlines(True),fromfile='before/'+name,tofile=name))
(OUT/'SOURCE_CHANGES.patch').write_text(''.join(patch),encoding='utf-8')
manifest=ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
assert sha(manifest)==sha(OUT/'Before/geocity_runtime_manifest.json'),'Manager seal changed during supplement; reconcile before freeze'
checks={name:json.loads((OUT/name).read_text(encoding='utf-8-sig')) for name in ['SOURCE_CHECKS.json','LAUNCHER_CHECKS.json','BaselineRegression/SOURCE_CHECKS.json']}
interface=ROOT/'Staging/ManagedSystemsAstra_2026-10-04/Task2_Roads/ROAD_LANDSCAPE_INTERFACE.json'
receipt={
    'schema':'environmentpipeline.task1_bank_authority_supplement.v1',
    'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'status':'SOURCE_FROZEN_READY_FOR_MANAGER_REVIEW_NATIVE_NOT_RUN',
    'task_thread_id':'01a106e8-ef65-78e0-aa96-f419393ebd6c',
    'manager_thread_id':'01a106bc-2fde-7f23-9aa7-8ba413dc6245',
    'sources':changes,
    'existing_combined_manifest_sha256':sha(manifest),'manifest_resealed':False,
    'preserved_baseline':'Before/ contains exact three accepted source files, prior combined seal and supplemental pointer; older accepted receipts untouched',
    'bank_contract':{
        'startup':'Same reviewed launcher and mandatory map/profile/manifest hashes; bank operator resolved against bank assignment plus root BANK_ACTIVATION. Startup OWNER=CODEX_MANAGED_SYSTEMS_STARTUP task=bank, exact actual PID and awaiting activation. Inspection cannot generate.',
        'content_lease_owner':'CODEX_BANK_INTEGRATION',
        'content_scope':'Existing bank-owned native import/material/catalog preflight and EDITOR_ACQUIRED.json remain bank/root responsibility; task1 does not authorize or implement these operations.',
        'lease_template':'OWNER=CODEX_BANK_INTEGRATION manager_thread_id=01a106bc-2fde-7f23-9aa7-8ba413dc6245 operator_thread_id=01a1067c-5012-7550-b449-015b53c9d726 task=bank assigned_editor_PID=<actual> map=<exact original map> activation=MANAGER_ACTIVATED',
        'activation_file':'Staging/ManagedSystemsAstra_2026-10-04/BANK_ACTIVATION.json',
        'required_generation_fields':{'native_authorized_now':True,'ordinary_generation_authorized':True,'assigned_editor_PID':'actual integer PID matching lease and os.getpid()','map':'exact named original map matching lease and active world'},
        'existing_fields_checked':['schema','manager_thread_id','bank_thread_id','scope_receipt','native_save_scope'],
        'imports_only':'Root may activate the exact bank native content lease and native_authorized_now while ordinary_generation_authorized remains false/missing. Menu, direct lifecycle guard and public run reject generation until it is literal true. Public run preflight rejects before constructing GeoCityRun, history/workflow writes, ACTIVE registration or failure cleanup/Engine mutations. Root alone integrates bank catalog/profile patches first.',
        'task4':'Existing exact task4 generation and launcher path preserved; no bank masquerading as task4 or OWNER=NONE'
    },
    'landscape_interface':{'receipt':str(interface.relative_to(ROOT)).replace('\\','/'),'receipt_sha256':sha(interface),
        'callback':'GeoCityRun.current_road_landscape_authority bound method, passed as landscape_authority= to task2 build',
        'resolution':'Fresh official_landscapes(self.wrapper) before build and on callback. Exactly one source-bound current Landscape, exact accounted prior list and owner, no unknown loaded Landscapes, no suffix inference or dependency on cooked_landscape.',
        'evidence_schema':'environmentpipeline.current_road_landscape.v1','parent_receipt_field':'current_road_landscape_authority','provider_receipt_field':'current_landscape_authority',
        'prior_retirement':'Unchanged; no early prior Landscape deletion or weakened final singleton/partial-output gate'},
    'checks':{name:data['passed'] for name,data in checks.items()},
    'total_offline_checks':sum(data['passed'] for data in checks.values()),
    'unreal_imported':False,'native_execution':False,'editor_launched':False,'lease_modified':False,'profiles_modified':False,
    'manager_next':[
        'Review these exact hashes plus task2 final frozen interface; root alone performs final combined seal.',
        'Fresh paused original-map bank startup via reviewed launcher, then factual sole-PID/world/dirty/Engine checks and bank EDITOR_ACQUIRED.json.',
        'Root issues exact CODEX_BANK_INTEGRATION native content lease. Keep ordinary_generation_authorized false until merged profile/catalog and combined source/contracts pass.',
        'For generation, root supplies literal flags plus assigned_editor_PID/map in BANK_ACTIVATION and same exact actual-PID lease identities.',
        'Prove current official Landscape selection through native road rebuild/clipping/grounding, final suppression, scoped Bake and prior retirement; named save/reopen/regeneration and appearance remain separate native acceptance.'
    ]}
(OUT/'SOURCE_HANDOFF.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
(OUT/'RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
(OUT/'RESULT.txt').write_text('SOURCE FROZEN - BANK STARTUP / GENERATION LEASE AND CURRENT ROAD LANDSCAPE AUTHORITY\n\n'
    'Changed only the three reopened task1 sources. Native content owner is CODEX_BANK_INTEGRATION. Startup remains paused inspection with truthful task=bank. Imports-only activation cannot run ordinary generation through either menu or direct lifecycle guard. Root BANK_ACTIVATION requires native_authorized_now=true, ordinary_generation_authorized=true, assigned_editor_PID=<actual>, map=<exact original map>, plus matching manager/bank/scope identities before generation. Root owns these fields and all profiles.\n\n'
    'Road generation resolves fresh official Landscape identity before authoring and passes the bound current_road_landscape_authority callback to task2. Exact previous accounted paths remain until the existing complete replacement lifecycle retires them. No name suffix selection or paint-wait field dependency remains in this handoff.\n\n'
    'Public run also rejects denied activation before GeoCityRun construction, ordinary workflow/history writes, ACTIVE registration or failure cleanup/Engine mutations. Prior provisional freeze is preserved in BeforePreflightGuard/.\n\n'+
    f"Offline checks passed: {receipt['total_offline_checks']} ({checks['SOURCE_CHECKS.json']['passed']} focused Python including actual task2 pure consumer and public entrypoint denial, 8 launcher identity/parser, 18 retained regressions). No Unreal import, native run, lease change, profile edit or combined reseal. Root review/seal, fresh bank startup and native acceptance remain.\n\n"+
    '\n'.join(row['file']+' SHA256 '+row['sha256'] for row in changes)+'\n',encoding='utf-8')
pointer={'schema':'environmentpipeline.task1_supplemental_pointer.v1','status':receipt['status'],'latest_supplement':str((OUT/'SOURCE_HANDOFF.json').relative_to(ROOT)).replace('\\','/'),'sha256':sha(OUT/'SOURCE_HANDOFF.json'),'prior_pointer_preserved':'BankAuthority_Repair/Before/SUPPLEMENTAL_HANDOFF.json'}
(OUT.parent/'SUPPLEMENTAL_HANDOFF.json').write_text(json.dumps(pointer,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':receipt['status'],'checks':receipt['total_offline_checks'],'sources':changes},indent=2))
