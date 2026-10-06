"""Read-only ground role/height and preservation evidence."""
import hashlib,json,math,os
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve();HERE=ROOT/'Staging/GroundPainting_2026-10-04'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
assignment=json.loads((HERE/'ASSIGNMENT.json').read_text());area=next(k for k,v in assignment['original_maps'].items() if v==world.get_outermost().get_path_name())
lease=[x for x in (ROOT/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip()][-1]
assert f'assigned_editor_PID={os.getpid()}' in lease and 'OWNER=CODEX_GROUND_PAINTING' in lease
result={'pid':os.getpid(),'area':area,'landscapes':[]}
for a in actors:
 if not isinstance(a,unreal.Landscape):continue
 comps=list(a.get_components_by_class(unreal.LandscapeComponent));samples=[]
 for c in comps:
  origin,extent,radius=unreal.SystemLibrary.get_component_bounds(c)
  for x in (-.7,0,.7):
   for y in (-.7,0,.7):
    loc=unreal.Vector(origin.x+x*extent.x,origin.y+y*extent.y,origin.z)
    weights={n:float(c.editor_get_paint_layer_weight_by_name_at_location(loc,n)) for n in ('Sand_01','Sand_02','Dirt_Path','Sand_Path')}
    samples.append({'xy':[loc.x,loc.y],'weights':weights})
 ignored=[b for b in actors if b!=a];heights=[]
 for x,y in [(-1268.1745794274116,2408.9167042506506),(0,0),(3584.2702876308795,-3809.2016187295335)]:
  hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,100000),unreal.Vector(x,y,-100000),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,ignored,unreal.DrawDebugTrace.NONE,False)
  fields=hit.to_dict();assert fields['blocking_hit'] and fields['hit_actor']==a
  assert isinstance(fields['hit_component'],unreal.LandscapeHeightfieldCollisionComponent)
  heights.append([x,y,float(fields['impact_point'].z)])
 result['landscapes'].append({'path':a.get_path_name(),'tags':[str(t) for t in a.tags],
  'target_layers':[str(n) for n in a.get_target_layer_names()],'weight_samples':samples,'weights_sha256':hashlib.sha256(json.dumps(samples,sort_keys=True).encode()).hexdigest(),'height_samples':heights,
  'visibility':[{'path':c.get_path_name(),'visible':c.get_editor_property('visible'),'hidden_in_game':c.get_editor_property('hidden_in_game')} for c in comps]})
grass=unreal.load_asset('/Game/Project/Shared/SurfacePainting/Appearance_20261003/LG_GeoCity_PermittedGroundGrass')
result['grass_settings_sha256']=hashlib.sha256(str(grass.get_editor_property('grass_varieties')).encode()).hexdigest()
result['grass_settings']=str(grass.get_editor_property('grass_varieties'))
out=HERE/f'{area}_{ARGS.get("label","probe")}_PROBE_PID{os.getpid()}.json';out.write_text(json.dumps(result,indent=2),encoding='utf-8')
RESULT={'receipt':str(out),'landscapes':[{'path':s['path'],'layers':s['target_layers'],'weight_digest':s['weights_sha256'],'height_samples':s['height_samples']} for s in result['landscapes']]}
