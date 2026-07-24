import os
import signal
import subprocess
import time
from typing import Callable, List, Optional

from .alive import alive
from .config import STATE_DIR
from .debug_log import trace
from .errors import QemuCliError
from .pidfile import pidfile
from .read_pid import read_pid


class ProcessEngine:
    """Thin wrapper around os/subprocess: spawning (foreground, detached,
    detached-with-exit-monitor), signaling, and pidfile bookkeeping. Knows
    nothing about vm definitions or hooks — just processes and pidfiles."""

    @trace
    def running_pid(self, name: str) -> Optional[int]:
        pid = read_pid(name)
        if alive(pid):
            return pid
        self._clear_pidfile(name)
        return None

    @trace
    def spawn(self, argv: List[str], cwd: str) -> subprocess.Popen:
        try:
            return subprocess.Popen(argv, cwd=cwd)
        except FileNotFoundError as e:
            raise QemuCliError(f"binary not found: {argv[0]}") from e

    @trace
    def spawn_detached(self, name: str, argv: List[str], cwd: str) -> int:
        try:
            proc = subprocess.Popen(
                argv, cwd=cwd, start_new_session=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError as e:
            raise QemuCliError(f"binary not found: {argv[0]}") from e
        self._write_pidfile(name, proc.pid)
        return proc.pid

    @trace
    def spawn_detached_with_monitor(
        self, name: str, argv: List[str], cwd: str, on_exit: Callable[[], None],
    ) -> int:
        """Start argv detached, keeping a background monitor process around
        to call `on_exit` once the vm actually exits (whether on its own or
        via `terminate`)."""
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
                    argv, cwd=cwd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            except FileNotFoundError:
                os.write(w, b"ERR\n")
                os.close(w)
                os._exit(1)

            self._write_pidfile(name, proc.pid)
            os.write(w, f"{proc.pid}\n".encode())
            os.close(w)

            proc.wait()
            on_exit()
            self._clear_pidfile(name)
            os._exit(0)

        os.close(w)
        with os.fdopen(r) as fh:
            reply = fh.readline().strip()
        if not reply or reply == "ERR":
            raise QemuCliError(f"binary not found: {argv[0]}")
        return int(reply)

    @trace
    def terminate(self, pid: int, timeout: float = 10.0) -> bool:
        """SIGTERM, then SIGKILL if it's still alive after `timeout` seconds.
        Returns True if a SIGKILL was needed."""
        os.kill(pid, signal.SIGTERM)
        force_killed = True
        for _ in range(int(timeout * 10)):
            if not alive(pid):
                force_killed = False
                break
            time.sleep(0.1)
        if force_killed:
            os.kill(pid, signal.SIGKILL)
        return force_killed

    @trace
    def write_pidfile(self, name: str, pid: int) -> None:
        self._write_pidfile(name, pid)

    @trace
    def clear_pidfile(self, name: str) -> None:
        self._clear_pidfile(name)

    @trace
    def started_at(self, name: str) -> Optional[float]:
        try:
            return os.stat(pidfile(name)).st_mtime
        except OSError:
            return None

    def _write_pidfile(self, name: str, pid: int) -> None:
        with open(pidfile(name), "w") as fh:
            fh.write(str(pid))

    def _clear_pidfile(self, name: str) -> None:
        try:
            os.unlink(pidfile(name))
        except OSError:
            pass
