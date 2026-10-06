"""Targeted saved-source response for the existing Iran semantic/ground owners.
No native call; unknown material UV/normal/RVT fields remain unknown.
"""
from pathlib import Path
from . import intake as I

def build():
    roots=[I.ROOT/'Content/StarterContent/Materials'/x for x in ['M_Water_Lake.uasset','M_Water_Ocean.uasset','M_Ground_Grass.uasset','M_Ground_Gravel.uasset','M_Rock_Sandstone.uasset']]
    roots += list((I.ROOT/'Content/FC_Coastal_Landscape/Ocean/Materials').glob('*.uasset'))
    roots += [I.ROOT/'Content/FC_Coastal_Landscape/Landscape'/x for x in ['MF_BaseGrass.uasset','MF_Grass.uasset','MF_Sand1.uasset','MF_Sand2.uasset','MF_Soil1.uasset','MF_Soil2.uasset']]
    textures=list((I.ROOT/'Content/FC_Coastal_Landscape/Landscape/LandscapeTextures').glob('T_*.uasset'))
    textures=[p for p in textures if any(x in p.stem for x in ['Grass','Soil','Sand'])]
    rows=[]
    for p in roots+textures:
        if not p.is_file():continue
        rows.append({'object_path':I.obj(p.relative_to(I.ROOT/'Content')),'source_file':str(p),'source_sha256':I.sha(p),
            'native_present_on_disk':True,'native_load_verified_this_supplier':False,
            'native_class':'unverified_material_function_or_texture_candidate','serialized_dependency_hints_not_closure':I.hints(p),
            'uv_space':None,'world_scale_cm':None,'normal_encoding':None,'rvt_requirements':None,
            'channel_packing':'Unverified: BC/NAOR filename suffix is not channel-layout evidence.',
            'wetness_or_farmland_use_qualified':False,'selection_release':False,
            'required_native_fields':['native class','material parent and full dependency closure','texture sampler/normal compression and sRGB','UV/world coordinate graph and parameter values','RVT nodes and textures','actual shader/appearance'],
            'consumer':'Water-class display only uses measured source grid cells with classification provenance; no surveyed polygon/shoreline or water-body simulation inferred.'})
    cat=I.read(I.CATALOG);prep={r['asset_id']:r for r in I.read(I.PREP)['rows']}
    native_contract_path=I.ROOT/'Staging/ManagedSystemsAstra_2026-10-04/Task3_GroundGrass/NATIVE_HANDOFF.json'
    ground=I.read(native_contract_path);grass=[]
    for path in ground['grass_contract']['meshes']:
        r=next(r for r in cat['rows'] if r['runtime']['ObjectPath']==path);rt=r['runtime'];p=I.ROOT/'Content'/(path.split('.')[0][6:]+'.uasset')
        grass.append({'asset_id':r['asset_id'],'object_path':path,'source_sha256':I.sha(p),'catalog_native_revision':rt['AssetRevision'],
            'runtime_fields':{k:rt[k] for k in ['RunEligible','ExplicitHold','AllowedAreas','AllowedZones','RequestRole','PlacementRule','StyleSet','DecisionId','HoldReasons']},
            'native_measurement':prep[r['asset_id']].get('native_measurement'),'rights_state':r['recorded_rights_state'],
            'iran_permission_inferred':False,'rule':'Current area must pass the exact existing canonical eligibility gate; Gaza eligibility is not an Iran release.'})
    repair_path=I.ROOT/'Staging/AppearanceRepair_2026-10-03/GROUND_SHADER_REPAIR_20261003T160849345599Z.json'
    repair=I.read(repair_path)
    retained={'receipt':str(repair_path),'receipt_sha256':I.sha(repair_path),'measurement_date':'2026-10-03; current Grass graph was changed later; recheck native current graph before binding',
        'master':repair['master'],'instance':repair['instance'],'parameters_recorded':repair['instance_values_after'],
        'macro_parameters_recorded':repair.get('macro_parameters'),'soil_tile_parameter_recorded':repair.get('soil_tile_parameter'),
        'normal_settings_recorded':repair.get('normal_settings_after'),'normal_copies_recorded':repair.get('normal_copies'),
        'rvt_requirements':None,'geographic_mask_layers_retained':['Sand_01','Sand_02','Dirt_Path','Sand_Path'],
        'farmland_use_qualified':False,'wet_ground_use_qualified':False}
    result={'schema':'environmentpipeline.semantic_material_supply.v1','recipient_thread':'01a1067b-a64c-7cb1-b244-111b118e4940',
        'scope':'Exact requested installed water/soil/grass material and texture candidates; no new broad intake inventory.',
        'materials_and_textures':rows,'existing_ground_receipt':retained,'permitted_grass_candidates':grass,
        'grass_consumer_contract':ground['grass_contract'],'grass_contract_path':str(native_contract_path),'grass_contract_sha256':I.sha(native_contract_path),
        'catalog_sha256':I.sha(I.CATALOG),'native_operations':0,'new_holds_or_rights_releases':0,
        'unresolved_input':'Bank operator must read the unknown material graph fields after dirty-original recovery; do not invent UV, normal or RVT semantics from names.'}
    I.write('SEMANTIC_MATERIAL_SUPPLY.json',result)
    print('Semantic material/texture candidates:',len(rows),'exact existing grass meshes:',len(grass))
    return result

if __name__=='__main__':build()
