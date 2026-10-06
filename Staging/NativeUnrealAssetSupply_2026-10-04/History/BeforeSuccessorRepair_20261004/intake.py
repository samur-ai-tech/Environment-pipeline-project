"""Offline native supplier. Writes only its own staging directory; no Unreal import.

Names are discovery hints, never class, contact, style or eligibility evidence.
Rebuilds a deterministic queue while preserving separate native receipts.
"""
from pathlib import Path
import collections
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CATALOG = ROOT / 'Staging/ModelBank/PermanentIntegration_2026-10-02/catalog_v4_source.json'
PREP = ROOT / 'Staging/BankPreparation_2026-10-04/PREPARED_BANK.json'
BANK = ROOT / 'Staging/BankIntegration_2026-10-04'

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def write(name, data):
    p = (HERE / name).resolve()
    assert p.is_relative_to(HERE)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
    tmp.replace(p)

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def obj(relative):
    p = Path(relative)
    return '/Game/' + p.with_suffix('').as_posix() + '.' + p.stem

def hints(p):
    # Serialized names provide leads only. Registry closure must be measured by writer.
    with p.open('rb') as f:
        head = f.read(4*1024*1024)
    return sorted(set(x.decode('ascii') for x in re.findall(rb'/(?:Game|Engine|Script)/[A-Za-z0-9_/]+', head)))

def classify(path, fallback):
    s = path.lower()
    if 'roof' in s and any(t in s for t in ('ac_', 'vent', 'exhaust', 'tank', 'compressor')): return 'roof_hosted_utility'
    if 'airconditioning' in s: return 'wall_hosted_utility'
    if any(t in s for t in ('railing', 'fence')): return 'linear_boundary'
    if 'sign' in s: return 'sign_hosted'
    if any(t in s for t in ('garage', 'loading')): return 'warehouse_loading_opening'
    if 'warehouse_building' in s: return 'whole_warehouse'
    if 'corner' in s: return 'modular_corner'
    if any(t in s for t in ('door', 'entrance')): return 'modular_entrance'
    if any(t in s for t in ('window', 'glaz')): return 'modular_glazing'
    if 'roof' in s: return 'modular_roof'
    if 'wall' in s: return 'modular_straight'
    return fallback

def selected():
    specs = [
        ('Current', ROOT, 'Warehouse_Building/StaticMeshes', 'whole_warehouse', 'source_warehouse_style_unreviewed'),
        ('Current', ROOT, 'AssetsvilleTown/Meshes/BuildingTilset', 'modular_straight', 'stylized_town'),
        ('Current', ROOT, 'ModularBuildingSet/Meshes/Store_fronts', 'modular_glazing', 'source_modular_building_style_unreviewed'),
        ('Current', ROOT, 'ModularBuildingSet/Meshes/Store_fronts_doors', 'modular_entrance', 'source_modular_building_style_unreviewed'),
        ('Current', ROOT, 'ModularBuildingSet/Meshes/Roof_Trims', 'modular_roof', 'source_modular_building_style_unreviewed'),
        ('Current', ROOT, 'ModularBuildingSet/Meshes/Building_Deco', 'wall_hosted_utility', 'source_modular_building_style_unreviewed'),
        ('Current', ROOT, 'ProceduralBuildingGenerator/Meshes/Entrance_Door', 'modular_entrance', 'source_procedural_building_style_unreviewed'),
        ('Current', ROOT, 'StarterContent/Materials', 'surface_material', 'generic_physical_surface_unreviewed'),
        ('Current', ROOT, 'Palms_Pack_01/Add_Props/Grass/Meshes', 'understory', 'source_vegetation_species_unreviewed'),
        ('Current', ROOT, 'Palms_Pack_01/Add_Props/Plants/Meshes', 'understory', 'source_vegetation_species_unreviewed'),
    ]
    city = ROOT.parent/'CitySample'
    for folder, role in [
        ('Kit_bench_RR','street_prop'), ('Kit_Trashcan_A','street_prop'),
        ('Kit_Railing_A','linear_boundary'), ('Kit_Railing_B','linear_boundary'),
        ('Kit_roof_AC_Unit_B','roof_hosted_utility'), ('Kit_roof_AC_Unit_C','roof_hosted_utility'),
        ('Kit_roof_Exhaust_A','roof_hosted_utility'), ('Kit_roof_tank_a_RR','roof_hosted_utility'),
        ('Kit_BusStopSign_A','sign_hosted'), ('Kit_Tree_Alder','tree'), ('Kit_Tree_Birch','tree'),
    ]:
        specs.append(('CitySample',city,'Prop/'+folder,role,'CitySample_North_American_source_not_Gaza_qualified'))
    for folder in ['Building/SF/A/Kit_Bldg_SFA_L1_A','Building/SF/A/Kit_Bldg_SFA_L2_A','Building/SF/A/Kit_Bldg_SFA_L9_A']:
        specs.append(('CitySample',city,folder,'modular_straight','CitySample_SF_A_source_not_Gaza_qualified'))
    specs += [('CitySample',city,'Megascans/3D_Assets','small_prop','individual_scan_context_unreviewed')]
    gis = ROOT.parent/'GIS_WorldBLD'
    specs += [('GISWorldBLD',gis,'Light_Foliage/Meshes','vegetation','source_species_and_climate_unreviewed'),
              ('GISWorldBLD',gis,'Megaplant_Library/Tree_Goat_Willow','tree','goat_willow_source_label_not_botanical_validation')]
    result = {}
    for sid, project, folder, role, style in specs:
        for p in sorted((project/'Content'/folder).rglob('*.uasset')):
            rel = p.relative_to(project/'Content').as_posix()
            low = rel.lower()
            if sid != 'Current' and not ('/mesh/' in low or '/meshes/' in low or p.stem.startswith(('SM_','S_'))): continue
            if any(v in low for v in ('/decal/','/blueprint','_decal','/maps/','/map/','primitive')): continue
            if folder.endswith('BuildingTilset') and not any(v in p.stem.lower() for v in ('garage','metal','roof')): continue
            if folder == 'StarterContent/Materials' and not any(v in p.stem for v in ('Concrete','Ground','Brick','Metal_Rust','Rock_Sandstone')): continue
            result[(sid,rel)] = (sid,project,p,rel,classify(rel,role) if role!='surface_material' else role,style)
    return list(result.values())

def build():
    catalog = read(CATALOG)
    records = catalog['rows']
    by_path = {r.get('runtime',{}).get('ObjectPath'):r for r in records if r.get('runtime',{}).get('ObjectPath')}
    by_hash = collections.defaultdict(list)
    for r in records:
        for h in {r.get('asset_revision_sha256',''),r.get('runtime',{}).get('AssetRevision','')}:
            if h: by_hash[h.lower()].append(r)
    prepared = {r['asset_id']:r for r in read(PREP)['rows']}
    bank_jobs = {j['object_path']:j for j in read(BANK/'NATIVE_CONFIGURATIONS.json')['rows']}
    r020 = {j['native_path']:j for j in read(BANK/'R020_NATIVE_CONTENT_CONTRACTS.json')['jobs']}
    # Full path/size index is cheap; byte-hash only size-matching candidates.
    current = list((ROOT/'Content').rglob('*.uasset'))
    sizes = collections.defaultdict(list)
    for p in current: sizes[p.stat().st_size].append(p)
    hash_cache = {}
    jobs = []
    for sid, project, p, relative, role, style in selected():
        digest = sha(p)
        source_obj = obj(relative)
        exact = ROOT/'Content'/relative
        target = source_obj if sid=='Current' else None
        aliases = []
        if sid!='Current':
            candidates = ([exact] if exact.is_file() else []) + sizes[p.stat().st_size]
            for native in dict.fromkeys(candidates):
                if native not in hash_cache: hash_cache[native] = sha(native)
                if hash_cache[native] == digest:
                    aliases.append(obj(native.relative_to(ROOT/'Content')))
            if aliases: target = sorted(aliases, key=lambda x:(x!=source_obj,x))[0]
        canonical = by_path.get(target)
        hash_matches = {r['asset_id']:r for r in by_hash[digest]}
        if not canonical and len(hash_matches)==1:
            canonical = next(iter(hash_matches.values()))
        aid = canonical['asset_id'] if canonical else 'native.'+sid+'.'+hashlib.sha256((sid+'/'+relative).encode()).hexdigest()[:24]
        jid = 'NU_' + hashlib.sha256((sid+'/'+relative).encode()).hexdigest()[:20]
        native_evidence = r020.get(target)
        prep = prepared.get(aid,{})
        held = canonical.get('hold_reasons',[]) if canonical else ['native_supply_qualification_pending']
        intended = target or '/Game/Project/Shared/ModelBank/Prepared/NativeUnreal/'+sid+'/'+relative[:-7]+'.'+p.stem
        jobs.append({'job_id':jid,'source_id':sid,'source_project':str(project),
            'source_file':str(p),'source_relative_file':relative,'source_object_path':source_obj,
            'source_sha256':digest,'source_bytes':p.stat().st_size,
            'asset_id':aid,'canonical_existing':bool(canonical),
            'catalog_row_name':canonical['catalog_row_name'] if canonical else 'MB_'+hashlib.md5(aid.encode()).hexdigest().upper(),
            'deduplication':{'exact_native_path':target,'byte_identical_current_paths':aliases,'canonical_hash_matches':sorted(hash_matches)},
            'operation':'reference_existing' if target else 'native_migrate_with_dependency_remap',
            'native_object_path':target,'target_object_path':intended,
            'requested_role_candidate':role,'role_basis':'path_triage_requires_native_geometry_and_visual_review',
            'source_style':canonical.get('environment_style_set',style) if canonical else style,
            'rights_state':canonical.get('recorded_rights_state') if canonical else 'acquisition_and_terms_unverified',
            'explicit_hold_preserved':canonical['runtime']['ExplicitHold'] if canonical else 'true',
            'hold_reasons_preserved':held,'serialized_reference_hints_not_closure':hints(p),
            'existing_bank_job':bool(target in bank_jobs),'existing_r020_evidence':str(BANK/'R020_NATIVE_CONTENT_CONTRACTS.json') if native_evidence else None,
            'existing_measurement':native_evidence.get('measurement') if native_evidence else prep.get('native_measurement'),
            'states':{'sourced':True,'native_present':bool(target),'native_imported_by_supplier':False,
                'materials_complete':False,'canonical_identity_present':bool(canonical),
                'bank_connected':bool(canonical and canonical['runtime']['ObjectPath']==target),
                'permitted_selection':str(canonical['runtime']['RunEligible']).lower()=='true' if canonical else False,
                'correct_consumer_verified':False,'actual_area_output':False,'named_persistence_verified':False},
            'status':'owner_existing_work' if target in bank_jobs or native_evidence else ('ready_native_inspection' if target else 'blocked_source_registry_and_namespace_remap'),
            'blockers':[] if target else ['source_dependency_closure_not_native_measured','source_engine_compatibility_not_verified','supported_namespace_remap_requires_owner_contract'],
        })
    assert len({j['job_id'] for j in jobs})==len(jobs)
    sources = []
    for sid,project in [('Current',ROOT),('CitySample',ROOT.parent/'CitySample'),('GISWorldBLD',ROOT.parent/'GIS_WorldBLD'),('MyProject58',ROOT.parent/'MyProject 5.8')]:
        up = next(project.glob('*.uproject'),None)
        d = read(up) if up else {}
        sources.append({'source_id':sid,'project':str(project),'uproject':str(up),'uproject_sha256':sha(up) if up else None,
            'engine_association':d.get('EngineAssociation'),'project_modules':d.get('Modules',[]),'enabled_project_plugins':[x['Name'] for x in d.get('Plugins',[]) if x.get('Enabled')],
            'plugins_required_by_selected_assets':'unknown_until_native_dependency_closure; project_enabled_plugins_are_not_asset_requirements',
            'content_roots_present':sorted(x.name for x in (project/'Content').iterdir() if x.is_dir()),
            'startup_hooks_or_maps_to_import':[],'source_write_authorized':False})
    summary = {'jobs':len(jobs),'by_status':dict(collections.Counter(j['status'] for j in jobs)),
        'by_source':dict(collections.Counter(j['source_id'] for j in jobs)),
        'by_role':dict(collections.Counter(j['requested_role_candidate'] for j in jobs)),
        'canonical_existing':sum(j['canonical_existing'] for j in jobs),
        'unique_new_identity_candidates':len({j['asset_id'] for j in jobs if not j['canonical_existing']})}
    queue={'schema':'environmentpipeline.native_unreal_supply_queue.v1','catalog_source':str(CATALOG),
        'catalog_sha256':sha(CATALOG),'canonical_rows_at_read':len(records),'summary':summary,
        'default_entrypoint':'native_supplier.inspect(job_ids) by the designated bank writer only',
        'ordinary_generation_authorized':False,'jobs':jobs}
    write('READY_JOBS.json',queue)
    write('SOURCES.json',{'sources':sources,'vault_paths_checked':[{'path':str(p),'exists':p.exists()} for p in [Path('C:/ProgramData/Epic/EpicGamesLauncher/VaultCache'),Path('C:/Program Files (x86)/Epic Games/Launcher/VaultCache'),Path('C:/Program Files/Epic Games/Launcher/VaultCache')]],'vault_catalog_claim':'No payload assumed from a product or folder name; no downloads requested.'})
    print(json.dumps(summary))
    return queue

if __name__=='__main__': build()
