# Testing

## Setup

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

This installs the package in editable mode plus `pytest` and `pytest-cov`.

## Running the tests

```sh
pytest
```

`pyproject.toml` sets `testpaths = ["tests"]` and `addopts = "--cov=qemu_cli
--cov-report=term-missing"`, so a bare `pytest` from the repo root runs all
118+ tests (in well under a second) and prints a coverage summary.

Run a single file or test (still reports coverage for the whole package,
just exercised by the one test):

```sh
pytest tests/core/test_create_vm.py
pytest tests/core/test_create_vm.py::test_refuses_to_overwrite_without_force
```

For an HTML report you can browse locally:

```sh
pytest --cov-report=html
open htmlcov/index.html  # or xdg-open on Linux
```

## What's covered

Tests live under `tests/core/`, one file per `qemu_cli.core` module
(`test_create_vm.py`, `test_run_vm.py`, `test_stop_vm.py`, etc.), plus
`tests/core/test_public_api.py`, which checks the package's public surface.
There's no separate test file for `qemu_cli.cli` — the CLI layer is a thin
wrapper that just parses args and calls straight into `core`, so it's
exercised indirectly through the core tests.

## The `isolated_dirs` fixture

`tests/conftest.py` defines `isolated_dirs`, used by nearly every test.
`qemu_cli.core` resolves its system/user/state directories once at import
time, and several modules bind their own copy of those names via
`from .config import SYSTEM_DIR, ...`. The fixture monkeypatches each
consuming module's bound copy to point at fresh `tmp_path` sandboxes, so
tests never read or write your real `/etc/qemu-cli`, `~/.config/qemu-cli`,
or `~/.local/state/qemu-cli`.

Any test that touches VM storage or runtime state should take `isolated_dirs`
as an argument, even if it doesn't reference the returned object directly —
just requesting it is what triggers the patching.

## Adding a test

New tests should go in `tests/core/`, named `test_<module>.py` to match the
`qemu_cli.core` module under test, and follow the existing style: import the
function under test directly, use `isolated_dirs` for anything touching
storage, and use `pytest.raises(QemuCliError, match="...")` to assert on
error messages.

## Manual smoke test

To exercise the actual CLI end-to-end (not just unit tests):

```sh
pip install -e .
qemu vm create -n smoketest --cmdline "qemu-system-x86_64 -m 128 -nographic"
qemu vm list
qemu vm inspect smoketest
qemu vm remove smoketest
```

This does not require QEMU itself to be installed unless you actually
`qemu run` a VM.
