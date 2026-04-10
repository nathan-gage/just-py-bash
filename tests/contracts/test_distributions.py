from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tests.support.harness import ROOT

PACKAGE_ROOT = ROOT / "just_py_bash"
RUNTIME_PACKAGE_ROOT = ROOT / "just_bash_bundled_runtime"

pytestmark = [
    pytest.mark.contract,
    pytest.mark.packaging,
    pytest.mark.xdist_group(name="runtime_contracts"),
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
    keep = {
        "PATH",
        "HOME",
        "TMPDIR",
        "TMP",
        "TEMP",
        "SYSTEMROOT",
        "COMSPEC",
        "PATHEXT",
        "APPDATA",
        "LOCALAPPDATA",
    }
    env = {key: value for key, value in os.environ.items() if key.upper() in keep}
    env.pop("JUST_BASH_JS_ENTRY", None)
    env.pop("JUST_BASH_PACKAGE_JSON", None)
    env.pop("PYTHONPATH", None)
    env.pop("VIRTUAL_ENV", None)
    env.pop("PYTEST_CURRENT_TEST", None)
    env.pop("PYTEST_XDIST_WORKER", None)
    env.pop("PYTEST_XDIST_WORKER_COUNT", None)
    env.pop("COV_CORE_SOURCE", None)
    env.pop("COV_CORE_CONFIG", None)
    env.pop("COV_CORE_DATAFILE", None)
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


def assert_installed_optional_runtimes_work(installed: InstalledDistribution, *, label: str) -> None:
    python_completed = run_installed_python(
        installed,
        (
            "import json\n"
            "from just_bash import Bash\n"
            "with Bash(python=True) as bash:\n"
            "    result = bash.exec('python -c \\\"print(sum([2, 3, 5]))\\\"', timeout=60)\n"
            "print(json.dumps({'code': result.exit_code, 'stdout': result.stdout, 'stderr': result.stderr}))\n"
        ),
    )
    assert_packaged_runtime_available(python_completed, label=f"{label} python runtime")
    python_payload = json.loads(python_completed.stdout)
    assert python_payload == {"code": 0, "stdout": "10\n", "stderr": ""}

    javascript_completed = run_installed_python(
        installed,
        (
            "import json\n"
            "from just_bash import Bash, JavaScriptConfig\n"
            "with Bash(javascript=JavaScriptConfig(bootstrap=\"globalThis.prefix = 'bootstrapped';\")) as bash:\n"
            '    result = bash.exec("js-exec -c \'console.log(globalThis.prefix + \\"\\:\\" + (2 + 3))\'", timeout=60)\n'
            "print(json.dumps({'code': result.exit_code, 'stdout': result.stdout, 'stderr': result.stderr}))\n"
        ),
    )
    assert_packaged_runtime_available(javascript_completed, label=f"{label} javascript runtime")
    javascript_payload = json.loads(javascript_completed.stdout)
    assert javascript_payload == {"code": 0, "stdout": "bootstrapped:5\n", "stderr": ""}


def assert_installed_session_fs_api_and_richer_initial_files_work(
    installed: InstalledDistribution,
    *,
    label: str,
) -> None:
    completed = run_installed_python(
        installed,
        (
            "import json\n"
            "from datetime import UTC, datetime\n"
            "from just_bash import Bash, FileInit, LazyFile\n"
            "with Bash(\n"
            "    cwd='/',\n"
            "    files={\n"
            "        'meta.txt': FileInit(content='meta\\n', mode=0o640, mtime=datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)),\n"
            "        'lazy.txt': LazyFile(provider='lazy\\n'),\n"
            "    },\n"
            ") as bash:\n"
            "    bash.fs.mkdir('docs')\n"
            "    bash.fs.write_text('docs/note.txt', 'note\\n')\n"
            "    bash.fs.cp('docs/note.txt', 'copy.txt')\n"
            "    bash.exec('ln -s copy.txt link.txt')\n"
            "    stat = bash.fs.stat('meta.txt')\n"
            "    payload = {\n"
            "        'exists': bash.fs.exists('copy.txt'),\n"
            "        'mode': stat.mode,\n"
            "        'mtime': int(stat.mtime.timestamp()),\n"
            "        'lazy': bash.read_text('lazy.txt'),\n"
            "        'readlink': bash.fs.readlink('link.txt'),\n"
            "        'realpath': bash.fs.realpath('link.txt'),\n"
            "        'listing': sorted(bash.fs.readdir('/')),\n"
            "    }\n"
            "print(json.dumps(payload))\n"
        ),
    )
    assert_packaged_runtime_available(completed, label=label)
    payload = json.loads(completed.stdout)
    assert payload["exists"] is True
    assert payload["mode"] == 0o640
    assert payload["mtime"] == int(datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC).timestamp())
    assert payload["lazy"] == "lazy\n"
    assert payload["readlink"] == "copy.txt"
    assert payload["realpath"] == "/copy.txt"
    assert {"copy.txt", "docs", "lazy.txt", "link.txt", "meta.txt"} <= set(payload["listing"])


def assert_installed_option_hooks_work(installed: InstalledDistribution, *, label: str) -> None:
    completed = run_installed_python(
        installed,
        (
            "import json\n"
            "from just_bash import Bash\n"
            "class Logger:\n"
            "    def __init__(self):\n"
            "        self.events = []\n"
            "    def info(self, message, data=None):\n"
            "        self.events.append(['info', message])\n"
            "    def debug(self, message, data=None):\n"
            "        self.events.append(['debug', message])\n"
            "class Coverage:\n"
            "    def __init__(self):\n"
            "        self.hits = []\n"
            "    def hit(self, feature):\n"
            "        self.hits.append(feature)\n"
            "logger = Logger()\n"
            "coverage = Coverage()\n"
            "traces = []\n"
            "requests = []\n"
            "def trace(event):\n"
            "    traces.append(event.category)\n"
            "def fetch(request):\n"
            "    requests.append({\n"
            "        'url': request.url,\n"
            "        'method': request.method,\n"
            "        'headers': dict(request.headers),\n"
            "        'body': request.body,\n"
            "    })\n"
            "    return {\n"
            "        'status': 200,\n"
            "        'statusText': 'OK',\n"
            "        'headers': {'content-type': 'text/plain'},\n"
            "        'body': 'option-hooks\\n',\n"
            "        'url': request.url,\n"
            "    }\n"
            "with Bash(\n"
            "    files={'/workspace/a.txt': 'a\\n'},\n"
            "    cwd='/workspace',\n"
            "    logger=logger,\n"
            "    trace=trace,\n"
            "    fetch=fetch,\n"
            ") as bash:\n"
            "    fetch_result = bash.exec('curl -s https://example.com/api')\n"
            "    find_result = bash.exec('find . -maxdepth 1 -type f | sort')\n"
            "with Bash(coverage=coverage) as bash:\n"
            "    coverage_result = bash.exec('true')\n"
            "payload = {\n"
            "    'fetch_stdout': fetch_result.stdout,\n"
            "    'find_stdout': find_result.stdout,\n"
            "    'coverage_exit': coverage_result.exit_code,\n"
            "    'requests': requests,\n"
            "    'logger_messages': logger.events,\n"
            "    'trace_categories': traces,\n"
            "    'coverage_hits': coverage.hits,\n"
            "}\n"
            "print(json.dumps(payload))\n"
        ),
    )
    assert_packaged_runtime_available(completed, label=label)
    payload = json.loads(completed.stdout)
    assert payload["fetch_stdout"] == "option-hooks\n"
    assert payload["find_stdout"] == "./a.txt\n"
    assert payload["coverage_exit"] == 0
    assert payload["requests"] == [
        {
            "url": "https://example.com/api",
            "method": "GET",
            "headers": {},
            "body": None,
        }
    ]
    logger_messages = [tuple(item) for item in payload["logger_messages"]]
    assert ("info", "exec") in logger_messages
    assert ("debug", "stdout") in logger_messages
    assert ("info", "exit") in logger_messages
    assert "find" in payload["trace_categories"]
    assert payload["coverage_hits"]
    assert any(hit.startswith("bash:") or hit.startswith("cmd:") for hit in payload["coverage_hits"])


@pytest.fixture(scope="module")
def installed_wheel() -> InstalledDistribution:
    root = Path(tempfile.mkdtemp(prefix="just-py-bash-installed-wheel-"))
    wheel = build_distribution("wheel", root / "dist")
    return install_distribution(wheel, root)


@pytest.fixture(scope="module")
def installed_sdist() -> InstalledDistribution:
    root = Path(tempfile.mkdtemp(prefix="just-py-bash-installed-sdist-"))
    sdist = build_distribution("sdist", root / "dist")
    return install_distribution(sdist, root)


def test_installed_wheel_boots_without_repo_checkout(installed_wheel: InstalledDistribution) -> None:
    completed = run_installed_python(
        installed_wheel,
        (
            "from just_bash import Bash; "
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
            "from just_bash import Bash; "
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


def test_installed_wheel_supports_session_fs_api_and_richer_initial_files(
    installed_wheel: InstalledDistribution,
) -> None:
    assert_installed_session_fs_api_and_richer_initial_files_work(
        installed_wheel,
        label="installed wheel session fs API test",
    )


def test_installed_wheel_supports_option_hooks(installed_wheel: InstalledDistribution) -> None:
    assert_installed_option_hooks_work(installed_wheel, label="installed wheel option hooks test")


def test_installed_wheel_supports_optional_python_and_javascript_runtimes(
    installed_wheel: InstalledDistribution,
) -> None:
    assert_installed_optional_runtimes_work(installed_wheel, label="installed wheel")


def test_installed_sdist_boots_without_repo_checkout(installed_sdist: InstalledDistribution) -> None:
    completed = run_installed_python(
        installed_sdist,
        (
            "from just_bash import Bash; "
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


def test_installed_sdist_supports_session_fs_api_and_richer_initial_files(
    installed_sdist: InstalledDistribution,
) -> None:
    assert_installed_session_fs_api_and_richer_initial_files_work(
        installed_sdist,
        label="installed sdist session fs API test",
    )


def test_installed_sdist_supports_option_hooks(installed_sdist: InstalledDistribution) -> None:
    assert_installed_option_hooks_work(installed_sdist, label="installed sdist option hooks test")


def test_installed_sdist_supports_optional_python_and_javascript_runtimes(
    installed_sdist: InstalledDistribution,
) -> None:
    assert_installed_optional_runtimes_work(installed_sdist, label="installed sdist")


def test_wheel_declares_explicit_node_extra(tmp_path: Path) -> None:
    wheel = build_distribution("wheel", tmp_path / "dist")

    with zipfile.ZipFile(wheel) as archive:
        metadata_name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        metadata = archive.read(metadata_name).decode("utf-8")

    assert "Provides-Extra: node" in metadata
    requires_dist_lines = [line for line in metadata.splitlines() if line.startswith("Requires-Dist: ")]
    assert any(
        line.startswith("Requires-Dist: just-bash-bundled-runtime")
        and ">=22" in line
        and "<23" in line
        and "extra == 'node'" in line
        for line in requires_dist_lines
    )


def test_wheel_contains_packaged_just_bash_runtime(tmp_path: Path) -> None:
    wheel = build_distribution("wheel", tmp_path / "dist")

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())

    assert "just_bash/_vendor/just-bash/package.json" in names
    assert any(
        candidate in names
        for candidate in (
            "just_bash/_vendor/just-bash/dist/index.js",
            "just_bash/_vendor/just-bash/dist/bundle/index.js",
        )
    )
    assert any(name.startswith("just_bash/_vendor/just-bash/vendor/cpython-emscripten/") for name in names)


def test_sdist_contains_packaged_just_bash_runtime(tmp_path: Path) -> None:
    sdist = build_distribution("sdist", tmp_path / "dist")

    with tarfile.open(sdist, "r:gz") as archive:
        names = set(archive.getnames())

    assert any(name.endswith("/src/just_bash/_vendor/just-bash/package.json") for name in names)
    assert any(
        name.endswith("/src/just_bash/_vendor/just-bash/dist/index.js")
        or name.endswith("/src/just_bash/_vendor/just-bash/dist/bundle/index.js")
        for name in names
    )
    assert any("/src/just_bash/_vendor/just-bash/vendor/cpython-emscripten/" in name for name in names)


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
