"""Authorized retained Iran generation through the normal GeoCity action."""
import unreal,json,hashlib,datetime,shutil
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir()).resolve();HERE=ROOT/'Staging/AssetBankOperator_2026-10-06'
ns={'__file__':str(HERE/'native_operator.py')};exec((HERE/'native_operator.py').read_text(),ns);ns['preflight']()
import geocity_editor_action,geocity_runtime_guard,geocity_bank_workflow
geocity_runtime_guard.verify()
profile=ROOT/'Staging/ModelBank/Iran_38196167_46086167_4km/AREA_PROFILE.json';p=json.loads(profile.read_text())
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name();assert world==p['map']
assert not any(getattr(r,k,None) is not None for r in geocity_bank_workflow.ACTIVE for k in ('watch_tick','save_tick'))
dirty=unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()+unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages();dirty_paths=[x.get_path_name() for x in dirty]
assert set(dirty_paths).issubset(geocity_editor_action.acknowledged_cook_leftovers(ROOT,dirty_paths)),dirty_paths
map_file=ROOT/'Content'/(p['map'][6:]+'.umap');backup=HERE/'Before/IRAN_MAP_BEFORE_EXPANSION.umap'
assert not backup.exists();shutil.copy2(map_file,backup)
ns['write']('Generation/IRAN_STARTED.json',{'pid':29900,'world':world,'map_before_sha256':hashlib.sha256(map_file.read_bytes()).hexdigest(),'profile_sha256':hashlib.sha256(profile.read_bytes()).hexdigest(),'profile':p,'authorization':'DIRECT_USER_ACTIVATION_29900.json','previous_dirty_acknowledged':dirty_paths})
owner=ROOT/'Staging/ModelBank/EDITOR_OWNER.txt'
with owner.open('a',encoding='utf-8') as f:f.write('\n'+datetime.datetime.now(datetime.timezone.utc).isoformat()+' OWNER=NONE released_by=ASSET_BANK_OPERATOR editor_PID=29900 next=AVIV_AUTHORIZED_ORDINARY_IRAN_GENERATION activation=Staging/AssetBankOperator_2026-10-06/DIRECT_USER_ACTIVATION_29900.json\n')
geocity_editor_action.generate_current_area()
print(json.dumps({'generation_dispatched':True,'active_phases':[r.state.get('phase') for r in geocity_bank_workflow.ACTIVE]}))
