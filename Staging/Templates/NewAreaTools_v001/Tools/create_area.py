"""In-editor. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); the El Wahat create_area.py with the
NorthOffset defect fixed (RC-71 / RC-72).
Create and named-save the new area's native packages; same method as Lebanon's create_native_area.py plus a named
copy of an existing area ground instance (area_constants.py GROUND_MI_SOURCE: shared parent master, snow line at 1e6):
  1. import the owned HDA (HDA_SOURCE.json) as profile['hda'], save it;
  2. duplicate GROUND_MI_SOURCE to <root>/Materials/MI_GeoCityGround_Auto, check MW_SnowWorldPosition = 1e6, save it;
  3. new level <root>/L_<AreaId> with the reusable sky at this latitude/longitude, SKY_DATE and SKY_TIMEZONE_H, and
     NorthOffset -90 set on THIS sky instance (GeoCity X = east, Y = south; playbook 4.5; no class-default change, RC-72),
     then the sun direction is checked at SKY_CHECK_HOURS against an INDEPENDENT solar model (NOAA formulas, taken from
     the El Wahat create_area_finish.py): the sky's own elevation property reads 180 + elevation after UpdateSky, so a
     check built on it inverts. Light vs NOAA sun direction < 1.5 deg, north arrow = -Y, first hour light along -X; save it.
No Cook, Bake or generation. Only exact named saves of these three packages; other areas' and shared packages are
hash-checked unchanged (area_constants.py PROTECTED_CONTENT_FILES + the ground MI source + the reusable sky).
Requires: this is the only Unreal editor, nothing dirty, targets absent.
ARGS: expected_pid, script_file (both from the client).
"""
import datetime, hashlib, importlib.util, json, math, os, subprocess, traceback
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
TOOLS = Path(ARGS['script_file']).resolve().parent                     # template v001: this task's Tools (ky_client.py passes it)
_spec = importlib.util.spec_from_file_location('area_constants', TOOLS / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (Tools/area_constants.py)
TASK = A.task_dir(TOOLS, ROOT)
# copy source: an area ground MI (parent = shared M_GeoCityAuto, MW_SnowWorldPosition 1e6), sha-pinned. Read only (duplicated).
GROUND_MI_SOURCE = A.GROUND_MI_SOURCE
GROUND_MI_SOURCE_SHA = A.GROUND_MI_SOURCE_SHA256
SKY = '/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky'
LAT, LON, TZ, DATE = A.LAT, A.LON, float(A.SKY_TIMEZONE_H), tuple(A.SKY_DATE)
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


def noaa(hour_local):
    """Approximate solar azimuth (deg from north, clockwise) and elevation (deg), NOAA general solar position formulas
    (independent of the sky blueprint; from the El Wahat create_area_finish.py)."""
    doy = datetime.date(*DATE).timetuple().tm_yday
    g = 2 * math.pi / 365 * (doy - 1 + (hour_local - TZ - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    dec = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
           - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    ha = math.radians((hour_local * 60 + eqt + 4 * LON - 60 * TZ) / 4 - 180)
    la = math.radians(LAT)
    el = math.asin(math.sin(la) * math.sin(dec) + math.cos(la) * math.cos(dec) * math.cos(ha))
    az = (math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(la) - math.tan(dec) * math.cos(la))) + 180) % 360
    return az, math.degrees(el)


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
    assert profile['map'].startswith(A.AREA_PREFIX), (profile['map'], A.AREA_PREFIX)
    for pkg, ext in ((profile['map'], '.umap'), (profile['hda'], '.uasset'), (MI, '.uasset')):
        assert not native_file(pkg, ext).exists() and not u.EditorAssetLibrary.does_asset_exist(pkg), 'Target exists: ' + pkg
    source = Path(hda_record['path'])
    assert source.parent.name == A.HDA_REVISION_DIR, 'HDA_SOURCE.json does not point at this area revision folder: %s' % source
    assert sha(source) == hda_record['sha256'], 'Owned 4 km HDA changed'
    assert sha(native_file(GROUND_MI_SOURCE)) == GROUND_MI_SOURCE_SHA, 'Ground MI copy source changed'
    # one shared protected list (area_constants.py PROTECTED_CONTENT_FILES) plus the ground MI copy source
    protected_paths = [ROOT / f for f in A.PROTECTED_CONTENT_FILES] + [native_file(GROUND_MI_SOURCE)]
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

    # 2. Area ground instance: named copy of the Karmei Yosef 2 km MI (same parent master and values).
    source_mi = u.load_asset(GROUND_MI_SOURCE)
    parent = source_mi.get_editor_property('parent')
    mi = u.EditorAssetLibrary.duplicate_asset(GROUND_MI_SOURCE, MI)
    assert mi and mi.get_outermost().get_name() == MI
    assert mi.get_editor_property('parent') == parent
    # Snow fix (playbook 4.4): MW_SnowWorldPosition must be 1e6 on the area MI (scalar read only; reading static
    # switches would mark the MI dirty). The copy source already carries 1e6; set it only if not.
    lib = u.MaterialEditingLibrary
    snow_copied = lib.get_material_instance_scalar_parameter_value(mi, 'MW_SnowWorldPosition')
    if abs(snow_copied - 1000000.0) > 1e-3:
        lib.set_material_instance_scalar_parameter_value(mi, 'MW_SnowWorldPosition', 1000000.0)  # return value unreliable
        lib.update_material_instance(mi)
    report['ground_mi_snow_world_position'] = {'copied': snow_copied,
                                               'saved': lib.get_material_instance_scalar_parameter_value(mi, 'MW_SnowWorldPosition')}
    assert abs(report['ground_mi_snow_world_position']['saved'] - 1000000.0) < 1e-3, report['ground_mi_snow_world_position']
    exclusive()
    assert u.EditorLoadingAndSavingUtils.save_packages([mi.get_outermost()], False)
    report['saves'].append(MI)
    report['ground_mi_parent'] = parent.get_path_name() if parent else None
    report['ground_mi_copied_from'] = GROUND_MI_SOURCE

    # 3. Area map with the reusable sky.
    level = u.get_editor_subsystem(u.LevelEditorSubsystem)
    assert level.new_level(profile['map'])
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    assert world.get_outermost().get_name() == profile['map']
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    sky = actors.spawn_actor_from_class(u.EditorAssetLibrary.load_blueprint_class(SKY), u.Vector(0, 0, 0))
    assert sky
    sky.set_actor_label('EnvironmentSky')
    # TimeZone = SKY_TIMEZONE_H without DST (the area's standard-time meridian), so TimeOfDay is close to solar time.
    # NorthOffset -90 on THIS instance: GeoCity levels use X = east, Y = south (north = -Y); the BP default 0 puts north on +X.
    for name, value in dict(Latitude=LAT, Longitude=LON, TimeZone=TZ, UseDaylightSavingTime=False, Year=DATE[0],
                            Month=DATE[1], Day=DATE[2], TimeOfDay=12.0, NorthOffset=-90.0, RigEnabled=True).items():
        sky.set_editor_property(name, value)
    sky.call_method('PresetPartlyCloudy')

    def sun_check(hour):  # NOAA check (create_area_finish.py): independent of the sky's own elevation property
        sky.call_method('SetSkyTime', (hour,))
        sky.call_method('UpdateSky')
        comps = {c.get_name(): c for c in sky.get_components_by_class(u.SceneComponent)}  # re-gathered: construction reruns
        f = comps['DirectionalLight'].get_forward_vector()
        n = comps['NorthArrow'].get_forward_vector()
        az, el = noaa(hour)
        a, e = math.radians(az), math.radians(el)
        want = (-math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), -math.sin(e))  # light travel, X east / Y south / Z up
        err = math.degrees(math.acos(max(-1.0, min(1.0, f.x * want[0] + f.y * want[1] + f.z * want[2]))))
        return {'hour': hour, 'noaa_azimuth': round(az, 3), 'noaa_elevation': round(el, 3),
                'sky_azimuth': round(sky.get_editor_property('Azimuth'), 3),
                'light_forward': [round(f.x, 4), round(f.y, 4), round(f.z, 4)], 'expected_forward': [round(v, 4) for v in want],
                'angle_error_deg': round(err, 3), 'north_arrow_forward': [round(n.x, 4), round(n.y, 4), round(n.z, 4)]}

    # SKY_CHECK_HOURS (area_constants.py): the first hour is after sunrise on this area's sky clock in this season.
    north = [sun_check(float(h)) for h in A.SKY_CHECK_HOURS]
    sky.call_method('SetSkyTime', (12.0,))
    sky.call_method('UpdateSky')
    report['sky'] = {'path': sky.get_path_name(), 'status': str(sky.get_editor_property('Status')),
                     'latitude': sky.get_editor_property('Latitude'), 'longitude': sky.get_editor_property('Longitude'),
                     'rig_enabled': sky.get_editor_property('RigEnabled'), 'north_offset': sky.get_editor_property('NorthOffset'),
                     'north_check_model': 'NOAA general solar position (independent of the sky blueprint)',
                     'north_check': north, 'outside_generated_ownership': True}
    assert sky.get_editor_property('RigEnabled')
    assert abs(sky.get_editor_property('NorthOffset') + 90.0) < 1e-3, report['sky']
    assert all(c['angle_error_deg'] < 1.5 and c['north_arrow_forward'][1] < -0.99 for c in north), north
    assert north[0]['light_forward'][0] < -0.8, north[0]  # first (morning) hour: light travels -X = sun in +X (east)
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
    u.log('NEWAREA_NATIVE_CREATION ' + A.AREA_ID + ' ' + report['status'])
RESULT = {'ok': report['status'] != 'FAILED', 'status': report['status'], 'files': report.get('files'),
          'saves': report['saves'], 'error': report.get('error', '')[-1500:]}
