import os

import pytest

from qemu_cli.core.create_vm import create_vm
from qemu_cli.core.errors import QemuCliError
from qemu_cli.core.read_ini import read_ini


@pytest.mark.parametrize("name", ["", "a/b"])
def test_invalid_name_raises(isolated_dirs, name):
    with pytest.raises(QemuCliError, match="invalid vm name"):
        create_vm(name, "qemu-system-x86_64")


def test_empty_cmdline_raises(isolated_dirs):
    with pytest.raises(QemuCliError, match="empty --cmdline"):
        create_vm("vm", "   ")


def test_unparsable_cmdline_raises(isolated_dirs):
    with pytest.raises(QemuCliError, match="cannot parse cmdline"):
        create_vm("vm", "qemu 'unterminated")


def test_creates_an_ini_file_with_expected_fields(isolated_dirs):
    dest = create_vm("vm", "qemu-system-x86_64 -m 512")
    assert os.path.isfile(dest)
    cfg = read_ini(dest)
    assert cfg["vm"]["name"] == "vm"
    assert cfg["vm"]["cmdline"] == "qemu-system-x86_64 -m 512"
    assert cfg["vm"]["workdir"] == os.getcwd()
    assert "created" in cfg["vm"]


def test_refuses_to_overwrite_without_force(isolated_dirs):
    create_vm("vm", "qemu-system-x86_64")
    with pytest.raises(QemuCliError, match="already exists"):
        create_vm("vm", "qemu-system-x86_64 -m 1024")


def test_force_overwrites_existing_definition(isolated_dirs):
    create_vm("vm", "qemu-system-x86_64")
    dest = create_vm("vm", "qemu-system-x86_64 -m 2048", force=True)
    cfg = read_ini(dest)
    assert cfg["vm"]["cmdline"] == "qemu-system-x86_64 -m 2048"


def test_stores_pre_and_post_hooks_joined_by_newline(isolated_dirs):
    dest = create_vm(
        "vm", "qemu-system-x86_64",
        pre_hook=["ip tuntap add tap0", "ip link set tap0 up"],
        post_hook=["ip tuntap del tap0"],
    )
    cfg = read_ini(dest)
    assert cfg["vm"]["pre-hook"] == "ip tuntap add tap0\nip link set tap0 up"
    assert cfg["vm"]["post-hook"] == "ip tuntap del tap0"


def test_omits_hook_keys_when_none_given(isolated_dirs):
    dest = create_vm("vm", "qemu-system-x86_64")
    cfg = read_ini(dest)
    assert "pre-hook" not in cfg["vm"]
    assert "post-hook" not in cfg["vm"]


def test_returned_path_can_be_loaded_back_by_load_vm(isolated_dirs):
    from qemu_cli.core.load_vm import load_vm

    dest = create_vm("vm", "qemu-system-x86_64 -m 512")
    section, path = load_vm("vm")
    assert path == dest
    assert section["cmdline"] == "qemu-system-x86_64 -m 512"
