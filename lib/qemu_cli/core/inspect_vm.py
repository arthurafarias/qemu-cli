from .debug_log import trace
from .get_hooks import get_hooks
from .load_vm import load_vm
from .running_pid import running_pid
from .vm_detail import VmDetail


@trace
def inspect_vm(name: str) -> VmDetail:
    vm, path = load_vm(name)
    return VmDetail(
        name=name,
        path=path,
        created=vm.get("created", "-"),
        workdir=vm.get("workdir", "-"),
        pid=running_pid(name),
        pre_hook=get_hooks(vm, "pre-hook"),
        post_hook=get_hooks(vm, "post-hook"),
        cmdline=vm["cmdline"],
    )
