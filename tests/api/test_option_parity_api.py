from __future__ import annotations

import asyncio
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

from tests.support.fake_backend import write_fake_backend
from tests.support.harness import public_api

pytestmark = pytest.mark.api


def fake_node_command(script_path: Path) -> list[str]:
    return [sys.executable, str(script_path)]


class _RecorderLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict[str, object] | None]] = []

    def info(self, message: str, data: dict[str, object] | None = None) -> None:
        self.events.append(("info", message, data))

    def debug(self, message: str, data: dict[str, object] | None = None) -> None:
        self.events.append(("debug", message, data))


class _CoverageWriter:
    def __init__(self) -> None:
        self.hits: list[str] = []

    def hit(self, feature: str) -> None:
        self.hits.append(feature)


def test_bash_logger_trace_coverage_and_fetch_hooks_are_supported() -> None:
    api = public_api()
    logger = _RecorderLogger()
    coverage = _CoverageWriter()
    trace_events: list[Any] = []
    fetch_requests: list[Any] = []

    def trace(event: Any) -> None:
        trace_events.append(event)

    def fetch(request: Any) -> Any:
        fetch_requests.append(request)
        return api.FetchResult(
            status=200,
            status_text="OK",
            headers={"content-type": "text/plain"},
            body="hello from fetch\n",
            url=request.url,
        )

    with api.Bash(
        files={"/workspace/seed.txt": "seed\n"},
        cwd="/workspace",
        logger=logger,
        trace=trace,
        coverage=coverage,
        fetch=fetch,
    ) as bash:
        fetch_result = bash.exec("curl -s https://example.com")
        find_result = bash.exec("find . -maxdepth 1 -type f | sort")
        stderr_result = bash.exec("printf err >&2; false")

    assert fetch_result.stdout == "hello from fetch\n"
    assert fetch_requests
    assert fetch_requests[0].url == "https://example.com"
    assert fetch_requests[0].method == "GET"

    assert find_result.stdout == "./seed.txt\n"
    assert trace_events
    assert any(event.category == "find" for event in trace_events)

    assert stderr_result.exit_code == 1
    assert any(level == "info" and message == "exec" for level, message, _ in logger.events)
    assert any(level == "debug" and message == "stdout" for level, message, _ in logger.events)
    assert any(level == "info" and message == "stderr" for level, message, _ in logger.events)
    assert any(level == "info" and message == "exit" for level, message, _ in logger.events)

    assert coverage.hits
    assert any(hit.startswith("bash:") or hit.startswith("cmd:") for hit in coverage.hits)


def test_bash_accepts_defense_in_depth_config_object() -> None:
    api = public_api()
    violations: list[Any] = []

    with api.Bash(
        javascript=True,
        defense_in_depth=api.DefenseInDepthConfig(
            enabled=True,
            audit_mode=True,
            on_violation=violations.append,
            exclude_violation_types=["webassembly"],
        ),
    ) as bash:
        result = bash.exec("js-exec -c \"try { new Function('return 1')(); } catch (e) { console.log(e.message); }\"")

    assert result.exit_code == 0
    assert "Function constructor is not allowed" in result.stdout
    # The upstream security layer is allowed to evolve, so this is a smoke check:
    # when violations are surfaced, they should arrive as structured objects.
    for violation in violations:
        assert isinstance(violation.type, str)
        assert isinstance(violation.message, str)
        assert isinstance(violation.path, str)


def test_async_bash_supports_async_fetch_and_trace_callbacks() -> None:
    api = public_api()

    async def exercise() -> None:
        trace_events: list[Any] = []
        fetch_requests: list[Any] = []

        async def trace(event: Any) -> None:
            trace_events.append(event)
            await asyncio.sleep(0)

        async def fetch(request: Any) -> Any:
            fetch_requests.append(request)
            await asyncio.sleep(0)
            return api.FetchResult(
                status=200,
                status_text="OK",
                headers={"content-type": "text/plain"},
                body="async fetch\n",
                url=request.url,
            )

        async with api.AsyncBash(
            files={"/workspace/a.txt": "a\n"},
            cwd="/workspace",
            trace=trace,
            fetch=fetch,
        ) as bash:
            fetch_result = await bash.exec("curl -s https://example.com")
            find_result = await bash.exec("find . -maxdepth 1 -type f | sort")

        assert fetch_result.stdout == "async fetch\n"
        assert fetch_requests
        assert fetch_requests[0].url == "https://example.com"
        assert find_result.stdout == "./a.txt\n"
        assert trace_events
        assert any(event.category == "find" for event in trace_events)

    asyncio.run(exercise())


def test_bash_exec_waits_for_logger_callback_completion() -> None:
    api = public_api()
    started = threading.Event()
    release = threading.Event()
    done = threading.Event()
    result_holder: dict[str, Any] = {}

    class WaitingLogger:
        def info(self, message: str, data: dict[str, object] | None = None) -> None:
            if message == "exit":
                started.set()
                assert release.wait(timeout=2)

        def debug(self, message: str, data: dict[str, object] | None = None) -> None:
            return None

    with api.Bash(logger=WaitingLogger()) as bash:

        def run_exec() -> None:
            result_holder["result"] = bash.exec("echo hi")
            done.set()

        thread = threading.Thread(target=run_exec, daemon=True)
        thread.start()
        assert started.wait(timeout=2)
        assert not done.wait(timeout=0.1)
        release.set()
        thread.join(timeout=2)

    result = result_holder["result"]
    assert result.stdout == "hi\n"
    assert done.is_set()


def test_bash_exec_waits_for_trace_callback_completion() -> None:
    api = public_api()
    started = threading.Event()
    release = threading.Event()
    done = threading.Event()
    result_holder: dict[str, Any] = {}

    def trace(event: Any) -> None:
        if not started.is_set():
            started.set()
            assert release.wait(timeout=2)

    with api.Bash(files={"/workspace/a.txt": "a\n"}, cwd="/workspace", trace=trace) as bash:

        def run_exec() -> None:
            result_holder["result"] = bash.exec("find . -maxdepth 1 -type f | sort")
            done.set()

        thread = threading.Thread(target=run_exec, daemon=True)
        thread.start()
        assert started.wait(timeout=2)
        assert not done.wait(timeout=0.1)
        release.set()
        thread.join(timeout=2)

    result = result_holder["result"]
    assert result.stdout == "./a.txt\n"
    assert done.is_set()


def test_bash_exec_waits_for_coverage_callback_completion() -> None:
    api = public_api()
    started = threading.Event()
    release = threading.Event()
    done = threading.Event()
    result_holder: dict[str, Any] = {}

    class WaitingCoverage:
        def hit(self, feature: str) -> None:
            if not started.is_set():
                started.set()
                assert release.wait(timeout=2)

    with api.Bash(coverage=WaitingCoverage()) as bash:

        def run_exec() -> None:
            result_holder["result"] = bash.exec("echo hi")
            done.set()

        thread = threading.Thread(target=run_exec, daemon=True)
        thread.start()
        assert started.wait(timeout=2)
        assert not done.wait(timeout=0.1)
        release.set()
        thread.join(timeout=2)

    result = result_holder["result"]
    assert result.stdout == "hi\n"
    assert done.is_set()


def test_async_bash_exec_waits_for_logger_callback_completion() -> None:
    api = public_api()

    class AsyncWaitingLogger:
        def __init__(self) -> None:
            self.started = asyncio.Event()
            self.release = asyncio.Event()

        async def info(self, message: str, data: dict[str, object] | None = None) -> None:
            if message == "exit":
                self.started.set()
                await self.release.wait()

        async def debug(self, message: str, data: dict[str, object] | None = None) -> None:
            return None

    async def exercise() -> None:
        logger = AsyncWaitingLogger()
        async with api.AsyncBash(logger=logger) as bash:
            task = asyncio.create_task(bash.exec("echo hi"))
            await asyncio.wait_for(logger.started.wait(), timeout=2)
            assert not task.done()
            logger.release.set()
            result = await asyncio.wait_for(task, timeout=2)

        assert result.stdout == "hi\n"

    asyncio.run(exercise())


def test_async_bash_exec_waits_for_trace_callback_completion() -> None:
    api = public_api()

    async def exercise() -> None:
        started = asyncio.Event()
        release = asyncio.Event()

        async def trace(event: Any) -> None:
            if not started.is_set():
                started.set()
                await release.wait()

        async with api.AsyncBash(files={"/workspace/a.txt": "a\n"}, cwd="/workspace", trace=trace) as bash:
            task = asyncio.create_task(bash.exec("find . -maxdepth 1 -type f | sort"))
            await asyncio.wait_for(started.wait(), timeout=2)
            assert not task.done()
            release.set()
            result = await asyncio.wait_for(task, timeout=2)

        assert result.stdout == "./a.txt\n"

    asyncio.run(exercise())


def test_async_bash_exec_waits_for_coverage_callback_completion() -> None:
    api = public_api()

    class AsyncWaitingCoverage:
        def __init__(self) -> None:
            self.started = asyncio.Event()
            self.release = asyncio.Event()

        async def hit(self, feature: str) -> None:
            if not self.started.is_set():
                self.started.set()
                await self.release.wait()

    async def exercise() -> None:
        coverage = AsyncWaitingCoverage()
        async with api.AsyncBash(coverage=coverage) as bash:
            task = asyncio.create_task(bash.exec("echo hi"))
            await asyncio.wait_for(coverage.started.wait(), timeout=2)
            assert not task.done()
            coverage.release.set()
            result = await asyncio.wait_for(task, timeout=2)

        assert result.stdout == "hi\n"

    asyncio.run(exercise())


def test_bash_exec_waits_for_fetch_callback_completion() -> None:
    api = public_api()
    started = threading.Event()
    release = threading.Event()
    done = threading.Event()
    result_holder: dict[str, Any] = {}

    def fetch(request: Any) -> Any:
        started.set()
        assert release.wait(timeout=2)
        return api.FetchResult(status=200, status_text="OK", body="fetch-wait\n", url=request.url)

    with api.Bash(fetch=fetch) as bash:

        def run_exec() -> None:
            result_holder["result"] = bash.exec("curl -s https://example.com")
            done.set()

        thread = threading.Thread(target=run_exec, daemon=True)
        thread.start()
        assert started.wait(timeout=2)
        assert not done.wait(timeout=0.1)
        release.set()
        thread.join(timeout=2)

    result = result_holder["result"]
    assert result.stdout == "fetch-wait\n"
    assert done.is_set()


def test_async_bash_exec_waits_for_fetch_callback_completion() -> None:
    api = public_api()

    async def exercise() -> None:
        started = asyncio.Event()
        release = asyncio.Event()

        async def fetch(request: Any) -> Any:
            started.set()
            await release.wait()
            return api.FetchResult(status=200, status_text="OK", body="fetch-wait\n", url=request.url)

        async with api.AsyncBash(fetch=fetch) as bash:
            task = asyncio.create_task(bash.exec("curl -s https://example.com"))
            await asyncio.wait_for(started.wait(), timeout=2)
            assert not task.done()
            release.set()
            result = await asyncio.wait_for(task, timeout=2)

        assert result.stdout == "fetch-wait\n"

    asyncio.run(exercise())


def test_bash_fetch_callback_failure_is_returned_as_command_result() -> None:
    api = public_api()

    def fetch(request: Any) -> Any:
        raise RuntimeError("fetch boom")

    with api.Bash(fetch=fetch) as bash:
        result = bash.exec("curl -s https://example.com")

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == ""


def test_async_bash_fetch_callback_failure_is_returned_as_command_result() -> None:
    api = public_api()

    async def exercise() -> None:
        async def fetch(request: Any) -> Any:
            raise RuntimeError("fetch boom")

        async with api.AsyncBash(fetch=fetch) as bash:
            result = await bash.exec("curl -s https://example.com")

        assert result.exit_code == 1
        assert result.stdout == ""
        assert result.stderr == ""

    asyncio.run(exercise())


def test_bash_logger_callback_failure_closes_bridge() -> None:
    api = public_api()

    class BoomLogger:
        def info(self, message: str, data: dict[str, object] | None = None) -> None:
            raise RuntimeError("logger boom")

        def debug(self, message: str, data: dict[str, object] | None = None) -> None:
            raise RuntimeError("logger boom")

    with api.Bash(logger=BoomLogger()) as bash:
        with pytest.raises(RuntimeError, match="logger boom"):
            bash.exec("echo hi")
        assert bash.closed is True


def test_bash_trace_callback_failure_closes_bridge() -> None:
    api = public_api()

    def trace(event: Any) -> None:
        raise RuntimeError("trace boom")

    with api.Bash(files={"/workspace/a.txt": "a\n"}, cwd="/workspace", trace=trace) as bash:
        with pytest.raises(RuntimeError, match="trace boom"):
            bash.exec("find . -maxdepth 1 -type f | sort")
        assert bash.closed is True


def test_bash_coverage_callback_failure_closes_bridge() -> None:
    api = public_api()

    class BoomCoverage:
        def hit(self, feature: str) -> None:
            raise RuntimeError("coverage boom")

    with api.Bash(coverage=BoomCoverage()) as bash:
        with pytest.raises(RuntimeError, match="coverage boom"):
            bash.exec("echo hi")
        assert bash.closed is True


def test_async_bash_logger_callback_failure_closes_bridge() -> None:
    api = public_api()

    class BoomLogger:
        async def info(self, message: str, data: dict[str, object] | None = None) -> None:
            raise RuntimeError("logger boom")

        async def debug(self, message: str, data: dict[str, object] | None = None) -> None:
            raise RuntimeError("logger boom")

    async def exercise() -> None:
        async with api.AsyncBash(logger=BoomLogger()) as bash:
            with pytest.raises(RuntimeError, match="logger boom"):
                await bash.exec("echo hi")
            assert bash.closed is True

    asyncio.run(exercise())


def test_async_bash_trace_callback_failure_closes_bridge() -> None:
    api = public_api()

    async def exercise() -> None:
        async def trace(event: Any) -> None:
            raise RuntimeError("trace boom")

        async with api.AsyncBash(files={"/workspace/a.txt": "a\n"}, cwd="/workspace", trace=trace) as bash:
            with pytest.raises(RuntimeError, match="trace boom"):
                await bash.exec("find . -maxdepth 1 -type f | sort")
            assert bash.closed is True

    asyncio.run(exercise())


def test_async_bash_coverage_callback_failure_closes_bridge() -> None:
    api = public_api()

    class BoomCoverage:
        async def hit(self, feature: str) -> None:
            raise RuntimeError("coverage boom")

    async def exercise() -> None:
        async with api.AsyncBash(coverage=BoomCoverage()) as bash:
            with pytest.raises(RuntimeError, match="coverage boom"):
                await bash.exec("echo hi")
            assert bash.closed is True

    asyncio.run(exercise())


def test_bash_exec_waits_for_defense_callback_completion(tmp_path: Path) -> None:
    api = public_api()
    worker = tmp_path / "defense-wait-worker.py"
    write_fake_backend(worker, mode="defense_violation_event")
    started = threading.Event()
    release = threading.Event()
    done = threading.Event()
    result_holder: dict[str, Any] = {}

    def on_violation(violation: Any) -> None:
        started.set()
        assert release.wait(timeout=2)

    with api.Bash(
        node_command=fake_node_command(worker),
        defense_in_depth=api.DefenseInDepthConfig(on_violation=on_violation),
    ) as bash:

        def run_exec() -> None:
            result_holder["result"] = bash.exec("printf ok")
            done.set()

        thread = threading.Thread(target=run_exec, daemon=True)
        thread.start()
        assert started.wait(timeout=2)
        assert not done.wait(timeout=0.1)
        release.set()
        thread.join(timeout=2)

    result = result_holder["result"]
    assert result.stdout == "ok\n"
    assert done.is_set()


def test_async_bash_exec_waits_for_defense_callback_completion(tmp_path: Path) -> None:
    api = public_api()
    worker = tmp_path / "async-defense-wait-worker.py"
    write_fake_backend(worker, mode="defense_violation_event")

    async def exercise() -> None:
        started = asyncio.Event()
        release = asyncio.Event()

        async def on_violation(violation: Any) -> None:
            started.set()
            await release.wait()

        async with api.AsyncBash(
            node_command=fake_node_command(worker),
            defense_in_depth=api.DefenseInDepthConfig(on_violation=on_violation),
        ) as bash:
            task = asyncio.create_task(bash.exec("printf ok"))
            await asyncio.wait_for(started.wait(), timeout=2)
            assert not task.done()
            release.set()
            result = await asyncio.wait_for(task, timeout=2)

        assert result.stdout == "ok\n"

    asyncio.run(exercise())


def test_bash_defense_callback_failure_closes_bridge(tmp_path: Path) -> None:
    api = public_api()
    worker = tmp_path / "defense-boom-worker.py"
    write_fake_backend(worker, mode="defense_violation_event")

    def on_violation(violation: Any) -> None:
        raise RuntimeError("defense boom")

    with api.Bash(
        node_command=fake_node_command(worker),
        defense_in_depth=api.DefenseInDepthConfig(on_violation=on_violation),
    ) as bash:
        with pytest.raises(RuntimeError, match="defense boom"):
            bash.exec("printf ok")
        assert bash.closed is True


def test_async_bash_defense_callback_failure_closes_bridge(tmp_path: Path) -> None:
    api = public_api()
    worker = tmp_path / "async-defense-boom-worker.py"
    write_fake_backend(worker, mode="defense_violation_event")

    async def exercise() -> None:
        async def on_violation(violation: Any) -> None:
            raise RuntimeError("defense boom")

        async with api.AsyncBash(
            node_command=fake_node_command(worker),
            defense_in_depth=api.DefenseInDepthConfig(on_violation=on_violation),
        ) as bash:
            with pytest.raises(RuntimeError, match="defense boom"):
                await bash.exec("printf ok")
            assert bash.closed is True

    asyncio.run(exercise())


def test_bash_options_to_wire_rejects_bridge_only_option_hooks() -> None:
    api = public_api()

    def fetch(request: Any) -> Any:
        return {"status": 200, "body": "ok"}

    def trace(event: Any) -> None:
        return None

    def on_violation(violation: Any) -> None:
        return None

    cases = [
        (
            api.BashOptions(fetch=fetch),
            "Custom fetch callbacks require bridge-aware initialization",
        ),
        (
            api.BashOptions(logger=_RecorderLogger()),
            "Logger callbacks require bridge-aware initialization",
        ),
        (
            api.BashOptions(trace=trace),
            "Trace callbacks require bridge-aware initialization",
        ),
        (
            api.BashOptions(coverage=_CoverageWriter()),
            "Coverage writers require bridge-aware initialization",
        ),
        (
            api.BashOptions(defense_in_depth=api.DefenseInDepthConfig(on_violation=on_violation)),
            "Defense violation callbacks require bridge-aware initialization",
        ),
    ]

    for options, message in cases:
        with pytest.raises(ValueError, match=message):
            options.to_wire()


def test_bash_defense_in_depth_callback_receives_worker_violation_event(tmp_path: Path) -> None:
    api = public_api()
    worker = tmp_path / "defense-violation-worker.py"
    write_fake_backend(worker, mode="defense_violation_event")
    violations: list[Any] = []

    with api.Bash(
        node_command=fake_node_command(worker),
        defense_in_depth=api.DefenseInDepthConfig(on_violation=violations.append),
    ) as bash:
        result = bash.exec("printf ok")

    assert result.stdout == "ok\n"
    assert len(violations) == 1
    violation = violations[0]
    assert violation.type == "function_constructor"
    assert violation.message == "blocked Function constructor"
    assert violation.path == "globalThis.Function"
    assert violation.execution_id == "fake-exec"


def test_async_bash_defense_in_depth_callback_receives_worker_violation_event(tmp_path: Path) -> None:
    api = public_api()
    worker = tmp_path / "async-defense-violation-worker.py"
    write_fake_backend(worker, mode="defense_violation_event")

    async def exercise() -> None:
        violations: list[Any] = []
        async with api.AsyncBash(
            node_command=fake_node_command(worker),
            defense_in_depth=api.DefenseInDepthConfig(on_violation=violations.append),
        ) as bash:
            result = await bash.exec("printf ok")

        assert result.stdout == "ok\n"
        assert len(violations) == 1
        violation = violations[0]
        assert violation.type == "function_constructor"
        assert violation.message == "blocked Function constructor"
        assert violation.path == "globalThis.Function"
        assert violation.execution_id == "fake-exec"

    asyncio.run(exercise())
