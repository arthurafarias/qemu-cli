import configparser
import datetime
import os
import shlex

from .debug_log import trace
from .errors import QemuCliError
from .vm_path import vm_path
from .write_store import write_store


@trace
def create_vm(name, cmdline, force=False, pre_hook=None, post_hook=None) -> str:
    if not name or "/" in name:
        raise QemuCliError("invalid vm name")
    if vm_path(name) and not force:
        raise QemuCliError(f"vm '{name}' already exists (use -f to overwrite)")
    cmdline = cmdline.strip()
    if not cmdline:
        raise QemuCliError("empty --cmdline")
    try:
        argv = shlex.split(cmdline)
    except ValueError as e:
        raise QemuCliError(f"cannot parse cmdline: {e}") from e
    if not argv:
        raise QemuCliError("empty cmdline")

    cfg = configparser.ConfigParser(interpolation=None)
    cfg["vm"] = {
        "name": name,
        "cmdline": cmdline,
        "workdir": os.getcwd(),
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    if pre_hook:
        cfg["vm"]["pre-hook"] = "\n".join(pre_hook)
    if post_hook:
        cfg["vm"]["post-hook"] = "\n".join(post_hook)
    dest = os.path.join(write_store(), f"{name}.ini")
    with open(dest, "w") as fh:
        cfg.write(fh)
    return dest
