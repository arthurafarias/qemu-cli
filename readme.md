# qemu-cli

A docker-style CLI for managing QEMU VM command lines. Instead of retyping
long `qemu-system-x86_64 ...` invocations, save them once as named VM
definitions and start/stop/inspect them like containers.

## Features

- Save a VM's full command line under a name; run it with `qemu run NAME`
- List defined VMs and see which ones are currently running
- Optional `pre-hook` / `post-hook` shell commands (e.g. set up/tear down a
  tap device) run automatically around VM start/stop
- Detached (`-d`) mode with PID tracking and log capture
- Definitions stored as plain INI files, readable/editable by hand

## Requirements

- Python 3
- QEMU (whichever `qemu-system-*` binary your VM definitions call)

## Installation

```sh
git clone https://github.com/arthurafarias/qemu-cli.git
ln -s "$(pwd)/qemu-cli/bin/qemu" ~/.local/bin/qemu
```

## Usage

Define a VM:

```sh
qemu vm create -n myvm --cmdline "qemu-system-x86_64 -m 2G -hda disk.img -nic user"
```

With hooks (e.g. to bring up a tap interface):

```sh
qemu vm create -n myvm \
  --cmdline "qemu-system-x86_64 -m 2G -hda disk.img -netdev tap,id=n0,ifname=tap0,script=no" \
  --pre-hook "ip tuntap add dev tap0 mode tap user $USER" \
  --pre-hook "ip link set dev tap0 up" \
  --post-hook "ip tuntap del dev tap0"
```

List and inspect:

```sh
qemu vm list          # all defined vms
qemu vm ps            # only running vms (also: qemu ps)
qemu vm inspect myvm  # full definition + status
```

Run and stop:

```sh
qemu run myvm             # foreground, blocks until qemu exits
qemu run -d myvm          # detached, prints the pid
qemu run myvm -- -cdrom install.iso   # extra args appended to the stored cmdline
qemu stop myvm             # SIGTERM, escalates to SIGKILL after a timeout
```

Remove a definition:

```sh
qemu vm remove myvm   # alias: qemu vm rm myvm
```

## Storage locations

VM definitions are INI files, one per VM:

- System store: `/etc/qemu-cli/vms` (used when writable, i.e. as root)
- User store: `$XDG_CONFIG_HOME/qemu-cli/vms` (defaults to `~/.config/qemu-cli/vms`)

Both are searched when looking up or listing VMs; the user store takes
precedence on name collisions. New definitions are written to whichever
store is preferred (system if writable, otherwise user).

Runtime state (PID files, and logs for detached VMs with post-hooks) lives
under `$XDG_STATE_HOME/qemu-cli/run` (defaults to `~/.local/state/qemu-cli/run`).

Override the system store location with the `QEMU_CLI_SYSTEM_DIR`
environment variable.

## VM definition format

```ini
[vm]
name = myvm
cmdline = qemu-system-x86_64 -m 2G -hda disk.img -nic user
workdir = /home/me/vms/myvm
created = 2026-07-24T12:00:00
pre-hook = ip tuntap add dev tap0 mode tap user me
    ip link set dev tap0 up
post-hook = ip tuntap del dev tap0
```

`pre-hook` and `post-hook` accept multiple commands as indented
continuation lines. A failing pre-hook aborts the run; a failing post-hook
only prints a warning.
