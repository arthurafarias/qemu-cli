import importlib
import os

from qemu_cli.core.pidfile import pidfile

read_pid_module = importlib.import_module("qemu_cli.core.read_pid")


def _write_pid_file(name, contents):
    path = pidfile(name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(contents)


def test_missing_file_returns_none(isolated_dirs):
    assert read_pid_module.read_pid("nope") is None


def test_reads_a_valid_pid(isolated_dirs):
    _write_pid_file("vm", "4321")
    assert read_pid_module.read_pid("vm") == 4321


def test_strips_whitespace(isolated_dirs):
    _write_pid_file("vm", "  4321\n")
    assert read_pid_module.read_pid("vm") == 4321


def test_malformed_contents_return_none(isolated_dirs):
    _write_pid_file("vm", "not-a-number")
    assert read_pid_module.read_pid("vm") is None


def test_empty_file_returns_none(isolated_dirs):
    _write_pid_file("vm", "")
    assert read_pid_module.read_pid("vm") is None
