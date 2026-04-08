from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from tests.support.harness import BackendArtifacts, load_public_api, run_differential_scenario

ScenarioFactory = Callable[[], dict[str, Any]]
CuratedScenario = tuple[str, ScenarioFactory, list[dict[str, Any]]]


def make_shell_state_isolated_but_filesystem_persists_session() -> dict[str, Any]:
    return {"cwd": "/workspace", "env": {"BASE": "root"}}


def make_exec_options_and_timeout_session() -> dict[str, Any]:
    return {"cwd": "/workspace"}


def make_binary_round_trip_session() -> dict[str, Any]:
    return {}


def make_initial_files_and_command_allowlist_session() -> dict[str, Any]:
    return {
        "files": {"/seed.txt": "seed\n"},
        "commands": ["cat", "echo"],
        "execution_limits": load_public_api().ExecutionLimits(max_command_count=50),
    }


def make_empty_values_are_transported_exactly_session() -> dict[str, Any]:
    return {"cwd": "/workspace", "env": {"BASE": "root"}}


def make_unicode_and_raw_script_round_trip_session() -> dict[str, Any]:
    return {"cwd": "/workspace"}


CURATED_SCENARIOS: list[CuratedScenario] = [
    (
        "shell_state_isolated_but_filesystem_persists",
        make_shell_state_isolated_but_filesystem_persists_session,
        [
            {
                "op": "exec",
                "script": "printf 'hello\\n' > note.txt; export TEMP=42; cd /",
            },
            {
                "op": "exec",
                "script": 'printf \'%s|%s|%s\' "$(cat note.txt)" "${TEMP:-unset}" "$PWD"',
            },
            {"op": "read_text", "path": "note.txt"},
            {"op": "get_cwd"},
        ],
    ),
    (
        "exec_options_and_timeout",
        make_exec_options_and_timeout_session,
        [
            {"op": "exec", "script": "mkdir -p /workspace/subdir"},
            {"op": "exec", "script": "cat", "kwargs": {"stdin": "from-stdin\n"}},
            {
                "op": "exec",
                "script": 'printf \'%s|%s\' "${ONLY:-missing}" "${HOME:-missing}"',
                "kwargs": {"replace_env": True, "env": {"ONLY": "yes"}},
            },
            {
                "op": "exec",
                "script": "printf '%s|%s|%s' foo",
                "kwargs": {"args": ["bar", "baz"]},
            },
            {
                "op": "exec",
                "script": "printf '%s' \"$PWD\"",
                "kwargs": {"cwd": "/workspace/subdir"},
            },
            {"op": "exec", "script": "sleep 1", "kwargs": {"timeout": 0.01}},
        ],
    ),
    (
        "binary_round_trip",
        make_binary_round_trip_session,
        [
            {
                "op": "write_bytes",
                "path": "/payload.bin",
                "content": b"\x00\xffABC",
            },
            {"op": "read_bytes", "path": "/payload.bin"},
            {"op": "exec", "script": "wc -c < /payload.bin"},
            {"op": "exec", "script": "base64 /payload.bin"},
        ],
    ),
    (
        "initial_files_and_command_allowlist",
        make_initial_files_and_command_allowlist_session,
        [
            {"op": "exec", "script": "cat /seed.txt"},
            {"op": "exec", "script": "pwd"},
        ],
    ),
    (
        "empty_values_are_transported_exactly",
        make_empty_values_are_transported_exactly_session,
        [
            {"op": "exec", "script": "cat", "kwargs": {"stdin": ""}},
            {
                "op": "exec",
                "script": 'printf \'%s|%s|%s\' "${BASE:-missing}" "${ONLY:-missing}" "${HOME:-missing}"',
                "kwargs": {"replace_env": True, "env": {}},
            },
            {
                "op": "exec",
                "script": "printf '%s|%s|%s' foo",
                "kwargs": {"args": []},
            },
        ],
    ),
    (
        "unicode_and_raw_script_round_trip",
        make_unicode_and_raw_script_round_trip_session,
        [
            {
                "op": "write_text",
                "path": "unicode.txt",
                "content": "héllo 🌍\n",
            },
            {"op": "exec", "script": "cat unicode.txt"},
            {
                "op": "exec",
                "script": "cat <<'EOF'\nhello\n    EOF",
            },
            {
                "op": "exec",
                "script": "cat <<'EOF'\nhello\n    EOF",
                "kwargs": {"raw_script": True},
            },
        ],
    ),
]


@pytest.mark.parametrize(
    ("name", "init_factory", "operations"),
    CURATED_SCENARIOS,
    ids=[name for name, _, _ in CURATED_SCENARIOS],
)
def test_curated_session_scenarios_match_upstream(
    name: str,
    init_factory: ScenarioFactory,
    operations: list[dict[str, Any]],
    backend_artifacts: BackendArtifacts,
) -> None:
    python_result, reference_result = run_differential_scenario(
        init_kwargs=init_factory(),
        operations=operations,
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result, name
