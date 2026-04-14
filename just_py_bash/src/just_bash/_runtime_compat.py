from __future__ import annotations

import re
import shlex
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

from ._bridge import resolve_node_command
from ._exceptions import BackendUnavailableError, UnsupportedRuntimeConfigurationError
from ._fs import MountableFs, OverlayFs, ReadWriteFs

if TYPE_CHECKING:
    from ._fs import FileSystemConfig
    from ._options import BashOptions


@dataclass(frozen=True, order=True, slots=True)
class _NodeVersion:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, raw: str) -> _NodeVersion | None:
        match = re.match(r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)", raw.strip())
        if match is None:
            return None
        return cls(
            major=int(match.group("major")),
            minor=int(match.group("minor")),
            patch=int(match.group("patch")),
        )

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


_MIN_JAVASCRIPT_RUNTIME_NODE = _NodeVersion(22, 6, 0)


def _current_platform() -> str:
    return sys.platform


def _collect_host_backed_filesystem_kinds(filesystem: FileSystemConfig) -> tuple[str, ...]:
    kinds: set[str] = set()

    def collect(candidate: FileSystemConfig) -> None:
        if isinstance(candidate, OverlayFs):
            kinds.add("OverlayFs")
            return
        if isinstance(candidate, ReadWriteFs):
            kinds.add("ReadWriteFs")
            return
        if isinstance(candidate, MountableFs):
            if candidate.base is not None:
                collect(candidate.base)
            if candidate.mounts is not None:
                for mount in candidate.mounts:
                    collect(mount.filesystem)

    collect(filesystem)
    return tuple(sorted(kinds))


def _ensure_filesystem_configuration_supported(options: BashOptions) -> None:
    if options.fs is None or _current_platform() != "win32":
        return

    host_backed_kinds = _collect_host_backed_filesystem_kinds(options.fs)
    if not host_backed_kinds:
        return

    configurations = ", ".join(host_backed_kinds)
    raise UnsupportedRuntimeConfigurationError(
        (
            "The requested just-py-bash host-backed filesystem configuration is not supported on Windows. "
            f"{configurations} rely on upstream just-bash host filesystem semantics, which are currently unstable on Windows "
            "and can silently report incorrect file state. Use `InMemoryFs`, avoid host-backed mounts, or run this workload "
            "under WSL or another POSIX environment."
        ),
        feature="host_filesystem",
        required_platform="non-Windows",
        actual_platform="win32",
        configuration=host_backed_kinds,
    )


@lru_cache(maxsize=32)
def _probe_node_version(command: tuple[str, ...]) -> _NodeVersion:
    try:
        completed = subprocess.run(
            [*command, "--version"],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:  # pragma: no cover - defensive subprocess failure
        raise BackendUnavailableError(
            f"Failed to inspect the Node.js runtime version for {shlex.join(command)}: {exc}"
        ) from exc

    output = completed.stdout.strip() or completed.stderr.strip()
    if completed.returncode != 0 or not output:
        details = output or "no version output"
        raise BackendUnavailableError(
            f"Failed to inspect the Node.js runtime version for {shlex.join(command)}: {details}"
        )

    version = _NodeVersion.parse(output)
    if version is None:
        raise BackendUnavailableError(f"Could not parse a Node.js version from {shlex.join(command)}: {output!r}")
    return version


def ensure_runtime_configuration_supported(
    options: BashOptions,
    *,
    node_command: Sequence[str] | None = None,
) -> None:
    _ensure_filesystem_configuration_supported(options)
    if not options.javascript:
        return

    resolved_command = tuple(resolve_node_command(node_command))
    node_version = _probe_node_version(resolved_command)
    if node_version >= _MIN_JAVASCRIPT_RUNTIME_NODE:
        return

    minimum = str(_MIN_JAVASCRIPT_RUNTIME_NODE)
    actual = str(node_version)
    command_display = shlex.join(resolved_command)
    raise UnsupportedRuntimeConfigurationError(
        (
            "The requested just-py-bash JavaScript runtime is not supported by the resolved Node.js runtime. "
            f"JavaScript features (`javascript=True`, `JavaScriptConfig(...)`, and `js-exec`) require Node.js >= {minimum}, "
            f"but just-py-bash resolved Node.js {actual} from {command_display}. "
            "This incompatibility comes from upstream just-bash's js-exec worker depending on "
            "`node:module.stripTypeScriptTypes`, which is unavailable on older Node.js releases. "
            "Upgrade Node.js, install `just-py-bash[node]`, or pass `node_command=` pointing at a compatible Node.js binary."
        ),
        feature="javascript",
        required_version=minimum,
        actual_version=actual,
        node_command=resolved_command,
    )
