"""Prepare retained bank work queues. Never write canonical catalogs or vendor files."""
import csv, hashlib, json, pathlib, collections
from datetime import datetime, timezone
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent
SOURCE_OUT = pathlib.Path('C:/Users/USER/Documents/Pipeline Environment/ModelBank/Prepared_2026-10-04')
SOURCE_OUT.mkdir(parents=True, exist_ok=True)
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name, value): (OUT/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
index = list(csv.DictReader((ROOT/'Staging/ModelBank/BANK_CANDIDATE_INDEX_2026-09-29.csv').open(encoding='utf-8-sig')))
catalog_path = ROOT/'Staging/ModelBank/PermanentIntegration_2026-10-02/catalog_v4_source.json'
catalog=read(catalog_path)
jobs=[]
for row in index:
    p=pathlib.Path(row['source_path'])
    if row['source_scope']!='external' or row['category']=='Buildings/Modules' or p.suffix.lower()!='.fbx' or row['record_kind']!='asset_candidate': continue
    # Existing archive reports identify exact reusable .blend and texture dependencies.
    source_root=p.parents[2]
    report_path=source_root/'Reports'/(row['asset_id'].split('.')[-1][1:]+'.json')
    report=read(report_path) if report_path.is_file() else {}
    blend=source_root/report.get('blend','MISSING')
    jobs.append({**{k:row[k] for k in ('asset_id','family_id','name','category','representation','source_package','rights_state')},
        'source_fbx':str(p),'source_fbx_sha256':sha(p),
        'source_blend':str(blend) if blend.is_file() else None,
        'source_report':str(report_path) if report_path.is_file() else None,
        'source_root':str(source_root),'output_dir':str(SOURCE_OUT/row['asset_id'].replace('.','_'))})
jobs.sort(key=lambda r: (r['category']=='Buildings/Whole',r['category'] in ('Signs','Utility/RooftopProps'),r['asset_id']))
write('BLENDER_QUEUE.json',jobs)
protected=[catalog_path,ROOT/'Staging/ModelBank/PermanentIntegration_2026-10-02/catalog_v4_full.csv',ROOT/'Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json',ROOT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json',ROOT/'Content/Python/geocity_bank_workflow.py',pathlib.Path('C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank/geocity_city_module.py')]
write('BASELINE.json',{'recorded_utc':datetime.now(timezone.utc).isoformat(),'files':{str(p):sha(p) for p in protected},'catalog_rows':len(catalog['rows']),'blender_queue':len(jobs),'existing_blend_sources':sum(bool(x['source_blend']) for x in jobs)})
write('ASSIGNMENT.json',{'schema':'environmentpipeline.bank_preparation.v1','thread':'01a10653-ec52-77b2-abbf-91441ce8b7f9','authorization':'Aviv resumed implementation 2026-10-04: entire bank, first existing props and whole buildings needing measurement/configuration; modular authoring follows later.','owned_directories':[str(OUT),str(SOURCE_OUT)],'editor_owner_observed':'CODEX_NEW_AREA PID30812; no editor calls or competing launch','phase':'nonmodular_batch_preparation','preserve':['original sources','canonical identities','named holds','declined palms','canonical rights and eligibility','system-owned source and area profiles'],'modular_authoring':'deferred until this phase is complete','native_integration':'handoff payload until exclusive editor ownership permits actual import/readback/named save'})
print(json.dumps({'queue':len(jobs),'existing_blends':sum(bool(x['source_blend']) for x in jobs),'categories':dict(collections.Counter(x['category'] for x in jobs))}))
