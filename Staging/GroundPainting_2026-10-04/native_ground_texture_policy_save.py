"""Named save of reviewed twelve owned texture copies and current-area MI only.

Preparation only until root independently reviews/pins and executes this file.
ARGS: expected_pid, label, plan_receipt + sha256, policy_verify_receipt + sha256,
visual_review_receipt + sha256, reviewed_visual_stage. Exactly current authoring
lease/sole PID, frozen definitions/policy helper and successful complete policy
identity plus actual matched Lit visual evidence are mandatory. No map/master
save, compile, setters, Cook/Bake, residency force, rollback or Save All.
Import without ARGS is idle. A failed native save retains partial-state evidence.
"""
import datetime
import hashlib
import json
import math
import os
import struct
import types
from pathlib import Path

FROZEN_SHA = 'e535a74bca2ca6b9ca7856db8152d5b938ef79597b3a17f35c48e14a0dd69f6e'
POLICY_HELPER_SHA = 'bdba22a3bcf801663788166649e3fd593704507f133995a1085ed0b37c2404b4'
PLAN_SHA = 'ab8ba794426c390f6b9e7178b0ab6081bb26f0044199b38ae8772de80e56ca5c'
ASSIGNMENT_SHA = 'c3c49a9baabdfe357a5852d383501d0ac0396bfc7a795b58762ac52b61d3fec7'
REQUIRED_POLICY_CHECKS = (
    'complete_code_input_output_mip_identity_equal', 'preserved_grass',
    'preserved_scene', 'preserved_cvars', 'preserved_original_package_files',
    'preserved_source_texture_properties',
    'exact_twelve_copy_properties_and_mapping_verified',
)


def sha(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def load_policy_definitions():
    import unreal
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
    file = (root / 'Staging/GroundPainting_2026-10-04/native_ground_texture_policy.py').resolve(strict=True)
    data = file.read_bytes()
    check(hashlib.sha256(data).hexdigest() == POLICY_HELPER_SHA, 'Policy helper identity changed')
    module = types.ModuleType('ground_texture_policy_save_readonly_definitions')
    module.__file__ = str(file)
    exec(compile(data, str(file), 'exec'), module.__dict__)
    check('ARGS' not in module.__dict__, 'Policy authoring entry point must remain idle')
    check(sha(file) == POLICY_HELPER_SHA, 'Policy definitions changed during load')
    return module, file


def read_bound(h, args, key):
    file = Path(args[key]).resolve(strict=True)
    check(file.is_relative_to(h.REV) and file.suffix == '.json', 'Receipt must be under Revision: ' + key)
    check(sha(file) == args[key + '_sha256'], 'Bound receipt SHA mismatch: ' + key)
    return file, json.loads(file.read_text(encoding='utf-8-sig'))


def near(values, expected, tolerance, angular=False):
    check(isinstance(values, list) and len(values) == len(expected), 'Malformed measured camera vector')
    deltas = [((float(a) - float(b) + 180.0) % 360.0 - 180.0)
              if angular else float(a) - float(b) for a, b in zip(values, expected)]
    return all(math.isfinite(v) and abs(v) <= tolerance for v in deltas)


def rotation_for(camera):
    dx, dy, dz = [float(b) - float(a) for a, b in zip(camera['eye'], camera['target'])]
    return [math.degrees(math.atan2(dz, math.hypot(dx, dy))), math.degrees(math.atan2(dy, dx)), 0.0]


def visual_evidence(h, visual_file, visual, args, area, named_map):
    stage = args['reviewed_visual_stage']
    check(stage and all(c.isascii() and (c.isalnum() or c == '_') for c in stage), 'Unsafe visual stage')
    check(visual['pid'] == os.getpid() and visual['area'] == area and visual['world'] == named_map,
          'Visual approval identity mismatch')
    check(visual['stage'] == stage and visual['save_approved_within_scope'] is True,
          'Exact visual stage is not approved for this named save')
    check(visual['measured_viewmode'] == 3 and visual['images_opened_and_visually_inspected'] is True,
          'Visual approval requires inspected actual-Lit images')
    check(len(visual['images']) == 3 and len(set(visual['images'])) == 3, 'Exactly three approved PNGs required')
    cameras_file = (h.HERE / ('CAMERAS_' + area + '.json')).resolve(strict=True)
    cameras = json.loads(cameras_file.read_text(encoding='utf-8-sig'))
    cameras_sha = sha(cameras_file)
    check(set(cameras) == {'close', 'middle', 'wide'}, 'Exact existing camera set required')
    approved_captures = {Path(row['path']).resolve(strict=True): row['sha256']
                         for row in visual['capture_evidence']}
    check(len(approved_captures) == 3, 'Visual review must bind all three capture receipts')
    hashes = visual['image_sha256']
    check(set(hashes) == set(visual['images']), 'Visual approval must bind all three image hashes')
    records = []
    for shot in ('close', 'middle', 'wide'):
        image_file = (h.HERE / 'Images' / (area + '_' + stage + '_' + shot + '.png')).resolve(strict=True)
        check(str(image_file) in visual['images'] and image_file.is_relative_to(h.HERE / 'Images'),
              'Unexpected approved image path')
        check(sha(image_file) == hashes[str(image_file)], 'Approved image changed: ' + shot)
        header = image_file.read_bytes()[:24]
        check(header[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', header[16:24]) == (1600, 1000),
              'Expected actual 1600x1000 PNG: ' + shot)
        capture_file = (h.HERE / ('CAPTURE_' + area + '_' + stage + '_' + shot + '.json')).resolve(strict=True)
        check(capture_file in approved_captures and sha(capture_file) == approved_captures[capture_file],
              'Approved capture receipt changed: ' + shot)
        capture = json.loads(capture_file.read_text(encoding='utf-8-sig'))
        check(capture['schema'] == 'environmentpipeline.ground_policy_capture.v1' and
              capture['status'] == 'MATCHED_ACTUAL_LIT_CAPTURE_REQUESTED' and
              capture['helper_sha256'] == sha(h.HERE / 'native_capture_policy.py'),
              'Unsupported or changed capture helper/schema: ' + shot)
        check(capture['scene_content_preservation_passed'] is True and
              capture['content_mutation'] is False and capture['compile_or_save_called'] is False and
              capture['force_residency_called'] is False, 'Capture preservation did not pass: ' + shot)
        check(capture['pid'] == os.getpid() and capture['world'] == named_map and capture['area'] == area,
              'Capture process/world/area mismatch: ' + shot)
        check(capture['stage'] == stage and capture['shot'] == shot and
              Path(capture['path']).resolve(strict=True) == image_file, 'Capture stage/path mismatch: ' + shot)
        check(capture['requested_dimensions'] == [1600, 1000] and capture['requested'] is True and
              capture['valid_task'] is True, 'Invalid capture request: ' + shot)
        check(capture['viewmode_readback'] == '<ViewModeIndex.VMI_LIT: 3>' and
              capture['active_viewport_key'], 'Measured actual Lit evidence required: ' + shot)
        check(capture['camera_file_sha256'] == cameras_sha and capture['camera'] == cameras[shot],
              'Existing camera definition changed: ' + shot)
        readback = capture['camera_readback']
        check(all(readback[k] is True for k in ('eye_match', 'rotation_match', 'fov_match',
              'primary_eye_match', 'primary_rotation_match', 'all_supported_matches')),
              'Camera readback did not match: ' + shot)
        expected_rotation = rotation_for(cameras[shot])
        for key in ('keyed', 'primary'):
            check(near(readback[key]['eye'], cameras[shot]['eye'], 0.01) and
                  near(readback[key]['rotation'], expected_rotation, 0.01, angular=True),
                  'Measured camera values differ: ' + shot + ' ' + key)
        check(abs(float(readback['keyed']['fov']) - float(cameras[shot]['fov'])) <= 0.001,
              'Measured keyed FOV differs: ' + shot)
        records.append({'shot': shot, 'image': str(image_file), 'image_sha256': sha(image_file),
                        'capture': str(capture_file), 'capture_sha256': sha(capture_file)})
    return {'visual_review': str(visual_file), 'visual_review_sha256': sha(visual_file),
            'camera_file': str(cameras_file), 'camera_file_sha256': cameras_sha, 'captures': records}


def save(args):
    p, policy_script = load_policy_definitions()
    h = p.load_helper()
    check(h.sha(h.SCRIPT) == FROZEN_SHA, 'Frozen graph definitions changed')
    check(os.getpid() == args['expected_pid'], 'Wrong current process')
    p.sole_editor()
    assignment_file = h.HERE / 'ASSIGNMENT.json'
    check(sha(assignment_file) == ASSIGNMENT_SHA, 'Assignment changed')
    assignment = json.loads(assignment_file.read_text(encoding='utf-8-sig'))
    world = h.unreal.get_editor_subsystem(h.unreal.UnrealEditorSubsystem).get_editor_world()
    named_map = world.get_outermost().get_path_name()
    area = h.one((k for k, v in assignment['original_maps'].items() if v == named_map), 'original area')
    sources, actors = h.guard(assignment, named_map, require_authoring=True)
    check(len(sources) == 12, 'Exactly twelve sealed runtime modules required')
    files, docs = {}, {}
    for key in ('plan_receipt', 'policy_verify_receipt', 'visual_review_receipt'):
        files[key], docs[key] = read_bound(h, args, key)
    plan, verified, visual = (docs[k] for k in ('plan_receipt', 'policy_verify_receipt', 'visual_review_receipt'))
    check(files['plan_receipt'] == (h.REV / 'GROUND_TEXTURE_POLICY_PLAN_R025.json').resolve(strict=True)
          and sha(files['plan_receipt']) == PLAN_SHA, 'Only the exact retained twelve-copy plan is supported')
    check(plan['schema'] == 'environmentpipeline.ground_texture_policy_plan.v1' and
          plan['world'] == named_map and plan['area'] == area, 'Plan world/area/schema mismatch')
    check(plan['policy'] == {'never_stream': True, 'max_texture_size': 4096,
          'global_force_mip_levels_to_be_resident': False}, 'Unreviewed texture policy')
    items = plan['items']
    check(len(items) == 12 and {r['parameter'] for r in items} == set(p.PARAMETERS), 'Exact twelve roles required')
    check(len({r['source'] for r in items}) == len({r['destination'] for r in items}) == 12,
          'Texture source/destination identities must be unique')
    for row in items:
        name = 'T_' + row['parameter'] + '_GeoCityResident4K'
        check(set(row) == {'parameter', 'source', 'destination'} and
              row['destination'] == h.SURFACE + '/Textures/Resident4K/' + name + '.' + name,
              'Unexpected owned destination')
    check(verified['schema'] == 'environmentpipeline.ground_texture_policy.v1' and
          verified['status'] == 'IDENTITY_VERIFIED_READ_ONLY_TEXTURE_POLICY' and verified['mode'] == 'verify',
          'Successful read-only policy verification required')
    check(verified['pid'] == os.getpid() and verified['world'] == named_map and verified['area'] == area,
          'Policy verification identity mismatch')
    check(verified['helper_sha256'] == POLICY_HELPER_SHA and verified['frozen_helper_sha256'] == FROZEN_SHA and
          verified['plan_sha256'] == PLAN_SHA and verified['plan'] == plan, 'Policy verification binding mismatch')
    check(verified['graph_count'] == 1015 and all(verified[k] is True for k in REQUIRED_POLICY_CHECKS),
          'Complete graph/source/scene/policy verification did not pass')
    check(verified['native_mutation'] is False and verified['explicit_save_called'] is False and
          verified['explicit_master_compile_called'] is False, 'Policy verify must be read-only')
    check(verified['before'] == verified['after'], 'Policy verification observed changing state')
    for key in ('nodes', 'roots', 'material_settings', 'instances', 'grass', 'scene', 'cvars'):
        check(verified[key] == verified['after'][key], 'Policy alias differs from complete observed state: ' + key)
    check(verified['package_sha256'] == verified['after']['disk'], 'Policy package hash alias mismatch')
    for key, row in verified['input_files'].items():
        file = Path(row['file']).resolve(strict=True)
        check(file.is_relative_to(h.HERE) and sha(file) == row['sha256'], 'Policy input changed: ' + key)
    check(Path(verified['input_files']['plan_receipt']['file']).resolve(strict=True) == files['plan_receipt'],
          'Policy verification used another plan')
    master = h.unreal.load_asset(h.MASTER)
    child = h.unreal.load_asset(assignment['material_contract']['area_instances'][area])
    check(isinstance(master, h.unreal.Material) and isinstance(child, h.unreal.MaterialInstanceConstant),
          'Expected retained material types')
    child_path, child_package = h.path(child), child.get_outermost().get_path_name()
    check(child_path in verified['instances'], 'Current child absent from verified instance state')
    allowed = {r['destination'].split('.')[0] for r in items} | {child_package}
    check(len(allowed) == 13 and set(verified['allowed_dirty_packages']) == allowed,
          'Only twelve owned copies and current child may be saved')

    def dirty():
        return {'maps': sorted(h.path(v) for v in h.unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                'content': sorted(h.path(v) for v in h.unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}

    def snapshot():
        current_sources, current_actors = h.guard(assignment, named_map, require_authoring=True)
        check(current_sources == verified['after']['sources'] and len(current_sources) == 12,
              'Loaded sealed source identity changed')
        nodes = {h.path(e): h.describe(master, e) for e in h.LIB.get_material_expressions(master)}
        roots = {k: h.path(h.LIB.get_material_property_input_node(master, prop)) for k, prop in h.PROPERTIES.items()}
        settings = {k: h.plain(master.get_editor_property(k)) for k in verified['material_settings']}
        check(len(nodes) == 1015 and nodes == verified['nodes'], 'Complete 1015-node graph/code/mip identity changed')
        check(roots == verified['roots'] and settings == verified['material_settings'], 'Roots/material settings changed')
        instances = {key: h.material_state(master, h.unreal.load_asset(key)) for key in verified['instances']}
        check(instances == verified['instances'], 'Verified material instance state changed')
        grass_nodes = [e for e in h.LIB.get_material_expressions(master)
                       if isinstance(e, h.unreal.MaterialExpressionLandscapeGrassOutput)]
        check(len(grass_nodes) == 1, 'Expected one preserved Grass output')
        grass = {'graph': {key: h.describe(master, e) for key, e in h.reachable(master, grass_nodes).items()},
                 'settings': h.grass_settings(h.unreal.load_asset(h.GRASS)),
                 'effective_coverage': {h.path(a): float(h.LIB.get_material_instance_scalar_parameter_value(
                     child, 'GeoCity_GrassCoverage')) for a in current_actors if isinstance(a, h.unreal.LandscapeProxy)}}
        check(grass == verified['grass'] and set(grass['effective_coverage'].values()) == {0.0}, 'Preserved Grass state changed')
        scene = h.scene_state(current_actors)
        check(scene == verified['scene'], 'Preserved scene identity changed')
        cvars = {name: h.unreal.SystemLibrary.get_console_variable_string_value(name) for name in p.CVARS}
        check(cvars == verified['cvars'], 'Global quality/streaming CVar state changed')
        source_details, copy_details, copy_disks = {}, {}, {}
        for row in items:
            parameter = row['parameter']
            original = h.unreal.load_asset(row['source'])
            copied = h.unreal.load_asset(row['destination'])
            source_details[parameter] = p.texture_details(h, original)
            copy_details[parameter] = p.texture_details(h, copied)
            p.assert_source(h, parameter, source_details[parameter])
            p.compare_copy(source_details[parameter], copy_details[parameter])
            check(source_details[parameter] == verified['after']['source_textures'][parameter], 'Original texture metadata changed')
            check(copy_details[parameter] == verified['copy_textures'][parameter] and
                  h.path(h.LIB.get_material_instance_texture_parameter_value(child, parameter)) == row['destination'],
                  'Copied metadata or exact current-child binding changed')
            copy_disks[parameter] = {'asset_exists': h.unreal.EditorAssetLibrary.does_asset_exist(row['destination']),
                                     'disk': h.disk_state(h.package_file(row['destination']))}
        disk = {key: sha(Path(key).resolve(strict=True)) for key in verified['package_sha256']}
        return {'sources': current_sources, 'nodes': nodes, 'roots': roots, 'material_settings': settings,
                'instances': instances, 'grass': grass, 'scene': scene, 'cvars': cvars,
                'source_textures': source_details, 'copy_textures': copy_details, 'copies': copy_disks,
                'disk': disk, 'dirty': dirty()}

    before = snapshot()
    check(before['disk'] == verified['package_sha256'], 'Verified source/original file hashes changed')
    check(before['copies'] == verified['after']['copies'], 'Owned copy disk state changed after policy verification')
    check(before['dirty'] == verified['after']['dirty'], 'Dirty state changed after policy verification')
    check(before['dirty']['maps'] == [] and set(before['dirty']['content']) <= allowed,
          'Master, maps or unrelated packages are dirty; stop without save')
    check(before['dirty']['content'], 'No dirty reviewed policy packages')
    visual_binding = visual_evidence(h, files['visual_review_receipt'], visual, args, area, named_map)
    # Fail before native save if the supported save API or package identity is absent.
    save_packages = getattr(h.unreal.EditorLoadingAndSavingUtils, 'save_packages', None)
    check(callable(save_packages), 'Supported named package save API is absent')
    objects = {r['destination'].split('.')[0]: h.unreal.load_asset(r['destination']) for r in items}
    objects[child_package] = child
    packages = [objects[key].get_outermost() for key in sorted(before['dirty']['content'])]
    check({h.path(v) for v in packages} == set(before['dirty']['content']), 'Named package identity mismatch')
    label = args['label']
    check(label and all(c.isascii() and (c.isalnum() or c == '_') for c in label), 'Unsafe save label')
    output = h.REV / ('GROUND_TEXTURE_POLICY_NAMED_SAVE_' + area + '_' + label + '_PID' + str(os.getpid()) + '.json')
    check(not output.exists(), 'Never overwrite prior save evidence')
    script = (h.HERE / 'native_ground_texture_policy_save.py').resolve(strict=True)
    script_sha = sha(script)
    package_files = {key: h.package_file(key).resolve() for key in sorted(allowed)}
    named_before = {key: h.disk_state(file) for key, file in package_files.items()}
    protected = {key: value for key, value in before['disk'].items()
                 if Path(key).resolve() != h.package_file(child_package).resolve()}
    # All original source texture packages must remain in the protected table.
    check({str(h.package_file(row['source']).resolve(strict=True)) for row in items} <= set(protected),
          'Original texture source file guard is incomplete')
    result = {'schema': 'environmentpipeline.ground_texture_policy_named_save.v1', 'status': 'PRE_SAVE_CHECKS_PASSED',
              'pid': os.getpid(), 'world': named_map, 'area': area,
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'helper_sha256': script_sha,
              'frozen_helper_sha256': FROZEN_SHA, 'policy_helper_sha256': POLICY_HELPER_SHA,
              'input_files': {key: {'file': str(file), 'sha256': sha(file)} for key, file in files.items()},
              'visual_evidence': visual_binding, 'reviewed_visual_stage': visual['stage'],
              'allowed_named_packages': sorted(allowed), 'named_packages': sorted(before['dirty']['content']),
              'named_package_files_before': named_before, 'protected_package_sha256_before': protected,
              'dirty_before': before['dirty'], 'graph_count': 1015, 'graph_sha256': h.digest(before['nodes']),
              'explicit_save_called': False, 'save_all_called': False, 'map_save_called': False,
              'master_save_called': False, 'explicit_compile_called': False,
              'cook_or_bake_called': False, 'force_residency_called': False, 'rollback_executed': False,
              'user_acceptance': 'PENDING', 'reference_quality': 'NOT_ESTABLISHED'}
    p.sole_editor()
    check(snapshot() == before, 'State changed during final pre-save checks')
    check(all(sha(file) == args[key + '_sha256'] for key, file in files.items()), 'Bound approvals changed')
    with output.open('x', encoding='utf-8') as file:
        file.write(json.dumps(result, indent=2))
    failure = None
    try:
        result['explicit_save_called'] = True
        check(save_packages(packages, False) is True, 'Named package save reported failure')
        after = snapshot()
        check(after['dirty'] == {'maps': [], 'content': []}, 'Named save did not leave an entirely clean editor')
        for key in ('sources', 'nodes', 'roots', 'material_settings', 'instances', 'grass', 'scene',
                    'cvars', 'source_textures', 'copy_textures'):
            check(after[key] == before[key], 'State changed during named save: ' + key)
        check({key: after['disk'][key] for key in protected} == protected, 'Original/source file changed during save')
        named_after = {key: h.disk_state(file) for key, file in package_files.items()}
        check(all(row['exists'] and 'sha256' in row for row in named_after.values()), 'Saved owned package file missing')
        for key in allowed - set(before['dirty']['content']):
            check(named_after[key] == named_before[key], 'A non-dirty reviewed package changed on disk')
        p.sole_editor()
        check(sha(script) == script_sha and sha(policy_script) == POLICY_HELPER_SHA and sha(h.SCRIPT) == FROZEN_SHA,
              'Reviewed helper identity changed during save')
        check(sha(assignment_file) == ASSIGNMENT_SHA and
              all(sha(file) == args[key + '_sha256'] for key, file in files.items()), 'Input identity changed during save')
        check(visual_evidence(h, files['visual_review_receipt'], visual, args, area, named_map) == visual_binding,
              'Approved visual evidence changed during save')
        result.update(status='NAMED_TEXTURE_POLICY_SAVE_VERIFIED_CLEAN', dirty_after=after['dirty'],
                      named_package_files_after=named_after,
                      protected_package_sha256_after={key: after['disk'][key] for key in protected},
                      complete_graph_code_mip_identity_preserved=True, material_instances_preserved=True,
                      texture_properties_preserved=True, scene_and_grass_preserved=True, cvars_preserved=True,
                      ordinary_visual_persistence='PENDING_FRESH_PROCESS_REOPEN')
    except Exception as error:
        failure = error
        result['status'] = 'FAILED_NAMED_SAVE_PARTIAL_STATE_PRESERVED'
        result['error'] = repr(error)
        try:
            result['failure_dirty'] = dirty()
            result['failure_named_package_files'] = {key: h.disk_state(file) for key, file in package_files.items()}
            result['failure_protected_package_sha256'] = {key: sha(key) for key in protected}
        except Exception as capture_error:
            result['failure_evidence_error'] = repr(capture_error)
    finally:
        output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    if failure:
        raise failure
    return {'receipt': str(output), 'sha256': sha(output), 'status': result['status'],
            'pid': os.getpid(), 'world': named_map, 'area': area, 'named_packages': result['named_packages']}


if 'ARGS' in globals():
    RESULT = save(ARGS)
