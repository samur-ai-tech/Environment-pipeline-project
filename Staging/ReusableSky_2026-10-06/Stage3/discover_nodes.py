import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3';bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
g=BP.get_graph(bp,'UpdateSky')
queries=['SetActorTickEnabled','SetActorTickInterval','GetForwardVector','BreakVector','FMod','SetLightColor','SetMaterial','SetVisibility','SetWorldRotation','SetIntensity','GetWorldDeltaSeconds']
RESULT={'node_types':{q:list(BP.find_node_types(g,q)) for q in queries},'graphs':[str(x.get_name()) for x in BP.list_graphs(bp)],'dirty_content':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
(root/'NODE_TYPES.json').write_text(json.dumps(RESULT,indent=2))
