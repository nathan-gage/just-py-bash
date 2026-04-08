from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from tests.support.harness import ROOT, public_api

pytestmark = pytest.mark.contract


@pytest.fixture(scope="module")
def packaged_runtime_artifacts(tmp_path_factory: pytest.TempPathFactory) -> tuple[str, str]:
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
