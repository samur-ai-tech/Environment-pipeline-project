"""Owned Karmei Yosef 4 km generator v002, derived from v001 (Aviv 2026-10-11: road 44 must be built by the generator,
"Yes, full generator route"). v001 dropped every OSM highway class missing from ROAD_WIDTH_M, so road 44 (highway=trunk)
and its links were never built although the source package contains them. Changes (PythonModule only):
1. ROAD_WIDTH_M: trunk 12 m, trunk_link 7 m, primary 10 m, primary_link 7 m (OSM 'width' tags still win, as for every class);
2. ROAD_CLASSES: the same four classes are drivable roads (road surface mesh, road bed paint, junctions);
3. NO_SIDEWALK_CLASSES: no 1.5 m sidewalks along them (rural highway; the active cook_sidewalks treats them as non-drivable
   edges for the sidewalk lane only).
New operator type name 15.0_4km_karmeiyosef_v002 so it never collides with v001 inside Unreal. No cook; v001 and every other
HDA untouched. Run with hython.
"""
import datetime
import hashlib
import json
from pathlib import Path
import hou

TASK = Path(__file__).resolve().parent
REV = Path(r"C:\Users\USER\Documents\Pipeline Environment\Houdini\GeoCity_city_v015_PermanentBank\revisions\20261008_KarmeiYosef_4km")
SRC = REV / "GeoCity_city_v015_CurrentBank_4km_KY_v001.hdalc"
SRC_SHA = "1789ea386217e5b958b82e8369134a0fd04e5a00adcc5246eacfdd8bae9e4797"
SRC_TYPE = "trackb::geocity_city::15.0_4km_karmeiyosef"
DEST = REV / "GeoCity_city_v015_CurrentBank_4km_KY_v002.hdalc"
TYPE = "trackb::geocity_city::15.0_4km_karmeiyosef_v002"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(SRC) == SRC_SHA, 'v001 changed'
assert not DEST.exists(), 'Retain existing revision; do not overwrite'
hou.setUpdateMode(hou.updateMode.Manual)
definition = next(d for d in hou.hda.definitionsInFile(str(SRC)) if d.nodeTypeName() == SRC_TYPE)
text = definition.sections()['PythonModule'].contents()
assert text == (TASK / 'geocity_city_module_4km_ky_v001.py').read_text(encoding='utf-8'), 'module differs from the v001 copy'
EDITS = [
    ('                "track": 3.0, "unclassified": 6.0}\n',
     '                "track": 3.0, "unclassified": 6.0,\n'
     '                # Karmei Yosef 4 km v002 (Aviv 2026-10-11): road 44 and its links were dropped by v001.\n'
     '                "trunk": 12.0, "trunk_link": 7.0, "primary": 10.0, "primary_link": 7.0}\n'),
    ('ROAD_CLASSES = {"secondary", "secondary_link", "tertiary", "residential", "service", "unclassified"}\n',
     'ROAD_CLASSES = {"secondary", "secondary_link", "tertiary", "residential", "service", "unclassified",\n'
     '                "trunk", "trunk_link", "primary", "primary_link"}\n'),
    ('FOOTPATH_CLASSES = {"footway", "path", "track"}\n',
     'FOOTPATH_CLASSES = {"footway", "path", "track"}\n'
     '# v002: rural highways get no 1.5 m sidewalks (road surface and road bed only)\n'
     'NO_SIDEWALK_CLASSES = {"trunk", "trunk_link", "primary", "primary_link"}\n'),
    ("            if cls not in ROAD_CLASSES:\n                ledger['non_drivable_edge_count'] += 1\n",
     "            if cls not in ROAD_CLASSES or cls in NO_SIDEWALK_CLASSES:\n                ledger['non_drivable_edge_count'] += 1\n"),
]
updated = text
for old, new in EDITS:
    assert updated.count(old) == 1, ('edit anchor not unique', old[:60], updated.count(old))
    updated = updated.replace(old, new)
assert updated.count('def cook_sidewalks') == 2 and updated.rfind('NO_SIDEWALK_CLASSES:\n') > updated.rfind('def cook_sidewalks'), \
    'the sidewalk edit must be in the last (active) cook_sidewalks definition'
compile(updated, 'geocity_currentbank_4km_karmeiyosef_v002', 'exec')
definition.copyToHDAFile(str(DEST), new_name=TYPE, new_menu_name='GeoCity current bank - 4 km (Karmei Yosef v002)')
hou.hda.installFile(str(DEST))
new = next(d for d in hou.hda.definitionsInFile(str(DEST)) if d.nodeTypeName() == TYPE)
new.addSection('PythonModule', updated)
new.setIsPreferred(True)
new.save(str(DEST), create_backup=False)
saved = next(d for d in hou.hda.definitionsInFile(str(DEST)) if d.nodeTypeName() == TYPE)
assert saved.sections()['PythonModule'].contents() == updated
check = hou.node('/obj').createNode('geo', 'karmeiyosef_4km_v002_check').createNode(TYPE, 'city', exact_type_name=True)
check.allowEditingOfContents()
check.allSubChildren(sync_delayed_definition=True)
saved_grid = {n: check.node('terrain_grid_1009').parm(n).rawValue() for n in ('sizex', 'sizey', 'gridsamples', 'gridspacing')}
assert saved_grid == {'sizex': '4032', 'sizey': '4032', 'gridsamples': '4033', 'gridspacing': '1'}, saved_grid
v1_parm = next(d for d in hou.hda.definitionsInFile(str(SRC)) if d.nodeTypeName() == SRC_TYPE).parmTemplateGroup().find('building_assembly_contract_json').defaultValue()
assert check.parm('building_assembly_contract_json').rawValue() == v1_parm[0], 'assembly contract default differs from v001'
assert sha(SRC) == SRC_SHA, 'Source HDA changed'
(TASK / 'geocity_city_module_4km_ky_v002.py').write_text(updated, encoding='utf-8')
record = {'status': 'SAVED_OWNED_4KM_HDA_V002_NOT_COOKED', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'path': str(DEST), 'sha256': sha(DEST), 'type': TYPE, 'previous': {'path': str(SRC), 'sha256': SRC_SHA, 'type': SRC_TYPE},
          'changes': ['ROAD_WIDTH_M: trunk 12, trunk_link 7, primary 10, primary_link 7 (v001 dropped them: road 44 missing)',
                      'ROAD_CLASSES: the same four are drivable roads',
                      'NO_SIDEWALK_CLASSES: no sidewalks along them (active cook_sidewalks only)',
                      'own operator type name 15.0_4km_karmeiyosef_v002'],
          'authority': 'Aviv 2026-10-11: "Generator builds it" + "Yes, full generator route"',
          'saved_heightfield_readback': saved_grid, 'module_copy': str(TASK / 'geocity_city_module_4km_ky_v002.py'),
          'cooked_in_authoring': False, 'v001_modified': False}
(TASK / 'HDA_SOURCE_V002.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({k: record[k] for k in ('status', 'path', 'sha256', 'type', 'saved_heightfield_readback')}, indent=2))
