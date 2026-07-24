import os

from qemu_cli.core.all_vms import all_vms


def _touch(directory, *names):
    os.makedirs(directory, exist_ok=True)
    for n in names:
        with open(os.path.join(directory, n), "w") as fh:
            fh.write("")


def test_empty_when_no_store_dirs_exist(isolated_dirs):
    assert all_vms() == {}


def test_ignores_non_ini_files(isolated_dirs):
    _touch(isolated_dirs.user_dir, "a.ini", "readme.txt", "b.ini.bak")
    assert set(all_vms().keys()) == {"a"}


def test_merges_across_stores(isolated_dirs):
    _touch(isolated_dirs.user_dir, "u.ini")
    _touch(isolated_dirs.system_dir, "s.ini")
    assert set(all_vms().keys()) == {"u", "s"}


def test_user_store_wins_on_name_collision(isolated_dirs):
    _touch(isolated_dirs.user_dir, "vm.ini")
    _touch(isolated_dirs.system_dir, "vm.ini")
    result = all_vms()
    assert result["vm"] == os.path.join(isolated_dirs.user_dir, "vm.ini")


def test_names_come_back_sorted_within_a_store(isolated_dirs):
    _touch(isolated_dirs.user_dir, "b.ini", "a.ini", "c.ini")
    assert list(all_vms().keys()) == ["a", "b", "c"]
