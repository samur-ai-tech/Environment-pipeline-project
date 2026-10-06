import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
graphs={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
(root/'GRAPH_READBACK.json').write_text(json.dumps(graphs,indent=2))
RESULT={'update':graphs['UpdateSun'],'event':graphs['EventGraph'],'blueprint_editor_methods':[n for n in dir(unreal.BlueprintEditorLibrary) if 'refresh' in n],'exporters':[n for n in dir(unreal) if 'Exporter' in n and ('Object' in n or 'Blueprint' in n)]}
