"""Exact reviewed source loader; no stale bytecode/hot reload or implicit native action."""
import hashlib, importlib.util, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(request_path,request_sha,activation_path,command,family_id=None,max_parts=8,activation_sha=None):
    assert sha(request_path)==request_sha
    request=json.loads(Path(request_path).read_text(encoding='utf-8-sig'))
    assert request['family_count']==20 and request['part_count']==609
    assert request['python_sources'][str(Path(__file__).resolve())]==sha(__file__)
    for path,expected in request['python_sources'].items():assert sha(path)==expected,('unreviewed_source',path)
    def load(name,path):
        path=Path(path).resolve();assert str(path) in request['python_sources']
        if name in sys.modules:
            module=sys.modules[name];assert Path(module.__file__).resolve()==path
        else:
            spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
            sys.modules[name]=module
            try:exec(compile(path.read_bytes(),str(path),'exec',dont_inherit=True),module.__dict__)
            except Exception:sys.modules.pop(name,None);raise
        return module
    loader=load('bank_batch_loader',HERE.parent/'bank_batch_loader.py');loader.verify_module(loader,loader.__file__)
    loader.verify_module(sys.modules[__name__],__file__)
    if command=='inspect_startup':
        assert activation_sha
        module=load('modular_startup_inspector_20261005',HERE/'inspect_modular_startup.py')
        loader.verify_module(module,module.__file__)
        return module.inspect(activation_path,activation_sha)
    assert command=='import_family' and 1<=int(max_parts)<=20
    for name in ('bank_contracts','native_bank_ops','import_prepared'):
        module=load(name,HERE.parent/(name+'.py'));loader.verify_module(module,module.__file__)
    module=load('modular_native_adapter_20261005',HERE/'modular_native_adapter.py')
    loader.verify_module(module,module.__file__)
    result=module.run(request_path,request_sha,activation_path,family_id,int(max_parts))
    return {k:result[k] for k in ('family_id','expected_part_count','imported_part_count','complete_native_import','native_reloaded','procedural_eligible')}
