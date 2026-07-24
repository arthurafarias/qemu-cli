import pytest

from qemu_cli.core.errors import QemuCLIError
from qemu_cli.core.vm_descriptor import VirtualMachineDescriptor
from qemu_cli.core.qemu_version_check import (
    installed_qemu_version, verify_qemu_version, version_satisfies,
)


def _descriptor(cmdline="qemu-system-x86_64", qemu_version=""):
    return VirtualMachineDescriptor(
        name="vm", cmdline=cmdline, workdir="/tmp", created="-", qemu_version=qemu_version,
    )


# -- version_satisfies -------------------------------------------------

@pytest.mark.parametrize("actual,spec", [
    ("8.2.0", "8.2.0"),
    ("8.2.0", "8.2"),
    ("8.2", "8.2.0"),
    ("8.2.0", "==8.2.0"),
    ("8.2.0", ">=8.0"),
    ("8.2.0", ">=8.2.0"),
    ("8.2.0", "<=9.0"),
    ("9.0.0", ">8.2"),
    ("8.0.0", "<8.2"),
    ("8.2.0", "!=8.3"),
])
def test_version_satisfies_true_cases(actual, spec):
    assert version_satisfies(actual, spec) is True


@pytest.mark.parametrize("actual,spec", [
    ("8.1.0", "8.2.0"),
    ("8.1.0", ">=8.2"),
    ("9.0.0", "<=8.2"),
    ("8.2.0", ">8.2"),
    ("8.2.0", "<8.2"),
    ("8.2.0", "!=8.2.0"),
])
def test_version_satisfies_false_cases(actual, spec):
    assert version_satisfies(actual, spec) is False


def test_version_satisfies_invalid_spec_raises():
    with pytest.raises(QemuCLIError, match="invalid qemu-version spec"):
        version_satisfies("8.2.0", "not-a-version")


# -- installed_qemu_version ---------------------------------------------

def test_installed_qemu_version_parses_version_from_output(monkeypatch):
    import qemu_cli.core.qemu_version_check as mod

    class FakeResult:
        stdout = "QEMU emulator version 8.2.2 (Debian 1:8.2.2+ds-0ubuntu1)\n"

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: FakeResult())
    assert installed_qemu_version("qemu-system-x86_64") == "8.2.2"


def test_installed_qemu_version_binary_not_found_raises():
    with pytest.raises(QemuCLIError, match="binary not found"):
        installed_qemu_version("/no/such/binary")


def test_installed_qemu_version_unparsable_output_raises(monkeypatch):
    import qemu_cli.core.qemu_version_check as mod

    class FakeResult:
        stdout = "no version here"

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: FakeResult())
    with pytest.raises(QemuCLIError, match="cannot determine version"):
        installed_qemu_version("qemu-system-x86_64")


# -- verify_qemu_version ---------------------------------------------------

def test_verify_qemu_version_is_a_noop_when_unset(monkeypatch):
    import qemu_cli.core.qemu_version_check as mod

    monkeypatch.setattr(mod, "installed_qemu_version",
                         lambda binary: pytest.fail("should not be called"))
    verify_qemu_version(_descriptor(qemu_version=""))


def test_verify_qemu_version_passes_when_satisfied(monkeypatch):
    import qemu_cli.core.qemu_version_check as mod

    monkeypatch.setattr(mod, "installed_qemu_version", lambda binary: "8.2.0")
    verify_qemu_version(_descriptor(qemu_version=">=8.0"))


def test_verify_qemu_version_raises_when_not_satisfied(monkeypatch):
    import qemu_cli.core.qemu_version_check as mod

    monkeypatch.setattr(mod, "installed_qemu_version", lambda binary: "7.0.0")
    with pytest.raises(QemuCLIError, match="requires qemu >=8.0, found 7.0.0"):
        verify_qemu_version(_descriptor(qemu_version=">=8.0"))
