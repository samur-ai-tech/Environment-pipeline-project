"""Bind current assignments, succession, immutable commands and actual native lease."""
import hashlib
import json
import os
import builtins
import marshal
import subprocess
from pathlib import Path
import sys
import types
from . import intake as I

SUPPLIER='01a1075c-313d-7133-9bc5-580cb2681f9b'
_CACHE={}

def authority():
    path=I.HERE/'ASSIGNMENT.json';a=I.read(path)
    assert a['thread_id']==SUPPLIER,'supplier_identity_mismatch'
    receipt=(I.ROOT/a['management_succession']['receipt']).resolve()
    assert receipt.is_relative_to(I.ROOT/'Staging'),'succession_outside_project'
    s=I.read(receipt);bpath=I.BANK/'ASSIGNMENT.json';b=I.read(bpath)
    assert s['status']=='TRANSFERRED_TO_SUCCESSOR','succession_not_complete'
    manager=a['manager_thread_id'];operator=a['native_writer_thread']
    assert manager==s['successor_manager_thread_id']==a['management_succession']['successor_manager_thread_id']==b['system_owner'],'successor_identity_mismatch'
    assert a['previous_manager_thread_id']==s['previous_manager_thread_id'],'predecessor_identity_mismatch'
    assert operator==s['native_operator_thread_id']==b['thread'],'native_operator_identity_mismatch'
    return {'manager_thread_id':manager,'operator_thread_id':operator,'supplier_thread_id':SUPPLIER,
        'assignment_path':str(path),'assignment_sha256':I.sha(path),'succession_path':str(receipt),'succession_sha256':I.sha(receipt),
        'bank_assignment_path':str(bpath),'bank_assignment_sha256':I.sha(bpath)}

def immutable_json(path,data):
    p=Path(path).resolve();assert p.is_relative_to(I.HERE)
    payload=(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==payload,'immutable_artifact_conflict:'+str(p)
    else:
        with p.open('xb') as f:f.write(payload)
    return p

def manifest(path=None):
    if path is None:
        pointer=I.read(I.HERE/'COMMAND_MANIFEST.json')
        path=Path(pointer['path']);assert I.sha(path)==pointer['sha256'],'command_manifest_pointer_stale'
    path=Path(path).resolve();assert path.is_relative_to(I.HERE/'CommandManifests')
    m=I.read(path)
    assert m['authority']==authority(),'assignment_or_succession_changed_since_seal'
    for filename,digest in m['files'].items():
        assert I.sha(filename)==digest,'command_source_changed:'+filename
    assert I.sha(I.HERE/'READY_JOBS.json')==m['queue_sha256'],'queue_changed_since_seal'
    return m,path

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


def pinned_module(name,path,m,imports=None):
    p=Path(path).resolve();expected=m['files'][str(p)]
    assert I.sha(p)==expected,'pinned_source_changed'
    key=(name,str(p))
    if key in _CACHE:
        mod=_CACHE[key]
        assert Path(mod.__file__).resolve()==p and mod.__supplier_source_sha256__==expected,'cached_module_identity_mismatch_wait_fresh_process'
        assert mod.__supplier_code_sha256__==code_digest(mod),'cached_module_code_mismatch_wait_fresh_process'
        return mod
    code=p.read_bytes();assert hashlib.sha256(code).hexdigest()==expected
    mod=types.ModuleType('_ep_native_supplier_bank_'+name);mod.__file__=str(p)
    original_import=builtins.__import__
    def local_import(import_name,*args,**kwargs):
        if imports and import_name in imports:return imports[import_name]
        return original_import(import_name,*args,**kwargs)
    mod.__dict__['__builtins__']=dict(vars(builtins),__import__=local_import)
    exec(compile(code,str(p),'exec'),mod.__dict__)
    mod.__supplier_source_sha256__=expected
    mod.__supplier_code_sha256__=code_digest(mod)
    _CACHE[key]=mod
    return mod

def lease(action,activation,manifest_path=None):
    m,p=manifest(manifest_path);a=m['authority']
    assert activation['manager_thread_id']==a['manager_thread_id'],'activation_manager_mismatch'
    assert activation['operator_thread_id']==a['operator_thread_id'],'activation_operator_mismatch'
    assert activation['authority']==a,'activation_authority_revision_mismatch'
    assert activation['command_manifest_sha256']==I.sha(p),'activation_command_manifest_mismatch'
    assert activation['action']==action and activation['pid']==os.getpid(),'activation_action_or_pid_mismatch'
    assert activation['ordinary_generation_authorized'] is False
    fields=dict(t.split('=',1) for t in [v for v in (I.ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().splitlines() if v.strip()][-1].split() if '=' in t)
    assert fields.get('manager_thread_id')==a['manager_thread_id'] and fields.get('operator_thread_id')==a['operator_thread_id'],'lease_identity_mismatch'
    assert fields.get('assigned_editor_PID')==str(os.getpid()) and fields.get('activation')=='MANAGER_ACTIVATED','native_lease_not_activated'
    assert fields.get('native_authorized_now','true')!='false' and fields.get('native_handoff_clean','true')!='false','native_recovery_not_complete'
    # Actual OS process evidence, not only a lease's recorded PID.
    command="@(Get-Process UnrealEditor -ErrorAction SilentlyContinue | ForEach-Object { [pscustomobject]@{pid=$_.Id;executable=$_.Path;start_utc=$_.StartTime.ToUniversalTime().ToString('o')} }) | ConvertTo-Json -Compress"
    raw=subprocess.check_output(['powershell','-NoProfile','-Command',command],text=True).strip()
    processes=json.loads(raw) if raw else []
    if isinstance(processes,dict):processes=[processes]
    assert len(processes)==1 and processes[0]['pid']==os.getpid(),'actual_OS_editor_count_or_PID_mismatch'
    assert Path(processes[0]['executable']).name.lower()=='unrealeditor.exe'
    evidence={'action':action,'processes':processes,'lease_fields':fields,'authority':a,'command_manifest_sha256':I.sha(p)}
    key=hashlib.sha256(json.dumps(evidence,sort_keys=True).encode()).hexdigest()
    immutable_json(I.HERE/'NativeTransitions'/(key+'.json'),evidence)
    return m,p,fields
