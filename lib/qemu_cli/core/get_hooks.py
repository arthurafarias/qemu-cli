from typing import List

from .debug_log import trace


@trace
def get_hooks(vm, key: str) -> List[str]:
    """A hook config value as a list of individual shell commands."""
    raw = vm.get(key, "")
    return [line.strip() for line in raw.splitlines() if line.strip()]
