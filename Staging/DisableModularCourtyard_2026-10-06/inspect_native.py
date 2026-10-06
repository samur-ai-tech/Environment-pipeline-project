import unreal,pathlib,json,os,hashlib
P=pathlib.Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline');D=P/'Staging/DisableModularCourtyard_2026-10-06'
a=json.loads((D/'ASSIGNMENT.json').read_text());rows=[]
for path in sorted(set(p['hda'] for p in a['profiles'])):
 obj=unreal.load_asset(path);assert obj;source=pathlib.Path(obj.get_editor_property('asset_import_data').get_first_filename());native=P/('Content/'+path[6:]+'.uasset');assert source.is_file()
 rows.append(dict(asset=path,source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),native_file=str(native),native_sha256=hashlib.sha256(native.read_bytes()).hexdigest()))
(D/'NATIVE_BEFORE.json').write_text(json.dumps(dict(pid=os.getpid(),hdas=rows),indent=2));print('HDA_READBACK',len(rows))
