"""Shared PythonModule edits for this area's owned generator (template v001, NewAreaTools_v001; maintained by the agent Aviv
assigns, GOVERNANCE_RECORD.md RC-69). Skeleton of the El Wahat edits-file pattern (playbook 3 and 10c): build_hda.py and
verify_hda.py import this file, so verify proves module = base + exactly these edits. Plain Python, no hou.
Base: the generator named by Tools/area_constants.py HDA_BASE_* (the closest owned HDA that completed a full non-Gaza cook).
It must already hold the El Wahat road edits (drivable precedence L, its bank-receipt ledger L2, the module default track
route T), so only the per-area edits remain:
  P  failed generated street poles omitted for this area too: AREA_ID appended to the final proxy policy tuple (2 places;
     found by pattern, the base's own area list is kept as it is);
  T  the module default 'track' route material points at THIS area's track MI (TRACK_MI of area_constants.py), which
     Tools/track_mi.py creates and the run checks (start_area_generation.py expected_track_mi).
Other edits the new area's [D] answers ask for (playbook 1.1 and 3) are added to EXTRA_EDITS by the operator, each with
its expected anchor count, and EXPECTED_DIFF is re-measured offline on the base module copy.
The tools that need the generator constants (track_mi.py, road_asphalt.py, start_area_generation.py, switch_profile_hda.py,
hda_revision_prepare.py) load this file by path, never through sys.path.
"""
import importlib.util
from pathlib import Path
import re

TASK = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('area_constants', TASK / 'Tools' / 'area_constants.py')
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)  # per-area constants (refuses if not filled in)
assert TASK.name == A.TASK_FOLDER, (TASK.name, A.TASK_FOLDER)

AREA = A.AREA_ID
HREV = Path(r'C:\Users\USER\Documents\Pipeline Environment\Houdini\GeoCity_city_v015_PermanentBank\revisions')
REV = HREV / A.HDA_REVISION_DIR
SRC = Path(A.HDA_BASE_SRC)
SRC_SHA = A.HDA_BASE_SHA256
SRC_TYPE = A.HDA_BASE_TYPE
REF_MODULE = Path(A.HDA_BASE_MODULE_COPY)
REF_MODULE_SHA = A.HDA_BASE_MODULE_SHA256
DEST = REV / (A.HDA_NAME + '.hdalc')
TYPE = A.HDA_TYPE
MENU = A.HDA_MENU
VERSION = A.HDA_VERSION
RECORD = A.HDA_RECORD                       # HDA_SOURCE.json for the first generator, HDA_SOURCE_<VERSION>.json after it
MODULE_COPY = A.HDA_MODULE_COPY
UNREAL_HDA = A.UNREAL_HDA
UNREAL_HDA_PREVIOUS = A.UNREAL_HDA_PREVIOUS  # None for the first generator of the area
TRACK_MI = A.TRACK_MI
TRACK_MI_PARENT = A.TRACK_MI_PARENT
ROAD_GENERATED_MATERIAL = '/Game/UtopianCity/Materials/MI_Asphalt.MI_Asphalt'
TOLERANCE_M = 0.25
STATUS = 'drivable_corridor_precedence'
DETAIL = 'road_drivable_precedence_json'
ROUTE_PATH_RE = r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+'
_POLES_RE = re.compile(r"not in \(('GazaRimal'(?:, '[A-Za-z0-9_]+')*)\)")
_TRACK_RE = re.compile(r"'track': \{'path': '(" + ROUTE_PATH_RE + r")',")
EXTRA_EDITS = []                            # (anchor, replacement, count, description) from this area's [D] answers
# expected diff of base -> this area's module: P changes 2 lines, T 1 line (re-measure if EDITS grows)
EXPECTED_DIFF = {'minus': 3, 'plus': 3}


def edits(text):
    """(anchor, replacement, expected occurrences in the base, change description), built from the base text."""
    poles = sorted(set(_POLES_RE.findall(text)))
    assert len(poles) == 1, ('the base must hold exactly one final proxy policy area tuple', poles)
    ids = re.findall(r"'([^']+)'", poles[0])
    assert AREA not in ids, ('the base already names this area in the pole tuple', AREA)
    tracks = _TRACK_RE.findall(text)
    assert len(tracks) == 1, ('the base must hold exactly one module default track route path', tracks)
    return [("not in (%s)" % poles[0], "not in (%s, '%s')" % (poles[0], AREA),
             2, 'P: failed generated street poles omitted for this area id too (final proxy policy tuple, 2 places)'),
            ("'track': {'path': '%s'," % tracks[0], "'track': {'path': '%s'," % TRACK_MI,
             1, 'T: module default track route material = this area TRACK_MI')] + list(EXTRA_EDITS)


def check_base(text):
    assert 'GRID_SAMPLES = %d' % A.GRID_SAMPLES in text, 'base grid differs from this area size'
    assert text.count('def cook_road_surfaces') == 1 and text.count('_ew_drivable_corridors') >= 1, \
        'base must already hold the drivable-precedence road edits (L/L2)'
    assert text.count(DETAIL) == 3 and text.count(STATUS) == 1, 'base must already hold the L/L2 ledger'
    assert re.fullmatch(ROUTE_PATH_RE, TRACK_MI), TRACK_MI
    for old, _new, count, _why in edits(text):
        assert text.count(old) == count, ('anchor count', old[:70], text.count(old), count)


def apply(text):
    check_base(text)
    for old, new, count, _why in edits(text):
        text = text.replace(old, new)
    assert text.count(TRACK_MI) == 1 and text.count(DETAIL) == 3 and text.count(STATUS) == 1
    assert text.count("'%s')" % AREA) == 2
    return text


def check_diff(diff):
    minus = [l for l in diff if l.startswith('-')]
    plus = [l for l in diff if l.startswith('+')]
    assert len(minus) == EXPECTED_DIFF['minus'] and len(plus) == EXPECTED_DIFF['plus'], (len(minus), len(plus), EXPECTED_DIFF)
