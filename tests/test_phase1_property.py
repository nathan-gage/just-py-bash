from __future__ import annotations

from typing import Any, Literal

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from tests.helpers import BackendArtifacts, phase1_snapshot_operations, run_differential_scenario

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


@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.too_slow,
    ],
)
@given(
    init_kwargs=initial_state_strategy(),
    operations=st.lists(operation_strategy(), min_size=1, max_size=8),
)
def test_phase1_property_differential_parity(
    init_kwargs: dict[str, Any],
    operations: list[dict[str, Any]],
    backend_artifacts: BackendArtifacts,
) -> None:
    python_result, reference_result = run_differential_scenario(
        init_kwargs=init_kwargs,
        operations=[*operations, *phase1_snapshot_operations(root="/workspace")],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
