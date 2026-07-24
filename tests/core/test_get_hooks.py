from qemu_cli.core.get_hooks import get_hooks


def test_empty_when_key_missing():
    assert get_hooks({}, "pre-hook") == []


def test_empty_when_value_is_blank():
    assert get_hooks({"pre-hook": ""}, "pre-hook") == []


def test_single_line():
    assert get_hooks({"pre-hook": "echo hi"}, "pre-hook") == ["echo hi"]


def test_multiple_lines_are_stripped_and_blank_lines_dropped():
    raw = "echo one\n  echo two  \n\n   \necho three"
    assert get_hooks({"pre-hook": raw}, "pre-hook") == ["echo one", "echo two", "echo three"]


def test_reads_the_requested_key_only():
    vm = {"pre-hook": "echo pre", "post-hook": "echo post"}
    assert get_hooks(vm, "post-hook") == ["echo post"]


def test_works_with_configparser_section(tmp_path):
    import configparser

    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read_string("[vm]\npre-hook = echo a\n    echo b\n")
    assert get_hooks(cfg["vm"], "pre-hook") == ["echo a", "echo b"]
