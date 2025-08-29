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
import configparser
import ipaddress
from collections import deque
from typing import List

from cached_remote_file import CachedRemoteFile

CONF_FILE = "https://svn.apache.org/repos/infra/infrastructure/trunk/dns/zones/inventory.conf"
ASF_DOMAIN = "apache.org"


class Host:
    """
    a class to hold host objects from an inventory.conf file.

    Args:
        name(str): the name of the host
        attributes(str): a string of attributes

    Attributes:
        name(str): the name of the host
        altnames(List[str]): a list of alternative names (optional)
        _groups(List[str]): a list of groups to which this host belongs

    Properties:
        fqdn(str): the name of the host concatenated with the domain name

    """

    def __init__(self, name: str, attributes: str):
        self.name = name
        self.altnames = set()
        self.groups = set()
        self.owner = "infra"
        self.ip4_address = None
        self.ip6_address = None
        self.cname = ""
        self.extras = ""
        self.ttl = None

        if "-win-" in name:
            self.groups.add("windows")
        else:
            self.groups.add("ubuntu")

        attr_parts = deque(attributes.split(" "))

        while len(attr_parts) > 0:
            attr = attr_parts.popleft().strip()
            try:
                ipaddr = ipaddress.ip_address(attr)
                if isinstance(ipaddr, ipaddress.IPv4Address):
                    self.ip4_address = ipaddr
                else:
                    self.ip6_address = ipaddr
            except ValueError:
                if ":" not in attr:
                    self.cname = attr
                else:
                    k, v = attr.split(":", maxsplit=1)
                    match k:
                        case "owner":
                            self.owner = v
                        case "names":
                            names = v.split(",")
                            # print(f"{self.name} --> {len(names)}")
                            for n in names:
                                # print(f"ADDING ALTNAME: {n}")
                                self.altnames.add(n)
                        case "ttl":
                            self.ttl = v
                        case _:
                            self.extras = f"{k}:{v}"

            except Exception as e:
                print(f"Attribute parsing error: {e}")

    def __repr__(self):
        return f"<Host: {self.name}>"

    @property
    def fqdn(self) -> str:
        return f"{self.name}.{ASF_DOMAIN}"

    @property
    def is_cname(self) -> bool:
        if self.cname and not self.ip:
            return True
        return False

    @property
    def ip(self) -> str | None:
        if self.ip4_address:
            return str(self.ip4_address)
        elif self.ip6_address:
            return str(self.ip6_address)
        else:
            return None

    def has_group(self, group: str) -> bool:
        return group in self.groups

    def has_owner(self, owner: str) -> bool:
        return owner == self.owner

    def has_ip(self, ip_str: str) -> bool:
        ipaddr = ipaddress.ip_address(ipaddr)
        return self.ip4_address == ipaddr or self.ip6_address == ipaddr

    def in_subnet(self, subnet_str: str) -> bool:
        subnet = ipaddress.ip_network(subnet_str)
        return self.ip4_address in subnet or self.ip6_address in subnet


class InventoryConf:
    """a class to hold inventory.conf information"""

    def __init__(self):
        self._file = CachedRemoteFile(CONF_FILE, local_subdir="shabti")

        # setup a configparser object and parse in the config from a CachedRemoteFile object
        self.conf = configparser.ConfigParser()
        self.conf.read_string(self._file.contents())

        ## build up list of hosts
        self.hosts = {}

        # grab all the non-jenkins hosts and CNAMES
        for name, attributes in self.conf["hosts"].items():
            self.hosts[name] = Host(name, attributes)

        # grab all the jenkins nodes, and prepend their names with 'jenkins-'
        for name, attributes in self.conf["prefix:jenkins"].items():
            name = f"jenkins-{name}"
            self.hosts[name] = Host(name, attributes)
            self.hosts[name].groups.add("jenkins")

        ## attach all the groups to the targeted hosts
        self._groups = [group for group in self.conf.sections() if group.startswith("group")]

        # iterate through the groups and figure out their targets
        for group in self._groups:
            targets = self.conf[group].get("targets", "").split()
            if len(targets) > 0:
                for target in targets:
                    target = target.split("[", maxsplit=1)[0]
                    g = group.split(":", maxsplit=1)[1]
                    try:
                        self.hosts[target].groups.add(g)
                    except KeyError:
                        continue

    @property
    def groups(self):
        """send back a 'clean' version of the group name (no 'group:' prefix)"""
        return [group[6:] for group in self._groups]

    def from_group(self, grp: str) -> List[Host]:
        return [host for host in self.hosts.values() if host.has_group(grp)]

    def from_owner(self, owner: str) -> List[Host]:
        return [host for host in self.hosts.values() if host.has_owner(owner)]


if __name__ == "__main__":
    conf = InventoryConf()
    for _, host in conf.hosts.items():
        print("----")
        print(f"Host: {host.name}.{ASF_DOMAIN}")
        if host.ipaddress:
            print("IP:", host.ipaddress)
        if host.owner:
            print("Owner:", host.owner)
        if host.cname:
            print("CNAME:", host.cname)
        if host.groups:
            print("Groups:")
            for g in host.groups:
                print(f"\t{g}")
        if host.altnames:
            print("AltNames:")
            for n in host.altnames:
                print(f"\t{n}")
