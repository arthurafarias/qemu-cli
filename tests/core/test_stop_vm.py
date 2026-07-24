import importlib
import os
import subprocess
import threading
import time

import pytest

from qemu_cli.core.errors import QemuCliError
from qemu_cli.core.pidfile import pidfile

stop_vm_module = importlib.import_module("qemu_cli.core.stop_vm")


def _write_pidfile(name, pid):
    path = pidfile(name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(str(pid))


def test_not_running_raises(isolated_dirs):
    with pytest.raises(QemuCliError, match="is not running"):
        stop_vm_module.stop_vm("nope")


def test_stops_a_cooperative_process_with_sigterm(isolated_dirs, monkeypatch):
    proc = subprocess.Popen(["sleep", "30"])
    # Our test process is proc's real parent, so until something calls
    # wait() on it, a terminated child lingers as a zombie -- and zombies
    # still answer os.kill(pid, 0), which would make stop_vm's alive-poll
    # loop think SIGTERM didn't work. Reap concurrently on a background
    # thread so the process table reflects termination promptly.
    reaper = threading.Thread(target=proc.wait, daemon=True)
    reaper.start()
    monkeypatch.setattr(stop_vm_module, "running_pid", lambda name: proc.pid)
    _write_pidfile("vm", proc.pid)
    try:
        result = stop_vm_module.stop_vm("vm", timeout=5.0)
    finally:
        if proc.poll() is None:
            proc.kill()
        reaper.join(5)
    assert result.force_killed is False
    assert not os.path.exists(pidfile("vm"))


def test_force_kills_a_process_that_ignores_sigterm(isolated_dirs, monkeypatch):
    proc = subprocess.Popen(["sh", "-c", "trap '' TERM; sleep 30"])
    time.sleep(0.2)  # give the trap time to install
    monkeypatch.setattr(stop_vm_module, "running_pid", lambda name: proc.pid)
    _write_pidfile("vm", proc.pid)
    try:
        result = stop_vm_module.stop_vm("vm", timeout=0.3)
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait()
    assert result.force_killed is True
    assert not os.path.exists(pidfile("vm"))
