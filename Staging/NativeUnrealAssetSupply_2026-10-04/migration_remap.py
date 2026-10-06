"""Supported native Migrate -> RenameAssets -> soft-reference fixup.

Only newly migrated target copies are renamed. External project originals and
pre-existing target assets cannot enter the rename list. No raw file rename,
overwrite, redirector deletion, sample maps or generator import is performed.
"""
from pathlib import Path
import os
import re
from . import intake as I
from . import authority as A
from . import integrity as V

SUFFIXES=('.uasset','.uexp','.ubulk','.uptnl','.umap')

def package_file(package):
    assert re.fullmatch(r'/Game/[A-Za-z0-9_/]+',package),'invalid_package_name'
    return I.ROOT/'Content'/(package[6:]+'.uasset')

def assert_unoccupied(p):
    for item in p['mapping']:
        for package in (item['original_package'],item['target_package']):
            base=package_file(package)
            assert not any(base.with_suffix(e).exists() for e in SUFFIXES),'preexisting_target_collision:'+package

def verify_source_files(p):
    c=I.read(p['closure_path'])
    for package in c['packages']:
        for f in package['files']:assert I.sha(f['file'])==f['sha256'],'source_or_engine_dependency_changed'

def plan(closure_path):
    m,mp=A.manifest();c=I.read(closure_path)
    assert c['native_measured'] is True and c['authority']==m['authority']
    assert c['queue_sha256']==m['queue_sha256'] and c['command_manifest_sha256']==I.sha(mp)
    sid=c['source_id'];assert re.fullmatch(r'[A-Za-z0-9_]+',sid)
    prefix='/Game/Project/Shared/ModelBank/Prepared/NativeUnreal/'+sid
    mapping=[]
    for r in c['packages']:
        if r['package'].startswith('/Engine/'):continue
        assert r['package'].startswith('/Game/') and not r['package'].startswith('/Game/Project/')
        target=prefix+'/'+r['package'][6:]
        mapping.append({'original_package':r['package'],'original_object':r['object_path'],
            'target_package':target,'target_object':target+'.'+r['object_path'].rsplit('.',1)[1],'class':r['class']})
    assert mapping and len(mapping)==len({r['original_package'].casefold() for r in mapping})==len({r['target_package'].casefold() for r in mapping})
    jobs={j['job_id']:j for j in I.read(I.HERE/'READY_JOBS.json')['jobs']}
    roots=[jobs[j]['source_object_path'].split('.')[0] for j in c['job_ids']]
    p={'schema':'environmentpipeline.native_migration_remap_plan.v1','authority':m['authority'],
       'command_manifest_path':str(mp),'command_manifest_sha256':I.sha(mp),'source_id':sid,'source_project':c['source_project'],
       'closure_path':str(Path(closure_path).resolve()),'closure_sha256':I.sha(closure_path),
       'target_project':str(I.ROOT),'target_prefix':prefix,'job_ids':c['job_ids'],'root_packages':roots,'mapping':mapping,
       'temporary_namespace_permission_required':True,'redirector_policy':'Retain and name-save only exact newly created redirector packages; no cleanup or source deletion.',
       'source_write_authorized':False,'native_run':False}
    assert_unoccupied(p);verify_source_files(p)
    dest=I.HERE/'MigrationPlans'/V.digest(p)/'PLAN.json';A.immutable_json(dest,p)
    return {'path':str(dest),'sha256':I.sha(dest)}

def validate_plan(path):
    path=Path(path).resolve();assert path.is_relative_to(I.HERE/'MigrationPlans')
    p=I.read(path);m,mp=A.manifest(p['command_manifest_path'])
    assert V.digest(p)==path.parent.name
    assert I.sha(mp)==p['command_manifest_sha256'] and p['authority']==m['authority']
    assert I.sha(p['closure_path'])==p['closure_sha256']
    expected='/Game/Project/Shared/ModelBank/Prepared/NativeUnreal/'+p['source_id']
    assert p['target_prefix']==expected and Path(p['target_project']).resolve()==I.ROOT
    for item in p['mapping']:
        assert item['target_package']==expected+'/'+item['original_package'][6:]
        package_file(item['original_package']);package_file(item['target_package'])
    verify_source_files(p)
    return p

def remap(plan_path,activation_path):
    import unreal
    from . import native_supplier as N
    p=validate_plan(plan_path);act=I.read(activation_path)
    _,mp,fields=A.lease('remap_exact_migrated_native_packages',act,p['command_manifest_path'])
    assert fields['OWNER']=='CODEX_BANK_INTEGRATION'
    assert act['plan_sha256']==I.sha(plan_path) and act['allow_exact_intermediate_namespace'] is True
    originals={x['original_package'] for x in p['mapping']};targets={x['target_package'] for x in p['mapping']}
    assert set(act['intermediate_packages'])==originals and set(act['prepared_packages'])==targets
    assert set(act['allowed_redirector_packages'])==originals
    C,B=N.bank_modules(mp);state=B.preflight()
    assert not state['dirty']['content'] and not state['dirty']['maps'],'remap_requires_clean_native_boundary'
    folder=Path(plan_path).parent;done=folder/'REMAPPED.json'
    if done.exists():
        result=I.read(done)
        assert result['plan_sha256']==I.sha(plan_path)
        for f in result['saved_files']:assert I.sha(f['file'])==f['sha256'],'completed_remap_changed'
        return result
    assert not (folder/'REMAP_STARTED.json').exists(),'partial_remap_requires_reconciliation'
    migrated=I.read(folder/'MIGRATED.json');assert migrated['plan_sha256']==I.sha(plan_path)
    assert act['migration_receipt_sha256']==I.sha(folder/'MIGRATED.json'),'migration_receipt_not_reviewed'
    for f in migrated['target_files']:assert I.sha(f['file'])==f['sha256'],'migrated_copy_changed'
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    assert not registry.is_loading_assets(),'target_registry_not_ready'
    registry.scan_files_synchronous([str(package_file(x)) for x in originals],True)
    E=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools()
    assets=[];renames=[]
    for item in p['mapping']:
        assert not E.does_asset_exist(item['target_object']) and not package_file(item['target_package']).exists()
        refs=set(E.find_package_referencers_for_asset(item['original_object'],load_assets_to_confirm=False))
        assert refs.issubset(originals),'external_referencer_to_imported_package:'+str(refs-originals)
        asset=unreal.load_asset(item['original_object'])
        assert asset and asset.get_path_name()==item['original_object'] and asset.get_class().get_name()==item['class']
        closure=B.dependency_closure(item['original_package'])
        assert not closure['missing']
        assert all(x.startswith('/Engine/') or x in originals for x in closure['packages']),'unexpected_target_dependency'
        assets.append(asset)
        renames.append(unreal.AssetRenameData(asset=asset,new_package_path=item['target_package'].rsplit('/',1)[0],new_name=item['target_package'].rsplit('/',1)[1]))
    assert B.dirty()==state['dirty'],'load_dirtied_import_or_vendor_package_before_rename'
    A.immutable_json(folder/'REMAP_STARTED.json',{'pid':os.getpid(),'plan_sha256':I.sha(plan_path),'originals':sorted(originals),'targets':sorted(targets)})
    assert tools.rename_assets(renames),'native_rename_failed_stop_for_reconciliation'
    softmap={unreal.SoftObjectPath(x['original_object']):unreal.SoftObjectPath(x['target_object']) for x in p['mapping']}
    for a,x in zip(assets,p['mapping']):assert a.get_path_name()==x['target_object']
    tools.rename_referencing_soft_object_paths([a.get_outermost() for a in assets],softmap)
    # Save only explicit prepared packages plus redirector packages created by this transaction.
    dirty=unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert {x.get_path_name() for x in dirty}.issubset(originals|targets),'unexpected_dirty_package_after_rename'
    named={a.get_outermost().get_path_name():a.get_outermost() for a in assets}
    named.update({x.get_path_name():x for x in dirty})
    assert set(named).issubset(originals|targets)
    assert unreal.EditorLoadingAndSavingUtils.save_packages(list(named.values()),only_dirty=False),'named_package_save_failed'
    registry.scan_files_synchronous([str(package_file(x)) for x in targets],True)
    for original in originals:
        remaining=registry.get_assets_by_package_name(original)
        assert all(str(a.asset_class_path.asset_name)=='ObjectRedirector' for a in remaining),'original_namespace_retains_nonredirector_payload'
    closures={}
    for x in p['mapping']:
        closure=B.dependency_closure(x['target_package']);assert not closure['missing']
        assert all(dep.startswith('/Engine/') or dep in targets for dep in closure['packages']),'unremapped_dependency_retained'
        closures[x['target_object']]=closure
    verify_source_files(p)
    assert B.dirty()==state['dirty'],'dirty_state_not_restored'
    saved=[]
    for package in sorted(originals|targets):
        base=package_file(package)
        for ext in SUFFIXES:
            f=base.with_suffix(ext)
            if f.exists():saved.append({'file':str(f),'sha256':I.sha(f),'bytes':f.stat().st_size})
    result={'plan_sha256':I.sha(plan_path),'pid':os.getpid(),'source_originals_unchanged':True,'namespace_remap_completed':True,
        'prepared_targets':sorted(targets),'dependency_closures':closures,'saved_files':saved,
        'retained_redirector_packages':[x for x in sorted(originals) if package_file(x).exists()],
        'native_measurement_and_material_review_pending':True,'registration_applied':False,'selection_eligible':False,
        'reopened':False,'regenerated':False,'no_source_project_writes':True}
    A.immutable_json(done,result)
    return result
