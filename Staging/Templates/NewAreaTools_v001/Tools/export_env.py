"""Offline. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the Karmei Yosef export_env.py (playbook 10b). Builds a
standalone UE 5.8 project holding this area's working map (the single root of receipts/DEPS_export_v2.json, under this
area's prefixes) and every package it depends on, then zips it.
  - file list: receipts/DEPS_export_v2.json (asset-registry closure, hard + soft references, from Tools/deps_probe.py with
    label export_v2) plus the landscape layer infos the in-editor check could not see (their full paths exceed 260
    characters): found by name in <area>/LayerInfos from the profile's HDA name and this area's landscape name;
  - same /Game paths as the source project, so nothing is renamed or re-referenced;
  - <name>.uproject with the plugins the map's classes need (SunPosition, PCG; Houdini Engine is NOT included: the generator
    actor is skipped on load, every visible result is baked), Config with the source renderer settings and the map as
    editor/game start map, README.txt, EXPORT_MANIFEST.json;
  - Windows long paths are off on this PC: the project root must stay <= 27 characters (longest relative path is 232).
Source files are only read. Usage:
  python export_env.py build <out_root> <ProjectName> <EngineAssociation>   (out_root must not exist; EngineAssociation =
                                                                             this PC's registered UE 5.8 id, '{...}')
  python export_env.py zip <out_root> <zip_path>
"""
import datetime, importlib.util, json, os, shutil, sys, uuid, zipfile
from pathlib import Path

SRC = Path(r'C:\Users\USER\Documents\Unreal Projects\Environmentpipeline')
TASK = Path(__file__).resolve().parents[1]                             # template v001: this task folder (G1)
assert TASK.parent == SRC / 'Staging', ('run from a task folder under <project>/Staging, never from the template', str(TASK))
_spec = importlib.util.spec_from_file_location('area_constants', TASK / 'Tools' / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (refuses if not filled in)
MAP = None                                                             # the single dependency root (set by file_list)
LAYERS = 'Content/Project/Areas/%s/BankIntegration_v015/%s/LayerInfos/' % (A.AREA_ID, A.AREA_ID)
LAYER_NAMES = ('Dirt_Path', 'Sand_01', 'Sand_02', 'Sand_Path')
LAYER_FILES = []                                                       # found by file_list
ENGINE_ASSOCIATION = None                                              # input (build argument)
LP = lambda p: '\\\\?\\' + os.path.abspath(str(p))                 # long-path-safe file access


def layer_files():
    """<HDA name>_<cook id>_<AREA_ID>_landscape_<layer>.uasset in LayerInfos, one per layer (names from the profile)."""
    hda = json.loads((SRC / A.PROFILE_REL).read_text(encoding='utf-8-sig'))['hda'].rsplit('/', 1)[1]
    names = os.listdir(LP(SRC / LAYERS))
    out = []
    for n in LAYER_NAMES:
        hits = [x for x in names if x.startswith(hda + '_') and x.endswith('_%s_landscape_%s.uasset' % (A.AREA_ID, n))]
        assert len(hits) == 1, ('layer info by name', n, hits)
        out.append(LAYERS + hits[0])
    return out


def file_list():
    global MAP
    d = json.loads((TASK / 'receipts' / 'DEPS_export_v2.json').read_text(encoding='utf-8'))
    assert len(d['roots']) == 1 and d['roots'][0].startswith((A.AREA_PREFIX, A.TRIAL_PREFIX)), d['roots']
    MAP = d['roots'][0]
    LAYER_FILES[:] = layer_files()
    rel = []
    for pkg, f, sz, extra in d['game']:
        rel += [f] + extra
    for f in LAYER_FILES:
        assert os.path.exists(LP(SRC / f)), f
        rel.append(f)
    return sorted(set(rel)), d


def build(out, name):
    out = Path(out)
    assert not out.exists(), 'output exists: %s' % out
    assert len(str(out)) + 1 <= 27, ('root too long for 260-character paths', len(str(out)) + 1)
    rel, d = file_list()
    total = 0
    for f in rel:
        dst = out / f
        os.makedirs(LP(dst.parent), exist_ok=True)
        shutil.copy2(LP(SRC / f), LP(dst))
        assert os.path.getsize(LP(dst)) == os.path.getsize(LP(SRC / f)), f
        total += os.path.getsize(LP(dst))
    up = {'FileVersion': 3, 'EngineAssociation': ENGINE_ASSOCIATION, 'Category': '',
          'Description': '%s environment (exported from Environmentpipeline, %s)' % (A.AREA_ID, datetime.date.today().isoformat()),
          'Plugins': [{'Name': 'SunPosition', 'Enabled': True}, {'Name': 'PCG', 'Enabled': True}]}
    (out / (name + '.uproject')).write_text(json.dumps(up, indent=1), encoding='utf-8')
    (out / 'Config').mkdir()
    obj = MAP + '.' + MAP.rsplit('/', 1)[1]
    (out / 'Config' / 'DefaultEngine.ini').write_text('\n'.join([
        '; copied from the source project: renderer/hardware/audio settings the materials and lighting rely on',
        '[Audio]', 'UseAudioMixer=True', '',
        '[/Script/HardwareTargeting.HardwareTargetingSettings]', 'TargetedHardwareClass=Desktop', 'AppliedTargetedHardwareClass=Desktop',
        'DefaultGraphicsPerformance=Maximum', 'AppliedDefaultGraphicsPerformance=Maximum', '',
        '[/Script/WindowsTargetPlatform.WindowsTargetSettings]', 'DefaultGraphicsRHI=DefaultGraphicsRHI_DX12',
        '!D3D12TargetedShaderFormats=ClearArray', '+D3D12TargetedShaderFormats=PCD3D_SM6', '',
        '[/Script/Engine.RendererSettings]', 'r.AllowStaticLighting=0', 'r.GenerateMeshDistanceFields=True',
        'r.DynamicGlobalIlluminationMethod=1', 'r.ReflectionMethod=1', 'r.Shadow.Virtual.Enable=1',
        'r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=True', 'r.DefaultFeature.LocalExposure.HighlightContrastScale=0.8',
        'r.DefaultFeature.LocalExposure.ShadowContrastScale=0.8', 'r.SkinCache.CompileShaders=True', 'r.RayTracing=True',
        'r.RayTracing.RayTracingProxies.ProjectEnabled=True', 'r.Substrate=True', 'r.Substrate.ProjectGBufferFormat=0', '',
        '[/Script/EngineSettings.GameMapsSettings]', 'EditorStartupMap=' + obj, 'GameDefaultMap=' + obj, '']), encoding='utf-8')
    (out / 'Config' / 'DefaultGame.ini').write_text('[/Script/EngineSettings.GeneralProjectSettings]\nProjectID=%s\nProjectName=%s\n'
                                                    % (uuid.uuid4().hex.upper(), name), encoding='utf-8')
    (out / 'README.txt').write_text(README.format(name=name, area=A.AREA_ID, map=MAP, n=len(rel), gb=round(total / 1e9, 2)), encoding='utf-8')
    man = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'map': MAP, 'files': len(rel), 'bytes': total,
           'source_project': str(SRC), 'source_map_file_sha256_at_dependency_scan': None,
           'missing_in_source_too': [m for m in d['missing_files'] if not any(m.endswith(x.rsplit('/', 1)[1][:-7]) for x in LAYER_FILES)],
           'list': rel}
    (out / 'EXPORT_MANIFEST.json').write_text(json.dumps(man, indent=1), encoding='utf-8')
    print(json.dumps({'out': str(out), 'files': len(rel), 'GB': round(total / 1e9, 2), 'uproject': name + '.uproject'}))


def make_zip(out, zpath):
    out, zpath = Path(out), Path(zpath)
    assert not zpath.exists(), zpath
    top = out.name
    n = 0
    with zipfile.ZipFile(LP(zpath), 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as z:
        for dp, dn, fn in os.walk(LP(out)):
            dn[:] = [x for x in dn if x not in ('Saved', 'Intermediate', 'DerivedDataCache')]
            for f in fn:
                full = os.path.join(dp, f)
                arc = top + '/' + os.path.relpath(full, LP(out)).replace(os.sep, '/')
                packed = f.endswith(('.uasset', '.umap', '.ubulk', '.uexp', '.uptnl'))
                z.write(full, arc, compress_type=zipfile.ZIP_STORED if packed else zipfile.ZIP_DEFLATED)
                n += 1
    with zipfile.ZipFile(LP(zpath)) as z:
        bad = z.testzip()
    print(json.dumps({'zip': str(zpath), 'entries': n, 'GB': round(os.path.getsize(LP(zpath)) / 1e9, 2), 'crc_check': bad or 'ok'}))


README = """{name} - {area} environment (Unreal Engine 5.8)
=========================================================================

Open: double-click {name}.uproject (Unreal Engine 5.8). The editor opens the map
  {map}
First open compiles shaders and builds mesh distance fields; that can take a while once.

IMPORTANT - unzip to a SHORT folder, for example C:\\  (giving C:\\{name}\\).
Some asset paths are 232 characters long; Windows refuses paths over 260 characters
unless long paths are enabled. If Windows reports "path too long", unzip with 7-Zip
to C:\\ or enable long paths.

Contents: the map and every asset it uses ({n} files, {gb} GB), same /Game paths as the
source project. Plugins enabled: Sun Position, PCG (both ship with UE 5.8).
Not included: Houdini Engine. The map holds the generator's Houdini actor; without the
plugin it is skipped on load (a warning) - everything you see is already baked.
Not included: the generator, GIS sources and pipeline tools (they live in the source
project's git repository).

Licences: the environment contains assets from store packs (Fab/Marketplace). They may be
shared inside your team or organisation, not published or given to outside parties.
"""

if __name__ == '__main__':
    if sys.argv[1] == 'build':
        ENGINE_ASSOCIATION = sys.argv[4]                                   # this PC's registered UE 5.8 id (input)
        assert ENGINE_ASSOCIATION.startswith('{') and ENGINE_ASSOCIATION.endswith('}'), ENGINE_ASSOCIATION
        build(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'zip':
        make_zip(sys.argv[2], sys.argv[3])
