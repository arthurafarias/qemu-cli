import os
import time
from typing import List

from .all_vms import all_vms
from .debug_log import trace
from .pidfile import pidfile
from .running_pid import running_pid
from .vm_proc_entry import VmProcEntry


@trace
def ps_vms() -> List[VmProcEntry]:
    rows = []
    for name in all_vms():
        pid = running_pid(name)
        if not pid:
            continue
        try:
            started = os.stat(pidfile(name)).st_mtime
            up = int(time.time() - started)
            uptime = f"{up // 3600}h{(up % 3600) // 60:02d}m"
        except OSError:
            uptime = "?"
        rows.append(VmProcEntry(name=name, pid=pid, uptime=uptime))
    return rows
