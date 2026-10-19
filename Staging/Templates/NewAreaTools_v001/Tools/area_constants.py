"""Per-area constants of the NewAreaTools template (template v001, created 2026-10-19 per Docs/GOVERNANCE_RECORD.md item 16,
RC-71; maintained by the agent Aviv assigns, RC-69).

This is the ONLY file of the template that names an area: its id, centre, size, short prefix, task folder, sky date, editor
ports, generator base and the protected packages. Every other tool loads it (in the editor through ARGS['script_file'],
which ky_client.py passes; offline through its own path) and builds every path and size from it.

How to use (playbook NEW_ENVIRONMENT_PLAYBOOK.md sections 1.2-1.3 and 11):
  1. copy the whole template folder to Staging/NewArea_<Name>_<lat8>_<lon8>_<size>_<YYYY-MM-DD>/;
  2. set EVERY value in the block "SET PER AREA" below (each one says what it is; UNSET / None are refused);
  3. run nothing from Staging/Templates/: load() refuses a folder whose name is not TASK_FOLDER.
Playbook constant names -> here: TASK -> TASK_FOLDER (task_dir()); AREA / area id -> AREA_ID; MAIN / MAP -> MAIN_MAP;
TRIAL -> TRIAL_ROOT; CLONE -> clone_map(suffix); landscape half-extent -> HALF_EXTENT_CM; $AreaPrefix -> AREA_PREFIX /
TRIAL_PREFIX; the three editor ports -> COPILOT_PORT, PLUGIN_PORT, NATIVE_PORT (choose three that no other task uses).
The launcher reads the values with: python -I -B Tools/area_constants.py --json
EXAMPLE lines (marked "example, El Wahat task") show the values of an earlier area for orientation only; never reuse them.
"""
import json
import re
import sys
from pathlib import Path

UNSET = '<SET_PER_AREA>'

# ============================== SET PER AREA (every value below) ==========================================================
AREA_NAME = UNSET          # <Name> of the task folder, letters only (example, El Wahat task: 'ElWahatEgypt')
LAT = None                 # area centre latitude, 6 decimals (example, El Wahat task: 29.176036)
LON = None                 # area centre longitude, 6 decimals (example, El Wahat task: 29.602273)
SIZE_KM = None             # 4 (4033 samples at 1 m) or 2 (2017 samples), playbook 1.1
AREA_ID = UNSET            # '<Name>_<lat8>_<lon8>_<size>km' (example, El Wahat task: 'ElWahatEgypt_29176036_29602273_4km')
TASK_DATE = UNSET          # 'YYYY-MM-DD' of the task folder name
AREA_SHORT = UNSET         # short prefix of area-owned asset names: T_<AREA_SHORT>_Satellite, M_GeoCityAuto_<AREA_SHORT>,
                           # PCG_<AREA_SHORT>_Zones, M_RoadAsphalt_<AREA_SHORT>_v001 (example, El Wahat task: 'EW4')
SKY_DATE = None            # (year, month, day) set on the sky in create_area.py, normally the task date
SKY_TIMEZONE_H = None      # standard-time UTC offset of the area in hours, no daylight saving (example, El Wahat task: 2.0)
SKY_CHECK_HOURS = None     # three sky-clock hours for the NOAA sun check, the first one after sunrise at this longitude and
                           # season, e.g. (7.0, 12.0, 17.0); the first must give a morning sun in the east (light along -X)
COPILOT_PORT = None        # UnrealCopilot MCP port of this task's editors (launcher, ky_client.py)
PLUGIN_PORT = None         # UnrealCopilot internal plugin port (launcher)
NATIVE_PORT = None         # native ModelContextProtocol port (launcher, ky_capture.py)

# Area ground MI copy source for create_area.py: an existing area-owned MI_GeoCityGround_Auto whose snow line is already at
# 1e6, read only and sha-pinned (example, El Wahat task: the Karmei Yosef 2 km MI, sha 016e75a4...).
GROUND_MI_SOURCE = UNSET   # /Game/... package path (no object suffix)
GROUND_MI_SOURCE_SHA256 = UNSET

# Profile template for prepare_profile.py / promote_profile.py: the AREA_PROFILE.json of the last area that completed a
# full non-Gaza cook (Staging/ModelBank/<PROFILE_TEMPLATE_AREA_ID>/AREA_PROFILE.json), and the bank facts it must carry.
PROFILE_TEMPLATE_AREA_ID = UNSET
PROFILE_TEMPLATE_ROW_COUNT = None        # its 'row_count'
PROFILE_TEMPLATE_CATALOG_SHA256 = UNSET  # its 'catalog_sha256' (= release.catalog_sha256)
PROFILE_TEMPLATE_RELEASE_ID = UNSET      # its release.id
PROFILE_TEMPLATE_REGISTRY_SHA256 = UNSET # sha256 of its building_assembly_contract.source_family_registry_ref file

# Owned generator (build_hda.py / verify_hda.py / hda_edits.py): the base is the closest owned HDA that completed a full
# non-Gaza cook and already holds the drivable-precedence road edits (playbook 3 and 10c).
HDA_BASE_SRC = UNSET            # absolute path of the base .hdalc
HDA_BASE_SHA256 = UNSET
HDA_BASE_TYPE = UNSET           # its operator type name, e.g. 'trackb::geocity_city::15.0_4km_<name>_v002'
HDA_BASE_MODULE_COPY = UNSET    # absolute path of the exact text copy of the base PythonModule (written by the base's build)
HDA_BASE_MODULE_SHA256 = UNSET
HDA_REVISION_DIR = UNSET        # new folder under .../GeoCity_city_v015_PermanentBank/revisions/, '<YYYYMMDD>_<Name>_<size>'
HDA_VERSION = 'v001'            # this area's generator revision; a later revision (instantiate switch) raises it
HDA_PREVIOUS_VERSION = None     # None for the first generator of the area; else the version the profile names now ('v001')

# Ground zones (Zones/): Sentinel-2 windows (dates, ISO) and classification thresholds. REVIEW per area and hemisphere.
S2_RECENT_START = UNSET         # start of the 'recent' search window, e.g. three months before the task date
S2_SPRING_WINDOW = None         # ('YYYY-MM-DDT00:00:00Z', 'YYYY-MM-DDT23:59:59Z') of the green season
SAT_STRETCH = None              # satellite texture stretch (make_textures.py); 2500 clipped desert sand to white, 5000 did not
ZONE_RULES = None               # classify_zones.py thresholds, e.g. {'bright_reflectance': 2600, 'bright_ndvi_max': 0.25,
                                # 'green_crop_ndvi': 0.45, 'trees_ndvi_low': 0.25, 'trees_ndvi_high': 0.45,
                                # 'trees_spring_ndvi': 0.45, 'bare_ndvi': 0.22}
TREE_RULES = None               # Zones/trees_v2.py thresholds, e.g. {'forest_min': 0.28, 'forest_span': 0.22, 'forest_floor': 0.4,
                                # 'scrub_min': 0.26, 'scrub_span': 0.24, 'scrub_floor': 0.12, 'sat_now': 0.36, 'sat_spring': 0.42,
                                # 'sat_delta': 0.05, 'sat_min': 0.34, 'sat_span': 0.14}

# Packages create_area.py hash-checks before and after (other areas' maps, the shared bank and generator, the ground MI copy
# source and the reusable sky). Other areas' ids may appear here and only here. Project-relative file paths under Content/.
PROTECTED_CONTENT_FILES = None  # list of 'Content/...uasset|.umap' strings; GROUND_MI_SOURCE and the sky are added by the tools
# ============================== end of SET PER AREA ======================================================================

# ---- derived (do not edit) -----------------------------------------------------------------------------------------------
GRID_SAMPLES = 1008 * SIZE_KM + 1 if isinstance(SIZE_KM, int) else None        # 4033 for 4 km, 2017 for 2 km
HALF_EXTENT_M = 504.0 * SIZE_KM if isinstance(SIZE_KM, int) else None          # landscape half-extent (m)
HALF_EXTENT_CM = HALF_EXTENT_M * 100.0 if HALF_EXTENT_M else None              # landscape half-extent (cm)
REQUEST_HALF_M = 500.0 * SIZE_KM if isinstance(SIZE_KM, int) else None          # requested source area half-size (m)
ZONE_PX = (GRID_SAMPLES - 1) // 4 + 1 if GRID_SAMPLES else None                 # 4 m zone grid over the landscape
TASK_FOLDER = 'NewArea_%s_%s' % (AREA_ID, TASK_DATE)
AREA_PREFIX = '/Game/Project/Areas/%s/' % AREA_ID
TRIAL_PREFIX = '/Game/Project/Areas/%s_PCGTrial/' % AREA_ID
AREA_ROOT = AREA_PREFIX + 'BankIntegration_v015'
MAIN_MAP = '%s/L_%s' % (AREA_ROOT, AREA_ID)
AREA_MATERIALS = AREA_ROOT + '/Materials'
COOK_PREFIX = AREA_ROOT + '/Cook/'
ROAD_MESH = '%s/Bake/%s_road_surfaces' % (AREA_ROOT, AREA_ID)
BUILDINGS_MESH = '%s/Bake/%s_buildings' % (AREA_ROOT, AREA_ID)
GROUND_MI = AREA_MATERIALS + '/MI_GeoCityGround_Auto'
GROUND_MASTER_COPY = '%s/M_GeoCityAuto_%s' % (AREA_MATERIALS, AREA_SHORT)
SAT_TEXTURE = 'T_%s_Satellite' % AREA_SHORT
ZONES_TEXTURE = 'T_%s_Zones' % AREA_SHORT
MASK_PREFIX = 'T_%s_Mask_' % AREA_SHORT
ROAD_MASTER = '%s/M_RoadAsphalt_%s_v001' % (AREA_MATERIALS, AREA_SHORT)
ROAD_MI = '%s/MI_RoadAsphalt_%s_v001' % (AREA_MATERIALS, AREA_SHORT)
TRACK_MI_NAME = 'MI_RoadTrack_%s_v001' % AREA_SHORT
TRACK_MI = '%s/%s.%s' % (AREA_MATERIALS, TRACK_MI_NAME, TRACK_MI_NAME)   # module default track route material (hda_edits)
TRACK_MI_PARENT = ROAD_MASTER
TRIAL_ROOT = TRIAL_PREFIX.rstrip('/')
PCG_VOLUME_LABEL = '%s_PCG_Zones' % AREA_SHORT
WINDBREAKS_LABEL = '%s_Windbreaks' % AREA_SHORT
PROFILE_REL = 'Staging/ModelBank/%s/AREA_PROFILE.json' % AREA_ID
SOURCE_DATA = 'C:/Users/USER/Documents/Pipeline Environment/SourceData'
HDA_NAME = 'GeoCity_city_v015_CurrentBank_%skm_%s_%s' % (SIZE_KM, AREA_SHORT, HDA_VERSION)
HDA_TYPE = 'trackb::geocity_city::15.0_%skm_%s_%s' % (SIZE_KM, str(AREA_NAME).lower(), HDA_VERSION)
HDA_MENU = 'GeoCity current bank - %s km (%s %s)' % (SIZE_KM, AREA_NAME, HDA_VERSION)
HDA_MODULE_COPY = 'geocity_city_module_%skm_%s_%s.py' % (SIZE_KM, str(AREA_SHORT).lower(), HDA_VERSION)
UNREAL_HDA = '%s/HDA/%s' % (AREA_ROOT, HDA_NAME)
UNREAL_HDA_PREVIOUS = ('%s/HDA/GeoCity_city_v015_CurrentBank_%skm_%s_%s' % (AREA_ROOT, SIZE_KM, AREA_SHORT, HDA_PREVIOUS_VERSION)
                       if HDA_PREVIOUS_VERSION else None)
HDA_RECORD = 'HDA_SOURCE.json' if not HDA_PREVIOUS_VERSION else 'HDA_SOURCE_%s.json' % HDA_VERSION.upper()


def clone_map(suffix):
    """PCG clone map. suffix is REQUIRED and explicit: '' = first clone L_<AreaId>_PCGTrial (playbook 1.2), '_v2' = the clone
    rebuilt after a regeneration (clone_v2.py). No tool may default it."""
    assert isinstance(suffix, str) and re.fullmatch(r'(_v[0-9]+)?', suffix), ('clone suffix must be "" or "_v<N>"', suffix)
    return '%s/L_%s_PCGTrial%s' % (TRIAL_ROOT, AREA_ID, suffix)


def zones_graph(version):
    """Zone PCG graph: version '' = the graph build_zone_pcg.py makes (PCG_<AREA_SHORT>_Zones), 'v002' and later = the
    rebuilt graphs of trees_pcg.py (PCG_<AREA_SHORT>_Zones_v002). version is REQUIRED (an old version is an unused graph)."""
    assert isinstance(version, str) and re.fullmatch(r'(v[0-9]{3})?', version), ('graph version must be "" or "v<NNN>"', version)
    return '%s/PCG/PCG_%s_Zones%s' % (TRIAL_ROOT, AREA_SHORT, ('_' + version) if version else '')


def missing():
    """Names of SET PER AREA values that are still unset or inconsistent."""
    out = [k for k in ('AREA_NAME', 'AREA_ID', 'TASK_DATE', 'AREA_SHORT', 'GROUND_MI_SOURCE', 'GROUND_MI_SOURCE_SHA256',
                       'PROFILE_TEMPLATE_AREA_ID', 'PROFILE_TEMPLATE_CATALOG_SHA256', 'PROFILE_TEMPLATE_RELEASE_ID',
                       'PROFILE_TEMPLATE_REGISTRY_SHA256', 'HDA_BASE_SRC', 'HDA_BASE_SHA256', 'HDA_BASE_TYPE',
                       'HDA_BASE_MODULE_COPY', 'HDA_BASE_MODULE_SHA256', 'HDA_REVISION_DIR', 'S2_RECENT_START')
           if globals()[k] in (UNSET, None, '')]
    out += [k for k in ('LAT', 'LON', 'SKY_TIMEZONE_H') if not isinstance(globals()[k], (int, float))]
    out += [k for k in ('SIZE_KM', 'COPILOT_PORT', 'PLUGIN_PORT', 'NATIVE_PORT', 'PROFILE_TEMPLATE_ROW_COUNT')
            if not isinstance(globals()[k], int)]
    out += [k for k in ('SKY_DATE', 'SKY_CHECK_HOURS', 'S2_SPRING_WINDOW') if not (isinstance(globals()[k], tuple) and globals()[k])]
    out += [k for k in ('SAT_STRETCH',) if not isinstance(globals()[k], (int, float))]
    out += [k for k in ('ZONE_RULES', 'TREE_RULES') if not isinstance(globals()[k], dict)]
    out += [k for k in ('PROTECTED_CONTENT_FILES',) if not isinstance(globals()[k], list)]
    if not out:
        if SIZE_KM not in (2, 4):
            out.append('SIZE_KM (2 or 4)')
        if AREA_ID != '%s_%08d_%08d_%dkm' % (AREA_NAME, round(LAT * 1e6), round(LON * 1e6), SIZE_KM):
            out.append('AREA_ID (must be <AREA_NAME>_<lat8>_<lon8>_<SIZE_KM>km)')
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9]*', AREA_NAME) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9]*', AREA_SHORT):
            out.append('AREA_NAME / AREA_SHORT (letters and digits only)')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', TASK_DATE):
            out.append('TASK_DATE (YYYY-MM-DD)')
        if len({COPILOT_PORT, PLUGIN_PORT, NATIVE_PORT}) != 3:
            out.append('ports (three different ports)')
        if HDA_PREVIOUS_VERSION is not None and HDA_PREVIOUS_VERSION == HDA_VERSION:
            out.append('HDA_PREVIOUS_VERSION (must differ from HDA_VERSION)')
    return out


def check_location(path=None):
    """Refuse unless this file sits in <project>/Staging/<TASK_FOLDER>/Tools/ (the template is never run in place)."""
    here = Path(path or __file__).resolve()
    tools = here.parent
    assert tools.name == 'Tools' and tools.parent.name == TASK_FOLDER and tools.parent.parent.name == 'Staging', (
        'area_constants.py must sit in Staging/%s/Tools/ (copy the template to a task folder first; it never runs in place)'
        % TASK_FOLDER, str(here))
    return tools.parent


def task_dir(tools, root=None):
    """The task folder of a Tools folder, checked against TASK_FOLDER and (in the editor) the project root."""
    tools = Path(tools).resolve()
    task = check_location(tools / 'area_constants.py')
    if root is not None:
        assert task.parent == Path(root).resolve() / 'Staging', ('task folder is not under <project>/Staging', str(task))
    return task


def load_check():
    problems = missing()
    if problems:
        raise RuntimeError('area_constants.py is not filled in for this area: ' + ', '.join(problems))
    check_location()


load_check()

if __name__ == '__main__':
    if sys.argv[1:] != ['--json']:
        raise SystemExit('usage: python -I -B area_constants.py --json')
    names = [k for k in sorted(globals()) if k.isupper()]
    print(json.dumps({k: globals()[k] for k in names}, default=str))
