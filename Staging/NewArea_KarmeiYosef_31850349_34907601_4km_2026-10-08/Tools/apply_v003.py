"""In-editor (Karmei Yosef operator), 2026-10-10. Aviv: "Yes, import both" = Astra VisualFix v003 (3 Aleppo pines + strawberry
bed v003, each with an authored lowest LOD). Imported NEXT TO earlier versions under <clone>/PazFarm/VisualFix_v003/; nothing
existing is changed by the import steps (they run in any world; the map steps run only on the clone).
steps (ARGS.step):
  probe      read-only: available LOD API, bounds of the current pine copies and the strawberry bed in use.
  textures   36 PNGs -> VisualFix_v003/Textures (BaseColor sRGB; Normal = normal map, green flipped OpenGL -> DirectX; ORM linear masks).
  materials  master M_PazFarm_Master_OpaqueTwoSided (copy of the v1 opaque master with two-sided on; property only, no graph
             edit) + one MI per v003 material (BaseColor/Normal/ORM) on the opaque or opaque two-sided master.
  meshes     4 base FBX (Nanite on, Preserve Area, no collision), slots bound by name; the matching *_LOD3.fbx imported as
             LOD1 = the authored final LOD (no auto reduction, no billboard); LOD1 section slots checked by name.
  swap_bed   clone only: PazFarm_Detail strawberry HISM -> v003 bed (763 instances unchanged). Writes the before-receipt.
  swap_windbreak_pines  clone only: KY4_Windbreaks pine HISMs -> Aleppo pines (ARGS.pine_map {old name: new name}).
  revert     clone only: restore the meshes in the before-receipt.
ARGS: expected_pid, step [, pine_map].
"""
import datetime, hashlib, json, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
SRC = ROOT / 'Staging/PazFarm_2026-10-08/AstraModels/Revisions/VisualFix_v003'
TRIAL = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial'
CLONE = TRIAL + '/L_KarmeiYosef_31850349_34907601_4km_PCGTrial' + ARGS.get('clone_suffix', '')     # '_v2' = rebuilt clone
V1 = TRIAL + '/PazFarm'
VF3 = TRIAL + '/PazFarm/VisualFix_v003'
COPY = TRIAL + '/Vegetation/Meshes/'
BEFORE = TASK / 'receipts' / 'PAZFARM_V003_BEFORE.json'
BASES = ('SM_PazFarm_AleppoPine_A', 'SM_PazFarm_AleppoPine_B', 'SM_PazFarm_AleppoPine_C', 'SM_PazFarm_StrawberryBed_4m')
L = u.MaterialEditingLibrary
EAL = u.EditorAssetLibrary
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
sms = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
step = ARGS['step']
man = json.loads((SRC / 'MANIFEST.json').read_text(encoding='utf-8'))
assets = {a['name']: a for a in man['assets']}
mats = {}
for a in man['assets']:
    for m in a['materials']:
        mats.setdefault(m['name'], {'mode': m['mode'], 'textures': [Path(t.replace('\\', '/')).stem for t in m['textures']]})
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
save = lambda objs: u.EditorLoadingAndSavingUtils.save_packages([o.get_outermost() for o in objs], False)
mesh_path = lambda m: m.get_path_name().split('.')[0] if m else None
mi_name = lambda mat: 'MI_PazFarm_' + mat[len('M_PazFarm_'):]


def bounds_m(mesh):
    b = mesh.get_bounding_box()
    return [round((b.max.x - b.min.x) / 100, 2), round((b.max.y - b.min.y) / 100, 2), round((b.max.z - b.min.z) / 100, 2)]


def lod_sections(mesh, lod):
    out = []
    slots = mesh.get_editor_property('static_materials')
    for s in range(sms.get_number_materials(mesh) if False else 64):
        try:
            idx = sms.get_lod_material_slot(mesh, lod, s)
        except Exception:
            break
        if idx is None or idx < 0:
            break
        out.append(str(slots[idx].get_editor_property('material_slot_name')) if idx < len(slots) else 'slot%d?' % idx)
    return out


def in_clone():
    assert world.get_outermost().get_path_name() == CLONE, world.get_outermost().get_path_name()


if step == 'probe':
    out = {'world': world.get_outermost().get_path_name(),
           'sms_methods': sorted(n for n in dir(sms) if 'lod' in n.lower() or 'section' in n.lower()),
           'pine_copies_m': {n: bounds_m(u.load_asset(COPY + n)) for n in ('SM_Pine_Tree_01', 'SM_Pine_Tree_02', 'SM_Pine_Tree_03', 'SM_Pine_Tree_05', 'SM_green-tree01', 'SM_green-tree02')},
           'v003_sizes_m': {n: a.get('size_metres_W_D_H') for n, a in assets.items()}}
    RESULT = {'ok': True, **out, 'dirty': dirty()}

elif step == 'textures':
    files = sorted((SRC / 'Textures').glob('*.png'))
    tasks = []
    for f in files:
        if EAL.does_asset_exist(VF3 + '/Textures/' + f.stem):
            continue
        t = u.AssetImportTask()
        for k, v in dict(filename=str(f), destination_path=VF3 + '/Textures', destination_name=f.stem, automated=True, replace_existing=False, save=False).items():
            t.set_editor_property(k, v)
        tasks.append(t)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    objs = []
    for f in files:
        tex = u.load_asset(VF3 + '/Textures/' + f.stem); assert tex, f.stem
        if f.stem.endswith('_Normal'):
            tex.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_NORMALMAP)
            tex.set_editor_property('srgb', False); tex.set_editor_property('flip_green_channel', True)
        elif f.stem.endswith('_ORM'):
            tex.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_MASKS); tex.set_editor_property('srgb', False)
        else:
            tex.set_editor_property('srgb', True)
        objs.append(tex)
    assert save(objs)
    RESULT = {'ok': True, 'imported': len(tasks), 'textures': len(objs), 'dirty': dirty()}

elif step == 'materials':
    opaque = u.load_asset(V1 + '/Materials/M_PazFarm_Master_Opaque'); assert opaque
    two_path = VF3 + '/Materials/M_PazFarm_Master_OpaqueTwoSided'
    if not EAL.does_asset_exist(two_path):
        two = EAL.duplicate_asset(V1 + '/Materials/M_PazFarm_Master_Opaque', two_path)
        two.set_editor_property('two_sided', True)
        L.recompile_material(two)
        assert save([two])
    two = u.load_asset(two_path)
    assert two.get_editor_property('two_sided') and opaque.get_editor_property('blend_mode') == u.BlendMode.BLEND_OPAQUE
    masters = {'OPAQUE': opaque, 'OPAQUE_TWO_SIDED': two}
    mis = []
    for name, m in sorted(mats.items()):
        path = VF3 + '/Materials/' + mi_name(name)
        mi = u.load_asset(path) if EAL.does_asset_exist(path) else \
            u.AssetToolsHelpers.get_asset_tools().create_asset(mi_name(name), VF3 + '/Materials', u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        L.set_material_instance_parent(mi, masters[m['mode']])
        for stem in m['textures']:
            kind = stem.rsplit('_', 1)[1]
            assert kind in ('BaseColor', 'Normal', 'ORM'), stem
            L.set_material_instance_texture_parameter_value(mi, kind, u.load_asset(VF3 + '/Textures/' + stem))
        L.update_material_instance(mi)
        mis.append(mi)
    assert save(mis)
    RESULT = {'ok': True, 'masters': {k: v.get_path_name() for k, v in masters.items()}, 'instances': [m.get_name() for m in mis], 'dirty': dirty()}

elif step == 'meshes':
    out, notes = {}, []
    for name in ARGS.get('names', BASES):
        f = SRC / 'FBX' / (name + '.fbx'); low = SRC / 'FBX' / (name + '_LOD3.fbx'); assert f.exists() and low.exists(), name
        path = VF3 + '/Meshes/' + name
        if not EAL.does_asset_exist(path):
            ui = u.FbxImportUI()
            ui.set_editor_property('import_mesh', True); ui.set_editor_property('import_as_skeletal', False)
            ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False)
            ui.set_editor_property('import_animations', False)
            smd = ui.get_editor_property('static_mesh_import_data')
            smd.set_editor_property('combine_meshes', True); smd.set_editor_property('auto_generate_collision', False)
            smd.set_editor_property('build_nanite', True)
            t = u.AssetImportTask()
            for k, v in dict(filename=str(f), destination_path=VF3 + '/Meshes', destination_name=name, automated=True, replace_existing=False, save=False, options=ui).items():
                t.set_editor_property(k, v)
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        mesh = u.load_asset(path); assert isinstance(mesh, u.StaticMesh), path
        s = mesh.get_editor_property('nanite_settings')
        s.set_editor_property('enabled', True)
        if hasattr(s, 'shape_preservation'):
            s.set_editor_property('shape_preservation', u.NaniteShapePreservation.PRESERVE_AREA)
        sms.set_nanite_settings(mesh, s, True)
        slots = mesh.get_editor_property('static_materials')
        bound = []
        for i, sl in enumerate(slots):
            base = str(sl.get_editor_property('material_slot_name')).split('.')[0]
            p = VF3 + '/Materials/' + mi_name(base) if base.startswith('M_PazFarm_') else None
            if p and EAL.does_asset_exist(p):
                mesh.set_material(i, u.load_asset(p)); bound.append(base)
            else:
                notes.append('%s slot %d %s unmatched' % (name, i, base))
        lods_before = sms.get_lod_count(mesh)
        if lods_before < 2:
            got = sms.import_lod(mesh, 1, str(low))
            assert got == 1, ('import_lod', name, got)
        mesh.set_editor_property('auto_compute_lod_screen_size', False) if hasattr(mesh, 'auto_compute_lod_screen_size') else None
        out[name] = {'slots': bound, 'lod_count': sms.get_lod_count(mesh), 'lod_verts': [sms.get_number_verts(mesh, l) for l in range(sms.get_lod_count(mesh))],
                     'lod1_sections': lod_sections(mesh, 1), 'lod0_sections': lod_sections(mesh, 0),
                     'size_m': bounds_m(mesh), 'manifest_size_m': assets[name].get('size_metres_W_D_H'),
                     'nanite': str(mesh.get_editor_property('nanite_settings').get_editor_property('enabled'))}
        assert save([mesh])
    (TASK / 'receipts' / 'PAZFARM_V003_MESHES.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    RESULT = {'ok': True, 'meshes': out, 'notes': notes, 'dirty': dirty()}

elif step in ('swap_bed', 'swap_windbreak_pines', 'revert'):
    in_clone()
    det = [a for a in eas.get_all_level_actors() if a.get_actor_label() == 'PazFarm_Detail'][0]
    wb = [a for a in eas.get_all_level_actors() if a.get_actor_label() == 'KY4_Windbreaks'][0]
    comps = lambda a: {mesh_path(c.get_editor_property('static_mesh')).rsplit('/', 1)[1]: c for c in a.get_components_by_class(u.HierarchicalInstancedStaticMeshComponent)}
    before = json.loads(BEFORE.read_text()) if BEFORE.exists() else {}
    changed = []
    if step == 'swap_bed':
        c = [x for n, x in comps(det).items() if n.startswith('SM_PazFarm_StrawberryBed_4m')][0]
        before.setdefault('bed', {'component': c.get_name(), 'mesh': mesh_path(c.get_editor_property('static_mesh')), 'instances': c.get_instance_count()})
        before['bed']['component'] = before['bed'].get('component') or c.get_name()
        n0 = c.get_instance_count(); det.modify(); c.modify()
        c.set_static_mesh(u.load_asset(VF3 + '/Meshes/SM_PazFarm_StrawberryBed_4m'))
        assert c.get_instance_count() == n0 == 762, (n0, c.get_instance_count())        # 763 placed, one trimmed by fence_v003 (2026-10-09)
        changed.append([before['bed']['mesh'], mesh_path(c.get_editor_property('static_mesh'))])
    elif step == 'swap_windbreak_pines':
        pm = ARGS['pine_map']; cs = comps(wb)
        before.setdefault('windbreak', {})
        for old, new in pm.items():
            c = cs[old]; before['windbreak'].setdefault(c.get_name(), mesh_path(c.get_editor_property('static_mesh')))
            n0 = c.get_instance_count(); wb.modify(); c.modify()
            c.set_static_mesh(u.load_asset(VF3 + '/Meshes/' + new))
            assert c.get_instance_count() == n0
            changed.append([old, new, n0])
    else:
        for c in det.get_components_by_class(u.HierarchicalInstancedStaticMeshComponent):
            if 'bed' in before and c.get_name() == before['bed']['component']:   # restores the recorded (v002) bed
                det.modify(); c.modify(); c.set_static_mesh(u.load_asset(before['bed']['mesh'])); changed.append(c.get_name())
        for c in wb.get_components_by_class(u.HierarchicalInstancedStaticMeshComponent):
            if c.get_name() in before.get('windbreak', {}):
                wb.modify(); c.modify(); c.set_static_mesh(u.load_asset(before['windbreak'][c.get_name()])); changed.append(c.get_name())
    if step != 'revert':
        before['utc_first'] = before.get('utc_first', datetime.datetime.now(datetime.timezone.utc).isoformat())
        BEFORE.write_text(json.dumps(before, indent=2), encoding='utf-8')
    RESULT = {'ok': True, 'changed': changed, 'dirty': dirty()}
