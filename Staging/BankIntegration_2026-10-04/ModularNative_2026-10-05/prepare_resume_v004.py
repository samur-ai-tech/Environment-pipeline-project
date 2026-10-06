"""Retain v003 import implementation; add bounded resume and per-part isolation."""
from pathlib import Path
import hashlib, json, os
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent
src=(HERE/'modular_native_adapter_v003.py').read_text()
src=src.replace("assert not E.does_asset_exist(dest) and not C.package_file(dest).exists(),('unreceipted_existing_destination',dest)","assert (not E.does_asset_exist(dest) and not C.package_file(dest).exists()) or dest in RESUME_REIMPORT,('unreceipted_existing_destination',dest)")
src=src.replace("objects=P.import_file(import_source,dest,opts,unreal.FbxFactory())","objects=resume_import_file(import_source,dest,opts,unreal.FbxFactory())")
src=src.replace("dirty=N.dirty();assert not dirty['maps'] and set(dirty['content']).issubset(created),('unexpected_dirty_packages',dirty)","dirty=N.dirty();assert set(dirty['maps'])==set(RESUME_BASELINE['maps']) and set(dirty['content']).issubset(set(created)|set(RESUME_BASELINE['content'])),('unexpected_dirty_packages',dirty)")
src=src.replace("assert N.dirty()=={'content':[],'maps':[]}\n    closure=", "assert set(N.dirty()['maps'])==set(RESUME_BASELINE['maps']) and set(N.dirty()['content']).issubset(RESUME_BASELINE['content'])\n    closure=")
needle="""        material_receipt=read(HERE/'MaterialReceipts'/(key+'.json'))"""
replacement="""        receipt_file=HERE/'MaterialReceipts'/(key+'.json')
        if not receipt_file.is_file():
            mat=unreal.load_asset(dest)
            assert dest in RESUME_OWNED,('unreceipted_unowned_material',dest)
            assert E.get_metadata_tag(mat,'ModularRecipeSHA256')==key
            assert E.get_metadata_tag(mat,'ModularRecipeComplete')=='true'
            created[dest]=mat
            for tex in M.get_used_textures(mat):
                path=tex.get_path_name().split('.')[0]
                if path in N.dirty()['content']:
                    assert path in RESUME_OWNED,('unowned_dirty_texture',path)
                    created[path]=tex
            return mat
        material_receipt=read(receipt_file)"""
assert needle in src
src=src.replace(needle,replacement)
src+='''

# Resume-only boundary. Original import geometry/material/UV checks above are retained.
RESUME_BASELINE={'content':[], 'maps':[]}
RESUME_OWNED=set()
RESUME_REIMPORT=set()
RESUME_REQUEST=None
RESUME_BASES={}

def resume_import_file(filename,dest,options,factory):
    if dest not in RESUME_REIMPORT:
        return P.import_file(filename,dest,options,factory)
    assert not C.package_file(dest).exists() and dest in RESUME_OWNED
    task=unreal.AssetImportTask()
    for k,v in {'filename':str(filename),'destination_path':dest.rsplit('/',1)[0],
                'destination_name':dest.rsplit('/',1)[1],'automated':True,
                'replace_existing':True,'replace_existing_settings':True,'save':False,
                'options':options,'factory':factory}.items():task.set_editor_property(k,v)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    result=list(task.get_objects());assert result,('import_returned_no_objects',filename)
    return result

def resume_boundary():
    activation=read(HERE/'RESUME_ACTIVATION_v004.json')
    assert activation['native_authorized_now'] and activation['assigned_editor_PID']==os.getpid()
    lease=[l for l in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().splitlines() if l.strip()][-1]
    import geocity_editor_action
    fields=geocity_editor_action.lease_fields(lease)
    assert fields.get('OWNER')=='CODEX_BANK_INTEGRATION'
    assert fields.get('operator_thread_id')==activation['operator_thread_id']
    assert fields.get('assigned_editor_PID')==str(os.getpid())
    assert fields.get('activation')=='MODULAR_NATIVE_RESUME_V004'
    assert fields.get('native_authorized_now')=='true'
    ids=json.loads(subprocess.check_output(['powershell','-NoProfile','-NonInteractive','-Command','ConvertTo-Json -Compress -InputObject @((Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue).Id)'],creationflags=subprocess.CREATE_NO_WINDOW,text=True))
    assert ids==[os.getpid()]
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
    assert world==activation['world']
    assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
    return activation,{'pid':os.getpid(),'world':world,'activation_sha256':sha(HERE/'RESUME_ACTIVATION_v004.json')}

def resume_initialize():
    global RESUME_REQUEST,RESUME_BASELINE
    activation,state=resume_boundary()
    RESUME_REQUEST=read(HERE/'NATIVE_IMPORT_REQUEST_v003.json')
    assert sha(HERE/'NATIVE_IMPORT_REQUEST_v003.json')==activation['request_sha256']
    for path,expected in RESUME_REQUEST['python_sources'].items():assert sha(path)==expected
    for module in (C,N,P,L,sys.modules[__name__]):L.verify_module(module,module.__file__)
    for path,expected in protected_files(activation['preservation_path']).items():assert sha(path)==expected,('protected_file_changed',path)
    before=N.dirty();RESUME_BASELINE=before
    previous=read(HERE/'USER_DEADLINE_STOP_2026-10-05.json')
    RESUME_OWNED.update(set(before['content']) & set(previous['dirty']['content']))
    # Only the exact failed, never-saved mesh may be reimported in place.
    RESUME_REIMPORT.add(NATIVE_ROOT+'/H0017/Modules/SM_H0017_Ground_SWCorner')
    reused=[];pins={}
    for family in RESUME_REQUEST['families']:
        for part in family['parts']:
            rp=HERE/'Receipts'/family['id']/(part['name']+'.json')
            if rp.is_file():
                r=read(rp);assert r['named_saved'] and r['source_sha256']==part['fbx_sha256']
                assert E.does_asset_exist(part['native_package'])
                pins.update(r['saved_packages']);reused.append(part['derivative_id'])
                RESUME_BASES[family['id']]=r['basis_readback']['source_xyz_to_native_xyz']
    assert len(reused)==34
    for path,expected in pins.items():assert sha(C.package_file(path))==expected
    write(HERE/'RESUME_BASELINE_v004.json',{'state':state,'dirty':before,'owned_partial_packages':sorted(RESUME_OWNED),'reused':reused,'preserved_saved_packages':pins})
    write(HERE/'RESUME_RESULT_v004.json',{'status':'RUNNING','reused_existing':reused,'imported_saved':[],'failed':[]})
    return {'reused':len(reused),'remaining':575,'preserved_dirty':before}

def resume_batch(max_parts=15):
    global RESUME_BASELINE
    activation,state=resume_boundary()
    assert RESUME_REQUEST is not None
    result=read(HERE/'RESUME_RESULT_v004.json')
    done=set(result['reused_existing'])|{r['id'] for r in result['imported_saved']}|{r['id'] for r in result['failed']}
    count=0
    for family in RESUME_REQUEST['families']:
        for part in family['parts']:
            if part['derivative_id'] in done:continue
            if count>=max_parts:break
            RESUME_BASELINE=N.dirty();count+=1
            try:
                r=import_part(family,part,activation['request_sha256'],state,RESUME_BASES.get(family['id']))
                RESUME_BASES[family['id']]=r['basis_readback']['source_xyz_to_native_xyz']
                result['imported_saved'].append({'id':part['derivative_id'],'family':family['id'],'name':part['name'],'native_package':part['native_package']})
            except Exception as exc:
                import traceback
                failure={'id':part['derivative_id'],'family':family['id'],'name':part['name'],'native_package':part['native_package'],
                         'error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'dirty_after':N.dirty()}
                result['failed'].append(failure)
                write(HERE/'RepairQueue'/family['id']/(part['name']+'.json'),failure)
            after=N.dirty()
            RESUME_OWNED.update(set(after['content'])-set(RESUME_BASELINE['content']))
            result['last_part']=part['name'];result['dirty_remaining']=after
            write(HERE/'RESUME_RESULT_v004.json',result)
        if count>=max_parts:break
    total=len(result['reused_existing'])+len(result['imported_saved'])+len(result['failed'])
    if total==609:
        baseline=read(HERE/'RESUME_BASELINE_v004.json')
        for path,expected in baseline['preserved_saved_packages'].items():assert sha(C.package_file(path))==expected
        result['status']='COMPLETE_WITH_REPAIR_QUEUE' if result['failed'] else 'COMPLETE'
        write(HERE/'RESUME_RESULT_v004.json',result)
    return {'status':result['status'],'imported_saved':len(result['imported_saved']),'reused_existing':len(result['reused_existing']),
            'failed':len(result['failed']),'remaining':609-total,'last_part':result.get('last_part'),'recent_errors':[f['error'] for f in result['failed'][-3:]]}
'''
(HERE/'modular_native_adapter_v004.py').write_text(src,encoding='utf-8')
compile(src,str(HERE/'modular_native_adapter_v004.py'),'exec')
prior=json.loads((HERE.parents[1]/'ManagedSystemsAstra_2026-10-04/MODULAR_NATIVE_ACTIVATION_v002_2026-10-05.json').read_text(encoding='utf-8-sig'))
activation={'status':'MODULAR_NATIVE_RESUME_V004','utc':datetime.now(timezone.utc).isoformat(),'authorization':'Direct human request in current chat: resume only native import, reuse34, import575, per-asset repair queue, one operator',
 'operator_thread_id':os.environ['CODEX_THREAD_ID'],'assigned_editor_PID':21608,'native_authorized_now':True,'ordinary_generation_authorized':False,
 'world':prior['world'],'preservation_path':prior['preservation_path'],'request_sha256':hashlib.sha256((HERE/'NATIVE_IMPORT_REQUEST_v003.json').read_bytes()).hexdigest(),
 'adapter_sha256':hashlib.sha256((HERE/'modular_native_adapter_v004.py').read_bytes()).hexdigest()}
(HERE/'RESUME_ACTIVATION_v004.json').write_text(json.dumps(activation,indent=2)+'\n')
owner=HERE.parents[1]/'ModelBank/EDITOR_OWNER.txt'
with owner.open('a',encoding='utf-8') as f:f.write('\n'+activation['utc']+' OWNER=CODEX_BANK_INTEGRATION operator_thread_id='+activation['operator_thread_id']+' task=modular_bank assigned_editor_PID=21608 activation=MODULAR_NATIVE_RESUME_V004 scope=575remaining_native_parts_only native_authorized_now=true ordinary_generation_authorized=false\n')
print(json.dumps({'adapter':'modular_native_adapter_v004.py','activation':activation['status']}))
