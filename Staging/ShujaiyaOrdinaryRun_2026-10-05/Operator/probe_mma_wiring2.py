import json,unreal
LIB=unreal.MaterialEditingLibrary
m=unreal.load_asset('/Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER')
nodes=list(LIB.get_material_expressions(m))
mma=[e for e in nodes if e.get_name()=='MaterialExpressionMakeMaterialAttributes_0'][0]
out={'ok':True,'pins':{}}
for pin in ('base_color','metallic','specular','roughness','normal','ambient_occlusion'):
    row={}
    try:
        inp=mma.get_editor_property(pin)
        src=inp.get_editor_property('expression'); idx=int(inp.get_editor_property('output_index'))
        row={'source':src.get_name() if src else None,'output_index':idx}
        if src:
            names=list(LIB.get_material_expression_output_names(src)); row['source_outputs']=[str(n) for n in names]; row['resolved']=str(names[idx]) if 0<=idx<len(names) else None
            row['legacy_reader_name']=str(LIB.get_input_node_output_name_for_material_expression(mma,src))
    except Exception as e: row['error']=repr(e)
    out['pins'][pin]=row
print(json.dumps(out)); RESULT=out
