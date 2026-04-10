from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
from pytest import MonkeyPatch

from tests.support.harness import ROOT, public_api

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

    with Bash(javascript=JavaScriptConfig(bootstrap="globalThis.prefix = 'bootstrapped';")) as bash:
        result = bash.exec("js-exec -c 'console.log(globalThis.prefix + \":\" + (2 + 3))'", timeout=60)

    assert result.exit_code == 0
    assert result.stdout == "bootstrapped:5\n"
    assert result.stderr == ""


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
