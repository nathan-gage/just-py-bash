from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

PACKAGE_DIR = Path(__file__).resolve().parents[1]
PYPROJECT = PACKAGE_DIR / "pyproject.toml"
TOOL_SECTION = "just-bash-bundled-runtime"
RUNTIME_TAG_PREFIX = "runtime/v"


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    node_version: str
    target_major: int


def as_string_key_mapping(value: object, *, context: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeError(context)
    mapping = cast(Mapping[object, object], value)
    return {str(key): entry for key, entry in mapping.items()}


def read_runtime_config(pyproject: Path = PYPROJECT) -> RuntimeConfig:
    payload = as_string_key_mapping(
        tomllib.loads(pyproject.read_text(encoding="utf-8")),
        context=f"Invalid TOML document in {pyproject}",
    )
    tool = as_string_key_mapping(payload.get("tool"), context=f"Missing [tool] table in {pyproject}")
    settings = as_string_key_mapping(
        tool.get(TOOL_SECTION),
        context=f"Missing [tool.{TOOL_SECTION}] table in {pyproject}",
    )

    node_version = settings.get("node-version")
    target_major = settings.get("target-major")
    if not isinstance(node_version, str):
        raise RuntimeError(f"Invalid node-version in {pyproject}")
    if not isinstance(target_major, int):
        raise RuntimeError(f"Invalid target-major in {pyproject}")

    return RuntimeConfig(node_version=node_version, target_major=target_major)


def update_runtime_node_version(new_version: str, pyproject: Path = PYPROJECT) -> None:
    current_version = read_runtime_config(pyproject).node_version
    text = pyproject.read_text(encoding="utf-8")
    old_line = f'node-version = "{current_version}"'
    new_line = f'node-version = "{new_version}"'
    if old_line not in text:
        raise RuntimeError(f"Could not find node-version line {old_line!r} in {pyproject}")
    pyproject.write_text(text.replace(old_line, new_line, 1), encoding="utf-8")


def release_tag_for_version(version: str) -> str:
    return f"{RUNTIME_TAG_PREFIX}{version}"
