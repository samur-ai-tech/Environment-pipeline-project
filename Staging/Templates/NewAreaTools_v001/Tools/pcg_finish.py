"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the Karmei Yosef tool. PCG clone status; with ARGS.save and a
finished generation, named-save the clone map only and write receipts/PCG_RESULT_<label>.json.
ARGS: expected_pid, script_file (client), clone_suffix (required: '' first clone, '_v2' rebuilt clone), save (bool), label."""
import datetime, hashlib, importlib.util, json, os
from collections import Counter
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
CLONE = A.clone_map(ARGS['clone_suffix'])                               # required, explicit
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
