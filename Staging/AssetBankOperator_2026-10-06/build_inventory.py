"""File-only inventory and proposals. Never imports unreal or writes outside this folder."""
from pathlib import Path
import collections, csv, hashlib, json, re, sqlite3
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJECTS = ROOT.parent
BANK = ROOT/'Staging/ModelBank/PermanentIntegration_2026-10-02'
INTEGRATION = ROOT/'Staging/BankIntegration_2026-10-04'
VAULT = Path('C:/ProgramData/Epic/EpicGamesLauncher/VaultCache')
NOW = datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()
def out(name,value):
    p=HERE/name
    assert p.parent == HERE
    p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def yes(v): return str(v).lower() in ('true','1')
def obj(rel):
    p=Path(rel);return '/Game/'+p.with_suffix('').as_posix()+'.'+p.stem
def file_for(op,root=ROOT):
    return root/'Content'/(op.split('.')[0][6:]+'.uasset') if op.startswith('/Game/') else None
source=read(BANK/'catalog_v4_source.json')
rows=source['rows']
prepared={r['asset_id']:r for r in read(ROOT/'Staging/BankPreparation_2026-10-04/PREPARED_BANK.json')['rows']}
validation=read(INTEGRATION/'NATIVE_VALIDATION.json')
contacts=read(INTEGRATION/'NATIVE_CONTACT_READBACK.json')
supplier=read(ROOT/'Staging/NativeUnrealAssetSupply_2026-10-04/READY_JOBS.json')['jobs']
supplier_by_file={str(Path(j['source_file']).resolve()).lower():j for j in supplier}
by_path={r['object_path']:r for r in rows if r.get('object_path')}
protected=[BANK/'catalog_v4_source.json',BANK/'catalog_v4_full.csv',ROOT/'Content/Python/geocity_bank_workflow.py',ROOT/'Content/Project/Shared/ModelBank/DT_EnvironmentBank_v4.uasset',ROOT/'Staging/ManagedSystemsAstra_2026-10-04/ASSIGNMENTS.json']
protected_before={str(p):sha(p) for p in protected if p.exists()}
lease_before=(ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().splitlines()[-1]

def category(r):
    cat=r['recorded_category'];s=(r['asset_id']+' '+r.get('object_path','')).lower();role=r.get('request_role') or r.get('runtime',{}).get('Role','')
    if cat=='Vegetation':
        if 'mout_family' in s:return 'Vegetation family placeholders'
        if 'fallen' in s:return 'Deadwood'
        if role=='tree' or any(x in s for x in ['st_pine','st_conifer','st_cypress','hornbeam','sm_oak','aspen_tree']):return 'Trees'
        if role=='shrub' or r['asset_id']=='external.T1144' or any(x in s for x in ['desertbush','sm_shrub','bushdry','hedge']):return 'Bushes and shrubs'
        if role=='understory' or 'grassdry' in s:return 'Grass and understory'
        return 'Vegetation unclassified'
    if cat=='SmallProps' and any(x in s for x in ['sm_rock','sm_stone','sm_boulder']):return 'Stones and rocks'
    if cat in ['SmallProps','Utility/SceneSetup'] and 'mountain' in s:return 'Mountain backdrops'
    if cat in ['StreetProps','Signs','Utility/RooftopProps','SmallProps']:return cat
    return 'Outside requested categories'

inventory=[]
for r in rows:
    aid=r['asset_id'];p=prepared.get(aid,{})
    m=contacts.get(aid) or p.get('native_measurement') or {}
    op=r.get('object_path','');f=file_for(op);exists=bool(f and f.is_file())
    retained_hash=m.get('source_sha256') or m.get('package_sha256_at_queue') or p.get('current_package_sha256')
    current_hash=sha(f) if exists else None
    v=validation.get(aid,{})
    ready=bool(v.get('ready') and current_hash and v.get('source_sha256','').lower()==current_hash.lower())
    known=[]
    if aid.startswith('external.ST_'):known.append('SpeedTree source-faithful material binding unresolved in retained vegetation handoff')
    if aid=='external.T1144':known.append('Hedge import and binding receipt absent in retained handoff')
    if aid.startswith('external.MOUT_FAMILY_'):known.append('Family placeholder; individual mesh identities needed')
    status='retained_ready_receipt_mesh_hash_matches' if ready else ('known_repair_or_registration_work' if known else ('verification_pending' if exists else 'native_binding_or_file_absent'))
    inventory.append({'asset_id':aid,'catalog_row_name':r['catalog_row_name'],'category':category(r),'recorded_category':r['recorded_category'],'asset_path':op,'native_package_on_disk':exists,'under_shared_modelbank':op.startswith('/Game/Project/Shared/ModelBank/'),'native_mesh_sha256':current_hash,'retained_measurement_mesh_hash_matches':bool(current_hash and retained_hash and current_hash.lower()==retained_hash.lower()),'usable_now_live_verified':None,'status':status,'known_work':known,'retained_ready_receipt':v if ready else None,'retained_triangles_LOD0':m.get('triangles',m.get('triangles_LOD0')),'retained_LODs':m.get('lod_count'),'retained_collision':{k:m.get(k) for k in ['simple_collision_count','convex_collision_count','collision_complexity']},'retained_materials_bound':m.get('material_slots',p.get('material_slots_recorded',[])),'retained_dependencies':m.get('dependencies'),'rights_state':r.get('recorded_rights_state'),'explicit_hold':yes(r['runtime']['ExplicitHold']),'run_eligible_recorded':yes(r['runtime']['RunEligible']),'role':r['runtime']['Role'],'style':r['runtime']['StyleSet'],'family':r['runtime']['FamilyId']})
def summary(key):
    result=[]
    for cat in sorted(set(x[key] for x in inventory)):
        rs=[r for r in inventory if r[key]==cat]
        result.append({'category':cat,'catalog_identities':len(rs),'native_packages_on_disk':sum(x['native_package_on_disk'] for x in rs),'under_shared_modelbank':sum(x['under_shared_modelbank'] for x in rs),'retained_ready_receipt_mesh_hash_matches':sum(x['status']=='retained_ready_receipt_mesh_hash_matches' for x in rs),'known_repair_or_registration_work':sum(bool(x['known_work']) for x in rs),'verification_or_native_binding_pending':sum(x['status'] in ['verification_pending','native_binding_or_file_absent'] for x in rs),'held':sum(x['explicit_hold'] for x in rs),'run_eligible_recorded':sum(x['run_eligible_recorded'] for x in rs),'usable_now_live_verified':None})
    return result
out('CANONICAL_INVENTORY.json',{'captured_utc':NOW,'source_file':str(BANK/'catalog_v4_source.json'),'source_sha256':protected_before[str(BANK/'catalog_v4_source.json')],'live_editor_read':False,'note':'Retained measurements are historical. Mesh hash checks do not revalidate materials, shader compilation or all dependencies. Unknown readiness is not a repair failure. Family records are not individual meshes.','rows':inventory})
out('INVENTORY_SUMMARY.json',{'recorded_categories':summary('recorded_category'),'requested_categories':summary('category')})

# Read only local acquisition metadata, deliberately omit account identifiers.
db=VAULT/'FabLibrary/listings_v1.db'
c=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)
acquisitions=[dict(zip(['listing_id','title','acquisition_rows'],r)) for r in c.execute('SELECT l.uid,l.title,COUNT(a.listing_uid) FROM local_listing l LEFT JOIN listing_acquisition a ON a.listing_uid=l.uid GROUP BY l.uid,l.title')]
c.close()
out('LOCAL_ACQUISITIONS.json',{'source':str(db),'captured_utc':NOW,'rows':acquisitions,'limitation':'No acquisition licence, tier or date fields in this database. User identifies owned sources; do not infer exact terms from presence.'})

# File candidates, not an Asset Registry query. Source inventory is separate from canonical counts.
packs=['StarterContent','ModularCourtyard','MOUT_Arabian','FC_Coastal_Landscape','UtopianCity','WorldBLD','Palms_Pack_01','HighPoly_Tree_Model','Iceland_Environment','FantasyRuins','AssetsvilleTown','ProceduralBuildingGenerator','ModularBuildingSet','Stylized_Egypt','Warehouse_Building','MWLandscapeAutoMaterial']
sources=[('Current',ROOT,pack) for pack in packs]+[('CitySample',PROJECTS/'CitySample','Prop'),('CitySample',PROJECTS/'CitySample','Vehicle'),('GISWorldBLD',PROJECTS/'GIS_WorldBLD','MOUT_Arabian'),('GISWorldBLD',PROJECTS/'GIS_WorldBLD','Light_Foliage')]
source_rows=[];source_summary=[]
for sid,project,pack in sources:
    fs=list((project/'Content'/pack).rglob('*.uasset'))
    meshes=[f for f in fs if f.stem.startswith('SM_') or (('/Mesh/' in f.as_posix() or '/Meshes/' in f.as_posix()) and f.stem.startswith(('Tree_','Border_','Rock_')))]
    source_summary.append({'source_id':sid,'pack':pack,'uasset_files':len(fs),'mesh_filename_candidates':len(meshes),'count_basis':'filename heuristic; class and dependency closure require leased native verification'})
    for f in meshes:source_rows.append({'source_id':sid,'pack':pack,'source_file':str(f),'source_relative_file':f.relative_to(project/'Content').as_posix(),'bytes':f.stat().st_size})
out('SOURCE_INVENTORY.json',{'captured_utc':NOW,'summary':source_summary,'mesh_candidates':source_rows})

batch=[]
def add(sid,rel,cat,role,style,family,listing,parent=None):
    project=ROOT if sid=='Current' else PROJECTS/('GIS_WorldBLD' if sid=='GISWorldBLD' else sid)
    f=project/'Content'/rel;assert f.exists(),f
    existing=by_path.get(obj(rel)) if sid=='Current' else None
    source_hash=sha(f)
    hash_aliases=[x for x in inventory if x['native_mesh_sha256']==source_hash]
    if not existing and len(hash_aliases)==1:
        existing=next(r for r in rows if r['asset_id']==hash_aliases[0]['asset_id'])
    assert len(hash_aliases)<=1 or existing, 'Ambiguous canonical hash aliases: '+str(f)
    old=supplier_by_file.get(str(f.resolve()).lower())
    aid=existing['asset_id'] if existing else old['asset_id'] if old else 'native.'+sid+'.'+hashlib.sha256((sid+'/'+rel).encode()).hexdigest()[:24]
    rowname=existing['catalog_row_name'] if existing else old['catalog_row_name'] if old else 'MB_'+hashlib.md5(aid.encode()).hexdigest().upper()
    target='/Game/Project/Shared/ModelBank/Prepared/NativeUnreal/'+sid+'/'+rel[:-7]+'.'+f.stem
    assert target.startswith('/Game/Project/Shared/ModelBank/')
    measure=prepared.get(aid,{}).get('native_measurement') or {}
    batch.append({'asset_id':aid,'row_name':rowname,'category':cat,'source_id':sid,'source_file':str(f),'source_relative_file':rel,'source_object_path':obj(rel),'source_sha256':sha(f),'proposed_asset_path':target,'source_pack_listing_id':listing,'licence_state':'acquisition_record_present_exact_terms_pending','licence_confirmed':False,'licence_evidence':['LOCAL_ACQUISITIONS.json','https://www.fab.com/listings/'+listing],'source_family_parent_id':parent,'existing_canonical_identity':bool(existing),'existing_supplier_job_id':old.get('job_id') if old else None,'proposed_role':role,'proposed_style':style,'family_id':family,'size_cm':None,'size_status':'measure_native_bounds_before_registration','triangles':measure.get('triangles_LOD0'),'LODs':measure.get('lod_count'),'collision':None,'materials_bound':None,'textures_resolved':None,'native_measurements_status':'pending_manager_lease','selection_change_authorized':False,'state':'PROPOSED_NOT_IMPORTED','operation':'reuse_existing_identity_copy_native_with_dependencies_to_bank' if existing else 'native_copy_with_dependency_remap_and_held_registration','deduplication_required':'reconcile existing supplier job and canonical source-path/hash aliases before execution'})

MOUT='2f06f74d-db49-4ce9-83e5-0f08e51af597';MW='6602874e-ef24-48c9-9055-a7ac07384696';CITY='4898e707-7855-404b-af0e-a505ee690e68'
for i in range(1,7):add('GISWorldBLD',f'MOUT_Arabian/Meshes/Props/Foliage/DesertTree/SM_Desert_Tree_{i:02}.uasset','Trees','tree','arid_regional_review_pending','MOUT_DesertTree',MOUT,'external.MOUT_FAMILY_DesertTree')
for i in [1,6]:add('GISWorldBLD',f'MOUT_Arabian/Meshes/Props/Foliage/PalmTrees/SM_PalmTree_{i:02}.uasset','Trees','tree','arid_regional_review_pending','MOUT_PalmTrees',MOUT,'external.MOUT_FAMILY_PalmTrees')
for name in ['SM_Shrub_A','SM_Shrub_B_01','SM_Shrub_Bare_A','SM_Shrub_Bare_B']:add('GISWorldBLD','MOUT_Arabian/Meshes/Props/Foliage/DesertBush/'+name+'.uasset','Bushes and shrubs','shrub','arid_regional_review_pending','MOUT_DesertBush',MOUT,'external.MOUT_FAMILY_DesertBush')
for name in ['SM_Desert_Shrub_01','SM_Desert_Shrub_01_Bare','SM_Desert_Shrub_02','SM_Desert_Shrub_03']:add('GISWorldBLD','MOUT_Arabian/Meshes/Props/Foliage/DesertShrub/'+name+'.uasset','Bushes and shrubs','shrub','arid_regional_review_pending','MOUT_DesertShrub',MOUT,'external.MOUT_FAMILY_DesertShrub')
for v in 'ABCD':add('Current',f'MWLandscapeAutoMaterial/Meshes/Plants/SM_MWAM_Grass{v}.uasset','Grass and understory','understory','source_grass_review_pending','MW_Grass',MW)
for folder,name in [('Kit_Tree_Alder','Tree_Alder_A'),('Kit_Tree_Alder','Tree_Alder_B'),('Kit_Tree_Maple_Red','Tree_Maple_Red_A'),('Kit_Tree_Maple_Sugar','Tree_Maple_A')]:add('CitySample',f'Prop/{folder}/Mesh/{name}.uasset','Trees','tree','temperate_urban_review_pending',folder,CITY)

def city(rel,subtype,role='street_prop'):
    add('CitySample','Prop/'+rel+'.uasset','Props','' if role=='hosted' else role,'urban_source_style_review_pending',subtype,CITY)
    batch[-1]['prop_subcategory']=subtype
    if role=='hosted':batch[-1]['consumer_status']='requires_explicit_host_consumer_manager_review; no invented runtime role'
for size in ['Large','Long','Small']:city('Kit_StreetLamp_A/Mesh/SM_StreetLamp_A_Pole_'+size,'poles','street_pole')
for v in 'ABCD':city('CITY/Kit_StreetSign/Mesh/SM_CTY_StreetSign_'+v+'01_N1','signs','hosted')
city('Kit_Border_B/Mesh/Border_B_StoneBench_N1','benches')
city('Kit_Trashcan_A/Mesh/SM_Trashcan_A_01','bins')
for v in 'AB':city('FWY/Kit_Trash/Mesh/SM_FWYTrash_Container_'+v+'01_N1','bins')
for name in ['SM_Fence_ChainLink_A01_N1','SM_Fence_ChainLink_A02_N1','SM_Fence_ChainLink_B01_N1','SM_Fence_Post_A01_N1']:city('CONSTRUCTION/Kit_Fence/Mesh/'+name,'fences','hosted')
for v in 'ACD':city('BLDG/B/Kit_Prop_BA/Mesh/SM_BLDG_Prop_BA_Awning_'+v+'01_N1','awnings','hosted')
for i in [1,2]:city('BLDG/Kit_Prop_AC/Mesh/SM_BLDG_Prop_AC_Window_A0'+str(i)+'_N1','AC units','hosted')
city('Kit_roof_tank_a_RR/Mesh/SM_roof_tank_a_N1','water tanks','hosted')
city('Kit_roof_tank_B_RR/Mesh/SM_roof_tank_b','water tanks','hosted')
for v in ['a','d']:city('Kit_antenna_RR/Mesh/SM_roof_antenna_'+v+'_N1','antennas','hosted')
for v in 'ab':city('Kit_antenna_RR/Mesh/SM_roof_breaker_box_'+v+'_N1','utility boxes','hosted')
for v in 'AB':city('FWY/Kit_Trash/Mesh/SM_FWYTrash_Bag_'+v+'01_N1','clutter','small_prop')
# Two complete construction barriers, selected from observed mesh files.
barriers=sorted((PROJECTS/'CitySample/Content/Prop').glob('**/Mesh/*Barrier*.uasset'))
barriers=[f for f in barriers if 'Sign' not in f.stem and ('Concrete' in f.stem or 'Barrier' in f.stem)]
for f in barriers[:2]:city(f.relative_to(PROJECTS/'CitySample/Content/Prop').with_suffix('').as_posix(),'barriers')
assert sum(x['category']=='Props' for x in batch)==30
for v in 'ABCD':add('Current',f'MWLandscapeAutoMaterial/Meshes/Cover/SM_MWAM_Stone{v}.uasset','Stones and rocks','small_prop','arid_material_review_pending','MW_Stone',MW)
for v in 'AB':add('Current',f'MWLandscapeAutoMaterial/Meshes/Background/SM_MWAM_Mountain{v}.uasset','Mountain backdrops','','background_only_review_pending','MW_Mountain',MW)
assert len(batch)==60 and len({x['asset_id'] for x in batch})==60
assert not any(any(h in x['asset_id'] for h in ['H0013','H0907','H0051','H0958','H0094']) for x in batch)
out('BATCH_001_PROPOSAL.json',{'schema':'environmentpipeline.bank_operator_proposal.v1','captured_utc':NOW,'manager_session':'cc37d4d2-3d62-4f53-b689-28432b5527ae','status':'NOT_EXECUTED_LICENCE_TERMS_AND_MANAGER_LEASE_PENDING','counts':dict(collections.Counter(x['category'] for x in batch)),'prop_subcategories':dict(collections.Counter(x['prop_subcategory'] for x in batch if x['category']=='Props')),'rows':batch})

# Exact native CSV schema. Unknown measurements explicitly remain invalid.
fields=list(rows[0]['runtime'])
patch=[]
for b in batch:
    r={k:'' for k in fields}
    for k in fields:
        if k.endswith('Cm') or k in ['SelectionWeight','PreviewWeight']:r[k]='0.0'
    r.update(Name=b['row_name'],SchemaVersion='3',AssetId=b['asset_id'],ObjectPath=b['proposed_asset_path'],Role=b['proposed_role'],VariantId=Path(b['source_file']).stem,RunEligible='false',BoundsValid='false',AnchorValid='false',OrientationValid='false',FamilyId=b['family_id'],StyleSet=b['proposed_style'],SelectionWeight='0.0',PlacementScope='none',AllowedAreas='',AllowedZones='',ReleaseId='',DecisionId='',RequestRole=b['proposed_role'],PlacementRule={'tree':'terrain_tree','shrub':'terrain_shrub','understory':'terrain_understory','street_pole':'roadside_pole','street_prop':'roadside_prop','small_prop':'zone_ground_prop'}.get(b['proposed_role'],''),TechnicalPreviewEligible='false',ExplicitHold='true',PreviewWeight='0.0',HoldReasons='native_supply_qualification_pending|licence_terms_pending|manager_review_pending')
    if b['source_family_parent_id']:
        parent=next(x for x in rows if x['asset_id']==b['source_family_parent_id'])
        r['HoldReasons']='|'.join(dict.fromkeys(r['HoldReasons'].split('|')+['source_family_hold_preserved']+parent['hold_reasons']))
    patch.append(r)
out('CATALOG_PATCH_PROPOSAL.json',{'target_table':source['native_data_table_package'],'baseline_source_sha256':protected_before[str(BANK/'catalog_v4_source.json')],'apply_authorized':False,'apply_status':'DO_NOT_APPLY_UNMEASURED_PROPOSAL','instructions':'Rebase against manager-approved current catalogue. Preserve all existing IDs/holds and 87 road candidates. Fill native bounds, revisions, geometry, materials and licence evidence before table registration. This proposal does not alter profiles, pins or selection. Existing canonical identities must be updated rather than duplicated.','rows':patch})
out('BATCH_001_RECEIPT_TEMPLATE.json',{'state':'TEMPLATE_NOT_EXECUTED','manager_lease_line':None,'actual_editor_pid':None,'counts':{'imported':0,'reused':0,'failed':0,'pending':60},'rows':[{'asset_id':b['asset_id'],'asset_path':b['proposed_asset_path'],'source':b['source_file'],'source_sha256':b['source_sha256'],'licence':None,'triangles':None,'LODs':None,'collision':None,'materials_bound':None,'textures_resolved':None,'named_saved_packages':[],'reopen_verified':False,'result':'pending'} for b in batch]})

receipt=read(BANK/'HDA_CATALOG_RECEIPT.json')
out('SCHEMA_AND_CONSUMER_REVIEW.json',{'workflow_file':str(ROOT/'Content/Python/geocity_bank_workflow.py'),'workflow_sha256':protected_before[str(ROOT/'Content/Python/geocity_bank_workflow.py')],'native_table':source['native_data_table_package'],'native_row_schema_version':source['native_schema_version'],'runtime_fields':fields,'size_contract':'BoundsValid plus BoundsMinXCm/Y/Z and BoundsMaxXCm/Y/Z. No Size enum or scalar field exists in the native row schema. Unknown bounds remain invalid, not fabricated.','role_contract':'Role/RequestRole and PlacementRule use retained supported roles. Hosted signs, fences, awnings, AC/tanks/antennas and backdrop consumers need manager mapping before Role is set. Blank roles cannot generate.','style_contract':'StyleSet/FamilyId proposed only; source style and botanical names are unverified unless explicit in asset names. No area profile changes.','historical_hda_receipt':{'path':str(BANK/'HDA_CATALOG_RECEIPT.json'),'mtime_utc':datetime.fromtimestamp((BANK/'HDA_CATALOG_RECEIPT.json').stat().st_mtime,timezone.utc).isoformat(),'catalog_sha256':receipt.get('catalog_sha256'),'schema_version':receipt.get('schema_version'),'native_table_schema_version':receipt.get('native_table_schema_version'),'active_candidate_roles':receipt.get('active_candidate_roles')},'first_batch_imports':0,'first_batch_table_registrations':0,'selection_rows_enabled':0})
out('LICENCE_REVIEW.json',{'checked_utc':NOW,'status':'EXACT_ACQUISITION_TERMS_UNCONFIRMED','ownership_basis':'User relayed that owned Fab/Marketplace sources may be used; local acquisition records exist for all three proposed source packs. This does not record the licence attached to each acquisition.','confirmed_for_batch':0,'pending_for_batch':60,'packs':[{'name':name,'listing_id':uid,'batch_assets':sum(b['source_pack_listing_id']==uid for b in batch),'acquisition_record_present':any(a['listing_id']==uid and a['acquisition_rows'] for a in acquisitions),'exact_licence_at_acquisition':None} for name,uid in [('City Sample',CITY),('MOUT Arabian',MOUT),('MW Landscape Auto Material',MW)]],'primary_sources':[{'url':'https://www.unrealengine.com/eula/content','finding':'Epic Content Licence covers relevant Marketplace content and private use/modification; UE-only restrictions apply where designated. This general agreement is not an acquisition receipt.'},{'url':'https://www.fab.com/eula','finding':'Fab Standard licence summary permits use and modification in projects and restricts standalone redistribution. Do not assign it automatically to legacy acquisitions.'},{'url':'https://www.fab.com/listings/'+CITY,'finding':'Official product identity checked; fetched licence field was a dash, so exact terms were not established.'},{'url':'https://www.fab.com/listings/'+MW,'finding':'Official product identity checked; fetched licence field was a dash, so exact terms were not established.'}],'rights_holds_changed':False,'next_evidence':'Manager/Aviv to identify the acquisition licence for City Sample, MOUT Arabian and MW Landscape Auto Material, or provide the acquisition-specific licence record. No purchase requested.'})
lines=['ASSET BANK OPERATOR — INVENTORY AND BATCH 001 PROPOSAL','Date: 2026-10-06 (Asia/Jerusalem); captured UTC: '+NOW,'Manager: Claude Code cc37d4d2-3d62-4f53-b689-28432b5527ae','Status: file-only preparation complete; native inspection/import and licence-confirmed release NOT complete.','','Authority and editor boundary',lease_before,'The last owner line belongs to the manager. No Unreal/Houdini call, editor launch, import, save or catalogue/profile change was made. Wait for OWNER=NONE, then obtain the manager lease through Aviv before any editor work.','','Inventory scope and confidence','1,223 canonical identities were read from the current on-disk catalog_v4_source.json. Asset file existence and mesh hashes were checked now. Catalogue rows include family placeholders, materials and utilities; they are not all unique usable models.','Usable now: NOT LIVE-VERIFIED. Eleven prop identities have retained ready receipts with matching current mesh hashes. Those receipts do not revalidate current material dependencies or licence terms. Do not count every file as ready or every unknown as broken.','Columns: category | identities | packages present | already under Shared/ModelBank | retained ready receipts with matching mesh hash | known repair/registration work | other verification/binding pending | recorded eligible']
for s in summary('category'):
    lines.append(' | '.join(str(s[k]) for k in ['category','catalog_identities','native_packages_on_disk','under_shared_modelbank','retained_ready_receipt_mesh_hash_matches','known_repair_or_registration_work','verification_or_native_binding_pending','run_eligible_recorded']))
lines+=['','Known work','- Six SpeedTree trees: source-faithful material binding remained unresolved in the retained handoff; fresh native inspection is required.','- external.T1144 hedge: native binding absent; retained prepared import was not executed.','- Four vegetation MOUT family records: aggregate inventory only. Individual source meshes are available in GIS_WorldBLD and need held per-mesh registration.','- Other MOUT prop family placeholders also need individual identities; they are not failed mesh files.','- Grass/Plant07 diagnostic records require native material review; a diagnosis record is not a successful repair.','','Installed source survey','These are mesh filename candidates, not verified class counts, dependency closures, unique model counts or complete vehicles. Vendor originals are retained. No full-bank source reset was made.']
for s in source_summary:lines.append(f"- {s['source_id']} / {s['pack']}: {s['mesh_filename_candidates']} mesh filename candidates, {s['uasset_files']} asset packages.")
lines+=['ModularBuildingSet uses names outside the mesh filename heuristic; its zero candidate count does NOT mean it contains no meshes. Canonical rows and native measurement records remain in CANONICAL_INVENTORY.json.','Environmentpipeline/MOUT_Arabian has landscape resources but no discovered foliage meshes. The complete installed MOUT source is in GIS_WorldBLD.','FC_Coastal_Landscape contributes a sea-plane mesh and landscape assets; no vegetation meshes were found in this survey.','City Sample vehicle file counts include parts; no complete, ready vehicle is claimed.','','First batch: 60 proposed assets','12 trees + 8 bushes/shrubs + 4 grass = 24 vegetation; 30 props; 4 stones + 2 mountain backdrops supplemental.','Source split: 16 MOUT Arabian vegetation; 34 City Sample assets (4 trees + 30 props); 10 MW assets (4 grass + 4 stones + 2 backdrops).','Trees include six desert-tree variants and two palm variants from MOUT, plus alder A/B, red maple and sugar maple. MOUT species and physical size ranges await native measurement. Temperate trees are bank variety, not automatic approval for Gaza or Iran.','The 30 props include poles, signs, bench, bins, fences, awnings, AC units, water tanks, antennas, utility boxes, barriers and clutter. Walls and licensed complete vehicles remain later supply work.','All 60 exact source files, SHA-256 values, stable IDs and bank-only target paths are in BATCH_001_PROPOSAL.json. Existing supplier job IDs are reused where present. Source path and canonical hash aliases were reconciled; recheck duplicates immediately before apply.','','Licence outcome — outstanding requirement','All three proposed packs have local acquisition entries in the current 42-entry Fab cache. Ownership is identified by Aviv in the mission; no extra purchase is requested. The database does not contain acquisition-specific licence terms/tier/date, and the fetched City Sample/MW listings do not expose their licence text.','Therefore 0 of these 60 are marked licence-confirmed. All 60 remain proposed pending exact applicable terms. This is NOT a licence-confirmed executable import batch yet. LICENCE_REVIEW.json records the evidence and missing fields.','Primary references: https://www.unrealengine.com/eula/content and https://www.fab.com/eula . General permission under those agreements does not by itself map a licence to this local acquisition.','Additional locally acquired leads: Light Foliage; Megaplants Greasewood; Palms Pack 02 (Phoenix canariensis); mediterranean Vegetation giant Reed; Rock Environment Pack; Realistic Desert Pack; Namaqualand Environment and Asset Pack. Acquisition records are inventory leads; payload availability, exact terms and regional suitability require review.','','Catalogue proposal and integration contract','DT_EnvironmentBank_v4 currently uses native row schema 3. Size is represented by valid measured BoundsMin/Max fields; there is no Size enum. The proposal preserves this schema.','CATALOG_PATCH_PROPOSAL.json is manager review data only. BoundsValid/AnchorValid/OrientationValid remain false until measured. RunEligible, TechnicalPreviewEligible and weights are zero; no selection row or profile pin is enabled.','Hosted props and mountain backdrops retain blank runtime roles pending manager consumer mapping. Their metadata describes the desired function; no unsupported generator role is invented.','Family holds and named holds H0013, H0907, H0051, H0958, H0094 remain unchanged. The 87 road candidates are untouched.','After the manager releases the editor and supplies a lease: inspect exact current PID/world/dirty packages; resolve source dependencies read-only; duplicate/migrate meshes and required project dependencies into /Game/Project/Shared/ModelBank/Prepared/NativeUnreal/... with reference remapping; never raw-copy UAssets into renamed namespaces.','Reuse existing shared assets and stable IDs. Do not overwrite vendor originals or use Save All. Keep failures isolated. Record actual triangles/LODs/collision/material bindings/texture resolution, named saves and reopen result per item in one batch receipt. Register held rows only after measurements and manager-reviewed catalogue rebase; keep selection/profile proposals separate.','Source projects must not be opened concurrently with the manager editor; any required source-editor inspection/migration also needs an explicitly scoped one-writer lease. No startup hooks, sample maps or sample gameplay modules are part of the asset supply.','','Batch outcome','Imported: 0; reused/applied: 0; failed imports: 0; proposed/pending: 60. No actual import receipt exists; BATCH_001_RECEIPT_TEMPLATE.json is explicitly a template.','','Short Hebrew summary for Aviv','נבדקו 1,223 רשומות בקטלוג. הוכנה הצעה ל־24 פריטי צמחייה, 30 אביזרים ועוד 6 סלעים ורקעי הרים. לא בוצע ייבוא ולא שונה הקטלוג. העורך מוחזק כעת בידי המנהל. רישומי רכישה קיימים, אך תנאי הרישיון המדויקים עדיין לא אומתו; נדרשים השלמת האימות והקצאת עורך מהמנהל.','','Exact first-batch list']
for i,b in enumerate(batch,1):lines.append(f"{i:02}. {b['category']} / {b.get('prop_subcategory',b['family_id'])} | {Path(b['source_file']).stem} | {b['asset_id']}")
(HERE/'INVENTORY_AND_BATCH_001.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
after={str(p):sha(p) for p in protected if p.exists()}
out('PRESERVATION_CHECK.json',{'before':protected_before,'after':after,'unchanged':protected_before==after,'lease_last_line_before':lease_before,'lease_last_line_after':(ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().splitlines()[-1],'editor_calls':0,'native_writes':0,'assignments_writes':0,'area_profile_writes':0,'catalog_writes':0,'vendor_writes':0,'road_candidate_writes':0,'note':'Only this operator staging folder was written. Concurrent manager writes, if any, are not operator changes.'})
print(json.dumps({'summary':summary('category'),'batch_counts':dict(collections.Counter(x['category'] for x in batch)),'source_summary':source_summary,'acquisitions':len(acquisitions),'protected_unchanged':protected_before==after},indent=2))
