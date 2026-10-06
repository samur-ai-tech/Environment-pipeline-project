import hou,pathlib,json,hashlib,copy
D=pathlib.Path(__file__).parent
read=lambda p:json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
before=read(D/'NATIVE_BEFORE.json');assert len(before['hdas'])==1;b=before['hdas'][0];assert sha(b['source'])==b['source_sha256']
hou.setUpdateMode(hou.updateMode.Manual)
definition=next(d for d in hou.hda.definitionsInFile(b['source']) if d.nodeTypeName()=='trackb::geocity_city::15.0')
source=definition.sections()['PythonModule'].contents();assert 'def procedural_bank_families' in source and 'def assembly_layout' in source
patch="""

# User retired ModularCourtyard on 2026-10-06. Keep source assets, exclude outputs.
_RETIRED_COURTYARD_PREVIOUS_LAYOUT = assembly_layout
RETIRED_BUILDING_MODULE_PREFIXES = ('/Game/ModularCourtyard/',)

def assembly_layout(feature, contract):
    record = _RETIRED_COURTYARD_PREVIOUS_LAYOUT(feature, contract)
    blocked = sorted({item.get('path', '') for item in record.get('wall_placements', [])
                      if item.get('path', '').startswith(RETIRED_BUILDING_MODULE_PREFIXES)})
    if blocked:
        # Existing normal cook records the unsupported lot; no retired instances emitted.
        raise ValueError('retired_building_family:ModularCourtyard:no_eligible_replacement:'
                         + str(feature.get('osm_id', '')))
    return record
"""
assert 'RETIRED_BUILDING_MODULE_PREFIXES' not in source
updated=source+patch;compile(updated,'courtyard_retirement','exec')
dest=pathlib.Path(b['source']).parent.parent/'20261006_courtyard_retired_v005'/'GeoCity_city_v015_PermanentBank_NoCourtyard_v005.hdalc';dest.parent.mkdir(exist_ok=True);assert not dest.exists()
definition.copyToHDAFile(str(dest));hou.hda.installFile(str(dest));saved=next(d for d in hou.hda.definitionsInFile(str(dest)) if d.nodeTypeName()==definition.nodeTypeName());saved.addSection('PythonModule',updated)
group=saved.parmTemplateGroup();parm=group.find('building_assembly_contract_json');c=json.loads(parm.defaultValue()[0]);c['retired_building_module_prefixes']=['/Game/ModularCourtyard/'];c['retired_building_family_reason']='User rejected ModularCourtyard; no automatic reuse via fallback.';parm.setDefaultValue((json.dumps(c),));group.replace(parm.name(),parm);saved.setParmTemplateGroup(group);saved.save(str(dest))
(dest.parent/'geocity_city_module.py').write_text(updated)
(D/'BUILD.json').write_text(json.dumps(dict(source=b,hda=dict(path=str(dest),sha256=sha(dest)),policy='Reject complete layout records containing any ModularCourtyard native module, including legacy fallback. Preserve registered source-family outputs and normal unmatched-lot reporting.'),indent=2));print('BUILD_PASS')
