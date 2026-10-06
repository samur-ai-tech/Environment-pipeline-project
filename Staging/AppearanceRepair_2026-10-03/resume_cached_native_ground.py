"""Finish the original Rimal transaction from its verified transient meshes.

Scheduling returns immediately. The sole owner performs one actual native
seam/clip/validate/save operation and records any failure without saving it.
"""
import datetime
import importlib
import json
import time
from pathlib import Path
import unreal
import geocity_bank_workflow as bank
import geocity_roadbld_workflow as native
import geocity_roadbld_clip as clip
import geocity_roadbld_grounding as grounding
import geocity_roadbld_seams as seams

HERE = Path('C:/Users/USER/Documents/Unreal Projects/Environmentpipeline/Staging/AppearanceRepair_2026-10-03')
p, r = bank.ACTIVE[-1], native.ACTIVE[-1]
p.guard(); p.guard_processes(); r.guard()
assert r.area == 'GazaRimal' and not p.watch_tick and not p.save_tick and not r.tick_handle
assert r.state['phase'] == 'failed_clipping'
d = r._grounding_transient_diagnostic
assert len(d['rows']) == 24 and len(d['outputs']) == len(d['surfaces']) == 41
assert not r.network.is_road_network_stale()
for row in d['outputs']:
    assert native._path(row['component'].static_mesh) == row['original_mesh_path']
for module in (native, clip, grounding, seams):
    importlib.reload(module)
native.ACTIVE.append(r); r.__class__ = native.RoadBLDRun
r.on_complete = p.after_native_roads
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
status_path = HERE / ('NATIVE_CACHED_COMPLETION_' + stamp + '.json')

def record(phase, **values):
    payload = dict(area=r.area, phase=phase, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), **values)
    status_path.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    return payload

def finish_cached(delta_time):
    unreal.unregister_slate_post_tick_callback(r._cached_completion_tick)
    r._cached_completion_tick = None
    p.suspend_transaction_autosave()
    try:
        r.guard()
        record('repairing_exact_native_seam')
        seam_result = seams.repair_source_seams(r, d['surfaces'], r.landscape_sampler, empty_geos=d['empty'])
        seam_proof = seam_result[0] if isinstance(seam_result, tuple) else seam_result
        coverage = grounding.verify_source_coverage(r.plan, d['rows'], d['surfaces'],
            r.landscape_sampler, d['empty'], guard=r.guard)
        r.grounding_report = dict(schema=grounding.SCHEMA,
            phase='transient_grounded_physically_verified', landscape_actor_path=r.landscape_sampler.path,
            source_sha256=r.plan['source_sha256'], centreline_sha256=r.plan['centreline_sha256'],
            components=d['component_proofs'], source_coverage=coverage,
            automatic_empty_geometry=coverage['automatic_empty_geometry'],
            native_component_count=len(d['outputs']), assets_bound=False, saved=False, passed=True,
            native_seam_repair=seam_proof, retained_original_transients=True)
        r.state.update(phase='clipping', grounding_report=r.grounding_report)
        r.state.pop('error', None); r.write()
        record('clipping_verified_native_meshes', max_height_error_cm=coverage['max_surface_height_error_cm'])
        token = r.revision + '_' + datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S%f')
        r.clipping_report = clip.clip_native_outputs(r.plan, r.owned_actors(), r.guard,
            generation_id=token, max_seconds=600.,
            prepared_native_meshes={row['component_path']:row for row in d['outputs']})
        for path in r.clipping_report['created_asset_paths']:
            asset = unreal.load_asset(path)
            r.owned_assets[native._path(asset.get_outermost())] = asset.get_outermost()
        r.state.update(phase='validating', clipping_report=r.clipping_report); r.write()
        record('validating_actual_bound_native_meshes')
        r.validate(); r.finish()
        p.native_road_phase = 'authoring'; p.native_road_run = r; p.started_epoch = time.time()
        p.state.pop('error', None)
        p.wrapper.on_post_cook_delegate.add_callable(p.after_cook)
        p.wrapper.on_post_processing_delegate.add_callable(p.after_processing)
        p.watch_tick = unreal.register_slate_post_tick_callback(p.watch)
        p.after_native_roads(r, True)
        record('official_suppression_cook_started', native_validated=True, map_saved=False)
    except Exception as exc:
        r.fail(exc)
        record('failed_preserving_saved_map', error=repr(exc), map_saved=False)

record('scheduled', map_saved=False)
r._cached_completion_tick = unreal.register_slate_post_tick_callback(finish_cached)
print(json.dumps({'scheduled':True, 'status_path':str(status_path), 'same_editor_pid':__import__('os').getpid()}))
