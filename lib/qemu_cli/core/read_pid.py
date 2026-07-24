from typing import Optional

from .pidfile import pidfile


def read_pid(name: str) -> Optional[int]:
    try:
        with open(pidfile(name)) as fh:
            return int(fh.read().strip())
    except (OSError, ValueError):
        return None
