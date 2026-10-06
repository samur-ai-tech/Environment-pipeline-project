"""Retained bank-owned configuration. Importing this module never operates Unreal."""
import collections
import copy
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PREP = ROOT / 'Staging/BankPreparation_2026-10-04'
BANK = ROOT / 'Staging/ModelBank/PermanentIntegration_2026-10-02'
SOURCE = BANK / 'catalog_v4_source.json'
CSV = BANK / 'catalog_v4_full.csv'
AREAS = ['GazaRimal', 'GazaShujaiya']
DECISION = 'Aviv_BankIntegration_2026-10-04_Nonmodular_v001'
INTS = {'SchemaVersion','RunEligible','BoundsValid','AnchorValid','OrientationValid','TechnicalPreviewEligible','ExplicitHold'}
RULES = {'small_prop':'zone_ground_prop','street_prop':'roadside_prop','street_pole':'roadside_pole','understory':'terrain_understory','shrub':'terrain_shrub','tree':'terrain_tree','whole_building':'building_footprint'}
NAMED_HOLDS = ['H0013','H0907','H0051','H0958','H0094']

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def yes(value):
    return str(value).lower() in ('true','1')

def package_file(obj):
    assert obj.startswith('/Game/')
    return ROOT/'Content'/(obj.split('.')[0][6:]+'.uasset')

def typed_rows(rows):
    result=[]
    for raw in rows:
        row={}
        for key,value in raw.items():
            if key in INTS:
                row[key]=int(value) if key=='SchemaVersion' else int(yes(value))
            elif key.endswith('Cm') or key in ('SelectionWeight','PreviewWeight'):
                row[key]=float(value)
                assert math.isfinite(row[key]),key
            else:
                row[key]=value
        result.append(row)
    return sorted(result,key=lambda r:r['Name'])

def digest(rows):
    return hashlib.sha256(json.dumps(typed_rows(rows),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def native_definitions():
    """Explicitly reviewed shortlist; no automatic name-based activation."""
    return [
      ('current_ModularCourtyard__Meshes__SM_Rubbish_bug_2t','small_prop','soft_ground_bag','+X',350,'Same retained rubbish-bag material override as the existing enabled family; native view/contact review required.'),
      ('current_ProceduralBuildingGenerator__Meshes__Slum__Trashbag','small_prop','soft_ground_bag','+X',350,'Freestanding tied bag. Ground contact and retained material usage require native verification.'),
      ('current_ProceduralBuildingGenerator__Meshes__Slum__Trashcan_Closed02','street_prop','freestanding_bin','+X',600,'Complete closed street bin; rotational facing is unconstrained.'),
      ('current_ProceduralBuildingGenerator__Meshes__Slum__Trashcan_Open01','street_prop','freestanding_bin','+X',600,'Complete open street bin; rotational facing is unconstrained.'),
      ('current_ProceduralBuildingGenerator__Meshes__Slum__Trashcan_Open02','street_prop','freestanding_bin','+X',600,'Complete open street bin; rotational facing is unconstrained.'),
      ('current_ProceduralBuildingGenerator__Meshes__Slum__Trashcan_Open03','street_prop','freestanding_bin','+X',600,'Complete open street bin; rotational facing is unconstrained.'),
      ('current_Project__Shared__Bank_ME_v3__Props__SM_H0034_Cart','small_prop','wheel_contact','+X',450,'Native cart; wheel support and forward orientation require review before activation.'),
      ('current_Project__Shared__Bank_ME_v3__Props__SM_H0046_Foodcrate','small_prop','flat_bottom','+Y',350,'Existing native crate; open ground clutter only, not a wall/roof attachment.'),
      ('current_Project__Shared__Bank_ME_v3__Props__SM_H0058_Gaz','small_prop','flat_bottom','+X',350,'Freestanding cylinder; no working equipment or utility hookup is inferred.'),
      ('current_Project__Shared__Bank_ME_v3__Props__SM_H0059_Grill_','small_prop','foot_contact','+X',350,'Small freestanding grill; native foot support must be read back.'),
      ('current_Project__Shared__Bank_ME_v3__Props__SM_H0089_Tires','small_prop','tyre_contact','+X',350,'Retained tyre prop; static ground clutter with existing material override.'),
      ('current_Palms_Pack_01__Add_Props__Grass__Meshes__SM_Grass_05_4','understory','grass_base','+X',180,'Historical native Lit image reviewed: sparse upright grass tuft, no palm geometry; base contact must be retained.'),
      ('current_Palms_Pack_01__Add_Props__Plants__Meshes__SM_Plant_06_2_G','understory','stem_base','+X',180,'Historical native Lit image reviewed: upright leafy ruderal stem. No species identification or area art acceptance claimed.'),
      ('current_Palms_Pack_01__Add_Props__Plants__Meshes__SM_Plant_07_2_G','understory','stem_base','+X',180,'Historical native Lit image reviewed: thin ground stem; yaw does not define a functional facing direction.'),
      ('current_Palms_Pack_01__Add_Props__Plants__Meshes__SM_Plant_07_5_G','understory','stem_base','+X',180,'Historical native Lit image reviewed: related stem variant; shares a fixed aggregate family budget.'),
      ('current_Palms_Pack_01__Add_Props__Plants__Meshes__SM_Plant_07_6_G','understory','stem_base','+X',180,'Historical native Lit image reviewed: related stem variant; shares a fixed aggregate family budget.'),
      ('current_Project__Shared__Bank_ME_v3__Buildings__SM_H0902_Slum_k_fbx','whole_building','building_base','+X',824,'Historical native Lit image reviewed: complete two-storey building with ladder. Suspicious cracked normal must be reviewed/repaired before eligibility.'),
      ('current_Project__Shared__Bank_ME_v3__Buildings__SM_H0016_Building_03','whole_building','building_base_full_measured_envelope','+Y',5682,'Historical native Lit image and source material derivative reviewed: complete multi-storey building. A visible preview floor is not established as mesh geometry. Retain full measured native bounds; no stretching, geometric cleanup or footprint shrink.')
    ]

EXTERNAL_IDS=['external.H0023','external.H0047','external.H0052','external.H0078','external.H0633','external.T1160','external.T1161','external.T1172','external.T1173','external.T1174','external.T1175']

def prepare():
    cat=read(SOURCE);records={r['asset_id']:r for r in cat['rows']}
    prep={r['asset_id']:r for r in read(PREP/'PREPARED_BANK.json')['rows']}
    selected=[]
    for aid,role,contact,forward,spacing,note in native_definitions():
        record=records[aid];r=prep[aid];rt=record['runtime'];measurement=r['native_measurement']
        assert not yes(rt['ExplicitHold']) and not record['hold_reasons'] and not r['named_holds_preserved'],aid
        assert not r['palm_hold_not_released'],aid
        assert measurement['vertex_scan'].startswith('complete'),aid
        assert measurement['dependencies']['unresolved_registry_packages']==[],aid
        assert sha(package_file(rt['ObjectPath'])).lower()==r['current_package_sha256'].lower(),aid
        bounds=measurement['vertex_bounds_cm'];zones='open_ground'
        anchor=bounds['min'][2]
        anchor_basis='exact_native_minimum_vertex_plus_individual_contact_review_required'
        if aid.endswith('SM_H0902_Slum_k_fbx'):
            anchor=0.0
            anchor_basis='Source/native signed axes agree within 0.00006 cm. Ten building-base vertices span the wall footprint at Z=0; the ladder extends to Z=-2.2491 cm and must not float the building. SOURCE_CONTACT_READBACK.json.'
        elif aid.endswith('SM_H0016_Building_03'):
            anchor=0.0
            anchor_basis='Native and source full bounds agree within 0.00016 cm. Building support plane at authored Z=0; sub-centimetre decorative extent is not a platform. SOURCE_CONTACT_READBACK.json.'
        elif aid.endswith('SM_H0034_Cart'):
            anchor=-2.0
            anchor_basis='Source/native axes agree within 0.000003 cm. Paired wheel minima are approximately -2 cm; the front support extends to -3.1296 cm. Allow 1.2 cm support penetration without geometry or tilt changes; native view still required.'
        if role=='street_prop':zones='roadside'
        if role=='whole_building':zones='building_yes|building_residential|building_house|building_apartments|building_commercial'
        selected.append({'asset_id':aid,'row_name':r['catalog_row_name'],'object_path':rt['ObjectPath'],
            'package_sha256':r['current_package_sha256'],'role':role,'placement_rule':RULES[role],
            'contact_kind':contact,'anchor_z_cm':anchor,
            'anchor_basis':anchor_basis,
            'bounds_cm':bounds,'forward_axis':forward,
            'forward_basis':'geographic_long_axis_for_whole_building; rotationally_unconstrained_for_vegetation_and_bins; individual_review_for_other_props',
            'native_scale':[1,1,1],'allowed_areas':AREAS,'allowed_zones':zones,
            'style_context':'mediterranean_urban','source_style_preserved':record['environment_style_set'],
            'family_id':rt['FamilyId'],'min_spacing_cm':spacing,
            'material_slots':measurement['material_slots'],'existing_instance_materials':cat.get('instance_materials',{}).get(rt['ObjectPath'],[]),
            'review_note':note,'historical_native_images':r['native_preview_sources'],
            'rights_state_preserved':record['recorded_rights_state'],
            'state':'configuration_saved_native_contact_material_review_pending',
            'activation_requires':'NATIVE_VALIDATION.json explicit per-asset ready=true with matching source SHA, contact/facing review, verified instance materials and no unresolved native dependency'})
    from expanded_native_contracts import expand
    selected=expand(selected,prep,records,AREAS,RULES)
    for job in selected:
        job['existing_instance_materials']=cat.get('instance_materials',{}).get(job['object_path'],[])
    write(HERE/'NATIVE_CONFIGURATIONS.json',{'schema':'environmentpipeline.bank_native_configuration.v2','decision_id':DECISION,
        'scope':'All additional measured native models without explicit/named/palm holds; no fixed shortlist cap.',
        'native_activation_completed':False,'rows':selected})
    manifest={r['asset_id']:r for r in read(PREP/'EXTERNAL_IMPORT_MANIFEST.json')}
    external=[]
    external_ids=list(EXTERNAL_IDS)
    for aid,item in manifest.items():
        p=prep[aid]
        if (p['prepared_source']['primary_render_object_count']==1
                and p['category'] in {'SmallProps','StreetProps','Buildings/Whole','Vegetation'}
                and p.get('required_consumer_context') in {'ground_prop_contact_clearance','whole_building_footprint_height_terrain_fit','vegetation_ground_fit'}
                and not p['named_holds_preserved'] and not p['palm_hold_not_released']
                and aid not in external_ids):
            external_ids.append(aid)
    for aid in external_ids:
        r=copy.deepcopy(manifest[aid]);record=records[aid];prepared=prep[aid]['prepared_source']
        assert not prep[aid]['named_holds_preserved'] and not prep[aid]['palm_hold_not_released']
        assert prepared['primary_render_object_count']==1,aid
        r.update(original_explicit_hold=record['runtime']['ExplicitHold'],hold_reasons_preserved=record['hold_reasons'],
            native_activation=False,activation_policy='Preserve every existing ExplicitHold flag. Native import/configuration is not hold release.',
            source_bounds_m=prepared['bounds_m'],source_dimensions_m=prepared['dimensions_m'],
            original_source_receipt=prepared['receipt'],native_import_status='pending_exclusive_editor_window',
            category=prep[aid]['category'],required_consumer_context=prep[aid].get('required_consumer_context'),
            primary_render_object_count=prepared['primary_render_object_count'])
        external.append(r)
    write(HERE/'EXTERNAL_IMPORT_QUEUE.json',external)
    # Technical interfaces are concrete existing consumers; no invented scene hosts.
    blocked=[]
    for r in prep.values():
        if r.get('required_consumer_context') in {'roof_or_wall_host_attachment','sign_host_attachment_or_measured_standalone_pole','linear_boundary_alignment','road_or_surface_host'}:
            blocked.append({'asset_id':r['asset_id'],'object_path':r['object_path'],'consumer':r['required_consumer_context'],'existing_holds':r['hold_reasons_preserved']})
    write(HERE/'HOST_DEPENDENT_ASSETS.json',{'implementation_status':'not_implemented_by_bank_chat','required_interface':{
        'roof_or_wall_host_attachment':['source_area_id','source_osm_id','host actor/component identity','host local surface frame and normal','support polygon','contact offset','clearance','owned replacement identity'],
        'sign_host_attachment_or_measured_standalone_pole':['sign type and host identity','readable outward facing','mount height','road orientation/context','owned replacement identity'],
        'linear_boundary_alignment':['source polyline','segment length','corner/end roles','terrain support','spacing and overlap policy','owned replacement identity'],
        'road_or_surface_host':['owning road/surface provider','lane/sidewalk/curb context','surface normal/contact','material consumer','owned replacement identity']},
        'retained_hda_behavior':'mount_sign/roof_anchor candidates fail unsupported_attachment_contract; no fence or road-drain host substitute is added.', 'assets':blocked})
    write(HERE/'BASELINE.json',{'catalog_source_sha256':sha(SOURCE),'catalog_csv_sha256':sha(CSV),'typed_catalog_sha256':digest([r['runtime'] for r in cat['rows']]),'enabled_before':sum(yes(r['runtime']['RunEligible']) for r in cat['rows']),'selected_native':len(selected),'selected_external_imports':len(external),'host_dependent_assets':len(blocked),'runtime_mutated':False})
    print(json.dumps({'saved_native_configurations':len(selected),'retained_import_jobs':len(external),'host_dependent_assets':len(blocked),'native_imported':0,'newly_enabled':0}))

if __name__=='__main__':
    prepare()
