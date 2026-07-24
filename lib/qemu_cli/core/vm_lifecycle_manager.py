import os
import shlex
import time
from typing import Optional

from .config import Logger, STATE_DIR
from .debug_log import trace
from .vm_descriptor import VirtualMachineDescriptor
from .errors import QemuCliError
from .null_log import null_log
from .process_engine import ProcessEngine
from .run_post_hooks import run_post_hooks
from .run_pre_hooks import run_pre_hooks
from .run_result import RunResult
from .stop_result import StopResult


class VirtualMachineLifecycleManager:
    """Drives the qemu process lifecycle for a VirtualMachineDescriptor: run (foreground
    or detached), stop, and status/uptime queries. Built on ProcessEngine
    for the actual os/subprocess work."""

    def __init__(self, engine: Optional[ProcessEngine] = None):
        self.engine = engine or ProcessEngine()

    @trace
    def status(self, descriptor: VirtualMachineDescriptor) -> Optional[int]:
        return self.engine.running_pid(descriptor.name)

    @trace
    def is_running(self, name: str) -> bool:
        """Like `status`, but keyed by name — usable even when a
        descriptor can't be loaded (e.g. a corrupt/removed definition)."""
        return bool(self.engine.running_pid(name))

    @trace
    def uptime(self, descriptor: VirtualMachineDescriptor) -> str:
        started = self.engine.started_at(descriptor.name)
        if started is None:
            return "?"
        up = int(time.time() - started)
        return f"{up // 3600}h{(up % 3600) // 60:02d}m"

    @trace
    def run(self, descriptor: VirtualMachineDescriptor, extra_args=(), detach: bool = False,
            log: Logger = null_log) -> RunResult:
        if self.engine.running_pid(descriptor.name):
            raise QemuCliError(f"vm '{descriptor.name}' is already running")

        argv = shlex.split(descriptor.cmdline) + list(extra_args)
        argv = [os.path.expanduser(a) for a in argv]
        workdir = descriptor.workdir
        if not os.path.isdir(workdir):
            workdir = os.getcwd()

        os.makedirs(STATE_DIR, exist_ok=True)

        run_pre_hooks(descriptor.pre_hook, log=log)

        if detach:
            if descriptor.post_hook:
                pid = self.engine.spawn_detached_with_monitor(
                    descriptor.name, argv, workdir,
                    on_exit=lambda: run_post_hooks(descriptor.post_hook, log=log),
                )
            else:
                pid = self.engine.spawn_detached(descriptor.name, argv, workdir)
            return RunResult(detached=True, pid=pid)

        proc = self.engine.spawn(argv, workdir)
        self.engine.write_pidfile(descriptor.name, proc.pid)
        try:
            rc = proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            rc = proc.wait()
        finally:
            self.engine.clear_pidfile(descriptor.name)

        failures = run_post_hooks(descriptor.post_hook, log=log)
        return RunResult(detached=False, returncode=rc, post_hook_failures=failures)

    @trace
    def stop(self, descriptor: VirtualMachineDescriptor, timeout: float = 10.0) -> StopResult:
        pid = self.engine.running_pid(descriptor.name)
        if not pid:
            raise QemuCliError(f"vm '{descriptor.name}' is not running")
        force_killed = self.engine.terminate(pid, timeout=timeout)
        self.engine.clear_pidfile(descriptor.name)
        return StopResult(force_killed=force_killed)
