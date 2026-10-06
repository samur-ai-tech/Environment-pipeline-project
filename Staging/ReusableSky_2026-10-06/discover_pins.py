import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky');g=BP.get_graph(bp,'UpdateSun')
queries=['Math|Rotator|MakeRotator','Math|Float|Truncate','ToString(Text)','Variables|Default|Get','Variables|01','Variables|02','Variables|03','Variables|04','Variables|05','SetEnabled','MakePostProcessSettings','SetmembersinPostProcessSettings','IsVisible','SetCorrectedElevation','SetAzimuth']
found={q:list(BP.find_node_types(g,q)) for q in queries}
types=['SunPosition|GetSunPosition','Utilities|Struct|BreakSunPositionData','Transformation|SetWorldRotation','Rendering|SetVisibility','Rendering|Components|Light|SetIntensity','Rendering|Components|SkyLight|SetIntensity','Utilities|Text|ToText(Integer)','Utilities|String|Append','Class|PostProcessComponent|SetSettings','Class|PostProcessComponent|SetBlendWeight','Math|DateTime|DaysInMonth','Math|Integer|Clamp(Integer)','Math|Float|Clamp(Float)','Math|Rotator|MakeRotator','Math|Float|Truncate']
pins={}
for typ in types:
 i=BP.get_node_type_pins(g,typ)
 pins[typ]={'inputs':[(p.name,p.type_id,p.value) for p in i.input_pins],'outputs':[(p.name,p.type_id) for p in i.output_pins]}
(root/'NODE_PINS.json').write_text(json.dumps(pins,indent=2))
v=unreal.ToolsetLibrary.get_object_properties(bp,['NewVariables'])
(root/'VARIABLE_METADATA_BEFORE.json').write_text(v)
RESULT={'found':found,'pins':pins,'metadata_sample':v[:2800],'postprocess_methods':[x for x in dir(unreal.PostProcessComponent) if 'set' in x or 'enable' in x]}
