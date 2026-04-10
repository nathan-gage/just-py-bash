from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ._bridge import resolve_backend_artifacts, resolve_node_command
from ._exceptions import BackendUnavailableError


def run_upstream_cli(argv: list[str] | None = None) -> int:
    return _run_cli_entrypoint(_resolve_cli_entrypoint("dist/bin/just-bash.js"), argv)


def run_upstream_shell(argv: list[str] | None = None) -> int:
    return _run_cli_entrypoint(_resolve_cli_entrypoint("dist/bin/shell/shell.js"), argv)


def _resolve_cli_entrypoint(relative_path: str) -> Path:
    artifacts = resolve_backend_artifacts()
    runtime_root = artifacts.package_json.parent
    entrypoint = runtime_root / Path(relative_path)
    if not entrypoint.is_file():
        raise BackendUnavailableError(
            "Could not find the upstream just-bash CLI asset required for delegation: "
            f"{entrypoint}. Rebuild the packaged runtime with `make build-packaged-runtime`, "
            "or point JUST_BASH_JS_ENTRY / JUST_BASH_PACKAGE_JSON at a just-bash artifact "
            "that also ships dist/bin/**."
        )
    return entrypoint


def _run_cli_entrypoint(entrypoint: Path, argv: list[str] | None) -> int:
    forwarded_argv = sys.argv[1:] if argv is None else argv
    command = [*resolve_node_command(), str(entrypoint), *forwarded_argv]

    completed = subprocess.run(command, check=False)
    return int(completed.returncode)


__all__ = ["run_upstream_cli", "run_upstream_shell"]
