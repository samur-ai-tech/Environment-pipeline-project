"""Read-only verification of saved native evidence and production preservation."""
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BANK = HERE.parent
PROJECT = BANK.parents[2]

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    pins, conflicts, failures = {}, [], []
    part_receipts = [p for p in (BANK / 'Receipts').glob('*/*.json') if p.name != 'FAMILY.json']
    for p in part_receipts:
        value = read(p)
        assert value['named_saved']
        for package, expected in value['saved_packages'].items():
            if package in pins and pins[package] != expected:
                conflicts.append(package)
            pins[package] = expected
    for package, expected in pins.items():
        p = PROJECT / 'Content' / (package[6:] + '.uasset')
        actual = sha(p) if p.exists() else None
        if actual != expected:
            failures.append({'package': package, 'expected': expected, 'actual': actual})
    manifest = read(HERE / 'REVIEW_MANIFEST.json')
    preserved = []
    for item in manifest['preserved_inputs']:
        actual = sha(Path(item['path']))
        preserved.append({'path': item['path'], 'expected': item['sha256'], 'actual': actual, 'unchanged': actual == item['sha256']})
    before = PROJECT / 'Staging/ModularConstruction_2026-10-05/Bindings/Before'
    maps = []
    for area in ('GazaRimal', 'GazaShujaiya'):
        name = 'L_' + area + '_BankIntegration.umap'
        p = PROJECT / 'Content/Project/Areas' / area / 'BankIntegration_v015' / name
        old = before / name
        maps.append({'path': str(p), 'sha256': sha(p), 'backup_sha256': sha(old), 'matches_backup': sha(p) == sha(old)})
    value = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'saved_part_receipts': len(part_receipts), 'unique_pinned_packages': len(pins),
             'pin_conflicts': conflicts, 'hash_mismatches': failures,
             'preserved_inputs': preserved, 'maps': maps,
             'native_editor_called': False, 'native_dirty_inventory_available': False,
             'fresh_process_reopen_performed': False}
    (HERE / 'SAVED_STATE_VERIFICATION.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    assert len(part_receipts) == 603 and not conflicts and not failures
    assert all(p['unchanged'] for p in preserved)
    print(json.dumps({'saved_parts': len(part_receipts), 'unique_packages': len(pins),
                      'hash_mismatches': len(failures), 'maps_match_backups': all(x['matches_backup'] for x in maps)}))

if __name__ == '__main__':
    main()
