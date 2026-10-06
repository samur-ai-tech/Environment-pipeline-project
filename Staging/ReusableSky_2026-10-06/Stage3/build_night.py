import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets import blueprint_dsl
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3';base='/Game/Project/Shared/Atmosphere/ReusableSky/'
bp=unreal.load_asset(base+'BP_EnvironmentSky');g=BP.get_graph(bp,'UpdateSky')
def get(n):
 t=[x for x in BP.find_node_types(g,'Get'+n) if x.startswith('Variables|') and x.endswith('|Get'+n)];assert len(t)==1,(n,t);return '('+t[0]+')'
def put(n,v):
 t=[x for x in BP.find_node_types(g,'Set'+n) if x.startswith('Variables|') and x.endswith('|Set'+n)];assert len(t)==1,(n,t);return '('+t[0]+' '+v+')'
def write(graph,code):
 def create(gr,t,pos):
  cls=unreal.MaterialLibrary.static_class() if t=='Rendering|Material|CreateDynamicMaterialInstance' else unreal.MaterialInstanceDynamic.static_class() if t in ['Rendering|Material|SetScalarParameterValue','Rendering|Material|SetVectorParameterValue'] else unreal.PrimitiveComponent.static_class() if t=='Rendering|Material|SetMaterial' else None
  return BP.create_node(gr,t,pos,cls)
 blueprint_dsl.Transpiler(graph,create,BP.connect_pins,BP._get_node_info,BP.set_pin_value,lambda gr:BP.find_nodes(gr),delete_node_fn=BP.delete_node,find_node_types_fn=lambda f:BP.find_node_types(graph,f)).transpile(code)
 (root/(graph.get_name()+'.dsl')).write_text(code)
 BP.compile_blueprint(bp,True)
def smooth(x):return '(* '+x+' (* '+x+' (- 3.0 (* 2.0 '+x+'))))'
def clamp(x,lo,hi):return '(Math|Float|Clamp(Float) '+x+' '+str(lo)+' '+str(hi)+')'
for name in ['UpdateNight','ApplyNightMaterial']:
 BP.add_function_graph(bp,name)
api={'SetSkyTime':[('Hour','float')],'SetMoonAppearance':[('Enabled','bool'),('LightBrightness','float'),('DiskBrightness','float'),('Phase','float')],'SetStarAppearance':[('Enabled','bool'),('Brightness','float')],'SetTimeProgression':[('Enabled','bool'),('Paused','bool'),('DayMinutes','float')],'AdvanceSkyTime':[('DeltaSeconds','float')]}
for name,params in api.items():
 gr=BP.add_function_graph(bp,name)
 for n,t in params:BP.add_function_param(gr,n,t,True)
BP.compile_blueprint(bp,True)
night=['(fn ApplyNightMaterial ()', '(Rendering|Material|SetMaterial :self '+get('CelestialDome')+' :ElementIndex 0 :Material '+get('CelestialMID')+')', '(Rendering|SetVisibility :self '+get('CelestialDome')+' :bNewVisibility '+get('CanRender')+')']
night+=['(bind moonHorizon '+clamp('(/ (- 0.0 '+get('SunElevation')+') 5.0)',0.0,1.0)+')','(bind moonFade '+smooth('moonHorizon')+')','(bind starT '+clamp('(/ (- (- 0.0 '+get('SunElevation')+') 4.0) 8.0)',0.0,1.0)+')']
values={'MoonLuminance':'(select '+get('MoonEnabled')+' (* '+clamp(get('MoonDiskBrightness'),0.0,100.0)+' (* '+get('NightBlend')+' moonFade)) 0.0)','MoonPhase':clamp(get('MoonPhase'),0.0,1.0),'MoonDiameter':clamp(get('MoonAngularDiameter'),.1,10.0),'StarLuminance':'(select '+get('StarsEnabled')+' (* '+clamp(get('StarBrightness'),0.0,100.0)+' '+smooth('starT')+') 0.0)','NorthRadians':'(* '+get('NorthOffset')+' 0.01745329252)'}
for n,v in values.items():night+=['(Rendering|Material|SetScalarParameterValue :self '+get('CelestialMID')+' :ParameterName "'+n+'" :Value '+v+')']
night+=['(bind (mx my mz) (Math|Vector|BreakVector (Transformation|GetForwardVector :self '+get('MoonLight')+')))','(Rendering|Material|SetVectorParameterValue :self '+get('CelestialMID')+' :ParameterName "MoonDirection" :Value (Math|Color|MakeColor :R (- 0.0 mx) :G (- 0.0 my) :B (- 0.0 mz) :A 1.0))',')']
write(BP.get_graph(bp,'ApplyNightMaterial'),'\n'.join(night))
code=['(fn UpdateNight ()',put('SunElevation','(- '+get('CorrectedElevation')+' 180.0)'),'(bind nightT '+clamp('(/ (- 2.0 '+get('SunElevation')+') 12.0)',0.0,1.0)+')',put('NightBlend',smooth('nightT')),'(bind sunT '+clamp('(/ '+get('SunElevation')+' 4.0)',0.0,1.0)+')','(bind cloudCube (* '+get('CloudAmount')+' (* '+get('CloudAmount')+' '+get('CloudAmount')+')))']
code+=['(Rendering|Components|Light|SetIntensity :self '+get('DirectionalLight')+' :NewIntensity (* '+clamp(get('SunIntensity'),0.0,200000.0)+' (* '+smooth('sunT')+' (- 1.0 (* 0.88 cloudCube)))))','(Rendering|Components|SkyLight|SetIntensity :self '+get('SkyLight')+' :NewIntensity (* '+clamp(get('SkyIntensity'),0.0,20.0)+' (* (- 1.0 (* 0.15 '+get('CloudAmount')+')) (+ (- 1.0 '+get('NightBlend')+') (* '+get('NightBlend')+' '+clamp(get('NightSkyFill'),0.0,1.0)+')))))']
code+=['(Transformation|SetWorldRotation :self '+get('MoonLight')+' :NewRotation (Math|Rotator|MakeRotator :Pitch (- 180.0 '+get('SunElevation')+') :Yaw (+ 180.0 (+ '+get('Azimuth')+' '+get('NorthOffset')+'))))','(Rendering|SetVisibility :self '+get('MoonLight')+' :bNewVisibility (and '+get('CanRender')+' '+get('MoonEnabled')+'))','(bind moonT '+clamp('(/ (- 0.0 '+get('SunElevation')+') 5.0)',0.0,1.0)+')','(bind phaseLight (* 0.5 (- 1.0 (Math|Trig|Cos(Degrees) (* 360.0 '+clamp(get('MoonPhase'),0.0,1.0)+')))))']
code+=['(Rendering|Components|Light|SetIntensity :self '+get('MoonLight')+' :NewIntensity (select '+get('MoonEnabled')+' (* '+clamp(get('MoonBrightness'),0.0,10.0)+' (* '+get('NightBlend')+' (* '+smooth('moonT')+' (* phaseLight (- 1.0 (* 0.7 '+get('CloudAmount')+')))))) 0.0))','(Rendering|Components|Light|SetLightColor :self '+get('MoonLight')+' :NewLightColor (Math|Color|MakeColor :R 0.64 :G 0.74 :B 1.0 :A 1.0))','(Rendering|Lighting|SetLightSourceAngle :self '+get('MoonLight')+' :NewValue '+clamp(get('MoonAngularDiameter'),.1,10.0)+')','(Actor|Tick|SetActorTickInterval :TickInterval 0.1)','(Actor|Tick|SetActorTickEnabled :bEnabled (and '+get('CanRender')+' (and '+get('AnimateTime')+' (not '+get('TimePaused')+'))))']
code+=['(Utilities|IsValid '+get('CelestialMID')+' (:"Is Valid" (CallFunction|ApplyNightMaterial)) (:"Is Not Valid" '+put('CelestialMID','(Rendering|Material|CreateDynamicMaterialInstance :Parent "'+base+'M_EnvironmentCelestial.M_EnvironmentCelestial" :OptionalName "EnvironmentCelestialMID" :CreationFlags "Transient")')+' (CallFunction|ApplyNightMaterial)))',')']
write(BP.get_graph(bp,'UpdateNight'),'\n'.join(code))
# Keep clock, geographic solver, activation and weather; lights have only one final update path.
code=(root.parent/'Stage2/UpdateSky_Stage2.dsl').read_text();code='\n'.join(l for l in code.splitlines() if not l.startswith('(Rendering|Components|Light|SetIntensity') and not l.startswith('(Rendering|Components|SkyLight|SetIntensity'))
code=code.replace('Automatic time animation is off.','Optional time progression is runtime-only; Animate Time defaults off. Moon phase and orbit are artistic.')
write(g,code)
weather=(root.parent/'Stage2/ApplyWeather.dsl').read_text().rstrip()[:-1]+'\n(CallFunction|UpdateNight)\n)';write(BP.get_graph(bp,'ApplyWeather'),weather)
ucs='(fn ConstructionScript () '+put('CloudMID','(Rendering|Material|CreateDynamicMaterialInstance :Parent "'+base+'MI_EnvironmentCloudDefaults.MI_EnvironmentCloudDefaults" :OptionalName "EnvironmentCloudMID" :CreationFlags "Transient")')+' '+put('CelestialMID','(Rendering|Material|CreateDynamicMaterialInstance :Parent "'+base+'M_EnvironmentCelestial.M_EnvironmentCelestial" :OptionalName "EnvironmentCelestialMID" :CreationFlags "Transient")')+' (CallFunction|UpdateSky))'
write(BP.get_graph(bp,'UserConstructionScript'),ucs)
wrap=lambda x:'(- '+x+' (* 24.0 (Math|Float|Floor (/ '+x+' 24.0))))'
functions={
'SetSkyTime':put('TimeOfDay',wrap('Hour')),
'SetMoonAppearance':' '.join([put('MoonEnabled','Enabled'),put('MoonBrightness',clamp('LightBrightness',0.0,10.0)),put('MoonDiskBrightness',clamp('DiskBrightness',0.0,100.0)),put('MoonPhase',clamp('Phase',0.0,1.0))]),
'SetStarAppearance':put('StarsEnabled','Enabled')+' '+put('StarBrightness',clamp('Brightness',0.0,100.0)),
'SetTimeProgression':' '.join([put('AnimateTime','Enabled'),put('TimePaused','Paused'),put('DayLengthMinutes',clamp('DayMinutes',.1,1440.0))])}
for name,body in functions.items():write(BP.get_graph(bp,name),'(fn '+name+' ('+' '.join(n for n,t in api[name])+') '+body+' (CallFunction|UpdateSky))')
advance='(fn AdvanceSkyTime (DeltaSeconds) (if (and '+get('CanRender')+' (and '+get('AnimateTime')+' (not '+get('TimePaused')+'))) (bind nextHour (+ '+get('TimeOfDay')+' (/ (* '+clamp('DeltaSeconds',0.0,3600.0)+' 24.0) (* '+clamp(get('DayLengthMinutes'),.1,1440.0)+' 60.0)))) '+put('TimeOfDay',wrap('nextHour'))+' (CallFunction|UpdateSky)))'
write(BP.get_graph(bp,'AdvanceSkyTime'),advance)
write(BP.get_graph(bp,'EventGraph'),'(event EventBeginPlay (CallFunction|UpdateSky))\n(event EventTick (DeltaSeconds) (CallFunction|AdvanceSkyTime :DeltaSeconds DeltaSeconds))')
BP.compile_blueprint(bp,True)
a=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name()=='BP_EnvironmentSky_C_0');a.call_method('UpdateSky')
RESULT={'compiled':True,'clock':a.get_editor_property('ClockDisplay'),'night_blend':a.get_editor_property('NightBlend'),'celestial_mid':str(a.get_editor_property('CelestialMID')),'tick_enabled':a.is_actor_tick_enabled(),'saved':False}
(root/'IMPLEMENTED.json').write_text(json.dumps(RESULT,indent=2))
