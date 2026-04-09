from __future__ import annotations

import asyncio
from datetime import UTC, datetime

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


def test_bash_accepts_in_memory_fs_richer_initial_files() -> None:
    api = public_api()
    calls = 0

    def provider() -> str:
        nonlocal calls
        calls += 1
        return "lazy\n"

    seeded_mtime = datetime(2024, 7, 8, 9, 10, 11, tzinfo=UTC)

    with api.Bash(
        fs=api.InMemoryFs(
            files={
                "/meta.txt": api.FileInit(content="meta\n", mode=0o640, mtime=seeded_mtime),
                "/lazy.txt": api.LazyFile(provider=provider),
            },
        ),
        cwd="/",
    ) as bash:
        assert bash.read_text("meta.txt") == "meta\n"
        assert bash.fs.stat("meta.txt").mode == 0o640
        assert bash.fs.stat("meta.txt").mtime == seeded_mtime
        assert bash.read_text("lazy.txt") == "lazy\n"
        assert bash.read_text("lazy.txt") == "lazy\n"

    assert calls == 1
