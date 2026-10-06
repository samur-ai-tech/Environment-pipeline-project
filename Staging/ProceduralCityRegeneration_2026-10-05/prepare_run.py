"""Preserve the existing city and resolve verified derived-only dirty function state."""
import unreal,json,pathlib,shutil,hashlib,re,sys,runpy
ROOT=pathlib.Path(__file__).parent;PROJECT=ROOT.parents[1]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def graph(text):return '\n'.join(l for l in text.splitlines() if not re.match(r'\s*(StateId|CombinedInputTypes|CombinedOutputTypes)=',l))
def run():
    import geocity_runtime_guard,geocity_editor_action
    verified=geocity_runtime_guard.verify();api=unreal.HoudiniPublicAPIBlueprintLib.get_api()
    assert api.is_session_valid() and api.is_asset_cooking_paused()
    assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert 'OWNER=NONE' in (PROJECT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text().strip().splitlines()[-1]
    rows=json.loads((ROOT/'DIRTY_MATERIAL_COMPARISON.json').read_text())
    export=runpy.run_path(str(ROOT/'inspect_dirty_materials.py'))['export'];saved=[]
    for row in rows:
        path=row['package'];name=path.rsplit('/',1)[-1];a=(ROOT/'Before'/(name+'_loaded.t3d')).read_text();b=(ROOT/'Before'/(name+'_disk.t3d')).read_text().replace('/Game/Project/Shared/Recovery/ProceduralCity_20261005/DiskFunctions/','/Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/')
        assert graph(a)==graph(b),name+' contains non-derived edits'
        source=PROJECT/'Content'/(path[6:]+'.uasset');assert sha(source)==row['disk_sha256']
        asset=unreal.load_asset(path);export(asset,ROOT/'Before'/(name+'_pre_save.t3d'));assert graph((ROOT/'Before'/(name+'_pre_save.t3d')).read_text())==graph(a)
        assert unreal.EditorAssetLibrary.save_loaded_asset(asset,only_if_is_dirty=True)
        export(asset,ROOT/'Before'/(name+'_saved.t3d'));assert graph((ROOT/'Before'/(name+'_saved.t3d')).read_text())==graph(a)
        saved.append({'package':path,'original_disk_sha256':row['disk_sha256'],'saved_sha256':sha(source),'material_graph_unchanged':True})
    profile_path=PROJECT/'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json';profile=json.loads(profile_path.read_text())
    assert profile['roadbld_workflow']['enabled'] is False and profile['road_provider_contract']['saved'] is True
    backup=ROOT/'Before/City';backup.mkdir(exist_ok=True)
    paths=[profile_path,pathlib.Path(profile['workflow_receipt']),pathlib.Path(profile['catalog_receipt']),PROJECT/'Content'/(profile['map'][6:]+'.umap')]
    paths.extend(pathlib.Path(profile['workflow_receipt']).parent.glob('LAST_SUCCESSFUL*'))
    backups=[]
    for path in paths:
        if path.exists():
            dest=backup/path.name;assert not dest.exists();shutil.copy2(path,dest);backups.append({'path':str(path),'backup':str(dest),'sha256':sha(path)})
    dirty=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
    assert set(dirty).issubset(geocity_editor_action.acknowledged_cook_leftovers(PROJECT,dirty))
    state={'world':unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name(),'profile':str(profile_path),'backups':backups,'derived_material_state_saved':saved,'dirty_acknowledged':dirty,'runtime_sources':verified,'official_engine_valid':True,'roads_reused':True}
    write(ROOT/'PREPARATION.json',state);return {'ready':True,'derived_only_packages_saved':len(saved),'city_backups':len(backups),'dirty_acknowledged':dirty}
