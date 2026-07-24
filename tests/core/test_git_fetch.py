import subprocess

import pytest

from qemu_cli.core.errors import QemuCLIError
from qemu_cli.core.git_fetch import fetch_descriptor


def _make_repo(tmp_path, files):
    repo = tmp_path / "origin"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo, check=True)
    for name, content in files.items():
        (repo / name).write_text(content)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    return str(repo)


def test_fetch_descriptor_returns_file_contents(isolated_dirs, tmp_path):
    url = _make_repo(tmp_path, {"vm.ini": "[vm]\ncmdline = true\n"})
    text = fetch_descriptor(url, "vm.ini")
    assert text == "[vm]\ncmdline = true\n"


def test_fetch_descriptor_missing_path_raises(isolated_dirs, tmp_path):
    url = _make_repo(tmp_path, {"vm.ini": "[vm]\ncmdline = true\n"})
    with pytest.raises(QemuCLIError, match="no such file in repo"):
        fetch_descriptor(url, "missing.ini")


def test_fetch_descriptor_bad_url_raises(isolated_dirs, tmp_path):
    with pytest.raises(QemuCLIError, match="git failed"):
        fetch_descriptor(str(tmp_path / "no-such-repo"), "vm.ini")


def test_fetch_descriptor_reuses_cache_on_second_call(isolated_dirs, tmp_path):
    url = _make_repo(tmp_path, {"vm.ini": "[vm]\ncmdline = true\n"})
    fetch_descriptor(url, "vm.ini")
    text = fetch_descriptor(url, "vm.ini")  # second call updates the cached clone
    assert text == "[vm]\ncmdline = true\n"


def test_fetch_descriptor_with_explicit_ref(isolated_dirs, tmp_path):
    url = _make_repo(tmp_path, {"vm.ini": "[vm]\ncmdline = true\n"})
    text = fetch_descriptor(url, "vm.ini", ref="main")
    assert text == "[vm]\ncmdline = true\n"
    text = fetch_descriptor(url, "vm.ini", ref="main")  # exercises the re-fetch path too
    assert text == "[vm]\ncmdline = true\n"


def test_fetch_descriptor_git_not_found_raises(isolated_dirs, tmp_path, monkeypatch):
    import qemu_cli.core.git_fetch as git_fetch_module

    def fake_run(argv, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr(git_fetch_module.subprocess, "run", fake_run)
    with pytest.raises(QemuCLIError, match="git not found"):
        fetch_descriptor(str(tmp_path), "vm.ini")
