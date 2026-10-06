"""Retained bank execution under Aviv's direct 2026-10-06 authorization."""
import os, json, hashlib, time, subprocess
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
HERE = ROOT / 'Staging/AssetBankOperator_2026-10-06'
BANK = '/Game/Project/Shared/ModelBank/'
E = unreal.EditorAssetLibrary
REG = unreal.AssetRegistryHelpers.get_asset_registry()
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name, data):
    p=HERE/name; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def dirty():
    return {'content':sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
            'maps':sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())}
def preflight():
    assert os.getpid()==29900, 'Wrong editor PID'
    raw=subprocess.check_output(['powershell.exe','-NoProfile','-Command','Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],text=True,creationflags=subprocess.CREATE_NO_WINDOW)
    assert [int(x) for x in raw.split()]==[os.getpid()],'Another editor is running; no authoring'
    line=[s for s in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().splitlines() if s.strip()][-1]
    assert 'OWNER=ASSET_BANK_OPERATOR ' in line and 'assigned_editor_PID=29900 ' in line
    assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
    assert not REG.is_loading_assets()
    assert not dirty()['maps']
    return dirty()
def candidates(batch_id):
    batches=read(HERE/'EXPANDED_BATCH_MANIFEST.json')['batches']
    if (HERE/'EXECUTION_BATCHES.json').exists():batches+=read(HERE/'EXECUTION_BATCHES.json')['batches']
    b=next(x for x in batches if x['batch_id']==batch_id)
    q={r['asset_id']:r for r in read(HERE/'EXPANDED_SUPPLY_QUEUE.json')['rows']}
    rows=[dict(q[k]) for k in b['asset_ids']]
    for r in rows:r['proposed_role']=b.get('role_overrides',{}).get(r['asset_id'],r['proposed_role'])
    return rows
def closure(packages):
    opts=unreal.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True,include_game_package_references=True,include_editor_only_package_references=False)
    todo=list(packages); seen=set(); result=[]; missing=[]
    while todo:
        p=todo.pop()
        if p in seen or p.startswith('/Script/'):continue
        seen.add(p)
        data=REG.get_assets_by_package_name(p)
        if not data:
            missing.append(p);continue
        deps=[str(x) for x in (REG.get_dependencies(p,opts) or [])]
        result.append({'package':p,'classes':[str(x.asset_class_path.asset_name) for x in data],'dependencies':deps})
        todo.extend(deps)
    return {'packages':result,'missing':sorted(missing)}
def inspect_source(batch_id):
    before=preflight();rows=candidates(batch_id)
    c=closure([r['source_object_path'].split('.')[0] for r in rows])
    report={'batch_id':batch_id,'pid':os.getpid(),'closure':c,'dirty_before':before,'dirty_after':dirty(),'state':'source_registry_inspected'}
    write('Native/'+batch_id+'_SOURCE.json',report)
    assert dirty()==before
    print(json.dumps({'batch':batch_id,'packages':len(c['packages']),'missing':c['missing'],'classes':sorted(set(k for p in c['packages'] for k in p['classes']))}))

def import_mounted(batch_id, mount_root):
    before=preflight(); rows=candidates(batch_id)
    mounts=tuple(mount_root) if isinstance(mount_root,list) else (mount_root,)
    for mount in mounts:
        assert mount.startswith('/Game/') and not (ROOT/'Content'/mount[6:]).exists()
        physical=Path(unreal.Paths.convert_relative_path_to_full(unreal.PackageTools.package_name_to_filename(mount+'marker'))).parent.resolve()
        assert physical.is_relative_to(HERE/'NativeIntake'), str(physical)
    c=closure([r['source_object_path'].split('.')[0] for r in rows])
    assert not c['missing'], c['missing']
    selected={r['source_object_path'].split('.')[0]:r['target_object_path'].split('.')[0] for r in rows}
    prefix=BANK+'Supply/'+rows[0]['source_pack']+'/Dependencies/'
    mapping=[]
    for p in c['packages']:
        old=p['package']
        if old.startswith('/Engine/'):continue
        assert old.startswith(mounts), 'Off-pack dependency: '+old
        if p['classes']==['ObjectRedirector']:continue
        classes=[x for x in p['classes'] if x!='ObjectRedirector']
        assert len(classes)==1 and classes[0] in ['StaticMesh','Material','MaterialInstanceConstant','MaterialFunction','Texture2D','TextureCube','MaterialParameterCollection','SubsurfaceProfile','RuntimeVirtualTexture','MaterialFunctionMaterialLayer','MaterialFunctionMaterialLayerBlend','MaterialFunctionMaterialLayerInstance'],p
        new=selected.get(old,prefix+old[6:])
        assert new.startswith(BANK) and not E.does_asset_exist(new),new
        mapping.append({'old':old,'new':new,'class':classes[0]})
    receipt={'batch_id':batch_id,'pid':os.getpid(),'state':'loading_intake_copies','mapping':mapping,'dirty_before':before,'source_files_moved':False}
    name='Native/'+batch_id+'_IMPORT.json'
    assert not (HERE/name).exists(), 'Existing transaction requires reconciliation'
    write(name,receipt)
    objects=[]; renames=[]
    for m in mapping:
        obj=unreal.load_asset(m['old']);assert obj and obj.get_class().get_name()==m['class'],m
        objects.append(obj)
        renames.append(unreal.AssetRenameData(asset=obj,new_package_path=m['new'].rsplit('/',1)[0],new_name=m['new'].rsplit('/',1)[1]))
    new_dirty=set(dirty()['content'])-set(before['content'])
    assert all(x.startswith(mounts) for x in new_dirty),new_dirty
    receipt['state']='native_rename_started';write(name,receipt)
    assert TOOLS.rename_assets(renames),'Native rename failed; reconcile receipt before retry'
    redirect={unreal.SoftObjectPath(m['old']+'.'+m['old'].rsplit('/',1)[1]):unreal.SoftObjectPath(m['new']+'.'+m['new'].rsplit('/',1)[1]) for m in mapping}
    TOOLS.rename_referencing_soft_object_paths([x.get_outermost() for x in objects],redirect)
    for obj,m in zip(objects,mapping):assert obj.get_outermost().get_path_name()==m['new'],m
    receipt['state']='renamed_preparing_instancing_materials';write(name,receipt)
    for obj in objects:
        if isinstance(obj,unreal.Material):
            obj.set_editor_property('used_with_instanced_static_meshes',True)
            obj.set_editor_property('automatically_set_usage_in_editor',False)
            unreal.MaterialEditingLibrary.recompile_material(obj)
    extra=set(dirty()['content'])-set(before['content'])
    assert not dirty()['maps'] and all(x.startswith((BANK,)+mounts) for x in extra),dirty()
    named={obj.get_outermost().get_path_name():obj.get_outermost() for obj in objects}
    for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages():
        if p.get_path_name() in extra:named[p.get_path_name()]=p
    receipt['state']='saving_named_bank_and_intake_redirector_packages';receipt['named_packages']=sorted(named);write(name,receipt)
    assert unreal.EditorLoadingAndSavingUtils.save_packages(list(named.values()),only_dirty=False)
    REG.scan_paths_synchronous([BANK.rstrip('/')],True)
    after=closure([r['target_object_path'].split('.')[0] for r in rows])
    assert not after['missing'],after['missing']
    assert all(p['package'].startswith(('/Engine/',BANK)) for p in after['packages']), 'Source dependency retained'
    receipt.update(state='native_import_saved',imported_meshes=len(rows),saved_bank_packages=[p for p in named if p.startswith(BANK)],dependency_closure=after,dirty_after=dirty())
    write(name,receipt)
    assert dirty()==before,dirty()
    print(json.dumps({'batch':batch_id,'imported':len(rows),'bank_packages':len(receipt['saved_bank_packages']),'missing_dependencies':len(after['missing']),'dirty_restored':True}))

def validate_batch(batch_id):
    before=preflight();rows=candidates(batch_id);report=[]
    REG.scan_paths_synchronous([BANK.rstrip('/')],True)
    sub=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    for r in rows:
        v={'asset_id':r['asset_id'],'asset_path':r['target_object_path'],'source':r['source_file'],'source_sha256':r['source_sha256'],'licence':{'basis':'Aviv owner confirmation and direct full-process authorization 2026-10-06','exact_acquisition_document':'pending owner readout'},'status':'checking'}
        try:
            mesh=unreal.load_asset(r['target_object_path']);assert isinstance(mesh,unreal.StaticMesh)
            desc=mesh.get_static_mesh_description(0);assert desc
            box=mesh.get_bounding_box();lo=box.min;hi=box.max
            v.update(triangles=desc.get_triangle_count(),vertices=desc.get_vertex_count(),LODs=sub.get_lod_count(mesh),uv_channels=sub.get_num_uv_channels(mesh,0),bounds_cm={'min':[lo.x,lo.y,lo.z],'max':[hi.x,hi.y,hi.z]},collision={'simple':sub.get_simple_collision_count(mesh),'convex':sub.get_convex_collision_count(mesh)},materials=[],textures=[],native_class='StaticMesh')
            for slot in mesh.static_materials:
                mat=slot.material_interface
                v['materials'].append({'slot':str(slot.material_slot_name),'path':mat.get_path_name() if mat else None,'instancing':bool(mat and unreal.MaterialEditingLibrary.has_material_usage(mat,unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES))})
                if isinstance(mat,unreal.Material):
                    v['textures'].extend(t.get_path_name() for t in unreal.MaterialEditingLibrary.get_used_textures(mat))
                elif isinstance(mat,unreal.MaterialInstanceConstant):
                    v['textures'].extend(t.parameter_value.get_path_name() for t in mat.get_editor_property('texture_parameter_values') if t.parameter_value)
            v['textures']=sorted(set(v['textures']))
            c=closure([mesh.get_outermost().get_path_name()]);v['missing_dependencies']=c['missing']
            v['textures']=sorted(set(v['textures'])|{p['package']+'.'+p['package'].rsplit('/',1)[1] for p in c['packages'] if any(cls.startswith('Texture') for cls in p['classes'])})
            v['materials_bound']=bool(v['materials']) and all(m['path'] for m in v['materials'])
            v['textures_resolved']=not c['missing'] and all(unreal.load_asset(t) is not None for t in v['textures'])
            f=ROOT/'Content'/(mesh.get_outermost().get_path_name()[6:]+'.uasset');v['asset_revision_sha256']=hashlib.sha256(f.read_bytes()).hexdigest()
            v['named_saved']=f.is_file();v['status']='native_validated' if v['triangles']>1 and v['materials_bound'] and v['textures_resolved'] and all(m['instancing'] for m in v['materials']) else 'needs_repair'
        except Exception as exc:v.update(status='needs_repair',error=repr(exc))
        report.append(v);write('Native/'+batch_id+'_VALIDATION.json',{'batch_id':batch_id,'pid':os.getpid(),'assets':report,'complete':False})
    after=dirty();write('Native/'+batch_id+'_VALIDATION.json',{'batch_id':batch_id,'pid':os.getpid(),'assets':report,'complete':True,'dirty_before':before,'dirty_after':after})
    assert before==after,after
    print(json.dumps({'batch':batch_id,'counts':{s:sum(x['status']==s for x in report) for s in ['native_validated','needs_repair']},'errors':[{'id':x['asset_id'],'error':x.get('error')} for x in report if x['status']=='needs_repair']}))

def duplicate_current(batch_id):
    before=preflight();rows=candidates(batch_id);created={};copies={};done=[]
    def compatible(mat):
        key=mat.get_path_name()
        if key in copies:return copies[key]
        target=BANK+'Supply/Current/Materials/'+('M_' if isinstance(mat,unreal.Material) else 'MI_')+hashlib.sha256(key.encode()).hexdigest()[:20]
        copied=unreal.load_asset(target) if E.does_asset_exist(target) else E.duplicate_asset(key,target)
        assert copied;copies[key]=copied;created[target]=copied
        if isinstance(copied,unreal.Material):
            copied.set_editor_property('used_with_instanced_static_meshes',True)
            copied.set_editor_property('automatically_set_usage_in_editor',False)
            unreal.MaterialEditingLibrary.recompile_material(copied)
        elif isinstance(copied,unreal.MaterialInstanceConstant):
            copied.set_editor_property('parent',compatible(mat.get_editor_property('parent')))
            unreal.MaterialEditingLibrary.update_material_instance(copied)
        else:raise AssertionError('Unsupported material class')
        return copied
    for r in rows:
        assert not r['existing_canonical_identity'],'Reuse existing identity without automatic hold release'
        assert hashlib.sha256(Path(r['source_file']).read_bytes()).hexdigest()==r['source_sha256']
        target=r['target_object_path'].split('.')[0];assert target.startswith(BANK)
        assert not E.does_asset_exist(target),'Existing target needs reconciliation'
        src=unreal.load_asset(r['source_object_path']);assert isinstance(src,unreal.StaticMesh)
        mesh=E.duplicate_asset(src.get_path_name(),target);assert mesh;created[target]=mesh
        for i,slot in enumerate(src.static_materials):
            assert slot.material_interface
            mesh.set_material(i,compatible(slot.material_interface))
        done.append(r['asset_id'])
    extra=set(dirty()['content'])-set(before['content'])
    assert all(p.startswith(BANK) for p in extra) and not dirty()['maps'],dirty()
    for name in sorted(created):assert E.save_asset(name,only_if_is_dirty=False),name
    assert dirty()==before,dirty()
    assert all(hashlib.sha256(Path(r['source_file']).read_bytes()).hexdigest()==r['source_sha256'] for r in rows)
    write('Native/'+batch_id+'_IMPORT.json',{'batch_id':batch_id,'state':'native_import_saved','imported_meshes':len(done),'asset_ids':done,'saved_bank_packages':sorted(created),'vendor_source_hashes_unchanged':True,'dirty_before':before,'dirty_after':dirty()})
    print(json.dumps({'batch':batch_id,'imported':len(done),'bank_packages':len(created)}))

