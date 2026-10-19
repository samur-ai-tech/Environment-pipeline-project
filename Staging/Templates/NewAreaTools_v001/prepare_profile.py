"""Prepare this area's profile candidate. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the El Wahat / Karmei
Yosef prepare_profile.py. Template profile: Tools/area_constants.py PROFILE_TEMPLATE_AREA_ID, the last profile that completed
a full non-Gaza cook (Lebanon is kept aside as a scaffold, GOVERNANCE_RECORD.md RC-40); its row count, bank digest, release
id and registry sha are asserted from area_constants.py. The HDA is the build record's unreal_asset (hda_edits.RECORD).
The decision texts are this area's own [D] answers, ASSIGNMENT.json 'profile_decisions' (required keys: authorization,
unsupported_shell_decided_by, roadbld_status, external_landscape_material, authority, houdini_placeholder_trees,
failed_generated_street_poles, unsupported_buildings).
RoadBLD stays disabled here: RC-60 opened RoadBLD to all areas, but the sealed menu code still limits it to its own area
list (Content/Python/geocity_editor_action.py; sealed code changes only with Aviv's per-item approval).
Writes only this task's staging files. No editor, Houdini, bank or shared-profile change.
"""
import copy
import hashlib
import importlib.util
import json
import re
from pathlib import Path

TASK = Path(__file__).resolve().parent
PROJECT = TASK.parents[1]
_spec = importlib.util.spec_from_file_location('area_constants', TASK / 'Tools' / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (refuses if not filled in)
assert TASK.name == A.TASK_FOLDER, (TASK.name, A.TASK_FOLDER)
AREA = A.AREA_ID
TEMPLATE_AREA = A.PROFILE_TEMPLATE_AREA_ID
ANYAREA_TABLE = '/Game/Project/Shared/ModelBank/DT_EnvironmentBank_AnyArea'
ANYAREA_RELEASE = A.PROFILE_TEMPLATE_RELEASE_ID
CATALOG_SHA = A.PROFILE_TEMPLATE_CATALOG_SHA256
TEMPLATE_REGISTRY_SHA = A.PROFILE_TEMPLATE_REGISTRY_SHA256
read = lambda p: json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


acquisition = read(TASK / 'ACQUISITION_RECEIPT.json')
assert acquisition['status'] == 'SOURCE_PACKAGE_VALIDATED'
assert read(acquisition['package_path'])['area_id'] == AREA
D = read(TASK / 'ASSIGNMENT.json').get('profile_decisions') or {}
missing_d = [k for k in ('authorization', 'unsupported_shell_decided_by', 'roadbld_status', 'external_landscape_material',
                         'authority', 'houdini_placeholder_trees', 'failed_generated_street_poles', 'unsupported_buildings')
             if not str(D.get(k, '')).strip()]
assert not missing_d, ('ASSIGNMENT.json profile_decisions lacks this area\'s [D] answers', missing_d)
hda_record = read(TASK / A.HDA_RECORD)
assert hda_record['unreal_asset'] == A.UNREAL_HDA, ('the build record must name this area HDA (build_hda.py)', hda_record.get('unreal_asset'))

template_path = PROJECT / 'Staging/ModelBank' / TEMPLATE_AREA / 'AREA_PROFILE.json'
template_sha = sha(template_path)
template = read(template_path)
assert template['table'] == ANYAREA_TABLE and template['row_count'] == A.PROFILE_TEMPLATE_ROW_COUNT
assert template['catalog_sha256'] == template['release']['catalog_sha256'] == CATALOG_SHA, 'Bank digest moved; re-check'
assert template['release']['id'] == ANYAREA_RELEASE

registry_ref = template['building_assembly_contract']['source_family_registry_ref']
assert sha(registry_ref['path']) == registry_ref['sha256'] == TEMPLATE_REGISTRY_SHA
registry = read(registry_ref['path'])
for kit in registry.get('modular_kits', []):
    if TEMPLATE_AREA in kit.get('allowed_area_ids', []):
        kit['allowed_area_ids'] = list(dict.fromkeys(kit['allowed_area_ids'] + [AREA]))
registry_path = TASK / 'AREA_SOURCE_FAMILY_REGISTRY.json'
write(registry_path, registry)

p = copy.deepcopy(template)
root = f'/Game/Project/Areas/{AREA}/BankIntegration_v015'
p.update(root=root, map=f'{root}/L_{AREA}', hda=hda_record['unreal_asset'],
         source=acquisition['package_path'],
         landscape_material=f'{root}/Materials/MI_GeoCityGround_Auto.MI_GeoCityGround_Auto',
         cook_folder=f'{root}/Cook', bake_folder=f'{root}/Bake',
         catalog_receipt=str(TASK / 'HDA_CATALOG_RECEIPT.json'),
         workflow_receipt=str(TASK / 'WORKFLOW_STATE.json'),
         build_state_alias=str(TASK / 'BUILD_STATE.json'),
         operation_timeout_seconds=14400,
         native_ground_receipt=str(TASK / 'NATIVE_AREA_CREATION.json'),
         native_ground_receipt_sha256=None)
p.pop('road_repair_candidate', None)

contract = p['building_assembly_contract']
contract['scope_area_ids'] = [AREA]
contract['authorization'] = D['authorization']
contract['source_family_registry_ref'] = {'path': str(registry_path), 'sha256': sha(registry_path)}
contract['unsupported_shell_tolerance'] = {
    'enabled': True, 'max_count': 100000, 'max_fraction': 1.0,
    'decided_by': D['unsupported_shell_decided_by'],
    'meaning': ('pads whose assembly failed keep the original Houdini shell (status unsupported_original_shell_retained); '
                'for this area the bake always proceeds and the count is reported')}
styles = contract['building_style_variants']
styles['scope_area_ids'] = [AREA]
if 'disabled_reason' in styles:
    styles['disabled_reason'] = re.sub(r"disabled for the (\S+) run on Aviv's instruction to run now",
                                       r"kept disabled as in the \1 run (one style set, everything open)",
                                       styles['disabled_reason'])

p['roadbld_workflow'] = dict(p['roadbld_workflow'], requested=False, enabled=False,
                             status=D['roadbld_status'],
                             repair_queue_ref=str(TASK / 'ROAD_REPAIR_QUEUE.json'),
                             workflow_receipt=str(TASK / 'ROADBLD_WORKFLOW_STATE.json'))
assert p['road_provider'] == 'houdini' and p['road_provider_contract'] == {}
p['external_landscape_material'] = dict(p['external_landscape_material'],
    decision=D['external_landscape_material'])

decision = {'id': 'Aviv_NewArea_%s_%s' % (AREA, A.TASK_DATE.replace('-', '')),
            'authority': D['authority'],
            'source_request': read(TASK / 'REQUEST.json'),
            'bank_release': {k: p['release'][k] for k in ('id', 'style_set', 'catalog_sha256')},
            'catalog_sha256': p['catalog_sha256'], 'table': p['table'],
            'template_profile': {'path': str(template_path), 'sha256': template_sha},
            'canonical_table_modified': False, 'named_holds_preserved': True,
            'family_enablement_unchanged': True, 'new_area_kit_scope_only': True,
            'houdini_placeholder_trees': D['houdini_placeholder_trees'],
            'failed_generated_street_poles': D['failed_generated_street_poles'],
            'unsupported_buildings': D['unsupported_buildings'],
            'visual_acceptance': False}
write(TASK / 'AREA_DECISION.json', decision)
p['release'] = dict(p['release'], decision_receipt=str(TASK / 'AREA_DECISION.json'),
                    decision_sha256=sha(TASK / 'AREA_DECISION.json'))
assert p['release']['id'] == ANYAREA_RELEASE

write(TASK / 'PROFILE_CANDIDATE.json', p)
leftovers = sorted(set(re.findall(r'[^"]{0,50}' + re.escape(TEMPLATE_AREA.split('_')[0]) + r'[^"]{0,30}', json.dumps(p, ensure_ascii=False))))
print(json.dumps({'status': 'PROFILE_CANDIDATE_WRITTEN', 'template_sha256': template_sha,
                  'registry_sha256': sha(registry_path), 'decision_sha256': p['release']['decision_sha256'],
                  'template_area_mentions_left': leftovers}, indent=2, ensure_ascii=False))
