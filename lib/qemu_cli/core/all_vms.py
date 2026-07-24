import os

from .debug_log import trace
from .stores import stores


@trace
def all_vms() -> dict:
    seen = {}
    for d in stores():
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".ini"):
                name = f[:-4]
                seen.setdefault(name, os.path.join(d, f))
    return seen
