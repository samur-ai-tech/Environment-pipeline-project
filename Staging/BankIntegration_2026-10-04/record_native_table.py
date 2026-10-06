"""Retain actual typed native table rows for the ordinary-generation handoff."""
import csv
import json
import os
import bank_contracts as C

def record():
    import unreal
    import native_bank_ops as N
    before = N.preflight()
    table_path = '/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4'
    table = unreal.load_asset(table_path)
    actual = json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(table))
    typed = C.typed_rows(actual)
    source = C.read(C.SOURCE)
    with C.CSV.open(encoding='utf-8-sig', newline='') as handle:
        csv_rows = list(csv.DictReader(handle))
    assert typed == C.typed_rows(csv_rows) == C.typed_rows([r['runtime'] for r in source['rows']])
    assert N.dirty() == before['dirty']
    assert table_path not in before['dirty']['content'], 'table_has_unsaved_changes'
    digest = C.digest(actual)
    destination = C.HERE / ('NATIVE_TABLE_TYPED_' + digest + '_PID' + str(os.getpid()) + '.json')
    receipt = {'schema': 'environmentpipeline.actual_native_typed_table_readback.v1',
               'pid': os.getpid(), 'world': before['world'], 'table': table_path,
               'native_table_package_sha256': C.sha(C.package_file(table_path)),
               'source_sha256': C.sha(C.SOURCE), 'csv_sha256': C.sha(C.CSV),
               'digest': digest, 'row_count': len(typed), 'typed_rows': typed,
               'native_source_csv_typed_equal': True, 'dirty_unchanged': True,
               'native_table_dirty': False, 'content_or_map_saved': False,
               'binary_table_reload_performed_by_this_readback': False}
    if destination.exists():
        assert C.read(destination) == receipt, 'immutable_native_table_receipt_collision'
    else:
        with destination.open('x', encoding='utf-8') as handle:
            json.dump(receipt, handle, indent=2, ensure_ascii=False, allow_nan=False)
            handle.write('\n')
    return {'receipt': str(destination), 'sha256': C.sha(destination), 'digest': digest, 'rows': len(typed)}

if __name__ == '__main__':
    print(json.dumps(record()))
