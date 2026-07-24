import logging

import pytest

from qemu_cli.core.debug_log import logger, trace


@trace
def add(a, b):
    return a + b


@trace
def boom():
    raise ValueError("bad")


def test_silent_by_default(caplog):
    caplog.clear()
    assert add(2, 3) == 5
    assert caplog.records == []


def test_logs_call_and_return_at_debug(caplog):
    caplog.set_level(logging.DEBUG, logger="qemu_cli.core")
    assert add(2, 3) == 5
    messages = [r.getMessage() for r in caplog.records]
    assert any("-> " in m and "add(2, 3)" in m for m in messages)
    assert any("<- " in m and "= 5" in m for m in messages)


def test_logs_kwargs_in_call_trace(caplog):
    caplog.set_level(logging.DEBUG, logger="qemu_cli.core")
    add(2, b=3)
    messages = [r.getMessage() for r in caplog.records]
    assert any("b=3" in m for m in messages)


def test_logs_exception_and_reraises(caplog):
    caplog.set_level(logging.DEBUG, logger="qemu_cli.core")
    with pytest.raises(ValueError, match="bad"):
        boom()
    messages = [r.getMessage() for r in caplog.records]
    assert any("!! " in m and "raised" in m for m in messages)


def test_preserves_wrapped_function_identity():
    assert add.__wrapped__ is not None
    assert add.__name__ == "add"


def test_logger_name_is_qemu_cli_core():
    assert logger.name == "qemu_cli.core"
