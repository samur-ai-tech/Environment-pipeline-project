"""Build a larger deduplicated bank supply proposal. File-only; never applies a native patch."""
from pathlib import Path
import collections, hashlib, json, re, sys
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];PROJECTS=ROOT.parent
sys.path.insert(0,str(HERE))
from stage_owned_packs import load,safe_file
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(n,d):(HERE/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
 return h.hexdigest()
def yes(v):return str(v).lower() in ['true','1']
def object_path(rel):p=Path(rel);return '/Game/'+p.with_suffix('').as_posix()+'.'+p.stem
catalog_path=ROOT/'Staging/ModelBank/PermanentIntegration_2026-10-02/catalog_v4_source.json'
catalog=read(catalog_path);baseline=sha(catalog_path)
canonical={x['object_path']:x for x in catalog['rows'] if x.get('object_path')}
native_hashes=collections.defaultdict(list)
for r in read(HERE/'CANONICAL_INVENTORY.json')['rows']:
 if r['native_mesh_sha256']:native_hashes[r['native_mesh_sha256']].append(r['asset_id'])
by_id={x['asset_id']:x for x in catalog['rows']}
first=read(HERE/'BATCH_001_PROPOSAL.json')['rows'];first_by_source={(r['source_id'],r['source_relative_file']):r for r in first}
supplier=read(ROOT/'Staging/NativeUnrealAssetSupply_2026-10-04/READY_JOBS.json')['jobs']
old={(r['source_id'],r['source_relative_file']):r for r in supplier}
entries={};excluded=[]
HOLD_IDS=['H0013','H0907','H0051','H0958','H0094']
def classify(rel):
 s=rel.lower();name=Path(rel).stem.lower()
 if any(k in s for k in ['/outerlandscapes/','mountain']):return 'Mountain backdrops',''
 if any(k in s for k in ['/rock','stone','cliff','boulder','/meshes/general/']):return 'Stones and rocks','small_prop'
 if any(k in s for k in ['grass','reed','flower','succulent','iceplant','lily','lill','clover','plant_','plant07','vine','nopal']):return 'Grass and understory','understory'
 if any(k in s for k in ['bush','shrub','greasewood','gw_cluster','thicket','didelta','euphorbia','lycium','roussea','salvia']):return 'Bushes and shrubs','shrub'
 if any(k in s for k in ['palm','tree_','_tree','acacia','willow','alder','birch','maple','oak','quiver']):return 'Trees','tree'
 if '/foliage/' in s:return 'Grass and understory','understory'
 if any(k in s for k in ['awning','antenna','tank','ac_window','aircond','fence','railing','sign','wall','breaker']):return 'Hosted and boundary props',''
 if 'pole' in s:return 'Street props','street_pole'
 return 'Street props','street_prop'
def add(sid,project,rel,pack,listing=None,family=None,variant_paths=None):
 key=(sid,rel)
 if key in entries:return
 p=safe_file(project/'Content',rel)
 if not p.exists():excluded.append({'source':str(p),'reason':'source_file_not_yet_staged'});return
 op=object_path(rel);existing=canonical.get(op) if sid=='Current' else None
 digest=sha(p)
 aliases=native_hashes.get(digest,[])
 if existing is None and len(aliases)==1:existing=by_id[aliases[0]]
 if existing and any(x in existing['asset_id'] for x in HOLD_IDS):excluded.append({'source':str(p),'reason':'named_hold_preserved','asset_id':existing['asset_id']});return
 prior=first_by_source.get(key) or old.get(key)
 aid=existing['asset_id'] if existing else prior['asset_id'] if prior else 'native.'+sid+'.'+hashlib.sha256((sid+'/'+rel).encode()).hexdigest()[:24]
 rn=existing['catalog_row_name'] if existing else (prior.get('row_name') or prior.get('catalog_row_name')) if prior else 'MB_'+hashlib.md5(aid.encode()).hexdigest().upper()
 cat,role=classify(rel)
 if prior and 'proposed_asset_path' in prior:target=prior['proposed_asset_path']
 elif existing and existing['object_path'].startswith('/Game/Project/Shared/ModelBank/'):target=existing['object_path']
 else:target='/Game/Project/Shared/ModelBank/Supply/'+re.sub('[^A-Za-z0-9_]','_',pack)+'/Meshes/'+p.stem+'_'+hashlib.sha256((sid+'/'+rel).encode()).hexdigest()[:8]+'.'+p.stem+'_'+hashlib.sha256((sid+'/'+rel).encode()).hexdigest()[:8]
 holds=list(existing.get('hold_reasons',[])) if existing else []
 parent=None
 if pack=='MOUT_Arabian':
  for candidate in by_id:
   if candidate.startswith('external.MOUT_FAMILY_') and candidate.split('MOUT_FAMILY_',1)[1].lower() in rel.lower():
    parent=candidate;holds+=by_id[candidate].get('hold_reasons',[]);break
 if not existing:holds+=['native_supply_qualification_pending','manager_review_pending']
 # Serialized package paths are offline dependency leads, never complete registry closure.
 with p.open('rb') as f:header=f.read(256*1024)
 hints=sorted(set(x.decode('ascii') for x in re.findall(rb'/(?:Game|Engine|Script)/[A-Za-z0-9_/]+',header)))
 entries[key]={'asset_id':aid,'row_name':rn,'category':cat,'source_pack':pack,'source_id':sid,'source_file':str(p),'source_relative_file':rel,'source_object_path':op,'source_sha256':digest,'target_object_path':target,'listing_id':listing,'family_id':family or pack+'__'+re.sub(r'_(?:NN|LP|LOD\d+)$','',p.stem,flags=re.I),'quality_alternatives':variant_paths or [],'existing_canonical_identity':bool(existing),'canonical_hash_aliases':aliases,'existing_supplier_job':(old.get(key) or {}).get('job_id'),'source_family_parent_id':parent,'hold_reasons_preserved':sorted(set(holds)),'proposed_role':existing.get('request_role') if existing else role,'proposed_style':existing.get('environment_style_set') if existing else ('regional_review_required_'+pack.lower()),'licence_basis':'OWNER_CONFIRMED_FOR_TECHNICAL_PREPARATION_2026_10_06','exact_acquisition_licence_document':'pending_owner_check','selection_changed':False,'native_imported_this_run':False,'native_class':'filename_candidate_pending_registry_verification','source_status':'file_present_hash_recorded','triangles':None,'LODs':None,'collision':None,'materials_bound':None,'textures_resolved':None,'bounds_cm':None,'serialized_reference_hints_not_closure':hints,'native_dependency_check':'pending_lease'}

# Retain all initial proposal identities.
for r in first:
 project=ROOT if r['source_id']=='Current' else PROJECTS/('GIS_WorldBLD' if r['source_id']=='GISWorldBLD' else r['source_id'])
 add(r['source_id'],project,r['source_relative_file'],r['source_relative_file'].split('/')[0] if r['source_id']!='CitySample' else 'CitySample',r['source_pack_listing_id'],r['family_id'])

specs=[('GISWorldBLD',PROJECTS/'GIS_WorldBLD','MOUT_Arabian','2f06f74d-db49-4ce9-83e5-0f08e51af597'),('GISWorldBLD',PROJECTS/'GIS_WorldBLD','Light_Foliage','30e6c98c-6634-4b7e-b142-2c3cdfde6e1e'),('GISWorldBLD',PROJECTS/'GIS_WorldBLD','RockEnv_Pack','06a642fd-6639-4831-9230-18c91cae5ec2'),('Current',ROOT,'Palms_Pack_01','9f81069d-877c-4d4e-aa28-30f5d1a8d8c9'),('Current',ROOT,'UtopianCity','1e9f098e-5157-4cbf-b8a0-803eda37474b'),('Current',ROOT,'HighPoly_Tree_Model','2f1f43fe-fd59-42ff-967d-c8eb1a0785e7'),('Current',ROOT,'ModularCourtyard','ecd3dc8a-5888-4421-91b5-a18390ed4828'),('Current',ROOT,'ProceduralBuildingGenerator','783058bc-1afc-472a-96b1-289ad13c6aa9')]
useful=('bench','trash','bin','fence','railing','awning','lamp','tank','antenna','aircond','ac_','pole','hydrant','bollard','barrier','pallet','crate','dumpster','sign','rubbish','grass','plant','bush','tree','rock','stone')
for sid,project,pack,listing in specs:
 for p in sorted((project/'Content'/pack).rglob('*.uasset')):
  rel=p.relative_to(project/'Content').as_posix();low=rel.lower()
  if not p.stem.startswith('SM_') and not (pack=='ProceduralBuildingGenerator' and '/Meshes/' in rel):continue
  if pack=='MOUT_Arabian' and '/Meshes/Props/' not in rel:continue
  if pack=='RockEnv_Pack' and p.parent.name not in ['Rocks','Small_Rocks','Mesa_Rocks','Cliff_Rocks']:continue
  if pack in ['UtopianCity','ModularCourtyard','ProceduralBuildingGenerator'] and not any(k in p.stem.lower() for k in useful):continue
  if any(k in low for k in ['/materials/','/textures/','/demo/','road','sidewalk','curb']):continue
  add(sid,project,rel,pack,listing)

city=PROJECTS/'CitySample'
for p in sorted((city/'Content/Prop').rglob('*.uasset')):
 rel=p.relative_to(city/'Content').as_posix()
 if '/Mesh/' not in rel or not p.stem.startswith(('SM_','Tree_','Border_')):continue
 if not any(k in p.stem.lower() for k in useful) and not p.stem.startswith('Tree_'):continue
 if any(k in p.stem.lower() for k in ['sidewalk','road_','curb','treebase']):continue
 add('CitySample',city,rel,'CitySample','4898e707-7855-404b-af0e-a505ee690e68')

# New acquisitions: distinct geometry varieties; LP/NN quality versions grouped under one identity.
for key in ['greasewood','giant_reed','phoenix_palms','desert','namaqualand']:
 receipt_file=HERE/'OwnedPackSources'/key/'SOURCE_RECEIPT.json'
 if not receipt_file.exists():excluded.append({'pack':key,'reason':'staging_receipt_not_complete'});continue
 receipt=read(receipt_file)
 if receipt['status']!='SOURCE_STAGED_HASH_VERIFIED_NOT_NATIVE_IMPORTED':continue
 listing=(receipt.get('listing_url') or '').split('/')[-1];project=HERE/'OwnedPackSources'/key
 groups=collections.defaultdict(list)
 for f in receipt['files']:
  rel=f['relative_path'][8:];name=Path(rel).stem;low=rel.lower()
  if not rel.endswith('.uasset'):continue
  if key=='greasewood':ok=name.startswith('GW_Cluster_')
  elif key=='giant_reed':ok=name.endswith('_SM') and '/Meshes/' in rel
  elif key=='phoenix_palms':ok=name.startswith('SM_Palm_02_')
  elif key=='desert':ok=name.startswith('SM_') and any(x in rel for x in ['/Plants/','/Rocks/','/OuterLandscapes/'])
  else:ok=name.startswith('SM_') and any(x in rel for x in ['/Foliage/','/General/'])
  if not ok:continue
  family=re.sub(r'_(NN|LP)$','',name)
  groups[family].append(rel)
 for family,rels in groups.items():
  # Preserve NN geometry as primary where present; actual LOD/collision approval remains native.
  rel=sorted(rels,key=lambda r:(0 if r.endswith('_NN.uasset') else 1,r))[0]
  add('Fab_'+listing[:8],project,rel,key,listing,family,[str(safe_file(project/'Content',r)) for r in rels if r!=rel])

# Preserve identities even where several source aliases exist; do not double-count aliases.
unique={};aliases=[]
for r in entries.values():
 if r['asset_id'] in unique:aliases.append({'asset_id':r['asset_id'],'source_file':r['source_file']});continue
 unique[r['asset_id']]=r
queue=sorted(unique.values(),key=lambda r:({'Trees':0,'Bushes and shrubs':1,'Grass and understory':2,'Stones and rocks':3,'Street props':4,'Hosted and boundary props':5,'Mountain backdrops':6}.get(r['category'],9),r['source_pack'],r['asset_id']))
assert len({r['target_object_path'] for r in queue})==len(queue)
assert all(r['target_object_path'].startswith('/Game/Project/Shared/ModelBank/') for r in queue)
counts=dict(collections.Counter(r['category'] for r in queue));packs=dict(collections.Counter(r['source_pack'] for r in queue))
summary={'utc':datetime.now(timezone.utc).isoformat(),'status':'SOURCE_SUPPLY_PREPARED_NATIVE_LEASE_REQUIRED','catalog_baseline_sha256':baseline,'model_candidates':len(queue),'categories':counts,'source_packs':packs,'new_candidate_ids':sum(not r['existing_canonical_identity'] for r in queue),'existing_canonical_ids_reused':sum(r['existing_canonical_identity'] for r in queue),'native_imports':0,'selection_changes':0,'quality_alternatives_not_counted_twice':sum(len(r['quality_alternatives']) for r in queue),'source_aliases_not_counted_twice':len(aliases),'named_holds_excluded':sum(x.get('reason')=='named_hold_preserved' for x in excluded),'staging_incomplete':[x for x in excluded if x.get('reason')=='staging_receipt_not_complete'],'licence_status':'Owner confirms licences; exact acquisition document follow-up retained. No named or catalogue hold release.'}
write('EXPANDED_SUPPLY_QUEUE.json',{'summary':summary,'rows':queue,'source_aliases':aliases,'excluded':excluded})

patch=[];fields=list(catalog['rows'][0]['runtime'])
for b in queue:
 existing=by_id.get(b['asset_id'])
 r=dict(existing['runtime']) if existing else {k:'' for k in fields}
 if not existing:
  for k in fields:
   if k.endswith('Cm') or k in ['SelectionWeight','PreviewWeight']:r[k]='0.0'
  r.update(Name=b['row_name'],SchemaVersion='3',AssetId=b['asset_id'],ObjectPath=b['target_object_path'],Role=b['proposed_role'],VariantId=Path(b['source_file']).stem,RunEligible='false',BoundsValid='false',AnchorValid='false',OrientationValid='false',FamilyId=b['family_id'],StyleSet=b['proposed_style'],SelectionWeight='0.0',PlacementScope='none',RequestRole=b['proposed_role'],PlacementRule={'tree':'terrain_tree','shrub':'terrain_shrub','understory':'terrain_understory','small_prop':'zone_ground_prop','street_pole':'roadside_pole','street_prop':'roadside_prop'}.get(b['proposed_role'],''),TechnicalPreviewEligible='false',ExplicitHold='true',PreviewWeight='0.0',HoldReasons='|'.join(b['hold_reasons_preserved']))
 patch.append({'operation':'retain_existing_row_no_change_pending_native_review' if existing else 'propose_new_held_row_unmeasured','asset_id':b['asset_id'],'proposed_bank_copy':b['target_object_path'],'runtime_row':r})
write('EXPANDED_CATALOG_PATCH_PROPOSAL.json',{'apply_authorized':False,'state':'UNMEASURED_PROPOSAL_DO_NOT_APPLY','target_table':catalog['native_data_table_package'],'catalog_baseline_sha256':baseline,'rows':patch,'note':'Existing runtime rows are preserved verbatim. New rows stay held, disabled and unmeasured. No profile pins or source catalogue writes.'})
assert sha(catalog_path)==baseline,'Canonical catalogue changed concurrently; rebase required'
write('EXPANSION_SUMMARY.json',summary)
print(json.dumps(summary,indent=2))
