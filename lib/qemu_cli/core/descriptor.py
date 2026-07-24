import dataclasses
from typing import List


@dataclasses.dataclass
class VmDescriptor:
    name: str
    cmdline: str
    workdir: str
    created: str
    pre_hook: List[str] = dataclasses.field(default_factory=list)
    post_hook: List[str] = dataclasses.field(default_factory=list)
