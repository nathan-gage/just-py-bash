from __future__ import annotations

import sys
from collections.abc import Callable
from importlib.metadata import PackageNotFoundError, version

from ._api import Bash
from ._async_api import AsyncBash
from ._cli import run_upstream_cli, run_upstream_shell
from ._command_registry import (
    get_command_names,
    get_javascript_command_names,
    get_network_command_names,
    get_python_command_names,
)
from ._custom_commands import (
    AsyncCustomCommandCallback,
    AsyncCustomCommandContext,
    AsyncCustomCommands,
    CustomCommandCallback,
    CustomCommandContext,
    CustomCommands,
)
from ._exceptions import (
    BackendError,
    BackendUnavailableError,
    BridgeError,
    BridgeTimeoutError,
    CommandFailedError,
    JustBashError,
)
from ._fs import FileInit, FsStat, InMemoryFs, LazyFile, MountableFs, MountConfig, OverlayFs, ReadWriteFs
from ._models import ExecResult, ExecutionLimits, JavaScriptConfig
from ._option_hooks import (
    BashLogger,
    DefenseInDepthConfig,
    DefenseViolationCallback,
    FeatureCoverageWriter,
    FetchCallback,
    FetchRequest,
    FetchResult,
    SecurityViolation,
    TraceCallback,
    TraceEvent,
)
from ._options import BashOptions, ExecOptions
from ._parser import parse, serialize
from ._sandbox import (
    AsyncSandbox,
    AsyncSandboxCommand,
    Sandbox,
    SandboxCommand,
    SandboxOptions,
    SandboxOutputMessage,
    SandboxWriteFile,
)
from ._security import (
    SecurityViolationError,
    SecurityViolationLogger,
    ViolationSummary,
    create_console_violation_callback,
)
from ._transform import (
    BashTransformPipeline,
    BashTransformResult,
    CommandCollectorPlugin,
    TeePlugin,
    TransformPlugin,
)
from ._types import AllowedUrl, AllowedUrlEntry, NetworkConfig, ProcessInfo, RequestTransform

try:
    __version__ = version("just-py-bash")
except PackageNotFoundError:  # pragma: no cover - editable installs during development
    __version__ = "0.0.0"

__all__ = [
    "AsyncBash",
    "Bash",
    "AsyncCustomCommandCallback",
    "AsyncCustomCommandContext",
    "AsyncCustomCommands",
    "AllowedUrl",
    "AllowedUrlEntry",
    "AsyncSandbox",
    "AsyncSandboxCommand",
    "BackendError",
    "BackendUnavailableError",
    "BashOptions",
    "BashTransformPipeline",
    "BashTransformResult",
    "CustomCommandCallback",
    "CustomCommandContext",
    "CustomCommands",
    "BridgeError",
    "BridgeTimeoutError",
    "CommandCollectorPlugin",
    "CommandFailedError",
    "DefenseInDepthConfig",
    "DefenseViolationCallback",
    "ExecOptions",
    "ExecResult",
    "ExecutionLimits",
    "FileInit",
    "FsStat",
    "FeatureCoverageWriter",
    "FetchCallback",
    "FetchRequest",
    "FetchResult",
    "InMemoryFs",
    "MountConfig",
    "MountableFs",
    "NetworkConfig",
    "OverlayFs",
    "ProcessInfo",
    "JavaScriptConfig",
    "LazyFile",
    "BashLogger",
    "ReadWriteFs",
    "Sandbox",
    "SandboxCommand",
    "SandboxOptions",
    "SandboxOutputMessage",
    "SandboxWriteFile",
    "SecurityViolation",
    "SecurityViolationError",
    "SecurityViolationLogger",
    "JustBashError",
    "RequestTransform",
    "TeePlugin",
    "TraceCallback",
    "TraceEvent",
    "TransformPlugin",
    "ViolationSummary",
    "__version__",
    "create_console_violation_callback",
    "get_command_names",
    "get_javascript_command_names",
    "get_network_command_names",
    "get_python_command_names",
    "main",
    "parse",
    "serialize",
    "shell_main",
]


def _run_cli_with_error_handling(
    runner: Callable[[list[str] | None], int],
    argv: list[str] | None = None,
) -> int:
    try:
        return runner(argv)
    except BackendUnavailableError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    return _run_cli_with_error_handling(run_upstream_cli, argv)


def shell_main(argv: list[str] | None = None) -> int:
    return _run_cli_with_error_handling(run_upstream_shell, argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
