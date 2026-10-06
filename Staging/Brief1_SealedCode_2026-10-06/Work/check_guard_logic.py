"""Static verification of the parallel-editor logic with synthetic inputs.

No editor, no map, no writes; reads the three real AREA_PROFILE.json files only.
Usage: python -I -B check_guard_logic.py <project root> <guard file>
"""
import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
guard_path = Path(sys.argv[2]).resolve()
g = {'__name__': 'geocity_runtime_guard', '__file__': str(guard_path)}
exec(compile(guard_path.read_bytes(), str(guard_path), 'exec', dont_inherit=True), g)

# 1. timestamps
for s, ok in (('2026-10-06T16:20:47.3731360Z', True), ('2026-10-06T14:48:43.106695+00:00', True),
              ('2026-10-06T16:20:47+00:00', True), ('garbage', False), ('`n2026-10-06T16:20:47.3731360Z', False)):
    assert (g['parse_utc'](s) is not None) == ok, s

# 2. lease line selection
text = '\n'.join([
    '2026-10-06T10:00:00+00:00 OWNER=GEOCITY_MENU assigned_editor_PID=500 scope=x',
    '2026-10-06T12:00:00+00:00 OWNER=CODEX_MANAGED_SYSTEMS_STARTUP assigned_editor_PID=500',
    '2026-10-06T12:01:00+00:00 OWNER=OTHER assigned_editor_PID=777',
    '2026-10-06T12:02:00+00:00 OWNER=NONE released_by=X editor_PID=500_still_running',
    '2026-10-06T12:03:00+00:00 OWNER=NONE editor_PID=777'])
assert g['editor_lease_line'](text, 500, '2026-10-06T11:59:59Z').endswith('assigned_editor_PID=500'), 'per-PID last line'
assert g['editor_lease_line'](text, 500, '2026-10-06T12:30:00Z') is None, 'line before process start is ignored'
assert g['editor_lease_line'](text, 500, None).endswith('assigned_editor_PID=500'), 'no start = no floor'
assert g['editor_lease_line'](text, 1, None) is None
assert g['lease_fields']('a OWNER=NONE b=c')['OWNER'] == 'NONE' and g['lease_fields'](None) == {}

# 3. scopes of the three real profiles
profiles = {p.parent.name: p for p in (root / 'Staging/ModelBank').glob('*/AREA_PROFILE.json')}
scopes = {name: g['generation_scope'](path, root) for name, path in profiles.items()}
for name, s in scopes.items():
    print(name, '| area', s['area_id'], '| roads', s['roads_enabled'], '| grass', s['grass_enabled'])
    print('   write', s['write'])
    print('   read#', len(s['read']), '| file_write', s['file_write'], '| file_read#', len(s['file_read']))
rimal = scopes['PermanentIntegration_2026-10-02']
iran = scopes['Iran_38196167_46086167_4km']
shuj = scopes['GazaShujaiyaIntegration_2026-10-02']
SURF = '/Game/Project/Shared/SurfacePainting/Appearance_20261003/'
assert rimal['write'] == ['/Game/Project/Areas/GazaRimal/', SURF + 'LG_GeoCity_PermittedGroundGrass', SURF + 'M_SurfaceBank_Natural']
assert iran['write'] == ['/Game/Project/Areas/Iran_38196167_46086167_4km/']
assert shuj['write'] == ['/Game/Project/Areas/GazaShujaiya/']
assert '/Game/Project/Shared/RoadBLD/' in rimal['read'] and '/Game/Project/Shared/RoadBLD/' not in iran['read']
assert SURF + 'M_SurfaceBank_Natural' in iran['read']
assert 'staging/modelbank/editor_owner.txt' in [x.lower() for x in rimal['file_write']]

# 4. pairing table with synthetic records (synthetic live list; Staging/ParallelEditors is not read)
def rec(pid, start, write, original_map=None, files=(), released=None):
    r = {'schema': g['PARALLEL_EDITOR_SCHEMA'], 'pid': pid, 'process_start_utc': start, 'task': 'synthetic',
         'write_scope': list(write), 'file_write_scope': list(files), 'original_map': original_map, 'released_utc': released}
    return {'path': 'Staging/ParallelEditors/EDITOR_%d.json' % pid,
            'sha256': hashlib.sha256(json.dumps(r).encode()).hexdigest(), 'record': r, 'error': None}

RIMAL_MAP = '/Game/Project/Areas/GazaRimal/BankIntegration_v015/L_GazaRimal_BankIntegration'
T0, T1 = '2026-10-06T16:00:00.0000000Z', '2026-10-06T16:05:00.0000000Z'
sky = rec(5200, T0, ['/Game/Project/Shared/Atmosphere/ReusableSky/', RIMAL_MAP], RIMAL_MAP)
bank = rec(5200, T0, ['/Game/Project/Shared/ModelBank/DT_EnvironmentBank_v4', '/Game/Project/Shared/ModelBank/Prepared',
                      '/Game/Project/Shared/ModelBank/Materials/BankIntegration_20261004'])


def own(scope_write):
    return rec(9000, T1, scope_write)


def verdict(profile_name, other, own_rec, live=((5200, T0), (9000, T1))):
    r = g['parallel_editor_report'](root, profiles[profile_name], 9000, live=list(live), records=[x for x in (other, own_rec) if x])
    return r['verdict'], r['reasons']


rows = []
for label, prof in (('Iran', 'Iran_38196167_46086167_4km'), ('Shujaiya', 'GazaShujaiyaIntegration_2026-10-02'),
                    ('Rimal', 'PermanentIntegration_2026-10-02')):
    v, why = verdict(prof, sky, own(scopes[prof]['write']))
    rows.append(('sky+' + label, v, why[:1]))
    v, why = verdict(prof, bank, own(scopes[prof]['write']))
    rows.append(('bank+' + label, v, why[:1]))
for r in rows:
    print(r)
assert dict((a, b) for a, b, _ in rows) == {'sky+Iran': 'PASS', 'bank+Iran': 'REFUSE', 'sky+Shujaiya': 'PASS',
                                            'bank+Shujaiya': 'REFUSE', 'sky+Rimal': 'REFUSE', 'bank+Rimal': 'REFUSE'}
iran_gen = rec(5200, T0, iran['write'], iran['map'])
v, why = verdict('PermanentIntegration_2026-10-02', iran_gen, own(rimal['write']))
print('rimal+iran_generation (record without read_scope)', v, why[:1])
assert v == 'PASS', 'a record without read_scope cannot be matched against our writes (documented limitation)'
iran_gen['record']['read_scope'] = iran['read']
v, why = verdict('PermanentIntegration_2026-10-02', iran_gen, own(rimal['write']))
print('rimal+iran_generation (record with read_scope)', v, why[:1])
assert v == 'REFUSE' and any('M_SurfaceBank_Natural' in r for r in why)
v, why = verdict('Iran_38196167_46086167_4km', rec(5200, T0, rimal['write'], rimal['map']), own(iran['write']))
print('iran+rimal_generation', v, why[:1])
assert v == 'REFUSE' and any('M_SurfaceBank_Natural' in r for r in why)
assert all(f == f.rstrip('/') or f.endswith('/') for f in rimal['file_write']) and 'Staging/ModelBank/EDITOR_OWNER.txt' in rimal['file_write']
IRAN = profiles['Iran_38196167_46086167_4km']
r = g['parallel_editor_report'](root, IRAN, 9000, live=[(9000, T1)], records=[])
assert r['verdict'] == 'PASS', r
r = g['parallel_editor_report'](root, IRAN, 9000, live=[(5200, T0), (9000, T1)], records=[own(iran['write'])])
assert r['verdict'] == 'REFUSE' and 'PID 5200' in r['reasons'][0] and 'EDITOR_5200.json' in r['reasons'][0], r['reasons']
print('unrecorded:', r['reasons'][0])
r = g['parallel_editor_report'](root, IRAN, 9000, live=[(5200, T0), (9000, T1)], records=[sky])
assert r['verdict'] == 'REFUSE' and 'PID 9000' in r['reasons'][0]
print('own missing:', r['reasons'][0])
r = g['parallel_editor_report'](root, IRAN, 9000, live=[(5200, '2026-10-06T17:00:00Z'), (9000, T1)], records=[sky, own(iran['write'])])
assert r['verdict'] == 'REFUSE' and 'PID reuse' in r['reasons'][0]
print('pid reuse:', r['reasons'][0])
r = g['parallel_editor_report'](root, IRAN, 9000, live=[(5200, T0), (9000, T1)],
                                records=[rec(5200, T0, ['/Game/X/'], released='2026-10-06T16:30:00Z'), own(iran['write'])])
assert r['verdict'] == 'REFUSE' and 'released' in r['reasons'][0]
r = g['parallel_editor_report'](root, IRAN, 9000, live=[(9000, T1)], records=[sky])
assert r['verdict'] == 'PASS' and r['stale_records'][0]['pid'] == 5200
r = g['parallel_editor_report'](root, IRAN, 9000, live=[(5200, T0), (9000, T1)],
                                records=[rec(5200, T0, ['/Game/X/'], files=['Content/Python/']), own(iran['write'])])
assert r['verdict'] == 'REFUSE' and 'protected' in r['reasons'][0]
r = g['parallel_editor_report'](root, IRAN, None, live=[(5200, T0)], records=[sky])
assert r['verdict'] == 'PASS', r['reasons']
r = g['parallel_editor_report'](root, profiles['PermanentIntegration_2026-10-02'], 9000, live=[(5200, T0), (9000, T1)],
                                records=[rec(5200, T0, ['/Game/Other/']), own(['/Game/Project/Areas/GazaRimal/'])])
assert r['verdict'] == 'REFUSE' and 'does not cover' in r['reasons'][0]
print('coverage:', r['reasons'][0])
assert not g['_overlaps']('/Game/Project/Areas/GazaRimalX/', '/Game/Project/Areas/GazaRimal/')
assert g['_overlaps']('/Game/Project/Areas/GazaRimal/Bake/Foo.Foo', '/Game/Project/Areas/GazaRimal/')
live = g['live_editors']()
print('live now:', live)
print('ALL CHECKS PASSED')
