"""Offline rejection checks. Synthetic records are never written as real receipts."""
import copy
import json
import runpy
from pathlib import Path

HERE=Path(__file__).resolve().parent
h=runpy.run_path(str(HERE/'continuation_manifest.py'))
checks=[]

def rejects(name,call):
    try:
        call()
    except (AssertionError,KeyError,ValueError,FileNotFoundError):
        checks.append(name)
    else:
        raise AssertionError('Accepted invalid case: '+name)

h['require_sole_editor']([32508],32508)
for pids in ([],[1],[32508,77]):
    rejects('sole_PID_reject_'+str(pids),lambda pids=pids:h['require_sole_editor'](pids,32508))

area={'map':'/Game/Project/Areas/Synthetic','map_sha256':'map_hash','source_sha256':'source_hash'}
prefix=area['map']+'.Synthetic:PersistentLevel.'
expected=dict(area,hda_actor_path=prefix+'HDA',actor_paths=[prefix+'Prior',prefix+'Official'],
    official_actor_paths=[prefix+'Official'],baked_actor_paths=[prefix+'Prior'])

def landscape(e=expected,actual=None,official=None,baked=None):
    h['validate_landscapes'](e,area,e['actor_paths'] if actual is None else actual,
        e['official_actor_paths'] if official is None else official,
        e['baked_actor_paths'] if baked is None else baked,prefix+'HDA')

landscape();checks.append('exact_two_landscapes_pass')
rejects('missing_prior_landscape',lambda:landscape(actual=[prefix+'Official']))
rejects('missing_official_landscape',lambda:landscape(actual=[prefix+'Prior']))
rejects('unknown_landscape',lambda:landscape(actual=expected['actor_paths']+[prefix+'Unknown']))
rejects('empty_official_result',lambda:landscape(official=[]))
rejects('wrong_official_result',lambda:landscape(official=[prefix+'Prior']))
rejects('lost_baked_ownership',lambda:landscape(baked=[]))
for key in ('source_sha256','map_sha256','hda_actor_path'):
    e=copy.deepcopy(expected);e[key]='changed'
    rejects('changed_'+key,lambda e=e:landscape(e))
e=copy.deepcopy(expected);e['actor_paths']=[prefix+'Official'];e['baked_actor_paths']=[prefix+'Official']
landscape(e);checks.append('separately_reviewed_singleton_pass')

record=h['verify']();approval={'manager_thread_id':h['MANAGER'],'release_operator_thread_id':h['BANK_OPERATOR'],
    'released_editor_pid':32508,'released_map':record['areas'][0]['map'],
    'bank_clean_handoff_receipt':str(HERE/'SYNTHETIC_NOT_WRITTEN.json'),'bank_clean_handoff_sha256':'synthetic_hash'}
baseline=h['read'](HERE.parent/'DISK_RECONCILIATION.json')
candidates={r['file']:r['sha256'] for a in baseline['areas'] for r in a['preserved_candidate_disk_checks']}
vendor={name:h['sha'](h['ROOT']/name) for name in (
    'Content/Palms_Pack_01/Add_Props/Plants/Materials/MI_Plant_07_6_Leaves_G.uasset',
    'Content/Palms_Pack_01/Add_Props/Plants/Materials/MI_Plant_07_6_Stem_G.uasset',
    'Content/Palms_Pack_01/Add_Props/Plants/Meshes/SM_Plant_07_6_G.uasset')}
receipt={'schema':'environmentpipeline.clean_editor_release.v1','manager_thread_id':h['MANAGER'],
    'operator_thread_id':h['BANK_OPERATOR'],'released_editor_pid':32508,'map':approval['released_map'],
    'process_exited':True,'clean_handoff':True,'cooking_paused_before_exit':True,'no_shutdown_saves':True,
    'auto_cook_before_exit':False,'auto_bake_before_exit':False,'callbacks_before_exit':0,
    'dirty_maps_before_exit':[],'dirty_content_before_exit':[],
    'catalog_digest':record['catalog']['typed_source_digest'],
    'preserved_original_maps':{a['map']:a['map_sha256'] for a in record['areas']},
    'preserved_candidates':candidates,'preserved_vendor_originals':vendor,'named_saved_packages':{}}
lease=' '.join(k+'='+str(v) for k,v in {'OWNER':'NONE','manager_thread_id':h['MANAGER'],
    'operator_thread_id':h['BANK_OPERATOR'],'released_editor_PID':32508,'map':approval['released_map'],
    'clean_handoff':'true','process_exited':'true',
    'release_receipt':Path(approval['bank_clean_handoff_receipt']).relative_to(h['ROOT']).as_posix(),
    'release_receipt_sha256':'synthetic_hash'}.items())
validate=h['validate_release_data']
validate(receipt,approval,record,lease);checks.append('synthetic_complete_release_contract_pass_NO_REAL_RELEASE_ASSERTED')
for key,value in [('released_editor_pid',1),('map','/Game/Wrong'),('clean_handoff',False),
    ('dirty_content_before_exit',['/Game/Vendor']),('catalog_digest','old'),('preserved_candidates',{}),
    ('preserved_vendor_originals',{}),('named_saved_packages',{'Content/Vendor.uasset':'hash'})]:
    bad=copy.deepcopy(receipt);bad[key]=value
    rejects('release_reject_'+key,lambda bad=bad:validate(bad,approval,record,lease))
rejects('lease_receipt_hash_mismatch',lambda:validate(receipt,approval,record,lease.replace('synthetic_hash','other')))
rejects('lease_not_released',lambda:validate(receipt,approval,record,lease.replace('OWNER=NONE','OWNER=CODEX_BANK_INTEGRATION')))
rejects('missing_actual_receipt',lambda:h['checked_receipt'](approval['bank_clean_handoff_receipt'],'hash'))

namespace=h['current_authority'].__globals__;original_read=namespace['read']
for mode in ('transfer','operator'):
    def altered(path, mode=mode):
        value=copy.deepcopy(original_read(path))
        if Path(path)==h['TRANSFER'] and mode=='transfer':value['status']='NOT_TRANSFERRED'
        if Path(path)==h['ASSIGNMENTS'] and mode=='operator':
            next(t for t in value['tasks'] if t['id']=='task4')['thread_id']='different_operator'
        return value
    namespace['read']=altered
    try:rejects('authority_reject_'+mode,h['current_authority'])
    finally:namespace['read']=original_read

print(json.dumps({'passed':True,'checks':checks,'native_calls':0,'real_release_asserted':False},indent=2))
