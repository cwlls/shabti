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

    _instance = None

    def __new__(cls, remote_path: str, local_dir: str | pathlib.Path = STATE_DIR, local_subdir: str | None = None):
        if cls._instance is None:
            cls._instance = super(CachedRemoteFile, cls).__new__(cls)

            # file paths
            cls.remote_path = remote_path
            if local_subdir:
                cls.local_path = pathlib.Path(local_dir).joinpath(
                    local_subdir, f"{pathlib.Path(remote_path).name}.json"
                )
            else:
                cls.local_path = pathlib.Path(local_dir).joinpath(f"{pathlib.Path(remote_path).name}.json")

            # contents
            cls._etag = ""
            cls._contents = ""
            cls._last_update = datetime.fromisoformat("1901-01-01T00:00:00.000Z")

            # setup local file if not exist
            if not cls.local_path.parent.exists():
                cls.local_path.parent.mkdir()
            if not cls.local_path.exists():
                cls._save_file()

            cls._load_file()

        return cls._instance

    @classmethod
    def _load_file(cls):
        json_bits = json.loads(cls.local_path.read_text())
        cls._etag = json_bits["etag"]
        cls._contents = str(json_bits["contents"])
        cls._last_update = datetime.fromisoformat(json_bits["last_update"])

    @classmethod
    def _save_file(cls):
        cls.local_path.write_text(
            json.dumps({"etag": cls._etag, "contents": cls._contents, "last_update": str(cls._last_update)})
        )

    @classmethod
    async def _update_file(cls):
        headers = {"Accept-Encoding": "Identity"}
        if cls._etag is not None:
            headers["If-None-Match"] = cls._etag
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(
                cls.remote_path,
                ssl=False,
            ) as resp:
                if resp.status == 200:
                    cls._etag = resp.headers.get("Etag")
                    cls._last_update = datetime.now().isoformat()
                    cls._contents = await resp.text()
                elif resp.status == 304:
                    pass
                else:
                    print(f"Error fetching file: {resp.status}")

        cls._save_file()

    @classmethod
    def contents(cls) -> str:
        asyncio.run(cls._update_file())
        return cls._contents


if __name__ == "__main__":
    test_file = CachedRemoteFile(
        "https://svn.apache.org/repos/infra/infrastructure/trunk/dns/zones/inventory.conf", local_subdir="shabti"
    )
    print(test_file.contents())
