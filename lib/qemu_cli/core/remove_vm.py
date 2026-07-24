import os

from .errors import QemuCliError
from .running_pid import running_pid
from .vm_path import vm_path


def remove_vm(name: str) -> str:
    p = vm_path(name)
    if not p:
        raise QemuCliError(f"no such vm: {name}")
    if running_pid(name):
        raise QemuCliError(f"vm '{name}' is running; stop it first")
    try:
        os.unlink(p)
    except PermissionError as e:
        raise QemuCliError(f"permission denied removing {p} (try sudo)") from e
    return p
