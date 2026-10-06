"""Offline read-only inventory of MWLandscapeAutoMaterial + HighPoly_Tree_Model (no unreal import).
Writes PACK_INVENTORY.json next to this script. Run: python inventory_packs.py
"""
import os, sys, json, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uasset_offline import Pkg, R, read_props, export_props

PROJ = r'C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Content'
ROOTS = ['MWLandscapeAutoMaterial', 'HighPoly_Tree_Model']
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'PACK_INVENTORY.json')


def simplify(v):
    if isinstance(v, list) and v and isinstance(v[0], tuple):
        return {n: simplify(x) for n, t, e, x in v}
    if isinstance(v, dict):
        return {k: simplify(x) for k, x in v.items()}
    if isinstance(v, list):
        return [simplify(x) for x in v]
    return v


def import_data(p, ex):
    r = R(p.b, ex['offset'])
    try:
        js = r.fstr()
        return [m.group(1) for m in re.finditer(r'"RelativeFilename" : "([^"]*)"', js)]
    except Exception:
        return None


def game_path(fp):
    rel = os.path.relpath(fp, PROJ).replace('\\', '/')
    return '/Game/' + rel.rsplit('.', 1)[0]


def strings_desc(p, ex):
    pass


def handle(fp):
    p = Pkg(fp)
    rec = dict(path=game_path(fp), bytes=os.path.getsize(fp), saved_by='%d.%d.%d' % p.saved_by[:3])
    rec['deps'] = sorted(i['name'] for i in p.imports if i['class_name'] == 'Package' and i['name'].startswith('/Game'))
    main = [e for e in p.exports if e['is_asset']] or p.exports[-1:]
    rec['class'] = p.cls(main[0]) if main else None
    exprs = collections.Counter(); params = []; tex = set(); funcs = set(); details = []
    for e in p.exports:
        c = p.cls(e)
        if c == 'AssetImportData':
            src = import_data(p, e)
            if src: rec['source_file'] = src
            continue
        if c == 'MetaData':
            continue
        try:
            props = simplify(export_props(p, e))
            if not isinstance(props, dict): props = {}
        except Exception as ex:
            props = {'ERR': str(ex)}
        if e['is_asset'] or e is main[0]:
            keep = {}
            for k, v in props.items():
                if k in ('Source', 'ImportedSize', 'SRGB', 'CompressionSettings', 'LODGroup', 'Parent', 'ScalarParameterValues',
                         'VectorParameterValues', 'TextureParameterValues', 'StaticParameters', 'StaticParametersRuntime',
                         'BlendMode', 'ShadingModel', 'TwoSided', 'MaterialDomain', 'Description', 'bUsedWithInstancedStaticMeshes',
                         'GrassVarieties', 'PhysMaterial', 'CachedExpressionData', 'AdjustBrightness', 'AdjustBrightnessCurve',
                         'AdjustSaturation', 'AdjustVibrance', 'AdjustRGBCurve', 'AdjustHue', 'AdjustMinAlpha', 'AdjustMaxAlpha',
                         'CompressionNoAlpha', 'MipGenSettings', 'Filter', 'AddressX', 'AddressY', 'MaxTextureSize',
                         'bFlipGreenChannel', 'StaticMaterials', 'LODGroup', 'NaniteSettings', 'SourceModels', 'bExposeToLibrary',
                         'LibraryCategoriesText', 'UserDescription', 'PhysicalMaterial', 'bUsedWithStaticLighting',
                         'BasePropertyOverrides', 'LayerInfoObjects', 'LayerName', 'Hardness', 'bNoWeightBlend', 'LayerUsageDebugColor',
                         'ExtendedBounds', 'NumSourceModels', 'bHasNavigationData', 'LightMapResolution', 'BodySetup', 'Materials',
                         'bUseFullPrecisionUVs', 'LightmapUVDensity', 'PositiveBoundsExtension', 'NegativeBoundsExtension'):
                    keep[k] = v
            rec['asset_props'] = keep
        if c.startswith('MaterialExpression'):
            exprs[c] += 1
            d = {k: props.get(k) for k in ('ParameterName', 'DefaultValue', 'Group', 'Desc', 'Texture', 'SamplerSource', 'SamplerType',
                                           'MaterialFunction', 'Layers', 'GrassTypes', 'InputName', 'Description', 'SortPriority',
                                           'Function', 'Constant', 'R', 'G', 'B', 'A', 'SliderMin', 'SliderMax', 'ConstA', 'ConstB',
                                           'ConstAlpha', 'Text', 'Values', 'Collection', 'ParameterId', 'MinRange', 'MaxRange', 'OutputName',
                                           'MatchedLayerName', 'CommentColor', 'PreviewValue', 'Value', 'bUseCustomPrimitiveData',
                                           'LayerName', 'PreviewWeight', 'VirtualTexture', 'MaterialType', 'ConstantA', 'ConstantB',
                                           'ExponentIn', 'BaseReflectFractionIn', 'Period', 'SizeX', 'SizeY', 'Coordinate',
                                           'UTiling', 'VTiling', 'InputType', 'bUseWorldspace', 'Mapping', 'MappingType',
                                           'MappingScale', 'MappingRotation', 'MappingPanSpeed', 'MappingCustomUV0Index',
                                           'FadeDistance', 'FadeDistanceDefault', 'BlendSharpness', 'BlendBias', 'Name',
                                           'Expression', 'ChannelNames', 'bUseWorldPos') if props.get(k) is not None}
            d['_class'] = c; d['_name'] = e['name']
            if 'Texture' in d and d['Texture']: tex.add(d['Texture'])
            if 'MaterialFunction' in d and d['MaterialFunction']: funcs.add(d['MaterialFunction'])
            details.append(d)
    if exprs:
        rec['expression_counts'] = dict(exprs.most_common())
        rec['expressions'] = details
        rec['textures_referenced'] = sorted(tex)
        rec['functions_referenced'] = sorted(funcs)
    return rec


def main():
    out = {}
    for root in ROOTS:
        for dp, dn, fn in os.walk(os.path.join(PROJ, root)):
            for f in sorted(fn):
                fp = os.path.join(dp, f)
                if f.endswith('.uasset'):
                    try:
                        out[game_path(fp)] = handle(fp)
                    except Exception as ex:
                        out[game_path(fp)] = {'ERR': repr(ex), 'bytes': os.path.getsize(fp)}
                else:
                    out[game_path(fp) + '|' + f] = {'bytes': os.path.getsize(fp), 'note': 'non-uasset (map or other); header not parsed'}
    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1, default=str)
    print('wrote', OUT, len(out))


if __name__ == '__main__':
    main()
