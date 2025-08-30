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

from helpers import inventory_conf

INVENTORY_FILE = inventory_conf.InventoryConf()


@click.command(help="commands to help find and manipulate hosts")
@click.argument("hostname", required=False)
@click.option("-k", "--keyword", help="filter hosts by keyword", is_flag=False)
@click.option("-o", "--owner", help="filter hosts by owner", is_flag=False)
@click.option("-g", "--group", help="filter hosts by group", is_flag=False)
@click.option("-i", "--ip", help="filter hosts by IP", is_flag=False)
@click.option("-s", "--subnet", help="filter hosts by subnet", is_flag=False)
def cli(hostname, keyword, owner, group, ip, subnet):
    if hostname:
        if hostname in INVENTORY_FILE.hosts.keys():
            print_host(INVENTORY_FILE.hosts[hostname])
        else:
            click.echo("Host not found!")
    else:
        hosts = INVENTORY_FILE.hosts.values()

        # build up a filter stack
        filters = []
        if filter_keyword := keyword or "":
            filters.append(lambda h: h.has_keyword(filter_keyword.lower()))
        if filter_owner := owner:
            filters.append(lambda h: h.owner == filter_owner.lower())
        if filter_group := group:
            filters.append(lambda h: filter_group.lower() in h.groups)
        if filter_ip := ip:
            filters.append(lambda h: h.has_ip(filter_ip))
        if filter_subnet := subnet:
            filters.append(lambda h: h.in_subnet(filter_subnet))

        # filter hosts using built up stack of filters
        if len(filters) > 0:
            filtered_hosts = filter(lambda h: all(f(h) for f in filters), hosts)
        else:
            filtered_hosts = hosts

        # display each of the possibly filtered hosts
        for host in filtered_hosts:
            click.echo(f"  {host.name}")


def print_host(host: inventory_conf.Host):
    click.echo(f"Host: {host.name}")
    if host.ip:
        click.echo(f"IP: {host.ip}")
    if host.owner:
        click.echo(f"Owner: {host.owner}")
    if host.cname:
        click.echo(f"CNAME: {host.cname}")
    if host.groups:
        click.echo("Groups:")
        for g in host.groups:
            click.echo(f"\t{g}")
    if host.altnames:
        click.echo("AltNames:")
        for n in host.altnames:
            click.echo(f"\t{n}")
