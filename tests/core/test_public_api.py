"""Locks down qemu_cli.core's public surface: what's exported, and the
shape each export must have (dataclass vs. callable vs. traced function).
A change here should be a deliberate API decision, not an accident.
"""

import dataclasses

import qemu_cli.core as core
from qemu_cli.core.errors import QemuCliError

DATACLASS_EXPORTS = {"VmListEntry", "VmProcEntry", "VmDetail", "RunResult", "StopResult"}

FUNCTION_EXPORTS = {
    "stores", "write_store", "vm_path", "load_vm", "all_vms",
    "pidfile", "read_pid", "alive", "running_pid",
    "get_hooks", "run_pre_hooks", "run_post_hooks",
    "create_vm", "list_vms", "ps_vms", "inspect_vm", "remove_vm",
    "run_vm", "stop_vm",
}

CONSTANT_EXPORTS = {"STATE_DIR", "SYSTEM_DIR", "USER_DIR", "debug_logger"}

EXPECTED_EXPORTS = CONSTANT_EXPORTS | {"QemuCliError"} | DATACLASS_EXPORTS | FUNCTION_EXPORTS


def test_all_matches_expected_public_api():
    assert set(core.__all__) == EXPECTED_EXPORTS


def test_every_declared_export_is_importable():
    for name in core.__all__:
        assert hasattr(core, name), f"__all__ lists {name!r} but it isn't importable"


def test_error_type_is_the_documented_qemu_cli_error():
    assert core.QemuCliError is QemuCliError
    assert issubclass(core.QemuCliError, Exception)


def test_dataclass_exports_are_dataclasses():
    for name in DATACLASS_EXPORTS:
        assert dataclasses.is_dataclass(getattr(core, name)), f"{name} is not a dataclass"


def test_function_exports_are_callable():
    for name in FUNCTION_EXPORTS:
        assert callable(getattr(core, name)), f"{name} is not callable"


def test_every_public_function_is_traced():
    """The package promises every function logs via debug_log.trace;
    functools.wraps leaves a __wrapped__ breadcrumb we can check for."""
    for name in FUNCTION_EXPORTS:
        fn = getattr(core, name)
        assert hasattr(fn, "__wrapped__"), f"{name} is missing the @trace decorator"
