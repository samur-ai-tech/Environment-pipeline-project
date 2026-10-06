    def consumer_parameter_strings(self,w):
        """Prepare exact optional contracts; original definitions need no new parm."""
        tuples=w.get_parameter_tuples()
        assert tuples is not None,'Official parameter interface is unavailable'
        tuples={str(name):value for name,value in tuples.items()}
        strings={}
        def present(name,required=False):
            if name not in tuples:
                assert not required,'Promoted HDA lacks required parameter: '+name
                return False
            assert len(tuples[name].string_values)==1,'Consumer parameter must be one string: '+name
            return True
        semantic=self.p.get('landscape_semantics') is not None
        if present('semantic_runtime_binding_json',semantic):
            if semantic:
                binding=_semantic_prepared_binding(self.p,self.state['landscape_grass_connection'])
                prior=self.state.get('semantic_native_binding')
                assert prior is None or prior==binding,'Semantic receiver/source changed between complete cooks'
                self.state['semantic_native_binding']=binding
                strings['semantic_runtime_binding_json']=binding['json']
            else:
                # New definition on a legacy area must not inherit another area's token.
                strings['semantic_runtime_binding_json']=''
        building=self.p.get('building_rules_json') is not None
        if present('building_rules_json',building):
            if building:
                binding=_building_rules_binding(self.p)
                prior=self.state.get('building_rules_binding')
                assert prior is None or prior==binding,'Building policy/evidence changed between complete cooks'
                self.state['building_rules_binding']=binding
                strings['building_rules_json']=binding['json']
            else:
                # Preserve the definition's existing inference defaults. Only
                # remove stale cross-area evidence when no profile contract exists.
                raw=w.get_string_parameter_value('building_rules_json')
                if raw:
                    rules=json.loads(raw)
                    assert isinstance(rules,dict),'Malformed retained building defaults'
                    if 'content_input' in rules:
                        rules.pop('content_input')
                        strings['building_rules_json']=_consumer_json(rules)
                        self.state['cleared_stale_building_content_input']=True
        self.state['consumer_parameter_requests']=dict(strings)
        return strings

    def verify_consumer_receipt(self,receipt):
        """Persist exact producer evidence, then reject incomplete/mismatched output."""
        if self.p.get('landscape_semantics') is not None:
            keys=('semantic_surface_contract','semantic_surface_contract_sha256','semantic_surface_complete',
                  'semantic_grass_provider','semantic_nonweight_layers','semantic_hda_understory_suppressed',
                  'semantic_runtime_binding_sha256','semantic_consumer','semantic_native_postcook_verified')
            self.state['semantic_producer_receipt']={key:receipt.get(key) for key in keys}
            self.write()
            binding=_semantic_prepared_binding(self.p,self.state['landscape_grass_connection'])
            assert binding==self.state['semantic_native_binding'],'Semantic source/receiver changed after Cook'
            raw=receipt.get('semantic_surface_contract')
            assert isinstance(raw,dict) and raw.get('schema')=='environmentpipeline.semantic_landscape_contract.v1'
            assert receipt.get('semantic_surface_contract_sha256')==_consumer_digest(raw)
            assert receipt.get('semantic_surface_complete') is True,'Semantic surface is incomplete'
            assert receipt.get('semantic_native_postcook_verified') is False,'Producer cannot assert native postcook acceptance'
            token=binding['token']
            for key,value in {'area_id':token['area_id'],'source_package_sha256':token['source_package_sha256'],
                              'policy_sha256':token['consumer_contract_sha256'],'class_grid_sha256':binding['class_grid_sha256'],
                              'vegetation_provider':token['provider']}.items():
                assert raw.get(key)==value,'Semantic producer identity differs: '+key
            assert receipt.get('semantic_grass_provider')==token['provider']
            assert receipt.get('semantic_runtime_binding_sha256')==binding['sha256'],'HDA receiver acknowledgment differs'
            assert set(receipt['semantic_nonweight_layers'])==set(raw['auxiliary_layers'])
            assert set(raw['auxiliary_layers']).issubset(token['nonweight_layer_names'])
            assert set(raw['paint_layers']).union(raw['auxiliary_layers']).issubset(token['material_layer_names'])
            assert isinstance(receipt['nonbuilding_instances'],list)
            if token['provider']=='native_landscape_grass':
                assert receipt.get('semantic_hda_understory_suppressed') is True
                assert not any(item.get('role')=='understory' for item in receipt['nonbuilding_instances'])
            consumer=receipt['semantic_consumer']
            assert consumer['source_contract']==binding['source_contract']
            assert consumer['contract_sha256']==binding['consumer_contract_sha256'] and consumer['runtime_binding']==token
            self.state['semantic_producer_receipt_verified']=True
        if self.p.get('building_rules_json') is not None:
            keys=('building_dependencies_complete','building_content_revision','building_content_input_sha256',
                  'building_content_rejections','qualified_whole_building_records')
            self.state['building_consumer_receipt']={key:receipt.get(key) for key in keys}
            self.write()
            binding=_building_rules_binding(self.p)
            assert binding==self.state['building_rules_binding'],'Building evidence changed after Cook'
            assert receipt.get('building_content_input_sha256')==binding['content_input_sha256']
            assert receipt.get('building_dependencies_complete') is True,'Building content dependencies remain incomplete'

