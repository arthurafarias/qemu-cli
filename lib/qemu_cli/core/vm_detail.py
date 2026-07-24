import dataclasses
from typing import List, Optional


@dataclasses.dataclass
class VmDetail:
    name: str
    path: str
    created: str
    workdir: str
    pid: Optional[int]
    pre_hook: List[str]
    post_hook: List[str]
    cmdline: str
