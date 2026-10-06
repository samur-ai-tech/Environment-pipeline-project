"""Bank-executed read-only diagnosis; importing this module has no Unreal effects.

The frozen category_batch adapter remains unchanged. This module never saves,
recompiles, creates material assets, changes parameters, or operates city actors.
Optional material-editor opening and TGA export are explicit collector arguments.
"""
import hashlib
import importlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQUEST = HERE / 'FOLIAGE_MASK_INSPECTION_REQUEST.json'
MANIFEST = HERE / 'FOLIAGE_MASK_INSPECTION_MANIFEST.json'
OUTPUT = HERE / 'NATIVE_FOLIAGE_MASK_DIAGNOSTICS_V1.json'
OVERRIDES = ['override_blend_mode', 'blend_mode', 'override_two_sided',
             'two_sided', 'override_opacity_mask_clip_value',
             'opacity_mask_clip_value', 'override_shading_model', 'shading_model']
ROOT_PROPERTIES = ['blend_mode', 'two_sided', 'opacity_mask_clip_value',
                   'shading_model', 'use_material_attributes',
                   'used_with_instanced_static_meshes', 'used_with_foliage']


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked(path, expected):
    assert Path(path).is_file() and sha(path) == expected, ('identity_mismatch', str(path))


def value(v):
    if v is None or isinstance(v, (str, bool, int, float)):
        return v
    if hasattr(v, 'get_path_name'):
        return v.get_path_name()
    if all(hasattr(v, p) for p in ['r', 'g', 'b', 'a']):
        return [v.r, v.g, v.b, v.a]
    return str(v)


def attempt(call):
    try:
        return {'available': True, 'value': value(call())}
    except Exception as error:
        return {'available': False, 'error': type(error).__name__ + ': ' + str(error)}


def props(obj, names):
    return {name: attempt(lambda name=name: obj.get_editor_property(name)) for name in names}


def collect(open_material_editors=False, export_color_textures=False):
    """Only the active bank operator invokes this after inspecting the sealed request.

    Open roots solely to satisfy graph getter editor-context requirements. Close
    only editors opened by this call; no save prompt or save operation is issued.
    With open_material_editors=False, null graph inputs never prove disconnection.
    """
    manifest = read(MANIFEST)
    for path, expected in manifest['files'].items():
        checked(path, expected)
    request = read(REQUEST)
    spec = importlib.util.spec_from_file_location('vegetation_frozen_category_adapter', HERE / 'category_batch.py')
    B = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(B)
    checked(B.__file__, manifest['files'][str((HERE / 'category_batch.py').resolve())])
    N, U = B.integrator_modules()
    context = N.preflight()
    before = N.dirty()
    original_hashes = {}
    for row in request['rows']:
        for item in row['source_bindings']:
            checked(item['path'], item['sha256'])
            original_hashes[item['path']] = item['sha256']
    M = U.MaterialEditingLibrary
    editor = U.get_editor_subsystem(U.AssetEditorSubsystem)
    initial_editors = {a.get_path_name() for a in editor.get_all_edited_assets()}
    opened = []
    textures = {}
    roots = {}

    def texture_info(path):
        if path in textures:
            return textures[path]
        texture = U.load_asset(path)
        assert texture, ('missing_texture', path)
        info = {'path': path, 'class': texture.get_class().get_name(),
                'sha256': sha(B.package_file(path)) if path.startswith('/Game/') else None,
                'properties': props(texture, ['compression_settings', 'compression_no_alpha',
                                             'srgb', 'virtual_texture_streaming', 'lod_group'])}
        data = None
        try:
            data = texture.get_editor_property('asset_import_data')
        except Exception as error:
            info['import_data_error'] = str(error)
        if data:
            info['source_filenames'] = attempt(lambda: list(data.extract_filenames()))
        if export_color_textures and '/Game/' in path and path.split('.')[-1].endswith('_Color'):
            out = HERE / 'MaskDiagnostics' / (info['sha256'] + '.tga')
            out.parent.mkdir(exist_ok=True)
            if not out.exists():
                task = U.AssetExportTask()
                task.object = texture
                task.exporter = U.TextureExporterTGA()
                task.filename = str(out)
                task.automated = True
                task.prompt = False
                task.replace_identical = False
                task.selected = False
                info['export_succeeded'] = bool(U.Exporter.run_asset_export_task(task))
            if out.exists():
                info['export'] = {'path': str(out), 'sha256': sha(out),
                                  'basis': 'Native TextureExporterTGA source-image export; not rendered leaf visibility.'}
        textures[path] = info
        return info

    def node_info(node, seen, active):
        if not node:
            return None
        key = node.get_path_name()
        if key in seen or len(seen) >= 256:
            return {'path': key, 'reference_only': True}
        seen.add(key)
        record = {'path': key, 'class': node.get_class().get_name(),
                  'properties': props(node, ['parameter_name', 'texture', 'coordinate_index',
                                            'const_coordinate', 'sampler_type', 'material_function',
                                            'default_value']),
                  'input_names': attempt(lambda: list(M.get_material_expression_input_names(node))),
                  'output_names': attempt(lambda: list(M.get_material_expression_output_names(node)))}
        if active:
            try:
                record['inputs'] = [node_info(n, seen, active) for n in M.get_inputs_for_material_expression(active, node)]
            except Exception as error:
                record['inputs_error'] = str(error)
        return record

    def root_info(material):
        path = material.get_path_name()
        if path in roots:
            return roots[path]
        if open_material_editors and path not in initial_editors:
            assert editor.open_editor_for_assets([material]), ('material_editor_open_failed', path)
            opened.append(material)
        active = path in {a.get_path_name() for a in editor.get_all_edited_assets()}
        record = {'path': path, 'sha256': sha(B.package_file(path)),
                  'properties': props(material, ROOT_PROPERTIES),
                  'active_material_editor_context': active,
                  'graph_null_semantics': 'Null is inconclusive unless active material-editor context is verified.',
                  'graph': {}}
        for name in ['MP_BASE_COLOR', 'MP_OPACITY_MASK', 'MP_MATERIAL_ATTRIBUTES', 'MP_WORLD_POSITION_OFFSET']:
            try:
                node = M.get_material_property_input_node(material, getattr(U.MaterialProperty, name))
                record['graph'][name] = {'getter_succeeded': True,
                    'output_name': attempt(lambda name=name: M.get_material_property_input_node_output_name(material, getattr(U.MaterialProperty, name))),
                    'node': node_info(node, set(), material if active else None)}
            except Exception as error:
                record['graph'][name] = {'getter_succeeded': False, 'error': str(error)}
        roots[path] = record
        return record

    def chain_info(path):
        material = U.load_asset(path)
        assert material, ('material_load_failed', path)
        chain = []
        seen = set()
        while isinstance(material, U.MaterialInstanceConstant):
            key = material.get_path_name()
            assert key not in seen, ('material_parent_cycle', key)
            seen.add(key)
            overrides = material.get_editor_property('base_property_overrides')
            parameters = {}
            for kind in ['static_switch', 'scalar', 'texture', 'vector']:
                try:
                    names = getattr(M, 'get_' + kind + '_parameter_names')(material)
                    getter = getattr(M, 'get_material_instance_' + kind + '_parameter_value')
                    parameters[kind] = {str(n): attempt(lambda n=n: getter(material, n)) for n in names}
                except Exception as error:
                    parameters[kind] = {'_unavailable': str(error)}
            for name, item in parameters.get('texture', {}).items():
                if isinstance(item, dict) and item.get('available') and item['value']:
                    texture_info(item['value'])
            chain.append({'path': key, 'sha256': sha(B.package_file(key)),
                          'base_property_overrides': props(overrides, OVERRIDES),
                          'parameters': parameters})
            material = material.get_editor_property('parent')
            assert material
        assert isinstance(material, U.Material)
        root = root_info(material)
        effective = {}
        for name in ['blend_mode', 'two_sided', 'opacity_mask_clip_value', 'shading_model']:
            effective[name] = {'resolved': False}
            for instance in chain:
                overrides = instance['base_property_overrides']
                flag, item = overrides['override_' + name], overrides[name]
                if not flag.get('available'):
                    effective[name]['reason'] = 'An outer override flag is unavailable; inheritance cannot be inferred.'
                    break
                if flag['value']:
                    effective[name] = {'resolved': item['available'], 'value': item.get('value'), 'origin': instance['path']}
                    break
            else:
                item = root['properties'][name]
                effective[name] = {'resolved': item['available'], 'value': item.get('value'), 'origin': root['path']}
        return {'chain': chain, 'root_path': root['path'], 'effective_base_properties': effective}

    rows = {}
    failure = None
    try:
        for row in request['rows']:
            rows[row['asset_id']] = {'mesh_sha256': row['mesh_sha256'], 'slots': [
                {'slot': slot['slot'], 'name': slot['name'],
                 'selected': chain_info(slot['selected_path']),
                 'original': chain_info(slot['original_path'])} for slot in row['slots']],
                 'ready': False, 'lit_visibility_not_measured': True}
        st = {}
        for source in request['speedtree_receipts']:
            checked(source['path'], source['sha256'])
            receipt = read(source['path'])
            checked(B.package_file(receipt['native_path']), receipt['native_sha256'])
            mesh = U.load_asset(receipt['native_path'])
            data = mesh.get_editor_property('asset_import_data')
            st[receipt['asset_id']] = {'native_path': receipt['native_path'],
                'import_data_class': data.get_class().get_name() if data else None,
                'import_properties': props(data, ['tree_scale', 'import_geometry_type', 'lod_type',
                    'make_materials_check', 'include_normal_map_check', 'include_detail_map_check',
                    'include_specular_map_check', 'include_vertex_processing_check', 'include_wind_check',
                    'include_smooth_lod_check']) if data else {},
                'native_slots': [{'slot': i, 'name': str(s.material_slot_name),
                    'material_path': s.material_interface.get_path_name() if s.material_interface else None}
                    for i, s in enumerate(mesh.static_materials)],
                'geometry_not_modified': True, 'held': True}
    except Exception as error:
        failure = error
    finally:
        for material in reversed(opened):
            editor.close_all_editors_for_asset(material)
        assert N.dirty() == before, 'diagnostic_changed_dirty_state_bank_must_preserve_and_review'
        for path, expected in original_hashes.items():
            checked(path, expected)
    if failure:
        raise failure
    assert N.preflight()['world'] == context['world']
    result = {'schema': 'environmentpipeline.native_foliage_mask_diagnosis.v1',
              'pid': os.getpid(), 'world': context['world'], 'dirty_before': before, 'dirty_after': N.dirty(),
              'request_sha256': sha(REQUEST), 'manifest_sha256': sha(MANIFEST),
              'loaded_module': {'path': str(Path(__file__).resolve()), 'sha256': sha(__file__)},
              'rows': rows, 'roots': roots, 'textures': textures, 'speedtree_import_data': st,
              'native_assets_saved_or_changed': False, 'city_cook_or_scene_operations': False,
              'appearance_or_eligibility_approved': False}
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    return {'path': str(OUTPUT), 'sha256': sha(OUTPUT), 'assets': len(rows), 'dirty_unchanged': True}
