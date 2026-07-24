from qemu_cli.core.run_post_hooks import run_post_hooks


def test_no_commands_returns_no_failures():
    assert run_post_hooks([]) == []


def test_successful_commands_produce_no_failures(tmp_path):
    marker = tmp_path / "marker"
    failures = run_post_hooks([f"touch {marker}"])
    assert failures == []
    assert marker.exists()


def test_failures_are_collected_but_execution_continues(tmp_path):
    marker = tmp_path / "marker"
    failures = run_post_hooks(["exit 2", f"touch {marker}", "exit 5"])
    assert failures == [("exit 2", 2), ("exit 5", 5)]
    assert marker.exists()


def test_logs_each_command():
    logged = []
    run_post_hooks(["exit 0", "exit 1"], log=logged.append)
    assert logged == ["[post-hook] exit 0", "[post-hook] exit 1"]
