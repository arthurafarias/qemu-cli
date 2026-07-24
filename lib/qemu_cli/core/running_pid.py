import os
from typing import Optional

from .alive import alive
from .debug_log import trace
from .pidfile import pidfile
from .read_pid import read_pid


@trace
def running_pid(name: str) -> Optional[int]:
    pid = read_pid(name)
    if alive(pid):
        return pid
    # stale
    try:
        os.unlink(pidfile(name))
    except OSError:
        pass
    return None
