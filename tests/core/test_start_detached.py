import importlib
import os
import signal

import pytest

from qemu_cli.core.errors import QemuCliError
from qemu_cli.core.pidfile import pidfile

start_detached_module = importlib.import_module("qemu_cli.core.start_detached")


def test_no_post_hooks_spawns_detached_and_writes_pidfile(isolated_dirs, tmp_path):
    # In production, run_vm() always creates STATE_DIR before calling
    # start_detached(); do the same here since we're calling it directly.
    os.makedirs(isolated_dirs.state_dir, exist_ok=True)
    pid = start_detached_module.start_detached("vm", ["sleep", "5"], str(tmp_path), [])
    try:
        assert os.path.isfile(pidfile("vm"))
        with open(pidfile("vm")) as fh:
            assert int(fh.read()) == pid
        os.kill(pid, 0)  # still alive; raises if not
    finally:
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)


def test_no_post_hooks_binary_not_found_raises(isolated_dirs, tmp_path):
    with pytest.raises(QemuCliError, match="binary not found"):
        start_detached_module.start_detached("vm", ["/no/such/binary"], str(tmp_path), [])


def _spy_on_fork(monkeypatch, captured):
    real_fork = os.fork

    def spy_fork():
        pid = real_fork()
        if pid != 0:
            captured["monitor_pid"] = pid
        return pid

    monkeypatch.setattr(start_detached_module.os, "fork", spy_fork)


def test_with_post_hooks_runs_them_after_the_process_exits(isolated_dirs, tmp_path, monkeypatch):
    os.makedirs(isolated_dirs.state_dir, exist_ok=True)
    marker = tmp_path / "post-hook-ran"
    captured = {}
    _spy_on_fork(monkeypatch, captured)

    pid = start_detached_module.start_detached(
        "vm", ["true"], str(tmp_path), [f"touch {marker}"]
    )
    assert isinstance(pid, int)

    os.waitpid(captured["monitor_pid"], 0)  # wait for the monitor to finish its work

    assert marker.exists()
    assert not os.path.isfile(pidfile("vm"))
    assert os.path.isfile(os.path.join(isolated_dirs.state_dir, "vm.log"))


def test_with_post_hooks_binary_not_found_raises(isolated_dirs, tmp_path, monkeypatch):
    os.makedirs(isolated_dirs.state_dir, exist_ok=True)
    captured = {}
    _spy_on_fork(monkeypatch, captured)

    with pytest.raises(QemuCliError, match="binary not found"):
        start_detached_module.start_detached(
            "vm", ["/no/such/binary"], str(tmp_path), ["true"]
        )
    os.waitpid(captured["monitor_pid"], 0)
