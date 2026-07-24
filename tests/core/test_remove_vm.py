import importlib
import os

import pytest

from qemu_cli.core.errors import QemuCliError

remove_vm_module = importlib.import_module("qemu_cli.core.remove_vm")


def _write(isolated_dirs, name):
    os.makedirs(isolated_dirs.user_dir, exist_ok=True)
    path = os.path.join(isolated_dirs.user_dir, f"{name}.ini")
    with open(path, "w") as fh:
        fh.write("[vm]\ncmdline = qemu-system-x86_64\n")
    return path


def test_missing_vm_raises(isolated_dirs):
    with pytest.raises(QemuCliError, match="no such vm"):
        remove_vm_module.remove_vm("nope")


def test_removes_the_definition_file(isolated_dirs):
    path = _write(isolated_dirs, "vm")
    result = remove_vm_module.remove_vm("vm")
    assert result == path
    assert not os.path.exists(path)


def test_refuses_when_vm_is_running(isolated_dirs, monkeypatch):
    _write(isolated_dirs, "vm")
    monkeypatch.setattr(remove_vm_module, "running_pid", lambda name: 123)
    with pytest.raises(QemuCliError, match="is running"):
        remove_vm_module.remove_vm("vm")


def test_permission_denied_is_translated_to_qemu_cli_error(isolated_dirs, monkeypatch):
    _write(isolated_dirs, "vm")
    monkeypatch.setattr(remove_vm_module, "running_pid", lambda name: None)

    def fake_unlink(path):
        raise PermissionError("denied")

    monkeypatch.setattr(remove_vm_module.os, "unlink", fake_unlink)
    with pytest.raises(QemuCliError, match="permission denied"):
        remove_vm_module.remove_vm("vm")
