import os

from qemu_cli.core.pidfile import pidfile


def test_path_is_under_state_dir(isolated_dirs):
    assert pidfile("myvm") == os.path.join(isolated_dirs.state_dir, "myvm.pid")


def test_path_varies_with_name(isolated_dirs):
    assert pidfile("a") != pidfile("b")
