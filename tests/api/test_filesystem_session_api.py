from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from tests.support.harness import public_api

pytestmark = pytest.mark.api


def test_bash_fs_proxy_supports_core_session_operations() -> None:
    api = public_api()
    seeded_mtime = datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)

    with api.Bash(
        files={"seed.txt": api.FileInit(content="seed\n", mode=0o640, mtime=seeded_mtime)},
        cwd="/",
    ) as bash:
        assert bash.fs.exists("seed.txt") is True

        seeded_stat = bash.fs.stat("seed.txt")
        assert seeded_stat.is_file is True
        assert seeded_stat.is_directory is False
        assert seeded_stat.mode == 0o640
        assert seeded_stat.mtime == seeded_mtime

        bash.fs.mkdir("docs")
        bash.fs.write_text("docs/guide.txt", "guide\n")
        assert bash.fs.read_text("docs/guide.txt") == "guide\n"

        bash.fs.cp("docs/guide.txt", "copy.txt")
        bash.fs.mv("copy.txt", "moved.txt")
        bash.fs.chmod("moved.txt", 0o600)

        listing = set(bash.fs.readdir("/"))
        assert {"docs", "moved.txt", "seed.txt"} <= listing

        bash.exec("ln -s moved.txt link.txt")
        assert bash.fs.readlink("link.txt") == "moved.txt"
        assert bash.fs.realpath("link.txt") == "/moved.txt"

        bash.fs.rm("docs", recursive=True)
        assert bash.fs.exists("docs/guide.txt") is False


def test_bash_fs_proxy_supports_extended_session_operations() -> None:
    api = public_api()
    updated_mtime = datetime(2024, 2, 3, 4, 5, 6, tzinfo=UTC)

    with api.Bash(cwd="/workspace") as bash:
        bash.fs.mkdir("docs")
        bash.fs.write_text("docs/guide.txt", "guide\n")
        bash.fs.append_text("docs/guide.txt", "more\n")
        assert bash.fs.read_text("docs/guide.txt") == "guide\nmore\n"

        bash.fs.write_bytes("data.bin", b"ab")
        bash.fs.append_bytes("data.bin", b"cd")
        assert bash.fs.read_bytes("data.bin") == b"abcd"

        bash.fs.symlink("docs/guide.txt", "guide-link.txt")
        bash.fs.link("docs/guide.txt", "guide-hardlink.txt")

        link_stat = bash.fs.lstat("guide-link.txt")
        assert link_stat.is_symbolic_link is True
        assert link_stat.is_file is False
        assert bash.fs.readlink("guide-link.txt") == "docs/guide.txt"
        assert bash.fs.realpath("guide-link.txt") == "/workspace/docs/guide.txt"

        typed_listing = {entry.name: entry for entry in bash.fs.readdir_with_file_types(".")}
        assert isinstance(typed_listing["docs"], api.DirentEntry)
        assert typed_listing["docs"].is_directory is True
        assert typed_listing["guide-link.txt"].is_symbolic_link is True
        assert typed_listing["guide-hardlink.txt"].is_file is True

        assert bash.fs.resolve_path("../guide-link.txt", base="docs") == "/workspace/guide-link.txt"
        assert {
            "/workspace/docs/guide.txt",
            "/workspace/guide-link.txt",
            "/workspace/guide-hardlink.txt",
        } <= set(bash.fs.get_all_paths())

        bash.fs.utimes("docs/guide.txt", updated_mtime, updated_mtime)
        assert bash.fs.stat("docs/guide.txt").mtime == updated_mtime
        assert bash.fs.read_text("guide-hardlink.txt") == "guide\nmore\n"


def test_bash_lazy_file_callback_is_materialized_once() -> None:
    api = public_api()
    calls = 0

    def provider() -> str:
        nonlocal calls
        calls += 1
        return "lazy\n"

    with api.Bash(files={"lazy.txt": api.LazyFile(provider=provider)}, cwd="/") as bash:
        assert calls == 0
        assert bash.read_text("lazy.txt") == "lazy\n"
        assert calls == 1
        assert bash.read_text("lazy.txt") == "lazy\n"
        assert calls == 1


def test_bash_lazy_file_callback_is_not_invoked_if_path_is_overwritten_first() -> None:
    api = public_api()
    calls = 0

    def provider() -> str:
        nonlocal calls
        calls += 1
        return "lazy\n"

    with api.Bash(files={"lazy.txt": api.LazyFile(provider=provider)}, cwd="/") as bash:
        bash.write_text("lazy.txt", "eager\n")
        assert bash.read_text("lazy.txt") == "eager\n"

    assert calls == 0


def test_bash_fs_takes_precedence_over_files_init() -> None:
    api = public_api()

    with api.Bash(
        files={"note.txt": "from-files\n"},
        fs=api.InMemoryFs(files={"/note.txt": "from-fs\n"}),
        cwd="/",
    ) as bash:
        assert bash.read_text("note.txt") == "from-fs\n"


def test_async_bash_fs_proxy_supports_extended_session_operations() -> None:
    api = public_api()
    updated_mtime = datetime(2024, 8, 9, 10, 11, 12, tzinfo=UTC)

    async def exercise() -> None:
        async with api.AsyncBash(cwd="/workspace") as bash:
            await bash.fs.mkdir("docs")
            await bash.fs.write_text("docs/guide.txt", "guide\n")
            await bash.fs.append_text("docs/guide.txt", "more\n")
            assert await bash.fs.read_text("docs/guide.txt") == "guide\nmore\n"

            await bash.fs.write_bytes("data.bin", b"ab")
            await bash.fs.append_bytes("data.bin", b"cd")
            assert await bash.fs.read_bytes("data.bin") == b"abcd"

            await bash.fs.symlink("docs/guide.txt", "guide-link.txt")
            await bash.fs.link("docs/guide.txt", "guide-hardlink.txt")

            link_stat = await bash.fs.lstat("guide-link.txt")
            assert link_stat.is_symbolic_link is True
            assert link_stat.is_file is False
            assert await bash.fs.readlink("guide-link.txt") == "docs/guide.txt"
            assert await bash.fs.realpath("guide-link.txt") == "/workspace/docs/guide.txt"

            typed_listing = {entry.name: entry for entry in await bash.fs.readdir_with_file_types(".")}
            assert isinstance(typed_listing["docs"], api.DirentEntry)
            assert typed_listing["docs"].is_directory is True
            assert typed_listing["guide-link.txt"].is_symbolic_link is True
            assert typed_listing["guide-hardlink.txt"].is_file is True

            assert await bash.fs.resolve_path("../guide-link.txt", base="docs") == "/workspace/guide-link.txt"
            assert {
                "/workspace/docs/guide.txt",
                "/workspace/guide-link.txt",
                "/workspace/guide-hardlink.txt",
            } <= set(await bash.fs.get_all_paths())

            await bash.fs.utimes("docs/guide.txt", updated_mtime, updated_mtime)
            assert (await bash.fs.stat("docs/guide.txt")).mtime == updated_mtime
            assert await bash.fs.read_text("guide-hardlink.txt") == "guide\nmore\n"

    asyncio.run(exercise())


def test_async_bash_fs_proxy_and_async_lazy_provider_work() -> None:
    api = public_api()
    seeded_mtime = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)

    async def exercise() -> None:
        calls = 0

        async def provider() -> str:
            nonlocal calls
            calls += 1
            await asyncio.sleep(0)
            return "async-lazy\n"

        async with api.AsyncBash(
            files={
                "seed.txt": api.FileInit(content="seed\n", mode=0o644, mtime=seeded_mtime),
                "lazy.txt": api.LazyFile(provider=provider),
            },
            cwd="/",
        ) as bash:
            assert await bash.fs.exists("seed.txt") is True

            stat = await bash.fs.stat("seed.txt")
            assert stat.mode == 0o644
            assert stat.mtime == seeded_mtime

            await bash.fs.mkdir("nested")
            await bash.fs.write_text("nested/note.txt", "note\n")
            assert await bash.fs.read_text("nested/note.txt") == "note\n"

            await bash.fs.cp("nested/note.txt", "copied.txt")
            await bash.fs.mv("copied.txt", "moved.txt")
            await bash.fs.chmod("moved.txt", 0o600)
            await bash.exec("ln -s moved.txt link.txt")

            assert await bash.fs.readlink("link.txt") == "moved.txt"
            assert await bash.fs.realpath("link.txt") == "/moved.txt"
            assert await bash.read_text("lazy.txt") == "async-lazy\n"
            assert await bash.read_text("lazy.txt") == "async-lazy\n"
            assert calls == 1

            await bash.fs.rm("nested", recursive=True)
            assert await bash.fs.exists("nested/note.txt") is False

    asyncio.run(exercise())
