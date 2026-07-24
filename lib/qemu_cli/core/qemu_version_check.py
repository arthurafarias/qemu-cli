import re
import shlex
import subprocess
from typing import Tuple

from .debug_log import trace
from .errors import QemuCLIError
from .vm_descriptor import VirtualMachineDescriptor

_OPERATORS = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
}

_SPEC_RE = re.compile(r"^(==|!=|>=|<=|>|<)?\s*(\d+(?:\.\d+)*)$")
_VERSION_RE = re.compile(r"(\d+(?:\.\d+)+)")


def _parse_version(text: str) -> Tuple[int, ...]:
    return tuple(int(p) for p in text.split("."))


def _pad(a: Tuple[int, ...], b: Tuple[int, ...]) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    length = max(len(a), len(b))
    return a + (0,) * (length - len(a)), b + (0,) * (length - len(b))


@trace
def version_satisfies(actual: str, spec: str) -> bool:
    """Check `actual` (e.g. "8.2.2") against `spec`. No operator prefix
    means an exact match (e.g. "8.2"); otherwise one of ==, !=, >=, <=, >, <
    (e.g. ">=8.0")."""
    match = _SPEC_RE.match(spec.strip())
    if not match:
        raise QemuCLIError(f"invalid qemu-version spec: {spec}")
    op, version_text = match.group(1) or "==", match.group(2)
    a, b = _pad(_parse_version(actual), _parse_version(version_text))
    return _OPERATORS[op](a, b)


@trace
def installed_qemu_version(binary: str) -> str:
    try:
        result = subprocess.run([binary, "--version"], capture_output=True, text=True)
    except FileNotFoundError as e:
        raise QemuCLIError(f"binary not found: {binary}") from e
    match = _VERSION_RE.search(result.stdout)
    if not match:
        raise QemuCLIError(f"cannot determine version of {binary}")
    return match.group(1)


@trace
def verify_qemu_version(descriptor: VirtualMachineDescriptor) -> None:
    """No-op if the descriptor doesn't pin a qemu-version."""
    if not descriptor.qemu_version:
        return
    binary = shlex.split(descriptor.cmdline)[0]
    actual = installed_qemu_version(binary)
    if not version_satisfies(actual, descriptor.qemu_version):
        raise QemuCLIError(
            f"vm '{descriptor.name}' requires qemu {descriptor.qemu_version}, found {actual}"
        )
