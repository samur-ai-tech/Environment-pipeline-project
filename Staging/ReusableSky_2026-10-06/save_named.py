import json,hashlib,os
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
asset='/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky'
bp=unreal.load_asset(asset)
g=BP.get_graph(bp,'UpdateSky')
# The north arrow is an editor-only aid; it does not appear in game.
code=(root/'UpdateSky.dsl').read_text().replace('Runtime: call UpdateSun','Runtime: call UpdateSky')
arrow=[t for t in BP.find_node_types(g,'GetNorthArrow') if t.startswith('Variables|')][0]
es=[t for t in BP.find_node_types(g,'GetExposureSettings') if t.startswith('Variables|')][0]
ec=[t for t in BP.find_node_types(g,'GetExposureOverride') if t.startswith('Variables|')][0]
code=code.rstrip()[:-1]+'\n(Class|PostProcessComponent|SetSettings :self ('+ec+') :Settings ('+es+'))\n(Rendering|SetVisibility :self ('+arrow+') :bNewVisibility true)\n)'
BP.write_graph_dsl(g,code)
unreal.BlueprintGraphEditor.get_graph_editor(g).set_is_call_in_editor_function(True)
BP.compile_blueprint(bp,True)
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors=sub.get_all_level_actors();rig=[a for a in actors if a.get_class()==bp.generated_class()]
assert len(rig)==1 and len(actors)==122
a=rig[0];a.set_editor_property('TimeOfDay',12.0)
assert a.get_editor_property('Status')=='Active - Time and Location'
assert a.get_editor_property('ClockDisplay')=='12:00'
assert a.get_editor_property('ConflictActors')==''
before=json.loads((root/'SCENE_BEFORE.json').read_text())
for row in before['actors']:
 old=unreal.find_object(None,row['path']);assert old
 for c in row['components']:
  obj=unreal.find_object(None,c['path']);assert obj
  if 'intensity' in c:assert str(obj.get_editor_property('intensity'))==c['intensity']
map_path=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
assert map_path=='/Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration'
dirty=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
assert set(dirty).issubset({asset,'/SunPosition/SunSky'})
assert unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert unreal.EditorLoadingAndSavingUtils.save_map(world,map_path)
RESULT={'pid':os.getpid(),'saved':[asset,map_path],'actor':a.get_path_name(),'actor_count':len(actors),'clock':a.get_editor_property('ClockDisplay'),'status':a.get_editor_property('Status'),'north_arrow_visible':a.get_editor_property('NorthArrow').is_visible(),'dirty_content_remaining':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],'dirty_maps_remaining':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],'vendor_saved':False,'bank_saved_or_modified':False}
(root/'NAMED_SAVE.json').write_text(json.dumps(RESULT,indent=2))
sub.set_selected_level_actors([a])
