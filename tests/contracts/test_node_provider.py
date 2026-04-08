from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from tests.support.harness import ROOT

pytestmark = pytest.mark.contract


PACKAGE_SRC = ROOT / "just_py_bash" / "src"


def write_node_wrapper(path: Path, marker_path: Path, node_path: str) -> None:
    path.write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "",
                "import subprocess",
                "import sys",
                "from pathlib import Path",
                "",
                f"Path({str(marker_path)!r}).write_text('used\\n', encoding='utf-8')",
                "completed = subprocess.run(",
                f"    [{node_path!r}, *sys.argv[1:]],",
                "    check=False,",
                ")",
                "raise SystemExit(completed.returncode)",
                "",
            ],
        ),
        encoding="utf-8",
    )


def write_fake_provider(package_root: Path, wrapper_path: Path) -> None:
    provider_dir = package_root / "just_bash_bundled_runtime"
    provider_dir.mkdir(parents=True)
    provider_dir.joinpath("__init__.py").write_text(
        textwrap.dedent(
            f"""
            from __future__ import annotations

            def get_node_command() -> tuple[str, str]:
                return ({sys.executable!r}, {str(wrapper_path)!r})
            """,
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def run_python(code: str, *, pythonpath_entries: list[Path]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    pythonpath = os.pathsep.join(str(entry) for entry in [*pythonpath_entries, *existing_pythonpath_entries(env)])
    env["PYTHONPATH"] = pythonpath
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def existing_pythonpath_entries(env: dict[str, str]) -> list[Path]:
    raw = env.get("PYTHONPATH", "")
    if not raw:
        return []
    return [Path(entry) for entry in raw.split(os.pathsep) if entry]


def test_bundled_node_provider_is_preferred_over_system_node(tmp_path: Path) -> None:
    node_path = shutil.which("node")
    if node_path is None:
        pytest.skip("node is required for provider resolution tests")

    provider_root = tmp_path / "provider"
    marker_path = tmp_path / "provider-marker.txt"
    wrapper_path = tmp_path / "provider-wrapper.py"
    write_node_wrapper(wrapper_path, marker_path, node_path)
    write_fake_provider(provider_root, wrapper_path)

    completed = run_python(
        textwrap.dedent(
            """
            from just_bash import Bash

            with Bash() as bash:
                result = bash.exec("printf provider")

            print(result.stdout, end="")
            """,
        ),
        pythonpath_entries=[provider_root, PACKAGE_SRC],
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == "provider"
    assert marker_path.exists()


def test_node_command_argument_overrides_bundled_node_provider(tmp_path: Path) -> None:
    node_path = shutil.which("node")
    if node_path is None:
        pytest.skip("node is required for provider resolution tests")

    provider_root = tmp_path / "provider"
    provider_marker = tmp_path / "provider-marker.txt"
    provider_wrapper = tmp_path / "provider-wrapper.py"
    arg_marker = tmp_path / "arg-marker.txt"
    arg_wrapper = tmp_path / "arg-wrapper.py"

    write_node_wrapper(provider_wrapper, provider_marker, node_path)
    write_node_wrapper(arg_wrapper, arg_marker, node_path)
    write_fake_provider(provider_root, provider_wrapper)

    completed = run_python(
        textwrap.dedent(
            f"""
            import json
            import sys

            from just_bash import Bash

            with Bash(node_command=[sys.executable, {str(arg_wrapper)!r}]) as bash:
                result = bash.exec("printf explicit")

            print(json.dumps({{"stdout": result.stdout, "code": result.exit_code}}))
            """,
        ),
        pythonpath_entries=[provider_root, PACKAGE_SRC],
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == '{"stdout": "explicit", "code": 0}'
    assert arg_marker.exists()
    assert not provider_marker.exists()
