"""Hybrid ground profile edit for GazaShujaiya (manager runs it; OFFLINE, never imports unreal).

Base: the Path B profile (measured 2026-10-06 07:40Z: 1bd89e5b..., Path B leaves + the bank chat's accepted
building_assembly_contract.source_family_registry_ref leaf). Changes exactly these leaves of
Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json:
  /landscape_material                        MI_GeoCityGround_MW -> MI_GeoCityGround_Auto
  /external_landscape_material/parent_chain  [DesertExample, MW master] -> [M_GeoCityAuto]
                                             (leaf diff: parent_chain[0] changed, parent_chain[1] absent)
  /external_landscape_material/decision      Path B text -> Hybrid text
landscape_grass.enabled stays false; external_landscape_material.static_switches_false stays unchanged.
Every other byte is preserved: re-serialised with the measured format (json indent=2, CRLF, trailing CRLF,
ensure_ascii; M: 1bd89e5b round-trips byte-exactly) and refused if the input does not round-trip.

Usage (any cwd):
  python -B hybrid_profile_patch.py --expected-before <sha256> [--dry-run]   # default: dry run, writes NOTHING
  python -B hybrid_profile_patch.py --expected-before <sha256> --apply [--expected-map <sha256>]
  python -B hybrid_profile_patch.py --rollback <Before/AREA_PROFILE_*.json> --expect-current <sha256>
  python -B hybrid_profile_patch.py --rollback-map <Before/L_GazaShujaiya_*.umap> --expect-current-map <sha256>
--apply/--rollback/--rollback-map refuse unless the last EDITOR_OWNER.txt line is OWNER=NONE and no UnrealEditor.exe
runs. Writes only: Hybrid_Auto/Before/AREA_PROFILE_<sha8>_<utc>.json and Hybrid_Auto/Before/
L_GazaShujaiya_BankIntegration_<sha8>_<utc>.umap (both exclusive; the map copy is the rollback point, valid until
the next ordinary regeneration), the profile itself (atomic replace), Hybrid_Auto/PROFILE_PATCH_RECORD_<utc>.json
(exclusive).
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PROFILE = ROOT / 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json'
LEASE = ROOT / 'Staging/ModelBank/EDITOR_OWNER.txt'
MAP_FILE = ROOT / 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration.umap'
EXPECTED_MAP = '4efebdfb0bf6c36b699a577b33faa64d28afbec0488115e6596883af518940d0'        # ratified B2, M 2026-10-06
LEDGER = ROOT / 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/LAST_SUCCESSFUL_WORKFLOW_STATE.json'
AREA_ROOT = '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015'
PATHB_MATERIAL = AREA_ROOT + '/Materials/MI_GeoCityGround_MW.MI_GeoCityGround_MW'
NEW_MATERIAL = AREA_ROOT + '/Materials/MI_GeoCityGround_Auto.MI_GeoCityGround_Auto'
DESERT = '/Game/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_DesertExample.MTL_MWAM_Landscape_DesertExample'
MW_MASTER = '/Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.MTL_MWAM_AutoMaterial_MASTER'
HYBRID_MASTER = '/Game/Project/Shared/SurfacePainting/Auto_20261006/M_GeoCityAuto.M_GeoCityAuto'
PROCEDURALS = ['MW_[x]_UseRockProcedurals', 'MW_[x]_UseStonesProcedurals', 'MW_[x]_UseGrassProcedurals',
               'MW_[x]_UseDirtProcedurals', 'MW_[x]_UseSnowProcedurals']
DECISION = ('Aviv 2026-10-06 Hybrid: M_GeoCityAuto (project copy of the MW auto-landscape master, vendor untouched) '
            'plus an Urban layer driven by the Houdini Sand_Path (BuildingPad) and Dirt_Path (RoadBed) paint weights is '
            'the GazaShujaiya ground; the material names all four painted layers (Sand_01, Sand_02, Dirt_Path, '
            'Sand_Path) so regeneration keeps them; no grass. Path B MI_GeoCityGround_MW was never saved and is '
            'superseded. Previous Natural/Grass configuration kept in landscape_grass for rollback.')
ALLOWED_CHANGES = {'/landscape_material', '/external_landscape_material/decision',
                   '/external_landscape_material/parent_chain[0]', '/external_landscape_material/parent_chain[1]'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def serialise(obj):
    # MEASURED 2026-10-06: both Gaza profiles (incl. 1bd89e5b) round-trip byte-exactly with this format.
    return (json.dumps(obj, indent=2, ensure_ascii=True).replace('\n', '\r\n') + '\r\n').encode('utf-8')


def leaves(obj, prefix=''):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            out.update(leaves(v, prefix + '/' + k))
        return out if obj else {prefix: {}}
    if isinstance(obj, list):
        out = {}
        for i, v in enumerate(obj):
            out.update(leaves(v, prefix + '[' + str(i) + ']'))
        return out if obj else {prefix: []}
    return {prefix: obj}


def diff(before, after):
    a, b = leaves(before), leaves(after)
    return [{'path': k, 'before': a.get(k, '<absent>'), 'after': b.get(k, '<absent>')}
            for k in sorted(set(a) | set(b)) if a.get(k, '<absent>') != b.get(k, '<absent>')]


def editor_state():
    last = [x for x in LEASE.read_text(encoding='utf-8-sig').splitlines() if x.strip()][-1]
    fields = dict(re.findall(r'(?:^|\s)([A-Za-z_]+)=([^\s]+)', last))   # geocity_editor_action.lease_fields
    listing = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq UnrealEditor.exe', '/FO', 'CSV', '/NH'],
                             capture_output=True, text=True, timeout=30)
    return last, fields.get('OWNER'), 'UnrealEditor.exe' in listing.stdout


def editor_free():
    last, owner, running = editor_state()
    if owner != 'NONE':
        raise SystemExit('Refused: last EDITOR_OWNER.txt line is not OWNER=NONE: ' + last)
    if running:
        raise SystemExit('Refused: an UnrealEditor.exe process is running; profile edits happen with the editor closed.')
    return last


def build(profile):
    new = json.loads(json.dumps(profile))
    ext = new.get('external_landscape_material')
    if new.get('landscape_material') != PATHB_MATERIAL:
        raise SystemExit('Refused: landscape_material is not the Path B MI: ' + str(new.get('landscape_material')))
    if new.get('landscape_grass', {}).get('enabled') is not False:
        raise SystemExit('Refused: landscape_grass.enabled is not false in the Path B profile.')
    if new.get('root') != AREA_ROOT or not isinstance(ext, dict):
        raise SystemExit('Refused: unexpected profile root or no external_landscape_material block.')
    if ext.get('parent_chain') != [DESERT, MW_MASTER] or ext.get('static_switches_false') != PROCEDURALS \
            or set(ext) != {'decision', 'parent_chain', 'static_switches_false'}:
        raise SystemExit('Refused: external_landscape_material is not the measured Path B block: ' + json.dumps(ext))
    new['landscape_material'] = NEW_MATERIAL
    new['external_landscape_material']['parent_chain'] = [HYBRID_MASTER]
    new['external_landscape_material']['decision'] = DECISION
    return new


def rollback(a):
    target, source, expect = ((PROFILE, a.rollback, a.expect_current) if a.rollback
                              else (MAP_FILE, a.rollback_map, a.expect_current_map))
    backup = Path(source).resolve()
    now = sha(target.read_bytes())
    if backup.parent != (HERE / 'Before') or not backup.is_file() or expect != now:
        raise SystemExit('Refused: rollback needs a Hybrid_Auto/Before backup and the current sha256 ' + now)
    if a.rollback_map and LEDGER.is_file() and LEDGER.stat().st_mtime_ns > backup.stat().st_mtime_ns:
        # A later ordinary regeneration replaced the baked actors/packages the old .umap references.
        raise SystemExit('Refused: an ordinary regeneration ran after this map backup; roll back by restoring the '
                         'profile and running an ordinary regeneration instead.')
    editor_free()
    data = backup.read_bytes()
    pending = target.with_name(target.name + '.hybrid_rollback.pending')
    pending.write_bytes(data)
    os.replace(pending, target)
    record = {'utc': utc(), 'action': 'rollback', 'file': str(target), 'before_sha256': now,
              'after_sha256': sha(target.read_bytes()), 'restored_from': str(backup), 'restored_sha256': sha(data)}
    with open(HERE / ('PROFILE_PATCH_RECORD_%s_rollback_%s.json' % (record['utc'], target.suffix[1:])), 'x',
              encoding='utf-8') as f:
        json.dump(record, f, indent=2)
    print(json.dumps(record, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='default; prints the plan, writes nothing')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--expected-before', help='current profile sha256 (re-measured by the manager); required')
    ap.add_argument('--expected-map', default=EXPECTED_MAP)
    ap.add_argument('--rollback', help='Hybrid_Auto/Before/AREA_PROFILE_*.json to restore')
    ap.add_argument('--expect-current', help='current profile sha256 (rollback)')
    ap.add_argument('--rollback-map', help='Hybrid_Auto/Before/L_GazaShujaiya_BankIntegration_*.umap to restore')
    ap.add_argument('--expect-current-map', help='current map sha256 (rollback-map)')
    a = ap.parse_args()
    if a.rollback or a.rollback_map:
        if a.apply or (a.rollback and a.rollback_map):
            raise SystemExit('Refused: one action per call.')
        return rollback(a)
    if a.apply and a.dry_run:
        raise SystemExit('Refused: --apply and --dry-run are exclusive.')
    if not (isinstance(a.expected_before, str) and re.fullmatch(r'[0-9a-f]{64}', a.expected_before)):
        raise SystemExit('Refused: --expected-before <64-hex sha256 of the current profile> is required.')
    raw = PROFILE.read_bytes()
    current = sha(raw)
    if current != a.expected_before:
        raise SystemExit('Refused: profile sha256 %s differs from expected %s' % (current, a.expected_before))
    profile = json.loads(raw.decode('utf-8'))
    if serialise(profile) != raw:
        raise SystemExit('Refused: profile does not round-trip byte-exactly; a format-preserving edit is not proven.')
    new = build(profile)
    data = serialise(new)
    changes = diff(profile, new)
    paths = {c['path'] for c in changes}
    if paths != ALLOWED_CHANGES:
        raise SystemExit('Refused: leaf changes differ from the reviewed set ' + json.dumps(changes))
    if new['landscape_grass'] != profile['landscape_grass'] or \
            new['external_landscape_material']['static_switches_false'] != PROCEDURALS:
        raise SystemExit('Refused: grass block or static_switches_false would change.')
    last, owner, running = editor_state()
    summary = {'profile': str(PROFILE), 'before_sha256': current, 'after_sha256': sha(data), 'changes': changes,
               'grass_enabled_after': new['landscape_grass']['enabled'], 'applied': False,
               'editor_state_now': {'last_lease_line': last, 'owner': owner, 'unreal_editor_running': running}}
    if not a.apply:
        print(json.dumps(summary, indent=2))
        return
    lease = editor_free()
    map_raw = MAP_FILE.read_bytes()
    if sha(map_raw) != a.expected_map:
        raise SystemExit('Refused: saved map sha256 %s differs from expected %s' % (sha(map_raw), a.expected_map))
    stamp = utc()
    backup_dir = HERE / 'Before'
    backup_dir.mkdir(exist_ok=True)
    map_backup = backup_dir / ('L_GazaShujaiya_BankIntegration_%s_%s.umap' % (a.expected_map[:8], stamp))
    with open(map_backup, 'xb') as f:          # byte rollback point for the map (editor closed)
        f.write(map_raw)
    backup = backup_dir / ('AREA_PROFILE_%s_%s.json' % (current[:8], stamp))
    with open(backup, 'xb') as f:
        f.write(raw)
    if sha(PROFILE.read_bytes()) != current or sha(map_backup.read_bytes()) != a.expected_map:
        raise SystemExit('Refused: profile changed while preparing the edit, or the map copy differs.')
    pending = PROFILE.with_name(PROFILE.name + '.hybrid.pending')
    pending.write_bytes(data)
    os.replace(pending, PROFILE)
    after = PROFILE.read_bytes()
    if after != data or diff(profile, json.loads(after.decode('utf-8'))) != changes:
        raise SystemExit('Profile readback differs after replace; restore from ' + str(backup))
    summary.update(applied=True, utc=stamp, backup=str(backup), backup_sha256=sha(raw), lease_at_edit=lease,
                   map_backup=str(map_backup), map_backup_sha256=sha(map_raw),
                   authority='Aviv decision Hybrid ground (2026-10-06, Incident_01a10c77_2026-10-05/'
                             'DECISION_HYBRID_20261006.json); manager-run; record required by RATIFICATION_B2 rule_from_now')
    summary.pop('editor_state_now')
    with open(HERE / ('PROFILE_PATCH_RECORD_' + stamp + '.json'), 'x', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    sys.exit(main())
