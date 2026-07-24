import subprocess
from typing import List, Tuple

from .config import Logger
from .debug_log import trace
from .null_log import null_log


@trace
def run_post_hooks(commands: List[str], log: Logger = null_log) -> List[Tuple[str, int]]:
    failures = []
    for cmd in commands:
        log(f"[post-hook] {cmd}")
        rc = subprocess.run(cmd, shell=True).returncode
        if rc != 0:
            failures.append((cmd, rc))
    return failures
