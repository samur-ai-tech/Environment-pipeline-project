"""Finalize exact retained H0017 material bindings; no import or geometry edit."""
import collections
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REQUEST = HERE / 'H0017_RECOVERY_REQUEST.json'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def geometry(mesh, U, N):
    measurement = N.measure(mesh)
    measurement.pop('material_slots', None)
    sub = U.get_editor_subsystem(U.StaticMeshEditorSubsystem)
    sections = []
    for lod in range(sub.get_lod_count(mesh)):
        desc = mesh.get_static_mesh_description(lod)
        counts = collections.Counter()
        for i in range(desc.get_triangle_count()):
            tri = U.TriangleID(i)
            assert desc.is_triangle_valid(tri), 'unexpected_sparse_triangle_ids'
            counts[str(desc.get_triangle_polygon_group(tri).get_editor_property('id_value'))] += 1
        sections.append({'lod': lod, 'triangles': desc.get_triangle_count(), 'polygon_group_triangles': dict(counts),
                         'section_material_indices': [sub.get_lod_material_slot(mesh, lod, i) for i in range(mesh.get_num_sections(lod))]})
    return {'measurement_excluding_materials': measurement, 'lod_sections': sections}

def run():
    import unreal as U
    import bank_contracts as C
    import native_bank_ops as N
    import bank_batch_loader as L
    request = read(REQUEST)
    for path, expected in request['file_pins'].items():
        assert sha(path) == expected, ('recovery_input_changed', path)
    for module in (C, N, L):
        path = str(Path(module.__file__).resolve())
        assert path in request['file_pins']
        L.verify_module(module, path)
    assert sha(__file__) == request['script_sha256']
    activation = read(request['activation_path'])
    assert activation['approved'] is True and activation['scope'] == 'FINALIZE_RETAINED_H0017_MATERIALS_ONLY'
    assert activation['request_sha256'] == sha(REQUEST) and activation['script_sha256'] == sha(__file__)
    state = N.preflight()
    assert state['pid'] == request['pid'] == activation['pid'] == os.getpid()
    assert state['world'] == request['world'] == activation['world']
    assert state['dirty']['content'] == sorted(request['named_save_paths']) and not state['dirty']['maps']
    assert activation['manager_thread_id'] == C.read(HERE/'ASSIGNMENT.json')['system_owner']
    assert activation['operator_thread_id'] == C.read(HERE/'ASSIGNMENT.json')['thread']
    receipt_path = HERE / 'H0017_RECOVERY_RESULT.json'
    assert not receipt_path.exists(), 'review_existing_receipt_before_any_retry'
    E = U.EditorAssetLibrary
    mesh = U.find_object(None, request['mesh_object_path'])
    assert isinstance(mesh, U.StaticMesh)
    assert Path(mesh.get_editor_property('asset_import_data').get_first_filename()).resolve() == Path(request['source_fbx']).resolve()
    assert len(mesh.static_materials) == len(request['material_bindings'])
    for package in request['named_save_paths']:
        assert package.startswith('/Game/Project/Shared/ModelBank/Prepared/')
        assert not C.package_file(package).exists(), ('pending_destination_already_saved', package)
        assert U.find_object(None, package + '.' + package.rsplit('/', 1)[1])
    before = geometry(mesh, U, N)
    assert before['measurement_excluding_materials']['triangles'] == request['expected_triangles']
    assert before['lod_sections'][0]['polygon_group_triangles'] == request['expected_polygon_group_triangles']
    assert before['lod_sections'][0]['section_material_indices'] == list(range(len(request['material_bindings'])))
    for binding in request['material_bindings']:
        slot = mesh.static_materials[binding['native_slot']]
        assert str(slot.get_editor_property('imported_material_slot_name')) == binding['native_imported_name']
        material = U.find_object(None, binding['native_material'])
        assert isinstance(material, U.Material)
        assert E.get_metadata_tag(material, 'BankRecipeSHA256') == binding['recipe_sha256']
        assert E.get_metadata_tag(material, 'BankRecipeComplete') == 'true'
        assert U.MaterialEditingLibrary.has_material_usage(material, U.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES)
    result = {'schema': 'environmentpipeline.h0017_retained_material_recovery.v1', 'request_sha256': sha(REQUEST),
              'pid': os.getpid(), 'saved_paths': [], 'geometry_before': before, 'passed': False,
              'geometry_modified': False, 'source_reimported': False, 'map_saved': False, 'holds_released': False}
    try:
        for binding in request['material_bindings']:
            mesh.set_material(binding['native_slot'], U.find_object(None, binding['native_material']))
        for key, value in request['metadata'].items():
            E.set_metadata_tag(mesh, key, value)
        result['geometry_after_binding'] = geometry(mesh, U, N)
        assert result['geometry_after_binding'] == before, 'geometry_or_sections_changed'
        slots = [s.material_interface.get_path_name() for s in mesh.static_materials]
        assert slots == [b['native_material'] for b in request['material_bindings']]
        mesh_package = request['mesh_object_path'].split('.')[0]
        ordered = sorted(p for p in request['named_save_paths'] if p != mesh_package) + [mesh_package]
        for package in ordered:
            assert E.save_asset(package, only_if_is_dirty=True), package
            result['saved_paths'].append({'path': package, 'sha256': C.sha(C.package_file(package))})
            C.write(receipt_path, result)
        result['geometry_after_save'] = geometry(mesh, U, N)
        assert result['geometry_after_save'] == before
        assert N.dirty() == {'content': [], 'maps': []}
        closure = N.dependency_closure(mesh_package)
        assert not closure['missing'], closure
        result.update(passed=True, native_material_slots=slots, dependencies=closure,
                      native_mesh_sha256=C.sha(C.package_file(mesh_package)), native_dirty_after=N.dirty(),
                      geometry_validation_scope='Native vertex bounds/count, triangle counts, all LOD polygon-group triangle counts and section material indices; no UV/normal/appearance acceptance inferred.')
    except Exception as exc:
        result['error'] = repr(exc)
        raise
    finally:
        C.write(receipt_path, result)
    print(json.dumps({'passed': result['passed'], 'saved_packages': len(result['saved_paths']), 'receipt': str(receipt_path)}))

if __name__ == '__main__':
    run()
