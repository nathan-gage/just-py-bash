from __future__ import annotations

import asyncio

import pytest

from tests.support.harness import public_api

pytestmark = pytest.mark.api


def test_bash_exposes_backend_version() -> None:
    Bash = public_api().Bash
    with Bash() as bash:
        assert bash.backend_version
        assert isinstance(bash.get_env(), dict)


def test_exec_result_check_raises_on_failure() -> None:
    api = public_api()
    Bash = api.Bash
    CommandFailedError = api.CommandFailedError
    with Bash() as bash:
        result = bash.exec("false")

    assert result.exit_code == 1
    try:
        result.check()
    except CommandFailedError as exc:
        assert exc.result.exit_code == 1
    else:  # pragma: no cover - defensive
        raise AssertionError("expected CommandFailedError")


def test_sessions_are_isolated() -> None:
    Bash = public_api().Bash
    with Bash() as left, Bash() as right:
        left.exec("echo left > only-here.txt")

        left_contents = left.exec("cat only-here.txt")
        right_contents = right.exec("cat only-here.txt")

    assert left_contents.stdout == "left\n"
    assert right_contents.exit_code != 0


def test_file_helpers_round_trip_text_and_bytes() -> None:
    Bash = public_api().Bash
    with Bash(cwd="/workspace") as bash:
        bash.write_text("note.txt", "hello\n")
        bash.write_bytes("blob.bin", b"\x00\x01abc")

        text = bash.read_text("note.txt")
        blob = bash.read_bytes("blob.bin")

    assert text == "hello\n"
    assert blob == b"\x00\x01abc"


def test_close_is_idempotent() -> None:
    Bash = public_api().Bash
    bash = Bash()
    bash.close()
    bash.close()


def test_async_bash_round_trips_commands_and_files() -> None:
    api = public_api()
    AsyncBash = api.AsyncBash

    async def exercise() -> None:
        async with AsyncBash(cwd="/workspace") as bash:
            assert bash.backend_version

            await bash.write_text("note.txt", "hello\n")
            result = await bash.exec("cat note.txt")
            contents = await bash.read_text("note.txt")
            env = await bash.get_env()
            cwd = await bash.get_cwd()

        assert result.stdout == "hello\n"
        assert contents == "hello\n"
        assert isinstance(env, dict)
        assert cwd == "/workspace"

    asyncio.run(exercise())


def test_async_bash_close_is_idempotent() -> None:
    AsyncBash = public_api().AsyncBash

    async def exercise() -> None:
        bash = AsyncBash()
        await bash.close()
        await bash.close()
        assert bash.closed

    asyncio.run(exercise())
