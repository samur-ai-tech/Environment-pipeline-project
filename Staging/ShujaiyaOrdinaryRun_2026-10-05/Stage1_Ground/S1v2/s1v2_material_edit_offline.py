"""OFFLINE companion of s1v2_material_edit.py. Never imports unreal; writes only new files under S1v2.

  python -B s1v2_material_edit_offline.py selftest
      For BOTH cell_sample_mip_mode values ('derivative', 'gradient_free'): builds the 5 MF graphs and the
      full master branch (probe switches + params + branch) against a MOCK engine whose pin/output names are
      MEASURED from the baseline describe() dump (S1_Prep/receipts/GRAPH_BEFORE_23156.json: TextureSample
      'DDX(UVs)'/'DDY(UVs)' pins exist only in TMVM_DERIVATIVE, DDX/DDY pin 'Value', Custom outputs ''),
      FunctionOutput's single pin 'None' (v1 mock). Checks: every link names an existing pin/output, every
      required pin is connected, float dimensions are consistent, function outputs have their declared
      types, CellSample fetches use the chosen mip mode with derivative pins connected (derivative mode),
      counts, and that NO existing (anchor) node received an input link (edges == {}).
      Also: anchors re-resolved against the baseline dump, and the AST scan below.
      It proves the script's Python wiring logic only, not engine behaviour.
  python -B s1v2_material_edit_offline.py scan
      AST scan of s1v2_material_edit.py: save_packages only in save()/child_save() with the named lists;
      apply() cannot reach a save; no delete/save_assets/prepare/verify_landscape calls;
      connect_material_property only in apply()'s probe loop; links only through Builder.link.
  python -B s1v2_material_edit_offline.py expectations <args.json> <out.json>
      Writes the expectations JSON for the design implemented in s1v2_material_edit.py plus the args'
      child values (asserted equal to S1V2_SPEC.json child_values for GazaShujaiya) and the args' mip mode.
"""
import ast
import hashlib
import importlib.util
import json
import os
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent                 # .../Stage1_Ground/S1v2
STAGE = HERE.parent
TARGET = HERE / 's1v2_material_edit.py'
SPEC_V2 = HERE / 'S1V2_SPEC.json'
SPEC_D2 = STAGE / 'S1_Prep' / 'S1_MINIMAL_SAFE_SPEC.json'       # read-only (master/children/baseline blocks)
GRAPH_BEFORE = STAGE / 'S1_Prep' / 'receipts' / 'GRAPH_BEFORE_23156.json'  # read-only baseline dump (605c55d0)
MODES = ('derivative', 'gradient_free')


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_target():
    assert 'unreal' not in sys.modules, 'offline only'
    os.environ.pop('GEOCITY_S1_ARGS', None)
    spec = importlib.util.spec_from_file_location('s1v2_material_edit_offline_copy', TARGET)
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
DERIV = ('DDX(UVs)', 'DDY(UVs)')


class TextureSample(Expr):
    """M (GRAPH_BEFORE_23156): TMVM_DERIVATIVE samples list ['UVs','Tex','DDX(UVs)','DDY(UVs)','Apply View MipBias'];
    TMVM_NONE samples ['UVs','Tex','Apply View MipBias']."""
    CLASS, OUTPUTS = 'MaterialExpressionTextureSample', RGBA_OUT

    def input_names(self):
        if self.props.get('mip_value_mode') == 'TMVM_DERIVATIVE':
            return ['UVs', 'Tex', DERIV[0], DERIV[1], 'Apply View MipBias']
        return ['UVs', 'Tex', 'Apply View MipBias']


CLASSES = {n: cls(n, AB) for n in ('Multiply', 'Add', 'Subtract', 'Divide', 'Max', 'DotProduct', 'AppendVector')}
CLASSES.update({n: cls(n, ONE) for n in ('Saturate', 'OneMinus', 'ComponentMask')})
CLASSES.update({
    'Normalize': cls('Normalize', ('VectorInput',)), 'Clamp': cls('Clamp', ('None', 'Min', 'Max')),
    'LinearInterpolate': cls('LinearInterpolate', ('A', 'B', 'Alpha')),
    'SmoothStep': cls('SmoothStep', ('Min', 'Max', 'Value')),
    'Constant2Vector': cls('Constant2Vector', (), ('', 'R', 'G')),
    'Constant3Vector': cls('Constant3Vector', (), ('', 'R', 'G', 'B')),
    'TextureSample': TextureSample,
    'DDX': cls('DDX', ('Value',)), 'DDY': cls('DDY', ('Value',)),
    'FunctionInput': cls('FunctionInput', ('Preview',)), 'FunctionOutput': cls('FunctionOutput', ('None',), ()),
    'ScalarParameter': cls('ScalarParameter'), 'VectorParameter': cls('VectorParameter', (), RGBA_OUT),
    'TextureObjectParameter': cls('TextureObjectParameter', ('UVs', 'Apply View MipBias')),
    'LandscapeLayerSample': cls('LandscapeLayerSample'), 'VertexNormalWS': cls('VertexNormalWS'),
    'StaticSwitchParameter': cls('StaticSwitchParameter', ('True', 'False')),
})


class LayerBlend(Expr):
    CLASS = 'MaterialExpressionLandscapeLayerBlend'

    def input_names(self):
        names = []
        for entry in self.props.get('layers', []):
            names.append('Layer ' + entry.props['layer_name'])
            if entry.props.get('blend_type') == 'LB_HEIGHT_BLEND':
                names.append('Height ' + entry.props['layer_name'])
        return names


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
        return ['ExistingPin']  # any link into an anchor would land here and fail the edges == {} check


class Struct:
    def __init__(self):
        self.props = {}

    def set_editor_property(self, key, value):
        self.props[key] = value

    def get_editor_property(self, key):
        return self.props[key]


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
    names.update(MaterialExpressionLandscapeLayerBlend=LayerBlend, MaterialExpressionMaterialFunctionCall=FunctionCall)
    u = types.SimpleNamespace(**names)
    u.Name = str
    u.LinearColor = lambda *v: tuple(float(x) for x in v)
    u.LayerBlendInput = Struct
    u.LandscapeLayerBlendType = types.SimpleNamespace(LB_HEIGHT_BLEND='LB_HEIGHT_BLEND')
    u.TextureMipValueMode = types.SimpleNamespace(TMVM_NONE='TMVM_NONE', TMVM_DERIVATIVE='TMVM_DERIVATIVE')
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
            return e.dim[output] if isinstance(e.dim, dict) else e.dim
        if c in ('ScalarParameter', 'LandscapeLayerSample'):
            return 1
        if c in ('VectorParameter', 'TextureSample'):
            if c == 'TextureSample':
                assert self.pin(e, 'UVs') == 2 and self.pin(e, 'Tex') == 'tex', ('bad sample inputs', where)
                if e.props.get('mip_value_mode') == 'TMVM_DERIVATIVE':
                    assert self.pin(e, DERIV[0]) == 2 and self.pin(e, DERIV[1]) == 2, ('bad derivative inputs', where)
            return {'RGB': 3, 'RGBA': 4, '': 3}.get(output, 1)
        if c == 'TextureObjectParameter':
            return 'tex'
        if c == 'Constant2Vector':
            return 2 if output == '' else 1
        if c == 'Constant3Vector':
            return 3 if output == '' else 1
        if c == 'VertexNormalWS':
            return 3
        if c == 'FunctionInput':
            return FIN_DIM[e.props['input_type']]
        if c in ('DDX', 'DDY'):
            d = self.pin(e, 'Value')
            assert d not in (None, 'tex'), ('derivative of nothing/texture', where)
            return d
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
        if c in ('Saturate', 'OneMinus'):
            return self.pin(e, 'None')
        if c == 'Clamp':
            return self.pin(e, 'None')
        if c == 'Normalize':
            d = self.pin(e, 'VectorInput')
            assert d in (2, 3, 4), ('normalize of scalar', where)
            return d
        if c == 'SmoothStep':
            d = self.pin(e, 'Value')
            for k in ('Min', 'Max'):
                d = combine(d, self.pin(e, k), where)
            return d
        if c == 'StaticSwitchParameter':
            return combine(self.pin(e, 'True'), self.pin(e, 'False'), where)
        if c == 'LandscapeLayerBlend':
            d = None
            for name in e.input_names():
                if name.startswith('Layer '):
                    d = combine(d, self.pin(e, name), where)
                else:
                    assert self.pin(e, name) == 1, ('height pin not scalar', where, name)
            return d
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
    if 'const_min' in p or e.CLASS.endswith('Clamp'):
        optional.add('Min')
    if 'const_max' in p or e.CLASS.endswith('Clamp'):
        optional.add('Max')
    if e.CLASS.endswith('TextureObjectParameter'):
        optional.add('UVs')
    return [n for n in names if n not in optional]


def check_connected(owner):
    missing = [(e.get_name(), n) for e in owner.nodes for n in required_pins(e) if n not in e.edges]
    assert not missing, ('unconnected required pins', owner.name, missing[:20])


# ------------------------------------------------------------------ anchors vs the baseline dump
ANCHOR_DIMS = {'ground_full': 3, 'ground_full_normal': 3, 'ground_near': 3, 'ground_far': 3,
               'road_uv': 2, 'pad_uv': 2, 'steep_far_scale': 1, 'road_far_scale': 1, 'pad_far_scale': 1,
               'steep_normal': 3, 'road_normal': 3, 'pad_normal': 3, 'distance_alpha': 1, 'layer_coords': 2,
               'grid_cm': 1, **{'near_hash%d' % k: 2 for k in range(4)}, **{'far_hash%d' % k: 2 for k in range(4)},
               'near_wx': 1, 'near_wy': 1, 'far_wx': 1, 'far_wy': 1}


def anchor_check(m):
    """Re-resolve ANCHORS / PARAM_ANCHORS / ROUGHNESS / root-layer expectations on the baseline dump."""
    dump = json.loads(GRAPH_BEFORE.read_text(encoding='utf-8'))
    nodes, roots = dump['nodes'], dump['roots']
    assert dump['graph_sha256'] == m.BASELINE['graph_sha256'] and len(nodes) == m.BASELINE['node_count']
    by_desc = {}
    for path, row in nodes.items():
        by_desc.setdefault(row['properties'].get('desc') or '', []).append(path)
    found = {}
    for key, (desc, kind, suffix, output) in m.ANCHORS.items():
        hits = by_desc.get(desc, [])
        assert len(hits) == 1, ('anchor not unique', key, hits)
        row = nodes[hits[0]]
        assert row['class'] == 'MaterialExpression' + kind and hits[0].endswith(':MaterialExpression' + suffix), key
        assert output in row['output_names'] or (output == '' and row['output_names']), key
        found[key] = hits[0]

    def reach(starts):
        seen, stack = set(), list(starts)
        while stack:
            cur = stack.pop()
            if cur in seen or cur not in nodes:
                continue
            seen.add(cur)
            stack.extend(e['source'] for e in nodes[cur]['edges'].values() if e['source'])
        return seen
    active = reach([roots[k] for k in ('color', 'normal', 'roughness')])
    params = dict(m.PARAM_ANCHORS)
    params.update({'rough_' + l: (l + '_Roughness', 'ScalarParameter', s, '') for l, s in m.ROUGHNESS.items()})
    for key, (name, kind, suffix, output) in params.items():
        hits = [p for p in active if nodes[p]['class'] == 'MaterialExpression' + kind
                and nodes[p]['properties'].get('parameter_name') == name]
        assert len(hits) == 1 and hits[0].endswith(':MaterialExpression' + suffix), ('parameter anchor', key, hits)
        assert output in nodes[hits[0]]['output_names'] or (output == '' and nodes[hits[0]]['output_names']), key
        found[key] = hits[0]
    for (root, layer), key in m.ROOT_LAYER_EXPECT.items():
        assert nodes[roots[root]]['edges']['Layer ' + layer]['source'] == found[key], ('root layer', root, layer)
    for (root, layer), suffix in m.ROOT_LAYER_SUFFIX.items():
        assert nodes[roots[root]]['edges']['Layer ' + layer]['source'].endswith(':MaterialExpression' + suffix)
    for layer in m.LAYERS:
        assert nodes[roots['roughness']]['edges']['Layer ' + layer]['source'] == found['rough_' + layer]
    derivative = [r for r in nodes.values() if r['class'] == 'MaterialExpressionTextureSample'
                  and 'TMVM_DERIVATIVE' in str(r['properties'].get('mip_value_mode'))]
    connected = [r for r in derivative if all(p in r['input_names'] and r['edges'][p]['source'] for p in DERIV)]
    textures = sorted({r['properties']['texture'] for r in nodes.values() if r['properties'].get('texture')})
    for name, (kind, default, sampler) in m.PARAMS.items():
        if kind == 'texture':
            assert default in textures, ('master default texture not referenced by the master', name)
    return {'graph': str(GRAPH_BEFORE), 'graph_sha256': dump['graph_sha256'], 'anchors_resolved': len(found),
            'active_set': len(active), 'derivative_samples': len(derivative),
            'derivative_samples_pins_connected': len(connected), 'status': 'ANCHORS_RESOLVE_ON_BASELINE_DUMP'}


# ------------------------------------------------------------------ selftest
def build(m, mode):
    MockLib.links = 0
    m.CELL_MIP['mode'] = mode
    report = {'functions': {}, 'master': {}}
    functions = {}
    for name, spec in m.FUNCTIONS.items():
        fn = Owner(name)
        g = m.Builder(fn, True, -1600, 0, 8)
        _, outputs = m.build_function_graph(g, name, spec, ())
        check_connected(fn)
        dims = Dims({})
        for pin, kind in spec['outputs']:
            got = dims.of(outputs[pin].edges['None'])
            assert got == DECL_DIM[kind], (name, pin, got)
        samples = [e for e in fn.nodes if e.CLASS.endswith('TextureSample')]
        for e in samples:  # force dimension checks of every fetch (incl. derivative pins)
            dims.of((e, 'RGB'))
        assert len(samples) == sum(spec['samples'].values()), name
        assert all(e.props['sampler_source'] == m.WRAP for e in samples), name
        derivative = spec['cell_mip'] and mode == 'derivative'
        assert all(e.props['mip_value_mode'] == ('TMVM_DERIVATIVE' if derivative else 'TMVM_NONE') for e in samples), name
        assert all((DERIV[0] in e.edges and DERIV[1] in e.edges) == derivative for e in samples), name
        ddx = [e for e in fn.nodes if e.CLASS.endswith(('DDX', 'DDY'))]
        assert len(ddx) == (2 if derivative else 0), (name, len(ddx))
        assert all(e.props['desc'].startswith(m.MARK) for e in fn.nodes), name
        assert not [e for e in fn.nodes if 'Parameter' in e.CLASS], name
        functions[name] = fn
        report['functions'][name] = {'nodes': len(fn.nodes), 'samples': len(samples),
                                     'mip_value_mode': sorted({e.props['mip_value_mode'] for e in samples}),
                                     'derivative_pins_connected': sum(DERIV[0] in e.edges for e in samples),
                                     'inputs': [p for p, _ in spec['inputs']], 'outputs': [p for p, _ in spec['outputs']]}
    master = Owner('M_SurfaceBank_Natural')
    old = Owner('existing')
    anchors = {}
    for key, (desc, kind, suffix, output) in m.ANCHORS.items():
        anchors[key] = (Anchor(old, suffix, ('',), ANCHOR_DIMS[key]), output)
    for layer, suffix in m.ROUGHNESS.items():
        anchors['rough_' + layer] = (Anchor(old, suffix, ('',), 1), '')
    for key, (name, kind, suffix, output) in m.PARAM_ANCHORS.items():
        if kind == 'TextureObjectParameter':
            anchors[key] = (Anchor(old, suffix, ('',), 'tex'), output)
        elif kind == 'VectorParameter':
            anchors[key] = (Anchor(old, suffix, RGBA_OUT, {'RGB': 3, 'RGBA': 4, 'R': 1, 'G': 1, 'B': 1, 'A': 1}), output)
        else:
            anchors[key] = (Anchor(old, suffix, ('',), 1), output)
    old_llb = {k: Anchor(old, v, ('',), 1 if k == 'roughness' else 3) for k, v in m.ROOT_LLB.items()}
    g = m.Builder(master, False, -4000, 36000, 10)
    switches = {}
    for key in m.ROOT_PROPS:  # same calls as apply()'s probe
        switches[key] = g.node(m.unreal.MaterialExpressionStaticSwitchParameter, 'Enable' + key.title(),
                               parameter_name=m.SWITCH, default_value=False, group='GeoCity_S1')
        assert sorted(MockLib.get_material_expression_input_names(switches[key])) == ['False', 'True']
        m.Builder.link(old_llb[key], switches[key], 'True')
        m.Builder.link(old_llb[key], switches[key], 'False')
    P = m.make_params(g)
    branch = m.build_branch(g, anchors, P, functions)
    for key in m.ROOT_PROPS:
        m.Builder.link(branch['finals'][key], switches[key], 'True')
    check_connected(master)
    untouched = [a.get_name() for a in old.nodes if a.edges]
    assert not untouched, ('An existing node received an input link', untouched)
    dims = Dims(m.FUNCTIONS)
    root_dims = {key: dims.of((switches[key], '')) for key in m.ROOT_PROPS}
    assert root_dims == {'color': 3, 'normal': 3, 'roughness': 1}, root_dims
    for llb in branch['llbs'].values():
        dims.of((llb, ''))
    for e in master.nodes:  # every new node must have a consistent dimension
        if not e.CLASS.endswith(('FunctionOutput',)):
            for out in (e.output_names() or [''])[:1]:
                dims.of((e, out))
    nodes = master.nodes
    classes = {}
    for e in nodes:
        classes[e.CLASS] = classes.get(e.CLASS, 0) + 1
    samples = [e for e in nodes if e.CLASS.endswith('TextureSample')]
    assert not samples, 'master-level texture samples (SPEC master_level_texture_samples = 0)'
    calls = [e for e in nodes if e.CLASS.endswith('MaterialFunctionCall')]
    call_names = sorted(c.props['material_function'].name for c in calls)
    assert call_names == sorted(['MF_GeoCityV2_CellSample'] * 5 + ['MF_GeoCityV2_MacroField', 'MF_GeoCityV2_MacroColor',
                                 'MF_GeoCityV2_SlopeBlend'] + ['MF_GeoCityV2_HeightBlend'] * 4), call_names
    effective = sum(sum(m.FUNCTIONS[c.props['material_function'].name]['samples'].values()) for c in calls)
    params = [e.props['parameter_name'] for e in nodes if 'Parameter' in e.CLASS]
    assert sorted(set(params)) == sorted(m.PARAMS) and len(params) == len(m.PARAMS) + 2
    assert all(e.props['desc'].startswith(m.MARK) and not e.props['desc'].startswith(m.GRASS_OWNER) for e in nodes)
    xs = [e.props['material_expression_editor_x'] for e in nodes]
    assert min(xs) >= -4000 and max(xs) <= -1840
    heights = {}
    for llb in branch['llbs'].values():
        row = tuple((n, id(llb.edges[n][0]), llb.edges[n][1]) for n in sorted(llb.input_names()) if n.startswith('Height'))
        heights[row] = True
    assert len(heights) == 1, 'height sources differ between LLBs'
    layer_samples = sorted(e.props['parameter_name'] for e in nodes if e.CLASS.endswith('LandscapeLayerSample'))
    assert layer_samples == sorted(m.LAYERS)
    # Ground identity wiring: GroundWithB.A is the existing LinearInterpolate_42 anchor; Sand_01 normal pin is Normalize_9.
    with_b = [e for e in nodes if e.props.get('desc') == m.MARK + 'GroundWithB'][0]
    assert with_b.edges['A'][0].get_name() == 'LinearInterpolate_42', 'Ground colour base is not LinearInterpolate_42'
    assert branch['llbs']['normal'].edges['Layer Sand_01'][0].get_name() == 'Normalize_9', 'Ground normal base'
    per_cell_fetch = sum(m.FUNCTIONS['MF_GeoCityV2_CellSample']['samples'].values())
    report['master'] = {'added_node_count': len(nodes), 'direct_texture_samples': len(samples),
                        'function_calls': call_names, 'effective_new_samples': effective,
                        'cell_sample_fetches': 5 * per_cell_fetch, 'parameter_names': len(set(params)),
                        'parameter_nodes': len(params), 'class_counts': dict(sorted(classes.items())),
                        'root_dims': root_dims, 'links': MockLib.links, 'layer_samples': layer_samples,
                        'existing_nodes_with_new_input_links': 0}
    return report


def selftest():
    m = load_target()
    bind_mock(m)
    report = {'target': str(TARGET), 'target_sha256': sha_file(TARGET), 'modes': {}}
    for mode in MODES:
        report['modes'][mode] = build(m, mode)
    m.CELL_MIP['mode'] = None
    report['anchors'] = anchor_check(m)
    report['scan'] = scan()
    report['status'] = 'SELFTEST_PASSED_MOCK_ENGINE'
    report['scope'] = ('Python wiring/pin-name/dimension logic only; engine behaviour (pin names inside MFs, '
                       'StaticSwitchParameter/height LLB/FunctionOutput/VertexNormalWS, compile, propagation) '
                       'is asserted at run time by s1v2_material_edit.py.')
    return m, report


# ------------------------------------------------------------------ AST scan
FORBIDDEN = ('save_assets', 'save_asset', 'save_loaded_asset', 'save_loaded_assets', 'save_dirty_packages',
             'save_directory', 'save_current_level', 'save_map', 'save_all_dirty_levels', 'delete_asset',
             'delete_loaded_asset', 'delete_directory', 'delete_material_expression',
             'delete_material_expression_in_function', 'delete_all_material_expressions',
             'delete_all_material_expressions_in_function', 'prepare', 'verify_landscape', 'rename_asset',
             'duplicate_asset', 'consolidate_assets', 'set_material_instance_parent_editor_only',
             'disconnect_material_property')
SAVE_GROUPS = ("groups = [('functions', [FUNCTION_DIR + '/' + n for n in FUNCTIONS]), ('master', [MASTER]),\n"
               "              ('children', [CHILDREN[area]])]")


def scan():
    src = TARGET.read_text(encoding='utf-8')
    tree = ast.parse(src)
    owners, calls_by_fn, sites = {}, {}, {}
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
    setters = sorted({(n, k) for k in ('set_material_instance_scalar_parameter_value', 'set_material_instance_vector_parameter_value',
                                       'set_material_instance_texture_parameter_value',
                                       'set_material_instance_static_switch_parameter_value', 'set_material_instance_parent')
                      for n, _ in sites.get(k, [])})
    assert {n for n, _ in setters} <= {'apply', 'tune'}, setters
    return {'status': 'AST_SCAN_PASSED', 'save_packages_sites': saves, 'connect_material_property_sites': props,
            'link_sites': links, 'instance_setter_functions': sorted({n for n, _ in setters}),
            'forbidden_checked': list(FORBIDDEN), 'save_named_list': SAVE_GROUPS}


# ------------------------------------------------------------------ expectations
def expectations(args_file, out_file):
    m, report = selftest()
    args = json.loads(Path(args_file).read_text(encoding='utf-8-sig'))
    spec = json.loads(SPEC_V2.read_text(encoding='utf-8'))
    d2 = json.loads(SPEC_D2.read_text(encoding='utf-8'))
    mode = m.cell_mip_mode(args)
    # Same validation the editor run applies (sampler kinds of existing params: M, r031 dump).
    plans = m.plan_children(args, {'Dirt_Path_Albedo': 'COLOR', 'Dirt_Path_Normal': 'NORMAL',
                                   'Sand_Path_Albedo': 'COLOR', 'Sand_Path_Normal': 'NORMAL'})
    areas = sorted(args['child_values'])
    spec_values = spec['child_values']['GazaShujaiya']
    spec_match = None
    if 'GazaShujaiya' in args['child_values']:
        mine = args['child_values']['GazaShujaiya']
        spec_match = {k: mine.get(k, {}) == spec_values[k] for k in ('textures', 'vectors', 'scalars')}
        spec_match['grass_coverage'] = (args.get('grass_coverage') or {}).get('GazaShujaiya') == spec_values['grass_coverage']
        assert all(spec_match.values()), ('args child values differ from S1V2_SPEC.json child_values', spec_match)
    assert sorted(spec['params']) == sorted(m.PARAMS), 'PARAMS differ from S1V2_SPEC.json params'
    for name, (kind, default, sampler) in m.PARAMS.items():
        want = spec['params'][name]
        assert want[0] == kind and (list(default) if kind == 'vector' else default) == want[1] and want[2] == sampler, name
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
    existing = {}
    for area in areas:
        values = args['child_values'][area]
        existing[area] = {n: (m.obj_path(v) if k == 'textures' else v) for k in ('textures', 'vectors', 'scalars')
                          for n, v in values.get(k, {}).items() if n not in m.PARAMS}
    both = {n: v for n, v in existing[areas[0]].items() if all(existing[a].get(n) == v for a in areas)}
    functions = {}
    for name, fspec in m.FUNCTIONS.items():
        row = {'inputs': ['%s:%s' % p for p in fspec['inputs']], 'outputs': ['%s:%s' % p for p in fspec['outputs']],
               'texture_samples': sum(fspec['samples'].values()),
               'mip_value_mode': ('TMVM_DERIVATIVE' if fspec['cell_mip'] and mode == 'derivative' else 'TMVM_NONE')
               if fspec['samples'] else None,
               'derivative_pins_connected': bool(fspec['cell_mip'] and mode == 'derivative'),
               'nodes_mock': report['modes'][mode]['functions'][name]['nodes']}
        if fspec['samples']:
            row.update(sampler_type=m.SAMPLER_NAMES[next(iter(fspec['samples']))], sampler_source='SSM_WRAP_WORLD_GROUP_SETTINGS')
        functions[name] = row
    master = report['modes'][mode]['master']
    result = {
        'schema': 'environmentpipeline.stage1_s1_minimal_safe_spec.v1',
        'schema_note': 'v1 expectations schema reused for review; S1_Prep/s1_verify.py post_s1 cannot consume v2 receipts.',
        'variant': 's1v2',
        'status': 'IMPLEMENTED_DESIGN_EXPECTATIONS_NOT_EXECUTED',
        'generated_by': {'file': str(Path(__file__).resolve()), 'file_sha256': sha_file(Path(__file__).resolve()),
                         'target': str(TARGET), 'target_sha256': sha_file(TARGET),
                         'args_file': str(Path(args_file).resolve()), 'args_sha256': sha_file(args_file),
                         'spec': str(SPEC_V2), 'spec_sha256': sha_file(SPEC_V2)},
        'design_notes': ('S1v2: one CellSample function for every routed albedo through the existing Sand_01 hash lattice, '
                         'MacroField (127/463/1531 m, 0/37/71 deg, linear), new MacroColor body, Ground base '
                         'LinearInterpolate_42/Normalize_9 (B0 identity on Ground at zero amounts), SlopeBlend/HeightBlend '
                         'from v1. Values = the args child values (SPEC section 3 t001), i.e. the state that would be saved.'),
        'cell_sample_mip_mode': mode,
        'spec_child_values_match': spec_match,
        'master': d2['master'], 'base_mi_untouched': d2['base_mi_untouched'], 'children': d2['children'],
        'new_function_packages': [m.FUNCTION_DIR + '/' + n for n in m.FUNCTIONS],
        'v1_function_packages_must_be_absent': [m.FUNCTION_DIR + '/' + n for n in m.V1_FUNCTIONS],
        'functions': functions, 'node_desc_prefix': m.MARK, 'canvas': {'x': [-4000, -1840], 'y_min': 36000},
        'new_parameters': params, 'new_parameter_names': len(params),
        'new_landscape_layer_samples': list(m.LAYERS),
        'new_llbs': {'count': 3, 'layers': list(m.LAYERS), 'blend_type': 'LB_HEIGHT_BLEND',
                     'preview_weight': {l: (1.0 if l == 'Sand_01' else 0.0) for l in m.LAYERS},
                     'pins': ['Layer <name>', 'Height <name>'], 'height_sources_identical_on_all_three': True},
        'static_switch_nodes': {'name': m.SWITCH, 'count': 3, 'default': False,
                                'False_pin_sources': [m.ROOT_LLB[k] for k in ('color', 'normal', 'roughness')],
                                'roots': ['MP_BASE_COLOR', 'MP_NORMAL', 'MP_ROUGHNESS'],
                                'ao_root': 'LandscapeLayerBlend_0 unchanged'},
        'switch_pins': {'true': 'True', 'false': 'False'},
        'ground_base_anchors': {'color': 'LinearInterpolate_42', 'normal': 'Normalize_9'},
        'added_node_count': master['added_node_count'],
        'function_calls': master['function_calls'],
        'allowed_sampler_sources': ['SSM_WRAP_WORLD_GROUP_SETTINGS'],
        'existing_param_child_overrides': {'both_children': both, 'per_area': existing},
        'grass_coverage': args.get('grass_coverage'),
        'sampler_estimate': {'new_samples': master['effective_new_samples'], 'cell_sample_fetches': master['cell_sample_fetches'],
                             'direct_master_samples': master['direct_texture_samples'],
                             'new_sampler_states': 0, 'iran_change': 0},
        'baseline_expectations': d2['baseline_expectations'],
        'plans': plans,
        'selftest': report,
    }
    out = Path(out_file).resolve()
    assert out.parent == HERE and not out.exists(), 'Writes only new files directly under S1v2'
    out.write_text(json.dumps(result, indent=1), encoding='utf-8')
    return {'file': str(out), 'sha256': sha_file(out), 'parameters': len(params), 'mode': mode,
            'added_node_count': result['added_node_count'], 'new_samples': result['sampler_estimate']['new_samples']}


if __name__ == '__main__':
    if sys.argv[1:2] == ['selftest']:
        print(json.dumps(selftest()[1], indent=1))
    elif sys.argv[1:2] == ['scan']:
        print(json.dumps(scan(), indent=1))
    elif sys.argv[1:2] == ['expectations'] and len(sys.argv) == 4:
        print(json.dumps(expectations(sys.argv[2], sys.argv[3]), indent=1))
    else:
        raise SystemExit(__doc__)
