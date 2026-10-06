"""OFFLINE companion of s1v2a_material_edit.py. Never imports unreal; writes only new files under S1v2.

  python -B s1v2a_material_edit_offline.py selftest
      For EVERY macro_noise_source ('macro_variation', 'mw_noise', 'perlin'): builds MF_GeoCityV2a_MacroColor and
      the master change (one BaseColor switch + params + one MF call) against a MOCK engine whose pin/output
      names are MEASURED from the baseline describe() dump (S1_Prep/receipts/GRAPH_BEFORE_23156.json:
      WorldPosition outputs XYZ/XY/Z, TextureSample TMVM_NONE pins, StaticSwitch True/False, MF call outputs).
      Checks: every link names an existing pin/output, required pins connected, float dimensions consistent,
      3 Shared:Wrap TMVM_NONE fetches of the source's sampler type, no existing node received an input link,
      only the BaseColor root is bound. A NUMERIC evaluation of the mock MF graph then proves:
      master defaults -> Color == Base exactly; t001 child values -> brightness and R/B ranges.
      Also: baseline-dump checks and the AST scan below. Proves Python wiring/maths only, not engine behaviour.
  python -B s1v2a_material_edit_offline.py scan
      AST scan: save_packages only in save()/child_save() with the named lists; inspect/apply/tune/verify cannot
      reach a save; no delete/save_assets/prepare/verify_landscape calls; connect_material_property only in
      apply(); links only through Builder.link; instance setters only in apply/tune.
  python -B s1v2a_material_edit_offline.py expectations <args.json> <out.json>
      Writes the expectations JSON for the implemented design plus the args' child values and noise source.
"""
import ast
import hashlib
import importlib.util
import json
import math
import os
import random
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent                 # .../Stage1_Ground/S1v2
STAGE = HERE.parent
TARGET = HERE / 's1v2a_material_edit.py'
STATS = HERE / 'NOISE_STATS_v2a.json'
SPEC_D2 = STAGE / 'S1_Prep' / 'S1_MINIMAL_SAFE_SPEC.json'       # read-only (master/children/baseline blocks)
GRAPH_BEFORE = STAGE / 'S1_Prep' / 'receipts' / 'GRAPH_BEFORE_23156.json'  # read-only baseline dump (605c55d0)
SOURCES = ('macro_variation', 'mw_noise', 'perlin')
# t001 child values (manager v2a order): ValueAmount 0.07, HueGain 0.30, symmetric hue endpoints a = 0.034
# chosen so that R/B = 1.05 at the +2 sigma clamp: (1 + 0.725 a) / (1 - 0.725 a) = 1.05 with 2t-1 = 0.3 * 2 * 1.2083.
T001 = {'ValueAmount': 0.07, 'HueGain': 0.30, 'HueA': (1.034, 1.0, 0.966, 1.0), 'HueB': (0.966, 1.0, 1.034, 1.0)}


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_target():
    assert 'unreal' not in sys.modules, 'offline only'
    os.environ.pop('GEOCITY_S1_ARGS', None)
    spec = importlib.util.spec_from_file_location('s1v2a_material_edit_offline_copy', TARGET)
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    assert module.RESULT.get('idle') is True and 'unreal' not in sys.modules
    return module


# ------------------------------------------------------------------ mock engine
class Owner:
    def __init__(self, name):
        self.name, self.nodes = name, []


class Expr:
    CLASS, INPUTS, OUTPUTS = 'MaterialExpression', (), ('',)

    def __init__(self, owner):
        self.owner, self.props, self.edges = owner, {}, {}
        self.index = len(owner.nodes)

    def get_class(self):
        return types.SimpleNamespace(get_name=lambda: self.CLASS)

    def get_name(self):
        return '%s_%d' % (self.CLASS.replace('MaterialExpression', ''), self.index)

    def set_editor_property(self, key, value):
        self.props[key] = value

    def get_editor_property(self, key):
        return self.props[key]

    def input_names(self):
        return list(self.INPUTS)

    def output_names(self):
        return list(self.OUTPUTS)


def cls(name, inputs=(), outputs=('',)):
    return type(name, (Expr,), {'CLASS': 'MaterialExpression' + name, 'INPUTS': tuple(inputs), 'OUTPUTS': tuple(outputs)})


AB, ONE = ('A', 'B'), ('None',)
RGBA_OUT = ('RGB', 'R', 'G', 'B', 'A', 'RGBA')
CLASSES = {n: cls(n, AB) for n in ('Multiply', 'Add', 'Subtract', 'Divide', 'Max', 'DotProduct', 'AppendVector')}
CLASSES.update({n: cls(n, ONE) for n in ('Saturate', 'OneMinus', 'ComponentMask')})
CLASSES.update({
    'Normalize': cls('Normalize', ('VectorInput',)), 'Clamp': cls('Clamp', ('None', 'Min', 'Max')),
    'LinearInterpolate': cls('LinearInterpolate', ('A', 'B', 'Alpha')),
    'SmoothStep': cls('SmoothStep', ('Min', 'Max', 'Value')),
    'Constant2Vector': cls('Constant2Vector', (), ('', 'R', 'G')),
    'Constant3Vector': cls('Constant3Vector', (), ('', 'R', 'G', 'B')),
    'TextureSample': cls('TextureSample', ('UVs', 'Tex', 'Apply View MipBias'), RGBA_OUT),  # M: TMVM_NONE pins
    'WorldPosition': cls('WorldPosition', (), ('XYZ', 'XY', 'Z')),                         # M: WorldPosition_0
    'FunctionInput': cls('FunctionInput', ('Preview',)), 'FunctionOutput': cls('FunctionOutput', ('None',), ()),
    'ScalarParameter': cls('ScalarParameter'), 'VectorParameter': cls('VectorParameter', (), RGBA_OUT),
    'TextureObjectParameter': cls('TextureObjectParameter', ('UVs', 'Apply View MipBias')),
    'StaticSwitchParameter': cls('StaticSwitchParameter', ('True', 'False')),
})


class FunctionCall(Expr):
    CLASS = 'MaterialExpressionMaterialFunctionCall'

    def _nodes(self, kind):
        fn = self.props['material_function']
        rows = [n for n in fn.nodes if n.CLASS == 'MaterialExpression' + kind]
        return sorted(rows, key=lambda n: n.props['sort_priority'])

    def input_names(self):
        return [n.props['input_name'] for n in self._nodes('FunctionInput')]

    def output_names(self):
        return [n.props['output_name'] for n in self._nodes('FunctionOutput')]


class Anchor(Expr):
    """An EXISTING master node: its edges must stay {} (nothing may link INTO an existing node)."""
    CLASS = 'MaterialExpressionAnchor'

    def __init__(self, owner, name, outputs, dim):
        super().__init__(owner)
        self.name, self.OUTPUTS, self.dim = name, tuple(outputs), dim

    def get_name(self):
        return self.name

    def input_names(self):
        return ['ExistingPin']


class MockLib:
    links = 0

    @staticmethod
    def _create(owner, kind, x, y):
        e = kind(owner)
        e.props.update(material_expression_editor_x=x, material_expression_editor_y=y)
        owner.nodes.append(e)
        return e

    create_material_expression = _create
    create_material_expression_in_function = _create

    @staticmethod
    def get_material_expression_input_names(e):
        return e.input_names()

    @staticmethod
    def get_material_expression_output_names(e):
        return e.output_names()

    @staticmethod
    def connect_material_expressions(src, output, dst, pin):
        assert pin in dst.input_names() and (output in src.output_names() or (output == '' and src.output_names()))
        dst.edges[pin] = (src, output)
        MockLib.links += 1
        return True


def mock_unreal():
    names = {'MaterialExpression' + k: v for k, v in CLASSES.items()}
    names.update(MaterialExpressionMaterialFunctionCall=FunctionCall)
    u = types.SimpleNamespace(**names)
    u.Name = str
    u.LinearColor = lambda *v: tuple(float(x) for x in v)
    u.TextureMipValueMode = types.SimpleNamespace(TMVM_NONE='TMVM_NONE')
    u.Texture = object
    u.load_asset = lambda path: object()
    return u


def bind_mock(m):
    m.unreal, m.LIB = mock_unreal(), MockLib
    m.WRAP = 'SSM_WRAP_WORLD_GROUP_SETTINGS'
    m.SAMPLER.update({k: v for k, v in m.SAMPLER_NAMES.items()})
    m.FIN.update({k: v for k, v in m.FIN_NAMES.items()})
    m.ROOT_PROPS.update({k: v for k, v in m.ROOT_PROP_NAMES.items()})
    m.MIP.update({k: v for k, v in m.MIP_NAMES.items()})


# ------------------------------------------------------------------ dimension inference
FIN_DIM = {'FUNCTION_INPUT_SCALAR': 1, 'FUNCTION_INPUT_VECTOR2': 2, 'FUNCTION_INPUT_VECTOR3': 3,
           'FUNCTION_INPUT_TEXTURE2D': 'tex'}
DECL_DIM = {'S': 1, 'V2': 2, 'V3': 3, 'T2D': 'tex'}


def combine(a, b, where):
    if a == b or b is None:
        return a
    if a is None:
        return b
    assert 'tex' not in (a, b), ('texture used as a value', where)
    if a == 1:
        return b
    if b == 1:
        return a
    raise AssertionError(('dimension mismatch %s vs %s' % (a, b), where))


class Dims:
    def __init__(self, function_specs):
        self.memo, self.function_specs = {}, function_specs

    def of(self, source):
        e, output = source
        key = (id(e), output)
        if key not in self.memo:
            self.memo[key] = self._dim(e, output)
        return self.memo[key]

    def pin(self, e, name):
        return self.of(e.edges[name]) if name in e.edges else None

    def _dim(self, e, output):
        c, where = e.CLASS.replace('MaterialExpression', ''), e.get_name()
        if c == 'Anchor':
            return e.dim
        if c == 'ScalarParameter':
            return 1
        if c in ('VectorParameter', 'TextureSample'):
            if c == 'TextureSample':
                assert self.pin(e, 'UVs') == 2 and self.pin(e, 'Tex') == 'tex', ('bad sample inputs', where)
            return {'RGB': 3, 'RGBA': 4, '': 3}.get(output, 1)
        if c == 'TextureObjectParameter':
            return 'tex'
        if c == 'WorldPosition':
            return {'XYZ': 3, 'XY': 2, 'Z': 1}[output]
        if c == 'Constant2Vector':
            return 2 if output == '' else 1
        if c == 'Constant3Vector':
            return 3 if output == '' else 1
        if c == 'FunctionInput':
            return FIN_DIM[e.props['input_type']]
        if c == 'ComponentMask':
            source = self.pin(e, 'None')
            count = sum(bool(e.props.get(k)) for k in 'rgba')
            assert count >= 1 and source != 'tex' and count <= source, ('mask wider than input', where)
            return count
        if c == 'AppendVector':
            return self.pin(e, 'A') + self.pin(e, 'B')
        if c == 'DotProduct':
            assert self.pin(e, 'A') == self.pin(e, 'B'), ('dot dims', where)
            return 1
        if c in ('Multiply', 'Add', 'Subtract', 'Divide', 'Max'):
            a = self.pin(e, 'A') if 'A' in e.edges else 1
            b = self.pin(e, 'B') if 'B' in e.edges else 1
            return combine(a, b, where)
        if c == 'LinearInterpolate':
            a = self.pin(e, 'A') if 'A' in e.edges else 1
            out = combine(a, self.pin(e, 'B'), where)
            return combine(out, self.pin(e, 'Alpha'), where + ':Alpha')
        if c in ('Saturate', 'Clamp'):
            return self.pin(e, 'None')
        if c == 'StaticSwitchParameter':
            return combine(self.pin(e, 'True'), self.pin(e, 'False'), where)
        if c == 'MaterialFunctionCall':
            fn = e.props['material_function']
            spec = self.function_specs[fn.name]
            for pin, kind in spec['inputs']:
                got, want = self.pin(e, pin), DECL_DIM[kind]
                assert got == want or (got == 1 and want in (2, 3)), ('call input dims', where, pin, got, want)
            return DECL_DIM[dict(spec['outputs'])[output]]
        raise AssertionError(('no dim rule', c))


def required_pins(e):
    names, p = e.input_names(), e.props
    optional = {'Apply View MipBias', 'Preview'}
    if 'const_a' in p:
        optional.add('A')
    if 'const_b' in p:
        optional.add('B')
    if e.CLASS.endswith('Clamp'):
        optional.update({'Min', 'Max'})
    if e.CLASS.endswith('TextureObjectParameter'):
        optional.add('UVs')
    return [n for n in names if n not in optional]


def check_connected(owner):
    missing = [(e.get_name(), n) for e in owner.nodes for n in required_pins(e) if n not in e.edges]
    assert not missing, ('unconnected required pins', owner.name, missing[:20])


# ------------------------------------------------------------------ numeric evaluation of the mock MF graph
def vec(x):
    return tuple(x) if isinstance(x, (tuple, list)) else (float(x),)


def bc(a, b, op):
    a, b = vec(a), vec(b)
    n = max(len(a), len(b))
    a = a * n if len(a) == 1 else a
    b = b * n if len(b) == 1 else b
    assert len(a) == len(b) == n
    out = tuple(op(x, y) for x, y in zip(a, b))
    return out[0] if n == 1 else out


class Evaluator:
    """Evaluates the mock function graph in double precision. inputs: {pin: value}; sampler(label, uv) -> RGBA."""

    def __init__(self, inputs, sampler, world_xyz):
        self.inputs, self.sampler, self.world = inputs, sampler, world_xyz

    def of(self, source):
        e, output = source
        c = e.CLASS.replace('MaterialExpression', '')
        p = e.props
        pin = lambda name: self.of(e.edges[name])
        if c == 'FunctionInput':
            return self.inputs[p['input_name']]
        if c == 'WorldPosition':
            return {'XYZ': self.world, 'XY': self.world[:2], 'Z': self.world[2]}[output]
        if c == 'ComponentMask':
            x = vec(pin('None'))
            out = tuple(x[i] for i, k in enumerate('rgba') if p.get(k))
            return out[0] if len(out) == 1 else out
        if c == 'Constant2Vector':
            return (p['r'], p['g']) if output == '' else {'R': p['r'], 'G': p['g']}[output]
        if c == 'TextureSample':
            rgba = self.sampler(p['desc'], pin('UVs'))
            return {'RGB': rgba[:3], 'R': rgba[0], 'G': rgba[1], 'B': rgba[2], 'A': rgba[3], 'RGBA': rgba}[output]
        a = pin('A') if 'A' in e.edges else p.get('const_a')
        b = pin('B') if 'B' in e.edges else p.get('const_b')
        if c == 'Multiply':
            return bc(a, b, lambda x, y: x * y)
        if c == 'Add':
            return bc(a, b, lambda x, y: x + y)
        if c == 'Subtract':
            return bc(a, b, lambda x, y: x - y)
        if c == 'Divide':
            return bc(a, b, lambda x, y: x / y)
        if c == 'Max':
            return bc(a, b, max)
        if c == 'DotProduct':
            return sum(x * y for x, y in zip(vec(a), vec(b)))
        if c == 'AppendVector':
            return vec(a) + vec(b)
        if c == 'Clamp':
            return bc(pin('None'), 0.0, lambda x, _: min(max(x, p['min_default']), p['max_default']))
        if c == 'Saturate':
            return bc(pin('None'), 0.0, lambda x, _: min(max(x, 0.0), 1.0))
        if c == 'LinearInterpolate':
            t = pin('Alpha')
            d = bc(b, a, lambda x, y: x - y)
            return bc(a, bc(d, t, lambda x, y: x * y), lambda x, y: x + y)
        raise AssertionError(('no eval rule', c))


def evaluate(m, fn, values, sampler, world):
    out = [n for n in fn.nodes if n.CLASS.endswith('FunctionOutput')][0]
    return Evaluator(values, sampler, world).of(out.edges['None'])


def numeric_checks(m, fn, source):
    row = m.NOISE_SOURCES[source]
    rng = random.Random(20261006)
    base_inputs = {'NoiseTex': None, 'Tile1Cm': m.OCTAVES[0][2], 'Tile2Cm': m.OCTAVES[1][2], 'Tile3Cm': m.OCTAVES[2][2],
                   'Mean': tuple(row['mean']), 'InvStd': tuple(row['inv_std'])}
    identity_max = 0.0
    for _ in range(300):  # master defaults: Color == Base exactly for any noise / position / base
        world = (rng.uniform(-2e5, 2e5), rng.uniform(-2e5, 2e5), rng.uniform(0, 5e3))
        base = tuple(rng.uniform(0.0, 1.2) for _ in range(3))
        noise = tuple(rng.random() for _ in range(4))
        values = dict(base_inputs, Base=base, ValueAmount=0.0, HueGain=0.0, HueA=(1.0, 1.0, 1.0), HueB=(1.0, 1.0, 1.0))
        color = evaluate(m, fn, values, lambda label, uv: noise, world)
        identity_max = max(identity_max, max(abs(x - y) for x, y in zip(color, base)))
    assert identity_max == 0.0, ('master defaults are not an exact identity', identity_max)
    child = dict(base_inputs, Base=(0.3, 0.3, 0.3), ValueAmount=T001['ValueAmount'], HueGain=T001['HueGain'],
                 HueA=T001['HueA'][:3], HueB=T001['HueB'][:3])
    lo = tuple(row['mean'][k] - 10.0 * row['std'][k] for k in range(3))  # far below: clamps at -2 sigma_V
    hi = tuple(row['mean'][k] + 10.0 * row['std'][k] for k in range(3))
    rows = {}
    for label, noise in (('mean', tuple(row['mean']) + (1.0,)), ('low', lo + (1.0,)), ('high', hi + (1.0,))):
        c = evaluate(m, fn, child, lambda _l, _uv, n=noise: n, (1234.0, -5678.0, 0.0))
        rows[label] = {'color': [round(x, 6) for x in c], 'luma_factor': round(sum(w * x for w, x in zip(m.LUMA, c)) / 0.3, 6),
                       'r_over_b': round(c[0] / c[2], 6)}
    assert abs(rows['mean']['r_over_b'] - 1.0) < 1e-9 and abs(rows['mean']['luma_factor'] - 1.0) < 1e-9, rows['mean']
    assert 1.049 < rows['high']['r_over_b'] < 1.052 and 0.949 < rows['low']['r_over_b'] < 0.952, rows
    return {'master_defaults_identity_max_abs_error': identity_max, 't001_extremes': rows,
            'brightness_cap': round(T001['ValueAmount'] * m.CLAMP_V, 6)}


# ------------------------------------------------------------------ baseline-dump checks
def baseline_check(m):
    dump = json.loads(GRAPH_BEFORE.read_text(encoding='utf-8'))
    nodes, roots = dump['nodes'], dump['roots']
    assert dump['graph_sha256'] == m.BASELINE['graph_sha256'] and len(nodes) == m.BASELINE['node_count']
    for key, suffix in m.ROOT_LLB.items():
        assert roots[key].endswith(':MaterialExpression' + suffix), key
    assert nodes[roots['color']]['output_names'] == [''], 'LLB_6 output names'
    textures = sorted({r['properties']['texture'] for r in nodes.values() if r['properties'].get('texture')})
    for source, row in m.NOISE_SOURCES.items():
        assert row['master_texture'] in textures, ('master default texture is not referenced by the master', source)
    child_only = sorted({row['child_texture'] for row in m.NOISE_SOURCES.values()} - set(textures))
    wp = [r for r in nodes.values() if r['class'] == 'MaterialExpressionWorldPosition']
    assert wp and wp[0]['output_names'] == ['XYZ', 'XY', 'Z'], 'WorldPosition outputs'
    stats = json.loads(STATS.read_text(encoding='utf-8'))['textures']
    names = {'macro_variation': 'T_MacroVariation', 'mw_noise': 'TEX_MW_Noise_msk', 'perlin': 'T_Perlin_Noise_M'}
    for source, row in m.NOISE_SOURCES.items():
        measured = stats[names[source]]
        assert list(row['mean']) == measured['mean_rgb'] and list(row['inv_std']) == measured['inv_std_rgb'], source
        assert list(row['std']) == measured['std_rgb'] and list(row['block256_std']) == measured['block_mean_std']['mip8_block256_std']
        assert measured['package'] == row['child_texture'] and measured['sampler'] == row['sampler'], source
    return {'graph_sha256': dump['graph_sha256'], 'root_color': roots['color'].split(':')[-1],
            'child_only_textures': child_only, 'noise_stats_file': str(STATS), 'noise_stats_sha256': sha_file(STATS),
            'status': 'BASELINE_DUMP_AND_NOISE_STATS_MATCH'}


# ------------------------------------------------------------------ selftest
def build(m, source):
    MockLib.links = 0
    m.set_noise_source(source)
    kind = m.NOISE_SOURCES[source]['sampler']
    report = {'functions': {}, 'master': {}}
    functions = {}
    for name, spec in m.FUNCTIONS.items():
        fn = Owner(name)
        g = m.Builder(fn, True, -1600, 0, 8)
        _, outputs = m.build_function_graph(g, name, spec, ())
        check_connected(fn)
        dims = Dims({})
        for pin, decl in spec['outputs']:
            got = dims.of(outputs[pin].edges['None'])
            assert got == DECL_DIM[decl], (name, pin, got)
        samples = [e for e in fn.nodes if e.CLASS.endswith('TextureSample')]
        for e in samples:
            dims.of((e, 'RGB'))
        assert len(samples) == 3 == sum(spec['samples'].values()), name
        assert all(e.props['sampler_type'] == m.SAMPLER[kind] and e.props['sampler_source'] == m.WRAP
                   and e.props['mip_value_mode'] == 'TMVM_NONE' for e in samples), name
        assert sum(e.CLASS.endswith('WorldPosition') for e in fn.nodes) == 1, name
        assert all(e.props['desc'].startswith(m.MARK) for e in fn.nodes), name
        assert not [e for e in fn.nodes if 'Parameter' in e.CLASS], name
        functions[name] = fn
        report['functions'][name] = {'nodes': len(fn.nodes), 'samples': len(samples), 'sampler': kind,
                                     'inputs': [p for p, _ in spec['inputs']], 'outputs': [p for p, _ in spec['outputs']],
                                     'numeric': numeric_checks(m, fn, source)}
    master, old = Owner('M_SurfaceBank_Natural'), Owner('existing')
    llb6 = Anchor(old, 'LandscapeLayerBlend_6', ('',), 3)
    anchors = {'base_color': (llb6, '')}
    g = m.Builder(master, False, -4000, 36000, 10)
    switches = {}
    for key in m.ROOT_PROPS:  # same calls as apply()'s probe
        switches[key] = g.node(m.unreal.MaterialExpressionStaticSwitchParameter, 'Enable' + key.title(),
                               parameter_name=m.SWITCH, default_value=False, group='GeoCity_S1')
        assert sorted(MockLib.get_material_expression_input_names(switches[key])) == ['False', 'True']
        m.Builder.link(llb6, switches[key], 'True')
        m.Builder.link(llb6, switches[key], 'False')
    P = m.make_params(g)
    branch = m.build_branch(g, anchors, P, functions)
    for key in m.ROOT_PROPS:
        m.Builder.link(branch['finals'][key], switches[key], 'True')
    check_connected(master)
    assert not [a.get_name() for a in old.nodes if a.edges], 'An existing node received an input link'
    assert list(m.ROOT_PROPS) == ['color'], 'only the BaseColor root may be rebound'
    dims = Dims(m.FUNCTIONS)
    assert dims.of((switches['color'], '')) == 3
    assert switches['color'].edges['False'] == (llb6, '') and switches['color'].edges['True'] == (branch['call'], 'Color')
    nodes = master.nodes
    classes = {}
    for e in nodes:
        classes[e.CLASS] = classes.get(e.CLASS, 0) + 1
    assert not [e for e in nodes if e.CLASS.endswith('TextureSample')], 'master-level texture samples'
    calls = [e for e in nodes if e.CLASS.endswith('MaterialFunctionCall')]
    assert [c.props['material_function'].name for c in calls] == ['MF_GeoCityV2a_MacroColor']
    params = [e.props['parameter_name'] for e in nodes if 'Parameter' in e.CLASS]
    assert sorted(params) == sorted(m.PARAMS) and len(params) == len(m.PARAMS) == 11
    tex = [e for e in nodes if e.CLASS.endswith('TextureObjectParameter')]
    assert len(tex) == 1 and tex[0].props['sampler_type'] == m.SAMPLER[kind] and tex[0].props['sampler_source'] == m.WRAP
    assert all(e.props['desc'].startswith(m.MARK) and not e.props['desc'].startswith(m.GRASS_OWNER) for e in nodes)
    xs = [e.props['material_expression_editor_x'] for e in nodes]
    assert min(xs) >= -4000 and max(xs) <= -1840
    report['master'] = {'added_node_count': len(nodes), 'function_calls': [c.props['material_function'].name for c in calls],
                        'new_samples': 3, 'parameter_names': len(set(params)), 'class_counts': dict(sorted(classes.items())),
                        'links': MockLib.links, 'existing_nodes_with_new_input_links': 0, 'roots_rebound': ['color']}
    return report


def selftest():
    m = load_target()
    bind_mock(m)
    report = {'target': str(TARGET), 'target_sha256': sha_file(TARGET), 'sources': {}}
    for source in SOURCES:
        report['sources'][source] = build(m, source)
    m.set_noise_source('macro_variation')
    report['baseline'] = baseline_check(m)
    report['scan'] = scan()
    report['status'] = 'SELFTEST_PASSED_MOCK_ENGINE'
    report['scope'] = ('Python wiring/pin-name/dimension logic and the MF maths only; engine behaviour (pin names '
                       'inside MFs, LWC WorldPosition maths, compile, switch propagation) is asserted at run time.')
    return m, report


# ------------------------------------------------------------------ AST scan
FORBIDDEN = ('save_assets', 'save_asset', 'save_loaded_asset', 'save_loaded_assets', 'save_dirty_packages',
             'save_directory', 'save_current_level', 'save_map', 'save_all_dirty_levels', 'delete_asset',
             'delete_loaded_asset', 'delete_directory', 'delete_material_expression',
             'delete_material_expression_in_function', 'delete_all_material_expressions',
             'delete_all_material_expressions_in_function', 'prepare', 'verify_landscape', 'rename_asset',
             'duplicate_asset', 'consolidate_assets', 'disconnect_material_property')
SAVE_GROUPS = ("groups = [('functions', [FUNCTION_DIR + '/' + n for n in FUNCTIONS]), ('master', [MASTER]),\n"
               "              ('children', [CHILDREN[area]])]")


def scan():
    src = TARGET.read_text(encoding='utf-8')
    tree = ast.parse(src)
    calls_by_fn, sites = {}, {}
    for top in tree.body:
        if isinstance(top, ast.ClassDef):
            members = [(top.name + '.' + f.name, f) for f in top.body if isinstance(f, ast.FunctionDef)]
        elif isinstance(top, ast.FunctionDef):
            members = [(top.name, top)]
        else:
            members = [('<module>', top)]
        for name, node in members:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    f = sub.func
                    called = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else None)
                    if called:
                        sites.setdefault(called, []).append((name, sub.lineno))
                        calls_by_fn.setdefault(name, set()).add(called)
    bad = {k: v for k, v in sites.items() if k in FORBIDDEN}
    assert not bad, ('Forbidden calls', bad)
    saves = sites.get('save_packages', [])
    assert sorted({n for n, _ in saves}) == ['child_save', 'save'] and len(saves) == 2, ('save_packages sites', saves)
    save_fn = next(f for f in tree.body if isinstance(f, ast.FunctionDef) and f.name == 'save')
    seg = ast.get_source_segment(src, next(s for s in ast.walk(save_fn) if isinstance(s, ast.Assign)
                                           and getattr(s.targets[0], 'id', None) == 'groups'))
    assert seg == SAVE_GROUPS, ('save() named list differs', seg)
    child_fn = next(f for f in tree.body if isinstance(f, ast.FunctionDef) and f.name == 'child_save')
    child_src = ast.get_source_segment(src, child_fn)
    assert "package = unreal.load_asset(child_path).get_outermost()" in child_src
    assert "save_packages([package], False)" in child_src and "child_path = CHILDREN[area]" in child_src
    for name, line in saves:
        call = next(s for s in ast.walk(tree) if isinstance(s, ast.Call) and getattr(s, 'lineno', 0) == line
                    and getattr(s.func, 'attr', '') == 'save_packages')
        assert len(call.args) == 2 and isinstance(call.args[1], ast.Constant) and call.args[1].value is False, (name, line)

    def closure(start):
        seen, stack = set(), [start]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(c for c in calls_by_fn.get(cur, ()) if c in calls_by_fn)
        return seen
    for mode in ('inspect', 'apply', 'tune', 'verify'):
        reach = closure(mode)
        assert not ({'save', 'child_save'} & reach), (mode, 'can reach a save')
        assert 'save_packages' not in set().union(*(calls_by_fn.get(f, set()) for f in reach)), (mode, 'save_packages')
    props = sites.get('connect_material_property', [])
    assert [n for n, _ in props] == ['apply'], ('connect_material_property sites', props)
    links = sites.get('connect_material_expressions', [])
    assert [n for n, _ in links] == ['Builder.link'], ('connect_material_expressions sites', links)
    setter_names = ('set_material_instance_scalar_parameter_value', 'set_material_instance_vector_parameter_value',
                    'set_material_instance_texture_parameter_value', 'set_material_instance_static_switch_parameter_value',
                    'set_material_instance_parent')
    setters = sorted({n for k in setter_names for n, _ in sites.get(k, [])})
    assert set(setters) <= {'apply', 'tune'}, setters
    return {'status': 'AST_SCAN_PASSED', 'save_packages_sites': saves, 'connect_material_property_sites': props,
            'link_sites': links, 'instance_setter_functions': setters, 'forbidden_checked': list(FORBIDDEN),
            'save_named_list': SAVE_GROUPS}


# ------------------------------------------------------------------ expectations
def expectations(args_file, out_file):
    m, report = selftest()
    args = json.loads(Path(args_file).read_text(encoding='utf-8-sig'))
    d2 = json.loads(SPEC_D2.read_text(encoding='utf-8'))
    source = m.noise_source(args)
    m.set_noise_source(source)
    plans = m.plan_children(args, {})
    areas = sorted(args['child_values'])
    kind_map = {'switch': 'static_switch', 'scalar': 'scalar', 'vector': 'vector'}
    params = []
    for name, (kind, default, sampler) in m.PARAMS.items():
        entry = {'name': name, 'kind': kind_map.get(kind, 'texture_' + str(sampler).lower()),
                 'master_default': list(default) if kind == 'vector' else default}
        for area in areas:
            values = args['child_values'][area]
            if kind == 'switch':
                value = True
            elif kind == 'texture':
                value = m.obj_path(values.get('textures', {}).get(name, default))
            elif kind == 'vector':
                value = list(values.get('vectors', {}).get(name, default))
            else:
                value = values.get('scalars', {}).get(name, default)
            entry[area] = value
        params.append(entry)
    fspec = m.FUNCTIONS['MF_GeoCityV2a_MacroColor']
    src_report = report['sources'][source]
    result = {
        'schema': 'environmentpipeline.stage1_s1_minimal_safe_spec.v1',
        'schema_note': 'v1 expectations schema reused for review; S1_Prep/s1_verify.py post_s1 cannot consume v2a receipts.',
        'variant': 's1v2a',
        'status': 'IMPLEMENTED_DESIGN_EXPECTATIONS_NOT_EXECUTED',
        'generated_by': {'file': str(Path(__file__).resolve()), 'file_sha256': sha_file(Path(__file__).resolve()),
                         'target': str(TARGET), 'target_sha256': sha_file(TARGET),
                         'args_file': str(Path(args_file).resolve()), 'args_sha256': sha_file(args_file),
                         'noise_stats': str(STATS), 'noise_stats_sha256': sha_file(STATS)},
        'design_notes': ('S1v2a (manager order after CODEX_DESIGN_REVIEW.md section 5): one BaseColor static switch; '
                         'True = MF_GeoCityV2a_MacroColor(LandscapeLayerBlend_6). Every existing chain, weight blend, '
                         'Grass node and the Normal/Roughness/AO roots untouched. Values = the args child values (t001), '
                         'i.e. the state that would be saved.'),
        'macro_noise_source': source,
        'noise_stats_used': m.noise_record(plans),
        'master': d2['master'], 'base_mi_untouched': d2['base_mi_untouched'], 'children': d2['children'],
        'new_function_packages': [m.FUNCTION_DIR + '/' + n for n in m.FUNCTIONS],
        'function_packages_must_be_absent': [m.FUNCTION_DIR + '/' + n for n in m.V1_FUNCTIONS + m.V2_DRAFT_FUNCTIONS],
        'functions': {'MF_GeoCityV2a_MacroColor': {
            'inputs': ['%s:%s' % p for p in fspec['inputs']], 'outputs': ['%s:%s' % p for p in fspec['outputs']],
            'texture_samples': 3, 'sampler_type': m.SAMPLER_NAMES[m.NOISE_SOURCES[source]['sampler']],
            'sampler_source': 'SSM_WRAP_WORLD_GROUP_SETTINGS', 'mip_value_mode': 'TMVM_NONE',
            'nodes_mock': src_report['functions']['MF_GeoCityV2a_MacroColor']['nodes'],
            'numeric': src_report['functions']['MF_GeoCityV2a_MacroColor']['numeric']}},
        'node_desc_prefix': m.MARK, 'canvas': {'x': [-4000, -1840], 'y_min': 36000},
        'new_parameters': params, 'new_parameter_names': len(params),
        'new_landscape_layer_samples': [], 'new_llbs': {'count': 0},
        'static_switch_nodes': {'name': m.SWITCH, 'count': 1, 'default': False,
                                'False_pin_sources': [m.ROOT_LLB['color']], 'roots': ['MP_BASE_COLOR'],
                                'untouched_roots': ['MP_NORMAL <- LandscapeLayerBlend_7', 'MP_ROUGHNESS <- LandscapeLayerBlend_8',
                                                    'MP_AMBIENT_OCCLUSION <- LandscapeLayerBlend_0']},
        'switch_pins': {'true': 'True', 'false': 'False'},
        'added_node_count': src_report['master']['added_node_count'],
        'function_calls': src_report['master']['function_calls'],
        'allowed_sampler_sources': ['SSM_WRAP_WORLD_GROUP_SETTINGS'],
        'existing_param_child_overrides': {'both_children': {}, 'per_area': {a: {} for a in areas}},
        'grass_coverage': args.get('grass_coverage'),
        'sampler_estimate': {'new_samples': 3, 'direct_master_samples': 0, 'new_sampler_states': 0, 'iran_change': 0},
        'expected_dirty_after_apply': sorted([m.FUNCTION_DIR + '/' + n for n in m.FUNCTIONS] + [m.MASTER]
                                             + [m.CHILDREN[a] for a in areas]),
        'named_save_list': {'functions': [m.FUNCTION_DIR + '/' + n for n in m.FUNCTIONS], 'master': [m.MASTER],
                            'children': [m.CHILDREN[a] for a in areas]},
        'baseline_expectations': d2['baseline_expectations'],
        'plans': plans,
        'selftest': report,
    }
    out = Path(out_file).resolve()
    assert out.parent == HERE and not out.exists(), 'Writes only new files directly under S1v2'
    out.write_text(json.dumps(result, indent=1), encoding='utf-8')
    return {'file': str(out), 'sha256': sha_file(out), 'parameters': len(params), 'source': source,
            'added_node_count': result['added_node_count'], 'new_samples': 3}


if __name__ == '__main__':
    if sys.argv[1:2] == ['selftest']:
        print(json.dumps(selftest()[1], indent=1))
    elif sys.argv[1:2] == ['scan']:
        print(json.dumps(scan(), indent=1))
    elif sys.argv[1:2] == ['expectations'] and len(sys.argv) == 4:
        print(json.dumps(expectations(sys.argv[2], sys.argv[3]), indent=1))
    else:
        raise SystemExit(__doc__)
