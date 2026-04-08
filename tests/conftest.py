from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from tests.support.harness import BackendArtifacts

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRCS = [
    ROOT / "just_py_bash" / "src",
]
for src in reversed(PACKAGE_SRCS):
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


@pytest.fixture(scope="session", autouse=True)
def configure_source_checkout_backend() -> Generator[None, None, None]:
    from tests.support.harness import resolve_backend_artifacts

    previous_js_entry = os.environ.get("JUST_BASH_JS_ENTRY")
    previous_package_json = os.environ.get("JUST_BASH_PACKAGE_JSON")
    artifacts = resolve_backend_artifacts()
    os.environ["JUST_BASH_JS_ENTRY"] = str(artifacts.js_entry)
    os.environ["JUST_BASH_PACKAGE_JSON"] = str(artifacts.package_json)
    try:
        yield
    finally:
        if previous_js_entry is None:
            os.environ.pop("JUST_BASH_JS_ENTRY", None)
        else:
            os.environ["JUST_BASH_JS_ENTRY"] = previous_js_entry

        if previous_package_json is None:
            os.environ.pop("JUST_BASH_PACKAGE_JSON", None)
        else:
            os.environ["JUST_BASH_PACKAGE_JSON"] = previous_package_json


@pytest.fixture(scope="session")
def backend_artifacts() -> BackendArtifacts:
    from tests.support.harness import resolve_backend_artifacts

    return resolve_backend_artifacts()
