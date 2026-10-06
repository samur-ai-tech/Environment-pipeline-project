import json
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
mel=unreal.MaterialEditingLibrary
mat=unreal.load_asset('/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud')
rows=[]
for e in mel.get_material_expressions(mat):
 d={'path':e.get_path_name(),'class':e.get_class().get_name()}
 for p in ['parameter_name','desc','material_function','default_value']:
  try:d[p]=str(e.get_editor_property(p))
  except:pass
 d['inputs']=[str(x.get_path_name()) if x else None for x in mel.get_inputs_for_material_expression(mat,e)]
 d['input_names']=[str(x) for x in mel.get_material_expression_input_names(e)]
 rows.append(d)
RESULT={'expressions':rows,'dirty':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}
(root/'ENGINE_CLOUD_GRAPH.json').write_text(json.dumps(RESULT,indent=2))
