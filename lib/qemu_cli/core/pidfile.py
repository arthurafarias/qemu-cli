import os

from .config import STATE_DIR


def pidfile(name: str) -> str:
    return os.path.join(STATE_DIR, f"{name}.pid")
