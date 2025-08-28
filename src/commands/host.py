# Copyright 2025 Chris Wells <ehlo@cwlls.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import click

from tools import inventory_conf

INVENTORY_FILE = inventory_conf.InventoryConf()


@click.group(help="commands to help find and manipulate hosts", invoke_without_command=True)
@click.pass_context
@click.option("--owner", help="filter hosts by owner", is_flag=False)
@click.option("--group", help="filter hosts by group", is_flag=False)
def cli(ctx, owner, group):
    if ctx.invoked_subcommand is None:
        hosts = []
        if owner:
            banner = f"Host(s) owned by {owner}:"
            hosts = [host for host in INVENTORY_FILE.hosts.values() if host.owner == owner]
        elif group:
            banner = f"Host(s) in group {group}:"
            hosts = [host for host in INVENTORY_FILE.hosts.values() if group in host.groups]
        else:
            banner = "All hosts:"
            hosts = [host for host in INVENTORY_FILE.hosts.values()]

        click.echo(banner)
        for host in hosts:
            click.echo(f"  {host.name}")


@cli.command()
def ssh():
    ## TEMP
    user = "wells"
    identity_file = "~/.ssh/id_rsa"
    for host in INVENTORY_FILE.hosts.values():
        click.echo(f"Host {host.name}")
        click.echo(f"\tHostName {host.fqdn}")
        click.echo(f"\tUser {user}")
        click.echo(f"\tIdentityFile {identity_file}")
        click.echo()
