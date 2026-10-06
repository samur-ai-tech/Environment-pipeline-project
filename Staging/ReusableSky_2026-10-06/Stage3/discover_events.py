import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
r=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3';bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky');g=BP.get_graph(bp,'UpdateSky')
RESULT={'events':BP.read_graph_dsl(BP.get_graph(bp,'EventGraph')),'material_fn_types':list(BP.find_node_types(g,'SetMaterial')),'math_floor':list(BP.find_node_types(g,'Floor')),'float_fraction':list(BP.find_node_types(g,'Fraction'))}
(r/'EVENT_DISCOVERY.json').write_text(json.dumps(RESULT,indent=2,default=str))
