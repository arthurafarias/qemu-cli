import importlib
import os

write_store_module = importlib.import_module("qemu_cli.core.write_store")

_real_makedirs = os.makedirs


def test_prefers_system_dir_when_writable(isolated_dirs, monkeypatch):
    monkeypatch.setattr(write_store_module.os, "access", lambda path, mode: True)
    assert write_store_module.write_store() == isolated_dirs.system_dir
    assert os.path.isdir(isolated_dirs.system_dir)


def test_falls_back_to_user_dir_when_system_dir_not_writable(isolated_dirs, monkeypatch):
    monkeypatch.setattr(write_store_module.os, "access", lambda path, mode: False)
    assert write_store_module.write_store() == isolated_dirs.user_dir
    assert os.path.isdir(isolated_dirs.user_dir)


def test_falls_back_to_user_dir_when_system_dir_cannot_be_created(isolated_dirs, monkeypatch):
    def fake_makedirs(path, exist_ok=False):
        if path == isolated_dirs.system_dir:
            raise PermissionError("denied")
        return _real_makedirs(path, exist_ok=exist_ok)

    monkeypatch.setattr(write_store_module.os, "makedirs", fake_makedirs)
    assert write_store_module.write_store() == isolated_dirs.user_dir
    assert os.path.isdir(isolated_dirs.user_dir)
