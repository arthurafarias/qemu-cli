import dataclasses
from typing import List, Optional, Tuple


@dataclasses.dataclass
class RunResult:
    detached: bool
    pid: Optional[int] = None
    returncode: Optional[int] = None
    post_hook_failures: List[Tuple[str, int]] = dataclasses.field(default_factory=list)
