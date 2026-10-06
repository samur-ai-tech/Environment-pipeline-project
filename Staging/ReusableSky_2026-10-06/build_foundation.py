import json, dataclasses
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.actor import ActorTools as AT
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
path='/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky'
assert not unreal.EditorAssetLibrary.does_asset_exist(path), 'Asset already exists; inspect before altering'
bp=unreal.EditorAssetLibrary.duplicate_asset('/SunPosition/SunSky',path)
assert bp
# Retained derivative: native components copied into this project asset, no live child SunSky solver.
for name in BP.list_variables(bp): BP.set_variable_instance_editable(bp,name,False)
definitions=[('TimeOfDay','float','01 Time and Sun'),('ManualSun','bool','01 Time and Sun'),('ClockDisplay','string','01 Time and Sun'),('ManualDirection','float','03 Manual Sun'),('ManualElevation','float','03 Manual Sun'),('RigEnabled','bool','00 Activation'),('Status','string','00 Activation'),('SunIntensity','float','04 Lighting'),('SkyIntensity','float','04 Lighting'),('OverrideExposure','bool','05 Exposure'),('ExposureEV100','float','05 Exposure')]
for name,typ,cat in definitions:
 BP.add_variable(bp,name,typ);BP.set_variable_instance_editable(bp,name,True);BP.set_variable_category(bp,name,cat)
for name in ['Latitude','Longitude','TimeZone','Year','Month','Day','UseDaylightSavingTime','NorthOffset']:
 BP.set_variable_instance_editable(bp,name,True);BP.set_variable_category(bp,name,'02 Date Location and North')
BP.compile_blueprint(bp)
pp=AT.add_component(bp,unreal.PostProcessComponent.static_class(),'ExposureOverride')
pp.set_editor_property('enabled',False)
pp.set_editor_property('unbound',True)
pp.set_editor_property('blend_weight',0.0)
pp.set_editor_property('priority',0.0)
arrow=AT.add_component(bp,unreal.ArrowComponent.static_class(),'NorthArrow')
arrow.set_editor_property('hidden_in_game',True)
BP.compile_blueprint(bp)
g=BP.get_graph(bp,'UpdateSun')
queries=['GetSunPosition','BreakSunPosition','SetWorldRotation','SetVisibility','SetIntensity','ToText(Integer)','Append','SetClock','SetStatus','GetAllActorsOfClass','GetComponentsByClass','GetOwner','SetSettings','SetBlendWeight','DaysInMonth','Clamp','SetNorth','GetNorth','SetSolar','SetPostProcess','SetEnabled','GetTimeOfDay']
nodes={q:BP.find_node_types(g,q) for q in queries}
(root/'NODE_TYPES.json').write_text(json.dumps(nodes,indent=2))
props={}
for name in ['new_variables','NewVariables']:
 try:
  arr=bp.get_editor_property(name)
  props[name]=[{'repr':str(x),'fields':[n for n in dir(x) if not n.startswith('_')]} for x in list(arr)[:1]]
 except Exception as e:props[name]=str(e)
RESULT={'asset':bp.get_path_name(),'node_types':nodes,'var_struct':props,'metadata_classes':[n for n in dir(unreal) if 'Variable' in n and ('Meta' in n or 'Description' in n)],'cdo_properties':[n for n in dir(unreal.get_default_object(bp.generated_class())) if any(k in n.lower() for k in ['time','sun','direction','north','exposure'])]}
