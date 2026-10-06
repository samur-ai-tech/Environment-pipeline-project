import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
p=root.parent.parent/'Environmentpipeline.uproject'
b=p.read_bytes();data=json.loads(b)
assert not any(x['Name']=='SunPosition' for x in data['Plugins'])
(root/'Before/Environmentpipeline.uproject').write_bytes(b)
marker=b'"Plugins": ['
assert b.count(marker)==1
patched=b.replace(marker,marker+b'\r\n\t\t{\r\n\t\t\t"Name": "SunPosition",\r\n\t\t\t"Enabled": true\r\n\t\t},',1)
check=json.loads(patched);check['Plugins']=check['Plugins'][1:];assert check==data
assert p.read_bytes()==b
p.write_bytes(patched)
(root/'DEPENDENCY_CHANGE.json').write_text(json.dumps({'plugin':'SunPosition','enabled':True,'other_fields_unchanged':True,'before_sha256':hashlib.sha256(b).hexdigest(),'after_sha256':hashlib.sha256(patched).hexdigest(),'other_editor_restart':False},indent=2))
print('Enabled only SunPosition; other project fields unchanged.')
