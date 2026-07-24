"""Default no-op logger used when a caller doesn't care about progress output."""

from .debug_log import trace


@trace
def null_log(_msg: str) -> None:
    pass
