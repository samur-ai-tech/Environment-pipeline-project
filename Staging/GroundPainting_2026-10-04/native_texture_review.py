"""Read-only export and settings for the four currently used native texture sets."""
import datetime,json,os
from pathlib import Path
import unreal,geocity_runtime_guard
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve();HERE=ROOT/'Staging/GroundPainting_2026-10-04'
lease=[s for s in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1]
assert 'OWNER=CODEX_GROUND_PAINTING' in lease and f'assigned_editor_PID={os.getpid()} ' in lease
geocity_runtime_guard.verify();assert unreal.HoudiniPublicAPIBlueprintLib.get_api().is_asset_cooking_paused()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() and not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
def safe(o,k):
 try:return str(o.get_editor_property(k))
 except Exception:return None
outdir=HERE/'Revision_2026-10-05'/'TextureReview';outdir.mkdir(exist_ok=True)
result={}
for name in ('Sand_01','Sand_02','Dirt_Path_01','Sand_Path_01'):
 for channel in ('Albedo','Normal','Mask'):
  p=f'/Game/MOUT_Arabian/Textures/Landscape/{name}/T_{name}_{channel}';t=unreal.load_asset(p);assert isinstance(t,unreal.Texture2D)
  row={'path':t.get_path_name(),'settings':{k:safe(t,k) for k in ('srgb','compression_settings','lod_group','mip_gen_settings','never_stream')}}
  if channel in ('Albedo','Mask'):
   dst=outdir/f'T_{name}_{channel}.tga';assert not dst.exists()
   task=unreal.AssetExportTask();task.set_editor_property('object',t);task.set_editor_property('filename',str(dst));task.set_editor_property('automated',True);task.set_editor_property('prompt',False);task.set_editor_property('replace_identical',False);task.set_editor_property('exporter',unreal.TextureExporterTGA())
   assert unreal.Exporter.run_asset_export_task(task),p;row['export']=str(dst)
  result[p]=row
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() and not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
out=HERE/'Revision_2026-10-05'/f'TEXTURE_REVIEW_PID{os.getpid()}.json';out.write_text(json.dumps(result,indent=2),encoding='utf-8')
RESULT={'receipt':str(out),'textures':result}
