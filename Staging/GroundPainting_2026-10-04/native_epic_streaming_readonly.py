"""Read-only ground streaming inspection in either fresh original-area process.

ARGS: expected_pid, baseline_receipt + baseline_receipt_sha256,
mode=inspect|investigate, unique ASCII label. Area is derived from the live world.
No editor action is taken by import without ARGS. Root pins and runs this file.
Only the fixed streamer log commands are dispatched; their output is in the
native log, not in the Python dispatch return. No setters or asset operations.
"""
import datetime
import hashlib
import json
import os
import time
import types
from pathlib import Path

FROZEN_SHA = 'e535a74bca2ca6b9ca7856db8152d5b938ef79597b3a17f35c48e14a0dd69f6e'
MANIFEST_SHA = 'f73181be9b8ffc1ee499448dd986266ca5ebe76aab2b1a7e3bea52f06b7d202e'
ASSIGNMENT_SHA = 'c3c49a9baabdfe357a5852d383501d0ac0396bfc7a795b58762ac52b61d3fec7'
PERSISTENT_TEXTURE_FIELDS = (
    'lod_bias', 'lod_group', 'max_texture_size', 'never_stream',
    'global_force_mip_levels_to_be_resident', 'num_cinematic_mip_levels',
    'virtual_texture_streaming',
)
CVAR_NAMES = (
    'r.TextureStreaming', 'r.Streaming.PoolSize', 'r.Streaming.MipBias',
    'r.Streaming.UsePerTextureBias', 'r.Streaming.Boost',
    'r.Streaming.MaxEffectiveScreenSize', 'r.Streaming.HiddenPrimitiveScale',
    'r.Streaming.FullyLoadUsedTextures', 'r.Streaming.UseAllMips',
    'r.ScreenPercentage', 'sg.TextureQuality',
)
READONLY_COMMANDS = ('DumpTextureStreamingStats',) + tuple(
    'InvestigateTexture ' + name for name in (
        'T_Ground_Gravel_D', 'T_Ground_Gravel_N',
        'T_Rock_Sandstone_D', 'T_Rock_Sandstone_N',
    )
)


def load_definitions():
    import unreal
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
    file = (root / 'Staging/GroundPainting_2026-10-04/native_graph_stochastic.py').resolve(strict=True)
    data = file.read_bytes()
    assert hashlib.sha256(data).hexdigest() == FROZEN_SHA
    module = types.ModuleType('ground_streaming_frozen_readonly')
    module.__file__ = str(file)
    exec(compile(data, str(file), 'exec'), module.__dict__)
    assert 'ARGS' not in module.__dict__ and module.SCRIPT.resolve(strict=True) == file
    assert module.sha(file) == FROZEN_SHA
    return module


def inspect(args):
    h = load_definitions()
    script = h.HERE / 'native_epic_streaming_readonly.py'
    script_sha = h.sha(script)
    mode = args.get('mode', 'inspect')
    assert mode in ('inspect', 'investigate')
    assert isinstance(args['expected_pid'], int) and os.getpid() == args['expected_pid']
    label = args['label']
    assert label and all(c.isascii() and (c.isalnum() or c == '_') for c in label)
    out = h.REV / ('GROUND_STREAMING_FRESH_' + label + '_PID' + str(os.getpid()) + '.json')
    assert not out.exists(), 'Preserve the prior streaming receipt'

    assignment_file = h.HERE / 'ASSIGNMENT.json'
    assert h.sha(assignment_file) == ASSIGNMENT_SHA
    assignment = json.loads(assignment_file.read_text(encoding='utf-8-sig'))
    world = h.unreal.get_editor_subsystem(h.unreal.UnrealEditorSubsystem).get_editor_world()
    named_map = world.get_outermost().get_path_name()
    area = h.one((k for k, v in assignment['original_maps'].items() if v == named_map), 'original area')
    assert area in ('GazaShujaiya', 'GazaRimal')
    assert args.get('world', named_map) == named_map
    sources, actors = h.guard(assignment, named_map, require_authoring=False)
    assert len(sources) == 12
    baseline_file, baseline = h.load_document(args['baseline_receipt'])
    baseline_sha = args['baseline_receipt_sha256']
    assert h.sha(baseline_file) == baseline_sha
    assert baseline['pid'] == os.getpid() and baseline['world'] == named_map and baseline['area'] == area
    assert baseline['sources'] == sources and baseline['graph_expression_count'] == 1015
    assert baseline['cooking_paused'] and not baseline['autosave'] and not any(baseline['callbacks'].values())
    assert len(baseline['hdas']) == 1 and all(not x['auto_cook'] and not x['auto_bake'] for x in baseline['hdas'])
    before_scene = h.scene_state(actors)
    assert len(actors) == baseline['actor_count']
    assert before_scene['transforms'] == baseline['actor_transforms']
    assert before_scene['native_mesh_components'] == sorted(baseline['native_mesh_components'], key=lambda x: x['component'])
    expected_landscapes = sorted([{'path': row['path'], 'material': row['material']['path'], 'hidden': row['hidden']}
                                 for row in baseline['landscapes']], key=lambda x: x['path'])
    assert [{k: v for k, v in row.items() if k != 'layers'} for row in before_scene['landscapes']] == expected_landscapes
    landscapes = sorted((a for a in actors if isinstance(a, h.unreal.LandscapeProxy)), key=h.path)
    assert len(landscapes) == len(baseline['landscapes']) > 0

    manifest_file, manifest = h.load_document(h.REV / 'STOCHASTIC_BACKUP_MANIFEST.json')
    assert h.sha(manifest_file) == MANIFEST_SHA
    assert manifest['helper_sha256'] == FROZEN_SHA
    assert len(manifest['file_bindings']) == len(manifest['sealed_files']) == 17
    disk_before = {str(Path(p).resolve(strict=True)): h.sha(p) for p in manifest['file_bindings']}
    sealed_files = {str((h.ROOT / p).resolve(strict=True)): value
                    for p, value in manifest['sealed_files'].items()}
    assert all(h.sha(p) == value for p, value in sealed_files.items())

    master = h.unreal.load_asset(h.MASTER)
    child = h.unreal.load_asset(assignment['material_contract']['area_instances'][area])
    assert isinstance(master, h.unreal.Material) and isinstance(child, h.unreal.MaterialInstanceConstant)
    allowed_dirty = {master.get_outermost().get_path_name(), child.get_outermost().get_path_name()}

    def dirty():
        return {'maps': sorted(h.path(p) for p in h.unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                'content': sorted(h.path(p) for p in h.unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}

    def property_read(obj, name):
        try:
            return {'status': 'READ', 'value': h.plain(obj.get_editor_property(name))}
        except Exception as error:
            return {'status': 'API_FAILURE', 'object': h.path(obj), 'property': name, 'error': str(error)}

    def viewport():
        level = h.unreal.get_editor_subsystem(h.unreal.LevelEditorSubsystem)
        key = level.get_active_viewport_config_key()
        assert str(key) not in ('', 'None')
        eye, rotation = level.get_level_viewport_camera_info(key)
        actual_mode = h.unreal.AutomationLibrary.get_editor_active_viewport_view_mode()
        assert actual_mode == h.unreal.ViewModeIndex.VMI_LIT, 'Read only after the actual active viewport is Lit'
        editor = h.unreal.get_editor_subsystem(h.unreal.UnrealEditorSubsystem)
        primary = {}
        for field, name in (('camera', 'get_level_viewport_camera_info'), ('size', 'get_level_viewport_size')):
            getter = getattr(editor, name, None)
            if not callable(getter):
                primary[field] = {'status': 'API_NOT_EXPOSED', 'method': name}
                continue
            try:
                value = getter()
                if field == 'camera':
                    p, r = value
                    value = {'eye': [float(p.x), float(p.y), float(p.z)],
                             'rotation': [float(r.pitch), float(r.yaw), float(r.roll)]}
                else:
                    value = h.plain(value)
                primary[field] = {'status': 'READ', 'value': value}
            except Exception as error:
                primary[field] = {'status': 'API_FAILURE', 'method': name, 'error': str(error)}
        return {'primary_viewport': primary, 'active_key': str(key), 'camera': {
            'eye': [float(eye.x), float(eye.y), float(eye.z)],
            'rotation': [float(rotation.pitch), float(rotation.yaw), float(rotation.roll)]},
            'viewmode_readback': str(actual_mode), 'actual_lit': True}

    def landscape_streaming():
        result = {}
        for actor in landscapes:
            components = sorted(actor.get_components_by_class(h.unreal.LandscapeComponent), key=h.path)
            result[h.path(actor)] = {
                'streaming_distance_multiplier': property_read(actor, 'streaming_distance_multiplier'),
                'components': {h.path(c): {
                    'is_actor_texture_streaming_built_data': property_read(c, 'is_actor_texture_streaming_built_data'),
                    'is_valid_texture_streaming_built_data': property_read(c, 'is_valid_texture_streaming_built_data'),
                    'cached_texel_factor': {
                        'status': 'API_NOT_REFLECTED_INSTALLED_HEADER',
                        'reason': 'LandscapeComponent has no cached texel-factor UPROPERTY; '
                                  'GetStreamingRenderAssetInfo and GetStreamingScale are C++ methods without UFUNCTION.'},
                } for c in components},
            }
        return result

    def texture_snapshot():
        textures = {}
        for node in h.LIB.get_material_expressions(master):
            try:
                texture = node.get_editor_property('texture')
            except Exception:
                continue
            if texture:
                textures[h.path(texture)] = {
                    'persistent': {name: property_read(texture, name) for name in PERSISTENT_TEXTURE_FIELDS},
                    'transient_residency_deadline': property_read(texture, 'force_mip_levels_to_be_resident_timestamp'),
                }
        assert len(textures) == 70, 'The reviewed master texture inventory must remain exact'
        return textures

    def snapshot():
        return {'dirty': dirty(), 'textures': texture_snapshot(),
                'cvars': {name: h.unreal.SystemLibrary.get_console_variable_string_value(name) for name in CVAR_NAMES},
                'landscapes': landscape_streaming(), 'viewport': viewport()}

    before = snapshot()
    assert before['dirty'] == {'maps': sorted(baseline['dirty_maps']), 'content': sorted(baseline['dirty_content'])}
    assert before['dirty']['maps'] == [] and set(before['dirty']['content']).issubset(allowed_dirty)
    assert len(h.LIB.get_material_expressions(master)) == baseline['graph_expression_count']
    result = {
        'schema': 'environmentpipeline.ground_streaming_fresh_readonly.v1', 'status': 'STARTED',
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': os.getpid(),
        'world': named_map, 'area': area, 'mode': mode, 'helper_sha256': script_sha,
        'frozen_definitions_sha256': FROZEN_SHA, 'backup_manifest_sha256': MANIFEST_SHA,
        'assignment_sha256': ASSIGNMENT_SHA, 'sources': sources,
        'baseline_receipt': str(baseline_file), 'baseline_receipt_sha256': baseline_sha,
        'baseline_scene_verified': True, 'landscape_count': len(landscapes),
        'sealed_files': sealed_files, 'package_sha256_before': disk_before,
        'scene_before': before_scene,
        'allowed_dirty_content': sorted(allowed_dirty), 'before': before,
        'native_mutation': False, 'explicit_compile_called': False, 'explicit_save_called': False,
        'limitations': [
            'InvestigateTexture uses a name query; incidental matches require exact paths in the native log.',
            'Command dispatch is not the streamer log readout; root must collect and inspect the native log.',
            'Python-hidden component data is unknown; no guessed cached texel-factor metric is reported.',
            'The transient residency deadline is recorded when exposed and is excluded from persistent equality.',
            'This inspection does not prove ordinary visual persistence or the viewport-selected GPU branch.',
        ],
    }
    # Reserve the unique receipt before even the fixed read-only log dispatch.
    with out.open('x', encoding='utf-8') as file:
        file.write(json.dumps(result, indent=2))
    started = time.monotonic()
    failure = None
    try:
        if mode == 'investigate':
            result['readonly_commands_requested'] = list(READONLY_COMMANDS)
            result['readonly_commands_dispatched'] = []
            for command in READONLY_COMMANDS:
                h.unreal.SystemLibrary.execute_console_command(world, command)
                result['readonly_commands_dispatched'].append(command)
    except Exception as error:
        failure = error
        result['dispatch_error'] = repr(error)
    finally:
        try:
            after = snapshot()
            sources_after, actors_after = h.guard(assignment, named_map, require_authoring=False)
            result['after'] = after
            result['sources_after'] = sources_after
            result['package_sha256_after'] = {p: h.sha(p) for p in disk_before}
            assert after['dirty'] == before['dirty']
            assert after['cvars'] == before['cvars']
            assert {p: row['persistent'] for p, row in after['textures'].items()} == {
                p: row['persistent'] for p, row in before['textures'].items()}
            assert after['landscapes'] == before['landscapes'] and after['viewport'] == before['viewport']
            assert sources_after == sources and h.scene_state(actors_after) == before_scene
            assert result['package_sha256_after'] == disk_before
            assert all(h.sha(p) == value for p, value in sealed_files.items())
            assert h.sha(script) == script_sha and h.sha(h.SCRIPT) == FROZEN_SHA
            assert h.sha(manifest_file) == MANIFEST_SHA and h.sha(assignment_file) == ASSIGNMENT_SHA
            assert h.sha(baseline_file) == baseline_sha
            assert len(h.LIB.get_material_expressions(master)) == baseline['graph_expression_count']
            result['preservation_checks_passed'] = True
            result['status'] = 'FAILED_DISPATCH_PRESERVATION_PASSED' if failure else 'COMPLETED_READONLY_PRESERVED'
        except Exception as error:
            result['status'] = 'FAILED_PRESERVATION_OR_READBACK'
            result['preservation_checks_passed'] = False
            result['verification_error'] = repr(error)
            if failure is None:
                failure = error
        result['elapsed_seconds'] = time.monotonic() - started
        out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    if failure:
        raise failure
    return {'receipt': str(out), 'sha256': h.sha(out), 'mode': mode,
            'status': result['status'], 'texture_count': len(before['textures']),
            'native_mutation': False, 'preservation_checks_passed': True}


if 'ARGS' in globals():
    RESULT = inspect(ARGS)
