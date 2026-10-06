"""Preserve the rendered r016 revision and correct retained generated solids."""
from pathlib import Path
import json, hashlib, shutil, datetime

root = Path('C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank')
module = root / 'geocity_city_module.py'
source = module.read_text(encoding='utf-8')
previous = source.replace(
    "    # Houdini's polygon front and N use the negative raw cross convention.\n    return tuple(-component for component in n.normalized())",
    '    return tuple(n.normalized())').replace(
    "            # The closed solid's mathematical winding must be reversed for\n            # Houdini fronts; _normal uses the same outward convention.\n            face_points = [vertices[row][column] for row, column in reversed(indices)]",
    '            face_points = [vertices[row][column] for row, column in indices]')
assert hashlib.sha256(previous.replace('\n', '\r\n').encode()).hexdigest() == '532ebaeb2b8cd6dead5c3987a10f3a168fd6e6a5c03572dbdeede9b7d4383706'
archive = root / 'revisions/r016_inward_roof_before_repair'
archive.mkdir(parents=True, exist_ok=False)
(archive / module.name).write_text(previous, encoding='utf-8')
shutil.copy2(root / 'GeoCity_city_v015_PermanentBank.hdalc', archive / 'unversioned_winding_before_r017.hdalc')
shutil.copy2(root / 'definition_receipt.json', archive / 'unversioned_winding_receipt.json')
project = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
shutil.copy2(project / 'Content/Project/Shared/ModelBank/HDA/GeoCity_city_v015_PermanentBank.uasset', archive / 'r016_saved_native_HDA.uasset')
for name in ('WORKFLOW_STATE.json', 'HDA_CATALOG_RECEIPT.json'):
    shutil.copy2(project / 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02' / name, archive / name)
(archive / 'ARCHIVE_NOTE.txt').write_text('r016 module bytes verified against the original SHA256. Native HDA uasset and area receipts are the saved r016 artifacts. The separately named unversioned HDA was authored with the winding correction before the revision label advanced; it is not the original r016 external HDA.\n')
source = source.replace('r016_retained_native_environment', 'r017_retained_native_environment')
compile(source, str(module), 'exec')
module.write_text(source, encoding='utf-8')
receipt = json.loads((root / 'definition_receipt.json').read_text())
receipt.update(revision='r017_retained_native_environment',
    revision_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    status='authored_pending_two_real_area_regeneration',
    validation='Pending actual r017 official Engine replacement and saved-area inspection in both existing areas.',
    repair=receipt['repair'] + '; corrected outward Houdini front winding and aligned normals for every closed generated roof/floor/corner solid')
(root / 'definition_receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps({'archived': str(archive), 'revision': receipt['revision']}))
