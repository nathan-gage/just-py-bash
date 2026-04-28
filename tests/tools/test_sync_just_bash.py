from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from typing import Protocol, cast

ROOT = Path(__file__).resolve().parents[2]
SYNC_SCRIPT = ROOT / "just_py_bash" / "tools" / "sync_just_bash.py"


class SyncJustBashModule(Protocol):
    SUBMODULE: Path

    def read_upstream_version_from_checkout(self, checkout: Path) -> str: ...

    def read_upstream_version_at(self, ref: str) -> str: ...


def load_sync_module() -> SyncJustBashModule:
    spec = importlib.util.spec_from_file_location("sync_just_bash_under_test", SYNC_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {SYNC_SCRIPT}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(SyncJustBashModule, module)


def run_git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def write_package_json(path: Path, *, name: str, version: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    version_field = "" if version is None else f', "version": "{version}"'
    path.write_text(f'{{"name": "{name}"{version_field}}}\n', encoding="utf-8")


def test_read_upstream_version_from_checkout_supports_monorepo_layout(tmp_path: Path) -> None:
    checkout = tmp_path / "just-bash"
    write_package_json(checkout / "package.json", name="just-bash-monorepo")
    write_package_json(checkout / "packages" / "just-bash" / "package.json", name="just-bash", version="2.14.3")

    sync = load_sync_module()

    assert sync.read_upstream_version_from_checkout(checkout) == "2.14.3"


def test_read_upstream_version_at_supports_root_and_monorepo_layouts(tmp_path: Path) -> None:
    repo = tmp_path / "just-bash"
    repo.mkdir()
    run_git(repo, "init")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test User")

    write_package_json(repo / "package.json", name="just-bash", version="2.14.2")
    run_git(repo, "add", "package.json")
    run_git(repo, "commit", "-m", "root package layout")
    root_layout_sha = run_git(repo, "rev-parse", "HEAD")

    write_package_json(repo / "package.json", name="just-bash-monorepo")
    write_package_json(repo / "packages" / "just-bash" / "package.json", name="just-bash", version="2.14.3")
    run_git(repo, "add", "package.json", "packages/just-bash/package.json")
    run_git(repo, "commit", "-m", "monorepo package layout")
    monorepo_layout_sha = run_git(repo, "rev-parse", "HEAD")

    sync = load_sync_module()
    sync.SUBMODULE = repo

    assert sync.read_upstream_version_at(root_layout_sha) == "2.14.2"
    assert sync.read_upstream_version_at(monorepo_layout_sha) == "2.14.3"
