"""In-editor (Karmei Yosef operator): temporary probe on the 4 km clone (nothing saved). 'start': transient graph with
two ways to sample the Forest mask at 0.001 per m2 -> A: Intersection(landscape, texture) -> Surface Sampler;
B: landscape Surface Sampler -> Sample Texture -> Density Filter >= 0.5. Logs pins/types. 'read': counts and Z range per
output dataset, then removes the probe. ARGS: expected_pid, step."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
LABEL = 'KY4_ZoneProbe'
MASK = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/Masks/T_KY4_Mask_Forest'
labels = lambda pins: [str(p.properties.label) for p in pins]
if ARGS['step'] == 'start':
    land = [a for a in eas.get_all_level_actors() if isinstance(a, u.Landscape)][0]
    origin, extent = land.get_actor_bounds(False)
    vol = eas.spawn_actor_from_class(u.PCGVolume, origin); vol.set_actor_label(LABEL)
    vol.set_actor_scale3d(u.Vector(extent.x / 100.0, extent.y / 100.0, (extent.z + 5000) / 100.0))
    g = u.new_object(u.PCGGraph, outer=vol)
    getl, gs = g.add_node_of_type(u.PCGGetLandscapeSettings)
    sp = gs.get_editor_property('sampling_properties'); sp.set_editor_property('get_layer_weights', True); gs.set_editor_property('sampling_properties', sp)
    tex, ts = g.add_node_of_type(u.PCGTextureSamplerSettings)
    ts.set_editor_property('texture', u.load_asset(MASK))
    ts.set_editor_property('use_absolute_transform', True)
    ts.set_editor_property('transform', u.Transform(location=u.Vector(0, 0, float(ARGS.get('tz', 0))), rotation=u.Rotator(0, 0, 0), scale=u.Vector(201600.0, 201600.0, float(ARGS.get('sz', 1.0)))))
    ts.set_editor_property('filter', u.PCGTextureFilter.POINT)
    ts.set_editor_property('color_channel', u.PCGTextureColorChannel.RED)
    ts.set_editor_property('density_function', u.PCGTextureDensityFunction.MULTIPLY)
    info = {'tex_in': labels(tex.input_pins), 'tex_out': labels(tex.output_pins)}
    o = g.get_output_node()
    # A: intersection
    inter_cls = getattr(u, 'PCGIntersectionSettings', None) or getattr(u, 'PCGInnerIntersectionSettings', None)
    info['intersection_class'] = inter_cls.__name__ if inter_cls else None
    if inter_cls and ARGS.get('only') in (None, 'A'):
        inter, _ = g.add_node_of_type(inter_cls)
        info['inter_in'] = labels(inter.input_pins); info['inter_out'] = labels(inter.output_pins)
        g.add_edge(getl, 'Out', inter, info['inter_in'][0])
        g.add_edge(tex, info['tex_out'][0], inter, info['inter_in'][1] if len(info['inter_in']) > 1 and info['inter_in'][1] not in ('Execution Dependency', 'Overrides') else info['inter_in'][0])
        sa, sas = g.add_node_of_type(u.PCGSurfaceSamplerSettings); sas.set_editor_property('points_per_squared_meter', 0.001)
        g.add_edge(inter, info['inter_out'][0], sa, 'Surface'); g.add_edge(sa, 'Out', o, 'Out')
    # B: sample texture onto landscape points
    if ARGS.get('only') in (None, 'B'):
        sb, sbs = g.add_node_of_type(u.PCGSurfaceSamplerSettings); sbs.set_editor_property('points_per_squared_meter', 0.001)
        g.add_edge(getl, 'Out', sb, 'Surface')
        st, sts = g.add_node_of_type(u.PCGSampleTextureSettings)
        sts.set_editor_property('texture_mapping_method', u.PCGTextureMappingMethod.PLANAR)
        info['st_in'] = labels(st.input_pins); info['st_out'] = labels(st.output_pins)
        g.add_edge(sb, 'Out', st, info['st_in'][0]); g.add_edge(tex, info['tex_out'][0], st, info['st_in'][1])
        df, dfs = g.add_node_of_type(u.PCGDensityFilterSettings); dfs.set_editor_property('lower_bound', 0.5); dfs.set_editor_property('upper_bound', 1.0)
        g.add_edge(st, info['st_out'][0], df, 'In'); g.add_edge(df, 'Out', o, 'Out')
    comp = vol.get_component_by_class(u.PCGComponent); comp.set_graph(g)
    comp.set_editor_property('generation_trigger', u.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    u.SystemLibrary.execute_console_command(world, 'pcg.FlushCache')
    comp.generate_local(True)
    RESULT = {'ok': True, **info}
else:
    vol = [a for a in eas.get_all_level_actors() if a.get_actor_label() == LABEL][0]
    comp = vol.get_component_by_class(u.PCGComponent)
    datas, _ = comp.get_generated_graph_output().get_typed_inputs(u.PCGBasePointData)
    res = []
    for d in datas:
        n = d.get_num_points()
        zs = [d.get_transform(i).translation.z for i in range(0, n, max(1, n // 200))] if n else []
        xs = [d.get_transform(i).translation.x for i in range(0, n, max(1, n // 200))] if n else []
        ys = [d.get_transform(i).translation.y for i in range(0, n, max(1, n // 200))] if n else []
        res.append({'points': n, 'z_min_max': [round(min(zs)), round(max(zs))] if zs else None,
                    'x_mean': round(sum(xs) / len(xs)) if xs else None, 'y_mean': round(sum(ys) / len(ys)) if ys else None})
    eas.destroy_actor(vol)
    RESULT = {'ok': True, 'datasets': res}
