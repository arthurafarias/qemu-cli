"""Opt-in call tracing for the core package.

`logger` is a plain stdlib logger ("qemu_cli.core"); nothing in this module
configures handlers, so tracing is silent until a caller (the CLI, a test)
turns on logging for that name. The `trace` decorator, applied to every
function in core, logs each call's arguments, return value, and any
exception at DEBUG level.
"""

import functools
import logging

logger = logging.getLogger("qemu_cli.core")


def trace(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if logger.isEnabledFor(logging.DEBUG):
            call_args = ", ".join(
                [repr(a) for a in args] + [f"{k}={v!r}" for k, v in kwargs.items()]
            )
            logger.debug("-> %s(%s)", fn.__qualname__, call_args)
        try:
            result = fn(*args, **kwargs)
        except Exception as e:
            logger.debug("!! %s raised %r", fn.__qualname__, e)
            raise
        logger.debug("<- %s = %r", fn.__qualname__, result)
        return result
    return wrapper
