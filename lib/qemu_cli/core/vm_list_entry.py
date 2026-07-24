import dataclasses


@dataclasses.dataclass
class VirtualMachineListEntry:
    name: str
    path: str
    binary: str
    running: bool
