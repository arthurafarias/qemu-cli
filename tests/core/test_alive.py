import importlib
import os

alive_module = importlib.import_module("qemu_cli.core.alive")


def test_none_pid_is_not_alive():
    assert alive_module.alive(None) is False


def test_current_process_is_alive():
    # A real, guaranteed-alive pid, exercised without mocking os.kill.
    assert alive_module.alive(os.getpid()) is True


def test_alive_when_kill_succeeds(monkeypatch):
    monkeypatch.setattr(alive_module.os, "kill", lambda pid, sig: None)
    assert alive_module.alive(123) is True


def test_not_alive_on_process_lookup_error(monkeypatch):
    def fake_kill(pid, sig):
        raise ProcessLookupError

    monkeypatch.setattr(alive_module.os, "kill", fake_kill)
    assert alive_module.alive(123) is False


def test_alive_on_permission_error(monkeypatch):
    # We can't signal it, but PermissionError means it exists under another uid.
    def fake_kill(pid, sig):
        raise PermissionError

    monkeypatch.setattr(alive_module.os, "kill", fake_kill)
    assert alive_module.alive(123) is True
