from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from tests.helpers import BackendArtifacts

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(scope="session")
def backend_artifacts() -> BackendArtifacts:
    from tests.helpers import resolve_backend_artifacts

    return resolve_backend_artifacts()
