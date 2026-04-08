#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBMODULE = ROOT / "vendor" / "just-bash"
PACKAGE_JSON = SUBMODULE / "package.json"
PYTHON_PACKAGE_PYPROJECT = ROOT / "just_py_bash" / "pyproject.toml"


def run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )


def write_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return

    with Path(output_path).open("a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def read_upstream_version() -> str:
    payload = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    version = payload.get("version")
    if not isinstance(version, str):
        raise RuntimeError(f"Could not read just-bash version from {PACKAGE_JSON}")
    return version


def read_python_package_version() -> str:
    for raw_line in PYTHON_PACKAGE_PYPROJECT.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("version = "):
            _, _, value = line.partition("=")
            return value.strip().strip('"')
    raise RuntimeError(f"Could not read just-py-bash version from {PYTHON_PACKAGE_PYPROJECT}")


def update_python_package_version(new_version: str) -> None:
    current_version = read_python_package_version()
    old_line = f'version = "{current_version}"'
    new_line = f'version = "{new_version}"'
    text = PYTHON_PACKAGE_PYPROJECT.read_text(encoding="utf-8")
    if old_line not in text:
        raise RuntimeError(f"Could not find version line {old_line!r} in {PYTHON_PACKAGE_PYPROJECT}")
    PYTHON_PACKAGE_PYPROJECT.write_text(text.replace(old_line, new_line, 1), encoding="utf-8")


def git(*args: str, cwd: Path) -> str:
    return run(["git", *args], cwd=cwd).stdout.strip()


def short_sha(value: str) -> str:
    return value[:7]


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync the vendored just-bash submodule to an upstream ref.")
    parser.add_argument(
        "--target",
        default="origin/main",
        help="Upstream git ref to sync to (default: origin/main)",
    )
    args = parser.parse_args()

    if not SUBMODULE.exists():
        raise RuntimeError(f"Missing submodule checkout: {SUBMODULE}")

    run(["git", "submodule", "update", "--init", "--recursive"], cwd=ROOT)
    git("fetch", "origin", "--tags", "main", cwd=SUBMODULE)

    from_sha = git("rev-parse", "HEAD", cwd=SUBMODULE)
    from_version = read_upstream_version()
    python_package_from_version = read_python_package_version()
    to_sha = git("rev-parse", args.target, cwd=SUBMODULE)

    changed = from_sha != to_sha
    if changed:
        run(["git", "checkout", "--detach", to_sha], cwd=SUBMODULE)
        run(["pnpm", "install", "--frozen-lockfile"], cwd=SUBMODULE)
        run(["pnpm", "build"], cwd=SUBMODULE)

    to_version = read_upstream_version()
    version_changed = from_version != to_version

    python_package_to_version = python_package_from_version
    if version_changed and python_package_from_version != to_version:
        update_python_package_version(to_version)
        python_package_to_version = to_version

    outputs = {
        "changed": str(changed).lower(),
        "from_sha": from_sha,
        "to_sha": to_sha,
        "from_sha_short": short_sha(from_sha),
        "to_sha_short": short_sha(to_sha),
        "from_version": from_version,
        "to_version": to_version,
        "version_changed": str(version_changed).lower(),
        "python_package_from_version": python_package_from_version,
        "python_package_to_version": python_package_to_version,
        "release_candidate": str(version_changed).lower(),
        "target": args.target,
    }

    for name, value in outputs.items():
        write_output(name, value)

    json.dump(outputs, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
