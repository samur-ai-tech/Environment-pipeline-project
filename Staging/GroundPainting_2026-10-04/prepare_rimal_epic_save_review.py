"""Staging-only root review of the completed Rimal material verification."""
import datetime, hashlib, json
from pathlib import Path

here = Path(__file__).resolve().parent
rev = here / 'Revision_2026-10-05'
def read_checked(name, expected):
    p = rev / name
    assert hashlib.sha256(p.read_bytes()).hexdigest() == expected
    return json.loads(p.read_text()), p

d, native = read_checked('EPIC_RESIDENT_RIMAL_verify_r031_epic_verify_PID25008.json', 'a561335794054f30a7ba3ce64025bf80078bded2666062d3d6fe727f27739ed1')
v, visual = read_checked('VISUAL_REVIEW_GazaRimal_epic_r031_PID25008.json', 'c6a7a81ee7036c6b1e4ce60047ab376bbd2e34217e834479da010b7a6342c833')
s, source = read_checked('EPIC_RESIDENT_RIMAL_CONSUMER_SCRIPT_REVIEW.json', '9b2a023d01678723cd0374d01861a89006bff7c5df65810400c29823c3d8cc96')
target = '/Game/Project/Areas/GazaRimal/BankIntegration_v015/Materials/MI_GeoCityGround'
assert d['pid'] == 25008 and d['area'] == 'GazaRimal'
assert d['status'] == 'IDENTITY_VERIFIED_READ_ONLY_EPIC_RESIDENT_RIMAL'
for k in ('complete_code_input_output_mip_identity_equal', 'preserved_1015_nodes', 'preserved_69_layer_names', 'preserved_grass', 'preserved_scene', 'preserved_cvars', 'preserved_original_files', 'preserved_epic_texture_properties', 'held_copy_unchanged', 'all_four_resources_strict_ready', 'preserved_resident_copy_files', 'copy_properties_match_except_policy_and_inactive_normal_gamma'):
    assert d[k] is True, k
assert d['dirty'] == {'maps': [], 'content': [target]}
assert v['save_approved_within_scope'] is True and v['named_save_scope'] == [target]
assert v['source_verify_receipt_sha256'] == hashlib.sha256(native.read_bytes()).hexdigest()
helper = here / 'native_revision_save.py'
assert hashlib.sha256(helper.read_bytes()).hexdigest() == 'b13b5037f8fa40bc21fffc32a2f6bac442d904e4a1832cac159d78f9e3ddb836'
review = {
    'schema': 'environmentpipeline.epic_rimal_root_graph_save_review.v1',
    'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'reviewer': '/root', 'pid': 25008, 'area': 'GazaRimal', 'world': d['world'],
    'master': '/Game/Project/Shared/SurfacePainting/Appearance_20261003/M_SurfaceBank_Natural.M_SurfaceBank_Natural',
    'graph_preserved': True, 'master_graph_delta': 'NONE',
    'authorized_ground_delta': 'Exactly27 reviewed Rimal child overrides:11Epic texture bindings,8scalars,8vectors. No graph edits or other packages.',
    'native_verify_receipt': str(native), 'native_verify_sha256': hashlib.sha256(native.read_bytes()).hexdigest(),
    'independent_source_review': str(source), 'independent_source_review_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'visual_review_receipt': str(visual), 'visual_review_sha256': hashlib.sha256(visual.read_bytes()).hexdigest(),
    'eligible_named_dirty_packages': [target], 'maps_clean': True,
    'ordinary_generation_run': False, 'visual_quality_or_user_acceptance': False,
}
out = rev / 'EPIC_GRAPH_SAVE_REVIEW_R031_PID25008.json'
args = here / 'ARGS_save_epic_r031.json'
assert not out.exists() and not args.exists()
out.write_text(json.dumps(review, indent=2), encoding='utf-8')
args.write_text(json.dumps({'action':'save','stage':'epic_r031','reviewed_visual_stage':'epic_r031','graph_review_receipt':str(out),'visual_review_receipt':str(visual)}, indent=2), encoding='utf-8')
print(json.dumps({'root_review':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'args':str(args),'only_save':target}))
