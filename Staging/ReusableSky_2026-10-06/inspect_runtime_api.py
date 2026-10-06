import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky');g=BP.get_graph(bp,'UpdateSun')
solar={}
for hour in [6,12,18]:
 s=unreal.SunPositionFunctionLibrary.get_sun_position(31.52,34.44,2.0,False,2026,6,21,hour,0,0)
 solar[hour]={'elevation':s.elevation,'corrected':s.corrected_elevation,'azimuth':s.azimuth}
node=BP.create_node(g,'Utilities|Struct|MakePostProcessSettings',unreal.IntPoint(0,0))
arr=node.get_editor_property('show_pin_for_properties')
opts=[]
for p in arr:
 if 'AutoExposure' in str(p.get_editor_property('PropertyName')):opts.append(str(p))
for p in arr:
 p.set_editor_property('bShowPin',str(p.get_editor_property('PropertyName')) in ['AutoExposureMinBrightness','AutoExposureMaxBrightness'])
node.set_editor_property('show_pin_for_properties',arr)
info=BP._get_node_info(node)
pins=[(p.name,p.type_id) for p in info.input_pins]
BP.delete_node(node)
RESULT={'solar':solar,'exposure_options':opts,'exposed_pins':pins,'all_actor_node':list(BP.find_node_types(g,'GetAllActorsOfClass')),'cast_nodes':list(BP.find_node_types(g,'CastToSceneComponent'))}
