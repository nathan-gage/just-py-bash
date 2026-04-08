#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import sys
import tarfile
import tempfile
import tomllib
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class NodeTarget:
    platform: str
    extension: str


def normalize_machine(machine: str) -> str:
    lowered = machine.lower()
    if lowered in {"x86_64", "amd64"}:
        return "x64"
    if lowered in {"aarch64", "arm64"}:
        return "arm64"
    return lowered


def current_target() -> NodeTarget:
    machine = normalize_machine(platform.machine())
    if sys.platform == "linux":
        if machine == "x64":
            return NodeTarget(platform="linux-x64", extension=".tar.xz")
        if machine == "arm64":
            return NodeTarget(platform="linux-arm64", extension=".tar.xz")
    elif sys.platform == "darwin":
        if machine == "x64":
            return NodeTarget(platform="darwin-x64", extension=".tar.gz")
        if machine == "arm64":
            return NodeTarget(platform="darwin-arm64", extension=".tar.gz")
    elif sys.platform == "win32":
        if machine == "x64":
            return NodeTarget(platform="win-x64", extension=".zip")
        if machine == "arm64":
            return NodeTarget(platform="win-arm64", extension=".zip")

    raise RuntimeError(f"Unsupported Node.js target for platform={sys.platform!r}, machine={platform.machine()!r}")


def read_package_version(package_dir: Path) -> str:
    payload = tomllib.loads((package_dir / "pyproject.toml").read_text(encoding="utf-8"))
    version = payload["project"]["version"]
    if not isinstance(version, str):
        raise RuntimeError(f"Invalid version in {(package_dir / 'pyproject.toml')}")
    return version


def release_base_url(node_version: str) -> str:
    return f"https://nodejs.org/dist/v{node_version}"


def archive_name(node_version: str, target: NodeTarget) -> str:
    return f"node-v{node_version}-{target.platform}{target.extension}"


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = response.read()
    if not isinstance(payload, bytes):
        raise RuntimeError(f"Expected bytes payload from {url}")
    return payload.decode("utf-8")


def download_file(url: str, destination: Path) -> None:
    with urllib.request.urlopen(url, timeout=60) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def parse_checksums(payload: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in payload.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        checksum, filename = stripped.split(maxsplit=1)
        result[filename.strip()] = checksum
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_archive(archive_path: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)

    extract_root = destination.parent / f"{destination.name}-extract"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True)

    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extract_root)
    else:
        with tarfile.open(archive_path) as archive:
            archive.extractall(extract_root)

    roots = [path for path in extract_root.iterdir() if path.is_dir()]
    if len(roots) != 1:
        raise RuntimeError(f"Expected exactly one extracted root directory in {extract_root}, found {len(roots)}")

    shutil.copytree(roots[0], destination)
    shutil.rmtree(extract_root)


def vendor_runtime(package_dir: Path) -> None:
    node_version = read_package_version(package_dir)
    target = current_target()
    release_url = release_base_url(node_version)
    name = archive_name(node_version, target)
    checksums_url = f"{release_url}/SHASUMS256.txt"
    archive_url = f"{release_url}/{name}"
    runtime_dir = package_dir / "src" / "just_bash_bundled_runtime" / "runtime"
    metadata_path = package_dir / "src" / "just_bash_bundled_runtime" / "runtime-metadata.json"

    checksums = parse_checksums(fetch_text(checksums_url))
    expected_checksum = checksums.get(name)
    if expected_checksum is None:
        raise RuntimeError(f"Could not find checksum for {name} in {checksums_url}")

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        archive_path = tmp_dir / name
        download_file(archive_url, archive_path)

        actual_checksum = sha256_file(archive_path)
        if actual_checksum != expected_checksum:
            raise RuntimeError(
                f"Checksum mismatch for {name}: expected {expected_checksum}, got {actual_checksum}",
            )

        extract_archive(archive_path, runtime_dir)

    metadata = {
        "archive_name": name,
        "archive_url": archive_url,
        "node_version": node_version,
        "platform": target.platform,
        "sha256": expected_checksum,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(metadata, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Vendor an official Node.js runtime into the just-bash-bundled-runtime package."
    )
    parser.add_argument(
        "--package-dir",
        type=Path,
        default=PACKAGE_DIR,
        help="Path to the just-bash-bundled-runtime package directory (default: this package)",
    )
    args = parser.parse_args()

    vendor_runtime(args.package_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
