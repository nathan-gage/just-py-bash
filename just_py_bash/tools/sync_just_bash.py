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


def read_upstream_version_at(ref: str) -> str:
    payload = json.loads(run(["git", "show", f"{ref}:package.json"], cwd=SUBMODULE).stdout)
    version = payload.get("version")
    if not isinstance(version, str):
        raise RuntimeError(f"Could not read just-bash version from {ref}:package.json")
    return version


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
