"""In-editor (Karmei Yosef operator, session 4a6a1d0c), 2026-10-08. Create and named-save the new area's native
packages; same method as Lebanon's create_native_area.py plus a named copy of the Lebanon area ground instance:
  1. import the owned 4 km HDA (HDA_SOURCE.json) as <root>/HDA/GeoCity_city_v015_CurrentBank_4km_KY, save it;
  2. duplicate Lebanon's MI_GeoCityGround_Auto to <root>/Materials/MI_GeoCityGround_Auto, save it;
  3. new level <root>/L_KarmeiYosef_31850349_34907601_4km with the reusable sky at this latitude/longitude, save it.
No Cook, Bake or generation. Only exact named saves of these three packages; Lebanon/Shujaiya/shared packages are
hash-checked unchanged. Requires: this is the only Unreal editor, nothing dirty, targets absent.
ARGS: expected_pid (client).
"""
import datetime, hashlib, json, os, subprocess, traceback
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TASK = ROOT / 'Staging/NewArea_KarmeiYosef_31850349_34907601_4km_2026-10-08'
LEBANON_MI = '/Game/Project/Areas/KarmeiYosef_31850349_34907601_2km/BankIntegration_v015/Materials/MI_GeoCityGround_Auto'  # copy source: 2 km MI with the snow fix
SKY = '/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky'
LAT, LON = 31.850349, 34.907601
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()


def native_file(pkg, extension='.uasset'):
    return ROOT / ('Content/' + pkg.split('.')[0][6:] + extension)


def exclusive():
    rows = subprocess.check_output(['powershell', '-NoProfile', '-Command',
        "Get-CimInstance Win32_Process -Filter \"Name='UnrealEditor.exe' OR Name='UnrealEditor-Cmd.exe'\" | Select-Object -ExpandProperty ProcessId"],
        text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    assert [int(p) for p in rows.split()] == [os.getpid()], 'Another Unreal editor is live: ' + rows


def dirty():
    return (sorted(p.get_path_name() for p in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
            sorted(p.get_path_name() for p in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()))


pid = os.getpid()
assert pid == ARGS['expected_pid'], (pid, ARGS['expected_pid'])
assignment = json.loads((TASK / 'ASSIGNMENT_RUN.json').read_text(encoding='utf-8-sig'))
assert assignment.get('assigned_editor_PID') == pid and assignment.get('editor_live') is True and assignment.get('purpose') == 'create', assignment
profile = json.loads((TASK / 'PROFILE_CANDIDATE.json').read_text(encoding='utf-8'))
hda_record = json.loads((TASK / 'HDA_SOURCE.json').read_text(encoding='utf-8'))
MI = profile['landscape_material'].split('.')[0]
report = {'pid': pid, 'utc_start': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'saves': [],
          'cooked': False, 'generated': False, 'map': profile['map'], 'hda': profile['hda'], 'ground_mi': MI}
try:
    exclusive()
    assert dirty() == ([], []), 'Dirty packages before creation: %s' % (dirty(),)
    assert profile['map'].startswith('/Game/Project/Areas/KarmeiYosef_31850349_34907601_4km/')
    for pkg, ext in ((profile['map'], '.umap'), (profile['hda'], '.uasset'), (MI, '.uasset')):
        assert not native_file(pkg, ext).exists() and not u.EditorAssetLibrary.does_asset_exist(pkg), 'Target exists: ' + pkg
    source = Path(hda_record['path'])
    assert sha(source) == hda_record['sha256'], 'Owned 4 km HDA changed'
    protected_paths = [ROOT / 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration.umap',
                       ROOT / 'Content/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank.uasset',
                       ROOT / 'Content/Project/Shared/ModelBank/DT_EnvironmentBank_AnyArea.uasset',
                       ROOT / 'Content/Project/Areas/Lebanon_33390778_35506639_4km/BankIntegration_v015/L_Lebanon_33390778_35506639_4km.umap',
                       ROOT / 'Content/Project/Areas/Lebanon_33390778_35506639_4km/BankIntegration_v015/HDA/GeoCity_city_v015_CurrentBank_4km.uasset',
                       native_file(LEBANON_MI),
                       ROOT / 'Content/Project/Shared/SurfacePainting/Auto_20261006/M_GeoCityAuto.uasset']
    protected_paths += [native_file('/Game/Project/Shared/Atmosphere/ReusableSky/' + n) for n in
                        ('BP_EnvironmentSky', 'M_EnvironmentCelestial', 'MI_EnvironmentCloudDefaults')]
    protected = {str(p): sha(p) for p in protected_paths}

    # 1. Owned 4 km HDA asset.
    task = u.AssetImportTask()
    for key, value in dict(filename=str(source), destination_path=profile['hda'].rsplit('/', 1)[0],
                           destination_name=profile['hda'].rsplit('/', 1)[1], automated=True, replace_existing=False,
                           save=False, factory=u.HoudiniAssetFactory()).items():
        task.set_editor_property(key, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    objects = list(task.get_objects())
    assert len(objects) == 1, objects
    hda = objects[0]
    assert hda.get_outermost().get_name() == profile['hda']
    assert Path(hda.get_editor_property('asset_import_data').get_first_filename()).resolve() == source.resolve()
    exclusive()
    assert u.EditorLoadingAndSavingUtils.save_packages([hda.get_outermost()], False)
    report['saves'].append(profile['hda'])

    # 2. Area ground instance: named copy of Lebanon's (same parent master and values).
    lebanon_mi = u.load_asset(LEBANON_MI)
    parent = lebanon_mi.get_editor_property('parent')
    mi = u.EditorAssetLibrary.duplicate_asset(LEBANON_MI, MI)
    assert mi and mi.get_outermost().get_name() == MI
    assert mi.get_editor_property('parent') == parent
    exclusive()
    assert u.EditorLoadingAndSavingUtils.save_packages([mi.get_outermost()], False)
    report['saves'].append(MI)
    report['ground_mi_parent'] = parent.get_path_name() if parent else None
    report['ground_mi_copied_from'] = LEBANON_MI

    # 3. Area map with the reusable sky.
    level = u.get_editor_subsystem(u.LevelEditorSubsystem)
    assert level.new_level(profile['map'])
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    assert world.get_outermost().get_name() == profile['map']
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    sky = actors.spawn_actor_from_class(u.EditorAssetLibrary.load_blueprint_class(SKY), u.Vector(0, 0, 0))
    assert sky
    sky.set_actor_label('EnvironmentSky')
    for name, value in dict(Latitude=LAT, Longitude=LON, TimeZone=2.0, UseDaylightSavingTime=False, Year=2026,
                            Month=10, Day=8, TimeOfDay=12.0, RigEnabled=True).items():
        sky.set_editor_property(name, value)
    sky.call_method('PresetPartlyCloudy')
    sky.call_method('SetSkyTime', (12.0,))
    report['sky'] = {'path': sky.get_path_name(), 'status': str(sky.get_editor_property('Status')),
                     'latitude': sky.get_editor_property('Latitude'), 'longitude': sky.get_editor_property('Longitude'),
                     'rig_enabled': sky.get_editor_property('RigEnabled'), 'outside_generated_ownership': True}
    assert sky.get_editor_property('RigEnabled')
    assert not any(a.get_class().get_name() == 'HoudiniAssetActor' for a in actors.get_all_level_actors())
    assert dirty()[1] == [], 'Out-of-scope dirty content: %s' % (dirty()[1],)
    exclusive()
    assert u.EditorLoadingAndSavingUtils.save_map(world, profile['map'])
    report['saves'].append(profile['map'])
    assert dirty() == ([], []), 'Dirty after saves: %s' % (dirty(),)
    changed = [p for p, digest in protected.items() if sha(p) != digest]
    assert not changed, 'Protected packages changed: %s' % changed
    report['files'] = {'map_sha256': sha(native_file(profile['map'], '.umap')), 'hda_sha256': sha(native_file(profile['hda'])),
                       'ground_mi_sha256': sha(native_file(MI))}
    report['protected_unchanged'] = protected
    report['status'] = 'AREA_MAP_SKY_GROUND_AND_HDA_SAVED_GENERATION_PENDING'
except Exception:
    report['status'] = 'FAILED'
    report['error'] = traceback.format_exc()
finally:
    report['utc_end'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report['dirty_end'] = dirty()
    (TASK / 'NATIVE_AREA_CREATION.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    u.log('KARMEIYOSEF_NATIVE_CREATION ' + report['status'])
RESULT = {'ok': report['status'] != 'FAILED', 'status': report['status'], 'files': report.get('files'),
          'saves': report['saves'], 'error': report.get('error', '')[-1500:]}
