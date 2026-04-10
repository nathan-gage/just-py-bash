from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
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
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
PTY_TIMEOUT_SECONDS = 5.0
InteractivePredicate = Callable[[str], bool]
InteractiveStep = tuple[bytes, InteractivePredicate]


@dataclass(slots=True, frozen=True)
class InteractiveSessionResult:
    returncode: int
    transcript: str


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


def backend_env_missing_cli_assets(tmp_path: Path) -> dict[str, str]:
    runtime_root = tmp_path / "fake-runtime"
    (runtime_root / "dist").mkdir(parents=True)
    (runtime_root / "package.json").write_text('{"name":"just-bash","version":"1.0.0"}\n', encoding="utf-8")
    (runtime_root / "dist" / "index.js").write_text("export {};\n", encoding="utf-8")
    return {
        "JUST_BASH_JS_ENTRY": str(runtime_root / "dist" / "index.js"),
        "JUST_BASH_PACKAGE_JSON": str(runtime_root / "package.json"),
    }


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


def popen_source_cli(
    *args: str,
    cwd: Path | None = None,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.Popen[str]:
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    pythonpath = os.pathsep.join(str(entry) for entry in [PACKAGE_SRC, *existing_pythonpath_entries(env)])
    env["PYTHONPATH"] = pythonpath
    return subprocess.Popen(
        [sys.executable, "-c", CLI_BOOTSTRAP, *args],
        cwd=ROOT if cwd is None else cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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


def popen_upstream_cli(*args: str, cwd: Path | None = None) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [*resolve_node_command(), str(UPSTREAM_CLI_ENTRY), *args],
        cwd=ROOT if cwd is None else cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def normalize_terminal_output(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")
    text = ANSI_ESCAPE_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


def _has_shell_prompt(text: str) -> bool:
    return text.endswith("$ ")


def _contains_exit_line(text: str) -> bool:
    return "exit\n" in text


def _contains_goodbye(text: str) -> bool:
    return "Goodbye!" in text


def _read_pty_until(
    master_fd: int,
    process: subprocess.Popen[bytes],
    predicate: InteractivePredicate,
    *,
    timeout_seconds: float = PTY_TIMEOUT_SECONDS,
) -> bytes:
    import select

    end = time.monotonic() + timeout_seconds
    chunks = bytearray()
    while time.monotonic() < end:
        ready, _, _ = select.select([master_fd], [], [], 0.05)
        if ready:
            try:
                chunk = os.read(master_fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            chunks.extend(chunk)
            if predicate(normalize_terminal_output(bytes(chunks))):
                return bytes(chunks)
            continue

        if process.poll() is not None:
            if predicate(normalize_terminal_output(bytes(chunks))):
                return bytes(chunks)
            break

    normalized = normalize_terminal_output(bytes(chunks))
    raise AssertionError(f"Timed out waiting for PTY output. Saw:\n{normalized}")


def _drain_pty(master_fd: int) -> bytes:
    import select

    chunks = bytearray()
    while True:
        ready, _, _ = select.select([master_fd], [], [], 0.05)
        if not ready:
            break
        try:
            chunk = os.read(master_fd, 4096)
        except OSError:
            break
        if not chunk:
            break
        chunks.extend(chunk)
    return bytes(chunks)


def run_interactive_process(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None,
    steps: list[InteractiveStep],
) -> InteractiveSessionResult:
    import pty

    master_fd, slave_fd = pty.openpty()
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        close_fds=True,
    )
    os.close(slave_fd)

    transcript = bytearray()
    try:
        transcript.extend(_read_pty_until(master_fd, process, _has_shell_prompt))
        for payload, predicate in steps:
            os.write(master_fd, payload)
            transcript.extend(_read_pty_until(master_fd, process, predicate))

        process.wait(timeout=PTY_TIMEOUT_SECONDS)
        transcript.extend(_drain_pty(master_fd))
        return InteractiveSessionResult(
            returncode=int(process.returncode),
            transcript=normalize_terminal_output(bytes(transcript)),
        )
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master_fd)


def run_source_shell_cli_interactive(
    *args: str,
    cwd: Path,
    env_overrides: dict[str, str] | None = None,
    steps: list[InteractiveStep],
) -> InteractiveSessionResult:
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    pythonpath = os.pathsep.join(str(entry) for entry in [PACKAGE_SRC, *existing_pythonpath_entries(env)])
    env["PYTHONPATH"] = pythonpath
    return run_interactive_process(
        [sys.executable, "-c", SHELL_BOOTSTRAP, *args],
        cwd=cwd,
        env=env,
        steps=steps,
    )


def run_upstream_shell_cli_interactive(
    *args: str,
    cwd: Path,
    steps: list[InteractiveStep],
) -> InteractiveSessionResult:
    return run_interactive_process(
        [*resolve_node_command(), str(UPSTREAM_SHELL_ENTRY), *args],
        cwd=cwd,
        env=None,
        steps=steps,
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


def test_cli_delegates_help_to_upstream() -> None:
    python_completed = run_source_cli("--help", env_overrides=packaged_backend_env())
    upstream_completed = run_upstream_cli("--help")

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


def test_cli_delegates_allow_write_flag_to_upstream(tmp_path: Path) -> None:
    args = ("-c", "echo write-ok > out.txt && cat out.txt", "--allow-write")
    python_completed = run_source_cli(*args, cwd=tmp_path, env_overrides=packaged_backend_env())
    upstream_completed = run_upstream_cli(*args, cwd=tmp_path)

    assert_completed_matches_upstream(python_completed, upstream_completed)


def test_cli_delegates_errexit_flag_to_upstream() -> None:
    args = ("-e", "-c", "false; echo nope")
    python_completed = run_source_cli(*args, env_overrides=packaged_backend_env())
    upstream_completed = run_upstream_cli(*args)

    assert_completed_matches_upstream(python_completed, upstream_completed)
    assert python_completed.returncode == 1


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


@pytest.mark.skipif(os.name == "nt", reason="signal parity differs on Windows")
def test_cli_propagates_sigint_without_python_traceback() -> None:
    python_process = popen_source_cli("-c", "sleep 30", env_overrides=packaged_backend_env())
    upstream_process = popen_upstream_cli("-c", "sleep 30")

    time.sleep(1.0)
    python_process.send_signal(signal.SIGINT)
    upstream_process.send_signal(signal.SIGINT)

    python_stdout, python_stderr = python_process.communicate(timeout=PTY_TIMEOUT_SECONDS)
    upstream_stdout, upstream_stderr = upstream_process.communicate(timeout=PTY_TIMEOUT_SECONDS)

    assert python_process.returncode == upstream_process.returncode
    assert python_stdout == upstream_stdout
    assert python_stderr == upstream_stderr
    assert "Traceback" not in python_stderr


def test_cli_propagates_unknown_option_error_to_upstream() -> None:
    python_completed = run_source_cli("--definitely-not-a-flag", env_overrides=packaged_backend_env())
    upstream_completed = run_upstream_cli("--definitely-not-a-flag")

    assert_completed_matches_upstream(python_completed, upstream_completed)


def test_cli_reports_missing_cli_assets_cleanly(tmp_path: Path) -> None:
    completed = run_source_cli("--help", env_overrides=backend_env_missing_cli_assets(tmp_path))

    assert completed.returncode == 1
    assert completed.stdout == ""
    assert "Traceback" not in completed.stderr
    assert "Could not find the upstream just-bash CLI asset required for delegation" in completed.stderr
    assert "dist/bin/just-bash.js" in completed.stderr


def test_cli_reports_invalid_node_command_cleanly() -> None:
    missing_node = ROOT / ".pytest-node-does-not-exist" / ("node.exe" if os.name == "nt" else "node")
    completed = run_source_cli(
        "--help",
        env_overrides={
            **packaged_backend_env(),
            "JUST_BASH_NODE": str(missing_node),
        },
    )

    assert completed.returncode == 1
    assert completed.stdout == ""
    assert "Traceback" not in completed.stderr
    assert "Could not launch the upstream just-bash CLI" in completed.stderr


def test_shell_cli_delegates_help_to_upstream() -> None:
    python_completed = run_source_shell_cli("--help", env_overrides=packaged_backend_env())
    upstream_completed = run_upstream_shell_cli("--help")

    assert_completed_matches_upstream(python_completed, upstream_completed)


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


@pytest.mark.skipif(os.name == "nt", reason="interactive PTY tests require POSIX")
def test_shell_cli_interactive_session_matches_upstream(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    subdir = workspace / "sub"
    subdir.mkdir(parents=True)
    (subdir / "note.txt").write_text("shell-note\n", encoding="utf-8")

    steps: list[InteractiveStep] = [
        (b"pwd\n", _has_shell_prompt),
        (b"cat note.txt\n", _has_shell_prompt),
        (b"echo write-ok > created.txt && cat created.txt\n", _has_shell_prompt),
        (b"exit\n", _contains_exit_line),
    ]
    python_result = run_source_shell_cli_interactive(
        "--cwd",
        "/sub",
        cwd=workspace,
        env_overrides=packaged_backend_env(),
        steps=steps,
    )
    upstream_result = run_upstream_shell_cli_interactive(
        "--cwd",
        "/sub",
        cwd=workspace,
        steps=steps,
    )

    assert python_result == upstream_result
    assert "Virtual Shell v1.0" in python_result.transcript
    assert "user@virtual:/sub$" in python_result.transcript
    assert "shell-note" in python_result.transcript
    assert "write-ok" in python_result.transcript


@pytest.mark.skipif(os.name == "nt", reason="interactive PTY tests require POSIX")
def test_shell_cli_interactive_ctrl_c_matches_upstream(tmp_path: Path) -> None:
    steps: list[InteractiveStep] = [
        (b"\x03", _has_shell_prompt),
        (b"pwd\n", _has_shell_prompt),
        (b"exit\n", _contains_exit_line),
    ]
    python_result = run_source_shell_cli_interactive(
        cwd=tmp_path,
        env_overrides=packaged_backend_env(),
        steps=steps,
    )
    upstream_result = run_upstream_shell_cli_interactive(
        cwd=tmp_path,
        steps=steps,
    )

    assert python_result == upstream_result
    assert "^C" in python_result.transcript
    assert "user@virtual:~$" in python_result.transcript


@pytest.mark.skipif(os.name == "nt", reason="interactive PTY tests require POSIX")
def test_shell_cli_interactive_eof_matches_upstream(tmp_path: Path) -> None:
    steps: list[InteractiveStep] = [(b"\x04", _contains_goodbye)]
    python_result = run_source_shell_cli_interactive(
        cwd=tmp_path,
        env_overrides=packaged_backend_env(),
        steps=steps,
    )
    upstream_result = run_upstream_shell_cli_interactive(
        cwd=tmp_path,
        steps=steps,
    )

    assert python_result == upstream_result
    assert "Goodbye!" in python_result.transcript


def test_shell_cli_reports_missing_cli_assets_cleanly(tmp_path: Path) -> None:
    completed = run_source_shell_cli("--help", env_overrides=backend_env_missing_cli_assets(tmp_path))

    assert completed.returncode == 1
    assert completed.stdout == ""
    assert "Traceback" not in completed.stderr
    assert "Could not find the upstream just-bash CLI asset required for delegation" in completed.stderr
    assert "dist/bin/shell/shell.js" in completed.stderr
