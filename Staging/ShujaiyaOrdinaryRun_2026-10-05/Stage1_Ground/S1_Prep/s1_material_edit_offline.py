"""OFFLINE companion of s1_material_edit.py. Never imports unreal; writes only under S1_Prep.

  python s1_material_edit_offline.py selftest
      Builds the 5 MF graphs and the full master branch (probe switches + params + branch)
      against a MOCK engine whose pin/output names are MEASURED from the r031 describe() dump
      (REV/EPIC_RESIDENT_RIMAL_verify_r031_epic_fresh_reopen_PID35000.json; FunctionOutput's
      single pin 'None' from REV/INSTALLED_FUNCTIONS_PID30632.json). Checks: every link names
      an existing pin/output, every required pin is connected, float dimensions are consistent
      (UE rejects e.g. float2+float3), function outputs have their declared types, and counts.
      It proves the script's Python wiring logic only, not engine behaviour.
  python s1_material_edit_offline.py expectations <args.json> <out.json>
      Writes the s1_verify.py expectations JSON (S1_MINIMAL_SAFE_SPEC.json schema) for the
      design actually implemented in s1_material_edit.py plus the args' child values.
"""
import copy
import importlib.util
import json
import os
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / 's1_material_edit.py'
SPEC_D2 = HERE / 'S1_MINIMAL_SAFE_SPEC.json'


def load_target():
    assert 'unreal' not in sys.modules, 'offline only'
    os.environ.pop('GEOCITY_S1_ARGS', None)
    spec = importlib.util.spec_from_file_location('s1_material_edit_offline_copy', TARGET)
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
    'TextureSample': cls('TextureSample', ('UVs', 'Tex', 'Apply View MipBias'), RGBA_OUT),
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
    CLASS = 'MaterialExpressionAnchor'

    def __init__(self, owner, name, outputs, dim):
        super().__init__(owner)
        self.name, self.OUTPUTS, self.dim = name, tuple(outputs), dim

    def get_name(self):
        return self.name


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
        if c in ('ScalarParameter', 'LandscapeLayerSample'):
            return 1
        if c in ('VectorParameter', 'TextureSample'):
            if c == 'TextureSample':
                assert self.pin(e, 'UVs') == 2 and self.pin(e, 'Tex') == 'tex', ('bad sample inputs', where)
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


# ------------------------------------------------------------------ selftest
def selftest():
    m = load_target()
    bind_mock(m)
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
        assert len(samples) == sum(spec['samples'].values()), name
        assert all(e.props['sampler_source'] == m.WRAP for e in samples), name
        assert all(e.props['desc'].startswith(m.MARK) for e in fn.nodes), name
        assert not [e for e in fn.nodes if 'Parameter' in e.CLASS], name
        functions[name] = fn
        report['functions'][name] = {'nodes': len(fn.nodes), 'samples': len(samples),
                                     'inputs': [p for p, _ in spec['inputs']], 'outputs': [p for p, _ in spec['outputs']]}
    master = Owner('M_SurfaceBank_Natural')
    anchors = {}
    dims_of_anchor = {'ground_color': 3, 'steep_color': 3, 'road_color': 3, 'pad_color': 3, 'ground_normal': 3,
                      'steep_normal': 3, 'road_normal': 3, 'pad_normal': 3, 'ground_near': 3, 'ground_far': 3,
                      'steep_near': 3, 'steep_far': 3, 'road_near': 3, 'road_far': 3, 'pad_near': 3, 'pad_far': 3,
                      'distance_alpha': 1, 'layer_coords': 2, 'grid_cm': 1}
    for key, (desc, kind, suffix, output) in m.ANCHORS.items():
        outputs = ('XY Texture', 'Z Texture', 'XYZ Texture') if output else ('',)
        anchors[key] = (Anchor(Owner('old'), suffix, outputs, dims_of_anchor[key]), output)
    for layer, suffix in m.ROUGHNESS.items():
        anchors['rough_' + layer] = (Anchor(Owner('old'), suffix, ('',), 1), '')
    old_llb = {k: Anchor(Owner('old'), v, ('',), 1 if k == 'roughness' else 3) for k, v in m.ROOT_LLB.items()}
    g = m.Builder(master, False, -4000, 36000, 10)
    switches = {}
    for key in m.ROOT_PROPS:  # same calls as apply()'s probe
        switches[key] = g.node(m.unreal.MaterialExpressionStaticSwitchParameter, 'Enable' + key.title(),
                               parameter_name=m.SWITCH, default_value=False, group='GeoCity_S1')
        assert sorted(MockLib.get_material_expression_input_names(switches[key])) == ['False', 'True']
        m.Builder.link(old_llb[key], switches[key], 'True')
        m.Builder.link(old_llb[key], switches[key], 'False')
    mock_functions = {}
    for name, fn in functions.items():
        mock_functions[name] = fn
    P = m.make_params(g)
    branch = m.build_branch(g, anchors, P, mock_functions)
    for key in m.ROOT_PROPS:
        m.Builder.link(branch['finals'][key], switches[key], 'True')
    check_connected(master)
    dims = Dims(m.FUNCTIONS)
    root_dims = {key: dims.of((switches[key], '')) for key in m.ROOT_PROPS}
    assert root_dims == {'color': 3, 'normal': 3, 'roughness': 1}, root_dims
    for llb in branch['llbs'].values():
        dims.of((llb, ''))
    nodes = master.nodes
    classes = {}
    for e in nodes:
        classes[e.CLASS] = classes.get(e.CLASS, 0) + 1
    samples = [e for e in nodes if e.CLASS.endswith('TextureSample')]
    calls = [e for e in nodes if e.CLASS.endswith('MaterialFunctionCall')]
    effective = len(samples) + sum(sum(m.FUNCTIONS[c.props['material_function'].name]['samples'].values()) for c in calls)
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
    report['master'] = {'added_node_count': len(nodes), 'direct_texture_samples': len(samples),
                        'direct_sampler_types': sorted(e.props['sampler_type'] for e in samples),
                        'function_calls': sorted(c.props['material_function'].name for c in calls),
                        'effective_new_samples': effective, 'parameter_names': len(set(params)),
                        'parameter_nodes': len(params), 'class_counts': dict(sorted(classes.items())),
                        'root_dims': root_dims, 'links': MockLib.links, 'layer_samples': layer_samples}
    report['status'] = 'SELFTEST_PASSED_MOCK_ENGINE'
    report['scope'] = ('Python wiring/pin-name/dimension logic only; engine behaviour (pin names of '
                       'StaticSwitchParameter/height LLB/FunctionOutput/VertexNormalWS, compile, propagation) '
                       'is asserted at run time by s1_material_edit.py.')
    return m, report


# ------------------------------------------------------------------ expectations
def expectations(args_file, out_file):
    m, report = selftest()
    args = json.loads(Path(args_file).read_text(encoding='utf-8-sig'))
    d2 = json.loads(SPEC_D2.read_text(encoding='utf-8'))
    # Same validation the editor run applies (sampler kinds of existing params: M, r031 dump).
    m.plan_children(args, {'Dirt_Path_Albedo': 'COLOR', 'Dirt_Path_Normal': 'NORMAL',
                           'Sand_Path_Albedo': 'COLOR', 'Sand_Path_Normal': 'NORMAL'})
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
    existing = {}
    for area in areas:
        values = args['child_values'][area]
        existing[area] = {n: (m.obj_path(v) if k == 'textures' else v) for k in ('textures', 'vectors', 'scalars')
                          for n, v in values.get(k, {}).items() if n not in m.PARAMS}
    both = {n: v for n, v in existing[areas[0]].items() if all(existing[a].get(n) == v for a in areas)}
    functions = {}
    for name, spec in m.FUNCTIONS.items():
        row = {'inputs': ['%s:%s' % p for p in spec['inputs']], 'outputs': ['%s:%s' % p for p in spec['outputs']],
               'texture_samples': sum(spec['samples'].values())}
        if spec['samples']:
            row.update(sampler_type=m.SAMPLER_NAMES[next(iter(spec['samples']))], sampler_source='SSM_WRAP_WORLD_GROUP_SETTINGS')
        functions[name] = row
    result = {
        'schema': 'environmentpipeline.stage1_s1_minimal_safe_spec.v1',
        'status': 'IMPLEMENTED_DESIGN_EXPECTATIONS_NOT_EXECUTED',
        'generated_by': {'file': str(Path(__file__).resolve()), 'target': str(TARGET),
                         'target_sha256': __import__('hashlib').sha256(TARGET.read_bytes()).hexdigest(),
                         'args_file': str(Path(args_file).resolve())},
        'design_notes': ('D2 + corrections: GroundC (SandC) slot, Soil_FarScale, Variation mask/normal (amount 0 until '
                         'review), SteepStones reusing Pad outputs, HeightAmount identity formula H=lerp(1-w,h,A), '
                         'SteepLo/Hi defaults 0/0.001 (identity) instead of D2 0.25/0.45.'),
        'master': d2['master'], 'base_mi_untouched': d2['base_mi_untouched'], 'children': d2['children'],
        'new_function_packages': [m.FUNCTION_DIR + '/' + n for n in m.FUNCTIONS],
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
        'added_node_count': report['master']['added_node_count'],
        'allowed_sampler_sources': ['SSM_WRAP_WORLD_GROUP_SETTINGS'],
        'existing_param_child_overrides': {'both_children': both, 'per_area': existing},
        'sampler_estimate': {'new_samples': report['master']['effective_new_samples'],
                             'direct_master_samples': report['master']['direct_texture_samples'],
                             'new_sampler_states': 0, 'iran_change': 0},
        'baseline_expectations': d2['baseline_expectations'],
        'selftest': report,
    }
    out = Path(out_file).resolve()
    assert out.parent == HERE and not out.exists(), 'Writes only new files directly under S1_Prep'
    out.write_text(json.dumps(result, indent=1), encoding='utf-8')
    return {'file': str(out), 'sha256': __import__('hashlib').sha256(out.read_bytes()).hexdigest(),
            'parameters': len(params), 'added_node_count': result['added_node_count'],
            'new_samples': result['sampler_estimate']['new_samples']}


if __name__ == '__main__':
    if sys.argv[1:2] == ['selftest']:
        print(json.dumps(selftest()[1], indent=1))
    elif sys.argv[1:2] == ['expectations'] and len(sys.argv) == 4:
        print(json.dumps(expectations(sys.argv[2], sys.argv[3]), indent=1))
    else:
        raise SystemExit(__doc__)
