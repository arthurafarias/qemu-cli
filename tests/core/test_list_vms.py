import importlib
import os

list_vms_module = importlib.import_module("qemu_cli.core.list_vms")


def _write(directory, name, cmdline):
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, f"{name}.ini"), "w") as fh:
        fh.write(f"[vm]\ncmdline = {cmdline}\n")


def test_empty_when_no_vms_defined(isolated_dirs):
    assert list_vms_module.list_vms() == []


def test_extracts_binary_basename_from_cmdline(isolated_dirs, monkeypatch):
    _write(isolated_dirs.user_dir, "vm", "/usr/bin/qemu-system-x86_64 -m 512")
    monkeypatch.setattr(list_vms_module, "running_pid", lambda name: None)
    entries = list_vms_module.list_vms()
    assert len(entries) == 1
    assert entries[0].binary == "qemu-system-x86_64"
    assert entries[0].running is False


def test_binary_is_question_mark_when_cmdline_missing(isolated_dirs, monkeypatch):
    os.makedirs(isolated_dirs.user_dir, exist_ok=True)
    with open(os.path.join(isolated_dirs.user_dir, "broken.ini"), "w") as fh:
        fh.write("[vm]\n")
    monkeypatch.setattr(list_vms_module, "running_pid", lambda name: None)
    entries = list_vms_module.list_vms()
    assert entries[0].binary == "?"


def test_running_flag_reflects_running_pid(isolated_dirs, monkeypatch):
    _write(isolated_dirs.user_dir, "vm", "qemu-system-x86_64")
    monkeypatch.setattr(list_vms_module, "running_pid", lambda name: 111)
    entries = list_vms_module.list_vms()
    assert entries[0].running is True


def test_lists_every_defined_vm(isolated_dirs, monkeypatch):
    _write(isolated_dirs.user_dir, "a", "qemu-system-x86_64")
    _write(isolated_dirs.user_dir, "b", "qemu-system-aarch64")
    monkeypatch.setattr(list_vms_module, "running_pid", lambda name: None)
    names = {e.name for e in list_vms_module.list_vms()}
    assert names == {"a", "b"}
