from __future__ import annotations

import asyncio

import pytest

from tests.support.harness import public_api

pytestmark = pytest.mark.api


def test_bash_accepts_in_memory_fs_config_object() -> None:
    api = public_api()

    with api.Bash(fs=api.InMemoryFs(files={"/seed.txt": "seed\n"}), cwd="/") as bash:
        result = bash.exec("cat seed.txt")

    assert result.stdout == "seed\n"


def test_async_bash_accepts_in_memory_fs_config_object() -> None:
    api = public_api()

    async def exercise() -> None:
        async with api.AsyncBash(fs=api.InMemoryFs(files={"/seed.txt": "seed\n"}), cwd="/") as bash:
            result = await bash.exec("cat seed.txt")

        assert result.stdout == "seed\n"

    asyncio.run(exercise())
