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
import pathlib
import json
from datetime import datetime
import asyncio

import aiohttp

STATE_DIR = pathlib.Path.home().joinpath(".local/state")


class CachedRemoteFile(object):
    def __init__(self, remote_path: str, local_dir: str | pathlib.Path = STATE_DIR, local_subdir: str | None = None):
        # file paths
        self.remote_path = remote_path
        if local_subdir:
            self.local_path = pathlib.Path(local_dir).joinpath(local_subdir, f"{pathlib.Path(remote_path).name}.json")
        else:
            self.local_path = pathlib.Path(local_dir).joinpath(f"{pathlib.Path(remote_path).name}.json")

        # contents
        self._etag = ""
        self._contents = ""
        self._last_update = datetime.fromisoformat("1901-01-01T00:00:00.000Z")

        # setup local file if not exist
        if not self.local_path.parent.exists():
            self.local_path.parent.mkdir()
        if not self.local_path.exists():
            self._save_file()

        self._load_file()

    def _load_file(self):
        json_bits = json.loads(self.local_path.read_text())
        self._etag = json_bits["etag"]
        self._contents = str(json_bits["contents"])
        self._last_update = datetime.fromisoformat(json_bits["last_update"])

    def _save_file(self):
        self.local_path.write_text(
            json.dumps({"etag": self._etag, "contents": self._contents, "last_update": str(self._last_update)})
        )

    async def _update_file(self):
        headers = {"Accept-Encoding": "Identity"}
        if self._etag is not None:
            headers["If-None-Match"] = self._etag
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(
                self.remote_path,
                ssl=False,
            ) as resp:
                if resp.status == 200:
                    self._etag = resp.headers.get("Etag")
                    self._last_update = datetime.now().isoformat()
                    self._contents = await resp.text()
                elif resp.status == 304:
                    pass
                else:
                    print(f"Error fetching file: {resp.status}")

        self._save_file()

    def contents(self) -> str:
        asyncio.run(self._update_file())
        return self._contents


if __name__ == "__main__":
    test_file = CachedRemoteFile(
        "https://svn.apache.org/repos/infra/infrastructure/trunk/dns/zones/inventory.conf", local_subdir="shabti"
    )
    print(test_file.contents())
