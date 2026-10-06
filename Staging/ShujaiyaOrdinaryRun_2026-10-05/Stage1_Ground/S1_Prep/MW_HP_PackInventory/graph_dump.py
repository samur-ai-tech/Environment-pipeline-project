"""Offline read-only material / material-function graph dump (no unreal import).
Prints one line per expression: name, class, key props, and wired inputs (input <- node:outputIndex).
Usage: python graph_dump.py <file.uasset> [--all]   (--all keeps Comment nodes)
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uasset_offline import Pkg, export_props

KEYS = ('ParameterName', 'DefaultValue', 'Group', 'Desc', 'Texture', 'SamplerSource', 'SamplerType', 'MaterialFunction',
        'InputName', 'InputType', 'OutputName', 'Description', 'Constant', 'R', 'G', 'B', 'A', 'ConstA', 'ConstB', 'ConstAlpha',
        'Text', 'Name', 'Code', 'OutputType', 'MinRange', 'MaxRange', 'bUseWorldspace', 'WorldPositionShaderOffset',
        'Coordinate', 'UTiling', 'VTiling', 'MappingType', 'TextureSize', 'ConstAdd', 'ConstExponent', 'ConstBase', 'Period',
        'FadeDistance', 'FadeLength', 'Absolute', 'Value', 'PreviewValue', 'bUseConstant', 'ConstantValue',
        'ExponentIn', 'Mapping', 'MappingScale', 'NoiseFunction', 'Scale', 'Quality', 'Levels', 'OutputMin', 'OutputMax',
        'LevelScale', 'bTiling', 'RepeatSize', 'WorldPositionOriginType', 'Layers', 'GrassTypes', 'SortPriority',
        'TransformSourceType', 'TransformType', 'bRequiresVertexData', 'PreviewWeight')


def is_input(v):
    return isinstance(v, dict) and 'expr' in v and 'out' in v


def short(x):
    if isinstance(x, str) and x.startswith('export:'):
        return x[7:].replace('MaterialExpression', '')
    if isinstance(x, str) and '/' in x:
        return x.rsplit('.', 1)[-1]
    return x


def flat_inputs(prefix, v, out):
    if is_input(v):
        if v['expr']:
            s = '%s<-%s:%d' % (prefix, short(v['expr']), v['out'])
            if v.get('mask'): s += '.' + v['mask']
            out.append(s)
        return
    if isinstance(v, dict):
        if 'items' in v and isinstance(v['items'], list):
            for i, it in enumerate(v['items']):
                flat_inputs('%s[%d]' % (prefix, i), it, out)
            return
        for k, x in v.items():
            flat_inputs('%s.%s' % (prefix, k) if prefix else k, x, out)
    elif isinstance(v, list):
        for i, it in enumerate(v):
            flat_inputs('%s[%d]' % (prefix, i), it, out)


def simplify(v):
    if isinstance(v, list) and v and isinstance(v[0], tuple):
        return {n: simplify(x) for n, t, e, x in v}
    if isinstance(v, dict):
        return {k: simplify(x) for k, x in v.items()}
    if isinstance(v, list):
        return [simplify(x) for x in v]
    return v


def dump(path, keep_comments=False):
    p = Pkg(path)
    lines = []
    for e in p.exports:
        c = p.cls(e)
        props = simplify(export_props(p, e))
        if c == 'Comment' or c == 'MaterialExpressionComment':
            if keep_comments: lines.append('# COMMENT %s' % props.get('Text'))
            continue
        if not (c.startswith('MaterialExpression') or c in ('Material', 'MaterialFunction', 'MaterialEditorOnlyData',
                                                              'MaterialFunctionEditorOnlyData')):
            continue
        kp = {k: short(props[k]) for k in KEYS if k in props and not is_input(props[k]) and k not in ('Layers', 'GrassTypes')}
        if 'Layers' in props:
            kp['Layers'] = [{kk: vv for kk, vv in it.items() if not is_input(vv)} for it in props['Layers'].get('items', [])]
        ins = []
        for k, v in props.items():
            flat_inputs(k, v, ins)
        if c in ('Material', 'MaterialFunction', 'MaterialEditorOnlyData', 'MaterialFunctionEditorOnlyData'):
            kp = {k: v for k, v in props.items() if not isinstance(v, (dict, list)) and k not in ('LightingGuid', 'StateId', 'ParameterGroupData')}
        lines.append('%s [%s] %s %s' % (e['name'].replace('MaterialExpression', ''), c.replace('MaterialExpression', ''),
                                        json.dumps(kp, default=str) if kp else '', ' '.join(ins)))
    return lines


if __name__ == '__main__':
    for l in dump(sys.argv[1], '--all' in sys.argv):
        print(l)
