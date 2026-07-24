import os

from qemu_cli.core.vm_path import vm_path


def _touch_ini(directory, name):
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{name}.ini")
    with open(path, "w") as fh:
        fh.write("[vm]\ncmdline = qemu-system-x86_64\n")
    return path


def test_returns_none_when_not_found(isolated_dirs):
    assert vm_path("missing") is None


def test_finds_definition_in_user_dir(isolated_dirs):
    path = _touch_ini(isolated_dirs.user_dir, "myvm")
    assert vm_path("myvm") == path


def test_finds_definition_in_system_dir(isolated_dirs):
    path = _touch_ini(isolated_dirs.system_dir, "myvm")
    assert vm_path("myvm") == path


def test_user_dir_takes_priority_over_system_dir(isolated_dirs):
    _touch_ini(isolated_dirs.system_dir, "myvm")
    user_path = _touch_ini(isolated_dirs.user_dir, "myvm")
    assert vm_path("myvm") == user_path
