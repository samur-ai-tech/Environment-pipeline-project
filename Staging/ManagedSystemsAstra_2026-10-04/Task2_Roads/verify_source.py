"""Offline checks of production policy gates; no Unreal import or editor IO."""
import ast
import configparser
import hashlib
import json
import re
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'Content/Python/geocity_roadbld_workflow.py'
tree = ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
names = {'_path', '_names', '_get', '_call', '_read', '_sha', '_retirement_history', 'inspect_geographic_landscape_authority',
         'require_geographic_landscape_authority'}
constants = {'NATIVE_LANDSCAPE_EDIT_FLAGS', 'NATIVE_SETTINGS_CLASS', 'NATIVE_SETTINGS_CONFIG'}
selected = [node for node in tree.body if
            (isinstance(node, ast.FunctionDef) and node.name in names) or
            (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants for t in node.targets))]
scope = {'__file__': str(SOURCE), 'Path': Path, 'configparser': configparser,
         'hashlib': hashlib, 'json': json, 're': re}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), 'exec'), scope)
flags = scope['NATIVE_LANDSCAPE_EDIT_FLAGS']
class_path = scope['NATIVE_SETTINGS_CLASS']
observations = []


class Settings:
    def __init__(self, values=None, path=class_path):
        self.values = {name: False for name in flags} if values is None else values
        self.path = path
        self.effective = self

    def get_editor_property(self, name):
        return self.values[name]

    def get_class(self):
        return SimpleNamespace(get_path_name=lambda: self.path)

    def get_path_name(self):
        return self.path + ':offline_fixture'

    def get(self):
        return self.effective


def configure(cdo):
    scope['unreal'] = SimpleNamespace(RoadBLDRuntimeSettings=object(), get_default_object=lambda cls: cdo)


def expect(label, passed):
    report = scope['inspect_geographic_landscape_authority']()
    assert report['passed'] is passed, (label, report)
    try:
        result = scope['require_geographic_landscape_authority']()
    except RuntimeError:
        assert not passed, label
    else:
        assert passed and result == {n: False for n in flags}, label
    observations.append({'case': label, 'expected_pass': passed, 'passed': True})


configure(Settings())
expect('Actual project config plus false native CDO/accessor views', True)
for label in ('class_default', 'native_get'):
    for name in flags:
        cdo, effective = Settings(), Settings()
        cdo.effective = effective
        (cdo if label == 'class_default' else effective).values[name] = True
        configure(cdo)
        expect(label + ': reject enabled ' + name, False)
for value in (None, 0, 'False'):
    cdo = Settings()
    cdo.values[flags[0]] = value
    configure(cdo)
    expect('Reject non-boolean readback ' + repr(value), False)
cdo = Settings()
cdo.effective = None
configure(cdo)
expect('Reject absent native accessor object', False)
cdo.effective = Settings(path='/Script/Other.Settings')
expect('Reject wrong native settings class', False)
cdo.effective = Settings(values={})
expect('Reject unavailable reflected property', False)

# Substitute only the config read, without creating alternate files/projects.
class ConfigFile:
    def __init__(self, data):
        self.data = data

    def read_bytes(self):
        if isinstance(self.data, Exception):
            raise self.data
        return self.data

    def __str__(self):
        return 'offline_config_read'


class ConfigRoot:
    def __init__(self, data):
        self.data = data

    def __truediv__(self, key):
        return ConfigFile(self.data)


configure(Settings())
raw = (ROOT / scope['NATIVE_SETTINGS_CONFIG']).read_bytes()
for label, data in [('Missing correct category file', FileNotFoundError()),
                    ('Wrong section', raw.replace(class_path.encode(), b'/Script/Wrong.Settings')),
                    ('Missing mandatory scalar', raw.replace((flags[0] + '=False').encode(), b''))] + [
                    ('Enabled disk flag ' + n, raw.replace((n+'=False').encode(), (n+'=True').encode())) for n in flags]:
    scope['Path'] = lambda unused, data=data: SimpleNamespace(resolve=lambda: SimpleNamespace(parents=[None, None, ConfigRoot(data)]))
    expect(label, False)
scope['Path'] = Path

failed = [{'revision': 'failed', 'actor_paths': ['failed_actor'], 'unvalidated_mesh_paths': ['mesh_a', 'mesh_b']}]
previous = {'revision': 'saved_1', 'owned_actor_paths': ['old_actor'], 'named_generated_dependency_paths': ['old_dependency']}
history = scope['_retirement_history'](previous, None, failed)
failed.clear()
assert history['unvalidated_previous_mesh_packages_preserved'] == ['mesh_a', 'mesh_b']
assert history['retired_failed_generations'][0]['actor_paths'] == ['failed_actor']
next_delivery = dict(history, revision='saved_2', owned_actor_paths=['new_actor'], named_generated_dependency_paths=['new_dependency'])
second = scope['_retirement_history'](next_delivery, history, [])
assert second['unvalidated_previous_mesh_packages_preserved'] == ['mesh_a', 'mesh_b']
assert len(second['retired_failed_generations']) == 1
assert len(second['retired_successful_generations']) == 2
assert second['retired_successful_generations'][0]['named_generated_dependency_paths'] == ['old_dependency']
observations.append({'case': 'Failed package/actor and successful dependency history survives clearing and repeat generation', 'passed': True})

# Execute the actual early create_road gate with unsafe policy. Native spawn
# is deliberately unreachable; this is Python control-flow proof only.
run_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'RoadBLDRun')
methods = {n.name: n for n in run_class.body if isinstance(n, ast.FunctionDef)}
for name in ('check_landscape_policy', 'create_road', 'verify_owned_landscape_patches'):
    exec(compile(ast.Module(body=[methods[name]], type_ignores=[]), str(SOURCE), 'exec'), scope)
spawn_calls = []
fake = SimpleNamespace(guard=lambda: None, state={}, write=lambda: None,
                       network=SimpleNamespace(add_road_to_road_network=lambda *a: spawn_calls.append(a)))
fake.check_landscape_policy = lambda stage: scope['check_landscape_policy'](fake, stage)
configure(Settings(values={n: True for n in flags}))
try:
    scope['create_road'](fake, {})
except RuntimeError:
    pass
else:
    raise AssertionError('Unsafe authoring did not stop')
assert not spawn_calls
observations.append({'case': 'Unsafe policy stops before native road spawn', 'passed': True})

for enabled in (True, False):
    patch = SimpleNamespace(is_enabled=lambda enabled=enabled: enabled,
                            get_path_name=lambda: 'offline_owned_patch')
    scope['unreal'].LandscapePatchComponent = object()
    fake.owned_actors = lambda: [SimpleNamespace(get_components_by_class=lambda cls: [patch])]
    try:
        scope['verify_owned_landscape_patches'](fake)
    except RuntimeError:
        assert enabled
    else:
        assert not enabled
    observations.append({'case': 'Owned patch enabled=' + str(enabled), 'passed': True})

# Review call order and preservation without executing native implementation.
dispatch = ast.unparse(methods['request_rebuild'])
assert dispatch.index("check_landscape_policy('rebuild_dispatch')") < dispatch.index("_tool('RoadBLDBuildToolset', 'Rebuild'")
assert 'set_is_enabled' not in ast.unparse(tree)
assert "check_landscape_policy('rebuild_completed')" in ast.unparse(methods['tick'])
assert "check_landscape_policy('native_validation')" in ast.unparse(methods['_validate_native'])
junctions = ast.parse((ROOT/'Content/Python/geocity_roadbld_junctions.py').read_bytes())
assert "check_landscape_policy('junction_authoring')" in ast.unparse(junctions)
prior = ast.parse((OUT/'Before/geocity_roadbld_workflow.py').read_bytes())
before_class = next(n for n in prior.body if isinstance(n, ast.ClassDef) and n.name == 'RoadBLDRun')
before_methods = {n.name: n for n in before_class.body if isinstance(n, ast.FunctionDef)}
unchanged = ['build_presets', 'validate_preset', 'check_road', 'validate_mesh_footprints',
             'clip_final_geometry', 'validate', 'staged_contract', 'fail']
for name in unchanged:
    assert ast.dump(before_methods[name], include_attributes=False) == ast.dump(methods[name], include_attributes=False), name
syntax = []
for source in sorted((ROOT/'Content/Python').glob('geocity_roadbld_*.py')):
    compile(source.read_bytes(), str(source), 'exec', dont_inherit=True)
    syntax.append(source.name)
result = {'status': 'PASSED_OFFLINE_SOURCE_CHECKS', 'cases': observations,
          'syntax_valid': syntax, 'unchanged_geometry_appearance_transaction_methods': unchanged,
          'rebuild_dispatch_gate_before_native_call': True, 'posthoc_patch_disable_removed': True,
          'native_editor_calls': 0, 'unreal_imports': 0,
          'limits': 'Native Get/config binding, terrain-write prevention, geometry, UObject lifetime, rollback fidelity, Lit appearance and persistence remain unverified.'}
(OUT/'SOURCE_CHECKS.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({'status': result['status'], 'policy_cases': len(observations), 'syntax_modules': len(syntax)}))
