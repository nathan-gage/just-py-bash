from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from tests.support.harness import (
    BackendArtifacts,
    op_exec,
    op_get_cwd,
    op_get_env,
    op_read_bytes,
    op_read_text,
    op_write_bytes,
    op_write_text,
    public_api,
    run_differential_scenario,
)

pytestmark = pytest.mark.parity

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
        "execution_limits": public_api().ExecutionLimits(max_command_count=50),
    }


def make_empty_values_are_transported_exactly_session() -> dict[str, Any]:
    return {"cwd": "/workspace", "env": {"BASE": "root"}}


def make_unicode_environment_round_trip_session() -> dict[str, Any]:
    return {
        "cwd": "/workspace",
        "env": {"ALPHA": "ō", "ONLY": "\x80"},
    }


def make_unicode_and_raw_script_round_trip_session() -> dict[str, Any]:
    return {"cwd": "/workspace"}


CURATED_SCENARIOS: list[CuratedScenario] = [
    (
        "shell_state_isolated_but_filesystem_persists",
        make_shell_state_isolated_but_filesystem_persists_session,
        [
            op_exec("printf 'hello\\n' > note.txt; export TEMP=42; cd /"),
            op_exec('printf \'%s|%s|%s\' "$(cat note.txt)" "${TEMP:-unset}" "$PWD"'),
            op_read_text("note.txt"),
            op_get_cwd(),
        ],
    ),
    (
        "exec_options_and_timeout",
        make_exec_options_and_timeout_session,
        [
            op_exec("mkdir -p /workspace/subdir"),
            op_exec("cat", stdin="from-stdin\n"),
            op_exec(
                'printf \'%s|%s\' "${ONLY:-missing}" "${HOME:-missing}"',
                replace_env=True,
                env={"ONLY": "yes"},
            ),
            op_exec("printf '%s|%s|%s' foo", args=["bar", "baz"]),
            op_exec("printf '%s' \"$PWD\"", cwd="/workspace/subdir"),
            op_exec("sleep 1", timeout=0.01),
        ],
    ),
    (
        "binary_round_trip",
        make_binary_round_trip_session,
        [
            op_write_bytes("/payload.bin", b"\x00\xffABC"),
            op_read_bytes("/payload.bin"),
            op_exec("wc -c < /payload.bin"),
            op_exec("base64 /payload.bin"),
        ],
    ),
    (
        "initial_files_and_command_allowlist",
        make_initial_files_and_command_allowlist_session,
        [
            op_exec("cat /seed.txt"),
            op_exec("pwd"),
        ],
    ),
    (
        "empty_values_are_transported_exactly",
        make_empty_values_are_transported_exactly_session,
        [
            op_exec("cat", stdin=""),
            op_exec(
                'printf \'%s|%s|%s\' "${BASE:-missing}" "${ONLY:-missing}" "${HOME:-missing}"',
                replace_env=True,
                env={},
            ),
            op_exec("printf '%s|%s|%s' foo", args=[]),
        ],
    ),
    (
        "unicode_environment_round_trip",
        make_unicode_environment_round_trip_session,
        [
            op_get_env(),
        ],
    ),
    (
        "unicode_and_raw_script_round_trip",
        make_unicode_and_raw_script_round_trip_session,
        [
            op_write_text("unicode.txt", "héllo 🌍\n"),
            op_exec("cat unicode.txt"),
            op_exec("cat <<'EOF'\nhello\n    EOF"),
            op_exec("cat <<'EOF'\nhello\n    EOF", raw_script=True),
        ],
    ),
]


@pytest.mark.parametrize(
    ("name", "init_factory", "operations"),
    CURATED_SCENARIOS,
    ids=[name for name, _, _ in CURATED_SCENARIOS],
)
def test_scenarios_match_upstream(
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
