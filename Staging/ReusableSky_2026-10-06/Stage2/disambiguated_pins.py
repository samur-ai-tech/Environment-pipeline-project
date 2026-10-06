import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky');g=BP.get_graph(bp,'UpdateSky')
out={}
for t,cls in [('Rendering|Material|CreateDynamicMaterialInstance',unreal.MaterialLibrary),('Rendering|Material|SetScalarParameterValue',unreal.MaterialInstanceDynamic),('Rendering|Material|SetVectorParameterValue',unreal.MaterialInstanceDynamic)]:
 n=BP.create_node(g,t,unreal.IntPoint(0,0),cls.static_class());i=BP._get_node_info(n)
 out[t]={'in':[(p.name,p.type_id,p.value) for p in i.input_pins],'out':[(p.name,p.type_id) for p in i.output_pins]};BP.delete_node(n)
RESULT=out

