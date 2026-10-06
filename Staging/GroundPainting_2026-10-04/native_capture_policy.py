"""Matched actual-Lit policy captures with measured keyed and primary cameras.

New Staging companion; the frozen native_capture.py and camera files stay intact.
Root reviews/pins and executes. ARGS: expected_pid, plan_receipt + sha256,
camera_file_sha256, stage, shot. Only original existing presets are accepted.
The ordinary capture UI setters are followed by actual camera/FOV/Lit getters;
unknown primary FOV is reported explicitly. No Content writes, compile, Cook,
Bake, shader/lighting settings, residency force, camera-file generation or save.
Import without ARGS is idle. PNG completion is checked separately by the writer.
"""
import datetime
import hashlib
import json
import math
import os
import subprocess
import types
from pathlib import Path

FROZEN_SHA = 'e535a74bca2ca6b9ca7856db8152d5b938ef79597b3a17f35c48e14a0dd69f6e'
ORIGINAL_CAPTURE_SHA = '6c3ed43847aed4da0dad36b76efb5935f97eebbf52a6b93a9373e99330e0c7d4'
PLAN_SHA = 'ab8ba794426c390f6b9e7178b0ab6081bb26f0044199b38ae8772de80e56ca5c'
ASSIGNMENT_SHA = 'c3c49a9baabdfe357a5852d383501d0ac0396bfc7a795b58762ac52b61d3fec7'


def sha(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def load_definitions():
    import unreal
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
    file = (root / 'Staging/GroundPainting_2026-10-04/native_graph_stochastic.py').resolve(strict=True)
    data = file.read_bytes()
    check(hashlib.sha256(data).hexdigest() == FROZEN_SHA, 'Frozen definitions changed')
    h = types.ModuleType('ground_policy_capture_frozen_definitions')
    h.__file__ = str(file)
    exec(compile(data, str(file), 'exec'), h.__dict__)
    check('ARGS' not in h.__dict__ and sha(h.SCRIPT) == FROZEN_SHA, 'Authoring entry point must stay idle')
    return h


def sole_editor():
    command = 'ConvertTo-Json -Compress -InputObject @(Get-CimInstance Win32_Process -Filter "Name = \'UnrealEditor.exe\'" | ForEach-Object { [int]$_.ProcessId })'
    run = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
                         check=True, capture_output=True, text=True, timeout=30,
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    check(json.loads(run.stdout) == [os.getpid()], 'Exactly the current editor process is required')


def vector(v):
    return [float(v.x), float(v.y), float(v.z)]


def rotation(r):
    return [float(r.pitch), float(r.yaw), float(r.roll)]


def matches(values, expected, tolerance, angular=False):
    check(len(values) == len(expected), 'Malformed camera values')
    deltas = [((float(a) - float(b) + 180.0) % 360.0 - 180.0)
              if angular else float(a) - float(b) for a, b in zip(values, expected)]
    return all(math.isfinite(v) and abs(v) <= tolerance for v in deltas)


def capture(args):
    h = load_definitions()
    check(os.getpid() == args['expected_pid'], 'Wrong current process')
    sole_editor()
    script = (h.HERE / 'native_capture_policy.py').resolve(strict=True)
    script_sha = sha(script)
    original_capture = (h.HERE / 'native_capture.py').resolve(strict=True)
    check(sha(original_capture) == ORIGINAL_CAPTURE_SHA, 'Frozen original capture helper changed')
    assignment_file = h.HERE / 'ASSIGNMENT.json'
    check(sha(assignment_file) == ASSIGNMENT_SHA, 'Assignment changed')
    assignment = json.loads(assignment_file.read_text(encoding='utf-8-sig'))
    editor = h.unreal.get_editor_subsystem(h.unreal.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    named_map = world.get_outermost().get_path_name()
    area = h.one((key for key, value in assignment['original_maps'].items() if value == named_map), 'original area')
    sources, actors = h.guard(assignment, named_map, require_authoring=True)
    check(len(sources) == 12, 'Exactly twelve sealed runtime modules required')
    plan_file = Path(args['plan_receipt']).resolve(strict=True)
    check(plan_file == (h.REV / 'GROUND_TEXTURE_POLICY_PLAN_R025.json').resolve(strict=True) and
          sha(plan_file) == args['plan_receipt_sha256'] == PLAN_SHA, 'Only the exact retained policy plan is supported')
    plan = json.loads(plan_file.read_text(encoding='utf-8-sig'))
    check(plan['schema'] == 'environmentpipeline.ground_texture_policy_plan.v1' and
          plan['world'] == named_map and plan['area'] == area and len(plan['items']) == 12, 'Plan area/world mismatch')
    child = h.unreal.load_asset(assignment['material_contract']['area_instances'][area])
    master = h.unreal.load_asset(h.MASTER)
    check(isinstance(child, h.unreal.MaterialInstanceConstant) and isinstance(master, h.unreal.Material),
          'Retained material types required')
    allowed_dirty = {row['destination'].split('.')[0] for row in plan['items']} | {child.get_outermost().get_path_name()}
    check(len(allowed_dirty) == 13, 'Exact twelve copies and current child required')
    cameras_file = (h.HERE / ('CAMERAS_' + area + '.json')).resolve(strict=True)
    camera_sha = sha(cameras_file)
    check(camera_sha == args['camera_file_sha256'], 'Approved existing camera file changed')
    cameras = json.loads(cameras_file.read_text(encoding='utf-8-sig'))
    check(set(cameras) == {'close', 'middle', 'wide'}, 'Exact existing camera definitions required')
    shot, stage = args['shot'], args['stage']
    check(shot in cameras and stage and all(c.isascii() and (c.isalnum() or c == '_') for c in stage),
          'Unsafe capture stage/shot')
    camera = cameras[shot]
    check(set(camera) == {'eye', 'target', 'fov'} and len(camera['eye']) == len(camera['target']) == 3,
          'Malformed existing camera')
    image_file = h.HERE / 'Images' / (area + '_' + stage + '_' + shot + '.png')
    receipt_file = h.HERE / ('CAPTURE_' + area + '_' + stage + '_' + shot + '.json')
    check(image_file.parent.is_dir() and not image_file.exists() and not receipt_file.exists(),
          'Preserve existing images and capture receipts')
    instance_paths = [assignment['material_contract']['base_instance'], *assignment['material_contract']['area_instances'].values()]
    files = {h.package_file(h.MASTER), h.package_file(h.BASE), h.package_file(h.GRASS),
             *(h.package_file(value.split('.')[0], '.umap') for value in assignment['original_maps'].values()),
             *(h.package_file(value.split('.')[0]) for value in instance_paths),
             *(h.package_file(row['source']).resolve(strict=True) for row in plan['items']),
             *(h.package_file(row['destination']) for row in plan['items'])}

    def dirty():
        return {'maps': sorted(h.path(v) for v in h.unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                'content': sorted(h.path(v) for v in h.unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}

    def content_state():
        current_sources, current_actors = h.guard(assignment, named_map, require_authoring=True)
        return {'sources': current_sources, 'scene': h.scene_state(current_actors), 'dirty': dirty(),
                'instances': {key: h.material_state(master, h.unreal.load_asset(key)) for key in instance_paths},
                'disk': {str(file.resolve()): h.disk_state(file) for file in sorted(files)}}

    before = content_state()
    check(before['sources'] == sources and before['dirty']['maps'] == [] and
          set(before['dirty']['content']) <= allowed_dirty, 'Map/master/unrelated content is dirty')
    level = h.unreal.get_editor_subsystem(h.unreal.LevelEditorSubsystem)
    key = level.get_active_viewport_config_key()
    check(str(key) not in ('', 'None'), 'An active viewport key is required')
    for obj, name in ((level, 'get_level_viewport_camera_info'), (level, 'get_level_viewport_fov'),
                      (editor, 'get_level_viewport_camera_info'), (h.unreal.AutomationLibrary, 'take_high_res_screenshot'),
                      (h.unreal.AutomationLibrary, 'get_editor_active_viewport_view_mode')):
        check(callable(getattr(obj, name, None)), 'Required camera/capture API absent: ' + name)
    eye, target = h.unreal.Vector(*camera['eye']), h.unreal.Vector(*camera['target'])
    dx, dy, dz = target.x - eye.x, target.y - eye.y, target.z - eye.z
    intended_rotation = [math.degrees(math.atan2(dz, math.hypot(dx, dy))), math.degrees(math.atan2(dy, dx)), 0.0]
    rot = h.unreal.Rotator(pitch=intended_rotation[0], yaw=intended_rotation[1], roll=0)
    level.set_level_viewport_camera_info(eye, rot, key)
    level.set_level_viewport_fov(camera['fov'], key)
    level.editor_invalidate_viewports()
    editor.set_level_viewport_camera_info(eye, rot)
    mode_before = h.unreal.AutomationLibrary.get_editor_active_viewport_view_mode()
    h.unreal.AutomationLibrary.set_editor_active_viewport_view_mode(h.unreal.ViewModeIndex.VMI_LIT)
    mode_after = h.unreal.AutomationLibrary.get_editor_active_viewport_view_mode()
    check(mode_after == h.unreal.ViewModeIndex.VMI_LIT and level.get_active_viewport_config_key() == key,
          'Active viewport must remain exact and measured Lit')
    keyed_eye, keyed_rot = level.get_level_viewport_camera_info(key)
    keyed_fov = float(level.get_level_viewport_fov(key))
    primary_eye, primary_rot = editor.get_level_viewport_camera_info()
    measured = {'keyed': {'eye': vector(keyed_eye), 'rotation': rotation(keyed_rot), 'fov': keyed_fov},
                'primary': {'eye': vector(primary_eye), 'rotation': rotation(primary_rot),
                            'fov_status': 'API_NOT_EXPOSED_USE_KEYED_FOV'},
                'eye_match': matches(vector(keyed_eye), camera['eye'], 0.01),
                'rotation_match': matches(rotation(keyed_rot), intended_rotation, 0.01, angular=True),
                'fov_match': math.isfinite(keyed_fov) and abs(keyed_fov - float(camera['fov'])) <= 0.001,
                'primary_eye_match': matches(vector(primary_eye), camera['eye'], 0.01),
                'primary_rotation_match': matches(rotation(primary_rot), intended_rotation, 0.01, angular=True)}
    measured['all_supported_matches'] = all(measured[name] for name in (
        'eye_match', 'rotation_match', 'fov_match', 'primary_eye_match', 'primary_rotation_match'))
    check(measured['all_supported_matches'], 'Measured keyed or primary camera differs from existing preset')
    check(content_state() == before, 'Capture UI setters changed preserved content')
    level.editor_invalidate_viewports()
    result = {'schema': 'environmentpipeline.ground_policy_capture.v1', 'status': 'CAMERA_VERIFIED_REQUEST_PENDING',
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': os.getpid(),
              'world': named_map, 'area': area, 'stage': stage, 'shot': shot, 'camera': camera,
              'rotation': intended_rotation, 'camera_readback': measured, 'camera_file': str(cameras_file),
              'camera_file_sha256': camera_sha, 'viewmode': 'Lit', 'viewmode_before': str(mode_before),
              'viewmode_readback': str(mode_after), 'active_viewport_key': str(key), 'path': str(image_file),
              'requested_dimensions': [1600, 1000], 'requested': False, 'valid_task': False,
              'helper_sha256': script_sha, 'frozen_helper_sha256': FROZEN_SHA,
              'original_capture_helper_sha256': ORIGINAL_CAPTURE_SHA,
              'plan_receipt': str(plan_file), 'plan_receipt_sha256': PLAN_SHA,
              'dirty_before': before['dirty'], 'allowed_dirty_packages': sorted(allowed_dirty),
              'content_mutation': False, 'ui_camera_and_viewmode_setters_called': True,
              'compile_or_save_called': False, 'force_residency_called': False,
              'limitations': ['Readback is measured immediately before the asynchronous screenshot request.',
                  'Primary FOV has no supported accessor here; measured active keyed FOV is recorded.',
                  'The writer must await the PNG and inspect it; request/task validity is not visual quality.']}
    with receipt_file.open('x', encoding='utf-8') as file:
        file.write(json.dumps(result, indent=2))
    failure = None
    try:
        task = h.unreal.AutomationLibrary.take_high_res_screenshot(1600, 1000, str(image_file),
                                                                 delay=2.0, force_game_view=True)
        result['requested'] = True
        result['valid_task'] = bool(task and task.is_valid_task())
        check(result['valid_task'], 'Native screenshot task is invalid')
        check(content_state() == before, 'Screenshot request changed preserved scene/content state')
        check(level.get_active_viewport_config_key() == key and
              h.unreal.AutomationLibrary.get_editor_active_viewport_view_mode() == h.unreal.ViewModeIndex.VMI_LIT,
              'Capture viewport identity/viewmode changed during request')
        sole_editor()
        check(sha(script) == script_sha and sha(h.SCRIPT) == FROZEN_SHA and
              sha(original_capture) == ORIGINAL_CAPTURE_SHA and sha(cameras_file) == camera_sha and
              sha(plan_file) == PLAN_SHA and sha(assignment_file) == ASSIGNMENT_SHA, 'Capture input/helper identity changed')
        result['status'] = 'MATCHED_ACTUAL_LIT_CAPTURE_REQUESTED'
        result['dirty_after'] = dirty()
        result['scene_content_preservation_passed'] = True
    except Exception as error:
        failure = error
        result['status'] = 'FAILED_CAPTURE_PARTIAL_UI_STATE_PRESERVED'
        result['error'] = repr(error)
        result['failure_dirty'] = dirty()
    finally:
        receipt_file.write_text(json.dumps(result, indent=2), encoding='utf-8')
    if failure:
        raise failure
    return {'receipt': str(receipt_file), 'sha256': sha(receipt_file), 'path': str(image_file),
            'world': named_map, 'area': area, 'pid': os.getpid(), 'stage': stage, 'shot': shot,
            'camera_readback': measured, 'requested': True, 'valid_task': True}


if 'ARGS' in globals():
    RESULT = capture(ARGS)
