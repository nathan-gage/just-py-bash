from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

from tests.support.fake_backend import write_fake_backend
from tests.support.harness import public_api

pytestmark = pytest.mark.api


def fake_node_command(script_path: Path) -> list[str]:
    return [sys.executable, str(script_path)]


def test_bash_from_options_constructs_session() -> None:
    api = public_api()
    options = api.BashOptions(cwd="/workspace", files={"/workspace/seed.txt": "seed\n"})

    with api.Bash.from_options(options) as bash:
        result = bash.exec("cat seed.txt")
        cwd = bash.get_cwd()

    assert result.stdout == "seed\n"
    assert cwd == "/workspace"


def test_async_bash_from_options_constructs_session() -> None:
    api = public_api()
    options = api.BashOptions(cwd="/workspace", files={"/workspace/seed.txt": "seed\n"})

    async def exercise() -> None:
        async with api.AsyncBash.from_options(options) as bash:
            result = await bash.exec("cat seed.txt")
            cwd = await bash.get_cwd()

        assert result.stdout == "seed\n"
        assert cwd == "/workspace"

    asyncio.run(exercise())


def test_bash_raises_backend_unavailable_when_node_command_is_missing() -> None:
    api = public_api()

    with pytest.raises(api.BackendUnavailableError):
        api.Bash(node_command=["/definitely/missing/just-bash-node"])


def test_bash_raises_bridge_error_on_malformed_worker_response(tmp_path: Path) -> None:
    api = public_api()
    worker = tmp_path / "malformed-worker.py"
    write_fake_backend(worker, mode="malformed_exec")

    with api.Bash(node_command=fake_node_command(worker)) as bash:
        with pytest.raises(api.BridgeError, match="Failed to decode just-bash worker response"):
            bash.exec("printf malformed")


def test_bash_returns_timeout_result_when_worker_stops_responding(tmp_path: Path) -> None:
    api = public_api()
    worker = tmp_path / "hanging-worker.py"
    write_fake_backend(worker, mode="hang_on_exec")

    with api.Bash(node_command=fake_node_command(worker)) as bash:
        result = bash.exec("printf slow", timeout=0.0)

    assert result.exit_code == 124
    assert result.stdout == ""
    assert result.stderr == "bash: execution timeout exceeded after 1ms; session was reset\n"
    assert result.metadata == {"timed_out": True, "timeout_ms": 1, "session_reset": True}


def test_bash_returns_timeout_result_and_recovers_after_exec_timeout(tmp_path: Path) -> None:
    api = public_api()
    worker = tmp_path / "timeout-worker.py"
    write_fake_backend(worker, mode="hang_on_first_exec")

    with api.Bash(node_command=fake_node_command(worker)) as bash:
        timeout_result = bash.exec("printf slow", timeout=0.0)
        recovered_result = bash.exec("printf ok")

    assert timeout_result.exit_code == 124
    assert timeout_result.stdout == ""
    assert timeout_result.stderr == "bash: execution timeout exceeded after 1ms; session was reset\n"
    assert timeout_result.metadata == {"timed_out": True, "timeout_ms": 1, "session_reset": True}
    assert recovered_result.stdout == "recovered\n"
    assert recovered_result.stderr == ""


def test_bash_can_close_cleanly_after_worker_crash(tmp_path: Path) -> None:
    api = public_api()
    worker = tmp_path / "crashing-worker.py"
    write_fake_backend(worker, mode="crash_on_exec")

    bash = api.Bash(node_command=fake_node_command(worker))
    try:
        with pytest.raises(api.BridgeError, match="worker exited unexpectedly"):
            bash.exec("printf boom")
    finally:
        bash.close()
        bash.close()


def test_bash_repr_does_not_perform_bridge_io_after_worker_crash(tmp_path: Path) -> None:
    api = public_api()
    worker = tmp_path / "repr-crashing-worker.py"
    write_fake_backend(worker, mode="crash_on_exec")

    bash = api.Bash(node_command=fake_node_command(worker))
    try:
        with pytest.raises(api.BridgeError, match="worker exited unexpectedly"):
            bash.exec("printf boom")

        rendered = repr(bash)
    finally:
        bash.close()

    assert rendered.startswith("Bash(")
    assert "backend_version='fake-backend'" in rendered
    assert "closed=" in rendered


def test_async_bash_raises_backend_unavailable_when_node_command_is_missing() -> None:
    api = public_api()

    async def exercise() -> None:
        with pytest.raises(api.BackendUnavailableError):
            async with api.AsyncBash(node_command=["/definitely/missing/just-bash-node"]):
                pass

    asyncio.run(exercise())


def test_async_bash_raises_bridge_error_on_malformed_worker_response(tmp_path: Path) -> None:
    api = public_api()
    worker = tmp_path / "async-malformed-worker.py"
    write_fake_backend(worker, mode="malformed_exec")

    async def exercise() -> None:
        async with api.AsyncBash(node_command=fake_node_command(worker)) as bash:
            with pytest.raises(api.BridgeError, match="Failed to decode just-bash worker response"):
                await bash.exec("printf malformed")

    asyncio.run(exercise())


def test_async_bash_returns_timeout_result_and_recovers_after_exec_timeout(tmp_path: Path) -> None:
    api = public_api()
    worker = tmp_path / "async-timeout-worker.py"
    write_fake_backend(worker, mode="hang_on_first_exec")

    async def exercise() -> None:
        async with api.AsyncBash(node_command=fake_node_command(worker)) as bash:
            timeout_result = await bash.exec("printf slow", timeout=0.0)
            recovered_result = await bash.exec("printf ok")

        assert timeout_result.exit_code == 124
        assert timeout_result.stdout == ""
        assert timeout_result.stderr == "bash: execution timeout exceeded after 1ms; session was reset\n"
        assert timeout_result.metadata == {"timed_out": True, "timeout_ms": 1, "session_reset": True}
        assert recovered_result.stdout == "recovered\n"
        assert recovered_result.stderr == ""

    asyncio.run(exercise())


def test_async_bash_can_close_cleanly_after_worker_crash(tmp_path: Path) -> None:
    api = public_api()
    worker = tmp_path / "async-crashing-worker.py"
    write_fake_backend(worker, mode="crash_on_exec")

    async def exercise() -> None:
        bash = api.AsyncBash(node_command=fake_node_command(worker))
        try:
            with pytest.raises(api.BridgeError, match="worker exited unexpectedly"):
                await bash.exec("printf boom")
        finally:
            await bash.close()
            await bash.close()
            assert bash.closed

    asyncio.run(exercise())
