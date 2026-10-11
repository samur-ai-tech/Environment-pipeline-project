"""In-editor (Karmei Yosef operator) on the 4 km PCG clone, 2026-10-08: Paz Farm, reversible.
step 'ground_mi': MI_GeoCityGround_PazFarm (child of the 4 km area MI) in the clone folder with Farm_Blend = 1, assigned
                  to the clone's landscape only. Undo: assign the area MI back (or Farm_Blend = 0).
step 'place':     one actor 'PazFarm_Detail' (folder PazFarm) with one hierarchical instanced component per mesh: strawberry
                  beds, avocado / citrus trees, fence panels and corner posts; separate actors for the barn and the gate.
                  Positions from Staging/PazFarm_2026-10-08/Georef/PLACEMENTS.json, height from a downward trace that hits
                  only the landscape. Undo: delete the PazFarm actors.
step 'masks':     re-import the six zone masks with the farm footprint cleared, flush the PCG cache, regenerate the zone
                  vegetation (stand-ins leave the farm). Undo: re-import the original masks and regenerate.
Nothing is saved here except new assets (MI); the map is saved by pcg_finish.py. ARGS: expected_pid, step.
"""
import datetime, json, math, os
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
GEO = ROOT / 'Staging/PazFarm_2026-10-08/Georef'
TRIAL = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial'
CLONE = TRIAL + '/L_KarmeiYosef_31850349_34907601_4km_PCGTrial'
AREA_MI = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/BankIntegration_v015/Materials/MI_GeoCityGround_Auto'
MESH = TRIAL + '/PazFarm/Meshes/'
L = u.MaterialEditingLibrary
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == CLONE
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
land = [a for a in eas.get_all_level_actors() if isinstance(a, u.Landscape)]
assert len(land) == 1
land = land[0]
step = ARGS['step']
pe, pn = json.loads((GEO / 'roads.json').read_text())['pin_local_m_from_area_centre']
XY = lambda e, n: ((pe + e) * 100.0, -(pn + n) * 100.0)          # metres from pin -> Unreal cm (X east, Y south)

if step == 'ground_mi':
    path = TRIAL + '/PazFarm/Materials/MI_GeoCityGround_PazFarm'
    mi = u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else \
        u.AssetToolsHelpers.get_asset_tools().create_asset('MI_GeoCityGround_PazFarm', TRIAL + '/PazFarm/Materials', u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
    L.set_material_instance_parent(mi, u.load_asset(AREA_MI))
    L.set_material_instance_scalar_parameter_value(mi, 'Farm_Blend', 1.0)
    L.update_material_instance(mi)
    assert abs(L.get_material_instance_scalar_parameter_value(mi, 'Farm_Blend') - 1.0) < 1e-6
    assert u.EditorLoadingAndSavingUtils.save_packages([mi.get_outermost()], False)
    before = land.get_editor_property('landscape_material').get_path_name()
    land.set_editor_property('landscape_material', mi)
    RESULT = {'ok': True, 'mi': path, 'landscape_material_before': before, 'after': land.get_editor_property('landscape_material').get_path_name()}

elif step == 'place':
    assert not [a for a in eas.get_all_level_actors() if a.get_actor_label().startswith('PazFarm_')], 'PazFarm actors already placed'
    P = json.loads((GEO / 'PLACEMENTS.json').read_text())
    ignore = [a for a in eas.get_all_level_actors() if not isinstance(a, (u.Landscape, u.LandscapeProxy))]
    misses = []
    def ground(x, y):
        hit = u.SystemLibrary.line_trace_single(world, u.Vector(x, y, 60000.0), u.Vector(x, y, -20000.0),
                                                u.TraceTypeQuery.TRACE_TYPE_QUERY1, False, ignore, u.DrawDebugTrace.NONE, True)
        h = hit[1] if isinstance(hit, tuple) else hit           # UE 5.8 returns a HitResult; to_tuple()[0] = blocking hit
        t = h.to_tuple() if h is not None else None
        if not t or not t[0]:
            misses.append((x, y)); return None
        return t[4].z
    actor = eas.spawn_actor_from_class(u.Actor, u.Vector(*XY(0, 0), 0.0))
    actor.set_actor_label('PazFarm_Detail'); actor.set_folder_path('PazFarm')
    sds = u.get_engine_subsystem(u.SubobjectDataSubsystem)
    root = sds.k2_gather_subobject_data_for_instance(actor)[0]
    comps = {}
    def comp_for(mesh_name):
        if mesh_name not in comps:
            handle, fail = sds.add_new_subobject(u.AddNewSubobjectParams(parent_handle=root, new_class=u.HierarchicalInstancedStaticMeshComponent))
            c = u.SubobjectDataBlueprintFunctionLibrary.get_object(u.SubobjectDataBlueprintFunctionLibrary.get_data(handle))
            c.set_static_mesh(u.load_asset(MESH + mesh_name))
            comps[mesh_name] = c
        return comps[mesh_name]
    batches = {}
    def put(mesh_name, x, y, yaw, scale=(1.0, 1.0, 1.0)):
        z = ground(x, y)
        if z is None:
            return
        batches.setdefault(mesh_name, []).append(u.Transform(location=u.Vector(x, y, z), rotation=u.Rotator(roll=0.0, pitch=0.0, yaw=yaw), scale=u.Vector(*scale)))
    for it in P['items']:
        x, y = XY(it['e'], it['n'])
        if it['kind'] == 'strawberry_bed':
            put(it['mesh'], x, y, 90.0 - it['row_deg'])                      # bed length runs along local -Y
        else:
            s = it['scale']; put(it['mesh'], x, y, -it['row_deg'], (s, s, s))
    for seg in P['fence_segments']:
        x, y = XY(seg['e'], seg['n']); put('SM_PazFarm_Fence_Mesh_3m', x, y, -seg['dir_deg'])
    for c in P['corner_posts']:
        x, y = XY(c['e'], c['n']); put('SM_PazFarm_Fence_Post', x, y, 0.0)
    counts = {}
    for name, ts in batches.items():
        comp_for(name).add_instances(ts, False, True)
        counts[name] = len(ts)
    # barn and gate as their own actors
    b = P['barn']; bx, by = XY(b['e'], b['n'])
    barn = eas.spawn_actor_from_object(u.load_asset(MESH + b['mesh']), u.Vector(bx, by, ground(bx, by) or 0.0), u.Rotator(roll=0.0, pitch=0.0, yaw=-b['rotation_deg']))
    barn.set_actor_label('PazFarm_Barn'); barn.set_folder_path('PazFarm')
    barn.set_actor_scale3d(u.Vector(b['footprint_ew_m'] / 20.57, b['footprint_ns_m'] / 12.59, 1.0))
    g = P['gate']; d = math.radians(g['dir_deg'])
    gx, gy = XY(g['e'] + 3.0 * math.cos(d), g['n'] + 3.0 * math.sin(d))
    gate = eas.spawn_actor_from_object(u.load_asset(MESH + g['mesh']), u.Vector(gx, gy, ground(gx, gy) or 0.0), u.Rotator(roll=0.0, pitch=0.0, yaw=-g['dir_deg']))
    gate.set_actor_label('PazFarm_Gate'); gate.set_folder_path('PazFarm')
    rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'instances': counts, 'total': sum(counts.values()),
           'trace_misses': len(misses), 'barn': barn.get_path_name(), 'gate': gate.get_path_name(), 'detail_actor': actor.get_path_name()}
    (TASK / 'receipts' / 'PAZFARM_PLACE.json').write_text(json.dumps(rec, indent=2), encoding='utf-8')
    RESULT = {'ok': True, **rec}

elif step == 'masks':
    info = json.loads((GEO / 'MASKS_WITHOUT_FARM.json').read_text())
    for name, f in info['files'].items():
        t = u.AssetImportTask()
        for k, v in dict(filename=f['file'], destination_path=TRIAL + '/Masks', destination_name='T_KY4_Mask_' + name,
                         automated=True, replace_existing=True, replace_existing_settings=False, save=False).items():
            t.set_editor_property(k, v)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        tex = u.load_asset(TRIAL + '/Masks/T_KY4_Mask_' + name)
        tex.set_editor_property('srgb', False); tex.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_GRAYSCALE)
        tex.set_editor_property('mip_gen_settings', u.TextureMipGenSettings.TMGS_NO_MIPMAPS); tex.set_editor_property('filter', u.TextureFilter.TF_NEAREST)
        tex.set_editor_property('never_stream', True)
        assert u.EditorLoadingAndSavingUtils.save_packages([tex.get_outermost()], False)
    u.SystemLibrary.execute_console_command(world, 'pcg.FlushCache')
    vol = [a for a in eas.get_all_level_actors() if isinstance(a, u.PCGVolume)][0]
    comp = vol.get_component_by_class(u.PCGComponent)
    comp.cleanup_local(True)
    RESULT = {'ok': True, 'masks_replaced': list(info['files']), 'pcg': 'cleaned; run pcg_gen.py to regenerate'}
