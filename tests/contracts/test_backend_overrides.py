from __future__ import annotations

from pathlib import Path

import pytest

from tests.support.harness import BackendArtifacts, public_api

pytestmark = pytest.mark.contract


def bundle_entry_path(backend_artifacts: BackendArtifacts) -> Path:
    js_entry = backend_artifacts.js_entry
    if js_entry.parent.name == "bundle":
        return js_entry

    candidate = js_entry.parent / "bundle" / js_entry.name
    if not candidate.exists():
        raise AssertionError(f"Expected bundle entry next to {js_entry}, but {candidate} is missing")
    return candidate


def test_js_entry_and_package_json_arguments_override_environment_variables(
    backend_artifacts: BackendArtifacts,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JUST_BASH_JS_ENTRY", "/definitely/missing/index.js")
    monkeypatch.setenv("JUST_BASH_PACKAGE_JSON", "/definitely/missing/package.json")
    Bash = public_api().Bash

    with Bash(
        js_entry=str(backend_artifacts.js_entry),
        package_json=str(backend_artifacts.package_json),
    ) as bash:
        result = bash.exec("printf explicit-backend")

    assert result.stdout == "explicit-backend"


def test_js_entry_argument_can_infer_package_json_for_bundle_paths(
    backend_artifacts: BackendArtifacts,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("JUST_BASH_JS_ENTRY", raising=False)
    monkeypatch.delenv("JUST_BASH_PACKAGE_JSON", raising=False)
    Bash = public_api().Bash
    bundle_entry = bundle_entry_path(backend_artifacts)

    with Bash(js_entry=str(bundle_entry)) as bash:
        result = bash.exec("printf inferred-args")

    assert result.stdout == "inferred-args"


def test_js_entry_environment_variable_can_infer_package_json_for_bundle_paths(
    backend_artifacts: BackendArtifacts,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle_entry = bundle_entry_path(backend_artifacts)
    monkeypatch.setenv("JUST_BASH_JS_ENTRY", str(bundle_entry))
    monkeypatch.delenv("JUST_BASH_PACKAGE_JSON", raising=False)
    Bash = public_api().Bash

    with Bash() as bash:
        result = bash.exec("printf inferred-env")

    assert result.stdout == "inferred-env"
