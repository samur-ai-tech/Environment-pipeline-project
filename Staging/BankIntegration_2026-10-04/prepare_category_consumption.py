"""File-only combined category command closure and exact configuration proposal."""
import csv
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bank_contracts as C


def prepare():
    assignment=C.read(HERE/'CategoryBatches/ASSIGNMENT.json')
    catalog=C.read(C.SOURCE)
    with C.CSV.open(encoding='utf-8-sig',newline='') as f:csv_rows=list(csv.DictReader(f))
    assert C.typed_rows(csv_rows)==C.typed_rows([r['runtime'] for r in catalog['rows']])
    source_paths=list(HERE.glob('*.py'))+list((HERE/'CategoryBatches').rglob('*.py'))
    python_sources={str(p.resolve()):C.sha(p) for p in sorted(source_paths)}
    payloads={};file_pins={};issues=[];categories={}
    configs=C.read(HERE/'NATIVE_CONFIGURATIONS.json')
    existing={r['asset_id']:r for r in configs['rows']}
    proposal={'before_sha256':C.sha(HERE/'NATIVE_CONFIGURATIONS.json'),'insertions':[],'existing_exact':[],'existing_differences':[],'native_operations':False}
    canonical={r['asset_id']:r for r in catalog['rows']}
    config_files={'Props':None,'Vegetation':'NATIVE_CONFIGURATIONS.payload.json','WholeBuildings':'NATIVE_CONFIGURATIONS.json'}
    for category in assignment['categories']:
        folder=HERE/'CategoryBatches'/category
        jobs_path=folder/'READY_JOBS.json';handoff_path=folder/'HANDOFF.json'
        jobs=C.read(jobs_path);handoff=C.read(handoff_path)
        categories[category]={'jobs':str(jobs_path),'jobs_sha256':C.sha(jobs_path),'handoff':str(handoff_path),'handoff_sha256':C.sha(handoff_path),
            'status':handoff['status'],'counts':handoff.get('counts',handoff.get('action_counts',{}))}
        for p in folder.glob('*.json'):
            if p.name!='EXECUTION_MANIFEST.json':payloads[str(p.resolve())]=C.sha(p)
        local_manifest=folder/'EXECUTION_MANIFEST.json'
        if local_manifest.exists():
            pin=C.read(local_manifest)
            for section,target in (('files',file_pins),('payloads',payloads)):
                for path,expected in pin.get(section,{}).items():
                    actual=C.sha(path)
                    if actual!=expected: issues.append({'category':category,'path':path,'issue':'category_pin_stale','expected':expected,'actual':actual})
                    if path in target and target[path]!=expected:issues.append({'category':category,'path':path,'issue':'conflicting_category_pins'})
                    target[path]=expected
            categories[category]['execution_manifest']=str(local_manifest)
            categories[category]['execution_manifest_sha256']=C.sha(local_manifest)
        cfg_file=config_files[category]
        if cfg_file:
            data=C.read(folder/cfg_file);rows=data['rows'] if isinstance(data,dict) else data
            for row in rows:
                aid=row['asset_id'];assert aid in canonical,('unknown_category_identity',aid)
                assert row['object_path']==canonical[aid]['runtime']['ObjectPath'],('category_native_path_differs',aid)
                assert C.sha(C.package_file(row['object_path']))==row['package_sha256'],('category_source_changed',aid)
                if aid not in existing:proposal['insertions'].append(row)
                elif existing[aid]==row:proposal['existing_exact'].append(aid)
                else:proposal['existing_differences'].append({'asset_id':aid,'category':category,'differences':{k:{'existing':existing[aid].get(k),'category':row.get(k)} for k in existing[aid].keys()|row.keys() if existing[aid].get(k)!=row.get(k)}})
    merged_files=dict(file_pins)
    for p,s in python_sources.items():
        if p in merged_files and merged_files[p]!=s:issues.append({'path':p,'issue':'category_helper_pin_stale'})
        merged_files[p]=s
    command_specs=[('props_finalize','Props','props_category_batch','integrate_reviewed'),
        ('vegetation_material_diagnostics','Vegetation','vegetation_category_batch','collect_material_diagnostics'),
        ('vegetation_repair','Vegetation','vegetation_category_batch','apply_reviewed_foliage_repairs'),
        ('vegetation_speedtree_import','Vegetation','vegetation_category_batch','import_speedtree'),
        ('vegetation_original_lods','Vegetation','vegetation_category_batch','append_original_lods'),
        ('whole_building_import','WholeBuildings','category_batch','execute_native')]
    commands={name:{'path':str(HERE/'CategoryBatches'/cat/'category_batch.py'),'module_name':module,'function':fn} for name,cat,module,fn in command_specs}
    commands.update({'catalog_apply':{'path':str(HERE/'apply_bank_configuration.py'),'module_name':'apply_bank_configuration','function':'apply'}})
    result={'schema':'environmentpipeline.combined_category_execution.v1','manager_thread':assignment['system_manager_thread'],
        'status':'PREPARED_REVIEW_AND_NATIVE_ACTIVATION_REQUIRED','python_sources':python_sources,'payload_files':payloads,
        'files':merged_files,'payloads':payloads,'commands':commands,'categories':categories,'pin_issues':issues,
        'baseline':{'catalog_rows':len(catalog['rows']),'catalog_digest':C.digest(csv_rows),'source_sha256':C.sha(C.SOURCE),'csv_sha256':C.sha(C.CSV)},
        'no_native_execution':True,'no_catalog_change':True,
        'execution_order':['Resolve only concrete category pin/config conflicts; freeze exact combined manifest with manager.',
            'Preserve dirty originals; reviewed clean fresh startup and successor bank activation before native work.',
            'Merge approved exact configuration/material/import payloads by canonical ID, keeping existing readiness and all holds.',
            'Finalize retained supported ordinary prop reviews, prepare remaining regular native materials/contacts in groups, and import category prepared sources.',
            'Build/apply existing canonical transaction with typed source/CSV/native identity and profile-hash CAS; submit exact manager profile patch.',
            'Publish GENERATION_READINESS with exact digests/roles/holds/dirty state for original-area normal output/save/reopen.'],
        'cache_rule':'Reject stale loaded helpers, path aliases and changed module identities; no hot reload. Complete category/module source pins supplement the existing12-module system guard.'}
    if issues:result['status']='CATEGORY_PIN_REFRESH_REQUIRED_BEFORE_REVIEW'
    C.write(HERE/'CATEGORY_CONFIGURATION_MERGE_PROPOSAL.json',proposal)
    C.write(HERE/'CATEGORY_CONSUMPTION_REQUEST.json',result)
    digest=C.sha(HERE/'CATEGORY_CONSUMPTION_REQUEST.json')
    frozen=HERE/('CATEGORY_CONSUMPTION_'+digest[:16]+'.json')
    if frozen.exists():assert C.read(frozen)==result
    else:C.write(frozen,result)
    print(json.dumps({'manifest':str(frozen),'sha256':digest,'python_sources':len(python_sources),'payload_files':len(payloads),'pin_issues':issues,'new_configurations':len(proposal['insertions']),'configuration_differences':len(proposal['existing_differences'])}))


if __name__=='__main__':prepare()
