import importlib
import os

from qemu_cli.core import config as config_module


def _reload():
    return importlib.reload(config_module)


def test_defaults_when_no_env_vars_set(monkeypatch):
    monkeypatch.delenv("QEMU_CLI_SYSTEM_DIR", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    try:
        cfg = _reload()
        assert cfg.SYSTEM_DIR == "/etc/qemu-cli/vms"
        assert cfg.USER_DIR == os.path.join(
            os.path.expanduser("~/.config"), "qemu-cli", "vms"
        )
        assert cfg.STATE_DIR == os.path.join(
            os.path.expanduser("~/.local/state"), "qemu-cli", "run"
        )
        assert cfg.CACHE_DIR == os.path.join(os.path.expanduser("~/.cache"), "qemu-cli")
        assert cfg.GIT_CACHE_DIR == os.path.join(
            os.path.expanduser("~/.cache"), "qemu-cli", "git"
        )
        assert cfg.IMAGE_CACHE_DIR == os.path.join(
            os.path.expanduser("~/.cache"), "qemu-cli", "images"
        )
    finally:
        _reload()


def test_env_vars_override_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("QEMU_CLI_SYSTEM_DIR", str(tmp_path / "sys"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    try:
        cfg = _reload()
        assert cfg.SYSTEM_DIR == str(tmp_path / "sys")
        assert cfg.USER_DIR == str(tmp_path / "cfg" / "qemu-cli" / "vms")
        assert cfg.STATE_DIR == str(tmp_path / "state" / "qemu-cli" / "run")
        assert cfg.CACHE_DIR == str(tmp_path / "cache" / "qemu-cli")
        assert cfg.GIT_CACHE_DIR == str(tmp_path / "cache" / "qemu-cli" / "git")
        assert cfg.IMAGE_CACHE_DIR == str(tmp_path / "cache" / "qemu-cli" / "images")
    finally:
        _reload()


def test_logger_type_alias_accepts_a_plain_callable():
    def sink(msg: str) -> None:
        pass

    # Logger is just `Callable[[str], None]` used for type hints; the real
    # contract is "callable that takes one string", exercised here directly.
    result: config_module.Logger = sink
    result("hello")
