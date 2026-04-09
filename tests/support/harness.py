from __future__ import annotations

import asyncio
import base64
import json
import os
import shlex
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter, ValidationError

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_SCRIPT = Path(__file__).resolve().with_name("reference.mjs")
BYTE_TAG = "__just_bash_bytes__"
_JSON_OBJECT_ADAPTER = TypeAdapter(dict[str, object])


@dataclass(slots=True, frozen=True)
class BackendArtifacts:
    js_entry: Path
    package_json: Path


def resolve_node_command() -> list[str]:
    if configured := os.environ.get("JUST_BASH_NODE"):
        return shlex.split(configured)

    node = shutil.which("node")
    if not node:
        raise AssertionError(
            "Node.js is required for differential tests. Install Node or set JUST_BASH_NODE.",
        )
    return [node]


def infer_package_json_from_js_entry(js_entry: Path) -> Path:
    for parent in js_entry.parents:
        candidate = parent / "package.json"
        if candidate.exists():
            return candidate.resolve()
    return (js_entry.parent.parent / "package.json").resolve()


def resolve_backend_artifacts() -> BackendArtifacts:
    env_js_entry = os.environ.get("JUST_BASH_JS_ENTRY")
    env_package_json = os.environ.get("JUST_BASH_PACKAGE_JSON")
    if env_js_entry:
        js_entry = Path(env_js_entry).expanduser().resolve()
        package_json = (
            Path(env_package_json).expanduser().resolve()
            if env_package_json
            else infer_package_json_from_js_entry(js_entry)
        )
        if not js_entry.exists():
            raise AssertionError(f"Configured JS entry does not exist: {js_entry}")
        if not package_json.exists():
            raise AssertionError(f"Configured package.json does not exist: {package_json}")
        return BackendArtifacts(js_entry=js_entry, package_json=package_json)

    vendor_root = ROOT / "vendor" / "just-bash"
    package_json = vendor_root / "package.json"
    for rel in ("dist/index.js", "dist/bundle/index.js"):
        js_entry = vendor_root / rel
        if js_entry.exists() and package_json.exists():
            return BackendArtifacts(js_entry=js_entry.resolve(), package_json=package_json.resolve())

    raise AssertionError(
        "Could not locate a built just-bash artifact for reference testing. "
        "Build vendor/just-bash first or set JUST_BASH_JS_ENTRY and JUST_BASH_PACKAGE_JSON.",
    )


def encode_file_value(value: str | bytes) -> str | dict[str, str]:
    if isinstance(value, bytes):
        return {BYTE_TAG: base64.b64encode(value).decode("ascii")}
    return value


def decode_bytes_payload(payload: dict[str, str]) -> bytes:
    return base64.b64decode(payload[BYTE_TAG].encode("ascii"))


def public_api() -> Any:
    return import_module("just_bash")


def normalize_exec_result(result: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exitCode": result.exit_code,
        "env": dict(result.env),
    }
    if result.metadata is not None:
        payload["metadata"] = dict(result.metadata)
    return payload


def normalize_operation_error(error: BaseException) -> dict[str, Any]:
    error_type = getattr(error, "error_type", None)
    if not isinstance(error_type, str) or not error_type:
        error_type = type(error).__name__

    return {
        "kind": "error",
        "type": error_type,
        "message": str(error),
    }


def wrap_success(value: Any) -> dict[str, Any]:
    return {
        "kind": "ok",
        "value": value,
    }


def execution_limits_to_reference(execution_limits: Any) -> dict[str, int]:
    payload: dict[str, int] = {}
    mapping = {
        "max_call_depth": "maxCallDepth",
        "max_command_count": "maxCommandCount",
        "max_loop_iterations": "maxLoopIterations",
        "max_awk_iterations": "maxAwkIterations",
        "max_sed_iterations": "maxSedIterations",
        "max_jq_iterations": "maxJqIterations",
        "max_sqlite_timeout_ms": "maxSqliteTimeoutMs",
        "max_python_timeout_ms": "maxPythonTimeoutMs",
        "max_js_timeout_ms": "maxJsTimeoutMs",
        "max_glob_operations": "maxGlobOperations",
        "max_string_length": "maxStringLength",
        "max_array_elements": "maxArrayElements",
        "max_heredoc_size": "maxHeredocSize",
        "max_substitution_depth": "maxSubstitutionDepth",
        "max_brace_expansion_results": "maxBraceExpansionResults",
        "max_output_size": "maxOutputSize",
        "max_file_descriptors": "maxFileDescriptors",
        "max_source_depth": "maxSourceDepth",
    }
    for python_name, wire_name in mapping.items():
        value = getattr(execution_limits, python_name, None)
        if value is not None:
            payload[wire_name] = value
    return payload


def javascript_config_to_reference(config: Any) -> bool | dict[str, str]:
    if config is True:
        return True
    bootstrap = getattr(config, "bootstrap", None)
    payload: dict[str, str] = {}
    if bootstrap is not None:
        payload["bootstrap"] = bootstrap
    return payload


def to_reference_init_options(init_kwargs: Mapping[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    files = init_kwargs.get("files")
    if files is not None:
        payload["files"] = {path: encode_file_value(content) for path, content in dict(files).items()}

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
        payload["javascript"] = javascript_config_to_reference(javascript)

    execution_limits = init_kwargs.get("execution_limits")
    if execution_limits is not None:
        payload["executionLimits"] = execution_limits_to_reference(execution_limits)

    network = init_kwargs.get("network")
    if network is not None:
        payload["network"] = dict(network)

    process_info = init_kwargs.get("process_info")
    if process_info is not None:
        payload["processInfo"] = dict(process_info)

    return payload


def to_reference_exec_options(exec_kwargs: Mapping[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    if "env" in exec_kwargs:
        payload["env"] = dict(exec_kwargs["env"])

    if exec_kwargs.get("replace_env"):
        payload["replaceEnv"] = True

    if "cwd" in exec_kwargs:
        payload["cwd"] = exec_kwargs["cwd"]

    if exec_kwargs.get("raw_script"):
        payload["rawScript"] = True

    if "stdin" in exec_kwargs:
        payload["stdin"] = exec_kwargs["stdin"]

    if "args" in exec_kwargs:
        payload["args"] = list(exec_kwargs["args"])

    if "timeout" in exec_kwargs and exec_kwargs["timeout"] is not None:
        payload["timeoutMs"] = max(1, int(exec_kwargs["timeout"] * 1000))

    return payload


def to_reference_operation(operation: Mapping[str, Any]) -> dict[str, Any]:
    op = operation["op"]
    if op == "exec":
        payload: dict[str, Any] = {
            "op": "exec",
            "script": operation["script"],
        }
        if "kwargs" in operation:
            payload["options"] = to_reference_exec_options(operation["kwargs"])
        return payload

    if op == "write_bytes":
        return {
            "op": "write_bytes",
            "path": operation["path"],
            "content": encode_file_value(operation["content"]),
        }

    return dict(operation)


def run_reference_scenario(
    *,
    js_entry: Path,
    package_json: Path,
    init_options: Mapping[str, Any] | None = None,
    operations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    request = {
        "jsEntry": str(js_entry),
        "packageJson": str(package_json),
        "initOptions": dict(init_options or {}),
        "operations": [dict(operation) for operation in operations],
    }
    completed = subprocess.run(
        [*resolve_node_command(), str(REFERENCE_SCRIPT)],
        input=json.dumps(request),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"reference harness failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )

    try:
        payload = _JSON_OBJECT_ADAPTER.validate_json(completed.stdout)
    except ValidationError as exc:
        raise AssertionError(f"reference harness returned an invalid payload: {exc}\n{completed.stdout}") from exc
    return payload


def op_exec(script: str, **kwargs: Any) -> dict[str, Any]:
    operation: dict[str, Any] = {"op": "exec", "script": script}
    if kwargs:
        operation["kwargs"] = kwargs
    return operation


def op_read_text(path: str) -> dict[str, Any]:
    return {"op": "read_text", "path": path}


def op_read_bytes(path: str) -> dict[str, Any]:
    return {"op": "read_bytes", "path": path}


def op_write_text(path: str, content: str) -> dict[str, Any]:
    return {"op": "write_text", "path": path, "content": content}


def op_write_bytes(path: str, content: bytes) -> dict[str, Any]:
    return {"op": "write_bytes", "path": path, "content": content}


def op_get_env() -> dict[str, Any]:
    return {"op": "get_env"}


def op_get_cwd() -> dict[str, Any]:
    return {"op": "get_cwd"}


def run_python_scenario(
    *,
    init_kwargs: Mapping[str, Any],
    operations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    bash_type = public_api().Bash
    with bash_type(**dict(init_kwargs)) as bash:
        results: list[Any] = []
        for operation in operations:
            op = operation["op"]
            try:
                if op == "exec":
                    result = bash.exec(operation["script"], **dict(operation.get("kwargs", {})))
                    results.append(wrap_success(normalize_exec_result(result)))
                elif op == "read_text":
                    results.append(wrap_success(bash.read_text(operation["path"])))
                elif op == "read_bytes":
                    results.append(wrap_success(encode_file_value(bash.read_bytes(operation["path"]))))
                elif op == "write_text":
                    bash.write_text(operation["path"], operation["content"])
                    results.append(wrap_success(None))
                elif op == "write_bytes":
                    bash.write_bytes(operation["path"], operation["content"])
                    results.append(wrap_success(None))
                elif op == "get_env":
                    results.append(wrap_success(bash.get_env()))
                elif op == "get_cwd":
                    results.append(wrap_success(bash.get_cwd()))
                else:  # pragma: no cover - defensive
                    raise AssertionError(f"unknown op: {op}")
            except Exception as error:
                results.append(normalize_operation_error(error))

        return {
            "backendVersion": bash.backend_version,
            "results": results,
        }


def run_async_python_scenario(
    *,
    init_kwargs: Mapping[str, Any],
    operations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    async def exercise() -> dict[str, Any]:
        bash_type = public_api().AsyncBash
        async with bash_type(**dict(init_kwargs)) as bash:
            results: list[Any] = []
            for operation in operations:
                op = operation["op"]
                try:
                    if op == "exec":
                        result = await bash.exec(operation["script"], **dict(operation.get("kwargs", {})))
                        results.append(wrap_success(normalize_exec_result(result)))
                    elif op == "read_text":
                        results.append(wrap_success(await bash.read_text(operation["path"])))
                    elif op == "read_bytes":
                        results.append(wrap_success(encode_file_value(await bash.read_bytes(operation["path"]))))
                    elif op == "write_text":
                        await bash.write_text(operation["path"], operation["content"])
                        results.append(wrap_success(None))
                    elif op == "write_bytes":
                        await bash.write_bytes(operation["path"], operation["content"])
                        results.append(wrap_success(None))
                    elif op == "get_env":
                        results.append(wrap_success(await bash.get_env()))
                    elif op == "get_cwd":
                        results.append(wrap_success(await bash.get_cwd()))
                    else:  # pragma: no cover - defensive
                        raise AssertionError(f"unknown op: {op}")
                except Exception as error:
                    results.append(normalize_operation_error(error))

            return {
                "backendVersion": bash.backend_version,
                "results": results,
            }

    return asyncio.run(exercise())


def run_differential_scenario(
    *,
    init_kwargs: Mapping[str, Any],
    operations: Sequence[Mapping[str, Any]],
    backend_artifacts: BackendArtifacts,
) -> tuple[dict[str, Any], dict[str, Any]]:
    python_result = run_python_scenario(init_kwargs=init_kwargs, operations=operations)
    reference_result = run_reference_scenario(
        js_entry=backend_artifacts.js_entry,
        package_json=backend_artifacts.package_json,
        init_options=to_reference_init_options(init_kwargs),
        operations=[to_reference_operation(operation) for operation in operations],
    )
    return python_result, reference_result


def run_async_differential_scenario(
    *,
    init_kwargs: Mapping[str, Any],
    operations: Sequence[Mapping[str, Any]],
    backend_artifacts: BackendArtifacts,
) -> tuple[dict[str, Any], dict[str, Any]]:
    python_result = run_async_python_scenario(init_kwargs=init_kwargs, operations=operations)
    reference_result = run_reference_scenario(
        js_entry=backend_artifacts.js_entry,
        package_json=backend_artifacts.package_json,
        init_options=to_reference_init_options(init_kwargs),
        operations=[to_reference_operation(operation) for operation in operations],
    )
    return python_result, reference_result


def session_snapshot_operations(*, root: str = "/workspace") -> list[dict[str, Any]]:
    return [
        op_get_cwd(),
        op_get_env(),
        op_exec(f"find {root} -maxdepth 2 -mindepth 1 | sort"),
    ]


__all__ = [
    "BackendArtifacts",
    "BYTE_TAG",
    "decode_bytes_payload",
    "encode_file_value",
    "op_exec",
    "op_get_cwd",
    "op_get_env",
    "op_read_bytes",
    "op_read_text",
    "op_write_bytes",
    "op_write_text",
    "public_api",
    "normalize_exec_result",
    "normalize_operation_error",
    "session_snapshot_operations",
    "infer_package_json_from_js_entry",
    "resolve_backend_artifacts",
    "resolve_node_command",
    "run_async_differential_scenario",
    "run_async_python_scenario",
    "run_differential_scenario",
    "run_python_scenario",
    "run_reference_scenario",
    "wrap_success",
    "to_reference_exec_options",
    "to_reference_init_options",
    "to_reference_operation",
]
