import json,unreal
m=unreal.load_asset('/Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER')
lib=unreal.MaterialEditingLibrary
exprs=list(m.get_editor_property('expressions')) if hasattr(m,'get_editor_property') else []
mma=[e for e in exprs if e.get_name()=='MaterialExpressionMakeMaterialAttributes_0']
out={'ok':True,'found_mma':bool(mma),'pins':{}}
if mma:
    mma=mma[0]
    for pin in ('base_color','metallic','specular','roughness','normal','ambient_occlusion'):
        try:
            inp=mma.get_editor_property(pin)
            src=inp.get_editor_property('expression'); idx=int(inp.get_editor_property('output_index'))
            row={'source':src.get_name() if src else None,'output_index':idx}
            if src and src.get_class().get_name()=='MaterialExpressionMaterialFunctionCall':
                fo=list(src.get_editor_property('function_outputs'))
                names=[str(o.get_editor_property('expression_output').get_editor_property('output_name')) for o in fo]
                row['function_outputs']=names; row['resolved']=names[idx] if 0<=idx<len(names) else None
                row['function']=str(src.get_editor_property('material_function').get_path_name())
            out['pins'][pin]=row
        except Exception as e:
            out['pins'][pin]={'error':repr(e)}
print(json.dumps(out))
RESULT=out
