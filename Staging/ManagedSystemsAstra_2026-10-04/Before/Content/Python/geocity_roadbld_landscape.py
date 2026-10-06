"""Read the exact retained/official-current-cook Landscape collision surface."""
import math
import unreal


class LandscapeSampler:
    def __init__(self, run, saved=False):
        self.run = run
        self.world = run.guard()
        actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
        landscapes = [a for a in actors if isinstance(a, unreal.Landscape)]
        cooked = [a for a in landscapes if a.get_name().startswith('GeoCity_city_v015_PermanentBank_')
                  and a.get_name().endswith('_' + run.plan['area_id'] + '_landscape')]
        if saved:
            assert len(landscapes) == 1, 'Saved area requires exactly one Landscape'
            self.landscape = landscapes[0]
        else:
            assert len(cooked) == 1, 'Exactly one current official HDA cooked Landscape is required'
            self.landscape = cooked[0]
            assert all(a == self.landscape or a.get_name() == run.plan['area_id'] + '_landscape'
                       for a in landscapes), 'Unexpected Landscape ownership'
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
