from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.support.harness import ROOT, public_api

pytestmark = [pytest.mark.api, pytest.mark.xdist_group(name="runtime_contracts")]

PACKAGE_SRC = ROOT / "just_py_bash" / "src"
PACKAGED_BACKEND_ROOT = PACKAGE_SRC / "just_bash" / "_vendor" / "just-bash"
CLI_BOOTSTRAP = "from just_bash import main; raise SystemExit(main())"


def existing_pythonpath_entries(env: dict[str, str]) -> list[Path]:
    raw = env.get("PYTHONPATH", "")
    if not raw:
        return []
    return [Path(entry) for entry in raw.split(os.pathsep) if entry]


def packaged_backend_env() -> dict[str, str]:
    for relative in (Path("dist/index.js"), Path("dist/bundle/index.js")):
        candidate = PACKAGED_BACKEND_ROOT / relative
        if candidate.exists():
            return {
                "JUST_BASH_JS_ENTRY": str(candidate),
                "JUST_BASH_PACKAGE_JSON": str(PACKAGED_BACKEND_ROOT / "package.json"),
            }
    raise AssertionError(f"Packaged backend entrypoint missing under {PACKAGED_BACKEND_ROOT}")


def run_source_cli(
    *args: str,
    stdin: str | None = None,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    pythonpath = os.pathsep.join(str(entry) for entry in [PACKAGE_SRC, *existing_pythonpath_entries(env)])
    env["PYTHONPATH"] = pythonpath
    return subprocess.run(
        [sys.executable, "-c", CLI_BOOTSTRAP, *args],
        cwd=ROOT,
        env=env,
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_prints_version() -> None:
    completed = run_source_cli("--version")

    assert completed.returncode == 0
    assert completed.stdout.strip() == public_api().__version__
    assert completed.stderr == ""


def test_cli_respects_cwd_and_python_runtime_flag() -> None:
    completed = run_source_cli(
        "--cwd",
        "/workspace",
        "--python",
        'python -c "import os; print(os.getcwd())"',
        env_overrides=packaged_backend_env(),
    )

    assert completed.returncode == 0
    assert completed.stdout == "/workspace\n"
    assert completed.stderr == ""


def test_cli_reads_piped_stdin() -> None:
    completed = run_source_cli("cat", stdin="from-stdin\n")

    assert completed.returncode == 0
    assert completed.stdout == "from-stdin\n"
    assert completed.stderr == ""


def test_cli_propagates_exec_timeout_and_exit_code() -> None:
    timed_out = run_source_cli("--timeout", "0.01", "while true; do sleep 1; done")
    failed = run_source_cli("false")

    assert timed_out.returncode == 124
    assert timed_out.stdout == ""
    assert failed.returncode == 1
    assert failed.stdout == ""
