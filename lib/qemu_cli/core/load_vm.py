import configparser
from typing import Tuple

from .errors import QemuCliError
from .read_ini import read_ini
from .vm_path import vm_path


def load_vm(name: str) -> Tuple[configparser.SectionProxy, str]:
    p = vm_path(name)
    if not p:
        raise QemuCliError(f"no such vm: {name}")
    cfg = read_ini(p)
    if "vm" not in cfg or "cmdline" not in cfg["vm"]:
        raise QemuCliError(f"corrupt definition: {p}")
    return cfg["vm"], p
