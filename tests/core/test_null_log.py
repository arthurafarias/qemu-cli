from qemu_cli.core.null_log import null_log


def test_returns_none_and_has_no_side_effects():
    assert null_log("anything") is None
    assert null_log("") is None
