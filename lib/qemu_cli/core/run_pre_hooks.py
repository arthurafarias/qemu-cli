import subprocess
from typing import List

from .config import Logger
from .debug_log import trace
from .errors import QemuCliError
from .null_log import null_log


@trace
def run_pre_hooks(commands: List[str], log: Logger = null_log) -> None:
    for cmd in commands:
        log(f"[pre-hook] {cmd}")
        rc = subprocess.run(cmd, shell=True).returncode
        if rc != 0:
            raise QemuCliError(f"pre-hook failed (exit {rc}): {cmd}")
