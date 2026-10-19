"""Separate read-only verify of this area's owned generator (hython, after build_hda.py). Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69);
from the El Wahat v002 verify. Installs the base and the new HDA and checks: the base module equals the base module copy;
the new module equals base + exactly the shared edits of hda_edits.py and nothing else (diff counts); same section set,
nothing changed besides PythonModule/DialogScript; the assembly-contract and route-material parm defaults equal the
base's; the GRID_SAMPLES grid; TRACK_MI matches the module's route-path regex; an in-memory synthetic test of the two
drivable-precedence helpers as saved; the base unchanged. No cook. Updates hda_edits.RECORD."""
import datetime, difflib, hashlib, json, re, sys
from pathlib import Path
import hou
import numpy as np

TASK = Path(__file__).resolve().parent
sys.path.insert(0, str(TASK))
import hda_edits as E  # noqa: E402

GRID = E.A.GRID_SAMPLES
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
record = json.loads((TASK / E.RECORD).read_text(encoding='utf-8'))
assert sha(E.SRC) == E.SRC_SHA and sha(E.REF_MODULE) == E.REF_MODULE_SHA, 'base unchanged'
assert sha(E.DEST) == record['sha256'], 'new HDA changed since the build'
hou.setUpdateMode(hou.updateMode.Manual)
hou.hda.installFile(str(E.SRC)); hou.hda.installFile(str(E.DEST))
d1 = next(d for d in hou.hda.definitionsInFile(str(E.SRC)) if d.nodeTypeName() == E.SRC_TYPE)
d2 = next(d for d in hou.hda.definitionsInFile(str(E.DEST)) if d.nodeTypeName() == E.TYPE)
m1, m2 = d1.sections()['PythonModule'].contents(), d2.sections()['PythonModule'].contents()
assert m1 == E.REF_MODULE.read_text(encoding='utf-8'), 'base module differs from the base module copy'
assert m2 == E.apply(m1), 'new module is not exactly base + the shared edits'
assert m2 == (TASK / E.MODULE_COPY).read_text(encoding='utf-8'), 'module copy differs'
diff = [l for l in difflib.unified_diff(m1.splitlines(), m2.splitlines(), lineterm='', n=0)
        if l.startswith(('+', '-')) and not l.startswith(('+++', '---'))]
E.check_diff(diff)
for name in ('building_assembly_contract_json', 'route_surface_materials_json'):
    assert d1.parmTemplateGroup().find(name).defaultValue() == d2.parmTemplateGroup().find(name).defaultValue(), name
assert set(d1.sections()) == set(d2.sections()), (sorted(d1.sections()), sorted(d2.sections()))
others = [s for s in d1.sections() if s != 'PythonModule' and d1.sections()[s].contents() != d2.sections()[s].contents()]
assert set(others) <= {'DialogScript'}, others
assert re.fullmatch(E.ROUTE_PATH_RE, E.TRACK_MI), E.TRACK_MI
# synthetic test of the drivable-precedence helpers exactly as saved in the new module (they come with the base)
ns = {'np': np, 'ROAD_CLASSES': {'trunk', 'trunk_link', 'primary', 'primary_link', 'service', 'unclassified'}}
exec(m2[m2.index('EW_DRIVABLE_PRECEDENCE_TOLERANCE_M = 0.25'):m2.index('def cook_road_surfaces')], ns)
starts = np.array([[0.0, 0.0], [0.0, 0.0], [100.0, 0.0]]); ends = np.array([[100.0, 0.0], [0.0, -50.0], [200.0, 0.0]])
features = [('trunkA', 'trunk', 12.0), ('track1', 'track', 3.0), ('trunkB', 'trunk', 12.0)]
cor = ns['_ew_drivable_corridors']((starts, ends, features)); f = ns['_ew_drivable_containing']
synthetic = {'inside_5m': f((50, 5), cor), 'outside_7m': f((50, 7), cor), 'track_end': f((0.5, -2), cor),
             'down_track': f((0, -30), cor), 'tie': f((100, 1), cor)}
assert synthetic['inside_5m'][1] == 'trunkA' and synthetic['outside_7m'] is None and synthetic['track_end'][1] == 'trunkA'
assert synthetic['down_track'] is None and synthetic['tie'][1] == 'trunkA'
node = hou.node('/obj').createNode('geo', 'newarea_verify').createNode(E.TYPE, 'city', exact_type_name=True)
node.allowEditingOfContents(); node.allSubChildren(sync_delayed_definition=True)
grid = {n: node.node('terrain_grid_1009').parm(n).rawValue() for n in ('sizex', 'sizey', 'gridsamples', 'gridspacing')}
assert grid == {'sizex': str(GRID - 1), 'sizey': str(GRID - 1), 'gridsamples': str(GRID), 'gridspacing': '1'}, grid
assert sha(E.SRC) == E.SRC_SHA and sha(E.REF_MODULE) == E.REF_MODULE_SHA, 'base unchanged'
record.update(verified_by_separate_script=True, verify_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              module_diff_lines=diff, other_sections_changed_vs_base=others, parm_defaults_equal_base=True,
              synthetic_helper_test={k: (list(v) if v else None) for k, v in synthetic.items()},
              verify_heightfield_readback=grid, base_modified=sha(E.SRC) != E.SRC_SHA)
(TASK / E.RECORD).write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({k: record[k] for k in ('status', 'sha256', 'type', 'other_sections_changed_vs_base', 'base_modified',
                                         'synthetic_helper_test')}, indent=1))
print('diff lines -%d +%d' % (sum(l.startswith('-') for l in diff), sum(l.startswith('+') for l in diff)))
