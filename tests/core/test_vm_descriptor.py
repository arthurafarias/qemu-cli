from qemu_cli.core.vm_descriptor import CURRENT_DESCRIPTOR_VERSION, VirtualMachineDescriptor


def test_fields():
    d = VirtualMachineDescriptor(
        name="vm", cmdline="qemu-system-x86_64", workdir="/tmp", created="2024-01-01",
        qemu_version=">=8.0", descriptor_version="1",
        pre_hook=["echo start"], post_hook=["echo end"],
    )
    assert d.name == "vm"
    assert d.cmdline == "qemu-system-x86_64"
    assert d.workdir == "/tmp"
    assert d.created == "2024-01-01"
    assert d.qemu_version == ">=8.0"
    assert d.descriptor_version == "1"
    assert d.pre_hook == ["echo start"]
    assert d.post_hook == ["echo end"]


def test_hook_defaults_are_empty_lists():
    d = VirtualMachineDescriptor(name="vm", cmdline="true", workdir="/tmp", created="2024-01-01")
    assert d.pre_hook == []
    assert d.post_hook == []


def test_qemu_version_defaults_to_empty_string():
    d = VirtualMachineDescriptor(name="vm", cmdline="true", workdir="/tmp", created="2024-01-01")
    assert d.qemu_version == ""


def test_descriptor_version_defaults_to_current_version():
    d = VirtualMachineDescriptor(name="vm", cmdline="true", workdir="/tmp", created="2024-01-01")
    assert d.descriptor_version == CURRENT_DESCRIPTOR_VERSION


def test_hook_default_is_not_shared_between_instances():
    a = VirtualMachineDescriptor(name="a", cmdline="true", workdir="/tmp", created="-")
    b = VirtualMachineDescriptor(name="b", cmdline="true", workdir="/tmp", created="-")
    a.pre_hook.append("echo hi")
    assert b.pre_hook == []
