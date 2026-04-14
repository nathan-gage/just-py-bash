from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
from pytest import MonkeyPatch

from tests.support.harness import public_api

if TYPE_CHECKING:
    from just_bash import UnsupportedRuntimeConfigurationError

pytestmark = pytest.mark.api


def assert_unsupported_windows_host_filesystem(error: Exception, *, expected_kinds: tuple[str, ...]) -> None:
    api = public_api()
    assert isinstance(error, api.UnsupportedRuntimeConfigurationError)
    typed_error = cast("UnsupportedRuntimeConfigurationError", error)
    assert typed_error.feature == "host_filesystem"
    assert typed_error.required_platform == "non-Windows"
    assert typed_error.actual_platform == "win32"
    assert typed_error.configuration == expected_kinds
    assert "host-backed filesystem configuration" in str(typed_error)
    assert "InMemoryFs" in str(typed_error)


@pytest.fixture
def force_windows_runtime_compat(monkeypatch: MonkeyPatch) -> None:
    runtime_compat = import_module("just_bash._runtime_compat")
    monkeypatch.setattr(runtime_compat, "_current_platform", lambda: "win32")


def test_bash_accepts_in_memory_fs_config_object() -> None:
    api = public_api()

    with api.Bash(fs=api.InMemoryFs(files={"/seed.txt": "seed\n"}), cwd="/") as bash:
        result = bash.exec("cat seed.txt")

    assert result.stdout == "seed\n"


def test_async_bash_accepts_in_memory_fs_config_object() -> None:
    api = public_api()

    async def exercise() -> None:
        async with api.AsyncBash(fs=api.InMemoryFs(files={"/seed.txt": "seed\n"}), cwd="/") as bash:
            result = await bash.exec("cat seed.txt")

        assert result.stdout == "seed\n"

    asyncio.run(exercise())


def test_bash_accepts_in_memory_fs_richer_initial_files() -> None:
    api = public_api()
    calls = 0

    def provider() -> str:
        nonlocal calls
        calls += 1
        return "lazy\n"

    seeded_mtime = datetime(2024, 7, 8, 9, 10, 11, tzinfo=UTC)

    with api.Bash(
        fs=api.InMemoryFs(
            files={
                "/meta.txt": api.FileInit(content="meta\n", mode=0o640, mtime=seeded_mtime),
                "/lazy.txt": api.LazyFile(provider=provider),
            },
        ),
        cwd="/",
    ) as bash:
        assert bash.read_text("meta.txt") == "meta\n"
        assert bash.fs.stat("meta.txt").mode == 0o640
        assert bash.fs.stat("meta.txt").mtime == seeded_mtime
        assert bash.read_text("lazy.txt") == "lazy\n"
        assert bash.read_text("lazy.txt") == "lazy\n"

    assert calls == 1


def test_bash_rejects_host_backed_filesystem_configs_on_windows(
    tmp_path: Path,
    force_windows_runtime_compat: None,
) -> None:
    api = public_api()

    with pytest.raises(api.UnsupportedRuntimeConfigurationError) as exc_info:
        api.Bash(fs=api.ReadWriteFs(root=str(tmp_path)), cwd="/")

    assert_unsupported_windows_host_filesystem(exc_info.value, expected_kinds=("ReadWriteFs",))


def test_async_bash_rejects_nested_host_backed_filesystem_configs_on_windows(
    tmp_path: Path,
    force_windows_runtime_compat: None,
) -> None:
    api = public_api()
    overlay_root = tmp_path / "overlay"
    overlay_root.mkdir()
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()

    async def exercise() -> None:
        with pytest.raises(api.UnsupportedRuntimeConfigurationError) as exc_info:
            async with api.AsyncBash(
                fs=api.MountableFs(
                    base=api.InMemoryFs(files={"/seed.txt": "seed\n"}),
                    mounts=[
                        api.MountConfig(
                            mount_point="/docs",
                            filesystem=api.OverlayFs(root=str(overlay_root), mount_point="/", read_only=True),
                        ),
                        api.MountConfig(
                            mount_point="/workspace",
                            filesystem=api.ReadWriteFs(root=str(workspace_root)),
                        ),
                    ],
                ),
                cwd="/workspace",
            ):
                pass

        assert_unsupported_windows_host_filesystem(
            exc_info.value,
            expected_kinds=("OverlayFs", "ReadWriteFs"),
        )

    asyncio.run(exercise())
