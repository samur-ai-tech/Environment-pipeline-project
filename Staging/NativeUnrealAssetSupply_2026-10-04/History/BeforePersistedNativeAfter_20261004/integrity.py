"""Pure validation before any lossy indexing or native mutation."""
import hashlib
import json

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def validate_records(records):
    ids=set();names=set();paths=set()
    for r in records:
        aid=r['asset_id'];name=r['catalog_row_name'];rt=r['runtime'];path=rt['ObjectPath']
        assert aid and name and aid not in ids,'duplicate_or_empty_asset_id:'+aid
        assert name.casefold() not in names,'duplicate_row_name:'+name
        assert rt['AssetId']==aid and rt['Name']==name,'record_runtime_identity_mismatch'
        assert r.get('object_path','')==path,'record_runtime_path_mismatch:'+aid
        assert not path or path.casefold() not in paths,'duplicate_native_path:'+path
        ids.add(aid);names.add(name.casefold())
        if path:paths.add(path.casefold())
    return True

def require_held(record):
    r=record['runtime']
    assert r['RunEligible']=='false' and r['ExplicitHold']=='true'
    assert r['TechnicalPreviewEligible']=='false' and r['AnchorValid']=='false' and r['OrientationValid']=='false'
    assert r['SelectionWeight']=='0.0' and r['PreviewWeight']=='0.0'
    assert r['PlacementScope']=='none' and r['AllowedAreas']=='' and r['AllowedZones']==''
    assert r['ReleaseId']=='' and r['Role']=='' and r['RequestRole']=='' and r['PlacementRule']==''
    assert r['HoldReasons']=='native_supply_qualification_pending'
    assert record['explicit_hold'] is True and record['hold_reasons']==['native_supply_qualification_pending']
    for key in ['canonical_qualified','canonical_run_eligible','general_generation_released','technical_preview_eligible']:
        assert record[key] is False

def preserved(before,after,new_records):
    validate_records(before['rows']);validate_records(after['rows'])
    assert after['rows']==before['rows']+new_records,'existing_rows_or_addition_order_changed'
    for r in new_records:require_held(r)
    allowed={'rows','catalog_sha256','normal_use_catalog_digest','native_supply_registration_receipt'}
    assert {k:v for k,v in before.items() if k not in allowed}=={k:v for k,v in after.items() if k not in allowed},'unapproved_top_level_change'

def baseline_state(source_sha,csv_sha,native_digest,tx):
    before=(tx['catalog_source_before_sha256'],tx['catalog_csv_before_sha256'],tx['before_digest'])
    after=(tx['bundle_source_sha256'],tx['bundle_csv_sha256'],tx['after_digest'])
    current=(source_sha,csv_sha,native_digest)
    if current==before:return 'before'
    if current==after:return 'applied'
    raise AssertionError('partial_apply_or_stale_baseline_requires_reconciliation')

def applied_receipt(receipt,tx,transaction_sha,table):
    assert receipt['transaction_sha256']==transaction_sha,'applied_transaction_mismatch'
    assert receipt['decision_sha256']==tx['decision_sha256'],'applied_decision_mismatch'
    assert receipt['table']==table and receipt['rows']==tx['after_rows'],'applied_table_or_count_mismatch'
    assert receipt['digest']==tx['after_digest'],'applied_digest_mismatch'
    assert receipt['registered_held_ids']==tx['added_ids'],'applied_registered_ids_mismatch'
    assert receipt['saved'] is True and receipt['newly_eligible']==[],'applied_save_or_selection_mismatch'
    assert receipt['ordinary_generation_authorized'] is False
    assert isinstance(receipt['pid'],int) and receipt['pid']>0
    return True
