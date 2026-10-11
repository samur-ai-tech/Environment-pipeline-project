"""In-editor, read-only: availability and doc of the legacy runtime spatial hash class in this build."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
c = getattr(u, 'WorldPartitionRuntimeSpatialHash', None)
doc = (c.__doc__ or '') if c else ''
RESULT = {'ok': True, 'spatial_hash_class': bool(c), 'doc': [l for l in doc.splitlines() if l.strip()][:25],
          'hashset_class': bool(getattr(u, 'WorldPartitionRuntimeHashSet', None)),
          'grid_doc': [l for l in ((getattr(u, 'SpatialHashRuntimeGrid', None).__doc__ or '') if getattr(u, 'SpatialHashRuntimeGrid', None) else '').splitlines() if '``' in l][:15]}
