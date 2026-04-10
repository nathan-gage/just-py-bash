from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime

import pytest
from just_bash import BashTransformPipeline, CommandCollectorPlugin, TeePlugin, parse, serialize

from tests.support.harness import ROOT, BackendArtifacts, resolve_node_command

pytestmark = pytest.mark.parity

_REFERENCE_EXPORTS_SCRIPT = ROOT / "tests" / "support" / "reference_exports.mjs"


def _run_reference_export(backend_artifacts: BackendArtifacts, request: dict[str, object]) -> object:
    completed = subprocess.run(
        [*resolve_node_command(), str(_REFERENCE_EXPORTS_SCRIPT)],
        input=json.dumps({
            **request,
            "jsEntry": str(backend_artifacts.js_entry),
        }),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.stdout == "":
        raise AssertionError(f"reference export runner produced no stdout\nstderr:\n{completed.stderr}")

    payload = json.loads(completed.stdout)
    if payload.get("ok") is not True:
        raise AssertionError(
            f"reference export runner failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return payload["result"]


@pytest.mark.parametrize(
    ("kind", "callable_name"),
    [
        ("all", "get_command_names"),
        ("network", "get_network_command_names"),
        ("python", "get_python_command_names"),
        ("javascript", "get_javascript_command_names"),
    ],
)
def test_command_registry_helpers_match_upstream(
    backend_artifacts: BackendArtifacts,
    kind: str,
    callable_name: str,
) -> None:
    import just_bash

    python_result = getattr(just_bash, callable_name)()
    reference_result = _run_reference_export(
        backend_artifacts,
        {"op": "get_command_names", "kind": kind},
    )

    assert python_result == reference_result


def test_parse_and_serialize_match_upstream(backend_artifacts: BackendArtifacts) -> None:
    script = "echo hello | grep h && printf 'done\\n'"

    python_ast = parse(script)
    reference_ast = _run_reference_export(
        backend_artifacts,
        {"op": "parse", "script": script},
    )

    assert python_ast == reference_ast
    assert serialize(python_ast) == _run_reference_export(
        backend_artifacts,
        {"op": "serialize", "ast": reference_ast},
    )


def test_standalone_transform_pipeline_matches_upstream(backend_artifacts: BackendArtifacts) -> None:
    timestamp = datetime(2024, 1, 15, 10, 30, 45, 123000, tzinfo=UTC)
    pipeline = (
        BashTransformPipeline()
        .use(TeePlugin(output_dir="/tmp/logs", timestamp=timestamp))
        .use(CommandCollectorPlugin())
    )

    python_result = pipeline.transform("echo hello | grep h")
    reference_result = _run_reference_export(
        backend_artifacts,
        {
            "op": "transform_script",
            "script": "echo hello | grep h",
            "plugins": [plugin.to_wire() for plugin in pipeline.plugins],
        },
    )

    assert {
        "script": python_result.script,
        "ast": python_result.ast,
        "metadata": python_result.metadata,
    } == reference_result
