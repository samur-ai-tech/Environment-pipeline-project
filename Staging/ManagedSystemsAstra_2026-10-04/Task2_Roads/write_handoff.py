"""Write this source-only assignment's receipts from saved project evidence."""
import datetime
import difflib
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2), encoding='utf-8')


flags = ['bEnableIntersectionLandscapePatch', 'bEnableIntersectionLandscapeVisibilityHole',
         'bEnableRoadLandscapePaint', 'bUseRoadLandscapeHeightPatch', 'bAutoCreatePaintLayerInfo']
files = sorted((ROOT/'Content/Python').glob('geocity_roadbld_*.py')) + [ROOT/'Config/DefaultEngine.ini', ROOT/'Config/DefaultRoadBLD.ini']
changed = {'geocity_roadbld_workflow.py', 'geocity_roadbld_junctions.py', 'DefaultEngine.ini', 'DefaultRoadBLD.ini'}
hashes = {p.relative_to(ROOT).as_posix(): {'sha256': sha(p), 'changed_by_task2': p.name in changed} for p in files}
stop = json.loads((ROOT/'Staging/SystemCompletion_2026-10-04/STOP_HANDOFF.json').read_text(encoding='utf-8-sig'))
unchanged = {}
for p in files:
    if p.name not in changed:
        before = stop['source_snapshot'].get(p.stem, {}).get('sha256')
        unchanged[p.name] = {'sha256': sha(p), 'stop_sha256': before, 'matches_stop': sha(p) == before if before else None}
evidence_paths = [
    'Plugins/RoadBLD/Intermediate/Build/Win64/UnrealEditor/Inc/RoadBLDRuntime/UHT/RoadBLDRuntimeSettings.gen.cpp',
    'Plugins/RoadBLD/Config/DefaultRoadBLD.ini',
    'Staging/SystemCompletion_2026-10-04/ROADBLD_LANDSCAPE_CRASH.json',
    'Staging/SystemCompletion_2026-10-04/SHUJAIYA_CRASHED_ROAD_STATE.json',
    'Staging/SystemCompletion_2026-10-04/STOP_HANDOFF.json',
    'Staging/ManagedAstra_2026-10-03/TASK1_REPLACEMENT_V3_SOURCE_RESULT.json',
    'Staging/ManagedAstra_2026-10-03/TASK3_FROZEN_REPLACEMENT_V3_REVIEW.json']
write('EFFECTIVE_CONFIG_EVIDENCE.json', {
    'schema': 'environmentpipeline.task2.effective_config_evidence.v1',
    'installed_category': 'RoadBLD', 'settings_class': '/Script/RoadBLDRuntime.RoadBLDRuntimeSettings',
    'project_file': 'Config/DefaultRoadBLD.ini', 'required_values': {n: False for n in flags},
    'installed_uht': {'path': evidence_paths[0], 'category_lines': [1022, 1026], 'Get_accessor_lines': [27, 82],
                      'config_properties_lines': [902, 912], 'terrain_semantics_lines': [317, 449],
                      'property_flags': '0x0010000000004005 includes CPF_Config'},
    'vendor_ini': {'path': evidence_paths[1], 'all_five_vendor_values': True, 'vendor_unchanged': True},
    'stop_native_readback': {'pid': 27188, 'all_five_flags': True, 'historical_only': True},
    'measured_config_defect': 'Prior false values lived in DefaultEngine.ini, while installed class uses RoadBLD and vendor DefaultRoadBLD.ini enables all five. No project DefaultRoadBLD.ini existed before task2 created it under manager-expanded ownership.',
    'measured_crash': 'PID30548 Landscape/RenderCore access violation in first rebuild after 40 roads; log reported 32 tile patches, zero height/weight texels and old Landscape missing weightmap mips. Failed new roads/map were not saved.',
    'inference': 'Patch contribution to the crash remains inferred. Config binding repair is not proof the native access violation is resolved.',
    'official_source': {'url': 'https://dev.epicgames.com/documentation/en-us/unreal-engine/configuration-files-in-unreal-engine',
                        'retrieved': '2026-10-04', 'support': 'UCLASS config category chooses its INI hierarchy. Project Config/Default<CATEGORY>.ini supplies defaults; later layers can override them. Effective native readback is therefore mandatory.'},
    'evidence_sha256': {p: sha(ROOT/p) for p in evidence_paths}})

preflight = [
    'Manager/task4 only: actual sole UnrealEditor PID, exact current lease, original target map, paused Houdini, autoCook/autoBake off, zero callbacks and exact dirty packages. A released PID is not activation.',
    'After all source owners freeze, task1 reseals final code and both Config/DefaultRoadBLD.ini and Config/DefaultEngine.ini. Start a fresh process; no hot reload into PID27188 or another old process.',
    'Before any HDA mutation/native authoring save inspect_geographic_landscape_authority() report: passed=true; project_flags, native_views.class_default.flags and native_views.native_get.flags must each contain five literal false values. Record both settings object paths and project config SHA.',
    'If either native view is enabled/unavailable, stop. Inspect the RoadBLD hierarchy/accessor. No CDO setter, runtime config reload, vendor edit or output suppression to force a pass.',
    'Reconcile the two known saved Shujaiya Landscapes and exact successful/failed road actors. LandscapeSampler still demands one current cooked Landscape and one final saved Landscape; do not select arbitrarily or broadly remove actors.',
    'Use the registered ordinary current-map action with licensed RoadBLD. Policy gates occur before network spawn, road creation, junction edits, every rebuild dispatch, after rebuild and during native validation.',
    'Capture native logs and patch readback for each rebuild. No enabled owned LandscapePatchComponent is accepted or disabled afterward. Also inspect tile-patch logs and authoritative height/paint for changes outside owned components; zero owned components alone is not no-write proof.']
validation = [
    'Both originals: exact source XY, class/full width, protected-building exclusions, complete exterior intervals/sidewalks/junction seams and support/height gates. No fixed-road exceptions or lowered limits.',
    'Validate actual UVs, split normals, material slots, collision and one visible road provider; preserve native originals and project-owned preset copies.',
    'Inspect class-aware markings/crossings/native modules/PropSpawners in generated components and Lit views. Enabled settings are not visible detail proof. Empty native kit features remain explicit content gaps.',
    'Check prop provenance, exact retained transforms/contact and omitted-conflict receipts; no bank expansion, held releases or candidate approvals.',
    'Pending correction handles survive link checks, two validations and staged contract; rollback restores prior UV/normal/material/collision/state until explicit commit immediately before suppression. Real UObject lifetime and rollback fidelity remain unproven. Do not revive historical in-memory snapshots.',
    'build callback true means validated unsaved output. staged_contract must feed the same PID/token/source official suppression Cook/Bake. commit rechecks the sole Landscape/provider before exact prior-road retirement and named saves.',
    'Independently compare SAVED_ROAD_PRESERVATION.json: 132 failed actor paths, 87 saved package hashes and 136 successful actor paths/dependencies. Preserve packages; retire only verified current actor ledgers after replacement passes.',
    'Task4 proves Shujaiya then Rimal Lit appearance, named saves, fresh-process reopen and repeated ordinary generation without duplicate providers/actors/Landscapes. User acceptance remains separate.']
interfaces = {
    'unchanged': 'require_geographic_landscape_authority() returns the existing flat five-false dict or raises; no mutation.',
    'new_readonly': 'inspect_geographic_landscape_authority() returns passed/errors, project config SHA, CDO/native Get paths and flags. It never sets defaults, reloads config, builds or saves.',
    'run': 'check_landscape_policy(stage) records structured evidence; verify_owned_landscape_patches() detects enabled patches without disabling them.',
    'receipt_fields': ['native_landscape_authority', 'native_landscape_edit_policy', 'native_owned_landscape_patches',
                       'retired_failed_generations', 'retired_successful_generations', 'unvalidated_previous_mesh_packages_preserved'],
    'profile_field_patches': [],
    'profile_reason': 'Existing enabled road workflow/material setting suffices; terrain authority is project-wide and must not be profile-toggleable.',
    'task1_required': ['Keep pre-HDA require_geographic_landscape_authority call.',
                       'Include both project config files in final startup seal/hash verification; task2 did not edit task1 sealer/manifest/guard.',
                       'Keep existing build/staged_contract/commit and correction rollback ordering; reconcile prior saved Landscapes by exact official-output ownership.']}
write('SOURCE_HANDOFF.json', {
    'schema': 'environmentpipeline.task2.road_source_handoff.v1', 'status': 'SOURCE_READY_FOR_MANAGER_REVIEW',
    'worker_thread_id': '01a106e8-f1fa-7741-bbcd-6c772df0ae03', 'manager_thread_id': '01a106bc-2fde-7f23-9aa7-8ba413dc6245',
    'source_hashes': hashes, 'configuration_applied': True, 'native_policy_verified': False,
    'interfaces': interfaces, 'native_preflight': preflight, 'required_validation': validation,
    'source_editing_stopped': True, 'next': 'Manager review/task1 final seal, then task4 only after actual-PID activation.'})
result = {
    'schema': 'environmentpipeline.task2.roads_result.v1', 'status': 'SOURCE_READY_FOR_MANAGER_REVIEW',
    'written_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source_implementation': 'COMPLETE_WITHIN_ASSIGNED_SCOPE', 'source_hashes': hashes, 'unchanged_modules': unchanged,
    'changes': ['Correct five project values in Config/DefaultRoadBLD.ini; remove ineffective Engine section.',
                'Require correct disk category policy and both native CDO/Get views to read False.',
                'Recheck before authoring/rebuild and native validation; preserve policy evidence in delivery.',
                'Reject enabled owned Landscape patches instead of disabling after rebuild.',
                'Carry historical failed package/actor and successful dependency ledgers across repeat generations; deletion input stays exact and unchanged.'],
    'checks': json.loads((OUT/'SOURCE_CHECKS.json').read_text()),
    'native_operation': 'NOT_PERFORMED_SOURCE_ONLY', 'visible_result': 'NOT_VERIFIED', 'persistence': 'NOT_VERIFIED',
    'regeneration': 'NOT_VERIFIED', 'user_acceptance': 'NOT_CLAIMED', 'native_calls': 0, 'maps_or_content_saved': False,
    'holds_bank_vendor_upstream_unchanged': True, 'prior_87_candidates': 'PRESERVED_UNVALIDATED_UNAPPROVED',
    'content_gaps': ['No newly measured content gap can be asserted source-only. Task4 must report actual generated/visible kit details and empty features. Existing bank fit rejections remain separate bank work.'],
    'unresolved': ['Native crash causality remains unproven; patch contribution is inference and old missing weightmap mips remain an observed condition.',
                   'Fresh native Get/config binding and actual no-terrain-write behavior are not yet measured.',
                   'Retained exterior geometry repair, actual details, transaction fidelity and both original save/reopen/regeneration remain native work.'],
    'native_preflight': preflight, 'required_validation': validation,
    'receipts': ['SOURCE_HANDOFF.json', 'EFFECTIVE_CONFIG_EVIDENCE.json', 'MANAGER_CONFIG_PATCH.json',
                 'SAVED_ROAD_PRESERVATION.json', 'SOURCE_CHECKS.json', 'verify_source.py', 'SOURCE_DIFF.patch', 'Before/'],
    'source_editing_stopped': True}
write('RESULT.json', result)
diffs = []
for p in files:
    before = OUT/'Before'/p.name
    if before.is_file() or p.name == 'DefaultRoadBLD.ini':
        old = before.read_text(encoding='utf-8-sig').splitlines(True) if before.is_file() else []
        diffs.extend(difflib.unified_diff(old, p.read_text(encoding='utf-8-sig').splitlines(True),
                                        fromfile='Before/'+p.name, tofile=p.relative_to(ROOT).as_posix()))
(OUT/'SOURCE_DIFF.patch').write_text(''.join(diffs), encoding='utf-8')
print(json.dumps({'status': result['status'], 'files_hashed': len(hashes), 'unchanged_modules': unchanged}))
