import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets import blueprint_dsl
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
def get(n):
 matches=[s for s in BP.find_node_types(g,'Get'+n) if s.startswith('Variables|') and s.endswith('|Get'+n)]
 assert len(matches)==1,(n,list(matches))
 return '('+matches[0]+')'
def put(n,val):
 matches=[s for s in BP.find_node_types(g,'Set'+n) if s.startswith('Variables|') and s.endswith('|Set'+n)]
 assert len(matches)==1,(n,list(matches))
 return '('+matches[0]+' '+val+')'
if 'CanRender' not in BP.list_variables(bp):BP.add_variable(bp,'CanRender','bool')
BP.compile_blueprint(bp)
g=BP.add_function_graph(bp,'UpdateSky')
parts=['(fn UpdateSky ()']
parts += ['(bind normalized (select (>= '+get('TimeOfDay')+' 24.0) 0.0 (Math|Float|Clamp(Float) '+get('TimeOfDay')+' 0.0 24.0)))',put('TimeOfDay','normalized'),'(bind hours (Math|Float|Truncate normalized))','(bind minutes (Math|Float|Truncate (+ (* (- normalized hours) 60.0) 0.0001)))']
parts += [put('ClockDisplay','(Utilities|String|Append (Utilities|String|Append (Utilities|String|ToString(Text) (Utilities|Text|ToText(Integer) :Value hours :bUseGrouping false :MinimumIntegralDigits 2 :MaximumIntegralDigits 2)) ":") (Utilities|String|ToString(Text) (Utilities|Text|ToText(Integer) :Value minutes :bUseGrouping false :MinimumIntegralDigits 2 :MaximumIntegralDigits 2)))')]
parts += [put('ConflictActors','""'),'(bind actors (Actor|GetAllActorsOfClass :ActorClass "/Script/Engine.Actor"))','(for other actors (if (!= other self)']
for cls in ['DirectionalLightComponent','SkyLightComponent','SkyAtmosphereComponent']:
 parts += ['(for component (Actor|GetComponentsByClass :self other :ComponentClass "/Script/Engine.'+cls+'")','(bind sceneComponent (Utilities|Casting|CastToSceneComponent :Object component)','(:then (if (Rendering|IsVisible :self sceneComponent) '+put('ConflictActors','(Utilities|String|Append '+get('ConflictActors')+' (Utilities|String|Append (Utilities|GetDisplayName :Object other) "; "))')+'))','(:CastFailed)))']
parts += ['))',put('CanRender','(and '+get('RigEnabled')+' (Utilities|String|IsEmpty '+get('ConflictActors')+'))')]
parts += ['(if '+get('ManualSun'),put('CorrectedElevation','(+ 180.0 (Math|Float|Clamp(Float) :Value '+get('ManualElevation')+' :Min -90.0 :Max 90.0))'),put('Azimuth',get('ManualDirection')),'(else','(bind year (Math|Integer|Clamp(Integer) :Value '+get('Year')+' :Min 1 :Max 9999))','(bind month (Math|Integer|Clamp(Integer) :Value '+get('Month')+' :Min 1 :Max 12))','(bind day (Math|Integer|Clamp(Integer) :Value '+get('Day')+' :Min 1 :Max (Math|DateTime|DaysInMonth year month)))','(bind solar (SunPosition|GetSunPosition :Latitude (Math|Float|Clamp(Float) '+get('Latitude')+' -90.0 90.0) :Longitude (Math|Float|Clamp(Float) '+get('Longitude')+' -180.0 180.0) :TimeZone (Math|Float|Clamp(Float) '+get('TimeZone')+' -12.0 14.0) :bIsDaylightSavingTime '+get('UseDaylightSavingTime')+' :Year year :Month month :Day day :Hours hours :Minutes minutes :Seconds 0))','(bind (elevation corrected azimuth sunrise sunset solarNoon) (Utilities|Struct|BreakSunPositionData solar))',put('CorrectedElevation','corrected'),put('Azimuth','azimuth'),'))']
parts += ['(Transformation|SetWorldRotation :self '+get('DirectionalLight')+' :NewRotation (Math|Rotator|MakeRotator :Pitch '+get('CorrectedElevation')+' :Yaw (+ '+get('Azimuth')+' '+get('NorthOffset')+')))','(Transformation|SetWorldRotation :self '+get('NorthArrow')+' :NewRotation (Math|Rotator|MakeRotator :Yaw '+get('NorthOffset')+'))','(Transformation|SetWorldRotation :self '+get('CompassMesh')+' :NewRotation (Math|Rotator|MakeRotator :Yaw (+ '+get('NorthOffset')+' 90.0)))']
for comp in ['DirectionalLight','SkyLight','SkyAtmosphere']:
 parts += ['(Rendering|SetVisibility :self '+get(comp)+' :bNewVisibility '+get('CanRender')+')']
parts += ['(Rendering|Components|Light|SetIntensity :self '+get('DirectionalLight')+' :NewIntensity (select (> '+get('CorrectedElevation')+' 180.0) (Math|Float|Clamp(Float) '+get('SunIntensity')+' 0.0 200000.0) 0.0))','(Rendering|Components|SkyLight|SetIntensity :self '+get('SkyLight')+' :NewIntensity (Math|Float|Clamp(Float) '+get('SkyIntensity')+' 0.0 20.0))','(Class|PostProcessComponent|SetEnabled :self '+get('ExposureOverride')+' :bEnabled (and '+get('CanRender')+' '+get('OverrideExposure')+'))','(Class|PostProcessComponent|SetBlendWeight :self '+get('ExposureOverride')+' :BlendWeight (select (and '+get('CanRender')+' '+get('OverrideExposure')+') 1.0 0.0))']
parts += ['(if (not (Utilities|String|IsEmpty '+get('ConflictActors')+'))',put('Status','"Lighting conflict: existing actors preserved; rig inactive. See Conflict Actors."'),'(else (if '+get('CanRender'),put('Status','(select '+get('ManualSun')+' "Active - Manual Sun" "Active - Time and Location")'),'(else '+put('Status','"Inactive - enable Rig Enabled after resolving lighting conflicts."')+'))))',put('RuntimeNotes','"Runtime: call UpdateSun after changing controls. Automatic time animation is off. Invalid date inputs are clamped for the solar solver."'),')']
code='\n'.join(parts)
(root/'UpdateSky.dsl').write_text(code)
# Use the installed Blueprint DSL; all node IDs/pins were inspected first.
BP.write_graph_dsl(g,code)
event=BP.get_graph(bp,'EventGraph')
for node in BP.find_nodes(event):BP.delete_node(node)
BP.write_graph_dsl(event,'(event EventBeginPlay (CallFunction|UpdateSky))')
BP.write_graph_dsl(BP.get_graph(bp,'UserConstructionScript'),'(fn ConstructionScript () (CallFunction|UpdateSky))')
for obsolete in ['UpdateSun','GetHMSFromSolarTime','IsDST']:
 BP.remove_function_graph(bp,obsolete)
BP.compile_blueprint(bp,True)
RESULT={'implemented':True,'asset':bp.get_path_name(),'function':'UpdateSky','graphs':{x.get_name():len(BP.find_nodes(x)) for x in BP.list_graphs(bp)},'saved':False}
