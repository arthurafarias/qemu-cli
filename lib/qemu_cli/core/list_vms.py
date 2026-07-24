import os
import shlex
from typing import List

from .all_vms import all_vms
from .debug_log import trace
from .read_ini import read_ini
from .running_pid import running_pid
from .vm_list_entry import VmListEntry


@trace
def list_vms() -> List[VmListEntry]:
    out = []
    for name, path in all_vms().items():
        cfg = read_ini(path)
        cmdline = cfg.get("vm", "cmdline", fallback="")
        binary = shlex.split(cmdline)[0] if cmdline else "?"
        out.append(VmListEntry(
            name=name, path=path,
            binary=os.path.basename(binary),
            running=bool(running_pid(name)),
        ))
    return out
