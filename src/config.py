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

import os
from configparser import ConfigParser

CONFIG_FILE = os.path.expanduser("~/.config/shabti.conf")


class Config:
    def __init__(self):
        if not os.path.exists(CONFIG_FILE):
            open(CONFIG_FILE, "w").close()

        self._conf = ConfigParser()
        self._conf.read(CONFIG_FILE, encoding="utf-8")

    @property
    def ssh(self):
        user = os.environ.get("USER")
        key = os.path.expanduser("~/.ssh/id_rsa")
        if self._conf.has_option("ssh", "user"):
            user = self._conf["ssh"].get("user")
        if self._conf.has_option("ssh", "key"):
            key = self._conf["ssh"].get("key")

        return {"user": user, "key": key}
