"""In-editor (Karmei Yosef operator, own editor on the 4 km PCG clone), 2026-10-09. Apply Astra's Paz Farm VisualFix_v002
reversibly (Aviv: "make it reversible"): the revision is imported NEXT TO v1 under <clone>/PazFarm/v002/ and swapped in;
v1 packages stay untouched, so 'revert' swaps back from the before-receipt.
steps (ARGS.step):
  probe      read-only: PazFarm actors, HISM meshes/counts, barn mesh/overrides, gate e/n, ground MI FarmColor, Nanite fields.
  textures   import changed/new v002 PNGs (sha differs from v1) + the v002 ground PNG into v002/Textures (named saves).
  materials  one MIC per v002 material that uses a changed/new texture, parent = existing v1 master (named saves).
  meshes     ARGS.names: import those FBX into v002/Meshes (Nanite; plants get Preserve Area), bind slots by name
             (v002 MI if present, else v1 MI), compare bounds with v1 (named saves).
  swap       write receipts/PAZFARM_V002_BEFORE.json once, then: HISM meshes -> v002, barn mesh -> v002, clone ground MI
             FarmColor -> v002 ground texture, gate moved to Astra's PLACEMENT_PATCH centre (centre pivot). No save.
  revert     restore everything recorded in the before-receipt. No save.
  save       named saves: dirty content under <clone>/PazFarm/ only, then the clone map. Refuses anything else.
ARGS: expected_pid, step [, names].
"""
import datetime, hashlib, json, math, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
GEO = ROOT / 'Staging/PazFarm_2026-10-08/Georef'
SRC1 = ROOT / 'Staging/PazFarm_2026-10-08/AstraModels'
SRC2 = SRC1 / 'Revisions/VisualFix_v002'
TRIAL = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial'
CLONE = TRIAL + '/L_KarmeiYosef_31850349_34907601_4km_PCGTrial'
V1, V2 = TRIAL + '/PazFarm', TRIAL + '/PazFarm/v002'
GROUND_MI = V1 + '/Materials/MI_GeoCityGround_PazFarm'
BEFORE = TASK / 'receipts' / 'PAZFARM_V002_BEFORE.json'
PLANTS = ('SM_PazFarm_Avocado_A', 'SM_PazFarm_Avocado_B', 'SM_PazFarm_Avocado_C', 'SM_PazFarm_Lemon_A', 'SM_PazFarm_Lemon_B',
          'SM_PazFarm_Orange_A', 'SM_PazFarm_Orange_B', 'SM_PazFarm_StrawberryBed_4m')
L = u.MaterialEditingLibrary
EAL = u.EditorAssetLibrary
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == CLONE
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
actors = {a.get_actor_label(): a for a in eas.get_all_level_actors() if a.get_actor_label().startswith('PazFarm_')}
step = ARGS['step']
pe, pn = json.loads((GEO / 'roads.json').read_text())['pin_local_m_from_area_centre']
XY = lambda e, n: ((pe + e) * 100.0, -(pn + n) * 100.0)          # metres from pin -> Unreal cm (X east, Y south)
EN = lambda x, y: (x / 100.0 - pe, -y / 100.0 - pn)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
man2 = json.loads((SRC2 / 'MANIFEST.json').read_text(encoding='utf-8'))
mats2 = {}
for a in man2['assets']:
    for m in a['materials']:
        mats2.setdefault(m['name'], {'mode': m['mode'], 'textures': [Path(t.replace('\\', '/')).stem for t in m['textures']]})
changed_tex = sorted(f.stem for f in (SRC2 / 'Textures').glob('*.png')
                     if not (SRC1 / 'Textures' / f.name).exists() or sha(f) != sha(SRC1 / 'Textures' / f.name))
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
save = lambda objs: u.EditorLoadingAndSavingUtils.save_packages([o.get_outermost() for o in objs], False)
mesh_path = lambda m: m.get_path_name().split('.')[0] if m else None


def bounds(mesh):
    b = mesh.get_bounding_box()
    return {'min': [round(b.min.x, 1), round(b.min.y, 1), round(b.min.z, 1)], 'max': [round(b.max.x, 1), round(b.max.y, 1), round(b.max.z, 1)]}


def nanite_fields(mesh):
    s = mesh.get_editor_property('nanite_settings')
    out = {}
    for n in dir(s):
        if n.startswith('_') or callable(getattr(s, n, None)):
            continue
        try:
            out[n] = str(getattr(s, n))
        except Exception as exc:
            out[n] = 'ERR ' + repr(exc)[:60]
    return out


def detail_hisms():
    return {mesh_path(c.get_editor_property('static_mesh')).rsplit('/', 1)[1]: c
            for c in actors['PazFarm_Detail'].get_components_by_class(u.HierarchicalInstancedStaticMeshComponent)}


def ground(x, y):
    ignore = [a for a in eas.get_all_level_actors() if not isinstance(a, (u.Landscape, u.LandscapeProxy))]
    hit = u.SystemLibrary.line_trace_single(world, u.Vector(x, y, 60000.0), u.Vector(x, y, -20000.0),
                                            u.TraceTypeQuery.TRACE_TYPE_QUERY1, False, ignore, u.DrawDebugTrace.NONE, True)
    h = hit[1] if isinstance(hit, tuple) else hit
    t = h.to_tuple() if h is not None else None
    assert t and t[0], 'ground trace missed at %s,%s' % (x, y)
    return t[4].z


def state():
    hisms = detail_hisms()
    barn, gate = actors['PazFarm_Barn'], actors['PazFarm_Gate']
    bc = barn.static_mesh_component
    gl, gr = gate.get_actor_location(), gate.get_actor_rotation()
    mi = u.load_asset(GROUND_MI)
    farm = L.get_material_instance_texture_parameter_value(mi, 'FarmColor')
    return {
        'hism': {k: {'mesh': mesh_path(c.get_editor_property('static_mesh')), 'instances': c.get_instance_count()} for k, c in hisms.items()},
        'barn': {'mesh': mesh_path(bc.get_editor_property('static_mesh')),
                 'override_materials': [m.get_path_name() if m else None for m in bc.get_editor_property('override_materials')],
                 'scale': [round(v, 4) for v in (barn.get_actor_scale3d().x, barn.get_actor_scale3d().y, barn.get_actor_scale3d().z)]},
        'gate': {'loc': [gl.x, gl.y, gl.z], 'yaw': gr.yaw, 'pitch': gr.pitch, 'roll': gr.roll, 'en': [round(v, 3) for v in EN(gl.x, gl.y)]},
        'ground_mi': {'path': GROUND_MI, 'FarmColor': farm.get_path_name() if farm else None,
                      'Farm_Blend': L.get_material_instance_scalar_parameter_value(mi, 'Farm_Blend')},
    }


if step == 'probe':
    s = state()
    v1_tree = u.load_asset(V1 + '/Meshes/SM_PazFarm_Avocado_A')
    RESULT = {'ok': True, 'actors': sorted(actors), 'state': s, 'changed_textures': changed_tex,
              'nanite_v1_avocado_a': nanite_fields(v1_tree), 'v1_bounds': {n: bounds(u.load_asset(V1 + '/Meshes/' + n)) for n in PLANTS + ('SM_PazFarm_Barn',)},
              'v2_exists': EAL.does_directory_exist(V2), 'dirty': dirty()}

elif step == 'textures':
    jobs = [(SRC2 / 'Textures' / (n + '.png'), n) for n in changed_tex] + [(SRC2 / 'Georef/T_PazFarm_Ground.png', 'T_PazFarm_Ground')]
    tasks = []
    for f, name in jobs:
        if EAL.does_asset_exist(V2 + '/Textures/' + name):
            continue
        t = u.AssetImportTask()
        for k, v in dict(filename=str(f), destination_path=V2 + '/Textures', destination_name=name, automated=True, replace_existing=False, save=False).items():
            t.set_editor_property(k, v)
        tasks.append(t)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    v1g = u.load_asset(TRIAL.replace('_PCGTrial', '') + '/BankIntegration_v015/Materials/Zones/T_PazFarm_Ground')
    objs = []
    for f, name in jobs:
        tex = u.load_asset(V2 + '/Textures/' + name)
        assert tex, name
        if name == 'T_PazFarm_Ground':                                           # same settings as the v1 farm texture
            for p in ('srgb', 'address_x', 'address_y', 'compression_settings', 'mip_gen_settings', 'lod_group'):
                tex.set_editor_property(p, v1g.get_editor_property(p))
        elif name.endswith('_Normal'):
            tex.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_NORMALMAP)
            tex.set_editor_property('srgb', False); tex.set_editor_property('flip_green_channel', True)
        elif name.endswith('_ORM'):
            tex.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_MASKS); tex.set_editor_property('srgb', False)
        else:
            tex.set_editor_property('srgb', True)
        objs.append(tex)
    assert save(objs)
    RESULT = {'ok': True, 'imported': len(tasks), 'textures': [o.get_name() for o in objs], 'dirty': dirty()}

elif step == 'materials':
    masters = {mode: u.load_asset(V1 + '/Materials/M_PazFarm_Master_' + label) for label, mode in
               (('Opaque', 'OPAQUE'), ('Masked', 'MASKED_TWO_SIDED'), ('Translucent', 'TRANSLUCENT_TWO_SIDED'))}
    assert all(masters.values()), masters
    tex = lambda stem: u.load_asset((V2 if stem in changed_tex else V1) + '/Textures/' + stem)
    mis, notes = [], []
    for name, m in sorted(mats2.items()):
        if not set(m['textures']) & set(changed_tex):
            continue
        mi_name = 'MI_PazFarm_' + name[len('M_PazFarm_'):]
        path = V2 + '/Materials/' + mi_name
        mi = u.load_asset(path) if EAL.does_asset_exist(path) else \
            u.AssetToolsHelpers.get_asset_tools().create_asset(mi_name, V2 + '/Materials', u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        L.set_material_instance_parent(mi, masters[m['mode']])
        for stem in m['textures']:
            kind = stem.rsplit('_', 1)[1]
            if kind in ('BaseColor', 'Normal', 'ORM'):
                t = tex(stem); assert t, stem
                L.set_material_instance_texture_parameter_value(mi, kind, t)
            else:
                notes.append('%s: extra texture %s not wired (as v1)' % (name, stem))
        L.update_material_instance(mi)
        mis.append(mi)
    assert save(mis)
    RESULT = {'ok': True, 'instances': [m.get_name() for m in mis], 'notes': notes, 'dirty': dirty()}

elif step == 'meshes':
    sms = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    out, notes = {}, []
    for name in ARGS['names']:
        f = SRC2 / 'FBX' / (name + '.fbx'); assert f.exists(), f
        path = V2 + '/Meshes/' + name
        if not EAL.does_asset_exist(path):
            ui = u.FbxImportUI()
            ui.set_editor_property('import_mesh', True); ui.set_editor_property('import_as_skeletal', False)
            ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False)
            ui.set_editor_property('import_animations', False)
            sm = ui.get_editor_property('static_mesh_import_data')
            sm.set_editor_property('combine_meshes', True); sm.set_editor_property('auto_generate_collision', False)
            sm.set_editor_property('build_nanite', True)
            t = u.AssetImportTask()
            for k, v in dict(filename=str(f), destination_path=V2 + '/Meshes', destination_name=name, automated=True, replace_existing=False, save=False, options=ui).items():
                t.set_editor_property(k, v)
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        mesh = u.load_asset(path)
        assert isinstance(mesh, u.StaticMesh), path
        nanite = None
        if name in PLANTS:                                                       # disconnected leaves: keep their area at distance
            s = mesh.get_editor_property('nanite_settings')
            s.set_editor_property('enabled', True)
            if hasattr(s, 'shape_preservation'):
                s.set_editor_property('shape_preservation', u.NaniteShapePreservation.PRESERVE_AREA)
            else:
                s.set_editor_property('preserve_area', True)
            sms.set_nanite_settings(mesh, s, True)
            nanite = {k: v for k, v in nanite_fields(mesh).items() if k in ('enabled', 'shape_preservation', 'preserve_area')}
        slots = mesh.get_editor_property('static_materials')
        bound = []
        for i, sl in enumerate(slots):
            base = str(sl.get_editor_property('material_slot_name')).split('.')[0]
            mi_name = 'MI_PazFarm_' + base[len('M_PazFarm_'):] if base.startswith('M_PazFarm_') else None
            mi = mi_name and (u.load_asset(V2 + '/Materials/' + mi_name) if EAL.does_asset_exist(V2 + '/Materials/' + mi_name)
                              else u.load_asset(V1 + '/Materials/' + mi_name))
            if mi:
                mesh.set_material(i, mi); bound.append(mi.get_path_name().split('.')[0].replace(TRIAL + '/PazFarm/', ''))
            else:
                notes.append('%s slot %d %s unmatched' % (name, i, base))
        b1, b2 = bounds(u.load_asset(V1 + '/Meshes/' + name)), bounds(mesh)
        out[name] = {'slots': bound, 'nanite': nanite, 'v1': b1, 'v2': b2,
                     'max_bound_diff_cm': max(abs(a - b) for k in ('min', 'max') for a, b in zip(b1[k], b2[k]))}
        assert save([mesh])
    rec = TASK / 'receipts' / 'PAZFARM_V002_MESHES.json'
    old = json.loads(rec.read_text()) if rec.exists() else {}
    old.update(out)
    rec.write_text(json.dumps(old, indent=2), encoding='utf-8')
    RESULT = {'ok': True, 'meshes': out, 'notes': notes, 'dirty': dirty()}

elif step == 'swap':
    s = state()
    if not BEFORE.exists():
        assert all(v['mesh'].startswith(V1 + '/Meshes/') for v in s['hism'].values()), s['hism']
        BEFORE.write_text(json.dumps({'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, **s}, indent=2), encoding='utf-8')
    hisms = detail_hisms()
    for name in PLANTS:
        c = hisms[name]
        n0 = c.get_instance_count()
        new = u.load_asset(V2 + '/Meshes/' + name); assert new, name
        actors['PazFarm_Detail'].modify(); c.modify()
        c.set_static_mesh(new)
        assert c.get_instance_count() == n0, (name, n0, c.get_instance_count())
    barn = actors['PazFarm_Barn']; bc = barn.static_mesh_component
    assert not [m for m in bc.get_editor_property('override_materials') if m], 'barn has material overrides'
    barn.modify(); bc.modify()
    bc.set_static_mesh(u.load_asset(V2 + '/Meshes/SM_PazFarm_Barn'))
    mi = u.load_asset(GROUND_MI)
    L.set_material_instance_texture_parameter_value(mi, 'FarmColor', u.load_asset(V2 + '/Textures/T_PazFarm_Ground'))
    L.update_material_instance(mi)
    g = json.loads((SRC2 / 'Georef/PLACEMENT_PATCH.json').read_text())['replace_only_gate']['after']
    gx, gy = XY(g['e'], g['n'])                                                  # centre pivot: no end offset
    gate = actors['PazFarm_Gate']; gate.modify()
    gate.set_actor_location_and_rotation(u.Vector(gx, gy, ground(gx, gy)), u.Rotator(roll=0.0, pitch=0.0, yaw=-g['dir_deg']), False, False)
    after = state()
    old_c, new_c = s['gate']['en'], after['gate']['en']
    RESULT = {'ok': True, 'before': s, 'after': after, 'gate_move_m': round(math.hypot(new_c[0] - old_c[0], new_c[1] - old_c[1]), 3), 'dirty': dirty()}

elif step == 'revert':
    b = json.loads(BEFORE.read_text())
    hisms = detail_hisms()
    for name, v in b['hism'].items():
        c = hisms[name]; actors['PazFarm_Detail'].modify(); c.modify()
        c.set_static_mesh(u.load_asset(v['mesh']))
    barn = actors['PazFarm_Barn']; barn.modify(); barn.static_mesh_component.modify()
    barn.static_mesh_component.set_static_mesh(u.load_asset(b['barn']['mesh']))
    mi = u.load_asset(GROUND_MI)
    L.set_material_instance_texture_parameter_value(mi, 'FarmColor', u.load_asset(b['ground_mi']['FarmColor'].split('.')[0]))
    L.update_material_instance(mi)
    gate = actors['PazFarm_Gate']; gate.modify(); gl = b['gate']
    gate.set_actor_location_and_rotation(u.Vector(*gl['loc']), u.Rotator(roll=gl['roll'], pitch=gl['pitch'], yaw=gl['yaw']), False, False)
    RESULT = {'ok': True, 'restored': state(), 'dirty': dirty()}

elif step == 'save':
    d = dirty()
    assert d[0] == [CLONE] or d[0] == [], d
    other = [n for n in d[1] if not n.startswith(V1 + '/')]
    assert not other, 'dirty outside the clone PazFarm folder: %s' % other
    pk = list(u.EditorLoadingAndSavingUtils.get_dirty_content_packages())
    if pk:
        assert u.EditorLoadingAndSavingUtils.save_packages(pk, False)
    assert u.EditorLoadingAndSavingUtils.save_map(world, CLONE)
    f = ROOT / ('Content' + CLONE[5:] + '.umap')
    rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'saved_content': d[1],
           'map_sha256': sha(f), 'map_bytes': f.stat().st_size, 'state': state(), 'dirty_after': dirty()}
    (TASK / 'receipts' / 'PAZFARM_V002_SAVE.json').write_text(json.dumps(rec, indent=2), encoding='utf-8')
    RESULT = {'ok': True, **rec}
