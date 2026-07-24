"""Shared fixtures for core unit tests.

The core package resolves its storage locations (SYSTEM_DIR, USER_DIR,
STATE_DIR) once, at import time, from qemu_cli.core.config. Several other
modules do `from .config import SYSTEM_DIR, ...`, which binds their own
private copy of the name into their own module namespace. Patching
qemu_cli.core.config itself therefore isn't enough -- each consuming module's
bound copy has to be patched too. The isolated_dirs fixture below does that,
pointing every module at its own tmp_path-backed sandbox so tests never touch
a real system/user config or state directory.
"""

import importlib
from types import SimpleNamespace

import pytest

_PATCHED_DIR_ATTRS = {
    "qemu_cli.core.stores": ("SYSTEM_DIR", "USER_DIR"),
    "qemu_cli.core.write_store": ("SYSTEM_DIR", "USER_DIR"),
    "qemu_cli.core.pidfile": ("STATE_DIR",),
    "qemu_cli.core.vm_lifecycle_manager": ("STATE_DIR",),
    "qemu_cli.core.process_engine": ("STATE_DIR",),
}


@pytest.fixture
def isolated_dirs(tmp_path, monkeypatch):
    """Point every core module at fresh, empty system/user/state dirs."""
    system_dir = str(tmp_path / "system" / "vms")
    user_dir = str(tmp_path / "user" / "vms")
    state_dir = str(tmp_path / "state" / "run")
    values = {"SYSTEM_DIR": system_dir, "USER_DIR": user_dir, "STATE_DIR": state_dir}

    for mod_name, attrs in _PATCHED_DIR_ATTRS.items():
        mod = importlib.import_module(mod_name)
        for attr in attrs:
            monkeypatch.setattr(mod, attr, values[attr])

    return SimpleNamespace(system_dir=system_dir, user_dir=user_dir, state_dir=state_dir)
