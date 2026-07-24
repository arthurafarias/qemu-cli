"""Business logic for the qemu VM manager.

Nothing in this package prints to stdout/stderr or calls sys.exit — it
raises QemuCLIError for expected failures and returns plain data (dicts,
dataclasses) so it can be driven by a CLI, tests, or anything else.

Two services form the core API:

- `VirtualMachineManager` persists/retrieves `VirtualMachineDescriptor`s (vm definitions) to/from
  disk, via `serialize_descriptor`/`deserialize_descriptor`.
- `VirtualMachineLifecycleManager` drives the qemu process lifecycle for a
  `VirtualMachineDescriptor` — run (foreground/detached), stop, status/uptime — built on
  `ProcessEngine`, the thin os/subprocess wrapper. Before spawning it calls
  `verify_qemu_version` to check the descriptor's optional `qemu_version`
  spec (e.g. "8.2", ">=8.0") against the installed binary.

`fetch_descriptor` shallow-clones a git repo (cached under `GIT_CACHE_DIR`)
and returns the text of a descriptor file inside it, for `vm pull`.
`download_image` shells out to aria2c to fetch a disk/cd image from an
http(s) or magnet/torrent URI into a destination directory.

Descriptors also carry a `descriptor_version` (the on-disk format's own
schema version, separate from `qemu_version`); `verify_descriptor_version`
rejects one written in a format newer than this qemu-cli understands.

Every class and function in this package is decorated with
`debug_log.trace`, which logs its call, return value, and any exception to
the "qemu_cli.core" logger at DEBUG level. Logging is silent by default (no
handler is configured); enable it with `qemu --debug ...` or by calling
`logging.basicConfig(level=logging.DEBUG)` yourself.
"""

from .config import CACHE_DIR, GIT_CACHE_DIR, IMAGE_CACHE_DIR, STATE_DIR, SYSTEM_DIR, USER_DIR
from .debug_log import logger as debug_logger
from .errors import QemuCLIError
from .vm_descriptor import CURRENT_DESCRIPTOR_VERSION, VirtualMachineDescriptor
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
from .descriptor_version import verify_descriptor_version
from .git_fetch import fetch_descriptor
from .image_downloader import download_image
from .qemu_version_check import installed_qemu_version, verify_qemu_version, version_satisfies

from .vm_manager import VirtualMachineManager
from .process_engine import ProcessEngine
from .vm_lifecycle_manager import VirtualMachineLifecycleManager

__all__ = [
    "CACHE_DIR", "GIT_CACHE_DIR", "IMAGE_CACHE_DIR", "STATE_DIR", "SYSTEM_DIR", "USER_DIR",
    "CURRENT_DESCRIPTOR_VERSION",
    "debug_logger",
    "QemuCLIError",
    "VirtualMachineDescriptor", "VirtualMachineListEntry", "VirtualMachineProcEntry", "RunResult", "StopResult",
    "stores", "write_store",
    "get_hooks", "run_pre_hooks", "run_post_hooks",
    "serialize_descriptor", "deserialize_descriptor", "verify_descriptor_version",
    "fetch_descriptor", "download_image",
    "installed_qemu_version", "verify_qemu_version", "version_satisfies",
    "VirtualMachineManager", "ProcessEngine", "VirtualMachineLifecycleManager",
]
