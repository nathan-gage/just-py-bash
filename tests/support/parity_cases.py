from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from hypothesis import strategies as st

from tests.support.harness import (
    op_exec,
    op_get_cwd,
    op_get_env,
    op_read_bytes,
    op_read_text,
    op_write_bytes,
    op_write_text,
    public_api,
)

ScenarioFactory = Callable[[], dict[str, Any]]
CuratedScenario = tuple[str, ScenarioFactory, list[dict[str, Any]]]

FILE_NAMES = st.sampled_from(["alpha.txt", "beta.txt", "blob.bin"])
BLACKLIST_CATEGORIES: tuple[Literal["Cs"], ...] = ("Cs",)
TEXT_VALUES = st.text(
    alphabet=st.characters(
        blacklist_categories=BLACKLIST_CATEGORIES,
        blacklist_characters="\r",
    ),
    min_size=0,
    max_size=24,
)
BYTE_VALUES = st.binary(min_size=0, max_size=24)
ENV_KEYS = st.sampled_from(["ALPHA", "ONLY", "BASE"])
PATHS = st.sampled_from(["alpha.txt", "beta.txt", "blob.bin"])


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


@st.composite
def initial_state_strategy(draw: st.DrawFn) -> dict[str, Any]:
    names = draw(st.lists(FILE_NAMES, unique=True, max_size=3))
    files: dict[str, str | bytes] = {}
    for name in names:
        if draw(st.booleans()):
            files[f"/workspace/{name}"] = draw(TEXT_VALUES)
        else:
            files[f"/workspace/{name}"] = draw(BYTE_VALUES)

    env = draw(st.dictionaries(ENV_KEYS, TEXT_VALUES, max_size=3))
    return {
        "cwd": "/workspace",
        "files": files,
        "env": env,
    }


@st.composite
def operation_strategy(draw: st.DrawFn) -> dict[str, Any]:
    kind = draw(
        st.sampled_from(
            [
                "write_text",
                "write_bytes",
                "read_text",
                "read_bytes",
                "exec_cat",
                "exec_wc",
                "exec_stdin",
                "exec_env",
                "exec_args",
                "exec_cwd",
                "get_env",
                "get_cwd",
            ],
        ),
    )

    if kind == "write_text":
        return {
            "op": "write_text",
            "path": draw(PATHS),
            "content": draw(TEXT_VALUES),
        }

    if kind == "write_bytes":
        return {
            "op": "write_bytes",
            "path": draw(PATHS),
            "content": draw(BYTE_VALUES),
        }

    if kind == "read_text":
        return {"op": "read_text", "path": draw(PATHS)}

    if kind == "read_bytes":
        return {"op": "read_bytes", "path": draw(PATHS)}

    if kind == "exec_cat":
        path = draw(PATHS)
        return {"op": "exec", "script": f"cat {path}"}

    if kind == "exec_wc":
        path = draw(PATHS)
        return {"op": "exec", "script": f"wc -c < {path}"}

    if kind == "exec_stdin":
        return {
            "op": "exec",
            "script": "cat",
            "kwargs": {"stdin": draw(TEXT_VALUES)},
        }

    if kind == "exec_env":
        env = draw(st.dictionaries(ENV_KEYS, TEXT_VALUES, max_size=3))
        return {
            "op": "exec",
            "script": 'printf \'%s|%s|%s\' "${ALPHA:-missing}" "${ONLY:-missing}" "${HOME:-missing}"',
            "kwargs": {
                "env": env,
                "replace_env": draw(st.booleans()),
            },
        }

    if kind == "exec_args":
        return {
            "op": "exec",
            "script": "printf '%s|%s|%s' foo",
            "kwargs": {
                "args": draw(st.lists(TEXT_VALUES, max_size=3)),
            },
        }

    if kind == "exec_cwd":
        return {
            "op": "exec",
            "script": "printf '%s' \"$PWD\"",
            "kwargs": {
                "cwd": draw(st.sampled_from(["/workspace", "/"])),
            },
        }

    if kind == "get_env":
        return {"op": "get_env"}

    return {"op": "get_cwd"}


__all__ = [
    "CURATED_SCENARIOS",
    "CuratedScenario",
    "ScenarioFactory",
    "initial_state_strategy",
    "operation_strategy",
]
