"""Retain preparation pointers and measured descriptive fields in the canonical source.
No runtime row, native table, release decision, profile or system source is changed.
"""
import pathlib,json,hashlib,copy
from datetime import datetime,timezone
OUT=pathlib.Path(__file__).resolve().parent
patch=json.loads((OUT/'CATALOG_METADATA_PATCH.json').read_text())
target=pathlib.Path(patch['target']);before=target.read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(before)==patch['target_sha256'],'canonical_source_changed_since_preparation'
catalog=json.loads(before.decode('utf-8-sig'));original=copy.deepcopy(catalog)
by_id={r['asset_id']:r for r in catalog['rows']};runtime=[r['runtime'] for r in catalog['rows']]
backup=OUT/'CATALOG_BEFORE_METADATA.json'
assert not backup.exists(),'metadata_apply_already_started_review_receipt'
backup.write_bytes(before)
changed=[]
for item in patch['patches']:
    r=by_id[item['asset_id']];p=item['bank_preparation']
    assert r['catalog_row_name']==item['catalog_row_name']
    r['bank_preparation']={'schema':'environmentpipeline.bank_preparation.v1','date':'2026-10-04',
        'registry':str(OUT/'PREPARED_BANK.json'),'asset_id':r['asset_id'],
        'status':p['phase_status'],'native_load_measured_this_run':p.get('native_load_verified_this_run',False),
        'native_bounds_cm_measured':p.get('bounds_native_cm_measured'),
        'native_material_slots_measured':p.get('native_measurement',{}).get('material_slots'),
        'prepared_blend':(p.get('prepared_source') or {}).get('blend'),
        'prepared_source_dimensions_m':(p.get('prepared_source') or {}).get('dimensions_m'),
        'required_consumer_context':p['required_consumer_context'],'blockers':p['blockers'],
        'runtime_enablement_changed':False,'canonical_rights_or_qualification_changed':False}
    changed.append(r['asset_id'])
catalog['bank_preparation_registry']={'path':str(OUT/'PREPARED_BANK.json'),'metadata_asset_ids':changed,
    'phase':'nonmodular_measurement_and_source_preparation','native_runtime_changes':False}
assert runtime==[r['runtime'] for r in catalog['rows']]
check=copy.deepcopy(catalog);check.pop('bank_preparation_registry')
for r in check['rows']:r.pop('bank_preparation',None)
assert check==original,'unexpected_change_outside_preparation_fields'
after=(json.dumps(catalog,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
target.write_bytes(after)
receipt={'recorded_utc':datetime.now(timezone.utc).isoformat(),'target':str(target),'before_sha256':sha(before),'after_sha256':sha(after),
    'backup':str(backup),'records_annotated':len(changed),'all_runtime_rows_identical':True,'native_table_unchanged':True,
    'catalog_release_digest_unchanged':True,'profiles_and_system_source_unchanged':True,'native_imported_or_enabled':False}
(OUT/'CATALOG_METADATA_APPLIED.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
