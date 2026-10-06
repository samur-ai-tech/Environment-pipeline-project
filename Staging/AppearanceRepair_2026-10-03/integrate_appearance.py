"""Root integration of independently handed-off retained appearance sources."""
import json,hashlib,datetime
from pathlib import Path
PROJECT=Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE=PROJECT/'Staging/AppearanceRepair_2026-10-03'
SOURCE=Path('C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank')
path=SOURCE/'geocity_city_module.py'
text=path.read_text(encoding='utf-8')
assert '_STYLE_VARIETY_PREVIOUS_CONTRACT' not in text and '_surface_r018_previous_material' not in text
for name in ('SURFACE_GEOMETRY_PATCH.py','BUILDING_VARIETY_PATCH.py'):
    text+='\n\n'+(HERE/name).read_text(encoding='utf-8')
text=text.replace('r017_retained_native_environment','r018_retained_appearance')
# Honor the saved profile's native Landscape material on the whole palette.
start=text.index('def cook_surface_palette(node):')
end=text.index('\ndef ',start+5)
section=text[start:end]
needle='    geo = node.geometry()  # The Python SOP starts with a writable input copy.'
assert needle in section
section=section.replace(needle,needle+'\n    palette_material = str(node.parent().evalParm("landscape_material")).strip()\n    if not re.fullmatch(r"/Game/[A-Za-z0-9_/]+\\.[A-Za-z0-9_]+", palette_material):\n        _fail("Invalid retained native Landscape material path")')
section=section.replace('SURFACE_PALETTE_MATERIAL','palette_material')
text=text[:start]+section+text[end:]
compile(text,str(path),'exec')
path.write_text(text,encoding='utf-8')
materials=json.loads((HERE/'INSTANCE_MATERIALS.json').read_text())
surface=json.loads((HERE/'SURFACE_MATERIAL.json').read_text())
palette=json.loads((HERE/'FACADE_MATERIALS.json').read_text())
styles=json.loads((HERE/'STYLE_CONTRACT_PROPOSAL.json').read_text())['building_style_variants']
for m in styles['modules'].values():
    m['material_slots']=materials['mesh_slots'][m['path']]
    m['dependency_status']='closed'
    m['instancing_material_receipt']=str(HERE/'INSTANCE_MATERIALS.json')
for p in styles['palettes']:
    p['surface_material_path']=palette['variants'][p['id']]['material_path']
    p['dependency_status']='closed'
    p['native_parameter_evidence']=str(HERE/'FACADE_MATERIALS.json')
styles['enabled']=True
(HERE/'STYLE_CONTRACT.json').write_text(json.dumps(styles,indent=2)+'\n')
for sub in ('PermanentIntegration_2026-10-02','GazaShujaiyaIntegration_2026-10-02'):
    pp=PROJECT/'Staging/ModelBank'/sub/'AREA_PROFILE.json'
    p=json.loads(pp.read_text())
    p['building_assembly_contract']['building_style_variants']=styles
    p['landscape_material']=surface['instance']
    p['instance_materials'].update(materials['mesh_slots'])
    p['road_provider']='houdini'
    p['road_provider_contract']={}
    p['roadbld_workflow']={'requested':True,'enabled':False,'status':'prepared_pending_user_signin_and_actual_native_verification','adapter':'Content/Python/geocity_roadbld_workflow.py','no_authentication_bypass':True}
    p['appearance_repair_receipt']=str(HERE/'ASSIGNMENT.json')
    p['normal_material_policy']['appearance_receipt']=str(HERE/'FACADE_MATERIALS.json')
    pp.write_text(json.dumps(p,indent=2)+'\n')
receipt=json.loads((SOURCE/'definition_receipt.json').read_text())
receipt.update(revision='r018_retained_appearance',revision_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='authored_pending_two_real_area_regeneration',validation='Pending actual official Engine replacement, native material-family checks, visual inspection and named saved-map reopen in both existing areas.',appearance_assignment=str(HERE/'ASSIGNMENT.json'),road_provider='houdini_until_native_signed_in_generated_validated_single_provider_delivery')
(SOURCE/'definition_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
result={'module_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'revision':receipt['revision'],'style_families':len(styles['families']),'native_palettes':len(styles['palettes']),'landscape':surface['instance']}
(HERE/'SOURCE_INTEGRATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
