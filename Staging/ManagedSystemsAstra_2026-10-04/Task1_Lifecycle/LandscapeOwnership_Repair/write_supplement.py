"""Publish the bounded ownership-repair source handoff, never a runtime seal."""
import datetime
import difflib
import hashlib
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
TASK=OUT.parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
source=ROOT/'Content/Python/geocity_bank_workflow.py'
baseline=OUT/'geocity_bank_workflow_before.py'
assert sha(baseline)=='bcf1335e014cb8c89d9fef47d961009bcf4c6fde2fd34c42f7051fa4a1b490db'
prior=json.loads((OUT/'AcceptedBaseline/SOURCE_HANDOFF.json').read_text())
# The first complete check payload remains embedded in the unchanged first
# handoff. Restore a standalone baseline copy from that exact embedded payload;
# the root SOURCE_CHECKS now records the explicitly rerun current regressions.
old_checks={key:value for key,value in prior['validation'].items() if key not in ('powershell_launcher_parse_passed','test_script','receipt')}
(OUT/'AcceptedBaseline/SOURCE_CHECKS.json').write_text(json.dumps(old_checks,indent=2)+'\n',encoding='utf-8')
(OUT/'AcceptedBaseline/PRESERVATION.txt').write_text('SOURCE_HANDOFF.json, RESULT.json and RESULT.txt are unchanged copies of the initial handoff. SOURCE_CHECKS.json preserves its exact embedded original check payload; the root standalone SOURCE_CHECKS was updated by the current regression run before this archival copy. The initial handoff remains unchanged and authoritative for that original check result.\n',encoding='utf-8')
review=json.loads((ROOT/'Staging/ManagedSystemsAstra_2026-10-04/SOURCE_REVIEW.json').read_text())
unchanged=[]
for row in review['source_checks']:
    if row['path']=='Content/Python/geocity_bank_workflow.py':continue
    path=ROOT/row['path']
    assert sha(path)==row['sha256'],'Frozen unrelated source/config changed: '+row['path']
    unchanged.append({'path':row['path'],'sha256':sha(path)})
manifest=ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
assert sha(manifest)=='06129276fd3743dfb5754a13454c81d22305adcd2d28bedd0da9810ff89e431a'
native_path=ROOT/'Staging/ManagedSystemsAstra_2026-10-04/Task4_Integration/LANDSCAPE_EXPORT_DIAGNOSTIC.json'
native=json.loads(native_path.read_text())
assert native['state_clean_unchanged'] and not native['errors'] and len(native['exports'])==5
native_hashes=[]
for row in native['exports']:
    assert sha(Path(row['filename']))==row['sha256']
    native_hashes.append({'file':row['filename'],'sha256':row['sha256'],'object':row['object']})
checks=json.loads((OUT/'SOURCE_CHECKS.json').read_text())
assert checks['source_sha256']==sha(source)
compile((OUT/'CHECK_NATIVE_CONSUMER.py').read_bytes(),str(OUT/'CHECK_NATIVE_CONSUMER.py'),'exec')
diff=''.join(difflib.unified_diff(baseline.read_text().splitlines(True),source.read_text().splitlines(True),
                                 fromfile='accepted/geocity_bank_workflow.py',tofile='Content/Python/geocity_bank_workflow.py'))
(OUT/'SOURCE_CHANGES.patch').write_text(diff,encoding='utf-8')
result={
 'schema':'environmentpipeline.task1_landscape_ownership_source_handoff.v1',
 'status':'SOURCE_READY_FOR_MANAGER_REVIEW','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_scope_frozen':True,'source_file':'Content/Python/geocity_bank_workflow.py','source_sha256':sha(source),
 'baseline_sha256':sha(baseline),'scope':'Only Landscape identity diagnostic/parser and re import; other lifecycle gates/order unchanged.',
 'blocker':'Fresh native PID5368 proved HoudiniLandscapeTargetLayerOutput.Landscape protected in Python. UPROPERTY alone does not establish supported read access.',
 'repair':'Use built-in ObjectExporterT3D and public AssetExportTask/Exporter.run_asset_export_task on each exact same-wrapper official output object. Parse only its root explicit native Landscape reference, matching Class/Name/full ExportPath and exact HDA outer chain. Resolve native map-local references only in the verified exact named-map package context; match exact full path against already loaded actors.',
 'fail_closed':['Wrong source or HDA outer','wrong/duplicate serialized root identity','missing/duplicate/nested Landscape reference','wrong native class or malformed quoting','cross-package/relative-to-other-map reference','unknown loaded actor','duplicate official output objects or actor identities','multiple Landscape targets','differing parent/proxy references','export failure/empty/oversized output','changed dirty packages, Engine state or actor membership'],
 'preservation':'No label/class-only ownership inference; no unknown-actor removal; successful ledger plus exact source-bound output accounting remains required. Export files and hashes are durable Staging diagnostics, never imported native assets. Failure attempts retain diagnostic paths in workflow state. Scoped replacement and complete-output gates are unchanged.',
 'installed_api_basis':[
  {'file':'C:/Program Files/Epic Games/UE_5.8/Engine/Source/Editor/UnrealEd/Classes/Exporters/ObjectExporterT3D.h','contract':'Native UExporter ExportText override'},
  {'file':'C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Public/AssetExportTask.h','contract':'Public BlueprintReadWrite Object, Exporter, Filename, automated/prompt/selected settings and Errors'},
  {'file':'C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Exporters/Exporter.h','contract':'Public BlueprintCallable RunAssetExportTask, lines246-255'},
  {'file':'Plugins/HoudiniEngine/Source/HoudiniEngineEditor/Private/HoudiniPublicAPIAssetWrapper.cpp','contract':'GetOutputObjectAt returns exact official output record UObject; GetOutputObjects does not unwrap Landscape layer references'}],
 'official_documentation':[
  'https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/ObjectExporterT3D?application_version=5.6',
  'https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AssetExportTask?application_version=5.6',
  'https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/Exporter?application_version=5.6'],
 'native_evidence':{'provider':'task4 read-only native diagnostic; not executed by task1','pid':native['pid'],
   'receipt':str(native_path.relative_to(ROOT)),'receipt_sha256':sha(native_path),'exports':native_hashes,
   'resolved_landscapes':native['resolved_official_landscape_paths'],'unaccounted':native['ownership_accounting']['unaccounted'],
   'state_clean_unchanged':True,'generation_started':False,'retirement_authorized':False},
 'offline_validation':{'focused_checks':checks['passed'],'focused_receipt':'SOURCE_CHECKS.json','retained_lifecycle_regressions':18,
   'retained_receipt':'../SOURCE_CHECKS.json','fresh_consumer_script_compile':True,'unreal_imported':False,
   'actual_serialized_fixtures':'All5 hashed task4 exports parsed and matched the exact second saved Landscape. Synthetic rejection and fake-runtime tests are separate from that evidence.'},
 'fresh_native_confirmation':{'required':True,'script':'CHECK_NATIVE_CONSUMER.py','script_sha256':sha(OUT/'CHECK_NATIVE_CONSUMER.py'),
   'procedure':'Manager reviews/reseals then performs reviewed fresh startup. In startup inspection lease, task4 runs prepared script via runpy.run_path(..., run_name="__main__") using the newly loaded module. Script avoids GeoCityRun constructor/start/account state writers and calls only official_landscapes with a Task4 receipt target.',
   'required_result':'LANDSCAPE_CONSUMER_CONFIRMATION.json passed=true, state_unchanged=true, exact bank source hash, five exact same-wrapper records resolving second Landscape, zero unaccounted after successful-ledger union; dirty/cooking/callback/actor snapshot unchanged.',
   'guard':'No native generation until manager separately activates it. No reload of old PID5368 source. If integrated helper fails, preserve receipt and return to exact source-owner repair.'},
 'unchanged_other_frozen_files':unchanged,'manifest_unchanged_sha256':sha(manifest),'resealed_by_task1':False,
 'native_integrated_helper_executed':False,'visible_result':'NOT_RUN','persistence':'NOT_RUN','regeneration':'NOT_RUN','user_acceptance':'NOT_GRANTED',
 'initial_receipts':'Unchanged first handoff retained in parent and AcceptedBaseline; original embedded checks preserved there. This supplement supersedes only its protected-property ownership method.'}
for name in ('SOURCE_HANDOFF.json','RESULT.json'):
    (OUT/name).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(OUT/'RESULT.txt').write_text('SOURCE_READY_FOR_MANAGER_REVIEW — bounded Landscape ownership repair\n\n'
 'Frozen source: Content/Python/geocity_bank_workflow.py\nSHA256: '+sha(source)+'\nBaseline: '+sha(baseline)+'\n\n'
 'Native evidence: task4 exported all five exact same-wrapper Landscape target-layer records using the installed public ObjectExporterT3D/AssetExportTask APIs in clean paused PID5368. All references identify the second saved Landscape; union with the successful baked ledger accounts both. No generation, save or actor removal occurred.\n\n'
 'Repair: replace the protected Python Landscape-property access with exact native export identity inspection. Full serialized root ExportPath, HDA outer identity, profile source and same-package actor-reference context are checked. Missing, duplicate, nested, cross-package or ambiguous references fail closed. Only exact loaded actor paths can match. No native class/label heuristic, plugin change, custom bridge or unknown-actor deletion. Complete-output/scoped replacement gates remain unchanged.\n\n'
 'Validation:23 focused offline checks, all5 actual hashed native export fixtures, and18 retained lifecycle regressions passed. Task1 did not import Unreal or execute native operations. The integrated new helper still needs fresh native confirmation.\n\n'
 'Next: root reviews/reseals; task4 uses fresh startup and CHECK_NATIVE_CONSUMER.py under its inspection-only lease. Require passed/state_unchanged, exact source hash, all five record identities and zero unaccounted Landscapes. No hot reload or generation before separate manager activation.\n\n'
 'The combined manifest and all other frozen source/config files remain unchanged. Initial SOURCE_HANDOFF and result receipts remain preserved; AcceptedBaseline also retains the original checks from the initial handoff. Source writes are now stopped.\n',encoding='utf-8')
(TASK/'SUPPLEMENTAL_HANDOFF.json').write_text(json.dumps({'status':result['status'],'supplement':'LandscapeOwnership_Repair/SOURCE_HANDOFF.json',
  'source_sha256':sha(source),'source_scope_frozen':True,'native_integrated_helper_executed':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'source_sha256':sha(source),'other_frozen_files_unchanged':len(unchanged),'checks':checks['passed'],'resealed':False}))
