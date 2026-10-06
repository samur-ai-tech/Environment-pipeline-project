import json,re,unreal
from pathlib import Path
OUT=Path(r'C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/ShujaiyaOrdinaryRun_2026-10-05/Operator/MWPreview_20261006'); OUT.mkdir(exist_ok=True)
m=unreal.load_asset('/Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER')
dest=OUT/'MTL_MWAM_AutoMaterial_MASTER.t3d'
task=unreal.AssetExportTask()
for k,v in {'object':m,'filename':str(dest),'automated':True,'prompt':False,'replace_identical':True,'exporter':unreal.ObjectExporterT3D()}.items(): task.set_editor_property(k,v)
ok=unreal.Exporter.run_asset_export_task(task)
txt=dest.read_text(encoding='utf-8',errors='ignore') if dest.exists() else ''
# find MMA_0 block
i=txt.find('MaterialExpressionMakeMaterialAttributes_0')
blk=txt[i:i+6000] if i>=0 else ''
pins={}
for pin in ('BaseColor','Metallic','Specular','Roughness','Normal','AmbientOcclusion'):
    mm=re.search(pin+r'=\(([^)]*)\)',blk)
    if mm:
        s=mm.group(1); ex=re.search(r"Expression=([^,]+)",s); oi=re.search(r'OutputIndex=(\d+)',s)
        pins[pin]={'expression':ex.group(1).split('.')[-1].strip('"\'') if ex else None,'output_index':int(oi.group(1)) if oi else 0}
# MF14 outputs
j=txt.find('MaterialExpressionMaterialFunctionCall_14'); blk2=txt[j:j+8000] if j>=0 else ''
outs=re.findall(r'OutputName="([^"]+)"',blk2)
res={'ok':bool(ok) and bool(pins),'t3d':str(dest),'t3d_bytes':len(txt),'mma_pins':pins,'mf14_output_names_in_order':outs[:8]}
print(json.dumps(res)); RESULT=res
