"""Owner-executed HDA compiler. Preparation alone never imports hou or writes HDA.

Only the exact manager-reserved external derivative is a valid destination.
The active r018 HDA, source, graphs, profiles and Unreal packages stay untouched.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = Path('C:/Users/USER/Documents/Pipeline Environment/Houdini/GeoCity_city_v015_PermanentBank')
RESERVED = BASE/'revisions/20261005_modular_source_families_v001'
DESTINATION = RESERVED/'GeoCity_city_v015_PermanentBank_ModularFamilies_v001.hdalc'
TYPE_NAME = 'trackb::geocity_city::15.0'
BASE_MODULE_SHA = 'e67b6e15ab9214c7b1b6d4c9dca454430e56e72935250100f5f05771e529804b'
BASE_HDA_SHA = '61303c1559b82daa7afca90213725dfde691905bf551ab1ef7e373e740cb8440'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_ref(ref):
    path = Path(ref['path']); assert sha(path) == ref['sha256'], ('changed_input', path)
    return json.loads(path.read_text(encoding='utf-8-sig'))


def graph(asset):
    return [{'name': node.name(), 'type': node.type().name(),
        'inputs': [n.name() if n else None for n in node.inputs()]} for node in sorted(asset.children(), key=lambda n: n.name())]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--activation', required=True)
    parser.add_argument('--activation-sha256', required=True)
    args = parser.parse_args()
    activation_path = Path(args.activation); assert sha(activation_path) == args.activation_sha256
    activation = json.loads(activation_path.read_text(encoding='utf-8-sig'))
    assert activation['schema'] == 'environmentpipeline.modular_retained_hda_activation.v1'
    assert activation['approved'] and activation['manager_thread_id']
    assert activation['staged_owner_thread_id'] == '01a10c07-cd82-7871-8450-30b7e1001e02'
    assert 'compile_reserved_dated_derivative' in activation['allowed_actions']
    assert Path(activation['destination']).resolve() == DESTINATION.resolve()
    assert DESTINATION.resolve().is_relative_to(RESERVED.resolve()) and RESERVED.resolve().is_relative_to(BASE.resolve())
    inputs = checked_ref(activation['candidate_inputs_ref'])
    module_path = BASE/'geocity_city_module.py'; hda_path = BASE/'GeoCity_city_v015_PermanentBank.hdalc'
    assert sha(module_path) == BASE_MODULE_SHA and sha(hda_path) == BASE_HDA_SHA
    assert inputs['retained_module']['sha256'] == BASE_MODULE_SHA and inputs['retained_hda']['sha256'] == BASE_HDA_SHA
    append_path = Path(inputs['candidate_append']['path']); assert sha(append_path) == inputs['candidate_append']['sha256']
    # Actual native contract must exist before the manager executes authoring.
    native_registry = checked_ref(activation['native_registry_ref'])
    assert native_registry['schema'] == 'environmentpipeline.retained_source_family_registry.v1'
    assert any(e.get('enabled') and e.get('execution_mode') in ('qualification', 'connection')
        and e.get('native_manifest_ref') for e in native_registry['families'])
    for entry in native_registry['families']:
        if entry.get('enabled'):
            checked_ref(entry['native_manifest_ref'])
    combined = module_path.read_text(encoding='utf-8')+'\n\n'+append_path.read_text(encoding='utf-8')
    compile(combined, str(RESERVED/'geocity_city_module.py'), 'exec')
    # The first native import occurs only after explicit pinned activation above.
    import hou
    hou.setUpdateMode(hou.updateMode.Manual)
    hou.hda.installFile(str(hda_path))
    original = next(d for d in hou.hda.definitionsInFile(str(hda_path)) if d.nodeTypeName() == TYPE_NAME)
    assert original.sections()['PythonModule'].contents() == module_path.read_text(encoding='utf-8')
    base_asset = hou.node('/obj').createNode('geo', 'source_family_base_readback').createNode(TYPE_NAME, 'city', exact_type_name=True)
    base_asset.allSubChildren(sync_delayed_definition=True)
    original_graph = graph(base_asset)
    assert base_asset.node('normal_building_assembly_points') and base_asset.parm('building_assembly_contract_json')
    assert base_asset.node('normal_building_assembly_points').inputs()[0].name() == 'nonbuilding_catalog_selector'
    assert base_asset.node('catalog_wholebuilding_replacement').inputs()[1].name() == 'normal_building_assembly_points'
    base_asset.parent().destroy()
    RESERVED.mkdir(parents=True, exist_ok=True)
    resumed_saved_derivative = DESTINATION.exists()
    if resumed_saved_derivative:
        # A previous compiler invocation may have saved this exact definition
        # before its final readback. Reconcile its contents, never blindly copy.
        existing = next(d for d in hou.hda.definitionsInFile(str(DESTINATION)) if d.nodeTypeName() == TYPE_NAME)
        assert existing.sections()['PythonModule'].contents() == combined
        existing_protocol = json.loads(existing.sections()['SourceFamilyProtocol'].contents())
        assert existing_protocol['candidate_append_sha256'] == sha(append_path)
        assert existing_protocol['native_registry_ref'] == activation['native_registry_ref']
    else:
        original.copyToHDAFile(str(DESTINATION), new_name=TYPE_NAME,
            new_menu_name='GeoCity retained v015 with source-derived families v001')
    hou.hda.installFile(str(DESTINATION))
    saved = next(d for d in hou.hda.definitionsInFile(str(DESTINATION)) if d.nodeTypeName() == TYPE_NAME)
    saved.addSection('PythonModule', combined)
    saved.addSection('SourceFamilyProtocol', json.dumps({'candidate_append_sha256': sha(append_path),
        'activation_ref': {'path': str(activation_path), 'sha256': args.activation_sha256},
        'native_registry_ref': activation['native_registry_ref'], 'ordinary_selection_enabled': False,
        'ordinary_selection_configured': any(e.get('enabled') and e.get('execution_mode') == 'connection'
            for e in native_registry['families'])}, sort_keys=True))
    saved.save(str(DESTINATION))
    derivative = hou.node('/obj').createNode('geo', 'source_family_derivative_readback').createNode(TYPE_NAME, 'city', exact_type_name=True)
    derivative.allSubChildren(sync_delayed_definition=True)
    assert Path(derivative.type().definition().libraryFilePath()).resolve() == DESTINATION.resolve(), \
        derivative.type().definition().libraryFilePath()
    assert graph(derivative) == original_graph, 'Retained SOP graph changed unexpectedly.'
    assert saved.sections()['PythonModule'].contents() == combined
    assert sha(module_path) == BASE_MODULE_SHA and sha(hda_path) == BASE_HDA_SHA
    (RESERVED/'geocity_city_module.py').write_text(combined, encoding='utf-8')
    receipt = {'schema': 'environmentpipeline.modular_retained_hda_build.v1', 'passed': True,
        'hda': str(DESTINATION), 'hda_sha256': sha(DESTINATION), 'type': TYPE_NAME,
        'resumed_saved_derivative': resumed_saved_derivative,
        'module_sha256': sha(RESERVED/'geocity_city_module.py'), 'base_module_sha256': BASE_MODULE_SHA,
        'base_hda_sha256': BASE_HDA_SHA, 'retained_sop_graph_unchanged': True,
        'houdini_version': hou.applicationVersionString(), 'actual_stage_cook': False,
        'separate_candidate_checks_run': False,
        'separate_candidate_checks_reason': 'Latest direct user requested connection without additional tests; compilation and immutable input guards are part of this operation.',
        'official_engine_native_output': False, 'ordinary_selection_enabled': False,
        'native_registry_ref': activation['native_registry_ref'], 'retained_graph': original_graph}
    (RESERVED/'BUILD_RECEIPT.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    derivative.parent().destroy()
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
