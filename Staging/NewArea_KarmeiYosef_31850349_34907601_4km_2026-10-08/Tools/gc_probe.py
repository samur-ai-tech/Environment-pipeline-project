"""In-editor diagnosis (2026-10-10, three editor crashes in GC-like paths): force a garbage collection now, so a corrupted
Python/UObject reference left by the previous step crashes here instead of minutes later. No changes. ARGS: expected_pid."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
u.SystemLibrary.collect_garbage()
RESULT = {'ok': True, 'gc': 'done'}
