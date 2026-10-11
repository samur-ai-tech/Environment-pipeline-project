"""In-editor, read-only (WP trial verification, 2026-10-10): for every WorldPartitionHLOD actor - spatial loading flag, runtime grid,
and what it holds (instances per content class: vegetation / farm / buildings / landscape meshes / other). Totals are compared
with the sources: 109,893 PCG plants + PazFarm_Detail instances + barn/gates for vegetation, 35,459 + shells for buildings.
ARGS: expected_pid."""
import os
from collections import Counter, defaultdict
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
VEG = ('/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/Vegetation/', '/Game/STF/', '/Game/Palms_Pack_01/', '/Game/ProceduralNtr_vol2/',
       '/Game/Project/Shared/ModelBank/Supply/desert/', '/Game/Modular_Rural_Cabin/Meshes/Foliage/')
FARM = ('/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/PazFarm/',)
BLD = ('/Game/ModularCourtyard/', '/Game/Project/Shared/Bank_ME_v3/Buildings/', '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_WPTrial/Buildings/')


def kind(p):
    if p is None:
        return 'none'
    if p.startswith(FARM):
        return 'farm'
    if p.startswith(VEG):
        return 'vegetation'
    if p.startswith(BLD):
        return 'building'
    if '/HLOD' in p or 'Landscape' in p or '__ExternalObjects__' in p or 'Transient' in p:
        return 'landscape_or_generated'
    return 'other:' + p.rsplit('/', 1)[0][:60]


per_actor = []
tot = Counter(); spatial = Counter(); grids = Counter(); by_kind_spatial = Counter()
for a in eas.get_all_level_actors():
    if not a.get_class().get_name().startswith('WorldPartitionHLOD'):
        continue
    sp = bool(a.get_editor_property('is_spatially_loaded'))
    try:
        g = str(a.get_editor_property('runtime_grid'))
    except Exception:
        g = 'n/a'
    k = Counter()
    for c in a.get_components_by_class(u.StaticMeshComponent):
        m = c.get_editor_property('static_mesh')
        p = m.get_path_name().split('.')[0] if m else None
        n = c.get_instance_count() if isinstance(c, u.InstancedStaticMeshComponent) else 1
        k[kind(p)] += n
    main = k.most_common(1)[0][0] if k else 'empty'
    spatial[sp] += 1; grids[g] += 1; by_kind_spatial[(main, sp)] += 1
    for kk, v in k.items():
        tot[(kk, sp)] += v
RESULT = {'ok': True, 'hlod_actors': sum(spatial.values()), 'spatially_loaded': {str(k): v for k, v in spatial.items()},
          'runtime_grids': dict(grids), 'actors_by_main_content_and_spatial': {'%s|spatial=%s' % k: v for k, v in by_kind_spatial.items()},
          'instances_by_content_and_spatial': {'%s|spatial=%s' % k: v for k, v in sorted(tot.items(), key=lambda x: -x[1])}}
