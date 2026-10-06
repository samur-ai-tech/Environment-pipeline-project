"""Read-only probe of the parallel-editor safeguard (brief 1, 2026-10-06).

Runs the sealed guard's parallel_editor_report outside any editor, with the engine
Python, and writes one receipt Probes/PROBE_<utc>.json (opened with 'x'). No editor,
map, Content or lease write. The guard source is read from Content/Python and checked
against the sealed manifest unless --guard names a working copy (then recorded as
unsealed). Usage:
  python -I -B probe_parallel_editors.py [--project <root>] [--guard <file>] [--out <dir>]
Cases: (a) measured live editors and records for each canonical profile (launcher view,
own_pid=None); (b) the same inputs with each valid record left out, expecting a refusal
that names the unrecorded PID; (c) the pairing table with synthetic records (sky on
Rimal, bank, Iran generation with and without read_scope); (d) a record whose start
time differs from the live process, expecting a refusal.
"""
import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RIMAL_MAP = '/Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration'


def load_guard(project, guard_file):
    manifest = json.loads((project / 'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json').read_text(encoding='utf-8'))
    expected = manifest['modules']['geocity_runtime_guard']['sha256']
    path = Path(guard_file).resolve() if guard_file else (project / 'Content/Python/geocity_runtime_guard.py').resolve()
    source = path.read_bytes()
    actual = hashlib.sha256(source).hexdigest()
    if guard_file is None and actual != expected:
        raise SystemExit('Content/Python/geocity_runtime_guard.py differs from the sealed manifest (%s != %s)' % (actual, expected))
    namespace = {'__name__': 'geocity_runtime_guard', '__file__': str(path)}
    exec(compile(source, str(path), 'exec', dont_inherit=True), namespace)
    if 'parallel_editor_report' not in namespace:
        raise SystemExit('this guard revision has no parallel_editor_report')
    return namespace, {'guard_file': str(path), 'guard_sha256': actual, 'manifest_guard_sha256': expected,
                       'guard_verified_against_manifest': actual == expected,
                       'manifest_sha256': hashlib.sha256((project / 'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json').read_bytes()).hexdigest()}


def synthetic(pid, start, write, original_map=None, read=None, released=None):
    record = {'schema': 'environmentpipeline.parallel_editor.v1', 'pid': pid, 'process_start_utc': start,
              'task': 'synthetic_probe_record', 'write_scope': list(write), 'file_write_scope': [],
              'original_map': original_map, 'released_utc': released}
    if read is not None:
        record['read_scope'] = list(read)
    return {'path': 'synthetic/EDITOR_%d.json' % pid, 'sha256': hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest(),
            'record': record, 'error': None}


def brief(report):
    return {'verdict': report['verdict'], 'reasons': report['reasons'], 'summary': report.get('summary'),
            'other_editors': [{k: row[k] for k in ('pid', 'start_utc', 'record', 'record_sha256', 'task')} for row in report['other_editors']],
            'stale_records': report['stale_records'], 'invalid_records': report['invalid_records'], 'own_record': report['own_record']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', default=str(HERE.parents[1]))
    parser.add_argument('--guard', default=None, help='working-copy guard (recorded as unsealed); default = sealed Content/Python guard')
    parser.add_argument('--out', default=str(HERE / 'Probes'))
    args = parser.parse_args()
    project = Path(args.project).resolve(strict=True)
    g, provenance = load_guard(project, args.guard)
    utc = datetime.datetime.now(datetime.timezone.utc)
    live = g['live_editors']()
    records = g['read_parallel_records'](project)
    profiles = {p.parent.name: p for p in sorted((project / 'Staging/ModelBank').glob('*/AREA_PROFILE.json'))}
    scopes = {name: g['generation_scope'](path, project) for name, path in profiles.items()}
    receipt = {'schema': 'environmentpipeline.parallel_editor_probe.v1', 'utc': utc.isoformat(), 'project': str(project),
               'read_only': True, 'writes': ['this receipt only'], 'guard': provenance,
               'measured': {'live_editors': [{'pid': pid, 'start_utc': start} for pid, start in live],
                            'records': [{'path': e['path'], 'sha256': e['sha256'], 'pid': (e['record'] or {}).get('pid'),
                                         'task': (e['record'] or {}).get('task'), 'released_utc': (e['record'] or {}).get('released_utc'),
                                         'error': e['error']} for e in records],
                            'profiles': {name: {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                                'scope': scopes[name]} for name, path in profiles.items()}},
               'cases': {}}
    # (a) measured inputs, launcher view
    receipt['cases']['a_measured_launcher_view'] = {name: brief(g['parallel_editor_report'](project, path, None, live=live, records=records))
                                                    for name, path in profiles.items()}
    # (b) each valid record left out -> the live PID becomes unrecorded
    left_out = {}
    for entry in records:
        if entry['record'] is None:
            continue
        pid = int(entry['record']['pid'])
        if pid not in dict(live):
            continue
        rest = [e for e in records if e is not entry]
        left_out[entry['path']] = {name: brief(g['parallel_editor_report'](project, path, None, live=live, records=rest))
                                   for name, path in profiles.items()}
    receipt['cases']['b_record_left_out'] = left_out
    # (c) pairing table with synthetic records, synthetic live list (5200 = other, 9000 = this editor)
    T0, T1 = '2026-10-06T16:00:00.0000000Z', '2026-10-06T16:05:00.0000000Z'
    rimal = scopes.get('PermanentIntegration_2026-10-02')
    iran = scopes.get('Iran_38196167_46086167_4km')
    others = {'sky_on_rimal': synthetic(5200, T0, ['/Game/Project/Shared/Atmosphere/ReusableSky/', RIMAL_MAP], RIMAL_MAP),
              'bank_imports': synthetic(5200, T0, ['/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4',
                                                   '/Game/Project/Shared/ModelBank/Prepared',
                                                   '/Game/Project/Shared/ModelBank/Materials/BankIntegration_20261004'])}
    if iran:
        others['iran_generation_no_read_scope'] = synthetic(5200, T0, iran['write'], iran['map'])
        others['iran_generation_with_read_scope'] = synthetic(5200, T0, iran['write'], iran['map'], read=iran['read'])
    if rimal:
        others['rimal_generation_with_read_scope'] = synthetic(5200, T0, rimal['write'], rimal['map'], read=rimal['read'])
    table = {}
    for label, other in others.items():
        table[label] = {}
        for name, path in profiles.items():
            own = synthetic(9000, T1, scopes[name]['write'], scopes[name]['map'], read=scopes[name]['read'])
            report = g['parallel_editor_report'](project, path, 9000, live=[(5200, T0), (9000, T1)], records=[other, own])
            table[label][name] = {'verdict': report['verdict'], 'reasons': report['reasons']}
    receipt['cases']['c_pairing_table'] = table
    # (d) wrong start time (PID reuse) and released record for a live PID
    name, path = next(iter(profiles.items()))
    own = synthetic(9000, T1, scopes[name]['write'], scopes[name]['map'])
    wrong = g['parallel_editor_report'](project, path, 9000, live=[(5200, '2026-10-06T17:00:00.0000000Z'), (9000, T1)],
                                        records=[others['sky_on_rimal'], own])
    released = g['parallel_editor_report'](project, path, 9000, live=[(5200, T0), (9000, T1)],
                                           records=[synthetic(5200, T0, ['/Game/X/'], released='2026-10-06T16:30:00Z'), own])
    unrecorded = g['parallel_editor_report'](project, path, 9000, live=[(5200, T0), (9000, T1)], records=[own])
    receipt['cases']['d_invalid_records'] = {'profile': name, 'wrong_start_time': brief(wrong), 'released_but_live': brief(released),
                                             'no_record_at_all': brief(unrecorded)}
    expectations = {
        'c_sky_vs_rimal_refused': table['sky_on_rimal'].get('PermanentIntegration_2026-10-02', {}).get('verdict') == 'REFUSE',
        'c_sky_vs_iran_pass': table['sky_on_rimal'].get('Iran_38196167_46086167_4km', {}).get('verdict') == 'PASS',
        'c_sky_vs_shujaiya_pass': table['sky_on_rimal'].get('GazaShujaiyaIntegration_2026-10-02', {}).get('verdict') == 'PASS',
        'c_bank_refused_everywhere': all(row['verdict'] == 'REFUSE' for row in table['bank_imports'].values()),
        'd_wrong_start_refused': wrong['verdict'] == 'REFUSE',
        'd_released_refused': released['verdict'] == 'REFUSE',
        'd_unrecorded_refused_names_pid': unrecorded['verdict'] == 'REFUSE' and any('PID 5200' in r for r in unrecorded['reasons']),
        'b_left_out_refused': all(all(v['verdict'] == 'REFUSE' for v in case.values()) for case in left_out.values()) if left_out else None}
    receipt['expectations'] = expectations
    receipt['all_expectations_met'] = all(v in (True, None) for v in expectations.values())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    target = out / ('PROBE_' + utc.strftime('%Y%m%dT%H%M%SZ') + '.json')
    with target.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
    print(json.dumps({'receipt': str(target), 'guard_verified_against_manifest': provenance['guard_verified_against_manifest'],
                      'live_editors': receipt['measured']['live_editors'], 'records': len(records),
                      'a_measured': {k: v['verdict'] for k, v in receipt['cases']['a_measured_launcher_view'].items()},
                      'a_first_reasons': {k: v['reasons'][:1] for k, v in receipt['cases']['a_measured_launcher_view'].items()},
                      'expectations': expectations, 'all_expectations_met': receipt['all_expectations_met']}, indent=2))
    return 0 if receipt['all_expectations_met'] else 1


if __name__ == '__main__':
    sys.exit(main())
