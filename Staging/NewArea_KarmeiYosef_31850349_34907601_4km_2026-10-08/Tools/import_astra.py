"""In-editor (Karmei Yosef operator), Aviv's editor PID 19732, 2026-10-08. Import Astra's Paz Farm delivery into the 4 km PCG
trial folder only: <trial>/PazFarm/{Textures,Materials,Meshes}. Textures: *_BaseColor sRGB, *_Normal normal map with green
flip (OpenGL -> DirectX), *_ORM linear masks. Three masters (Opaque, Masked two-sided, Translucent two-sided) with
BaseColor/Normal/ORM parameters (ORM: R=AO, G=Roughness, B=Metallic; alpha -> opacity mask / opacity) and one MI per Astra
material (MI_PazFarm_<Name>). FBX: no material/texture import, Nanite on, UCX collision kept; mesh slots get the matching MI.
Named saves of these new packages only. ARGS: expected_pid, step ('textures' | 'master' + label | 'instances' | 'meshes').
"""
import datetime, json, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
SRC = ROOT / 'Staging/PazFarm_2026-10-08/AstraModels'
BASE = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/PazFarm'
L = u.MaterialEditingLibrary
pid = os.getpid(); assert pid == ARGS['expected_pid']
man = json.loads((SRC / 'MANIFEST.json').read_text(encoding='utf-8'))
mats = {}
for a in man['assets']:
    for m in a['materials']:
        mats.setdefault(m['name'], {'mode': m['mode'], 'textures': [Path(t).name for t in m['textures']]})
step = ARGS['step']
saved, notes = [], []
save = lambda objs: (u.EditorLoadingAndSavingUtils.save_packages([o.get_outermost() for o in objs], False), saved.extend(o.get_outermost().get_name() for o in objs))

if step == 'textures':
    files = sorted((SRC / 'Textures').glob('*.png'))
    tasks = []
    for f in files:
        if u.EditorAssetLibrary.does_asset_exist(BASE + '/Textures/' + f.stem):
            continue
        t = u.AssetImportTask()
        for k, v in dict(filename=str(f), destination_path=BASE + '/Textures', destination_name=f.stem, automated=True, replace_existing=False, save=False).items():
            t.set_editor_property(k, v)
        tasks.append(t)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    objs = []
    for f in files:
        tex = u.load_asset(BASE + '/Textures/' + f.stem)
        assert tex, f.stem
        if f.stem.endswith('_Normal'):
            tex.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_NORMALMAP)
            tex.set_editor_property('srgb', False); tex.set_editor_property('flip_green_channel', True)
        elif f.stem.endswith('_ORM'):
            tex.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_MASKS); tex.set_editor_property('srgb', False)
        else:
            tex.set_editor_property('srgb', True)
        objs.append(tex)
    save(objs)
    RESULT = {'ok': True, 'textures': len(objs)}

elif step == 'master':
    # One master per call. MaterialFactoryNew crashed Aviv's editor (16:00:06Z, python311 <- MaterialEditor), so copy a
    # simple StarterContent material and rebuild its graph instead (duplicate + edit worked all day).
    tex = lambda name: u.load_asset(BASE + '/Textures/' + name)
    LABELS = {'Opaque': 'OPAQUE', 'Masked': 'MASKED_TWO_SIDED', 'Translucent': 'TRANSLUCENT_TWO_SIDED'}
    label = ARGS['label']; mode = LABELS[label]
    path = BASE + '/Materials/M_PazFarm_Master_' + label
    assert not u.EditorAssetLibrary.does_asset_exist(path), 'master exists'
    first = next(m for m in mats.values() if m['mode'] == mode)
    mat = u.EditorAssetLibrary.duplicate_asset('/Game/StarterContent/Materials/M_Basic_Wall', path)
    L.delete_all_material_expressions(mat)
    if mode != 'OPAQUE':
        mat.set_editor_property('two_sided', True)
        mat.set_editor_property('blend_mode', u.BlendMode.BLEND_MASKED if mode == 'MASKED_TWO_SIDED' else u.BlendMode.BLEND_TRANSLUCENT)
    if mode == 'TRANSLUCENT_TWO_SIDED':
        mat.set_editor_property('translucency_lighting_mode', u.TranslucencyLightingMode.TLM_SURFACE)
    tx = {Path(t).stem.rsplit('_', 1)[1]: Path(t).stem for t in first['textures']}
    exprs = {}
    for i, (name, sampler) in enumerate((('BaseColor', u.MaterialSamplerType.SAMPLERTYPE_COLOR), ('Normal', u.MaterialSamplerType.SAMPLERTYPE_NORMAL),
                                         ('ORM', u.MaterialSamplerType.SAMPLERTYPE_MASKS))):
        e = L.create_material_expression(mat, u.MaterialExpressionTextureSampleParameter2D, -600, -200 + 300 * i)
        e.set_editor_property('parameter_name', name); e.set_editor_property('texture', tex(tx[name])); e.set_editor_property('sampler_type', sampler)
        exprs[name] = e
    P = u.MaterialProperty
    assert L.connect_material_property(exprs['BaseColor'], 'RGB', P.MP_BASE_COLOR)
    assert L.connect_material_property(exprs['Normal'], 'RGB', P.MP_NORMAL)
    assert L.connect_material_property(exprs['ORM'], 'R', P.MP_AMBIENT_OCCLUSION)
    assert L.connect_material_property(exprs['ORM'], 'G', P.MP_ROUGHNESS)
    assert L.connect_material_property(exprs['ORM'], 'B', P.MP_METALLIC)
    if mode == 'MASKED_TWO_SIDED':
        assert L.connect_material_property(exprs['BaseColor'], 'A', P.MP_OPACITY_MASK)
    if mode == 'TRANSLUCENT_TWO_SIDED':
        assert L.connect_material_property(exprs['BaseColor'], 'A', P.MP_OPACITY)
    L.recompile_material(mat)
    save([mat])
    RESULT = {'ok': True, 'master': path}

elif step == 'instances':
    tex = lambda name: u.load_asset(BASE + '/Textures/' + name)
    masters = {mode: u.load_asset(BASE + '/Materials/M_PazFarm_Master_' + label) for label, mode in
               (('Opaque', 'OPAQUE'), ('Masked', 'MASKED_TWO_SIDED'), ('Translucent', 'TRANSLUCENT_TWO_SIDED'))}
    assert all(masters.values()), masters
    mis = []
    for name, m in mats.items():
        mi_name = 'MI_PazFarm_' + name[len('M_PazFarm_'):]
        path = BASE + '/Materials/' + mi_name
        mi = u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else             u.AssetToolsHelpers.get_asset_tools().create_asset(mi_name, BASE + '/Materials', u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        L.set_material_instance_parent(mi, masters[m['mode']])
        for t in m['textures']:
            stem = Path(t).stem; kind = stem.rsplit('_', 1)[1]
            if kind in ('BaseColor', 'Normal', 'ORM'):
                L.set_material_instance_texture_parameter_value(mi, kind, tex(stem))
            else:
                notes.append('%s: extra texture %s not wired' % (name, stem))
        L.update_material_instance(mi)
        mis.append(mi)
    save(mis)
    RESULT = {'ok': True, 'instances': len(mis), 'notes': notes}

elif step == 'meshes':
    out = {}
    for f in sorted((SRC / 'FBX').glob('*.fbx')):
        path = BASE + '/Meshes/' + f.stem
        if not u.EditorAssetLibrary.does_asset_exist(path):
            ui = u.FbxImportUI()
            ui.set_editor_property('import_mesh', True); ui.set_editor_property('import_as_skeletal', False)
            ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False)
            ui.set_editor_property('import_animations', False)
            sm = ui.get_editor_property('static_mesh_import_data')
            sm.set_editor_property('combine_meshes', True); sm.set_editor_property('auto_generate_collision', False)
            try:
                sm.set_editor_property('build_nanite', True)
            except Exception as exc:
                notes.append('build_nanite not set: ' + repr(exc)[:80])
            t = u.AssetImportTask()
            for k, v in dict(filename=str(f), destination_path=BASE + '/Meshes', destination_name=f.stem, automated=True, replace_existing=False, save=False, options=ui).items():
                t.set_editor_property(k, v)
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        mesh = u.load_asset(path)
        assert isinstance(mesh, u.StaticMesh), path
        slots = mesh.get_editor_property('static_materials')
        assigned = []
        for i, s in enumerate(slots):
            sname = str(s.get_editor_property('material_slot_name'))
            base = sname.split('.')[0]
            if base.startswith('M_PazFarm_'):
                mi = u.load_asset(BASE + '/Materials/MI_PazFarm_' + base[len('M_PazFarm_'):])
                if mi:
                    mesh.set_material(i, mi); assigned.append(base); continue
            notes.append('%s slot %d %s unmatched' % (f.stem, i, sname))
        b = mesh.get_bounding_box()
        out[f.stem] = {'size_cm': [round(b.max.x - b.min.x), round(b.max.y - b.min.y), round(b.max.z - b.min.z)],
                       'min_cm': [round(b.min.x), round(b.min.y), round(b.min.z)], 'slots': len(slots), 'assigned': len(assigned)}
        save([mesh])
    (TASK / 'receipts' / 'ASTRA_IMPORT_MESHES.json').write_text(json.dumps({'meshes': out, 'notes': notes}, indent=2), encoding='utf-8')
    RESULT = {'ok': True, 'meshes': out, 'notes': notes[:20]}
