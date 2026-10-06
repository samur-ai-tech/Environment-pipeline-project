import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
g=BP.get_graph(bp,'UpdateSky')
for n in BP.find_nodes(g,node_class=unreal.K2Node_MakeStruct.static_class()):
 if 'PostProcess' in n.get_node_title():BP.delete_node(n)
BP.add_struct_variable(bp,'ExposureSettings',unreal.PostProcessSettings.static_struct())
BP.set_variable_category(bp,'ExposureSettings','05 Exposure')
BP.set_variable_instance_editable(bp,'ExposureSettings',True)
BP.remove_variable(bp,'ExposureEV100')
BP.compile_blueprint(bp)
typ=[t for t in BP.find_node_types(g,'GetExposureSettings') if t.startswith('Variables|')][0]
exp=[t for t in BP.find_node_types(g,'GetExposureOverride') if t.startswith('Variables|')][0]
code=(root/'UpdateSky.dsl').read_text().replace('Runtime: call UpdateSun','Runtime: call UpdateSky')
code=code.rstrip()[:-1]+'\n(Class|PostProcessComponent|SetSettings :self ('+exp+') :Settings ('+typ+'))\n)'
BP.write_graph_dsl(g,code)
unreal.BlueprintGraphEditor.get_graph_editor(g).set_is_call_in_editor_function(True)
cdo=unreal.get_default_object(bp.generated_class())
pp=unreal.PostProcessSettings()
pp.set_editor_property('override_auto_exposure_min_brightness',True)
pp.set_editor_property('override_auto_exposure_max_brightness',True)
pp.set_editor_property('auto_exposure_min_brightness',3.0)
pp.set_editor_property('auto_exposure_max_brightness',3.0)
cdo.set_editor_property('ExposureSettings',pp)
tick=cdo.get_editor_property('primary_actor_tick');tick.set_editor_property('start_with_tick_enabled',False);cdo.set_editor_property('primary_actor_tick',tick)
# Remove inherited unused control variables and obsolete comment-only blocks.
keep={'Latitude','Longitude','TimeZone','NorthOffset','Year','Month','Day','UseDaylightSavingTime','TimeOfDay','ManualSun','ManualDirection','ManualElevation','RigEnabled','ClockDisplay','SunIntensity','SkyIntensity','OverrideExposure','ExposureSettings','Status','ConflictActors','RuntimeNotes','CanRender','CorrectedElevation','Azimuth'}
for name in list(BP.list_variables(bp)):
 if name not in keep:BP.remove_variable(bp,name)
eg=BP.get_graph(bp,'EventGraph')
for n in unreal.BlueprintGraphEditor.get_graph_editor(eg).list_comment_nodes():
 unreal.BlueprintGraphEditor.get_graph_editor(eg).remove_comment_node(n)
BP.compile_blueprint(bp,True)
export=unreal.AssetExportTask();export.object=bp;export.exporter=unreal.ObjectExporterT3D();export.filename=str(root/'BP_FINAL.t3d');export.automated=True;export.prompt=False;export.replace_identical=True
unreal.Exporter.run_asset_export_task(export)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(bp)
RESULT={'variables':list(BP.list_variables(bp)),'compiled':True,'exposure_settings':str(cdo.get_editor_property('ExposureSettings'))}
