"""Focused source check with recorded paths and fake IO; no Unreal import."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
from types import MethodType

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
failure_path = ROOT/'Staging/ManagedSystemsAstra_2026-10-04/Task4_Integration/SHUJAIYA_RUN1_FAILURE_NATIVE.json'
failure = json.loads(failure_path.read_text(encoding='utf-8-sig'))
fixture_path = OUT/'LANDSCAPE_FAILURE_EVIDENCE.json'
if not fixture_path.exists():
    state_path = ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/WORKFLOW_STATE.json'
    state = json.loads(state_path.read_text(encoding='utf-8-sig'))
    road_path = state_path.with_name('ROADBLD_WORKFLOW_STATE.json')
    road = json.loads(road_path.read_text(encoding='utf-8-sig'))
    fixture = {'failure_receipt_sha256': hashlib.sha256(failure_path.read_bytes()).hexdigest(),
               'workflow_receipt_sha256': hashlib.sha256(state_path.read_bytes()).hexdigest(),
               'road_receipt_sha256': hashlib.sha256(road_path.read_bytes()).hexdigest(),
               'landscapes': failure['landscapes'], 'map': road['named_map'], 'area': road['area_id'],
               'previous_landscape_accounting': state['previous_landscape_accounting'],
               'source_sha256': road['source_sha256'], 'centreline_sha256': road['centreline_sha256'],
               'operation_started_epoch': state['operation_started_epoch'],
               'failure_phase': road['phase'], 'rebuild_pass': road['rebuild_pass'],
               'native_owned_landscape_patches': road['native_owned_landscape_patches']}
    fixture_path.write_text(json.dumps(fixture, indent=2), encoding='utf-8')
fixture = json.loads(fixture_path.read_text())
source = ROOT/'Content/Python/geocity_roadbld_landscape.py'
tree = ast.parse(source.read_bytes())
tree.body = [n for n in tree.body if not (isinstance(n, ast.Import) and any(a.name == 'unreal' for a in n.names))]


class Actor:
    def __init__(self, path, package=None):
        self.path = path
        self.package = package or fixture['map']

    def get_path_name(self):
        return self.path

    def get_outermost(self):
        return SimpleNamespace(get_path_name=lambda: self.package)


class Landscape(Actor):
    pass


class Parent:
    def guard(self):
        assert not self.state.get('phase', '').startswith('failed'), 'Failed parent operation'

    def authority(self):
        self.guard()
        return {'actor': self.current, 'evidence': copy.deepcopy(self.evidence)}


def setup():
    parent = Parent()
    parent.current = Landscape(fixture['landscapes'][1]['path'])
    assert parent.current.path.endswith('_landscape_0')
    previous = Landscape(fixture['landscapes'][0]['path'])
    owner = Actor(fixture['previous_landscape_accounting']['hda_actor_path'])
    world = Actor(fixture['map'] + '.' + fixture['map'].rsplit('/', 1)[-1])
    parent.p = {'map': fixture['map'], 'source': fixture['previous_landscape_accounting']['source']}
    parent.state = {'phase': 'native_road_authoring', 'previous_landscape_accounting': copy.deepcopy(fixture['previous_landscape_accounting'])}
    parent.started_epoch = fixture['operation_started_epoch']
    parent.lease_line = 'OFFLINE_SAME_LEASE'
    parent.native_road_phase = 'authoring'
    parent.previous_baked_paths = list(parent.state['previous_landscape_accounting']['live_actor_paths'])
    parent.wrapper = SimpleNamespace(get_houdini_asset_actor=lambda: owner)
    actors = [owner, previous, parent.current]
    parent.evidence = {'schema': 'environmentpipeline.current_road_landscape.v1', 'pid': os.getpid(),
        'named_map': fixture['map'], 'area_id': fixture['area'], 'source_sha256': fixture['source_sha256'],
        'centreline_sha256': fixture['centreline_sha256'],
        'lease_sha256': hashlib.sha256(parent.lease_line.encode()).hexdigest(),
        'operation_started_epoch': parent.started_epoch, 'hda_actor_path': owner.path,
        'current_actor_path': parent.current.path,
        'accounted_previous_landscape_paths': sorted(parent.previous_baked_paths), 'official_output_verified': True}
    run = SimpleNamespace(landscape_authority=parent.authority, _landscape_authority_parent=parent,
        lease_line=parent.lease_line, p=dict(parent.p),
        plan={'named_map': fixture['map'], 'area_id': fixture['area'], 'source_sha256': fixture['source_sha256'], 'centreline_sha256': fixture['centreline_sha256']},
        _current_landscape_actor=None, _current_landscape_evidence=None, state={}, guard=lambda: world)
    parent.native_road_run = run
    api = SimpleNamespace(Landscape=Landscape, EditorActorSubsystem=object(),
        get_editor_subsystem=lambda cls: SimpleNamespace(get_all_level_actors=lambda: actors),
        load_object=lambda unused, path: next((a for a in actors if a.path == path), None))
    scope = {'unreal': api}
    exec(compile(tree, str(source), 'exec'), scope)
    return scope, run, parent, actors, world


checks = []
scope, run, parent, actors, world = setup()
sampler = scope['LandscapeSampler'](run)
assert sampler.landscape is parent.current
assert all(a is not parent.current for a in sampler.ignored)
assert scope['LandscapeSampler'](run).landscape is parent.current
checks.append('Recorded _0 actor selected exactly; repeated resolution stays identical')
scope, run, parent, actors, world = setup()
parent.native_road_run = None
assert scope['LandscapeSampler'](run).landscape is parent.current
checks.append('Synchronous build entry before parent assigns native_road_run')


def reject(label, mutate):
    scope, run, parent, actors, world = setup()
    mutate(scope, run, parent, actors, world)
    try:
        scope['LandscapeSampler'](run)
    except (AssertionError, RuntimeError, KeyError, FileNotFoundError):
        checks.append(label)
    else:
        raise AssertionError('Accepted invalid authority: ' + label)


reject('Unknown Landscape rejects', lambda s,r,p,a,w: a.append(Landscape(fixture['map']+'.Unknown')))
reject('Foreign current world rejects', lambda s,r,p,a,w: setattr(p.current, 'package', '/Game/Other'))
reject('Missing current loaded actor rejects', lambda s,r,p,a,w: a.remove(p.current))
reject('Stale same-path object rejects', lambda s,r,p,a,w: a.__setitem__(-1, Landscape(p.current.path)))
reject('Missing callback rejects', lambda s,r,p,a,w: setattr(r,'landscape_authority',None))
reject('Unbound callback rejects', lambda s,r,p,a,w: setattr(r,'landscape_authority',lambda: p.authority()))
reject('Foreign parent rejects', lambda s,r,p,a,w: setattr(r,'_landscape_authority_parent',object()))
reject('Wrong current road run rejects', lambda s,r,p,a,w: setattr(p,'native_road_run',object()))
reject('Failed parent rejects', lambda s,r,p,a,w: p.state.update(phase='failed_operation'))
reject('Wrong native phase rejects', lambda s,r,p,a,w: setattr(p,'native_road_phase','suppression'))
reject('Changed lease rejects', lambda s,r,p,a,w: setattr(p,'lease_line','OTHER'))
reject('Missing HDA owner rejects', lambda s,r,p,a,w: a.pop(0))
reject('Unaccounted prior Landscape rejects', lambda s,r,p,a,w: p.state['previous_landscape_accounting'].update(unaccounted_actor_paths=['unknown']))
reject('Prior paths missing lifecycle ownership rejects', lambda s,r,p,a,w: p.previous_baked_paths.clear())
for field in ('source_sha256','centreline_sha256','pid','operation_started_epoch','hda_actor_path','current_actor_path','lease_sha256','official_output_verified'):
    reject('Wrong evidence '+field, lambda s,r,p,a,w,field=field: p.evidence.update({field: 'WRONG'}))


def change_frozen(scope, run, parent, actors, world):
    scope['LandscapeSampler'](run)
    parent.started_epoch += 1
    parent.evidence['operation_started_epoch'] = parent.started_epoch


reject('Changed current operation after first binding rejects', change_frozen)
scope, run, parent, actors, world = setup()
try:
    scope['LandscapeSampler'](run, saved=True)
except AssertionError:
    checks.append('Saved two-Landscape world still rejects')
else:
    raise AssertionError('Saved singleton gate weakened')
actors.remove(actors[1])
assert scope['LandscapeSampler'](run, saved=True).landscape is parent.current
checks.append('Saved singleton remains supported without pre-Bake authority call')

# Exercise task1's actual callback body against this selector, substituting
# only its already-verified official helper/native IO boundary.
parent_source = ROOT/'Content/Python/geocity_bank_workflow.py'
parent_tree = ast.parse(parent_source.read_bytes())
parent_class = next(n for n in parent_tree.body if isinstance(n,ast.ClassDef) and n.name=='GeoCityRun')
callback_node = next(n for n in parent_class.body if isinstance(n,ast.FunctionDef) and n.name=='current_road_landscape_authority')
scope, run, parent, actors, world = setup()
parent_scope = {'Path':Path,'hashlib':hashlib,'os':os,'unreal':scope['unreal'],'_path':lambda obj:obj.get_path_name()}
exec(compile(ast.Module(body=[callback_node],type_ignores=[]),str(parent_source),'exec'),parent_scope)
parent.native_road_export = {'area_id':fixture['area'],'source_sha256':fixture['source_sha256'],'centreline_sha256':fixture['centreline_sha256']}
parent.official_landscapes = lambda wrapper:{parent.current.path:parent.current}
parent.write = lambda:None
run.landscape_authority = MethodType(parent_scope['current_road_landscape_authority'],parent)
assert scope['LandscapeSampler'](run).landscape is parent.current
checks.append('Task1 actual callback body and task2 selector agree on recorded _0 authority envelope')

before = ast.parse((OUT/'BeforeLandscapeAuthority/geocity_roadbld_landscape.py').read_bytes())
def collision_method(module):
    cls = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name=='LandscapeSampler')
    return next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name=='__call__')
assert ast.dump(collision_method(before), include_attributes=False) == ast.dump(collision_method(tree), include_attributes=False)
workflow = ast.parse((ROOT/'Content/Python/geocity_roadbld_workflow.py').read_bytes())
for name in ('build',):
    fn = next(n for n in workflow.body if isinstance(n,ast.FunctionDef) and n.name==name)
    assert fn.args.args[-1].arg=='landscape_authority'
assert 'LandscapeSampler(run)' in (ROOT/'Content/Python/geocity_roadbld_grounding.py').read_text()
for p in (source, ROOT/'Content/Python/geocity_roadbld_workflow.py'):
    compile(p.read_bytes(), str(p), 'exec', dont_inherit=True)
result = {'status':'PASSED_OFFLINE_LANDSCAPE_AUTHORITY_CHECKS','checks':checks,
          'collision_method_AST_unchanged':True, 'correction_uses_same_sampler':True,
          'native_calls':0,'unreal_imports':0,'native_selector_execution':'NOT_RUN',
          'task1_callback_source_sha256_at_check':hashlib.sha256(parent_source.read_bytes()).hexdigest(),
          'limits':'Recorded paths and metadata with fake UObject/actor enumeration. Real official helper, collision, clipping, save/reopen and regeneration require manager-activated fresh startup.'}
(OUT/'LANDSCAPE_AUTHORITY_CHECKS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'cases':len(checks)}))
