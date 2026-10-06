"""Verify exact source, loaded hashes and function code without hot reloading.
Supplier modules use a unique package namespace. Generic modules are untouched.
"""
from pathlib import Path
import hashlib
import json
import marshal
import sys
import types

PACKAGE='_ep_native_unreal_supply_20261004'
LOADED_SOURCE_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def code_digest(module):
    def encode(code):
        return {'bytecode':code.co_code.hex(),'names':code.co_names,'locals':code.co_varnames,
            'free':code.co_freevars,'cells':code.co_cellvars,'flags':code.co_flags,
            'args':[code.co_argcount,code.co_kwonlyargcount,getattr(code,'co_posonlyargcount',0)],
            'filename':code.co_filename,'firstline':code.co_firstlineno,
            'exceptiontable':getattr(code,'co_exceptiontable',b'').hex(),
            'constants':[encode(c) if isinstance(c,types.CodeType) else {'value':repr(c)} for c in code.co_consts]}
    payload={name:{'code':encode(value.__code__),'defaults':repr(value.__defaults__),'kwdefaults':repr(value.__kwdefaults__)}
        for name,value in sorted(vars(module).items()) if isinstance(value,types.FunctionType) and value.__module__==module.__name__}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def load_exact(here,files,names):
    """Reuse verified modules; compile only absent modules. No replacement or reload."""
    here=Path(here).resolve();package=sys.modules.get(PACKAGE)
    if package is None:
        package=types.ModuleType(PACKAGE);package.__path__=[str(here)];package.__package__=PACKAGE
        package.__supplier_root__=str(here);sys.modules[PACKAGE]=package
    else:
        assert getattr(package,'__supplier_root__',None)==str(here) and package.__path__==[str(here)],'unrelated_unique_package_collision'
    # A legacy generic import of these same supplier files is also loaded code.
    # Never sidestep it by compiling a changed revision under a new namespace.
    supplier_paths={str(here/(short+'.py')):short for short in names}
    aliases={}
    for registered,old in list(sys.modules.items()):
        if old is None or registered.startswith(PACKAGE+'.'):continue
        filename=getattr(old,'__file__',None)
        if not filename:continue
        resolved=str(Path(filename).resolve())
        if resolved not in supplier_paths:continue
        expected=files[resolved]
        assert getattr(old,'__supplier_source_sha256__',None)==expected,'legacy_loaded_supplier_hash_requires_fresh_process'
        assert getattr(old,'__supplier_code_sha256__',None)==code_digest(old),'legacy_loaded_supplier_code_requires_fresh_process'
        assert getattr(old,'__package__',None)==PACKAGE,'legacy_supplier_namespace_requires_fresh_process'
        aliases[supplier_paths[resolved]]=old
    # Check every existing module before compiling any absent one.
    for short in names:
        name=PACKAGE+'.'+short;p=here/(short+'.py');expected=files[str(p)]
        assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,'source_changed_wait_fresh_process'
        old=sys.modules.get(name)
        if old is not None:
            assert Path(old.__file__).resolve()==p,'cached_module_path_mismatch_wait_fresh_process'
            assert getattr(old,'__supplier_source_sha256__',None)==expected,'cached_module_source_mismatch_wait_fresh_process'
            assert getattr(old,'__supplier_code_sha256__',None)==code_digest(old),'cached_module_code_mismatch_wait_fresh_process'
    for short in names:
        name=PACKAGE+'.'+short;p=here/(short+'.py')
        if name in sys.modules:continue
        if short in aliases:
            sys.modules[name]=aliases[short];setattr(package,short,aliases[short]);continue
        data=p.read_bytes();expected=files[str(p)];assert hashlib.sha256(data).hexdigest()==expected
        module=types.ModuleType(name);module.__file__=str(p);module.__package__=PACKAGE
        sys.modules[name]=module
        try:exec(compile(data,str(p),'exec'),module.__dict__)
        except BaseException:
            sys.modules.pop(name,None);raise
        module.__supplier_source_sha256__=expected;module.__supplier_code_sha256__=code_digest(module)
        setattr(package,short,module)
    return {short:sys.modules[PACKAGE+'.'+short] for short in names}


def run(manifest_path,command,kwargs=None):
    path=Path(manifest_path).resolve();m=json.loads(path.read_text(encoding='utf-8'))
    self_path=str(Path(__file__).resolve())
    assert m['files'][self_path]==LOADED_SOURCE_SHA256==hashlib.sha256(Path(self_path).read_bytes()).hexdigest(),'stale_entrypoint_wait_fresh_process'
    here=Path(self_path).parent;assert path.is_relative_to(here/'CommandManifests')
    for filename,digest in m['files'].items():
        assert hashlib.sha256(Path(filename).read_bytes()).hexdigest()==digest,'pinned_file_changed:'+filename
    entries={'inspect':('native_supplier','inspect'),'build_registration':('native_supplier','build_registration'),
        'validate_transaction':('native_supplier','validate_transaction'),'apply_registration':('native_supplier','apply_registration'),
        'capture_source':('source_migration','capture'),'migrate_source':('source_migration','export'),
        'plan_migration':('migration_remap','plan'),'remap_native':('migration_remap','remap'),
        'prepare_target_jobs':('post_remap','prepare_jobs'),'prepare_intake':('qualification_intake','prepare'),
        'validate_intake':('qualification_intake','validate'),'apply_prepared':('qualification_intake','apply_prepared')}
    assert command in entries
    names=['integrity','intake','authority','native_supplier','source_migration','migration_remap','post_remap','qualification_intake','targeted_measurement']
    mods=load_exact(here,m['files'],names)
    mods['authority'].manifest(path)
    pointer=mods['intake'].read(here/'COMMAND_MANIFEST.json')
    assert Path(pointer['path']).resolve()==path and pointer['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    mod,fn=entries[command]
    return getattr(mods[mod],fn)(**(kwargs or {}))
