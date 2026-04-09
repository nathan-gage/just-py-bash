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
            "cat hello.txt",
            "hello from just-py-bash",
            "ls -1",
            "hello.txt",
            "note.txt",
            "read_text('note.txt')",
            "written from Python",
        ),
    ),
    ExampleCase(
        script=Path("examples/quickstart_async.py"),
        required_fragments=(
            "cat note.txt",
            "hello from async just-py-bash",
            "cwd=/workspace",
        ),
        required_patterns=(r"env vars available=\d+",),
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
]


def run_example(case: ExampleCase) -> subprocess.CompletedProcess[str]:
    uv = shutil.which("uv")
    if uv is None:  # pragma: no cover
        raise RuntimeError("uv executable is required to run example smoke tests")

    return subprocess.run(
        [uv, "run", "--with-editable", "./just_py_bash", "python", str(case.script)],
        cwd=ROOT,
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize("case", CASES, ids=[case.script.stem for case in CASES])
def test_non_network_examples_run_from_repo_root(case: ExampleCase) -> None:
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


def test_network_example_is_documented_as_optional_only() -> None:
    readme = (ROOT / "examples" / "README.md").read_text(encoding="utf-8")

    assert "Optional example:" in readme
    assert "network_access.py" in readme
    assert "outbound internet" in readme
