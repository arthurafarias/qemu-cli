import os

import pytest

from qemu_cli.core.errors import QemuCliError
from qemu_cli.core.load_vm import load_vm


def _write_ini(isolated_dirs, name, body):
    os.makedirs(isolated_dirs.user_dir, exist_ok=True)
    path = os.path.join(isolated_dirs.user_dir, f"{name}.ini")
    with open(path, "w") as fh:
        fh.write(body)
    return path


def test_missing_vm_raises(isolated_dirs):
    with pytest.raises(QemuCliError, match="no such vm"):
        load_vm("nope")


def test_missing_vm_section_is_corrupt(isolated_dirs):
    _write_ini(isolated_dirs, "broken", "[other]\nfoo = bar\n")
    with pytest.raises(QemuCliError, match="corrupt definition"):
        load_vm("broken")


def test_missing_cmdline_key_is_corrupt(isolated_dirs):
    _write_ini(isolated_dirs, "broken", "[vm]\nname = broken\n")
    with pytest.raises(QemuCliError, match="corrupt definition"):
        load_vm("broken")


def test_loads_a_valid_definition(isolated_dirs):
    path = _write_ini(
        isolated_dirs, "vm", "[vm]\ncmdline = qemu-system-x86_64 -m 512\n"
    )
    section, returned_path = load_vm("vm")
    assert section["cmdline"] == "qemu-system-x86_64 -m 512"
    assert returned_path == path
