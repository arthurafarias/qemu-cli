import dataclasses
from typing import List

CURRENT_DESCRIPTOR_VERSION = "1"


@dataclasses.dataclass
class VirtualMachineDescriptor:
    name: str
    cmdline: str
    workdir: str
    created: str
    qemu_version: str = ""
    descriptor_version: str = CURRENT_DESCRIPTOR_VERSION
    pre_hook: List[str] = dataclasses.field(default_factory=list)
    post_hook: List[str] = dataclasses.field(default_factory=list)
