from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pytest
from pytest import MonkeyPatch

from tests.support.harness import ROOT, public_api

if TYPE_CHECKING:
    from just_bash import UnsupportedRuntimeConfigurationError

pytestmark = [pytest.mark.contract, pytest.mark.xdist_group(name="runtime_contracts")]


@pytest.fixture(scope="module")
def packaged_runtime_artifacts(tmp_path_factory: pytest.TempPathFactory) -> tuple[str, str]:
    prebuilt_js_entry = os.environ.get("JUST_BASH_TEST_PACKAGED_JS_ENTRY")
    prebuilt_package_json = os.environ.get("JUST_BASH_TEST_PACKAGED_PACKAGE_JSON")
    if prebuilt_js_entry and prebuilt_package_json:
        js_entry = Path(prebuilt_js_entry)
        package_json = Path(prebuilt_package_json)
        if not js_entry.exists():
            raise AssertionError(f"Configured packaged runtime entrypoint missing: {js_entry}")
        if not package_json.exists():
            raise AssertionError(f"Configured packaged runtime package.json missing: {package_json}")
        return str(js_entry), str(package_json)

    runtime_root = tmp_path_factory.mktemp("packaged-runtime") / "just-bash"
    env = os.environ.copy()
    env["JUST_BASH_PACKAGED_RUNTIME_OUT_DIR"] = str(runtime_root)
    completed = subprocess.run(
        ["bash", str(ROOT / "just_py_bash" / "tools" / "build_packaged_runtime.sh")],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"packaged runtime build failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )

    for relative in (Path("dist/index.js"), Path("dist/bundle/index.js")):
        candidate = runtime_root / relative
        if candidate.exists():
            return str(candidate), str(runtime_root / "package.json")

    raise AssertionError(f"packaged runtime entrypoint missing under {runtime_root}")


def use_packaged_runtime(monkeypatch: MonkeyPatch, packaged_runtime_artifacts: tuple[str, str]) -> None:
    js_entry, package_json = packaged_runtime_artifacts
    monkeypatch.setenv("JUST_BASH_JS_ENTRY", js_entry)
    monkeypatch.setenv("JUST_BASH_PACKAGE_JSON", package_json)


def assert_unsupported_javascript_runtime(error: Exception) -> None:
    api = public_api()
    assert isinstance(error, api.UnsupportedRuntimeConfigurationError)
    typed_error = cast("UnsupportedRuntimeConfigurationError", error)
    assert typed_error.feature == "javascript"
    assert typed_error.required_version == "22.6.0"
    assert typed_error.actual_version is not None
    assert "just-py-bash[node]" in str(typed_error)
    assert "node:module.stripTypeScriptTypes" in str(typed_error)


def test_python_runtime_executes_when_enabled(
    monkeypatch: MonkeyPatch,
    packaged_runtime_artifacts: tuple[str, str],
) -> None:
    use_packaged_runtime(monkeypatch, packaged_runtime_artifacts)
    Bash = public_api().Bash

    with Bash(python=True) as bash:
        result = bash.exec('python -c "print(sum([2, 3, 5]))"', timeout=60)

    assert result.exit_code == 0
    assert result.stdout == "10\n"
    assert result.stderr == ""


def test_python_runtime_respects_execution_timeout_limit(
    monkeypatch: MonkeyPatch,
    packaged_runtime_artifacts: tuple[str, str],
) -> None:
    use_packaged_runtime(monkeypatch, packaged_runtime_artifacts)
    api = public_api()
    Bash = api.Bash
    ExecutionLimits = api.ExecutionLimits

    with Bash(
        python=True,
        execution_limits=ExecutionLimits(max_python_timeout_ms=50),
    ) as bash:
        result = bash.exec('python -c "import time; time.sleep(0.2)"', timeout=60)

    assert result.exit_code == 124
    assert "execution timeout exceeded" in result.stderr.lower()
    assert "50ms limit" in result.stderr


def test_javascript_runtime_executes_when_enabled(
    monkeypatch: MonkeyPatch,
    packaged_runtime_artifacts: tuple[str, str],
) -> None:
    use_packaged_runtime(monkeypatch, packaged_runtime_artifacts)
    api = public_api()
    Bash = api.Bash
    JavaScriptConfig = api.JavaScriptConfig

    try:
        with Bash(javascript=JavaScriptConfig(bootstrap="globalThis.prefix = 'bootstrapped';")) as bash:
            result = bash.exec("js-exec -c 'console.log(globalThis.prefix + \":\" + (2 + 3))'", timeout=60)
    except api.UnsupportedRuntimeConfigurationError as exc:
        assert_unsupported_javascript_runtime(exc)
        return

    assert result.exit_code == 0
    assert result.stdout == "bootstrapped:5\n"
    assert result.stderr == ""


def test_async_javascript_runtime_executes_when_enabled(
    monkeypatch: MonkeyPatch,
    packaged_runtime_artifacts: tuple[str, str],
) -> None:
    use_packaged_runtime(monkeypatch, packaged_runtime_artifacts)
    api = public_api()
    AsyncBash = api.AsyncBash
    JavaScriptConfig = api.JavaScriptConfig

    async def exercise() -> None:
        try:
            async with AsyncBash(javascript=JavaScriptConfig(bootstrap="globalThis.prefix = 'bootstrapped';")) as bash:
                result = await bash.exec("js-exec -c 'console.log(globalThis.prefix + \":\" + (2 + 3))'", timeout=60)
        except api.UnsupportedRuntimeConfigurationError as exc:
            assert_unsupported_javascript_runtime(exc)
            return

        assert result.exit_code == 0
        assert result.stdout == "bootstrapped:5\n"
        assert result.stderr == ""

    asyncio.run(exercise())


def test_async_javascript_runtime_exec_timeout_leaves_async_session_usable(
    monkeypatch: MonkeyPatch,
    packaged_runtime_artifacts: tuple[str, str],
) -> None:
    use_packaged_runtime(monkeypatch, packaged_runtime_artifacts)
    api = public_api()
    AsyncBash = api.AsyncBash

    async def exercise() -> None:
        try:
            async with AsyncBash(files={"/workspace/seed.txt": "seed\n"}, cwd="/workspace", javascript=True) as bash:
                result = await bash.exec("js-exec -c 'while(true){}'", timeout=0.01)
                follow_up = await bash.exec("cat seed.txt", timeout=60)
        except api.UnsupportedRuntimeConfigurationError as exc:
            assert_unsupported_javascript_runtime(exc)
            return

        assert result.stdout == ""
        if result.exit_code == 124:
            assert "execution timeout exceeded" in result.stderr
            assert "session was reset" in result.stderr
            assert result.metadata == {"timed_out": True, "timeout_ms": 10, "session_reset": True}
        else:
            assert result.exit_code == 1
            assert "interrupted" in result.stderr
        assert follow_up.stdout == "seed\n"
        assert follow_up.stderr == ""

    asyncio.run(exercise())


def test_async_packaged_runtime_fetch_hook_round_trips_through_javascript(
    monkeypatch: MonkeyPatch,
    packaged_runtime_artifacts: tuple[str, str],
) -> None:
    use_packaged_runtime(monkeypatch, packaged_runtime_artifacts)
    api = public_api()
    AsyncBash = api.AsyncBash
    FetchResult = api.FetchResult

    async def exercise() -> None:
        fetch_requests: list[tuple[str, str]] = []

        async def fetch(request: Any) -> object:
            fetch_requests.append((request.method, request.url))
            return FetchResult(
                status=200,
                status_text="OK",
                headers={"content-type": "text/plain"},
                body="hooked fetch",
                url=request.url,
            )

        try:
            async with AsyncBash(javascript=True, fetch=fetch) as bash:
                result = await bash.exec(
                    "js-exec -c \"fetch('https://example.com').then(r=>r.text()).then(t=>console.log(t))\"",
                    timeout=60,
                )
        except api.UnsupportedRuntimeConfigurationError as exc:
            assert_unsupported_javascript_runtime(exc)
            return

        assert result.exit_code == 0
        assert result.stdout == "hooked fetch\n"
        assert result.stderr == ""
        assert fetch_requests == [("GET", "https://example.com")]

    asyncio.run(exercise())


def test_async_packaged_runtime_matches_downstream_javascript_bootstrap_scenario(
    monkeypatch: MonkeyPatch,
    packaged_runtime_artifacts: tuple[str, str],
) -> None:
    use_packaged_runtime(monkeypatch, packaged_runtime_artifacts)
    api = public_api()
    AsyncBash = api.AsyncBash
    JavaScriptConfig = api.JavaScriptConfig

    async def exercise() -> None:
        try:
            async with AsyncBash(
                python=True,
                javascript=JavaScriptConfig(bootstrap="globalThis.answer = 42;"),
                commands=["echo"],
            ) as bash:
                echo_result = await bash.exec("echo allowed", timeout=60)
                cat_result = await bash.exec("cat missing.txt", timeout=60)
                python_result = await bash.exec('python -c "print(2 + 3)"', timeout=60)
                javascript_result = await bash.exec('js-exec -c "console.log(globalThis.answer)"', timeout=60)
        except api.UnsupportedRuntimeConfigurationError as exc:
            assert_unsupported_javascript_runtime(exc)
            return

        assert echo_result.stdout == "allowed\n"
        assert cat_result.exit_code == 127
        assert cat_result.stderr == "bash: cat: command not found\n"
        assert python_result.stdout == "5\n"
        assert javascript_result.stdout == "42\n"

    asyncio.run(exercise())


def test_async_packaged_runtime_matches_downstream_fetch_logger_and_coverage_scenario(
    monkeypatch: MonkeyPatch,
    packaged_runtime_artifacts: tuple[str, str],
) -> None:
    use_packaged_runtime(monkeypatch, packaged_runtime_artifacts)
    api = public_api()
    AsyncBash = api.AsyncBash
    FetchResult = api.FetchResult

    class Logger:
        def __init__(self) -> None:
            self.events: list[tuple[str, str, object | None]] = []

        def info(self, message: str, data: object | None = None) -> None:
            self.events.append(("info", message, data))

        def debug(self, message: str, data: object | None = None) -> None:
            self.events.append(("debug", message, data))

    class Coverage:
        def __init__(self) -> None:
            self.hits: list[str] = []

        def hit(self, feature: str) -> None:
            self.hits.append(feature)

    async def exercise() -> None:
        logger = Logger()
        coverage = Coverage()
        fetch_requests: list[tuple[str, str]] = []

        async def fetch(request: Any) -> object:
            fetch_requests.append((request.method, request.url))
            return FetchResult(
                status=200,
                status_text="OK",
                headers={"content-type": "text/plain"},
                body="hooked fetch",
                url=request.url,
            )

        try:
            async with AsyncBash(
                javascript=True,
                fetch=fetch,
                logger=logger,
                coverage=coverage,
            ) as bash:
                echo_result = await bash.exec("echo hello", timeout=60)
                fetch_result = await bash.exec(
                    "js-exec -c \"fetch('https://example.test/data').then(r=>r.text()).then(t=>console.log(t))\"",
                    timeout=60,
                )
        except api.UnsupportedRuntimeConfigurationError as exc:
            assert_unsupported_javascript_runtime(exc)
            return

        assert echo_result.stdout == "hello\n"
        assert fetch_result.stdout == "hooked fetch\n"
        assert fetch_requests == [("GET", "https://example.test/data")]
        assert any(level == "info" and message == "exec" for level, message, _ in logger.events)
        assert any(level == "info" and message == "exit" for level, message, _ in logger.events)
        assert any(level == "debug" and message == "stdout" for level, message, _ in logger.events)
        assert coverage.hits

    asyncio.run(exercise())


def test_packaged_runtime_option_hooks_work_with_coverage_enabled(
    monkeypatch: MonkeyPatch,
    packaged_runtime_artifacts: tuple[str, str],
) -> None:
    use_packaged_runtime(monkeypatch, packaged_runtime_artifacts)
    api = public_api()
    Bash = api.Bash
    DefenseInDepthConfig = api.DefenseInDepthConfig
    FetchResult = api.FetchResult

    class Logger:
        def __init__(self) -> None:
            self.events: list[tuple[str, str]] = []

        def info(self, message: str, data: object | None = None) -> None:
            del data
            self.events.append(("info", message))

        def debug(self, message: str, data: object | None = None) -> None:
            del data
            self.events.append(("debug", message))

    class Coverage:
        def __init__(self) -> None:
            self.hits: list[str] = []

        def hit(self, feature: str) -> None:
            self.hits.append(feature)

    logger = Logger()
    coverage = Coverage()
    trace_events: list[Any] = []
    fetch_requests: list[tuple[str, str]] = []
    violations: list[Any] = []

    def fetch(request: Any) -> object:
        fetch_requests.append((request.method, request.url))
        return FetchResult(
            status=200,
            status_text="OK",
            headers={"content-type": "text/plain"},
            body="hello from fetch\n",
            url=request.url,
        )

    with Bash(
        files={"/workspace/seed.txt": "seed\n"},
        cwd="/workspace",
        logger=logger,
        trace=trace_events.append,
        coverage=coverage,
        fetch=fetch,
        javascript=True,
        defense_in_depth=DefenseInDepthConfig(enabled=True, audit_mode=True, on_violation=violations.append),
    ) as bash:
        fetch_result = bash.exec("curl -s https://example.com")
        find_result = bash.exec("find . -maxdepth 1 -type f | sort")
        js_result = bash.exec(
            "js-exec -c \"try { new Function('return 1')(); } catch (e) { console.log(e.message); }\"",
        )

    assert fetch_result.exit_code == 0
    assert fetch_result.stdout == "hello from fetch\n"
    assert fetch_result.stderr == ""
    assert fetch_requests == [("GET", "https://example.com")]

    assert find_result.exit_code == 0
    assert find_result.stdout == "./seed.txt\n"
    assert find_result.stderr == ""
    assert any(getattr(event, "category", None) == "find" for event in trace_events)

    assert js_result.exit_code == 0
    assert "Function constructor is not allowed" in js_result.stdout
    assert js_result.stderr == ""

    assert ("info", "exec") in logger.events
    assert ("info", "exit") in logger.events
    assert coverage.hits
    assert any(hit.startswith("bash:") or hit.startswith("cmd:") for hit in coverage.hits)
