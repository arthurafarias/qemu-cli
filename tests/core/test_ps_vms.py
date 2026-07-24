import importlib
import os
import time

ps_vms_module = importlib.import_module("qemu_cli.core.ps_vms")


def _make_vm(isolated_dirs, name):
    os.makedirs(isolated_dirs.user_dir, exist_ok=True)
    with open(os.path.join(isolated_dirs.user_dir, f"{name}.ini"), "w") as fh:
        fh.write("[vm]\ncmdline = qemu-system-x86_64\n")


def test_no_vms_defined_returns_empty(isolated_dirs):
    assert ps_vms_module.ps_vms() == []


def test_skips_non_running_vms(isolated_dirs, monkeypatch):
    _make_vm(isolated_dirs, "stopped")
    monkeypatch.setattr(ps_vms_module, "running_pid", lambda name: None)
    assert ps_vms_module.ps_vms() == []


def test_includes_running_vm_with_computed_uptime(isolated_dirs, monkeypatch):
    _make_vm(isolated_dirs, "running")
    monkeypatch.setattr(ps_vms_module, "running_pid", lambda name: 4242)
    os.makedirs(isolated_dirs.state_dir, exist_ok=True)
    pidfile_path = os.path.join(isolated_dirs.state_dir, "running.pid")
    with open(pidfile_path, "w") as fh:
        fh.write("4242")
    started = time.time() - 3725  # 1h 02m 05s ago
    os.utime(pidfile_path, (started, started))

    rows = ps_vms_module.ps_vms()
    assert len(rows) == 1
    row = rows[0]
    assert row.name == "running"
    assert row.pid == 4242
    assert row.uptime == "1h02m"


def test_uptime_is_question_mark_when_pidfile_is_missing(isolated_dirs, monkeypatch):
    _make_vm(isolated_dirs, "ghost")
    monkeypatch.setattr(ps_vms_module, "running_pid", lambda name: 555)
    rows = ps_vms_module.ps_vms()
    assert rows[0].uptime == "?"
