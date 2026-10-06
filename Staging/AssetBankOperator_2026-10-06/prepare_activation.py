"""Build measured additive table transactions; no editor calls or shared writes."""
from pathlib import Path
import json,hashlib,copy,csv,importlib.util,collections
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
spec=importlib.util.spec_from_file_location('bank_digest_only',ROOT/'Staging/BankIntegration_2026-10-04/bank_contracts.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
SOURCE=ROOT/'Staging/ModelBank/PermanentIntegration_2026-10-02/catalog_v4_source.json'
original=read(SOURCE);canonical=copy.deepcopy(original)
old_native=read(HERE/'Before/NATIVE_TABLE_V4.json')
assert C.typed_rows(old_native)==C.typed_rows([x['runtime'] for x in original['rows']])
queue={r['asset_id']:r for r in read(HERE/'EXPANDED_SUPPLY_QUEUE.json')['rows']}
proposals={r['asset_id']:r for r in read(HERE/'EXPANDED_CATALOG_PATCH_PROPOSAL.json')['rows']}
overrides=read(HERE/'EXECUTION_BATCHES.json')['batches'][0]['role_overrides']
valid=[]
for batch in ['BANK_EXPANSION_007','BANK_EXPANSION_011','BANK_EXPANSION_014','BANK_USE_CITY_001']:
    p=HERE/f'Native/{batch}_VALIDATION.json';x=read(p);assert x['complete']
    for v in x['assets']:
        assert v['status']=='native_validated' and v['named_saved'];v['receipt']=str(p);valid.append(v)
role_counts=collections.Counter(overrides.get(v['asset_id'],queue[v['asset_id']]['proposed_role']) for v in valid)
decision_id='Aviv_DirectAssetBankUse_20261006'
gaza_release=read(ROOT/'Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json')['release']['id']
new=[]
for v in valid:
    q=queue[v['asset_id']];assert not q['existing_canonical_identity']
    assert not any(h in v['asset_id'] for h in C.NAMED_HOLDS)
    assert v['asset_id'] not in {r['asset_id'] for r in original['rows']}
    r=copy.deepcopy(proposals[v['asset_id']]['runtime_row']);role=overrides.get(v['asset_id'],q['proposed_role'])
    bounds=v['bounds_cm'];span=[b-a for a,b in zip(bounds['min'],bounds['max'])]
    spacing=max({'tree':1200,'shrub':350,'understory':180,'small_prop':300,'street_prop':600,'street_pole':1500}[role],max(span[:2])+100)
    r.update(ObjectPath=v['asset_path'],Role=role,RequestRole=role,PlacementRule=C.RULES[role],AssetRevision=v['asset_revision_sha256'],RunEligible='true',BoundsValid='true',AnchorValid='true',OrientationValid='true',AnchorZCm=str(bounds['min'][2]),ForwardAxis='+X',StyleSet='mediterranean_urban',SelectionWeight=str(2.0/role_counts[role]),PlacementScope='area_zone',AllowedAreas='GazaRimal|GazaShujaiya',AllowedZones='roadside' if role in ('street_prop','street_pole') else 'open_ground',ReleaseId=gaza_release,DecisionId=decision_id,TechnicalPreviewEligible='true',ExplicitHold='false',PreviewWeight='1.0',MinSpacingCm=str(spacing),HoldReasons='')
    for side,key in [('Min','min'),('Max','max')]:
        for i,axis in enumerate('XYZ'):r['Bounds'+side+axis+'Cm']=str(bounds[key][i])
    record={'asset_id':v['asset_id'],'catalog_row_name':r['Name'],'object_path':v['asset_path'],'asset_revision_sha256':v['asset_revision_sha256'],'source_package':q['source_pack'],'source_revision':q['source_sha256'],'source_catalog':str(HERE/'EXPANDED_SUPPLY_QUEUE.json'),'recorded_category':q['category'],'recorded_native_class':'StaticMesh','recorded_rights_state':'owner_confirmed_technical_use_exact_acquisition_document_followup','recorded_dependency_state':'native_dependency_closure_resolved','recorded_material_state':'all_slots_bound_instancing_compatible_textures_resolved','canonical_run_eligible':True,'general_generation_released':True,'canonical_qualified':False,'recorded_visual_state':'retained_scene_verification_pending','request_role':role,'placement_rule':C.RULES[role],'hold_reasons':[],'explicit_hold':False,'review_hold':'','runtime':r,'native_validation_receipt':v['receipt'],'activation_basis':str(HERE/'DIRECT_USER_ACTIVATION_29900.json'),'contact_basis':'Native mesh bounds minimum Z; retained generator uses center-bottom terrain fit. Vegetation and freestanding clutter do not require semantic front-facing alignment. Visible placement verification remains pending.'}
    canonical['rows'].append(record);new.append(r)
assert len(new)==72
canonical['catalog_sha256']=C.digest([r['runtime'] for r in canonical['rows']]);canonical['normal_use_catalog_digest']=canonical['catalog_sha256'];canonical['asset_bank_expansion_receipt']=str(HERE/'Activation/DECISION.json')
dest=HERE/'Activation';dest.mkdir(exist_ok=True)
write(dest/'CATALOG_SOURCE.json',canonical)
rows_v4=[r['runtime'] for r in canonical['rows']];rows_iran=read(HERE/'Before/NATIVE_TABLE_IRAN.json')
iran_profile=ROOT/'Staging/ModelBank/Iran_38196167_46086167_4km/AREA_PROFILE.json';iran=read(iran_profile)
for row in new:
    r=copy.deepcopy(row);r['AllowedAreas']='Iran_38196167_46086167_4km';r['ReleaseId']=iran['release']['id']
    if queue[r['AssetId']]['source_pack']=='phoenix_palms':
        r.update(RunEligible='false',TechnicalPreviewEligible='false',ExplicitHold='true',SelectionWeight='0.0',PreviewWeight='0.0',HoldReasons='regional_ecology_palm_not_enabled_for_iran_mountain_area')
    rows_iran.append(r)
transactions=[]
for key,rows,table in [('V4',rows_v4,'/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4'),('IRAN',rows_iran,iran['table'])]:
    path=dest/(key+'.csv')
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(new[0]));w.writeheader();w.writerows(rows)
    write(dest/(key+'.json'),rows)
    transactions.append({'key':key,'table':table,'before_digest':C.digest(read(HERE/('Before/NATIVE_TABLE_'+key+'.json'))),'after_digest':C.digest(rows),'row_count':len(rows),'csv':str(path),'rows':str(dest/(key+'.json'))})
profiles=[]
for label,rel,key in [('GazaRimal','Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json','V4'),('GazaShujaiya','Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json','V4'),('Iran','Staging/ModelBank/Iran_38196167_46086167_4km/AREA_PROFILE.json','IRAN')]:
    p=ROOT/rel;x=read(p);tx=next(t for t in transactions if t['key']==key)
    backup=HERE/'Before'/('AREA_PROFILE_'+label+'.json');assert not backup.exists();backup.write_bytes(p.read_bytes())
    before_sha=sha(p);x['catalog_sha256']=tx['after_digest'];x['row_count']=tx['row_count']
    x['release'].update(catalog_sha256=tx['after_digest'],decision_receipt=str(dest/'DECISION.json'))
    profiles.append({'label':label,'path':str(p),'before_sha256':before_sha,'before':str(backup),'proposed':x})
decision={'id':decision_id,'authority':'Aviv direct authorization in this chat','activation':str(HERE/'DIRECT_USER_ACTIVATION_29900.json'),'native_validated_added_ids':[r['AssetId'] for r in new],'added':72,'role_counts':dict(role_counts),'tables':transactions,'existing_rows_preserved_verbatim':True,'existing_holds_and_87_road_candidates_preserved':True,'palms_excluded_from_iran':18,'grass_policy':'Retain existing landscape grass switches. New grass is eligible through the HDA understory role; native landscape-grass mesh paths are a separate later binding.','no_visual_acceptance_claim':True}
write(dest/'DECISION.json',decision)
for p in profiles:
    p['proposed']['release']['decision_sha256']=sha(dest/'DECISION.json')
write(dest/'TRANSACTION.json',{'source_before_sha256':sha(SOURCE),'csv_before_sha256':sha(SOURCE.with_name('catalog_v4_full.csv')),'source_path':str(SOURCE),'csv_path':str(SOURCE.with_name('catalog_v4_full.csv')),'new_source':str(dest/'CATALOG_SOURCE.json'),'tables':transactions,'profiles':profiles,'native_source_before':str(HERE/'Before/NATIVE_TABLE_V4.json'),'decision_sha256':sha(dest/'DECISION.json')})
print(json.dumps({'added':len(new),'role_counts':dict(role_counts),'tables':[{k:t[k] for k in ['key','row_count','after_digest']} for t in transactions]}))
