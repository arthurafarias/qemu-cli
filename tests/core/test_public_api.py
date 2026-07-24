"""Locks down qemu_cli.core's public surface: what's exported, and the
shape each export must have (dataclass vs. traced function vs. class with
traced public methods). A change here should be a deliberate API decision,
not an accident.
"""

import dataclasses
import inspect

import qemu_cli.core as core
from qemu_cli.core.errors import QemuCliError

DATACLASS_EXPORTS = {"VirtualMachineDescriptor", "VirtualMachineListEntry", "VirtualMachineProcEntry", "RunResult", "StopResult"}

FUNCTION_EXPORTS = {
    "stores", "write_store",
    "get_hooks", "run_pre_hooks", "run_post_hooks",
    "serialize_descriptor", "deserialize_descriptor",
}

CLASS_EXPORTS = {"VirtualMachineManager", "ProcessEngine", "VirtualMachineLifecycleManager"}

CONSTANT_EXPORTS = {"STATE_DIR", "SYSTEM_DIR", "USER_DIR", "debug_logger"}

EXPECTED_EXPORTS = (
    CONSTANT_EXPORTS | {"QemuCliError"} | DATACLASS_EXPORTS | FUNCTION_EXPORTS | CLASS_EXPORTS
)


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


def test_class_exports_are_classes():
    for name in CLASS_EXPORTS:
        assert inspect.isclass(getattr(core, name)), f"{name} is not a class"


def test_every_public_class_method_is_traced():
    for cls_name in CLASS_EXPORTS:
        cls = getattr(core, cls_name)
        public_methods = [
            attr_name for attr_name, attr in vars(cls).items()
            if not attr_name.startswith("_") and inspect.isfunction(attr)
        ]
        assert public_methods, f"{cls_name} has no public methods"
        for attr_name in public_methods:
            fn = vars(cls)[attr_name]
            assert hasattr(fn, "__wrapped__"), (
                f"{cls_name}.{attr_name} is missing the @trace decorator"
            )
