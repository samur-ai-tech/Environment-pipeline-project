"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the Karmei Yosef tool. Zone vegetation on the PCG clone
(Aviv: zones from map data + satellite, stand-in plants; PCG vegetation for new areas: yes, RC-46). One graph, one branch
per planted zone:
  landscape Surface Sampler (branch density/spacing) -> Sample Texture (zone mask, planar over +-HALF_EXTENT_CM) ->
  Density Filter >= 0.5 (inside the zone) -> keep Dirt_Path < 0.05, Sand_Path < 0.05, Sand_02 < 0.5 (road bed, building
  pads, steep) -> Self Pruning -> Transform Points (absolute yaw 0..360, scale) -> Static Mesh Spawner (WPO off).
Masks and texture placement were verified by a probe (forest points in the south-east, on the ground).
Lessons from the 2 km trial applied: selector via import_text, Rotator keywords, absolute rotation, WPO off, flush cache.
Stand-ins (no olive/vine/crop models in the project): orchards = small broad trees on a 6 m grid, vineyards = low bushes
on a 4 m grid, crops = green grass patches. Only non-held bank rows or pack meshes outside the bank.
Creates area_constants.zones_graph('') (<trial>/PCG/PCG_<AREA_SHORT>_Zones, named save), one PCGVolume, starts generation.
Order: this graph samples the PACK ORIGINALS; trees_pcg.py 'graph' checks its first 8 branches against this graph and expects
the never-vanish copies in <clone>/Vegetation/Meshes, so run never_vanish.py (pines, copy_swap) on this graph before it.
ARGS: expected_pid, script_file (client), clone_suffix (required: '' first clone, '_v2' rebuilt clone).
"""
import datetime, importlib.util, json, os
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
TRIAL = A.TRIAL_ROOT
CLONE = A.clone_map(ARGS['clone_suffix'])                               # required, explicit
GRAPH_NAME = A.zones_graph('').rsplit('/', 1)[1]
MR = '/Game/Modular_Rural_Cabin/Meshes/Foliage/'
STF = '/Game/STF/Pack03-LandscapePro/Environment/Foliage/'
PP = '/Game/Palms_Pack_01/Add_Props/'
DES = '/Game/Project/Shared/ModelBank/Supply/desert/Meshes/'
PN = '/Game/ProceduralNtr_vol2/pnp_v2_assets/Assets/'
CREOSOTE = [DES + 'SM_Creosote_Bush_1_aa4444f6', DES + 'SM_Creosote_Bush_2_7b3523f6', DES + 'SM_Creosote_Bush_3_7d14a2df', DES + 'SM_Creosote_Bush_4_23fed412']
GRASSB = [STF + 'GrassBush/SM_grass_bush0%d_lod00' % i for i in (1, 2, 3, 4)]
BR = [  # name, mask, points/m2, half extent cm, looseness, scale range, [(mesh, weight)]
    ('forest', 'Forest', 0.008, 200, 1.0, (0.8, 1.2), [(MR + 'SM_Pine_Tree_01', 4), (MR + 'SM_Pine_Tree_02', 4), (MR + 'SM_Pine_Tree_03', 4),
                                                        (MR + 'SM_Pine_Tree_05', 3), (STF + 'GreenTrees/tree01/SM_green-tree01', 1)]),
    ('forest_shrubs', 'Forest', 0.004, 100, 1.0, (0.7, 1.2), [(PP + 'Thicket/Meshes/SM_Thicket_01_G', 2), (PP + 'Thicket/Meshes/SM_Thicket_02_G', 2),
                                                              (PN + 'eldeberry_bushes/Static_Meshes/Elderberry_Living_Medium', 2)] + [(m, 1) for m in CREOSOTE]),
    ('orchard', 'Orchard', 1.0 / 36.0, 150, 0.0, (0.45, 0.55), [(STF + 'GreenTrees/tree01/SM_green-tree01', 1), (STF + 'GreenTrees/tree02/SM_green-tree02', 1)]),
    ('vineyard', 'Vineyard', 0.0625, 60, 0.0, (0.85, 1.1), [(STF + 'Bush/SM_bush01', 2), (PN + 'eldeberry_bushes/Static_Meshes/Elderberry_Living_Medium', 1)]),
    ('scrub', 'ScrubMix', 0.008, 100, 1.0, (0.7, 1.3), [(m, 3) for m in CREOSOTE] + [(PP + 'Thicket/Meshes/SM_Thicket_01_G', 2), (PP + 'Thicket/Meshes/SM_Thicket_02_G', 2),
                                                       (PN + 'eldeberry_bushes/Static_Meshes/Elderberry_Living_Medium', 2), (STF + 'Bush/SM_bush01', 2),
                                                       (STF + 'Pines/pine-small01/SM_pine-small01', 1), (STF + 'Pines/pine-small03/SM_pine-small03', 1)]),
    ('scrub_trees', 'ScrubMix', 0.0008, 250, 1.0, (0.75, 1.2), [(MR + 'SM_Pine_Tree_03', 2), (MR + 'SM_Pine_Tree_05', 2), (STF + 'GreenTrees/tree01/SM_green-tree01', 3),
                                                               (STF + 'GreenTrees/tree02/SM_green-tree02', 3), (PP + 'Thicket/Meshes/SM_Thicket_03_G', 2)]),
    ('grass', 'Grass', 0.004, 60, 1.0, (0.7, 1.3), [(m, 3) for m in GRASSB] + [(PP + 'Plants/Meshes/SM_Plant_06_2_G', 1), (PP + 'Plants/Meshes/SM_Plant_07_2_G', 1),
                                                    (PP + 'Plants/Meshes/SM_Plant_09_3_G', 1), (CREOSOTE[0], 1)]),
    ('crop', 'Crop', 0.01, 50, 0.3, (0.7, 1.0), [(PN + 'grass/Static_Meshes/green_grass_patch_tall_01', 3), (PN + 'grass/Static_Meshes/grass_patch_01', 2),
                                                 (GRASSB[0], 1), (GRASSB[2], 1)])]
FILTERS = [('Dirt_Path', 0.05), ('Sand_Path', 0.05), ('Sand_02', 0.5)]

pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == CLONE
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
assert not [a for a in eas.get_all_level_actors() if isinstance(a, u.PCGVolume)], 'PCG volume already present'
assert not u.EditorAssetLibrary.does_asset_exist(TRIAL + '/PCG/' + GRAPH_NAME)
for b in BR:
    for path, _ in b[6]:
        assert isinstance(u.load_asset(path), u.StaticMesh), path
labels = lambda pins: [str(p.properties.label) for p in pins]
g = u.AssetToolsHelpers.get_asset_tools().create_asset(GRAPH_NAME, TRIAL + '/PCG', u.PCGGraph, u.PCGGraphFactory())
getl, gs = g.add_node_of_type(u.PCGGetLandscapeSettings)
sp = gs.get_editor_property('sampling_properties'); sp.set_editor_property('get_layer_weights', True); gs.set_editor_property('sampling_properties', sp)
out = g.get_output_node()
tex_nodes = {}
for mask in sorted({b[1] for b in BR}):
    n, s = g.add_node_of_type(u.PCGTextureSamplerSettings)
    s.set_editor_property('texture', u.load_asset(TRIAL + '/Masks/' + A.MASK_PREFIX + mask))
    s.set_editor_property('use_absolute_transform', True)
    s.set_editor_property('transform', u.Transform(location=u.Vector(0, 0, 0), rotation=u.Rotator(roll=0, pitch=0, yaw=0), scale=u.Vector(A.HALF_EXTENT_CM, A.HALF_EXTENT_CM, 1.0)))
    s.set_editor_property('filter', u.PCGTextureFilter.POINT)
    s.set_editor_property('color_channel', u.PCGTextureColorChannel.RED)
    s.set_editor_property('density_function', u.PCGTextureDensityFunction.MULTIPLY)
    tex_nodes[mask] = n
counts = {}
for name, mask, pps, ext, loose, scale, meshes in BR:
    samp, ss = g.add_node_of_type(u.PCGSurfaceSamplerSettings)
    ss.set_editor_property('points_per_squared_meter', pps); ss.set_editor_property('point_extents', u.Vector(ext, ext, 100.0))
    ss.set_editor_property('looseness', loose); ss.set_editor_property('seed', 100 + len(counts))
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
    g.add_edge(xf, 'Out', sp_n, 'In'); g.add_edge(sp_n, 'Out', out, 'Out')
    counts[name] = {'mask': mask, 'pps': pps, 'looseness': loose, 'scale': scale, 'meshes': [[p, w] for p, w in meshes]}
assert u.EditorLoadingAndSavingUtils.save_packages([g.get_outermost()], False)
land = [a for a in eas.get_all_level_actors() if isinstance(a, u.Landscape)][0]
origin, extent = land.get_actor_bounds(False)
vol = eas.spawn_actor_from_class(u.PCGVolume, origin); vol.set_actor_label(A.PCG_VOLUME_LABEL)
vol.set_actor_scale3d(u.Vector(extent.x / 100.0, extent.y / 100.0, (extent.z + 5000.0) / 100.0))
comp = vol.get_component_by_class(u.PCGComponent)
comp.set_graph(g)
comp.set_editor_property('generation_trigger', u.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
u.SystemLibrary.execute_console_command(world, 'pcg.FlushCache')
comp.generate_local(True)
record = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': pid, 'graph': TRIAL + '/PCG/' + GRAPH_NAME,
          'volume': vol.get_path_name(), 'branches': counts, 'filters_keep_lesser_than': FILTERS, 'generation_started': True,
          'bank_changes': 'none'}
(TASK / 'receipts' / 'ZONE_PCG_BUILD.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
RESULT = {'ok': True, 'graph': record['graph'], 'branches': list(counts)}
