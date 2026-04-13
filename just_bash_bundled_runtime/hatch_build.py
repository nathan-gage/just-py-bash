from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

_PACKAGE_DIR = Path("src") / "just_bash_bundled_runtime"
_RUNTIME_MISSING_MESSAGE = (
    "Bundled Node runtime is missing. Run `python just_bash_bundled_runtime/tools/vendor_runtime.py` first."
)
_HOST_PLATFORM_PREFIX = {
    "darwin": "darwin",
    "linux": "linux",
    "win32": "win",
}
_ARCH_TO_WHEEL_TAG = {
    "arm64": "arm64",
    "x64": "x86_64",
}
_WINDOWS_ARCH_TO_WHEEL_TAG = {
    "arm64": "arm64",
    "x64": "amd64",
}
_MACOS_BUILD_VERSION = re.compile(r"minos (\d+)\.(\d+)(?:\.\d+)?")
_MACOS_MIN_VERSION = re.compile(r"version (\d+)\.(\d+)(?:\.\d+)?")
_GLIBC_VERSION = re.compile(r"Name:\s+GLIBC_(\d+)\.(\d+)\b")


class RuntimeMetadata:
    __slots__ = ("archive_name", "archive_url", "node_version", "platform", "sha256")

    def __init__(
        self,
        *,
        archive_name: str,
        archive_url: str,
        node_version: str,
        platform: str,
        sha256: str,
    ) -> None:
        self.archive_name = archive_name
        self.archive_url = archive_url
        self.node_version = node_version
        self.platform = platform
        self.sha256 = sha256

    @property
    def platform_parts(self) -> tuple[str, str]:
        parts = self.platform.split("-", 1)
        if len(parts) != 2:
            raise RuntimeError(f"Unsupported bundled runtime platform value: {self.platform!r}")
        return parts[0], parts[1]


class BundledRuntimeBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, object]) -> None:
        del version

        runtime_root, metadata = require_runtime_payload(Path(self.root))

        if self.target_name != "wheel":
            return

        build_data["pure_python"] = False
        build_data["tag"] = f"py3-none-{runtime_platform_tag(runtime_root, metadata)}"


def require_runtime_payload(project_root: Path) -> tuple[Path, RuntimeMetadata]:
    package_root = project_root / _PACKAGE_DIR
    runtime_root = package_root / "runtime"
    metadata_path = package_root / "runtime-metadata.json"
    if not runtime_root.exists() or not metadata_path.exists():
        raise RuntimeError(_RUNTIME_MISSING_MESSAGE)

    metadata = load_runtime_metadata(metadata_path)
    expected_prefix = _HOST_PLATFORM_PREFIX.get(sys.platform)
    if expected_prefix is None:
        raise RuntimeError(f"Unsupported build host platform: {sys.platform!r}")

    actual_prefix, _ = metadata.platform_parts
    if actual_prefix != expected_prefix:
        raise RuntimeError(
            f"Bundled runtime target {metadata.platform!r} does not match build host platform {sys.platform!r}.",
        )

    return runtime_root, metadata


def load_runtime_metadata(path: Path) -> RuntimeMetadata:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Invalid runtime metadata payload in {path}")

    return RuntimeMetadata(
        archive_name=read_metadata_field(payload, "archive_name", path),
        archive_url=read_metadata_field(payload, "archive_url", path),
        node_version=read_metadata_field(payload, "node_version", path),
        platform=read_metadata_field(payload, "platform", path),
        sha256=read_metadata_field(payload, "sha256", path),
    )


def read_metadata_field(payload: dict[object, object], key: str, path: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise RuntimeError(f"Invalid or missing {key!r} in {path}")
    return value


def runtime_platform_tag(runtime_root: Path, metadata: RuntimeMetadata) -> str:
    platform_name, arch = metadata.platform_parts
    if platform_name == "linux":
        major, minor = required_glibc_version(runtime_root)
        return f"manylinux_{major}_{minor}_{linux_arch_tag(arch)}"
    if platform_name == "win":
        return f"win_{windows_arch_tag(arch)}"
    if platform_name == "darwin":
        major, minor = macos_minimum_version(node_executable(runtime_root, metadata))
        return f"macosx_{major}_{minor}_{macos_arch_tag(arch)}"

    raise RuntimeError(f"Unsupported bundled runtime platform: {metadata.platform!r}")


def node_executable(runtime_root: Path, metadata: RuntimeMetadata) -> Path:
    platform_name, _ = metadata.platform_parts
    if platform_name == "win":
        executable = runtime_root / "node.exe"
    else:
        executable = runtime_root / "bin" / "node"

    if not executable.exists():
        raise RuntimeError(f"Bundled Node executable is missing from {runtime_root}")
    return executable


def required_glibc_version(runtime_root: Path) -> tuple[int, int]:
    versions: list[tuple[int, int]] = []
    for path in elf_binaries(runtime_root):
        versions.extend(glibc_versions_for_binary(path))

    if not versions:
        raise RuntimeError(f"Could not determine GLIBC requirement from bundled runtime payload under {runtime_root}")

    return max(versions)


def elf_binaries(runtime_root: Path) -> list[Path]:
    result: list[Path] = []
    for path in runtime_root.rglob("*"):
        if not path.is_file():
            continue
        with path.open("rb") as handle:
            if handle.read(4) == b"\x7fELF":
                result.append(path)
    return result


def glibc_versions_for_binary(path: Path) -> list[tuple[int, int]]:
    try:
        completed = subprocess.run(
            ["readelf", "--version-info", str(path)],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:  # pragma: no cover - depends on host image
        raise RuntimeError("Could not inspect bundled Linux binaries because `readelf` is not available") from exc

    if completed.returncode != 0:
        raise RuntimeError(
            "Could not inspect bundled Linux binary with `readelf --version-info`. "
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )

    return parse_glibc_versions(completed.stdout)


def parse_glibc_versions(payload: str) -> list[tuple[int, int]]:
    return [(int(major), int(minor)) for major, minor in _GLIBC_VERSION.findall(payload)]


def linux_arch_tag(arch: str) -> str:
    if arch == "x64":
        return "x86_64"
    if arch == "arm64":
        return "aarch64"
    raise RuntimeError(f"Unsupported Linux runtime architecture: {arch!r}")


def windows_arch_tag(arch: str) -> str:
    tag = _WINDOWS_ARCH_TO_WHEEL_TAG.get(arch)
    if tag is None:
        raise RuntimeError(f"Unsupported Windows runtime architecture: {arch!r}")
    return tag


def macos_arch_tag(arch: str) -> str:
    tag = _ARCH_TO_WHEEL_TAG.get(arch)
    if tag is None:
        raise RuntimeError(f"Unsupported macOS runtime architecture: {arch!r}")
    return tag


def macos_minimum_version(executable: Path) -> tuple[int, int]:
    completed = subprocess.run(
        ["otool", "-l", str(executable)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Could not inspect bundled Node executable with `otool -l`. "
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )

    versions: list[tuple[int, int]] = []
    current_command: str | None = None
    for raw_line in completed.stdout.splitlines():
        line = raw_line.strip()
        if line == "cmd LC_BUILD_VERSION":
            current_command = line
            continue
        if line == "cmd LC_VERSION_MIN_MACOSX":
            current_command = line
            continue

        if current_command == "cmd LC_BUILD_VERSION":
            match = _MACOS_BUILD_VERSION.fullmatch(line)
            if match is not None:
                versions.append((int(match.group(1)), int(match.group(2))))
                current_command = None
            continue

        if current_command == "cmd LC_VERSION_MIN_MACOSX":
            match = _MACOS_MIN_VERSION.fullmatch(line)
            if match is not None:
                versions.append((int(match.group(1)), int(match.group(2))))
                current_command = None

    if not versions:
        raise RuntimeError(f"Could not determine macOS minimum version for {executable}")

    return max(versions)
