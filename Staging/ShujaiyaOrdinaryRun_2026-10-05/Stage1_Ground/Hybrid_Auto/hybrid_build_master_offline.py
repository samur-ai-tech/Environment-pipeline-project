"""OFFLINE companion of hybrid_build_master.py. Never imports unreal; writes only HYBRID_EDIT_EXPECTATIONS.json.

  python -B hybrid_build_master_offline.py selftest
      Loads hybrid_build_master.py idle (no ARGS), then builds the full Urban graph + MMA_0 rewire against a MOCK
      engine whose pin/output names are MEASURED (S1 GRAPH_AFTER_23156.json rows for Multiply/Add/Divide/Max/
      Saturate/Normalize/LinearInterpolate/Constant3Vector/TextureSample/TextureObjectParameter/Scalar/Vector
      parameters/LandscapeLayerSample/LandscapeLayerCoords; MW master MMA_0 27 input names and MW_MWAM_Water
      outputs from AstraMWInventory/native_inventory_complete.json; PixelDepth single output is INFERRED and
      asserted live by Builder.link). Checks: every link names an existing pin/output, '' is refused on
      multi-output sources, required pins connected, float dimensions consistent, MMA_0 pin dimensions,
      reachability from MMA_0, canvas, desc marker, sampler derivation table, texture verdicts, ARGS validation,
      and that canonical() of engine-shaped rows reproduces the expectations. It proves Python wiring only.
  python -B hybrid_build_master_offline.py expectations [--force]
      Runs selftest, then writes Hybrid_Auto/HYBRID_EDIT_EXPECTATIONS.json (planned nodes/edges/params for both
      texture sets, bound to hybrid_build_master.py sha256) which build mode compares against.
  python -B hybrid_build_master_offline.py staticscan
      AST scan of every Hybrid_Auto/*.py: save calls only in hybrid_assign_and_save.py do_save (2x save_packages +
      save_map); no save_assets / Save All / prepare / verify_landscape / get_material_info / cook / bake calls; no
      MW vendor object as an argument (or receiver) of a mutating call; duplicate_asset destination is COPY_PKG; no
      file/name dunder or 'main' tokens in the in-editor scripts (runner convention).
  python -B hybrid_build_master_offline.py argscheck
      Validates every Hybrid_Auto/Args/*.json against its script's validate() (placeholders '<FILL...>' replaced by
      typed dummies) and checks script_sha256 / expectations_sha256 / SCRIPT_PINS.json against the current files.
"""
import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / 'hybrid_build_master.py'
OUT = HERE / 'HYBRID_EDIT_EXPECTATIONS.json'
SCRIPTS = {'hybrid_build_master.py', 'hybrid_assign_and_save.py', 'hybrid_verify_fresh.py'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, name):
    sys.dont_write_bytecode = True
    assert 'unreal' not in sys.modules, 'offline only'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.RESULT.get('idle') is True and 'unreal' not in sys.modules, 'target must be idle without ARGS'
    return module


# ------------------------------------------------------------------ mock engine
class Owner:
    def __init__(self, name):
        self.name, self.nodes = name, []


class Expr:
    CLASS, INPUTS, OUTPUTS = 'MaterialExpression', (), ('',)

    def __init__(self, owner):
        self.owner, self.props, self.edges = owner, {}, {}
        self.index = sum(1 for n in owner.nodes if n.CLASS == self.CLASS)

    def get_class(self):
        return types.SimpleNamespace(get_name=lambda: self.CLASS)

    def get_name(self):
        return getattr(self, 'fixed_name', None) or '%s_%d' % (self.CLASS, self.index)

    def set_editor_property(self, key, value):
        self.props[key] = value
        if key == 'texture' and self.CLASS.endswith('TextureObjectParameter'):
            self.props['sampler_type'] = 'AUTO_FROM_TEXTURE'      # mimics AutoSetSampleType

    def get_editor_property(self, key):
        return self.props[key]

    def input_names(self):
        return list(self.INPUTS)

    def output_names(self):
        return list(self.OUTPUTS)


def cls(name, inputs=(), outputs=('',)):
    return type(name, (Expr,), {'CLASS': 'MaterialExpression' + name, 'INPUTS': tuple(inputs), 'OUTPUTS': tuple(outputs)})


AB = ('A', 'B')
RGBA_OUT = ('RGB', 'R', 'G', 'B', 'A', 'RGBA')                       # M: S1 GRAPH_AFTER_23156.json
MMA_INPUTS = ('BaseColor', 'Metallic', 'Specular', 'Roughness', 'Anisotropy', 'EmissiveColor', 'Opacity', 'OpacityMask',
              'Normal', 'Tangent', 'WorldPositionOffset', 'SubsurfaceColor', 'ClearCoat', 'ClearCoatRoughness',
              'AmbientOcclusion', 'Refraction', 'CustomizedUVs_0', 'CustomizedUVs_1', 'CustomizedUVs_2',
              'CustomizedUVs_3', 'CustomizedUVs_4', 'CustomizedUVs_5', 'CustomizedUVs_6', 'CustomizedUVs_7',
              'PixelDepthOffset', 'ShadingModel', 'Displacement')      # M: native_inventory_complete.json MMA_0
WATER_OUT = ('BaseColor', 'Metallic', 'Specular', 'Roughness', 'Normal', 'WaterRefractionUV')   # M: MF_14
CLASSES = {n: cls(n, AB) for n in ('Multiply', 'Add', 'Divide', 'Max')}
CLASSES.update({
    'Saturate': cls('Saturate', ('None',)), 'Normalize': cls('Normalize', ('VectorInput',)),
    'LinearInterpolate': cls('LinearInterpolate', ('A', 'B', 'Alpha')),
    'Constant3Vector': cls('Constant3Vector', (), ('', 'R', 'G', 'B')),
    'TextureSample': cls('TextureSample', ('UVs', 'Tex', 'Apply View MipBias'), RGBA_OUT),
    'ScalarParameter': cls('ScalarParameter'), 'VectorParameter': cls('VectorParameter', (), RGBA_OUT),
    'TextureObjectParameter': cls('TextureObjectParameter', ('UVs', 'Apply View MipBias')),
    'LandscapeLayerSample': cls('LandscapeLayerSample'), 'LandscapeLayerCoords': cls('LandscapeLayerCoords'),
    'PixelDepth': cls('PixelDepth'),
    'StaticSwitchParameter': cls('StaticSwitchParameter', ('True', 'False')),
    'MaterialFunctionCall': cls('MaterialFunctionCall', ('BaseColor', 'Specular', 'Roughness', 'Normal', 'WorldCoords',
                                                         'WaterMask'), WATER_OUT),
    'MakeMaterialAttributes': cls('MakeMaterialAttributes', MMA_INPUTS),
})


class MockLib:
    links = 0

    @staticmethod
    def create_material_expression(owner, kind, x, y):
        e = kind(owner)
        e.props.update(material_expression_editor_x=x, material_expression_editor_y=y)
        owner.nodes.append(e)
        return e

    @staticmethod
    def get_material_expression_input_names(e):
        return e.input_names()

    @staticmethod
    def get_material_expression_output_names(e):
        return e.output_names()

    @staticmethod
    def connect_material_expressions(src, output, dst, pin):
        assert pin in dst.input_names() and output in src.output_names()
        dst.edges[pin] = (src, output)
        MockLib.links += 1
        return True


def mock_unreal():
    u = types.SimpleNamespace(**{'MaterialExpression' + k: v for k, v in CLASSES.items()})
    u.Name = str
    u.LinearColor = lambda *v: tuple(float(x) for x in v)
    u.TextureMipValueMode = types.SimpleNamespace(TMVM_NONE='TMVM_NONE')
    return u


def mock_t3d(owner):
    """T3D text for a mock material in the measured ObjectExporterT3D shape (declaration + definition blocks;
    'Pin=(Expression="/Script/Engine.<Class>'<Material>:<Name>'",OutputIndex=N)' with N omitted when 0;
    'Outputs(N)=(OutputName="...")' on function calls)."""
    lines = ['Begin Object Class=/Script/Engine.Material Name="%s" ExportPath="x"' % owner.name]
    for e in owner.nodes:
        lines += ['   Begin Object Class=/Script/Engine.%s Name="%s" ExportPath="x"' % (e.CLASS, e.get_name()), '   End Object']
    for e in owner.nodes:
        lines.append('   Begin Object Name="%s" ExportPath="x"' % e.get_name())
        for pin, (src, output) in e.edges.items():
            index = src.output_names().index(output) if output in src.output_names() else 0
            ref = 'Expression="/Script/Engine.%s\'%s:%s\'"' % (src.CLASS, owner.name, src.get_name())
            lines.append('      %s=(%s%s)' % (pin.replace(' ', '_'), ref, ',OutputIndex=%d' % index if index else ''))
        if e.CLASS.endswith('MaterialFunctionCall'):
            lines += ['      Outputs(%d)=(OutputName="%s")' % (i, n) for i, n in enumerate(e.output_names())]
        lines += ['      MaterialExpressionEditorX=%s' % e.props.get('material_expression_editor_x', 0),
                  '      Material="/Script/Engine.Material\'%s\'"' % owner.name, '   End Object']
    lines.append('End Object')
    return '\r\n'.join(lines) + '\r\n'


# ------------------------------------------------------------------ dimension inference
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


ANCHOR_DIMS = {('StaticSwitchParameter', ''): 3, ('MaterialFunctionCall', 'Normal'): 3,
               ('MaterialFunctionCall', 'Roughness'): 1, ('MaterialFunctionCall', 'Specular'): 1,
               ('MaterialFunctionCall', 'Metallic'): 1, ('MaterialFunctionCall', 'BaseColor'): 3}


def dim(source, memo=None):
    memo = {} if memo is None else memo
    e, output = source
    key = (id(e), output)
    if key in memo:
        return memo[key]
    c = e.CLASS.replace('MaterialExpression', '')
    pin = lambda name: dim(e.edges[name], memo) if name in e.edges else None
    where = e.props.get('desc', e.get_name())
    if (c, output) in ANCHOR_DIMS:
        d = ANCHOR_DIMS[(c, output)]
    elif c in ('ScalarParameter', 'LandscapeLayerSample', 'PixelDepth'):
        d = 1
    elif c == 'LandscapeLayerCoords':
        d = 2
    elif c == 'VectorParameter':
        d = {'RGB': 3, 'RGBA': 4}.get(output, 1)
    elif c == 'TextureObjectParameter':
        d = 'tex'
    elif c == 'TextureSample':
        assert pin('UVs') == 2 and pin('Tex') == 'tex', ('bad sample inputs', where)
        d = {'RGB': 3, 'RGBA': 4}.get(output, 1)
    elif c == 'Constant3Vector':
        d = 3 if output == '' else 1
    elif c in ('Multiply', 'Add', 'Divide', 'Max'):
        d = combine(pin('A') if 'A' in e.edges else 1, pin('B') if 'B' in e.edges else 1, where)
    elif c == 'LinearInterpolate':
        d = combine(combine(pin('A') if 'A' in e.edges else 1, pin('B'), where), pin('Alpha'), where + ':Alpha')
        assert pin('Alpha') == 1, ('lerp alpha not scalar', where)
    elif c == 'Saturate':
        d = pin('None')
    elif c == 'Normalize':
        d = pin('VectorInput')
        assert d in (2, 3, 4), ('normalize of scalar', where)
    else:
        raise AssertionError(('no dim rule', c))
    memo[key] = d
    return d


def required_pins(e):
    optional = {'Apply View MipBias', 'UVs'} if e.CLASS.endswith('TextureObjectParameter') else {'Apply View MipBias'}
    if 'const_a' in e.props:
        optional.add('A')
    if 'const_b' in e.props:
        optional.add('B')
    return [n for n in e.input_names() if n not in optional]


def reach_mock(start):
    seen, stack = set(), [start]
    while stack:
        cur = stack.pop()
        if id(cur) in seen:
            continue
        seen.add(id(cur))
        stack.extend(src for src, _ in cur.edges.values())
    return seen


def plain(value):
    if isinstance(value, tuple):
        return [float(x) for x in value]
    return value


# ------------------------------------------------------------------ selftest
def unit_checks(m):
    d = m.derive_sampler
    assert d(True, 'TC_DEFAULT', 'TEXTUREGROUP_WORLD', False) == ('COLOR', None)
    assert d(True, '<TextureCompressionSettings.TC_BC7: 13>', 'TEXTUREGROUP_WORLD', False)[0] == 'COLOR'
    assert d(False, 'TC_NORMALMAP', 'TEXTUREGROUP_WORLD_NORMAL_MAP', False) == ('NORMAL', None)
    assert d(False, 'TC_MASKS', 'TEXTUREGROUP_WORLD', False) == ('MASKS', None)
    assert d(False, 'TC_GRAYSCALE', 'TEXTUREGROUP_WORLD', False) == ('LINEAR_GRAYSCALE', None)
    assert d(True, 'TC_GRAYSCALE', 'TEXTUREGROUP_WORLD', False) == ('GRAYSCALE', None)
    assert d(False, 'TC_DEFAULT', 'TEXTUREGROUP_WORLD', False) == ('LINEAR_COLOR', None)
    assert d(False, 'TC_DEFAULT', 'TEXTUREGROUP_8BIT_DATA', False) == ('DATA', None)
    assert d(True, 'TC_DEFAULT', 'TEXTUREGROUP_WORLD', True)[0] is None
    assert d(False, 'TC_EDITOR_ICON', 'TEXTUREGROUP_WORLD', False)[0] is None
    assert m.enum_name('<TextureCompressionSettings.TC_NORMALMAP: 1>') == 'TC_NORMALMAP'
    assert m.enum_name('<MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE: 10>') == 'SAMPLERTYPE_LINEAR_GRAYSCALE'
    v = m.texture_verdict
    assert v('linear', True, 'GRAYSCALE', False)[0] is False and v('linear', True, 'COLOR', False)[0] is False
    assert v('linear', False, 'LINEAR_GRAYSCALE', False)[0] and v('linear', False, 'MASKS', None)[0]
    assert v('color', True, 'COLOR', False)[0] and not v('color', False, 'LINEAR_COLOR', False)[0]
    assert v('normal', False, 'NORMAL', False)[0] and not v('normal', False, 'NORMAL', True)[0]
    s = m.select_texture_set
    assert s({'asphalt_cracked': True, 'concrete_plate': True}) == ('asphalt_cracked', 'INSPECTED_READ_ONLY')
    assert s({'asphalt_cracked': False, 'concrete_plate': True}) == ('concrete_plate', 'STOP_TEXTURE_FALLBACK_REQUIRED')
    assert s({'asphalt_cracked': False, 'concrete_plate': False}) == (None, 'STOP_NO_TEXTURE_SET')
    assert m.short('/Game/A/M.M:MaterialExpressionAdd_3') == 'MaterialExpressionAdd_3' and m.short(None) is None
    assert set(m.MMA_TARGETS) == {'BaseColor', 'Normal', 'Roughness', 'Specular', 'AmbientOcclusion'}
    assert len(m.TEXTURE_FILES) == 7 and all(f.startswith('Content/ModularCourtyard/Textures/') for f in m.TEXTURE_FILES)
    good = {'mode': 'inspect', 'label': 'x_1', 'expected_pid': 1, 'lease_owner': 'GEOCITY_GROUND_HYBRID',
            'manager_thread_id': 'a-b', 'operator_thread_id': 'a-b', 'script_file': 'C:/x.py', 'script_sha256': '0' * 64,
            'profile_sha256': '1' * 64, 'expected_map_sha256': '2' * 64, 'vendor_sha256': {'desert': '3' * 64, 'master': '4' * 64}}
    assert m.validate(dict(good)) == 'inspect'
    for bad in ({'expected_pid': True}, {'label': 'a b'}, {'extra': 1}, {'vendor_sha256': {'master': '4' * 64}}):
        try:
            m.validate(dict(good, **bad))
            raise AssertionError(('validate accepted', bad))
        except RuntimeError:
            pass
    build = dict(good, mode='build', inspect_receipt='C:/r.json', inspect_receipt_sha256='5' * 64,
                 texture_set='asphalt_cracked', expectations_file='C:/e.json', expectations_sha256='6' * 64)
    assert m.validate(dict(build)) == 'build'
    for bad in ({'texture_set': 'x'}, {'lease_owner': 'OTHER'}, {'fallback_acknowledged_by_manager': 'yes'}):
        try:
            m.validate(dict(build, **bad))
            raise AssertionError(('validate accepted', bad))
        except RuntimeError:
            pass
    return 'PASSED'


def build_mock(m, set_name):
    u, MockLib.links = mock_unreal(), 0
    copy = Owner('M_GeoCityAuto')
    ssp = MockLib.create_material_expression(copy, CLASSES['StaticSwitchParameter'], 1744, 784)
    mf = MockLib.create_material_expression(copy, CLASSES['MaterialFunctionCall'], 416, 416)
    mma = MockLib.create_material_expression(copy, CLASSES['MakeMaterialAttributes'], 2225, 948)
    ssp.fixed_name, mf.fixed_name, mma.fixed_name = m.SSP16, m.MF14, m.MMA
    vendor = list(copy.nodes)
    MockLib.connect_material_expressions(ssp, '', mma, 'BaseColor')
    for pin in ('Metallic', 'Specular', 'Roughness', 'Normal'):
        MockLib.connect_material_expressions(mf, pin, mma, pin)       # M: T3D OutputIndex 1/2/3/4 (pin-matched)
    before = dict(mma.edges)
    true, water = m.mma_true_outputs(m.t3d_blocks(mock_t3d(copy)), WATER_OUT)
    assert {p: (v['output_index'], v['output']) for p, v in true.items()} == {
        'BaseColor': (0, ''), 'Metallic': (1, 'Metallic'), 'Specular': (2, 'Specular'), 'Roughness': (3, 'Roughness'),
        'Normal': (4, 'Normal')}, true
    g = m.Builder(u, MockLib, copy, m.MARK, m.CANVAS, 'SSM_WRAP_WORLD_GROUP_SETTINGS')
    # Negative check: '' on a multi-output source must be refused (would wire MW_MWAM_Water:BaseColor).
    probe = Owner('probe')
    target = MockLib.create_material_expression(probe, CLASSES['Saturate'], 0, 0)
    try:
        g.link((mf, ''), target, 'None')
        raise AssertionError("Builder.link accepted '' on a multi-output node")
    except RuntimeError:
        pass
    spec = m.TEXTURE_SETS[set_name]
    samplers = {'Urban_BaseColor': 'SAMPLERTYPE_COLOR', 'Urban_Normal': 'SAMPLERTYPE_NORMAL',
                'Urban_Roughness': 'SAMPLERTYPE_MASKS', 'Urban_AO': 'SAMPLERTYPE_MASKS'}
    textures = {p: 'TEXTURE:' + path for p, (path, role) in spec['textures'].items()}
    P = m.make_params(g, textures, samplers)
    anchors = {'base_color': (ssp, true['BaseColor']['output']), 'normal': (mf, true['Normal']['output']),
               'roughness': (mf, true['Roughness']['output']), 'specular': (mf, true['Specular']['output'])}
    finals = m.build_urban(g, anchors, P, samplers, spec['channels'])
    for pin, source in finals.items():
        g.link(source, mma, pin)
    new = [n for n in copy.nodes if n not in vendor]
    assert new == g.added and len(new) == len(g.labels), 'node bookkeeping'
    missing = [(e.props['desc'], n) for e in new for n in required_pins(e) if n not in e.edges]
    assert not missing, ('unconnected required pins', missing[:10])
    memo = {}
    for e in new:
        if e.output_names() == ['']:
            dim((e, ''), memo)
    mma_dims = {pin: dim(mma.edges[pin], memo) for pin in m.MMA_TARGETS}
    assert mma_dims == {'BaseColor': 3, 'Normal': 3, 'Roughness': 1, 'Specular': 1, 'AmbientOcclusion': 1}, mma_dims
    changed = sorted(p for p in mma.edges if mma.edges[p] != before.get(p))
    assert changed == sorted(m.MMA_TARGETS) and mma.edges['Metallic'] == (mf, 'Metallic'), changed
    reached = reach_mock(mma)
    assert all(id(e) in reached for e in new), 'node not reachable from MMA_0'
    assert all(e.props['desc'] == m.MARK + label for label, e in g.labels.items())
    assert all(e.props['material_expression_editor_x'] >= 2500 and e.props['material_expression_editor_y'] >= 1400 for e in new)
    samples = [e for e in new if e.CLASS.endswith('TextureSample')]
    assert len(samples) == 5 and all(e.props['sampler_source'] == 'SSM_WRAP_WORLD_GROUP_SETTINGS' for e in samples)
    tparams = [e for e in new if e.CLASS.endswith('TextureObjectParameter')]
    assert all(e.props['sampler_source'] == 'SSM_WRAP_WORLD_GROUP_SETTINGS' and e.props['sampler_type'].startswith('SAMPLERTYPE_')
               for e in tparams) and len(tparams) == 4
    params = sorted(e.props['parameter_name'] for e in new if 'Parameter' in e.CLASS)
    assert params == sorted(list(m.URBAN_SCALARS) + list(m.URBAN_VECTORS) + list(m.URBAN_TEXTURES)) and len(params) == 15
    layers = sorted(e.props['parameter_name'] for e in new if e.CLASS.endswith('LandscapeLayerSample'))
    assert layers == sorted(m.LAYERS), layers
    # Canonical expectations, keyed by desc label; anchors by role.
    label_of = {id(e): label for label, e in g.labels.items()}
    ref = lambda src: ('new:' + label_of[id(src)]) if id(src) in label_of else \
        {id(ssp): 'anchor:debug_bake', id(mf): 'anchor:water'}[id(src)]
    nodes = {}
    for label, e in g.labels.items():
        props = {k: plain(v) for k, v in e.props.items() if k in m.CANON_PROPS}
        nodes[label] = {'class': e.CLASS, 'edges': {pin: [ref(src), out] for pin, (src, out) in e.edges.items()},
                        'x': e.props['material_expression_editor_x'], 'y': e.props['material_expression_editor_y'],
                        'props': props}
    sample_textures = {label_of[id(e)]: label_of[id(e.edges['Tex'][0])] for e in samples}
    # Exercise the engine-side canonical() on describe()-shaped rows built from the mock.
    names = {id(e): e.get_name() for e in copy.nodes}
    rows = {}
    for e in copy.nodes:
        rows[names[id(e)]] = {'class': e.CLASS, 'edges': {pin: ({'source': names[id(e.edges[pin][0])], 'output': e.edges[pin][1]}
                                                               if pin in e.edges else {'source': None, 'output': None})
                                                         for pin in e.input_names()},
                              'properties': {k: plain(v) for k, v in e.props.items()}}
    labels = {names[id(e)]: label for label, e in g.labels.items()}
    refs = {names[id(e)]: 'new:' + label for label, e in g.labels.items()}
    refs.update({names[id(ssp)]: 'anchor:debug_bake', names[id(mf)]: 'anchor:water'})
    assert m.compare_canon(m.canonical(rows, labels, refs), nodes) == [], 'canonical() differs from expectations'
    broken = json.loads(json.dumps(nodes))
    broken['OutRoughness']['edges']['A'] = ['anchor:water', 'BaseColor']
    assert m.compare_canon(m.canonical(rows, labels, refs), broken), 'compare_canon missed a wrong edge'
    assert m.reach(rows, [names[id(mma)]]) >= set(labels), 'reach() over rows'
    short_of = {'new:' + v: k for k, v in labels.items()}
    short_of.update({'anchor:debug_bake': m.SSP16, 'anchor:water': m.MF14})
    refs_expected = m.expected_refs(nodes, short_of, {names[id(e)]: e.output_names() for e in copy.nodes})
    mma_expected = {pin: [short_of['new:' + label], 0] for pin, label in m.MMA_TARGETS.items()}
    mma_expected['Metallic'] = [m.MF14, 1]
    post = m.t3d_blocks(mock_t3d(copy))
    assert m.t3d_check(post, mma_expected, refs_expected) == [], m.t3d_check(post, mma_expected, refs_expected)[:3]
    assert refs_expected[short_of['new:OutSpecular']] == sorted([[m.MF14, 2], [short_of['new:Urban_Specular'], 0],
                                                                 [short_of['new:UrbanMask'], 0]])
    wrong = g.labels['OutSpecular']
    saved_edge = wrong.edges['A']
    wrong.edges['A'] = (mf, 'Metallic')                     # the PID23068 legacy-reader wiring
    assert m.t3d_check(m.t3d_blocks(mock_t3d(copy)), mma_expected, refs_expected), 't3d_check missed Water:Metallic'
    wrong.edges['A'] = saved_edge
    bad_vendor = Owner('M_GeoCityAuto')
    b_ssp, b_mf, b_mma = (MockLib.create_material_expression(bad_vendor, CLASSES[c], 0, 0)
                          for c in ('StaticSwitchParameter', 'MaterialFunctionCall', 'MakeMaterialAttributes'))
    b_ssp.fixed_name, b_mf.fixed_name, b_mma.fixed_name = m.SSP16, m.MF14, m.MMA
    MockLib.connect_material_expressions(b_ssp, '', b_mma, 'BaseColor')
    for pin in ('Metallic', 'Specular', 'Roughness', 'Normal'):
        MockLib.connect_material_expressions(b_mf, 'Metallic' if pin == 'Specular' else pin, b_mma, pin)
    try:
        m.mma_true_outputs(m.t3d_blocks(mock_t3d(bad_vendor)), WATER_OUT)
        raise AssertionError('mma_true_outputs accepted Specular <- Water:Metallic')
    except RuntimeError:
        pass
    classes = {}
    for e in new:
        classes[e.CLASS] = classes.get(e.CLASS, 0) + 1
    report = {'added_node_count': len(new), 'links': MockLib.links, 'class_counts': dict(sorted(classes.items())),
              'mma_pin_dims': mma_dims, 'texture_samples': len(samples), 'parameters': len(params),
              'layer_samples': layers, 'texture_param_auto_sampler_notes': g.notes}
    return nodes, sample_textures, report


INVENTORY = HERE.parent / 'S1_Prep/AstraMWInventory/native_inventory_complete.json'
LEDGER = HERE.parents[3] / 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/LAST_SUCCESSFUL_WORKFLOW_STATE.json'
TINTS_P1 = HERE.parent / 'PathB_MW/TINT_PRESETS.json'


def assign_verify_checks():
    """Pure logic of hybrid_assign_and_save.py / hybrid_verify_fresh.py against MEASURED data (read-only)."""
    a = load(HERE / 'hybrid_assign_and_save.py', 'hybrid_assign_offline_copy')
    v = load(HERE / 'hybrid_verify_fresh.py', 'hybrid_verify_offline_copy')
    inv = json.loads(INVENTORY.read_text(encoding='utf-8'))
    desert_row = [x for x in inv['assets'] if isinstance(x, dict) and x.get('path') == a.DESERT][0]
    kinds = {'scalar': 'scalars', 'vector': 'vectors', 'texture': 'textures', 'static_switch': 'switches'}
    desert = {k: {} for k in kinds.values()}
    for p in desert_row['parameters']:
        value = p['effective_value']
        if p['type'] == 'vector':
            value = [value[c] for c in 'rgba']
        desert[kinds[p['type']]][p['name']] = value
    assert sum(len(x) for x in desert.values()) == a.MW_PARAM_COUNT, 'inventory DesertExample count'
    preset = json.loads(TINTS_P1.read_text(encoding='utf-8'))['presets']['P1_gaza_pale_sand']['vectors']
    tints = {n: [preset[n][c] for c in 'rgb'] for n in a.TINT_PARAMS}
    mi = json.loads(json.dumps(desert))
    mi['switches'].update(a.SET_SWITCHES)
    for n in a.TINT_PARAMS:
        mi['vectors'][n] = tints[n] + [1.0]
    for n, value in a.DESERT_SCALARS.items():
        if n in mi['scalars']:
            assert abs(mi['scalars'][n] - value) < 1e-6, ('Desert scalar pin differs from the inventory', n)
    for n, path in a.DESERT_TEXTURES.items():
        assert mi['textures'][n] == path, ('Desert texture pin differs from the inventory', n)
    for kind, names in a.URBAN_NAMES.items():
        for n in names:
            mi[kind][n] = 1.0
    rows, diff, expected = a.parity(desert, mi, tints)
    assert len(rows) == 99 and diff == expected and len(diff) == 11, (len(rows), diff, expected)
    assert set(diff) == set(a.FORCED_SWITCH_DIFFS) | set(a.TINT_PARAMS)
    bad = json.loads(json.dumps(mi))
    bad['scalars']['MW_RoughnessPower'] = 0.5
    assert a.parity(desert, bad, tints)[1] != a.parity(desert, bad, tints)[2], 'parity missed an extra difference'
    assert a.values_equal(mi, json.loads(json.dumps(mi))) and not a.values_equal(mi, bad)
    common = {'label': 'x', 'expected_pid': 1, 'lease_owner': 'GEOCITY_GROUND_HYBRID', 'manager_thread_id': 'a',
              'operator_thread_id': 'a', 'script_file': 'C:/x.py', 'script_sha256': '0' * 64, 'profile_sha256': '1' * 64,
              'expected_map_sha256': '2' * 64, 'vendor_sha256': {'desert': '3' * 64, 'master': '4' * 64},
              'build_receipt': 'C:/b.json', 'build_receipt_sha256': '5' * 64}
    urban = {'Urban_Amount': 1.0, 'Urban_PadAmount': 1.0, 'Urban_RoadAmount': 1.0, 'Urban_TileCm': 400.0,
             'Urban_FarScale': 6.0, 'Urban_FarDistanceCm': 4000.0, 'Urban_RoughnessScale': 1.0,
             'Urban_NormalStrength': 1.0, 'Urban_Specular': 0.5, 'Urban_Tint': [2.5, 0.4, 0.4]}
    apply = dict(common, mode='apply', purpose='mask_proof', tints=tints, urban=urban)
    assert a.validate(json.loads(json.dumps(apply))) == 'apply'
    for change in ({'purpose': 'final'}, {'urban': dict(urban, Urban_GridCm=100.0)}, {'urban': dict(urban, Urban_Amount=1.5)},
                   {'tints': dict(tints, MW_RockColorCorrection=[4.0, 1.0, 1.0])}, {'lease_owner': 'OTHER'}):
        try:
            a.validate(dict(apply, **change))
            raise AssertionError(('assign validate accepted', change))
        except RuntimeError:
            pass
    save = dict(common, mode='save', scope='master_mi_map', apply_receipt='C:/a.json', apply_receipt_sha256='6' * 64,
                approval_receipt='C:/p.json', approval_receipt_sha256='7' * 64)
    assert a.validate(dict(save)) == 'save'
    try:
        a.validate(dict(save, scope='mi_only'))
        raise AssertionError('save accepted a scope other than master_mi_map')
    except RuntimeError:
        pass
    ver = {'mode': 'verify', 'label': 'v', 'expected_pid': 2, 'lease_owner': 'GEOCITY_GROUND_HYBRID', 'manager_thread_id': 'a',
           'operator_thread_id': 'a', 'script_file': 'C:/v.py', 'script_sha256': '0' * 64, 'profile_sha256': '1' * 64,
           'save_receipt': 'C:/s.json', 'save_receipt_sha256': '2' * 64, 'build_receipt': 'C:/b.json',
           'build_receipt_sha256': '3' * 64, 'post_regeneration': False}
    assert v.validate(dict(ver)) == 'verify'
    try:
        v.validate(dict(ver, post_regeneration=True))
        raise AssertionError('post_regeneration accepted without expected_map_sha256')
    except RuntimeError:
        pass
    assert v.validate(dict(ver, post_regeneration=True, expected_map_sha256='4' * 64)) == 'verify'
    ledger = json.loads(LEDGER.read_text(encoding='utf-8'))
    paths = ledger.get('named_generated_dependency_paths') or []
    assert all(v.layer_info_ok(paths, l) for l in v.LAYERS), 'measured B2 ledger LayerInfo suffix format'
    assert not v.layer_info_ok(paths, 'RemoveFoliage') and not v.layer_info_ok(['/x/y_landscape_Sand_Path_1'], 'Sand_Path')
    return {'assign_parity_measured_desert': {'compared': len(rows), 'differing': diff},
            'assign_validate': 'PASSED', 'verify_validate': 'PASSED',
            'verify_layerinfo_suffix_on_measured_B2_ledger': sorted(p for p in paths if '_landscape_' in p)}


PROBE_T3D = HERE.parents[1] / 'Operator/MWPreview_20261006/MTL_MWAM_AutoMaterial_MASTER.t3d'


def t3d_probe_check(m, rows):
    """MEASURED vendor T3D (coordinator probe, PID23068) through the same parser/gates build/inspect use."""
    if not PROBE_T3D.is_file():
        return {'skipped': 'probe T3D absent: ' + str(PROBE_T3D)}
    blocks = m.t3d_blocks(m.t3d_text(PROBE_T3D.read_bytes()))
    exprs = [k for k in blocks if k.startswith('MaterialExpression') and not k.startswith('MaterialExpressionComment')]
    assert len(exprs) == m.VENDOR_NODE_COUNT, len(exprs)          # + 32 comment boxes, not material expressions
    true, water = m.mma_true_outputs(blocks, rows[m.MF14]['output_names'])
    anchors = m.anchors_check(rows, {'material_attributes': m.MMA}, blocks)
    assert anchors['mma_true_outputs'] == true
    return {'file': str(PROBE_T3D), 'sha256': sha(PROBE_T3D), 'water_outputs': water,
            'mma_true_outputs': {p: [v['source'], v['output_index'], v['output']] for p, v in true.items()}}


def vendor_dump_check(m):
    """Pre-run the inspect gates that need no engine against the MEASURED MW master dump (output names unknown
    offline -> '' here; the live inspect asserts them)."""
    inv = json.loads(INVENTORY.read_text(encoding='utf-8'))
    master = [x for x in inv['assets'] if isinstance(x, dict) and x.get('path') == m.VENDOR_OBJ][0]
    rows = {}
    for n in master['nodes']:
        rows[n['name']] = {'class': n['class'], 'properties': dict(n['properties']),
                           'edges': {pin: {'source': src, 'output': ''} for pin, src in zip(n['input_names'], n['input_nodes'])}}
    assert len(rows) == m.VENDOR_NODE_COUNT, len(rows)
    outputs = master['material_outputs']
    roots = {'material_attributes': outputs['MP_MATERIAL_ATTRIBUTES']}
    assert roots['material_attributes'] == m.MMA
    samples = m.layer_samples(rows)
    assert sorted(samples.values()) == [m.MW_LAYER], samples
    reachable = m.reach(rows, [m.MMA] + m.output_nodes(rows))
    assert all(k in reachable for k in samples), 'RemoveFoliage unreachable in the measured dump'
    assert sorted(m.output_nodes(rows)) == ['MaterialExpressionLandscapeGrassOutput_0',
                                            'MaterialExpressionLandscapePhysicalMaterialOutput_0'], m.output_nodes(rows)
    mma = rows[m.MMA]['edges']
    assert {p: mma[p]['source'] for p in m.MMA_SOURCES} == m.MMA_SOURCES and mma['AmbientOcclusion']['source'] is None
    assert not [p for p, e in mma.items() if e['source'] and p not in m.MMA_SOURCES]
    assert rows[m.SSP16]['properties']['parameter_name'] == 'MW_DebugBake'
    assert rows[m.MF14]['properties']['material_function'] == m.WATER_FUNCTION
    busy = [k for k, r in rows.items() if r['properties'].get('material_expression_editor_x', 0) >= m.CANVAS['x0'] - 260
            and r['properties'].get('material_expression_editor_y', 0) >= m.CANVAS['y0'] - 260]
    assert not busy, busy
    reach_from = {k: [o for o in [m.MMA] + m.output_nodes(rows) if k in m.reach(rows, [o])] for k in samples}
    for n in master['nodes']:
        rows[n['name']]['output_names'] = n['output_names']
    return {'rows': len(rows), 'remove_foliage_reached_from': reach_from, 'canvas_free': True,
            'mma_sources_match': True, 't3d_probe': t3d_probe_check(m, rows)}


def selftest():
    m = load(TARGET, 'hybrid_build_master_offline_copy')
    report = {'unit_checks': unit_checks(m), 'texture_sets': {}, 'assign_verify_checks': assign_verify_checks(),
              'vendor_dump_check': vendor_dump_check(m)}
    sets = {}
    for name in m.TEXTURE_SETS:
        nodes, sample_textures, rep = build_mock(m, name)
        sets[name] = {'nodes': nodes, 'sample_textures': sample_textures}
        report['texture_sets'][name] = rep
    a, c = sets['asphalt_cracked']['nodes'], sets['concrete_plate']['nodes']
    diff = sorted(k for k in a if a[k] != c[k])
    assert diff == ['RoughnessScaled'] and sets['asphalt_cracked']['sample_textures'] == sets['concrete_plate']['sample_textures'], diff
    report['set_difference'] = {'labels': diff, 'reason': 'roughness channel R (Asphalt roughness map) vs G (Concrete ORM)'}
    report['status'] = 'SELFTEST_PASSED_MOCK_ENGINE'
    report['scope'] = ('Python wiring/pin-name/dimension logic only; engine behaviour (duplicate_asset, compile, '
                       'sampler validation, PixelDepth output names) is asserted at run time by hybrid_build_master.py.')
    return m, sets, report


def expectations(force):
    m, sets, report = selftest()
    count = report['texture_sets']['asphalt_cracked']['added_node_count']
    result = {
        'schema': 'environmentpipeline.ground_hybrid_expectations.v1',
        'status': 'OFFLINE_EXPECTATIONS_NOT_EXECUTED',
        'generated_from': {'target': str(TARGET), 'target_sha256': sha(TARGET),
                           'generator': str(Path(__file__).resolve()), 'generator_sha256': sha(Path(__file__).resolve())},
        'plan': 'Stage1_Ground/Hybrid_Auto/PLAN_HYBRID.md (Urban graph, Option A injection into MakeMaterialAttributes_0)',
        'node_desc_prefix': m.MARK, 'canvas': m.CANVAS, 'vendor_node_count': m.VENDOR_NODE_COUNT,
        'added_node_count': count, 'expected_node_count': m.VENDOR_NODE_COUNT + count,
        'mma_rewire': {pin: 'new:' + label for pin, label in m.MMA_TARGETS.items()},
        'mma_unchanged': {'Metallic': ['anchor:water', 'Metallic']},
        'anchors': {'debug_bake': m.SSP16, 'water': m.MF14, 'mma': m.MMA},
        'parameters': {'scalars': m.URBAN_SCALARS, 'vectors': {k: list(v) for k, v in m.URBAN_VECTORS.items()},
                       'textures': list(m.URBAN_TEXTURES), 'group': m.GROUP},
        'layer_samples_after': sorted(list(m.LAYERS) + [m.MW_LAYER]),
        'sample_textures': sets['asphalt_cracked']['sample_textures'],
        'texture_sets': {name: {'textures': {p: list(v) for p, v in m.TEXTURE_SETS[name]['textures'].items()},
                                'channels': m.TEXTURE_SETS[name]['channels'], 'nodes': sets[name]['nodes']}
                         for name in m.TEXTURE_SETS},
        'sampler_estimate': {'new_texture_samples': 5, 'all_shared_wrap': True,
                             'vendor_measured': {'num_samplers': 2, 'num_pixel_texture_samples': 48},
                             'gate_max_samplers': m.MAX_SAMPLERS},
        'selftest': report,
    }
    if OUT.exists() and not force:
        raise SystemExit('Refused: %s exists; pass --force to regenerate (then re-pin expectations_sha256)' % OUT)
    OUT.write_text(json.dumps(result, indent=1), encoding='utf-8', newline='\n')
    return {'file': str(OUT), 'sha256': sha(OUT), 'added_node_count': count, 'target_sha256': result['generated_from']['target_sha256']}


# ------------------------------------------------------------------ static scan
SAVE_CALLS = {'save_packages', 'save_map', 'save_asset', 'save_assets', 'save_directory', 'save_loaded_asset',
              'save_loaded_assets', 'save_dirty_packages', 'save_current_level', 'save_packages_with_dialog',
              'save_all', 'save_dirty_packages_with_dialog'}
MUTATING_CALLS = SAVE_CALLS | {'set_material_instance_parent', 'set_material_instance_scalar_parameter_value',
                               'set_material_instance_vector_parameter_value', 'set_material_instance_texture_parameter_value',
                               'set_material_instance_static_switch_parameter_value', 'update_material_instance',
                               'recompile_material', 'set_metadata_tag', 'delete_asset', 'rename_asset',
                               'connect_material_expressions', 'create_material_expression', 'connect_material_property',
                               'delete_material_expression', 'set_editor_property'}
FORBIDDEN_CALLS = {'prepare', 'verify_landscape', 'get_material_info', 'inspect_near_view', 'cook', 'bake',
                   'recook', 'bake_all_outputs', 'save_assets'}
VENDOR_NAMES = {'desert', 'vendor', 'DESERT', 'VENDOR_OBJ', 'VENDOR_PKG', 'WATER_FUNCTION'}


def staticscan():
    import ast
    import tokenize
    report = {}
    for path in sorted(HERE.glob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        rows = {'save_calls': [], 'forbidden_calls': [], 'vendor_mutations': [], 'dunder_tokens': []}
        parents = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node

        def enclosing(node):
            while node in parents:
                node = parents[node]
                if isinstance(node, ast.FunctionDef):
                    return node.name
            return '<module>'

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, 'id', None)
            if name in SAVE_CALLS:
                rows['save_calls'].append({'call': name, 'function': enclosing(node), 'line': node.lineno})
            if name in FORBIDDEN_CALLS:
                rows['forbidden_calls'].append({'call': name, 'line': node.lineno})
            if name in MUTATING_CALLS:
                receivers = [node.func.value] if isinstance(node.func, ast.Attribute) and name == 'set_editor_property' else []
                for arg in list(node.args) + receivers:
                    for sub in ast.walk(arg):
                        if isinstance(sub, ast.Name) and sub.id in VENDOR_NAMES:
                            rows['vendor_mutations'].append({'call': name, 'name': sub.id, 'line': node.lineno})
            if name == 'duplicate_asset':
                dest = node.args[1] if len(node.args) > 1 else None
                if not (isinstance(dest, ast.Name) and dest.id == 'COPY_PKG'):
                    rows['vendor_mutations'].append({'call': name, 'destination': ast.dump(dest) if dest else None})
        if path.name in SCRIPTS:
            with open(path, 'rb') as stream:
                for tok in tokenize.tokenize(stream.readline):
                    if tok.type == tokenize.NAME and tok.string in ('__file__', '__name__', 'main'):
                        rows['dunder_tokens'].append({'token': tok.string, 'line': tok.start[0]})
        report[path.name] = rows
    saves = [(f, r['function'], r['call']) for f, rows in report.items() for r in rows['save_calls']]
    assert all(f == 'hybrid_assign_and_save.py' and fn == 'do_save' for f, fn, c in saves), ('save outside save mode', saves)
    assert sorted(c for f, fn, c in saves) == ['save_map', 'save_packages', 'save_packages'], saves
    assert not any(rows['forbidden_calls'] or rows['vendor_mutations'] or rows['dunder_tokens'] for rows in report.values()), report
    return {'status': 'STATICSCAN_PASSED', 'save_calls': saves, 'files': sorted(report)}


# ------------------------------------------------------------------ args check
DUMMY = {'expected_pid': 12345}


def fill(value, key):
    if isinstance(value, dict):
        return {k: fill(v, k) for k, v in value.items()}
    if isinstance(value, str) and value.startswith('<FILL'):
        if key in DUMMY:
            return DUMMY[key]
        if key.endswith('sha256'):
            return 'f' * 64
        return 'C:/FILLED/' + key + '.json'
    return value


def argscheck():
    pins = json.loads((HERE / 'SCRIPT_PINS.json').read_text(encoding='utf-8'))
    current = {p.name: sha(p) for p in HERE.glob('*.py')}
    assert pins == current, ('SCRIPT_PINS.json differs from the current files', pins, current)
    modules = {name: load(HERE / name, name.replace('.py', '_argscheck')) for name in SCRIPTS}
    # Cross-script agreement on disk state (apply/save hard-require the build's disk/vendor snapshots; verify uses
    # the save receipt's): same file lists and identical results on the real project (file reads only).
    build, assign, verify = (modules[n] for n in ('hybrid_build_master.py', 'hybrid_assign_and_save.py', 'hybrid_verify_fresh.py'))
    root = HERE.parents[3]
    assert set(build.PROTECTED_FILES) == set(assign.PROTECTED_FILES), 'PROTECTED_FILES differ between build and assign'
    assert build.disk(root) == assign.disk(root), 'disk() differs between build and assign'
    snaps = [x.vendor_snapshot(root) for x in (build, assign, verify)]
    assert snaps[0] == snaps[1] == snaps[2] and snaps[0], 'vendor_snapshot() differs between scripts'
    for name in ('MAP', 'MI_PATH', 'PATHB_MI_PATH', 'COPY_OBJ', 'OWNER_VALUE', 'OUT_REL', 'HELPER_SHA', 'MAP_FILE', 'MI_FILE',
                 'COPY_FILE', 'PATHB_MI_FILE'):
        values = {getattr(x, name) for x in (build, assign, verify) if hasattr(x, name)}
        assert len(values) == 1, (name, values)
    for name in ('LEASE_OWNER', 'SCOPE', 'AUTHORING', 'VENDOR_FILES', 'PROFILE_REL'):
        assert getattr(build, name) == getattr(assign, name), name
    rows = {}
    for path in sorted((HERE / 'Args').glob('*.json')):
        args = json.loads(path.read_text(encoding='utf-8'))
        script = Path(args['script_file']).name
        assert script in SCRIPTS and Path(args['script_file']).parent == HERE, (path.name, args['script_file'])
        assert args['script_sha256'] == current[script], (path.name, 'script_sha256 stale')
        if 'expectations_sha256' in args:
            assert args['expectations_sha256'] == sha(OUT) and Path(args['expectations_file']) == OUT, (path.name, 'expectations pin')
        filled = fill(args, '')
        mode = modules[script].validate(filled)
        placeholders = sorted(k for k, v in args.items() if isinstance(v, str) and v.startswith('<FILL'))
        rows[path.name] = {'script': script, 'mode': mode, 'placeholders': placeholders}
    return {'status': 'ARGSCHECK_PASSED', 'pins': current, 'args': rows}


if __name__ == '__main__':
    command = sys.argv[1:2]
    if command == ['selftest']:
        print(json.dumps(selftest()[2], indent=1))
    elif command == ['expectations']:
        print(json.dumps(expectations('--force' in sys.argv[2:]), indent=1))
    elif command == ['argscheck']:
        print(json.dumps(argscheck(), indent=1))
    elif command == ['staticscan']:
        print(json.dumps(staticscan(), indent=1))
    else:
        raise SystemExit(__doc__)
