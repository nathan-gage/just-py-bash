from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.support.harness import ROOT

PACKAGE_ROOT = ROOT / "just_py_bash"
RUNTIME_PACKAGE_ROOT = ROOT / "just_bash_bundled_runtime"

pytestmark = [
    pytest.mark.contract,
    pytest.mark.packaging,
    pytest.mark.xdist_group(name="distribution_contracts"),
]


@dataclass(slots=True, frozen=True)
class InstalledDistribution:
    python: Path
    bin_dir: Path
    env: dict[str, str]
    root: Path


def venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def venv_bin_dir(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts"
    return venv_dir / "bin"


def build_distribution(kind: str, dist_dir: Path, *, package_root: Path = PACKAGE_ROOT) -> Path:
    uv = shutil.which("uv")
    if not uv:
        raise NotImplementedError("uv is required to exercise the packaging flow")

    command = [uv, "build", str(package_root), f"--{kind}", "--out-dir", str(dist_dir)]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"{kind} build failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )

    pattern = "*.whl" if kind == "wheel" else "*.tar.gz"
    built = sorted(dist_dir.glob(pattern))
    if not built:
        raise AssertionError(f"uv build did not produce a {kind}")
    return built[0]


def scrub_distribution_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("JUST_PY_BASH_JS_ENTRY", None)
    env.pop("JUST_PY_BASH_PACKAGE_JSON", None)
    return env


def install_distribution(dist_path: Path, root: Path) -> InstalledDistribution:
    venv_dir = root / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    python = venv_python(venv_dir)
    subprocess.run([str(python), "-m", "pip", "install", str(dist_path)], check=True)

    isolated_root = root / "isolated"
    isolated_root.mkdir()

    return InstalledDistribution(
        python=python,
        bin_dir=venv_bin_dir(venv_dir),
        env=scrub_distribution_env(),
        root=isolated_root,
    )


def run_installed_python(installed: InstalledDistribution, code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(installed.python), "-c", code],
        cwd=installed.root,
        env=installed.env,
        text=True,
        capture_output=True,
        check=False,
    )


def run_installed_console_script(
    installed: InstalledDistribution,
    script_name: str,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    script = installed.bin_dir / (f"{script_name}.exe" if sys.platform == "win32" else script_name)
    return subprocess.run(
        [str(script), *args],
        cwd=installed.root,
        env=installed.env,
        text=True,
        capture_output=True,
        check=False,
    )


def assert_packaged_runtime_available(completed: subprocess.CompletedProcess[str], *, label: str) -> None:
    if completed.returncode == 0:
        return

    combined = f"{completed.stdout}\n{completed.stderr}"
    raise AssertionError(
        f"{label} failed unexpectedly\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}\ncombined:\n{combined}",
    )


@pytest.fixture(scope="module")
def installed_wheel(tmp_path_factory: pytest.TempPathFactory) -> InstalledDistribution:
    root = tmp_path_factory.mktemp("installed-wheel")
    wheel = build_distribution("wheel", root / "dist")
    return install_distribution(wheel, root)


@pytest.fixture(scope="module")
def installed_sdist(tmp_path_factory: pytest.TempPathFactory) -> InstalledDistribution:
    root = tmp_path_factory.mktemp("installed-sdist")
    sdist = build_distribution("sdist", root / "dist")
    return install_distribution(sdist, root)


def test_installed_wheel_boots_without_repo_checkout(installed_wheel: InstalledDistribution) -> None:
    completed = run_installed_python(
        installed_wheel,
        (
            "from just_py_bash import Bash; "
            "bash = Bash(); "
            "result = bash.exec('printf wheel-runtime'); "
            "print(bash.backend_version); "
            "print(result.stdout, end='')"
        ),
    )
    assert_packaged_runtime_available(completed, label="installed wheel smoke test")

    lines = [line for line in completed.stdout.splitlines() if line]
    assert len(lines) >= 2
    assert lines[0]
    assert lines[-1] == "wheel-runtime"


def test_installed_wheel_console_script_runs_without_repo_checkout(
    installed_wheel: InstalledDistribution,
) -> None:
    completed = run_installed_console_script(installed_wheel, "just-py-bash", "printf wheel-cli")
    assert_packaged_runtime_available(completed, label="installed wheel CLI smoke test")

    assert completed.stdout == "wheel-cli"
    assert completed.stderr == ""


def test_installed_wheel_supports_stateful_api_session(installed_wheel: InstalledDistribution) -> None:
    completed = run_installed_python(
        installed_wheel,
        (
            "import json; "
            "from just_py_bash import Bash; "
            "bash = Bash(cwd='/workspace', files={'/workspace/seed.txt': 'seed\\n'}); "
            "first = bash.exec('cat seed.txt'); "
            "bash.write_text('extra.txt', 'more\\n'); "
            "second = bash.read_text('extra.txt'); "
            "third = bash.exec('printf %s \"$PWD\"'); "
            "print(json.dumps({'backend': bash.backend_version, 'first': first.stdout, 'second': second, 'cwd': third.stdout}))"
        ),
    )
    assert_packaged_runtime_available(completed, label="installed wheel stateful API test")

    payload = json.loads(completed.stdout)
    assert payload["backend"]
    assert payload["first"] == "seed\n"
    assert payload["second"] == "more\n"
    assert payload["cwd"] == "/workspace"


def test_installed_sdist_boots_without_repo_checkout(installed_sdist: InstalledDistribution) -> None:
    completed = run_installed_python(
        installed_sdist,
        (
            "from just_py_bash import Bash; "
            "bash = Bash(); "
            "result = bash.exec('printf sdist-runtime'); "
            "print(bash.backend_version); "
            "print(result.stdout, end='')"
        ),
    )
    assert_packaged_runtime_available(completed, label="installed sdist smoke test")

    lines = [line for line in completed.stdout.splitlines() if line]
    assert len(lines) >= 2
    assert lines[0]
    assert lines[-1] == "sdist-runtime"


def test_installed_sdist_console_script_runs_without_repo_checkout(
    installed_sdist: InstalledDistribution,
) -> None:
    completed = run_installed_console_script(installed_sdist, "just-py-bash", "printf sdist-cli")
    assert_packaged_runtime_available(completed, label="installed sdist CLI smoke test")

    assert completed.stdout == "sdist-cli"
    assert completed.stderr == ""


def test_wheel_declares_explicit_node_extra(tmp_path: Path) -> None:
    wheel = build_distribution("wheel", tmp_path / "dist")

    with zipfile.ZipFile(wheel) as archive:
        metadata_name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        metadata = archive.read(metadata_name).decode("utf-8")

    assert "Provides-Extra: node" in metadata
    assert "Requires-Dist: just-bash-bundled-runtime>=22,<23 ; extra == 'node'" in metadata


def test_bundled_runtime_wheel_is_platform_specific_and_installs(tmp_path: Path) -> None:
    wheel = build_distribution("wheel", tmp_path / "runtime-dist", package_root=RUNTIME_PACKAGE_ROOT)

    assert "-py3-none-" in wheel.name
    assert not wheel.name.endswith("-any.whl")

    with zipfile.ZipFile(wheel) as archive:
        wheel_name = next(name for name in archive.namelist() if name.endswith(".dist-info/WHEEL"))
        wheel_metadata = archive.read(wheel_name).decode("utf-8")
        archived_names = set(archive.namelist())

    expected_node_path = (
        "just_bash_bundled_runtime/runtime/node.exe"
        if sys.platform == "win32"
        else "just_bash_bundled_runtime/runtime/bin/node"
    )

    assert "Generator: hatchling" in wheel_metadata
    assert "Root-Is-Purelib: false" in wheel_metadata
    assert expected_node_path in archived_names
    assert "just_bash_bundled_runtime/runtime-metadata.json" in archived_names

    installed = install_distribution(wheel, tmp_path / "runtime-install")
    completed = run_installed_python(
        installed,
        (
            "import json, subprocess; "
            "from just_bash_bundled_runtime import get_node_executable, get_runtime_metadata; "
            "metadata = get_runtime_metadata(); "
            "completed = subprocess.run([str(get_node_executable()), '--version'], text=True, capture_output=True, check=False); "
            "print(json.dumps({'code': completed.returncode, 'version': completed.stdout.strip(), 'metadata': metadata}))"
        ),
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["code"] == 0
    assert payload["metadata"]["platform"]
    assert payload["version"] == f"v{payload['metadata']['node_version']}"
