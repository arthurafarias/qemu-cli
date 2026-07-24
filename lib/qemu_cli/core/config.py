"""Paths and shared type aliases used across the core package."""

import os
from typing import Callable

SYSTEM_DIR = os.environ.get("QEMU_CLI_SYSTEM_DIR", "/etc/qemu-cli/vms")
USER_DIR = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
    "qemu-cli", "vms",
)
STATE_DIR = os.path.join(
    os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state")),
    "qemu-cli", "run",
)

Logger = Callable[[str], None]
