# Read-only scene probe for the Iran area after the 2026-10-06 ordinary regeneration (manager cc37d4d2).
import json
from collections import Counter
import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = ues.get_editor_world()
actors = list(eas.get_all_level_actors())
out = {'world': w.get_path_name(), 'actor_count': len(actors),
       'classes': Counter(a.get_class().get_name() for a in actors).most_common(25)}
lands = []
for a in actors:
    if isinstance(a, unreal.LandscapeProxy):
        o, e = a.get_actor_bounds(False)
        mat = a.get_editor_property('landscape_material')
        lands.append({'label': a.get_actor_label(), 'class': a.get_class().get_name(),
                      'origin': [round(o.x), round(o.y), round(o.z)], 'extent': [round(e.x), round(e.y), round(e.z)],
                      'material': mat.get_path_name() if mat else None,
                      'components': len(a.get_components_by_class(unreal.LandscapeComponent))})
out['landscapes'] = lands
inst_total = 0; per_actor = Counter(); samples = []; zs = []
for a in actors:
    for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
        n = c.get_instance_count(); inst_total += n; per_actor[a.get_actor_label()] += n
        for i in range(0, n, max(1, n // 3)):
            if len(samples) >= 24: break
            t = c.get_instance_transform(i, True).translation
            samples.append([round(t.x), round(t.y), round(t.z)]); zs.append(t.z)
out['ism_instances_total'] = inst_total
out['ism_top_actors'] = per_actor.most_common(12)
out['instance_samples'] = samples[:24]
out['instance_z_minmax'] = [round(min(zs)), round(max(zs))] if zs else None
out['static_mesh_actors'] = sum(1 for a in actors if isinstance(a, unreal.StaticMeshActor))
out['houdini_actors'] = [a.get_actor_label() for a in actors if 'Houdini' in a.get_class().get_name()][:10]
out['foliage_actors'] = sum(1 for a in actors if 'Foliage' in a.get_class().get_name())
result = out
RESULT = out
print(json.dumps(out))
