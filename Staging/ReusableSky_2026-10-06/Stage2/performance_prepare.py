import json
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()/'Staging/ReusableSky_2026-10-06/Stage2'
s=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
props={k:s.get_editor_property(k) for k in ['bThrottleCPUWhenNotForeground','bAllowSlateThrottling','bMonitorEditorPerformance','bEnableVSync']}
(root/'PERFORMANCE_EDITOR_SETTINGS_BEFORE.json').write_text(json.dumps(props,indent=2))
s.set_editor_property('bThrottleCPUWhenNotForeground',False)
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(w,'r.GPUCsvStatsEnabled 1')
RESULT={'temporary_editor_throttle_off':True,'original_settings':props,'GPU_stats_requested':True,'csv_start_api':'csvprofile frames=180','no_scalability_changed':True}


