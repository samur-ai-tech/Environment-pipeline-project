r"""Stage 1 ground (S1) OFFLINE backup of the retained surface-material contract.

OFFLINE ONLY: never imports unreal, never calls MCP / Houdini / editor tools, never starts
or stops an editor. Sources are opened 'rb' only. Writes only under S1_Prep/Before/<set>/
(and, for --selftest only, a self-deleting temp folder under S1_Prep).

Modes
  (default)      Back up the S1 copy set into S1_Prep/Before/S1B_<UTC>/Content/... + BACKUP_MANIFEST.json.
                 REFUSES if any UnrealEditor* process exists (tasklist), before and after copying, and on ANY
                 integrity blocker found by collect_state():
                   - runtime seal manifest sha256 != pinned 3cd33b15 (STAGE1_GROUND_PLAN.md:158) unless root's
                     ratification is passed (--ratified-seal + --ratification-record);
                   - any of the 17 sealed files != its pin in that manifest (modules + startup + support_files);
                   - any sealed file != REV BACKUP_MANIFEST sealed_files (unless under a ratified seal);
                   - any MWLandscapeAutoMaterial / HighPoly_Tree_Model file differing from, or missing in,
                     its Epic VaultCache original (SHA-1 + size), or a vault file missing in the project;
                   - a missing copy-set / hash-only / sealed file, an unparsable import table or an
                     unresolved /Game import of master, base MI or children;
                   - the REV BACKUP_MANIFEST sha256 != its pin, spec new_function_packages != NEW_ASSET_PATHS,
                     a planned new MF_GeoCity_* package already on disk.
                 Idempotent: if the newest complete set already holds exactly the current hashes it prints
                 UP_TO_DATE and writes nothing. Otherwise it builds a NEW timestamped set in S1B_<UTC>.partial
                 and renames it only after every check passed. Existing sets are never modified.
  --plan         Read-only dry run (resolve, hash, vault/seal/baseline checks, blockers). Writes nothing; exit 1 if would_refuse.
  --verify SET   Read-only: re-hash SET's backup copies, the project files of its files[], every preserved_files
                 pin (this includes every vendor-pack file, so a vendor change shows here; the vault SHA-1
                 itself is checked at backup time), every sealed_files pin and the runtime manifest sha.
                 Status INTACT | EDIT_TARGETS_CHANGED (only master/children differ, expected after an S1 save)
                 | PRESERVED_DRIFT | BACKUP_DAMAGED; exit 1 for the last two. A pre-edit caller (the S1 editor
                 step, inside its session, immediately before its first change) must require INTACT.
  --selftest     Exercise copy / idempotency / no-overwrite / refusals on synthetic files in a temp folder
                 under S1_Prep (deleted afterwards). Touches no real asset.
  --ratified-seal SHA256 --ratification-record FILE
                 Accept a runtime manifest other than the pinned one ONLY with a root ratification record
                 (a file under <project>/Staging that names the exact 64-hex sha). Both are recorded.
Exit: 0 ok or up-to-date, 1 refused / failed / integrity error / drift / --plan would_refuse, 2 usage.
Note: --plan/--verify only read files; run them with the editor closed if possible. CPython open('rb')
does not grant FILE_SHARE_DELETE (INFERRED), so an editor save replacing a package while it is being
hashed can see a transient sharing violation. Default mode refuses while an editor runs.

Precedents reused (cite):
  Staging/ShujaiyaOrdinaryRun_2026-10-05/RunExisting_20261005/prepare_run.py:9-10  editor-process refusal
      (Get-Process UnrealEditor,UnrealEditor-Cmd; the S1 spec requires tasklist instead)
  prepare_run.py:21     '\\?\' extended-length path prefix for the Before/ mirror
  prepare_run.py:27-32  Content-relative mirror, shutil.copy2, never overwrite a differing copy
  STAGE1_GROUND_PLAN.md:181-184  REV BACKUP_MANIFEST schema: ready, created_utc,
      files[{file,sha256,backup}], preserved_files, sealed_files, new_asset_paths, pid, world,
      execution_thread_id, file_bindings  (GroundPainting_2026-10-04/Revision_2026-10-05/BACKUP_MANIFEST.json)
  GroundPainting_2026-10-04/native_revision_verify.py:48  consumer loop over preserved_files+sealed_files
  S1_Prep/s1_material_edit.py:571-588  check_backup: file_bindings must cover master, base MI, Grass type,
      both children, both maps; sha(source) == sha(backup) == row sha256; backup under Stage1_Ground
  S1_Prep/MW_HP_PackInventory/compare_vault.py:6-9,12-17,28-41  VaultCache pairs + SHA1 (reimplemented:
      that file runs at import)
  S1_Prep/MW_HP_PackInventory/uasset_offline.py:43-73  package summary / name map / import map layout
      (extended here for LegacyFileVersion -9 and FileVersionUE5 >= 1016 SavedHash; MEASURED 2026-10-05)
  Content/Python/geocity_runtime_guard.py:50-57  seal = module sha256 vs geocity_runtime_manifest.json

Copy set: REV files[] minus the 4 MOUT masks (master, base MI, both children, both maps, Grass type,
T_Sand_01/02_Normal_GeoCity) + the 11 D2 MW textures (S1_MINIMAL_SAFE_SPEC.json / S1_MAXREUSE_EDIT_SPEC.json;
the 'correction 5' wording is not in any file under Staging/ShujaiyaOrdinaryRun_2026-10-05).
"""
import argparse
import csv
import hashlib
import io
import json
import locale
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))  # S1_Prep->Stage1_Ground->Run->Staging->project
BEFORE_DIR = os.path.join(HERE, 'Before')
SCHEMA = 'environmentpipeline.s1_offline_backup.v2'
MANIFEST_NAME = 'BACKUP_MANIFEST.json'  # STAGE1_GROUND_PLAN.md:183 / REV precedent
SET_RE = re.compile(r'^S1B_(\d{8}T\d{6}Z)(?:_(\d+))?$')
HEX64 = re.compile(r'^[0-9a-f]{64}$')
PKG_MAGIC = b'\xc1\x83\x2a\x9e'  # FPackageFileSummary tag 0x9E2A83C1, little-endian
SIDECAR_EXTS = ('.uexp', '.ubulk', '.m.ubulk', '.uptnl')
CHUNK = 1 << 22

A = '/Game/Project/Shared/SurfacePainting/Appearance_20261003'
MW = '/Game/MWLandscapeAutoMaterial/Textures'
SHUJ = '/Game/Project/Areas/GazaShujaiya/BankIntegration_v015'
RIMAL = '/Game/Project/Areas/GazaRimal/BankIntegration_v015'
MASTER = A + '/M_SurfaceBank_Natural'  # path fixed by geocity_landscape_workflow.py:15-16
BASE_MI = A + '/MI_SurfaceBank_Natural'
CHILD_SHUJ = SHUJ + '/Materials/MI_GeoCityGround'
CHILD_RIMAL = RIMAL + '/Materials/MI_GeoCityGround'
MW_ROLE = 'mw_vendor_reference_readonly'

# (package, role). Every role not in EDIT_ROLES is preserved (S1 must never save it) and is pinned in
# preserved_files as well as copied, so it can be both detected and restored.
COPY_SET = [
    (MASTER, 'master_edit_target'),
    (BASE_MI, 'base_mi_preserved_iran'),
    (CHILD_SHUJ, 'child_GazaShujaiya_edit_target'),
    (CHILD_RIMAL, 'child_GazaRimal_edit_target'),
    (SHUJ + '/L_GazaShujaiya_BankIntegration', 'map_GazaShujaiya_preserved'),
    (RIMAL + '/L_GazaRimal_BankIntegration', 'map_GazaRimal_preserved'),
    (A + '/LG_GeoCity_PermittedGroundGrass', 'grass_type_preserved'),
    (A + '/Textures/T_Sand_01_Normal_GeoCity', 'pinned_normal_preserved'),
    (A + '/Textures/T_Sand_02_Normal_GeoCity', 'pinned_normal_preserved'),
] + [(MW + '/' + p, MW_ROLE) for p in (
    'Ground/TEX_MWAM_SandA_col', 'Ground/TEX_MWAM_SandA_nrm',
    'Ground/TEX_MWAM_SandC_col', 'Ground/TEX_MWAM_SandC_nrm',
    'Ground/TEX_MWAM_Dirt_col', 'Ground/TEX_MWAM_Dirt_nrm',
    'Ground/TEX_MWAM_Stones_col', 'Ground/TEX_MWAM_Stones_nrm',
    'FX/TEX_MW_Noise_msk',
    'Extra/TEX_MWAM_Variation_msk', 'Extra/TEX_MWAM_Variation_nrm')]
EDIT_ROLES = ('master_edit_target', 'child_GazaShujaiya_edit_target', 'child_GazaRimal_edit_target')

# Hash-only pins are DERIVED in collect_state (union, edit targets excluded):
#   explicit floor below | REV BACKUP_MANIFEST preserved_files keys | every /Game package imported by
#   IMPORT_SCAN | the whole Appearance_20261003/Textures tree | every file of the VAULT_PAIRS packs.
EXPLICIT_PINS = [
    A + '/Textures/EpicResident2K/T_Ground_Gravel_D_GeoCityResident2K',
    A + '/Textures/EpicResident2K/T_Ground_Gravel_N_GeoCityResident2K',
    A + '/Textures/EpicResident2K/T_Rock_Sandstone_D_GeoCityResident2K',
    A + '/Textures/EpicResident2K/T_Rock_Sandstone_N_GeoCityResident2K',
    A + '/Textures/T_Sand_01_Mask_GeoCity',
    '/Game/StarterContent/Textures/T_MacroVariation',
    '/Game/StarterContent/Textures/T_Ground_Gravel_D',
]
IMPORT_SCAN = [MASTER, BASE_MI, CHILD_SHUJ, CHILD_RIMAL]
APPEARANCE_TEXTURES_REL = 'Content/Project/Shared/SurfacePainting/Appearance_20261003/Textures'
VAULT_ROOT = 'C:/ProgramData/Epic/EpicGamesLauncher/VaultCache'
VAULT_PAIRS = [('MWLandscapeAutoMaterial', VAULT_ROOT + '/MWLandsc0bb389159dceV3/data/Content'),  # compare_vault.py:6-7
               ('HighPoly_Tree_Model', VAULT_ROOT + '/HighPoly7a52ca673258V1/data/Content')]     # compare_vault.py:8-9

# Planned new packages (S1_MINIMAL_SAFE_SPEC.json new_function_packages); must NOT exist at backup time.
NEW_ASSET_PATHS = [A + '/Functions/MF_GeoCity_' + n for n in
                   ('MacroNoise', 'DistanceBlend', 'MacroColor', 'SlopeBlend', 'HeightBlend')]
SPEC_REL = 'Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/S1_Prep/S1_MINIMAL_SAFE_SPEC.json'
FACTS_REL = 'Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground/S1_Prep/MASTER_GRAPH_FACTS_r030.json'
RUNTIME_MANIFEST_REL = 'Staging/SystemCompletion_2026-10-04/geocity_runtime_manifest.json'
# Ratified seal (AGENTS.md "manifest3cd33b15...", STAGE1_GROUND_PLAN.md:158). MEASURED: its 17 pins equal the
# REV sealed_files exactly. The on-disk manifest 258469e1 (geocity_roadbld_props.py bf59bf96 -> 2bf41ec3) has
# no ratification record; root must ratify or revert it before S1.
EXPECTED_RUNTIME_MANIFEST_SHA256 = '3cd33b1513c8c040377d0da9e98225c737bffa034f1241d99371b1e2e4c5a9cd'
REV_MANIFEST_REL = 'Staging/GroundPainting_2026-10-04/Revision_2026-10-05/BACKUP_MANIFEST.json'
REV_MANIFEST_SHA256 = '4e01a9926ae0e2479879a52fadeb13fdc1d3a927025e0db098f42b677e2bdd83'  # MEASURED 2026-10-05

# REV BACKUP_MANIFEST.json sealed_files key list (17 paths) = runtime manifest modules+startup+support_files.
SEALED_REL = ['Content/Python/' + n for n in (
    'geocity_bank_workflow.py', 'geocity_editor_action.py', 'geocity_landscape_workflow.py',
    'geocity_roadbld_clip.py', 'geocity_roadbld_grounding.py', 'geocity_roadbld_junctions.py',
    'geocity_roadbld_landscape.py', 'geocity_roadbld_props.py', 'geocity_roadbld_seams.py',
    'geocity_roadbld_topology.py', 'geocity_roadbld_workflow.py', 'geocity_runtime_guard.py',
    'init_unreal.py')] + ['Config/DefaultEngine.ini', 'Config/DefaultRoadBLD.ini',
                          'Staging/SystemCompletion_2026-10-04/launch_editor.ps1',
                          'Staging/SystemCompletion_2026-10-04/seal_runtime.py']

RESTORE_NOTE = ('Not performed by this script. With every editor closed and root approval: for each files[] row '
                'root names, copy backup -> <project>/file with shutil.copyfile (NOT copy2: backups are read-only and '
                'copy2 would carry the read-only bit into Content), then assert sha256 == row.sha256. Maps are '
                'non-World-Partition here (no Content/__ExternalActors__/Project/Areas, MEASURED), so the .umap is the '
                'full map state. MW rows are vault originals: restore them from VaultCache, never over a '
                'vault-identical file. Hash-only pins (preserved_files without a files[] row) detect change only.')


class Refuse(Exception):
    pass


# ---------------------------------------------------------------- helpers
def now_utc():
    return datetime.now(timezone.utc)


def L(path):
    """Extended-length path for Windows I/O (prepare_run.py:21)."""
    p = os.path.abspath(path)
    if os.name == 'nt' and not p.startswith('\\\\?\\'):
        p = '\\\\?\\' + p
    return p


def unL(path):
    return path[4:] if path.startswith('\\\\?\\') else path


def rel_of(root, path):
    return os.path.relpath(unL(path), unL(os.path.abspath(root))).replace(os.sep, '/')


def digest(path, sha1=False, sha256=True):
    h256 = hashlib.sha256() if sha256 else None
    h1 = hashlib.sha1() if sha1 else None
    n = 0
    with open(L(path), 'rb') as fh:
        for chunk in iter(lambda: fh.read(CHUNK), b''):
            if h256:
                h256.update(chunk)
            if h1:
                h1.update(chunk)
            n += len(chunk)
    return (h256.hexdigest() if h256 else None), (h1.hexdigest() if h1 else None), n


def sha256_file(path):
    return digest(path)[0]


def sha256_or_none(path):
    return sha256_file(path) if os.path.isfile(L(path)) else None


def pkg_file(root, pkg):
    """'/Game/X' -> <root>/Content/X.uasset (or .umap). None if neither exists."""
    assert pkg.startswith('/Game/') and '..' not in pkg, pkg
    base = os.path.join(root, 'Content', *pkg[len('/Game/'):].split('/'))
    for ext in ('.uasset', '.umap'):
        if os.path.isfile(L(base + ext)):
            return base + ext
    return None


def sidecars(main):
    stem = main.rsplit('.', 1)[0]
    return [stem + e for e in SIDECAR_EXTS if os.path.isfile(L(stem + e))]


def walk_files(top):
    out = []
    for dp, dn, fn in os.walk(L(top)):
        for f in fn:
            out.append(unL(os.path.join(dp, f)))
    return sorted(out)


def read_json(path):
    with open(L(path), 'r', encoding='utf-8-sig') as fh:
        return json.load(fh)


def iso_mtime(st):
    return datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat()


# ---------------------------------------------------------------- offline import-table reader (no unreal)
def package_imports(path, expected_package=None):
    """Return {'package', 'imports' (/Game Package imports), 'non_game_imports', 'game_names', ...}.
    Layout: uasset_offline.py:43-73. Extension MEASURED 2026-10-05 on master/base MI/children: LegacyFileVersion -9,
    FileVersionUE5 1018 (>= 1016 PACKAGE_SAVED_HASH: 20-byte SavedHash + TotalHeaderSize precede the custom
    versions), editor package, import entry 40 bytes == (ExportOffset - ImportOffset) / ImportCount.
    Raises Refuse on anything unexpected (fail closed)."""
    with open(L(path), 'rb') as fh:
        b = fh.read()
    pos = [0]

    def take(fmt):
        v = struct.unpack_from(fmt, b, pos[0])[0]
        pos[0] += struct.calcsize(fmt)
        return v

    def fstr():
        n = take('<i')
        if n == 0:
            return ''
        if abs(n) > 4096:
            raise ValueError('FString length %d' % n)
        if n > 0:
            v = b[pos[0]:pos[0] + n - 1].decode('latin-1')
            pos[0] += n
            return v
        v = b[pos[0]:pos[0] - 2 * n - 2].decode('utf-16-le')
        pos[0] += -2 * n
        return v

    try:
        if take('<I') != 0x9E2A83C1:
            raise ValueError('package magic')
        legacy = take('<i')
        if legacy not in (-8, -9):
            raise ValueError('LegacyFileVersion %d' % legacy)
        take('<i')
        take('<i')  # FileVersionUE4
        ue5 = take('<i')
        take('<i')  # licensee
        if not 1000 <= ue5 < 1100:
            raise ValueError('FileVersionUE5 %d' % ue5)
        if ue5 >= 1016:
            pos[0] += 20  # SavedHash
            take('<i')    # TotalHeaderSize
        ncv = take('<i')
        if not 0 <= ncv < 1000:
            raise ValueError('custom version count %d' % ncv)
        pos[0] += 20 * ncv
        if ue5 < 1016:
            take('<i')
        name = fstr()
        flags = take('<I')
        if flags & 0x80000000:
            raise ValueError('FilterEditorOnly package (import PackageName field absent)')
        name_count = take('<i')
        name_off = take('<i')
        if ue5 >= 1008:
            take('<i')
            take('<i')  # soft object paths
        fstr()  # LocalizationId (editor packages)
        take('<i')
        take('<i')  # gatherable text
        exp_count = take('<i')
        exp_off = take('<i')
        imp_count = take('<i')
        imp_off = take('<i')
        if not (0 < name_count < (1 << 20) and 0 < name_off < len(b) and 0 <= imp_count < (1 << 20)
                and 0 < imp_off <= len(b) and exp_count >= 0):
            raise ValueError('summary counts/offsets out of range')
        names = []
        r = name_off
        for _ in range(name_count):
            n = struct.unpack_from('<i', b, r)[0]
            r += 4
            if n >= 0:
                if n > 4096:
                    raise ValueError('name length %d' % n)
                names.append(b[r:r + n - 1].decode('latin-1'))
                r += n
            else:
                if -n > 4096:
                    raise ValueError('name length %d' % n)
                names.append(b[r:r - 2 * n - 2].decode('utf-16-le'))
                r += -2 * n
            r += 4  # name hashes (uasset_offline.py:62-63)
        esize = 8 + 8 + 4 + 8 + 8 + (4 if ue5 >= 1003 else 0)
        if imp_off + imp_count * esize > len(b):
            raise ValueError('import map past EOF')
        if exp_off > imp_off and exp_off - imp_off != imp_count * esize:
            raise ValueError('import map size %d != %d x %d' % (exp_off - imp_off, imp_count, esize))

        def fname(o):
            i, num = struct.unpack_from('<ii', b, o)
            if not 0 <= i < len(names):
                raise ValueError('name index %d' % i)
            return names[i] if num == 0 else '%s_%d' % (names[i], num - 1)

        pkgs = set()
        for k in range(imp_count):
            o = imp_off + k * esize
            cls = fname(o + 8)
            outer = struct.unpack_from('<i', b, o + 16)[0]
            obj = fname(o + 20)
            if cls == 'Package' and outer == 0:
                pkgs.add(obj)
    except (struct.error, ValueError, UnicodeDecodeError, IndexError) as exc:
        raise Refuse('cannot parse package header/import map of %s: %r' % (path, exc))
    if expected_package and name != expected_package:
        raise Refuse('package name %r in %s != expected %r' % (name, path, expected_package))
    return {'package': name, 'legacy': legacy, 'ue5': ue5, 'import_count': imp_count,
            'imports': sorted(p for p in pkgs if p.startswith('/Game/')),
            'non_game_imports': sorted(p for p in pkgs if not p.startswith(('/Game/', '/Script/'))),
            'game_names': sorted(n for n in names if n.startswith('/Game/'))}


# ---------------------------------------------------------------- editor guard (fail closed)
def tasklist_probe():
    exe = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32', 'tasklist.exe')
    try:
        proc = subprocess.run([exe, '/FO', 'CSV', '/NH'], capture_output=True, timeout=120)
    except Exception as exc:  # missing tool, timeout, sandbox
        raise Refuse('tasklist failed: %r' % (exc,))
    if proc.returncode != 0:
        raise Refuse('tasklist exit %d' % proc.returncode)
    text = proc.stdout.decode(locale.getpreferredencoding(False) or 'mbcs', errors='replace')
    rows = [r for r in csv.reader(io.StringIO(text)) if len(r) >= 2]
    pids = {r[1].strip() for r in rows}
    if len(rows) < 5 or str(os.getpid()) not in pids:  # own process must be listed, else the list is not trustworthy
        raise Refuse('tasklist output implausible (%d rows, own PID %s listed: %s)'
                     % (len(rows), os.getpid(), str(os.getpid()) in pids))
    editors = [{'image': r[0], 'pid': r[1]} for r in rows if r[0].strip().lower().startswith('unrealeditor')]
    return {'method': 'tasklist /FO CSV /NH', 'utc': now_utc().isoformat(), 'process_rows': len(rows),
            'unreal_editor_processes': editors}


# ---------------------------------------------------------------- configuration
def default_cfg(root=PROJECT_ROOT, seal_override=None):
    return {'root': root, 'vault_pairs': VAULT_PAIRS, 'expected_manifest_sha256': EXPECTED_RUNTIME_MANIFEST_SHA256,
            'rev_manifest_sha256': REV_MANIFEST_SHA256, 'seal_override': seal_override, 'imports_fn': package_imports}


def make_seal_override(sha, record, root=PROJECT_ROOT):
    """Root ratification of a runtime manifest other than the pinned one. The record must be an existing file
    under <project>/Staging whose text contains the exact sha. Never auto-accepts the on-disk manifest."""
    sha = (sha or '').strip().lower()
    if not HEX64.match(sha):
        raise Refuse('--ratified-seal must be an exact 64-hex sha256')
    if sha == EXPECTED_RUNTIME_MANIFEST_SHA256:
        raise Refuse('--ratified-seal equals the pinned seal; no override needed')
    rp = os.path.abspath(record)
    staging = os.path.join(os.path.abspath(root), 'Staging') + os.sep
    if not rp.startswith(staging) or not os.path.isfile(L(rp)):
        raise Refuse('--ratification-record must be an existing file under ' + staging)
    with open(L(rp), 'rb') as fh:
        text = fh.read().decode('utf-8', errors='replace').lower()
    if sha not in text:
        raise Refuse('ratification record does not name sha256 ' + sha)
    return {'sha256': sha, 'record': rel_of(root, rp), 'record_sha256': sha256_file(rp)}


# ---------------------------------------------------------------- state collection
def resolve_copy_set(root):
    rows = []
    for pkg, role in COPY_SET:
        main = pkg_file(root, pkg)
        if main is None:
            raise Refuse('copy-set package missing on disk: ' + pkg)
        for path in [main] + sidecars(main):
            rows.append({'package': pkg, 'role': role, 'src': path,
                         'sidecar_of': None if path == main else rel_of(root, main)})
    return rows


def scan_vendor_packs(root, pairs, blockers):
    """Every file of each vendor pack vs its VaultCache original (compare_vault.py pairing: path after /Content/)."""
    content = os.path.join(root, 'Content')
    rows, summary = {}, []
    for pack, vault_content in pairs:
        pdir = os.path.join(content, pack)
        vdir = os.path.join(vault_content, pack)
        s = {'pack': pack, 'project_dir': pdir.replace(os.sep, '/'), 'vault_dir': vdir.replace(os.sep, '/'),
             'files': 0, 'bytes': 0, 'identical': 0, 'differ': [], 'project_only': [], 'vault_only': []}
        summary.append(s)
        if not os.path.isdir(L(pdir)):
            blockers.append('vendor pack folder missing in project: Content/' + pack)
            continue
        if not os.path.isdir(L(vdir)):
            blockers.append('VaultCache original folder missing for %s: %s (vendor baseline unverifiable)' % (pack, vdir))
            continue
        proj = {rel_of(content, p): p for p in walk_files(pdir)}
        vault = {rel_of(vault_content, p): p for p in walk_files(vdir)}
        for rc, p in sorted(proj.items()):
            s256, s1, n = digest(p, sha1=True)
            rel = 'Content/' + rc
            row = {'pack': pack, 'sha256': s256, 'sha1': s1, 'bytes': n, 'vault_file': None, 'vault_sha1': None,
                   'vault_match': False}
            vf = vault.get(rc)
            if vf is None:
                s['project_only'].append(rel)
            else:
                _, v1, vn = digest(vf, sha1=True, sha256=False)
                row.update(vault_file=vf.replace(os.sep, '/'), vault_sha1=v1, vault_match=(v1 == s1 and vn == n))
                if row['vault_match']:
                    s['identical'] += 1
                else:
                    s['differ'].append(rel)
            rows[rel] = row
            s['files'] += 1
            s['bytes'] += n
        s['vault_only'] = sorted('Content/' + rc for rc in vault if rc not in proj)
        if s['differ']:
            blockers.append('%s: %d project file(s) differ from VaultCache: %s' % (pack, len(s['differ']), s['differ']))
        if s['project_only']:
            blockers.append('%s: %d project file(s) without a VaultCache original: %s'
                            % (pack, len(s['project_only']), s['project_only']))
        if s['vault_only']:
            blockers.append('%s: %d VaultCache file(s) missing in the project: %s'
                            % (pack, len(s['vault_only']), s['vault_only']))
    return rows, summary


def collect_state(cfg):
    """Hash everything (read-only). Returns the dict used for the manifest, idempotency and plan.
    'blockers' must be empty for a backup; 'warnings' are informational."""
    root = cfg['root']
    blockers, warnings = [], []
    vendor_rows, vendor_summary = scan_vendor_packs(root, cfg['vault_pairs'], blockers)

    # ---- copy set
    files = []
    for row in resolve_copy_set(root):
        st = os.stat(L(row['src']))
        rel = rel_of(root, row['src'])
        v = vendor_rows.get(rel)
        if v is not None:
            s256, n = v['sha256'], v['bytes']
        else:
            s256, _, n = digest(row['src'])
        if row['sidecar_of'] is None:
            with open(L(row['src']), 'rb') as fh:
                if fh.read(4) != PKG_MAGIC:
                    raise Refuse('not an Unreal package (magic): ' + row['src'])
        entry = {'file': rel, 'package': row['package'], 'role': row['role'], 'sidecar_of': row['sidecar_of'],
                 'sha256': s256, 'bytes': n, 'size_at_stat': st.st_size, 'mtime_ns': st.st_mtime_ns,
                 'mtime_utc': iso_mtime(st), 'src': row['src']}
        if row['role'] == MW_ROLE:
            if v is None:
                blockers.append('MW copy-set texture not covered by the vendor vault scan: ' + rel)
            else:
                entry.update(sha1=v['sha1'], vault_file=v['vault_file'], vault_sha1_match=v['vault_match'])
        files.append(entry)
    copy_files = {e['file'] for e in files}
    edit_files = {e['file'] for e in files if e['role'] in EDIT_ROLES}

    # ---- hash-only pins (derived)
    prov = {}

    def pin(rel, source):
        prov.setdefault(rel, set()).add(source)

    for pkg in EXPLICIT_PINS:
        f = pkg_file(root, pkg)
        if f is None:
            blockers.append('explicit pin missing on disk: ' + pkg)
            continue
        for p in [f] + sidecars(f):
            pin(rel_of(root, p), 'explicit')

    rev = {'path': REV_MANIFEST_REL, 'sha256': None, 'expected_sha256': cfg['rev_manifest_sha256'],
           'preserved_keys': 0, 'preserved_changed_since_rev': [], 'sealed_drift_vs_rev': []}
    rev_man = None
    rp = os.path.join(root, *REV_MANIFEST_REL.split('/'))
    if not os.path.isfile(L(rp)):
        blockers.append('REV BACKUP_MANIFEST missing: ' + REV_MANIFEST_REL)
    else:
        rev['sha256'] = sha256_file(rp)
        if rev['sha256'] != cfg['rev_manifest_sha256']:
            blockers.append('REV BACKUP_MANIFEST sha256 %s != pinned %s' % (rev['sha256'], cfg['rev_manifest_sha256']))
        else:
            rev_man = read_json(rp)
            rev['preserved_keys'] = len(rev_man.get('preserved_files', {}))
            for rel in rev_man.get('preserved_files', {}):
                pin(rel, 'rev_preserved_files')

    import_scan = []
    master_imports = None
    for pkg in IMPORT_SCAN:
        f = pkg_file(root, pkg)
        try:
            res = cfg['imports_fn'](f, pkg)
        except Refuse as exc:
            blockers.append(str(exc))
            continue
        extra = [n for n in res['game_names'] if n not in res['imports'] and n != pkg]
        if extra:
            warnings.append('%s: /Game names outside the import map (soft references, pinned when resolvable): %s'
                            % (pkg, extra))
        for ip in res['imports'] + extra:
            f2 = pkg_file(root, ip)
            if f2 is None:
                (blockers if ip in res['imports'] else warnings).append('unresolved /Game reference %s in %s' % (ip, pkg))
                continue
            for p in [f2] + sidecars(f2):
                pin(rel_of(root, p), 'imports:' + pkg)
        import_scan.append({'package': pkg, 'file': rel_of(root, f), 'import_count': res.get('import_count'),
                            'game_imports': len(res['imports']), 'non_game_imports': res['non_game_imports'],
                            'extra_game_names': extra})
        if pkg == MASTER:
            master_imports = set(res['imports'])

    td = os.path.join(root, *APPEARANCE_TEXTURES_REL.split('/'))
    if not os.path.isdir(L(td)):
        blockers.append('Appearance textures tree missing: ' + APPEARANCE_TEXTURES_REL)
    else:
        for p in walk_files(td):
            pin(rel_of(root, p), 'appearance_textures_tree')

    for rel in vendor_rows:
        pin(rel, 'vendor_pack:' + vendor_rows[rel]['pack'])

    excluded_edit_targets = sorted(r for r in prov if r in edit_files)
    hash_only = {}
    for rel in sorted(prov):
        if rel in copy_files:
            continue  # preserved roles are pinned from their copy row; edit targets are never pinned
        if rel in vendor_rows:
            hash_only[rel] = vendor_rows[rel]['sha256']
            continue
        p = os.path.join(root, *rel.split('/'))
        if not os.path.isfile(L(p)):
            blockers.append('hash-only pin missing on disk: ' + rel)
            continue
        hash_only[rel] = sha256_file(p)

    preserved = {e['file']: e['sha256'] for e in files if e['role'] not in EDIT_ROLES}
    preserved.update(hash_only)
    leaked = sorted(set(preserved) & edit_files)
    if leaked:
        blockers.append('edit targets would be pinned in preserved_files: %s' % leaked)
    provenance = {rel: sorted(prov.get(rel, set())) for rel in preserved}
    for e in files:
        if e['file'] in provenance:
            provenance[e['file']] = sorted(set(provenance[e['file']]) | {'copy_set:' + e['role']})
    if rev_man:
        rev['preserved_changed_since_rev'] = [{'file': rel, 'rev': h, 'current': preserved.get(rel)}
                                              for rel, h in sorted(rev_man['preserved_files'].items())
                                              if preserved.get(rel) != h]
        if rev['preserved_changed_since_rev']:
            warnings.append('INFO: %d REV preserved_files changed since REV (pinned at current values): %s'
                            % (len(rev['preserved_changed_since_rev']),
                               [r['file'] for r in rev['preserved_changed_since_rev']]))

    # ---- sealed runtime sources
    sealed = {}
    for rel in SEALED_REL:
        cur = sha256_or_none(os.path.join(root, *rel.split('/')))
        if cur is None:
            blockers.append('sealed file missing on disk: ' + rel)
        else:
            sealed[rel] = cur
    ov = cfg.get('seal_override')
    seal = {'manifest': RUNTIME_MANIFEST_REL, 'manifest_sha256': None, 'expected_sha256': cfg['expected_manifest_sha256'],
            'override': ov, 'accepted_by': None, 'pins_checked': 0, 'pin_keys_equal_sealed_rel': None,
            'drift_vs_manifest': [], 'drift_vs_rev': []}
    rm = os.path.join(root, *RUNTIME_MANIFEST_REL.split('/'))
    if not os.path.isfile(L(rm)):
        blockers.append('runtime seal manifest missing: ' + RUNTIME_MANIFEST_REL)
    else:
        seal['manifest_sha256'] = sha256_file(rm)
        if seal['manifest_sha256'] == cfg['expected_manifest_sha256']:
            seal['accepted_by'] = 'pinned'
        elif ov and seal['manifest_sha256'] == ov['sha256']:
            seal['accepted_by'] = 'ratification_record'
            warnings.append('runtime seal %s accepted via ratification record %s (pinned %s)'
                            % (ov['sha256'], ov['record'], cfg['expected_manifest_sha256']))
        else:
            blockers.append('runtime seal manifest %s sha256 %s != ratified %s (STAGE1_GROUND_PLAN.md:158); root must '
                            'ratify (--ratified-seal/--ratification-record) or revert before S1'
                            % (RUNTIME_MANIFEST_REL, seal['manifest_sha256'], cfg['expected_manifest_sha256']))
        man = read_json(rm)
        pins = {'Content/Python/' + v['file']: v['sha256'] for v in man.get('modules', {}).values()}
        if 'startup' in man:
            pins['Content/Python/' + man['startup']['file']] = man['startup']['sha256']
        pins.update(man.get('support_files', {}))
        seal['pin_keys_equal_sealed_rel'] = sorted(pins) == sorted(SEALED_REL)
        if not seal['pin_keys_equal_sealed_rel']:
            blockers.append('runtime manifest pin set != SEALED_REL: extra %s missing %s'
                            % (sorted(set(pins) - set(SEALED_REL)), sorted(set(SEALED_REL) - set(pins))))
        for rel, p in sorted(pins.items()):
            seal['pins_checked'] += 1
            cur = sealed.get(rel) if rel in sealed else sha256_or_none(os.path.join(root, *rel.split('/')))
            if cur != p:
                seal['drift_vs_manifest'].append({'file': rel, 'pinned': p, 'current': cur})
        if seal['drift_vs_manifest']:
            blockers.append('sealed files drift vs runtime manifest pins: %s' % [d['file'] for d in seal['drift_vs_manifest']])
    if rev_man:
        rs = rev_man.get('sealed_files', {})
        if sorted(rs) != sorted(SEALED_REL):
            blockers.append('REV sealed_files key list != SEALED_REL')
        seal['drift_vs_rev'] = [{'file': rel, 'rev': h, 'current': sealed.get(rel)}
                                for rel, h in sorted(rs.items()) if sealed.get(rel) != h]
        rev['sealed_drift_vs_rev'] = [d['file'] for d in seal['drift_vs_rev']]
        if seal['drift_vs_rev']:
            if seal['accepted_by'] == 'ratification_record':
                warnings.append('sealed files differ from REV sealed_files under the ratified seal: %s' % rev['sealed_drift_vs_rev'])
            else:
                blockers.append('sealed files differ from REV BACKUP_MANIFEST sealed_files: %s' % rev['sealed_drift_vs_rev'])

    # ---- planned new packages + spec
    existing_new = [p for p in NEW_ASSET_PATHS if pkg_file(root, p) is not None]
    if existing_new:
        blockers.append('planned new packages already exist on disk: %s' % existing_new)
    spec = {'path': SPEC_REL, 'sha256': None, 'matches_hardcoded_list': None}
    sp = os.path.join(root, *SPEC_REL.split('/'))
    if not os.path.isfile(L(sp)):
        blockers.append('S1_MINIMAL_SAFE_SPEC missing: ' + SPEC_REL)
    else:
        spec['sha256'] = sha256_file(sp)
        try:
            spec['matches_hardcoded_list'] = sorted(read_json(sp).get('new_function_packages', [])) == sorted(NEW_ASSET_PATHS)
        except Exception as exc:
            spec['matches_hardcoded_list'] = 'unreadable: %r' % (exc,)
        if spec['matches_hardcoded_list'] is not True:
            blockers.append('S1_MINIMAL_SAFE_SPEC new_function_packages differs from NEW_ASSET_PATHS')

    # ---- known baseline (facts the S1 spec was derived from)
    baseline = {'source': FACTS_REL, 'rows': [], 'all_equal': False, 'master_import_crosscheck': None}
    fp = os.path.join(root, *FACTS_REL.split('/'))
    if not os.path.isfile(L(fp)):
        warnings.append('MASTER_GRAPH_FACTS missing: ' + FACTS_REL)
    else:
        cur = {e['file']: e['sha256'] for e in files}
        facts = read_json(fp).get('current_disk_headers', {})
        for key, v in facts.items():
            if isinstance(v, dict) and str(v.get('file', '')).startswith('Content/'):
                baseline['rows'].append({'key': key, 'file': v['file'], 'known_sha256': v.get('sha256'),
                                         'current_sha256': cur.get(v['file']),
                                         'equal': cur.get(v['file']) == v.get('sha256')})
        baseline['all_equal'] = bool(baseline['rows']) and all(r['equal'] is True for r in baseline['rows'])
        if not baseline['all_equal']:
            warnings.append('known baseline mismatch vs MASTER_GRAPH_FACTS (ready_for_s1=false; refresh facts before '
                            'S1 relies on them): %s' % [r['key'] for r in baseline['rows'] if r['equal'] is not True])
        mrow = facts.get('master') if isinstance(facts.get('master'), dict) else None
        if mrow and master_imports is not None and isinstance(mrow.get('referenced_packages'), list):
            fset = set(mrow['referenced_packages']) - {MASTER}
            same_file = mrow.get('sha256') == cur.get(mrow.get('file'))
            baseline['master_import_crosscheck'] = {'facts_refs_minus_self': len(fset), 'parsed_imports': len(master_imports),
                                                    'equal': fset == master_imports, 'same_master_file': same_file}
            if same_file and fset != master_imports:
                blockers.append('import parser disagrees with MASTER_GRAPH_FACTS referenced_packages for the same master '
                                'file: only_facts %s only_parsed %s' % (sorted(fset - master_imports), sorted(master_imports - fset)))

    return {'files': files, 'hash_only': hash_only, 'preserved_files': preserved, 'preserved_provenance': provenance,
            'excluded_edit_targets': excluded_edit_targets, 'sealed_files': sealed, 'seal': seal, 'rev': rev,
            'import_scan': import_scan, 'vendor_rows': vendor_rows, 'vendor_summary': vendor_summary,
            'existing_new_asset_paths': existing_new, 'spec': spec, 'known_baseline_compare': baseline,
            'blockers': blockers, 'warnings': warnings}


def state_key(files_map, preserved, sealed, seal_sha):
    return json.dumps({'files': files_map, 'preserved': preserved, 'sealed': sealed, 'seal_manifest_sha256': seal_sha},
                      sort_keys=True)


def man_key(man):
    return state_key({r['file']: r['sha256'] for r in man['files']}, man['preserved_files'], man['sealed_files'],
                     man.get('seal', {}).get('manifest_sha256'))


def cur_key(state):
    return state_key({e['file']: e['sha256'] for e in state['files']}, state['preserved_files'], state['sealed_files'],
                     state['seal']['manifest_sha256'])


# ---------------------------------------------------------------- existing sets
def list_sets(before):
    out = []
    if not os.path.isdir(L(before)):
        return out
    for name in os.listdir(L(before)):
        m = SET_RE.match(name)
        if m:
            out.append(((m.group(1), int(m.group(2) or 1)), name))
    return [n for _, n in sorted(out, reverse=True)]


def load_set(before, name):
    mp = os.path.join(before, name, MANIFEST_NAME)
    if not os.path.isfile(L(mp)):
        return None
    try:
        man = read_json(mp)
    except Exception:
        return None
    return man if man.get('ready') is True and man.get('schema') == SCHEMA else None


def verify_set_integrity(before, name, man):
    bad = []
    for row in man['files']:
        b = os.path.join(before, name, *row['file'].split('/'))
        if not os.path.isfile(L(b)):
            bad.append({'file': row['file'], 'problem': 'missing backup'})
        elif sha256_file(b) != row['sha256']:
            bad.append({'file': row['file'], 'problem': 'backup sha256 mismatch'})
    return bad


def newest_complete(before):
    for name in list_sets(before):
        man = load_set(before, name)
        if man is not None:
            return name, man
    return None, None


# ---------------------------------------------------------------- backup
def backup(cfg=None, before=BEFORE_DIR, probe=tasklist_probe, force_new=False):
    cfg = cfg or default_cfg()
    root = cfg['root']
    pre_probe = probe()
    if pre_probe['unreal_editor_processes']:
        raise Refuse('UnrealEditor process present: %s' % pre_probe['unreal_editor_processes'])
    state = collect_state(cfg)
    if state['blockers']:
        raise Refuse('integrity blockers (%d): %s' % (len(state['blockers']), ' | '.join(state['blockers'])))
    key = cur_key(state)

    name, man = newest_complete(before)
    if man is not None and not force_new:
        if man_key(man) == key:
            bad = verify_set_integrity(before, name, man)
            if not bad:
                return {'status': 'UP_TO_DATE', 'set': os.path.join(before, name), 'warnings': state['warnings']}
            state['warnings'].append('newest identical set %s failed integrity %s; building a new set' % (name, bad))

    os.makedirs(L(before), exist_ok=True)
    stamp = now_utc().strftime('%Y%m%dT%H%M%SZ')
    n = 1
    while True:
        set_name = 'S1B_' + stamp + ('' if n == 1 else '_%d' % n)
        final = os.path.join(before, set_name)
        partial = final + '.partial'
        if not os.path.exists(L(final)) and not os.path.exists(L(partial)):
            break
        n += 1
    os.makedirs(L(partial), exist_ok=False)

    rows = []
    bindings = {}
    for e in state['files']:
        dest = os.path.join(partial, *e['file'].split('/'))
        if os.path.exists(L(dest)):
            raise Refuse('refusing to overwrite ' + dest)
        os.makedirs(L(os.path.dirname(dest)), exist_ok=True)
        shutil.copy2(L(e['src']), L(dest))  # prepare_run.py:31
        if sha256_file(dest) != e['sha256']:
            raise Refuse('copy hash mismatch (source changed during copy?): ' + e['file'])
        os.chmod(L(dest), stat.S_IREAD)
        final_dest = os.path.join(final, *e['file'].split('/'))
        row = {k: e[k] for k in ('file', 'sha256', 'bytes', 'package', 'role', 'sidecar_of', 'mtime_utc')}
        row['backup'] = final_dest
        for k in ('sha1', 'vault_file', 'vault_sha1_match'):
            if k in e:
                row[k] = e[k]
        rows.append(row)
        bindings[os.path.join(root, *e['file'].split('/'))] = {'backup': final_dest, 'sha256': e['sha256']}

    # TOCTOU: every copied, preserved and sealed source plus both pinned manifests must be unchanged after copying.
    changed = []
    copied = set()
    for e in state['files']:
        copied.add(e['file'])
        st = os.stat(L(e['src']))
        if st.st_size != e['bytes'] or st.st_mtime_ns != e['mtime_ns'] or sha256_file(e['src']) != e['sha256']:
            changed.append(e['file'])
    for rel, h in list(state['preserved_files'].items()) + list(state['sealed_files'].items()) + [
            (RUNTIME_MANIFEST_REL, state['seal']['manifest_sha256']), (REV_MANIFEST_REL, state['rev']['sha256'])]:
        if rel in copied:
            continue
        if sha256_or_none(os.path.join(root, *rel.split('/'))) != h:
            changed.append(rel)
    if changed:
        raise Refuse('sources changed while backing up (set left as %s): %s' % (partial, changed))
    post_probe = probe()
    if post_probe['unreal_editor_processes']:
        raise Refuse('UnrealEditor appeared during backup (set left as %s): %s'
                     % (partial, post_probe['unreal_editor_processes']))

    me = os.path.abspath(__file__)
    vendor_files = {rel: {k: v[k] for k in ('pack', 'sha1', 'bytes', 'vault_file', 'vault_sha1', 'vault_match')}
                    for rel, v in sorted(state['vendor_rows'].items())}
    manifest = {
        'schema': SCHEMA,
        'rev_schema_keys': 'ready, created_utc, files[{file,sha256,backup}], preserved_files, sealed_files, '
                           'new_asset_paths, pid, world, execution_thread_id, file_bindings (STAGE1_GROUND_PLAN.md:181-184)',
        'ready': True,
        'ready_for_s1': state['known_baseline_compare']['all_equal'],
        'created_utc': now_utc().isoformat(),
        'set_id': set_name,
        'offline': True,
        'pid': None, 'editor_pid': None, 'world': None,
        'pid_note': 'Offline backup: no editor process was running (editor_check); no world loaded.',
        'in_session_requirement': ('Offline set: files can change between this backup and editor startup. The S1 editor '
                                   'step must call s1_backup.verify(<this set>) inside its session immediately before '
                                   'its first change and require status INTACT.'),
        'execution_thread_id': os.environ.get('CODEX_THREAD_ID'),
        'execution_thread_id_note': 'CODEX_THREAD_ID when set by the runner; null otherwise.',
        'ordinary_generation_authorized': False,
        'project_root': root,
        'script': {'path': me, 'sha256': sha256_file(me)},
        'editor_check': {'before': pre_probe, 'after': post_probe},
        'copy_set_basis': ('REV files[] minus the 4 MOUT masks (master, base MI, both children, both maps, Grass type, '
                           'T_Sand_01/02_Normal_GeoCity) + 11 D2 MW textures; hash-only pins derived (explicit floor, '
                           'REV preserved_files keys, /Game imports of master/base MI/children, Appearance Textures tree, '
                           'all MW + HighPoly vendor files vs VaultCache)'),
        'files': rows,
        'file_bindings': bindings,
        'preserved_files': state['preserved_files'],
        'preserved_provenance': state['preserved_provenance'],
        'hash_only_files': sorted(state['hash_only']),
        'excluded_edit_targets': state['excluded_edit_targets'],
        'sealed_files': state['sealed_files'],
        'seal': state['seal'],
        'rev_precedent': state['rev'],
        'import_scan': state['import_scan'],
        'new_asset_paths': NEW_ASSET_PATHS,
        'new_asset_paths_absent_at_backup': True,
        'new_asset_paths_spec': state['spec'],
        'known_baseline_compare': state['known_baseline_compare'],
        'vendor_vault': {'pairs': [list(p) for p in cfg['vault_pairs']], 'summary': state['vendor_summary'],
                         'all_match': all(v['vault_match'] for v in state['vendor_rows'].values()),
                         'files': vendor_files},
        'totals': {'copied_files': len(rows), 'copied_bytes': sum(r['bytes'] for r in rows),
                   'preserved_files': len(state['preserved_files']), 'sealed_files': len(state['sealed_files']),
                   'vendor_files': len(vendor_files), 'vendor_bytes': sum(v['bytes'] for v in vendor_files.values())},
        'restore_note': RESTORE_NOTE,
        'blockers': [],
        'warnings': state['warnings'],
    }
    mpath = os.path.join(partial, MANIFEST_NAME)
    with open(L(mpath), 'x', encoding='utf-8') as fh:
        fh.write(json.dumps(manifest, indent=2) + '\n')
    os.chmod(L(mpath), stat.S_IREAD)
    if os.path.exists(L(final)):
        raise Refuse('final set folder appeared concurrently: ' + final)
    os.rename(L(partial), L(final))
    return {'status': 'CREATED', 'set': final, 'files': len(rows), 'bytes': manifest['totals']['copied_bytes'],
            'preserved_files': len(state['preserved_files']), 'ready_for_s1': manifest['ready_for_s1'],
            'vault_all_match': manifest['vendor_vault']['all_match'], 'warnings': state['warnings']}


# ---------------------------------------------------------------- plan / verify
def plan(cfg=None, before=BEFORE_DIR, probe=tasklist_probe):
    cfg = cfg or default_cfg()
    try:
        pr = probe()
    except Refuse as exc:
        pr = {'error': str(exc)}
    state = collect_state(cfg)
    name, man = newest_complete(before)
    up = man is not None and man_key(man) == cur_key(state)
    prov_counts = {}
    for srcs in state['preserved_provenance'].values():
        for s in srcs:
            k = s.split(':')[0] if s.startswith(('imports:', 'vendor_pack:', 'copy_set:')) else s
            prov_counts[k] = prov_counts.get(k, 0) + 1
    non_vendor_hash_only = {r: h for r, h in state['hash_only'].items() if r not in state['vendor_rows']}
    return {'status': 'PLAN_ONLY_NOTHING_WRITTEN',
            'editor_check': pr,
            'would_refuse': bool(pr.get('unreal_editor_processes') or pr.get('error') or state['blockers']),
            'blockers': state['blockers'],
            'newest_complete_set': name, 'would_be_up_to_date': up,
            'copy_set': [{k: e.get(k) for k in ('file', 'role', 'bytes', 'sha256', 'mtime_utc', 'vault_sha1_match')}
                         for e in state['files']],
            'copy_files': len(state['files']), 'copy_bytes': sum(e['bytes'] for e in state['files']),
            'preserved_count': len(state['preserved_files']), 'preserved_provenance_counts': prov_counts,
            'hash_only_non_vendor': non_vendor_hash_only, 'excluded_edit_targets': state['excluded_edit_targets'],
            'vendor_summary': [{k: v for k, v in s.items()} for s in state['vendor_summary']],
            'import_scan': state['import_scan'], 'seal': state['seal'], 'rev_precedent': state['rev'],
            'sealed_files': state['sealed_files'],
            'existing_new_asset_paths': state['existing_new_asset_paths'], 'spec': state['spec'],
            'known_baseline_compare': state['known_baseline_compare'], 'warnings': state['warnings']}


def verify(set_dir, root=PROJECT_ROOT, before=BEFORE_DIR):
    set_dir = os.path.abspath(set_dir if os.path.isabs(set_dir) else os.path.join(before, set_dir))
    name = os.path.basename(set_dir)
    if not SET_RE.match(name):
        raise Refuse('not a complete S1 backup set name (.partial or foreign folder): ' + set_dir)
    man = load_set(os.path.dirname(set_dir), name)
    if man is None:
        raise Refuse('not a complete S1 backup set: ' + set_dir)
    bad = verify_set_integrity(os.path.dirname(set_dir), name, man)
    edit_drift, other_drift = [], []
    for row in man['files']:
        cur = sha256_or_none(os.path.join(root, *row['file'].split('/')))
        if cur != row['sha256']:
            d = {'file': row['file'], 'role': row['role'], 'backup_sha256': row['sha256'], 'current': cur}
            (edit_drift if row['role'] in EDIT_ROLES else other_drift).append(d)
    pres_drift = []
    for rel, h in man['preserved_files'].items():
        cur = sha256_or_none(os.path.join(root, *rel.split('/')))
        if cur != h:
            pres_drift.append({'file': rel, 'pinned': h, 'current': cur})
    sealed_drift = []
    for rel, h in man['sealed_files'].items():
        cur = sha256_or_none(os.path.join(root, *rel.split('/')))
        if cur != h:
            sealed_drift.append({'file': rel, 'pinned': h, 'current': cur})
    seal_sha = man.get('seal', {}).get('manifest_sha256')
    cur_seal = sha256_or_none(os.path.join(root, *RUNTIME_MANIFEST_REL.split('/')))
    seal_manifest_changed = cur_seal != seal_sha
    if bad:
        status = 'BACKUP_DAMAGED'
    elif pres_drift or sealed_drift or other_drift or seal_manifest_changed:
        status = 'PRESERVED_DRIFT'
    elif edit_drift:
        status = 'EDIT_TARGETS_CHANGED'
    else:
        status = 'INTACT'
    return {'status': status, 'set': set_dir, 'backup_problems': bad,
            'project_files_changed_since_backup': edit_drift + other_drift,
            'preserved_files_changed': pres_drift, 'sealed_files_changed': sealed_drift,
            'runtime_manifest': {'backup': seal_sha, 'current': cur_seal, 'changed': seal_manifest_changed}}


FAIL_STATUSES = ('BACKUP_DAMAGED', 'PRESERVED_DRIFT')


# ---------------------------------------------------------------- selftest (synthetic, temp dir under S1_Prep)
def selftest():
    import tempfile
    tmp = tempfile.mkdtemp(prefix='_s1_backup_selftest_', dir=HERE)
    checks = []

    def ok(cond, what):
        checks.append({'check': what, 'pass': bool(cond)})
        if not cond:
            raise AssertionError(what)

    def put(path, data):
        os.makedirs(L(os.path.dirname(path)), exist_ok=True)
        if os.path.exists(L(path)):
            os.chmod(L(path), stat.S_IWRITE | stat.S_IREAD)
        with open(L(path), 'wb') as fh:
            fh.write(data)

    def refuses(fn, what):
        try:
            fn()
        except Refuse:
            ok(True, what)
            return
        ok(False, what)

    no_editor = lambda: {'method': 'stub', 'utc': now_utc().isoformat(), 'process_rows': 99, 'unreal_editor_processes': []}
    try:
        root, vroot, before = (os.path.join(tmp, x) for x in ('proj', 'vault', 'Before'))
        content = os.path.join(root, 'Content')

        def pf(pkg, ext='.uasset'):
            return os.path.join(content, *pkg[6:].split('/')) + ext

        for pkg, role in COPY_SET:
            put(pf(pkg, '.umap' if pkg.rsplit('/', 1)[1].startswith('L_') else '.uasset'), PKG_MAGIC + pkg.encode() * 64)
        put(pf(CHILD_RIMAL, '.ubulk'), b'bulk')
        mw_extra = '/Game/MWLandscapeAutoMaterial/Materials/MASTER/Func/MF_MWAM_DefaultLayer'
        hp_file = '/Game/HighPoly_Tree_Model/Meshes/SM_HP_Tree'
        for pkg in (mw_extra, hp_file):
            put(pf(pkg), PKG_MAGIC + pkg.encode())
        pairs = [('MWLandscapeAutoMaterial', os.path.join(vroot, 'MW', 'Content')),
                 ('HighPoly_Tree_Model', os.path.join(vroot, 'HP', 'Content'))]
        for pack, vc in pairs:
            for p in walk_files(os.path.join(content, pack)):
                with open(L(p), 'rb') as fh:
                    put(os.path.join(vc, *rel_of(content, p).split('/')), fh.read())
        for pkg in EXPLICIT_PINS:
            put(pf(pkg), PKG_MAGIC + pkg.encode())
        put(os.path.join(root, *APPEARANCE_TEXTURES_REL.split('/'), 'Resident4K', 'T_Sand_01_Albedo_GeoCityResident4K.uasset'),
            PKG_MAGIC + b'r4k')
        mout = '/Game/MOUT_Arabian/Textures/Landscape/Sand_01/T_Sand_01_Albedo'
        put(pf(mout), PKG_MAGIC + b'mout')
        imports = {MASTER: [mout, '/Game/StarterContent/Textures/T_MacroVariation', A + '/Textures/T_Sand_01_Normal_GeoCity'],
                   BASE_MI: [MASTER], CHILD_SHUJ: [BASE_MI], CHILD_RIMAL: [BASE_MI]}

        def imports_fn(path, pkg):
            return {'package': pkg, 'import_count': len(imports[pkg]), 'imports': sorted(imports[pkg]),
                    'non_game_imports': [], 'game_names': sorted(imports[pkg] + [pkg])}

        sealed_h = {}
        for rel in SEALED_REL:
            put(os.path.join(root, *rel.split('/')), rel.encode())
            sealed_h[rel] = hashlib.sha256(rel.encode()).hexdigest()

        def runtime_manifest(pins):
            return {'modules': {r.rsplit('/', 1)[1][:-3]: {'file': r.rsplit('/', 1)[1], 'sha256': h} for r, h in pins.items()
                                if r.startswith('Content/Python/') and not r.endswith('init_unreal.py')},
                    'startup': {'file': 'init_unreal.py', 'sha256': pins['Content/Python/init_unreal.py']},
                    'support_files': {r: h for r, h in pins.items() if not r.startswith('Content/Python/')}}
        rtp = os.path.join(root, *RUNTIME_MANIFEST_REL.split('/'))
        put(rtp, json.dumps(runtime_manifest(sealed_h)).encode())
        profile = 'Staging/ModelBank/X/AREA_PROFILE.json'
        put(os.path.join(root, *profile.split('/')), b'{}')
        revp = os.path.join(root, *REV_MANIFEST_REL.split('/'))
        put(revp, json.dumps({'preserved_files': {rel_of(root, pf(mout)): 'old', profile: 'old'},
                              'sealed_files': sealed_h}).encode())
        put(os.path.join(root, *SPEC_REL.split('/')), json.dumps({'new_function_packages': NEW_ASSET_PATHS}).encode())
        master_rel = rel_of(root, pf(MASTER))
        put(os.path.join(root, *FACTS_REL.split('/')), json.dumps({'current_disk_headers': {'master': {
            'file': master_rel, 'sha256': sha256_file(pf(MASTER)), 'referenced_packages': imports[MASTER] + [MASTER]}}}).encode())
        cfg = {'root': root, 'vault_pairs': pairs, 'expected_manifest_sha256': sha256_file(rtp),
               'rev_manifest_sha256': sha256_file(revp), 'seal_override': None, 'imports_fn': imports_fn}

        r1 = backup(cfg, before, no_editor)
        ok(r1['status'] == 'CREATED', 'first run creates a set')
        man1 = load_set(before, os.path.basename(r1['set']))
        ok(man1 and man1['ready'] and len(man1['files']) == len(COPY_SET) + 1, 'manifest ready, copy set + sidecar')
        ok(man1['ready_for_s1'] is True and man1['known_baseline_compare']['master_import_crosscheck']['equal'],
           'baseline equal and import cross-check equal')
        ok(man1['vendor_vault']['all_match'] is True and man1['totals']['vendor_files'] == 13, 'all vendor files vault-matched')
        edits = {e['file'] for e in man1['files'] if e['role'] in EDIT_ROLES}
        ok(len(edits) == 4 and not (edits & set(man1['preserved_files'])), 'edit targets (+ Rimal child sidecar) never in preserved_files')
        ok(master_rel in man1['excluded_edit_targets'], 'master import of base MI excluded as edit target')
        need = {rel_of(root, pf(p, '.umap' if p.rsplit('/', 1)[1].startswith('L_') else '.uasset'))
                for p, r in COPY_SET[:9]}
        ok(need <= {rel_of(root, k) for k in man1['file_bindings']}, 'bindings cover master/base/children/maps/grass/normals')
        ok(all(rel in man1['preserved_files'] for rel in (rel_of(root, pf(mw_extra)), rel_of(root, pf(hp_file)),
                                                         rel_of(root, pf(mout)), profile)), 'vendor, import and REV pins present')
        ok(len(man1['rev_precedent']['preserved_changed_since_rev']) == 2, 'REV value changes reported as info')
        ok(any('Resident4K' in r for r in man1['preserved_files']), 'Appearance Textures tree pinned')
        ok(any(f['sidecar_of'] for f in man1['files']), 'sidecar picked up')
        ok(not any(n.endswith('.partial') for n in os.listdir(before)), 'no .partial left')
        b0 = os.path.join(r1['set'], *man1['files'][0]['file'].split('/'))
        ok(not os.access(L(b0), os.W_OK), 'backup copy is read-only')
        r2 = backup(cfg, before, no_editor)
        ok(r2['status'] == 'UP_TO_DATE' and r2['set'] == r1['set'], 'second run is idempotent')
        snap1 = {f['file']: sha256_file(os.path.join(r1['set'], *f['file'].split('/'))) for f in man1['files']}
        put(pf(MASTER), PKG_MAGIC + b'edited')
        r3 = backup(cfg, before, no_editor)
        ok(r3['status'] == 'CREATED' and r3['set'] != r1['set'] and r3['ready_for_s1'] is False,
           'changed master -> new set, baseline mismatch -> ready_for_s1 false')
        ok(snap1 == {f['file']: sha256_file(os.path.join(r1['set'], *f['file'].split('/'))) for f in man1['files']},
           'old set untouched')
        v = verify(r3['set'], root, before)
        ok(v['status'] == 'INTACT' and not v['project_files_changed_since_backup'], 'verify intact, no drift')
        v1 = verify(r1['set'], root, before)
        ok(v1['status'] == 'EDIT_TARGETS_CHANGED', 'verify of older set: only edit target changed')
        mapf = pf(COPY_SET[4][0], '.umap')
        with open(L(mapf), 'rb') as fh:
            map_orig = fh.read()
        put(mapf, PKG_MAGIC + b'map edited')
        v2 = verify(r3['set'], root, before)
        ok(v2['status'] == 'PRESERVED_DRIFT' and len(v2['preserved_files_changed']) == 1, 'verify reports map drift')
        r4 = backup(cfg, before, no_editor)
        ok(r4['status'] == 'CREATED', 'preserved-file change -> new set')
        put(mapf, map_orig)
        r4 = backup(cfg, before, no_editor)
        ok(r4['status'] == 'CREATED' and verify(r4['set'], root, before)['status'] == 'INTACT', 'restored map -> new intact set')

        sets_before = sorted(os.listdir(before))
        refuses(lambda: backup(cfg, before, lambda: dict(no_editor(), unreal_editor_processes=[
            {'image': 'UnrealEditor.exe', 'pid': '1'}])), 'refuses with editor')
        put(pf(NEW_ASSET_PATHS[0]), PKG_MAGIC)
        refuses(lambda: backup(cfg, before, no_editor, force_new=True), 'refuses when planned new package exists')
        os.remove(L(pf(NEW_ASSET_PATHS[0])))
        # seal: manifest sha not ratified
        refuses(lambda: backup(dict(cfg, expected_manifest_sha256='0' * 64), before, no_editor), 'refuses unratified seal manifest')
        # seal: sealed file drift vs manifest pins
        props = os.path.join(root, 'Content', 'Python', 'geocity_roadbld_props.py')
        put(props, b'resealed props')
        refuses(lambda: backup(cfg, before, no_editor), 'refuses sealed-file drift vs manifest')
        # seal: new manifest re-pins props (unratified) -> refuses; with ratification record -> REV delta only warns
        new_pins = dict(sealed_h, **{'Content/Python/geocity_roadbld_props.py': sha256_file(props)})
        with open(L(rtp), 'rb') as fh:
            rt_orig = fh.read()
        put(rtp, json.dumps(runtime_manifest(new_pins)).encode())
        refuses(lambda: backup(cfg, before, no_editor), 'refuses resealed manifest without ratification')
        rec = os.path.join(root, 'Staging', 'RATIFY.json')
        put(rec, json.dumps({'ratified': sha256_file(rtp)}).encode())
        ov = make_seal_override(sha256_file(rtp), rec, root)
        st_ov = collect_state(dict(cfg, seal_override=ov))
        ok(not st_ov['blockers'] and st_ov['seal']['accepted_by'] == 'ratification_record'
           and st_ov['rev']['sealed_drift_vs_rev'] == ['Content/Python/geocity_roadbld_props.py'],
           'ratified seal accepted; REV delta reported')
        refuses(lambda: make_seal_override('a' * 64, rec, root), 'override record must name the sha')
        put(rtp, rt_orig)
        put(props, b'Content/Python/geocity_roadbld_props.py')
        # vendor: vault difference / project-only / vault-only
        vf = os.path.join(pairs[0][1], *rel_of(content, pf(mw_extra)).split('/'))
        with open(L(vf), 'rb') as fh:
            vf_orig = fh.read()
        put(vf, vf_orig + b'x')
        refuses(lambda: backup(cfg, before, no_editor), 'refuses MW vault difference')
        put(vf, vf_orig)
        extra = os.path.join(content, 'HighPoly_Tree_Model', 'Extra.uasset')
        put(extra, PKG_MAGIC)
        refuses(lambda: backup(cfg, before, no_editor), 'refuses project-only vendor file')
        os.remove(L(extra))
        vextra = os.path.join(pairs[1][1], 'HighPoly_Tree_Model', 'VaultOnly.uasset')
        put(vextra, PKG_MAGIC)
        refuses(lambda: backup(cfg, before, no_editor), 'refuses vault file missing in project')
        os.remove(L(vextra))
        refuses(lambda: backup(dict(cfg, vault_pairs=[('MWLandscapeAutoMaterial', os.path.join(vroot, 'none'))]),
                               before, no_editor), 'refuses missing vault folder')
        # imports: unresolved import
        imports[MASTER].append('/Game/Missing/T_Missing')
        refuses(lambda: backup(cfg, before, no_editor), 'refuses unresolved import')
        imports[MASTER].pop()
        # REV manifest pin
        refuses(lambda: backup(dict(cfg, rev_manifest_sha256='0' * 64), before, no_editor), 'refuses REV manifest change')
        ok(sorted(os.listdir(before)) == sets_before, 'refusals write nothing')

        os.makedirs(os.path.join(before, 'S1B_29991231T235959Z.partial'))
        r5 = backup(cfg, before, no_editor)
        ok(r5['status'] == 'UP_TO_DATE' and r5['set'] == r4['set'], '.partial sets are ignored')
        refuses(lambda: verify(os.path.join(before, 'S1B_29991231T235959Z.partial'), root, before), 'verify refuses .partial')
        put(props, b'drifted')
        v3 = verify(r4['set'], root, before)
        ok(v3['status'] == 'PRESERVED_DRIFT' and len(v3['sealed_files_changed']) == 1, 'verify reports sealed drift')
        put(props, b'Content/Python/geocity_roadbld_props.py')

        def failing_probe():
            raise Refuse('tasklist failed')
        refuses(lambda: backup(cfg, before, failing_probe), 'probe failure refuses')
        # mid-copy TOCTOU: a pinned (hash-only) source changes while copying -> refuse, set stays .partial
        real_copy2, mout_file = shutil.copy2, pf(mout)
        with open(L(mout_file), 'rb') as fh:
            mout_orig = fh.read()

        def copy2_then_touch(src, dst, *a, **k):
            r = real_copy2(src, dst, *a, **k)
            put(mout_file, mout_orig + b'changed mid-copy')
            return r
        shutil.copy2 = copy2_then_touch
        try:
            refuses(lambda: backup(cfg, before, no_editor, force_new=True), 'refuses source change during copy')
        finally:
            shutil.copy2 = real_copy2
        put(mout_file, mout_orig)
        calls = []

        def late_editor():
            calls.append(1)
            return dict(no_editor(), unreal_editor_processes=[] if len(calls) == 1 else [{'image': 'UnrealEditor.exe', 'pid': '2'}])
        refuses(lambda: backup(cfg, before, late_editor, force_new=True), 'refuses editor appearing during copy')
        partials = [n for n in os.listdir(before) if n.endswith('.partial') and not n.startswith('S1B_2999')]
        ok(len(partials) == 2 and newest_complete(before)[0] == os.path.basename(r4['set']),
           'refused runs leave only .partial folders, never a complete set')
        return {'status': 'SELFTEST_PASS', 'checks': checks}
    finally:
        for dp, dn, fn in os.walk(L(tmp)):
            for f in fn:
                try:
                    os.chmod(os.path.join(dp, f), stat.S_IWRITE | stat.S_IREAD)
                except OSError:
                    pass
        shutil.rmtree(L(tmp), ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--plan', action='store_true')
    g.add_argument('--verify', metavar='SET')
    g.add_argument('--selftest', action='store_true')
    ap.add_argument('--force-new', action='store_true', help='create a new set even if the newest set is identical')
    ap.add_argument('--ratified-seal', metavar='SHA256', help='root-ratified runtime manifest sha256 (with --ratification-record)')
    ap.add_argument('--ratification-record', metavar='FILE', help='file under <project>/Staging naming the ratified sha256')
    a = ap.parse_args(argv)
    if bool(a.ratified_seal) != bool(a.ratification_record):
        ap.error('--ratified-seal and --ratification-record must be given together')
    try:
        override = make_seal_override(a.ratified_seal, a.ratification_record) if a.ratified_seal else None
        if a.selftest:
            out = selftest()
        elif a.plan:
            out = plan(default_cfg(seal_override=override))
        elif a.verify:
            out = verify(a.verify)
        else:
            if not os.path.isfile(os.path.join(PROJECT_ROOT, 'Environmentpipeline.uproject')):
                raise Refuse('project root not found from script location: ' + PROJECT_ROOT)
            out = backup(default_cfg(seal_override=override), force_new=a.force_new)
    except Refuse as exc:
        print(json.dumps({'status': 'REFUSED', 'reason': str(exc)}, indent=2))
        return 1
    print(json.dumps(out, indent=2))
    return 1 if out.get('status') in FAIL_STATUSES or out.get('would_refuse') is True else 0  # README 7.13


if __name__ == '__main__':
    sys.exit(main())
