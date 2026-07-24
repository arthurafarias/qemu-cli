import dataclasses


@dataclasses.dataclass
class VmProcEntry:
    name: str
    pid: int
    uptime: str
