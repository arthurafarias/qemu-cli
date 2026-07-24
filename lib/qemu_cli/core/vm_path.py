import os
from typing import Optional

from .debug_log import trace
from .stores import stores


@trace
def vm_path(name: str) -> Optional[str]:
    for d in stores():
        p = os.path.join(d, f"{name}.ini")
        if os.path.isfile(p):
            return p
    return None
