"""In-editor, read-only: docstrings listing editor properties of HLOD classes."""
import os
import unreal as u
assert os.getpid() == ARGS['expected_pid']
RESULT = {'ok': True, 'HLODLayer': (u.HLODLayer.__doc__ or '')[:2500], 'Instancing': (u.HLODBuilderInstancingSettings.__doc__ or '')[:2500],
          'LayerType': [x for x in dir(u.HLODLayerType) if x.isupper()], 'EditorLoading': [x for x in dir(u.HLODLayerEditorLoadingBehavior) if x.isupper()],
          'PCGHLODSettings': (u.PCGHLODSettings.__doc__ or '')[:800]}
