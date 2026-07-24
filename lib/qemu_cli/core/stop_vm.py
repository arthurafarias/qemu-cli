import os
import signal
import time

from .alive import alive
from .errors import QemuCliError
from .pidfile import pidfile
from .running_pid import running_pid
from .stop_result import StopResult


def stop_vm(name: str, timeout: float = 10.0) -> StopResult:
    pid = running_pid(name)
    if not pid:
        raise QemuCliError(f"vm '{name}' is not running")
    os.kill(pid, signal.SIGTERM)
    force_killed = True
    for _ in range(int(timeout * 10)):
        if not alive(pid):
            force_killed = False
            break
        time.sleep(0.1)
    if force_killed:
        os.kill(pid, signal.SIGKILL)
    try:
        os.unlink(pidfile(name))
    except OSError:
        pass
    return StopResult(force_killed=force_killed)
