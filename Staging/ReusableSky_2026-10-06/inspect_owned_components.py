import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.actor import ActorTools as AT
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
objects=[]
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
 d=unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
 o=unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(d,bp)
 if o:
  p={'name':o.get_name(),'class':o.get_class().get_name()}
  for key in ['visible','intensity','real_time_capture','mobility','bHiddenInGame','bIsEditorOnly','bEnabled']:
   try:p[key]=str(o.get_editor_property(key))
   except Exception:pass
  objects.append(p)
g=BP.get_graph(bp,'UpdateSky')
export=unreal.AssetExportTask();export.object=bp;export.exporter=unreal.ObjectExporterT3D();export.filename=str(root/'BP_CURRENT.t3d');export.automated=True;export.prompt=False;export.replace_identical=True
ok=unreal.Exporter.run_asset_export_task(export)
node=BP.create_node(g,'Utilities|Struct|MakePostProcessSettings',unreal.IntPoint(0,0))
opts=node.get_editor_property('ShowPinForProperties')
for opt in opts:
 if str(opt.get_editor_property('PropertyName')) in ['AutoExposureMinBrightness','AutoExposureMaxBrightness']:
  opt.set_editor_property('bShowPin',True)
node.set_editor_property('ShowPinForProperties',opts)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
info=BP._get_node_info(node)
RESULT={'components':objects,'export_ok':ok,'exposure_node':node.get_path_name(),'exposure_pins':[(p.name,p.type_id) for p in info.input_pins],'node_props':unreal.ToolsetLibrary.list_struct_properties(node.get_class()),'graph_edit':dir(unreal.BlueprintGraphEditor)}
