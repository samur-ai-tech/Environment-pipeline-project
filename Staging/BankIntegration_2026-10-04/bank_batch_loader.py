"""Exact-source category command loader. Refuses stale caches; never reloads them."""
import hashlib
import importlib.util
import inspect
import json
import sys
import types
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def signature(code):
    return (code.co_code,tuple(signature(v) if isinstance(v,types.CodeType) else v for v in code.co_consts),
        code.co_names,code.co_varnames,code.co_freevars,code.co_cellvars,code.co_argcount,
        code.co_posonlyargcount,code.co_kwonlyargcount,code.co_flags,getattr(code,'co_exceptiontable',b''))


def verify_module(module,path):
    path=Path(path).resolve(strict=True)
    assert Path(module.__file__).resolve(strict=True)==path,('wrong_module_origin',module.__name__)
    expected={}
    def walk(code):
        expected[getattr(code,'co_qualname',code.co_name)]=code
        for v in code.co_consts:
            if isinstance(v,types.CodeType): walk(v)
    walk(compile(path.read_bytes(),str(path),'exec',dont_inherit=True))
    functions=[]
    for v in vars(module).values():
        if inspect.isfunction(v) and v.__module__==module.__name__: functions.append(v)
        elif inspect.isclass(v) and v.__module__==module.__name__:
            for member in vars(v).values():
                if isinstance(member,(staticmethod,classmethod)): member=member.__func__
                if inspect.isfunction(member): functions.append(member)
                elif isinstance(member,property): functions.extend(f for f in (member.fget,member.fset,member.fdel) if f is not None)
    for fn in functions:
        fn=inspect.unwrap(fn)
        assert Path(fn.__code__.co_filename).resolve(strict=True)==path,('function_origin_changed',fn.__qualname__)
        wanted=expected.get(fn.__qualname__) or expected.get(fn.__name__)
        assert wanted is not None and signature(fn.__code__)==signature(wanted),('stale_loaded_bank_helper_restart_required',module.__name__,fn.__qualname__)
    return {'module':module.__name__,'path':str(path),'module_identity':id(module),'verified_functions':len(functions)}


def verify_closure(manifest_path,expected_sha256):
    manifest_path=Path(manifest_path).resolve(strict=True)
    assert sha(manifest_path)==expected_sha256,'unreviewed_batch_manifest'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    approved={str(Path(p).resolve(strict=True)):s for p,s in manifest['python_sources'].items()}
    for p,s in approved.items(): assert sha(p)==s,('batch_helper_changed',p)
    for p,s in manifest['payload_files'].items(): assert sha(p)==s,('batch_payload_changed',p)
    checked=[]
    for name,m in list(sys.modules.items()):
        origin=getattr(m,'__file__',None)
        if not origin: continue
        path=Path(origin).resolve()
        if path==HERE or HERE in path.parents:
            assert str(path) in approved,('unbound_loaded_bank_helper',name,str(path))
            checked.append(verify_module(m,path))
    return manifest,checked


def load_command(manifest_path,expected_sha256,command_name):
    manifest,checked=verify_closure(manifest_path,expected_sha256)
    command=manifest['commands'][command_name]
    path=Path(command['path']).resolve(strict=True)
    name=command['module_name']
    assert str(path) in manifest['python_sources']
    if name in sys.modules:
        module=sys.modules[name];verify_module(module,path)
    else:
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module
        try:
            exec(compile(path.read_bytes(),str(path),'exec',dont_inherit=True),module.__dict__)
            verify_module(module,path)
        except Exception:
            if sys.modules.get(name) is module: del sys.modules[name]
            raise
    verify_closure(manifest_path,expected_sha256)
    return getattr(module,command['function'])


def execute(manifest_path,expected_sha256,command_name,**kwargs):
    # The native helper enforces manager activation, actual PID/world and dirty scope.
    import native_bank_ops
    fn=load_command(manifest_path,expected_sha256,command_name)
    native_bank_ops.preflight()
    identities={name:id(m) for name,m in sys.modules.items() if getattr(m,'__file__',None) and HERE in Path(m.__file__).resolve().parents}
    result=fn(**kwargs)
    verify_closure(manifest_path,expected_sha256)
    assert all(name in sys.modules and id(sys.modules[name])==identity for name,identity in identities.items()),'bank_module_identity_replaced'
    return result
