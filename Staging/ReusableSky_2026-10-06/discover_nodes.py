import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06'
bp=unreal.load_asset('/Game/Project/Shared/Atmosphere/ReusableSky/BP_EnvironmentSky')
g=BP.get_graph(bp,'UpdateSun')
queries=['GetSunPosition','BreakSunPosition','SetWorldRotation','SetVisibility','SetIntensity','ToText(Integer)','Append','SetClock','SetStatus','GetAllActorsOfClass','GetComponentsByClass','GetOwner','SetSettings','SetBlendWeight','DaysInMonth','Clamp','SetNorth','GetNorth','SetSolar','SetPostProcess','SetEnabled','GetTimeOfDay']
nodes={q:list(BP.find_node_types(g,q)) for q in queries}
(root/'NODE_TYPES.json').write_text(json.dumps(nodes,indent=2))
props={}
for name in ['new_variables','NewVariables']:
 try:
  arr=bp.get_editor_property(name)
  props[name]=[{'repr':str(x),'fields':[n for n in dir(x) if not n.startswith('_')]} for x in list(arr)[:1]]
 except Exception as e:props[name]=str(e)
RESULT={'asset':bp.get_path_name(),'node_types':nodes,'var_struct':props,'metadata_classes':[n for n in dir(unreal) if 'Variable' in n and ('Meta' in n or 'Description' in n)],'cdo_properties':[n for n in dir(unreal.get_default_object(bp.generated_class())) if any(k in n.lower() for k in ['time','sun','direction','north','exposure'])]}
