import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
BP.remove_variable(bp,'TimeOfDay')
api=unreal.get_editor_subsystem(unreal.CppSkillApiSubsystem)
res=api.execute_blueprint_commands(bp.get_path_name(),json.dumps([{'op':'rename_variable','old_name':'SolarTime','new_name':'TimeOfDay'}]),False,False)
print('RENAME',res)
BP.set_variable_category(bp,'TimeOfDay','01 Time and Sun');BP.set_variable_instance_editable(bp,'TimeOfDay',True)
for name in ['ConflictActors','RuntimeNotes']:
 BP.add_variable(bp,name,'string');BP.set_variable_category(bp,name,'00 Activation');BP.set_variable_instance_editable(bp,name,True)
BP.compile_blueprint(bp)
g=BP.get_graph(bp,'UpdateSun')
types=['Utilities|Struct|MakePostProcessSettings','Class|PostProcessComponent|SetEnabled','Actor|GetAllActorsOfClass','Actor|GetComponentsByClass','Components|GetOwner','Rendering|IsVisible']
types += [x for q in ['GetPathName','GetDisplayName','ToString(Text)','SetRelativeRotation'] for x in BP.find_node_types(g,q)]
pins={}
for typ in types:
 i=BP.get_node_type_pins(g,typ);pins[typ]={'inputs':[(p.name,p.type_id,p.value) for p in i.input_pins],'outputs':[(p.name,p.type_id) for p in i.output_pins]}
(root/'MORE_PINS.json').write_text(json.dumps(pins,indent=2))
cdo=unreal.get_default_object(bp.generated_class())
defaults={'TimeOfDay':12.0,'ManualSun':False,'ManualDirection':180.0,'ManualElevation':35.0,'RigEnabled':False,'SunIntensity':10.0,'SkyIntensity':1.0,'OverrideExposure':False,'ExposureEV100':3.0,'Latitude':31.52,'Longitude':34.44,'TimeZone':2.0,'Year':2026,'Month':6,'Day':21,'UseDaylightSavingTime':False,'NorthOffset':0.0}
for k,v in defaults.items():cdo.set_editor_property(k,v)
RESULT={'renamed':res,'pins':{k:v for k,v in pins.items() if 'PostProcessSettings' not in k},'pp_pins_count':len(pins['Utilities|Struct|MakePostProcessSettings']['inputs']),'graph_editor_methods':[n for n in dir(unreal.BlueprintGraphEditor) if any(k in n for k in ['pin','property','export','import'])],'node_methods':[n for n in dir(unreal.K2Node_MakeStruct) if any(k in n for k in ['pin','reconstruct'])]}
