"""Administrative manager succession only; no Unreal or native asset operation."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(r'C:\Users\USER\Documents\Unreal Projects\Environmentpipeline')
HERE = ROOT / 'Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer'
OLD = '01a106bc-2fde-7f23-9aa7-8ba413dc6245'
NEW = '01a10789-2e6a-7321-ad85-0a2964f8a937'
BANK = '01a1067c-5012-7550-b449-015b53c9d726'
LINK = 'Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/STATE.json'
UTC = datetime.datetime.now(datetime.timezone.utc).isoformat()

def read(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8-sig'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(rel, value):
    path = ROOT / rel
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

checkpoint_path = 'Staging/BankIntegration_2026-10-04/MANAGEMENT_TRANSFER_CHECKPOINT.json'
cp = read(checkpoint_path)
expected_dirty = [
    '/Game/Palms_Pack_01/Add_Props/Plants/Materials/MI_Plant_07_6_Leaves_G',
    '/Game/Palms_Pack_01/Add_Props/Plants/Materials/MI_Plant_07_6_Stem_G',
    '/Game/Palms_Pack_01/Add_Props/Plants/Meshes/SM_Plant_07_6_G',
]
assert cp['passed'] is False and cp['native_mutations'] is False
assert cp['before'] == cp['after'] and cp['state_unchanged'] is True
assert cp['after']['pid'] == 32508 and not cp['after']['dirty']['maps']
assert sorted(cp['after']['dirty']['content']) == sorted(expected_dirty)
assert cp['after']['cooking_paused'] is True
assert all(v == 0 for v in cp['after']['active_callback_handles'].values())
assert cp['catalog']['row_count'] == 1223 and cp['catalog']['enabled_total'] == 24
assert len(set(cp['catalog']['digests'].values())) == 1
source_rel = 'Staging/ModelBank/PermanentIntegration_2026-10-02/catalog_v4_source.json'
assert digest(ROOT / source_rel) == cp['catalog']['source_sha256']

assignment_rel = 'Staging/ManagedSystemsAstra_2026-10-04/ASSIGNMENTS.json'
activation_rel = 'Staging/ManagedSystemsAstra_2026-10-04/BANK_ACTIVATION.json'
bank_rel = 'Staging/BankIntegration_2026-10-04/ASSIGNMENT.json'
category_rel = 'Staging/BankIntegration_2026-10-04/CategoryBatches/ASSIGNMENT.json'
supplier_rel = 'Staging/NativeUnrealAssetSupply_2026-10-04/ASSIGNMENT.json'
owner_rel = 'Staging/ModelBank/EDITOR_OWNER.txt'
status_rel = 'Staging/ManagedSystemsAstra_2026-10-04/STATUS.txt'
state = read(LINK)
assert state['status'] == 'CREATING_SUCCESSOR_NATIVE_AUTHORING_PAUSED'
a, activation, bank, category, supplier = [read(p) for p in (assignment_rel, activation_rel, bank_rel, category_rel, supplier_rel)]
assert a['manager_thread_id'] == activation['manager_thread_id'] == bank['system_owner'] == category['system_manager_thread'] == supplier['manager_thread_id'] == OLD
last_lease = [line for line in (ROOT / owner_rel).read_text().splitlines() if line.strip()][-1]
assert last_lease == cp['lease']

protected = [source_rel,
    'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json',
    'Staging/ModelBank/PermanentIntegration_2026-10-02/AREA_PROFILE.json',
    'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json',
    'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration.umap',
    'Content/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration.umap',
]
before_protected = {p: digest(ROOT / p) for p in protected}
changed = [assignment_rel, activation_rel, bank_rel, category_rel, supplier_rel, owner_rel, status_rel, LINK, 'AGENTS.md', 'Staging/CURRENT_STATE.md', 'Staging/WORK_PLAN.md']
before = {}
for rel in changed:
    raw = (ROOT / rel).read_bytes()
    target = HERE / 'Before' / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists(), 'Do not overwrite a prior succession backup'
    target.write_bytes(raw)
    before[rel] = hashlib.sha256(raw).hexdigest()

succession = {'utc': UTC, 'previous_manager_thread_id': OLD, 'successor_manager_thread_id': NEW, 'receipt': LINK, 'native_clean_handoff': False, 'native_authoring_paused': True}
a['previous_manager_thread_id'] = OLD
a['manager_thread_id'] = NEW
a['management_succession'] = succession
a['phase'] = 'SUCCESSOR_MANAGER_ACTIVE_BANK_NATIVE_PAUSED_EXACT_DIRTY_ORIGINALS'
a['editor_activation'] = 'READ_ONLY_NATIVE_CHECKPOINT_RECOVERY_REQUIRED_PID32508'
a['editor'].update(current_actual_pid=32508, current_phase='BANK_READ_ONLY_RECOVERY_REQUIRED', current_dirty_maps=[], current_dirty_content=expected_dirty, current_checkpoint=checkpoint_path, warning='Current3dirty vendor buffers require exact preservation review. Prior stop/PID fields are historical. No native authoring or ordinary generation activated by succession.')
a['shared_files']['area_profiles_owner'] = 'Successor manager ' + NEW + ' only; workers submit immutable exact before-hash patches; preserve unrelated fields and instance overrides.'
a['other_owners']['bank'] = BANK + ' sole potential bank editor operator; paused for exact dirty-original recovery, then successor-reviewed content activation and concrete full category-batch consumption.'
write(assignment_rel, a)
activation['previous_manager_thread_id'] = OLD
activation['manager_thread_id'] = NEW
activation['management_succession'] = succession
activation['status'] = 'SUCCESSOR_COORDINATED_NATIVE_AUTHORING_PAUSED_DIRTY_ORIGINALS'
activation['native_authorized_now'] = False
activation['ordinary_generation_authorized'] = False
activation['current_native_checkpoint'] = checkpoint_path
activation['next'] = ['Successor coordinates read-only exact vendor-buffer diagnostics and preservation review', 'Supported safe recovery and fresh native preflight before content reactivation', 'Consume full existing category batches and supplier delivery', 'Merge exact shared-profile/native contracts then separately activate ordinary complete-output integration']
write(activation_rel, activation)
bank['previous_system_owner'] = OLD
bank['system_owner'] = NEW
bank['management_succession'] = succession
bank['status'] = 'NATIVE_AUTHORING_PAUSED_EXACT_DIRTY_VENDOR_PACKAGES;84imports/24active preserved; category deliveries pending actual integration'
bank['bank_runtime_apply'] = 'Paused. Successor manager owns actual-PID reactivation after exact dirty-original preservation/recovery and fresh native preflight. Read-only diagnostics remain assigned to the same bank operator.'
write(bank_rel, bank)
category['previous_system_manager_thread'] = OLD
category['system_manager_thread'] = NEW
category['management_succession'] = succession
write(category_rel, category)
supplier['previous_manager_thread_id'] = OLD
supplier['manager_thread_id'] = NEW
supplier['management_succession'] = succession
write(supplier_rel, supplier)

lease = (f'{UTC} OWNER=CODEX_BANK_INTEGRATION manager_thread_id={NEW} operator_thread_id={BANK} task=bank assigned_editor_PID=32508 '
    'map=/Game/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration activation=INSPECTION_ONLY '
    'scope=read_only_exact_dirty_original_preservation_recovery native_authorized_now=false ordinary_generation_authorized=false '
    'dirty_original_packages=3 native_handoff_clean=false management_transfer=true')
with (ROOT / owner_rel).open('a', encoding='utf-8') as stream:
    stream.write('\n' + lease + '\n')

paragraph = ('[decided/measured: Aviv, 2026-10-04, latest management succession] New GPT-6 Astra manager chat' + NEW +
    ' is the sole manager responsible for completing all retained system and full-bank work. Former manager chat' + OLD +
    ' has transferred shared management/profile ownership and will not issue competing activations. Current complete status and transfer: [ManagementTransfer/STATE.json](Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/STATE.json) and [STATUS_REPORT.txt](Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/STATUS_REPORT.txt). Existing category/supplier/system workers are retained; no duplicate chats or competing plan. Bank operator on solePID32508 is paused/read-only: exactly3dirty Palms_Pack_01 originals, mapclean/callbacks0. This is NOT a clean native handoff. Successor must coordinate preservation/recovery and fresh preflight before native authoring. Ordinary generation remainsfalse.84 external imports/bindings and24 active rows(22models+2materials) are retained progress, not a completion cap. New repaired road/Grass/map save/fresh reopen/regeneration and Iran semantic/building/consumer work remain open. Source seal/original maps/profiles/catalog/holds/87candidates preserved. Successor may assign exact bounded downstream repairs needed for already authorized completion, with existing owners/review/reseal/fresh startup; no source hot reload or implicit upstream promotion.\n\n')
for rel in ['AGENTS.md', 'Staging/CURRENT_STATE.md', 'Staging/WORK_PLAN.md']:
    path = ROOT / rel
    original = path.read_text(encoding='utf-8-sig')
    first, separator, rest = original.partition('\n')
    path.write_text(first + '\n\n' + paragraph + rest.lstrip('\r\n'), encoding='utf-8')

(ROOT / status_rel).write_text('Environmentpipeline current status — successor management,4October2026\n\n'
    f'Sole manager:{NEW} (GPT-6 Astra). Previous manager:{OLD}, administrative transfer complete; no competing profile/editor authoring.\n'
    'Read ManagementTransfer/STATUS_REPORT.txt for verified subsystem status and STATE.json for succession.\n'
    'Bank:84 external imports and bindings,153 material contracts,523 named saved packages;24 active rows(22models+2materials),6newmodels. No bank area generation/fresh reopen completed. Existing3category batches are active staging work and require actual bank consumption. Supplier180candidate jobs require bounded registration/migration/consumer repair.\n'
    'Native:solePID32508/originalShujaiya; mapclean,cookingpaused,autooff,callbacks0,officialEnginefalse;3exact dirty vendor plant packages. Content writes and ordinary generation are PAUSED. This is not a clean native handoff. Checkpoint:BankIntegration_2026-10-04/MANAGEMENT_TRANSFER_CHECKPOINT.json.\n'
    'Nonbank remaining:new sealed road authority correction nativeNOTRUN; Grass Lit/Rimal integration; final replacement/Bake/named map saves/fresh reopen/ordinary repeat; Iran r020 dependencies/semantic water/material/scatter/consumer integration; place-to-saved-map automation. Baseline receipts are preserved, not final new-repair acceptance.\n'
    'Successor owns exact preservation/recovery,next actual-PID activations,canonical profile merges,bounded worker repairs and full retained completion. Preserve originals/holds/87unapproved candidates; no SaveAll,pilots,migration of generator or Linear.\n', encoding='utf-8')

assert before_protected == {p: digest(ROOT / p) for p in protected}
assert read(assignment_rel)['manager_thread_id'] == read(activation_rel)['manager_thread_id'] == read(bank_rel)['system_owner'] == NEW
state.update(status='TRANSFERRED_TO_SUCCESSOR', successor_manager_thread_id=NEW, transferred_utc=UTC, successor_model='gpt-6-astra', previous_manager_shared_authoring_active=False, native_checkpoint_passed=False, checkpoint_sha256=digest(ROOT / checkpoint_path), native_lease_after=lease, protected_file_hashes=before_protected, report_sha256=digest(HERE / 'STATUS_REPORT.txt'))
write(LINK, state)
receipt = {'schema':'environmentpipeline.administrative_succession_receipt.v1', 'utc':UTC, 'previous_manager':OLD, 'successor':NEW, 'native_operation_performed':False, 'native_authoring_authorized':False, 'ordinary_generation_authorized':False, 'before_file_hashes':before, 'after_file_hashes':{p:digest(ROOT/p) for p in changed}, 'protected_file_hashes':before_protected, 'native_clean_handoff':False}
write('Staging/ManagedSystemsAstra_2026-10-04/ManagementTransfer/RECEIPT.json', receipt)
print(json.dumps({'status':state['status'],'successor':NEW,'protected_files_unchanged':True,'native_authoring_authorized':False,'ordinary_generation_authorized':False,'dirty_originals':3}))
