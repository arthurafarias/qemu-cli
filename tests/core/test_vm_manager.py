import os

import pytest

from qemu_cli.core.vm_descriptor import VirtualMachineDescriptor
from qemu_cli.core.errors import QemuCLIError
from qemu_cli.core.vm_manager import VirtualMachineManager


def _touch_ini(directory, name, body="[vm]\ncmdline = qemu-system-x86_64\n"):
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{name}.ini")
    with open(path, "w") as fh:
        fh.write(body)
    return path


def _descriptor(name="vm", cmdline="qemu-system-x86_64", **kwargs):
    kwargs.setdefault("workdir", os.getcwd())
    kwargs.setdefault("created", "2024-01-01T00:00:00")
    return VirtualMachineDescriptor(name=name, cmdline=cmdline, **kwargs)


# -- path_for --------------------------------------------------------------

def test_path_for_returns_none_when_not_found(isolated_dirs):
    assert VirtualMachineManager().path_for("missing") is None


def test_path_for_finds_definition_in_user_dir(isolated_dirs):
    path = _touch_ini(isolated_dirs.user_dir, "myvm")
    assert VirtualMachineManager().path_for("myvm") == path


def test_path_for_finds_definition_in_system_dir(isolated_dirs):
    path = _touch_ini(isolated_dirs.system_dir, "myvm")
    assert VirtualMachineManager().path_for("myvm") == path


def test_path_for_user_dir_takes_priority_over_system_dir(isolated_dirs):
    _touch_ini(isolated_dirs.system_dir, "myvm")
    user_path = _touch_ini(isolated_dirs.user_dir, "myvm")
    assert VirtualMachineManager().path_for("myvm") == user_path


# -- create ------------------------------------------------------------

@pytest.mark.parametrize("name", ["", "a/b"])
def test_create_invalid_name_raises(isolated_dirs, name):
    with pytest.raises(QemuCLIError, match="invalid vm name"):
        VirtualMachineManager().create(_descriptor(name=name))


def test_create_empty_cmdline_raises(isolated_dirs):
    with pytest.raises(QemuCLIError, match="empty --cmdline"):
        VirtualMachineManager().create(_descriptor(cmdline="   "))


def test_create_unparsable_cmdline_raises(isolated_dirs):
    with pytest.raises(QemuCLIError, match="cannot parse cmdline"):
        VirtualMachineManager().create(_descriptor(cmdline="qemu 'unterminated"))


def test_create_writes_a_loadable_ini_file(isolated_dirs):
    manager = VirtualMachineManager()
    dest = manager.create(_descriptor(cmdline="qemu-system-x86_64 -m 512"))
    assert os.path.isfile(dest)
    loaded = manager.load("vm")
    assert loaded.name == "vm"
    assert loaded.cmdline == "qemu-system-x86_64 -m 512"
    assert loaded.workdir == os.getcwd()


def test_create_refuses_to_overwrite_without_force(isolated_dirs):
    manager = VirtualMachineManager()
    manager.create(_descriptor())
    with pytest.raises(QemuCLIError, match="already exists"):
        manager.create(_descriptor(cmdline="qemu-system-x86_64 -m 1024"))


def test_create_force_overwrites_existing_definition(isolated_dirs):
    manager = VirtualMachineManager()
    manager.create(_descriptor())
    manager.create(_descriptor(cmdline="qemu-system-x86_64 -m 2048"), force=True)
    assert manager.load("vm").cmdline == "qemu-system-x86_64 -m 2048"


def test_create_stores_pre_and_post_hooks(isolated_dirs):
    manager = VirtualMachineManager()
    manager.create(_descriptor(
        pre_hook=["ip tuntap add tap0", "ip link set tap0 up"],
        post_hook=["ip tuntap del tap0"],
    ))
    loaded = manager.load("vm")
    assert loaded.pre_hook == ["ip tuntap add tap0", "ip link set tap0 up"]
    assert loaded.post_hook == ["ip tuntap del tap0"]


# -- load ----------------------------------------------------------------

def test_load_missing_vm_raises(isolated_dirs):
    with pytest.raises(QemuCLIError, match="no such vm"):
        VirtualMachineManager().load("nope")


def test_load_missing_vm_section_is_corrupt(isolated_dirs):
    _touch_ini(isolated_dirs.user_dir, "broken", "[other]\nfoo = bar\n")
    with pytest.raises(QemuCLIError, match="corrupt definition"):
        VirtualMachineManager().load("broken")


def test_load_missing_cmdline_key_is_corrupt(isolated_dirs):
    _touch_ini(isolated_dirs.user_dir, "broken", "[vm]\nname = broken\n")
    with pytest.raises(QemuCLIError, match="corrupt definition"):
        VirtualMachineManager().load("broken")


def test_load_a_valid_definition(isolated_dirs):
    _touch_ini(isolated_dirs.user_dir, "vm", "[vm]\ncmdline = qemu-system-x86_64 -m 512\n")
    d = VirtualMachineManager().load("vm")
    assert d.cmdline == "qemu-system-x86_64 -m 512"


# -- list ------------------------------------------------------------------

def test_list_empty_when_no_vms_defined(isolated_dirs):
    assert VirtualMachineManager().list() == []


def test_list_ignores_non_ini_files(isolated_dirs):
    os.makedirs(isolated_dirs.user_dir, exist_ok=True)
    _touch_ini(isolated_dirs.user_dir, "a")
    with open(os.path.join(isolated_dirs.user_dir, "readme.txt"), "w") as fh:
        fh.write("")
    with open(os.path.join(isolated_dirs.user_dir, "b.ini.bak"), "w") as fh:
        fh.write("")
    assert {d.name for d in VirtualMachineManager().list()} == {"a"}


def test_list_merges_across_stores(isolated_dirs):
    _touch_ini(isolated_dirs.user_dir, "u")
    _touch_ini(isolated_dirs.system_dir, "s")
    assert {d.name for d in VirtualMachineManager().list()} == {"u", "s"}


def test_list_user_store_wins_on_name_collision(isolated_dirs):
    _touch_ini(isolated_dirs.system_dir, "vm", "[vm]\ncmdline = system-binary\n")
    _touch_ini(isolated_dirs.user_dir, "vm", "[vm]\ncmdline = user-binary\n")
    entries = VirtualMachineManager().list()
    assert len(entries) == 1
    assert entries[0].cmdline == "user-binary"


def test_list_tolerates_a_corrupt_definition(isolated_dirs):
    _touch_ini(isolated_dirs.user_dir, "broken", "[vm]\n")
    entries = VirtualMachineManager().list()
    assert entries[0].cmdline == ""


# -- remove ------------------------------------------------------------

def test_remove_missing_vm_raises(isolated_dirs):
    with pytest.raises(QemuCLIError, match="no such vm"):
        VirtualMachineManager().remove("nope")


def test_remove_deletes_the_definition_file(isolated_dirs):
    path = _touch_ini(isolated_dirs.user_dir, "vm")
    manager = VirtualMachineManager()
    result = manager.remove("vm")
    assert result == path
    assert not os.path.exists(path)


def test_remove_permission_denied_is_translated_to_qemu_cli_error(isolated_dirs, monkeypatch):
    import qemu_cli.core.vm_manager as vm_manager_module

    _touch_ini(isolated_dirs.user_dir, "vm")

    def fake_unlink(path):
        raise PermissionError("denied")

    monkeypatch.setattr(vm_manager_module.os, "unlink", fake_unlink)
    with pytest.raises(QemuCLIError, match="permission denied"):
        VirtualMachineManager().remove("vm")
