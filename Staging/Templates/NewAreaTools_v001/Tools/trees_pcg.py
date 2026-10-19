"""In-editor on the PCG clone. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); the Karmei Yosef ky4_trees_v2.py (Aviv approved:
more trees - satellite tree map, denser forest and scrub + single field trees; playbook 7.2-7.5). Everything shared is only
READ; new packages only. Names from area_constants.py (MASK_PREFIX, zones_graph(), PCG_VOLUME_LABEL, WINDBREAKS_LABEL).
A hero site is optional: the steps crops and windbreaks run only when ARGS.site / ARGS.site_georef name one (playbook 8).
steps
  import_masks  ARGS.masks {name: png}: <clone>/Masks_v2/<MASK_PREFIX><name> (linear, grayscale, no mips, nearest, never stream)
  graph         zones_graph(ARGS.version), rebuilt like build_zone_pcg.py: same 8 branches in the same order (same seeds) on
                the _P3 masks, forest + scrub_trees on the satellite tree masks with higher density, plus sat_trees and
                field_trees; meshes = the base graph's (never-vanish copies), checked against it
  assign_graph  the clone's PCG volume -> zones_graph(ARGS.version) (old output cleaned), generation started
  crops         (site only) actor <site>_Extension (folder <site>, Static chain): HISMs for the site's CROPS_V3 trees (same
                meshes as <site>_Detail) + green-field stand-in plants; height = landscape only (first blocking hit must be
                the landscape, else the point is skipped)
  windbreaks    (site only) actor WINDBREAKS_LABEL (folder Vegetation, Static chain) from the site's WINDBREAKS_V2.json
  volume        new clone: one PCG volume (PCG_VOLUME_LABEL) over the landscape with zones_graph(ARGS.version)
  status        graph, generation state, instance counts of the placed actors, dirty packages
Undo: volume graph back to zones_graph('') and regenerate; delete the placed actors. Map saved by pcg_finish.py.
ARGS: expected_pid, script_file (client), step, clone_suffix (required), version (required, e.g. 'v002'), site,
site_georef (project-relative Georef folder of the site), site_mesh_folder (site meshes under the clone folder), ...
"""
import datetime, importlib.util, json, math, os
from collections import Counter
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
SITE = ARGS.get('site')                                                 # hero-site name (crops / labels), optional
GEO = (ROOT / ARGS['site_georef']) if ARGS.get('site_georef') else None # the site's Georef folder (crops, windbreaks only)
TRIAL = A.TRIAL_ROOT
CLONE = A.clone_map(ARGS['clone_suffix'])                               # required, explicit ('' first clone, '_v2' rebuilt)
VERSION = ARGS['version']                                              # required graph version (an old one is an unused graph)
OLD_GRAPH = A.zones_graph('')
NEW_GRAPH = A.zones_graph(VERSION)
assert NEW_GRAPH != OLD_GRAPH, 'ARGS.version must name a rebuilt graph (v002 or later)'
VF3 = (TRIAL + '/' + ARGS['site_mesh_folder'].strip('/') + '/') if ARGS.get('site_mesh_folder') else None   # site meshes
MASKS2 = TRIAL + '/Masks_v2/'
COPY = TRIAL + '/Vegetation/Meshes/'
SITE_LABELS = ((SITE + '_Extension',) if SITE else ()) + (A.WINDBREAKS_LABEL,)
PP = '/Game/Palms_Pack_01/Add_Props/'
DES = '/Game/Project/Shared/ModelBank/Supply/desert/Meshes/'
PN = '/Game/ProceduralNtr_vol2/pnp_v2_assets/Assets/'
STF = '/Game/STF/Pack03-LandscapePro/Environment/Foliage/'
CREOSOTE = [DES + 'SM_Creosote_Bush_1_aa4444f6', DES + 'SM_Creosote_Bush_2_7b3523f6', DES + 'SM_Creosote_Bush_3_7d14a2df', DES + 'SM_Creosote_Bush_4_23fed412']
GRASSB = [STF + 'GrassBush/SM_grass_bush0%d_lod00' % i for i in (1, 2, 3, 4)]
P1, P2, P3, P5 = (COPY + 'SM_Pine_Tree_0%d' % i for i in (1, 2, 3, 5))
GT1, GT2, PS1, PS3 = COPY + 'SM_green-tree01', COPY + 'SM_green-tree02', COPY + 'SM_pine-small01', COPY + 'SM_pine-small03'
BR = [  # name, mask, points/m2, half extent cm, looseness, scale, meshes   (first 8 = build_zone_pcg.py order -> same seeds)
    ('forest', 'ForestTrees', 0.033, 200, 1.0, (0.8, 1.2), [(P1, 4), (P2, 4), (P3, 4), (P5, 3), (GT1, 1)]),
    ('forest_shrubs', 'Forest_P3', 0.004, 100, 1.0, (0.7, 1.2), [(PP + 'Thicket/Meshes/SM_Thicket_01_G', 2), (PP + 'Thicket/Meshes/SM_Thicket_02_G', 2),
                                                                (PN + 'eldeberry_bushes/Static_Meshes/Elderberry_Living_Medium', 2)] + [(m, 1) for m in CREOSOTE]),
    ('orchard', 'Orchard_P3', 1.0 / 36.0, 150, 0.0, (0.45, 0.55), [(GT1, 1), (GT2, 1)]),
    ('vineyard', 'Vineyard_P3', 0.0625, 60, 0.0, (0.85, 1.1), [(STF + 'Bush/SM_bush01', 2), (PN + 'eldeberry_bushes/Static_Meshes/Elderberry_Living_Medium', 1)]),
    ('scrub', 'ScrubMix_P3', 0.008, 100, 1.0, (0.7, 1.3), [(m, 3) for m in CREOSOTE] + [(PP + 'Thicket/Meshes/SM_Thicket_01_G', 2), (PP + 'Thicket/Meshes/SM_Thicket_02_G', 2),
                                                          (PN + 'eldeberry_bushes/Static_Meshes/Elderberry_Living_Medium', 2), (STF + 'Bush/SM_bush01', 2), (PS1, 1), (PS3, 1)]),
    ('scrub_trees', 'ScrubTrees', 0.0086, 250, 1.0, (0.75, 1.2), [(P3, 2), (P5, 2), (GT1, 3), (GT2, 3), (PP + 'Thicket/Meshes/SM_Thicket_03_G', 2)]),
    ('grass', 'Grass_P3', 0.004, 60, 1.0, (0.7, 1.3), [(m, 3) for m in GRASSB] + [(PP + 'Plants/Meshes/SM_Plant_06_2_G', 1), (PP + 'Plants/Meshes/SM_Plant_07_2_G', 1),
                                                       (PP + 'Plants/Meshes/SM_Plant_09_3_G', 1), (CREOSOTE[0], 1)]),
    ('crop', 'Crop_P3', 0.01, 50, 0.3, (0.7, 1.0), [(PN + 'grass/Static_Meshes/green_grass_patch_tall_01', 3), (PN + 'grass/Static_Meshes/grass_patch_01', 2),
                                                    (GRASSB[0], 1), (GRASSB[2], 1)]),
    ('sat_trees', 'SatTrees', 0.012, 250, 1.0, (0.8, 1.2), [(GT1, 3), (GT2, 3), (P3, 1), (P5, 1)]),
    ('field_trees', 'OpenField', 0.00006, 400, 1.0, (0.85, 1.25), [(GT1, 1), (GT2, 1)]),
]
OLD_MASK = {'forest': 'Forest', 'scrub_trees': 'ScrubMix'}          # the two branches whose mask/density change on purpose
FILTERS = [('Dirt_Path', 0.05), ('Sand_Path', 0.05), ('Sand_02', 0.5)]
GREEN_STANDINS = [PN + 'grass/Static_Meshes/green_grass_patch_tall_01', PN + 'grass/Static_Meshes/grass_patch_01']
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == CLONE
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
step = ARGS['step']
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
if GEO is not None:                                                    # site pin (metres from the area centre)
    pe, pn = json.loads((GEO / 'roads.json').read_text())['pin_local_m_from_area_centre']
    XY = lambda e, n: ((pe + e) * 100.0, -(pn + n) * 100.0)
vols = [a for a in eas.get_all_level_actors() if isinstance(a, u.PCGVolume)]


def spawner_sets(g):
    out = []
    for node in g.get_editor_property('nodes'):
        s = node.get_settings()
        if isinstance(s, u.PCGStaticMeshSpawnerSettings):
            sel = s.get_editor_property('mesh_selector_parameters')
            out.append(sorted((e.get_editor_property('descriptor').get_editor_property('static_mesh').get_path_name().split('.')[0],
                               int(e.get_editor_property('weight'))) for e in sel.get_editor_property('mesh_entries')))
    return out


def static_actor(label, folder, at):
    assert not [a for a in eas.get_all_level_actors() if a.get_actor_label() == label], label + ' exists'
    actor = eas.spawn_actor_from_class(u.Actor, at)
    actor.set_actor_label(label); actor.set_folder_path(folder)
    sds = u.get_engine_subsystem(u.SubobjectDataSubsystem)
    top = sds.k2_gather_subobject_data_for_instance(actor)[0]
    h, _ = sds.add_new_subobject(u.AddNewSubobjectParams(parent_handle=top, new_class=u.SceneComponent))
    root = u.SubobjectDataBlueprintFunctionLibrary.get_object(u.SubobjectDataBlueprintFunctionLibrary.get_data(h))
    root.set_mobility(u.ComponentMobility.STATIC)
    comps = {}

    def comp_for(mesh):
        key = mesh.get_path_name()
        if key not in comps:
            hh, _ = sds.add_new_subobject(u.AddNewSubobjectParams(parent_handle=h, new_class=u.HierarchicalInstancedStaticMeshComponent))
            c = u.SubobjectDataBlueprintFunctionLibrary.get_object(u.SubobjectDataBlueprintFunctionLibrary.get_data(hh))
            c.set_mobility(u.ComponentMobility.STATIC)
            c.set_static_mesh(mesh)
            if c.get_attach_parent() is None:
                c.attach_to_component(root, '', u.AttachmentRule.KEEP_RELATIVE, u.AttachmentRule.KEEP_RELATIVE, u.AttachmentRule.KEEP_RELATIVE, False)
            comps[key] = c
        return comps[key]
    return actor, root, comp_for, comps


misses = Counter()


def ground(x, y):
    hit = u.SystemLibrary.line_trace_single(world, u.Vector(x, y, 60000.0), u.Vector(x, y, -20000.0),
                                            u.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], u.DrawDebugTrace.NONE, True)
    h = hit[1] if isinstance(hit, tuple) else hit
    t = h.to_tuple() if h is not None else None
    if not t or not t[0]:
        misses['no_hit'] += 1; return None
    act = t[9] if len(t) > 9 else None
    if act is None or not isinstance(act, (u.Landscape, u.LandscapeProxy)):
        misses['not_landscape:' + (act.get_class().get_name() if act else 'None')] += 1; return None
    return t[4].z


if step == 'import_masks':
    out = {}
    for name, png in ARGS['masks'].items():
        dst = MASKS2 + A.MASK_PREFIX + name
        assert not u.EditorAssetLibrary.does_asset_exist(dst), dst
        t = u.AssetImportTask()
        for k, v in dict(filename=png, destination_path=MASKS2.rstrip('/'), destination_name=A.MASK_PREFIX + name, automated=True,
                         replace_existing=False, save=False).items():
            t.set_editor_property(k, v)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        tex = u.load_asset(dst)
        tex.set_editor_property('srgb', False); tex.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_GRAYSCALE)
        tex.set_editor_property('mip_gen_settings', u.TextureMipGenSettings.TMGS_NO_MIPMAPS); tex.set_editor_property('filter', u.TextureFilter.TF_NEAREST)
        tex.set_editor_property('never_stream', True)
        assert u.EditorLoadingAndSavingUtils.save_packages([tex.get_outermost()], False)
        out[name] = dst
    RESULT = {'ok': True, 'imported': out, 'dirty': dirty()}

elif step == 'graph':
    assert not u.EditorAssetLibrary.does_asset_exist(NEW_GRAPH)
    old_sets = spawner_sets(u.load_asset(OLD_GRAPH))
    for name, mask, pps, ext, loose, scale, meshes in BR[:8]:
        want = sorted((p, w) for p, w in meshes)
        assert want in old_sets, ('mesh set differs from the current graph', name, want)
    for b in BR:
        for path, _ in b[6]:
            assert isinstance(u.load_asset(path), u.StaticMesh), path
        assert u.EditorAssetLibrary.does_asset_exist(MASKS2 + A.MASK_PREFIX + b[1]), b[1]
    assert not ARGS.get('pine_map') or VF3, 'ARGS.pine_map needs ARGS.site_mesh_folder'
    pmap = {COPY + k: VF3 + v for k, v in ARGS.get('pine_map', {}).items()}      # e.g. {'SM_Pine_Tree_01': '<site pine mesh>'}
    if pmap:
        subst = []
        for b in BR:
            merged = {}
            for path, w in b[6]:
                q = pmap.get(path, path); merged[q] = merged.get(q, 0) + w
            subst.append(b[:6] + (list(merged.items()),))
        BR[:] = subst
        for b in BR:
            for path, _ in b[6]:
                assert isinstance(u.load_asset(path), u.StaticMesh), path
    g = u.AssetToolsHelpers.get_asset_tools().create_asset(NEW_GRAPH.rsplit('/', 1)[1], NEW_GRAPH.rsplit('/', 1)[0], u.PCGGraph, u.PCGGraphFactory())
    getl, gs = g.add_node_of_type(u.PCGGetLandscapeSettings)
    sp = gs.get_editor_property('sampling_properties'); sp.set_editor_property('get_layer_weights', True); gs.set_editor_property('sampling_properties', sp)
    out_node = g.get_output_node()
    tex_nodes = {}
    for mask in sorted({b[1] for b in BR}):
        n, s = g.add_node_of_type(u.PCGTextureSamplerSettings)
        s.set_editor_property('texture', u.load_asset(MASKS2 + A.MASK_PREFIX + mask))
        s.set_editor_property('use_absolute_transform', True)
        s.set_editor_property('transform', u.Transform(location=u.Vector(0, 0, 0), rotation=u.Rotator(roll=0, pitch=0, yaw=0), scale=u.Vector(A.HALF_EXTENT_CM, A.HALF_EXTENT_CM, 1.0)))
        s.set_editor_property('filter', u.PCGTextureFilter.POINT)
        s.set_editor_property('color_channel', u.PCGTextureColorChannel.RED)
        s.set_editor_property('density_function', u.PCGTextureDensityFunction.MULTIPLY)
        tex_nodes[mask] = n
    counts = {}
    for idx, (name, mask, pps, ext, loose, scale, meshes) in enumerate(BR):
        samp, ss = g.add_node_of_type(u.PCGSurfaceSamplerSettings)
        ss.set_editor_property('points_per_squared_meter', pps); ss.set_editor_property('point_extents', u.Vector(ext, ext, 100.0))
        ss.set_editor_property('looseness', loose); ss.set_editor_property('seed', 100 + idx)
        g.add_edge(getl, 'Out', samp, 'Surface')
        st, sts = g.add_node_of_type(u.PCGSampleTextureSettings)
        sts.set_editor_property('texture_mapping_method', u.PCGTextureMappingMethod.PLANAR)
        g.add_edge(samp, 'Out', st, 'Point'); g.add_edge(tex_nodes[mask], 'Out', st, 'BaseTexture')
        df, dfs = g.add_node_of_type(u.PCGDensityFilterSettings)
        dfs.set_editor_property('lower_bound', 0.5); dfs.set_editor_property('upper_bound', 1.0)
        g.add_edge(st, 'Out', df, 'In')
        prev, prev_out = df, 'Out'
        for attr, thr in FILTERS:
            n, fs = g.add_node_of_type(u.PCGAttributeFilteringSettings)
            fs.set_editor_property('operator', u.PCGAttributeFilterOperator.LESSER)
            sel = fs.get_editor_property('target_attribute'); sel.import_text('(Selection=Attribute,AttributeName="%s")' % attr)
            fs.set_editor_property('target_attribute', sel)
            assert str(fs.get_editor_property('target_attribute').get_attribute_name()) == attr
            fs.set_editor_property('use_constant_threshold', True)
            c = fs.get_editor_property('attribute_types'); c.set_editor_property('type', u.PCGMetadataTypes.FLOAT); c.set_editor_property('float_value', thr)
            fs.set_editor_property('attribute_types', c)
            g.add_edge(prev, prev_out, n, 'In'); prev, prev_out = n, 'InsideFilter'
        pr, ps = g.add_node_of_type(u.PCGSelfPruningSettings)
        params = ps.get_editor_property('parameters'); params.set_editor_property('pruning_type', u.PCGSelfPruningType.LARGE_TO_SMALL)
        params.set_editor_property('randomized_pruning', True); ps.set_editor_property('parameters', params)
        g.add_edge(prev, prev_out, pr, 'In')
        xf, xs = g.add_node_of_type(u.PCGTransformPointsSettings)
        xs.set_editor_property('absolute_rotation', True)
        xs.set_editor_property('rotation_min', u.Rotator(roll=0.0, pitch=0.0, yaw=0.0)); xs.set_editor_property('rotation_max', u.Rotator(roll=0.0, pitch=0.0, yaw=360.0))
        xs.set_editor_property('uniform_scale', True)
        xs.set_editor_property('scale_min', u.Vector(scale[0], scale[0], scale[0])); xs.set_editor_property('scale_max', u.Vector(scale[1], scale[1], scale[1]))
        g.add_edge(pr, 'Out', xf, 'In')
        sp_n, sms = g.add_node_of_type(u.PCGStaticMeshSpawnerSettings)
        sms.set_mesh_selector_type(u.PCGMeshSelectorWeighted)
        selector = sms.get_editor_property('mesh_selector_parameters')
        entries = []
        for path, w in meshes:
            e = u.PCGMeshSelectorWeightedEntry(); d = e.get_editor_property('descriptor')
            d.set_editor_property('static_mesh', u.load_asset(path)); d.set_editor_property('evaluate_world_position_offset', False)
            e.set_editor_property('descriptor', d); e.set_editor_property('weight', w); entries.append(e)
        selector.set_editor_property('mesh_entries', entries)
        g.add_edge(xf, 'Out', sp_n, 'In'); g.add_edge(sp_n, 'Out', out_node, 'Out')
        counts[name] = {'mask': mask, 'pps': pps, 'seed': 100 + idx, 'meshes': [[p.rsplit('/', 1)[1], w] for p, w in meshes]}
    assert u.EditorLoadingAndSavingUtils.save_packages([g.get_outermost()], False)
    rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'graph': NEW_GRAPH, 'branches': counts,
           'meshes_checked_against': OLD_GRAPH, 'filters_keep_lesser_than': FILTERS}
    (TASK / 'receipts' / ('ZONE_PCG_%s_BUILD.json' % VERSION.upper())).write_text(json.dumps(rec, indent=2), encoding='utf-8')
    RESULT = {'ok': True, **rec, 'dirty': dirty()}

elif step == 'assign_graph':
    assert len(vols) == 1
    comp = vols[0].get_component_by_class(u.PCGComponent)
    before = comp.get_editor_property('graph_instance').get_editor_property('graph').get_path_name() if comp.get_editor_property('graph_instance') else None
    comp.cleanup_local(True)
    comp.set_graph(u.load_asset(NEW_GRAPH))
    u.SystemLibrary.execute_console_command(world, 'pcg.FlushCache')
    comp.generate_local(True)
    RESULT = {'ok': True, 'graph_before': before, 'graph_after': NEW_GRAPH, 'generation_started': True}

elif step == 'crops':
    assert SITE and GEO is not None, 'crops needs a hero site: ARGS.site and ARGS.site_georef'
    C = json.loads((GEO / 'CROPS_V3.json').read_text())
    detail = [a for a in eas.get_all_level_actors() if a.get_actor_label() == SITE + '_Detail'][0]
    farm_meshes = {}
    for c in detail.get_components_by_class(u.HierarchicalInstancedStaticMeshComponent):
        m = c.get_editor_property('static_mesh')
        if m:
            farm_meshes[m.get_name()] = m

    def farm_mesh(base):
        hits = [m for n, m in farm_meshes.items() if n == base] or [m for n, m in farm_meshes.items() if n.startswith(base)]
        assert hits, (base, sorted(farm_meshes))
        return hits[0]
    actor, root, comp_for, comps = static_actor(SITE + '_Extension', SITE, u.Vector(*XY(0, 0), 0.0))
    batches = {}
    for t in C['trees']:
        x, y = XY(t['e'], t['n']); z = ground(x, y)
        if z is None:
            continue
        s = t['scale']
        batches.setdefault(farm_mesh(t['mesh']).get_path_name(), []).append(u.Transform(location=u.Vector(x, y, z), rotation=u.Rotator(roll=0.0, pitch=0.0, yaw=t['yaw_deg']), scale=u.Vector(s, s, s)))
    green = [u.load_asset(p) for p in GREEN_STANDINS]
    for k, (e, n, yaw, s) in enumerate(C['green_plants']):
        x, y = XY(e, n); z = ground(x, y)
        if z is None:
            continue
        batches.setdefault(green[k % 2].get_path_name(), []).append(u.Transform(location=u.Vector(x, y, z), rotation=u.Rotator(roll=0.0, pitch=0.0, yaw=yaw), scale=u.Vector(s, s, s)))
    counts = {}
    for path, ts in batches.items():
        comp_for(u.load_asset(path)).add_instances(ts, False, True); counts[path.split('.')[0].rsplit('/', 1)[1]] = len(ts)
    rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actor': actor.get_path_name(), 'instances': counts,
           'total': sum(counts.values()), 'skipped': dict(misses), 'root_mobility': str(root.get_editor_property('mobility')),
           'detached': sum(1 for c in comps.values() if c.get_attach_parent() is None)}
    (TASK / 'receipts' / (SITE.upper() + '_EXTENSION_PLACE.json')).write_text(json.dumps(rec, indent=2), encoding='utf-8')
    RESULT = {'ok': True, **rec}

elif step == 'windbreaks':
    assert GEO is not None, 'windbreaks needs a hero site: ARGS.site_georef (its WINDBREAKS_V2.json)'
    W = json.loads((GEO / 'WINDBREAKS_V2.json').read_text())
    assert VF3 or not any(t['mesh'].startswith('VF3:') for t in W['trees']), 'site meshes (VF3:) need ARGS.site_mesh_folder'
    actor, root, comp_for, comps = static_actor(A.WINDBREAKS_LABEL, 'Vegetation', u.Vector(*XY(0, 0), 0.0))
    batches = {}
    for t in W['trees']:
        x, y = XY(t['e'], t['n']); z = ground(x, y)
        if z is None:
            continue
        s = t['scale']
        batches.setdefault((VF3 + t['mesh'][4:]) if t['mesh'].startswith('VF3:') else (COPY + t['mesh']), []).append(u.Transform(location=u.Vector(x, y, z), rotation=u.Rotator(roll=0.0, pitch=0.0, yaw=t['yaw_deg']), scale=u.Vector(s, s, s)))
    counts = {}
    for path, ts in batches.items():
        comp_for(u.load_asset(path)).add_instances(ts, False, True); counts[path.rsplit('/', 1)[1]] = len(ts)
    rec = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actor': actor.get_path_name(), 'instances': counts,
           'total': sum(counts.values()), 'skipped': dict(misses), 'detached': sum(1 for c in comps.values() if c.get_attach_parent() is None)}
    (TASK / 'receipts' / 'WINDBREAKS_PLACE.json').write_text(json.dumps(rec, indent=2), encoding='utf-8')
    RESULT = {'ok': True, **rec}

elif step == 'make_static':
    # HLOD builders take only Static components and a Static part under a Movable parent loses its attachment on save:
    # whole chain Static top-down (actor root first), then re-attach anything detached (keep relative = identity here)
    out = {}
    for lab in SITE_LABELS:
        found = [x for x in eas.get_all_level_actors() if x.get_actor_label() == lab]
        if not found:
            continue                                   # not placed in this area
        a = found[0]
        a.modify()
        rootc = a.root_component
        comps = [rootc] + [c for c in a.get_components_by_class(u.SceneComponent) if c != rootc]
        for c in comps:
            if c is not None and not isinstance(c, u.BillboardComponent):
                c.modify(); c.set_mobility(u.ComponentMobility.STATIC)
        re = 0
        for c in comps[1:]:
            if c.get_attach_parent() is None:
                c.attach_to_component(rootc, '', u.AttachmentRule.KEEP_RELATIVE, u.AttachmentRule.KEEP_RELATIVE, u.AttachmentRule.KEEP_RELATIVE, False); re += 1
        out[lab] = {'root': rootc.get_name(), 'components': len(comps), 'reattached': re,
                    'mobility': sorted({str(c.get_editor_property('mobility')).split('.')[-1].split(':')[0] for c in comps}),
                    'detached': sum(1 for c in comps[1:] if c.get_attach_parent() is None)}
    RESULT = {'ok': True, **out}

elif step == 'remove_placed':
    gone = []
    for lab in ARGS.get('labels', list(SITE_LABELS)):
        for a in [x for x in eas.get_all_level_actors() if x.get_actor_label() == lab]:
            eas.destroy_actor(a); gone.append(lab)
    RESULT = {'ok': True, 'removed': gone, 'dirty': dirty()}

elif step == 'reimport_masks':
    out = {}
    for name, png in ARGS['masks'].items():
        dst = MASKS2 + A.MASK_PREFIX + name
        assert u.EditorAssetLibrary.does_asset_exist(dst), dst
        t = u.AssetImportTask()
        for k, v in dict(filename=png, destination_path=MASKS2.rstrip('/'), destination_name=A.MASK_PREFIX + name, automated=True,
                         replace_existing=True, replace_existing_settings=False, save=False).items():
            t.set_editor_property(k, v)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        tex = u.load_asset(dst)
        assert not tex.get_editor_property('srgb') and tex.get_editor_property('filter') == u.TextureFilter.TF_NEAREST, name
        assert u.EditorLoadingAndSavingUtils.save_packages([tex.get_outermost()], False)
        out[name] = dst
    RESULT = {'ok': True, 'reimported': out, 'dirty': dirty()}

elif step == 'volume':
    # new clone (after the v002 regeneration): one PCG volume over the landscape with the given graph version, generation started
    assert not vols, 'PCG volume already present'
    land = [a for a in eas.get_all_level_actors() if isinstance(a, u.Landscape)]
    assert len(land) == 1
    origin, extent = land[0].get_actor_bounds(False)
    vol = eas.spawn_actor_from_class(u.PCGVolume, origin); vol.set_actor_label(A.PCG_VOLUME_LABEL)
    vol.set_actor_scale3d(u.Vector(extent.x / 100.0, extent.y / 100.0, (extent.z + 5000.0) / 100.0))
    comp = vol.get_component_by_class(u.PCGComponent)
    comp.set_graph(u.load_asset(NEW_GRAPH))
    comp.set_editor_property('generation_trigger', u.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
    u.SystemLibrary.execute_console_command(world, 'pcg.FlushCache')
    comp.generate_local(True)
    RESULT = {'ok': True, 'volume': vol.get_path_name(), 'graph': NEW_GRAPH, 'generation_started': True}

elif step == 'status':
    out = {'dirty': dirty()}
    if vols:
        comp = vols[0].get_component_by_class(u.PCGComponent)
        gi = comp.get_editor_property('graph_instance')
        out['graph'] = gi.get_editor_property('graph').get_path_name() if gi else None
        out['generated'] = comp.get_editor_property('generated'); out['in_progress'] = comp.get_editor_property('generation_in_progress')
        pm = Counter()
        for c in vols[0].get_components_by_class(u.InstancedStaticMeshComponent):
            m = c.get_editor_property('static_mesh'); pm[m.get_name() if m else None] += c.get_instance_count()
        out['pcg_instances'] = sum(pm.values()); out['pcg_per_mesh'] = dict(pm)
    for lab in SITE_LABELS + ((SITE + '_Detail',) if SITE else ()):
        a = [x for x in eas.get_all_level_actors() if x.get_actor_label() == lab]
        if a:
            cs = a[0].get_components_by_class(u.InstancedStaticMeshComponent)
            out[lab] = {'instances': sum(c.get_instance_count() for c in cs), 'components': len(cs),
                        'mobility': sorted({str(c.get_editor_property('mobility')).split('.')[-1].split(':')[0] for c in cs}),
                        'detached': sum(1 for c in cs if c.get_attach_parent() is None)}
    RESULT = {'ok': True, **out}
