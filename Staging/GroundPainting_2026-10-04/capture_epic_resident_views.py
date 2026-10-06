"""Root orchestration: sequential reviewed native captures and actual PNG completion."""
import hashlib, json, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
area, stage, pid = sys.argv[1:4]
camera_sha = hashlib.sha256((HERE / ('CAMERAS_' + area + '.json')).read_bytes()).hexdigest()
for shot in sys.argv[4:] or ['close', 'middle', 'wide']:
    args = HERE / ('ARGS_capture_' + area + '_' + stage + '_' + shot + '.json')
    assert not args.exists()
    args.write_text(json.dumps({'expected_pid': int(pid), 'camera_file_sha256': camera_sha,
                               'stage': stage, 'shot': shot}), encoding='utf-8')
    run = subprocess.run([sys.executable, str(HERE/'copilot_call.py'),
                          str(HERE/'native_capture_epic_resident.py'), str(args)],
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    reply = json.loads(run.stdout)
    assert reply['ok'], reply
    request = reply['result']
    assert request['area'] == area and request['pid'] == int(pid), request
    run = subprocess.run([sys.executable, str(HERE/'tool_capture.py'), 'CaptureViewport',
                          'RoadBLDToolset.RoadBLDFeedbackToolset',
                          area + '_' + stage + '_' + shot + '_native.png'],
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    native = json.loads(run.stdout)
    assert 'image' in native, native
    capture = json.loads(Path(request['receipt']).read_text(encoding='utf-8-sig'))
    eye = capture['camera']['eye']
    assert all(abs(eye[i] - native['cameraLocation'][key]) < .01
               for i, key in enumerate(('x', 'y', 'z')))
    image = Path(request['path'])
    deadline = time.monotonic() + 12
    while not image.exists() and time.monotonic() < deadline:
        time.sleep(.25)
    assert image.exists(), request
    print(json.dumps({'area': area, 'stage': stage, 'shot': shot, 'file': str(image),
                      'bytes': image.stat().st_size, 'camera_matched': True}), flush=True)
