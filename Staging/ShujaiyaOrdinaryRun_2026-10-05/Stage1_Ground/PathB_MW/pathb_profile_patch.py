"""Path B profile edit for GazaShujaiya (manager runs it; offline, no unreal import).

Changes exactly two leaves of Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/AREA_PROFILE.json:
  landscape_material        -> /Game/Project/Areas/GazaShujaiya/BankIntegration_v015/Materials/MI_GeoCityGround_MW.MI_GeoCityGround_MW
  landscape_grass.enabled   -> false
and, only with --external-block (needed only if the OPTIONAL hardening patch is applied), adds one key:
  external_landscape_material = {decision, parent_chain, static_switches_false}
Every other byte is preserved: the file is re-serialised with the measured format (json indent=2, CRLF,
trailing CRLF, ensure_ascii) and the script refuses if the unmodified input does not round-trip byte-exactly.

Usage (from the project root or anywhere):
  python pathb_profile_patch.py                       # dry run: prints before/after sha256 + leaf diff, writes nothing
  python pathb_profile_patch.py --apply               # backup -> atomic replace -> record
  python pathb_profile_patch.py --apply --external-block [--parent desert|master]
  python pathb_profile_patch.py --rollback <backup.json> --expect-current <sha256>
  python pathb_profile_patch.py --rollback-map <backup.umap> --expect-current-map <sha256>
--apply/--rollback/--rollback-map refuse unless the last EDITOR_OWNER.txt line is OWNER=NONE and no UnrealEditor.exe runs.
Writes only: PathB_MW/Before/AREA_PROFILE_<sha8>_<utc>.json and a byte copy of the saved Shujaiya map
PathB_MW/Before/L_GazaShujaiya_BankIntegration_<sha8>_<utc>.umap (both exclusive; the map copy is the
rollback point), the profile itself (atomic), PathB_MW/PROFILE_PATCH_RECORD_<utc>.json (exclusive).
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
EXPECTED_BEFORE = '1328d5bbdf0005bbb5b4b7ede85269c0d203beca361e193e0c9fd0edb0478b39'   # ratified B2
MAP_FILE = ROOT / 'Content/Project/Areas/GazaShujaiya/BankIntegration_v015/L_GazaShujaiya_BankIntegration.umap'
EXPECTED_MAP = '4efebdfb0bf6c36b699a577b33faa64d28afbec0488115e6596883af518940d0'        # ratified B2
LEDGER = ROOT / 'Staging/ModelBank/GazaShujaiyaIntegration_2026-10-02/LAST_SUCCESSFUL_WORKFLOW_STATE.json'
AREA_ROOT = '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015'
OLD_MATERIAL = AREA_ROOT + '/Materials/MI_GeoCityGround.MI_GeoCityGround'
NEW_MATERIAL = AREA_ROOT + '/Materials/MI_GeoCityGround_MW.MI_GeoCityGround_MW'
DESERT = '/Game/MWLandscapeAutoMaterial/Materials/Landscape/MTL_MWAM_Landscape_DesertExample.MTL_MWAM_Landscape_DesertExample'
MASTER = '/Game/MWLandscapeAutoMaterial/Materials/MASTER/MTL_MWAM_AutoMaterial_MASTER.MTL_MWAM_AutoMaterial_MASTER'
PROCEDURALS = ['MW_[x]_UseRockProcedurals', 'MW_[x]_UseStonesProcedurals', 'MW_[x]_UseGrassProcedurals',
               'MW_[x]_UseDirtProcedurals', 'MW_[x]_UseSnowProcedurals']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def serialise(obj):
    # MEASURED 2026-10-06: both Gaza profiles round-trip byte-exactly with this format.
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


def editor_free():
    last = [x for x in LEASE.read_text(encoding='utf-8-sig').splitlines() if x.strip()][-1]
    fields = dict(re.findall(r'(?:^|\s)([A-Za-z_]+)=([^\s]+)', last))   # geocity_editor_action.lease_fields
    if fields.get('OWNER') != 'NONE':
        raise SystemExit('Refused: last EDITOR_OWNER.txt line is not OWNER=NONE: ' + last)
    listing = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq UnrealEditor.exe', '/FO', 'CSV', '/NH'],
                             capture_output=True, text=True, timeout=30)
    if 'UnrealEditor.exe' in listing.stdout:
        raise SystemExit('Refused: an UnrealEditor.exe process is running; profile edits happen with the editor closed.')
    return last


def build(profile, external_block, parent):
    new = json.loads(json.dumps(profile))
    if new.get('landscape_material') != OLD_MATERIAL:
        raise SystemExit('Refused: landscape_material is not the retained Natural child: ' + str(new.get('landscape_material')))
    if new.get('landscape_grass', {}).get('enabled') is not True:
        raise SystemExit('Refused: landscape_grass.enabled is not true in the baseline profile.')
    if new.get('root') != AREA_ROOT or 'external_landscape_material' in new:
        raise SystemExit('Refused: unexpected profile root or an existing external_landscape_material block.')
    new['landscape_material'] = NEW_MATERIAL
    new['landscape_grass']['enabled'] = False
    if external_block:
        new['external_landscape_material'] = {
            'decision': ('Aviv 2026-10-06 Path B: MW auto-landscape material is the GazaShujaiya ground; no grass; '
                         'the material does not consume the Houdini RoadBed/BuildingPad paint (accepted for now). '
                         'Previous Natural/Grass configuration kept in landscape_grass for rollback.'),
            'parent_chain': [DESERT, MASTER] if parent == 'desert' else [MASTER],
            'static_switches_false': PROCEDURALS}
    return new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--external-block', action='store_true')
    ap.add_argument('--parent', choices=('desert', 'master'), default='desert')
    ap.add_argument('--expected-before', default=EXPECTED_BEFORE)
    ap.add_argument('--expected-map', default=EXPECTED_MAP)
    ap.add_argument('--rollback', help='PathB_MW/Before/AREA_PROFILE_*.json to restore')
    ap.add_argument('--expect-current', help='current profile sha256 (rollback)')
    ap.add_argument('--rollback-map', help='PathB_MW/Before/L_GazaShujaiya_BankIntegration_*.umap to restore')
    ap.add_argument('--expect-current-map', help='current map sha256 (rollback-map)')
    a = ap.parse_args()
    raw = PROFILE.read_bytes()
    current = sha(raw)
    if a.rollback or a.rollback_map:
        target, source, expect = ((PROFILE, a.rollback, a.expect_current) if a.rollback
                                  else (MAP_FILE, a.rollback_map, a.expect_current_map))
        backup = Path(source).resolve()
        now = sha(target.read_bytes())
        if backup.parent != (HERE / 'Before') or expect != now:
            raise SystemExit('Refused: rollback needs a PathB_MW/Before backup and the current sha256 ' + now)
        if a.rollback_map and LEDGER.is_file() and LEDGER.stat().st_mtime_ns > backup.stat().st_mtime_ns:
            # A later ordinary regeneration replaced the baked actors/packages the old .umap references.
            raise SystemExit('Refused: an ordinary regeneration ran after this map backup; roll back by restoring the '
                             'profile and running an ordinary regeneration instead.')
        editor_free()
        data = backup.read_bytes()
        pending = target.with_name(target.name + '.pathb_rollback.pending')
        pending.write_bytes(data)
        os.replace(pending, target)
        record = {'utc': utc(), 'action': 'rollback', 'file': str(target), 'before_sha256': now,
                  'after_sha256': sha(target.read_bytes()), 'restored_from': str(backup), 'restored_sha256': sha(data)}
        with open(HERE / ('PROFILE_PATCH_RECORD_%s_rollback_%s.json' % (record['utc'], target.suffix[1:])), 'x', encoding='utf-8') as f:
            json.dump(record, f, indent=2)
        print(json.dumps(record, indent=2))
        return
    if current != a.expected_before:
        raise SystemExit('Refused: profile sha256 %s differs from expected %s' % (current, a.expected_before))
    profile = json.loads(raw.decode('utf-8'))
    if serialise(profile) != raw:
        raise SystemExit('Refused: profile does not round-trip byte-exactly; a format-preserving edit is not proven.')
    new = build(profile, a.external_block, a.parent)
    data = serialise(new)
    changes = diff(profile, new)
    required = {'/landscape_material', '/landscape_grass/enabled'}
    paths = {c['path'] for c in changes}
    extra = {p for p in paths - required
             if not (a.external_block and p.startswith('/external_landscape_material/'))}
    if extra or not required <= paths:
        raise SystemExit('Refused: unexpected leaf changes ' + json.dumps(changes))
    summary = {'profile': str(PROFILE), 'before_sha256': current, 'after_sha256': sha(data),
               'external_block': a.external_block, 'parent': a.parent, 'changes': changes, 'applied': False}
    if not a.apply:
        print(json.dumps(summary, indent=2))
        return
    lease = editor_free()
    stamp = utc()
    backup_dir = HERE / 'Before'
    backup_dir.mkdir(exist_ok=True)
    map_raw = MAP_FILE.read_bytes()
    if sha(map_raw) != a.expected_map:
        raise SystemExit('Refused: saved map sha256 %s differs from expected %s' % (sha(map_raw), a.expected_map))
    map_backup = backup_dir / ('L_GazaShujaiya_BankIntegration_%s_%s.umap' % (a.expected_map[:8], stamp))
    with open(map_backup, 'xb') as f:          # byte rollback point for the map (editor closed)
        f.write(map_raw)
    backup = backup_dir / ('AREA_PROFILE_%s_%s.json' % (current[:8], stamp))
    with open(backup, 'xb') as f:
        f.write(raw)
    if sha(PROFILE.read_bytes()) != current:
        raise SystemExit('Refused: profile changed while preparing the edit.')
    pending = PROFILE.with_name(PROFILE.name + '.pathb.pending')
    pending.write_bytes(data)
    os.replace(pending, PROFILE)
    after = PROFILE.read_bytes()
    if after != data or diff(profile, json.loads(after.decode('utf-8'))) != changes:
        raise SystemExit('Profile readback differs after replace; restore from ' + str(backup))
    summary.update(applied=True, utc=stamp, backup=str(backup), backup_sha256=sha(raw), lease_at_edit=lease,
                   map_backup=str(map_backup), map_backup_sha256=sha(map_raw),
                   authority='Aviv decision Path B (2026-10-06); manager-run; record required by RATIFICATION_B2 rule_from_now')
    with open(HERE / ('PROFILE_PATCH_RECORD_' + stamp + '.json'), 'x', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    sys.exit(main())
