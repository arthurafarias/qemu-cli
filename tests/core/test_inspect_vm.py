import importlib
import os

import pytest

from qemu_cli.core.errors import QemuCliError

inspect_vm_module = importlib.import_module("qemu_cli.core.inspect_vm")


def _write(isolated_dirs, name, body):
    os.makedirs(isolated_dirs.user_dir, exist_ok=True)
    with open(os.path.join(isolated_dirs.user_dir, f"{name}.ini"), "w") as fh:
        fh.write(body)


def test_missing_vm_raises(isolated_dirs):
    with pytest.raises(QemuCliError):
        inspect_vm_module.inspect_vm("nope")


def test_returns_full_detail(isolated_dirs, monkeypatch):
    body = (
        "[vm]\n"
        "cmdline = qemu-system-x86_64 -m 512\n"
        "created = 2024-01-01T00:00:00\n"
        "workdir = /tmp\n"
        "pre-hook = echo start\n"
        "post-hook = echo end\n"
    )
    _write(isolated_dirs, "vm", body)
    monkeypatch.setattr(inspect_vm_module, "running_pid", lambda name: 555)

    detail = inspect_vm_module.inspect_vm("vm")
    assert detail.name == "vm"
    assert detail.created == "2024-01-01T00:00:00"
    assert detail.workdir == "/tmp"
    assert detail.pid == 555
    assert detail.pre_hook == ["echo start"]
    assert detail.post_hook == ["echo end"]
    assert detail.cmdline == "qemu-system-x86_64 -m 512"


def test_defaults_when_optional_fields_are_absent(isolated_dirs, monkeypatch):
    _write(isolated_dirs, "vm", "[vm]\ncmdline = qemu-system-x86_64\n")
    monkeypatch.setattr(inspect_vm_module, "running_pid", lambda name: None)

    detail = inspect_vm_module.inspect_vm("vm")
    assert detail.created == "-"
    assert detail.workdir == "-"
    assert detail.pid is None
    assert detail.pre_hook == []
    assert detail.post_hook == []
