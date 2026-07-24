from qemu_cli.core.run_result import RunResult
from qemu_cli.core.stop_result import StopResult
from qemu_cli.core.vm_list_entry import VirtualMachineListEntry
from qemu_cli.core.vm_proc_entry import VirtualMachineProcEntry


def test_vm_list_entry_fields():
    e = VirtualMachineListEntry(name="n", path="p", binary="qemu-system-x86_64", running=True)
    assert (e.name, e.path, e.binary, e.running) == ("n", "p", "qemu-system-x86_64", True)


def test_vm_proc_entry_fields():
    e = VirtualMachineProcEntry(name="n", pid=123, uptime="1h00m")
    assert (e.name, e.pid, e.uptime) == ("n", 123, "1h00m")


def test_run_result_defaults():
    r = RunResult(detached=True)
    assert r.pid is None
    assert r.returncode is None
    assert r.post_hook_failures == []


def test_run_result_mutable_default_is_not_shared_between_instances():
    a = RunResult(detached=True)
    b = RunResult(detached=True)
    a.post_hook_failures.append(("cmd", 1))
    assert b.post_hook_failures == []


def test_stop_result_fields():
    assert StopResult(force_killed=True).force_killed is True
    assert StopResult(force_killed=False).force_killed is False
