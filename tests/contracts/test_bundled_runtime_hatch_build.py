from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[2]
HATCH_BUILD_PATH = ROOT / "just_bash_bundled_runtime" / "hatch_build.py"

pytestmark = pytest.mark.contract


def load_hatch_build_module(monkeypatch: pytest.MonkeyPatch) -> Any:
    interface_module = cast(Any, types.ModuleType("hatchling.builders.hooks.plugin.interface"))

    class BuildHookInterface:  # pragma: no cover - test shim for optional hatchling dependency
        pass

    interface_module.BuildHookInterface = BuildHookInterface

    plugin_module = cast(Any, types.ModuleType("hatchling.builders.hooks.plugin"))
    plugin_module.interface = interface_module

    hooks_module = cast(Any, types.ModuleType("hatchling.builders.hooks"))
    hooks_module.plugin = plugin_module

    builders_module = cast(Any, types.ModuleType("hatchling.builders"))
    builders_module.hooks = hooks_module

    hatchling_module = cast(Any, types.ModuleType("hatchling"))
    hatchling_module.builders = builders_module

    monkeypatch.setitem(sys.modules, "hatchling", hatchling_module)
    monkeypatch.setitem(sys.modules, "hatchling.builders", builders_module)
    monkeypatch.setitem(sys.modules, "hatchling.builders.hooks", hooks_module)
    monkeypatch.setitem(sys.modules, "hatchling.builders.hooks.plugin", plugin_module)
    monkeypatch.setitem(sys.modules, "hatchling.builders.hooks.plugin.interface", interface_module)

    spec = importlib.util.spec_from_file_location("bundled_runtime_hatch_build_test", HATCH_BUILD_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_glibc_versions_extracts_required_versions(monkeypatch: pytest.MonkeyPatch) -> None:
    hatch_build = load_hatch_build_module(monkeypatch)

    payload = """
Version needs section '.gnu.version_r' contains 2 entries:
  000000: Version: 1  File: libc.so.6  Cnt: 3
  0x0010:   Name: GLIBC_2.2.5  Flags: none  Version: 8
  0x0020:   Name: GLIBC_2.25   Flags: none  Version: 7
  0x0030:   Name: GLIBC_2.28   Flags: none  Version: 6
"""

    assert hatch_build.parse_glibc_versions(payload) == [(2, 2), (2, 25), (2, 28)]


def test_runtime_platform_tag_uses_manylinux_for_linux(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    hatch_build = load_hatch_build_module(monkeypatch)
    metadata = hatch_build.RuntimeMetadata(
        archive_name="node-v22.22.2-linux-x64.tar.xz",
        archive_url="https://nodejs.org/dist/v22.22.2/node-v22.22.2-linux-x64.tar.xz",
        node_version="22.22.2",
        platform="linux-x64",
        sha256="deadbeef",
    )

    def fake_required_glibc_version(runtime_root: Path) -> tuple[int, int]:
        del runtime_root
        return (2, 28)

    monkeypatch.setattr(hatch_build, "required_glibc_version", fake_required_glibc_version)

    assert hatch_build.runtime_platform_tag(tmp_path, metadata) == "manylinux_2_28_x86_64"
