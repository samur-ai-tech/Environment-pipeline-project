"""Seal staging receipts only. Does not publish the runtime source seal."""
import ast, datetime, hashlib, json
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
read=lambda path:json.loads(path.read_text(encoding='utf-8-sig'))
checks=read(OUT/'SOURCE_CHECKS.json');baseline_checks=read(OUT/'BaselineRegression/SOURCE_CHECKS.json')
assert checks['candidate_sha256']==sha(OUT/'geocity_bank_workflow.py')
for path,digest in checks['dependencies'].items():assert sha(ROOT/path)==digest,'Dependency changed after tests: '+path
manifest_path=ROOT/'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
assert manifest_path.read_bytes()==(OUT/'Before/geocity_runtime_manifest.json').read_bytes()
manifest=read(manifest_path)
runtime={}
for name,entry in manifest['modules'].items():
    path=ROOT/'Content/Python'/entry['file'];runtime[str(path.relative_to(ROOT)).replace('\\','/')]=sha(path)
    assert sha(path)==entry['sha256'],name
for relative,digest in manifest['support_files'].items():assert sha(ROOT/relative)==digest,relative
assert sha(ROOT/'Content/Python/init_unreal.py')==manifest['startup']['sha256']
assert (ROOT/'Content/Python/geocity_bank_workflow.py').read_bytes()==(OUT/'Before/geocity_bank_workflow.py').read_bytes()
building=ROOT/'Staging/IranBuildingAdaptation_2026-10-04/ConsumerIntegration'
policy_source=ROOT/'Staging/IranBuildingAdaptation_2026-10-04/building_extension.py'
policy=next(n.value for n in ast.parse(policy_source.read_bytes()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='BUILDING_POLICY' for t in n.targets))
rules=ast.literal_eval(policy)
rules['content_input']={'path':str(building/'INPUT_CONTRACT_COMBINED.json'),'sha256':sha(building/'INPUT_CONTRACT_COMBINED.json')}
profile=ROOT/'Staging/ModelBank/Iran_38196167_46086167_4km/AREA_PROFILE.json'
proposal={'status':'PROPOSED_ONLY_MANAGER_MERGE_REQUIRED','profile':str(profile),'before_sha256':sha(profile),
          'required_source_sha256':read(building/'INPUT_CONTRACT_COMBINED.json')['source_sha256'],
          'set':{'building_rules_json':rules},'policy_source':{'path':str(policy_source),'sha256':sha(policy_source)},
          'semantics_profile_proposal':'Staging/ManagedSystemsAstra_2026-10-04/Task3_GroundGrass/IranSemanticConsumer/PROFILE_PATCH_PROPOSAL.json',
          'qualification':'No acceptance or eligibility manufactured. Producer building_dependencies_complete must be true for ordinary delivery. Current supplied candidates remain unqualified.',
          'ordinary_activation':False}
(OUT/'PROFILE_INTERFACE_PROPOSAL.json').write_text(json.dumps(proposal,indent=2)+'\n')
interface_paths=[ROOT/'Staging/PipelineSemanticRepair_2026-10-04/Completion/INTERFACE_CONTRACT.json',
                 ROOT/'Staging/ManagedSystemsAstra_2026-10-04/Task3_GroundGrass/IranSemanticConsumer/INTERFACE_FROZEN_DECISION.json',
                 building/'INTEGRATION_MANIFEST.json']
receipt={
    'schema':'environmentpipeline.task1_semantic_lifecycle_patch.v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'status':'STAGED_FROZEN_READY_FOR_COMBINED_REVIEW_NATIVE_NOT_RUN',
    'manager_thread_id':'01a10789-2e6a-7321-ad85-0a2964f8a937','owner_thread_id':'01a106e8-ef65-78e0-aa96-f419393ebd6c',
    'target':'Content/Python/geocity_bank_workflow.py','before_sha256':sha(OUT/'Before/geocity_bank_workflow.py'),
    'candidate_sha256':sha(OUT/'geocity_bank_workflow.py'),'patch_sha256':sha(OUT/'SOURCE_PATCH.diff'),
    'active_runtime_manifest_sha256_preserved':sha(manifest_path),'active_runtime_modules_preserved':runtime,
    'source_module_count_unchanged':len(runtime),
    'changes':[
        'Existing prepare remains before configure. Validate its measured semantic_runtime_binding/native receipt against exact source, consumer, classified grid, material, provider and catalog hashes before complete Cook.',
        'Official parameter inventory requires one string for new semantic_runtime_binding_json and configured building_rules_json; existing setter and exact getter readback run before sole recook. Missing definition interface or changed/malformed evidence fails closed.',
        'Profile building_rules_json forwards full owner policy/content_input exact hashref; direct inline objects retain canonical wire digest, naked mutable filenames are rejected. Evidence remains qualified only by producer-owned qualification parser.',
        'Legacy definition lacking both optional parameters remains compatible. If new parameters exist without profile contracts, clear stale semantic token and only stale building content_input; retain existing building defaults.',
        'Producer owns detail semantic_surface_contract_json to ordinary catalog receipt transport. Lifecycle stores raw semantic receipt fields unchanged and verifies canonical digest/completion/source/auxiliary/provider/exclusivity/token acknowledgment; no guessed SOP read API or reconstructed contract.',
        'Require producer building_content_input_sha256 echo and building_dependencies_complete=true when profile supplies rules. Preserve incomplete output evidence and refuse complete-area save.',
        'Semantic verifier runs at cooked/pre-Bake readiness, completed Bake and final saved-area checks whenever landscape_semantics exists. Native-only provider contract rejects disabled/alternative setup; all existing120s waits, native counts, RoadBLD authority, scoped retirement and named saves stay intact.'
    ],
    'installed_api_evidence':{'file':'Plugins/HoudiniEngine/Source/HoudiniEngineEditor/Public/HoudiniPublicAPIAssetWrapper.h',
        'sha256':sha(ROOT/'Plugins/HoudiniEngine/Source/HoudiniEngineEditor/Public/HoudiniPublicAPIAssetWrapper.h'),
        'GetParameterTuples':'outputs FName -> FHoudiniParameterTuple with UPROPERTY StringValues array; read only',
        'SetStringParameterValue':'returns true if set OR already equal; marks changed for next cook, existing auto-cook disabled before complete recook',
        'python_native_call_verified':False},
    'interfaces':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in interface_paths},
    'cross_owner_dependencies':checks['dependencies'],'offline_checks':checks['passed']+baseline_checks['passed'],
    'focused_checks':checks['passed'],'retained_regressions':baseline_checks['passed'],
    'test_evidence':'Actual source hashes and actual owner production functions; classified sample has synthetic geometric masks, native preparation readback is fake and labeled. No native ready token produced for operational use.',
    'profile_patch':'PROFILE_INTERFACE_PROPOSAL.json (not applied); Task3 semantic profile proposal must be merged jointly by root',
    'runtime_written':False,'manifest_resealed':False,'profiles_written':False,'hda_written':False,'editor_actions':False,
    'remaining':[
        'Root independent review and one combined-definition integration in producer/building-defined order; exact parameter interface must exist in promoted same-type HDA.',
        'Root reviews/merges exact current-source building and semantic profile proposals; no unqualified building, unknown survey or hold is waived.',
        'Root sole-writer source integration/seal/fresh startup and actual-PID activation. Test installed Python parameter-map/readback on that exact HDA before full native Cook.',
        'Native prepare/material/Grass/source probes, complete output, named save/fresh reopen/regenerate, Lit pixels and user acceptance remain NOT RUN by this patch.'
    ]}
owned=['geocity_bank_workflow.py','lifecycle_helpers.py','lifecycle_methods.py','build_candidate.py','SOURCE_PATCH.diff','verify_candidate.py','verify_baseline.py','SOURCE_CHECKS.json','BaselineRegression/SOURCE_CHECKS.json','PROFILE_INTERFACE_PROPOSAL.json']
receipt['files']={name:sha(OUT/name) for name in owned}
(OUT/'SOURCE_HANDOFF.json').write_text(json.dumps(receipt,indent=2)+'\n')
(OUT/'RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
(OUT/'RESULT.txt').write_text('STAGING ONLY: SEMANTIC AND BUILDING CONSUMER LIFECYCLE PATCH\n\n'
    'Ready for root combined review. No active source, seal, HDA, profile, editor or Content writes. '+str(receipt['offline_checks'])+' offline checks pass ('+str(checks['passed'])+' cross-owner/focused + '+str(baseline_checks['passed'])+' retained regressions).\n\n'
    'Candidate SHA256 '+receipt['candidate_sha256']+'\nPatch SHA256 '+receipt['patch_sha256']+'\nBaseline SHA256 '+receipt['before_sha256']+'\n\n'
    'Set/readback semantic_runtime_binding_json from exact measured Task3 prepare token and building_rules_json from root-reviewed profile before full Cook. Producer transports its actual surface detail to the ordinary catalog receipt; lifecycle verifies/preserves it and passes the same receipt to Task3. Source/grid/consumer/catalog/native-binding and building input hashes stay bound; incomplete dependencies remain blocking. Default Gaza definitions remain compatible and all120s waits/named-save/road/output safeguards persist.\n\n'
    'Use building owner INPUT_CONTRACT_COMBINED.json plus SOURCE_BINDING.json for the staged849cf4 source; original0c13 input remains bound only to sourcec54a. Profile proposal is review-only; no source retarget or qualification performed. Current receiver supports native_landscape_grass only.\n\n'
    'Actual native token/preparation, parameter inventory/setter/readback, full output, save/reopen/regeneration and appearance remain unverified. Root must review all exact owner dependencies, perform sole combined integration/seal/fresh startup, and activate native writer.\n')
print(json.dumps({'status':receipt['status'],'checks':receipt['offline_checks'],'candidate_sha256':receipt['candidate_sha256'],'patch_sha256':receipt['patch_sha256']}))
