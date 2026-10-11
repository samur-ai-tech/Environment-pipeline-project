"""In-editor (Karmei Yosef operator, WP trial stage B verification, 2026-10-10). Verifies streaming + HLOD in the editor the way a
runtime view would see it: only actors within ARGS.radius_cm of ARGS.center stay loaded; everything else is unloaded so its HLOD
stand-ins must show (vegetation layer always loaded; buildings/landscape layers forced visible in the editor for the check).
steps (ARGS.step):
  editor_hlod  set editor_loading_behavior FORCE_LOADED on HL_Buildings and HL_Landscape (trial assets) so unloaded regions
               show their HLODs in the editor (no effect at runtime). Not saved unless wptrial_save runs.
  region       unload every spatially loaded actor outside the radius, load those inside; report loaded counts.
  hlods        read-only: loaded HLOD actors per layer and their instance counts.
ARGS: expected_pid, step [, center [x,y], radius_cm].
"""
import math, os, time
from collections import Counter
import unreal as u
TRIAL = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial'
WPMAP = TRIAL + '/L_KarmeiYosef_31850349_34907601_4km_WPTrial_WP'
assert os.getpid() == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == WPMAP
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
step = ARGS['step']

if step == 'editor_hlod':
    out = {}
    for n in ('HL_Buildings', 'HL_Landscape'):
        l = u.load_asset(TRIAL + '/HLOD/' + n)
        l.set_editor_property('editor_loading_behavior', u.HLODLayerEditorLoadingBehavior.FORCE_LOADED)
        out[n] = str(l.get_editor_property('editor_loading_behavior'))
    RESULT = {'ok': True, **out}

elif step == 'region':
    cx, cy = ARGS['center']; R = float(ARGS['radius_cm'])
    descs = u.WorldPartitionBlueprintLibrary.get_actor_descs()
    keep, drop, nonspatial = [], [], 0
    for d in descs:
        if not d.get_editor_property('is_spatially_loaded'):
            nonspatial += 1; continue
        b = d.get_editor_property('bounds')
        mn, mx = b.min, b.max
        # distance from the centre to the actor's 2D bounds
        dx = max(mn.x - cx, 0, cx - mx.x); dy = max(mn.y - cy, 0, cy - mx.y)
        (keep if math.hypot(dx, dy) <= R else drop).append(d.get_editor_property('guid'))
    t0 = time.time()
    u.WorldPartitionBlueprintLibrary.unload_actors(drop)
    u.WorldPartitionBlueprintLibrary.load_actors(keep)
    secs = round(time.time() - t0, 1)
    loaded = eas.get_all_level_actors()
    RESULT = {'ok': True, 'keep': len(keep), 'unload': len(drop), 'nonspatial': nonspatial, 'seconds': secs, 'loaded_now': len(loaded),
              'loaded_by_class': dict(Counter(a.get_class().get_name() for a in loaded).most_common(12))}

elif step == 'ground':
    # ground height at ARGS.xy: temporarily load the landscape proxies there, trace, then unload them again
    x, y = ARGS['xy']
    descs = [d for d in u.WorldPartitionBlueprintLibrary.get_actor_descs() if 'LandscapeStreamingProxy' in str(d.get_editor_property('native_class'))]
    near = []
    for d in descs:
        b = d.get_editor_property('bounds')
        if b.min.x - 100 <= x <= b.max.x + 100 and b.min.y - 100 <= y <= b.max.y + 100:
            near.append(d.get_editor_property('guid'))
    u.WorldPartitionBlueprintLibrary.load_actors(near)
    land = [a for a in eas.get_all_level_actors() if isinstance(a, (u.Landscape, u.LandscapeProxy))]
    ignore = [a for a in eas.get_all_level_actors() if a not in land]
    hit = u.SystemLibrary.line_trace_single(world, u.Vector(x, y, 80000.0), u.Vector(x, y, -20000.0), u.TraceTypeQuery.TRACE_TYPE_QUERY1, False, ignore, u.DrawDebugTrace.NONE, True)
    h = hit[1] if isinstance(hit, tuple) else hit
    t = h.to_tuple()
    z = t[4].z if t[0] else None
    u.WorldPartitionBlueprintLibrary.unload_actors(near)
    RESULT = {'ok': z is not None, 'z': z, 'proxies': len(near)}

elif step == 'hlods':
    c = Counter(); inst = Counter()
    for a in eas.get_all_level_actors():
        if a.get_class().get_name().startswith('WorldPartitionHLOD'):
            try:
                l = a.get_editor_property('source_cell_name')
            except Exception:
                l = None
            lay = None
            try:
                lay = a.get_editor_property('sub_actors_hlod_layer')
                lay = lay.get_name() if lay else None
            except Exception:
                pass
            c[lay] += 1
            for ic in a.get_components_by_class(u.InstancedStaticMeshComponent):
                inst[lay] += ic.get_instance_count()
            for sc in a.get_components_by_class(u.StaticMeshComponent):
                if not isinstance(sc, u.InstancedStaticMeshComponent):
                    inst[str(lay) + ':meshes'] += 1
    RESULT = {'ok': True, 'hlod_actors': dict(c), 'hlod_instances': dict(inst)}
