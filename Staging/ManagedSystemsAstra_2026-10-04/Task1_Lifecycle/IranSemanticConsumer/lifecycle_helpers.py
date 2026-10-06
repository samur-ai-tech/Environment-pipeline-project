"""Staged source fragment, embedded in the existing lifecycle module only."""

def _consumer_json(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def _consumer_digest(value):
    return hashlib.sha256(_consumer_json(value).encode('utf-8')).hexdigest()


def _consumer_hashref(reference):
    assert isinstance(reference,dict) and set(('path','sha256')).issubset(reference),'Missing hash-bound consumer reference'
    path=Path(reference['path'])
    assert path.is_absolute(),'Consumer reference must be absolute'
    raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==reference['sha256'],'Consumer evidence bytes changed: '+str(path)
    return json.loads(raw)


def _semantic_prepared_binding(profile,prepared):
    """Validate measured Task3 token against exact source and native receipt."""
    envelope=profile['landscape_semantics']
    assert envelope['schema']=='environmentpipeline.semantic_landscape_profile.v2'
    path=Path(profile['source']);raw=path.read_bytes();source=json.loads(raw)
    source_sha=hashlib.sha256(raw).hexdigest()
    assert source_sha==envelope['source_package_sha256'],'Semantic source package changed'
    ref=source['semantic_consumer_contract']
    policy_path=(path.parent/ref['path']).resolve()
    policy=_consumer_hashref({'path':str(policy_path),'sha256':ref['sha256']})
    assert ref['sha256']==envelope['consumer_contract_sha256'],'Semantic consumer contract changed'
    assert policy['schema']=='environmentpipeline.semantic_consumer.v2'
    geography_ref=source['semantic_geography'];geography_path=(path.parent/geography_ref['path']).resolve()
    geography=_consumer_hashref({'path':str(geography_path),'sha256':geography_ref['sha256']})
    assert policy['semantic_manifest_sha256']==geography_ref['sha256']
    grid_ref=geography['class_grid'];grid_bytes=(geography_path.parent/grid_ref['path']).read_bytes()
    assert hashlib.sha256(grid_bytes).hexdigest()==grid_ref['sha256']==envelope['class_grid_sha256'],'Semantic class grid changed'
    assert len(grid_bytes)==grid_ref['bytes']
    token=prepared['semantic_runtime_binding'];native=prepared['native_binding_receipt']
    assert isinstance(token,dict) and isinstance(native,dict),'Measured semantic preparation is missing'
    grass=policy['grass']
    assert grass['provider']=='native_landscape_grass','Current reviewed native semantic consumer supports only native_landscape_grass'
    expected={'schema':'environmentpipeline.semantic_runtime_binding.v1','area_id':source['area_id'],
              'source_package_sha256':source_sha,'consumer_contract_sha256':ref['sha256'],
              'landscape_material':profile['landscape_material'],'provider':grass['provider'],
              'mask_layer':grass['mask_layer'],'grass_mesh_paths':grass['mesh_paths'],
              'coverage':grass['coverage'] if grass['provider']=='native_landscape_grass' else 0.0,
              'density_per_10m2':grass['density_per_10m2'],
              'catalog_sha256':profile['catalog_sha256'],'native_binding_receipt_sha256':_consumer_digest(native)}
    assert source['area_id']==policy['area_id']==profile['map'].split('/')[4]
    for key,value in expected.items():assert token.get(key)==value,'Prepared semantic binding differs: '+key
    assert token['material_graph_prepared'] is True,'Native material graph is not prepared'
    assert token['canonical_area_eligibility_verified'] is True and token['grass_bindings_verified'] is True
    assert profile['landscape_grass']['enabled'] is True
    assert token.get('output_weight_readback_verified') is False and token.get('visible_lit_grass_verified') is False,'Preparation cannot assert generated output or appearance'
    assert native['landscape_material']==token['landscape_material']
    assert native['material_layer_names']==token['material_layer_names']
    assert len(token['material_layer_names'])==len(set(token['material_layer_names']))
    assert set(policy['class_material_targets'].values()).issubset(token['material_layer_names'])
    return {'token':json.loads(_consumer_json(token)),'json':_consumer_json(token),'sha256':_consumer_digest(token),
            'source_package_sha256':source_sha,'consumer_contract_sha256':ref['sha256'],
            'class_grid_sha256':envelope['class_grid_sha256'],'source_contract':policy,
            'native_binding_receipt':native,'native_output_verified':False}


def _building_rules_binding(profile):
    """Forward reviewed building policy and pinned evidence; never qualify it."""
    value=profile.get('building_rules_json')
    if value is None:return None
    if isinstance(value,str):value=json.loads(value)
    assert isinstance(value,dict) and value.get('schema')=='environmentpipeline.building_rules.v1'
    # Normalize file-reference separators before computing the exact wire digest.
    rules=json.loads(_hda_json(value))
    content=rules.get('content_input')
    assert isinstance(content,dict),'Building content input requires a hashref or atomic inline object'
    if 'schema' not in content:
        payload=_consumer_hashref(content);input_sha=content['sha256']
    else:payload=content;input_sha=_consumer_digest(content)
    source_path=Path(profile['source']);source_bytes=source_path.read_bytes();source=json.loads(source_bytes)
    source_sha=hashlib.sha256(source_bytes).hexdigest()
    assert payload.get('schema')=='environmentpipeline.building_content_input.v1'
    assert payload.get('source_sha256')==source_sha and payload.get('area_id')==source['area_id'],'Building input does not match exact geographic source'
    assert source['area_id']==profile['map'].split('/')[4]
    refs=payload['refs']
    assert {'adopted','role_contracts','whole_consumer'}.issubset(refs),'Building qualification evidence references missing'
    for reference in refs.values():_consumer_hashref(reference)
    if payload.get('inference_policy'):
        assert payload['inference_policy']['source_sha256']==source_sha,'Building inference policy source mismatch'
    return {'json':_consumer_json(rules),'sha256':_consumer_digest(rules),'source_sha256':source_sha,
            'content_input_sha256':input_sha,'evidence_refs':refs,
            'qualification_verified_by_lifecycle':False,'qualification_owner':'HDA building evidence consumer'}
