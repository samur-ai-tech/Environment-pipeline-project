import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky');g=BP.get_graph(bp,'UpdateSky')
types=['Rendering|Material|CreateDynamicMaterialInstance','Rendering|Material|SetScalarParameterValue','Rendering|Material|SetVectorParameterValue','Rendering|SetMaterial','Rendering|SetMieScatteringScale','Rendering|Lighting|SetLightSourceAngle','Rendering|SetViewSampleCountScale','Rendering|SetReflectionViewSampleCountScale','Rendering|SetShadowViewSampleCountScale','Rendering|SetShadowReflectionViewSampleCountScale']
types += list(BP.find_node_types(g,'MakeColor'))
types += [t for t in BP.find_node_types(g,'Cos') if t.startswith('Math|Trig')]+[t for t in BP.find_node_types(g,'Sin') if t.startswith('Math|Trig')]
out={}
for t in types:
 i=BP.get_node_type_pins(g,t);out[t]={'in':[(p.name,p.type_id,p.value) for p in i.input_pins],'out':[(p.name,p.type_id) for p in i.output_pins]}
RESULT=out
(root/'WEATHER_PINS.json').write_text(json.dumps(out,indent=2))
