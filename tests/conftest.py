from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from just_py_bash._bridge import BackendArtifacts, resolve_backend_artifacts  # noqa: E402


@pytest.fixture(scope="session")
def backend_artifacts() -> BackendArtifacts:
    return resolve_backend_artifacts()
