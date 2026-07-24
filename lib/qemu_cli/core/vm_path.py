import os
from typing import Optional

from .stores import stores


def vm_path(name: str) -> Optional[str]:
    for d in stores():
        p = os.path.join(d, f"{name}.ini")
        if os.path.isfile(p):
            return p
    return None
