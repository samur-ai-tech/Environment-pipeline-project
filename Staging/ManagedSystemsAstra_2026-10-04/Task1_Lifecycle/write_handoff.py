"""Write task1 source-only delivery receipts; no native imports or operations."""
import datetime
import difflib
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
FILES=['Content/Python/init_unreal.py','Content/Python/geocity_runtime_guard.py',
       'Content/Python/geocity_editor_action.py','Content/Python/geocity_bank_workflow.py',
       'Staging/SystemCompletion_2026-10-04/seal_runtime.py','Staging/SystemCompletion_2026-10-04/launch_editor.ps1']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
hashes=[];diffs=[]
for name in FILES:
    path=ROOT/name;before=OUT/'Before'/path.name
    hashes.append({'path':name,'before_sha256':sha(before),'sha256':sha(path)})
    diffs.extend(difflib.unified_diff(before.read_text().splitlines(True),path.read_text().splitlines(True),
                                    fromfile='before/'+name,tofile=name))
(OUT/'SOURCE_CHANGES.patch').write_text(''.join(diffs),encoding='utf-8')
manifest=ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
assert sha(manifest)==sha(OUT/'Before/geocity_runtime_manifest.json'),'Task1 must not publish combined seal'
checks=json.loads((OUT/'SOURCE_CHECKS.json').read_text())
integration_path=ROOT/'Staging/ManagedSystemsAstra_2026-10-04/PROFILE_INTEGRATION.json'
profile_integration=[]
if integration_path.exists():
    for row in json.loads(integration_path.read_text()):
        path=ROOT/row['profile']
        assert sha(path)==row['after_sha256'],'Manager-integrated profile changed since integration receipt'
        profile=json.loads(path.read_text())
        roles=[p['expected_role'] for p in profile['landscape_grass']['paint_probe_locations']]
        assert roles.count('RoadBed')>=1 and roles.count('BuildingPad')>=1
        profile_integration.append({'profile':row['profile'],'sha256':sha(path),'matches_manager_integration':True,
                                    'known_RoadBed_probes':roles.count('RoadBed'),'known_BuildingPad_probes':roles.count('BuildingPad')})
stop=json.loads((ROOT/'Staging/SystemCompletion_2026-10-04/STOP_HANDOFF.json').read_text())
iran=json.loads((ROOT/'Staging/HoudiniEngineOutputRepair_2026-10-04/RESULT.json').read_text())
changes=[
 'Combined v2 sealer/startup verify exact Python bytes, entrypoint, launcher, sealer, DefaultEngine.ini and dedicated DefaultRoadBLD.ini. Per-PID startup receipts retained. Rebootstrap cannot replace an already bound manifest.',
 'Launcher requires reviewed map, profile and manifest hashes plus current assignment manager/operator identities. It grants paused startup inspection only. Manager actual-PID activation is a separate lease transition.',
 'Canonical current-map profiles use one-level ModelBank paths, excluding nested archives. Registered ordinary menu accepts and preserves the exact activated task4 lease, while retaining ordinary unowned-menu use.',
 'Runtime profile merge is limited to landscape_material, road_provider, road_provider_contract and roadbld_workflow.status. Concurrent file/hash edits or other in-memory configuration changes fail closed; exact before/after field diff and hashes are recorded.',
 'Previous workflow snapshots are retained under WorkflowHistory; current and last-successful profile identity and actor scope are checked. Failure cleanup attempts all callback removals, pauses failed operations, disables automatic execution/autosave, records cleanup errors/dirty state and holds unsafe leases.',
 'Previous Landscapes are accounted through the last successful baked ledger plus exact public-wrapper Landscape output objects bound to this source and named map. Unaccounted actors stop before rebuild. No class/name-based deletion is added.',
 'Native building coverage records constructed and explicitly unsupported separately; unsupported counts, duplicate assembly identities or module receipt mismatch stop before Bake. Existing 398-building Shujaiya ledger passes offline.',
 'Effective native road policy is consumed through task2 public read-only gate before Engine mutations. Input table identity and supported native Bake/parameter readbacks are checked.',
 'Cook paint readiness is deferred through bounded Slate callbacks before roads/Bake, and paint_ready is checked again after Bake. The original operation start/time allowance remains unchanged.',
 'Staged native road contract ownership is checked before correction commit; suppression token/source contract must match before official Bake. Exceptions in Bake callbacks now enter the failure ledger.'
]
sequence=[
 'Manager reviews all source receipts, integrates profile fields and final provider interfaces, then runs seal_runtime.py followed by seal_runtime.py --check after all three source writers stop. Task1 does not perform this combined seal.',
 'Manager reviews clean shutdown of existing editor, then authorizes launch_editor.ps1 with exact map/profile/manifest SHA256 and assignment manager/task4 IDs. Launcher writes CODEX_MANAGED_SYSTEMS_STARTUP + AWAITING_MANAGER_ACTUAL_PID; it cannot authorize generation.',
 'Task4 proves fresh exact-source startup, actual sole PID/world/dirty state, paused HDA flags, official output ownership of both saved Landscapes, and all five effective RoadBLD flags false. Manager appends an actual-PID/map lease using the schema below.',
 'Registered current-map menu verifies seal, canonical profile, task4 activation, dirty package acknowledgments and native policy. It keeps the manager lease; it does not fabricate OWNER=NONE or release task4 on completion.',
 'Official Engine connects, permanent ground/Grass preparation uses its named saves, existing source-bound output is accounted, input/output parameters bind, and rebuild/recook runs. Output/receipt/native instance/material/building gates must all pass.',
 'Full task3 paint_ready is awaited for up to120 seconds per cook without resetting original operation timeout. Then road build(profile, export, settings, reviewed_dirty_packages, on_complete) runs with Engine cooking paused.',
 'Native completion -> staged_contract() -> verify map/PID/lease hash/tagged actor paths -> grounding.commit_correction(native) -> official suppression Cook. Pending corrections rollback on precommit failure; committed corrections are not falsely described as reversible after suppression.',
 'Suppression Cook repeats full output/building/material/paint readiness gates; provider token and source/centreline/generated-piece identities must match the staged contract before Bake.',
 'Official Bake completes and removes cooked mesh components. Task3 paint_ready is awaited on the exact new baked Landscape for up to120 seconds. New native instance/material counts pass before exact prior baked/official-output paths are retired; unknown actors stop the operation.',
 'Parent saves named HDA dependency closure, then native.commit(hda_receipt) revalidates post-Bake terrain and road output, saves its named dependencies, retires exact successful/failed native actors, and performs its existing named map save. This existing provider-owned intermediate map save is explicit.',
 'Parent sets final saved native contract on HDA, performs the final named map save and dependency closure readback, proves named map clean, then atomically merges only runtime profile delivery fields and records baked_saved_verified/LAST_SUCCESSFUL. Parent is final-save owner; provider intermediate saved state remains recorded if a later parent step fails.',
 'Task4 separately inspects Lit pixels, near grass, scoped replacement, clean native state, fresh-process reopen and ordinary repeat regeneration in Shujaiya then Rimal. Manager owns final clean release and acceptance.'
]
native_checks=[
 'Fresh startup accepts v2 combined seal; wrong module, config, launcher, startup, profile or reviewed map hash fails before generation. Never hot reload.',
 'Actual-PID task4 activation is required; startup-only lease is rejected by menu and direct lifecycle run. The menu must preserve the exact task4 lease across success/failure.',
 'Native task2 effective-policy receipt reports all5 flagsFalse. No runtime setting coercion is added. A correct source config is not native crash-resolution proof.',
 'Prove get_output_object_at returns installed HoudiniLandscapeTargetLayerOutput/Output with readable reflected landscape property. Existing second saved Shujaiya actor must be in exact official output bindings or source accounting stops; no guessed deletion fallback.',
 'Prove existing wrapper package_file equals profile source. Receipt records source SHA, saved map SHA, exact official and last-successful actor lists. Preserve prior baked output until complete new replacement verification.',
 'Official native schema/catalog digest/table bindings, actual outputs, all398/269 building construction, instance/material counts and zero unsupported buildings pass. HDA errors or missing output prevent Bake.',
 'Task3 paint_ready (all required target/readiness checks) gates native road build and post-Bake named persistence. Mere nonzero Ground or empty viewer grass cache is not final visible grass evidence.',
 'Native build/staged/correction/suppression/Bake/commit sequence succeeds with correct token/lease/source ownership; captured correction rollback and operation time ledgers retain original start.',
 'Native intermediate map-save plus parent final-save ordering is captured. After final save there is one Landscape, no cooked mesh components, no overlapping native copies, named dependencies clean and exact runtime profile diff only.',
 'On any native error: preserve partial save facts and failed ledgers; no false clean release, no autosave of failed content. Pausing/detaching is not proof a running HAPI cook was cancelled. Activated task4 must inspect session/callbacks and recover explicitly.',
 'Both original areas need repeated ordinary generation, named save, fresh-process reopen, actual Lit road/material/building/grass views and explicit remaining limitations. This source phase does not claim any of them.'
]
handoff={
 'schema':'environmentpipeline.task1_source_handoff.v1','status':'SOURCE_READY_FOR_MANAGER_REVIEW',
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'date_local':'2026-10-04','timezone':'Asia/Jerusalem',
 'task':'task1','thread_id':'01a106e8-ef65-78e0-aa96-f419393ebd6c','manager_thread_id':'01a106bc-2fde-7f23-9aa7-8ba413dc6245',
 'source_phase_complete':True,'source_writes_stopped':True,'native_activation':False,
 'files':hashes,'combined_manifest':{'published_by_task1':False,'existing_manifest_sha256':sha(manifest),'status':'STALE_BY_DESIGN_UNTIL_MANAGER_COMBINED_SEAL','required_schema':'environmentpipeline.geocity_runtime_sources.v2'},
 'changes':changes,'validation':{**checks,'powershell_launcher_parse_passed':True,'test_script':'verify_source.py','receipt':'SOURCE_CHECKS.json'},
 'reconciliation':{'authoritative_stop':'Staging/SystemCompletion_2026-10-04/STOP_HANDOFF.json',
   'stop_status':stop['status'],'stop_pid_historical':27188,'stop_flags_all_true':True,
   'gaza_new_delivery_complete':False,'iran_receipt':'Staging/HoudiniEngineOutputRepair_2026-10-04/RESULT.json',
   'iran_ordinary_runs':iran['ordinary_runs_completed'],'iran_fresh_process_reopen':iran['final_fresh_process_reopen'],
   'iran_native_instances':iran['native_instances_each_run'],'iran_actor_count':iran['actor_count_each_run'],
   'iran_scope_limit':'Prior retained lifecycle evidence only; does not verify these source changes or Gaza RoadBLD/Grass. Iran visual captures were Unlit; Lit/art acceptance remained open.'},
 'profile_field_patches':[],
 'manager_profile_integration':{'receipt':str(integration_path.relative_to(ROOT)).replace('\\','/'),
     'receipt_sha256':sha(integration_path) if integration_path.exists() else None,'current_profiles':profile_integration,
     'native_weights_verified':False,'task3_revised_probe_enforcement_freeze_required':True,
     'consumer_contract':'Stable verify_landscape(...).paint_ready; task3 must enforce required known RoadBed/BuildingPad probe presence and matches. Grid-only readiness is not sufficient.'},
 'profile_contract':{'manager_source_patch_required_by_task1':False,'runtime_owned_fields':['landscape_material','road_provider','road_provider_contract','roadbld_workflow.status'],
   'landscape_material_limit':'Enabled Grass profile only: root + /Materials/MI_GeoCityGround.MI_GeoCityGround',
   'immutable_fields':'Everything else, including bank release/holds, selected assets, road settings, source/map roots, Grass configuration, capacity, and area profiles identity.',
   'concurrency':'Reject any profile byte/hash change during operation; merge current identical baseline plus allowed runtime diff, atomic replace after final map save. No manager/bank edit during native run.',
   'profile_hashes':'Launcher requires ExpectedProfileSha256; profile delivery fields intentionally excluded from immutable runtime manifest because ordinary successful generation updates them.'},
 'launcher':{'parameters':['AreaMap','ExpectedMapSha256','ExpectedManifestSha256','ExpectedProfileSha256','ManagerThreadId','OperatorThreadId'],
   'startup_owner':'CODEX_MANAGED_SYSTEMS_STARTUP','startup_activation':'AWAITING_MANAGER_ACTUAL_PID',
   'generation_lease_template':'<UTC> OWNER=CODEX_MANAGED_SYSTEMS_TASK4 manager_thread_id=01a106bc-2fde-7f23-9aa7-8ba413dc6245 operator_thread_id=<ASSIGNMENTS.task4.thread_id> task=task4 assigned_editor_PID=<actual sole PID> map=<exact current area package> activation=MANAGER_ACTIVATED scope=original_maps_normal_menu_named_saves_one_writer_bank_unchanged',
   'lease_issuer':'Manager only, after actual PID/native preflight review','lease_release':'Manager/task4 exact clean handoff; ordinary action never releases a managed lease'},
 'provider_interfaces':{'roads':['require_geographic_landscape_authority() must read effective defaults and fail, never force values','build(...,on_complete=...)','staged_contract()','grounding.commit_correction(native)','grounding.rollback_correction(native,error)','commit(hda_receipt) currently performs an intermediate named map save and returns saved delivery'],
   'ground':['prepare(run) may change only run.p.landscape_material and named retained ground/Grass assets','verify_landscape(run,landscape,receipt) must return paint_ready; False waits bounded; exception fails','is_native_grass(actor,component,profile) separates approved Landscape Grass cache from exact HDA instances'],
   'final_save_owner':'GeoCityRun.finish_save; task2 native commit retains existing intermediate named-save behavior, which must not be presented as an atomic all-or-nothing transaction'},
 'ordering':sequence,'native_acceptance_checks':native_checks,
 'installed_contract_evidence':['Plugins/HoudiniEngine/Source/HoudiniEngineEditor/Public/HoudiniPublicAPIAssetWrapper.h',
 'Plugins/HoudiniEngine/Source/HoudiniEngineEditor/Private/HoudiniPublicAPIAssetWrapper.cpp',
 'Plugins/HoudiniEngine/Source/HoudiniEngineRuntime/Private/HoudiniOutput.h:237-309'],
 'completion_states':{'source_implementation':'IMPLEMENTED_OFFLINE_CHECKED','actual_native_operation':'NOT_RUN_BY_TASK1',
 'visible_result':'NOT_RUN','persistence':'NOT_RUN','fresh_reopen':'NOT_RUN','ordinary_regeneration':'NOT_RUN','user_acceptance':'NOT_GRANTED'},
 'preservation':'Only six exclusive source/launcher/sealer files plus Task1_Lifecycle receipts changed by task1. No profiles/config/vendor/upstream/assets/maps/leases/editor operations changed. Combined manifest remains untouched.87 candidates and holds are unchanged.'}
for name in ('SOURCE_HANDOFF.json','RESULT.json'):
    (OUT/name).write_text(json.dumps(handoff,indent=2)+'\n',encoding='utf-8')
text='Task1 Lifecycle — SOURCE_READY_FOR_MANAGER_REVIEW\n4 October 2026, source-only phase complete. Native execution NOT RUN.\n\n'
text+='Retained evidence\nThe stopped predecessor remains stopped. Its STOP_HANDOFF supersedes older RESULT prose. The prior Iran delivery completed two ordinary runs and fresh-process reopen; it proves that retained lifecycle only. Shujaiya reached complete HDA output but the new road/map replacement was not saved. The five native road Landscape flags were still true at stop.\n\n'
text+='Implemented\n'+'\n'.join(str(i+1)+'. '+item for i,item in enumerate(changes))+'\n\n'
text+='Integration and save ordering\n'+'\n'.join(str(i+1)+'. '+item for i,item in enumerate(sequence))+'\n\n'
text+='Manager handoff\nNo task1 profile source patch is required. Approve the runtime four-field allowlist and task3 field patches, review task2 config and all provider interfaces, then publish the final combined v2 seal only after all source writers stop. The old manifest was deliberately not rewritten and is now stale. The launcher requires reviewed map/profile/manifest hashes and current manager/operator IDs. Use SOURCE_HANDOFF.json for the exact activation lease and native acceptance checklist. No source hot reload.\n\n'
text+='Validation\n18 offline checks passed using installed Unreal Python311 without importing Unreal or provider modules; PowerShell launcher parsed without errors. Checks cover real retained building ledger plus unsupported/module corruption, exact leases, profile allowlist/concurrency, paint callback timing, cleanup failures, Landscape output identity, suppression token and sealer coverage. These checks do not prove native API exposure, crash resolution, persistence or appearance.\n\n'
text+='Manager profile integration verified\n'+''.join(row['sha256']+'  '+row['profile']+'\n' for row in profile_integration)
text+='Both profiles contain three known RoadBed and three known BuildingPad probes. Native weights are unverified. Combined sealing remains pending task3 revised probe-enforcement freeze; the paint_ready consumer API is unchanged.\n\n'
text+='Hashes\n'+'\n'.join(row['sha256']+'  '+row['path'] for row in hashes)+'\n\n'
text+='Source writes are stopped for manager review. Await native findings or a further scoped repair assignment. No messages were sent to other chats.\n'
(OUT/'RESULT.txt').write_text(text,encoding='utf-8')
print(json.dumps({'status':handoff['status'],'files':len(hashes),'offline_checks':checks['passed'],'manifest_published':False,'native_operation':False}))
