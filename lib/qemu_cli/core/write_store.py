import os

from .config import SYSTEM_DIR, USER_DIR


def write_store() -> str:
    """Preferred directory for writes: /etc if writable, else user config."""
    try:
        os.makedirs(SYSTEM_DIR, exist_ok=True)
        if os.access(SYSTEM_DIR, os.W_OK):
            return SYSTEM_DIR
    except PermissionError:
        pass
    os.makedirs(USER_DIR, exist_ok=True)
    return USER_DIR
