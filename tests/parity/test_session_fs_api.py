from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest

from tests.support.harness import (
    BackendArtifacts,
    op_chmod,
    op_cp,
    op_exec,
    op_exists,
    op_mkdir,
    op_mv,
    op_read_text,
    op_readdir,
    op_readlink,
    op_realpath,
    op_rm,
    op_stat,
    op_write_text,
    public_api,
    run_async_differential_scenario,
    run_differential_scenario,
)

pytestmark = pytest.mark.parity

ScenarioRunner = Callable[..., tuple[dict[str, Any], dict[str, Any]]]
_WINDOWS_HOST_FS_SEMANTICS_ARE_UPSTREAM_UNSTABLE = sys.platform == "win32"


def _without_mtime(result: dict[str, Any], *, stat_indices: set[int]) -> dict[str, Any]:
    normalized_results: list[dict[str, Any]] = []
    for index, entry in enumerate(result["results"]):
        if index not in stat_indices or entry.get("kind") != "ok":
            normalized_results.append(entry)
            continue

        value = entry.get("value")
        if not isinstance(value, dict):
            normalized_results.append(entry)
            continue

        normalized_value: dict[str, Any] = dict(cast(dict[str, Any], value))
        normalized_value.pop("mtimeMs", None)
        normalized_results.append({**entry, "value": normalized_value})

    return {
        **result,
        "results": normalized_results,
    }


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_session_fs_core_operations_match_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    operations = [
        op_mkdir("docs"),
        op_write_text("docs/guide.txt", "guide\n"),
        op_exists("docs/guide.txt"),
        op_stat("docs/guide.txt"),
        op_cp("docs/guide.txt", "copy.txt"),
        op_mv("copy.txt", "moved.txt"),
        op_chmod("moved.txt", 0o600),
        op_stat("moved.txt"),
        op_readdir("."),
        op_rm("docs", recursive=True),
        op_exists("docs/guide.txt"),
    ]

    python_result, reference_result = runner(
        init_kwargs={"cwd": "/workspace"},
        operations=operations,
        backend_artifacts=backend_artifacts,
    )

    assert _without_mtime(python_result, stat_indices={3, 7}) == _without_mtime(
        reference_result,
        stat_indices={3, 7},
    )
    assert python_result["results"][2]["value"] is True
    assert python_result["results"][3]["value"]["isFile"] is True
    assert python_result["results"][3]["value"]["size"] == 6
    assert python_result["results"][7]["value"]["mode"] == 0o600
    assert "moved.txt" in set(python_result["results"][8]["value"])
    assert python_result["results"][10]["value"] is False


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_session_fs_symlink_operations_match_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    operations = [
        op_write_text("target.txt", "target\n"),
        op_exec("ln -s target.txt link.txt"),
        op_readlink("link.txt"),
        op_realpath("link.txt"),
        op_stat("link.txt"),
    ]

    python_result, reference_result = runner(
        init_kwargs={"cwd": "/workspace"},
        operations=operations,
        backend_artifacts=backend_artifacts,
    )

    assert _without_mtime(python_result, stat_indices={4}) == _without_mtime(
        reference_result,
        stat_indices={4},
    )
    assert python_result["results"][2]["value"] == "target.txt"
    assert python_result["results"][3]["value"] == "/workspace/target.txt"
    assert python_result["results"][4]["value"]["isFile"] is True


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_session_fs_path_failures_match_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    operations = [
        op_stat("missing.txt"),
        op_rm("missing.txt"),
        op_mkdir("dir"),
        op_write_text("dir/file.txt", "x\n"),
        op_rm("dir"),
    ]

    python_result, reference_result = runner(
        init_kwargs={"cwd": "/workspace"},
        operations=operations,
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["kind"] == "error"
    assert python_result["results"][1]["kind"] == "error"
    assert python_result["results"][4]["kind"] == "error"


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_session_fs_read_only_overlay_failures_match_upstream(
    tmp_path: Path,
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    api = public_api()
    host_root = tmp_path / "overlay-root"
    host_root.mkdir()
    (host_root / "note.txt").write_text("seed\n", encoding="utf-8")

    operations = [
        op_read_text("note.txt"),
        op_exists("note.txt"),
        op_stat("note.txt"),
        op_write_text("note.txt", "changed\n"),
        op_mkdir("blocked"),
        op_rm("note.txt"),
        op_chmod("note.txt", 0o600),
    ]

    python_result, reference_result = runner(
        init_kwargs={
            "fs": api.OverlayFs(root=str(host_root), mount_point="/workspace", read_only=True),
            "cwd": "/workspace",
        },
        operations=operations,
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    if _WINDOWS_HOST_FS_SEMANTICS_ARE_UPSTREAM_UNSTABLE:
        assert python_result["results"][1]["value"] is False
        for index in (3, 4, 5, 6):
            assert python_result["results"][index]["kind"] == "error"
            assert "read-only file system" in python_result["results"][index]["message"]
        return

    assert python_result["results"][1]["value"] is True
    assert python_result["results"][2]["value"]["isFile"] is True
    for index in (3, 4, 5, 6):
        assert python_result["results"][index]["kind"] == "error"
        assert "read-only file system" in python_result["results"][index]["message"]


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_session_fs_read_write_root_operations_match_upstream(
    tmp_path: Path,
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    api = public_api()
    host_root = tmp_path / "read-write-root"
    reference_root = tmp_path / "read-write-root-reference"
    host_root.mkdir()
    reference_root.mkdir()

    operations = [
        op_write_text("created.txt", "created\n"),
        op_stat("created.txt"),
        op_mv("created.txt", "moved.txt"),
        op_exists("created.txt"),
        op_read_text("moved.txt"),
        op_rm("moved.txt"),
        op_exists("moved.txt"),
    ]

    python_result, reference_result = runner(
        init_kwargs={"fs": api.ReadWriteFs(root=str(host_root)), "cwd": "/"},
        operations=operations,
        backend_artifacts=backend_artifacts,
        reference_init_kwargs={"fs": api.ReadWriteFs(root=str(reference_root)), "cwd": "/"},
    )

    assert _without_mtime(python_result, stat_indices={1}) == _without_mtime(
        reference_result,
        stat_indices={1},
    )
    if _WINDOWS_HOST_FS_SEMANTICS_ARE_UPSTREAM_UNSTABLE:
        assert python_result["results"][1]["kind"] == "error"
        return

    assert python_result["results"][1]["value"]["isFile"] is True

    assert python_result["results"][4]["value"] == "created\n"
    assert python_result["results"][6]["value"] is False
    assert not (host_root / "created.txt").exists()
    assert not (host_root / "moved.txt").exists()


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_session_fs_cross_mount_copy_matches_upstream(
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
    (knowledge_root / "guide.txt").write_text("knowledge\n", encoding="utf-8")
    (reference_knowledge_root / "guide.txt").write_text("knowledge\n", encoding="utf-8")

    mountable = api.MountableFs(
        base=api.InMemoryFs(files={"/base.txt": "base\n"}),
        mounts=[
            api.MountConfig(
                mount_point="/mnt/knowledge",
                filesystem=api.OverlayFs(root=str(knowledge_root), mount_point="/", read_only=True),
            ),
            api.MountConfig(
                mount_point="/workspace",
                filesystem=api.ReadWriteFs(root=str(workspace_root)),
            ),
        ],
    )
    reference_mountable = api.MountableFs(
        base=api.InMemoryFs(files={"/base.txt": "base\n"}),
        mounts=[
            api.MountConfig(
                mount_point="/mnt/knowledge",
                filesystem=api.OverlayFs(root=str(reference_knowledge_root), mount_point="/", read_only=True),
            ),
            api.MountConfig(
                mount_point="/workspace",
                filesystem=api.ReadWriteFs(root=str(reference_workspace_root)),
            ),
        ],
    )

    operations = [
        op_cp("/mnt/knowledge/guide.txt", "copy.txt"),
        op_read_text("copy.txt"),
        op_rm("copy.txt"),
        op_exists("copy.txt"),
    ]

    python_result, reference_result = runner(
        init_kwargs={"fs": mountable, "cwd": "/workspace"},
        operations=operations,
        backend_artifacts=backend_artifacts,
        reference_init_kwargs={"fs": reference_mountable, "cwd": "/workspace"},
    )

    assert python_result == reference_result
    assert python_result["results"][1]["value"] == "knowledge\n"
    assert python_result["results"][3]["value"] is False
    assert not (workspace_root / "copy.txt").exists()


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_metadata_aware_initial_files_match_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    api = public_api()
    seeded_mtime = datetime(2024, 3, 4, 5, 6, 7, tzinfo=UTC)

    operations = [op_stat("meta.txt"), op_read_text("meta.txt")]

    python_result, reference_result = runner(
        init_kwargs={
            "files": {"meta.txt": api.FileInit(content="meta\n", mode=0o640, mtime=seeded_mtime)},
            "cwd": "/",
        },
        operations=operations,
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["value"]["mode"] == 0o640
    assert python_result["results"][0]["value"]["mtimeMs"] == int(seeded_mtime.timestamp() * 1000)
    assert python_result["results"][1]["value"] == "meta\n"


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_static_lazy_initial_files_match_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    api = public_api()
    operations = [op_read_text("lazy.txt"), op_read_text("lazy.txt")]

    python_result, reference_result = runner(
        init_kwargs={"files": {"lazy.txt": api.LazyFile(provider="lazy\n")}, "cwd": "/"},
        operations=operations,
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["value"] == "lazy\n"
    assert python_result["results"][1]["value"] == "lazy\n"


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_static_lazy_initial_file_overwrite_before_first_read_matches_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    api = public_api()
    operations = [op_write_text("lazy.txt", "override\n"), op_read_text("lazy.txt")]

    python_result, reference_result = runner(
        init_kwargs={"files": {"lazy.txt": api.LazyFile(provider="lazy\n")}, "cwd": "/"},
        operations=operations,
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][1]["value"] == "override\n"


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_callable_lazy_initial_files_match_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    api = public_api()

    def provider() -> str:
        return "lazy\n"

    operations = [op_read_text("lazy.txt"), op_read_text("lazy.txt")]

    python_result, reference_result = runner(
        init_kwargs={"files": {"lazy.txt": api.LazyFile(provider=provider)}, "cwd": "/"},
        operations=operations,
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["value"] == "lazy\n"
    assert python_result["results"][1]["value"] == "lazy\n"


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_async_callable_lazy_initial_files_match_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    api = public_api()

    async def provider() -> str:
        await asyncio.sleep(0)
        return "async-lazy\n"

    operations = [op_read_text("lazy.txt"), op_read_text("lazy.txt")]

    python_result, reference_result = runner(
        init_kwargs={"files": {"lazy.txt": api.LazyFile(provider=provider)}, "cwd": "/"},
        operations=operations,
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["value"] == "async-lazy\n"
    assert python_result["results"][1]["value"] == "async-lazy\n"


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_callable_lazy_initial_file_overwrite_before_first_read_matches_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    api = public_api()

    def provider() -> str:
        return "lazy\n"

    operations = [op_write_text("lazy.txt", "override\n"), op_read_text("lazy.txt")]

    python_result, reference_result = runner(
        init_kwargs={"files": {"lazy.txt": api.LazyFile(provider=provider)}, "cwd": "/"},
        operations=operations,
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][1]["value"] == "override\n"


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_callable_lazy_initial_file_errors_match_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    api = public_api()

    def provider() -> str:
        raise RuntimeError("boom")

    operations = [op_read_text("lazy.txt")]

    python_result, reference_result = runner(
        init_kwargs={"files": {"lazy.txt": api.LazyFile(provider=provider)}, "cwd": "/"},
        operations=operations,
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["kind"] == "error"
    assert "boom" in python_result["results"][0]["message"]


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_callable_lazy_initial_file_invalid_return_matches_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    api = public_api()

    def provider() -> object:
        return None

    operations = [op_read_text("lazy.txt")]

    python_result, reference_result = runner(
        init_kwargs={"files": {"lazy.txt": api.LazyFile(provider=provider)}, "cwd": "/"},
        operations=operations,
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["kind"] == "error"
    assert (
        "Lazy file providers must return str, bytes, or an awaitable of either"
        in python_result["results"][0]["message"]
    )
