from __future__ import annotations

from pathlib import Path

import pytest

from tools.release_metadata import (
    BUNDLED_RUNTIME,
    JUST_PY_BASH,
    parse_release_tag,
    read_target_base_version,
    release_tag_for_target,
    validate_artifacts,
)

pytestmark = pytest.mark.contract


def test_just_py_bash_release_tag_matches_vendored_version() -> None:
    version = read_target_base_version(JUST_PY_BASH)

    parsed = parse_release_tag(JUST_PY_BASH, release_tag_for_target(JUST_PY_BASH, version))

    assert parsed.tagged_version == version
    assert parsed.base_version == version


def test_bundled_runtime_release_tag_uses_runtime_namespace() -> None:
    version = read_target_base_version(BUNDLED_RUNTIME)

    parsed = parse_release_tag(BUNDLED_RUNTIME, release_tag_for_target(BUNDLED_RUNTIME, f"{version}.post1"))

    assert parsed.tagged_version == f"{version}.post1"
    assert parsed.base_version == version


def test_validate_artifacts_accepts_main_package_filenames(tmp_path: Path) -> None:
    version = "1.2.3.post1"
    (tmp_path / f"just_py_bash-{version}-py3-none-any.whl").write_text("", encoding="utf-8")
    (tmp_path / f"just_py_bash-{version}.tar.gz").write_text("", encoding="utf-8")

    validate_artifacts(JUST_PY_BASH, version, tmp_path)


def test_validate_artifacts_accepts_bundled_runtime_wheel_filename(tmp_path: Path) -> None:
    version = "22.22.2"
    (tmp_path / f"just_bash_bundled_runtime-{version}-py3-none-macosx_11_0_arm64.whl").write_text("", encoding="utf-8")

    validate_artifacts(BUNDLED_RUNTIME, version, tmp_path)
