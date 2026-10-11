"""Offline (Karmei Yosef operator, 2026-10-12; Aviv: "Yes, build the zip for me"). Builds a standalone UE 5.8 project holding
the Karmei Yosef 4 km working map (L_..._PCGTrial_v2) and every package it depends on, then zips it.
  - file list: receipts/DEPS_export_v2.json (asset-registry closure, hard + soft references, from Tools/deps_probe.py) plus
    the v002 landscape layer infos the in-editor check could not see (their full paths exceed 260 characters);
  - same /Game paths as the source project, so nothing is renamed or re-referenced;
  - <name>.uproject with the plugins the map's classes need (SunPosition, PCG; Houdini Engine is NOT included: the generator
    actor is skipped on load, every visible result is baked), Config with the source renderer settings and the map as
    editor/game start map, README.txt, EXPORT_MANIFEST.json;
  - Windows long paths are off on this PC: the project root must stay <= 27 characters (longest relative path is 232).
Source files are only read. Usage:
  python export_env.py build <out_root> <ProjectName>        (out_root must not exist)
  python export_env.py zip <out_root> <zip_path>
"""
import datetime, json, os, shutil, sys, uuid, zipfile
from pathlib import Path

SRC = Path(r'C:\Users\USER\Documents\Unreal Projects\Environmentpipeline')
TASK = SRC / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
MAP = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km_PCGTrial/L_KarmeiYosef_31850349_34907601_4km_PCGTrial_v2'
LAYERS = 'Content/Project/Areas/KarmeiYosef_31850349_34907601_4km/BankIntegration_v015/KarmeiYosef_31850349_34907601_4km/LayerInfos/'
LAYER_FILES = [LAYERS + 'GeoCity_city_v015_CurrentBank_4km_KY_v002_3_373_0_KarmeiYosef_31850349_34907601_4km_landscape_%s.uasset' % n
               for n in ('Dirt_Path', 'Sand_01', 'Sand_02', 'Sand_Path')]
ENGINE_ASSOCIATION = '{F2B44468-4491-1E02-F0D0-7087DF70CD1C}'      # this PC's registered UE 5.8 (C:/Program Files/Epic Games/UE_5.8)
LP = lambda p: '\\\\?\\' + os.path.abspath(str(p))                 # long-path-safe file access


def file_list():
    d = json.loads((TASK / 'receipts' / 'DEPS_export_v2.json').read_text(encoding='utf-8'))
    assert d['roots'] == [MAP], d['roots']
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
          'Description': 'Karmei Yosef 4 km + Paz Farm environment (exported from Environmentpipeline, %s)' % datetime.date.today().isoformat(),
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
    (out / 'README.txt').write_text(README.format(name=name, map=MAP, n=len(rel), gb=round(total / 1e9, 2)), encoding='utf-8')
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


README = """{name} - Karmei Yosef 4 km + Paz Farm environment (Unreal Engine 5.8)
=========================================================================

Open: double-click {name}.uproject (Unreal Engine 5.8). The editor opens the map
  {map}
First open compiles shaders and builds mesh distance fields; that can take a while once.

IMPORTANT - unzip to a SHORT folder, for example C:\\  (giving C:\\KYPaz\\).
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
        build(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'zip':
        make_zip(sys.argv[2], sys.argv[3])
