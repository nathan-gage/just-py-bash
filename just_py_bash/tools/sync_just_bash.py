#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[2]
SUBMODULE = ROOT / "vendor" / "just-bash"
PACKAGE_JSON_PATHS = (
    Path("package.json"),
    Path("packages/just-bash/package.json"),
)


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


def read_version_from_package_json(payload_text: str, *, source: str) -> str | None:
    raw_payload = json.loads(payload_text)
    if not isinstance(raw_payload, dict):
        raise RuntimeError(f"Could not read just-bash version from {source}")
    payload = cast("dict[str, object]", raw_payload)

    if payload.get("name") != "just-bash":
        return None

    version = payload.get("version")
    if not isinstance(version, str):
        raise RuntimeError(f"Could not read just-bash version from {source}")
    return version


def read_upstream_version_from_checkout(checkout: Path) -> str:
    checked_paths: list[str] = []
    for relative_path in PACKAGE_JSON_PATHS:
        package_json = checkout / relative_path
        checked_paths.append(str(package_json))
        if not package_json.is_file():
            continue

        version = read_version_from_package_json(package_json.read_text(encoding="utf-8"), source=str(package_json))
        if version is not None:
            return version

    raise RuntimeError(f"Could not read just-bash version; checked: {', '.join(checked_paths)}")


def read_upstream_version() -> str:
    return read_upstream_version_from_checkout(SUBMODULE)


def read_file_at_ref(ref: str, relative_path: Path) -> str | None:
    completed = subprocess.run(
        ["git", "show", f"{ref}:{relative_path.as_posix()}"],
        cwd=SUBMODULE,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def read_upstream_version_at(ref: str) -> str:
    checked_paths: list[str] = []
    for relative_path in PACKAGE_JSON_PATHS:
        checked_paths.append(f"{ref}:{relative_path.as_posix()}")
        payload_text = read_file_at_ref(ref, relative_path)
        if payload_text is None:
            continue

        version = read_version_from_package_json(payload_text, source=f"{ref}:{relative_path.as_posix()}")
        if version is not None:
            return version

    raise RuntimeError(f"Could not read just-bash version; checked: {', '.join(checked_paths)}")


def git(*args: str, cwd: Path) -> str:
    return run(["git", *args], cwd=cwd).stdout.strip()


def short_sha(value: str) -> str:
    return value[:7]


def first_parent(ref: str) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", f"{ref}^1"],
        cwd=SUBMODULE,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    parent = completed.stdout.strip()
    return parent or None


def find_version_introduction_commit(target_sha: str, target_version: str) -> str:
    candidate = target_sha
    while True:
        parent = first_parent(candidate)
        if parent is None:
            return candidate
        parent_version = read_upstream_version_at(parent)
        if parent_version != target_version:
            return candidate
        candidate = parent


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
    run(
        ["git", "fetch", "origin", "--tags", "--force", "+refs/heads/*:refs/remotes/origin/*"],
        cwd=SUBMODULE,
    )

    from_sha = git("rev-parse", "HEAD", cwd=SUBMODULE)
    from_version = read_upstream_version()

    requested_sha = git("rev-parse", args.target, cwd=SUBMODULE)
    requested_version = read_upstream_version_at(requested_sha)

    version_changed = from_version != requested_version
    to_sha = requested_sha
    selected_reason = "requested upstream ref"
    pinned_to_version_commit = False
    if version_changed:
        to_sha = find_version_introduction_commit(requested_sha, requested_version)
        pinned_to_version_commit = to_sha != requested_sha
        selected_reason = (
            "commit where the target upstream version was introduced"
            if pinned_to_version_commit
            else "requested upstream ref is already the version introduction commit"
        )

    changed = from_sha != to_sha
    if changed:
        run(["git", "checkout", "--detach", to_sha], cwd=SUBMODULE)

    to_version = read_upstream_version()

    outputs = {
        "changed": str(changed).lower(),
        "from_sha": from_sha,
        "to_sha": to_sha,
        "from_sha_short": short_sha(from_sha),
        "to_sha_short": short_sha(to_sha),
        "from_version": from_version,
        "to_version": to_version,
        "version_changed": str(version_changed).lower(),
        "release_candidate": str(version_changed).lower(),
        "target": args.target,
        "requested_sha": requested_sha,
        "requested_sha_short": short_sha(requested_sha),
        "requested_version": requested_version,
        "pinned_to_version_commit": str(pinned_to_version_commit).lower(),
        "selected_reason": selected_reason,
        "release_tag": f"v{to_version}",
    }

    for name, value in outputs.items():
        write_output(name, value)

    json.dump(outputs, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
