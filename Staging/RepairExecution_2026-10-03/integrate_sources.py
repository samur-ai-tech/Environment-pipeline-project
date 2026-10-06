"""Integrate the retained generator repairs after worker source handoff."""
import json
import hashlib
from pathlib import Path

PROJECT = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline')
HERE = PROJECT / 'Staging/RepairExecution_2026-10-03'
SOURCE = Path('C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank')
module_path = SOURCE / 'geocity_city_module.py'
source = module_path.read_text(encoding='utf-8')
assert '_terrain_r015_previous_building_pads' not in source, 'Repair patches already integrated'
for filename in ('BUILDING_ASSEMBLY_PATCH.py', 'TERRAIN_PATCH.py'):
    source += '\n\n' + (HERE / filename).read_text(encoding='utf-8')
source = source.replace("receipt['generator_revision'] = 'r014'", "receipt['generator_revision'] = 'r015_retained_ground_native_assembly'")
source = source.replace('receipt["generator_revision"] = "r015_geographic_native_assembly"', 'receipt["generator_revision"] = "r015_retained_ground_native_assembly"')
compile(source, str(module_path), 'exec')
module_path.write_text(source, encoding='utf-8')
contract = json.loads((HERE / 'ASSEMBLY_CONTRACT.json').read_text(encoding='utf-8'))
for sub in ('PermanentIntegration_2026-10-02', 'GazaShujaiyaIntegration_2026-10-02'):
    path = PROJECT / 'Staging/ModelBank' / sub / 'AREA_PROFILE.json'
    profile = json.loads(path.read_text(encoding='utf-8'))
    profile['building_assembly_contract'] = contract
    profile['normal_asset_policy']['assembly_contract_receipt'] = str(HERE / 'ASSEMBLY_CONTRACT.json')
    profile['normal_asset_policy']['modular_asset_scale'] = 'Measured facade bay width 0.5..1.5, story height 0.65..1.1; doors native scale. Whole buildings native 1:1.'
    path.write_text(json.dumps(profile, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'module_sha256': hashlib.sha256(module_path.read_bytes()).hexdigest(), 'source': str(module_path)}))
