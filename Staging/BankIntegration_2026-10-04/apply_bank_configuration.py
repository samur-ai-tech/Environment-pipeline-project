"""Build/apply a reviewed catalog transaction; never rewrite another owner's profiles."""
import argparse
import collections
import copy
import csv
import io
import json
import os
import shutil
import bank_contracts as C

PROFILES=[C.BANK/'AREA_PROFILE.json',C.ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json']

def assert_catalog_identity(source,rows):
    """Allow reviewed catalog growth without dropping or duplicating identities."""
    records=source['rows']
    assert records and len(rows)==len(records),'catalog_row_count_mismatch'
    ids=[r['asset_id'] for r in records]
    names=[r['catalog_row_name'] for r in records]
    csv_names=[r['Name'] for r in rows]
    assert all(ids) and len(set(ids))==len(ids),'duplicate_or_empty_asset_id'
    assert all(names) and len(set(names))==len(names),'duplicate_or_empty_catalog_row_name'
    assert len(set(csv_names))==len(csv_names) and set(csv_names)==set(names),'csv_row_identity_mismatch'
    assert all(r['runtime']['Name']==r['catalog_row_name'] for r in records),'runtime_row_identity_mismatch'
    assert C.typed_rows(rows)==C.typed_rows([r['runtime'] for r in records]),'typed_source_csv_mismatch'
    return sorted(zip(ids,names))


def build():
    source=C.read(C.SOURCE);before=copy.deepcopy(source)
    with C.CSV.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);fields=list(reader.fieldnames);rows=list(reader)
    before_identities=assert_catalog_identity(source,rows)
    assert sorted((r['Name'],r) for r in rows)==sorted((r['catalog_row_name'],r['runtime']) for r in source['rows'])
    records={r['asset_id']:r for r in source['rows']};by_name={r['Name']:r for r in rows}
    validation=C.read(C.HERE/'NATIVE_VALIDATION.json')
    material_path=C.HERE/'NATIVE_INSTANCE_MATERIALS.json'
    materials=C.read(material_path) if material_path.exists() else {'mesh_slots':{}}
    enabled=[];connected=[];changed_ids=set()
    receipt_path=C.HERE/'NORMAL_CONFIGURATION.json'
    for job in C.read(C.HERE/'NATIVE_CONFIGURATIONS.json')['rows']:
        aid=job['asset_id'];v=validation.get(aid,{})
        if not v.get('ready'):continue
        assert job.get('automatic_ground_activation_allowed',True),('missing_role_specific_consumer',aid)
        assert v.get('contact_reviewed') and v.get('facing_reviewed') and v.get('material_reviewed'),aid
        assert v['source_sha256']==job['package_sha256']==C.sha(C.package_file(job['object_path'])),aid
        record=records[aid];rt=record['runtime']
        assert not C.yes(rt['ExplicitHold']) and not rt['HoldReasons'] and not record['hold_reasons']
        assert not any(h in aid for h in C.NAMED_HOLDS)
        if C.yes(rt['RunEligible']):
            assert rt['DecisionId']==C.DECISION and record.get('normal_use_configuration',{}).get('eligible'),('already_enabled_outside_this_transaction',aid)
            continue
        slots=materials['mesh_slots'][job['object_path']]
        assert len(slots)==len(job['material_slots']) and all(C.package_file(s).is_file() for s in slots)
        update={'Role':job['role'],'RequestRole':job['role'],'PlacementRule':job['placement_rule'],
            'RunEligible':'true','BoundsValid':'true','AnchorValid':'true','AnchorZCm':str(v.get('anchor_z_cm',job['anchor_z_cm'])),
            'OrientationValid':'true','ForwardAxis':v.get('forward_axis',job['forward_axis']),
            'StyleSet':job['style_context'],'SelectionWeight':'1.0','PlacementScope':'area_zone',
            'AllowedAreas':'|'.join(C.AREAS),'AllowedZones':job['allowed_zones'],'AllowedPlacementIds':'',
            'ReleaseId':source['normal_use_release_id'],'DecisionId':C.DECISION,'MinSpacingCm':str(job['min_spacing_cm'])}
        for axis,lo,hi in zip('XYZ',job['bounds_cm']['min'],job['bounds_cm']['max']):
            update['BoundsMin'+axis+'Cm']=str(lo);update['BoundsMax'+axis+'Cm']=str(hi)
        rt.update(update);by_name[rt['Name']].update(rt)
        record['normal_use_configuration']={'eligible':True,'areas':C.AREAS,'decision_id':C.DECISION,
            'decision_receipt':str(receipt_path),'native_scale':[1,1,1],
            'contact':job['contact_kind'],'review_receipt':str(C.HERE/'NATIVE_VALIDATION.json'),
            'instance_material_slots':slots,'source_style_set_preserved':record['environment_style_set'],
            'rights_state_preserved':record['recorded_rights_state'],'canonical_qualification_unchanged':True,
            'visual_acceptance':'pending_Aviv_actual_area_review'}
        source['instance_materials'][job['object_path']]=slots
        enabled.append(aid);changed_ids.add(aid)
    for path in sorted(C.HERE.glob('IMPORTED_external_*.json')):
        imp=C.read(path)
        if not imp.get('saved'):continue
        aid=imp['asset_id'];record=records[aid];rt=record['runtime']
        assert C.sha(C.package_file(imp['native_path']))==imp['native_sha256']
        if rt['ObjectPath']:
            assert (rt['ObjectPath']==imp['native_path'] and rt['AssetRevision']==imp['native_sha256']
                and record.get('native_bank_integration',{}).get('imported_and_saved')),('preexisting_native_reference_differs',aid)
            continue
        assert not C.yes(rt['RunEligible']),aid
        rt['ObjectPath']=imp['native_path'];rt['AssetRevision']=imp['native_sha256']
        rt['BoundsValid']='true'
        for axis,lo,hi in zip('XYZ',imp['measurement']['bounds_cm']['min'],imp['measurement']['bounds_cm']['max']):
            rt['BoundsMin'+axis+'Cm']=str(lo);rt['BoundsMax'+axis+'Cm']=str(hi)
        record['object_path']=imp['native_path'];record['asset_revision_sha256']=imp['native_sha256']
        record['recorded_native_class']='StaticMesh'
        record['native_bank_integration']={'receipt':str(path),'imported_and_saved':True,
            'native_path':imp['native_path'],'source_identity_preserved':True,'existing_hold_preserved':rt['ExplicitHold'],
            'normal_use_enabled':False,'reason':'existing_explicit_hold_preserved','material_slots':imp['native_material_slots']}
        by_name[rt['Name']].update(rt);connected.append(aid);changed_ids.add(aid)
    assert enabled or connected,'no_completed_native_activation_or_saved_import_to_connect'
    # One total budget per role/style/context family after actual normal eligibility.
    families=collections.defaultdict(list)
    for record in source['rows']:
        r=record['runtime']
        if enabled and C.yes(r['RunEligible']) and r['RequestRole'] in C.RULES:
            assert not C.yes(r['ExplicitHold']) and not r['HoldReasons']
            key=tuple(r[k] for k in ['RequestRole','StyleSet','AllowedAreas','AllowedZones','FamilyId'])
            families[key].append(record)
    budgets=[]
    for key,members in sorted(families.items()):
        weight=1.0/len(members)
        for record in members:
            rt=record['runtime'];old=rt['SelectionWeight'];rt['SelectionWeight']=repr(weight)
            by_name[rt['Name']]['SelectionWeight']=rt['SelectionWeight']
            if old!=rt['SelectionWeight']:changed_ids.add(record['asset_id'])
        budgets.append({'role':key[0],'style':key[1],'areas':key[2],'zones':key[3],'family_id':key[4],
            'total_weight':1.0,'member_weight':weight,'enabled_members':[r['asset_id'] for r in members]})
    assert len({r['ObjectPath'] for r in rows if r['ObjectPath']})==sum(bool(r['ObjectPath']) for r in rows)
    assert assert_catalog_identity(source,rows)==before_identities,'configuration_transaction_changed_identities'
    after_digest=C.digest(rows)
    # Immutable decision receipts keep previously applied profile hashes valid.
    receipt_path=C.HERE/('NORMAL_CONFIGURATION_'+after_digest[:16]+'.json')
    for aid in enabled:
        records[aid]['normal_use_configuration']['decision_receipt']=str(receipt_path)
    source['revision']='2026-10-04.normal.nonmodular_integration.v001'
    source['catalog_sha256']=source['normal_use_catalog_digest']=after_digest
    source['bank_integration_receipt']=str(receipt_path)
    # Every pre-existing hold, identity and rights/qualification field must remain exact.
    for old,new in zip(before['rows'],source['rows']):
        assert old['asset_id']==new['asset_id'] and old['catalog_row_name']==new['catalog_row_name']
        for key in ['canonical_qualified','canonical_run_eligible','general_generation_released','recorded_rights_state','review_hold','explicit_hold','hold_reasons','environment_style_set','style_evidence']:
            assert old.get(key)==new.get(key),(new['asset_id'],key)
        for key in ['ExplicitHold','HoldReasons']:
            assert old['runtime'][key]==new['runtime'][key],(new['asset_id'],key)
        if C.yes(old['runtime']['ExplicitHold']):assert not C.yes(new['runtime']['RunEligible'])
        if new['asset_id'] not in changed_ids:assert old==new,new['asset_id']
    receipt={'schema':'environmentpipeline.scoped_nonmodular_activation.v1','status':'reviewed_bundle_native_apply_pending',
        'decision_id':C.DECISION,'authorization':'Direct Aviv 2026-10-04 retained bank integration instruction; no rights or final art acceptance inferred.',
        'areas':C.AREAS,'release_id':source['normal_use_release_id'],'native_enabled_asset_ids':enabled,
        'imported_catalog_connected_held_ids':connected,'before_digest':C.digest([r['runtime'] for r in before['rows']]),'after_digest':after_digest,
        'rows':len(rows),'catalog_identities':before_identities,'enabled_before':sum(C.yes(r['runtime']['RunEligible']) for r in before['rows']),
        'enabled_after':sum(C.yes(r['RunEligible']) for r in rows),'family_budgets':budgets,
        'runtime_changes':{r['asset_id']:{k:{'before':o['runtime'][k],'after':v} for k,v in r['runtime'].items() if o['runtime'][k]!=v} for o,r in zip(before['rows'],source['rows']) if o['runtime']!=r['runtime']},
        'catalog_source_before_sha256':C.sha(C.SOURCE),'catalog_csv_before_sha256':C.sha(C.CSV),
        'held_flags_and_rights_unchanged':True,'native_table_saved':False,'areas_regenerated':False}
    if receipt_path.exists():
        assert C.read(receipt_path)==receipt,'immutable_decision_receipt_collision'
    else:
        C.write(receipt_path,receipt)
    C.write(C.HERE/'NORMAL_CONFIGURATION.json',receipt)
    bundle=C.HERE/'ApplyBundle';bundle.mkdir(exist_ok=True)
    C.write(bundle/'catalog_v4_source.json',source)
    with (bundle/'catalog_v4_full.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    C.write(C.HERE/'PROFILE_BANK_FIELD_PATCH.json',{
        'system_owner':C.read(C.HERE/'ASSIGNMENT.json')['system_owner'],'apply_only_after_coordinated_ownership_transfer':True,
        'profiles':[str(p) for p in PROFILES],'require_previous_catalog_digest':receipt['before_digest'],
        'profile_before_sha256':{str(p):C.sha(p) for p in PROFILES},
        'set':{'catalog_sha256':after_digest,'release.catalog_sha256':after_digest,'release.decision_receipt':str(receipt_path),
            'release.decision_sha256':C.sha(receipt_path),'normal_asset_policy.bank_integration_receipt':str(receipt_path)},
        'merge_instance_materials':{records[a]['object_path']:source['instance_materials'][records[a]['object_path']] for a in enabled},
        'preserve_every_other_profile_field':True})
    print(json.dumps({'prepared_enabled_candidates':len(enabled),'imported_held_connections':len(connected),'total_enabled_after':receipt['enabled_after'],'after_digest':after_digest}))
    return receipt

def apply():
    import native_bank_ops as N
    import unreal
    N.preflight()
    receipt=C.read(C.HERE/'NORMAL_CONFIGURATION.json')
    assert C.sha(C.SOURCE)==receipt['catalog_source_before_sha256'] and C.sha(C.CSV)==receipt['catalog_csv_before_sha256'],'catalog_changed_since_review'
    source=C.read(C.SOURCE)
    with C.CSV.open(encoding='utf-8-sig',newline='') as f: csv_rows=list(csv.DictReader(f))
    identities=assert_catalog_identity(source,csv_rows)
    assert identities==[tuple(p) for p in receipt['catalog_identities']] and len(csv_rows)==receipt['rows'],'catalog_identity_changed_since_review'
    patch=C.read(C.HERE/'PROFILE_BANK_FIELD_PATCH.json')
    assert patch['require_previous_catalog_digest']==receipt['before_digest'] and patch['set']['catalog_sha256']==receipt['after_digest']
    assert all(C.sha(p)==expected for p,expected in patch['profile_before_sha256'].items()),'profile_changed_since_review'
    table_path='/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4';table=unreal.load_asset(table_path)
    prior=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
    assert C.digest(prior)==receipt['before_digest'],'native_table_not_expected_baseline'
    assert len(prior)==receipt['rows'] and C.typed_rows(prior)==C.typed_rows(csv_rows),'native_source_csv_typed_agreement_failed'
    backup=C.HERE/'Before';backup.mkdir(exist_ok=True)
    for path in [C.SOURCE,C.CSV]:
        dest=backup/path.name
        if not dest.exists():shutil.copy2(path,dest)
    if not (backup/'NATIVE_TABLE.json').exists():C.write(backup/'NATIVE_TABLE.json',prior)
    C.write(backup/('NATIVE_TABLE_'+receipt['before_digest'][:16]+'.json'),prior)
    bundle=C.HERE/'ApplyBundle';expected=C.read(bundle/'catalog_v4_source.json')
    with (bundle/'catalog_v4_full.csv').open(encoding='utf-8-sig',newline='') as f: bundle_rows=list(csv.DictReader(f))
    assert assert_catalog_identity(expected,bundle_rows)==identities,'apply_bundle_identity_mismatch'
    assert C.digest(bundle_rows)==receipt['after_digest'],'apply_bundle_digest_mismatch'
    assert unreal.DataTableFunctionLibrary.fill_data_table_from_csv_file(table,str(bundle/'catalog_v4_full.csv'))
    actual=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
    assert C.typed_rows(actual)==C.typed_rows([r['runtime'] for r in expected['rows']]),'native_import_fields_differ'
    assert C.digest(actual)==receipt['after_digest']
    assert unreal.EditorAssetLibrary.save_asset(table_path,only_if_is_dirty=True)
    shutil.copy2(bundle/'catalog_v4_source.json',C.SOURCE);shutil.copy2(bundle/'catalog_v4_full.csv',C.CSV)
    C.write(C.HERE/'NATIVE_TABLE_READBACK.json',C.typed_rows(actual))
    C.write(C.HERE/'NATIVE_TABLE_APPLIED.json',{'pid':os.getpid(),'table':table_path,'rows':len(actual),'saved':True,'digest':C.digest(actual),'newly_enabled':receipt['native_enabled_asset_ids'],'imported_connected_held':receipt['imported_catalog_connected_held_ids'],'profile_patch_still_required':True})
    print(json.dumps({'native_table_saved':table_path,'digest':C.digest(actual),'newly_enabled':len(receipt['native_enabled_asset_ids'])}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    apply() if args.apply else build()
