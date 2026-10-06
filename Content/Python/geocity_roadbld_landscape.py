"""Read the exact retained/official-current-cook Landscape collision surface."""
import math
import hashlib
import json
import os
from pathlib import Path
import unreal


def _current_landscape(run, world, actors):
    """Resolve only the current official lifecycle's explicit live authority."""
    callback = run.landscape_authority
    parent = getattr(callback, '__self__', None)
    assert callable(callback) and parent is not None, 'Current Landscape requires a bound official lifecycle authority'
    assert parent is run._landscape_authority_parent, 'Landscape authority parent changed'
    parent.guard()
    assert parent.native_road_phase == 'authoring', 'Landscape authority is not the current authoring operation'
    assert parent.native_road_run is None or parent.native_road_run is run, 'Landscape authority belongs to another road operation'
    assert parent.lease_line == run.lease_line, 'Landscape authority lease differs'
    assert parent.p['map'] == run.plan['named_map'], 'Landscape authority map differs'
    source = Path(run.p['source']).resolve(strict=True)
    assert Path(parent.p['source']).resolve(strict=True) == source, 'Landscape authority source differs'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == run.plan['source_sha256'], 'Current geographic source changed'
    previous = parent.state['previous_landscape_accounting']
    assert not previous['unaccounted_actor_paths'], 'Previous Landscape ownership was not established'
    assert previous['source_sha256'] == run.plan['source_sha256'], 'Previous Landscape source differs'
    allowed = previous['live_actor_paths']
    assert len(allowed) == len(set(allowed)), 'Duplicate previous Landscape identities'
    assert set(allowed).issubset(parent.previous_baked_paths), 'Previous Landscape lacks retained lifecycle ownership'
    owner = parent.wrapper.get_houdini_asset_actor()
    live = {actor.get_path_name(): actor for actor in actors}
    assert len(live) == len(actors), 'Duplicate loaded actor identities'
    assert owner and live.get(owner.get_path_name()) == owner, 'Current official HDA owner is not loaded'
    assert previous['hda_actor_path'] == owner.get_path_name(), 'Official HDA owner changed'
    assert owner.get_outermost().get_path_name() == run.plan['named_map'], 'Official HDA owner is in another world'
    authority = callback()
    assert isinstance(authority, dict), 'Missing current Landscape authority'
    actor, evidence = authority.get('actor'), authority.get('evidence')
    assert isinstance(actor, unreal.Landscape) and isinstance(evidence, dict), 'Incomplete current Landscape authority'
    path = actor.get_path_name()
    assert live.get(path) == actor and unreal.load_object(None, path) == actor, 'Current Landscape object is missing or stale'
    assert actor.get_outermost().get_path_name() == world.get_outermost().get_path_name() == run.plan['named_map'], 'Current Landscape is in another world'
    prefix = run.plan['named_map'] + '.' + run.plan['named_map'].rsplit('/', 1)[-1] + ':PersistentLevel.'
    assert path.startswith(prefix) and all(p.startswith(prefix) for p in allowed), 'Landscape path is outside the named world'
    expected = {
        'schema': 'environmentpipeline.current_road_landscape.v1', 'pid': os.getpid(),
        'named_map': run.plan['named_map'], 'area_id': run.plan['area_id'],
        'source_sha256': run.plan['source_sha256'], 'centreline_sha256': run.plan['centreline_sha256'],
        'lease_sha256': hashlib.sha256(run.lease_line.encode('utf-8')).hexdigest(),
        'operation_started_epoch': parent.started_epoch, 'hda_actor_path': owner.get_path_name(),
        'current_actor_path': path, 'accounted_previous_landscape_paths': sorted(allowed),
        'official_output_verified': True}
    assert evidence.get('official_output_verified') is True, 'Official current Landscape output is unverified'
    assert evidence == expected, 'Current Landscape operation/source/owner evidence differs'
    landscape_paths = {a.get_path_name() for a in actors if isinstance(a, unreal.Landscape)}
    assert not landscape_paths - {path} - set(allowed), 'Unexpected Landscape ownership'
    frozen = run._current_landscape_evidence
    if frozen is not None:
        assert run._current_landscape_actor == actor and frozen == expected, 'Current Landscape authority changed during road operation'
    else:
        run._current_landscape_actor = actor
        run._current_landscape_evidence = json.loads(json.dumps(expected))
    run.state['current_landscape_authority'] = json.loads(json.dumps(expected))
    return actor


class LandscapeSampler:
    def __init__(self, run, saved=False):
        self.run = run
        self.world = run.guard()
        actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
        landscapes = [a for a in actors if isinstance(a, unreal.Landscape)]
        if saved:
            assert len(landscapes) == 1, 'Saved area requires exactly one Landscape'
            self.landscape = landscapes[0]
        else:
            self.landscape = _current_landscape(run, self.world, actors)
        self.path = self.landscape.get_path_name()
        assert self.path.startswith(run.plan['named_map'] + '.')
        self.ignored = [a for a in actors if a != self.landscape]
        self.cache = {}

    def __call__(self, x, y):
        key = (round(float(x), 6), round(float(y), 6))
        if key not in self.cache:
            self.run.guard()
            hit = unreal.SystemLibrary.line_trace_single(self.world,
                unreal.Vector(x, y, 100000.0), unreal.Vector(x, y, -100000.0),
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, self.ignored,
                unreal.DrawDebugTrace.NONE, False)
            assert hit is not None, 'Authoritative Landscape collision is missing at ' + str(key)
            fields = hit.to_dict()
            assert fields['blocking_hit'] and not fields['initial_overlap']
            assert fields['hit_actor'] == self.landscape
            component = fields['hit_component']
            assert isinstance(component, unreal.LandscapeHeightfieldCollisionComponent)
            assert component.get_owner() == self.landscape
            point = fields['impact_point']
            assert abs(point.x - x) < 0.001 and abs(point.y - y) < 0.001
            assert math.isfinite(point.z)
            self.cache[key] = float(point.z)
        return self.cache[key]
