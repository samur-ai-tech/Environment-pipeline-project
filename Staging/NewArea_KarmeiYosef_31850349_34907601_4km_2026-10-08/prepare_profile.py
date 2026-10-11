"""Prepare the Karmei Yosef 4 km area profile candidate from the current Lebanon profile.

Same method as Lebanon's prepare_profile.py, but the template is the Lebanon profile
that completed a full non-Gaza cook (run 2, 2026-10-08) on the shared AnyArea bank.
Writes only this task's staging files. No editor, Houdini, bank or shared-profile change.
"""
import copy
import hashlib
import json
import re
from pathlib import Path

TASK = Path(__file__).resolve().parent
PROJECT = TASK.parents[1]
AREA = 'KarmeiYosef_31850349_34907601_4km'
LEBANON = 'Lebanon_33390778_35506639_4km'
ANYAREA_TABLE = '/Game/Project/Shared/ModelBank/DT_EnvironmentBank_AnyArea'
ANYAREA_RELEASE = 'EnvironmentBank_AnyArea_20261007'
CATALOG_SHA = '12552e1421d7cda8e05b0f00a22d9ac52960fa27c0c3e12502efa7c8a470b41e'
LEBANON_REGISTRY_SHA = 'bf425fd06ac07eae30cc27411d128bd603895bd2186d8d8b26fc0496b2f3791f'
read = lambda p: json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


acquisition = read(TASK / 'ACQUISITION_RECEIPT.json')
assert acquisition['status'] == 'SOURCE_PACKAGE_VALIDATED'
assert read(acquisition['package_path'])['area_id'] == AREA

template_path = PROJECT / 'Staging/ModelBank' / LEBANON / 'AREA_PROFILE.json'
template_sha = sha(template_path)
template = read(template_path)
assert template['table'] == ANYAREA_TABLE and template['row_count'] == 1295
assert template['catalog_sha256'] == template['release']['catalog_sha256'] == CATALOG_SHA, 'Bank digest moved; re-check'
assert template['release']['id'] == ANYAREA_RELEASE

registry_ref = template['building_assembly_contract']['source_family_registry_ref']
assert sha(registry_ref['path']) == registry_ref['sha256'] == LEBANON_REGISTRY_SHA
registry = read(registry_ref['path'])
for kit in registry.get('modular_kits', []):
    if LEBANON in kit.get('allowed_area_ids', []):
        kit['allowed_area_ids'] = list(dict.fromkeys(kit['allowed_area_ids'] + [AREA]))
registry_path = TASK / 'AREA_SOURCE_FAMILY_REGISTRY.json'
write(registry_path, registry)

p = copy.deepcopy(template)
root = f'/Game/Project/Areas/{AREA}/BankIntegration_v015'
p.update(root=root, map=f'{root}/L_{AREA}', hda=f'{root}/HDA/GeoCity_city_v015_CurrentBank_4km_KY',
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
contract['authorization'] = ('Aviv requested this retained 4x4 km geographic area (2026-10-08) using the existing '
                             'qualified bank and construction rules. Existing family enablement, holds and capabilities are preserved.')
contract['source_family_registry_ref'] = {'path': str(registry_path), 'sha256': sha(registry_path)}
contract['unsupported_shell_tolerance'] = {
    'enabled': True, 'max_count': 100000, 'max_fraction': 1.0,
    'decided_by': "Aviv, Karmei Yosef chat, 2026-10-08 ~10:35Z: 'Never stop for this'",
    'meaning': ('pads whose assembly failed keep the original Houdini shell (status unsupported_original_shell_retained); '
                'for this area the bake always proceeds and the count is reported')}
styles = contract['building_style_variants']
styles['scope_area_ids'] = [AREA]
if 'disabled_reason' in styles:
    styles['disabled_reason'] = re.sub(r"disabled for the Lebanon run on Aviv's instruction to run now",
                                       "kept disabled as in the Lebanon run (one style set, everything open)",
                                       styles['disabled_reason'])

p['roadbld_workflow'] = dict(p['roadbld_workflow'], requested=False, enabled=False,
                             status="Disabled: Houdini roads for the first Karmei Yosef run (Aviv 2026-10-08)",
                             repair_queue_ref=str(TASK / 'ROAD_REPAIR_QUEUE.json'),
                             workflow_receipt=str(TASK / 'ROADBLD_WORKFLOW_STATE.json'))
assert p['road_provider'] == 'houdini' and p['road_provider_contract'] == {}
p['external_landscape_material'] = dict(p['external_landscape_material'],
    decision=("Karmei Yosef 4 km uses a named-saved copy of the Karmei Yosef 2 km ground instance "
              "(Lebanon MountainRangeExample values with the snow line moved to 10 km); appearance is pending the actual area."))

decision = {'id': 'Aviv_NewArea_KarmeiYosef_31850349_34907601_4km_20261008',
            'authority': 'Direct human request (Aviv, 2026-10-08) for this new retained 4x4 km geographic area and the complete existing pipeline',
            'source_request': read(TASK / 'REQUEST.json'),
            'bank_release': {k: p['release'][k] for k in ('id', 'style_set', 'catalog_sha256')},
            'catalog_sha256': p['catalog_sha256'], 'table': p['table'],
            'template_profile': {'path': str(template_path), 'sha256': template_sha},
            'canonical_table_modified': False, 'named_holds_preserved': True,
            'family_enablement_unchanged': True, 'new_area_kit_scope_only': True,
            'houdini_placeholder_trees': 'none (owned 4 km generator, carried over from the 2 km area; Aviv 2026-10-08)',
            'failed_generated_street_poles': 'omitted as in the Gaza areas (owned 4 km generator, carried over from the 2 km area; Aviv 2026-10-08)',
            'unsupported_buildings': 'never stop the bake; original shells retained and counted (Aviv 2026-10-08, carried over from the 2 km area)',
            'visual_acceptance': False}
write(TASK / 'AREA_DECISION.json', decision)
p['release'] = dict(p['release'], decision_receipt=str(TASK / 'AREA_DECISION.json'),
                    decision_sha256=sha(TASK / 'AREA_DECISION.json'))
assert p['release']['id'] == ANYAREA_RELEASE

write(TASK / 'PROFILE_CANDIDATE.json', p)
leftovers = sorted(set(re.findall(r'[^"]{0,50}Lebanon[^"]{0,30}', json.dumps(p, ensure_ascii=False))))
print(json.dumps({'status': 'PROFILE_CANDIDATE_WRITTEN', 'template_sha256': template_sha,
                  'registry_sha256': sha(registry_path), 'decision_sha256': p['release']['decision_sha256'],
                  'lebanon_mentions_left': leftovers}, indent=2, ensure_ascii=False))
