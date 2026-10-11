"""In-editor (Karmei Yosef operator): PCG trial status; with ARGS.save and a finished generation, named-save the clone map
only and write receipts/PCG_RESULT.json. ARGS: expected_pid, save (bool), label."""
import datetime, hashlib, json, os
from collections import Counter
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
CLONE = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/L_KarmeiYosef_31850349_34907601_4km_PCGTrial' + ARGS.get('clone_suffix', '')     # '_v2' = rebuilt clone
pid = os.getpid(); assert pid == ARGS['expected_pid']
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == CLONE
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
vols = [a for a in eas.get_all_level_actors() if isinstance(a, u.PCGVolume)]
assert len(vols) == 1, [v.get_path_name() for v in vols]
comp = vols[0].get_component_by_class(u.PCGComponent)
state = {'generated': comp.get_editor_property('generated'), 'in_progress': comp.get_editor_property('generation_in_progress')}
per_mesh = Counter(); comps = 0
for c in vols[0].get_components_by_class(u.InstancedStaticMeshComponent):
    comps += 1
    m = c.get_editor_property('static_mesh')
    per_mesh[m.get_path_name().split('.')[0] if m else None] += c.get_instance_count()
state.update(ism_components=comps, instances=sum(per_mesh.values()), per_mesh=dict(per_mesh))
dirty = lambda: (sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
                 sorted(x.get_path_name() for x in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))
state['dirty'] = dirty()
if ARGS.get('save'):
    assert state['generated'] and not state['in_progress'] and state['instances'] > 0, state
    assert state['dirty'][1] == [], 'Unexpected dirty content: %s' % (state['dirty'][1],)
    assert u.EditorLoadingAndSavingUtils.save_map(world, CLONE)
    f = ROOT / ('Content' + CLONE[5:] + '.umap')
    state.update(saved_map_sha256=hashlib.sha256(f.read_bytes()).hexdigest(), saved_bytes=f.stat().st_size, dirty_after=dirty(),
                 utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), pid=pid)
    (TASK / 'receipts' / ('PCG_RESULT_%s.json' % ARGS.get('label', 'save'))).write_text(json.dumps(state, indent=2), encoding='utf-8')
RESULT = {'ok': True, **state}
