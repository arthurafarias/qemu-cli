import dataclasses
import os
import shlex
from typing import List, Optional

from .debug_log import trace
from .vm_descriptor import VirtualMachineDescriptor
from .errors import QemuCLIError
from .serialization import deserialize_descriptor, serialize_descriptor
from .stores import stores
from .write_store import write_store


class VirtualMachineManager:
    """Persists and retrieves VirtualMachineDescriptors. Owns the on-disk vm definition
    store; knows nothing about running qemu processes."""

    @trace
    def path_for(self, name: str) -> Optional[str]:
        for d in stores():
            p = os.path.join(d, f"{name}.ini")
            if os.path.isfile(p):
                return p
        return None

    @trace
    def create(self, descriptor: VirtualMachineDescriptor, force: bool = False) -> str:
        if not descriptor.name or "/" in descriptor.name:
            raise QemuCLIError("invalid vm name")
        if self.path_for(descriptor.name) and not force:
            raise QemuCLIError(
                f"vm '{descriptor.name}' already exists (use -f to overwrite)")
        cmdline = descriptor.cmdline.strip()
        if not cmdline:
            raise QemuCLIError("empty --cmdline")
        try:
            argv = shlex.split(cmdline)
        except ValueError as e:
            raise QemuCLIError(f"cannot parse cmdline: {e}") from e
        if not argv:
            raise QemuCLIError("empty cmdline")

        descriptor = dataclasses.replace(descriptor, cmdline=cmdline)
        dest = os.path.join(write_store(), f"{descriptor.name}.ini")
        with open(dest, "w") as fh:
            fh.write(serialize_descriptor(descriptor))
        return dest

    @trace
    def load(self, name: str) -> VirtualMachineDescriptor:
        p = self.path_for(name)
        if not p:
            raise QemuCLIError(f"no such vm: {name}")
        with open(p) as fh:
            descriptor = deserialize_descriptor(name, fh.read())
        if not descriptor.cmdline:
            raise QemuCLIError(f"corrupt definition: {p}")
        return descriptor

    @trace
    def list(self) -> List[VirtualMachineDescriptor]:
        out = []
        for name, path in self._discover().items():
            with open(path) as fh:
                out.append(deserialize_descriptor(name, fh.read()))
        return out

    @trace
    def remove(self, name: str) -> str:
        p = self.path_for(name)
        if not p:
            raise QemuCLIError(f"no such vm: {name}")
        try:
            os.unlink(p)
        except PermissionError as e:
            raise QemuCLIError(f"permission denied removing {p} (try sudo)") from e
        return p

    def _discover(self) -> dict:
        """name -> path for every defined vm, merged across stores
        (priority order, first store wins on name collision)."""
        seen = {}
        for d in stores():
            if not os.path.isdir(d):
                continue
            for f in sorted(os.listdir(d)):
                if f.endswith(".ini"):
                    name = f[:-4]
                    seen.setdefault(name, os.path.join(d, f))
        return seen
