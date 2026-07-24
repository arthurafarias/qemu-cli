"""qemu — docker-style CLI for managing QEMU VM command lines.

This module is a thin presentation layer: every command decorates a
function whose body parses/echoes and then calls straight into
qemu_cli.core, which holds all the actual business logic.
"""

import functools

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
def main():
    pass


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
    dest = core.create_vm(name, cmdline, force=force,
                           pre_hook=list(pre_hook), post_hook=list(post_hook))
    click.echo(f"{name}  ->  {dest}")


@vm_group.command("list", help="list defined vms")
@handle_errors
def vm_list():
    entries = core.list_vms()
    if not entries:
        click.echo("no vms defined")
        return
    click.echo(f"{'NAME':<24}{'STATUS':<12}{'BINARY':<22}DEFINITION")
    for e in entries:
        status = "running" if e.running else "-"
        click.echo(f"{e.name:<24}{status:<12}{e.binary:<22}{e.path}")


@vm_group.command("ps", help="list running vms")
@handle_errors
def vm_ps():
    rows = core.ps_vms()
    if not rows:
        click.echo("no vms running")
        return
    click.echo(f"{'NAME':<24}{'PID':<10}UPTIME")
    for r in rows:
        click.echo(f"{r.name:<24}{r.pid:<10}{r.uptime}")


@vm_group.command("inspect", help="show vm details")
@click.argument("name")
@handle_errors
def vm_inspect(name):
    d = core.inspect_vm(name)
    click.echo(f"path:    {d.path}")
    click.echo(f"name:    {d.name}")
    click.echo(f"created: {d.created}")
    click.echo(f"workdir: {d.workdir}")
    click.echo(f"status:  {'running (pid ' + str(d.pid) + ')' if d.pid else 'stopped'}")
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
    path = core.remove_vm(name)
    click.echo(f"removed {path}")


vm_group.add_command(vm_remove, name="rm")


@main.command("run", context_settings=dict(ignore_unknown_options=True),
              help="start a vm")
@click.argument("name")
@click.option("-d", "--detach", is_flag=True, help="run in background")
@click.argument("extra", nargs=-1, type=click.UNPROCESSED)
@handle_errors
def run_cmd(name, detach, extra):
    result = core.run_vm(name, extra_args=extra, detach=detach, log=click.echo)
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
    result = core.stop_vm(name, timeout=timeout)
    if result.force_killed:
        click.echo(f"{name}: SIGKILL after {timeout}s")
    click.echo(f"{name} stopped")


main.add_command(vm_ps, name="ps")


if __name__ == "__main__":
    main()
