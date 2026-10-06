"""Supported read-only graph connection getters for the selected asphalt master."""
import datetime,hashlib,json,time
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_junctions as j
ROOT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline');HERE=ROOT/'Staging/ManagedAstra_2026-10-03'
p=bank.ACTIVE[-1];r=native.ACTIVE[-1];p.guard();r.guard()
assert p.watch_tick is None and p.save_tick is None and r.tick_handle is None and p.api.is_asset_cooking_paused()
def dirty():return sorted(x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())+sorted(x.get_path_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
before=dirty();owned=j._owned_state(r)
m=unreal.load_object(None,'/RoadBLD/RoadBLD/DefaultRoadKit/Materials/M_RoadBLD_Asphalt_Master.M_RoadBLD_Asphalt_Master')
lib=unreal.MaterialEditingLibrary;rows=[]
for n in lib.get_material_expressions(m):
    names=[str(x) for x in lib.get_material_expression_input_names(n)]
    inputs=lib.get_inputs_for_material_expression(m,n)
    rows.append({'name':n.get_name(),'class':n.get_class().get_name(),'input_names':names,'inputs':[x.get_name() if x else None for x in inputs]})
outputs={}
for label,prop in [('base_color',unreal.MaterialProperty.MP_BASE_COLOR),('roughness',unreal.MaterialProperty.MP_ROUGHNESS),('normal',unreal.MaterialProperty.MP_NORMAL),('material_attributes',unreal.MaterialProperty.MP_MATERIAL_ATTRIBUTES)]:
    node=lib.get_material_property_input_node(m,prop);outputs[label]=node.get_name() if node else None
assert before==dirty() and owned==j._owned_state(r)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
receipt=ROOT/'Staging/AppearanceRepair_2026-10-03'/('TASK2_ASPHALT_PATCH_CONNECTIONS_'+stamp+'.json')
d={'status':'READ_ONLY_ASPHALT_CONNECTIONS_COMPLETE','material':m.get_path_name(),'nodes':rows,'outputs':outputs,'supported_api':'MaterialEditingLibrary get_material_expressions/get_material_expression_input_names/get_inputs_for_material_expression/get_material_property_input_node','no_material_editor_open_compile_or_mutation':True,'participants_dirty_packages_unchanged':True,'callbacks':0}
receipt.write_text(json.dumps(d,indent=2)+'\n')
(HERE/'TASK2_PATCH_CONNECTIONS_STATUS.json').write_text(json.dumps({'status':d['status'],'receipt':str(receipt),'sha256':hashlib.sha256(receipt.read_bytes()).hexdigest()},indent=2)+'\n')
print(str(receipt))
