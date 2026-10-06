"""Read-only native checkpoint for coordinated manager succession; no asset saves."""
import csv
import datetime
import json
import os
import runpy
import sys
from pathlib import Path
import unreal
import bank_contracts as C


def checkpoint():
    native = runpy.run_path(str(C.HERE / 'native_bank_ops.py'))
    try:
        preflight = {'passed': True, 'state': native['preflight']()}
    except Exception as exc:
        # A failing write preflight must still be documented read-only for transfer.
        preflight = {'passed': False, 'error': repr(exc)}
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
    actors = actor_sub.get_all_level_actors()
    hdas = [a for a in actors if a.get_class().get_name() == 'HoudiniAssetActor']
    wrappers = [(a, unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(None, a)) for a in hdas]

    def snapshot():
        return {
            'pid': os.getpid(),
            'world': unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name(),
            'dirty': native['dirty'](),
            'cooking_paused': api.is_asset_cooking_paused(),
            'official_session_valid': api.is_session_valid(),
            'hda_flags': [{'actor': a.get_path_name(), 'auto_cook': w.is_auto_cooking_enabled(), 'auto_bake': w.is_auto_bake_enabled()} for a, w in wrappers],
            'autosave': unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorLoadingSavingSettings')).get_editor_property('bAutoSaveEnable'),
            'active_callback_handles': {name: sum(getattr(run, key, None) is not None for run in getattr(sys.modules.get(name), 'ACTIVE', []) for key in ('watch_tick', 'save_tick', 'tick_handle', '_pending_correction')) for name in ('geocity_bank_workflow', 'geocity_roadbld_workflow')}
        }

    before = snapshot()
    result = {
        'schema': 'environmentpipeline.bank_management_transfer_checkpoint.v1',
        'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'operator_thread': '01a1067c-5012-7550-b449-015b53c9d726',
        'lease': [s for s in (C.ROOT / 'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()][-1],
        'preflight': preflight,
        'before': before,
        'ordinary_generation_authorized': False,
        'native_mutations': False,
        'content_saved_by_checkpoint': [],
        'map_saved_by_checkpoint': False,
        'safe_boundary': 'No native transaction pending in this bank chat. Category chats own disjoint file-only job directories; none has an editor lease.'
    }
    try:
        source = C.read(C.SOURCE)
        with C.CSV.open(encoding='utf-8-sig', newline='') as f:
            csv_rows = list(csv.DictReader(f))
        table = unreal.load_asset('/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4')
        table_rows = json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
        source_rows = [r['runtime'] for r in source['rows']]
        digests = {'source': C.digest(source_rows), 'csv': C.digest(csv_rows), 'native_table': C.digest(table_rows)}
        result['catalog'] = {
            'digests': digests, 'source_sha256': C.sha(C.SOURCE), 'csv_sha256': C.sha(C.CSV),
            'row_count': len(table_rows), 'enabled_total': sum(C.yes(r['RunEligible']) for r in table_rows),
            'enabled_by_role': {role: sum(C.yes(r['RunEligible']) and r['RequestRole'] == role for r in table_rows) for role in sorted({r['RequestRole'] for r in table_rows if C.yes(r['RunEligible'])})},
            'new_native_enabled_ids': [r['asset_id'] for r in source['rows'] if C.yes(r['runtime']['RunEligible']) and r['runtime']['DecisionId'] == C.DECISION],
            'new_imported_connected_ids': [r['asset_id'] for r in source['rows'] if r.get('native_bank_integration', {}).get('imported_and_saved')],
            'saved_import_receipts': sum(bool(C.read(p).get('saved')) for p in C.HERE.glob('IMPORTED_external_*.json'))
        }
        result['profiles'] = []
        for p in (C.BANK / 'AREA_PROFILE.json', C.ROOT / 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json'):
            profile = C.read(p)
            result['profiles'].append({'path': str(p), 'file_sha256': C.sha(p), 'catalog_sha256': profile.get('catalog_sha256'), 'release_catalog_sha256': profile.get('release', {}).get('catalog_sha256'), 'map': profile.get('map')})
        result['category_assignment'] = C.read(C.HERE / 'CategoryBatches/ASSIGNMENT.json')
        assert len(set(digests.values())) == 1, 'source_csv_native_digest_mismatch'
        assert all(p['catalog_sha256'] == digests['source'] and p['release_catalog_sha256'] == digests['source'] for p in result['profiles']), 'profile_catalog_mismatch'
        assert not before['dirty']['maps'] and not before['dirty']['content'], 'dirty_packages_at_transfer'
        assert preflight['passed'], 'bank_write_preflight_failed'
        assert before['cooking_paused'] and not before['autosave']
        assert not any(before['active_callback_handles'].values())
        assert all(not f['auto_cook'] and not f['auto_bake'] for f in before['hda_flags'])
        result['passed'] = True
    except Exception as exc:
        result.update(passed=False, error=repr(exc))
    finally:
        result['after'] = snapshot()
        result['state_unchanged'] = before == result['after']
        result['passed'] = bool(result.get('passed') and result['state_unchanged'])
        C.write(C.HERE / 'MANAGEMENT_TRANSFER_CHECKPOINT.json', result)
    print(json.dumps({k: result.get(k) for k in ('passed', 'error', 'state_unchanged', 'before', 'catalog', 'profiles')}, ensure_ascii=False))
    return result


if __name__ == '__main__':
    checkpoint()
