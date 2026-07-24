"""Business logic for the qemu VM manager.

Nothing in this package prints to stdout/stderr or calls sys.exit — it
raises QemuCliError for expected failures and returns plain data (dicts,
dataclasses) so it can be driven by a CLI, tests, or anything else.

Every class and every function lives in its own module; this file just
re-exports the public API so callers can keep writing `core.create_vm(...)`,
`core.QemuCliError`, etc.

Every function in this package is decorated with `debug_log.trace`, which
logs its call, return value, and any exception to the "qemu_cli.core"
logger at DEBUG level. Logging is silent by default (no handler is
configured); enable it with `qemu --debug ...` or by calling
`logging.basicConfig(level=logging.DEBUG)` yourself.
"""

from .config import STATE_DIR, SYSTEM_DIR, USER_DIR
from .debug_log import logger as debug_logger
from .errors import QemuCliError
from .vm_list_entry import VmListEntry
from .vm_proc_entry import VmProcEntry
from .vm_detail import VmDetail
from .run_result import RunResult
from .stop_result import StopResult

from .stores import stores
from .write_store import write_store
from .vm_path import vm_path
from .load_vm import load_vm
from .all_vms import all_vms

from .pidfile import pidfile
from .read_pid import read_pid
from .alive import alive
from .running_pid import running_pid

from .get_hooks import get_hooks
from .run_pre_hooks import run_pre_hooks
from .run_post_hooks import run_post_hooks

from .create_vm import create_vm
from .list_vms import list_vms
from .ps_vms import ps_vms
from .inspect_vm import inspect_vm
from .remove_vm import remove_vm

from .run_vm import run_vm
from .stop_vm import stop_vm

__all__ = [
    "STATE_DIR", "SYSTEM_DIR", "USER_DIR",
    "debug_logger",
    "QemuCliError",
    "VmListEntry", "VmProcEntry", "VmDetail", "RunResult", "StopResult",
    "stores", "write_store", "vm_path", "load_vm", "all_vms",
    "pidfile", "read_pid", "alive", "running_pid",
    "get_hooks", "run_pre_hooks", "run_post_hooks",
    "create_vm", "list_vms", "ps_vms", "inspect_vm", "remove_vm",
    "run_vm", "stop_vm",
]
