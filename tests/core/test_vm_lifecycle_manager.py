import os
import subprocess
import threading
import time

import pytest

from qemu_cli.core.vm_descriptor import VirtualMachineDescriptor
from qemu_cli.core.errors import QemuCliError
from qemu_cli.core.pidfile import pidfile
from qemu_cli.core.vm_lifecycle_manager import VirtualMachineLifecycleManager


def _descriptor(name="vm", cmdline="true", workdir=None, pre_hook=None, post_hook=None):
    return VirtualMachineDescriptor(
        name=name, cmdline=cmdline, workdir=workdir or os.getcwd(), created="-",
        pre_hook=pre_hook or [], post_hook=post_hook or [],
    )


# -- run: guard rails ------------------------------------------------------

def test_run_already_running_raises(isolated_dirs, monkeypatch):
    lifecycle = VirtualMachineLifecycleManager()
    monkeypatch.setattr(lifecycle.engine, "running_pid", lambda name: 111)
    with pytest.raises(QemuCliError, match="already running"):
        lifecycle.run(_descriptor())


# -- run: foreground -------------------------------------------------------

def test_run_foreground_returns_the_exit_code(isolated_dirs, tmp_path):
    lifecycle = VirtualMachineLifecycleManager()
    result = lifecycle.run(_descriptor(cmdline="sh -c 'exit 7'", workdir=str(tmp_path)))
    assert result.detached is False
    assert result.returncode == 7
    assert not os.path.isfile(pidfile("vm"))


def test_run_extra_args_are_appended_to_the_cmdline(isolated_dirs, tmp_path):
    marker = tmp_path / "extra-arg-marker"
    lifecycle = VirtualMachineLifecycleManager()
    result = lifecycle.run(
        _descriptor(cmdline="touch", workdir=str(tmp_path)), extra_args=[str(marker)],
    )
    assert result.returncode == 0
    assert marker.exists()


def test_run_binary_not_found_raises(isolated_dirs, tmp_path):
    lifecycle = VirtualMachineLifecycleManager()
    with pytest.raises(QemuCliError, match="binary not found"):
        lifecycle.run(_descriptor(cmdline="/no/such/binary", workdir=str(tmp_path)))


def test_run_falls_back_to_cwd_when_workdir_is_missing(isolated_dirs, tmp_path):
    lifecycle = VirtualMachineLifecycleManager()
    result = lifecycle.run(_descriptor(workdir=str(tmp_path / "does-not-exist")))
    assert result.returncode == 0


def test_run_pre_hook_failure_prevents_the_vm_from_starting(isolated_dirs, tmp_path):
    marker = tmp_path / "should-not-exist"
    lifecycle = VirtualMachineLifecycleManager()
    with pytest.raises(QemuCliError, match="pre-hook failed"):
        lifecycle.run(_descriptor(
            cmdline=f"touch {marker}", workdir=str(tmp_path), pre_hook=["exit 1"],
        ))
    assert not marker.exists()


def test_run_post_hook_failures_are_collected_without_masking_returncode(isolated_dirs, tmp_path):
    lifecycle = VirtualMachineLifecycleManager()
    result = lifecycle.run(_descriptor(workdir=str(tmp_path), post_hook=["exit 9"]))
    assert result.returncode == 0
    assert result.post_hook_failures == [("exit 9", 9)]


def test_run_keyboard_interrupt_terminates_the_process_then_still_returns_a_result(
    isolated_dirs, tmp_path, monkeypatch
):
    import qemu_cli.core.process_engine as process_engine_module

    calls = {"wait": 0, "terminate": 0}

    class FakeProc:
        pid = 12345

        def wait(self):
            calls["wait"] += 1
            if calls["wait"] == 1:
                raise KeyboardInterrupt
            return 0

        def terminate(self):
            calls["terminate"] += 1

    monkeypatch.setattr(process_engine_module.subprocess, "Popen", lambda *a, **k: FakeProc())
    lifecycle = VirtualMachineLifecycleManager()
    result = lifecycle.run(_descriptor(workdir=str(tmp_path)))
    assert result.returncode == 0
    assert calls == {"wait": 2, "terminate": 1}


# -- run: detach -------------------------------------------------------

def test_run_detach_without_post_hooks_uses_plain_spawn_detached(isolated_dirs, tmp_path, monkeypatch):
    lifecycle = VirtualMachineLifecycleManager()
    calls = []
    monkeypatch.setattr(lifecycle.engine, "spawn_detached",
                         lambda name, argv, cwd: calls.append((name, argv, cwd)) or 4242)
    monkeypatch.setattr(lifecycle.engine, "spawn_detached_with_monitor",
                         lambda *a, **k: pytest.fail("should not use the monitor path"))

    result = lifecycle.run(_descriptor(workdir=str(tmp_path)), detach=True)
    assert result.detached is True
    assert result.pid == 4242
    assert calls == [("vm", ["true"], str(tmp_path))]


def test_run_detach_with_post_hooks_uses_monitor(isolated_dirs, tmp_path, monkeypatch):
    lifecycle = VirtualMachineLifecycleManager()
    captured = {}

    def fake_monitor(name, argv, cwd, on_exit):
        captured["on_exit"] = on_exit
        return 4242

    monkeypatch.setattr(lifecycle.engine, "spawn_detached_with_monitor", fake_monitor)
    monkeypatch.setattr(lifecycle.engine, "spawn_detached",
                         lambda *a, **k: pytest.fail("should use the monitor path"))

    result = lifecycle.run(
        _descriptor(workdir=str(tmp_path), post_hook=["true"]), detach=True,
    )
    assert result.detached is True
    assert result.pid == 4242
    assert callable(captured["on_exit"])


# -- stop ------------------------------------------------------------------

def test_stop_not_running_raises(isolated_dirs):
    with pytest.raises(QemuCliError, match="is not running"):
        VirtualMachineLifecycleManager().stop(_descriptor())


def test_stop_stops_a_cooperative_process_with_sigterm(isolated_dirs, monkeypatch):
    lifecycle = VirtualMachineLifecycleManager()
    proc = subprocess.Popen(["sleep", "30"])
    # See test_process_engine.py for why this needs a concurrent reaper.
    reaper = threading.Thread(target=proc.wait, daemon=True)
    reaper.start()
    monkeypatch.setattr(lifecycle.engine, "running_pid", lambda name: proc.pid)
    os.makedirs(isolated_dirs.state_dir, exist_ok=True)
    lifecycle.engine.write_pidfile("vm", proc.pid)
    try:
        result = lifecycle.stop(_descriptor(), timeout=5.0)
    finally:
        if proc.poll() is None:
            proc.kill()
        reaper.join(5)
    assert result.force_killed is False
    assert not os.path.exists(pidfile("vm"))


def test_stop_force_kills_a_process_that_ignores_sigterm(isolated_dirs, monkeypatch):
    lifecycle = VirtualMachineLifecycleManager()
    proc = subprocess.Popen(["sh", "-c", "trap '' TERM; sleep 30"])
    time.sleep(0.2)  # give the trap time to install
    monkeypatch.setattr(lifecycle.engine, "running_pid", lambda name: proc.pid)
    os.makedirs(isolated_dirs.state_dir, exist_ok=True)
    lifecycle.engine.write_pidfile("vm", proc.pid)
    try:
        result = lifecycle.stop(_descriptor(), timeout=0.3)
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait()
    assert result.force_killed is True
    assert not os.path.exists(pidfile("vm"))


# -- status / uptime / is_running ------------------------------------------

def test_status_returns_pid_when_running(isolated_dirs, monkeypatch):
    lifecycle = VirtualMachineLifecycleManager()
    monkeypatch.setattr(lifecycle.engine, "running_pid", lambda name: 555)
    assert lifecycle.status(_descriptor()) == 555


def test_status_returns_none_when_not_running(isolated_dirs):
    assert VirtualMachineLifecycleManager().status(_descriptor()) is None


def test_is_running_reflects_status(isolated_dirs, monkeypatch):
    lifecycle = VirtualMachineLifecycleManager()
    monkeypatch.setattr(lifecycle.engine, "running_pid", lambda name: 555)
    assert lifecycle.is_running("vm") is True
    monkeypatch.setattr(lifecycle.engine, "running_pid", lambda name: None)
    assert lifecycle.is_running("vm") is False


def test_uptime_is_computed_from_the_pidfile_mtime(isolated_dirs):
    os.makedirs(isolated_dirs.state_dir, exist_ok=True)
    lifecycle = VirtualMachineLifecycleManager()
    lifecycle.engine.write_pidfile("vm", os.getpid())
    started = time.time() - 3725  # 1h 02m 05s ago
    os.utime(pidfile("vm"), (started, started))
    assert lifecycle.uptime(_descriptor()) == "1h02m"


def test_uptime_is_question_mark_when_pidfile_is_missing(isolated_dirs):
    assert VirtualMachineLifecycleManager().uptime(_descriptor()) == "?"
