"""Apply the brief-1 call-site patches to the working copies (exact, once-only replacements)."""
from pathlib import Path
here = Path(__file__).resolve().parent


def patch(name, pairs):
    path = here / name
    text = path.read_text(encoding='utf-8')
    for old, new in pairs:
        if text.count(old) != 1:
            raise SystemExit('%s: expected exactly one occurrence of %r' % (name, old[:60]))
        text = text.replace(old, new, 1)
    path.write_text(text, encoding='utf-8', newline='\n')
    print('patched', name, len(pairs), 'sites')


patch('geocity_editor_action.py', [
    (
        "def lease_fields(line):\n    return dict(re.findall(r'(?:^|\\s)([A-Za-z_]+)=([^\\s]+)', line))\n",
        "def lease_fields(line):\n    import geocity_runtime_guard\n    return geocity_runtime_guard.lease_fields(line)\n",
    ),
    (
        "        lease_path=project/'Staging/ModelBank/EDITOR_OWNER.txt'\n"
        "        lease=lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]\n"
        "        managed = managed_operation_lease(project,lease,world_path)\n"
        "        if lease_fields(lease).get('OWNER') != 'NONE' and not managed:\n",
        "        lease_path=project/'Staging/ModelBank/EDITOR_OWNER.txt'\n"
        "        # Ownership is this PID's own last lease line; other recorded editors' lines are not takeovers.\n"
        "        lease=geocity_runtime_guard.own_lease_line(project)\n"
        "        managed = lease is not None and managed_operation_lease(project,lease,world_path)\n"
        "        if lease is not None and lease_fields(lease).get('OWNER') != 'NONE' and not managed:\n",
    ),
    (
        "        process_read=subprocess.run(['powershell.exe','-NoProfile','-Command','Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],capture_output=True,text=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)\n"
        "        process_read.check_returncode()\n"
        "        pids=[int(p) for p in process_read.stdout.split()]\n"
        "        if pids!=[os.getpid()]:\n"
        "            raise RuntimeError('GeoCity requires this to be the only open Unreal editor.')\n"
        "        if lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]!=lease:\n",
        "        # Other live editors are allowed only with a record whose scope is disjoint from this run.\n"
        "        parallel=geocity_runtime_guard.require_parallel_editors(project,matching[0],os.getpid())\n"
        "        unreal.log('GeoCity parallel editor check '+parallel['verdict']+': '+parallel['summary'])\n"
        "        if geocity_runtime_guard.own_lease_line(project)!=lease:\n",
    ),
    (
        "        if menu_lease is not None and lease_path.read_text(encoding='utf-8-sig').splitlines()[-1] == menu_lease:\n",
        "        if menu_lease is not None and geocity_runtime_guard.own_lease_line(project) == menu_lease:\n",
    ),
])

patch('geocity_bank_workflow.py', [
    (
        "    from geocity_editor_action import lease_fields, managed_operation_lease\n"
        "    lease=(project/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]\n"
        "    fields=lease_fields(lease)\n"
        "    assert fields.get('OWNER') not in (None,'NONE','CODEX_MANAGED_SYSTEMS_STARTUP') and fields.get('assigned_editor_PID')==str(os.getpid()),lease\n",
        "    from geocity_editor_action import lease_fields, managed_operation_lease\n"
        "    import geocity_runtime_guard\n"
        "    # This editor's own last lease line; lines of other recorded editors are not ownership changes.\n"
        "    lease=geocity_runtime_guard.own_lease_line(project)\n"
        "    fields=lease_fields(lease)\n"
        "    assert lease and fields.get('OWNER') not in (None,'NONE','CODEX_MANAGED_SYSTEMS_STARTUP') and fields.get('assigned_editor_PID')==str(os.getpid()),repr(lease)\n",
    ),
    (
        "        self.lease_line=(self.project/'Staging/ModelBank/EDITOR_OWNER.txt').read_text(encoding='utf-8-sig').splitlines()[-1]\n",
        "        import geocity_runtime_guard\n"
        "        self.lease_line=geocity_runtime_guard.own_lease_line(self.project)\n",
    ),
    (
        "            lease_path=self.project/'Staging/ModelBank/EDITOR_OWNER.txt'\n"
        "            latest=lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]\n",
        "            import geocity_runtime_guard\n"
        "            lease_path=self.project/'Staging/ModelBank/EDITOR_OWNER.txt'\n"
        "            latest=geocity_runtime_guard.own_lease_line(self.project)\n",
    ),
    (
        "    def guard_processes(self):\n"
        "        process_read=subprocess.run(['powershell.exe','-NoProfile','-Command','Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],capture_output=True,text=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)\n"
        "        process_read.check_returncode()\n"
        "        assert [int(p) for p in process_read.stdout.split()]==[os.getpid()],'Exactly one Unreal editor is required'\n",
        "    def guard_processes(self):\n"
        "        \"\"\"Refuse unless every other live editor is recorded with a scope disjoint from this run.\"\"\"\n"
        "        import geocity_runtime_guard\n"
        "        report=geocity_runtime_guard.require_parallel_editors(self.project,self.profile_path,os.getpid())\n"
        "        self.state.setdefault('parallel_editor_checks',[]).append(report)\n",
    ),
    (
        "    def bake_and_save(self):\n"
        "        self.guard()\n"
        "        assert self.state['phase']=='cooked_verified'\n",
        "    def bake_and_save(self):\n"
        "        self.guard()\n"
        "        # Recheck parallel editors before the named Bake/saves (AGENTS.md parallel-editor rule).\n"
        "        self.guard_processes()\n"
        "        assert self.state['phase']=='cooked_verified'\n",
    ),
])

patch('geocity_roadbld_workflow.py', [
    (
        "        self.lease_line = self.lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]\n",
        "        import geocity_runtime_guard\n"
        "        self.lease_line = geocity_runtime_guard.own_lease_line(self.project)\n",
    ),
    (
        "        lease = self.lease_path.read_text(encoding='utf-8-sig').splitlines()[-1]\n"
        "        assert lease == self.lease_line and 'OWNER=NONE' not in lease and f'assigned_editor_PID={os.getpid()}' in lease, 'Root editor lease is missing or changed'\n",
        "        import geocity_runtime_guard\n"
        "        lease = geocity_runtime_guard.own_lease_line(self.project) or ''\n"
        "        assert lease and lease == self.lease_line and 'OWNER=NONE' not in lease and f'assigned_editor_PID={os.getpid()}' in lease, 'Root editor lease is missing or changed'\n",
    ),
    (
        "        process = subprocess.run(['powershell.exe', '-NoProfile', '-Command',\n"
        "                                  'Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],\n"
        "                                 capture_output=True, text=True, timeout=10,\n"
        "                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))\n"
        "        assert process.returncode == 0 and sorted(int(x) for x in process.stdout.split()) == [os.getpid()], 'Exactly one Unreal editor is required'\n",
        "        # Other live editors are allowed only with a record whose scope is disjoint from this run.\n"
        "        import geocity_runtime_guard\n"
        "        self.state['parallel_editor_check'] = geocity_runtime_guard.require_parallel_editors(\n"
        "            self.project, self.profile_path or self.p, os.getpid())\n",
    ),
])
