from typing import Optional

from .debug_log import trace
from .pidfile import pidfile


@trace
def read_pid(name: str) -> Optional[int]:
    try:
        with open(pidfile(name)) as fh:
            return int(fh.read().strip())
    except (OSError, ValueError):
        return None
