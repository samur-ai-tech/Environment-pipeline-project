"""Save exactly four reviewed EpicResident2K textures and the Shujaiya child.

Preparation only: root must independently review, pin and execute this companion.
Import without ARGS is idle. Full read-only copy readiness/identity, three actual
matched Lit PNGs and an independent exact named visual-save approval are required.
Only five explicit save_loaded_asset calls are permitted: copies before child.
No master/map save, compile, setters, copying, Cook/Bake or residency/CVar call.
ARGS: expected_pid=26820,label,reviewed_visual_stage and SHA-bound plan_receipt,
mutation_backup,resident_verify_receipt,visual_review_receipt (each *_sha256).
The successful creation, strict ordinary-frame inspection and binding receipts
are inherited and checked through the successful resident verify's input_files.
"""
import copy
import datetime
import hashlib
import json
import math
import os
import struct
import types
from pathlib import Path

FROZEN_SHA = 'e535a74bca2ca6b9ca7856db8152d5b938ef79597b3a17f35c48e14a0dd69f6e'
PROPERTY_SHA = 'bdba22a3bcf801663788166649e3fd593704507f133995a1085ed0b37c2404b4'
PLAN_SHA = 'ca022f90c571f9e77ebde9546545c998e85bd26e47494a41f7608f5618191d34'
BACKUP_SHA = 'ef0bb74f6083a0c0aab36af33ee6c541c684fbaba960d3345cd3406ca7105465'
EPIC_SHA = '9b7785af647a3eaf5674cf45c8f1b56aa9d80da1f02d0848da46ebad391598b6'
ASSIGNMENT_SHA = 'c3c49a9baabdfe357a5852d383501d0ac0396bfc7a795b58762ac52b61d3fec7'
CAPTURE_SHA = '6a8ca3e3209d9a39f79c2916fe2d715f0bdefdf177fb04f2de677e4af228ac1c'
RESIDENT_HELPER_SHA = 'e97858becfa1df6a405297779e32d224c49d1c32034d0d5dcb66f7d7b690d4bf'
ORIGINAL_FAILED_HELPER_SHA = 'fa1721fdbd5cd8d36599bfd587adbf092dc2f2a2f018fd1522c5b662c4d953d7'
ORIGINAL_FAILED_RECEIPT_SHA = 'c1c36213025db1c11e67694f82a3f7b7c0be3747e9e3d97b2340b16037e177c1'
EXPECTED_PID = 26820
AREA = 'GazaShujaiya'


def sha(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def load_definitions():
    import unreal
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
    file = (root / 'Staging/GroundPainting_2026-10-04/native_ground_texture_policy.py').resolve(strict=True)
    data = file.read_bytes()
    check(hashlib.sha256(data).hexdigest() == PROPERTY_SHA, 'Frozen property definitions changed')
    p = types.ModuleType('epic_resident_save_property_definitions')
    p.__file__ = str(file)
    exec(compile(data, str(file), 'exec'), p.__dict__)
    check('ARGS' not in p.__dict__ and sha(file) == PROPERTY_SHA, 'Property entry point must stay idle')
    h = p.load_helper()
    check(sha(h.SCRIPT) == FROZEN_SHA, 'Frozen graph definitions changed')
    return h, p, file


def bound(h, args, key):
    file = Path(args[key]).resolve(strict=True)
    check(file.is_relative_to(h.REV) and file.suffix == '.json', 'Review receipt outside Revision: ' + key)
    check(sha(file) == args[key + '_sha256'], 'Bound receipt changed: ' + key)
    return file, json.loads(file.read_text(encoding='utf-8-sig'))


def near(values, expected, tolerance, angular=False):
    check(isinstance(values, list) and len(values) == len(expected), 'Malformed measured camera')
    deltas = [((float(a) - float(b) + 180.0) % 360.0 - 180.0) if angular else float(a) - float(b)
              for a, b in zip(values, expected)]
    return all(math.isfinite(value) and abs(value) <= tolerance for value in deltas)


def camera_rotation(camera):
    dx, dy, dz = [float(b) - float(a) for a, b in zip(camera['eye'], camera['target'])]
    return [math.degrees(math.atan2(dz, math.hypot(dx, dy))), math.degrees(math.atan2(dy, dx)), 0.0]


def png_info(file):
    """Validate a complete PNG chunk envelope without importing an image editor."""
    data = Path(file).read_bytes()
    check(data[:8] == b'\x89PNG\r\n\x1a\n', 'Not an actual PNG')
    offset, size, finished = 8, None, False
    while offset + 12 <= len(data):
        length = struct.unpack('>I', data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + length
        check(end <= len(data), 'Incomplete PNG chunk')
        if offset == 8:
            check(kind == b'IHDR' and length == 13, 'Missing PNG header')
            size = list(struct.unpack('>II', data[offset + 8:offset + 16]))
        if kind == b'IEND':
            check(length == 0 and end == len(data), 'Incomplete/trailing PNG end')
            finished = True
            break
        offset = end
    check(finished and size == [1600, 1000], 'Complete actual 1600x1000 PNG required')
    return {'sha256': hashlib.sha256(data).hexdigest(), 'dimensions': size}


def visual_evidence(h, args, visual_file, visual, verify_file, named_map, allowed):
    stage = args['reviewed_visual_stage']
    check(stage and all(c.isascii() and (c.isalnum() or c == '_') for c in stage), 'Unsafe visual stage')
    check(visual['schema'] == 'environmentpipeline.ground_visual_review.v1' and
          visual['status'] == 'APPROVED_BOUNDED_EPIC_RESIDENT_SAVE', 'Independent resident visual-save approval required')
    check(visual['pid'] == os.getpid() and visual['area'] == AREA and visual['world'] == named_map,
          'Visual review process/world mismatch')
    check(visual['stage'] == stage and visual['save_approved_within_scope'] is True and
          set(visual['named_save_scope']) == allowed and len(visual['named_save_scope']) == 5,
          'Exact five-package visual-save scope required')
    check(visual['viewmode'] == 3 and visual['actual_lit_measured'] is True and
          visual['camera_matched_all_three'] is True, 'Actual matched Lit images required')
    check(Path(visual['source_verify_receipt']).resolve(strict=True) == verify_file and
          visual['source_verify_receipt_sha256'] == sha(verify_file), 'Visual review used another native verification')
    cameras_file = (h.HERE / ('CAMERAS_' + AREA + '.json')).resolve(strict=True)
    cameras = json.loads(cameras_file.read_text(encoding='utf-8-sig'))
    check(set(cameras) == {'close', 'middle', 'wide'}, 'Exact existing camera presets required')
    camera_sha = sha(cameras_file)
    capture_helper = (h.HERE / 'native_capture_epic_resident.py').resolve(strict=True)
    check(sha(capture_helper) == CAPTURE_SHA, 'Reviewed resident capture helper changed')
    expected_images = {str((h.HERE / 'Images' / (AREA + '_' + stage + '_' + shot + '.png')).resolve())
                       for shot in cameras}
    check(set(visual['images']) == expected_images, 'Exactly three current-stage images required')
    records = []
    for shot in ('close', 'middle', 'wide'):
        image = (h.HERE / 'Images' / (AREA + '_' + stage + '_' + shot + '.png')).resolve(strict=True)
        row = visual['images'][str(image)]
        measured_png = png_info(image)
        check(row['sha256'] == measured_png['sha256'] and row['dimensions'] == [1600, 1000] and
              row['shot'] == shot and row['viewmode'] == 3, 'Approved actual PNG identity differs: ' + shot)
        check(all(row[k] is True for k in ('camera_matches', 'actual_lit_measured', 'visually_inspected')),
              'Actual image was not independently inspected: ' + shot)
        capture_file = (h.HERE / ('CAPTURE_' + AREA + '_' + stage + '_' + shot + '.json')).resolve(strict=True)
        check(Path(row['capture_receipt']).resolve(strict=True) == capture_file and
              row['capture_receipt_sha256'] == sha(capture_file), 'Capture receipt changed: ' + shot)
        capture = json.loads(capture_file.read_text(encoding='utf-8-sig'))
        check(capture['schema'] == 'environmentpipeline.ground_epic_capture.v1' and
              capture['status'] == 'MATCHED_ACTUAL_LIT_CAPTURE_REQUESTED' and
              capture['helper_sha256'] == CAPTURE_SHA and capture['resident_plan_sha256'] == PLAN_SHA,
              'Unsupported or changed resident capture: ' + shot)
        check(capture['pid'] == row['capture_pid'] == os.getpid() and
              capture['world'] == row['capture_world'] == named_map and capture['area'] == AREA and
              capture['stage'] == stage and capture['shot'] == shot and
              Path(capture['path']).resolve(strict=True) == image, 'Capture identity mismatch: ' + shot)
        check(capture['scene_content_preservation_passed'] is True and
              all(capture[k] is False for k in ('content_mutation', 'compile_or_save_called', 'force_residency_called')),
              'Capture content preservation failed: ' + shot)
        check(capture['requested_dimensions'] == [1600, 1000] and capture['requested'] is True and
              capture['valid_task'] is True and capture['viewmode_readback'] == '<ViewModeIndex.VMI_LIT: 3>' and
              capture['active_viewport_key'], 'Actual Lit request/readback required: ' + shot)
        check(capture['camera_file_sha256'] == camera_sha and capture['camera'] == cameras[shot],
              'Existing camera definition changed: ' + shot)
        measured = capture['camera_readback']
        check(all(measured[k] is True for k in ('eye_match', 'rotation_match', 'fov_match',
              'primary_eye_match', 'primary_rotation_match', 'all_supported_matches')), 'Camera mismatch: ' + shot)
        expected_rotation = camera_rotation(cameras[shot])
        for key in ('keyed', 'primary'):
            check(near(measured[key]['eye'], cameras[shot]['eye'], .01) and
                  near(measured[key]['rotation'], expected_rotation, .01, angular=True), 'Camera values differ: ' + shot)
        check(math.isfinite(float(measured['keyed']['fov'])) and
              abs(float(measured['keyed']['fov']) - float(cameras[shot]['fov'])) <= .001, 'FOV mismatch: ' + shot)
        records.append({'shot': shot, 'image': str(image), 'image_sha256': measured_png['sha256'],
                        'capture_receipt': str(capture_file), 'capture_receipt_sha256': sha(capture_file)})
    return {'visual_review_receipt': str(visual_file), 'visual_review_receipt_sha256': sha(visual_file),
            'camera_file': str(cameras_file), 'camera_file_sha256': camera_sha, 'images': records}


def compare_instances(h, original, current, child_path, bindings):
    check(set(original) == set(current), 'Material instance set changed')
    association = h.plain(h.unreal.MaterialParameterAssociation.GLOBAL_PARAMETER)
    for path, prior in original.items():
        live = current[path]
        if path != child_path:
            check(live == prior, 'Base or Rimal instance changed')
            continue
        check(set(prior) == set(live), 'Child instance schema changed')
        for key in prior:
            if key not in ('textures', 'texture_overrides'):
                check(live[key] == prior[key], 'The 21-control recipe/non-texture identity changed: ' + key)
        check(live['textures'] == dict(prior['textures'], **bindings), 'Only eight resident bindings may change')
        check([r for r in live['texture_overrides'] if r['name'] not in bindings] ==
              [r for r in prior['texture_overrides'] if r['name'] not in bindings], 'Other texture overrides changed')
        selected = [r for r in live['texture_overrides'] if r['name'] in bindings]
        check(len(selected) == 8 and {r['name'] for r in selected} == set(bindings), 'Duplicate/missing resident override')
        check(all(r['association'] == association and r['index'] == -1 and r['value'] == bindings[r['name']]
                  for r in selected), 'Resident override association/index/value changed')


def copy_contract(h, p, original, copied):
    check(original['class'] == copied['class'] == 'Texture2D', 'Expected native Texture2D')
    check(all(copied['metadata'][key] == {'status': 'READ', 'value': 2048} for key in ('size_x', 'size_y')),
          'Copied native resource is not ready at original 2048 resolution')
    check(set(original['properties']) == set(copied['properties']), 'Copy property schema differs')
    for name, expected in original['properties'].items():
        actual = copied['properties'][name]
        if name in ('never_stream', 'max_texture_size'):
            check(actual == {'status': 'READ', 'value': True if name == 'never_stream' else 2048}, 'Copy policy differs')
        elif expected['status'] == 'READ':
            check(actual == expected, 'Readable copy PBR/LOD/filter/mip field changed: ' + name)
        else:
            check(actual['status'] == expected['status'], 'Unexposed field status differs; value is not established')
    check(p.value(original, 'never_stream') is False and p.value(original, 'max_texture_size') == 0,
          'Original source policy differs')
    check(p.value(original, 'global_force_mip_levels_to_be_resident') is False and
          p.value(copied, 'global_force_mip_levels_to_be_resident') is False, 'Persistent global force is forbidden')
    normal = original['path'].endswith('_N')
    check(p.value(original, 'srgb') is (not normal) and p.value(original, 'compression_settings') ==
          h.plain(h.unreal.TextureCompressionSettings.TC_NORMALMAP if normal else
                  h.unreal.TextureCompressionSettings.TC_DEFAULT), 'Original color/normal semantics differ')


def save(args):
    check(isinstance(RESIDENT_HELPER_SHA, str) and len(RESIDENT_HELPER_SHA) == 64,
          'Preparation incomplete: independent resident helper is not frozen')
    h, p, property_script = load_definitions()
    check(os.getpid() == args['expected_pid'] == EXPECTED_PID, 'Wrong sole current process')
    p.sole_editor()
    assignment_file = h.HERE / 'ASSIGNMENT.json'
    check(sha(assignment_file) == ASSIGNMENT_SHA, 'Assignment changed')
    assignment = json.loads(assignment_file.read_text(encoding='utf-8-sig'))
    named_map = h.unreal.get_editor_subsystem(h.unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
    check(named_map == assignment['original_maps'][AREA], 'Only original Shujaiya may be saved here')
    sources, actors = h.guard(assignment, named_map, require_authoring=True)
    check(len(sources) == 12, 'Exactly twelve sealed runtime modules required')
    files, docs = {}, {}
    for key in ('plan_receipt', 'mutation_backup', 'resident_verify_receipt', 'visual_review_receipt'):
        files[key], docs[key] = bound(h, args, key)
    plan, backup, verified, visual = (docs[k] for k in ('plan_receipt', 'mutation_backup', 'resident_verify_receipt', 'visual_review_receipt'))
    check(files['plan_receipt'] == (h.REV / 'EPIC_RESIDENT_PLAN_R028.json').resolve(strict=True) and
          sha(files['plan_receipt']) == PLAN_SHA and sha(files['mutation_backup']) == BACKUP_SHA, 'Exact plan/backup changed')
    check(plan['schema'] == 'environmentpipeline.epic_resident_plan.v1' and plan['pid'] == EXPECTED_PID and
          plan['world'] == named_map and plan['area'] == AREA, 'Resident plan identity differs')
    check(plan['policy'] == {'never_stream': True, 'max_texture_size': 2048,
          'global_force_mip_levels_to_be_resident': False} and plan['no_source_upscale'] is True and
          plan['original_epic_assets_immutable'] is True, 'Only the original 2K owned-copy policy is allowed')
    items = plan['items']
    check(len(items) == len({r['source'] for r in items}) == len({r['destination'] for r in items}) == 4,
          'Exactly four unique sources and owned copies required')
    for row in items:
        name = row['source'].split('.')[-1]
        copied_name = name + '_GeoCityResident2K'
        check(set(row) == {'source', 'destination'} and name in
              ('T_Ground_Gravel_D', 'T_Ground_Gravel_N', 'T_Rock_Sandstone_D', 'T_Rock_Sandstone_N') and
              row['source'] == '/Game/StarterContent/Textures/' + name + '.' + name and
              row['destination'] == h.SURFACE + '/Textures/EpicResident2K/' + copied_name + '.' + copied_name,
              'Unexpected source/copy identity')
    check(len(plan['bindings']) == 8 and set(plan['bindings'].values()) == {r['destination'] for r in items},
          'Exactly eight consumer bindings to these four copies required')
    check(backup['ready'] is True and backup['ready_for_epic_resident'] is True and backup['pid'] == EXPECTED_PID and
          backup['world'] == named_map and backup['execution_thread_id'] == assignment['execution_thread_id'] and
          backup['plan_sha256'] == PLAN_SHA, 'Exact mutation backup is not ready')
    for original, row in backup['file_bindings'].items():
        check(sha(Path(row['backup']).resolve(strict=True)) == row['sha256'], 'Mutation backup changed: ' + original)
    check(verified['schema'] == 'environmentpipeline.epic_resident_recovery.v1' and
          verified['status'] == 'IDENTITY_VERIFIED_READ_ONLY_EPIC_RESIDENT' and verified['mode'] == 'verify' and
          verified['native_mutation'] is False and verified['pid'] == os.getpid() and verified['world'] == named_map and
          verified['area'] == AREA, 'Full actual read-only resident verify is required')
    check(verified['helper_sha256'] == RESIDENT_HELPER_SHA and verified['plan'] == plan and
          verified['plan_sha256'] == PLAN_SHA and verified['graph_count'] == 1015, 'Resident verify source/plan mismatch')
    check(all(verified[k] is True for k in ('complete_code_input_output_mip_identity_equal', 'preserved_grass',
          'preserved_scene', 'preserved_cvars', 'preserved_original_files', 'preserved_epic_texture_properties',
          'all_four_resources_strict_ready')),
          'Full resident verification/readiness did not pass')
    before_verify, after_verify = copy.deepcopy(verified['before']), copy.deepcopy(verified['after'])
    for state in (before_verify, after_verify):
        for texture in state['epic_textures'].values():
            texture.pop('metadata')
        state['held_texture'].pop('metadata')
    check(before_verify == after_verify, 'Read-only verification observed changing persistent state')
    for key in ('nodes', 'roots', 'material_settings', 'instances', 'grass', 'scene', 'cvars'):
        check(verified[key] == verified['after'][key], 'Resident readback alias differs: ' + key)
    check(verified['package_sha256'] == verified['after']['disk'], 'Resident disk alias differs')
    for key, row in verified['input_files'].items():
        file = Path(row['file']).resolve(strict=True)
        check(file.is_relative_to(h.HERE) and sha(file) == row['sha256'], 'Resident verification input changed: ' + key)
    reference_row = verified['input_files']['reference_receipt']
    reference_file = Path(reference_row['file']).resolve(strict=True)
    reference = json.loads(reference_file.read_text(encoding='utf-8-sig'))
    check(reference_row['sha256'] == plan['reference_sha256'] and
          reference['status'] == 'IDENTITY_VERIFIED_READ_ONLY_EPIC_GROUND', 'Actual original Epic fresh reference required')
    ready_row = verified['input_files']['inspect_receipt']
    ready_file = Path(ready_row['file']).resolve(strict=True)
    ready = json.loads(ready_file.read_text(encoding='utf-8-sig'))
    check(ready['status'] == 'EPIC_RESIDENT_RECOVERY_CANDIDATE_REQUIRES_ROOT_REVIEW' and ready['mode'] == 'inspect' and
          ready['inspect_stage'] == 'BIND_READY' and ready['all_four_resources_strict_ready'] is True and
          ready['pid'] == os.getpid() and ready['world'] == named_map and ready['plan_sha256'] == PLAN_SHA and
          ready['helper_sha256'] == RESIDENT_HELPER_SHA and ready['native_mutation'] is False,
          'Actual separately observed native copy readiness is required before any save')
    creation_row = verified['input_files']['prepared_receipt']
    creation_file = Path(creation_row['file']).resolve(strict=True)
    creation = json.loads(creation_file.read_text(encoding='utf-8-sig'))
    failure_row = verified['input_files']['failure_receipt']
    failure_file = Path(failure_row['file']).resolve(strict=True)
    failed = json.loads(failure_file.read_text(encoding='utf-8-sig'))
    check(sha(failure_file) == ORIGINAL_FAILED_RECEIPT_SHA and
          failed['schema'] == 'environmentpipeline.epic_resident.v1' and
          failed['status'] == 'FAILED_PARTIAL_STATE_PRESERVED' and failed['mode'] == 'apply' and
          failed['helper_sha256'] == ORIGINAL_FAILED_HELPER_SHA and failed['plan_sha256'] == PLAN_SHA and
          failed['pid'] == EXPECTED_PID and failed['world'] == named_map and len(failed['created_assets']) == 1 and
          failed['bound_parameters'] == [] and failed['update_material_instance_called'] is False and
          failed['explicit_save_called'] is False, 'Original failed one-copy provenance changed')
    check(creation['status'] == 'EPIC_RESIDENT_RECOVERY_COPIES_CREATED_PENDING_READINESS' and creation['mode'] == 'apply' and
          creation['helper_sha256'] == RESIDENT_HELPER_SHA and creation['pid'] == os.getpid() and
          creation['world'] == named_map and creation['plan_sha256'] == PLAN_SHA and
          creation['bound_parameters'] == [] and creation['update_material_instance_called'] is False and
          len(creation['created_assets']) == 3 and creation['reused_assets'] == failed['created_assets'] and
          len(creation['all_copy_provenance']) == 4 and
          {row['source']: row['destination'] for row in creation['all_copy_provenance']} ==
          {row['source']: row['destination'] for row in items} and
          creation['all_copy_provenance'] == creation['reused_assets'] + creation['created_assets'],
          'Recovery must honestly reuse one failed-origin copy and create only three')
    check(ready['input_files']['prepared_receipt']['sha256'] == sha(creation_file), 'Native ready inspection used another creation')
    binding_row = verified['input_files']['bind_receipt']
    binding_file = Path(binding_row['file']).resolve(strict=True)
    binding = json.loads(binding_file.read_text(encoding='utf-8-sig'))
    check(binding['status'] == 'EPIC_RESIDENT_RECOVERY_BOUND_NO_EXPLICIT_SAVE' and binding['mode'] == 'bind' and
          binding['helper_sha256'] == RESIDENT_HELPER_SHA and binding['pid'] == os.getpid() and
          binding['world'] == named_map and binding['plan_sha256'] == PLAN_SHA and
          binding['all_four_resources_strict_ready'] is True and
          binding['input_files']['inspect_receipt']['sha256'] == sha(ready_file) and
          binding['input_files']['prepared_receipt']['sha256'] == sha(creation_file) and
          binding['after']['instances'] == verified['instances'], 'Exact native bind provenance differs')
    for document in (verified, ready, creation, binding):
        check(document['schema'] == 'environmentpipeline.epic_resident_recovery.v1' and
              document['origin_helper_sha256'] == ORIGINAL_FAILED_HELPER_SHA and
              document['failure_receipt_sha256'] == ORIGINAL_FAILED_RECEIPT_SHA and
              document['creation_mode'] == 'RECOVERY_REUSE_ONE_CREATE_THREE' and
              document['input_files']['failure_receipt']['sha256'] == ORIGINAL_FAILED_RECEIPT_SHA,
              'Recovery stage cannot promote the old failed creation to success')
    epic_file = (h.REV / 'EPIC_STARTER_GROUND_NATIVE_READONLY_PID32464.json').resolve(strict=True)
    check(sha(epic_file) == EPIC_SHA, 'Pinned Epic original inspection changed')
    epic = json.loads(epic_file.read_text(encoding='utf-8-sig'))
    for row in items:
        original_size = epic['textures'][row['source']]['metadata']
        check(all(original_size[key] == {'status': 'READ', 'value': 2048} for key in ('size_x', 'size_y')),
              'Immutable original source inspection did not measure 2048 resolution')
    resident_script = (h.HERE / 'native_ground_epic_resident_recovery.py').resolve(strict=True)
    check(sha(resident_script) == RESIDENT_HELPER_SHA, 'Frozen resident helper changed')
    origin_script = (h.HERE / 'native_ground_epic_resident.py').resolve(strict=True)
    check(sha(origin_script) == ORIGINAL_FAILED_HELPER_SHA, 'Frozen failed-origin helper changed')
    master = h.unreal.load_asset(h.MASTER)
    child = h.unreal.load_asset(assignment['material_contract']['area_instances'][AREA])
    child_path, child_package = h.path(child), child.get_outermost().get_path_name()
    copies = {r['destination'].split('.')[0]: h.unreal.load_asset(r['destination']) for r in items}
    allowed = set(copies) | {child_package}
    check(len(allowed) == 5 and h.MASTER not in allowed and set(verified['allowed_dirty_packages']) == allowed,
          'Only four copied textures and current child may be saved')

    def dirty():
        return {'maps': sorted(h.path(v) for v in h.unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                'content': sorted(h.path(v) for v in h.unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}

    def snapshot():
        modules, current_actors = h.guard(assignment, named_map, require_authoring=True)
        check(modules == sources == verified['after']['sources'] and len(modules) == 12, 'Runtime source identity changed')
        nodes = {h.path(e): h.describe(master, e) for e in h.LIB.get_material_expressions(master)}
        check(len(nodes) == 1015 and nodes == verified['nodes'] == reference['nodes'], 'Retained full graph/code/mips changed')
        roots = {k: h.path(h.LIB.get_material_property_input_node(master, v)) for k, v in h.PROPERTIES.items()}
        settings = {k: h.plain(master.get_editor_property(k)) for k in verified['material_settings']}
        check(roots == verified['roots'] == reference['roots'] and
              settings == verified['material_settings'] == reference['material_settings'], 'Material roots/settings changed')
        instances = {k: h.material_state(master, h.unreal.load_asset(k)) for k in verified['instances']}
        check(instances == verified['instances'], 'Verified MI state changed')
        compare_instances(h, reference['instances'], instances, child_path, plan['bindings'])
        grass_nodes = [e for e in h.LIB.get_material_expressions(master)
                       if isinstance(e, h.unreal.MaterialExpressionLandscapeGrassOutput)]
        check(len(grass_nodes) == 1, 'Expected one preserved Grass output')
        grass = {'graph': {k: h.describe(master, e) for k, e in h.reachable(master, grass_nodes).items()},
                 'settings': h.grass_settings(h.unreal.load_asset(h.GRASS)),
                 'effective_coverage': {h.path(a): float(h.LIB.get_material_instance_scalar_parameter_value(
                     child, 'GeoCity_GrassCoverage')) for a in current_actors if isinstance(a, h.unreal.LandscapeProxy)}}
        scene = h.scene_state(current_actors)
        cvars = {name: h.unreal.SystemLibrary.get_console_variable_string_value(name) for name in p.CVARS}
        check(grass == verified['grass'] == reference['grass'] and scene == verified['scene'] == reference['scene'] and
              cvars == verified['cvars'] == reference['cvars'],
              'Scene/Grass/CVars changed')
        epic_rows = {asset: p.texture_details(h, h.unreal.load_asset(asset)) for asset in epic['textures']}
        for asset, row in epic_rows.items():
            check(row['properties'] == epic['textures'][asset]['properties'] ==
                  verified['after']['epic_textures'][asset]['properties'], 'Original Epic properties changed')
        held_path = h.SURFACE + '/Textures/Resident4K/T_Sand_01_Albedo_GeoCityResident4K'
        held = p.texture_details(h, h.unreal.load_asset(held_path))
        check(held['properties'] == verified['after']['held_texture']['properties'], 'Held unused copy properties changed')
        source_rows, copy_rows, copy_disks = {}, {}, {}
        for row in items:
            original = epic_rows[row['source']]
            copied = p.texture_details(h, h.unreal.load_asset(row['destination']))
            copy_contract(h, p, original, copied)
            check(copied['properties'] == verified['copy_textures'][row['destination']]['properties'] ==
                  ready['copy_textures'][row['destination']]['properties'], 'Ready/verified copied texture properties differ')
            check(original['properties'] == epic['textures'][row['source']]['properties'], 'Original Epic PBR fields changed')
            source_rows[row['source']] = {k: original[k] for k in ('path', 'class', 'properties')}
            copy_rows[row['destination']] = {k: copied[k] for k in ('path', 'class', 'properties')}
            copy_disks[row['destination'].split('.')[0]] = h.disk_state(h.package_file(row['destination']))
        disk = {file: sha(Path(file).resolve(strict=True)) for file in verified['package_sha256']}
        for asset, expected in epic['original_file_sha256'].items():
            check(disk[str(h.package_file(asset).resolve(strict=True))] == expected, 'Original Epic package changed')
        return {'sources': modules, 'nodes': nodes, 'roots': roots, 'material_settings': settings,
                'instances': instances, 'grass': grass, 'scene': scene, 'cvars': cvars,
                'source_properties': source_rows, 'copy_properties': copy_rows, 'copy_disks': copy_disks,
                'epic_properties': {asset: row['properties'] for asset, row in epic_rows.items()},
                'held_properties': held['properties'],
                'disk': disk, 'dirty': dirty()}

    before = snapshot()
    check(before['disk'] == verified['package_sha256'] and before['dirty'] == verified['after']['dirty'],
          'Verified existing files/dirty state changed')
    check(before['dirty'] == {'maps': [], 'content': sorted(allowed)}, 'Exactly the five reviewed packages must be dirty')
    check(all(not row['exists'] for row in before['copy_disks'].values()), 'New copied texture files must be unsaved')
    check(all(row['asset_exists'] and not row['disk']['exists'] for row in verified['after']['copies'].values()) and
          {r['destination'] for r in items} == set(verified['after']['copies']), 'Native verification copy disk provenance differs')
    protected = {k: v for k, v in before['disk'].items() if Path(k).resolve() != h.package_file(child_package).resolve()}
    check(len(before['disk']) == 113 and str(h.package_file(h.MASTER).resolve(strict=True)) in protected,
          'Complete 113-file guard including unchanged clean master required')
    visual_binding = visual_evidence(h, args, files['visual_review_receipt'], visual,
                                     files['resident_verify_receipt'], named_map, allowed)
    save_asset = getattr(h.unreal.EditorAssetLibrary, 'save_loaded_asset', None)
    check(callable(save_asset), 'Supported explicit named asset save API is unavailable')
    check(all(isinstance(v, h.unreal.Texture2D) for v in copies.values()) and
          isinstance(child, h.unreal.MaterialInstanceConstant), 'Unexpected saved asset types')
    label = args['label']
    check(label and all(c.isascii() and (c.isalnum() or c == '_') for c in label), 'Unsafe save label')
    output = h.REV / ('EPIC_RESIDENT_NAMED_SAVE_' + AREA + '_' + label + '_PID' + str(os.getpid()) + '.json')
    once = h.REV / ('EPIC_RESIDENT_NAMED_SAVE_ONCE_' + PLAN_SHA + '.json')
    check(not output.exists() and not once.exists(), 'Preserve previous save/attempt receipts')
    script = (h.HERE / 'native_epic_resident_save.py').resolve(strict=True)
    script_sha = sha(script)
    result = {'schema': 'environmentpipeline.epic_resident_named_save.v1', 'status': 'PRE_SAVE_CHECKS_PASSED',
              'pid': os.getpid(), 'world': named_map, 'area': AREA,
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'helper_sha256': script_sha,
              'resident_helper_sha256': RESIDENT_HELPER_SHA, 'plan_sha256': PLAN_SHA,
              'origin_helper_sha256': ORIGINAL_FAILED_HELPER_SHA,
              'failure_receipt_sha256': ORIGINAL_FAILED_RECEIPT_SHA,
              'creation_provenance': creation['all_copy_provenance'],
              'input_files': {k: {'file': str(v), 'sha256': sha(v)} for k, v in files.items()},
              'visual_evidence': visual_binding, 'named_packages': sorted(allowed),
              'dirty_before': before['dirty'], 'named_files_before': before['copy_disks'],
              'protected_package_sha256_before': protected, 'graph_count': 1015,
              'graph_sha256': h.digest(before['nodes']), 'save_attempts': [],
              'master_save_called': False, 'map_save_called': False, 'save_all_called': False,
              'compile_called': False, 'texture_or_material_setters_called': False,
              'copying_called': False, 'cook_or_bake_called': False, 'force_or_loading_called': False,
              'user_acceptance': 'PENDING', 'ordinary_visual_persistence': 'PENDING_FRESH_PROCESS_REOPEN'}
    check(snapshot() == before, 'State changed during final save preparation')
    check(all(sha(file) == args[key + '_sha256'] for key, file in files.items()), 'Review input changed')
    with once.open('x', encoding='utf-8') as file:
        file.write(json.dumps({'status': 'ATTEMPT_RESERVED', 'helper_sha256': script_sha, 'receipt': str(output)}))
    with output.open('x', encoding='utf-8') as file:
        file.write(json.dumps(result, indent=2))
    failure = None
    try:
        remaining = set(allowed)
        for package, asset in [*sorted(copies.items()), (child_package, child)]:
            p.sole_editor()
            current_sources, _ = h.guard(assignment, named_map, require_authoring=True)
            check(current_sources == sources and dirty() == {'maps': [], 'content': sorted(remaining)},
                  'Exact lease/source/dirty state changed before named save')
            row = {'package': package, 'attempted': True, 'returned': None}
            result['save_attempts'].append(row)
            row['returned'] = bool(save_asset(asset, only_if_is_dirty=True))
            row['disk_after_call'] = h.disk_state(h.package_file(package))
            check(row['returned'] is True and row['disk_after_call']['exists'] and
                  'sha256' in row['disk_after_call'], 'Named asset save did not report success: ' + package)
            remaining.remove(package)
        after = snapshot()
        check(after['dirty'] == {'maps': [], 'content': []}, 'Named saves did not leave the whole editor clean')
        for key in before:
            if key not in ('dirty', 'disk', 'copy_disks'):
                check(after[key] == before[key], 'Preserved state changed during save: ' + key)
        check({k: after['disk'][k] for k in protected} == protected, 'Source/master/map/protected file changed')
        named_hashes = {package: sha(h.package_file(package)) for package in sorted(allowed)}
        check(all(row['exists'] and 'sha256' in row for row in after['copy_disks'].values()), 'Saved copy file missing')
        p.sole_editor()
        check(sha(script) == script_sha and sha(resident_script) == RESIDENT_HELPER_SHA and
              sha(origin_script) == ORIGINAL_FAILED_HELPER_SHA and
              sha(property_script) == PROPERTY_SHA and sha(h.SCRIPT) == FROZEN_SHA and
              sha(assignment_file) == ASSIGNMENT_SHA, 'Helper/assignment identity changed during save')
        check(all(sha(file) == args[key + '_sha256'] for key, file in files.items()), 'Bound save approvals changed')
        check(visual_evidence(h, args, files['visual_review_receipt'], visual,
              files['resident_verify_receipt'], named_map, allowed) == visual_binding, 'Approved images/review changed')
        result.update(status='NAMED_EPIC_RESIDENT_SAVE_VERIFIED_CLEAN', dirty_after=after['dirty'],
                      named_package_sha256=named_hashes, copied_texture_disk_after=after['copy_disks'],
                      current_child_package_sha256=named_hashes[child_package],
                      protected_package_sha256_after={k: after['disk'][k] for k in protected},
                      complete_graph_code_mip_identity_preserved=True, material_recipe_preserved=True,
                      source_and_copy_PBR_properties_preserved=True, scene_grass_and_cvars_preserved=True)
    except Exception as error:
        failure = error
        result['status'] = 'FAILED_NAMED_SAVE_PARTIAL_STATE_PRESERVED'
        result['error'] = repr(error)
        try:
            result['failure_dirty'] = dirty()
            result['failure_named_files'] = {package: h.disk_state(h.package_file(package)) for package in allowed}
            result['failure_protected_files'] = {file: h.disk_state(file) for file in protected}
        except Exception as capture_error:
            result['failure_evidence_error'] = repr(capture_error)
    finally:
        output.write_text(json.dumps(result, indent=2), encoding='utf-8')
        once.write_text(json.dumps({'status': result['status'], 'pid': os.getpid(), 'helper_sha256': script_sha,
                                   'receipt': str(output), 'receipt_sha256': sha(output)}, indent=2), encoding='utf-8')
    if failure:
        raise failure
    return {'receipt': str(output), 'sha256': sha(output), 'status': result['status'], 'pid': os.getpid(),
            'world': named_map, 'area': AREA, 'named_package_sha256': result['named_package_sha256']}


if 'ARGS' in globals():
    RESULT = save(ARGS)
