import pytest

from qemu_cli.core.errors import QemuCliError


def test_is_an_exception_carrying_a_message():
    err = QemuCliError("boom")
    assert isinstance(err, Exception)
    assert str(err) == "boom"


def test_can_be_raised_and_caught_by_type():
    with pytest.raises(QemuCliError, match="nope"):
        raise QemuCliError("nope")
