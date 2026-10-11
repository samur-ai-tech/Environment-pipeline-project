"""Completes build_hda_4km_v002.py's checks (its last check read v001's parameter template without installing v001; the
v002 file had already been saved and its grid verified). Read-only on both HDAs: installs both, compares the v002 module
with the intended edit of the v001 copy, the assembly-contract default and the grid, then writes the module copy and
HDA_SOURCE_V002.json. Run with hython."""
import datetime, hashlib, json
from pathlib import Path
import hou
TASK = Path(__file__).resolve().parent
REV = Path(r"C:\Users\USER\Documents\Pipeline Environment\Houdini\GeoCity_city_v015_PermanentBank\revisions\20261008_KarmeiYosef_4km")
SRC, DEST = REV / "GeoCity_city_v015_CurrentBank_4km_KY_v001.hdalc", REV / "GeoCity_city_v015_CurrentBank_4km_KY_v002.hdalc"
SRC_SHA = "1789ea386217e5b958b82e8369134a0fd04e5a00adcc5246eacfdd8bae9e4797"
T1, T2 = "trackb::geocity_city::15.0_4km_karmeiyosef", "trackb::geocity_city::15.0_4km_karmeiyosef_v002"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(SRC) == SRC_SHA
hou.setUpdateMode(hou.updateMode.Manual)
hou.hda.installFile(str(SRC)); hou.hda.installFile(str(DEST))
d1 = next(d for d in hou.hda.definitionsInFile(str(SRC)) if d.nodeTypeName() == T1)
d2 = next(d for d in hou.hda.definitionsInFile(str(DEST)) if d.nodeTypeName() == T2)
m1, m2 = d1.sections()['PythonModule'].contents(), d2.sections()['PythonModule'].contents()
assert m1 == (TASK / 'geocity_city_module_4km_ky_v001.py').read_text(encoding='utf-8')
import difflib
diff = [l for l in difflib.unified_diff(m1.splitlines(), m2.splitlines(), lineterm='', n=0) if l.startswith(('+', '-')) and not l.startswith(('+++', '---'))]
p1 = d1.parmTemplateGroup().find('building_assembly_contract_json').defaultValue()
p2 = d2.parmTemplateGroup().find('building_assembly_contract_json').defaultValue()
assert p1 == p2, 'assembly contract default differs'
assert set(s for s in d1.sections()) == set(s for s in d2.sections()), (sorted(d1.sections()), sorted(d2.sections()))
others = [s for s in d1.sections() if s not in ('PythonModule',) and d1.sections()[s].contents() != d2.sections()[s].contents()]
node = hou.node('/obj').createNode('geo', 'v002_verify').createNode(T2, 'city', exact_type_name=True)
node.allowEditingOfContents(); node.allSubChildren(sync_delayed_definition=True)
grid = {n: node.node('terrain_grid_1009').parm(n).rawValue() for n in ('sizex', 'sizey', 'gridsamples', 'gridspacing')}
assert grid == {'sizex': '4032', 'sizey': '4032', 'gridsamples': '4033', 'gridspacing': '1'}
(TASK / 'geocity_city_module_4km_ky_v002.py').write_text(m2, encoding='utf-8')
record = {'status': 'SAVED_OWNED_4KM_HDA_V002_NOT_COOKED', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'path': str(DEST), 'sha256': sha(DEST), 'type': T2, 'previous': {'path': str(SRC), 'sha256': SRC_SHA, 'type': T1},
          'changes': ['ROAD_WIDTH_M: trunk 12, trunk_link 7, primary 10, primary_link 7 (v001 dropped them: road 44 missing)',
                      'ROAD_CLASSES: the same four are drivable roads',
                      'NO_SIDEWALK_CLASSES: no sidewalks along them (active cook_sidewalks only)',
                      'own operator type name 15.0_4km_karmeiyosef_v002'],
          'module_diff_lines': diff, 'other_sections_changed_vs_v001': others,
          'authority': 'Aviv 2026-10-11: "Generator builds it" + "Yes, full generator route"',
          'saved_heightfield_readback': grid, 'assembly_contract_default_equal_v001': True,
          'module_copy': str(TASK / 'geocity_city_module_4km_ky_v002.py'), 'cooked_in_authoring': False, 'v001_modified': sha(SRC) != SRC_SHA}
(TASK / 'HDA_SOURCE_V002.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({k: record[k] for k in ('status', 'sha256', 'type', 'module_diff_lines', 'other_sections_changed_vs_v001', 'v001_modified')}, indent=1))
