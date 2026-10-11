"""Owned Karmei Yosef 4 km generator v001, derived from the Lebanon 4 km v006 HDA (already 4033 samples / 1 m).

Same two changes as the Karmei Yosef 2 km v002 generator, carried over by Aviv's choices (2026-10-08):
1. cook_vegetation places no generated placeholder tree blockouts (vegetation comes from Unreal PCG);
2. failed generated decorations (street poles) are omitted like the Gaza areas: this area id is added to the final proxy
   policy tuple (two places).
New operator type name (15.0_4km_karmeiyosef) so it never collides with Lebanon's 15.0_4km_currentbank asset inside
Unreal. Also sets the building_assembly_contract_json default from PROFILE_CANDIDATE.json (the sealed workflow sets it at
runtime anyway). No cook; Lebanon, canonical and Karmei Yosef 2 km HDAs untouched.
"""
import datetime
import hashlib
import json
from pathlib import Path
import hou

TASK = Path(__file__).resolve().parent
SRC = Path(r"C:\Users\USER\Documents\Pipeline Environment\Houdini\GeoCity_city_v015_PermanentBank\revisions\20261007_Lebanon_4km_CurrentBank\GeoCity_city_v015_CurrentBank_4km_v006.hdalc")
SRC_SHA = "60edf95cb2d91a6872ada28490ae2af78224e2390a45ab816eab8839a965e07f"
SRC_TYPE = "trackb::geocity_city::15.0_4km_currentbank"
REV = Path(r"C:\Users\USER\Documents\Pipeline Environment\Houdini\GeoCity_city_v015_PermanentBank\revisions\20261008_KarmeiYosef_4km")
DEST = REV / "GeoCity_city_v015_CurrentBank_4km_KY_v001.hdalc"
TYPE = "trackb::geocity_city::15.0_4km_karmeiyosef"
AREA = "KarmeiYosef_31850349_34907601_4km"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(SRC) == SRC_SHA, 'v006 changed'
assert not DEST.exists(), 'Retain existing revision; do not overwrite'
REV.mkdir(parents=True, exist_ok=True)
hou.setUpdateMode(hou.updateMode.Manual)
definition = next(d for d in hou.hda.definitionsInFile(str(SRC)) if d.nodeTypeName() == SRC_TYPE)
text = definition.sections()['PythonModule'].contents()
assert 'GRID_SAMPLES = 4033' in text
old_trees = ("    placed=[]\n"
             "    ix0,ix1=math.floor(xmin/spacing),math.ceil(xmax/spacing)\n"
             "    iz0,iz1=math.floor(zmin/spacing),math.ceil(zmax/spacing)\n")
new_trees = ("    placed=[]\n"
             "    # Karmei Yosef 4 km v001 (Aviv 2026-10-08): no generated placeholder tree\n"
             "    # blockouts; vegetation comes from the Unreal PCG tool.\n"
             "    ix0,ix1=0,0\n"
             "    iz0,iz1=0,0\n")
old_poles = "not in ('GazaRimal', 'GazaShujaiya')"
new_poles = "not in ('GazaRimal', 'GazaShujaiya', '%s')" % AREA
assert text.count(old_trees) == 1 and text.count(old_poles) == 2
updated = text.replace(old_trees, new_trees).replace(old_poles, new_poles)
compile(updated, 'geocity_currentbank_4km_karmeiyosef_v001', 'exec')
definition.copyToHDAFile(str(DEST), new_name=TYPE, new_menu_name='GeoCity current bank - 4 km (Karmei Yosef v001)')
hou.hda.installFile(str(DEST))
new = next(d for d in hou.hda.definitionsInFile(str(DEST)) if d.nodeTypeName() == TYPE)
new.addSection('PythonModule', updated)
group = new.parmTemplateGroup()
profile = json.loads((TASK / 'PROFILE_CANDIDATE.json').read_text(encoding='utf-8'))
parm = group.find('building_assembly_contract_json')
parm.setDefaultValue((json.dumps(profile['building_assembly_contract']),))
group.replace(parm.name(), parm)
new.setParmTemplateGroup(group)
new.setIsPreferred(True)
new.save(str(DEST), create_backup=False)
saved = next(d for d in hou.hda.definitionsInFile(str(DEST)) if d.nodeTypeName() == TYPE)
assert saved.sections()['PythonModule'].contents() == updated
check = hou.node('/obj').createNode('geo', 'karmeiyosef_4km_check').createNode(TYPE, 'city', exact_type_name=True)
check.allowEditingOfContents()
check.allSubChildren(sync_delayed_definition=True)
saved_grid = {n: check.node('terrain_grid_1009').parm(n).rawValue() for n in ('sizex', 'sizey', 'gridsamples', 'gridspacing')}
assert saved_grid == {'sizex': '4032', 'sizey': '4032', 'gridsamples': '4033', 'gridspacing': '1'}, saved_grid
assert sha(SRC) == SRC_SHA, 'Source HDA changed'
(TASK / 'geocity_city_module_4km_ky_v001.py').write_text(updated, encoding='utf-8')
record = {'status': 'SAVED_OWNED_4KM_HDA_NOT_COOKED', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'path': str(DEST), 'sha256': sha(DEST), 'type': TYPE, 'previous': {'path': str(SRC), 'sha256': SRC_SHA, 'type': SRC_TYPE},
          'changes': ['cook_vegetation places no generated placeholder trees (Aviv 2026-10-08)',
                      'failed generated street poles omitted like the Gaza areas (area id added to the final proxy policy tuple, 2 places)',
                      'own operator type name to avoid colliding with the Lebanon 4 km asset'],
          'saved_heightfield_readback': saved_grid, 'module_copy': str(TASK / 'geocity_city_module_4km_ky_v001.py'),
          'cooked_in_authoring': False, 'canonical_bank_hda_modified': False, 'lebanon_hda_modified': False}
(TASK / 'HDA_SOURCE.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({k: record[k] for k in ('status', 'path', 'sha256', 'type', 'saved_heightfield_readback')}, indent=2))
