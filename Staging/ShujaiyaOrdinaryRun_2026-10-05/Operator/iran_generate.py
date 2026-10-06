import os,json,unreal,importlib
assert os.getpid()==29900
import geocity_editor_action as ea
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_outermost().get_path_name()
assert world.endswith('L_Iran_38196167_46086167_4km'),world
r=ea.generate_current_area()
print(json.dumps({'ok':True,'dispatched':True,'returned':str(r)[:300],'world':world}))
RESULT={'ok':True,'returned':str(r)[:300]}
