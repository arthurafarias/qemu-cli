"""qemu — docker-style CLI for managing QEMU VM command lines.

This module is a thin presentation layer: every command decorates a
function whose body parses/echoes and then calls straight into
qemu_cli.core's VirtualMachineManager (vm definition persistence) and
VirtualMachineLifecycleManager (qemu process lifecycle), which hold all the actual
business logic.
"""

import datetime
import functools
import logging
import os
import shlex

import click

from . import core

HELP_INTRO = """qemu — docker-style CLI for managing QEMU VM command lines.

VM definitions are stored as INI files. System store: /etc/qemu-cli/vms
(used when writable, i.e. root); otherwise falls back to
~/.config/qemu-cli/vms. Both are merged for lookup/list, user store wins.

A vm definition may set 'pre-hook' and 'post-hook': one or more shell
commands run before the vm starts / after it exits. Use indented
continuation lines for more than one command:

\b
  [vm]
  pre-hook = ip tuntap add dev tap0 mode tap user me
      ip link set dev tap0 up
  post-hook = ip tuntap del dev tap0
"""


def handle_errors(fn):
    """Turn a core.QemuCliError into an `Error: ...` message + exit 1."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except core.QemuCliError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)
    return wrapper


@click.group(help=HELP_INTRO)
@click.option("--debug", is_flag=True, envvar="QEMU_CLI_DEBUG",
              help="log every core function call to stderr")
def main(debug):
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(name)s %(message)s",
            datefmt="%H:%M:%S",
        )
        core.debug_logger.setLevel(logging.DEBUG)


@main.group("vm", help="manage vm definitions")
def vm_group():
    pass


@vm_group.command("create", help="define a new vm")
@click.option("-n", "--name", required=True)
@click.option("--cmdline", required=True, help="full qemu command line")
@click.option("-f", "--force", is_flag=True, help="overwrite")
@click.option("--pre-hook", "pre_hook", multiple=True, metavar="CMD",
              help="shell command to run before start (repeatable)")
@click.option("--post-hook", "post_hook", multiple=True, metavar="CMD",
              help="shell command to run after the vm exits (repeatable)")
@handle_errors
def vm_create(name, cmdline, force, pre_hook, post_hook):
    descriptor = core.VirtualMachineDescriptor(
        name=name,
        cmdline=cmdline,
        workdir=os.getcwd(),
        created=datetime.datetime.now().isoformat(timespec="seconds"),
        pre_hook=list(pre_hook),
        post_hook=list(post_hook),
    )
    dest = core.VirtualMachineManager().create(descriptor, force=force)
    click.echo(f"{name}  ->  {dest}")


@vm_group.command("list", help="list defined vms")
@handle_errors
def vm_list():
    vm_manager = core.VirtualMachineManager()
    lifecycle = core.VirtualMachineLifecycleManager()
    descriptors = vm_manager.list()
    if not descriptors:
        click.echo("no vms defined")
        return
    click.echo(f"{'NAME':<24}{'STATUS':<12}{'BINARY':<22}DEFINITION")
    for d in descriptors:
        binary = shlex.split(d.cmdline)[0] if d.cmdline else "?"
        status = "running" if lifecycle.status(d) else "-"
        path = vm_manager.path_for(d.name)
        click.echo(f"{d.name:<24}{status:<12}{os.path.basename(binary):<22}{path}")


@vm_group.command("ps", help="list running vms")
@handle_errors
def vm_ps():
    vm_manager = core.VirtualMachineManager()
    lifecycle = core.VirtualMachineLifecycleManager()
    rows = []
    for d in vm_manager.list():
        pid = lifecycle.status(d)
        if not pid:
            continue
        rows.append((d.name, pid, lifecycle.uptime(d)))
    if not rows:
        click.echo("no vms running")
        return
    click.echo(f"{'NAME':<24}{'PID':<10}UPTIME")
    for name, pid, uptime in rows:
        click.echo(f"{name:<24}{pid:<10}{uptime}")


@vm_group.command("inspect", help="show vm details")
@click.argument("name")
@handle_errors
def vm_inspect(name):
    vm_manager = core.VirtualMachineManager()
    lifecycle = core.VirtualMachineLifecycleManager()
    d = vm_manager.load(name)
    path = vm_manager.path_for(name)
    pid = lifecycle.status(d)
    click.echo(f"path:    {path}")
    click.echo(f"name:    {d.name}")
    click.echo(f"created: {d.created}")
    click.echo(f"workdir: {d.workdir}")
    click.echo(f"status:  {'running (pid ' + str(pid) + ')' if pid else 'stopped'}")
    for label, hooks in (("pre-hook", d.pre_hook), ("post-hook", d.post_hook)):
        if hooks:
            click.echo(f"{label}:")
            for cmd in hooks:
                click.echo(f"  - {cmd}")
    click.echo(f"cmdline: {d.cmdline}")


@vm_group.command("remove", help="delete a vm definition")
@click.argument("name")
@handle_errors
def vm_remove(name):
    vm_manager = core.VirtualMachineManager()
    lifecycle = core.VirtualMachineLifecycleManager()
    if not vm_manager.path_for(name):
        raise core.QemuCliError(f"no such vm: {name}")
    if lifecycle.is_running(name):
        raise core.QemuCliError(f"vm '{name}' is running; stop it first")
    path = vm_manager.remove(name)
    click.echo(f"removed {path}")


vm_group.add_command(vm_remove, name="rm")


@main.command("run", context_settings=dict(ignore_unknown_options=True),
              help="start a vm")
@click.argument("name")
@click.option("-d", "--detach", is_flag=True, help="run in background")
@click.argument("extra", nargs=-1, type=click.UNPROCESSED)
@handle_errors
def run_cmd(name, detach, extra):
    vm_manager = core.VirtualMachineManager()
    lifecycle = core.VirtualMachineLifecycleManager()
    descriptor = vm_manager.load(name)
    result = lifecycle.run(descriptor, extra_args=extra, detach=detach, log=click.echo)
    if result.detached:
        click.echo(f"{name} started (pid {result.pid})")
        return
    for cmd, rc in result.post_hook_failures:
        click.echo(f"Warning: post-hook failed (exit {rc}): {cmd}", err=True)
    raise SystemExit(result.returncode)


@main.command("stop", help="stop a running vm (SIGTERM)")
@click.argument("name")
@click.option("-t", "--timeout", type=float, default=10.0)
@handle_errors
def stop_cmd(name, timeout):
    vm_manager = core.VirtualMachineManager()
    lifecycle = core.VirtualMachineLifecycleManager()
    descriptor = vm_manager.load(name)
    result = lifecycle.stop(descriptor, timeout=timeout)
    if result.force_killed:
        click.echo(f"{name}: SIGKILL after {timeout}s")
    click.echo(f"{name} stopped")


main.add_command(vm_ps, name="ps")


if __name__ == "__main__":
    main()
