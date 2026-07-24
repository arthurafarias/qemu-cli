import dataclasses


@dataclasses.dataclass
class VirtualMachineProcEntry:
    name: str
    pid: int
    uptime: str
