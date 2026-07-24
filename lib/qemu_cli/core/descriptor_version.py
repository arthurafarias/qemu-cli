from .debug_log import trace
from .errors import QemuCLIError
from .vm_descriptor import CURRENT_DESCRIPTOR_VERSION, VirtualMachineDescriptor

SUPPORTED_DESCRIPTOR_VERSIONS = {CURRENT_DESCRIPTOR_VERSION}


@trace
def verify_descriptor_version(descriptor: VirtualMachineDescriptor) -> None:
    """Guard against a descriptor written in a format this qemu-cli doesn't
    understand (e.g. produced by a newer qemu-cli release)."""
    if descriptor.descriptor_version not in SUPPORTED_DESCRIPTOR_VERSIONS:
        supported = ", ".join(sorted(SUPPORTED_DESCRIPTOR_VERSIONS))
        raise QemuCLIError(
            f"unsupported descriptor-version: {descriptor.descriptor_version} "
            f"(this qemu-cli supports: {supported})"
        )
