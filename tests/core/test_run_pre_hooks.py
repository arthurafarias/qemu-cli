import pytest

from qemu_cli.core.errors import QemuCLIError
from qemu_cli.core.run_pre_hooks import run_pre_hooks


def test_no_commands_is_a_noop():
    run_pre_hooks([])


def test_runs_each_command_and_logs_it(tmp_path):
    marker = tmp_path / "marker"
    logged = []
    run_pre_hooks([f"touch {marker}"], log=logged.append)
    assert marker.exists()
    assert logged == [f"[pre-hook] touch {marker}"]


def test_failing_command_raises_with_its_exit_code():
    with pytest.raises(QemuCLIError, match=r"exit 3"):
        run_pre_hooks(["exit 3"])


def test_stops_at_the_first_failure(tmp_path):
    marker = tmp_path / "marker"
    with pytest.raises(QemuCLIError):
        run_pre_hooks(["exit 1", f"touch {marker}"])
    assert not marker.exists()


def test_runs_commands_in_order(tmp_path):
    log_file = tmp_path / "order.log"
    run_pre_hooks([
        f"echo first >> {log_file}",
        f"echo second >> {log_file}",
    ])
    assert log_file.read_text().splitlines() == ["first", "second"]
