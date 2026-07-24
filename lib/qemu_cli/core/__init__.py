"""Business logic for the qemu VM manager.

Nothing in this package prints to stdout/stderr or calls sys.exit — it
raises QemuCLIError for expected failures and returns plain data (dicts,
dataclasses) so it can be driven by a CLI, tests, or anything else.

Two services form the core API:

- `VirtualMachineManager` persists/retrieves `VirtualMachineDescriptor`s (vm definitions) to/from
  disk, via `serialize_descriptor`/`deserialize_descriptor`.
- `VirtualMachineLifecycleManager` drives the qemu process lifecycle for a
  `VirtualMachineDescriptor` — run (foreground/detached), stop, status/uptime — built on
  `ProcessEngine`, the thin os/subprocess wrapper.

Every class and function in this package is decorated with
`debug_log.trace`, which logs its call, return value, and any exception to
the "qemu_cli.core" logger at DEBUG level. Logging is silent by default (no
handler is configured); enable it with `qemu --debug ...` or by calling
`logging.basicConfig(level=logging.DEBUG)` yourself.
"""

from .config import STATE_DIR, SYSTEM_DIR, USER_DIR
from .debug_log import logger as debug_logger
from .errors import QemuCLIError
from .vm_descriptor import VirtualMachineDescriptor
from .vm_list_entry import VirtualMachineListEntry
from .vm_proc_entry import VirtualMachineProcEntry
from .run_result import RunResult
from .stop_result import StopResult

from .stores import stores
from .write_store import write_store
from .get_hooks import get_hooks
from .run_pre_hooks import run_pre_hooks
from .run_post_hooks import run_post_hooks

from .serialization import serialize_descriptor, deserialize_descriptor

from .vm_manager import VirtualMachineManager
from .process_engine import ProcessEngine
from .vm_lifecycle_manager import VirtualMachineLifecycleManager

__all__ = [
    "STATE_DIR", "SYSTEM_DIR", "USER_DIR",
    "debug_logger",
    "QemuCLIError",
    "VirtualMachineDescriptor", "VirtualMachineListEntry", "VirtualMachineProcEntry", "RunResult", "StopResult",
    "stores", "write_store",
    "get_hooks", "run_pre_hooks", "run_post_hooks",
    "serialize_descriptor", "deserialize_descriptor",
    "VirtualMachineManager", "ProcessEngine", "VirtualMachineLifecycleManager",
]
