from qemu_cli.core.descriptor import VmDescriptor


def test_fields():
    d = VmDescriptor(
        name="vm", cmdline="qemu-system-x86_64", workdir="/tmp", created="2024-01-01",
        pre_hook=["echo start"], post_hook=["echo end"],
    )
    assert d.name == "vm"
    assert d.cmdline == "qemu-system-x86_64"
    assert d.workdir == "/tmp"
    assert d.created == "2024-01-01"
    assert d.pre_hook == ["echo start"]
    assert d.post_hook == ["echo end"]


def test_hook_defaults_are_empty_lists():
    d = VmDescriptor(name="vm", cmdline="true", workdir="/tmp", created="2024-01-01")
    assert d.pre_hook == []
    assert d.post_hook == []


def test_hook_default_is_not_shared_between_instances():
    a = VmDescriptor(name="a", cmdline="true", workdir="/tmp", created="-")
    b = VmDescriptor(name="b", cmdline="true", workdir="/tmp", created="-")
    a.pre_hook.append("echo hi")
    assert b.pre_hook == []
