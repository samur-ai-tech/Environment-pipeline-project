"""In-editor, read-only: PCGComponent / PCGWorldActor partition-related API names and current values."""
import os, re
import unreal as u
assert os.getpid() == ARGS['expected_pid']
eas = u.get_editor_subsystem(u.EditorActorSubsystem)
doc = u.PCGComponent.__doc__ or ''
lines = [l for l in doc.splitlines() if re.search('artition|hlod|HLOD|grid|Grid', l)]
meth = [n for n in dir(u.PCGComponent) if re.search('artition|grid|hlod', n)]
wa = [a for a in eas.get_all_level_actors() if a.get_class().get_name() == 'PCGWorldActor']
wdoc = [l for l in (u.PCGWorldActor.__doc__ or '').splitlines() if re.search('artition|rid|ize', l)]
vol = [a for a in eas.get_all_level_actors() if isinstance(a, u.PCGVolume)][0]
c = vol.get_component_by_class(u.PCGComponent)
vals = {}
for n in ('is_partitioned', 'b_is_partitioned', 'is_component_partitioned'):
    try:
        vals[n] = str(c.get_editor_property(n))
    except Exception as e:
        vals[n] = 'n/a'
for n in meth:
    if n.startswith(('is_', 'get_')) and callable(getattr(c, n)):
        try:
            vals[n + '()'] = str(getattr(c, n)())[:80]
        except Exception as e:
            vals[n + '()'] = 'err'
RESULT = {'ok': True, 'doc_lines': lines[:30], 'methods': meth, 'world_actor_doc': wdoc[:20], 'values': vals,
          'world_actor_props': None}
