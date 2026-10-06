import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets import blueprint_dsl
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
base='/Game/Project/Shared/Atmosphere/ReusableSky/'
bp=unreal.load_asset(base+'BP_EnvironmentSky');g=BP.get_graph(bp,'UpdateSky')
def get(n):
 ts=[t for t in BP.find_node_types(g,'Get'+n) if t.startswith('Variables|') and t.endswith('|Get'+n)];assert len(ts)==1,(n,ts);return '('+ts[0]+')'
def put(n,v):
 ts=[t for t in BP.find_node_types(g,'Set'+n) if t.startswith('Variables|') and t.endswith('|Set'+n)];assert len(ts)==1,(n,ts);return '('+ts[0]+' '+v+')'
def write(graph,code):
 def create(graph,t,pos):
  cls=None
  if t=='Rendering|Material|CreateDynamicMaterialInstance':cls=unreal.MaterialLibrary.static_class()
  elif t in ['Rendering|Material|SetScalarParameterValue','Rendering|Material|SetVectorParameterValue']:cls=unreal.MaterialInstanceDynamic.static_class()
  return BP.create_node(graph,t,pos,cls)
 blueprint_dsl.Transpiler(graph,create,BP.connect_pins,BP._get_node_info,BP.set_pin_value,lambda graph:BP.find_nodes(graph),delete_node_fn=BP.delete_node,find_node_types_fn=lambda f:BP.find_node_types(graph,f)).transpile(code)
 BP.compile_blueprint(bp,True)
code=(root.parent/'UpdateSky.dsl').read_text().replace('Runtime: call UpdateSun','Runtime: call UpdateSky')
code=code.replace('(fn UpdateSky ()','(fn UpdateSky ()\n'+put('CloudAmount','(Math|Float|Clamp(Float) '+get('CloudAmount')+' 0.0 1.0)')+'\n'+put('Haze','(Math|Float|Clamp(Float) '+get('Haze')+' 0.0 1.0)'))
# Treat external active clouds as conflicts; only inspect them, never mutate them.
start=code.index('(for component (Actor|GetComponentsByClass :self other :ComponentClass "/Script/Engine.SkyAtmosphereComponent")')
end=code.index('(:CastFailed)))',start)+len('(:CastFailed)))')
cloudcheck=code[start:end].replace('SkyAtmosphereComponent','VolumetricCloudComponent')
code=code[:end]+'\n'+cloudcheck+code[end:]
sunbase='(Math|Float|Clamp(Float) '+get('SunIntensity')+' 0.0 200000.0)'
skybase='(Math|Float|Clamp(Float) '+get('SkyIntensity')+' 0.0 20.0)'
cover='(* '+get('CloudAmount')+' (* '+get('CloudAmount')+' '+get('CloudAmount')+'))'
assert sunbase in code and skybase in code
code=code.replace(sunbase,'(* '+sunbase+' (- 1.0 (* 0.88 '+cover+')))').replace(skybase,'(* '+skybase+' (- 1.0 (* 0.15 '+get('CloudAmount')+')))')
parts=[code.rstrip()[:-1]]
parts+=['(Utilities|IsValid '+get('CloudMID')+' (:"Is Valid") (:"Is Not Valid" '+put('CloudMID','(Rendering|Material|CreateDynamicMaterialInstance :Parent "'+base+'MI_EnvironmentCloudDefaults.MI_EnvironmentCloudDefaults" :OptionalName "EnvironmentCloudMID" :CreationFlags "Transient")')+'))']
parts+=['(Rendering|SetMaterial :self '+get('WeatherClouds')+' :NewValue '+get('CloudMID')+')','(Rendering|SetVisibility :self '+get('WeatherClouds')+' :bNewVisibility (and '+get('CanRender')+' (> '+get('CloudAmount')+' 0.001)))']
for n,v in [('Cloud_GlobalCoverage','(+ -1.0 (* 2.5 '+get('CloudAmount')+'))'),('Cloud_GlobalDensity','(+ 0.006 (* 0.012 '+get('CloudAmount')+'))')]:
 parts+=['(Rendering|Material|SetScalarParameterValue :self '+get('CloudMID')+' :ParameterName "'+n+'" :Value '+v+')']
parts+=['(bind windAngle (+ '+get('CloudDirection')+' '+get('NorthOffset')+'))','(bind windSpeed (Math|Float|Clamp(Float) '+get('CloudSpeed')+' 0.0 20.0))','(Rendering|Material|SetVectorParameterValue :self '+get('CloudMID')+' :ParameterName "Layout_WindControls" :Value (Math|Color|MakeColor :R (Math|Trig|Cos(Degrees) windAngle) :G (Math|Trig|Sin(Degrees) windAngle) :B 0.0 :A (* 0.333333 windSpeed)))','(Rendering|SetMieScatteringScale :self '+get('SkyAtmosphere')+' :NewValue (+ 0.5 (* 7.0 '+get('Haze')+')))','(Rendering|Lighting|SetLightSourceAngle :self '+get('DirectionalLight')+' :NewValue (+ 0.5357 (* 4.0 '+cover+')))']
for fn,lo,hi in [('SetViewSampleCountScale',1,2),('SetReflectionViewSampleCountScale',.5,1),('SetShadowViewSampleCountScale',.5,1),('SetShadowReflectionViewSampleCountScale',.25,.5)]:
 parts+=['(Rendering|'+fn+' :self '+get('WeatherClouds')+' :NewValue (select '+get('HighQuality')+' '+str(hi)+' '+str(lo)+'))']
parts+=['(Class|PostProcessComponent|SetSettings :self '+get('ExposureOverride')+' :Settings '+get('ExposureSettings')+')','(Rendering|SetVisibility :self '+get('NorthArrow')+' :bNewVisibility true)',')']
wg=BP.add_function_graph(bp,'ApplyWeather')
weather='(fn ApplyWeather ()\n'+'\n'.join(parts[2:])
write(wg,weather)
full=parts[0]+'\n(Utilities|IsValid '+get('CloudMID')+' (:"Is Valid" (CallFunction|ApplyWeather)) (:"Is Not Valid" '+put('CloudMID','(Rendering|Material|CreateDynamicMaterialInstance :Parent "'+base+'MI_EnvironmentCloudDefaults.MI_EnvironmentCloudDefaults" :OptionalName "EnvironmentCloudMID" :CreationFlags "Transient")')+' (CallFunction|ApplyWeather)))\n)'
(root/'UpdateSky_Stage2.dsl').write_text(full);(root/'ApplyWeather.dsl').write_text(weather)
write(g,full);unreal.BlueprintGraphEditor.get_graph_editor(g).set_is_call_in_editor_function(True)
for name,amount,haze,label in [('PresetClear',0.0,.05,'Clear'),('PresetPartlyCloudy',.45,.15,'Partly Cloudy'),('PresetOvercast',1.0,.25,'Overcast'),('PresetHazy',.2,.8,'Hazy')]:
 pg=BP.add_function_graph(bp,name)
 pcode='(fn '+name+' () '+put('CloudAmount',str(amount))+' '+put('Haze',str(haze))+' '+put('WeatherPreset','"'+label+'"')+' (CallFunction|UpdateSky))'
 write(pg,pcode);unreal.BlueprintGraphEditor.get_graph_editor(pg).set_is_call_in_editor_function(True)
BP.compile_blueprint(bp,True)
# Enable cloud shadows on the existing owned sun template, without changing external lights.
sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
 d=unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h);c=unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(d,bp)
 if isinstance(c,unreal.DirectionalLightComponent):c.set_editor_property('cast_cloud_shadows',True)
BP.compile_blueprint(bp,True)
RESULT={'compiled':True,'presets':['Clear','Partly Cloudy','Overcast','Hazy'],'quality':'HighQuality false=Balanced true=High','saved':False}
