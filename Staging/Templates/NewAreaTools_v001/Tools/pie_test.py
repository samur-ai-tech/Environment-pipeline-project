"""In-editor (Karmei Yosef operator, play-mode test 2026-10-10; Aviv: "Play-mode test first"). Drives Play In Editor on the
loaded map: real World Partition streaming from the player position, in-game screenshots, CSV frame-time capture.
No saves; PIE changes are discarded when play ends.
steps (ARGS.step):
  start      request PIE.
  state      read-only: PIE running?, player pawn location, actors in the game world by class (HLOD / buildings / PCG cells...).
  move       ARGS.eye [x,y,z], ARGS.target [x,y,z]: put the player pawn there, looking at the target (controller rotation too).
  shot       HighResShot of the PIE viewport (ARGS.res, default 1600x900); file lands in Saved/Screenshots.
  csv_start  'csvprofile start'; csv_stop  'csvprofile stop' (CSV in Saved/Profiling/CSV).
  stop       end PIE.
ARGS: expected_pid, step, ...
"""
import math, os
from collections import Counter
import unreal as u
assert os.getpid() == ARGS['expected_pid']
les = u.get_editor_subsystem(u.LevelEditorSubsystem)
ues = u.get_editor_subsystem(u.UnrealEditorSubsystem)
step = ARGS['step']
gw = ues.get_game_world()


def rot(eye, target):
    dx, dy, dz = (target[i] - eye[i] for i in range(3)); h = math.hypot(dx, dy)
    return u.Rotator(roll=0.0, pitch=math.degrees(math.atan2(dz, h)), yaw=math.degrees(math.atan2(dy, dx)))


if step == 'start':
    assert gw is None, 'PIE already running'
    les.editor_request_begin_play()
    RESULT = {'ok': True, 'requested': True}

elif step == 'state':
    out = {'pie': gw is not None}
    if gw:
        pawn = u.GameplayStatics.get_player_pawn(gw, 0)
        out['pawn'] = pawn.get_class().get_name() if pawn else None
        out['pawn_loc'] = [round(v) for v in (pawn.get_actor_location().x, pawn.get_actor_location().y, pawn.get_actor_location().z)] if pawn else None
        acts = u.GameplayStatics.get_all_actors_of_class(gw, u.Actor)
        def g(a):
            n = a.get_class().get_name(); lab = a.get_name()
            return 'HLOD' if n.startswith('WorldPartitionHLOD') else ('Bldg' if any(c.get_name().startswith('BuildingRoot') for c in a.get_components_by_class(u.SceneComponent)) else n)
        out['actors'] = len(acts)
        out['by_class'] = dict(Counter(g(a) for a in acts).most_common(14))
        vis = 0; hid = 0
        for a in acts:
            if a.get_class().get_name().startswith('WorldPartitionHLOD'):
                comps = a.get_components_by_class(u.PrimitiveComponent)
                shown = any(c.is_visible() for c in comps) and not a.get_editor_property('hidden')
                vis += shown; hid += (not shown)
        out['hlod_visible'] = vis; out['hlod_hidden'] = hid
    RESULT = {'ok': True, **out}

elif step == 'move':
    assert gw is not None, 'PIE not running'
    eye, target = ARGS['eye'], ARGS['target']
    pawn = u.GameplayStatics.get_player_pawn(gw, 0)
    pc = u.GameplayStatics.get_player_controller(gw, 0)
    r = rot(eye, target)
    if pawn:
        pawn.set_actor_location_and_rotation(u.Vector(*eye), r, False, True)
    if pc:
        pc.set_control_rotation(r)
    RESULT = {'ok': True, 'pawn': pawn.get_class().get_name() if pawn else None, 'rot': [round(r.pitch, 1), round(r.yaw, 1)]}

elif step == 'shot':
    assert gw is not None
    u.SystemLibrary.execute_console_command(gw, 'HighResShot %s' % ARGS.get('res', '1600x900'))
    RESULT = {'ok': True}

elif step in ('csv_start', 'csv_stop'):
    w = gw or ues.get_editor_world()
    u.SystemLibrary.execute_console_command(w, 'csvprofile start' if step == 'csv_start' else 'csvprofile stop')
    RESULT = {'ok': True}

elif step == 'unthrottle':
    # editor would drop to ~3 fps when not the foreground window; in-memory only (the editor runs with -NoSaveConfig)
    ps = u.find_object(None, '/Script/UnrealEd.Default__EditorPerformanceSettings')
    ps.set_editor_property('bThrottleCPUWhenNotForeground', False)
    RESULT = {'ok': True, 'throttle': bool(ps.get_editor_property('bThrottleCPUWhenNotForeground'))}

elif step == 'stop':
    if gw is not None:
        les.editor_request_end_play()
    RESULT = {'ok': True, 'was_running': gw is not None}
