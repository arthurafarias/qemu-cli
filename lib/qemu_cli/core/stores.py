from typing import List

from .config import SYSTEM_DIR, USER_DIR
from .debug_log import trace


@trace
def stores() -> List[str]:
    """Directories searched for VM definitions (priority order)."""
    return [USER_DIR, SYSTEM_DIR]
