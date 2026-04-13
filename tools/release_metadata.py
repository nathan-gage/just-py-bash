#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
JUST_BASH_PACKAGE_JSON = ROOT / "vendor" / "just-bash" / "package.json"
BUNDLED_RUNTIME_PYPROJECT = ROOT / "just_bash_bundled_runtime" / "pyproject.toml"
VERSION_PATTERN = re.compile(r"^(?P<base>\d+\.\d+\.\d+)(?:\.post\d+)?$")


@dataclass(frozen=True, slots=True)
class ReleaseTarget:
    name: str
    tag_prefix: str
    artifact_stem: str
    expects_sdist: bool


@dataclass(frozen=True, slots=True)
class ParsedTag:
    tagged_version: str
    base_version: str


JUST_PY_BASH = ReleaseTarget(
    name="just-py-bash",
    tag_prefix="v",
    artifact_stem="just_py_bash",
    expects_sdist=True,
)
BUNDLED_RUNTIME = ReleaseTarget(
    name="bundled-runtime",
    tag_prefix="runtime/v",
    artifact_stem="just_bash_bundled_runtime",
    expects_sdist=False,
)


def get_target(name: str) -> ReleaseTarget:
    if name == JUST_PY_BASH.name:
        return JUST_PY_BASH
    if name == BUNDLED_RUNTIME.name:
        return BUNDLED_RUNTIME
    raise RuntimeError(f"Unknown release target {name!r}")


def as_string_key_mapping(value: object, *, context: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeError(context)
    mapping = cast(Mapping[object, object], value)
    return {str(key): entry for key, entry in mapping.items()}


def read_json(path: Path) -> dict[str, object]:
    return as_string_key_mapping(
        json.loads(path.read_text(encoding="utf-8")), context=f"Expected JSON object in {path}"
    )


def read_bundled_runtime_node_version() -> str:
    payload = as_string_key_mapping(
        tomllib.loads(BUNDLED_RUNTIME_PYPROJECT.read_text(encoding="utf-8")),
        context=f"Invalid TOML document in {BUNDLED_RUNTIME_PYPROJECT}",
    )
    tool = as_string_key_mapping(
        payload.get("tool"),
        context=f"Missing [tool] table in {BUNDLED_RUNTIME_PYPROJECT}",
    )
    settings = as_string_key_mapping(
        tool.get("just-bash-bundled-runtime"),
        context=f"Missing [tool.just-bash-bundled-runtime] table in {BUNDLED_RUNTIME_PYPROJECT}",
    )

    node_version = settings.get("node-version")
    if not isinstance(node_version, str):
        raise RuntimeError(f"Invalid node-version in {BUNDLED_RUNTIME_PYPROJECT}")
    return node_version


def read_target_base_version(target: ReleaseTarget) -> str:
    if target == JUST_PY_BASH:
        payload = read_json(JUST_BASH_PACKAGE_JSON)
        version = payload.get("version")
        if not isinstance(version, str):
            raise RuntimeError(f"Invalid version in {JUST_BASH_PACKAGE_JSON}")
        return version

    if target == BUNDLED_RUNTIME:
        return read_bundled_runtime_node_version()

    raise RuntimeError(f"Unsupported release target {target.name!r}")


def release_tag_for_target(target: ReleaseTarget, version: str) -> str:
    return f"{target.tag_prefix}{version}"


def parse_release_tag(target: ReleaseTarget, tag: str) -> ParsedTag:
    if not tag.startswith(target.tag_prefix):
        raise RuntimeError(f"Expected {target.tag_prefix!r}-prefixed tag, got {tag!r}")

    tagged_version = tag.removeprefix(target.tag_prefix)
    match = VERSION_PATTERN.fullmatch(tagged_version)
    if match is None:
        raise RuntimeError(
            f"Tag {tag!r} must use {target.tag_prefix}<X.Y.Z> or {target.tag_prefix}<X.Y.Z.postN> semantics"
        )

    base_version = match.group("base")
    if base_version is None:
        raise RuntimeError(f"Could not determine base version from tag {tag!r}")

    return ParsedTag(tagged_version=tagged_version, base_version=base_version)


def git_tag_exists(tag: str) -> bool:
    completed = subprocess.run(
        ["git", "tag", "-l", tag],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return tag in completed.stdout.splitlines()


def validate_tag(target: ReleaseTarget, tag: str) -> ParsedTag:
    parsed = parse_release_tag(target, tag)
    expected_base_version = read_target_base_version(target)
    if parsed.base_version != expected_base_version:
        raise RuntimeError(
            f"Release tag {tag!r} does not match source base version {expected_base_version!r} for {target.name}"
        )
    return parsed


def validate_artifacts(target: ReleaseTarget, version: str, dist_dir: Path) -> None:
    names = [path.name for path in dist_dir.glob("*") if path.is_file()]
    expected_wheel_fragment = f"{target.artifact_stem}-{version}-"
    if not any(name.endswith(".whl") and expected_wheel_fragment in name for name in names):
        raise RuntimeError(f"Built artifacts {names!r} do not contain a wheel for version {version!r}")

    if target.expects_sdist:
        expected_sdist = f"{target.artifact_stem}-{version}.tar.gz"
        if expected_sdist not in names:
            raise RuntimeError(f"Built artifacts {names!r} do not contain sdist {expected_sdist!r}")


def write_output(name: str, value: str) -> None:
    raw = os.environ.get("GITHUB_OUTPUT")
    if not raw:
        return

    with Path(raw).open("a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def handle_describe(target: ReleaseTarget, *, github_output: bool, check_tag_exists: bool) -> int:
    version = read_target_base_version(target)
    outputs = {
        "version": version,
        "tag": release_tag_for_target(target, version),
    }
    if check_tag_exists:
        outputs["tag_exists"] = "true" if git_tag_exists(outputs["tag"]) else "false"

    if github_output:
        for name, value in outputs.items():
            write_output(name, value)

    json.dump(outputs, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def handle_validate_tag(target: ReleaseTarget, *, tag: str, github_output: bool) -> int:
    parsed = validate_tag(target, tag)
    outputs = {
        "version": parsed.tagged_version,
        "tag": tag,
    }

    if github_output:
        for name, value in outputs.items():
            write_output(name, value)

    json.dump(outputs, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def handle_validate_artifacts(target: ReleaseTarget, *, tag: str, dist_dir: Path) -> int:
    parsed = parse_release_tag(target, tag)
    validate_artifacts(target, parsed.tagged_version, dist_dir)
    json.dump({"version": parsed.tagged_version, "dist_dir": str(dist_dir)}, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Release metadata helpers for GitHub Actions.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    describe = subparsers.add_parser("describe")
    describe.add_argument("target", choices=[JUST_PY_BASH.name, BUNDLED_RUNTIME.name])
    describe.add_argument("--github-output", action="store_true")
    describe.add_argument("--check-tag-exists", action="store_true")

    validate_tag_parser = subparsers.add_parser("validate-tag")
    validate_tag_parser.add_argument("target", choices=[JUST_PY_BASH.name, BUNDLED_RUNTIME.name])
    validate_tag_parser.add_argument("--tag", required=True)
    validate_tag_parser.add_argument("--github-output", action="store_true")

    validate_artifacts_parser = subparsers.add_parser("validate-artifacts")
    validate_artifacts_parser.add_argument("target", choices=[JUST_PY_BASH.name, BUNDLED_RUNTIME.name])
    validate_artifacts_parser.add_argument("--tag", required=True)
    validate_artifacts_parser.add_argument("--dist-dir", type=Path, required=True)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    target = get_target(args.target)

    if args.command == "describe":
        return handle_describe(target, github_output=args.github_output, check_tag_exists=args.check_tag_exists)
    if args.command == "validate-tag":
        return handle_validate_tag(target, tag=args.tag, github_output=args.github_output)
    if args.command == "validate-artifacts":
        return handle_validate_artifacts(target, tag=args.tag, dist_dir=args.dist_dir)

    raise RuntimeError(f"Unsupported command {args.command!r}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI guardrail
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
