import importlib
import os

import pytest

from qemu_cli.core.errors import QemuCliError
from qemu_cli.core.pidfile import pidfile

run_vm_module = importlib.import_module("qemu_cli.core.run_vm")


def _write_vm(isolated_dirs, name, cmdline, workdir=None, pre_hook=None, post_hook=None):
    os.makedirs(isolated_dirs.user_dir, exist_ok=True)
    lines = ["[vm]", f"cmdline = {cmdline}"]
    if workdir is not None:
        lines.append(f"workdir = {workdir}")
    if pre_hook:
        lines.append("pre-hook = " + "\n    ".join(pre_hook))
    if post_hook:
        lines.append("post-hook = " + "\n    ".join(post_hook))
    with open(os.path.join(isolated_dirs.user_dir, f"{name}.ini"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


def test_already_running_raises(isolated_dirs, monkeypatch):
    _write_vm(isolated_dirs, "vm", "true")
    monkeypatch.setattr(run_vm_module, "running_pid", lambda name: 111)
    with pytest.raises(QemuCliError, match="already running"):
        run_vm_module.run_vm("vm")


def test_foreground_run_returns_the_exit_code(isolated_dirs, tmp_path):
    _write_vm(isolated_dirs, "vm", "sh -c 'exit 7'", workdir=str(tmp_path))
    result = run_vm_module.run_vm("vm")
    assert result.detached is False
    assert result.returncode == 7
    assert not os.path.isfile(pidfile("vm"))


def test_extra_args_are_appended_to_the_cmdline(isolated_dirs, tmp_path):
    marker = tmp_path / "extra-arg-marker"
    _write_vm(isolated_dirs, "vm", "touch", workdir=str(tmp_path))
    result = run_vm_module.run_vm("vm", extra_args=[str(marker)])
    assert result.returncode == 0
    assert marker.exists()


def test_binary_not_found_raises(isolated_dirs, tmp_path):
    _write_vm(isolated_dirs, "vm", "/no/such/binary", workdir=str(tmp_path))
    with pytest.raises(QemuCliError, match="binary not found"):
        run_vm_module.run_vm("vm")


def test_falls_back_to_cwd_when_workdir_is_missing(isolated_dirs, tmp_path):
    _write_vm(isolated_dirs, "vm", "true", workdir=str(tmp_path / "does-not-exist"))
    result = run_vm_module.run_vm("vm")
    assert result.returncode == 0


def test_pre_hook_failure_prevents_the_vm_from_starting(isolated_dirs, tmp_path):
    marker = tmp_path / "should-not-exist"
    _write_vm(isolated_dirs, "vm", f"touch {marker}", workdir=str(tmp_path), pre_hook=["exit 1"])
    with pytest.raises(QemuCliError, match="pre-hook failed"):
        run_vm_module.run_vm("vm")
    assert not marker.exists()


def test_post_hook_failures_are_collected_without_masking_returncode(isolated_dirs, tmp_path):
    _write_vm(isolated_dirs, "vm", "true", workdir=str(tmp_path), post_hook=["exit 9"])
    result = run_vm_module.run_vm("vm")
    assert result.returncode == 0
    assert result.post_hook_failures == [("exit 9", 9)]


def test_keyboard_interrupt_terminates_the_process_then_still_returns_a_result(
    isolated_dirs, tmp_path, monkeypatch
):
    _write_vm(isolated_dirs, "vm", "true", workdir=str(tmp_path))
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

    monkeypatch.setattr(run_vm_module.subprocess, "Popen", lambda *a, **k: FakeProc())
    result = run_vm_module.run_vm("vm")
    assert result.returncode == 0
    assert calls == {"wait": 2, "terminate": 1}


def test_pidfile_removal_failure_after_run_is_swallowed(isolated_dirs, tmp_path, monkeypatch):
    _write_vm(isolated_dirs, "vm", "true", workdir=str(tmp_path))

    def fake_unlink(path):
        raise OSError("boom")

    monkeypatch.setattr(run_vm_module.os, "unlink", fake_unlink)
    result = run_vm_module.run_vm("vm")
    assert result.returncode == 0


def test_detach_delegates_to_start_detached(isolated_dirs, tmp_path, monkeypatch):
    _write_vm(isolated_dirs, "vm", "true", workdir=str(tmp_path))
    monkeypatch.setattr(
        run_vm_module, "start_detached",
        lambda name, argv, workdir, post_hooks, log: 4242,
    )
    result = run_vm_module.run_vm("vm", detach=True)
    assert result.detached is True
    assert result.pid == 4242
