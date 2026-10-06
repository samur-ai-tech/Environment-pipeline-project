import json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets import blueprint_dsl
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage3';base='/Game/Project/Shared/Atmosphere/ReusableSky/'
bp=unreal.load_asset(base+'BP_EnvironmentSky');g=BP.get_graph(bp,'UpdateSky')
def get(n):
 t=[x for x in BP.find_node_types(g,'Get'+n) if x.startswith('Variables|') and x.endswith('|Get'+n)];assert len(t)==1,(n,t);return '('+t[0]+')'
def put(n,v):
 t=[x for x in BP.find_node_types(g,'Set'+n) if x.startswith('Variables|') and x.endswith('|Set'+n)];assert len(t)==1,(n,t);return '('+t[0]+' '+v+')'
def write(graph,code):
 def create(gr,t,pos):
  cls=unreal.MaterialLibrary.static_class() if t=='Rendering|Material|CreateDynamicMaterialInstance' else unreal.MaterialInstanceDynamic.static_class() if t in ['Rendering|Material|SetScalarParameterValue','Rendering|Material|SetVectorParameterValue'] else unreal.PrimitiveComponent.static_class() if t=='Rendering|Material|SetMaterial' else None
  return BP.create_node(gr,t,pos,cls)
 blueprint_dsl.Transpiler(graph,create,BP.connect_pins,BP._get_node_info,BP.set_pin_value,lambda gr:BP.find_nodes(gr),delete_node_fn=BP.delete_node,find_node_types_fn=lambda f:BP.find_node_types(graph,f)).transpile(code)
 (root/(graph.get_name()+'.dsl')).write_text(code)
 BP.compile_blueprint(bp,True)
def smooth(x):return '(* '+x+' (* '+x+' (- 3.0 (* 2.0 '+x+'))))'
def clamp(x,lo,hi):return '(Math|Float|Clamp(Float) '+x+' '+str(lo)+' '+str(hi)+')'

code=(root/'UpdateSky.dsl').read_text().replace(':Seconds 0', ':Seconds (Math|Integer|Clamp(Integer) (Math|Float|Truncate (+ (- (* normalized 3600.0) (+ (* hours 3600.0) (* minutes 60.0))) 0.0001)) 0 59)')
write(BP.get_graph(bp,'UpdateSky'),code)
RESULT={'second_resolution_solar_solver':True,'play_api':{n:getattr(unreal.LevelEditorSubsystem,n).__doc__ for n in dir(unreal.LevelEditorSubsystem) if 'play' in n},'world_api':[n for n in dir(unreal.UnrealEditorSubsystem) if 'world' in n]}
(root/'Resume/TIME_RESOLUTION.json').write_text(json.dumps(RESULT,indent=2))
