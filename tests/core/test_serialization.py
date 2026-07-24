import configparser

from qemu_cli.core.descriptor import VmDescriptor
from qemu_cli.core.serialization import deserialize_descriptor, serialize_descriptor


def _parse(text):
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read_string(text)
    return cfg


def test_serialize_produces_ini_with_expected_fields():
    d = VmDescriptor(name="vm", cmdline="qemu-system-x86_64 -m 512",
                      workdir="/tmp", created="2024-01-01T00:00:00")
    cfg = _parse(serialize_descriptor(d))
    assert cfg["vm"]["name"] == "vm"
    assert cfg["vm"]["cmdline"] == "qemu-system-x86_64 -m 512"
    assert cfg["vm"]["workdir"] == "/tmp"
    assert cfg["vm"]["created"] == "2024-01-01T00:00:00"


def test_serialize_joins_hooks_with_newline():
    d = VmDescriptor(
        name="vm", cmdline="true", workdir="/tmp", created="-",
        pre_hook=["ip tuntap add tap0", "ip link set tap0 up"],
        post_hook=["ip tuntap del tap0"],
    )
    cfg = _parse(serialize_descriptor(d))
    assert cfg["vm"]["pre-hook"] == "ip tuntap add tap0\nip link set tap0 up"
    assert cfg["vm"]["post-hook"] == "ip tuntap del tap0"


def test_serialize_omits_hook_keys_when_absent():
    d = VmDescriptor(name="vm", cmdline="true", workdir="/tmp", created="-")
    cfg = _parse(serialize_descriptor(d))
    assert "pre-hook" not in cfg["vm"]
    assert "post-hook" not in cfg["vm"]


def test_serialize_interpolation_is_disabled():
    # BasicInterpolation (configparser's default) would collapse "%%" to
    # "%"; serialize/deserialize explicitly opt out so raw values like
    # shell commands containing "%" survive unmodified.
    d = VmDescriptor(name="vm", cmdline="qemu %% test", workdir="/tmp", created="-")
    text = serialize_descriptor(d)
    assert deserialize_descriptor("vm", text).cmdline == "qemu %% test"


def test_deserialize_parses_a_valid_definition():
    text = "[vm]\ncmdline = qemu-system-x86_64 -m 512\n"
    d = deserialize_descriptor("vm", text)
    assert d.name == "vm"
    assert d.cmdline == "qemu-system-x86_64 -m 512"


def test_deserialize_missing_vm_section_yields_empty_cmdline():
    d = deserialize_descriptor("broken", "[other]\nfoo = bar\n")
    assert d.cmdline == ""


def test_deserialize_missing_cmdline_key_yields_empty_cmdline():
    d = deserialize_descriptor("broken", "[vm]\nname = broken\n")
    assert d.cmdline == ""


def test_deserialize_defaults_when_optional_fields_are_absent():
    d = deserialize_descriptor("vm", "[vm]\ncmdline = qemu-system-x86_64\n")
    assert d.created == "-"
    assert d.workdir == "-"
    assert d.pre_hook == []
    assert d.post_hook == []


def test_deserialize_parses_hooks_into_lists():
    text = "[vm]\ncmdline = true\npre-hook = echo start\npost-hook = echo end\n"
    d = deserialize_descriptor("vm", text)
    assert d.pre_hook == ["echo start"]
    assert d.post_hook == ["echo end"]


def test_round_trip_preserves_all_fields():
    original = VmDescriptor(
        name="vm", cmdline="qemu-system-x86_64 -m 512", workdir="/tmp",
        created="2024-01-01T00:00:00",
        pre_hook=["echo start"], post_hook=["echo end"],
    )
    restored = deserialize_descriptor("vm", serialize_descriptor(original))
    assert restored == original
