"""Retained vegetation derivatives; run with Blender --background --disable-autoexec.

Only this category directory is written. Original and prepared sources are hashed
before/after. No new render, scene placement, original save, or Unreal operation.
"""
import collections
import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Matrix

HERE = Path(__file__).resolve().parent
OUT = HERE / 'Derivatives'
OUT.mkdir(exist_ok=True)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def socket_value(socket):
    try:
        return list(socket.default_value)
    except TypeError:
        return socket.default_value


def recipe(material, slot, source_name):
    nodes = list(material.node_tree.nodes)
    bsdfs = [n for n in nodes if n.type == 'BSDF_PRINCIPLED']
    assert len(bsdfs) == 1, material.name
    bsdf = bsdfs[0]
    inputs = {n: {'default': socket_value(bsdf.inputs[n]), 'links': [
        {'node': l.from_node.name, 'type': l.from_node.type, 'output': l.from_socket.name}
        for l in bsdf.inputs[n].links]} for n in
        ['Base Color', 'Metallic', 'Roughness', 'Alpha', 'Normal', 'Emission Color', 'Emission Strength']}
    images = []
    for node in nodes:
        if node.type != 'TEX_IMAGE' or not node.image or not any(s.is_linked for s in node.outputs):
            continue
        image = Path(bpy.path.abspath(node.image.filepath)).resolve()
        assert image.is_file(), image
        images.append({'node': node.name, 'path': str(image), 'sha256': sha(image),
                       'colorspace': node.image.colorspace_settings.name,
                       'outputs': [{'socket': s.name, 'destinations': [
                           l.to_node.name + '.' + l.to_socket.name for l in s.links]}
                           for s in node.outputs if s.is_linked]})
    return {'slot': slot, 'source_material': source_name, 'prepared_material_name': material.name,
            'backface_culling': material.use_backface_culling, 'diffuse_color': list(material.diffuse_color),
            'principled_inputs': inputs, 'linked_images': images,
            'normal_basis': 'Existing prepared tangent-space graph retained; native transfer/readback remains required.'}


def geometry_records(objects, layer_names):
    """World-space triangles including all UVs, corner normals and source materials."""
    records = []
    for obj in objects:
        mesh = obj.data
        mesh.calc_loop_triangles()
        normal_transform = obj.matrix_world.to_3x3().inverted().transposed()
        for tri in mesh.loop_triangles:
            corners = []
            for vi, li in zip(tri.vertices, tri.loops):
                xyz = obj.matrix_world @ mesh.vertices[vi].co
                normal = (normal_transform @ mesh.corner_normals[li].vector).normalized()
                uvs = [list(mesh.uv_layers[name].data[li].uv) if name in mesh.uv_layers else [0, 0]
                       for name in layer_names]
                corners.append([list(xyz), list(normal), uvs])
            records.append([obj.material_slots[tri.material_index].material.name, corners])
    return records


def fingerprint(records):
    def rounded(value):
        if isinstance(value, float):
            return round(value, 5)
        if isinstance(value, list):
            return [rounded(v) for v in value]
        return value
    return hashlib.sha256(json.dumps(rounded(records), separators=(',', ':')).encode()).hexdigest()


def merge_without_remodel(objects):
    """Combine exact source triangles; retain each source vertex, UV, normal and color."""
    layers = sorted({layer.name for o in objects for layer in o.data.uv_layers})
    before = geometry_records(objects, layers)
    verts, faces, normals, uv_values, face_materials, smooth = [], [], [], [], [], []
    materials = []
    color_specs = {}
    colors = collections.defaultdict(list)
    for obj in objects:
        mesh = obj.data
        mesh.calc_loop_triangles()
        for attr in mesh.color_attributes:
            assert attr.domain in {'POINT', 'CORNER'}, attr.name
            spec = (attr.data_type, 'CORNER')
            assert attr.name not in color_specs or color_specs[attr.name] == spec
            color_specs[attr.name] = spec
    for obj in objects:
        mesh = obj.data
        mesh.calc_loop_triangles()
        offset = len(verts)
        verts.extend(list(obj.matrix_world @ v.co) for v in mesh.vertices)
        local_slots = []
        for slot in obj.material_slots:
            assert slot.material
            if slot.material not in materials:
                materials.append(slot.material)
            local_slots.append(materials.index(slot.material))
        nt = obj.matrix_world.to_3x3().inverted().transposed()
        for tri in mesh.loop_triangles:
            faces.append([offset + vi for vi in tri.vertices])
            face_materials.append(local_slots[tri.material_index])
            smooth.append(mesh.polygons[tri.polygon_index].use_smooth)
            for vi, li in zip(tri.vertices, tri.loops):
                normals.append(list((nt @ mesh.corner_normals[li].vector).normalized()))
                uv_values.append([list(mesh.uv_layers[name].data[li].uv) if name in mesh.uv_layers else [0, 0]
                                  for name in layers])
                for name in color_specs:
                    attr = mesh.color_attributes.get(name)
                    colors[name].append(list(attr.data[vi if attr.domain == 'POINT' else li].color)
                                        if attr else [0, 0, 0, 0])
    mesh = bpy.data.meshes.new('VegetationExactLOD0')
    mesh.from_pydata(verts, [], faces)
    for mat in materials:
        mesh.materials.append(mat)
    for i, poly in enumerate(mesh.polygons):
        poly.material_index = face_materials[i]
        poly.use_smooth = smooth[i]
    for j, name in enumerate(layers):
        layer = mesh.uv_layers.new(name=name)
        for i, values in enumerate(uv_values):
            layer.data[i].uv = values[j]
    for name, (kind, domain) in color_specs.items():
        attr = mesh.color_attributes.new(name=name, type=kind, domain=domain)
        for i, color in enumerate(colors[name]):
            attr.data[i].color = color
    mesh.normals_split_custom_set(normals)
    joined = bpy.data.objects.new('VegetationJoinedLOD0', mesh)
    bpy.context.collection.objects.link(joined)
    joined.matrix_world = Matrix.Identity(4)
    after = geometry_records([joined], layers)
    assert len(before) == len(after)
    maximum = {'position_m': 0.0, 'uv': 0.0, 'normal_component': 0.0}
    for a, b in zip(before, after):
        assert a[0] == b[0], 'material_identity_changed'
        for old, new in zip(a[1], b[1]):
            maximum['position_m'] = max(maximum['position_m'], max(abs(x-y) for x,y in zip(old[0],new[0])))
            maximum['normal_component'] = max(maximum['normal_component'], max(abs(x-y) for x,y in zip(old[1],new[1])))
            maximum['uv'] = max(maximum['uv'], max(abs(x-y) for u,v in zip(old[2],new[2]) for x,y in zip(u,v)))
    write(HERE / 'DERIVATIVE_GEOMETRY_COMPARISON.json', maximum)
    assert maximum['position_m'] <= 0.000001 and maximum['uv'] <= 0.000001, maximum
    # Blender stores custom corner normals in a quantized encoding.
    assert maximum['normal_component'] <= 0.0002, maximum
    return joined, {'source_objects': [o.name for o in objects], 'source_triangle_count': len(before),
                    'derivative_triangle_count': len(after), 'triangles_uv_normals_material_sha256': fingerprint(before),
                    'maximum_numeric_difference': maximum,
                    'comparison_tolerances': {'position_m': 0.000001, 'uv': 0.000001, 'normal_component': 0.0002},
                    'vertex_colors_copied': list(color_specs), 'geometry_remodeled': False}


def export(obj, path):
    bpy.ops.object.select_all(action='DESELECT')
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'MESH'},
        use_mesh_modifiers=False, mesh_smooth_type='FACE', use_triangles=False, use_tspace=True,
        add_leaf_bones=False, bake_anim=False, axis_forward='-Z', axis_up='Y',
        apply_unit_scale=True, global_scale=1.0)


results = {}
recipes = []
usage = {}
for entry in read(HERE / 'DERIVATIVE_INPUTS.json')['rows']:
    aid, prepared, manifest = entry['asset_id'], entry['prepared'], entry['manifest']
    original = Path(prepared['blend'])
    before_sha = sha(original)
    bpy.ops.wm.open_mainfile(filepath=str(original), load_ui=False, use_scripts=False)
    primary = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render]
    derivative_evidence = None
    source_names = None
    if aid == 'external.T0976':
        assert len(primary) == 2
        joined, derivative_evidence = merge_without_remodel(primary)
        assert len(joined.data.polygons) == read(prepared['receipt'])['triangles']
        for obj in primary:
            bpy.data.objects.remove(obj, do_unlink=True)
        primary = [joined]
        source_names = [s.material.name for s in joined.material_slots]
    else:
        assert len(primary) == 1
        mappings = [m for m in manifest['material_mapping_by_source_object'] if m['geometry_role'] == 'render_lod0']
        assert len(mappings) == 1
        source_names = mappings[0]['material_slots']
    obj = primary[0]
    assert len(source_names) == len(obj.material_slots)
    folder = OUT / aid.replace('.', '_')
    folder.mkdir(exist_ok=True)
    exports = []
    lod_objects = [obj]
    if aid == 'external.T0976':
        lod_objects += sorted([o for o in bpy.context.scene.objects if o.type == 'MESH' and '_LOD' in o.name], key=lambda o: o.name)
    for level, lod in enumerate(lod_objects):
        file = folder / ('LOD' + str(level) + '.fbx')
        export(lod, file)
        lod.data.calc_loop_triangles()
        exports.append({'lod': level, 'source_object': lod.name, 'fbx': str(file), 'sha256': sha(file),
                        'triangles': len(lod.data.loop_triangles)})
    # An explicit derivative copy gives import recipes a reproducible material/slot source.
    derivative_blend = folder / 'Prepared_Category.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(derivative_blend), check_existing=False)
    recipe_rows = [recipe(s.material, i, source_names[i]) for i, s in enumerate(obj.material_slots)]
    recipes.append({'asset_id': aid, 'prepared_blend': str(derivative_blend),
                    'prepared_blend_sha256': sha(derivative_blend), 'materials': recipe_rows,
                    'source_preserved': True, 'native_imported': False, 'source_object': obj.name,
                    'render_kind': 'existing_preparation_reused_no_new_render',
                    'material_transfer_status': 'recipe_saved_native_binding_pending'})
    counts = collections.Counter(p.material_index for p in obj.data.polygons)
    usage[aid] = {'source': str(derivative_blend), 'sha256': sha(derivative_blend),
                  'used_slots': sorted(counts), 'slots': [
                      {'index': i, 'material': s.material.name, 'polygons': counts[i]}
                      for i, s in enumerate(obj.material_slots)]}
    assert sha(original) == before_sha
    results[aid] = {'original_prepared_blend': str(original), 'original_prepared_sha256': before_sha,
                    'prepared_blend': str(derivative_blend), 'prepared_blend_sha256': sha(derivative_blend),
                    'exports': exports, 'material_slots': source_names, 'source_files_unchanged': True,
                    'derivative_evidence': derivative_evidence, 'native_import_or_appearance_proven': False}
write(HERE / 'DERIVATIVE_RESULT.json', results)
write(HERE / 'ADDITIONAL_MATERIAL_RECIPES.json', recipes)
write(HERE / 'ADDITIONAL_SLOT_USAGE.json', usage)
print(json.dumps({'vegetation_derivatives': list(results), 'originals_changed': False, 'new_renders': 0}))
