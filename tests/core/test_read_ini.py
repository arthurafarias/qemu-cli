from qemu_cli.core.read_ini import read_ini


def test_reads_an_existing_file(tmp_path):
    p = tmp_path / "vm.ini"
    p.write_text("[vm]\ncmdline = qemu-system-x86_64 -m 512\n")
    cfg = read_ini(str(p))
    assert cfg["vm"]["cmdline"] == "qemu-system-x86_64 -m 512"


def test_missing_file_yields_an_empty_config(tmp_path):
    cfg = read_ini(str(tmp_path / "missing.ini"))
    assert cfg.sections() == []


def test_interpolation_is_disabled(tmp_path):
    # BasicInterpolation (configparser's default) would collapse "%%" to
    # "%"; read_ini explicitly opts out so raw values like shell commands
    # containing "%" survive unmodified.
    p = tmp_path / "vm.ini"
    p.write_text("[vm]\ncmdline = qemu %% test\n")
    cfg = read_ini(str(p))
    assert cfg["vm"]["cmdline"] == "qemu %% test"
