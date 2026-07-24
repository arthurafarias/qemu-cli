import configparser
import io

from .debug_log import trace
from .descriptor import VmDescriptor
from .get_hooks import get_hooks


@trace
def serialize_descriptor(descriptor: VmDescriptor) -> str:
    """Render a VmDescriptor as INI text."""
    cfg = configparser.ConfigParser(interpolation=None)
    cfg["vm"] = {
        "name": descriptor.name,
        "cmdline": descriptor.cmdline,
        "workdir": descriptor.workdir,
        "created": descriptor.created,
    }
    if descriptor.pre_hook:
        cfg["vm"]["pre-hook"] = "\n".join(descriptor.pre_hook)
    if descriptor.post_hook:
        cfg["vm"]["post-hook"] = "\n".join(descriptor.post_hook)
    buf = io.StringIO()
    cfg.write(buf)
    return buf.getvalue()


@trace
def deserialize_descriptor(name: str, text: str) -> VmDescriptor:
    """Parse INI text (as produced by serialize_descriptor) into a VmDescriptor.

    Best-effort: a missing/corrupt 'vm' section or 'cmdline' key yields a
    descriptor with cmdline="" rather than raising, so callers that only
    need to enumerate/display vms (e.g. listing) aren't broken by one bad
    file. Callers that require a usable vm (run/inspect/...) should check
    `descriptor.cmdline` themselves.
    """
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read_string(text)
    vm = cfg["vm"] if cfg.has_section("vm") else {}
    return VmDescriptor(
        name=name,
        cmdline=vm.get("cmdline", ""),
        workdir=vm.get("workdir", "-"),
        created=vm.get("created", "-"),
        pre_hook=get_hooks(vm, "pre-hook"),
        post_hook=get_hooks(vm, "post-hook"),
    )
