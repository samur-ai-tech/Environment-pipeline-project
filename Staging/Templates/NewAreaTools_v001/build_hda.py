"""This area's owned generator. Template v001 (NewAreaTools_v001; maintained by the agent Aviv assigns, GOVERNANCE_RECORD.md RC-69); from the El Wahat v002 build
(edits-file pattern, playbook 3 and 10c). Base: Tools/area_constants.py HDA_BASE_* (it already holds the El Wahat road
edits L/L2/T). PythonModule edits in hda_edits.py (shared with verify_hda.py): P failed poles omitted for this area id, T the
module default track material = this area's TRACK_MI, plus EXTRA_EDITS from this area's [D] answers.
The building_assembly_contract_json default is kept from the base (asserted equal). New operator type hda_edits.TYPE in the
revision folder HDA_REVISION_DIR; the base and every earlier revision are only read (sha-checked before and after). Writes
the record hda_edits.RECORD (HDA_SOURCE.json for the first generator of the area). No cook. Run with hython:
    hython build_hda.py "<Aviv's words for this generator>"
"""
import datetime
import hashlib
import json
from pathlib import Path
import sys
import hou

TASK = Path(__file__).resolve().parent
sys.path.insert(0, str(TASK))
import hda_edits as E  # noqa: E402

assert len(sys.argv) == 2 and sys.argv[1].strip(), 'usage: hython build_hda.py "<Aviv\'s words for this generator>"'
AUTHORITY = sys.argv[1].strip()
GRID = E.A.GRID_SAMPLES
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(E.SRC) == E.SRC_SHA, 'Base HDA changed'
assert sha(E.REF_MODULE) == E.REF_MODULE_SHA, 'Base module copy changed'
assert not E.DEST.exists(), 'Retain existing revision; do not overwrite'
assert not (TASK / E.RECORD).exists(), E.RECORD + ' exists'

hou.setUpdateMode(hou.updateMode.Manual)
hou.hda.installFile(str(E.SRC))   # parmTemplateGroup() needs the base type installed (read only; KY v002 lesson)
definition = next(d for d in hou.hda.definitionsInFile(str(E.SRC)) if d.nodeTypeName() == E.SRC_TYPE)
text = definition.sections()['PythonModule'].contents()
assert text == E.REF_MODULE.read_text(encoding='utf-8'), 'module differs from the base module copy'
updated = E.apply(text)
compile(updated, E.TYPE, 'exec')
v1_contract = definition.parmTemplateGroup().find('building_assembly_contract_json').defaultValue()

definition.copyToHDAFile(str(E.DEST), new_name=E.TYPE, new_menu_name=E.MENU)
hou.hda.installFile(str(E.DEST))
new = next(d for d in hou.hda.definitionsInFile(str(E.DEST)) if d.nodeTypeName() == E.TYPE)
new.addSection('PythonModule', updated)
new.setIsPreferred(True)
new.save(str(E.DEST), create_backup=False)

saved = next(d for d in hou.hda.definitionsInFile(str(E.DEST)) if d.nodeTypeName() == E.TYPE)
assert saved.sections()['PythonModule'].contents() == updated
check = hou.node('/obj').createNode('geo', 'newarea_build_check').createNode(E.TYPE, 'city', exact_type_name=True)
check.allowEditingOfContents()
check.allSubChildren(sync_delayed_definition=True)
saved_grid = {n: check.node('terrain_grid_1009').parm(n).rawValue() for n in ('sizex', 'sizey', 'gridsamples', 'gridspacing')}
assert saved_grid == {'sizex': str(GRID - 1), 'sizey': str(GRID - 1), 'gridsamples': str(GRID), 'gridspacing': '1'}, saved_grid
assert check.parm('building_assembly_contract_json').rawValue() == v1_contract[0], 'assembly contract default differs from the base'
assert check.parm('route_surface_materials_json').rawValue() == '{}', 'route parm default changed'
assert sha(E.SRC) == E.SRC_SHA, 'Source HDA changed'
assert sha(E.REF_MODULE) == E.REF_MODULE_SHA, 'Reference module copy changed'

(TASK / E.MODULE_COPY).write_text(updated, encoding='utf-8')
record = {'status': 'SAVED_OWNED_HDA_NOT_COOKED', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'path': str(E.DEST), 'sha256': sha(E.DEST), 'type': E.TYPE, 'version': E.VERSION,
          'previous': {'path': str(E.SRC), 'sha256': E.SRC_SHA, 'type': E.SRC_TYPE},
          'changes': [e[3] for e in E.edits(text)] + ['own operator type name ' + E.TYPE],
          'track_material': E.TRACK_MI, 'unreal_asset': E.UNREAL_HDA,
          'authority': AUTHORITY,
          'saved_heightfield_readback': saved_grid, 'module_copy': str(TASK / E.MODULE_COPY),
          'assembly_contract_default_equal_base': True, 'cooked_in_authoring': False, 'base_modified': False,
          'verified_by_separate_script': False}
(TASK / E.RECORD).write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({k: record[k] for k in ('status', 'path', 'sha256', 'type', 'saved_heightfield_readback')}, indent=2))
