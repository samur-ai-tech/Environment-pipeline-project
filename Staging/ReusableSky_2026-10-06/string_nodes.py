import json
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky');g=BP.get_graph(bp,'UpdateSky')
RESULT={q:list(BP.find_node_types(g,q)) for q in ['Utilities|String|Equal','Utilities|String|NotEqual','Utilities|String|IsEmpty','UpdateSky']}
