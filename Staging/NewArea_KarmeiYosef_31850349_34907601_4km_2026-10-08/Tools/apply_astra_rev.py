"""In-editor (Karmei Yosef operator), 2026-10-11. Generic import of an Astra revision (first use: FieldCrops_v004 = vine rows,
olives, field grass; Aviv asked Astra for them, and for using them in the rebuilt farmland). Same rules as apply_v003.py:
imported NEXT TO earlier versions under <clone>/PazFarm/<revision>/, nothing existing changed, runs in any world.
  textures   PNGs -> <rev>/Textures (BaseColor sRGB; Normal = normal map, green flipped; ORM linear masks)
  materials  one MI per material on the v1 opaque master or the existing VisualFix_v003 opaque two-sided master
  meshes     base FBX (Nanite on, Preserve Area, no collision), slots bound by name, the matching *_LOD3.fbx as LOD1
ARGS: expected_pid, step, revision (folder name under AstraModels/Revisions), names (optional subset of base meshes),
import_normals (bool, meshes step: keep the FBX normals; used from StrawberryBeds_v005 on).
"""
import datetime, hashlib, json, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
REVN = ARGS['revision']
SRC = ROOT / 'Staging/PazFarm_2026-10-08/AstraModels/Revisions' / REVN
TRIAL = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial'
V1 = TRIAL + '/PazFarm'
VF3 = TRIAL + '/PazFarm/' + REVN                     # destination folder (named like the revision)
TWO_SIDED = TRIAL + '/PazFarm/VisualFix_v003/Materials/M_PazFarm_Master_OpaqueTwoSided'
L = u.MaterialEditingLibrary
EAL = u.EditorAssetLibrary
pid = os.getpid(); assert pid == ARGS['expected_pid']
sms = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
step = ARGS['step']
man = json.loads((SRC / 'MANIFEST.json').read_text(encoding='utf-8'))
assets = {a['name']: a for a in man['assets']}
BASES = tuple(p.get('base_asset') or p['base_model'] for p in man['lod_pairings'])      # v005 manifest: base_model
mats = {}
for a in man['assets']:
    for m in a['materials']:
        mats.setdefault(m['name'], {'mode': m['mode'], 'textures': [Path(t.replace(chr(92), '/')).stem for t in m['textures']]})
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
    for s_ in range(64):
        try:
            idx = sms.get_lod_material_slot(mesh, lod, s_)
        except Exception:
            break
        if idx is None or idx < 0:
            break
        out.append(str(slots[idx].get_editor_property('material_slot_name')) if idx < len(slots) else 'slot%d?' % idx)
    return out


if step == 'textures':
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
    two = u.load_asset(TWO_SIDED); assert two, TWO_SIDED                 # reuse the v003 two-sided master (no new master)
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
            if kind not in ('BaseColor', 'Normal', 'ORM'):
                continue
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
            if ARGS.get('import_normals'):                     # v005 (Astra): keep the authored normals
                smd.set_editor_property('normal_import_method', u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
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
        lods_before = sms.get_lod_count(mesh)
        if lods_before < 2:
            got = sms.import_lod(mesh, 1, str(low))
            assert got == 1, ('import_lod', name, got)
        # bind AFTER the lowest-LOD import: a slot used only by the lowest LOD (v005 MulchDistant) is created by import_lod
        slots = mesh.get_editor_property('static_materials')
        bound = []
        for i, sl in enumerate(slots):
            base = str(sl.get_editor_property('material_slot_name')).split('.')[0]
            p = VF3 + '/Materials/' + mi_name(base) if base.startswith('M_PazFarm_') else None
            if p and EAL.does_asset_exist(p):
                mesh.set_material(i, u.load_asset(p)); bound.append(base)
            else:
                notes.append('%s slot %d %s unmatched' % (name, i, base))
        mesh.set_editor_property('auto_compute_lod_screen_size', False) if hasattr(mesh, 'auto_compute_lod_screen_size') else None
        out[name] = {'slots': bound, 'lod_count': sms.get_lod_count(mesh), 'lod_verts': [sms.get_number_verts(mesh, l) for l in range(sms.get_lod_count(mesh))],
                     'lod1_sections': lod_sections(mesh, 1), 'lod0_sections': lod_sections(mesh, 0),
                     'size_m': bounds_m(mesh), 'manifest_size_m': assets[name].get('size_metres_W_D_H'),
                     'nanite': str(mesh.get_editor_property('nanite_settings').get_editor_property('enabled'))}
        assert save([mesh])
    (TASK / 'receipts' / ('ASTRA_%s_MESHES.json' % REVN)).write_text(json.dumps(out, indent=2), encoding='utf-8')
    RESULT = {'ok': True, 'meshes': out, 'notes': notes, 'dirty': dirty()}

