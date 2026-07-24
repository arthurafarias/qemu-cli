import os
import signal
import subprocess
import threading
import time

import pytest

from qemu_cli.core.errors import QemuCLIError
from qemu_cli.core.pidfile import pidfile
from qemu_cli.core.process_engine import ProcessEngine


def _write_pidfile(name, pid):
    path = pidfile(name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(str(pid))


# -- running_pid -------------------------------------------------------

def test_running_pid_returns_none_when_no_pidfile_exists(isolated_dirs):
    assert ProcessEngine().running_pid("nope") is None


def test_running_pid_returns_pid_when_process_is_alive(isolated_dirs):
    _write_pidfile("vm", os.getpid())
    assert ProcessEngine().running_pid("vm") == os.getpid()


def test_running_pid_cleans_up_a_stale_pidfile(isolated_dirs, monkeypatch):
    import qemu_cli.core.process_engine as process_engine_module

    _write_pidfile("vm", 99999)
    monkeypatch.setattr(process_engine_module, "alive", lambda pid: False)
    assert ProcessEngine().running_pid("vm") is None
    assert not os.path.exists(pidfile("vm"))


# -- write/clear pidfile, started_at ----------------------------------

def test_write_and_clear_pidfile(isolated_dirs):
    os.makedirs(isolated_dirs.state_dir, exist_ok=True)
    engine = ProcessEngine()
    engine.write_pidfile("vm", 4242)
    assert os.path.isfile(pidfile("vm"))
    with open(pidfile("vm")) as fh:
        assert fh.read() == "4242"
    engine.clear_pidfile("vm")
    assert not os.path.exists(pidfile("vm"))


def test_clear_pidfile_missing_file_does_not_raise(isolated_dirs):
    ProcessEngine().clear_pidfile("nope")


def test_started_at_returns_mtime_of_pidfile(isolated_dirs):
    os.makedirs(isolated_dirs.state_dir, exist_ok=True)
    engine = ProcessEngine()
    engine.write_pidfile("vm", os.getpid())
    assert engine.started_at("vm") == pytest.approx(os.stat(pidfile("vm")).st_mtime)


def test_started_at_returns_none_when_pidfile_is_missing(isolated_dirs):
    assert ProcessEngine().started_at("nope") is None


# -- spawn (foreground) -------------------------------------------------

def test_spawn_binary_not_found_raises(isolated_dirs, tmp_path):
    with pytest.raises(QemuCLIError, match="binary not found"):
        ProcessEngine().spawn(["/no/such/binary"], str(tmp_path))


def test_spawn_returns_a_running_popen(isolated_dirs, tmp_path):
    proc = ProcessEngine().spawn(["true"], str(tmp_path))
    assert proc.wait() == 0


# -- spawn_detached -----------------------------------------------------

def test_spawn_detached_spawns_and_writes_pidfile(isolated_dirs, tmp_path):
    os.makedirs(isolated_dirs.state_dir, exist_ok=True)
    pid = ProcessEngine().spawn_detached("vm", ["sleep", "5"], str(tmp_path))
    try:
        assert os.path.isfile(pidfile("vm"))
        with open(pidfile("vm")) as fh:
            assert int(fh.read()) == pid
        os.kill(pid, 0)  # still alive; raises if not
    finally:
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)


def test_spawn_detached_binary_not_found_raises(isolated_dirs, tmp_path):
    with pytest.raises(QemuCLIError, match="binary not found"):
        ProcessEngine().spawn_detached("vm", ["/no/such/binary"], str(tmp_path))


# -- spawn_detached_with_monitor -----------------------------------------

def _spy_on_fork(monkeypatch, captured):
    import qemu_cli.core.process_engine as process_engine_module

    real_fork = os.fork

    def spy_fork():
        pid = real_fork()
        if pid != 0:
            captured["monitor_pid"] = pid
        return pid

    monkeypatch.setattr(process_engine_module.os, "fork", spy_fork)


def test_spawn_detached_with_monitor_runs_on_exit_after_process_exits(
    isolated_dirs, tmp_path, monkeypatch
):
    os.makedirs(isolated_dirs.state_dir, exist_ok=True)
    marker = tmp_path / "on-exit-ran"
    captured = {}
    _spy_on_fork(monkeypatch, captured)

    pid = ProcessEngine().spawn_detached_with_monitor(
        "vm", ["true"], str(tmp_path), on_exit=lambda: marker.write_text("done"),
    )
    assert isinstance(pid, int)

    os.waitpid(captured["monitor_pid"], 0)  # wait for the monitor to finish its work

    assert marker.exists()
    assert not os.path.isfile(pidfile("vm"))
    assert os.path.isfile(os.path.join(isolated_dirs.state_dir, "vm.log"))


def test_spawn_detached_with_monitor_binary_not_found_raises(
    isolated_dirs, tmp_path, monkeypatch
):
    os.makedirs(isolated_dirs.state_dir, exist_ok=True)
    captured = {}
    _spy_on_fork(monkeypatch, captured)

    with pytest.raises(QemuCLIError, match="binary not found"):
        ProcessEngine().spawn_detached_with_monitor(
            "vm", ["/no/such/binary"], str(tmp_path), on_exit=lambda: None,
        )
    os.waitpid(captured["monitor_pid"], 0)


# -- terminate -----------------------------------------------------------

def test_terminate_stops_a_cooperative_process_with_sigterm(isolated_dirs):
    proc = subprocess.Popen(["sleep", "30"])
    # Our test process is proc's real parent, so until something calls
    # wait() on it, a terminated child lingers as a zombie -- and zombies
    # still answer os.kill(pid, 0), which would make the alive-poll loop
    # think SIGTERM didn't work. Reap concurrently on a background thread
    # so the process table reflects termination promptly.
    reaper = threading.Thread(target=proc.wait, daemon=True)
    reaper.start()
    try:
        force_killed = ProcessEngine().terminate(proc.pid, timeout=5.0)
    finally:
        if proc.poll() is None:
            proc.kill()
        reaper.join(5)
    assert force_killed is False


def test_terminate_force_kills_a_process_that_ignores_sigterm(isolated_dirs):
    proc = subprocess.Popen(["sh", "-c", "trap '' TERM; sleep 30"])
    time.sleep(0.2)  # give the trap time to install
    try:
        force_killed = ProcessEngine().terminate(proc.pid, timeout=0.3)
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait()
    assert force_killed is True
