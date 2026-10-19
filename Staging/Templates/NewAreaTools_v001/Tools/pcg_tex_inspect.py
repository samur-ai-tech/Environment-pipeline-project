"""In-editor, read-only: PCG texture node APIs. ARGS: expected_pid."""
import os, re
import unreal as u
assert os.getpid() == ARGS['expected_pid']
props = lambda c: re.findall(r'^\s*- ``(\w+)`` \(([^)]*)\)', c.__doc__ or '', re.M)
skip = ('debug', 'break', 'dump', 'print', 'profile', 'trigger', 'category', 'description', 'expose', 'execution_dep', 'determinism', 'enabled', 'execute_on_gpu', 'seed', 'use_seed')
out = {}
for n in ('PCGTextureSamplerSettings', 'PCGSampleTextureSettings', 'PCGTextureData', 'PCGBaseTextureData', 'PCGGetTextureInfoSettings'):
    c = getattr(u, n, None)
    out[n] = None if c is None else [(a, b[:40]) for a, b in props(c) if not a.startswith(skip)]
for n in ('PCGTextureMappingMethod', 'PCGTextureColorChannel', 'PCGTextureDensityFunction', 'PCGTextureFilter', 'PCGTextureAddressMode'):
    e = getattr(u, n, None)
    out[n] = None if e is None else [m for m in dir(e) if m.isupper()]
out['get_texture_like'] = [n for n in dir(u) if n.startswith('PCG') and ('GetTexture' in n or 'DataFromTexture' in n or 'TextureData' in n)]
RESULT = {'ok': True, **out}
