import importlib
import os

from qemu_cli.core.pidfile import pidfile

running_pid_module = importlib.import_module("qemu_cli.core.running_pid")


def _write_pid_file(name, pid):
    path = pidfile(name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(str(pid))


def test_returns_none_when_no_pidfile_exists(isolated_dirs):
    assert running_pid_module.running_pid("nope") is None


def test_returns_pid_when_process_is_alive(isolated_dirs):
    _write_pid_file("vm", os.getpid())
    assert running_pid_module.running_pid("vm") == os.getpid()


def test_cleans_up_a_stale_pidfile(isolated_dirs, monkeypatch):
    _write_pid_file("vm", 99999)
    monkeypatch.setattr(running_pid_module, "alive", lambda pid: False)
    assert running_pid_module.running_pid("vm") is None
    assert not os.path.exists(pidfile("vm"))


def test_missing_pidfile_unlink_failure_is_swallowed(isolated_dirs, monkeypatch):
    monkeypatch.setattr(running_pid_module, "alive", lambda pid: False)
    # No pidfile was ever written, so the internal unlink() will hit ENOENT;
    # running_pid must not let that OSError escape.
    assert running_pid_module.running_pid("nope") is None
