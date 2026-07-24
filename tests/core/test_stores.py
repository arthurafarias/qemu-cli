import importlib

stores_module = importlib.import_module("qemu_cli.core.stores")


def test_returns_user_dir_before_system_dir(isolated_dirs):
    assert stores_module.stores() == [isolated_dirs.user_dir, isolated_dirs.system_dir]
