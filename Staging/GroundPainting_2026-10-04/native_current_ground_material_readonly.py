"""Read-only actual Landscape/Nanite component material diagnosis.

ARGS: pid (14776), label. Root pins this file before execution. No material
updates, compile/save, actor writes, cook, residency changes or Nanite rebuild.
Unexposed native fields are reported as API_FAILURE, never guessed.
"""
import datetime
import hashlib
import json
import os
import types
from pathlib import Path

FROZEN_SHA = 'e535a74bca2ca6b9ca7856db8152d5b938ef79597b3a17f35c48e14a0dd69f6e'
ROLES_SHA = '83ace2f7670bbe68deb71089505596383d9a3c1cedb5f6a37f188ece261d161c'


def load_helper():
    import unreal
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
    file = (root / 'Staging/GroundPainting_2026-10-04/native_graph_stochastic.py').resolve(strict=True)
    data = file.read_bytes()
    assert hashlib.sha256(data).hexdigest() == FROZEN_SHA
    module = types.ModuleType('ground_material_frozen_readonly')
    module.__file__ = str(file)
    exec(compile(data, str(file), 'exec'), module.__dict__)
    assert 'ARGS' not in module.__dict__ and module.sha(file) == FROZEN_SHA
    return module


def inspect(args):
    h = load_helper()
    script = h.HERE / 'native_current_ground_material_readonly.py'
    assignment = json.loads((h.HERE / 'ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
    world = h.unreal.get_editor_subsystem(h.unreal.UnrealEditorSubsystem).get_editor_world()
    named_map = world.get_outermost().get_path_name()
    assert named_map == assignment['original_maps']['GazaShujaiya'] and os.getpid() == args['pid'] == 14776
    sources, actors = h.guard(assignment, named_map, require_authoring=False)
    roles_file, roles = h.load_document(h.REV / 'CLOSE_GROUND_ROLES_PID14776.json')
    assert h.sha(roles_file) == ROLES_SHA and roles['pid'] == os.getpid() and roles['world'] == named_map
    assert roles['native_mutation'] is False and len(roles['samples']) == 10
    wanted = {row['component'] for row in roles['samples']}
    landscape_paths = {row['landscape'] for row in roles['samples']}
    assert len(wanted) == len(landscape_paths) == 2 and all(p.endswith('.LandscapeComponent_35') for p in wanted)
    landscapes = {h.path(a): a for a in actors if isinstance(a, h.unreal.LandscapeProxy)}
    assert set(landscapes) == landscape_paths
    dirty = lambda: {'maps': [h.path(p) for p in h.unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
                     'content': [h.path(p) for p in h.unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
    intended = h.unreal.load_asset(assignment['material_contract']['area_instances']['GazaShujaiya'])
    allowed_dirty = {h.MASTER, intended.get_outermost().get_path_name()}
    before_dirty, before_scene = dirty(), h.scene_state(actors)
    assert before_dirty['maps'] == [] and set(before_dirty['content']) == allowed_dirty
    assert float(h.LIB.get_material_instance_scalar_parameter_value(intended, 'GeoCity_CellScale')) == 1.0
    manifest_file, manifest = h.load_document(h.REV / 'STOCHASTIC_BACKUP_MANIFEST.json')
    assert manifest['helper_sha256'] == FROZEN_SHA and len(manifest['file_bindings']) == 17
    disk_before = {p: h.sha(p) for p in manifest['file_bindings']}

    def raw_property(obj, name, convert):
        try:
            return {'status': 'READ', 'value': convert(obj.get_editor_property(name))}
        except Exception as error:
            return {'status': 'API_FAILURE', 'object': h.path(obj), 'property': name, 'error': str(error)}

    def scalar_overrides(instance):
        def convert(values):
            rows = []
            for value in values:
                info = value.get_editor_property('parameter_info')
                rows.append({'name': str(info.get_editor_property('name')),
                    'association': h.plain(info.get_editor_property('association')),
                    'index': int(info.get_editor_property('index')),
                    'value': float(value.get_editor_property('parameter_value'))})
            return rows
        return raw_property(instance, 'scalar_parameter_values', convert)

    masters = {}

    def material_chain(material):
        rows, seen = [], set()
        current, status, terminal = material, 'NULL_MATERIAL', None
        while current:
            p = h.path(current)
            if p in seen or len(rows) >= 16:
                status = 'PARENT_CYCLE_OR_LIMIT'
                break
            seen.add(p)
            row = {'path': p, 'class': current.get_class().get_name()}
            try:
                if isinstance(current, h.unreal.MaterialInstanceConstant):
                    cell = h.LIB.get_material_instance_scalar_parameter_value(current, 'GeoCity_CellScale')
                elif isinstance(current, h.unreal.MaterialInstanceDynamic):
                    cell = current.get_scalar_parameter_value('GeoCity_CellScale')
                elif isinstance(current, h.unreal.Material):
                    cell = h.LIB.get_material_default_scalar_parameter_value(current, 'GeoCity_CellScale')
                else:
                    raise TypeError('Unsupported MaterialInterface class for scalar accessor')
                row['effective_cell_scale'] = {'status': 'READ', 'value': float(cell), 'equals_intended_1': float(cell) == 1.0}
            except Exception as error:
                row['effective_cell_scale'] = {'status': 'API_FAILURE', 'error': str(error)}
            if isinstance(current, h.unreal.Material):
                terminal, status = p, 'MASTER_REACHED'
                if p not in masters:
                    expressions = list(h.LIB.get_material_expressions(current))
                    layer_roots = {}
                    for key in ('color', 'normal', 'roughness', 'ao'):
                        try:
                            root = h.LIB.get_material_property_input_node(current, h.PROPERTIES[key])
                            if isinstance(root, h.unreal.MaterialExpressionLandscapeLayerBlend):
                                names = [str(v.get_editor_property('layer_name')) for v in root.get_editor_property('layers')]
                                layer_roots[key] = {'path': h.path(root), 'layer_count': len(names), 'layer_names': names}
                            else:
                                layer_roots[key] = {'path': h.path(root), 'status': 'ROOT_NOT_LANDSCAPE_LAYER_BLEND'}
                        except Exception as error:
                            layer_roots[key] = {'status': 'API_FAILURE', 'error': str(error)}
                    masters[p] = {'expression_count': len(expressions), 'layer_roots': layer_roots}
                rows.append(row)
                break
            row['scalar_parameter_values'] = scalar_overrides(current)
            row['override_guid_capture'] = 'GUID_NOT_CAPTURED_PYTHON_UNEXPOSED'
            parent = raw_property(current, 'parent', lambda v: v)
            if parent['status'] != 'READ':
                row['parent'] = parent
                rows.append(row)
                status = 'PARENT_API_FAILURE'
                break
            current = parent['value']
            row['parent'] = {'status': 'READ', 'path': h.path(current)}
            rows.append(row)
            status = 'NULL_PARENT' if current is None else status
        return {'leaf': h.path(material), 'status': status, 'chain': rows, 'resolved_master': terminal,
                'resolved_expected_natural_master': terminal == h.path(h.unreal.load_asset(h.MASTER))}

    def component_materials(component):
        try:
            count = component.get_num_materials()
            return {'status': 'READ', 'num_materials': count,
                    'materials': [{'index': i, 'material': material_chain(component.get_material(i))} for i in range(count)]}
        except Exception as error:
            return {'status': 'API_FAILURE', 'error': str(error)}

    def capture():
        components, proxies = {}, {}
        for p, actor in landscapes.items():
            found = {h.path(c): c for c in actor.get_components_by_class(h.unreal.LandscapeComponent) if h.path(c) in wanted}
            assert len(found) == 1
            for cp, component in found.items():
                components[cp] = {'landscape': p, 'class': component.get_class().get_name(),
                    'material_instances': raw_property(component, 'material_instances', lambda v: [material_chain(m) for m in v]),
                    'material_instances_dynamic': raw_property(component, 'material_instances_dynamic', lambda v: [material_chain(m) for m in v]),
                    'lod_index_to_material_index': raw_property(component, 'lod_index_to_material_index', lambda v: [int(i) for i in v]),
                    'get_material_slots': component_materials(component)}
            proxies[p] = {'enable_nanite': raw_property(actor, 'enable_nanite', bool),
                'nanite_components': raw_property(actor, 'nanite_components', lambda v: [
                    {'path': h.path(c), 'class': c.get_class().get_name(), 'materials': component_materials(c)} for c in v]),
                'enumerated_static_mesh_components': [{'path': h.path(c), 'class': c.get_class().get_name(),
                    'static_mesh': raw_property(c, 'static_mesh', h.path), 'materials': component_materials(c)}
                    for c in actor.get_components_by_class(h.unreal.StaticMeshComponent)]}
        assert set(components) == wanted
        return {'landscape_components': components, 'landscape_render_components': proxies}

    intended_chain = material_chain(intended)
    captured = capture()
    assert capture() == captured, 'Read-only material state changed during inspection'
    sources_after, actors_after = h.guard(assignment, named_map, require_authoring=False)
    assert sources_after == sources and h.scene_state(actors_after) == before_scene and dirty() == before_dirty
    assert all(h.sha(p) == expected for p, expected in disk_before.items())
    assert h.sha(h.SCRIPT) == FROZEN_SHA and h.sha(roles_file) == ROLES_SHA
    label = args.get('label', 'r016')
    assert label and all(c.isascii() and (c.isalnum() or c == '_') for c in label)
    out = h.REV / ('CURRENT_GROUND_RENDER_MATERIAL_' + label + '_PID' + str(os.getpid()) + '.json')
    assert not out.exists()
    result = {'pid': os.getpid(), 'world': named_map, 'area': 'GazaShujaiya',
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'helper_sha256': h.sha(script),
        'frozen_definitions_sha256': FROZEN_SHA, 'roles_receipt_sha256': ROLES_SHA,
        'intended_area_material': intended_chain, 'resolved_masters': masters, **captured,
        'dirty_before': before_dirty, 'dirty_after': dirty(), 'package_sha256': disk_before,
        'native_mutation': False, 'explicit_compile_called': False, 'explicit_save_called': False,
        'limitations': ['Reflected internal arrays may be unexposed to Python; API_FAILURE remains unknown.',
            'Assigned/generated material identities do not independently prove which render branch the viewport selected.',
            'ExpressionGUID is not captured; serialized package hashes are checked unchanged during this read.']}
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    return {'receipt': str(out), 'sha256': h.sha(out), 'native_mutation': False,
            'intended_area_material': intended_chain, **captured}


if 'ARGS' in globals():
    RESULT = inspect(ARGS)
