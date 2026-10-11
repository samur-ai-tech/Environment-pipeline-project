"""In-editor (Karmei Yosef operator, WP/per-building trial stage B, 2026-10-10) on the converted map
/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/L_KarmeiYosef_31850349_34907601_4km_WPTrial_WP.
steps (ARGS.step):
  probe   read-only: World Partition present, actor descriptors vs loaded actors, external-actor setting (can it be turned
          off?), landscape proxies, HLOD layers in use, spatial-loading flags per actor group.
  hlod    create HLOD layers in <trial>/HLOD: HL_Vegetation (Instancing, NOT spatially loaded = always loaded, Nanite allowed,
          every instance filter 0) and HL_Buildings (Instancing, spatially loaded); assign: PCG volume + PazFarm_Detail ->
          HL_Vegetation; Bldg_* -> HL_Buildings; 4 km-wide actors (bank props, roads, sidewalks, sky) -> not spatially loaded.
          PCG component -> partitioned (regenerate with step pcg).
  pcg     flush the PCG cache, clean up and regenerate the (partitioned) zone volume.
  status  PCG state and counts of partition actors / instances. Read-only.
No save here (wptrial_save.py). ARGS: expected_pid, step.
"""
import json, os
from collections import Counter
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TRIAL = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial'
WPMAP = TRIAL + '/L_KarmeiYosef_31850349_34907601_4km_WPTrial_WP'
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == WPMAP, world.get_outermost().get_path_name()
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
step = ARGS['step']
actors = eas.get_all_level_actors()


def group(a):
    lab = a.get_actor_label(); cls = a.get_class().get_name()
    if lab.startswith('Bldg_'):
        return 'building'
    if lab.startswith('bank_instances'):
        return 'bank_props'
    if lab.startswith('PazFarm_'):
        return 'pazfarm'
    if cls in ('PCGVolume',) or cls.startswith('PCG'):
        return cls
    if 'Landscape' in cls:
        return cls
    if lab.endswith(('_road_surfaces', '_sidewalks')):
        return 'road_mesh'
    return cls


if step == 'probe':
    out = {'loaded_actors': len(actors), 'groups': dict(Counter(group(a) for a in actors))}
    try:
        descs = u.WorldPartitionBlueprintLibrary.get_actor_descs()
        out['actor_descs'] = len(descs)
        out['desc_classes'] = dict(Counter(str(d.get_editor_property('native_class')).split('.')[-1][:40] for d in descs).most_common(15))
    except Exception as e:
        out['descs_err'] = repr(e)[:200]
    lvl = world.get_editor_property('persistent_level') if hasattr(world, 'persistent_level') else None
    try:
        lvl = world.persistent_level
    except Exception:
        pass
    out['level_ext_methods'] = [n for n in dir(lvl) if 'xternal' in n] if lvl else None
    ws = world.get_world_settings()
    out['ws_props'] = [n for n in dir(ws) if any(k in n.lower() for k in ('partition', 'external', 'hlod'))][:30]
    flags = Counter()
    for a in actors:
        try:
            flags[(group(a), bool(a.get_editor_property('is_spatially_loaded')))] += 1
        except Exception:
            flags[(group(a), 'n/a')] += 1
    out['spatially_loaded'] = {'%s:%s' % k: v for k, v in flags.items()}
    hl = Counter()
    for a in actors:
        try:
            l = a.get_editor_property('hlod_layer'); hl[l.get_name() if l else None] += 1
        except Exception:
            pass
    out['hlod_layers'] = dict(hl)
    RESULT = {'ok': True, **out}

elif step in ('load_all', 'unload_all'):
    import time
    descs = u.WorldPartitionBlueprintLibrary.get_actor_descs()
    guids = [d.get_editor_property('guid') for d in descs]
    t0 = time.time()
    if step == 'load_all':
        r = u.WorldPartitionBlueprintLibrary.load_actors(guids)
    else:
        r = u.WorldPartitionBlueprintLibrary.unload_actors(guids)
    secs = round(time.time() - t0, 1)
    now = eas.get_all_level_actors()
    RESULT = {'ok': True, 'step': step, 'descs': len(guids), 'result': str(r)[:80], 'seconds': secs, 'loaded_actors': len(now),
              'groups': dict(Counter(group(a) for a in now))}

elif step == 'hlod':
    at = u.AssetToolsHelpers.get_asset_tools()
    def layer(name, spatial):
        path = TRIAL + '/HLOD/' + name
        l = u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else at.create_asset(name, TRIAL + '/HLOD', u.HLODLayer, u.HLODLayerFactory())
        l.set_editor_property('layer_type', u.HLODLayerType.INSTANCING)
        l.set_editor_property('is_spatially_loaded', bool(spatial))
        bs = l.get_editor_property('hlod_builder_settings')
        info = {'builder_settings_class': bs.get_class().get_name() if bs else None, 'spatial': bool(l.get_editor_property('is_spatially_loaded')),
                'type': str(l.get_editor_property('layer_type'))}
        if bs:
            bs.set_editor_property('disallow_nanite', False)
            for p in ('minimum_area', 'minimum_extent', 'minimum_volume'):
                bs.set_editor_property(p, 0.0)
            ift = getattr(u, 'InstanceFilteringType', None)
            if ift is not None and hasattr(ift, 'NONE'):
                bs.set_editor_property('instance_filtering_type', ift.NONE)
            info.update({p: str(bs.get_editor_property(p)) for p in ('disallow_nanite', 'instance_filtering_type', 'minimum_area', 'minimum_extent', 'minimum_volume')})
        return l, info
    veg, vinfo = layer('HL_Vegetation', False)
    bld, binfo = layer('HL_Buildings', True)
    n = Counter()
    for a in actors:
        g = group(a)
        try:
            if g in ('PCGVolume', 'pazfarm'):
                a.set_editor_property('hlod_layer', veg); n['veg'] += 1
            elif g == 'building':
                a.set_editor_property('hlod_layer', bld); n['bld'] += 1
            elif g in ('bank_props', 'road_mesh', 'BP_EnvironmentSky_C', 'StaticMeshActor'):
                a.set_editor_property('is_spatially_loaded', False); n['always_loaded'] += 1
        except Exception as e:
            n['err:' + g + ':' + repr(e)[:50]] += 1
    vol = [a for a in actors if isinstance(a, u.PCGVolume)]
    pc = None
    if vol:
        c = vol[0].get_component_by_class(u.PCGComponent)
        c.set_editor_property('is_component_partitioned', True); pc = bool(c.get_editor_property('is_component_partitioned'))
    RESULT = {'ok': True, 'veg_layer': vinfo, 'bld_layer': binfo, 'assigned': dict(n), 'pcg_partitioned': pc}

elif step == 'pcg':
    vol = [a for a in actors if isinstance(a, u.PCGVolume)][0]
    c = vol.get_component_by_class(u.PCGComponent)
    u.SystemLibrary.execute_console_command(world, 'pcg.FlushCache')
    c.cleanup_local(True)
    c.generate_local(True)
    RESULT = {'ok': True, 'partitioned': bool(c.get_editor_property('is_component_partitioned'))}

elif step == 'use_converter_layers':
    # The converter's RuntimeHashSet only builds HLODs for layers listed in its partition HLOD setups: its own two layers
    # (..._HLODLayer_Instanced, ..._HLODLayer_Merged). Python cannot edit those setups, so reuse the two layer assets:
    # 'Merged' asset -> reconfigured as Instancing (Nanite allowed, no instance filtering) for vegetation + landscape,
    # 'Instanced' asset -> buildings. Which setup is persistent (always loaded) is read back from the built HLOD actors.
    base = TRIAL + '/L_KarmeiYosef_31850349_34907601_4km_WPTrial_HLODLayer_'
    li, lm = u.load_asset(base + 'Instanced'), u.load_asset(base + 'Merged')
    info = {}
    for name, l in (('Instanced', li), ('Merged', lm)):
        info[name + '_before'] = {p: str(l.get_editor_property(p))[:90] for p in ('layer_type', 'is_spatially_loaded', 'parent_layer', 'cell_size', 'loading_range')}
    lm.set_editor_property('layer_type', u.HLODLayerType.INSTANCING)
    for l in (li, lm):
        bs = l.get_editor_property('hlod_builder_settings')
        if bs and bs.get_class().get_name() == 'HLODBuilderInstancingSettings':
            bs.set_editor_property('disallow_nanite', False)
            for p in ('minimum_area', 'minimum_extent', 'minimum_volume'):
                bs.set_editor_property(p, 0.0)
            bs.set_editor_property('instance_filtering_type', u.InstanceFilteringType.FILTER_NONE)
        l.set_editor_property('editor_loading_behavior', u.HLODLayerEditorLoadingBehavior.FORCE_LOADED)
    for name, l in (('Instanced', li), ('Merged', lm)):
        info[name + '_after'] = {p: str(l.get_editor_property(p))[:90] for p in ('layer_type', 'is_spatially_loaded', 'parent_layer')}
    n = Counter()
    for a in actors:
        g = group(a); cls = a.get_class().get_name()
        if g in ('PCGVolume', 'pazfarm') or cls.startswith('PCGPartitionActor') or cls == 'LandscapeStreamingProxy':
            a.set_editor_property('hlod_layer', lm); n['veg_landscape->Merged(instancing)'] += 1
        elif g == 'building':
            a.set_editor_property('hlod_layer', li); n['buildings->Instanced'] += 1
    RESULT = {'ok': True, 'layers': info, 'assigned': dict(n)}

elif step == 'farm_static':
    # HLOD builders take only Static components; PazFarm_Detail's HISMs were created Movable (subobject default), so its 1,192
    # trees, beds and fence were missing from the HLOD. Static chain top-down (root first), then the HISMs.
    out = {}
    for a in actors:
        if not a.get_actor_label().startswith('PazFarm_'):
            continue
        a.modify()
        comps = [a.root_component] + [c for c in a.get_components_by_class(u.SceneComponent) if c != a.root_component]
        n = 0
        for c in comps:
            if c is not None and not isinstance(c, u.BillboardComponent):
                c.modify(); c.set_mobility(u.ComponentMobility.STATIC); n += 1
        out[a.get_actor_label()] = {'components': n, 'mobility': sorted({str(c.get_editor_property('mobility')).split('.')[-1].split(':')[0] for c in comps if c is not None and not isinstance(c, u.BillboardComponent)}),
                                    'detached': sum(1 for c in comps[1:] if c is not None and c.get_attach_parent() is None and not isinstance(c, u.BillboardComponent))}
    RESULT = {'ok': True, 'farm': out}

elif step == 'editor_default':
    base = TRIAL + '/L_KarmeiYosef_31850349_34907601_4km_WPTrial_HLODLayer_'
    out = {}
    for n in ('Instanced', 'Merged'):
        l = u.load_asset(base + n)
        l.set_editor_property('editor_loading_behavior', u.HLODLayerEditorLoadingBehavior.DEFAULT)
        out[n] = str(l.get_editor_property('editor_loading_behavior'))
    RESULT = {'ok': True, **out}

elif step == 'landscape_always_loaded':
    # Aviv 2026-10-10: ground looked low quality = the landscape HLOD stand-in (simplified mesh + one baked texture) shown for
    # every unloaded region. For a 4 km area keep all landscape streaming proxies always loaded (full material everywhere)
    # and drop their HLOD layer, so no landscape stand-ins are built.
    descs = [d for d in u.WorldPartitionBlueprintLibrary.get_actor_descs() if 'LandscapeStreamingProxy' in str(d.get_editor_property('native_class'))]
    u.WorldPartitionBlueprintLibrary.load_actors([d.get_editor_property('guid') for d in descs])
    n = 0
    for a in eas.get_all_level_actors():
        if a.get_class().get_name() == 'LandscapeStreamingProxy':
            a.modify()
            a.set_editor_property('is_spatially_loaded', False)
            a.set_editor_property('hlod_layer', None)
            n += 1
    RESULT = {'ok': True, 'proxies_always_loaded': n}

elif step == 'veg_lowest_lod':
    # Aviv 2026-10-10: far trees use their LOWEST LOD -> Nanite disallowed in the always-loaded vegetation/landscape layer
    l = u.load_asset(TRIAL + '/L_KarmeiYosef_31850349_34907601_4km_WPTrial_HLODLayer_Merged')
    bs = l.get_editor_property('hlod_builder_settings')
    bs.set_editor_property('disallow_nanite', True)
    RESULT = {'ok': True, 'disallow_nanite': bool(bs.get_editor_property('disallow_nanite')), 'type': str(l.get_editor_property('layer_type'))}

elif step == 'landscape_hlod':
    # Landscape streaming proxies need an HLOD layer or distant ground disappears when their cells unload. Landscape uses its
    # own HLOD builder whatever the layer type; the layer is always loaded so a low-detail ground exists everywhere.
    at = u.AssetToolsHelpers.get_asset_tools()
    path = TRIAL + '/HLOD/HL_Landscape'
    l = u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else at.create_asset('HL_Landscape', TRIAL + '/HLOD', u.HLODLayer, u.HLODLayerFactory())
    l.set_editor_property('layer_type', u.HLODLayerType.MESH_SIMPLIFY)
    l.set_editor_property('is_spatially_loaded', False)
    n = 0
    for a in actors:
        if a.get_class().get_name() == 'LandscapeStreamingProxy':
            a.set_editor_property('hlod_layer', l); n += 1
    RESULT = {'ok': True, 'proxies': n, 'layer_type': str(l.get_editor_property('layer_type')), 'spatial': bool(l.get_editor_property('is_spatially_loaded'))}

elif step == 'pcg_generate':
    # partitioned components: use the editor's Generate (dispatches to the partition-local components)
    vol = [a for a in actors if isinstance(a, u.PCGVolume)][0]
    c = vol.get_component_by_class(u.PCGComponent)
    meths = [n for n in dir(c) if n.startswith(('generate', 'cleanup', 'refresh', 'notify'))]
    u.SystemLibrary.execute_console_command(world, 'pcg.FlushCache')
    c.generate(True)
    RESULT = {'ok': True, 'methods': meths}

elif step == 'status':
    vol = [a for a in actors if isinstance(a, u.PCGVolume)]
    c = vol[0].get_component_by_class(u.PCGComponent) if vol else None
    parts = [a for a in actors if a.get_class().get_name().startswith('PCGPartitionActor')]
    inst = 0
    for a in parts + vol:
        for ic in a.get_components_by_class(u.InstancedStaticMeshComponent):
            inst += ic.get_instance_count()
    RESULT = {'ok': True, 'generated': bool(c.get_editor_property('generated')) if c else None,
              'in_progress': bool(c.get_editor_property('generation_in_progress')) if c else None,
              'partition_actors_loaded': len(parts), 'instances_loaded': inst}
