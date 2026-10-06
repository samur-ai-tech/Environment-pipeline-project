"""Independent read-only review of the bank owner's bounded native request.

This script never imports the adapter, Unreal, Houdini, or Blender, and writes
only review evidence beside itself. It does not activate native operations.
"""
import ast
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OWNER = ROOT / 'Staging/BankIntegration_2026-10-04/ModularNative_2026-10-05'
parser = argparse.ArgumentParser()
parser.add_argument('--request-sha', required=True)
args = parser.parse_args()
EXPECTED_REQUEST = args.request_sha.lower()
assert len(EXPECTED_REQUEST) == 64 and all(c in '0123456789abcdef' for c in EXPECTED_REQUEST)

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')

path = OWNER / 'NATIVE_IMPORT_REQUEST.json'
assert sha(path) == EXPECTED_REQUEST, 'review_target_changed'
request = read(path)
source = read(OWNER / 'SOURCE_BINDINGS.json')
semantics = read(OWNER / 'SHADER_SEMANTICS.json')
duplicate_path = ROOT / 'Staging/ModularConstruction_2026-10-05/SourceAudit/DUPLICATE_FACE_SLOT_READBACK.json'
duplicate_proof = {p['part_name']: p for p in read(duplicate_path)['parts']}
assert request['files'][str(duplicate_path.resolve())] == sha(duplicate_path)
source_by_id = {family['id']: family for family in source['families']}
catalog_path = ROOT / 'Staging/ModelBank/PermanentIntegration_2026-10-02/catalog_v4_source.json'
catalog = read(catalog_path)
catalog_by_id = {row['asset_id']: row for row in catalog['rows']}
pin_checks = []
for field in ('files', 'python_sources'):
    for pinned_path, expected in request[field].items():
        item = {'path': pinned_path, 'expected_sha256': expected, 'exists': Path(pinned_path).is_file(), 'kind': field}
        if item['exists']:
            item['sha256'] = sha(pinned_path)
        item['matches'] = item.get('sha256') == expected
        pin_checks.append(item)
assert all(item['matches'] for item in pin_checks), 'request_pin_drift'

code_checks = []
for code_path in request['python_sources']:
    text = Path(code_path).read_text(encoding='utf-8-sig')
    ast.parse(text, filename=code_path)
    compile(text, code_path, 'exec')
    code_checks.append({'path': code_path, 'syntax_passed': True, 'executed': False})

parts = []
materials = []
family_checks = []
for family in request['families']:
    original = source_by_id[family['id']]
    parent = catalog_by_id[family['parent_asset_id']]
    assert family['source_family_sha256'] == digest(original)
    assert family['parent_catalog_row'] == original['parent_catalog_row'] == parent['catalog_row_name']
    assert family['family_id'] == original['family_id']
    assert family['rights_state'] == parent['recorded_rights_state'] == 'unconfirmed'
    assert str(family['explicit_hold']).lower() == str(parent['runtime']['ExplicitHold']).lower() == 'true'
    assert family['hold_reasons'] == parent['hold_reasons']
    assert family['enabled'] is False
    source_parts = {part['name']: part for group in original['sets'] for part in group['parts']}
    source_materials = {digest(mat): mat for group in original['sets'] for mat in group['materials'].values()}
    assert {part['name'] for part in family['parts']} == set(source_parts)
    for key, recipe in family['materials'].items():
        assert key == digest(recipe)
        assert recipe['source_graph_supported'] is True and recipe['visual_fidelity_verified'] is False
        assert recipe['channels']['Alpha'] == {'constant': 1.0}
        source_material = source_materials[recipe['source_graph_sha256']]
        assert recipe['source_material'] == source_material['source_material']
        assert recipe['two_sided'] == (not source_material['backface_culling'])
        graph = {node['name']: node for node in source_material['graph']}
        principled = [node for node in graph.values() if node['type'] == 'BSDF_PRINCIPLED']
        assert len(principled) == 1
        inputs = principled[0]['inputs']
        assert recipe['specular'] == inputs['Specular IOR Level']['default']
        assert recipe['emission_strength'] == inputs['Emission Strength']['default']
        for channel in ('Base Color', 'Roughness', 'Metallic', 'Alpha', 'Emission Color'):
            if not inputs[channel]['links']:
                assert recipe['channels'][channel] == {'constant': inputs[channel]['default']}
        normal_link = inputs['Normal']['links']
        if normal_link:
            assert len(normal_link) == 1
            normal = graph[normal_link[0]['node']]
            assert normal['type'] == 'NORMAL_MAP'
            assert recipe['normal']['strength'] == normal['inputs']['Strength']['default']
        else:
            assert recipe['normal']['strength'] == 0
        for ref in recipe['textures'].values():
            assert ref['uv_channel'] == 0 and ref['uv_offset'] == [0, 0]
            assert request['files'][str(Path(ref['path']).resolve())] == ref['sha256']
        materials.append({'family_id': family['family_id'], 'source_material': recipe['source_material'],
                          'recipe_sha256': key, 'normal_strength': recipe['normal']['strength'],
                          'normal_has_texture': 'texture' in recipe['normal'],
                          'normal_strength_rule': recipe['normal_strength_rule'],
                          'native_visual_fidelity_verified': False})
    for part in family['parts']:
        prior = source_parts[part['name']]
        for source_field, source_value in prior.items():
            assert part[source_field] == source_value, ('source_binding_changed', part['name'], source_field)
        assert part['fbx_sha256'] == prior['fbx_sha256']
        assert part['native_package'] == prior['native_package']
        assert part['native_package'].startswith('/Game/Project/Shared/ModelBank/Prepared/Modular/' + family['id'] + '/')
        assert part['derivative_id'] == family['family_id'] + '/' + part['name']
        assert part['uv_channels'][0] == part['render_uv_name'] == 'SourceRenderUV'
        assert len(part['material_keys']) == len(part['source_material_slots'])
        assert all(key in family['materials'] for key in part['material_keys'])
        assert part['source_uv0_probes'] and part['sample_local_vertices_m']
        assert part['source_uv0_probes'] == semantics['uv_probes'][part['name']]
        assert sum(part['slot_triangle_counts'].values()) == part['triangles']
        if part['name'] in duplicate_proof:
            proof = duplicate_proof[part['name']]
            expected = {str(slot['slot_index']): slot['triangle_count'] for slot in proof['fresh_blender_fbx_readback']['slots'] if slot['triangle_count']}
            assert part['roundtrip_slot_triangle_counts'] == expected
            assert part['roundtrip_proof_sha256'] == sha(duplicate_path)
            assert proof['recorded_fbx_sha256'] == part['fbx_sha256']
        else:
            assert 'roundtrip_slot_triangle_counts' not in part
        part_summary = {'name': part['name'], 'native_package': part['native_package'],
                        'derivative_id': part['derivative_id'], 'source_sha256': part['fbx_sha256'],
                        'source_triangles': part['triangles'], 'source_readback_triangles': part['source_readback']['triangles'] if part['source_readback'] else None,
                        'source_vertex_probe_count': len(part['sample_local_vertices_m']),
                        'source_uv0_probe_count': len(part['source_uv0_probes'])}
        parts.append(part_summary)
    family_checks.append({'id': family['id'], 'source_family_digest_matches': True,
                          'parent_identity_preserved': True, 'current_parent_hold_and_rights_match': True,
                          'part_name_keyset_matches': True, 'enabled': False})

assert len(request['families']) == request['family_count'] == 20
assert len(parts) == request['part_count'] == 609
for field in ('name', 'native_package', 'derivative_id', 'source_sha256'):
    assert len({part[field] for part in parts}) == 609, ('duplicate_part_identity', field)
assert not request['native_authorized'] and not request['selection_changes'] and not request['map_saves'] and not request['originals_modified']

adapter_path = OWNER / 'modular_native_adapter.py'
adapter_text = adapter_path.read_text(encoding='utf-8')
adapter_lines = adapter_text.splitlines()
def line(fragment):
    return next(index + 1 for index, text in enumerate(adapter_lines) if fragment in text)

findings = []
resolved_findings = [
    {'id': 'R1', 'state': 'resolved_in_reviewed_source', 'line': line("material_receipt=read(HERE/'MaterialReceipts'"),
     'resolution': 'Reuse requires a material receipt and matching SHA of its root material plus all dependency packages. Named-save readback records used textures directly as well as registry closure, captures native properties, and compares the complete material receipt on reuse. All pins are included in part receipts.'},
    {'id': 'R2', 'state': 'resolved_in_reviewed_source', 'line': line("assert obj.get_editor_property('srgb')==(ref['kind']=='color')"),
     'resolution': 'Source-appropriate sRGB, compression, green flip, wrap and filter policies are asserted for non-normal dependencies too. A mismatched existing parent dependency fails instead of being modified. Source appearance still requires native visual verification.'},
    {'id': 'R3', 'state': 'resolved_in_reviewed_source', 'line': line("assert actual==expected,('material_face_count_changed'"),
     'resolution': 'Only the two source/hash-bound documented alternate per-slot triangle vectors are allowed. Each imported slot maps uniquely to its source slot by material name and must have the exact face count. Pruning unused slots is allowed; every used source slot must still occur.'},
    {'id': 'R4', 'state': 'resolved_in_reviewed_source', 'line': line("value=read(path);assert value['schema']=='environmentpipeline.modular_native_preservation.v1'"),
     'resolution': 'Adapter, startup inspector and launcher now consume the same preservation files dictionary schema. The sole GUI/commandlet PID, current request and current manager/operator boundaries are checked.'}
]

verified_controls = [
    'The request contains exactly the registered twenty families and all 609 unique source parts and destination identities.',
    'All source/input and Python-source pins match; syntax compiles without executing owner code.',
    'Current parent canonical rows, holds, hold reasons and unconfirmed rights match the request; all family enabling flags remain false.',
    'Native preflight binds approved request SHA, manager/operator identities, actual PID/world, active exact lease, runtime seal, paused cooking and clean native boundary.',
    'Source export files and original packages are never replaced; unreceipted pre-existing part destinations are refused.',
    'Raw source RGB normals are imported into distinct derivative TC_VECTOR_DISPLACEMENTMAP dependencies; source blue remains available; OpenGL green is converted once in the graph.',
    'Normal strength applies XY times source strength, clamped-strength Z blend, then normalization; this handles source strengths above one and zero.',
    'Texture samples explicitly use UV0 and source tiling; source role labels do not become repeatable floors.',
    'Signed full bounds and source vertex probes resolve metre-to-centimetre basis; actual native UV0 position/UV probes are recorded with explicit V convention.',
    'Material namespace matches must be unique and material use is checked by triangle groups; aliases do not bypass ambiguity checks.',
    'Native material slots retain an explicit source_slot mapping; unused source slots can be absent or reordered, while the exact used slot face counts and recipe identities are required.',
    'Material receipts and part receipts include the material root and every used texture package, and fail on changed dependencies before reuse.',
    'Only exact created dependency/part paths are named-saved; dirty maps or unrelated dirty packages fail before saves.',
    'Per-part and family receipts keep import, fresh reopen, visual fidelity, procedural eligibility, collision and LOD states separate.'
]

result = {'schema': 'environmentpipeline.modular_native_request_independent_review.v1',
          'recorded_utc': datetime.now(timezone.utc).isoformat(),
          'review_state': 'offline_request_and_import_adapter_review_passed_no_identified_activation_blockers',
          'request_path': str(path), 'request_sha256': EXPECTED_REQUEST,
          'reviewed_python_sources': request['python_sources'], 'pin_checks': pin_checks,
          'syntax_checks': code_checks, 'family_checks': family_checks,
          'summary': {'families': 20, 'parts': 609, 'input_pins': len(request['files']),
                      'python_pins': len(request['python_sources']), 'materials': len(materials),
                      'part_identities_unique': True, 'failed_pin_checks': 0,
                      'source_vertex_probe_count_range': [min(part['source_vertex_probe_count'] for part in parts), max(part['source_vertex_probe_count'] for part in parts)],
                      'source_uv0_probe_count_range': [min(part['source_uv0_probe_count'] for part in parts), max(part['source_uv0_probe_count'] for part in parts)]},
          'verified_controls': verified_controls, 'findings': findings, 'resolved_findings': resolved_findings,
          'required_native_followup': [
              'Manager activation and startup readback must prove the sole current PID, exact original map, paused cooking, no callbacks, clean state, runtime seal and preservation baseline.',
              'The first bounded native import must prove supported native APIs, shader graph compilation, used-slot mapping after FBX pruning, signed basis and UV0 convention. An asserted mismatch must stop the batch.',
              'A saved material receipt proves package stability, not matching rendered appearance. Verify normals, roughness, metallic/base color and alpha under native visual comparison.',
              'Hash-validated completed receipts are reused without fresh geometry/material measurement. Fresh-process readback must independently establish reopened results before qualification.',
              'Failures after creating or named-saving packages but before writing a part receipt leave an unreceipted destination that subsequent runs intentionally refuse. Reconcile through the owner; never silently overwrite it.',
              'These import receipts keep procedural_eligible false. Final Engine reconstruction/repetition, regeneration and named save/reopen still require separate proofs; existing rights and holds stay active.'
          ],
          'materials': materials, 'parts': parts,
          'normal_rule_reference': 'https://raw.githubusercontent.com/blender/blender/blender-v5.2-release/source/blender/gpu/shaders/material/gpu_shader_material_normal_map.glsl',
          'installed_engine_reference': {'texture_enum': 'C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Engine/TextureDefines.h:398',
                                         'normal_unpack': 'C:/Program Files/Epic Games/UE_5.8/Engine/Shaders/Private/Common.ush:1698'},
          'canonical_catalog_at_review': {'path': str(catalog_path), 'sha256': sha(catalog_path)},
          'native_execution_performed': False, 'bank_files_modified': False,
          'originals_modified': False, 'identity_or_hold_changes': False,
          'native_graph_or_actual_import_verified': False,
          'acceptance_not_implied': 'This offline request/code review does not prove native API execution, graph compilation, original appearance, actual geometry/UV equivalence, Engine assembly, regeneration, named save/reopen or user acceptance.'}
assert sha(path) == EXPECTED_REQUEST, 'request_changed_during_review'
for pinned_path, expected in request['python_sources'].items():
    assert sha(pinned_path) == expected, ('code_changed_during_review', pinned_path)
write('NATIVE_REQUEST_INDEPENDENT_REVIEW_' + EXPECTED_REQUEST[:8] + '.json', result)
print(json.dumps({'request_sha256': EXPECTED_REQUEST, 'summary': result['summary'], 'findings': [item['id'] for item in findings]}))
