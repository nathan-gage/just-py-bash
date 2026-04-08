from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from tests.support.harness import BackendArtifacts

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRCS = [
    ROOT / "just_bash_bundled_runtime" / "src",
    ROOT / "just_py_bash" / "src",
]
for src in reversed(PACKAGE_SRCS):
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


@pytest.fixture(scope="session")
def backend_artifacts() -> BackendArtifacts:
    from tests.support.harness import resolve_backend_artifacts

    return resolve_backend_artifacts()
