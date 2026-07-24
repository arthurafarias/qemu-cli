import pytest

from qemu_cli.core.errors import QemuCLIError


def test_is_an_exception_carrying_a_message():
    err = QemuCLIError("boom")
    assert isinstance(err, Exception)
    assert str(err) == "boom"


def test_can_be_raised_and_caught_by_type():
    with pytest.raises(QemuCLIError, match="nope"):
        raise QemuCLIError("nope")
