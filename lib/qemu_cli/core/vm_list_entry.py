import dataclasses


@dataclasses.dataclass
class VmListEntry:
    name: str
    path: str
    binary: str
    running: bool
