import os
import subprocess

from .config import Logger, STATE_DIR
from .errors import QemuCliError
from .null_log import null_log
from .pidfile import pidfile
from .run_post_hooks import run_post_hooks


def start_detached(name, argv, workdir, post_hooks, log: Logger = null_log) -> int:
    """Start argv detached; if there are post-hooks, keep a background
    monitor process around to run them once the vm actually exits
    (whether it exits on its own or via `qemu stop`)."""
    if not post_hooks:
        try:
            proc = subprocess.Popen(
                argv, cwd=workdir, start_new_session=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError as e:
            raise QemuCliError(f"binary not found: {argv[0]}") from e
        with open(pidfile(name), "w") as fh:
            fh.write(str(proc.pid))
        return proc.pid

    r, w = os.pipe()
    monitor_pid = os.fork()
    if monitor_pid == 0:
        os.close(r)
        os.setsid()
        logfile = os.path.join(STATE_DIR, f"{name}.log")
        log_fd = os.open(logfile, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        os.dup2(log_fd, 1)
        os.dup2(log_fd, 2)
        os.close(log_fd)

        try:
            proc = subprocess.Popen(
                argv, cwd=workdir,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            os.write(w, b"ERR\n")
            os.close(w)
            os._exit(1)

        with open(pidfile(name), "w") as fh:
            fh.write(str(proc.pid))
        os.write(w, f"{proc.pid}\n".encode())
        os.close(w)

        proc.wait()
        run_post_hooks(post_hooks, log=log)
        try:
            os.unlink(pidfile(name))
        except OSError:
            pass
        os._exit(0)

    os.close(w)
    with os.fdopen(r) as fh:
        reply = fh.readline().strip()
    if not reply or reply == "ERR":
        raise QemuCliError(f"binary not found: {argv[0]}")
    return int(reply)
