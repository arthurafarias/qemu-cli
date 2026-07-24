import os
import shlex
import subprocess

from .config import Logger, STATE_DIR
from .debug_log import trace
from .errors import QemuCliError
from .get_hooks import get_hooks
from .load_vm import load_vm
from .null_log import null_log
from .pidfile import pidfile
from .run_post_hooks import run_post_hooks
from .run_pre_hooks import run_pre_hooks
from .run_result import RunResult
from .running_pid import running_pid
from .start_detached import start_detached


@trace
def run_vm(name: str, extra_args=(), detach=False, log: Logger = null_log) -> RunResult:
    vm, _ = load_vm(name)
    if running_pid(name):
        raise QemuCliError(f"vm '{name}' is already running")

    pre_hooks = get_hooks(vm, "pre-hook")
    post_hooks = get_hooks(vm, "post-hook")

    argv = shlex.split(vm["cmdline"]) + list(extra_args)
    argv = [os.path.expanduser(a) for a in argv]
    workdir = vm.get("workdir", os.getcwd())
    if not os.path.isdir(workdir):
        workdir = os.getcwd()

    os.makedirs(STATE_DIR, exist_ok=True)

    run_pre_hooks(pre_hooks, log=log)

    if detach:
        pid = start_detached(name, argv, workdir, post_hooks, log=log)
        return RunResult(detached=True, pid=pid)

    try:
        proc = subprocess.Popen(argv, cwd=workdir)
    except FileNotFoundError as e:
        raise QemuCliError(f"binary not found: {argv[0]}") from e

    with open(pidfile(name), "w") as fh:
        fh.write(str(proc.pid))

    try:
        rc = proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        rc = proc.wait()
    finally:
        try:
            os.unlink(pidfile(name))
        except OSError:
            pass

    failures = run_post_hooks(post_hooks, log=log)
    return RunResult(detached=False, returncode=rc, post_hook_failures=failures)
