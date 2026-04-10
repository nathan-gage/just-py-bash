from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.support.harness import ROOT, resolve_node_command

pytestmark = [pytest.mark.api, pytest.mark.xdist_group(name="runtime_contracts")]

PACKAGE_SRC = ROOT / "just_py_bash" / "src"
PACKAGED_BACKEND_ROOT = PACKAGE_SRC / "just_bash" / "_vendor" / "just-bash"
UPSTREAM_CLI_ENTRY = ROOT / "vendor" / "just-bash" / "dist" / "bin" / "just-bash.js"
UPSTREAM_SHELL_ENTRY = ROOT / "vendor" / "just-bash" / "dist" / "bin" / "shell" / "shell.js"
CLI_BOOTSTRAP = "from just_bash import main; raise SystemExit(main())"
SHELL_BOOTSTRAP = "from just_bash import shell_main; raise SystemExit(shell_main())"


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
    cwd: Path | None = None,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    pythonpath = os.pathsep.join(str(entry) for entry in [PACKAGE_SRC, *existing_pythonpath_entries(env)])
    env["PYTHONPATH"] = pythonpath
    return subprocess.run(
        [sys.executable, "-c", CLI_BOOTSTRAP, *args],
        cwd=ROOT if cwd is None else cwd,
        env=env,
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
    )


def run_source_shell_cli(
    *args: str,
    stdin: str | None = None,
    cwd: Path | None = None,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    pythonpath = os.pathsep.join(str(entry) for entry in [PACKAGE_SRC, *existing_pythonpath_entries(env)])
    env["PYTHONPATH"] = pythonpath
    return subprocess.run(
        [sys.executable, "-c", SHELL_BOOTSTRAP, *args],
        cwd=ROOT if cwd is None else cwd,
        env=env,
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
    )


def run_upstream_cli(
    *args: str,
    stdin: str | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*resolve_node_command(), str(UPSTREAM_CLI_ENTRY), *args],
        cwd=ROOT if cwd is None else cwd,
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
    )


def run_upstream_shell_cli(
    *args: str,
    stdin: str | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*resolve_node_command(), str(UPSTREAM_SHELL_ENTRY), *args],
        cwd=ROOT if cwd is None else cwd,
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
    )


def assert_completed_matches_upstream(
    python_completed: subprocess.CompletedProcess[str],
    upstream_completed: subprocess.CompletedProcess[str],
) -> None:
    assert python_completed.returncode == upstream_completed.returncode
    assert python_completed.stdout == upstream_completed.stdout
    assert python_completed.stderr == upstream_completed.stderr


def test_cli_delegates_version_to_upstream() -> None:
    python_completed = run_source_cli("-v", env_overrides=packaged_backend_env())
    upstream_completed = run_upstream_cli("-v")

    assert_completed_matches_upstream(python_completed, upstream_completed)


def test_cli_delegates_inline_script_execution_to_upstream() -> None:
    python_completed = run_source_cli("-c", "printf inline", env_overrides=packaged_backend_env())
    upstream_completed = run_upstream_cli("-c", "printf inline")

    assert_completed_matches_upstream(python_completed, upstream_completed)


def test_cli_delegates_stdin_script_execution_to_upstream() -> None:
    python_completed = run_source_cli(stdin="echo hello from stdin\n", env_overrides=packaged_backend_env())
    upstream_completed = run_upstream_cli(stdin="echo hello from stdin\n")

    assert_completed_matches_upstream(python_completed, upstream_completed)


def test_cli_delegates_root_and_cwd_flags_to_upstream(tmp_path: Path) -> None:
    root = tmp_path / "project"
    workspace = root / "sub"
    workspace.mkdir(parents=True)
    (workspace / "note.txt").write_text("root-note\n", encoding="utf-8")

    args = (
        "-c",
        "pwd; cat note.txt",
        "--root",
        str(root),
        "--cwd",
        "/home/user/project/sub",
    )
    python_completed = run_source_cli(*args, env_overrides=packaged_backend_env())
    upstream_completed = run_upstream_cli(*args)

    assert_completed_matches_upstream(python_completed, upstream_completed)


def test_cli_delegates_json_output_to_upstream() -> None:
    python_completed = run_source_cli("-c", "echo hello", "--json", env_overrides=packaged_backend_env())
    upstream_completed = run_upstream_cli("-c", "echo hello", "--json")

    assert_completed_matches_upstream(python_completed, upstream_completed)


def test_cli_delegates_script_file_execution_to_upstream(tmp_path: Path) -> None:
    script_path = tmp_path / "script.sh"
    script_path.write_text("printf file-script", encoding="utf-8")

    python_completed = run_source_cli("./script.sh", cwd=tmp_path, env_overrides=packaged_backend_env())
    upstream_completed = run_upstream_cli("./script.sh", cwd=tmp_path)

    assert_completed_matches_upstream(python_completed, upstream_completed)


def test_cli_propagates_upstream_failure_exit_code() -> None:
    python_completed = run_source_cli("-c", "false", env_overrides=packaged_backend_env())
    upstream_completed = run_upstream_cli("-c", "false")

    assert_completed_matches_upstream(python_completed, upstream_completed)
    assert python_completed.returncode == 1


def test_shell_cli_delegates_noninteractive_execution_to_upstream(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("shell-note\n", encoding="utf-8")

    python_completed = run_source_shell_cli(
        "--cwd",
        "/",
        stdin="pwd\ncat note.txt\n",
        cwd=tmp_path,
        env_overrides=packaged_backend_env(),
    )
    upstream_completed = run_upstream_shell_cli(
        "--cwd",
        "/",
        stdin="pwd\ncat note.txt\n",
        cwd=tmp_path,
    )

    assert_completed_matches_upstream(python_completed, upstream_completed)
