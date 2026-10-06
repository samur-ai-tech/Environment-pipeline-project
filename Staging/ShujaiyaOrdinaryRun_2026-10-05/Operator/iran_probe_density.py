# Read-only: compact scene facts + densest building cell for camera planning (Iran, 2026-10-06).
import json
from collections import Counter
import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = ues.get_editor_world(); actors = list(eas.get_all_level_actors())
out = {'world': w.get_path_name(), 'actor_count': len(actors),
       'classes': Counter(a.get_class().get_name() for a in actors).most_common(14),
       'landscape_count': sum(1 for a in actors if isinstance(a, unreal.LandscapeProxy)),
       'houdini_actors': [a.get_actor_label() for a in actors if 'Houdini' in a.get_class().get_name()][:10],
       'static_mesh_actors': sum(1 for a in actors if isinstance(a, unreal.StaticMeshActor)),
       'foliage_actors': sum(1 for a in actors if 'Foliage' in a.get_class().get_name())}
cell = 25000.0  # 250 m cells over the 4 km area
grid = Counter(); zsum = {}; n_total = 0
for a in actors:
    if not a.get_actor_label().startswith('bank_instances_'): continue
    for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
        n = c.get_instance_count(); n_total += n
        step = max(1, n // 400)
        for i in range(0, n, step):
            t = c.get_instance_transform(i, True).translation
            k = (int(t.x // cell), int(t.y // cell)); grid[k] += step
            zsum[k] = zsum.get(k, [0.0, 0])
            zsum[k][0] += t.z; zsum[k][1] += 1
top = grid.most_common(5)
out['instances_total'] = n_total
out['dense_cells'] = [{'cell': k, 'center': [k[0]*cell + cell/2, k[1]*cell + cell/2], 'count_est': v,
                       'z_mean': round(zsum[k][0] / zsum[k][1])} for k, v in top]
result = out; RESULT = out
print(json.dumps(out))
