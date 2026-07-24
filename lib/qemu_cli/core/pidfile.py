import os

from .config import STATE_DIR
from .debug_log import trace


@trace
def pidfile(name: str) -> str:
    return os.path.join(STATE_DIR, f"{name}.pid")
