from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from tests.support.harness import (
    BackendArtifacts,
    op_exec,
    public_api,
    run_async_differential_scenario,
    run_differential_scenario,
)

pytestmark = pytest.mark.parity

ScenarioRunner = Callable[..., tuple[dict[str, Any], dict[str, Any]]]


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_overlay_fs_matches_upstream_and_keeps_host_files_unchanged(
    tmp_path: Path,
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    api = public_api()
    host_root = tmp_path / "overlay-root"
    host_root.mkdir()
    host_file = host_root / "note.txt"
    host_file.write_text("seed\n", encoding="utf-8")

    init_kwargs = {
        "fs": api.OverlayFs(root=str(host_root), mount_point="/workspace"),
        "cwd": "/workspace",
    }
    operations = [
        op_exec("cat note.txt"),
        op_exec("printf 'changed\\n' > note.txt"),
        op_exec("cat note.txt"),
        op_exec("printf '%s' \"$PWD\""),
    ]

    python_result, reference_result = runner(
        init_kwargs=init_kwargs,
        operations=operations,
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["value"]["stdout"] == "seed\n"
    assert python_result["results"][2]["value"]["stdout"] == "changed\n"
    assert python_result["results"][3]["value"]["stdout"] == "/workspace"
    assert host_file.read_text(encoding="utf-8") == "seed\n"


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_read_write_fs_matches_upstream_and_persists_host_writes(
    tmp_path: Path,
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    api = public_api()
    host_root = tmp_path / "read-write-root"
    reference_root = tmp_path / "read-write-root-reference"
    host_root.mkdir()
    reference_root.mkdir()
    existing = host_root / "existing.txt"
    reference_existing = reference_root / "existing.txt"
    existing.write_text("before\n", encoding="utf-8")
    reference_existing.write_text("before\n", encoding="utf-8")

    init_kwargs = {
        "fs": api.ReadWriteFs(root=str(host_root)),
        "cwd": "/",
    }
    reference_init_kwargs = {
        "fs": api.ReadWriteFs(root=str(reference_root)),
        "cwd": "/",
    }
    operations = [
        op_exec("cat existing.txt"),
        op_exec("printf 'after\\n' > existing.txt"),
        op_exec("printf 'new\\n' > created.txt"),
        op_exec("cat created.txt"),
    ]

    python_result, reference_result = runner(
        init_kwargs=init_kwargs,
        operations=operations,
        backend_artifacts=backend_artifacts,
        reference_init_kwargs=reference_init_kwargs,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["value"]["stdout"] == "before\n"
    assert python_result["results"][3]["value"]["stdout"] == "new\n"
    assert existing.read_text(encoding="utf-8") == "after\n"
    assert (host_root / "created.txt").read_text(encoding="utf-8") == "new\n"


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_mountable_fs_matches_upstream_for_mixed_mounts_and_cross_mount_copy(
    tmp_path: Path,
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    api = public_api()
    knowledge_root = tmp_path / "knowledge"
    reference_knowledge_root = tmp_path / "knowledge-reference"
    workspace_root = tmp_path / "workspace"
    reference_workspace_root = tmp_path / "workspace-reference"
    knowledge_root.mkdir()
    reference_knowledge_root.mkdir()
    workspace_root.mkdir()
    reference_workspace_root.mkdir()
    knowledge_file = knowledge_root / "guide.txt"
    reference_knowledge_file = reference_knowledge_root / "guide.txt"
    knowledge_file.write_text("knowledge\n", encoding="utf-8")
    reference_knowledge_file.write_text("knowledge\n", encoding="utf-8")

    init_kwargs = {
        "fs": api.MountableFs(
            base=api.InMemoryFs(files={"/base.txt": "base\n"}),
            mounts=[
                api.MountConfig(
                    mount_point="/mnt/knowledge",
                    filesystem=api.OverlayFs(
                        root=str(knowledge_root),
                        mount_point="/",
                        read_only=True,
                    ),
                ),
                api.MountConfig(
                    mount_point="/workspace",
                    filesystem=api.ReadWriteFs(root=str(workspace_root)),
                ),
            ],
        ),
        "cwd": "/workspace",
    }
    reference_init_kwargs = {
        "fs": api.MountableFs(
            base=api.InMemoryFs(files={"/base.txt": "base\n"}),
            mounts=[
                api.MountConfig(
                    mount_point="/mnt/knowledge",
                    filesystem=api.OverlayFs(
                        root=str(reference_knowledge_root),
                        mount_point="/",
                        read_only=True,
                    ),
                ),
                api.MountConfig(
                    mount_point="/workspace",
                    filesystem=api.ReadWriteFs(root=str(reference_workspace_root)),
                ),
            ],
        ),
        "cwd": "/workspace",
    }
    operations = [
        op_exec("cat /base.txt"),
        op_exec("cp /mnt/knowledge/guide.txt ./copy.txt"),
        op_exec("cat copy.txt"),
        op_exec("printf 'blocked\\n' > /mnt/knowledge/guide.txt"),
    ]

    python_result, reference_result = runner(
        init_kwargs=init_kwargs,
        operations=operations,
        backend_artifacts=backend_artifacts,
        reference_init_kwargs=reference_init_kwargs,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["value"]["stdout"] == "base\n"
    assert python_result["results"][2]["value"]["stdout"] == "knowledge\n"
    assert python_result["results"][3]["kind"] == "error"
    assert "read-only file system" in python_result["results"][3]["message"]
    assert (workspace_root / "copy.txt").read_text(encoding="utf-8") == "knowledge\n"
    assert knowledge_file.read_text(encoding="utf-8") == "knowledge\n"
