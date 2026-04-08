from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TypedDict


class RuntimeMetadata(TypedDict):
    archive_name: str
    archive_url: str
    node_version: str
    platform: str
    sha256: str


def get_runtime_root() -> Path:
    return Path(__file__).resolve().parent / "runtime"


def get_node_executable() -> Path:
    runtime_root = get_runtime_root()
    executable = runtime_root / "node.exe" if sys.platform == "win32" else runtime_root / "bin" / "node"
    if not executable.exists():
        raise FileNotFoundError(
            "Bundled Node.js executable is missing. Rebuild the just-bash-bundled-runtime package runtime.",
        )
    return executable


def get_node_command() -> tuple[str, ...]:
    return (str(get_node_executable()),)


def get_runtime_metadata() -> RuntimeMetadata:
    metadata_path = Path(__file__).resolve().parent / "runtime-metadata.json"
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    return {
        "archive_name": str(payload["archive_name"]),
        "archive_url": str(payload["archive_url"]),
        "node_version": str(payload["node_version"]),
        "platform": str(payload["platform"]),
        "sha256": str(payload["sha256"]),
    }


__all__ = [
    "RuntimeMetadata",
    "get_node_command",
    "get_node_executable",
    "get_runtime_metadata",
    "get_runtime_root",
]
