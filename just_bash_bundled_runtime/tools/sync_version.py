#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import tomllib
import urllib.request
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1]
PYPROJECT = PACKAGE_DIR / "pyproject.toml"
TARGET_MAJOR = 22


def write_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return

    with Path(output_path).open("a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def read_current_version() -> str:
    payload = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    version = payload["project"]["version"]
    if not isinstance(version, str):
        raise RuntimeError(f"Invalid version in {PYPROJECT}")
    return version


def fetch_latest_lts_version(major: int) -> str:
    with urllib.request.urlopen("https://nodejs.org/dist/index.tab", timeout=60) as response:
        payload = response.read()
    if not isinstance(payload, bytes):
        raise RuntimeError("Expected bytes payload from nodejs.org index")

    rows = payload.decode("utf-8").splitlines()
    if not rows:
        raise RuntimeError("Unexpected empty Node release index")

    header = rows[0].split("\t")
    try:
        version_index = header.index("version")
        lts_index = header.index("lts")
    except ValueError as exc:
        raise RuntimeError("Node release index is missing expected columns") from exc

    for row in rows[1:]:
        columns = row.split("\t")
        if len(columns) <= max(version_index, lts_index):
            continue
        version = columns[version_index]
        lts = columns[lts_index]
        if not version.startswith("v"):
            continue
        if lts == "-":
            continue
        if version[1:].split(".", maxsplit=1)[0] != str(major):
            continue
        return version[1:]

    raise RuntimeError(f"Could not find an LTS Node {major} release")


def update_version(new_version: str) -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    current = read_current_version()
    old_line = f'version = "{current}"'
    new_line = f'version = "{new_version}"'
    if old_line not in text:
        raise RuntimeError(f"Could not find version line {old_line!r} in {PYPROJECT}")
    PYPROJECT.write_text(text.replace(old_line, new_line, 1), encoding="utf-8")


def main() -> int:
    current_version = read_current_version()
    latest_version = fetch_latest_lts_version(TARGET_MAJOR)
    changed = current_version != latest_version

    if changed:
        update_version(latest_version)

    outputs = {
        "changed": str(changed).lower(),
        "from_version": current_version,
        "to_version": latest_version,
        "target_major": str(TARGET_MAJOR),
    }
    for name, value in outputs.items():
        write_output(name, value)

    json.dump(outputs, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
