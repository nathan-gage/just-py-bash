from __future__ import annotations

from typing import Any

import pytest

from just_py_bash import Bash, ExecResult, ExecutionLimits, JavaScriptConfig
from just_py_bash._bridge import BackendArtifacts, encode_file_value
from tests.helpers import run_reference_scenario


@pytest.mark.parametrize(
    ("name", "init_kwargs", "operations"),
    [
        (
            "shell_state_isolated_but_filesystem_persists",
            {"cwd": "/workspace", "env": {"BASE": "root"}},
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
            {"cwd": "/workspace"},
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
            {},
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
            {
                "files": {"/seed.txt": "seed\n"},
                "commands": ["cat", "echo"],
                "execution_limits": ExecutionLimits(max_command_count=50),
            },
            [
                {"op": "exec", "script": "cat /seed.txt"},
                {"op": "exec", "script": "pwd"},
            ],
        ),
    ],
)
def test_wrapper_matches_direct_just_bash(
    name: str,
    init_kwargs: dict[str, Any],
    operations: list[dict[str, Any]],
    backend_artifacts: BackendArtifacts,
) -> None:
    python_result = run_python_scenario(init_kwargs=init_kwargs, operations=operations)
    reference_result = run_reference_scenario(
        js_entry=backend_artifacts.js_entry,
        package_json=backend_artifacts.package_json,
        init_options=to_reference_init_options(init_kwargs),
        operations=[to_reference_operation(op) for op in operations],
    )

    assert python_result == reference_result, name


def run_python_scenario(
    *,
    init_kwargs: dict[str, Any],
    operations: list[dict[str, Any]],
) -> dict[str, Any]:
    with Bash(**init_kwargs) as bash:
        results: list[Any] = []
        for operation in operations:
            op = operation["op"]
            if op == "exec":
                result = bash.exec(operation["script"], **operation.get("kwargs", {}))
                results.append(normalize_exec_result(result))
            elif op == "read_text":
                results.append(bash.read_text(operation["path"]))
            elif op == "read_bytes":
                results.append(encode_file_value(bash.read_bytes(operation["path"])))
            elif op == "write_text":
                bash.write_text(operation["path"], operation["content"])
                results.append(None)
            elif op == "write_bytes":
                bash.write_bytes(operation["path"], operation["content"])
                results.append(None)
            elif op == "get_env":
                results.append(bash.get_env())
            elif op == "get_cwd":
                results.append(bash.get_cwd())
            else:  # pragma: no cover - defensive
                raise AssertionError(f"unknown op: {op}")

        return {
            "backendVersion": bash.backend_version,
            "results": results,
        }


def normalize_exec_result(result: ExecResult) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exitCode": result.exit_code,
        "env": result.env,
    }
    if result.metadata is not None:
        payload["metadata"] = result.metadata
    return payload


def to_reference_init_options(init_kwargs: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    files = init_kwargs.get("files")
    if files is not None:
        payload["files"] = {path: encode_file_value(content) for path, content in files.items()}

    env = init_kwargs.get("env")
    if env is not None:
        payload["env"] = dict(env)

    cwd = init_kwargs.get("cwd")
    if cwd is not None:
        payload["cwd"] = cwd

    commands = init_kwargs.get("commands")
    if commands is not None:
        payload["commands"] = list(commands)

    if init_kwargs.get("python"):
        payload["python"] = True

    javascript = init_kwargs.get("javascript")
    if javascript:
        payload["javascript"] = javascript.to_wire() if isinstance(javascript, JavaScriptConfig) else True

    execution_limits = init_kwargs.get("execution_limits")
    if execution_limits is not None:
        payload["executionLimits"] = execution_limits.to_wire()

    network = init_kwargs.get("network")
    if network is not None:
        payload["network"] = dict(network)

    process_info = init_kwargs.get("process_info")
    if process_info is not None:
        payload["processInfo"] = dict(process_info)

    return payload


def to_reference_operation(operation: dict[str, Any]) -> dict[str, Any]:
    op = operation["op"]
    if op == "exec":
        payload: dict[str, Any] = {
            "op": "exec",
            "script": operation["script"],
        }
        if kwargs := operation.get("kwargs"):
            payload["options"] = to_reference_exec_options(kwargs)
        return payload
    if op == "write_bytes":
        return {
            "op": op,
            "path": operation["path"],
            "content": encode_file_value(operation["content"]),
        }
    return dict(operation)


def to_reference_exec_options(exec_kwargs: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    env = exec_kwargs.get("env")
    if env is not None:
        payload["env"] = dict(env)

    if exec_kwargs.get("replace_env"):
        payload["replaceEnv"] = True

    cwd = exec_kwargs.get("cwd")
    if cwd is not None:
        payload["cwd"] = cwd

    if exec_kwargs.get("raw_script"):
        payload["rawScript"] = True

    stdin = exec_kwargs.get("stdin")
    if stdin is not None:
        payload["stdin"] = stdin

    args = exec_kwargs.get("args")
    if args is not None:
        payload["args"] = list(args)

    timeout = exec_kwargs.get("timeout")
    if timeout is not None:
        payload["timeoutMs"] = max(1, int(timeout * 1000))

    return payload
