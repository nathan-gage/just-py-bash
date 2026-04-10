from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

from ._api import Bash
from ._async_api import AsyncBash
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
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="just-py-bash",
        description="Execute a command through the Python just-bash wrapper.",
    )
    parser.add_argument("command", nargs="?", help="Shell command to execute")
    parser.add_argument("--cwd", help="Session cwd")
    parser.add_argument(
        "--python",
        action="store_true",
        help="Enable just-bash's optional python/python3 commands",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Abort execution after N seconds",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the wrapper version and exit",
    )

    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if not args.command:
        parser.print_help()
        return 0

    stdin = None if sys.stdin.isatty() else sys.stdin.read()

    with Bash(cwd=args.cwd, python=args.python) as bash:
        result = bash.exec(args.command, stdin=stdin, timeout=args.timeout)

    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
