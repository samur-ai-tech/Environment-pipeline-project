"""S1 in-editor env setter for s1_material_edit.py (EDIT reads only os.environ['GEOCITY_S1_ARGS'], EDIT:2124).

IN-EDITOR, sent by S1_Prep/run_s1.py through run_unreal_skill inline (ARGS global in, RESULT out). It only
sets / clears / reads one environment variable of the editor process. No asset, map, actor, CVar or file
write; `unreal` is used only to resolve the project directory.

ARGS
  {"action": "set", "path": "<abs args .json under Stage1_Ground>", "sha256": "<64hex of that file>"}
      refuses when GEOCITY_S1_ARGS is already set (stale value from an interrupted run: clear it first)
  {"action": "clear", "expected_path": "<abs path or null>"}   always pops; reports the previous value
  {"action": "status"}
Importing this file without ARGS is idle.
"""
import hashlib
import os
from pathlib import Path

KEY = 'GEOCITY_S1_ARGS'
REL_STAGE = 'Staging/ShujaiyaOrdinaryRun_2026-10-05/Stage1_Ground'


def _stage():
    import unreal
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
    return root / REL_STAGE


def _run(args):
    action = args.get('action')
    prior = os.environ.get(KEY)
    if action == 'status':
        return {'ok': True, 'action': 'status', 'pid': os.getpid(), 'value': prior}
    if action == 'clear':
        os.environ.pop(KEY, None)
        expected = args.get('expected_path')
        return {'ok': True, 'action': 'clear', 'pid': os.getpid(), 'previous': prior,
                'previous_matched_expected': None if expected is None else prior == expected,
                'now': os.environ.get(KEY)}
    if action == 'set':
        if prior is not None:
            return {'ok': False, 'action': 'set', 'pid': os.getpid(), 'previous': prior,
                    'error': KEY + ' is already set (interrupted earlier run?); run: run_s1.py --clear-env'}
        file = Path(args['path']).resolve(strict=True)
        if not (file.is_relative_to(_stage()) and file.suffix == '.json'):
            return {'ok': False, 'action': 'set', 'error': 'Args must be a .json file under Stage1_Ground: ' + str(file)}
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        if digest != args.get('sha256'):
            return {'ok': False, 'action': 'set', 'error': 'Args file sha256 differs from the runner: ' + digest}
        os.environ[KEY] = str(file)
        return {'ok': True, 'action': 'set', 'pid': os.getpid(), 'value': os.environ[KEY], 'sha256': digest}
    return {'ok': False, 'error': 'action must be set, clear or status'}


if 'ARGS' in globals():
    RESULT = _run(ARGS)  # noqa: F821 (injected by run_unreal_skill)
