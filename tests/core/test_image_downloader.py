import os

import pytest

from qemu_cli.core.errors import QemuCLIError
from qemu_cli.core.image_downloader import download_image


def test_raises_when_aria2c_is_not_installed(tmp_path, monkeypatch):
    import qemu_cli.core.image_downloader as mod

    monkeypatch.setattr(mod.shutil, "which", lambda name: None)
    with pytest.raises(QemuCLIError, match="aria2c not found"):
        download_image("https://example.com/disk.img", str(tmp_path))


def test_downloads_with_filename_returns_full_path(tmp_path, monkeypatch):
    import qemu_cli.core.image_downloader as mod

    calls = []
    monkeypatch.setattr(mod.shutil, "which", lambda name: "/usr/bin/aria2c")
    monkeypatch.setattr(mod.subprocess, "run", lambda cmd, **k: calls.append(cmd) or type("R", (), {"returncode": 0})())

    dest = download_image("magnet:?xt=urn:btih:abc", str(tmp_path), filename="disk.img")
    assert dest == os.path.join(str(tmp_path), "disk.img")
    assert calls[0][:3] == ["aria2c", "-d", str(tmp_path)]
    assert "magnet:?xt=urn:btih:abc" in calls[0]
    assert "-o" in calls[0] and "disk.img" in calls[0]


def test_downloads_without_filename_returns_dest_dir(tmp_path, monkeypatch):
    import qemu_cli.core.image_downloader as mod

    monkeypatch.setattr(mod.shutil, "which", lambda name: "/usr/bin/aria2c")
    monkeypatch.setattr(mod.subprocess, "run", lambda cmd, **k: type("R", (), {"returncode": 0})())

    dest = download_image("https://example.com/disk.img", str(tmp_path))
    assert dest == str(tmp_path)


def test_nonzero_exit_raises(tmp_path, monkeypatch):
    import qemu_cli.core.image_downloader as mod

    monkeypatch.setattr(mod.shutil, "which", lambda name: "/usr/bin/aria2c")
    monkeypatch.setattr(mod.subprocess, "run", lambda cmd, **k: type("R", (), {"returncode": 1})())

    with pytest.raises(QemuCLIError, match="download failed"):
        download_image("https://example.com/disk.img", str(tmp_path))


def test_creates_dest_dir_if_missing(tmp_path, monkeypatch):
    import qemu_cli.core.image_downloader as mod

    monkeypatch.setattr(mod.shutil, "which", lambda name: "/usr/bin/aria2c")
    monkeypatch.setattr(mod.subprocess, "run", lambda cmd, **k: type("R", (), {"returncode": 0})())

    dest_dir = str(tmp_path / "does" / "not" / "exist")
    download_image("https://example.com/disk.img", dest_dir)
    assert os.path.isdir(dest_dir)
