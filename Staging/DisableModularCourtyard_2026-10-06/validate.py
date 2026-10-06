import hou,pathlib,json,hashlib,copy
D=pathlib.Path(__file__).parent;R=pathlib.Path('C:/Users/USER/Documents/Pipeline Environment/ModelBank/Modular_2026-10-04/ProceduralFamilies_Additional20')
read=lambda p:json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
build=read(D/'BUILD.json');hou.setUpdateMode(hou.updateMode.Manual);hou.hda.installFile(build['hda']['path'])
geo=hou.node('/obj').createNode('geo','RetainedBankValidation');asset=geo.createNode('trackb::geocity_city::15.0','GeoCity_Retained')
module=asset.hdaModule()
for name in ('building_assembly_contract_json','modular_pilot_enabled','module_test_enabled','bank_receipt_file'):
    template=asset.parm(name).parmTemplate();geo.addSpareParmTuple(template)
geo.parm('modular_pilot_enabled').set(0);geo.parm('module_test_enabled').set(0);geo.parm('bank_receipt_file').set('')
selected=geo.createNode('python','Native_Bank_Input')
selected.parm('python').set("g=hou.pwd().geometry();g.addAttrib(hou.attribType.Global,'bank_catalog_readback_json','');g.setGlobalAttribValue('bank_catalog_readback_json','{}')")
terrain=geo.createNode('python','Supported_Terrain_Input')
terrain.parm('python').set("g=hou.pwd().geometry();v=g.createVolume(1009,1009,1);v.setAllVoxels([2.75]*(1009*1009));a=g.addAttrib(hou.attribType.Prim,'name','');v.setAttribValue(a,'height')")
pads=geo.createNode('python','Family_Pad_Input')
native_points=geo.createNode('python','Retained_Official_Instance_Output')
native_points.setInput(0,selected);native_points.setInput(1,pads);native_points.setInput(2,terrain)
native_points.parm('python').set("hou.node(%r).hdaModule().cook_normal_building_assembly_points(hou.pwd())"%asset.path())

rows=[]
for p in read(D/'ASSIGNMENT.json')['profiles']:
 contract=read(p['path'])['building_assembly_contract'];contract=json.loads(json.dumps(contract).replace('\\\\','/'));contract['retired_building_module_prefixes']=['/Game/ModularCourtyard/']
 area='GazaRimal' if 'PermanentIntegration' in p['path'] else 'GazaShujaiya'
 families=module.procedural_bank_families(contract);assert len(families)==30
 prior=next(x for x in read(R/'SAVED_PROFILE_VALIDATION.json')['profiles'] if x['area']==area)
 for old in prior['automatic_selected']:
  f=old['feature'];rec=module.assembly_layout(f,contract);assert rec['style_family_id']==old['family_id'];assert all(not i['path'].startswith('/Game/ModularCourtyard/') for i in rec['wall_placements'])
 # Exercise actual retained point-output cook for the four formerly dark families plus one old family.
 for old in [x for x in prior['automatic_selected'] if x['id'] in ['H0909','H0098','H0099','H0107','H0108']]:
  f=old['feature'];geo.parm('building_assembly_contract_json').set(json.dumps(contract))
  pads.parm('python').set("f=%r\ng=hou.pwd().geometry();p=g.createPolygon()\nfor x,z in f['ring_xz_m']:\n q=g.createPoint();q.setPosition((x,f['base_m'],z));p.addVertex(q)\nfor k,v in [('source_area_id',f['area_id']),('source_osm_id',f['osm_id']),('base_m',f['base_m']),('height_m',f['height_m']),('height_rule',f['height_rule']),('building_use',f['building_use'])]:\n a=g.addAttrib(hou.attribType.Prim,k,v);p.setAttribValue(a,v)\n"%f)
  hou.setUpdateMode(hou.updateMode.AutoUpdate);native_points.cook(force=True);assert not native_points.errors();g=native_points.geometry();
  if not len(g.points()):print('EMPTY',area,old['id'],g.attribValue('bank_catalog_readback_json'),flush=True)
  assert len(g.points())>0;assert all(not x.attribValue('unreal_instance').startswith('/Game/ModularCourtyard/') for x in g.points())
 # Removing source registry must not re-enable the retired fallback.
 blocked=copy.deepcopy(contract);blocked.pop('source_family_registry_ref',None)
 f=dict(area_id=area,osm_id='courtyard_retirement_regression',ring_xz_m=[[-12,-8],[12,-8],[12,8],[-12,8]],base_m=2.75,height_m=6.4,height_rule='explicit',closed=True,holes=False,building_use='residential')
 legacy=module._RETIRED_COURTYARD_PREVIOUS_LAYOUT(f,blocked);assert any(i['path'].startswith('/Game/ModularCourtyard/') for i in legacy['wall_placements'])
 try:module.assembly_layout(f,blocked)
 except ValueError as error:assert str(error).startswith('retired_building_family:ModularCourtyard:')
 else:raise AssertionError('Retired fallback escaped guard')
 geo.parm('building_assembly_contract_json').set(json.dumps(blocked))
 pads.parm('python').set("f=%r\ng=hou.pwd().geometry();p=g.createPolygon()\nfor x,z in f['ring_xz_m']:\n q=g.createPoint();q.setPosition((x,f['base_m'],z));p.addVertex(q)\nfor k,v in [('source_area_id',f['area_id']),('source_osm_id',f['osm_id']),('base_m',f['base_m']),('height_m',f['height_m']),('height_rule',f['height_rule']),('building_use',f['building_use'])]:\n a=g.addAttrib(hou.attribType.Prim,k,v);p.setAttribValue(a,v)\n"%f)
 native_points.cook(force=True);assert not native_points.errors();g=native_points.geometry();receipt=json.loads(g.attribValue('bank_catalog_readback_json'));assert len(g.points())==0 and receipt['building_assembly']['unsupported_count']==1
 rows.append(dict(area=area,discovered_families=30,automatic_family_plans_passed=30,normal_output_cases_passed=5,retired_fallback_emitted_points=0,unsupported_count=1,passed=True))
(D/'VALIDATION.json').write_text(json.dumps(dict(hda=build['hda'],areas=rows,passed=True,unmatched_behavior='Existing normal cook reports unsupported original shell retained; no ModularCourtyard instances.'),indent=2));print('VALIDATION_PASS',len(rows),60)
