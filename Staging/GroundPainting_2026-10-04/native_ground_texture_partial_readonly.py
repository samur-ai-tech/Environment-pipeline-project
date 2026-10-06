"""Read the single preserved copy after the failed first creation; no setters."""
import datetime
import hashlib
import json
import os
import types
from pathlib import Path
import unreal

POLICY_SHA = 'bdba22a3bcf801663788166649e3fd593704507f133995a1085ed0b37c2404b4'
FAILURE_SHA = '43434496fff82505a125ffa70bb8ad5cf8f8ca43aa507d9f6905b61f0c437f7f'
root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
here = root / 'Staging/GroundPainting_2026-10-04'
rev = here / 'Revision_2026-10-05'
file = here / 'native_ground_texture_policy.py'
data = file.read_bytes()
assert hashlib.sha256(data).hexdigest() == POLICY_SHA
p = types.ModuleType('ground_partial_readonly_definitions')
p.__file__ = str(file)
exec(compile(data, str(file), 'exec'), p.__dict__)
assert 'ARGS' not in p.__dict__
h = p.load_helper()
p.sole_editor()
assert os.getpid() == ARGS['expected_pid'] == 32464
failure_file = rev / 'GROUND_TEXTURE_POLICY_apply_GazaShujaiya_r025_retained_residency_PID32464.json'
assert h.sha(failure_file) == FAILURE_SHA
failure = json.loads(failure_file.read_text())
assert failure['status'] == 'FAILED_PARTIAL_STATE_PRESERVED'
assert len(failure['created_assets']) == 1 and failure['bound_parameters'] == []
assignment = json.loads((here / 'ASSIGNMENT.json').read_text())
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_path_name() == failure['world']
master = unreal.load_asset(h.MASTER)
item = failure['plan']['items'][0]
assert item['parameter'] == 'Sand_01_Albedo'
copy = unreal.load_asset(item['destination'])
assert copy and not h.package_file(item['destination']).exists()

def snapshot():
    sources, actors = h.guard(assignment, failure['world'], require_authoring=False)
    nodes = {h.path(e): h.describe(master, e) for e in h.LIB.get_material_expressions(master)}
    instances = {k: h.material_state(master, unreal.load_asset(k)) for k in failure['before']['instances']}
    dirty = {'maps': sorted(h.path(v) for v in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
             'content': sorted(h.path(v) for v in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())}
    states = {r['parameter']: {'asset_exists': unreal.EditorAssetLibrary.does_asset_exist(r['destination']),
                              'disk': h.disk_state(h.package_file(r['destination']))}
              for r in failure['plan']['items']}
    return {'sources': sources, 'scene': h.scene_state(actors), 'nodes': nodes,
            'instances': instances, 'dirty': dirty, 'copies': states,
            'disk': {k: h.sha(k) for k in failure['before']['disk']},
            'cvars': {n: unreal.SystemLibrary.get_console_variable_string_value(n) for n in p.CVARS},
            'source': p.texture_details(h, unreal.load_asset(item['source'])),
            'copy': p.texture_details(h, copy)}

before = snapshot()
for key in ('sources', 'scene', 'nodes', 'instances', 'disk', 'cvars'):
    assert before[key] == failure['before'][key], key
assert before['dirty'] == failure['failure_dirty']
assert before['copies'] == failure['failure_all_twelve_copy_states']
assert before['source'] == failure['before']['source_textures'][item['parameter']]
p.compare_copy(before['source'], before['copy'])
assert snapshot() == before
assert h.sha(file) == POLICY_SHA and h.sha(failure_file) == FAILURE_SHA
out = rev / 'GROUND_TEXTURE_PARTIAL_READY_PID32464.json'
assert not out.exists()
result = {'status': 'SINGLE_PRESERVED_COPY_READ_ONLY_READY_4096', 'pid': os.getpid(),
          'world': failure['world'], 'area': failure['area'],
          'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'helper_sha256': h.sha(here / 'native_ground_texture_partial_readonly.py'),
          'policy_definitions_sha256': POLICY_SHA, 'failure_receipt_sha256': FAILURE_SHA,
          'state': before, 'native_mutation': False, 'force_or_loading_api_called': False,
          'source_scene_graph_cvars_and_dirty_preserved': True,
          'limited_claim': 'The one unsaved copy now reports 4096 by both native size getters. No MI binding or copy save occurred.'}
out.write_text(json.dumps(result, indent=2))
RESULT = {'receipt': str(out), 'sha256': h.sha(out), 'status': result['status'],
          'copy_metadata': before['copy']['metadata'], 'dirty': before['dirty']}
