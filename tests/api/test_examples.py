from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

pytestmark = pytest.mark.api

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class ExampleCase:
    script: Path
    required_fragments: tuple[str, ...] = ()
    required_patterns: tuple[str, ...] = ()


CASES = [
    ExampleCase(
        script=Path("examples/quickstart_sync.py"),
        required_fragments=(
            "shell state resets, filesystem persists",
            "name=missing cwd=/workspace file=hello from the shared filesystem",
            "read_text('note.txt')",
            "written via bash.fs",
        ),
    ),
    ExampleCase(
        script=Path("examples/quickstart_async.py"),
        required_fragments=(
            "shell state resets, filesystem persists",
            "name=missing cwd=/workspace file=hello from async shared filesystem",
            "read_text('note.txt')",
            "written via async bash.fs",
        ),
    ),
    ExampleCase(
        script=Path("examples/custom_commands_sync.py"),
        required_fragments=(
            "=== Python Custom Commands Demo ===",
            "2. Format JSON from file:",
            '"name": "Alice"',
            "5. Count words in lorem ipsum:",
            "Words: 19",
            "8. Complex pipeline:",
            "Words: 52",
        ),
    ),
    ExampleCase(
        script=Path("examples/custom_commands_async.py"),
        required_fragments=(
            "=== Async Custom Command Demo ===",
            "[summary] words=3 body=one two three",
            "[MEMO] WORDS=2 BODY=ALPHA BETA",
        ),
    ),
    ExampleCase(
        script=Path("examples/configuration_and_runtimes.py"),
        required_fragments=(
            "=== Per-exec env and cwd overrides ===",
            "hello from /workspace",
            "override from /tmp",
            "=== replace_env ===",
            "this / unset",
            "=== stdin and args ===",
            "hello from stdin",
            "2:beta",
            "=== raw_script ===",
            "  indented",
            "=== python runtime ===",
            "=== javascript runtime ===",
        ),
        required_patterns=(
            r"(^10$|python unavailable in this backend build:)",
            r"(^bootstrapped:5$|js-exec unavailable in this backend build:)",
        ),
    ),
    ExampleCase(
        script=Path("examples/filesystem_surfaces.py"),
        required_fragments=(
            "=== Filesystem surfaces ===",
            "exists(meta.txt)=True",
            "mode=0o640",
            "mtime=2024-01-02T03:04:05+00:00",
            "lazy=lazy content",
            "link=copy.txt",
            "copy=from bash.fs",
        ),
        required_patterns=(r"realpath=.*/copy\.txt",),
    ),
    ExampleCase(
        script=Path("examples/network_access.py"),
        required_fragments=(
            "=== Network access ===",
            "GET /inspect from-network-config",
            "POST alpha=beta",
        ),
    ),
    ExampleCase(
        script=Path("examples/option_hooks.py"),
        required_fragments=(
            "=== Option hooks ===",
            "fetch=hello from fetch",
            "fetch_request=GET:https://example.com",
            "trace_has_find=True",
            "logger_has_exec=True",
            "logger_has_exit=True",
            "find_result=./seed.txt",
            "defense_blocked=True",
        ),
        required_patterns=(r"coverage_hits=\d+", r"violations_recorded=\d+"),
    ),
    ExampleCase(
        script=Path("examples/parser_and_command_registry.py"),
        required_fragments=(
            "=== Command registry helpers ===",
            "builtins include echo=True",
            "network commands=['curl']",
            "ast.type=Script",
            "serialized=echo hello | grep h && printf 'done",
        ),
    ),
    ExampleCase(
        script=Path("examples/transforms.py"),
        required_fragments=(
            "=== Standalone transform pipeline ===",
            "tee /tmp/logs/2024-01-15T10-30-45.123Z-000-echo.stdout.txt",
            "'commands': ['echo', 'exit', 'grep', 'tee']",
            "=== Session-integrated transform plugins ===",
            "{'commands': ['echo', 'grep']}",
        ),
    ),
    ExampleCase(
        script=Path("examples/sandbox.py"),
        required_fragments=(
            "=== Sandbox API ===",
            "inline exit=0 stdout=script says hi",
            "captured stdout=script says hi",
            "detached exit=0 stdout=hello from sandbox",
            "read_back=hello from sandbox",
        ),
    ),
    ExampleCase(
        script=Path("examples/security_helpers.py"),
        required_fragments=(
            "=== Security helpers ===",
            "total=1",
            "summary=eval:1:globalThis.eval",
            "stored_stack=None",
            "error_message=security violation",
            "error_type=eval",
        ),
    ),
]


def run_example(case: ExampleCase) -> subprocess.CompletedProcess[str]:
    uv = shutil.which("uv")
    if uv is None:  # pragma: no cover
        raise RuntimeError("uv executable is required to run example smoke tests")

    env = os.environ.copy()
    env.pop("JUST_BASH_JS_ENTRY", None)
    env.pop("JUST_BASH_PACKAGE_JSON", None)

    return subprocess.run(
        [uv, "run", "--quiet", "--with-editable", "./just_py_bash", "python", str(case.script)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize("case", CASES, ids=[case.script.stem for case in CASES])
def test_examples_run_from_repo_root(case: ExampleCase) -> None:
    completed = run_example(case)

    assert completed.returncode == 0, (
        f"example {case.script} failed\nstdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
    )
    assert completed.stderr == ""
    assert "Traceback" not in completed.stdout

    for fragment in case.required_fragments:
        assert fragment in completed.stdout

    for pattern in case.required_patterns:
        assert re.search(pattern, completed.stdout, re.MULTILINE) is not None


def test_network_example_is_documented_as_smoke_tested() -> None:
    readme = (ROOT / "examples" / "README.md").read_text(encoding="utf-8")

    assert "network_access.py" in readme
    assert "All listed examples are smoke-tested" in readme
    assert "local HTTP fixture" in readme
