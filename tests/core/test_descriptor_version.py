import dataclasses

import pytest

from qemu_cli.core.errors import QemuCLIError
from qemu_cli.core.vm_descriptor import VirtualMachineDescriptor
from qemu_cli.core.descriptor_version import verify_descriptor_version


def _descriptor(**kwargs):
    kwargs.setdefault("name", "vm")
    kwargs.setdefault("cmdline", "true")
    kwargs.setdefault("workdir", "/tmp")
    kwargs.setdefault("created", "-")
    return VirtualMachineDescriptor(**kwargs)


def test_current_version_passes():
    verify_descriptor_version(_descriptor())


def test_unsupported_version_raises():
    d = dataclasses.replace(_descriptor(), descriptor_version="99")
    with pytest.raises(QemuCLIError, match="unsupported descriptor-version: 99"):
        verify_descriptor_version(d)
